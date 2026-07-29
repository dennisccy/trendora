# goal-ops-hardening-iter-29 Execution Plan

**Goal alignment:** closes the session's last open AG-8 (critical) finding — an unbounded
in-memory join accumulator on the Evidence read path — directly serving goal.md's Constraint
"boot and request paths serve stored values and never stream the full `daily_prices` table into
RAM" and Success Criterion "No unbounded whole-table loads." No drift from goal.md: no new page,
no new score/claim, no proven-language. Targets J-06 (measured `/evidence` latency) and J-07
(heavy-aggregate memory resilience) per the spec's own reasoning; all 6 other Must-have journeys
(J-01, J-03, J-04, J-05, J-08, J-09) are required-still-passing via regression replay only.

## What to Build

Hardening-only iteration. No new journey, page, endpoint, score, or claim — `/evidence` becomes
memory-safe on the deep basis, plus one small honest failure-disclosure state.

- **Fix 1 (AG-8, `apps/backend/app/engine/research.py:205-217`, `_factor_observations`):** the
  SOURCE query (`fr_stmt` against `ForwardReturn`) is already `yield_per`-streamed, but its join
  accumulator `ret_by_run_symbol` still holds one entry per distinct `(run_id, symbol)` pair
  across the FULL horizon's `forward_returns` history for `as_of=None` — measured 803,042 pairs /
  3,964,725 rows live at iter-28. Chunk/bound the accumulator itself (not just the source query)
  so peak added memory no longer scales with the full history. `runs_with_fr` (already a sorted
  list of run ids) is the natural chunk axis — process it in bounded slices, building
  `ret_by_run_symbol` scoped to one slice at a time, streaming+joining that slice's
  `ScannerResult`s, extending the final `observations` list, then discarding the slice's dict
  before the next. The final `observations` list itself is the function's existing return shape
  and is NOT the target — downstream `_deciles`/`_decile_member_slice` need it whole; only the
  accumulator dict's peak size is bounded. Reuse `config.research.read_batch_size` (2000, already
  the single source of this module's streaming batch size — no-magic-numbers convention) for the
  chunk width unless TDD against TC-1 shows a dedicated config key is cleaner; either way, no
  inline literal. Two reachers of this function (`compute_samples`'s factor-cohort caller, and the
  `/research` Factor Lab page's own direct call) must see byte-identical output, in the same
  order, for both `as_of=None` and `as_of=D` (TC-1, TC-2, TC-3, TC-9).
- **Fix 2 (`apps/backend/app/engine/evidence.py:113-153`, `build_evidence_payload`):** wrap the
  per-claim `compute_drawdown_expectations_cached(session, row["claim"], config)` call (inside the
  `if session is not None:` branch) in a try/except mirroring the EXISTING per-claim
  `MemoryError`-then-continue convention `data_manager.py`'s drawdown-expectations ingest warm
  loop already uses at `data_manager.py:3361` (isolate-and-continue, not a blanket catch around
  the whole claims loop). On a caught failure (`MemoryError` or otherwise) for one claim: omit
  `row["expectations"]`, set `row["expectations_status"] = "unavailable"` on that claim's row
  ONLY; every other claim's row stays byte-unchanged, and the loop continues to the next entry
  (TC-4). The pre-existing honest-None case (unresolvable cohort, zero-observation cohort — the
  function returning `None` without raising) is UNCHANGED: no `expectations` key, no
  `expectations_status` key — this fix is additive for the exception path only, never a
  replacement of the existing silent-omission behavior.
- **Leave alone:** `data_manager.py:3361`'s existing per-loop `MemoryError` catch in the
  ingest-finalize warm loop (defense-in-depth, unremoved); `compute_forward_aggregates`,
  `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched` and
  J-08's serving split (byte-frozen, iteration-state.md "Do not redo" — different function/table
  family, do not reopen).
- **Frontend (`apps/frontend/lib/evidence.ts`):** add one new optional field to the
  `CertifiedClaim` interface (~line 78-89): `expectations_status?: "unavailable"`, alongside the
  existing `expectations` field. Add a small pure rendering-state helper (mirrors this codebase's
  established pattern of extracting a testable decision function rather than testing a React
  component directly — the iter-24/25 J-09 branch-resolver precedent) that returns a value
  distinct for `expectations_status === "unavailable"` vs. the pre-existing "no `expectations`, no
  status field" case. Unit-test it in `apps/frontend/lib/evidence.test.ts` (TC-5).
- **Frontend (`apps/frontend/app/evidence/page.tsx`, `DrawdownExpectationsPanel` ~line 242-306):**
  when the new helper reports "unavailable," render a calm, factual inline note in place of the
  panel's table — distinct from the EXISTING "renders nothing" behavior when `expectations` is
  absent with no status field (that case stays byte-unchanged). Reads the field verbatim; no
  client-side recompute. Style like the codebase's existing honest-copy pattern (e.g. the "Pending
  — monitored as new data matures" treatment already used elsewhere on this same card for
  `forward_walk == null`) — never an alarming/error treatment; this is a routine transient-failure
  disclosure, not an error banner.
