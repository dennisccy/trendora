# Goal Session ops-hardening — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-19T15:19:32Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter touching `data_manager.py` `_do_backfill` / `_cadence_allowed_dates`
(build J-01's explicit-request override before J-05); any iter building J-04's logfile/memory-cap
layer in `scripts/start-backend.sh`.

## iter-1 — 2026-07-19T19:21:22Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter adding persisted/served numeric fields to `data_provider_runs` /
`JobProgress` / a run-summary or aggregate payload (J-05's `coverage_snapshot` finalize hooks next
cycle) — cover the interrupted/orphan-sweep and >sample-cap paths, not just the happy path.

## iter-2 — 2026-07-20T06:06:21Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter warming/serving an ingest-time cache keyed on a dataset-version fingerprint —
EVERY count-changing ingest path (fetch/expand/remove-data too) must refresh it or the sentinel must
do a cheap real existence check; verify the fetch-then-view path, not just backfill-then-view.

## iter-3 — 2026-07-20T11:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that first drives a new load pattern (heavy job / real fetch) through the
browser; any iter touching `app/engine/readiness.py`, `_refresh_ingest_aggregates`, or the shared
`HealthBadge`/`PreflightBanner`/`JobProgressPanel` status surfaces; any eval where the QA PASS and
the raw browser-qa verdict diverge.

## iter-4 — 2026-07-20T15:02:47Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future goal-evaluator reading browser-qa results for this repo while the merge
script stays unfixed — whenever the merged `ui-test-results.md` references a `## Notes` section it
does not contain, open the `.llm.md` sibling before scoring any target journey.

## iter-5 — 2026-07-20T22:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter measuring or asserting page-load performance budgets; any iter adding on-load API
calls to an already call-heavy page (Dashboard, Data Manager).

## iter-5 — 2026-07-20T22:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter whose measurement/backfill runs add rows to /scanner-runs or /api/runs; any
goal-evaluator triaging a required-still-passing deterministic-replay FAIL with no LLM-fallback adjudication.

## iter-6 — 2026-07-21T01:43:56Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter closing J-06 / touching a lazy-warmed derived cache (event_study_cache,
market_phase_cache, drawdown_expectations); any perf claim measured while a heavy pytest/ingest runs concurrently.

## iter-7 — 2026-07-21T08:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that adds work to `_refresh_ingest_aggregates` / the ingest finalize hook, or
any "warm-a-cache-earlier" change; any iter where the audit runs before browser-qa and asserts a required
journey is orthogonal to the diff — the evaluator must still weight the live browser evidence over the
orthogonality argument.

## iter-8 — 2026-07-21T23:53:18Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any backend-only iteration whose spec names browser journeys in TESTING REQUIREMENTS or
targets a regressed journey — check `browser_checks_run` and the existence of the evidence directory before
believing any completion claim.

## iter-8 — 2026-07-21T23:53:18Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration claiming an AG-8 memory/availability regression is closed, and any perf
measurement taken after host-guard settings changed.

## iter-8 — 2026-07-21T23:53:18Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration inserting a large block into an existing test file — re-read the function
boundaries on BOTH sides of the insertion point, and treat "a long-standing test still passes" as
suspicious when the diff touched its file.

## iter-9 — 2026-07-22T19:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where an audit/fix round lands product code AFTER the browser-qa step, and
any evaluation weighing operator/API evidence against a stale lane verdict.

## iter-9 — 2026-07-22T19:05:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration recording VmPeak/VmSize/RSS headroom against `server.memory_cap_mb`, and any
future J-05/AG-8 re-measurement as the price basis deepens.

## iter-10 — 2026-07-22T20:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration verifying crash/restart, orphan-sweep or checkpoint behaviour; any spec writing a
run-summary arithmetic assertion that must also hold for partial runs.

## iter-11 — 2026-07-22T21:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose verdict rests on browser-measured latency or on an anomaly
explained away as host contention; also any perf sweep, since the same log read reveals whether the
product's own ingest was running during the measurement.

## iter-11 — 2026-07-22T21:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose DoD says "record X in `reports/perf-budgets.md`" while X is
produced by browser-qa rather than by the developer.

## iter-12 — 2026-07-23T02:00:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose target is "measure-and-record" work against committed budgets
(`reports/perf-budgets.md`), and any evaluator tempted to accept a downstream agent's "may be scored passing"
when the recorded measurement breaches the acceptance metric.

