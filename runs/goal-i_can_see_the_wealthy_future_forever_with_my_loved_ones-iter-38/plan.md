# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 Execution Plan

Two coupled journeys: **J-97** (Dashboard two-pane synced indexes / phase-severity cross-view, fed by a
new full-history serialization of the market-phase timeline) and **J-98** (Dashboard at-a-glance
restructure that depends on the J-97 chart). Depth **full** (crosses backend + frontend, touches a served
payload shape, adds a new chart primitive). NOT a GOAL_ACHIEVED candidate (J-99/J-100 still unbuilt).
Everything re-displays already-served canonical values — **no new computation, no new endpoint, no new
snapshot column, no rebuild, no new date state**.

## What to Build

**Backend (J-97 serialization)**
- Add a `full: bool = Query(default=False)` param to the EXISTING `GET /api/market-phase`
  (`apps/backend/app/api/market_phase.py`). When `full=true`, additively attach the full causal timeline
  series `[{date, phase, p_bear, severity}]` — `timeline_full` that `compute_market_phase` ALREADY builds
  at `market_phase.py:739` (`_timeline_series(readings, filtered_path, cfg)`) and currently truncates to the
  bounded tail (`timeline = timeline_full[-limit:]`, line 740/771). Read it VERBATIM; no new derivation, no
  recompute.
- Serve it through the SAME `market_phase_cached` / `dataset_version` path (no new cache, no new endpoint).
  Mirror the `/api/indexes?full=true` + `/api/regime-history?full=true` (J-49) precedent exactly.
- The `full=false` default card payload MUST stay **byte-identical** to today (the bounded disclosure tail,
  `total_timeline_dates`, episodes, recovery-turn, retrospective-fence all unchanged). The new field is an
  additive opt-in used only by the J-97 chart.
- The full series stays strictly causal per point; the SMOOTHED/retrospective (J-89) `retrospective_cached`
  path stays structurally fenced — no code path from `retrospective` into the full causal series.

**Frontend (J-97 chart)**
- New `apps/frontend/components/phase-band-primitive.ts`: a config-colored phase-band primitive analogous
  to `regime-band-primitive.ts` (same `ISeriesPrimitive`/background-rect step-function pattern). Maps each
  served timeline point's `phase` label → a band span, reading served, config-driven phase labels/colours
  via the design-token approach in `lib/regime.ts` / globals.css — **NO hardcoded phase list, NO hardcoded
  hex**. NA/empty phase → no band (never a fabricated band). It clips at the as-of x exactly like the regime
  primitive so post-D bands stay display-only behind the marker.
- Render the two-pane synced chart in `index-regime-chart.tsx` (or a thin sibling that reuses it): pane 0 =
  the existing normalized index % lines + stored-regime bands + as-of marker (UNCHANGED, J-44/J-49); pane 1
  = the SAME normalized index lines + phase-colored bands + a 0–100 severity line + the filtered P(bear)
  line — all read from ONE served `GET /api/market-phase?full=true` series. Add pane 1 to the SAME
  `lightweight-charts` chart (use `addSeries(..., { pane: 1 })` / `createPane`) so both panes share ONE time
  scale → zoom/pan is inherently synchronized. The bottom pane carries the SAME `AsOfMarkerPrimitive`.
  Frontend only re-formats — NO client-side return/probability/severity math.
- A new `fetchMarketPhase(asof, signal, full)` helper in `lib/api.ts` (extend the existing
  `MarketPhaseResponse` with the optional `timeline_full` field), and place the cross-view directly below
  `MajorIndexesCard` on the Dashboard.

**Frontend (J-98 restructure — `apps/frontend/app/page.tsx`)**
- First paint shows ONLY: (a) a compact **Market Regime** figure (stored label + 0–100 score from
  `/api/dashboard`) and a compact **Market Phase & Severity** figure (stored phase label + 0–100 severity +
  severity-band label + filtered P(bear) from `/api/market-phase`) — each re-displaying the SAME served
  canonical values, each keeping its **named component breakdown** reachable (reuse `ComponentBreakdown`
  inline-compact or in a popover — never a bare number); then (b) the J-97 cross-view chart.
