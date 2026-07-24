# goal-ops-hardening-iter-18 Dev Handoff

**Phase:** goal-ops-hardening-iter-18
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete (backend code + tests); TC-9 and TC-10 are OPERATOR-performed, see below

## What Was Built

This is a LEAN, diagnosis-first iteration: instrumentation + two cheap wins, deliberately NOT a latency
mitigation (per the spec's own explicit sequencing — the fix-or-fork decision is for the iteration that
follows this one's fresh measurement).

1. **Per-request, phase-broken-down timing instrumentation** for `GET /api/backtest`
   (`apps/backend/app/api/backtest.py`) and the MCP `query_backtest` tool
   (`apps/backend/app/mcp/tools.py`). One INFO-level, key=value structured log line per request carrying:
   an ISO-8601 wall-clock timestamp (`ts=`), `is_latest`, `total_ms`, and separate elapsed-ms values for
   run resolution (`resolved_run_ms`), the `backfill_run_forward_returns` step
   (`backfill_forward_returns_ms`), `compute_run_scorecard` (`scorecard_ms`), and
   `resolved_forward_aggregate_evidence` (`evidence_ms`) — plus `ensure_loop_ms`, present ONLY on the
   historical/non-`is_latest` ensure-loop branch (the `forward_aggregates_ingest_cached` calls + the
   re-resolve), mirroring exactly when that branch runs. Two new loggers follow the existing
   `logging.getLogger("trendora.<component>")` convention: `trendora.backtest` and `trendora.mcp_backtest`.
   **Load-bearing detail found and fixed during this iteration** (not itself in the spec's bullet list, but
   necessary for the instrumentation to do anything in production): this process's ROOT logger carries NO
   handler and defaults to level WARNING (confirmed by direct interpreter inspection —
   `logging.getLogger().handlers == []`, `logging.getLogger().getEffectiveLevel() == 30`). An
   otherwise-unconfigured `trendora.*` logger's `.info(...)` call is therefore **silently dropped** —
   Python's own `logging.lastResort` fallback (the thing that lets the codebase's EXISTING
   `.warning()`/`.exception()` calls reach `logs/backend.log` today with zero configuration anywhere) only
   emits WARNING-and-above, so a bare `logger.info(...)` would have produced nothing at all in the real
   log file, defeating this iteration's entire purpose while still passing any test that used `caplog`
   (which sets its own level, masking the gap). Fixed by explicitly `logger.setLevel(logging.INFO)` +
   attaching a guarded, directly-owned `logging.StreamHandler()` to each of the two new loggers, entirely
   inside `api/backtest.py` / `mcp/tools.py` — `main.py`'s boot sequence and all other global logging
   config are untouched (binding "Do not redo"). `propagate` stays at its default `True` so `caplog`-based
   tests observe the same records production emits via this handler.
2. **Cheap win — deferred `payload_json` load in the widened cross-`asof_key` fallback**
   (`resolved_forward_aggregate_evidence`, `apps/backend/app/engine/forward_testing.py`). The
   candidate-selection scan across older `(asof_key, dataset_version)` identities now selects only the
   identifying columns (`asof_key`, `horizon`, `dataset_version`, `created_at`) — never `payload_json`.
   Once the winning pair is chosen, exactly one targeted follow-up query selects `payload_json` (+ the
   same identifying columns) filtered to that winning pair alone, before `_serve(...)` runs. Same query
   intent, same winner, byte-identical served evidence — fewer bytes materialized for every OLDER
   candidate that gets discarded along the way (today ~819 KB across 25 rows, growing ~164 KB per
   distinct as-of ever viewed, per the iter-17 audit). Verified race-safe: both queries run inside the
   same request session's already-open read transaction (the function issues no `commit()`), and this
   app's WAL journal mode fixes a reader's snapshot for the life of that transaction regardless of any
   concurrent writer elsewhere — confirmed by reading `app/db.py`'s pragma/session setup, not assumed.
3. **New endpoint-level test for the iter-17 cross-`asof_key` fallback** — until this iteration, every
   test exercising the widened fallback (an OLDER `evidence_asof` served for a brand-new latest date with
   zero forward-aggregate rows of its own) called `resolved_forward_aggregate_evidence` directly; nothing
   proved it end-to-end through the two actual request-serving entry points. Added
   `test_backtest_route_and_mcp_tool_serve_older_evidence_asof_across_boundary` to
   `test_forward_testing_serving_split.py`.

## Files Changed

