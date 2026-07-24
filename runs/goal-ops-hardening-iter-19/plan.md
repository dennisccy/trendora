# goal-ops-hardening-iter-19 Execution Plan

Target journeys: J-06, J-07, J-08 (shared blocker). Required-still-passing: J-01, J-03, J-04, J-05.
Depth: full (trigger 1 — cross-cutting change touching 3 files/modules whose interaction is untested
by any single journey). Frontend Present: no — backend-only, byte-identical served payload.

## Alignment check

Directly serves `docs/goal.md`'s "compute-at-ingest, serve-from-storage" principle: the ingest finalize
path (`data_manager.py:2918`) already backfills a run's forward returns at creation, so the per-request
call in `GET /api/backtest` / MCP `query_backtest` is pure redundant re-derivation that only costs real
latency once concurrency forces SQLite's writer lock to serialize (iter-18 TC-9: 881 ms mean / 999 ms
max, 82.2% of each slow request). Rule 3 of the target-selection rubric applies (unblocker: one root
cause, one fix, three journey labels). No drift from the goal or CORE RULES detected — nothing to flag
as out-of-scope beyond what the spec itself already excludes (mirrored below so it isn't silently
dropped by the developer).

## What to Build

- A guard **inside** `backfill_run_forward_returns` (`apps/backend/app/engine/forward_testing.py:1365`)
  so a request for a run whose forward returns are already fully backfilled performs zero SQLite
  write-lock-acquiring work (no `INSERT`, no non-trivial `commit()`). Default shape (per the spec's own
  steer, confirmed by reading the function): skip calling `_commit_forward_returns_concurrency_safe`
  when `_insert_run_forward_returns` returns `inserted == 0` — no new query needed, the idempotency
  check already computes this count. The genuinely-missing case keeps inserting synchronously and
  committing exactly as today (idempotent, race-tolerant via the existing IntegrityError-rollback path,
  unchanged).
- **Developer decision point, explicit in the spec:** if the TC-6 live re-measurement shows
  skip-commit-when-zero does not collapse the phase, swap to a cheap pre-check ahead of the
  read+insert+commit block instead. Either way, state which shape was used and why (grounded in the
  live TC-6 number, not a code-level argument alone) in the dev handoff.
- Extend the two existing `backtest_timing` / `query_backtest_timing` log lines (landed iter-18) with
  one additional field recording whether the create-once write was skipped or taken this request —
  operational log only, supports TC-6/TC-7 evidence-gathering, not a served value.
- Add/extend unit tests: TC-1, TC-2, TC-3, TC-5 in `test_forward_testing_serving_split.py`; TC-4
  (concurrency) in `test_forward_testing_concurrency.py`, co-located with but distinct from that file's
  existing forward-*aggregate* concurrency tests (this is forward-*returns*, a different
  table/mechanism).
