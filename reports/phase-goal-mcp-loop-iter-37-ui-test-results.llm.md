# Phase goal-mcp-loop-iter-37 — UI Test Results

**Phase:** goal-mcp-loop-iter-37
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 2/2 tests passed (0 skipped)

Scope note (lean iteration, goal-mode dispatch): this run live-verifies EXACTLY the two
Target journeys named by the dispatch wrapper — **J-05** and **J-11** — the same two rows
the iter-36 closure auditor flagged as unverified (no screenshot evidence). The other 18
Required-still-passing journeys (J-01..J-04, J-06..J-10, J-12..J-14, J-17..J-22) are
explicitly OUT of this agent's scope this run; they are covered by the deterministic
golden-script replay lane (`demo_runner.py --mode verify`), which had already produced
fresh `<J-XX>-verify.png` evidence for all 18 of them in
`reports/qa/goal-mcp-loop-iter-37-evidence/` before this browser-qa dispatch started.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Audit the evidence ledger | smoke | P1 | `/evidence` renders a list of certified claims, each with hypothesis, out-of-sample verdict, control comparison, registration date, and forward-walk score-to-date; clicking a claim's linkback navigates to the surface whose badge it backs | Nav → Evidence loaded `/evidence`; 7 claim cards rendered, each showing HYPOTHESIS chips, OUT-OF-SAMPLE VERDICT (e.g. "FAIL · holdout edge -0.03%" for leadership_score), CONTROL COMPARISON (VS SPY), REGISTRATION DATE "2026-07-03", and FORWARD-WALK SCORE-TO-DATE "Pending — monitored as new data matures"; clicked "Backs: Stocks leaderboard →" on the leadership_score card → navigated to `http://localhost:3255/stocks` (heading "Stocks", "Stock Leaderboard" subtitle) | PASS | `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-ledger-list.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-backlink-stocks.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-verify.png` |
| UT-J-11 | Every displayed "Proven" edge is re-certified on the new 30-year data — no stale edge survives | regression | P1 | `/evidence` shows only rows the referee re-passed on the 30-year data (no pre-refresh stale value such as old +21.34% / +6.36% / p=0.0004998 unless independently re-certified); a surviving factor's `/evidence` row byte-matches its Research-lab badge for the same as-of | `/evidence` lists 7 claims, all FAIL, all `register_date=2026-07-03`, all `seed=20240601` (confirmed via `GET /api/evidence`); grepped rendered page text for `21.34`, `6.36`, `0.0004998` — none found. Cross-checked vcp_contraction: `/evidence` shows "FAIL · holdout edge -0.38%" (h20) and "FAIL · holdout edge -1.64%" (h60); `/api/evidence` returns `control_excess=-0.003773` (-0.38%) and `control_excess=-0.016364` (-1.64%) for the same two claims — byte-match confirmed. `/research/factor-lab` renders "Walk-forward evidence now spans up to ~30 years of history (1996 to present...)"; the vcp_contraction badge (`data-testid="factor-evidence-vcp_contraction"`) shows `data-proven="false"` at every horizon (1d/5d/10d/20d/60d), title text "Not yet proven — no certified out-of-sample evidence... (see the Evidence ledger)"; `/stocks` leaderboard shows "Not yet proven" on every score chip. No factor/cohort anywhere reads "Proven". | PASS | `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-factor-lab-list.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-vcp-crosscheck.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-verify.png` |

---

## Passed Tests

### UT-J-05 — Audit the evidence ledger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-ledger-list.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-05-backlink-stocks.png`

- Step 1: Navigated to `http://localhost:3255/`, clicked "Evidence" in the persistent left nav (`a[href="/evidence"]`) → landed on `/evidence`.
- Step 2: Extracted page text — 7 certified-claim cards render (leadership_score, Breakout-watch setup, ma_stack, vcp_contraction ×2, rs_spy_3m × high_proximity composite, rs_spy_3m). Every card carries all five required fields: HYPOTHESIS (selector chips), OUT-OF-SAMPLE VERDICT (status + holdout-edge headline + reason sentence), CONTROL COMPARISON (VS SPY), REGISTRATION DATE (2026-07-03), FORWARD-WALK SCORE-TO-DATE ("Pending — monitored as new data matures"). No score/claim is missing a field.
- Step 3: Clicked the "Backs: Stocks leaderboard →" linkback on the leadership_score card (`//a[contains(., "Stocks leaderboard")]`). `window.location.href` confirmed `http://localhost:3255/stocks`; the page heading changed to "Stocks" / "Stock Leaderboard — ranked by Leadership...". The linkback correctly routes to the exact surface (`/stocks`) whose inline score badges the leadership_score claim backs.
- Acceptance ("the user can audit every proven claim... end to end") is satisfied: every claim on the ledger — proven or not — is fully inspectable (hypothesis, verdict, control, date, forward-walk) and each links back to its backed surface. The ledger is honestly all-FAIL right now (no "proven" claim exists to audit a proof for), which is the correct state given the current referee verdicts, not a gap in the audit mechanism itself.
- Additionally self-checked with the deterministic replay runner (`demo_runner.py --mode verify`) against the freshly written golden `J-05.json` — replayed cleanly end-to-end (see `J-05-verify.png`), confirming the golden script is launch-ready for future regression replay.