- Relocate the existing breadth metrics + `CandidateCountsCard` + Top Sectors + Top Themes into a
  **collapsed, expandable "More detail" section** below the chart (same data, same endpoints, only
  repositioned — nothing removed). The `MarketPhaseCard` keeps serving the detail card surface (J-87/J-88
  card unchanged).

## Agents Required

- backend-data: yes -- add the `full` query param to `/api/market-phase` serving `timeline_full` verbatim;
  byte-identical-default guard; tests (full-series equals engine `timeline_full`, default byte-identical,
  tail-invariance/no-lookahead, no smoothed/true-bear value in the full series).
- frontend-ux: yes -- `phase-band-primitive.ts`, the two-pane synced chart, the `fetchMarketPhase(full)`
  helper + type, and the J-98 Dashboard restructure (at-a-glance summary + "More detail" disclosure).
- developer: yes -- single developer owns both (backend + frontend) per the dev agent's combined scope.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/api/market_phase.py` -- add `full: bool = Query(default=False)`; attach `timeline_full`
  verbatim when true via the existing cached path.
- `apps/frontend/components/phase-band-primitive.ts` -- NEW config-colored phase-band primitive (token-driven).
- `apps/frontend/components/index-regime-chart.tsx` -- add pane 1 (same time scale): index lines +
  phase bands + severity line + filtered P(bear) line + as-of marker.
- `apps/frontend/lib/api.ts` -- `fetchMarketPhase(asof, signal, full)` + optional `timeline_full` on
  `MarketPhaseResponse` (and a `MarketPhaseTimelinePoint`-shaped reuse).
- `apps/frontend/lib/regime.ts` (or a small phase helper) -- a config/token-driven phase→fill mapping for
  the band primitive (mirror `regimeBandFill`); no hardcoded hex.
- `apps/frontend/components/major-indexes-card.tsx` (or a new sibling card) -- host the second pane below the
  Major-indexes card; fetch `?full=true` market-phase once.
- `apps/frontend/app/page.tsx` -- J-98 restructure: compact at-a-glance summary first, cross-view chart,
  then collapsed "More detail" with breadth/sectors/candidates/themes.
- `apps/backend/tests/test_api_engine.py` (or `test_market_phase.py`) -- new full-mode + byte-identical-default
  + no-lookahead + fence assertions; update any byte-equality guard ONLY if a served shape actually changes
  (the default must NOT change, so existing guards should NOT trip — the recurring iter-20/23/24/32 lesson).
- `docs/handoffs/goal-…-iter-38-dev.md` -- dev handoff.

## UI Evolution

- New user-facing capability: the reader sees the same index path under BOTH lenses at once — regime (top
  pane) and phase/severity/P(bear) (bottom pane) — on one synchronized chart, and lands on a compact
  at-a-glance regime + phase/severity summary at first paint with supporting detail one click away.
- New information displayed: full-history phase-colored bands, a 0–100 severity line, and the filtered
  P(bear) line over the index chart (a re-format of the already-served market-phase series); a compact
  at-a-glance regime + phase/severity summary header.
- New user actions: zoom / scroll / drag either chart pane (zooms BOTH to the same window — synchronized,
  NOT a new date control); expand / collapse the "More detail" section.
- UI surface changes: Dashboard `/` only — a second chart pane under the Major-indexes card, a restructured
  top-of-page at-a-glance summary, a collapsed "More detail" disclosure. No new page, no new route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse `Card`/`CardHeader`/`CardContent` for the summary figures and "More detail"
  section; reuse `ComponentBreakdown` for the named breakdowns; reuse `lightweight-charts` for the panes and
  the `AsOfMarkerPrimitive` / band-primitive pattern. Use a Disclosure/collapsible (existing
  `usePersistedToggle` idiom or a details/summary) for "More detail".
