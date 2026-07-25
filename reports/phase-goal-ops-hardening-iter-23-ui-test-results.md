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
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-23-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-23-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-23-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-23-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | journey | P1 | All 11 named pages load with real, correct content (no blank/frozen/error frame); each `J-06.json` expect-text present | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) loaded live via Chrome MCP; every golden-script expect-text confirmed present verbatim in the live DOM, including the two iter-23-reverified values (`$304.89` on `/stocks/AAPL`, `"Setup & Pattern event study"` heading on `/research/event-study`) | PASS | `reports/qa/goal-ops-hardening-iter-23-evidence/J-06-backtest-fullpage.png`, `J-06-research-event-study-fullpage.png` |
| UT-J-07 | Heavy aggregates never take the service down | journey | P1 | While a background forward-aggregate compute runs, `/api/health` and `/api/backtest` keep answering HTTP 200 with truthful readiness, no wedge; `VmPeak` stays under the memory cap; a memory-pressure abort stays honest and non-wedging | Live-triggered one background compute (same trigger as UT-J-08, see below). Server-side timing + before/after health checks: HTTP 200 throughout, `readiness: "ready"` throughout (confirmed both via `/api/health` JSON and the top-bar badge screenshot), `VmPeak` flat at 4,974,536 kB before AND after (zero measured growth). Step 4 (induced memory-pressure abort) was NOT re-triggered this iteration — reused iter-22's already-disclosed evidence per the binding "no new TC-13/TC-14-scale trigger" instruction. See Notes for full figures and disclosed scope limits | PASS | `reports/qa/goal-ops-hardening-iter-23-evidence/J-08-refreshing-2026-07-08-domtext.md` (shared trigger evidence); see Notes |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | journey | P1 | Latest `/backtest` serves stored evidence directly; viewing a not-yet-complete historical date serves a labeled last-good OLDER version with a "refreshing" indicator within budget; after the background compute finishes, reloading serves the date's own fresh evidence with the banner gone | Latest (`2026-07-22`): full evidence rendered directly, no banner (screenshotted). `?asof=2026-07-08` (3/5 horizons cached at the current dataset_version, confirmed read-only beforehand — genuinely incomplete): first load returned in 168.97 ms / 569.95 ms server-side (both requests, well under the 1.5 s steady budget) and showed `"Refreshing — showing the last complete evidence ... evidence as of 2026-07-08, generated 2026-07-24 16:54:54"` — a genuinely older COMPLETE version, not the incomplete current-version rows, correctly never mixing versions. 26.80 s later (horizon 60 committed, confirmed via DB), reloading the same URL showed `"Forward-tested evidence (expanding window ≤ 2026-07-08)"` with the word "Refreshing" absent anywhere on the page — the date's own fresh evidence, banner gone | PASS | `reports/qa/goal-ops-hardening-iter-23-evidence/J-08-refreshing-2026-07-08-viewport.png` + `-domtext.md`, `J-08-ready-after-warm-2026-07-08.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-25

