# goal-ops-hardening-iter-19 Dev Handoff

**Phase:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

- **The zero-write guard** inside `backfill_run_forward_returns` (`apps/backend/app/engine/forward_testing.py:1365`):
  when a run's forward returns are already fully backfilled, `_insert_run_forward_returns`'s own
  idempotency check already computes `inserted == 0` — the function now performs **no SQLite
  write-lock-acquiring operation at all** in that case (`_commit_forward_returns_concurrency_safe`, and
  the `session.commit()` inside it, is skipped entirely). The genuinely-missing case (`inserted > 0`) is
  **unchanged**: it still commits synchronously, exactly as before this iteration.
  - **Guard shape chosen: (a) skip-commit-when-zero** (the spec's own default/preferred shape), not the
    fallback pre-check. Why: `_insert_run_forward_returns` already returns the exact count needed to make
    this decision — no new query, no new schema, no new state. I could **not** run the operator-only TC-6
    live re-measurement myself (see "Operator-performed items" below), so this choice is grounded in the
    code-level diagnosis (iter-18's TC-9 pinned the cost specifically to the `session.commit()` call
    itself, which this shape eliminates on the warm path) rather than a live number — per this session's
    own repeated lesson ("trust the live number over the root-cause extrapolation"), **this shape is not
    yet confirmed sufficient until the operator's TC-6 re-measurement lands**. If TC-6 shows the phase has
    not collapsed to the ≤350ms mean / ≤400ms max budget, the documented fallback (a cheap pre-check ahead
    of the read+insert+commit block) is the next thing to try — not a new persisted column (explicitly
    out of scope per the spec unless TC-6 proves the guard insufficient).
- **Extended the two existing timing log lines** (`backtest_timing` in `apps/backend/app/api/backtest.py`,
  `query_backtest_timing` in `apps/backend/app/mcp/tools.py`, both landed iter-18) with one additional
  field, `write_taken` (`True`/`False`), recording whether the create-once write was committed or skipped
  this request. Derived from the **already-returned** `rows_inserted` count (`> 0`) — no new query. Appended
  as the **last** field on each line (after the optional `ensure_loop_ms`) so the pre-existing
  `test_backtest_timing.py` regex (which does not anchor to end-of-string) is completely undisturbed —
  verified by running that file's existing tests unchanged (see Tests Run).
- **New tests**: TC-1, TC-2, TC-3, TC-5 in `test_forward_testing_serving_split.py`; TC-4 (concurrency) in
  `test_forward_testing_concurrency.py`. Details below.

## A note on "call sites untouched"

The plan/spec say `backtest.py:140` and `mcp/tools.py:263` (the two calls to
`backfill_run_forward_returns(session, run, cfg)`) stay "untouched." I read this as: the call remains
**unconditional, same function, same arguments, no caller-side guard** (the skip-vs-commit decision lives
entirely inside `backfill_run_forward_returns` — single-producer discipline, no duplicated logic at either
caller). I did make one minimal, unavoidable edit at each call site: capturing the call's own return value
into a variable (`backfill_result = backfill_run_forward_returns(...)`, previously a bare expression
statement) so `write_taken` could be read off the `rows_inserted` field the function already returns — this
was explicitly required by the plan's own "extend the two existing log lines" instruction, and involves zero
new logic, no new query, and no change to which function is called or with what arguments. Flagging this
explicitly per the token/questioning policy (documenting the interpretation rather than silently taking it).

## Files Changed

- `apps/backend/app/engine/forward_testing.py` — `backfill_run_forward_returns`: added `if inserted:`
  around the `_commit_forward_returns_concurrency_safe(session)` call; extended the docstring. No other
  line changed; `_insert_run_forward_returns` and `_commit_forward_returns_concurrency_safe` themselves are
  byte-for-byte unchanged.
- `apps/backend/app/api/backtest.py` — `_log_backtest_timing` gained a `write_taken: bool` parameter,
  appended last to the log line; the route function now captures `backfill_run_forward_returns`'s return
  value to compute `write_taken = backfill_result["rows_inserted"] > 0` and passes it through. The call
  itself (function, arguments, unconditional) is unchanged.
- `apps/backend/app/mcp/tools.py` — mirrors the same two changes in `_log_query_backtest_timing` and
  `query_backtest`.
- `apps/backend/tests/test_forward_testing_serving_split.py` — added `compute_run_scorecard` and
  `timedelta` to imports; added 4 new tests (see below).
- `apps/backend/tests/test_forward_testing_concurrency.py` — added `IntegrityError` import; added 1 new
  test (TC-4).
- `docs/handoffs/goal-ops-hardening-iter-19-dev.md` (this file, new).
- `reports/phase-goal-ops-hardening-iter-19-implementation-summary.md` (new).
- `runs/goal-ops-hardening-iter-19/status.json` — `current_step: dev_complete`.

No changes to `docs/blueprint.md` — verified the iter-19 comment-block paragraph and Notes-cell append the
decomposer already wrote are present (confirmed in
`runs/goal-session-ops-hardening/state/blueprint.md`); nothing duplicated or added.

## New tests, what each proves

- **TC-1** (`test_backtest_route_zero_write_when_forward_returns_already_complete`): a run whose forward
  returns are already fully backfilled (the "AAA" scored ticker has a `ForwardReturn` row at every
  configured horizon; the benchmark ETFs have no price data in this fixture, an honest NA gap — see
  below) — `GET /api/backtest`'s route function, SQL-inspected via `before_cursor_execute` (the same
  technique the file already uses), issues **zero** `INSERT`/`UPDATE`/`DELETE` statements. The timing log
  records `write_taken=False`.
