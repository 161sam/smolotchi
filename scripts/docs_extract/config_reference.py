#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO_ROOT))

from smolotchi.core import config as config_mod
from smolotchi.core import paths as paths_mod


def _type_name(tp: Any) -> str:
    if isinstance(tp, type):
        return tp.__name__
    return str(tp)


def _iter_fields(prefix: str, obj: Any) -> Iterable[tuple[str, str, Any]]:
    for field in dataclasses.fields(obj):
        name = f"{prefix}.{field.name}" if prefix else field.name
        value = getattr(obj, field.name)
        if dataclasses.is_dataclass(value):
            yield from _iter_fields(name, value)
        else:
            yield name, _type_name(field.type), value


def _format_default(value: Any) -> str:
    if isinstance(value, str):
        return value or "\"\""
    return value


def build_config_table() -> str:
    store = config_mod.ConfigStore()
    default_cfg = store._from_dict({})
    rows = []
    for key, type_name, value in _iter_fields("", default_cfg):
        rows.append((key, type_name, _format_default(value)))
    rows.sort(key=lambda r: r[0])

    lines = [
        "# Configuration Reference",
        "",
        "The configuration schema is defined by dataclasses in `smolotchi/core/config.py`.",
        "",
        "Code: smolotchi/core/config.py:ConfigStore",
        "",
        "## Environment variables",
        "",
        "| Name | Default | Description | Code Reference |",
        "| --- | --- | --- | --- |",
        f"| `SMOLOTCHI_DB` | `{paths_mod.DEFAULT_DB_PATH}` | Override the SQLite DB path. | `smolotchi/core/paths.py:resolve_db_path` |",
        f"| `SMOLOTCHI_ARTIFACT_ROOT` | `{paths_mod.DEFAULT_ARTIFACT_ROOT}` | Override artifact root. | `smolotchi/core/paths.py:resolve_artifact_root` |",
        f"| `SMOLOTCHI_LOCK_ROOT` | `{paths_mod.DEFAULT_LOCK_ROOT}` | Override lock root. | `smolotchi/core/paths.py:resolve_lock_root` |",
        f"| `SMOLOTCHI_CONFIG` | `{paths_mod.DEFAULT_CONFIG_PATH}` | Override config path. | `smolotchi/core/paths.py:resolve_config_path` |",
        f"| `SMOLOTCHI_DEFAULT_TAG` | `{paths_mod.DEFAULT_TAG}` | Default tag for actions. | `smolotchi/core/paths.py:resolve_default_tag` |",
        f"| `SMOLOTCHI_DEVICE` | `{paths_mod.DEFAULT_DEVICE}` | Device identifier. | `smolotchi/core/paths.py:resolve_device` |",
        f"| `SMOLOTCHI_DISPLAY_DRYRUN` | `{paths_mod.DEFAULT_DISPLAY_DRYRUN}` | Display dry-run toggle. | `smolotchi/core/paths.py:resolve_display_dryrun` |",
        "",
        "## `config.toml` fields",
        "",
        "| Name | Type | Default | Description | Code Reference |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key, type_name, value in rows:
        lines.append(
            f"| `{key}` | `{type_name}` | `{value}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    content = build_config_table()
    output_path = "docs-site/docs/reference/configuration.md"
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(content)


if __name__ == "__main__":
    main()
