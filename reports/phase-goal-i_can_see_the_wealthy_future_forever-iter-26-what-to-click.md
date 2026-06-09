# Phase goal-i_can_see_the_wealthy_future_forever-iter-26 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (confirm: `curl http://localhost:8000/health` returns 200)
- At least one paused/resumable import with a required session key is visible in the Unfinished Imports panel on `/data` — if none is present, you cannot verify the new error-feedback fix directly; proceed to step 4 for regression checks

---

## Verification Steps

1. Navigate to `http://localhost:3835/data`
   - **Expect:** The Data Manager page loads fully. The "Unfinished Imports" panel is visible. No blank screen, no "Checking backend…" spinner, no React error boundary message ("Something went wrong").
   - **Broken looks like:** The page stays on a loading spinner indefinitely, shows a white box where the panel should be, or displays a raw JSON error.

2. In the Unfinished Imports panel, find a resumable import row that requires a session key (it will show a key input field and a "Resume" button). Leave the key input field empty. Click the "Resume" button.
   - **Expect:** A red inline message appears immediately next to or below the Resume button reading "Enter the session key for [source name] to resume." The import row stays visible in the panel — it does NOT disappear from the list.
   - **Broken looks like:** Nothing happens after clicking Resume (no message), the row vanishes from the panel silently, or a page-level error overlay replaces the inline message.

3. Without refreshing the page, count the rows in the Unfinished Imports panel. Confirm the row you just attempted to resume is still there.
   - **Expect:** The row count is unchanged from before you clicked Resume. The row still shows its original import label and the Resume button.
   - **Broken looks like:** The panel now shows zero rows or the specific row is gone.

4. Navigate to `http://localhost:3835/data` in a fresh tab (or press F5 to refresh the current tab).
   - **Expect:** The page reloads without error. All panels (Unfinished Imports, coverage/data sections) render with content or an appropriate empty state — no "Something went wrong" panels.

5. On the loaded `/data` page, open browser DevTools (press F12), switch to the Console tab, and run: `document.querySelectorAll('select, input[type="date"]').length`
   - **Expect:** The number returned is the same as before this phase's changes — you should see only one date-related selector (the global as-of control). The J-38 UX fix should NOT have added a new date input or picker.
   - **Broken looks like:** The count is higher than expected, indicating a new date control was accidentally introduced.

6. On the `/data` page, locate an unfinished import row with a "Retry" button. Click "Retry".
   - **Expect:** The row updates (shows a new status or a spinner), or a job is queued without the Unfinished Imports panel going blank. No inline "Enter the session key" error appears during a Retry (that error belongs to Resume only).
   - **Broken looks like:** The panel flashes empty, the entire list disappears, or a key-required error appears on a Retry action.

---

## What "Working Correctly" Looks Like

- After clicking Resume without a key: a red message with the exact provider name is immediately visible next to the button, and the import row is still in the list below it.
- After any failed resume: the Unfinished Imports panel still shows the same rows it had before — no silent removal.
- The `/data` page has one date selector in the header/sidebar — not two.

## Common Issues

- **"Checking backend…" never clears / page is a dead shell:** The dev server's `.next` cache may be stale. Stop the frontend server, delete `apps/frontend/.next`, and restart with `next dev`. Confirm `GET http://localhost:3835/_next/static/chunks/main-app.js` returns 200 before retesting.
- **No resumable import row visible:** The Unfinished Imports panel only shows rows for imports that are paused/in-progress. If none exist, you cannot trigger the inline-error path directly. Check with the backend team whether a test resumable job can be created, or verify via the functional test plan (TC-07).
- **Backend not responding:** Run `curl http://localhost:8000/health`; if it fails, restart the backend with `uvicorn` on port 8000.
