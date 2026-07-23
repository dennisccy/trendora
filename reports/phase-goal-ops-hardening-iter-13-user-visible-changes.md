# Phase goal-ops-hardening-iter-13 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-13
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. No new user action, button, form, filter, or navigation target was added this iteration. This
matches the plan/spec exactly — goal.md and `runs/goal-ops-hardening-iter-13/plan.md` both state "no
product source changes anticipated" and "New user actions: none," and this is confirmed independently: `git
status`/`git diff --stat` show zero files under `apps/frontend/` in this iteration's diff.

---

## What Changed in the Visible UI

- **Page-load speed of the major-indexes chart (Dashboard `/`) and the index-vendor panel (Data Manager
  `/data`).** Both surfaces call `GET /api/indexes?full=true` unparameterized on mount to render their
  default ("all-history") view. That one specific view is now served from an ingest-time-warmed cache
  instead of being recomputed from the full multi-decade price history of ~10 index symbols on every
  request. The chart lines, values, and displayed as-of date are unchanged — confirmed byte-identical by
  the developer's own direct-vs-cached comparison (`direct == api → True`, full dict equality including
  `asof_date`, all 10 `series` entries, and the `range`/`ranges` blocks). This is a loading-speed change
  only, not a content or layout change — see "What Old Behavior Changed" below for the important caveat on
  whether the speed win has actually been confirmed with a real browser yet.
- **The "Refreshed: ..." summary line on `/data` can now include one new item: "index series."** This line
  already existed (added in an earlier ops-hardening iteration) on three surfaces of the Data Manager page:
  the live "Job progress" panel (while a job runs this session), the persisted "Last run summary" card
  (when no job has started this browser session), and the Run History table's per-row breakdown. It is a
  generic, comma-separated list built from whatever ingest-aggregate names the backend reports for that run
  (e.g. "latest snapshot, coverage, membership timeline, market phase, research hot keys, drawdown
  expectations"). No frontend code changed to make this possible — the rendering was already generic
  (`aggregatesRefreshed.map(a => a.replace(/_/g, " ")).join(", ")`), so it automatically picks up any new
  legal value the backend starts returning. "index series" will appear in that line only for a run whose
  ingest finalize hook actually persisted a new/refreshed index-chart cache row (i.e., a backfill, fetch, or
  rebuild that lands a new price bar for one of the ~10 configured index symbols: SPY, QQQ, IWM, RSP, DIA,
  ^SPX, ^NDX, ^DJI, ^VIX, ^TNX). A run that doesn't touch any of those symbols' bars will not show it — the
  line reads exactly as it did before this iteration.

---

## What Old Behavior Changed

- **`GET /api/indexes?full=true` (the default index-chart view, used on both `/` and `/data`):**
  previously recomputed from the full stored price history on every single request — measured at
  2138.7–2257.7ms by real-Chrome testing in the prior iteration (iter-12), over its committed 1.5-second
  budget. It is now intended to be served from a pre-computed store, refreshed only when new price data for
  a configured symbol actually changes it.
  **Important caveat (per the dev handoff, not glossed over):** as of this analysis, the canonical
  real-browser confirmation that this change actually brings the page back within its 1.5s budget has **not
  yet run**. The developer's own preliminary check used `curl`, not a browser, and showed a large
  improvement (~0.847s on the first, cold cache-miss request; ~0.065–0.09s on subsequent cache-hit
  requests) — but this project's own iter-5 finding is that `curl` systematically reads faster than a real
  Chrome page load on this exact call (Chrome's per-origin connection queuing under-reports differently).
  So the mechanism is verified to work correctly and produce identical data, but whether a real user's
  browser will now see the page load within budget is still an open, unconfirmed question pending the next
  pipeline stage (browser-qa-agent's three-load `/data` control plus a `/` spot-check).
- Every other index-chart view a user can select — a shorter preset window (e.g. "3M"), or looking back to
  a specific historical as-of date — is unchanged: still computed fresh on every request, exactly as
  before. Confirmed by the developer: a `range=3M` and an explicit historical `as_of` request neither read
  from nor write to the new cache, and produce byte-identical output to the pre-iteration code path.

---

## Not Visible Yet

- **The `IndexSeriesCache` database table, its index-scoped dataset-version freshness stamp, and the
  ingest-time warm step's `MemoryError` isolation logic** are pure backend infrastructure. There is no page,
  panel, setting, or debug view anywhere in the product that exposes the cache table, its contents, or its
  freshness stamp directly — it is observable only indirectly through the two effects described above
  (page-load speed, and the conditional "index series" item in the "Refreshed: ..." line).
- **The real-browser (Chrome) confirmation that `/` and `/data`'s default index-chart load now lands within
  its 1.5-second budget has not been produced as of this analysis.** Per the dev handoff, this is
  browser-qa-agent's job (the next pipeline stage), not something this iteration's own developer pass or
  this report can confirm. Until that measurement runs, the speed improvement above should be read as the
  *intended, mechanically-verified* effect of this change — not yet a confirmed user-facing outcome.
