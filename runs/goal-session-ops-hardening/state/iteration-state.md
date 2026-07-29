# Iteration State — ops-hardening

**After iteration:** 31 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-03 J-04 J-05 J-08 J-09) · 2 partial (J-06 J-07) · 0 failing · 0 unknown — 8 total

## Active blockers

- **dev, FIRST (deferred 3x):** `stock_obs` at `forward_testing.py:988` is still an unbounded in-memory list
  inside `compute_forward_aggregates` — J-07's own named producer, so J-07's acceptance clause stays
  contradicted. Bounding it means deliberately re-pinning `_attribution_slices`'s frozen, test-asserted
  `(stock_obs, cfg)` signature. Also record the warm's VmPeak + margin in `perf-budgets.md` (J-07 step 3).
- **dev, SECOND (new, blocks J-06's last step):** `scripts/start-frontend.sh:28` execs `npx next dev` — the
  script J-06 step 1 names as its "prod mode" launcher. Dev mode compiles on demand, so the 11-page
  time-to-interactive sweep yields no real numbers until this is a built server (or the goal is amended);
  then run the sweep and write the numbers into `perf-budgets.md`, untouched this iteration.
- **dev, carried:** a stray `GET /research/factor-lab?all=true` (no `/api` prefix) 404s and puts a red
  "1 error" badge on an otherwise clean Factor Lab page; `warmup.py:194` boot warm-up; `prices.py:141`
  whole-table `daily_prices` prefill; decide what the badge says after a permanently failed warm-up.
- **framework:** `merge_ui_test_results.py` `_ROW_RE` matches only `UT-` and can drop a FAIL headline (fix
  before any achievement run); J-03/J-04/J-07 shared one screenshot again (11th recurrence).
- **human/owner, non-blocking:** `GET /api/health` 0.127787s vs its ≤0.1s budget — until amended or rescoped,
  J-06 step 2 and J-07 step 2 can never both read true. No agent fix exists.

## Last 2 verdicts

- iter 31: CONTINUE — Factor Lab crash fixed (0 MemoryError after boot 132546, 23 requests all 200), but
  J-06/J-07 stay partial and 4 AG-8 findings are open.
- iter 30: CONTINUE — the forward-aggregate warm ran clean, but its fix was headroom not a bound.

## Do not redo

- **Factor Lab all-factors crash is FIXED** (`research.py` compact `(core_records, pools)` encoding +
  `factor_lab_all_cached` single-flight guard). Residual scale limit = record iter-31/e, not a re-fix.
- **`J-06.json` replay artifact gap CLOSED** — `...iter-31-j06-ridealong-replay-results.md` (UT-J-06 PASS).
- **`_factor_observations`/`_runs_with_fr`/`_fr_slice_map` byte-frozen** — iter-29's AG-8 fix is untouched.
- **`perf-budgets.md`'s "Iteration 30" section exists** — extend it, do not rewrite it.
- **AG-10 host-guard caps intact** — `scripts/` and `project-extensions/` zero diff; never weaken.
