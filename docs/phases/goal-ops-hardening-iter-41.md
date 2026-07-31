# Goal Iteration 41 — Repair the verification lane, then close the last unbounded whole-table load

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 41
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (mandatory, no exceptions)
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(critical)*

## GOAL

Make the seven required-still-passing journeys verifiable again (they shipped with ZERO evidence
last iteration while every gate reported clean), and close the session's oldest open AG-8 finding
by bounding `_BarCache.prefill`'s own in-memory accumulator — the last code path that streams the
full `daily_prices` table into RAM.

## BACKGROUND

Prior verdict: **ESCALATE** (5th consecutive) — depth is `full` per the binding rule, no exceptions
(Full trigger 3). iter-40's own evaluator found that all seven required-still-passing journeys
(J-01, J-03, J-04, J-06, J-08, J-09, plus J-07 itself) shipped completely unverified — zero
screenshots, zero replay artifact, zero demo steps — while review, QA, AND the deterministic
closure gate all reported clean; only the auditor caught it (the 4th consecutive iteration where
that is true). Direct inspection this iteration confirmed the two root causes are still live in
the framework tooling: (1) `browser-qa-phase.sh` / `goal-iter-lean.sh` / sibling `*-phase.sh`
scripts still derive `BACKEND_HEALTH_URL` from the framework's generic `${CHAIN_BACKEND_HEALTH_URL:-http://localhost:<port>/health}`
default and surface that (wrong, for this project) URL to the browser-qa LLM dispatch — even
though `demo_runner.py`'s OWN deterministic-replay precondition was already fixed at iter-39 to
resolve the correct `/api/health` path (`apps/backend/main.py:127` mounts the health router under
`/api`); and (2) the `ui-test-designer` agent's neutral-source "Backend-only phase handling"
(`incredible_auto_dev/agents/ui-test-designer/body.md`) still stubs out ALL UI test-case
generation — including the required-still-passing regression rows — the instant a spec declares
`Frontend Present: no`, which is exactly this session's steady state for ops-only iterations. Per
the priority rubric this is the clearest possible "unblocker" (rule 3): nothing else in this
session can be trusted `passing` until journeys can actually be re-checked, and per rule 1 nothing
here is a regression (four journeys read `unknown` — never tested — not `failing`; no journey
actually broke, per the evaluator's own explicit finding). Bundled into the SAME iteration (see
`assumptions.md` iter-41 for the explicit reasoning on why this is one iteration, not two): the
LAST unbounded whole-table load named in goal.md's Success Criteria — `_BarCache.prefill`
(`apps/backend/app/engine/prices.py:132-142`) already streams its query via `.yield_per(batch)`
(the cursor is bounded, since before iter-35) but still accumulates every `daily_prices` row into
one resident `by_symbol` dict (~1.1 GB at the live basis, iter-29/d, carried 12 iterations). This
is DISTINCT from and not closed by iter-35/36/37's earlier, narrower attempt at this same row,
which bounded only `membership_timeline_cached`'s cache-MISS sub-call and explicitly left
`_BarCache.prefill` itself untouched (see `blueprint.md`'s Coverage payload row, iter-35 text).
Also folded in (diagnostic only, explicitly NOT a cap retune — binding iter-39/40 instruction):
`faulthandler`-based thread identification for iter-39/u's still-unexplained run-1 freeze, and
extending the wedge-drill monitor to keep polling past terminal job status (audit B2), since both
ride along cheaply on the same drill infrastructure this iteration already touches. Per rule 5,
this iteration's ONE risky product-code action is the `_BarCache.prefill` bound; the
verification-lane fix and drill diagnostics are tooling/instrumentation, not a second risky
product change — iter-33/g (Regime Lab's cold `view=pooled` dispatch) is deliberately deferred a
6th time to keep it that way.

**Lesson applied (iter-40, binding):** "a precondition check must distinguish connection refused
(down) from any HTTP status (up) — never treat a 404 as absence" and "`Frontend Present: no` may
suppress NEW-surface UI tests, never the required-still-passing regression replay." Both are
directly implemented below, not just noted.

**Lesson applied (iter-39, binding):** "a drill that has probed three times without hitting its
target is diagnosing the wrong thing" and "`.yield_per()` bounds the DB cursor, not your
accumulator" — exactly the distinction this iteration closes in `_BarCache.prefill`.

## IN SCOPE

### Backend / Pipeline tooling
- [ ] Fix the health-check URL(s) surfaced to the browser-qa LLM dispatch: `browser-qa-phase.sh`,
      `goal-iter-lean.sh`, and any sibling `*-phase.sh` script that derives
      `BACKEND_HEALTH_URL="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${PORT}/health}"` must
      surface Trendora's actual `GET /api/health` path to the agent, mirroring
      `demo_runner.py`'s existing `resolve_backend_health_url` project-specific override. A live
      backend answering a non-200 on the wrong path must never be reported to the agent as "down."
- [ ] Fix `incredible_auto_dev/agents/ui-test-designer/body.md` (the neutral source — never the
      rendered `.claude/agents/ui-test-designer.md` mirror directly): `Frontend Present: no` stubs
      out NEW-surface UI test-case generation ONLY; the required-still-passing journeys named in
      the iteration spec still each get one `UT-J-XX` regression test case written into the test
      plan. Re-render via `python3 scripts/automation/sync-cli-assets.py --cli claude` before this
      iteration's own test-plan step runs.
- [ ] Extend `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` (additive to
      the already-shipped iter-39 `BLOCKED` class — do not reopen that mechanism): a merged result
      set with zero executed test cases for a required-still-passing journey must not produce a
      clean `SKIPPED`/`PASS` headline.
- [ ] Bound `apps/backend/app/engine/prices.py:132-142`'s `_BarCache.prefill`: keep the existing
      `.yield_per(batch)` cursor streaming, but stop accumulating every row into one resident
      `by_symbol` dict. Byte-identical `Bar` output required for every existing consumer (coverage
      payload, membership-timeline resolver, any other `_BarCache` caller) via a fixture-backed
      equality test. Reconcile/retire iter-35/36/37's narrower
      `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` target, which this
      global bound supersedes.
- [ ] Diagnostic only (do NOT retune `server.memory_cap_mb` again): arm
      `faulthandler.register(signal.SIGUSR1, all_threads=True)` in the throwaway-DB wedge-drill
      launch and re-run the SAME tightened cap once to positively identify the thread frozen in
      iter-39/u's run-1 — report whichever outcome actually occurs (identified freeze, or no
      recurrence) honestly.
- [ ] Extend `wedge-drill/monitor.py` to keep polling at the same interval for a fixed window PAST
      a terminal `job_status` (audit B2), instead of stopping the instant the row reads
      `ok`/`interrupted`.
- [ ] Small, already written down: add a count-based floor to `_checkpoint_run_record`'s existing
      time-based throttle (dev Known Issue #2 / reviewer NOTE — same `message` field, same
      serializer, no new field). Add `BLOCKED` to `verdicts.py::BrowserQAVerdict` and the four
      `grep -oE 'PASS|FAIL|SKIPPED'` sites in `goal-iter-lean.sh` (audit T3 hygiene).

### Frontend
- None. No new UI surface this iteration — the verification-lane fix's whole point is that this
  must not suppress the required-still-passing regression check anyway (see TESTING REQUIREMENTS).

### New user-facing capability
None — ops/tooling correctness and an internal memory bound; no Evidence Claims (per goal.md's
Loop mechanics, J-01…J-06 carry none, and this iteration touches neither the referee nor the
ledger).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible to the end user. `/data`'s coverage payload keeps producing byte-identical values
through a bounded code path instead of an unbounded one; a user cannot tell the difference except
that the process no longer risks the run-1-class freeze under memory pressure.

### Blueprint conformance
No new page/nav. J-05 and J-07 keep their existing homes (`/data` coverage/job-history panels,
global readiness badge + `/backtest`) per `blueprint.md`'s Information Architecture table — see
the iter-41 update paragraph and the Coverage payload / Job history row notes appended there.

### Data-contract additions
None. This iteration bounds an EXISTING computing module
(`app.engine.data_manager._compute_coverage_uncached` via `app.engine.prices._BarCache.prefill`),
served by the SAME EXISTING endpoint (`GET /api/data`) — no second producer, no second endpoint,
no schema change. The verification-lane fixes and drill diagnostics are pipeline/QA-tooling
artifacts, not served/displayed values (iter-18/23/33 precedent) — no Data Contract row.

## OUT OF SCOPE

- iter-33/g — Regime Lab's cold `view=pooled` background dispatch (deferred a 6th time; rule 5
  keeps this iteration's one risky product-code action confined to `_BarCache.prefill`).
- Any re-tuning of `server.memory_cap_mb` (binding iter-39/40 instruction — the cap trials are
  done; this iteration only instruments the SAME cap to identify the frozen thread).
- J-07's `[NEW]` walkthrough recording (capture-only, never an iteration's goal — 10 iterations
  unrecorded, ride-along only).
