# goal-i_can_see_the_wealthy_future-iter-2 Execution Plan

Indicators + Market Regime + Sector/Industry Leadership — the **first canonical values**, computed
once in `apps/backend/app/engine/` and served read-only from one endpoint each. Lights up **J-04**
(Sector Leaderboard) and **partially** advances **J-01** (regime + breadth + data-as-of + Top Sectors
on the Dashboard). On-request, deterministic against the frozen seed; **no persistence** (iter-5),
**no live fetch**, **no per-stock/theme scoring** (iter-3).

> Central risk this iteration: the **Single source of truth** anti-goal goes live. Each value =
> exactly ONE computing module + ONE serving endpoint, and the Dashboard's Top Sectors must READ
> `/api/sectors` (no second computation). A second code path for any registered value is a hard
> coherence-auditor fail.

## What to Build

**Config (additive — every number lives here; no literal in calc code)**
- `indicators:` section (NEW): MA periods `[20,50,150,200]`, RS lookback windows 1m/3m/6m (trading
  days), ATR period, 52-week-high window, volume-average period, and a `min_history_bars` floor
  (below it long MAs/RS report **NA**, never fabricated).
- `sectors:` section (NEW): sector-score component **weights** (`rs_spy_1m`, `rs_spy_3m`, `rs_spy_6m`,
  `ma_stack`, `dist_from_high`, `vol_trend`) + **trend-label cutoffs** (score → label).
- `regime:` — add `label_edges` only (score→label cutoffs covering 0–100 → one of the six existing
  `regime.labels`). Keep existing `vix_threshold` + `weights`.
- `app/config.py`: type + **validate** the three sections — explicit `ConfigError` on missing/invalid
  (label_edges not covering 0–100, weights missing/insane). `scores`/`decision_rules`/`walk_forward`
  stay scaffolded (untyped, `extra="allow"`) — not consumed this iteration.

**Backend engine — `apps/backend/app/engine/` (new package; names match the Data Contract verbatim)**
- `prices.py` → `bars_asof(session, symbol, d)`: rows with **date ≤ d**, ascending. The no-lookahead
  boundary; **all** engine math reads bars through it.
- `indicators.py` → pure, DB-free, deterministic functions on a price series: `sma`, `rs_vs`,
  `atr_pct`, `dist_from_high`, `ma_stack`, `vol_trend`. Periods come from `config.indicators`.
- `buckets.py` → `to_bucket(score)` = A/B/C/D/E from `config.buckets`. The ONLY place A–E is derived.
- `regime.py` → `score_regime(session, asof)`: `{score 0–100, label, breadth_above_50dma,
  breadth_above_200dma, new_high_low, components[], asof_date}`. Inputs (weights from `config.regime`):
  index MA-stack (SPY/QQQ), universe breadth above 50/200-DMA, universe-relative new-high/low, `^VIX`
  gate. Label via `regime.label_edges`. Breadth/new-high-low are **universe-relative**.
- `sectors.py` → `score_sectors(session, asof)`: list ranked by Sector Score descending; one row per
  **sector ETF (11 GICS SPDRs, `kind="sector"`) and per industry-group ETF (`kind="industry"`)**, each
  `{ticker, kind, name, score 0–100, bucket (via to_bucket), rs_vs_spy, dist_from_52w_high_pct,
  trend_label, components[], rank}`. **SPY is the RS benchmark — excluded from ranked rows.**
  Short-history ETFs (WGMI, BKCH, GEV) report **NA** for long MAs/RS — no crash, no fabrication.

**Backend API — `apps/backend/app/api/` (registered under `/api` in `main.py`, like `health`)**
- `GET /api/sectors` (`sectors.py`) → `score_sectors(asof=latest_data_date)`. Canonical & only endpoint
  for Sector Score.
- `GET /api/dashboard` (`dashboard.py`) → `{regime:{score,label,components}, breadth:{above_50dma_pct,
  above_200dma_pct, label:"universe-relative"}, asof_date, candidate_counts: null, top_themes: null}`.
  Canonical & only endpoint for the Market Regime value. `candidate_counts`/`top_themes` returned
  **explicitly null** (iter-3) — never a fabricated number.
- as-of date for both = `max(daily_prices.date)` (deterministic on the frozen seed).

**Frontend — `apps/frontend/`**
- `lib/api.ts`: add typed `fetchSectors()` + `fetchDashboard()` clients and matching interfaces.
  **Re-format only — no score/bucket/return computed client-side.** Throw on non-200 so callers render
  an explicit unavailable state (mirror the existing `fetchHealth` pattern).
