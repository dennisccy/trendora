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

## iter-43 — 2026-08-03T19:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that raises a resource cap and reads the result as "the problem is solved";
any iter touching `compute_forward_aggregates` / the ingest finalize warm; any launcher change
(`scripts/start-backend.sh`, `dev.sh`) — a long-running background task needs a shutdown deadline.

## iter-43 — 2026-08-03T19:30:01Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter shipping a guard/except clause written against a named past failure; any
`threading.Thread(...).start()` site (`warmup.start_warmup`, `forward_testing.py:1691` are the two
still unguarded).

## iter-44 — 2026-08-03T22:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter adding a timeout/watchdog/health-deadline to a process that can freeze; any
launcher change (`scripts/start-backend.sh`, `dev.sh`); any claim that a config flag "closes" an
availability failure mode — ask first which component enforces it.

## iter-44 — 2026-08-03T22:10:01Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter whose proof is a test that runs under a tightened `ulimit -v` /
`memory_cap_mb` (`test_ingest_finalize_memory_pressure.py` and friends) — run it 3-5x consecutively
before calling the contract closed, and treat a new flake as a new escape to trace, never a number to
tune.

## iter-45 — 2026-08-04T04:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that picks its target from a stack/thread dump taken during a freeze —
especially `apps/backend/app/engine/` memory work.

## iter-45 — 2026-08-04T04:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose fix is scoped to a data shape (append-forward, latest-only,
same-version) — verify the live DB contains an instance of that shape during decomposition.

## iter-46 — 2026-08-04T09:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration relying on `demo_runner.py --mode verify` for J-01/J-03 (or any journey
whose acceptance text also appears in a persisted history panel); any golden-script authoring — assert
against the NEW run's own row/testid, never page-wide text.

## iter-46 — 2026-08-04T09:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that enters fix-mode or audit-fix after browser-qa has run; the
orchestrator should treat "product code changed after `ui-test-results.md` was written" as a hard
re-run trigger, not an advisory note.

## iter-47 — 2026-08-04T17:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that reads a `regression-replay-results.md` PASS as journey evidence,
and any iteration whose spec mandates re-running a lane after a fix pass (the TC-7 shape) — check
the results-file mtime against the newest product-code mtime before scoring, because iter-46 and
iter-47 both ended with every lane naming the requirement and nobody executing it.

## iter-48 — 2026-08-05T02:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration attributing a wall-clock blocker to one phase of a multi-phase job —
especially `_refresh_ingest_aggregates`'s tail.

## iter-48 — 2026-08-05T02:45:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator scoring a journey `passing` on a deterministic-replay row; any
iteration rebuilding a golden for a journey that writes to the DB.

## iter-49 — 2026-08-05T12:50:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reading `data_manager` / `warmup` finalize-or-warm phase logs, and any
agent attributing a MemoryError or timing outlier to a specific loop — always confirm the frame, not
the message.

## iter-49 — 2026-08-05T12:50:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance is a wall-clock or memory bound (J-05, J-07, and any
future perf-budget work) — require at least one measurement through the app's own pages, under
concurrent reads, before the journey moves up.

## iter-50 — 2026-08-06T07:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter scoring J-05/J-06/J-07 or any memory-bounding work; any evaluator or auditor
citing a `logs/backend.log` MemoryError count.

## iter-50 — 2026-08-06T07:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter targeting J-07's health-poll ceiling, or proposing a memory bound as the
remedy for a latency/availability journey.

## iter-51 — 2026-08-07T10:05:11Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter scoring J-07/J-05 responsiveness, or reading `logs/backend.log` for outage,
wedge, or latency evidence.

## iter-51 — 2026-08-07T10:05:11Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any full-depth iter whose spec carries the TC-8 lane-last sequencing rule.

## iter-52 — 2026-08-08T04:34:46Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration scoring a journey off a golden `expect.text` assertion, and any
log-based availability claim about `apps/backend/` (`ui-test-results.md` rows, `perf-budgets.md`
drill addenda). Assert a value the endpoint must have produced, not a heading the shell renders.

