# Smolotchi Roadmap

Stand: 2026-01-09  
Ziel: Stabiler, auditierbarer, offline-first Agent (Pi Zero 2 W) mit systemd-first Betrieb, klaren Privilegiengrenzen, robustem State/Artifact-Handling und stabiler CLI-Oberfläche.

---

## Guiding Principles

- **Offline-first, privacy-first, open-source only**
- **systemd-first**: Services laufen als Units, Hardening via Drop-ins, reproduzierbare Installation
- **Least privilege**: Capabilities minimal, CAP_NET_ADMIN nur per Opt-in Unit
- **Single source of truth**: keine Hardening-Duplizierung (Unit vs Drop-in), klare Runtime-Pfade
- **Operator-friendly**: klare Logs, klare Exit-Codes, maschinenlesbare Outputs, sichere Defaults

---

## Release Gates (Definition of Done)

### v0.1.x (MVP / Phase 1)
- Services starten stabil (core/web/ai/prune), kein Restart-Sturm
- Runtime-Layout konsistent: `/run/smolotchi` + `/var/lib/smolotchi`
- systemd Hardening vereinheitlicht, Ziel: `systemd-analyze security < 6.0` (core/web/ai/prune)
- CAP_NET_ADMIN strikt opt-in (separate Unit, disabled by default)
- SQLite Schema Versioning + Migrationen + Integrity-Hashes für Artifacts
- CLI stabil: Exit-Codes, `--dry-run`, `--format`, maschinenlesbare Fehler

### v0.2 (Operational Hardening + UX)
- Display/EPaper sauber integriert (ohne Home-Abhängigkeit, falls möglich)
- Observability & diagnostics (health endpoints/commands, structured logs)
- Saubere “Operator Workflows” (install/upgrade/rollback)
- Docs komplett (Hardening Model, Runtime Model, Troubleshooting)

### v0.3+ (Ecosystem & Scale)
- Content pipelines, plugin/agent SDK, workflows, integrations
- Multi-node / Fleet Management (optional)
- Advanced AI planning/eval harness

---

# Phase 1 – MVP: Stable Autonomous Agent (v0.1.x) ✅ ACTIVE

## Phase 1.0 – Runtime & systemd (FOUNDATION)
### Goals
- Einheitliches Runtime-Modell: `/run/smolotchi` (runtime locks/sockets) + `/var/lib/smolotchi` (state/db/artifacts)
- systemd Units stabil (kein Restart-Loop), Watchdog korrekt, klare Service-Dependencies

### Tasks
1. **Runtime directory creation**
   - Standard: `RuntimeDirectory=smolotchi` + `RuntimeDirectoryMode=0775`
   - Zusätzlich: `ExecStartPre=/usr/bin/install -d ... /var/lib/smolotchi` wo nötig
   - Alle Services, die `ReadWritePaths=/run/smolotchi` nutzen, müssen garantieren, dass es existiert.

2. **ExecStartPre für Runtime-Verzeichnisse**
   - core/web/ai/prune: `/run/smolotchi`, `/var/lib/smolotchi` sicherstellen
   - display: falls aktiv, Pfade konsolidieren (langfristig nicht in /home arbeiten)

3. **Watchdog / Type=notify**
   - core nutzt `Type=notify`, `WatchdogSec=...`, `NotifyAccess=main`
   - Applikation muss (falls nicht bereits) `sd_notify("WATCHDOG=1")` in Intervallen liefern oder watchdog deaktivieren.

4. **Restart-Loop-Schutz**
   - Konvention: `StartLimitIntervalSec`, `StartLimitBurst`, `RestartSec` Backoff
   - Definierter Fail-State: nach N Fehlschlägen in Zeitraum -> stopped/failed, nicht endlos rotieren.

### Acceptance
- `systemctl restart smolotchi-core` stabil, kein “status=226/NAMESPACE”
- Nach Boot: core/web/ai laufen; prune via timer (oneshot)
- `journalctl -u ...` zeigt keine restart counter explosions

---