- **New backend unit tests** (steer at the CHEAP, hand-built fixtures — confirmed by direct read
  this iteration, never `test_api_evidence.py`'s expensive `loaded_engine`):
  - `apps/backend/tests/test_research_streaming.py` — extend with a new fixture (the file's own
    `prune_engine`-style hand-built pattern) whose rows span more than one `read_batch_size` chunk
    across ≥2 `run_id`s; assert the live accumulator never holds more than one bounded chunk's
    worth of entries at any point (TC-1); assert byte-identity vs. the pre-fix implementation via
    the file's own `_eq()` convention, for both `as_of=None` and `as_of=D` (TC-2); assert zero
    returned observations reference a run dated after `D` for the `as_of=D` call (TC-3).
  - `apps/backend/tests/test_evidence.py` — extend `evidence_dd_engine` with a second resolvable
    claim; monkeypatch `compute_drawdown_expectations_cached` to raise `MemoryError` for exactly
    one of the two; assert that claim's row carries `expectations_status: "unavailable"` and no
    `expectations` key while the other claim's row is unaffected (TC-4).
  - `apps/frontend/lib/evidence.test.ts` — new cases for the rendering-state helper (TC-5).
  - Error-case regression: a claim with a genuinely unresolvable cohort (unknown factor,
    out-of-scope horizon) must keep the EXISTING silent-omission behavior unchanged — no
    `expectations_status` field — proving the new path is additive, not a replacement.
- **Live/browser verification** (reviewer/QA, not developer-authored tests):
  - TC-6: live `/evidence` load on the deep-basis DB renders every claim's card within its
    committed budget (`reports/perf-budgets.md`, Item I), and `logs/backend.log` shows zero
    MemoryError / "Exception in ASGI application" lines for that request window.
  - TC-7: a small single-day backfill on an unsnapshotted date runs to completion and its
    ingest-finalize drawdown-expectations warm loop (`data_manager.py:3361`) processes every
    ledger claim; the run's persisted `aggregates_refreshed` list includes
    `"drawdown_expectations"`; zero MemoryError lines from that loop. **Consumed race dates
    already used this session (do not reuse):** 2011-03-10, 2015-09-09, 2018-02-15, 2018-03-15,
    2025-05-15, 2026-05-02..29 (`runs/goal-session-ops-hardening/state/iteration-state.md`, "Do
    not redo") — pick a genuinely unsnapshotted date outside this list, confirmed against
    `/scanner-runs` at execution time.
  - TC-8: J-06's 11-page sweep re-measures `/evidence` within its existing committed budget, no
    regression from the pre-fix reading.
  - TC-9: `/research` Factor Lab page (secondary consumer, not a Must-have journey) renders its
    decile table + rank-IC figures with real values for at least one factor/horizon combination —
    no console error, no blank/empty table.
  - TC-10: deterministic golden replay of `runs/goal-session-ops-hardening/journey-scripts/
    J-06.json` (fixed at iter-28, never exercised through the replay lane since) runs end-to-end
    with zero FAIL rows.
  - Regression smoke replay: J-01, J-03, J-04, J-05, J-08, J-09 (golden scripts, unchanged this
    iteration) must all stay green — this fix touches shared research-engine code read by multiple
    pages.
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-29-dev.md`.

## Agents Required

- backend-data: yes — `research.py`'s accumulator bound, `evidence.py`'s per-claim guard, new
  backend unit tests (TC-1–TC-4), and confirming the ingest-finalize warm loop still completes
  cleanly (TC-7).
- frontend-ux: yes — `CertifiedClaim` field + rendering-state helper + `DrawdownExpectationsPanel`
  inline note + `evidence.test.ts` cases (TC-5).

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- bound `_factor_observations`'s `ret_by_run_symbol`
  accumulator (TC-1, TC-2, TC-3, TC-9)
- `apps/backend/app/engine/evidence.py` -- per-claim isolate-and-continue guard in
  `build_evidence_payload` around `compute_drawdown_expectations_cached` (TC-4)
- `apps/backend/tests/test_research_streaming.py` -- new bounded-accumulator + byte-identity +
  no-lookahead tests (TC-1, TC-2, TC-3)
- `apps/backend/tests/test_evidence.py` -- extend `evidence_dd_engine`, new monkeypatched-failure
  test (TC-4)
- `apps/frontend/lib/evidence.ts` -- `CertifiedClaim.expectations_status?: "unavailable"` field +
  new pure rendering-state helper
- `apps/frontend/lib/evidence.test.ts` -- new rendering-state helper cases (TC-5)
- `apps/frontend/app/evidence/page.tsx` -- `DrawdownExpectationsPanel` renders the inline
  "unavailable" note
- `docs/handoffs/goal-ops-hardening-iter-29-dev.md` -- dev handoff (required, Definition of Done)

Already updated this iteration (goal-decomposer, additive-only — verify no drift, do not re-edit
unless a genuine mismatch is found): `runs/goal-session-ops-hardening/state/blueprint.md` (the
`expectations_status` Data-Contract row).

**Explicitly OUT OF SCOPE (do not touch):** `_combination_observations` / `_event_study_members`
(sibling accumulators, same theoretical AG-8 risk but unproven — named follow-up only, never
bundle two risky changes); `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
`ensure_historical_forward_aggregates_dispatched`, J-08's serving split (byte-frozen); audit
finding B2 (`_backfill` rollback residual); `test_forward_testing_serving_split.py` monkeypatch
retargeting / dangling imports at `backtest.py:75` / `mcp/tools.py:38`; UT-04's fresh-install DB
fixture gap; any live/real memory-pressure induction on the running backend (forbidden —
monkeypatch/mocked test hooks only, per iteration-state.md); the historical `/backtest`
first-touch latency budget decision (owner-only); backlog card B-1107; any new feature, page, or
unrelated Data-Contract value.

## UI Evolution

- New user-facing capability: when the backend cannot resolve one claim's historical
  drawdown/dry-spell expectations (a transient per-claim compute failure), that ONE claim's
  Evidence card now discloses it honestly instead of silently rendering nothing indistinguishable
  from "not applicable" — every other claim on the page is unaffected.
- New information displayed: one new optional per-claim field, `expectations_status:
  "unavailable"`, surfaced as a small inline note on the affected claim's card only.
- New user actions: none — passive disclosure, no new control.
- UI surface changes: no new page or panel — an additive state inside the EXISTING
  `DrawdownExpectationsPanel` section of the EXISTING Evidence claim card.
- Navigation changes: none — lives entirely under the existing `/evidence` nav item.

## Visual Requirements

- Component patterns: reuse the existing claim-card / `Field` / `DrawdownExpectationsPanel`
  structure in `apps/frontend/app/evidence/page.tsx` — no new component library usage.
- Layout: no layout change — the note occupies the same panel slot the expectations table
  currently renders into, for that one claim only.
- Key visual effects: calm and factual, matching the card's existing honest-copy conventions (the
  `text-text-faint` "Pending — monitored as new data matures" treatment already used on the same
  card) — never an alarming/red/error treatment; this is an expected transient state, not a system
  error.
- States to handle: existing "expectations present" (table renders, unchanged); existing "no
  expectations, no status field" (renders nothing, unchanged — the honest-None cohort-unresolvable
  case); NEW "expectations_status === 'unavailable'" (inline note, no table).