## iter-52 — 2026-08-08T04:34:46Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** every full-depth iteration in this session; any spec author restating TC-8/TC-9;
anyone diagnosing why a round ends `blocked` at `audit_qa_failed` with `browser_checks_run: false`.

## iter-53 — 2026-08-08T09:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec depends on stage ordering (browser/replay lane vs audit-fix vs
review), and any recurring process failure that has survived two or more "try harder" rounds — encode it
as a DoD/TC item instead of a reminder.

## iter-53 — 2026-08-08T09:55:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration bounding a fetch/scan/window (`bars_asof` -> `bars_asof_window`,
chunking, `LIMIT` pushdown) — check the bound's unit against the consumer's unit, and require the
byte-identity test to compare against the ORIGINAL implementation, never against another instance of
the new one.

## iter-54 — 2026-08-09T23:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter touching `data_manager._refresh_ingest_aggregates` / `forward_testing`'s warm
loop, and any lane or evaluator scoring an ingest run from `aggregates_refreshed` / `status`.

## iter-54 (second entry) — 2026-08-09T23:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any browser-qa or golden script asserting J-05 step 4 / J-07 step 2, and any iteration
that plans to replace the 1 Hz concurrent drill with in-turn browser polling.

## iter-54 (third entry) — 2026-08-09T23:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every golden in `runs/goal-session-ops-hardening/journey-scripts/` whose first assertion
reads a readiness/health-derived attribute (J-04.json step 2, J-07.json step 2).

## iter-55 — 2026-08-10T03:00:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any golden script whose assertions depend on a one-shot state the script itself
changes (single-use dates, "first time" flags, one-off job outcomes) — and any evaluator scoring a
replay FAIL on such a journey.

## iter-55 (second entry) — 2026-08-10T03:00:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose replay lane runs more than once (developer pass + lane pass),
and any evaluator reading a results table that disagrees with a dev handoff or review report.

## iter-56 — 2026-08-10T06:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or changing an ingest-warmed cache under
`app/engine/data_manager.py` / `app/engine/indexes.py` (coverage_snapshot, membership_timeline,
index_series, availability_heatmap, factor_lab_all), and any browser check that only ever loads a page
on a warm idle system.

## iter-56 — 2026-08-10T06:30:01Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** the goal-decomposer choosing a target journey, and any evaluator writing a next-step
summary of a multi-part gap.

## iter-57 — 2026-08-10T18:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose DoD asserts a property of the RUNTIME state ("no live fetches", "no new
rows", "no MemoryErrors") — verify it after the lane, never before, and record the pre-lane watermark.

## iter-57 — 2026-08-10T18:55:01Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration recording a poll/latency drill in `reports/perf-budgets.md`, and any agent
reading a "N polls, zero failures" claim — check N against the log's own line count first.

## iter-57 — 2026-08-10T18:55:02Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration replaying J-06, or scheduling heavy work immediately after the browser lane —
budget for the regime-lab compute the golden starts, or pin the golden to a lab that serves from storage.

## iter-58 — 2026-08-10T21:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that produces a latency/health drill or cites screenshots as journey
evidence; specifically the browser-qa lane's write-ups and any evaluator scoring J-05 step 4 or J-07 step 2.

## iter-59 — 2026-08-11T07:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every goal-mode iteration — check `Target journeys:` against the merged results table's
rows before believing any headline; and any framework work on `scripts/automation/lib/replay-lane.sh` or the
ui-test-designer's plan generation.

## iter-59 (2 of 2) — 2026-08-11T07:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that reads `logs/backend.log` counts as evidence, and any future
fault-injection site added to `_FAULT_INJECT_SITES`.

## iter-60 — 2026-08-11T08:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose scope includes `scripts/automation/lib/*.sh`, `goal-iter-lean.sh`, or
any other shell library the running executor sources at startup.

## iter-60 (second) — 2026-08-11T08:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that runs a live backfill/fetch/rebuild, or that touches
`data_manager.compute_coverage` / `coverage_snapshot` / any ingest-maintained aggregate.

