from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass
class ReplayMetrics:
    plan_id: str
    run_id: str
    run_status: str
    steps_planned: int
    steps_executed: int
    total_time_s: float
    avg_step_s: float
    artifacts_linked: int
    reports_linked: int
    bundles_linked: int
    jobs_linked: int
    error: Optional[str] = None


def _collect_links(steps: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    artifacts: Set[str] = set()
    reports: Set[str] = set()
    bundles: Set[str] = set()
    jobs: Set[str] = set()

    for s in steps:
        links = s.get("links") or {}
        for a in (links.get("artifacts") or []):
            artifacts.add(str(a))
        for r in (links.get("reports") or []):
            reports.add(str(r))
        for b in (links.get("bundles") or []):
            bundles.add(str(b))
        for j in (links.get("jobs") or []):
            jobs.add(str(j))

    return {
        "artifacts": artifacts,
        "reports": reports,
        "bundles": bundles,
        "jobs": jobs,
    }


def evaluate_plan_run(plan: Dict[str, Any], run: Dict[str, Any]) -> Dict[str, Any]:
    steps_planned = len(plan.get("steps") or [])
    steps = run.get("steps") or []
    steps_executed = len(steps)

    durations = [float(s.get("duration_s") or 0.0) for s in steps]
    total_time = sum(durations)
    avg_step = (total_time / steps_executed) if steps_executed else 0.0

    links = _collect_links(steps)

    m = ReplayMetrics(
        plan_id=str(run.get("plan_id") or plan.get("id") or ""),
        run_id=str(run.get("job_id") or run.get("run_id") or ""),
        run_status=str(run.get("status") or "unknown"),
        steps_planned=steps_planned,
        steps_executed=steps_executed,
        total_time_s=round(total_time, 3),
        avg_step_s=round(avg_step, 3),
        artifacts_linked=len(links["artifacts"]),
        reports_linked=len(links["reports"]),
        bundles_linked=len(links["bundles"]),
        jobs_linked=len(links["jobs"]),
        error=run.get("error"),
    )

    signal = m.artifacts_linked + 2 * m.reports_linked + 3 * m.bundles_linked
    reward = (signal / total_time) if total_time > 0 else 0.0

    return {
        "metrics": m.__dict__,
        "reward_proxy": round(float(reward), 6),
        "signal": {
            "artifacts": sorted(links["artifacts"]),
            "reports": sorted(links["reports"]),
            "bundles": sorted(links["bundles"]),
            "jobs": sorted(links["jobs"]),
        },
    }


def metrics_row(result: Dict[str, Any]) -> Dict[str, Any]:
    m = result.get("metrics") or {}
    return {
        "plan_id": m.get("plan_id"),
        "run_id": m.get("run_id"),
        "status": m.get("run_status"),
        "steps_planned": m.get("steps_planned"),
        "steps_executed": m.get("steps_executed"),
        "total_time_s": m.get("total_time_s"),
        "avg_step_s": m.get("avg_step_s"),
        "artifacts_linked": m.get("artifacts_linked"),
        "reports_linked": m.get("reports_linked"),
        "bundles_linked": m.get("bundles_linked"),
        "jobs_linked": m.get("jobs_linked"),
        "reward_proxy": result.get("reward_proxy"),
        "error": m.get("error"),
    }
