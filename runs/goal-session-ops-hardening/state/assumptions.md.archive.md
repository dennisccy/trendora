# assumptions.md — archive

Entries moved out of `assumptions.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-07-20T21:02:41Z: moved 2 entries (keep-iters=5) -->

## iter-0 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s Product Shape names only 9 nav sections as "existing nav
unchanged" (Dashboard | Stocks | Sectors | Themes | Backtest | Research | Data | Watchlist |
Evidence), but the actual sidebar (`apps/frontend/components/sidebar.tsx`) has 11 items —
also Scanner Runs and Methodology, neither mentioned in that prose list.
**We chose:** treated the actual 11-item sidebar as ground truth for the blueprint's
Information Architecture; read goal.md's 9-item list as "these stay, at minimum," not "exactly
these and no others" — removing/hiding Scanner Runs or Methodology would itself violate the
Non-Goal "not a rewrite — additive to existing surfaces."
**Reversible:** yes

## iter-0 — goal-evaluator

**Ambiguity:** The iter spec's NOTES steer "surface not yet implemented → FAIL," and browser-QA
scored all five journeys FAIL under a strict PASS/FAIL/SKIP contract, yet the journey-history
schema offers a distinct `partial` status ("only some assertion steps passed"). J-04 had 5 of 6
numbered steps reproduce live (fast boot, phase-aware initializing badge, distinct crash
presentation, interrupted-job-after-restart — all inherited working from mcp-loop iter-28/33),
with only the persistent-logfile + memory-cap-enforcement step confirmed missing.
**We chose:** scored J-04 `partial` (not `failing`) to signal to the decomposer that only the
logfile/memory-cap layer remains, while keeping J-06 `failing` (its 8/11 fast pages are
pre-existing baseline behavior, not progress toward J-06's own new deliverables, all of which are
absent). Either way neither counts toward GOAL_ACHIEVED, so the CONTINUE verdict is unaffected.
**Reversible:** yes


<!-- condense.sh 2026-07-21T08:09:38Z: moved 8 entries (keep-iters=5) -->

## iter-1 — goal-decomposer

**Ambiguity:** goal.md's lessons/binding notes establish "requested range always wins" for
explicit backfill requests, but the cadence gate `_cadence_allowed_dates` today filters both the
plain `backfill`/`both` kinds AND the `rebuild` kind (which internally widens the range to the
full historical calendar before calling the same `_do_backfill`); it is not stated whether the
cadence bypass should extend to `rebuild` too.
**We chose:** scoped the "requested range always wins" bypass to explicit `backfill`/`both`
requests only. `rebuild` keeps applying `_cadence_allowed_dates` unchanged — no Must-have journey
this cycle exercises `rebuild`, the user does not supply its date range (`validate_job_request`
already exempts it from range validation), and changing its snapshot density is outside this
iteration's tested scope.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** J-03's acceptance states "the chunk plan derives from the config `import_chunking`
values; the UI progress reflects the same plan the engine executes," but `_do_backfill` today has
no date-window chunking at all — `chunk_index`/`chunk_total` are populated only by the fetch/expand
stage. It is not stated whether removing the `max_range_days` rejection alone satisfies J-03, or
whether real date-window chunking must be added to the backfill stage.
**We chose:** read the acceptance language literally and scoped J-03 to include adding real
date-window chunking to `_do_backfill` (splitting `[start,end]` into
`import_chunking.date_window_days`-sized windows, populating the existing dormant
`chunk_index`/`chunk_total` fields the frontend already renders for fetch jobs) — not just the cap
removal.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** browser-qa scored the whole J-04 journey row `UT-J-04` as PASS, but J-04's full
Acceptance also requires a `scripts/start-backend.sh`-written persistent logfile and enforced
`memory_cap_mb`/`malloc_arena_max` — both explicitly OUT OF SCOPE this iteration and confirmed
unbuilt (dev handoff). The UT-J-04 step-5 log check passed against the harness's own
`fanout-backend-8255.log` (written by run-phase's fanout), not a start-backend.sh persistent log.
**We chose:** kept J-04 at `partial` (not promoted to `passing`) — treating the Required-still-
passing mandate as a non-regression check of J-04's 5 already-working sub-behaviors, not a
completion claim. The logfile + memory-cap acceptance bullets remain the open gap.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-01's DoD pins the productive May run's exact breakdown (19/19/0/9/28), but the
prescribed 2026-05-02→05-29 range had already been backfilled by a prior functional-QA pass before
the browser session began, so no fresh same-session productive submission was captured live — the
live submission hit the zero-work path instead.
**We chose:** scored J-01 `passing` on the productive path via three corroborating sources rather
than a fresh live run: the still-on-screen historical Run-History row (DOM-read exact match
"28 calendar days · 0 already snapshotted · 9 non-trading", 19 snapshots), the re-run's
`already_snapshotted=19` (UT-04), and the unit test `test_backfill_breakdown_invariants_hold_on_
fresh_and_rerun` which proves the fresh-run 19/19/0 by construction.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** goal.md's "four offenders to retire" and the Aggregation-candidates table read as a
mandate to fully retire boot's `ensure_latest_snapshot` synchronous-compute-if-missing branch and
the boot warm-up loop's cadence-snapshot bootstrap, but neither is exercisable in this session:
`fetch` is offline zero-work (AG-9), so `latest_data_date` never advances outside an explicit
backfill/rebuild, and the currently-running DB already has a snapshot for its latest date
(fast-boot already verified <2s in iter-1) — so both branches are dormant either way this iteration.
**We chose:** scoped J-05 to what its own 4 numbered acceptance steps literally exercise — a single
historical day's backfill, a cold restart-and-visit of `/data`, and health responsiveness during a
heavy job — building the new `coverage_snapshot` table + ingest finalize hooks + the boot thread's
safety-net warm step, while leaving `ensure_latest_snapshot` and the warm-up loop's cadence
bootstrap unchanged (their retirement is unverifiable against the offline seed and risks regressing
mcp-loop-era readiness/warm-up guarantees no Must-have journey this cycle re-tests).
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** `config.yaml`'s `server:` section comment block claims `scripts/start-backend.sh`
already wires all five fields (`memory_cap_mb`, `malloc_arena_max`, `limit_concurrency`,
`timeout_keep_alive_seconds`, `graceful_timeout_seconds`) — "reads every value from here via the
venv python" — but a direct read of the script (confirming iter-0's identical finding about the
first two) shows NONE of the five are wired; goal.md's own binding note, however, names only
`memory_cap_mb`/`malloc_arena_max` + the logfile as required this cycle.
**We chose:** scoped `scripts/start-backend.sh`'s fix to exactly the three goal.md names (`ulimit -v`
from `memory_cap_mb`, `MALLOC_ARENA_MAX` from `malloc_arena_max`, persistent logfile) and left
`limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds` unwired this iteration,
flagging the same drift in NOTES rather than silently expanding scope beyond what goal.md asks — a
future iteration should wire them if J-05 step 4's health-responsiveness check ever reveals it's
actually needed.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-04's 6-step acceptance includes step 4 (kill backend → UI transitions to an explicit
unreachable/crashed presentation, visibly distinct from initializing). This iteration built and
freshly verified J-04's *remaining* gap (persistent logfile + memory-cap + boot-no-prefill) and
freshly re-verified four other steps (fast boot UT-04, phase-aware initializing badge UT-06,
interrupted-job-after-restart UT-07, crash→logfile-abrupt-end via the TC-17 real-process SIGKILL
test), but the crash→UI-unreachable *visual* presentation (step 4) was NOT freshly screenshotted this
iteration.
**We chose:** scored J-04 `passing` (partial→passing) rather than holding it partial for the one
un-rescreenshotted sub-step — its badge/preflight/readiness/health code is UNCHANGED this iteration
(coherence confirms no nav/badge diff), step 4 was verified passing in mcp-loop iter-28/33 and re-noted
working at baseline, and its crash-side counterpart (logfile abrupt-end) IS freshly verified. Future
required-still-passing replay/QA re-exercises the crash-UI path.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** AG-3 ("A journey passes ONLY if the displayed numbers are correct") can be read
journey-scoped (only Must-have journeys' numbers must be correct) or product-wide (no surface may ever
show wrong numbers). Audit B1 (fetch-lands-bars → false-zero default `/data` coverage) is a genuine
wrong-number display, but on a path no Must-have journey (J-01/J-03/J-04/J-05/J-06) exercises, and the
audit was "genuinely unsure IMPORTANT-vs-CRITICAL."
**We chose:** applied the journey-scoped reading for the VERDICT — B1 breaks no Must-have journey, so
it is not a journey-failing AG-3 violation and does not force REGRESSION; recorded it unresolved
(minor for loop-mechanics, AG-3-dimension-serious) that blocks a future GOAL_ACHIEVED and is the #1
next-step. The product-wide reading would halt the loop now; rejected because the issue self-heals, is
disclosed with a queued fix, and the loop continues regardless (J-06 unbuilt). A human can override to
REGRESSION.
**Reversible:** yes


<!-- condense.sh 2026-07-21T21:48:38Z: moved 2 entries (keep-iters=5) -->

## iter-3 — goal-evaluator

**Ambiguity:** J-05 step-4's acceptance is the qualitative "while a heavy ingest job runs, poll
`GET /api/health`; assert it stays responsive throughout" — the ui-test-plan sharpened this to a
stricter "every poll within 1 s", and the reviewer explicitly asked the evaluator to rule which
applies. Item L measured zero non-200 / zero timeout / zero hang across 1,725 polls (badge "Ready"
throughout), but 50 (2.9%) ranged 1.00–3.29 s during the parallel-backfill contention window.
**We chose:** applied goal.md's qualitative reading — "stays responsive throughout" is satisfied by
the always-200, no-hang, badge-Ready result; the 2.9% sub-3.3 s slow window is a bounded,
self-resolving latency blip, not an unresponsive/frozen state. (Does not change the verdict: J-05
stays `partial` for the browser-story gaps below, not for step-4.)
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** ux-regression scored UX-REGRESSION-FAIL and framed B3 (fetch → false app-wide
"Backend unavailable"/NO-GO) and F1 (frozen job heartbeat) as directly undermining required-passing
J-04's "visible status stays accurate" trust promise — which could be read as J-04 having regressed.
But both root-cause to modules NOT in this iteration's diff (I confirmed `readiness.py` absent from
the 3-file diff), and J-04's scripted 6-step replay (UT-J-04) PASSED; the defects live on paths
J-04's acceptance never scripts (fetch-time badge, heavy-job heartbeat).
**We chose:** scored J-04 `passing` (scripted acceptance holds, replay confirmed, code unchanged)
and treated B3/F1 as newly-surfaced PRE-EXISTING defects / hard blockers to a future GOAL_ACHIEVED
— NOT a REGRESSION halt (no verified journey moved passing→failing; neither is a clean named-AG
violation). A human who reads B3 as a vision "the UI tells the truth about the backend's own state"
/ AG-3 violation may override to REGRESSION — flagged explicitly in eval.md.
**Reversible:** yes


<!-- condense.sh 2026-07-23T09:14:48Z: moved 16 entries (keep-iters=5) -->

## iter-4 — goal-decomposer

**Ambiguity:** J-05's acceptance and the iter-3 evaluator's B3 fix direction ("give 'new data
landed, snapshot pending' its own calm label + an in-app recovery pointer, compare vs the
benchmark's own latest bar") are qualitative — `docs/goal.md` never anticipated this pre-existing
defect (B3/F1 were discovered by iter-3's browser exercise, not named in the goal text), so no
canonical name or field shape exists yet for the new readiness condition.
**We chose:** a fourth `ReadinessState` literal `awaiting_snapshot` (sibling to `ready`/
`initializing`/`unavailable`) plus one new nullable `readiness.detail: string|null` field on the
SAME `GET /api/health` payload (computed by the SAME `compute_readiness`), and narrowed the
servability comparison to the benchmark symbol (`cfg.etfs.index[0]`, the same symbol
`_warmup_dates`/`walk_forward_asof_dates` already use to define the trading calendar) rather than
the whole-table `latest_data_date` max.
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** J-05's Acceptance has four bullets; the fourth is a `[NEW]`-flagged `demo.sh
ops-hardening --session-live` walkthrough. That walkthrough was deliberately deferred this iteration
(iter spec OUT OF SCOPE — "a showcase/demo-chain concern, not a browser-qa-verifiable behavior").
So J-05's product-behavior acceptance (all 4 steps + the consistency/correctness/anti-goals bullets)
is fully verified, but one named Acceptance bullet is not yet produced.
**We chose:** scored J-05 `passing` on its product-behavior acceptance, treating the `[NEW]` demo.sh
walkthrough as a session-closure showcase artifact rather than a per-journey passing gate — the same
way J-01/J-03/J-04 were each scored passing without a fresh demo.sh walkthrough, and the same way the
archived mcp-loop session produced terminal showcase renders only at close-out. Flagged in eval.md
+ evaluator-log as a closure-gate item: BOTH J-05 and J-06 walkthroughs must be produced (or the
human must accept their deferral) before the final GOAL_ACHIEVED gate.
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** J-05 step 3 / TC-8 (the cold-boot check, SKIPPED in iter-3, whose re-execution was a
named iter-4 DoD item) was written by the ui-test-designer with a literal "every coverage figure
reads 0 or —" precondition on a byte-empty DB. browser-qa found this precondition architecturally
unreachable via any real boot (`main.py`'s lifespan runs `load_seed()` + `ensure_latest_snapshot()`
to completion before the port accepts a connection), and scored UT-08 "PASS on the underlying safety
property" instead of on the literal wording.
**We chose:** accepted that adjusted-scope PASS and counted J-05 step-3's cold-boot check as
executed-and-satisfied, because goal.md's OWN wording of step 3 asks only for "coverage renders from
the persisted payload within its committed budget and the process performs no 3.3M-row bar prefill"
— which was directly verified (41ms `/api/data`, clean render, no prefill), independent of the
stricter all-zero framing the test-designer added. (The all-zero precondition was a test-plan
over-specification, not a goal.md requirement.)
**Reversible:** yes

## iter-5 — goal-decomposer

**Ambiguity:** J-06's DoD step 3 requires a "code-level audit that no on-load endpoint performs an
unbounded `daily_prices` scan or recomputes an inventory aggregate," but goal.md does not say what to do
if the audit (or a live measurement) finds a genuine violation on an endpoint outside the "four offenders"
list goal.md itself names (already retired iter-2 through iter-4) — e.g. one of the two candidates this
iteration's spec flags (`/api/backtest`'s 5x per-horizon `compute_forward_aggregates` read, `/api/runs`'s
per-run N+1 count query).
**We chose:** scoped this iteration to INCLUDE a bounded, minimal fix if the audit/measurement finds a
genuine violation, but ONLY if it fits the existing ingest-time-cache convention (mirroring
`coverage_snapshot`/`EventStudyCache`/`MarketPhaseCache`) through the value's EXISTING computing module and
endpoint (no second producer); a violation whose fix would need a new architectural decision is out of
scope this iteration and hands back to a fresh decomposer pass instead of growing this iteration's scope
open-endedly.
**Reversible:** yes

## iter-5 — goal-decomposer

**Ambiguity:** J-06 carries the same `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthrough
acceptance bullet that iter-4 already deferred for J-05 (assumptions.md, iter-4 — goal-evaluator) as a
session-closure showcase artifact rather than a per-journey passing gate.
**We chose:** applied the SAME reading to J-06 for consistency — the walkthrough stays a session-closeout
showcase artifact, not part of this iteration's DEFINITION OF DONE; the closure-gate reminder (produce BOTH
J-05's and J-06's walkthroughs, or have the human accept the deferral, before GOAL_ACHIEVED) is restated in
the iteration spec's NOTES so it is not lost now that J-06 may be the session's final journey.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** J-01's deterministic golden-script replay FAILED (step-6: literal "2026-05-15" not found on
/scanner-runs), with no LLM-fallback adjudication run — so the mechanical re-verification lane did not
cleanly pass a required-still-passing journey. The methodology says a replay FAIL can be a golden-script
false positive but expects an in-pipeline reconciliation footer, which is absent here.
**We chose:** scored J-01 `passing` (not `regressed`/`failing`/`unknown`) by adjudicating the miss myself as
a stale proxy: replay steps 1-5 (J-01's ACTUAL goal.md acceptance — the "2 non-trading" zero-work
explanation) PASSED; the audit's direct DB query confirms the 2026-05-15 run exists; the runs-display code
path (runs.py/scanner-runs/page.tsx) is git-confirmed untouched in the diff; TC-09 loaded /scanner-runs
in-budget; and J-01-verify.png shows a healthy 750-row table. Step-6 is an auxiliary "run history intact"
proxy on a page J-01 doesn't modify, gone stale as the run list grew past its fixed assertion. Flagged the
golden-script fix as a next-iter blocker.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** J-04 and J-05 (required-still-passing) received ZERO regression-replay coverage this cycle —
the replay lane ran only J-01/J-03 — yet the shared function they depend on (`_refresh_ingest_aggregates`)
was modified this iteration. No failing evidence exists, but no fresh passing evidence does either.
**We chose:** scored both `unknown` (schema: "not tested this iteration; carry over previous status") rather
than carrying `passing` forward silently — honest about the missing this-cycle evidence and it flags them
for mandatory re-verification next iter. Did NOT treat the coverage gap as a regression (absence of evidence
≠ evidence of failure), and noted the audit's read that the ingest-time warm actually reinforces J-05's
"precomputed at ingest" claim.
**Reversible:** yes