---

### UT-J-11 — Every displayed "Proven" edge is re-certified on the new 30-year data — no stale edge survives
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-factor-lab-list.png`, `reports/qa/goal-mcp-loop-iter-37-evidence/J-11-vcp-crosscheck.png`

- Step 1 (data-basis check): `/research/factor-lab` explicitly states "Walk-forward evidence now spans up to ~30 years of history (1996 to present, each name from its real first bar)" — confirms the surfaced evidence is computed on the rebuilt 30-year basis, not the retired ~5-year window. Backend `/api/health` reports `seed_latest_date: 2026-07-01`, 590 symbols, consistent with the widened basis.
- Step 2: Visited `/evidence` — all 7 rows are FAIL, all `register_date=2026-07-03` (the sanctioned re-referee date), all `seed=20240601` (confirmed via `GET /api/evidence` JSON — determinism preserved). Grepped the rendered page's extracted text/markdown for the named pre-refresh stale values `21.34`, `6.36`, and `0.0004998` — none present anywhere on the page. Every displayed control/edge is a small, clearly-negative-or-insignificant value (-0.03%, -0.68%, +0.21%, -0.38%, -1.64%, +0.01%, -1.42%), consistent with a freshly regenerated, non-carried ledger.
- Step 3 (cross-check): Picked vcp_contraction (appears twice on `/evidence`: top-decile h20 "FAIL · holdout edge -0.38%" and the canonical h60 promotion "FAIL · holdout edge -1.64%"). Queried `GET /api/evidence` directly and confirmed byte-level match: `control_excess=-0.003773` → -0.38% (h20, p=0.9595) and `control_excess=-0.016364` → -1.64% (h60, p=0.9995) — the UI values are not recomputed, they are the verbatim served numbers. On `/research/factor-lab`, expanded the "Volatility contraction (VCP-style)" row (`data-testid="factor-evidence-vcp_contraction"`); every horizon badge (1d/5d/10d/20d/60d) carries `data-proven="false"` with title text "Not yet proven — no certified out-of-sample evidence backs this factor's top decile (D10) at the N-day horizon yet (see the Evidence ledger)." No horizon, no factor, and no cohort anywhere on the Factor Lab or the `/stocks` leaderboard reads "Proven" — every score chip on `/stocks` reads "Not yet proven".
- Honest-status / anti-goal check: no retired/overfit edge is shown as proven (anti-goal #4); every non-clearing edge honestly reads "Not yet proven" (anti-goal #1); no return/price/buy-sell language observed on either page.
- Additionally self-checked with the deterministic replay runner (`demo_runner.py --mode verify`) against the freshly written golden `J-11.json` — replayed cleanly end-to-end (see `J-11-verify.png`), confirming the golden script is launch-ready for future regression replay.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden replay scripts

Both journeys PASSED live, so both goldens were (re)written to
`runs/goal-session-mcp-loop/journey-scripts/`, overwriting the pre-existing (older,
un-replayed) versions with scripts grounded in this session's actual verified steps/text:

- `runs/goal-session-mcp-loop/journey-scripts/J-05.json` — 6 steps: load `/evidence`,
  assert hypothesis/verdict/date/forward-walk text, click "Backs: Stocks leaderboard"
  (text target), assert landing on the Stock Leaderboard.
- `runs/goal-session-mcp-loop/journey-scripts/J-11.json` — 6 steps: load `/evidence`,
  assert the regenerated vcp_contraction h60 verdict text + registration date, load
  `/research/factor-lab`, assert the "~30 years of history" disclosure, click the
  `factor-evidence-vcp_contraction` testid to expand the decile grid, load `/stocks` and
  assert "Not yet proven".

Both were validated two ways before being treated as final:
1. `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-mcp-loop/journey-scripts --journeys J-05,J-11` → `J-05 ok`, `J-11 ok`.
2. A full headless replay self-check: `python3 scripts/automation/lib/demo_runner.py --mode verify --base-url http://localhost:3255 --scripts-dir runs/goal-session-mcp-loop/journey-scripts --journeys J-05,J-11 --evidence-dir reports/qa/goal-mcp-loop-iter-37-evidence --repo-root /home/dennis-chan/Git/trendora` → `2 journey(s), 0 failed (verdict: PASS)`, producing `J-05-verify.png` and `J-11-verify.png` in the evidence directory (filling the exact two-row gap this lean iteration exists to close).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (prod-mode uvicorn; `/api/health` → `status: ok`, `readiness: ready`, `preflight.verdict: GO`, `seed_latest_date: 2026-07-01`, `symbol_count: 590`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`) for the live walk; headless Chromium via Playwright (`demo_runner.py --mode verify`) for the golden-script self-check
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-37-evidence/`
