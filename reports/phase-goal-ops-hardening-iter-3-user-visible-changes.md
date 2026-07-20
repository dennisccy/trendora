# Phase goal-ops-hardening-iter-3 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-3
**Date:** 2026-07-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Run a **"Fetch EOD prices"** job (or **"Fetch + backfill"**, the `both` job kind) on the `/data` page and, as soon as it lands even one new price bar, see the "Dataset coverage" panel's Universe, Candidate universe, Symbols, Trading days, Snapshot dates, and Backfill gaps figures — plus the per-symbol coverage table underneath — reflect the new data right away. This happens twice over: the panel refreshes itself automatically the moment the job card reaches a finished status (no manual action needed, in the same browser tab), and a plain reload of `/data` afterward shows the same corrected numbers, proving they are now saved, not just held in memory. Previously, only a "Backfill snapshots" job or the separate "Rebuild snapshots for current universe" action did this — an ordinary fetch (the single most common, everyday ingest action) left those same numbers frozen at their old values, which could mean the page kept showing an honest-*looking* but **false** "nothing here yet" all-zero state for a database that was actually fully up to date, until an unrelated restart or backfill/rebuild happened to refresh it.
- Re-run that same "Fetch EOD prices" job when there is genuinely nothing new to pull (the everyday no-op case — e.g., re-fetching a range already up to date) and see it finish exactly as fast as before. The new freshness check adds no delay, no extra database write, and no change in what's displayed when there is truly nothing to refresh.
- Generally trust the "Dataset coverage" panel's numbers more: they can no longer quietly go stale or falsely show all-zero just because the last ingest action happened to be a plain fetch rather than a backfill or rebuild.

---

## What Changed in the Visible UI

- Nothing was added, removed, relabeled, or restyled anywhere in the product. Same `/data` page, same "Dataset coverage" panel and its stat tiles, same per-symbol coverage table, same job form, same three options in the "Job kind" dropdown ("Backfill snapshots" / "Fetch EOD prices" / "Fetch + backfill"), same "Rebuild snapshots for current universe" panel. This iteration is a pure under-the-hood correctness fix beneath an existing, visually unchanged screen — zero frontend files were touched.

---

## What Old Behavior Changed

- **"Dataset coverage" panel's refresh trigger widened.** Previously the panel's underlying saved figures were only refreshed after a "Backfill snapshots" or "Rebuild" job finished. Now a plain "Fetch EOD prices" job — and the API-only "expand universe" job kind (see "Not Visible Yet") — that actually lands new data also refreshes it, the same way (read from storage, never recomputed live while the page is loading).
- **The "Refreshed: ..." status line is unchanged on purpose.** The small line that appears on a completed backfill/rebuild run's card and history row (e.g., "Refreshed: coverage, market phase, membership timeline, research hot keys") still does **not** appear for a fetch run — even though a fetch now also refreshes the coverage numbers behind the scenes. This is a deliberate, unchanged design choice (that status line is reserved for the richer backfill/rebuild refresh), not an oversight, but it is worth knowing so an operator does not expect that line to start appearing after an ordinary fetch.

---

## Not Visible Yet

- **The "expand universe" half of this same fix has no UI trigger anywhere in the product.** The fix applies equally to a "fetch" job and an "expand" job at the code level, and both are covered by the backend's automated tests — but no button, form, or control anywhere in the app lets a user actually submit an "expand" job (the `/data` "Job kind" dropdown only offers Backfill snapshots / Fetch EOD prices / Fetch + backfill; the separate "Rebuild" action is its own distinct control). That portion of the fix can only be confirmed by reading the backend's test suite, never by clicking through the app.
- **The internal cleanup of old, superseded coverage bookkeeping rows has no on-screen representation.** A small internal table that records what the coverage numbers looked like under a previous version of the database is now cleaned up automatically in one step whenever the data changes, instead of accumulating old rows indefinitely. There is no "storage cleaned up" message, counter, or settings toggle anywhere in the UI — it is verifiable only by inspecting the database directly.
- **The live confirmation that the backend stays responsive and within its memory budget during a real heavy data job** is recorded in an internal engineering report (`reports/perf-budgets.md`), not shown anywhere in the running app. Users only ever experience its effect — the app not slowing to a crawl or crashing during a big rebuild — never a visible measurement or meter.
