# Goal Iteration 14 — Bounded/streamed forward-aggregate rewrite (J-07, AG-8 REGRESSION recovery)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 14
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(critical)*

## GOAL

The backend stays available and honestly responsive — `/api/health` keeps answering, no page freezes on a
blank "Checking backend…" frame — while computing and serving heavy forward-return aggregates for every
configured horizon, closing the critical AG-8 defect that caused this session's two full-availability
outages (iter-7, iter-13).

## BACKGROUND

iter-13 REGRESSION-halted under decision-tree C.1: the critical, session-long AG-8 defect
(`compute_forward_aggregates`'s unbounded `ForwardReturn`/`ScannerResult` whole-partition ORM reads,
`apps/backend/app/engine/forward_testing.py:805/826`) escalated from a silent per-request abort
(iter-11/iter-12) to a ~12-minute full-backend futex-style wedge under concurrent load (4 replay
backfills + a diagnostic read), needing an operator hard-restart — falsifying the "mitigation holds,
smaller than iter-7" rationale iters 9-12 used to defer it. **Lesson (iter-13, verbatim intent):** a
carried critical anti-goal's severity must be re-tested against fresh load evidence every iteration, not
assumed stable — this iteration's own tests must therefore prove the fix against the ACTUAL trigger shape
(concurrent load), not only a narrower single-process reading. The owner has now authorized the fix
directly: `docs/goal.md` gained Must-have journey **J-07** ("Heavy aggregates never take the service
down", commit `e5624010`, verified) and flipped `HOST_GUARD_REQUIRE_MARKERS=1` (same commit, verified —
this resolves that item as an open blocker). J-07 is this iteration's sole risky target (rubric rule 5:
never bundle two risky journeys); J-06's two purely-transcriptional residual gaps (the `perf-budgets.md`
single-source clause and J-04's overdue live boot spot-check, DoD-#7) ride along at zero incremental code
risk. **Depth is full — trigger 1 (structural/cross-cutting):** this rewrites the core forward-aggregate
read path shared by `GET /api/backtest`, the MCP `query_backtest` tool, and every ingest job's finalize
warm trigger (`_refresh_ingest_aggregates`), and the prior two failures of this exact code path
(iter-7, iter-13) both escaped a lean cycle's review + browser-qa loop and needed the full pipeline's
audit/closure to characterize accurately. The affected tables have grown materially since goal.md's
"2026-07-18 ground truth" note: `scanner_results` is now 611,689 rows (was 66,836, ~9×) and
`forward_returns` is now 3,098,302 rows (was 344,334, ~9×) — read directly from
`apps/backend/data/trendora.db` for this spec, read-only, no service start required — so the unbounded
read this iteration targets is materially heavier today than when it was first measured.

## IN SCOPE

### Backend
- [ ] Rewrite `compute_forward_aggregates`'s two whole-partition ORM reads
  (`apps/backend/app/engine/forward_testing.py`: the `fr_stmt` / `session.exec(...).all()` read of
  `ForwardReturn` at horizon scope, and `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`
  at line 826) to column-projected, chunked/streamed access bounded by the EXISTING
  `cfg.research.read_batch_size` config knob (already the single source of streaming batch size across
  `research.py`'s heavy queries and this SAME module's `_streamed_existing_keys`, iter-47/J-105 — do not
  introduce a second batch-size config value). `compute_forward_aggregates` remains the SAME canonical
  producer with the SAME signature; `forward_aggregates_cached`, `GET /api/backtest`
  (`apps/backend/app/api/backtest.py`), and the MCP `query_backtest` tool
  (`apps/backend/app/mcp/tools.py`) call it UNCHANGED — no second aggregation path, no schema change
  (`ForwardAggregateCache` itself is untouched).
- [ ] Add fixture-backed byte-identity tests (small basis, mirroring the existing `aggregates_engine`
  fixture convention in `apps/backend/tests/test_forward_testing.py`) proving the rewrite is
  behaviorally identical to the pre-rewrite reference across all 5 configured horizons
  (`[1, 5, 10, 20, 60]`), with `as_of=None` and with a historical `as_of`.
