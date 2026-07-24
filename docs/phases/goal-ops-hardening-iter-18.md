# Goal Iteration 18 — `/backtest` latency-diagnosis instrumentation + two cheap wins

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 18
- **Mode:** next
- **Depth:** lean
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

Replace guesswork with real per-request timing evidence for `/backtest`'s undiagnosed ≤1.5s serving-budget
breaches, plus land two low-risk cheap wins the iter-17 audit already flagged, so the next iteration's
fix-or-owner-fork decision for J-06/J-07/J-08 rests on measurement rather than elimination-by-narrowing.

## BACKGROUND

**Re-derivation note:** an earlier decomposer pass already wrote a complete iter-18 spec at this same path,
but the engine aborted immediately after decomposition (an operator dispatch-protocol error, unrelated to
scope) — no dev/review/audit ran against it. This spec is re-derived from current codebase + artifact state,
not copied forward; `blueprint.md`'s stale "already added"-phrased iter-18 paragraph and Data-Contract tail
sentence have been corrected to "targeted, not yet built" to match.

Iter-17 closed the B1 cross-`asof_key` fallback (evaluator-confirmed: 15 unit tests, AG-5 strictly-older SQL-verified,
AG-3 byte-identical, live TC-07/TC-09 captures, COHERENCE-PASS) but J-06/J-07/J-08 all stay `partial` on ONE
shared blocker: 11/68 `/backtest` reads breach the committed ≤1.5s budget (max 12.655s) inside the ingest
window, narrowed to "SQLite-writer vs. GIL/threadpool contention" but not pinned — because `logs/backend.log`
carries zero per-request timestamps. Reconfirmed by direct read this iteration: `grep -cE
'^[0-9]{4}-[0-9]{2}-[0-9]{2}' logs/backend.log` → 0; every `/api/backtest` line is uvicorn's bare default
access line (`INFO: <client> - "GET /api/backtest HTTP/1.1" 200 OK`), no timing field at all — and no
request-timing middleware exists anywhere in `apps/backend/main.py` or the two serving modules (confirmed by
direct grep: zero `logger`/`logging` calls in `app/api/backtest.py` or `app/mcp/tools.py` today).

