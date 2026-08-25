# Iteration 17 — Coherence Audit

**Iteration:** goal-market-compass-iter-17
**Date:** 2026-08-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope note

Backend-only maintenance iteration under active maintenance isolation (no frontend, browser, demo, or
replay lane — per the iter spec and the dispatching pump's coordinator note). `git diff` against tracked
files shows only 2 changed source files; the coordinator note flagged that 5 of the 7 changed source
files are untracked. All 7 were opened and read directly (not inferred from a diff):

Tracked (via `git diff a3d88484a5...`):
- `apps/backend/app/engine/j11_preboot_guard.py` — AG-8 bounded-query rewrite of `evaluate_boundary_for_date` / new `_relevant_boundary_rows_statement()` helper + table-absence handling.
- `apps/backend/tests/test_j11_preboot_guard.py` — new `test_iter17_*` cases (owner cases B/E/F, table-absent regression).

Untracked (read directly per coordinator note, confirmed via `git status --porcelain`):
- `apps/backend/scripts/run_j11_maintenance_boundary_arm.py`
- `apps/backend/scripts/run_j11_maintenance_boundary_disarm.py`
- `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py`
- `apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py`
- `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py`

Independently verified empty diffs (confirms the iter spec's own claims):
- `apps/backend/app/api/*` — untouched (no endpoint added/changed).
- `apps/backend/app/models.py` — untouched (no schema change; `MaintenanceBoundary` model pre-existing).
- `apps/frontend/*` — untouched (no UI surface).
- `runs/goal-session-market-compass/state/blueprint.md` — untouched (matches "no blueprint edit this
  iteration" claim).
- `apps/backend/app/engine/warmup.py` — untouched; confirmed (via grep) it is the only production
  call-site of `evaluate_boundary_for_date`, and the function's signature/return shape is unchanged, so
  no call-site update was needed.

## Data Contract check

No row in the blueprint's Data Contract concerns `MaintenanceBoundary` state, the J-11 pre-boot guard,
arm/disarm lifecycle, or AVB/Stage-D readiness classification — this matches the iter spec's own
"Data-contract additions: None" and iteration 16's established precedent (cited in this iteration's spec)
that none of this is a *displayed* value. Independently confirmed: zero touches to
`apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or `compass.py` (the modules backing every
registered Data Contract row).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest (CONTENT + FREEZE/INTEGRITY) | OK — untouched | `app/api` diff empty; `compass.py` not in changed-file set |
| Engine identity | OK — untouched (read-only, from a prior artifact file, in the Stage-D script) | `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py:150-152` reads `iteration-14-identity-path` JSON, never recomputes |
| Stock sector label / Regime / Market phase / Breadth / Sector-theme scores / Stock scores / Evidence ledger / Coverage / Run summary / Readiness-preflight | OK — untouched | no diff hunk in any owning module (`scoring.py`, `sectors.py`, `themes.py`, `evidence` module, `data_manager.py`, `runs.py`, readiness module) |
| J-11 `MaintenanceBoundary` state (arm/disarm, `evaluate_boundary_for_date`) | OK — internal safety/evidence state, never routed through an endpoint or UI component; new arm/disarm scripts are thin CLI wrappers around the pre-existing `register_j11_incident_boundary` / `clear_boundary` functions, not a duplicate registration path | `apps/backend/scripts/run_j11_maintenance_boundary_arm.py:131`, `_disarm.py:123` |
| AVB Stage D readiness / single-bar A/B dollar-volume ratio | OK — script-level composition of already-existing `j11_stage_d.*` / `j11_avb_diagnostic.*` functions (unchanged), writes to a NEW iter-17-scoped evidence file, never edits iteration 16's artifact | `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py:341-345` (reuses `jsd.produce_stage_d_readiness_artifact` unchanged); byte-hash check at lines 134/362 proves iter-16's file is untouched |

No new UI surface was added that fetches any Data Contract value from a non-canonical source (there is
no new UI surface at all this iteration). No new displayed value was introduced that duplicates or
requires registering an existing concept.

## Information Architecture check

No new page/route/feature exists this iteration to check — `apps/frontend/*` has zero diff, and the iter
spec's own "UI surface changes: None" / "Product surface delta: None" fields are confirmed by the diff.
`reports/phase-goal-market-compass-iter-17-ui-surface-map.md` independently confirms: "Status: Not mapped
this iteration — maintenance isolation... No surface was opened or inspected."

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change) | N/A | `apps/frontend/` diff is empty; ui-surface-map confirms no surface touched |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This is a clean, self-contained backend maintenance iteration: the AG-8 fix rewrites the
  existing canonical `evaluate_boundary_for_date` in place (not a parallel implementation), the new
  arm/disarm scripts are thin wrappers around pre-existing registration/clear functions sourcing their
  date-set exclusively from the canonical `j11_maintenance.INCIDENT_DATES`, and the Stage-D readiness
  rider reuses iteration 15/16's functions unchanged while writing to its own new, non-overlapping
  evidence file. Nothing here creates a second source of truth for any registered or displayed value.
