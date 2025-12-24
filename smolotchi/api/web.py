import json
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from smolotchi.api.theme import load_theme_tokens, tokens_to_css_vars
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.config import ConfigStore
from smolotchi.core.toml_patch import (
    patch_baseline_add,
    patch_baseline_remove,
    patch_lan_lists,
)
from smolotchi.reports.exec_summary import (
    build_exec_summary,
    render_exec_summary_html,
    render_exec_summary_md,
)
from smolotchi.reports.host_diff import host_diff_html, host_diff_markdown
from smolotchi.reports.baseline import expected_findings_for_scope
from smolotchi.reports.baseline_diff import compute_baseline_diff
from smolotchi.reports.top_findings import aggregate_top_findings


def pretty(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def _atomic_write_text(path: Path, text: str) -> None:
    path = path.resolve()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def create_app(config_path: str = "config.toml") -> Flask:
    app = Flask(__name__)
    bus = SQLiteBus()
    store = ConfigStore(config_path)
    store.load()
    artifacts = ArtifactStore("/var/lib/smolotchi/artifacts")
    jobstore = JobStore(bus.db_path)

    def nav_active(endpoint: str) -> str:
        return "active" if request.endpoint == endpoint else ""

    @app.context_processor
    def inject_globals():
        cfg = store.get()
        tokens = {}
        if cfg.theme and cfg.theme.json_path:
            tokens = load_theme_tokens(cfg.theme.json_path)
        theme_css = tokens_to_css_vars(tokens) if tokens else ""
        return {
            "nav_active": nav_active,
            "app_cfg": cfg,
            "config_path": config_path,
            "theme_css": theme_css,
        }

    @app.get("/")
    def dashboard():
        events = bus.tail(limit=30)
        status_evt = next(
            (event for event in events if event.topic == "core.state.changed"), None
        )
        health_evts = bus.tail(limit=10, topic_prefix="core.health")
        health_evt = health_evts[0] if health_evts else None
        return render_template(
            "dashboard.html",
            status_evt=status_evt,
            health_evt=health_evt,
            events=events,
        )

    @app.get("/wifi")
    def wifi():
        events = bus.tail(limit=50, topic_prefix="wifi.")
        return render_template("wifi.html", events=events)

    @app.get("/lan")
    def lan():
        events = bus.tail(limit=80, topic_prefix="lan.")
        return render_template("lan.html", events=events)

    def _bundle_finding_state(bundle: dict, fid: str):
        """
        Returns:
          None                → finding not present
          "active"            → present, not suppressed
          "suppressed"        → present, suppressed
        """
        hs = bundle.get("host_summary") or {}
        for finding in (hs.get("findings") or []):
            finding_id = str(finding.get("id") or finding.get("title") or "")
            if finding_id != fid:
                continue
            suppressed = bool(
                finding.get("suppressed") or finding.get("suppressed_by_policy")
            )
            return "suppressed" if suppressed else "active"
        return None

    def _bundle_ts(meta: dict, bundle: dict) -> float:
        for key in ("ts", "created_ts", "created_at", "time"):
            value = meta.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        for key in ("ts", "created_ts", "created_at", "time"):
            value = bundle.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        job_id = str(bundle.get("job_id") or "")
        if job_id.startswith("job-"):
            try:
                return float(int(job_id.split("-", 1)[1]))
            except Exception:
                pass
        return 0.0

    def _fmt_ts(ts: float) -> str:
        if not ts:
            return "unknown"
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    def _expected_findings_for_bundles(bundles: list[dict]) -> set[str]:
        cfg = store.get()
        scope = None
        if bundles:
            scope = bundles[0].get("scope")
        if not scope:
            scope = getattr(getattr(cfg, "lan", None), "default_scope", None)
        return expected_findings_for_scope(cfg, scope)

    @app.get("/lan/results")
    def lan_results():
        fid = request.args.get("finding", "").strip()
        include_suppressed = request.args.get("include_suppressed", "0") in (
            "1",
            "true",
            "yes",
        )
        only_suppressed = request.args.get("only_suppressed", "0") in ("1", "true", "yes")

        metas = artifacts.list(limit=50, kind="lan_bundle")

        bundles = []
        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            bundle.setdefault("id", meta.id)
            bundle.setdefault("title", meta.title)
            bundle.setdefault("diff_summary", bundle.get("diff_summary") or {})
            bundle.setdefault("diff_badges", bundle.get("diff_badges") or {})

            state = None
            if fid:
                state = _bundle_finding_state(bundle, fid)
                if state is None:
                    continue
                if only_suppressed and state != "suppressed":
                    continue
                if not include_suppressed and state == "suppressed":
                    continue

                bundle["_finding_state"] = state
                bundle["_finding_id"] = fid

            bundles.append(bundle)

        all_items = (
            bundles
            if not fid
            else [artifacts.get_json(meta.id) or {} for meta in metas]
        )
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            all_items,
            limit=6,
            expected=expected,
        )
        return render_template(
            "lan_results.html",
            items=bundles,
            top_findings=top_findings,
            finding_filter=fid,
            include_suppressed=include_suppressed,
            only_suppressed=only_suppressed,
        )

    def _bundle_has_finding(bundle: dict, fid: str):
        summary = bundle.get("host_summary") or {}
        for finding in (summary.get("findings") or []):
            finding_id = str(finding.get("id") or finding.get("title") or "")
            if finding_id != fid:
                continue
            suppressed = bool(
                finding.get("suppressed") or finding.get("suppressed_by_policy")
            )
            return True, suppressed
        return False, False

    def _find_latest_bundle_for_finding(
        fid: str, include_suppressed: bool, only_suppressed: bool
    ) -> str | None:
        metas = artifacts.list(limit=300, kind="lan_bundle")
        best_unsuppressed = None
        best_suppressed = None

        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            ok, suppressed = _bundle_has_finding(bundle, fid)
            if not ok:
                continue

            if suppressed:
                if best_suppressed is None:
                    best_suppressed = meta.id
            else:
                if best_unsuppressed is None:
                    best_unsuppressed = meta.id

            if not only_suppressed and best_unsuppressed is not None:
                break
            if only_suppressed and best_suppressed is not None:
                break

        if only_suppressed:
            return best_suppressed
        if best_unsuppressed:
            return best_unsuppressed
        if include_suppressed:
            return best_suppressed
        return None

    def _load_recent_bundles(limit: int = 50) -> list[dict]:
        metas = artifacts.list(limit=limit, kind="lan_bundle")
        items = []
        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            bundle.setdefault("id", meta.id)
            items.append(bundle)
        return items

    def _pick_scope(cfg, bundles: list[dict]) -> str:
        if bundles:
            scope = (bundles[0].get("scope") or "").strip()
            if scope:
                return scope
        default_scope = (getattr(getattr(cfg, "lan", None), "default_scope", "") or "")
        return default_scope.strip() or "default"

    def _baseline_scopes(cfg) -> list[str]:
        baseline = getattr(cfg, "baseline", None)
        scopes = getattr(baseline, "scopes", None) if baseline else None
        if isinstance(scopes, dict):
            return sorted([str(key) for key in scopes.keys()])
        return []

    @app.get("/lan/baseline")
    def lan_baseline_overview():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=200)
        scopes = _baseline_scopes(cfg)
        scope_q = (request.args.get("scope") or "").strip()
        scope = scope_q or _pick_scope(cfg, bundles)
        if scopes and scope not in scopes:
            scope = scopes[0]
        expected = expected_findings_for_scope(cfg, scope)

        window = int(request.args.get("window", "50") or "50")
        window = max(5, min(window, 500))
        window_bundles = bundles[:window]

        diff = compute_baseline_diff(scope, expected, window_bundles)

        return render_template(
            "lan_baseline.html",
            scope=scope,
            scopes=scopes,
            window=window,
            expected_count=len(expected),
            diff=diff,
        )

    @app.get("/lan/baseline/diff")
    def lan_baseline_diff_latest():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=50)
        scopes = _baseline_scopes(cfg)
        scope_q = (request.args.get("scope") or "").strip()
        scope = scope_q or _pick_scope(cfg, bundles)
        if scopes and scope not in scopes:
            scope = scopes[0]
        expected = expected_findings_for_scope(cfg, scope)

        latest = bundles[0] if bundles else {}
        diff = compute_baseline_diff(scope, expected, [latest] if latest else [])

        return render_template(
            "lan_baseline_diff.html",
            scope=scope,
            scopes=scopes,
            bundle_id=(latest.get("id") if latest else None),
            diff=diff,
        )

    @app.post("/lan/baseline/add")
    def lan_baseline_add():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=50)
        scope = (request.form.get("scope") or "").strip() or _pick_scope(cfg, bundles)
        fid = (request.form.get("fid") or "").strip()

        if not fid or "\n" in fid or "\r" in fid or len(fid) > 200:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_baseline_add(text, scope=scope, finding_id=fid)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish("ui.baseline.added", {"scope": scope, "fid": fid, "ts": time.time()})

        back = request.form.get("back") or ""
        if back:
            return redirect(back)
        return redirect(url_for("lan_baseline_overview"))

    @app.post("/lan/baseline/remove")
    def lan_baseline_remove():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=50)
        scope = (request.form.get("scope") or "").strip() or _pick_scope(cfg, bundles)
        fid = (request.form.get("fid") or "").strip()

        if not fid or "\n" in fid or "\r" in fid or len(fid) > 200:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_baseline_remove(text, scope=scope, finding_id=fid)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.baseline.removed", {"scope": scope, "fid": fid, "ts": time.time()}
        )

        back = request.form.get("back") or ""
        return redirect(back or url_for("lan_baseline_overview"))

    @app.get("/lan/finding/<fid>/jump")
    def lan_finding_jump(fid: str):
        fid = fid.strip()
        if not fid:
            abort(400)
        include_suppressed = request.args.get("include_suppressed", "0") in (
            "1",
            "true",
            "yes",
        )
        only_suppressed = request.args.get("only_suppressed", "0") in (
            "1",
            "true",
            "yes",
        )
        bundle_id = _find_latest_bundle_for_finding(
            fid,
            include_suppressed=include_suppressed,
            only_suppressed=only_suppressed,
        )
        if not bundle_id:
            return redirect(url_for("lan_results") + f"?finding={fid}")
        return redirect(url_for("lan_result_details", bundle_id=bundle_id))

    @app.get("/lan/summary")
    def lan_exec_summary():
        bundles = _load_recent_bundles(limit=50)
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            bundles, limit=10, expected=expected
        )
        summary = build_exec_summary(bundles, top_findings)
        html = render_exec_summary_html(summary)
        return Response(html, mimetype="text/html")

    @app.get("/lan/summary.md")
    def lan_exec_summary_md():
        bundles = _load_recent_bundles(limit=50)
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            bundles, limit=10, expected=expected
        )
        summary = build_exec_summary(bundles, top_findings)
        md = render_exec_summary_md(summary)
        return Response(md, mimetype="text/markdown; charset=utf-8")

    @app.get("/lan/summary.json")
    def lan_exec_summary_json():
        bundles = _load_recent_bundles(limit=50)
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            bundles, limit=10, expected=expected
        )
        summary = build_exec_summary(bundles, top_findings)
        return Response(
            response=json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            status=200,
            mimetype="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="smolotchi_lan_summary.json"'
            },
        )

    def resolve_result_by_job_id(job_id: str):
        """
        Fallback resolver:
        1) Try lan_bundle by job_id (fast)
        2) Else: scan artifacts index for lan_result/lan_report and correlate via content.job.id
        """
        bundle_id = artifacts.find_bundle_by_job_id(job_id)
        if bundle_id:
            bundle = artifacts.get_json(bundle_id)
            json_id = (bundle.get("result_json") or {}).get("artifact_id")
            reports = bundle.get("reports") or {}
            report_html = reports.get("html") or bundle.get("report_html") or {}
            report_md = reports.get("md") or {}
            report_json = reports.get("json") or {}
            rep_id = report_html.get("artifact_id")
            diff_report = reports.get("diff") or {}
            diff_summary = bundle.get("diff_summary") or {}
            diff_badges = bundle.get("diff_badges") or {}
            return {
                "bundle_id": bundle_id,
                "bundle": bundle,
                "json_id": json_id,
                "report_id": rep_id,
                "report_md_id": report_md.get("artifact_id"),
                "report_json_id": report_json.get("artifact_id"),
                "diff_html_id": (diff_report.get("html") or {}).get("artifact_id"),
                "diff_md_id": (diff_report.get("md") or {}).get("artifact_id"),
                "diff_json_id": (diff_report.get("json") or {}).get("artifact_id")
                or diff_summary.get("artifact_id"),
                "diff_changed_hosts": diff_summary.get("changed_hosts", []),
                "diff_changed_hosts_count": diff_summary.get("changed_hosts_count"),
                "diff_badges": diff_badges,
            }

        idx = artifacts.list(limit=300)
        json_id = None
        report_id = None

        for artifact in idx:
            if artifact.kind == "lan_result":
                data = artifacts.get_json(artifact.id)
                if data and str(data.get("job", {}).get("id")) == job_id:
                    json_id = artifact.id
                    break

        for artifact in idx:
            if artifact.kind == "lan_report" and job_id in artifact.title:
                report_id = artifact.id
                break

        return {
            "bundle_id": None,
            "bundle": None,
            "json_id": json_id,
            "report_id": report_id,
            "report_md_id": None,
            "report_json_id": None,
            "diff_html_id": None,
            "diff_md_id": None,
            "diff_json_id": None,
            "diff_changed_hosts": [],
            "diff_changed_hosts_count": None,
            "diff_badges": {},
        }

    @app.get("/lan/result/<bundle_id>")
    def lan_result_details(bundle_id: str):
        bundle = artifacts.get_json(bundle_id)
        if not bundle:
            abort(404)
        json_id = (bundle.get("result_json") or {}).get("artifact_id")
        reports = bundle.get("reports") or {}
        report = reports.get("html") or bundle.get("report_html") or {}
        report_md = reports.get("md") or {}
        report_json = reports.get("json") or {}
        report_id = report.get("artifact_id")
        diff_report = reports.get("diff") or {}
        diff_summary = bundle.get("diff_summary") or {}
        diff_badges = bundle.get("diff_badges") or {}
        resolved = {
            "bundle_id": bundle_id,
            "bundle": bundle,
            "json_id": json_id,
            "report_id": report_id,
            "report_md_id": report_md.get("artifact_id"),
            "report_json_id": report_json.get("artifact_id"),
            "diff_html_id": (diff_report.get("html") or {}).get("artifact_id"),
            "diff_md_id": (diff_report.get("md") or {}).get("artifact_id"),
            "diff_json_id": (diff_report.get("json") or {}).get("artifact_id")
            or diff_summary.get("artifact_id"),
            "diff_changed_hosts": diff_summary.get("changed_hosts", []),
            "diff_changed_hosts_count": diff_summary.get("changed_hosts_count"),
            "diff_badges": diff_badges,
        }
        return _render_result_details(resolved, job_id=bundle.get("job_id"))

    @app.get("/lan/result")
    def lan_result_by_job():
        job_id = request.args.get("job_id", "").strip()
        if not job_id:
            abort(400)
        resolved = resolve_result_by_job_id(job_id)
        return _render_result_details(resolved, job_id=job_id)

    @app.get("/lan/finding/<fid>/timeline")
    def lan_finding_timeline(fid: str):
        fid = fid.strip()
        if not fid:
            abort(400)

        metas = artifacts.list(limit=500, kind="lan_bundle")
        history = []
        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            state = _bundle_finding_state(bundle, fid)
            if state is None:
                continue
            meta_data = artifacts.get_meta(meta.id) or {}
            ts = _bundle_ts(meta_data, bundle)
            history.append(
                {
                    "ts": ts,
                    "ts_str": _fmt_ts(ts),
                    "bundle_id": meta.id,
                    "state": state,
                }
            )

        if not history:
            return render_template(
                "lan_finding_timeline.html",
                fid=fid,
                first=None,
                last=None,
                history=[],
            )

        history_sorted = sorted(history, key=lambda x: x["ts"] or 0)
        first = history_sorted[0]
        last = history_sorted[-1]
        history_desc = sorted(history_sorted, key=lambda x: x["ts"] or 0, reverse=True)

        return render_template(
            "lan_finding_timeline.html",
            fid=fid,
            first=first,
            last=last,
            history=history_desc,
        )

    def _render_result_details(resolved: dict, job_id: str | None):
        bundle_id = resolved.get("bundle_id")
        bundle = resolved.get("bundle")
        json_id = resolved.get("json_id")
        report_id = resolved.get("report_id")
        report_md_id = resolved.get("report_md_id")
        report_json_id = resolved.get("report_json_id")
        diff_html_id = resolved.get("diff_html_id")
        diff_md_id = resolved.get("diff_md_id")
        diff_json_id = resolved.get("diff_json_id")
        diff_changed_hosts = resolved.get("diff_changed_hosts") or []
        diff_changed_hosts_count = resolved.get("diff_changed_hosts_count")
        diff_badges = resolved.get("diff_badges") or {}
        if diff_changed_hosts_count is None and diff_changed_hosts:
            diff_changed_hosts_count = len(diff_changed_hosts)

        result_json = artifacts.get_json(json_id) if json_id else None
        bundle_pretty = pretty(bundle) if bundle else ""
        result_pretty = pretty(result_json) if result_json else ""

        evts = []
        if job_id:
            raw = bus.tail(limit=300)
            for event in raw:
                payload = event.payload or {}
                if payload.get("id") == job_id or payload.get("job", {}).get("id") == job_id:
                    evts.append(event)
            evts = evts[:80]

        return render_template(
            "lan_result_details_tabs.html",
            job_id=job_id,
            bundle_id=bundle_id,
            bundle_pretty=bundle_pretty,
            result_json_id=json_id,
            result_pretty=result_pretty,
            report_id=report_id,
            report_md_id=report_md_id,
            report_json_id=report_json_id,
            diff_html_id=diff_html_id,
            diff_md_id=diff_md_id,
            diff_json_id=diff_json_id,
            diff_changed_hosts=diff_changed_hosts,
            diff_changed_hosts_count=diff_changed_hosts_count,
            diff_badges=diff_badges,
            events=evts,
        )

    @app.get("/lan/reports")
    def lan_reports():
        report_metas = artifacts.list(limit=50, kind="lan_report")

        bundle_metas = artifacts.list(limit=200, kind="lan_bundle")
        report_to_bundle: dict[str, str] = {}
        bundle_cache: dict[str, dict] = {}

        for bm in bundle_metas:
            bundle = artifacts.get_json(bm.id) or {}
            bundle_cache[bm.id] = bundle
            reports = bundle.get("reports") or {}
            html = reports.get("html") or bundle.get("report_html") or {}
            rep_id = (html or {}).get("artifact_id")
            if rep_id:
                report_to_bundle[str(rep_id)] = bm.id

        items = []
        for rm in report_metas:
            bundle_id = report_to_bundle.get(rm.id)
            job_id = None
            diff_html_id = None
            diff_md_id = None
            diff_json_id = None

            if bundle_id:
                bundle = bundle_cache.get(bundle_id) or (artifacts.get_json(bundle_id) or {})
                job_id = bundle.get("job_id")

                reports = bundle.get("reports") or {}
                diff_report = reports.get("diff") or {}
                diff_summary = bundle.get("diff_summary") or {}

                diff_html_id = (diff_report.get("html") or {}).get("artifact_id")
                diff_md_id = (diff_report.get("md") or {}).get("artifact_id")
                diff_json_id = (diff_report.get("json") or {}).get("artifact_id") or diff_summary.get(
                    "artifact_id"
                )

            items.append(
                {
                    "id": rm.id,
                    "title": rm.title,
                    "bundle_id": bundle_id,
                    "job_id": job_id,
                    "diff_html_id": diff_html_id,
                    "diff_md_id": diff_md_id,
                    "diff_json_id": diff_json_id,
                }
            )

        return render_template("lan_reports.html", items=items)

    def _resolve_bundle(bundle_id: str):
        bundle = artifacts.get_json(bundle_id)
        if bundle:
            return bundle_id, bundle
        bundle_id = artifacts.find_bundle_by_job_id(bundle_id)
        if not bundle_id:
            return None, None
        return bundle_id, artifacts.get_json(bundle_id)

    @app.get("/lan/diff/host/<bundle_id>/<host>")
    def lan_host_diff(bundle_id: str, host: str):
        bundle_id, bundle = _resolve_bundle(bundle_id)
        if not bundle:
            abort(404)
        reports = bundle.get("reports") or {}
        diff_report = reports.get("diff") or {}
        diff_summary = bundle.get("diff_summary") or {}
        diff_json_id = (diff_report.get("json") or {}).get("artifact_id") or diff_summary.get(
            "artifact_id"
        )
        if not diff_json_id:
            abort(404)
        diff = artifacts.get_json(diff_json_id) or {}
        prev_v = request.args.get("prev_v", "").strip()
        cur_v = request.args.get("cur_v", "").strip()
        html = host_diff_html(diff, host, artifacts=artifacts, prev_v=prev_v, cur_v=cur_v)
        return Response(html, mimetype="text/html")

    @app.get("/lan/diff/host/<bundle_id>/<host>.md")
    def lan_host_diff_md(bundle_id: str, host: str):
        bundle_id, bundle = _resolve_bundle(bundle_id)
        if not bundle:
            abort(404)
        reports = bundle.get("reports") or {}
        diff_report = reports.get("diff") or {}
        diff_summary = bundle.get("diff_summary") or {}
        diff_json_id = (diff_report.get("json") or {}).get("artifact_id") or diff_summary.get(
            "artifact_id"
        )
        if not diff_json_id:
            abort(404)
        diff = artifacts.get_json(diff_json_id) or {}
        md = host_diff_markdown(diff, host)
        return Response(md, mimetype="text/markdown; charset=utf-8")

    @app.get("/artifact/<artifact_id>")
    def artifact_view(artifact_id: str):
        data = artifacts.get_json(artifact_id)
        if data is None:
            abort(404)
        return render_template("artifact.html", artifact_id=artifact_id, data=data)

    @app.get("/artifact/<artifact_id>.json")
    def artifact_download(artifact_id: str):
        data = artifacts.get_json(artifact_id)
        if data is None:
            abort(404)
        return Response(
            response=json.dumps(data, ensure_ascii=False, indent=2),
            status=200,
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{artifact_id}.json"'
            },
        )

    @app.get("/artifact/<artifact_id>/download")
    def artifact_file_download(artifact_id: str):
        meta = artifacts.get_meta(artifact_id)
        if not meta:
            abort(404)
        path = meta.get("path")
        if not path or not Path(path).exists():
            abort(404)
        return send_file(path, as_attachment=True)

    @app.get("/report/<artifact_id>")
    def report_view(artifact_id: str):
        meta = artifacts.get_meta(artifact_id)
        if not meta:
            abort(404)
        path = meta.get("path")
        if not path or not Path(path).exists():
            abort(404)
        return send_file(path, as_attachment=False)

    @app.get("/lan/jobs")
    def lan_jobs():
        queued = jobstore.list(limit=30, status="queued")
        running = jobstore.list(limit=10, status="running")
        done = jobstore.list(limit=30, status="done")
        failed = jobstore.list(limit=30, status="failed")
        return render_template(
            "lan_jobs.html",
            queued=queued,
            running=running,
            done=done,
            failed=failed,
        )

    @app.post("/lan/job/<job_id>/cancel")
    def lan_job_cancel(job_id: str):
        ok = jobstore.cancel(job_id)
        bus.publish("ui.job.cancel", {"id": job_id, "ok": ok})
        return redirect(url_for("lan_jobs"))

    @app.post("/lan/job/<job_id>/reset")
    def lan_job_reset(job_id: str):
        ok = jobstore.reset_running(job_id)
        bus.publish("ui.job.reset", {"id": job_id, "ok": ok})
        return redirect(url_for("lan_jobs"))

    @app.post("/lan/job/<job_id>/delete")
    def lan_job_delete(job_id: str):
        ok = jobstore.delete(job_id)
        bus.publish("ui.job.delete", {"id": job_id, "ok": ok})
        return redirect(url_for("lan_jobs"))

    @app.get("/lan/policy")
    def lan_policy():
        cfg_file = Path(config_path)
        cfg = store.get()
        noisy = getattr(getattr(cfg, "lan", None), "noisy_scripts", None) or []
        allow = getattr(getattr(cfg, "lan", None), "allowlist_scripts", None) or []
        return render_template(
            "lan_policy.html",
            noisy="\n".join(noisy),
            allow="\n".join(allow),
        )

    @app.post("/lan/policy")
    def lan_policy_save():
        cfg_file = Path(config_path)
        noisy = [
            value.strip()
            for value in request.form.get("noisy", "").splitlines()
            if value.strip()
        ]
        allow = [
            value.strip()
            for value in request.form.get("allow", "").splitlines()
            if value.strip()
        ]
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_lan_lists(text, noisy=noisy, allow=allow)
        _atomic_write_text(cfg_file, patched)
        bus.publish("ui.policy.saved", {"ts": time.time()})
        return redirect(url_for("lan_policy"))

    @app.post("/lan/policy/save_reload")
    def lan_policy_save_reload():
        cfg_file = Path(config_path)
        noisy = [
            value.strip()
            for value in request.form.get("noisy", "").splitlines()
            if value.strip()
        ]
        allow = [
            value.strip()
            for value in request.form.get("allow", "").splitlines()
            if value.strip()
        ]
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_lan_lists(text, noisy=noisy, allow=allow)
        _atomic_write_text(cfg_file, patched)
        store.reload()
        bus.publish("ui.policy.saved_reloaded", {"ts": time.time()})
        return redirect(url_for("lan_policy"))

    @app.get("/config")
    def config():
        cfg = store.get()
        cfg_file = Path(config_path)
        msg = None
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception as exc:
            content = ""
            msg = {"title": "Error", "text": f"Failed to read {cfg_file}: {exc}"}

        return render_template(
            "config.html",
            cfg=cfg,
            config_path=str(cfg_file),
            content=content,
            msg=msg,
        )

    @app.post("/config")
    def config_save():
        cfg_file = Path(config_path)
        content = request.form.get("content", "")
        msg = None

        try:
            if not isinstance(content, str):
                raise ValueError("Invalid content")
            _atomic_write_text(cfg_file, content)
            msg = {
                "title": "Saved",
                "text": f"Updated {cfg_file}. You may want to Reload config.",
            }
            bus.publish("ui.config.saved", {"path": str(cfg_file), "ts": time.time()})
        except Exception as exc:
            msg = {"title": "Error", "text": f"Failed to write {cfg_file}: {exc}"}

        cfg = store.get()
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception:
            pass

        return render_template(
            "config.html",
            cfg=cfg,
            config_path=str(cfg_file),
            content=content,
            msg=msg,
        )

    @app.post("/config/save_reload")
    def config_save_reload():
        cfg_file = Path(config_path)
        content = request.form.get("content", "")
        msg = None

        try:
            if not isinstance(content, str):
                raise ValueError("Invalid content")

            _atomic_write_text(cfg_file, content)
            store.reload()

            bus.publish(
                "ui.config.saved_reloaded",
                {"path": str(cfg_file), "ts": time.time()},
            )

            msg = {
                "title": "Saved & Reloaded",
                "text": f"{cfg_file} updated and reloaded successfully.",
            }
        except Exception as exc:
            msg = {"title": "Error", "text": f"Save+Reload failed: {exc}"}

        cfg = store.get()
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception:
            pass

        return render_template(
            "config.html",
            cfg=cfg,
            config_path=str(cfg_file),
            content=content,
            msg=msg,
        )

    @app.post("/config/reload")
    def config_reload():
        store.reload()
        bus.publish("ui.config.reloaded", {"path": config_path, "ts": time.time()})
        return redirect(url_for("config"))

    @app.get("/audit")
    def audit():
        events = bus.tail(limit=120)
        return render_template("audit.html", events=events)

    @app.post("/handoff")
    def handoff():
        tag = request.form.get("tag", "lab-approved")
        note = request.form.get("note", "")
        bus.publish("ui.handoff.request", {"tag": tag, "note": note})
        return redirect(url_for("dashboard"))

    @app.post("/lan_done")
    def lan_done():
        bus.publish("lan.done", {"note": "manual done"})
        return redirect(url_for("lan"))

    @app.post("/lan_enqueue")
    def lan_enqueue():
        scope = request.form.get("scope", "10.0.10.0/24")
        note = request.form.get("note", "")
        bus.publish(
            "ui.lan.enqueue",
            {
                "job": {
                    "id": f"job-{int(time.time())}",
                    "kind": "inventory",
                    "scope": scope,
                    "note": note,
                }
            },
        )
        return redirect(url_for("lan"))

    @app.post("/ai/plan")
    def ai_plan():
        scope = request.form.get("scope", "10.0.10.0/24")
        note = request.form.get("note", "")
        bus.publish("ui.ai.generate_plan", {"scope": scope, "note": note})
        return redirect(url_for("dashboard"))

    @app.post("/ai/run")
    def ai_run():
        bus.publish("ui.ai.run_autonomous_safe", {})
        return redirect(url_for("dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=False)
