from __future__ import annotations

from .bettercap import BettercapParser
from .masscan import MasscanParser
from .nmap import NmapParser

PARSERS = {
    "nmap": NmapParser(),
    "masscan": MasscanParser(),
    "bettercap": BettercapParser(),
}


def parse(tool: str, raw: str | bytes):
    parser = PARSERS.get(tool)
    if not parser:
        raise ValueError(f"Unknown parser {tool}")
    return parser.parse(raw)
