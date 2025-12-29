# Symbol Index

## smolotchi/actions/cache.py
- function: `find_fresh_discovery`
  - Docstring: Find newest action_run for net.host_discovery within ttl.
Returns dict {artifact_id, hosts, ts}.
  - Code: smolotchi/actions/cache.py:find_fresh_discovery
- function: `find_fresh_portscan_for_host`
  - Docstring: Find newest action_run for net.port_scan with payload.target==host within ttl.
Returns {artifact_id, services, ts}.
  - Code: smolotchi/actions/cache.py:find_fresh_portscan_for_host
- function: `find_fresh_vuln_for_host_action`
  - Docstring: Find newest action_run for vuln_* action with payload.target==host within ttl.
If expected_fp is provided, require payload._svc_fp == expected_fp.
  - Code: smolotchi/actions/cache.py:find_fresh_vuln_for_host_action
- function: `put_service_fingerprint`
  - Docstring: Not present
  - Code: smolotchi/actions/cache.py:put_service_fingerprint
- function: `find_latest_fingerprint`
  - Docstring: Not present
  - Code: smolotchi/actions/cache.py:find_latest_fingerprint

## smolotchi/actions/execution.py
- class: `ActionResult`
  - Docstring: Not present
  - Code: smolotchi/actions/execution.py:ActionResult
- function: `run_action_spec`
  - Docstring: Not present
  - Code: smolotchi/actions/execution.py:run_action_spec

## smolotchi/actions/fingerprint.py
- function: `service_fingerprint`
  - Docstring: Stable hash of relevant open-service facts.
Only include fields that matter for planning & cache invalidation.
  - Code: smolotchi/actions/fingerprint.py:service_fingerprint
- function: `service_fingerprint_by_key`
  - Docstring: Returns fingerprints for coarse service groups: http/ssh/smb.
Only includes services that match each key.
  - Code: smolotchi/actions/fingerprint.py:service_fingerprint_by_key

## smolotchi/actions/parse.py
- function: `parse_nmap_xml_up_hosts`
  - Docstring: Extract IPv4 addresses of hosts with <status state="up"> from Nmap XML.
  - Code: smolotchi/actions/parse.py:parse_nmap_xml_up_hosts

## smolotchi/actions/parse_services.py
- function: `parse_nmap_xml_services`
  - Docstring: Returns:
  { "1.2.3.4": [ {port:22, proto:"tcp", name:"ssh", product:"OpenSSH", version:"9.3", tunnel:"", state:"open"} ] }
  - Code: smolotchi/actions/parse_services.py:parse_nmap_xml_services
- function: `summarize_service_keys`
  - Docstring: Produces coarse service keys for planning (ssh/http/smb/rdp/etc).
  - Code: smolotchi/actions/parse_services.py:summarize_service_keys

## smolotchi/actions/plan_runner.py
- class: `PlanRunner`
  - Docstring: Executes an ActionPlan step-by-step.

Guarantees:
- registry validation
- policy gate (risk)
- progress events
- cancel / reset support
  - Code: smolotchi/actions/plan_runner.py:PlanRunner
- class: `BatchPlanRunner`
  - Docstring: Not present
  - Code: smolotchi/actions/plan_runner.py:BatchPlanRunner

## smolotchi/actions/planners/ai_planner.py
- class: `PlanCandidate`
  - Docstring: Not present
  - Code: smolotchi/actions/planners/ai_planner.py:PlanCandidate
- class: `PlanStep`
  - Docstring: Not present
  - Code: smolotchi/actions/planners/ai_planner.py:PlanStep
- class: `ActionPlan`
  - Docstring: Not present
  - Code: smolotchi/actions/planners/ai_planner.py:ActionPlan
- class: `AIPlanner`
  - Docstring: Smolotchi AI Planner v1 (Research)

- Deterministic
- Policy-gated
- Explainable
- Registry-driven
- No exploitation by default

Future:
- RL hook points
- Exploit selection gates
  - Code: smolotchi/actions/planners/ai_planner.py:AIPlanner

## smolotchi/actions/registry.py
- class: `UnknownAction`
  - Docstring: Not present
  - Code: smolotchi/actions/registry.py:UnknownAction
- class: `ActionImpl`
  - Docstring: Not present
  - Code: smolotchi/actions/registry.py:ActionImpl
- class: `ActionRegistry`
  - Docstring: Not present
  - Code: smolotchi/actions/registry.py:ActionRegistry
- function: `_spec_from_dict`
  - Docstring: Not present
  - Code: smolotchi/actions/registry.py:_spec_from_dict
- function: `load_pack`
  - Docstring: Not present
  - Code: smolotchi/actions/registry.py:load_pack

## smolotchi/actions/runner.py
- class: `ActionRunner`
  - Docstring: Not present
  - Code: smolotchi/actions/runner.py:ActionRunner

## smolotchi/actions/schema.py
- class: `ActionSpec`
  - Docstring: Not present
  - Code: smolotchi/actions/schema.py:ActionSpec

## smolotchi/actions/summary.py
- function: `build_host_summary`
  - Docstring: Not present
  - Code: smolotchi/actions/summary.py:build_host_summary

## smolotchi/actions/throttle.py
- class: `ThrottleDecision`
  - Docstring: Not present
  - Code: smolotchi/actions/throttle.py:ThrottleDecision
