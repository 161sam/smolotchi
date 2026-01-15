---

<div align="center">

# 🚧 ACTIVE DEVELOPMENT 🚧

⚠️ **This project is currently under active development** ⚠️

Expect:
- breaking changes
- incomplete features
- experimental behavior
- occasional bugs

🧪 **Not production-ready**

💬 Issues, feedback and PRs are very welcome.

</div>

---

## Smolotchi — Research-Grade Offensive Security Orchestrator

### Abstract

**Smolotchi** is a research-oriented, profile-driven offensive security orchestration framework designed for **controlled laboratory environments**.
It combines wireless reconnaissance, network enumeration, vulnerability assessment, and exploit execution with **full auditability, reproducibility, and temporal analysis**.

Unlike gamified or purely exploit-driven tools, Smolotchi focuses on **understanding attack surface evolution**, **configuration drift**, and **profile-dependent security posture**.

---

### Core Principles

1. **Research before exploitation**
2. **Deterministic behavior**
3. **Full audit trail**
4. **Profile-driven decision making**
5. **Reproducibility over speed**
6. **Strict lab-only design**

---

### Intended Use

Smolotchi is designed for:

* Security research laboratories
* Defensive capability testing
* Detection engineering & purple teaming
* Controlled red-team simulations
* Network hardening validation
* AI-driven attack planning research

🚫 **Not intended for uncontrolled environments**
🚫 **No default “drive-by exploitation”**

---

### Architecture Overview

```
[ Sensors ]
  ├─ WiFi (802.11)
  ├─ LAN (Ethernet/IP)
  ├─ Bluetooth (Classic + BLE)
  └─ Future: SDR / IoT

        ↓

[ Smolotchi Core ]
  ├─ Event Bus (append-only)
  ├─ Job Graph + Planner
  ├─ Profile Engine (SSID / Network / Radio)
  ├─ Artifact Store
  ├─ Baseline + Timeline Engine
  └─ AI Research Engine

        ↓

[ Engines ]
  ├─ WiFi Engine
  ├─ LAN Engine
  ├─ Bluetooth Engine
  └─ (Future) SDR Engine

        ↓

[ Reports ]
  ├─ HTML / Markdown / JSON
  ├─ Diff Reports
  ├─ Baseline Reports
  └─ Research Summaries
```

---

### What makes Smolotchi different?

| Feature                  | Smolotchi |
| ------------------------ | --------- |
| Profile-based attacks    | ✅         |
| Full timeline history    | ✅         |
| Baseline per profile     | ✅         |
| Drift detection          | ✅         |
| Deterministic replay     | ✅         |
| AI as planner            | ✅         |

---

### Legal & Ethical Notice

Smolotchi is a **research framework**.

* All offensive modules are **explicitly disabled by default**
* Exploit execution requires **explicit configuration**
* Designed for **isolated lab networks only**

The authors assume **no liability** for misuse.

---

## Run locally (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### CLI (recommended)

```bash
smolotchi --help
smo --help
smolotchi web
smolotchi core
```

CLI output and exit codes:

* `--format {table,json}` toggles human-readable tables vs JSON for automation (default: table).
* `--dry-run` previews destructive actions without mutating state.
* Exit codes: `0` success, `2` usage, `10` runtime error, `20` validation error, `30` dependency missing.

Terminal A (web):

```bash
python -m smolotchi.api.web
```

Terminal B (AI worker):

```bash
python -m smolotchi.ai.worker --loop --log-level INFO
```

Artifacts are stored under `/var/lib/smolotchi/artifacts`.

---

## Documentation (Docusaurus)

The documentation site lives in `docs-site/` and is built with pnpm.
Docs live at: https://161sam.github.io/smolotchi/
Deployment via GitHub Actions workflow docs-pages.yml.

```bash
cd docs-site
pnpm install
pnpm build
pnpm start
```

---

## Pi Zero / systemd install (canonical)

Use the canonical deploy script to avoid `/opt` vs `/home` drift and to keep systemd pinned to
`/opt/smolotchi/current/.venv` with `SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml`.

**curl | bash**

```bash
curl -sfL https://raw.githubusercontent.com/161sam/smolotchi/main/scripts/deploy.sh | \
  sudo bash -s -- --repo "https://github.com/161sam/smolotchi.git" --branch main --apply
```

**Local repo**

```bash
sudo ./scripts/deploy.sh --apply
```

Optional flags:

* `--with-display` (enable display service)
* `--enable-core-net` (enable CAP_NET_ADMIN unit, disables core)

Environment overrides live in `/etc/smolotchi/env`. The deploy script enforces:

```bash
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
```

### Drift checks

Verify the interpreter and package location are pinned to `/opt`:

```bash
/opt/smolotchi/current/.venv/bin/python -c "import smolotchi, smolotchi.cli as c; print('smolotchi:', smolotchi.__file__); print('cli:', c.__file__)"
/opt/smolotchi/current/.venv/bin/pip show -f smolotchi
```