**Target-selection rubric applied:** rule 1 (regressed first) — N/A, nothing regressed (0 regressed per
`iteration-state.md`). Rule 2 (consolidation before features) — N/A, iter-17's `coherence.md` was
`COHERENCE-PASS`, not FAIL, so no consolidation mandate. Rule 3 (unblockers next) — this IS unblocker work:
J-06/J-07/J-08 are gated by exactly ONE shared root cause on ONE shared serving path
(`resolved_forward_aggregate_evidence` + its two callers), so one instrumentation pass serves all three
labels rather than being three separate changes; rule 5's "never bundle two risky journeys" does not apply
here — this is one moderate-risk change addressing a shared blocker, the same shape iterations 14-17 all
used for this exact journey cluster. Rule 6 (don't pick a human-blocked journey) — the iter-17 evaluator
explicitly ruled this agent-tractable ("the next step — add timing instrumentation, then diagnose — is
agent-owned, so not every unblock path is human-owned"), which is why iter-17 returned CONTINUE, not
STALLED.

**Depth: lean — no full trigger holds.** (1) Structural/cross-cutting: NO — the change touches three files
(`api/backtest.py`, `mcp/tools.py`, `forward_testing.py`) but all three are the SAME already-heavily-tested
J-06/J-07/J-08 serving surface (15 existing tests in `test_forward_testing_serving_split.py` alone already
exercise this exact resolver + both endpoints); the work itself is additive logging plus a query
column-selection reorder behind a byte-identity regression test, not a shared-architecture refactor. (2) Data
model: NO — no persisted schema change, and the Data-Contract value's computing module
(`app.engine.forward_testing`) and both serving endpoints are UNCHANGED; only internal query-column
selection and log output change (a log line is not a Data-Contract value). (3) Prior ESCALATE: NO — iter-17's
verdict was `CONTINUE`. The evaluator's own "Depth Recommendation For Next Iteration: full" is advisory, not
one of this rubric's four binding triggers — only a prior verdict of literal `ESCALATE` forces full, and
this session has not had one since iter-11. (4) Hardening cadence: NOT MET — "Consecutive lean iterations
dispatched: 0" (iter-17 ran full, which resets the counter); the threshold is 4. This also matches goal.md's
own Loop mechanics note ("full when an iteration first lands user-visible UI changes") — this iteration lands
none (`Frontend Present: no`).

**Lesson applied (iter-17, this exact blocker):** "Do NOT STALL on a latency-budget breach until it is
DIAGNOSED... check whether the diagnosis is blocked by missing telemetry before treating the residual as an
owner budget-amendment decision" — this iteration IS that telemetry pass, and per that same lesson it
deliberately does NOT attempt a mitigation or a budget-amendment fork before the diagnosis exists. **Lesson
applied (iter-11):** "cross-read `logs/backend.log`... before accepting an 'environmental, not code'
explanation" — the reason this iteration instruments the log stream directly rather than guessing from
wall-clock-only measurements again.

Reading `apps/backend/app/api/backtest.py:69-114` directly surfaced a concrete, testable hypothesis worth
separating into its own timing phase: `backfill_run_forward_returns` (line 81) is the ONE call in the
handler that can perform a real SQLite INSERT (create-once, idempotent) on the read path, on every request,
independent of `is_latest` — if a slow request's dominant phase is consistently this write-capable call
rather than the pure-read `resolved_forward_aggregate_evidence` (line 89), that is direct evidence for the
SQLite-writer-contention candidate over GIL/threadpool scheduling.

## IN SCOPE

### Backend

- [ ] Add wall-clock, phase-broken-down per-request timing instrumentation to `GET /api/backtest`
  (`apps/backend/app/api/backtest.py`) and the MCP `query_backtest` tool (`apps/backend/app/mcp/tools.py`),
  via a new logger following the existing `logging.getLogger("trendora.<component>")` convention
  (`main.py:45` = `"trendora.lifespan"`, `data_manager.py:89` = `"trendora.data_manager"`) — one INFO-level
  structured log line per request carrying: an ISO-8601 wall-clock timestamp, `is_latest`, a total elapsed
  time in milliseconds, and separate elapsed-ms values for: run resolution (`resolved_run`), the
  `backfill_run_forward_returns` step, `compute_run_scorecard`, and `resolved_forward_aggregate_evidence`
  (plus, only on the historical/non-`is_latest` ensure-loop branch, the `forward_aggregates_ingest_cached`
  calls it makes).
- [ ] In `resolved_forward_aggregate_evidence`'s widened cross-`asof_key` fallback
  (`apps/backend/app/engine/forward_testing.py`, the `older_rows` query at lines 1286-1292), defer loading
  `payload_json`: the initial selection scan across older candidate rows should read only the identifying
  columns (`asof_key`, `horizon`, `dataset_version`, `created_at`), then — once the winning `(asof_key,
  dataset_version)` pair is chosen — issue one targeted follow-up query selecting `payload_json` (plus the
  same identifying columns) filtered to exactly that winning pair, before calling `_serve(...)`. Same query
  intent and result; fewer bytes materialized for the older candidates that get discarded (today ~819 KB
  across 25 rows, growing ~164 KB per distinct as-of ever viewed, per the iter-17 audit).
- [ ] Add the missing endpoint-level test in `apps/backend/tests/test_forward_testing_serving_split.py`:
  an OLDER `evidence_asof` carried end-to-end through BOTH `app.api.backtest.backtest(...)` and
  `app.mcp.tools.query_backtest(...)` called directly (mirroring
  `test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows`'s fixture shape, lines 315-356, but
  calling the endpoint functions the way `test_backtest_route_and_mcp_tool_serve_evidence_asof_identically`
  does at lines 586-609). Confirmed by direct read: today's endpoint-layer tests (lines 484-609) only
  exercise the same-key `ready` and `not_yet_computed` states — every cross-boundary test exercises the
  resolver directly, never through either endpoint function.

### Frontend

None this iteration — the instrumentation and query-projection change are backend-only; no frontend file
changes, no new or altered UI surface, no served-value change for `RefreshingEvidenceBanner`/`EmptyState`
to consume differently.

### New user-facing capability

None directly visible this iteration. It produces the diagnostic evidence a future iteration needs to close
J-06/J-07/J-08's shared latency blocker.

### New information displayed

None — the new timing data lands only in `logs/backend.log`, an operational artifact, never a UI-served
value.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible to the user this iteration. `/backtest`'s served evidence stays byte-identical (TC-6); only the
operational observability behind it changes.

### Blueprint conformance

No new surfaces. This iteration's work lives entirely behind the existing `/backtest` + MCP `query_backtest`
home already registered in `blueprint.md`'s Information Architecture table for J-06/J-07/J-08.
`blueprint.md` has been updated this iteration: the stale "already added"-phrased iter-18 narrative paragraph
and the Data-Contract row's iter-18 tail sentence are corrected to "TARGETED this iteration, not yet built"
(the prior aborted pass had drafted them prematurely in the past tense); the iter-17 tail sentence is also
corrected from "TARGETED... not yet built" to "BUILT + EVALUATOR-CONFIRMED" since iter-17's B1 fix is in
fact already built and evaluator-confirmed (J-06/J-07/J-08 stay `partial` for the separate latency reason,
not for any defect in B1).

### Data-contract additions

None. A log line is not a served/displayed UI value, so nothing new is registered in the Data Contract this
iteration. The existing `evidence_status` / `evidence_generated_at` / `evidence_asof` / `evidence_by_horizon`
fields are unchanged in shape and, per TC-6/TC-7 below, byte-identical in value to their pre-iteration
behavior.

## OUT OF SCOPE

- Applying a latency mitigation, or an owner budget-amendment fork, before the diagnosis exists — this
  iteration deliberately stops at "make it measurable"; the fix-or-fork decision is sequenced to whichever
  iteration follows this one's fresh operator-supervised measurement (see BACKGROUND).
- `compute_forward_aggregates`'s body — byte-unchanged since iter-14, AG-8 resolved; not reopened (binding,
  `iteration-state.md` "Do not redo").
- The compute-vs-serve split and the completeness-gated cutover pruning logic (`forward_testing.py`
  ~lines 1023-1160) — untouched; never add a compute branch to the read path (binding, "Do not redo").
- TC-8-class live cross-`asof_key`-boundary capture — unproducible on this seed (`MAX(daily_prices.date)` =
  `MAX(scanner_runs.asof_date)` = `2026-07-22`); stays a documented, deferred owner data-cycle item, not a
  target here (binding, "Do not redo").
- `refreshing`'s no-self-heal behavior (audit B2) — settled trade-off, not revisited.
- `main.py`'s boot sequence, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`,
  `scripts/*`, `scripts/automation/*` — untouched (binding, "Do not redo"); the instrumentation lives inside
  `api/backtest.py` / `mcp/tools.py`, never the boot path.
- A generic, all-endpoint request-timing middleware or APM rollout — scoped strictly to `/backtest` and
  `query_backtest`, matching the evaluator's own next-step recommendation; not a framework-wide change.
- The full pytest suite — targeted, host-guard-confined runs only (`taskset -c 0-3,8-11`, BLAS/OMP=4). The
  `loaded_engine`-dependent `test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys` (the
  ~80-minute fixture) — cite it, do not run it (binding, "Do not redo").
- The `demo.sh ops-hardening --session-live` walkthrough — settled non-autonomous-deliverable (iter-12
  finding); not part of this iteration's DoD.
- J-06's other 10 idle-host page budgets, the ≤5s boot budget, and the non-`/backtest` on-load audit —
  settled iter-9/11/13; not re-measured (binding, "Do not redo").
- `data_manager.py`'s ingest finalize hook — investigated but not modified by iter-17 (confirmed: writes
  commit frequently, never one long-held transaction); not reopened by this instrumentation-only pass.

