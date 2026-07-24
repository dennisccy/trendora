# Goal Iteration 19 — Remove the create-once forward-returns write from `/backtest`'s serving path

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 19
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
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

`GET /api/backtest` and the MCP `query_backtest` tool stop paying a real SQLite write-lock cost on every
request for a run whose forward returns are already backfilled, closing the one shared latency blocker that
has held J-06/J-07/J-08 at `partial` since iter-11 — proven by a live re-measurement against the deep basis,
not merely a code-level argument.

## BACKGROUND

Iter-18's operator-supervised TC-9 re-measurement (966 requests, host-guard-confined via
`scripts/start-backend.sh`) **definitively pinned** the mechanism behind the un-remediated `/backtest`
≤1.5s budget breach (11/68 @ max 12.655s, iter-16/17 baseline): `backfill_run_forward_returns`
(`apps/backend/app/engine/forward_testing.py:1365`) — a create-once, INSERT-only write into the append-only
`forward_returns` table — is invoked **unconditionally on every request** by both `GET /api/backtest`
(`apps/backend/app/api/backtest.py:140`) and the MCP `query_backtest` tool
(`apps/backend/app/mcp/tools.py:263`). Under 6× concurrency that phase balloons from ~175 ms
single-threaded to **881 ms (p99 964, max 999)** — 82.2% of each slow request — while the pure-read
resolver `resolved_forward_aggregate_evidence` stays flat at 9.6 ms. This is a DIFFERENT table/function from
`compute_forward_aggregates`/`ForwardAggregateCache` (the iter-14/16/17 machinery, untouched, do not
conflate): `backfill_run_forward_returns` populates each run's own realized-return rows; the forward
*aggregates* J-08 already made request-path-compute-free are a separate value entirely.