### Uninstall

Use the CLI wrapper (dry-run by default):

```bash
sudo smolotchi uninstall
sudo smolotchi uninstall --apply
```

---

## AI stage approvals (caution-risk actions)

Actions marked with `risk=caution` are gated by a stage approval flow instead of failing:

1. The plan runner records an `ai_stage_request` artifact and marks the job as **blocked**.
2. Open **/ai/stages** to review and approve the request.
3. Once approved, the worker re-queues the blocked job and continues the run.

You can track blocked jobs in **/ai/jobs** (look for “Blocked (approval required)”).

---

## Troubleshooting

* **Worker offline banner**: If the UI shows the worker as offline, confirm the AI worker process is running and emitting health ticks.
* **Blocked job**: A blocked AI job means a stage approval is required. Approve it in **/ai/stages** or via the CLI `smolotchi stages approve <request_id>`.
* **Artifact 404**: Artifacts are served only from the artifact root (`/var/lib/smolotchi/artifacts`). A 404 usually means the artifact index points to a missing file or a path outside the root.

---

## 🔐 systemd Hardening Model

Smolotchi nutzt ein **zentrales, minimales Hardening-Baseline-Modell** auf Basis von **systemd Drop-ins**, um Sicherheitsoptionen konsistent anzuwenden, ohne Unit-Files zu duplizieren.

### Drop-ins

Hardening wird über Drop-in-Dateien (`*.service.d/*.conf`) umgesetzt:

* gemeinsames Baseline-Hardening (`10-hardening.conf`)
* prune-spezifisches Hardening (`10-hardening-prune.conf`)
* Capability-Defaults für nicht privilegierte Services (`20-cap-defaults.conf`)
* service-spezifische Overrides (`dropins/smolotchi-*.service.d/*.conf`)
  * `ProtectHome` + `PrivateNetwork` + `ReadWritePaths` pro Service
  * `PrivateNetwork=true` exklusiv für prune (alle anderen explizit `false`)
  * Capability-Gates für core/core-net

Dadurch bleiben die eigentlichen Unit-Files schlank, stabil und wartbar.

### RuntimeDirectory

Alle Services verwenden explizite Laufzeit- und State-Verzeichnisse:

* `/run/smolotchi` (Runtime, Locks)
* `/var/lib/smolotchi` (State, DB, Artifacts)

Diese Pfade werden von systemd verwaltet (`RuntimeDirectory=`/`StateDirectory=`), um Namespace-Fehler zu vermeiden.

### ProtectHome – Rationale

`ProtectHome` ist **nicht Teil** der gemeinsamen Baseline, sondern wird pro Service gesetzt.
Für Services ohne Bedarf an `/home` (z. B. Core, Web, AI, Prune) gilt `ProtectHome=true` oder `ProtectHome=read-only`.

Services, die bewusst mit `/home` arbeiten (z. B. Display), setzen `ProtectHome=false` als explizites Override.
So bleibt Hardening **gezielt**, aber **nicht funktional brechend**.

### PrivateNetwork – Rationale

`PrivateNetwork` wird pro Service explizit gesetzt, damit Netzwerkzugriff bewusst dokumentiert bleibt.
Prune läuft mit `PrivateNetwork=true` (über `10-hardening-prune.conf`), alle anderen Services setzen `PrivateNetwork=false`, um Netzwerkzugriff nicht versehentlich zu verlieren.

### CAP_NET_ADMIN (Opt-in)

Netzwerk-relevante Privilegien sind **nicht standardmäßig aktiv**.

* Standard: `smolotchi-core.service` läuft ohne `CAP_NET_ADMIN` und nutzt nur `CAP_NET_RAW`.
* `CAP_NET_ADMIN` ist **exklusiv** für `smolotchi-core-net.service` reserviert.
* Der NET_ADMIN-Service ist **standardmäßig deaktiviert** und muss explizit vom Operator aktiviert werden.
* Opt-in über separate Units oder Flags (z. B. `smolotchi-core-net.service`).

Das macht privilegierte Operationen **explizit sichtbar und auditierbar**.

### Capability-Defaults (alle anderen Services)

Web, AI, Prune und Display laufen mit **leeren Capability-Sets** (`AmbientCapabilities=` und `CapabilityBoundingSet=`) via `20-cap-defaults.conf`.
So bleibt jede Erweiterung eine **bewusste, dokumentierte Ausnahme**.

---

## 🧠 Wrapper vs. systemd

Smolotchi unterscheidet bewusst zwischen **Operator-CLI** und **systemd-Services**.

### Wann `smolotchi`

Der systemweite Wrapper (`/usr/local/bin/smolotchi`) ist gedacht für:

* interaktive Nutzung
* Debugging
* manuelle Wartung
* Operator-Workflows

Er wählt automatisch ein geeignetes Python (System, venv, Repo).

