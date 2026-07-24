# goal-ops-hardening-iter-17 — Implementation Summary

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** developer

---

## Features Implemented

- **Backtest evidence now survives the single most common ingest shape.** When the latest trading day
  advances and its behind-the-scenes forward-aggregate computation hasn't finished yet, the `/backtest`
  page now keeps showing yesterday's real, labeled numbers instead of going blank with a "not yet
  computed" message. This was the single most impactful gap left from the previous iteration: previously,
  every time the backend finished a normal daily update, the Backtest page would briefly show an empty
  state for the newest date even though good data existed from the day before.
- **The evidence banner now says which date's evidence it's showing.** The existing "refreshing" banner
  (a small notice that appears when the page is showing slightly-stale-but-complete evidence) now names
  the specific date whose numbers are on screen, not just when they were computed. A user can now tell at
  a glance "this is Tuesday's evidence" rather than just "this was generated at 2:15pm."

## Changed Behavior

- **The "Backtest evidence not yet computed" empty state**: Previously this message could appear any time
  a fresh trading day was added, even while normal processing was still catching up — and its wording told
  the user to "run an ingest," which was confusing if they had just done exactly that. Now this message is
  reserved for the one case it was always meant to describe — a brand-new, never-used database — and the
  wording no longer presumes the user hasn't already started anything.
- **Backtest page for historical dates loads slightly faster on repeat visits.** Revisiting a date on the
  Backtest page that was already looked at once no longer re-reads and re-processes the same stored data
  a second time behind the scenes. The displayed numbers are unchanged — this is purely an internal
  efficiency cleanup.

## Backend-Only Items

None — every change in this iteration has a corresponding, user-visible effect on the `/backtest` page.

## Incomplete Items

- **Live, in-browser confirmation of the fix and the empty state were not captured this session.** The
  application (backend and frontend) was not running when this work was done, and this automated session
  cannot start or stop it. Two pieces of evidence still need a human to run:
  1. A quick before/after look at the Backtest page during a normal daily data update, to visually confirm
     the fix (this is a 5-10 minute check against the app as it's already normally used).
  2. A one-time look at the never-used-database empty state, which requires briefly starting a second,
     disposable copy of the app pointed at a blank database (never the real one) — see "Known Limitations"
     below for the exact steps.
- **The intermittent slow loading noticed during data updates was investigated but not fixed.** During
  the previous iteration's testing, roughly 1 in 6 page loads of `/backtest` were slower than the target
  speed (a few seconds instead of under 1.5) WHILE a data update was actively running in the background —
  never at any other time, and the page always eventually loaded correctly. This iteration traced the
  likely cause as deep as the available diagnostic tools allow but could not pin it to one exact
  mechanism, and made no code change to address it this session (a fix attempted without a way to verify
  it live would be a bigger risk than the slow-loading itself, which is disclosed and bounded, not a
  crash or wrong data). See `reports/perf-budgets.md` for the full write-up and what a future check should
  measure.

## Config/Env Changes

None. No new environment variables, config file entries, or database schema changes in this iteration.

## Known Limitations

- **The two checks above require someone to run the app.** Specifically:
  - **Check 1** (confirm the fix, live): with the app running normally, start a small data update for
    "today" through the existing Data page, and watch the Backtest page while that update is still in
    progress — it should keep showing yesterday's real numbers with a small "refreshing" notice, never a
    blank/empty message.
  - **Check 2** (confirm the never-used-database message, one-time): start a SECOND, temporary copy of the
    backend pointed at a throwaway, empty copy of the database (the real database is never touched by
    this) on a spare port, and load the Backtest page against it — it should show the "not yet computed"
    message. This is a one-time visual check; the exact commands are in the developer handoff
    (`docs/handoffs/goal-ops-hardening-iter-17-dev.md`).
  - **Check 3** (re-measure the occasional slow loading): a repeat of the same measured pass from the
    previous iteration, run while the app is under normal data-update load, to see whether the slow-loading
    rate has changed. Also detailed in the developer handoff.
- **The occasional slow page load during data updates is unresolved.** It never produces wrong data or a
  crash — the page always eventually shows correct numbers — but roughly 1 in 6 loads during an active
  data update can take a few seconds longer than usual. This is disclosed, not hidden, and is a candidate
  for a future iteration once there's a way to watch it happen live.
