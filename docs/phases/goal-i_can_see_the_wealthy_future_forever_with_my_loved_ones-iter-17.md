# Goal Iteration 17 — Availability heatmap multi-hue legibility + stock-detail price-chart hover box

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 17
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-74, J-76
- **Required-still-passing journeys:** J-61, J-70, J-20, J-45, J-42, J-05, J-06
- **Anti-goal reminders:**
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code. (Here: the heatmap colour scale + day-number contrast MUST be defined from the design-token system — no scattered magic hex in individual cells.)
  - **No lookahead.** Chart visualization MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking, and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)* (Here: the J-76 hover box on a post-as-of bar MUST be labelled forward/after-as-of and stay visualization-only.)
  - **Coverage & missing-data are descriptive & honest.** The coverage figures and the heatmap MUST be read-only metadata derived from stored bars + config — they MUST NOT recompute or restate any canonical score, return, bucket, or setup; a thin/empty day MUST be shown honestly, never as a fabricated or filled value.
  - **Exactly one date selector** — the global as-of control drives every date-scoped page; neither surface in this iteration may introduce a second/page-local date state. *(critical)*

## GOAL

A user can read the per-date availability heatmap at a glance — coverage levels are obviously different colours on a perceptually-ordered multi-hue scale with a legend and legible day numbers in every bucket — and can hover any bar on the stock-detail price chart to see a tracking detail box with that bar's date, OHLCV, % change, and each moving-average value.

## BACKGROUND

Iter-16 reached GOAL_ACHIEVED for the J-68..J-71 appended scope; `docs/goal.md` was then extended (commit 3b5d9a9) with seven new buildable Must-haves J-72..J-78, none data-dependent and none allowed to halt the loop. This iteration starts that extension with the two lowest-risk, pure-frontend, no-backend, no-canonical-value display polishes — J-74 (heatmap multi-hue scale + legend + per-bucket legible day numbers, hardening J-61/J-70) and J-76 (stock-detail price-chart per-bar hover box, mirroring the existing `index-regime-chart` crosshair tooltip). Bundling them keeps the iteration lean and easy to score: both re-display already-served payloads (`GET /api/data/availability`, `GET /api/stocks/{ticker}/bars`), touch zero backend code (no pytest gate, no `_ADDITIVE_COLUMNS` trap), and avoid `asof-provider.tsx` entirely (so the J-18/J-43 invariant is untouched). The backend-touching and `asof-provider`-touching journeys (J-72, J-73, J-75, J-77, J-78) are deferred to later iterations at appropriate depth.

Applied lessons (see `state/lessons.md`):
- **iter-16 (styling buckets not all reachable from seed):** the committed seed exercises only buckets 4–5 of the heatmap (every day has full coverage), so the contrast/colour of buckets 0–3 must be verified at SOURCE level (the colour-scale + text-contrast token maps) rather than recorded partial — a static className map's correctness is provable without a live render of every branch. Browser-QA should still capture the legend and the rendered (4–5) cells full-viewport.
- **iter-16/iter-5 (nested interactive elements & dev-overlay badge):** if any heatmap cell or legend swatch becomes a new interactive affordance, do not nest a `<button>` inside another `<button>` (the iter-5 SortHeader/InfoTooltip trap); treat a NEW red "N error" Next dev-overlay badge appearing in a `/data` or `/stocks/[ticker]` capture (vs prior iterations of the same page) as a must-explain regression signal even when every leg passes.
- **iters 3/7/10/13/15/16 (evidence hygiene):** md5sum the evidence dir FIRST; re-capture any blank or byte-identical close-up at full-viewport; never reuse one PNG under multiple evidence names; validate filename-vs-content for any shared-bytes capture.
- **iter-1 (frontend gate):** ESLint is not installed in `apps/frontend`; the frontend gate is `tsc --noEmit`, not `npm run lint`.

## IN SCOPE

### Backend
- [ ] None. `git diff -- apps/backend/` MUST be empty at handoff. Both surfaces re-display already-served payloads with no new endpoint, no new column, no engine change.

