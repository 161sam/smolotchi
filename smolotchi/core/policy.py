from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import ipaddress


@dataclass
class Policy:
    """
    v0.0.1: simple allowlist.
    Später: Profiles, human confirmation, audit, scope by VLAN/SSID etc.
    """

    allowed_tags: List[str] = field(default_factory=lambda: ["lab-approved"])
    allowed_scopes: List[str] = field(
        default_factory=lambda: ["10.0.0.0/8", "192.168.0.0/16"]
    )
    allowed_tools: List[str] = field(default_factory=lambda: ["nmap", "ip", "arp", "ping"])
    block_categories: List[str] = field(
        default_factory=lambda: ["system_attack", "file_steal"]
    )
    autonomous_categories: List[str] = field(
        default_factory=lambda: ["network_scan", "vuln_assess"]
    )

    def allow_handoff(self, payload: Dict) -> bool:
        tag = str(payload.get("tag", ""))
        return tag in self.allowed_tags

    def scope_allowed(self, target: str) -> bool:
        try:
            if "/" in target:
                net = ipaddress.ip_network(target, strict=False)
                return any(
                    net.subnet_of(ipaddress.ip_network(s, strict=False))
                    for s in self.allowed_scopes
                )
            ip = ipaddress.ip_address(target)
            return any(
                ip in ipaddress.ip_network(s, strict=False)
                for s in self.allowed_scopes
            )
        except Exception:
            return False

    def category_allowed(self, category: str) -> bool:
        return category not in self.block_categories

    def autonomous_allowed(self, category: str) -> bool:
        return category in self.autonomous_categories and self.category_allowed(category)


@dataclass
class PolicyDecision:
    ok: bool
    requires_approval: bool = False
    reason: str = ""
    level: int = 1
    tags: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


def evaluate_tool_action(
    *,
    tool: str,
    job_kind: str,
    scope: str,
    cfg_policy: Optional[Dict[str, Any]] = None,
) -> PolicyDecision:
    """
    Pi-Zero friendly: simple, deterministic gate for tool execution.
    """
    cfg_policy = cfg_policy or {}
    allowed_tools = set(cfg_policy.get("allowed_tools") or ["nmap", "ip", "arp", "ping"])

    if tool not in allowed_tools:
        return PolicyDecision(
            ok=False,
            requires_approval=False,
            reason=f"tool not allowed by config: {tool}",
            level=2,
            tags=["policy", "tool", "deny"],
        )

    if job_kind == "scan.nmap":
        return PolicyDecision(
            ok=False,
            requires_approval=True,
            reason="approval required for scan.nmap",
            level=2,
            tags=["policy", "nmap", "approval"],
            meta={"scope": scope},
        )

    if job_kind == "scan.bettercap":
        return PolicyDecision(
            ok=False,
            requires_approval=True,
            reason="approval required for scan.bettercap",
            level=2,
            tags=["policy", "bettercap", "approval"],
            meta={"scope": scope},
        )

    if job_kind == "scan.masscan":
        enabled = bool(cfg_policy.get("enable_masscan", False))
        if not enabled:
            return PolicyDecision(
                ok=False,
                requires_approval=False,
                reason="masscan disabled by config (policy.enable_masscan=0)",
                level=2,
                tags=["policy", "masscan", "deny"],
            )
        return PolicyDecision(
            ok=False,
            requires_approval=True,
            reason="approval required for scan.masscan",
            level=2,
            tags=["policy", "masscan", "approval"],
            meta={"scope": scope},
        )

    return PolicyDecision(ok=True, reason="ok", level=1, tags=["policy", "allow"])
