# UI Test Results (merged)

**Date:** 2026-07-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/7 journeys passed (4 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-18-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-18-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-18-evidence/J-05-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | This iteration's scope is a non-disruptive steady-state check only (no kill/restart — that is TC-10, operator-performed); health 200/ready, badge correct, no new crash lines | Chrome MCP unavailable — no badge/DOM/screenshot evidence obtainable. Non-browser signal only: `GET /api/health` → 200, `readiness:"ready"`, `db_ok:true`; `logs/backend.log` tail shows only clean `INFO` access lines plus new `backtest_timing` instrumentation lines, no crash/traceback | SKIPPED | none — see reason below |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 pages from the existing `J-06.json` golden script (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) render their expected content; spot-check that `/backtest` is byte-identical post-instrumentation | Chrome MCP unavailable — could not navigate to or render any page. Non-browser signal only: raw `GET /backtest` (server-rendered HTML, not client-verified) → HTTP 200, 45684 bytes, 0.46s; `GET /api/backtest` → `evidence_status:"ready"`, `evidence_asof:"2026-07-22"`, 5 horizon keys, `scorecard` present | SKIPPED | none — see reason below |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Spot-check only this iteration (no new UI behavior for J-06/J-07/J-08); full acceptance requires triggering a deep-basis forward-aggregate warm + memory-pressure induction, out of scope for this agent | Chrome MCP unavailable, and the full journey additionally requires a heavy-compute trigger this agent was instructed not to perform (see note above). Non-browser signal only: `GET /api/health` → 200 while idle | SKIPPED | none — see reason below |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | Spot-check that `/backtest` still serves stored evidence correctly; full acceptance requires submitting a live backfill to observe the version-bump/refreshing transition, out of scope for this agent | Chrome MCP unavailable, and the full journey additionally requires an ingest trigger this agent was instructed not to perform (see note above). Non-browser signal only: `GET /api/backtest` → `evidence_status:"ready"` (not `refreshing`, not `not_yet_computed`), `evidence_generated_at:"2026-07-24T02:11:25Z"`, `is_latest:true`; two fresh curl calls each produced a `backtest_timing` log line with `total_ms` ~150-160ms (well under the 1.5s budget at idle, consistent with a stored-value read, not a request-path recompute) | SKIPPED | none — see reason below |

## Skipped Tests

### UT-J-04 — Non-blocking boot with visible status

**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable — no badge/DOM/screenshot evidence obtainable. Non-browser signal only: `GET /api/health` → 200, `readiness:"ready"`, `db_ok:true`; `logs/backend.log` tail shows only clean `INFO` access lines plus new `backtest_timing` instrumentation lines, no crash/traceback

### UT-J-06 — Pages load only what they need

**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable — could not navigate to or render any page. Non-browser signal only: raw `GET /backtest` (server-rendered HTML, not client-verified) → HTTP 200, 45684 bytes, 0.46s; `GET /api/backtest` → `evidence_status:"ready"`, `evidence_asof:"2026-07-22"`, 5 horizon keys, `scorecard` present

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable, and the full journey additionally requires a heavy-compute trigger this agent was instructed not to perform (see note above). Non-browser signal only: `GET /api/health` → 200 while idle

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request

**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable, and the full journey additionally requires an ingest trigger this agent was instructed not to perform (see note above). Non-browser signal only: `GET /api/backtest` → `evidence_status:"ready"` (not `refreshing`, not `not_yet_computed`), `evidence_generated_at:"2026-07-24T02:11:25Z"`, `is_latest:true`; two fresh curl calls each produced a `backtest_timing` log line with `total_ms` ~150-160ms (well under the 1.5s budget at idle, consistent with a stored-value read, not a request-path recompute)

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-24

