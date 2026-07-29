# Goal Iteration 32 — Bound `stock_obs`, the last unbounded accumulator inside `compute_forward_aggregates`

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 32
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — restructures `compute_forward_aggregates`'s shared per-observation accumulation
  architecture across four pure functions (`_group_means`'s six callers, `_group_mdd`, `_control_groups`,
  `_attribution_slices`) and lifts a frozen, test-pinned signature that nine direct-call unit tests assert —
  no single journey's browser test covers that interaction surface.
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08, J-09
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
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars
    > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from
    the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader
    pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing
    consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary,
    honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads
    are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may be
    introduced without an explicit goal.md amendment. *(critical)*
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

Stop `compute_forward_aggregates` — J-07's own named canonical producer — from holding one full
per-observation dict per `(run_id, ticker)` pair across an entire horizon's ~771K-800K live observations
at once (`stock_obs.append`, `forward_testing.py:988`, the literal frame of this session's original
production `MemoryError`), so the forward-aggregate warm and its two serving call sites stop scaling with
the crash dimension.

## BACKGROUND

This is the FIRST blocking item named by the iter-31 evaluator, deferred three iterations running: iter-29
bounded a sibling accumulator in `research.py`, iter-30 bounded `compute_forward_aggregates`'s OWN
`ret_by_run_symbol`/`mdd_by_run_symbol` join dicts (to `bm_returns`, a benchmark-only subset) but explicitly
left `stock_obs` unbounded, and iter-31 bounded the Factor-Lab-all `pools[h]` return value — each iteration
deliberately confined to ONE risky change (rule 5). `stock_obs` is the one accumulator left standing between
J-07 and its own acceptance clause ("no unbounded whole-table ORM materialization remains on the warm or
serving path... chunked into bounded accumulators"). Two binding lessons from this exact function family
drive this iteration's design: (iter-30) "a memory bound can be real, measured, byte-identical — and still
leave the crash in place, because it bounded the containers NEXT TO the failing allocation rather than the
allocation itself... name the exact frame from the traceback and require the plan to bound THAT"; (iter-31)
"a memory 'bound' can be a constant-factor win wearing a bound's clothes... ask of any memory-bound claim:
which term did it remove, and would the test fail if the fix were reverted?" Both rule out a
compact-encoding/columnar-storage-only fix for `stock_obs` (still O(N), just a smaller constant) — the same
critique already applied twice to this module. J-06's separate remaining gap (the `scripts/start-frontend.sh`
dev-vs-prod launcher decision + its real-browser TTI sweep) is a second, independently risky/cross-cutting
decision and is deliberately NOT bundled into this iteration (rule 5); it is next iteration's scope. This
decomposer also verified, rather than re-planned, the carried "stray `GET /research/factor-lab?all=true`
404" item: a codebase search of `apps/frontend` found no call site anywhere that constructs that unprefixed
URL (`lib/api.ts:1482` correctly calls `/api/research/factor-lab?all=true`) — the two log lines both prior
evaluators cite (`logs/backend.log:132550-132551`) are the SAME two lines, most likely a one-time
browser-navigation artifact from a single earlier QA session, not a recurring product defect; see OUT OF
SCOPE.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/forward_testing.py` — restructure `compute_forward_aggregates`'s per-observation
  accumulation so `stock_obs` no longer holds one full ~9-field dict per `(run_id, ticker)` pair across the
  WHOLE horizon-partition. Every consumer that only needs a GROUP-level statistic — `_group_means`'s six
  callers (`by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `by_pullback_to_rising_dma`,
  `by_flat_base_breakout`), `_group_mdd`, `_control_groups`'s per-run cohort sampling, and
  `_attribution_slices`'s `per_stock`/`by_sector`/`by_rank_band` slices — must be driven by state built
  incrementally inside the EXISTING per-chunk loop (`walk_forward.forward_agg_run_chunk`-sized slices,
  iter-30), bounded by the number of distinct groups/runs/tickers rather than by total observation count.
- [ ] `_control_groups`'s per-run RNG re-seed (`control_group.seed`) and its deterministic
  sorted-run/sorted-sector/sorted-pool draw order (the mechanism that makes its cohort sampling reproducible)
  must produce IDENTICAL `top_ranked`/`random_same_sector`/`spy`/`qqq`/`sector_etf` cohort output whether fed
  via the old full list or the new incrementally-built path — never a second RNG state, never a changed draw
  order (AG-5).
