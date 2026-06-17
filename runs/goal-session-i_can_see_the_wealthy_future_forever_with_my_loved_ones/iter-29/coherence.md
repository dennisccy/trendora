**Verdict:** COHERENCE-PASS

## Iteration 29 — Coherence Audit

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration index: 29
Target journeys: J-87 (Market Phase & Severity panel) + J-88 (Filtered P(bear))
Snapshot SHA: 6a2c115c2c6571497275897f9d714b41969fe20b

---

## Part A — Data Contract check

### New values registered in this iteration

The blueprint (as updated in this iteration) registers two new Data Contract rows:

1. **Market phase + drawdown-severity** (J-87): discrete phase label, 0-100 severity, named component breakdown.
   - Canonical computing module: `app/engine/market_phase.py` — `compute_market_phase` / `market_phase_cached`.
   - Canonical serving endpoint: `GET /api/market-phase`.

2. **Filtered P(bear) 0-1** (J-88): deterministic forward Hamilton FILTERED probability + observation vector.
   - Same canonical computing module and serving endpoint as J-87.

### Checks for duplicate computation

- `apps/backend/app/engine/market_phase.py` is the sole computing module. The regime input is read VERBATIM from `ScannerRun.regime_score` (line 146: `regime_risk = (100 - run.regime_score) / 100`) — `score_regime` is never called. No grep hit for `score_regime`, `compute_regime`, or `_score_regime` in the new module. No duplicate computation of any existing canonical value.
- The cache dataset-version stamp re-uses `_dataset_version` imported from `app.engine.research` (line 51 of `market_phase.py`). Single-sourced — not a second computation of that stamp.
- `MarketPhaseCache` is a standalone cache table (not a new snapshot column on `scanner_runs`/`scanner_results`/`forward_returns`). It is registered in `test_db.py` per the surface map. The `_ADDITIVE_COLUMNS` trap does not apply (separate table).
- `market_phase.py` added to `test_no_magic_numbers` `CALC_FILES` per the surface map.

### Checks for non-canonical source in the UI

- `apps/frontend/components/market-phase-card.tsx` fetches only `fetchMarketPhase` → `GET /api/market-phase`. No fetch from any other endpoint for phase/severity/P(bear) values.
- `PBearBadge` (market-phase-card.tsx line 141) uses `>= 2/3` and `>= 1/3` as PRESENTATION-only colour-band thresholds on the already-served P(bear) float — it does not recompute P(bear). This is a re-format of the canonical served value, not a canonical computation violation (per the "Re-format is fine" rule).
- No client-side recomputation of severity, phase, or P(bear) found.

**Part A result: no violations.**

---

## Part B — Information Architecture check

### New UI surface

The sole new UI surface is the `MarketPhaseCard` component, mounted in `apps/frontend/app/page.tsx` on the Dashboard route `/`.

- **Canonical home:** the blueprint IA registers this panel under Dashboard (`/`) — "J-87 NEW Market Phase & Severity panel" and "J-88 the same panel gains a 0-1 FILTERED P(bear)". The panel lives on the correct IA home.
- **No new route/page:** no new route is introduced. The panel is embedded in the existing Dashboard page. Reachability check is trivially satisfied — the Dashboard is 1 click from the sidebar (the top nav entry).
- **No new nav section:** the sidebar (`apps/frontend/components/sidebar.tsx`) has no new entry for market-phase. Correct — the blueprint explicitly states "NO new top-level nav section" for this cluster.
- **No duplicate home:** no second page exists for market phase/severity. The one panel is on the Dashboard, its sole registered home.
- **No parallel shell:** the panel uses the existing Card/CardHeader/CardContent shell. No new layout frame introduced.

**Part B result: no violations.**

---

## Part C — Advisory observations (WARN only)

- **Presentation colour thresholds in PBearBadge:** `market-phase-card.tsx:141` uses the fractional literals `2/3` and `1/3` as colour-band cutoffs for the P(bear) badge. These tune only the visual palette (green / amber / red) of a value the backend computed; they recompute no canonical value. This is a presentation decision, not a data-contract concern. Advisory only.

No formatting drift, label inconsistency, or undiscoverable-feature concerns observed. The J-87/J-88 panel follows the established card shell and uses `formatIsoDate` (lib/dates.ts) for all date display (J-42 intact).

---

## Summary

| Check | Result |
|---|---|
| Duplicate computation of any existing canonical value | PASS — not found |
| Non-canonical source for any new displayed value | PASS — sole source is `GET /api/market-phase` |
| New value duplicating an existing registered concept | PASS — phase/severity/P(bear) are genuinely new |
| New page/route with no nav path | N/A — no new page/route |
| Duplicate home for an existing entity | PASS — not found |
| Parallel shell | PASS — existing card shell used |

No objective violations (Part A or Part B). One advisory presentation note (Part C).
