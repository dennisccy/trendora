# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Agent:** developer
**Status:** complete

## What Was Built (UI)

**J-104 — Research split into a hub + lazy sub-routes**
- `/research` is now a **HUB**: a responsive link grid (1/2/3 columns at sm/xl breakpoints) of the 7 labs,
  each card with an icon, title, one-line description, and a hover arrow. The hub fires NO heavy fetch.
- Every heavy lab moved to its OWN lazy-loaded route, so navigating to one fires at most ONE heavy fetch:
  - `/research/factor-lab` — Factor Lab
  - `/research/factor-combination` — Multi-factor combination
  - `/research/event-study` — Setup & Pattern event study
  - `/research/regime-setup-pattern` — Regime × Setup × Pattern
  - `/research/recovery-turn-edge` — Recovery-Turn Edge
  - `/research/downtrend-opportunity` — Downtrend Opportunity
  - `/research/severity-velocity` — Severity-velocity × Regime (NEW, J-103)
- The sidebar "Research" entry still points to `/research`; `isActive` uses `startsWith`, so every sub-route
  highlights Research in the nav. Each lab is ≤2 clicks from the persistent nav and deep-linkable (the hub
  links carry the global `?asof` via `useAsOfHref` — J-50).
- Each relocated lab keeps its EXISTING behavior verbatim: the same tables, mode toggles, sort/filter
  controls, and the `N=` samples drill-down chips (new tab + `?asof`). The lab bodies were extracted into a
  shared module (`app/research/_labs.tsx`) and are rendered unchanged — figures are byte-identical.
- Shared shell: every lab route renders a `ResearchControls` bar (heading + the All-history⇄As-of analysis
  mode toggle + a config-driven horizon selector) + the survivorship/descriptive caveat banner + a warming
  state — single-sourced so the relocated labs look identical to before. The analysis mode + global as-of
  are shared (`useResearchControls`); no second date state.

**J-103 — Severity-velocity × Regime study page**
- `/research/severity-velocity` renders the **regime-family × velocity-sign matrix**: rows are the regime
  families (Risk-on / Neutral / Risk-off "red"), columns are the velocity signs (Rising / Flat / Falling),
  each cell showing the mean forward SPY return (colored pos/neg), the win-rate, and a count-coherent `N=`
  chip that opens the reproducing cohort in `/research/samples` in a NEW tab (carrying `?asof`).
- A horizon selector (5/10/20/60-day, config-driven) and the shared All-history⇄As-of mode (defaults to the
  all-history aggregate; As-of mode is a pure observation-set filter).
- A **verdict card** displays the honest verdict + limitations VERBATIM from the backend (survivorship /
  bull-dominated-sample / underpowered-for-crashes caveats; the hypothesis that rising stress under a red
  regime predicts a decline is NOT supported — it preceded a bounce). The frontend authors no conclusion.
- States handled: loading skeleton, "backend unavailable" error card, warming state, honest empty state
  (n_total 0 → an EmptyState, never a fabricated row), and low-sample cells gated to "NA / low sample".

## Files Changed (UI)

- `apps/frontend/app/research/page.tsx` — the Research hub (link grid).
- `apps/frontend/app/research/_labs.tsx` — shared lab components + scaffolding + per-lab route-page wrappers.
- `apps/frontend/app/research/severity-velocity/page.tsx` — NEW severity-velocity matrix + verdict page.
- `apps/frontend/app/research/{factor-lab,factor-combination,event-study,regime-setup-pattern,recovery-turn-edge,downtrend-opportunity}/page.tsx`
  — NEW thin route pages.
- `apps/frontend/app/research/samples/page.tsx` — `describeCohort` severity-velocity case.
- `apps/frontend/lib/api.ts` — `SeverityVelocity*` types + `fetchSeverityVelocity`; `SampleCohort` additions.
- `apps/frontend/lib/samples-link.ts` — `SeverityVelocityCohortParams` + `buildSamplesHref` case.

## Design System Adherence

- Component library: existing `Card`, `Select`, `EmptyState`, `SampleLink`/`SampleSize`, `PageHeading`,
  `WarmingState`, lucide icons — no new component vocabulary.
- Color / spacing / typography: only existing palette + spacing tokens (`text-pos`/`text-neg`/`text-warn`/
  `text-accent`/`border-border`/`bg-surface`…) and the shared `fmtPct`/`returnClass` formatters — no
  arbitrary hex or pixel values.
- Interactive states: hub cards + chips have hover/focus/active states (ring + border + translate).
- Responsive: the hub grid collapses 3→2→1 columns at xl/sm; the matrix table is horizontally scrollable on
  narrow screens.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` → clean (0 errors).
- `cd apps/frontend && npx next build` → success; all 7 research sub-routes generated; `/research` hub 2.3 kB.

## Known Issues

- The severity-velocity page has no Episodes/Pooled toggle (the study has one SPY observation per date — the
  modes would be identical; see the dev handoff). The As-of mode is the real mode and is present.
- Browser-QA (Chrome MCP / Playwright) was not run by the developer; live rendered-evidence capture is the
  browser-qa-agent's job. The page is verified to build + typecheck, and the backend endpoint it reads was
  live-probed returning the real matrix.
