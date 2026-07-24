# Goal Iteration 20 — Take the historical-view cold recompute off `/backtest`'s request path

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 20
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07, J-08
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or
    alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars >
    as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from
    the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader
    pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing
    consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest
    "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are
    forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may be
    introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe
    rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project
    launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host
    caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present
    (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or
    bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless
    of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware
    resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance
    budget to optimize away. *(critical)*

## GOAL

A first-ever view of any historical `/backtest` as-of date never blocks the request on a multi-second
forward-aggregate compute — it renders instantly with an honest interim state while that date's own evidence
finishes warming off the request thread, closing the SECOND (and, on current evidence, last known) shared
latency/honesty blocker behind J-06/J-07/J-08.

## BACKGROUND

Iter-19 fixed the create-once `backfill_run_forward_returns` write (877 ms → 13.9 ms mean under 6×
concurrency) and browser-QA's own UT-04 (re-opened by this decomposer) proved it: three concurrent
first-touch requests for the same never-before-viewed historical date (`2025-05-30`) all showed
`backfill_forward_returns_ms` staying small (12.2, 13.6, 79.9 ms) — the iter-19 fix holds. But the SAME three
log lines showed `total_ms` of **9548, 54483, and 54328 ms**, overwhelmingly dominated by a DIFFERENT logged
field this iteration's diff never touched: `ensure_loop_ms` (**9288, 54281, 54084 ms**). Reading
`apps/backend/app/api/backtest.py` directly confirms the mechanism: for a historical (`is_latest == False`)
as-of whose `resolved_forward_aggregate_evidence` read is not already `"ready"`, the endpoint (and MCP
`query_backtest`, identical logic) runs `for h in cfg.walk_forward.horizons:
forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)` **synchronously on the request
thread**, then re-resolves, before returning anything — a genuine "skeleton waiting on a fresh compute" (J-08
step 2's own forbidden phrase) with **zero loading affordance** on the page the whole time (audit F1,
ux-regression). This is precisely the pattern the pump note for this iteration named as the mandate: find
what `ensure_loop_ms` measures, diagnose the historical-first-view stall, and take it off the request path.

**Why it stalls 9.6–54 s, not a fixed small number:** `forward_aggregates_ingest_cached` calls
`compute_forward_aggregates(session, h, cfg, as_of=D)` once per configured horizon (5) — each an
as-of-scoped-but-otherwise-full aggregation over every `ForwardReturn`/`ScannerResult` row for every stored
run dated ≤ D. That cost is inherent to a genuinely historical D deep in a 20-year basis; it is bounded
(streamed, column-projected, byte-unchanged since iter-14) but not FAST. The already-existing per-key
single-flight guard inside `forward_aggregates_ingest_cached` (iter-15) means only the first concurrent
caller for a given `(horizon, asof_key, dataset_version)` computes; the other two waiters in UT-04's capture
each call `event.wait(timeout=45.0)` — consistent with the observed ~54 s figures (≈ the 45 s bounded wait
plus a redundant independent compute on timeout, TC-8's documented rare-fallback path, evidently not rare
under this concurrency shape). The request thread should never be waiting on any of this at all.

**Why not simply remove the historical carve-out, and why not precompute every historical date at ingest —
two alternatives considered and rejected:**
1. *Remove the historical ensure-loop entirely, always serve the resolver's own cross-`asof_key` fallback.*
   Rejected: a historical date's OWN evidence would then never be computed by anything (ingest only warms the
   LATEST date's aggregates) — a real regression of the existing time-machine capability (J-14/17/18) that no
   journey step asks for.
2. *Precompute every historical `ScannerRun.asof_date`'s forward aggregates at ingest, the way the LATEST
   date already is.* Rejected: `_dataset_version` is a GLOBAL fingerprint bumped by any ingest anywhere in the
   dataset (confirmed by reading `resolved_forward_aggregate_evidence`'s own "SAME `asof_key`, a PRIOR
   `dataset_version`" sub-case), so every ordinary ingest would need to re-warm potentially ALL ~180+ stored
   historical dates × 5 horizons to keep them "ready" under the new stamp — unbounded, ever-growing ingest
   cost for a page few users view, exactly the whole-table-scale-of-work anti-pattern this session exists to
   retire (goal.md's own "cannot be precomputed (user-parameterized)" carve-out already rules this out for
   equivalent cases).

**The fix built here:** keep the historical evidence lazy, create-once, and request-triggered (preserving the
carve-out's substance and byte-identical served values) but move the actual compute **off the requesting
thread** — a single-flight-guarded background dispatch (own DB session, mirrors the established
`data_manager.start_data_job` / `warmup.start_warmup` thread-plus-own-session idiom already in this codebase)
so `GET /api/backtest` and MCP `query_backtest` return immediately with whatever
`resolved_forward_aggregate_evidence` already finds (`refreshing` via its existing cross-`asof_key`/version
fallback, or `not_yet_computed`), while that SAME resolver will find the exact date `ready` on a later view
once the background compute lands. This is a genuine reading of J-08's literal "never a request-path
recompute" against the iter-16 decomposer's own carve-out precedent — logged to `assumptions.md` (iter-20),
not silently decided.

**Target-selection rubric applied:** Rule 1 (regressed first) — N/A, nothing regressed (iter-19 eval:
none). Rule 2 (consolidation before features) — N/A, iter-19's `coherence.md` is `COHERENCE-PASS` (re-read
this iteration; re-confirmed). Rule 3 (unblockers) — this is unblocker work: J-06/J-07/J-08 share this ONE
serving-path defect, so one fix (not three separate changes) is the correct shape, continuing the exact
pattern iterations 14–19 have each used for this cluster. Rule 5 (never bundle two risky journeys) — this is
ONE moderate-to-high-risk change (a new concurrency/background-dispatch mechanism on a cluster with iter-13's
REGRESSION history) carried across three journey labels that share it, not two unrelated risky changes. Rule
6 (don't pick a human-blocked journey) — J-04's remaining work (the disruptive kill/restart replay) stays
OPERATOR-gated and is NOT picked as a target; it is carried in Required-still-passing with its owed replay
flagged contingently below, unchanged in kind from iterations 15–19's own treatment.

**Depth: full — trigger 1 (structural/cross-cutting) fires; no other trigger needed.** The fix touches ≥3
modules whose interaction is not covered by any one journey's own tests: `apps/backend/app/engine/
forward_testing.py` (the new dispatch mechanism), `apps/backend/app/api/backtest.py` and
`apps/backend/app/mcp/tools.py` (both request-path callers, whose serving behavior changes), and
`apps/frontend/app/backtest/page.tsx` (a status-copy audit/correction). It introduces a genuinely NEW
concurrency primitive (request-triggered background compute) on the exact cluster iter-13's REGRESSION came
from, and changes the literal assertions of two existing tests that previously codified synchronous
same-call completion — none of this is covered by a single journey's own acceptance text. Trigger 3 (prior
ESCALATE) does not apply (iter-19's verdict was `CONTINUE`); the hardening-cadence trigger also does not fire
(0 consecutive lean iterations — iter-19 was full, resetting the counter) — trigger 1 alone is sufficient and
matches the iter-19 evaluator's own explicit next-step framing ("frontend + serving-path change → UI chain
warranted, hence full").

**Lessons applied (surfaced per agent instructions, not repeated mistakes):**
- **iter-19** (this exact page, the lesson that found this iteration's target): "a same-symptom latency/UX
  gap can hide in a DIFFERENT subsystem than the one you instrumented and fixed... verify the OTHER
  first-touch paths with a live browser walk, not just the instrumented phase." This iteration IS that
  verification's result; TC-12 below repeats the discipline once more after this fix lands, so a THIRD hiding
  subsystem (if any) would still be caught rather than assumed away.
- **iter-18**: "a load test that omits the ingest overlay will falsely read 'budget holds'." TC-3/TC-12 below
  are pure-request-concurrency tests, not an ingest-overlay test — TC-13 (contingent, operator-gated) is what
  actually proves the ≤1.5 s budget under a concurrent ingest; this spec does not claim TC-3 alone proves
  that.
- **iter-16** (two lessons, both directly applicable): "enumerate the ways the *identity* can move, not just
  the ways the *value* can go stale" — the new outer dispatch guard is keyed on the SAME `(asof_key,
  dataset_version)` identity the resolver already uses, not a new axis. And: "status-disclosure copy is a
  testable assertion about system state, not styling... verify each sentence against the code that would have
  to be true for it" — directly why TC-8/TC-9 require the `RefreshingEvidenceBanner`/`EmptyState` copy to be
  re-checked against the NEW trigger, not assumed still accurate.
- **iter-14**: "a memory fix and a lock-contention fix are different problems... measure latency under
  concurrent load on the deep basis, not just peak memory" — TC-12's browser walk and TC-13's operator
  measurement are what actually prove the fix, not the unit tests alone.
- **iter-11**: any latency claim must first confirm no concurrent ingest is contaminating the measurement
  (`logs/backend.log` check) — binding on whoever runs TC-3/TC-12/TC-13's protocols.

**Two carried, owner-gated items — handled honestly, not silently dropped (pump note items 5a/5b):**
1. **TC-13 (concurrent-ingest-overlay `/backtest` re-measurement)** — owed since iter-17/18/19, blocked by
   this session's AG-10 ingest-trigger safety classifier. OPERATOR-performed, explicitly CONTINGENT on owner
   go-ahead — not assumed runnable autonomously, and not this iteration's blocker.
2. **TC-14 (disruptive J-04 kill/restart checkpoint-survival replay)** — owed since iter-15, same ingest-
   trigger gate. OPERATOR-performed, explicitly CONTINGENT on owner go-ahead — a hard GOAL_ACHIEVED
   precondition per every evaluator since iter-15, not this iteration's blocker.

**Live-service snapshot at spec-writing time** (read-only introspection only — `curl`/`ps`/`/proc`/`taskset`
reads; no service was started, stopped, or restarted by this decomposer pass): main backend `:8255` up (pid
3143437), `/proc`-verified caps intact (`Max address space` 6,442,450,944 bytes = 6144 MB, `MALLOC_ARENA_MAX
=2`, `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=4`, affinity `0-3,8-11`); frontend `:3255` answers HTTP 200;
`logs/backend.log`'s recent tail shows only clean `200 OK` health polls, no crash banner; `hwmon` sampler
(pid 29286) live, host at 44–50 °C (cool). Chrome MCP's devtools port (`9224`) still does NOT respond
(connection refused) — the wedge carried since iter-18 is unchanged; TC-12 has a documented operator-curl
fallback if it persists through execution.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/engine/forward_testing.py`: add a request-triggered, single-flight-guarded
  ASYNCHRONOUS dispatch for a historical (`is_latest == False`) `asof_key` whose forward-aggregate evidence
  is not `"ready"` for the current `dataset_version` — a background thread with its OWN DB session (mirrors
  the established `data_manager.start_data_job` / `warmup.start_warmup` thread-plus-own-session idiom), single-
  flight-guarded so AT MOST ONE background compute is ever in flight per `(asof_key, dataset_version)` (an
  outer guard around the existing per-horizon single-flight lock in `forward_aggregates_ingest_cached`, which
  itself stays unchanged). A dispatch-owner thread that raises must release the outer guard (mirrors the
  existing waiter-does-not-deadlock discipline) so a later request can re-dispatch.
- [ ] `apps/backend/app/api/backtest.py`: the historical branch of `GET /api/backtest` stops synchronously
  computing/waiting — it triggers the dispatch above (only if one is not already in flight or already
  satisfied) and returns immediately with whatever `resolved_forward_aggregate_evidence` already found;
  rename/repurpose the `ensure_loop_ms` timing field to reflect a dispatch-decision cost (sub-millisecond),
  never a compute-wait duration.
- [ ] `apps/backend/app/mcp/tools.py`: mirror the identical change in `query_backtest` (same dispatch
  mechanism; the existing `test_backtest_route_and_mcp_tool_serve_evidence_asof_identically`-style parity
  must keep holding).
- [ ] Update `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` (TC-13, iter-16/17) and
  `test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists` (iter-17 regression
  guard) in `apps/backend/tests/test_forward_testing_serving_split.py` to assert the NEW contract (see
  TESTING REQUIREMENTS) — keep, never weaken, their "exactly `len(HORIZONS)` real computes, never more on a
  repeat view" and byte-identity assertions.
- [ ] Update `test_backtest_evidence_is_as_of_scoped_expanding_window` in `apps/backend/tests/
  test_api_backtest.py` so its as-of no-lookahead/expanding-window proof waits for the dispatched background
  compute to complete rather than depending on same-request synchronous completion.
- [ ] Add a new concurrency test (in or alongside `apps/backend/tests/test_forward_testing_concurrency.py`,
  following its existing naming convention) proving the dispatch-once guarantee and non-blocking response
  under N concurrent first-touch requests for the same never-before-warmed historical date (TC-3), plus a
  dispatch-owner-failure recovery test (TC-7).

### Frontend

- [ ] `apps/frontend/app/backtest/page.tsx`: audit `RefreshingEvidenceBanner`'s and the `not_yet_computed`
  `EmptyState`'s copy against the NEW trigger (a historical view's own background dispatch — distinct from a
  latest-view version-bump or a true fresh-install) — correct any sentence that is untrue for this cause
  (e.g. an unconditional "the dataset has changed... reload after the next ingest finishes" claim, or an
  empty-state claim that only "backfilling or fetching data" — not viewing the page — starts a compute). No
  new component, no new fetch, no new field; reuses the existing three-state `evidence_status` contract as-is.

### New user-facing capability

None new. Historical as-of viewing on `/backtest` already existed (J-14/17/18); this iteration removes its
up-to-54 s blocking stall so that existing capability is honestly responsive for the first time, matching the
same interim-state UX already shipped for the latest-view version-bump case.

### New information displayed

None — reuses the existing `evidence_status: "ready"|"refreshing"|"not_yet_computed"` /
`evidence_generated_at` / `evidence_asof` / `evidence_by_horizon` fields exactly as already displayed.

### New user actions

None.

### UI surface changes

None new. `RefreshingEvidenceBanner` / the `not_yet_computed` `EmptyState` (both pre-existing, iter-16/17)
may have corrected copy; no new panel, page, or control.

### Product surface delta

A first-ever view of a not-yet-warmed historical `/backtest` date now renders within budget showing an
honest interim state (the resolver's existing fallback or empty state) instead of a blank, frozen skeleton
for up to 54 seconds; a later reload shows that date's own real evidence once the background compute
completes. The LATEST (default) view is unaffected — it never reached this code path before or after.

### Blueprint conformance

No new surfaces. This iteration's work lives entirely inside the existing `/backtest` + MCP `query_backtest`
home already registered in `blueprint.md`'s Information Architecture table for J-06/J-07/J-08. `blueprint.md`
has been updated this iteration: a new "iter-20 update" narrative paragraph is appended to the comment block,
and the "Regime score, market phase, realized forward-returns" Data-Contract row's Notes cell gains a short
appended sentence pointing to it. No nav-skeleton change — `blueprint.reapproval-requested` was NOT written.

### Data-contract additions

None. `evidence_status` / `evidence_generated_at` / `evidence_asof` / `evidence_by_horizon` keep their exact
existing shape, same computing module (`app.engine.forward_testing`), same two serving endpoints
(`GET /api/backtest`, MCP `query_backtest`). This iteration changes ONLY the internal trigger-timing
mechanism (which thread computes, and when) for the historical branch — no new displayed value, no second
producer, no second endpoint.

## OUT OF SCOPE

- `compute_forward_aggregates`'s body, signature, columns read, and streamed/`yield_per` pattern — untouched
  (byte-identical since iter-14; binding, `iteration-state.md` "Do not redo").
- `resolved_forward_aggregate_evidence`'s cross-`asof_key`/version fallback logic and the completeness/cutover
  pruning contract (iter-16/17) — untouched; this iteration changes WHO/WHEN triggers a compute for the
  historical branch, never the resolver's own read logic (binding, "Do not redo").
- `backfill_run_forward_returns` and its iter-19 zero-write guard — untouched, not reopened.
- The LATEST (`is_latest == True`) view/branch — unaffected; it never reached the ensure-loop before this
  iteration and does not reach the new dispatch path either.
- **Precomputing every historical `ScannerRun.asof_date`'s forward aggregates at ingest** — explicitly
  rejected as unbounded/ever-growing ingest cost (see BACKGROUND); not the direction this iteration takes.
- **Removing the historical create-once-and-cache capability entirely** — explicitly rejected as a real
  time-machine capability regression no journey step asks for (see BACKGROUND).
- TC-13 (concurrent-ingest-overlay re-measurement) and TC-14 (disruptive J-04 kill/restart replay) —
  OPERATOR/owner-gated (AG-10 ingest-trigger classifier), carried since iter-17/18/19 and iter-15
  respectively; this iteration's agent work does not depend on either landing.
- The four sibling ingest-time lazy caches (event-study, market-phase, drawdown-expectations, index-series)
  and their own lazy-compute paths — no evidence this iteration that any of them exhibits the same
  synchronous-block symptom; if a future browser walk finds one that does, treat it as its OWN targeted
  iteration rather than preemptively extending this fix there without evidence (mirrors the iter-19 lesson's
  own discipline — verify before generalizing).
- `scanner.resolve_run`'s pre-existing "cold arbitrary as-of snapshot" create-once carve-out (the ScannerRun
  itself, not its forward-aggregate evidence) — a distinct, already-sanctioned mechanism (goal.md's own
  Improvement-direction carve-out); UT-04's own timing breakdown shows `resolved_run_ms` staying small on the
  same slow requests that showed large `ensure_loop_ms`, so it is not implicated by this iteration's
  diagnosis. Untouched.
- The frontend's fetch-scheduling/staggering fix (iter-6, Dashboard/Data-Manager on-load calls) — unrelated,
  untouched.
- `main.py`'s boot sequence, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`,
  `scripts/*`, `scripts/automation/*` — untouched (binding, "Do not redo").
- The full pytest suite — targeted, host-guard-confined runs only (`taskset -c 0-3,8-11`, BLAS/OMP=4). The
  `loaded_engine`-dependent `test_api_backtest.py` fixture (~80-minute) — cite it, do not run it wholesale
  (binding, "Do not redo").
- The `demo.sh ops-hardening --session-live` walkthrough — settled non-autonomous deliverable (iter-12
  finding); not part of this iteration's DoD.
- Fixing the Chrome MCP port-9224 infra wedge itself — an environment/framework issue outside this
  iteration's product scope; TC-12 has a documented operator-curl fallback.
- A generic, all-endpoint async-job framework or task-queue rollout — scoped strictly to this ONE historical
  ensure-loop's dispatch, reusing the existing thread-plus-own-session idiom already in this codebase, not a
  new framework-wide abstraction.

## DEFINITION OF DONE

- [ ] A first-ever view of a not-yet-warmed historical `/backtest` as-of never blocks past the committed
  ≤1.5 s budget and never renders a blank/frozen skeleton (TC-1, TC-3, TC-12)
- [ ] Exactly one background compute is ever dispatched per `(asof_key, dataset_version)` — never zero, never
  duplicated under concurrency (TC-1, TC-3)
- [ ] Once the dispatched background compute completes, the exact requested date serves `"ready"`,
  byte-identical to a direct `compute_forward_aggregates` call, for every configured horizon (TC-4)
- [ ] `GET /api/health` stays within its existing ≤0.1 s budget throughout a dispatched historical background
  warm — no frozen or unresponsive window (TC-5)
- [ ] MCP `query_backtest` behaves identically to the HTTP endpoint for the same never-before-warmed
  historical date (TC-6)
- [ ] A dispatch-owner failure never permanently wedges the outer guard — a subsequent request can re-dispatch
  and eventually reach `"ready"` (TC-7)
- [ ] `RefreshingEvidenceBanner` and the `not_yet_computed` `EmptyState` copy are verified true (and corrected
  if not) under the historical-view-dispatch trigger, not only the pre-existing triggers (TC-8, TC-9)
- [ ] `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` and its iter-17 sibling are
  updated to the new contract without weakening their compute-count/byte-identity assertions (TC-10)
- [ ] `test_backtest_evidence_is_as_of_scoped_expanding_window`'s no-lookahead/expanding-window proof still
  holds under the new dispatch model (TC-11, AG-5)
- [ ] Target journeys J-06, J-07, J-08 are evaluated by the goal-evaluator against the browser + unit evidence
  this iteration produces (this spec does not itself declare any journey passing) (TC-12)
- [ ] Operator-performed, owner-gated: the concurrent-ingest-overlay re-measurement (TC-13) and the disruptive
  J-04 kill/restart replay (TC-14) are attempted/documented honestly if authorized, or their blocked status is
  recorded plainly — neither silently dropped
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green via deterministic replay + LLM
  fallback (TC-15)
- [ ] No anti-goal violation introduced: AG-3 (TC-4), AG-5 (TC-11), AG-8 + coherence (TC-16 —
  `compute_forward_aggregates`/the resolver's fallback logic byte-unchanged, no second producer/resolver),
  AG-10 (TC-5/TC-13/TC-14 launcher-only via `scripts/start-backend.sh`, host-guard-confined)
- [ ] Unit tests pass; no regressions across `test_forward_testing_serving_split.py`,
  `test_forward_testing_concurrency.py`, `test_forward_testing.py`, `test_api_backtest.py`, and
  `test_data_manager.py` (the pre-existing, unrelated `test_db.py::test_create_all_produces_expected_tables`
  failure is carried, not new)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-20-dev.md`, stating explicitly how the
  outer dispatch guard is keyed and why it cannot duplicate work or wedge (per the live TC-1/TC-3/TC-7
  evidence)

## TESTING REQUIREMENTS

- Browser: target journeys J-06, J-07, J-08 via a first-ever view of a not-yet-warmed historical `/backtest`
  as-of (TC-12). Required-still-passing regression: deterministic golden replay for J-01/J-03/J-05 (TC-15);
  the LLM browser-qa lane for J-04 (no golden script exists for it, per the established session pattern — may
  SKIP again if Chrome MCP stays wedged, matching the iter-16/17/18/19 carried treatment; TC-14 is the
  disruptive substitute, owner-gated, not this iteration's blocker).
- Unit/integration: `apps/backend/tests/test_forward_testing_serving_split.py` (TC-1, TC-4, TC-6, TC-7,
  TC-10, TC-11) and `apps/backend/tests/test_forward_testing_concurrency.py` (TC-3, TC-7).
- Error cases: an invalid or not-yet-stored `as_of` date must continue to raise the existing explicit
  4xx/503 via `_STATUS_BY_KIND` — unchanged by this iteration, regression-covered by the pre-existing
  `test_api_backtest.py` / `test_forward_testing_serving_split.py` suites (no new TC needed for this
  already-covered, unchanged path). A dispatch-owner exception (TC-7) must surface as a log/handled condition,
  never an unhandled exception that crashes the request thread that triggered the dispatch.

Test-first contract: every DEFINITION OF DONE checkbox above maps to at least one of the following.

- TC-1: given a historical (`is_latest == False`) as-of date D with no `ForwardAggregateCache` row for D
  under the current `dataset_version` (a never-before-warmed date), when `GET /api/backtest?as_of=D` is
  requested, then the HTTP response returns status 200 within the committed ≤1.5 s budget, its
  `evidence_status` is `"refreshing"` or `"not_yet_computed"` per the resolver's pre-dispatch read (never
  blocking on D's own compute), and a background compute of D's forward-aggregate evidence for every
  configured horizon has been dispatched but the request thread does not wait for it.
- TC-2: given the same scenario as TC-1, when `apps.backend.app.api.backtest._log_backtest_timing`'s emitted
  log line is inspected, then its dispatch-decision field records a sub-millisecond cost, never a multi-second
  compute-wait duration.
- TC-3: given N=5 concurrent `GET /api/backtest?as_of=D` requests for the SAME never-before-warmed D, when all
  5 are issued together, then `compute_forward_aggregates` is invoked exactly `len(cfg.walk_forward.horizons)`
  times in total across all 5 requests (never `5 × len(horizons)`, never zero), and every one of the 5 HTTP
  responses completes within the committed ≤1.5 s budget.
- TC-4: given TC-1/TC-3's dispatched background compute for D has completed, when `GET /api/backtest?as_of=D`
  is requested again, then `evidence_status == "ready"`, `evidence_asof == D`, and `evidence_by_horizon[h]` is
  byte-identical to a direct `compute_forward_aggregates(session, h, cfg, as_of=D)` call for every configured
  horizon h.
- TC-5: given a historical D's background compute is in flight, when `GET /api/health` is polled once per
  second throughout, then every poll returns HTTP 200 within its existing ≤0.1 s committed budget (mirrors
  J-07 step 2 — no frozen or unresponsive window).
- TC-6: given the same never-before-warmed D scenario as TC-1, when MCP `query_backtest(session, asof=D)` is
  called instead of the HTTP endpoint, then it exhibits identical behavior (same `evidence_status` on the
  first call, same dispatch-once guarantee, no wait) — the two entry points stay behaviorally identical
  (mirrors the existing `test_backtest_route_and_mcp_tool_serve_evidence_asof_identically` pattern).
- TC-7: given the dispatched background compute's owning thread raises before completing (a forced failure,
  mirroring the existing `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`
  fixture), when a subsequent request for the SAME D arrives, then it is able to re-dispatch a fresh
  background compute (the outer guard is released, never permanently wedged) and D eventually reaches
  `"ready"` on a following view — never a stuck `"refreshing"`/`"not_yet_computed"` state.
- TC-8: given `evidence_status == "refreshing"` is rendered on `/backtest` for a historical D whose OWN
  evidence is warming in the background (not a latest-view version bump), when `RefreshingEvidenceBanner`'s
  rendered text is read, then it contains no claim that is untrue for this cause (no unconditional assertion
  that "the dataset has changed" or that reloading "after the next ingest finishes" is what surfaces the new
  value, when here no ingest is involved) — corrected if the current copy fails this check.
- TC-9: given a genuinely never-warmed store (no complete evidence exists at or before D for any as-of — the
  true fresh-install shape), when `GET /api/backtest?as_of=D` is requested, then `evidence_status ==
  "not_yet_computed"`, `evidence_by_horizon == {}`, HTTP 200 within budget, and the `EmptyState` copy makes no
  claim untrue under the new trigger (viewing the page itself now also starts a background compute, not only
  "backfilling or fetching data") — corrected if the current copy fails this check.
- TC-10: given `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` and
  `test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists` are updated for the new
  contract, when they run, then both still assert exactly `len(HORIZONS)` real `compute_forward_aggregates`
  calls total for D (never recomputed once cached) and byte-identical served evidence across repeated calls
  once `"ready"` — only the "ready on the very first synchronous call" assumption is removed.
- TC-11: given `test_backtest_evidence_is_as_of_scoped_expanding_window` is updated to wait for D's dispatched
  background compute to complete before asserting, when it runs, then `n_runs` at the oldest date equals 1,
  is strictly less than `n_runs` at the latest date, and every `asof_dates` entry is `<= D` (AG-5, no
  lookahead).
- TC-12: given a warm backend and a historical as-of date never viewed this browser session, when a user
  navigates to `/backtest?as_of=<date>` in the browser, then the page renders within the committed budget
  showing either the `RefreshingEvidenceBanner` or the "not yet computed" `EmptyState` — never a blank/frozen
  skeleton — and a reload after the background compute completes shows that date's own real per-horizon
  evidence; if Chrome MCP (port 9224) has not recovered by execution time, an operator-curl capture of
  `backtest_timing`'s `total_ms`/dispatch field is an acceptable documented fallback for the timing half of
  this claim (mirrors iter-19's TC-10 fallback), though the rendered-copy half (TC-8/TC-9) still needs a live
  browser render.
- TC-13 (OPERATOR-performed, AG-10-class, launcher-only via `scripts/start-backend.sh`, CONTINGENT on owner
  go-ahead for the ingest trigger — do not assume it can run autonomously; document the attempt and outcome
  regardless): given the deep-basis backend under concurrent `GET /api/backtest` polling WITH a concurrent
  ingest job also running (the overlay condition owed since iter-17/18/19), when the poll completes, then
  breach count and max latency are recorded in a new dated `reports/perf-budgets.md` section, directly
  comparable to the iter-16/17 baseline (11/68 breaches, max 12.655 s); if the ingest trigger remains blocked
  this session, the section records that plainly rather than silently omitting it.
- TC-14 (OPERATOR-performed, AG-10-class, CONTINGENT on owner go-ahead for the ingest trigger — owed since
  iter-15): given the owner authorizes a real backfill submitted then `kill -9`-ed mid-run, when the backend
  restarts, then the `/data` Run History panel shows the interrupted run's last-checkpointed progress (not
  all-zero creation-time defaults); if the trigger remains blocked, the non-disruptive `GET /api/health`
  sanity check (HTTP 200, `readiness: "ready"`, no new crash banner) is recorded as the carried substitute,
  exactly as iterations 16–19 have each done.
- TC-15: given the deterministic golden-replay scripts for J-01/J-03/J-05 and J-04's carried/LLM-fallback
  status, when the goal-evaluator's regression pass runs after this iteration's diff, then none transitions
  from passing to failing.
- TC-16: given the reviewer/auditor inspects `compute_forward_aggregates` and `resolved_forward_aggregate_
  evidence`'s cross-`asof_key`/version fallback logic after this iteration's diff, when compared against
  iter-19, then both are byte-unchanged (confirming no second producer or resolver was introduced — coherence
  contract).

## NOTES

- **`assumptions.md` entry logged this iteration.** The choice to preserve the historical carve-out's
  lazy-create-once SUBSTANCE while requiring the compute to run off-thread (rather than removing historical
  lazy compute entirely, or precomputing every historical date at ingest) is a genuine reading of ambiguous
  goal text against the iter-16 decomposer's own prior carve-out precedent — logged in full, not decided
  silently. The full-vs-lean depth call is a rubric application (justified above via trigger 1), not a fresh
  goal-text interpretation, so it gets no separate entry.
- **Why the outer dispatch guard, not just the existing per-horizon single-flight lock:** the existing lock
  in `forward_aggregates_ingest_cached` already prevents duplicate COMPUTES for the same key, but leaving the
  REQUEST thread to call it (even as a "waiter") is exactly the synchronous block this iteration removes —
  UT-04's ~54 s figures are consistent with a waiter's bounded 45 s wait plus a redundant independent compute
  on timeout under this concurrency shape (TC-8's documented rare fallback, evidently not rare here). The new
  outer guard's job is narrower: decide whether a background dispatch is already in flight for this identity
  BEFORE ever touching the per-horizon lock from the request thread — the request thread itself never calls
  `event.wait()` at all after this change.
- **Why not defer to a generic background-job framework:** this codebase already has an established,
  narrow idiom for "kick off work in a daemon thread with its own session and return immediately"
  (`data_manager.start_data_job`, `warmup.start_warmup`) — reusing it keeps this fix a small, in-module
  addition rather than a new cross-cutting abstraction (Simplicity First, `.claude/core.md`).
- Carried, unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing, no schema change
  this iteration).
- `blueprint.md` updated this iteration (new "iter-20 update" comment-block paragraph; a short Notes-cell
  append to the "Regime score, market phase, realized forward-returns" row pointing to it) — no nav-skeleton
  change, so `blueprint.reapproval-requested` was not written.
- If TC-13/TC-14 land this iteration (owner authorizes the ingest trigger), record them in the SAME
  `reports/perf-budgets.md` artifact used throughout this session — no second measurement file.
