# goal-ops-hardening-iter-19 — Implementation Summary

**Phase:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Written by:** developer (updated after review FAIL — attempt 3, the proven root cause)

---

## What this iteration is trying to fix

Loading the `/backtest` page (and the matching tool a connected assistant would use) has been several
seconds too slow under concurrent traffic since earlier in this cycle. The cause was internal housekeeping
the page redoes on **every** request — recomputing forward-return records — for a run whose history is
already as complete as it can be. That work was pure waste on every view.

## What changed (and why the first two attempts were not enough)

Think of a "run" as a snapshot taken on a given date, and "horizons" as how far ahead we measure results
(1, 5, 10, 20, and 60 trading days later). A horizon can only be filled in once enough calendar days have
actually elapsed after the snapshot date. The page you get **by default** is the *newest* snapshot — whose
date is today's data edge — so **none** of its horizons have elapsed yet: there is simply no future data to
measure against.

- **Attempt 1** removed a redundant database *save* on that path. A live under-load measurement showed **no
  difference** — the save was never the real cost.
- **Attempt 2** made an internal "what's already stored?" lookup read fewer columns. The reviewer's live
  measurement showed that lookup was **already cheap** (a fraction of a millisecond) — also not the real
  cost.
- **Attempt 3 (this one)** fixes the actual cost. For every symbol in the snapshot (~550 of them), the page
  was reaching into the price history **twice per un-elapsed horizon** to try to compute a result that
  cannot exist yet — about **1,100 wasted database lookups on every single request**. The fix checks
  **once**, up front, how many days have actually elapsed after the snapshot date, and then simply skips the
  horizons that have no data yet. For the default newest snapshot, that means zero elapsed horizons, so the
  whole per-symbol loop is skipped and the wasted lookups drop to **zero**.

The corrections from attempts 1 and 2 are **kept** — they are correct and complementary; they just were not
the thing that mattered for speed.

**Nothing the user sees changes.** The same numbers, evidence badges, and scorecard render exactly as
before. A skipped horizon had no result to show anyway (it correctly displays as "not yet available"), so
the page is identical field-for-field — confirmed by tests that compare the output before and after.

---

## Changed Behavior

- **`/backtest` and its MCP equivalent**: before doing its per-symbol work, the request now checks how many
  trading days are actually available after the snapshot's date and only processes horizons that have data.
  On the common case (the newest snapshot, or any run whose stored history is already complete) it does no
  price lookups and no database write at all. A run that genuinely has newly-elapsed, not-yet-stored
  horizons still computes and saves them exactly as before. The served response is byte-for-byte identical
  either way.

---

## Backend-Only Items

- The `write_taken` field in the backend's operational timing log (`logs/backend.log`) — a diagnostic detail
  (added on attempt 1, unchanged here) recording whether a given request saved or skipped. For operators
  investigating performance only; not shown anywhere in the product UI.

---

## Incomplete Items

None from this iteration's own code scope — the change and its unit tests are complete. This attempt also
includes a concrete, captured before/after measurement against the real dataset (read-only): on the current
newest snapshot the wasted lookups drop from **1,106 to 0** and the internal phase from **113.6 ms to
1.6 ms** single-threaded. The remaining step is a **live under-load re-measurement only an operator can
run** (see Known Limitations) — the standing pattern for this cycle.

---

## Config and Environment Changes

None. No new settings, environment variables, or database migrations.

---

## Known Limitations

- **The under-load speed-up is not yet confirmed on the live server.** The mechanism is proven at the
  unit-test level (identical numbers before/after; zero price lookups on the newest snapshot; safe under
  simulated concurrent requests) and by a read-only measurement against the real dataset. But the final
  "is it fast under real concurrent load" check needs an operator to **restart the real server** (to load
  this fix — the running server still has the earlier code) and re-run the same 6-way concurrent load
  measurement used last cycle, targeting an average ≤ 350 ms (down from ~880 ms). Not done yet as of this
  handoff.
- **A second, contingent measurement** — testing this fix while a real data-import job runs (the condition
  behind the worst historical slowdowns) — depends on the instance owner authorizing that import this
  session; if not authorized it will be documented as skipped, not silently omitted.
- **A related, separate pre-existing finding** (surfaced earlier in this cycle) remains open: under a very
  specific artificial pile-up of simultaneous requests on a brand-new date with several missing symbols, an
  internal save can occasionally raise an unhandled error before the existing safety net catches it. The
  reviewer explicitly asked for this to be its **own** follow-up, not bundled into this speed fix, so it was
  left untouched here.
- **A boot-time echo of the same waste** (newly noted this attempt): the once-per-startup history rebuild
  still does the same redundant per-symbol lookups for recent snapshots. It is a one-time startup cost, not
  a per-request cost, and was out of scope for this request-path fix — flagged in the developer handoff for
  the review/audit stage to consider as a future cleanup.
- A handful of other backend test files that also touch this code path were not run this session because
  they exceed this host's safe one-sitting testing budget on the deep dataset (they legitimately time out) —
  documented plainly in the developer handoff.
