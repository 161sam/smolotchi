from __future__ import annotations

from typing import Any, Set


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


def profile_key_for_job_meta(job_meta: dict | None) -> str | None:
    if not isinstance(job_meta, dict):
        return None
    ssid = (job_meta.get("wifi_ssid") or "").strip()
    profile_hash = (job_meta.get("wifi_profile_hash") or "").strip()
    if not ssid or not profile_hash:
        return None
    return f"{ssid}.{profile_hash}"


def expected_findings_for_profile(cfg, profile_key: str | None) -> Set[str]:
    if not cfg or not getattr(cfg, "baseline", None):
        return set()
    baseline = cfg.baseline
    if not baseline.enabled:
        return set()
    profiles = getattr(baseline, "profiles", None) or {}
    if not isinstance(profiles, dict) or not profiles:
        return set()
    if profile_key and profile_key in profiles:
        return set(profiles.get(profile_key, []))
    return set(next(iter(profiles.values()), []))


def expected_findings_for_bundle(cfg, bundle: dict) -> Set[str]:
    job_meta = (
        (bundle.get("job") or {}).get("meta") if isinstance(bundle.get("job"), dict) else {}
    )
    if not job_meta and isinstance(bundle.get("job_meta"), dict):
        job_meta = bundle.get("job_meta") or {}
    profile_key = profile_key_for_job_meta(job_meta)
    expected = expected_findings_for_profile(cfg, profile_key)
    if expected:
        return expected
    scope = bundle.get("scope") if isinstance(bundle, dict) else None
    return expected_findings_for_scope(cfg, scope)


def expected_findings_for_profile_dict(
    baseline: dict | None, profile_key: str | None
) -> Set[str]:
    if not isinstance(baseline, dict) or not baseline.get("enabled", False):
        return set()
    profiles = baseline.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        return set()
    if profile_key and profile_key in profiles:
        return set(profiles.get(profile_key, []))
    return set(next(iter(profiles.values()), []))


def expected_findings_for_scope_dict(
    baseline: dict | None, scope: str | None
) -> Set[str]:
    if not isinstance(baseline, dict) or not baseline.get("enabled", False):
        return set()
    scopes = baseline.get("scopes")
    if not isinstance(scopes, dict) or not scopes:
        return set()
    if scope and scope in scopes:
        return set(scopes.get(scope, []))
    return set(next(iter(scopes.values()), []))


def summarize_baseline_status(
    *,
    findings: list[dict],
    expected: Set[str],
    baseline_profiles: dict | None = None,
    profile_key: str | None = None,
) -> dict:
    seen = {str(f.get("id") or f.get("title") or "") for f in findings}
    seen = {fid for fid in seen if fid}
    disappeared = set(expected) - set(seen)
    new = set(seen) - set(expected)
    drifted: Set[str] = set()
    if isinstance(baseline_profiles, dict) and baseline_profiles:
        other_expected: Set[str] = set()
        for key, ids in baseline_profiles.items():
            if profile_key and key == profile_key:
                continue
            if isinstance(ids, list):
                other_expected |= {str(x) for x in ids}
        drifted = new & other_expected
        new = new - drifted
    return {
        "profile": profile_key,
        "expected": len(expected),
        "new": len(new),
        "disappeared": len(disappeared),
        "drifted": len(drifted),
    }
