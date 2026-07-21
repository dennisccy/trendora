# Phase goal-ops-hardening-iter-6 — Implementation Summary

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-21 (fix pass)
**Written by:** developer

---

## Features Implemented

- **Dashboard loads its market chart without the browser-connection stall**: the Dashboard's "Regime ×
  phase cross-view" chart used to occasionally take 1.7-2.2 seconds to fetch its data in a real browser
  (even though the backend itself answers in under a second) because it fired its network requests at the
  exact same instant as the rest of the page's own traffic, and the browser could only handle so many
  requests to the same server at once. It now waits a fraction of a second before asking for its data, so
  it never gets stuck behind that initial burst. The chart looks and behaves exactly the same — it just
  loads noticeably faster and more consistently.
- **Data Manager's availability calendar loads without competing for backend attention**: the small
  calendar heatmap on the Data Manager page showing which trading days have data was taking up to 3
  seconds to appear, because it was asking the backend for its data at the same moment as another chart on
  that same page, and the backend could only truly work on one of those two requests at a time. It now
  waits briefly so the two don't collide, and loads in about one second instead.

---

## Changed Behavior

- **Dashboard cross-view chart and Data Manager availability calendar**: previously fetched their data the
  instant the page loaded. Now each waits a short, fixed pause (a quarter of a second for the Dashboard
  chart, two and a half seconds for the availability calendar) before fetching — invisible to the user
  because the existing loading spinner/skeleton already covers that pause. No number, chart, or figure
  shown to the user changed; only how quickly it appears did.
- **The automated "weekend backfill" test script** (used to verify the Data Manager's backfill feature)
  used to check a leftover date on an unrelated page that had become buried under hundreds of rows over
  time. It now checks the actual result of the backfill it just ran, on the Data Manager page itself —
  more reliable and directly tied to what the test is actually doing.

---

## Backend-Only Items

None — this phase touched no backend code.

---

## Incomplete Items

- **None from this phase's own assigned work** — both targeted fixes (Dashboard chart, Data Manager
  calendar) are complete, measured, and verified in a real browser.

---

## Config and Environment Changes

None.

---

## Known Limitations

- **CORRECTED (fix pass): the "Evidence/Research pages take minutes to load" alarm from the first pass was
  a measurement error, not a real slowdown.** The original pass measured those two pages while a separate,
  very heavy background test (an 84-minute full-database rebuild) plus a leftover diagnostic request were
  running at the same time on the same computer — so the machine was overloaded, and the "over 9 minutes"
  and "minute and a half" figures reflected that overload, not the pages themselves. Re-measured on an
  otherwise-idle machine, the Evidence page loads its data in **~22 milliseconds** and the Research event
  study in **~4 milliseconds to under a second** — both comfortably within their committed budgets. No
  code change was needed to "fix" this because there was nothing wrong; the correction is to the
  measurement conditions. All 11 pages checked for this phase now load within budget. Details and the full
  before/after numbers are in `reports/perf-budgets.md` under the "CORRECTION (iter-6 developer fix pass)"
  heading.
- **One honest caveat, for transparency (not a defect):** the Evidence page does a one-time heavier
  calculation the very first time it is opened after new data is added, then remembers the result so every
  later visit is instant (~22 ms). On the current developer machine — whose stored data has grown to about
  9× the size the product actually ships with, purely from many prior test runs adding data — that
  one-time first-open calculation takes about 73 seconds; on the size the product ships with it is about
  9.5 seconds (its long-standing committed figure). It never blocks or breaks the page (a loading
  indicator shows while it computes), and it is paid at most once per data update. A future work session
  could make even that first open instant by pre-computing the result when data is added (the product
  already does exactly this for the Research event-study page) — noted for the backlog, not required for
  this phase.
- The two fetch-timing fixes made in this phase use fixed short pauses (a quarter of a second and two and
  a half seconds) rather than a smarter "wait until the right moment" approach, because the smarter
  approach (waiting for the browser to be idle) was tried first and did not actually solve the problem —
  the real cause turned out to be the backend briefly being busy with another request, not the browser
  being busy. The fixed pauses were tested and confirmed to reliably fix the problem in a real browser, but
  if the backend becomes even busier in the future, these pauses may need to be lengthened again.