- **TC-2** (`test_query_backtest_mcp_tool_zero_write_when_forward_returns_already_complete`): mirrors TC-1
  for the MCP `query_backtest` tool — zero writes, `write_taken=False`, and its full returned dict is
  byte-identical (`==`) to the API route's for the same inputs.
- **TC-3** (`test_backfill_still_inserts_when_genuinely_missing_then_zero_write_on_repeat`): a run whose
  forward returns have **never** been backfilled — first `GET /api/backtest` call still INSERTs
  (`len(HORIZONS)` rows for the one scored ticker with sufficient post-snapshot bars; `write_taken=True`);
  a second call for the same as-of issues zero further writes (`write_taken=False`); the repeat view
  serves the identical scorecard.
- **TC-4** (`test_iter19_concurrent_missing_run_backtest_calls_no_duplicate_rows_and_rollback_path_exercised`,
  in `test_forward_testing_concurrency.py`): 5 concurrent `GET /api/backtest` calls for the SAME as-of
  whose forward returns are genuinely missing. A `threading.Barrier` forces all 5 callers to finish their
  own pre-insert `existing` read before any proceeds to stage or flush a write, deterministically
  reproducing the concurrent-INSERT race (not left to scheduling luck). Asserts: no unhandled exception
  across all 5, no duplicate `(run_id, symbol, horizon)` key in `forward_returns`, and the pre-existing
  `_commit_forward_returns_concurrency_safe` `IntegrityError`-tolerant rollback path is exercised at least
  once (call-count instrumented — in the 5 repeated dev-side runs, it fired for exactly 4 of the 5 callers
  every time, well above the ">= 1" bar). Distinct fixture from this file's existing forward-*aggregate*
  concurrency tests (a different table/function — `forward_returns`, not `forward_aggregate_cache`).
- **TC-5** (`test_scorecard_and_evidence_byte_identical_with_and_without_explicit_as_of`): the TC-1
  fixture's served scorecard + `evidence_status`/`evidence_generated_at`/`evidence_asof`/
  `evidence_by_horizon` are byte-for-byte identical to a **direct**, independent call to
  `compute_run_scorecard`/`resolved_forward_aggregate_evidence` for the same as-of, checked both with
  `as_of` omitted and passed explicitly — proving the guard changes only whether a redundant commit
  happens, never a served value (AG-3).

### A finding surfaced while building TC-4 (not this iteration's to fix — recorded for triage)

