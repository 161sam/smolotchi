from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


def _load_toml(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        import tomllib  # py>=3.11

        return tomllib.loads(p.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        import tomli  # type: ignore

        return tomli.loads(p.read_text(encoding="utf-8"))


@dataclass
class CoreCfg:
    tick_interval: float = 1.0
    default_state: str = "WIFI_OBSERVE"


@dataclass
class PolicyCfg:
    allowed_tags: List[str] = field(default_factory=lambda: ["lab-approved"])


@dataclass
class WifiCfg:
    enabled: bool = True
    safe_mode: bool = True


@dataclass
class LanCfg:
    enabled: bool = True
    safe_mode: bool = True
    max_jobs_per_tick: int = 1


@dataclass
class UiCfg:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class ThemeCfg:
    json_path: str = "theme.json"


@dataclass
class AppConfig:
    core: CoreCfg
    policy: PolicyCfg
    wifi: WifiCfg
    lan: LanCfg
    ui: UiCfg
    theme: ThemeCfg


class ConfigStore:
    """
    Singleton-ish store: lädt config.toml, cached, reload on demand oder bei mtime change.
    """

    def __init__(self, path: str = "config.toml"):
        self.path = path
        self._mtime: float = 0.0
        self._cfg: AppConfig = self._from_dict({})

    def _from_dict(self, d: Dict[str, Any]) -> AppConfig:
        core = d.get("core", {})
        policy = d.get("policy", {})
        wifi = d.get("wifi", {})
        lan = d.get("lan", {})
        ui = d.get("ui", {})
        theme = d.get("theme", {})

        return AppConfig(
            core=CoreCfg(
                tick_interval=float(core.get("tick_interval", 1.0)),
                default_state=str(core.get("default_state", "WIFI_OBSERVE")),
            ),
            policy=PolicyCfg(
                allowed_tags=list(policy.get("allowed_tags", ["lab-approved"])),
            ),
            wifi=WifiCfg(
                enabled=bool(wifi.get("enabled", True)),
                safe_mode=bool(wifi.get("safe_mode", True)),
            ),
            lan=LanCfg(
                enabled=bool(lan.get("enabled", True)),
                safe_mode=bool(lan.get("safe_mode", True)),
                max_jobs_per_tick=int(lan.get("max_jobs_per_tick", 1)),
            ),
            ui=UiCfg(
                host=str(ui.get("host", "0.0.0.0")),
                port=int(ui.get("port", 8080)),
            ),
            theme=ThemeCfg(
                json_path=str(theme.get("json_path", "theme.json")),
            ),
        )

    def load(self) -> AppConfig:
        d = _load_toml(self.path)
        self._cfg = self._from_dict(d)
        try:
            self._mtime = Path(self.path).stat().st_mtime
        except OSError:
            self._mtime = time.time()
        return self._cfg

    def get(self) -> AppConfig:
        p = Path(self.path)
        if p.exists():
            m = p.stat().st_mtime
            if m > self._mtime:
                self.load()
        return self._cfg

    def reload(self) -> AppConfig:
        return self.load()