- function: `read_loadavg_1m`
  - Docstring: Not present
  - Code: smolotchi/actions/throttle.py:read_loadavg_1m
- function: `read_cpu_temp_c`
  - Docstring: Not present
  - Code: smolotchi/actions/throttle.py:read_cpu_temp_c
- function: `decide_multiplier`
  - Docstring: Not present
  - Code: smolotchi/actions/throttle.py:decide_multiplier

## smolotchi/ai/errors.py
- class: `StageRequired`
  - Docstring: Raised when a policy blocks an action with risk='caution' and we must request approval.
  - Code: smolotchi/ai/errors.py:StageRequired

## smolotchi/ai/replay.py
- class: `ReplayMetrics`
  - Docstring: Not present
  - Code: smolotchi/ai/replay.py:ReplayMetrics
- function: `_collect_links`
  - Docstring: Not present
  - Code: smolotchi/ai/replay.py:_collect_links
- function: `baseline_delta_from_bundles`
  - Docstring: Not present
  - Code: smolotchi/ai/replay.py:baseline_delta_from_bundles
- function: `evaluate_plan_run`
  - Docstring: Not present
  - Code: smolotchi/ai/replay.py:evaluate_plan_run
- function: `metrics_row`
  - Docstring: Not present
  - Code: smolotchi/ai/replay.py:metrics_row

## smolotchi/ai/worker.py
- class: `WorkerState`
  - Docstring: Not present
  - Code: smolotchi/ai/worker.py:WorkerState
- class: `AIWorker`
  - Docstring: Single-thread worker:
- listens for ui.ai.run_plan events
- loads ai_plan artifact
- executes via PlanRunner
- emits health ticks
  - Code: smolotchi/ai/worker.py:AIWorker
- function: `_build_policy`
  - Docstring: Not present
  - Code: smolotchi/ai/worker.py:_build_policy
- function: `_build_registry`
  - Docstring: Not present
  - Code: smolotchi/ai/worker.py:_build_registry
- function: `main`
  - Docstring: Not present
  - Code: smolotchi/ai/worker.py:main

## smolotchi/api/conftest.py
- function: `client`
  - Docstring: Not present
  - Code: smolotchi/api/conftest.py:client

## smolotchi/api/health.py
- function: `core_health_ok`
  - Docstring: Not present
  - Code: smolotchi/api/health.py:core_health_ok
- function: `worker_health_ok`
  - Docstring: Not present
  - Code: smolotchi/api/health.py:worker_health_ok

## smolotchi/api/theme.py
- function: `load_theme_tokens`
  - Docstring: Not present
  - Code: smolotchi/api/theme.py:load_theme_tokens
- function: `tokens_to_css_vars`
  - Docstring: Not present
  - Code: smolotchi/api/theme.py:tokens_to_css_vars

## smolotchi/api/view_models.py
- function: `effective_lan_overrides`
  - Docstring: Not present
  - Code: smolotchi/api/view_models.py:effective_lan_overrides

## smolotchi/api/web.py
- function: `pretty`
  - Docstring: Not present
  - Code: smolotchi/api/web.py:pretty
- function: `_atomic_write_text`
  - Docstring: Not present
  - Code: smolotchi/api/web.py:_atomic_write_text
- function: `create_app`
  - Docstring: Not present
  - Code: smolotchi/api/web.py:create_app

## smolotchi/cli.py
- function: `_format_ts`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_format_ts
- function: `_print_json`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_print_json
- function: `_print_table`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_print_table
- function: `cmd_web`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_web
- function: `cmd_display`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_display
- function: `cmd_core`
  - Docstring: Minimaler Core-Daemon: tickt State-Machine periodisch.
(v0.0.1 tickte im Web-Request – jetzt unabhängig)
  - Code: smolotchi/cli.py:cmd_core
- function: `cmd_status`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_status
- function: `cmd_events`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_events
- function: `cmd_wifi_scan`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_wifi_scan
- function: `cmd_wifi_connect`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_wifi_connect
- function: `cmd_wifi_status`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_wifi_status
- function: `cmd_jobs_enqueue`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_jobs_enqueue
- function: `cmd_jobs_list`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_jobs_list
- function: `cmd_jobs_get`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_jobs_get
- function: `cmd_jobs_tail`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_jobs_tail
- function: `_stage_approval_index`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_stage_approval_index
- function: `cmd_stages_list`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_stages_list
- function: `cmd_stages_approve`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_stages_approve
- function: `cmd_health`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_health
- function: `cmd_job_cancel`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_job_cancel
- function: `cmd_job_reset`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_job_reset
- function: `cmd_job_delete`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_job_delete
- function: `cmd_prune`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_prune
- function: `cmd_handoff`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_handoff
- function: `cmd_lan_done`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_lan_done
- function: `cmd_diff_baseline_set`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_diff_baseline_set
- function: `cmd_diff_baseline_show`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_diff_baseline_show
- function: `_resolve_profile_key`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_resolve_profile_key
- function: `cmd_profile_timeline`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_profile_timeline
- function: `cmd_baseline_show`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_baseline_show
- function: `cmd_baseline_diff`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_baseline_diff
- function: `cmd_finding_history`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_finding_history
- function: `cmd_dossier_build`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_dossier_build
- function: `_write_text`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_write_text
- function: `_write_json`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_write_json
- function: `cmd_ai_replay`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_ai_replay
- function: `cmd_ai_replay_batch`
  - Docstring: Not present
  - Code: smolotchi/cli.py:cmd_ai_replay_batch