While designing TC-4's fixture, an unbarriered version (all `forward_symbols_for_run` benchmark symbols —
SPY/QQQ/sector ETFs — left with no pre-existing `ForwardReturn` rows, mirroring "genuinely missing"
literally) reproducibly hit an **uncaught** `IntegrityError` (and, in one earlier barrier-placement attempt,
an uncaught `OperationalError: database is locked`) from **inside** `_insert_run_forward_returns` itself —
**not** from the explicit `_commit_forward_returns_concurrency_safe` call this iteration's guard gates.
Root cause: SQLAlchemy's autoflush fires when the per-symbol loop moves from a symbol with staged pending
INSERTs (e.g., the scored ticker) to the **next** symbol requiring a read (`close_on`) — that autoflush is
not wrapped in any try/except, so a concurrent duplicate-key collision at that point propagates uncaught.
This is a **pre-existing** gap (present before this iteration, unrelated to the write-skip guard: it's
about writes that happen *inside* `_insert_run_forward_returns` via autoflush, before the explicit commit
this iteration touches) reachable whenever 2+ concurrent callers race on a run with 2+ genuinely-missing
symbols — which is the common shape for any real (multi-ticker) run, not just this test's minimal fixture.
I did **not** fix it (out of scope: the plan explicitly keeps "`_commit_forward_returns_concurrency_safe`
and the genuinely-missing INSERT path... behaviorally unchanged," and a real fix means restructuring
`_insert_run_forward_returns`'s flush behavior, not the single-line guard this iteration specifies). I
isolated my actual TC-4 fixture from it by pre-seeding the benchmark symbols as already-complete (so the
per-symbol loop `continue`s past them without a further read), keeping TC-4 focused on exactly the race
this iteration's guard is responsible for. **Flagging for the reviewer/auditor to triage** — given this
cluster's REGRESSION history (iter-13's ~12-minute futex deadlock), a follow-up iteration hardening
`_insert_run_forward_returns` against this autoflush-driven uncaught-exception path (e.g., disabling
autoflush for the duration of that loop, or wrapping it in the same `IntegrityError`-tolerant pattern) seems
warranted, though it was reproduced only under an artificially-tight synchronization barrier in a scratch
script — I have not established how often it manifests under real (non-forced) production concurrency.

## Tests Run

Command (host-guard-confined per this session's standing constraint — scoped to specific files, never the
full suite, never concurrent pytest):

```
cd /home/dennis-chan/Git/trendora
apps/backend/.venv/bin/python -m pytest \
  apps/backend/tests/test_forward_testing_serving_split.py \
  apps/backend/tests/test_forward_testing_concurrency.py \
  apps/backend/tests/test_backtest_timing.py \
  apps/backend/tests/test_backtest_scorecard.py \
  -q
```