## Phase 1.1 – Security Baseline (HARDENING)
### Goals
- Hardening zentral in Drop-ins, Units schlank
- `systemd-analyze security < 6.0` für core/web/ai/prune
- Capabilities auditierbar, keine impliziten Privilegien
- CAP_NET_ADMIN nur per Opt-in Unit (disabled default)

### Tasks
1. **Hardening vereinheitlichen**
   - Global baseline drop-in: `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, Kernel protec., `RestrictNamespaces`, `MemoryDenyWriteExecute`, `UMask=0077`, etc.
   - Keine Duplizierung: gleiche Direktiven nicht zusätzlich in Unit-Dateien.

2. **ProtectHome rationale**
   - Global nicht erzwingen, da display ggf. Home benötigt
   - Zielbild: möglichst viele Services mit `ProtectHome=true` oder `read-only`; exceptions dokumentieren.

3. **Capability audit**
   - core: minimal `CAP_NET_RAW` (falls wirklich nötig)
   - core-net: opt-in `CAP_NET_ADMIN` + evtl. `CAP_NET_RAW`
   - web/ai/prune/display: standardmäßig keine Caps

4. **PrivateNetwork nur wo sinnvoll**
   - prune: `PrivateNetwork=true` (wenn prune kein Netz braucht)
   - core/web/ai: nicht aktivieren

### Acceptance
- `systemd-analyze security smolotchi-{core,web,ai,prune}.service` < 6.0
- `systemd-analyze capability` zeigt nur core/core-net mit Caps
- Keine regressions (web erreichbar, ai worker loop ok, prune läuft per timer)

---

## Phase 1.2 – Storage & State (DURABILITY)
### Goals
- SQLite Schema Versioning + Migrationen
- Artifact integrity (Hashes, optional: manifest)
- Lock-leak detection / robustness

### Tasks
1. **Schema versioning**
   - `schema_version` table
   - Migration runner (idempotent, logs)
2. **Migrationslogik**
   - On startup: detect version, apply migrations safely
3. **Artifact Integrity**
   - Hash pro Artifact (sha256), optional: size+ctime
   - Verify option (CLI)
4. **Lock leak detection**
   - Identify stale locks in `/run/smolotchi/locks`
   - Automatic cleanup policy (safe) + diagnostics

### Acceptance
- Upgrade path tested (older db -> migrate)
- Integrity check passes, corruption surfaces clearly
- No deadlocks / stale locks blocking operations

---

## Phase 1.3 – CLI Stabilisierung (UX FOR OPERATORS)
### Goals
- Einheitliche Exit-Codes
- `--dry-run` für destruktive Befehle
- Konsistente Ausgabeformate `--format json|table`
- Maschinenlesbare Fehlermeldungen

### Tasks
1. **Exit codes standard**
   - 0 success
   - 2 usage
   - 10 runtime error
   - 20 validation error
   - 30 dependency missing
2. **--dry-run**
   - prune / delete / reset etc.
3. **--format**
   - `json` strukturiert
   - `table` human friendly
4. **Errors**
   - JSON errors: `{code, message, hint, details}`

### Acceptance
- CLI tests (smoke) definieren und laufen lassen
- Keine “random” stderr strings ohne code
- Operator workflows dokumentiert

---

# Phase 2 – Operational Hardening & UX (v0.2)
- Display service: Home-Abhängigkeit entfernen (WorkingDirectory -> `/var/lib/smolotchi`)
- Unified install/upgrade flow, rollback strategy
- Better docs, troubleshooting playbooks
- Optional: metrics/logging improvements (still offline-friendly)

---

# Phase 3 – Ecosystem (v0.3+)
- Plugin/agent SDK
- Fleet mode (optional)
- Extended AI evaluation harness

---

## Operator Checklist (always)
- `systemctl cat smolotchi-*.service`
- `systemd-analyze security smolotchi-*.service`
- `systemd-analyze capability smolotchi-core.service smolotchi-core-net.service`
- `journalctl -u smolotchi-core -u smolotchi-web -u smolotchi-ai --since "10 min ago"`
- `smolotchi health` (core/web/ai); prune = timer/oneshot
