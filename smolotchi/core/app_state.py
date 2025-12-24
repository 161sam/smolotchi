from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class AppState:
    baseline_host_summary_id: str = ""


def state_path_for_artifacts(root: str | Path) -> Path:
    return Path(root) / "state" / "baseline.json"


def load_state(path: str | Path) -> AppState:
    p = Path(path)
    if not p.exists():
        return AppState()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return AppState(baseline_host_summary_id=str(data.get("baseline_host_summary_id", "")))
    except Exception:
        return AppState()


def save_state(path: str | Path, state: AppState) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"baseline_host_summary_id": state.baseline_host_summary_id}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
