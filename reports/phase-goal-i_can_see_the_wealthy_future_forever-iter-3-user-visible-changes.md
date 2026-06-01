# Phase goal-i_can_see_the_wealthy_future_forever-iter-3 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3 (J-17 — Data Manager: grow the dataset by date / date range)
**Date:** 2026-06-01
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open a brand-new **Data Manager** page by clicking the **"Data Manager"** entry (database icon) at the bottom of the left sidebar, which navigates to `/data`.
- Users can now **see how much data the system holds** at a glance: the price-history date range, number of symbols, number of trading days, number of snapshot/as-of dates, and the count of **backfill gaps** (trading days that have prices but no snapshot yet).
- Users can now **start a fetch / backfill job** for a single date or a date range by setting a **Start date** and **End date**, choosing a **Job kind** (Backfill snapshots / Fetch EOD prices / Fetch + backfill), and clicking the **Start** button.
- Users can now **watch a job run live**: a progress bar and counters update roughly every second showing symbols fetched (X/Y, ok vs failed) and snapshots backfilled (A/B dates), ending in a final success / partial / failed status.
- Users can now **read an explicit error breakdown** when a job fails or partially fails — the progress card lists the per-symbol failures and states plainly that no data was fabricated.
- Users can now **review a run-history table** of recent fetch/backfill runs (and the original seed load): start time, kind, date range, status, symbols ok/failed, snapshots created, and a summary message.
- After a backfill job completes, users can now **select the newly created snapshot dates in the global as-of switcher without reloading the page**, and those dates resolve across the rest of the dashboard (e.g. `/stocks`, `/`).
- After a backfill job completes, users will see the **System Health sample size (n) increase**, because the new snapshots add more forward-test evidence.

---

## What Changed in the Visible UI

- A new sidebar navigation item **"Data Manager"** (database icon) was added as the last entry in the left sidebar `NAV`, linking to `/data`.
- A new page at **`/data`** was added with four panels:
  - **Dataset coverage** panel — five metrics (Price history range, Symbols, Trading days, Snapshot dates, Backfill gaps) plus a gap-range line. The gap count shows amber when gaps exist, green ("no backfill gaps") otherwise.
  - **Start a fetch / backfill job** panel — Start date / End date date-pickers, a Job kind dropdown, and a **Start** button (shows a spinner and "Job running…" while busy). The date range is pre-filled once from the real gap dates so the default Start does useful work.
  - **Job progress** panel — a status badge, live message, a "Symbols fetched" progress bar with ok/failed counts and new-bar count (for fetch jobs), a "Snapshots backfilled" progress bar with snapshot / forward-return counts (for backfill jobs), and an error list when failures occur. Shows an idle placeholder before any job is started.
  - **Run history** table — recent runs, or an empty-state card ("No fetch / backfill runs yet") when none exist.
- The page shows a **loading skeleton** while coverage loads, and a styled **"Backend unavailable"** error card (red) if coverage cannot be fetched — explicitly stating no figures are fabricated.

---

## What Old Behavior Changed

- **Global as-of switcher** — previously its list of selectable dates was fetched once on mount and only changed on a hard page reload. Now the switcher exposes an additive `refresh()` that the Data Manager calls on job completion, so newly backfilled dates appear in the switcher **without a hard reload**. Note: `refresh()` only adds date options; it does **not** change the user's currently selected as-of date, and backfilling older dates leaves the "latest" date unchanged. No other date-driven page behavior changed (J-18 / "exactly one date selector" preserved).
- **System Health sample size (n)** — previously fixed to the ~quarterly seed snapshots bootstrapped at boot. Now n can grow when a user backfills additional seed-bar dates via the Data Manager.

---

## Not Visible Yet

- **Live "Fetch EOD prices" path is selectable but cannot currently retrieve real data in this environment.** The Stooq provider's free CSV endpoint now requires an API key, so a fetch job surfaces an explicit per-symbol failure with zero fabricated prices (correct, honest behavior) rather than returning new bars. The UI control exists and behaves correctly on failure; successful live fetch needs a Stooq API key (env-only) or another free EOD provider. The **backfill** path is fully functional offline.
- **Live job progress is in-memory on the backend** and resets if the backend restarts mid-job; only the final summary of each run persists (in the run-history table). There is no UI to resume or recover an interrupted in-flight job.
