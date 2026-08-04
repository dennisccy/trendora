# goal-ops-hardening-iter-47 Execution Plan

## Context read
`docs/goal.md` (ops-hardening session, J-01…J-09), `docs/phases/goal-ops-hardening-iter-47.md` (full spec,
already exhaustively detailed by the goal-decomposer — TC-1…TC-9 are load-bearing, treat them as the
authoritative acceptance contract, not this plan's paraphrase), the iter-46 dev handoff (3 passes: original +
QA-fix + audit-fix) and iter-46 audit (FAIL, findings B1-B5/T1-T4), and `state/assumptions.md`'s iter-47
decomposer entry (why J-06/J-07 over J-05 this round). No drift: this iteration is a direct continuation of
iter-46's audit "Recommended Next Step" items 2-4 (B2/B3/B4) plus the two carried logger sites — squarely
inside the session's "compute at ingest, serve from storage" hardening arc, no new capability, no scope
creep. J-05's old-day-insert case is a **deliberate, disclosed** exclusion (separate riskier subsystem,
documented in the spec's OUT OF SCOPE and in assumptions.md) — not an oversight to flag.

## What to Build
- Fix `GET /api/evidence`'s cache-key/staleness handling so an unrelated new `forward_returns` row never
  forces the page onto its ~163s cold-recompute tail (iter-46 audit B2). Two candidate paths, both
  explicitly sanctioned by the spec — the NOTES section states a preference:
  - **Path A (cache-key scoping)** — narrow `compute_drawdown_expectations_cached`'s invalidation
    (`forward_testing.py:2475`, `version = _dataset_version(session)`) so it keys on data relevant to the
    claim's own cohort, not the global `f{count(forward_returns)}` in `_dataset_version`
    (`research.py:1705-1720`). No frontend change; no new `expectations_status` value.
  - **Path B (serve-stale-behind-a-label)** — keep the current cache miss on ANY dataset-version change,
    but on a miss serve the previous generation's payload immediately while a background re-warm runs, and
    add `expectations_status: "refreshing"` to the affected claim row(s) (mirrors the ALREADY-REGISTERED
    `"unavailable"` sibling value at `evidence.py`'s per-claim loop, ~line 164-176, and the neighboring
    `/backtest` `evidence_status: "ready"|"refreshing"|"not_yet_computed"` pattern,
    `apps/frontend/app/backtest/page.tsx:232-312`). Requires a frontend change (see below).
  - **The spec's own NOTES recommend Path B** if Path A proves materially riskier/slower to prove
    byte-identical — Path B has a direct precedent and degrades honestly by construction. Investigate Path
    A first (it is the smaller diff and needs no frontend change); fall back to Path B if the cohort-scoped
    key cannot be proven byte-identical quickly. Whichever path is taken, `GET /api/evidence` must answer
    within ≤1.5s endpoint / ≤3s page (`reports/perf-budgets.md` Item I) after one new `forward_returns` row
    lands, both idle and under concurrent load (TC-1, TC-2, TC-3).
- Bound the third unbounded whole-cohort site on the SAME serving path: `apps/backend/app/engine/
  samples.py:145` (`observations = _factor_observations(session, factor, horizon, as_of)`) and `:156`
  (`sorted(observations, key=...)` inside `_factor_samples`'s decile branch) — the site `logs/backend.log`
  caught `MemoryError`-ing at 02:20:31 on 2026-08-04, reached via `evidence.py` →
  `compute_drawdown_expectations_cached` → `compute_drawdown_expectations` → `compute_samples` →
  `_factor_samples` (iter-46 audit B3). **Important nuance for the developer to resolve, not prescribed
  here**: `_factor_samples`/`_factor_observations` is a DUAL-CONSUMER function — the `/api/research/samples`
  drill-down endpoint needs the actual per-observation row list for display, while
  `compute_drawdown_expectations`'s internal call only needs the AGGREGATE stats over that pool (the
  slice-and-discard convention iter-46 applied to `_combination_observations`/`compute_drawdown_expectations`
  folds each chunk into an accumulator and discards it — it does not apply cleanly to a function whose
  return value IS the row list some callers legitimately need). Byte-identical output is required for
  whichever consumer path is bounded; do not regress the drill-down endpoint's existing row-list contract.
