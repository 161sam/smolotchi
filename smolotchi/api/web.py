import json
import time

from flask import Flask, Response, abort, redirect, render_template, request, url_for

from smolotchi.api.theme import load_theme_tokens, tokens_to_css_vars
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.config import ConfigStore


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

    @app.get("/lan/results")
    def lan_results():
        items = artifacts.list(limit=50, kind="lan_result")
        return render_template("lan_results.html", items=items)

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

    @app.get("/config")
    def config():
        cfg = store.get()
        return render_template("config.html", cfg=cfg)

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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=False)