## DEFINITION OF DONE

- [ ] Per-request timing instrumentation lands for `GET /api/backtest` and MCP `query_backtest` (TC-1, TC-2,
  TC-3, TC-4)
- [ ] `resolved_forward_aggregate_evidence`'s widened fallback defers `payload_json` loading to a second,
  winner-only read (TC-5), with served evidence byte-identical to before (TC-6)
- [ ] A new endpoint-level test proves an OLDER `evidence_asof` survives end-to-end through both
  `GET /api/backtest` and MCP `query_backtest` (TC-7)
- [ ] Instrumentation never changes the honest empty-state behavior on a never-warmed store — still HTTP
  200, still logged (TC-8)
- [ ] All pre-existing tests in `test_forward_testing_serving_split.py`, `test_forward_testing_concurrency.py`,
  and `test_forward_testing.py` keep passing alongside the new tests; no regressions (the pre-existing,
  unrelated `test_db.py::test_create_all_produces_expected_tables` failure is carried, not new)
- [ ] Target journeys J-06, J-07, J-08 are evaluated by the goal-evaluator against the diagnostic evidence
  this iteration produces — this spec does not itself declare any journey passing; no code fix for the
  latency is attempted until a diagnosis exists
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (TC-11)
- [ ] No anti-goal violation introduced: AG-8 (the deferred-payload read stays bounded by the same
  distinct-as-of-count scope as today, TC-5), AG-3 (byte-identical served evidence, TC-6), AG-5 (the fallback
  filter direction is unchanged, not reopened), AG-10 (the operator re-measurement runs only via
  `scripts/start-backend.sh` under host-guard caps, TC-9)
