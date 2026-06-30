# Phase goal-mcp-loop-iter-3 — UI Test Results

**Phase:** goal-mcp-loop-iter-3
**Date:** 2026-06-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 16/16 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stocks leaderboard page loads without errors | smoke | P1 | Page renders, 5+ rows, no spinner/error, health badge "Ready" | 120 rows loaded, health badge reads "Ready", no errors | PASS | `UT-01-result.png` |
| UT-02 | Leadership column displays green "Proven" chip on every visible row | regression | P1 | Green "Proven" chip on all rows | All 120 rows show "Proven" chip (color rgb(79,209,197) teal accent) | PASS | `UT-02-result.png` |
| UT-03 | Entry Quality column displays muted "Not yet proven" chip | regression | P1 | Muted grey chip, no drill-down on click | All 120 rows show "Not yet proven" (rgb(91,102,119) grey); clicking opened no panel | PASS | `UT-03-after-click.png` |
| UT-04 | Risk column displays muted "Not yet proven" chip | regression | P1 | Muted grey chip, no drill-down on click | All 120 rows show "Not yet proven" grey chip; clicking opened no panel | PASS | `UT-04-after-click.png` |
| UT-05 | Health badge reads "Ready" when both services are up | regression | P1 | Badge reads "Ready" | Badge reads "Ready" with backend confirmed healthy at /api/health | PASS | `UT-01-result.png` |
| UT-06 | Stock detail page for MU loads with three score cards | smoke | P1 | Three cards: Leadership, Entry Quality, Risk; no 404/error | Three cards visible: Leadership A/94.58 Proven, Entry Quality E/23.66 Not yet proven, Risk E/53.11 Not yet proven | PASS | `UT-06-result.png` |
| UT-07 | Leadership "Why proven?" toggle expands proof panel | happy-path | P1 | Panel expands with "PASS"; "Why proven?" button still visible | Panel expanded showing PASS verdict; button visible; panel contains text | PASS | `UT-07-panel-open.png` |
| UT-08 | Expanded proof panel displays correct OOS evidence values | regression | P1 | PASS, +6.36%, p≈0.0005, n=12,297, vs SPY, leadership_score, 2026-06-30 | PASS, +6.36%, p=0.0004998 (≈0.0005), 12,297 observations, vs SPY, leadership_score, registered 2026-06-30 — all values correct | PASS | `UT-08-proof-panel.png` |
| UT-09 | "View backing evidence row" link navigates to evidence anchor | regression | P1 | Browser navigates to /evidence#signal-leadership_score; leadership_score row visible | Link href was http://localhost:3255/evidence#signal-leadership_score; navigated successfully; leadership_score row visible | PASS | `UT-09-evidence-page.png` |
| UT-10 | Entry Quality score card has no "Why proven?" toggle | regression | P1 | No "Why proven?" button on Entry Quality card | Only 1 "Why proven?" button on page (Leadership); Entry Quality card has none | PASS | `UT-06-result.png` |
| UT-11 | Risk score card has no "Why proven?" toggle | regression | P1 | No "Why proven?" button on Risk card | Only 1 "Why proven?" button on page (Leadership); Risk card has none | PASS | `UT-06-result.png` |
| UT-12 | Evidence ledger page loads with leadership_score row | smoke | P1 | Page renders; leadership_score row visible; no 404/error | Page rendered; leadership_score row present with PASS verdict, +6.36%, SPY benchmark, 2026-06-30 date | PASS | `UT-12-evidence-page.png` |
| UT-13 | leadership_score claim row shows all five required evidence fields | regression | P1 | Hypothesis, PASS verdict, +6.36%, SPY benchmark, 2026-06-30; no blank fields | All five fields present: hypothesis text (decile=10 … factor=leadership_score …), PASS, +6.36%, VS SPY, 2026-06-30 | PASS | `UT-12-evidence-page.png` |
| UT-14 | "Backs: Stocks leaderboard" link returns to /stocks | regression | P1 | Browser navigates to /stocks; leaderboard populated; Leadership shows green "Proven" | Link clicked from /evidence; navigated to /stocks; 120 rows with "Proven" chips visible | PASS | `UT-14-back-to-stocks.png` |
| UT-15 | "Proven" badge visually distinct from "Not yet proven" badges | ux | P2 | Proven=accent/green; Not yet proven=muted/grey; immediately distinct | Proven: rgb(79,209,197) teal accent; Not yet proven: rgb(91,102,119) muted grey — clearly distinct at a glance | PASS | `UT-15-badge-comparison.png` |
| UT-16 | Evidence proof drill-down discoverable within 2 clicks | ux | P2 | 2 clicks from leaderboard reach proof panel; no additional nav required | Click 1: MU link → /stocks/MU; Click 2: "Why proven?" → proof panel with PASS/+6.36%/12,297 — 2 clicks confirmed | PASS | `UT-16-2click-proof.png` |

