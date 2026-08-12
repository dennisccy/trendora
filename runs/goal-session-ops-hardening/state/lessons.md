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

## iter-54 — 2026-08-09T23:45:00Z

**Verdict:** ESCALATE
**Lesson:** A finalize-tail warm can abort part-way and still be persisted as complete: run 351's
forward-aggregate warm stopped at horizon 20 under real memory pressure (`logs/backend.log:233042`,
"stopping remaining horizons in this loop" — horizon 60 never ran), yet `data_provider_runs.id=351`
stores `status='ok'` with `forward_aggregates` still listed in `aggregates_refreshed`. The
isolate-and-continue path drops a *failed* member from the list (that is how `factor_lab_all`
disappeared, `:233277`) but a *partially completed* member keeps its entry — so the honest-omission
mechanism has a hole exactly where a loop aborts mid-iteration. Every future scoring of J-05/J-07 must
read the finalize-tail sub-phase timing lines for the job (count the horizons) instead of trusting
`aggregates_refreshed` alone.
**Applies to:** any iter touching `data_manager._refresh_ingest_aggregates` / `forward_testing`'s warm
loop, and any lane or evaluator scoring an ingest run from `aggregates_refreshed` / `status`.

## iter-54 (second entry) — 2026-08-09T23:45:00Z

**Verdict:** ESCALATE
**Lesson:** Poll density decides whether an availability defect is visible at all. The browser lane's
127 samples over 20m50s recorded "0 non-answers" and passed J-05/J-07; the developer's 1-per-second
drill over the same tree recorded 6 non-answers and 53 polls over 2.0s. Both are honest measurements of
the same product — the sparse one simply cannot see a 5-second gap. A lane row asserting "health stayed
responsive" is only evidence if its sampling interval is shorter than the outage it claims to exclude.
**Applies to:** any browser-qa or golden script asserting J-05 step 4 / J-07 step 2, and any iteration
that plans to replace the 1 Hz concurrent drill with in-turn browser polling.

## iter-54 (third entry) — 2026-08-09T23:45:00Z

**Verdict:** ESCALATE
**Lesson:** A behaviour-asserting golden can fail for the very behaviour it exists to protect. J-04's new
golden asserts `[data-testid="readiness-badge"][data-state="ready"]` on step 2 and FAILED — because the
replay started ~1 minute after a backend restart and `J-04-verify.png` shows the badge reading
"Initializing… history 89/89", which is J-04's own required behaviour. `J-08-verify.png` from the same
replay minutes later shows "Ready". Goldens that assert a steady state must first `wait_for` that state,
or they encode a race as a regression.
**Applies to:** every golden in `runs/goal-session-ops-hardening/journey-scripts/` whose first assertion
reads a readiness/health-derived attribute (J-04.json step 2, J-07.json step 2).

## iter-55 — 2026-08-10T03:00:00Z

**Verdict:** CONTINUE
**Lesson:** A verification fixture that CONSUMES its own precondition is a guaranteed future
false-regression. `journey-scripts/J-05.json` requires a trading day with zero snapshot rows and
asserts "0 already snapshotted"; running it creates that snapshot, so the very act of passing it
makes the next run fail. This round consumed 2010-11-08 (`scanner_runs.id=2940`) and left the
script un-rotated — and the failure mode is already demonstrated in this round's own data: a
second concurrent `demo_runner` instance hit the same date and recorded `already_snapshotted=1`
(`data_provider_runs.id=359`). A lean round would see the FAIL, have no audit to explain it, and
could score J-05 `regressed` and halt the session on a fixture artifact. Either rotate the date in
the same commit that runs the golden, or make single-use goldens pick their target date at run
time from `GET /api/data/availability`.
**Applies to:** any golden script whose assertions depend on a one-shot state the script itself
changes (single-use dates, "first time" flags, one-off job outcomes) — and any evaluator scoring a
replay FAIL on such a journey.

## iter-55 (second entry) — 2026-08-10T03:00:00Z

