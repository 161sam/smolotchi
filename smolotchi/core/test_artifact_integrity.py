import json
from pathlib import Path
import tempfile

from smolotchi.core.artifacts import ArtifactStore, MANIFEST_SUFFIX


def test_manifest_created_with_hash_and_size():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        meta = store.put_text("note", "hello", "payload")
        artifact_path = Path(meta.path)
        manifest_path = Path(str(artifact_path) + MANIFEST_SUFFIX)

        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["sha256"]
        assert manifest["size_bytes"] == len("payload".encode("utf-8"))
        assert manifest["path"] == str(artifact_path.relative_to(store.root))


def test_verify_ok_on_fresh_artifact():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        meta = store.put_text("note", "hello", "payload")
        result = store.verify(Path(meta.path).relative_to(store.root).as_posix())
        assert result.status == "ok"


def test_verify_detects_hash_mismatch_after_modification():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        meta = store.put_text("note", "hello", "payload")
        artifact_path = Path(meta.path)
        artifact_path.write_bytes(b"corrupt")
        result = store.verify(meta.path)
        assert result.status == "hash_mismatch"
        assert result.expected_sha256
        assert result.actual_sha256


def test_verify_detects_missing_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        meta = store.put_text("note", "hello", "payload")
        artifact_path = Path(meta.path)
        manifest_path = Path(str(artifact_path) + MANIFEST_SUFFIX)
        manifest_path.unlink()
        result = store.verify(meta.path)
        assert result.status == "missing_manifest"


def test_verify_detects_missing_artifact():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        meta = store.put_text("note", "hello", "payload")
        artifact_path = Path(meta.path)
        artifact_path.unlink()
        result = store.verify(meta.path)
        assert result.status == "missing_artifact"
