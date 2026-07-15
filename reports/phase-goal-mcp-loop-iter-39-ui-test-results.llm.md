# Goal Iteration 39 — UI Test Results (Browser QA — Target journeys)

**Phase:** goal-mcp-loop-iter-39
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 8/8 tests passed (0 skipped)

**Scope note:** Per this iteration's lean verify-only closeout split, this agent live-browser-verified exactly the 8 **Target journeys** (J-01, J-02, J-03, J-05, J-10, J-13, J-20, J-23) — the required-still-passing set from iter-38's closure gap plus J-23's first-time golden. The other 13 required-still-passing journeys (J-04, J-06, J-07, J-08, J-09, J-11, J-12, J-14, J-17, J-18, J-19, J-21, J-22) were separately re-verified by deterministic golden-script replay (`demo_runner.py --mode verify`); see `reports/phase-goal-mcp-loop-iter-39-regression-replay-results.md` (13/13 PASS). All 8 golden scripts below were re-confirmed byte-accurate against live behavior and lint clean (`demo_runner.py --mode lint`) — no edits were needed to any of the 8 existing `runs/goal-session-mcp-loop/journey-scripts/J-XX.json` files.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | regression | P1 | No score on the leaderboard is presented without a visible evidence status | Visited `/stocks`; 541/541 rows loaded; all 3 score columns (Leadership/Entry Quality/Risk) × 541 rows = 1623 evidence badges present, every one reading "Not yet proven" (0 bare "Proven" occurrences) — consistent with the all-FAIL ledger | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-01-result.png |
| UT-J-02 | Drill into the evidence behind a score | regression | P1 | User can always see what the evidence says about a score; honest "Not yet proven" naming the Evidence ledger as audit path when no PASS backs it; no fabricated proof panel | Visited `/stocks/AAPL`; all 3 scores (Leadership E 55.78, Entry Quality D 69.70, Risk E 33.12) show "Not yet proven" badges (`data-testid="evidence-badge"`, `data-proven="false"`); badge title reads "Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."; badge is a static indicator (no fabricated proof panel opens) | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-02-result.png |
| UT-J-03 | Unproven / noise signals are honestly marked | regression | P1 | Unvalidated or failed signals are visibly flagged and never presented as confident | Visited `/stocks` and `/stocks/MU`; MU shows a strong Leadership score (grade C, 77.18) yet all 3 scores still read "Not yet proven" — never shown as confident despite the score strength | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-03-result.png |
| UT-J-05 | Audit the evidence ledger | regression | P1 | User can audit every "proven" claim the platform relies on, end to end | Clicked Evidence nav; 7 certified claims render, each with hypothesis, out-of-sample verdict (e.g. "FAIL · holdout edge -0.03%"), control comparison vs SPY, registration date (2026-07-03), forward-walk score-to-date ("Pending — monitored as new data matures"); clicked "Backs: Stocks leaderboard →" and landed on `/stocks` showing "Stock Leaderboard" | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-05-result.png |
| UT-J-10 | The product surfaces deep (~30-year) price history, honestly bounded per name | regression | P1 | Long-tenured names show deep history to their real first bar; post-IPO names honestly show only real short history; no fabricated bars | NVDA: Technology sector confirmed; "Full history" (default-active) shows 3025 bars since 1999-01-22 (NVDA's real listing); "Recent" toggle shows 1255 bars. Spot-checked ARM: 701 bars since 2023-09-14 (ARM's real IPO date) — honest short history, no fabrication | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-10-result.png |
| UT-J-13 | Data Manager reflects the broadened symbol universe with an unambiguous availability legend | regression | P1 | Fetch operates over the full committed pool; "Expand universe" option removed; fill (data completeness) vs snapshot (scored scan) are clearly distinct, orthogonal encodings | `/data` shows "590 symbols"; "Expand universe" confirmed absent from the page; legend text explicitly separates the two signals ("the cell fill is how many symbols have price data... and the ring is whether a scored snapshot exists...", "in a distinct colour never used by the fill"); clicked Start on the persisted idempotent backfill fixture (2005-02-28→2005-03-07) and "Snapshots backfilled" appeared in Job progress; reload showed "SCORED SNAPSHOT — INDICATOR" legend | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-13-result.png |
| UT-J-20 | A single daily preflight verdict guards every decision surface | regression | P1 | Every decision surface shows the same verdict, sourced from one place | Verified "GO — today's board is current." renders byte-identically across all 5 surfaces: `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence`. NO-GO induced-fixture path requires a controlled test-environment condition (not a live-browser-reachable action) — out of this pass's scope, consistent with the existing golden script's established scope (browser QA covers the cross-surface GO consistency; the induced-degradation matrix is a backend/fixture-level concern) | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-20-result.png |
| UT-J-23 | The watchlist discloses its real concentration | regression | P1 | X-ray shows pairwise correlation, cluster groupings, sector/theme concentration, and an ENB headline with window stated; descriptive only, no recommendations; honest NA for insufficient history | `/watchlist` (persisted 2-stock demo watchlist: MSFT, ABBV) shows "≈ 2.0 effective independent bets (over the last 126 trading days)"; info button reveals the eigenvalues-of-correlation-matrix explanation; correlation matrix shows ABBV/MSFT = -0.11; clusters, sector concentration (Technology/Unassigned 50/50), theme concentration, and shared-setup (Avoid, 100%) all render; "Descriptive only — how correlated, clustered, and concentrated your watchlist really is. No recommendations." label confirmed present | PASS | reports/qa/goal-mcp-loop-iter-39-evidence/J-23-result.png |

