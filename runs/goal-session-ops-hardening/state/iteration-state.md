# Iteration State — ops-hardening

**After iteration:** 54 · **Date:** 2026-08-09 · **Verdict:** ESCALATE

## Journeys

5 passing (J-01 J-03 J-04 J-08 J-09) · 3 partial (J-05 J-06 J-07) · 0 failing — 8 total

## Active blockers

- **J-05 step 4 / J-07 step 2 (dev):** 6 connection-level `/api/health` non-answers + 53 polls >2.0s
  across 1,821 — **all inside `forward_aggregates_warm`**, zero in the phase this round fixed.
  `reports/qa/goal-ops-hardening-iter-54-evidence/tc4-drill-out/health-polls.csv`, Addendum 17.
- **Honest-status hole (dev):** run 351's warm aborted at horizon 20 (`logs/backend.log:233042`,
  horizon 60 never ran) yet `data_provider_runs.id=351` stores `status='ok'` with `forward_aggregates`
  still listed in `aggregates_refreshed`. Fix the record before the performance.
- **J-06 step 2 (dev):** `/api/runs` 3.2-7.5s, `/api/data/availability` 15.1-21.2s vs ≤1.5s; `/api/health`
  0.18-1.213s vs ≤0.1s — DB grew to 8.37 GB / 2,937 `scanner_runs` rows. Addendum 18 WARN.
- **Verification debt (dev):** `journey-scripts/J-05.json` skipped a 2nd round (TC-7); J-04.json and
  J-07.json authored but never replayed; J-04.json step 2 races the boot — needs a `wait_for`.
- **Depth mismatch (engine):** spec said `Depth: full`, `iter-54/depth-dispatched` = `lean` → no audit,
  no QA report. ESCALATE pins iter-55 to full.
- **Owner, open since iter-50/51:** (a) may heavy compute move off-process? (b) does the 1,200s finalize-tail budget bind while serving traffic, or only when idle?

## Last 2 verdicts

- iter 54: ESCALATE — every code item delivered and verified in source, but zero journey movement, and a
  lean-dispatched round hid a mid-horizon warm abort that no lane reported.
- iter 53: CONTINUE — J-04 moved to passing; first scoreboard movement since iter-45.

## Do not redo

- **B1 off-by-one FIXED** — `market_phase.py:230` fetches `lookback_days + 1`, `:572`
  `recovery_trailing_ma_days + 1`; byte-identity comment corrected; treated-vs-UNTREATED oracle test ships.
- **B3 FIXED** — `market_phase.py:1197` `_benchmark_close_on_or_before` returns `close_on(...)`.
- **B2 FIXED** — fault probe removed from `universe_resolver.py`, now at `data_manager.py:4130-4139`.
- **T2 FIXED** (`test_universe_resolver.py:340` restored) · **T5 done** (76/76, 3862.87s) ·
  **`per_date_coverage_warm` FIXED** — zero non-answers there across 1,822 polls (was 1); do not re-treat.
- **J-04 product behaviour is proven** (boot/badge/crash/interrupted rows, iter-53 + iter-54 replay);
  AG-9 (`provider='seed'`, runs 346-351) and AG-10 (5 frozen paths clean) re-verified at source iter-54.
