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

## Systemd units (web + AI worker)

Sample units live in `packaging/systemd/`:

* `smolotchi-web.service`
* `smolotchi-ai-worker.service`

Optional overrides can be placed in `/etc/smolotchi/smolotchi.env`:

```bash
SMOLOTCHI_PROJECT_DIR=/opt/smolotchi
SMOLOTCHI_VENV_PYTHON=/opt/smolotchi/.venv/bin/python
SMO_AI_WATCHDOG_S=300
```

Enable services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now smolotchi-web smolotchi-ai-worker
```

Smoke-test:

```bash
bash scripts/smoke_ai_run.sh
```

Artifacts are stored under `/var/lib/smolotchi/artifacts`.

---

## Pi Zero Setup (Raspberry Pi OS Lite)

Bootstrap a fresh Raspberry Pi OS Lite installation with the provided script.

**Option A: curl | bash (example)**

```bash
curl -sfL https://raw.githubusercontent.com/<you>/smolotchi/main/scripts/pi_zero/bootstrap.sh | \
  sudo bash -s -- --repo "https://github.com/<you>/smolotchi.git" --branch main --enable-sudo
```

**Option B: clone the repo and run locally**

```bash
git clone https://github.com/<you>/smolotchi.git
cd smolotchi
sudo ./scripts/pi_zero/bootstrap.sh --repo "https://github.com/<you>/smolotchi.git" --branch main --enable-sudo
```

Services are installed to `/etc/systemd/system` and enabled on boot. Check status:

```bash
sudo systemctl status smolotchi-core smolotchi-web smolotchi-ai-worker --no-pager
sudo journalctl -u smolotchi-core -n 50 --no-pager
```

Start/stop/restart:

```bash
sudo systemctl start smolotchi-core smolotchi-web smolotchi-ai-worker
sudo systemctl stop smolotchi-core smolotchi-web smolotchi-ai-worker
sudo systemctl restart smolotchi-core smolotchi-web smolotchi-ai-worker
```

See `scripts/pi_zero/README.md` for a smoke checklist.

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