- [ ] `_attribution_slices`'s `distribution` slice (exact `median`/`dispersion`) is the ONE disclosed
  exception: it may keep a single list sized to the observation count, but of bare `float` return values
  only — never the current ~9-field dict — since an exact median/stdev fundamentally requires the full
  realized-return multiset (no O(1) exact streaming median exists; logged as an interpretation call,
  `assumptions.md` iter-32).
- [ ] `_attribution_slices`'s frozen, test-pinned `(stock_obs, cfg)` signature
  (`test_attribution_is_pure_over_passed_observations_no_new_query`) is lifted ON PURPOSE for this
  restructuring; every one of its nine existing direct-call unit tests in `apps/backend/tests/test_forward_testing.py`
  is updated to the new contract, none deleted, none weakened (same documented behaviors: empty-observations
  all-NA, single-observation null dispersion, config-derived rank-band padding, config-derived sector order).
- [ ] `compute_forward_aggregates`'s three existing call sites (`GET /api/backtest`, MCP `query_backtest`,
  the ingest finalize warm `_refresh_ingest_aggregates`) and `compute_run_scorecard`'s own separate,
  already-small per-run `stock_obs` (`forward_testing.py:1832`, bounded by one run's universe) stay
  byte-unchanged — this is a different accumulator inside the SAME producer, not a re-open of that function.
- [ ] Extend `apps/backend/tests/test_forward_testing_aggregates_streaming.py`'s existing
  `_reference_compute_forward_aggregates` byte-identity oracle to cover this restructuring (same pattern
  iter-30 used for the run-chunking dimension) — proves every returned key byte-identical to the pre-change
  reference for the same fixture inputs.
- [ ] Add a dedicated test proving the shipped bound holds at realistic scale, not just at a small fixture
  (mirrors `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`'s live-vs-fixture discipline,
  the binding iter-29 lesson): peak size attributable to the by-group/per-stock accumulation paths must not
  grow proportionally when total observation count grows at FIXED group/run/ticker cardinality — a test that
  would fail if the restructuring were reverted to the current full-list design.
- [ ] Live full-deep-basis forward-aggregate warm across all 5 configured `walk_forward.horizons` in one
  long-lived backend process (mirrors the iter-14/iter-30 measurement protocol): confirm zero `MemoryError`
  at this accumulation site and record the peak `VmPeak` + margin under `server.memory_cap_mb` in a new
  dated section of `reports/perf-budgets.md` (J-07 step 3, never done across 31 prior iterations).

### Frontend
None this iteration.

### New user-facing capability
None — this is an internal reliability fix. `/backtest` continues serving the same byte-identical evidence;
the change removes a crash-risk accumulator, it does not add a feature.

### New information displayed
None. `reports/perf-budgets.md` gains a new dated measurement section (an engineering artifact, not a UI
surface — matches this session's existing convention for VmPeak entries).

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible to the user. The forward-aggregate warm and `GET /api/backtest` / MCP `query_backtest` keep
serving identical figures; only the internal accumulation shape changes.

### Blueprint conformance
No new surfaces. J-07 keeps its existing cross-cutting home in `blueprint.md`'s Information Architecture —
Feature/journey homes table (global readiness badge + `/backtest`). `reports/perf-budgets.md` remains the
single canonical J-06/J-07 measurement artifact per the Data Contract's "Page performance budgets" row.

### Data-contract additions
None. `compute_forward_aggregates` stays the single canonical producer; its two serving endpoints
(`GET /api/backtest`, MCP `query_backtest`) and the ingest finalize warm trigger are unchanged — no second
producer, no second endpoint, no new field. `blueprint.md`'s "Regime score, market phase, realized
forward-returns" row and "Page performance budgets" row were both updated (additive Notes-cell iter-32
paragraphs, plus a new top-level "iter-32 update" narrative paragraph) to record this iteration's planned
change.

## OUT OF SCOPE

- J-06's `scripts/start-frontend.sh` dev-vs-prod launcher decision and its real-browser 11-page TTI sweep —
  a SEPARATE risky/cross-cutting decision (rule 5: never bundle two risky changes); next iteration's scope.
- `warmup.py:194` boot warm-up whole-table prefill (iter-29/b, carried, unchanged).
- `prices.py:141` ingest coverage refresh whole-table `daily_prices` prefill (iter-29/d, carried, unchanged).
- The Factor-Lab-all `pools[h]` 2.63x constant-factor residual (iter-31/e) — a separate, already-tracked
  finding; not reopened this iteration.
- J-07 step 4 (induce memory pressure via a test hook and assert an honest abort without a wedge) — the
  underlying isolation convention (per-item `MemoryError` catch-and-continue in `_refresh_ingest_aggregates`,
  iter-8) has strong first-hand live evidence across this session's real crashes (iter-29/30's own observed
  `stock_obs`/`research.py` MemoryErrors, in every case the process kept serving). A dedicated synthetic
  test-hook reproduction is a candidate for a future lean iteration, not required to close this iteration.
