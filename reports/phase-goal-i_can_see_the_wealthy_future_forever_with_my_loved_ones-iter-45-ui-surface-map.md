# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | Hub card grid | Changed behavior | Monolithic lab page split into a hub linking to sub-routes | Navigate to `/research`; confirm the page shows a card grid of 7 lab links and NO heavy analysis table or chart renders on this page |
| `/research/severity-velocity` | Regime x velocity-sign matrix table | New page | J-103: new study answering whether rising/falling stress predicts market direction | Load the page; confirm the matrix table has 3 rows (Risk-on / Neutral / Risk-off) and 3 columns (Rising / Flat / Falling), each cell showing mean return, win-rate, and an N= chip |
| `/research/severity-velocity` | Horizon selector | New component | Allows choosing the forward-return window (5 / 10 / 20 / 60 days) | Change the horizon from 20d to 5d; confirm the mean return and N values in the matrix cells update |
| `/research/severity-velocity` | As-of mode toggle | New component | Allows limiting observations to on-or-before a selected date | Toggle from "All history" to "As of"; confirm the total observation count (n_total) changes and cells reflect the narrowed date range |
| `/research/severity-velocity` | Verdict card | New component | Displays the honest plain-language finding + survivorship / bull-dominated / underpowered caveats verbatim | Confirm the verdict card text includes "NOT supported" and explicitly mentions that rising stress under a red regime preceded a bounce, not a decline |
| `/research/severity-velocity` | N= drill-down chips | New interactive element | Each chip opens the reproducing cohort in `/research/samples` in a new tab | Click the N= chip for any non-zero cell; confirm a new browser tab opens at `/research/samples` showing the same count as the chip label |
| `/research/severity-velocity` | Loading / empty / NA states | New page states | Must never show a fabricated row or skeleton for an honest-empty cell | Select an As-of date early in the dataset where some cells have zero observations; confirm those cells show "NA / low sample" rather than a number or a broken placeholder |
| `/research/factor-lab` | Relocated Factor Lab page | New page (relocation) | Extracted from the old monolith so it loads independently | Navigate to `/research/factor-lab`; confirm the Factor Lab analysis loads and its figures match what appeared on the old `/research` page |
| `/research/factor-combination` | Relocated Multi-factor Combination page | New page (relocation) | Extracted from the old monolith; now cached after first load | Navigate to `/research/factor-combination`; confirm the analysis table loads and figures are identical to pre-split values; revisit the page and confirm it returns faster on the second load |
| `/research/event-study` | Relocated Event Study page | New page (relocation) | Extracted from the old monolith so it loads independently | Navigate to `/research/event-study`; confirm the setup-and-pattern table renders; click an N= chip and verify the `/research/samples` drill-down count matches |
| `/research/regime-setup-pattern` | Relocated Regime x Setup x Pattern page | New page (relocation) | Extracted from the old monolith; now cached after first load | Navigate to `/research/regime-setup-pattern`; confirm the matrix table renders with the same values as before the split |
| `/research/recovery-turn-edge` | Relocated Recovery-Turn Edge page | New page (relocation) | Extracted from the old monolith so it loads independently; avoids orphaning the lab | Navigate to `/research/recovery-turn-edge`; confirm the Recovery-Turn Edge study renders and its N= chips open valid cohort tabs |
| `/research/downtrend-opportunity` | Relocated Downtrend Opportunity page | New page (relocation) | Extracted from the old monolith so it loads independently | Navigate to `/research/downtrend-opportunity`; confirm the downtrend analysis table renders with the same figures as before the split |
| `/research/samples` | Cohort description for severity-velocity kind | Changed behavior | `describeCohort` now handles `kind=severity-velocity` parameters so the drill-down page shows a meaningful title | Open a severity-velocity N= chip in a new tab; confirm the Samples page displays a human-readable cohort label (regime family + velocity sign + horizon) rather than a raw JSON dump or generic title |
| Sidebar | Research active-highlight | Changed behavior | `isActive` now uses `startsWith` so any `/research/*` sub-route keeps Research highlighted | Navigate to `/research/event-study`; confirm the "Research" sidebar entry is highlighted/active without requiring a click back to `/research` |
| `/research` hub | Deep-linkability and `?asof` propagation | New behavior | Hub lab cards link to sub-routes carrying the global `?asof` param | With an `?asof` date in the URL on `/research`, click a lab card; confirm the sub-route URL carries the same `?asof` value |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` + `config.yaml` — new `RegimeFamily`, `VelocitySign`, `SeverityVelocityCfg` config models and the `research.severity_velocity` block in `config.yaml`. These back-fill the vocabulary used by the severity-velocity study; all values are already reflected in the page via the API response. No standalone UI impact beyond what the page already exposes.
- `apps/backend/app/engine/market_phase.py` — new `severity_velocity_by_date` public accessor. Internal accessor consumed by `compute_severity_velocity_study`; no direct rendering.
- `apps/backend/app/engine/research.py` — `compute_severity_velocity_study`, `severity_velocity_cached`, `factor_combination_cached`, `regime_setup_pattern_cached`, bounded downtrend scan. Backend engine functions; their impact is fully surfaced through the API endpoints and pages described above.
- `apps/backend/app/engine/samples.py` — `KIND_SEVERITY_VELOCITY` constant and `_severity_velocity_samples` builder. Backend cohort construction; user-visible only through the `/research/samples` drill-down already mapped above.
- `apps/backend/tests/test_severity_velocity.py`, `apps/backend/tests/test_api_research.py` — new and updated test files. No UI impact.
- `apps/frontend/lib/api.ts` — `SeverityVelocity*` types and `fetchSeverityVelocity`. Frontend data-fetching module; not itself a rendered surface.
- `apps/frontend/lib/samples-link.ts` — `SeverityVelocityCohortParams` and `buildSamplesHref` case. URL-builder utility; impact visible through N= chip behavior already mapped above.
- `apps/frontend/app/research/_labs.tsx` — shared lab components and scaffolding. Internal module; impact visible through the relocated lab pages already mapped above.

---

## Summary

- **Frontend surfaces changed:** 16
- **New pages/routes:** 8 (`/research/severity-velocity`, `/research/factor-lab`, `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/recovery-turn-edge`, `/research/downtrend-opportunity`, and the redesigned `/research` hub)
- **Modified components:** 3 (`/research/samples` cohort description, sidebar active-highlight behavior, hub `?asof` propagation)
- **Navigation changes:** yes — `/research` is now a hub; sidebar active-highlight covers all `/research/*` sub-routes
- **Backend-only changes:** 8 files (config, engine, samples, tests, lib utilities — all surfaced through the mapped pages)
