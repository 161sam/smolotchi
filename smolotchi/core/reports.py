from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass
class ReportConfig:
    templates_dir: str


class ReportRenderer:
    def __init__(self, cfg: ReportConfig):
        self.env = Environment(
            loader=FileSystemLoader(cfg.templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_lan_result(self, title: str, result: Dict[str, Any]) -> bytes:
        tpl = self.env.get_template("lan_result.html")
        html = tpl.render(
            title=title,
            ts=time.strftime("%Y-%m-%d %H:%M:%S"),
            job=result.get("job", {}),
            summary=result.get("summary", ""),
            result=result,
        )
        return html.encode("utf-8")
