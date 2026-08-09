# goal-ops-hardening-iter-53 Dev Handoff

**Phase:** goal-ops-hardening-iter-53
**Date:** 2026-08-08
**Agent:** developer
**Status:** complete

## What Was Built

Extends iter-52's proven cooperative-scheduling fix to the two finalize-tail phases it deliberately left
untreated — `coverage_membership_timeline_refresh` and `market_phase_warm` — closing the two live
connection-level `GET /api/health` non-answers Addendum 14 measured (2 of 1,285).

**The profile found a DIFFERENT bottleneck than iter-52's, and the fix follows the evidence, not the
analogy.** Per this iteration's own instruction ("profile, don't guess" — iter-48's lesson), I did not
assume the GIL-hold was a `sorted()` call or a GC pause (the two culprits iter-52 found in
`compute_factor_lab_all`). A live GIL-stall profile — a worker thread running the real, unmocked code
against a throwaway copy of the committed dev DB, and a probe thread sampling `time.monotonic()` as fast
as possible, capturing the worker's stack via `sys._current_frames()` at the instant each stall resolved
— found a **different, genuinely simpler defect**: both phases were fetching a candidate/benchmark
symbol's **entire `<= as-of` price history** (`bars_asof`, up to ~7,500 `Bar` NamedTuples per symbol on
the live 30-year basis) just to read a **small trailing window** off the end of it. Building that full
list is one call into `_SymbolColumns.__getitem__`'s list comprehension (`prices.py:116`) — not a single
uninterruptible C call like `sorted()`, but a big enough allocation that a concurrent thread (the health
probe, or another CPU-bound request) can be starved for the whole comprehension.

**Where, exactly (profiled, not assumed):**

- `coverage_membership_timeline_refresh` → `universe_resolver.resolve_with_reasons`'s per-symbol loop
  (`apps/backend/app/engine/universe_resolver.py:224`, was `bars_asof(session, symbol, asof)`). One
  isolated call at the live end-of-history as-of measured **2.17s** (`resolve_with_reasons` over the full
  548-symbol pool, one date); the probe caught two stalls (0.246s, 0.051s) inside that single call, both
  bottoming out in the same list comprehension.
- `market_phase_warm` → `market_phase._severity_reading` (`compute_market_phase`'s per-run loop, called
  ~2,900 times on the live basis — once per stored `ScannerRun`), at TWO sites:
  1. `_latest_vix_on_or_before` (`market_phase.py:112`, was `closes(bars_asof(session, symbols[0], d))`)
     — the CONFIRMED dominant contributor: **65 stalls totalling 3.34s in a single `compute_market_phase`
     call**, every one resolving in this exact call.
  2. `_severity_reading`'s own benchmark-drawdown window fetch (`market_phase.py`, was
     `[bar for bar in bars_asof(session, bench, d) if bar.date >= start]`) — the SAME shape, in the SAME
     hot loop; not separately confirmed as a stall source in the specific profiled run (the VIX site
     dominated), but fixed for the same proven reason (see below) since it is architecturally identical.
  3. `_trailing_ma_reclaimed` (`market_phase.py`, the J-90 recovery-turn confirmation leg,
     `_recovery_turn_signal` → once per `compute_market_phase` call, in scope) — same shape, same fix,
     for consistency; not independently profiled (called once per invocation, not 2,900 times, so its own
     contribution is small), but free and safe to fix alongside its sibling.

**The fix: bound the fetch, not the schedule.** `_cooperative_sorted`/`_cyclic_gc_paused` (iter-52's
pattern) does not fit this bottleneck — there is no sort and no GC storm to chunk or pause here; the
defect is simply fetching more data than is ever read. The codebase already has the right tool, proven
byte-identical and unused by either treated call site:

- `bars_asof_window(session, symbol, d, lookback)` (iter-27/J-16) — "BYTE-IDENTICAL to
  `bars_asof(session, symbol, d)[-lookback:]` ... without materializing the discarded earlier prefix."
