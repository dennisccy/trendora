# goal-ops-hardening-iter-14 Execution Plan

## Context (read before building)

**REGRESSION-recovery iteration.** iter-13's product diff left `forward_testing.py` byte-unchanged,
but iter-13's own concurrent browser-qa load (4 replay backfills + a diagnostic read) escalated the
standing, owner-deferred AG-8 defect from a silent per-request abort into a ~12-minute full-backend
futex-style wedge needing an operator hard-restart — falsifying the "smaller blast radius, keep
deferring" rationale iters 9-12 used. The owner has now authorized the direct fix (`docs/goal.md`
gained Must-have journey **J-07**, commit `e5624010`, verified). This iteration IS that fix.

**Goal alignment check:** J-07 ("Heavy aggregates never take the service down") and J-06's two
transcriptional closure items are both pre-existing Must-have journeys/acceptance clauses already
committed in `docs/goal.md` — this spec is a direct, faithful continuation, not new scope. The one
interpretation call worth flagging (not a drift, a disclosed tightening): the decomposer required a
REAL tightened-`ulimit -v` induction test **and** a concurrent-caller test, which is stricter than
J-07 step 4's literal "test hook OR monkeypatch, single sequential process" wording. This is justified
— the cheaper monkeypatch/single-process reading is exactly what already missed this defect twice this
session (iter-11 live 500s, iter-13's live 12-minute wedge) — and is logged in `assumptions.md`. Not
scope creep; carry it forward as written.

**The two reads this iteration rewrites** (verified live in `apps/backend/app/engine/forward_testing.py`,
inside `compute_forward_aggregates`):
- `~line 813-818` — `fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)` (+ an
  optional `.join(ScannerRun...)` for the `as_of` filter), materialized via `.all()`. Only 4 fields are
  ever read off each row afterward: `run_id`, `symbol`, `realized_return`, `max_drawdown`.
- `~line 825-826` — `select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`. Only
  8 fields are ever read: `run_id`, `ticker`, `leadership_bucket`, `setup_status`, `sector`, `rank`,
  `is_vcp`, `is_pullback_to_rising_dma`, `is_flat_base_breakout`.
- Both tables have grown ~9x since `docs/goal.md`'s last ground-truth note (`scanner_results` 611,689
  rows, `forward_returns` 3,098,302 rows) — materially heavier than ever measured.
- **Do NOT touch** the third read in the same function, `run_rows = session.exec(select(ScannerRun)...)
  .all()` (~line 829-832) — bounded/small (one row per cadence date, ~180+ total), not one of the
  spec's two named offenders, and mirrors the codebase's own established rationale for `_backfill`'s
  materialized `ScannerRun` list (small, safe to hold whole). Rewriting it is scope creep.

**In-repo precedent to mirror (do not invent a new technique):**
- `_streamed_existing_keys` (`forward_testing.py:~437-449`, iter-47/J-105) — column-projected
  `session.exec(select(...)).yield_per(batch)` bounded by `cfg.research.read_batch_size`
  (`config.yaml`: 2000) — the single source of the streaming batch size; do not add a second one.
- **Closer structural match** (same shape as what this iteration needs — stream `ForwardReturn` into a
  lookup dict, stream `ScannerResult` and probe that dict): `app/engine/research.py`'s iter-47/J-105
  trio — `_subject_matching_result_rows` (~line 983-1024, column-projects `ScannerResult`,
  `yield_per(batch)`, builds an ordered list + a `needed_runs` set), the `ForwardReturn` scan inside
  `_event_study_members` (~line 1074-1083, column-projects `run_id, symbol, realized_return, mae, mfe,
  max_drawdown`, streams into a `dict[(run_id, symbol) -> tuple]`), and `_regime_by_run_projected`
  (~line 1027-1039, a projected+streamed `ScannerRun` lookup). All three are proven byte-identical
  rewrites of this exact unbounded-ORM-read pattern in this exact codebase — reuse the technique, not
  necessarily the code.
- `compute_forward_aggregates` keeps its exact signature/return shape; `forward_aggregates_cached`
  (same file), `GET /api/backtest` (`app/api/backtest.py:~72`), and the MCP `query_backtest` tool
  (`app/mcp/tools.py:~205`) all call it unchanged — one call site each, confirmed, no second
  aggregation path.