- Add the snapshot-date filter to `_drawdown_ticker_slice_map` (`forward_testing.py:2270-2286`, extracted at
  iter-46) — narrows a 7,994,388-row `ForwardReturn` read (71 calls / 7 claims) to only the dates each
  claim's evaluation window needs (iter-46 audit B4, provably byte-identical — the surplus rows are never
  looked up). Measure and record the row-count reduction in the dev handoff (TC-5).
- Guard `warmup.py:205` and `:212` (both bare `logger.exception(...)` calls inside
  `_warm_drawdown_expectations`'s per-claim `MemoryError`/`Exception` handlers) with the existing
  `_log_isolation_failure` degrade-to-marker convention (`data_manager.py:3653`, already imported via
  `from app.engine import data_manager` at the top of `warmup.py`) — mirrors the 19+ other sites already
  converted at iter-44/45.
- Full re-verification of all 8 Must-have journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) via
  browser-qa-agent against the CURRENT build, each with its OWN dedicated evidence file/screenshot — no
  journey may borrow another's script or assert page-wide text a persisted panel already satisfies (binding
  iter-46 lesson: this cost the session's J-01/J-03 golden-replay a null-test finding and TC-9's
  screenshot-uniqueness rule has now been reopened three times). J-05 gets its FIRST dedicated live capture
  in 3 rounds this round (no code change targets it — verification only, expected outcome is still `failing`
  per assumptions.md's own honest prediction).
- **Sequencing constraint (binding iter-46 lesson, TC-7):** the browser-qa lane must be the LAST
  product-code-adjacent event before scoring. If a QA-fix or audit-fix pass lands ANY product code after
  browser-qa has run, the lane MUST be re-run before the iteration is scored — this is exactly the defect
  that silently voided iter-46's QA pass (T1: the browser lane there ran hours before `warmup.py`'s fix
  landed, and QA scored PASS anyway).
- **Memory-pressure proof discipline (binding iter-44 lesson, TC-4):** the new `samples.py` bound needs the
  SAME 5-consecutive-run pressure-test protocol already used for its siblings — a real subprocess induction
  under tightened `ulimit -v` (RLIMIT_AS), not a monkeypatch. Mirror
  `apps/backend/tests/test_evidence_drawdown_memory_pressure.py`'s established pattern (real DB copy,
  host-calibrated KB caps discriminating pinned-reference-unchunked-aborts vs shipped-chunked-completes,
  plus a STARVED_CAP proving honest degradation, not a crash/wedge).

## Agents Required
- developer: yes -- implements the backend fix cluster (Evidence cache-key/staleness path, samples.py
  bound + its 5-run pressure test, `_drawdown_ticker_slice_map` date filter, warmup.py logger guards) and,
  CONDITIONALLY on which cache fix path is chosen, a small frontend change (the `expectations_status:
  "refreshing"` label on `/evidence`'s claim card(s) — required ONLY if Path B is taken; not needed for
  Path A). Also runs the full 8-journey live re-verification per the phase spec's DEFINITION OF DONE.
- backend-data: yes (folded into the developer agent above — this framework instance uses a single
  `developer` agent for both backend and frontend work; no separate backend-data agent type exists in the
  agent catalog).
- frontend-ux: conditional (folded into the developer agent above) -- only if Path B (serve-stale-behind-
  a-label) is the fix chosen; Path A requires zero frontend change.

## Frontend Present
yes

(The metadata line in the phase spec itself reads "yes (conditional)" — marking `yes` here per the
orchestrator's own rule: browser-qa-agent MUST verify J-06/J-07 either way, and Path B, if taken, adds a
real user-visible label. Marking `no` would incorrectly skip the required Chrome MCP checks regardless of
which backend path ships.)