- Both owner-decision items: the `/api/health` ≤ 0.1 s budget (iter-34/j, missed 7 consecutive
  times — three dispositions, all his) and whether `start-frontend.sh` joins
  `HOST_GUARD_MARKER_FILES` (iter-33/i). Neither is re-planned as agent work this iteration.
- Re-opening `_missing_data_diagnostic`'s streaming fix, the time-based checkpoint cadence, the
  `BLOCKED` verdict class itself, or J-07 steps 1/2/3/step-4-isolation — all DONE/CLOSED per
  iteration-state.md's binding "Do not redo" list.
- Any launch-script or `host-guard.env` change — AG-10's byte-frozen launch scripts are untouched;
  the drill diagnostics still launch exclusively via `scripts/start-backend.sh`.

## DEFINITION OF DONE

- [ ] Target journeys J-05, J-07 pass (or, for J-07, its remaining acceptance-clause state is
      re-scored with fresh, this-iteration evidence) via browser-qa-agent.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 each get fresh,
      non-`SKIP` mechanical verification (deterministic replay + LLM fallback) this iteration —
      not a carried-forward reference.
- [ ] An all-SKIP/zero-executed regression run can no longer merge into a clean `SKIPPED`/`PASS`
      headline.
- [ ] No anti-goal violation introduced; AG-8 specifically improves (accumulator bounded,
      byte-identical, measured).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-41-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05, J-07 (targets); J-01, J-03, J-04, J-06, J-08, J-09 (required-still-passing,
  fresh evidence mandatory — see TC-4).
