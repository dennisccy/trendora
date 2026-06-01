# Goal Iteration 3 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3
**Date:** 2026-06-01
**Written by:** developer

---

## Features Implemented

- **Data Manager page (`/data`)**: A new screen, reachable from a new "Data Manager" entry in the left
  sidebar, where the user can grow the dataset on demand. It shows current coverage, lets the user start
  a fetch/backfill job over a date or date range, watches the job's live progress, and lists past runs.
- **Dataset coverage panel**: Shows the price-history date range, how many symbols have prices, how many
  trading days exist, how many immutable snapshot/as-of dates are stored, and how many "gaps" remain
  (trading days that have prices but no snapshot yet — the actionable backfill targets), plus the gap
  date range.
- **Start a job**: Pick a start date, an end date, and a job kind — "Backfill snapshots", "Fetch EOD
  prices", or "Fetch + backfill" — and press Start. The page pre-fills a sensible default range drawn
  from the real gaps so the default action immediately does useful work.
- **Backfill (offline, deterministic)**: For each trading day in the chosen range that has prices but no
  snapshot, the system creates that day's immutable scan snapshot and its forward-test returns using the
  exact same engines the rest of the app uses. The result: new as-of dates appear in the global date
  switcher and the System Health evidence sample size grows — all from the committed data, reproducibly.
- **Fetch (live, real-data-only)**: For the chosen range, pulls real end-of-day prices via the
  config-selected live provider (Stooq) and stores only new days (it never overwrites committed prices).
  If the provider is unavailable, the affected symbols are reported as failed and **no prices are
  invented** — the failure is shown explicitly.
- **Live progress + final summary**: The job runs in the background; the page polls and shows a progress
  bar ("symbols X/Y", "snapshots A/B dates"), a status badge (running / ok / partial / failed), the
  number of new price bars / snapshots / forward returns, and any explicit error messages.
- **Run history**: A table of recent fetch/backfill runs (and the original seed load) with the date,
  kind, range, status, and symbol/snapshot counts.
- **New as-of dates appear without a reload**: When a job finishes, the global top-bar as-of date
  switcher refreshes itself so the newly created snapshot dates are immediately selectable — no page
  reload needed.

---

## Changed Behavior

- **Global as-of date switcher**: Previously it loaded the list of available dates only once when the app
  first mounted. Now it also exposes a refresh action; the Data Manager calls it when a job completes so
  new dates show up immediately. The user's currently-selected viewing date is never changed by a
  refresh — only the list of available dates is updated.

---

## Backend-Only Items

- The **live "fetch" path** is fully wired to the UI, but in this environment it cannot retrieve real
  data because Stooq now requires an API key for its free CSV endpoint (see Known Limitations). The UI
  correctly surfaces this as an explicit per-symbol failure with zero fabricated prices. The
  **backfill path** (which J-17's acceptance flow relies on) is fully functional offline.

<!-- All other new capabilities are accessible through the /data page. -->

---

## Incomplete Items

- **None of the in-scope J-17 items are deferred.** All spec items (coverage, async job with live
  progress + final summary, backfill that grows the evidence, real-data-only fetch with explicit
  failure, run history, new dates selectable without reload, sidebar entry, API client) are implemented.
- Out-of-scope items remain out of scope as the spec directs: committing fetched live bars back into the
  seed, scheduled auto-refresh, and the five iter-0 partials (left for the next closure pass).

---

## Config and Environment Changes

- **`config.yaml` → new `data_manager` block** (all values are read from config — no magic numbers in
  code):
  - `live_provider: stooq` — the live provider used by the **fetch** path only. The default boot/runtime
    provider stays `seed` (offline, deterministic), so the seed and walk-forward evidence remain
    reproducible.
  - `max_range_days: 370` — the maximum span a single job may cover (a guardrail; over-long ranges are
    rejected with an explicit error).
  - `gap_preview: 60` — how many gap dates the coverage view previews.
  - `run_history_limit: 50` — how many recent runs the history list returns.
- No new environment variables. No secrets. Stooq needs no key for the (now-gated) endpoint; any future
  provider key would be read only from the environment, never committed.
- No database migration. The Data Manager reuses the existing append-only `data_provider_runs` table for
  the run history (structured detail stored as JSON in its `message` column) and the existing
  `scanner_runs` / `forward_returns` tables for snapshots and returns — no schema change.

---

## Known Limitations

- **Live Stooq fetch is currently unavailable in this environment**: Stooq now gates its free daily-CSV
  endpoint behind an API key (it returns an "apikey required" page instead of CSV). The provider treats
  that non-CSV response as an explicit failure (`ProviderUnavailableError`) and fabricates nothing — the
  correct, honest behavior. The live integration test therefore **skips honestly** rather than passing.
  This does not affect J-17's acceptance flow, which uses the offline **backfill** path. Restoring live
  fetch would require a Stooq API key (read from the environment) or swapping in another free EOD
  provider behind the same interface — a small, isolated change.
- **One job at a time**: SQLite is single-writer; the design assumes a single active job (concurrent jobs
  are out of scope). Live progress is held in memory, so it resets on a backend restart — but the final
  summary of every run is persisted to the run-history table.
- **Backfilling a very early date** (near the start of price history) produces a valid snapshot, but its
  scores rely on limited prior history, so some components read as not-available — this is correct, not a
  defect. The default pre-filled range uses the earliest gaps; operators can pick any range.
