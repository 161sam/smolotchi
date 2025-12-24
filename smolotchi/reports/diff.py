from __future__ import annotations

from typing import Any, Dict, List, Optional
import time

from smolotchi.core.artifacts import ArtifactStore

SEV_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def find_previous_host_summary(
    artifacts: ArtifactStore,
    current_id: str,
    window_s: int,
) -> Optional[str]:
    now = time.time()
    items = artifacts.list(limit=50, kind="host_summary")
    for item in items:
        if item.id == current_id:
            continue
        data = artifacts.get_json(item.id) or {}
        ts = float(data.get("ts", item.created_ts) or item.created_ts)
        if now - ts > window_s:
            continue
        return item.id
    return None


def resolve_baseline_host_summary(
    artifacts: ArtifactStore,
    current_id: str,
    window_s: int,
    baseline_id: str | None = None,
) -> Optional[str]:
    baseline_id = (baseline_id or "").strip()
    if baseline_id:
        data = artifacts.get_json(baseline_id)
        if isinstance(data, dict) and data.get("hosts") is not None:
            return baseline_id
        return None
    return find_previous_host_summary(
        artifacts, current_id=current_id, window_s=window_s
    )


def _ports_union(host: dict) -> List[int]:
    ports_by_key = host.get("ports_by_key") or {}
    ports = set(
        (ports_by_key.get("http") or [])
        + (ports_by_key.get("ssh") or [])
        + (ports_by_key.get("smb") or [])
    )
    return sorted(list(ports))


def _sev_highest(counts: dict) -> str:
    for sev in ("critical", "high", "medium", "low", "info"):
        if int((counts or {}).get(sev, 0)) > 0:
            return sev
    return "info"


def diff_host_summaries(
    prev: Dict[str, Any],
    cur: Dict[str, Any],
    *,
    max_hosts: int = 50,
) -> Dict[str, Any]:
    prev_hosts = prev.get("hosts") or {}
    cur_hosts = cur.get("hosts") or {}

    all_hosts = sorted(set(prev_hosts.keys()) | set(cur_hosts.keys()))
    all_hosts = all_hosts[:max_hosts]

    added = [h for h in all_hosts if h not in prev_hosts and h in cur_hosts]
    removed = [h for h in all_hosts if h in prev_hosts and h not in cur_hosts]
    changed = []

    for host in all_hosts:
        if host not in prev_hosts or host not in cur_hosts:
            continue
        prev_host = prev_hosts[host]
        cur_host = cur_hosts[host]

        prev_ports = _ports_union(prev_host)
        cur_ports = _ports_union(cur_host)
        if prev_ports != cur_ports:
            changed.append(
                {"host": host, "type": "ports", "prev": prev_ports, "cur": cur_ports}
            )

        prev_fp = prev_host.get("fp_by_key") or {}
        cur_fp = cur_host.get("fp_by_key") or {}
        fp_changes = {}
        for key in ("http", "ssh", "smb"):
            if str(prev_fp.get(key, "")) != str(cur_fp.get(key, "")):
                fp_changes[key] = {
                    "prev": str(prev_fp.get(key, ""))[:8],
                    "cur": str(cur_fp.get(key, ""))[:8],
                }
        if fp_changes:
            changed.append({"host": host, "type": "fingerprints", "changes": fp_changes})

        prev_sev = prev_host.get("sev_counts") or {}
        cur_sev = cur_host.get("sev_counts") or {}
        keys = ("critical", "high", "medium", "low", "info")
        prev_norm = {key: int(prev_sev.get(key, 0) or 0) for key in keys}
        cur_norm = {key: int(cur_sev.get(key, 0) or 0) for key in keys}
        if prev_norm != cur_norm:
            changed.append(
                {
                    "host": host,
                    "type": "severity_counts",
                    "prev": prev_norm,
                    "cur": cur_norm,
                    "prev_highest": str(prev_host.get("sev_highest", "info")),
                    "cur_highest": str(cur_host.get("sev_highest", "info")),
                }
            )

    return {
        "prev_id": prev.get("artifact_id"),
        "cur_id": cur.get("artifact_id"),
        "ts_prev": prev.get("ts"),
        "ts_cur": cur.get("ts"),
        "hosts_added": added,
        "hosts_removed": removed,
        "changes": changed,
    }
