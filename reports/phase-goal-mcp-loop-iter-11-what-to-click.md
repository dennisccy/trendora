# Phase goal-mcp-loop-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-11
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (verify with: `curl http://localhost:8000/health` — should return 200)
- No special login or seed data required — the evidence data is loaded from the application's built-in certified-claims file

---

## Verification Steps

1. Navigate to `http://localhost:3255/research/factor-lab` in your browser
   - **Expect:** The factor table loads with at least one visible row. The Evidence column header reads **"Evidence (D10 · per horizon)"** — if it still reads "Evidence (D10 · 20d)", the column header update did not apply.

2. In the factor table, find the `vcp_contraction` row and look at the Evidence column
   - **Expect:** The Evidence column for that row shows **5 chips** (one for each horizon: 1d, 5d, 10d, 20d, 60d). If you only see 1 chip, the per-horizon strip did not render.

3. On the `vcp_contraction` row, check the **60d chip** (the fifth chip in the strip)
   - **Expect:** The chip reads **"Proven"** (with or without a checkmark). It should appear as a clickable link — hovering shows a URL in the browser status bar. If it reads "Not yet proven" or shows no text, the h60 certified claim is not being picked up.

4. Click the 60d **"Proven"** chip on the `vcp_contraction` row
   - **Expect:** Browser navigates to `http://localhost:3255/evidence#factor-vcp_contraction-d10-h60`. The Evidence page opens and the URL in the address bar ends with `#factor-vcp_contraction-d10-h60`. If you land on a 404 or the page loads without that anchor, the deep-link is broken.

5. On the Evidence page, locate the **fifth claim row** — it should be titled "vcp_contraction — top decile (D10)" with a subtitle containing the text **"60-day hold"**
   - **Expect:** The row shows status **"PASS"**, holdout edge **"+8.91%"**, SPY comparison **"+8.91%"**, and forward-walk **"Pending"**. If no fifth row exists, or the row lacks any of those fields, the h60 claim is not being rendered.

6. On the Evidence page, locate the **earlier `vcp_contraction` row** (the 20-day one — it appears before the 60-day row)
   - **Expect:** Its subtitle refers to the **20-day** horizon (not 60-day). The status is "PASS". If the subtitle now says "60-day hold", the h20 subtitle was incorrectly overwritten.

7. Navigate back to `http://localhost:3255/research/factor-lab`; find the `vcp_contraction` row and check the **20d chip** (the fourth chip in the strip)
   - **Expect:** The 20d chip reads **"Proven"** and links to `/evidence#factor-vcp_contraction-d10-h20`. If it now links to h60 or has no link, the h20 regression guard failed.

8. On the Factor Lab, find the `leadership_score` row and check its **20d chip**
   - **Expect:** The 20d chip reads **"Proven"**. If it reads "Not yet proven", a prior claim regressed.

9. On the Factor Lab, find the `vcp_contraction` row again and check the **1d, 5d, and 10d chips**
   - **Expect:** All three chips read **"Not yet proven"** and none of them is a link (hovering shows no URL). If any of the three reads "Proven", an uncertified horizon is being incorrectly promoted.

10. Navigate to `http://localhost:3255/evidence` and count the total number of claim rows
    - **Expect:** Exactly **5 rows** are listed. The first four (leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS) are unchanged. If you see fewer than 5 rows, or the ma_stack row no longer reads "FAIL", a prior claim was altered.

---

## What "Working Correctly" Looks Like

- The Factor Lab Evidence column header reads "Evidence (D10 · per horizon)" (not the old "Evidence (D10 · 20d)")
- Every factor row in the Factor Lab shows a strip of 5 evidence chips
- The `vcp_contraction` 60d chip is a "Proven" link; its 1d, 5d, and 10d chips are non-linked "Not yet proven"
- The `vcp_contraction` 20d chip remains "Proven" linking to the h20 anchor (unchanged from before)
- The Evidence page shows exactly 5 rows; the new h60 row has "+8.91%" and "Pending"; the prior 4 rows are byte-for-byte unchanged

## Common Issues

- **Evidence column still shows one chip per row**: The frontend asset cache may be stale — hard-refresh with Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- **h60 "Proven" chip does not appear on vcp_contraction**: Confirm the backend is running and serving the h60 claim — run `curl -s http://localhost:8000/api/evidence | grep '"horizon": 60'` in a terminal; if no output, the h60 entry is missing from certified-claims.jsonl
- **Evidence page shows only 4 rows**: Same backend check as above — the frontend renders rows from the API response; if the API returns 4, the frontend will show 4
- **Clicking the 60d chip does nothing or shows a broken link**: Check that the href attribute on the chip element is `/evidence#factor-vcp_contraction-d10-h60` — inspect via DevTools → Elements → find the chip element → check the `href` attribute
