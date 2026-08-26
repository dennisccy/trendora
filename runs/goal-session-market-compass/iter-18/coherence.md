# Iteration 18 — Coherence Audit

**Iteration:** goal-market-compass-iter-18
**Date:** 2026-08-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

No registered Data Contract row is touched, read, or recomputed by this iteration's diff. This
iteration is backend-internal maintenance/safety tooling only (J-11 boundary table creation + live
arm + boot-path guard closure); it does not create a new endpoint, does not create a new displayed
value, and does not touch any file behind an existing Data Contract row.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| (none of the blueprint's registered rows are touched) | OK | confirmed via file-list check below |

Confirmation performed (not merely asserted): `git status --porcelain -uall` for the full changed-file
set (tracked + untracked) grepped against `app/api/`, `scoring.py`, `sectors.py`, `compass.py` — zero
matches, satisfying the iteration spec's own TC-17. None of `dashboard.py`, `market-phase` route,
`themes.py`, `stocks.py`, `evidence.py`, `data_manager.py`/`data.py` route, `runs.py`, or any readiness
module appears in the changed-file set either — every Data Contract row's sole computing
module/endpoint is provably untouched, not merely unmentioned.

New internal state introduced this iteration — `j11_preboot_guard.evaluate_boundary_for_date_fail_closed`
(`apps/backend/app/engine/j11_preboot_guard.py:151-176`), `j11_maintenance.capture_full_table_sweep` /
`diff_full_table_sweeps` (`apps/backend/app/engine/j11_maintenance.py:54-128`), and the two new scripts
`apps/backend/scripts/run_j11_maintenance_boundary_table_create.py` and
`apps/backend/scripts/run_j11_iter18_full_table_sweep.py` — was checked against Part A's "new
NOT-yet-in-contract value" test (rule A4/A5) and found not to apply at all, because none of it is ever
displayed: `MaintenanceBoundary` state is never routed through any API route or UI component (verified:
no route file changed), so it is not a "new displayed value" requiring registration, exactly as the
iteration spec's own "Data-contract additions: None" / "Blueprint conformance" sections claim. This
audit independently confirms that self-assessment rather than taking it on faith — see file-list check
above.

`evaluate_boundary_for_date_fail_closed` is a pure delegating wrapper (`return
evaluate_boundary_for_date(session, one_date)` inside a try/except) around the pre-existing canonical
guard function — not a second implementation of boundary evaluation. Both new call sites
(`warmup.py:363` in `_run_warmup`'s cadence loop, `forward_testing.py:562` in `_backfill`'s cadence
loop) call this exact same wrapper object; neither hand-rolls its own boundary check. No duplicate
computation.

## Information Architecture check

No new page, route, or feature exists this iteration to check. Confirmed independently (not just from
the spec's own claim): `git status --porcelain | grep -i frontend` returns zero matches — no file under
`apps/frontend/` is modified or added. This matches
`reports/phase-goal-market-compass-iter-18-ui-surface-map.md` ("Not mapped this iteration — maintenance
isolation... No surface was opened or inspected") and
`reports/phase-goal-market-compass-iter-18-user-visible-changes.md` ("Nothing was rendered, clicked or
screenshotted this iteration").

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (no new page/route/feature this iteration) | OK | apps/frontend/ — zero files changed (git status) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Two evidence-artifact text corrections landed as riders (TC-14, TC-15), both verified in the diff to
  be scoped exactly as specced, with no application-code or Data Contract impact: (1)
  `runs/goal-market-compass-iter-17/j11-avb-bridge-diagnostic.json:576,589` — the "genuinely
  independent" claim is replaced with the correct algebraic-identity explanation
  (`dollar_b = dollar_a` follows from the `bridge_factor` rescaling by construction); the file's
  `AVB-A` classification field is unchanged. (2)
  `reports/phase-goal-market-compass-iter-17-ui-test-plan.md` — the eleven-date list now distinguishes
  the two genuinely raw-data-damaged dates (2026-08-11, 2026-08-12) from the nine that only had derived
  `scanner_runs` cleared. Both are documentation/evidence corrections, not code or UI, and neither
  interacts with the Data Contract or IA.
- This is a pure infra/safety iteration with no frontend touch and no new registered value — a
  textbook instance of the "no-op" case in this gate's own edge-case rules. Nothing here needs
  tidying by the next iteration.
