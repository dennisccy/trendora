# Phase goal-ops-hardening-iter-78 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

<!-- This iteration ships no new user action or new capability (spec: "New user actions: none").
     It is a consolidation/refinement pass. The one behavior a user can newly rely on: -->

- Users can now trust the small gray "as of Ns ago" freshness label — shown next to the green
  "Ready" pill in the top-right header on every page, and again inside the preflight banner strip
  under the header — to always reflect real elapsed time. Previously the number could sit frozen
  (e.g. stuck at "as of 3s ago") for up to 30 seconds at a stretch; it now counts up every second
  like a normal clock, so a user glancing at it mid-session sees an accurate age rather than a
  stale-looking number.
- Users are less likely to ever encounter a completely broken/unreachable frontend: a specific
  failure mode where a leftover test file could make the entire app fail to start is now
  automatically defended against by the launch script (see "Not Visible Yet" — this is an
  operational fix with no direct UI element of its own, but its absence previously meant "the
  whole product is down," so its presence is what keeps every other row in this report reachable
  at all).

---

## What Changed in the Visible UI

- The readiness badge's staleness annotation (`data-testid="readiness-staleness"`, the "as of Ns
  ago" text next to the "Ready" pill in the top-right header, present on every page) now updates
  every second instead of only when a new backend health check lands (health checks happen every
  30 seconds once the backend is steady-state `Ready`).
- The preflight banner's staleness annotation (`data-testid="preflight-staleness"`, the
  parenthetical "(as of Ns ago)" shown next to the "GO — today's board is current." message, or
  next to a "DEGRADED"/"NO-GO" warning, in the strip directly under the header on every page) ticks
  on the same live, per-second cadence.
- No new badge, chip, page, panel, button, or menu item was added. No label text, icon, or color
  changed. The layout, position, and styling of both annotations are unchanged from iter-77 — only
  how often the displayed number updates changed.

---

## What Old Behavior Changed

- **Readiness badge / preflight banner staleness annotation**: previously froze at the value from
  the last landed `GET /api/health` poll and only refreshed when the next poll landed — for up to
  the full 30-second idle poll interval, the "as of Ns ago" text could visibly stop counting even
  though real time kept passing. Now it increases by 1 every second regardless of when the next
  poll lands, so a user watching it never sees it appear stuck.
- The annotation's existing honesty rules are unchanged and still apply while it ticks: it still
  shows nothing at all when the backend has never answered a poll, when the last poll failed, or
  when the underlying value is a fresh/synchronous compute (`stale_for_s === 0`) — ticking never
  starts counting up from a value that was never meant to render.

---

## Not Visible Yet

- The frontend launcher's new defense against leftover test-residue files
  (`scripts/start-frontend.sh` now purges the known `__tc3_intentionally_broken.ts` file and any
  `.next-test-*` scratch build directory before building) has no UI element of its own — it is an
  operational/launch-time fix. A user only "sees" its effect in the negative: the specific outage
  mode it defends against (leftover residue from an interrupted automated test run breaking `next
  build`, taking down the whole frontend) can no longer happen. Verifiable only by inspecting the
  launcher's log output or the new regression test, not by clicking anything in the running app.
- This iteration's fix to the walkthrough-gallery screenshot tool
  (`scripts/automation/lib/demo_runner.py`'s per-step timeout ceiling, raised from a hard 20s cap
  to an opt-in 45s cap) has no UI element either — it only affects the internal tooling that
  captures documentation/showcase screenshots of the product for the demo gallery, not anything a
  real user of the running app interacts with. Whether it actually produces a corrected "background
  compute in flight" gallery photo for J-09 depends on a downstream step (this iteration's own
  `reports/phase-goal-ops-hardening-iter-78-demo.json`, authored later in the pipeline) setting a
  raised `timeout_ms` and a discriminating `expect` on that specific step — not yet confirmed as of
  this report.
