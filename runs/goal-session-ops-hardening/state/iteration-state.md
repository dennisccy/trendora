# Iteration State — ops-hardening

**After iteration:** 32 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-03 J-04 J-05 J-08 J-09) · 2 partial (J-06 J-07) · 0 failing · 0 unknown — 8 total

## Active blockers

- **dev, FIRST — J-06, settle the launcher BEFORE measuring:** `start-frontend.sh:28` execs `npx next dev`,
  the script J-06 step 1 calls "prod mode", so a TTI sweep measures dev compilation. Make it `next build`+
  `next start` or amend goal.md; THEN sweep 11 pages → `perf-budgets.md` + step 3's on-load audit = J-06 done.
- **dev, SECOND — J-07's last two steps:** record `GET /api/health` LATENCY (not just its 200 rate) through a
  live warm and say if it is in budget; run step 4's induced-pressure drill (tight cap, throwaway process —
  warm aborts honestly while the SAME process keeps serving); deferred since iter-14.
- **dev, carried AG-8 findings, all minor, none firing today:** `warmup.py:194` (+ the unmade badge decision
  after a permanently failed warm-up); `prices.py:141`, now load-bearing since it sits on the ingest-finalize
  path J-07 step 1 calls "the warm"; iter-31/e Factor-Lab residual.
- **framework/human, 4th flag:** `merge_ui_test_results.py` `_ROW_RE` matches only `UT-` and can drop a
  headline FAIL — did not misfire this run (verified), but fix before any achievement run. `J-07.json` now
  asserts the literal `n=8869`, which will break on the next backfill.
- **owner, non-blocking:** `GET /api/health` 0.127787s vs its ≤0.1s budget — until amended, rescoped, or an
  honest WARN, J-06/J-07 step 2 cannot both read true. Ride-alongs: no `[NEW]` demo step; J-07 shot cropped.

## Last 2 verdicts

- iter 32: CONTINUE — `stock_obs` bounded for real (981→170 MB live, byte-identical payload, zero
  MemoryError); AG-8 finding iter-29/c CLOSED; J-07 still partial on its own steps 2 and 4.
- iter 31: CONTINUE — Factor Lab crash fixed, but the fix was a 2.63x constant factor, not a bound.

## Do not redo

- **`stock_obs` is bounded** — `stock_obs.append` gone from `compute_forward_aggregates`; the one left
  (`forward_testing.py:2097`) is `compute_run_scorecard`'s own, spec-sanctioned. Do not reopen.
- **J-07 step 3 DONE** — VmPeak 2,691,600 kB / 57.2% margin, `reports/perf-budgets.md:4023-4098`; extend it.
- **Byte-identity proven at live scale** (SHA-256, 771,129 obs) and its oracle repaired — do not re-verify.
- **Factor Lab crash stays FIXED**; its stray unprefixed `?all=true` 404 has no call site in `apps/frontend`.
- **`run_rows` (`forward_testing.py:1195`) is a WATCH ITEM (iter-32/f), not a blocker** — leave it.
- **AG-10 host-guard caps intact** — `scripts/` and `project-extensions/` zero diff; never weaken.
