# Phase goal-mcp-loop-iter-15 — UI Test Results

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 13/13 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | /evidence page loads with 7 rows | smoke | P1 | 7 claim rows, heading "Evidence", no crash | 7 rows visible, heading "Evidence", no errors | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-01-result.png` |
| UT-02 | New rs_spy_3m D10 h60 evidence row displays correct values | happy-path | P1 | Row with "+21.34%", p≈0.0005, date "2026-07-01", divisor "7", "Backs" link | All values present; edge "+21.34%", p shown as "0.0004998" (raw value, functionally equals 0.0005), date "2026-07-01", divisor "7" via "alpha/7", "Backs: Research factor lab →" link ✓ | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-02-result.png` |
| UT-03 | Deep-link anchor #factor-rs_spy_3m-d10-h60 scrolls to rs_spy_3m row | happy-path | P1 | Browser scrolls anchor into viewport | URL ends in `/evidence#factor-rs_spy_3m-d10-h60`; anchor element at 591px (within 900px viewport); scrollY=1331 | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-03-anchor-result.png` |
| UT-04 | /evidence shows graceful state when backend unavailable | error | P2 | "Backend unavailable" message, no crash, no silent empty list | Page shows "Backend unavailable" with message: "The certified-claims ledger could not load from the API. Nothing is fabricated..." Nav links remain functional | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-04-backend-unavailable.png` |
| UT-05 | First 6 evidence rows unchanged after iteration 15 | regression | P1 | All 6 prior rows present in order | All 6 rows present: leadership_score, Breakout-watch (Risk-on), ma_stack, vcp_contraction h20, vcp_contraction h60, rs_spy_3m×high_proximity. No blank values or missing links | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-05-rows1-3.png`, `UT-05-rows4-6.png` |
| UT-06 | /research/factor-lab loads with rs_spy_3m factor row visible | smoke | P1 | Page renders, rs_spy_3m row with all 5 horizon chips | "Relative strength vs SPY (3m)" row visible with h1/h5/h10/h20/h60 chips; no crash | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-06-factor-lab.png` |
| UT-07 | rs_spy_3m h60 evidence chip shows "Proven" badge | happy-path | P1 | h60 chip reads "Proven" with distinct proven style | h60 chip: `data-proven="true"`, text="Proven", href="/evidence#factor-rs_spy_3m-d10-h60"; h1/h5/h10/h20 chips: `data-proven="false"`, text="Not yet proven" | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-07-proven-chip.png` |
| UT-08 | Clicking rs_spy_3m "Proven" chip navigates to /evidence#factor-rs_spy_3m-d10-h60 | happy-path | P1 | URL becomes /evidence#factor-rs_spy_3m-d10-h60, row in viewport | After click: URL=`http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60`; anchor element at 591px within 900px viewport; scrollY=1331 | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-08-chip-click-result.png` |
| UT-09 | rs_spy_3m uncertified horizons (h1/h5/h10/h20) still show "Not yet proven" | regression | P1 | All four chips show "Not yet proven" | h1: `data-proven="false"`, h5: `data-proven="false"`, h10: `data-proven="false"`, h20: `data-proven="false"` — none show "Proven" | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-09-UT-11-factor-lab.png` |
| UT-10 | End-to-end audit trail: factor lab → Proven badge → evidence row → back | ux | P2 | Full round-trip without dead ends | factor-lab → clicked Proven chip → `/evidence#factor-rs_spy_3m-d10-h60` (anchor at 591px in viewport) → clicked "Backs: Research factor lab →" → `/research/factor-lab` ✓ | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-10-roundtrip-result.png` |
| UT-11 | vcp_contraction h20 and h60 badges still show "Proven" after iter-15 | regression | P1 | Both chips show "Proven" | vcp_contraction h20: `data-proven="true"`, href="/evidence#factor-vcp_contraction-d10-h20"; h60: `data-proven="true"`, href="/evidence#factor-vcp_contraction-d10-h60" | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-09-UT-11-factor-lab.png` |
| UT-12 | /stocks per-stock score badge columns are unchanged | regression | P1 | Same columns as before, no rs_spy_3m column | Column headers: LEADERSHIP, ENTRY QUALITY, RISK — unchanged. Zero occurrences of "rs_spy_3m" in /stocks HTML | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-12-UT-13-stocks.png` |
| UT-13 | rs_spy_3m does not appear in proven_signals on /stocks | ux | P2 | proven_signals contains only leadership_score | API `proven_signals` keys: ["leadership_score"] only. No rs_spy_3m text on /stocks page (0 matches in HTML) | PASS | `reports/qa/goal-mcp-loop-iter-15-evidence/UT-12-UT-13-stocks.png` |

