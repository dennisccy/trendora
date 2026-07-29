# Goal Iteration 31 — Bound Factor Lab's returned per-horizon pools + single-flight guard `factor_lab_all_cached` (AG-8 finding (a), deferred twice)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 31
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the fix restructures `app.engine.research`'s shared
  Factor-Lab-all computation chain (`_all_factor_observations_by_horizon` → `compute_factor_lab_all` →
  `factor_lab_all_cached`), consumed by two independent modules whose byte-identity is not covered by any
  single journey's own tests (`app.api.research`'s `GET /research/factor-lab?all=true` route AND
  `app.mcp.tools`'s MCP tool, both calling `factor_lab_all_cached` directly) — while preserving an existing
  tested architectural invariant (`test_all_factors_fires_one_shared_pool_read_not_n`: ONE shared read
  serves every factor at every horizon, never N re-reads), which rules out the naive "re-read per horizon"
  fix and requires a genuine memory-representation redesign proven byte-identical across every
  `(factor, horizon, decile)` tuple for two independent callers.
- **Frontend Present:** no
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08, J-09
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

`/research/factor-lab`'s all-factors view stops crashing with `MemoryError` and stops risking a wasted
duplicate compute under concurrent load — closing the session's oldest still-open critical AG-8 finding.

## BACKGROUND

Iter-29 and iter-30 both surfaced and then deferred the SAME live, 100%-reproducible finding: opening
`/research/factor-lab` raises `MemoryError` at `research.py:583` (`pools[h].append`) inside
`_all_factor_observations_by_horizon`. That function's OWN join accumulator was already bounded at
iter-29 (chunked by `research.factor_join_run_chunk`, proven on the live run count), but its RETURN
VALUE — `pools[h]`, one list per configured horizon, all five held resident simultaneously so
`compute_factor_lab_all` can derive every factor's deciles — is explicitly documented as "NOT bounded
here (deliberate)" at ~771,129 observations × 5 horizons on the live basis (iter-30 `eval.md`, iter-30
`iteration-state.md` blocker "dev, FIRST"). The iter-30 evaluator named this "deferred twice already" and
made it the FIRST blocking item for this iteration; the auditor separately found (B5) that
`factor_lab_all_cached`'s cache-MISS path has NO single-flight de-dup — a concurrent duplicate compute of
the same identity was observed completing while another was still in flight, wasting exactly the memory
headroom this fix is trying to create. Per the session's own rule-5 discipline (never bundle two risky
changes), this iteration takes ONLY this one finding — the SEPARATE `stock_obs` (`forward_testing.py:988`)
bound, `warmup.py:194`, and `prices.py:141` deferrals stay carried, unchanged, their own future iterations
(iteration-state.md "Active blockers"). Lesson applied (iter-29, iter-30 second entry): a memory bound
must be proven against the REAL live basis, not a fixture-sized reproduction, and must be shown to bind
the ACTUAL frame the traceback names — an "unbounded by design return shape" is the bug, not an
acceptable disclosed gap. `_factor_observations`/`_runs_with_fr`/`_fr_slice_map` (the single-factor path
that already serves `/evidence`'s drawdown expectations and is evaluator-confirmed fixed) are BYTE-FROZEN
this iteration — they share the `_runs_with_fr` helper with the function this iteration touches, but the
fix must not alter their behavior.

## IN SCOPE

### Backend
- [ ] Restructure `_all_factor_observations_by_horizon` / `compute_factor_lab_all`
      (`apps/backend/app/engine/research.py`) so that the Factor-Lab-all view's peak resident memory for
      its returned per-horizon observation pools no longer scales with holding all 5 configured horizons'
      full pools simultaneously — bound the memory footprint of the RETURN VALUE itself (the frame the
      live traceback names, `research.py:583`), not merely the join accumulator (already bounded at
      iter-29). The existing "ONE shared read serves every factor at every horizon" property
      (`test_all_factors_fires_one_shared_pool_read_not_n`) MUST be preserved — do not fix this by
      re-reading `ScannerResult` once per horizon. Byte-identical output required for every
      `(factor, horizon, decile)` tuple, both callers (`GET /research/factor-lab?all=true`,
      MCP `query_factor_lab_all`-equivalent tool in `app.mcp.tools`).
- [ ] Add an in-process single-flight de-dup guard to `factor_lab_all_cached`'s cache-MISS path
      (`apps/backend/app/engine/research.py`), mirroring the existing `data_manager.compute_coverage`
      per-key-lock + in-flight-event idiom (never invent a new abstraction) — audit B5's finding (a
      concurrent duplicate compute of the SAME `(asof_key, dataset_version+schema_token)` identity ran
      while another was already in flight and about to write the same row) must not recur. A waiting
      caller that times out on a bounded wait falls back to an independent compute (never a hang),
      mirroring `forward_aggregates_cached`'s iter-15 failure-path convention.
