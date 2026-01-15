# Smolotchi Pi Zero Bootstrap (Deprecated)

The scripts in this directory are **deprecated**. Use the canonical deploy script instead:

```bash
curl -sfL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/deploy.sh | \
  sudo bash -s -- --repo "https://github.com/<owner>/<repo>.git" --branch main --apply
```

Local repo usage:

```bash
sudo ./scripts/deploy.sh --apply
```

These legacy scripts now forward to `scripts/deploy.sh` and will be removed in a future release.
