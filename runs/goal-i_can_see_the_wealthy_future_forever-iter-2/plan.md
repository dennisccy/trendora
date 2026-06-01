# goal-i_can_see_the_wealthy_future_forever-iter-2 Execution Plan

**Target journey:** J-19 — Diagnose weak forward-test returns via attribution (full depth).
**Critical anti-goal in play:** *Attribution is read-only* (extends *No recompute in the read path*).

Verified against source before planning: `app/engine/forward_testing.py` already builds the exact
`stock_obs` list this journey needs in **both** `compute_forward_aggregates` (keys: `run_id, ticker,
return, bucket, setup, sector, rank, regime, is_vcp`) and `compute_run_scorecard` (per-horizon; keys:
`run_id, ticker, return, bucket, setup, sector, rank`). `_group_means(obs, group_attr, label_key,
order, pad)` exists with that exact signature; the `by_vcp` block (forward_testing.py:462-465) is the
plug-in model. `walk_forward.control_group` (config.yaml:496-499) + `ControlGroupCfg`/`WalkForwardCfg`
(config.py:288-321) are the typed-accessor model to mirror. Frontend `ForwardGroupRow`,
`SystemHealthResponse`, `BacktestScorecardHorizonRow` (api.ts:343-441) and the `Return`/`fmtPct`/
`returnClass`/`BreakdownPanel`/`HorizonSelector` primitives (system-health/page.tsx) all exist.
**This iteration is additive — no existing value is recomputed, no new endpoint, no nav change.**

## What to Build

- **config** — add a `walk_forward.attribution` block (no magic numbers): `rank_bands` as an ordered
  list of `{label, min, max}` (e.g. `1–10`/`11–50`/`51+`, with `max: null` for the open top band) and
  `top_contributors_k` (list length, e.g. 5). Add a typed `AttributionCfg` to `app/config.py` nested
  under `WalkForwardCfg` (mirror `ControlGroupCfg`: validate bands non-empty, monotonic/positive
  edges, `top_contributors_k > 0`).
- **engine** — ONE shared helper `_attribution_slices(stock_obs, cfg)` in `forward_testing.py` that
  takes the **already-built** `stock_obs` and returns four read-only slices (recomputing no return,
  issuing no new bar/`forward_returns` query):
  - `per_stock` → `{contributors: [...], detractors: [...]}`, each row `{ticker, mean_return, n,
    sector}`: aggregate each ticker's stored realized returns over the same observations (mean + n),
    sort desc for contributors / asc for detractors, take `top_contributors_k` each.
  - `by_sector` → `_group_means(stock_obs, "sector", "sector", <config sector-name order>, pad=False)`.
  - `by_rank_band` → map each obs's stored `rank` to its config band label (drop `rank is None`), then
    `_group_means(..., "rank_band", "rank_band", <band-label order>, pad=True)` (every band shows; n=0
    → mean None).
  - `distribution` → `{mean_return, median, pct_positive, dispersion, n}` over `[o["return"] for o in
    stock_obs]` (`pct_positive` = share > 0; `dispersion` = stdev; `median` via `statistics.median`;
    `n<2` → `dispersion: null`; empty → all-None, `n: 0`).
  - Call from `compute_forward_aggregates(...)` → add `attribution` key (keyed to the requested
    `horizon`). Call from `compute_run_scorecard(...)` per horizon → add `attribution` to each
    `by_horizon` entry. No API/route change — the data rides the existing payloads verbatim.
- **frontend api types** — extend `SystemHealthResponse` and `BacktestScorecardHorizonRow` with an
  `attribution` object; add `PerStockRow` and `Distribution`; add `BySectorRow`/`ByRankBandRow extends
  ForwardGroupRow` (matching the existing `ForwardBucketRow` convention). No fetcher signature change.
- **frontend UI** — a single **shared** `ReturnAttributionSection` component (four panels) consumed by
  BOTH pages so the contract value renders identically:
  - `/system-health`: append the section below the existing panels; it reads `data.attribution` and
    **rides the page's existing horizon refetch** (no new selector — System Health already owns one).
  - `/backtest`: append the section; add a small **client-side horizon selector** that picks which
    `by_horizon[*].attribution` to show from data **already in the payload** — NO refetch, NO new fetch
    param, NO date state (see Coherence Guardrails).
  - Honest states: `n=0` slice → "—" (NA); `n < min_sample` → existing `⚠` low-sample treatment;
    no-elapsed-window → existing empty-state copy. Never a fabricated number.

