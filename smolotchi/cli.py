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

    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
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
    bus = SQLiteBus(db_path=args.db)
    policy = Policy(allowed_tags=args.allowed_tags)
    core = SmolotchiCore(bus=bus, policy=policy)

    bus.publish("core.started", {"pid": os.getpid()})
    try:
        while True:
            core.tick()
            time.sleep(args.interval)
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

    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("web", help="Run Flask web UI")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=8080)
    s.set_defaults(fn=cmd_web)

    s = sub.add_parser("display", help="Run e-paper display daemon")
    s.set_defaults(fn=cmd_display)

    s = sub.add_parser("core", help="Run core state-machine daemon")
    s.add_argument("--interval", type=float, default=1.0)
    s.add_argument(
        "--allowed-tag",
        dest="allowed_tags",
        action="append",
        default=["lab-approved"],
        help="Allowlist tags for handoff (repeatable)",
    )
    s.set_defaults(fn=cmd_core)

    s = sub.add_parser("status", help="Show current state")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("events", help="Print recent events")
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--topic-prefix", default=None)
    s.set_defaults(fn=cmd_events)

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
