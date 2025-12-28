"""Tool-specific parsers that normalize scan results into HostSummary-like dicts."""

from .base import BaseParser
from .bettercap import BettercapParser
from .masscan import MasscanParser
from .nmap import NmapParser
from .registry import PARSERS, parse

__all__ = [
    "BaseParser",
    "BettercapParser",
    "MasscanParser",
    "NmapParser",
    "PARSERS",
    "parse",
]
