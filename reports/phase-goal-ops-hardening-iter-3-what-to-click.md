# Phase goal-ops-hardening-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-3
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (e.g., started via `scripts/start-backend.sh`)
- No login required — this is a single-user local application
- No special seed data needed beyond the normal committed database (it already has some price history and at least one existing backfill gap)

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads with a "Dataset coverage" panel showing tiles for Price history, Universe, Candidate universe, Symbols, Trading days, Snapshot dates, and Backfill gaps. No "Backend unavailable" message.

2. In the "Dataset coverage" panel, write down the current "Symbols" and "Snapshot dates" numbers
   - **Expect:** Both are visible, non-blank numbers (e.g., "Symbols: 47").

3. In the "Start a fetch / backfill job" panel, set "Job kind" to **"Fetch EOD prices"** (leave the pre-filled Start date / End date fields exactly as they are), then click the **"Start"** button
   - **Expect:** The "Job progress" panel shows a spinning status badge, which settles to **"ok"** (or "partial") within a few seconds.

4. Without reloading the page, look at the "Dataset coverage" panel again
   - **Expect:** "Symbols" and/or "Snapshot dates" is now a higher number than what you wrote down in step 2 — it updated on its own, with no manual reload. *(If nothing changed, extend the "End date" field a few days further forward and repeat step 3 once — the pre-filled range occasionally needs widening to land new data.)*

5. Press **F5** to hard-reload the page
   - **Expect:** The same updated numbers from step 4 are still shown — they did NOT revert to the old values. This is the actual fix: the new numbers were saved to the database, not just held in the page's memory.

6. Click **"Start"** again with the exact same "Job kind" and dates you just used
   - **Expect:** It finishes about as fast as the first run, and the "Dataset coverage" numbers stay exactly the same as step 5 (no further change, no added delay) — a job with nothing new to fetch does no extra work.

7. Check that run's card in the "Job progress" panel
   - **Expect:** Only a plain summary is shown (a "Symbols fetched" count and a short message). No line starting with **"Refreshed:"** appears — that line only ever appears after a "Backfill snapshots" or rebuild run, never after a plain fetch.

8. Look at the readiness badge in the page header (visible on every page)
   - **Expect:** It reads **"Ready"** — confirming the backend is healthy and responsive after everything above.

---

## What "Working Correctly" Looks Like

- The "Dataset coverage" numbers update themselves right after a "Fetch EOD prices" job finishes — no manual reload needed — and the new numbers survive a hard reload (F5).
- Re-running the identical fetch a second time changes nothing further and takes no longer than the first run.
- The "Refreshed: …" line never appears on a plain fetch run's card — only ever on a "Backfill snapshots" or rebuild run's card.
- The header's readiness badge reads "Ready" throughout, never "Backend unavailable" or stuck on "Checking backend…".

## If Something Looks Wrong

- **"Backend unavailable" card / blank page:** the backend isn't running or isn't reachable — start it with `scripts/start-backend.sh` and reload.
- **Coverage numbers stay unchanged after a fetch that should have landed new data (step 4 fails even after widening the date range):** this is the literal bug this iteration was built to fix (a fetch used to leave the coverage panel stale until an unrelated restart or backfill). If you still see this after retrying step 4 with a wider range, treat it as a regression and flag it.
- **"Start" button stays greyed out:** one of the date fields has an invalid value — look for a red "Enter a valid date as yyyy-MM-dd" message beneath it and correct the date.
- **A "Refreshed: …" line DOES appear after a plain fetch (step 7):** this is unexpected — that line is reserved for Backfill/Rebuild runs only and should not appear for a fetch.
