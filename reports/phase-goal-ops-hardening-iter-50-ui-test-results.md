# UI Test Results (merged)

**Date:** 2026-08-06
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 11/14 journeys passed (2 skipped, 1 required-missing, 3 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-50-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-50-evidence/J-03-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-50-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-50-evidence/J-09-verify.png |
| UT-01 | Factor Lab loads without errors | smoke | P1 | Heading + populated all-factors table, real rank-IC/forward-return figures, no console 500s | Page loaded, heading "Research — Factor Lab" present, `factors-table` rendered 11 rows with real rank-IC/decile figures on a warm cache (163ms API call) | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-01-result.png` |
| UT-02 | Historical-day backfill reaches terminal status | happy-path | P1 | Job reaches terminal status ≤20min, scanner-runs row + leaderboard render | Backfill for `2012-01-04` reached `status: "ok"` in 11m16s (21:52:45→22:04:01 UTC), `aggregates_refreshed` included `membership_timeline`; `/api/runs` confirmed the date present (2908 rows). The "within ~30 seconds" aggregates-line sub-claim did NOT hold (see note) | PASS (with note) | API responses (see Notes); no final UI screenshot of the scanner-runs leaderboard was captured — see Notes |
| UT-03 | Factor Lab survives a concurrent finalize-tail warm | error | P1 | Readiness stays `ready` throughout; Factor Lab loads every time; no crash/hang | **Backend became fully unresponsive to `GET /api/health` for 12m03s+ (confirmed continuously, still ongoing when this report was written) during a second ingest job's finalize tail. The browser's readiness badge stayed stuck on "Checking backend…" (never `ready`, never even `unavailable`) for 17m+ straight. Process never crashed (still running, CPU-busy, `futex_do_wait`) but the service was not serving ANY request, including `/api/health`.** | **FAIL** | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-03-fail.png` |
| UT-04 | Job form blocks incomplete date range | validation | P3 | Start button stays disabled when start date is empty | Start-date field emptied, end-date set to `2012-01-06`, Start button `disabled=true` confirmed via DOM | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-04-result.png` |
| UT-05 | Evidence drawdown-expectations panel still renders | regression | P2 | Table renders real percentage/numeric rows, not the unavailable fallback | `evidence-expectations-table` rendered 5 rows with real figures (e.g. "-7.42% (p90 -3.65%) n=362642") for the regime claim card | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-05-result.png` |
| UT-06 | Backtest scorecard still renders | regression | P2 | Scorecard shows real numeric hit-rate/mean-return figures, Leadership cohorts populated | At the default "Latest" as-of, every horizon showed honest NA (n=0) — correct behavior, no elapsed forward window yet, not a defect. Selecting a historical as-of (`2026-04-01`) showed a full real scorecard (hit rate 59.18%, mean +0.26%, populated sector/theme/ticker leadership tables) | PASS (see note) | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-06-result.png` |
| UT-07 | Background-compute panel still renders | regression | P2 | Idle OR populated active-row state, never blank | `background-compute-active-row` rendered with real as-of (`2026-04-01`), elapsed (18.6s), horizons (0/5), dataset version | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-07-result.png` |
| UT-08 | Degraded Factor Lab response reuses empty-state | ux | P3 | N/A (advanced, requires backend restart) | Not attempted — see Skipped section | SKIP | none |
| UT-09 | Cold restart renders coverage within budget | regression | P2 | N/A (advanced, requires backend restart) | Not attempted — see Skipped section | SKIP | none |
| UT-10 | Factor Lab page-load timing measured | ux | P2 | First live measurement recorded; warm load feels responsive (low single-digit seconds) | Warm/cached load: nav 52ms, API call 163ms, table (11 rows) rendered essentially instantly — well within budget. Separately (diagnostic, not part of the formal timing claim), two COLD cache-miss computations of the same endpoint took 780s and 875s (13–14.6 min) — see Notes | PASS (with finding) | timings recorded in Notes / `reports/perf-budgets.md` Addendum 8 |

## Missing Required Journeys

_Required-still-passing journeys named in the iteration spec that were NOT verified this iteration — either no lane (deterministic replay or LLM browser-qa) produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-40 lesson: this is exactly how required journeys shipped with zero evidence while every gate reported clean)._

- `UT-J-04` — no test case executed for J-04 by any lane

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-05` — no test case executed for J-05 by any lane
- `UT-J-06` — no test case executed for J-06 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane

## Failed Tests

### UT-03 — Factor Lab survives a concurrent finalize-tail warm

**Verdict:** FAIL
**Failure:** **Backend became fully unresponsive to `GET /api/health` for 12m03s+ (confirmed continuously, still ongoing when this report was written) during a second ingest job's finalize tail. The browser's readiness badge stayed stuck on "Checking backend…" (never `ready`, never even `unavailable`) for 17m+ straight. Process never crashed (still running, CPU-busy, `futex_do_wait`) but the service was not serving ANY request, including `/api/health`.**
**Evidence:** ``reports/qa/goal-ops-hardening-iter-50-evidence/UT-03-fail.png``

## Skipped Tests

### UT-08 — Degraded Factor Lab response reuses empty-state

**Verdict:** SKIPPED
**Reason:** Not attempted — see Skipped section

### UT-09 — Cold restart renders coverage within budget

**Verdict:** SKIPPED
**Reason:** Not attempted — see Skipped section

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-06


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
