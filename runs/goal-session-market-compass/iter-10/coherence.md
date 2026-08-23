# Iteration 10 — Coherence Audit

**Iteration:** goal-market-compass-iter-10
**Date:** 2026-08-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration is J-11 Stages B/B1/B2 only: read-only pre-reset inventory tooling, a schema-contract
model-declaration change, and a frozen attempt-identity precondition. Per the iter spec (`docs/phases/
goal-market-compass-iter-10.md`, "New user-facing capability" / "New information displayed" / "New user
actions" / "UI surface changes" / "Product surface delta" — all `None`; "Frontend Present: no"), no
served endpoint, page, or displayed value changes. Confirmed against the diff: `git diff
fe7844f062aad7d93cb648cce47d945d15cf0c8a --stat -- apps/frontend/` returns empty — zero frontend files
touched. The full noise-excluded diff touches exactly one tracked file (`apps/backend/app/models.py`,
+29/-1) plus three new backend-only files (`apps/backend/app/engine/j11_maintenance.py`,
`apps/backend/scripts/run_j11_pre_reset_inventory.py`, `apps/backend/tests/test_j11_maintenance.py`).
`reports/phase-goal-market-compass-iter-10-ui-surface-map.md` records "Not mapped this iteration —
maintenance isolation," consistent with zero UI surface change.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `NextSessionManifest.source_run_id` (internal provenance column, never a displayed field per blueprint's Blueprint-conformance note) | OK | `apps/backend/app/models.py:820` — FK *declaration* dropped (`foreign_key="scanner_runs.id"` removed), column and its VALUE-write-once behavior unchanged; `index=True` retained. No live-DB migration (comment confirms additive-ALTER-only rule respected). Not a Data Contract row and not served to any UI. |
| Engine identity (registered Data Contract row: `app.engine.engine_identity`, served via `GET /api/compass` / `GET /api/runs`) | OK — canonical source reused, not duplicated | `apps/backend/app/engine/j11_maintenance.py:210` — `freeze_attempt_identity` calls `engine_identity.compute_engine_identity(cfg)`, the SAME function `scanner.persist_run_payload` already stamps onto `ScannerRun.engine_identity` (confirmed in module docstring lines 11-14 and function docstring lines 200-203: "reused, not reimplemented"). Result is written only to a maintenance JSON artifact (`runs/goal-market-compass-iter-10/j11-frozen-identity.json`), never served via a new endpoint. |
| `app.engine.compass.basis_disclosure` (existing reconciliation logic) | OK — unchanged | Dev handoff confirms "needed no change — confirmed by reading it, not modified"; `git diff` shows no edits to `apps/backend/app/engine/compass.py`. |
| Pre-reset inventory / frozen-identity artifacts (`capture_pre_reset_inventory`, `freeze_attempt_identity`, `check_attempt_identity_consistency`) | UNREGISTERED (not applicable — internal tooling, not a UI-displayed value) | `apps/backend/app/engine/j11_maintenance.py:100-236` — these compute maintenance artifacts written to `runs/goal-market-compass-iter-10/*.json` for a later engineering stage (Stage D), not values served to any user-facing endpoint or page. Outside the Data Contract's scope by the blueprint's own definition (displayed values only). Not a WARN — nothing new is displayed. |

No duplicate computation and no non-canonical serving path found. The one registered value this
iteration touches (Engine identity) explicitly reuses its canonical computing function.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | N/A | `git diff fe7844f062aad7d93cb648cce47d945d15cf0c8a --stat -- apps/frontend/` is empty; `apps/frontend/components/sidebar.tsx` untouched. |

No new nav entries, no new pages, no parallel shell, no duplicate home. IA is unaffected this
iteration, matching the spec's own "Blueprint conformance: No new surfaces; no edit to
`runs/goal-session-market-compass/state/blueprint.md` this iteration."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None specific to coherence. (The dev handoff's "Known Issues" note about a pre-existing,
  iteration-unrelated `test_no_magic_numbers.py` failure in `indicators.py`/`forward_testing.py`/
  `research.py` is a test-suite/code-quality matter for the reviewer/auditor, not a coherence
  concern — no displayed value or nav surface is implicated.)
