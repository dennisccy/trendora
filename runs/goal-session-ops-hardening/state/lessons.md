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

## iter-28 — 2026-07-27T20:45:00Z

**Verdict:** CONTINUE
**Lesson:** A config default pointing at ANOTHER goal session's folder
(`data_quality.drift.report_path` -> `runs/goal-session-mcp-loop/state/drift-report.json`) silently
poisoned this session's J-06 golden for two iterations: a closed session's artifact flipped the preflight
verdict, and the journey read as a product regression when nothing was wrong. Two rules came out of it —
per-session diagnostic artifacts belong under the session's OWN `state/` dir (the ledger-family paths that
goal.md deliberately roots at project level are the exception), and a golden `expect` must assert stable
content (a card heading), never a status/verdict string. Separately: a lean spec called
`test_readiness.py -k drift` "fixture-free" and it silently pulled the 30-year `loaded_engine` fixture,
costing 1h37m — verify that claim by reading the fixtures, not by the selector's name.
**Applies to:** any iteration that adds a `_DEFAULT_*_PATH` constant or a `config.yaml` path, writes or
repairs a journey-script `expect`, or budgets a "small" backend pytest selector.

## iter-28 — 2026-07-27T21:20:00Z

**Verdict:** CONTINUE
**Lesson:** A QA agent's account of a concurrency test can be wrong about WHICH requests it observed while
still being right about the outcome. Here the report described "two concurrent requests" on 2018-03-15, but
`logs/backend.log`'s `backtest_timing` lines show four overlapping requests in two pairs, and the pair the
report timed (273435.90 / 273479.83 ms) carried `write_taken=False` on both — an EARLIER pair
(206104.88 `write_taken=True`) wrote `scanner_runs` 1873 at 19:01:47. Read `write_taken` plus the row's
`created_at` before crediting or doubting a create-once race claim; the row count in the database is the
real verdict, not the narrative's request count.
**Applies to:** any iteration whose QA claims a concurrent-request or create-once result; any change to
`forward_testing._insert_run_forward_returns` / `data_manager._scanner_run_exists`.

## iter-29 — 2026-07-29T00:23:10Z

**Verdict:** CONTINUE
**Lesson:** A memory bound can ship green and bind nothing. This iteration chunked
`research._factor_observations` by reusing `research.read_batch_size` (2000, a ROW knob) as a RUN-count chunk
width; against a live basis of only 1,812-1,871 distinct runs per horizon the loop produced exactly ONE chunk
and peak accumulator size was 0.0% below the pre-fix figure at all five horizons. Every unit test passed,
because they all drove an artificial 2-run width — they proved the MECHANISM, never the SHIPPED PROPERTY. The
audit caught it only by measuring against the real DB and then added a test that pins the shipped config value
against the real run count (`test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`, RED/GREEN
proven at 2000 vs 100).
**Applies to:** any iteration that claims a memory/size bound — the test must assert the bound at the REAL
`load_config()` value against the REAL basis, not at a fixture-sized knob. Also: never reuse an existing
config knob for a new dimension whose UNIT differs (rows vs runs vs bytes) — give it its own key.

## iter-29 — 2026-07-29T00:23:10Z

**Verdict:** CONTINUE
**Lesson:** A golden replay script can be silently weakened to match a degraded product. The browser-QA lane
rewrote `journey-scripts/J-07.json`, dropping its `expect "Ready"` step because readiness is now stuck at
`initializing` (boot warm-up MemoryError at `warmup.py:194`), and recorded that only in a "Known Issue" note.
The rewrite was defensible in isolation, but it removed the one assertion that would have surfaced the
regression to the replay lane — and a reader of the merged results file would see 8/8 PASS with no hint. The
same run's merged `ui-test-results.md` also OVERWROTE the earlier one that carried the Factor Lab UT-07 FAIL.
**Applies to:** any iteration where a golden script is rewritten or a merged results file is regenerated —
the evaluator must diff the golden against its prior version and treat a REMOVED assertion as a status
signal, not housekeeping; QA reports that regenerate a merged file should preserve prior FAIL rows.

## iter-30 — 2026-07-29T03:05:00Z

