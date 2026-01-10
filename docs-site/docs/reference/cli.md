# CLI Reference

The CLI is built with `argparse` in `smolotchi/cli.py` and is invoked via `smolotchi.cli.main`.

Code: smolotchi/cli.py:build_parser, smolotchi/cli.py:main

## Top-level help (`python -m smolotchi.cli --help`)

```
usage: smolotchi [-h] [--db DB] [--artifact-root ARTIFACT_ROOT]
                 [--config CONFIG]
                 {web,display,core,status,events,wifi,jobs,job-cancel,job-reset,job-delete,stages,health,prune,handoff,lan-done,diff-baseline-set,diff-baseline-show,profile,dossier,baseline,finding,install-systemd,ai,profiles,artifacts,locks}
                 ...

Smolotchi (Pi Zero 2 W) – core/web/display CLI

positional arguments:
  {web,display,core,status,events,wifi,jobs,job-cancel,job-reset,job-delete,stages,health,prune,handoff,lan-done,diff-baseline-set,diff-baseline-show,profile,dossier,baseline,finding,install-systemd,ai,profiles,artifacts,locks}
    web                 Run Flask web UI
    display             Run e-paper display daemon
    core                Run core state-machine daemon
    status              Show current state
    events              Print recent events
    wifi                WiFi utilities
    jobs                Job utilities
    job-cancel          Cancel queued job
    job-reset           Reset running job to queued
    job-delete          Delete job
    stages              Stage approvals
    health              Show worker health
    prune               Run retention prune once
    handoff             Request handoff to LAN_OPS (publishes event)
    lan-done            Mark LAN ops done (publishes event)
    diff-baseline-set   Set baseline host_summary artifact id
    diff-baseline-show  Show baseline host_summary artifact id
    profile             Profile timeline utilities
    dossier             Dossier utilities (timeline merge)
    baseline            Baseline utilities
    finding             Finding history utilities
    install-systemd     Install systemd units (needs sudo)
    ai                  AI tools (planner replay/eval)
    profiles            WiFi profile utilities
    artifacts           Artifact store utilities
    locks               Lock leak detection utilities

options:
  -h, --help            show this help message and exit
  --db DB               SQLite DB path (default: /var/lib/smolotchi/events.db)
  --artifact-root ARTIFACT_ROOT
                        Artifact store root path
  --config CONFIG       Path to config.toml (default: config.toml)
```

Code: smolotchi/cli.py:build_parser
