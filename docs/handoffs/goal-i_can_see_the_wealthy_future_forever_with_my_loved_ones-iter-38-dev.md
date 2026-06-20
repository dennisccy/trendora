# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Date:** 2026-06-20
**Agent:** developer
**Status:** complete

## What Was Built

J-97 (Dashboard two-pane synced regime × phase cross-view) + J-98 (Dashboard at-a-glance restructure).

**Backend (J-97 serialization)**
- Added `full: bool = Query(default=False)` to the EXISTING `GET /api/market-phase`
  (`apps/backend/app/api/market_phase.py`). When `full=true`, the payload ADDITIVELY carries the
  full-history causal timeline series `timeline_full` (`[{date, phase, p_bear, severity}]`).
- `timeline_full` is read VERBATIM from the SAME `compute_market_phase` derivation that already builds it
  (`_timeline_series(readings, filtered_path, cfg)` — the SAME series the bounded card `timeline` tail is
  sliced from). No new derivation, no recompute, no new endpoint, no new cache, no new snapshot column,
  no rebuild.
- Served through the SAME `market_phase_cached` / `dataset_version` path: `compute_market_phase` now
  includes `timeline_full` in its (cached) payload; the new helper `market_phase_full_cached` returns the
  cached payload with the full series, and `market_phase_default_payload` STRIPS the `timeline_full` key so
  the default (`full=false`) card response stays BYTE-IDENTICAL to today. Mirrors the
  `/api/indexes?full=true` + `/api/regime-history?full=true` (J-49) clamp-optional precedent.
- The full series stays strictly causal per point; the SMOOTHED/retrospective (J-89) path remains
  structurally fenced — no code path from `retrospective` into the full causal series, no `p_bear_smoothed`
  on any full-series point.

**Frontend (J-97 chart)**
- New `apps/frontend/lib/phase.ts`: the ONE shared phase-label → stress-posture → token/colour mapping
  (mirrors `lib/regime.ts`). `phaseFillVar` (CSS `var()` for the card SVG), `phaseColor`/`phaseBandFill`
  (resolved rgba for the canvas band primitive), and a posture legend. NO hardcoded phase list as a source
  of truth, NO hardcoded hex outside the design-token palette mirror. `market-phase-card.tsx` now imports
  `phaseFillVar` from here (deleted its private duplicate) so the card timeline and the cross-view bands use
  ONE mapping (coherence).
- New `apps/frontend/components/phase-band-primitive.ts`: a config-coloured phase-band `ISeriesPrimitive`
  (background-rect step function), analogous to `regime-band-primitive.ts`. Maps each served timeline
  point's `phase` → a band span via `phaseBandFill`; NA/empty phase → NO band. Clips at the as-of x.
- New `apps/frontend/components/phase-cross-view-chart.tsx`: ONE `lightweight-charts` chart with TWO panes
  sharing ONE time scale. Pane 0 = index % lines + stored-regime bands + as-of marker (the J-44/J-49 lens,
  unchanged). Pane 1 = the SAME index % lines + phase-coloured bands + a 0–100 severity line + the filtered
  P(bear) line, all from the SAME served `?full=true` series; the bottom pane carries the SAME
  `AsOfMarkerPrimitive`. Severity (0–100) and P(bear) (0–1) are on dedicated invisible overlay price scales
  so they don't distort the % index scale. The synced zoom is the shared time scale (a view transform).
- New `apps/frontend/components/phase-cross-view-card.tsx`: hosts the chart below `MajorIndexesCard`;
  fetches `/api/indexes?full=true`, `/api/regime-history?full=true`, and `/api/market-phase?full=true`;
  loading / honest-empty / error states; persisted hide toggle.
- Extended `apps/frontend/lib/api.ts`: `fetchMarketPhase(asof, signal, retrospective, full)` and the
  optional `timeline_full?: MarketPhaseTimelinePoint[]` on `MarketPhaseResponse`.

**Frontend (J-98 restructure — `apps/frontend/app/page.tsx`)**
- First paint shows ONLY: (a) a compact **Market Regime** figure (stored label + 0–100 score from
  `/api/dashboard`) and a compact **Market Phase & Severity** figure (stored phase + 0–100 severity +
  filtered P(bear) from `/api/market-phase`) — each re-displaying the SAME served canonical values, each
  keeping its named component breakdown REACHABLE via an inline `<details>` disclosure (never a bare
  number); then (b) the J-44 Major-indexes card + the J-97 cross-view chart.
