# Goal Iteration 11 — Re-sweep J-06's page-load/boot measurements + on-load audit (no source changes anticipated)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 11
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
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

Bring J-06's evidence current: re-sweep all 11 named pages' real-browser TTI/on-load latencies and the
≤5s boot-to-health budget under the now-host-guard-hardened `scripts/start-backend.sh` (unmeasured since
iter-9 added that block), and record a code-level audit confirming no on-load path performs an unbounded
scan or recomputes an already-ingest-warmed aggregate — so J-06 can be scored on complete, current
evidence instead of numbers that predate this session's own launcher changes.

## BACKGROUND

Priority rubric: no journey is `regressed` (rule 1 — none apply); the last coherence verdict
(`iter-10/coherence.md`) was COHERENCE-PASS, so no consolidation mandate (rule 2); J-06 is the only
non-passing Must-have and both iter-9's and iter-10's evaluators explicitly rejected STALLED for it,
stating its remaining work — the perf re-sweep, the boot re-measure, and the code audit — is fully
agent-owned (rule 3/6). Excluded from this iteration, per explicit owner-decision framing repeated across
iter-8/9/10's evals: the on-load `GET /api/backtest` → `forward_aggregates_cached` MemoryError (critical
AG-8 dimension) and `HOST_GUARD_REQUIRE_MARKERS`. Also excluded: the J-05/J-06 `demo.sh
ops-hardening --session-live` walkthroughs — per the iter-5 decomposer's own established reading
(`assumptions.md` iter-5/6/7/8 entries), these are session-closeout showcase artifacts produced
automatically by the pipeline's own iteration-summarizer/demo-narrator stage once their originating
iteration flags them `[NEW]`, not a developer TESTING REQUIREMENT — restating that reading here rather
than re-logging it.

Depth is **lean**: none of the four full-depth triggers fire — no structural/cross-cutting refactor (zero
source changes are planned; the code audit is read-only), no Data-Contract/schema change (this iteration
only re-times already-registered rows through their existing endpoints), the last verdict was CONTINUE
not ESCALATE, and "Consecutive lean iterations dispatched: 1" is below the hardening-cadence threshold of
4. iter-10's own evaluator recommended full again, but per the established iter-9→iter-10 precedent that
recommendation is non-binding, and "a thorough measurement pass" is not a valid full trigger any more than
"needs unit tests" is — a lean developer→reviewer→browser-qa cycle is exactly what closed the structurally
identical iter-10 measurement/verification pass.

