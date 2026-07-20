# Phase goal-ops-hardening-iter-2 — Implementation Summary

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19
**Written by:** developer

---

## Features Implemented

- **Aggregates are now computed when new data arrives, not when a page is viewed.** Whenever an operator
  runs a backfill (or the equivalent "both"/"rebuild" data job) and it completes successfully, the system
  now immediately recomputes and stores several pieces of information that pages need — the dataset
  coverage summary, the market-condition ("phase") reading for any newly-added date, and one commonly-used
  research chart. Previously, several of these were computed on-demand the first time a page asked for
  them, which was the source of slow/occasionally-crashing page loads.
- **The Data page's coverage panel is now served from storage, not recomputed live.** Visiting the `/data`
  page no longer triggers the expensive database scan that used to run every time that page's coverage
  section loaded (the scan that could hang or crash the backend on a large dataset). It now reads a
  pre-computed record instead.
- **A safety net for a brand-new database.** If the coverage record hasn't been computed yet (for example,
  right after the very first boot, before any data job has run), the backend now waits for a background
  process to fill it in shortly after startup — and in the meantime, the coverage panel shows an honest
  "nothing here yet" state instead of crashing or hanging.
- **Operators can now see which pieces of information a completed data job refreshed.** On the `/data`
  page, a completed backfill/rebuild job's detail now shows one additional line naming what it kept
  up to date — for example "Refreshed: coverage, market phase, membership timeline, research hot keys" —
  so an operator can confirm the background work actually happened, not just that the job finished.
- **The backend start script now actually enforces its own stated memory limit and writes a persistent
  log file.** Previously, the configuration file claimed the backend process was capped at a certain memory
  ceiling and that a safety setting was applied — but the actual start-up script did none of this. This
  iteration makes the script genuinely apply both settings, and also makes it write everything the backend
  prints to a permanent log file (`logs/backend.log`) instead of only to whatever terminal window launched
  it — so if the backend ever crashes, there is now a record of what happened right before it did.

## Changed Behavior

- **The Data page's "coverage" section**: previously computed live on every page visit (a scan of the
  entire price history table). Now read from a stored record that gets refreshed automatically whenever a
  data job finishes. The numbers shown to operators are exactly the same — only *when* they get computed
  has changed. In the rare case where the stored record does not exist yet (a brand-new, not-yet-used
  database), the page now shows an honest empty/zero state rather than the previous behavior of computing
  it live.
- **The Data page's coverage now shows correct numbers for EVERY date the "as-of date" selector offers, not
  only the most recent one** (fix applied after code review). The Data page has a date selector that lets an
  operator view the dataset "as of" any earlier date that has a stored snapshot. In the first version of
  this iteration, only the single most-recent date had its coverage stored, so picking any *older* date
  showed an all-zero "nothing here yet" panel even though that date genuinely has data — an incorrect,
  misleading picture. Now: (a) every date a data job newly adds gets its coverage stored at the same time,
  and (b) if an operator selects an older date that was added before this feature existed, the backend
  computes and stores its correct coverage on first view (so it is instant every time after). The default,
  most-common view (the latest date) is unchanged and still served instantly from storage.
- **Starting the backend** (`scripts/start-backend.sh`): now applies a memory ceiling to the process and
  writes all of its startup/runtime output to a permanent file on disk, in addition to what it did before
  (starting the server, setting up network permissions). Nothing about how to invoke the script changed.

## Backend-Only Items

- None. Every backend change in this phase has a corresponding, if minimal, piece of it visible in the UI
  (the one new "Refreshed: ..." line on the Data page) or is invisible-by-design infrastructure hardening
  (the memory cap, the log file, and the "compute at the right time instead of every page load" change,
  none of which are meant to be user-visible — they are meant to make the existing, already-visible pages
  faster and more reliable).

## Incomplete Items

- **Confirming the behavior against a heavy, in-progress data job** (does the backend stay responsive and
  stay within its memory limit *while* a large historical backfill is actively running) was not directly
  observed this pass, to avoid disturbing the specific test scenario the next verification stage needs.
  Everything else — the memory limit, the log file, and the faster page-load timing — was confirmed live
  against the real, running backend (see `docs/handoffs/goal-ops-hardening-iter-2-dev.md` and
  `reports/perf-budgets.md` for the exact measurements: a page load that used to take roughly 9-10 seconds
  now completes in well under a tenth of a second).
- No functionality from this iteration's plan was intentionally left out. Items explicitly scoped OUT of
  this iteration (carried over from the plan, not gaps): retiring an older, separate boot-time "sanity
  check" step; a fully rewritten fetch/import workflow; wiring up three additional, less-critical
  start-up settings (connection limits/timeouts) that were also found to be unenforced but were not part
  of this iteration's committed scope.

## Config and Environment Changes

- No new settings were added to the main configuration file — the memory-cap and safety-setting values
  already existed there; this iteration is the first time the start-up script actually reads and applies
  them.
- **New log file:** `logs/backend.log` (created automatically the first time the backend is started via
  `scripts/start-backend.sh`; not tracked in version control, matching how other logs in this project are
  handled). Each restart adds to this file rather than erasing it, so a history of start-ups (and any
  abrupt stops) accumulates there over time.

## Known Limitations

- The very first time a brand-new, never-used database is queried for coverage information (before any
  data job has run and before the background startup process has had a chance to fill it in), the
  coverage panel will show all-zero/empty values rather than a "please wait" message. This window is
  expected to be brief in normal operation, but it is a deliberate simplification — the alternative (a
  partially-live computed view) would reintroduce some of the performance risk this iteration exists to
  remove. Note this all-zero state now applies ONLY to a genuinely empty/never-ingested state — selecting a
  real historical date with data always shows its correct numbers (see the review-fix bullet above).
- The one-time "compute on first view" that heals an older date added before this feature existed (the
  review fix) does pay a single expensive computation on that first view of that specific date. This only
  ever happens for a deliberate, manual selection of an older date on a database that predates the feature,
  and it stores the result so it never repeats for that date. It never affects the normal latest-date page
  load.
- To avoid disturbing the exact test scenario the next verification stage needs (a specific date range
  that has not yet been backfilled), the developer did not personally run a real backfill job against the
  live product database as part of this implementation pass. The underlying capability has been verified
  with automated tests using realistic copies of the data, but the very first real-world use of "run a
  backfill and see the Refreshed line appear" is expected to happen during the next verification stage,
  not before it.