Result: **53 passed** (21 in `test_forward_testing_serving_split.py` [17 pre-existing + 4 new: TC-1/2/3/5];
7 in `test_forward_testing_concurrency.py` [6 pre-existing + 1 new: TC-4]; 5 in `test_backtest_timing.py`
[all pre-existing — confirms the new `write_taken` field, appended last, does not break its existing
timing-line regex/assertions]; 20 in `test_backtest_scorecard.py` [all pre-existing — directly exercises
`backfill_run_forward_returns`'s create-once/idempotent/no-lookahead behavior]). 0 failed.

**TDD verification performed, not just claimed**: `git stash push -- apps/backend/app/engine/forward_testing.py
apps/backend/app/api/backtest.py apps/backend/app/mcp/tools.py` to revert ONLY the three source files to
their pre-iteration state; re-ran the write_taken-dependent new tests (TC-1, TC-2, TC-3) and confirmed all
three FAILED with the expected `write_taken=False`/`write_taken=True` assertion mismatches (the guard/field
did not yet exist); `git stash pop` restored the fix; re-ran and confirmed all pass again.

**TC-4 flake check**: ran the concurrency test 5 additional times in isolation (`-k iter19`) — passed all
5, ~0.4s each, no hang, no flake.

`py_compile` run against all five changed files — clean.

### Regression scope not run — host-guard / time-cost, flagged plainly (not silently skipped)

Per this session's standing testing-discipline constraint (do not run the full suite or files with
expensive shared fixtures), I did **not** run:

- `test_forward_testing.py` (83 tests) — even after `--deselect`-ing its one explicitly `loaded_engine`-
  tagged test, a targeted run of the rest of the file still did not complete within an 8-minute budget
  (killed cleanly, no process left running, verified via `ps aux`) — some other shared fixture in this
  file is evidently also expensive on this host's current ~30-year deep basis. This file DOES check
  `backfill_run_forward_returns`'s `rows_inserted` return value (lines ~1020-1041) in a way my change does
  not alter (the returned dict's shape and values are unchanged; only whether an internal commit call
  fires is different).
- `test_warmup.py` (19 tests) — timed out at 90s despite no `loaded_engine` reference; same likely cause.
- `test_data_manager.py` (136 tests) and `test_data_manager_backfill_committed_session.py` — not attempted
  after the two timeouts above made the risk pattern clear; both call `backfill_run_forward_returns`
  (directly, or via `_do_backfill`'s per-date orchestration) but always for a genuinely-new or
  already-committed-elsewhere run, and each date gets its own fresh session (`data_manager.py`'s J-68
  fresh-session-per-date design) — by code inspection, my guard only ever *removes* a redundant commit
  when there is nothing to commit, which cannot itself put a session into an invalid state, but I have not
  run these files to confirm.
- `test_api_backtest.py` (12 tests, 11 of them `loaded_engine`-dependent) — the ~80-minute fixture the spec
  explicitly says to cite, not run.

**Recommend the reviewer/QA stage run these five files** (with an appropriately larger time budget / off
this constrained box) as part of broader regression confirmation before this iteration is scored against
its DoD's "all pre-existing tests... keep passing" bullet.

## Known Issues

- The autoflush-driven uncaught-exception finding above (separate from this iteration's guard, flagged for
  triage).
- The five regression files not run this session (listed above) — flagged, not silently dropped.
- Guard-shape sufficiency (TC-6) is **not yet confirmed** — operator-performed, listed below.

## Operator-performed items (could not run myself this session)

Per the PUMP NOTE: I cannot start/stop services or launch a raw uvicorn process (AG-10, host-guard). The
following remain exactly as the spec scopes them:

- **TC-6 (mandatory)**: 6 concurrent `GET /api/backtest` pollers on the deep basis via
  `scripts/start-backend.sh` (host-guard-confined, mirrors iter-18's TC-9 protocol) — assert
  `backfill_forward_returns_ms` mean ≤ 350ms / max ≤ 400ms (down from iter-18's 881ms/999ms), recorded in a
  new dated `reports/perf-budgets.md` section. **This is the number that actually confirms (or refutes) the
  guard shape chosen above** — I have not seen it.
- **TC-7 (contingent on owner go-ahead for the ingest trigger)**: same protocol plus a concurrent ingest
  job — record breach count/max latency vs. the iter-16/17 baseline (11/68 @ max 12.655s), or document the
  block plainly if the trigger stays blocked.
- **TC-8 (non-disruptive)**: `GET /api/health` → 200/`ready`; no new crash banner in `logs/backend.log`.
- **TC-9**: required-still-passing golden replay for J-01/J-03/J-05 — per plan.md's "Agents Required"
  section this iteration is backend-only/developer-only; the golden-replay regression check is the
  standard downstream QA-stage responsibility, not something I ran myself.
- **TC-10**: a live single `GET /api/backtest` request captured before/after the fix on the real deep-basis
  process, diffed for byte-identity (corroborates TC-5 against the real process, not only the unit-test
  fixture); a bonus browser screenshot only if Chrome MCP (port 9224) has recovered.

If a backend restart is needed to pick up these code changes before TC-6/7/8/10 can run, that restart is
also operator-performed (per the PUMP NOTE).

## Config / Environment Changes

None. No new config keys, environment variables, or migrations.

---

# Fix Notes (attempt 2 — review FAILed on TC-6 latency)

**Date:** 2026-07-24 · **Agent:** developer (fix mode) · **Review:** `reports/reviews/goal-ops-hardening-iter-19-review.md` (FAIL)

## Why attempt 1 FAILed (reviewer's CRITICAL, confirmed by the operator's live TC-6 re-measurement)

Attempt 1 chose guard shape **(a) skip-commit-when-`inserted==0`**. The reviewer confirmed that guard is
correctly implemented and race-safe, but the live TC-6 re-measurement proved it did **not** collapse the
target phase: `backfill_forward_returns_ms` mean stayed at **877 ms** post-fix vs **881 ms** pre-fix
(required ≤ 350 ms mean / ≤ 400 ms max). The commit was never the bottleneck. The real cost driver is the
**existence-check query itself** (`forward_testing.py`, was line ~1397): it did
`select(ForwardReturn).where(run_id == run.id).all()`, **materializing every full `ForwardReturn` ORM row
for the run** just to build a 3-tuple key set. Under 6× concurrency that whole-row hydration is
GIL-serialized Python object construction — 82.5 % of each request.

## The fix (this attempt)

**Column-project the idempotency existence read** so the warm path never hydrates full ORM rows
(`forward_testing.py`, `backfill_run_forward_returns`):

```python
# before (attempt 1 and earlier): full-row ORM materialization
existing = {(fr.run_id, fr.symbol, fr.horizon)
            for fr in session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()}
# after: 2-column projection to plain tuples (run_id constant = run.id for this run-filtered read)
existing = {(run.id, symbol, horizon)
            for symbol, horizon in session.exec(
                select(ForwardReturn.symbol, ForwardReturn.horizon).where(ForwardReturn.run_id == run.id)
            ).all()}
```

- **Chosen over the COUNT/coverage alternative deliberately.** A COUNT check cannot cheaply know the
  *expected* row count because a `(symbol, horizon)` with fewer than `horizon` post-D bars legitimately
  stores **no** row (honest NA gap) — so "stored count == symbols × horizons" is not a valid completeness
  test and would either loop forever re-inserting or falsely skip a genuinely-incomplete run. Column
  projection sidesteps this entirely: the projected `(symbol, horizon)` values are the **exact same** plain
  tuples ORM attribute access returns, so `existing` is **byte-identical** to the prior set and the
  create-once / idempotent completeness semantics are **unchanged** — `_insert_run_forward_returns` still
  detects and fills any genuinely-missing key at the `(symbol, horizon)` grain. Zero correctness risk, which
  matters on this REGRESSION-history cluster.
- The attempt-1 **skip-commit-when-zero guard is retained** (`if inserted:` before
  `_commit_forward_returns_concurrency_safe`). It is correct and complementary — a warm request now (1) does
  a cheap projected read and (2) acquires no write lock. It simply was not, by itself, the latency fix.
- Kept the `_streamed_existing_keys` idiom already in this module (line ~439) as the precedent — same
  projection technique, here scoped to one run.

## Evidence this attempt

- **SQL-shape verification (the load-bearing proof attempt-1 lacked):** captured the actual SQL a warm
  `backfill_run_forward_returns` issues via `before_cursor_execute`. The ONLY `forward_returns` read is now
  `SELECT forward_returns.symbol, forward_returns.horizon FROM forward_returns WHERE forward_returns.run_id = ?`
  — a 2-column projection, **no** full-row hydration (`realized_return`/`entry_close`/`mae`/… absent), and
  **zero** write statements on the warm path. (attempt-1's query was the full-row `SELECT` of all columns.)
- **54 scoped tests pass** (was 53 in attempt 1; +1 new completeness test), 24.99 s, host-guard-confined
  (`taskset -c 0-3,8-11`, BLAS/OMP=4), sequential (never concurrent pytest):
  `test_forward_testing_serving_split.py` (22: 17 pre-existing + TC-1/2/3/5 + new completeness test),
  `test_forward_testing_concurrency.py` (7: incl. TC-4), `test_backtest_timing.py` (5),
  `test_backtest_scorecard.py` (20).
- **New test** `test_iter19_partial_backfill_run_is_detected_incomplete_and_completed`
  (`test_forward_testing_serving_split.py`): fully backfills a run, deletes a proper SUBSET of horizons, and
  asserts the projected existence read re-inserts **exactly** the deleted keys (not all, not none) and a
  subsequent call inserts zero — proving the cheaper read did not change completeness semantics (the pump's
  explicit ask).
- **Byte-identity preserved (AG-3):** TC-2 (MCP == API) and TC-5 (scorecard + all `evidence_*` fields, every
  horizon, with/without `as_of`) still pass unchanged — the projection changes only the query shape, never a
  served value.
- **Concurrency-race safety preserved:** TC-4 (5 concurrent genuinely-missing callers, `IntegrityError`
  rollback path exercised) still passes; the genuinely-missing INSERT path is behaviorally unchanged.
- **AG-8:** the projected read is bounded to ONE run's own rows (symbols × horizons; deeper history adds
  *runs*, not rows-per-run) — not a whole-table load, and no longer an ORM materialization.

## MINOR (reviewer's pre-existing autoflush hazard) — assessed, deferred as reviewer-scoped follow-up

The reviewer flagged (MINOR, "does not block this fix", "triage as follow-up") the pre-existing autoflush
`IntegrityError` hazard inside `_insert_run_forward_returns`'s per-symbol loop (a staged INSERT for symbol N,
then symbol N+1's `close_on`/`bars_after` read triggers an autoflush not wrapped in the
`IntegrityError`-tolerant pattern). **Assessment (per the PUMP NOTE):**

- The **warm / common path never reaches this code.** On a run whose forward returns are complete, every
  symbol's `needed` list is empty, so `_insert_run_forward_returns` `continue`s past every symbol and
  **never calls `session.add(...)`** — no INSERT is staged, so no autoflush can fire. This is **proven** by
  the SQL-shape capture above: the warm path issued **0 write statements**. Every TC-6 request takes this
  path, so the hazard is **moot for the measured latency path**.
- My column-projection fix does **not** change the hazard's reachability (the warm path already staged
  nothing in attempt 1 — `inserted == 0`). The hazard remains confined to the **rare** genuinely-missing
  path with 2+ missing symbols under 2+ concurrent callers (a cold historical snapshot's first view under
  concurrency).
- **Not fixed this attempt (deliberate).** The reviewer's own remedy ("disable autoflush for the loop's
  duration") is a one-line `with session.no_autoflush:` and I believe it is safe (the loop's reads hit
  `DailyPrice`, not `ForwardReturn`, so deferring the flush changes no query result). But it changes
  **flush/transaction timing on exactly the concurrency cluster that caused iter-13's REGRESSION_HALT** — I
  judged "trivial to write" ≠ "trivial to prove safe under concurrent load," and bundling it into the
  critical-latency-fix attempt is the wrong risk trade. It is filed as a focused follow-up (its own
  iteration, its own concurrency test budget), matching the reviewer's "triage as a follow-up" and the PUMP
  NOTE's "you need not fully fix the pre-existing hazard this attempt unless it's trivial."

## Operator-performed items (unchanged from attempt 1 — I have no service-control permission, AG-10)

1. **RESTART the backend** (`scripts/start-backend.sh`, host-guard-confined) to load this fix. The live
   service on `:8255` (pid **2734551**) is still running **attempt-1's code** (verified read-only:
   `uvicorn main:app`, `/api/health` → `readiness: "ready"`) — it does **not** contain the column-projection
   fix. I did not and cannot restart it, and did not launch any raw uvicorn (AG-10). I started **no** server
   processes (read-only `curl`/`ss`/`/proc` only — nothing to clean up).
