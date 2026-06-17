# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- A paused-resumable Expand-universe job must exist in the database. This job was created by running an Expand-universe import against the Yahoo source when Yahoo authentication was unavailable. If no such job exists, ask a developer to seed one before proceeding.

---

## Verification Steps

1. Open `http://localhost:3835/data` in your browser
   - **Expect:** The Data Manager page loads. A heading containing "Data" is visible. No full-page error or blank screen appears.

2. Scroll the page and locate the section labeled "Unfinished imports" (or "Unfinished-imports")
   - **Expect:** The section is visible on the page. Inside it you can see a job row for the paused Expand-universe job. The row has an amber or "Resumable" status indicator — NOT a green "Completed" badge.
   - **Broken looks like:** The section is missing entirely, or it shows the paused job with a green "Completed" badge and a message like "0 passers, 548 omitted" — that is the old silent-failure behavior this iteration was supposed to fix.

3. Read the message text on the paused job row without clicking anything
   - **Expect:** The message text says something like "market-cap provider auth failed — Resume to retry" or similar honest description. It does NOT contain a URL with query parameters (`?crumb=` or `?symbols=`), a long alphanumeric token, or the text "0 passers".
   - **Broken looks like:** A raw URL visible in the message (e.g., `https://query2.finance.yahoo.com/v7/finance/quote?symbols=AAPL&crumb=ABC123xyz`) — that is a credential/token leak.

4. Locate and click the "Resume" button on the paused job row
   - **Expect:** After clicking, the job row updates — either the status badge changes (e.g., to "Running" or "Queued") or the row disappears from the Unfinished-imports list as the job moves to the active queue. The page does NOT crash or show a red error banner.
   - **Broken looks like:** Nothing happens when you click Resume, or a full-page error appears, or the status stays "Resumable" indefinitely with no visible progress after 10 seconds.

5. Navigate to `http://localhost:3835/stocks` in your browser
   - **Expect:** The Stocks page loads and displays stock data (at least the seeded symbols are visible). No blank screen or "backend unavailable" error is shown.
   - **Broken looks like:** The Stocks page is blank or shows an error — this would indicate the iter-26 backend changes broke the price-seed manifest.

6. Return to `http://localhost:3835/data` and confirm the Unfinished-imports section no longer shows the job row you just resumed (or shows it in a non-resumable terminal state)
   - **Expect:** The job you clicked Resume on is either gone from the Unfinished-imports panel, or it now shows a different status (e.g., "Running", "Completed", or "Failed" — anything other than "Resumable").

---

## What "Working Correctly" Looks Like

- The Unfinished-imports panel shows the paused Expand job with an amber "Resumable" badge and an honest message like "market-cap provider auth failed — Resume to retry"
- The "Resume" button is visible and clickable, and clicking it moves the job out of the "Resumable" state
- No raw Yahoo URLs, crumb tokens, or credential strings are visible anywhere in the job card
- The Stocks page (`/stocks`) continues to load and display data normally

## Common Issues

- **Blank page / "Checking backend..." on all pages:** The `.next` build cache may be stale. Ask a developer to restart the frontend dev server.
- **Unfinished-imports section is empty:** No paused-resumable job exists in the database yet. Ask a developer to seed a paused expand job (or trigger one by running an Expand against Yahoo with auth blocked).
- **Job stays "Resumable" after clicking Resume:** The backend may not be running. Verify the backend is up by opening `http://localhost:8835/api/health` in your browser — you should see a JSON response, not a connection error.
- **Stocks page is blank or shows "0 symbols":** The seed manifest may have been corrupted. Ask a developer to check `apps/backend/data/seed/meta.json` — after iter-26 it should list 159 symbols.
