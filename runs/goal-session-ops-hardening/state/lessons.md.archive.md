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


<!-- condense.sh 2026-07-27T20:07:50Z: moved 3 entries (keep-iters=5) -->

## iter-22 — 2026-07-25T08:55:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A measured "window duration" reported by a polling lane can be the POLLER's elapsed time, not the
window's. The browser-qa lane reported its BCW as "28.06 s (well inside the bound)"; the
`forward_aggregate_cache` commit rows for that same `(asof_key, dataset_version)` show 07:31:59.453 ->
07:32:56.164 (56.71 s first-to-last commit, ~14 s/horizon), so with the usual ~13 s trigger->first-commit lead
the real window was ~69.8 s — inside the amended 90 s bound but NOT inside the 60 s one it was cited against.
Re-derive any window/elapsed claim from the source-of-truth timestamps (DB rows, server logs), never from the
measuring script's own clock start. Corollary from the same iteration: a handoff's "I grepped the log for X and
found none" is checkable in seconds and was FALSE here — `logs/backend.log:76796-76808` contains both the exact
string the developer said they searched for and a real `MemoryError`.
**Applies to:** any iteration whose acceptance rests on a timed window, poll series, or "no errors in the log"
claim — especially perf/latency measurement passes and any goal-closing evaluation.

## iter-23 — 2026-07-25T11:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A served `evidence_generated_at` can legitimately have NO surviving row in
`forward_aggregate_cache` — the iter-16 cutover contract (`apps/backend/app/engine/forward_testing.py:1135-1156`)
deletes the prior `dataset_version`'s rows for an `asof_key` the instant the current version becomes complete.
An evaluator who checks the refreshing banner's timestamp against the DB *after* the warm finishes will find
nothing and can wrongly conclude the number was fabricated (I nearly did). Check the pruning contract before
calling an AG-3 violation; the absence is actually positive evidence for the "never mixes versions" clause.
**Applies to:** any iteration or evaluation that verifies `/backtest` refreshing/last-good evidence against
`forward_aggregate_cache`, or that audits AG-3 on a `generated_at`/`evidence_asof` label.

## iter-23 — 2026-07-25T11:05:00Z (second)

**Verdict:** GOAL_ACHIEVED
**Lesson:** A spec can contradict itself and produce a "violation" that is really the developer obeying the
other half: iter-23's BACKGROUND (line 114) instructed the exact 4-decimal figures "7.1191 s / 0.2530 s"
while its own TC-2 demanded figures "verbatim in `perf-budgets.md`" (which prints 3 decimals). The developer
followed BACKGROUND; the reviewer flagged TC-2. Resolve these by going to the raw source
(`runs/goal-ops-hardening-iter-22/bcw-measure.csv` — max `bt_latency_s` is 7.1191 exactly), not by picking a
side between two spec clauses.
**Applies to:** any iteration whose DoD requires "verbatim" citation of a figure that exists at two
precisions (raw CSV vs rounded report); decomposers should name ONE canonical rendering.


<!-- condense.sh 2026-07-29T19:00:40Z: moved 7 entries (keep-iters=5) -->

## iter-24 — 2026-07-26T13:52:22Z

**Verdict:** CONTINUE
**Lesson:** A goal-proposer auto-appended journey (J-09) inherited this session's standard Acceptance
clauses verbatim — including the `demo.sh --session-live` walkthrough clause — but the iteration spec's
IN SCOPE / DEFINITION OF DONE never mapped that clause to any task, so the journey shipped fully working and
still could not be scored `passing`. Nothing in `run-goal.sh` writes
`reports/goal-session-ops-hardening-demo.json`, so a walkthrough clause is only ever closed by an explicit
task — the same gap that made the iter-22 second-key CONFIRM reject GOAL_ACHIEVED, now repeated one journey
later.
**Applies to:** any iteration targeting a journey whose Acceptance block was auto-appended between the
`<!-- AUTO:journeys -->` markers, and any decomposer writing a DoD — enumerate EVERY Acceptance bullet,
especially the walkthrough/demo-manifest one, before declaring scope.