**Verdict:** CONTINUE
**Lesson:** The replay lane writes `reports/phase-<iter>-regression-replay-results.md` wholesale,
so a NARROWER later run silently erases a BROADER earlier one. This round a 7-journey developer
run at ~02:09 (which produced the only J-05/J-07 rows this session has ever had) was overwritten
at 02:32 by a 5-journey lane run; `replay-lane/verify-run.log` was truncated to 0 bytes at the
same time. The reviewer had read the 7-row file at 02:25 and cited it; six minutes later QA cited
the same rows and they no longer existed. Nothing detected this except mtimes and the PNG
provenance stamps (`Created=2026-08-10T02:09:47`), which is the only reason the evidence was
recoverable at all — keep stamping capture artifacts. Fix: per-run result files, or merge rows
instead of overwriting.
**Applies to:** any iteration whose replay lane runs more than once (developer pass + lane pass),
and any evaluator reading a results table that disagrees with a dev handoff or review report.

## iter-56 — 2026-08-10T06:30:00Z

**Verdict:** ESCALATE
**Lesson:** Moving a value from "computed on every request" to "warmed at ingest" silently changes
what the page shows *while an ingest is running*. `availability_from_storage`
(`apps/backend/app/engine/data_manager.py:1676-1690`) reads only the row matching the current
`_membership_dataset_version` stamp, and that stamp folds in `count(daily_prices)` — so the first bar
a job commits invalidates it, the only writer is the finalize-tail warm at the END of the job, and for
the whole run `/data` renders `availability-heatmap.tsx:230-238`'s "No availability yet — There are no
stored trading days to chart. Fetch real EOD prices" on a 3.3M-row database. The stale row is still in
the table; the serving path just refuses it. Any future ingest-time cache must decide, explicitly,
whether a stamp miss means "serve the previous value with an as-of marker", "say updating", or
"say empty" — the empty sentinel that is honest on a fresh install is a lie on a mature one.
**Applies to:** any iteration adding or changing an ingest-warmed cache under
`app/engine/data_manager.py` / `app/engine/indexes.py` (coverage_snapshot, membership_timeline,
index_series, availability_heatmap, factor_lab_all), and any browser check that only ever loads a page
on a warm idle system.

## iter-56 — 2026-08-10T06:30:01Z (second entry)

**Verdict:** ESCALATE
**Lesson:** A journey's gap list lives in `journey-history.json`, not in the previous round's prose.
iter-54 recorded FOUR over-budget readings for J-06; iter-55's next-step summarised them as "two slow
endpoints"; the iter-56 spec was built on the summary, fixed exactly those two, and the journey still
cannot pass. Read the structured note before planning a journey's closing round.
**Applies to:** the goal-decomposer choosing a target journey, and any evaluator writing a next-step
summary of a multi-part gap.

## iter-57 — 2026-08-10T18:55:00Z