### Wann `.venv/bin/python -m smolotchi.cli`

Direktaufrufe (`.venv/bin/python -m smolotchi.cli`) sind für **Development/Manuell** gedacht.
systemd startet Smolotchi über `ExecStart=/usr/local/bin/smolotchi` (oder einen expliziten Exec-Override).

➡️ **Faustregel:** Menschen nutzen die venv/manuellen Aufrufe – systemd nutzt den Wrapper.

---

# 2️⃣ Threat Model (Research-Tool-konform)

## Threat Model: Smolotchi

### Assets

* Network topology
* Credential artifacts
* Vulnerability findings
* Baseline datasets
* Profile configurations
* AI decision logs

---

### Threat Actors

| Actor                  | Description                 |
| ---------------------- | --------------------------- |
| Researcher             | Authorized lab user         |
| Misconfigured Operator | Accidental misuse           |
| Insider                | Malicious but authenticated |
| External               | Should never access         |

---

### Threats & Mitigations

| Threat                       | Mitigation                   |
| ---------------------------- | ---------------------------- |
| Accidental live exploitation | Profiles + scope hard limits |
| Data poisoning               | Append-only artifacts        |
| AI runaway behavior          | Policy + safety constraints  |
| Privilege escalation         | Engine sandboxing            |
| Replay ambiguity             | Profile hash + timeline      |

---

### AI-Specific Risks

| Risk                   | Mitigation                |
| ---------------------- | ------------------------- |
| Over-optimization      | Deterministic constraints |
| Hallucinated actions   | Action schema validation  |
| Unsafe exploration     | Lab scope enforcement     |
| Non-reproducible plans | Plan graph serialization  |

---

# 3️⃣ Roadmap-Diagramm (klar getrennte Phasen)

```
┌──────────────────────────┐
│          MVP             │
│  (Controlled Research)   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│        Research           │
│  (AI + Timeline + Drift) │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│   Offensive Extensions   │
│  (Explicit, gated, off)  │
└──────────────────────────┘
```

---

## Phase 1 — MVP (JETZT)

**Ziel:** Stabil, auditierbar, erklärbar

✔ WiFi scanning + profiles
✔ LAN scanning + vuln assess
✔ Baseline + diff
✔ Reports
✔ CLI + Web UI
✔ No autonomous exploitation

**Status:** 🟢 fast fertig

---

## Phase 2 — Research Mode

**Ziel:** Erkenntnisse generieren

✔ AI Planner (non-gaming)
✔ Profile timeline
✔ Finding evolution
✔ Cross-profile analysis
✔ “Why was this chosen?” explainability

**Neu: AI Algorithmus**

### Smolotchi AI ≠ Pwnagotchi AI

| Pwnagotchi          | Smolotchi                 |
| ------------------- | ------------------------- |
| Reward = handshakes | Reward = information gain |
| RL + fun            | Constrained planning      |
| Emergent chaos      | Deterministic graphs      |

---

### Smolotchi AI Core (Konzept)

**Input:**

* Current findings
* Baseline deltas
* Profile constraints
* Resource budget

**Output:**

* Action Plan Graph
* Confidence score
* Expected gain
* Risk score

```json
{
  "plan": [
    { "action": "port_scan", "target": "host:10.0.10.5" },
    { "action": "service_enum", "service": "ssh" }
  ],
  "why": [
    "ssh newly appeared",
    "baseline deviation"
  ]
}
```

🧠 **AI erklärt sich selbst.**

---

## Phase 3 — Offensive Extensions (GATED)

**Ziel:** Forschung an Angriffstechniken, nicht Script-Kiddie-Tool

### Module (alle OFF by default)

* LAN brute force
* Bluetooth exploitation
* WiFi Evil Twin
* Credential replay
* Lateral movement
* Payload research

### Sicherheitsmechanismen

✔ Compile-time disable
✔ Config kill-switch
✔ Legal warning banners
✔ Explicit enable flags
✔ Lab scope enforcement

---

# 4️⃣ Bluetooth Engine (analog zu WiFi/LAN)

## Bluetooth Research Scope

### Capabilities

* Device discovery (Classic + BLE)
* Service enumeration
* Weak pairing detection
* Known vuln fingerprinting
* Signal timeline

### Profile Example

```toml
[wifi.profiles."LAB-1"]
bluetooth_enabled = true
bluetooth_scan_mode = "passive"
bluetooth_exploit = false
```

Bluetooth wird **gleichberechtigter Sensor**, nicht “Addon”.

---

# 5️⃣ Entwicklungsplan (konkret)

## Nächste 6 Schritte

1. **Finalize MVP**

   * Stabilisieren
   * Docs
   * Threat model
2. **AI Planner v1**

   * Rule + score based
   * Kein ML yet
3. **Profile Timeline UI**
4. **Bluetooth Scan Engine**
5. **Research Reports**
6. **Exploit Gating Layer**

---
