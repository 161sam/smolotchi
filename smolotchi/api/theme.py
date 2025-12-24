import json
from pathlib import Path
from typing import Any, Dict


def load_theme_tokens(path: str) -> Dict[str, str]:
    p = Path(path)
    if not p.exists():
        return {}
    data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    out: Dict[str, str] = {}
    for key, value in data.items():
        out[str(key)] = str(value)
    return out


def tokens_to_css_vars(tokens: Dict[str, str]) -> str:
    parts = []
    for key, value in tokens.items():
        parts.append(f"--{key}: {value};")
    return ":root{" + "".join(parts) + "}"
