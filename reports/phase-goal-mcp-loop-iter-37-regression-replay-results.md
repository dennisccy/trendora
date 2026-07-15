# Regression Replay — goal-mcp-loop-iter-37

**Phase:** goal-mcp-loop-iter-37
**Date:** 2026-07-15
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 18/18 journeys passed (0 skipped)

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

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-15
