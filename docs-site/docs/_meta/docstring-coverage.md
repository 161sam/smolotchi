# Docstring Coverage

**Global Coverage:** 72/766 symbols (9.40%)

## Coverage by Module Group

- smolotchi: 2/59 (3.39%)
- smolotchi.actions: 15/98 (15.31%)
- smolotchi.ai: 3/36 (8.33%)
- smolotchi.api: 1/118 (0.85%)
- smolotchi.core: 29/235 (12.34%)
- smolotchi.device: 1/20 (5.00%)
- smolotchi.display: 1/22 (4.55%)
- smolotchi.engines: 5/68 (7.35%)
- smolotchi.merge: 4/11 (36.36%)
- smolotchi.parsers: 2/18 (11.11%)
- smolotchi.reports: 9/81 (11.11%)

## Coverage by File

- smolotchi/__init__.py: 0/1 (0.00%)
- smolotchi/__main__.py: 0/1 (0.00%)
- smolotchi/actions/__init__.py: 1/1 (100.00%)
- smolotchi/actions/cache.py: 3/7 (42.86%)
- smolotchi/actions/execution.py: 0/3 (0.00%)
- smolotchi/actions/fingerprint.py: 2/4 (50.00%)
- smolotchi/actions/parse.py: 1/2 (50.00%)
- smolotchi/actions/parse_services.py: 2/3 (66.67%)
- smolotchi/actions/plan_runner.py: 4/30 (13.33%)
- smolotchi/actions/planners/__init__.py: 1/1 (100.00%)
- smolotchi/actions/planners/ai_planner.py: 1/11 (9.09%)
- smolotchi/actions/registry.py: 0/18 (0.00%)
- smolotchi/actions/runner.py: 0/4 (0.00%)
- smolotchi/actions/schema.py: 0/2 (0.00%)
- smolotchi/actions/summary.py: 0/2 (0.00%)
- smolotchi/actions/test_plan_runner.py: 0/5 (0.00%)
- smolotchi/actions/throttle.py: 0/5 (0.00%)
- smolotchi/ai/__init__.py: 1/1 (100.00%)
- smolotchi/ai/errors.py: 1/2 (50.00%)
- smolotchi/ai/replay.py: 0/6 (0.00%)
- smolotchi/ai/test_worker.py: 0/4 (0.00%)
- smolotchi/ai/worker.py: 1/23 (4.35%)
- smolotchi/api/__init__.py: 0/1 (0.00%)
- smolotchi/api/conftest.py: 0/2 (0.00%)
- smolotchi/api/health.py: 0/3 (0.00%)
- smolotchi/api/test_templates_smoke.py: 0/2 (0.00%)
- smolotchi/api/test_web_wifi_smoke.py: 0/4 (0.00%)
- smolotchi/api/theme.py: 0/3 (0.00%)
- smolotchi/api/view_models.py: 0/2 (0.00%)
- smolotchi/api/web.py: 1/101 (0.99%)
- smolotchi/cli.py: 2/43 (4.65%)
- smolotchi/cli_artifacts.py: 0/8 (0.00%)
- smolotchi/cli_profiles.py: 0/6 (0.00%)
- smolotchi/core/__init__.py: 0/1 (0.00%)
- smolotchi/core/app_state.py: 0/5 (0.00%)
- smolotchi/core/artifacts.py: 4/28 (14.29%)
- smolotchi/core/artifacts_gc.py: 3/7 (42.86%)
- smolotchi/core/bus.py: 2/10 (20.00%)
- smolotchi/core/config.py: 1/27 (3.70%)
- smolotchi/core/dossier.py: 1/2 (50.00%)
- smolotchi/core/engines.py: 0/13 (0.00%)
- smolotchi/core/jobs.py: 4/28 (14.29%)
- smolotchi/core/lan_resolver.py: 1/2 (50.00%)
- smolotchi/core/lan_state.py: 0/2 (0.00%)
- smolotchi/core/normalize.py: 1/3 (33.33%)
- smolotchi/core/paths.py: 0/8 (0.00%)
- smolotchi/core/policy.py: 2/8 (25.00%)
- smolotchi/core/presets.py: 0/1 (0.00%)
- smolotchi/core/reports.py: 0/5 (0.00%)
- smolotchi/core/resources.py: 1/12 (8.33%)
- smolotchi/core/self_heal.py: 0/5 (0.00%)
- smolotchi/core/state.py: 0/11 (0.00%)
- smolotchi/core/test_artifact_sanity.py: 0/2 (0.00%)
- smolotchi/core/test_artifacts_stage_helpers.py: 0/3 (0.00%)
- smolotchi/core/test_dossier_builder.py: 0/2 (0.00%)
- smolotchi/core/test_policy_tools.py: 0/4 (0.00%)
- smolotchi/core/toml_patch.py: 9/32 (28.12%)
- smolotchi/core/validate.py: 0/2 (0.00%)
- smolotchi/core/watchdog.py: 0/12 (0.00%)
- smolotchi/device/__init__.py: 1/1 (100.00%)
- smolotchi/device/buttons.py: 0/10 (0.00%)
- smolotchi/device/power.py: 0/6 (0.00%)
- smolotchi/device/profile.py: 0/3 (0.00%)
- smolotchi/display/__init__.py: 0/1 (0.00%)
- smolotchi/display/displayd.py: 0/10 (0.00%)
- smolotchi/display/render.py: 0/2 (0.00%)
- smolotchi/display/test_display_render.py: 0/2 (0.00%)
- smolotchi/display/waveshare_driver.py: 1/7 (14.29%)
- smolotchi/engines/__init__.py: 1/1 (100.00%)
- smolotchi/engines/lan_engine.py: 0/12 (0.00%)
- smolotchi/engines/net_detect.py: 2/5 (40.00%)
- smolotchi/engines/net_health.py: 0/6 (0.00%)
- smolotchi/engines/test_wifi_artifacts.py: 0/7 (0.00%)
- smolotchi/engines/tools_engine.py: 0/16 (0.00%)
- smolotchi/engines/wifi_connect.py: 1/4 (25.00%)
- smolotchi/engines/wifi_engine.py: 0/11 (0.00%)
- smolotchi/engines/wifi_scan.py: 1/4 (25.00%)
- smolotchi/engines/wifi_targets.py: 0/2 (0.00%)
- smolotchi/merge/__init__.py: 1/1 (100.00%)
- smolotchi/merge/sources.py: 3/6 (50.00%)
- smolotchi/merge/timeline.py: 0/4 (0.00%)
- smolotchi/parsers/__init__.py: 1/1 (100.00%)
- smolotchi/parsers/base.py: 1/4 (25.00%)
- smolotchi/parsers/bettercap.py: 0/3 (0.00%)
- smolotchi/parsers/masscan.py: 0/3 (0.00%)
- smolotchi/parsers/merge.py: 0/2 (0.00%)
- smolotchi/parsers/nmap.py: 0/3 (0.00%)
- smolotchi/parsers/registry.py: 0/2 (0.00%)
- smolotchi/reports/__init__.py: 1/1 (100.00%)
- smolotchi/reports/aggregate.py: 0/6 (0.00%)
- smolotchi/reports/badges.py: 0/4 (0.00%)
- smolotchi/reports/baseline.py: 0/8 (0.00%)
- smolotchi/reports/baseline_diff.py: 0/5 (0.00%)
- smolotchi/reports/diff.py: 0/7 (0.00%)
- smolotchi/reports/diff_export.py: 0/5 (0.00%)
- smolotchi/reports/diff_links.py: 1/2 (50.00%)
- smolotchi/reports/exec_summary.py: 0/5 (0.00%)
- smolotchi/reports/export.py: 0/4 (0.00%)
- smolotchi/reports/filtering.py: 1/3 (33.33%)
- smolotchi/reports/findings_aggregate.py: 2/4 (50.00%)
- smolotchi/reports/host_diff.py: 0/13 (0.00%)
- smolotchi/reports/nmap_classify.py: 0/2 (0.00%)
- smolotchi/reports/nmap_findings.py: 2/3 (66.67%)
- smolotchi/reports/normalize.py: 0/2 (0.00%)
- smolotchi/reports/severity.py: 1/2 (50.00%)
- smolotchi/reports/top_findings.py: 1/2 (50.00%)
- smolotchi/reports/wifi_session_report.py: 0/3 (0.00%)

