# goal-i_can_see_the_wealthy_future-iter-4 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete
**Depth:** full · **Target journey:** J-05 · **Frontend Present:** yes

## What Was Built

Completed the Stock Detail page (`/stocks/[ticker]`) into the full per-stock research view J-05
describes: a price + moving-average candle chart with a volume series, theme-membership chips, and a
concrete, **server-computed** invalidation level — alongside the three explainable scores that
already render. Everything new is computed once in the backend; the frontend re-formats/plots only.

**Backend:**
- `app/engine/indicators.py` — new `sma_series(values, period)`: the rolling MA aligned 1:1 with the
  input (`None` for the warm-up prefix, then the SMA). It is built by **reusing the existing `sma`**
  over each prefix, so there is ONE MA definition and the invariant
  `sma_series(values, p)[-1] == sma(values, p)` holds by construction (single source — the chart
  overlay, the invalidation level, and the scoring `extension`/`support_nearby` components can never
  disagree). Period stays an argument (no literal).
- `app/api/stocks.py` — new canonical endpoint **`GET /api/stocks/{ticker}/bars`**. Returns
  `asof_date`, `ticker`, ascending OHLCV `bars` read **only** through `bars_asof` (date ≤ as-of —
  no lookahead), and `ma`: a map keyed by every period in `config.indicators.ma_periods`
  (`"20"`,`"50"`,`"150"`,`"200"`) → the `sma_series` aligned 1:1 with `bars` (a number, or `null`/NA
  for the warm-up gap). `503` when no price data exists, `404` for an unknown ticker — never a
  fabricated row (mirrors the existing `/api/stocks/{ticker}` contract). Case-insensitive ticker,
  resolved to the canonical config spelling.