- function: `_write_unit`
  - Docstring: Not present
  - Code: smolotchi/cli.py:_write_unit
- function: `cmd_install_systemd`
  - Docstring: Installiert systemd units nach /etc/systemd/system.
  - Code: smolotchi/cli.py:cmd_install_systemd
- function: `add_ai_subcommands`
  - Docstring: Not present
  - Code: smolotchi/cli.py:add_ai_subcommands
- function: `build_parser`
  - Docstring: Not present
  - Code: smolotchi/cli.py:build_parser
- function: `main`
  - Docstring: Not present
  - Code: smolotchi/cli.py:main

## smolotchi/cli_artifacts.py
- function: `_format_ts`
  - Docstring: Not present
  - Code: smolotchi/cli_artifacts.py:_format_ts
- function: `_print_json`
  - Docstring: Not present
  - Code: smolotchi/cli_artifacts.py:_print_json
- function: `_print_table`
  - Docstring: Not present
  - Code: smolotchi/cli_artifacts.py:_print_table
- function: `add_artifacts_subcommands`
  - Docstring: Not present
  - Code: smolotchi/cli_artifacts.py:add_artifacts_subcommands

## smolotchi/cli_profiles.py
- function: `add_profiles_subcommands`
  - Docstring: Not present
  - Code: smolotchi/cli_profiles.py:add_profiles_subcommands

## smolotchi/core/app_state.py
- class: `AppState`
  - Docstring: Not present
  - Code: smolotchi/core/app_state.py:AppState
- function: `state_path_for_artifacts`
  - Docstring: Not present
  - Code: smolotchi/core/app_state.py:state_path_for_artifacts
- function: `load_state`
  - Docstring: Not present
  - Code: smolotchi/core/app_state.py:load_state
- function: `save_state`
  - Docstring: Not present
  - Code: smolotchi/core/app_state.py:save_state

## smolotchi/core/artifacts.py
- class: `ArtifactMeta`
  - Docstring: Not present
  - Code: smolotchi/core/artifacts.py:ArtifactMeta
- class: `ArtifactStore`
  - Docstring: Not present
  - Code: smolotchi/core/artifacts.py:ArtifactStore

## smolotchi/core/artifacts_gc.py
- class: `GCPlan`
  - Docstring: Not present
  - Code: smolotchi/core/artifacts_gc.py:GCPlan
- function: `_extract_ref_ids_from_bundle`
  - Docstring: Bundle schema varies a bit over time; we defensively collect all common refs.
  - Code: smolotchi/core/artifacts_gc.py:_extract_ref_ids_from_bundle
- function: `plan_gc`
  - Docstring: Keep:
  - N newest lan_bundle (and everything referenced by them)
  - M newest lan_report (in case some reports exist without a bundle reference)
Delete:
  - everything else (best-effort listing)
  - Code: smolotchi/core/artifacts_gc.py:plan_gc
- function: `_safe_unlink`
  - Docstring: Not present
  - Code: smolotchi/core/artifacts_gc.py:_safe_unlink
- function: `apply_gc`
  - Docstring: Returns (deleted_count, failed_count)
Deletion is best-effort: remove underlying file path if present.
If ArtifactStore exposes a delete() method, we use it.
  - Code: smolotchi/core/artifacts_gc.py:apply_gc

## smolotchi/core/bus.py
- class: `Event`
  - Docstring: Not present
  - Code: smolotchi/core/bus.py:Event
- class: `SQLiteBus`
  - Docstring: Minimaler Event-Bus: append-only Events in SQLite.
Reicht für v0.0.1 + lässt sich später durch Redis/MQTT ersetzen.
  - Code: smolotchi/core/bus.py:SQLiteBus