## smolotchi/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |

## smolotchi/__main__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |

## smolotchi/actions/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/actions/cache.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| find_fresh_discovery | function | ✅ | present |
| find_fresh_portscan_for_host | function | ✅ | present |
| find_fresh_vuln_for_host_action | function | ✅ | present |
| put_service_fingerprint | function | ❌ | missing |
| _ports_by_key | function | ❌ | missing |
| find_latest_fingerprint | function | ❌ | missing |

## smolotchi/actions/execution.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ActionResult | class | ❌ | missing |
| run_action_spec | function | ❌ | missing |

## smolotchi/actions/fingerprint.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| service_fingerprint | function | ✅ | present |
| service_fingerprint_by_key | function | ✅ | present |
| _filter | function | ❌ | missing |

## smolotchi/actions/parse.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| parse_nmap_xml_up_hosts | function | ✅ | present |

## smolotchi/actions/parse_services.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| parse_nmap_xml_services | function | ✅ | present |
| summarize_service_keys | function | ✅ | present |

## smolotchi/actions/plan_runner.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| PlanRunner | class | ✅ | present |
| PlanRunner.__init__ | method | ❌ | missing |
| PlanRunner.run | method | ✅ | present |
| PlanRunner._run_step | method | ❌ | missing |
| PlanRunner._run_with_runner | method | ❌ | missing |
| PlanRunner._risk_allowed | method | ❌ | missing |
| PlanRunner._approved_request_ids | method | ❌ | missing |
| PlanRunner._find_stage_request | method | ❌ | missing |
| PlanRunner._stage_approved | method | ❌ | missing |
| PlanRunner._ensure_stage_request | method | ❌ | missing |
| PlanRunner._extract_req_id | method | ❌ | missing |
| PlanRunner._job_cancelled | method | ❌ | missing |
| PlanRunner._emit_done | method | ❌ | missing |
| PlanRunner._emit_cancel | method | ❌ | missing |
| PlanRunner._emit_blocked | method | ❌ | missing |
| PlanRunner._emit_failed | method | ❌ | missing |
| PlanRunner._summarize_result | method | ✅ | present |
| PlanRunner._extract_links | method | ✅ | present |
| PlanRunner.add | method | ❌ | missing |
| PlanRunner._record_job_link | method | ❌ | missing |
| BatchPlanRunner | class | ❌ | missing |
| BatchPlanRunner.__init__ | method | ❌ | missing |
| BatchPlanRunner._links_from_artifact_id | method | ❌ | missing |
| BatchPlanRunner._ensure_job_link | method | ❌ | missing |
| BatchPlanRunner._build_batched_steps | method | ❌ | missing |
| BatchPlanRunner.run | method | ❌ | missing |
| BatchPlanRunner.diff_ports | method | ❌ | missing |
| BatchPlanRunner.vuln_ttl_for_key | method | ❌ | missing |
| ThrottleCfg | class | ❌ | missing |

## smolotchi/actions/planners/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/actions/planners/ai_planner.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| PlanCandidate | class | ❌ | missing |
| PlanStep | class | ❌ | missing |
| ActionPlan | class | ❌ | missing |
| AIPlanner | class | ✅ | present |
| AIPlanner.__init__ | method | ❌ | missing |
| AIPlanner.generate | method | ❌ | missing |
| AIPlanner._generate_candidates | method | ❌ | missing |
| AIPlanner._candidate | method | ❌ | missing |
| AIPlanner._norm_cost | method | ❌ | missing |
| AIPlanner._risk_penalty | method | ❌ | missing |

