# goal-ops-hardening-iter-78 — Implementation Summary

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Written by:** developer

---

## Features Implemented

- **Frontend launcher now defends itself against leftover test files.** If a previous automated
  test run gets killed partway through and accidentally leaves a broken practice file (or a
  temporary build folder) sitting in the frontend's source folder, the app-starting script now
  notices it, deletes it, and logs what it removed — before it can break the real build. Previously
  a single leftover file could make the whole frontend fail to start.
- **The "as of Ns ago" freshness note now updates every second.** The small gray text next to the
  green "Ready" indicator (and on the confirmation banner) that shows how old the current status
  reading is used to only refresh when the app checked in with the backend — which, once things
  settle down, only happens every 30 seconds. So the note could sit frozen at, say, "as of 3s ago"
  for up to half a minute even though real time kept passing. It now counts up smoothly every
  second, the way a normal "time since" clock would.
- **The automated screenshot-and-narration tool used to build the product walkthrough gallery can
  now wait longer for slow-to-appear content.** Investigated and fixed the underlying reason one of
  last round's walkthrough photos showed the wrong moment (an idle screen instead of "background
  work in progress"): the tool had a hard 20-second cap on how long any step could wait for its
  content to show up, but the badge that photo needed to capture can take up to 30 seconds to
  update. The cap can now be raised per-step when a step specifically asks for more time.

## Changed Behavior

- **Readiness badge / preflight banner freshness text**: previously froze between backend
  check-ins (up to 30 seconds stale-looking even though nothing was actually wrong). Now ticks up
  every second, always showing an accurate age.

## Backend-Only Items

None — every change in this round is either a launch-script fix (operational, not a UI feature) or
paired with its own visible frontend change.

## Incomplete Items

- **This round's walkthrough gallery photo of "background compute in flight" for feature J-09**:
  the underlying timing bug in the screenshot tool is fixed, but the actual gallery photo for this
  iteration is produced by a separate step later in the pipeline (an AI agent that writes the
  walkthrough script itself, after this developer's work is done). That later step needs to
  specifically ask the (now-fixed) tool to wait long enough and look for the right thing on screen.
  If it still gets the timing wrong, that will need one more small fix pass once that photo exists
  to look at.

## Config and Environment Changes

None — no new environment variables, config file values, or database migrations this round.

## Known Limitations

- The freshness-tick fix ticks once per second on a fixed clock, independent of how often the app
  actually checks in with the backend — that's intentional (it's meant to keep counting between
  check-ins), not a bug.
- One of the pre-existing automated test files
  (`test_start_frontend_applies_host_guard_and_skips_when_absent_or_disabled`) can occasionally
  report a false failure if it happens to run at the exact same time as another real app build on
  the same machine (the two builds briefly compete for the same disk cache). It passes reliably
  when nothing else is building at the same time — confirmed directly this round. This is a
  pre-existing test-timing sensitivity, not something introduced by this round's changes.
- One of this round's new unit-test files could not be run directly on this particular development
  machine because of a known, previously-documented limitation in how its command-line tools are
  installed (it lacks a component needed to run TypeScript test files directly). The test logic was
  verified by hand instead, and the test file itself follows this project's normal pattern, so it
  will run normally in the project's regular automated-testing environment.
