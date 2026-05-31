# Phase goal-i_can_see_the_wealthy_future-iter-12 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/methodology` | `app/methodology/page.tsx` (glossary page) | New page | J-12: a single config-backed catalog explaining every setup status + the VCP pattern | Navigate to `/methodology`; confirm **7 entry cards** render — the six setup statuses (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) and the VCP pattern. |
| `/methodology` | Entry card — Actionable | New component | Display each entry's meaning + config-matching thresholds + example | On the Actionable card, confirm the thresholds list shows `Leadership ≥ 80`, `Entry ≥ 70`, `Risk ≤ 60`, the Regime text rule, a plain-language meaning, and a worked example. |
| `/methodology` | Entry card — VCP | New component | VCP documented as a `kind:pattern` entry (J-16 step 4), never a 7th status | On the VCP card, confirm the **"Pattern"** chip (not "Setup") and threshold rows `Min contractions ≥ 2`, `Max base depth ≤ 35%`, shrink `≤ 0.9`, `Final ≤ 12%`, `Within pivot ≤ 8%`, `Volume dry-up ≤ 0.9`. |
| `/methodology` | Setup/Pattern `Badge` chip | New element | Distinguish setup statuses from the pattern | Confirm the six status cards show a **"Setup"** chip and only the VCP card shows a **"Pattern"** chip. |
| `/methodology` | Loading / error / empty states | New component | Standard data-fetch idioms | Stop the backend, reload `/methodology`; confirm an explicit **"Backend unavailable"** error card appears (no fabricated copy / no blank page). |
| `/stocks` | `InfoTooltip` on setup badge | New component | Inline catalog definition reachable on hover/tap/focus | On a stock row, click the ⓘ button next to the setup badge; confirm a `role="tooltip"` panel opens whose text **matches the `/methodology` meaning** for that row's status (e.g. an "Extended" row shows the Extended definition). |
| `/stocks` | `InfoTooltip` on VCP badge | New component | VCP definition reachable inline alongside the per-row reason | On a row flagged VCP, click the VCP badge's ⓘ button; confirm the panel shows the catalog VCP meaning, and the badge's native hover `title` still shows the per-row reason. |
| `/stocks` | `InfoTooltip` dismissal | Changed behavior | Click pins the panel; outside-click / Escape dismisses | Click a setup badge ⓘ to pin the panel open; press **Escape** (or click outside) and confirm the panel closes. |
| `/stocks` | Setup filter dropdown | Changed behavior | Options now sourced from the catalog instead of a hard-coded array | Open the Setup filter; confirm the six status options appear (catalog order), select **"Actionable"**, and confirm the leaderboard narrows to only Actionable rows (J-02 still works). |
| `/stocks` | Setup filter — fallback path | Changed behavior | Graceful degradation if the catalog fetch fails (protect J-02 / J-15) | With the methodology endpoint unavailable but the stocks data loaded, confirm the Setup filter still lists the statuses present in the data and still narrows rows. |
| `/stocks` | VCP filter | Regression check | Page now also fetches the catalog; VCP filter must be unaffected | Apply the **VCP** filter; confirm the leaderboard narrows to only VCP-flagged names (J-16 unchanged). |
| Sidebar (all pages) | `components/sidebar.tsx` — "Methodology" nav item | Added navigation | New top-level IA home for J-12 | Confirm a **"Methodology"** link with a book icon appears after "Watchlist"; click it and confirm it routes to `/methodology` and shows the active-state indicator. |

---

## Backend-Only Changes (No UI Impact)

- `config.yaml` — new top-level `methodology:` section (intro + 7 catalog entries). Drives the UI but is not itself a UI surface; its effect is visible only through `/methodology` and the `/stocks` tooltips/filter.
- `apps/backend/app/config.py` — new typed models (`MethodologyThreshold`, `MethodologyEntry`, `MethodologyCfg`), `resolve_ref` dotted-path resolver, and a boot `model_validator` that raises `ConfigError` on any unresolvable threshold reference — no UI surface (boot-time validation only).
- `apps/backend/app/engine/methodology.py` — NEW `build_catalog(config)`; resolves refs to live config values, asserts completeness (every `ALL_STATUSES` status + every `config.patterns` pattern is documented). Computes no score; reached only via the API.
- `apps/backend/app/api/methodology.py` + `apps/backend/main.py` — NEW `GET /api/methodology` endpoint and its router registration. Consumed by the frontend (so its data is visible), but the endpoint itself is not a UI surface.
- `apps/backend/tests/*` (`test_methodology.py`, `test_api_methodology.py`, `test_config.py`, `test_config_engine.py`, `test_no_magic_numbers.py`, plus `_SYNTH_CFG` fixture updates in `test_sectors.py` / `test_themes.py`) — tests only, no UI impact.
- **Empty-diff guarantee:** `models.py`, `scanner.py`, `scoring.py`, `setups.py`, `patterns.py`, `forward_testing.py`, and all pre-existing API routers are byte-unchanged — no behavioral change to any existing surface (J-01–J-11, J-13–J-16 cannot structurally regress).

---

## Summary

- **Frontend surfaces changed:** 3 (new `/methodology` page, `/stocks` page, sidebar)
- **New pages/routes:** 1 (`/methodology`; app routes 11 → 12)
- **Modified components:** 3 (`app/stocks/page.tsx`, `components/sidebar.tsx`, `lib/api.ts`) + 2 new (`app/methodology/page.tsx`, `components/ui/info-tooltip.tsx`)
- **Navigation changes:** yes — new "Methodology" sidebar item after Watchlist
- **Backend-only changes:** 5 source/config files (`config.yaml`, `config.py`, `engine/methodology.py`, `api/methodology.py`, `main.py`) + tests
