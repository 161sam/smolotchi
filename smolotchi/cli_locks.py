from __future__ import annotations

import argparse
import json
from pathlib import Path

from smolotchi.core.locks import list_locks, prune_locks
from smolotchi.core.paths import resolve_lock_root


STALE_STATUSES = {"stale_pid", "stale_ttl"}


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def _format_age_minutes(age_seconds: int | None) -> str:
    if age_seconds is None:
        return "-"
    return f"{age_seconds / 60.0:.1f}"


def _display_path(path_value: str, lock_root: str) -> str:
    try:
        return str(Path(path_value).resolve().relative_to(Path(lock_root).resolve()))
    except Exception:
        return path_value


def _summarize(records: list[dict]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for record in records:
        status = record.get("status", "unknown")
        summary[status] = summary.get(status, 0) + 1
    summary["total"] = len(records)
    return summary


def add_locks_subcommands(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("locks", help="Lock leak detection utilities")
    sub = parser.add_subparsers(dest="locks_cmd", required=True)

    list_cmd = sub.add_parser("list", help="List lock files and stale candidates")
    list_cmd.add_argument("--lock-root", default=resolve_lock_root())
    list_cmd.add_argument("--ttl-min", type=int, default=30)
    list_cmd.add_argument("--format", choices=["json", "table"], default="table")

    prune_cmd = sub.add_parser("prune", help="Prune stale locks")
    prune_cmd.add_argument("--lock-root", default=resolve_lock_root())
    prune_cmd.add_argument("--ttl-min", type=int, default=30)
    prune_cmd.add_argument("--dry-run", action="store_true", default=False)
    prune_cmd.add_argument("--force", action="store_true", default=False)
    prune_cmd.add_argument("--format", choices=["json", "table"], default="table")

    def _run_list(args: argparse.Namespace) -> int:
        try:
            ttl_seconds = args.ttl_min * 60
            records = list_locks(args.lock_root, ttl_seconds)
            summary = _summarize(records)
            if args.format == "json":
                _print_json({"locks": records, "summary": summary})
            else:
                rows = []
                for record in records:
                    rows.append(
                        [
                            record.get("status") or "-",
                            _format_age_minutes(record.get("age_seconds")),
                            str(record.get("pid") or "-"),
                            record.get("purpose") or "-",
                            _display_path(record.get("path") or "-", args.lock_root),
                            record.get("details") or "-",
                        ]
                    )
                _print_table(["STATUS", "AGE_MIN", "PID", "PURPOSE", "PATH", "DETAILS"], rows)
            stale_count = sum(
                1 for record in records if record.get("status") in STALE_STATUSES
            )
            return 20 if stale_count > 0 else 0
        except Exception as exc:
            if args.format == "json":
                _print_json({"error": {"code": "runtime_error", "message": str(exc)}})
            else:
                print(f"error: {exc}")
            return 10

    def _run_prune(args: argparse.Namespace) -> int:
        try:
            ttl_seconds = args.ttl_min * 60
            result = prune_locks(
                args.lock_root,
                ttl_seconds,
                dry_run=args.dry_run,
                force=args.force,
            )
            actions = result.get("actions", [])
            summary = result.get("summary", {})
            if args.format == "json":
                _print_json({"locks": actions, "summary": summary})
            else:
                rows = []
                for record in actions:
                    details = record.get("details") or "-"
                    reason = record.get("reason") or "-"
                    action = record.get("action") or "-"
                    rows.append(
                        [
                            record.get("status") or "-",
                            _format_age_minutes(record.get("age_seconds")),
                            str(record.get("pid") or "-"),
                            record.get("purpose") or "-",
                            _display_path(record.get("path") or "-", args.lock_root),
                            f"{action} ({reason}) {details}",
                        ]
                    )
                _print_table(["STATUS", "AGE_MIN", "PID", "PURPOSE", "PATH", "DETAILS"], rows)
            if summary.get("failed"):
                return 10
            return 0
        except Exception as exc:
            if args.format == "json":
                _print_json({"error": {"code": "runtime_error", "message": str(exc)}})
            else:
                print(f"error: {exc}")
            return 10

    list_cmd.set_defaults(fn=_run_list)
    prune_cmd.set_defaults(fn=_run_prune)