## iter-6 — goal-decomposer

**Ambiguity:** iter-5's evaluator offered three alternative directions to close J-06's Dashboard
browser-latency violation without mandating one: an HTTP/2 uvicorn launcher change, coalescing the
Dashboard's 10-13 on-load calls into fewer requests, or a documented browser-realistic budget re-commit.
**We chose:** a frontend-only fetch-scheduling/staggering fix (no new backend endpoint, no TLS/HTTP2
launcher change, no budget loosening) — because (a) any combined/coalescing endpoint would create a
second serving path for values already registered in the Data Contract (explicitly barred), (b) HTTP/2
without TLS is not viable in browsers and adding TLS/cert machinery is disproportionate to a local-first,
offline-deterministic tool, and (c) curl's own baseline (0.79-1.0s) already sits comfortably under the
1.5s budget, so removing browser connection-queuing alone should close the gap without loosening any
committed number.
**Reversible:** yes

## iter-6 — goal-decomposer

**Ambiguity:** `GET /api/data/availability` has no committed budget in `reports/perf-budgets.md`; iter-5's
QA explicitly said its over-budget-class real-browser reading (2.9-3.0s) was "not a test failure per
TC-07's criteria" (unbudgeted) but "flagged for future budget commitment." goal.md's J-06 step 2 only
names the boot budget and the cold `/api/data` budget as required additions, not this sibling endpoint.
**We chose:** to commit an explicit budget for it this iteration (generic ≤1.5s endpoint class, same file)
rather than leave it permanently unbudgeted, because it shares J-06's exact Dashboard-class root cause and
the iter-5 evaluator explicitly recommended folding it into the same fix decision.
**Reversible:** yes

