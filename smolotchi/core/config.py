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
class AiExecCfg:
    concurrency: int = 1
    batch_strategy: str = "per_host"
    cooldown_between_actions_ms: int = 250
    cooldown_between_hosts_ms: int = 800
    max_retries: int = 1
    retry_backoff_ms: int = 800


@dataclass
class AiCacheCfg:
    discovery_ttl_seconds: int = 600
    use_cached_discovery: bool = True
    use_cached_portscan: bool = True
    portscan_ttl_seconds: int = 900
    use_cached_vuln: bool = True
    vuln_ttl_seconds: int = 1800
    vuln_ttl_http_seconds: int = 600
    vuln_ttl_ssh_seconds: int = 3600
    vuln_ttl_smb_seconds: int = 1800


@dataclass
class AiThrottleCfg:
    enabled: bool = True
    loadavg_soft: float = 0.90
    loadavg_hard: float = 1.50
    cooldown_multiplier_soft: float = 1.5
    cooldown_multiplier_hard: float = 3.0
    min_cooldown_ms: int = 150
    max_cooldown_ms: int = 5000
    use_cpu_temp: bool = True
    temp_soft_c: int = 70
    temp_hard_c: int = 80
    temp_multiplier_soft: float = 1.5
    temp_multiplier_hard: float = 3.0


@dataclass
class AiCfg:
    max_hosts_per_plan: int = 16
    max_steps: int = 80
    autonomous_include_vuln_assess: bool = True
    exec: AiExecCfg = field(default_factory=AiExecCfg)
    cache: AiCacheCfg = field(default_factory=AiCacheCfg)
    throttle: AiThrottleCfg = field(default_factory=AiThrottleCfg)


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
class ReportFindingsCfg:
    enabled: bool = True
    allowlist: List[str] = field(default_factory=list)
    denylist: List[str] = field(default_factory=list)
    deny_contains: List[str] = field(default_factory=list)
    max_findings_per_host: int = 12
    max_output_chars: int = 600
    max_output_lines: int = 6


@dataclass
class ReportNormalizeCfg:
    enabled: bool = True
    force_severity: Dict[str, str] = field(default_factory=dict)
    force_tag: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReportDiffCfg:
    enabled: bool = True
    compare_window_seconds: int = 86400
    max_hosts: int = 50
    baseline_host_summary_id: str = ""


@dataclass
class InvalidationCfg:
    enabled: bool = True
    invalidate_on_port_change: bool = True


