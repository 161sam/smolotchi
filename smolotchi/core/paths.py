from __future__ import annotations

import os


DEFAULT_DB_PATH = "/var/lib/smolotchi/events.db"
DEFAULT_ARTIFACT_ROOT = "/var/lib/smolotchi/artifacts"
DEFAULT_CONFIG_PATH = "config.toml"
DEFAULT_TAG = "lab-approved"
DEFAULT_DEVICE = "pi_zero"
DEFAULT_DISPLAY_DRYRUN = ""


def resolve_db_path() -> str:
    return os.environ.get("SMOLOTCHI_DB", DEFAULT_DB_PATH)


def resolve_artifact_root() -> str:
    return os.environ.get("SMOLOTCHI_ARTIFACT_ROOT", DEFAULT_ARTIFACT_ROOT)


def resolve_config_path() -> str:
    return os.environ.get("SMOLOTCHI_CONFIG", DEFAULT_CONFIG_PATH)


def resolve_default_tag() -> str:
    return os.environ.get("SMOLOTCHI_DEFAULT_TAG", DEFAULT_TAG)


def resolve_device() -> str:
    return os.environ.get("SMOLOTCHI_DEVICE", DEFAULT_DEVICE)


def resolve_display_dryrun() -> bool:
    return os.environ.get("SMOLOTCHI_DISPLAY_DRYRUN", DEFAULT_DISPLAY_DRYRUN).strip() == "1"
