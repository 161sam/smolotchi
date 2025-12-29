#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path
from typing import List


class Route:
    def __init__(self, method: str, path: str, handler: str):
        self.method = method
        self.path = path
        self.handler = handler


def parse_routes(path: Path) -> List[Route]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    routes: List[Route] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                if isinstance(deco.func.value, ast.Name) and deco.func.value.id == "app":
                    method = deco.func.attr.upper()
                    if deco.args and isinstance(deco.args[0], ast.Constant):
                        path_val = str(deco.args[0].value)
                        routes.append(Route(method, path_val, node.name))
    return routes


def build_markdown(routes: List[Route]) -> str:
    lines = [
        "# HTTP API",
        "",
        "Routes are registered on the Flask app in `smolotchi/api/web.py`.",
        "",
        "Code: smolotchi/api/web.py:create_app",
        "",
        "| Method | Path | Handler | Code Reference |",
        "| --- | --- | --- | --- |",
    ]
    for route in sorted(routes, key=lambda r: (r.path, r.method)):
        lines.append(
            f"| `{route.method}` | `{route.path}` | `{route.handler}` | `smolotchi/api/web.py:{route.handler}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    path = Path("smolotchi/api/web.py")
    routes = parse_routes(path)
    output_path = Path("docs-site/docs/reference/http-api.md")
    output_path.write_text(build_markdown(routes), encoding="utf-8")


if __name__ == "__main__":
    main()