- [ ] The operator-supervised deep-basis re-measurement runs WITH the new instrumentation active and is
  recorded in a new dated `reports/perf-budgets.md` section directly comparable to the iter-16/17 baseline
  (11/68 breaches, max 12.655s), including whatever the phase breakdown reveals about the dominant
  contributor on breaching requests, or an honest "still indeterminate" if it does not resolve (TC-9)
- [ ] A fresh live J-04 kill/restart replay (owed since iter-15; iter-16/17 performed only non-disruptive
  sanity checks) is performed by the operator in the same session, immediately after TC-9 concludes, and the
  `/data` Run History panel is confirmed to display the interrupted run's real checkpointed progress after
  restart (TC-10)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-18-dev.md`

## TESTING REQUIREMENTS

- Browser: regression-only for J-01, J-03, J-04, J-05 (deterministic golden replay for J-01/J-03/J-05; the
  LLM browser-qa lane for J-04, which has no golden script per the established session pattern) — TC-11. A
  spot check that `/backtest` still renders its evidence section with byte-identical values after the
  query-projection change (TC-6/TC-7) — no new UI behavior to verify for J-06/J-07/J-08 this iteration.
- Unit/integration: `apps/backend/tests/test_forward_testing_serving_split.py` (TC-5, TC-6, TC-7, TC-8
  below) plus a new or extended test module for the timing instrumentation itself (TC-1 through TC-4).
- Error cases: a request whose resolved run has no complete evidence anywhere in the table (the true
  fresh-install shape) must still return HTTP 200 with the honest empty state AND still emit a timing log
  line — instrumentation must never turn this path into a 500 or silently skip logging on it (TC-8).

- TC-1: given a request to `GET /api/backtest`, when the response is returned, then `logs/backend.log`
  contains one new log line for that request carrying a wall-clock ISO-8601 timestamp and a total-elapsed-time
  field in milliseconds.
- TC-2: given a request to `GET /api/backtest` for a date whose forward returns are not yet backfilled (so
  `backfill_run_forward_returns` inserts at least one row for that run), when the response is returned, then
  the logged line reports separate elapsed-ms values for run resolution, the forward-returns-backfill step,
  scorecard compute, and evidence resolution, and their sum falls within 5ms or 5% (whichever is larger) of
  the logged total.
- TC-3: given a call to the MCP `query_backtest` tool, when it returns, then it emits a timing log line
  carrying the same field names as TC-1/TC-2 (timestamp, total elapsed ms, per-phase elapsed ms).
- TC-4: given a pytest test using the `caplog` fixture, when `app.api.backtest.backtest(...)` is invoked
  directly (no live server or socket needed), then the captured log records include the timing fields from
  TC-1/TC-2 — provable without a running process.
- TC-5: given a `ForwardAggregateCache` fixture with several older `(asof_key, dataset_version)` candidates
  and exactly one complete, when `resolved_forward_aggregate_evidence`'s widened fallback executes, then the
  initial selection query (SQL-inspected via the same `before_cursor_execute` technique the existing
  `test_completeness_query_is_filtered_by_asof_key` test uses) does not name the `payload_json` column, and
  exactly one follow-up query selects `payload_json` filtered to the winning `(asof_key, dataset_version)`
  pair only.
- TC-6: given the same fixture as TC-5, when `resolved_forward_aggregate_evidence` is called, then
  `evidence_status`, `evidence_asof`, and `evidence_by_horizon` equal byte-for-byte the values it returned
  before this iteration's query-shape change (a regression guard against
  `test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows`'s existing assertions).
- TC-7: given a `ForwardAggregateCache` fixture where the LATEST `asof_key` has zero rows and an OLDER
  `asof_key` has a complete version (mirrors `test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows`),
  when `app.api.backtest.backtest(as_of=None, session=session)` AND `app.mcp.tools.query_backtest(session,
  asof=None)` are each called directly, then both responses report `evidence_status == "refreshing"` and an
  identical `evidence_asof` equal to the older date — the first endpoint-level test for this cross-boundary
  case (today only resolver-level tests cover it).
- TC-8: given a resolved run with no complete evidence anywhere in the table (the true fresh-install shape,
  mirrors `test_evidence_not_yet_computed_before_any_warm`), when `GET /api/backtest` is called after
  instrumentation lands, then it returns HTTP 200 with `evidence_status == "not_yet_computed"`, and a timing
  log line is still emitted for that request.
- TC-9 (OPERATOR-performed, AG-10-class, ONE pass, launcher-only — `scripts/start-backend.sh` ONLY): given
  the same deep-basis ingest-window concurrent-poll protocol iter-16/17's TC-16/TC-10 used (cooled host, 1 Hz
  `hwmon` sampler live, thermal watchdog armed, `taskset -c 0-3,8-11`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=
  MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`), when `/backtest` is re-measured with this iteration's
  instrumentation active, then the breach count, max latency, and the per-phase timing breakdown for at
  least the slowest observed requests are recorded in a new dated section of `reports/perf-budgets.md`,
  directly comparable to the iter-16/17 baseline (11/68 breaches, max 12.655s).
