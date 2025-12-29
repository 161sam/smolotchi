# Actions Catalog

Action specs are loaded from YAML packs via `load_pack` and registered in `ActionRegistry`.

Code: smolotchi/actions/registry.py:load_pack, smolotchi/actions/registry.py:ActionRegistry

## Pack: `smolotchi/actions/packs/bjorn_core.yml`

| Action ID | Name | Category | Risk | Driver | Code Reference |
| --- | --- | --- | --- | --- | --- |
| `net.host_discovery` | Host Discovery | `network_scan` | `safe` | `command` | `smolotchi/actions/packs/bjorn_core.yml` |
| `net.port_scan` | Port Scan (XML) | `network_scan` | `caution` | `command` | `smolotchi/actions/packs/bjorn_core.yml` |
| `vuln.assess_basic` | Vulnerability Assessment (basic, XML) | `vuln_assess` | `caution` | `command` | `smolotchi/actions/packs/bjorn_core.yml` |
| `vuln.http_basic` | HTTP Assessment (safe) | `vuln_assess` | `safe` | `command` | `smolotchi/actions/packs/bjorn_core.yml` |
| `vuln.ssh_basic` | SSH Assessment (safe) | `vuln_assess` | `safe` | `command` | `smolotchi/actions/packs/bjorn_core.yml` |
| `vuln.smb_basic` | SMB Assessment (safe) | `vuln_assess` | `caution` | `command` | `smolotchi/actions/packs/bjorn_core.yml` |
| `attack.bruteforce_ssh` | Brute Force SSH | `system_attack` | `danger` | `external_stub` | `smolotchi/actions/packs/bjorn_core.yml` |
| `steal.files_smb` | File Stealing SMB | `file_steal` | `danger` | `external_stub` | `smolotchi/actions/packs/bjorn_core.yml` |

## Action runner

Action execution uses `ActionRunner.execute` and `run_action_spec`.

Code: smolotchi/actions/runner.py:ActionRunner.execute, smolotchi/actions/execution.py:run_action_spec
