# Code Audit Scripts

These scripts generate the markdown reports in `docs-site/docs/_meta`.
They are offline, deterministic, and rely on Python's standard library.

## Usage

From the repo root:

```bash
python scripts/code_audit/scan_docstrings.py
python scripts/code_audit/scan_complexity.py
python scripts/code_audit/scan_todos.py
python scripts/code_audit/scan_tests.py
python scripts/code_audit/scan_docs.py
python scripts/code_audit/generate_roadmap.py
```

## Outputs

- `scan_docstrings.py` → `docs-site/docs/_meta/docstring-coverage.md`
- `scan_docstrings.py` → `docs-site/docs/_meta/docstring-quality.md`
- `scan_complexity.py` → `docs-site/docs/_meta/tech-debt.md`
- `scan_todos.py` → `docs-site/docs/_meta/todos.md`
- `scan_tests.py` → `docs-site/docs/_meta/test-coverage-gaps.md`
- `scan_docs.py` → `docs-site/docs/_meta/documentation-gaps.md`
- `generate_roadmap.py` → `docs-site/docs/_meta/roadmap-tech-debt.md`
