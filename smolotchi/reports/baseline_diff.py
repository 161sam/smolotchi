from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple


@dataclass
class BaselineDiff:
    scope: str
    expected: Set[str]
    seen_active: Set[str]
    seen_suppressed: Set[str]
    missing_expected: Set[str]
    unexpected_active: Set[str]
    unexpected_suppressed: Set[str]


def _bundle_findings(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    host_summary = bundle.get("host_summary") or {}
    return (host_summary.get("findings") or []) if isinstance(host_summary, dict) else []


def collect_seen_findings(
    bundles: List[Dict[str, Any]],
    include_suppressed: bool = True,
) -> Tuple[Set[str], Set[str]]:
    active: Set[str] = set()
    suppressed: Set[str] = set()

    for bundle in bundles:
        for finding in _bundle_findings(bundle):
            fid = str(finding.get("id") or finding.get("title") or "").strip()
            if not fid:
                continue
            is_suppressed = bool(
                finding.get("suppressed") or finding.get("suppressed_by_policy")
            )
            if is_suppressed:
                if include_suppressed:
                    suppressed.add(fid)
            else:
                active.add(fid)
    return active, suppressed


def compute_baseline_diff(
    scope: str,
    expected: Set[str],
    bundles: List[Dict[str, Any]],
) -> BaselineDiff:
    seen_active, seen_suppressed = collect_seen_findings(
        bundles, include_suppressed=True
    )
    missing_expected = set(expected) - (seen_active | seen_suppressed)

    unexpected_active = set(seen_active) - set(expected)
    unexpected_suppressed = set(seen_suppressed) - set(expected)

    return BaselineDiff(
        scope=scope,
        expected=set(expected),
        seen_active=seen_active,
        seen_suppressed=seen_suppressed,
        missing_expected=missing_expected,
        unexpected_active=unexpected_active,
        unexpected_suppressed=unexpected_suppressed,
    )
