#!/usr/bin/env python3
from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Iterable, List, Set


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = REPO_ROOT / "smolotchi"
OUTPUT_PATH = REPO_ROOT / "docs-site" / "docs" / "_meta" / "test-coverage-gaps.md"


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


def is_test_file(path: Path) -> bool:
    name = path.name
    return name.startswith("test_") or name.endswith("_test.py")


def module_path(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT)
    return ".".join(rel.with_suffix("").parts)


def collect_imports(path: Path) -> Set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def main() -> None:
    all_modules = [path for path in iter_python_files(TARGET_ROOT) if not is_test_file(path)]
    test_files = [path for path in iter_python_files(TARGET_ROOT) if is_test_file(path)]

    imports_by_test = {path: collect_imports(path) for path in test_files}
    referenced_modules: Set[str] = set()
    for imports in imports_by_test.values():
        for module in imports:
            if module.startswith("smolotchi"):
                referenced_modules.add(module)

    gaps: List[str] = []
    for path in sorted(all_modules):
        module = module_path(path)
        if not any(module == ref or module.startswith(f"{ref}.") for ref in referenced_modules):
            gaps.append(module)

    lines: List[str] = ["# Test Coverage Gaps (Static)\n"]
    lines.append("Tests are detected by file naming (test_*.py, *_test.py) and imports from smolotchi.* modules.\n")

    lines.append("## Tests Discovered\n")
    if test_files:
        for path in sorted(test_files):
            lines.append(f"- {path.relative_to(REPO_ROOT)}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Untested Modules (No direct import from tests found)\n")
    if gaps:
        for module in gaps:
            lines.append(f"- {module}")
    else:
        lines.append("- None")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