- `/sectors` page: replace empty state with a **dense ranked table** (Card/Badge, `.num` tabular-nums,
  palette tokens) — columns: ticker · kind · **Sector Score (A–E bucket foregrounded + raw 0–100,
  green→red graded)** · **RS-vs-SPY** · **dist-from-52w-high %** · **trend label**; each row expands to
  its **component breakdown** (explainability — no bare numbers). SPY absent. Loading / empty /
  **"Backend unavailable"** states.
- `/` (Dashboard) page: replace empty state with a **Market Regime panel** (six-label badge + 0–100
  score + component breakdown), a **breadth %** labelled **"universe-relative"**, a **"Data as-of
  <date>"** indicator, and a **Top Sectors** list (≥3) that **fetches `/api/sectors`** and slices top N
  (SAME data as the leaderboard). **Candidate counts** and **Top Themes** render an explicit
  **"pending — arriving in a later iteration"** placeholder (not zeros). Loading + "Backend
  unavailable" states.

## Agents Required
- developer: yes -- single-phase TDD across backend engine + API + frontend, per the spec's DoD.
- backend-data: yes -- config sections + validation, the `app/engine/` package (prices/indicators/
  buckets/regime/sectors), `GET /api/sectors` + `GET /api/dashboard`, pytest suite with exact-value
  asserts.
- frontend-ux: yes -- `lib/api` clients + interfaces, populated `/sectors` ranked table + `/` dashboard
  (regime panel, breadth, data-as-of, Top Sectors), with loading/empty/unavailable states.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

**Create**
- `apps/backend/app/engine/__init__.py` -- new engine package.
- `apps/backend/app/engine/prices.py` -- `bars_asof` no-lookahead accessor.
- `apps/backend/app/engine/indicators.py` -- pure indicator functions.
- `apps/backend/app/engine/buckets.py` -- single `to_bucket(score)`.
- `apps/backend/app/engine/regime.py` -- `score_regime`.
- `apps/backend/app/engine/sectors.py` -- `score_sectors`.
- `apps/backend/app/api/sectors.py` -- `GET /api/sectors`.
- `apps/backend/app/api/dashboard.py` -- `GET /api/dashboard`.
- `apps/backend/tests/test_indicators.py` -- exact hand-computed values + NA on short history.
- `apps/backend/tests/test_prices_asof.py` -- includes date=d, excludes date>d.
- `apps/backend/tests/test_buckets.py` -- correct letter at each config edge (incl. E below D).
- `apps/backend/tests/test_regime.py` -- score∈[0,100], label∈six, boundary mapping, breadth∈[0,100], components.
- `apps/backend/tests/test_sectors.py` -- ranked descending, row fields present, SPY excluded, determinism.
- `apps/backend/tests/test_api_engine.py` -- TestClient shape + served==engine (no drift); dashboard null counts/themes.
- `apps/backend/tests/test_config_engine.py` -- `ConfigError` on missing/invalid indicators/sectors/`label_edges`.

**Modify**
- `config.yaml` -- add `indicators:` + `sectors:`; add `regime.label_edges`.
- `apps/backend/app/config.py` -- typed+validated `IndicatorsCfg`/`SectorsCfg`/`RegimeCfg`.
- `apps/backend/main.py` -- `include_router` for `sectors` + `dashboard` under `/api`.
- `apps/frontend/lib/api.ts` -- `fetchSectors()`, `fetchDashboard()` + interfaces.
- `apps/frontend/app/sectors/page.tsx` -- populated ranked leaderboard table.
- `apps/frontend/app/page.tsx` -- populated dashboard (regime + breadth + data-as-of + Top Sectors + pending placeholders).
- (optional, only if it reduces duplication) a small `components/score-badge.tsx` or
  `components/component-breakdown.tsx` reused by both pages — keep minimal, no speculative props.

> Recommended frontend approach: `"use client"` pages that fetch on mount with loading/error state
> (consistent with `components/health-badge.tsx`), so the **"Backend unavailable"** state renders
> cleanly in-browser. A server component with try/catch is acceptable if all three states still render.

## UI Evolution (Frontend Present: yes)
- New user-facing capability: open `/sectors` to see every sector & industry ETF **ranked by a real
  Sector Score** with RS-vs-SPY, distance-below-52w-high, and a trend label — expand any row for the
  component breakdown. On `/` read today's **market regime** (label + score + why), universe-relative
  breadth, the data-as-of date, and the strongest sectors at a glance.
- New information displayed: Market Regime score + label + components; market breadth (% above
  50/200-DMA, universe-relative); data-as-of date; per-row Sector Score (A–E + raw), RS-vs-SPY,
  dist-from-52w-high %, trend label, component breakdown.