## iter-13 — 2026-07-23T04:39:47Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter carrying an UNRESOLVED critical anti-goal on a "smaller blast radius than the
acknowledged incident" rationale — especially memory/availability bugs whose severity is load-dependent;
re-read logs/backend.log + the audit + closure for a worse-than-before manifestation before re-deferring.

## iter-14 — 2026-07-23T14:25:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that replaces a `.all()` fetch-and-release with a streamed/`yield_per` read on a
hot path shared by concurrent ingest writers — measure latency under concurrent load on the deep basis, not
just peak memory.

## iter-15 — 2026-07-23T18:00:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration proposing a wrapper/cache/concurrency fix validated on a synthetic fixture
before a deep-basis pass; any "the fix fully accounts for X" claim not yet reconciled against a live
full-scale measurement; future decomposers tempted to loop CONTINUE on an owner-owned direction decision.

## iter-16 — 2026-07-23T23:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a cache/precompute layer keyed on a derived identity (`asof_key`,
`dataset_version`, tenant, run id) — enumerate the ways the *identity* can move, not just the ways the
*value* can go stale, and make sure the live test exercises the identity-advancing shape, not only the
convenient one.

## iter-16 — 2026-07-23T23:22:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding user-facing status/progress/explanatory copy — verify each sentence
against the code that would have to be true for it, the same way a displayed number is verified against
the engine (AG-3's discipline, applied to prose).

## iter-17 — 2026-07-24T07:44:45Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter where a page/endpoint misses a committed `reports/perf-budgets.md` budget and the
mechanism is not yet pinned — check whether the diagnosis is blocked by missing telemetry (agent work)
before treating the residual as an owner budget-amendment decision.

## iter-18 — 2026-07-24T11:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter touching `apps/backend/app/api/backtest.py` / `mcp/tools.py` serving path or the
`resolved_forward_aggregate_evidence` resolver; more generally, any "read" endpoint that lazily
creates-once-on-first-view — instrument phases and test under a concurrent-ingest overlay, not pure reads.

## iter-19 — 2026-07-24T16:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter closing a "single root-cause" latency/perf journey on a page that has more than one on-load compute path — verify the OTHER first-touch paths (cold historical as-of, empty-store, first-of-day) with a live browser walk, not just the instrumented phase.

## iter-20 — 2026-07-24T19:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that moves a heavy compute to an in-process thread/daemon (verify concurrent-window budgets, not just the trigger); any evaluator facing "target fully achieved but no journey crossed" (weigh C.2 human-owned-blocker before defaulting to CONTINUE).

## iter-21 — 2026-07-25T03:25:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration verifying `/backtest` evidence states (`refreshing` / `not_yet_computed` /
`ready`), and any evaluator receiving screenshots whose md5s repeat across iterations — hash the evidence
directory before crediting a status change.

## iter-22 — 2026-07-25T08:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance rests on a timed window, poll series, or "no errors in the log"
claim — especially perf/latency measurement passes and any goal-closing evaluation.

## iter-23 — 2026-07-25T11:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration or evaluation that verifies `/backtest` refreshing/last-good evidence against
`forward_aggregate_cache`, or that audits AG-3 on a `generated_at`/`evidence_asof` label.

## iter-23 — 2026-07-25T11:05:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose DoD requires "verbatim" citation of a figure that exists at two
precisions (raw CSV vs rounded report); decomposers should name ONE canonical rendering.

## iter-24 — 2026-07-26T13:52:22Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration targeting a journey whose Acceptance block was auto-appended between the
`<!-- AUTO:journeys -->` markers, and any decomposer writing a DoD — enumerate EVERY Acceptance bullet,
especially the walkthrough/demo-manifest one, before declaring scope.

## iter-24 — 2026-07-26T13:52:22Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any future iteration whose acceptance state renders below the fold on this host, and any
evaluator weighing "no screenshot" against the absolute no-screenshot rail.

## iter-25 — 2026-07-26T16:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose lanes run alongside detached pytest/heavy jobs; any golden script whose
`expect` is a readiness/badge string; any change to `warmup.py` / `readiness.py` badge states.

## iter-25 — 2026-07-26T16:10:01Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any goal-proposer auto-appended journey (it inherits the session's standard Acceptance bullets
verbatim, including the `demo.sh --session-live` walkthrough clause).

