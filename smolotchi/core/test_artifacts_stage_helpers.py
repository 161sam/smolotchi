import tempfile

from smolotchi.core.artifacts import ArtifactStore


def test_stage_pending_helpers() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        store.put_json("ai_stage_request", "req", {"job_id": "j1"})
        req = store.find_latest_stage_request()
        assert req is not None
        assert req["id"]
        assert store.is_stage_request_pending(req) is True
        store.put_json("ai_stage_approval", "appr", {"request_id": req["id"]})
        req2 = store.find_latest_stage_request()
        assert req2 is not None
        assert store.is_stage_request_pending(req2) is False


def test_pending_stage_request_id_injected() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        store.put_json("ai_stage_request", "req", {"job_id": "j1"})
        pending = store.find_latest_pending_stage_request()
        assert pending is not None
        assert pending["id"]
        assert store.count_pending_stage_requests() == 1
        store.put_json(
            "ai_stage_approval", "appr", {"request_id": pending["id"]}
        )
        assert store.find_latest_pending_stage_request() is None
        assert store.count_pending_stage_requests() == 0
