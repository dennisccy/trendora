# Phase goal-mcp-loop-iter-11 — UI Test Results

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 15/15 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab page loads without errors | smoke | P1 | Table of factors visible, Evidence column header present | 11 factors rendered, "Evidence (D10 · per horizon)" column visible | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-01-result.png` |
| UT-02 | Evidence page loads with five claim rows | smoke | P1 | 5 claim rows visible | 5 PASS/FAIL status badges confirmed (PASS, PASS, FAIL, PASS, PASS) | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-02-initial.png` |
| UT-03 | Evidence column header reads "Evidence (D10 · per horizon)" | happy-path | P1 | Exact header text "Evidence (D10 · per horizon)" | textContent = "Evidence (D10 · per horizon)" exactly | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-03-header.png` |
| UT-04 | vcp_contraction h60 chip shows "Proven" with correct link | happy-path | P1 | 60d chip: "Proven", link to /evidence#factor-vcp_contraction-d10-h60 | data-proven="true", href="/evidence#factor-vcp_contraction-d10-h60", tag=A | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-04-UT-07-vcp-chips.png` |
| UT-05 | New vcp_contraction h60 evidence row shows all required fields | happy-path | P1 | Title, subtitle "60-day hold", PASS, +8.91%, date, Pending, linkback | All fields present: PASS, +8.91%, 2026-07-01, "Pending — monitored as new data matures", "Backs: Research factor lab →" | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-05-h60-row.png` |
| UT-06 | Clicking h60 "Proven" chip navigates to evidence h60 anchor | happy-path | P1 | URL ends with #factor-vcp_contraction-d10-h60 | URL = http://localhost:3255/evidence#factor-vcp_contraction-d10-h60 | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-06-after-click.png` |
| UT-07 | vcp_contraction h1/h5/h10 chips show "Not yet proven" without links | validation | P2 | All three chips: "Not yet proven", no href, no link | h1/h5/h10: data-proven="false", tag=DIV, no href | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-04-UT-07-vcp-chips.png` |
| UT-08 | Factor with no certified claims shows 5 "Not yet proven" chips | validation | P2 | 5 chips, all "Not yet proven", no links | Moving-average stack: 5 chips, all "Not yet proven", hasLinks=false | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-14-chips-visible.png` |
| UT-09 | Factor Lab shows error state when backend unavailable | error | P2 | Error indicator shown instead of blank page | "Backend unavailable" panel with descriptive text, no blank screen or JS crash | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-09-backend-unavailable.png` |
| UT-10 | vcp_contraction h20 chip still shows "Proven" linking to h20 anchor | regression | P1 | h20: "Proven", /evidence#factor-vcp_contraction-d10-h20 | href="/evidence#factor-vcp_contraction-d10-h20", data-proven="true", data-horizon="20" | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-10-UT-11-h20-chips.png` |
| UT-11 | leadership_score h20 chip still shows "Proven" | regression | P1 | h20: "Proven", /evidence#signal-leadership_score | href="/evidence#signal-leadership_score", data-proven="true", data-horizon="20" | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-10-UT-11-h20-chips.png` |
| UT-12 | Four prior evidence rows render correctly and are unchanged | regression | P1 | All 4 prior rows present with correct statuses | leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS — no 60-day in h20 subtitle | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png` |
| UT-13 | vcp_contraction h20 evidence row subtitle does not reference "60-day" | regression | P1 | h20 subtitle contains no "60-day" or "h60" | h20 subtitle: "Out-of-sample edge — factor top decile" (no 60-day); h60 subtitle: "…· 60-day hold" | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png` |
| UT-14 | All five horizon chips visible and labeled in a factor row | ux | P2 | 5 chips per row labeled 1d/5d/10d/20d/60d | data-horizon=[1,5,10,20,60] confirmed, chip labels "1d"–"60d" visible in text | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-14-chips-visible.png` |
| UT-15 | "Backs: Research factor lab →" linkback is clickable and navigates | ux | P2 | Click navigates to /research/factor-lab | Click on "Backs: Research factor lab →" navigated to http://localhost:3255/research/factor-lab, page loaded | PASS | `reports/qa/goal-mcp-loop-iter-11-evidence/UT-06-after-click.png` |

---

## Passed Tests

### UT-01 — Factor Lab page loads without errors

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-01-result.png`
- Navigated to http://localhost:3255/research/factor-lab; page loaded with 11 factor rows in the table.
- The factor table rendered with columns including "Evidence (D10 · per horizon)".
- Backend health badge shows "Ready". No blank screen, no red error, no spinner stuck indefinitely.
- Note: Initial load required backend pre-warm (factor-lab?all=true computation ~90s); subsequent load served from cache in <5s.

---

### UT-02 — Evidence page loads with five claim rows

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-02-initial.png`
- Navigated to http://localhost:3255/evidence; page loaded immediately.
- Confirmed 5 status badges: PASS (leadership_score), PASS (Breakout-watch setup), FAIL (ma_stack), PASS (vcp_contraction h20), PASS (vcp_contraction h60).
- No blank screen or error message.

---

### UT-03 — Evidence column header reads "Evidence (D10 · per horizon)"

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-03-header.png`
- `Array.from(document.querySelectorAll('th')).map(th => th.textContent.trim())` returned "Evidence (D10 · per horizon)" as the second header (index 1).
- The header does NOT read "Evidence (D10 · 20d)".
- CSS `text-transform: uppercase` renders it visually as "EVIDENCE (D10 · PER HORIZON)" but the underlying textContent is exact.

---

