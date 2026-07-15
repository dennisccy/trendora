# UI Test Results (merged)

**Date:** 2026-07-15
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 20/20 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-01-verify.png |
| UT-J-02 | Drill into the evidence behind a score | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-02-verify.png |
| UT-J-03 | Unvalidated signals flagged Not yet proven on leaderboard and detail page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-03-verify.png |
| UT-J-04 | Regime-conditioned evidence | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-04-verify.png |
| UT-J-06 | vcp_contraction top-decile certified evidence outcome surfaced on Evidence + Research factor lab | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-06-verify.png |
| UT-J-07 | Multi-horizon certified evidence outcome surfaced (the loop sees beyond the 20-day horizon) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-07-verify.png |
| UT-J-08 | Multi-factor combination certified evidence outcome surfaced on the Combination lab + Evidence | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-08-verify.png |
| UT-J-09 | Relative-strength (rs_spy_3m) 60-day-horizon certified evidence outcome surfaced on Evidence + Research factor lab | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-09-verify.png |
| UT-J-10 | The product surfaces deep (up to ~30-year) price history, honestly bounded per name | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-10-verify.png |
| UT-J-12 | The universe is a broad, point-in-time dynamic set across the deep history | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-12-verify.png |
| UT-J-13 | Data Manager — widened Fetch scope, honest Backfill run, two-group availability legend | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-13-verify.png |
| UT-J-14 | The 30-year basis carries deep, honestly-sourced index context (benchmarks + macro), each labeled by vendor | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-14-verify.png |
| UT-J-17 | Certification-budget accounting panel — total trials, required_p, Thresholdout remaining, staging LORD++ wealth, each with spend-over-time | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-17-verify.png |
| UT-J-18 | Pre-registration registry — discoverable from Research hub, lists every registered hypothesis | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-18-verify.png |
| UT-J-19 | Negative-results graveyard lineage link scrolls the matching registry row into view | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-19-verify.png |
| UT-J-20 | A single daily preflight verdict guards every decision surface | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-20-verify.png |
| UT-J-21 | Live-vs-seed drift monitor feeds the preflight verdict | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-21-verify.png |
| UT-J-22 | Referee audit — certifier calibration: null-trial false-pass rate + CI, configured alpha, contaminated-factor tripwire labeled 'expected: rejected', run date from persisted artifact | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-37-evidence/J-22-verify.png |
| UT-J-05 | Audit the evidence ledger | smoke | P1 | `/evidence` renders a list of certified claims, each with hypothesis, out-of-sample verdict, control comparison, registration date, and forward-walk score-to-date; clicking a claim's linkback navigates to the surface whose badge it backs | Nav → Evidence loaded `/evidence`; 7 claim cards rendered, each showing HYPOTHESIS chips, OUT-OF-SAMPLE VERDICT (e.g. "FAIL · holdout edge -0.03%" for leadership_score), CONTROL COMPARISON (VS SPY), REGISTRATION DATE "2026-07-03", and FORWARD-WALK SCORE-TO-DATE "Pending — monitored as new data matures"; clicked "Backs: Stocks leaderboard →" on the leadership_score card → navigated to `http://localhost:3255/stocks` (heading "Stocks", "Stock Leaderboard" subtitle) | PASS | `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-ledger-list.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-backlink-stocks.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-verify.png` |
| UT-J-11 | Every displayed "Proven" edge is re-certified on the new 30-year data — no stale edge survives | regression | P1 | `/evidence` shows only rows the referee re-passed on the 30-year data (no pre-refresh stale value such as old +21.34% / +6.36% / p=0.0004998 unless independently re-certified); a surviving factor's `/evidence` row byte-matches its Research-lab badge for the same as-of | `/evidence` lists 7 claims, all FAIL, all `register_date=2026-07-03`, all `seed=20240601` (confirmed via `GET /api/evidence`); grepped rendered page text for `21.34`, `6.36`, `0.0004998` — none found. Cross-checked vcp_contraction: `/evidence` shows "FAIL · holdout edge -0.38%" (h20) and "FAIL · holdout edge -1.64%" (h60); `/api/evidence` returns `control_excess=-0.003773` (-0.38%) and `control_excess=-0.016364` (-1.64%) for the same two claims — byte-match confirmed. `/research/factor-lab` renders "Walk-forward evidence now spans up to ~30 years of history (1996 to present...)"; the vcp_contraction badge (`data-testid="factor-evidence-vcp_contraction"`) shows `data-proven="false"` at every horizon (1d/5d/10d/20d/60d), title text "Not yet proven — no certified out-of-sample evidence... (see the Evidence ledger)"; `/stocks` leaderboard shows "Not yet proven" on every score chip. No factor/cohort anywhere reads "Proven". | PASS | `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-factor-lab-list.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-vcp-crosscheck.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-verify.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-15