## Agents Required
- developer: yes — one developer covers both tracks (the developer agent handles backend + frontend).
  - backend-data: yes — config block + `AttributionCfg` + `_attribution_slices` + wiring into both
    engine payloads + unit/consistency tests.
  - frontend-ux: yes — `api.ts` types + the shared `ReturnAttributionSection` + grafting it onto
    `/system-health` and `/backtest` (with the no-refetch horizon selector on Backtest).

Frontend Present: yes

## Files to Create/Modify
- `config.yaml` — add `walk_forward.attribution: { rank_bands: [...], top_contributors_k: N }`.
- `apps/backend/app/config.py` — add `AttributionCfg`; add `attribution: AttributionCfg` to
  `WalkForwardCfg` with validation (mirror `ControlGroupCfg`).
- `apps/backend/app/engine/forward_testing.py` — add `_attribution_slices(stock_obs, cfg)`; attach
  `attribution` in `compute_forward_aggregates` and per-horizon in `compute_run_scorecard`.
- `apps/backend/tests/test_forward_testing.py` — read-only/consistency + config-band + honesty/edge
  unit tests (see Key Test Scenarios). Add API-shape assertions to
  `tests/test_api_system_health.py` and `tests/test_api_backtest.py` / `tests/test_backtest_scorecard.py`.
- `apps/frontend/lib/api.ts` — new `attribution` types on the two response types; `PerStockRow`,
  `Distribution`, `BySectorRow`, `ByRankBandRow`.
- `apps/frontend/components/return-attribution.tsx` — **new** shared four-panel section (per-stock
  contributors/detractors table, by-sector, by-rank-band, distribution & hit-rate) reusing
  `Return`/`fmtPct`/`returnClass`/`SampleSize` from `@/components/forward-return` and palette tokens.
- `apps/frontend/app/system-health/page.tsx` — render `<ReturnAttributionSection a={data.attribution}/>`
  below the existing grid (rides the existing horizon state).
- `apps/frontend/app/backtest/page.tsx` — add a client-side horizon-view selector + render the section
  for the selected `by_horizon[h].attribution`. **Preserve:** no page-local date state; still reads
  only `useAsOf()`.
- Dev handoff: `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-2-dev.md`.

## UI Evolution
- **New user-facing capability:** on `/system-health` (aggregate) and `/backtest` (single resolved
  date), open any forward-test mean into four diagnostic layers for a chosen horizon — which tickers
  drove/dragged it, which sectors and rank-bands carried it, and its distribution shape.
- **New information displayed:** per-stock top contributors & detractors (ticker + realized mean
  return + n + sector); by-sector mean fwd return (+n); by-rank-band mean fwd return for the config
  bands 1–10 / 11–50 / 51+ (+n); distribution panel (mean, median, % positive/hit-rate, dispersion, n).
- **New user actions:** a horizon selector on `/backtest` choosing which horizon's per-date
  attribution to view (data already in payload — no refetch). System Health rides its existing
  horizon selector. No other new control.
- **UI surface changes:** a new "Return attribution" section (four panels) appended to
  `/system-health` and `/backtest`. No new page.
- **Navigation changes:** none (both surfaces already have canonical homes in the nav skeleton — no
  re-approval needed).

## Visual Requirements
- **Component patterns:** reuse `Card` + `PanelTitle`-style headers and the existing `BreakdownPanel`
  table pattern for by-sector / by-rank-band; a compact two-column table (contributors | detractors)
  for per-stock; a small key/value stat row for distribution. All numbers via the existing `Return` /
  `fmtPct` / `returnClass` / `SampleSize` primitives so n / NA / low-sample render identically to the
  current panels.
- **Layout:** the four panels sit in the existing responsive grid (`grid-cols-1 lg:grid-cols-2`) under
  the current System Health panels; on Backtest, the section follows the scorecard with the horizon
  selector styled like the System Health `HorizonSelector` (segmented buttons).
- **Key visual effects:** dark analytical-workstation tokens only (`--surface`, `--border`, `--pos`,
  `--neg`, `--warn`); monospace/tabular-nums for every figure; positive/negative return colour-grading
  via `returnClass`; low-sample `⚠` in `--warn`. No new ad-hoc colours.
