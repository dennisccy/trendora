**Verdict:** COHERENCE-PASS

## Iteration 38 — Coherence Audit

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 38
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Snapshot SHA:** 800c9126d6d5e12b7d4b97da39a50969c8762b72

---

## Files changed this iteration

Backend:
- `apps/backend/app/api/market_phase.py` — adds `full=true` query param to `GET /api/market-phase`
- `apps/backend/app/engine/market_phase.py` — adds `market_phase_full_cached` and `market_phase_default_payload` helpers; carries `timeline_full` in the canonical payload
- `apps/backend/tests/test_market_phase.py` — new backend tests (no UI surface)

Frontend (new):
- `apps/frontend/components/phase-band-primitive.ts`
- `apps/frontend/components/phase-cross-view-card.tsx`
- `apps/frontend/components/phase-cross-view-chart.tsx`
- `apps/frontend/lib/phase.ts`

Frontend (modified):
- `apps/frontend/app/page.tsx` — J-98 Dashboard restructure (compact summary, cross-view chart, collapsed More-detail)
- `apps/frontend/components/market-phase-card.tsx` — unified `phaseFillVar` to shared `lib/phase`
- `apps/frontend/lib/api.ts` — extends `fetchMarketPhase` with `full` param; adds `timeline_full` field to `MarketPhaseResponse` type

---

## Step 1 — Data Contract check

### Registered values audited

**J-97 Full-history market-phase timeline** (`timeline_full`):
- Blueprint canonical computing module: `apps/backend/app/engine/market_phase.py` `_timeline_series` / `compute_market_phase` `timeline_full` (read verbatim — no new derivation).
- Blueprint canonical serving endpoint: `GET /api/market-phase?full=true`.

Assessment:
- The engine diff (`market_phase.py`) shows `timeline_full` is carried in the SAME `compute_market_phase` return dict, produced by the SAME existing `_timeline_series` call (no second computation). The new `market_phase_full_cached` function is a thin pass-through that calls the SAME `market_phase_cached` — it adds no new computation path.
- The `market_phase_default_payload` helper STRIPS `timeline_full` from the default response via a shallow dict comprehension, keeping the card payload byte-identical.
- `PhaseCrossViewCard` (`phase-cross-view-card.tsx:56`) fetches via `fetchMarketPhase(asof, controller.signal, false, true)` — which resolves to `GET /api/market-phase?full=true`, the registered canonical endpoint.
- The chart (`phase-cross-view-chart.tsx:29`) reads the served `timeline_full` verbatim; no client-side severity, phase, or P(bear) math is present.

No duplicate computation. No non-canonical source. No new endpoint. PASS.

**Regime label / score** (registered: `GET /api/dashboard`):
- `page.tsx` fetches regime values via `fetchDashboard` (`GET /api/dashboard`) at line 67 and renders them in `RegimeGlanceCard`. No recompute. PASS.

**Market Phase / Severity / Filtered P(bear)** (registered: `GET /api/market-phase`):
- `page.tsx` fetches these via `fetchMarketPhase` (no `full=true`, just `GET /api/market-phase`) at line 73 for the compact `PhaseGlanceCard`. These are the same canonical endpoint values.
- The `MarketPhaseCard` detail (relocated into `MoreDetailSection` at `page.tsx:405`) continues to fetch via its own `useEffect`/`fetchMarketPhase` call in the existing `market-phase-card.tsx` (unchanged endpoint).
- No recompute. PASS.

**Phase color mapping** (coherence note): Previously `market-phase-card.tsx` had a private `phaseFillVar` function (a local duplicate of the label→CSS-token mapping). This iter CONSOLIDATED it into the shared `lib/phase.ts` module; the card now imports `phaseFillVar` from `lib/phase` (`market-phase-card.tsx:12`). This is a coherence improvement, not a violation.

The `phaseBadgeVariant` function in `page.tsx` (line 50) and `phaseVariant` in `market-phase-card.tsx` (line 43) are purely presentational badge-variant mappers (string label → "ok"/"warn"/"danger") — they do not compute a canonical stored value; they select a UI component variant. These are display helpers, not data-contract values. No violation.

### New displayed values not in Data Contract

No genuinely new canonical stored value is introduced. The `timeline_full` series is explicitly registered as [TARGET iter-38] in the blueprint's Data Contract (blueprint.md line 391). PASS.

---

## Step 2 — Information Architecture check

### New pages / routes

None. The spec and UI surface map both confirm: "No new page, no new route, no nav change." The Dashboard `/` remains the single home. PASS.

### New surfaces placed correctly

- `PhaseCrossViewCard` is placed on Dashboard `/` at `page.tsx:161`, directly below `MajorIndexesCard`. Dashboard is the registered IA home for J-97 (blueprint line 329, explicitly annotated `[TARGET iter-38]`). PASS.
- `RegimeGlanceCard` and `PhaseGlanceCard` are placed on Dashboard `/` as a compact at-a-glance summary (J-98 restructure). These re-display values from `GET /api/dashboard` and `GET /api/market-phase` — both already registered on the Dashboard home. PASS.
- `MoreDetailSection` is the relocated breadth/sectors/themes/phase-detail content, still on Dashboard `/`. Nothing removed; content repositioned within the same page. PASS.

### Navigation reachability

All new surfaces are on the Dashboard `/`, which is the top-level nav landing page (1 click from any page via the nav logo/home link). The "More detail" section requires 1 additional click to expand — total 2 clicks from any location, within the allowed bound. PASS.

### Duplicate home

No entity gains a second home. Dashboard `/` remains the single home for regime, phase/severity, and the cross-view chart. PASS.

### Parallel shell

No new layout shell introduced. `page.tsx` uses the same page wrapper pattern as before. PASS.

---

## Step 3 — Advisory observations (WARN only)

**WARN — `phaseBadgeVariant` (page.tsx:50) and `phaseVariant` (market-phase-card.tsx:43) are functionally equivalent but not shared.**

Both functions map a phase label to an "ok"/"warn"/"danger" badge variant using the same posture logic. The fill-color mapping was consolidated into `lib/phase.ts` this iteration, but the badge-variant mapping was not. This is not a data-contract violation (badge variant selection is purely presentational, not a canonical stored value), but a minor presentation-layer duplication that could drift if phase labels change. Advisory only.

No other advisory issues observed.

---

## Summary

| Check | Result |
|-------|--------|
| Data Contract: `timeline_full` serves from canonical `GET /api/market-phase?full=true` | PASS |
| Data Contract: no second computation of phase/severity/P(bear) | PASS |
| Data Contract: `market_phase_full_cached` is a pass-through, not a recompute | PASS |
| Data Contract: `market_phase_default_payload` strips the opt-in key only | PASS |
| Data Contract: regime/breadth served from `GET /api/dashboard` | PASS |
| IA: all new surfaces on Dashboard `/` (registered home) | PASS |
| IA: no new page/route/nav section | PASS |
| IA: More-detail section reachable in ≤2 clicks | PASS |
| IA: no duplicate home, no parallel shell | PASS |
| Advisory: `phaseBadgeVariant` / `phaseVariant` badge-variant duplication | WARN |
