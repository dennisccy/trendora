# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 7/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-43-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-43-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-43-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-43-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-43-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-43-evidence/J-09-verify.png |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly | regression | P1 | Backfill honors the request; scanner-runs renders promptly from storage; Run history "Refreshed:" eventually lists forward aggregates; badge never drops | Job (id 258) started 2026-07-31T13:10:59 UTC, reached terminal `status:"ok"` at 13:16:25 UTC (325.4s); `/scanner-runs/1882` rendered "as of 2005-04-12" + 152-row leaderboard instantly; badge stayed `data-state="ready"` throughout; final "Refreshed:" text = "coverage, membership timeline, forward aggregates, research hot keys, drawdown expectations" | PASS | `reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-05-result.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | All 3 fast anchors render; health stays 200 within ≤2s BCW budget throughout a heavy warm; badge never drops to unavailable; `/backtest` never blank | Backend found **fully unreachable** (connection-refused) at session start under a stuck background compute (see critical finding above) — direct contradiction of the acceptance criterion. After recovery: anchors "/" ("Ready") and "/data" (badge Ready) confirmed; "/backtest" anchor text "n=8878" not found (page rendered real evidence figures, no error/stale banner — likely benign golden drift). Steps 4-8 (dedicated wide-range trigger + 5re+ min timed curl loop + second-tab `/backtest`) not independently executed this pass — time was spent recovering the stuck backend and completing UT-J-05; starting a second concurrent heavy job was deliberately avoided per the dev handoff's own documented confound risk. Closest available substitute: 16 health polls (5s interval, 83s span) taken concurrently with UT-J-05's job 258 — 16/16 HTTP 200, latency 0.118-1.678s, mean 0.309s, 16/16 within the ≤2s BCW ceiling for that window (a lighter, zero-new-snapshot case — not a substitute for the dev's own 272-sample genuinely-heavy measurement, which found 63.6% over 2s) | FAIL | `reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-07-fail.png` |

## Failed Tests

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** FAIL
**Failure:** Backend found **fully unreachable** (connection-refused) at session start under a stuck background compute (see critical finding above) — direct contradiction of the acceptance criterion. After recovery: anchors "/" ("Ready") and "/data" (badge Ready) confirmed; "/backtest" anchor text "n=8878" not found (page rendered real evidence figures, no error/stale banner — likely benign golden drift). Steps 4-8 (dedicated wide-range trigger + 5re+ min timed curl loop + second-tab `/backtest`) not independently executed this pass — time was spent recovering the stuck backend and completing UT-J-05; starting a second concurrent heavy job was deliberately avoided per the dev handoff's own documented confound risk. Closest available substitute: 16 health polls (5s interval, 83s span) taken concurrently with UT-J-05's job 258 — 16/16 HTTP 200, latency 0.118-1.678s, mean 0.309s, 16/16 within the ≤2s BCW ceiling for that window (a lighter, zero-new-snapshot case — not a substitute for the dev's own 272-sample genuinely-heavy measurement, which found 63.6% over 2s)
**Evidence:** ``reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-07-fail.png``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

