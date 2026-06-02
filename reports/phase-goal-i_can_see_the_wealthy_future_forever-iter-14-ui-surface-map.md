# Phase goal-i_can_see_the_wealthy_future_forever-iter-14 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `EventStudyLab` section (`data-testid="event-study-section"`) | New component | J-29 adds the Setup & Pattern Lab event study below the Factor Lab + Combination Lab | Scroll to "Setup & Pattern Lab — event study"; confirm the section renders with a Subject selector, a per-horizon table, by-regime and by-sector panels, and the caveat banner |
| `/research` | `SubjectSelector` dropdown (`data-testid="subject-select"`) | New form control | User can choose any setup or pattern subject; catalog is config-driven from the payload | Open the dropdown; confirm two `<optgroup>`s ("Setups" and "Patterns"); confirm Setups lists all 6 setups and Patterns lists VCP / Pullback-to-rising-DMA / Flat-base — none hard-coded |
| `/research` | `EventStudyHorizonTable` (`data-testid="event-study-horizon-table"`) | New table | Per-horizon distribution + expectancy + MAE/MFE + downside risk-adjusted, J-29 step 4/5 | Select subject **Breakout-watch**; confirm one row per horizon with Mean, Median, % Positive, Dispersion, Expectancy, Mean MAE, Mean MFE, Return÷downside-dev, Return÷MAE, n all populated (not NA) |
| `/research` | `EventStudyHorizonTable` — best-exit-horizon highlight | New table | Best exit-horizon curve, J-29 step 5 | With **Breakout-watch** selected, confirm exactly one row carries the "best exit" badge/highlight; confirm it is among non-low-sample rows |
| `/research` | `EventStudyHorizonTable` — low-sample NA rows | New behavior | Honest NA + n on low-sample, never fabricated | Select subject **VCP** (or default **Actionable**); confirm horizon rows render literal "NA" with an `n` chip (e.g. n=27 / n=2) instead of numbers |
| `/research` | `EventStudyRegimeTable` (`data-testid="event-study-regime-table"`) | New table | By-regime slice for selected horizon; every configured regime label emitted | Select **Breakout-watch**; confirm one row per configured regime label, each with n / mean / hit-rate / downside risk-adjusted; confirm ≥1 empty regime row shows NA + n=0 |
| `/research` | `EventStudySectorTable` (`data-testid="event-study-sector-table"`) | New table | By-sector slice for selected horizon; present-only sectors | Select **Pullback to a rising DMA**; confirm only sectors with members appear, each with n / mean / downside risk-adjusted; confirm a low-sample sector shows NA + n |
| `/research` | Shared `HorizonSelector` (`data-testid="horizon-select"`) re-points event study | Changed behavior | Event study reuses the shared horizon (no second date/horizon state) | Change the Horizon buttons above; confirm the by-regime and by-sector panels (and per-horizon highlight) re-point to the chosen horizon |
| `/research` | `CaveatBanner` inside the event-study section | New element | Survivorship-bias + descriptive ("not predictive") labels visible in the lab | Confirm the survivorship-bias caveat and descriptive caveat text render within the Setup & Pattern Lab section |
| `/research` | `EventStudyLab` empty / error / loading states | New behavior | Honest unavailable states, no fabricated values | Stop the backend and reload; confirm "Backend unavailable" error block (not a blank/fabricated table); for a zero-occurrence subject confirm the "No forward-tested occurrences" empty state |
| `/research` | Whole page under as-of toggle | Changed behavior (regression guard, J-18) | New section adds no date/as-of state | Toggle the global as-of control latest→historical; confirm the event-study tables are byte-identical (distinct sha256 of shots equal) and the network tab shows **zero** `as_of`-param requests for `/api/research/event-study` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — `ForwardReturn` gains append-only `mae` / `mfe` `Optional[float]` columns. Stored data only; surfaced solely in aggregated form via the event study, not on any existing page.
- `apps/backend/app/engine/forward_testing.py` — new `forward_excursions(...)` helper + `_insert_run_forward_returns` now populates `mae`/`mfe`. Internal forward-side compute; no direct UI surface (feeds the event-study aggregation).
- `apps/backend/app/engine/research.py` — `compute_event_study(...)` + helpers. Read-only aggregation backing the new endpoint; not a UI surface itself.
- `apps/backend/app/api/research.py` — new `GET /api/research/event-study` endpoint. Consumed by the frontend via `fetchEventStudy(...)` → drives the `EventStudyLab` section (so its effect is visible, but the endpoint itself is not a UI surface).
- `apps/backend/data/trendora.db` — regenerated from the committed seed (gitignored runtime artifact) so existing rows carry MAE/MFE. No UI change beyond enabling populated event-study figures.
- `apps/backend/tests/*` (`test_forward_testing.py`, `test_research.py`, `test_api_research.py`, `test_no_magic_numbers.py`) — test additions, no UI impact.
- `apps/frontend/lib/api.ts` — `fetchEventStudy(...)` helper + `EventStudyResponse` / row types. Data-access layer wiring; the user-visible effect is the `EventStudyLab` section above.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/research`), 1 new lab section with 1 selector + 3 tables + caveat/empty/error states
- **New pages/routes:** 0 (additive section on existing approved `/research` home)
- **Modified components:** `apps/frontend/app/research/page.tsx` (new `EventStudyLab` + sub-components), `apps/frontend/lib/api.ts`
- **Navigation changes:** no (no new nav entry, no new route, no new date control)
- **Backend-only changes:** 7 (models, forward_testing, research engine, research API, DB regen, tests, api.ts data layer)