- TC-10 (OPERATOR-performed, immediately after TC-9, same session, non-code-change verification only): given
  the backend already running from TC-9's protocol, when a bounded-range backfill is submitted and the
  process is killed (`kill -9`, no clean shutdown) mid-run after at least one checkpoint interval has
  elapsed, then after restart the `/data` Run History panel displays the interrupted run's checkpointed
  progress (non-zero snapshot/date counts, not the creation-time defaults), and `GET /api/health` returns
  HTTP 200 with `readiness: "ready"` post-restart.
- TC-11: given the deterministic golden-replay scripts for J-01/J-03/J-05 and the LLM browser-qa lane for
  J-04 (no golden script exists for J-04, per the established session pattern), when this iteration's lean
  regression check runs, then all four report a PASS verdict (replay exit 0 for J-01/J-03/J-05; browser-qa
  PASS for J-04) with no new failure attributable to this iteration's diff.

## NOTES

- **Sequencing, not scope-shrinking:** TC-9/TC-10 are the only items this iteration hands to the operator;
  everything else (instrumentation, the query-projection cheap win, the new test) is agent/reviewer-performable.
- **Current live-service snapshot at spec-writing time** (read-only introspection only — `ss`/`curl`/`/proc`
  reads; no service was started, stopped, or restarted by this decomposer pass): the main backend (`:8255`)
  did NOT respond to a health probe at spec-writing time (connection refused/timeout) — consistent with this
  session's documented "the box reaps services between stages" behavior; the operator will need to
  (re)launch it via `scripts/start-backend.sh` for TC-9/TC-10. The iter-17 TC-9 throwaway backend is still
  listening on `:18255` (currently pid 1245537, started 2026-07-24T02:41:19 UTC, ~6h41m uptime at
  spec-writing time) — but unlike the uncapped pid the iter-17 dev handoff flagged as an AG-10 hazard
  (pid 1101499, `Max address space: unlimited`, no `MALLOC_ARENA_MAX`), THIS pid was checked directly via
  `/proc/1245537/limits`/`environ` and carries the correct `memory_cap_mb` `ulimit -v` (6,442,450,944 bytes =
  6144 MB) and `MALLOC_ARENA_MAX=2` — i.e., someone since re-launched it via `scripts/start-backend.sh` with
  both caps present (confirmed via `/proc`), addressing that flagged hazard. Recommend the operator tear this throwaway process down (its evidentiary
  value for TC-9 is already captured in `reports/perf-budgets.md`'s iter-17 section) once this iteration's
  own TC-9/TC-10 pass is done — a stray long-lived process against a disposable `/tmp` DB copy serves no
  further purpose, even though it is no longer an uncapped hazard.
- **Why the phase breakdown singles out `backfill_run_forward_returns`:** it is the one call in
  `backtest()`/`query_backtest()` that can perform a real SQLite INSERT on the read path (create-once,
  idempotent), independent of `is_latest`. If TC-9's phase breakdown shows this phase — not the pure-read
  `resolved_forward_aggregate_evidence` — dominating the breaching requests, that is direct evidence for the
  SQLite-writer/checkpoint-contention candidate over GIL/threadpool scheduling; if neither phase dominates
  and total-minus-phases is large, that points to scheduling/queueing delay instead. Record whichever pattern
  TC-9 actually shows — do not force a conclusion the numbers do not support.
- **`data_manager.py`'s ingest finalize hook has no comparable timestamped log line today** (confirmed by
  direct read of iter-17's own investigation: its `logger.exception(...)`/`logger.warning(...)` calls are
  failure-path only, and its `elapsed_seconds` fields are written to job/run records, not to
  `logs/backend.log` with a wall-clock stamp). If TC-9's read-side instrumentation alone still cannot pin the
  mechanism, ingest-side timing is the next cheap candidate — explicitly not this iteration's scope, carried
  forward as a contingent note for whichever iteration follows.
- Carried, unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing, no schema change
  this iteration).
- No new `assumptions.md` entry this iteration — the scope-sequencing choice (diagnose now, fix-or-fork
  later) is a direct continuation of the iter-17 evaluator's own stated sequencing, not a fresh ambiguity in
  goal.md; the lean-vs-full depth call is a rubric application (justified above with the four numbered
  triggers), not a goal-text interpretation, so it is not logged as an assumption either.
