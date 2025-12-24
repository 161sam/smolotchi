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


def service_fingerprint_by_key(services: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Returns fingerprints for coarse service groups: http/ssh/smb.
    Only includes services that match each key.
    """

    def _filter(key: str) -> List[Dict[str, Any]]:
        out = []
        for svc in services or []:
            name = (svc.get("name") or "").lower()
            port = int(svc.get("port") or 0)
            tunnel = (svc.get("tunnel") or "").lower()

            if key == "http":
                if (
                    name.startswith("http")
                    or port in (80, 81, 443, 8080, 8443)
                    or tunnel == "ssl"
                ):
                    out.append(svc)
            elif key == "ssh":
                if name == "ssh" or port == 22:
                    out.append(svc)
            elif key == "smb":
                if name in ("microsoft-ds", "netbios-ssn") or port in (
                    139,
                    445,
                ) or "smb" in name:
                    out.append(svc)
        return out

    fps = {}
    for key in ("http", "ssh", "smb"):
        fps[key] = service_fingerprint(_filter(key))
    return fps
