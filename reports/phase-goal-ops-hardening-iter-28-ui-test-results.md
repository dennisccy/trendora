# UI Test Results (merged)

**Date:** 2026-07-27
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/9 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-28-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-28-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-28-evidence/J-04-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-28-evidence/J-09-verify.png |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly | happy-path | P1 | Single-day backfill (2018-02-15) persists snapshot + aggregates; `/scanner-runs` and market phase serve from storage; cold restart serves coverage from storage within budget with no whole-table prefill; `/api/health` stays responsive during ingest | See "J-05 detail" below | PASS | `J-05-scanner-run-2018-02-15.png`, `J-05-cold-data-restart.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 pages in the golden script (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) load and each step's `expect.text` appears | See "J-06 detail" below | PASS | `J-06-dashboard-market-regime.png` |
| UT-J-07 | Heavy aggregates never take the service down | smoke/ux | P1 | `/backtest` latest view loads clean (smoke baseline); stale-coverage notice reads calm/factual, never alarm styling (UX regression guard) | See "J-07 detail" below | PASS | `UT-05-backtest-latest.png`, `UT-02-UT-08-stale-coverage.png` |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | error/regression | P1 | Two concurrent `/backtest` requests for the SAME never-scanned historical date both return 200 with zero ASGI exceptions; an already-scanned historical view renders consistently with what the race established | See "J-08 detail" below | PASS | `UT-06-backtest-2018-03-15.png`, `UT-07-backtest-already-scanned.png` |
| UT-04 (J-05's P3 sub-case) | Coverage panel "not yet computed" state | regression | P3 | Only reachable on a genuinely fresh-install DB with zero `CoverageSnapshot` rows | This session's seeded dev database cannot exhibit this state (confirmed: 1872+ snapshot rows exist) — no fresh-install environment available to point the frontend at | SKIP | none (documented-only, per iter-27's own test plan) |

## Skipped Tests

### UT-04 (J-05's P3 sub-case) — Coverage panel "not yet computed" state

**Verdict:** SKIPPED
**Reason:** This session's seeded dev database cannot exhibit this state (confirmed: 1872+ snapshot rows exist) — no fresh-install environment available to point the frontend at

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-27

