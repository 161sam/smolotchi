from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class ParserResult(Dict):
    pass


class BaseParser(ABC):
    name: str

    @abstractmethod
    def parse(self, raw: str | bytes) -> List[ParserResult]:
        """
        Return list of HostSummary-like dicts.
        """
        raise NotImplementedError
