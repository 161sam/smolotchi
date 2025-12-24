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
