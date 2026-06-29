# Phase goal-mcp-loop-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (confirm with: `curl http://localhost:8000/health`)
- No specific login credentials required — the app is accessible without authentication
- No seed data required — the leaderboard is populated from the existing backend data

---

## Verification Steps

1. Navigate to `http://localhost:3255/stocks` in your browser
   - **Expect:** The stocks leaderboard loads with rows visible. Each row shows score columns (Leadership, Entry Quality, Risk). Below each score badge you should see a small gray chip labeled "Not yet proven". All three chips must be present on every row — if any chip is missing, that is a failure.

2. Look at the left sidebar navigation menu and find the "Evidence" entry
   - **Expect:** "Evidence" appears directly after "Research" in the sidebar list. It has a shield-and-checkmark icon to its left. If "Evidence" is not in the sidebar, or if it appears before "Research" or at a different position, that is a failure.

3. Click "Evidence" in the left sidebar
   - **Expect:** The browser navigates to `http://localhost:3255/evidence`. The page heading "Evidence" is visible at the top. The "Evidence" sidebar link becomes highlighted/active. A card reading "No certified claims yet" is visible in the main content area — this is the correct empty state.

4. Read the empty state card on the `/evidence` page
   - **Expect:** The card contains the phrase "every signal currently reads Not yet proven". Below that, a bullet list shows exactly these five items: "Hypothesis", "Out-of-sample verdict", "Control comparison (vs SPY)", "Registration date", "Forward-walk score-to-date". If any of the five is missing, that is a failure. If a table of claim rows appears (not just the empty state), that is also a failure.

5. Click the first stock row on the leaderboard (navigate back to `http://localhost:3255/stocks`, then click any row)
   - **Expect:** The browser navigates to a stock detail page at `/stocks/<ticker>`. Three score cards are visible — Leadership, Entry Quality, and Risk. Each score card shows a "Not yet proven" chip directly below the numeric score value. The numeric score value and the score label (e.g., "Leadership") are still visible alongside the chip — the chip is additive and does not replace anything.

6. Confirm the existing score values and labels are unchanged on the detail page
   - **Expect:** Each ScoreCard still shows its numeric score (e.g., "87.3"), its label (e.g., "Leadership"), and any descriptive text below the label — exactly as before this phase. The "Not yet proven" chip appears below the score number and above or beside the description. Nothing from the ScoreCard has been removed.

7. Navigate back to `http://localhost:3255/stocks` and confirm the leaderboard is unchanged
   - **Expect:** Letter-grade badges (e.g., "A", "B+") and numeric scores are visible on every row in all three score columns. The "Not yet proven" chips appear below the letter-grade badges — they do not replace or cover them. Row order is the same as before this phase.

---

## What "Working Correctly" Looks Like

- The `/evidence` page loads with an empty-state card saying "No certified claims yet" — no table of claim rows, no error banner, no spinner that never resolves
- Every stock row on `/stocks` shows three "Not yet proven" chips (one per score column) in a muted gray style — not bright green, not red, not missing
- The "Evidence" sidebar link is visible after "Research" on every page of the app and navigates to `/evidence` in one click
- The stock detail page ScoreCards show both the existing score values and the new "Not yet proven" chips — both coexist, nothing is removed

## Common Issues

- **"Evidence" not in sidebar**: Check that the frontend build is current. If running in dev mode, confirm the dev server restarted after the frontend changes.
- **Chips missing from leaderboard rows**: This usually means the evidence API call failed silently. Open browser DevTools (F12) > Console — look for any network errors on `/api/evidence`. Confirm the backend is running and the `/api/evidence` endpoint responds with HTTP 200.
- **Evidence page is blank or shows an error card**: Confirm the backend is running (`curl http://localhost:8000/api/evidence`). If the response is `{"claims":[], "proven_signals":{}}`, the backend is healthy and the frontend should show the empty state. If the endpoint is unreachable, the page will show the "Backend unavailable" error card — restart the backend to resolve.
- **Score values look different from before**: This is a regression. The evidence chips must be purely additive — scores must not change. Stop and report immediately.