### Frontend
- [ ] **J-74 (`apps/frontend/components/availability-heatmap.tsx`):** replace the single-hue teal-opacity ramp (`bg-accent/15…/70`, where buckets 1–3 were near-identical) with a **perceptually-ordered, clearly-separated multi-hue scale** across the six density buckets (0–5) — a low→high progression across distinct hues (e.g. slate → blue → teal → green → amber) so neighbouring buckets are unambiguously different on the dark background. The scale and the per-bucket day-number text-contrast classes MUST be defined ONCE from the existing design-token system (Tailwind tokens registered in `tailwind.config.ts` — extend the token palette there if new hues are needed) — **no hardcoded hex in individual cells** (anti-goal: No magic numbers / coherence invariant 10). Keep / harden the J-70 per-bucket legible day-number contrast for every bucket 0–5 (including the dark-on-dark empty/low-density case). Add a **legend** that maps each colour to its coverage level. PRESERVE all J-61/J-70 semantics verbatim: same `GET /api/data/availability` payload (no new fetch, no recompute), all `data-*` attributes (`data-testid="availability-cell"`, `data-bucket`, `data-date`, `data-symbols`, `data-total`, `data-snapshot`, `data-testid="availability-month"`), the hover-exact-figures tooltip, the snapshot-day distinct marking, honest partial-coverage rendering (a 3-of-158 day visibly distinct from a full day), the graceful empty-DB state, the J-70 descending month order + two-up layout, and the cell-click-prefills-the-job-form-NEVER-the-as-of behaviour (J-18).
- [ ] **J-76 (`apps/frontend/components/price-chart.tsx`):** add a per-bar **hover detail box** that tracks the crosshair, mirroring the existing `index-regime-chart.tsx` crosshair-move tooltip pattern (its `subscribeCrosshairMove` handler at `index-regime-chart.tsx:99,166`). On hover of any bar show: that bar's **date** (via the shared `formatIsoDate` formatter, `apps/frontend/lib/dates.ts` — J-42, never a locale path), **open / high / low / close**, **volume**, the bar's **% change**, and each rendered **moving-average value** (the same MA arrays the chart already plots — single source of truth, read from the already-served `/api/stocks/{ticker}/bars` data, NO extra request, NO recompute). A **forward (post-as-of, display-only) bar MUST be labelled** as such in the box (reuse the existing forward-region/`is_forward` treatment) and stays visualization-only — never an as-of signal (anti-goal: No lookahead). The box MUST NOT obscure the as-of marker / forward divider (J-20) or the regime bands (J-45). Style with the existing design tokens. Leaving the chart hides the box. It works for every timeframe the chart renders.

### New user-facing capability
- The availability heatmap is now readable at a glance: coverage density maps to clearly distinct hues with a documented legend, and every date number is legible against its cell in every bucket.
- The stock-detail price chart now reveals exact per-bar figures on hover (date, OHLCV, % change, each MA value), including a forward-bar label past the as-of marker.

### New information displayed
- Heatmap: a colour legend mapping each density bucket to its coverage level (the figures themselves were already on hover — this adds the colour→level key and the multi-hue separation).
- Price chart: a crosshair-tracking detail box surfacing the exact OHLCV / % change / MA values the chart already plots for the hovered bar.

### New user actions
- Hover the price chart to read a bar's detail box; move off to dismiss. (Heatmap interactions — hover for figures, click to prefill the job form — are unchanged.)

### UI surface changes
- `/data` — the Per-date availability heatmap card gains a multi-hue scale + legend; same card, same payload.
- `/stocks/[ticker]` — the price chart gains a hover detail box; same chart, same served bars.

### Product surface delta
- Two existing surfaces become materially more legible/informative with no new data, no new page, and no backend change — pure presentation upgrades of already-served payloads.

### Blueprint conformance
- No new surfaces. J-74 lands on the existing **Data Manager** home (`/data`), hardening the registered "Per-date availability counts" / `GET /api/data/availability` row. J-76 lands on the existing **Stock Detail** home (`/stocks/[ticker]`), as a presentation of the registered "Price/MA/volume series" / `GET /api/stocks/{ticker}/bars` row. Blueprint updated with additive `[TARGET iter-17]` annotations on both rows + the IA entries (no nav-skeleton change → no re-approval needed).

### Data-contract additions
- **None.** No NEW displayed value is introduced. J-74 re-styles the SAME `GET /api/data/availability` payload (same density buckets, no recompute). J-76 re-displays the SAME `GET /api/stocks/{ticker}/bars` payload (the exact OHLCV / volume / MA values the chart already plots) — read in the view, computed nowhere new. No second computation or endpoint for any registered value.

## OUT OF SCOPE

- Any backend change (engine, API, config, schema). `git diff -- apps/backend/` MUST be empty.
- J-72 (Research perf/cache over the event study — backend, byte-identity guard, full pytest gate).
- J-73 (synchronous `?asof` URL hydration — touches `asof-provider.tsx`, the J-18/J-43/J-50 invariant core; deferred to its own iteration).
- J-75 (forward-return columns on `/stocks` + detail — new read surface over the stored `forward_returns` table; backend + frontend, full depth).
- J-77 (Regime × Setup × Pattern ranked study — event-study observation enrichment + new samples cohort; full depth, highest risk).
- J-78 (dashboard major-indexes default range `6M` → `all` — a one-line `config.yaml` change at `index_chart.default_range`, line 305; trivial but backend-config-touching so it rides a later iteration to keep this one frontend-only).
- The data-walled trio J-22/J-23/J-24 stays honest blocked-NA (non-vetoing, non-halting per goal.md) — not in scope, not touched.