- Unit/integration: `_BarCache.prefill` byte-identity fixture test; `merge_ui_test_results.py`
  all-SKIP-detection test; `_checkpoint_run_record` count-based-floor test;
  `BrowserQAVerdict`/`goal-iter-lean.sh` `BLOCKED`-recognition test.
- Error cases: a required journey with zero executed test cases must be rejected as "clean," not
  silently accepted; a wedge-drill freeze must produce a positively-identified thread or an
  honestly-reported non-recurrence, never a silent cap-widening.

- TC-1: given the `ui-test-designer` neutral source is fixed and re-rendered, when an iteration
  spec sets `Frontend Present: no` and names 6 required-still-passing journeys, then
  `reports/phase-goal-ops-hardening-iter-41-ui-test-plan.md` contains one `UT-J-XX` regression
  test case per required journey and zero NEW-surface test cases.
- TC-2: given the backend is running and mounted at `/api/health` (not `/health`), when
  `browser-qa-phase.sh`/`goal-iter-lean.sh` compute the health URL surfaced to the browser-qa-agent
  dispatch, then the surfaced URL resolves to `http://localhost:<port>/api/health`, and a
  wrong-path 404 is never reported to the agent as "backend down."
- TC-3: given a browser-qa run whose merged results show zero executed test cases for a
  required-still-passing journey, when `merge_ui_test_results.py` builds the merged headline, then
  the merged file's verdict is NOT a clean `SKIPPED`/`PASS` — it surfaces the gap so the
  goal-evaluator and `closure_gate.py` treat it as an unmet DoD item.
