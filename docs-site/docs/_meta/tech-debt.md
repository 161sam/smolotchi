# Tech-Debt (Structural)

Findings are based on static structure. No runtime behavior is inferred.

### smolotchi/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/actions/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/actions/cache.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - find_fresh_portscan_for_host (LOC: 30, complexity: 11)
    - find_fresh_vuln_for_host_action (LOC: 33, complexity: 13)
    - put_service_fingerprint (LOC: 47, complexity: 16)

### smolotchi/actions/execution.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - run_action_spec (LOC: 147, complexity: 16)

### smolotchi/actions/fingerprint.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - service_fingerprint_by_key (LOC: 35, complexity: 18)

### smolotchi/actions/parse.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - parse_nmap_xml_up_hosts (LOC: 29, complexity: 11)

### smolotchi/actions/parse_services.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - parse_nmap_xml_services (LOC: 61, complexity: 24)
    - summarize_service_keys (LOC: 22, complexity: 17)

### smolotchi/actions/plan_runner.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - BatchPlanRunner.run (LOC: 748, complexity: 140)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - PlanRunner.run (LOC: 77, complexity: 11)
    - PlanRunner._find_stage_request (LOC: 26, complexity: 10)
    - BatchPlanRunner._build_batched_steps (LOC: 21, complexity: 10)
    - BatchPlanRunner.run (LOC: 748, complexity: 140)

### smolotchi/ai/replay.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - _collect_links (LOC: 23, complexity: 11)
    - evaluate_plan_run (LOC: 39, complexity: 12)

### smolotchi/ai/worker.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - AIWorker._tick (LOC: 102, complexity: 26)
    - AIWorker._process_job (LOC: 97, complexity: 16)

### smolotchi/api/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/api/conftest.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - client (LOC: 6, complexity: 1); missing annotations

### smolotchi/api/test_templates_smoke.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - test_templates_smoke (LOC: 9, complexity: 1); missing annotations

### smolotchi/api/view_models.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - effective_lan_overrides (LOC: 53, complexity: 24)

### smolotchi/api/web.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - create_app (LOC: 2198, complexity: 523)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - create_app (LOC: 2198, complexity: 523)

### smolotchi/cli.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - cmd_core (LOC: 289, complexity: 17)
    - build_parser (LOC: 201, complexity: 1)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - cmd_core (LOC: 289, complexity: 17)
    - cmd_wifi_connect (LOC: 26, complexity: 11)
    - cmd_jobs_list (LOC: 49, complexity: 13)
    - cmd_stages_list (LOC: 38, complexity: 10)
    - cmd_finding_history (LOC: 38, complexity: 18)
    - cmd_ai_replay (LOC: 38, complexity: 10)
    - cmd_ai_replay_batch (LOC: 69, complexity: 18)

### smolotchi/cli_artifacts.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - add_artifacts_subcommands (LOC: 152, complexity: 23)

### smolotchi/cli_profiles.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - add_profiles_subcommands (LOC: 48, complexity: 10)

### smolotchi/core/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/core/artifacts.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - ArtifactStore.prune (LOC: 60, complexity: 17)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - ArtifactStore.__init__ (LOC: 5, complexity: 2); missing annotations
- Problem: Classes with many methods (>= 20)
  - Risk: Potential God-object / unclear responsibilities
  - Affected symbols:
    - ArtifactStore (methods: 25)

### smolotchi/core/artifacts_gc.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - _extract_ref_ids_from_bundle (LOC: 42, complexity: 24)

### smolotchi/core/bus.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - SQLiteBus.__init__ (LOC: 4, complexity: 2); missing annotations

### smolotchi/core/config.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - ConfigStore._from_dict (LOC: 210, complexity: 28)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - ConfigStore._from_dict (LOC: 210, complexity: 28)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - ConfigStore.__init__ (LOC: 4, complexity: 1); missing annotations

### smolotchi/core/dossier.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - build_lan_dossier (LOC: 91, complexity: 21); missing annotations
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - build_lan_dossier (LOC: 91, complexity: 21); missing annotations

### smolotchi/core/jobs.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - JobStore.pop_next_filtered (LOC: 63, complexity: 19)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - JobStore.__init__ (LOC: 4, complexity: 2); missing annotations
- Problem: Classes with many methods (>= 20)
  - Risk: Potential God-object / unclear responsibilities
  - Affected symbols:
    - JobStore (methods: 25)

### smolotchi/core/lan_resolver.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - resolve_result_by_job_id (LOC: 99, complexity: 30)

### smolotchi/core/normalize.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - normalize_profile (LOC: 50, complexity: 12)

### smolotchi/core/presets.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - PRESETS

### smolotchi/core/reports.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - ReportRenderer.__init__ (LOC: 5, complexity: 1); missing annotations

### smolotchi/core/resources.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - ResourceManager.__init__ (LOC: 3, complexity: 1); missing annotations

### smolotchi/core/state.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - SmolotchiCore._apply_state_engines (LOC: 54, complexity: 15)
    - SmolotchiCore.tick (LOC: 67, complexity: 23)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - SmolotchiCore.__init__ (LOC: 18, complexity: 1); missing annotations

### smolotchi/core/test_artifact_sanity.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - test_stage_request_min_fields (LOC: 9, complexity: 2); missing annotations

