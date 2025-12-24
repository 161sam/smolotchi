from __future__ import annotations

from typing import Any, Dict, Optional
import time

from smolotchi.actions.fingerprint import service_fingerprint
from smolotchi.actions.parse import parse_nmap_xml_up_hosts
from smolotchi.actions.parse_services import parse_nmap_xml_services
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


def find_fresh_portscan_for_host(
    artifacts: ArtifactStore, host: str, ttl_s: int
) -> Optional[Dict[str, Any]]:
    """
    Find newest action_run for net.port_scan with payload.target==host within ttl.
    Returns {artifact_id, services, ts}.
    """
    now = time.time()
    items = artifacts.list(limit=400, kind="action_run")
    for meta in items:
        data = artifacts.get_json(meta.id) or {}
        spec = data.get("spec") or {}
        if spec.get("id") != "net.port_scan":
            continue

        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        tgt = str((payload or {}).get("target", ""))
        if tgt != host:
            continue

        ts = float(data.get("ts", meta.created_ts) or meta.created_ts)
        if now - ts > ttl_s:
            continue

        stdout = (data.get("stdout") or "")
        svc_by_host = parse_nmap_xml_services(stdout)
        services = svc_by_host.get(host, [])
        return {"artifact_id": meta.id, "services": services, "ts": ts}

    return None


def find_fresh_vuln_for_host_action(
    artifacts: ArtifactStore,
    host: str,
    action_id: str,
    ttl_s: int,
    expected_fp: str | None = None,
) -> Optional[Dict[str, Any]]:
    """
    Find newest action_run for vuln_* action with payload.target==host within ttl.
    If expected_fp is provided, require payload._svc_fp == expected_fp.
    """
    now = time.time()
    items = artifacts.list(limit=600, kind="action_run")
    for meta in items:
        data = artifacts.get_json(meta.id) or {}
        spec = data.get("spec") or {}
        if spec.get("id") != action_id:
            continue

        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        tgt = str((payload or {}).get("target", ""))
        if tgt != host:
            continue
        if expected_fp:
            if str((payload or {}).get("_svc_fp", "")) != expected_fp:
                continue

        ts = float(data.get("ts", meta.created_ts) or meta.created_ts)
        if now - ts > ttl_s:
            continue

        return {"artifact_id": meta.id, "ts": ts}
    return None


def put_service_fingerprint(
    artifacts: ArtifactStore, host: str, services: list, source: str
) -> str:
    fp = service_fingerprint(services)
    meta = artifacts.put_json(
        kind="svc_fingerprint",
        title=f"FP • {host}",
        payload={
            "host": host,
            "fp": fp,
            "count": len(services or []),
            "services": services,
            "source": source,
            "ts": time.time(),
        },
    )
    return meta.id


def find_latest_fingerprint(
    artifacts: ArtifactStore, host: str, ttl_s: int = 3600
) -> Optional[dict]:
    now = time.time()
    items = artifacts.list(limit=200, kind="svc_fingerprint")
    for meta in items:
        data = artifacts.get_json(meta.id) or {}
        if str(data.get("host", "")) != host:
            continue
        ts = float(data.get("ts", meta.created_ts) or meta.created_ts)
        if now - ts > ttl_s:
            continue
        return data
    return None
