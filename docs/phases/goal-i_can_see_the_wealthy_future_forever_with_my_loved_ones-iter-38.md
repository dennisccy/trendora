# Goal Iteration 38 — Dashboard two-pane synced cross-view (J-97) + at-a-glance restructure (J-98)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 38
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-97, J-98
- **Required-still-passing journeys:** J-01, J-06, J-07, J-18, J-13, J-43, J-44, J-49, J-78, J-87, J-88, J-89, J-90, J-15
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking — all of which remain computed from bars with date ≤ D — and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)*
  - **Chart pane-zoom / range-sync is a view transform, not a date control** (J-97). Synchronizing the visible date range across the Dashboard's stacked chart panes changes only the **displayed window**; it MUST NOT introduce a second date state, write the global as-of, or feed any as-of-scoped computed value — the single global as-of switcher stays the only date control, and the full-history context past the as-of stays display-only behind the as-of marker.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*

## GOAL

Below the existing Major-indexes & regime chart, render a second stacked, time-axis-synced chart pane showing the same index lines under phase-colored bands + a 0–100 severity line + the filtered P(bear) line (J-97), and reorganize the Dashboard so the first paint shows a compact at-a-glance regime + phase/severity summary above that cross-view chart with the breadth/sectors/candidates/themes cards relocated into a collapsed "More detail" section (J-98) — all re-displaying already-served canonical values with no new computation.

## BACKGROUND

The prior session reached GOAL_ACHIEVED at iter-37 (J-01..J-96, 93/96; J-22/J-23/J-24 data-walled non-vetoing). `docs/goal.md` has been extended in-place with four NEW buildable Must-haves J-97..J-100 (goal.md:2285-2327, explicitly "NOT data-dependent" — none may be recorded blocked-NA, none may halt). Per the iter-22 lesson, these are `unknown` buildable Must-haves with no journey-history entry and no positive evidence, so they drive CONTINUE and are this resume's new work. iter-38 takes the riskiest, most coupled pair first: J-97 (a backend `?full=true` serialization of the market-phase timeline + a new two-pane synced frontend chart) and J-98 (a structural Dashboard restructure that depends on J-97's chart). Because they cross backend + frontend, touch a served-payload shape, and add a new chart primitive, depth is **full**. J-99 (lean, frontend-only view transform on `/data`) and J-100 (full backend perf/stability hardening + concurrency load test) follow in later iterations. iter-37 was COHERENCE-PASS, so no consolidation pass is owed.

## IN SCOPE

### Backend
- [ ] Add a `full: bool = Query(default=False)` parameter to `GET /api/market-phase` (in `apps/backend/app/api/market_phase.py`) that, when true, additively serves the **full-history** causal timeline series `[{date, phase, p_bear, severity}]` for the Dashboard cross-view — a clamp-optional SERIALIZATION of the `timeline_full` the `market_phase` engine ALREADY computes via `_timeline_series` (read VERBATIM; no new derivation, no recompute). Mirror the existing `GET /api/indexes?full=true` + `GET /api/regime-history?full=true` (J-49) clamp-optional precedent. Serve from the SAME `dataset_version` cache (the `market_phase_cached` path) — NO new endpoint, NO new cache, NO new snapshot column, NO rebuild.
- [ ] Keep the Market-Phase CARD's bounded disclosure tail unchanged (the card payload `full=false` default stays byte-identical to today). The full series is an additive opt-in field/mode used only by the J-97 chart.
- [ ] The full series stays strictly causal per point (each point observed from its own ≤ D snapshot) and the SMOOTHED / retrospective (J-89) path stays structurally fenced — the full causal series MUST NOT read or expose any smoothed/true-bear value.

### Frontend
- [ ] Add a config-colored **phase band primitive** (`apps/frontend/components/phase-band-primitive.ts`) analogous to the existing stored-regime `regime-band-primitive.ts` — maps each timeline point's served `phase` label → a band span, reading the served, config-driven phase labels/colours verbatim (no hardcoded phase list or hex; reuse the design-token approach in `lib/regime.ts` / globals.css tokens). NA/empty phase → no band, never a fabricated band.
- [ ] Render the J-97 **two-pane synced chart**: pane 0 = the existing normalized index % lines + stored-regime bands + as-of marker (J-44/J-49, unchanged); pane 1 = the SAME normalized index lines + phase-colored bands + a 0–100 severity line + the filtered P(bear) line — every J-97 series read from the SAME single served full-history market-phase series (`GET /api/market-phase?full=true`), the frontend only re-formats (NO client-side return/probability/severity math). Reuse `index-regime-chart.tsx` + `asof-marker-primitive.ts`; add pane 1 to the SAME `lightweight-charts` chart so the two panes share ONE time scale (zoom/pan inherently synchronized). The bottom pane carries the SAME as-of marker the top pane uses.
- [ ] Place this cross-view directly below the existing `MajorIndexesCard` on the Dashboard.
- [ ] J-98 Dashboard restructure (`apps/frontend/app/page.tsx`): first paint shows ONLY (a) a compact **Market Regime** figure (stored label + 0–100 score, from `GET /api/dashboard`) and a compact **Market Phase & Severity** figure (stored phase label + 0–100 severity + severity-band label + filtered P(bear), from `GET /api/market-phase`) — each re-displaying the SAME server-computed canonical values, each keeping its **named component breakdown** reachable inline-compact or via a popover (reuse `ComponentBreakdown` — no bare number); then (b) the J-97 cross-view chart. Relocate the existing breadth metrics + `CandidateCountsCard` + Top Sectors + Top Themes into a **collapsed, expandable "More detail" section** below the chart (same data, same endpoints, only repositioned; nothing removed).

