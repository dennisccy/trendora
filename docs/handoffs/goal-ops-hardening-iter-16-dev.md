# goal-ops-hardening-iter-16 Dev Handoff

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Agent:** developer
**Status:** complete (code + targeted tests + the one operator-supervised TC-16 live pass, now transcribed — see "Known Issues" #2 and the "TC-16 Results" section appended below)

## What Was Built

- **The compute-vs-serve split (J-08).** `forward_aggregates_cached` (`apps/backend/app/engine/forward_testing.py`)
  split into two functions:
  - **`forward_aggregates_ingest_cached`** — the INGEST-ONLY compute-and-persist half. The SOLE remaining
    caller of `compute_forward_aggregates`. Keeps iter-15's single-flight lock/in-flight-event guard
    completely UNCHANGED (still needed for two concurrent ingest jobs racing the same key). Called by:
    (a) `data_manager._refresh_ingest_aggregates`'s existing per-horizon warm loop (line 3230, loop/
    trigger/`MemoryError` handling unchanged — only the function name at the call site changed), and
    (b) `GET /api/backtest` / MCP `query_backtest`'s pre-existing, UNCHANGED historical (`is_latest ==
    False`) create-once-and-cache carve-out (TC-13) — this second caller is REQUIRED for that carve-out
    to keep working post-split, since the new read-only function (below) structurally cannot compute.
  - **`resolved_forward_aggregate_evidence`** — the NEW read-only serving half. The ONLY function `GET
    /api/backtest` and MCP `query_backtest` call for the LATEST (`is_latest == True`) view. Structurally
    incapable of calling `compute_forward_aggregates` under any circumstance — there is no
    compute-fallback branch here at all, including a would-be lock-wait timeout.

- **Completeness/cutover redesign.** The read-only resolver resolves, for the requested `asof_key`, the
  latest `dataset_version` whose stored rows cover EVERY horizon in `config.walk_forward.horizons`
  ("complete") — never a per-horizon-independent read (the old shape). Three states:
  - `ready` — the complete version found IS the current global `_dataset_version` stamp.
  - `refreshing` — the current stamp's row set isn't complete yet, but a PRIOR complete version survives;
    serves that older version's FULL row set byte-identically (all 5 horizons from the SAME version,
    never mixed), labeled with that version's own `created_at` (max across its horizon rows).
  - `not_yet_computed` — no complete version has ever existed for this `asof_key`:
    `evidence_by_horizon == {}`, `evidence_generated_at == None`, HTTP 200 (never a compute, never 500/503).
  `ForwardAggregateCache` pruning moved from per-horizon-write deletion to a **cutover**: a superseded
  version's rows for an `asof_key` are deleted in one shot ONLY once this write brings the CURRENT
  version's configured-horizon set to full completeness — never before. This closes the confirmed live
  bug the spec cited: a direct DB read found `asof_key='2026-07-17'` already split across two
  `dataset_version` stamps across its 5 rows under the OLD per-horizon-write-deletes-immediately pruning.
  The completeness-lookup query is filtered by `asof_key` alone (never an unfiltered table scan — TC-18).

- **`apps/backend/app/api/backtest.py` / `apps/backend/app/mcp/tools.py`** — both switched their
  per-horizon dict-comprehension call site to the new resolver, called ONCE per request for all
  configured horizons together. Both add `evidence_status` and `evidence_generated_at` to the response.
  For `is_latest == True`, neither function calls `forward_aggregates_ingest_cached` at all (proven by
  structural monkeypatch-to-raise tests, not just by reading the code). For `is_latest == False`
  (historical), the pre-existing per-horizon ensure-computed loop runs first (unchanged behavior, renamed
  function), then both branches read back through the SAME resolver — one code path builds the response's
  evidence fields either way.

- **`apps/backend/app/engine/data_manager.py`** — line 3230's one call site renamed to
  `forward_aggregates_ingest_cached`; the surrounding per-horizon loop, trigger, and `MemoryError`
  isolation are byte-for-byte unchanged.

- **`apps/backend/tests/conftest.py`** — the session-scoped `loaded_engine` fixture now additionally
  warms the LATEST run's `ForwardAggregateCache` (via the SAME `forward_aggregates_ingest_cached` the real
  ingest finalize hook calls) right after `backfill_forward_returns`. **Why this was necessary (not
  optional polish):** before this iteration, `GET /api/backtest`'s `is_latest` view computed-on-first-
  request, so every `loaded_engine`-based test transparently got a warm cache on its first hit. Post-split,
  the `is_latest` view NEVER computes on request — so without this fixture change, every one of the ~29
  test files sharing `loaded_engine` would see `evidence_status == "not_yet_computed"` /
  `evidence_by_horizon == {}` on the latest date, breaking every existing assertion on that content (e.g.
  `test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys`,
  `test_api_engine.py`/`test_api_research.py`'s cross-endpoint forward-return checks, etc.). The fixture
  now warms it up front instead — same values, same producer, no second compute path — restoring the
  exact byte-identical content those tests already expect.

- **Frontend (`Frontend Present: yes`)** — see "Frontend Changes" below and the companion frontend
  handoff.

- **`reports/perf-budgets.md`** — a new dated section for TC-16 (all three serving states vs. the
  committed ≤1.5s `/backtest` budget). This is an honest PENDING placeholder with the exact operator
  protocol — see "Known Issues" below; NOT a fabricated or estimated number.

- **`runs/goal-session-ops-hardening/state/blueprint.md`** — light-touch corrections to the decomposer's
  pre-drafted J-08 paragraphs (both the Notes cell and the Data Contract row's Notes cell) to name the
  ACTUAL function names chosen and to fix one imprecision in the original drafting: the ingest-only
  function is called by TWO sites (the ingest warm loop AND the historical carve-out), not the warm loop
  alone — the pre-drafted "invoked ONLY by..." phrasing undercounted a caller that must exist for TC-13 to
  keep passing. Left as "BUILT (pending evaluator confirmation)" — not upgraded to "evaluator-confirmed"
  per this session's own instruction.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` -- split `forward_aggregates_cached` into
  `forward_aggregates_ingest_cached` (ingest-only, cutover-gated pruning) +
  `resolved_forward_aggregate_evidence` (new, read-only); `compute_forward_aggregates` itself untouched
  (signature/body/columns byte-identical, per the binding "Do not redo").