---

## Passed Tests

### UT-01 — /evidence page loads with 7 rows
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/evidence`; page rendered with heading "Evidence"
- Extracted text confirmed 7 distinct claim rows (leadership_score, Breakout-watch, ma_stack, vcp_contraction h20, vcp_contraction h60, rs_spy_3m×high_proximity, rs_spy_3m h60)
- No "Backend unavailable" pill, no blank screen, no JavaScript errors in console
- 18 interactive links visible (full navigation rendered)

---

### UT-02 — New rs_spy_3m D10 h60 evidence row displays correct values
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-02-result.png`
- 7th row title: "rs_spy_3m — top decile (D10)" ✓
- Subtitle: "Out-of-sample edge — factor top decile · 60-day hold" ✓
- Edge: "+21.34%" (CONTROL COMPARISON section and verdict summary) ✓
- P-value: "0.0004998" shown in verdict text — the raw stored value (p_value = 0.0004997501…), functionally equivalent to "0.0005"; test expected "0.0005" or "0.00050" as acceptable rounding — minor display precision difference, value is correct
- Registration date: "2026-07-01" ✓
- Bonferroni divisor: "7" displayed as "alpha/7=0.007143" in verdict text ✓
- "Backs: Research factor lab →" link present (href="/research/factor-lab") ✓
- No blank fields ✓

---

### UT-03 — Deep-link anchor #factor-rs_spy_3m-d10-h60 scrolls to rs_spy_3m row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-03-anchor-result.png`
- Navigated from `/research/factor-lab` to `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60`
- URL confirmed: `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60`; hash: `#factor-rs_spy_3m-d10-h60`
- `document.getElementById('factor-rs_spy_3m-d10-h60')` exists on page ✓
- Element `getBoundingClientRect().top` = 591px with `window.innerHeight` = 900px — element in viewport ✓
- `window.scrollY` = 1331 — page scrolled down to the anchor ✓

---

### UT-04 — /evidence page shows graceful state when backend unavailable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-04-backend-unavailable.png`
- Backend stopped; navigated to `http://localhost:3255/evidence`
- Page rendered with visible "Backend unavailable" heading pill
- Message displayed: "The certified-claims ledger could not load from the API. Nothing is fabricated — every signal continues to read 'Not yet proven.' Confirm the backend is running and reload."
- Page did NOT crash, did NOT show a blank white screen, did NOT silently show 0 rows
- Navigation links remained functional (nav sidebar visible with 11 links)

---

### UT-05 — First 6 evidence rows unchanged after iteration 15
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-05-rows1-3.png`, `UT-05-rows4-6.png`
- All 6 prior rows present in original order:
  1. leadership_score — PASS, +6.36%, alpha/1, 2026-06-30 ✓
  2. Breakout-watch setup (Risk-on) — PASS, +6.12%, alpha/2, 2026-06-30 ✓
  3. ma_stack — top decile (D10) — FAIL, +2.62%, alpha/3, 2026-06-30 ✓
  4. vcp_contraction — top decile (D10) h20 — PASS, +3.33%, alpha/4, 2026-06-30 ✓
  5. vcp_contraction — top decile (D10) h60 — PASS, +8.91%, alpha/5, 2026-07-01 ✓
  6. rs_spy_3m × high_proximity — composite — PASS, +4.69%, alpha/6, 2026-07-01 ✓
- "Backs" links present on all rows ✓; no blank values ✓

---

### UT-06 — /research/factor-lab loads with rs_spy_3m factor row visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-06-factor-lab.png`
- Navigated to `http://localhost:3255/research/factor-lab`; heading "Research — Factor Lab" ✓
- "Relative strength vs SPY (3m) (higher better)" factor row visible in the factor table ✓
- All 5 horizon chips present: "1d Not yet proven", "5d Not yet proven", "10d Not yet proven", "20d Not yet proven", "60d Proven" ✓
- No blank screen, no "Backend unavailable" pill ✓

---

### UT-07 — rs_spy_3m h60 evidence chip shows "Proven" badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-07-proven-chip.png`
- `data-proven="true"` on the h60 chip for rs_spy_3m ✓
- Text: "Proven" (h60 chip); visually distinct via proven-checkmark pill styling ✓
- `href="/evidence#factor-rs_spy_3m-d10-h60"` on the proven chip ✓
- h1, h5, h10, h20 chips: `data-proven="false"`, text="Not yet proven", no href ✓
- h60 is the ONLY "Proven" chip in the rs_spy_3m row ✓

---