Lessons applied directly: **iter-5** — TTI/latency measurement must come from a REAL BROWSER, not `curl`
(Chrome's 6-connections-per-origin cap under-reports on call-heavy pages); the browser-qa lane, not
`measure-perf.sh`'s curl helper, must produce the page-timing numbers this iteration commits. **iter-6** —
measure on an otherwise-IDLE host; a concurrent heavy job/pytest run contaminates a cold-miss reading
(iter-6's own 555s→73s retraction). **iter-8** — this spec sets `Frontend Present: yes` explicitly even
though no frontend source changes are planned, because TESTING REQUIREMENTS name browser journeys and the
still-unfixed `Frontend Present: no` misrouting bug would otherwise skip browser-qa outright. **iter-10**
— AG-10 hygiene: the iter-10 developer session ran targeted pytest unconfined (hwmon peak 91 °C vs the
95 °C watchdog, no trip, but a documented minor AG-10 finding); this iteration explicitly confines any
pytest it runs under `host-guard.env`'s `taskset`/BLAS caps to avoid repeating that finding.

**Operational constraint (new this iteration, from the operator).** The dispatching operator reports that
agents in this pipeline cannot start or stop backend/frontend services directly (the permission classifier
blocks it) and that the mid-task operator-resume channel is broken this session. The 11-page browser sweep
does not need a fresh process start — it needs services already running, which `browser-qa-phase.sh`'s own
service management provides (outside any agent's own Bash calls), exactly as it has for every prior
browser-qa pass this session. The ONE step that inherently needs a backend **start** (nothing may already
be listening on the port) is the boot-to-health measurement — see NOTES for the operator-assisted fallback
and `assumptions.md`'s iter-11 entry.

## IN SCOPE

### Backend
- [ ] No product source changes anticipated. Re-run `bash scripts/measure-perf.sh --boot` (standard path)
      against the current committed tree — the first boot measurement since iter-9 added the host-guard
      `taskset`/BLAS block to `scripts/start-backend.sh` (the last recorded number, 1.387s, predates that
      change) — and append the dated result to `reports/perf-budgets.md`. If it exceeds the 5s budget,
      record an honest WARN with the exact overage; never loosen or omit the number.
- [ ] Perform a static, read-only code-level audit of every on-load endpoint feeding the 11 pages named in
      goal.md J-06 step 1, confirming none performs an unbounded `daily_prices`/whole-table ORM scan or
      recomputes an already-ingest-warmed aggregate (the Coverage payload, Backfill run-summary, Job
      history, and Membership-timeline/research-hot-key Data-Contract rows). Cite file:line evidence per
      endpoint in the dev handoff.
- [ ] If the audit finds a genuine violation, do NOT fix it inline — name it precisely (module/function/
      file:line) in the dev handoff and leave it for a future iteration's scope, per iter-5's own
      precedent of not bundling an unplanned fix into a measurement pass.
- [ ] Any pytest invocation this iteration runs under `project-extensions/host-guard/host-guard.env`'s
      `HOST_GUARD_CPU_LIST` taskset mask plus `HOST_GUARD_BLAS_THREADS`-derived OMP/OpenBLAS/MKL/numexpr
      thread caps (AG-10 hygiene).

### Frontend
- [ ] No product source changes anticipated. The real-browser TTI/on-load-latency sweep of all 11 pages is
      browser-qa-agent's own Chrome-MCP measurement pass, not a code change.

### New user-facing capability
None new. This iteration re-measures and re-audits already-shipped behavior; no new capability ships.

### New information displayed
None new to the product UI. `reports/perf-budgets.md` gains fresh dated sections (a measurement artifact,
not a served runtime value — already registered, see Data-contract additions below).

### New user actions
None.

### UI surface changes
None. Every measured page is an existing, unchanged page.

### Product surface delta
None — a verification-only iteration. The product surface is unchanged; only the currency of its
committed performance evidence is being refreshed.

### Blueprint conformance
No new surfaces. This iteration's work lives entirely under J-06's existing home in `blueprint.md`'s
Information Architecture table ("cross-cutting measurement; canonical artifact is
`reports/perf-budgets.md`, not a UI page") plus the 10 other pages' already-registered homes it re-times
(Dashboard, Stocks, Sectors, Themes, Data Manager, Evidence, Scanner Runs, Backtest, Watchlist, Research).

### Data-contract additions
None. This iteration reads/re-times only the already-registered "Page performance budgets" row (`N/A` —
a measurement artifact, served via `reports/perf-budgets.md`) and re-exercises the already-registered
endpoints behind the 11 pages (Coverage payload, Backfill run-summary contract, Job history, Membership-
timeline/research-hot-key caches, readiness/preflight) through their EXISTING single computing module +
serving endpoint each — no second producer, no second endpoint, no new field.

## OUT OF SCOPE

- The deferred on-load `GET /api/backtest` → `forward_aggregates_cached` MemoryError (critical AG-8
  dimension) — owner decision still outstanding per iter-9/iter-10's evals; not re-planned here.
- Flipping `HOST_GUARD_REQUIRE_MARKERS` — owner decision.
- The J-05/J-06 `demo.sh ops-hardening --session-live` walkthroughs — produced automatically by the
  showcase pipeline once their originating iteration flags them `[NEW]` (iter-5 decomposer precedent);
  not a developer TESTING REQUIREMENT this iteration.
- Fixing any genuine on-load-scan violation this iteration's own audit might find — named in the dev
  handoff and scoped to a future iteration instead (see IN SCOPE).
- Re-running the heavy-ingest pytest test (`test_start_backend_survives_back_to_back_heavy_ingest_
  under_memory_cap`) — settled/BINDING "do NOT re-run" per iteration-state (iter-9: 1092.93s, 439/439
  health-200, VmPeak 24.7% under cap). This iteration's boot/page measurements are all LIGHT.
- Any change to `app/api/health.py`, `app/engine/readiness.py`, `main.py` boot sequence, `warmup.py`,
  `max_range_days`/`snapshot_cadence`, the `/evidence` drawdown warm, or `server.memory_cap_mb` — all
  BINDING "Do not redo" items from iteration-state.
- `runs/goal-ops-hardening-iter-10/status.json`'s stuck `dev_complete`/`browser_checks_run: false`
  bookkeeping, `merge_ui_test_results.py`'s dropped `**FAIL**` cells, and the `Frontend Present: no`
  browser-qa-skip misrouting — goal-mode harness bugs, out of a product-facing decomposer's remit (iter-9
  precedent: never patch `scripts/automation/*`); the last item is routed around here via the explicit
  `Frontend Present: yes` metadata field, not fixed at the source.
- Hand-editing any past iteration's point-in-time artifacts.

## DEFINITION OF DONE

- [ ] J-06 passes its measurement + audit acceptance via browser-qa-agent + dev handoff: all 11 named
      pages' real-browser TTI/on-load latencies recorded in `reports/perf-budgets.md` within budget (or
      honestly flagged WARN), the ≤5s boot budget re-measured under the current host-guard-hardened
      `start-backend.sh`, and the dev handoff's code audit states explicitly that no on-load endpoint
      performs an unbounded scan or recompute.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (deterministic replay + LLM
      fallback, mechanically verified).
- [ ] No anti-goal violation introduced — AG-10 confinement honored for any pytest run this iteration; AG-3
      byte-identity of at least two already-warmed values spot-checked against a fresh recomputation.
- [ ] Existing backend test suite (targeted subset, host-guard-confined) passes with no NEW failures beyond
      the pre-existing documented `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-11-dev.md`, stating explicitly whether
      any source file changed (expected: none) and citing the exact `reports/perf-budgets.md` sections +
      audit file:line evidence supporting J-06's acceptance.

## TESTING REQUIREMENTS

- Browser: J-06 (target — real-browser TTI + on-load latency sweep across all 11 named pages, plus the
  boot-to-health measurement), J-01/J-03/J-04/J-05 (required-still-passing, deterministic golden replay
  with LLM fallback).
- Unit/integration: targeted backend subset touching the read paths this iteration re-times
  (`apps/backend/tests/test_data_manager_jobs_pipeline.py`, `apps/backend/tests/
  test_start_backend_script.py`, excluding the opt-in `TRENDORA_RUN_HEAVY_INGEST_TEST` lane), run under
  host-guard confinement.
- Error cases: N/A — no new input surface; this iteration's "failure path" is an honest WARN if any
  page/boot measurement exceeds its committed budget, never a silently loosened or omitted number.

Test-first contract:

- TC-1: given the backend and frontend running in prod mode (`scripts/start-backend.sh` /
  `scripts/start-frontend.sh`, never `dev.sh`) with the host otherwise idle (no concurrent heavy ingest or
  pytest run), when a real Chrome browser navigates to each of the 11 named pages (`/`, `/stocks`,
  `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`,
  one `/research` lab), then each page's real-browser time-to-interactive and on-load API latencies are
  recorded as a new dated section in `reports/perf-budgets.md`.
- TC-2: given the measurements recorded in TC-1, when each is compared against its committed budget row in
  `reports/perf-budgets.md`, then every measurement is marked "holds: yes", or, for any that exceed
  budget, an honest WARN is recorded stating the exact overage (never silently loosened or omitted).
- TC-3: given nothing is currently listening on the backend port, when a fresh backend cold-boot is
  measured (process start → first `GET /api/health` HTTP 200), then the wall-clock time is recorded as a
  new dated row in `reports/perf-budgets.md`, is ≤5 seconds, and cites the exact PID/timestamp evidence —
  or, if the executing agent's environment blocks a direct service start, the dev handoff names the
  operator-provided command output verbatim (see NOTES) rather than fabricating or omitting the number.
- TC-4: given the dev handoff's static code audit of every on-load endpoint feeding the 11 J-06 pages, when
  it is read, then it states explicitly, per endpoint, whether it performs an unbounded
  `daily_prices`/whole-table ORM scan or recomputes an already-ingest-warmed aggregate, citing file:line
  for each (expected: none found; any found is named, not fixed, and filed as future scope).
- TC-5: given at least two already-registered ingest-time-warmed values (e.g. `forward_aggregates_cached`,
  `market_phase_cached`), when their served value for a fixed as-of is spot-checked against a canonical
  fresh recomputation, then the two are byte-identical (AG-3).
- TC-6: given any pytest invocation run during this iteration, when its launch command is inspected in the
  dev handoff, then it is wrapped in `HOST_GUARD_CPU_LIST`'s `taskset` mask plus the
  `HOST_GUARD_BLAS_THREADS`-derived `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/
  `NUMEXPR_NUM_THREADS` caps sourced from `project-extensions/host-guard/host-guard.env` (AG-10 hygiene).
- TC-7: given the targeted backend test subset named above (excluding `TRENDORA_RUN_HEAVY_INGEST_TEST`),
  when it is run under the TC-6 confinement, then it completes with zero failures other than the
  pre-existing documented `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- TC-8: given J-01/J-03/J-04/J-05's stored golden replay scripts, when they are executed via deterministic
  replay against the current build, then each records a PASS outcome in the regression-replay-results
  artifact (LLM fallback only on an adjudicated non-pass).
- TC-9: given this iteration reaches completion, when
  `docs/handoffs/goal-ops-hardening-iter-11-dev.md` is inspected, then it exists, states explicitly
  whether any source file changed (expected: none), and cites the specific `reports/perf-budgets.md`
  section + audit file:line evidence that supports J-06's acceptance.

## NOTES

- **Operational constraint on who starts the backend for TC-3.** The dispatching operator reports that
  agents in this pipeline cannot start or stop services directly (permission classifier) and that the
  mid-task operator-resume channel is broken this session. The 11-page browser sweep (TC-1/TC-2) needs no
  fresh process start — services are expected already running via `browser-qa-phase.sh`'s own service
  management, exactly as every prior browser-qa pass this session. Only TC-3 (boot-to-health) inherently
  needs nothing currently listening on the backend port. Standard path: the developer runs
  `bash scripts/measure-perf.sh --boot` itself. Fallback, if that is genuinely blocked in this environment:
  request the operator run exactly that command (confirming nothing already listening first) and report
  the console output/timestamps verbatim; the developer then records that operator-provided output, with
  attribution, in `reports/perf-budgets.md` rather than fabricating or silently omitting the number. See
  `assumptions.md`'s iter-11 entry.
- **Heavy-ingest test — settled, do NOT re-run** (iter-9: 1092.93s, 439/439 health-200, VmPeak 24.7% under
  cap). Nothing in this iteration's scope is a full-universe rebuild or backfill.
- **Host-guard launcher caps — DONE**, already shipped in `start-backend.sh` + `dev.sh`'s backend subshell;
  the fresh TC-3 boot's `logs/backend.log` banner should still show `cpu_list=0-3,8-11 blas_threads=4` —
  re-confirm, never weaken or strip.
- **Session state entering this iteration:** J-01/J-03/J-04/J-05 passing; J-06 partial, the ONLY
  non-passing Must-have. AG-8 (on-load `/api/backtest` MemoryError) and `HOST_GUARD_REQUIRE_MARKERS`
  remain open owner decisions, unaffected by this iteration. If J-06 scores `passing` this iteration, ALL
  FIVE Must-have journeys are passing session-wide, but the unresolved critical AG-8 dimension still
  hard-blocks GOAL_ACHIEVED per iter-8/9/10 precedent — flagging so the next decomposer pass does not
  manufacture new journey scope and instead writes the "all journeys passing, AG-8 owner-decision
  outstanding" holding spec if that state is reached, deferring to the evaluator/human on GOAL_ACHIEVED.
- Framework maintainer items (carried, unchanged): `merge_ui_test_results.py` drops emphasised `**FAIL**`
  cells from the merged rollup — always score from the raw `.llm.md`. The `Frontend Present: no` →
  browser-qa-skip misrouting is routed around here via the explicit `Frontend Present: yes` field, not
  fixed at the source. `runs/goal-ops-hardening-iter-10/status.json` remains stuck at `dev_complete`/
  `browser_checks_run: false` despite a passing browser lane — a goal-mode harness bookkeeping bug, not
  touched here (iter-9 precedent: never patch `scripts/automation/*`).
