# goal-ops-hardening-iter-15 Execution Plan

## Context (read before building)

**Continuation iteration, not REGRESSION-recovery.** iter-14 closed the critical AG-8 defect (unbounded
ORM reads in `compute_forward_aggregates` behind two full-backend outages) with a byte-identity-proven,
column-projected/`yield_per`-streamed rewrite — 61.8% VmPeak margin, 250/250 health 200 on the first
successful full-deep-basis 5-horizon warm this basis size has ever completed. Browser-qa's OWN regression
lane over that same rewritten path (UT-04) then found `GET /api/backtest`'s cache-miss resolving in
**211.8s** (measured via the browser's Resource Timing API) when it lands concurrently with the ingest
finalize warm — honest (no crash, no frozen frame, `/api/health` stayed green) but a ~140x overrun of the
committed ≤1.5s budget. Both iter-14's evaluator (scored J-06/J-07 `partial`, not `passing`, specifically
because of this finding) and its auditor (F1) named this THE next item. This iteration IS that fix.

**Goal alignment check:** no drift. `docs/goal.md` J-06/J-07 are both pre-existing Must-have journeys;
per the phase spec's own rubric this is rule-3 "unblocker" — the ONLY remaining agent-tractable
substantive item standing between them and `passing`. One interpretation call already made and logged
(not this iteration's to re-litigate, `assumptions.md` iter-15): goal.md's literal text does not
unambiguously require `/backtest`'s OWN response time to stay in budget during a concurrent warm — the
decomposer explicitly followed iter-14's evaluator's reading (UT-04 blocks BOTH J-06 and J-07) rather than
treating it as disclosed-but-out-of-contract. Build against that reading; do not re-derive it.

**Root-cause candidates — confirmed in live code ahead of this dispatch (none prescribed; determine the
dominant one(s) with evidence, per iter-9's carried lesson: a plausible story is not a substitute for a
measurement):**
- **(a) No de-duplication in `forward_aggregates_cached`** (`forward_testing.py:987-1057`) — a cache MISS
  (`hit is None`, ~line 1031) falls straight through to `payload = compute_forward_aggregates(...)`
  (line 1035) with no lock, in-flight marker, or memoization keyed by `(horizon, asof_key,
  dataset_version)`. Confirmed by direct read — this is real today, not a hypothesis.
- **(b) Single uvicorn process, no `--workers`** — `scripts/start-backend.sh:95` execs
  `uvicorn main:app` and `scripts/dev.sh:78` execs `uvicorn main:app --reload ...`; neither passes
  `--workers` (confirmed by grep across both scripts and `main.py`). `GET /api/backtest` is a sync `def`
  handler (`app/api/backtest.py:49`), so Starlette runs it on the process's request threadpool — the SAME
  process and GIL the ingest finalize warm's own thread uses. **Compounding detail worth flagging to the
  developer:** the finalize warm (`data_manager.py:3216-3241`) loops sequentially over all 5 configured
  horizons calling `forward_aggregates_cached(session, h, cfg, as_of=latest_run_date)`, and
  `GET /api/backtest` (`backtest.py:71-74`) does the exact same 5-horizon dict comprehension for
  `run.asof_date`. When a request lands during a backfill of the current latest date, both loops can
  target the SAME 5 keys at once — combined with (a), that is up to **10 redundant concurrent heavy
  aggregation passes** over the same data, not 2, which plausibly compounds (b) and (c) into a number this
  large.
- **(c) WAL-mode long-held read transaction** — `app/db.py`'s `_apply_sqlite_pragmas` sets
  `journal_mode=WAL` (config default, `config.py:1865`, confirmed live via `PRAGMA journal_mode` per the
  spec). `compute_forward_aggregates`'s two `yield_per`-streamed selects (`forward_testing.py:837-853,
  877-885`) hold their scan open across the full horizon-partition iteration. Audit F1's hypothesis: this
  may hold a read snapshot open longer in wall-clock time than the old fast `.all()` fetch-and-release did,
  overlapping more WAL growth from the warm/request's own concurrent writes (`JobProgress` ticks,
  `ForwardAggregateCache` upserts) — plausible, unverified.
- `database.pool_size=10` / `max_overflow=20` (`config.py:~1897-1898`) — connection count is not the
  binding constraint; GIL and/or WAL contention are the live candidates.

**Escalation discipline (spec's own words, do not soften):** if the investigation concludes the latency is
a hard architectural single-process/GIL limit that a targeted fix cannot meaningfully reduce, name that
plainly as a scoped finding for the evaluator/owner — do NOT reach for `uvicorn --workers`/multiprocessing
as a workaround (out of scope — the IN SCOPE section confines the fix to `forward_aggregates_cached`
and/or `app.db`'s session/WAL config, not the launch scripts or process model) and do NOT silently decide
"accept + add an affordance" — that is an owner call for iter-16, not this iteration's to make.

**Lessons applied (carry forward verbatim from the spec):** iter-14 — "a memory fix and a lock-contention
fix are different problems... a passing byte-identity/VmPeak proof does not substitute for a fresh
concurrent-load timing measurement." iter-11 — cross-read `logs/backend.log` and `logs/hwmon/hwmon.csv`
for the TC-4 measurement window before attributing any remaining slowness to "ambient load." iter-9 — a
"concurrency overhead is expected and acceptable" narrative is not a substitute for the recorded number;
if post-fix latency is still elevated, record WARN, do not rationalize it away.

**`blueprint.md` is already partially updated for this iteration** (`runs/goal-session-ops-hardening/
state/blueprint.md:139-158`) — the decomposer pre-wrote the additive "iter-15 update" paragraph describing
this iteration's intended scope. The developer's job is to confirm it stays accurate once the actual fix
mechanism is known (e.g. if the fix does touch `app.db`, or if the outcome is an escalation rather than a
close), not to author it from scratch.

## PUMP NOTE constraints (operator, this dispatch) — binding on this plan

- Services are **UP** (backend :8255, frontend :3255, host idle Tctl 42°C) as of this dispatch — but the
  TC-4/5/6 heavy pass needs a **fresh** restart regardless: the spec's own NOTES state "since TC-4 needs a
  clean, freshly-started process to correctly attribute timing/VmPeak to THIS iteration's build, a restart
  is required... do not reuse the currently-running pre-fix process's numbers."
- Agents cannot start/stop services this session (subagent-resume broken) — write every restart/monitor
  step as **operator-performed**: the operator restarts/monitors and reports console output, pids, and
  timestamps verbatim; the developer records that operator-provided output with attribution in
  `reports/perf-budgets.md` — never fabricate or silently omit a number.
- No full pytest suite — targeted files only, host-guard-confined (`taskset -c 0-3,8-11`;
  `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS=4`). `loaded_engine`-
  fixture files legitimately run ~80 minutes — not a hang, do not run them casually.
- The TC-4/5/6 full-deep-basis pass is AG-10-class: exactly ONE operator-supervised pass, cooled host,
  sampler + thermal watchdog armed — mirrors the iter-3/8/9/14 protocol. Standard path: developer/reviewer
  runs it directly under confinement if the environment allows; fallback (this session's standing
  constraint): operator performs it and reports verbatim for attributed transcription.
- Before running any test or command that writes temp files:
  `export TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-har-383e2250.3543639"`.

## What to Build

- **Root-cause determination** for UT-04's 211.8s finding, naming which of the three candidates above
  (or a combination) actually dominates, with evidence — not adopted as the first plausible story.
- **A targeted concurrency-safety fix**, scoped ONLY to `forward_aggregates_cached`
  (`apps/backend/app/engine/forward_testing.py:987-1057`) and/or `app.db`'s session/connection/WAL
  configuration:
  - Most directly indicated by candidate (a): an in-process **single-flight / de-dup mechanism** so that
    N concurrent same-key MISSes invoke `compute_forward_aggregates` **exactly once** for that key —
    concurrent callers wait for (or otherwise reuse) the one in-flight computation's result instead of each
    redundantly recomputing. Must handle the failure path cleanly (TC-8): if the owning computation
    raises, a waiting caller does not hang indefinitely — it either gets a clean isolated error within a
    bounded time or independently recomputes and returns correctly.
  - If evidence also implicates (c), a scoped `app.db` session/WAL adjustment (e.g. transaction-scope or
    busy-timeout tuning for the streamed read) — conditional on what the investigation actually shows, not
    prescribed here.
  - `compute_forward_aggregates` (`forward_testing.py:781-984`) stays byte-identical — same signature,
    same columns read, same streamed pattern from iter-14 (binding "do not redo"); all three call sites
    (`app/api/backtest.py:72`, `app/mcp/tools.py:205`, `data_manager.py:3230`) keep calling it unchanged.
- **Test additions** (TC-1, TC-2, TC-8 — see Key Test Scenarios) proving the de-dup holds, bounding the
  concurrent-vs-baseline wall-clock ratio, and proving the failure path never deadlocks a waiting caller.
- **Re-confirmation of byte-identity** (TC-3): the existing 32-test suite in
  `test_forward_testing_aggregates_streaming.py` continues to pass unmodified (since
  `compute_forward_aggregates` itself is untouched); extend it only if the fix's wrapper-level behavior
  needs its own byte-identity assertion beyond what TC-1's "all N callers return identical payloads"
  already covers.
- **ONE operator-supervised, host-guard-confined, full-deep-basis reproduction** of the exact iter-14 UT-04
  trigger shape (TC-4/5/6): fresh backend start under `scripts/start-backend.sh` against the current DB
  (`scanner_results` 775,094+ rows, `forward_returns` 3,935,930+ rows), the ingest finalize warm (all 5
  horizons) running concurrently with a live `GET /api/backtest` cache-miss request; record the resolving
  request's wall-clock in `reports/perf-budgets.md`, PASS (≤1.5s) or WARN (measured number). Same pass:
  spot-check `/stocks`, `/sectors`, `/scanner-runs`, `/evidence` under the concurrent warm (TC-5, honest
  PASS/WARN, never blank/frozen); poll `GET /api/health` at 1Hz throughout (TC-6, no wedge).
- **Dev handoff** at `docs/handoffs/goal-ops-hardening-iter-15-dev.md`.

## Agents Required

- backend-data: yes -- the root-cause investigation; the targeted `forward_aggregates_cached`/`app.db`
  fix; the TC-1/TC-2/TC-8 test additions; the byte-identity re-confirmation; coordinating (with operator
  fallback) the one authorized TC-4/5/6 heavy pass and transcribing its results with attribution; the
  `reports/perf-budgets.md` section; the dev handoff.
- frontend-ux: no -- `docs/goal.md`/this spec both state no frontend file is touched
  (`Frontend Present: no`); the observable difference (if the fix holds) is a faster `/backtest` response
  under load, not a new UI feature, display, action, or surface.

## Frontend Present

no

Note for the QA stage: even with no frontend file touched, TESTING REQUIREMENTS names four browser
journeys (J-01, J-03, J-04, J-05) for required-still-passing regression replay, plus J-06/J-07 verified via
the operator-supervised pass's recorded numbers — the framework fix (commit `d0799803`, verified) stops
`Frontend Present: no` from suppressing the browser-qa lane whenever TESTING REQUIREMENTS names journeys.
Browser-qa MUST still run this iteration.

## Out of Scope (do not build)

- The `demo.sh ops-hardening --session-live` walkthrough — already executed by the operator post-iter-14
  (`runs/goal-ops-hardening-iter-14/operator-session-live-walkthrough.md`); the evaluator weighs it
  directly, no re-run.
- TC-6's (iter-14 numbering) live induced-memory-pressure sufficiency call — already an evaluator/owner
  judgment made in iter-14; not re-litigated.
- `HOST_GUARD_REQUIRE_MARKERS` — resolved iter-14 (commit `e5624010`); no further action.
- A `/backtest` elapsed-time/progress affordance — deferred; only relevant if this iteration's fix does
  not materially close the latency gap (owner/evaluator call for iter-16 if so).
- Reconciling the per-horizon heartbeat cadence sizing (audit F2 / UT-10) — carried, non-blocking; likely
  shrinks as a side effect of this iteration's fix; revisit only if it does not.
- Raising `server.memory_cap_mb` / `malloc_arena_max`, or touching `main.py`, `app/api/health.py`,
  `app/engine/readiness.py`, `app/engine/warmup.py` — binding "do not redo."
- **Any uvicorn multi-process/`--workers` change, or other launch-script/process-model change** — even if
  the investigation finds GIL contention dominant, the fix must stay inside `forward_aggregates_cached`/
  `app.db`; a process-model change is exactly the "bigger redesign" the spec's escalation flag reserves
  for an explicit owner call, not a developer-chosen workaround.
- Touching `scripts/automation/*` or the dead `apps/frontend/components/major-indexes-card.tsx`.
- Re-measuring the 10 already-in-budget J-06 pages under IDLE conditions, or re-deriving the boot budget —
  settled iter-9/11; this iteration's 4-page spot-check is a NEW check under CONCURRENT load, not a repeat.
- A full pytest suite run — targeted, host-guard-confined tests only.
- Any change to `compute_forward_aggregates`'s columns, signature, or return shape.
- Repeating the full-deep-basis heavy measurement pass beyond the ONE authorized run.
- Any new UI page, nav entry, or displayed value.

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` -- modify `forward_aggregates_cached` only (concurrency-
  safety/de-dup mechanism); `compute_forward_aggregates` byte-identical (no signature/column/behavior
  change).
- `apps/backend/app/db.py` -- **conditional**: touch only if the root-cause evidence implicates
  session/connection/WAL handling; document the decision either way (why touched, or why not needed) in
  the dev handoff.
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` -- extend if the fix needs a new
  wrapper-level byte-identity assertion; otherwise confirm the existing 32 tests still pass unmodified
  (TC-3).
- `apps/backend/tests/test_forward_testing_concurrency.py` (existing, iter-14) -- add new tests for TC-1
  (same-key concurrent-MISS de-dup), TC-2 (concurrent-write-during-read ratio), and TC-8 (failure-path/
  no-deadlock). **Naming note:** this file already has iter-14 tests literally named
  `test_tc3_...`/`test_tc4_...` referring to iter-14's OWN TC-3/TC-4 (real memory-cap induction / concurrent-
  caller). This iteration's TC-1/TC-2/TC-8 are a DIFFERENT numbering scheme (per THIS phase spec) — name
  the new tests to avoid ambiguity (e.g. a module-level docstring banner separating the two iterations'
  test groups, and/or an `iter15_`-prefixed or descriptively-named test function), not reused `test_tc1_`/
  `test_tc2_` names that could read as continuing iter-14's own TC numbering.