### New user-facing capability
The reader sees the same index path under both lenses at once — the regime lens (top pane) and the phase/severity/P(bear) lens (bottom pane) — on one synchronized chart, and lands on a compact at-a-glance summary (regime + phase/severity) at first paint with the supporting breadth/sectors/candidates/themes detail one click away.

### New information displayed
The full-history phase-colored bands, the 0–100 severity line, and the filtered P(bear) line over the index chart (a re-format of the already-served market-phase series); a compact at-a-glance regime + phase/severity summary header.

### New user actions
Zoom / scroll / drag either chart pane (zooms BOTH to the same window — synchronized, not a new date control); expand / collapse the "More detail" section. No new date control.

### UI surface changes
Dashboard `/` only: a new second chart pane under the Major-indexes card, a restructured top-of-page at-a-glance summary, and a collapsed "More detail" disclosure. No new page, no new route, no nav change.

### Product surface delta
The Dashboard becomes a faster-to-read at-a-glance view with a richer market-context cross-view chart, while every supporting figure stays present (relocated, not removed).

### Blueprint conformance
Both journeys live on the EXISTING Dashboard `/` home (Information Architecture — registered, annotated [TARGET iter-38]). No new top-level nav section, no new page, no nav-skeleton change. J-99/J-100 are pre-registered on their existing homes for later iterations.

### Data-contract additions
- **J-97 Full-history market-phase timeline** — the per-snapshot-date causal series `[{date, phase, p_bear, severity}]` served full. Single canonical computing module: `apps/backend/app/engine/market_phase.py` `_timeline_series` / `compute_market_phase` `timeline_full` (read verbatim — the SAME series the Market-Phase card + the J-89 timeline already read; NOT a second computation). Single serving endpoint: `GET /api/market-phase?full=true` (a `full` query param on the EXISTING endpoint, the `/api/indexes?full=true` + `/api/regime-history?full=true` J-49 precedent — no new endpoint). Registered in `blueprint.md` Data Contract.
- J-98 introduces **no** new displayed value — it re-displays the EXISTING `/api/dashboard` regime label+score and the EXISTING `/api/market-phase` phase/severity/band/P(bear), read from their already-registered canonical sources. The Dashboard component breakdowns reuse the existing served `components`.
- Never introduce a second computation or endpoint for any value already in the Data Contract — read the registered canonical source.

## OUT OF SCOPE

- J-99 (membership-timeline pagination + year/month filter on `/data`) — a separate lean frontend-only iteration.
- J-100 (bounded-resource backend single-flight/cache/worker-thread/memory-cap hardening + concurrency load test) — a separate full backend iteration; do NOT attempt the `/api/data` perf rework here.
- Any change to a canonical score, bucket, setup, pattern, regime label/score, the Risk-Off→Actionable gate, the as-of contract, or any stored snapshot value.
- Any new endpoint, new snapshot column, snapshot rebuild (`kind:"rebuild"`), or new date state.
- The SMOOTHED / retrospective (J-89) probability anywhere on the causal full series or the live cross-view chart.

## DEFINITION OF DONE

