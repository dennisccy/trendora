# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## What Was Built

**J-91 — Downtrend Opportunity lab on `/research`:**
- New `DowntrendOpportunityLab` section appended below `RecoveryTurnEdgeLab` (the last lab). It fetches
  `GET /api/research/downtrend-opportunity` via `fetchDowntrendOpportunity` with its OWN read-only data
  source + loading state, reusing the page's shared `horizon` + `asofCutoff` (no second date/horizon state).
- Conditioning controls: a **Condition on** dimension selector (Phase / Severity band / P(bear) band, built
  from the payload's config-driven `dimensions` list) + the Episodes ⇄ Pooled toggle (reused
  `EventStudyViewToggle`). The As-of⇄All-history scoping is the page's shared analysis-mode toggle (the
  single global as-of) — the lab adds NO date control and NO window/document keydown listener (J-18).
- Three angles render side by side as ranked, client-side-sortable tables (`xl:grid-cols-3`, stacks on
  narrow widths): **Held up best**, **Fell hardest** (labelled `Research evidence only` — NO order/execution
  affordance), and the reused **Recovery-turn edge by phase**. Columns: Cohort, n, Mean, Hit-rate,
  Ret/DD (downside-only risk-adjusted), Mean MDD. Sort is a pure view transform (re-orders only, J-48/J-82);
  NA-last uses the SAME cell predicate (`low_sample || n===0 || value===null`).
- Each row's `n` is a `SampleLink` `N=` chip → the samples drill-down in a NEW tab (J-65), count-coherent
  (`total == published n`). Held-up-best + fell-hardest share cohorts, so a chip from either angle drills
  into the SAME `(dimension, cohort)` group.
- Honest states: loading skeleton (`CombinationSkeleton`), warming (inherited from the page shell), empty
  (`EmptyState`), error (styled alert — "no figures rather than fabricated values"), and NA + n on
  low-sample/empty conditioned cohorts. Survivorship + descriptive `CaveatBanner` persists.

**J-92 — publication-lag limitation label + macro provider visibility:**
- A `MacroPublicationLagLabel` is shown in the Downtrend Opportunity lab: macro inputs are optional and
  config-default-OFF (today's figures use the price/breadth/VIX path only), and a macro value is used for a
  date only once published (`published_date <= D`) — never the reference-date value; a walled/uncommitted
  series is shown as NA, never fabricated.
- A new `MacroFeedPanel` on `/data` (after the missing-data diagnostic) surfaces the FRED macro feed
  catalog: the provider, the live-key availability (env-var NAME only — `detected` / `not set (NA)`), the
  per-leg config-default-OFF flags (severity / regime / study, each `on`/`off`), and a per-series table
  (FRED id, publication lag, OHLCV proxy, committed-seed observation count, `available`/`NA` status). With
  every leg off (the default) it shows an explicit "default figures are unchanged" note.

## Files Changed
- `apps/frontend/lib/api.ts` -- `DowntrendOpportunityRow` / `DowntrendOpportunityResponse` types +
  `fetchDowntrendOpportunity`; the `SampleCohort` union gains `downtrend-opportunity` + `dimension`; the
  `MacroSeriesAvailability` / `MacroAvailability` types + the `macro` field on `DataOverviewResponse`.
- `apps/frontend/lib/samples-link.ts` -- `DowntrendOpportunityCohortParams` + the `buildSamplesHref` branch.
- `apps/frontend/app/research/page.tsx` -- `DowntrendOpportunityLab` + `DowntrendDimensionSelector` +
  `MacroPublicationLagLabel` + `DowntrendOpportunityBody` + `DowntrendAngleTable` + `DowntrendRecoveryAngle`.
- `apps/frontend/app/research/samples/page.tsx` -- the downtrend-opportunity cohort header in `describeCohort`.
- `apps/frontend/app/data/page.tsx` -- the `MacroFeedPanel` + the `macro` block render + the `Activity` icon.

## Tests Run
- `npx tsc --noEmit` (TypeScript typecheck): PASSED (0 errors).
- (No JS unit-test runner is configured in this project — `tsc` is the frontend gate; the live browser
  flows are validated by the browser-qa-agent.)

Key data-testids for browser QA:
- `downtrend-opportunity-section`, `downtrend-dimension-{phase|severity_band|pbear_band}`,
  `downtrend-held-up-best-table`, `downtrend-fell-hardest-table`, `downtrend-fell-hardest-table-evidence-only`,
  `downtrend-recovery-angle-table`, `downtrend-held-up-best-table-sort-{col}`, `macro-publication-lag-label`,
  `sample-link` (the `N=` chips, resolved by `aria-label`).
- `macro-feed-panel`, `macro-live-available`, `macro-default-off-note`, `macro-series-table`,
  `macro-series-{id}`.

## Known Issues
- The Downtrend Opportunity lab sits below the existing labs on `/research` (scroll-into-view for QA —
  `md5sum` the evidence dir first, resolve sort/`N=` controls by `aria-label`, scroll the panel into full
  viewport and VIEW the pixels — the recurring evidence-hygiene lesson).
- The macro feed `/data` panel is read-only catalog/availability only — there is no UI affordance to trigger
  a live FRED fetch this iteration (out of scope; the committed seed + the FRED provider give the
  offline-testable path). A walled/uncommitted series shows NA honestly.
- Because every macro leg is config-default-OFF, the Dashboard market-phase panel and the Research downtrend
  study render the price/breadth/VIX-only figures by default — the publication-lag label is shown
  pre-emptively (it discloses the contract even when no macro-conditioned figure is currently displayed).
