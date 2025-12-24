from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

ActionCategory = Literal[
    "network_scan",
    "vuln_assess",
    "system_attack",
    "file_steal",
]

ActionMode = Literal["manual", "ai", "autonomous"]


@dataclass
class ActionSpec:
    id: str
    name: str
    category: ActionCategory
    description: str = ""
    tags: List[str] = field(default_factory=list)

    inputs_schema: Dict[str, Any] = field(default_factory=dict)

    driver: Literal["builtin", "command", "external_stub"] = "builtin"
    command: Optional[List[str]] = None
    timeout_s: int = 120
    produces: List[str] = field(default_factory=lambda: ["artifact"])

    risk: Literal["safe", "caution", "danger"] = "safe"
    requires_confirmation: bool = False
    allow_autonomous: bool = False

    allowed_scopes: List[str] = field(default_factory=list)
