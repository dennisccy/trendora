# Goal Iteration 12 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Date:** 2026-06-13
**Written by:** developer

---

## Features Implemented

- **Resume a long import from where it stopped (J-59):** If a Data Manager job finishes fetching its price
  history but then fails while building snapshots, the Data Manager now offers a **Resume** button that
  picks up **from the backfill stage with zero re-downloading** — it never re-fetches anything it already
  has.
- **Stop re-downloading data you already have (J-59):** Re-running a job over a date range that is already
  fully downloaded now **skips the download in seconds** (it adds "0 new bars") instead of spending ~45
  minutes re-fetching data it already holds. A range that is only partly covered still downloads the
  missing days, with no duplicate rows.
- **Every job appears in Run history the moment it starts (J-60):** Starting any job immediately records a
  **"running"** entry in Run history (with its kind, date range, and source). When it finishes, that same
  entry updates once to an honest final state — **ok / partial / failed**, or **resumable** for a
  rate-limited pause. If the server is killed mid-job, the next startup marks the abandoned entry
  **"interrupted"** so nothing is ever stuck on "running" forever or silently vanishes.
- **Trustworthy, fine-grained live progress (J-66):** The live job card now shows a **"now working on…"**
  line (e.g. "scanning 2021-03-11 (12/22)"), an **"updated Ns ago"** heartbeat that ticks while the job is
  alive (and turns amber if it stops advancing), and a **symbols counter that can no longer show an
  impossible value** like "318/159" — it counts each symbol once. The "× faster" speed figure is now
  computed on the server (the screen only formats it).
- **Multi-month backfills finish reliably, and one bad day no longer crashes the rest (J-67):** Running a
  backfill over many months now completes without the previous database "committed-session" crash. If a
  single date fails, **that date is isolated and reported** (with its error) while every other date still
  completes — the job ends **"partial"** and shows which dates failed, instead of aborting the whole stage.
  Nothing is ever made up for a failed date.

---

## Changed Behavior

- **Run history records a job from its start, not only at the end.** Previously a job appeared in Run
  history only once it finished (or the process died before it could). Now it appears immediately as
  "running" and updates in place to its final state — one entry per job.
- **A multi-date backfill with a failing date now ends "partial", not "failed".** Previously a single
  failing date could abort the whole stage. Now each date is isolated; the others complete.
- **Re-running a covered date range is now near-instant.** Previously it re-downloaded everything (adding
  "0 new bars" the slow way). Now it skips straight to the snapshot stage.
- **The "× faster" speedup figure is computed on the server.** The screen no longer does that math itself
  (it just displays the server's number).

---

## Backend-Only Items

- None. Every backend change has a corresponding `/data` UI surface (the live job card, Run history, and
  Unfinished-imports sections).

---

## Incomplete Items

- None from this iteration's scope (J-59 / J-60 / J-66 / J-67). The next-cluster journeys J-61
  (availability heatmap), J-62 (as-of calendar popover), and J-63 (event-study episode mode) are
  explicitly out of scope and deferred to later iterations.

---

## Config and Environment Changes

- `config.yaml` → `data_manager.job_progress` — a new settings block controlling the live job card:
  - `poll_interval_seconds` (default `1.0`) — how often the job card refreshes.
  - `heartbeat_stale_seconds` (default `20.0`) — how long without progress before the job is flagged as
    "possibly stalled".
  - `per_symbol_ticks` (default `true`) — count fetch progress per individual symbol.
- No schema migration tool is used (the app creates tables on boot). Two new, defaulted, append-only
  columns were added so a fresh database carries them automatically: a stage-completion field on the import
  checkpoint, and a job-id correlation field on the run-history record.

---

## Known Limitations

- The live "real provider" download leg stays honestly unavailable (NA) in this environment because the
  network is walled — all of this iteration's behavior is verified offline with injected counting/fault
  test providers, exactly as the plan requires.
- The full automated test suite (~46 minutes, including the slow startup-warmup tests) was NOT run inside
  this development turn because it exceeds the per-step time limit; it is handed to the pipeline runner to
  execute. The directly-affected areas were all verified green in this turn (job pipeline, lifecycle,
  config, parallel backfill byte-identity, and the API surface).
- The "interrupted on restart" sweep assumes a freshly started server has no jobs of its own already
  running — true for this single-process setup; it would need revisiting only if the app were ever run as
  multiple server processes (which is out of scope).
