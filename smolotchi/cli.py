import argparse
import os
import subprocess
import time
from pathlib import Path

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.policy import Policy
from smolotchi.core.state import SmolotchiCore

DEFAULT_DB = os.environ.get("SMOLOTCHI_DB", "/var/lib/smolotchi/events.db")
DEFAULT_TAG = os.environ.get("SMOLOTCHI_DEFAULT_TAG", "lab-approved")


def cmd_web(args) -> int:
    from smolotchi.api.web import create_app
    from smolotchi.core.config import ConfigStore

    store = ConfigStore(args.config)
    cfg = store.load()

    app = create_app(config_path=args.config)
    host = args.host or cfg.ui.host
    port = args.port or cfg.ui.port
    app.run(host=host, port=port, debug=False)
    return 0


def cmd_display(args) -> int:
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
    from smolotchi.engines.lan_engine import LanConfig, LanEngine
    from smolotchi.engines.wifi_engine import WifiConfig, WifiEngine

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

    artifacts = ArtifactStore("/var/lib/smolotchi/artifacts")
    jobs = JobStore(args.db)
    resources = ResourceManager("/run/smolotchi/locks")
    renderer = (
        ReportRenderer(ReportConfig(templates_dir=cfg.reports.templates_dir))
        if cfg.reports.enabled
        else None
    )

    reg = EngineRegistry()
    reg.register(
        WifiEngine(
            bus,
            WifiConfig(
                enabled=cfg.wifi.enabled,
                safe_mode=cfg.wifi.safe_mode,
            ),
        )
    )
    from smolotchi.actions.plan_runner import PlanRunner
    from smolotchi.actions.planners.ai_planner import AIPlanner
    from smolotchi.actions.registry import load_pack
    from smolotchi.actions.runner import ActionRunner

    actions = load_pack("smolotchi/actions/packs/bjorn_core.yml")
    action_runner = ActionRunner(bus=bus, artifacts=artifacts, policy=policy)
    plan_runner = PlanRunner(
        bus=bus, registry=actions, runner=action_runner, artifacts=artifacts
    )
    planner = AIPlanner(bus=bus, registry=actions)

    reg.register(
        LanEngine(
            bus,
            LanConfig(
                enabled=cfg.lan.enabled,
                safe_mode=cfg.lan.safe_mode,
                max_jobs_per_tick=cfg.lan.max_jobs_per_tick,
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
                "diff": {
                    "enabled": cfg.report_diff.enabled,
                    "compare_window_seconds": cfg.report_diff.compare_window_seconds,
                    "max_hosts": cfg.report_diff.max_hosts,
                },
            },
        )
    )

    core = SmolotchiCore(bus=bus, policy=policy, engines=reg, resources=resources)
    core.set_state(cfg.core.default_state, "default from config")

    bus.publish("core.started", {"pid": os.getpid(), "config": args.config})
    try:
        while True:
            new_cfg = store.get()
            wifi = reg.get("wifi")
            lan = reg.get("lan")
            if wifi:
                wifi.cfg.enabled = new_cfg.wifi.enabled
                wifi.cfg.safe_mode = new_cfg.wifi.safe_mode
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
                    },
                }
            if not hasattr(cmd_core, "_last_prune"):
                cmd_core._last_prune = 0.0  # type: ignore[attr-defined]
            if not hasattr(cmd_core, "_last_wd"):
                cmd_core._last_wd = 0.0  # type: ignore[attr-defined]

            now = time.time()
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
            if now - cmd_core._last_wd > 10.0:  # type: ignore[attr-defined]
                cmd_core._last_wd = now  # type: ignore[attr-defined]
                wd = new_cfg.watchdog
                if wd.enabled:
                    if wd.action == "fail":
                        n = jobs.fail_stuck(
                            older_than_seconds=wd.running_stuck_after_seconds,
                            limit=50,
                        )
                        if n:
                            bus.publish(
                                "core.watchdog",
                                {
                                    "action": "fail",
                                    "count": n,
                                    "after_s": wd.running_stuck_after_seconds,
                                },
                            )
                    else:
                        n = jobs.reset_stuck(
                            older_than_seconds=wd.running_stuck_after_seconds,
                            limit=50,
                        )
                        if n:
                            bus.publish(
                                "core.watchdog",
                                {
                                    "action": "reset",
                                    "count": n,
                                    "after_s": wd.running_stuck_after_seconds,
                                },
                            )
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


def cmd_jobs(args) -> int:
    from smolotchi.core.jobs import JobStore

    js = JobStore(args.db)
    rows = js.list(limit=args.limit, status=args.status)
    for j in rows:
        print(f"{j.status:7} {j.id} {j.kind} {j.scope} {j.note}".strip())
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
    artifacts = ArtifactStore("/var/lib/smolotchi/artifacts")

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
ExecStart={venv_python} -m smolotchi.cli web --host 0.0.0.0 --port 8080
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
    _write_unit(Path("/etc/systemd/system/smolotchi-display.service"), disp_unit)

    subprocess.check_call(["systemctl", "daemon-reload"])
    print("ok: installed units. Enable/start with:")
    print("  sudo systemctl enable --now smolotchi-core smolotchi-web smolotchi-display")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="smolotchi",
        description="Smolotchi (Pi Zero 2 W) – core/web/display CLI",
    )
    p.add_argument("--db", default=DEFAULT_DB, help=f"SQLite DB path (default: {DEFAULT_DB})")
    p.add_argument(
        "--config",
        default=os.environ.get("SMOLOTCHI_CONFIG", "config.toml"),
        help="Path to config.toml (default: config.toml)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("web", help="Run Flask web UI")
    s.add_argument("--host", default=None)
    s.add_argument("--port", type=int, default=None)
    s.set_defaults(fn=cmd_web)

    s = sub.add_parser("display", help="Run e-paper display daemon")
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

    s = sub.add_parser("jobs", help="List jobs")
    s.add_argument("--status", default=None)
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_jobs)

    s = sub.add_parser("job-cancel", help="Cancel queued job")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_job_cancel)

    s = sub.add_parser("job-reset", help="Reset running job to queued")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_job_reset)

    s = sub.add_parser("job-delete", help="Delete job")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_job_delete)

    s = sub.add_parser("prune", help="Run retention prune once")
    s.set_defaults(fn=cmd_prune)

    s = sub.add_parser("handoff", help="Request handoff to LAN_OPS (publishes event)")
    s.add_argument("--tag", default=DEFAULT_TAG)
    s.add_argument("--note", default="")
    s.set_defaults(fn=cmd_handoff)

    s = sub.add_parser("lan-done", help="Mark LAN ops done (publishes event)")
    s.add_argument("--note", default="manual done")
    s.set_defaults(fn=cmd_lan_done)

    s = sub.add_parser("install-systemd", help="Install systemd units (needs sudo)")
    s.add_argument("--project-dir", default=".", help="Path to smolotchi project root")
    s.add_argument("--user", default=os.environ.get("SUDO_USER", "pi"))
    s.add_argument("--db", default=DEFAULT_DB)
    s.set_defaults(fn=cmd_install_systemd)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
