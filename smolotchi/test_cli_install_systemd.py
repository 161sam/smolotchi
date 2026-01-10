from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import os
import shutil
import subprocess
import sys

import smolotchi.cli as cli


def _make_project(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    tmpfiles_dir = proj / "packaging" / "systemd" / "tmpfiles.d"
    tmpfiles_dir.mkdir(parents=True)
    (tmpfiles_dir / "smolotchi.conf").write_text(
        "d /run/smolotchi 0775 root root -\n", encoding="utf-8"
    )
    return proj


def _run_install(tmp_path: Path, monkeypatch) -> tuple[int, list[tuple[Path, str]], list]:
    proj = _make_project(tmp_path)
    args = SimpleNamespace(
        project_dir=str(proj),
        user="smolotchi",
        db="/var/lib/smolotchi/events.db",
    )

    written: list[tuple[Path, str]] = []
    calls: list = []

    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(cli, "_write_unit", lambda dst, content: written.append((dst, content)))
    monkeypatch.setattr(shutil, "copyfile", lambda src, dst: calls.append(("copyfile", src, dst)))
    monkeypatch.setattr(subprocess, "check_call", lambda cmd: calls.append(("check_call", cmd)))

    result = cli.cmd_install_systemd(args)
    return result, written, calls


def test_install_systemd_falls_back_to_sys_executable(tmp_path: Path, monkeypatch, capsys) -> None:
    sys_python = tmp_path / "sys-python"
    sys_python.write_text("", encoding="utf-8")
    sys_python.chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(sys_python))

    result, written, calls = _run_install(tmp_path, monkeypatch)

    assert result == 0
    assert any(f"ExecStart={sys_python}" in content for _, content in written)
    assert any(
        call == ("check_call", ["systemd-tmpfiles", "--create", "/etc/tmpfiles.d/smolotchi.conf"])
        for call in calls
    )
    out = capsys.readouterr().out
    assert "info:" in out


def test_install_systemd_prefers_venv_python(tmp_path: Path, monkeypatch, capsys) -> None:
    proj = _make_project(tmp_path)
    venv_python = proj / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")
    venv_python.chmod(0o755)

    sys_python = tmp_path / "sys-python"
    sys_python.write_text("", encoding="utf-8")
    sys_python.chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(sys_python))

    args = SimpleNamespace(
        project_dir=str(proj),
        user="smolotchi",
        db="/var/lib/smolotchi/events.db",
    )

    written: list[tuple[Path, str]] = []
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(cli, "_write_unit", lambda dst, content: written.append((dst, content)))
    monkeypatch.setattr(shutil, "copyfile", lambda src, dst: None)
    monkeypatch.setattr(subprocess, "check_call", lambda cmd: None)

    result = cli.cmd_install_systemd(args)

    assert result == 0
    assert any(f"ExecStart={venv_python}" in content for _, content in written)
    out = capsys.readouterr().out
    assert "not usable" not in out
