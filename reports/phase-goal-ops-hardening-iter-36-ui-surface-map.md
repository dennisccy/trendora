# Phase goal-ops-hardening-iter-36 — UI Surface Map

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/factor-lab` | `FactorLabPage` — pre-data loading area | Changed behavior | Cold/slow load previously showed a bare unlabelled `LabSkeleton` with no feedback | Throttle/delay the `GET /api/research/factor-lab` response past 3s and confirm a card with heading text starting "Still computing —" and a spinner (`data-testid="slow-compute-notice"`) appears before the table renders |
| `/research/factor-lab` | `FactorLabPage` — error card (`ResearchError`) | Changed behavior | Error card previously had no retry affordance | Force the fetch to fail (stop the backend or block the request), confirm the card reads "Backend unavailable" with a "Retry" button (`data-testid="research-error-retry"`); click it and confirm the page re-enters the loading state (skeleton/computing card reappears, not a second frozen error card) |
| `/research/phase-severity-lab` | `PhaseSeverityLabPage` — pre-data loading area | Changed behavior | Same bare-skeleton gap as Factor Lab | Throttle/delay `GET /api/research/phase-severity-lab` past 3s and confirm the "Still computing — Ns elapsed" card (`data-testid="slow-compute-notice"`) appears before the tables render |
| `/research/phase-severity-lab` | `PhaseSeverityLabPage` — error card (`ResearchError`) | Changed behavior | Error card previously had no retry affordance | Force the fetch to fail, confirm "Backend unavailable" card with "Retry" button (`data-testid="research-error-retry"`); click it and confirm the page re-enters loading (never a second frozen error card) |
| `/research/regime-phase-factor` | `RegimePhaseFactorPage` — pre-data loading area (own `CombinationSkeleton`) | Changed behavior | Same bare-skeleton gap; this page keeps its own skeleton/error markup shape | Throttle/delay `GET /api/research/regime-phase-factor` past 3s and confirm the "Still computing — Ns elapsed" card (`data-testid="slow-compute-notice"`) appears above the existing `CombinationSkeleton` |
| `/research/regime-phase-factor` | `RegimePhaseFactorPage` — inline "Backend unavailable" error card | Changed behavior | Page's own bespoke error card previously had no retry affordance | Force the fetch to fail, confirm the inline "Backend unavailable" card shows a "Retry" button (`data-testid="rpf-error-retry"`, NOT `research-error-retry` — this page uses its own testid); click it and confirm the page re-enters loading |
| `/research/severity-velocity` | `SeverityVelocityPage` — pre-data loading area | Changed behavior | Same bare-skeleton gap as Factor Lab | Throttle/delay `GET /api/research/severity-velocity` past 3s and confirm the "Still computing — Ns elapsed" card (`data-testid="slow-compute-notice"`) appears before the body renders |
| `/research/severity-velocity` | `SeverityVelocityPage` — error card (`ResearchError`) | Changed behavior | Error card previously had no retry affordance | Force the fetch to fail, confirm "Backend unavailable" card with "Retry" button (`data-testid="research-error-retry"`); click it and confirm the page re-enters loading |
| `/research/regime-lab` | `RegimeLabPage` (unchanged, control) | Unchanged | Reference implementation the other 4 pages now match — no code change this phase | Load the page normally and confirm it still shows the same computing/error/retry behavior it already had before this phase (regression check, not a new capability) |
| `/data` | Coverage / membership-timeline panel | Changed behavior (backend-internal, byte-identical) | `_membership_timeline`'s candidate-pool bar loading is now batched (50 symbols/batch) instead of loading the whole 590-symbol × 30-year table at once | Load `/data`, note the `universe_count`, membership-timeline point count, and `coverage_status` values shown; confirm they are unchanged from a pre-phase capture (byte-identical payload — no visible difference expected) |
| `/evidence` | Per-claim "drawdown & dry-spell expectations" panel | Changed behavior (backend-internal, byte-identical in the normal case) | `compute_drawdown_expectations`'s `stored_by_key` read is now chunked (50 tickers/chunk) instead of one unbounded read; reduces (not eliminates) the chance of the "not available right now" placeholder appearing under heavy load | Load `/evidence`, open a certified claim's expectations panel, and confirm it renders real figures (not the "not available right now" placeholder) under normal load — the figures themselves must match a pre-phase capture |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — new `research.membership_timeline_batch_symbols` and `research.drawdown_expectations_ticker_chunk` config keys — no UI surface; internal tuning knobs only.
- `config.yaml` — sets both new keys to `50` — no UI surface.
- `apps/backend/app/engine/prices.py` — new `_BarCache.load_only()` method — internal cache-loading mechanism, no UI surface.
- `apps/backend/app/engine/universe_resolver.py` — `resolve_with_reasons` gained an optional `symbols=` param (default `None`, byte-identical for existing callers) — internal resolver change, no UI surface.
- `apps/backend/app/engine/data_manager.py` — `_membership_timeline`/`_compute_coverage_uncached` restructured for batched loading — byte-identical output served at `/data`, listed above as "changed behavior (backend-internal)" rather than here since it is the mechanism behind a listed row.
- `apps/backend/app/engine/forward_testing.py` — `compute_drawdown_expectations`'s chunked read — byte-identical output served at `/evidence`, listed above as "changed behavior (backend-internal)" rather than here since it is the mechanism behind a listed row.
- Backend test files (`test_bar_cache.py`, `test_data_manager_membership_cache.py`, `test_forward_testing.py`, new `test_membership_timeline_batch_bound.py`, new `test_evidence_drawdown_memory_pressure.py`) — test-only, no UI surface.

---

## Summary

- **Frontend surfaces changed:** 4 (`/research/factor-lab`, `/research/phase-severity-lab`, `/research/regime-phase-factor`, `/research/severity-velocity`)
- **New pages/routes:** 0
- **Modified components:** 4 (`FactorLabPage`, `PhaseSeverityLabPage`, `RegimePhaseFactorPage`, `SeverityVelocityPage`) — all pre-data loading/error state wiring only
- **Navigation changes:** no
- **Backend-only changes:** 7 files (`config.py`, `config.yaml`, `prices.py`, `universe_resolver.py`, `data_manager.py`, `forward_testing.py`, plus backend test files) — all byte-identical payload requirements, no visible number/label change on `/data` or `/evidence`