## Key Test Scenarios

- TC-1/TC-2/TC-3: the join accumulator never holds more than one bounded chunk's worth of entries
  at any point during a call; output is byte-identical to the pre-fix implementation for both
  `as_of=None` and `as_of=D`; zero returned observations reference a run dated after `D`.
- TC-4: a monkeypatched per-claim compute failure yields `expectations_status: "unavailable"` +
  no `expectations` key for that claim only; the other claim's row is byte-unchanged.
- TC-5: the frontend rendering-state helper returns a value distinct from the pre-existing
  no-field case.
- TC-6: live `/evidence` load on the deep-basis DB (7 ledger claims) renders every card within
  budget; zero MemoryError / ASGI-exception lines in `logs/backend.log`.
- TC-7: a single-day backfill on a genuinely fresh date completes; ingest-finalize
  drawdown-expectations warm loop processes every claim; `aggregates_refreshed` includes
  `"drawdown_expectations"`; zero MemoryError lines.
- TC-8: J-06's `/evidence` reading stays within its existing committed budget, no regression.
- TC-9: `/research` Factor Lab renders its decile table + rank-IC with real values, no console
  error, no blank table.
- TC-10: golden replay of `journey-scripts/J-06.json` runs end-to-end, all-PASS, zero FAIL rows.
- Regression: J-01, J-03, J-04, J-05, J-08, J-09 all replay green via golden/smoke — this fix
  touches shared research-engine code read by multiple pages, so this is a full regression sweep,
  not a spot-check.
- Error-case regression: a genuinely unresolvable cohort (unknown factor, out-of-scope horizon)
  keeps rendering the pre-existing silent-omission behavior — no `expectations_status` field.

## Testing Notes (host constraint)

Run all new backend selectors (TC-1–TC-4) in ONE combined pytest invocation, host-guard
taskset/BLAS-thread-capped per `project-extensions/host-guard/host-guard.env`, launched via
`setsid nohup` + polled to completion in-turn — never run the full suite, never run a second
concurrent pytest process (established project convention; iter-26/27/28 precedent). The spec's
own investigation this iteration already confirmed `test_research_streaming.py`'s `prune_engine`/
`component_engine` fixtures and `test_evidence.py`'s `evidence_dd_engine` fixture are all small,
hand-built, in-file SQLite fixtures — NOT the expensive session-scoped `loaded_engine` fixture —
so this run should be fast. Still, per iter-28's own lesson ("verify a selector's fixture cost by
reading the fixtures, not the name" — `test_readiness.py -k drift` looked fixture-free but pulled
in `loaded_engine` anyway, 1h37m), re-confirm any NEW selector's actual fixture chain before
assuming it's cheap.