## smolotchi/actions/registry.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| UnknownAction | class | ❌ | missing |
| ActionImpl | class | ❌ | missing |
| ActionRegistry | class | ❌ | missing |
| ActionRegistry.__init__ | method | ❌ | missing |
| ActionRegistry.register | method | ❌ | missing |
| ActionRegistry.register_spec | method | ❌ | missing |
| ActionRegistry.register_impl | method | ❌ | missing |
| ActionRegistry.get | method | ❌ | missing |
| ActionRegistry.get_spec | method | ❌ | missing |
| ActionRegistry.get_impl | method | ❌ | missing |
| ActionRegistry.all | method | ❌ | missing |
| ActionRegistry.by_category | method | ❌ | missing |
| ActionRegistry.dump | method | ❌ | missing |
| ActionRegistry._default_impl | method | ❌ | missing |
| ActionRegistry._run | method | ❌ | missing |
| _spec_from_dict | function | ❌ | missing |
| load_pack | function | ❌ | missing |

## smolotchi/actions/runner.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ActionRunner | class | ❌ | missing |
| ActionRunner.__init__ | method | ❌ | missing |
| ActionRunner.execute | method | ❌ | missing |

## smolotchi/actions/schema.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ActionSpec | class | ❌ | missing |

## smolotchi/actions/summary.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| build_host_summary | function | ❌ | missing |

## smolotchi/actions/test_plan_runner.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| PlanRunnerPolicyGateTest | class | ❌ | missing |
| PlanRunnerPolicyGateTest.test_policy_block_creates_stage_request | method | ❌ | missing |
| _Step | class | ❌ | missing |
| _Plan | class | ❌ | missing |

## smolotchi/actions/throttle.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ThrottleDecision | class | ❌ | missing |
| read_loadavg_1m | function | ❌ | missing |
| read_cpu_temp_c | function | ❌ | missing |
| decide_multiplier | function | ❌ | missing |

## smolotchi/ai/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/ai/errors.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| StageRequired | class | ✅ | present |

## smolotchi/ai/replay.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ReplayMetrics | class | ❌ | missing |
| _collect_links | function | ❌ | missing |
| baseline_delta_from_bundles | function | ❌ | missing |
| evaluate_plan_run | function | ❌ | missing |
| metrics_row | function | ❌ | missing |

## smolotchi/ai/test_worker.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| WorkerResumeTest | class | ❌ | missing |
| WorkerResumeTest.test_stage_resume_executes_blocked_step_once | method | ❌ | missing |
| WorkerResumeTest._run_action | method | ❌ | missing |

## smolotchi/ai/worker.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| WorkerState | class | ❌ | missing |
| AIWorker | class | ✅ | present |
| AIWorker.__init__ | method | ❌ | missing |
| AIWorker._extract_req_id | method | ❌ | missing |
| AIWorker._parse_resume_from | method | ❌ | missing |
| AIWorker._strip_resume_from | method | ❌ | missing |
| AIWorker._extract_stage_req | method | ❌ | missing |
| AIWorker.start | method | ❌ | missing |
| AIWorker.stop | method | ❌ | missing |
| AIWorker._loop | method | ❌ | missing |
| AIWorker.run_once | method | ❌ | missing |
| AIWorker._tick | method | ❌ | missing |
| AIWorker._approved_stage_request_ids | method | ❌ | missing |
| AIWorker._approved_stage_request_for_job | method | ❌ | missing |
| AIWorker._process_job | method | ❌ | missing |
| AIWorker._run_plan_artifact | method | ❌ | missing |
| _Plan | class | ❌ | missing |
| _Step | class | ❌ | missing |
| AIWorker._run_plan_object | method | ❌ | missing |
| _build_policy | function | ❌ | missing |
| _build_registry | function | ❌ | missing |
| main | function | ❌ | missing |

## smolotchi/api/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |

## smolotchi/api/conftest.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| client | function | ❌ | missing |

## smolotchi/api/health.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| core_health_ok | function | ❌ | missing |
| worker_health_ok | function | ❌ | missing |

## smolotchi/api/test_templates_smoke.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_templates_smoke | function | ❌ | missing |

## smolotchi/api/test_web_wifi_smoke.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_wifi_page_renders | function | ❌ | missing |
| test_wifi_lan_timeline_shows_done_when_jobstore_done | function | ❌ | missing |
| test_resolve_result_by_job_id_prefers_lan_job_result | function | ❌ | missing |

## smolotchi/api/theme.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| load_theme_tokens | function | ❌ | missing |
| tokens_to_css_vars | function | ❌ | missing |

## smolotchi/api/view_models.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| effective_lan_overrides | function | ❌ | missing |

