# goal-ops-hardening-iter-51 Dev Handoff

**Phase:** goal-ops-hardening-iter-51
**Date:** 2026-08-06
**Agent:** developer
**Status:** complete

## What Was Built

- **New finalize-tail warm phase `factor_lab_all_warm`** (`_refresh_ingest_aggregates`,
  `apps/backend/app/engine/data_manager.py`): calls `research.factor_lab_all_cached(session, cfg,
  as_of=None)` — the SAME function `GET /api/research/factor-lab?all=true` calls on the request path —
  from inside every ingest job's finalize tail (fetch/backfill/rebuild), immediately after
  `index_series_warm`. Mirrors the existing `research_hot_keys_warm`/`index_series_warm` phases exactly:
  own try/except, `MemoryError` caught distinctly (logs + `_release_process_memory()`), a `prog.tick()`
  heartbeat stamped immediately before the call (this single call can run several minutes), and a
  `"J-05 finalize-tail phase timing"` log line unconditionally. Unconditional — not gated on
  `prog.new_snapshot_dates` — because the cache key is the GLOBAL dataset-version stamp, the same reasoning
  already used for `forward_aggregates`/`index_series`.
  - **Honesty gate:** `factor_lab_all_cached` never lets a `MemoryError` escape — it catches it internally
    and returns a degraded payload (`factors_status: "unavailable"`, or a per-`(factor,horizon)`
    `by_horizon[].status: "unavailable"`) that is deliberately never persisted to `EventStudyCache`. The new
    phase inspects those SAME degrade signals before appending `"factor_lab_all"` to `aggregates_refreshed`
    — "the call didn't raise" is not treated as sufficient proof a fresh row was written.
  - `aggregates_refreshed`'s legal member set gains `"factor_lab_all"` (docstrings on `JobProgress` and
    `_refresh_ingest_aggregates` updated to list it).
- **Bounded `_combination_cohort_members`'s `strict_members` construction**
  (`apps/backend/app/engine/research.py:1530`): no longer unconditionally allocates `set(range(pool_n))`
  before reducing it by intersection (the exact frame logged immediately before the 2026-08-05 17m30s
  wedge). Now starts the AND-intersection from a COPY of the first single-condition membership set (copied
  because `&=` mutates in place and `single_members[0]` is a shared reference returned to every caller), or
  an empty set when `resolved` has no conditions. Pure allocation-strategy change — the full range under
  intersection is the identity element, so the result is mathematically identical; proven byte-identical
  against a pinned pre-fix reference oracle.

## Files Changed

- `apps/backend/app/engine/data_manager.py` -- new `factor_lab_all_warm` finalize-tail phase (~55 lines,
  after `index_series_warm`, before `drawdown_expectations_warm`); one new import
  (`factor_lab_all_cached` from `app.engine.research`); `aggregates_refreshed`'s documented legal set
  extended in two docstrings.
- `apps/backend/app/engine/research.py` -- `_combination_cohort_members`'s `strict_members` construction
  bounded (removed the unconditional `pool_n = len(pool)` / `set(range(pool_n))` allocation). No
  signature or behavior change to `factor_lab_all_cached`/`compute_factor_lab_all` themselves.
- `apps/backend/tests/test_data_manager.py` -- 6 new tests for the `factor_lab_all_warm` phase: cache-row
  creation + correct `EventStudyCache` identity on a MISS, unconditional warm even with zero new snapshot
  dates, a second call is honestly reported on a genuine cache HIT (no duplicate row), `MemoryError`
  isolation (`_release_process_memory()` called, category honestly omitted, other categories unaffected),
  a generic-exception isolation variant, the whole-response-degrade honesty gate (a non-raising but
  degraded payload must never be reported as refreshed), and the phase-timing log line's presence. Also
  extended `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates` and
  `test_finalize_hook_never_raises_even_when_everything_fails` to include the new category.
