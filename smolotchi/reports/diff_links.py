from __future__ import annotations

from typing import Any, Dict, List

from smolotchi.core.artifacts import ArtifactStore

WANTED_PREFIXES = ("net.port_scan", "vuln.")


def index_host_actions(
    artifacts: ArtifactStore, host_summary: Dict[str, Any]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Returns: host -> action_id -> [artifact_id, ...]
    Uses host_summary["artifacts"] list and action_run payload.target.
    """
    refs = host_summary.get("artifacts") or []
    out: Dict[str, Dict[str, List[str]]] = {}

    for ref in refs:
        action_id = str(ref.get("action_id") or "")
        art_id = str(ref.get("artifact_id") or "")
        if not action_id or not art_id:
            continue
        if not (action_id == "net.port_scan" or action_id.startswith("vuln.")):
            continue

        art = artifacts.get_json(art_id) or {}
        payload = art.get("payload") if isinstance(art.get("payload"), dict) else {}
        host = str((payload or {}).get("target") or "")
        if not host:
            continue

        out.setdefault(host, {}).setdefault(action_id, []).append(art_id)

    return out