## smolotchi/api/web.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| pretty | function | ❌ | missing |
| _atomic_write_text | function | ❌ | missing |
| create_app | function | ❌ | missing |
| nav_active | function | ❌ | missing |
| fmt_ts | function | ❌ | missing |
| core_recently_active | function | ❌ | missing |
| _build_policy | function | ❌ | missing |
| _safe_store_path | function | ❌ | missing |
| _record_wifi_config_patch | function | ❌ | missing |
| _artifact_rows | function | ❌ | missing |
| inject_globals | function | ❌ | missing |
| dashboard | function | ❌ | missing |
| wifi | function | ❌ | missing |
| _job_status | function | ❌ | missing |
| _job_links | function | ❌ | missing |
| wifi_connect | function | ❌ | missing |
| wifi_disconnect | function | ❌ | missing |
| wifi_profile_apply | function | ❌ | missing |
| wifi_profile_create | function | ❌ | missing |
| wifi_profile_preset | function | ❌ | missing |
| wifi_credentials_save | function | ❌ | missing |
| wifi_credentials_save_reload | function | ❌ | missing |
| wifi_profiles_save | function | ❌ | missing |
| wifi_profiles_save_reload | function | ❌ | missing |
| wifi_allowlist_add | function | ❌ | missing |
| wifi_allowlist_remove | function | ❌ | missing |
| wifi_scope_map_set | function | ❌ | missing |
| wifi_scope_map_remove | function | ❌ | missing |
| lan | function | ❌ | missing |
| lan_dossiers | function | ❌ | missing |
| _key | function | ❌ | missing |
| lan_dossier_view | function | ❌ | missing |
| _bundle_finding_state | function | ✅ | present |
| _bundle_ts | function | ❌ | missing |
| _fmt_ts | function | ❌ | missing |
| list_lan_dossiers | function | ❌ | missing |
| _load_profile_timeline | function | ❌ | missing |
| _expected_findings_for_bundles | function | ❌ | missing |
| lan_results | function | ❌ | missing |
| _bundle_has_finding | function | ❌ | missing |
| _find_latest_bundle_for_finding | function | ❌ | missing |
| _load_recent_bundles | function | ❌ | missing |
| _pick_scope | function | ❌ | missing |
| _baseline_scopes | function | ❌ | missing |
| _profile_key_for_bundle | function | ❌ | missing |
| _baseline_profiles | function | ❌ | missing |
| _pick_profile | function | ❌ | missing |
| lan_baseline_overview | function | ❌ | missing |
| lan_baseline_diff_latest | function | ❌ | missing |
| lan_baseline_add | function | ❌ | missing |
| lan_baseline_remove | function | ❌ | missing |
| lan_baseline_cleanup | function | ❌ | missing |
| lan_finding_jump | function | ❌ | missing |
| lan_exec_summary | function | ❌ | missing |
| lan_exec_summary_md | function | ❌ | missing |
| lan_exec_summary_json | function | ❌ | missing |
| resolve_result_by_job_id | function | ❌ | missing |
| lan_result_details | function | ❌ | missing |
| lan_result_by_job | function | ❌ | missing |
| lan_finding_timeline | function | ❌ | missing |
| _render_result_details | function | ❌ | missing |
| lan_reports | function | ❌ | missing |
| _resolve_bundle | function | ❌ | missing |
| lan_host_diff | function | ❌ | missing |
| lan_host_diff_md | function | ❌ | missing |
| artifact_view | function | ❌ | missing |
| artifact_download | function | ❌ | missing |
| artifact_file_download | function | ❌ | missing |
| report_view | function | ❌ | missing |
| lan_jobs | function | ❌ | missing |
| _enrich_jobs | function | ❌ | missing |
| lan_job_cancel | function | ❌ | missing |
| lan_job_reset | function | ❌ | missing |
| lan_job_delete | function | ❌ | missing |
| lan_job_json | function | ❌ | missing |
| lan_policy | function | ❌ | missing |
| lan_policy_save | function | ❌ | missing |
| lan_policy_save_reload | function | ❌ | missing |
| config | function | ❌ | missing |
| config_save | function | ❌ | missing |
| config_save_reload | function | ❌ | missing |
| config_reload | function | ❌ | missing |
| audit | function | ❌ | missing |
| handoff | function | ❌ | missing |
| lan_done | function | ❌ | missing |
| lan_enqueue | function | ❌ | missing |
| dossier_build | function | ❌ | missing |
| ai_plans | function | ❌ | missing |
| ai_plan_detail | function | ❌ | missing |
| ai_run_detail | function | ❌ | missing |
| normalize_links | function | ❌ | missing |
| ai_plan | function | ❌ | missing |
| ai_run | function | ❌ | missing |
| ai_jobs | function | ❌ | missing |
| ai_stages | function | ❌ | missing |
| ai_stage_new | function | ❌ | missing |
| ai_stage_new_post | function | ❌ | missing |
| ai_stage_approve | function | ❌ | missing |
| ai_job_cancel | function | ❌ | missing |
| ai_progress | function | ❌ | missing |

## smolotchi/cli.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _format_ts | function | ❌ | missing |
| _print_json | function | ❌ | missing |
| _print_table | function | ❌ | missing |
| cmd_web | function | ❌ | missing |
| cmd_display | function | ❌ | missing |
| cmd_core | function | ✅ | present |
| cmd_status | function | ❌ | missing |
| cmd_events | function | ❌ | missing |
| cmd_wifi_scan | function | ❌ | missing |
| cmd_wifi_connect | function | ❌ | missing |
| cmd_wifi_status | function | ❌ | missing |
| cmd_jobs_enqueue | function | ❌ | missing |
| cmd_jobs_list | function | ❌ | missing |
| cmd_jobs_get | function | ❌ | missing |
| cmd_jobs_tail | function | ❌ | missing |
| _stage_approval_index | function | ❌ | missing |
| cmd_stages_list | function | ❌ | missing |
| cmd_stages_approve | function | ❌ | missing |
| cmd_health | function | ❌ | missing |
| cmd_job_cancel | function | ❌ | missing |
| cmd_job_reset | function | ❌ | missing |
| cmd_job_delete | function | ❌ | missing |
| cmd_prune | function | ❌ | missing |
| cmd_handoff | function | ❌ | missing |
| cmd_lan_done | function | ❌ | missing |
| cmd_diff_baseline_set | function | ❌ | missing |
| cmd_diff_baseline_show | function | ❌ | missing |
| _resolve_profile_key | function | ❌ | missing |
| cmd_profile_timeline | function | ❌ | missing |
| cmd_baseline_show | function | ❌ | missing |
| cmd_baseline_diff | function | ❌ | missing |
| cmd_finding_history | function | ❌ | missing |
| cmd_dossier_build | function | ❌ | missing |
| _write_text | function | ❌ | missing |
| _write_json | function | ❌ | missing |
| cmd_ai_replay | function | ❌ | missing |
| cmd_ai_replay_batch | function | ❌ | missing |
| _write_unit | function | ❌ | missing |
| cmd_install_systemd | function | ✅ | present |
| add_ai_subcommands | function | ❌ | missing |
| build_parser | function | ❌ | missing |
| main | function | ❌ | missing |