- `app/engine/scoring.py` — each per-stock row now carries two new fields, computed **once** in
  `score_stocks`:
  - `invalidation` = `{basis, ma_period, level, price, note}`. `level` is the canonical
    `sma(closes_asof, config invalidation ma_period)` — the SAME value that ends the `/bars` 50-DMA
    series. The human **`note` is built server-side** ("Invalid below the 50-DMA at $X") and rendered
    verbatim by the UI. Short history → `level: null` + an honest note ("Invalidation level NA —
    insufficient history"), never a fabricated number.
  - `themes` = `[{slug, name}, …]` — every config theme whose member list contains the ticker, in
    config order (the reverse of the SAME `config.themes` map `score_themes` ranks; `[]` if none).
  Because both ride on the shared `score_stocks` row, `/api/stocks` (list) and `/api/stocks/{ticker}`
  (detail) carry them identically — J-06 stays byte-identical.
- `app/engine/themes.py` — extracted `theme_name(slug)` (the existing
  `slug.replace("_"," ").title()` derivation), now the single naming source shared by `score_themes`
  and `score_stocks` (no second theme→name mapping). Behaviour unchanged for `score_themes`.
- `app/config.py` — new `InvalidationCfg { ma_period }` on `DecisionRulesCfg`, plus a `Config`-level
  validator asserting `decision_rules.invalidation.ma_period ∈ indicators.ma_periods` (so the
  invalidation MA is always an already-charted canonical MA — never a second basis).
- `config.yaml` — added `decision_rules.invalidation: { ma_period: 50 }`.

**Frontend:**
- Installed **`lightweight-charts@5.2.0`** (TradingView; **Apache-2.0**, client-side only, no
  account/key, no runtime network callout). Cleared the supply-chain gate (see Config changes). The
  only transitive dep added is `fancy-canvas`; `npm audit` shows the two new packages introduce
  **zero** advisories.
- `components/price-chart.tsx` *(new, `"use client"`)* — Lightweight-Charts wrapper. The library is
  **dynamically imported inside an effect** (it touches `document`; this keeps SSR safe) and disposed
  on unmount (`autoSize` tracks the container). Plots candles from `bars`, one line series per
  `ma[period]` (skipping the NA warm-up so it draws as a gap), and a muted volume histogram on its
  own scale. **Never computes a moving average from the close array** — it plots the server `ma`
  series. All colours are read at runtime from the SAME CSS palette tokens the rest of the UI uses
  (`--pos`/`--neg`/`--accent`/`--warn`/`--text-muted`/`--text-faint`) — no arbitrary hex. A compact
  legend mirrors the overlay colours.
- `app/stocks/[ticker]/page.tsx` — replaced the iter-3 "arrives next iteration" placeholder with: a
  theme-chips + invalidation card (chips link to the existing `/themes`; the invalidation `note` is
  rendered **verbatim**, in amber when `level` is null), and a full-width price-chart card with its
  own loading / empty / error states. The three score cards are unchanged.
- `lib/api.ts` — added `ThemeChip`, `Invalidation`, `PriceBar`, `BarsResponse` types and
  `fetchStockBars(ticker, signal)`; extended `StockRow` with `themes` and `invalidation`. Kept the
  "RE-FORMATS server values only — NO business computation here" discipline.

## Files Changed

**Backend**
- `apps/backend/app/engine/indicators.py` — add `sma_series` (reuses `sma`; NA-prefix aligned)
- `apps/backend/app/api/stocks.py` — add `GET /api/stocks/{ticker}/bars` (OHLCV + per-period `ma`)
- `apps/backend/app/engine/scoring.py` — attach `invalidation` + `themes` to each canonical row
- `apps/backend/app/engine/themes.py` — extract shared `theme_name(slug)`
- `apps/backend/app/config.py` — `InvalidationCfg` + cross-field validator (period ∈ ma_periods)
- `config.yaml` — add `decision_rules.invalidation: { ma_period: 50 }`

**Backend tests**
- `apps/backend/tests/test_bars.py` *(new)* — `/bars` ascending/no-lookahead, `ma` keyed by every
  config period & length-aligned, 404 unknown, 503 no-data, and the single-source tie
  (`ma[str(p)][-1] == sma(closes,p)`; `ma[str(inv)][-1] ==` detail `invalidation.level`)
- `apps/backend/tests/test_indicators.py` — `sma_series` warm-up NA, rolling values, `[-1]==sma`
- `apps/backend/tests/test_scoring.py` — row `invalidation` == canonical sma + server note;
  short-history NA honest; `themes` == reverse of `config.themes`; fields on the shared row
- `apps/backend/tests/test_config_engine.py` — invalidation block validated; period-outside-periods
  rejected; missing block rejected; real config exposes `ma_period == 50`
- `apps/backend/tests/test_config.py`, `tests/test_sectors.py`, `tests/test_themes.py` — added the
  now-required `invalidation` key to the minimal/synthetic config fixtures

**Frontend**
- `apps/frontend/components/price-chart.tsx` *(new)* — client-only Lightweight-Charts wrapper
- `apps/frontend/app/stocks/[ticker]/page.tsx` — chart panel + theme chips + invalidation note
- `apps/frontend/lib/api.ts` — new types + `fetchStockBars`; `StockRow` extended
- `apps/frontend/package.json`, `apps/frontend/package-lock.json` — pin `lightweight-charts@5.2.0`

**Config (dev-chain subtree copy, via the `config/` symlink)**
- `incredible_auto_dev/config/install-security-policy.json` — add `lightweight-charts` to
  `npm.allowlist` (the documented permit path for the supply-chain gate)

## Tests Run

- Backend: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
  Result: **126 passed, 0 failed** (483s). The slowness is inherent to running the full scoring
  engine on the frozen seed across many tests, not the new code.
- Frontend: `cd apps/frontend && npm run build` → **compiled + typechecked successfully** (all 10
  routes; `/stocks/[ticker]` now 5.33 kB, with the charting lib dynamically code-split). Also booted
  `next dev` and force-compiled `/stocks/[ticker]` (672 modules) → HTTP 200, no errors.
- **Live integration smoke** (real uvicorn, not just TestClient): `GET /api/stocks/NVDA/bars` → 200,
  1356 bars, `ma` keyed `20/50/150/200`, warm-up NA prefix exactly `period-1` long, `max(bar.date)
  == asof` (no lookahead). `ma["50"][-1] == 198.734` **equals** the detail row's
  `invalidation.level` (198.73400026) — single source confirmed end-to-end. Note served verbatim:
  "Invalid below the 50-DMA at $198.73". Unknown ticker → `404 {"detail":"unknown ticker: …"}`.
  `themes` = `[ai_data_centre, semiconductors, megacap_leaders]`. Server stopped after the smoke.

## Process requirements for downstream (please do not skip)

- **Emit the audit handoff** — this is a **full-depth** iteration, and the auditor report
  (`reports/audits/<phase>-audit.md`) was NOT produced at full depth in iter-2 or iter-3. The
  iteration spec's DEFINITION OF DONE explicitly requires it this time. (Developer cannot author the
  auditor's own report; surfacing the requirement here so the pipeline runs the audit step.)
- **Browser-QA must own/self-heal its frontend and verify the canvas is actually populated.** J-05 is
  **canvas-rendered** (Lightweight-Charts draws to `<canvas>`), so a "page loaded" check is NOT
  enough. During this dev smoke I hit the exact lesson-#1 failure mode: a **stale uvicorn from a
  prior iteration was still bound to port 8835** and served old code (no `/bars` → 404), while a
  freshly-started server could not bind. I could not kill that pre-existing process (multi-project
  safety guard), so I verified against my own server on a separate port. **Browser-QA / the
  orchestrator must ensure a FRESH backend+frontend on the expected ports** (kill/replace stale
  instances by port) or the canvas evidence will be stale/blank and the SKIP-vs-PASS flap recurs.
  The evaluator should reconcile J-05 from the on-disk evidence PNGs (confirming candles + MA
  overlays + volume are visible), not a lone SKIP/PASS verdict.

## Known Issues

- **Pre-existing npm advisories (NOT introduced this iteration):** `npm audit` reports 1 critical /
  high cluster in `next@15.1.3` and 1 moderate in its transitive `postcss`. These predate iter-4;
  `lightweight-charts`/`fancy-canvas` add none. Upgrading Next.js is out of scope for J-05 (the spec
  forbids touching unrelated/existing surfaces) — flagged here for a future maintenance iteration.
- **Stack-doc license note:** the stack doc calls Lightweight-Charts "MIT"; the actual license is
  **Apache-2.0** (still permissive, no-key, client-side). No anti-goal impact; documented for accuracy.
- **Theme chips link to `/themes` (the home), not a per-theme anchor** — the Themes page has no
  per-slug anchor and the spec scopes this to "no new route". Acceptable per the spec ("label or
  link to the existing `/themes` home").
- `score_stocks` re-reads each ticker's bars once in pass 3 for the invalidation level (via the
  canonical `bars_asof`). This matches the codebase's existing access pattern (e.g. `themes.py`
  reads each member's bars multiple times) and keeps the single-source story explicit; it is not a
  correctness issue.

## Suggested Next Phase

iter-5 (J-07, J-08): Scanner snapshots + Scanner Runs pages with immutability — persist a
`scanner_run` and its result rows (append-only), seed a Risk-Off historical run plus ≥1 earlier run,
and add the Scanner Runs list/detail pages. `models.py` was intentionally left unchanged this
iteration; snapshot persistence is the next step and unlocks the per-snapshot score history that is
deliberately out of scope for J-05.
