# Codex Agent Instructions – Smolotchi

Dieses Repository wird **sequenziell und strikt roadmap-getrieben** entwickelt.

## Autorität

Die Datei `ROADMAP.md` ist **verbindlich**.
Kein Feature, keine Refactor-Maßnahme und keine Optimierung darf außerhalb der aktuellen Phase erfolgen.

---

## Arbeitsmodus

Der Agent arbeitet **single-threaded, sequenziell und deterministisch**.

Für jeden Schritt gilt:
1. ROADMAP.md lesen
2. Aktuelle Phase bestimmen
3. Kleinste sinnvolle Arbeitseinheit wählen
4. Änderungen umsetzen
5. Commit erstellen
6. Fortschritt dokumentieren

---

## Harte Regeln

❌ Keine neuen Features ohne Roadmap-Eintrag  
❌ Keine Privilegien ohne explizite Freigabe  
❌ Keine systemd-Hardening-Duplikate  
❌ Keine stillen Verhaltensänderungen  

✅ Kleine, überprüfbare Commits  
✅ Explizite Sicherheit vor Funktion  
✅ Kommentare bei Security-relevanten Stellen  

---

## Commit-Regeln

- Präfixe: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `security:`
- Ein Commit = ein Thema
- Keine Misch-Commits

---

## Dokumentation

- Jede strukturelle Änderung → Docs anpassen
- systemd-Änderungen immer erklären
- Security-Entscheidungen begründen

---

## Abbruchkriterien

Der Agent **stoppt und meldet zurück**, wenn:
- ein Schritt unklar ist
- Security-Implikationen nicht eindeutig sind
- Roadmap-Konflikte auftreten

---

## Ziel

Am Ende von `v0.1.0` ist Smolotchi:
- boot-stabil
- sicher gehärtet
- reproduzierbar installierbar
- operator-kontrolliert
