# Goal Iteration 29 — Bound the Evidence page's per-claim compute and close the session's last AG-8 finding

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 29
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
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

Close the session's last open anti-goal finding: bound the Evidence page's per-claim drawdown-expectations
computation so it can never exhaust the backend's memory or crash `GET /api/evidence`, and make a residual
per-claim compute failure degrade honestly instead of being silently indistinguishable from "not
applicable."

## BACKGROUND

All 8 Must-have journeys have passed since iter-28's re-verification (`journey-history.json`,
iteration-state.md: "8 passing... all re-verified at iter-28"), and the evaluator has recommended this exact
scope, at full depth, across three consecutive log entries (iter-27's own next-step, and both of iter-28's
evaluations) — the one thing left before GOAL_ACHIEVED can be considered is a real, code-confirmed AG-8
(critical, scored minor) finding. I re-derived it read-only rather than inheriting it: `app.engine.research.
_factor_observations` (`research.py:205-217`) already `yield_per`-streams its SOURCE query, but the join's
accumulator, `ret_by_run_symbol`, still holds one entry per distinct `(run_id, symbol)` pair across a full
horizon's `forward_returns` history for `as_of=None` — 803,042 pairs / 3,964,725 rows measured live at
iter-28 — an unbounded whole-table materialization in substance. I confirmed `apps/backend/tests/
test_research_streaming.py` (a prior pass's own test suite for this exact function) proves VALUE correctness
is independent of `read_batch_size`, but asserts no upper bound on live accumulator size — a correctness
proof, not a memory-boundedness proof, so the existing test suite would not catch this. I also confirmed the
exact reachability chain by direct code read: `GET /api/evidence` → `build_evidence_payload` →
`compute_drawdown_expectations_cached` → `compute_drawdown_expectations` → `compute_samples` →
`_factor_samples` → `_factor_observations`, matching the evaluator's own `research.py:215` traceback
attribution — and the SAME ingest-finalize warm loop (`data_manager.py:3361`), which iter-8 already hardened
with a per-claim `MemoryError` catch (a real safety net, but one that leaves whichever claims come after an
abort permanently un-warmed, deferring the SAME crash to the next live request). The live ledger
(`runs/goal-session-mcp-loop/state/certified-claims.jsonl`, 7 claims) confirms the exposure is real: 5 of 7
claims are `kind="factor"`, the exact path that reaches `_factor_observations`.

Full depth is justified two independent ways (self-check item 4): (1) trigger #1 — the fix and its safety
net span ≥3 modules (`app.engine.research`, `app.engine.evidence`, `app.engine.data_manager`) whose
interaction (a nested call chain from `api/evidence.py` through `evidence.py`, `forward_testing.py`,
`samples.py`, into `research.py`, plus the separate `data_manager.py` ingest path) is not covered by any
single journey's own test suite; (2) goal.md's own written trigger — this lands a genuinely new
user-visible degraded-state message on the Evidence page (`expectations_status: "unavailable"`), not merely
a backend robustness change.

Target-selection deviation (self-check item 5): none of the 8 journeys is currently failing or partial, so
the usual "pick the next FAILING/PARTIAL journey" rubric does not directly apply — this is anti-goal
remediation, not journey progression. I targeted J-06 (its own step 1 measures `/evidence`'s on-load
latency — the natural home for this fix's live smoke evidence) and J-07 ("heavy aggregates never take the
service down" — the closest thematic and evidentiary match for a memory-safety fix), while noting the
iter-28 evaluator's own assumption-ledger entry scoped J-07's LITERAL acceptance clause to
`compute_forward_aggregates` alone, treating this `research.py` defect as "a separate, open AG-8 finding on
a neighbouring aggregate" — I am not reopening that scoping, only reusing J-07 as the regression anchor for
a resilience fix in the same spirit.

Lesson applied (iter-28, "verify a [test selector's fixture cost] by reading the fixtures, not the
[selector's] name"): I read `test_research_streaming.py`'s `prune_engine`/`component_engine` fixtures and
`test_evidence.py`'s `evidence_dd_engine` fixture directly — all three are small, hand-built, in-test-file
SQLite fixtures (a handful of rows), not the expensive 30-year `loaded_engine` fixture. `test_api_evidence.py`,
by contrast, DOES use `loaded_engine` — new tests below are steered at the cheap fixtures, not that file.
Lesson applied (iter-13, "any iter carrying an UNRESOLVED critical anti-goal on a 'smaller blast radius'
rationale... re-read for a worse-than-before manifestation before re-deferring"): this iteration does NOT
defer AG-8 again — it fixes it, per the evaluator's own three-times-repeated recommendation.

## IN SCOPE

### Backend

- [ ] Bound `app.engine.research._factor_observations`'s per-observation join (`ret_by_run_symbol`,
  `research.py:205-217`) so peak added memory no longer scales with a full horizon's `forward_returns`
  history — chunk/bound the accumulator itself (the SOURCE query is already `yield_per`-streamed; the
  accumulator is the unbounded structure). Same computing module; same two reachers
  (`compute_samples`'s factor-cohort caller, and the pre-existing `/research` Factor Lab page's own direct
  call); byte-identical output for both, for `as_of=None` and for an `as_of=D` call (TC-1, TC-2, TC-3,
  TC-9).
- [ ] Add a generic per-claim isolate-and-continue guard to `app.engine.evidence.build_evidence_payload`'s
  per-claim `expectations` attach step, mirroring the EXISTING per-claim `MemoryError`-then-continue
  convention `data_manager.py`'s drawdown-expectations ingest warm loop already uses near
  `data_manager.py:3361` — a compute failure (`MemoryError` or otherwise) for one claim must never abort
  the response for the others. On a caught failure, omit `expectations` and add the new
  `expectations_status: "unavailable"` field to THAT claim's row only; every other claim's row is
  byte-unchanged (TC-4).
- [ ] Leave `data_manager.py`'s existing per-loop `MemoryError` catch in the ingest-finalize
  drawdown-expectations warm loop in place, unremoved (defense-in-depth); TC-7 confirms that under
  today's basis it is no longer needed to complete a normal ingest once `_factor_observations` is bounded.
- [ ] `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and
  `ensure_historical_forward_aggregates_dispatched` stay byte-frozen (binding, iteration-state.md "Do not
  redo") — this fix touches a different function/table family; do not reopen them.

### Frontend

- [ ] `apps/frontend/lib/evidence.ts`'s `CertifiedClaim` interface gains one new optional field,
  `expectations_status?: "unavailable"`, alongside the existing `expectations` field.
- [ ] Add a small pure rendering-state helper to `apps/frontend/lib/evidence.ts` (mirrors this codebase's
  established pattern of extracting a testable decision function rather than testing a React component
  directly — the iter-24/25 J-09 branch-resolver precedent) that returns a distinct state for
  `expectations_status === "unavailable"` versus the pre-existing "no `expectations`, no status field"
  case; test it in `apps/frontend/lib/evidence.test.ts` (TC-5).
- [ ] `apps/frontend/app/evidence/page.tsx`'s `DrawdownExpectationsPanel` (or its caller) renders a calm,
  factual inline note when a claim's `expectations_status === "unavailable"` — distinct from its EXISTING
  "renders nothing" behavior when `expectations` is absent with no status field. Reads the field verbatim;
  no client-side recompute.

### New user-facing capability

When the backend cannot resolve one claim's historical drawdown/dry-spell expectations (a transient
per-claim compute failure), that ONE claim's Evidence card now discloses it honestly instead of silently
rendering nothing indistinguishable from "not applicable" — every other claim on the page is unaffected.
Structurally, `/evidence` becomes memory-safe on the deep basis, which is the primary change; the
disclosure above is what makes the residual-failure case honest rather than silent.

### New information displayed

One new optional per-claim field, `expectations_status: "unavailable"`, surfaced as a small inline note on
the affected claim's card only.

### New user actions

None — this is a passive disclosure, no new control.

### UI surface changes

No new page or panel — an additive state inside the EXISTING `DrawdownExpectationsPanel` section of the
EXISTING Evidence claim card.

### Product surface delta

`/evidence` becomes memory-safe on the deep basis (structural), and, as a secondary consequence, gains one
small honest failure-disclosure state that was previously indistinguishable from "not applicable."

### Blueprint conformance

No new page/nav/route. Lives entirely under the EXISTING "Evidence" nav item (`/evidence`), already
registered in `blueprint.md`'s Information Architecture as one of J-05's homes (per-claim drawdown
expectations, iter-7) and as one of J-06's 11 measured pages. `runs/goal-session-ops-hardening/state/
blueprint.md` already carries this iteration's additive narrative paragraph (written this iteration).

### Data-contract additions

`expectations_status: "unavailable"` — string literal enum with ONE legal value today; OPTIONAL, present
ONLY on a claim row whose per-claim drawdown-expectations compute raised an exception this request; absent,
unchanged, for a successful compute AND for every pre-existing honest-None case (out-of-scope horizon,
unresolvable cohort selectors, zero-observation cohort). Computed by: `app.engine.evidence.
build_evidence_payload` (existing function, extended — the SAME canonical producer already documented for
the `expectations` field). Served by: `GET /api/evidence` (unchanged, same endpoint). Registered this
iteration in `runs/goal-session-ops-hardening/state/blueprint.md` as an additive Notes-column append to the
EXISTING "Membership timeline / research hot-key caches" row (tagged `[TARGET, iter-29 building]`; the
`[TARGET]` tag is removed once the evaluator confirms it built and passing) — no new row, no second
producer, no second endpoint.

## OUT OF SCOPE

- Sibling accumulator functions in `research.py` serving the ledger's other two claim kinds
  (`_combination_observations` for `kind="combination"`, `_event_study_members` for `kind="event-study"`) —
  the same theoretical AG-8 risk, but unproven: both of this session's observed MemoryErrors trace to
  `_factor_observations`, and 5 of the live ledger's 7 claims are `kind="factor"`. Named as a non-blocking
  follow-up, not attempted this iteration (rule 5 — never bundle two risky changes).
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split — byte-frozen (binding,
  iteration-state.md "Do not redo").
- Audit finding B2 (`_backfill`'s cross-call rollback residual) — carried, unchanged, its own iteration.
- Retargeting `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches, or removing the
  dangling imports at `backtest.py:75` / `mcp/tools.py:38` — carried, unchanged.
- UT-04's fresh-install DB fixture (or an explicit written waiver) — carried, unchanged; a separate,
  orthogonal gap this iteration does not touch.
- Any live, real memory-pressure induction on the running backend — forbidden (iteration-state.md "Do not
  redo": "Never re-trigger a live memory-pressure background-compute failure"). All failure-path proof in
  this iteration is via monkeypatch/mocked test hooks only (TC-4, TC-5), mirroring the iter-26 J-09
  precedent of accepting a deterministic code-level round-trip over an actual witnessed live trigger.
- OWNER, non-blocking: whether the historical `/backtest` first-touch latency (206–273 s at iter-28) needs
  its own written budget or a redesign; backlog card B-1107 (global dispatch cap) stays optional.
- Any new feature, page, or unrelated Data-Contract value.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent (TC-6, TC-8, TC-10)
- [ ] J-07 passes via browser-qa-agent (TC-6, TC-7)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green via deterministic
  golden replay / LLM fallback — a full regression sweep, since this iteration's fix touches shared
  research-engine code read by multiple pages
- [ ] `_factor_observations`'s join is memory-bounded (TC-1), byte-identical (TC-2), and
  no-lookahead-preserving (TC-3)
- [ ] A per-claim compute failure never crashes `GET /api/evidence` for the other claims (TC-4) and is
  honestly, distinguishably disclosed on the Evidence page (TC-5)
- [ ] The Factor Lab secondary consumer is unaffected (TC-9)
- [ ] No anti-goal violation introduced; this iteration's own live evidence (TC-6, TC-7) gives the evaluator
  what it needs to assess whether AG-8's `research.py:207-217` finding is now resolved
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-29-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (full 11-page sweep including `/evidence`, plus the deterministic replay lane per TC-10)
  and J-07 (heavy-aggregate resilience, including a live `/evidence` load and a small single-day backfill
  exercising the ingest-finalize drawdown-expectations warm loop). Regression spot-check: the `/research`
  Factor Lab page (TC-9) — not a Must-have journey, but a secondary consumer of the changed function.
  Smoke replay for the required-still-passing set: J-01, J-03, J-04, J-05, J-08, J-09 (golden scripts,
  unchanged this iteration).
- Unit/integration (steer new tests at the CHEAP, hand-built fixtures confirmed by direct read this
  iteration — never `test_api_evidence.py`'s `loaded_engine`):
  - `apps/backend/tests/test_research_streaming.py` — extend with a new fixture whose row count spans
    more than one `read_batch_size` chunk across ≥2 `run_id`s, using the file's own `prune_engine`-style
    hand-built pattern and `_eq()` byte-identity convention (TC-1, TC-2, TC-3).
  - `apps/backend/tests/test_evidence.py` — extend `evidence_dd_engine` (or a small variant with a second
    claim) with a monkeypatched-failure test (TC-4).
  - `apps/frontend/lib/evidence.test.ts` — new cases for the rendering-state helper (TC-5).
- Error cases: a claim whose cohort is genuinely unresolvable (unknown factor, out-of-scope horizon) must
  keep rendering the EXISTING silent-omission behavior unchanged — no `expectations_status` field, proving
  the new code path is additive, not a replacement of the pre-existing honest-None case.

Test-first contract:

- TC-1: given a `forward_returns` test fixture (extending `test_research_streaming.py`'s existing
  hand-built fixtures) whose rows span more than one `research.read_batch_size` chunk across ≥2 distinct
  `run_id`s, when `_factor_observations` processes it for `as_of=None`, then a new unit test asserts the
  join's live accumulator dict never holds more entries than one bounded chunk at any point during the
  call — never one entry per distinct `(run_id, symbol)` pair in the whole fixture.
- TC-2: given the same extended fixture, when the bounded rewrite's `_factor_observations` output is
  compared to the current (pre-fix) implementation's output on the identical fixture (mirrors
  `test_research_streaming.py`'s own `_eq()` byte-identity convention), then every returned observation
  (`run_id`, `ticker`, `factor`, `return`, `max_drawdown`, `regime`) matches exactly, in the same order,
  for both an `as_of=None` call and an `as_of=D` call.
- TC-3: given the `as_of=D`-scoped call from TC-2, when a unit test inspects the returned observations'
  `run_id`s against `ScannerRun.asof_date`, then zero returned observations reference a run dated after
  `D`.
- TC-4: given `test_evidence.py`'s `evidence_dd_engine` fixture extended with a second resolvable claim,
  and `compute_drawdown_expectations_cached` monkeypatched to raise `MemoryError` for exactly one of the
  two claims, when `build_evidence_payload(ledger_path, session=session, config=...)` is called directly,
  then the returned payload has exactly two claim rows: the monkeypatched claim's row carries
  `expectations_status: "unavailable"` and no `expectations` key, and the other claim's row carries its
  normal `expectations` key unaffected.
- TC-5: given a `CertifiedClaim`-shaped object with `expectations_status: "unavailable"` and no
  `expectations` key, when the new pure rendering-state helper (`apps/frontend/lib/evidence.ts`, tested in
  `evidence.test.ts`) evaluates it, then it returns a value distinct from what it returns for an object
  with no `expectations_status` field at all (the pre-existing not-applicable case).
- TC-6: given the live deep-basis DB (the evidence ledger's 7 claims) and a backend started via
  `scripts/start-backend.sh`, when `/evidence` is loaded in a browser, then the page renders every claim's
  card (including the `expectations` panel for each resolvable factor/combination/event-study claim)
  within its committed budget in `reports/perf-budgets.md` (Item I), and `logs/backend.log` shows zero
  MemoryError / "Exception in ASGI application" lines for that request window.
- TC-7: given an unsnapshotted historical trading day distinct from every date already consumed by this
  session's prior tests (iteration-state.md "Do not redo" list), when a small single-day backfill runs to
  completion (mirrors J-05 step 1's existing action) and its ingest-finalize drawdown-expectations warm
  loop (`data_manager.py:3361`) processes every ledger claim, then the run's persisted
  `aggregates_refreshed` list includes `"drawdown_expectations"` and `logs/backend.log` shows zero
  MemoryError lines from that loop for this run.
- TC-8: given J-06's own 11-page load sweep is re-run this iteration, when `/evidence`'s reading is
  recorded in `reports/perf-budgets.md`, then the reading is within its existing committed budget with no
  regression from the pre-fix reading.
- TC-9: given the `/research` Factor Lab page (a pre-existing consumer of `_factor_observations`, not
  itself a Must-have journey), when it is loaded in a browser for at least one factor/horizon combination,
  then its decile table and rank-IC figures render with real numeric values — no console error, no blank
  or empty table.
- TC-10: given `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (fixed at iter-28, never
  exercised through the deterministic replay lane since — iter-28's carried gap), when the deterministic
  golden replay runs J-06 end-to-end this iteration, then every step returns a PASS row with zero FAIL rows
  in the merged `ui-test-results.md`.

## NOTES

- **Depth justification (self-check item 4):** full, citing trigger #1 (structural/cross-cutting — the fix
  and its safety net span `app.engine.research`, `app.engine.evidence`, and `app.engine.data_manager`, a
  ≥3-module interaction no single journey's own tests cover) AND goal.md's own written trigger (a genuinely
  new user-visible degraded-state message on `/evidence`). The last evaluator verdict (iter-28) was
  CONTINUE, not ESCALATE, and consecutive lean iterations dispatched = 1 (hardening cadence 4, not met) —
  neither of those triggers is the basis; both structural and UI-change triggers hold independently.
- **Target selection (self-check item 5):** deviates from the standard failing/partial-journey rubric
  because zero journeys are failing or partial — see BACKGROUND for the full reasoning (this is anti-goal
  remediation, and J-06/J-07 are the closest-matching journeys for fresh regression scrutiny, not journeys
  moving from failing to passing).
- Coherence: iter-28's `coherence.md` verdict was COHERENCE-PASS — no consolidation pass required this
  iteration.
- An assumptions.md entry was recorded this iteration (`runs/goal-session-ops-hardening/state/
  assumptions.md`, "iter-29 — goal-decomposer"): whether AG-8's "honest NA placeholder" language requires
  the new failure state to be visually distinguishable from the pre-existing silent-omission state, or
  whether reusing the existing silent omission would already satisfy it. This spec chose to make it
  distinguishable (a new `expectations_status` field); a human who disagrees can drop that field and the
  frontend bullet, keeping only the backend bound + catch-and-continue.
- If the evaluator scores this iteration's evidence as closing AG-8's `research.py:207-217` finding (no
  new anti-goal finding, all 8 journeys still passing, TC-1 through TC-10 all green), no further named
  blocking work is known to this decomposer — the next iteration's decomposer should check whether that
  makes this the point to consider GOAL_ACHIEVED, rather than manufacturing new scope.
