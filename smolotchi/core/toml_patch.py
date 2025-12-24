from __future__ import annotations

import re
from typing import List


def _toml_list(xs: List[str]) -> str:
    quoted = [f'"{x}"' for x in xs if x]
    return "[" + ", ".join(quoted) + "]"


def patch_lan_lists(toml_text: str, noisy: List[str], allow: List[str]) -> str:
    noisy_line = f"noisy_scripts = {_toml_list(noisy)}"
    allow_line = f"allowlist_scripts = {_toml_list(allow)}"

    match = re.search(r"^\[lan\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return (
            toml_text.rstrip()
            + "\n\n[lan]\n"
            + noisy_line
            + "\n"
            + allow_line
            + "\n"
        )

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    block = toml_text[start:end]

    def upsert_line(block: str, key: str, line: str) -> str:
        rx = re.compile(rf"^\s*{re.escape(key)}\s*=.*$", flags=re.MULTILINE)
        if rx.search(block):
            return rx.sub(line, block, count=1)
        if not block.endswith("\n"):
            block += "\n"
        return block + line + "\n"

    block = upsert_line(block, "noisy_scripts", noisy_line)
    block = upsert_line(block, "allowlist_scripts", allow_line)

    return toml_text[:start] + block + toml_text[end:]


def patch_baseline_add(toml_text: str, scope: str, finding_id: str) -> str:
    scope = scope.strip()
    finding_id = finding_id.strip()

    if not scope or not finding_id:
        return toml_text

    if not re.search(r"^\[baseline\]\s*$", toml_text, flags=re.MULTILINE):
        toml_text = (
            toml_text.rstrip() + "\n\n[baseline]\nenabled = true\n\n[baseline.scopes]\n"
        )

    if not re.search(r"^\[baseline\.scopes\]\s*$", toml_text, flags=re.MULTILINE):
        toml_text = toml_text.rstrip() + "\n\n[baseline.scopes]\n"

    match = re.search(r"^\[baseline\.scopes\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return toml_text

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    block = toml_text[start:end]

    key = f'"{scope}"'
    rx = re.compile(
        rf"^\s*{re.escape(key)}\s*=\s*\[(.*?)\]\s*$", flags=re.MULTILINE
    )

    if rx.search(block):
        def repl(match: re.Match) -> str:
            inner = match.group(1).strip()
            items = re.findall(r'"([^"]+)"', inner) if inner else []
            if finding_id not in items:
                items.append(finding_id)
            joined = ", ".join([f'"{x}"' for x in items])
            return f"{key} = [{joined}]"

        block = rx.sub(repl, block, count=1)
    else:
        if not block.endswith("\n"):
            block += "\n"
        block = block + f'{key} = ["{finding_id}"]\n'

    return toml_text[:start] + block + toml_text[end:]


def patch_baseline_remove(toml_text: str, scope: str, finding_id: str) -> str:
    scope = scope.strip()
    finding_id = finding_id.strip()
    if not scope or not finding_id:
        return toml_text

    match = re.search(r"^\[baseline\.scopes\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return toml_text

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    block = toml_text[start:end]
    key = f'"{scope}"'
    rx = re.compile(
        rf"^\s*{re.escape(key)}\s*=\s*\[(.*?)\]\s*$", flags=re.MULTILINE
    )

    if not rx.search(block):
        return toml_text

    def repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        items = re.findall(r'"([^"]+)"', inner) if inner else []
        items = [x for x in items if x != finding_id]
        joined = ", ".join([f'"{x}"' for x in items])
        return f"{key} = [{joined}]"

    block = rx.sub(repl, block, count=1)

    return toml_text[:start] + block + toml_text[end:]