- `apps/backend/app/api/backtest.py` — added the `trendora.backtest` logger + `_log_backtest_timing`
  helper; wrapped each phase of `backtest()` in `time.perf_counter()` spans; one timing log call before
  return. Returned dict is byte-identical (nothing added/removed/renamed).
- `apps/backend/app/mcp/tools.py` — added `trendora.mcp_backtest` logger + `_log_query_backtest_timing`
  helper (field-for-field mirror of the API side); same timing wrap around `query_backtest()`. Returned
  dict is byte-identical.
- `apps/backend/app/engine/forward_testing.py` — `resolved_forward_aggregate_evidence`'s widened-fallback
  `older_rows` query no longer selects `payload_json`; added `_complete_version_identities` (a
  payload-free sibling of the existing `_complete_versions`, used only by this scan); added the one
  targeted `winner_rows` follow-up query. `same_key_rows` (the SAME-`asof_key` completeness check) and
  everything else in the function are untouched.
- `apps/backend/tests/test_backtest_timing.py` (**new file**) — TC-1/TC-2/TC-3/TC-4 for the
  instrumentation itself: one timing line per request with an ISO-8601 timestamp + `total_ms` (API route,
  caplog-only, no live server); the 4 named phases sum within 5ms-or-5% of the logged total when
  `backfill_run_forward_returns` performs a real INSERT; the MCP tool emits the same field names; plus two
  additional tests locking in `ensure_loop_ms`'s presence-only-on-the-historical-branch behavior (API and
  MCP) — an explicit IN-SCOPE requirement not individually TC-numbered by the spec.
- `apps/backend/tests/test_forward_testing_serving_split.py` — added
  `test_widened_fallback_defers_payload_json_to_a_single_winner_only_query` (TC-5/TC-6: SQL-inspected via
  the same `before_cursor_execute` technique the file's existing TC-18/iter-17-TC-5 tests use, plus a
  byte-identical content assertion against the pre-iter-18 shape) and
  `test_backtest_route_and_mcp_tool_serve_older_evidence_asof_across_boundary` (TC-7); extended
  `test_backtest_route_is_latest_not_yet_computed_is_honest_200` in place with a `caplog` assertion that a
  timing line is still emitted on the honest empty-state path (TC-8).

## Tests Run

Command (host-guard-confined per this session's standing constraint — scoped to specific files, never the
full suite, never concurrent pytest):

```
cd /home/dennis-chan/Git/trendora
apps/backend/.venv/bin/python -m pytest apps/backend/tests/test_backtest_timing.py \
  apps/backend/tests/test_forward_testing_serving_split.py \
  apps/backend/tests/test_forward_testing_concurrency.py -q
```

Result: **28 passed** (5 new instrumentation tests + 17 in `test_forward_testing_serving_split.py` [15
pre-existing + 2 new] + 6 pre-existing in `test_forward_testing_concurrency.py`), 0 failed.

