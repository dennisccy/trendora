# goal-i_can_see_the_wealthy_future-iter-3 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete

## What Was Built

Per-entity canonical scores: the three independent per-stock scores, theme scores, and setup
classification — each computed **exactly once** in the engine and read identically everywhere.

**Backend engine (new modules):**
- `app/engine/scoring.py` — `score_stocks(session, asof, config)` → `{asof_date, benchmark, rows[]}`.
  For every universe stock it produces the **complete canonical record in one pass**: three
  independent scores (**Leadership / Entry Quality / Risk**), each a config-weighted blend of named,
  cross-sectionally-normalized components (≥3 *available* per score), each with an A–E bucket via the
  single `to_bucket`; **plus** the setup status + reason. Reads the canonical regime once
  (`score_regime`) and the canonical sector ranking once (`score_sectors`) for the two contextual
  Risk components (`regime`, `sector_strength`) — never recomputes them. Risk = *danger* (higher =
  more dangerous), stated in the docstring. `gap_climax` (needs earnings data) reports NA /
  `available:false` and is excluded — never fabricated. All bars via `bars_asof` (no lookahead).
- `app/engine/themes.py` — `score_themes(...)` → price-confirmed Theme Score (0–100 + bucket + named
  components) per theme, plus member tickers, equal-weight 1m & 3m basket return, member breadth %
  (universe-relative), trend label. Also exposes the shared `basket_return` / `total_return` helpers
  (reused by scoring's `rs_theme`).
- `app/engine/setups.py` — `classify_setup(scores, regime_label, config)` → one of the six configured
  statuses via `config.decision_rules`. **CRITICAL gate: a Risk-off regime ⇒ "Risk-off-watchlist"
  for every name (zero Actionable), regardless of scores** — unit-tested exhaustively.
  `summarize_candidates(rows)` is the single place candidate counts are derived (counts the canonical
  setup statuses).
- `app/engine/labels.py` — `label_for(score, edges)` promoted out of `regime.py`; `regime.py`,
  `sectors.py`, `themes.py` all import it (removes `sectors.py`'s import of the private
  `regime._label_for`). No output change to `/api/sectors` (J-04 preserved).
- `app/engine/normalize.py` — `cross_sectional_percentiles(...)`, the shared peer-ranking helper for
  `scoring.py` + `themes.py` (sectors.py keeps its own copy to avoid touching J-04 math).

**Backend API (new/changed endpoints, all serve engine output verbatim; 503 on no data):**
- `GET /api/stocks` — the ranked leaderboard (`score_stocks`).
- `GET /api/stocks/{ticker}` — the **same row** filtered from the *same* `score_stocks` result
  (case-insensitive); `404` for an unknown ticker → byte-identical to the list row (**J-06**).
- `GET /api/themes` — `score_themes`.
- `GET /api/dashboard` — now also returns real `candidate_counts` (from
  `setups.summarize_candidates(score_stocks.rows)`). The `top_themes` placeholder was **removed**:
  Top Themes is served by the canonical `/api/themes` and sliced in the frontend (exactly like Top
  Sectors reads `/api/sectors`) so the Theme Score keeps **one** serving path (blueprint Data Contract).
- Registered the `stocks` and `themes` routers in `main.py`.

**Config + data linkage:**
- `config.yaml`: added `theme_scores` (weights + trend_edges) and `stock_sectors` (every universe
  symbol → GICS sector name). The previously-scaffolded `scores` / `decision_rules` blocks are now
  consumed.
- `app/config.py`: typed validation for `scores` (each of leadership/entry_quality/risk covers its
  component set + sums ~1.0), `theme_scores`, `decision_rules` (required cutoff keys present), and
  `stock_sectors` (covers every universe symbol; values ∈ the 11 sector names).
- `app/seed_loader.py`: `load_reference_data` sets `Stock.sector_id` from `stock_sectors` on create
  **and backfills** existing rows lacking it; `load_seed` now ensures reference data on every boot
  (idempotent) so a pre-existing DB gets the `sector_id` backfill. `models.py` UNCHANGED.

**Frontend:** see the frontend handoff. Four surfaces: `/stocks` (leaderboard + 2 filters),
`/stocks/[ticker]` (3-score detail), `/themes` (leaderboard), `/` (real candidate counts + Top Themes).

## Files Changed

**Created (backend):**
- `apps/backend/app/engine/scoring.py` — the three per-stock scores + setup composition (single producer)
- `apps/backend/app/engine/themes.py` — theme scoring + basket math
- `apps/backend/app/engine/setups.py` — setup classification + Risk-off gate + candidate counting
- `apps/backend/app/engine/labels.py` — shared score→label helper (extracted from regime.py)
- `apps/backend/app/engine/normalize.py` — shared cross-sectional percentile helper
- `apps/backend/app/api/stocks.py` — `GET /api/stocks` + `GET /api/stocks/{ticker}`
- `apps/backend/app/api/themes.py` — `GET /api/themes`
- `apps/backend/tests/test_scoring.py`, `test_themes.py`, `test_setups.py` — new engine unit tests

**Modified (backend):**
- `apps/backend/app/config.py` — `ScoresCfg` / `ThemeScoresCfg` / `DecisionRulesCfg` + `stock_sectors` validation
- `apps/backend/app/engine/regime.py` — import `labels.label_for` (dropped private `_label_for`)
- `apps/backend/app/engine/sectors.py` — import `labels.label_for` (no output change)
- `apps/backend/app/api/dashboard.py` — real `candidate_counts`; `top_themes` removed (served by `/api/themes`)
- `apps/backend/main.py` — register `stocks` + `themes` routers
- `apps/backend/app/seed_loader.py` — `Stock.sector_id` set+backfill; `session.scalar` fix; reference data ensured every boot
- `config.yaml` — `theme_scores` + `stock_sectors` added; comment updates
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_sectors.py` — fixtures updated for now-required config blocks (+ new validation tests)
- `apps/backend/tests/test_api_engine.py` — J-06 list==detail guard, real candidate-counts assertion, /api/stocks + /api/themes equality, 404/503 cases
- `apps/backend/tests/test_no_magic_numbers.py` — `CALC_FILES` += scoring/themes/setups/labels/normalize; `FORBIDDEN_INT_LITERALS` += 85
- `apps/backend/tests/test_regime.py` — import `label_for` from `app.engine.labels`

**Created/Modified (frontend):** see the frontend handoff.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **109 passed** (0 failed). Up from 72 at iter-2 baseline (+37 new/extended tests).

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully** — all 10 routes typecheck + build clean.

**Live integration smoke test** (booted `scripts/start-backend.sh`, hit all endpoints, killed server):
- `/api/stocks` → 122 ranked rows; top leader MU (Leadership A 94.5 / Entry E 22.4 / Risk E 54.3 →
  setup "Extended"); leadership 7/7, entry 5/5, risk 7/8 components available (gap_climax NA).
- **J-06 verified live**: NVDA's three scores + buckets identical on `/api/stocks` and `/api/stocks/NVDA`.
- `sector_id` backfill confirmed working on the pre-existing live DB (rs_sector + sector_strength available).
- `/api/themes` → 11 themes, non-increasing; top "Semiconductors" 100.0 (+28.4% 1m / +61.2% 3m,
  breadth 100%, "Strong uptrend").
- `/api/dashboard` → regime Risk-on 74.32; candidate_counts `{Actionable:0, Breakout-watch:8,
  Pullback-watch:1, Extended:11, Avoid:102, Risk-off-watchlist:0}`; no `top_themes` key.
- `/api/stocks/NOTREAL` → 404.

## Known Issues

- **Zero "Actionable" on the latest seed date (2026-05-28) — this is correct, not a bug.** The market
  is Risk-on but extended; strong leaders are near highs (high Leadership, low Entry Quality), so none
  meet the strict Actionable gate (Leadership≥80 **and** Entry≥70 **and** Risk≤60). This is Trendora's
  intended "don't chase extended leaders" signal. The `/stocks` Actionable filter therefore shows an
  explicit empty-state (allowed by the J-02 acceptance criterion); Breakout-watch (8) and
  Pullback-watch (1) have rows, so browser QA should also verify a non-empty status filter. Cutoffs
  live in `config.decision_rules` and are tunable without code changes.
- **Component→indicator mapping is illustrative** (developer discretion per the spec): e.g.
  `up_down_vol` uses the existing `vol_trend` indicator as a proxy; `liquidity` uses average dollar
  volume; `reward_risk` uses room-to-52w-high / ATR. Journeys assert structure (a number renders,
  buckets ordered, same value in two places), not exact score numbers, so weights may be retuned later.
- **`decision_rules.theme_floor` is validated-present but not yet consumed** by `classify_setup` (it
  takes the three scores + regime, not the theme score). It is reserved for a later theme-gating step;
  it rides along via `extra="allow"` and is intentionally not removed.
- **`/api/dashboard` now runs full `score_stocks` (122 stocks) to count statuses** — a deliberate
  single-source choice (counts derive from the canonical rows). On the local SQLite seed this is ~1–2s
  per dashboard request; acceptable for a research tool. iter-5's scanner will persist these so the
  dashboard reads stored values.
- **Live `next dev` boot not separately exercised** beyond `npm run build` (the project's frontend
  gate). Browser QA (Chrome MCP) covers live UI; confirm the managed `next dev` on port 3835 is up and
  inspect on-disk screenshots before trusting any SKIP/PASS (per the iter-1/2 flap note).

## Suggested Next Phase

iter-4 (J-05): the full Stock Detail page — a price + moving-average candle chart and volume series,
theme-membership chips, and a concrete invalidation note ("below 50-DMA at $X") — plus regime-gating
logic surfaced on the detail page. The three-score engine and the `/api/stocks/{ticker}` endpoint
built here are the foundation; iter-4 enriches the detail view on top of the now-canonical scores.