- Layout: full-width stacked Dashboard — at-a-glance summary row (two compact figures) → cross-view chart
  (two stacked panes, shared time axis) → collapsed "More detail" grid.
- Key visual effects: phase bands as soft background fills (token alpha, matching the regime-band treatment);
  severity + P(bear) as distinct token-colored lines with a legend; vertical as-of marker on the bottom pane
  using the `--warn` family (same as the top pane). No hardcoded hex anywhere.
- States to handle: loading (chart skeleton like the existing card); honest-empty bottom pane when the
  causal timeline is empty/early (no fabricated bands/lines); error (backend-unavailable message, nothing
  fabricated); collapsed/expanded "More detail".

## Risks / Unknowns

- **Second-date-state trap (CRITICAL, J-18):** the synced zoom MUST touch ONLY the visible range. Reject any
  new date `useState`, any `window`/`document` keydown handler, or any write to the global as-of from the
  chart. Keep 0 native `input[type=date]`. (iter-16/J-71 grep check on the diff.)
- **Byte-identical default (recurring iter-20/23/24/32 lesson):** the `full=false` card payload must remain
  byte-identical; the `full` param is additive opt-in, so the existing `test_api_engine.py` byte-equality
  guards should NOT trip. If they do, the default changed — fix the default, do not loosen the guard.
- **lightweight-charts multi-pane:** confirm the installed version supports panes (`pane` series option /
  `addPane`); if not, the two panes must still share ONE chart/time scale (a second chart with a manual
  range-sync subscription is a fallback but is heavier and risks a sync seam — prefer the single-chart pane
  API). Flag in the handoff which API was used.
- **No-magic-numbers (iter-20/21):** the phase-band colours and any severity/P(bear) line styling must come
  from design tokens / served config, never a hardcoded hex or float threshold in an engine CALC_FILE
  (`test_no_magic_numbers` is green and must stay green — but note this iter adds no engine calc literal).
- **Coherence:** J-97 must read the SAME single served market-phase series (no second computation/endpoint
  for phase/severity/P(bear)); J-98 must introduce NO new endpoint / NO new canonical value (pure IA
  reshuffle). Dashboard stays the single home.
- **Full pytest suite gate:** hand the FULL backend pytest suite to the pump nohup-async and gate the next
  evaluator on the FLUSHED `0 failed, EXIT 0` line — never block on the in-flight stream; re-run any
  `test_warmup.py` / `test_data_manager_jobs_pipeline.py` flake in isolation before attributing it here
  (known slow-boot/scanner_runs-race contention).
- **Browser-QA must capture LIVE evidence (iter-36/18 lesson):** this iter is `Frontend Present: yes`; do not
  accept J-97/J-98 on API-layer evidence alone. Scroll the below-the-fold bottom pane into the full
  viewport, md5sum the evidence dir first, and prove the synchronized zoom with TWO byte-DISTINCT
  before/after frames; reject any un-hydrated skeleton.

## Out of Scope (do NOT build here)

- **J-99** (membership-timeline pagination + year/month filter on `/data`) — a separate lean frontend-only iter.
- **J-100** (bounded-resource backend single-flight/cache/worker-thread/memory-cap hardening + concurrency
  load test) — a separate full backend iter; do NOT touch the `/api/data` perf rework here.
- Any change to a canonical score, bucket, setup, pattern, regime label/score, the Risk-Off→Actionable gate,
  the as-of contract, or any stored snapshot value.
- Any new endpoint, new snapshot column, snapshot rebuild (`kind:"rebuild"`), or new date state.
- The SMOOTHED / retrospective (J-89) probability anywhere on the causal full series or the cross-view chart.

## Assumptions (documented, not blocking)

- The `full=true` serialization attaches `timeline_full` to the existing payload (rather than replacing
  `timeline`), keeping the bounded `timeline` tail and `total_timeline_dates` byte-identical. (Mirrors how
  `/api/indexes?full=true` extends, not replaces.)
