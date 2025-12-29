#!/usr/bin/env python3
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = REPO_ROOT / "smolotchi"
OUTPUT_COVERAGE = REPO_ROOT / "docs-site" / "docs" / "_meta" / "docstring-coverage.md"
OUTPUT_QUALITY = REPO_ROOT / "docs-site" / "docs" / "_meta" / "docstring-quality.md"


@dataclass
class SymbolDoc:
    name: str
    kind: str
    docstring: Optional[str]
    lineno: int


@dataclass
class FileDocInfo:
    path: Path
    symbols: List[SymbolDoc]


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


class SymbolCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols: List[SymbolDoc] = []
        self._class_stack: List[str] = []

    def visit_Module(self, node: ast.Module) -> None:
        docstring = ast.get_docstring(node)
        self.symbols.append(SymbolDoc("<module>", "module", docstring, 1))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        docstring = ast.get_docstring(node)
        self.symbols.append(SymbolDoc(node.name, "class", docstring, node.lineno))
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            if self._class_stack:
                name = f"{self._class_stack[-1]}.{node.name}"
                kind = "method"
            else:
                name = node.name
                kind = "function"
            self.symbols.append(SymbolDoc(name, kind, docstring, node.lineno))
        self.generic_visit(node)


def collect_file_info(path: Path) -> FileDocInfo:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    collector = SymbolCollector()
    collector.visit(tree)
    return FileDocInfo(path=path, symbols=collector.symbols)


def module_group(path: Path) -> str:
    rel = path.relative_to(TARGET_ROOT)
    parts = rel.parts
    if len(parts) == 1:
        return "smolotchi"
    return f"smolotchi.{parts[0]}"


def coverage_stats(symbols: List[SymbolDoc]) -> tuple[int, int, float]:
    total = len(symbols)
    present = sum(1 for s in symbols if s.docstring)
    coverage = (present / total) * 100 if total else 0.0
    return present, total, coverage


def write_coverage_report(files: List[FileDocInfo]) -> None:
    lines: List[str] = []
    lines.append("# Docstring Coverage\n")

    global_symbols = [symbol for info in files for symbol in info.symbols]
    present, total, coverage = coverage_stats(global_symbols)
    lines.append(
        f"**Global Coverage:** {present}/{total} symbols ({coverage:.2f}%)\n"
    )

    lines.append("## Coverage by Module Group\n")
    by_module: dict[str, List[SymbolDoc]] = {}
    for info in files:
        by_module.setdefault(module_group(info.path), []).extend(info.symbols)
    for mod, symbols in sorted(by_module.items()):
        present, total, coverage = coverage_stats(symbols)
        lines.append(f"- {mod}: {present}/{total} ({coverage:.2f}%)")
    lines.append("")

    lines.append("## Coverage by File\n")
    for info in files:
        present, total, coverage = coverage_stats(info.symbols)
        rel = info.path.relative_to(REPO_ROOT)
        lines.append(f"- {rel}: {present}/{total} ({coverage:.2f}%)")
    lines.append("")

    for info in files:
        rel = info.path.relative_to(REPO_ROOT)
        lines.append(f"## {rel}\n")
        lines.append("| Symbol | Typ | Docstring | Status |")
        lines.append("|------|-----|-----------|--------|")
        for symbol in info.symbols:
            doc_present = "✅" if symbol.docstring else "❌"
            status = "present" if symbol.docstring else "missing"
            lines.append(f"| {symbol.name} | {symbol.kind} | {doc_present} | {status} |")
        lines.append("")

    OUTPUT_COVERAGE.write_text("\n".join(lines), encoding="utf-8")


def _has_section(doc: str, needles: Iterable[str]) -> bool:
    lower = doc.lower()
    return any(needle in lower for needle in needles)


def _function_needs_params(node: ast.AST) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    args = [arg.arg for arg in node.args.args]
    if args and args[0] in {"self", "cls"}:
        args = args[1:]
    return bool(args or node.args.kwonlyargs or node.args.vararg or node.args.kwarg)


def _function_has_return(node: ast.AST) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def _function_has_raise(node: ast.AST) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(isinstance(child, ast.Raise) for child in ast.walk(node))


def _docstring_quality(doc: str, node: ast.AST) -> dict[str, str]:
    multiline = "yes" if "\n" in doc.strip() else "no"
    has_params = _has_section(doc, ["args:", "arguments:", "parameters:", ":param"]) 
    has_returns = _has_section(doc, ["returns:", "return:", ":return"]) 
    has_raises = _has_section(doc, ["raises:", ":raises"]) 

    params_needed = _function_needs_params(node)
    returns_needed = _function_has_return(node)
    raises_needed = _function_has_raise(node)

    missing_sections: List[str] = []
    if params_needed and not has_params:
        missing_sections.append("params")
    if returns_needed and not has_returns:
        missing_sections.append("returns")
    if raises_needed and not has_raises:
        missing_sections.append("raises")

    return {
        "multiline": multiline,
        "params": "yes" if has_params else "no",
        "returns": "yes" if has_returns else "no",
        "raises": "yes" if has_raises else "no",
        "missing_sections": ", ".join(missing_sections) if missing_sections else "none",
    }


def write_quality_report(files: List[FileDocInfo]) -> None:
    lines: List[str] = []
    lines.append("# Docstring Quality (Structural)\n")
    lines.append(
        "Checks are structural only. Docstring content is not evaluated. Sections are detected via simple keyword matching.\n"
    )

    quality_rows: List[dict[str, str]] = []

    for info in files:
        tree = ast.parse(info.path.read_text(encoding="utf-8"))
        node_by_line = {node.lineno: node for node in ast.walk(tree) if hasattr(node, "lineno")}
        for symbol in info.symbols:
            if not symbol.docstring:
                continue
            node = node_by_line.get(symbol.lineno)
            if node is None:
                continue
            quality = _docstring_quality(symbol.docstring, node)
            quality_rows.append(
                {
                    "file": str(info.path.relative_to(REPO_ROOT)),
                    "symbol": symbol.name,
                    "kind": symbol.kind,
                    **quality,
                }
            )

    total = len(quality_rows)
    multiline_count = sum(1 for row in quality_rows if row["multiline"] == "yes")
    params_count = sum(1 for row in quality_rows if row["params"] == "yes")
    returns_count = sum(1 for row in quality_rows if row["returns"] == "yes")
    raises_count = sum(1 for row in quality_rows if row["raises"] == "yes")

    lines.append("## Summary\n")
    lines.append(f"- Docstrings evaluated: {total}")
    lines.append(f"- Multi-line docstrings: {multiline_count}")
    lines.append(f"- With params section: {params_count}")
    lines.append(f"- With returns section: {returns_count}")
    lines.append(f"- With raises section: {raises_count}\n")

    lines.append("## Details\n")
    lines.append(
        "| File | Symbol | Type | Multiline | Params | Returns | Raises | Missing Sections |"
    )
    lines.append(
        "|------|--------|------|-----------|--------|---------|--------|------------------|"
    )
    for row in sorted(quality_rows, key=lambda r: (r["file"], r["symbol"])):
        lines.append(
            f"| {row['file']} | {row['symbol']} | {row['kind']} | {row['multiline']} | {row['params']} | {row['returns']} | {row['raises']} | {row['missing_sections']} |"
        )

    OUTPUT_QUALITY.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    files = [collect_file_info(path) for path in sorted(iter_python_files(TARGET_ROOT))]
    write_coverage_report(files)
    write_quality_report(files)


if __name__ == "__main__":
    main()
