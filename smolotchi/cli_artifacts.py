from __future__ import annotations

import argparse
import json
import sys
import time

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.artifacts_gc import apply_gc, plan_gc


def _format_ts(ts: float | None) -> str:
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))


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


def _emit_error(
    *,
    code: int,
    message: str,
    fmt: str,
    hint: str | None = None,
    details: dict | None = None,
) -> None:
    if fmt == "json":
        _print_json(
            {
                "code": code,
                "message": message,
                "hint": hint,
                "details": details or {},
            }
        )
    else:
        print(f"error: {message}", file=sys.stderr)
        if hint:
            print(f"hint: {hint}", file=sys.stderr)
        if details:
            print(f"details: {details}", file=sys.stderr)


def add_artifacts_subcommands(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("artifacts", help="Artifact store utilities")
    sub = parser.add_subparsers(dest="artifacts_cmd", required=True)

    find = sub.add_parser("find", help="Find artifacts by filters")
    find.add_argument("--kind", default=None, help="Filter by artifact kind")
    find.add_argument("--job-id", default=None, help="Filter by payload job_id")
    find.add_argument("--request-id", default=None, help="Filter by payload request_id")
    find.add_argument("--limit", type=int, default=20, help="Limit results")
    find.add_argument(
        "--scan-limit",
        type=int,
        default=500,
        help="Scan the newest N artifacts when filtering",
    )
    find.add_argument(
        "--include-payload",
        action="store_true",
        help="Include payload in json output",
    )

    gc = sub.add_parser("gc", help="Garbage collect artifacts with retention rules")
    gc.add_argument(
        "--keep-bundles",
        type=int,
        default=50,
        help="Keep newest N lan_bundle artifacts",
    )
    gc.add_argument(
        "--keep-reports",
        type=int,
        default=200,
        help="Keep newest M lan_report artifacts",
    )

    def _run(args: argparse.Namespace) -> int:
        store = ArtifactStore(args.artifact_root)
        plan = plan_gc(store, keep_bundles=args.keep_bundles, keep_reports=args.keep_reports)

        print("Smolotchi Artifact GC")
        print(f"- root: {args.root}")
        print(f"- keep bundles: {args.keep_bundles} (actual: {len(plan.keep_bundles)})")
        print(f"- keep reports: {args.keep_reports} (actual: {len(plan.keep_reports)})")
        print(f"- keep total ids: {len(plan.keep_ids)}")
        print(f"- delete candidates: {len(plan.delete_ids)}")
        print(f"- mode: {'DRY-RUN' if args.dry_run else 'DELETE'}")
        print("")

        preview = plan.delete_ids[:40]
        if preview:
            print("Delete preview (first 40):")
            for artifact_id in preview:
                meta = store.get_meta(artifact_id) or {}
                kind = meta.get("kind", "?")
                title = meta.get("title", "")
                print(f"  - {artifact_id}  [{kind}]  {title}")
            if len(plan.delete_ids) > len(preview):
                print(f"  … +{len(plan.delete_ids) - len(preview)} more")
            print("")

        deleted, failed = apply_gc(store, plan, dry_run=args.dry_run)

        if args.dry_run:
            print("Dry-run done. Nothing was deleted.")
        else:
            print(f"Deleted: {deleted}")
            print(f"Failed:  {failed}")

        return 0 if failed == 0 else 2

    gc.set_defaults(fn=_run)

    def _run_find(args: argparse.Namespace) -> int:
        store = ArtifactStore(args.artifact_root)
        fmt = getattr(args, "format", "table")
        matches = []
        candidates = store.list(limit=args.scan_limit, kind=args.kind)
        for meta in candidates:
            doc = store.get_json(meta.id) or {}
            if args.job_id and str(doc.get("job_id")) != str(args.job_id):
                continue
            if args.request_id and str(doc.get("request_id")) != str(args.request_id):
                continue
            matches.append(
                {
                    "id": meta.id,
                    "kind": meta.kind,
                    "title": meta.title,
                    "created_ts": meta.created_ts,
                    "path": meta.path,
                    "payload": doc if args.include_payload else None,
                }
            )
            if len(matches) >= args.limit:
                break

        if fmt == "json":
            if not args.include_payload:
                for row in matches:
                    row.pop("payload", None)
            _print_json(matches)
            return 0

        rows = [
            [
                row["id"],
                row["kind"],
                _format_ts(row["created_ts"]),
                row["title"],
            ]
            for row in matches
        ]
        _print_table(["ID", "KIND", "CREATED", "TITLE"], rows)
        return 0

    find.set_defaults(fn=_run_find)

    get = sub.add_parser("get", help="Show an artifact payload")
    get.add_argument("artifact_id", help="Artifact id")

    def _run_get(args: argparse.Namespace) -> int:
        store = ArtifactStore(args.artifact_root)
        fmt = getattr(args, "format", "table")
        meta = store.get_meta(args.artifact_id)
        if not meta:
            _emit_error(
                code=2,
                message="artifact not found",
                hint="Verify the artifact id with `smolotchi artifacts find`.",
                details={"artifact_id": args.artifact_id},
                fmt=fmt,
            )
            return 2
        doc = store.get_json(args.artifact_id)
        payload = {"meta": meta, "payload": doc}
        if fmt == "json":
            _print_json(payload)
        else:
            rows = [
                [key, json.dumps(value, ensure_ascii=False)]
                for key, value in payload.items()
            ]
            _print_table(["FIELD", "VALUE"], rows)
        return 0

    get.set_defaults(fn=_run_get)

    verify = sub.add_parser("verify", help="Verify artifact integrity")
    verify.add_argument("--kind", default=None, help="Filter by artifact kind")
    verify.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Limit number of artifacts scanned (use 0 for all)",
    )

    def _run_verify(args: argparse.Namespace) -> int:
        store = ArtifactStore(args.artifact_root)
        fmt = getattr(args, "format", "table")
        limit = None if args.limit <= 0 else args.limit
        candidates = store.list(limit=limit, kind=args.kind)
        failed = []
        ok_count = 0
        for meta in candidates:
            result = store.verify(meta.path)
            if result.status == "ok":
                ok_count += 1
                continue
            reason = result.error or result.status
            if result.status == "hash_mismatch":
                reason = f"expected {result.expected_sha256} got {result.actual_sha256}"
            elif result.status == "missing_manifest":
                reason = "manifest missing"
            elif result.status == "missing_artifact":
                reason = "artifact missing"
            failed.append({"id": meta.id, "reason": reason})

        payload = {
            "total": len(candidates),
            "ok": ok_count,
            "failed": failed,
        }

        if fmt == "json":
            _print_json(payload)
            return 0 if not failed else 2

        rows = [[str(item["id"]), str(item["reason"])] for item in failed]
        print(f"Total: {payload['total']}  OK: {payload['ok']}  Failed: {len(failed)}")
        if rows:
            _print_table(["ID", "REASON"], rows)
        return 0 if not failed else 2

    verify.set_defaults(fn=_run_verify)