- **No call-site edits.** `apps/backend/app/api/backtest.py:140`, `apps/backend/app/mcp/tools.py:263`,
  and `data_manager.py:2918` all keep calling `backfill_run_forward_returns(session, run, cfg)`
  unconditionally, exactly as today (confirmed by direct read of both request-path call sites) — the
  guard lives in the one shared function only (single-producer discipline).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-19-dev.md` stating the chosen guard shape + why,
  test results, and which TCs remain operator-performed.

**Explicitly NOT this iteration's work (carried from the spec's OUT OF SCOPE, do not expand into these):**
- `compute_forward_aggregates` / the compute-vs-serve split / cutover-pruning logic — different
  function/table entirely, untouched.
- The resolver's cross-`asof_key` fallback / `evidence_asof`/`evidence_status`/`evidence_generated_at`
  (iter-16/17) — untouched.
- Deferring the genuinely-missing backfill to a background/async job — explicitly rejected (would break
  AG-3 byte-identity by serving a transient NA on first view).
- A new persisted schema/column (e.g. a `forward_returns_backfilled` flag) — not the default plan; only
  if TC-6 proves the guard insufficient, and if so flag it as its own migration, don't add it silently.
- The owed J-04 disruptive kill/restart replay — owner-gated (ingest-trigger classifier), not this
  iteration's blocker; TC-8's non-disruptive check substitutes.
- `main.py` boot, `health.py`, `readiness.py`, `warmup.py`, `scripts/*` — untouched.
- Full pytest suite — targeted, host-guard-confined runs only; cite (don't run) the ~80-minute
  `loaded_engine`-dependent `test_api_backtest.py` fixture.
- A generic all-endpoint timing middleware/APM rollout — scoped strictly to extending the two existing
  log lines.

## Agents Required

- developer: yes -- implement the write-skip guard, extend the two timing log lines, add TC-1..TC-5 +
  TC-4(concurrency), write the dev handoff. This is backend-only work (no UI-facing agent needed).
  - backend-data: yes -- all of the above.
  - frontend-ux: no -- zero UI/served-payload change; TC-5 is a hard byte-identity constraint on the
    same response shape, so no component, page, or API-contract work of any kind this iteration.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` -- add the zero-write guard inside
  `backfill_run_forward_returns` (~line 1365); `_commit_forward_returns_concurrency_safe` and the
  genuinely-missing INSERT path stay behaviorally unchanged.
- `apps/backend/app/api/backtest.py` -- extend the existing `_log_backtest_timing`/`backtest_timing`
  line with the skip/taken field only; call site (~line 140) itself untouched.
- `apps/backend/app/mcp/tools.py` -- mirror the same log-line extension in
  `_log_query_backtest_timing`/`query_backtest_timing`; call site (~line 263) itself untouched.
- `apps/backend/tests/test_forward_testing_serving_split.py` -- add TC-1 (zero writes via
  `before_cursor_execute` SQL-inspection on `GET /api/backtest`), TC-2 (same for MCP `query_backtest`,
  plus byte-identical fields vs. the API for the same inputs), TC-3 (genuinely-missing run still inserts
  once, second call zero-writes), TC-5 (`compute_run_scorecard` + all `evidence_*` fields byte-identical
  before/after, every horizon, with/without `as_of`).
- `apps/backend/tests/test_forward_testing_concurrency.py` -- add TC-4: 5 concurrent `GET /api/backtest`
  calls for the same genuinely-missing as-of; no unhandled exception, no duplicate
  `(run_id, symbol, horizon)` row, and the `IntegrityError`-tolerant rollback path demonstrably exercised
  by at least one of the 5 (assertion-proven, not merely reachable in theory).
- `docs/handoffs/goal-ops-hardening-iter-19-dev.md` (new) -- guard-shape decision + why, test results,
  operator hand-off list (TC-6/TC-7/TC-8/TC-9/TC-10).
- `reports/perf-budgets.md` -- OPERATOR appends the TC-6 (mandatory) and TC-7 (contingent) dated
  sections after the live re-measurement; not a developer deliverable, do not fabricate numbers here.
- `docs/blueprint.md` -- spec states the iter-19 comment-block paragraph + Notes-cell append were
  already written this iteration; verify it's present, do not duplicate or add a nav-skeleton change (no
  `blueprint.reapproval-requested` this iteration).

## Key Test Scenarios

- TC-1: fully-backfilled run's as-of via `GET /api/backtest` issues zero `INSERT`/`UPDATE`/`DELETE`
  (SQL-inspected), HTTP 200.
- TC-2: same fixture via MCP `query_backtest` also issues zero writes; scorecard + `evidence_*` fields
  match the API route's for the same inputs.
- TC-3: never-backfilled run still gets its `ForwardReturn` rows INSERTed synchronously on first view
  (idempotent, count = symbols × horizons minus NA gaps); a second call for the same as-of is zero-write.
- TC-4 (mandatory concurrency test, new fixture): 5 concurrent `GET /api/backtest` calls for the same
  genuinely-missing as-of all complete with no unhandled exception, no duplicate key, and the
  `IntegrityError` rollback path is provably exercised.
- TC-5: `compute_run_scorecard` + `evidence_status`/`evidence_generated_at`/`evidence_asof`/
  `evidence_by_horizon` byte-for-byte identical before/after, every horizon, with and without `as_of`.
- TC-6 (OPERATOR, mandatory, mirrors iter-18's TC-9 protocol exactly): 6 concurrent `GET /api/backtest`
  pollers on the deep basis, pure reads, host-guard-confined via `scripts/start-backend.sh` — assert
  `backfill_forward_returns_ms` mean ≤ 350 ms and max ≤ 400 ms (down from iter-18's 881 ms / 999 ms),
  recorded in a new dated `reports/perf-budgets.md` section.
- TC-7 (OPERATOR, contingent on owner ingest-trigger go-ahead): same protocol plus a concurrent ingest
  job; record breach count/max latency comparable to the iter-16/17 baseline (11/68 @ max 12.655s) if
  authorized this session, else document the block plainly (not silently dropped).
- TC-8 (OPERATOR, non-disruptive): `GET /api/health` → HTTP 200/`ready`; no new crash banner in
  `logs/backend.log`.
- TC-9 (required-still-passing regression): J-01/J-03/J-05 deterministic golden replay all PASS, no new
  failure attributable to this diff.
- TC-10 (OPERATOR): a live single `GET /api/backtest` request captured before/after the fix, diffed for
  byte-identity — corroborates TC-5 against the real deep-basis process, not only the unit-test fixture.

## Notes for downstream agents

- J-06/J-07/J-08 are evaluated by the goal-evaluator against the evidence this iteration produces; this
  plan (like the spec) does not itself declare any journey passing.
- The pre-existing `test_db.py::test_create_all_produces_expected_tables` failure is carried, not new —
  do not treat it as a regression caused by this diff.
- Chrome MCP (port 9224) is confirmed unreachable at spec-writing time; no browser verification is
  required for J-06/J-07/J-08 (Frontend Present: no); TC-10's browser screenshot is bonus/non-blocking
  only if the wedge has cleared by execution time.