- `reports/perf-budgets.md` -- **the original UT-04 211.8s finding is NOT yet transcribed into this file**
  (confirmed by a direct search — it currently exists only in
  `reports/phase-goal-ops-hardening-iter-14-ux-regression.md:61,118-122`). This iteration's developer must
  first transcribe that original finding into a new dated section here (with attribution to the iter-14
  ux-regression report), THEN append this iteration's own TC-4/5/6 re-measurement immediately below it in
  the SAME section, per the spec's "immediately below the original 211.8s finding" instruction.
- `docs/handoffs/goal-ops-hardening-iter-15-dev.md` -- new dev handoff.
- `runs/goal-session-ops-hardening/state/blueprint.md` -- the iter-15 paragraph (lines 139-158) is already
  drafted; confirm/amend it once the actual fix mechanism and outcome are known (light-touch, not a
  rewrite).

No file under `apps/frontend/` should appear in the diff.

## Implementation notes (advisory, not prescriptive)

- **Single-flight pattern**: a module-level `dict[key -> in-flight marker]` guarded by a `threading.Lock`
  (or `threading.Condition`) is the classic "compute-once, others wait" idiom for this shape. Clean up the
  in-flight marker in a `finally` on BOTH success and failure so a crashed computation does not permanently
  poison the key for the next caller, and so a waiting caller can time out cleanly (TC-8) rather than
  hanging forever. Key on the SAME `(horizon, asof_key, dataset_version)` tuple `forward_aggregates_cached`
  already uses for its cache lookup — no new identity scheme.
