# Smolotchi Tech-Debt & Lose Ends Report

## Executive Summary
Smolotchi’s Flask UI is functional but relies on several implicit runtime assumptions (core/worker availability, artifact integrity, action registry capabilities). The UI templates also mix inline styling with button/link conventions, and error handling is mostly “silent fail,” which makes debugging harder. The biggest near-term risks are around brittle AI job execution (registry mismatch) and artifact/report path handling.

---

## AI worker execution pipeline
1. UI enqueues `ai_plan` jobs via `POST /ai/run`, storing an `ai_run_request` artifact with `plan_artifact_id` or `scope`.
2. The AI worker (`python -m smolotchi.ai.worker --loop`) polls the JobStore for queued `ai_plan` jobs, parses `req:<artifact_id>` from the job note, and loads the request artifact.
3. If the request references a plan artifact, the worker loads the `ai_plan` document and runs it; otherwise it generates a plan via `AIPlanner` and runs it.
4. `PlanRunner` executes steps (policy-aware via `ActionRunner`), records an `ai_plan_run` artifact, and emits `ai_job_link` so the UI can link “Open run.”

### Known risks
- Missing or malformed `ai_run_request` artifacts will fail jobs (watch for stale job notes).
- Plan artifacts that are missing or corrupted will fail before any `ai_plan_run` is written, leaving no run link for the UI.
- Action registry mismatches (metadata-only packs vs executable actions) can still block execution if the runner cannot execute actions.

---

## Priority P0 (Immediate)

### P0-1: AI job execution uses a registry that may not have runnable actions
**Symptom →** AI jobs can enqueue/attempt to run but fail at runtime with “Unknown action” or attribute errors when invoking `action.run`.
**Cause →** `PlanRunner` expects action instances with a `.run()` method, but in several entry points only `ActionSpec` metadata is loaded (e.g., `load_pack` in `smolotchi/actions/registry.py`), which does not provide executable actions.
**Fix Proposal →** Either (a) load executable action implementations into the registry used by `PlanRunner`, or (b) update `PlanRunner` to dispatch via `ActionRunner` (which already knows how to execute actions by id). Ensure the same registry is used by worker + core.
**Effort →** M

### P0-2: Artifact/report file handling relies on stored paths without validation
**Symptom →** `/artifact/<id>/download` and `/report/<id>` trust paths from the artifact index; corrupted index entries can produce unexpected file access or failures.
**Cause →** `send_file` uses whatever `path` is stored in the artifact index without enforcing a root or validating file extension.
**Fix Proposal →** Constrain artifacts to the artifact store root (`ArtifactStore.root`) and verify path resolution before sending files. Return 404 for any path outside root.
**Effort →** S

---

## Priority P1 (Soon)

### P1-1: UI assumes background services are running
**Symptom →** UI actions (e.g., plan generation) are acknowledged but no artifacts appear if core/worker is not running.
**Cause →** The web UI publishes bus events without verifying that a core daemon is consuming them.
**Fix Proposal →** Add “core health” indicators and a small status banner if no recent `core.health` ticks are seen; optionally queue fallback tasks or show “pending” states in the UI.
**Effort →** S

### P1-2: Inconsistent link/button styling across templates
**Symptom →** Mixed inline styles and button classes cause inconsistent visual hierarchy and spacing.
**Cause →** Templates combine inline-styled anchors with `.btn` and `.pill` classes.
**Fix Proposal →** Consolidate common action rows into reusable partials, adopt `.btn`/`.btn.secondary` consistently, and remove inline styles for common actions.
**Effort →** S

### P1-3: Missing or sparse empty-state guidance
**Symptom →** Pages like LAN reports/results and AI plans can appear blank with no next step.
**Cause →** Empty state text is minimal and lacks CTAs.
**Fix Proposal →** Standardize an empty-state component with a short explanation and a primary action button (e.g., “Run LAN Job”).
**Effort →** S

---

## Priority P2 (Backlog)

### P2-1: Inline styles across templates
**Symptom →** Styling in templates is hard to maintain and inconsistent.
**Cause →** Many templates rely on per-element inline styles instead of a shared CSS system.
**Fix Proposal →** Promote repeated inline styles into CSS utility classes (`.row`, `.btn-row`, spacing helpers).
**Effort →** M

### P2-2: Sparse test coverage and validation
**Symptom →** Changes to templates or core logic can regress without detection.
**Cause →** No UI/template tests, limited input validation on routes, and few assertions on artifact payloads.
**Fix Proposal →** Add lightweight tests for view rendering and core artifact validation; consider schema validation for artifact payloads.
**Effort →** M

### P2-3: Mixed concerns in `smolotchi/api/web.py`
**Symptom →** `web.py` contains data access, normalization, and presentation logic in a single file.
**Cause →** View logic is monolithic rather than separated into helpers/services.
**Fix Proposal →** Introduce helpers for artifact normalization and move reusable logic into `smolotchi/api/view_models.py`.
**Effort →** M

---

## Quick Wins
- Add a “core health” banner in the layout when no recent `core.health` events are seen. (S)
- Normalize artifact link lists in one helper to avoid repeated defensive checks. (S)
- Convert repeated inline link styles in templates to `.btn` classes. (S)

## Bigger Refactors (Later)
- Create a dedicated UI view-model layer for AI/LAN pages to keep templates minimal. (M)
- Introduce a single job/plan status API to drive UI instead of pulling from multiple tables/artifacts. (L)
- Consolidate action execution around `ActionRunner` with clear interfaces for planning vs execution. (L)

## Security / Robustness Notes
- Validate artifact/report paths to avoid serving unexpected files. (`smolotchi/api/web.py`)
- Guard against malformed artifacts and unknown IDs by adding schema checks before rendering.
- Add rate limits or size caps for large JSON payloads in artifact views/downloads.
