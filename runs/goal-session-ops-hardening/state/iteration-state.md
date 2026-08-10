# Iteration State — ops-hardening

**After iteration:** 55 · **Date:** 2026-08-10 · **Verdict:** CONTINUE

## Journeys

5 passing (J-01 J-03 J-04 J-08 J-09) · 3 partial (J-05 J-06 J-07) · 0 failing — 8 total

## Active blockers

- **J-05's golden is a live landmine (dev, cheap, DO FIRST).** `journey-scripts/J-05.json` needs a
  0-snapshot trading day; it consumed 2010-11-08 (`scanner_runs.id=2940`) and was not rotated, so the
  next replay FAILS for a fixture reason, not a product one. Verified swaps: 2010-11-10/11/12/15/16.
- **The replay lane erases its own results (dev).** A 5-journey run at 02:32 overwrote the 7-row file
  holding this session's only J-05/J-07 rows; `replay-lane/verify-run.log` truncated to 0 bytes.
- **QA reports PASS over a BLOCKED lane (dev, 5th round).** `reports/qa/…-iter-55-qa.md:7,110` cites
  replay rows deleted 6 min earlier; `status.json` blockers omit the BLOCKED lane.
- **J-06's only gap is unprofiled (dev).** `/api/runs` 3.2–7.5s, `/api/data/availability` 15.1–21.2s vs
  a ≤1.5s budget, driven by DB growth to 8.37 GB. Deferred twice; never measured once.
- **Availability ceiling (HUMAN — owner decision (a), open since iter-50).** 11/1,839 non-answers vs
  6/1,821 last round. Addendum 19 proves the per-compute-yield lever exhausted. Do not retry it.
- **Demo recorder broken (dev, ~5 min):** "invalid demo script: step[6] fill requires text" — no walkthrough at all; costs J-04/J-05/J-07 their `[NEW]` captures.

## Last 2 verdicts

- iter 55: CONTINUE — honest-status fix built and verified 3 ways (code, tests, live run 356); no
  journey moved; TC-5 regressed 6→11; audit found the consumed golden + destroyed rows.
- iter 54: ESCALATE — dispatched lean against its own `Depth: full` spec, so no audit ran and the
  horizon-20 warm abort (persisted as a complete refresh) reached the evaluator unreported.

## Do not redo

- **`forward_aggregates` completeness fix DONE + verified** — `data_manager.py:4300` (`_completed ==
  _total` after the loop); escape hatch closed by `config.py:766` `min_length=1`.
- **Intra-chunk GIL yield DONE, byte-identical, and USELESS** — `forward_testing.py:1139`; h10
  438.40s post-fix vs 336–438s pre-fix. Do not extend it.
- **J-04's golden race FIXED** (`J-04.json` step 2 `wait_for`, replayed PASS) and its product behavior
  (boot/badge/crash/interrupted) proven — do not rebuild either.
- **AG-9/AG-10 re-verified** (all runs `provider='seed'`; both git checks empty on all 5 frozen paths;
  `config.yaml:1363-1364` = 8192 / 2) and the **lane-ordering rule held a 3rd round** — keep both.