TDD verification performed, not just claimed: `git stash push -- apps/backend/app/engine/forward_testing.py`
to revert ONLY that file to its pre-iteration state, re-ran
`test_widened_fallback_defers_payload_json_to_a_single_winner_only_query` alone — it FAILED exactly as
expected (`AssertionError: the widened candidate-selection scan must not select payload_json: [...]`,
showing the old query's SQL with `payload_json` still in the SELECT list). `git stash pop` restored the
fix; diffed before/after the stash round-trip to confirm byte-identical restoration; re-ran the full
28-test set again to confirm green.

`test_forward_testing.py` (the third file the spec's DoD names as "must keep passing"): launched in the
background (`pytest apps/backend/tests/test_forward_testing.py --deselect
...::test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon -q --durations=15`, the one
explicitly-flagged 83rd test being the ~80-minute `loaded_engine`-dependent one this session's binding
constraint says to cite, not run). At handoff time this run was **still in progress** — confirmed via `ps`
to be making genuine CPU progress (not hung/deadlocked; steadily increasing CPU time, stable memory), and
the first 47 of 82 selected tests had already completed with no failure markers in the streamed output.
Root-caused the slow point via `--collect-only`: position 48 in file order is the deselected test itself
(skipped, no cost); position 49 is `test_backfill_inserts_forward_returns_without_mutating_snapshot`, the
FIRST test requesting the module-scoped `backfilled_engine` fixture — a real, one-time backfill
construction cost paid once per module, wholly pre-existing and independent of anything this iteration
touched. Confirmed by direct grep this iteration's ONLY functional change
(`resolved_forward_aggregate_evidence`) is referenced **zero times** anywhere in `test_forward_testing.py`
— that file exercises `compute_forward_aggregates` and `forward_aggregates_ingest_cached` instead, and I
did not modify either. There is no plausible mechanism for this iteration's diff to regress that file; its
long tail is a pre-existing fixture-construction cost, not new. Recommend the reviewer either let the
background run finish (it was not killed) or accept this zero-overlap reasoning as sufficient.

`test_api_backtest.py` — NOT run, per binding "Do not redo": its `loaded_engine`-dependent
`test_backtest_evidence_by_horizon_shape_and_keys` is the cited ~80-minute fixture. Confirmed by reading
the diff that this is safe to skip: the `/backtest` response dict's key set is completely unchanged by
this iteration (unlike iter-17, which added the new `evidence_asof` key and needed a matching update
there) — this iteration only adds a side-effect log call and reshapes two internal SQL queries, so no
exact-key-set assertion anywhere could be affected.

`apps/backend/.venv/bin/python -m py_compile` run against all five changed/new files — clean.

## Known Issues

- **TC-9 and TC-10 are OPERATOR-performed and NOT run by me** — I cannot start, stop, or restart backend
  services myself (the permission classifier blocks agent service control per this session's standing
  constraint) and must not launch a raw `uvicorn` process to work around that (would strip the host-guard
  caps, AG-10). Per my dispatch instructions, I'm flagging this explicitly: the operator needs to (1) run
  the deep-basis concurrent-poll re-measurement protocol (cooled host, `hwmon` sampler, thermal watchdog,
  `taskset -c 0-3,8-11`, BLAS/OMP=4) against a backend launched via `scripts/start-backend.sh` with this
  iteration's instrumentation active, and record the breach count / max latency / per-phase breakdown in a
  new dated `reports/perf-budgets.md` section directly comparable to the iter-16/17 baseline (11/68
  breaches, max 12.655s) — TC-9; then (2), same session, immediately after, submit a bounded backfill,
  `kill -9` it mid-run after a checkpoint interval, restart, and confirm the `/data` Run History panel
  shows the interrupted run's real checkpointed progress plus a healthy `GET /api/health` — TC-10.
- **Service-startup pre-handoff verification was not performed by me** — same reason (no service-control
  permission this session). I did not run `scripts/dev.sh`/`scripts/start-backend.sh` myself; recommend the
  operator fold a clean start/stop/restart smoke check into the TC-9/TC-10 pass rather than treating it as
  a separate step.
- **`test_forward_testing.py`'s full targeted run had not concluded at handoff time** (see Tests Run above
  for the full reasoning on why this is not a regression risk) — recommend the reviewer confirm its final
  tally before/alongside their own pass, or independently accept the zero-call-site-overlap argument.
- **No live external integration to verify** — this iteration adds no adapters, scrapers, or external API
  calls (AG-9 unaffected); the pre-handoff "external integrations work live" check does not apply.
- **No new dependency** — nothing added to `requirements`/`pyproject`, so there is no new native-binary
  post-install step to verify.
- The pre-existing `test_db.py::test_create_all_produces_expected_tables` failure is carried, not new (per
  the spec's own NOTES section) — I did not touch anything schema-related this iteration and did not
  re-verify this specific pre-existing failure myself; noting it here only so its presence (if seen by a
  later stage) is not mistaken for something this iteration introduced.
- The message format for the new timing log lines (`backtest_timing ts=... is_latest=... total_ms=...
  resolved_run_ms=... backfill_forward_returns_ms=... scorecard_ms=... evidence_ms=... [ensure_loop_ms=...]`,
  space-separated `key=value` pairs, one line per request) is a judgment call — the spec asks for
  "parseable form" without prescribing an exact schema. Chose plain key=value over JSON to match this
  codebase's existing lazy `%`-style logging convention and to keep TC-9's own `grep`/eyeball workflow
  trivial; flagging the exact shape here in case the operator's TC-9 analysis script expects something
  different.

## Notes for the operator (per the pump note)

`logs/backend.log` will now receive one `backtest_timing ...` or `query_backtest_timing ...` line per
`/backtest` request/tool-call once a backend built from this diff is running — this is what TC-9's
phase-breakdown analysis reads. No service action was taken by me; the backend needs to be (re)launched by
the operator via `scripts/start-backend.sh` for TC-9/TC-10, same as the dispatch note anticipated.
