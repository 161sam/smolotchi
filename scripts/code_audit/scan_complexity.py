#!/usr/bin/env python3
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = REPO_ROOT / "smolotchi"
OUTPUT_PATH = REPO_ROOT / "docs-site" / "docs" / "_meta" / "tech-debt.md"

MAX_FUNCTION_LOC = 200
MAX_COMPLEXITY = 10
MAX_METHODS_PER_CLASS = 20
MAX_PARAMS_WITHOUT_TYPES = 5


@dataclass
class FunctionMetric:
    qualname: str
    loc: int
    complexity: int
    missing_annotations: bool


@dataclass
class ClassMetric:
    qualname: str
    method_count: int


@dataclass
class ModuleMetric:
    path: Path
    functions: List[FunctionMetric]
    classes: List[ClassMetric]
    global_mutables: List[str]


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


def is_mutable_literal(node: ast.AST) -> bool:
    return isinstance(node, (ast.List, ast.Dict, ast.Set))


def count_complexity(node: ast.AST) -> int:
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.AsyncFor, ast.IfExp, ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.Try):
            complexity += len(child.handlers) or 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(len(child.values) - 1, 0)
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(child.generators)
    return complexity


def has_missing_annotations(node: ast.AST) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if node.returns is None:
        missing_return = True
    else:
        missing_return = False
    args = node.args
    all_args = list(args.args) + list(args.kwonlyargs)
    if args.vararg is not None:
        all_args.append(args.vararg)
    if args.kwarg is not None:
        all_args.append(args.kwarg)
    if all_args and all_args[0].arg in {"self", "cls"}:
        all_args = all_args[1:]
    missing_args = [arg for arg in all_args if arg.annotation is None]
    return missing_return or len(missing_args) >= MAX_PARAMS_WITHOUT_TYPES


def collect_module_metrics(path: Path) -> ModuleMetric:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions: List[FunctionMetric] = []
    classes: List[ClassMetric] = []
    global_mutables: List[str] = []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            if is_mutable_literal(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_mutables.append(target.id)
        if isinstance(node, ast.AnnAssign):
            if is_mutable_literal(node.value):
                if isinstance(node.target, ast.Name):
                    global_mutables.append(node.target.id)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            loc = (node.end_lineno or node.lineno) - node.lineno + 1
            functions.append(
                FunctionMetric(
                    qualname=node.name,
                    loc=loc,
                    complexity=count_complexity(node),
                    missing_annotations=has_missing_annotations(node),
                )
            )
        elif isinstance(node, ast.ClassDef):
            method_count = 0
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_count += 1
                    loc = (child.end_lineno or child.lineno) - child.lineno + 1
                    functions.append(
                        FunctionMetric(
                            qualname=f"{node.name}.{child.name}",
                            loc=loc,
                            complexity=count_complexity(child),
                            missing_annotations=has_missing_annotations(child),
                        )
                    )
            classes.append(ClassMetric(qualname=node.name, method_count=method_count))

    return ModuleMetric(
        path=path,
        functions=functions,
        classes=classes,
        global_mutables=global_mutables,
    )


def format_metric_line(metric: FunctionMetric) -> str:
    parts = [f"{metric.qualname} (LOC: {metric.loc}, complexity: {metric.complexity})"]
    if metric.missing_annotations:
        parts.append("missing annotations")
    return "; ".join(parts)


def build_report(modules: List[ModuleMetric]) -> str:
    lines: List[str] = []
    lines.append("# Tech-Debt (Structural)\n")
    lines.append(
        "Findings are based on static structure. No runtime behavior is inferred.\n"
    )

    for module in modules:
        issues: List[str] = []
        large_functions = [f for f in module.functions if f.loc >= MAX_FUNCTION_LOC]
        complex_functions = [f for f in module.functions if f.complexity >= MAX_COMPLEXITY]
        untyped_functions = [f for f in module.functions if f.missing_annotations]
        large_classes = [c for c in module.classes if c.method_count >= MAX_METHODS_PER_CLASS]

        if large_functions or complex_functions or untyped_functions or large_classes or module.global_mutables:
            rel = module.path.relative_to(REPO_ROOT)
            lines.append(f"### {rel}\n")

        if large_functions:
            lines.append("- Problem: Very large functions (>= 200 LOC)")
            lines.append("  - Risk: Hard to test, unclear error paths")
            lines.append("  - Affected symbols:")
            for func in large_functions:
                lines.append(f"    - {format_metric_line(func)}")
            issues.append("large_functions")

        if complex_functions:
            lines.append("- Problem: High cyclomatic complexity (>= 10)")
            lines.append("  - Risk: Increased branching makes maintenance harder")
            lines.append("  - Affected symbols:")
            for func in complex_functions:
                lines.append(f"    - {format_metric_line(func)}")
            issues.append("complex_functions")

        if untyped_functions:
            lines.append("- Problem: Functions with missing type annotations")
            lines.append("  - Risk: Harder static analysis and refactoring")
            lines.append("  - Affected symbols:")
            for func in untyped_functions:
                lines.append(f"    - {format_metric_line(func)}")
            issues.append("untyped_functions")

        if large_classes:
            lines.append("- Problem: Classes with many methods (>= 20)")
            lines.append("  - Risk: Potential God-object / unclear responsibilities")
            lines.append("  - Affected symbols:")
            for klass in large_classes:
                lines.append(f"    - {klass.qualname} (methods: {klass.method_count})")
            issues.append("large_classes")

        if module.global_mutables:
            lines.append("- Problem: Module-level mutable globals")
            lines.append("  - Risk: Implicit shared state across imports")
            lines.append("  - Affected symbols:")
            for name in module.global_mutables:
                lines.append(f"    - {name}")
            issues.append("global_mutables")

        if issues:
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    modules = [collect_module_metrics(path) for path in sorted(iter_python_files(TARGET_ROOT))]
    OUTPUT_PATH.write_text(build_report(modules), encoding="utf-8")


if __name__ == "__main__":
    main()
