# App Blueprint — i_can_see_the_wealthy_future (Trendora)

<!--
Coherence contract for the whole app. Drafted by the goal-decomposer at baseline; you approve it once
(edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

REVIEW CHECKLIST (before you resume):
  1. Information Architecture — are the nav sections sensible, and does every journey have an obvious
     home reachable in <=2 clicks? Stock Detail and Run Detail are intentionally reached from a row,
     not the top nav.
  2. Data Contract — is every "same-number-everywhere" value listed with exactly ONE computing module
     and ONE serving path? The six canonical scores + A-E bucket + setup status are the critical ones
     (J-06). Add any I missed; fix any wrong source. Module paths (app.engine.*) are proposals for
     iter-1+ to create — rename here if you prefer a different layout.
-->

## Information Architecture

**Layout shell:** Left persistent sidebar (nav) + main content area — a dense, dark analytical
workstation. Numbers are monospace/tabular; every score shows its **A–E bucket first, raw 0–100
secondary**. Single mobile breakpoint ~640px (wide tables scroll horizontally). The backend is the
single source of truth; every page only re-formats server-computed values and never recomputes a
score, bucket, or return.

**Navigation skeleton** (the persistent sidebar — every feature lives under one of these):

```
Trendora
├── Dashboard        /                       (J-01)
├── Stocks           /stocks                 (J-02, J-06)
│   └── Stock Detail /stocks/[ticker]        (J-05, J-06)   — opened from a leaderboard row, not the nav
├── Themes           /themes                 (J-03)
├── Sectors          /sectors                (J-04)
├── Scanner Runs     /scanner-runs           (J-08)
│   └── Run Detail   /scanner-runs/[runId]   (J-07, J-08)   — opened from a run row
├── System Health    /system-health          (J-09, J-10)
└── Watchlist        /watchlist              (J-11)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the sidebar):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Daily dashboard at a glance | `/` | Dashboard |
| J-02 Stock Leaderboard + working filters | `/stocks` | Stocks |
| J-05 Stock Detail with explainable scores | `/stocks/[ticker]` | Stocks (row → detail) |
| J-06 Score consistency across pages | `/stocks` ↔ `/stocks/[ticker]` | Stocks |
| J-03 Theme Leaderboard | `/themes` | Themes |
| J-04 Sector / industry Leaderboard | `/sectors` | Sectors |
| J-08 Immutable scanner-run history | `/scanner-runs` | Scanner Runs |
| J-07 Risk-Off regime suppresses Actionable | `/scanner-runs/[runId]` | Scanner Runs (row → detail) |
| J-09 System Health forward-tested evidence | `/system-health` | System Health |
| J-10 Control-group honesty (selection vs sector beta) | `/system-health` | System Health |
| J-11 Watchlist with persistence | `/watchlist` | Watchlist |

## Data Contract

Every value below is computed **once** by the scoring / regime / forward-testing engine during a scan
(or the forward-returns job), **stored** on an append-only snapshot table, and only re-formatted by the
API/UI. No page recomputes or re-fetches a value from a second code path; the frontend never recomputes
a score, bucket, or return. Module paths under `apps/backend/app/`.

| Value / entity | Computed by (single module/function) | Served by (canonical endpoint) | Notes |
|---|---|---|---|
| Market Regime score + label | `app.engine.regime:score_regime` | `GET /api/runs/{run_id}` (iter-5); `GET /api/dashboard` (current) | 0–100 + one of 6 labels; stored on `scanner_runs` (iter-5). Dashboard shows the latest run's value via `GET /api/dashboard` (no recompute). **Also computed once here and served from `/api/dashboard` (re-attributed iter-3, resolving the iter-2 coherence WARN):** market breadth % (above 50-/200-DMA) and net new-high/low — both **universe-relative**. iter-5 `summarize_run` must READ these, never recompute. |
| Candidate counts (# Actionable / Breakout-watch / Pullback-watch) + last-scan ts | `app.engine.setups:summarize_candidates` | `GET /api/dashboard` | counts derived once by counting the canonical per-stock **setup statuses** (`classify_setup`). iter-3 computes on-request from `score_stocks`. **iter-5 `summarize_run` must READ stored setup statuses (via this helper), not recompute** (re-attributed iter-3 from the not-yet-existing `app.engine.scanner:summarize_run`, per the iter-2 coherence WARN). last-scan ts = run timestamp in iter-5 (currently the latest seed date). |
| Sector / industry score | `app.engine.sectors:score_sector` | `GET /api/sectors` | per sector/industry ETF, per run; stored on `sector_scores`. Row also carries RS-vs-SPY, dist-from-52w-high, trend label (J-04). SPY shown as 0% RS reference, not ranked vs itself. |
| Theme score | `app.engine.themes:score_themes` | `GET /api/themes` | per theme; stored on `theme_scores` (iter-5). Row also carries members, 1m/3m basket return, breadth %, trend label (J-03). Price-confirmed, not news-driven. Dashboard **Top Themes** slices this same endpoint — no second source. |
| Leadership / Entry Quality / Risk score (per stock) | `app.engine.scoring:score_stocks` | `GET /api/stocks` (list) **and** `GET /api/stocks/{ticker}` (detail) | each 0–100 with named component breakdown; stored on `scanner_results` (iter-5). Leaderboard and detail read the **same computation** → J-06. Never collapsed into one "buy" number. |
| A–E bucket | `app.engine.buckets:to_bucket` (config edges) | (rides on each score it labels) | derived once from a stored score by the single bucketing fn; never re-derived in the API or UI. |
| Setup status (per stock) | `app.engine.setups:classify_setup` | (rides on the stock rows above) | one of: Actionable / Pullback-watch / Breakout-watch / Extended / Avoid / Risk-off-watchlist. **Risk-Off regime ⇒ zero "Actionable"** (J-07). |
| Score component breakdown + reason + invalidation | breakdown+reason emitted by `app.engine.scoring:score_stocks`; **invalidation level** computed once there from the **config-named invalidation MA** (`decision_rules.invalidation.ma_period`, default 50-DMA — must be one of `indicators.ma_periods`) via the canonical `app.engine.indicators:sma` | (same stock endpoints: `/api/stocks` + `/api/stocks/{ticker}`) | stored as `components_json`; the source of the reason summary. Every displayed score carries it — no bare numbers. **Invalidation (iter-4):** the engine emits the structured level (basis MA, `$level`, latest close) AND the human note string ("Invalid below the 50-DMA at $X"); the frontend renders it verbatim — never assembles the level client-side. NA (honest "insufficient history") when the MA is not computable — no fabrication. |
| Theme membership (per stock) | derived by `app.engine.scoring:score_stocks` from the canonical `config.themes` map (the SAME map `app.engine.themes:score_themes` ranks) | (rides on the per-stock rows: `/api/stocks` + `/api/stocks/{ticker}`) | list of `{slug, name}` the stock belongs to; chips on Stock Detail link to the existing `/themes` home. One source = the config theme definitions; no second mapping. |
| Price / MA / volume series (per ticker, as-of) | bars from `app.engine.prices:bars_asof` (date ≤ as-of — no lookahead); rolling MA overlays from the canonical `app.engine.indicators:sma`/`sma_series` over `config.indicators.ma_periods` | `GET /api/stocks/{ticker}/bars` (iter-4) | OHLCV bars + per-period MA series for the Stock Detail chart. **MAs computed server-side; the frontend plots the server MA series and NEVER recomputes a MA from the close array.** The latest charted 50-DMA equals the scoring 50-DMA and the invalidation level (one value, three displays). NA where history is too short — drawn as a gap, never fabricated. |
| Forward-return aggregates (by bucket A–E / by setup / by regime; excess vs SPY/QQQ/sector; control-group cohorts) | `app.engine.forward_testing:compute_forward_aggregates` | `GET /api/system-health` | from stored snapshots + **post-snapshot** prices only (no-lookahead); each cell carries sample size `n`; evidence labelled as carrying survivorship bias. Stored in the append-only `forward_returns` table — snapshots never mutated. |
| Watchlist entry (date-added, reason, current score/setup, price-since-added, invalidation) | reuses stored `scanner_results` (current score/setup) + `app.engine.indicators` (price-since-added) | `GET /api/watchlist` (`POST` add, `DELETE` remove) | persisted in DB (survives restart, J-11); current score/setup READ the canonical stored values — no second computation. |
| **Scanner run snapshot** (immutable as-of run: list + detail) — J-07, J-08 | `app.engine.scanner:run_scan` — **calls** the canonical engine modules once per as-of date (`score_regime`/`score_sectors`/`score_themes`/`score_stocks`/`setups:summarize_candidates`); recomputes NOTHING | `GET /api/runs` (list) **and** `GET /api/runs/{run_id}` (detail) | **iter-5.** Stored on the **append-only** `scanner_runs` + `scanner_results` (+ `sector_scores` + `theme_scores`) tables — never updated after creation (*Snapshots-immutable* critical). Each stored value is the byte-identical output of its ONE canonical module (proven by a faithful-equality unit test); `/api/runs/{id}` serves a stored COPY for a historical date — not a second computation. Bootstrap dates from `config.scanner.bootstrap_dates` (≥1 exactly `"Risk-off"`) + the latest seed date. `forward_returns` stays a SEPARATE append-only table keyed to the snapshot (iter-6). |

Health probe: `GET /api/health` → `{"status":"ok", ...}` (no canonical value).

### Iteration serving notes (additive; no nav/source change)

- **Module home:** the `app.engine.*` computing modules above live under **`apps/backend/app/engine/`** (reconciles the design doc's flat `app/<module>/` with this contract's `app.engine.*` — resolved in iter-2 when the first engine modules were created).
- **iter-2 (Regime + Sectors) serving model:** the Market Regime score+label and the Sector/industry scores are computed **on-request, deterministically** from the frozen seed via an as-of accessor (`bars_asof`, date ≤ d) and served by their canonical endpoints (`/api/dashboard`, `/api/sectors`). **Persistence** of these values into the append-only snapshot tables (`scanner_runs`, `sector_scores`) and the "scan ran at" run timestamp arrive with the scanner in **iter-5**; until then the displayed "Data as-of <date>" is the latest seed date. Single-source-of-truth still holds: one computing module + one serving endpoint per value, deterministic output.
- **Dashboard ↔ Sectors:** the Dashboard's "Top Sectors" list **reads the canonical `GET /api/sectors`** (frontend slices the top N) — it does NOT recompute or re-serve the sector score from a second path.
- **iter-3 (per-stock scores + theme scores + setups) serving model:** the three per-stock scores (`app.engine.scoring:score_stocks`), the theme scores (`app.engine.themes:score_themes`), and the setup status (`app.engine.setups:classify_setup`) are computed **on-request, deterministically** from the frozen seed via `bars_asof` (date ≤ d) — the same model as iter-2. Persistence into the append-only snapshot tables (`scanner_results`, `theme_scores`) arrives in **iter-5**; `models.py` is unchanged in iter-3. Single-source holds: `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) read the **same** `score_stocks` output (→ J-06); the Dashboard's **candidate counts** count the canonical setup statuses (`setups:summarize_candidates`) and its **Top Themes** slice the canonical `/api/themes` — neither recomputes a value. Breadth/new-high-low are NOT recomputed here — they are read from the regime engine.
- **Shared label helper (iter-3 consolidation):** the score→label-via-edges helper is promoted out of `regime.py` into a public `app.engine.labels:label_for(score, edges)`; `regime.py`, `sectors.py`, and `themes.py` all import it (resolves the review NOTE that `sectors.py` imported the private `regime._label_for`). No canonical value or serving path changes.
- **iter-4 (Stock Detail: chart + theme chips + invalidation) serving model:** the price/MA/volume **chart series** is a NEW displayed value with its own canonical endpoint `GET /api/stocks/{ticker}/bars` — bars via `bars_asof` (date ≤ as-of, no-lookahead), MA overlays via the canonical `indicators:sma`/`sma_series` over `config.indicators.ma_periods` (the frontend plots the **server** MA series, never recomputing a MA client-side). The **invalidation level** and **theme membership** are NEW fields carried on the SAME `score_stocks` per-stock row, so `/api/stocks` and `/api/stocks/{ticker}` stay byte-identical (→ J-06 preserved); the invalidation MA basis comes from a new `config.decision_rules.invalidation` block (no magic number). `models.py` is unchanged (no persistence this iter; snapshots arrive iter-5). No nav-skeleton change — Stock Detail remains row-reached under Stocks and theme chips link to the existing `/themes` home, so no `blueprint.reapproval-requested` is written.
- **iter-5 (Scanner snapshots: immutable run history) serving model:** `models.py` gains the **append-only** snapshot tables (`scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`); `app.engine.scanner:run_scan` **calls** the existing canonical engine functions once per as-of date and **persists** a complete immutable snapshot (it recomputes nothing — honoring the iter-2 lesson: read the canonical source, never recompute). `bootstrap_runs` (run from the lifespan, idempotent, frozen-seed-only) ensures runs for `config.scanner.bootstrap_dates` (≥1 verified `"Risk-off"`, e.g. 2025-04-04 / 2022-10-07) + the latest seed date. Historical runs are served by the NEW `GET /api/runs` + `GET /api/runs/{run_id}`; the run-detail page reads STORED as-of rows (never the live `score_stocks`) so an old run shows its frozen numbers (→ J-08), and a `"Risk-off"` run stores zero `Actionable` (→ J-07). **The existing live-view endpoints (`/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, `/api/stocks/{ticker}/bars`) are NOT re-pointed this iter** — they keep computing the latest as-of view on-request from the same canonical modules, so J-01–J-06 are untouched. Single-source holds: each value still has ONE computing module; `/api/runs/{id}` serves a stored COPY of that module's output, and a faithful-equality unit test proves the latest persisted snapshot == the live computation (one value, two read paths — never two computations). The Dashboard's "Data as-of" date equals the latest run's `asof_date` because the seed is frozen. No nav-skeleton change (Scanner Runs + Run Detail already in the IA; Run Detail row-reached) — no `blueprint.reapproval-requested`.
- **iter-6 (Walk-forward forward-testing + System Health) serving model:** `models.py` gains ONE new **append-only** table `forward_returns` keyed `(run_id, symbol, horizon)` — the realized forward return of a symbol over `horizon` trading days measured **only from bars with date > the run's `asof_date`** (the strict forward inverse of `bars_asof`, via a new `app.engine.prices:bars_after`; NA when fewer than `horizon` post-snapshot bars exist — never fabricated, excluded from `n`). `symbol` spans the universe stocks AND the benchmarks (SPY, QQQ, the 11 sector ETFs) so excess-vs-benchmark is a stored-value subtraction. A walk-forward backfill (`app.engine.forward_testing:backfill_forward_returns`, run idempotently from the lifespan like `bootstrap_runs`) persists a scanner_run snapshot for each as-of date generated from `config.walk_forward.{history_years, asof_cadence}` ∩ seed trading days **by calling the existing idempotent `run_scan`** (it recomputes NO score — single source; the stored snapshot is the canonical bucket/setup/sector source) and then INSERTs the per-`(run, symbol, horizon)` realized returns. **Snapshots are never mutated** — forward returns live ONLY in the separate `forward_returns` table (Snapshots-immutable critical). The displayed evidence is the **forward-return aggregates** already in the Data Contract (row: `app.engine.forward_testing:compute_forward_aggregates` → `GET /api/system-health`): by-bucket (A–E) / by-setup / by-regime mean returns, excess vs SPY/QQQ/sector, and the control-group cohorts (top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF) — each computed **once** by `compute_forward_aggregates`, which READS the stored snapshot rows (`scanner_results`: bucket/setup/sector — never recomputed) joined with stored `forward_returns`, and carries sample size `n` + the **survivorship-bias** label (Honest-limitations anti-goal). The random-same-sector cohort is drawn with a **config-seeded** RNG (`config.walk_forward.control_group.{seed, top_n, peers_per_sector}` — additive keys, no magic number) so it is reproducible. The frontend `/system-health` page (graduating from the iter-1 EmptyState stub) re-formats this single payload only — it recomputes no return/excess/bucket. The live endpoints (`/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, `/bars`) and the iter-5 run endpoints (`/api/runs`, `/api/runs/{run_id}`) are NOT re-pointed — J-01–J-08 cannot regress. System Health is already the blueprint IA home for J-09/J-10 (`/system-health` in the sidebar) → no nav-skeleton change, no `blueprint.reapproval-requested`.
