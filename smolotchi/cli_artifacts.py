from __future__ import annotations

import argparse

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.artifacts_gc import apply_gc, plan_gc


def add_artifacts_subcommands(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("artifacts", help="Artifact store utilities")
    sub = parser.add_subparsers(dest="artifacts_cmd", required=True)

    gc = sub.add_parser("gc", help="Garbage collect artifacts with retention rules")
    gc.add_argument(
        "--root",
        default="/var/lib/smolotchi/artifacts",
        help="Artifact store root path",
    )
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
        store = ArtifactStore(args.root)
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