- [ ] `_factor_observations`, `_runs_with_fr`, `_fr_slice_map` (the single-factor path serving
      `/evidence`'s drawdown expectations and the single-factor Factor Lab view, evaluator-confirmed fixed
      at iter-29) stay byte-frozen — read-only reuse of `_runs_with_fr` is fine; no behavior change.
      `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and
      `ensure_historical_forward_aggregates_dispatched` (`forward_testing.py`) also stay byte-frozen — a
      different module's accumulators, not this iteration's scope (iteration-state.md "Do not redo").
- [ ] Add or extend a unit test that measures the new bound against the SHIPPED (real `config.yaml`, not a
      test-only override) run/observation count — mirroring
      `test_shared_pool_accumulator_is_chunk_bounded_at_the_shipped_config`'s existing convention but
      asserting the RETURN VALUE's peak resident size, not the join accumulator's.
- [ ] Add a fixture-backed byte-identity test proving the restructured `pools`/`compute_factor_lab_all`
      output is unchanged for every `(factor, horizon, decile)` combination, all-history and an `as_of`
      window (extends the existing `test_shared_pools_chunked_equal_the_pinned_unchunked_reference` /
      `test_all_horizons_per_factor_is_byte_identical_to_compute_factor_lab` oracle pattern).
- [ ] Add a unit test proving the single-flight guard: N concurrent MISS callers for the SAME identity
      trigger exactly ONE real `compute_factor_lab_all` invocation (instrumented counter, mirrors
      `data_manager`'s J-100 single-flight test convention), plus a dedicated failure-path test proving a
      waiting caller never hangs when the owner computation raises.
- [ ] Dev handoff records the ACTUAL measured peak memory (traced peak and/or `VmPeak`) of one full
      `/research/factor-lab?all=true` cold-MISS compute against the live deep basis, compared to
      `server.memory_cap_mb` (6144 MB), with the margin stated plainly — honestly, even if the margin is
      thin (do not round a thin margin to "fixed").

### Frontend
- None — no UI file changes; the Factor Lab page's existing decile table / rank-IC rendering is unchanged,
  it simply stops receiving a 500.

### New user-facing capability
`/research/factor-lab`'s all-factors view (decile table + rank-IC figures, every catalog factor, every
configured horizon) loads successfully instead of crashing — no new capability, an existing one becomes
reliably available.

### New information displayed
None — the decile table and rank-IC figures already exist in the response shape; this iteration fixes
availability and concurrency-safety, not shape or correctness.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change when the page already worked; on the (previously 100%-reproducible) crash path, the
page now renders instead of showing a contained "Backend unavailable" error box.

### Blueprint conformance
No new page/nav — `/research/factor-lab` already has its home under the existing "Research" nav section
(Information Architecture, `state/blueprint.md`). This iteration is a backend-only availability/
memory-safety fix to an existing legacy display value with no dedicated Data Contract row (established at
iter-29: "a legacy consumer with no Data Contract row of its own since its OWN displayed values are
unchanged by this fix"). `state/blueprint.md` gets an additive iter-31 documentation paragraph only — no
Information Architecture change, no reapproval request.

### Data-contract additions
None. The Factor-Lab-all view's `factors_table` shape, values, and derivation are unchanged (same
computing module `app.engine.research`, same two callers) — this fix changes memory representation and
concurrency handling only, never the served values.

## OUT OF SCOPE

- `stock_obs` (`forward_testing.py:988`), `warmup.py:194`'s boot warm-up MemoryError, and
  `prices.py:141`'s whole-table `daily_prices` coverage-refresh prefill — all three deliberately deferred
  (rule 5: one risky change per iteration); carried in iteration-state.md's "Active blockers."
- Adding `factor_lab_all_cached` to the ingest-time `research_hot_keys` warm (it is currently lazy-only,
  unlike `event_study_cached`'s default-key warm) — a genuine follow-on improvement, not required to
  close AG-8 (which forbids crashing/exhausting memory, not lazy-warm timing); not attempted here.
- `J-06.json`'s deterministic-replay artifact gap and the real-browser 11-page TTI sweep — capture-only
  passenger tasks (see TESTING REQUIREMENTS), never this iteration's own goal (rule 7).
- `merge_ui_test_results.py`'s `_ROW_RE` framework bug (matches only `UT-`, drops `TC-`-prefixed rows) —
  a pipeline/framework file, not product code; flagged again in NOTES for owner/framework-maintenance
  action, not developer scope.
- Any change to `docs/goal.md`, `readiness.py`/`compute_preflight`'s state machine, or the
  `GET /api/health` budget amendment — untouched, owner-owned.
- Widening this fix's pattern to `_combination_observations` / `_event_study_members` (named deferred
  siblings, same theoretical risk, unproven) — stays a non-blocking follow-up per iter-29's own scoping.

## DEFINITION OF DONE

- [ ] `/research/factor-lab` (all-factors view, `?all=true`) opened in a real browser on a verifiably idle
      host: HTTP 200, decile table + rank-IC figures render real numeric values for every catalog factor
      at every configured horizon, zero console errors — captured by browser-qa-agent with a real
      screenshot (not byte-identical to a prior unrelated capture).
- [ ] Zero `MemoryError` with a `research.py` frame in `logs/backend.log` across that request and a
      repeat/concurrent-load spot-check, counted from THIS run's own boot banner line number (cited
      explicitly in the QA report — iter-30's next-step item 5).
- [ ] The single-flight guard is proven live or by test: no concurrent duplicate `compute_factor_lab_all`
      invocation for the same identity (audit B5's finding does not recur).
- [ ] `compute_factor_lab_all`'s output is byte-identical to the pre-iteration reference for every
      `(factor, horizon, decile)` tuple (fixture-backed equality test, all-history and an `as_of` window).
- [ ] The shipped memory bound is proven against the REAL live run/observation count (not a fixture-sized
      width) by a dedicated unit test — mirrors the iter-29 lesson on shipped-vs-fixture proof.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green (deterministic
      replay + LLM fallback where no golden exists).
- [ ] `_factor_observations` / `_runs_with_fr` / `_fr_slice_map`'s existing tests
      (incl. `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`) pass unmodified —
      proof of no regression to the Evidence page's already-confirmed AG-8 fix.
- [ ] No anti-goal violation introduced; AG-8 finding (a) (the Factor Lab crash) is resolved — or, if the
      live measurement shows the margin against `server.memory_cap_mb` is thin, honestly recorded as such
      with the actual measured figures (never silently rounded to "fixed" — iter-30's own precedent).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-31-dev.md`, stating the measured peak
      memory and margin plainly.