- The stray unprefixed `GET /research/factor-lab?all=true` 404 — investigated this iteration (see
  BACKGROUND); no reproducible call site found in `apps/frontend`. Not re-planned as product work without a
  fresh, reproducible browser-QA capture that pins an actual call site.
- `merge_ui_test_results.py`'s `_ROW_RE` framework bug — lives in
  `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`, outside this project's product code;
  framework-maintenance work, not a goal-mode iteration deliverable (flagged in NOTES for the human/framework
  maintainer — two consecutive evaluators have called it "MUST be fixed before any achievement run").
- `test_no_magic_numbers.py` red on `indicators.py`/`forward_testing.py`; UT-04's fresh-install DB fixture or
  a written waiver; `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches; audit B2
  (`_backfill`'s cross-call rollback residual) — all carried, unchanged, none touched this iteration.
- `GET /api/health`'s 0.127787s vs its ≤0.1s-at-rest budget — an owner-decision item, non-blocking, unchanged.
- `J-01/J-03/J-04-verify.png` byte-identity (11th recurrence) — a browser-qa capture-tooling issue, not
  product scope.

## DEFINITION OF DONE

- [ ] `stock_obs`'s per-group/per-run consumers (`_group_means`, `_group_mdd`, `_control_groups`,
  `_attribution_slices`'s `per_stock`/`by_sector`/`by_rank_band`) no longer scale with total observation
  count (TC-1)
- [ ] Restructured `compute_forward_aggregates` is byte-identical to the existing reference oracle for the
  same fixture inputs (TC-2)
- [ ] All nine `_attribution_slices` direct-call unit tests updated to the lifted-on-purpose contract, none
  weakened (TC-3)
- [ ] Live full-deep-basis warm shows zero `MemoryError` at this site and `GET /api/health` stays healthy
  throughout (TC-4)
- [ ] VmPeak + margin recorded in `reports/perf-budgets.md` under `server.memory_cap_mb` (J-07 step 3) (TC-5)
- [ ] `_control_groups`'s deterministic RNG cohort sampling is unchanged in output for the same seed/inputs
  (TC-6)
- [ ] `compute_run_scorecard`'s own separate per-run `stock_obs` stays byte-unchanged (TC-7)
- [ ] The evaluator re-derives (not inherits) the status of all four carried AG-8 findings, closing only the
  `stock_obs` one if TC-1/TC-4 hold (TC-8)
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) replay green (TC-9)
- [ ] J-07 evaluated via browser-qa-agent against its four acceptance steps
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-32-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (four acceptance steps: full warm, 1Hz health poll, VmPeak margin, memory-pressure
  isolation carve-out per OUT OF SCOPE); deterministic replay for J-01, J-03, J-04, J-05, J-08, J-09.
- Unit/integration: `apps/backend/tests/test_forward_testing.py` (all nine `_attribution_slices` direct-call
  tests), `apps/backend/tests/test_forward_testing_aggregates_streaming.py` (extended byte-identity oracle),
  a new live-basis-scale accumulator-size test, `_control_groups`'s existing RNG-reproducibility test(s),
  `compute_run_scorecard`'s existing tests (byte-unchanged confirmation).
- Error cases: a chunk whose slice produces zero observations for a group must still emit that group at
  n=0/mean=None where the existing `pad=True` contract requires it (unchanged NA discipline); an `as_of`
  cutoff that excludes all runs must still return the SAME all-NA/empty shape as today's `stock_obs=[]` case
  (`test_attribution_empty_observations_are_all_na`'s exact behavior, now reached via the new path).

Test-first contract:

- TC-1: given a synthetic fixture with a fixed small number of distinct groups/runs/tickers but observation
  count doubled, when `compute_forward_aggregates` runs for one horizon, then a tracemalloc-measured peak
  size attributable to the by-group/per-stock accumulation paths does not grow proportionally with the
  observation count (only the disclosed bare-`float` `distribution` list may still scale with N).
- TC-2: given the same fixture inputs `test_forward_testing_aggregates_streaming.py`'s existing
  `_reference_compute_forward_aggregates` oracle already uses, when the real (restructured)
  `compute_forward_aggregates` and the reference implementation both compute for the same `(horizon, as_of)`,
  then every top-level key (`by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `by_pullback_to_rising_dma`,
  `by_flat_base_breakout`, `control_group`, `attribution`, `overall`, `excess`) is byte-identical between the
  two.
