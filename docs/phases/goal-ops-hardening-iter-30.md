# Goal Iteration 30 — Bound `compute_forward_aggregates`'s own accumulators (J-07's newest AG-8 finding) and close J-06's perf-budgets/replay gap

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 30
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — the fix bounds memory inside `compute_forward_aggregates`, the SINGLE canonical
  producer consumed by three call sites across three modules (`api/backtest.py`, `mcp/tools.py`,
  `data_manager.py`'s ingest finalize warm) and feeds five-plus internal aggregation helpers within
  `forward_testing.py` itself (`_group_means`, `_control_groups`, `_attribution_slices`, the VCP/pullback/
  breakout groupings) whose byte-identity is not covered by any single journey's own tests — a
  byte-identity-constrained refactor of shared architecture, not a single-surface fix. (Also matches the
  evaluator's own explicit iter-29 "Next-step recommendation: FULL depth.")
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

Close J-07's newest, most acute AG-8 finding by bounding the three unbounded in-RAM accumulators
inside `compute_forward_aggregates` itself — J-07's own named canonical producer, which raised a live
`MemoryError` during this session's own background forward-aggregate warm — and close J-06's one
remaining literal gap (an unwritten `reports/perf-budgets.md` edit plus an un-run deterministic
replay of `J-06.json`).

## BACKGROUND

The iter-29 evaluator re-derived every fact read-only and found that iter-29's Evidence-page fix
(`research.py`'s `_factor_observations`) is real and closed the session's oldest AG-8 finding — but the
SAME browser-QA/log window it audited also surfaced THREE new, previously-unseen live `MemoryError`s,
none in iter-29's own diff: `warmup.py:194` (boot warm-up), `forward_testing.py:965` inside
`compute_forward_aggregates` (the background forward-aggregate job), and `prices.py:141` (the ingest
coverage refresh's whole-table `daily_prices` prefill). Of these three, only the second sits directly
inside J-07's OWN acceptance clause — "no unbounded whole-table ORM materialization remains on the warm
or serving path (`forward_returns` / `scanner_results` read column-projected and/or chunked into bounded
accumulators — AG-8)" — and inside J-07's own named producer, `compute_forward_aggregates`. Per rule 5
(never bundle two risky journeys/changes in one iteration), this iteration takes ONLY that one: the
`warmup.py:194` boot-warm-up failure (ties J-04's honest-status surface — a "what should the badge say
when warm-up fails permanently" decision, not yet made) and the `prices.py:141` whole-table prefill
(ties J-05's coverage payload) are DELIBERATELY DEFERRED to a future iteration, named explicitly in OUT
OF SCOPE below.

Reading `apps/backend/app/engine/forward_testing.py:857-995` directly confirms the mechanism: iter-14's
AG-8 recovery already made the two SOURCE queries (`ForwardReturn`, `ScannerResult`) column-projected
and `yield_per`-streamed — but the three CONTAINERS every streamed row lands in
(`ret_by_run_symbol`/`mdd_by_run_symbol` dicts, `stock_obs` list, lines 920-982) are still unbounded:
every `(run_id, symbol)` observation across the WHOLE horizon-partition of `forward_returns` /
`scanner_results` accumulates in RAM before any grouping happens. This is the identical shape of bug
iter-29 fixed one function over in `research.py` — including iter-29's own hard lesson (lessons.md,
iter-29 first entry): a memory bound can ship green and bind nothing if it reuses an existing
ROWS-shaped config knob (`cfg.research.read_batch_size`) as a RUN-count chunk width against a live basis
of ~1,800-1,900 runs/horizon, producing exactly one chunk and 0% peak reduction. This iteration's fix
MUST use its own dedicated run-count knob and prove — against the REAL `load_config()` value on the REAL
live run count, not a fixture-sized width — that it actually chunks (iter-29's second binding lesson).

J-06 is `partial` for one purely mechanical, zero-code-risk reason: iter-29 measured this iteration's
own on-load latencies but never wrote them to the committed `reports/perf-budgets.md` (DoD item TC-8,
J-06 step 2), and `J-06.json` has not been run through the deterministic replay lane since it was fixed
at iter-28 (TC-10). Both close with no code change.

Coherence: iter-29's `coherence.md` verdict was COHERENCE-PASS (no blocking violations) — no
consolidation pass required. Its one advisory (the blueprint's iter-29 `[TARGET]` tag lagging the
evaluator's confirmation) is fixed by this spec's own blueprint edit, made ahead of dispatch.

**Lesson applied (iter-29, both entries):** (1) any memory bound must be proven at the SHIPPED
`load_config()` value against the REAL basis, never a fixture-sized knob, and must use a dedicated
config key whose UNIT matches the new dimension (runs, not rows) — TC-3 below is written to enforce
this literally. (2) A golden script or merged results file can be silently weakened/overwritten to hide
a regression — TESTING REQUIREMENTS below requires the replay lane to diff `J-06.json` against its
prior committed version and requires browser-QA to cite the exact `logs/backend.log` boot line number
whenever it claims "zero MemoryError" (the iter-29 evaluator's own finding: a QA report claimed zero and
there were three).

## IN SCOPE

### Backend
- [ ] Bound `compute_forward_aggregates`'s (`apps/backend/app/engine/forward_testing.py:857-995`) three
      unbounded per-observation in-RAM containers — `ret_by_run_symbol`, `mdd_by_run_symbol` (dicts) and
      `stock_obs` (list) — so peak added memory no longer scales with the full horizon-partition of
      `forward_returns`/`scanner_results` (3.9M+/611K+ rows on the live basis). Restructure the downstream
      group-by aggregation this function feeds (`_group_means`, `_control_groups`, `_attribution_slices`,
      and the VCP/pullback/breakout groupings — all in `forward_testing.py`) so the SAME grouped output is
      produced from bounded, chunked/incremental accumulation rather than one unbounded observation list.
  - [ ] Gate the chunk width on a NEW, dedicated config knob (its own key, RUN-count unit — never reuse
        `cfg.research.read_batch_size`, a ROWS knob; iter-29's binding lesson on unit mismatch).
  - [ ] `compute_forward_aggregates` remains the SAME canonical producer at the SAME signature, called from
        the SAME three sites (`GET /api/backtest`, MCP `query_backtest`, the ingest finalize warm) — no
        second aggregation path, no schema change, no new field.
  - [ ] `resolved_forward_aggregate_evidence` and `ensure_historical_forward_aggregates_dispatched` stay
        byte-frozen (binding, iteration-state.md "Do not redo") — this fix is confined to
        `compute_forward_aggregates`'s own accumulators, not a re-open of the iter-16/17/20 serving split.
- [ ] Add a unit test asserting the SHIPPED config value (via `load_config()`, not a test fixture override)
      actually produces more than one chunk against the live/basis-scale run count for a representative
      horizon — mirrors iter-29's `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`.
- [ ] Add a fixture-backed equality test proving byte-identical output (every returned slice: `by_bucket`,
      `by_setup`, `by_regime`, `by_sector`, `by_rank_band`, `control_group`, `attribution`, VCP/pullback/
      breakout groupings, `excess`) between the pre-chunk and post-chunk implementation, for all 5
      configured horizons, with and without `as_of`.

### Frontend
None — this iteration is a backend memory-bound fix plus a measurement-artifact edit; no new or changed
UI surface.

### New user-facing capability
None new. The existing `/backtest` page and the ingest-time background forward-aggregate warm keep their
current behavior; the fix removes a live memory-exhaustion failure mode, it does not add a feature.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
The ingest-time forward-aggregate warm (all 5 horizons, full deep basis) completes without raising
`MemoryError`; `/backtest` and MCP `query_backtest` continue to serve byte-identical evidence. No visible
UI change.

### Blueprint conformance
No new page/nav/route. This iteration's backend fix is registered as an additive Notes-column append to
the EXISTING "Regime score, market phase, realized forward-returns" Data Contract row
(`runs/goal-session-ops-hardening/state/blueprint.md`, iter-30 note) — same computing module
(`app.engine.forward_testing`), same three call sites, no second producer. J-06's closure is registered
against the EXISTING "Page performance budgets" row (same file) — same artifact
(`reports/perf-budgets.md`), no second file. Both edits already made in `blueprint.md` ahead of dispatch,
alongside flipping iter-29's `[TARGET]` tag on the "Membership timeline / research hot-key caches" row to
BUILT + EVALUATOR-CONFIRMED (closing the iter-29 coherence advisory).

### Data-contract additions
None. `compute_forward_aggregates` keeps its exact registered computing module and serving endpoints; no
new field rides the `/api/backtest` / MCP `query_backtest` payload. `reports/perf-budgets.md` gains a new
dated section under its EXISTING single-artifact registration — not a new Data Contract row.

## OUT OF SCOPE

- `warmup.py:194`'s boot-warm-up `MemoryError` and the resulting permanently-stuck "Initializing…"
  readiness badge (ties J-04's honest-status surface) — a separate risky change; deferred per rule 5.
- `prices.py:141`'s whole-table `daily_prices` prefill inside the ingest coverage refresh's
  `_compute_coverage_uncached` path (ties J-05's coverage payload) — a separate risky change; deferred
  per rule 5.
- Audit B2 (`_backfill`'s cross-call rollback residual) — byte-frozen, its own iteration (iteration-state
  "Do not redo").
- UT-04's fresh-install DB fixture or an explicit written waiver.
- Retargeting `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches / removing the
  dangling imports at `backtest.py:75` / `mcp/tools.py:38` — investigated and deliberately left at
  iter-21, non-blocking.
- Any historical `/backtest` first-touch latency budget decision (owner, non-blocking, B-1107 optional).
- Whether `data_provider_runs` run 201's "coverage refreshed" disclosure is accurate given a same-window
  MemoryError in that refresh (owner, non-blocking).
- No new proven-language, evidence-claim, or referee-touching change (J-01–J-06 carry no Evidence Claims
  per goal.md's Loop mechanics; this iteration adds none either).

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent: the ingest-time forward-aggregate warm (all 5 configured
      horizons, full deep basis, in one long-lived process) completes with zero `MemoryError` carrying a
      `compute_forward_aggregates`/`stock_obs`/`ret_by_run_symbol` frame in `logs/backend.log`, and
      `GET /api/health` answers 200 throughout at 1 Hz.
- [ ] J-06 passes via browser-qa-agent: `reports/perf-budgets.md` carries a new dated section with this
      iteration's fresh 11-page real-browser TTI/on-load-latency sweep plus the ≤5s boot-to-health
      measurement, every reading scored against its committed budget; `J-06.json` runs through the
      deterministic replay lane with a PASS row and zero FAIL rows.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green (deterministic
      replay + LLM fallback where no golden exists).
- [ ] No anti-goal violation introduced; the one AG-8 finding this iteration targets is resolved (or, if
      the developer's live measurement shows it is not fully bound, honestly recorded as still-open with
      the actual measured figures — never silently rounded to "fixed").
- [ ] `compute_forward_aggregates`'s byte-identity to the pre-chunk implementation is proven by a
      fixture-backed equality test across every returned slice, all 5 horizons, with/without `as_of`.
- [ ] The shipped chunk-width config value is proven to actually chunk against the LIVE run count (not a
      fixture-sized width) by a dedicated unit test.
- [ ] `/research/factor-lab` (the Factor Lab page, sharing `app.engine.research`'s per-observation-join
      shape iter-29 fixed one function over — a same-pattern regression surface for this iteration's fix)
      is opened in a real browser on a verifiably idle host and its decile table + rank-IC figures render
      real numeric values, HTTP 200, zero console errors.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-30-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (full replay + fresh sweep), J-07 (ingest-time warm + health-poll liveness), plus a
  regression spot-check of `/research/factor-lab` (shares the accumulator-bounding pattern).
- Unit/integration: byte-identity fixture test for `compute_forward_aggregates` (all 5 horizons, with/
  without `as_of`); shipped-config-actually-chunks test against the live run count; existing
  `test_forward_testing.py` / `test_forward_testing_concurrency.py` / `test_forward_testing_serving_split.py`
  suites stay green unmodified in their assertions (no `is_latest` monkeypatch retargeting this iteration).
- Error cases: a chunk boundary that splits a run's observations across two chunks must not double-count
  or drop that run's contribution to any grouped mean; an empty chunk (a run with zero qualifying
  observations at this horizon) must not crash the merge step.

Test-first contract:

- TC-1: given the live DB's `forward_returns`/`scanner_results` tables (3.9M+/611K+ rows) and the ingest
  finalize warm triggering `compute_forward_aggregates` for every configured horizon in one long-lived
  backend process, when the warm runs to completion, then `logs/backend.log` for that run's window
  contains zero `MemoryError` lines carrying a `forward_testing.py` `compute_forward_aggregates` frame,
  and the run's `data_provider_runs` row lists `forward_aggregates` in `aggregates_refreshed` with no
  partial/failed status.
- TC-2: given a fixed fixture DB with a small, known pool, when `compute_forward_aggregates` runs before
  (git history) and after this iteration's change for all 5 configured horizons, with and without `as_of`,
  then the returned payload is byte-identical (deep-equal) across every slice: `by_bucket`, `by_setup`,
  `by_regime`, `by_sector`, `by_rank_band`, `control_group`, `attribution`, the VCP/pullback/breakout
  groupings, and `excess` (vs SPY, vs QQQ).
- TC-3: given the shipped, `load_config()`-resolved new run-chunk config value and the LIVE database's
  actual run count for a representative horizon (not a fixture-sized width), when the chunking loop runs,
  then it produces more than 1 chunk (a test asserts this against the real basis, per iter-29's binding
  lesson).
- TC-4: given `GET /api/health` polled at 1 Hz throughout the TC-1 warm, when every poll response is
  inspected, then 100% answer HTTP 200 within the existing committed budget — no frozen or unresponsive
  window.
- TC-5: given a verifiably idle host (`logs/backend.log` + `logs/hwmon/hwmon.csv` cross-checked, no
  concurrent ingest job) and a browser navigating to `/research/factor-lab`, when the page loads, then the
  decile table and rank-IC figures render populated real numeric values, HTTP 200, zero console errors,
  and zero blank/empty table cells.
- TC-6: given this iteration's fresh 11-page real-browser sweep plus the ≤5s boot-to-health measurement,
  when the developer appends a new dated section to `reports/perf-budgets.md`, then `git diff` for that
  file is non-empty for this iteration and every recorded reading is marked PASS/WARN against its
  committed budget (closing J-06 step 2 / DoD item TC-8).
- TC-7: given `runs/goal-session-ops-hardening/journey-scripts/J-06.json`, when the deterministic replay
  lane runs it via the demo-runner's verify mode, then the merged replay results file lists a J-06 row
  with PASS and zero FAIL rows (closing TC-10, literally unmet since iter-28).
- TC-8: given the required-still-passing set (J-01, J-03, J-04, J-05, J-08, J-09), when deterministic
  golden replay runs each, then every row is PASS with zero FAIL rows and zero reconciliation overturns.
- TC-9: given browser-QA asserts "zero MemoryError" for any window it inspected, when it writes its
  report, then the report cites the exact `logs/backend.log` line number of the boot banner it counted
  from (process-quality requirement; the iter-29 evaluator disproved an identical unqualified claim by
  finding three MemoryErrors the report missed).

## NOTES

- **Depth justification recap:** full, trigger 1 (structural — see Goal Mode Metadata). Consecutive lean
  iterations dispatched before this one = 2 (hardening cadence 6, not met) — that is not the basis; the
  structural blast radius across `api/backtest.py` / `mcp/tools.py` / `data_manager.py` (consumers) plus
  five-plus in-module aggregation helpers (all sharing this one function's byte-identity contract) is.
- **Target selection recap:** rule 3 (unblockers) — J-06/J-07 are the session's only two non-passing
  journeys; closing them is the direct path to GOAL_ACHIEVED eligibility (still contingent on any other
  anti-goal findings the evaluator surfaces). Rule 5 (never bundle two risky journeys) is why this
  iteration takes exactly ONE of the three new MemoryErrors iter-29 surfaced — the one inside J-07's own
  named producer and own acceptance-clause language — deferring the other two explicitly (OUT OF SCOPE).
- **If the developer's live measurement shows the accumulator bound does not fully eliminate the
  MemoryError** (e.g., a downstream helper still materializes a full-basis structure the plan above
  missed), do not silently patch around it or claim success on a partial fix — record the actual measured
  figures and let the evaluator score J-07 `partial`, consistent with this session's established honesty
  discipline (iter-28/29 lessons).
- **Do not re-open** `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`,
  J-08's serving split, the session-live demo JSON, or the owner's BCW budget amendment (all byte-frozen,
  iteration-state.md "Do not redo"). Do not re-trigger a live memory-pressure failure as a test technique;
  do not run the full test suite or two concurrent pytest processes (`test_readiness.py -k drift` pulls the
  30-year `loaded_engine` fixture, ~1h37m). Consumed historical dates, not "fresh": 2011-03-10, 2015-09-09,
  2018-02-15, 2018-03-15, 2022-04-12, 2026-05-02..29.