- [ ] Add a REAL (non-monkeypatched) tightened-memory-cap induction test — a throwaway subprocess with an
  artificially lowered `ulimit -v` against a sized fixture — proving the rewritten path aborts honestly
  without leaving the process's DB session/connection wedged. (The existing
  `test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds`-style tests in
  `test_data_manager.py` all use `monkeypatch`-injected `MemoryError`, which did not catch iter-11's live
  500s or iter-13's live wedge — this iteration must not repeat that same-layer-only blind spot.)
- [ ] Add a concurrent-caller regression test (N ≥ 4 simultaneous callers against a shared fixture DB,
  mirroring iter-13's actual trigger shape of 4 concurrent backfills + a diagnostic read) proving no
  caller hangs beyond a bounded timeout.
- [ ] Operator-authorized, host-guard-confined, ONE supervised full-deep-basis measurement pass (see
  NOTES for the exact protocol) recording: (a) `GET /api/health` polled at 1 Hz throughout a sequential
  warm of all 5 configured horizons plus one `GET /api/backtest` call per horizon in the SAME long-lived
  process, (b) the process's peak `VmPeak` (`/proc/<pid>/status`, 1 Hz sampling) against the declared
  `server.memory_cap_mb` (6144 MB / `ulimit -v` 6,291,456 KB) cap, (c) a live boot-to-first-200 timing
  captured from this SAME process start (closes J-04 DoD-#7). All three recorded in
  `reports/perf-budgets.md`.
- [ ] Transcribe iter-13's already evaluator-confirmed J-06 passing readings (218.7 ms / 218.7 ms /
  219.2 ms on `/data`, 70.5 ms on `/`) into `reports/perf-budgets.md` as a new dated section (closes
  J-06's single-source Consistency clause — a transcription of existing evidence, not a re-measurement).

### Frontend
None — no frontend file is touched (Frontend Present: no). The engine still forces the browser-qa lane
this iteration because Target/Required journeys are named (framework fix, commit `d0799803`, verified) —
see TESTING REQUIREMENTS.

### New user-facing capability
None new. The observable difference is behavioral, not a new feature: the app stays responsive (readiness
badge Ready, `/backtest` renders) while forward aggregates compute, instead of the frozen/blank
"Checking backend…" state iter-7 and iter-13 both produced.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — no page, panel, or card changes.

### Product surface delta
No visible surface changes when the fix holds; the delta is the ABSENCE of the frozen/blank-frame failure
mode previously reproducible during heavy forward-aggregate computation under concurrent load.

### Blueprint conformance
No new page/nav. J-07's home is cross-cutting (the global readiness badge, present on every page, plus
the existing `/backtest` page's `GET /api/backtest` evidence panel) — added as a new row in
`blueprint.md`'s Feature/journey-homes table (Nav section: (global) / Backtest). J-06 stays on its
existing cross-cutting home (`reports/perf-budgets.md` as the canonical artifact).

### Data-contract additions
None. `compute_forward_aggregates` remains the sole computing module and `GET /api/backtest` the sole
serving endpoint for this Data Contract row (the MCP `query_backtest` tool call site is unchanged too) —
this iteration changes internal read strategy only, never the contract's identity, shape, or values
(byte-identity is the acceptance criterion, not a new value).

## OUT OF SCOPE

- Raising `server.memory_cap_mb` (6144) or `malloc_arena_max` — the fix must stay under the EXISTING cap
  with margin; iter-13's own next-step recommendation explicitly rejected a cap raise as "does not fix
  the unbounded pattern."
- Touching `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or `app/engine/warmup.py` — binding
  "Do not redo" (iteration-state); the boot-path surface is unrelated to this fix and byte-unchanged since
  iter-9.
- Touching `scripts/start-backend.sh` / `scripts/dev.sh`'s host-guard blocks — AG-10 launcher confinement
  is DONE (iter-9/11), `/proc`-verified across iters 9-13; do not re-open.
- Re-measuring the 10 already-in-budget J-06 pages or re-deriving the 1.364 s boot number itself — settled
  (iter-11); only a FRESH spot-check timestamp is captured this iteration, piggybacked on the process
  start this iteration already needs.
- The `demo.sh ops-hardening --session-live` walkthrough (J-05/J-06 Acceptance) — no autonomous mechanism
  produces it (iter-12 finding, unchanged); stays an owner/framework decision, not developer scope.
- Retiring or rewiring the dead `apps/frontend/components/major-indexes-card.tsx` (UT-07's stale FAIL) —
  explicitly out of a product iteration's remit per iter-13's own audit finding F1 (a test-plan/UI-backlog
  item); do not touch it here.
- Patching `scripts/automation/*` framework files — out of product-iteration remit; also moot this
  iteration since the merge-verdict, journey-forced-browser-lane, and replay-retry fixes already landed
  (commit `d0799803`, verified against the repo).
- Any other aggregation candidate or data path besides `compute_forward_aggregates` (coverage, membership
  timeline, market phase, research hot-keys, index-series are all already-fixed "Do not redo" items).
- Repeating or multiplying the heavy full-deep-basis measurement pass beyond the ONE authorized run this
  iteration (AG-10-class; not a drill to repeat casually).
- Any new UI page, nav entry, or displayed value.

## DEFINITION OF DONE

- [ ] `compute_forward_aggregates` reads `ForwardReturn`/`ScannerResult` via column-projected,
  `yield_per`-streamed access bounded by `cfg.research.read_batch_size` — zero `.all()` whole-partition
  materialization remains on this path; `forward_aggregates_cached`, `GET /api/backtest`, and the MCP
  `query_backtest` tool call the SAME function/signature unchanged (TC-1, TC-2, TC-11).
- [ ] Byte-identity proven: rewritten output equals the pre-rewrite reference for all 5 configured
  horizons, with and without `as_of` (TC-1, TC-2).
- [ ] A real (non-monkeypatched) tightened-memory-cap test proves an honest, non-wedging abort with a
  successful same-process subsequent read (TC-3).
- [ ] A concurrent-caller test (N ≥ 4) proves no caller hangs beyond a bounded timeout (TC-4).
- [ ] The operator-authorized, host-guard-confined, single full-deep-basis pass records `/api/health`
  responsiveness throughout the full-horizon warm + per-horizon `GET /api/backtest` serve, and records
  process `VmPeak` under `server.memory_cap_mb` with a stated margin, in `reports/perf-budgets.md`
  (TC-5, TC-6).
- [ ] `reports/perf-budgets.md` gains iter-13's already-confirmed J-06 passing readings as a transcribed
  dated section (TC-8).
- [ ] A live boot-to-first-200 timing from this iteration's operator-authorized process start is recorded
  against the committed ≤5 s budget (TC-7).
- [ ] Required-still-passing journeys J-01/J-03/J-04/J-05 remain green via deterministic replay + LLM
  fallback (TC-10).
- [ ] The global readiness badge shows no frozen/blank frame during browser-qa's regression replay of
  J-01/J-03/J-05 (each of which drives a real backfill through the SAME rewritten warm path) (TC-9).
- [ ] No anti-goal violation introduced or worsened; the coherence-auditor confirms zero second producer/
  endpoint for the touched Data Contract row (TC-11).
- [ ] Unit tests pass, host-guard-confined (`taskset -c 0-3,8-11`, BLAS/OMP threads 4); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-14-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01, J-03, J-04, J-05 (regression replay/LLM fallback — each exercises the rewritten warm
  path live via a real backfill); J-06 (no new page-load measurement needed — the transcription is a
  developer-stage artifact edit); J-07 has no dedicated new page — verify via the readiness badge and
  `/backtest` render captured during the J-01/J-03/J-05 replay pass (TC-9), plus the developer-stage
  API-level checks below.
- Unit/integration: `apps/backend/tests/test_forward_testing.py` (extend the existing
  `aggregates_engine`-based byte-identity tests to cover the rewrite; mirror
  `test_forward_testing_streaming.py`'s convention for a projected/streamed-read test file if a new
  sibling file is cleaner than extending the existing one); a real (non-monkeypatched) tightened-`ulimit -v`
  subprocess test; a concurrent-caller (N ≥ 4) test. All run host-guard-confined
  (`taskset -c 0-3,8-11`, `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS=4`)
  — never the full pytest suite concurrently (existing session convention).
- Error cases: the induced tightened-memory-cap condition (TC-3) and the concurrent-caller saturation
  condition (TC-4) are this iteration's "invalid input" analogues — both must degrade to an honest,
  isolated failure (a raised `MemoryError` / a logged, contained abort) rather than corrupting output,
  silently returning partial data as if complete, or hanging the process.

Test-first contract:

- TC-1: given a small fixture DB and a pre-rewrite reference payload for horizon=20, `as_of=None`,
  computed once and stored, when the rewritten `compute_forward_aggregates` runs against the identical
  fixture, then its returned dict is `==` to the stored reference payload across every key (`overall`,
  `by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `by_pullback_to_rising_dma`,
  `by_flat_base_breakout`, `excess`, `control_group`, `attribution`).
- TC-2: given the same fixture DB, when `compute_forward_aggregates` runs for every one of the 5
  configured horizons (1, 5, 10, 20, 60), both with `as_of=None` and with a historical `as_of` date that
  excludes the newest snapshot, then each of the 10 resulting payloads is byte-`==` to its corresponding
  pre-rewrite reference payload.
- TC-3: given a throwaway subprocess with `ulimit -v` set below what the pre-rewrite unbounded path would
  need but above what the rewritten bounded path needs, when `compute_forward_aggregates` (or
  `forward_aggregates_cached`) is invoked against a fixture sized to trip that gap, then it raises
  `MemoryError` (or returns a logged, isolated failure) without hanging, and a subsequent DB read in the
  SAME process (a fresh session re-reading an existing `ForwardAggregateCache` row) succeeds immediately
  afterward.
- TC-4: given 4 or more concurrent callers (threads or processes) invoke
  `compute_forward_aggregates`/`forward_aggregates_cached` against a shared fixture DB at the same time,
  when all calls are issued, then every call returns (success or a clean isolated failure) within a
  bounded timeout (e.g., 30 s) with none left blocked.
- TC-5: given the backend process is started fresh under host-guard confinement
  (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4) against the full deep-basis DB with the 1 Hz hwmon
  sampler and thermal watchdog armed (Tctl ≥ 95 °C sustained 10 s / DIMM ≥ 85 °C / NVMe ≥ 75 °C abort),
  when the finalize warm triggers all 5 configured horizons sequentially and `GET /api/backtest` is then
  called once per horizon in the SAME long-lived process, then every `GET /api/health` poll (1 Hz
  throughout) returns HTTP 200 within its committed budget, and the run's peak `VmPeak` is recorded and
  stays below 6,291,456 KB (6144 MB) with the margin stated in `reports/perf-budgets.md`.
- TC-6: given the same run as TC-5, when a memory-pressure condition is induced (test hook or a tightened
  cap in a nested throwaway process, per J-07 step 4) during one horizon's warm, then that warm step
  aborts honestly (logged, isolated to that step) while the SAME long-lived process continues to answer
  `GET /api/health` with HTTP 200 and continues serving a previously-cached `GET /api/backtest` horizon
  from `ForwardAggregateCache` — no restart required.
- TC-7: given the process-start timestamp recorded for TC-5's boot, when the first `GET /api/health`
  HTTP 200 is observed, then the elapsed seconds are recorded in `reports/perf-budgets.md` against the
  committed ≤5 s boot budget.
- TC-8: given the developer transcribes iter-13's already-verified browser readings, when
  `reports/perf-budgets.md` is inspected, then it contains a new dated section listing 218.7 ms,
  218.7 ms, and 219.2 ms for `/data` and 70.5 ms for `/`, each labeled against the ≤1500 ms budget as PASS.
- TC-9: given browser-qa-agent's regression replay drives J-01/J-03/J-05 (each triggering a real backfill
  through the SAME `_refresh_ingest_aggregates` finalize hook this iteration rewrites, mirroring
  iter-13's own concurrent-backfill trigger shape), when the replay executes and `/backtest` is loaded
  once during the same pass, then the captured screenshots/DOM reads show the global readiness badge
  never rendering the frozen "Checking backend…" state or blank cards at any step, and `/backtest`
  renders its per-horizon evidence panel without a frozen or blank frame.
- TC-10: given J-01/J-03/J-04/J-05 are currently `passing`, when the deterministic golden-script replay
  runs against this iteration's build, then all four re-verify PASS (or, for any journey without a
  golden, the LLM browser-qa fallback returns PASS).
- TC-11: given no frontend file is touched and no new endpoint/table is added, when the
  coherence-auditor checks the Data Contract, then `app.engine.forward_testing.compute_forward_aggregates`
  and `GET /api/backtest` remain the sole computing module and sole endpoint for this row, with zero
  second producer recorded in `coherence.md`.

## NOTES

- **Operational protocol for TC-5/TC-6 (AG-10-class, ONE supervised pass):** launch via
  `scripts/start-backend.sh` only (never ad hoc), with `project-extensions/host-guard/host-guard.env`'s
  caps active (`HOST_GUARD_CPU_LIST="0-3,8-11"`, `HOST_GUARD_BLAS_THREADS=4`,
  `HOST_GUARD_REQUIRE_MARKERS=1` as of commit `e5624010` — verified current), the 1 Hz hwmon sampler
  running, and the thermal watchdog armed at the README abort criteria (mirrors the iter-3/8/9 protocol
  used for every prior VmPeak measurement this session). Standard path: the developer/reviewer runs it
  directly under this confinement (this is how iter-3/8/9's own heavy measurements were performed).
  Fallback: if the executing agent's environment blocks the process start this session, the operator
  starts/monitors it and reports console output, pids, and timestamps verbatim for the developer to
  record with attribution in `reports/perf-budgets.md` — never fabricate or silently omit a number
  (mirrors the accepted fallback pattern in `assumptions.md` iter-10/iter-11). Services are down as of
  this dispatch (nothing on :8255/:3255) — a fresh start is required regardless of who performs it.
- **Lesson applied (iter-9, VmPeak is a monotone high-water mark):** do not accept a "measurement
  artifact" or "cadence" explanation for any high `VmPeak` reading in TC-5 — re-sampling at a different
  interval cannot lower a kernel-maintained peak. Record the number as-is.
- **Lesson applied (iter-11, cross-read logs before accepting "ambient"):** if `GET /api/health` shows any
  outlier during TC-5, cross-read `logs/backend.log` and `logs/hwmon/hwmon.csv` for the same window before
  attributing it to host contention — a fast response can still be a 500, and this host's `MemAvailable`
  has never been the actual constraint (the per-process `ulimit -v` cap is).
- **Lesson applied (iter-12, closing an evidence gap ≠ passing):** the dev handoff must not claim J-06
  "passes" — record what TC-8 and TC-9 actually show and let the evaluator score the journey; J-06's
  owner-blocked walkthrough item is explicitly excluded from this iteration's DoD.
- **Why TC-3/TC-4 go beyond J-07 step 4's literal wording:** J-07 step 4 permits "a test hook OR a
  tightened cap in a throwaway process." This iteration requires a REAL tightened-`ulimit -v` induction
  (not only a `monkeypatch` stub) because the repo's existing
  `test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds`-style tests are all
  monkeypatch-based and did not catch iter-11's live 500s or iter-13's live 12-minute wedge — the same
  layer that already "passes" cannot be trusted alone this time. It also requires a concurrent-caller
  test because iter-13's actual trigger was 4 concurrent backfills + a diagnostic read, not a single
  sequential process — logged to `assumptions.md` (this iteration) as an interpretation call.
- **Resolved since iter-13 (verified against the repo, not just the pump note):**
  `merge_ui_test_results.py`'s dropped-`**FAIL**`-cell bug, the `Frontend Present: no` browser-lane
  misroute, and the golden-replay fill/click flake are all fixed (commit `d0799803`). Downstream agents
  should still sanity-check the raw `.llm.md` against the merged result once this iteration exercises the
  fix live, since this is its first real run.
- **Carried, unrelated:** `tests/test_db.py::test_create_all_produces_expected_tables` is a pre-existing
  failure, unaffected by this iteration (no schema change). Not this iteration's scope.
- **Escalation flag:** none. This iteration is itself the REGRESSION-recovery pass; if TC-3/TC-4/TC-6
  cannot be made to pass (i.e., the rewrite still permits a wedge under concurrent load or induced
  pressure), do not soften the finding — report it plainly for the evaluator, since a second consecutive
  failure of this exact code path is exactly what decision-tree escalation exists for.