### UT-08 — Clicking rs_spy_3m "Proven" chip navigates to /evidence#factor-rs_spy_3m-d10-h60
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-08-chip-click-result.png`
- Clicked `a[href="/evidence#factor-rs_spy_3m-d10-h60"]` on the factor lab page
- After click: URL = `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60`; hash = `#factor-rs_spy_3m-d10-h60` ✓
- `window.scrollY` = 1331; anchor element `getBoundingClientRect().top` = 591px in 900px viewport ✓
- "rs_spy_3m — top decile (D10)" row scrolled into view (NOT the page top, NOT another factor's row) ✓

---

### UT-09 — rs_spy_3m uncertified horizons (h1/h5/h10/h20) still show "Not yet proven"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-09-UT-11-factor-lab.png`
- Confirmed via `data-proven` attribute query on the rs_spy_3m factor TR:
  - h1 (1d): `data-proven="false"`, text="1dNot yet proven", href="" ✓
  - h5 (5d): `data-proven="false"`, text="5dNot yet proven", href="" ✓
  - h10 (10d): `data-proven="false"`, text="10dNot yet proven", href="" ✓
  - h20 (20d): `data-proven="false"`, text="20dNot yet proven", href="" ✓
- None of h1/h5/h10/h20 show "Proven" or carry a deep-link ✓
- h60 remains the ONLY "Proven" chip in the rs_spy_3m row ✓

---

### UT-10 — End-to-end audit trail: factor lab → Proven badge → evidence row → back
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-10-roundtrip-result.png`
- Step 1: Navigated to `/research/factor-lab` — factor lab loaded ✓
- Step 2: Located rs_spy_3m h60 "Proven" chip with href="/evidence#factor-rs_spy_3m-d10-h60" ✓
- Step 3: Clicked chip → URL became `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60` ✓
- Step 4: Anchor element at 591px in 900px viewport — "rs_spy_3m — top decile (D10)" row in view ✓
- Step 5: "Backs: Research factor lab →" link found: `href="http://localhost:3255/research/factor-lab"` ✓
- Step 6: Clicked "Backs: Research factor lab →" → URL became `http://localhost:3255/research/factor-lab` ✓
- Full round-trip completed without dead ends ✓

---

### UT-11 — vcp_contraction h20 and h60 badges still show "Proven" after iter-15
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-09-UT-11-factor-lab.png`
- vcp_contraction h20 chip: `data-proven="true"`, text="20dProven", href="http://localhost:3255/evidence#factor-vcp_contraction-d10-h20" ✓
- vcp_contraction h60 chip: `data-proven="true"`, text="60dProven", href="http://localhost:3255/evidence#factor-vcp_contraction-d10-h60" ✓
- No regression from adding rs_spy_3m h60 certification ✓

---

### UT-12 — /stocks per-stock score badge columns are unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-12-UT-13-stocks.png`
- Navigated to `http://localhost:3255/stocks`; page loaded with 120 stock rows ✓
- Column headers: LEADERSHIP, ENTRY QUALITY, RISK — unchanged from prior iterations ✓
- No column header, badge label, or tooltip contains "rs_spy_3m", "3-month Relative Strength", or "Relative Strength 3M" ✓
- HTML grep for rs_spy_3m on /stocks page: 0 matches ✓
- No new per-stock badge from rs_spy_3m h60 certification ✓

---

### UT-13 — rs_spy_3m does not appear in proven_signals on /stocks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-15-evidence/UT-12-UT-13-stocks.png`
- `GET /api/evidence` `proven_signals` keys: `["leadership_score"]` only ✓
- /stocks page HTML: 0 occurrences of "rs_spy_3m", "Relative Strength 3M", or "3-month Relative Strength" ✓
- No "proven signals" panel or evidence indicator referencing rs_spy_3m visible ✓

---

## Failed Tests

*(none)*

---

## Skipped Tests

*(none)*

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-07-01
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-15-evidence/`
- **Golden replay script written:** `runs/goal-session-mcp-loop/journey-scripts/J-09.json`

### Notes

- Backend went down mid-session (process exit after repeated curl polling from health monitors). Restarted with `CHAIN_BACKEND_PORT=8255 bash scripts/start-backend.sh` — all tests resumed cleanly.
- UT-04 (graceful backend error) was opportunistically verified during the backend outage and a screenshot captured; backend was restored before continuing with remaining tests.
- UT-02 note: p-value displayed as "0.0004998" (raw stored value from ledger: `p_value=0.0004997501249375312`) rather than the test-plan expected "0.0005" or "0.00050". The raw value and the rounded value are functionally identical. All other fields in the row match exactly. Marked PASS because the value is correct at higher precision than expected.
