from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from smolotchi import cli  # noqa: E402


def test_decide_web_server_auto_prefers_gunicorn_path() -> None:
    gunicorn_path = Path("/opt/smolotchi/current/.venv/bin/gunicorn")
    server, messages, is_error = cli._decide_web_server("auto", gunicorn_path, False)

    assert server == "gunicorn"
    assert messages == []
    assert is_error is False


def test_decide_web_server_gunicorn_requires_binary() -> None:
    server, messages, is_error = cli._decide_web_server("gunicorn", None, True)

    assert server == "gunicorn"
    assert any("gunicorn binary" in message for message in messages)
    assert is_error is True
