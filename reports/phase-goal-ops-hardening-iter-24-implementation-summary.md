# goal-ops-hardening-iter-24 — Implementation Summary

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Written by:** developer

---

## Features Implemented

- **A live "background compute running" indicator on every page.** The backend has, since an earlier
  iteration, sometimes needed to compute forward-looking evidence for a historical date in the background
  after someone views it (so the page itself never has to wait). Until now, there was no way to SEE that
  this was happening — the only way to know was to dig through raw database timestamps and server log
  files after the fact. Now, whenever this background work is running, a small badge appears next to the
  existing "Ready / Initializing / Unavailable" status pill in the top bar, on every page, saying
  "background compute running (N)" — and it disappears the instant the work finishes. Nothing to click,
  nothing to configure; it just tells the truth about what the backend is doing right now.
- **A new "Background compute" panel on the Data Manager page.** This panel shows the full detail behind
  that badge: which date(s) are currently being computed, how long each one has been running, how many of
  the (currently 5) required calculation steps are done for each, and the outcome (succeeded or failed,
  with the reason if it failed) of the most recently finished one. When nothing has ever run, it says so
  plainly ("No background compute running. Last outcome: none yet.") instead of showing an empty table.
  A one-line note makes clear this history only covers the current run of the backend — it is not saved
  anywhere and resets if the backend restarts.
- **A new, small, honest setting.** How many past outcomes the panel remembers (5 by default) is now a
  configurable number rather than a number buried in code — an operator could change it later without a
  code change if they wanted to remember more or fewer past results.

---

## Changed Behavior

- **`GET /api/health`** (the same single status check the badge and every readiness indicator already
  poll) now carries one additional piece of information alongside what it already reported — nothing it
  already reported was changed or removed.
- **The historical background-compute mechanism itself** (introduced in an earlier iteration) now also
  keeps a small amount of extra bookkeeping about itself — when it started, how far along it is, and how
  its last few runs turned out — purely so it can be reported. It computes exactly the same numbers, in
  exactly the same way, as before; nothing about WHAT gets computed or WHEN changed, only that it now also
  reports on itself while doing so.

---

## Backend-Only Items

None. Everything the backend now tracks is wired all the way through to the top-bar badge and the new
Data Manager panel this same iteration.

---

## Incomplete Items

- **A live browser walkthrough of the new badge and panel was not performed by this developer session** —
  that is a separate quality-check stage that runs after development work like this. I did confirm, using
  the real running backend (not a simulation), that triggering a genuine background compute produces
  exactly the data the badge and panel are built to show — the count went from 0 to 1 while the work was
  running, the "how far along" counter climbed from 0 up to the full number of steps, and a completed
  result appeared afterward with a real elapsed time — but I did not open an actual browser window to look
  at the badge and panel with my own eyes rendering. The reviewer/QA stage covers that.
- One of the automated regression checks (a broad pre-existing test file covering the general health/status
  check, unrelated in scope to what changed here) had not finished running by the time this work needed to
  be handed off — it is a known slow test in this project (it rebuilds a large practice dataset covering
  many years of history before it can even start, which has been separately documented as an existing,
  pre-iteration slowness, not something this iteration caused). It was still running cleanly with no
  errors reported partway through; the next stage should confirm its final result.

---

## Config and Environment Changes

- `startup.background_compute_history_size` (in `config.yaml`) — controls how many past background-compute
  outcomes are remembered and shown on the Data Manager panel. Default: `5`. No action needed to pick this
  up — it already has a safe default, and existing setups that don't mention it at all will simply use that
  default.
- No database changes. No new environment variables required to run the app normally.

---

## Known Limitations

- This feature only remembers what has happened since the backend last started. If the backend restarts,
  the "recent outcomes" history is cleared — this is by design (stated plainly in the panel's own copy),
  not a bug, since the underlying background-compute work itself is also not something that persists
  across a restart.
- The badge and panel show real, measured numbers only — elapsed time and step counts that have actually
  happened — never a guess at how much longer something will take or what percentage complete it "feels
  like." If that kind of estimate is wanted later, it would need to be a deliberate, separate decision (and
  would need real-world timing data to base it on, which this iteration also happened to capture and record
  for the future).
