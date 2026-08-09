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

## iter-49 — 2026-08-05T12:50:00Z

**Verdict:** ESCALATE
**Lesson:** A per-phase log MESSAGE is not a per-phase ATTRIBUTION — read the traceback under it.
`logs/backend.log`'s "evidence drawdown-expectations warm aborted — memory pressure" line at
10:36:03.525 was published in the round's headline report as the ingest finalize tail (this
iteration's own target); the traceback printed directly beneath it reads
`warmup.py", line 198, in _warm_drawdown_expectations` — the BOOT/re-warm path, whose only
distinguishing marker is the word "evidence" vs "ingest" in an otherwise identical message. Getting
this right is what turns audit finding B2 (an uninterlocked second heavy loop) from a theoretical
risk into a proven live contributor to a 12 m 45 s process death.
**Applies to:** any iteration reading `data_manager` / `warmup` finalize-or-warm phase logs, and any
agent attributing a MemoryError or timing outlier to a specific loop — always confirm the frame, not
the message.

## iter-49 — 2026-08-05T12:50:00Z (second entry)

**Verdict:** ESCALATE
**Lesson:** A bound proven on an idle host with a throwaway DB copy is not a bound proven in the
product. This round's 1,200 s termination bound held 3/3 in isolated drills (1,019.6/1,052.5/1,049.2 s
sampler spans) while the SAME job shape in the live app never terminated at all — the difference was
ordinary concurrent page traffic, not code. Record both numbers or the drill becomes a way of passing
without shipping.
**Applies to:** any iteration whose acceptance is a wall-clock or memory bound (J-05, J-07, and any
future perf-budget work) — require at least one measurement through the app's own pages, under
concurrent reads, before the journey moves up.

## iter-50 — 2026-08-06T07:45:00Z

**Verdict:** ESCALATE
**Lesson:** A raw `grep -c MemoryError logs/backend.log` total is an actively misleading metric in
this session and I nearly used it as one. The count went 7,083 → 7,862 this round (+779), which reads
as a catastrophe; segmenting by `start-backend.sh: launching at` banner shows 770 of them are the
developer's own deliberately fault-injected TC-2 memory-pressure drills (segments 13:58 and 14:14),
9 are the browser lane, and **0** are the post-fix TC-1 drill. Always split the count per backend
segment before drawing any conclusion from it.
**Applies to:** any iter scoring J-05/J-06/J-07 or any memory-bounding work; any evaluator or auditor
citing a `logs/backend.log` MemoryError count.

## iter-50 — 2026-08-06T07:45:00Z

**Verdict:** ESCALATE
**Lesson:** Bounding memory cannot close a responsiveness requirement, and this round proved it
cleanly: `compute_factor_lab_all`'s footprint fell 7.76 GB → 3.13 GB with zero MemoryErrors across a
1,522 s concurrent drill, and `GET /api/health` still breached its ≤2 s ceiling 96 times out of 1,179
(worst 10.06 s) in that same drill — because the cause is GIL contention between two CPU-bound Python
computes in one process, not allocation. J-07 step 2 is a *scheduling* problem wearing a memory
problem's clothes; three consecutive iterations aimed memory fixes at it.
**Applies to:** any iter targeting J-07's health-poll ceiling, or proposing a memory bound as the
remedy for a latency/availability journey.

## iter-51 — 2026-08-07T10:05:11Z

**Verdict:** ESCALATE
**Lesson:** Uvicorn access-log lines in `logs/backend.log` carry NO timestamp of their own, so any
"nearest preceding timestamped line" attribution manufactures phantom multi-minute dead windows that
land exactly on the longest CPU-bound phase — because that phase logs only at its end. My first pass
showed a 583 s gap with zero `/api/health` lines during `factor_lab_all_warm`; re-counting the lines
BUCKETED at that anchor found **248** health responses, all 200. Always count access lines per anchor
before claiming an unresponsive window; the wrong reading would have driven a REGRESSION halt.
**Applies to:** any iter scoring J-07/J-05 responsiveness, or reading `logs/backend.log` for outage,
wedge, or latency evidence.

## iter-51 — 2026-08-07T10:05:11Z (second entry)

