from __future__ import annotations

from types import SimpleNamespace
import os
import subprocess
from pathlib import Path

import smolotchi.cli as cli


def test_cli_uninstall_defaults_to_dry_run(monkeypatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(os, "geteuid", lambda: 0)

    def _exists(self: Path) -> bool:
        return str(self) == "/opt/smolotchi/current/scripts/uninstall_smolotchi.sh"

    monkeypatch.setattr(Path, "exists", _exists)
    monkeypatch.setattr(subprocess, "check_call", lambda cmd: calls.append(cmd))

    args = SimpleNamespace(apply=False, remove_user=False)
    result = cli.cmd_uninstall(args)

    assert result == 0
    assert calls == [["/opt/smolotchi/current/scripts/uninstall_smolotchi.sh", "--dry-run"]]
