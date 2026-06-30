# UI Test Results (merged)

**Date:** 2026-06-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | happy-path | P1 | All leaderboard rows show "Proven" or "Not yet proven" badge on every score; at least one badge present | All 120/120 rows show "Proven" on Leadership and "Not yet proven" on Entry Quality and Risk — no score lacks a status | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-01-result.png |
| UT-J-02 | Drill into the proof behind a score | happy-path | P1 | Clicking "Why proven?" shows OOS test result, control comparison, certified-claim id + registration date | Panel expanded on MU: OUT-OF-SAMPLE TEST PASS (holdout edge +6.36%, p=0.0004998, 12,297 obs), CONTROL COMPARISON +6.36% vs SPY, CERTIFIED CLAIM leadership_score · registered 2026-06-30 | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-02-result.png |
| UT-J-03 | Unproven / noise signals are honestly marked | happy-path | P1 | Unvalidated scores show "Not yet proven" rather than a confident number | Entry Quality (23.66) and Risk (53.11) for MU both display "Not yet proven"; same pattern across all 120 leaderboard rows | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-03-result.png |
| UT-J-04 | Regime-conditioned evidence | happy-path | P1 | Evidence surface for current regime is labeled with the regime it applies to | Dashboard shows current regime Risk-on (76.05). Evidence page (reached via "See evidence proven in this regime →") shows claim "Breakout-watch setup · Regime: Risk-on · Out-of-sample edge in the Risk-on regime" PASS holdout edge +6.12% | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-04-result.png |
| UT-J-05 | Audit the evidence ledger | happy-path | P1 | /evidence renders list of certified claims each with hypothesis, OOS verdict, control comparison, registration date, forward-walk score-to-date; each links back to backing surface | 2 certified claims rendered: (1) leadership_score — PASS, +6.36% vs SPY, registered 2026-06-30, "Backs: Stocks leaderboard →" href=/stocks; (2) Breakout-watch setup Regime: Risk-on — PASS, +6.12% vs SPY, registered 2026-06-30, "Backs: Research event-study lab →" href=/research/event-study | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-05-result.png |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-06-30