### UT-04 — vcp_contraction h60 chip shows "Proven" and links to the h60 evidence anchor

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-04-UT-07-vcp-chips.png`
- JS eval on the vcp_contraction row: `a[data-proven="true"][data-horizon="60"]` found with `href="/evidence#factor-vcp_contraction-d10-h60"`, text="60dProven", tag=A (clickable link).
- data-proven="true" attribute confirmed.

---

### UT-05 — New vcp_contraction h60 evidence row shows all required fields

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-05-h60-row.png`
- Row title: "vcp_contraction — top decile (D10)" ✓
- Subtitle: "Out-of-sample edge — factor top decile · 60-day hold" (contains "60-day hold") ✓
- Status: "PASS" ✓
- OUT-OF-SAMPLE VERDICT: "PASS · holdout edge +8.91%" ✓
- CONTROL COMPARISON (VS SPY): "+8.91%" ✓
- REGISTRATION DATE: "2026-07-01" (not blank) ✓
- FORWARD-WALK SCORE-TO-DATE: "Pending — monitored as new data matures" ✓
- Link "Backs: Research factor lab →" present with href="/research/factor-lab" ✓

---

### UT-06 — Clicking h60 "Proven" chip navigates to evidence h60 anchor

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-06-after-click.png`
- Clicked `a[data-proven="true"][data-horizon="60"]` on the vcp_contraction row in the factor-lab table.
- `window.location.href` became `http://localhost:3255/evidence#factor-vcp_contraction-d10-h60`.
- Evidence page loaded (heading "Evidence", 16 links); no 404, no blank page.

---

### UT-07 — vcp_contraction h1/h5/h10 chips show "Not yet proven" without links

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-04-UT-07-vcp-chips.png`
- JS eval result for vcp_contraction row chips:
  - h1: data-proven="false", tag=DIV, href=null ✓
  - h5: data-proven="false", tag=DIV, href=null ✓
  - h10: data-proven="false", tag=DIV, href=null ✓
- None of the three chips is a hyperlink; no URL appears and clicking does not navigate.

---

### UT-08 — A factor with no certified claims shows exactly five "Not yet proven" chips

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-14-chips-visible.png`
- Checked "Moving-average stack" row (ma_stack — factor with only a FAIL entry, not certified).
- Result: count=5, all texts="Not yet proven", hasLinks=false.
- Exactly 5 chips, none a hyperlink.

---

### UT-09 — Factor Lab shows error state when backend unavailable

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-09-backend-unavailable.png`
- Captured at test start when the backend was unavailable (port 8255 not responding).
- Page displayed: panel with "Backend unavailable" heading and message "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- No blank white screen; no unhandled JS error; page navigation remained functional.
- Backend readiness badge showed "Backend unavailable" (red badge, not a page crash).

---

### UT-10 — vcp_contraction h20 chip still shows "Proven" linking to h20 anchor

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-10-UT-11-h20-chips.png`
- JS eval: all h20 proven links found 2 entries.
- vcp_contraction row: href="/evidence#factor-vcp_contraction-d10-h20", data-proven="true", data-horizon="20" ✓
- Does NOT link to #factor-vcp_contraction-d10-h60 ✓

---

### UT-11 — leadership_score h20 chip still shows "Proven"

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-10-UT-11-h20-chips.png`
- Leadership score row: href="/evidence#signal-leadership_score", data-proven="true", data-horizon="20" ✓
- Uses signal anchor (not cohort anchor), as required ✓

---

### UT-12 — Four prior evidence rows render correctly and are unchanged

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png`
- leadership_score: status PASS, holdout +6.36% ✓
- Breakout-watch setup: status PASS, holdout +6.12% ✓
- ma_stack: status FAIL, holdout +2.62% ✓
- vcp_contraction h20: status PASS, holdout +3.33%, subtitle "Out-of-sample edge — factor top decile" (no "60-day") ✓
- All four rows present; order unchanged.

---

### UT-13 — vcp_contraction h20 evidence row subtitle does not reference "60-day"

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png`
- JS eval: `h20Contains60day=false`, `h60Contains60day=true`.
- h20 row text excerpt: "PASSvcp_contraction — top decile (D10)Backs: Research factor lab →Out-of-sample edge — factor top de…" — no "60-day" text ✓
- h60 row has "Out-of-sample edge — factor top decile · 60-day hold" ✓

---

### UT-14 — All five horizon chips visible and labeled in a factor row

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-14-chips-visible.png`
- data-horizon attributes on vcp_contraction row: [1, 5, 10, 20, 60] — exactly 5 chips.
- Chip text combines the label ("1d", "5d", etc.) with the status ("Not yet proven" / "Proven").
- All chips visually distinct and individually readable in screenshot.
- Chip strip fits within the Evidence column (no overflow observed).

---

### UT-15 — "Backs: Research factor lab →" linkback is clickable and navigates

**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-11-evidence/UT-06-after-click.png`
- On the h60 vcp_contraction evidence row, JS eval found link "Backs: Research factor lab →" with href="/research/factor-lab".
- Clicked the link; browser navigated to http://localhost:3255/research/factor-lab.
- Factor Lab page loaded (heading "Research — Factor Lab", 20 interactive elements including factor table rows).

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (superpowers-chrome 3.0.1)
- **Test Date:** 2026-07-01
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-11-evidence/`
- **Note:** Backend required manual restart and pre-warm of `/api/research/factor-lab?all=true` (heavy computation, ~90s on cold start; cached for subsequent requests). All tests were executed after the backend was confirmed ready.
