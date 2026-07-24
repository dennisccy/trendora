# Phase goal-ops-hardening-iter-19 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Context: `Frontend Present: no` is accurate, but a real behavior change exists

Zero files under `apps/frontend/` appear in this iteration's diff — confirmed via `git status --short`
and `git diff --stat -- apps/frontend/` (empty output). The only files touched are three backend source
files (`apps/backend/app/engine/forward_testing.py`, `apps/backend/app/api/backtest.py`,
`apps/backend/app/mcp/tools.py`), two backend test files, and `reports/perf-budgets.md` (a non-UI
reporting artifact). The plan's `Frontend Present: no` is literally accurate.

However, per this dispatch's PUMP NOTE, that flag is not read as "nothing to report" here: this
iteration's entire purpose is removing a real, multi-second latency problem a user could hit loading the
EXISTING `/backtest` page under concurrent traffic (the shared blocker behind J-06/J-07/J-08 since
iter-11). That is genuine, measured, user-facing behavior change even though no frontend file changed a
single line. This report documents it as a **performance/latency behavior change, not a new feature or
visual change** — matching the phase spec's own "Product surface delta" framing: "`/backtest` continues
to show identical evidence and scorecard values; the only observable change is the elimination of the
multi-second slowdown a user could previously hit loading `/backtest` under concurrent load."

---

## What Users Can Now Do

None. This iteration adds no new user action or capability — confirmed by the phase spec itself ("New
user-facing capability: None directly new", "New user actions: None") and by the diff (zero frontend
files touched, and the served response is proven byte-identical to before, every configured horizon, with
and without an explicit `as_of` — TC-5, cross-checked directly against the `backtest.py`/`mcp/tools.py`
diffs: the returned dict is untouched, only an internal timing-log call gained one argument). The nearest
thing to a new capability is a reliability/speed guarantee for an existing page, described below under
"What Old Behavior Changed."

---

## What Changed in the Visible UI

None. No page, component, label, layout, or displayed field was edited — everything a user sees on
`/backtest` today looks and reads exactly as it did before this iteration (proven byte-identical, TC-2,
TC-5). The change is entirely underneath one existing page's request-handling speed; see "What Old
Behavior Changed" below.

---

## What Old Behavior Changed

- **`/backtest` page load speed under concurrent traffic.** Previously, every single load of `/backtest`
  (and every call to the equivalent MCP tool a connected AI assistant would use) redid ~550 wasted,
  pointless lookups against the price history on the backend, trying to compute results for time windows
  that have not happened yet (e.g., "what happens 60 trading days after today" when today has no
  60-trading-days-later data at all). This was pure waste on every view of the page, and it piled up
  badly whenever several people (or requests) hit the page at the same time. This iteration makes the
  page check, once per request, how much of that future window is actually available, and skip the
  lookups for the part that isn't — instead of quietly retrying and failing ~550 times per view.
  - Under a live 6-concurrent-request re-measurement (mirroring the previous cycle's own protocol,
    `reports/perf-budgets.md`), the backend-side cost of this step dropped from a mean of **877 ms** to a
    mean of **13.9 ms** (about 63x faster; max dropped from 999 ms to 73.4 ms).
    Client-observed load time for the page's data dropped from a mean of **1083 ms to 112 ms** (about
    10x faster; p99 164 ms, max 302 ms), and the same test's throughput roughly **2.7x'd** (from ~470 to
    ~1269 completed requests in the same window). All 4,793 requests in the final confirmation run
    returned successfully with the page's normal, fully-populated evidence.
  - This was NOT a one-shot fix: two earlier attempts this iteration (removing a database save that
    turned out not to be the cost, then trimming an already-cheap lookup) were tried and measured live,
    found insufficient, and superseded before the actual cause (the wasted future-window lookups above)
    was found and fixed. The number above is from the attempt that was actually measured to work.
  - A page whose forward-looking window HAS already fully elapsed (an old, historical view) is
    unaffected — it still does the same work as before, byte-for-byte.

No feature, field, or button anyone clicks changed — only how long the page takes to load under load.

---

## Not Visible Yet

- **The specific worst-case condition — a real, concurrent data-import job running at the same time
  someone is hitting `/backtest` — has not been re-measured after this fix.** The dramatic 63x/10x
  numbers above come from a pure-concurrent-reads test; the previous cycle's own finding was that pure
  reads alone did NOT reproduce the original worst-case slowdown (11 of 68 requests over budget, one as
  slow as 12.7 seconds) — only reads happening DURING a live import did. That re-test is contingent on
  the instance owner authorizing a live import this session; it had not been authorized as of this
  report, so whether the page also holds up during an actual import remains unconfirmed (not silently
  dropped — tracked plainly as open).
- **A live, single before/after request capture on the real running server, byte-diffed to double-check
  nothing about the displayed numbers moved** (beyond the unit-test-level proof already done) has not
  been captured this iteration.
- **The equivalent speed-up for the MCP `query_backtest` tool** (the same interface a connected AI
  assistant, not a person clicking a browser, would use) was implemented identically — it shares the
  exact same backend function — but it has no page of its own in this project's browser UI to observe it
  on; see the companion UI Surface Map report for why it is tracked as backend-only rather than a browser
  surface.
- **A pre-existing, separate rare-race finding** (not new, not introduced by this iteration): under a
  very specific pile-up of several simultaneous requests for a brand-new date with multiple never-viewed
  symbols, an internal save can occasionally raise an error before the existing safety net catches it.
  This was deliberately left unfixed this iteration (filed as its own follow-up) and, by the developer's
  own analysis, cannot happen on the now-fast common path measured above (that path skips the save
  entirely) — it stays confined to the rare "brand-new snapshot, several people view it at once" case.
- **A one-time echo of the same waste at server startup**: the once-per-restart historical rebuild still
  redoes the same wasted future-window lookups for recently-created snapshots. This affects only how long
  the backend takes to finish starting up, not anything a user sees while the app is running, and was
  left out of scope for this iteration (flagged for a future cleanup).
