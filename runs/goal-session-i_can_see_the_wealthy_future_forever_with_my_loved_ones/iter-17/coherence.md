# Iteration 17 — Coherence Audit

**Iteration:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-17
**Date:** 2026-06-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Changed files: `apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/components/price-chart.tsx`, `apps/frontend/tailwind.config.ts`, `apps/frontend/app/globals.css`. Backend diff is empty (confirmed via `git diff <sha> -- apps/backend/`).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-date availability counts — `GET /api/data/availability` | OK | `availability-heatmap.tsx:15,29` — explicit "pure re-style of the SAME payload: no new fetch, no recompute"; component accepts data as a prop, makes no fetch of its own; all J-61/J-70 `data-*` attributes preserved verbatim |
| Price/MA/volume series — `GET /api/stocks/{ticker}/bars` | OK | `price-chart.tsx:127` — "no fetch, no recompute"; `buildHover` (line 139) reads OHLCV and MA values from the already-served `bars` and `ma` arrays that the chart already plotted; no additional API call introduced |
| % change displayed in hover box | OK (display derivation, not a stored canonical value) | `price-chart.tsx:144–145` — `(bar.close - prevClose) / prevClose * 100`; the spec and blueprint both explicitly class this as "presentation math over two already-served closes — acceptable, not a stored canonical value"; analogous to the existing index-chart tooltip |
| Heat token CSS vars (`--heat-0` … `--heat-5`) | OK — new presentation tokens, not a new computed value | `apps/frontend/app/globals.css:21–31` — hex literals are the ONLY source (tokens defined once; cells reference Tailwind class `bg-heat-N`, never inline hex); no canonical score or coverage figure recomputed; this is invariant-10–compliant design-token definition |
| All other registered Data Contract values | Not touched | Backend diff empty; no new endpoint, no engine change; no other frontend component modified |

No duplicate computation, no non-canonical source, no synonym/re-derivation of a registered value. The % change display derivation in the hover box was anticipated and pre-registered in the blueprint's J-76 row as acceptable presentation math.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — heatmap multi-hue scale + legend (J-74) | OK | No new route. Enhancement to the existing Data Manager card. Nav files (`apps/frontend/components/sidebar.tsx`, router) unchanged — confirmed by `git diff <sha> --name-only` returning no nav or routing file. IA entry: "Data Manager /data … J-74 heatmap multi-hue coverage scale + legend + per-bucket legible day numbers [TARGET iter-17]" |
| `/stocks/[ticker]` — price-chart hover box (J-76) | OK | No new route. Enhancement to the existing Stock Detail chart. IA entry: "Stock Detail /stocks/[ticker] … J-76 per-bar price-chart hover box [TARGET iter-17]" — row-reached, already navigable via the Stocks leaderboard in ≤2 clicks |

No new page, no new top-level nav section, no duplicate home, no parallel shell introduced. Both features land on their blueprint-registered existing homes.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The hex literals in `globals.css` are the single canonical definition for the heat tokens (not per-cell magic numbers), which satisfies invariant 10. The `pointer-events-none` absolute positioning of the hover box (`price-chart.tsx:335`) correctly avoids obscuring the J-20 as-of marker and J-45 regime bands as required.