## smolotchi/cli_artifacts.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _format_ts | function | ❌ | missing |
| _print_json | function | ❌ | missing |
| _print_table | function | ❌ | missing |
| add_artifacts_subcommands | function | ❌ | missing |
| _run | function | ❌ | missing |
| _run_find | function | ❌ | missing |
| _run_get | function | ❌ | missing |

## smolotchi/cli_profiles.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| add_profiles_subcommands | function | ❌ | missing |
| _load_profiles | function | ❌ | missing |
| _run_list | function | ❌ | missing |
| _run_show | function | ❌ | missing |
| _run_hash | function | ❌ | missing |

## smolotchi/core/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |

## smolotchi/core/app_state.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| AppState | class | ❌ | missing |
| state_path_for_artifacts | function | ❌ | missing |
| load_state | function | ❌ | missing |
| save_state | function | ❌ | missing |

## smolotchi/core/artifacts.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ArtifactMeta | class | ❌ | missing |
| ArtifactStore | class | ❌ | missing |
| ArtifactStore.__init__ | method | ❌ | missing |
| ArtifactStore._ensure_index | method | ❌ | missing |
| ArtifactStore._load_index | method | ❌ | missing |
| ArtifactStore._save_index | method | ❌ | missing |
| ArtifactStore.put_json | method | ❌ | missing |
| ArtifactStore.put_text | method | ❌ | missing |
| ArtifactStore.put_file | method | ❌ | missing |
| ArtifactStore.list | method | ❌ | missing |
| ArtifactStore.get_meta | method | ❌ | missing |
| ArtifactStore.get_json | method | ❌ | missing |
| ArtifactStore.find_bundle_by_job_id | method | ✅ | present |
| ArtifactStore.find_dossier_by_job_id | method | ✅ | present |
| ArtifactStore.find_latest | method | ❌ | missing |
| ArtifactStore.latest_meta | method | ❌ | missing |
| ArtifactStore.latest_json | method | ❌ | missing |
| ArtifactStore.count_kind | method | ❌ | missing |
| ArtifactStore.count_pending_stage_requests | method | ❌ | missing |
| ArtifactStore._inject_stage_request_id | method | ❌ | missing |
| ArtifactStore.find_latest_stage_request | method | ❌ | missing |
| ArtifactStore.find_latest_pending_stage_request | method | ✅ | present |
| ArtifactStore.find_latest_stage_approval_for_request | method | ❌ | missing |
| ArtifactStore.is_stage_request_pending | method | ❌ | missing |
| ArtifactStore.prune | method | ✅ | present |
| ArtifactStore._remove_meta | method | ❌ | missing |
| ArtifactStore.delete | method | ❌ | missing |

## smolotchi/core/artifacts_gc.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| GCPlan | class | ❌ | missing |
| _extract_ref_ids_from_bundle | function | ✅ | present |
| add | function | ❌ | missing |
| plan_gc | function | ✅ | present |
| _safe_unlink | function | ❌ | missing |
| apply_gc | function | ✅ | present |

## smolotchi/core/bus.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| Event | class | ❌ | missing |
| SQLiteBus | class | ✅ | present |
| SQLiteBus.__init__ | method | ❌ | missing |
| SQLiteBus._conn | method | ❌ | missing |
| SQLiteBus._init_db | method | ❌ | missing |
| SQLiteBus.db_path_value | method | ❌ | missing |
| SQLiteBus.publish | method | ❌ | missing |
| SQLiteBus.tail | method | ❌ | missing |
| SQLiteBus.prune | method | ✅ | present |

## smolotchi/core/config.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _load_toml | function | ❌ | missing |
| CoreCfg | class | ❌ | missing |
| PolicyCfg | class | ❌ | missing |
| WifiCfg | class | ❌ | missing |
| LanCfg | class | ❌ | missing |
| AiExecCfg | class | ❌ | missing |
| AiCacheCfg | class | ❌ | missing |
| AiThrottleCfg | class | ❌ | missing |
| AiCfg | class | ❌ | missing |
| UiCfg | class | ❌ | missing |
| ThemeCfg | class | ❌ | missing |
| RetentionCfg | class | ❌ | missing |
| WatchdogCfg | class | ❌ | missing |
| ReportsCfg | class | ❌ | missing |
| ReportFindingsCfg | class | ❌ | missing |
| ReportNormalizeCfg | class | ❌ | missing |
| ReportDiffCfg | class | ❌ | missing |
| InvalidationCfg | class | ❌ | missing |
| BaselineCfg | class | ❌ | missing |
| AppConfig | class | ❌ | missing |
| ConfigStore | class | ✅ | present |
| ConfigStore.__init__ | method | ❌ | missing |
| ConfigStore._from_dict | method | ❌ | missing |
| ConfigStore.load | method | ❌ | missing |
| ConfigStore.get | method | ❌ | missing |
| ConfigStore.reload | method | ❌ | missing |

## smolotchi/core/dossier.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| build_lan_dossier | function | ✅ | present |

## smolotchi/core/engines.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| EngineHealth | class | ❌ | missing |
| Engine | class | ❌ | missing |
| Engine.start | method | ❌ | missing |
| Engine.stop | method | ❌ | missing |
| Engine.tick | method | ❌ | missing |
| Engine.health | method | ❌ | missing |
| EngineRegistry | class | ❌ | missing |
| EngineRegistry.__init__ | method | ❌ | missing |
| EngineRegistry.register | method | ❌ | missing |
| EngineRegistry.all | method | ❌ | missing |
| EngineRegistry.get | method | ❌ | missing |
| EngineRegistry.health_all | method | ❌ | missing |

