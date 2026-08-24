# Iteration 13 — Coherence Audit

**Iteration:** goal-market-compass-iter-13
**Date:** 2026-08-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration

Backend-only, maintenance-isolation iteration executing J-11 Stage C — the owner-authorized (docs/goal.md
J-11 step 11, rulings C1-C12, 2026-08-24) bounded destructive clear of derived-state rows for exactly 11
incident dates. No frontend file changed, no application service booted, no new endpoint added, no
Data-Contract row registered or reassigned per the iteration spec's own "Blueprint conformance" /
"Data-contract additions: None" fields — confirmed directly against the diff, not just asserted by the
spec.

Diff reviewed: `git diff 37c7c7c8097c6ca45f40f1aa15e2708d042a7262` (snapshot SHA matches
`runs/goal-session-market-compass/iter-13/snapshot-sha`) plus `git status` for untracked new files. No
`iter-diff.md` bounded diff exists for this iteration; the raw noise-excluded diff was used directly.
Tracked change: `apps/backend/app/engine/data_manager.py` (+87/-1, new `clear_snapshot_dates` function).
Untracked new files: `apps/backend/app/engine/j11_stage_c.py` (635 lines, preflight/mutation-accounting
tooling), `apps/backend/scripts/run_j11_stage_c_bounded_clear.py` (`--confirm`-gated CLI), and two
fixture-only test modules (`test_j11_stage_c_bounded_clear.py`, `test_j11_stage_c_preflight.py`).
`docs/goal.md`'s apparent diff against the snapshot is a red herring from the snapshot being a stash
commit chronologically ahead of `HEAD` — `git diff <snapshot-sha> -- docs/goal.md` (the correct
comparison) shows zero change; the file is untouched by this iteration.

`reports/phase-goal-market-compass-iter-13-ui-surface-map.md` confirms: "Not mapped this iteration —
maintenance isolation... No surface was opened or inspected."

## Data Contract check

None of the blueprint's registered values have a new computing module, a new serving endpoint, or a
client-side recomputation introduced this iteration. `clear_snapshot_dates` (`data_manager.py:2244-2321`)
issues `DELETE` statements only against `ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`/
`ForwardReturn` for the 11 incident dates — it is a data-repair operation on the storage layer, not a
producer of any displayed value. `app/engine/j11_stage_c.py` is read-only precondition/evidence tooling
that explicitly composes existing canonical primitives (`app.engine.j11_maintenance.freeze_attempt_identity`
for the Data-Contract-registered "Engine identity" value, reused rather than reimplemented — line 210,
216) rather than introducing a parallel computation. Grepped both new files for FastAPI route
registrations (`APIRouter`, `@router`) and for any Data-Contract keyword (`engine_identity`, `compass.`,
`build_manifest_payload`, `coverage_from_storage`, `score_sectors`, `score_stocks`) — zero route
definitions found; the only `engine_identity` references are the documented reuse noted above.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Engine identity | OK — reused, not recomputed | `apps/backend/app/engine/j11_stage_c.py:210,216` (wraps `freeze_attempt_identity`) |
| ScannerRun / ScannerResult / SectorScoreRow / ThemeScoreRow / ForwardReturn (Layer 2 derived state, underlying several Data Contract rows) | OK — deleted, not recomputed; no serving-path file touched | `apps/backend/app/engine/data_manager.py:2244-2321` |
| Next-session manifest (CONTENT + FREEZE/INTEGRITY blocks) | OK — untouched; Stage C explicitly excludes manifest mutation (ruling C8/AG-12), confirmed by `next_session_manifests` row-count/fingerprint invariant in the mutation-accounting evidence | `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json` |
| Regime label, Market phase, Breadth, Sector/theme scores, Stock scores, Evidence ledger, Coverage, Run summary (all "existing engine module, unchanged" per blueprint) | OK — none of `scanner.py`, `forward_testing.py`, `research.py`, or any `GET /api/*` route file appears in the diff (verified via targeted `git diff --stat` against those exact paths) | n/a — confirmed absent from diff |

**Nuance carried forward (not a violation):** per the coordinator's brief and the blueprint's own iter-13
implication, the 11 incident dates now legitimately hold zero `scanner_runs` and zero derived children
until Stage D regenerates them. No new code path fabricates a substitute value for those dates — no
serving/API file was touched this iteration, so any surface reading one of those dates will simply hit
its existing "missing run" handling, unchanged. This is the intended mid-repair state (AG-17), not a
coherence defect.

## Information Architecture check

No new page, route, or feature. `apps/frontend/` does not appear anywhere in the diff (confirmed via
`git diff --stat` scoped to that path — zero output). The blueprint's nav skeleton and feature-home table
are unaffected.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change this iteration) | OK | `apps/frontend/` absent from diff; `reports/phase-goal-market-compass-iter-13-ui-surface-map.md` confirms no surface opened |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None beyond what is already tracked by the blueprint's own iter-11/iter-12 running notes (DDL residual
  acceptance, etc.) — none of that is reopened or affected by this iteration.
- Scope discipline held: TC-16's forbidden-file list (`scanner.py`, `forward_testing.py`, `research.py`,
  `j11_schema_migration.py`, `models.py`, any `apps/frontend/` file) is confirmed absent from the diff by
  direct `git diff --stat` check, not merely by trusting the spec's own claim.