## iter-24 — 2026-07-26T13:52:22Z (second)

**Verdict:** CONTINUE
**Lesson:** On this host Chrome MCP returns a solid-colour blank frame for ANY scrolled screenshot (verified
by the browser-QA agent across pages, scroll methods, `fullpage`, element selectors and CSS zoom), so the
new `/data` panel — the last panel on a ~24,800px page — is unphotographable. The workable substitute is the
auto-saved raw DOM capture (`~/.cache/superpowers/browser/<date>/session-*/NNN-*.html`) read verbatim and
cross-checked against the live API and the SQLite rows; that chain proved AG-3 to 1.68 ms, stronger than any
screenshot would have.
**Applies to:** any future iteration whose acceptance state renders below the fold on this host, and any
evaluator weighing "no screenshot" against the absolute no-screenshot rail.

## iter-25 — 2026-07-26T16:10:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two detached `pytest` runs building the `loaded_engine` fixture starved the `ulimit -v`-capped
backend during its boot warm-up: `_run_warmup` -> `backfill_forward_returns` raised a non-fatal `MemoryError`
(`logs/backend.log:79986`, the only such line in the whole logfile), readiness stayed permanently
`initializing` with the badge on "Initializing... history 89/89", and the deterministic replay lane then
FAILED J-07 purely because its golden step expects the text "Ready". The product was fine — the failure was
host memory contention created by our own test harness. Two consequences worth carrying: never leave heavy
pytest fixture builds running while a lane needs a healthy backend, and treat a replay FAIL whose expect is a
readiness word as an environment question first (check `logs/backend.log` + `ps`) before treating it as a
product regression.
**Applies to:** any iteration whose lanes run alongside detached pytest/heavy jobs; any golden script whose
`expect` is a readiness/badge string; any change to `warmup.py` / `readiness.py` badge states.

## iter-25 — 2026-07-26T16:10:01Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The iter-24 lesson ("enumerate EVERY Acceptance bullet, especially the walkthrough/demo-manifest
one") worked exactly as intended: iter-25's spec mapped the clause into IN SCOPE, the developer wrote the four
manifest steps, and the journey closed in one lean pass with no product-code risk. A journey blocked ONLY by an
unwritten artifact is the cheapest kind of blocker — spec it explicitly instead of carrying it as a "non-blocking
follow-up" across iterations.
**Applies to:** any goal-proposer auto-appended journey (it inherits the session's standard Acceptance bullets
verbatim, including the `demo.sh --session-live` walkthrough clause).

## iter-26 — 2026-07-26T18:48:05Z

**Verdict:** ESCALATE
**Lesson:** A "regression-only" browser pass can silently exercise a *heavier* code path than the journey
intends and leave the product in a worse state than it found it. This lane triggered background compute by
opening `/backtest` on two NEVER-SCANNED dates (2001-04-17, 1999-11-02) instead of dates that merely lack
forward aggregates: that ran a create-once `run_scan` on the request path (16.7-23.2 s, vs the ~40 ms the
intended trigger costs), produced the logfile's first-ever unhandled `IntegrityError` -> "Exception in ASGI
application" from `api/backtest.py:171`, and bumped `scanner_runs` to 1867 so `coverage_snapshot`'s key went
stale and `/data` began reporting an empty dataset for a 4.9 GB database. None of it appears in
`ui-test-results.md`; all of it is in `logs/backend.log` and the DB.
**Applies to:** any iteration whose QA triggers a background-compute window or time-machines to a historical
as-of date — pick a date that ALREADY has a snapshot, and always diff `logs/backend.log` (ASGI errors,
`backtest_timing total_ms`) plus `scanner_runs`/`coverage_snapshot` after a browser lane runs, before scoring
its narrative as evidence.

## iter-27 — 2026-07-27T17:30:00Z