## iter-6 — goal-evaluator

**Ambiguity:** J-06's acceptance is "every one of the 11 named pages within its committed budget," and
`/evidence`'s committed budget (Item I, from the archived mcp-loop session) is "warm ≤3s + a bounded
one-time cold miss." On the live dev DB the first-view cold miss is ~73s (audit B1). This can be read as
IN-budget (the cold-miss clause is explicitly unbounded-scaling with data) or as NOT satisfying the
journey's "pages load only what they need / available in seconds" intent on the basis the session runs.
**We chose:** scored J-06 `partial` rather than `passing` — the two TARGET endpoints are genuinely fixed
and in budget (3/3 real-browser), but I did NOT let the letter of Item I's cold-miss clause bless a ~73s
first-view on the last Must-have journey's page as a clean pass, because the audit itself recommends warming
it before the GOAL_ACHIEVED gate. Combined with the unproduced [NEW] demo.sh --session-live walkthrough and
the CLOSURE-FAIL, this keeps the decision tree consistent (not-all-passing → CONTINUE) without inventing an
ad-hoc veto. A human who reads Item I's clause as fully dispositive may override J-06 to `passing`.
**Reversible:** yes

## iter-7 — goal-decomposer

**Ambiguity:** iter-6's evaluator recommended `full` depth for the closeout iteration, but the core
product fix (extending `_refresh_ingest_aggregates` to warm `drawdown_expectations`) touches only one
existing function in one file, mirroring an already-built precedent (`research_hot_keys`,
`forward_aggregates`) — none of the four numbered depth triggers fire in the narrow, literal sense
(no ≥3-module structural change, no new computing module/endpoint, prior verdict was CONTINUE not
ESCALATE, hardening-cadence counter is 0).
**We chose:** `full` depth anyway, citing trigger 1 (structural/cross-cutting) on a broader reading:
J-06's own acceptance requires a real-browser re-measurement across all 11 named pages plus a written
`reports/perf-budgets.md` update — an interaction between the ingest warm change, the `/evidence`
consumption path, and the committed-budgets artifact that only a real-browser QA pass (not unit tests)
can confirm — and this is the session's last failing/partial journey, where an accurate closure
narrative (ui-impact-analyst + phase-closure-auditor, only produced at full depth) matters most after
two prior iterations' documented closure-narrative drift (iter-4's merge-script lesson, iter-6's
retracted-regression framing). The evaluator's non-binding recommendation corroborates but is not the
sole reason.
**Reversible:** yes

