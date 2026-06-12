**Verdict:** COHERENCE-PASS

## Coherence audit — iter-6 (J-49 + nested-button fix)

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration: 6
Snapshot SHA: 1a60a9a71d0d6481d9c0b56d43bbb181118b440c

---

### Step 1 — Data Contract check

**"Normalized index display series"**
- Registered canonical module: `indexes:compute_index_series`
- Registered canonical endpoint: `GET /api/indexes`
- This iteration adds a `full: bool = False` parameter to the same function (`apps/backend/app/engine/indexes.py:67`) and the same endpoint (`apps/backend/app/api/indexes.py:27`). When `full=True` the upper-bound bar source switches from `bars_asof` to `bars_through_latest` (already a registered helper in `app/engine/prices.py:164`). The normalization logic, rebase base, and range-preset logic are identical in both modes; only the upper date bound of the served window changes. No second computing module; no second endpoint; no client-side return math.
- The dashboard card (`major-indexes-card.tsx:53`) is the only consumer that passes `full=true`. No other surface calls `fetchIndexes` with this flag.
- **No violation.**

**"Regime history series"**
- Registered canonical module: `regime_history:get_regime_history`
- Registered canonical endpoint: `GET /api/regime-history`
- Same pattern: `full: bool = False` is added to `apps/backend/app/engine/regime_history.py:35` and `apps/backend/app/api/regime_history.py:24`. The `full=True` path removes the `WHERE asof_date <= resolved` SQL clause on the same immutable `scanner_runs` table; the stored `label` and `score` fields are read verbatim in both modes. The resolved `asof_date` is still echoed in the response (the client uses it to draw the marker). No recomputation; no second path.
- Stock-detail consumer (`apps/frontend/app/stocks/[ticker]/page.tsx:376`) calls `fetchRegimeHistory` without `full=true`, preserving the clamped J-45 behavior.
- **No violation.**

**New display elements: vertical as-of marker**
- `AsOfMarkerPrimitive` (`apps/frontend/components/asof-marker-primitive.ts`) draws a positional vertical line at the date value already received from the server-echoed `asof_date`. It computes nothing — it is pure display chrome (a CSS-styled canvas line). This is not a new registered value and does not duplicate any existing registered value.
- **No violation; not a data-contract concern.**

**`RegimeBandPrimitive.setData` change**
- The call in `index-regime-chart.tsx:149` changes from `bandPrimitive.setData(regimePoints.filter(...), asofDate)` to `bandPrimitive.setData(regimePoints, null)`. The `regimePoints` array still comes from the canonical `fetchRegimeHistory` result (the full set when `full=true`). Passing `null` as the clip bound is a rendering-layer decision, not a separate data source. **No violation.**

---

### Step 2 — Information Architecture check

**Changed surfaces:**
1. Dashboard `/` — `major-indexes-card.tsx` and `index-regime-chart.tsx` updated.
2. Stocks `/stocks` — `app/stocks/page.tsx` `SortHeader` nested-button restructure.

Both surfaces have registered canonical homes in the blueprint IA:
- Dashboard `/` is the first entry under the nav skeleton.
- Stocks `/stocks` is the second entry.

**No new page or route was introduced.** The sidebar (`apps/frontend/components/sidebar.tsx`) is unchanged; all existing nav entries remain and are reachable in ≤1 click.

**No parallel shell** — the changes are component-internal modifications to existing pages.
**No duplicate home** — no entity that already had a canonical home now has a second one.

---

### Step 3 — Subjective observations (advisory only)

- The new `AsOfMarkerPrimitive` uses the `--warn` palette token and "as-of \<date\>" label family matching `price-chart.tsx`'s J-20 divider. Visual language is consistent across surfaces. No formatting drift.
- The blueprint bookkeeping update (two Data Contract rows + one IA line changing "iter-5+" to "iter-6 in flight") is an additive annotation consistent with the convention accepted in prior coherence audits. No structural contract change.

---

### Summary

No Part A or Part B violations found. The `full` query parameter is a narrow, well-documented extension of the two registered canonical serving functions and endpoints — the same module, same endpoint, same stored values, with only the served date-range upper bound conditionally widened for the dashboard surface. The stock-detail clamped path (J-45) is demonstrably preserved. The nested-button fix is data-free UI restructuring. No new routes, no nav changes, no duplicate computations.