## Files to Create/Modify
- `apps/backend/app/engine/forward_testing.py` -- `compute_drawdown_expectations_cached` (~2461-2510,
  cache key at :2475) fixed per whichever path is chosen; `_drawdown_ticker_slice_map` (:2270-2286) gains
  the snapshot-date filter.
- `apps/backend/app/engine/samples.py` -- `_factor_samples` (:135-176, whole-history list at :145 / whole
  sort at :156) bounded; investigate whether `_factor_observations` itself (`research.py:226-`) needs the
  bound instead/also, given the dual-consumer nuance above.
- `apps/backend/app/engine/warmup.py` -- `_warm_drawdown_expectations` (:153-217): lines 205 and 212 switch
  from bare `logger.exception` to `data_manager._log_isolation_failure`.
- `apps/backend/app/engine/evidence.py` -- ONLY if Path B: `build_evidence_payload`'s per-claim loop
  (~140-183) adds `expectations_status: "refreshing"`/`"ready"` alongside the existing `"unavailable"` value.
- `apps/frontend/lib/evidence.ts` -- ONLY if Path B: extend the `expectations_status` type
  (currently `"unavailable"` only, :95) with `"ready" | "refreshing"`.
- `apps/frontend/app/evidence/page.tsx` -- ONLY if Path B: render the "recomputing" label on the affected
  claim card(s), reading the new field (mirror the existing `expectations_status === "unavailable"`
  handling at :251 and the `/backtest` `evidence_status` pattern).
- `apps/backend/tests/test_forward_testing.py` -- new tests for the cache-key/staleness fix (TC-2, TC-3
  byte-identity) and `_drawdown_ticker_slice_map`'s date filter (TC-5, byte-identity + row-count
  reduction).
- `apps/backend/tests/test_samples.py` or a new memory-pressure test file (TC-4: chunk-bounded size test +
  byte-identity test, mirroring iter-46's `test_research_streaming.py` pattern; PLUS a new 5-consecutive-run
  real-subprocess pressure test mirroring `test_evidence_drawdown_memory_pressure.py`).
- `apps/backend/tests/test_warmup.py` -- TC-6: two new unit tests asserting `warmup.py:205`/`:212` call
  `_log_isolation_failure` (not a bare `logger.exception`) on a textless `MemoryError` and a generic
  exception.