## iter-26 — 2026-07-26T18:48:05Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose QA triggers a background-compute window or time-machines to a historical
as-of date — pick a date that ALREADY has a snapshot, and always diff `logs/backend.log` (ASGI errors,
`backtest_timing total_ms`) plus `scanner_runs`/`coverage_snapshot` after a browser lane runs, before scoring
its narrative as evidence.

## iter-27 — 2026-07-27T17:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reading a replay FAIL row; any change to `readiness.py` / `drift.py` /
`config.yaml`'s `readiness.drift.report_path`; anyone authoring or re-recording a golden journey script.

## iter-27 — 2026-07-27T17:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any change to `apps/backend/app/engine/forward_testing.py` (`_insert_run_forward_returns`,
`_backfill` — audit B2's cross-call residual is the same bug one level up); any new `except IntegrityError`
/ rollback-and-continue pattern anywhere in the engine.

## iter-28 — 2026-07-27T20:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that adds a `_DEFAULT_*_PATH` constant or a `config.yaml` path, writes or
repairs a journey-script `expect`, or budgets a "small" backend pytest selector.

## iter-28 — 2026-07-27T21:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose QA claims a concurrent-request or create-once result; any change to
`forward_testing._insert_run_forward_returns` / `data_manager._scanner_run_exists`.

## iter-29 — 2026-07-29T00:23:10Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that claims a memory/size bound — the test must assert the bound at the REAL
`load_config()` value against the REAL basis, not at a fixture-sized knob. Also: never reuse an existing
config knob for a new dimension whose UNIT differs (rows vs runs vs bytes) — give it its own key.

## iter-29 — 2026-07-29T00:23:10Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where a golden script is rewritten or a merged results file is regenerated —
the evaluator must diff the golden against its prior version and treat a REMOVED assertion as a status
signal, not housekeeping; QA reports that regenerate a merged file should preserve prior FAIL rows.

## iter-30 — 2026-07-29T03:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every evaluation that reads a merged `ui-test-results.md`; any iteration whose browser-QA
lane emits non-`UT-` test ids; any verdict that would rest on an audit-or-dev self-report rather than an
openable file.

## iter-30 — 2026-07-29T03:05:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration bounding memory in `forward_testing.py` / `research.py`; any plan whose
IN SCOPE lists containers to bound — check each one against the failing traceback frame before accepting
"partial scope, disclosed".

## iter-31 — 2026-07-29T07:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that measures page-load/TTI performance, writes to `reports/perf-budgets.md`,
touches `scripts/start-frontend.sh`, or reads a browser-QA "zero console errors" claim from a screenshot
carrying a dev-overlay error pill.

## iter-31 — 2026-07-29T07:05:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration claiming to bound an accumulator, pool, or return value; any DoD item worded
"proven by a dedicated unit test".

## iter-32 — 2026-07-29T09:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that changes a signature which a byte-identity / golden-output test also
calls — especially `apps/backend/app/engine/forward_testing.py` and
`apps/backend/tests/test_forward_testing_aggregates_streaming.py`.

## iter-32 — 2026-07-29T09:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration writing or rewriting a golden journey script (prefer structural/label
assertions over computed figures, or record the figure's provenance), and any iteration asserting a
memory bound (measure the named term in isolation, not the whole call).

## iter-33 — 2026-07-29T23:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that measures page-load/TTI or writes to `reports/perf-budgets.md`;
any iteration touching `scripts/start-frontend.sh` / `start-backend.sh` / `dev.sh`; and any spec
whose acceptance names a measurement — schedule the measurement expecting it to FIND something,
and leave fix-mode room for what it finds.

## iter-34 — 2026-07-30T01:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that proves a liveness/recovery property from a log excerpt, and any
evaluator scoring a drill (memory pressure, concurrency, crash recovery) whose evidence is a trimmed file
rather than a line range in the live log.

## iter-34 — 2026-07-30T01:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future drill that must induce a specific failure inside one loop of a multi-stage
finalize hook; check which stage runs first and whether its except clause is specific enough to attribute
the result.

## iter-35 — 2026-07-30T02:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose `.steps/` lacks `developer.done`; any evaluator reading a
browser-qa FAIL whose Expected column quotes the iteration spec rather than the journey text.

## iter-35 — 2026-07-30T02:05:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator carrying an anti-goal finding whose severity rationale contains a
"nothing is failing today"-style clause — re-test the clause, do not re-copy it.

