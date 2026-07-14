# UI Test Results (merged)

**Date:** 2026-07-14
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 18/18 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-01-verify.png |
| UT-J-02 | Drill into the evidence behind a score | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-02-verify.png |
| UT-J-03 | Unvalidated signals flagged Not yet proven on leaderboard and detail page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-03-verify.png |
| UT-J-04 | Regime-conditioned evidence | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-04-verify.png |
| UT-J-05 | Audit the evidence ledger | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-05-verify.png |
| UT-J-06 | vcp_contraction top-decile certified evidence outcome surfaced on Evidence + Research factor lab | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-06-verify.png |
| UT-J-07 | Multi-horizon certified evidence outcome surfaced (the loop sees beyond the 20-day horizon) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-07-verify.png |
| UT-J-08 | Multi-factor combination certified evidence outcome surfaced on the Combination lab + Evidence | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-08-verify.png |
| UT-J-09 | Relative-strength (rs_spy_3m) 60-day-horizon certified evidence outcome surfaced on Evidence + Research factor lab | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-09-verify.png |
| UT-J-10 | The product surfaces deep (up to ~30-year) price history, honestly bounded per name | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-10-verify.png |
| UT-J-11 | Every displayed Proven edge is re-certified on the new 30-year data - no stale edge survives | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-11-verify.png |
| UT-J-12 | The universe is a broad, point-in-time dynamic set across the deep history | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-12-verify.png |
| UT-J-13 | Data Manager — widened Fetch scope, honest Backfill run, two-group availability legend | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-13-verify.png |
| UT-J-14 | The 30-year basis carries deep, honestly-sourced index context (benchmarks + macro), each labeled by vendor | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-14-verify.png |
| UT-J-17 | Certification-budget accounting panel — total trials, required_p, Thresholdout remaining, staging LORD++ wealth, each with spend-over-time | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-17-verify.png |
| UT-J-18 | Pre-registration registry — discoverable from Research hub, lists every registered hypothesis | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-18-verify.png |
| UT-J-19 | Negative-results graveyard lineage link scrolls the matching registry row into view | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-mcp-loop-iter-34-evidence/J-19-verify.png |
| UT-J-20 | A single daily preflight verdict guards every decision surface | smoke | P1 | GO banner ("GO — today's board is current.") renders identically on dashboard/`/stocks`/stock-detail/`/watchlist`/`/evidence`, sourced from one `/api/health` payload; DEGRADED/NO-GO states (carried from byte-identical iter-33 code) render loud banners with concrete reasons, NO-GO containing "do not rely on today's board" | All 5 required surfaces confirmed live via Chrome MCP: identical `data-verdict="GO"` banner, text byte-matches `"GO — today's board is current."`, matches live `GET /api/health` (`preflight.verdict:"GO"`, `reasons:[]`) verbatim. Single-source confirmed live (exactly 1 `[data-testid="preflight-banner"]` element; DOM verdict === fresh API fetch verdict). DEGRADED/NO-GO not re-induced live this session (blocked by a tool-permission boundary — see Notes) but carried on `git diff HEAD` byte-identity for `readiness.py`, `config.yaml`, and all of `apps/frontend` against iter-33's commit (4561da1), which live-verified DEGRADED + NO-GO (incl. the exact mandated phrase) on all 5 surfaces just prior, same day. | PASS | `reports/qa/goal-mcp-loop-iter-34-evidence/J-20-00-stocks-go.png`, `J-20-01-dashboard-go.png`, `J-20-02-stock-detail-go.png`, `J-20-03-watchlist-go.png`, `J-20-04-evidence-go.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-14