- `apps/backend/tests/test_research_streaming.py` -- 2 new tests for the `_combination_cohort_members`
  bound: byte-identical `single`/`strict`/`composite` output vs. a pinned pre-iter-51 reference
  implementation (a verbatim copy of the OLD `set(range(pool_n))` code path) on a representative
  `pool_n=5,000` synthetic fixture, and a monkeypatch-based proof that `set(range(pool_n))` is never
  called inside the function's own body.
- `reports/perf-budgets.md` -- new `## Item T` / `### Addendum 11` (append-only): the live-measured
  `factor_lab_all_warm` phase cost, the reconciled finalize-tail total against the existing 1,200s TC-1
  budget, and a new disclosed finding (see Known Issues).
- `docs/handoffs/goal-ops-hardening-iter-51-dev.md` -- this file.

No schema/migration changes — `EventStudyCache` (the table `factor_lab_all_cached` already writes to
under the `_ALL_FACTORS_SUBJECT`/`_ALL_FACTORS_VIEW` sentinel) is pre-existing and unmodified.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q -p no:randomly`

- `tests/test_research_streaming.py -k "combination_cohort_members"` -- 2 passed (the two new TC-4 tests)
- `tests/test_data_manager.py -k "factor_lab_all or finalize_hook"` -- 41 passed (the 6 new tests plus
  every existing finalize-hook test, confirming no regression)
- `tests/test_factor_lab_all.py` (full file, unmodified by this iteration but directly downstream of the
  `_combination_cohort_members` change via `compute_factor_combination`) -- 34 passed
- `tests/test_research_streaming.py` (full file) -- 83 passed
- Total: **160 passed, 0 failed** across the targeted + full-file runs above. The full backend suite was
  NOT run (this project's 30-year test basis makes a full `pytest tests/` run ~10-11 hours; targeted files
  directly touched or downstream of the diff were run instead, per this project's own established
  convention).

## Live/in-app verification (beyond unit tests)

Per this iteration's plan, a real backfill was run through the actual product (`scripts/start-backend.sh`,
`POST /api/data/jobs`, `kind: backfill`, offline/seed-only) to capture a genuine measurement of the new
phase's wall-clock cost, not just its unit-tested behavior. Full detail, raw numbers, and the reconciled
budget are in `reports/perf-budgets.md` Item T / Addendum 11. Headline results:

- **TC-1 proven live, in-app:** the persisted job record's `aggregates_refreshed` list contains
  `"factor_lab_all"`, and a matching `EventStudyCache` row exists at the run's own fresh dataset-version
  stamp (`subject=__all_factors__ view=factors_table asof_key=all horizon=20`) — verified directly against
  the database, not inferred from logs alone.
- **factor_lab_all_warm's own cost: 583.76s** (in line with the previously-recorded 578-875s range for
  this same compute on the request path — moving WHEN it runs, not what it costs).
- **Finalize-tail total (all 8 phases): 1,048.17s**, still under the existing 1,200s TC-1 budget by
  151.83s (12.65% margin) in this one warm-DB run — see Known Issues for the single-sample caveat.
- **Zero `MemoryError`/Traceback** anywhere in the run; process VmPeak 3,652.4 MB against the 8192 MB cap
  (55.4% margin).
- A **new, disclosed finding**: even with NO concurrent user request, 9 of 653 `GET /api/health` polls
  got no response at all (connection-level, not slow) during the new phase's own window. See Known Issues.

## Known Issues

- **A solo run of the new phase produced 9 connection-level `GET /api/health` non-responses (curl
  `code=000`, ~5s each), all inside the `factor_lab_all_warm` phase's own window, none anywhere else in
  653 polls over ~18 minutes.** This is a NEW finding this iteration's own change surfaces: even without a
  concurrent Factor Lab/Factor Combination request racing the warm, the new phase's background-thread
  compute alone can occasionally starve the event loop past a full connection cycle, not merely slow it.
  Per goal.md's owner amendment, this remains a genuine J-07 failure class ("a frozen or unresponsive
  window... remains a failure") even under the relaxed ≤2s during-background-compute ceiling. Not fixed
  this iteration — out of scope per this iteration's own NOTES ("closing J-07 step 2's ≤2s-during-ingest
  ceiling in full... is not this iteration's deliverable"). Full data and a methodological caveat (the
  health poller shares the same host, so a poller-side contribution cannot be fully excluded, though the
  precise within-phase clustering argues against pure noise) are in `reports/perf-budgets.md` Addendum 11.
- **The finalize-tail total (1,048.17s vs. the existing 1,200s budget) is a SINGLE sample under warm-DB
  conditions**, not the binding "≥3 samples" convention iter-49 established, and was measured against the
  real long-lived committed DB (warm OS page cache) rather than iter-49's fresh-throwaway-copy methodology
  (cold page cache) — the two are not directly comparable sample-for-sample. A cold-copy re-run could
  plausibly land closer to, or past, 1,200s. Disclosed in the addendum; the 1,200s figure itself is not
  re-certified or changed by this one run.
- **The full concurrent TC-5/TC-6 drill (a live Factor Lab/Factor Combination request issued WHILE the
  finalize tail's warm phases are running, mirroring the iter-50 wedge scenario) was not run this pass.**
  This developer pass ran a solo (non-concurrent) measurement only, consistent with Addendum 7's own
  precedent (iter-50 developer pass) of deferring the full concurrent live drill to the
  browser-qa-agent/audit lane per the phase spec's own division of labor. TC-3's browser time-to-interactive
  measurement is likewise deferred to that lane.
- **J-07 step 2's ≤2s-during-ingest ceiling is not closed in full** — a residual breach was already
  disclosed as carried before this iteration (goal.md's "Honest limit, stated up front"); this iteration
  does not claim to close it, and the new finding above adds to, rather than resolves, that disclosure.
- **A first attempt at the live measurement drill (targeting `2011-03-15`) was interrupted mid-compute**
  when its backing process was reaped at a harness session boundary — a subagent tooling limitation
  (background processes not surviving a turn boundary unless detached via `setsid` and polled in-turn),
  unrelated to the product code. `2011-03-15` was left snapshotted but without a persisted
  `EventStudyCache` row for `factor_lab_all` (the compute never reached its own commit). The measurement
  above is from a clean second attempt against `2011-03-16`. No product code or test was affected; noted
  here only so a later date-availability check does not misread why `2011-03-15` is snapshotted but its
  Factor Lab cache looks stale.
- **`docs/goal.md`'s own OUT OF SCOPE list explicitly excludes**, and this iteration does not touch: moving
  `compute_factor_lab_all` to a separate process/worker boundary; `server.memory_cap_mb`/
  `malloc_arena_max`/`host-guard.env` values (AG-10 frozen — confirmed untouched via
  `git diff --stat`, both before writing code and after); the columnar `_FactorCoreRecords`/
  `_FactorObsPool` bound, the single-flight waiter cooldown, and `phase_context_by_date` (all DONE per
  `iteration-state.md`'s binding "Do not redo" list); `_try_acquire_drawdown_warm`/`_release_drawdown_warm`
  (the owner-deferred `iter-50/cc` interlock spec contradiction).

## Suggested Next Phase

The structural fix this iteration delivers (warm at ingest, not on the request path) is proven live and
closes the multi-minute-cold-page-load class of failure. The one clearly-actionable next step is the NEW
finding above: even a solo finalize-tail run of `factor_lab_all_warm` produced brief connection-level
`/api/health` non-responses. Before the next iteration decides how to spend its "one risky change," it
should have the browser-qa-agent/audit lane run the FULL concurrent TC-5/TC-6 drill (a live Factor Lab
request issued mid-warm) plus TC-3's browser measurement — both still outstanding — since those results,
taken together with this addendum's solo finding, will determine whether J-07 step 2's ceiling needs a
scheduling-side fix (moving the compute off the event-loop-adjacent thread pool, or chunking the
CPU-bound loops with explicit yield points) rather than another memory-side change.
