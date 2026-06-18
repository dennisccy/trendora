# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## Mode

LEAN goal-mode iteration — **live re-verification + closure repair**, NO backend rework.
This is the iter-33 evaluator's prescribed next step. The backend (engine `universe_resolver.py`,
`data_manager` coverage/diagnostic/timeline derivations, `forward_symbols_for_run`,
`methodology._universe_selection`) was built byte-correct in iter-33 and is **NOT touched here**.

## Backend diff is EMPTY (precondition confirmed)

```
$ git diff --stat HEAD -- apps/backend/app
   (no output — backend source byte-unchanged)
$ git diff --name-only HEAD -- apps/backend/
   (no output — no backend source AND no backend test-file edits)
```

The only acceptable backend touch was none, and none was made. The iter-33 suite reconciliation
(the `macro` shape guard, open_item `iter32-stale-data-overview-shape`) was already applied in iter-33;
this iteration only **confirms** the suite flushes `0 failed`, it does not edit tests.

## What Was Built

Only the OPTIONAL, frontend-only render fold-in that closes the iter-33 coherence Part-C WARN
(the backend `methodology._universe_selection` already returns three per-date fields that the frontend
interface silently dropped):

- **Widened the `UniverseSelection` TypeScript interface** (`apps/frontend/lib/api.ts`) to declare the
  three fields the backend already serves on `GET /api/methodology`:
  - `candidate_pool_size: number`
  - `per_date_rule: string`
  - `per_date_min_history_bars: number`
- **Rendered the J-93 per-date membership rule prose** on the `/methodology` Universe Selection section
  (`apps/frontend/app/methodology/page.tsx`): a new "Per-date membership rule" block (separated by a
  `border-t border-border` divider, with an "As-of" `Badge`) showing the `per_date_rule` prose, the
  `candidate_pool_size` as the full candidate-pool denominator, and `per_date_min_history_bars` as the
  min-history bar count. Added `data-testid`s for QA: `universe-per-date-rule`,
  `universe-candidate-pool-size`, `universe-per-date-min-history-bars`.

**Re-format only** — every value is read verbatim from the existing `GET /api/methodology` payload.
NO new value, NO new computation, NO new endpoint, NO new date state. Design-system tokens only
(`text-text-muted`, `text-text-faint`, `text-text`, `border-border`, `num`, the existing `Badge`
component) — no raw `<div>` soup, no arbitrary values.

### Verified the backend already serves the three fields (in-process, no live server needed)

```
$ .venv/bin/python -c "from app.config import get_config; from app.engine.methodology import build_catalog; ..."
universe_selection present: True
candidate_pool_size: 122
per_date_min_history_bars: 200
per_date_rule len: 444
per_date_rule head: As of any date D the scored membership is this candidate pool screened — from bars dated on or before D only — on price ...
```

So the frontend renders real values, not `undefined`.

## Files Changed

- `apps/frontend/lib/api.ts` -- widened the `UniverseSelection` interface with the three additive
  per-date display fields (`candidate_pool_size`, `per_date_rule`, `per_date_min_history_bars`) + doc comment.
- `apps/frontend/app/methodology/page.tsx` -- added the "Per-date membership rule" render block to the
  `UniverseSelectionCard` (reads the three fields verbatim from the API payload).

No other frontend file constructs a `UniverseSelection` literal (grep confirmed), so widening the
interface with required fields breaks no other consumer.

## Tests Run

- **Frontend type check:** `cd apps/frontend && npx tsc --noEmit` → **EXIT 0** (clean).
- **Targeted backend smoke (sanity, not the gate):** `cd apps/backend && .venv/bin/python -m pytest
  tests/test_api_methodology.py tests/test_methodology.py -q` → **20 passed in 3.32s**.