### smolotchi/core/toml_patch.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - patch_wifi_credentials (LOC: 37, complexity: 12)
    - parse_wifi_credentials_text (LOC: 35, complexity: 12)
    - parse_wifi_profiles_text (LOC: 53, complexity: 16)
    - patch_wifi_profiles_set (LOC: 54, complexity: 14)
    - patch_wifi_profile_upsert (LOC: 51, complexity: 13)
    - patch_wifi_allow_add (LOC: 35, complexity: 13)
    - patch_wifi_allow_remove (LOC: 33, complexity: 12)
    - patch_wifi_scope_map_set (LOC: 36, complexity: 10)
    - patch_baseline_add (LOC: 46, complexity: 12)
    - patch_baseline_profile_add (LOC: 42, complexity: 12)
    - cleanup_baseline_profiles (LOC: 36, complexity: 10)

### smolotchi/core/validate.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - validate_profiles (LOC: 36, complexity: 14)

### smolotchi/core/watchdog.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - JobWatchdog.tick (LOC: 61, complexity: 15)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - JobWatchdog.__init__ (LOC: 10, complexity: 1); missing annotations

### smolotchi/device/buttons.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - ButtonWatcher.__init__ (LOC: 12, complexity: 2); missing annotations

### smolotchi/display/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/display/displayd.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - _poll_buttons (LOC: 87, complexity: 21)
    - _tick_render (LOC: 111, complexity: 26)
- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - SCREENS

### smolotchi/display/test_display_render.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - test_render_text_screen_smoke (LOC: 3, complexity: 1); missing annotations

### smolotchi/display/waveshare_driver.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - EPDDriver.__init__ (LOC: 2, complexity: 1); missing annotations
    - EPDDriver.size (LOC: 4, complexity: 2); missing annotations
    - EPDDriver.clear (LOC: 3, complexity: 2); missing annotations
    - EPDDriver.display_image (LOC: 3, complexity: 2); missing annotations

### smolotchi/engines/lan_engine.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - LanEngine.tick (LOC: 171, complexity: 27)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - LanEngine.__init__ (LOC: 41, complexity: 6); missing annotations
    - LanEngine._tail_since (LOC: 9, complexity: 6); missing annotations

### smolotchi/engines/tools_engine.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - ToolsEngine.tick (LOC: 74, complexity: 13)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - ToolsEngine.__init__ (LOC: 12, complexity: 1); missing annotations
    - ToolsEngine._evaluate_policy (LOC: 11, complexity: 3); missing annotations

### smolotchi/engines/wifi_engine.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - WifiEngine.tick (LOC: 608, complexity: 157)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - WifiEngine.tick (LOC: 608, complexity: 157)
- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - WifiEngine.__init__ (LOC: 17, complexity: 1); missing annotations
    - WifiEngine._tail_since (LOC: 9, complexity: 6); missing annotations

### smolotchi/engines/wifi_scan.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - scan_iw (LOC: 58, complexity: 14)

### smolotchi/engines/wifi_targets.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - update_targets_state (LOC: 47, complexity: 15)

### smolotchi/merge/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/merge/timeline.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - build_dossier (LOC: 128, complexity: 38)

### smolotchi/parsers/__init__.py

- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - __all__

### smolotchi/parsers/nmap.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - NmapParser.parse (LOC: 40, complexity: 10)

### smolotchi/parsers/registry.py

- Problem: Functions with missing type annotations
  - Risk: Harder static analysis and refactoring
  - Affected symbols:
    - parse (LOC: 5, complexity: 2); missing annotations
- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - PARSERS

### smolotchi/reports/aggregate.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - build_aggregate_model (LOC: 204, complexity: 75)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - build_aggregate_model (LOC: 204, complexity: 75)

### smolotchi/reports/badges.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - summarize_host_findings (LOC: 35, complexity: 14)
- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - SEV_RANK

### smolotchi/reports/baseline.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - summarize_baseline_status (LOC: 28, complexity: 12)

### smolotchi/reports/diff.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - diff_host_summaries (LOC: 84, complexity: 26)
- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - SEV_RANK

### smolotchi/reports/diff_export.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - diff_markdown (LOC: 59, complexity: 18)

### smolotchi/reports/diff_links.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - index_host_actions (LOC: 27, complexity: 14)

### smolotchi/reports/exec_summary.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - render_exec_summary_md (LOC: 35, complexity: 13)

### smolotchi/reports/export.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - build_report_markdown (LOC: 84, complexity: 31)

### smolotchi/reports/filtering.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - apply_policy_suppression (LOC: 59, complexity: 22)
    - filter_findings_scripts (LOC: 25, complexity: 23)

### smolotchi/reports/findings_aggregate.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - build_host_findings (LOC: 117, complexity: 33)
    - summarize_findings (LOC: 37, complexity: 10)

### smolotchi/reports/host_diff.py

- Problem: Very large functions (>= 200 LOC)
  - Risk: Hard to test, unclear error paths
  - Affected symbols:
    - host_diff_html (LOC: 310, complexity: 66)
- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - host_diff_markdown (LOC: 70, complexity: 29)
    - host_diff_html (LOC: 310, complexity: 66)

### smolotchi/reports/nmap_classify.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - classify_scripts (LOC: 28, complexity: 10)

### smolotchi/reports/nmap_findings.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - parse_nmap_xml_findings (LOC: 101, complexity: 31)

### smolotchi/reports/normalize.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - apply_normalization (LOC: 28, complexity: 13)
- Problem: Module-level mutable globals
  - Risk: Implicit shared state across imports
  - Affected symbols:
    - SEV_RANK

### smolotchi/reports/severity.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - infer_severity (LOC: 40, complexity: 15)

### smolotchi/reports/top_findings.py

- Problem: High cyclomatic complexity (>= 10)
  - Risk: Increased branching makes maintenance harder
  - Affected symbols:
    - aggregate_top_findings (LOC: 68, complexity: 14)
