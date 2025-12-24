from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from smolotchi.core.artifacts import ArtifactStore


@dataclass
class GCPlan:
    keep_ids: Set[str]
    delete_ids: List[str]
    keep_bundles: List[str]
    keep_reports: List[str]


def _extract_ref_ids_from_bundle(bundle: Dict[str, Any]) -> Set[str]:
    """
    Bundle schema varies a bit over time; we defensively collect all common refs.
    """
    refs: Set[str] = set()

    def add(value: Any) -> None:
        if not value:
            return
        if isinstance(value, str):
            refs.add(value)
        elif isinstance(value, dict):
            artifact_id = value.get("artifact_id")
            if isinstance(artifact_id, str) and artifact_id:
                refs.add(artifact_id)

    add((bundle.get("result_json") or {}).get("artifact_id"))

    reports = bundle.get("reports") or {}
    if isinstance(reports, dict):
        add((reports.get("html") or {}).get("artifact_id"))
        add((reports.get("md") or {}).get("artifact_id"))
        add((reports.get("json") or {}).get("artifact_id"))

        diff = reports.get("diff") or {}
        if isinstance(diff, dict):
            add((diff.get("html") or {}).get("artifact_id"))
            add((diff.get("md") or {}).get("artifact_id"))
            add((diff.get("json") or {}).get("artifact_id"))

    add((bundle.get("report_html") or {}).get("artifact_id"))
    diff_summary = bundle.get("diff_summary") or {}
    if isinstance(diff_summary, dict):
        add(diff_summary.get("artifact_id"))

    artifacts = bundle.get("artifacts") or []
    if isinstance(artifacts, list):
        for row in artifacts:
            if isinstance(row, dict):
                add(row.get("artifact_id"))

    return refs


def plan_gc(
    artifacts: ArtifactStore,
    keep_bundles: int,
    keep_reports: int,
) -> GCPlan:
    """
    Keep:
      - N newest lan_bundle (and everything referenced by them)
      - M newest lan_report (in case some reports exist without a bundle reference)
    Delete:
      - everything else (best-effort listing)
    """
    bundle_metas = (
        artifacts.list(limit=int(keep_bundles), kind="lan_bundle")
        if keep_bundles > 0
        else []
    )
    report_metas = (
        artifacts.list(limit=int(keep_reports), kind="lan_report")
        if keep_reports > 0
        else []
    )

    keep_bundle_ids = [meta.id for meta in bundle_metas]
    keep_report_ids = [meta.id for meta in report_metas]

    keep_ids: Set[str] = set(keep_bundle_ids) | set(keep_report_ids)

    for bundle_id in keep_bundle_ids:
        bundle = artifacts.get_json(bundle_id) or {}
        keep_ids |= _extract_ref_ids_from_bundle(bundle)

    all_metas = artifacts.list(limit=50_000)
    all_ids = [meta.id for meta in all_metas]

    delete_ids = [artifact_id for artifact_id in all_ids if artifact_id not in keep_ids]

    return GCPlan(
        keep_ids=keep_ids,
        delete_ids=delete_ids,
        keep_bundles=keep_bundle_ids,
        keep_reports=keep_report_ids,
    )


def _safe_unlink(path: Path) -> bool:
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True
    except Exception:
        return False
    return False


def apply_gc(
    artifacts: ArtifactStore,
    plan: GCPlan,
    dry_run: bool = True,
) -> Tuple[int, int]:
    """
    Returns (deleted_count, failed_count)
    Deletion is best-effort: remove underlying file path if present.
    If ArtifactStore exposes a delete() method, we use it.
    """
    deleted = 0
    failed = 0

    has_delete = hasattr(artifacts, "delete") and callable(getattr(artifacts, "delete"))

    for artifact_id in plan.delete_ids:
        if dry_run:
            continue

        try:
            if has_delete:
                artifacts.delete(artifact_id)  # type: ignore[attr-defined]
                deleted += 1
                continue

            meta = artifacts.get_meta(artifact_id) or {}
            path = meta.get("path")
            if path:
                ok = _safe_unlink(Path(path))
                if ok:
                    deleted += 1
                else:
                    failed += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return deleted, failed