---

## Passed Tests

### UT-01 — Stocks leaderboard page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-01-result.png`
- Navigated to http://localhost:3255/stocks; page loaded fully
- 120/120 rows visible in leaderboard table
- Health badge reads "Ready" (backend /api/health confirmed: status ok, readiness ready)
- No "Checking backend…" spinner; no blank screen; no error message

### UT-02 — Leadership column displays green "Proven" chip on every visible row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-02-result.png`
- All 120 rows in the Leadership column show "Proven" chip
- Computed color: rgb(79, 209, 197) — teal/green accent, clearly positive-state styling
- CSS classes include `border-accent bg-surface-` indicating accent color variant

### UT-03 — Entry Quality column displays muted "Not yet proven" chip
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-03-after-click.png`
- All 120 rows in Entry Quality column show "Not yet proven" chip (240 total instances across Entry Quality + Risk)
- Computed color: rgb(91, 102, 119) — muted grey, clearly different from Leadership's teal accent
- After clicking the Entry Quality "Not yet proven" chip: DOM structure remained the same (171 buttons, 6 inputs, 256 links unchanged); no drill-down panel opened

### UT-04 — Risk column displays muted "Not yet proven" chip
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-04-after-click.png`
- All 120 rows in Risk column show "Not yet proven" chip
- Same muted styling as Entry Quality (rgb(91, 102, 119))
- After clicking the Risk "Not yet proven" chip: DOM structure unchanged; no drill-down panel opened
- Styling identical to Entry Quality "Not yet proven" chip as expected

### UT-05 — Health badge reads "Ready" when both services are up
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-01-result.png`
- Health badge text confirmed as "Ready" on /stocks page
- Backend verified healthy: curl to http://localhost:8255/api/health returned `{"status":"ok","readiness":"ready","symbol_count":162}`
- Frontend and backend both running during all tests

### UT-06 — Stock detail page for MU loads with three score cards
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-06-result.png`
- Navigated to http://localhost:3255/stocks/MU
- Three score cards visible: Leadership (grade A, score 94.58, "Proven"), Entry Quality (grade E, score 23.66, "Not yet proven"), Risk (grade E, score 53.11, "Not yet proven")
- No blank screen, no 404, no error message

### UT-07 — Leadership "Why proven?" toggle expands proof panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-07-panel-open.png`
- Clicked "Why proven?" button on Leadership card
- Proof panel expanded; DOM link count increased from 15 to 16 (evidence of new link appearing in panel)
- Panel contains "PASS", "+6.36%", "leadership_score", "registered 2026-06-30"
- "Why proven?" button still present and visible after panel opened

