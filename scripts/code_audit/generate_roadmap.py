#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_META = REPO_ROOT / "docs-site" / "docs" / "_meta"
OUTPUT_PATH = DOCS_META / "roadmap-tech-debt.md"


def count_lines(path: Path, prefix: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(prefix))


def main() -> None:
    docstring_coverage = DOCS_META / "docstring-coverage.md"
    tech_debt = DOCS_META / "tech-debt.md"
    test_gaps = DOCS_META / "test-coverage-gaps.md"
    doc_gaps = DOCS_META / "documentation-gaps.md"

    missing_docstrings = count_lines(docstring_coverage, "| ") - count_lines(docstring_coverage, "| Symbol")
    tech_debt_items = count_lines(tech_debt, "- Problem")
    untested_modules = count_lines(test_gaps, "- smolotchi")
    doc_gaps_items = count_lines(doc_gaps, "- ")

    lines: List[str] = ["# Roadmap — Tech-Debt Prioritization\n"]
    lines.append("This roadmap aggregates the generated reports. Items are derived from counts only.\n")

    lines.append("## Quick Wins\n")
    lines.append(
        f"- Address missing docstrings (missing symbols detected in docstring-coverage.md). Approximate count: {missing_docstrings}."
    )
    lines.append(
        f"- Add tests for modules with no direct test imports. Approximate count: {untested_modules}.\n"
    )

    lines.append("## Mid-term Refactors\n")
    lines.append(
        f"- Reduce complexity hotspots flagged in tech-debt.md. Count of issues: {tech_debt_items}."
    )
    lines.append(
        f"- Document config and action gaps listed in documentation-gaps.md. Approximate count: {doc_gaps_items}.\n"
    )

    lines.append("## Architectural Risks\n")
    lines.append("- Modules with large functions or high complexity may hide implicit side-effects.")
    lines.append("- Global mutable state increases coupling across imports.")
    lines.append("- Sparse test coverage limits refactoring confidence.\n")

    lines.append("## Should-not-touch-before\n")
    lines.append("- Refactors in modules listed under tech-debt.md should wait for baseline tests.")
    lines.append("- Changes to config schema should wait for documentation updates to align docs/code.")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