**Verdict:** CONTINUE
**Lesson:** The canonical merged results file silently reported "PASS 6/6" while the authoritative
browser-QA report said "FAIL 3/5" — `merge_ui_test_results.py`'s `_ROW_RE` matches only `UT-`-prefixed
test ids, browser-qa emitted `TC-01..TC-07`, so all its rows were dropped AND its FAIL headline was
discarded (the fallback never fires when the *other* input file's rows parse). Never accept the merged
`ui-test-results.md` headline without opening the sibling `.llm.md`; and never treat an agent's prose
claim that it "executed X and it passed" as evidence — the auditor's TC-07 replay claim this iteration
left no artifact in `reports/`, `runs/`, the repo or TMPDIR.
**Applies to:** every evaluation that reads a merged `ui-test-results.md`; any iteration whose browser-QA
lane emits non-`UT-` test ids; any verdict that would rest on an audit-or-dev self-report rather than an
openable file.

## iter-30 — 2026-07-29T03:05:00Z (second entry)

**Verdict:** CONTINUE
**Lesson:** A memory bound can be real, measured, byte-identical — and still leave the crash in place,
because it bounded the containers NEXT TO the failing allocation rather than the allocation itself. Here
`ret_by_run_symbol`/`mdd_by_run_symbol` were chunked (-16.4% traced peak, -21.6% RSS) but `stock_obs`
(`forward_testing.py:988`) — the literal frame of the production `MemoryError` — was left unbounded
because bounding it required re-pinning `_attribution_slices`'s frozen test-asserted signature. The same
shape repeats one module over: `research.py`'s `_all_factor_observations_by_horizon` bounded its
accumulator at iter-29 and still crashes at `pools[h].append` because the RETURN VALUE is unbounded by
design. When scoping a memory fix, name the exact frame from the traceback and require the plan to bound
THAT — an "unbounded by design return shape" is not out of scope, it is the bug.
**Applies to:** any iteration bounding memory in `forward_testing.py` / `research.py`; any plan whose
IN SCOPE lists containers to bound — check each one against the failing traceback frame before accepting
"partial scope, disclosed".

## iter-31 — 2026-07-29T07:05:00Z

**Verdict:** CONTINUE
**Lesson:** `scripts/start-frontend.sh:28` execs `npx next dev` — the project's own "prod mode" frontend
launcher (named as such by J-06 step 1 in `docs/goal.md`) has always run Next.js in DEVELOPMENT mode, and
`ps aux` confirms `next dev -p 3255` served every screenshot in this run. That makes J-06's one remaining
step — a real-browser time-to-interactive sweep — unmeasurable as specified: dev mode compiles routes on
demand, so any TTI it produces is a compile time, not a page-load time. It also explains the red Next.js
"1 error" dev-overlay pill that appears in browser-QA captures and that the QA report keeps describing as
"zero console errors". Nobody caught this in 31 iterations because the sweep was deferred every time.
**Applies to:** any iteration that measures page-load/TTI performance, writes to `reports/perf-budgets.md`,
touches `scripts/start-frontend.sh`, or reads a browser-QA "zero console errors" claim from a screenshot
carrying a dev-overlay error pill.

## iter-31 — 2026-07-29T07:05:00Z (second entry)

**Verdict:** CONTINUE
**Lesson:** A memory "bound" can be a constant-factor win wearing a bound's clothes. The shipped fix
re-encoded `_all_factor_observations_by_horizon`'s return value (dedup'd `core_records` + compact per-horizon
tuples) and genuinely stopped the live crash — but it still holds all 5 horizons' pools resident at once, so
the audit measured 769 MB vs 2,025 MB: a 2.63x reduction, with the `horizons x observations` term intact.
The related trap: the shipped TC-6 "proves the bound" test was only a range check on a config integer and
would have stayed green after a full revert of the redesign; the auditor had to write the test that actually
deep-sizes the returned structure. Ask of any memory-bound claim: which term did it remove, and would the
test fail if the fix were reverted?
**Applies to:** any iteration claiming to bound an accumulator, pool, or return value; any DoD item worded
"proven by a dedicated unit test".

## iter-32 — 2026-07-29T09:45:00Z