## smolotchi/core/config.py
- function: `_load_toml`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:_load_toml
- class: `CoreCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:CoreCfg
- class: `PolicyCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:PolicyCfg
- class: `WifiCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:WifiCfg
- class: `LanCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:LanCfg
- class: `AiExecCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:AiExecCfg
- class: `AiCacheCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:AiCacheCfg
- class: `AiThrottleCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:AiThrottleCfg
- class: `AiCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:AiCfg
- class: `UiCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:UiCfg
- class: `ThemeCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:ThemeCfg
- class: `RetentionCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:RetentionCfg
- class: `WatchdogCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:WatchdogCfg
- class: `ReportsCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:ReportsCfg
- class: `ReportFindingsCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:ReportFindingsCfg
- class: `ReportNormalizeCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:ReportNormalizeCfg
- class: `ReportDiffCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:ReportDiffCfg
- class: `InvalidationCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:InvalidationCfg
- class: `BaselineCfg`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:BaselineCfg
- class: `AppConfig`
  - Docstring: Not present
  - Code: smolotchi/core/config.py:AppConfig
- class: `ConfigStore`
  - Docstring: Singleton-ish store: lädt config.toml, cached, reload on demand oder bei mtime change.
  - Code: smolotchi/core/config.py:ConfigStore

## smolotchi/core/dossier.py
- function: `build_lan_dossier`
  - Docstring: Create a lan_dossier artifact that merges:
  - WiFi→LAN timeline entry (best-effort)
  - LAN result bundle/report resolution
  - policy decisions (best-effort)
  - host summaries (best-effort)
Returns artifact_id of the dossier.
  - Code: smolotchi/core/dossier.py:build_lan_dossier

## smolotchi/core/engines.py
- class: `EngineHealth`
  - Docstring: Not present
  - Code: smolotchi/core/engines.py:EngineHealth
- class: `Engine`
  - Docstring: Not present
  - Code: smolotchi/core/engines.py:Engine
- class: `EngineRegistry`
  - Docstring: Not present
  - Code: smolotchi/core/engines.py:EngineRegistry

## smolotchi/core/jobs.py
- class: `JobRow`
  - Docstring: Not present
  - Code: smolotchi/core/jobs.py:JobRow
- class: `JobStore`
  - Docstring: Not present
  - Code: smolotchi/core/jobs.py:JobStore

## smolotchi/core/lan_resolver.py
- function: `resolve_result_by_job_id`
  - Docstring: Preferred resolver:
1) Try lan_job_result artifacts (stable mapping)
Fallback resolver:
2) Try lan_bundle by job_id (fast)
3) Else: scan artifacts index for lan_result/lan_report and correlate via content.job.id
  - Code: smolotchi/core/lan_resolver.py:resolve_result_by_job_id

## smolotchi/core/lan_state.py
- function: `lan_is_busy`
  - Docstring: Not present
  - Code: smolotchi/core/lan_state.py:lan_is_busy

## smolotchi/core/normalize.py
- function: `normalize_profile`
  - Docstring: Returns (normalized_profile, warnings)
  - Code: smolotchi/core/normalize.py:normalize_profile
- function: `profile_hash`
  - Docstring: Not present
  - Code: smolotchi/core/normalize.py:profile_hash

## smolotchi/core/paths.py
- function: `resolve_db_path`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_db_path
- function: `resolve_artifact_root`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_artifact_root
- function: `resolve_lock_root`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_lock_root
- function: `resolve_config_path`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_config_path
- function: `resolve_default_tag`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_default_tag
- function: `resolve_device`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_device
- function: `resolve_display_dryrun`
  - Docstring: Not present
  - Code: smolotchi/core/paths.py:resolve_display_dryrun

## smolotchi/core/policy.py
- class: `Policy`
  - Docstring: v0.0.1: simple allowlist.
Später: Profiles, human confirmation, audit, scope by VLAN/SSID etc.
  - Code: smolotchi/core/policy.py:Policy
- class: `PolicyDecision`
  - Docstring: Not present
  - Code: smolotchi/core/policy.py:PolicyDecision
- function: `evaluate_tool_action`
  - Docstring: Pi-Zero friendly: simple, deterministic gate for tool execution.
  - Code: smolotchi/core/policy.py:evaluate_tool_action

## smolotchi/core/reports.py
- class: `ReportConfig`
  - Docstring: Not present
  - Code: smolotchi/core/reports.py:ReportConfig
- class: `ReportRenderer`
  - Docstring: Not present
  - Code: smolotchi/core/reports.py:ReportRenderer

## smolotchi/core/resources.py
- class: `Lease`
  - Docstring: Not present
  - Code: smolotchi/core/resources.py:Lease
- class: `ResourceManager`
  - Docstring: Super simple file-based leases (atomic create). Pi-friendly.
Resources: 'wifi', 'display', ... (du kannst erweitern)
  - Code: smolotchi/core/resources.py:ResourceManager

## smolotchi/core/self_heal.py
- class: `SelfHealer`
  - Docstring: Not present
  - Code: smolotchi/core/self_heal.py:SelfHealer

## smolotchi/core/state.py
- class: `CoreStatus`
  - Docstring: Not present
  - Code: smolotchi/core/state.py:CoreStatus
- class: `SmolotchiCore`
  - Docstring: Not present
  - Code: smolotchi/core/state.py:SmolotchiCore

## smolotchi/core/toml_patch.py
- function: `_ensure_wifi_section`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:_ensure_wifi_section
- function: `patch_wifi_credentials`
  - Docstring: Writes [wifi.credentials] section with normalized formatting:
  "SSID" = "psk"
Keeps other sections intact.
Ensures [wifi] exists.
  - Code: smolotchi/core/toml_patch.py:patch_wifi_credentials
- function: `parse_wifi_credentials_text`
  - Docstring: Parses textarea format:
  SSID=psk
  SSID : psk
  "SSID" = "psk"
One per line. Ignores comments (#) and blanks.
  - Code: smolotchi/core/toml_patch.py:parse_wifi_credentials_text
- function: `parse_wifi_profiles_text`
  - Docstring: INI-like:
  [SSID]
  key=value
Supported value types:
  true/false -> bool
  int/float
  otherwise string
  - Code: smolotchi/core/toml_patch.py:parse_wifi_profiles_text
- function: `patch_wifi_profiles_set`
  - Docstring: Writes profiles as:
  [wifi.profiles."SSID"]
  key = value
Replaces the whole wifi.profiles tree (all SSIDs) deterministically.
Keeps other parts of config intact.
  - Code: smolotchi/core/toml_patch.py:patch_wifi_profiles_set
- function: `patch_wifi_profile_upsert`
  - Docstring: Upsert a single profile block:
  [wifi.profiles."SSID"]
  ...
Leaves other SSID blocks intact (but normalizes this SSID).
  - Code: smolotchi/core/toml_patch.py:patch_wifi_profile_upsert
- function: `patch_wifi_allow_add`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_wifi_allow_add
- function: `patch_wifi_allow_remove`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_wifi_allow_remove
- function: `patch_wifi_scope_map_set`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_wifi_scope_map_set
- function: `patch_wifi_scope_map_remove`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_wifi_scope_map_remove
- function: `_toml_list`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:_toml_list
- function: `patch_lan_lists`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_lan_lists
- function: `patch_baseline_add`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_baseline_add
- function: `patch_baseline_remove`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_baseline_remove
- function: `_parse_baseline_scopes_block`
  - Docstring: Parse lines like:
  "10.0.10.0/24" = ["a", "b"]
Returns dict scope -> list(ids)
  - Code: smolotchi/core/toml_patch.py:_parse_baseline_scopes_block
- function: `_render_baseline_scopes_block`
  - Docstring: Renders a normalized block for [baseline.scopes] with sorted keys and values.
  - Code: smolotchi/core/toml_patch.py:_render_baseline_scopes_block
- function: `cleanup_baseline_scopes`
  - Docstring: Cleans only the [baseline.scopes] section:
  - remove scopes with []
  - sort scope keys
  - dedup + sort ids
  - keep the [baseline.scopes] header
If the section becomes empty, it will keep just the header (no entries).
  - Code: smolotchi/core/toml_patch.py:cleanup_baseline_scopes
- function: `patch_baseline_profile_add`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_baseline_profile_add
- function: `patch_baseline_profile_remove`
  - Docstring: Not present
  - Code: smolotchi/core/toml_patch.py:patch_baseline_profile_remove
- function: `cleanup_baseline_profiles`
  - Docstring: Normalize [baseline.profiles."..."] blocks:
  - dedup + sort expected_findings
  - remove empty expected_findings lists
  - Code: smolotchi/core/toml_patch.py:cleanup_baseline_profiles

## smolotchi/core/validate.py
- function: `validate_profiles`
  - Docstring: Not present
  - Code: smolotchi/core/validate.py:validate_profiles

## smolotchi/core/watchdog.py
- class: `SystemdWatchdog`
  - Docstring: Not present
  - Code: smolotchi/core/watchdog.py:SystemdWatchdog
- class: `JobWatchdog`
  - Docstring: Not present
  - Code: smolotchi/core/watchdog.py:JobWatchdog

## smolotchi/device/buttons.py
- class: `ButtonConfig`
  - Docstring: Not present
  - Code: smolotchi/device/buttons.py:ButtonConfig
- class: `ButtonWatcher`
  - Docstring: Not present
  - Code: smolotchi/device/buttons.py:ButtonWatcher

## smolotchi/device/power.py
- class: `PowerStatus`
  - Docstring: Not present
  - Code: smolotchi/device/power.py:PowerStatus
- function: `_read_first_capacity_sysfs`
  - Docstring: Not present
  - Code: smolotchi/device/power.py:_read_first_capacity_sysfs
- class: `PowerMonitor`
  - Docstring: Not present
  - Code: smolotchi/device/power.py:PowerMonitor

## smolotchi/device/profile.py
- class: `DeviceProfile`
  - Docstring: Not present
  - Code: smolotchi/device/profile.py:DeviceProfile
- function: `get_device_profile`
  - Docstring: Not present
  - Code: smolotchi/device/profile.py:get_device_profile

## smolotchi/display/displayd.py
- class: `UIState`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:UIState
- function: `_utc_iso`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:_utc_iso
- function: `_safe_font`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:_safe_font
- function: `_render_text_screen`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:_render_text_screen
- function: `_dryrun_enabled`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:_dryrun_enabled
- function: `main`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:main
- function: `_poll_buttons`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:_poll_buttons
- function: `_tick_render`
  - Docstring: Not present
  - Code: smolotchi/display/displayd.py:_tick_render

## smolotchi/display/render.py
- function: `render_state`
  - Docstring: Not present
  - Code: smolotchi/display/render.py:render_state

## smolotchi/display/waveshare_driver.py
- class: `EPDDriver`
  - Docstring: Abstraktion, damit Smolotchi ohne Display booten kann.
  - Code: smolotchi/display/waveshare_driver.py:EPDDriver

## smolotchi/engines/lan_engine.py
- class: `LanConfig`
  - Docstring: Not present
  - Code: smolotchi/engines/lan_engine.py:LanConfig
- class: `LanEngine`
  - Docstring: Not present
  - Code: smolotchi/engines/lan_engine.py:LanEngine

## smolotchi/engines/net_detect.py
- function: `_run`
  - Docstring: Not present
  - Code: smolotchi/engines/net_detect.py:_run
- function: `detect_ipv4_cidr`
  - Docstring: Returns e.g. '10.0.10.23/24' or None.
Uses: ip -4 addr show dev <iface>
  - Code: smolotchi/engines/net_detect.py:detect_ipv4_cidr
- function: `cidr_to_network_scope`
  - Docstring: '10.0.10.23/24' -> '10.0.10.0/24'
No external libs; pure integer math.
  - Code: smolotchi/engines/net_detect.py:cidr_to_network_scope
- function: `detect_scope_for_iface`
  - Docstring: Not present
  - Code: smolotchi/engines/net_detect.py:detect_scope_for_iface

## smolotchi/engines/net_health.py
- function: `_run`
  - Docstring: Not present
  - Code: smolotchi/engines/net_health.py:_run
- function: `default_gateway`
  - Docstring: Not present
  - Code: smolotchi/engines/net_health.py:default_gateway
- function: `has_default_route`
  - Docstring: Not present
  - Code: smolotchi/engines/net_health.py:has_default_route
- function: `ping`
  - Docstring: Not present
  - Code: smolotchi/engines/net_health.py:ping
- function: `health_check`
  - Docstring: Not present
  - Code: smolotchi/engines/net_health.py:health_check

## smolotchi/engines/tools_engine.py
- class: `ToolsEngine`
  - Docstring: Not present
  - Code: smolotchi/engines/tools_engine.py:ToolsEngine

## smolotchi/engines/wifi_connect.py
- function: `_run`
  - Docstring: Not present
  - Code: smolotchi/engines/wifi_connect.py:_run
- function: `connect_wpa_psk`
  - Docstring: Lab-safe: connect only using provided credentials.
Uses wpa_supplicant + dhclient.
  - Code: smolotchi/engines/wifi_connect.py:connect_wpa_psk
- function: `disconnect_wpa`
  - Docstring: Not present
  - Code: smolotchi/engines/wifi_connect.py:disconnect_wpa

## smolotchi/engines/wifi_engine.py
- class: `WifiEngine`
  - Docstring: Not present
  - Code: smolotchi/engines/wifi_engine.py:WifiEngine

## smolotchi/engines/wifi_scan.py
- class: `WifiAP`
  - Docstring: Not present
  - Code: smolotchi/engines/wifi_scan.py:WifiAP
- function: `_run`
  - Docstring: Not present
  - Code: smolotchi/engines/wifi_scan.py:_run
- function: `scan_iw`
  - Docstring: Uses: iw dev <iface> scan
Parses minimal fields: SSID, BSSID, freq, signal.
  - Code: smolotchi/engines/wifi_scan.py:scan_iw

## smolotchi/engines/wifi_targets.py
- function: `update_targets_state`
  - Docstring: Not present
  - Code: smolotchi/engines/wifi_targets.py:update_targets_state

## smolotchi/merge/sources.py
- function: `_safe_dict`
  - Docstring: Not present
  - Code: smolotchi/merge/sources.py:_safe_dict
- function: `find_wifi_context_for_job`
  - Docstring: Scan newest wifi_lan_timeline entries and return the newest entry matching job_id.
  - Code: smolotchi/merge/sources.py:find_wifi_context_for_job
- function: `list_policy_events_for_job`
  - Docstring: Heuristic: scan recent events and pick those with job_id / request_id correlation.
Later we’ll switch to explicit policy artifacts.
  - Code: smolotchi/merge/sources.py:list_policy_events_for_job
- function: `list_host_summaries_for_job`
  - Docstring: Preferred: host_summary artifacts carry job_id in payload.meta/job_id (we’ll standardize this).
Fallback: scan newest host_summary and accept those within same time window (handled in timeline merge).
  - Code: smolotchi/merge/sources.py:list_host_summaries_for_job
- function: `get_lan_result_for_job`
  - Docstring: Not present
  - Code: smolotchi/merge/sources.py:get_lan_result_for_job

## smolotchi/merge/timeline.py
- function: `_safe_dict`
  - Docstring: Not present
  - Code: smolotchi/merge/timeline.py:_safe_dict
- function: `_ts`
  - Docstring: Not present
  - Code: smolotchi/merge/timeline.py:_ts
- function: `build_dossier`
  - Docstring: Not present
  - Code: smolotchi/merge/timeline.py:build_dossier

## smolotchi/parsers/base.py
- class: `ParserResult`
  - Docstring: Not present
  - Code: smolotchi/parsers/base.py:ParserResult
- class: `BaseParser`
  - Docstring: Not present
  - Code: smolotchi/parsers/base.py:BaseParser

## smolotchi/parsers/bettercap.py
- class: `BettercapParser`
  - Docstring: Not present
  - Code: smolotchi/parsers/bettercap.py:BettercapParser

## smolotchi/parsers/masscan.py
- class: `MasscanParser`
  - Docstring: Not present
  - Code: smolotchi/parsers/masscan.py:MasscanParser

## smolotchi/parsers/merge.py
- function: `merge_hosts`
  - Docstring: Not present
  - Code: smolotchi/parsers/merge.py:merge_hosts

## smolotchi/parsers/nmap.py
- class: `NmapParser`
  - Docstring: Not present
  - Code: smolotchi/parsers/nmap.py:NmapParser

## smolotchi/parsers/registry.py
- function: `parse`
  - Docstring: Not present
  - Code: smolotchi/parsers/registry.py:parse

## smolotchi/reports/aggregate.py
- function: `_ts_human`
  - Docstring: Not present
  - Code: smolotchi/reports/aggregate.py:_ts_human
- function: `_extract_host_from_action_run`
  - Docstring: Not present
  - Code: smolotchi/reports/aggregate.py:_extract_host_from_action_run
- function: `_action_summary`
  - Docstring: Not present
  - Code: smolotchi/reports/aggregate.py:_action_summary
- function: `build_aggregate_model`
  - Docstring: Not present
  - Code: smolotchi/reports/aggregate.py:build_aggregate_model
- function: `build_aggregate_report`
  - Docstring: Not present
  - Code: smolotchi/reports/aggregate.py:build_aggregate_report

## smolotchi/reports/badges.py
- function: `_rank`
  - Docstring: Not present
  - Code: smolotchi/reports/badges.py:_rank
- function: `summarize_host_findings`
  - Docstring: Not present
  - Code: smolotchi/reports/badges.py:summarize_host_findings

## smolotchi/reports/baseline.py
- function: `expected_findings_for_scope`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:expected_findings_for_scope
- function: `profile_key_for_job_meta`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:profile_key_for_job_meta
- function: `expected_findings_for_profile`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:expected_findings_for_profile
- function: `expected_findings_for_bundle`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:expected_findings_for_bundle
- function: `expected_findings_for_profile_dict`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:expected_findings_for_profile_dict
- function: `expected_findings_for_scope_dict`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:expected_findings_for_scope_dict
- function: `summarize_baseline_status`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline.py:summarize_baseline_status

## smolotchi/reports/baseline_diff.py
- class: `BaselineDiff`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline_diff.py:BaselineDiff
- function: `_bundle_findings`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline_diff.py:_bundle_findings
- function: `collect_seen_findings`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline_diff.py:collect_seen_findings
- function: `compute_baseline_diff`
  - Docstring: Not present
  - Code: smolotchi/reports/baseline_diff.py:compute_baseline_diff

## smolotchi/reports/diff.py
- function: `find_previous_host_summary`
  - Docstring: Not present
  - Code: smolotchi/reports/diff.py:find_previous_host_summary
- function: `resolve_baseline_host_summary`
  - Docstring: Not present
  - Code: smolotchi/reports/diff.py:resolve_baseline_host_summary
- function: `_ports_union`
  - Docstring: Not present
  - Code: smolotchi/reports/diff.py:_ports_union
- function: `_sev_highest`
  - Docstring: Not present
  - Code: smolotchi/reports/diff.py:_sev_highest
- function: `diff_host_summaries`
  - Docstring: Not present
  - Code: smolotchi/reports/diff.py:diff_host_summaries

## smolotchi/reports/diff_export.py
- function: `_ts`
  - Docstring: Not present
  - Code: smolotchi/reports/diff_export.py:_ts
- function: `diff_markdown`
  - Docstring: Not present
  - Code: smolotchi/reports/diff_export.py:diff_markdown
- function: `diff_html`
  - Docstring: Not present
  - Code: smolotchi/reports/diff_export.py:diff_html
- function: `diff_json`
  - Docstring: Not present
  - Code: smolotchi/reports/diff_export.py:diff_json

## smolotchi/reports/diff_links.py
- function: `index_host_actions`
  - Docstring: Returns: host -> action_id -> [artifact_id, ...]
Uses host_summary["artifacts"] list and action_run payload.target.
  - Code: smolotchi/reports/diff_links.py:index_host_actions

## smolotchi/reports/exec_summary.py
- function: `_now_utc`
  - Docstring: Not present
  - Code: smolotchi/reports/exec_summary.py:_now_utc
- function: `build_exec_summary`
  - Docstring: Not present
  - Code: smolotchi/reports/exec_summary.py:build_exec_summary
- function: `render_exec_summary_md`
  - Docstring: Not present
  - Code: smolotchi/reports/exec_summary.py:render_exec_summary_md
- function: `render_exec_summary_html`
  - Docstring: Not present
  - Code: smolotchi/reports/exec_summary.py:render_exec_summary_html

## smolotchi/reports/export.py
- function: `_ts_human`
  - Docstring: Not present
  - Code: smolotchi/reports/export.py:_ts_human
- function: `build_report_json`
  - Docstring: Not present
  - Code: smolotchi/reports/export.py:build_report_json
- function: `build_report_markdown`
  - Docstring: Not present
  - Code: smolotchi/reports/export.py:build_report_markdown

## smolotchi/reports/filtering.py
- function: `apply_policy_suppression`
  - Docstring: Marks findings as suppressed_by_policy instead of removing them.
Policy sources:
  cfg.lan.noisy_scripts: list[str]
  cfg.lan.allowlist_scripts: list[str]
  cfg.lan.suppress: dict (optional future)
  - Code: smolotchi/reports/filtering.py:apply_policy_suppression
- function: `filter_findings_scripts`
  - Docstring: Not present
  - Code: smolotchi/reports/filtering.py:filter_findings_scripts

## smolotchi/reports/findings_aggregate.py
- function: `extract_findings_for_host_from_action_run`
  - Docstring: Not present
  - Code: smolotchi/reports/findings_aggregate.py:extract_findings_for_host_from_action_run
- function: `build_host_findings`
  - Docstring: Returns: { host: { ports:[...], scripts:[...], sources:[{action_id,artifact_id}] } }
  - Code: smolotchi/reports/findings_aggregate.py:build_host_findings
- function: `summarize_findings`
  - Docstring: Returns per-host finding entries with minimal fields for timelines/baseline.
  - Code: smolotchi/reports/findings_aggregate.py:summarize_findings

## smolotchi/reports/host_diff.py
- function: `_ts`
  - Docstring: Not present
  - Code: smolotchi/reports/host_diff.py:_ts
- function: `host_diff_markdown`
  - Docstring: Not present
  - Code: smolotchi/reports/host_diff.py:host_diff_markdown
- function: `host_diff_html`
  - Docstring: Not present
  - Code: smolotchi/reports/host_diff.py:host_diff_html

## smolotchi/reports/nmap_classify.py
- function: `classify_scripts`
  - Docstring: Not present
  - Code: smolotchi/reports/nmap_classify.py:classify_scripts

## smolotchi/reports/nmap_findings.py
- function: `_summarize_output`
  - Docstring: Keep it safe & compact: strip and keep only a short snippet.
  - Code: smolotchi/reports/nmap_findings.py:_summarize_output
- function: `parse_nmap_xml_findings`
  - Docstring: Safe extraction:
  - open_ports with service product/version
  - script outputs (id, output snippet)
Returns:
  { hosts: {ip: { ports:[...], scripts:[...] } } }
  - Code: smolotchi/reports/nmap_findings.py:parse_nmap_xml_findings

## smolotchi/reports/normalize.py
- function: `apply_normalization`
  - Docstring: Not present
  - Code: smolotchi/reports/normalize.py:apply_normalization

## smolotchi/reports/severity.py
- function: `infer_severity`
  - Docstring: Returns: (severity, cvss, reason)
  severity: info|low|medium|high|critical
  - Code: smolotchi/reports/severity.py:infer_severity

## smolotchi/reports/top_findings.py
- function: `aggregate_top_findings`
  - Docstring: Returns:
  { id, title, severity, hosts, count, suppressed_count, suppressed_hosts }
  - Code: smolotchi/reports/top_findings.py:aggregate_top_findings

## smolotchi/reports/wifi_session_report.py
- function: `wifi_session_html`
  - Docstring: Not present
  - Code: smolotchi/reports/wifi_session_report.py:wifi_session_html

## HTTP Routes (Flask)
| Method | Path | Handler | Code Reference |
| --- | --- | --- | --- |

## CLI Commands (functions)
| Function | Code Reference |
| --- | --- |
| `cmd_ai_replay` | `smolotchi/cli.py:cmd_ai_replay` |
| `cmd_ai_replay_batch` | `smolotchi/cli.py:cmd_ai_replay_batch` |
| `cmd_baseline_diff` | `smolotchi/cli.py:cmd_baseline_diff` |
| `cmd_baseline_show` | `smolotchi/cli.py:cmd_baseline_show` |
| `cmd_core` | `smolotchi/cli.py:cmd_core` |
| `cmd_diff_baseline_set` | `smolotchi/cli.py:cmd_diff_baseline_set` |
| `cmd_diff_baseline_show` | `smolotchi/cli.py:cmd_diff_baseline_show` |
| `cmd_display` | `smolotchi/cli.py:cmd_display` |
| `cmd_dossier_build` | `smolotchi/cli.py:cmd_dossier_build` |
| `cmd_events` | `smolotchi/cli.py:cmd_events` |
| `cmd_finding_history` | `smolotchi/cli.py:cmd_finding_history` |
| `cmd_handoff` | `smolotchi/cli.py:cmd_handoff` |
| `cmd_health` | `smolotchi/cli.py:cmd_health` |
| `cmd_install_systemd` | `smolotchi/cli.py:cmd_install_systemd` |
| `cmd_job_cancel` | `smolotchi/cli.py:cmd_job_cancel` |
| `cmd_job_delete` | `smolotchi/cli.py:cmd_job_delete` |
| `cmd_job_reset` | `smolotchi/cli.py:cmd_job_reset` |
| `cmd_jobs_enqueue` | `smolotchi/cli.py:cmd_jobs_enqueue` |
| `cmd_jobs_get` | `smolotchi/cli.py:cmd_jobs_get` |
| `cmd_jobs_list` | `smolotchi/cli.py:cmd_jobs_list` |
| `cmd_jobs_tail` | `smolotchi/cli.py:cmd_jobs_tail` |
| `cmd_lan_done` | `smolotchi/cli.py:cmd_lan_done` |
| `cmd_profile_timeline` | `smolotchi/cli.py:cmd_profile_timeline` |
| `cmd_prune` | `smolotchi/cli.py:cmd_prune` |
| `cmd_stages_approve` | `smolotchi/cli.py:cmd_stages_approve` |
| `cmd_stages_list` | `smolotchi/cli.py:cmd_stages_list` |
| `cmd_status` | `smolotchi/cli.py:cmd_status` |
| `cmd_web` | `smolotchi/cli.py:cmd_web` |
| `cmd_wifi_connect` | `smolotchi/cli.py:cmd_wifi_connect` |
| `cmd_wifi_scan` | `smolotchi/cli.py:cmd_wifi_scan` |
| `cmd_wifi_status` | `smolotchi/cli.py:cmd_wifi_status` |