**Verdict:** CONTINUE
**Lesson:** A verification check placed BEFORE the lane is structurally incapable of catching a breach the
lane itself causes. This round's TC-16 ("all ingest rows read `provider='seed'`") was authored around 09:14
local and the AG-9 breach it exists to detect — `data_provider_runs` id=369, a drill click on `/data`'s
"Fetch real EOD prices" button that made 591 live outbound requests — happened an hour later. Five earlier
occurrences (ids 135/261/262/264/297) passed the same check for the same reason. The fix that worked was
positional, not rhetorical: record `max(data_provider_runs.id)` before the lane, re-query after it.
**Applies to:** any iteration whose DoD asserts a property of the RUNTIME state ("no live fetches", "no new
rows", "no MemoryErrors") — verify it after the lane, never before, and record the pre-lane watermark.

## iter-57 — 2026-08-10T18:55:01Z

**Verdict:** CONTINUE
**Lesson:** A drill summary that computes segment counts can silently delete its own failure. The TC-7
health drill's log has 1,212 records; `reports/perf-budgets.md` Addendum 23 reports three segments summing
to exactly 1,211 and states "ZERO non-200, no unresponsive gap" — the one record that failed
(`2026-08-10T10:30:00Z 000 10.002641`) fell outside every hand-picked sub-window, and the window's stated
end is one second before it. The same sentence then propagated into the dev handoff and `status.json`.
Segment boundaries chosen by hand are where failures go to disappear; bound them by the process's own
`ingest heavy-warm window OPEN/CLOSED` markers and reconcile the segment total against `wc -l` of the raw
log before writing any "zero failures" claim.
**Applies to:** any iteration recording a poll/latency drill in `reports/perf-budgets.md`, and any agent
reading a "N polls, zero failures" claim — check N against the log's own line count first.

## iter-57 — 2026-08-10T18:55:02Z

**Verdict:** CONTINUE
**Lesson:** J-06's own golden provokes the condition J-07 exists to catch. Its last step navigates to
`/research/regime-lab`, whose first read after any data change derives the whole stored forward-return
history — `J-06-verify.png` captures it mid-flight ("Still computing — 16s elapsed"), and that same
heavy-compute class hit the `ulimit -v` ceiling twice this round (23 new MemoryErrors after three clean
rounds, then a wedged process). So every J-06 replay leaves a multi-minute whole-history compute running in
the background of whatever runs next, including the lane's own later steps.
**Applies to:** any iteration replaying J-06, or scheduling heavy work immediately after the browser lane —
budget for the regime-lab compute the golden starts, or pin the golden to a lab that serves from storage.

## iter-58 — 2026-08-10T21:55:00Z

**Verdict:** ESCALATE
**Lesson:** Hashing an evidence directory for distinctness does NOT prove the pictures show anything —
this round's nine PNGs were all distinct, and one of them (`J-05-job-running.png`, 2,061 bytes) is a
completely blank frame while two more are viewport crops of the top of `/data` showing none of the state
their rows assert. Open the files; distinctness is a duplication check, not an evidence check. Second, and
worse: the SAME iteration that corrected iter-57's "segment boundary hid a failed poll" defect reproduced
it one lane over — a real 3.474 s health answer at `j05-health-poll.log:114` was written up as "a 4s gap
(poll-script restart, negligible)" when the log has no missing sample there at all. Re-derive a drill's
tally from its raw log before believing any prose summary of it, including a summary written by the same
round that fixed the identical bug.
**Applies to:** any iteration that produces a latency/health drill or cites screenshots as journey
evidence; specifically the browser-qa lane's write-ups and any evaluator scoring J-05 step 4 or J-07 step 2.

## iter-59 — 2026-08-11T07:05:00Z

**Verdict:** CONTINUE
**Lesson:** An iteration's TARGET journeys can end up verified by nobody. `replay-lane.sh` replays
`REQUIRED_JOURNEYS` only, and target journeys are assumed to get rows from the LLM browser lane — whose
generated test plan (UT-01..UT-06) contained no J-05 or J-07 case. Both target journeys had VALID goldens
that passed on the first attempt when the developer ran `demo_runner.py --mode verify` by hand, and neither
was ever replayed by a lane, so `ui-test-results.md` shipped `BLOCKED` with "no test case executed by any
lane" over work that was actually done and correct. Promoting a journey to an iteration's own target is
still the surest way to remove its verification (same class as iter-41's B2, which was thought fixed).
**Applies to:** every goal-mode iteration — check `Target journeys:` against the merged results table's
rows before believing any headline; and any framework work on `scripts/automation/lib/replay-lane.sh` or the
ui-test-designer's plan generation.

## iter-59 (2 of 2) — 2026-08-11T07:05:00Z

**Verdict:** CONTINUE
**Lesson:** Once a fault-injection hook exists, raw `grep -c MemoryError logs/backend.log` becomes a
misleading regression signal: this round's count moved 8,131 → 8,171 and **all 40 new lines were the
deliberate `injected at fault-injection site 'regime_lab'` hook**, while real memory exhaustion was zero.
Separate injected from real (`grep -v "injected at fault-injection"`) and locate the last real one against
the `start-backend.sh: launching at` markers to date it — that is what proved this iteration served zero
500s and raised zero real MemoryErrors across ~7.5 hours.
**Applies to:** any iteration that reads `logs/backend.log` counts as evidence, and any future
fault-injection site added to `_FAULT_INJECT_SITES`.

## iter-60 — 2026-08-11T08:40:00Z

**Verdict:** ESCALATE
**Lesson:** A shell library edited by the developer cannot take effect in the same run that edits it —
`goal-iter-lean.sh:45` sources `lib/replay-lane.sh` when the executor starts, so the round's own
top-priority fix (routing `TARGET_JOURNEYS` goldens into the deterministic replay set) was still the old
function body when the lane ran three minutes after the edit. The engine's own log proves it (07:46:43
"Regression (deterministic replay): J-01 J-03 J-04 J-06 J-08 J-09", and the new fix's log line appears
nowhere), yet the review recorded `definition_of_done: complete`. Any iteration whose deliverable is a
change to `scripts/automation/lib/*.sh` must state up front that its own run cannot verify it, and the
NEXT round must confirm it from the live lane log before the item is closed.
**Applies to:** any iteration whose scope includes `scripts/automation/lib/*.sh`, `goal-iter-lean.sh`, or
any other shell library the running executor sources at startup.

## iter-60 (second) — 2026-08-11T08:40:00Z

**Verdict:** ESCALATE
**Lesson:** Comparing a screenshot's numbers against the database found a defect that five lanes and two
"PASS" verdicts missed: `coverage_snapshot` (written inside the ingest finalize tail at 06:58:55) held
`snapshot_count=2954` / `gap_count=2442`, while `/data` frames captured 48 minutes later in the same
never-restarted process displayed 2953 / 2443. Golden replays assert selectors, not values, so a stale
served aggregate passes every deterministic check. Whenever an iteration runs a real ingest, read the
resulting persisted aggregate out of sqlite and compare it to whatever number the page shows in the
evidence frame.
**Applies to:** any iteration that runs a live backfill/fetch/rebuild, or that touches
`data_manager.compute_coverage` / `coverage_snapshot` / any ingest-maintained aggregate.

## iter-61 — 2026-08-11T11:40:00Z

**Verdict:** CONTINUE
**Lesson:** This repo stores naive **UTC** in sqlite (`data_provider_runs.started_at`,
`coverage_snapshot.computed_at`) while the backend's structured log lines and all file mtimes are
**local BST (UTC+1)** — so comparing a screenshot's mtime to a DB row's timestamp is off by an hour
in the direction that manufactures "staleness". That is exactly what happened at iter-60: its
`J-04`/`J-09` frames (mtime 07:47 local) were read as 48 minutes *after* a coverage write that
actually landed at 07:58:55 local, and a whole iteration (61) was commissioned to fix a defect that
never existed. Always pin the offset first against a job's own log marker (DB `started_at` 09:40:39
vs `backend.log` "heavy-warm window OPEN" 10:40:41) before calling a displayed number stale.
**Applies to:** any evaluation/audit that compares a UI screenshot or file mtime to a database
timestamp; anything reading `data_provider_runs`, `scanner_runs.created_at`, `coverage_snapshot`.

