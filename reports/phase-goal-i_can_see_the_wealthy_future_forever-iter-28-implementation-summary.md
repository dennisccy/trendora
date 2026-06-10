# goal-i_can_see_the_wealthy_future_forever-iter-28 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-28
**Date:** 2026-06-10
**Written by:** developer

---

## Features Implemented

- **Fast, usable cold start**: When the backend starts from scratch, it now becomes usable almost
  immediately — it serves the main pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest
  date within seconds, instead of appearing dead ("Backend unavailable") for minutes while it crunched
  through years of historical data.
- **Background catch-up ("warm-up")**: The years of historical evidence that the Backtest and Research
  pages need are now produced quietly in the background after the server is already answering, with honest
  live progress (e.g. "history 4/11"). Nothing is fabricated — the warm-up uses the exact same calculation
  engines as before; only WHEN it runs changed.
- **Honest readiness badge**: The top bar now tells the truth about backend state in three states:
  **Ready**, **Initializing… (with progress)**, or **Backend unavailable**. It updates quickly (so "Ready"
  appears within a second or two of the warm-up finishing).
- **"Warming up" state on Backtest & Research**: While the historical evidence is still loading, those two
  analytics pages clearly say "Warming up — historical evidence still loading (n/m)" instead of showing an
  error, a blank, or a half-finished result that looks complete. They fill in automatically when the
  warm-up finishes.
- **Survives a boot race**: If two startups happen to run at the same moment (or the warm-up runs while a
  user-triggered scan does), the system no longer crashes with a "UNIQUE constraint" database error — the
  duplicate is safely ignored and the already-saved result is returned unchanged.
- **Survives a failed warm-up**: If the background warm-up hits an error, it is logged and the server keeps
  running and serving what it already has; the badge honestly shows it is not finished; and the next
  startup quietly completes the remaining work.

---

## Changed Behavior

- **Backend startup**: Previously the server did the full multi-year historical backfill BEFORE it would
  answer any request (so even the health check was unreachable for minutes on a fresh database). Now it
  does only the minimal work to serve the latest day, starts answering, and warms up the history in the
  background.
- **Top-bar status badge**: Previously showed only "Backend OK" / "Backend unavailable". Now shows the
  three honest readiness states with live warm-up progress.
- **Health endpoint (`GET /api/health`)**: Now also reports a `readiness` state and `warmup` progress (plus
  the poll cadence the page uses). The previous fields are unchanged.

The actual numbers shown anywhere (scores, buckets, regime, forward returns, the Backtest aggregate) are
**byte-for-byte identical** to before — only the timing of when the historical data is produced changed.
This was verified with a test that fills two databases the old way and the new way and confirms they match
field-for-field.

---

## Backend-Only Items

- None. Every backend change has corresponding UI (the readiness badge and the warming states), or is an
  internal robustness change with no UI of its own (the concurrency/non-fatal guards).

---

## Incomplete Items

- None of the in-scope items were deferred. Two explicitly out-of-scope accelerators were intentionally NOT
  built (per the phase spec):
  - **A committed pre-computed snapshot cache** (would make even a first cold boot instant) — optional,
    not required to meet readiness; deferred.
  - **A faster (memoized) scan engine** — a separate future optimization; the per-date scan remains slow,
    which is the main reason a cold warm-up takes a few minutes.

---

## Config and Environment Changes

- New `startup` block in `config.yaml` (all boot-validated; the app refuses to start on an invalid block):
  - `readiness_budget_seconds` — the soft target for the minimal startup work before serving — default
    `30.0`.
  - `warmup_batch_size` — how many historical days the warm-up reports progress in per tick — default `1`.
  - `health_poll_interval_seconds` — how often the status badge checks the backend while warming — default
    `2.0`.
  - `health_poll_idle_interval_seconds` — the slower check rate once Ready — default `30.0`.
- No environment variables added. No database schema change (readiness is computed; warm-up progress lives
  in memory). No migration required.

---

## Known Limitations

- **A cold warm-up still takes a few minutes** because each historical day's scan is computationally heavy
  (~12–40 seconds each). This is expected and acceptable: the server is usable immediately and warms up in
  the background. Making the scan itself faster is a separate, deferred improvement.
- **The one synchronous latest-day scan on a fresh database takes ~29 seconds**, which is right at the
  30-second readiness budget. On a warm database it is effectively instant. If this ever needs to be
  faster, the deferred pre-computed snapshot cache is the intended fix (flagged, not built).
- **The boot-race protection covers the specific "duplicate UNIQUE-constraint" crash** documented for this
  system. Under extreme simultaneous-write pressure on the local SQLite file a different "database is
  locked" condition is theoretically possible; that is an environmental contention issue, not the failure
  this iteration targets, and was not observed in the concurrency tests.
- **The full new test file is slow** (~10–11 minutes) because it runs real warm-ups end-to-end to prove
  the behavior deterministically. It should not be run at the same time as the rest of the test suite.

---

## Fix Cycle — Second Quality-Gate Pass (2026-06-10)

The first pass built everything above, but the automated test suite failed at the quality gate: dozens of
the API tests failed when the whole suite was run together (yet passed one file at a time), and the run
crawled for over an hour. No user-facing behavior was wrong — this was a start-up-timing and test-setup
problem. Two corrections fixed it, with no change to any number the product shows.

- **Repeat start-up triggers are now safe (one warm-up at a time).** The background history-loader now runs
  exactly once while it is in progress; any concurrent repeat trigger (which happens constantly during
  automated testing, and can happen with a development auto-reload or a health probe) is politely ignored
  until the running one finishes. Before, every trigger started another full background load, so many
  piled up at once and fought over the database — the cause of both the test failures and the hour-long
  crawl. This also makes the real product more robust on boot.

- **The shared test database is now fully prepared once, up front.** The automated API tests expect the
  full history to be present (some check "there are at least two days of history", which the old, slower
  start-up guaranteed). The test setup now produces that full history once before the tests run, using the
  exact same calculation engines the product uses — so the tests are stable again. This is a test-harness
  change only; it does not touch how the product starts up for real users.

**Verified:** the two test files that reproduced the failure now pass together (15 of 15); the four
previously-failing API test files pass together (102 of 102); and a new test proves that five rapid repeat
start-up triggers spawn exactly one background loader, not five. The hour-long crawl is gone.
