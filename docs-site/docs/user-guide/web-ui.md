# Web UI

## Overview

The web UI is served by the Flask app in `smolotchi/api/web.py`. Navigation and templates are defined in `smolotchi/api/templates` and static assets in `smolotchi/api/static`.

Code: smolotchi/api/web.py:create_app, smolotchi/api/templates/layout.html, smolotchi/api/static/js/ui.js

## Primary routes

- Dashboard: `GET /` → `dashboard()`
- Wi-Fi management: `GET /wifi` → `wifi()`
- LAN overview: `GET /lan` → `lan()`
- AI jobs/stages: `GET /ai/jobs`, `GET /ai/stages`
- Config editor: `GET /config`

Code: smolotchi/api/web.py:dashboard, smolotchi/api/web.py:wifi, smolotchi/api/web.py:lan, smolotchi/api/web.py:ai_jobs, smolotchi/api/web.py:ai_stages, smolotchi/api/web.py:config

## Artifact and report views

Artifacts are served through `/artifact/<artifact_id>` and reports via `/report/<artifact_id>`.

Code: smolotchi/api/web.py:artifact_view, smolotchi/api/web.py:report_view
