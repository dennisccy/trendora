# Phase goal-market-compass-iter-7 — User-Visible Changes

**Phase:** goal-market-compass-iter-7
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

**Status:** N/A — Backend-only phase (Frontend Present: no)

No user-visible changes. All changes are internal backend implementation.

---

## Why this classification

This iteration (J-10, a bounded backend data-recovery retry) changed exactly three source files, all
backend: `apps/backend/app/engine/j10_recovery.py`, `apps/backend/app/data_providers/yahoo_provider.py`,
and `apps/backend/tests/test_j10_recovery.py` (per `docs/handoffs/goal-market-compass-iter-7-dev.md`'s
"Files Changed" list, corroborated by that handoff's own `git status --short` confirmation). No file
under `apps/frontend/` was touched, and no API route file changed. This matches:
- `runs/goal-market-compass-iter-7/plan.md`: `## Frontend Present` → `no`
- `docs/phases/goal-market-compass-iter-7.md`: `**Frontend Present:** no`, `### Frontend` → "None — J-10
  has no UI surface (goal.md: 'Walkthrough: waived — data-layer repair with no UI surface change of its
  own')", `### New user-facing capability` / `### New information displayed` / `### New user actions` /
  `### UI surface changes` → all "None this iteration"

**Note on a dispatch discrepancy:** the coordinator message that dispatched this report stated
"Frontend Present: yes" and a frontend URL. That line contradicts the plan.md and phase-spec metadata
above (both say `no`), the dev handoff (zero frontend files touched, no route changed), and the
implementation summary's own "Backend-Only Items" section (`reports/phase-goal-market-compass-iter-7-implementation-summary.md`).
Per this agent's standing instructions, plan.md/phase-spec are the authoritative sources for this
determination, not the dispatch line — this report follows them, per the explicit coordinator
instruction not to manufacture UI surfaces that don't exist.

## What Users Can Now Do

None. No new capability is reachable from the UI this iteration.

## What Changed in the Visible UI

Nothing. No frontend file was modified.

## What Old Behavior Changed

None. The new fail-closed adjustment-convention-check gate (`check_adjustment_convention`, J-10 step
2a) ran for real against the live database and returned **`mismatch`** — one of the 20 sampled tickers
(CVX) showed a ~0.865% delta against Yahoo's adjusted close, just over the 0.75% tolerance — so the
gate correctly stopped before writing anything. `daily_prices`, `scanner_runs`, and `data_provider_runs`
are byte-unchanged from their pre-iteration state (re-verified in the dev handoff's Step 5 table, not
just claimed). Nothing a user could notice changed, because nothing did.

## Not Visible Yet

- The convention-check gate (`check_adjustment_convention`) and its supporting `get_adjusted_close`
  capability on `YahooProvider` now exist in the backend, but neither has nor needs a UI surface — both
  run only as part of a one-time incident-recovery script (`run_gated_recovery`), never from a request
  path any page calls.

## Pre-Existing State, Unchanged By This Iteration (context only — not introduced this iteration)

- `GET /api/compass?as_of=2026-08-12` (and `?as_of=2026-08-11`) still returns HTTP 400
  (`"as_of <date> is after the latest data date 2026-08-10"`) — byte-identical to the error returned
  before this iteration ran, per the dev handoff's step 5(f) check. Because the recovery gate correctly
  refused to write (see above), the underlying condition that produces this 400 is unchanged. Any user
  journey depending on those two dates (J-01/J-02/J-03/J-04, per the phase spec) remains unable to load
  them — this is a carried-forward condition from the iter-5 data-loss incident and iteration 6's failed
  Stooq attempt, not something this iteration changed for better or worse.
- This state is reported from the dev handoff's direct, read-only `GET` calls against a transiently
  started backend — **no browser session was opened to confirm it**, and none should be: per
  `docs/goal.md`'s lane gate, verifying J-01–J-04 in a browser against the current, still-incomplete
  dataset is out of scope until J-10's recovery independently passes verification. That re-verification
  is explicitly deferred to iteration 8 regardless of this iteration's own outcome (phase spec
  BACKGROUND/OUT OF SCOPE).
