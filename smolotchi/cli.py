import argparse
import json
import os
import subprocess
import time
from pathlib import Path

from smolotchi.ai.replay import (
    baseline_delta_from_bundles,
    evaluate_plan_run,
    metrics_row,
)
from smolotchi.cli_artifacts import add_artifacts_subcommands
from smolotchi.cli_profiles import add_profiles_subcommands
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.app_state import load_state, save_state, state_path_for_artifacts
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.paths import (
    resolve_artifact_root,
    resolve_config_path,
    resolve_db_path,
    resolve_default_tag,
    resolve_device,
    resolve_lock_root,
)
from smolotchi.core.policy import Policy
from smolotchi.core.state import SmolotchiCore


def _format_ts(ts: float | None) -> str:
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def cmd_web(args) -> int:
    from smolotchi.api.web import create_app
    from smolotchi.core.config import ConfigStore

    store = ConfigStore(args.config)
    cfg = store.load()

    app = create_app(config_path=args.config)
    env_host = os.environ.get("SMOLOTCHI_WEB_HOST")
    env_port = os.environ.get("SMOLOTCHI_WEB_PORT")
    host = args.host or env_host or cfg.ui.host
    port = args.port or (int(env_port) if env_port else None) or cfg.ui.port
    app.run(host=host, port=port, debug=False)
    return 0


def cmd_display(args) -> int:
    os.environ["SMOLOTCHI_DEVICE"] = args.device
    os.environ["SMOLOTCHI_DB"] = args.db
    os.environ["SMOLOTCHI_ARTIFACT_ROOT"] = args.artifact_root
    from smolotchi.display.displayd import main

    main()
    return 0