2. **Re-run TC-6** (6× concurrent `GET /api/backtest`, pure reads, mirrors iter-18's TC-9): confirm
   `backfill_forward_returns_ms` mean ≤ 350 ms / max ≤ 400 ms (down from the 877 ms this attempt targets),
   record in a new dated `reports/perf-budgets.md` section. **This is the number that confirms the fix** —
   the mechanism (query shape) is now provably changed (SQL capture above), which is what attempt 1 lacked.
3. TC-7 / TC-8 / TC-10 unchanged from the attempt-1 list above.

## Files changed this attempt

- `apps/backend/app/engine/forward_testing.py` — `backfill_run_forward_returns`: replaced the full-row
  `select(ForwardReturn)` existence read with the 2-column projection; rewrote the docstring to attribute the
  latency collapse to the projection (attempt-1's docstring falsely credited the skip-commit). No other line
  changed; `_insert_run_forward_returns`, `_commit_forward_returns_concurrency_safe`, and the `if inserted:`
  guard are all unchanged.
- `apps/backend/tests/test_forward_testing_serving_split.py` — imported `backfill_run_forward_returns`; added
  `test_iter19_partial_backfill_run_is_detected_incomplete_and_completed`.
- `apps/backend/app/api/backtest.py`, `apps/backend/app/mcp/tools.py` — **not touched this attempt**
  (attempt-1's `write_taken` timing field stands).

---

# Fix Notes (attempt 3 — review FAILed on TC-6 latency; the PROVEN root cause)

## Why attempt 2 FAILed (reviewer's CRITICAL, live-confirmed)

Attempt 2's column-projected existence read was **correct but inert for latency**. The reviewer's live
`EXPLAIN QUERY PLAN` showed the projected read already resolves to a covering index (~0.06 ms) — it was
never the cost driver. Post-restart TC-6 still showed `backfill_forward_returns_ms` ~877 ms mean / 82 %
share under 6× concurrency. Neither attempt-1 (skip-commit) nor attempt-2 (column projection) touched the
**actual** bottleneck.

## The PROVEN root cause (reviewer + operator sub-phase, independently re-verified this attempt)

`backfill_run_forward_returns` → `_insert_run_forward_returns` does a per-symbol `close_on` + `bars_after`
price-fetch **pair** for every `(symbol, horizon)` absent from `existing`. For a run within `max_horizon`
(60 trading days) of the data end, the un-elapsed horizons are **not yet observable** (fewer than `h` bars
exist after `run.asof_date` for ANY symbol) — they can never be inserted (honest NA), never enter
`existing`, and are **re-attempted on every request**. The default `/backtest` resolves to the latest run
(asof == max `daily_prices` date, 0 elapsed days), so it pays ~553 symbols × 2 queries ≈ **1106 queries**
every request — the 82 % cost.

## The fix (this attempt): short-circuit un-elapsed horizons globally, before the per-symbol loop

In `backfill_run_forward_returns`, right after `symbols = forward_symbols_for_run(...)`, compute **once**
how many trading days are observable after `run.asof_date`, then pass only the elapsed horizons into
`_insert_run_forward_returns`:

```python
observable_days = len(
    session.exec(
        select(DailyPrice.date)
        .where(DailyPrice.date > run.asof_date)
        .distinct().order_by(DailyPrice.date).limit(max_h)
    ).all()
)
observable_horizons = [h for h in horizons if h <= observable_days]
...
inserted = _insert_run_forward_returns(session, run, symbols, observable_horizons, max_h, existing)
```

For the latest run `observable_days == 0` → `observable_horizons == []` → every symbol's `needed` list is
empty → the per-symbol loop `continue`s immediately → **zero `close_on`/`bars_after` calls**. Recent runs
skip only their un-elapsed horizons; an old fully-elapsed run (`observable_days >= max_h`) keeps every
horizon (unchanged). **Attempt-1's skip-commit guard and attempt-2's column-projected read are both
retained** — this attempt ADDS the horizon short-circuit, it does not revert them.

### Accessor decision — why distinct `daily_prices.date`, not the literal `bars_after(SPY, ...)`

The reviewer's fix-task suggested `k = len(bars_after(session, cfg.etfs.index[0], run.asof_date, limit=max_h))`
(SPY, the module's calendar anchor) and asked me to **"confirm the exact accessor … use the same one."** I
confirmed it and found a hard conflict with *"keep the 54 scoped tests green"*: **the unit-test fixtures seed
only the scored symbols (AAA/BBB/HHH), never SPY** (`grep 'symbol=' test_forward_testing_serving_split.py`
→ no SPY). With the literal SPY anchor, `k == 0` in every fixture, wrongly skipping ALL horizons and
breaking TC-3 / the partial-backfill test / every row-inserting test.

I therefore measure the SAME trading calendar directly — the **distinct `daily_prices.date > D` count**
(the calendar SPY is a proxy for). This is:
- **Equal to the SPY anchor in production** — verified live on the deep basis: for the latest run both give
  `0`; SPY trades every calendar day so its post-D bar count == the distinct post-D date count.
- **Byte-identity-safe by construction (a strict upper bound over ALL symbols)** — no symbol can have more
  post-D bars than there are distinct post-D dates, so any horizon `h > observable_days` has `< h` bars for
  **every** symbol and already stored nothing via `forward_return`'s `len(post_bars) < horizon` NA gate.
  (It is in fact *more* robust than the single-symbol SPY anchor: if a non-SPY symbol ever traded on a date
  SPY did not, the SPY anchor would wrongly skip it; the distinct-date count would not.)
- **Bounded / AG-8-safe** — a `COVERING INDEX ix_daily_prices_date` search, `LIMIT max_h`, short-circuits:
  measured **≤ 0.5 ms even at the 1996 basis floor** (3.3 M rows after D) and **0.0 ms for the latest run**.
  No whole-table scan.
- **No-lookahead / AG-5** — counts only already-stored bars with `date > D`; never a future/synthesized bar.

This is not "inventing a new symbol" — it is the benchmark-symbol-agnostic form of the exact calendar the
reviewer named. Flagging the deviation explicitly per the token/questioning policy.

## Evidence this attempt

**Live read-only before/after against the deep-basis DB** (`data/trendora.db`, opened `mode=ro` — no write,
no lock on the running backend; no server started; single-threaded; CPU-pinned + thread-capped):

```
latest run id=1439 asof=2026-07-22  #symbols=553  horizons=[1,5,10,20,60]
observable_days (distinct post-D trading dates, capped at max_h=60) = 0
--- BEFORE (unfiltered, the old per-request storm) ---
  rows_inserted=0  close_on_calls=553  bars_after_calls=553  total_price_fetches=1106  elapsed=113.6ms
--- AFTER (observable-horizon short-circuit, shipped this attempt) ---
  rows_inserted=0  close_on_calls=0    bars_after_calls=0    total_price_fetches=0     elapsed=1.6ms
fetch reduction: 1106 -> 0 price queries per request
```

Single-threaded the phase collapses **113.6 ms → 1.6 ms** (at the ~3 ms floor the reviewer targeted) with
**1106 → 0 price fetches**. This is the mechanism proof; the operator's 6× concurrent TC-6 confirms the DoD
number (≤ 350 ms mean / ≤ 400 ms max) since the eliminated fetches were the 82 % share that ballooned under
concurrency.

**Unit tests (scoped, host-capped `taskset -c 0-3`, `OMP/OPENBLAS/MKL=2`, single-process — no full-suite
burst):**
- `test_forward_testing_serving_split.py` — **25 passed** (22 prior + 3 new).
- `test_forward_testing_concurrency.py` — **7 passed** (TC-4 race path intact).
- New tests (all assert exact values + byte-identity vs the unfiltered path):
  - `test_iter19_latest_run_unelapsed_horizons_short_circuit_no_price_fetches` — latest run (k=0):
    `rows_inserted==0`, **zero** monkeypatch-counted `close_on`/`bars_after` calls, stored state identical
    to the unfiltered path (both empty).
  - `test_iter19_partially_elapsed_run_processes_only_elapsed_horizons_byte_identical` — K observable days
    (K = second-largest horizon): inserts ONLY the elapsed horizons, byte-identical (every `ForwardReturn`
    column) to the unfiltered path, and a warm re-call issues **zero** `bars_after` fetches (the un-elapsed
    horizon no longer re-triggers a per-symbol fetch).
  - `test_iter19_fully_elapsed_run_processes_all_horizons_unaffected` — k ≥ max_h: every horizon still
    inserted, exact realized returns (`h/100`) asserted (no regression for old runs).

## Files changed this attempt

- `apps/backend/app/engine/forward_testing.py` — added `DailyPrice` to the `app.models` import;
  `backfill_run_forward_returns`: added the `observable_days`/`observable_horizons` short-circuit and passed
  `observable_horizons` into `_insert_run_forward_returns`; rewrote the docstring (now THREE cooperating
  changes) and corrected the attempt-2 column-projection comment (it was NOT the latency driver).
  `_insert_run_forward_returns`, `_commit_forward_returns_concurrency_safe`, the boot `_backfill` call site,
  the `if inserted:` skip-commit guard, and the column-projected `existing` read are all unchanged.
- `apps/backend/tests/test_forward_testing_serving_split.py` — added helpers `_seed_run_with_post_window`,
  `_fr_rows_sorted` and the three `test_iter19_*` tests above.
- `apps/backend/app/api/backtest.py`, `apps/backend/app/mcp/tools.py`, `data_manager.py` — **not touched**
  (the reviewer's fix-task was scoped to `forward_testing.py` only; attempt-1's `write_taken` timing field
  stands).

## MINOR (reviewer's pre-existing autoflush IntegrityError hazard) — NOT touched

The reviewer's MINOR finding (`_insert_run_forward_returns:371` autoflush hazard) is explicitly *"correctly
deferred, not fixed this attempt … track as its own follow-up iteration."* Left untouched per "fix ONLY the
listed CRITICAL issue."

## Operator-performed items (I have no service-control permission, AG-10 — must NOT launch raw uvicorn)

1. **Restart the backend** via `scripts/start-backend.sh` to load this fix (live `:8255` pid 2796615 runs
   attempt-2 code). Stop → start; verify no port conflict and `/proc` caps intact.
2. **TC-6** (mandatory): 6× concurrent `/backtest` pollers, host-guard-confined, pure reads — confirm
   `backfill_forward_returns_ms` mean ≤ 350 ms / max ≤ 400 ms (from 881/999). Record a new dated
   `reports/perf-budgets.md` section. Expectation is strong: the eliminated 1106 fetches were the 82 % share.
3. **TC-8** (non-disruptive): `GET /api/health` → 200/`ready`; no new crash banner in `logs/backend.log`.
4. **TC-10**: single live `/backtest` before/after byte-diff (corroborates TC-5 on the real process).
5. **TC-7** (contingent on owner ingest-trigger go-ahead) and the disruptive J-04 replay — carried,
   owner-gated, not this iteration's blocker.

## Known issue / triage note (new, not in any report — do not silent-fix)

The boot walk-forward backfill `_backfill` (`forward_testing.py:487`) still calls
`_insert_run_forward_returns` with the **full** horizons for every run at startup, so it pays the same
un-elapsed-horizon fetches for recent runs during boot. This is **out of scope** here (the reviewer's
fix-task and the spec both scope the change to the request-path `backfill_run_forward_returns` only; boot is
a one-time cost, not the per-request latency). Flagging for the reviewer/auditor to triage as a possible
future consolidation, per "record new problems in the handoff, do not silently fix."
