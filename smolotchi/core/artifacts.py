from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import json
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

from smolotchi.core.paths import resolve_artifact_root

MANIFEST_SUFFIX = ".manifest.json"
HASH_CHUNK_SIZE = 1024 * 64

@dataclass
class ArtifactMeta:
    id: str
    kind: str
    created_ts: float
    title: str
    path: str


@dataclass
class ArtifactVerifyResult:
    status: str
    path: str
    expected_sha256: Optional[str] = None
    actual_sha256: Optional[str] = None
    error: Optional[str] = None


class ArtifactStore:
    def __init__(self, root: str | None = None):
        self.root = Path(root or resolve_artifact_root())
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.json"
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not self.index_path.exists():
            self.index_path.write_text("[]", encoding="utf-8")

    def _manifest_path(self, artifact_path: Path) -> Path:
        return Path(str(artifact_path) + MANIFEST_SUFFIX)

    def _relative_path(self, artifact_path: Path) -> str:
        try:
            return str(artifact_path.relative_to(self.root))
        except ValueError:
            return str(artifact_path)

    def _artifact_path_from_manifest(
        self, manifest: Optional[Dict[str, Any]], manifest_path: Path
    ) -> Path:
        if manifest and manifest.get("path"):
            manifest_path_value = Path(str(manifest["path"]))
            if manifest_path_value.is_absolute():
                return manifest_path_value
            return self.root / manifest_path_value
        if str(manifest_path).endswith(MANIFEST_SUFFIX):
            return Path(str(manifest_path)[: -len(MANIFEST_SUFFIX)])
        return manifest_path

    def _write_manifest_atomic(self, manifest_path: Path, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        self._write_bytes_atomic(manifest_path, data.encode("utf-8"), include_hash=False)

    def _write_bytes_atomic(
        self, path: Path, data: bytes, *, include_hash: bool = True
    ) -> tuple[str, int]:
        path.parent.mkdir(parents=True, exist_ok=True)
        hasher = hashlib.sha256()
        size = 0
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=str(path.parent))
        try:
            mv = memoryview(data)
            for idx in range(0, len(mv), HASH_CHUNK_SIZE):
                chunk = mv[idx : idx + HASH_CHUNK_SIZE]
                temp_file.write(chunk)
                if include_hash:
                    hasher.update(chunk)
                size += len(chunk)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        finally:
            temp_file.close()
        os.replace(temp_file.name, path)
        return hasher.hexdigest(), size

    def _hash_file(self, path: Path) -> tuple[str, int]:
        hasher = hashlib.sha256()
        size = 0
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(HASH_CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
                size += len(chunk)
        return hasher.hexdigest(), size

    def _load_manifest(self, manifest_path: Path) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return None, f"manifest_read_error: {exc}"
        if not isinstance(payload, dict):
            return None, "manifest_invalid: not a dict"
        return payload, None

    def _write_manifest_for_artifact(
        self, artifact_path: Path, sha256: str, size_bytes: int, created_at: str
    ) -> None:
        payload = {
            "path": self._relative_path(artifact_path),
            "sha256": sha256,
            "size_bytes": size_bytes,
            "created_at": created_at,
        }
        manifest_path = self._manifest_path(artifact_path)
        self._write_manifest_atomic(manifest_path, payload)

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
        now_ts = time.time()
        aid = f"{int(now_ts)}-{kind}"
        path = self.root / f"{aid}.json"
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        sha256, size_bytes = self._write_bytes_atomic(path, content)
        created_at = datetime.fromtimestamp(now_ts, tz=timezone.utc).replace(
            microsecond=0
        ).isoformat()
        self._write_manifest_for_artifact(path, sha256, size_bytes, created_at)
        tags = tags or []
        meta_payload = meta or {}

        meta = ArtifactMeta(
            id=aid,
            kind=kind,
            created_ts=now_ts,
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
        now_ts = time.time()
        aid = f"{int(now_ts)}-{kind}"
        suffix = ext if ext.startswith(".") else f".{ext}"
        path = self.root / f"{aid}{suffix}"
        content = text.encode("utf-8")
        sha256, size_bytes = self._write_bytes_atomic(path, content)
        created_at = datetime.fromtimestamp(now_ts, tz=timezone.utc).replace(
            microsecond=0
        ).isoformat()
        self._write_manifest_for_artifact(path, sha256, size_bytes, created_at)

        meta = ArtifactMeta(
            id=aid,
            kind=kind,
            created_ts=now_ts,
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
        now_ts = time.time()
        aid = f"{int(now_ts)}-{kind}"
        path = self.root / f"{aid}-{filename}"
        sha256, size_bytes = self._write_bytes_atomic(path, content)
        created_at = datetime.fromtimestamp(now_ts, tz=timezone.utc).replace(
            microsecond=0
        ).isoformat()
        self._write_manifest_for_artifact(path, sha256, size_bytes, created_at)

        meta = ArtifactMeta(
            id=aid,
            kind=kind,
            created_ts=now_ts,
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
                    path = Path(str(row.get("path")))
                    path.unlink(missing_ok=True)
                    self._manifest_path(path).unlink(missing_ok=True)
                except TypeError:
                    path = Path(str(row.get("path")))
                    if path.exists():
                        path.unlink()
                        manifest_path = self._manifest_path(path)
                        if manifest_path.exists():
                            manifest_path.unlink()
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
                    path = Path(str(row.get("path")))
                    path.unlink(missing_ok=True)
                    self._manifest_path(path).unlink(missing_ok=True)
                except TypeError:
                    path = Path(str(row.get("path")))
                    if path.exists():
                        path.unlink()
                        manifest_path = self._manifest_path(path)
                        if manifest_path.exists():
                            manifest_path.unlink()
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
                self._manifest_path(file_path).unlink(missing_ok=True)
            except TypeError:
                if file_path.exists():
                    file_path.unlink()
                    manifest_path = self._manifest_path(file_path)
                    if manifest_path.exists():
                        manifest_path.unlink()
        self._remove_meta(artifact_id)

    def verify(self, path: str) -> ArtifactVerifyResult:
        artifact_path = Path(path)
        if not artifact_path.is_absolute():
            artifact_path = self.root / artifact_path
        display_path = self._relative_path(artifact_path)
        manifest_path = self._manifest_path(artifact_path)

        if not artifact_path.exists():
            expected_sha = None
            if manifest_path.exists():
                manifest, error = self._load_manifest(manifest_path)
                if error:
                    return ArtifactVerifyResult(
                        status="error", path=display_path, error=error
                    )
                expected_sha = str(manifest.get("sha256") or "")
                if not expected_sha:
                    return ArtifactVerifyResult(
                        status="error",
                        path=display_path,
                        error="manifest_missing_sha256",
                    )
            return ArtifactVerifyResult(
                status="missing_artifact",
                path=display_path,
                expected_sha256=expected_sha,
            )

        if not manifest_path.exists():
            return ArtifactVerifyResult(status="missing_manifest", path=display_path)

        manifest, error = self._load_manifest(manifest_path)
        if error:
            return ArtifactVerifyResult(status="error", path=display_path, error=error)

        expected_sha = str(manifest.get("sha256") or "")
        if not expected_sha:
            return ArtifactVerifyResult(
                status="error", path=display_path, error="manifest_missing_sha256"
            )
        try:
            actual_sha, _ = self._hash_file(artifact_path)
        except Exception as exc:
            return ArtifactVerifyResult(
                status="error", path=display_path, error=f"hash_error: {exc}"
            )

        if expected_sha and actual_sha != expected_sha:
            return ArtifactVerifyResult(
                status="hash_mismatch",
                path=display_path,
                expected_sha256=expected_sha,
                actual_sha256=actual_sha,
            )

        return ArtifactVerifyResult(
            status="ok",
            path=display_path,
            expected_sha256=expected_sha,
            actual_sha256=actual_sha,
        )

    def verify_all(self, limit: Optional[int] = None) -> List[ArtifactVerifyResult]:
        manifests = sorted(self.root.rglob(f"*{MANIFEST_SUFFIX}"))
        if limit is not None:
            manifests = manifests[:limit]
        results: List[ArtifactVerifyResult] = []
        for manifest_path in manifests:
            manifest, error = self._load_manifest(manifest_path)
            if error:
                results.append(
                    ArtifactVerifyResult(
                        status="error",
                        path=self._relative_path(manifest_path),
                        error=error,
                    )
                )
                continue
            artifact_path = self._artifact_path_from_manifest(manifest, manifest_path)
            results.append(self.verify(str(artifact_path)))
        return results