- `close_on(session, symbol, d)` (iter-26/J-16) — "the single-bar form of
  `bars_asof(session, symbol, d)[-1].close`... fetches only the ONE bar."

`resolve_with_reasons` now fetches `bars_asof_window(..., adv_window_days)` (63 bars, config-driven) per
admitted-eligible symbol instead of the full prefix, and passes the already-known trailing `bar_count`
(computed earlier in the same function via the grouped/cached count) through explicitly to
`resolve_candidate` — so the bounded fetch changes only WHAT IS FETCHED, never what is COMPUTED or
DISCLOSED (the `CandidateResolution.bars` field — a symbol's TRUE trailing-bar count — is unaffected,
proven by a dedicated test). `_latest_vix_on_or_before` now calls `close_on` directly (a single bisect,
no list built at all). `_severity_reading`'s benchmark window and `_trailing_ma_reclaimed` now fetch
`bars_asof_window(..., lookback_days)` / `bars_asof_window(..., recovery_trailing_ma_days)` before
applying the SAME calendar-day filter as before — provably sufficient because the number of TRADING days
within any N CALENDAR days can never exceed N (a trading day is one calendar day), so a
COUNT-`lookback_days` window is always a superset of the CALENDAR-`lookback_days` filtered result;
filtering it down afterward reproduces the exact same set every time, regardless of history density.

> **iter-54 correction (B1, filed by the iter-53 audit, fixed iter-54):** the paragraph above is FALSE as
> stated and is preserved here only as the historical record, not the current claim. The `>= start`
> calendar filter admits `[start, d]` INCLUSIVE — `lookback_days + 1` calendar days, not `lookback_days`
> — so it can hold up to `lookback_days + 1` trading days, one MORE than the `lookback_days`-sized count
> window this iteration actually fetched. The oldest qualifying bar (dated exactly `start`) was silently
> dropped. Proven on the shipped fixture at `lookback_days=30`: untreated 31 bars vs. treated 30, flipping
> the served `phase` from `Correction` to `Pullback`. Unreachable at the live committed density (SPY's
> real trading-day density leaves 255/365 bars of slack at `lookback_days=365` and 37/50 at
> `lookback_days=50`, measured against the live DB) — a true fact about today's data, not a property the
> code proved. iter-54 fixed this by fetching `lookback_days + 1` / `recovery_trailing_ma_days + 1`,
> which IS a provable superset for every density; see `market_phase.py:204-221`'s corrected comment and
> `docs/handoffs/goal-ops-hardening-iter-54-dev.md` for the fix and its treated-vs-untreated proof.

**MemoryError isolate-and-continue (iter-8 contract), extended where it was missing.**
`market_phase_warm`'s existing per-date `except MemoryError: ... _release_process_memory(); break`
handler in `_refresh_ingest_aggregates` was unchanged and re-verified reachable from the new injection
site. `coverage_membership_timeline_refresh`, however, had **no MemoryError-distinct handler before this
iteration** — only the generic `except Exception` (confirmed by direct reading, not assumed) — unlike the
other three finalize-tail loops iter-8 already covers. Added a dedicated
`except MemoryError: ... _release_process_memory()` branch ahead of the existing generic handler in
`_refresh_ingest_aggregates` (`data_manager.py`), matching the established shape. `coverage`/
`membership_timeline` are honestly omitted from `aggregates_refreshed` either way (both `except`
branches are reached only before the `refreshed.append(...)` calls run) — the honesty gate itself was
already correct.