## TESTING REQUIREMENTS

- Browser: J-06, J-07 (via the Factor Lab spot-check below, plus the required-still-passing set's
  standard replay). Ride-along, capture-only, never the iteration's own goal (rule 7): (a) run
  `J-06.json` through the deterministic replay lane and confirm a discoverable PASS/FAIL results artifact
  exists (no artifact has existed for this row since iter-28 per iter-30's finding); (b) if time
  permits, run the real-browser 11-page TTI sweep J-06 step 1 still needs. Neither (a) nor (b) is a
  blocking DoD item for this iteration.
- QA evidence-quality requirement: whenever the browser-QA report claims "N MemoryError" or "zero
  MemoryError" over any log window, it MUST cite the exact boot-banner line number in
  `logs/backend.log` it counted from (iter-30's next-step item 5 — a prior run's identical claim was
  disproved by an evaluator who counted from a different, correct boundary).
- Unit/integration: `apps/backend/tests/test_factor_lab_all.py` gains the new bounded-return-value test,
  the byte-identity extension, and the single-flight tests named in IN SCOPE. `test_research_streaming.py`
  and the existing `_factor_observations` chunk-bound test are re-run unmodified as a regression guard.
- Error cases: a `factor_lab_all_cached` compute failure (e.g. a simulated exception during the owner's
  compute) must not leave a waiting caller hung — the dedicated failure-path test asserts a bounded wait
  followed by an independent fallback compute, never a deadlock.

Test-first contract scenarios:

- TC-1: given a warm backend process serving the full live deep basis under the `server.memory_cap_mb`
  ulimit, with no `EventStudyCache` row yet for the current `(__all_factors__, factors_table, asof_key,
  dataset_version+schema_token, default_horizon)` identity (a genuine cold cache MISS), when a real
  browser navigates to `/research/factor-lab` and its `?all=true` request fires, then the response is
  HTTP 200, the decile table and rank-IC figures render real numeric values for every catalog factor at
  every configured horizon, and zero console errors are logged.
- TC-2: given THIS run's boot banner line number in `logs/backend.log`, when the request in TC-1 (plus
  one repeat/concurrent-load request) completes, then a count of lines after that boot banner containing
  a `research.py` frame and `MemoryError` is exactly 0, and the QA report states the boot banner line
  number it counted from.
