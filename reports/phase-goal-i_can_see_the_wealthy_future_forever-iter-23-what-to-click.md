# Phase goal-i_can_see_the_wealthy_future_forever-iter-23 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (verify: open `http://localhost:8000/health` — should return 200)
- No credentials required
- No seed data required (the candidate pool and coverage data are pre-loaded)

---

## Verification Steps

1. Open `http://localhost:3835/data` in your browser
   - **Expect:** The Data Manager page loads fully — the JobForm card is visible showing a job-kind selector, the Coverage panel shows a "Universe" count, and no "Checking backend…" spinner persists

2. Click the job-kind dropdown on the JobForm card and read the options
   - **Expect:** You see exactly four options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill", and **"Expand universe"** — the fourth option is new to this iteration
   - **Broken if:** "Expand universe" is absent, or you see only three options

3. Select "Expand universe" from the job-kind dropdown
   - **Expect:** The Import source picker immediately appears below the job-kind selector (it was not visible before selecting Expand)
   - **Expect:** The card subtitle now reads "…and — for a fetch or expand — an import source…"

4. Open the Import source picker with "Expand universe" still selected and inspect the Alpha Vantage and Stooq options
   - **Expect:** "Alpha Vantage" and "Stooq" are visually grayed out (disabled) and each label includes the text "cannot supply market cap — not selectable for expand"
   - **Expect:** "Yahoo" and any other market-cap-capable sources appear in normal (enabled) style
   - **Broken if:** All sources appear enabled with no disabled state, or the "cannot supply market cap" label text is absent

5. With "Expand universe" selected, select "Yahoo" from the source picker
   - **Expect:** No amber alert block appears, the ineligible-reason element is absent, and the "Start job" button becomes active (not grayed out, cursor is a normal pointer)
   - **Broken if:** The Start button remains disabled even after selecting Yahoo, or an amber alert appears when Yahoo is selected

6. Without clicking "Start job", switch the job-kind back to "Fetch EOD prices" and reopen the source picker
   - **Expect:** Alpha Vantage and Stooq are no longer disabled — they appear in normal enabled style with no "cannot supply market cap" text in their labels
   - **Expect:** No amber ineligible-reason alert block is visible anywhere on the page
   - **Broken if:** The disabled state or amber alert persists after switching away from "Expand universe"

7. Switch back to "Expand universe", select "Yahoo", fill in "Start date" with "2025-01-01" and "End date" with "2025-01-07", then click "Start job"
   - **Expect:** A job card appears on the page showing the expand job is running, with a chunk progress badge like "Chunk 1/N" incrementing as it processes
   - **Expect:** If the job completes (with an injected provider or very fast), the job card shows a "Universe screen" section with a green "X passed" badge and an amber "X omitted" badge
   - **Note:** On this machine Yahoo is typically rate-limited. If the job lands in amber "rate-limited — resumable" state, that is correct behavior — proceed to step 8. If the job completes, skip to step 9.

8. If the job is in amber resumable state, click the "Resume" button on the job card
   - **Expect:** The job transitions from the amber resumable state back to a running state and the chunk progress badge increments from where it left off (not from chunk 1 again)
   - **Broken if:** The job restarts from chunk 1, or clicking Resume shows an error

9. Scroll down to the run history table on the `/data` page
   - **Expect:** A row with the "expand" kind badge is present for the job you just ran, and the Summary column contains text referencing the screen outcome (passers and/or omitted count)
   - **Broken if:** No expand row appears, or the row shows an unformatted error in the Summary column

10. Locate the Coverage panel and read the `universe-count` value
    - **Expect:** The Coverage panel displays a numeric "Universe" count — if the expand job completed with passers, this value reflects the grown universe (not zero)
    - **Broken if:** The universe-count shows zero, "N/A", or an error indicator after a completed expand job

---

## What "Working Correctly" Looks Like

- The job-kind dropdown has four options including "Expand universe"
- Selecting Expand reveals the source picker; Alpha Vantage and Stooq are visibly disabled with a plain-language reason
- Yahoo is enabled and allows starting an expand job
- A running expand job shows a "Chunk X/N" progress badge on the job card
- A completed expand job shows a "Universe screen" block with green passers and amber omitted badges, plus an omitted-with-reason list
- A rate-limited expand lands in amber "resumable" state with a Resume button that continues from the checkpoint
- The run history table shows the expand job row with a Summary of the screen outcome

## Common Issues

- **"Checking backend…" spinner does not resolve:** Backend is not running — verify `http://localhost:8000/health` returns 200
- **Source picker does not appear after selecting Expand:** Try a hard refresh (Ctrl+Shift+R / Cmd+Shift+R) — this may indicate a stale `.next` cache; do not run `npm run build` against the live dev server
- **All source options appear enabled (no disabled state for Alpha Vantage / Stooq):** The frontend may not have received the `supports_market_cap` flag from the backend — check the browser Network tab for `GET /api/data` and confirm the response includes `supports_market_cap: false` for alpha_vantage and stooq
- **"Expand universe" absent from the dropdown:** Confirm the frontend was rebuilt after the iter-23 changes — the dev server at port 3835 must be serving the updated `page.tsx`
