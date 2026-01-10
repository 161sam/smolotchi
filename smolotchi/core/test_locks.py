import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from smolotchi.core.locks import (
    LOCK_SUFFIX,
    META_SUFFIX,
    list_locks,
    prune_locks,
    write_lock,
)


def _meta_path(lock_path: Path) -> Path:
    return lock_path.with_suffix(META_SUFFIX)


def _write_meta(lock_path: Path, payload: dict) -> None:
    _meta_path(lock_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_list_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        records = list_locks(tmpdir, ttl_seconds=60)
        assert records == []


def test_list_ok_lock_with_meta():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        meta = write_lock(lock_path, purpose="test")
        records = list_locks(tmpdir, ttl_seconds=3600)
        assert len(records) == 1
        assert records[0]["status"] == "ok"
        assert records[0]["pid"] == meta["pid"]


def test_list_stale_pid_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        meta = write_lock(lock_path, purpose="test")
        meta["pid"] = 999999
        _write_meta(lock_path, meta)
        lock_path.write_text("999999", encoding="utf-8")
        records = list_locks(tmpdir, ttl_seconds=3600)
        assert records[0]["status"] == "stale_pid"


def test_list_stale_ttl_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        meta = write_lock(lock_path, purpose="test")
        meta["created_at"] = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).replace(microsecond=0).isoformat()
        _write_meta(lock_path, meta)
        records = list_locks(tmpdir, ttl_seconds=60)
        assert records[0]["status"] == "stale_ttl"


def test_list_missing_meta_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        lock_path.write_text("123", encoding="utf-8")
        records = list_locks(tmpdir, ttl_seconds=60)
        assert records[0]["status"] == "missing_meta"


def test_prune_dry_run_keeps_stale_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        meta = write_lock(lock_path, purpose="test")
        meta["pid"] = 999999
        _write_meta(lock_path, meta)
        lock_path.write_text("999999", encoding="utf-8")
        result = prune_locks(tmpdir, ttl_seconds=60, dry_run=True, force=False)
        assert lock_path.exists()
        assert _meta_path(lock_path).exists()
        assert result["summary"]["deleted"] == 0


def test_prune_deletes_stale_lock_and_meta():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        meta = write_lock(lock_path, purpose="test")
        meta["pid"] = 999999
        _write_meta(lock_path, meta)
        lock_path.write_text("999999", encoding="utf-8")
        result = prune_locks(tmpdir, ttl_seconds=60, dry_run=False, force=False)
        assert not lock_path.exists()
        assert not _meta_path(lock_path).exists()
        assert result["summary"]["deleted"] == 1


def test_prune_force_deletes_missing_meta():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / f"worker{LOCK_SUFFIX}"
        lock_path.write_text("123", encoding="utf-8")
        result = prune_locks(tmpdir, ttl_seconds=60, dry_run=False, force=True)
        assert not lock_path.exists()
        assert result["summary"]["deleted"] == 1