## smolotchi/core/jobs.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| JobRow | class | ❌ | missing |
| JobStore | class | ❌ | missing |
| JobStore.__init__ | method | ❌ | missing |
| JobStore._conn | method | ❌ | missing |
| JobStore._init_db | method | ❌ | missing |
| JobStore.enqueue | method | ❌ | missing |
| JobStore.get | method | ❌ | missing |
| JobStore.pop_next | method | ❌ | missing |
| JobStore.pop_next_filtered | method | ❌ | missing |
| JobStore.mark_running | method | ❌ | missing |
| JobStore.update_note | method | ❌ | missing |
| JobStore.mark_done | method | ❌ | missing |
| JobStore.mark_failed | method | ❌ | missing |
| JobStore.mark_blocked | method | ❌ | missing |
| JobStore.mark_cancelled | method | ❌ | missing |
| JobStore.mark_queued | method | ❌ | missing |
| JobStore.list | method | ❌ | missing |
| JobStore.list_recent | method | ❌ | missing |
| JobStore.list_stuck_running | method | ❌ | missing |
| JobStore._stuck_running_ids | method | ❌ | missing |
| JobStore.reset_stuck | method | ❌ | missing |
| JobStore.fail_stuck | method | ❌ | missing |
| JobStore.cancel | method | ✅ | present |
| JobStore.reset_running | method | ✅ | present |
| JobStore.fail | method | ✅ | present |
| JobStore.delete | method | ❌ | missing |
| JobStore.prune | method | ✅ | present |

## smolotchi/core/lan_resolver.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| resolve_result_by_job_id | function | ✅ | present |

## smolotchi/core/lan_state.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| lan_is_busy | function | ❌ | missing |

## smolotchi/core/normalize.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| normalize_profile | function | ✅ | present |
| profile_hash | function | ❌ | missing |

## smolotchi/core/paths.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| resolve_db_path | function | ❌ | missing |
| resolve_artifact_root | function | ❌ | missing |
| resolve_lock_root | function | ❌ | missing |
| resolve_config_path | function | ❌ | missing |
| resolve_default_tag | function | ❌ | missing |
| resolve_device | function | ❌ | missing |
| resolve_display_dryrun | function | ❌ | missing |

## smolotchi/core/policy.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| Policy | class | ✅ | present |
| Policy.allow_handoff | method | ❌ | missing |
| Policy.scope_allowed | method | ❌ | missing |
| Policy.category_allowed | method | ❌ | missing |
| Policy.autonomous_allowed | method | ❌ | missing |
| PolicyDecision | class | ❌ | missing |
| evaluate_tool_action | function | ✅ | present |

## smolotchi/core/presets.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |

## smolotchi/core/reports.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ReportConfig | class | ❌ | missing |
| ReportRenderer | class | ❌ | missing |
| ReportRenderer.__init__ | method | ❌ | missing |
| ReportRenderer.render_lan_result | method | ❌ | missing |

## smolotchi/core/resources.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| Lease | class | ❌ | missing |
| Lease.expires_at | method | ❌ | missing |
| Lease.to_dict | method | ❌ | missing |
| ResourceManager | class | ✅ | present |
| ResourceManager.__init__ | method | ❌ | missing |
| ResourceManager._lock_path | method | ❌ | missing |
| ResourceManager._read | method | ❌ | missing |
| ResourceManager.current | method | ❌ | missing |
| ResourceManager.acquire | method | ❌ | missing |
| ResourceManager.release | method | ❌ | missing |
| ResourceManager.snapshot | method | ❌ | missing |

## smolotchi/core/self_heal.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| SelfHealer | class | ❌ | missing |
| SelfHealer.report | method | ❌ | missing |
| SelfHealer.clear | method | ❌ | missing |
| SelfHealer.should_restart | method | ❌ | missing |

## smolotchi/core/state.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| CoreStatus | class | ❌ | missing |
| SmolotchiCore | class | ❌ | missing |
| SmolotchiCore.__init__ | method | ❌ | missing |
| SmolotchiCore.set_state | method | ❌ | missing |
| SmolotchiCore._apply_state_engines | method | ❌ | missing |
| SmolotchiCore.safe_stop | method | ❌ | missing |
| SmolotchiCore.safe_start | method | ❌ | missing |
| SmolotchiCore._coerce_lan_job | method | ❌ | missing |
| SmolotchiCore.tick | method | ❌ | missing |
| SmolotchiCore._restart_engine | method | ❌ | missing |

## smolotchi/core/test_artifact_sanity.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_stage_request_min_fields | function | ❌ | missing |

## smolotchi/core/test_artifacts_stage_helpers.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_stage_pending_helpers | function | ❌ | missing |
| test_pending_stage_request_id_injected | function | ❌ | missing |

## smolotchi/core/test_dossier_builder.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_build_lan_dossier_creates_artifact | function | ❌ | missing |

## smolotchi/core/test_policy_tools.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_nmap_requires_approval | function | ❌ | missing |
| test_masscan_disabled_by_default | function | ❌ | missing |
| test_tool_not_in_allowlist_denies | function | ❌ | missing |

## smolotchi/core/toml_patch.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _ensure_wifi_section | function | ❌ | missing |
| patch_wifi_credentials | function | ✅ | present |
| parse_wifi_credentials_text | function | ✅ | present |
| parse_wifi_profiles_text | function | ✅ | present |
| patch_wifi_profiles_set | function | ✅ | present |
| is_profiles_header | function | ❌ | missing |
| is_any_header | function | ❌ | missing |
| toml_value | function | ❌ | missing |
| patch_wifi_profile_upsert | function | ✅ | present |
| is_any_header | function | ❌ | missing |
| toml_value | function | ❌ | missing |
| patch_wifi_allow_add | function | ❌ | missing |
| render | function | ❌ | missing |
| patch_wifi_allow_remove | function | ❌ | missing |
| patch_wifi_scope_map_set | function | ❌ | missing |
| patch_wifi_scope_map_remove | function | ❌ | missing |
| _toml_list | function | ❌ | missing |
| patch_lan_lists | function | ❌ | missing |
| upsert_line | function | ❌ | missing |
| patch_baseline_add | function | ❌ | missing |
| repl | function | ❌ | missing |
| patch_baseline_remove | function | ❌ | missing |
| repl | function | ❌ | missing |
| _parse_baseline_scopes_block | function | ✅ | present |
| _render_baseline_scopes_block | function | ✅ | present |
| cleanup_baseline_scopes | function | ✅ | present |
| patch_baseline_profile_add | function | ❌ | missing |
| repl | function | ❌ | missing |
| patch_baseline_profile_remove | function | ❌ | missing |
| repl | function | ❌ | missing |
| cleanup_baseline_profiles | function | ✅ | present |

