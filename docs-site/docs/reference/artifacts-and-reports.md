# Artifacts and Reports

## Artifact storage

Artifacts are stored under the artifact root (see `resolve_artifact_root`) and indexed in `index.json`. JSON, text, and file artifacts are written via `ArtifactStore.put_json`, `put_text`, and `put_file`.

Code: smolotchi/core/paths.py:resolve_artifact_root, smolotchi/core/artifacts.py:ArtifactStore.put_json, smolotchi/core/artifacts.py:ArtifactStore.put_text, smolotchi/core/artifacts.py:ArtifactStore.put_file

## Artifact integrity manifests

Each artifact write produces a sidecar manifest at `<artifact_path>.manifest.json` with the relative path, SHA256, size in bytes, and creation timestamp. Use `smolotchi artifacts verify` to validate a single artifact or scan all manifests for corruption detection.

Code: smolotchi/core/artifacts.py:ArtifactStore._write_manifest_for_artifact, smolotchi/core/artifacts.py:ArtifactStore.verify, smolotchi/cli_artifacts.py:add_artifacts_subcommands

## Artifact lookup

Artifacts can be fetched by ID with `get_json` and listed with `list`. Stage requests/approvals are also resolved from artifacts.

Code: smolotchi/core/artifacts.py:ArtifactStore.get_json, smolotchi/core/artifacts.py:ArtifactStore.list, smolotchi/core/artifacts.py:ArtifactStore.find_latest_stage_request

## Reports

Report generation modules live in `smolotchi/reports/` and templates are referenced by config (`reports.templates_dir`).

Code: smolotchi/reports/__init__.py, smolotchi/core/config.py:ReportsCfg

## Safe artifact paths

Artifact downloads resolve paths via `_safe_store_path`, preventing traversal outside the artifact root.

Code: smolotchi/api/web.py:_safe_store_path
