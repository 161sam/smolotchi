from __future__ import annotations

import time
from datetime import datetime

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus


def core_health_ok(bus: SQLiteBus, max_age_s: float = 20.0) -> tuple[bool, float | None]:
    events = bus.tail(limit=1, topic_prefix="core.health")
    if not events:
        return False, None
    evt = events[0]
    age = time.time() - float(evt.ts)
    return age <= max_age_s, float(evt.ts)


def worker_health_ok(
    artifacts: ArtifactStore, max_age_s: float = 120.0
) -> tuple[bool, float | None]:
    latest = artifacts.list(limit=1, kind="worker_health")
    if not latest:
        return False, None
    meta = latest[0]
    doc = artifacts.get_json(meta.id) or {}
    ts = None
    raw = doc.get("ts")
    if raw:
        try:
            ts = datetime.fromisoformat(str(raw)).timestamp()
        except ValueError:
            ts = None
    if ts is None:
        ts = float(meta.created_ts)
    age = time.time() - ts
    return age <= max_age_s, ts
