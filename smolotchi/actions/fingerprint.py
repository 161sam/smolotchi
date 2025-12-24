from __future__ import annotations

from typing import Any, Dict, List
import hashlib
import json


def service_fingerprint(services: List[Dict[str, Any]]) -> str:
    """
    Stable hash of relevant open-service facts.
    Only include fields that matter for planning & cache invalidation.
    """
    norm = []
    for svc in services or []:
        norm.append(
            {
                "port": int(svc.get("port") or 0),
                "proto": (svc.get("proto") or "").lower(),
                "name": (svc.get("name") or "").lower(),
                "tunnel": (svc.get("tunnel") or "").lower(),
                "product": (svc.get("product") or "").lower(),
                "version": (svc.get("version") or "").lower(),
            }
        )
    norm.sort(
        key=lambda item: (
            item["proto"],
            item["port"],
            item["name"],
            item["tunnel"],
            item["product"],
            item["version"],
        )
    )
    blob = json.dumps(norm, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
