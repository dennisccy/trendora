# Iteration State — ops-hardening

**After iteration:** 76 · **Date:** 2026-08-13 · **Verdict:** ESCALATE

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) · 0 failing · 0 unknown — 8 total; all re-verified this round with their own evidence (merged browser-QA PASS 8/8, 0 skipped).

## Active blockers

- **STRUCTURAL, dev-owned, this round's headline:** the SPEED-9 evidence backstop at
  `scripts/automation/run-goal.sh:2509-2539` demotes EVERY `lean` spec to `evidence` while all Target
  journeys are `passing`, so no lean round can staff a developer — iters 75 and 76 both ran an empty
  diff against specs ordering real work. **Next spec MUST say `**Depth:** full`** (backstop is
  guarded by `DEPTH == "lean"` and never touches full).
- dev: QA frontend intermittently serves unstyled pages (iter-72/c, `scripts/start-frontend.sh`) —
  quiet two rounds, still un-root-caused. Strengthened `journey-scripts/J-07.json`+`J-09.json` have
  never been replayed; J-07 step 4 asserts text "1d" because the
  `data-testid="scorecard-row-<horizon>d"` hook in `apps/frontend/app/backtest/page.tsx` is missing.
- dev (small, carried): stray zero-byte `=` at repo root (5th round); `state/goldens-regen-pending` still lists J-05..J-09 though all pass; TC-7 `/data` honest-fallback capture unfilled (or drop the hook at `apps/backend/app/api/data.py:119`); walkthrough recorder saves byte-identical before/after frames (`reports/demo/…-iter-76/` step-04≡step-07, step-05≡step-06); badge wrap hides "Ready" at 1280px during a compute window; `stale_for_s` still unrendered (iter-72/f).
- human (owner): (a) finish now with 138 minor housekeeping notes as a to-do list, or clear them
  first? (b) 2 s health ceiling during long jobs or short jobs only? (c) B-1107 concurrency cap?
  (d) sign-off to edit `scripts/automation/browser-qa-phase.sh`; (e) cost — 16th over-budget round.

## Last 2 verdicts

- iter 76: ESCALATE — all 8 pass with fresh evidence, but the DoD went unexecuted a 2nd round; full
  depth is the only agent-owned way to restore the developer lane.
- iter 75: CONTINUE — all 8 verified fresh, but the spec's own DoD went unexecuted (evidence path).

## Do not redo

- J-07 step 3 VmPeak/margin (4,724.0 MB vs 8,192 MB = 42.33%, iter-74) + step 4 induced-pressure drill (2026-07-31, `reports/perf-budgets.md`) — carried, valid while the diff stays empty.
- Regenerating the J-05..J-09 goldens — never the right remedy (iter-73); CLEAR the queue instead.
- Removing the `data_overview_endpoint` fault hook — settled iter-76: capture the evidence.
- Re-verifying J-08/J-09 live acceptance — done fresh at iters 75 and 76, database-exact.
- `app.engine.readiness` cache/staleness and `compute_forward_aggregates` — frozen.
- iter-33/g Regime Lab — deferred a 43rd time; needs owner direction.