- The breadth metrics + Candidate Counts + Top Sectors + Top Themes + the full `MarketPhaseCard` detail are
  relocated into a **collapsed, expandable "More detail"** section below the chart (same data, same
  endpoints, only repositioned — nothing removed). Defaults collapsed (persisted toggle).

## Files Changed

- `apps/backend/app/api/market_phase.py` -- added the `full` query param; serves `timeline_full` verbatim
  via the cached path; default strips the key (byte-identical).
- `apps/backend/app/engine/market_phase.py` -- `compute_market_phase` carries `timeline_full` (available +
  NA paths); new `market_phase_full_cached` + `market_phase_default_payload` (strip helper).
- `apps/backend/tests/test_market_phase.py` -- 6 new tests (full default byte-identical, full serves
  `timeline_full` verbatim == engine, no smoothed/true-bear on full, full tail-invariance/no-lookahead,
  honest-empty early full).
- `apps/frontend/lib/phase.ts` -- NEW shared phase colour mapping (token-driven).
- `apps/frontend/lib/api.ts` -- `fetchMarketPhase(full)` + `MarketPhaseResponse.timeline_full`.
- `apps/frontend/components/phase-band-primitive.ts` -- NEW config-coloured phase-band primitive.
- `apps/frontend/components/phase-cross-view-chart.tsx` -- NEW two-pane synced chart.
- `apps/frontend/components/phase-cross-view-card.tsx` -- NEW host card (fetches the 3 full-mode sources).
- `apps/frontend/components/market-phase-card.tsx` -- imports `phaseFillVar` from `lib/phase` (deleted the
  private duplicate; single mapping).
- `apps/frontend/app/page.tsx` -- J-98 restructure (at-a-glance summary → cross-view → collapsed "More
  detail").

## Tests Run

Command (backend, from project-template): `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
- Targeted market-phase (incl. 6 new + determinism/cache/tail-invariance regressions):
  **15 passed** (`tests/test_market_phase.py -k "full or timeline or cache or determinism or api_default or no_lookahead"`).
- Anti-goal guards: `test_no_magic_numbers` + `test_db` expected-tables guard: **11 passed** (no new magic
  literal, no new table).
- FULL backend pytest suite: handed to a `nohup`-async run (`/tmp/iter38-full-pytest.log`, ~34 min) —
  gate the evaluator on the flushed `FULL_SUITE_EXIT=0` / `0 failed` line per the standing suite-gate
  lesson; do NOT block on the in-flight stream. Re-run any `test_warmup.py` /
  `test_data_manager_jobs_pipeline.py` flake in isolation before attributing it here.

Command (frontend): `cd apps/frontend && npx tsc --noEmit` → **EXIT 0** (clean, whole app).

## Known Issues

- **Live browser QA still required (this iter is `Frontend Present: yes`).** I did NOT start the live dev
  servers (the host runs on ports 8835/3835 and the memory warns against casual `/api/data` probes + broad
  pkill on this multi-project machine). The two-pane render + the SYNCHRONIZED zoom (two byte-DISTINCT
  before/after frames, bottom pane scrolled into the full viewport) MUST be captured live by browser-qa —
  do not accept J-97/J-98 on API/source evidence alone (iter-36/18 lesson).
- **lightweight-charts multi-pane API:** installed version is **5.2.0**, which supports panes via the
  `addSeries(definition, options, paneIndex)` overload — used the SINGLE-chart pane API (paneIndex 0/1) so
  both panes share ONE time scale (no second-chart range-sync seam).
- **J-18 static check (self-verified on the diff):** no new date `useState`, no `window`/`document` keydown
  listener (the only `document.` use is `getComputedStyle` for CSS tokens), no `setAsOf` write from the
  chart/card, and 0 native `input[type=date]`. The synced zoom touches only the visible range.
- **Severity / P(bear) overlay scales:** on pane 1 the severity (0–100) and P(bear) (0–1) lines ride
  dedicated invisible overlay price scales so they don't distort the % index scale they share the pane
  with — they remain a re-format of served values (no client math).
- Performance: untouched. This iter adds NO new computation and does NOT touch the `/api/data` path
  (J-100 is a separate later iter); the `?full=true` series is the already-cached `timeline_full`.
