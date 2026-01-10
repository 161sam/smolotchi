from __future__ import annotations

import argparse
import json
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
    find.add_argument("--format", choices=["json", "table"], default="table")
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
    gc.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only print what would be deleted (default)",
    )
    gc.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Actually delete candidates",
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

        if args.format == "json":
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
    get.add_argument("--format", choices=["json", "table"], default="json")

    def _run_get(args: argparse.Namespace) -> int:
        store = ArtifactStore(args.artifact_root)
        meta = store.get_meta(args.artifact_id)
        if not meta:
            print("error: artifact not found")
            return 2
        doc = store.get_json(args.artifact_id)
        payload = {"meta": meta, "payload": doc}
        if args.format == "json":
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
    scope = verify.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--path",
        help="Relative or absolute artifact path to verify",
    )
    scope.add_argument(
        "--all",
        action="store_true",
        help="Verify all artifacts by scanning manifests",
    )
    verify.add_argument("--format", choices=["json", "table"], default="table")

    def _run_verify(args: argparse.Namespace) -> int:
        store = ArtifactStore(args.artifact_root)
        results = []
        if args.all:
            results = store.verify_all()
        else:
            results = [store.verify(args.path)]

        if args.format == "json":
            payload = {"results": [result.__dict__ for result in results]}
            if args.all:
                summary = {}
                for result in results:
                    summary[result.status] = summary.get(result.status, 0) + 1
                summary["total"] = len(results)
                payload["summary"] = summary
            _print_json(payload)
            return 0 if all(r.status == "ok" for r in results) else 2

        rows = []
        for result in results:
            details = "-"
            if result.status == "hash_mismatch":
                details = f"expected {result.expected_sha256} got {result.actual_sha256}"
            elif result.status == "missing_manifest":
                details = "manifest missing"
            elif result.status == "missing_artifact":
                details = "artifact missing"
            elif result.status == "error":
                details = result.error or "error"
            rows.append([result.status, result.path, details])
        _print_table(["STATUS", "PATH", "DETAILS"], rows)
        return 0 if all(r.status == "ok" for r in results) else 2

    verify.set_defaults(fn=_run_verify)
