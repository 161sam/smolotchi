from __future__ import annotations

import argparse
import json

from smolotchi.core.config import ConfigStore
from smolotchi.core.normalize import normalize_profile, profile_hash


def add_profiles_subcommands(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("profiles", help="WiFi profile utilities")
    sub = parser.add_subparsers(dest="profiles_cmd", required=True)

    def _load_profiles(config_path: str) -> dict:
        store = ConfigStore(config_path)
        cfg = store.load()
        w = getattr(cfg, "wifi", None)
        profiles = getattr(w, "profiles", None) if w else None
        return profiles if isinstance(profiles, dict) else {}

    list_cmd = sub.add_parser("list", help="List available SSIDs")

    def _run_list(args: argparse.Namespace) -> int:
        profiles = _load_profiles(args.config)
        for ssid in sorted(profiles.keys()):
            print(ssid)
        return 0

    list_cmd.set_defaults(fn=_run_list)

    show_cmd = sub.add_parser("show", help="Show a normalized profile")
    show_cmd.add_argument("ssid")

    def _run_show(args: argparse.Namespace) -> int:
        profiles = _load_profiles(args.config)
        profile = profiles.get(args.ssid) or {}
        norm, warnings = normalize_profile(profile if isinstance(profile, dict) else {})
        if warnings:
            print("# warnings")
            for warn in warnings:
                print(f"- {warn}")
        print(json.dumps(norm, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    show_cmd.set_defaults(fn=_run_show)

    hash_cmd = sub.add_parser("hash", help="Show the profile hash")
    hash_cmd.add_argument("ssid")

    def _run_hash(args: argparse.Namespace) -> int:
        profiles = _load_profiles(args.config)
        profile = profiles.get(args.ssid) or {}
        norm, _ = normalize_profile(profile if isinstance(profile, dict) else {})
        print(profile_hash(norm))
        return 0

    hash_cmd.set_defaults(fn=_run_hash)