**Verdict:** CONTINUE
**Lesson:** A golden replay script can encode an *incidental* page string as an assertion and then fail
forever for reasons no iteration diff can explain. `J-06.json` step 1 expects the literal "DEGRADED" on `/`,
which comes from `compute_preflight`'s drift component reading
`config.yaml:1152` -> `runs/goal-session-mcp-loop/state/drift-report.json` — ANOTHER goal-mode session's
file. Worse, `J-01`'s own golden starts a Data Manager job whose `_check_drift` rewrites that same artifact
before `J-06` asserts against it, so the replay suite can invalidate itself. When a replay FAIL cites a
string that has nothing to do with the journey's stated subject, check the artifact the string is derived
from before treating the row as a product signal.
**Applies to:** any iteration reading a replay FAIL row; any change to `readiness.py` / `drift.py` /
`config.yaml`'s `readiness.drift.report_path`; anyone authoring or re-recording a golden journey script.

## iter-27 — 2026-07-27T17:30:00Z

**Verdict:** CONTINUE
**Lesson:** A guard that calls `session.rollback()` inside a function that never commits has a blast radius
far wider than its own bookkeeping. The iter-27 AG-8 fix undid only the CURRENT symbol's staged keys, while
the transaction-wide rollback also destroyed every earlier symbol's autoflushed-but-uncommitted rows — so
`rows_inserted` reached `/data` as "N forward returns inserted" with 0 actually persisted. The developer's
own TC-3 test could not catch it because it stages the collision on the FIRST symbol, where nothing earlier
exists to lose. When reviewing a rollback-based tolerance guard, always ask what else was pending in that
transaction, and check whether the test exercises a non-first element.
**Applies to:** any change to `apps/backend/app/engine/forward_testing.py` (`_insert_run_forward_returns`,
`_backfill` — audit B2's cross-call residual is the same bug one level up); any new `except IntegrityError`
/ rollback-and-continue pattern anywhere in the engine.


<!-- condense.sh 2026-07-30T21:35:03Z: moved 11 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-07-31T10:44:48Z: moved 9 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-04T20:56:14Z: moved 9 entries (keep-iters=5) -->

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

## iter-39 — 2026-07-31T02:10:00Z

**Verdict:** ESCALATE
**Lesson:** When a live drill cannot reach the code path it is aiming at, the obstacle is usually a
LARGER allocation upstream in the same sequence — not a cap that needs one more turn of tuning. Three
cap trials (3420/2700/2650 MB) all died in `_missing_data_diagnostic`'s ~3.3M-row materialization
(`data_manager.py:271`) before the per-item aggregate-warm handlers were ever reached; the fourth
attempt, at 2650 MB, wedged the process for 7+ minutes instead of producing a proof. Switching to the
test hook J-07 step 4 already sanctioned made the same proof deterministic at the COMMITTED cap with
zero host pressure. Two durable rules fell out: (a) a drill that has probed three times without hitting
its target is diagnosing the wrong thing — go read what allocates FIRST; (b) `select(...).where(...)`
being bounded by symbol set does NOT make it bounded in memory — SQLAlchemy buffers the whole result
via `_raw_all_rows` before the loop body runs, and the in-code comment at `data_manager.py:262-274`
currently asserts the opposite.
**Applies to:** any iteration running an induced-memory-pressure or cap-tightening drill; any iteration
touching `_missing_data_diagnostic` / `_compute_coverage_body` / the `_refresh_ingest_aggregates`
finalize tail; and any review of a "bounded query" claim in `apps/backend/app/engine/`.

## iter-39 — 2026-07-31T02:10:00Z (second)

**Verdict:** ESCALATE
**Lesson:** Deterministic-lane repairs must be verified in BOTH directions before they are called done.
iter-38's replay lane reported six FAILs against a backend that was simply down; iter-39 fixed it with a
`BLOCKED` verdict class — but the fix left the *merged* artifact able to headline `**Browser QA Verdict:**
PASS` for a run whose journeys were all BLOCKED, because `merge_ui_test_results.parse_rows` recognizes
only PASS/FAIL/SKIP/SKIPPED and drops an unknown verdict from every count. The machine gate is safe
(`goal_gate.py:89,151` returns rc 1 on any `BLOCKED` cell), so this bites only an LLM reader. Practical
rule for every future evaluator: read the results TABLE ROWS, never the `Overall:`/verdict headline.
**Applies to:** any iteration touching `merge_ui_test_results.py` / `demo_runner.py` / `replay-lane.sh`,
and every goal-evaluator reading `reports/phase-*-ui-test-results.md`.

## iter-40 — 2026-07-31T03:20:00Z

**Verdict:** ESCALATE
**Lesson:** A `404` from a health probe is proof the server is UP, not down — and this session just lost
seven journey verifications to that confusion. The browser-QA precondition probed
`http://localhost:8255/health`, but `apps/backend/main.py:127` mounts the health router under prefix
`/api`, so the live endpoint is `/api/health`; `logs/backend.log` shows the 404 interleaved with
`GET /api/health 200 OK` on the same process. Combined with a UI test plan that read the spec's
`Frontend Present: no` as "no UI tests required", DoD item 8 / TC-9 went entirely unexecuted while
review, QA and the deterministic closure gate all reported clean. Two durable rules: (a) a precondition
check must distinguish *connection refused* (down) from *any HTTP status* (up) — never treat a 404 as
absence; (b) `Frontend Present: no` may suppress NEW-surface UI tests, never the required-still-passing
regression replay, and a browser run whose every regression row is `SKIP` must read as an unmet DoD item,
not a clean `SKIPPED`.
**Applies to:** every iteration's browser-qa/replay precondition and ui-test-plan step; any
goal-evaluator reading a `SKIPPED` browser headline; and any framework work on
`goal-iter-lean.sh` / `replay-lane.sh` / the ui-test-designer.

## iter-40 — 2026-07-31T03:20:00Z (second)

**Verdict:** ESCALATE
**Lesson:** `.yield_per()` bounds the DB cursor, not your accumulator — the same distinction iter-39
learned about `WHERE` clauses, one level up. This iteration correctly fixed `_missing_data_diagnostic`
(`data_manager.py:271`), but `apps/backend/app/engine/prices.py:132-142` (`_BarCache.prefill`) already
used `.yield_per(batch)` AND still collects every `daily_prices` row into one `by_symbol` dict of `Bar`
objects (~1.1 GB on the deep basis, named by the dev handoff as one of the two consumers in the drill run
that froze). So "it streams" is not evidence of a bound; check what the loop BODY retains. Also worth
recording: the post-fix drill's `MemoryError` fired at `data_manager.py:898`, **53 lines before** the
fixed call at `:951` — so "no traceback names the fixed site" was true because the code never got there,
which is much weaker than "the fix held under pressure".
**Applies to:** any review of a "bounded read" claim in `apps/backend/app/engine/`; any
memory-pressure drill whose success criterion is the ABSENCE of a name in a traceback.

## iter-41 — 2026-07-31T06:20:00Z

**Verdict:** ESCALATE
**Lesson:** Promoting a journey to an iteration's **target** silently REMOVES its verification. Every
coverage gate in the chain — `ui-test-designer`'s backend-only carve-out, `merge_ui_test_results.py`'s
`missing_required_journeys`/`skipped_required_journeys`, `goal_gate.py`, `closure_gate.py` — is driven
by the spec's `Required-still-passing journeys:` line and has no notion of `Target journeys:`. So
iter-41's merged results headlined `PASS 6/6` while J-05 and J-07 had no row anywhere, and J-05 ended
up with LESS evidence than in iters 38/39 despite golden scripts `J-05.json`/`J-07.json` sitting unused
on disk. Second, related lesson from the same iteration (auditor's B1, worth keeping verbatim): when a
fix is written to prevent a specific past incident, that incident's own committed artifact IS the
regression fixture — feeding
`reports/phase-goal-ops-hardening-iter-40-ui-test-results.md` through the new guard took thirty seconds
and showed it still merged to a clean `SKIPPED`, because the guard caught a MISSING row while iter-40's
real shape was a PRESENT row reading `SKIP`.
**Applies to:** any iteration adding or trusting a journey-coverage gate; any iteration whose spec names
`Target journeys:` on a backend-only (`Frontend Present: no`) spec; any fix written to prevent a named
past incident.

## iter-42 — 2026-07-31T09:05:00Z

**Verdict:** REGRESSION
**Lesson:** Closing a verification hole is not a cost — it is a discovery. Two rounds of "unknown"
on J-05 read as neutral bookkeeping; the first time the check actually ran, the journey was broken,
and had been since at least iter-40. `unknown` is not a mild status: it is an unpaid debt that
compounds, and a session should treat two consecutive `unknown`s on the same journey as urgent, not
as deferred. The corollary bit this round too: `regressed` is defined as "was passing in a PRIOR
iteration, now failing" — not the immediately prior one — so an `unknown` interlude does not launder
a regression into a mere `failing`.
**Applies to:** any iteration that scores a journey `unknown`, and any evaluator choosing between
`failing` and `regressed` after a gap in verification.

## iter-42 — 2026-07-31T09:05:00Z (second)

**Verdict:** REGRESSION
**Lesson:** A memory measurement that only measures the work you REMOVED is not a measurement. The
`_BarCache.prefill` bench compared `prefill(pool)` vs `prefill(None)` and reported a 2.5% win; the
43 symbols the filter stops prefilling are not dropped, they fall onto the lazy `list[Bar]` path at
264.6 B/row instead of `_SymbolColumns`' 81.0 B/row, and 36 of them are `config.etfs` names read
every snapshot date. With that arm included the change is +5.1%, the wrong sign. Same shape as this
session's own `.yield_per()` lesson one file over: bounding one side of a transfer proves nothing
about the total. Any future memory claim in this codebase must measure a whole job, not a function.
**Applies to:** `apps/backend/app/engine/prices.py`, any `perf-budgets.md` memory claim, and any
iteration whose DoD contains a before/after resource measurement.


<!-- condense.sh 2026-08-05T08:58:55Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-06T22:00:10Z: moved 4 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-07T13:13:59Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-09T20:39:26Z: moved 3 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-10T17:30:40Z: moved 6 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-10T23:08:54Z: moved 4 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-13T22:41:48Z: moved 37 entries (keep-iters=5) -->

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

## iter-73 — 2026-08-13T03:06:22Z

**Verdict:** CONTINUE
**Lesson:** A deterministic-replay lane runs its journeys SEQUENTIALLY, so an environment break
part-way through masquerades as a per-journey golden defect. This round J-01/J-03/J-04 (frames
timestamped 03:14 BST) PASSed on fully styled, real pages and J-05/J-06/J-07/J-08/J-09 (03:15-03:16)
all FAILed on the identical unstyled, asset-less "Checking backend…" shell — the split is by CLOCK,
not by journey. The SPEED-22 mass-false-FAIL breaker guessed "suspected golden-script/selector drift"
and queued exactly the wrong remedy (`state/goldens-regen-pending` lists J-05..J-09 for regeneration;
regenerating a script cannot fix a frontend serving pages without their assets). Always sort the
FAILed frames by capture time and open two of them before accepting any lane's automatic explanation —
a contiguous time block of identical broken frames means the environment moved, and the fix belongs in
the harness, not in the goldens. Corollary for scoring: check whether the broken window straddles the
backend boot header in `logs/backend.log` (here the live server booted 02:13:14Z and the frames landed
~60-180 s later), because a just-restarted frontend is the cheapest explanation to test first.
**Applies to:** any iteration whose deterministic replay reports 3+ simultaneous FAILs; any evaluator
reading a `VOIDED`/`overturned` footer; anyone about to act on `state/goldens-regen-pending`.