### UT-08 — Expanded proof panel displays correct OOS evidence values
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-08-proof-panel.png`
- PASS verdict: "OUT-OF-SAMPLE TEST PASS" ✓
- Holdout edge: "holdout edge +6.36%" ✓
- P-value: "p = 0.0004998" (≈ 0.0005 as specified) ✓
- Cohort size: "Sealed holdout cohort: 12,297 observations" ✓
- Benchmark control: "+6.36% vs SPY (benchmark control)" ✓
- Claim id: "leadership_score · registered 2026-06-30" ✓
- Registration date: "registered 2026-06-30" ✓

### UT-09 — "View backing evidence row" link navigates to evidence anchor
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-09-evidence-page.png`
- Link "View backing evidence row →" found with href http://localhost:3255/evidence#signal-leadership_score
- After click: browser URL became http://localhost:3255/evidence#signal-leadership_score
- Evidence page rendered with heading "Evidence" and leadership_score claim row visible with PASS, +6.36%, SPY benchmark, 2026-06-30

### UT-10 — Entry Quality score card has no "Why proven?" toggle
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-06-result.png`
- On /stocks/MU, only 1 "Why proven?" button exists in the entire page DOM
- That single button belongs to the Leadership card only
- Entry Quality card shows "Not yet proven" badge only; no button, no toggle, no drill-down element

### UT-11 — Risk score card has no "Why proven?" toggle
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-06-result.png`
- On /stocks/MU, only 1 "Why proven?" button exists — confirmed with JS: `whyProvenCount: 1`
- Risk card shows "Not yet proven" badge only; no button, no toggle, no drill-down element
- Styling identical to Entry Quality card

### UT-12 — Evidence ledger page loads with leadership_score row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-12-evidence-page.png`
- Navigated to http://localhost:3255/evidence
- Page rendered with heading "Evidence" and subtitle about the certified-claims ledger
- leadership_score claim row visible with PASS verdict, +6.36% holdout edge
- No 404, no error state, no blank screen

### UT-13 — leadership_score claim row shows all five required evidence fields
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-12-evidence-page.png`
- Hypothesis: "decile=10 direction=positive factor=leadership_score horizon=20 kind=factor slice_kind=decile" (non-empty) ✓
- OOS verdict: "PASS · holdout edge +6.36%" ✓
- Holdout edge: "+6.36%" ✓
- Benchmark: "CONTROL COMPARISON (VS SPY) +6.36%" ✓
- Registration date: "REGISTRATION DATE 2026-06-30" ✓
- No blank or "N/A" placeholder fields

### UT-14 — "Backs: Stocks leaderboard" link returns to /stocks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-14-back-to-stocks.png`
- Found "Backs: Stocks leaderboard →" link on /evidence page with href http://localhost:3255/stocks
- After click: browser navigated to http://localhost:3255/stocks
- Leaderboard loaded with 120 rows; Leadership column showing "Proven" chips on all rows

### UT-15 — "Proven" badge visually distinct from "Not yet proven" badges
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-15-badge-comparison.png`
- "Proven" chip computed color: rgb(79, 209, 197) — bright teal/green accent
- "Not yet proven" chip computed color: rgb(91, 102, 119) — muted blue-grey
- CSS class difference: Proven uses `border-accent bg-surface-` while Not yet proven uses `border-border bg-surface-2`
- Distinction is immediately visible without clicking — two clearly different colors side by side

### UT-16 — Evidence proof drill-down discoverable within 2 clicks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-3-evidence/UT-16-2click-proof.png`
- Starting from /stocks leaderboard
- Click 1: Clicked "MU" link → navigated to http://localhost:3255/stocks/MU
- Click 2: Clicked "Why proven?" button → proof panel expanded at /stocks/MU
- Panel confirmed showing: PASS=true, +6.36%=true, p=0.0004998=true, 12,297=true, vs SPY=true
- No additional navigation steps required

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255/api/health (status: ok, readiness: ready)
- **Browser:** Chrome via MCP (Chrome DevTools at 127.0.0.1:9222)
- **Test Date:** 2026-06-30
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-3-evidence/`

### Service Notes

- Backend (port 8255) was not running at test start; started manually with `CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255 bash scripts/start-backend.sh`. /api/health returned `{"status":"ok","readiness":"ready","symbol_count":162}` before tests ran.
- Frontend (port 3255) was already running on a pre-built Next.js production bundle (`next start`).
- No test results were affected by service start order — all 16 tests ran with both services live.
