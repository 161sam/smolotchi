from __future__ import annotations

from typing import Optional, Tuple
import re

CVSS_RE = re.compile(
    r"(CVSS(?:v3(?:\.\d)?)?:?\s*)(\d+(?:\.\d+)?)", re.IGNORECASE
)
RISK_FACTOR_RE = re.compile(
    r"(risk[_\s-]*factor\s*:\s*)(low|medium|high|critical)", re.IGNORECASE
)


def infer_severity(output: str, script_id: str = "") -> Tuple[str, Optional[float], str]:
    """
    Returns: (severity, cvss, reason)
      severity: info|low|medium|high|critical
    """
    out = (output or "").strip()
    sid = (script_id or "").lower()

    m = RISK_FACTOR_RE.search(out)
    if m:
        sev = m.group(2).lower()
        return (sev, None, "risk_factor")

    m = CVSS_RE.search(out)
    if m:
        score = float(m.group(2))
        if score >= 9.0:
            return ("critical", score, "cvss")
        if score >= 7.0:
            return ("high", score, "cvss")
        if score >= 4.0:
            return ("medium", score, "cvss")
        if score > 0:
            return ("low", score, "cvss")
        return ("info", score, "cvss")

    txt = out.lower()
    if "vulnerable" in txt or "is vulnerable" in txt:
        return (
            "high"
            if "remote code execution" in txt or "rce" in txt
            else "medium",
            None,
            "keyword:vulnerable",
        )

    if sid.startswith(("vuln", "vulners")):
        return ("medium" if out else "info", None, "script:vuln_family")

    return ("info", None, "default")