- TC-3: given TWO concurrent requests for the SAME Factor-Lab-all cache identity on a cold MISS, when
  both reach `factor_lab_all_cached` at the same time, then exactly ONE real `compute_factor_lab_all`
  invocation executes (an instrumented counter in a unit test proves this), the second caller returns the
  SAME payload without itself invoking the compute, and neither caller raises or hangs.
- TC-4: given the single-flight owner computation raises a simulated exception, when a waiting caller's
  bounded wait elapses, then that caller falls back to an independent compute and returns a result — a
  dedicated unit test asserts no deadlock and no unbounded wait.
- TC-5: given a fixture DB with a small number of `ScannerResult`/`ForwardReturn` rows, when the
  restructured `compute_factor_lab_all` runs for all-history and for an `as_of` window that splits the
  fixture's runs, then every `(factor, horizon, decile)` output value is byte-identical to the pinned
  pre-iteration reference (existing oracle pattern, extended).
- TC-6: given the SHIPPED `config.yaml` (no fixture override) and a fixture sized to require real
  chunking of the new bound, when `_all_factor_observations_by_horizon` runs, then a dedicated unit test
  observes the peak resident size of the returned pools structure and asserts it is bounded — proven
  against the real run count, not a fixture-sized width (mirrors the iter-29 shipped-vs-fixture lesson).
- TC-7: given `_factor_observations`'s existing byte-identity and shipped-chunk-bound tests
  (`test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis` and neighbors), when this
  iteration's test suite runs, then those tests pass UNMODIFIED — proof the Evidence-page AG-8 fix
  (iter-29, evaluator-confirmed) is untouched.
- TC-8: given the required-still-passing journeys' golden scripts, when the deterministic replay lane
  runs J-01, J-03, J-04, J-05, J-08, J-09 against this iteration's build, then all six PASS with zero
  FAIL rows and zero reconciliation overturns.
- TC-9 (ride-along, capture-only, not a blocking DoD item): given `journey-scripts/J-06.json`, when it is
  run through the deterministic replay lane, then a discoverable results artifact (file path stated in
  the QA/audit report) records a PASS or FAIL row for it — closing the "no artifact exists" gap named at
  iter-30, whichever the outcome.

## NOTES

- Framework nit, carried, not this iteration's scope: `merge_ui_test_results.py`'s `_ROW_RE` matches only
  `UT-`-prefixed test ids and silently drops `TC-`-prefixed rows (and their FAIL headline) from the
  canonical merged `ui-test-results.md` — iter-30's evaluator called this "must be fixed before any
  achievement run." This is a pipeline/framework file, not product code; flagging again for an
  owner/framework-maintenance action outside this goal loop, per the maintenance protocol.
- Framework nit, 10th+ recurrence: `J-01`/`J-03`/`J-04-verify.png` have repeatedly been byte-identical
  across iterations (md5 collisions), meaning some of these journeys have gone without an independent
  visual capture for many runs. Not a code fix; browser-qa-agent should verify each required journey's
  screenshot is a genuinely fresh, distinct capture this run (fresh navigation, no cached frame reuse).
- OWNER, non-blocking, unchanged: `GET /api/health` measured 0.127787s vs its ≤0.1s steady-state budget —
  until amended, J-06 step 2 and J-07 step 2 can never both read true. No agent fix exists; carried.
- OWNER, non-blocking, unchanged: the historical `/backtest` first-touch latency (last measured 206s/273s)
  has no written budget; backlog card B-1107 stays optional.
- Carried, unchanged, own future iterations: audit B2 (`_backfill`'s cross-call rollback residual);
  `test_no_magic_numbers.py` red on unrelated files (`indicators.py`, `forward_testing.py`); UT-04's
  fresh-install DB fixture or a written waiver; retarget `test_forward_testing_serving_split.py`'s four
  `is_latest` monkeypatches before removing the dangling imports at `backtest.py:75` / `mcp/tools.py:38`.
- Consumed backfill/as-of dates this session (do not re-trigger a background-compute window on these):
  2005-04-05..11, 2011-03-10, 2015-09-09, 2018-02-15, 2018-03-15, 2022-04-12, 2026-05-02..29.
- Never re-trigger live memory pressure beyond what this iteration's own TC-1/TC-2 spot-check requires;
  never run the full test suite or two concurrent pytest processes (`test_readiness.py -k drift` pulls
  the 30-year `loaded_engine` fixture — 1h37m, not fixture-free, per the iter-28 lesson).
