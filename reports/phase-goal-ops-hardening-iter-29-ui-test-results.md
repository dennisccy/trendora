# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-29-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-29-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-29-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-29-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-29-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-29-evidence/J-09-verify.png |
| UT-J-06 | Pages load only what they need | smoke | P1 | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) render within budget; `/evidence` renders every claim's expectations panel with zero MemoryError/ASGI-exception lines | All 11 pages loaded HTTP 200 with correct content; `/evidence` rendered all 7 claim cards, every one with a fully-populated drawdown-expectations table (no `unavailable` notes anywhere); `logs/backend.log` showed 0 MemoryError / "Exception in ASGI application" / 500 lines across the whole 136-request sweep window; `GET /api/evidence` measured 0.010–0.047s, well within the ≤3s budget, no regression from prior `perf-budgets.md` entries (0.006–0.016s range) | PASS | `reports/qa/goal-ops-hardening-iter-29-evidence/J-06-evidence-page.png` |
| UT-J-07 | Heavy aggregates never take the service down | smoke | P1 | (Scoped this iteration to: live `/evidence` load + a small single-day backfill exercising the ingest-finalize drawdown-expectations warm loop.) `/evidence` loads live with zero MemoryError; the backfill's `aggregates_refreshed` includes `drawdown_expectations` with zero MemoryError from that loop; `GET /api/health` stays responsive (HTTP 200, no hang) throughout | Live `/evidence` load: 7/7 claims rendered, 0 MemoryError. Backfill of `2022-04-12` (a fresh, previously-unsnapshotted trading day, not on the session's consumed-race-dates list) ran to completion in 447s (started 2026-07-28T23:59:40Z, finished 2026-07-29T00:07:07Z); persisted run record's `aggregates_refreshed` = `["latest_snapshot","coverage","membership_timeline","market_phase","forward_aggregates","research_hot_keys","drawdown_expectations"]`; `/data`'s job-history panel independently confirmed the same list verbatim ("Refreshed: ... drawdown expectations"); `logs/backend.log` showed 0 MemoryError / 500 lines across the full 1,109-request window (all 200s); `GET /api/health` polled every ~15s throughout stayed HTTP 200 (never hung/timed out; latency ranged 0.09–1.47s under load — the process was actively computing, 60.8% CPU, never wedged) | PASS | `reports/qa/goal-ops-hardening-iter-29-evidence/J-07-backfill-complete.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