- **TC-1's call-count instrumentation**: a monkeypatch/wrapper counter around `compute_forward_aggregates`
  (or counted at its call site) is a reasonable, minimal-invasiveness way to assert "invoked exactly once"
  without a production code change purely for testability.
- **TC-2's fixture sizing is a distinct empirical task from TC-3's/iter-14's TC-3** (that one was
  memory-sized, not time-sized): size a fixture so a SINGLE uncontended `compute_forward_aggregates` call
  measures **at least 1.0s wall-clock** — check whether the existing 60,000-row memory-pressure fixture
  already clears this bar before building a second, larger one. The background writer thread should mirror
  ingest-warm write activity (inserting new rows or updating `JobProgress`), per the spec's own TC-2 text.
- **Root-cause attribution discipline (iter-11's lesson)**: cross-read `logs/backend.log` and
  `logs/hwmon/hwmon.csv` for the TC-4 measurement window before attributing any remaining slowness to
  "ambient load."
- The finalize warm's call site (`data_manager.py:3216-3241`) and `/api/backtest`'s own 5-horizon
  comprehension (`backtest.py:71-74`) are both already-existing, unchanged call shapes — useful context for
  reasoning about the fix, not something to modify.

## Key Test Scenarios

- TC-1: given N≥5 concurrent callers of `forward_aggregates_cached` requesting the SAME never-yet-cached
  `(horizon, asof_key, dataset_version)` key, `compute_forward_aggregates`'s row-scan is invoked **exactly
  once** for that key (call-count instrumentation), and all N callers return byte-identical payloads.
- TC-2: given a fixture where a single uncontended `compute_forward_aggregates` call measures ≥1.0s, and a
  background thread issuing repeated committed writes throughout that call (mirroring ingest-warm write
  activity), the concurrent-vs-baseline wall-clock ratio is recorded and asserted ≤5.0x (a smoke guard; TC-4
  is the full-scale proof).
- TC-3: the existing pinned byte-identity suite (32 tests, all 5 configured horizons x `{as_of=None,
  historical as_of}` x 3 batch sizes) remains `==` the pre-rewrite reference, unchanged from iter-14.
- TC-4: one operator-supervised, fresh-started, host-guard-confined pass against the current full deep
  basis reproduces the exact UT-04 trigger (ingest finalize warm across all 5 horizons concurrent with a
  live `GET /api/backtest` cache-miss); the resolving request's wall-clock is recorded in
  `reports/perf-budgets.md` immediately below the transcribed 211.8s finding, labeled PASS (≤1.5s) or WARN
  (measured number).
- TC-5: same pass — `/stocks`, `/sectors`, `/scanner-runs`, `/evidence` loaded (or their on-load endpoints
  called) while the warm is running; each recorded PASS (in its own committed budget) or a named WARN;
  none renders blank or frozen.
- TC-6: same pass — `GET /api/health` polled at 1Hz throughout; every poll HTTP 200 within budget, no
  wedge, no restart needed.
- TC-7: J-01/J-03/J-04/J-05 (required-still-passing) all re-verify PASS via deterministic golden replay or
  LLM fallback — none regresses from passing to failing.
- TC-8: given a same-key MISS whose in-flight computation mechanism fails with an exception, a second
  concurrent same-key caller does not block past a bounded timeout (e.g. 45s, mirroring this test file's
  existing `BOUNDED_TIMEOUT_S`) — it either raises a clean isolated error or independently computes and
  returns a correct payload.
- Coherence: zero second producer/endpoint for the touched Data Contract row —
  `compute_forward_aggregates`/`GET /api/backtest` (+ MCP tool + ingest warm) stay the sole
  producer/serving paths.
- Regression floor: targeted backend subset only, host-guard-confined; zero new failures beyond the
  pre-existing, unrelated `tests/test_db.py::test_create_all_produces_expected_tables` failure; no full
  pytest suite run.

## Environment Note (for the developer agent)

Before running any test or command that writes temp files:
`export TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-har-383e2250.3543639"`.
Services are UP as of this dispatch (backend :8255, frontend :3255) but the TC-4/5/6 pass needs a FRESH
restart regardless (do not reuse the currently-running pre-fix process's numbers) — request an operator
restart (with recorded pid/timestamp) for that pass rather than attempting to start/stop a service
directly.