- New user actions: expand a sector row to reveal its component breakdown (read-only; no forms).
- UI surface changes: `/sectors` empty state → populated ranked table; `/` empty state → populated
  dashboard with regime panel + breadth + data-as-of + Top Sectors and honest **pending** placeholders
  for candidate counts / Top Themes.
- Navigation changes: **none** — `/sectors` and `/` are existing IA homes; no new routes, no nav edit.

## Visual Requirements (Frontend Present: yes)
- Component patterns: shadcn-style `Card` (panels), `Badge` (regime label, A–E bucket, trend label),
  a dense table for the leaderboard; expandable row / inline tooltip for component breakdowns. No raw
  `<div>` soup where a primitive exists.
- Layout: existing sidebar + main content; `/sectors` = full-width dense ranked table (horizontally
  scrollable < ~640px); `/` = dashboard grid (regime panel + metric cards + Top Sectors list).
- Key visual effects: A–E score cells **colour-graded green→red** using palette tokens (`--pos`
  `#34d399` → `--neg` `#f87171`); numbers in monospace `.num` tabular-nums; `--warn` `#fbbf24` for the
  universe-relative/pending honesty labels. No arbitrary hex.
- States to handle: **loading** (skeleton/placeholder), **empty** (no rows), and explicit **"Backend
  unavailable"** (red, no fabricated rows/scores) on both pages; short-history rows show **NA**, not a
  fabricated value.

## Key Test Scenarios
1. **J-04 (browser, must pass):** `/sectors` renders multiple rows ranked by Sector Score
   (non-increasing); the top row shows a numeric **RS-vs-SPY** + **dist-from-52w-high %** + **trend
   label**; **SPY is not a ranked leader**. Screenshots to the evidence dir.
2. **J-01 (browser, partial — NOT expected green):** `/` shows the regime **label (one of six) +
   numeric 0–100 score**, a **universe-relative breadth %**, a **data-as-of date**, and **≥3 Top
   Sectors with scores** sourced from `/api/sectors`; candidate counts + Top Themes show the **pending**
   placeholder (no fabricated numbers). Screenshots. Confirm **both** servers up & stable; verify via
   on-disk evidence (iter-1 lesson).
3. **Single source of truth:** served `/api/sectors` & `/api/dashboard` values equal the engine outputs
   (no recompute drift); the Dashboard's Top Sectors values match `/api/sectors`; frontend recomputes
   nothing. (Coherence-auditor → COHERENCE-PASS.)
4. **No-lookahead boundary (unit):** `bars_asof` includes date = d, excludes date > d.
5. **No magic numbers:** a grep finds no period/weight/cutoff/bucket-edge literal in
   `app/engine/{indicators,regime,sectors,buckets}.py`.
6. **Determinism:** same `asof` → byte-identical regime + sector outputs across repeated calls.
7. **Explainable / honest:** every regime + sector score carries its named components in API and UI;
   breadth + new-high/low labelled "universe-relative".
8. **Error paths:** symbol with `< min_history_bars` → NA (no crash, no fabrication); missing/invalid
   new config → explicit `ConfigError`; backend unreachable → frontend "Backend unavailable".
9. **Buckets:** `to_bucket` correct letter at each config edge (A/B/C/D boundaries + E below D).
10. **Regression:** the existing **25 backend tests** still pass; `npm run build` still compiles +
    typechecks.

## Scope Flags / Assumptions (documented, not blocking)
- **In-scope reconciliation already done in the contract:** the blueprint's *Iteration serving notes*
  (`runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`, lines 78–82) **already records**
  the additive clarification (engine modules under `app/engine/`; iter-2 on-request serving; persistence
  → iter-5; Dashboard Top Sectors read `/api/sectors`). **Do NOT edit the blueprint again** — the note
  is present (the `M` in git status). The dev only needs to make the code match it.
- **`industries` table population, the industry→sector taxonomy, and internal sector breadth are OUT OF
  SCOPE** (spec) — even though iter-1's handoff floated populating `industries`. J-04 is satisfied by
  ranking the sector + industry **ETFs**. Follow the spec: defer.
- **No snapshot/score tables, no `scanner_runs`, no persistence, no run timestamp** — iter-2 computes
  **on-request** only (iter-5 persists). Do NOT create those tables or pre-empt the immutability machinery.
- **No per-stock / theme scoring, no candidate counts, no Top Themes, no setups** — iter-3+. Dashboard
  shows these as explicit pending placeholders only.
- **No live/network fetch** — read the committed seed via the DB only.
- **No anti-goal surface** — no order/execution path, no secrets, research-only.
