from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Policy:
    """
    v0.0.1: simple allowlist.
    Später: Profiles, human confirmation, audit, scope by VLAN/SSID etc.
    """

    allowed_tags: List[str]

    def allow_handoff(self, payload: Dict) -> bool:
        tag = str(payload.get("tag", ""))
        return tag in self.allowed_tags