**Escalation discipline (spec's own words, do not soften):** if the rewrite still permits a wedge
under concurrent load or induced pressure (TC-3/TC-4/TC-6 fail), report it plainly in the handoff —
this is a second consecutive failure of this exact code path and decision-tree escalation exists
precisely for that.

**Reporting discipline (iter-12 lesson, carried):** the dev handoff must not claim J-06 "passes" —
record what TC-8/TC-9 actually show and let the evaluator score it.

## PUMP NOTE constraints (operator, this dispatch) — binding on this plan

- Services are **DOWN** (nothing on :8255/:3255) as of this dispatch. Agents in this pipeline CANNOT
  start/stop services (permission classifier) and the subagent-resume channel is broken — write every
  restart/boot/kill step, including the TC-5/TC-6 heavy-pass process start, as an **operator-performed
  fallback**: the operator starts/monitors and reports console output, pids, and timestamps verbatim;
  the developer records that operator-provided output with attribution in `reports/perf-budgets.md` —
  never fabricate or silently omit a number.
- No full pytest suite (many hours on the 30-year basis) — targeted files only, host-guard-confined
  (`taskset -c 0-3,8-11`; `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/
  `NUMEXPR_NUM_THREADS=4`). `loaded_engine`-fixture files legitimately run ~80 minutes — not a hang.
- The TC-5/TC-6 full-deep-basis pass is AG-10-class: exactly ONE owner-authorized, operator-supervised
  pass, on a cooled host, sampler + watchdog armed, sequenced **after** the bounded rewrite lands and
  its targeted small-fixture tests are green. The current unbounded code hits the 6 GB cap on the
  live/deep basis TODAY — no full-basis compute before the fix is in.
- TC-1/TC-2's byte-identity fixtures run on a SMALL hand-built basis first (mirroring `aggregates_engine`),
  never the live 30-year DB.
- Do not fold in `HOST_GUARD_REQUIRE_MARKERS` (already flipped, verified current in `host-guard.env`),
  any `scripts/automation/*` framework file, or any scope beyond this spec.
- Before running tests or anything that writes temp files:
  `export TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-har-5d3197c0.3543639"`.

## What to Build

- **Bounded/streamed rewrite of `compute_forward_aggregates`'s two whole-partition reads**
  (`apps/backend/app/engine/forward_testing.py`):
  - `ForwardReturn` read → column-project `run_id, symbol, realized_return, max_drawdown` (keep the
    existing `as_of` join/filter), consume via `.yield_per(cfg.research.read_batch_size)`, accumulating
    `ret_by_run_symbol`, `mdd_by_run_symbol`, and the `runs_with_fr` set incrementally.
  - `ScannerResult` read → column-project the 8 fields actually used, consume via the same
    `.yield_per(batch)` pattern, building `stock_obs` directly in the loop (same
    `if realized is None: continue` gate, same row order → byte-identical list).
  - Everything downstream (`_group_means`, excess, control groups, attribution) is untouched.
  - Same signature, same return dict, all three call sites unchanged.
- **Byte-identity test suite**: rewritten output `==` a pre-rewrite reference, across all 5 configured
  horizons (`[1, 5, 10, 20, 60]`) x `{as_of=None, a historical as_of}` (10 payload comparisons), full-dict
  equality across every key (`overall`, `by_bucket`, `by_setup`, `by_regime`, `by_vcp`,
  `by_pullback_to_rising_dma`, `by_flat_base_breakout`, `excess`, `control_group`, `attribution`).
- **A REAL (non-monkeypatched) tightened-`ulimit -v` induction test**: a throwaway subprocess with an
  artificially lowered virtual-memory cap, against a fixture sized to trip the gap between the OLD
  unbounded path's memory need and the NEW bounded path's — proves an honest `MemoryError` (or a
  logged isolated failure), no hang, and a successful same-process subsequent DB read immediately after.
- **A concurrent-caller (N>=4) regression test** against a shared fixture DB, mirroring iter-13's actual
  trigger shape (4 concurrent backfills + a diagnostic read) — every call returns (success or clean
  isolated failure) within a bounded timeout (e.g. 30s); none left blocked.
- **ONE operator-authorized, host-guard-confined, full-deep-basis measurement pass**: in a single
  long-lived backend process, sequentially warm all 5 configured horizons then serve
  `GET /api/backtest` once per horizon; poll `GET /api/health` at 1 Hz throughout; sample
  `/proc/<pid>/status` `VmPeak` at 1 Hz; capture process-start → first-200 boot timing; induce a
  memory-pressure condition during one horizon's warm and confirm the SAME process keeps serving
  health + previously-cached reads afterward (no restart).
- **`reports/perf-budgets.md`** gains two new dated sections: (a) the TC-5/TC-6/TC-7 pass results
  (health-poll record, VmPeak vs. 6,291,456 KB / 6144 MB with stated margin, boot timing vs. ≤5s), (b)
  a transcription of iter-13's already-evaluator-confirmed J-06 readings (218.7 ms / 218.7 ms / 219.2 ms
  on `/data`, 70.5 ms on `/`, each labeled PASS against ≤1500 ms) — transcription only, not a
  re-measurement.
- **Dev handoff** at `docs/handoffs/goal-ops-hardening-iter-14-dev.md`.

## Agents Required

- backend-data: yes -- the bounded/streamed rewrite; the byte-identity, real-memory-cap-induction, and
  concurrent-caller test suites; coordinating (with operator fallback) the one authorized TC-5/TC-6
  heavy pass and recording its results; the two `reports/perf-budgets.md` sections; the dev handoff.
- frontend-ux: no -- `docs/goal.md`/this spec both state no frontend file is touched
  (`Frontend Present: no`); the observable difference is behavioral (no frozen/blank readiness frame
  under load), not a new UI feature, display, action, or surface.

## Frontend Present

no

Note for the QA stage: even with no frontend file touched, TESTING REQUIREMENTS names four browser
journeys (J-01, J-03, J-04, J-05) for regression replay — the framework fix (commit `d0799803`,
verified) stops `Frontend Present: no` from suppressing the browser-qa lane whenever TESTING
REQUIREMENTS names journeys. Browser-qa MUST still run this iteration.

## Out of Scope (do not build)

- Raising `server.memory_cap_mb` (6144) or `malloc_arena_max` (2) — must stay under the EXISTING cap.
- Touching `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or `app/engine/warmup.py` —
  byte-unchanged since iter-9, unrelated to this fix.
- Touching `scripts/start-backend.sh` / `scripts/dev.sh`'s host-guard blocks, or
  `HOST_GUARD_REQUIRE_MARKERS` — AG-10 launcher confinement is DONE and verified current.
- Re-measuring the 10 already-in-budget J-06 pages or re-deriving the 1.364s boot number — settled;
  only a fresh spot-check timestamp piggybacks on this iteration's own process start.
- The `demo.sh ops-hardening --session-live` walkthrough — operator/owner-owned this iteration.
- Retiring/rewiring the dead `apps/frontend/components/major-indexes-card.tsx` — test-plan/UI-backlog
  item, not product-iteration remit.
- Patching `scripts/automation/*` framework files.
- Any aggregation candidate or data path besides `compute_forward_aggregates` (all others are
  already-fixed "Do not redo" items).
- Repeating/multiplying the heavy full-deep-basis measurement pass beyond the ONE authorized run.
- Rewriting the `ScannerRun` read (`run_rows`) inside `compute_forward_aggregates` — bounded/small,
  not one of the spec's two named offenders.
- Any new UI page, nav entry, or displayed value.

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` -- rewrite the `ForwardReturn` read (`fr_stmt`/`.all()`,
  ~line 813-818) and the `ScannerResult` read (~line 825-826) inside `compute_forward_aggregates` to
  column-projected `.yield_per(cfg.research.read_batch_size)` streaming, mirroring
  `_streamed_existing_keys` and `research.py`'s `_event_study_members`/`_subject_matching_result_rows`
  trio. Leave the `ScannerRun` read (`run_rows`, ~line 829) untouched. No signature/return-shape change.
- `apps/backend/tests/test_forward_testing_streaming.py` (extend) or a new sibling file (e.g.
  `test_forward_testing_aggregates_streaming.py` — developer's choice, per the spec's own "if a new
  sibling file is cleaner" wording) -- byte-identity tests across all 5 horizons x
  `{as_of=None, historical as_of}`, mirroring this file's existing `_streamed_existing_keys` convention.
- A new or existing test module for TC-3 (real `ulimit -v` induction) and TC-4 (concurrent-caller) --
  suggested: the same new streaming test file, or a new `test_forward_testing_concurrency.py`. Both
  need a file-backed (not `:memory:`) SQLite fixture so a subprocess / multiple threads-processes can
  share it.
- `reports/perf-budgets.md` -- two new dated sections (TC-5/TC-6/TC-7 measurement pass; TC-8
  transcription of iter-13's readings).
- `docs/handoffs/goal-ops-hardening-iter-14-dev.md` -- new dev handoff.

No file under `apps/frontend/` should appear in the diff. `main.py`, `app/api/health.py`,
`app/engine/readiness.py`, `app/engine/warmup.py` must be byte-unchanged.

## Implementation notes (advisory, not prescriptive)

- **TC-3 fixture/cap sizing is a real empirical task**, not a fixed number: size a fixture (likely tens
  of thousands to ~100K+ `ForwardReturn`/`ScannerResult` rows at a single horizon) against a modest
  `ulimit -v` (likely a few hundred MB) such that the OLD `.all()` pattern clearly exceeds it while the
  NEW streamed pattern stays comfortably under it. Expect to iterate on both numbers empirically —
  spawn via `subprocess.run(["bash", "-c", f"ulimit -v {cap_kb}; exec {python} -c '...'"])` or
  `resource.setrlimit(RLIMIT_AS, ...)` in a forked child, whichever is cleaner in this codebase's
  existing test style.
- **TC-4** is most naturally a `ThreadPoolExecutor`-style test (N>=4 threads, each opening its own
  `Session` against a shared file-based engine) — this most directly mirrors how a real multi-threaded
  request server actually triggers concurrent calls into `compute_forward_aggregates`/
  `forward_aggregates_cached`; separate processes are also acceptable per the spec's own wording.

## Key Test Scenarios

- TC-1/TC-2: given a small fixture DB (mirroring `aggregates_engine`) and a pre-rewrite reference
  payload, the rewritten `compute_forward_aggregates` returns a `==` dict across all 10 aggregate keys,
  for every one of the 5 configured horizons x `{as_of=None, a historical as_of excluding the newest
  snapshot}` (10 payload comparisons total).
- TC-3: a throwaway subprocess with `ulimit -v` below what the OLD unbounded path needed but above what
  the NEW bounded path needs, run against a fixture sized to trip that gap, raises `MemoryError` (or a
  logged isolated failure) without hanging; a subsequent DB read in the SAME process succeeds
  immediately after.
- TC-4: >=4 concurrent callers (threads or processes) invoking `compute_forward_aggregates`/
  `forward_aggregates_cached` against a shared fixture DB all return (success or clean isolated
  failure) within a bounded timeout (e.g. 30s) — none left blocked.
- TC-5/TC-6: the one authorized host-guard-confined full-deep-basis pass — `GET /api/health` answers
  HTTP 200 on every 1 Hz poll throughout a sequential 5-horizon warm + per-horizon `GET /api/backtest`
  serve in one long-lived process; peak `VmPeak` stays below 6,291,456 KB with margin recorded; an
  induced memory-pressure abort during one horizon's warm stays isolated to that step while the SAME
  process keeps serving health + previously-cached reads (no restart needed).
- TC-7: process-start → first `GET /api/health` 200 elapsed time from this SAME pass, recorded against
  the committed ≤5s boot budget.
- TC-8: `reports/perf-budgets.md` gains a new dated section transcribing 218.7 ms / 218.7 ms / 219.2 ms
  (`/data`) and 70.5 ms (`/`), each labeled PASS against ≤1500 ms.
- TC-9: browser-qa's regression replay of J-01/J-03/J-05 (each drives a real backfill through the same
  rewritten warm path) plus one `/backtest` load shows the readiness badge never frozen/blank at any
  step, and `/backtest` renders its per-horizon evidence panel without a frozen/blank frame.
- TC-10: J-01/J-03/J-04/J-05 (required-still-passing) all re-verify PASS via deterministic golden
  replay or LLM fallback.
- TC-11: the coherence-auditor confirms `compute_forward_aggregates`/`GET /api/backtest` remain the
  sole producer/endpoint for this Data Contract row — zero second producer.
- Regression floor: targeted backend test subset (files above) run host-guard-confined, zero new
  failures beyond the pre-existing, unrelated `tests/test_db.py::test_create_all_produces_expected_tables`
  failure.

## Environment Note (for the developer agent)

Before running any test or command that writes temp files:
`export TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-har-5d3197c0.3543639"`.
Services are DOWN as of this dispatch — request an operator restart (with recorded pid/timestamp) for
any step that needs a live process, rather than attempting to start/stop one directly.