## iter-35 — 2026-07-30T02:05:00Z (third entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any journey scored on a "the page loaded correctly" claim where the screenshot shows
a skeleton, spinner, or empty card.

## iter-36 — 2026-07-30T08:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator or decomposer reasoning about whether a predecessor iteration actually
built something; any future edit to the iter-35 lesson's wording.

## iter-36 — 2026-07-30T08:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any `ui-test-plan` containing backend-down / service-kill steps; any iteration whose
target journey needs a live backend after an error-state test.

## iter-36 — 2026-07-30T08:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration mixing frontend and backend work whose ui-impact documents scope the
backend half explicitly; any fix to the closure gate.

## iter-37 — 2026-07-30T12:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration measuring memory/performance on a path guarded by a stashed
reference, an attach/fallback context, or an early return; and any change that moves a resource
release from one stage's `finally` to a later stage's.

## iter-38 — 2026-07-30T16:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec asks one run to both measure a delta AND assert a failure-handling
path — split them into two runs, and state the cap/threshold each one needs before touching either.

## iter-38 — 2026-07-30T16:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reading `regression-replay-results.md` — check the failure screenshot for a
service-down page BEFORE treating a replay FAIL as a regression signal; and any work on
`demo_runner.py --mode verify` should make it probe `/api/health` first and report BLOCKED, not FAIL.

## iter-39 — 2026-07-31T02:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration running an induced-memory-pressure or cap-tightening drill; any iteration
touching `_missing_data_diagnostic` / `_compute_coverage_body` / the `_refresh_ingest_aggregates`
finalize tail; and any review of a "bounded query" claim in `apps/backend/app/engine/`.

## iter-39 — 2026-07-31T02:10:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `merge_ui_test_results.py` / `demo_runner.py` / `replay-lane.sh`,
and every goal-evaluator reading `reports/phase-*-ui-test-results.md`.

## iter-40 — 2026-07-31T03:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every iteration's browser-qa/replay precondition and ui-test-plan step; any
goal-evaluator reading a `SKIPPED` browser headline; and any framework work on
`goal-iter-lean.sh` / `replay-lane.sh` / the ui-test-designer.

## iter-40 — 2026-07-31T03:20:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any review of a "bounded read" claim in `apps/backend/app/engine/`; any
memory-pressure drill whose success criterion is the ABSENCE of a name in a traceback.

## iter-41 — 2026-07-31T06:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or trusting a journey-coverage gate; any iteration whose spec names
`Target journeys:` on a backend-only (`Frontend Present: no`) spec; any fix written to prevent a named
past incident.

## iter-42 — 2026-07-31T09:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that scores a journey `unknown`, and any evaluator choosing between
`failing` and `regressed` after a gap in verification.

## iter-42 — 2026-07-31T09:05:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** `apps/backend/app/engine/prices.py`, any `perf-budgets.md` memory claim, and any
iteration whose DoD contains a before/after resource measurement.

## iter-43 — 2026-08-03T19:30:00Z

**Verdict:** ESCALATE
**Lesson:** Raising the memory ceiling fixed the failure it was aimed at and revealed a second,
independent one underneath: the same heavy warm that used to die of `MemoryError` at 6144 MB now
stalls at `horizons_done: 0/5` with 67.6% of the 8192 MB cap free, and because
`incredible_auto_dev/scripts/start-backend.sh:95` execs uvicorn with no
`--timeout-graceful-shutdown`, a single stuck in-flight task holds the whole process in
`Waiting for background tasks to complete` forever — the port stops listening while the process
stays alive at 90%+ CPU, which reads as "server crashed" from outside but is actually "server
politely waiting". Fixing a resource ceiling never proves the work terminates; measure completion,
not just headroom.
**Applies to:** any iter that raises a resource cap and reads the result as "the problem is solved";
any iter touching `compute_forward_aggregates` / the ingest finalize warm; any launcher change
(`scripts/start-backend.sh`, `dev.sh`) — a long-running background task needs a shutdown deadline.

## iter-43 — 2026-08-03T19:30:01Z

