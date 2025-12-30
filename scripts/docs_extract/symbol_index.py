#!/usr/bin/env python3
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class Symbol:
    name: str
    kind: str
    doc: str


@dataclass
class Route:
    method: str
    path: str
    handler: str


def _iter_py_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if path.name.startswith("test_"):
            continue
        if "/tests/" in str(path):
            continue
        yield path


def _docstring(node: ast.AST) -> str:
    doc = ast.get_docstring(node) or ""
    return doc.strip() if doc else "Not present"


def mdx_escape(text: str) -> str:
    return (
        text.replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )


def _parse_symbols(path: Path) -> list[Symbol]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: List[Symbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(Symbol(name=node.name, kind="function", doc=_docstring(node)))
        if isinstance(node, ast.ClassDef):
            out.append(Symbol(name=node.name, kind="class", doc=_docstring(node)))
    return out


def _parse_routes(path: Path) -> list[Route]:
    if path.name != "web.py":
        return []
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
                        routes.append(Route(method=method, path=path_val, handler=node.name))
    return routes


def _parse_cli_commands(path: Path) -> list[str]:
    if path.name != "cli.py":
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cmds: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("cmd_"):
            cmds.append(node.name)
    return sorted(cmds)


def build_markdown() -> str:
    root = Path("smolotchi")
    modules = sorted(_iter_py_files(root))
    lines: List[str] = ["# Symbol Index", ""]

    cli_cmds: List[str] = []
    route_rows: List[Route] = []

    for path in modules:
        rel = path.as_posix()
        symbols = _parse_symbols(path)
        if not symbols:
            continue
        lines.append(f"## {rel}")
        for symbol in symbols:
            lines.append(f"- {symbol.kind}: `{symbol.name}`")
            lines.append(f"  - Docstring: {mdx_escape(symbol.doc)}")
            lines.append(f"  - Code: {rel}:{symbol.name}")
        lines.append("")

        route_rows.extend(_parse_routes(path))
        cli_cmds.extend(_parse_cli_commands(path))

    lines.append("## HTTP Routes (Flask)")
    lines.append("| Method | Path | Handler | Code Reference |")
    lines.append("| --- | --- | --- | --- |")
    for route in sorted(route_rows, key=lambda r: (r.path, r.method)):
        lines.append(
            f"| `{route.method}` | `{route.path}` | `{route.handler}` | `smolotchi/api/web.py:{route.handler}` |"
        )

    lines.append("")
    lines.append("## CLI Commands (functions)")
    lines.append("| Function | Code Reference |")
    lines.append("| --- | --- |")
    for cmd in sorted(set(cli_cmds)):
        lines.append(f"| `{cmd}` | `smolotchi/cli.py:{cmd}` |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    output_path = Path("docs-site/docs/_meta/symbol-index.md")
    output_path.write_text(build_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