- `apps/backend/app/api/backtest.py` -- `is_latest`-branching read path; 2 new response fields.
- `apps/backend/app/mcp/tools.py` -- identical switch, mirrors the endpoint.
- `apps/backend/app/engine/data_manager.py` -- one call-site rename (line 3230) + one comment update.
- `apps/backend/tests/conftest.py` -- `loaded_engine` fixture now pre-warms the latest run's
  `ForwardAggregateCache` (required consequence of the split, see "What Was Built" above).
- `apps/backend/tests/test_forward_testing_concurrency.py` -- renamed all references to
  `forward_aggregates_ingest_cached`; this file's existing single-flight tests now prove TC-17
  (the guard survives the split) by construction.
- `apps/backend/tests/test_forward_testing.py` -- renamed references; the dataset-version-change test
  rewritten to warm ALL configured horizons (not just one) both before and after the dataset change, so it
  correctly exercises the NEW cutover-gating contract (a mid-refresh assertion proves the old version's
  rows survive an incomplete new-version warm; a full-refresh assertion proves the cutover then fires).
- `apps/backend/tests/test_data_manager.py` -- renamed 3 `monkeypatch`/direct-reference call sites
  (MemoryError-isolation tests); rewrote 1 test (`..._avoids_recompute_on_subsequent_read`) to call the
  NEW read-only resolver instead of the old function name, since that function is what a real
  "GET /api/backtest-shaped read" now calls (matching this test's own docstring claim more faithfully than
  a bare rename would have).
- `apps/backend/tests/test_api_backtest.py` -- updated one exact-top-level-key-set assertion
  (`test_backtest_does_not_reserve_regime_or_stock_values`) to include the 2 new fields. **Not executed
  this session** (a `loaded_engine`-fixture file, out of scope per the operational constraint) — fixed by
  careful reading since I could see with certainty this assertion would otherwise break.
- `apps/backend/tests/test_forward_testing_serving_split.py` -- **NEW.** 10 tests: completeness/cutover/
  never-computed/byte-identity for the resolver, the `asof_key`-filtered completeness query (TC-18), and
  the two request-serving entry points' wiring (`app.api.backtest.backtest`, `app.mcp.tools.query_backtest`
  called directly as plain functions — no TestClient/`loaded_engine` boot).
- `apps/frontend/lib/api.ts` -- `BacktestResponse` gains `evidence_status` + `evidence_generated_at`.
- `apps/frontend/app/backtest/page.tsx` -- refreshing banner + not-yet-computed empty state (see frontend
  handoff).
- `reports/perf-budgets.md` -- new TC-16 dated section (PENDING, operator protocol).
- `runs/goal-session-ops-hardening/state/blueprint.md` -- corrected J-08 paragraphs (2 spots).

