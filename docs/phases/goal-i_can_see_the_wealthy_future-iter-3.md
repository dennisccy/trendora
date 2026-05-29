# Goal Iteration 3 — Per-stock scores + theme scores → Stock & Theme Leaderboards + dashboard rollup

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-02, J-03, J-06, J-01
- **Required-still-passing journeys:** J-04 (Sector / industry Leaderboard)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)* (iter-3 adds NO persistence — `models.py` stays untouched; this anti-goal is preserved by deferral, see OUT OF SCOPE.)
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative".

## GOAL

A user can open the **Stock Leaderboard** (`/stocks`) and see every universe stock ranked with three
independent, A–E-bucketed, explainable scores (Leadership / Entry Quality / Risk), a setup status and a
reason — filterable by sector and by setup; open any stock's **detail page** and see the *same* three
scores; open the **Theme Leaderboard** (`/themes`) ranked by a price-confirmed Theme Score; and see the
**Dashboard** finally complete with real candidate counts and Top Themes.

## BACKGROUND

iter-2 shipped the first canonical values (Market Regime + Sector Score) and flipped **J-04**. This
iteration ships the *per-entity* scores that the rest of the product hangs on: the three independent
per-stock scores, theme scores, and the setup classification — each computed exactly once in the engine
and read identically everywhere. This is the **second and harder live test of *Single source of
truth*** (J-06): the same NVDA score must read identically on the leaderboard and on its detail page.
Per the eval's next-step recommendation and the roadmap, J-02/J-03/J-06 land together and the real
candidate counts + Top Themes finish and flip **J-01**. Depth is **full** (crosses backend+frontend,
introduces three new engine modules + new data model linkage + new unit tests beyond browser smoke).

