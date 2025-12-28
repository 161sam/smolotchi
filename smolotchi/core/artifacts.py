from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import time
from typing import Any, Dict, List, Optional

from smolotchi.core.paths import resolve_artifact_root

@dataclass
class ArtifactMeta:
    id: str
    kind: str
    created_ts: float
    title: str
    path: str


class ArtifactStore:
    def __init__(self, root: str | None = None):
        self.root = Path(root or resolve_artifact_root())
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

    def put_json(
        self,
        kind: str,
        title: str,
        payload: Dict[str, Any],
        *,
        tags: Optional[List[str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> ArtifactMeta:
        aid = f"{int(time.time())}-{kind}"
        path = self.root / f"{aid}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tags = tags or []
        meta_payload = meta or {}

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
                "tags": tags,
                **meta_payload,
            },
        )
        self._save_index(idx)
        return meta

    def put_text(
        self,
        kind: str,
        title: str,
        text: str,
        ext: str = ".txt",
        mime: str = "text/plain; charset=utf-8",
    ) -> ArtifactMeta:
        aid = f"{int(time.time())}-{kind}"
        suffix = ext if ext.startswith(".") else f".{ext}"
        path = self.root / f"{aid}{suffix}"
        path.write_text(text, encoding="utf-8")

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
                "mimetype": mime,
            },
        )
        self._save_index(idx)
        return meta

    def put_file(
        self,
        kind: str,
        title: str,
        filename: str,
        content: bytes,
        mimetype: str = "application/octet-stream",
    ) -> ArtifactMeta:
        aid = f"{int(time.time())}-{kind}"
        path = self.root / f"{aid}-{filename}"
        path.write_bytes(content)

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
                "mimetype": mimetype,
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

    def get_meta(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        idx = self._load_index()
        return next((r for r in idx if r.get("id") == artifact_id), None)

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

    def find_bundle_by_job_id(self, job_id: str) -> Optional[str]:
        """
        Returns artifact_id of newest lan_bundle for job_id.
        """
        idx = self._load_index()
        for row in idx:
            if row.get("kind") != "lan_bundle":
                continue
            aid = str(row.get("id"))
            data = self.get_json(aid)
            if data and str(data.get("job_id")) == job_id:
                return aid
        return None

    def find_dossier_by_job_id(self, job_id: str) -> Optional[str]:
        """
        Returns artifact_id of newest lan_dossier for job_id.
        """
        if not job_id:
            return None
        idx = self._load_index()
        for row in idx:
            if row.get("kind") != "lan_dossier":
                continue
            if str(row.get("job_id") or "") == job_id:
                return str(row.get("id"))
            aid = str(row.get("id"))
            data = self.get_json(aid)
            if data and str(data.get("job_id")) == job_id:
                return aid
        return None

    def find_latest(self, kind: str) -> Optional[str]:
        latest = self.list(limit=1, kind=kind)
        return latest[0].id if latest else None

    def latest_meta(self, kind: str) -> Optional[Dict[str, Any]]:
        aid = self.find_latest(kind)
        return self.get_meta(aid) if aid else None

    def latest_json(self, kind: str) -> Optional[Dict[str, Any]]:
        aid = self.find_latest(kind)
        return self.get_json(aid) if aid else None

    def count_kind(self, kind: str, limit_scan: int = 5000) -> int:
        idx = self._load_index()
        return sum(1 for row in idx[:limit_scan] if row.get("kind") == kind)

    def count_pending_stage_requests(self, limit_scan: int = 2000) -> int:
        idx = self._load_index()
        count = 0
        for row in idx[:limit_scan]:
            if row.get("kind") != "ai_stage_request":
                continue
            aid = str(row.get("id"))
            req = self.get_json(aid)
            if req:
                req = self._inject_stage_request_id(req, aid)
            if req and self.is_stage_request_pending(req):
                count += 1
        return count

    def _inject_stage_request_id(
        self, request: Dict[str, Any], artifact_id: str
    ) -> Dict[str, Any]:
        req_id = str(artifact_id)
        if request.get("id") != req_id:
            request["id"] = req_id
        if not request.get("request_id"):
            request["request_id"] = req_id
        return request

    def find_latest_stage_request(self) -> Optional[Dict[str, Any]]:
        latest = self.list(limit=1, kind="ai_stage_request")
        if not latest:
            return None
        req = self.get_json(latest[0].id)
        if not req:
            return None
        return self._inject_stage_request_id(req, latest[0].id)

    def find_latest_pending_stage_request(self) -> Optional[Dict[str, Any]]:
        """
        Returns newest ai_stage_request that has no matching ai_stage_approval.
        """
        idx = self._load_index()
        for row in idx:
            if row.get("kind") != "ai_stage_request":
                continue
            aid = str(row.get("id"))
            req = self.get_json(aid)
            if not req:
                continue
            req = self._inject_stage_request_id(req, aid)
            if self.is_stage_request_pending(req):
                return req
        return None

    def find_latest_stage_approval_for_request(
        self, request_id: str
    ) -> Optional[Dict[str, Any]]:
        idx = self._load_index()
        for row in idx:
            if row.get("kind") != "ai_stage_approval":
                continue
            aid = str(row.get("id"))
            data = self.get_json(aid)
            if data and str(data.get("request_id")) == str(request_id):
                return data
        return None

    def is_stage_request_pending(self, request: Dict[str, Any]) -> bool:
        rid = request.get("id") or request.get("request_id")
        if not rid:
            return True
        return self.find_latest_stage_approval_for_request(str(rid)) is None

    def prune(
        self, keep_last: int = 500, older_than_days: int = 30, kinds_keep_last=None
    ) -> int:
        """
        Deletes old artifacts + caps index.
        - older_than_days: delete artifacts older than cutoff based on meta.created_ts
        - keep_last: cap global index length
        - kinds_keep_last: list of kinds to additionally cap per kind (keep_last per kind)
        Returns number of deleted entries.
        """
        kinds_keep_last = kinds_keep_last or []
        idx = self._load_index()
        cutoff = time.time() - (older_than_days * 86400)

        deleted = 0

        new_idx = []
        for row in idx:
            ts = float(row.get("created_ts", 0))
            if ts and ts < cutoff:
                try:
                    Path(str(row.get("path"))).unlink(missing_ok=True)
                except TypeError:
                    path = Path(str(row.get("path")))
                    if path.exists():
                        path.unlink()
                deleted += 1
            else:
                new_idx.append(row)

        idx = new_idx

        if kinds_keep_last:
            by_kind: Dict[str, List[Dict[str, Any]]] = {}
            for row in idx:
                by_kind.setdefault(str(row.get("kind")), []).append(row)

            kept: List[Dict[str, Any]] = []
            for kind, rows in by_kind.items():
                if kind in kinds_keep_last:
                    kept.extend(rows[:keep_last])
                else:
                    kept.extend(rows)

            keep_set = {r.get("id") for r in kept}
            idx = [r for r in idx if r.get("id") in keep_set]

        if len(idx) > keep_last:
            for row in idx[keep_last:]:
                try:
                    Path(str(row.get("path"))).unlink(missing_ok=True)
                except TypeError:
                    path = Path(str(row.get("path")))
                    if path.exists():
                        path.unlink()
                deleted += 1
            idx = idx[:keep_last]

        self._save_index(idx)
        return deleted

    def _remove_meta(self, artifact_id: str) -> None:
        idx = self._load_index()
        idx = [row for row in idx if row.get("id") != artifact_id]
        self._save_index(idx)

    def delete(self, artifact_id: str) -> None:
        meta = self.get_meta(artifact_id)
        if meta is None:
            return
        path = meta.get("path")
        if path:
            file_path = Path(str(path))
            try:
                file_path.unlink(missing_ok=True)
            except TypeError:
                if file_path.exists():
                    file_path.unlink()
        self._remove_meta(artifact_id)
