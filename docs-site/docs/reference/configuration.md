# Configuration Reference

The configuration schema is defined by dataclasses in `smolotchi/core/config.py`.

Code: smolotchi/core/config.py:ConfigStore

## Environment variables

| Name | Default | Description | Code Reference |
| --- | --- | --- | --- |
| `SMOLOTCHI_DB` | `/var/lib/smolotchi/events.db` | Override the SQLite DB path. | `smolotchi/core/paths.py:resolve_db_path` |
| `SMOLOTCHI_ARTIFACT_ROOT` | `/var/lib/smolotchi/artifacts` | Override artifact root. | `smolotchi/core/paths.py:resolve_artifact_root` |
| `SMOLOTCHI_LOCK_ROOT` | `/run/smolotchi/locks` | Override lock root. | `smolotchi/core/paths.py:resolve_lock_root` |
| `SMOLOTCHI_CONFIG` | `config.toml` | Override config path. | `smolotchi/core/paths.py:resolve_config_path` |
| `SMOLOTCHI_DEFAULT_TAG` | `lab-approved` | Default tag for actions. | `smolotchi/core/paths.py:resolve_default_tag` |
| `SMOLOTCHI_DEVICE` | `pi_zero` | Device identifier. | `smolotchi/core/paths.py:resolve_device` |
| `SMOLOTCHI_DISPLAY_DRYRUN` | `` | Display dry-run toggle. | `smolotchi/core/paths.py:resolve_display_dryrun` |

## `config.toml` fields

| Name | Type | Default | Description | Code Reference |
| --- | --- | --- | --- | --- |
| `ai.autonomous_include_vuln_assess` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.discovery_ttl_seconds` | `int` | `600` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.portscan_ttl_seconds` | `int` | `900` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.use_cached_discovery` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.use_cached_portscan` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.use_cached_vuln` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.vuln_ttl_http_seconds` | `int` | `600` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.vuln_ttl_seconds` | `int` | `1800` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.vuln_ttl_smb_seconds` | `int` | `1800` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.cache.vuln_ttl_ssh_seconds` | `int` | `3600` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.exec.batch_strategy` | `str` | `per_host` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.exec.concurrency` | `int` | `1` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.exec.cooldown_between_actions_ms` | `int` | `250` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.exec.cooldown_between_hosts_ms` | `int` | `800` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.exec.max_retries` | `int` | `1` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.exec.retry_backoff_ms` | `int` | `800` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.max_hosts_per_plan` | `int` | `16` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.max_steps` | `int` | `80` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.cooldown_multiplier_hard` | `float` | `3.0` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.cooldown_multiplier_soft` | `float` | `1.5` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.loadavg_hard` | `float` | `1.5` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.loadavg_soft` | `float` | `0.9` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.max_cooldown_ms` | `int` | `5000` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.min_cooldown_ms` | `int` | `150` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.temp_hard_c` | `int` | `80` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.temp_multiplier_hard` | `float` | `3.0` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.temp_multiplier_soft` | `float` | `1.5` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.temp_soft_c` | `int` | `70` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ai.throttle.use_cpu_temp` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `baseline.enabled` | `bool` | `False` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `baseline.profiles` | `Dict[str, List[str]]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `baseline.scopes` | `Dict[str, List[str]]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `core.default_state` | `str` | `WIFI_OBSERVE` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `core.tick_interval` | `float` | `1.0` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `invalidation.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `invalidation.invalidate_on_port_change` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `lan.allowlist_scripts` | `List[str]` | `[]` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `lan.default_scope` | `str` | `10.0.10.0/24` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `lan.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `lan.max_jobs_per_tick` | `int` | `1` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `lan.noisy_scripts` | `List[str]` | `[]` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `lan.safe_mode` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `policy.allowed_scopes` | `List[str]` | `['10.0.0.0/8', '192.168.0.0/16']` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `policy.allowed_tags` | `List[str]` | `['lab-approved']` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `policy.allowed_tools` | `List[str]` | `['nmap', 'ip', 'arp', 'ping']` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `policy.autonomous_categories` | `List[str]` | `['network_scan', 'vuln_assess']` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `policy.block_categories` | `List[str]` | `['system_attack', 'file_steal']` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `policy.enable_masscan` | `bool` | `False` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_diff.baseline_host_summary_id` | `str` | `""` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_diff.compare_window_seconds` | `int` | `86400` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_diff.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_diff.max_hosts` | `int` | `50` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.allowlist` | `List[str]` | `[]` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.deny_contains` | `List[str]` | `[]` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.denylist` | `List[str]` | `[]` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.max_findings_per_host` | `int` | `12` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.max_output_chars` | `int` | `600` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_findings.max_output_lines` | `int` | `6` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_normalize.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_normalize.force_severity` | `Dict[str, str]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `report_normalize.force_tag` | `Dict[str, str]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `reports.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `reports.templates_dir` | `str` | `smolotchi/api/templates/reports` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.artifact_kinds_keep_last` | `List[str]` | `['lan_result']` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.artifacts_keep_last` | `int` | `500` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.artifacts_older_than_days` | `int` | `30` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.events_keep_last` | `int` | `5000` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.events_older_than_days` | `int` | `30` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.jobs_done_failed_older_than_days` | `int` | `14` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.jobs_keep_last` | `int` | `1000` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `retention.vacuum_after_prune` | `bool` | `False` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `theme.json_path` | `str` | `theme.json` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ui.host` | `str` | `0.0.0.0` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `ui.port` | `int` | `8080` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `watchdog.action` | `str` | `reset` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `watchdog.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `watchdog.interval_sec` | `int` | `30` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `watchdog.max_resets` | `int` | `2` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `watchdog.min_runtime_sec` | `int` | `60` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `watchdog.stuck_after_sec` | `int` | `300` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.allow_ssids` | `List[str]` | `[]` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.apply_profile_on_connect` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.auto_connect` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.auto_disconnect_on_broken` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.auto_reconnect_on_broken` | `bool` | `False` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.credentials` | `Dict[str, str]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.disconnect_after_lan` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.health_enabled` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.health_interval_sec` | `int` | `20` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.health_ping_gateway` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.health_ping_target` | `str` | `""` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.iface` | `str` | `wlan0` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.lock_during_lan` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.preferred_ssid` | `str` | `""` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.profiles` | `Dict[str, Dict[str, Any]]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.reconnect_on_failure` | `bool` | `False` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.safe_mode` | `bool` | `True` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.scan_interval_sec` | `int` | `30` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
| `wifi.scope_map` | `Dict[str, str]` | `{}` | Defaults from dataclass fields. | `smolotchi/core/config.py` |