## iter-7 — goal-decomposer

**Ambiguity:** iter-6's eval named "re-issue `user-visible-changes.md` + `ui-surface-map.md` (via
ui-impact-analyst) to replace the retracted framing" as a next-step item. Those are iter-6's own
point-in-time artifacts (`reports/phase-goal-ops-hardening-iter-6-*.md`); goal mode's artifact model is
append-only per iteration, and retroactively editing a past iteration's report would break that
pattern.
**We chose:** NOT to retroactively edit iter-6's artifacts. Instead, this iteration's own fix (warming
`drawdown_expectations` at ingest) removes the underlying cold-miss the retracted framing was about, so
iter-7's OWN fresh ui-impact-analyst/closure artifacts (produced because depth=full) will describe the
current, fixed state on their own terms — the stale iter-6 files remain as historical record, superseded
by iter-7's, not hand-edited.
**Reversible:** yes

## iter-7 — goal-evaluator

**Ambiguity:** J-05's step-4 acceptance ("health stays responsive throughout a heavy ingest") was hit
by a 7+ min hang, but the browser-qa itself flagged the deep cause as CONTESTED — earlier unrelated
`/api/backtest` MemoryErrors predate the test, suggesting pre-existing capacity fragility on the grown
live DB rather than a defect newly introduced by iter-7's diff. goal.md's decision tree triggers
REGRESSION on "a journey moved passing→failing" without requiring the current diff to be the proven
cause.
**We chose:** scored J-05 `regressed` and returned REGRESSION on the observed passing→failing move
(strong live evidence: screenshot + /proc + log signature; literal acceptance step; iter-6 had verified
health-200-on-20/20-polls). I did NOT downgrade to CONTINUE on the contested-attribution argument — a
regression is a regression regardless of proximate cause, and the whole point of the halt is for a human
to adjudicate cause and choose the fix (bound the ingest-time warm vs. tune the 6144MB cap vs. make heavy
paths fit). I recorded the AG-8 memory-exhaustion violation fail-closed (critical) with the attribution
caveat stated explicitly. A human who reads this as purely pre-existing capacity drift (not caused or
materially worsened by the diff) may `--acknowledge-regression` and re-scope, but the halt for review is
the correct default when a required Must-have journey breaks on its literal acceptance.
**Reversible:** yes

## iter-8 — goal-decomposer

