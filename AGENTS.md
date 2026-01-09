# AGENTS.md — Smolotchi Codex Agent Instructions

You are Codex working inside the Smolotchi repository.

## North Star
Implement the roadmap in `ROADMAP.md` sequentially. Do not jump phases.

## What to do first
1) Read `ROADMAP.md`
2) Identify the **ACTIVE phase** and its **next unblocked task**
3) Execute **only that task**, end-to-end, with tests + docs updates relevant to the task.

## Scope rules
- Work strictly within the currently active phase of `ROADMAP.md`.
- Never implement Phase 2/3 items while Phase 1 is incomplete.
- If a task depends on another task, do the dependency first.

## Change rules
- Prefer small, atomic commits.
- Avoid duplicated configuration: if hardening is in drop-ins, remove it from unit files (single source of truth).
- Never introduce implicit privileges.
- CAP_NET_ADMIN must remain **opt-in** only (separate unit, disabled by default).

## Output expectations for each task
When you respond, always include:
1) **What you changed** (files + summary)
2) **Why** (ties back to ROADMAP.md)
3) **How to validate** (exact commands)
4) **Risks / Rollback** steps
5) **Suggested commit message**

## Implementation constraints
- Keep runtime paths consistent: `/run/smolotchi` and `/var/lib/smolotchi`
- Use systemd drop-ins for hardening; keep units minimal.
- Do not break offline-first operation.

## If uncertain
If there is ambiguity:
- Make the safest assumption aligned with `ROADMAP.md`
- Document the assumption in the PR/commit message and in docs

## Start instruction
Always start your work by printing:
- Active phase
- The exact task you are executing (copy the task title from ROADMAP.md)
- The validation commands you will run at the end