- TC-3: given `_attribution_slices`'s nine existing direct-call unit tests in `test_forward_testing.py`, when
  this iteration lifts the frozen `(stock_obs, cfg)` signature on purpose, then every one of those nine tests
  is updated to the new contract and still asserts its documented behavior — none deleted, none weakened.
- TC-4: given a live full-deep-basis forward-aggregate warm across all 5 configured `walk_forward.horizons`
  in one long-lived backend process, when the warm runs to completion, then `grep -c MemoryError` on
  `logs/backend.log` from this run's own boot-banner line forward is 0, and `GET /api/health` polled at 1 Hz
  throughout answers HTTP 200 within its existing budget for every poll.
- TC-5: given that same live warm, when it completes, then the process's peak `VmPeak` (sampled from
  `/proc/<pid>/status` at ≥1 Hz) is recorded with its margin under the 6144 MB `server.memory_cap_mb` cap in
  a new dated section of `reports/perf-budgets.md`.
- TC-6: given `_control_groups`'s existing per-run RNG-sampling reproducibility (deterministic re-seed from
  `control_group.seed`), when the per-run cohort sampling is driven by the restructured incremental path
  instead of one full materialized list, then the `top_ranked`/`random_same_sector`/`spy`/`qqq`/`sector_etf`
  cohort `mean_return`/`n` figures are identical to the pre-change output for the same seed/config/fixture
  inputs.
- TC-7: given `compute_run_scorecard`'s own separate, already-small per-run `stock_obs` builder
  (`forward_testing.py:1832`), when this iteration ships, then that function's source lines and its existing
  tests are byte-unchanged (confirmed by diff).
- TC-8: given the four carried AG-8 findings (iter-29/b `warmup.py:194`, iter-29/c the `stock_obs` finding
  this iteration targets, iter-29/d `prices.py:141`, iter-31/e the Factor-Lab-all constant-factor residual),
  when the evaluator re-derives each finding's status read-only, then iter-29/c is marked `resolved: true`
  only if TC-4's zero-MemoryError result and TC-1's scaling proof both hold, and the other three stay open,
  unresolved, unchanged.
- TC-9: given the six passing journeys (J-01, J-03, J-04, J-05, J-08, J-09), when their deterministic golden
  replay scripts run against this iteration's build, then all six PASS with zero FAIL rows and zero
  reconciliation overturns.

## NOTES

- Lessons directly load-bearing for this iteration's design: iter-30 ("name the exact frame from the
  traceback and require the plan to bound THAT") and iter-31 ("a memory bound can be a constant-factor win
  wearing a bound's clothes... ask which term it removed, and whether the test would fail if the fix were
  reverted") — both rule out a compact-encoding/columnar-only fix for `stock_obs`; this spec requires a
  genuine per-group/per-run streaming restructure for every consumer except the one mathematically-forced
  exception (exact median/dispersion).
- Escalation flag for the human/framework maintainer (not this session's product scope): two consecutive
  evaluators (iter-30, iter-31) state that `merge_ui_test_results.py`'s `_ROW_RE` (matches only `UT-`,
  silently drops `TC-`-prefixed rows and their FAIL headline) "MUST be fixed before any achievement run."
  This session is not near GOAL_ACHIEVED (J-06/J-07 partial, four AG-8 findings open), so there is time, but
  it should not be forgotten before any future confirm-achievement pass.
- If the RNG-order-preservation constraint on `_control_groups` (TC-6) proves materially harder than the
  group-by restructuring within this iteration's budget, the developer should say so plainly in the dev
  handoff (mirroring this session's established honest-disclosure convention) rather than silently reverting
  `_control_groups` to a full-list read — the evaluator will score whatever actually ships.
- Assumption logged to `runs/goal-session-ops-hardening/state/assumptions.md` (iter-32): what "bounded
  accumulator" means for a slice (`distribution`) whose exact computation fundamentally requires O(N)
  access to the full value multiset.