- [ ] Target journeys J-97, J-98 pass via browser-qa-agent on LIVE rendered evidence (two-pane chart with both panes rendered + synchronized zoom; restructured at-a-glance summary + collapsed "More detail").
- [ ] Required-still-passing journeys remain green — especially the CRITICAL J-18 (exactly one date selector: 0 native `input[type=date]`; the synced zoom is a view transform, NOT a second date state) and J-07 (Risk-Off → zero Actionable, untouched).
- [ ] J-06 single-source holds: the compact Market Regime / Market Phase & Severity figures equal the Dashboard's existing served values for the same date; pane 1's series equal the Market-Phase card's series for the overlapping window.
- [ ] J-49 no-lookahead holds: pane 1 post-as-of points render display-only behind the as-of marker and feed no as-of value; an honest-empty timeline yields an honest-empty bottom pane.
- [ ] No anti-goal violation introduced (verify the diff is additive — no scoring/regime/snapshot change; no magic-number literal in any engine/calc file or new hardcoded phase/hex in the band primitive).
- [ ] Unit/integration tests pass; the FULL backend pytest suite flushes `0 failed, EXIT 0` (the standing GOAL_ACHIEVED gate); no regressions. `tsc --noEmit` EXIT 0.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-97 (both panes render; pane 1 shows phase-colored bands + severity line + filtered P(bear) line over the SAME index lines; zooming/scrolling ONE pane zooms BOTH to the same window; the bottom pane carries the as-of marker; an early as-of with no causal history → honest-empty bottom pane), J-98 (first paint shows ONLY the compact regime + phase/severity summary + the cross-view chart; each summary figure exposes its named component breakdown — no bare number; the breadth/sectors/candidates/themes cards are present inside the collapsed "More detail" section and expand correctly). Required-still-passing live smoke: J-01 (dashboard at a glance), J-06 (single source: summary figures == served values), J-07 (Risk-Off → 0 Actionable), J-18 (0 native date inputs, one global as-of; the synced zoom adds no date state), J-44/J-49 (pane 0 unchanged, full-history + as-of marker), J-87/J-88 (card phase/severity/P(bear) unchanged), J-13/J-43 (as-of switch still drives both panes).
- **Unit/integration:** assert `GET /api/market-phase?full=true` serves the full causal series byte-identical to `compute_market_phase`'s `timeline_full` for the same date (no recompute); assert `full=false` (the card default) is byte-identical to today's served card payload (the card disclosure tail is unchanged); assert the full series is strictly causal/no-lookahead per point (tail-invariance: removing bars dated > D never changes an earlier point — the way `forward_return` / the J-89 timeline are asserted) and contains NO smoothed/true-bear value (the J-89 fence holds — no code path from `retrospective` into the full causal series); `test_no_magic_numbers` green (no new literal in any engine CALC_FILE); `test_db.py` expected-tables guard green (NO new table — this iter adds none); any payload-shape guard touched (e.g. `test_api_data.py::test_get_data_overview_shape` / `test_api_engine.py` byte-equality guards) updated in the SAME iteration if a served shape changes (the recurring iter-20/23/24/32 additive-trips-blanket-guard lesson — but note this iter's `full` param is an ADDITIVE opt-in, the default card payload must stay byte-identical so the existing guards should NOT trip).
- **Error cases:** an out-of-range / invalid `as_of` on `?full=true` degrades to the resolved date (never a fabricated date); an empty/early DB → honest-empty full timeline (no fabricated points); `full` accepts only a boolean.

## NOTES

- **Lessons applied (surface to dev/reviewer/evaluator):**
  - iter-22: on an in-place resume after GOAL_ACHIEVED, "every journey in journey-history is green" is NOT sufficient — goal.md's newly-queued buildable Must-haves J-97..J-100 have no journey-history entry yet and count as `unknown` Must-haves with no positive evidence, which is exactly why this iteration exists. (Applies to: this resume.)
  - iter-16 / J-71 / J-18: the cheapest decisive check that the synced pane-zoom is a view transform and NOT a second date state is static — `grep` the diff for any new date `useState` / `window`/`document` keydown or a write to the global as-of from the chart; the synced zoom must touch ONLY the visible range. The single global as-of switcher stays the only date control (0 native `input[type=date]`).
  - iter-36: a backend-only restore-a-render iter gets browser-QA AUTO-SKIPPED on "Frontend Present: no" — this iter is explicitly `Frontend Present: yes` (it has real frontend work), so live render evidence MUST be captured in THIS iteration; do not accept J-97/J-98 passing on API-layer/source evidence alone.
  - iter-18 (7th-recurrence heatmap trap) + iter-33/34: capture below-the-fold panes by scrolling them INTO the viewport full-viewport and VIEW the pixels; reject any un-hydrated skeleton or blank frame; md5sum the evidence dir FIRST and reject byte-identical "differential" frames (a synchronized-zoom proof needs two byte-DISTINCT frames before/after the zoom). For the J-97 series-equals-card check, prefer live DOM / computed-CSS extraction over a single screenshot where a render-only signal (band colours per date) is load-bearing.
  - iter-11/29/30/37 (suite gate): hand the FULL pytest suite to the pump nohup-async and gate the next evaluator on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight stream; re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` F in isolation before attributing it to this iteration (the known slow-boot/scanner_runs-race contention flake).
  - iter-20/21: if any new float/threshold sentinel lands in an engine CALC_FILE it trips `test_no_magic_numbers`; the band-primitive colours must come from design tokens / config, never hardcoded hex.
- **Coherence focus for the auditor:** J-97 must read the SAME single served market-phase series (no second computation/endpoint for phase/severity/P(bear)); J-98 must introduce NO new endpoint / NO new canonical value (a pure information-architecture reshuffle of already-served values; Dashboard stays the single home). Both are registered in `blueprint.md` (Data Contract row for the J-97 full timeline; Dashboard IA annotation) — the edits are additive (new value row + a page annotation under the existing Dashboard nav home), so no nav-skeleton re-approval is required.
- **GOAL_ACHIEVED candidacy:** this iter is NOT a GOAL_ACHIEVED candidate (J-99/J-100 remain unbuilt buildable Must-haves). After J-97..J-100 all land green with the full suite GREEN, zero regression, and COHERENCE-PASS, the next evaluation becomes a candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).
