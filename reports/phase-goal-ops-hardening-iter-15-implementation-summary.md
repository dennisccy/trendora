# goal-ops-hardening-iter-15 — Implementation Summary

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Written by:** developer

---

## Features Implemented

- **Faster, reliable `/backtest` responses when a data-refresh job is running at the same time.**
  Previously, if you (or an automated job) opened the Backtest page's evidence panel at the exact moment
  the system was busy refreshing its cached statistics in the background, that page could take **over
  three minutes** to respond (measured at 211.8 seconds in an earlier check). This iteration found the
  exact cause and fixed it: several separate parts of the system were redundantly re-doing the SAME
  expensive calculation at once instead of sharing one answer. Now, whichever request asks first does the
  work once; every other request that asks for the same thing at the same moment waits a moment and reuses
  that one answer instead of repeating it. On a smaller test dataset built to reproduce the same shape of
  problem, this brought the wait down from about 10x a normal request's time to about 1x — i.e., back to
  normal.

---

## Changed Behavior

- **`/backtest`'s evidence-by-horizon data, when requested at the same time as an ingest job's background
  refresh**: Previously, each simultaneous request for the same time period's statistics redid the full
  expensive calculation from scratch, so the more requests landed at once, the slower ALL of them got —
  compounding badly under real load. Now, only the very first request does the real work; the rest wait
  briefly and get the same answer without repeating the calculation. The numbers shown to you are
  unchanged — this only affects how long you wait to see them.

---

## Backend-Only Items

- This is a backend performance/reliability fix with no new screen, button, or displayed value. The only
  user-visible effect (once confirmed on the live system) is that the Backtest page's evidence panel
  should no longer take minutes to load if it happens to load while a data-refresh job is running in the
  background — it should load quickly, the same as always.

---

## Incomplete Items

- **The final, real-world confirmation on the full live system has not been done yet.** This iteration's
  fix and its tests were built and verified on a smaller practice dataset built to reproduce the same
  problem shape, because the actual live system was not running at the time of this work (and automated
  agents are not allowed to start/stop it themselves this session). **Before this can be marked fully
  resolved, someone needs to:** restart the real backend fresh, let its background data-refresh job run,
  and at the same moment ask the Backtest page for numbers it hasn't already cached — then time how long
  that takes. The exact steps for this check are written out in `reports/perf-budgets.md` (the section
  titled "TC-4 / TC-5 / TC-6 — full-deep-basis live reproduction: PENDING, operator-supervised") and in
  this iteration's developer handoff. This is a normal, expected next step for this kind of fix — not a
  sign anything is broken.

---

## Config and Environment Changes

- None. No new environment variables, no config file changes, no database schema changes.

---

## Known Limitations

- The fix does not change what numbers are shown anywhere — only how fast they arrive when multiple
  requests for the same thing land at once. This was double-checked: the exact same large test suite that
  proves the displayed numbers are correct (32 separate checks across every configured time-window) was
  re-run unchanged and all still pass.
- A secondary, smaller possible cause (the database occasionally being a little slower to read while
  something else is actively writing to it at the same time) was measured separately and found to be a
  minor factor (about a 1.6x slowdown in an aggressive test, well within an acceptable range) — not
  something that needed a change on its own.
- As noted above, the real-world, full-scale confirmation on the live system is still outstanding and
  needs an operator to perform a brief, supervised check (a few minutes) the next time the system is
  restarted.
