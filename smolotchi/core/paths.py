from __future__ import annotations

import os


DEFAULT_DB_PATH = "/var/lib/smolotchi/events.db"
DEFAULT_ARTIFACT_ROOT = "/var/lib/smolotchi/artifacts"
DEFAULT_CONFIG_PATH = "config.toml"


def resolve_db_path() -> str:
    return os.environ.get("SMOLOTCHI_DB", DEFAULT_DB_PATH)


def resolve_artifact_root() -> str:
    return os.environ.get("SMOLOTCHI_ARTIFACT_ROOT", DEFAULT_ARTIFACT_ROOT)


def resolve_config_path() -> str:
    return os.environ.get("SMOLOTCHI_CONFIG", DEFAULT_CONFIG_PATH)
