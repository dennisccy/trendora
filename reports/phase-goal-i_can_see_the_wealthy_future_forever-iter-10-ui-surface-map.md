# Phase goal-i_can_see_the_wealthy_future_forever-iter-10 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (and all pages) | `Sidebar` (`components/sidebar.tsx`) | Added navigation | New `/research` nav home (Microscope icon) between System Health and Watchlist | Confirm a "Research" link with a microscope icon appears in the sidebar; click it and confirm the URL becomes `/research` and the Factor Lab loads (≤2 clicks from anywhere). |
| `/research` | `ResearchPage` (`app/research/page.tsx`) | New page | Stands up the Research home rendering the Factor Lab (J-25) | Navigate to `/research`; confirm the heading "Research — Factor Lab", the factor dropdown, horizon button group, caveat banner, decile table, and rank-IC card all render with the default factor (`leadership_score`) and default horizon (`20`). |
| `/research` | `FactorSelector` → `Select` (`data-testid="factor-select"`) | New form control | User selects which factor to analyze; options are config-driven from the server catalog | Open the dropdown and assert the `<option>` values exactly equal the server `factors` catalog keys: `leadership_score, entry_quality_score, risk_score, rs_spy_3m, ma_stack, high_proximity, up_down_vol, atr_pct`. Select `atr_pct` and confirm the decile table re-points (values change vs the previous factor). |
| `/research` | `HorizonSelector` button group (`data-testid="horizon-select"`) | New form control | User selects the forward-return horizon; buttons are config-driven from server `horizons` | Confirm one button per horizon (1d/5d/10d/20d/60d) with `aria-pressed` on the active one; click a different horizon (e.g. 60d) and assert the decile table and rank-IC values change (server values, no client recompute). |
| `/research` | `DecileTable` + `DecileValue` | New table | Displays D1…D10 mean forward return + downside risk-adjusted column with `n` | Confirm 10 rows D1→D10, each with a Factor range, a colour-graded Mean fwd return (%), a Risk-adjusted (downside) ratio, and a sample size `n`. Confirm the column header reads "Risk-adjusted (downside)" (downside, not total volatility). |
| `/research` | `DecileValue` (NA path) | New behavior | Low-sample / empty cells must show explicit "NA" + n, never fabricated | On a decile/horizon with `n < min_sample` or no observations, confirm the cell renders "NA" plus the `n` badge (not blank, not a number). Note: not triggerable on the committed seed — verify via backend unit tests `test_low_sample_decile_is_flagged_with_its_n` instead. |
| `/research` | `RankICCard` (`data-testid="rank-ic-value"`) | New component | Displays the Spearman rank-IC value + sign + n + interpretation | Confirm a large signed number (green positive / red negative / muted NA) with an `n` badge and a sentence interpreting the sign; switch factor and confirm the value and the interpretation sentence change. |
| `/research` | `CaveatBanner` | New component | Surfaces survivorship-bias / universe-relative / descriptive-not-predictive honesty labels | Confirm the warning-coloured banner shows the heading "Survivorship bias · universe-relative · descriptive" plus the survivorship and descriptive caveat text from the payload. |
| `/research` | `LabSkeleton` / error Card / `EmptyState` | New states | Loading, backend-error, and empty (`n_total === 0`) states styled like System Health | With the backend stopped, confirm the "Backend unavailable" card shows (no fabricated figures); on load confirm the skeleton appears then resolves to data. |
| `/research` | Page-level (J-18 guard) | New behavior | Cross-date aggregate — must expose NO date/as-of selector | Assert `/research` has no date picker / as-of control of any kind; the only controls are the factor dropdown and the horizon button group. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` (**new**) — read-only Factor-Lab analytics engine (`factor_catalog`, `compute_factor_lab`, `_downside_deviation`, `_risk_adjusted`, `_rank_ic`). Powers `/research` but is not itself a UI surface.
- `apps/backend/app/api/research.py` (**new**) — `GET /api/research/factor-lab?factor=&horizon=` (422 unknown factor / bad horizon; 503 no price data). Consumed by the `/research` page via `fetchFactorLab()`, so its data is visible there; the endpoint itself has no separate UI surface.
- `apps/backend/main.py` — registers `research.router` with `prefix="/api"`. No UI surface.
- `apps/backend/app/config.py` — new typed `FactorLabFactor`/`FactorLabCfg`/`ResearchCfg` + `parse_factor_source` + boot validators; `research` now required on `Config`. No direct UI surface (drives the catalog the dropdown renders).
- `config.yaml` — new `research.factor_lab` block (`deciles: 10` + 8-factor catalog). No UI surface; defines the dropdown options served to the UI.
- `apps/backend/tests/test_research.py`, `test_api_research.py` (**new**) and updates to `test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_no_magic_numbers.py` — tests only, no UI surface.
- `apps/frontend/lib/api.ts` — added `FactorLabResponse`/`FactorLabFactor`/`FactorDecileRow`/`RankIC` types + `fetchFactorLab()`. A client data helper, not a rendered surface (re-formats server values only; no client-side recompute).

---

## Summary

- **Frontend surfaces changed:** 2 files (`app/research/page.tsx` new, `components/sidebar.tsx` modified) + `lib/api.ts` client helper
- **New pages/routes:** 1 (`/research`)
- **Modified components:** 1 (`Sidebar` — additive nav item)
- **Navigation changes:** yes (new "Research" sidebar entry)
- **Backend-only changes:** 6 (engine, API router, main.py wiring, config models, config.yaml, tests)
