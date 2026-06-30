# Phase goal-mcp-loop-iter-7 — UI Test Results

**Phase:** goal-mcp-loop-iter-7
**Date:** 2026-06-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | happy-path | P1 | All leaderboard rows show "Proven" or "Not yet proven" badge on every score; at least one badge present | All 120/120 rows show "Proven" on Leadership and "Not yet proven" on Entry Quality and Risk — no score lacks a status | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-01-result.png |
| UT-J-02 | Drill into the proof behind a score | happy-path | P1 | Clicking "Why proven?" shows OOS test result, control comparison, certified-claim id + registration date | Panel expanded on MU: OUT-OF-SAMPLE TEST PASS (holdout edge +6.36%, p=0.0004998, 12,297 obs), CONTROL COMPARISON +6.36% vs SPY, CERTIFIED CLAIM leadership_score · registered 2026-06-30 | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-02-result.png |
| UT-J-03 | Unproven / noise signals are honestly marked | happy-path | P1 | Unvalidated scores show "Not yet proven" rather than a confident number | Entry Quality (23.66) and Risk (53.11) for MU both display "Not yet proven"; same pattern across all 120 leaderboard rows | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-03-result.png |
| UT-J-04 | Regime-conditioned evidence | happy-path | P1 | Evidence surface for current regime is labeled with the regime it applies to | Dashboard shows current regime Risk-on (76.05). Evidence page (reached via "See evidence proven in this regime →") shows claim "Breakout-watch setup · Regime: Risk-on · Out-of-sample edge in the Risk-on regime" PASS holdout edge +6.12% | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-04-result.png |
| UT-J-05 | Audit the evidence ledger | happy-path | P1 | /evidence renders list of certified claims each with hypothesis, OOS verdict, control comparison, registration date, forward-walk score-to-date; each links back to backing surface | 2 certified claims rendered: (1) leadership_score — PASS, +6.36% vs SPY, registered 2026-06-30, "Backs: Stocks leaderboard →" href=/stocks; (2) Breakout-watch setup Regime: Risk-on — PASS, +6.12% vs SPY, registered 2026-06-30, "Backs: Research event-study lab →" href=/research/event-study | PASS | reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-05-result.png |

---

## Passed Tests

### UT-J-01 — Every score shows an evidence status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-01-result.png`
- Navigated to `/stocks`. Leaderboard shows 120/120 rows.
- Every row's Leadership column shows the score AND "Proven" badge.
- Every row's Entry Quality column shows the score AND "Not yet proven" badge.
- Every row's Risk column shows the score AND "Not yet proven" badge.
- No row has a score presented without a visible evidence status.
- Acceptance condition met: no score on the leaderboard is presented without a visible evidence status.

---

### UT-J-02 — Drill into the proof behind a score
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-02-result.png`
- Navigated to `/stocks/MU` (rank 1 stock, Leadership A 94.58, Proven).
- Located the "Why proven?" button below the Leadership "Proven" badge.
- Clicked "Why proven?" — proof panel expanded inline.
- Panel showed:
  - OUT-OF-SAMPLE TEST: PASS · holdout edge +6.36% · p = 0.0004998 · Sealed holdout cohort: 12,297 observations
  - CONTROL COMPARISON: +6.36% vs SPY (benchmark control)
  - CERTIFIED CLAIM: leadership_score · registered 2026-06-30 · "View backing evidence row →" link
- Acceptance condition met: the user can see why a score is proven — the test, the controls, and the date.

---

### UT-J-03 — Unproven / noise signals are honestly marked
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-03-result.png`
- On `/stocks/MU` detail page:
  - Entry Quality score (E, 23.66/100) shows "Not yet proven" with no drill-down.
  - Risk score (E, 53.11/100) shows "Not yet proven" with no drill-down.
- On `/stocks` leaderboard, all 120 rows show "Not yet proven" for both Entry Quality and Risk.
- No unvalidated score is presented as a confident number without the "Not yet proven" flag.
- Acceptance condition met: unvalidated signals are visibly flagged and never presented as confident.

---

### UT-J-04 — Regime-conditioned evidence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-04-result.png` (Evidence page) and `reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-04-dashboard.png` (Dashboard)
- Visited `/` (Dashboard): current market regime is "Risk-on" (76.05/100).
- Dashboard shows "See evidence proven in this regime →" affordance under the regime card.
- Clicked the link → navigated to `/evidence`.
- Evidence page shows second certified claim: "Breakout-watch setup · Regime: Risk-on".
- Claim description: "Out-of-sample edge in the Risk-on regime".
- Claim details: PASS · holdout edge +6.12% · +6.12% vs SPY · registered 2026-06-30.
- Regime label "Risk-on" appears inline on the claim, matching the Dashboard regime.
- Acceptance condition met: evidence is regime-scoped and clearly labeled with the regime it holds in.

---

### UT-J-05 — Audit the evidence ledger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-7-evidence/UT-J-05-result.png`
- Navigated to `/evidence` via "Evidence" in the nav.
- Page renders 2 certified claims:
  1. **leadership_score**: hypothesis (decile=10, direction=positive, factor=leadership_score, horizon=20, kind=factor, slice_kind=decile), OOS verdict PASS holdout edge +6.36%, control comparison +6.36% vs SPY, registration date 2026-06-30, forward-walk score-to-date "Pending — monitored as new data matures". Back-link: "Backs: Stocks leaderboard →" (href=/stocks).
  2. **Breakout-watch setup · Regime: Risk-on**: hypothesis (direction=positive, horizon=20, kind=event-study, regime=Risk-on, slice_kind=regime, subject=Breakout-watch, view=pooled), OOS verdict PASS holdout edge +6.12%, control comparison +6.12% vs SPY, registration date 2026-06-30, forward-walk "Pending". Back-link: "Backs: Research event-study lab →" (href=/research/event-study).
- Both claims have all required fields: hypothesis, OOS verdict, control comparison, registration date, forward-walk score-to-date.
- Back-links confirmed present pointing to the surfaces whose badges they back.
- Acceptance condition met: the user can audit every "proven" claim the platform relies on, end to end.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chrome via MCP (mcp__plugin_superpowers-chrome_chrome__use_browser)
- **Test Date:** 2026-06-30
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-7-evidence/`