**Verdict:** ESCALATE
**Lesson:** A guard written for a specific past incident must be keyed to that incident's whole
exception set, not its headline exception. This iteration's thread-launch guard caught
`RuntimeError("can't start new thread")` — and iter-42's log contained `MemoryError` from the SAME
`Thread.start()` path side by side with it (CPython's `_start_new_thread` has two exits under one
memory ceiling). Only a live `MemoryError` parametrization, not a code reading, showed the job still
orphaned at `running` with no run-history row at all. Reading the incident's own log for every
exception it produced would have taken a minute.
**Applies to:** any iter shipping a guard/except clause written against a named past failure; any
`threading.Thread(...).start()` site (`warmup.start_warmup`, `forward_testing.py:1691` are the two
still unguarded).

## iter-44 — 2026-08-03T22:10:00Z

**Verdict:** ESCALATE
**Lesson:** A timeout enforced BY the thing that hangs is not a timeout. This iteration correctly
wired uvicorn's `--timeout-graceful-shutdown` (a genuine, previously-unenforced `ServerOpsCfg` gap)
and live-verified it on `/proc/<pid>/cmdline` — then the same build sat 20m51s unreachable and needed
`SIGKILL`, because that flag is enforced by the asyncio event loop and the loop itself was wedged
(`logs/backend.log` shows NO shutdown output at all for that process: a caught `MemoryError` in
`evidence.py`, then straight to the next launch banner). Any deadline that must survive a total wedge
has to live in a different process — the launcher backgrounding the server and owning its own SIGKILL
escalation, or a supervisor.
**Applies to:** any iter adding a timeout/watchdog/health-deadline to a process that can freeze; any
launcher change (`scripts/start-backend.sh`, `dev.sh`); any claim that a config flag "closes" an
availability failure mode — ask first which component enforces it.

## iter-44 — 2026-08-03T22:10:01Z

**Verdict:** ESCALATE
**Lesson:** A memory-pressure guard proven by ONE green run is not proven. The audit found and fixed
two real `MemoryError` escapes in `_refresh_ingest_aggregates` and cited a single
`pytest tests/test_ingest_finalize_memory_pressure.py -q → 2 passed`; the reviewer ran the identical
test twice back-to-back and got 1 failed / 1 passed, then 2 passed — exposing a THIRD escape
(`logger.exception()` itself allocating under the 750,000 KB cap). Under an exhausted cap the failing
site moves between runs, so the pass/fail signal is inherently flaky and a single run mostly measures
luck.
**Applies to:** any iter whose proof is a test that runs under a tightened `ulimit -v` /
`memory_cap_mb` (`test_ingest_finalize_memory_pressure.py` and friends) — run it 3-5x consecutively
before calling the contract closed, and treat a new flake as a new escape to trace, never a number to
tune.

## iter-45 — 2026-08-04T04:30:00Z

**Verdict:** ESCALATE
**Lesson:** A live thread dump names where a thread is BLOCKED, not necessarily what is KILLING the
process. iter-44's SIGUSR1 dump named `_membership_timeline`'s O(dates × pool) storm; iter-45 fixed
that storm correctly and the backend still died — because the memory pressure was arriving from a
different, request-serving path (`evidence.py:168` → `forward_testing.py:2343` / `research.py:777`,
16 of the 24 wedge-window `MemoryError`s). Under memory exhaustion the *slowest* stack and the
*allocating* stack are usually different stacks; pair any stack dump with a per-site allocation
count from the same window before choosing what to fix.
**Applies to:** any iteration that picks its target from a stack/thread dump taken during a freeze —
especially `apps/backend/app/engine/` memory work.

## iter-45 — 2026-08-04T04:30:00Z

**Verdict:** ESCALATE
**Lesson:** Check that the live data basis can actually SATISFY a fix's precondition before
committing an iteration to that fix. iter-45's append-forward fast path only fires when the ingested
date is at or after every cached date, but `GET /api/data` reports `gap_last = 2019-02-25` against a
latest snapshot of `2026-07-31` and the seed's data horizon IS that latest snapshot — so no
append-forward target can exist in this database, AG-9 forbids fetching one, and the mechanism
finished the iteration with zero live evidence (`grep` for it over 173k log lines → 0 matches). One
`gap_last`-vs-latest-snapshot query at decompose time would have caught this before the round was
spent.
**Applies to:** any iteration whose fix is scoped to a data shape (append-forward, latest-only,
same-version) — verify the live DB contains an instance of that shape during decomposition.

## iter-46 — 2026-08-04T09:15:00Z

