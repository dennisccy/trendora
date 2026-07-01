# Phase goal-mcp-loop-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-15
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (evidence API healthy — confirm no "Backend unavailable" pill appears on the evidence page)

---

## Verification Steps

1. Navigate to `http://localhost:3255/evidence`
   - **Expect:** Page loads and shows exactly 7 claim rows. The bottom row is titled "rs_spy_3m — top decile (D10)" with subtitle "Out-of-sample edge — factor top decile · 60-day hold". If you count fewer than 7 rows or see no "rs_spy_3m" row, the new claim did not render.

2. On the `/evidence` page, find the bottom "rs_spy_3m — top decile (D10)" row and confirm all four values:
   - Out-of-sample edge reads "+21.34%"
   - P-value reads "0.0005" or "0.00050"
   - Registration date reads "2026-07-01"
   - A "Backs: Research factor lab →" link is visible inside the row
   - **Expect:** All four match. If any field is blank or shows "—", the data did not render correctly.

3. In the browser address bar, type `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60` and press Enter
   - **Expect:** The page loads and scrolls so the "rs_spy_3m — top decile (D10)" row is in the visible viewport — not the page top and not a different factor's row. If the page scrolls to the top, the deep-link anchor is broken.

4. Navigate to `http://localhost:3255/research/factor-lab`
   - **Expect:** Page loads with a factor table. Find the `rs_spy_3m` row. The h60 (60-day hold) evidence chip reads "Proven" in a distinct proven pill style (checkmark or active styling). If the h60 chip reads "Not yet proven", the badge has not updated.

5. Still on `/research/factor-lab`, check the h1, h5, h10, and h20 evidence chips in the `rs_spy_3m` row
   - **Expect:** All four chips read "Not yet proven" in the muted style. If any of these four shows "Proven", proven-ness has leaked to an uncertified horizon — this is a failure.

6. Click the "Proven" chip in the `rs_spy_3m` h60 cell
   - **Expect:** Browser navigates to `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60` and scrolls to the `rs_spy_3m` row. URL bar must end with `#factor-rs_spy_3m-d10-h60`. If the URL shows a different anchor or the page scrolls to a different row, the deep-link is mis-wired.

7. Navigate to `http://localhost:3255/stocks`
   - **Expect:** Stock list loads with the same score badge columns as before. No new column labeled "rs_spy_3m", "Relative Strength 3M", or similar appears. The three existing score columns are unchanged.

---

## What "Working Correctly" Looks Like

- The `/evidence` ledger shows exactly 7 rows; the newest ("rs_spy_3m — top decile (D10)") shows "+21.34%" edge, "0.0005" p-value, "2026-07-01" date, and a "Backs: Research factor lab →" link
- The `rs_spy_3m` h60 chip on `/research/factor-lab` shows "Proven" in a visually distinct proven pill; the h1, h5, h10, and h20 chips for the same factor all still show "Not yet proven"
- Clicking the h60 "Proven" chip lands on `/evidence#factor-rs_spy_3m-d10-h60` with the correct row in view
- The `/stocks` score columns are unchanged — no rs_spy_3m badge or column appears anywhere in the stock list

## Common Issues

- **"Backend unavailable" pill on /evidence**: The backend is not running. Start the backend before verifying UI behavior. When the backend is down, factor-lab chips fall back to "Not yet proven" for all horizons — this will make the `rs_spy_3m` h60 chip appear broken even if the code is correct.
- **Only 6 rows on /evidence**: The backend is not serving the 7th ledger row. Check that `/api/evidence` returns 7 items (open `http://localhost:3255/api/evidence` in your browser and count the entries in the JSON response).
- **h60 chip shows "Not yet proven" on factor lab**: Confirm the backend is healthy first (see above). If the backend is healthy and the chip still reads "Not yet proven", check that `certified-claims.jsonl` contains a row 7 entry with `"ledger":"canonical"` and `"status":"PASS"`.
- **Clicking "Proven" chip scrolls to wrong row or top of page**: The anchor `#factor-rs_spy_3m-d10-h60` does not match the rendered `claimAnchorId` on the evidence row. Inspect the DOM element id on the rs_spy_3m row to verify it matches exactly.