## smolotchi/core/validate.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| validate_profiles | function | ❌ | missing |

## smolotchi/core/watchdog.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| SystemdWatchdog | class | ❌ | missing |
| SystemdWatchdog.__init__ | method | ❌ | missing |
| SystemdWatchdog._calc_interval | method | ❌ | missing |
| SystemdWatchdog.start | method | ❌ | missing |
| SystemdWatchdog.ping | method | ❌ | missing |
| SystemdWatchdog._loop | method | ❌ | missing |
| SystemdWatchdog._notify | method | ❌ | missing |
| JobWatchdog | class | ❌ | missing |
| JobWatchdog.__init__ | method | ❌ | missing |
| JobWatchdog.tick | method | ❌ | missing |
| JobWatchdog._last_job_event | method | ❌ | missing |

## smolotchi/device/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/device/buttons.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ButtonConfig | class | ❌ | missing |
| ButtonWatcher | class | ❌ | missing |
| ButtonWatcher.__init__ | method | ❌ | missing |
| ButtonWatcher.start | method | ❌ | missing |
| ButtonWatcher.setup | method | ❌ | missing |
| ButtonWatcher.register | method | ❌ | missing |
| ButtonWatcher.cb | method | ❌ | missing |
| ButtonWatcher._run | method | ❌ | missing |
| ButtonWatcher.stop | method | ❌ | missing |

## smolotchi/device/power.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| PowerStatus | class | ❌ | missing |
| _read_first_capacity_sysfs | function | ❌ | missing |
| PowerMonitor | class | ❌ | missing |
| PowerMonitor.read | method | ❌ | missing |
| PowerMonitor.to_dict | method | ❌ | missing |

## smolotchi/device/profile.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| DeviceProfile | class | ❌ | missing |
| get_device_profile | function | ❌ | missing |

## smolotchi/display/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |

## smolotchi/display/displayd.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| UIState | class | ❌ | missing |
| _utc_iso | function | ❌ | missing |
| _safe_font | function | ❌ | missing |
| _render_text_screen | function | ❌ | missing |
| _dryrun_enabled | function | ❌ | missing |
| main | function | ❌ | missing |
| on_btn | function | ❌ | missing |
| _poll_buttons | function | ❌ | missing |
| _tick_render | function | ❌ | missing |

## smolotchi/display/render.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| render_state | function | ❌ | missing |

## smolotchi/display/test_display_render.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| test_render_text_screen_smoke | function | ❌ | missing |

## smolotchi/display/waveshare_driver.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| EPDDriver | class | ✅ | present |
| EPDDriver.__init__ | method | ❌ | missing |
| EPDDriver.init | method | ❌ | missing |
| EPDDriver.size | method | ❌ | missing |
| EPDDriver.clear | method | ❌ | missing |
| EPDDriver.display_image | method | ❌ | missing |

## smolotchi/engines/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/engines/lan_engine.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| LanConfig | class | ❌ | missing |
| LanEngine | class | ❌ | missing |
| LanEngine.__init__ | method | ❌ | missing |
| LanEngine.start | method | ❌ | missing |
| LanEngine.stop | method | ❌ | missing |
| LanEngine._tail_since | method | ❌ | missing |
| LanEngine.enqueue | method | ❌ | missing |
| LanEngine.generate_plan | method | ❌ | missing |
| LanEngine.run_latest_plan_autonomous | method | ❌ | missing |
| LanEngine.tick | method | ❌ | missing |
| LanEngine.health | method | ❌ | missing |

## smolotchi/engines/net_detect.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _run | function | ❌ | missing |
| detect_ipv4_cidr | function | ✅ | present |
| cidr_to_network_scope | function | ✅ | present |
| detect_scope_for_iface | function | ❌ | missing |

## smolotchi/engines/net_health.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _run | function | ❌ | missing |
| default_gateway | function | ❌ | missing |
| has_default_route | function | ❌ | missing |
| ping | function | ❌ | missing |
| health_check | function | ❌ | missing |

## smolotchi/engines/test_wifi_artifacts.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _write_config | function | ❌ | missing |
| _make_engine | function | ❌ | missing |
| test_wifi_profile_selection_artifact | function | ❌ | missing |
| test_wifi_connect_artifacts | function | ❌ | missing |
| test_wifi_disconnect_artifacts | function | ❌ | missing |
| test_wifi_ui_connect_enqueues_lan_and_records_timeline | function | ❌ | missing |

## smolotchi/engines/tools_engine.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ToolsEngine | class | ❌ | missing |
| ToolsEngine.__init__ | method | ❌ | missing |
| ToolsEngine.start | method | ❌ | missing |
| ToolsEngine.stop | method | ❌ | missing |
| ToolsEngine.tick | method | ❌ | missing |
| ToolsEngine._run_nmap | method | ❌ | missing |
| ToolsEngine._run_bettercap | method | ❌ | missing |
| ToolsEngine._store_bundle | method | ❌ | missing |
| ToolsEngine._tool_for_job | method | ❌ | missing |
| ToolsEngine._evaluate_policy | method | ❌ | missing |
| ToolsEngine._extract_stage_request_id | method | ❌ | missing |
| ToolsEngine._has_approval | method | ❌ | missing |
| ToolsEngine._ensure_stage_request | method | ❌ | missing |
| ToolsEngine._release_approved_blocks | method | ❌ | missing |
| ToolsEngine.health | method | ❌ | missing |

## smolotchi/engines/wifi_connect.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _run | function | ❌ | missing |
| connect_wpa_psk | function | ✅ | present |
| disconnect_wpa | function | ❌ | missing |

