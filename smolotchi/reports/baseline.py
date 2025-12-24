from __future__ import annotations

from typing import Set


def expected_findings_for_scope(cfg, scope: str | None) -> Set[str]:
    if not cfg or not getattr(cfg, "baseline", None):
        return set()
    baseline = cfg.baseline
    if not baseline.enabled:
        return set()
    scopes = baseline.scopes or {}
    if not scopes:
        return set()
    if scope and scope in scopes:
        return set(scopes.get(scope, []))
    return set(next(iter(scopes.values()), []))
