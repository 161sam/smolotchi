from __future__ import annotations

from typing import Any, Dict
import time


def build_host_summary(
    plan_run: Dict[str, Any],
    fp_by_host: Dict[str, Any],
    host_sev: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    hosts = {}
    for host, fp in fp_by_host.items():
        hosts[host] = {
            "fp": fp.get("fp"),
            "fp_by_key": fp.get("fp_by_key"),
            "ports_by_key": fp.get("ports_by_key"),
        }
        if host_sev and host in host_sev:
            hosts[host]["sev_counts"] = host_sev[host].get("sev_counts", {})
            hosts[host]["sev_highest"] = host_sev[host].get("sev_highest", "info")

    steps = plan_run.get("steps", []) or []
    artifacts: list[dict[str, Any]] = []
    for step in steps:
        action_id = step.get("action_id")
        artifact_id = step.get("artifact_id")
        if not artifact_id:
            continue
        artifacts.append(
            {
                "action_id": action_id,
                "artifact_id": artifact_id,
                "ok": step.get("ok"),
            }
        )

    return {
        "ts": time.time(),
        "plan_id": plan_run.get("plan_id"),
        "scope": plan_run.get("scope"),
        "hosts": hosts,
        "artifacts": artifacts,
    }