## Tests Run

Command (host-guard-confined, targeted files/nodes only, `taskset -c 0-3,8-11` +
`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`):

```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_forward_testing_serving_split.py \
  tests/test_forward_testing_concurrency.py \
  tests/test_forward_testing.py::test_forward_aggregates_ingest_cached_byte_identical_and_single_row \
  tests/test_forward_testing.py::test_forward_aggregates_ingest_cached_avoids_recompute_on_hit \
  tests/test_forward_testing.py::test_forward_aggregates_ingest_cached_refreshes_on_dataset_version_change \
  tests/test_data_manager.py::test_finalize_hook_warms_forward_aggregates_for_every_configured_horizon \
  tests/test_data_manager.py::test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read \
  tests/test_data_manager.py::test_finalize_hook_never_raises_even_when_everything_fails \
  tests/test_data_manager.py::test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop \
  tests/test_data_manager.py::test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly
```

Result: **24 passed, 0 failed** (22.13s).

Also ran (frontend, no server started — a one-shot type-check, not a persistent process):
`cd apps/frontend && npx tsc --noEmit -p tsconfig.json` — **0 errors**.

Sanity import check (no server started): imported `app.engine.forward_testing`, `app.api.backtest`,
`app.mcp.tools`, `app.engine.data_manager` directly in a Python REPL to confirm no circular-import
regression and that `forward_aggregates_cached` (old name) no longer exists on the module — confirmed.

