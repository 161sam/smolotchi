# **Fix-Plan für den Raspberry Pi Zero (User: `smolotchi`)**

---

# 🔎 Analyse (kurz & präzise)

Aus deinem Output:

```text
core.engine.error {'engine': 'wifi', 'op': 'tick', 'err': "[Errno 2] No such file or directory: 'iw'"}
```

➡️ **Problem ist nicht Smolotchi**, sondern das System:

* Das **Linux-Tool `iw` fehlt**
* `WifiEngine` ruft es direkt auf
* Deshalb läuft:

  * ✅ Core
  * ✅ Worker
  * ❌ WiFi tick fehlerhaft
  * ❌ LAN Engine bewusst **stopped** (normal, siehe unten)

---

# ✅ Fix 1 – System-Pakete installieren (Pflicht)

Auf dem **Raspberry Pi Zero**, eingeloggt als:

```text
smolotchi@smolotchi:~
```

### 🔧 Einmal ausführen:

```bash
sudo apt update
sudo apt install -y iw wireless-tools rfkill iproute2
```

👉 Danach **kein Reboot nötig**, aber schadet nicht.

---

# ✅ Fix 2 – WLAN Interface prüfen

```bash
iw dev
```

Erwartet (Beispiel):

```text
phy#0
    Interface wlan0
        type managed
```

Falls **kein wlan0 erscheint**:

```bash
ip link
```

Wenn WLAN blockiert:

```bash
rfkill list
sudo rfkill unblock all
```

---

# ✅ Fix 3 – Smolotchi Dev-Defaults für Pi Zero setzen

Auf dem Pi bitte **dauerhaft** setzen:

```bash
echo 'export SMOLOTCHI_DEVICE=pi_zero' >> ~/.bashrc
echo 'export SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks' >> ~/.bashrc
echo 'export SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts' >> ~/.bashrc
echo 'export SMOLOTCHI_DB=/var/lib/smolotchi/events.db' >> ~/.bashrc
source ~/.bashrc
```

Und einmal:

```bash
sudo install -d -m 0775 -o smolotchi -g smolotchi /run/smolotchi/locks
sudo install -d -m 0775 -o smolotchi -g smolotchi /var/lib/smolotchi/artifacts
```

---

# ✅ Fix 4 – Services wieder starten (3 Terminals)

## Terminal A – Web

```bash
source .venv/bin/activate
python -m smolotchi.cli --config config.toml web
```

## Terminal B – Worker

```bash
source .venv/bin/activate
python -m smolotchi.ai.worker --loop --log-level INFO
```

## Terminal C – Core

```bash
source .venv/bin/activate
python -m smolotchi.cli --config config.toml core
```

---

# ✅ Erwarteter Health-Status (WICHTIG)

```bash
python -m smolotchi.cli health
```

Soll jetzt zeigen:

```text
wifi  ok=True  detail=running
lan   ok=False detail=stopped
```

👉 **LAN = stopped ist korrekt**, solange:

* kein LAN-Job aktiv
* kein `ui.lan.enqueue` erfolgt ist

---

# 🧠 Optional (aber empfohlen): LAN aktivieren

Zum Testen:

```bash
python -m smolotchi.cli handoff
```

Oder im Web:

* `/lan`
* „Enqueue LAN Job“

Danach:

```bash
python -m smolotchi.cli events --limit 30
```

---

# 🔜 Nächster Schritt 

Wenn `iw` installiert ist, poste **nur**:

```bash
python -m smolotchi.cli health
python -m smolotchi.cli events --limit 20
iw dev
```

Dann gehen wir direkt weiter mit:

> **WiFi → Auto-Connect → LAN Job → lan_job_result → UI Timeline (E2E live)**