## iter-61 — 2026-08-11T11:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluation/audit that compares a UI screenshot or file mtime to a database
timestamp; anything reading `data_provider_runs`, `scanner_runs.created_at`, `coverage_snapshot`.

## iter-61 (2 of 2) — 2026-08-11T11:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any change to `scripts/automation/lib/*.sh` consumed by both `goal-iter-lean.sh` and
`browser-qa-phase.sh`; any DoD item phrased as "the engine log lists X".

## iter-62 — 2026-08-11T15:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that runs, edits or trusts `runs/goal-session-*/journey-scripts/*.json`
goldens that create data (J-05 today; any future state-mutating golden).

## iter-62 — 2026-08-11T15:40:01Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reading `*-regression-replay-results.md`, and any change to the browser-QA
lane's restart/replay ordering.

## iter-63 — 2026-08-11T17:50:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that rotates, lints or trusts `runs/goal-session-*/journey-scripts/*.json`
goldens that create data.

## iter-63 — 2026-08-11T17:50:01Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `reports/perf-budgets.md` addenda, health-poll drills, or J-07's
latency acceptance.

## iter-63 — 2026-08-11T17:50:02Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching the demo/walkthrough recorder, `demo.sh`, or
`reports/phase-*-demo-*.md` — and any evaluator reading `/data` job rows after a demo pass.

## iter-64 — 2026-08-11T21:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where `regression-replay-results.md` carries a reconciliation footer; any
evaluator or QA agent tempted to accept "transient/false positive" without opening the PNG.

## iter-64 (2 of 2) — 2026-08-11T21:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any golden/fixture that writes to the shared DB (journey-scripts/J-01, J-03, J-05), and
any future "self-renewing" mechanism claim.

## iter-65 — 2026-08-12T00:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose goal is derived from a latency/throughput measurement, and any J-07-class
work in `apps/backend/app/engine/research.py` / `data_manager.py`; also any round planning to piggyback a
drill on a lane that runs a browser at the same time.

## iter-66 — 2026-08-12T02:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration chasing `GET /api/health` latency during ingest/warm phases; any lane that
cross-checks a UTC measurement against a Trendora log timestamp; any round that adds an explanatory metric.

## iter-67 — 2026-08-12T06:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reporting `scripts/qa/poll_health.py` drills, `logs/health-watchdog.jsonl`
samples, or any phase attribution in `reports/perf-budgets.md`.

## iter-68 — 2026-08-12T07:50:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a timing/diagnostic instrument, and any iteration whose measurement is
taken by one lane while a second lane independently measures the same thing (arm the flag session-wide, and
derive the cross-lane deltas before asking for a new sample type).

## iter-69 — 2026-08-12T10:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reporting a performance/availability metric that moved, especially J-07 health-poll
drills — group by ingest phase and report the grouping, and normalize any named confound by the same buckets.

## iter-69 — 2026-08-12T10:06:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** the goal-evaluator writing `iteration-state.md`'s Do-not-redo list, and any decomposer treating
that list as binding.

## iter-70 — 2026-08-12T15:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that caches, memoizes, or background-refreshes a value the UI uses to state
whether the system is trustworthy (`app.engine.readiness`, preflight verdicts, warmup/background-compute
status) — and any iteration that moves compute off a request path.

## iter-70 (second) — 2026-08-12T15:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose journeys are verified by a lane that depends on a long-lived service —
check the replay/browser results file directly, and treat a clean uvicorn shutdown signature (no traceback)
as infrastructure, never as a product crash.

## iter-71 — 2026-08-12T18:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration scoring J-04, J-06 or J-07 (all three name prod-mode measurement
conditions, two of them saying "never dev.sh" verbatim); any iteration that cannot find
backend evidence in `logs/backend.log`; any launcher-parity work on `scripts/dev.sh`.

## iter-71 (second) — 2026-08-12T18:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any change adding a cache-staleness bound or a synchronous fallback on a
request path; any future work on `app.engine.readiness` / `_TICK_LOCK` / `GET /api/health`.