**Verdict:** ESCALATE
**Lesson:** The deterministic replay lane has been scoring J-01/J-03 `passing` on text that
pre-existing rows already satisfy. `journey-scripts/J-01.json` step 5 asserts the string
"2 non-trading" is present on `/data`, and Run History persists every past run — so the assertion
passes whether or not the job it just submitted ever finished. Worse, `data_provider_runs` contains
**no row at all** for 01:23-01:24Z when the iter-45 replay ran, i.e. its `fill`+`Start` never created
a job (the iter-46 LLM tester independently found that plain `.value =` assignment does not update
React state on those date inputs). A golden script that asserts page-wide text on a page with
persistent history is a null test.
**Applies to:** any iteration relying on `demo_runner.py --mode verify` for J-01/J-03 (or any journey
whose acceptance text also appears in a persisted history panel); any golden-script authoring — assert
against the NEW run's own row/testid, never page-wide text.

## iter-46 — 2026-08-04T09:15:00Z

**Verdict:** ESCALATE
**Lesson:** A QA-fix or audit-fix pass that lands after the browser lane silently voids the entire
lane: this iteration's `warmup.py` (06:17Z) and `data_manager.py` (08:38Z) both changed the exact code
paths whose rows had failed at 05:49Z, so not one of the eight journeys could be scored on this
round's own work. Three independent places recorded the problem (`status.json`'s
`next_action: rerun_browser_lane_then_audit`, audit T1, review MINOR #2) and the iteration still ended
without re-running it — the note is not self-executing.
**Applies to:** any iteration that enters fix-mode or audit-fix after browser-qa has run; the
orchestrator should treat "product code changed after `ui-test-results.md` was written" as a hard
re-run trigger, not an advisory note.

## iter-47 — 2026-08-04T17:30:00Z

**Verdict:** ESCALATE
**Lesson:** A golden replay script can be a null test in a way that is invisible from its PASS row —
read the script, not the verdict. The six scripts that produced this round's "6/6 PASS" include one
with a SINGLE step (J-08: load `/backtest`, assert the text "Forward-tested evidence") and one that
clicks Start and then navigates straight to a PRE-EXISTING run page (J-05 → `/scanner-runs/1882`),
so both pass on a build where the feature is entirely broken. `git show HEAD:runs/.../journey-scripts/<J>.json`
costs one command and settles it. Second half of the same lesson: a rebuilt script that is never
executed buys nothing — this round rebuilt five goldens at 15:46-16:05 and ran none of them.
**Applies to:** any iteration that reads a `regression-replay-results.md` PASS as journey evidence,
and any iteration whose spec mandates re-running a lane after a fix pass (the TC-7 shape) — check
the results-file mtime against the newest product-code mtime before scoring, because iter-46 and
iter-47 both ended with every lane naming the requirement and nobody executing it.


## iter-48 — 2026-08-05T02:45:00Z

**Verdict:** ESCALATE
**Lesson:** A finalize-tail phase whose cost swings **102 s → 153 s → 1,334 s across three runs of
the same work** cannot be characterised from two samples: the dev handoff and `perf-budgets.md` both
attributed J-05's remaining non-termination to `drawdown_expectations_warm` alone, written from the
first two runs, and the third run showed `forward_aggregates_warm` ALONE exceeding TC-1's whole
1,200 s budget (audit B2). The instrumentation this iteration added to
`apps/backend/app/engine/data_manager.py`'s finalize tail is what made the spread visible — the
lesson is to read every run's phase table before naming a bottleneck, not the first two.
**Applies to:** any iteration attributing a wall-clock blocker to one phase of a multi-phase job —
especially `_refresh_ingest_aggregates`'s tail.

## iter-48 — 2026-08-05T02:45:00Z (second entry)

**Verdict:** ESCALATE
**Lesson:** The cure for the session's null-test problem is not "read the golden script" but "read
the ROW the golden created". J-01's and J-03's replay PASSes became trustworthy only when
`data_provider_runs` ids 305/306/307 turned out to exist at the replay's own timestamps with exactly
the counts the scripts assert. Conversely J-06's PASS survived a golden-content read and still had
to be declined, because `logs/backend.log` recorded two `MemoryError`s on `/research/regime-lab` —
the route its own step 11 loads — inside the same window. Text assertions and script content are
both satisfiable without the behaviour; a side-effect row or a log line is not.
**Applies to:** any evaluator scoring a journey `passing` on a deterministic-replay row; any
iteration rebuilding a golden for a journey that writes to the DB.