**NOT run this session (by design, per the pump note's operational constraint):**
- The `loaded_engine`-fixture files (`test_api_backtest.py`, `test_backtest_scorecard.py`,
  `test_mcp_window.py`) and any other `loaded_engine`-dependent test — the ~80-minute fixture cost is
  explicitly out of scope this session. `test_api_backtest.py`'s one affected assertion was still fixed by
  reading (see "Files Changed" above); its remaining ~10 `evidence_by_horizon`-touching tests were not
  independently re-verified live this session (see "Known Issues" #1).
- A full pytest suite run (standing session constraint).
- The unrelated, pre-existing `test_db.py::test_create_all_produces_expected_tables` failure — carried,
  not touched this iteration (no schema change).

## Frontend Changes

See `docs/handoffs/goal-ops-hardening-iter-16-frontend.md` for the full UI writeup.

## Known Issues

1. **`conftest.py`'s `loaded_engine` fixture change is unverified live this session.** This is the single
   highest-leverage change in this diff (it affects ~29 test files) but I could not run ANY
   `loaded_engine`-dependent test to confirm it directly (the fixture costs on the order of tens of
   minutes to build against the full committed seed, out of scope per this session's operational
   constraint). Confidence is high but not proven: (a) the exact SAME call pattern
   (`forward_aggregates_ingest_cached` looped over `cfg.walk_forward.horizons` for the latest run) is
   independently proven correct by 10/10 green tests in `test_forward_testing_serving_split.py`'s
   `evidence_engine`/`endpoint_engine` fixtures; (b) `compute_forward_aggregates` itself is untouched, so
   the actual VALUES this fixture now warms are byte-identical to what the old lazy-on-first-request path
   used to produce. **Recommended next step for the reviewer/QA stage:** run ONE `loaded_engine`-dependent
   test, e.g. `test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys` or
   `test_mcp_window.py::test_query_backtest_structural`, to close this gap with a live result.
2. **TC-16 — RESOLVED (2026-07-23).** The operator ran the pre-registered protocol below and reported a
   68-row raw CSV (`runs/goal-ops-hardening-iter-16/tc16-backtest-poll.csv`) plus console output, PIDs, and
   timestamps verbatim. This pass independently recomputed every derived statistic against that raw CSV
   (not just transcribed it) before writing it up — see `reports/perf-budgets.md`'s new "TC-16 — ... RESULTS"
   section for the full transcription, per-figure verification table, and two flagged-not-self-resolved
   discrepancies (the operator's overall and AFTER-segment "median" figures each equal the single
   upper-middle sorted value rather than the true average of the two middle values for their even-count
   samples — a systematic ~0.001-0.003 s convention difference, not a data problem; true overall median is
   0.304 s, not the reported 0.307 s). **Summary of the result:** the state-machine's STRUCTURAL contract
   (never a skeleton, never a mixed/newer generation while `refreshing`, exactly 3 phases/2 transitions
   across all 68/68 polls) holds perfectly. The LATENCY budget (≤1.5 s) is breached on 7/16 `refreshing`
   polls (up to 12.655 s) and 4/49 post-warm `ready` polls (up to 4.273 s) — concentrated entirely inside the
   ~380 s ingest window (BEFORE/AFTER segments: 0/1 and 0/6 over-budget, both ~0.13-0.17 s). This is a ~14x
   latency improvement over iter-15's 178.74 s cold-recompute MISS and is a stored-row read under
   concurrent-ingest contention, not a live recompute — but it is still 11/68 budget breaches, an honest
   finding recorded as such, not rounded away. Whether this satisfies J-08's budget clause overall is left
   for the evaluator, per the operator's own instruction and this file's protocol. The original protocol
   this resolves (kept for the record, mirrors the iter-3/8/9/14/15 pattern already used in this file):
   - Confirm a cooled host, 1 Hz hwmon sampler running, thermal watchdog armed.
   - `scripts/start-backend.sh` under host-guard confinement (`HOST_GUARD_CPU_LIST=0-3,8-11`,
     `HOST_GUARD_BLAS_THREADS=4`, `HOST_GUARD_REQUIRE_MARKERS=1`). Record the process-start timestamp/PID.
   - Note `/backtest`'s current `evidence_status`/`evidence_generated_at` (expect `ready`).
   - On `/data`, run a small single-day backfill for a not-yet-snapshotted date (bumps `dataset_version`,
     schedules the finalize warm).
   - While that warm is in flight, poll/load `/backtest` repeatedly: record response time vs. the
     committed ≤1.5s budget, confirm `evidence_status == "refreshing"` with the FULLY populated evidence
     section (never a skeleton) and `evidence_generated_at` unchanged from the pre-backfill reading.
   - Once the run record's `aggregates_refreshed` includes `"forward_aggregates"`, reload `/backtest`
     again: record response time vs. the same budget, confirm `evidence_status == "ready"` with a NEW
     `evidence_generated_at`.
   - Cross-read `logs/backend.log` / `logs/hwmon/hwmon.csv` for the window.
   - Report console output, PIDs, and timestamps verbatim — I (or the next dev/reviewer dispatch) will
     transcribe it into `reports/perf-budgets.md` with attribution, marking PASS/WARN against the ≤1.5s
     budget. This is the ONE authorized AG-10-class pass this iteration — not a drill to repeat.
3. **No schema change was needed.** The completeness/cutover design derives entirely from
   `ForwardAggregateCache`'s EXISTING `(horizon, asof_key, dataset_version, created_at)` columns — the
   spec's own escalation flag ("if the redesign turns out to require a genuinely new schema concept...")
   did not trigger. `apps/backend/app/models.py` was not touched.
4. **`test_data_manager.py`'s remaining ~4680 lines were not re-run in full this session** (only the 5
   tests this diff's rename touches). This file has no `loaded_engine` dependency (confirmed by grep), so
   a future full run of it is cheap relative to the `loaded_engine` files above — just outside this
   session's "targeted tests only" scope since nothing else in it was touched.
5. **Byte-identity (AG-3) and no-mixed-version (AG-5) are proven at the unit/fixture level, not yet at
   deep-basis scale.** TC-9's byte-identity check and the completeness/cutover tests all pass against
   small hand-built fixtures; the ONE thing that differs at deep-basis scale is latency, which is exactly
   what TC-16 (Known Issue #2) measures — this is intentional per this iteration's own lesson-application
   (iter-14/15: correctness and latency are different claims, proven separately).

## Suggested Next Phase

**Update (2026-07-23):** the operator's TC-16 pass (Known Issue #2) has now landed and is transcribed, with
independent recomputation, in `reports/perf-budgets.md`'s new "TC-16 — ... RESULTS" section. The structural
serving contract (never a skeleton, never a mixed generation) is fully proven live; the ≤1.5 s latency
budget is breached on 11/68 polls (7/16 `refreshing`, 4/49 post-warm `ready`), entirely within the ~380 s
ingest window, against a ~14x improvement over iter-15's 178.74 s cold-recompute MISS. Whether J-06/J-07 —
both held solely on that cold-MISS residual per the iteration spec — should now close as `passing` given
this WARN-not-PASS latency picture is an evaluator call this handoff does not make. A worthwhile
non-blocking follow-up (noted in the iteration spec's own NOTES, not a DoD item): a fresh
`demo.sh ops-hardening --session-live` operator run to newly exercise J-08's own walkthrough steps
(version-bump → instantly-served last-good with refreshing marker → fresh serve after the warm).
