import tempfile

from smolotchi.core.artifacts import ArtifactStore


def test_stage_request_min_fields():
    with tempfile.TemporaryDirectory() as d:
        artifacts = ArtifactStore(d)
        meta = artifacts.put_json(
            "ai_stage_request", "req", {"id": "r1", "job_id": "j1", "step_index": 0}
        )
        data = artifacts.get_json(meta.id)
        assert "job_id" in data
        assert "step_index" in data
