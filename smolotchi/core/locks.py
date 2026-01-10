from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOCK_SUFFIX = ".lock"
META_SUFFIX = ".lock.json"


def ensure_lock_dir(lock_root: str | Path) -> Path:
    path = Path(lock_root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _meta_path_for(lock_path: Path) -> Path:
    if lock_path.suffix == LOCK_SUFFIX:
        return lock_path.with_suffix(META_SUFFIX)
    return Path(f"{lock_path}{META_SUFFIX}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_lock(lock_path: Path, *, purpose: str | None = None) -> dict[str, Any]:
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(str(pid))

    meta = {
        "path": str(lock_path),
        "pid": pid,
        "created_at": _utc_now_iso(),
        "hostname": socket.gethostname(),
        "purpose": purpose,
    }
    meta_path = _meta_path_for(lock_path)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def _read_pid(lock_path: Path) -> int | None:
    try:
        raw = lock_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except OSError:
        return None
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def read_lock_meta(lock_path: Path) -> dict[str, Any]:
    lock_path = Path(lock_path)
    meta_path = _meta_path_for(lock_path)
    meta: dict[str, Any] = {}
    meta_missing = True
    meta_error = None
    if meta_path.exists():
        meta_missing = False
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                meta = payload
            else:
                meta_error = "meta payload is not an object"
        except (OSError, json.JSONDecodeError):
            meta_error = "invalid meta json"
            meta = {}

    pid = meta.get("pid")
    if pid is None:
        pid = _read_pid(lock_path)

    created_at = meta.get("created_at")
    if not created_at:
        try:
            stat = lock_path.stat()
            created_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(
                microsecond=0
            ).isoformat()
        except OSError:
            created_at = None

    return {
        "path": meta.get("path", str(lock_path)),
        "pid": pid,
        "created_at": created_at,
        "hostname": meta.get("hostname"),
        "purpose": meta.get("purpose"),
        "meta_missing": meta_missing,
        "meta_error": meta_error,
    }


def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value
        if value.endswith("Z"):
            normalized = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def classify_lock(lock_path: Path, ttl_seconds: int) -> dict[str, Any]:
    lock_path = Path(lock_path)
    try:
        meta = read_lock_meta(lock_path)
        pid = meta.get("pid")
        created_at_raw = meta.get("created_at")
        created_at = _parse_iso8601(created_at_raw)
        age_seconds = None
        if created_at:
            age_seconds = max(
                0, int((datetime.now(timezone.utc) - created_at).total_seconds())
            )
        meta_missing = bool(meta.get("meta_missing"))
        meta_error = meta.get("meta_error")

        status = "ok"
        details = "-"
        if meta_error:
            status = "error"
            details = meta_error
        elif meta_missing:
            status = "missing_meta"
            details = "meta sidecar missing"
        elif pid and not is_pid_alive(int(pid)):
            status = "stale_pid"
            details = "pid not alive"
        elif ttl_seconds >= 0 and age_seconds is not None and age_seconds > ttl_seconds:
            status = "stale_ttl"
            details = f"age {age_seconds}s > ttl {ttl_seconds}s"

        return {
            "status": status,
            "pid": pid,
            "age_seconds": age_seconds,
            "purpose": meta.get("purpose"),
            "path": meta.get("path", str(lock_path)),
            "details": details,
        }
    except Exception as exc:
        return {
            "status": "error",
            "pid": None,
            "age_seconds": None,
            "purpose": None,
            "path": str(lock_path),
            "details": str(exc),
        }


def list_locks(lock_root: str | Path, ttl_seconds: int) -> list[dict[str, Any]]:
    root = ensure_lock_dir(lock_root)
    locks: list[dict[str, Any]] = []
    for lock_path in sorted(root.glob(f"*{LOCK_SUFFIX}")):
        locks.append(classify_lock(lock_path, ttl_seconds))
    return locks


def prune_locks(
    lock_root: str | Path,
    ttl_seconds: int,
    *,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    records = list_locks(lock_root, ttl_seconds)
    summary: dict[str, int] = {
        "ok": 0,
        "stale_pid": 0,
        "stale_ttl": 0,
        "missing_meta": 0,
        "error": 0,
        "deleted": 0,
        "skipped": 0,
        "failed": 0,
    }
    actions: list[dict[str, Any]] = []

    for record in records:
        status = record.get("status")
        summary[status] = summary.get(status, 0) + 1
        action = "skip"
        reason = "status"
        should_delete = status in {"stale_pid", "stale_ttl"}
        if status == "missing_meta" and force:
            should_delete = True
            reason = "force"
        if status in {"ok", "missing_meta", "error"}:
            if status == "missing_meta" and force:
                reason = "force"
            else:
                reason = status

        lock_path = Path(str(record.get("path") or ""))
        if not lock_path.is_absolute():
            lock_path = Path(lock_root) / lock_path
        if should_delete:
            action = "delete"
            reason = "stale"
            if status == "missing_meta" and force:
                reason = "force"
            if not dry_run:
                try:
                    lock_path.unlink(missing_ok=True)
                except TypeError:
                    if lock_path.exists():
                        lock_path.unlink()
                except OSError as exc:
                    action = "error"
                    reason = f"delete failed: {exc}"
                    summary["failed"] += 1
                else:
                    meta_path = _meta_path_for(lock_path)
                    try:
                        meta_path.unlink(missing_ok=True)
                    except TypeError:
                        if meta_path.exists():
                            meta_path.unlink()
                    except OSError as exc:
                        action = "error"
                        reason = f"meta delete failed: {exc}"
                        summary["failed"] += 1
            if action == "delete" and not dry_run:
                summary["deleted"] += 1
            elif action == "delete" and dry_run:
                summary["skipped"] += 1
            elif action != "delete":
                summary["skipped"] += 1
        else:
            summary["skipped"] += 1

        actions.append(
            {
                "path": record.get("path"),
                "status": status,
                "action": action,
                "reason": reason,
                "pid": record.get("pid"),
                "age_seconds": record.get("age_seconds"),
                "purpose": record.get("purpose"),
                "details": record.get("details"),
            }
        )

    return {"summary": summary, "actions": actions}
