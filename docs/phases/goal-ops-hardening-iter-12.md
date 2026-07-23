# Goal Iteration 12 — J-06 gap closure: perf-budget transcription + controlled re-measurement + audit correction (no source changes anticipated)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 12
- **Mode:** next
- **Depth:** full
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

Close J-06's two remaining, agent-owned gaps (G1: sweep numbers missing from the canonical
`reports/perf-budgets.md` artifact; G2: `/api/indexes?full=true`'s over-budget reading has no valid
like-for-like control) and correct the record on iter-11's incomplete TC-4 audit — so J-06 can finally be
scored on complete, honest, current evidence, while the critical AG-8 anti-goal dimension it surfaced stays
flagged as an unresolved owner decision, rather than silently dropped or invented away, in the process.

## BACKGROUND

Priority rubric: no journey is `regressed` (rule 1 — none apply, all four other Must-haves are `passing`);
the last coherence verdict (`iter-11/coherence.md`) was COHERENCE-PASS, so no consolidation mandate (rule
2); J-06 is the only non-passing Must-have, and both G1 and G2 are explicitly agent-owned work per iter-11's
own evaluator ("transcribing the sweep into perf-budgets.md and re-measuring `/api/indexes` are concrete
agent work" — STALLED was rejected on exactly this basis) — rules 3/6. Rule 6 ("don't pick a human-blocked
journey") is satisfied precisely because this spec separates the two: J-06's G1/G2 gaps are agent work and
stay in scope; the critical AG-8 dimension the same iteration exposed (the `forward_aggregates_cached` →
`compute_forward_aggregates` unbounded `ScannerResult` load that OOM'd twice and produced two on-load
HTTP 500s) is an explicit, repeatedly-named OWNER decision and is excluded here, same as iter-8/9/10/11.

**Depth is FULL because the last dispatched verdict was ESCALATE** — trigger 3 ("Prior ESCALATE (mandatory,
no exceptions)") fires unconditionally regardless of how small this iteration's own work is. This is not a
structural/cross-cutting change on its own merits (no source file is expected to change; the diff is
report-file transcription, a controlled re-measurement, and an audit correction — the same "empty product
diff" shape as iter-9/iter-11), but the mandatory trigger applies regardless.

Lessons applied directly: **iter-5** — TTI/latency and endpoint-latency numbers must come from a REAL
BROWSER, not `curl` (Chrome's 6-connections-per-origin cap under-reports on call-heavy pages) — G2's
re-measurement is a real-Chrome pass, not curl. **iter-6** — measure on a verifiably IDLE host; a concurrent
job/pytest run contaminates a reading, and a contamination claim must be checked, not assumed. **iter-11**
(the load-bearing lesson for this iteration) — do not accept "ambient host contention" as an explanation
without cross-reading `logs/backend.log` for a same-window MemoryError/HTTP-500 and `logs/hwmon/hwmon.csv`
for MemAvailable/load1: iter-11's own WARN #1 disclosure attributed `/api/indexes?full=true`'s 2066.3ms/
2671.8ms spike to ambient load using only `uptime`/`ps`, and the goal-evaluator's log cross-read
subsequently proved that the OTHER two iter-11 anomalies in the very same window (the `/api/health`
2948.8ms outlier and two on-load 500s) were actually the backend's OWN near-OOM event
(`forward_aggregates_cached`'s MemoryError), not ambient load. G2 must positively rule this in or out for
`/api/indexes` specifically — via `logs/backend.log` (no concurrent ingest job) and `logs/hwmon/hwmon.csv`
(actual load1/MemAvailable at the moment of each reading) — not assume the same story a second time.
**iter-9's AG-10 lesson** — any pytest this iteration runs stays host-guard-confined.

## IN SCOPE

### Backend
- [ ] Transcribe the already-captured 11-page sweep + endpoint-latency readings from
      `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-perf-sweep-summary.txt` into a new dated
      section of `reports/perf-budgets.md`. Preserve the ORIGINAL measurement timestamp (2026-07-22
      ~21:38–21:49Z) alongside this iteration's transcription date. Include both over-budget
      `/api/indexes?full=true` readings (2066.3ms, 2671.8ms) and the `/api/health` 2948.8ms outlier as
      disclosed WARNs — do not omit, average away, or silently retain only the favorable reading. This is
      transcription of existing evidence, not a re-measurement.
- [ ] Re-measure `GET /api/indexes?full=true` on `/data` with three independent, cache-disabled real-browser
      loads (a fresh navigation each time — never a repeated hit inside the same already-warm tab). Before
      and during each reading, confirm via `logs/backend.log` that no backfill/fetch/rebuild job is
      in-flight, and via `logs/hwmon/hwmon.csv` that load1/MemAvailable at that timestamp are in the
      already-established idle range. Record all three readings plus this idle-confirmation evidence in
      `reports/perf-budgets.md`, honestly WARN-flagged if any reading still exceeds the committed ≤1.5s
      budget.
- [ ] Append a correction addendum to `reports/perf-budgets.md`'s existing TC-4 audit section (mirroring the
      `iter-9 P1` "AUDIT CORRECTION" blockquote convention already used in that same file), naming — not
      fixing — the unbounded-load site iter-11's audit never examined: `compute_forward_aggregates`'s
      MISS/compute path at `apps/backend/app/engine/forward_testing.py:826`
      (`session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`), reached
      via `forward_aggregates_cached` on a cache miss. State explicitly that iter-11's "no genuine violation
      found" conclusion covered only cache-HIT paths.
- [ ] Read `data_provider_runs` rows 120/121/122 directly and state in the dev handoff, explicitly, whether
      the recorded `aggregates_refreshed` set (4-of-7 on these zero-new-date runs) is consistent with
      `latest_snapshot`/`market_phase` being legitimately skipped when no new trading date lands, and that
      `forward_aggregates`'s absence in runs 121/122 is solely attributable to the MemoryError abort (cite
      `logs/backend.log:27185`/`:27233`) — confirming J-05's own contract is intact, or flagging it for
      re-open if the evidence does not support that reading.
- [ ] Any pytest invocation this iteration runs is wrapped in
      `project-extensions/host-guard/host-guard.env`'s `HOST_GUARD_CPU_LIST` taskset mask plus the
      `HOST_GUARD_BLAS_THREADS`-derived OMP/OpenBLAS/MKL/numexpr thread caps (AG-10 hygiene).
- [ ] No fix to the AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded load — name
      it precisely (above), do not touch the function.

### Frontend
- [ ] No product source changes anticipated. The three-load `/api/indexes` re-measurement (G2) and the
      required-still-passing replay are browser-qa-agent's own Chrome-MCP passes, not code changes.

### New user-facing capability
None new. This iteration transcribes existing evidence, re-measures one endpoint under a controlled
condition, and corrects an audit record; no new product capability ships.

### New information displayed
None new to the product UI. `reports/perf-budgets.md` gains a new dated section plus a correction
addendum — a measurement artifact, not a served runtime value, already registered in the Data Contract.

### New user actions
None.

### UI surface changes
None. Every touched/measured surface (`/data`) is an existing, unchanged page.

### Product surface delta
None — a verification/documentation-only iteration. The product surface is unchanged; only the
completeness and currency of J-06's committed evidence, and the accuracy of iter-11's audit record, change.

### Blueprint conformance
No new surfaces. This iteration's work lives entirely under J-06's existing home in `blueprint.md`'s
Information Architecture table ("cross-cutting measurement; canonical artifact is
`reports/perf-budgets.md`, not a UI page") plus `/data`'s existing home (Data Manager) for the G2
re-measurement.

### Data-contract additions
None. This iteration reads/re-times only the already-registered "Page performance budgets" row (`N/A` — a
measurement artifact, served via `reports/perf-budgets.md`) and the already-registered Coverage payload
row behind `/data`'s `/api/indexes` call — no second producer, no second endpoint, no new field.

## OUT OF SCOPE

- The AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load MemoryError fix —
  critical, unresolved, OWNER decision (scope a bounded/streamed rewrite, amend goal.md, or formally defer);
  not invented here.
- Flipping `HOST_GUARD_REQUIRE_MARKERS` — owner decision.
- The J-05/J-06 `demo.sh ops-hardening --session-live` walkthrough — this iteration's decomposer verified
  (by reading `scripts/automation/run-goal.sh`) that no automatic session-mode demo-narrator pass exists
  anywhere in the loop, correcting the "will self-resolve automatically" reading iterations 4/5/6/7/9/11
  applied (`assumptions.md`, iter-12). It is neither producible nor gradable as an autonomous artifact
  under this framework's evidence model and stays an explicit open owner decision alongside AG-8, not
  developer scope.
- Re-running the settled heavy-ingest pytest test
  (`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`) — BINDING "do NOT re-run"
  per iteration-state (iter-9: 1092.93s, 439/439 health-200, VmPeak 24.7% under cap).
- Any change to `app/api/health.py`, `app/engine/readiness.py`, `main.py` boot sequence, `warmup.py`,
  `max_range_days`/`snapshot_cadence`, the `/evidence` drawdown warm, or `server.memory_cap_mb` — all
  BINDING "Do not redo" items from iteration-state.
- Re-measuring the boot-to-health budget or the other 10 pages' TTI numbers — already freshly measured in
  iter-11 (1.364s boot; all 10 other pages comfortably in budget); only `/api/indexes?full=true` needs a
  genuine like-for-like control per G2.
- Framework harness bugs (`merge_ui_test_results.py`'s dropped `**FAIL**` cells, the `Frontend Present: no`
  browser-qa-skip misrouting, `runs/goal-ops-hardening-iter-11/status.json`'s stuck bookkeeping) — out of a
  product-facing decomposer's remit (never patch `scripts/automation/*`); flagged in NOTES, not fixed here.
- Hand-editing any past iteration's point-in-time artifacts.

## DEFINITION OF DONE

- [ ] J-06's G1 closed: `reports/perf-budgets.md` contains a new dated section transcribing the full
      iter-11 sweep (all 11 pages' TTI + every endpoint-latency reading), including both disclosed WARNs,
      with the original 2026-07-22 measurement timestamp cited alongside this iteration's transcription
      date.
- [ ] J-06's G2 closed: three independent, cache-disabled real-browser `GET /api/indexes?full=true`
      readings recorded in `reports/perf-budgets.md`, each cross-checked against `logs/backend.log` and
      `logs/hwmon/hwmon.csv` for a genuinely idle, no-concurrent-ingest window — not a single cached read
      accepted as the control.
- [ ] TC-4 audit correction recorded: `reports/perf-budgets.md` names
      `apps/backend/app/engine/forward_testing.py:826`'s MISS/compute path as the unbounded-load site
      distinct from the cache-HIT paths already audited — named, not fixed inline.
- [ ] Dev handoff states explicitly whether `data_provider_runs` rows 120/121/122's 4-of-7
      `aggregates_refreshed` outcome is design-correct, with J-05's contract confirmed intact or flagged
      for re-open.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (deterministic replay + LLM
      fallback, mechanically verified).
- [ ] No anti-goal violation introduced — the critical AG-8 entry is neither newly introduced nor worsened
      (product diff remains measurement/documentation-only); AG-10 confinement honored for any pytest run
      this iteration.
- [ ] Existing backend test suite (targeted subset, host-guard-confined) passes with no NEW failures beyond
      the pre-existing documented `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-12-dev.md`, stating explicitly whether
      any source file changed (expected: none) and citing the exact `reports/perf-budgets.md` sections
      supporting J-06's G1/G2 closure.

## TESTING REQUIREMENTS

- Browser: J-06 (target — G2's three-load `/api/indexes` control measurement, real Chrome via
  browser-qa-agent), J-01/J-03/J-04/J-05 (required-still-passing, deterministic golden replay with LLM
  fallback).
- Unit/integration: targeted backend subset touching the re-measured/re-audited read paths
  (`apps/backend/tests/test_data_manager_jobs_pipeline.py`, `apps/backend/tests/test_forward_testing.py`,
  excluding the opt-in `TRENDORA_RUN_HEAVY_INGEST_TEST` lane), run under host-guard confinement.
- Error cases: N/A — no new input surface; this iteration's "failure path" is an honest WARN if the
  re-measured endpoint still exceeds budget under a genuinely idle control, never a silently loosened or
  omitted number.

Test-first contract:

- TC-1: given `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-perf-sweep-summary.txt`'s
  already-captured readings, when transcribed into `reports/perf-budgets.md`, then a new dated section
  contains all 11 pages' TTI figures and all endpoint-latency readings, including the two over-budget
  `/api/indexes?full=true` values (2066.3ms, 2671.8ms) and the `/api/health` 2948.8ms outlier, each marked
  WARN where over budget, with both the original 2026-07-22 measurement timestamp and this iteration's
  transcription date stated.
- TC-2: given the backend and frontend running with no in-flight backfill/fetch/rebuild job (confirmed via
  `logs/backend.log`) and host load confirmed idle (confirmed via `logs/hwmon/hwmon.csv`), when a real
  Chrome browser performs three independent fresh navigations to `/data` (no repeated cached tab), then
  each navigation's `GET /api/indexes?full=true` latency is recorded in `reports/perf-budgets.md`, each
  marked "holds: yes" (≤1.5s) or an honest WARN stating the exact overage.
- TC-3: given `reports/perf-budgets.md`'s existing TC-4 audit table (iter-11), when the correction addendum
  is appended, then it names `apps/backend/app/engine/forward_testing.py:826`
  (`compute_forward_aggregates`'s `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`)
  as the unbounded MISS/compute-path site not covered by the prior cache-HIT-only audit, with no
  modification to that function's code.
- TC-4: given `data_provider_runs` rows 120/121/122, when their `aggregates_refreshed` field is read from
  the database, then the dev handoff states explicitly whether the 4-of-7 outcome on these zero-new-date
  runs is design-consistent (`latest_snapshot`/`market_phase` legitimately skipped) and that
  `forward_aggregates`'s absence is solely the MemoryError abort logged at `logs/backend.log:27185`/`:27233`.
- TC-5: given J-01's and J-03's stored golden replay scripts, when executed via deterministic replay against
  the current build, then each records a PASS outcome in the regression-replay-results artifact.
- TC-6: given J-04's and J-05's acceptance steps, when re-verified this iteration (LLM fallback lane), then
  both are confirmed passing with cited evidence (log grep, database row, or rendered screenshot).
- TC-7: given any pytest invocation run during this iteration, when its launch command is inspected in the
  dev handoff, then it is wrapped in `HOST_GUARD_CPU_LIST`'s `taskset` mask plus the
  `HOST_GUARD_BLAS_THREADS`-derived `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/
  `NUMEXPR_NUM_THREADS` caps sourced from `project-extensions/host-guard/host-guard.env`.
- TC-8: given the targeted backend test subset named above, when run under the TC-7 confinement, then it
  completes with zero failures other than the pre-existing documented
  `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- TC-9: given this iteration reaches completion, when
  `docs/handoffs/goal-ops-hardening-iter-12-dev.md` is inspected, then it exists, states explicitly whether
  any source file changed (expected: none), and cites the specific `reports/perf-budgets.md` sections
  supporting J-06's G1/G2 closure.

## NOTES

- Depth is FULL solely because the prior dispatched verdict was ESCALATE (trigger 3, mandatory, no
  exceptions) — not because this measurement/documentation pass is itself structurally risky. Its own
  expected product diff is empty, the same shape as iter-9/iter-11.
- **OWNER DECISIONS outstanding, not to be invented by any agent:** (1) scope, amend, or formally defer the
  critical AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load MemoryError —
  hard-blocks GOAL_ACHIEVED regardless of J-06's outcome this iteration; (2) `HOST_GUARD_REQUIRE_MARKERS`;
  (3) the J-05/J-06 `demo.sh ops-hardening --session-live` walkthrough — corrected this iteration
  (`assumptions.md`, iter-12) from "will self-resolve automatically" to "no autonomous mechanism produces
  it — needs a human to run it once, a goal.md wording amendment, or a framework enhancement adding a
  session-level record mode."
- **If J-06 reaches `passing` this iteration**, all five Must-have journeys are passing session-wide, but
  the unresolved critical AG-8 dimension and the two open owner decisions above still hard-block
  GOAL_ACHIEVED — the next decomposer pass should write the "all journeys passing, owner decisions
  outstanding" holding spec rather than manufacture new journey scope, deferring to the evaluator/human.
- **Operator note (as relayed):** backend is up on :8255, frontend on :3255, host-guard caps live — no
  service start/restart is needed for this iteration's measurements. G2's "no concurrent ingest" check only
  needs confirmation that no job is currently running (via `GET /api/data/jobs` or `logs/backend.log`), not
  a service action; nothing in this spec requires the operator to start, stop, or restart anything.
- Framework maintainer items, carried unchanged: `merge_ui_test_results.py` drops emphasised `**FAIL**`
  cells from the merged rollup — always score from the raw `.llm.md`. The `Frontend Present: no` →
  browser-qa-skip misrouting is routed around here via the explicit `Frontend Present: yes` field, not
  fixed at the source. `runs/goal-ops-hardening-iter-11/status.json`'s bookkeeping gap and the pre-existing
  `tests/test_db.py::test_create_all_produces_expected_tables` failure remain untouched (maintenance
  protocol: never patch `scripts/automation/*` from inside a product iteration).
