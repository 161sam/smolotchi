import pytest

from smolotchi.api.web import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOLOTCHI_DB", str(tmp_path / "events.db"))
    monkeypatch.setenv("SMOLOTCHI_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
