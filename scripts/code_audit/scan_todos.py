#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = REPO_ROOT / "smolotchi"
OUTPUT_PATH = REPO_ROOT / "docs-site" / "docs" / "_meta" / "todos.md"

MARKERS = ("TODO", "FIXME", "XXX")


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


def scan_file(path: Path) -> List[str]:
    hits: List[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for marker in MARKERS:
            if marker in line:
                hits.append(f"- {path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
                break
    return hits


def main() -> None:
    lines: List[str] = ["# TODO/FIXME Markers\n"]
    total_hits = 0
    for path in sorted(iter_python_files(TARGET_ROOT)):
        hits = scan_file(path)
        if hits:
            lines.append(f"## {path.relative_to(REPO_ROOT)}\n")
            lines.extend(hits)
            lines.append("")
            total_hits += len(hits)
    lines.insert(1, f"Found {total_hits} markers.\n")
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