**Ambiguity:** iter-7's evaluator offered three undirected recovery options for J-05's AG-8 memory
exhaustion ("bound the ingest-time warm vs. tune the memory cap vs. make heavy paths fit") without
mandating one, and its next-step item 2 ("health must fail-fast ... and the worker pool must recover
without a manual restart") does not specify whether that means new code in `app/api/health.py` itself
or removing the underlying memory pressure that prevents it from executing.
**We chose:** to bound peak RAM at the SOURCE — hardening `_refresh_ingest_aggregates`'s per-item warm
loops (coverage/market-phase/forward-aggregates/drawdown-expectations) to catch `MemoryError` distinctly
from their existing generic per-item exception handling and stop+`gc.collect()` on first occurrence,
rather than (a) raising `memory_cap_mb` (a threshold-loosening workaround that does not fix AG-8's
unbounded-growth pattern, only defers the same failure to a larger dataset) or (b) isolating ingest jobs
into a separate OS process (a bigger architecture change than this bounded fix, and closer to a rewrite
than goal.md's "additive, not a rewrite" non-goal allows). No new code in `app/api/health.py` itself —
its existing generic exception handling already degrades honestly once the process has allocation
headroom; this iteration's fix restores that headroom rather than adding a parallel fail-fast path.
**Reversible:** yes — if this iteration's live measurement shows peak RAM still approaches the cap after
the loop-level bound, the next iteration can escalate to raising the cap or process isolation without
undoing this change.

## iter-8 — goal-evaluator

**Ambiguity:** J-05 still carries status `regressed` and AG-8 is still recorded unresolved, but that
regression is iter-7's — already halted on, already human-acknowledged, with iter-8 dispatched as the
sanctioned recovery. The methodology's pre-finalize self-check E.1 says "any `regressed` status ⇒ verdict
must be REGRESSION", while the decision tree C.1 (the operative rule) fires on a journey that *moved*
passing → failing. Read strictly, E.1 would force a REGRESSION halt on every iteration until the journey is
fully restored, making `--acknowledge-regression` meaningless and re-presenting the human with a decision
they already made.
**We chose:** treated C.1 as operative and returned CONTINUE — no journey moved passing → failing in
iter-8, no NEW critical violation was introduced (scan-report CLEAN; the AG-10 gap was neither created nor
worsened by the diff), and every unblock path is agent-owned. J-05 stays `regressed` and AG-8 stays
unresolved (both still hard-block GOAL_ACHIEVED), so nothing is softened — only the halt is withheld. A
human who reads E.1 literally may re-halt.
**Reversible:** yes

## iter-8 — goal-evaluator

**Ambiguity:** AG-10 is a *critical* anti-goal and its MUST-apply clause is currently unsatisfied —
`host-guard.env` is present, but `scripts/start-backend.sh` applies only the config-derived `ulimit -v` +
`MALLOC_ARENA_MAX` (no `taskset` mask, no BLAS/OMP caps) and `scripts/dev.sh` applies no caps at all.
goal.md does not say whether an unmet MUST-apply clause is itself a "violation" of the same severity as
the REGRESSION trigger it does name ("stripping a HOST-GUARD marked block from a launch script").
**We chose:** recorded it as a `minor`, unresolved AG-10 entry rather than a critical one — nothing was
stripped or weakened (iter-8's product diff is `data_manager.py` + two test files), and goal.md's own
binding notes state "As of 2026-07-21 `dev.sh` applies no caps at all … closing that gap is in-scope
launcher work for the next iteration", i.e. the goal itself treats it as scheduled work rather than a
breach. Recording it critical would have forced a REGRESSION halt on a gap whose fix is fully agent-owned.
It is flagged as blocking GOAL_ACHIEVED and is item 3 of the next-step recommendation. I was not fully
certain of this severity call and state so explicitly.
**Reversible:** yes


<!-- condense.sh 2026-07-23T19:40:50Z: moved 7 entries (keep-iters=5) -->

## iter-9 — goal-decomposer

**Ambiguity:** iter-8's eval recommendation item 4 said to "fix the harness misrouting so `Frontend
Present: no` cannot suppress browser-qa when the spec's TESTING REQUIREMENTS name browser journeys" —
the actual defect lives in the goal-mode/phase-mode harness (`scripts/automation/*`, the neutral
`agents`/`config` asset source per CLAUDE.md), not in Trendora product code, and goal.md does not say
whether a goal-mode iteration spec should carry a fix to the shared framework harness itself.
**We chose:** did NOT touch `scripts/automation/*` or any neutral asset source. Instead this iteration's
own spec sets `Frontend Present: yes` explicitly — the honest value, since its TESTING REQUIREMENTS name
four browser journeys (J-01/J-03/J-04/J-05) regardless of whether any frontend *code* changes — which
routes around the exact bug that caused iter-8 to skip browser-qa outright (iter-8's spec had written
`Frontend Present: no`). Framework-harness maintenance is out of a product-facing decomposer's remit
(CLAUDE.md: edit the neutral asset source, never guess/patch the rendered mirrors from inside a product
iteration) and belongs to a human/maintainer pass, not this session's journey work. The underlying bug is
flagged in the iter-9 spec's NOTES as still open for the framework maintainer — it could recur if some
future spec sets `Frontend Present: no` while still naming browser journeys in TESTING REQUIREMENTS.
**Reversible:** yes

## iter-9 — goal-evaluator

**Ambiguity:** J-04's step-6 evidence is split across two builds. The browser lane FAILED it on the
pre-fix tree (real evidence: `UT-10-result.png`, run 110 `interrupted` with `0 snapshots · 0 trading days
in range`), the F1 `_checkpoint_run_record` fix then landed intra-iteration, and the only post-fix
observation is operator/API-level (`pump-j04-crash-recovery-evidence.md`: run 114 frozen at 59 snapshots /
64-of-84 dates vs. the all-zero pre-fix control run 113 in the same `GET /api/data` response). The journey
schema offers no status for "verified failing on a build that no longer exists, fixed, and re-verified at
a layer below the journey's own."
**We chose:** scored J-04 `partial` — steps 1-5 verified this iteration, step 6's product defect fixed and
credibly evidenced but NOT re-verified in a browser. Rejected `failing` (would cite a superseded build and
misrepresent the current tree), rejected `passing` (no rendered-surface evidence; both the round-3 auditor
and the phase-closure-auditor explicitly instructed that the F1 fix alone must not flip it), rejected
`unknown` (it WAS tested this iteration, and the audit's own "unknown pending the post-fix kill/restart"
framing predates the operator cycle that has since happened). `partial` blocks GOAL_ACHIEVED and schedules
exactly one browser cycle to close it.
**Reversible:** yes

## iter-9 — goal-evaluator

**Ambiguity:** The deferred on-load `/api/backtest` → `forward_aggregates_cached` MemoryError is an AG-8
(critical) dimension recorded unresolved, and decision-tree C.1 reads "a critical anti-goal violation is
unresolved → REGRESSION". Read literally, that would halt every remaining iteration on a finding the human
already halted on (iter-7), already acknowledged, and whose deferral this iteration's own spec records as
awaiting an owner decision.
**We chose:** recorded it fail-closed as a distinct CRITICAL, unresolved entry (so it hard-blocks
GOAL_ACHIEVED and cannot be quietly dropped) while NOT firing the REGRESSION branch on it — C.1's halt is
for a violation this iteration introduced, worsened, or newly discovered, and this one is none of those.
Same reading iter-8's evaluator applied to the carried AG-8. Nothing is softened; only the redundant halt
is withheld. Separately, I marked the ORIGINAL iter-7 AG-8 entry `resolved: true` — the specific violation
(heavy-ingest health hang + memory exhaustion + manual restart) is directly refuted by the qualified
evidence iter-8 lacked, gathered under caps applied by this iteration's own launcher block.
**Reversible:** yes

## iter-9 — goal-evaluator

**Ambiguity:** No artifact anywhere emits a `UT-J-05` verdict row (audit P3), yet J-05 is the iteration's
target journey and the DoD demands "J-05 passes all four acceptance steps via browser-qa-agent". The
evidence exists but is scattered across UT-04/05/06/07/08 plus a pytest run, and my rules say "no citation
→ unknown".
**We chose:** treated the per-step citation trace as satisfying the evidence bar rather than scoring J-05
`unknown` on a missing summary row — but I re-walked the mapping myself against `docs/goal.md`'s four
steps and personally opened UT-04/UT-06/UT-07/UT-08 and re-derived the health/VmPeak CSVs, instead of
accepting the audit's trace. A missing rollup row is a reporting gap, not an evidence gap, when every
underlying row is a real lane result I can open. Flagged as next-iteration work so a future reader is not
asked to assemble it.
**Reversible:** yes

## iter-10 — goal-decomposer

**Ambiguity:** J-04 step 6's acceptance literally requires "kill the backend process (simulated
crash); restart the backend" as live test actions. Across this session the browser-qa lane has
executed exactly this kind of restart/crash cycle itself for J-04 steps 3-4-5 (iter-9's UT-11/UT-12),
so it evidently has a sanctioned mechanism to do so. Separately, an out-of-band operator (pump) note
received alongside this dispatch asserted that "agents in this pipeline cannot start or stop services"
and that the fix is already "API-verified," implying only a rendered-surface observation remains. I
could not independently verify the operator's permission claim from any agent-facing artifact, and the
prior evaluator's own instruction (relayed from the round-3 auditor) was explicit that API-level
evidence alone must not be allowed to flip J-04 to passing.
**We chose:** wrote TESTING REQUIREMENTS for the standard path — browser-qa-agent re-drives J-04's
full six-step live acceptance itself, exactly as it has for steps 1-5 all session — and added a
fallback note (not a scope item) that if the harness genuinely cannot manage the kill/restart in this
environment, the operator may perform the documented sequence and hand the resulting state to
browser-qa-agent for it to read and score from the RENDERED page, not from API JSON alone. I did not
treat the operator note's claims as settled fact anywhere in the DEFINITION OF DONE or Data-contract
sections; the browser-lane observation requirement stands regardless of who triggers the restart.
**Reversible:** yes

## iter-10 — goal-evaluator

**Ambiguity:** My methodology says to open the screenshot for every journey whose status changes and let the
image outrank prose. J-04's decisive step-6 artifact is a DOM/HTML capture, not an image: every screenshot taken
after scrolling `/data` to the Run History row renders blank/near-black (I opened
`UT-J-04-step6-run119-scrolled.png` — it is genuinely a flat dark frame), a reproducible Chrome-MCP capture
artifact on this ~1,800-row page. The goal text asks for what the page *shows*, and nothing says the proof must
be a raster image.
**We chose:** accepted the verbatim `<tr>` DOM capture as rendered-surface evidence and scored J-04 `passing`,
but only after checking it is not disguised API evidence: the captured string "729 calendar days · 41 already
snapshotted · 225 non-trading" is composed client-side by `apps/frontend/app/data/page.tsx:2564-2573`
(`parts.join(" · ")` inside `data-testid="backfill-breakdown"`) and appears nowhere in the API payload, and its
numbers match the sqlite row I queried myself. A scroll-0 screenshot (`...-run119-data-page-top.png`) independently
shows `/data` live and healthy. A human who requires a raster image of the row itself may hold J-04 at `partial`
until the capture artifact is worked around (e.g. a narrower viewport or a filtered Run History view).
**Reversible:** yes

## iter-10 — goal-evaluator

**Ambiguity:** J-04 is a six-step journey, but only steps 5-6 were re-driven this iteration; steps 1-2 rest on a
2026-07-20 `perf-budgets.md` measurement and steps 3-4 on iter-9's controlled fetch-override simulations. iter-9
already flagged steps 1-2 as a WARN because that measurement predates iter-9 adding the host-guard
`taskset`/BLAS block to `scripts/start-backend.sh`, and this iteration's only timing datapoints (~35 s and ~37 s
from restart banner to first *observed* 200) are coarse operator polls, not measurements.
**We chose:** scored the journey `passing` on the strength of a literally empty product diff (`README.md` only —
scan-report, coherence audit and my own `iter-diff.md` read all agree), so no code path steps 1-4 cover could
have changed since iter-9 verified them; and treated the ~35 s figures as polling artifacts because run 119's
orphan finalize landed 1.3 s after the boot banner, which is incompatible with a 35 s boot stall. I did NOT let
that reasoning erase the gap: the un-re-measured ≤5 s budget is recorded as a carried caveat on J-04 and is item
1 of the next-step recommendation (`measure-perf.sh --boot`, a few minutes of work). A human who requires every
step of a Must-have journey to be re-driven in the iteration that scores it may hold J-04 at `partial`.
**Reversible:** yes


<!-- condense.sh 2026-07-24T08:16:35Z: moved 7 entries (keep-iters=5) -->

## iter-11 — goal-decomposer

**Ambiguity:** The dispatch prompt relayed an operator (pump) note, new to this session's decomposer
context, stating that "agents in this pipeline CANNOT start or stop services (the permission classifier
blocks them)" and that the subagent-resume channel is broken this session — meaning a developer/browser-qa
agent that hits a step needing a fresh backend process start (not a kill, just a start — nothing is
currently listening on the backend port per iter-10's eval) may be unable to execute it directly.
`bash scripts/measure-perf.sh --boot` (needed to re-measure J-06/J-04's ≤5s boot budget, unmeasured since
iter-9 added the host-guard block to `scripts/start-backend.sh`) is exactly this kind of step. goal.md
does not address who may launch backend processes, and I could not independently verify the permission
classifier's exact scope from any agent-facing artifact.
**We chose:** wrote the boot-budget measurement as the standard path (the developer/browser-qa agent runs
`bash scripts/measure-perf.sh --boot` itself) with an explicit NOTES fallback: if the executing agent's
environment blocks it, the operator runs the exact command and reports the console output/timestamps
verbatim, and the developer records that operator-provided output (with attribution) in
`reports/perf-budgets.md` rather than fabricating or silently omitting the number. This mirrors iter-10's
own accepted fallback pattern for J-04's kill/restart cycle (assumptions.md iter-10 entry) applied to a new
action (a boot-timing script) in a new context (an explicit pump note, not an inferred constraint). The
11-page real-browser TTI/on-load sweep itself is NOT written as operator-assisted — it needs no fresh
process start, only already-running services, which browser-qa-phase.sh's own service management (outside
the agent's tool-permission sandbox) is expected to provide, consistent with how J-01/J-03/J-04/J-05's
browser lanes have run all session.
**Reversible:** yes

## iter-11 — goal-evaluator

**Ambiguity:** Decision-tree C.1 reads "a critical anti-goal violation is unresolved → REGRESSION".
The AG-8 dimension (`forward_aggregates_cached` → `compute_forward_aggregates`, unbounded
`ScannerResult` load) is unresolved AND, unlike iters 8-10 where it was merely carried, it fired live
this iteration: two ingest-warm MemoryErrors and two on-load HTTP 500s. So "newly discovered damage"
is arguably true even though the violation itself is old and the product diff is empty.
**We chose:** did NOT fire the REGRESSION halt. This iteration's product diff is *literally* empty
(scan-report CLEAN, `iter-diff.md` "(no changes)", coherence-verified `git diff --stat -- apps/`
empty), so nothing could have been introduced or worsened here; the human deferred this exact code
path three times (iter-8/9/10) and re-halting re-presents a decision already made. Instead I upgraded
the ledger entry from "carried, not re-tested" to a fully evidenced live-firing record, kept it
critical + unresolved (so it still hard-blocks GOAL_ACHIEVED), made the owner decision item 1 of the
next step, and returned ESCALATE so a full-pipeline auditor adjudicates the blast radius. Nothing is
softened; only the redundant halt is withheld. **A human who reads C.1 literally should halt here, and
I say so in the eval's Halt Justification.**
**Reversible:** yes

## iter-11 — goal-evaluator

**Ambiguity:** J-05's step 2(b) requires the persisted run record to "list which inventory aggregates
its finalize hooks refreshed" and names five (latest-date snapshot, coverage payload, membership
timeline, market phase, research hot-key caches). This iteration's replay-triggered runs 121/122
recorded only four categories, and `forward_aggregates` is missing specifically because its warm
aborted on MemoryError. goal.md does not say whether an aggregate outside the named five failing to
warm breaks "aggregates are precomputed at ingest, never on the fly".
**We chose:** kept J-05 `passing`. `forward_aggregates` is not among the five the step names; the run
record is *honest* about what it did and did not refresh (which is what the step actually asserts);
and the replay's own acceptance expects all held. The unbounded-load dimension is scored under AG-8,
where it belongs, rather than double-counted as a journey failure. I flagged for the next full
iteration that the auditor must confirm the other two absentees (`latest_snapshot`, `market_phase`)
are legitimately skipped on a run that lands no new trading date, rather than silently failing too —
if they are not, J-05 should be re-opened.
**Reversible:** yes

## iter-11 — goal-evaluator

**Ambiguity:** J-04's steps 3-4 (pre-ready badge phase, crash-to-unreachable banner) were not re-driven
this iteration — the browser agent is barred from service actions this session — and were carried from
iter-9's controlled-fetch-override simulations. My own methodology says a status should rest on
evidence from the iteration that scores it.
**We chose:** kept J-04 `passing`. The product diff is literally empty, so `app/api/health.py`,
`app.engine.readiness`, `main.py`'s boot sequence and `warmup.py` — the entire code surface steps 3-4
exercise — provably cannot have changed since iter-9 verified them, and steps 1-2 (fresh 1.364 s boot)
and 5-6 (log grep + live DOM read, both of which I re-ran myself) ARE fresh this iteration. This also
closes iter-10's carried ≤5 s-boot caveat. A human who requires every step re-driven in the scoring
iteration may hold J-04 at `partial` until an operator-performed restart/kill cycle is observed live.
**Reversible:** yes

## iter-12 — goal-decomposer

**Ambiguity:** Every decomposer since iter-4 (iter-4/5/6/7/9/11) has scoped the `[NEW]`-flagged
`demo.sh ops-hardening --session-live` walkthrough (J-05/J-06's Acceptance names it) OUT of developer
scope on the stated reasoning that it "self-resolves automatically" via a session-mode demo-narrator
pass once J-06 reaches `passing`. I could not find that automatic pass anywhere in
`scripts/automation/run-goal.sh` — I grepped every `demo-phase.sh` invocation in that file and the only
one that exists is `bash "$SCRIPT_DIR/demo-phase.sh" "$iter_name"` inside `_run_showcase_steps` (per-iteration
record mode, no `--session` flag), run only for lean-depth CONTINUE/ESCALATE verdicts; there is no call
anywhere (including the GOAL_ACHIEVED path) that passes `--session` to `demo-phase.sh` or `--session-live`
to `demo.sh`. Separately, `demo-phase.sh`'s own header comment states `--live`/`--session` modes drive a
**visible, human-watched** Chrome window that narrates "waiting for Enter between steps" and explicitly
"writes no artifacts" — so even a manual invocation produces nothing an autonomous evaluator could later
cite as evidence. goal.md's J-06 acceptance says the walkthrough must be "viewable via
`demo.sh ops-hardening --session-live`," which is literally true right now (the command exists and would
run against every currently-passing journey) but is not a thing that can be "produced" as a stored,
gradable deliverable under this framework's evidence model.
**We chose:** kept this item OUT of iter-12's developer scope (same outcome as prior iterations) but
stopped repeating the "will self-resolve automatically" framing, since I have now falsified it by reading
the actual script. Recorded it as a second, parallel open owner-decision item alongside AG-8: either (a) a
human runs the command once and confirms it renders (satisfying the literal "viewable via" wording without
a stored artifact), (b) goal.md's acceptance wording is amended to name a recordable artifact instead, or
(c) a future framework enhancement adds a session-level record mode — none of which is this iteration's
(or any product-facing decomposer's) scope to invent. Did not touch `scripts/automation/*` per the
maintenance protocol.
**Reversible:** yes

## iter-12 — goal-evaluator

**Ambiguity:** J-06 step 2 says "assert every measurement is within budget" (and the success criterion is
"page loads stay within committed never-regress budgets"), but the Acceptance's "Honest status & anti-goals"
bullet contemplates something "slower than its budget" as long as it degrades honestly (no frozen/blank
frame). The G2 control confirmed `/api/indexes?full=true` is 43–51% over its ≤1.5 s budget on an idle host,
yet `/data` renders fully (panel populated, Ready badge). The two clauses pull opposite directions on whether
J-06 can be `passing`.
**We chose:** read step 2 / the success criterion as the primary gate (loads must stay within budget) and the
honest-status bullet as a defensive AG-8-tie-in fallback (IF over budget, still degrade honestly — not "over
budget is fine"). So scored J-06 `partial`, not `passing`, rejecting the audit's PASS_WITH_GAPS "may be scored
passing" recommendation. The graceful-degradation clause IS satisfied (opened `UT-04-result-top.png`), which
keeps this a latency shortfall rather than an AG-8 crash — but a committed budget breached by half on an idle
host is a real J-06 failure, not a pass. A human who reads the honest-status bullet as licensing "over budget
but honest = pass" would score J-06 `passing` (all five Must-haves then passing, still GOAL_ACHIEVED-blocked
by AG-8 + the walkthrough). Reversible.
**Reversible:** yes

## iter-12 — goal-evaluator

**Ambiguity:** Decision-tree C.1 reads "a critical anti-goal violation is unresolved → REGRESSION." AG-8
(`forward_testing.py:826` unbounded load) is unresolved and fired live again this iteration (3-for-3 on the
sampled runs). Read literally, C.1 halts.
**We chose:** did NOT fire REGRESSION — same reading iters 8/9/10/11 applied (and the human ratified by
continuing the session each time). C.1's halt is for a violation this iteration INTRODUCED, WORSENED, or NEWLY
DISCOVERED; this one is none: the product diff is literally empty (`iter-diff.md` "(no changes)", scan CLEAN,
coherence-verified), and the blast radius was SMALLER than iter-11 (caught internally, zero client-facing 500s
vs iter-11's two). Recorded it critical + unresolved so it still hard-blocks GOAL_ACHIEVED and cannot be
quietly dropped; withheld only the redundant halt on a decision the human has already made four times. A human
reading C.1 literally may still halt here — the eval's Halt Justification says so and lists the four owner
unblock options.
**Reversible:** yes


<!-- condense.sh 2026-07-25T01:03:55Z: moved 7 entries (keep-iters=5) -->

## iter-13 — goal-evaluator

**Ambiguity:** Decision-tree C.1 reads "an unresolved critical anti-goal → REGRESSION," but iters 11/12
established (and the human ratified by continuing) a doctrine that C.1's halt only fires for a violation
INTRODUCED/WORSENED/NEWLY-DISCOVERED *by this iteration's code*, and here the AG-8 code path is
byte-unchanged (TC-12). The trigger for the ~12-min outage was concurrent browser-qa test load, not
iter-13's product diff — so whether the observed-severity escalation counts as "worsened/newly
discovered" (fire REGRESSION) vs "same carried bug, just re-observed" (CONTINUE, as iter-12 did) is a
genuine interpretation call.
**We chose:** fired REGRESSION. Treated the escalation from "silent internal abort, zero client 500s"
(iter-12) to "full ~12-min availability outage requiring an operator hard-restart" (iter-13) as
NEWLY-DISCOVERED damage that changes the stakes of the deferred owner decision — not a re-presentation of
the settled call. The specific justification iters 11/12 used to withhold the halt (blast radius smaller
than iter-7, self-recovers, no manual restart) is directly falsified this iteration, and the affected
property (availability / "never a frozen frame") is the exact thing this ops-hardening goal exists to
guarantee. Corroborated by three independent artifacts (audit, closure, screenshot), not just the pump
note. A human who reads C.1 as strictly code-scoped, or who regards AG-8 as already-decided-defer
regardless of severity, would instead score CONTINUE (or plain STALLED, since all remaining GOAL_ACHIEVED
blockers are owner-owned) — I note STALLED as the true second decision-tree match in the eval.
**Reversible:** yes

## iter-14 — goal-decomposer

**Ambiguity:** J-07 step 4 permits either "a test hook OR a tightened cap in a throwaway process" and its
step 1 literally describes a SINGLE long-lived sequential process (warm all horizons, then poll health).
But iter-13's actual REGRESSION trigger was CONCURRENT load (4 replay backfills + a diagnostic read), and
the repo's existing "no leaked lock" tests (`test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds`
and siblings in `test_data_manager.py`) are all `monkeypatch`-injected MemoryError, a same-layer stub that
already failed to predict iter-11's live 500s or iter-13's live 12-minute wedge. goal.md does not say
whether J-07's Acceptance ("a memory-pressure abort never leaves the process wedged") must be proven under
a REAL tightened-`ulimit -v` induction and under concurrent callers, or whether the literal single-process/
test-hook-or-monkeypatch reading suffices.
**We chose:** wrote TESTING REQUIREMENTS to require BOTH a real (non-monkeypatched) tightened-`ulimit -v`
subprocess test AND a concurrent-caller (N>=4) test mirroring iter-13's actual trigger shape, in addition
to the byte-identity tests J-07 literally asks for. This is a stricter reading than the letter of step 4's
permissive "or," chosen because the cheaper (monkeypatch-only, single-process) reading is exactly the
methodology that already missed this defect twice this session (iter-11, iter-13) — repeating it would let
the recovery iteration "pass" its own tests while leaving the reproduced failure mode unverified. A human
who reads J-07 literally (test hook OR monkeypatch is sufficient, no concurrency requirement) may consider
TC-3/TC-4 as this iteration's own scope-add rather than something goal.md strictly requires.
**Reversible:** yes

## iter-14 — goal-decomposer

**Ambiguity:** The pump note instructed "write it as operator-supervised" for J-07 steps 1/3's full-basis
warm + VmPeak measurement (an AG-10-class heavy pass), stating the owner's plan approval already
authorizes it, but did not specify whether "operator-supervised" means the agent runs the confined
measurement itself (as iter-3/8/9's own heavy passes were performed, per `reports/perf-budgets.md`'s own
protocol descriptions) or whether the human must literally type the launch command this session, given
other pump/decomposer notes this session (iter-10, iter-11) that treated backend process starts as
potentially blocked by a permission classifier.
**We chose:** wrote the standard path as the developer/reviewer running the confined pass directly
(`scripts/start-backend.sh` under the declared host-guard caps, sampler, and watchdog — the same
mechanism iter-3/8/9 used), with an explicit operator-fallback if this session's environment blocks the
process start: the operator starts/monitors and reports console output, pids, and timestamps verbatim for
attributed recording. This mirrors the accepted fallback pattern from iter-10/iter-11's own ledger entries
applied to a new action (the J-07 heavy pass) in the same operational context. A human who reads
"operator-supervised" as requiring the literal human-typed command every time may instead treat this
iteration's TC-5/TC-6 as blocked pending an explicit operator action, regardless of the standard-path
attempt's outcome.
**Reversible:** yes

## iter-14 — goal-evaluator

**Ambiguity:** TC-6's literal GWT (induce memory pressure on the LIVE full-deep-basis TC-5 process; assert
isolated abort + continued serving in that SAME process) was not executed — the operator judged ballooning a
6 GB-capped process on this two-hard-reset host an unjustified AG-10 hazard. The spec explicitly assigns the
sufficiency call to the evaluator: is TC-3 (a REAL `ulimit -v` induction, but on a synthetic 60K-row
subprocess) + TC-5's organic MemoryError-absence enough for J-07 step 4?
**We chose:** ruled the two-leg evidence REASONABLE — TC-3 is a real (non-monkeypatched) RLIMIT_AS induction
that demonstrates the exact honest-abort-then-same-process-recovery mechanism TC-6 wants, and forcing a
live-process induction on this crash-history host is a genuine hardware hazard the host-guard regime exists
to prevent. So I did NOT treat TC-6-partial as a hard blocker requiring a halt. I did NOT upgrade it to a
literal PASS either: J-07 stays partial (independently held there by UT-04 + the unproduced walkthrough), and
a live-process induction remains a candidate owner-authorized follow-up. A human who requires TC-6's literal
GWT before crediting J-07 step 4 would keep that step explicitly unproven.
**Reversible:** yes

## iter-14 — goal-evaluator

**Ambiguity:** Decision-tree C.1 fires on an unresolved critical anti-goal. AG-8 drove iter-13's REGRESSION;
UT-04 shows the SAME trigger (concurrent load on the deep basis) still produces a 211.8s `/backtest` anomaly,
so "the fix fully holds under the reproduced trigger" is not proven — is AG-8 resolved or still open?
**We chose:** marked AG-8 RESOLVED. AG-8's own text forbids a crash, memory exhaustion, or an unbounded
whole-table ORM load; UT-04 is none of these (I opened `UT-04-resolved-slow.png`: page rendered fully, Ready
badge, health green, VmPeak flat, self-resolved) — it is a latency/lock-contention regression (J-06 budget
territory), a DISTINCT non-critical follow-up. Keeping AG-8 critical/unresolved would falsely imply the
memory-exhaustion/crash defect persists, which three independent verifications (evaluator CSV recompute,
reviewer rerun, audit rerun) contradict. I did NOT launder UT-04 away — it keeps J-06 and J-07 partial and is
next-step item 1. A human who reads AG-8 as "the guarantee must hold under the exact reproduced concurrent
trigger before it is resolved" would keep AG-8 open and likely score STALLED (remaining blockers then
owner-owned) or CONTINUE.
**Reversible:** yes

## iter-15 — goal-decomposer

**Ambiguity:** J-06's acceptance ties latency to "page loads stay within committed never-regress
budgets" via a step-1 sweep that reads as a single-page-at-a-time measurement; J-07's acceptance
literally requires only "no unbounded whole-table ORM materialization," "a memory-pressure abort
never leaves the process wedged," and "health/readiness stay truthful" — it does not explicitly
require `/backtest`'s OWN response time to stay in budget during the very concurrent warm+serve
scenario its own step 1 constructs. Whether UT-04's 211.8s concurrent-cache-miss finding is
therefore a J-06 budget violation, a J-07 "honestly responsive... while serving" violation, both, or
neither (health stayed green, no wedge, no crash) is not settled by goal.md's literal text — iter-14's
own audit flagged exactly this: "the ≤1.5s budget belongs to a prior phase under a condition that
phase never tested — it is not one of iter-14's DEFINITION-OF-DONE items."
**We chose:** followed iter-14's evaluator, who already read UT-04 as blocking BOTH J-06 and J-07
(scored `partial`, not `passing`, specifically because of this finding) rather than treating it as
out-of-contract disclosure. This iteration's entire scope — root-causing and fixing the
concurrent-load latency, gated PASS/WARN against the committed ≤1.5s budget — builds on that same
reading, continuing rather than re-litigating it. A human who reads J-06/J-07 literally (no
concurrent-load latency requirement in either journey's own step text) could instead score both
`passing` today with UT-04 disclosed as a footnote, in which case this iteration is still legitimate
hardening but not literally required for GOAL_ACHIEVED.
**Reversible:** yes

## iter-15 — goal-evaluator

**Ambiguity:** With the stacking pathology fixed, the residual `/backtest` cold-MISS is 178.74s (~119x
over the ≤1.5s budget) but the page renders honestly (Ready, honest NA, never frozen) and the WARM load
is fast (116-554ms). The pump note explicitly asks whether J-06/J-07's serve-responsiveness clause is
"satisfied by stacking-fixed + honest-skeleton + warm-path-fast (the cold-MISS being an inherent one-compute
cost the ingest warm exists to pre-empt)" — which would flip both to passing → GOAL_ACHIEVED — or whether
it stays partial pending an owner decision. J-06 step 2 ("assert every measurement is within budget") and
the acceptance's honest-status bullet ("anything slower than its budget shows honest progress, never a
frozen frame") pull opposite directions, and J-07's own step text arguably requires only health/no-wedge,
not `/backtest`'s own response time.
**We chose:** did NOT flip J-06/J-07 to passing on the evaluator's own authority; kept both `partial` and
returned STALLED to route the acceptance decision to the owner. The goal's Success Criteria commit to
"page loads stay within committed never-regress budgets", a 119x breach (plus a distinct 5.37s breach) is
a real recorded budget violation, and iter-12's human-ratified precedent kept J-06 partial rather than
launder a budget breach into a green check. The pump note, audit §5, and QA #3 all independently frame the
acceptance as an owner call. A human who reads J-06/J-07 literally (no concurrent-cold-MISS response-time
requirement in either journey's own step text; honest-status clause governs the slow path) could instead
accept option (3), score both passing, and reach GOAL_ACHIEVED — which is exactly why this halts for the
owner rather than the evaluator deciding it silently.
**Reversible:** yes

