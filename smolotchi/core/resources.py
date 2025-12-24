from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import time
from typing import Any, Dict, Optional


@dataclass
class Lease:
    resource: str
    owner: str
    ts: float
    ttl: float

    @property
    def expires_at(self) -> float:
        return self.ts + self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource": self.resource,
            "owner": self.owner,
            "ts": self.ts,
            "ttl": self.ttl,
        }


class ResourceManager:
    """
    Super simple file-based leases (atomic create). Pi-friendly.
    Resources: 'wifi', 'display', ... (du kannst erweitern)
    """

    def __init__(self, root: str = "/run/smolotchi/locks"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _lock_path(self, resource: str) -> Path:
        return self.root / f"{resource}.json"

    def _read(self, path: Path) -> Optional[Lease]:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Lease(
                resource=str(data["resource"]),
                owner=str(data["owner"]),
                ts=float(data["ts"]),
                ttl=float(data["ttl"]),
            )
        except Exception:
            return None

    def current(self, resource: str) -> Optional[Lease]:
        lease = self._read(self._lock_path(resource))
        if not lease:
            return None
        if time.time() > lease.expires_at:
            try:
                self._lock_path(resource).unlink(missing_ok=True)
            except TypeError:
                if self._lock_path(resource).exists():
                    self._lock_path(resource).unlink()
            return None
        return lease

    def acquire(self, resource: str, owner: str, ttl: float = 15.0) -> bool:
        path = self._lock_path(resource)

        cur = self.current(resource)
        if cur and cur.owner != owner:
            return False

        lease = Lease(resource=resource, owner=owner, ts=time.time(), ttl=ttl)

        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(lease.to_dict(), ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, path)
        return True

    def release(self, resource: str, owner: str) -> bool:
        path = self._lock_path(resource)
        cur = self._read(path)
        if not cur:
            return True
        if cur.owner != owner:
            return False
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return True

    def snapshot(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for p in self.root.glob("*.json"):
            lease = self._read(p)
            if not lease:
                continue
            if time.time() > lease.expires_at:
                continue
            out[lease.resource] = lease.to_dict()
        return out
