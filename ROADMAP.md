# Smolotchi – Project Roadmap

Smolotchi ist ein **offline-first, privacy-first, operator-kontrollierter Agent** für Forschung, Analyse und kontrollierte Sicherheits-Automatisierung auf ressourcenarmen Geräten (z. B. Raspberry Pi Zero 2 W).

Diese Roadmap definiert **klare Entwicklungsphasen**, **Sicherheitsgrenzen** und **Release-Ziele**.  
Offensive Fähigkeiten sind **explizit optional, gated und nie Default**.

---

## Leitprinzipien

- **Offline-first**: kein Cloud-Zwang
- **Privacy-first**: lokale Daten, minimale Exfiltration
- **Least Privilege**: systemd-Hardening, Capability-Gates
- **Operator Control**: keine autonomen Eskalationen ohne Policy
- **Open Source only**
- **Reproduzierbarkeit vor Feature-Tempo**

---

## Versionierung

- **SemVer**
- `v0.x.y` → Breaking Changes erlaubt
- `v1.0.0` → API + Behavior stabil
- Release Notes werden **automatisch aus PR-Titeln** erzeugt

---

## 🚀 Phase 1 – MVP: Stable Autonomous Agent (`v0.1.x`)

### Ziel
Ein **robuster, dauerhaft laufender Agent**, der sicher deploybar ist und keine Überraschungen verursacht.

---

### 1. Runtime & systemd

**Status**
- systemd Units aktiv
- Hardening über Drop-ins zentralisiert

**To-Dos**
- Einheitliches Runtime-Modell (`/run/smolotchi`, `/var/lib/smolotchi`)
- `ExecStartPre` für Runtime-Verzeichnisse in allen Services
- systemd Watchdog korrekt nutzen (`Type=notify`)
- Restart-Loop-Schutz (Backoff / Fail-State)

**Done-Kriterien**
- Alle Services boot-stabil
- Kein `NAMESPACE`-Fehler mehr
- systemd-Restart-Counter < 5 bei Fehlern

---

### 2. Security Baseline

**To-Dos**
- systemd-Hardening vereinheitlichen
- Zielwert: `systemd-analyze security < 6.0`
- Capability-Audit je Service
- `CAP_NET_ADMIN` ausschließlich per Opt-In Service
- Keine impliziten Privilegien

**Explizit verboten**
- Inline-Hardening in Unit-Files
- Default-NET_ADMIN

---

### 3. CLI Stabilisierung

**To-Dos**
- Einheitliche Exit-Codes
- `--dry-run` für destruktive Befehle
- Konsistente `--format json|table`
- Fehlertexte maschinenlesbar

---

### 4. Storage & State

**To-Dos**
- SQLite Schema Versioning
- Migrationslogik
- Artifact Integrity (Hashes)
- Lock-Leak Detection

---

### Meilenstein
**`v0.1.0 – Stable Agent`**

---

## 🔬 Phase 2 – Research & Observability (`v0.2.x`)

### Ziel
Smolotchi wird **messbar**, **vergleichbar** und **erklärbar**.

---

### 1. Observability

- System-Metriken (CPU, Temp, IO, Queue)
- AI-Run-Telemetry
- Replay + Diff stabilisieren
- Deterministische Replays (optional)

---

### 2. Baselines & Profiles

- Profil-Versionierung
- Baseline-Drift Detection
- Explain-Why-Chain:
  Finding → Profile → Policy → Action

---

### 3. UX (Read-only)

- Timeline-UI
- Dossier-Ansicht
- Stage-Approval UI
- Kein Write-Zugriff aus Web

---

### Meilenstein
**`v0.2.0 – Research Platform`**

---

## 🧪 Phase 3 – Gated Offensive Extensions (`v0.3.x`)

### Ziel
Kontrollierte Sicherheits-Automatisierung **ohne Autonomie-Risiko**.

---

### Gating-Modell

Jede offensive Fähigkeit benötigt:
1. systemd-Capability-Gate
2. Policy-Gate
3. Scope-Whitelist
4. Optional Human Approval

---

### Mögliche Module (optional)

- Passive Recon
- Rate-Limited Active Scans
- Exploit-Simulation (Dry-Run)
- Red-Team-Mode (isoliert)

---

### Safety Controls

- Scope-Enforcement
- Network Egress Guards
- Auto-Kill bei Policy-Verstoß
- Tamper Detection

---

### Meilenstein
**`v0.3.0 – Controlled Red-Team Research`**

---

## 🧭 Phase 4 – Ecosystem (`v0.4+`)

- Plugin SDK (read-only first)
- Multi-Agent Federation
- CI-Simulation Runs
- Reproducible Lab Snapshots

---

## Out of Scope (bis 1.0)

- Cloud-Zwang
- Self-Modifying Code
- Autonome Exploitation
- Undokumentierte Capabilities
