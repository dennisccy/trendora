# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-07-23T09:14:48Z: moved 12 entries (keep-iters=5) -->

## iter-0 — 2026-07-19T15:19:32Z

**Verdict:** CONTINUE
**Lesson:** J-01's real blocker is NOT the obvious missing exclusion-reason schema but the
cadence gate: `_do_backfill` (`data_manager.py` ~:2496) filters every backfill through
`_cadence_allowed_dates`, and because `snapshot_cadence.daily_start` is `2026-06-01`, the exact
goal.md-suggested May 2026 range (and J-05's 2026-05-15 single-day date) both compute
`dates_total=0` and ingest nothing. So J-01 and J-05 share ONE root cause — "requested range
always wins" must land before either journey can even be exercised. Secondary: the iter-25 prose
in `reports/perf-budgets.md` claims `start-backend.sh` applies a `ulimit -v` cap, but the current
script applies none (confirmed by source read + `/proc/<pid>/environ`) — whoever builds J-04's
memory-cap enforcement must not assume that doc reflects reality.
**Applies to:** any iter touching `data_manager.py` `_do_backfill` / `_cadence_allowed_dates`
(build J-01's explicit-request override before J-05); any iter building J-04's logfile/memory-cap
layer in `scripts/start-backend.sh`.

## iter-1 — 2026-07-19T19:21:22Z

**Verdict:** CONTINUE
**Lesson:** A new persisted numeric-display field's honesty risk lives in its NOT-YET-COMPUTED and
mass-failure edges, not its happy path. The breakdown fields (`calendar_days` etc.) were exact on
completed backfills but (a) served a fabricated literal `0` on interrupted/job-start rows — because
`_create_run_record` serializes `_run_detail(prog)` while `prog` is still at dataclass defaults and
the orphan-sweep freezes that row without recomputing — and (b) `error_other = len(date_failures)`
silently under-counted past the 20-sample cap. Both are direct AG-3 hits; the browser-qa's exact
DOM reads found (a) and the audit found both, yet the reviewer rated (b) MINOR/out-of-scope and QA
did not act — so DO NOT rely on reviewer/QA alone to catch honesty edges on a new field. Fix
pattern: gate each field's serialization on "actually computed" (a sentinel like `calendar_days>0`)
and mirror the existing bounded-sample/`_total` split (`omitted`/`omitted_total`) for any count.
**Applies to:** any iter adding persisted/served numeric fields to `data_provider_runs` /
`JobProgress` / a run-summary or aggregate payload (J-05's `coverage_snapshot` finalize hooks next
cycle) — cover the interrupted/orphan-sweep and >sample-cap paths, not just the happy path.

## iter-2 — 2026-07-20T06:06:21Z

**Verdict:** CONTINUE
**Lesson:** Keying a served ingest-time cache on a LIVE dataset fingerprint (`coverage_snapshot`'s
`dataset_version` = `_membership_dataset_version`, embedding bar/symbol/run counts) means ANY
count-changing ingest silently invalidates EVERY cached row for every as-of — and if some ingest
kinds are (correctly, per scope) excluded from the refresh hook, the read path serves the
honest-empty all-zero sentinel for a fully-populated DB until a restart or backfill re-persists. Two
individually-correct decisions (exclude `fetch`/`expand` from the finalize hook; key on a fingerprint
for byte-identity) compose into an emergent AG-3-class false-zero on the DEFAULT `/data` view (audit
B1, live-reproduced in UT-07 when a fetch landed 1 bar). The offline "fetch is always zero-work"
assumption also proved false — the committed fixture had a landable 2026-07-17 bar.
**Applies to:** any iter warming/serving an ingest-time cache keyed on a dataset-version fingerprint —
EVERY count-changing ingest path (fetch/expand/remove-data too) must refresh it or the sentinel must
do a cheap real existence check; verify the fetch-then-view path, not just backfill-then-view.

## iter-3 — 2026-07-20T11:20:00Z

**Verdict:** CONTINUE
**Lesson:** A tightly-scoped, correct backend fix (B1/B2, independently audit-verified) can still
fail to advance its target journey to `passing`, because the FIRST iteration to drive a realistic
load pattern (a heavy rebuild + a real fetch) through the browser exposes latent trust-surface
defects on SHARED components that no prior iteration exercised: B3 (`app/engine/readiness.py:129`
`latest_servable` flips the app-wide badge to a crash-identical false "Backend unavailable"/NO-GO
when a fetched bar out-dates the latest snapshot) and F1 (`_refresh_ingest_aggregates`'s per-date
loop emits no `tick()`, so the job heartbeat freezes → false "possibly stalled"). Both are
pre-existing and out-of-scope, but they gate a clean journey pass. Second lesson: the QA report
claimed a clean 12/12 and marked TC-11 PASS on a STATIC page load, burying the raw browser-qa FAIL
— only the audit (T1) and closure caught it. Always cross-check the QA verdict against the raw
`ui-test-results.md` browser verdict; never score a target journey clean on backend-correctness
alone.
**Applies to:** any iter that first drives a new load pattern (heavy job / real fetch) through the
browser; any iter touching `app/engine/readiness.py`, `_refresh_ingest_aggregates`, or the shared
`HealthBadge`/`PreflightBanner`/`JobProgressPanel` status surfaces; any eval where the QA PASS and
the raw browser-qa verdict diverge.

## iter-4 — 2026-07-20T15:02:47Z

**Verdict:** CONTINUE
**Lesson:** `merge_ui_test_results.py` silently corrupts the merged
`reports/phase-<iter>-ui-test-results.md`: it DROPS the raw browser-qa `## Notes` section (even
though the merged table cells still say "see Notes for the one caveat" 3×) and mis-sums the header
("12/13 journeys passed" over a 13-row all-PASS table). Those Notes hold the load-bearing caveats
(UT-03's DEGRADED-banner-is-unrelated-drift explanation, UT-04's blank-tiny-screenshot disclosure,
UT-08's architecturally-unreachable-precondition scope adjustment). The fix: read the raw
`reports/phase-<iter>-ui-test-results.llm.md` directly — which is exactly this session's own iter-3
lesson, now shown to be un-followable from the merged file alone. The closure auditor independently
reached the same finding.
**Applies to:** any future goal-evaluator reading browser-qa results for this repo while the merge
script stays unfixed — whenever the merged `ui-test-results.md` references a `## Notes` section it
does not contain, open the `.llm.md` sibling before scoring any target journey.

## iter-5 — 2026-07-20T22:45:00Z

**Verdict:** CONTINUE
**Lesson:** curl-based perf measurement systematically UNDER-reports real page latency: the developer's
harness measured /api/indexes?full=true at 0.79–0.95s (in-budget) while a real browser hit 1.68–2.19s
(over-budget, 3/3) because Chrome caps at 6 connections/origin against HTTP/1.1 uvicorn and the Dashboard
fires 10-13 same-origin calls in one ~10ms window. Any "pages load within budget" journey must be scored
on browser-measured latency, not curl — and a page's TOTAL on-load call fan-out is itself the risk, not
just each endpoint's isolated cost. Two endpoints (/api/indexes, /api/data/availability) are in this class.
**Applies to:** any iter measuring or asserting page-load performance budgets; any iter adding on-load API
calls to an already call-heavy page (Dashboard, Data Manager).

## iter-5 — 2026-07-20T22:45:00Z

**Verdict:** CONTINUE
**Lesson:** deterministic golden-script replay assertions that check for a hard-coded historical value on a
GROWING unpaginated list go stale silently: J-01's step-6 expected "2026-05-15" on /scanner-runs, but the
run history grew from ~180 (when the script was authored, iter-1) to 750 rows, pushing that date below the
fold / past the runner's step timeout — producing a FAIL that looks like a regression but is a test-harness
artifact (the run row still exists; the display path was untouched). A required-still-passing replay FAIL
must be adjudicated (DB query + is-the-code-path-in-the-diff check + screenshot), not auto-treated as
REGRESSION — and golden scripts should assert on data the journey's own action produces, not on a fixed
proxy row on a page the journey doesn't change.
**Applies to:** any iter whose measurement/backfill runs add rows to /scanner-runs or /api/runs; any
goal-evaluator triaging a required-still-passing deterministic-replay FAIL with no LLM-fallback adjudication.

## iter-6 — 2026-07-21T01:43:56Z

**Verdict:** CONTINUE
**Lesson:** A page can be "within its committed budget" on the shipped seed yet violate the journey's
intent on the basis the session actually runs: `/evidence`'s one-time cold recompute is ~9.5s on the
170k-row seed but ~73s on the accumulated ~1.5M-row live dev DB (UT-13 real-browser 73.5s vs 0.02s warm
curl), because `event_study_cache`/`drawdown_expectations` are lazy-warmed and any dataset change (e.g.
this cycle's own verification backfill) invalidates them. Item I's "warm ≤3s + bounded cold miss" clause
technically covers it, but for the LAST Must-have journey ("pages load only what they need") the honest bar
is first-view-in-budget on the grown basis — warm the hot keys at ingest finalize, don't lean on the
cold-miss clause. Also: iter-5's own curl-under-reports lesson recurred in reverse — the same page's first
handoff numbers (555s/92s) were contamination artifacts (concurrent 84-min pytest + stale cache), so
re-measure on an IDLE host before filing OR retracting a "severe regression."
**Applies to:** any iter closing J-06 / touching a lazy-warmed derived cache (event_study_cache,
market_phase_cache, drawdown_expectations); any perf claim measured while a heavy pytest/ingest runs concurrently.

## iter-7 — 2026-07-21T08:10:00Z

**Verdict:** REGRESSION
**Lesson:** An upstream audit that reasons about "orthogonality" (frontend/boot/readiness untouched →
"cannot have regressed those journeys") can be empirically WRONG when the diff touches a shared
hot-path function: iter-7's `_refresh_ingest_aggregates` warm looked orthogonal to J-05, but it runs
7 synchronous `compute_drawdown_expectations` calls on the ingest FINALIZE path — exactly J-05's
"health responsive during heavy ingest" window — and browser-qa caught a 7-min health hang + MemoryError
at the enforced 6144MB ulimit that the audit (which ran before browser-qa and never exercised that step)
declared impossible. Adding ANY synchronous per-item compute to the ingest finalize hook is a memory/
availability risk on the grown live DB, not a free timing move — its peak-RAM cost must be measured
during a real back-to-back heavy ingest, not just unit-tested.
**Applies to:** any iter that adds work to `_refresh_ingest_aggregates` / the ingest finalize hook, or
any "warm-a-cache-earlier" change; any iter where the audit runs before browser-qa and asserts a required
journey is orthogonal to the diff — the evaluator must still weight the live browser evidence over the
orthogonality argument.

## iter-8 — 2026-07-21T23:53:18Z

**Verdict:** CONTINUE
**Lesson:** `Frontend Present: no` in the iteration spec's Goal Mode Metadata caused the whole browser-qa
lane to be skipped (`ui-test-results.md` = "SKIPPED — Backend-only phase", `status.json`
`browser_checks_run: false`, no evidence directory at all) — even though the SAME spec's DEFINITION OF DONE
item 1 and TESTING REQUIREMENTS made a browser-qa pass over J-05's four acceptance steps the entire reason
the iteration existed. "No frontend CODE changed" is not "no journey needs browser verification": J-05's
regression was itself caught by a browser screenshot of a frozen readiness badge. The iteration shipped a
good fix and verified nothing.
**Applies to:** any backend-only iteration whose spec names browser journeys in TESTING REQUIREMENTS or
targets a regressed journey — check `browser_checks_run` and the existence of the evidence directory before
believing any completion claim.

## iter-8 — 2026-07-21T23:53:18Z

**Verdict:** CONTINUE
**Lesson:** A clean live capacity measurement does not prove the fix caused it. `reports/perf-budgets.md`'s
iter-8 section reports 43.6% VmPeak margin and 468/468 healthy polls, then states in the same paragraph
that the run "never hit enough memory pressure to trigger the new `MemoryError`-specific branch at all" —
and it executed under host-guard CPU-affinity (`0-3,8-11`) + 4-thread BLAS/OMP caps that did not exist
during iter-7's failing run. The confound (fewer threads → smaller arenas/VSZ) is at least as plausible an
explanation for the improvement as the diff. Capacity/availability fixes must be measured against
like-for-like host conditions, or the "closed" claim is unattributable.
**Applies to:** any iteration claiming an AG-8 memory/availability regression is closed, and any perf
measurement taken after host-guard settings changed.

## iter-8 — 2026-07-21T23:53:18Z

**Verdict:** CONTINUE
**Lesson:** A ~220-line block was pasted into the MIDDLE of an existing test
(`test_start_backend_logfile_ends_abruptly_after_simulated_crash`), silently deleting that test's four real
assertions — it still reported PASSED — and leaving the new headline test with a guaranteed `NameError` on
an undefined `spawned_backend`, so the iteration's own TC-1/TC-2 regression guard had never once executed.
Developer self-check, reviewer ("test_quality: pass") and QA ("2 PASSED") all reported green over it; only
the audit gate caught it.
**Applies to:** any iteration inserting a large block into an existing test file — re-read the function
boundaries on BOTH sides of the insertion point, and treat "a long-standing test still passes" as
suspicious when the diff touched its file.


<!-- condense.sh 2026-07-24T08:16:35Z: moved 6 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-07-25T01:03:55Z: moved 3 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-07-26T10:36:51Z: moved 4 entries (keep-iters=5) -->

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

## iter-17 — 2026-07-24T07:44:45Z

**Verdict:** CONTINUE
**Lesson:** Do NOT STALL on a latency-budget breach until it is DIAGNOSED. iter-15 correctly STALLED
because the cost was a KNOWN cold full-basis compute and only the product-direction response was
owner-owned. iter-17's residual (11/68 stored-row-read breaches, max 12.655s) looks similar but is
categorically different: it is UNDIAGNOSED (narrowed to SQLite-writer-contention vs GIL/threadpool but
indistinguishable because `logs/backend.log` carries zero per-request timestamps). Missing instrumentation
is agent-fixable, so the unblock path is agent-owned → CONTINUE, not STALLED. The routing test is "is the
cost proven, or merely unmeasured?" — a proven hard cost routes to the owner; an unmeasured one routes to
an agent instrumentation pass first.
**Applies to:** any iter where a page/endpoint misses a committed `reports/perf-budgets.md` budget and the
mechanism is not yet pinned — check whether the diagnosis is blocked by missing telemetry (agent work)
before treating the residual as an owner budget-amendment decision.

## iter-18 — 2026-07-24T11:05:00Z

**Verdict:** CONTINUE
**Lesson:** The undiagnosed `/backtest` latency budget breach (chased since iter-11 through
narrow-by-elimination) turned out to be a create-once SQLite INSERT (`backfill_run_forward_returns`) hiding on
a nominally READ endpoint's serving path — 82.2% of each slow request under concurrency, serializing on
SQLite's single-writer lock, while the pure-read resolver stayed flat at ~10ms. Two non-obvious traps it
exposes: (a) a "read" endpoint can carry a lazy create-once WRITE that only contends under load, so wall-clock
measurement alone (iters 11-17) could not attribute it — one iteration of cheap per-request phase timing did
what four of narrowing could not; (b) pure 6× concurrent reads did NOT reproduce the breach (0/966), because
the writer-lock contention only bites when a concurrent INGEST holds the same lock — so a load test that omits
the ingest overlay will falsely read "budget holds."
**Applies to:** any iter touching `apps/backend/app/api/backtest.py` / `mcp/tools.py` serving path or the
`resolved_forward_aggregate_evidence` resolver; more generally, any "read" endpoint that lazily
creates-once-on-first-view — instrument phases and test under a concurrent-ingest overlay, not pure reads.


<!-- condense.sh 2026-07-27T15:27:07Z: moved 3 entries (keep-iters=5) -->

## iter-19 — 2026-07-24T16:10:00Z

**Verdict:** CONTINUE
**Lesson:** "THE one shared latency blocker" framing was incomplete: fixing the create-once forward_returns INSERT on `/backtest` (backfill_forward_returns_ms, 877->13.9ms) left a SEPARATE cold-recompute subsystem on the SAME page (`ensure_loop_ms`, historical first-view, 9.6-54s no-affordance skeleton) untouched — same page, same user-visible latency class, different code path. A same-symptom latency/UX gap can hide in a different subsystem than the one you instrumented and fixed; a per-phase timing breakdown that only covers the phase you suspected will not surface it — the browser first-view walk (UT-04) did.
**Applies to:** any iter closing a "single root-cause" latency/perf journey on a page that has more than one on-load compute path — verify the OTHER first-touch paths (cold historical as-of, empty-store, first-of-day) with a live browser walk, not just the instrumented phase.

## iter-20 — 2026-07-24T19:30:00Z

**Verdict:** STALLED
**Lesson:** Moving a synchronous request-path compute to an in-process BACKGROUND thread eliminates the request-path BLOCK (9.6-54s -> 0.082s) but does NOT eliminate latency impact — the CPU-bound compute now contends for the GIL, transiently pushing OTHER concurrent traffic (and `/api/health`) over budget for the bounded compute window (3.0-6.3s `/backtest`, 1.60s health here). "Off the request thread" is not "no latency cost"; measure the CONCURRENT-traffic budget during the background window, not just the triggering request. Meta-lesson: an iteration can be a complete, correct success at its stated target yet move NO journey to passing — when the agent-tractable chain is exhausted and the journey stays blocked on owner-gated proofs + a spec-rejected-to-fix residual, STALLED is the honest verdict even after real progress (do not reflexively CONTINUE just because work landed).
**Applies to:** any iter that moves a heavy compute to an in-process thread/daemon (verify concurrent-window budgets, not just the trigger); any evaluator facing "target fully achieved but no journey crossed" (weigh C.2 human-owned-blocker before defaulting to CONTINUE).

## iter-21 — 2026-07-25T03:25:00Z

**Verdict:** STALLED
**Lesson:** A journey's acceptance state can be structurally UNPHOTOGRAPHABLE by the default capture:
`/backtest`'s `RefreshingEvidenceBanner` renders at the page BOTTOM (`page.tsx:241-274`, after
AsOfScanSummary/Scorecard/ReturnAttribution/LeadershipLists), so every viewport screenshot of the
`ready -> refreshing -> ready` cycle looked identical — `UT-J-08-01` and `-04` came back byte-identical to each
other (md5 `67e7793a…`) and to iter-17's `TC-07-backtest-page.png` and iter-20's
`TC-12-historical-view-loaded.png`. Two takeaways: (a) browser-QA must use a full-page or element-scoped
capture for any state that renders below the fold, and (b) when screenshots are uninformative, this codebase
offers a *stronger* substitute — the `dataset_version` stamp is literally `(scanner_runs count,
forward_returns count)`, so cross-referencing the stamp bump, `forward_aggregate_cache.created_at`, and the
screenshot mtimes proves the serving state machine from the DB without trusting any prose.
**Applies to:** any iteration verifying `/backtest` evidence states (`refreshing` / `not_yet_computed` /
`ready`), and any evaluator receiving screenshots whose md5s repeat across iterations — hash the evidence
directory before crediting a status change.