The ingest finalize path already backfills every run's forward returns at creation time
(`apps/backend/app/engine/data_manager.py:2918`, inside `_persist`, unchanged by this iteration) — so for
any run created through standard ingest, the request-path call is pure redundant re-derivation. This
iteration's fix: add a guard **inside `backfill_run_forward_returns` itself** so a request for a run whose
forward returns are already complete performs zero write-lock-acquiring work; the rare genuinely-missing
case (a cold historical snapshot's first view) keeps inserting synchronously exactly as today, preserving
idempotency and the existing `_commit_forward_returns_concurrency_safe` `IntegrityError`-tolerant
concurrent-race handling unchanged. Because the guard lives in the one shared function, `backtest.py` and
`mcp/tools.py` need **no code change at all** — both already call this function unconditionally; only its
internal control flow changes. Two shapes were considered for *how* the guard decides "already complete":
(a) skip the commit when the existing idempotency check finds zero rows to insert (the function already
computes this — `inserted == 0` — so no new query is needed), or (b) a cheap pre-check ahead of today's
read+insert+commit block. **The developer picks whichever shape the TC-6 re-measurement below actually
proves collapses the phase, and states which one + why in the dev handoff** — this session's whole arc
(iter-14 through iter-18) has consistently required a live measurement to confirm a fix, never a
code-level argument alone (lesson applied, iter-15: "trust the LIVE number over the root-cause
extrapolation"). Deferring the rare genuinely-missing case to a background/async job was considered and
explicitly rejected (see OUT OF SCOPE) — it would change a first-view request's served numbers from real
values to a transient NA placeholder, breaking AG-3 byte-identity.

**Target-selection rubric applied:** rule 1 (regressed first) — N/A, nothing regressed. Rule 2
(consolidation before features) — N/A, iter-18's `coherence.md` was `COHERENCE-PASS`. Rule 3 (unblockers) —
this IS unblocker work: J-06/J-07/J-08 share exactly ONE root cause on ONE serving path, so one fix closes
all three labels rather than three separate changes. Rule 5 (never bundle two risky journeys) — this is ONE
moderate-to-high-risk change (a write-path guard on a cluster with a REGRESSION history, see below) carried
across three journey IDs, not two unrelated risky changes — the same shape iterations 14-18 have each used
for this cluster. Rule 6 (don't pick a human-blocked journey) — the iter-18 evaluator explicitly ruled this
agent-tractable ("apply the diagnosed fix — is agent-owned and well-specified, not human-owned"), which is
why iter-18 returned CONTINUE, not STALLED.

**Depth: full — trigger 1 (structural/cross-cutting) fires.** The fix changes the behavior of a function
called from ≥3 distinct call sites across 3 files/modules whose interactions are NOT covered by any single
journey's own tests: `apps/backend/app/engine/forward_testing.py` (the function itself),
`apps/backend/app/api/backtest.py` and `apps/backend/app/mcp/tools.py` (both request-path callers, whose
behavior changes even though neither file's own code needs editing), and
`apps/backend/app/engine/data_manager.py`'s ingest call site (unedited, but its behavior — and its
interaction with concurrent request-path callers — changes). None of J-06 (page-load budget), J-07
(availability-under-load), or J-08 (zero-aggregate-compute-on-request) individually tests "is the new
write-guard correct under concurrent race conditions" — that is exactly why a dedicated concurrency suite
(`test_forward_testing_concurrency.py`) already exists as its own thing, and exactly the surface iter-13's
REGRESSION (a ~12-minute futex deadlock under concurrent load on this same general cluster) came from.
Trigger 3 (prior ESCALATE) does not apply (iter-18's verdict was `CONTINUE`), but trigger 1 alone is
sufficient and matches the iter-18 evaluator's own explicit "Depth Recommendation For Next Iteration: full."

**Lessons applied (surfaced per agent instructions, not repeated mistakes):**
- **iter-18** (this exact cluster): "a 'read' endpoint can carry a lazy create-once WRITE that only
  contends under load... pure 6× concurrent reads did NOT reproduce the breach (0/966)... a load test that
  omits the ingest overlay will falsely read 'budget holds.'" This is why TC-6 (pure-read re-measurement)
  alone is NOT treated as sufficient proof the budget holds under the actual historical breach condition —
  TC-7 (ingest-overlay re-measurement) is the test that matters for that claim, contingent as it is on the
  ingest-trigger authorization below.
- **iter-15**: "trust the LIVE number over the root-cause extrapolation" — the fix is not credited until
  TC-6/TC-7 show it live on the deep basis, not merely that the code change looks correct.
- **iter-14**: "a memory fix and a lock-contention fix are different problems... measure latency under
  concurrent load on the deep basis, not just peak memory" — TC-6/TC-7 measure latency specifically, not a
  proxy for it.
- **iter-13**: an unresolved critical anti-goal (or, by extension, an under-tested concurrency fix) can
  regress in observed severity under a heavier load profile than previously tested — this is why TC-4
  requires a genuine concurrent-race test, not an assumption that the existing
  `_commit_forward_returns_concurrency_safe` safety net still behaves safely without being exercised.

**Two carried blockers, not silently dropped:**
1. The fresh live DISRUPTIVE J-04 kill/restart checkpoint-survival replay (owed since iter-15) needs a real
   backfill submitted then killed mid-run — this ingest trigger was BLOCKED last session by the automated
   AG-10 safety classifier, and the operator did not work around it. It remains OPERATOR-performed and
   explicitly CONTINGENT on owner go-ahead for the ingest trigger — not assumed runnable autonomously, and
   not this iteration's blocker (TC-8 below is the non-disruptive substitute, as in iter-16/17/18).
2. Chrome MCP (port 9224) is confirmed still unreachable this iteration (read-only check at spec-writing
   time: `curl` to `/json/version` — connection refused). The deterministic golden-replay lane does
   not depend on Chrome MCP and is unaffected. TC-10 below has a documented operator-curl fallback if the wedge persists
   through execution.

## IN SCOPE

### Backend

- [ ] Add a guard inside `backfill_run_forward_returns` (`apps/backend/app/engine/forward_testing.py:1365`)
  so that when a run's forward returns are already fully backfilled, the call performs no SQLite
  write-lock-acquiring operation (no `INSERT`, no non-trivial `commit()`) — proven by SQL-inspection
  (`before_cursor_execute`), not by inference. The genuinely-missing case (this run has never been
  backfilled) keeps inserting synchronously and committing exactly as today — idempotent, INSERT-only,
  race-tolerant via the existing `_commit_forward_returns_concurrency_safe`.
- [ ] Do NOT touch the call sites themselves — `apps/backend/app/api/backtest.py:140` and
  `apps/backend/app/mcp/tools.py:263` keep calling `backfill_run_forward_returns(session, run, cfg)`
  exactly as today; only the function's own internals change. `data_manager.py:2918`'s ingest call site is
  also left unedited (it automatically benefits/is exercised by the same guard).
- [ ] Extend the existing `backtest_timing` / `query_backtest_timing` log lines
  (`apps/backend/app/api/backtest.py`, `apps/backend/app/mcp/tools.py`, landed iter-18) with one additional
  boolean-ish field recording whether the create-once write was skipped or taken on that request — cheap,
  non-blocking, directly supports TC-6/TC-7's evidence-gathering (operational log only, not a served value).
- [ ] Add/extend unit tests in `apps/backend/tests/test_forward_testing_serving_split.py` and
  `apps/backend/tests/test_forward_testing_concurrency.py` (TC-1 through TC-5 below).

### Frontend

None this iteration — backend-only fix. The served payload stays byte-identical (TC-5); no new or altered
UI surface, no new field for any existing component to render.

### New user-facing capability

None directly new. The existing `/backtest` page (and any consumer of `GET /api/backtest` / MCP
`query_backtest`) stops exhibiting the multi-second slowdown under concurrent load and during an ingest
window (TC-6/TC-7), closing the last blocking clause shared by J-06/J-07/J-08.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

`/backtest` continues to show identical evidence and scorecard values (TC-5); the only observable change is
the elimination of the multi-second slowdown a user could previously hit loading `/backtest` under
concurrent load near a heavy ingest.

### Blueprint conformance

No new surfaces. This iteration's work lives entirely inside the existing `/backtest` + MCP `query_backtest`
home already registered in `blueprint.md`'s Information Architecture table for J-06/J-07/J-08.
`blueprint.md` has been updated this iteration: a new "iter-19 update" narrative paragraph is appended to
the comment block, and the "Regime score, market phase, realized forward-returns" Data-Contract row's Notes
cell gains an appended sentence pointing to it. No nav-skeleton change — `blueprint.reapproval-requested`
was NOT written.

### Data-contract additions

None. `evidence_status` / `evidence_generated_at` / `evidence_asof` / `evidence_by_horizon` / the scorecard
fields are unchanged in shape and, per TC-5, byte-identical in value to their pre-iteration behavior. This
iteration is a request-path write-elimination inside an existing function, not a new computed or displayed
value — nothing new to register.

## OUT OF SCOPE

- `compute_forward_aggregates`'s body, the compute-vs-serve split, and the completeness-gated cutover
  pruning logic (`forward_testing.py` ~lines 1023-1354) — untouched; this fix targets a DIFFERENT
  function/table (`backfill_run_forward_returns` / the `forward_returns` table), never the forward-AGGREGATE
  machinery (binding, `iteration-state.md` "Do not redo").
- The resolver's cross-`asof_key` fallback and the `evidence_asof`/`evidence_status`/`evidence_generated_at`
  fields (iter-16/17, evaluator-confirmed) — untouched, not reopened.
- **Deferring the genuinely-missing forward-returns backfill to a background/async job** — explicitly OUT
  OF SCOPE even though the diagnosis's own framing floated it as "ideal": it would change a first-view
  request's served numbers from real values to a transient NA/placeholder state, breaking AG-3
  byte-identity. Keep the rare synchronous fallback exactly as it behaves today.
- **Any new persisted schema/column** (e.g., a `forward_returns_backfilled` flag on `ScannerRun`) — not the
  default plan. Only introduce one if the query-only guard proves insufficient under TC-6's live
  re-measurement, and if so, flag it explicitly in the dev handoff as a data-model change (its own
  migration) rather than silently adding a column.
- A fresh live DISRUPTIVE J-04 kill/restart replay — operator/owner-gated (ingest-trigger classifier),
  carried since iter-15; this iteration performs only the non-disruptive carry-forward check (TC-8).
- `main.py`'s boot sequence, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`,
  `scripts/*`, `scripts/automation/*` — untouched (binding, "Do not redo").
- The full pytest suite — targeted, host-guard-confined runs only (`taskset -c 0-3,8-11`, BLAS/OMP=4). The
  `loaded_engine`-dependent `test_api_backtest.py` fixture (~80-minute) — cite it, do not run it (binding,
  "Do not redo").
- J-06's other 10 idle-host page budgets and the ≤5s boot budget — settled iter-9/11/13; not re-measured
  (binding, "Do not redo").
- The `demo.sh ops-hardening --session-live` walkthrough — settled non-autonomous deliverable (iter-12
  finding); not part of this iteration's DoD.
- Fixing the Chrome MCP port-9224 infra wedge itself — an environment/framework issue outside this
  iteration's product scope; TC-10 has a documented operator-curl fallback.
- A generic, all-endpoint request-timing middleware or APM rollout — scoped strictly to extending the
  existing per-request timing log this cluster already has (iter-18), not a framework-wide change.

## DEFINITION OF DONE

- [ ] The request-path zero-write guard is verified for both callers via SQL-inspection, not inference
  (TC-1, TC-2)
- [ ] The genuinely-missing case still backfills synchronously and idempotently, exactly as before this
  iteration (TC-3)
- [ ] Concurrent-request race safety is preserved — no duplicate rows, no unhandled exception, the existing
  `IntegrityError`-tolerant rollback path is actually exercised by a test, not merely reachable in theory
  (TC-4)
- [ ] Served payload is byte-identical before/after the change, all configured horizons, with and without
  `as_of` (TC-5, AG-3)
- [ ] Operator pure-concurrency re-measurement (mirrors iter-18's TC-9 exactly) shows the
  `backfill_forward_returns_ms` phase collapsing: mean ≤ 350 ms and max ≤ 400 ms (down from iter-18's
  recorded 881 ms mean / 999 ms max), recorded in a new dated `reports/perf-budgets.md` section (TC-6)
- [ ] Operator ingest-overlay re-measurement is attempted; if the owner authorizes the ingest trigger this
  session, it records breach count and max latency directly comparable to the iter-16/17 baseline (11/68 @
  max 12.655s); if the trigger stays blocked, the attempt and the reason are documented plainly, not
  silently dropped (TC-7)
- [ ] J-04's non-disruptive carry-forward sanity check passes; the owed disruptive kill/restart replay stays
  explicitly flagged as owner-gated, not this iteration's blocker (TC-8)
- [ ] Required-still-passing J-01/J-03/J-05 golden replay stays green (TC-9)
- [ ] A live single-request `/backtest` capture against the real deep-basis backend corroborates TC-5's
  byte-identity outside the unit-test fixture (TC-10)
- [ ] Target journeys J-06, J-07, J-08 are evaluated by the goal-evaluator against the evidence this
  iteration produces (this spec does not itself declare any journey passing)
- [ ] No anti-goal violation introduced: AG-3 (TC-5, TC-10), AG-5 (fallback/filter logic untouched, not
  reopened), AG-8 (all reads stay bounded to one run's own scope — no new unbounded scan), AG-10 (TC-6/TC-7
  launcher-only via `scripts/start-backend.sh`, host-guard-confined, cooled host, sampler + watchdog armed)
- [ ] All pre-existing tests in `test_forward_testing_serving_split.py`, `test_forward_testing_concurrency.py`,
  `test_forward_testing.py`, `test_api_backtest.py`, and `test_data_manager.py` keep passing alongside the
  new tests; no regressions (the pre-existing, unrelated `test_db.py::test_create_all_produces_expected_tables`
  failure is carried, not new)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-19-dev.md`, stating explicitly which
  guard shape (skip-commit-when-zero vs. a pre-check) was chosen and why, per the live TC-6 evidence

## TESTING REQUIREMENTS

- Browser: no NEW browser verification is required for J-06/J-07/J-08 this iteration (`Frontend Present:
  no`) — the served payload is byte-identical (TC-5) and the primary fix evidence is an operator-supervised
  load measurement (TC-6/TC-7), not a rendering check. Required-still-passing regression: deterministic
  golden replay for J-01/J-03/J-05 (TC-9); the LLM browser-qa lane for J-04 (no golden script exists for
  it, per the established session pattern — may SKIP again if Chrome MCP stays wedged, matching the
  iter-16/17/18 carried treatment; TC-8 is the non-disruptive substitute regardless).
- Unit/integration: `apps/backend/tests/test_forward_testing_serving_split.py` (TC-1, TC-2, TC-3, TC-5) and
  `apps/backend/tests/test_forward_testing_concurrency.py` (TC-4).
- Error cases: an invalid or not-yet-stored `as_of` date must continue to raise the existing explicit
  4xx/503 via `_STATUS_BY_KIND` — unchanged by this iteration, regression-covered by the pre-existing
  `test_api_backtest.py` / `test_forward_testing_serving_split.py` suites (no new TC needed for this
  already-covered, unchanged path).

Test-first contract: every DEFINITION OF DONE checkbox above maps to at least one of the following.

- TC-1: given a `ScannerRun` whose `forward_returns` are already fully backfilled for every configured
  horizon and symbol (idempotency check finds nothing missing), when `GET /api/backtest` is called for that
  run's as-of, then SQL-inspection (the same `before_cursor_execute` technique
  `test_forward_testing_serving_split.py` already uses elsewhere) shows zero `INSERT`/`UPDATE`/`DELETE`
  statements issued during that request, and the response is HTTP 200.
- TC-2: given the same fixture as TC-1, when `app.mcp.tools.query_backtest(session, asof=...)` is called
  directly for the same as-of, then it also issues zero write statements, and its returned scorecard +
  `evidence_by_horizon`/`evidence_status`/`evidence_generated_at`/`evidence_asof` fields are identical to
  `GET /api/backtest`'s response for the same inputs.
- TC-3: given a `ScannerRun` whose forward returns have never been backfilled (mirrors the existing
  create-once test fixture), when `GET /api/backtest` is called for that as-of, then the endpoint still
  INSERTs the missing `ForwardReturn` rows exactly as before this iteration (idempotent, INSERT-only, the
  inserted row count matches `forward_symbols_for_run(...)` × configured horizons minus any NA gaps), and a
  SECOND call for the same as-of issues zero further write statements.
- TC-4: given 5 concurrent calls to `GET /api/backtest` for the SAME as-of whose forward returns are
  genuinely missing at request time (new test, co-located in `test_forward_testing_concurrency.py`
  alongside the existing forward-aggregate concurrency tests, but a distinct fixture/mechanism), when all 5
  complete, then none raises an unhandled exception, the `forward_returns` table contains no duplicate
  `(run_id, symbol, horizon)` key, and the pre-existing `_commit_forward_returns_concurrency_safe`
  `IntegrityError`-tolerant rollback path is demonstrably exercised by at least one of the 5 calls (proven
  by assertion, not merely reachable in theory).
- TC-5: given the TC-1 fixture (already-complete forward returns), when `compute_run_scorecard`'s returned
  dict plus `evidence_status`/`evidence_generated_at`/`evidence_asof`/`evidence_by_horizon` are captured
  before and after this iteration's change, then every field is byte-for-byte identical for every configured
  horizon, both with and without an explicit `as_of` query parameter.
- TC-6 (OPERATOR-performed, AG-10-class, launcher-only via `scripts/start-backend.sh`, host-guard-confined —
  cooled host, 1 Hz `hwmon` sampler live, thermal watchdog armed, `taskset -c 0-3,8-11`,
  `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=4`, mirrors iter-18's TC-9 protocol exactly): given the deep-basis
  backend under 6 concurrent `GET /api/backtest` pollers sustained for the same duration as iter-18's TC-9
  (pure reads, no concurrent ingest), when the per-request `backtest_timing` log is read after the run,
  then `backfill_forward_returns_ms`'s mean is ≤ 350 ms and its max is ≤ 400 ms (down from iter-18's
  recorded 881 ms mean / 999 ms max), recorded in a new dated `reports/perf-budgets.md` section directly
  comparable to iter-18's TC-9.
- TC-7 (OPERATOR-performed, AG-10-class, CONTINGENT on owner go-ahead for the ingest trigger — do not assume
  it can run autonomously; document the attempt and outcome regardless): given the same protocol as TC-6
  but with a concurrent ingest job also running (the overlay iter-18 deliberately did not trigger,
  reproducing the exact condition behind the iter-16/17 baseline breach), when the poll completes, then
  breach count and max latency are recorded in the same dated `reports/perf-budgets.md` section, directly
  comparable to the iter-16/17 baseline (11/68 breaches, max 12.655s); if the ingest trigger remains blocked
  this session, the section records that plainly (mirrors iter-18's TC-10 honest-gap treatment) rather than
  silently omitting it.
- TC-8: given the backend already running (non-disruptive, no kill/restart), when `GET /api/health` is
  polled once, then it returns HTTP 200 with `readiness: "ready"`, and `logs/backend.log` shows no new
  crash/restart banner since the last recorded one.
- TC-9: given the deterministic golden-replay scripts for J-01/J-03/J-05, when this iteration's regression
  check runs, then all three report a PASS verdict (replay exit 0), with no new failure attributable to
  this iteration's diff.
- TC-10 (OPERATOR-performed): given the same running deep-basis backend TC-6/TC-7 target, when a single live
  `GET /api/backtest` request is captured both before and after the fix lands, then the
  `evidence_by_horizon`/`evidence_status`/scorecard fields are diffed and confirmed identical (corroborating
  TC-5 against the real deep-basis process, not only a unit-test fixture); if Chrome MCP (port 9224) has
  recovered by execution time, an additional live browser screenshot of `/backtest` is a bonus, non-blocking
  confirmation — not required, since the wedge (confirmed unreachable at spec-writing time) is a carried,
  documented infra issue outside this iteration's control.

## NOTES

- **Current live-service snapshot at spec-writing time** (read-only introspection only — `curl`/`ss`/`/proc`
  reads; no service was started, stopped, or restarted by this decomposer pass): the main backend (`:8255`,
  pid 2388404 — the SAME process iter-18's TC-9 measured) is still running, `/proc`-verified caps intact
  (affinity `0-3,8-11`, `Max address space` 6,442,450,944 bytes = 6144 MB, `MALLOC_ARENA_MAX=2`,
  `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=4`); the frontend (`:3255`) answers HTTP 200; the `hwmon` sampler
  (pid 29286) is still live, host at 47 °C. Chrome MCP's devtools port (`9224`) does NOT respond
  (connection refused) — the wedge from iter-18's dispatch note is still present; see TC-10's fallback.
- **Why the fix needs no edit to `backtest.py` or `mcp/tools.py`:** both already call
  `backfill_run_forward_returns(session, run, cfg)` unconditionally and identically (confirmed by direct
  read of both call sites) — putting the guard inside the one shared function means both callers, and the
  ingest call site, get the corrected behavior automatically, with no duplicated guard logic anywhere
  (single-producer discipline).
- **Why TC-6 alone does not prove the budget holds:** iter-18's own TC-9 already showed pure 6× concurrent
  reads staying within budget (0/966, max 1.271s) even WITH the unguarded 881 ms phase present — the total
  request time had enough slack to absorb it. The historical 11/68 @ max 12.655s breach only manifested
  when a concurrent INGEST was ALSO holding the writer lock. TC-6 proves the MECHANISM improved (the phase
  itself collapses); TC-7 is what proves the BUDGET holds under the actual historical breach condition. If
  TC-7 cannot run (classifier block), the evaluator should weigh TC-1 through TC-6 as mechanism-level
  evidence and judge sufficiency explicitly, per this session's established precedent for contingent
  operator-gated evidence (iter-14's TC-6 partial-evidence call, iter-16/17/18's J-04 carry-forward calls) —
  this decomposer does not pre-judge that sufficiency call.
- **No new `assumptions.md` entry this iteration.** The guard-shape choice (skip-commit-when-zero vs. a
  pre-check) is an engineering decision explicitly handed to "the decomposer/developer" by the prior
  iteration's own diagnosis, not a fresh interpretation of ambiguous goal text. The full-vs-lean depth call
  is a rubric application (justified above via trigger 1), not a goal-text interpretation. The
  TC-7-contingent-on-owner-go-ahead framing directly continues iter-18's own established handling of the
  identical ingest-trigger constraint (TC-10 there) — not a new ambiguity being resolved here.
- Carried, unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing, no schema change
  this iteration).
- `blueprint.md` updated this iteration (new iter-19 comment-block paragraph; a Notes-cell append to the
  "Regime score, market phase, realized forward-returns" row) — no nav-skeleton change, so
  `blueprint.reapproval-requested` was not written.