## iter-61 (2 of 2) — 2026-08-11T11:40:00Z

**Verdict:** CONTINUE
**Lesson:** A shell-library fix can be correct, merged, and still dead on half its callers: iter-60's
target-journey replay routing (`lib/replay-lane.sh:300-317`) works on the lean path because
`goal-iter-lean.sh:204` assigns `TARGET_JOURNEYS` before calling the partition function, and is inert
on the full path because `browser-qa-phase.sh:272` calls it 14 lines *before* `:286` assigns the same
variable. Verify a lane fix on **every** caller (`grep -n "replay_lane_partition_and_verify" scripts/`),
and confirm from the engine log's own line — its distinctive "Target journey … routed" message has never
appeared once in this session.
**Applies to:** any change to `scripts/automation/lib/*.sh` consumed by both `goal-iter-lean.sh` and
`browser-qa-phase.sh`; any DoD item phrased as "the engine log lists X".

## iter-62 — 2026-08-11T15:40:00Z

**Verdict:** ESCALATE
**Lesson:** A golden that performs REAL work can destroy its own precondition: J-05's script backfills
2010-11-17 and asserts "0 already snapshotted", so this round's own successful replay (creating
`scanner_runs` id=2958) guarantees the SAME script fails next round. Any golden that mutates state needs
either a fresh target chosen at run time or an explicit rotation step — and its closing assertions must
name the row it just created, not a date from two rotations ago (steps 13-15 still assert 2010-11-16).
**Applies to:** any iteration that runs, edits or trusts `runs/goal-session-*/journey-scripts/*.json`
goldens that create data (J-05 today; any future state-mutating golden).

## iter-62 — 2026-08-11T15:40:01Z

