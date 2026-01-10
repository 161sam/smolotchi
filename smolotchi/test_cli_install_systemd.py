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


def _fake_sync_project(src: Path, dst: Path) -> None:
    tmpfiles_src = src / "packaging" / "systemd" / "tmpfiles.d" / "smolotchi.conf"
    tmpfiles_dst = dst / "packaging" / "systemd" / "tmpfiles.d"
    tmpfiles_dst.mkdir(parents=True, exist_ok=True)
    (tmpfiles_dst / "smolotchi.conf").write_text(
        tmpfiles_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    venv_python = src / ".venv" / "bin" / "python"
    if venv_python.exists():
        venv_dst = dst / ".venv" / "bin"
        venv_dst.mkdir(parents=True, exist_ok=True)
        (venv_dst / "python").write_text(
            venv_python.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (venv_dst / "python").chmod(0o755)


def _run_install(
    tmp_path: Path, monkeypatch, *, layout: str = "prod"
) -> tuple[int, list[tuple[Path, str]], list]:
    proj = _make_project(tmp_path)
    install_root = tmp_path / "install"
    args = SimpleNamespace(
        project_dir=str(proj),
        layout=layout,
        install_dir=str(install_root),
        user="smolotchi",
        db="/var/lib/smolotchi/events.db",
    )

    written: list[tuple[Path, str]] = []
    calls: list = []

    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(cli, "_write_unit", lambda dst, content: written.append((dst, content)))
    monkeypatch.setattr(cli, "_sync_project_tree", _fake_sync_project)
    def _copyfile(src, dst, **_kwargs) -> None:
        calls.append(("copyfile", src, dst))

    monkeypatch.setattr(shutil, "copyfile", _copyfile)
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

    install_root = tmp_path / "install"
    args = SimpleNamespace(
        project_dir=str(proj),
        layout="prod",
        install_dir=str(install_root),
        user="smolotchi",
        db="/var/lib/smolotchi/events.db",
    )

    written: list[tuple[Path, str]] = []
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(cli, "_write_unit", lambda dst, content: written.append((dst, content)))
    monkeypatch.setattr(cli, "_sync_project_tree", _fake_sync_project)
    monkeypatch.setattr(shutil, "copyfile", lambda src, dst, **_kwargs: None)
    monkeypatch.setattr(subprocess, "check_call", lambda cmd: None)

    result = cli.cmd_install_systemd(args)

    assert result == 0
    venv_python_install = install_root / ".venv" / "bin" / "python"
    assert any(f"ExecStart={venv_python_install}" in content for _, content in written)
    out = capsys.readouterr().out
    assert "not usable" not in out


def test_install_systemd_writes_prod_layout_units(tmp_path: Path, monkeypatch) -> None:
    sys_python = tmp_path / "sys-python"
    sys_python.write_text("", encoding="utf-8")
    sys_python.chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(sys_python))

    result, written, _ = _run_install(tmp_path, monkeypatch)

    assert result == 0
    assert any("WorkingDirectory=/var/lib/smolotchi" in content for _, content in written)
    assert any("ReadWritePaths=/var/lib/smolotchi /run/smolotchi" in content for _, content in written)
    assert any("ReadOnlyPaths=" in content for _, content in written)
    assert all("/home" not in content for _, content in written)


def test_install_systemd_disables_legacy_ai_unit(tmp_path: Path, monkeypatch) -> None:
    sys_python = tmp_path / "sys-python"
    sys_python.write_text("", encoding="utf-8")
    sys_python.chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(sys_python))

    legacy_unit = tmp_path / "smolotchi-ai.service"
    legacy_unit.write_text("", encoding="utf-8")
    monkeypatch.setattr(cli, "LEGACY_AI_UNIT_PATHS", (legacy_unit,))

    result, _, calls = _run_install(tmp_path, monkeypatch)

    assert result == 0
    assert ("check_call", ["systemctl", "disable", "--now", "smolotchi-ai.service"]) in calls