@dataclass
class AppConfig:
    core: CoreCfg
    policy: PolicyCfg
    wifi: WifiCfg
    lan: LanCfg
    ai: AiCfg
    ui: UiCfg
    theme: ThemeCfg
    retention: RetentionCfg
    watchdog: WatchdogCfg
    reports: ReportsCfg
    report_findings: ReportFindingsCfg
    report_normalize: ReportNormalizeCfg
    report_diff: ReportDiffCfg
    invalidation: InvalidationCfg


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
        ai = d.get("ai", {})
        ui = d.get("ui", {})
        theme = d.get("theme", {})
        retention = d.get("retention", {})
        watchdog = d.get("watchdog", {})
        reports = d.get("reports", {})
        report = d.get("report", {}) if isinstance(d.get("report"), dict) else {}
        rf = report.get("findings", {}) if isinstance(report.get("findings"), dict) else {}
        rn = report.get("normalize", {}) if isinstance(report.get("normalize"), dict) else {}
        rd = report.get("diff", {}) if isinstance(report.get("diff"), dict) else {}
        inv = d.get("invalidation", {}) if isinstance(d.get("invalidation"), dict) else {}
        aiexec = (ai.get("exec") or {}) if isinstance(ai.get("exec"), dict) else {}
        aicache = (ai.get("cache") or {}) if isinstance(ai.get("cache"), dict) else {}
        athrottle = (
            (ai.get("throttle") or {}) if isinstance(ai.get("throttle"), dict) else {}
        )

        ai_cfg = AiCfg(
            max_hosts_per_plan=int(ai.get("max_hosts_per_plan", 16)),
            max_steps=int(ai.get("max_steps", 80)),
            autonomous_include_vuln_assess=bool(
                ai.get("autonomous_include_vuln_assess", True)
            ),
        )
        ai_cfg.exec = AiExecCfg(
            concurrency=int(aiexec.get("concurrency", 1)),
            batch_strategy=str(aiexec.get("batch_strategy", "per_host")),
            cooldown_between_actions_ms=int(aiexec.get("cooldown_between_actions_ms", 250)),
            cooldown_between_hosts_ms=int(aiexec.get("cooldown_between_hosts_ms", 800)),
            max_retries=int(aiexec.get("max_retries", 1)),
            retry_backoff_ms=int(aiexec.get("retry_backoff_ms", 800)),
        )
        ai_cfg.cache = AiCacheCfg(
            discovery_ttl_seconds=int(aicache.get("discovery_ttl_seconds", 600)),
            use_cached_discovery=bool(aicache.get("use_cached_discovery", True)),
            use_cached_portscan=bool(aicache.get("use_cached_portscan", True)),
            portscan_ttl_seconds=int(aicache.get("portscan_ttl_seconds", 900)),
            use_cached_vuln=bool(aicache.get("use_cached_vuln", True)),
            vuln_ttl_seconds=int(aicache.get("vuln_ttl_seconds", 1800)),
            vuln_ttl_http_seconds=int(aicache.get("vuln_ttl_http_seconds", 600)),
            vuln_ttl_ssh_seconds=int(aicache.get("vuln_ttl_ssh_seconds", 3600)),
            vuln_ttl_smb_seconds=int(aicache.get("vuln_ttl_smb_seconds", 1800)),
        )
        ai_cfg.throttle = AiThrottleCfg(
            enabled=bool(athrottle.get("enabled", True)),
            loadavg_soft=float(athrottle.get("loadavg_soft", 0.90)),
            loadavg_hard=float(athrottle.get("loadavg_hard", 1.50)),
            cooldown_multiplier_soft=float(
                athrottle.get("cooldown_multiplier_soft", 1.5)
            ),
            cooldown_multiplier_hard=float(
                athrottle.get("cooldown_multiplier_hard", 3.0)
            ),
            min_cooldown_ms=int(athrottle.get("min_cooldown_ms", 150)),
            max_cooldown_ms=int(athrottle.get("max_cooldown_ms", 5000)),
            use_cpu_temp=bool(athrottle.get("use_cpu_temp", True)),
            temp_soft_c=int(athrottle.get("temp_soft_c", 70)),
            temp_hard_c=int(athrottle.get("temp_hard_c", 80)),
            temp_multiplier_soft=float(athrottle.get("temp_multiplier_soft", 1.5)),
            temp_multiplier_hard=float(athrottle.get("temp_multiplier_hard", 3.0)),
        )

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
            ai=ai_cfg,
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
            report_findings=ReportFindingsCfg(
                enabled=bool(rf.get("enabled", True)),
                allowlist=list(rf.get("allowlist", []) or []),
                denylist=list(rf.get("denylist", []) or []),
                deny_contains=list(rf.get("deny_contains", []) or []),
                max_findings_per_host=int(rf.get("max_findings_per_host", 12)),
                max_output_chars=int(rf.get("max_output_chars", 600)),
                max_output_lines=int(rf.get("max_output_lines", 6)),
            ),
            report_normalize=ReportNormalizeCfg(
                enabled=bool(rn.get("enabled", True)),
                force_severity=dict(rn.get("force_severity", {}) or {}),
                force_tag=dict(rn.get("force_tag", {}) or {}),
            ),
            report_diff=ReportDiffCfg(
                enabled=bool(rd.get("enabled", True)),
                compare_window_seconds=int(rd.get("compare_window_seconds", 86400)),
                max_hosts=int(rd.get("max_hosts", 50)),
                baseline_host_summary_id=str(rd.get("baseline_host_summary_id", "")),
            ),
            invalidation=InvalidationCfg(
                enabled=bool(inv.get("enabled", True)),
                invalidate_on_port_change=bool(
                    inv.get("invalidate_on_port_change", True)
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