**Lessons applied (from `lessons.md` — both entries match this iteration):**
- *iter-2 lesson (DIRECT MATCH — "any iter that ... touches breadth, new-high/low, or candidate
  counts"):* the blueprint attributed candidate counts + market breadth % to `app.engine.scanner:
  summarize_run`, a module that does not exist until iter-5. iter-3 now produces candidate counts. To
  avoid creating the exact two-sources-for-one-number the gate forbids, iter-3 **reconciles the Data
  Contract now** (done in this spec's blueprint edits): breadth/new-high-low are attributed to the
  regime engine; candidate counts to a single iter-3 setups summarizer; both served only from
  `/api/dashboard`. iter-5's `summarize_run` MUST *read* these, never recompute. New modules **read**
  the existing canonical source — they never recompute it.
- *iter-1 + iter-2 lesson (browser-qa SKIP-vs-PASS flap recurred twice):* this iteration is verified
  almost entirely through the browser (J-01/02/03/06). Before trusting any SKIP/PASS, confirm the
  managed `next dev` (port 3835) is up and stable and **inspect the on-disk evidence directory /
  screenshots** — do not trust a lone SKIP or PASS. See TESTING REQUIREMENTS.

## IN SCOPE

### Backend

**New engine modules (each value computed EXACTLY ONCE here; all tunables from `config.yaml`):**

- [ ] **`apps/backend/app/engine/scoring.py`** — `score_stocks(session, asof, config) -> {asof_date, benchmark, rows[]}`, mirroring the established `sectors.py` pattern (cross-sectional percentile normalization → config-weighted blend → 0–100, NA-graceful). For each universe stock it produces **three independent scores** — **Leadership**, **Entry Quality**, **Risk** — each:
  - a weighted sum (weights from `config.scores.{leadership,entry_quality,risk}.weights`, which already exist and each sum to 1.0) of **named components keyed to the config weight keys**;
  - rendered with its **A–E bucket via the single `app.engine.buckets.to_bucket`** (never re-derived) and the raw 0–100 secondary;
  - carrying a **component breakdown** (`name, raw, percentile, weight, contribution, available`) exactly like sectors, with **≥3 *available* (non-NA) components per score** (satisfies the explainability anti-goal and the J-05 "≥3 named components" contract).
  - Components are built from the **existing indicators** (`rs_vs`, `ma_stack`, `dist_from_high`, `atr_pct`, `vol_trend`, `sma`) plus the stock's **sector ETF** (for `rs_sector` / `sector_strength`) and **theme** (for `rs_theme`). A component that needs data not yet present (e.g. `gap_climax` needs earnings data — *explicitly deferred by the goal*: "earnings-gap stubbed until earnings data exists") reports **NA (`None`)** and is excluded from the weighted sum and shown `available:false` — **never fabricated**.
  - **Risk score direction:** Risk = *danger* (higher = more dangerous). State the direction in a docstring and keep all comparisons consistent with it (used by setup classification and the leaderboard colour grading).
  - **Each row is the stock's COMPLETE canonical record** — the three scores + buckets + components **and** its **setup status + reason** — composed in this **one** producer by reading the canonical regime once (`regime.score_regime`, *read* not recompute) and applying `setups.classify_setup` per row. `/api/stocks`, `/api/stocks/{ticker}`, and the dashboard's candidate counts all consume **this same producer's rows**, so there is exactly one composition path and no view can diverge (single source / J-06).
  - All bars read through `bars_asof` (no lookahead). Only structural numeric literals (0/1/2/100) — every tunable from config.
- [ ] **`apps/backend/app/engine/themes.py`** — `score_themes(session, asof, config) -> {asof_date, rows[]}` producing a **price-confirmed Theme Score** (0–100 + bucket + named components) per theme in `config.themes`, plus per row: **member tickers**, **1-month and 3-month basket return** (equal-weight member close-to-close return over `config.indicators.rs_windows`), **breadth %** (share of members above their 50-DMA, universe-relative), and a **trend label**. Price-derived only — **not** news-driven. Weights/edges from new config (see below).
- [ ] **`apps/backend/app/engine/setups.py`** — `classify_setup(scores, regime, config) -> {status, reason}` mapping the three scores + the **regime** to one of the six configured statuses (Actionable / Pullback-watch / Breakout-watch / Extended / Avoid / Risk-off-watchlist) using `config.decision_rules` (already present). **CRITICAL gate:** when the regime label is **Risk-off**, `classify_setup` MUST return **zero "Actionable"** (watchlist-only) regardless of scores — unit-tested. Also `summarize_candidates(stock_rows) -> {Actionable, Breakout-watch, Pullback-watch, ...}` — the **single** place candidate counts are derived (by counting the canonical per-stock setup statuses). The **reason** is a short plain-language string derived from the top contributing components + status (the full invalidation note is iter-4 — see OUT OF SCOPE).
- [ ] **`apps/backend/app/engine/labels.py`** (small consolidation — eval tidy-up (c)): promote the shared score→label-via-edges helper out of `regime.py` into a public `label_for(score, edges)`. Update `regime.py`, `sectors.py`, and the new `themes.py` to import it. `sectors.py` MUST stop importing the private `regime._label_for`. (No numeric literals in this module.)

**New API endpoints (serve the canonical engine output verbatim; 503 on no data, never fabricate):**

- [ ] **`GET /api/stocks`** (`apps/backend/app/api/stocks.py`) — serves `score_stocks(asof=latest_data_date)` (the ranked list). Mirror `sectors.py`: `503` when `latest_data_date is None`.
- [ ] **`GET /api/stocks/{ticker}`** — returns the **same row** for `{ticker}` from the *same* `score_stocks` computation (filter the canonical result; do **not** recompute per-ticker), so leaderboard and detail are byte-identical → **J-06**. `404` for an unknown ticker.
- [ ] **`GET /api/themes`** (`apps/backend/app/api/themes.py`) — serves `score_themes(asof=latest_data_date)` verbatim; `503` on no data.
- [ ] **Wire `/api/dashboard`** (`apps/backend/app/api/dashboard.py`): replace the `candidate_counts: None` and `top_themes: None` placeholders with **real** values:
  - `candidate_counts` ← `setups.summarize_candidates(score_stocks(asof).rows)` (the three counts the dashboard shows).
  - `top_themes` ← top-N rows of `score_themes(asof)` (slice the canonical theme result, exactly as Top Sectors slices `/api/sectors`). **Do not** add a second theme computation.
  - Leave breadth / new-high-low exactly as they are (already computed once in `regime.py`, served here) — **do not** recompute them.
- [ ] Register the three new routers in `apps/backend/main.py` (`app.include_router(..., prefix="/api")`).

**Data model linkage (reference data — NOT scoring literals):**

- [ ] Add a **`stock_sectors:`** mapping to `config.yaml` (ticker → GICS sector name; the name MUST be one of the `etfs.sector` values, e.g. `NVDA: Technology`). Cover **every** `universe.symbols` entry. This is reference data (like the universe list and theme defs), not a magic number.
- [ ] `apps/backend/app/seed_loader.py` (`load_reference_data`): set `Stock.sector_id` from `stock_sectors` when creating each stock, and **backfill** `sector_id` for any existing stock row that lacks it (idempotent upsert of the association — the loader currently creates stocks with `sector_id=None`). The DB (`apps/backend/data/trendora.db`) is gitignored and rebuilt deterministically from the seed, so a fresh build picks this up; the backfill covers a pre-existing DB.

**Config additions (all in `config.yaml`; add typed validation in `config.py` exactly as iter-2 did for `sectors`/`regime`):**

- [ ] **`theme_scores:`** — `weights:` (dict covering every theme-score component, sum ~1.0) + `trend_edges:` (LabelEdge list, strictly descending, covering 0..100) — analogous to the existing `sectors:` block. Themes' score tunables must not be hard-coded.
- [ ] Add typed validation + consumption for the **existing** `scores.{leadership,entry_quality,risk}.weights` (assert each component set is complete and sums ~1.0) and `decision_rules` (assert the cutoff keys are present). These blocks already exist in `config.yaml` — iter-3 *wires and validates* them.

### Frontend

- [ ] **`/stocks` — Stock Leaderboard** (`apps/frontend/app/stocks/page.tsx`): replace the empty stub with a ranked, dense dark table. Each row: **ticker** (links to `/stocks/[ticker]`), **Leadership / Entry Quality / Risk** via the existing `ScoreBadge` (A–E bucket + raw number), a **setup-status** badge, and a **reason summary**. Two working filters: a **Sector** dropdown (the GICS sectors) and a **Setup-status** dropdown (incl. **"Actionable"**). Filtering is **client-side re-display of server rows only** (no recompute / re-sort of scores). Show the existing `EmptyState` when a filter matches nothing.
- [ ] **`/stocks/[ticker]` — minimal Stock Detail** (`apps/frontend/app/stocks/[ticker]/page.tsx`): render the three scores (`ScoreBadge` + raw + the existing `ComponentBreakdown`), the setup status, and the reason — reading **`GET /api/stocks/{ticker}`**. This exists to satisfy **J-06** (scores identical to the leaderboard). The richer J-05 content (price+MA chart, volume, theme chips, concrete invalidation note) is **iter-4** — see OUT OF SCOPE.
- [ ] **`/themes` — Theme Leaderboard** (`apps/frontend/app/themes/page.tsx`): replace the empty stub with a table ranked by Theme Score (`ScoreBadge`); each row shows top **member tickers**, **1m** and **3m** basket return, **breadth %**, and **trend label**; expandable per-row `ComponentBreakdown` (like sectors).
- [ ] **`/` — Dashboard** (`apps/frontend/app/page.tsx`): replace the "pending" placeholders — render the three **candidate counts** (# Actionable / Breakout-watch / Pullback-watch) and a **Top Themes** list (≥3 themes, each with its score). Top Themes reads the canonical `/api/themes` (sliced), exactly as Top Sectors reads `/api/sectors`.
- [ ] **`apps/frontend/lib/api.ts`**: add `fetchStocks`, `fetchStock(ticker)`, `fetchThemes` and the `StockRow` / `ThemeRow` types (three scores + bucket + setup + reason + components + sector for stocks; score + bucket + members + 1m/3m return + breadth + trend for themes). Update `DashboardResponse.candidate_counts` / `top_themes` to their real shapes. **Re-format only — never compute a score/bucket/return client-side.**

### New user-facing capability

Rank, filter, and explain every stock by three independent A–E scores; drill into a stock's score
components; rank themes by a price-confirmed score; and read a complete daily dashboard (regime + real
candidate counts + Top Sectors + Top Themes + breadth + as-of date).

### New information displayed

Per-stock Leadership / Entry Quality / Risk (bucket + number + component breakdown), setup status,
reason; per-theme Theme Score, members, 1m/3m basket return, breadth, trend label; dashboard candidate
counts and Top Themes.

### New user actions

Filter the Stock Leaderboard by sector and by setup status; click a stock row to open its detail page;
expand a score's component breakdown; expand a theme row's component breakdown.

### UI surface changes

`/stocks` (was empty → leaderboard + filters), `/stocks/[ticker]` (was stub → minimal scores detail),
`/themes` (was empty → leaderboard), `/` (pending placeholders → real candidate counts + Top Themes).

### Product surface delta

The product graduates from "regime + sectors only" to the full **regime → sectors → themes → stocks**
leadership view with the three-score discipline that is Trendora's core thesis, and the dashboard
becomes a complete at-a-glance daily snapshot.

### Blueprint conformance

All four surfaces are **existing Information-Architecture homes** in `blueprint.md` (nav skeleton:
`Dashboard /`, `Stocks /stocks` → `Stock Detail /stocks/[ticker]`, `Themes /themes`). **No nav-skeleton
change** → no `blueprint.reapproval-requested` is written. Edits to `blueprint.md` are **additive only**
(Data-Contract attribution fixes + iter-3 serving notes — see Data-contract additions).

### Data-contract additions / reconciliations

Registered in `blueprint.md` this iteration (additive — values already conceptually present; this
iteration makes them real and fixes the iter-2 WARN attribution so iter-5 cannot create a duplicate):

- **Leadership / Entry Quality / Risk score (per stock)** → compute `app.engine.scoring:score_stocks`; serve `GET /api/stocks` (list) **and** `GET /api/stocks/{ticker}` (detail), both from the *same* computation (J-06). Already a contract row — add the iter-3 on-request serving note.
- **Theme score** → compute `app.engine.themes:score_themes`; serve `GET /api/themes`. Dashboard Top Themes reads `/api/themes` (sliced) — no second source.
- **Setup status (per stock)** → compute `app.engine.setups:classify_setup`; rides on the stock rows. **Risk-off regime ⇒ zero Actionable.**
- **Candidate counts (# Actionable / Breakout-watch / Pullback-watch)** → **re-attributed** from the not-yet-existing `app.engine.scanner:summarize_run` to **`app.engine.setups:summarize_candidates`** (counts the canonical per-stock setup statuses); serve `/api/dashboard`. Note: **iter-5 `summarize_run` must READ stored setup statuses (via this helper), not recompute** them.
- **Market breadth % + net new-high/low** → **re-attributed** to **`app.engine.regime:score_regime`** (where they are already computed) / serve `/api/dashboard`, labelled universe-relative. Note: iter-5 must read, not recompute.
- **A–E bucket** → unchanged (`app.engine.buckets:to_bucket`, the single deriver) — now also rides on the three stock scores + theme score.

Every new displayed value reads its single canonical endpoint; no value already in the contract gets a
second computation or a second serving path.

## OUT OF SCOPE

- **Snapshot persistence / immutability machinery** — `scanner_runs`, `*_scores`, `scanner_results`, `setup_classifications` tables, and the scanner that writes them. iter-3 computes **on-request** from the frozen seed via `bars_asof` (the iter-2 model). **`models.py` MUST NOT change** this iteration. (iter-5 — J-07/J-08.)
- **Full Stock Detail (J-05):** price+MA candle chart, volume series, theme-membership chips, and the concrete invalidation note ("below 50-DMA at $X"). iter-3's detail page is **scores + components only**, the minimum needed to verify J-06. (iter-4.)
- **The J-07 browser journey** (open a historical Risk-Off run and confirm zero Actionable). iter-3 implements and **unit-tests** the Risk-off→zero-Actionable *gate*, but the journey needs the scanner-runs history (iter-5).
- **Walk-forward / forward returns / System Health / Watchlist** (iters 6–7).
- **Live data provider / any network fetch.** Seed only.
- Adding the `^VIX`/earnings-dependent components beyond graceful NA stubs.

## DEFINITION OF DONE

- [ ] **J-02** passes via browser-qa: `/stocks` renders multiple ranked rows each with three bucketed scores (bucket + number), a setup status, and a non-empty reason; the **Sector** filter reduces rows to one sector; the **Setup-status = Actionable** filter shows only Actionable rows (or an explicit empty-state if none).
- [ ] **J-03** passes: `/themes` lists ≥3 themes ranked by Theme Score (non-increasing); the top theme shows member tickers, numeric 1m and 3m returns, a breadth %, and a trend label.
- [ ] **J-06** passes: NVDA's Leadership / Entry Quality / Risk scores **and** A–E buckets are identical on `/stocks` and `/stocks/NVDA`.
- [ ] **J-01** passes: regime label+score, **three candidate counts each rendering a number**, **≥3 Top Sectors** and **≥3 Top Themes** (each with a score), a breadth %, and a last-scan/as-of timestamp all render.
- [ ] **J-04 remains green** (Sector Leaderboard unaffected; the `labels.py` extraction must not change sector output).
- [ ] No anti-goal violation: single-source verified (NVDA identical across views; one compute fn per value; dashboard counts/top-themes read the same engine output); **Risk-off ⇒ zero Actionable** unit-tested; every score carries named components; no magic numbers (test extended); no fabricated data (NA components shown `available:false`); `models.py` unchanged; no order/execution path; no secrets.
- [ ] Unit tests pass (existing + new); `cd apps/backend && .venv/bin/python -m pytest tests/ -v` green; `cd apps/frontend && npm run build` green; no regressions.
- [ ] `blueprint.md` updated (additive Data-Contract reconciliations + iter-3 serving notes); **no** `blueprint.reapproval-requested` (no nav change).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-3-dev.md` (and a frontend handoff, per the iter-1/2 pattern).

## TESTING REQUIREMENTS

- **Browser (Chrome MCP, via browser-qa-agent):** J-02, J-03, J-06, J-01. **Before recording SKIP/PASS, confirm the managed `next dev` on port 3835 is up and stable, and inspect the on-disk evidence directory / screenshots** (the SKIP-vs-PASS flap has recurred twice — reconcile by viewing the PNGs, not by trusting a lone verdict). Capture: `/stocks` ranked + each filter applied; `/stocks/NVDA` showing the three scores; a side-by-side of NVDA's scores on list vs detail (J-06); `/themes` ranked with the top theme's members/returns/breadth/trend; `/` with candidate counts + Top Themes.
- **Unit/integration (pytest):**
  - `test_scoring.py` — each of the three scores is a config-weighted blend (changing a weight changes the score), components are named and keyed to config, ≥3 available components per score, NA components excluded + shown `available:false`, bucket via `to_bucket`, deterministic on the seed; all reads go through `bars_asof`.
  - `test_themes.py` — themes rank non-increasing by score; top theme exposes members + numeric 1m/3m basket return + breadth % + trend label.
  - `test_setups.py` — classification maps scores→status via `decision_rules`; **Risk-off regime ⇒ zero "Actionable"** (feed a Risk-off regime and assert no Actionable, the critical gate); `summarize_candidates` counts statuses correctly.
  - **J-06 coherence guard** (extend `test_api_engine.py`): the row for a ticker from `GET /api/stocks` equals the row from `GET /api/stocks/{ticker}` (identical scores + buckets) — the unit-level single-source proof.
  - `test_no_magic_numbers.py` — **extend `CALC_FILES`** to include `scoring.py`, `themes.py`, `setups.py` (and `labels.py`, which has no literals); **extend `FORBIDDEN_INT_LITERALS`** with any new config tunables not already present (note: `decision_rules.extended.leadership = 85` is **not** currently in the set — add `85`, plus any other new theme_scores/decision_rules integer cutoffs).
  - Config validation tests for the new `theme_scores` block + the now-validated `scores`/`decision_rules` (bad weights / missing cutoffs → `ConfigError`), mirroring `test_config_engine.py`.
- **Error cases:** unknown ticker on `/api/stocks/{ticker}` → 404; no price data → 503 on all three new endpoints (no fabricated rows); a stock with insufficient history → NA components, not a crash or a fabricated 0; a theme whose members all lack history → graceful NA / excluded, not a crash.

## NOTES

- **Single-source is the headline risk this iteration (J-06 + the iter-5 trap).** Implement `score_stocks` once and have *both* `/api/stocks` and `/api/stocks/{ticker}` read it; have the dashboard derive candidate counts and Top Themes from the *same* `score_stocks` / `score_themes` engine outputs (counting / slicing is re-format, not recompute). Do **not** recompute breadth/new-high-low — read the regime engine's. The blueprint reconciliation in this spec exists specifically so iter-5's `summarize_run` reads these values instead of creating a second source (the coherence-auditor's iter-2 WARN).
- **Follow the `sectors.py` pattern** for cross-sectional percentile normalization, NA handling, `components[]` shape, and the `{asof_date, rows[]}` envelope — it is the proven, coherence-passing template.
- **Risk score direction** (higher = more dangerous) and the Actionable comparison semantics must be stated explicitly in code docstrings and kept consistent between `scoring.py`, `setups.py`, and the leaderboard colour grading.
- Journeys assert **structural/relational** properties (a number renders, buckets non-increasing, filters change rows, same value in two places, zero Actionable in risk-off), **not exact score numbers** — so the illustrative config weights are fine and may be tuned later without breaking a journey.
- Process gaps flagged by the iter-2 eval for the orchestrator (not blocking, but worth fixing): the full-depth pipeline should produce the **audit handoff**, and frontend supervision (`next dev` staying up) should be hardened so browser-qa stops flapping.
