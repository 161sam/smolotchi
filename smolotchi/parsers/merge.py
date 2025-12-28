from __future__ import annotations


def merge_hosts(existing: dict, incoming: dict) -> dict:
    existing["last_seen"] = max(
        existing.get("last_seen", 0),
        incoming.get("last_seen", 0),
    )

    for key in ("ports", "services", "sources"):
        existing.setdefault(key, [])
        for v in incoming.get(key, []):
            if v not in existing[key]:
                existing[key].append(v)

    for k, v in incoming.get("host", {}).items():
        existing.setdefault("host", {})
        existing["host"].setdefault(k, v)

    return existing
