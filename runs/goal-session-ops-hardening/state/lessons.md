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

## iter-9 — 2026-07-22T19:05:00Z

**Verdict:** CONTINUE
**Lesson:** A journey can fail its browser lane and have the defect FIXED inside the same iteration, which
leaves every downstream artifact (raw `.llm.md`, merged results, regression-replay-results) frozen at the
pre-fix verdict while the newest evidence sits in an operator note nobody's lane owns. J-04 step 6 hit
exactly this: `UT-10-result.png` shows the real pre-fix "0 snapshots · 0 trading days", the F1
`_checkpoint_run_record` fix landed hours later, and the post-fix proof (run 114 frozen at 59 snapshots /
64-of-84 dates vs. the all-zero control run 113 in the same `GET /api/data` response) exists only in
`runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`. Neither `failing` (cites a build
that no longer exists) nor `passing` (no rendered-surface evidence) is honest — `partial` is. When a fix
lands after its own verification lane has run, the fix does not close the journey; it schedules a
re-verification.
**Applies to:** any iteration where an audit/fix round lands product code AFTER the browser-qa step, and
any evaluation weighing operator/API evidence against a stale lane verdict.

## iter-9 — 2026-07-22T19:05:00Z (second entry)

**Verdict:** CONTINUE
**Lesson:** iter-8's "the margin is comfortable" reading was doubly unsafe, and only iter-9's audit (P1)
caught why: `VmPeak` in `/proc/<pid>/status` is a kernel-maintained monotone high-water mark, so a finer
sampling cadence CANNOT raise it — re-subsampling the 4,347-row trace at 1 Hz and at 10 s yields the
identical 4,738,948 KB. The 43.6% → 24.7% margin narrowing is therefore real growth in peak demand, not a
measurement artifact, and the benign-sounding cadence explanation had to be struck from
`reports/perf-budgets.md`. Never let a plausible measurement-artifact story stand unverified next to a
number that is trending the wrong way.
**Applies to:** any iteration recording VmPeak/VmSize/RSS headroom against `server.memory_cap_mb`, and any
future J-05/AG-8 re-measurement as the price basis deepens.

## iter-10 — 2026-07-22T20:55:00Z

**Verdict:** CONTINUE
**Lesson:** A crash journey can be scored without trusting anyone's narration of the crash: the persisted run
row proves it by itself. `data_provider_runs` id 119 stopped at `dates_done 158 / dates_total 504` (mid-flight by
construction) and its `finished_at` lands 1.3 s AFTER the successor's `=== start-backend.sh: launching ... ===`
banner in `logs/backend.log`, which means the dead process wrote nothing on the way out and the new one's orphan
sweep finalized the row — with no `Shutting down`/`Finished server process [pid]` line anywhere before that
banner (the same log demonstrably records clean shutdowns for other pids). Two related traps this iteration hit:
the first crash rehearsal (run 118) missed because the job self-completed 38 s before the kill — use a range long
enough that the completion buffer exceeds poll-to-kill latency — and the run-summary identity for an INTERRUPTED
run is `snapshots_created + already_snapshotted + error_other = dates_done`, not `= dates_total` (TC-2 as written
assumes a completed run).
**Applies to:** any iteration verifying crash/restart, orphan-sweep or checkpoint behaviour; any spec writing a
run-summary arithmetic assertion that must also hold for partial runs.

## iter-11 — 2026-07-22T21:10:00Z

