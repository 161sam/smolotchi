# Troubleshooting

## Config changes not reflected

The config store caches values and reloads on file mtime changes or explicit reloads.

Code: smolotchi/core/config.py:ConfigStore.get, smolotchi/core/config.py:ConfigStore.reload

## Stage request pending

Stage requests are pending until an approval artifact is present.

Code: smolotchi/core/artifacts.py:ArtifactStore.is_stage_request_pending, smolotchi/api/web.py:ai_stage_approve