## iter-72 — 2026-08-12T23:38:45Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `config.yaml`'s `database.pool_size`/`max_overflow`/`pragmas`,
`server.limit_concurrency`, thread/worker counts, or any per-connection cache — and any evaluator
deciding whether A.6 evidence durability covers a memory/VmPeak step.

## iter-72 (2 of 2) — 2026-08-12T23:38:45Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any round reconciling deterministic-replay FAILs against an LLM lane, and any agent
writing a "false positive / host contention" note — cite a timestamp bracket and the frame's contents.

## iter-73 — 2026-08-13T03:06:22Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose deterministic replay reports 3+ simultaneous FAILs; any evaluator
reading a `VOIDED`/`overturned` footer; anyone about to act on `state/goldens-regen-pending`.

## iter-74 — 2026-08-13T06:20:00Z

**Verdict:** CONTINUE
**Lesson:** When a measurement keeps failing, change the TRIGGER, not the thing measured. Four
attempts across iters 72-73 could not get a VmPeak reading because `rebuild` unconditionally rescans
the full 2005-2026 basis (30-45+ min on today's 8.4 GB DB) before the finalize tail even starts; this
round got a complete 9-of-9-phase profile on the first try by firing the identical
`_refresh_ingest_aggregates` tail from a single-date `backfill` instead — same computation, same
pool pressure, same launcher, minus the irrelevant scan. Second half of the lesson: the resulting
"per-phase profile" turned out degenerate (VmPeak plateaued at t+134.7 s, before the tail, so all 14
rows carry one identical number). Do not read a per-phase table as per-phase measurement without
checking the underlying series for monotonic plateau first — VmPeak is a high-water mark, so joining
it to phase boundaries can only ever produce a step function.
**Applies to:** any iteration that must measure a cost inside `_refresh_ingest_aggregates` /
`data_manager.py`'s finalize tail, or that joins `_MemSampler` (or any `/proc` high-water metric)
against phase-timer log lines.

## iter-74 — 2026-08-13T06:20:01Z

**Verdict:** CONTINUE
**Lesson:** A capture defect and a product defect can hide in the same voided batch. Of this round's
five mass-voided replay FAILs, four frames were unstyled asset-less shells (harness), but J-05's was
the styled app showing its own contained error boundary on Scanner Runs — a real render failure that
the blanket "selector/environment drift" footer would have buried. Open EVERY frame in a voided batch,
not a sample: the batch reason is written once and applied to all, so a single genuine failure inside
it is invisible by construction.
**Applies to:** any iteration whose `regression-replay-results.md` carries a SPEED-22 mass-void footer,
and to any future change to that breaker.

## iter-75 (1 of 2) — 2026-08-13T08:00:00Z

**Verdict:** CONTINUE
**Lesson:** A clean replay round after three broken ones is NOT evidence the harness was repaired.
This round's product diff is literally "(no changes)" — no developer ran — yet the intermittent
asset-less-frontend defect (iter-72/c) that voided goldens in iters 72, 73 and 74 simply did not
fire, and 8/8 passed. Treat "did not recur" and "fixed" as different states in the ledger: the
former closes nothing, and a future clean round proves nothing until the mechanism is named.
**Applies to:** any iteration tempted to close an intermittent harness/environment defect on a
quiet round; any evaluator reading a first-clean-in-N replay result.

## iter-75 (2 of 2) — 2026-08-13T08:00:00Z

**Verdict:** CONTINUE
**Lesson:** "8/8 replay PASS" is a claim about the goldens, not about the product — parse them
before quoting the headline. `runs/goal-session-ops-hardening/journey-scripts/J-07.json` has
exactly two steps (goto `/` expect "Ready"; goto `/backtest` expect "Forward-test scorecard") and
`J-09.json`'s strongest assertion is a panel's presence, so J-09's golden passes against an IDLE
panel — which is why `J-09-verify.png` shows no in-flight window yet its row reads PASS. The
per-journey strength of a "PASS" varies enormously (J-01's golden asserts the exact exclusion
partition; J-07's asserts two words).
**Applies to:** any evaluator scoring from `ui-test-results.md`; any iteration that adds or
regenerates a golden; the queued work to strengthen J-07's and J-09' goldens.

## iter-76 — 2026-08-13T09:40:00Z

**Verdict:** ESCALATE
**Lesson:** Once every Must-have journey is recorded `passing`, the SPEED-9 evidence backstop at
`scripts/automation/run-goal.sh:2509-2539` silently demotes EVERY `lean` spec to `evidence` — the
guard only checks that each Target journey is `passing`/`already_passing` with no `pending_infra`,
so no lean iteration can ever staff a developer again, no matter what the spec's Definition of Done
says. Iters 75 and 76 both produced an empty diff for exactly this reason while their specs ordered
real code work. The backstop's own guard is `DEPTH == "lean"`, and `run-goal.sh:2427` / `:2482`
grant a full pass on `prior-verdict-ESCALATE`, so **ESCALATE is the deterministic escape and a
CONTINUE + "full" recommendation is not** (line 2452 falls through to the legacy allowlist and is
demoted straight back unless the spec happens to carry a `Full trigger:` line).
**Applies to:** any goal-mode session where all Must-have journeys are passing but harness,
hygiene, or non-journey-advancing work remains — i.e. every late-stage session. Check
`iter-<N>/depth-dispatched` against the spec's `**Depth:**` line before believing an iteration ran
its code lane.

## iter-76 — 2026-08-13T09:41:00Z

**Verdict:** ESCALATE
**Lesson:** A backfill submitted against a freshly booted backend can stay `running` for ~18 minutes
even when it is pure zero-work: `data_provider_runs` 493 ran 08:19:35 -> 08:38:11 because the first
ingest after boot opens a full finalize-tail heavy warm (`forward_aggregates_warm` 495.9 s,
`factor_lab_all_warm` 596.8 s). `demo_runner.py` hard-caps every step at 20 s, so any golden that
waits for a job's completion text will FAIL on the first post-boot run and PASS later — the same
golden that passed in iter-75 finished in 0.2 s because the caches were already warm. Do not read
that FAIL as selector drift, a frontend fault, or "transient load".
**Applies to:** any golden or QA step that submits an ingest job and waits for its outcome; any
round diagnosing a replay FAIL — check `data_provider_runs` start/finish times against the frame
mtime before accepting any other explanation.

## iter-77 — 2026-08-13T15:35:00Z

**Verdict:** ESCALATE
**Lesson:** A test that writes a deliberately-broken source file into the LIVE app tree
(`test_start_frontend_script.py:533` → `apps/frontend/__tc3_intentionally_broken.ts`) and cleans it
up only in its own fixture will, on any interrupted run, leave the whole frontend unbuildable — and
the ONLY symptom is `start-frontend.sh` exiting 1. It happened this round because an 11-minute test
module was dispatched into a 2-minute-limited tool; every browser lane afterwards would have found no
frontend at all. Sabotage-style fixtures must write outside the served tree, or the launcher must be
taught to ignore their filenames.
**Applies to:** any iter touching `apps/backend/tests/test_start_frontend_script.py`, any test that
plants files under `apps/frontend/`, and any lane that dispatches a long pytest module under a
short-timeout tool.

## iter-77 — 2026-08-13T15:36:00Z

**Verdict:** ESCALATE
**Lesson:** "Every lane passed" and "the round is closeable" are different claims. This round had
review PASS_WITH_NOTES, audit PASS_WITH_GAPS and QA PASS, yet the deterministic closure gate FAILED —
because the fix pass wrote its winning replay results to a side file
(`…-evidence/devfix-replay/replay-fast-results.md`) instead of re-merging them into
`…-ui-test-results.md`, leaving the artifact of record reporting three target journeys as never
tested. Whenever a fix pass re-runs a verification lane, it must write back into the artifact of
record, not beside it. Corollary found the same way: `closure_gate.py:72`'s backend-only guard is a
bare substring match and false-positives on a sentence that DENIES a backend-only gap.
**Applies to:** any fix-mode pass that re-runs browser-qa or the replay lane; any iter reading a
closure verdict; anyone editing `scripts/automation/lib/closure_gate.py`.

## iter-78 — 2026-08-13T19:30:00Z

**Verdict:** STALLED
**Lesson:** A carried "still owed" item can be false and stay false for twenty rounds. Every recent
log repeated "the `[NEW]` walkthroughs for J-05 and J-07 are owed"; opening
`reports/goal-session-ops-hardening-demo.json` showed step 9 IS a `new: true, verified: true` J-07
step, and the journey's acceptance only requires it be *viewable via* `demo.sh <sid> --session-live`
(a live run), not recorded into a frame gallery. J-05's step 7 genuinely is not `[NEW]`-flagged, so
half the carry was real and half was folklore.
**Applies to:** any evaluator or decomposer about to copy a "carried, Nth round owed" list forward —
re-open the artifact for at least the oldest items before restating them.

## iter-78 — 2026-08-13T19:31:00Z

**Verdict:** STALLED
**Lesson:** `closure_gate.py:66`'s placeholder regex (`\bTODO\b|\bTBD\b|<fill|…`) matches the token
anywhere in a UI-visibility artifact, including inside a QUOTED tool message. This round's browser-qa
row honestly quoted Chrome-MCP's own file contents ("TODO: Console logging not yet implemented") and
that single quotation failed the closure gate and left the whole iteration recorded
`blocked`/`closure_failed` — a complete artifact rejected for a word it was reporting, not authoring.
**Applies to:** browser-qa-agent, qa and any agent writing `reports/phase-*-{ui-test-results,
implementation-summary,user-visible-changes,ui-surface-map,ui-test-plan,what-to-click}.md` — paraphrase
tool messages containing TODO/TBD/XXX rather than quoting them verbatim.

## iter-78 — 2026-08-13T19:32:00Z

**Verdict:** STALLED
**Lesson:** An acceptance criterion that a thorough audit keeps adding to cannot be driven to zero by
working harder: this session's unresolved-note count went 138 → 140 → 146 across three rounds in which
all eight journeys passed every time, because each round's own auditing opens more notes than the round
closes. When the count trends UP across rounds with no failing journeys, the criterion — not the work —
is the blocker, and that is an owner decision, not another iteration.
**Applies to:** any goal-mode session whose journeys are all green while a self-maintained violation
ledger keeps growing; check the trend across the last three rounds before recommending "one more round".

## iter-79 — 2026-08-14T00:30:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A carried "Nth round owed" note was again wrong in a NEW way: opening
`reports/goal-session-ops-hardening-demo.json` shows FOUR journeys' walkthrough steps are
`new: false` (J-01 steps 3-4, J-03 5-6, J-04 2, J-05 7), not just J-05's as twenty rounds of logs
claimed — iter-78 corrected this carry once (for J-07) and it was still under-stated. Re-open the
artifact every time a carry is repeated; a partially-corrected carry is as misleading as an
uncorrected one.
**Applies to:** any evaluator or decomposer about to copy forward a "carried / Nth round owed"
item — especially walkthrough/demo-metadata claims and anything phrased as "still owed".

## iter-79 — 2026-08-14T00:30:01Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The 9.3 s `/api/backtest` outlier was reported as a budget breach; the database
settled the cause in one query — that as-of's five horizons committed inside ~1.5 s
(`forward_aggregate_cache` 23:56:41.68 → 23:56:43.14 UTC), so the wait was queueing behind
another in-flight warm, not slow compute. Timing outliers on a dispatch-based design should be
split into "compute time" vs "wait time" from the cache commit timestamps before being scored;
the two point at completely different fixes (bounding concurrency vs bounding the computation).
**Applies to:** any iteration touching `app/engine/forward_testing.py`, the background dispatch
registry, or B-1107 concurrency bounding.