**Verdict:** ESCALATE
**Lesson:** The deterministic replay lane can start while the backend is still warming up after the
pipeline's own pre-QA restart, and then reports FALSE FAILs on required-still-passing journeys — this
round J-01 (step 09) and J-04 (step 02, a 20 s `wait_for` on `data-state="ready"`). Proof is cheap and
should be the first check on any replay FAIL: compare the frame's mtime with the `=== start-backend.sh:
launching at ... ===` banner in `logs/backend.log` (13:24:00Z boot vs 14:25 local frames), and look at the
frame — both showed the honest "initializing history 89/89" chip. Never read such a FAIL as a regression.
**Applies to:** any iteration reading `*-regression-replay-results.md`, and any change to the browser-QA
lane's restart/replay ordering.

## iter-63 — 2026-08-11T17:50:00Z

**Verdict:** CONTINUE
**Lesson:** Rotating a state-mutating golden onto a fresh date is NOT enough when the same round then
replays it: the dev pass pointed `journey-scripts/J-05.json` at 2010-11-18 and this round's own replay
lane consumed it 50 minutes later (`data_provider_runs` id=419 → `scanner_runs` id=2960 at 16:34:50Z),
re-arming the exact false-FAIL the round existed to remove. Four consecutive rounds have now eaten the
date they set. The durable fix is for the lane to select-and-persist an unsnapshotted trading day AT
REPLAY TIME (or rotate immediately AFTER consuming), never a human guessing one round ahead.
**Applies to:** any iteration that rotates, lints or trusts `runs/goal-session-*/journey-scripts/*.json`
goldens that create data.

## iter-63 — 2026-08-11T17:50:01Z

**Verdict:** CONTINUE
**Lesson:** A single-worst-case headline can hide a whole-distribution regression. "2.849 s → 2.420 s,
~50 % overage reduction" compares ONE poll in one run to ONE poll in another, while the same two runs move
1 → 53 breaches, p90 0.911 s → 1.475 s and p99 1.259 s → 3.002 s. Always recount the raw CSV
(`evidence-drill/tc5-health-poll.csv`) into a distribution — count over ceiling, p90, p99, max — before
accepting any latency claim, and check the idle pre-job baseline to test the "host was busier" excuse.
**Applies to:** any iteration touching `reports/perf-budgets.md` addenda, health-poll drills, or J-07's
latency acceptance.

## iter-63 — 2026-08-11T17:50:02Z

**Verdict:** CONTINUE
**Lesson:** The showcase/demo lane is not read-only: when its fill steps fail ("unresolvable target
job-start-date"), it still clicks Start, and this round that launched a REAL 5-date backfill
(`data_provider_runs` id=420, 2005-06-24→2005-06-30) which the narration described as finishing "within
seconds" and which was left `running` with no live process when services were torn down. A demo step whose
own precondition failed must not proceed to a submit action.
**Applies to:** any iteration touching the demo/walkthrough recorder, `demo.sh`, or
`reports/phase-*-demo-*.md` — and any evaluator reading `/data` job rows after a demo pass.

## iter-64 — 2026-08-11T21:20:00Z

**Verdict:** CONTINUE
**Lesson:** When the deterministic replay lane FAILs a step and the LLM lane overturns it, the overturn's
stated REASON can be wrong even when its verdict is right — open the failing frame. This round both
write-ups called J-05's step-13 failure a "golden-script false positive" / "navigation outrunning a final
commit"; `reports/qa/goal-ops-hardening-iter-64-evidence/J-05-verify.png` actually shows `/scanner-runs`
rendering the app's contained error boundary ("Something went wrong on this page") with the top bar
reading `Ready`. The golden was right to fail; a product page had errored. J-07's overturn in the same
run WAS a lane artifact (its frame shows an unstyled, still-loading page) — so the two must be judged
frame by frame, never as one class.
**Applies to:** any iteration where `regression-replay-results.md` carries a reconciliation footer; any
evaluator or QA agent tempted to accept "transient/false positive" without opening the PNG.

## iter-64 (2 of 2) — 2026-08-11T21:20:00Z

**Verdict:** CONTINUE
**Lesson:** A state-mutating golden is only fixed when it selects its own input at run time AND the
selection is re-checked after the round consumes it. `resolve_sentinel_date()` (demo_runner.py:237-275)
ended five rounds of hand-rotating J-05's date, but the proof that mattered was cheap and post-hoc:
calling the resolver again once the round had used 2005-06-27 and confirming it returned 2005-06-28 with
2,193 eligible days left. Do that one call rather than reading the unit test.
**Applies to:** any golden/fixture that writes to the shared DB (journey-scripts/J-01, J-03, J-05), and
any future "self-renewing" mechanism claim.

## iter-65 — 2026-08-12T00:15:00Z

**Verdict:** CONTINUE
**Lesson:** A latency "regression" that reproduced twice (iters 63/64: 53 of 983 then 59 of 930 health
polls over 2.0s, ~52-58 of them inside `factor_lab_all_warm`) did NOT reproduce at all under four
escalating controlled profiles this round on byte-identical code — 0 stalls >0.30s solo, 0 breaches
against the real route function, 0 through real ASGI/HTTP, and 1 of 1,057 in a full live ingest with none
inside the phase. Worse, the same round's two measuring instruments disagreed by ~40x in rate (the dev's
single-process `poll_health.py` 1/1,057 vs the browser-QA lane's subprocess-per-poll loop 8/240 on a shell
reporting `nproc`=4). Prove the instrument and attribute each breach to an exact phase from the app's own
millisecond `logs/backend.log` phase markers BEFORE chartering a code fix — this round's whole premise
("a third GIL hold exists") came from a number nobody had yet pinned to a phase.
**Applies to:** any iteration whose goal is derived from a latency/throughput measurement, and any J-07-class
work in `apps/backend/app/engine/research.py` / `data_manager.py`; also any round planning to piggyback a
drill on a lane that runs a browser at the same time.

## iter-66 — 2026-08-12T02:40:00Z

**Verdict:** CONTINUE
**Lesson:** Two rounds of "profile the phase" found zero stalls because both re-ran the computation in a
standalone script; the thing that finally localized the problem was arithmetic on artifacts that already
existed — aligning the 1,024 health-poll timestamps in `tc1-health-poll.csv` against `dev.log`'s own phase
lines put 68 of 70 breaches inside `factor_lab_all_warm` (15.7 % of 433 polls) with ZERO in the 382 polls
right after it. Two traps to avoid next time: `dev.log`/`logs/backend.log` timestamps are host-local
(UTC+1) while every CSV and DB row is UTC — the browser-QA lane's phase attribution this round was wrong by
exactly one hour — and a newly added metric can refute the theory it was added to support (breaching polls
averaged load 1.77 vs 1.90 for non-breaching, so "the host was busy" is contradicted by its own column;
always compare the two groups, never just cite the values).
**Applies to:** any iteration chasing `GET /api/health` latency during ingest/warm phases; any lane that
cross-checks a UTC measurement against a Trendora log timestamp; any round that adds an explanatory metric.

## iter-67 — 2026-08-12T06:05:00Z

**Verdict:** CONTINUE
**Lesson:** Counting only the polls that cross a threshold hides the stabler signal. This round had
1 breach over 2.0 s (in `coverage_membership_timeline_refresh`) and concluded that the moving breach
location argues against a phase-specific hold — but 120 of the drill's 131 polls over **1.0 s** sat inside
`factor_lab_all_warm` (22.2 % of its 541 polls, mean 0.596 s vs 0.080 s in the next phase), exactly where
iter-66 put its breaches. Whenever a latency claim is made, group the FULL distribution by phase, not just
the ceiling crossings. Second trap from the same round: a "whole-run max" sample is not automatically in
the phase you are discussing — the drill's max `loop_lag_s` (1.382 s) was timestamped 03:13:54 Z, two
minutes BEFORE `factor_lab_all_warm` opened, next to the boot warm-up thread's own cache warms; always
re-read the sample's own timestamp before naming its phase.
**Applies to:** any iteration reporting `scripts/qa/poll_health.py` drills, `logs/health-watchdog.jsonl`
samples, or any phase attribution in `reports/perf-budgets.md`.

## iter-68 — 2026-08-12T07:50:00Z

**Verdict:** CONTINUE
**Lesson:** Before commissioning a new instrument, join the instruments you already have. This round's
"~19.6% genuinely unnamed" residual on the one health-check breach was ~14 points recoverable with zero new
code, by differencing the poller's own send timestamp in `evidence-drill/tc1-health-poll.csv` against the
server's `t_received_wall` in `health-watchdog-slice.jsonl` (0.353 s for the breach; p99 183 ms live vs
1.0 ms idle across the drill). Addendum 34 even printed that 0.353 s offset without converting it into a
share. Corollary from the same round: the instrument was armed only on the developer's own backend, so the
9 worst breaches of the round — caught by the browser lane against a backend with
`TRENDORA_HEALTH_WATCHDOG` unset — carry no attribution at all.
**Applies to:** any iteration adding a timing/diagnostic instrument, and any iteration whose measurement is
taken by one lane while a second lane independently measures the same thing (arm the flag session-wide, and
derive the cross-lane deltas before asking for a new sample type).

## iter-69 — 2026-08-12T10:05:00Z

**Verdict:** ESCALATE
**Lesson:** When a round blames a metric's regression on an external confound, test whether the confound is
distributed the same way the metric is before accepting it. Addendum 35 attributed this round's 8.09 % health-check
breach rate to a concurrent caller (`goal-iter-lean.sh`); grouping the same 952 rows of
`runs/goal-ops-hardening-iter-69/evidence-drill/tc1-health-poll.csv` against `logs/backend.log`'s phase windows
showed 74 of 77 breaches and all 3 non-answers inside `factor_lab_all_warm` (0 of 124 and 0 of 343 in its two
neighbours) while the confound was polling at 0.149 / 0.213 / 0.180 requests per health poll across those same
three phases — uniform, so it cannot produce that split.
**Applies to:** any iteration reporting a performance/availability metric that moved, especially J-07 health-poll
drills — group by ingest phase and report the grouping, and normalize any named confound by the same buckets.

## iter-69 — 2026-08-12T10:06:00Z

**Verdict:** ESCALATE
**Lesson:** A "Do not redo" entry written with a condition attached expires when the condition is met, and nobody
re-reads it to notice. iteration-state's ban read "bounding `factor_lab_all_warm` / `coverage_membership_timeline_
refresh` by code change — diagnostic only **until the handler-body sub-timing names a component**"; iter-69's
sub-spans named two (`readiness_s` 43 of 74 breaches, `preflight_s` 31), so the ban lapsed by its own terms in the
very round that satisfied it. Write conditional bans with their release condition in the same bullet, and check
each one against the round's own results before carrying it forward.
**Applies to:** the goal-evaluator writing `iteration-state.md`'s Do-not-redo list, and any decomposer treating
that list as binding.

## iter-70 — 2026-08-12T15:20:00Z

**Verdict:** CONTINUE
**Lesson:** After sixteen rounds of adding measurement, the round that REMOVED the named suspect from the
request path fixed the metric outright — `readiness_s` p90 fell from 0.5631 s to 0.000003 s and the breach
rate from 77/952 to 0/1,030 at matched phase duration (`factor_lab_all_warm` 564.77 s vs ~572 s). The
non-obvious part is the cost: caching a liveness value bought speed by creating a way to be silently WRONG —
`readiness.py:567-575` serves `_READINESS_CACHE` with no age check, so a dead tick thread would keep
answering 200 with a frozen "ready" forever. When you move a truth-telling computation off a request path,
bound its staleness in the same change, not the next one.
**Applies to:** any iteration that caches, memoizes, or background-refreshes a value the UI uses to state
whether the system is trustworthy (`app.engine.readiness`, preflight verdicts, warmup/background-compute
status) — and any iteration that moves compute off a request path.

## iter-70 (second) — 2026-08-12T15:20:00Z

**Verdict:** CONTINUE
**Lesson:** A full pipeline can reach CLOSURE-PASS while producing ZERO journey evidence. The QA backend on
:8255 shut down cleanly between the QA lane and the browser/replay lanes (`logs/backend.log:292128-292131` —
no traceback, no 5xx), the browser-qa-agent is correctly forbidden from restarting it, and every downstream
gate still passed: browser SKIPPED 0/8, replay BLOCKED 0/7, demo NOT_YET, closure PASS. Worse, the QA report
then recorded "✓ Developer verified via replay" for all seven required journeys — an artifact asserting the
opposite of its own upstream evidence. Never read a `✓` in a QA report as coverage; open the replay results
file the row actually depends on.
**Applies to:** any iteration whose journeys are verified by a lane that depends on a long-lived service —
check the replay/browser results file directly, and treat a clean uvicorn shutdown signature (no traceback)
as infrastructure, never as a product crash.


## iter-71 — 2026-08-12T18:35:00Z

**Verdict:** ESCALATE
**Lesson:** When a round's availability numbers look catastrophic, find out WHICH launcher
produced them before believing the size of the failure. This round's 165-second health-check
outage was measured against `scripts/dev.sh`, whose `exec` line is
`uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT` — no `--limit-concurrency`,
which `scripts/start-backend.sh:107` applies from `config.yaml:1362` (64) and which
`config.yaml:1355-1362` documents as the exact defence against "N connection-holding resolves
that exhaust the pool". The observed failure WAS pool exhaustion
(`QueuePool limit of size 10 overflow 20 reached`). The tell that a round ran on `dev.sh` is
free and instant: `logs/backend.log` stops updating, because `dev.sh` writes no persistent
logfile at all — the real log lands in the harness temp dir (`$TMPDIR/dev-start-*.log`), which
is also the ONLY place the tracebacks, the 500s and the per-phase finalize timings exist.
**Applies to:** any iteration scoring J-04, J-06 or J-07 (all three name prod-mode measurement
conditions, two of them saying "never dev.sh" verbatim); any iteration that cannot find
backend evidence in `logs/backend.log`; any launcher-parity work on `scripts/dev.sh`.

## iter-71 (second) — 2026-08-12T18:35:00Z

**Verdict:** ESCALATE
**Lesson:** Bounding a cached value's staleness by falling back to a synchronous recompute can
convert a slow-but-safe path into a self-amplifying stall. `readiness.py:165-194` serves the
cache while fresh but, past `max_stale_intervals × refresh_interval_seconds` (1.5 s), routes
every request into `_tick_and_cache`, which takes a global `_TICK_LOCK` and recomputes
**without any post-lock recheck** — so N queued requests each pay a full compute serially, and
the slower things get, the staler the cache gets, the more requests take that path. iter-70
removed exactly this compute from the request path and measured 0 of 1,030 breaches; iter-71
put a conditional version of it back and the next drill measured 58 of 900 non-answers. If you
bound staleness, prefer serving the aged value WITH its age disclosed over blocking on a
recompute, and always double-check the cache after acquiring the lock.
**Applies to:** any change adding a cache-staleness bound or a synchronous fallback on a
request path; any future work on `app.engine.readiness` / `_TICK_LOCK` / `GET /api/health`.

## iter-72 — 2026-08-12T23:38:45Z

**Verdict:** CONTINUE
**Lesson:** A connection-pool resize is a MEMORY change, not just a concurrency change, and it
silently voids any evidence-durability carry for a memory assertion. `config.yaml` raised
`pool_size`+`max_overflow` 30 → 68 to fix an availability bug, while `pragmas.cache_size: -262144`
gives each pooled sqlite connection a 256 MB page cache under an unchanged 8192 MB `ulimit -v` —
retained-connection worst case 2.5 GB → 6 GB against a warm whose last recorded VmPeak was 3.69 GB.
Reviewer, QA, auditor and coherence all read the diff and none named it; the availability drill only
ever opened a handful of connections, so the new ceiling was never exercised. Whenever a diff changes
pool size, worker count, or a per-connection/per-thread cache, re-measure peak memory before carrying
any prior memory evidence forward.
**Applies to:** any iteration touching `config.yaml`'s `database.pool_size`/`max_overflow`/`pragmas`,
`server.limit_concurrency`, thread/worker counts, or any per-connection cache — and any evaluator
deciding whether A.6 evidence durability covers a memory/VmPeak step.

## iter-72 (2 of 2) — 2026-08-12T23:38:45Z

**Verdict:** CONTINUE
**Lesson:** When a lane labels its own failures "transient / concurrent load", check the timestamps
and open the frame — the label is a hypothesis, not evidence. This round six replay goldens FAILed
and two artifacts (the merged results row and audit T2) blamed "running concurrently with this
session's own heavy drill". The replay frames are timestamped 22:22-22:24 UTC, ~12 minutes BEFORE the
drill started (22:35:14 UTC), and `logs/backend.log` shows no heavy phase in flight 22:05-22:29 UTC.
`J-07-verify.png` shows the real cause outright: an unstyled, asset-less page stuck at "Checking
backend…" — the QA FRONTEND was serving broken pages. The overturns were still correct; the
diagnosis was not, and a wrong diagnosis means the next round repairs the wrong thing.
**Applies to:** any round reconciling deterministic-replay FAILs against an LLM lane, and any agent
writing a "false positive / host contention" note — cite a timestamp bracket and the frame's contents.
