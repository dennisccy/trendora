# Phase goal-i_can_see_the_wealthy_future_forever-iter-28 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-28
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| All pages (layout shell) | `HealthBadge` in the top-bar header | Changed behavior | Badge now renders three readiness states (Ready / Initializing / Unavailable) plus an initial "Checking backend…" loading state, driven by the shared `ReadinessProvider` | With a warm backend, confirm the badge shows a green dot labeled "Ready"; inspect the `data-state` attribute on the badge element and confirm it equals `"ready"` |
| All pages (layout shell) | `HealthBadge` — Initializing state | New UI state | Backend warm-up progress must be displayed honestly while historical snapshots are still being produced | On a backend that is actively warming (fresh/fixture DB or simulated), confirm the badge shows an amber animated dot with text "Initializing… history N/M" where N and M are numeric integers (not zero/zero and not equal) |
| All pages (layout shell) | `HealthBadge` — Unavailable state | Changed behavior | Unavailable state now represents DB-down or no-latest-snapshot, distinguished from the Initializing state | With the backend stopped, reload any page and confirm the badge shows a red dot labeled "Backend unavailable" and the `data-state` attribute equals `"unavailable"` |
| All pages (layout shell) | `ReadinessProvider` context wrapper in `layout.tsx` | New component | Single shared readiness poll source mounted at the root so all pages read the same value without separate fetches | Navigate between Dashboard, Stocks, Sectors, and Backtest in sequence; confirm the badge does not re-fetch or flicker between pages (a single provider is mounted once per session) |
| `/backtest` | `WarmingState` card replacing the forward-test scorecard area | New UI state | During background warm-up the scorecard area must honestly show "Warming up" instead of an error or an empty result | On a warming backend, navigate to `/backtest` and confirm the card displays the text "Warming up — historical evidence still loading" (with n/m progress); confirm no "Backend unavailable" error card is shown instead |
| `/backtest` | Backtest page auto-populate on readiness flip | Changed behavior | Page now includes `readiness` in its fetch-effect dependency array so it re-fetches and renders results the moment the badge flips to Ready | With a warming backend, stay on `/backtest` while the badge transitions from Initializing to Ready; confirm the warming card disappears and the forward-test scorecard populates without a manual page refresh |
| `/research` | `WarmingState` card replacing the Factor Lab, Combination Lab, and Event Study sections | New UI state | All three research labs must show the honest warming state instead of empty/error results during background warm-up | On a warming backend, navigate to `/research` and confirm the warming card displays text "Warming up — historical evidence still loading" and that none of the three lab sections (decile table, combination table, event-study table) are visible underneath it |
| `/research` | Research page auto-populate on readiness flip | Changed behavior | The Factor Lab effect now includes `readiness` as a dependency so all three labs re-fetch and render the moment the badge flips to Ready | With a warming backend, stay on `/research` while the badge transitions from Initializing to Ready; confirm the warming card disappears and the Factor Lab decile table, Combination Lab table, and event-study horizons table all populate without a manual page refresh |
| All pages (via `lib/api.ts` types) | `HealthStatus` API type — extended with `readiness`, `warmup`, `poll_interval_seconds`, `poll_idle_interval_seconds` | Changed behavior | Frontend API contract extended to carry readiness state and config-derived poll cadences from `GET /api/health` | Call `GET /api/health` directly and confirm the JSON response includes a `readiness` string field (`"ready"`, `"initializing"`, or `"unavailable"`), a `warmup` object with integer `done` and `total` fields, and numeric `poll_interval_seconds` and `poll_idle_interval_seconds` fields |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/warmup.py` (new) — daemon-thread warm-up controller (`ensure_latest_snapshot`, `start_warmup`, `_run_warmup`); produces warm-up progress used by `GET /api/health` — its output IS surfaced in the badge, but the module itself has no direct UI surface
- `apps/backend/app/engine/readiness.py` (new) — single readiness producer `compute_readiness`; result served exclusively through the extended `GET /api/health` endpoint (single serving path, no second `/api/readiness` route)
- `apps/backend/app/engine/scanner.py` — `IntegrityError` guards on `run_scan` flush + commit; concurrency-safe idempotent create path — behavior change is a robustness fix (no new UI state; the guard returns the existing immutable row silently)
- `apps/backend/app/engine/forward_testing.py` — `_commit_forward_returns_concurrency_safe` on both backfill commit paths — same as above, internal robustness with no UI surface
- `apps/backend/main.py` — lifespan split into minimal sync + background warm-up; the user-visible outcome is faster availability, surfaced through the badge, but the lifespan code itself is backend-only
- `apps/backend/app/config.py` + `config.yaml` — new `StartupCfg` / `startup` block with `readiness_budget_seconds`, `warmup_batch_size`, `health_poll_interval_seconds`, `health_poll_idle_interval_seconds`; these values reach the frontend via the `GET /api/health` payload fields, not a new UI config surface
- `apps/backend/tests/test_warmup.py` (new), `test_health.py`, `test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py` — test files; no UI surface

---

## Summary

- **Frontend surfaces changed:** 4 (HealthBadge, ReadinessProvider in layout, Backtest page warming gate, Research page warming gate)
- **New pages/routes:** 0
- **Modified components:** 3 (`health-badge.tsx` extended, `backtest/page.tsx` warming gate added, `research/page.tsx` warming gate added)
- **New components:** 2 (`readiness-provider.tsx`, `warming-state.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 7
