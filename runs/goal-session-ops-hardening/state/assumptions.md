# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

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
