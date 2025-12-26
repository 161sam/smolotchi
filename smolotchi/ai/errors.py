from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class StageRequired(Exception):
    """
    Raised when a policy blocks an action with risk='caution' and we must request approval.
    """

    job_id: str
    plan_id: str
    step_index: int
    action_id: str
    payload: Dict[str, Any]
    risk: str
    scope: Optional[str] = None
    reason: str = "Action requires approval"