**Verdict:** ESCALATE
**Lesson:** A browser lane that only reads `performance.getEntriesByType('resource')` cannot tell a
15 ms success from a 15 ms **HTTP 500** — iter-11's lane called `/api/research/event-study` "already
succeeded" and blamed the page's "Backend unavailable" render on ambient host load, while
`logs/backend.log:27660` shows that exact call returning 500 (`RuntimeError: can't start new thread`
after a MemoryError). Always cross-read `logs/backend.log` for the measurement window before accepting
an "environmental, not code" explanation, and rule ambient load in/out with `logs/hwmon/hwmon.csv`
(MemAvailable was 12–20 GB — nothing ambient can consume a process's own `ulimit -v` cap).
**Applies to:** any iteration whose verdict rests on browser-measured latency or on an anomaly
explained away as host contention; also any perf sweep, since the same log read reveals whether the
product's own ingest was running during the measurement.

## iter-11 — 2026-07-22T21:10:00Z

**Verdict:** ESCALATE
**Lesson:** The developer pass writes `reports/perf-budgets.md` *before* the browser lane produces the
numbers, so in a lean pipeline a "measurement iteration" can finish with its measurements living only
in a QA evidence `.txt` and never reaching the artifact the journey's Acceptance names as the single
source (verified by mtime: file 20:24Z, sweep 20:38–20:52Z). Check the artifact's timestamp against
the lane's timestamps before scoring any "recorded in the budgets table" step.
**Applies to:** any iteration whose DoD says "record X in `reports/perf-budgets.md`" while X is
produced by browser-qa rather than by the developer.

## iter-12 — 2026-07-23T02:00:00Z

**Verdict:** CONTINUE
**Lesson:** Closing a journey's EVIDENCE gap is not the same as the journey passing — the evidence can be the
adverse finding. J-06's G1/G2 measurement work was completed correctly and in full, yet the G2 control
reading it produced (`/api/indexes?full=true` at 2.1–2.3 s vs a committed ≤1.5 s budget, on a verifiably idle
host) is exactly the shortfall that keeps J-06 out of `passing`. The audit recommended `passing` because the
work was done; the honest score is `partial` because J-06's own step-2 assertion ("every measurement within
budget") fails. Score on the contract, not on the fact that a measurement happened — and when a real number
contradicts a "may pass" prose recommendation, the number wins.
**Applies to:** any iteration whose target is "measure-and-record" work against committed budgets
(`reports/perf-budgets.md`), and any evaluator tempted to accept a downstream agent's "may be scored passing"
when the recorded measurement breaches the acceptance metric.

## iter-13 — 2026-07-23T04:39:47Z

**Verdict:** REGRESSION
**Lesson:** A carried, byte-unchanged critical anti-goal can REGRESS in observed severity without any
code change: AG-8 (`forward_testing.py:826` unbounded ScannerResult load) was "degraded-but-alive,
mitigation holds, smaller than iter-7" for iters 9/11/12 — then at iter-13, under heavier concurrent
load (4 replay backfills + a diagnostic read on one browser-qa turn), it wedged the entire backend into
a ~12-min futex deadlock needing an operator hard-restart, i.e. back to the original iter-7 full-outage
severity. The "blast-radius-smaller-than-the-acknowledged-incident" argument that justifies deferring a
critical anti-goal is only valid until a heavier load profile falsifies it; an evaluator must re-test
that premise every iteration against fresh load evidence, not carry it forward. When it flips, C.1's
literal "unresolved critical anti-goal → REGRESSION" is the right call even though prior iters deferred.
**Applies to:** any iter carrying an UNRESOLVED critical anti-goal on a "smaller blast radius than the
acknowledged incident" rationale — especially memory/availability bugs whose severity is load-dependent;
re-read logs/backend.log + the audit + closure for a worse-than-before manifestation before re-deferring.

## iter-14 — 2026-07-23T14:25:00Z

**Verdict:** CONTINUE
**Lesson:** Bounding the READS (column-projected `yield_per` streaming) closed the AG-8 memory-exhaustion/
crash dimension with a wide 61.8% margin, but the SAME rewrite surfaced a NEW concurrent-load latency: a
`/backtest` cache-MISS took 211.8s during a concurrent forward-aggregate warm (audit F1 hypothesis — a
streamed cursor holds a longer read-lock window under concurrent writes than the old fetch-and-release
`.all()` did). A memory fix and a lock-contention fix are different problems; proving the former (flat
VmPeak, health 200) does not prove the latter, and only a browser pass under the EXACT concurrent trigger
exposed it — neither TC-4 (concurrent-on-fixture, no cap) nor TC-5 (sequential-on-deep-basis) reproduces it.
**Applies to:** any iter that replaces a `.all()` fetch-and-release with a streamed/`yield_per` read on a
hot path shared by concurrent ingest writers — measure latency under concurrent load on the deep basis, not
just peak memory.

## iter-15 — 2026-07-23T18:00:00Z

**Verdict:** STALLED
**Lesson:** A small-fixture concurrency ratio does not extrapolate to a deep-basis cost. The 60k-row
fixture's 9.91x same-key stacking ratio predicted the single-flight de-dup would "fully account for" the
211.8s finding; the live deep-basis pass showed stacking was only ~15.6% and the dominant ~84% is ONE
cold full-basis `compute_forward_aggregates` pass (178.74s) a wrapper-scoped fix cannot touch. When a
targeted fix's own live evidence contradicts its root-cause extrapolation, the root-cause conclusion is
the thing to trust the LIVE number over — and the investigation *reaching* "this is a hard architectural
cost" is itself the terminal deliverable that hands the decision to the owner, not a bug to re-attempt.
**Applies to:** any iteration proposing a wrapper/cache/concurrency fix validated on a synthetic fixture
before a deep-basis pass; any "the fix fully accounts for X" claim not yet reconciled against a live
full-scale measurement; future decomposers tempted to loop CONTINUE on an owner-owned direction decision.

## iter-16 — 2026-07-23T23:20:00Z

**Verdict:** CONTINUE
**Lesson:** Removing a request-path compute silently changes what the page shows when the *identity*
moves, not just when the version moves. `resolved_forward_aggregate_evidence` resolves all three serving
states inside ONE `asof_key` (`forward_testing.py:1209`), while the default `/backtest` view resolves to
`max(ScannerRun.asof_date)` (`backtest.py:70`) — so the common single-latest-date ingest advances the
as-of into a key with no rows and the page shows an EMPTY evidence section, where the old code would have
blocked and eventually served real numbers. Neither the operator's live pass nor browser QA could catch it
because both backfilled *historical gap* dates (2025-05-22 / 2025-05-20), which leave the latest as-of
fixed — the only shape either lane ever exercised.
**Applies to:** any iteration adding a cache/precompute layer keyed on a derived identity (`asof_key`,
`dataset_version`, tenant, run id) — enumerate the ways the *identity* can move, not just the ways the
*value* can go stale, and make sure the live test exercises the identity-advancing shape, not only the
convenient one.

## iter-16 — 2026-07-23T23:22:00Z

**Verdict:** CONTINUE
**Lesson:** Four gates (review, QA, browser-QA UT-02/UT-09, ux-regression) all checked the new refreshing
banner for tone, colour token, position and heading, and all passed it — while it asserted two things that
were factually false ("a newer dataset version is still being warmed"; "this updates automatically"). No
lane's checklist contained "is the sentence true?", and the second claim is false in *every* case (the
page's only fetch effect depends on `[asOf, readiness]`, which never changes — browser QA's own UT-04
needed a manual reload). Status-disclosure copy is a testable assertion about system state, not styling.
**Applies to:** any iteration adding user-facing status/progress/explanatory copy — verify each sentence
against the code that would have to be true for it, the same way a displayed number is verified against
the engine (AG-3's discipline, applied to prose).
