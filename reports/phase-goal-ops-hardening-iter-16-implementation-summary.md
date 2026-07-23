# Phase goal-ops-hardening-iter-16 — Implementation Summary

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Written by:** developer

---

## Features Implemented

- **Backtest evidence never makes you wait for a live recalculation anymore.** The "Forward-tested
  evidence" panel at the bottom of the Backtest page used to be able to silently trigger a fresh,
  multi-minute recalculation the moment you loaded the page for the current (latest) date — if that
  happened to land at the wrong moment (right after new data came in), the page would just sit there.
  Now that panel is always served instantly from numbers that were already calculated when the data was
  ingested — never calculated on the spot while you're waiting on the page.
- **The Backtest page now tells you honestly which version of the evidence you're looking at.** Three
  possible states, always shown plainly:
  - Normal case: the evidence you see is fully current — no change from before.
  - While new data is still being processed in the background: a small "Refreshing — showing the last
    complete evidence" notice appears above the still-fully-visible evidence numbers, with a timestamp
    showing exactly when that version was generated. The page automatically shows the fresh numbers once
    the background processing finishes.
  - On a brand-new/empty setup where this evidence has never been calculated yet: an explicit "Backtest
    evidence not yet computed" message appears instead of a blank space, telling you to run an ingest.

---

## Changed Behavior

- **Backtest evidence panel (bottom of `/backtest`):** Previously, viewing the current date's evidence
  panel could quietly trigger a full recalculation behind the scenes if the cached copy was missing or
  stale — occasionally a very slow one. Now it NEVER recalculates when you view the page; it only ever
  reads numbers that were already calculated during the last data ingest. If those numbers are momentarily
  one version behind (because new data just came in and is still being processed), the page says so
  plainly instead of hiding it.
- **Internal bookkeeping for this evidence** (not user-visible directly, but underlies the fix above): the
  system used to discard the previous version's calculated numbers the instant it started saving the new
  version's numbers — piece by piece as each part finished. That created a brief window where a
  half-finished new version and a partially-deleted old version could overlap, in rare cases. Now the
  system keeps the complete old version fully intact until the complete new version is 100% ready, then
  switches over in one step. This closes a real (not hypothetical) inconsistency that was found in the
  live database during this iteration's investigation.

---

## Backend-Only Items

None. Every backend change in this iteration has a corresponding visible change on the `/backtest` page
(the refreshing notice and the not-yet-computed message).

---

## Incomplete Items

- **The live, full-scale timing measurement (confirming the evidence panel still loads within its
  ≤1.5-second budget in all three states, on the real, full-size dataset) has not been run yet.** The
  application services were not running when this work was done, and starting/stopping them is outside
  what this automated pass is allowed to do this round. The code and its automated tests are complete and
  passing; what's missing is the ONE live, hands-on confirmation pass. **Operator action needed:** start
  the backend under the normal host-safety settings, trigger a small one-day data backfill, and watch the
  Backtest page load through the version change while timing it — the developer handoff
  (`docs/handoffs/goal-ops-hardening-iter-16-dev.md`, "Known Issues" #2) has the exact step-by-step
  request, and the results should be recorded in `reports/perf-budgets.md`.
- **No one has looked at the new banner/message in an actual web browser yet** — only the underlying
  calculations were verified with automated tests. The visual appearance (colors, wording, layout) follows
  the same established look already used elsewhere on this page, and the code compiles cleanly, but a
  human/browser check of the actual screen has not happened yet. See the frontend handoff's "What to
  Click" section for exact steps once services are running.

---

## Config and Environment Changes

None. No new environment variables, no config file changes, no database schema changes — this iteration
reuses the existing storage table for this evidence without adding any new columns.

---

## Known Limitations

- This fix applies only to the CURRENT (latest) date's evidence panel. Looking at a HISTORICAL date (using
  the time-travel/as-of feature) behaves exactly as it always has — the first time you view an older date,
  it may take a moment to calculate, then it's instant on later views. That was already the existing,
  accepted behavior for historical dates and this iteration intentionally left it unchanged.
- The four OTHER background calculations this app maintains (event-study research views, market-phase
  status, drawdown expectations, and the major-index charts) were not touched by this iteration — only the
  Backtest evidence panel's own calculation was in scope.
- One pre-existing, unrelated test failure (about database table creation, nothing to do with this
  iteration's work) remains as a known, carried issue — it was already failing before this iteration and
  is not something this iteration's changes caused or were expected to fix.
