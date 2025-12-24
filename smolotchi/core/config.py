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
    allowed_scopes: List[str] = field(
        default_factory=lambda: ["10.0.0.0/8", "192.168.0.0/16"]
    )
    allowed_tools: List[str] = field(default_factory=lambda: ["nmap", "ip", "arp", "ping"])
    block_categories: List[str] = field(
        default_factory=lambda: ["system_attack", "file_steal"]
    )
    autonomous_categories: List[str] = field(
        default_factory=lambda: ["network_scan", "vuln_assess"]
    )


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
class RetentionCfg:
    events_keep_last: int = 5000
    events_older_than_days: int = 30
    jobs_done_failed_older_than_days: int = 14
    jobs_keep_last: int = 1000
    artifacts_older_than_days: int = 30
    artifacts_keep_last: int = 500
    artifact_kinds_keep_last: List[str] = field(default_factory=lambda: ["lan_result"])
    vacuum_after_prune: bool = False


@dataclass
class WatchdogCfg:
    enabled: bool = True
    running_stuck_after_seconds: int = 180
    action: str = "reset"


@dataclass
class ReportsCfg:
    enabled: bool = True
    templates_dir: str = "smolotchi/api/templates/reports"


@dataclass
class AppConfig:
    core: CoreCfg
    policy: PolicyCfg
    wifi: WifiCfg
    lan: LanCfg
    ui: UiCfg
    theme: ThemeCfg
    retention: RetentionCfg
    watchdog: WatchdogCfg
    reports: ReportsCfg


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
        retention = d.get("retention", {})
        watchdog = d.get("watchdog", {})
        reports = d.get("reports", {})

        return AppConfig(
            core=CoreCfg(
                tick_interval=float(core.get("tick_interval", 1.0)),
                default_state=str(core.get("default_state", "WIFI_OBSERVE")),
            ),
            policy=PolicyCfg(
                allowed_tags=list(policy.get("allowed_tags", ["lab-approved"])),
                allowed_scopes=list(
                    policy.get("allowed_scopes", ["10.0.0.0/8", "192.168.0.0/16"])
                ),
                allowed_tools=list(
                    policy.get("allowed_tools", ["nmap", "ip", "arp", "ping"])
                ),
                block_categories=list(
                    policy.get("block_categories", ["system_attack", "file_steal"])
                ),
                autonomous_categories=list(
                    policy.get("autonomous_categories", ["network_scan", "vuln_assess"])
                ),
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
            retention=RetentionCfg(
                events_keep_last=int(retention.get("events_keep_last", 5000)),
                events_older_than_days=int(retention.get("events_older_than_days", 30)),
                jobs_done_failed_older_than_days=int(
                    retention.get("jobs_done_failed_older_than_days", 14)
                ),
                jobs_keep_last=int(retention.get("jobs_keep_last", 1000)),
                artifacts_older_than_days=int(
                    retention.get("artifacts_older_than_days", 30)
                ),
                artifacts_keep_last=int(retention.get("artifacts_keep_last", 500)),
                artifact_kinds_keep_last=list(
                    retention.get("artifact_kinds_keep_last", ["lan_result"])
                ),
                vacuum_after_prune=bool(retention.get("vacuum_after_prune", False)),
            ),
            watchdog=WatchdogCfg(
                enabled=bool(watchdog.get("enabled", True)),
                running_stuck_after_seconds=int(
                    watchdog.get("running_stuck_after_seconds", 180)
                ),
                action=str(watchdog.get("action", "reset")),
            ),
            reports=ReportsCfg(
                enabled=bool(reports.get("enabled", True)),
                templates_dir=str(
                    reports.get("templates_dir", "smolotchi/api/templates/reports")
                ),
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
