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


def test_build_web_exec_start_gunicorn_includes_bind_and_port() -> None:
    description, exec_start = cli._build_web_exec_start(
        "gunicorn",
        Path("/opt/smolotchi/current/.venv/bin/gunicorn"),
        Path("/usr/bin/python3"),
        "0.0.0.0",
        8081,
    )

    assert description == "Smolotchi Web UI (Gunicorn)"
    assert "--bind 0.0.0.0:8081" in exec_start


def test_build_web_exec_start_flask_includes_host_and_port() -> None:
    description, exec_start = cli._build_web_exec_start(
        "flask",
        None,
        Path("/usr/bin/python3"),
        "127.0.0.1",
        8080,
    )

    assert description == "Smolotchi Web UI (Flask dev server)"
    assert "smolotchi.cli web --host 127.0.0.1 --port 8080" in exec_start
