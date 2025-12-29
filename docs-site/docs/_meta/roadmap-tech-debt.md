# Roadmap — Tech-Debt Prioritization

This roadmap aggregates the generated reports. Items are derived from counts only.

## Quick Wins

- Address missing docstrings (missing symbols detected in docstring-coverage.md). Approximate count: 766.
- Add tests for modules with no direct test imports. Approximate count: 87.

## Mid-term Refactors

- Reduce complexity hotspots flagged in tech-debt.md. Count of issues: 89.
- Document config and action gaps listed in documentation-gaps.md. Approximate count: 4.

## Architectural Risks

- Modules with large functions or high complexity may hide implicit side-effects.
- Global mutable state increases coupling across imports.
- Sparse test coverage limits refactoring confidence.

## Should-not-touch-before

- Refactors in modules listed under tech-debt.md should wait for baseline tests.
- Changes to config schema should wait for documentation updates to align docs/code.