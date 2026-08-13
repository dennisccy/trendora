# UI Test Results (merged)

**Date:** 2026-08-13
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression re-confirm | P1 | All 3 backfill submissions (full May range, weekend-only, May re-run) resolve with correct `dates_total`/exclusion breakdowns, zero-work rendered as an explanatory neutral state (never green success), persisted across reload, and a spot-checked scanner run's leaderboard renders stored values | All 3 submissions resolved exactly as expected; zero-work note confirmed neutrally styled; Run history persisted all 3 runs after reload; `/scanner-runs/748` (2026-05-29) rendered a populated, stored leaderboard; `/scanner-runs` confirmed 2026-05-04/05-15 present and 2026-05-25 (Memorial Day) absent | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-01-result.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-07-27, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/J-08-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | target | P1 | Readiness badge stays Ready/responsive and the Forward-test scorecard serves real content while heavy background compute runs; service never freezes | Badge `data-state="ready"` confirmed on `/`; `/backtest` scorecard renders (honest empty state at Latest, populated 1d row at historical as-of 2026-07-31); a real background-compute window (09:01:19–09:09:03 UTC, 463.7s) ran to completion WHILE this session concurrently submitted and completed 3 live backfill jobs — service stayed fully responsive throughout; 10/10 steady-state `GET /api/health` polls 0.022–0.032s (well under the ≤0.1s budget) | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-07-result.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | target | P1 | Badge shows "Ready" + a background-compute detail simultaneously during a window; `/data` panel mirrors the same window with elapsed/horizons, then transitions to idle + a real measured last-outcome duration; process-lifetime scope disclosed | Observed a full live active→idle lifecycle: badge showed "Ready" + "background compute running (1)" simultaneously; `/data`'s `background-compute-active-row` showed as-of 2026-07-31, elapsed 2m40s, horizons 1/5, dataset r2988-f6601195, matching `GET /api/health` exactly; after completion, panel correctly rendered the `background-compute-idle` sub-state (not the `background-compute-unknown` backend-unreachable branch) with `LAST OUTCOME: Completed / as-of 2026-07-31 / 7m 44s` — exact match to the API's duration_ms 463745; verbatim "Since the last backend restart — this history is process-lifetime only, never persisted" disclosure confirmed | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-09-result.png |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-13