- The bottom pane reuses the existing `IndexSeries` % lines (already served by `/api/indexes?full=true`) for
  its index lines, and reads phase/severity/P(bear) from `/api/market-phase?full=true` aligned by ISO date.
- "More detail" defaults to collapsed at first paint (per the spec "first paint shows ONLY the summary +
  chart").

## Acceptance Criteria Mapping

| Build item | Satisfies (spec DoD / journeys) |
|---|---|
| `full` param serving `timeline_full` verbatim via cached path | J-97 data contract; "served full, no recompute, no new endpoint" |
| `full=false` default byte-identical (+ test) | "card disclosure tail unchanged"; J-87/J-88 unchanged; byte-equality guards stay green |
| Full series strictly causal + no smoothed/true-bear (+ tail-invariance test) | No-lookahead anti-goal; J-49 fence; J-89 retrospective fence |
| `phase-band-primitive.ts` token/config-colored, NA→no band | J-97 phase bands; No-fabricated-data; config-driven UI vocabulary; `test_no_magic_numbers` |
| Two-pane single-time-scale chart (index lines + phase bands + severity + P(bear) + as-of marker) | J-97 target; pane 0 unchanged (J-44/J-49); synchronized zoom = view transform |
| Synced zoom touches only visible range; 0 native date inputs | CRITICAL J-18; "no second date state" |
| Pane 1 series == card series for overlapping window | J-06 single-source |
| Honest-empty bottom pane on early/empty timeline | J-97 honest-empty; No-fabricated-data |
| J-98 compact at-a-glance summary (regime + phase/severity) with reachable breakdowns | J-98 target; Scores-must-be-explainable; J-06 single-source |
| Breadth/sectors/candidates/themes relocated into collapsed "More detail" (kept, not removed) | J-98 target; IA reshuffle, single home, no new endpoint/value |
| Risk-Off→Actionable, regime/score, snapshots all untouched (additive diff) | J-07; Risk-Off gate; Snapshots immutable; Single source of truth |
| Full pytest `0 failed, EXIT 0`; `tsc --noEmit` EXIT 0 | Standing GOAL_ACHIEVED suite gate; no regressions |
| Required-still-passing live smoke green | J-01, J-06, J-07, J-13, J-18, J-43, J-44, J-49, J-78, J-87, J-88, J-89, J-90, J-15 |
| Dev handoff written | DoD final item |

## Key Test Scenarios

- `GET /api/market-phase?full=true` serves the full causal series byte-identical to `compute_market_phase`'s
  `timeline_full` for the same date (no recompute); `full=false` is byte-identical to today's card payload.
- The full series is strictly causal: removing bars dated > D never changes an earlier point (tail-invariance),
  and it contains NO smoothed/true-bear value (the J-89 fence holds).
- Browser J-97: both panes render; pane 1 shows phase-colored bands + a severity line + a filtered P(bear)
  line over the SAME index lines; zooming/scrolling ONE pane zooms BOTH to the same window (two byte-distinct
  frames); the bottom pane carries the as-of marker; an early as-of with no causal history → honest-empty
  bottom pane.
- Browser J-98: first paint shows ONLY the compact regime + phase/severity summary + the cross-view chart;
  each summary figure exposes its named component breakdown (no bare number); breadth/sectors/candidates/
  themes are present inside the collapsed "More detail" and expand correctly.
- Required-still-passing live smoke: J-01, J-06 (summary figures == served values), J-07 (Risk-Off → 0
  Actionable), J-18 (0 native date inputs; synced zoom adds no date state), J-44/J-49 (pane 0 unchanged +
  full-history + as-of marker), J-87/J-88 (card phase/severity/P(bear) unchanged), J-13/J-43 (as-of switch
  still drives both panes).
- `test_no_magic_numbers` green; `test_db.py` expected-tables guard green (NO new table); `tsc --noEmit`
  EXIT 0; full backend pytest `0 failed, EXIT 0`.