- `reports/perf-budgets.md` -- new dated item(s): TC-1/TC-2/TC-3 latency measurements (idle + concurrent),
  TC-4's 5-run pressure results, TC-5's row-count reduction, TC-9's VmPeak margin under J-07's concurrent
  scenario.
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json`, `J-07.json` -- update/verify anchors if the
  fix changes any displayed figure; all 8 journey scripts get a dedicated re-run this iteration.
- `docs/handoffs/goal-ops-hardening-iter-47-dev.md` -- required dev handoff (which path was taken and why,
  live TC-4/TC-9 drill results, honest reporting of any TC not met — this session's established convention
  per iter-45/46 handoffs, never round an unmet TC to a pass).

## UI Evolution
- New user-facing capability: none structurally — the Evidence page becomes reliably fast after any ingest;
  no new page/route/nav entry (spec's own "UI surface changes: None structurally").
- New information displayed: CONDITIONAL (Path B only) — a "recomputing" status label on the affected
  `/evidence` claim card(s) while a fresher generation warms in the background.
- New user actions: none.
- UI surface changes: none (existing `/evidence` claim cards gain, at most, a conditional status label).
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the EXISTING evidence-status badge/label pattern already on `/evidence`
  (`expectations_status === "unavailable"` handling, `apps/frontend/app/evidence/page.tsx:251`) and the
  `/backtest` `evidence_status` `"refreshing"` badge (`apps/frontend/app/backtest/page.tsx:232-312`) — same
  calm, factual, non-alarming visual treatment, no new component.
- Layout: no layout change — label is additive to the existing claim card, same position/pattern as the
  `"unavailable"` state.
- Key visual effects: none new — matches the existing evidence-status chip styling (calm, unmissable, never
  hype, per `docs/goal.md`'s Design Direction).
- States to handle: `ready` (unchanged rendering), `refreshing` (new, Path B only — label visible, values
  still the honest last-good generation, never mixed with a newer generation's fields per TC-3), and the
  pre-existing `unavailable` (unchanged).

## Key Test Scenarios
- TC-1/TC-2/TC-3: `GET /api/evidence` answers within ≤1.5s endpoint / ≤3s page after any new
  `forward_returns` row, idle AND under concurrent load; every claim panel byte-identical to the canonical
  computation (AG-3); if a stale generation is served, `expectations_status` reads `"refreshing"` — never
  silently stale.
- TC-4: `samples.py:145/156`'s bound survives 5 CONSECUTIVE real-subprocess memory-pressure runs with zero
  `MemoryError` escapes, byte-identical to a pinned pre-fix reference oracle (binding iter-44 lesson — one
  green run is not proof).
- TC-5: `_drawdown_ticker_slice_map`'s snapshot-date filter yields byte-identical `drawdown_expectations`
  values with a measured, recorded row-count reduction.
- TC-6: `warmup.py:205`/`:212` fire `_log_isolation_failure`, not a bare `logger.exception`, verified by
  dedicated unit tests for both lines.
- TC-7: no product code lands after browser-qa runs without triggering a mandatory re-run before scoring
  (verify via file-mtime vs results-file-timestamp comparison).
- TC-8: all 8 Must-have journeys carry their OWN dedicated evidence file/screenshot this round — J-05 gets
  its first capture in 3 rounds; no journey borrows another's script or screenshot (md5sum-distinct,
  journey-injective).
- TC-9: J-07 step 1's full-horizon forward-aggregate warm running concurrently with `GET /api/health` at
  1Hz — every poll HTTP 200 within budget, VmPeak stays under the 8192 MB cap, margin recorded in
  `reports/perf-budgets.md`.
- Anti-goal checks: AG-3 byte-identity preserved on every changed read path; AG-8 no new unbounded
  whole-table load introduced anywhere (including inside whichever samples.py fix is chosen); AG-10 caps
  unchanged (8192 MB / host-guard values untouched, launch scripts still enforce them).
- Regression: J-01, J-03, J-04, J-05, J-08, J-09 all remain at their PRE-iteration status (J-05 stays
  `failing` — expected, disclosed, not a regression since no code targets it) with dedicated fresh evidence
  each.

## Risk Flags / Notes for Reviewer + QA
- This is the SAME Evidence-page serving path that has now needed two prior audit-fix passes (iter-46) — the
  reviewer should verify the fix pass measures the FIX under the SAME conditions the audit used to disprove
  the prior claim (idle AND concurrent-load, not idle only — this is exactly how iter-46's original fix
  pass under-verified TC-4).
- Whichever cache-fix path is chosen, confirm it does not reintroduce iter-46 B1's exact failure shape (a
  narrowed invalidation check that silently skips a refresh a rebuild/backfill actually needed) — prove the
  new key/staleness rule against BOTH a genuine dataset change and a genuinely stale-but-narrow-key-match
  case.
- QA/browser-qa must let any boot-warm or re-warm window finish before scoring J-06/J-07's cold-path steps,
  per iter-46's own disclosed trap (scoring a cold window as a failure when the warm simply hadn't finished
  yet) — the dev handoff must state clearly when it is safe to score.
- Environment: before running tests, `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-4b4d003d.18723" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-4b4d003d.18723" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-4b4d003d.18723"`.
  Never run the full pytest suite (~10-11h on this 30-year basis — fork-locks the box); use targeted `-k`
  selections per file, mirroring the exact node-ID lists iter-46's handoffs already gave QA. Never
  killall/pkill broad patterns. Launch services ONLY via `scripts/start-backend.sh` /
  `scripts/start-frontend.sh` (AG-10) — never `dev.sh` for measurement-conditions journeys (J-04, J-06).
