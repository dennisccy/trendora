# Phase goal-mcp-loop-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-8
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (the `/api/evidence` endpoint must return 4 certified-claims entries)
- No login required

---

## Verification Steps

1. Navigate to `http://localhost:3255/research/factor-lab` in your browser
   - **Expect:** The Research factor lab page loads, a factors table is visible, and a column header reading exactly **"Evidence (D10 · 20d)"** appears in the table header row

2. Scroll down in the factors table to find the **vcp_contraction** row. Look at the "Evidence (D10 · 20d)" cell on that row
   - **Expect:** A chip reading exactly **"Proven"** is visible in that cell. The chip uses a green/accent color and shows a ShieldCheck icon. It appears as a clickable link (underline or pointer cursor on hover)

3. Click the **"Proven"** chip on the vcp_contraction row
   - **Expect:** Browser navigates to `http://localhost:3255/evidence#factor-vcp_contraction-d10-h20`. The Evidence page loads and the vcp_contraction claim row is already scrolled into view — you should see it without manually scrolling. The vcp_contraction factor row on the factor lab was NOT expanded or collapsed by this click

4. On the `/evidence` page, read the vcp_contraction row (the bottom-most claim row). Verify the following are visible in that row: title **"vcp_contraction — top decile (D10)"**, holdout edge **"+3.33%"**, p-value **"0.01149"**, control label **"vs SPY"**, registration date **"2026-06-30"**, and linkback text **"Backs: Research factor lab →"**
   - **Expect:** All six items above are present on the row. If any field is missing or shows a different number, the row is incorrect

5. Click **"Backs: Research factor lab →"** on the vcp_contraction row
   - **Expect:** Browser navigates to `http://localhost:3255/research/factor-lab`. The factors table is visible with the "Evidence (D10 · 20d)" column and the vcp_contraction "Proven" badge intact — confirming the round-trip works

6. On the factor lab page, scroll to the **ma_stack** row. Look at its "Evidence (D10 · 20d)" cell
   - **Expect:** The badge reads exactly **"Not yet proven"** in a muted/grey color with no underline. Clicking it does nothing (no navigation). This confirms that a rejected edge is honestly labeled

7. Navigate to `http://localhost:3255/stocks`
   - **Expect:** The stocks leaderboard loads. The Leadership score column shows a **"Proven"** badge. Entry Quality and Risk columns show **"Not yet proven"** badges. The text "vcp_contraction" does NOT appear anywhere on this page — the vcp_contraction edge backs the factor lab only, not per-stock scores

8. Click on the first stock ticker in the leaderboard to open its detail page at `/stocks/{ticker}`. Locate the Leadership score section and click the "Proven" badge to expand the proof panel
   - **Expect:** The proof drill-down panel opens showing an out-of-sample test result, a "vs SPY" control comparison label, and a registration date — same content as before this iteration's changes

---

## What "Working Correctly" Looks Like

- The factor lab table has a visible "Evidence (D10 · 20d)" column — every factor row has a badge in this column
- The vcp_contraction row shows an accent-colored "Proven" chip that navigates to the Evidence page on click
- The Evidence page has four claim rows; the vcp_contraction row is the fourth and shows +3.33%, p 0.01149, and "Backs: Research factor lab →"
- The `/stocks` page has no mention of vcp_contraction — this edge backs the factor lab only

## Common Issues

- **"Evidence (D10 · 20d)" column not visible:** Backend `/api/evidence` may be unavailable. Run `curl http://localhost:8000/api/evidence` to verify it returns JSON with a `claims` array of length 4. If it returns an error, restart the backend
- **vcp_contraction badge shows "Not yet proven" instead of "Proven":** The frontend may have loaded before the backend was ready. Hard-refresh the factor lab page (`Ctrl+Shift+R` or `Cmd+Shift+R`)
- **vcp_contraction row missing from /evidence:** Navigate to `http://localhost:3255/evidence` and scroll to the very bottom — the row is the last entry and may be below the fold
- **Blank page or error screen on any route:** Check that both frontend (port 3255) and backend are running
