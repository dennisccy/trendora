**Verdict:** COHERENCE-PASS

---

## Coherence Audit — Iteration 32

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 32
**Snapshot SHA:** bc1d42b8039aac7de9de69b234483c7219da51a9
**Target journeys:** J-91, J-92

---

## Step 1 — Data Contract Check

### J-91 — Downtrend Opportunity study

**Registered contract (blueprint lines 324):**
- Canonical computing module: `research:compute_downtrend_opportunity_study` in `apps/backend/app/engine/research.py`
- Canonical serving endpoint: `GET /api/research/downtrend-opportunity`
- Drill-down: new `kind=downtrend-opportunity` on the EXISTING `GET /api/research/samples`

**What the diff adds:**

- `apps/backend/app/engine/research.py` — `compute_downtrend_opportunity_study` (the ONLY computation site; a pure grouping of the SAME `_event_study_observation_set` observations, additively tagged with causal `market_phase` reads <= D, recomputing no return/excursion/score/regime/phase/signal).
- `apps/backend/app/api/research.py:364` — `GET /api/research/downtrend-opportunity` (the sole serving endpoint; delegates verbatim to `downtrend_opportunity_cached`).
- `apps/frontend/lib/api.ts` — `fetchDowntrendOpportunity` calls `/api/research/downtrend-opportunity` (the canonical endpoint, no client-side recomputation).
- `apps/frontend/app/research/page.tsx:76` — `DowntrendOpportunityLab` fetches via `fetchDowntrendOpportunity`; uses the page's shared `horizon` + `asofCutoff` (no second date state, no new `useState<Date>`; confirmed no window/document keydown listener added).
- `apps/backend/app/engine/samples.py` — `KIND_DOWNTREND_OPPORTUNITY` added; the new `_downtrend_opportunity_samples` builder extends the existing `GET /api/research/samples` with the new cohort kind — count-coherent drill-down, no independent observation grouping.

**Finding:** No duplicate computation. No non-canonical source. The new UI surface reads exclusively from `GET /api/research/downtrend-opportunity`. Angle (c) reuses `compute_recovery_turn_edge` verbatim (no re-derivation). ADDITIVE — J-29/J-63/J-77/J-90 figures and existing samples drill-downs are byte-identical (asserted in tests). No violation.

---

### J-92 — Macro series

**Registered contract (blueprint line 325):**
- Canonical computing module: new `FredProvider` in `data_providers/` writing the STANDALONE `macro_series` table + `^TNX`/`^DXY`/`^VXN` as plain `DailyPrice` bars.
- Serving: macro provider rides the EXISTING import path / provider catalog (`GET /api/data`, `POST /api/data/jobs*`); no new public read endpoint dedicated to macro.
- `MacroSeries` standalone table registered in `test_db.py` expected-tables (`MACRO_TABLES`, NOT `_ADDITIVE_COLUMNS`).

**What the diff adds:**

- `apps/backend/app/data_providers/__init__.py:82` — `FredProvider` registered in `make_provider` under name `"fred"` (the single registration point; FRED key read from environment, lazy-imported).
- `apps/backend/app/models.py:475` — `MacroSeries` standalone table (standalone `create_all`-managed, separate from the `_ADDITIVE_COLUMNS` pattern).
- `apps/backend/tests/test_db.py:53` — `MACRO_TABLES = {"macro_series"}` (the required expected-tables guard added, conforming to the J-92 contract and the iter-20 lesson).
- `apps/backend/app/api/data.py:109` — `"macro": data_manager.compute_macro_availability(session, cfg)` added to the `GET /api/data` overview payload (catalog/availability metadata only; no key value; the `MacroFeedPanel` reads this field from the existing `GET /api/data` response — canonical endpoint, no new endpoint).
- `apps/frontend/app/data/page.tsx:443` — `MacroFeedPanel` reads `state.data.macro` from the same `GET /api/data` response; shows env-var NAME only, never the key value.
- `apps/backend/app/engine/market_phase.py:130` — `MacroSeries` queried for severity + regime-switching inputs, config-default-OFF; with macro absent/disabled figures are byte-identical to the price/breadth/VIX-only path (asserted).

**Finding:** The macro series table has a single canonical writing path (FredProvider via the existing import machinery). The macro availability metadata is an additive field on the existing `GET /api/data` endpoint. No new read endpoint for macro data. No duplicate computation. No non-canonical source. No violation.

---

### New values introduced — registration check

| New value | Blueprint row | Status |
|-----------|--------------|--------|
| Per-(phase/severity-band/P(bear)-band × angle) forward-return stats (n, mean, median, hit-rate, expectancy, downside-only risk-adjusted, max-drawdown) | Blueprint line 324 (J-91 row) | Registered — PASS |
| `MacroSeries(symbol, date, value, source, published_date)` | Blueprint line 325 (J-92 row) | Registered — PASS |

No unregistered new displayed value.

---

## Step 2 — Information Architecture Check

### New UI surfaces from the diff

| Surface | Home in blueprint IA | Reachability | Finding |
|---------|---------------------|--------------|---------|
| Downtrend Opportunity panel on `/research` | Research (`/research`) — blueprint line 270 | 1 click from sidebar (sidebar.tsx line 37: `{ href: "/research", label: "Research" }`) | PASS |
| `MacroFeedPanel` on `/data` | Data Manager (`/data`) — blueprint line 272 | 1 click from sidebar (Data Manager nav link established in prior iterations) | PASS |
| `downtrend-opportunity` cohort kind on `/research/samples` | Samples (`/research/samples`, link-reached) — blueprint line 271 | 2 clicks: Research → N= chip | PASS |

**No new top-level nav section.** No new page. No new route. All surfaces land on their blueprint-designated existing homes. The sidebar requires no update (existing Research and Data Manager links are present and sufficient).

**No parallel shell.** All new components use the established page shell / layout inherited from `/research` and `/data`.

**No duplicate home.** The Downtrend Opportunity study is a new feature added to the Research home; it does not duplicate any existing entity's canonical home.

---

## Step 3 — Advisory Observations

No advisory issues found. The conditioning-dimension selector (`dimension` state in `DowntrendOpportunityLab`) is correctly a cohort/view selector, not a date state, consistent with the J-18 anti-goal. The macro feed panel prominently labels the env-var NAME without echoing any key value, consistent with the No-secrets anti-goal.

---

## Summary

- Part A (Data Contract): 0 violations. J-91 uses a single canonical computing module and serving endpoint; the frontend reads only from the canonical endpoint. J-92 uses a single canonical writing path and rides the existing import/provider endpoint. Both new values are registered in the blueprint.
- Part B (Information Architecture): 0 violations. All new surfaces are panel/component additions to existing blueprint-designated pages reachable in ≤ 1 click from the sidebar. No new top-level nav, no new page, no parallel shell, no duplicate home.
- Part C (Advisory): 0 notes.