**Verdict:** CONTINUE
**Lesson:** When a refactor lifts a function's signature, the byte-identity "reference oracle" that is
supposed to pin the OLD behavior gets updated too — and then both sides of the comparison run the NEW
code. That is exactly what shipped here: `_reference_compute_forward_aggregates` called the new
`_attribution_slices`, so for 1 of its 10 compared keys it was self-comparing. A mutation probe (swap
`contributors`/`detractors`) passed 47/47 before the auditor restored the verbatim pre-change bodies as
`_reference_*` helpers, and fails 39 after. An oracle that is edited to compile against new code has
stopped being an oracle; pin the old body from `git show HEAD:<file>` instead.
**Applies to:** any iteration that changes a signature which a byte-identity / golden-output test also
calls — especially `apps/backend/app/engine/forward_testing.py` and
`apps/backend/tests/test_forward_testing_aggregates_streaming.py`.

## iter-32 — 2026-07-29T09:45:00Z

**Verdict:** CONTINUE
**Lesson:** Two evidence artifacts in this session are quietly brittle for the same reason — they assert
values that legitimately move. The rewritten `runs/goal-session-ops-hardening/journey-scripts/J-07.json`
now asserts the literal `n=8869` on `/backtest`; that sample size changes the moment history deepens, so
the next backfill turns J-07's golden into a FAIL for a non-defect reason. Separately, a memory test that
measures a WHOLE function cannot isolate the term under test: the developer's first TC-1 failed against
correct code because tripling run count alone grew a pre-existing `run_rows` materialization ~2.96x,
which was nearly the entire signal.
**Applies to:** any iteration writing or rewriting a golden journey script (prefer structural/label
assertions over computed figures, or record the figure's provenance), and any iteration asserting a
memory bound (measure the named term in isolation, not the whole call).

## iter-33 — 2026-07-29T23:20:00Z

**Verdict:** CONTINUE
**Lesson:** A launcher label that contradicts its own code silently invalidated every
page-performance number for 33 iterations: `scripts/start-frontend.sh` execed `npx next dev`
while goal.md, `measure-perf.sh`'s header and the script's own comment all called it "prod mode".
Fixing it and then actually running the required measurement immediately surfaced a real P1 that
no unit test, golden replay or curl proxy could see (`/research/regime-lab`'s cold view sitting
on an unlabelled skeleton for 60-90 s, once returning HTTP 200 with the body "Internal Server
Error") — the measurement step was the defect detector, not paperwork. Corollary worth carrying:
when two consecutive evaluators put the SAME unblocker first, doing it as its own iteration paid
for itself in one pass.
**Applies to:** any iteration that measures page-load/TTI or writes to `reports/perf-budgets.md`;
any iteration touching `scripts/start-frontend.sh` / `start-backend.sh` / `dev.sh`; and any spec
whose acceptance names a measurement — schedule the measurement expecting it to FIND something,
and leave fix-mode room for what it finds.

## iter-34 — 2026-07-30T01:05:00Z

**Verdict:** CONTINUE
**Lesson:** A saved log EXCERPT is not the log. `mem-drill/pass6/drill-log-excerpt.txt` is cited by
`reports/perf-budgets.md`'s TC-8 row as "the source for every claim above", but it contains zero
`/api/health` lines — so it cannot corroborate TC-3 ("the SAME process kept serving health after the
abort"), the single most important claim of the drill. The real `logs/backend.log` does corroborate it
(14 post-abort health 200s inside the throwaway process's own boot section, 137264-137369, bounded by the
next boot banner). Whoever saves a verbatim excerpt as drill evidence must grep it for EVERY claim it is
going to be cited for, and whoever reads one must re-bound the same window in the source log.
**Applies to:** any iteration that proves a liveness/recovery property from a log excerpt, and any
evaluator scoring a drill (memory pressure, concurrency, crash recovery) whose evidence is a trimmed file
rather than a line range in the live log.

## iter-34 — 2026-07-30T01:05:00Z

**Verdict:** CONTINUE
**Lesson:** The reason the induced-memory-pressure drill finally worked after 20 iterations of deferral
is that it stopped trying to break the REAL basis. iter-32 measured the bounded warm as adding ZERO
VmPeak growth at the live 590-symbol/30-year scale, so tightening `server.memory_cap_mb` far enough to
matter kills BOOT, never the warm specifically — the drill is unreproducible there by construction. A
throwaway synthetic DB, launched through the real `scripts/start-backend.sh` so every host-guard cap
still applies, isolates the target frame at a cap (970 MB, ~73 MB over baseline) that leaves the rest of
boot intact. One non-obvious detail made the difference and is worth reusing: the fixture seeds
`setup_status="Avoid"` rather than `"Actionable"`, because Actionable rows make `research_hot_keys`'s
warm — which has a GENERIC, non-`MemoryError`-specific except — the first thing to fail, so the drill
would exercise the wrong handler and look like a pass.
**Applies to:** any future drill that must induce a specific failure inside one loop of a multi-stage
finalize hook; check which stage runs first and whether its except clause is specific enough to attribute
the result.

## iter-35 — 2026-07-30T02:05:00Z

**Verdict:** ESCALATE
**Lesson:** An `evidence`-depth dispatch paired with a spec whose Definition of Done requires code
produces a guaranteed-FAIL iteration that looks like a regression but is not: no developer runs, so
browser-qa measures the product against work nobody was asked to do, and it scores the target
journeys FAIL on grounds that are the *iteration's* scope rather than the *journey's* goal text.
Check `iter-<N>/depth-dispatched` against the spec's own `Depth:` metadata and `.steps/` contents
BEFORE reading any verdict — if only `decomposer.done` and `browser-qa.done` exist, every "FAIL"
row needs re-reading against `docs/goal.md`, not against the spec's DoD.
**Applies to:** any iteration whose `.steps/` lacks `developer.done`; any evaluator reading a
browser-qa FAIL whose Expected column quotes the iteration spec rather than the journey text.

## iter-35 — 2026-07-30T02:05:00Z (second entry)

**Verdict:** ESCALATE
**Lesson:** A finding classified `minor` on a stated, checkable premise must be re-read against that
premise every iteration, because the premise can die without the code changing. iter-33/h said in
its own text "no such lab is measured slow today" and iter-29/d rested on "no memory is exhausted";
one heavier live scenario (a long-lived process that had already run a backfill, then 5 concurrent
warms) falsified both at once — four labs caught slow behind unlabelled skeletons, and VmPeak at
exactly the 6,291,456 kB cap with 4 MemoryErrors. Reversing a journey's pass on a falsified premise
is NOT goalpost-moving; carrying the old wording forward would have been the dishonest move.
**Applies to:** any evaluator carrying an anti-goal finding whose severity rationale contains a
"nothing is failing today"-style clause — re-test the clause, do not re-copy it.

## iter-35 — 2026-07-30T02:05:00Z (third entry)

**Verdict:** ESCALATE
**Lesson:** browser-qa's prose and its own attached screenshots can disagree in the direction of
*more* severity, not less. Its J-06 text said the four sibling labs "render correct data
(functionally fine)"; all four attached PNGs show bare grey placeholders. The tie-breaker that
settled it was the backend log: zero completed `/api/research/*` access-log lines in the whole
process window (uvicorn logs on completion), proving those fetches were still in flight rather than
fast. Cross-check a "page renders fine" claim against the server's own access log for the same
minutes.
**Applies to:** any journey scored on a "the page loaded correctly" claim where the screenshot shows
a skeleton, spinner, or empty card.

## iter-36 — 2026-07-30T08:45:00Z

**Verdict:** ESCALATE
**Lesson:** `.steps/` marker presence does NOT tell you which lanes ran, and the binding iter-35
lesson ("check `.steps/` before trusting a verdict about the predecessor iteration") will manufacture
a false alarm if applied literally. iter-36 ran the FULL pipeline yet carries only
`decomposer.done` + `coherence.done` — exactly the same two markers as iter-32, which was also full —
because `developer.done` / `review-1.done` / `browser-qa.done` are written by the LEAN executor, not
by the full pipeline. The reliable check is `iter-<N>/depth-dispatched` plus the artifact set and its
timestamps (dev handoff, review, replay, QA, browser-qa, demo, audit, closure).
**Applies to:** any evaluator or decomposer reasoning about whether a predecessor iteration actually
built something; any future edit to the iter-35 lesson's wording.

## iter-36 — 2026-07-30T08:45:00Z

**Verdict:** ESCALATE
**Lesson:** A browser test plan that deliberately takes the backend DOWN must schedule those tests
LAST. iter-36 ran its four "Backend unavailable / Retry" tests in the middle of the plan, could not
get permission to restart the backend afterwards (three attempts denied), and thereby lost two P1
regression tests (`UT-13` `/data`, `UT-14` `/evidence`) AND the entire J-07 journey verification —
the iteration's own Definition-of-Done item 1 — even though every line of shipped code was sound. An
irreversible teardown placed early converts one permission denial into a whole journey's missing
evidence.
**Applies to:** any `ui-test-plan` containing backend-down / service-kill steps; any iteration whose
target journey needs a live backend after an error-state test.

## iter-36 — 2026-07-30T08:45:00Z

**Verdict:** ESCALATE
**Lesson:** `closure_gate.py:71-74`'s backend-only guard is a bare regex
(`backend-only|no user-visible|no visible changes|frontend present:\s*no`) over
`user-visible-changes.md`, so a CORRECTLY written document that documents four changed pages and then
labels its backend-only portion "Backend-only:" fails the gate as if it had claimed no visible
changes. iter-36 halted at `closure_failed` on exactly that single word. The guard needs to test the
document's CLAIM, not the presence of the phrase.
**Applies to:** any iteration mixing frontend and backend work whose ui-impact documents scope the
backend half explicitly; any fix to the closure gate.

## iter-37 — 2026-07-30T12:05:00Z

**Verdict:** ESCALATE
**Lesson:** A drill can execute every named step and still measure nothing, because the changed
code is *conditional on runtime state*. Both of this iteration's live drills missed it: the
step-1/3 warm was triggered from `GET /api/backtest` (a daemon-thread path with no `JobProgress`,
so `prog._shared_bar_cache` was never set), and the step-4 pressure drill used a `dates_total: 0`
backfill, so `_do_backfill` returned before its prefill and `cache_ctx` resolved to
`nullcontext()` — the new `with cache_ctx:` wrap was lexically present and semantically a no-op,
which the handoff then cited as proof the wrap works. Any perf/memory drill on a conditional code
path must ASSERT the condition was live (log the cache identity, assert `cache_ctx is not
nullcontext`, or assert a non-zero target count) or its evidence is vacuous. Second, smaller
lesson from the same diff: moving a `finally:` release to a later stage requires enumerating every
path between the two stages — `_do_backfill` -> `_refresh_ingest_aggregates` has three
intermediate writes plus a `Session(eng)`, any of which skips the hook, and `_JOBS` never evicts,
so the ~1.13 GB would have been pinned for the process lifetime (audit B1; both the reviewer and
QA passed it).
**Applies to:** any iteration measuring memory/performance on a path guarded by a stashed
reference, an attach/fallback context, or an early return; and any change that moves a resource
release from one stage's `finally` to a later stage's.

## iter-38 — 2026-07-30T16:05:00Z

**Verdict:** ESCALATE
**Lesson:** A drill that must PROVE a failure mode and a drill that must COMPARE two arms are different
experiments, and merging them silently kills the first. `mem-drill/config.scratch.yaml:1363` raised the cap
3072 -> 4608 MB with the honest reason "widened so BOTH arms complete gracefully" — correct for the
comparison, fatal for J-07 step 4, because both arms then finished `ok` and the per-item `MemoryError`
isolation handler never ran. Nobody noticed until the audit: the iteration shipped an "induced-pressure
drill" that induced no pressure.
**Applies to:** any iteration whose spec asks one run to both measure a delta AND assert a failure-handling
path — split them into two runs, and state the cap/threshold each one needs before touching either.

## iter-38 — 2026-07-30T16:05:00Z

**Verdict:** ESCALATE
**Lesson:** The deterministic replay lane cannot tell "product broken" from "backend not running", so it
emitted 6 FAILs out of 7 that were pure noise — I only caught it by opening `J-01-verify.png` and
`J-04-verify.png` and seeing the "Backend unavailable" page in both. The lane then costs more than it
saves: an LLM re-run has to overturn it every iteration, its reconciliation footer under-reported its own
overturns (omitting J-05 and J-04), and the one journey the LLM lane could not cover (J-04) silently went
unverified behind the noise.
**Applies to:** any iteration reading `regression-replay-results.md` — check the failure screenshot for a
service-down page BEFORE treating a replay FAIL as a regression signal; and any work on
`demo_runner.py --mode verify` should make it probe `/api/health` first and report BLOCKED, not FAIL.
