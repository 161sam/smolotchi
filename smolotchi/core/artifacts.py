from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import time
from typing import Any, Dict, List, Optional


@dataclass
class ArtifactMeta:
    id: str
    kind: str
    created_ts: float
    title: str
    path: str


class ArtifactStore:
    def __init__(self, root: str = "/var/lib/smolotchi/artifacts"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.json"
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not self.index_path.exists():
            self.index_path.write_text("[]", encoding="utf-8")

    def _load_index(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_index(self, idx: List[Dict[str, Any]]) -> None:
        self.index_path.write_text(
            json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def put_json(self, kind: str, title: str, payload: Dict[str, Any]) -> ArtifactMeta:
        aid = f"{int(time.time())}-{kind}"
        path = self.root / f"{aid}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        meta = ArtifactMeta(
            id=aid,
            kind=kind,
            created_ts=time.time(),
            title=title,
            path=str(path),
        )

        idx = self._load_index()
        idx.insert(
            0,
            {
                "id": meta.id,
                "kind": meta.kind,
                "created_ts": meta.created_ts,
                "title": meta.title,
                "path": meta.path,
            },
        )
        self._save_index(idx)
        return meta

    def list(self, limit: int = 50, kind: Optional[str] = None) -> List[ArtifactMeta]:
        idx = self._load_index()
        out: List[ArtifactMeta] = []
        for row in idx:
            if kind and row.get("kind") != kind:
                continue
            out.append(
                ArtifactMeta(
                    id=str(row.get("id")),
                    kind=str(row.get("kind")),
                    created_ts=float(row.get("created_ts")),
                    title=str(row.get("title")),
                    path=str(row.get("path")),
                )
            )
            if len(out) >= limit:
                break
        return out

    def get_json(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        idx = self._load_index()
        match = next((r for r in idx if r.get("id") == artifact_id), None)
        if not match:
            return None
        path = Path(str(match.get("path")))
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