def cmd_core(args) -> int:
    """
    Minimaler Core-Daemon: tickt State-Machine periodisch.
    (v0.0.1 tickte im Web-Request – jetzt unabhängig)
    """
    from smolotchi.core.engines import EngineRegistry
    from smolotchi.core.config import ConfigStore
    from smolotchi.core.artifacts import ArtifactStore
    from smolotchi.core.jobs import JobStore
    from smolotchi.core.reports import ReportConfig, ReportRenderer
    from smolotchi.core.resources import ResourceManager
    from smolotchi.core.watchdog import JobWatchdog
    from smolotchi.engines.lan_engine import LanConfig, LanEngine
    from smolotchi.engines.tools_engine import ToolsEngine
    from smolotchi.engines.wifi_engine import WifiEngine

    store = ConfigStore(args.config)
    cfg = store.load()

    bus = SQLiteBus(db_path=args.db)
    allowed_tags = cfg.policy.allowed_tags
    if args.allowed_tags:
        allowed_tags = args.allowed_tags
    policy = Policy(
        allowed_tags=allowed_tags,
        allowed_scopes=cfg.policy.allowed_scopes,
        allowed_tools=cfg.policy.allowed_tools,
        block_categories=cfg.policy.block_categories,
        autonomous_categories=cfg.policy.autonomous_categories,
    )

    artifact_root = resolve_artifact_root()
    artifacts = ArtifactStore(artifact_root)
    state_path = state_path_for_artifacts(artifacts.root)
    state = load_state(state_path)
    jobs = JobStore(args.db)
    resources = ResourceManager(resolve_lock_root())
    renderer = (
        ReportRenderer(ReportConfig(templates_dir=cfg.reports.templates_dir))
        if cfg.reports.enabled
        else None
    )

    reg = EngineRegistry()
    reg.register(
        WifiEngine(
            bus,
            store,
            artifacts,
        )
    )
    from smolotchi.actions.plan_runner import BatchPlanRunner
    from smolotchi.actions.planners.ai_planner import AIPlanner
    from smolotchi.actions.registry import load_pack
    from smolotchi.actions.runner import ActionRunner

    actions = load_pack("smolotchi/actions/packs/bjorn_core.yml")
    action_runner = ActionRunner(
        bus=bus, artifacts=artifacts, policy=policy, registry=actions
    )
    plan_runner = BatchPlanRunner(
        bus=bus, registry=actions, runner=action_runner, artifacts=artifacts
    )
    planner = AIPlanner(bus=bus, registry=actions, artifacts=artifacts)

    reg.register(
        LanEngine(
            bus,
            LanConfig(
                enabled=cfg.lan.enabled,
                safe_mode=cfg.lan.safe_mode,
                max_jobs_per_tick=cfg.lan.max_jobs_per_tick,
                noisy_scripts=cfg.lan.noisy_scripts,
                allowlist_scripts=cfg.lan.allowlist_scripts,
            ),
            artifacts=artifacts,
            jobs=jobs,
            report_renderer=renderer,
            registry=actions,
            planner=planner,
            plan_runner=plan_runner,
            ai_max_hosts=cfg.ai.max_hosts_per_plan,
            ai_max_steps=cfg.ai.max_steps,
            ai_include_vuln=cfg.ai.autonomous_include_vuln_assess,
            ai_batch_strategy=cfg.ai.exec.batch_strategy,
            ai_throttle={
                "enabled": cfg.ai.throttle.enabled,
                "loadavg_soft": cfg.ai.throttle.loadavg_soft,
                "loadavg_hard": cfg.ai.throttle.loadavg_hard,
                "cooldown_multiplier_soft": cfg.ai.throttle.cooldown_multiplier_soft,
                "cooldown_multiplier_hard": cfg.ai.throttle.cooldown_multiplier_hard,
                "min_cooldown_ms": cfg.ai.throttle.min_cooldown_ms,
                "max_cooldown_ms": cfg.ai.throttle.max_cooldown_ms,
                "use_cpu_temp": cfg.ai.throttle.use_cpu_temp,
                "temp_soft_c": cfg.ai.throttle.temp_soft_c,
                "temp_hard_c": cfg.ai.throttle.temp_hard_c,
                "temp_multiplier_soft": cfg.ai.throttle.temp_multiplier_soft,
                "temp_multiplier_hard": cfg.ai.throttle.temp_multiplier_hard,
            },
            ai_exec={
                "batch_strategy": cfg.ai.exec.batch_strategy,
                "cooldown_between_actions_ms": cfg.ai.exec.cooldown_between_actions_ms,
                "cooldown_between_hosts_ms": cfg.ai.exec.cooldown_between_hosts_ms,
                "max_retries": cfg.ai.exec.max_retries,
                "retry_backoff_ms": cfg.ai.exec.retry_backoff_ms,
            },
            ai_cache={
                "use_cached_discovery": cfg.ai.cache.use_cached_discovery,
                "discovery_ttl_seconds": cfg.ai.cache.discovery_ttl_seconds,
                "use_cached_portscan": cfg.ai.cache.use_cached_portscan,
                "portscan_ttl_seconds": cfg.ai.cache.portscan_ttl_seconds,
                "use_cached_vuln": cfg.ai.cache.use_cached_vuln,
                "vuln_ttl_seconds": cfg.ai.cache.vuln_ttl_seconds,
                "vuln_ttl_http_seconds": cfg.ai.cache.vuln_ttl_http_seconds,
                "vuln_ttl_ssh_seconds": cfg.ai.cache.vuln_ttl_ssh_seconds,
                "vuln_ttl_smb_seconds": cfg.ai.cache.vuln_ttl_smb_seconds,
            },
            invalidation={
                "enabled": cfg.invalidation.enabled,
                "invalidate_on_port_change": cfg.invalidation.invalidate_on_port_change,
            },
            report_cfg={
                "lan": {
                    "noisy_scripts": cfg.lan.noisy_scripts,
                    "allowlist_scripts": cfg.lan.allowlist_scripts,
                },
                "findings": {
                    "enabled": cfg.report_findings.enabled,
                    "allowlist": cfg.report_findings.allowlist,
                    "denylist": cfg.report_findings.denylist,
                    "deny_contains": cfg.report_findings.deny_contains,
                    "max_findings_per_host": cfg.report_findings.max_findings_per_host,
                    "max_output_chars": cfg.report_findings.max_output_chars,
                    "max_output_lines": cfg.report_findings.max_output_lines,
                },
                "normalize": {
                    "enabled": cfg.report_normalize.enabled,
                    "force_severity": cfg.report_normalize.force_severity,
                    "force_tag": cfg.report_normalize.force_tag,
                },
                "baseline": {
                    "enabled": cfg.baseline.enabled,
                    "scopes": cfg.baseline.scopes,
                    "profiles": cfg.baseline.profiles,
                },
                "diff": {
                    "enabled": cfg.report_diff.enabled,
                    "compare_window_seconds": cfg.report_diff.compare_window_seconds,
                    "max_hosts": cfg.report_diff.max_hosts,
                    "baseline_host_summary_id": state.baseline_host_summary_id
                    or cfg.report_diff.baseline_host_summary_id,
                },
            },
        )
    )
    tools_engine = ToolsEngine(bus=bus, artifacts=artifacts, jobstore=jobs, config=store)
    tools_engine.start()
    reg.register(tools_engine)

    core = SmolotchiCore(bus=bus, policy=policy, engines=reg, resources=resources)
    core.set_state(cfg.core.default_state, "default from config")

    bus.publish("core.started", {"pid": os.getpid(), "config": args.config})
    last_health = 0.0
    try:
        while True:
            now = time.time()
            if now - last_health > 10.0:
                last_health = now
                bus.publish("core.health", {"ts": now, "pid": os.getpid()})
            new_cfg = store.get()
            lan = reg.get("lan")
            if lan:
                lan.cfg.enabled = new_cfg.lan.enabled
                lan.cfg.safe_mode = new_cfg.lan.safe_mode
                lan.cfg.max_jobs_per_tick = new_cfg.lan.max_jobs_per_tick
                lan.ai_max_hosts = new_cfg.ai.max_hosts_per_plan
                lan.ai_max_steps = new_cfg.ai.max_steps
                lan.ai_include_vuln = new_cfg.ai.autonomous_include_vuln_assess
                lan.ai_batch_strategy = new_cfg.ai.exec.batch_strategy
                lan.ai_throttle = {
                    "enabled": new_cfg.ai.throttle.enabled,
                    "loadavg_soft": new_cfg.ai.throttle.loadavg_soft,
                    "loadavg_hard": new_cfg.ai.throttle.loadavg_hard,
                    "cooldown_multiplier_soft": new_cfg.ai.throttle.cooldown_multiplier_soft,
                    "cooldown_multiplier_hard": new_cfg.ai.throttle.cooldown_multiplier_hard,
                    "min_cooldown_ms": new_cfg.ai.throttle.min_cooldown_ms,
                    "max_cooldown_ms": new_cfg.ai.throttle.max_cooldown_ms,
                    "use_cpu_temp": new_cfg.ai.throttle.use_cpu_temp,
                    "temp_soft_c": new_cfg.ai.throttle.temp_soft_c,
                    "temp_hard_c": new_cfg.ai.throttle.temp_hard_c,
                    "temp_multiplier_soft": new_cfg.ai.throttle.temp_multiplier_soft,
                    "temp_multiplier_hard": new_cfg.ai.throttle.temp_multiplier_hard,
                }
                lan.ai_exec = {
                    "batch_strategy": new_cfg.ai.exec.batch_strategy,
                    "cooldown_between_actions_ms": new_cfg.ai.exec.cooldown_between_actions_ms,
                    "cooldown_between_hosts_ms": new_cfg.ai.exec.cooldown_between_hosts_ms,
                    "max_retries": new_cfg.ai.exec.max_retries,
                    "retry_backoff_ms": new_cfg.ai.exec.retry_backoff_ms,
                }
                lan.ai_cache = {
                    "use_cached_discovery": new_cfg.ai.cache.use_cached_discovery,
                    "discovery_ttl_seconds": new_cfg.ai.cache.discovery_ttl_seconds,
                    "use_cached_portscan": new_cfg.ai.cache.use_cached_portscan,
                    "portscan_ttl_seconds": new_cfg.ai.cache.portscan_ttl_seconds,
                    "use_cached_vuln": new_cfg.ai.cache.use_cached_vuln,
                    "vuln_ttl_seconds": new_cfg.ai.cache.vuln_ttl_seconds,
                    "vuln_ttl_http_seconds": new_cfg.ai.cache.vuln_ttl_http_seconds,
                    "vuln_ttl_ssh_seconds": new_cfg.ai.cache.vuln_ttl_ssh_seconds,
                    "vuln_ttl_smb_seconds": new_cfg.ai.cache.vuln_ttl_smb_seconds,
                }
                lan.invalidation = {
                    "enabled": new_cfg.invalidation.enabled,
                    "invalidate_on_port_change": new_cfg.invalidation.invalidate_on_port_change,
                }
                state = load_state(state_path)
                lan.report_cfg = {
                    "findings": {
                        "enabled": new_cfg.report_findings.enabled,
                        "allowlist": new_cfg.report_findings.allowlist,
                        "denylist": new_cfg.report_findings.denylist,
                        "deny_contains": new_cfg.report_findings.deny_contains,
                        "max_findings_per_host": new_cfg.report_findings.max_findings_per_host,
                        "max_output_chars": new_cfg.report_findings.max_output_chars,
                        "max_output_lines": new_cfg.report_findings.max_output_lines,
                    },
                    "normalize": {
                        "enabled": new_cfg.report_normalize.enabled,
                        "force_severity": new_cfg.report_normalize.force_severity,
                        "force_tag": new_cfg.report_normalize.force_tag,
                    },
                    "diff": {
                        "enabled": new_cfg.report_diff.enabled,
                        "compare_window_seconds": new_cfg.report_diff.compare_window_seconds,
                        "max_hosts": new_cfg.report_diff.max_hosts,
                        "baseline_host_summary_id": state.baseline_host_summary_id
                        or new_cfg.report_diff.baseline_host_summary_id,
                    },
                }
            if not hasattr(cmd_core, "_last_prune"):
                cmd_core._last_prune = 0.0  # type: ignore[attr-defined]
            if not hasattr(cmd_core, "_last_wd"):
                cmd_core._last_wd = 0.0  # type: ignore[attr-defined]
            if not hasattr(cmd_core, "_watchdog"):
                cmd_core._watchdog = JobWatchdog(  # type: ignore[attr-defined]
                    bus=bus, jobs=jobs, config=store
                )

            if now - cmd_core._last_prune > 60.0:  # type: ignore[attr-defined]
                cmd_core._last_prune = now  # type: ignore[attr-defined]
                r = new_cfg.retention
                deleted_events = bus.prune(
                    keep_last=r.events_keep_last,
                    older_than_days=r.events_older_than_days,
                    vacuum=r.vacuum_after_prune,
                )
                deleted_jobs = jobs.prune(
                    keep_last=r.jobs_keep_last,
                    done_failed_older_than_days=r.jobs_done_failed_older_than_days,
                )
                deleted_artifacts = artifacts.prune(
                    keep_last=r.artifacts_keep_last,
                    older_than_days=r.artifacts_older_than_days,
                    kinds_keep_last=r.artifact_kinds_keep_last,
                )
                bus.publish(
                    "core.retention.pruned",
                    {
                        "events_deleted": deleted_events,
                        "jobs_deleted": deleted_jobs,
                        "artifacts_deleted": deleted_artifacts,
                    },
                )
            wd_cfg = new_cfg.watchdog
            if wd_cfg.enabled and now - cmd_core._last_wd > wd_cfg.interval_sec:  # type: ignore[attr-defined]
                cmd_core._last_wd = now  # type: ignore[attr-defined]
                try:
                    cmd_core._watchdog.tick()  # type: ignore[attr-defined]
                except Exception as ex:
                    bus.publish("core.watchdog.error", {"err": str(ex)})
            core.tick()
            interval = (
                args.interval if args.interval is not None else new_cfg.core.tick_interval
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        bus.publish("core.stopped", {"pid": os.getpid()})
        return 0


def cmd_status(args) -> int:
    bus = SQLiteBus(db_path=args.db)
    evts = bus.tail(limit=50)
    st = None
    for e in evts:
        if e.topic == "core.state.changed":
            st = e.payload
            break
    if not st:
        print("state: <unknown> (no core.state.changed yet)")
        return 0

    print(f"state: {st.get('state')}")
    note = st.get("note", "")
    if note:
        print(f"note:  {note}")
    print(f"ts:    {st.get('ts')}")
    return 0


def cmd_events(args) -> int:
    bus = SQLiteBus(db_path=args.db)
    evts = bus.tail(limit=args.limit, topic_prefix=args.topic_prefix)
    for e in reversed(evts):
        print(f"{e.ts:.0f}  {e.topic}  {e.payload}")
    return 0


def cmd_wifi_scan(args) -> int:
    from smolotchi.core.config import ConfigStore
    from smolotchi.engines.wifi_scan import scan_iw

    store = ConfigStore(args.config)
    cfg = store.load()
    iface = args.iface or cfg.wifi.iface
    aps = scan_iw(iface)
    print(f"iface={iface} count={len(aps)}")
    print(f"{'SSID':32} {'BSSID':18} {'FREQ':6} {'SIGNAL':7} {'SEC':8}")
    for ap in aps[: args.limit]:
        print(
            f"{ap.ssid[:32]:32} {ap.bssid:18} "
            f"{ap.freq_mhz or '-':6} {ap.signal_dbm or '-':7} {ap.security or '-':8}"
        )
    return 0


def cmd_wifi_connect(args) -> int:
    from smolotchi.core.config import ConfigStore
    from smolotchi.engines.wifi_connect import connect_wpa_psk
    from smolotchi.engines.net_detect import detect_ipv4_cidr, detect_scope_for_iface

    store = ConfigStore(args.config)
    cfg = store.load()
    iface = args.iface or cfg.wifi.iface
    creds = cfg.wifi.credentials or {}
    allow = set(cfg.wifi.allow_ssids or [])
    if allow and args.ssid not in allow:
        print(f"error: ssid '{args.ssid}' not in allowlist")
        return 2
    if args.ssid not in creds:
        print(f"error: no credential for ssid '{args.ssid}'")
        return 2
    ok, out = connect_wpa_psk(iface, args.ssid, creds[args.ssid])
    print(out.strip())
    if ok:
        cidr = detect_ipv4_cidr(iface)
        scope = detect_scope_for_iface(iface)
        if cidr:
            print(f"cidr={cidr}")
        if scope:
            print(f"scope={scope}")
    return 0 if ok else 1


def cmd_wifi_status(args) -> int:
    from smolotchi.core.config import ConfigStore
    from smolotchi.engines.net_detect import detect_ipv4_cidr, detect_scope_for_iface

    store = ConfigStore(args.config)
    cfg = store.load()
    iface = args.iface or cfg.wifi.iface
    cidr = detect_ipv4_cidr(iface)
    scope = detect_scope_for_iface(iface)
    print(f"iface={iface} cidr={cidr or '-'} scope={scope or '-'}")
    return 0


def cmd_jobs_enqueue(args) -> int:
    from smolotchi.core.jobs import JobStore

    job_id = args.job_id or f"job-{int(time.time())}"
    js = JobStore(args.db)
    js.enqueue(
        {
            "id": job_id,
            "kind": args.kind,
            "scope": args.scope,
            "note": args.note or "",
            "meta": {},
        }
    )
    print(job_id)
    return 0


def cmd_jobs_list(args) -> int:
    from smolotchi.core.jobs import JobStore

    js = JobStore(args.db)
    statuses = args.status or []
    rows = []
    if statuses:
        if len(statuses) == 1:
            rows = js.list(limit=args.limit, status=statuses[0])
        else:
            rows = js.list(limit=max(args.limit, 200))
            rows = [row for row in rows if row.status in statuses]
    else:
        rows = js.list(limit=args.limit)

    if args.kind:
        rows = [row for row in rows if row.kind == args.kind]
    if args.note_contains:
        rows = [row for row in rows if args.note_contains in (row.note or "")]
    rows = rows[: args.limit]

    if args.format == "json":
        payload = [
            {
                "id": row.id,
                "kind": row.kind,
                "scope": row.scope,
                "note": row.note,
                "status": row.status,
                "created_ts": row.created_ts,
                "updated_ts": row.updated_ts,
            }
            for row in rows
        ]
        _print_json(payload)
        return 0

    table_rows = [
        [
            row.id,
            row.status,
            row.kind,
            _format_ts(row.created_ts),
            row.scope,
        ]
        for row in rows
    ]
    _print_table(["ID", "STATUS", "KIND", "CREATED", "SCOPE"], table_rows)
    return 0


def cmd_jobs_get(args) -> int:
    from smolotchi.core.jobs import JobStore

    js = JobStore(args.db)
    row = js.get(args.job_id)
    if not row:
        print("error: job not found")
        return 2
    payload = {
        "id": row.id,
        "kind": row.kind,
        "scope": row.scope,
        "note": row.note,
        "status": row.status,
        "created_ts": row.created_ts,
        "updated_ts": row.updated_ts,
        "meta": row.meta,
    }
    if args.format == "json":
        _print_json(payload)
    else:
        _print_table(
            ["FIELD", "VALUE"],
            [[key, str(value)] for key, value in payload.items()],
        )
    return 0


def cmd_jobs_tail(args) -> int:
    bus = SQLiteBus(db_path=args.db)
    events = bus.tail(limit=args.limit, topic_prefix=args.topic_prefix)
    if args.job_id:
        events = [
            evt
            for evt in events
            if str((evt.payload or {}).get("job_id")) == str(args.job_id)
        ]

    if args.format == "json":
        payload = [
            {
                "ts": evt.ts,
                "topic": evt.topic,
                "payload": evt.payload,
            }
            for evt in events
        ]
        _print_json(payload)
        return 0

    rows = [
        [_format_ts(evt.ts), evt.topic, json.dumps(evt.payload, ensure_ascii=False)]
        for evt in events
    ]
    _print_table(["TS", "TOPIC", "PAYLOAD"], rows)
    return 0


def _stage_approval_index(store: ArtifactStore) -> dict[str, dict]:
    approvals = {}
    for approval in store.list(limit=500, kind="ai_stage_approval"):
        doc = store.get_json(approval.id) or {}
        rid = doc.get("request_id")
        if rid:
            approvals[str(rid)] = {"id": approval.id, "payload": doc}
    return approvals


def cmd_stages_list(args) -> int:
    store = ArtifactStore(args.artifact_root)
    approvals = _stage_approval_index(store)
    requests = store.list(limit=args.limit, kind="ai_stage_request")
    rows = []
    for req in requests:
        doc = store.get_json(req.id) or {}
        approved = str(req.id) in approvals
        rows.append(
            {
                "request_id": req.id,
                "job_id": doc.get("job_id"),
                "plan_id": doc.get("plan_id"),
                "step_index": doc.get("step_index"),
                "action_id": doc.get("action_id"),
                "risk": doc.get("risk"),
                "approved": approved,
                "created_ts": req.created_ts,
            }
        )

    if args.format == "json":
        _print_json(rows)
        return 0

    table_rows = [
        [
            str(row["request_id"]),
            str(row["job_id"] or "-"),
            str(row["step_index"] or "-"),
            str(row["action_id"] or "-"),
            str(row["risk"] or "-"),
            "yes" if row["approved"] else "no",
        ]
        for row in rows
    ]
    _print_table(["REQUEST", "JOB", "STEP", "ACTION", "RISK", "APPROVED"], table_rows)
    return 0


def cmd_stages_approve(args) -> int:
    from smolotchi.core.jobs import JobStore

    store = ArtifactStore(args.artifact_root)
    approvals = _stage_approval_index(store)
    if str(args.request_id) in approvals:
        print("ok: already approved")
        return 0
    stage_req = store.get_json(args.request_id)
    if not stage_req:
        print("error: stage request not found")
        return 2
    payload = {
        "request_id": args.request_id,
        "approved_by": args.approved_by,
        "ts": time.time(),
    }
    meta = store.put_json(
        kind="ai_stage_approval",
        title=f"AI Stage Approval {args.request_id}",
        payload=payload,
        tags=["ai", "stage", "approval"],
        meta={"request_id": args.request_id},
    )

    job_id = stage_req.get("job_id")
    step_index = stage_req.get("step_index")
    if job_id and step_index is not None:
        note = f"approval granted resume_from:{int(step_index)} stage_req:{args.request_id}"
        JobStore(args.db).mark_queued(str(job_id), note=note)

    if args.format == "json":
        _print_json({"approval_id": meta.id, "request_id": args.request_id})
    else:
        print(f"approved: {args.request_id} ({meta.id})")
    return 0


def cmd_health(args) -> int:
    store = ArtifactStore(args.artifact_root)
    latest = store.list(limit=1, kind="worker_health")
    if not latest:
        print("worker: no health artifacts")
        return 1
    meta = latest[0]
    doc = store.get_json(meta.id) or {}
    ts = doc.get("ts") or meta.created_ts
    payload = {
        "worker_artifact_id": meta.id,
        "worker_ts": ts,
        "worker_pid": doc.get("pid"),
        "job_id": doc.get("job_id"),
    }
    if args.format == "json":
        _print_json(payload)
    else:
        _print_table(
            ["FIELD", "VALUE"],
            [[key, str(value)] for key, value in payload.items()],
        )
    return 0
def cmd_job_cancel(args) -> int:
    from smolotchi.core.jobs import JobStore

    js = JobStore(args.db)
    ok = js.cancel(args.job_id)
    print("ok" if ok else "no-op")
    return 0 if ok else 1


def cmd_job_reset(args) -> int:
    from smolotchi.core.jobs import JobStore

    js = JobStore(args.db)
    ok = js.reset_running(args.job_id)
    print("ok" if ok else "no-op")
    return 0 if ok else 1


def cmd_job_delete(args) -> int:
    from smolotchi.core.jobs import JobStore

    js = JobStore(args.db)
    ok = js.delete(args.job_id)
    print("ok" if ok else "no-op")
    return 0 if ok else 1


def cmd_prune(args) -> int:
    from smolotchi.core.config import ConfigStore
    from smolotchi.core.jobs import JobStore
    from smolotchi.core.artifacts import ArtifactStore

    store = ConfigStore(args.config)
    cfg = store.load()
    bus = SQLiteBus(db_path=args.db)
    jobs = JobStore(args.db)
    artifacts = ArtifactStore(args.artifact_root)

    r = cfg.retention
    deleted_events = bus.prune(
        keep_last=r.events_keep_last,
        older_than_days=r.events_older_than_days,
        vacuum=r.vacuum_after_prune,
    )
    deleted_jobs = jobs.prune(
        keep_last=r.jobs_keep_last,
        done_failed_older_than_days=r.jobs_done_failed_older_than_days,
    )
    deleted_artifacts = artifacts.prune(
        keep_last=r.artifacts_keep_last,
        older_than_days=r.artifacts_older_than_days,
        kinds_keep_last=r.artifact_kinds_keep_last,
    )

    print(
        f"events_deleted={deleted_events} jobs_deleted={deleted_jobs} artifacts_deleted={deleted_artifacts}"
    )
    return 0


def cmd_handoff(args) -> int:
    bus = SQLiteBus(db_path=args.db)
    bus.publish("ui.handoff.request", {"tag": args.tag, "note": args.note})
    print("ok: published ui.handoff.request")
    return 0


def cmd_lan_done(args) -> int:
    bus = SQLiteBus(db_path=args.db)
    bus.publish("lan.done", {"note": args.note})
    print("ok: published lan.done")
    return 0


def cmd_diff_baseline_set(args) -> int:
    artifacts = ArtifactStore(args.artifact_root)
    state_path = state_path_for_artifacts(artifacts.root)
    state = load_state(state_path)
    state.baseline_host_summary_id = str(args.artifact_id or "").strip()
    save_state(state_path, state)
    print(f"baseline_host_summary_id={state.baseline_host_summary_id}")
    return 0


def cmd_diff_baseline_show(args) -> int:
    artifacts = ArtifactStore(args.artifact_root)
    state_path = state_path_for_artifacts(artifacts.root)
    state = load_state(state_path)
    print(state.baseline_host_summary_id or "")
    return 0


def _resolve_profile_key(cfg, ssid_or_key: str, profile_hash_hint: str | None) -> str:
    ssid_or_key = ssid_or_key.strip()
    if "." in ssid_or_key:
        return ssid_or_key
    if profile_hash_hint:
        return f"{ssid_or_key}.{profile_hash_hint}"
    from smolotchi.core.normalize import normalize_profile, profile_hash

    wcfg = getattr(cfg, "wifi", None)
    profiles = getattr(wcfg, "profiles", None) if wcfg else None
    profile = profiles.get(ssid_or_key) if isinstance(profiles, dict) else None
    if isinstance(profile, dict):
        norm, _ = normalize_profile(profile)
        return f"{ssid_or_key}.{profile_hash(norm)}"
    return ssid_or_key


def cmd_profile_timeline(args) -> int:
    artifacts = ArtifactStore()
    items = []
    for meta in artifacts.list(limit=args.limit, kind="profile_timeline"):
        payload = artifacts.get_json(meta.id) or {}
        if args.ssid and payload.get("ssid") != args.ssid:
            continue
        payload["artifact_id"] = meta.id
        items.append(payload)
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def cmd_baseline_show(args) -> int:
    from smolotchi.core.config import ConfigStore
    from smolotchi.reports.baseline import expected_findings_for_profile

    store = ConfigStore(args.config)
    cfg = store.load()
    profile_key = _resolve_profile_key(cfg, args.profile, args.hash)
    expected = sorted(expected_findings_for_profile(cfg, profile_key))
    print(json.dumps({"profile": profile_key, "expected_findings": expected}, indent=2))
    return 0


def cmd_baseline_diff(args) -> int:
    from smolotchi.core.config import ConfigStore
    from smolotchi.reports.baseline import expected_findings_for_profile

    store = ConfigStore(args.config)
    cfg = store.load()
    from_key = _resolve_profile_key(cfg, args.profile, args.from_hash)
    to_key = _resolve_profile_key(cfg, args.profile, args.to_hash)
    from_expected = set(expected_findings_for_profile(cfg, from_key))
    to_expected = set(expected_findings_for_profile(cfg, to_key))
    added = sorted(to_expected - from_expected)
    removed = sorted(from_expected - to_expected)
    print(
        json.dumps(
            {
                "profile_from": from_key,
                "profile_to": to_key,
                "added": added,
                "removed": removed,
            },
            indent=2,
        )
    )
    return 0


def cmd_finding_history(args) -> int:
    from smolotchi.reports.baseline import profile_key_for_job_meta

    artifacts = ArtifactStore()
    history = []
    for meta in artifacts.list(limit=args.limit, kind="lan_bundle"):
        bundle = artifacts.get_json(meta.id) or {}
        summary = bundle.get("host_summary") or {}
        state = None
        for finding in (summary.get("findings") or []):
            fid = str(finding.get("id") or finding.get("title") or "")
            if fid != args.finding_id:
                continue
            suppressed = bool(
                finding.get("suppressed") or finding.get("suppressed_by_policy")
            )
            state = "suppressed" if suppressed else "active"
            break
        if state is None:
            continue
        job_meta = (
            (bundle.get("job") or {}).get("meta")
            if isinstance(bundle.get("job"), dict)
            else {}
        )
        if not job_meta and isinstance(bundle.get("job_meta"), dict):
            job_meta = bundle.get("job_meta") or {}
        history.append(
            {
                "bundle_id": meta.id,
                "state": state,
                "ts": meta.created_ts,
                "profile": profile_key_for_job_meta(job_meta),
            }
        )
    history.sort(key=lambda x: x.get("ts") or 0)
    print(json.dumps(history, indent=2))
    return 0


def cmd_dossier_build(args) -> int:
    from smolotchi.core.dossier import build_lan_dossier
    from smolotchi.core.jobs import JobStore
    from smolotchi.core.lan_resolver import resolve_result_by_job_id

    os.environ["SMOLOTCHI_DB"] = args.db
    os.environ["SMOLOTCHI_ARTIFACT_ROOT"] = args.artifact_root

    artifacts = ArtifactStore(args.artifact_root)
    jobstore = JobStore(args.db)
    dossier_id = build_lan_dossier(
        job_id=args.job_id,
        scope=args.scope,
        reason="cli",
        artifacts=artifacts,
        jobstore=jobstore,
        resolve_result_by_job_id=resolve_result_by_job_id,
    )
    print(f"OK: stored lan_dossier artifact_id={dossier_id}")
    return 0


def _write_text(out_path: str | None, text: str) -> None:
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")
    else:
        print(text)


def _write_json(out_path: str | None, obj) -> None:
    data = json.dumps(obj, ensure_ascii=False, indent=2)
    _write_text(out_path, data)


def cmd_ai_replay(args) -> int:
    artifacts = ArtifactStore(artifact_root)
    plan = artifacts.get_json(args.plan) or {}
    run = artifacts.get_json(args.run) or {}
    res = evaluate_plan_run(plan, run)

    bundle_ids = (res.get("signal") or {}).get("bundles") or []
    bundles = []
    for bid in bundle_ids:
        b = artifacts.get_json(bid)
        if b:
            bundles.append(b)
    if bundles:
        res["baseline_delta"] = baseline_delta_from_bundles(bundles)
        res["reward_combined_v1"] = round(
            float(res["reward_proxy"]) + float(res["baseline_delta"]["delta_reward"]),
            6,
        )

    if args.format == "json":
        _write_json(args.out, res)
        return 0

    m = res["metrics"]
    md = []
    md.append("# AI Replay")
    md.append("")
    md.append(f"- plan_id: `{m['plan_id']}`")
    md.append(f"- run_id: `{m['run_id']}`")
    md.append(f"- status: **{m['run_status']}**")
    md.append(f"- steps: {m['steps_executed']}/{m['steps_planned']}")
    md.append(f"- total_time_s: {m['total_time_s']}")
    md.append(f"- reward_proxy: {res['reward_proxy']}")
    if m.get("error"):
        md.append(f"- error: `{m['error']}`")
    md.append("")
    _write_text(args.out, "\n".join(md))
    return 0


def cmd_ai_replay_batch(args) -> int:
    artifacts = ArtifactStore(artifact_root)

    runs = artifacts.list(limit=max(args.last, 1), kind="ai_plan_run")

    rows = []
    full = []
    for run_meta in runs[: args.last]:
        run_doc = artifacts.get_json(run_meta.id) or {}
        plan_id = run_doc.get("plan_id")

        plan_doc = {}
        if plan_id:
            plans = artifacts.list(limit=200, kind="ai_plan")
            for plan_meta in plans:
                plan_payload = artifacts.get_json(plan_meta.id) or {}
                if plan_payload.get("id") == plan_id:
                    plan_doc = plan_payload
                    break

        res = evaluate_plan_run(plan_doc, run_doc)
        bundle_ids = (res.get("signal") or {}).get("bundles") or []
        bundles = []
        for bid in bundle_ids:
            b = artifacts.get_json(bid)
            if b:
                bundles.append(b)
        if bundles:
            res["baseline_delta"] = baseline_delta_from_bundles(bundles)
            res["reward_combined_v1"] = round(
                float(res["reward_proxy"]) + float(res["baseline_delta"]["delta_reward"]),
                6,
            )
        row = metrics_row(res)
        full.append(res)
        rows.append(row)

    if args.format == "json":
        _write_json(args.out, {"rows": rows, "results": full})
        return 0

    if args.format == "jsonl":
        lines = [json.dumps(r, ensure_ascii=False) for r in rows]
        _write_text(args.out, "\n".join(lines))
        return 0

    header = list(rows[0].keys()) if rows else [
        "plan_id",
        "run_id",
        "status",
        "steps_planned",
        "steps_executed",
        "total_time_s",
        "avg_step_s",
        "artifacts_linked",
        "reports_linked",
        "bundles_linked",
        "jobs_linked",
        "reward_proxy",
        "baseline_delta_reward",
        "baseline_changed_hosts",
        "reward_combined_v1",
        "error",
    ]
    out_lines = [",".join(header)]
    for row in rows:
        out_lines.append(",".join([str(row.get(k, "")).replace(",", ";") for k in header]))
    _write_text(args.out, "\n".join(out_lines))
    return 0


def _write_unit(dst: Path, content: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")


def cmd_install_systemd(args) -> int:
    """
    Installiert systemd units nach /etc/systemd/system.
    """
    if os.geteuid() != 0:
        print("error: run as root (sudo).")
        return 2

    proj = Path(args.project_dir).resolve()
    venv_python = proj / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print(f"error: {venv_python} not found. Create venv first.")
        return 2

    user = args.user
    db = args.db

    core_unit = f"""[Unit]
Description=Smolotchi Core
After=network.target

[Service]
User={user}
WorkingDirectory={proj}
Environment=PYTHONUNBUFFERED=1
Environment=SMOLOTCHI_DB={db}
ExecStart={venv_python} -m smolotchi.cli core --db {db} --allowed-tag lab-approved
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

    web_unit = f"""[Unit]
Description=Smolotchi Web UI (Flask)
After=network.target smolotchi-core.service

[Service]
User={user}
WorkingDirectory={proj}
Environment=PYTHONUNBUFFERED=1
Environment=SMOLOTCHI_DB={db}
ExecStart={venv_python} -m smolotchi.cli web --host 127.0.0.1 --port 8080
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

    ai_worker_unit = f"""[Unit]
Description=Smolotchi AI Worker
After=network.target smolotchi-core.service

[Service]
User={user}
WorkingDirectory={proj}
Environment=PYTHONUNBUFFERED=1
Environment=SMOLOTCHI_DB={db}
ExecStart={venv_python} -m smolotchi.ai.worker --loop --log-level INFO
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

    disp_unit = f"""[Unit]
Description=Smolotchi ePaper display daemon
After=network.target smolotchi-core.service

[Service]
User={user}
WorkingDirectory={proj}
Environment=PYTHONUNBUFFERED=1
Environment=SMOLOTCHI_DB={db}
ExecStart={venv_python} -m smolotchi.cli display
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

    _write_unit(Path("/etc/systemd/system/smolotchi-core.service"), core_unit)
    _write_unit(Path("/etc/systemd/system/smolotchi-web.service"), web_unit)
    _write_unit(Path("/etc/systemd/system/smolotchi-ai-worker.service"), ai_worker_unit)
    _write_unit(Path("/etc/systemd/system/smolotchi-display.service"), disp_unit)

    subprocess.check_call(["systemctl", "daemon-reload"])
    print("ok: installed units. Enable/start with:")
    print(
        "  sudo systemctl enable --now smolotchi-core smolotchi-web smolotchi-ai-worker smolotchi-display"
    )
    return 0


def add_ai_subcommands(subparsers) -> None:
    ai = subparsers.add_parser("ai", help="AI tools (planner replay/eval)")
    ai_sub = ai.add_subparsers(dest="ai_cmd", required=True)

    replay = ai_sub.add_parser("replay", help="Evaluate one plan+run (offline)")
    replay.add_argument("--plan", required=True, help="ai_plan artifact_id")
    replay.add_argument("--run", required=True, help="ai_plan_run artifact_id")
    replay.add_argument("--out", default=None, help="Write output to file (default: stdout)")
    replay.add_argument("--format", choices=["json", "md"], default="json")
    replay.set_defaults(fn=cmd_ai_replay)

    batch = ai_sub.add_parser("replay-batch", help="Evaluate last N ai_plan_run artifacts")
    batch.add_argument("--last", type=int, default=20, help="How many runs to evaluate")
    batch.add_argument("--out", default=None, help="Write output to file (default: stdout)")
    batch.add_argument("--format", choices=["jsonl", "csv", "json"], default="jsonl")
    batch.set_defaults(fn=cmd_ai_replay_batch)


def build_parser() -> argparse.ArgumentParser:
    default_db = resolve_db_path()
    default_artifact_root = resolve_artifact_root()
    default_tag = resolve_default_tag()
    p = argparse.ArgumentParser(
        prog="smolotchi",
        description="Smolotchi (Pi Zero 2 W) – core/web/display CLI",
    )
    p.add_argument(
        "--db",
        default=default_db,
        help=f"SQLite DB path (default: {default_db})",
    )
    p.add_argument(
        "--artifact-root",
        default=default_artifact_root,
        help="Artifact store root path",
    )
    p.add_argument(
        "--config",
        default=resolve_config_path(),
        help="Path to config.toml (default: config.toml)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("web", help="Run Flask web UI")
    s.add_argument("--host", default=None)
    s.add_argument("--port", type=int, default=None)
    s.set_defaults(fn=cmd_web)

    s = sub.add_parser("display", help="Run e-paper display daemon")
    s.add_argument("--device", default=resolve_device())
    s.add_argument("--db", default=default_db)
    s.add_argument("--artifact-root", default=default_artifact_root)
    s.set_defaults(fn=cmd_display)

    s = sub.add_parser("core", help="Run core state-machine daemon")
    s.add_argument("--interval", type=float, default=None)
    s.add_argument(
        "--allowed-tag",
        dest="allowed_tags",
        action="append",
        default=None,
        help="Allowlist tags for handoff (repeatable)",
    )
    s.set_defaults(fn=cmd_core)

    s = sub.add_parser("status", help="Show current state")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("events", help="Print recent events")
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--topic-prefix", default=None)
    s.set_defaults(fn=cmd_events)

    wifi = sub.add_parser("wifi", help="WiFi utilities")
    wifi_sub = wifi.add_subparsers(dest="wifi_cmd", required=True)

    s = wifi_sub.add_parser("scan", help="Scan nearby WiFi networks")
    s.add_argument("--iface", default=None)
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_wifi_scan)

    s = wifi_sub.add_parser(
        "connect", help="Connect to WiFi using config credentials"
    )
    s.add_argument("ssid")
    s.add_argument("--iface", default=None)
    s.set_defaults(fn=cmd_wifi_connect)

    s = wifi_sub.add_parser("status", help="Show WiFi CIDR + derived scope")
    s.add_argument("--iface", default=None)
    s.set_defaults(fn=cmd_wifi_status)

    jobs = sub.add_parser("jobs", help="Job utilities")
    jobs_sub = jobs.add_subparsers(dest="jobs_cmd", required=True)

    s = jobs_sub.add_parser("enqueue", help="Enqueue a job")
    s.add_argument("--kind", required=True)
    s.add_argument("--scope", required=True)
    s.add_argument("--note", default="")
    s.add_argument("--job-id", default=None)
    s.set_defaults(fn=cmd_jobs_enqueue)

    s = jobs_sub.add_parser("list", help="List jobs")
    s.add_argument("--status", action="append", default=None, help="Filter by status")
    s.add_argument("--kind", default=None, help="Filter by job kind")
    s.add_argument(
        "--note-contains",
        dest="note_contains",
        default=None,
        help="Filter by note substring",
    )
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--format", choices=["json", "table"], default="table")
    s.set_defaults(fn=cmd_jobs_list)

    s = jobs_sub.add_parser("get", help="Get job details")
    s.add_argument("job_id")
    s.add_argument("--format", choices=["json", "table"], default="json")
    s.set_defaults(fn=cmd_jobs_get)

    s = jobs_sub.add_parser("tail", help="Tail job-related events")
    s.add_argument("--job-id", default=None, help="Filter by job id")
    s.add_argument("--topic-prefix", default=None)
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--format", choices=["json", "table"], default="table")
    s.set_defaults(fn=cmd_jobs_tail)

    s = sub.add_parser("job-cancel", help="Cancel queued job")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_job_cancel)

    s = sub.add_parser("job-reset", help="Reset running job to queued")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_job_reset)

    s = sub.add_parser("job-delete", help="Delete job")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_job_delete)

    stages = sub.add_parser("stages", help="Stage approvals")
    stages_sub = stages.add_subparsers(dest="stages_cmd", required=True)
    s = stages_sub.add_parser("list", help="List stage requests")
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--format", choices=["json", "table"], default="table")
    s.set_defaults(fn=cmd_stages_list)
    s = stages_sub.add_parser("approve", help="Approve a stage request")
    s.add_argument("request_id")
    s.add_argument("--approved-by", default="cli")
    s.add_argument("--format", choices=["json", "table"], default="table")
    s.set_defaults(fn=cmd_stages_approve)

    s = sub.add_parser("health", help="Show worker health")
    s.add_argument("--format", choices=["json", "table"], default="table")
    s.set_defaults(fn=cmd_health)

    s = sub.add_parser("prune", help="Run retention prune once")
    s.set_defaults(fn=cmd_prune)

    s = sub.add_parser("handoff", help="Request handoff to LAN_OPS (publishes event)")
    s.add_argument("--tag", default=default_tag)
    s.add_argument("--note", default="")
    s.set_defaults(fn=cmd_handoff)

    s = sub.add_parser("lan-done", help="Mark LAN ops done (publishes event)")
    s.add_argument("--note", default="manual done")
    s.set_defaults(fn=cmd_lan_done)

    s = sub.add_parser("diff-baseline-set", help="Set baseline host_summary artifact id")
    s.add_argument("artifact_id")
    s.set_defaults(fn=cmd_diff_baseline_set)

    s = sub.add_parser("diff-baseline-show", help="Show baseline host_summary artifact id")
    s.set_defaults(fn=cmd_diff_baseline_show)

    profile = sub.add_parser("profile", help="Profile timeline utilities")
    profile_sub = profile.add_subparsers(dest="profile_cmd", required=True)
    s = profile_sub.add_parser("timeline", help="Show profile timeline by SSID")
    s.add_argument("ssid")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_profile_timeline)

    dossier = sub.add_parser("dossier", help="Dossier utilities (timeline merge)")
    dossier_sub = dossier.add_subparsers(dest="dossier_cmd", required=True)
    s = dossier_sub.add_parser("build", help="Build merged dossier for a LAN job_id")
    s.add_argument("--job-id", required=True)
    s.add_argument("--scope", default="")
    s.set_defaults(fn=cmd_dossier_build)

    baseline = sub.add_parser("baseline", help="Baseline utilities")
    baseline_sub = baseline.add_subparsers(dest="baseline_cmd", required=True)
    s = baseline_sub.add_parser("show", help="Show baseline for profile")
    s.add_argument("profile")
    s.add_argument("--hash", dest="hash", default=None)
    s.set_defaults(fn=cmd_baseline_show)
    s = baseline_sub.add_parser("diff", help="Diff baseline between profile hashes")
    s.add_argument("profile")
    s.add_argument("--from", dest="from_hash", required=True)
    s.add_argument("--to", dest="to_hash", required=True)
    s.set_defaults(fn=cmd_baseline_diff)

    finding = sub.add_parser("finding", help="Finding history utilities")
    finding_sub = finding.add_subparsers(dest="finding_cmd", required=True)
    s = finding_sub.add_parser("history", help="Show finding history across bundles")
    s.add_argument("finding_id")
    s.add_argument("--limit", type=int, default=200)
    s.set_defaults(fn=cmd_finding_history)

    s = sub.add_parser("install-systemd", help="Install systemd units (needs sudo)")
    s.add_argument("--project-dir", default=".", help="Path to smolotchi project root")
    s.add_argument("--user", default=os.environ.get("SUDO_USER", "pi"))
    s.add_argument("--db", default=default_db)
    s.set_defaults(fn=cmd_install_systemd)

    add_ai_subcommands(sub)
    add_profiles_subcommands(sub)
    add_artifacts_subcommands(sub)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