**Verdict:** ESCALATE
**Lesson:** TC-8/TC-13 ("the journey lane runs LAST, no product-code change afterward") held for the
first time in six rounds, and the reason is that the auditor applied **zero** fixes — it wrote B3/T1
up as findings precisely because editing `apps/backend/app/**` post-lane would have invalidated the
only lane evidence the iteration had. "Fix small things during audit" and "the lane runs last" are in
direct tension; when both are in force, findings-only is the correct resolution and should be stated
as the expectation, not left to the auditor's judgement each round.
**Applies to:** any full-depth iter whose spec carries the TC-8 lane-last sequencing rule.

## iter-52 — 2026-08-08T04:34:46Z

**Verdict:** ESCALATE
**Lesson:** A failed ASGI request leaves **no uvicorn access-log line at all** — grepping
`logs/backend.log` for `500` after line 205000 returns **zero hits** while three genuine
`MemoryError` tracebacks sit in that same range (`compute_regime_lab` ->
`_regime_lab_members_by_horizon`, lines 212191/212240/212296). The only way to find a page whose
data call died is to grep for the *exception frame*, never for a status code. Compounding it:
`J-06.json`'s step 11 asserts `expect.text = "Research — Regime Lab"` — the page HEADING — so the
golden scored PASS on the very load where that page returned no data; `J-06-verify.png` shows the
shell with an empty body.
**Applies to:** any iteration scoring a journey off a golden `expect.text` assertion, and any
log-based availability claim about `apps/backend/` (`ui-test-results.md` rows, `perf-budgets.md`
drill addenda). Assert a value the endpoint must have produced, not a heading the shell renders.

## iter-52 — 2026-08-08T04:34:46Z (second entry)

**Verdict:** ESCALATE
**Lesson:** TC-9 ("the 8-journey lane runs LAST, no product-code change afterward") has now broken
in **six of seven rounds**, and it is an ORDERING property of the pipeline, not a discipline
failure: the lane is dispatched BEFORE audit and audit-fix, so *any* audit finding that needs a
code change breaks the rule automatically. This round it broke maximally — the lane ran 01:41:48
and the iteration's entire deliverable (`research.py` `_cooperative_sorted`/`_cyclic_gc_paused`)
landed at 02:39:48, so the only independent evidence measured a superseded tree and returned FAIL
on both target journeys. Five rounds of restating the rule in the spec have not fixed it; moving
the lane's dispatch to after the audit-fix step would fix it once. Corroborating tell, cheap to
re-derive: the lane's job appears in `perf-budgets.md` as a "**pre-fix** job run" in the
developer's own words.
**Applies to:** every full-depth iteration in this session; any spec author restating TC-8/TC-9;
anyone diagnosing why a round ends `blocked` at `audit_qa_failed` with `browser_checks_run: false`.

## iter-53 — 2026-08-08T09:55:00Z

**Verdict:** CONTINUE
**Lesson:** A pipeline ordering property was fixed by writing it into the iteration spec's own
Definition of Done as a binding rule ("if the audit finds a defect needing a code change, it is filed
as a note for iter-54 rather than applied as a code-changing audit-fix"), not by asking agents to be
more careful. TC-9 had broken 6 of the previous 7 rounds under exhortation; the round it became a DoD
checkbox, it held cleanly — newest `apps/backend/**` mtime 07:05:37 vs earliest lane artifact 08:32:26,
and the auditor deliberately shipped five findings with zero fixes applied. Exhortation does not fix an
ordering property; a machine-checkable spec line does.
**Applies to:** any iteration whose spec depends on stage ordering (browser/replay lane vs audit-fix vs
review), and any recurring process failure that has survived two or more "try harder" rounds — encode it
as a DoD/TC item instead of a reminder.

## iter-53 — 2026-08-08T09:55:00Z (second entry)

**Verdict:** CONTINUE
**Lesson:** Replacing an unbounded fetch with a bounded one is an off-by-one trap whenever the bound
and the consumer speak different units. `market_phase.py:217`/`:554` fetch `lookback_days` bars **by
count** and then filter `bar.date >= d - timedelta(days=lookback_days)` — a **calendar** range that is
`lookback_days + 1` days inclusive — so the oldest qualifying bar can be silently dropped, and the code
comment's "byte-identical" proof is false as stated. The sibling change in `universe_resolver.py` is
correct precisely because it is a count bound feeding a count consumer (`_adv_dollar`'s
`bars[-adv_window_days:]`). The test shape matters just as much: all three new market-phase tests
compare **treated vs treated** (a bare fixture against the same fixture padded with older bars), which
can only prove the window is not too *wide*; nothing can detect "too narrow" except a **treated vs
untreated** comparison, which is what TC-3 actually asked for and what the resolver half did.
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
