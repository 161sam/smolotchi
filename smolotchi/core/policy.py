from dataclasses import dataclass, field
from typing import Dict, List
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
