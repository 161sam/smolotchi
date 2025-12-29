# Installation

## Python dependencies

The repository provides pip requirement sets for general usage and Raspberry Pi Zero usage.

- `requirements/base.txt`
- `requirements/pi_zero.txt`

Code: requirements/base.txt, requirements/pi_zero.txt

## Config file location

Runtime config is loaded from `config.toml` by default. Both the CLI and web app accept a `--config`/`config_path` argument to override this path.

Code: smolotchi/core/paths.py:resolve_config_path, smolotchi/core/config.py:ConfigStore, smolotchi/ai/worker.py:main, smolotchi/api/web.py:create_app
