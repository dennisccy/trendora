# goal-ops-hardening-iter-36 Execution Plan

## Context check
This is a re-dispatch: iter-35 wrote the same-scoped full-depth spec but was mis-dispatched at
`evidence` depth (no code required by its DoD, so nothing built) plus a NEW small finding
(iter-35/k, `/api/evidence` serving-path MemoryError). Per the phase spec's binding "Do not redo,"
this plan executes that unchanged scope — it does not re-plan or reinterpret it. Current tree is
verified clean/byte-identical to iter-34 (`git log`/`git diff` checked): no prior partial work
exists to build on; this is a from-scratch implementation.

## What to Build

**Backend — three independent bounded-memory fixes, each preserving byte-identical output:**
1. Bound `_membership_timeline`'s candidate-pool bar loading (`data_manager.py:497-544`) — replace
   the current call to `prefilled_bar_cache(session, expected_symbols=pool_symbols)` (which loads
   EVERY symbol's full series in one unbounded streamed query regardless of `expected_symbols` —
   see `prices.py:91-162` `_BarCache.prefill`) with a batched-by-symbol loading path so peak
   resident bar data scales with a configured batch width, not the full ~590-symbol × 30-year
   product. Must preserve `_BarCache`'s `_prefilled` load-once/re-entrancy guard, `trailing_count`'s
   byte-identity, and every other `prefilled_bar_cache`/`bars_asof`/`bars_after` consumer
   (scoring/regime/sector) — no signature change to any existing caller, no second cache instance,
   no second Coverage-payload producer (`_compute_coverage_uncached`, `data_manager.py:780`, calls
   `_membership_timeline` on a miss via `membership_timeline_cached`).
2. Bound `compute_drawdown_expectations`'s `stored_by_key` `ForwardReturn` read
   (`forward_testing.py:2320-2327`, currently `session.exec(fr_stmt).all()`) to a chunked/streamed
   read — same idiom as `_BarCache.prefill`'s `yield_per` fix and `research.py`'s iter-29
   `_factor_observations` fix. Same canonical module, same `EventStudyCache`-backed cache
   (`compute_drawdown_expectations_cached`), same endpoint (`GET /api/evidence` via
   `build_evidence_payload`, `evidence.py:116-191`) — no second producer, byte-identical payload.
   Do NOT touch `evidence.py`'s existing isolate-and-continue guard (lines 167-186, the
   `expectations_status: "unavailable"` MemoryError/Exception catch) — it must keep working
   unchanged; the fix only reduces how often it needs to fire.
3. New dedicated config key(s) for both bounds — do NOT reuse `research.read_batch_size` (a ROWS
   knob for `yield_per`) for the symbols-axis batch width; follow the established `ResearchCfg`
   idiom (`config.py:1338-1370`: `factor_join_run_chunk`, `factor_pool_max_observations`, each with
   its own unit, its own boot `>= 1` validation, its own doc comment naming why it's a different
   axis from its neighbors). Same idiom for the drawdown-expectations chunk width.

**Backend tests (new, permanent):**
- A `git show HEAD`-pinned reference-oracle test: pin the PRE-FIX `_membership_timeline` /
  `_compute_coverage_uncached` body verbatim via `git show HEAD:apps/backend/app/engine/
  data_manager.py` as a `_reference_*` helper (never an edited copy that also compiles against the
  new code — binding iter-32 lesson) and assert byte-identical `universe_count`, `per_symbol`,
  `membership_timeline`, `gaps`, `capacity` against the post-fix implementation on the live seed DB.