- **States to handle:** loading (existing skeletons), empty / no-elapsed-window (existing empty-state
  copy), per-slice `n=0` → "—" NA, `n < min_sample` → `⚠`. Backend-unavailable uses the existing error
  card. Nothing fabricated.

## Key Test Scenarios
- **Backend — read-only / consistency (the critical anti-goal):** for the aggregate path, the
  `distribution.mean_return` equals the existing `overall.mean_return`; by-sector and by-rank-band row
  `n`s sum to `overall.n` (holds because universe `scanner_results` rows all carry a `sector` and a
  `rank`; `rank is None` is excluded from bands — assert on a fixture where every obs has both). Assert
  the slices introduce **no new `forward_returns`/price-bar query** (same observation set as the
  aggregate).
- **Backend — config-driven bands (no magic numbers):** band labels/edges come from
  `walk_forward.attribution.rank_bands`; changing the config changes the emitted bands;
  `top_contributors_k` controls contributor/detractor list length. No band edge or list size literal
  in calc code.
- **Backend — honesty / edge cases:** empty `stock_obs` → all four slices NA with `n=0` (no fabricated
  0%); single-observation distribution → `dispersion: null`; a rank-band with no members → padded row
  `{mean_return: None, n: 0}`; per-date attribution at a horizon with no elapsed window → NA, not a
  number.
- **Backend — no-lookahead inheritance:** attribution reads only stored `forward_returns` (date > D) ⋈
  stored `scanner_results` — no direct bar access — so the existing guarantee is unaffected.
- **Backend regression:** full pytest suite stays green (was **248/0** at iter-1).
- **Browser — J-19 (primary):** `/system-health` at a horizon with samples — all four panels render
  numbers with n, named tickers + realized returns, by-sector / by-rank-band with n, distribution
  (mean/median/% positive/dispersion). `/backtest` — pick a historical date with ≥60 post-snapshot
  bars, read the four panels for a selected horizon; then a recent date → low/empty horizons show NA + n.
- **Browser — regression (must stay green):** J-09, J-10 (System Health existing panels + control
  group unchanged), J-14 + J-18 + J-13 (Backtest scorecard + single global as-of switcher intact —
  **drive date changes via in-app nav, not a hard reload**, per the iter-1 lesson), J-01.
- **Browser — opportunistic re-verify (no code):** J-02, J-06, J-11, J-15, J-16 — capture fresh
  evidence; the evaluator decides conversion.

## Assumptions & Coherence Guardrails
- **The Backtest horizon selector is a view selector, NOT a date control.** It selects which
  already-fetched `by_horizon[*].attribution` to display; it triggers no refetch, takes no fetch param,
  and keys no effect on a date. The page MUST continue to read only `useAsOf()` and hold **no
  independent date state** (preserves J-18 / *Exactly one date selector* / coherence invariant #5).
  This is the single highest false-positive regression risk — call it out in the dev handoff so the
  reviewer / coherence-auditor / J-18 re-verify do not misread the new `useState<number>` (horizon) as
  reintroduced date state.
- **One shared rendering component** for the four panels (consumed by both pages) so the same contract
  value is not given two divergent UI homes (coherence-friendly; avoids a duplicate-home finding).
- **Per-date distribution is over the full observed set at that horizon**, not the top-ranked cohort —
  so on `/backtest` `distribution.mean_return` need not equal the scorecard's headline `cohort` mean
  (the cohort is rank ≤ top_n only). The mean==overall consistency assertion applies to the
  **aggregate** (`compute_forward_aggregates`, which has an `overall`). Note this so QA/reviewer do not
  expect equality on Backtest.
- **by_sector order** is config-derived (e.g. `list(cfg.etfs.sector.values())`) or sorted — never a
  hard-coded sector list in calc code.

## Out of Scope (excluded; do not start)
- J-17 Data Manager (`/data`, `/api/data`, fetch/backfill) — the other failing journey, a separate
  larger iteration.
- Any change to how a return/score/bucket/setup/regime is **computed** (attribution only reads+groups).
- Any new endpoint, any new `?param` beyond the existing `horizon`, any Backtest refetch for the
  horizon selector.
- Re-pointing / persisting the as-of date (the global as-of stays an in-memory provider — no
  URL/localStorage persistence).
- Tuning scoring weights/thresholds.
