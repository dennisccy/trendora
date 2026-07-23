# Phase goal-ops-hardening-iter-15 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## Context

Zero files under `apps/frontend/` appear in this iteration's diff (confirmed via `git status`: only
`apps/backend/app/engine/forward_testing.py` [modified], `apps/backend/tests/test_forward_testing_concurrency.py`
[modified — three new tests added], and `reports/perf-budgets.md` [modified — a non-UI reporting
artifact] changed at the product/test level; `runs/goal-session-ops-hardening/state/blueprint.md` is
pipeline-internal planning state, not shipped product). The plan's `Frontend Present: no` is literally
accurate. Per this dispatch's PUMP NOTE, that flag does not mean "nothing to report" here: the changed
function, `forward_aggregates_cached`, is the SAME serving/caching wrapper called from an EXISTING,
already-consumed endpoint (`GET /api/backtest`, called by `apps/frontend/lib/api.ts`'s `fetchBacktest`,
rendered on the unchanged `/backtest` page) — so a change to its concurrency behavior is real, testable,
user-facing behavior even though no frontend file changed a single line. This report documents it as a
**behavior change** to an existing page's reliability under load, matching the phase spec's own framing
("no visible surface changes when the fix holds; the delta is `/backtest`'s response time under
concurrent ingest activity").

**Honesty note before the detail below:** this iteration's own live measurement
(`reports/perf-budgets.md`, "TC-4 / TC-5 / TC-6 ... RESULTS") found the fix demonstrably closes the
*pile-up* failure mode it targeted (no evidence of redundant/stacked computation across 64 sampled
requests), but does **not** close the full 211.8-second finding end-to-end: a genuinely first-ever cold
cache-miss on the live deep-basis data still took **178.7 seconds** post-fix, and a second, separate,
unexplained slow call (**5.4 seconds**) was newly observed in the same measurement window. Both are
recorded as WARN in the project's own evidence, not smoothed into a blanket "fixed" claim. The sections
below reflect that honestly rather than overstating the improvement.

---

## What Users Can Now Do

None. This iteration adds no new user action, page, button, or displayed value — confirmed by the phase
spec itself ("New user-facing capability: None new", "New user actions: None") and by the diff (zero
frontend files touched, and the underlying calculation's output is proven byte-identical to before,
across all 5 configured horizons with and without a historical `as_of`). The nearest thing to a new
capability is a partial reliability improvement to `/backtest`'s load time under one specific condition,
described under "What Old Behavior Changed" below — with the important caveat that the improvement is
real but incomplete (see Context above).

---

## What Changed in the Visible UI

None. No page, component, label, or layout was edited — everything a user sees today looks and reads
exactly as it did before this iteration. The change is entirely underneath one existing surface's
runtime behavior under one specific condition (a concurrent cache-miss on `/backtest`'s per-horizon
data); see "What Old Behavior Changed" below.

---

## What Old Behavior Changed

- **`/backtest`'s per-horizon evidence panel, when multiple requests for the SAME not-yet-cached
  horizon/date land at the same moment** (e.g., your own page load landing while the background
  data-refresh job's warm loop is computing that same horizon, or two tabs/users opening the page for
  the same not-yet-viewed date at once): previously, EACH simultaneous request redundantly redid the
  full expensive calculation from scratch — so the more requests that happened to land together, the
  slower ALL of them got, compounding badly (a same-shape practice-scale test measured this compounding
  at 9.91x a single request's time with just 5 concurrent requests; the live, full-scale version of this
  exact compounding was iter-14's 211.8-second finding). Now, only the very first request does the real
  work; every other request asking for the same thing at the same moment waits briefly (up to 45 seconds)
  and reuses that one answer instead of repeating it. Proven via automated tests (5 concurrent requests
  for the same never-before-loaded data now trigger the underlying calculation exactly once, not five
  times, and all 5 get byte-identical results) and via one live, full-scale run (all 64 polled
  `/backtest` requests during an ~11-minute concurrent data-refresh window resolved independently — none
  stacked redundant work on top of another).
- **What did NOT change, and remains slow:** a request that is the ONLY one asking for a given
  not-yet-cached horizon/date (i.e., nothing else was already computing it) is not sped up by this fix —
  the underlying calculation itself is untouched and takes exactly as long as before. The live full-scale
  test confirmed this directly: one such first-ever request still took **178.7 seconds** — still far past
  the committed ≤1.5-second target, and not something this iteration claims to have resolved (this was
  never what the fix targeted; the fix targets redundant duplicate work landing on the same key, not the
  cost of the one genuine calculation that must still happen for a truly new key).
- **A second, separate slow response was newly observed and is not yet explained:** later in that same
  live test window, one additional `/backtest` request took **5.4 seconds** (5.373490s precisely) — also
  over the ≤1.5-second target, and not accounted for by either the "first-ever cold load" explanation
  above or by any known redundant-computation pattern. This is recorded honestly as an open item in
  `reports/perf-budgets.md`, not diagnosed or fixed this iteration.
- **The numbers themselves are unchanged.** Every figure `/backtest` displays (the by-horizon scorecard,
  return-attribution lists) is proven byte-for-byte identical to before this iteration across all 5
  configured time windows, with and without a historical date selected (the existing 32-check automated
  test suite re-ran unmodified and all still pass) — this iteration only affects how long you wait to
  see them, never what they say.

---

## Not Visible Yet

- **No on-screen indicator distinguishes any of the states above.** A user has no way to tell, just from
  looking at the page, whether their request was "the first one" (full wait), "a waiter that got a fast
  shared answer" (the sped-up case), or one of the two still-slow cases described above — the page shows
  the same loading skeleton and the same eventual result either way; only browser network-timing tools
  would reveal the difference. No progress indicator or elapsed-time affordance was added this iteration
  (the phase spec explicitly defers that to a later iteration, only if needed).
- **The same "no de-duplication on a concurrent cache-miss" pattern was found, unaddressed, in four
  sibling caches** that this iteration did not touch, test, or measure: the Event Study lab
  (`GET /research/event-study`), the Market Phase read (`GET /market-phase`), the `/evidence` page's
  drawdown-expectations panel, and the index-series read behind the dashboard/Data Manager index chart
  (`GET /api/indexes`). None of these has ever been confirmed to produce a live symptom, and this
  iteration's developer explicitly flagged investigating them as a decision for a future iteration, not
  this one's to make — noted here only because it means a comparable slow-stacking experience is
  theoretically still possible on those OTHER pages, even though `/backtest`'s own version of it is now
  improved.
- **The final full-scale confirmation is honest but incomplete, per the Context note above** — it proved
  the pile-up fix works, but also surfaced that the underlying ≤1.5s budget is still not met in two of
  the 64 sampled requests this run (the 178.7s cold miss and the unexplained 5.4s spike). Whether that
  residual gap needs further work (a fix, an accepted-constraint decision, or a loading/progress
  affordance) is an evaluator/owner call, not resolved by this report.