- A live-basis-proven, mutation-style batch-bound regression test for item 1: uses the REAL
  `config.universe.symbols` count / real seed DB (not a fixture-sized substitute), fails against a
  reverted/unbatched implementation, passes against the shipped one (ask "would this fail if the
  fix were reverted?" — binding iter-31 lesson).
- A parallel mutation-style regression test for item 2's chunked `stored_by_key` read, plus a
  byte-identical-payload assertion (extend `test_forward_testing.py` / `test_evidence.py` —
  precedent chunking patterns already exist in `test_forward_testing_streaming.py` /
  `test_forward_testing_aggregates_streaming.py`).
- Extend `test_bar_cache.py` / `test_data_manager.py` for the batched load; confirm no regression
  in existing `_BarCache`/`bars_asof`/`bars_after`/`trailing_count` suites, `test_data_manager_
  membership_cache.py`.
- Before/after peak-RSS/VmPeak measurement of `_membership_timeline` specifically (isolate the
  named call, not the whole process — binding iter-31/32 lesson), recorded in
  `reports/perf-budgets.md` as a new dated "Iteration 36" section.
- Reproduce the iter-35 live memory-pressure scenario (throwaway process, tightened
  `server.memory_cap_mb`, launched ONLY via `scripts/start-backend.sh` per AG-10) against both
  pre-fix and post-fix `compute_drawdown_expectations`; confirm the existing isolation guard still
  degrades honestly (HTTP 200, `expectations_status: "unavailable"`, never a 500/wedge) in whichever
  case still fails, and record the reduced failure rate/threshold in the dev handoff + perf-budgets.

**Frontend — mechanical wiring only, zero new logic:**
- Wire the already-generic, already-exported `resolveLabLoadPanel` (`apps/frontend/lib/lab-load-
  panel.ts`) into 4 sibling lab pages, matching `RegimeLabPage`'s proven pattern
  (`_labs.tsx:4221-4282`: `attempt` state + `useElapsedSeconds(state.kind === "loading")` +
  `resolveLabLoadPanel(state.kind, elapsedSeconds)` + `SlowComputeNotice` on `panel.kind ===
  "computing"` + `LabSkeleton` on `skeleton`/`computing` + `ResearchError ... onRetry={() =>
  setAttempt(p => p + 1)}` on `error`, with `attempt` added to the fetch effect's dependency array):
  - `FactorLabPage` (`_labs.tsx:262-318`) — currently `state.kind === "loading" ? <LabSkeleton /> :
    null`, `ResearchError` called WITHOUT `onRetry` (no retry today).
  - `PhaseSeverityLabPage` (`_labs.tsx:4529-4572`) — same bare pattern, no retry today.
  - `RegimePhaseFactorPage` (`_labs.tsx:4856-~5010`) — DIFFERENT shape than the other three: it uses
    a bespoke inline "Backend unavailable" error card (not `<ResearchError>`) and `CombinationSkeleton`
    (not `LabSkeleton`) at lines ~4988-5000. Wire the SAME computing/error/retry semantics into this
    page's existing markup shape — do not force it onto `ResearchError`/`LabSkeleton` if that breaks
    its established visual/test-id contract; add the Retry action to its existing inline error card.
  - `SeverityVelocityPage` — NOT inside `_labs.tsx`; it is its own component in
    `apps/frontend/app/research/severity-velocity/page.tsx` (currently `state.kind === "loading" ?
    <LabSkeleton /> : null`, `ResearchError` without retry). Import `resolveLabLoadPanel`/
    `useElapsedSeconds`/`SlowComputeNotice` from `_labs.tsx`'s existing exports the same way this
    file already imports `LabSkeleton`/`ResearchError`/etc.
- No change to `resolveLabLoadPanel`'s own resolution logic or `lab-load-panel.ts`/`lab-load-
  panel.test.ts` (already proven correct at iter-33, 13/13 tests) — wiring only.

## Agents Required
- backend-data: yes -- bound `_membership_timeline` candidate-pool loading (data_manager.py) and
  `compute_drawdown_expectations`'s `stored_by_key` read (forward_testing.py); new dedicated config
  keys; reference-oracle + mutation-style regression tests; VmPeak measurements in
  reports/perf-budgets.md; reproduced memory-pressure drill for the evidence-serving path.
- frontend-ux: yes -- wire `resolveLabLoadPanel` into 4 sibling research lab pages (mechanical,
  reusing iter-33's proven Regime Lab pattern).

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- bound `_membership_timeline`'s (lines 497-544)
  candidate-pool bar loading to config-driven batches instead of the unbounded
  `prefilled_bar_cache(expected_symbols=...)` whole-table prefill.
- `apps/backend/app/engine/prices.py` -- only if the batching mechanism needs a new `_BarCache`
  method/param (e.g. a batched-symbol prefill entry point); preserve `_prefilled` guard and every
  existing caller's signature unchanged.
- `apps/backend/app/engine/forward_testing.py` -- bound `compute_drawdown_expectations`'s (lines
  2270-2392) `stored_by_key` read (currently `session.exec(fr_stmt).all()` at ~line 2326) to a
  chunked/streamed read.
- `apps/backend/app/config.py` -- new dedicated `ResearchCfg` (or sibling) config key(s) for the
  symbols-axis membership-timeline batch width and the drawdown-expectations chunk width, each
  boot-validated `>= 1`, following the `factor_join_run_chunk`/`factor_pool_max_observations`
  idiom (lines ~1338-1370).
- `config.yaml` -- real values for the new config key(s).
- `apps/backend/tests/test_bar_cache.py`, `test_data_manager.py` -- extended coverage +
  membership-timeline tests for the batched load; the `git show HEAD`-pinned reference-oracle
  byte-identity test; the live-basis mutation-style batch-bound regression test.
- `apps/backend/tests/test_forward_testing.py`, `test_evidence.py` -- extended for the chunked
  `stored_by_key` read: byte-identical payload + mutation-style bound proof.
- `reports/perf-budgets.md` -- new dated "Iteration 36" section(s): before/after peak-RSS/VmPeak
  for `_membership_timeline`; the reproduced memory-pressure comparison for the drawdown-
  expectations serving-path fix.
- `apps/frontend/app/research/_labs.tsx` -- wire `resolveLabLoadPanel` into `FactorLabPage`,
  `PhaseSeverityLabPage`, `RegimePhaseFactorPage`.
- `apps/frontend/app/research/severity-velocity/page.tsx` -- wire `resolveLabLoadPanel` into
  `SeverityVelocityPage` (its own file, not inside `_labs.tsx`).
- `docs/handoffs/goal-ops-hardening-iter-36-dev.md` -- dev handoff (required by DoD).

## UI Evolution
- New user-facing capability: on the 4 sibling research labs (`/research/factor-lab`,
  `/research/phase-severity-lab`, `/research/regime-phase-factor`, `/research/severity-velocity`),
  a cold or slow load now shows a labelled "Still computing — Ns elapsed" card with a spinner
  instead of a bare unlabelled skeleton, and a genuine backend-unavailable state now shows a
  working Retry control — matching Regime Lab's existing behavior exactly.
- New information displayed: none (reuses Regime Lab's existing computing/error copy verbatim).
- New user actions: a working Retry button on each of the 4 sibling labs' error state (previously
  absent on all 4).
- UI surface changes: the loading/error panels inside `_labs.tsx`'s `FactorLabPage`,
  `PhaseSeverityLabPage`, `RegimePhaseFactorPage`, and `severity-velocity/page.tsx`'s
  `SeverityVelocityPage`. No visual change to `/evidence` (its NA-disclosure rendering is
  unchanged; only backend resilience under load improves) or to `/data`'s coverage panel (backend
  fix is internal-only, byte-identical payload required).
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse existing `LabSkeleton`, `SlowComputeNotice`, `ResearchError` (with
  `onRetry`) components verbatim — no new components. `RegimePhaseFactorPage` keeps its own
  `CombinationSkeleton` + inline error-card markup but gains the same computing/retry semantics.
- Layout: unchanged — this is a state-machine wiring change inside each page's existing pre-data
  render branch, not a layout change.
- Key visual effects: none new — inherits Regime Lab's already-shipped spinner + labelled-copy
  treatment.
- States to handle: skeleton (brief load) -> computing (past grace window, labelled + elapsed
  time) -> data, and error -> retry -> re-enters loading (never a second frozen error card). Must
  not regress the existing `WarmingState` (boot-not-ready) branch, which wraps all of this and is
  untouched.

## Key Test Scenarios
- TC-1/TC-2/TC-3 (backend): `_compute_coverage_uncached`/`_membership_timeline` peak-RSS measured
  before/after and recorded; `git show HEAD`-pinned reference-oracle byte-identical payload proof;
  live-basis mutation-style test fails reverted, passes shipped.
- TC-4 (backend, browser-qa): J-07's four steps re-verified — `/api/health` 200 throughout, VmPeak
  margin does not regress from iter-34's measured value, memory-pressure drill still aborts
  honestly with the process continuing to serve.
- TC-5/TC-6 (frontend, browser-qa): each of the 4 sibling labs cold-loads to the labelled
  "computing" card (never bare `LabSkeleton`); a backend-unavailable condition shows the retryable
  error card and clicking Retry re-enters loading (never a frozen error card) on all 4.
- TC-7 (regression): J-01, J-03, J-04, J-05, J-08, J-09 all PASS via deterministic golden replay,
  zero FAIL, zero reconciliation overturns.
- TC-8 (backend): a claim's `compute_drawdown_expectations` call under reproduced memory pressure
  returns HTTP 200 before and after the fix (never 500/wedge); pre-fix reproduces the abort with
  `expectations_status: "unavailable"`; post-fix serves the real panel or degrades identically
  honestly, with a measurably reduced failure rate recorded in the dev handoff.
- Error-case regressions (must not break): a candidate-pool symbol with zero `daily_prices` rows
  still resolves via an empty series, no crash; a `membership_timeline_cache` MISS mid-batch never
  leaves `_BarCache`'s registry partially initialized to a concurrent reader.

## Out of Scope (per phase spec, do not build)
- Regime Lab's cold `view=pooled` background dispatch / the intermittent HTTP-200-body
  "Internal Server Error" (iter-33/g).
- `warmup.py:194` readiness-badge wording after a permanently failed warm-up (iter-31/e, iter-32/f).
- The two owner-only decisions (iter-34/j `/api/health` budget disposition; iter-33/i whether
  `start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`) — do not resolve these as agent work.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched` — byte-frozen.
- Re-running J-07's full iter-34 memory-pressure drill from scratch — only re-verify against the
  new code paths.
- `_combination_observations` / `_event_study_members` (`research.py`) — named non-blocking
  follow-up only, not this iteration.