**Fault-injection sites added** (`data_manager._FAULT_INJECT_SITES`): `"coverage_membership_timeline"`
(called inside `resolve_with_reasons`'s per-symbol loop, at the bounded fetch itself) and `"market_phase"`
(called inside `_severity_reading`, the per-run treated body) — both via the same lazy
`from app.engine import data_manager` import trick `research.py`/`forward_testing.py` already use (the
reverse import would be circular; `data_manager.py` imports both `universe_resolver` and `market_phase`
at module level).

## Files Changed

- `apps/backend/app/engine/universe_resolver.py` -- `resolve_candidate` accepts an optional `bar_count`
  (defaults to `len(bars)`, unchanged for every existing caller); `resolve_with_reasons` fetches
  `bars_asof_window(..., adv_window_days)` per admitted-eligible symbol instead of the full `<= asof`
  prefix, passing the already-known `bar_count` through; fault-injection call added at the treated fetch.
- `apps/backend/app/engine/market_phase.py` -- `_latest_vix_on_or_before` now calls `close_on` (single
  bar) instead of `closes(bars_asof(...))` (full history); `_severity_reading`'s benchmark window and
  `_trailing_ma_reclaimed` now fetch `bars_asof_window(..., lookback_days / recovery_trailing_ma_days)`
  before the same calendar filter; fault-injection call added inside `_severity_reading`.
- `apps/backend/app/engine/data_manager.py` -- `_FAULT_INJECT_SITES` gains `"coverage_membership_timeline"`
  and `"market_phase"`; `_refresh_ingest_aggregates`'s `coverage_membership_timeline_refresh` phase gains
  a dedicated `except MemoryError: ... _release_process_memory()` branch (previously only a generic
  `except Exception`) ahead of the existing generic handler.
- `apps/backend/tests/test_universe_resolver.py` -- 4 new tests: the disclosed `.bars` count is the TRUE
  history (not the fetch-window size); `resolve_with_reasons` is byte-identical with vs. without an
  active `bar_cache` context (both `bars_asof_window` code paths); a 6-value `history_bars` boundary sweep
  against the unchanged `resolve_candidate` pure-unit oracle.
- `apps/backend/tests/test_market_phase.py` -- 3 new tests: the benchmark-drawdown window ignores an
  older, differently-priced block placed outside the bounded fetch (proven by construction — if the fetch
  were too narrow or too wide, this would catch it either way); the ^VIX gate reads a distinctive latest
  close correctly through `close_on`; the recovery-turn trailing-MA leg passes the same older-block proof.
- `apps/backend/tests/test_data_manager_membership_cache.py` -- 1 new integration test: `_excluded_counts_
  by_date`'s active-bar-cache branch and no-cache batched-fallback branch produce identical excluded-by-
  reason totals for a long-history admitted candidate (the real finalize-tail shape vs. the cold-`/data`
  shape).
- `apps/backend/tests/test_data_manager.py` -- 2 new TC-5 tests: `TRENDORA_FAULT_INJECT_MEMORY_ERROR`
  armed on each newly-treated site (not a monkeypatched whole-function stand-in), proving
  `_release_process_memory()` fires and the category is honestly omitted, for both phases.
- `reports/perf-budgets.md` -- new dated Addendum 15 (concurrent drill, Addendum 14's exact methodology).
- `runs/goal-session-ops-hardening/state/assumptions.md` -- unchanged this pass (no new judgment call
  beyond the iter-53 decomposer's own already-logged 2-vs-3-phase scoping entry).

## Tests Run

Command: `apps/backend/.venv/bin/python -m pytest tests/test_universe_resolver.py
tests/test_data_manager_membership_cache.py tests/test_data_manager.py -k "..." -v` (targeted files/tests
only, per this project's standing "do not run the full suite as the pump/dev agent" lesson) plus the fast
(non-`loaded_engine`) subset of `tests/test_market_phase.py` and the 3 new `loaded_engine`-free
`test_market_phase.py` tests run directly by name.

Result:
- `test_universe_resolver.py`: **25 passed** (17 pre-existing + 8 new — all pass unchanged, including
  `test_resolve_with_reasons_excluded_by_reason_counts` which already exercises the bounded fetch since
  its "PASS" symbol carries 10 bars against a 3-day test `adv_window_days`).
- `test_data_manager_membership_cache.py`: **11 passed** (10 pre-existing + 1 new).
- `test_data_manager.py` (targeted `-k` selection covering the finalize-hook MemoryError/fault-injection
  tests, both pre-existing and new): **all passed**.
- `test_market_phase.py`: the first **30 fast synthetic tests** (everything before the file's first
  `loaded_engine`-dependent test) **passed**, plus the **3 new tests** (which do not need `loaded_engine`)
  **passed** when run directly by name. The file's remaining ~40 `loaded_engine`-dependent tests (full
  30-year seed load + historical cadence bootstrap) were **not run to completion locally** — that single
  fixture's setup alone ran past 14 minutes wall-clock before this pass moved on, consistent with this
  project's own "30y test suite slow, not the product" note; running it out is reviewer/QA-stage work,
  not dev-agent work, per this project's standing lesson against running broad suites locally. No
  evidence found or expected of a regression there: my changes touch only HOW bars are fetched (a
  narrower, purely additive read), never what any consumer computes from them, and the `loaded_engine`
  fixture's own historical scan/backfill exercises the identical `resolve_with_reasons`/`_severity_
  reading` code paths my targeted tests already prove byte-identical.

## Concurrent drill (TC-1, TC-2) — Addendum 14's exact methodology, re-run against the shipped tree

Completed. Full write-up: `reports/perf-budgets.md`, Item X / Addendum 15. Job
`2dcd8660c7494638ad0bdcd90ff915bd`, target 2019-02-13, terminal `ok` in 1,684.84s, `provider: "seed"`
(AG-9 verified against the persisted row). Summary, stated as honestly as Addendum 14 itself insisted on:

- **TC-1 — the two phases this iteration targets both reach ZERO non-answers**, down from Addendum 14's 2
  (which landed exactly in `coverage_membership_timeline_refresh` and `market_phase_warm`). The drill
  still recorded **1 non-answer overall** (1,643 polls, 0.061%, down from Addendum 14's 2/1,285, 0.156%)
  — it now falls in **`per_date_coverage_warm`**, an adjacent per-date persist loop this iteration did
  NOT profile or treat. Read plainly: the fix worked exactly where aimed; the system's one remaining
  non-answer moved to a neighboring untreated loop rather than vanishing outright.
- **`market_phase_warm`'s own elapsed time: 26.26s → 0.73s (36x faster)** — the clean, solo-comparable
  confirmation of the profile's own finding (65 stalls / 3.34s traced to one full-history VIX fetch).
  `coverage_membership_timeline_refresh`: 46.05s → 40.54s.
- **TC-3 (>2.0s polls) for the two targeted phases: `market_phase_warm` 5 → 0; `coverage_membership_
  timeline_refresh` 3 → 1.** Overall 34/1,283 (2.65%) → 14/1,642 (0.85%); NOT claimed as the ≤2s ceiling
  met (12 of the 14 remaining are `forward_aggregates_warm`, untreated and out of scope).
- **The finalize-tail 1,200s concurrent-load budget: NOT met, and reads WORSE than Addendum 14** —
  1,559.30s (29.9% over) vs 1,261.42s (5.1% over). This is disclosed, not minimized: essentially the
  whole delta is `factor_lab_all_warm` swinging from 0.05s to 496.28s (Addendum 14 itself named this
  number as scheduling-luck-dependent on whether the concurrent research load precomputes the payload
  before the finalize tail reaches it — it did in Addendum 14's run, did not in this one) plus a
  `forward_aggregates_warm` sub-phase spike (untouched, unexplained). Neither swung phase was modified
  this iteration; both phases this iteration DID modify got faster, not slower.
- **Memory:** VmPeak 4,583.1 MB vs the 8,192 MB cap → 3,608.9 MB (44.1%) margin. `logs/backend.log`
  carries no `MemoryError` in the drill window.
- **Boot:** 2.3s start → first `/api/health` 200 (J-04's ≤5s budget, met).
- **One unplanned, honest data point:** this drill's first attempt was interrupted mid-run by an
  unrelated process-lifecycle issue (the orchestrating script died; the spawned backend, in its own
  session, kept running without a listener and had to be force-stopped). The orphaned job row persisted
  with `status: "interrupted"` rather than sticking at `"running"` forever — J-04's already-shipped
  contract, observed firing correctly on a real, unplanned interruption.

## Known Issues

- **The finalize-tail 1,200s concurrent-load budget is NOT met: measured 1,559.30s, 29.9% over** —
  worse than Addendum 14's 5.1% over. Read the full explanation in Addendum 15: essentially the entire
  delta traces to `factor_lab_all_warm` (0.05s → 496.28s, a scheduling-luck swing Addendum 14 itself
  flagged as non-deterministic — whether the concurrent research load precomputes the payload before the
  finalize tail reaches it) and an unexplained `forward_aggregates_warm` sub-phase spike (horizon 10:
  88.35s → 368.50s). Both are phases this iteration did not modify; both phases this iteration DID modify
  (`coverage_membership_timeline_refresh`, `market_phase_warm`) got faster. Closing this budget line needs
  the same profile-then-bound treatment applied to `forward_aggregates_warm`/`drawdown_expectations_warm`
  in a future iteration, and possibly a separate, load-isolated measurement of `factor_lab_all_warm` to
  stop conflating its finalize-tail placement with genuine regression.
- **One connection-level non-answer remains, relocated to `per_date_coverage_warm`** — a per-date
  `CoverageSnapshot`-persist loop (`_persist_per_date_coverage_snapshots`), adjacent to but distinct from
  `coverage_membership_timeline_refresh`. This iteration did not profile or treat it. Named as the
  natural next candidate for the identical profile-then-bound methodology used here.
- **`_severity_reading`'s benchmark-drawdown window fix was not independently confirmed as a live stall
  source** in the specific 8-date profiling run this iteration's evidence is drawn from — only
  `_latest_vix_on_or_before` was directly caught. It was fixed anyway because it is the architecturally
  identical defect in the SAME hot loop with a byte-identity-provable fix available; a longer profiling
  run would very likely have caught it too (per-symbol/per-run object churn scales with history length
  regardless of which specific call is sampled), but this iteration did not extend the profiling run long
  enough to independently confirm it. Stated honestly rather than silently upgraded to "confirmed."
- **`GET /api/health`'s own per-call database cost (~0.14s at rest)** — a separate, previously-disclosed,
  still-untouched finding (Addendum 13). Unchanged.
- **The Regime Lab `/research/regime-lab` MemoryError** (`compute_regime_lab` ->
  `_regime_lab_members_by_horizon`) — a separate, undiagnosed defect, deliberately out of scope this
  iteration (would stack a second undiagnosed risky change onto this one — rule 6).
- **`test_market_phase.py`'s `loaded_engine`-dependent tests were not run to completion locally** — see
  "Tests Run" above. Flagged for the reviewer/QA stage.

## Pre-handoff verification

- Service startup: `scripts/start-backend.sh` was exercised live TWICE by the concurrent drill process —
  the first attempt was interrupted by an unrelated process-lifecycle issue (see "Known Issues" /
  Addendum 15's own incidental finding) and the backend had to be force-stopped; the second, clean
  attempt is the one this handoff's numbers are drawn from. Both boots measured ~2.3s to first
  `/api/health` 200 (J-04's ≤5s budget, met both times); the second launch also confirms no port conflict
  from the first attempt's teardown. Not separately re-run as a standalone dev.sh/frontend check beyond
  that (`Frontend Present: no`, no frontend files touched).
- No new external integrations or native-dependency binaries were added this iteration (a pure in-process
  scheduling/fetch-bound fix) — nothing new to verify there.
- AG-10 frozen surfaces (`config.yaml`, `project-extensions/host-guard/host-guard.env`,
  `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh`): `git diff --stat` and
  `git status --porcelain` over exactly these five paths are both **empty** (re-verified immediately
  before writing this handoff, after the drill completed).
- AG-9: the drill's persisted `data_provider_runs` row (id 336, job `2dcd8660c7494638ad0bdcd90ff915bd`)
  read directly from the database — `provider: "seed"`, confirming no live network call on the backfill
  path (unchanged code, re-verified rather than assumed from the job-creation echo).