## DEFINITION OF DONE

- [ ] Target journeys J-74, J-76 pass via browser-qa-agent (J-74 colour-separation + legend + per-bucket legibility verified; the seed-unreachable buckets 0–3 verified at source level on the colour-scale + text-contrast token maps — acceptable per the iter-16 lesson; J-76 hover box shows date/OHLCV/%chg/MA values, labels a forward bar, and disappears off-chart).
- [ ] Required-still-passing journeys remain green: J-61 (heatmap still reads the same payload, click still prefills the job form not the as-of), J-70 (descending months + two-up layout intact), J-20 (as-of marker / forward divider not obscured), J-45 (regime bands not obscured), J-42 (hover-box date is `yyyy-MM-dd` via the shared formatter), J-05/J-06 (stock-detail scores unchanged — frontend-only, no read-path touch).
- [ ] No anti-goal violation introduced (no fabricated data, no recompute in the read path, no magic hex, no lookahead from the forward-bar hover, exactly one date selector preserved).
- [ ] No NEW red Next dev-overlay error badge on `/data` or `/stocks/[ticker]` captures vs prior iterations (iter-5/iter-16 lesson).
- [ ] `apps/frontend` `tsc --noEmit` clean (NOT `npm run lint` — ESLint not installed here, iter-1 lesson).
- [ ] `git diff -- apps/backend/` is empty.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-17-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-74 and J-76 by ID. For J-74: open `/data`, screenshot the heatmap card full-viewport showing the multi-hue scale + legend; assert the legend maps colours to coverage levels; assert a (visually reachable) high-density cell and the snapshot-day marking; confirm hover still shows exact figures (date, symbols-with-bars / total, snapshot yes/no); confirm a cell click still prefills the job-form Start/End and NEVER changes the global as-of (indicator stays "Latest", URL stays `/data`). For J-76: open `/stocks/NVDA` (or another seeded ticker), move the crosshair across the chart, screenshot the hover box showing date (`yyyy-MM-dd`) + OHLCV + % change + MA values; move into the post-as-of forward region (set a historical as-of D first so a forward region exists) and screenshot the box labelling the bar forward/after-as-of; move off-chart and confirm the box disappears. md5sum the evidence dir first; one capture per claimed surface; full-viewport for any close-up that risks a blank.
- **Unit/integration:** none required (frontend-only presentation; no backend code path changes; `tsc --noEmit` is the frontend gate). The full pytest suite is NOT a gate this iteration (backend diff empty) — do not run it.
- **Error cases:** heatmap with an empty/thin DB still renders gracefully (honest empty state, never fabricated cells); a thin (e.g. 3-of-158) day renders visibly distinct from a full day; the hover box on a bar with NA/absent MA at the chart edge shows the MA honestly (NA / omitted) rather than a fabricated number; the box never renders for a non-existent bar.

## NOTES

- **Source-level verification is acceptable and expected for J-74 buckets 0–3.** Per the iter-16 lesson, the committed seed gives every day full coverage (buckets 4–5 only), so buckets 0–3 will not render live. Grade their colour + day-number contrast on the static colour-scale and text-contrast className/token maps in `availability-heatmap.tsx` (correctness of a static map is provable without a live render of every branch). Buckets 4–5 must be verified live full-viewport.
- **Coherence focus this iteration:** confirm both diffs are pure re-renders of already-served payloads — `availability-heatmap.tsx` adds no fetch/computation (only colour/legend/contrast token mapping over the same `data-bucket`); `price-chart.tsx` reads the OHLCV/volume/MA arrays it already plots and computes no canonical value in the view (the % change is a display derivation of two already-served closes, not a stored canonical value — acceptable presentation math, like the existing index-chart tooltip). No new `?asof` author; `asof-provider.tsx` / `asof-switcher.tsx` / `asof-calendar.tsx` untouched. Expect COHERENCE-PASS (no new Data Contract value, no duplicate computation, no new route/home).
- **Depth = lean** is justified: two isolated frontend component files, no backend, no data model, no new tests beyond browser smoke + `tsc`. The prior verdict was GOAL_ACHIEVED (not ESCALATE), so full depth is not mandated.
- After J-74 + J-76 pass with no regression, recommended next: J-78 (one-line config default range) bundled with J-73 (synchronous `?asof` hydration) — or J-73 alone given its J-18/J-43/J-50 sensitivity — then the backend cluster J-72 / J-75 / J-77 at full depth.
- J-22/J-23/J-24 remain honest blocked-NA (non-vetoing per goal.md "Data-dependent journeys (non-halting)"); not part of this scope and not a halt condition.
