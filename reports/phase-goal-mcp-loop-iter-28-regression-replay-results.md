# Regression Replay — goal-mcp-loop-iter-28

**Phase:** goal-mcp-loop-iter-28
**Date:** 2026-07-12
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every leaderboard score shows an evidence status badge | regression | P1 | journey replays end-to-end; all expects hold | step 04 expected "Unassigned" did not appear | FAIL | reports/qa/goal-mcp-loop-iter-28-evidence/J-01-verify.png |
| UT-J-03 | Unvalidated signals flagged Not yet proven on leaderboard and detail page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-28-evidence/J-03-verify.png |
| UT-J-04 | Regime-conditioned evidence | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-28-evidence/J-04-verify.png |
| UT-J-05 | Audit the evidence ledger | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-28-evidence/J-05-verify.png |
| UT-J-10 | The product surfaces deep (up to ~30-year) price history, honestly bounded per name | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-28-evidence/J-10-verify.png |
| UT-J-11 | Every displayed Proven edge is re-certified on the new 30-year data - no stale edge survives | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-28-evidence/J-11-verify.png |
| UT-J-13 | Data Manager — widened Fetch scope, honest Backfill run, two-group availability legend | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-28-evidence/J-13-verify.png |

## Failed Tests

### UT-J-01 — Every leaderboard score shows an evidence status badge

**Verdict:** FAIL
**Failure:** step 04 expected "Unassigned" did not appear
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/J-01-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-12
