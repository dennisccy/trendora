# Phase goal-mcp-loop-iter-6 — UI Test Results

**Phase:** goal-mcp-loop-iter-6
**Date:** 2026-06-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | regression | P1 | 120/120 stocks with Proven + Not yet proven badges on /stocks | /stocks loaded 120/120 rows; every Leadership badge shows "Proven", every Entry Quality + Risk badge shows "Not yet proven"; Market Regime Risk-on 76.05 visible | PASS | reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-01-stocks-badges.png |
| UT-J-02 | Drill into the proof behind a proven score | regression | P1 | MU /stocks/MU shows "Why proven?" expanding to PASS + +6.36% + 12,297 cohort | Navigated to /stocks/MU; "Why proven?" button present; clicked button; proof panel expanded showing "PASS holdout edge +6.36% p=0.0004998", "Sealed holdout cohort: 12,297 observations", "+6.36% vs SPY", "leadership_score · registered 2026-06-30", "View backing evidence row →" | PASS | reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-02-proof-panel.png |
| UT-J-03 | Unproven/noise signals are honestly marked | regression | P1 | "Not yet proven" appears on /stocks and /stocks/MU for Entry Quality and Risk | "Not yet proven" confirmed present on /stocks (120 rows, Entry Quality + Risk) and on /stocks/MU (Entry Quality 23.66 + Risk 53.11 both "Not yet proven") | PASS | reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-03-not-yet-proven.png |
| UT-J-04 | Regime-conditioned evidence | target (J-04 → passing) | P1 | Dashboard shows current regime; /evidence shows a claim labeled with that regime | Dashboard shows "Risk-on 76.05" and "See evidence proven in this regime →" link to /evidence; /evidence row 2 shows "Breakout-watch setup", "Regime: Risk-on", "Out-of-sample edge in the Risk-on regime", OOS PASS +6.12% p=0.0004998 < alpha/2=0.025, registered 2026-06-30 | PASS | reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-04-regime-evidence.png |
| UT-J-05 | Audit the evidence ledger (round-trip) | regression | P1 | /evidence shows 2 certified claims; "Backs:" link leads back to surface | /evidence shows both certified claims (leadership_score PASS +6.36%, Breakout-watch Regime:Risk-on PASS +6.12%); "Backs: Stocks leaderboard →" navigates to /stocks confirming round-trip; "Backs: Research event-study lab →" links to /research/event-study | PASS | reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-05-evidence-ledger.png |

---

## Passed Tests

### UT-J-01 — Every score shows an evidence status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-01-stocks-badges.png`
- Navigated to http://localhost:3255/stocks; page loaded "Stock Leaderboard" heading
- "120 / 120" count confirmed in the page text
- Market Regime strip shows "Risk-on 76.05"
- Every row verified: Leadership grade (A/B/C/D/E) + score + "Proven" badge; Entry Quality + Risk both show "Not yet proven"
- No score on the leaderboard is presented without a visible evidence status

---

### UT-J-02 — Drill into the proof behind a proven score
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-02-proof-panel.png`
- Navigated to http://localhost:3255/stocks/MU; Leadership A 94.58 "Proven" visible with "Why proven?" button
- Clicked "Why proven?" button (fifth button on page via JS click)
- Proof panel expanded showing:
  - "OUT-OF-SAMPLE TEST — PASS — holdout edge +6.36% — p = 0.0004998"
  - "Sealed holdout cohort: 12,297 observations"
  - "CONTROL COMPARISON — +6.36% vs SPY (benchmark control)"
  - "CERTIFIED CLAIM — leadership_score · registered 2026-06-30"
  - "View backing evidence row →" link present

---

### UT-J-03 — Unproven / noise signals are honestly marked
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-03-not-yet-proven.png`
- Confirmed "Not yet proven" text present on /stocks leaderboard (Entry Quality + Risk for all 120 rows)
- Confirmed "Not yet proven" text present on /stocks/MU detail page for Entry Quality 23.66 and Risk 53.11
- Leadership is the only score with a "Proven" badge, consistent with the single certified leadership_score claim

---

### UT-J-04 — Regime-conditioned evidence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-04-regime-evidence.png`
- Navigated to http://localhost:3255/ (Dashboard); confirmed Market Regime "Risk-on 76.05 / 100"
- Confirmed "See evidence proven in this regime →" link present on Dashboard, href = http://localhost:3255/evidence
- Navigated to http://localhost:3255/evidence
- Row 2 shows: "PASS — Breakout-watch setup — Regime: Risk-on — Backs: Research event-study lab →"
- Label "Out-of-sample edge in the Risk-on regime" present
- OOS verdict: "PASS · holdout edge +6.12% — p=0.0004998 < alpha/2=0.025"
- Control comparison: "+6.12% vs SPY"
- Registration date: 2026-06-30
- Evidence is regime-scoped and clearly labeled with the regime (Risk-on) it holds in
- J-04 flips from "partial" to "passing" this iteration

---

### UT-J-05 — Audit the evidence ledger (round-trip)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-05-evidence-ledger.png`
- Navigated to http://localhost:3255/evidence via nav link
- Both certified claims render:
  1. "PASS leadership_score" — hypothesis (decile=10, factor=leadership_score, horizon=20), OOS PASS +6.36%, control +6.36% vs SPY, registered 2026-06-30, "Backs: Stocks leaderboard →"
  2. "PASS Breakout-watch setup [Regime: Risk-on]" — hypothesis (event-study, regime=Risk-on), OOS PASS +6.12%, control +6.12% vs SPY, registered 2026-06-30, "Backs: Research event-study lab →"
- Round-trip verified: "Backs: Stocks leaderboard →" (href=/stocks) navigated to /stocks leaderboard
- "Backs: Research event-study lab →" href confirmed as /research/event-study

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (health: ok, db_ok: true, seed 2026-06-25, 162 symbols)
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-30
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-6-evidence/`

## Notes

This iteration had no new UI changes (harness-only: scripts/automation fixes only). The browser-qa lane re-verified all five required journeys from the journey-history contract.

Key result: **J-04 (Regime-conditioned evidence) passes for the first time in the canonical browser-qa-agent lane.** The evidence page at /evidence shows a certified claim explicitly labeled "Regime: Risk-on" with OOS PASS +6.12% (p=0.0004998 < alpha/2=0.025), and the Dashboard's "See evidence proven in this regime →" affordance links to it. J-04 status upgrades from "partial" to "passing".

J-02's expanded proof panel (the drill-down beyond the score cards, showing the OOS test + control + certified claim id + date) is now freshly captured in this canonical lane iteration (UT-J-02-proof-panel.png), resolving the iter-3 standing gap noted in the journey-history.
