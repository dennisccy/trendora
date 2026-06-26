# Iteration 52 — Coherence Audit

**Iteration:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Files changed this iteration: `apps/backend/app/engine/research.py`, `apps/backend/app/api/research.py`, `apps/frontend/app/research/_labs.tsx`, `apps/frontend/lib/api.ts`, `apps/backend/tests/test_api_research.py`, `apps/backend/tests/test_factor_lab_all.py`, `apps/backend/tests/test_research_streaming.py`, `runs/…/state/blueprint.md`.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Factor-Lab analytics (decile + rank-IC + by-regime; `as_of` mode) — canonical source `research:compute_factor_lab`, endpoint `GET /api/research/factor-lab` | OK | `_deciles` / `_rank_ic` / `_risk_adjusted` builders unchanged (research.py); endpoint unchanged (api/research.py:113); blueprint Data Contract row amended with J-109 annotation |
| `mean_max_drawdown` per decile (new displayed field) — sourced from `ForwardReturn.max_drawdown` (J-86 stored field) via same `_deciles` builder | OK — registered additive amendment | Blueprint Data Contract row updated in this iter (blueprint.md diff); value is a mean aggregation of stored `forward_returns.max_drawdown` read VERBATIM, the same pattern `mean_return` uses for `realized_return`; no new computing module, no new endpoint |
| Per-stock forward returns / max_drawdown (J-86) — stored in `forward_returns.max_drawdown`, served via multiple endpoints | OK | The Factor Lab reads the stored column VERBATIM; no independent recomputation of max_drawdown; the J-86 computing path (`forward_testing` INSERT) is untouched |

**Part A checks:**

- No new function computes `max_drawdown` independently. The diff adds `ForwardReturn.max_drawdown` to an existing SELECT projection in `_factor_observations` and `_all_factor_observations_by_horizon` (research.py), then passes it through `_deciles` as `_mean_or_none(mdds)` — an aggregation of stored values, not a recomputation of the canonical value.
- No new endpoint. `GET /api/research/factor-lab` is the only served path; `api/research.py:113` calls `factor_lab_all_cached` with the same cache table, extended key.
- `_all_factor_observations_by_horizon` (renamed from `_all_factor_observations`) is an internal helper — not a new public/service-level computing module and not callable from any other endpoint.
- The `fetchFactorLabAll` frontend function still calls `GET /api/research/factor-lab?all=true` (api.ts diff); the `horizon` param was removed because the view is now horizon-independent — not a new fetch path.
- The J-109 amendment is explicitly registered in the blueprint Data Contract row for "Factor-Lab analytics" (blueprint.md diff line +469 in the table row).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/factor-lab` — all-horizons paired columns (J-109) | OK | Existing canonical home in blueprint IA; UI surface map confirms "New pages/routes: 0"; no nav change |

**Part B checks:**

- The diff adds zero new routes. All frontend changes are confined to `apps/frontend/app/research/_labs.tsx` (the existing Factor Lab page component) and `apps/frontend/lib/api.ts` (type definitions).
- The UI surface map (`reports/phase-goal-…-iter-52-ui-surface-map.md`) explicitly states: "New pages/routes: 0 (all changes are to the existing `/research/factor-lab` route)" and "Navigation changes: no (no new top-level nav entry; no new route)".
- No parallel shell. The horizon selector removal and paired-column addition are presentation changes on the existing page layout.
- `/research/factor-lab` is reachable from the persistent Research nav section in 1 click per the IA (blueprint IA shows it under the Research hub). No reachability regression.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The `_all_factor_observations_by_horizon` rename is a clean internal refactor. The removal of the horizon `<select>` is intentional per J-109 spec and blueprint-registered. No label inconsistencies, no formatting drift, no unregistered genuinely-new value.
