# Docstring Quality (Structural)

Checks are structural only. Docstring content is not evaluated. Sections are detected via simple keyword matching.

## Summary

- Docstrings evaluated: 72
- Multi-line docstrings: 42
- With params section: 0
- With returns section: 7
- With raises section: 0

## Details

| File | Symbol | Type | Multiline | Params | Returns | Raises | Missing Sections |
|------|--------|------|-----------|--------|---------|--------|------------------|
| smolotchi/actions/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/actions/cache.py | find_fresh_discovery | function | yes | no | no | no | params, returns |
| smolotchi/actions/cache.py | find_fresh_portscan_for_host | function | yes | no | no | no | params, returns |
| smolotchi/actions/cache.py | find_fresh_vuln_for_host_action | function | yes | no | no | no | params, returns |
| smolotchi/actions/fingerprint.py | service_fingerprint | function | yes | no | no | no | none |
| smolotchi/actions/fingerprint.py | service_fingerprint_by_key | function | yes | no | no | no | none |
| smolotchi/actions/parse.py | parse_nmap_xml_up_hosts | function | no | no | no | no | none |
| smolotchi/actions/parse_services.py | parse_nmap_xml_services | function | yes | no | yes | no | none |
| smolotchi/actions/parse_services.py | summarize_service_keys | function | no | no | no | no | none |
| smolotchi/actions/plan_runner.py | PlanRunner | class | yes | no | no | no | none |
| smolotchi/actions/plan_runner.py | PlanRunner._extract_links | method | yes | no | no | no | none |
| smolotchi/actions/plan_runner.py | PlanRunner._summarize_result | method | no | no | no | no | none |
| smolotchi/actions/plan_runner.py | PlanRunner.run | method | yes | no | no | no | params |
| smolotchi/actions/planners/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/actions/planners/ai_planner.py | AIPlanner | class | yes | no | no | no | none |
| smolotchi/ai/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/ai/errors.py | StageRequired | class | no | no | no | no | none |
| smolotchi/ai/worker.py | AIWorker | class | yes | no | no | no | none |
| smolotchi/api/web.py | _bundle_finding_state | function | yes | no | yes | no | none |
| smolotchi/cli.py | cmd_core | function | yes | no | no | no | none |
| smolotchi/cli.py | cmd_install_systemd | function | no | no | no | no | none |
| smolotchi/core/artifacts.py | ArtifactStore.find_bundle_by_job_id | method | no | no | no | no | none |
| smolotchi/core/artifacts.py | ArtifactStore.find_dossier_by_job_id | method | no | no | no | no | none |
| smolotchi/core/artifacts.py | ArtifactStore.find_latest_pending_stage_request | method | no | no | no | no | none |
| smolotchi/core/artifacts.py | ArtifactStore.prune | method | yes | no | no | no | params, returns |
| smolotchi/core/artifacts_gc.py | _extract_ref_ids_from_bundle | function | no | no | no | no | none |
| smolotchi/core/artifacts_gc.py | apply_gc | function | yes | no | no | no | params, returns |
| smolotchi/core/artifacts_gc.py | plan_gc | function | yes | no | no | no | params, returns |
| smolotchi/core/bus.py | SQLiteBus | class | yes | no | no | no | none |
| smolotchi/core/bus.py | SQLiteBus.prune | method | yes | no | no | no | params, returns |
| smolotchi/core/config.py | ConfigStore | class | no | no | no | no | none |
| smolotchi/core/dossier.py | build_lan_dossier | function | yes | no | no | no | params, returns, raises |
| smolotchi/core/jobs.py | JobStore.cancel | method | no | no | no | no | none |
| smolotchi/core/jobs.py | JobStore.fail | method | no | no | no | no | none |
| smolotchi/core/jobs.py | JobStore.prune | method | yes | no | no | no | none |
| smolotchi/core/jobs.py | JobStore.reset_running | method | no | no | no | no | none |
| smolotchi/core/lan_resolver.py | resolve_result_by_job_id | function | yes | no | no | no | none |
| smolotchi/core/normalize.py | normalize_profile | function | no | no | no | no | none |
| smolotchi/core/policy.py | Policy | class | yes | no | no | no | none |
| smolotchi/core/policy.py | evaluate_tool_action | function | no | no | no | no | params, returns |
| smolotchi/core/resources.py | ResourceManager | class | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | _parse_baseline_scopes_block | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | _render_baseline_scopes_block | function | no | no | no | no | none |
| smolotchi/core/toml_patch.py | cleanup_baseline_profiles | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | cleanup_baseline_scopes | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | parse_wifi_credentials_text | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | parse_wifi_profiles_text | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | patch_wifi_credentials | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | patch_wifi_profile_upsert | function | yes | no | no | no | none |
| smolotchi/core/toml_patch.py | patch_wifi_profiles_set | function | yes | no | no | no | none |
| smolotchi/device/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/display/waveshare_driver.py | EPDDriver | class | no | no | no | no | none |
| smolotchi/engines/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/engines/net_detect.py | cidr_to_network_scope | function | yes | no | no | no | none |
| smolotchi/engines/net_detect.py | detect_ipv4_cidr | function | yes | no | no | no | none |
| smolotchi/engines/wifi_connect.py | connect_wpa_psk | function | yes | no | no | no | params, returns |
| smolotchi/engines/wifi_scan.py | scan_iw | function | yes | no | no | no | none |
| smolotchi/merge/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/merge/sources.py | find_wifi_context_for_job | function | no | no | no | no | params, returns |
| smolotchi/merge/sources.py | list_host_summaries_for_job | function | yes | no | no | no | params, returns |
| smolotchi/merge/sources.py | list_policy_events_for_job | function | yes | no | no | no | none |
| smolotchi/parsers/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/parsers/base.py | BaseParser.parse | method | no | no | no | no | none |
| smolotchi/reports/__init__.py | <module> | module | no | no | no | no | none |
| smolotchi/reports/diff_links.py | index_host_actions | function | yes | no | yes | no | params |
| smolotchi/reports/filtering.py | apply_policy_suppression | function | yes | no | no | no | params, returns |
| smolotchi/reports/findings_aggregate.py | build_host_findings | function | no | no | yes | no | params |
| smolotchi/reports/findings_aggregate.py | summarize_findings | function | no | no | no | no | params, returns |
| smolotchi/reports/nmap_findings.py | _summarize_output | function | no | no | no | no | none |
| smolotchi/reports/nmap_findings.py | parse_nmap_xml_findings | function | yes | no | yes | no | params |
| smolotchi/reports/severity.py | infer_severity | function | yes | no | yes | no | none |
| smolotchi/reports/top_findings.py | aggregate_top_findings | function | yes | no | yes | no | params |