## smolotchi/engines/wifi_engine.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| WifiEngine | class | ❌ | missing |
| WifiEngine.__init__ | method | ❌ | missing |
| WifiEngine.start | method | ❌ | missing |
| WifiEngine.stop | method | ❌ | missing |
| WifiEngine._tail_since | method | ❌ | missing |
| WifiEngine._start_session | method | ❌ | missing |
| WifiEngine._truncate_note | method | ❌ | missing |
| WifiEngine._end_session | method | ❌ | missing |
| WifiEngine.tick | method | ❌ | missing |
| WifiEngine.health | method | ❌ | missing |

## smolotchi/engines/wifi_scan.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| WifiAP | class | ❌ | missing |
| _run | function | ❌ | missing |
| scan_iw | function | ✅ | present |

## smolotchi/engines/wifi_targets.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| update_targets_state | function | ❌ | missing |

## smolotchi/merge/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/merge/sources.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _safe_dict | function | ❌ | missing |
| find_wifi_context_for_job | function | ✅ | present |
| list_policy_events_for_job | function | ✅ | present |
| list_host_summaries_for_job | function | ✅ | present |
| get_lan_result_for_job | function | ❌ | missing |

## smolotchi/merge/timeline.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _safe_dict | function | ❌ | missing |
| _ts | function | ❌ | missing |
| build_dossier | function | ❌ | missing |

## smolotchi/parsers/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/parsers/base.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| ParserResult | class | ❌ | missing |
| BaseParser | class | ❌ | missing |
| BaseParser.parse | method | ✅ | present |

## smolotchi/parsers/bettercap.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| BettercapParser | class | ❌ | missing |
| BettercapParser.parse | method | ❌ | missing |

## smolotchi/parsers/masscan.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| MasscanParser | class | ❌ | missing |
| MasscanParser.parse | method | ❌ | missing |

## smolotchi/parsers/merge.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| merge_hosts | function | ❌ | missing |

## smolotchi/parsers/nmap.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| NmapParser | class | ❌ | missing |
| NmapParser.parse | method | ❌ | missing |

## smolotchi/parsers/registry.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| parse | function | ❌ | missing |

## smolotchi/reports/__init__.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ✅ | present |

## smolotchi/reports/aggregate.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _ts_human | function | ❌ | missing |
| _extract_host_from_action_run | function | ❌ | missing |
| _action_summary | function | ❌ | missing |
| build_aggregate_model | function | ❌ | missing |
| build_aggregate_report | function | ❌ | missing |

## smolotchi/reports/badges.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _rank | function | ❌ | missing |
| summarize_host_findings | function | ❌ | missing |
| key | function | ❌ | missing |

## smolotchi/reports/baseline.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| expected_findings_for_scope | function | ❌ | missing |
| profile_key_for_job_meta | function | ❌ | missing |
| expected_findings_for_profile | function | ❌ | missing |
| expected_findings_for_bundle | function | ❌ | missing |
| expected_findings_for_profile_dict | function | ❌ | missing |
| expected_findings_for_scope_dict | function | ❌ | missing |
| summarize_baseline_status | function | ❌ | missing |

## smolotchi/reports/baseline_diff.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| BaselineDiff | class | ❌ | missing |
| _bundle_findings | function | ❌ | missing |
| collect_seen_findings | function | ❌ | missing |
| compute_baseline_diff | function | ❌ | missing |

## smolotchi/reports/diff.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| find_previous_host_summary | function | ❌ | missing |
| resolve_baseline_host_summary | function | ❌ | missing |
| _ports_union | function | ❌ | missing |
| _sev_highest | function | ❌ | missing |
| diff_host_summaries | function | ❌ | missing |
| _touch | function | ❌ | missing |

## smolotchi/reports/diff_export.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _ts | function | ❌ | missing |
| diff_markdown | function | ❌ | missing |
| diff_html | function | ❌ | missing |
| diff_json | function | ❌ | missing |

## smolotchi/reports/diff_links.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| index_host_actions | function | ✅ | present |

## smolotchi/reports/exec_summary.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _now_utc | function | ❌ | missing |
| build_exec_summary | function | ❌ | missing |
| render_exec_summary_md | function | ❌ | missing |
| render_exec_summary_html | function | ❌ | missing |

## smolotchi/reports/export.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _ts_human | function | ❌ | missing |
| build_report_json | function | ❌ | missing |
| build_report_markdown | function | ❌ | missing |

## smolotchi/reports/filtering.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| apply_policy_suppression | function | ✅ | present |
| filter_findings_scripts | function | ❌ | missing |

## smolotchi/reports/findings_aggregate.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| extract_findings_for_host_from_action_run | function | ❌ | missing |
| build_host_findings | function | ✅ | present |
| summarize_findings | function | ✅ | present |

## smolotchi/reports/host_diff.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _ts | function | ❌ | missing |
| host_diff_markdown | function | ❌ | missing |
| host_diff_html | function | ❌ | missing |
| esc | function | ❌ | missing |
| pretty_json | function | ❌ | missing |
| load_artifact_json | function | ❌ | missing |
| unified_diff_text | function | ❌ | missing |
| a_link | function | ❌ | missing |
| render_side | function | ❌ | missing |
| first_id | function | ❌ | missing |
| pick_vuln | function | ❌ | missing |
| side_preview | function | ❌ | missing |

## smolotchi/reports/nmap_classify.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| classify_scripts | function | ❌ | missing |

## smolotchi/reports/nmap_findings.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| _summarize_output | function | ✅ | present |
| parse_nmap_xml_findings | function | ✅ | present |

## smolotchi/reports/normalize.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| apply_normalization | function | ❌ | missing |

## smolotchi/reports/severity.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| infer_severity | function | ✅ | present |

## smolotchi/reports/top_findings.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| aggregate_top_findings | function | ✅ | present |

## smolotchi/reports/wifi_session_report.py

| Symbol | Typ | Docstring | Status |
|------|-----|-----------|--------|
| <module> | module | ❌ | missing |
| wifi_session_html | function | ❌ | missing |
| row | function | ❌ | missing |
