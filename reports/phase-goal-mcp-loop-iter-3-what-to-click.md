# Phase goal-mcp-loop-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-3
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Context

No UI features were added this iteration. The only change was a QA infrastructure fix (`scripts/start-frontend.sh`). This guide verifies that the evidence layer — Leadership "Proven" badges, proof drill-down, and the evidence ledger — renders correctly with live backend data.

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255` (confirm: `curl http://localhost:8255/api/health` returns HTTP 200)
- No login required — the app is public

---

## Verification Steps

1. Navigate to `http://localhost:3255/stocks`
   - **Expect:** Leaderboard loads with at least 5 rows populated. The Leadership column shows a green "Proven" chip on every visible row. The health badge near the top of the page reads "Ready". No "Checking backend…" spinner and no empty table.
   - **Broken looks like:** Table is empty, or shows "Checking backend…", or health badge reads "Backend unavailable".

2. On the `/stocks` leaderboard, look at the Entry Quality and Risk columns on any row.
   - **Expect:** Both columns show a muted grey chip with the text "Not yet proven". The grey chips are visually duller than the green "Proven" chip in the Leadership column. Clicking a "Not yet proven" chip opens no panel.
   - **Broken looks like:** Entry Quality or Risk shows "Proven", or clicking the chip opens a drill-down.

3. Click any stock ticker row in the leaderboard (e.g., the row for "MU").
   - **Expect:** Browser navigates to `/stocks/MU` (or whichever ticker you clicked). Three score cards are visible on the page: Leadership, Entry Quality, and Risk. Page does not show a 404 or error.

4. On the stock detail page, locate the Leadership score card and click the "Why proven?" button.
   - **Expect:** A proof panel expands within or below the Leadership card. The panel shows: the word "PASS", "+6.36%" holdout edge, "p ≈ 0.0005" p-value, "n = 12,297" cohort size, "vs SPY" benchmark control, the claim id "leadership_score", and the registration date "2026-06-30".
   - **Broken looks like:** No "Why proven?" button is visible, or the panel expands but shows blank or placeholder text.

5. Inside the expanded proof panel, click the "View backing evidence row →" link.
   - **Expect:** Browser navigates to `http://localhost:3255/evidence` (URL may include `#signal-leadership_score`). The evidence ledger page loads and the `leadership_score` row is visible.
   - **Broken looks like:** Link is missing from the panel, or clicking it navigates to a 404 or blank page.

6. On the `/evidence` page, find the `leadership_score` row and read its fields.
   - **Expect:** The row displays all five fields — a hypothesis statement (non-empty text), "PASS" OOS verdict, "+6.36%" edge, "SPY" benchmark control, and registration date "2026-06-30". None of the fields are blank.
   - **Broken looks like:** Row is missing, or one or more fields show blank, "N/A", or a loading placeholder.

7. In the `leadership_score` row, click "Backs: Stocks leaderboard →".
   - **Expect:** Browser navigates back to `http://localhost:3255/stocks`. The leaderboard renders with populated rows and the Leadership column still shows green "Proven" chips. Round-trip is complete.
   - **Broken looks like:** Link is missing, or navigation fails (404, error page, or empty leaderboard on return).

8. Back on `/stocks`, click the "Why proven?" button again on the Leadership card of a stock, then click it a second time.
   - **Expect:** The proof panel collapses on the second click. The toggle is repeatable with no errors.

---

## What "Working Correctly" Looks Like

- Leaderboard at `/stocks` shows a green "Proven" chip in the Leadership column on every row, and a muted "Not yet proven" chip in Entry Quality and Risk on every row.
- The "Why proven?" drill-down on any stock's Leadership card shows PASS, +6.36%, p ≈ 0.0005, n = 12,297, vs SPY, claim id leadership_score, registered 2026-06-30 — matching the live `/api/evidence` endpoint.
- The full loop `/stocks` → stock detail → proof panel → `/evidence` → `/stocks` completes with no broken links or error pages.

## Common Issues

- **Empty leaderboard or "Checking backend…"**: The backend may not be running or ready. Run `curl http://localhost:8255/api/health` — if it does not return 200, start the backend before retrying.
- **"Backend unavailable" health badge**: Same as above — backend is not reachable. Start the backend and reload the page.
- **Proof panel values do not match the expected numbers**: Confirm with `curl -s http://localhost:8255/api/evidence | jq '.proven_signals.leadership_score'` — the displayed values should be byte-identical to the API response.
- **All "Not yet proven" chips (including Leadership)**: The evidence certification may not be loaded. Check `curl -s http://localhost:8255/api/evidence | jq '.proven_signals.leadership_score.proven'` — it should return `true`.
