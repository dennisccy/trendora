# UI Test Results (merged)

**Date:** 2026-07-25
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-22-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-22-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-22-evidence/J-05-verify.png |
| UT-J-04 | Non-blocking boot with visible status | journey | P1 | While healthy: no crash/unreachable presentation anywhere; persistent backend logfile contains boot events; `/data`'s persisted run-history panel renders past runs with outcome/exclusion detail (non-disruptive steps only — disruptive kill/restart out of scope this pass, see note) | Readiness badge showed `Ready` / `provider: seed` on every page, no "Backend unavailable" text anywhere; `logs/backend.log` contains repeated clean `Started server process` → `Waiting for application startup` → `Application startup complete` → `Uvicorn running` sequences, most recently for the dev's iter-22 restart (PID 807942) with a preceding clean `Shutting down` / `Application shutdown complete` (no abrupt truncation, because that restart was graceful, not a kill); `/data` "Run history" table lists 9 persisted runs from earlier today (2026-07-25 00:41 → 07:16) each with calendar-day / already-snapshotted / non-trading counts and a "Refreshed:" aggregate list, no stuck "running" row | PASS | `reports/qa/goal-ops-hardening-iter-22-evidence/J-04-no-crash-banner.png`, `J-04-data-page-top.png` |
| UT-J-06 | Pages load only what they need | journey | P1 | Every page named in J-06 step 1 loads with real, correct-looking content (no blank/frozen/error frame); precise latency budgets are recorded in `reports/perf-budgets.md` by the developer this iteration, not remeasured here | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) loaded and rendered their expected content with no error/blank state; see per-page detail below | PASS | `reports/qa/goal-ops-hardening-iter-22-evidence/J-04-no-crash-banner.png` (home), `J-04-data-page-top.png` (`/data`) — remaining pages confirmed via DOM-text capture (no separate screenshot; see Notes) |
| UT-J-07 | Heavy aggregates never take the service down | journey | P1 | While a real background forward-aggregate compute (BCW) runs, `GET /api/health` and `GET /api/backtest` keep answering HTTP 200 with truthful `readiness`; no wedge/deadlock; the canonical VmPeak/margin measurement is the developer's, recorded in `reports/perf-budgets.md` | Independently triggered one fresh BCW (see UT-J-08) and polled both endpoints ~1/s for its full duration: **11/11 samples HTTP 200 on both endpoints, `readiness: "ready"` on every sample, zero non-200, zero wedge** — window completed in 28.06 s (well inside the amended 90 s bound), worst `/backtest` sample 7.55 s (inside the amended 8.0 s BCW ceiling), worst `/api/health` sample 0.41 s (inside the amended 2.0 s BCW ceiling) | PASS | `runs/goal-ops-hardening-iter-22/` scratch poll CSV quoted in Notes below (not copied into the evidence dir — raw timing log, not a screenshot); `reports/qa/goal-ops-hardening-iter-22-evidence/J-08-refreshing-2026-07-20.png` and `J-08-ready-after-warm-2026-07-20.png` bracket the same window |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | journey | P1 | `/backtest` at latest serves stored evidence directly (`ready`); viewing a not-yet-computed historical date serves a labeled last-good older version with a visible "refreshing" banner within budget (never a skeleton/blank wait); after the background compute finishes, reloading the same date serves its own fresh stored evidence with the banner gone | Latest view (`2026-07-22`): full evidence rendered directly, no banner. `?asof=2026-07-20` (a date with zero `forward_aggregate_cache` rows at any dataset_version, confirmed read-only beforehand): first load returned in ~88 ms client-side and showed the `refreshing` banner — "This date's own evidence is being computed in the background (started by viewing this page) ... evidence as of 2026-07-17, generated 2026-07-24 00:44:13" — i.e. serving the last-complete OLDER date's stored evidence, not a blank/skeleton wait. 28.06 s later the background compute finished; reloading the same URL now shows "Forward-tested evidence (expanding window ≤ 2026-07-20)" with no banner — the date's own evidence, served from storage | PASS | `reports/qa/goal-ops-hardening-iter-22-evidence/J-08-baseline-latest-ready.png`, `J-08-refreshing-2026-07-20.png`, `J-08-ready-after-warm-2026-07-20.png` (all full-page captures) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-25