- **FULL backend pytest suite:** launched **nohup-async** (backend is ~34 min; subagent cannot finish it
  within the Bash cap — per MEMORY.md) to
  `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-test.log`, terminated
  with a `PYTEST_EXIT=<code>` flush line. The backend source is byte-unchanged, so the iter-33-reconciled
  suite is the standing gate. **The pump must gate the GOAL_ACHIEVED candidacy on the flushed
  `0 failed, EXIT 0` line — do NOT block the evaluator on the in-flight stream** (iter-11 / iter-29 lesson).

## Browser-QA scope (the PRIMARY objective — NOT the dev step)

The bulk of this iteration is the browser-qa-agent's job against the LIVE environment
(`:3835` frontend + `:8835` backend + `:9222` Chrome DevTools — confirm all three reachable BEFORE scoring;
backend needs `CORS_ORIGINS` incl. `:3835`; manage dev servers by port, never broad `pkill`). It must
WRITE `reports/phase-goal-...-iter-34-ui-test-results.md` (the artifact whose absence drove the iter-33
CLOSURE-FAIL) with genuine live evidence:

- **J-93** — TWO byte-DISTINCT `/stocks` frames across the early→full as-of step (md5sum the evidence dir
  FIRST; row counts MUST differ; early date honestly empty/small, never padded). Reconcile the
  resolved-latest count against the resolver's stated behaviour — do NOT accept a stale 122/122.
- **J-94** — `/data` per-date coverage-diagnostic panel scrolled into the viewport with rendered admitted +
  excluded-by-reason counts (below-history / below-price / below-ADV), NOT an empty skeleton.
- **J-96** — `/data` membership-timeline panel scrolled into the viewport: step function + entries/exits +
  excluded-by-reason counts, with the THREE honesty labels visible (pool-survivorship caveat, warm-up
  boundary, universe-relative breadth caveat).
- **J-95** — confirm-gated backward-history extension control + survivorship label RENDER ONLY (do NOT
  execute a live rebuild/backward-history fetch — ~11h and clears the snapshot layer per MEMORY.md; the
  real fetch stays honest `blocked-NA`).
- **Required-still-passing live smoke:** J-06, J-18 (CRITICAL: 0 `<input type=date>`, no second date state),
  J-07 (CRITICAL: Risk-Off date → zero Actionable), J-87, J-88; J-89/J-90/J-91/J-92, J-08/J-36/J-37/J-39/J-85
  carried.
- **Fold-in verification:** `/methodology` Universe Selection now shows the per-date rule prose
  (`data-testid="universe-per-date-rule"`) with candidate-pool denominator and min-history bars.

Evidence hygiene (mandatory): md5sum the evidence dir FIRST; one capture per claimed surface; scroll
below-the-fold `/data` panels explicitly into the viewport; resolve control buttons by `aria-label`, never
visible `text()` (nested-span labels); VIEW the pixels of every cited frame.

## Known Issues

- The **live `:8835`/`:3835`/`:9222` environment was NOT up during the dev step** (a `curl
  http://localhost:8835/api/methodology` returned no JSON). The dev step does not require a live server —
  the backend payload was verified in-process via the venv. Bringing up the live environment is the
  browser-QA precondition (iter-33's env was down, which is the root cause J-93/J-94/J-96 sit at `partial`).
  Per the iter-17/25/30 lesson, a Chrome ECONNREFUSED hard-SKIP would leave the targets stuck
  `partial`/`unknown` — the env must be confirmed reachable before scoring.
- **J-95 real backward-history fetch** + the **true point-in-time index-constituent feed** stay honestly
  `blocked-NA` (data-walled, non-vetoing per `docs/goal.md`); only the confirm-gated control + survivorship
  label RENDER is in scope to verify.
- **J-22 / J-23 / J-24** stay `blocked-NA` (data-walled, non-vetoing), unchanged.
- The full backend suite was still in flight at handoff time (launched nohup-async). Its flushed
  `0 failed, EXIT 0` line is the GOAL_ACHIEVED gate, to be read off the log by the pump — not blocking the
  evaluator.