---

## Passed Tests

### UT-J-01 — Every score shows an evidence status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-01-result.png`
- 541/541 leaderboard rows loaded; every score cell across all 541 rows × 3 score types carries a visible evidence badge; page-wide text scan found 1623 "Not yet proven" occurrences and zero bare "Proven" occurrences — no score is presented without a status, and none is presented as confident.

### UT-J-02 — Drill into the evidence behind a score
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-02-result.png`
- On `/stocks/AAPL`, each of Leadership/Entry Quality/Risk shows a "Not yet proven" badge (`data-testid="evidence-badge"`). Inspected the DOM directly: `title="Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."` — the explanatory text honestly names the Evidence ledger as the audit path, reachable via the persistent nav. The badge is a non-interactive status indicator; clicking it does not open any panel — no fabricated proof renders.

### UT-J-03 — Unproven / noise signals are honestly marked
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-03-result.png`
- MU's Leadership score (77.18, grade C) is the strongest of its three scores, which could tempt a confident presentation — instead all three still show "Not yet proven," confirming the badge is driven by the ledger, not by score magnitude.

### UT-J-05 — Audit the evidence ledger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-05-result.png`
- `/evidence` lists 7 certified claims (leadership_score, Breakout-watch event-study, ma_stack, vcp_contraction ×2, rs_spy_3m×high_proximity composite, rs_spy_3m), each with hypothesis, verdict, SPY control comparison, 2026-07-03 registration date, and forward-walk score-to-date. Clicking "Backs: Stocks leaderboard →" navigated to `/stocks` and rendered "Stock Leaderboard" — the linkback to the backed surface works.

### UT-J-10 — The product surfaces deep (~30-year) price history, honestly bounded per name
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-10-result.png` (also `J-10-before.png`)
- NVDA "Full history" (the default-active state, confirmed via `aria-pressed="true"` on the button) shows 3025 bars, "history since 1999-01-22" — NVDA's real listing date, not a fabricated 1996 floor. Toggling "Recent" shows 1255 bars (~5y window). ARM (post-IPO) shows only 701 bars since 2023-09-14, its real IPO date — short history honestly disclosed, nothing synthesized.

### UT-J-13 — Data Manager reflects the broadened universe with an unambiguous availability legend
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-13-result.png` (also `J-13-before.png`)
- "590 symbols" shown; a page-wide text search confirmed "Expand universe" no longer appears anywhere. The legend explicitly states the fill = price-data completeness (from Fetch) and the ring = scored-snapshot existence (from Backfill), "in a distinct colour never used by the fill" — the two encodings are described as orthogonal, not merged. Clicked "Start" on the persisted idempotent backfill fixture (date range 2005-02-28→2005-03-07, already used by many prior iterations' QA passes per Run history); "Snapshots backfilled" appeared in the Job progress panel. Reloading confirmed "SCORED SNAPSHOT — INDICATOR" renders in the legend.

### UT-J-20 — A single daily preflight verdict guards every decision surface
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-20-result.png`
- "GO — today's board is current." confirmed present, byte-identical, on `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, and `/evidence` — strong behavioral evidence of a single shared readiness source rather than per-page computation.

### UT-J-23 — The watchlist discloses its real concentration
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-39-evidence/J-23-result.png` (also `J-23-enb-tooltip.png`)
- The persisted 2-name demo watchlist (MSFT, ABBV) on `/watchlist` shows "≈ 2.0 effective independent bets (over the last 126 trading days)". Clicking the info button (`aria-label="What is effective independent bets?"`) revealed: "...derived from the eigenvalues of the pairwise correlation matrix over the trailing 126 trading days... A name with under 60 days of overlapping history is excluded and shown as NA." The correlation matrix shows ABBV↔MSFT = -0.11 (symmetric); clusters show ABBV and MSFT as separate (uncorrelated, below the 0.70 grouping threshold); sector/theme concentration and shared-setup panels render; "Descriptive only ... No recommendations." confirmed present.

---

## Failed Tests

None — all 8 target journeys passed.

---

## Skipped Tests

None — frontend was reachable and Chrome MCP was available for the full run.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`, CDP-driven)
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-39-evidence/`
- **Golden scripts:** all 8 re-confirmed accurate in `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-02,J-03,J-05,J-10,J-13,J-20,J-23}.json`; all lint clean via `demo_runner.py --mode lint`. No edits were required — each already byte-matched live behavior.
- **Note — shared browser instance:** the Chrome MCP browser is a persistent instance shared with at least one other concurrent session (an unrelated "Tapeology" localhost:3301 tab kept reappearing mid-run). Two of my actions were momentarily misdirected at that stray tab; both were caught immediately (via `list_tabs`/DOM-title check), the stray tab was closed, and the actions were re-run against the correct Trendora tab with explicit `tab_index` targeting before any verdict was recorded. No PASS verdict above relies on a misdirected action.
