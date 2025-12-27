import tempfile

from smolotchi.core.artifacts import ArtifactStore


def test_stage_pending_helpers() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        store.put_json("ai_stage_request", "req", {"id": "r1", "job_id": "j1"})
        req = store.find_latest_stage_request()
        assert req is not None
        assert store.is_stage_request_pending(req) is True
        store.put_json("ai_stage_approval", "appr", {"request_id": "r1"})
        req2 = store.find_latest_stage_request()
        assert req2 is not None
        assert store.is_stage_request_pending(req2) is False
