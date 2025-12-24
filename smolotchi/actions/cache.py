from __future__ import annotations

from typing import Any, Dict, Optional
import time

from smolotchi.actions.parse import parse_nmap_xml_up_hosts
from smolotchi.core.artifacts import ArtifactStore


def find_fresh_discovery(
    artifacts: ArtifactStore, ttl_s: int
) -> Optional[Dict[str, Any]]:
    """
    Find newest action_run for net.host_discovery within ttl.
    Returns dict {artifact_id, hosts, ts}.
    """
    now = time.time()
    items = artifacts.list(limit=200, kind="action_run")
    for meta in items:
        data = artifacts.get_json(meta.id) or {}
        spec = data.get("spec") or {}
        if spec.get("id") != "net.host_discovery":
            continue
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        ts = float(payload.get("ts", data.get("ts", meta.created_ts)))
        ts = ts if ts > 0 else meta.created_ts
        if now - ts > ttl_s:
            continue
        stdout = data.get("stdout", "") or ""
        hosts = parse_nmap_xml_up_hosts(stdout)
        return {"artifact_id": meta.id, "hosts": hosts, "ts": ts}
    return None
