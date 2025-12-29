#!/usr/bin/env python3
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs-site" / "docs"
CODE_ROOT = REPO_ROOT / "smolotchi"
OUTPUT_PATH = REPO_ROOT / "docs-site" / "docs" / "_meta" / "documentation-gaps.md"


def iter_files(root: Path, suffixes: tuple[str, ...]) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(suffixes):
                yield Path(dirpath) / filename


def read_docs_text() -> str:
    chunks: List[str] = []
    for path in iter_files(DOCS_ROOT, (".md", ".mdx")):
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks).lower()


def is_dataclass(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "dataclass":
            return True
    return False


@dataclass
class ActionClass:
    name: str
    path: Path


@dataclass
class ConfigClass:
    name: str
    fields: List[str]


@dataclass
class Entrypoint:
    module: str
    path: Path


def find_actions() -> List[ActionClass]:
    actions: List[ActionClass] = []
    for path in iter_files(CODE_ROOT / "actions", (".py",)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                actions.append(ActionClass(name=node.name, path=path))
    return actions


def find_config_classes() -> List[ConfigClass]:
    config_path = CODE_ROOT / "core" / "config.py"
    if not config_path.exists():
        return []
    tree = ast.parse(config_path.read_text(encoding="utf-8"))
    configs: List[ConfigClass] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and is_dataclass(node):
            fields: List[str] = []
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    fields.append(child.target.id)
            configs.append(ConfigClass(name=node.name, fields=fields))
    return configs


def find_entrypoints() -> List[Entrypoint]:
    entrypoints: List[Entrypoint] = []
    for path in iter_files(CODE_ROOT, (".py",)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.If):
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and test.comparators[0].value == "__main__"
                ):
                    module = ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
                    entrypoints.append(Entrypoint(module=module, path=path))
    return entrypoints


def main() -> None:
    docs_text = read_docs_text()

    actions = find_actions()
    configs = find_config_classes()
    entrypoints = find_entrypoints()

    lines: List[str] = ["# Documentation Gaps (Code ↔ Docs)\n"]
    lines.append("Documentation presence is detected by string matching in docs-site/docs.\n")

    lines.append("## Undocumented Actions (by class name)\n")
    undocumented_actions = [
        action for action in actions if action.name.lower() not in docs_text
    ]
    if undocumented_actions:
        for action in sorted(undocumented_actions, key=lambda a: a.name):
            lines.append(f"- {action.name} ({action.path.relative_to(REPO_ROOT)})")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Undocumented Config Classes / Fields\n")
    if configs:
        for config in configs:
            class_mentioned = config.name.lower() in docs_text
            missing_fields = [
                field for field in config.fields if field.lower() not in docs_text
            ]
            if not class_mentioned or missing_fields:
                lines.append(f"- {config.name} (smolotchi/core/config.py)")
                if not class_mentioned:
                    lines.append("  - Class name not mentioned in docs")
                if missing_fields:
                    lines.append("  - Fields not mentioned in docs:")
                    for field in missing_fields:
                        lines.append(f"    - {field}")
    else:
        lines.append("- No dataclass configs detected")
    lines.append("")

    lines.append("## Undocumented Entrypoints\n")
    undocumented_entrypoints = [
        entry for entry in entrypoints if entry.module.lower() not in docs_text
    ]
    if undocumented_entrypoints:
        for entry in sorted(undocumented_entrypoints, key=lambda e: e.module):
            lines.append(f"- {entry.module} ({entry.path.relative_to(REPO_ROOT)})")
    else:
        lines.append("- None")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
