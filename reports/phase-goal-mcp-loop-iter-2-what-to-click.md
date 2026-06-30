# Phase goal-mcp-loop-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (the Evidence API must be reachable — the "Proven" badge reads from it)
- No login required — the app is publicly accessible

---

## Verification Steps

1. Navigate to `http://localhost:3255/stocks`
   - **Expect:** The Stocks leaderboard table loads with at least one stock row visible. The "Leadership" column badge on the first stock row reads "Proven" in a green accent chip — not "Not yet proven". The Entry Quality and Risk column badges on the same row read "Not yet proven" in muted/gray styling.
   - **Broken if:** Leadership also reads "Not yet proven", or the page shows a blank screen or error.

2. Click the green "Proven" badge in the Leadership column of any stock row
   - **Expect:** Browser navigates to `http://localhost:3255/evidence#signal-leadership_score`. The Evidence page loads and the `leadership_score` claim row is visible in the viewport (you do not need to scroll to find it).
   - **Broken if:** Navigation goes to `/evidence` without the `#signal-leadership_score` fragment, or the page is blank.

3. On the Evidence page, confirm the leadership_score claim row has all five data fields populated
   - **Expect:** The row shows: (1) a hypothesis description mentioning "leadership_score", (2) a "PASS" verdict chip with "+6.36% edge" and "p ≈ 0.0005", (3) a "+6.36% vs SPY" control comparison, (4) the registration date "2026-06-30", and (5) a forward-walk status such as "Pending". None of these fields are blank.
   - **Broken if:** Any field is empty, shows "N/A", or the row itself is missing.

4. Click "Backs: Stocks leaderboard →" within the leadership_score claim row
   - **Expect:** Browser navigates back to `http://localhost:3255/stocks` and the leaderboard table renders with stock rows.
   - **Broken if:** The link is missing, navigates to an error page, or the leaderboard is blank.

5. From the leaderboard, click on any stock ticker to open its detail page
   - **Expect:** The stock detail page opens at `http://localhost:3255/stocks/{ticker}`. The Leadership score card is visible and shows a "Proven" badge. Directly below or adjacent to the badge, a "Why proven?" button is visible with a chevron indicating it can be expanded.
   - **Broken if:** The Leadership badge reads "Not yet proven", or the "Why proven?" button is absent.

6. Click the "Why proven?" button on the Leadership score card
   - **Expect:** A proof panel expands in place beneath the button. The panel shows: a "PASS" chip; a holdout edge reading "+6.36%"; a p-value reading "0.0004998" (or "p ≈ 0.0005"); a control comparison reading "+6.36% vs SPY (benchmark control)"; and a certified claim line reading "leadership_score · registered 2026-06-30".
   - **Broken if:** Panel does not expand, values are blank, or values differ from the above (e.g., 0.00% or wrong date).

7. Within the expanded proof panel, click "View backing evidence row →"
   - **Expect:** Browser navigates to `http://localhost:3255/evidence#signal-leadership_score`. The evidence page loads and the leadership_score claim row is visible without scrolling.
   - **Broken if:** Link is missing, navigates to the wrong URL, or the anchor is not visible in the viewport.

8. Navigate back to the stock detail page and check Entry Quality and Risk score cards
   - **Expect:** Navigate to `http://localhost:3255/stocks/{ticker}` (any ticker). The Entry Quality score card shows a "Not yet proven" badge with no "Why proven?" button or expandable panel below it. The Risk score card also shows "Not yet proven" with no expand control.
   - **Broken if:** Either Entry Quality or Risk shows "Proven", or a "Why proven?" toggle appears on either card.

---

## What "Working Correctly" Looks Like

- The Leadership "Proven" badge appears in accent green on both the leaderboard and every stock detail page
- The "Why proven?" panel expands to show real numbers: "+6.36% edge", "p 0.0004998", "+6.36% vs SPY", and the date "2026-06-30"
- All navigation links form a closed loop: leaderboard → detail → proof panel → evidence → leaderboard, with no broken steps

## Common Issues

- **Leadership badge still reads "Not yet proven":** The backend `GET /api/evidence` may not be returning the certified claim. Verify the backend is running and `runs/goal-session-mcp-loop/state/certified-claims.jsonl` exists and contains a PASS entry.
- **Proof panel is missing on the Leadership card:** The frontend may not have deployed the new `ScoreProofPanel` component. Hard-refresh the page (Ctrl+Shift+R / Cmd+Shift+R) and try again.
- **Evidence page is blank or shows no claim rows:** Navigate directly to `http://localhost:3255/evidence` and check if the page renders at all. If blank, the backend API may be unreachable.
- **"View backing evidence row →" link does not scroll to the claim:** Ensure the URL includes the `#signal-leadership_score` fragment. If the anchor is missing from the URL, the component may not be passing it correctly.
