# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## What Was Built

### J-81 — Forward-return columns on the Themes & Sectors leaderboards (new read surface, no new canonical value)
- Each `/api/themes` row now additively carries `forward_returns` — one entry per `config.walk_forward.horizons` value (1/5/10/20/60d), the **equal-weight member-basket** realized forward return for the resolved as-of run.
- Each `/api/sectors` row now additively carries `forward_returns` — same five entries, the **sector/industry ETF's own** realized forward return.
- Both are read VERBATIM via the SAME `forward_testing:_leadership_returns` builder Backtest's Top Themes / Top Sectors already use, so a theme/sector value on its leaderboard is **byte-identical** to Backtest's for the same date+horizon (J-06 single-source). Absent members are skipped (never counted as 0); `None`/NA where no member / no stored row (so at/near latest all five are honestly NA).
- The per-horizon `ret_by_symbol` projection is built ONCE per request (one `forward_returns` SELECT for the whole run) — no second query per horizon per row.
- Frontend: `/themes` and `/sectors` each render five sortable, colour-graded, NA-honest forward-return columns reusing the shared `@/components/forward-return` helper (`fmtPct` + `returnClass`). Sort is the J-48 view-transform (re-orders rendered rows only; default stays the served theme/sector rank; NA-last in both directions).

### J-82 — Regime × Setup × Pattern table view/serve fixes (read-only; no canonical value changes)
- **(a) NA-last sorting** (`/research` RSP table): every numeric column sort now treats a cell as NA using the SAME predicate the cell DISPLAY uses (`low_sample || n === 0 || value === null`), so a low-sample row whose raw value is a real number (DISPLAYS NA) now also SORTS NA — sinking last in both directions.
- **(b) Three filter dropdowns** (Regime / Setup / Pattern, each default "All") built from the config-driven payload vocabulary (`regime_labels` / `setups` / `patterns` / `pattern_none`). Pure view transforms that compose with the sort; an honest empty-after-filter state.
- **(c) Samples validation reconciliation** (`_regime_setup_pattern_samples`): acceptance is now reconciled to EXACTLY the set of `(regime, setup, pattern)` combinations `compute_regime_setup_pattern_study` actually emits — derived from the SAME observation set via the SAME `_rsp_combination_members` rule. Every displayed row's N= chip (incl. `pattern = none`) opens its exact cohort without a 4xx, and `total == the row's n` by construction in BOTH Episodes & Pooled and BOTH All-history & As-of. A genuinely non-emitted combination still raises an honest 4xx.
- **(d) Pooled default for the RSP section only**: implemented in the frontend section toggle's initial state (`useState<EventStudyView>("pooled")`). The canonical `compute_regime_setup_pattern_study` default param stays `episodes`, and the rest of `/research` (J-29/J-63) keeps its Episodes default — no canonical figure changed.

## Files Changed
- `apps/backend/app/engine/snapshot_serving.py` — J-81: import `_leadership_returns`; new `_leadership_returns_by_horizon` (per-horizon projection, one SELECT) + `_forward_returns_from_projection` helpers; `themes_payload`/`sectors_payload` accept an optional `config` and attach `forward_returns` to each row.
- `apps/backend/app/engine/samples.py` — J-82(c): widen `_regime_setup_pattern_samples` validation to the study's emitted-combination set (via `_rsp_combination_members`); removed now-unused `ALL_STATUSES` / `PATTERN_NONE` imports, added `_rsp_combination_members`.
- `apps/frontend/lib/api.ts` — add `forward_returns: ForwardReturnEntry[]` to `ThemeRow` and `SectorRow`; introduce the shared `ForwardReturnEntry` type (`StockForwardReturn` kept as an alias).
- `apps/frontend/app/themes/page.tsx` — five sortable forward-return columns + `SortHeader`/`ForwardReturnCell`; sort state + stable NA-last memo.
- `apps/frontend/app/sectors/page.tsx` — same five columns/contract; aliased the shared `fmtPct` to avoid colliding with the page's local no-sign `fmtPct`.
- `apps/frontend/app/research/page.tsx` — RSP NA-last sort (display predicate); three "All"-default filter dropdowns (`RspFilters`) + empty-after-filter state; RSP section toggle defaults to Pooled.
- `apps/backend/tests/test_iter23_leaderboard_returns.py` — NEW: J-81 coherence (themes/sectors == Backtest `_leadership_returns`), equal-weight basket, NA-at-latest; J-82(c) every-emitted-combination count-coherence (Episodes + Pooled, All + As-of), `pattern = none` drill-down, genuinely-invalid 4xx.
- `apps/backend/tests/test_iter20_research_cluster.py` — updated `test_j77_samples_invalid_selectors_raise` to the J-82(c) reconciled contract (a config-valid but non-emitted `(Choppy, Avoid, none)` now 4xxes — it has no N= chip).

## Tests Run
Command (targeted modules — the full suite is ~34 min and handed to the pump per the standing rule):
`cd apps/backend && .venv/bin/python -m pytest tests/test_themes.py tests/test_sectors.py tests/test_samples.py tests/test_iter20_research_cluster.py tests/test_api_research.py tests/test_api_backtest.py tests/test_forward_testing.py tests/test_backtest_scorecard.py tests/test_iter23_leaderboard_returns.py -q`

Result: after the one updated test, all targeted modules pass — `test_iter23_leaderboard_returns.py` 12/12; `test_iter20_research_cluster.py` 16/16; the broader targeted batch was 191 passed + 1 (now-fixed) → 192 passing. Frontend `npx tsc --noEmit` exits 0 (no type errors).

**Full pytest suite: NOT run here** — ~34 min / 639+ tests exceeds the subagent Bash cap (the loaded_engine warm-up alone is ~4.5 min). Handed to the pump to run `nohup`-async; targeted fix tests are green and the full re-run is the gate.

## Known Issues
- The full backend pytest suite has not been run in this turn (handed to the pump per the iter-21/iter-22 standing rule and the backend-test-suite-runtime lesson). Targeted coverage of every changed path (snapshot-serving themes/sectors, forward_testing leadership-returns coherence, samples regime-setup-pattern, research event-study byte-identity) is green.
- No live dev-server / browser smoke was run here (additive read-path + view-transform changes; the endpoints are exercised end-to-end via FastAPI TestClient in the new test file). Live browser verification is the browser-qa stage's job — it should use ports backend 8835 / frontend 3835 and never broad-`pkill` (multi-project machine). For the controlled filter `<select>`s, drive via native-setter + bubbling `change` event then assert live DOM (Chrome MCP `select` doesn't fire React onChange on this frontend).
- No new config keys were introduced (no inline-test-config-dict churn needed).
- **Contract change to be aware of (J-82c):** for the regime-setup-pattern samples kind ONLY, a config-valid-vocabulary combination that the study does not emit now returns a 4xx instead of an empty 200. This is intentional (a non-emitted combination has no N= chip / no published N to be coherent with) and supersedes the iter-20 "valid n=0 returns empty" premise for this kind. Other sample kinds (factor deciles, event-study slices) keep their valid-n=0 empty-200 behaviour unchanged.
