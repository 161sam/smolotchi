# Troubleshooting

## Config changes not reflected

The config store caches values and reloads on file mtime changes or explicit reloads.

Code: smolotchi/core/config.py:ConfigStore.get, smolotchi/core/config.py:ConfigStore.reload

## ProtectHome / config path errors

If systemd logs show `PermissionError` or `ModuleNotFoundError` pointing at `/home/...`, verify that:

- `SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml` is present in `/etc/smolotchi/env`
- The active interpreter is `/opt/smolotchi/current/.venv/bin/python`

Drift checks:

```bash
/opt/smolotchi/current/.venv/bin/python -c "import smolotchi, smolotchi.cli as c; print('smolotchi:', smolotchi.__file__); print('cli:', c.__file__)"
/opt/smolotchi/current/.venv/bin/pip show -f smolotchi
```

## Stage request pending

Stage requests are pending until an approval artifact is present.

Code: smolotchi/core/artifacts.py:ArtifactStore.is_stage_request_pending, smolotchi/api/web.py:ai_stage_approve