- TC-4: given this iteration's own dev pass re-renders `.claude/agents/ui-test-designer.md` before
  the test-plan step runs, when browser-qa executes against J-01, J-03, J-04, J-06, J-08, J-09,
  then each produces a fresh, dated evidence artifact (screenshot or deterministic-replay record)
  under this iteration's own report/evidence path — not a reference to iter-39's artifacts.
- TC-5: given the throwaway-DB wedge-drill launched via `scripts/start-backend.sh` with
  `faulthandler.register(signal.SIGUSR1, all_threads=True)` armed, when the tightened-cap drill is
  re-run once, then either (a) a freeze recurs and sending `SIGUSR1` writes an all-thread stack
  dump to the drill log identifying the blocked thread/function, or (b) the freeze does not
  recur and the drill log records that outcome honestly without claiming the freeze is fixed.
- TC-6: given `_BarCache.prefill` is changed to bound its `by_symbol` accumulator, when the same
  fixture inputs run through the OLD and NEW implementations, then every returned `Bar` for every
  symbol/date is byte-identical (fixture-backed equality test), and a full-universe prefill's peak
  RSS/VmPeak on the live basis is measured and recorded in `reports/perf-budgets.md` lower than the
  unbounded baseline.
- TC-7: given `wedge-drill/monitor.py` polling a job, when `job_status` first reads a terminal
  value, then the monitor continues polling at the same interval for a fixed additional window
  before stopping, with every additional poll's HTTP status/latency recorded in the drill CSV.
- TC-8: given `_checkpoint_run_record`'s existing 1.0 s time-based throttle, when K dates complete
  within one throttle interval (a fast per-date compute, mocked clock that never crosses the time
  threshold), then a count-based floor forces a checkpoint write on the Kth date regardless of
  elapsed time.
- TC-9: given `verdicts.py::BrowserQAVerdict` and the four `grep -oE 'PASS|FAIL|SKIPPED'` sites in
  `goal-iter-lean.sh`, when a `BLOCKED` verdict is emitted, then `BrowserQAVerdict` accepts it as a
  legal enum member and every one of the four grep sites' pattern also matches `BLOCKED`.

## NOTES

- Session state: 5 consecutive ESCALATEs; depth is `full` with no exception available (Full
  trigger 3). See `assumptions.md` iter-41 for why the verification-lane fix and the
  `_BarCache.prefill` bound are one iteration rather than two.
- iter-40/y (verification lane off) and iter-29/d (`_BarCache.prefill` unbounded accumulator) are
  this iteration's two headline closures; both were logged in `iteration-state.md`'s "Active
  blockers" as top/second priority.
- Owner decisions carried unchanged and unplanned here: iter-34/j (`/api/health` ≤ 0.1 s budget,
  missed 7 consecutive times — ratify honest-WARN, rescope for the bounded background-compute
  window, or commission a cached-readiness snapshot) and iter-33/i (`start-frontend.sh` →
  `HOST_GUARD_MARKER_FILES`). Both should be settled by the owner before any GOAL_ACHIEVED attempt.
- `blueprint.md` updated: a new iter-41 narrative paragraph before "## Information Architecture,"
  plus iter-41 notes appended to the Coverage payload and Job history Data Contract rows. No IA
  change, so no `blueprint.reapproval-requested` file was written.
