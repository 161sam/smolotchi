from __future__ import annotations

from typing import Any, Dict, List, Tuple

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.reports.nmap_classify import classify_scripts
from smolotchi.reports.nmap_findings import parse_nmap_xml_findings


def extract_findings_for_host_from_action_run(
    artifacts: ArtifactStore, artifact_id: str, host: str
) -> Dict[str, Any]:
    art = artifacts.get_json(artifact_id) or {}
    stdout = art.get("stdout") or ""
    parsed = parse_nmap_xml_findings(stdout)
    host_data = (parsed.get("hosts") or {}).get(host) or {"ports": [], "scripts": []}
    host_data["scripts"] = classify_scripts(host_data.get("scripts") or [])
    return host_data


def build_host_findings(
    artifacts: ArtifactStore,
    host_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Returns: { host: { ports:[...], scripts:[...], sources:[{action_id,artifact_id}] } }
    """
    hosts = host_summary.get("hosts") or {}
    refs = host_summary.get("artifacts") or []

    host_refs: Dict[str, List[Tuple[str, str]]] = {h: [] for h in hosts.keys()}

    for ref in refs:
        action_id = ref.get("action_id")
        art_id = ref.get("artifact_id")
        if not art_id:
            continue
        art = artifacts.get_json(art_id) or {}
        payload = art.get("payload") if isinstance(art.get("payload"), dict) else {}
        target = str((payload or {}).get("target") or "")
        if not target:
            continue
        host_refs.setdefault(target, []).append((str(action_id), str(art_id)))

    out: Dict[str, Any] = {}
    for host in hosts.keys():
        items = host_refs.get(host, [])

        primary_portscan = None
        for action_id, art_id in items:
            if action_id == "net.port_scan":
                primary_portscan = art_id
                break

        ports = []
        scripts: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = [
            {"action_id": action_id, "artifact_id": art_id} for action_id, art_id in items
        ]

        if primary_portscan:
            parsed = extract_findings_for_host_from_action_run(
                artifacts, primary_portscan, host
            )
            ports = parsed.get("ports") or []
            scripts.extend(parsed.get("scripts") or [])

        for action_id, art_id in items:
            if not action_id.startswith("vuln."):
                continue
            parsed = extract_findings_for_host_from_action_run(artifacts, art_id, host)
            scripts.extend(parsed.get("scripts") or [])

        seen = set()
        deduped = []
        for script in scripts:
            key = (script.get("scope"), script.get("id"), script.get("output"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(script)

        deduped.sort(
            key=lambda x: (
                0 if x.get("tag") == "vuln" else 1,
                x.get("scope", ""),
                x.get("id", ""),
            )
        )
        out[host] = {"ports": ports, "scripts": deduped, "sources": sources}

    return out
