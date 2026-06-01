# Phase goal-i_can_see_the_wealthy_future_forever-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3 (J-17 — Data Manager)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` with the committed seed (158 symbols, quarterly snapshots)
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser, then look at the bottom of the left sidebar and click the "Data Manager" entry (the database icon, last item)
   - **Expect:** You navigate to `http://localhost:3835/data` and see the heading "Data Manager" with four panels: Dataset coverage, Start a fetch / backfill job, Job progress, and Run history. The "Data Manager" sidebar item is highlighted/active.

2. Read the "Dataset coverage" panel
   - **Expect:** "Price history" shows a real range like `2021-01-04 → 2026-05-28`; "Symbols" ≈ 158; "Trading days" and "Snapshot dates" are non-zero; "Backfill gaps" shows a count. If gaps > 0 the number is amber and a "Gap range" line shows `first → last`.
   - **Broken looks like:** zeros, `NaN`, blank values, or a red "Backend unavailable" card → the backend is down or `/api/data` failed.

3. Look at the "Start date" and "End date" inputs in the job form
   - **Expect:** Both are already filled with real dates inside the gap range; "Job kind" defaults to "Backfill snapshots"; the "Start" button is enabled.

4. Before continuing, open the global as-of date switcher in the header and note the currently selected date. Then close it. Separately, note its current value — you'll re-check it after the job.
   - **Expect:** A date is selected (e.g. the latest snapshot date).

5. With "Job kind" = "Backfill snapshots" and the pre-filled date range, click the "Start" button
   - **Expect:** The button shows a spinner and reads "Job running…", and the "Job progress" panel begins updating — the "Snapshots backfilled" bar advances (`A/B` dates rising) roughly each second.

6. Wait for the job to finish
   - **Expect:** A status badge of "ok" (or "partial"/"failed") with a final summary message; the "Start" button returns to its normal label.

7. Look at the "Run history" table at the bottom
   - **Expect:** A new top row showing Started time, Kind badge "Backfill snapshots", the Range you submitted, a Status badge, Symbols ok/failed, Snapshots created, and a Summary message.

8. WITHOUT refreshing the page, open the global as-of switcher again
   - **Expect:** The date(s) you just backfilled now appear as selectable options (no hard reload needed). The currently selected date is unchanged from step 4.

9. Select the newly backfilled date in the switcher, then click "Stocks" in the sidebar to go to `http://localhost:3835/stocks`
   - **Expect:** A valid per-date scorecard/leaderboard renders for that date — no error message, no empty table.

10. Click "Job kind" → "Fetch EOD prices", keep the date range, and click "Start"
    - **Expect:** The job ends "failed"/"partial" with an explicit per-symbol error list stating no data was fabricated (e.g. "(no data fabricated)") — an honest failure, NOT a fake success. A matching failed row appears in Run history.

---

## What "Working Correctly" Looks Like

- The `/data` page shows real, non-zero coverage numbers and a pre-filled gap range.
- A backfill job runs to a visible "ok" with a live-advancing progress bar, then logs a row in Run history.
- The newly backfilled date appears in the global as-of switcher without a page reload, the current selection is untouched, and that date renders valid content on `/stocks`.
- A "Fetch EOD prices" job fails honestly with a per-symbol error list and zero fabricated data.

## Common Issues

- **Red "Backend unavailable" card on `/data`**: backend is down — check `curl http://localhost:8000/api/data`.
- **"Backfill gaps" shows 0 / no gap range**: the dataset is already fully backfilled; pick any seed-bar date range manually, or this run has nothing to backfill (job may complete instantly with 0 new snapshots).
- **Backfilled date does not appear in the switcher after the job**: the additive `refresh()` did not fire — try a hard reload; if it only appears after reload, that's a regression in the no-reload behavior.
- **"Fetch EOD prices" shows a success instead of a failure**: this is a defect — the live Stooq endpoint requires an API key in this environment, so a fetch must fail honestly, never fabricate prices.
