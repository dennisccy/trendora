# Phase goal-i_can_see_the_wealthy_future_forever-iter-25 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (verify: `curl http://localhost:8000/health` returns `{"status": "ok"}`)
- The `/data` page health badge must show "Online" — if it shows "Checking backend..." the dev server's `.next` cache is stale; fix: stop the server, run `rm -rf apps/frontend/.next`, restart `next dev`, wait for `/_next/static/chunks/main-app.js` to return 200
- No other pull or import jobs are currently running (job card area should be idle)

---

## Verification Steps

1. Navigate to `http://localhost:3835/data`
   - **Expect:** The Data Manager page loads fully. The health badge in the header shows "Online". You can see the Coverage panel AND a "Missing-data diagnostic" panel directly below it. No red error banners anywhere on the page.
   - **Broken looks like:** A page showing "Checking backend...", a blank white screen, or a React error overlay. Fix: clear `.next` cache and restart the dev server (see Prerequisites).

2. Look at the "Missing-data diagnostic" panel — specifically whether any rows appear
   - **Expect:** One of two valid states: (a) the panel shows a "No missing data" confirmation message and no Pull buttons — this means the universe is clean; OR (b) the panel shows rows under "No history", "Thin history", or "Intra-series gaps" with exact shortfall values like "0 / 200 bars" or "3 missing 2025-01-15 → 2025-02-03"
   - **Broken looks like:** The panel is completely missing from the page, shows a blank card with no content, or shows an unformatted JSON blob.

3. If any row appears under "No history" or "Intra-series gaps": click the "Pull the missing data" button on that row (click the per-row button, not "Pull all missing")
   - **Expect:** A job card appears in the page's live job progress area showing the affected symbol name and a running or queued status. The `/data` page stays open — no redirect occurs.
   - **Broken looks like:** Nothing happens after clicking, the button throws an error toast, or the page navigates away.

4. Scroll down to find the "Unfinished imports" panel — check whether it is present or absent
   - **Expect:** If all past imports finished cleanly, the panel is completely absent from the page (no blank card, no empty section). If any paused, partial, or failed imports exist, the panel is visible with labeled rows showing an amber badge (for "Paused" or "Partial") or a red badge (for "Failed"), plus a plain-language state string like "Paused — hit a provider rate-limit (429); progress saved".
   - **Broken looks like:** A blank card labeled "Resumable imports" with no rows (old behavior — this panel should now be hidden when empty), OR a panel that shows all three state labels but with empty or identical text strings.

5. If the "Unfinished imports" panel is visible with at least one row: find a "Partial" or "Failed" row and click its "Dismiss" button
   - **Expect:** The dismissed row immediately disappears from the Unfinished-imports panel. If it was the only row, the entire panel disappears. Scroll down to the Run-history table below — the run's entry is STILL present there (the audit log is not deleted).
   - **Broken looks like:** The row stays after clicking, OR both the panel row AND the Run-history entry disappear.

6. Scroll back to the top and confirm the Coverage panel is still intact and the page shows exactly ONE date selector
   - **Expect:** The Coverage panel with per-symbol bar counts is visible and unchanged. Looking across the entire page — header, coverage panel, diagnostic panel, unfinished-imports panel — there is exactly one date control (a single dropdown or date-picker for the global as-of date). No second date control appears anywhere.
   - **Broken looks like:** The Coverage panel has disappeared or shows empty rows, OR a second date selector appears in or near the diagnostic/unfinished-imports panels.

---

## What "Working Correctly" Looks Like

- The "Missing-data diagnostic" panel appears directly below the Coverage panel with a clear heading label, either showing per-category shortfall rows or a "No missing data" empty-state — never a blank card
- Pull buttons appear only on "No history" and "Intra-series gaps" rows — never on "Thin history" rows
- The "Unfinished imports" panel is either hidden (when empty) or shows rows with amber/red badges and plain-language state strings — it never shows a blank card labeled "Resumable imports"
- Clicking "Dismiss" removes a row from the panel instantly while the Run-history table below remains unchanged

## Common Issues

- **Health badge stuck on "Checking backend..."**: The Next.js `.next` cache was clobbered by a production build. Stop the dev server, run `rm -rf apps/frontend/.next`, restart with `cd apps/frontend && npm run dev`, and wait for `GET http://localhost:3835/_next/static/chunks/main-app.js` to return HTTP 200 before testing.
- **Diagnostic panel missing from page entirely**: The backend API may not be returning the `coverage.diagnostic` field. Check the backend is running on the correct port and the `/api/data` response contains a `diagnostic` key.
- **Unfinished-imports panel shows blank card**: This is the old "Resumable imports" behavior (pre-iter-25). If you see this, the frontend code change has not taken effect — restart the dev server.
- **"Pull the missing data" button appears on Thin history rows**: This is a regression. Thin rows must be read-only (transparency only, no pull action).
