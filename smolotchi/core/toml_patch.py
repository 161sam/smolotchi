from __future__ import annotations

import re
from typing import Dict, List


def _ensure_wifi_section(toml_text: str) -> str:
    if not re.search(r"^\[wifi\]\s*$", toml_text, flags=re.MULTILINE):
        toml_text = (
            toml_text.rstrip() + '\n\n[wifi]\nenabled = true\niface = "wlan0"\n'
        )
    return toml_text


def patch_wifi_credentials(toml_text: str, creds: Dict[str, str]) -> str:
    """
    Writes [wifi.credentials] section with normalized formatting:
      "SSID" = "psk"
    Keeps other sections intact.
    Ensures [wifi] exists.
    """
    toml_text = _ensure_wifi_section(toml_text)

    if not re.search(r"^\[wifi\.credentials\]\s*$", toml_text, flags=re.MULTILINE):
        toml_text = toml_text.rstrip() + "\n\n[wifi.credentials]\n"

    match = re.search(r"^\[wifi\.credentials\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return toml_text

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    norm: Dict[str, str] = {}
    for key, value in (creds or {}).items():
        key = (key or "").strip()
        value = (value or "").strip()
        if not key or not value:
            continue
        norm[key] = value

    lines: List[str] = []
    for ssid in sorted(norm.keys()):
        psk = norm[ssid].replace('"', '\\"')
        ssid_safe = ssid.replace('"', '\\"')
        lines.append(f'"{ssid_safe}" = "{psk}"')

    new_block = "\n" + "\n".join(lines) + ("\n" if lines else "\n")

    return toml_text[:start] + new_block + toml_text[end:]


def parse_wifi_credentials_text(text: str) -> Dict[str, str]:
    """
    Parses textarea format:
      SSID=psk
      SSID : psk
      "SSID" = "psk"
    One per line. Ignores comments (#) and blanks.
    """
    out: Dict[str, str] = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if not line:
            continue

        match = re.match(r'^\s*"([^"]+)"\s*=\s*"([^"]+)"\s*$', line)
        if match:
            out[match.group(1).strip()] = match.group(2).strip()
            continue

        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue

        key = key.strip().strip('"')
        value = value.strip().strip('"')
        if key and value:
            out[key] = value
    return out


def patch_wifi_allow_add(toml_text: str, ssid: str) -> str:
    ssid = (ssid or "").strip()
    if not ssid:
        return toml_text
    toml_text = _ensure_wifi_section(toml_text)

    match = re.search(r"^\[wifi\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return toml_text

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    block = toml_text[start:end]
    rx = re.compile(r"^\s*allow_ssids\s*=\s*\[(.*?)\]\s*$", flags=re.MULTILINE)
    mm = rx.search(block)

    def render(items: list[str]) -> str:
        norm = sorted({x.strip() for x in items if x and x.strip()})
        escaped = [x.replace('"', '\\"') for x in norm]
        joined = ", ".join([f'"{x}"' for x in escaped])
        return f"allow_ssids = [{joined}]"

    if mm:
        inner = (mm.group(1) or "").strip()
        items = re.findall(r'"([^"]+)"', inner) if inner else []
        if ssid not in items:
            items.append(ssid)
        block = rx.sub(render(items), block, count=1)
    else:
        line = render([ssid])
        block = ("\n" + line + "\n") + block.lstrip("\n")

    return toml_text[:start] + block + toml_text[end:]


def patch_wifi_scope_map_set(toml_text: str, ssid: str, scope: str) -> str:
    ssid = (ssid or "").strip()
    scope = (scope or "").strip()
    if not ssid or not scope:
        return toml_text

    toml_text = _ensure_wifi_section(toml_text)

    if not re.search(r"^\[wifi\.scope_map\]\s*$", toml_text, flags=re.MULTILINE):
        toml_text = toml_text.rstrip() + "\n\n[wifi.scope_map]\n"

    match = re.search(r"^\[wifi\.scope_map\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return toml_text

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    block = toml_text[start:end]
    line_rx = re.compile(r'^\s*"([^"]+)"\s*=\s*"([^"]+)"\s*$', flags=re.MULTILINE)
    mp: Dict[str, str] = {}
    for mm in line_rx.finditer(block):
        mp[mm.group(1).strip()] = mm.group(2).strip()

    mp[ssid] = scope

    lines: List[str] = []
    for key in sorted(mp.keys()):
        value = mp[key]
        key_safe = key.replace('"', '\\"')
        value_safe = value.replace('"', '\\"')
        lines.append(f'"{key_safe}" = "{value_safe}"')

    new_block = "\n" + "\n".join(lines) + "\n"
    return toml_text[:start] + new_block + toml_text[end:]


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


def _parse_baseline_scopes_block(block: str) -> Dict[str, List[str]]:
    """
    Parse lines like:
      "10.0.10.0/24" = ["a", "b"]
    Returns dict scope -> list(ids)
    """
    scopes: Dict[str, List[str]] = {}
    line_rx = re.compile(r'^\s*"([^"]+)"\s*=\s*\[(.*?)\]\s*$', flags=re.MULTILINE)

    for match in line_rx.finditer(block):
        scope = match.group(1).strip()
        inner = (match.group(2) or "").strip()
        ids = re.findall(r'"([^"]+)"', inner) if inner else []
        scopes[scope] = ids

    return scopes


def _render_baseline_scopes_block(scopes: Dict[str, List[str]]) -> str:
    """
    Renders a normalized block for [baseline.scopes] with sorted keys and values.
    """
    lines: List[str] = []
    for scope in sorted(scopes.keys()):
        ids = scopes[scope]
        norm = sorted({x.strip() for x in ids if x and x.strip()})
        if not norm:
            continue
        joined = ", ".join([f'"{x}"' for x in norm])
        lines.append(f'"{scope}" = [{joined}]')
    if not lines:
        return ""
    return "\n" + "\n".join(lines) + "\n"


def cleanup_baseline_scopes(toml_text: str) -> str:
    """
    Cleans only the [baseline.scopes] section:
      - remove scopes with []
      - sort scope keys
      - dedup + sort ids
      - keep the [baseline.scopes] header
    If the section becomes empty, it will keep just the header (no entries).
    """
    match = re.search(r"^\[baseline\.scopes\]\s*$", toml_text, flags=re.MULTILINE)
    if not match:
        return toml_text

    start = match.end()
    next_header = re.search(r"^\[[^\]]+\]\s*$", toml_text[start:], flags=re.MULTILINE)
    end = start + (next_header.start() if next_header else len(toml_text[start:]))

    block = toml_text[start:end]
    scopes = _parse_baseline_scopes_block(block)
    new_block = _render_baseline_scopes_block(scopes)
    if new_block == "":
        new_block = "\n"

    return toml_text[:start] + new_block + toml_text[end:]
