# Iteration 36 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity, membership timeline) | OK | Canonical module `app.engine.data_manager` (`_compute_coverage_uncached`) and canonical endpoint `GET /api/data` are unchanged. `apps/backend/app/engine/data_manager.py:497-620` (`_membership_timeline`, new `_excluded_counts_by_date` helper) only change *how* bars are loaded (batched via a new `_BarCache.load_only` sibling method, `apps/backend/app/engine/prices.py:164-206`) inside the SAME function — no new function computes universe/coverage figures, no second endpoint. `resolve_with_reasons` (`apps/backend/app/engine/universe_resolver.py:122-160`) gained an optional `symbols=` filter param; every existing call site passes none (byte-identical default). Re-formatting/re-scoping of an existing read, not a duplicate computation. |
| Membership timeline / research hot-key caches — `drawdown_expectations` (`/evidence`) | OK | Canonical module `app.engine.forward_testing` (`compute_drawdown_expectations`) and canonical endpoint `GET /api/evidence` (via `event_study_cache`/`compute_drawdown_expectations_cached`) are unchanged. `apps/backend/app/engine/forward_testing.py:2316-2346` replaces one unchunked `session.exec(fr_stmt).all()` with a loop over `research.drawdown_expectations_ticker_chunk`-wide ticker chunks, each still built into the SAME `stored_by_key` dict inside the SAME function — no second producer, no second endpoint. Both new backend test files (`test_membership_timeline_batch_bound.py`, `test_evidence_drawdown_memory_pressure.py`) pin a `git show HEAD`-referenced pre-fix body and assert byte-identical output against the shipped version, consistent with the blueprint's byte-identity requirement. |
| Research lab computing/error/retry states (`/research/factor-lab`, `/research/phase-severity-lab`, `/research/regime-phase-factor`, `/research/severity-velocity`) | OK | All four pages now call the SAME already-exported `resolveLabLoadPanel` (`apps/frontend/lib/lab-load-panel.ts`, unmodified this iteration — 0 diff to the file) and the SAME shared `ResearchError`/`SlowComputeNotice`/`useElapsedSeconds` (`apps/frontend/app/research/_labs.tsx:179-243`), mirroring Regime Lab's iter-33 pattern. No new component, no forked resolution logic, no new fetch/endpoint — presentation-only wiring of a pre-data loading state onto an unchanged data fetch. |
| New config knobs `research.membership_timeline_batch_symbols`, `research.drawdown_expectations_ticker_chunk` | OK (not a displayed value) | `apps/backend/app/config.py:1371-1387`, `config.yaml:916-928` — internal tuning knobs for the batching mechanisms above, each explicitly given its own dedicated axis (not reused from `read_batch_size`/`factor_join_run_chunk`, per the binding iter-29 lesson). Not a served/displayed value — no Data Contract row applies (matches the session's own iter-18/23 "a log line/config knob is not a served value" precedent). |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/factor-lab`, `/research/phase-severity-lab`, `/research/regime-phase-factor`, `/research/severity-velocity` | OK | No new page/route — all four already live under the existing `Research` nav item (`/research`, blueprint IA table row 7). Diff touches only `apps/frontend/app/research/_labs.tsx` and `apps/frontend/app/research/severity-velocity/page.tsx`; no sidebar/nav/router file appears in `git diff <snapshot-sha> --stat` (checked full stat — no `sidebar.tsx`/`nav`/router change). Reachability unchanged (still ≤2 clicks via the pre-existing Research index). |
| `/data`, `/evidence` (backend-internal fixes) | OK | No visible surface change; both already have their homes in the blueprint IA table (Data Manager, Evidence). Confirmed no new component/route in the diff. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `RegimePhaseFactorPage` keeps its own pre-existing bespoke inline "Backend unavailable" error `<div>` (with its own `data-testid="rpf-error-retry"`) rather than switching to the shared `ResearchError` component the other three sibling labs use (`data-testid="research-error-retry"`) — `apps/frontend/app/research/_labs.tsx:5031-5048`. This is not new drift: the bespoke card pre-dates this iteration (this iteration only added a Retry button to the existing markup), the user-visible copy is verbatim-matched to `ResearchError`'s ("Backend unavailable" / "could not load from the API. No figures are shown rather than fabricated values..."), and the divergence is explicitly disclosed in an inline code comment ("only the computing/retry SEMANTICS are shared, not the markup") and in the ui-surface-map. A future hygiene pass could consolidate RPF's inline card into `ResearchError` itself, but this is cosmetic/test-id-only, not a coherence violation — WARN-level observation only, does not block.
