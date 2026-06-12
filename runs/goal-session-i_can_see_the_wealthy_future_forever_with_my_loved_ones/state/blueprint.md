# App Blueprint — i_can_see_the_wealthy_future_forever_with_my_loved_ones (Trendora)

<!--
Coherence contract for the whole app. Drafted by the goal-decomposer at baseline; you approve it once
(edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

WHAT THIS SESSION IS. It continues the same Trendora codebase the prior session
`i_can_see_the_wealthy_future_forever` built to GOAL_ACHIEVED at iter-28 (J-01..J-41 — commit
8c566d8). `docs/goal.md` (commit e0b5864) adds SIX new Must-haves: J-42 ISO dates everywhere,
J-43 deep-linkable `?asof`, J-44 dashboard major-indexes + regime chart, J-45 regime bands on the
stock-detail chart, J-46 faster fetch/backfill pipeline, J-47 full ≥100-term glossary + inline term
help. Baseline file-scan confirms J-01..J-41 surfaces are present; J-42..J-47 are NOT implemented
(no shared date formatter + native `type="date"` inputs on /data; no `?asof` handling in
asof-provider; no regime-history/indexes endpoint or chart; no parallel worker pool / benchmark
script; no glossary catalog in config). Rows below tagged [built] carry REAL verified names;
[TARGET] rows are the convention-named contract iter-1+ builds to — rename here if you prefer.

REVIEW CHECKLIST (~3 min): 1) every journey has a home ≤2 clicks from the nav (Stock Detail / Run
Detail are intentionally row-reached); 2) every same-number-everywhere value has exactly ONE
computing module + ONE serving endpoint; 3) the four [TARGET] rows at the bottom (J-42/J-44
normalized-index/J-44+45 regime-history/J-47 glossary) are the new registrations — check their
proposed homes.

SESSION EXTENSION (2026-06-12) — J-48..J-54 (this resume). `docs/goal.md` adds SEVEN UX/perf
Must-haves on top of the GOAL_ACHIEVED J-01..J-47 base: J-48 leaderboard column sorting (view-only),
J-49 dashboard indexes/regime card shows FULL history with an as-of MARKER (amends J-44; J-45
unchanged), J-50 `?asof` embedded in every in-app href incl. new tabs (extends J-43), J-51 every
research sample-count links to a new `/research/samples` drill-down, J-52 sample-row ticker → dated
stock detail in a new tab, J-53 fetch+backfill per-stage timings + ~2× parallel date backfill
(extends J-46), J-54 leaderboard ticker → stock detail in a new tab. The ONE new navigational
surface is `/research/samples` (link-reached under Research, like Stock/Run Detail). Items tagged
[TARGET — iter-5+] below are the new registrations — review their homes and the new samples Data
Contract row (read-only SELECT exposure of the existing `_factor_observations` /
`_combination_observations` / `_event_study_members` builders; drill-down total == published N).
-->

## Information Architecture

**Layout shell:** left persistent sidebar (nav) + top bar + main content — a dense, dark analytical
workstation. Top bar holds the **single global as-of date switcher** (the ONLY date control; J-43
serializes its state to `?asof=yyyy-MM-dd` while historical — a serialization, never a second state)
and the **readiness badge** (Ready / Initializing+progress / Unavailable). Backend is the single
source of truth; the frontend only re-formats server values.

**Navigation skeleton** (unchanged from the prior approved session — no new top-level section):

```
Trendora
├── Dashboard        /                       (J-01; J-44 Major-indexes & regime card [built iter-2]; J-49 full-history + as-of marker [TARGET — iter-6 in flight])
├── Stocks           /stocks                 (J-02, J-06, J-16/J-28 pattern filters, J-31 deep-link; J-48 sortable columns + J-54 ticker→new-tab [TARGET — iter-5 in flight])
│   └── Stock Detail /stocks/[ticker]        (J-05, J-06, J-16, J-20; J-45 regime bands [built iter-2]; J-24 timeframe — data-walled)  — row-reached
├── Themes           /themes                 (J-03)
├── Sectors          /sectors                (J-04)
├── Scanner Runs     /scanner-runs           (J-08)
│   └── Run Detail   /scanner-runs/[runId]   (J-07)  — row-reached
├── Backtest         /backtest               (J-09, J-10, J-14, J-18, J-19, J-21; J-47 tooltips)
├── Watchlist        /watchlist              (J-11)
├── Methodology      /methodology            (J-12, J-22 universe rule; J-47 full Glossary [TARGET — iter-4 in flight])
├── Research         /research               (J-25, J-26, J-27, J-29, J-30, J-31, J-32; J-47 tooltips)
│   └── Samples      /research/samples       (J-51 sample-count drill-down, J-52 row→dated detail) [TARGET — iter-7 in flight]  — link-reached
└── Data Manager     /data                   (J-17, J-33–J-39; J-42 ISO date inputs [built iter-1])
```

Cross-cutting (no page of their own): **J-13/J-43** top-bar as-of switcher (J-43 `?asof`
serialization built iter-2; **J-50 [TARGET — iter-5 in flight]** while historical the `?asof` is embedded in EVERY in-app `href` — sidebar/leaderboard/theme/sector/research links — so new-tab/middle-click/copied-link opens land on D without post-nav re-stamping, latest → clean hrefs); **J-15** snapshot-served reads; **J-40/J-41** fast boot + readiness
badge; **J-42** ISO dates on every surface (built iter-1 — `apps/frontend/lib/dates.ts`); **J-46**
backend pipeline speed (no UI surface; advisory benchmark script
`apps/backend/scripts/benchmark_pipeline.py` — built iter-3). **J-22/J-23/J-24**
are data-walled, non-halting (honest NA) on existing homes.

## Data Contract

Every value is computed **once** (scan / forward-returns / data-manager job, or a read-only
derivation over stored rows), **stored or derived from storage**, and only re-formatted by the
API/UI. Read endpoints serve the persisted immutable snapshot for the resolved as-of date — never
recomputed per request. Engine modules live under `apps/backend/app/engine/`.

| Canonical value | Computed once by | Served by | Status |
|---|---|---|---|
| Market regime score (0–100) + label (6) + breadth + net new-high/low | `regime:score_regime` | `GET /api/dashboard`, `GET /api/runs/{id}` | built; universe-relative labels |
| Candidate counts (#Actionable/Breakout/Pullback) + last-scan ts | `setups:summarize_candidates` | `GET /api/dashboard` | built |
| Sector/industry score (+RS-vs-SPY, dist-52w, trend) | `sectors:score_sector` | `GET /api/sectors` | built; SPY = 0% reference |
| Theme score (+members, 1m/3m basket, breadth, trend) | `themes:score_themes` | `GET /api/themes` | built |
| Leadership / Entry Quality / Risk + components + reason + invalidation + theme membership + volatility factor values (`hv`/`vcp_contraction`/`downside_vol`) | `scoring:score_stocks` (bars ≤ D) | `GET /api/stocks` + `GET /api/stocks/{ticker}` (same stored row → J-06) | built |
| A–E bucket | `buckets:to_bucket` (config edges) | rides each score | built |
| Setup status (Risk-Off ⇒ zero Actionable, J-07) | `setups:classify_setup` | rides stock rows | built |
| Detected patterns — VCP, `pullback_to_rising_dma`, `flat_base_breakout` (+pivot/invalidation/reason) | `patterns:detect_*` composed by `score_stocks` (≤ D) | `/api/stocks*` rows + mirror cols `scanner_results.is_*` + by-pattern breakdowns on `GET /api/backtest` | built; patterns-not-statuses |
| Price/MA/volume series (per ticker, as-of) + through-latest display extension (as-of divider, `is_forward`) | `prices:bars_asof`/`bars_through_latest` + `indicators:sma_series` | `GET /api/stocks/{ticker}/bars` | built; post-D = display-only (J-20) |
| Scanner run snapshot (immutable, append-only, create-once, concurrency-safe) | `scanner:run_scan` | `GET /api/runs`, `GET /api/runs/{run_id}` | built |
| Resolved as-of date + available dates (ONE global state) | `snapshot_serving` + create-once resolution in `scanner` | `GET /api/runs`; `asof_date` echoed by every read | built. **J-43 [built iter-2]:** state serializes to `?asof=yyyy-MM-dd` while historical, restored through the ONE global control; invalid `?asof` → latest; never a second date state; reload/fresh-tab/click-through URL durability verified iter-2 (`asof-provider.tsx` `searchKey` dep fix). **J-50 [TARGET — iter-5 in flight]:** the serialization is ALSO embedded directly in every in-app navigational `href` while historical (sidebar/leaderboard/theme/sector/research links) so same-tab, new-tab/middle-click, and copied-link opens all resolve D **without post-nav re-stamping** — still restored through the ONE global control (J-18 holds); at latest every href is clean |
| Forward-return evidence aggregates (by bucket/setup/regime/pattern; excess vs SPY/QQQ/sector; control groups) — as-of-scoped ≤ D | `forward_testing:compute_forward_aggregates(as_of)` | `GET /api/backtest` | built |
| Per-date scorecard + leadership realized returns + attribution slices (per-stock/by-sector/by-rank-band/distribution) | `forward_testing:compute_run_scorecard` + `_leadership_returns` + shared attribution helper (read-only over stored `forward_returns`) | `GET /api/backtest` | built |
| MAE/MFE excursions per (run, symbol, horizon) | `forward_testing` INSERT path (`forward_excursions`, bars > D) | stored append-only on `forward_returns`; read by event study | built |
| Watchlist entry (date-added, reason, current state, price-since, invalidation) | `watchlist` table; scores read from canonical stock rows at serve time | `GET/POST/DELETE /api/watchlist` | built |
| Setup & pattern catalog (meaning + config thresholds + example) | `methodology:build_catalog(config)` | `GET /api/methodology` | built. **J-47 [TARGET — iter-4 in flight]:** extend the SAME config-backed catalog mechanism with a **≥100-term glossary** (categorized, searchable on `/methodology`); info-tooltips on dense column headers/stat labels (Research, Backtest, Stocks, Dashboard cards, Data coverage) read the SAME entries — no duplicated copy, no second catalog; the Setups & Patterns glossary category is DERIVED from the existing `methodology.entries` (referenced/hosted, never re-described); glossary categories + terms live under `config.methodology` with `ref`-resolved thresholds; no new endpoint |
| Factor-Lab analytics (decile + rank-IC + by-regime; optional `as_of` mode) | `research:compute_factor_lab` | `GET /api/research/factor-lab` | built |
| Multi-factor composite combination cohort | `research:compute_factor_combination` | `GET /api/research/factor-combination` | built |
| Setup & Pattern event study (distribution/expectancy/MAE-MFE/exit-horizon/regime+sector slices) | `research:compute_event_study` | `GET /api/research/event-study` | built |
| **J-51/J-52 [TARGET — iter-7 in flight] — Research samples drill-down** (one row per observation: ticker, snapshot/as-of date, the qualifying stored factor/indicator value(s) — for a combination cohort each referenced factor's stored value, for an event study the matched setup/pattern — and the stored realized forward return at the stated horizon) | the SAME observation sets the aggregates already build, read-only: `research:_factor_observations` / `_combination_observations` / `_event_study_members` (SELECT-only exposure; recomputes no factor, return, or membership) | `GET /api/research/samples` (deep-linkable cohort params: analysis kind, factor(s)/subject, horizon, decile/cohort, regime, sector, all-history-vs-as-of per J-32) [TARGET — iter-7 in flight] | NOT built. **Count coherence:** the drill-down total **equals the published N** chip clicked (same membership filter + observation set the aggregate used); every displayed value is the same stored per-observation value; n=0 → explicit honest empty state (never a fabricated row); column headers read the SAME J-47 glossary; each row's ticker links via J-52 to `/stocks/[ticker]?asof=<row snapshot date>` in a NEW tab |
| Universe membership + selection screen | committed `universe.json` + `config.universe.symbols` via the single screen rule `screen_universe.screen_reasons` | `GET /api/methodology` (rule + size) + `GET /api/data` (`universe_count`) | built; ~500-name live expansion data-walled NA (J-22/J-35 live leg) |
| Coverage + per-symbol table + missing-data diagnostic + definitions | `data_manager:compute_coverage` (single producer; thresholds from config) | `GET /api/data` `coverage` | built |
| Import job control: provider catalog + availability, chunked/resumable checkpoints, unfinished imports (Resume/Retry/Dismiss), expand job, seed-safe remove preview+cascade | `data_manager:*` (ONE import engine; `import_checkpoints` + `DataProviderRun` job-control — not snapshots) | `GET /api/data`, `POST /api/data/jobs*` (+`/resume`,`/retry`,`/dismiss`), `POST /api/data/remove(/preview)` | built. **J-46 [built iter-3]:** the fetch loop runs on a bounded **config-set parallel worker pool** (`data_manager.import_chunking.fetch_workers`; network I/O on workers, DB writes serialized on the orchestrating thread) + **per-chunk single-transaction writes** in `data_manager:_run_chunked_fetch`; the walk-forward backfill loads each symbol's bars **once per job** via a job-scoped cache at the `prices:bars_asof` seam (consumed by `_do_backfill` / `warmup` / `scanner._bootstrap`; a loading optimization, never a second source of bar truth); canonical outputs identical (suites green 659/4/0) + committed **advisory** benchmark script `apps/backend/scripts/benchmark_pipeline.py`. No new displayed value (iter-3). **J-53 [TARGET — iter-5+]:** the multi-date snapshot backfill runs DATES IN PARALLEL (network/compute concurrent, SQLite writes serialized/transactional) ≥~2× faster than the sequential per-date-sum baseline (evidenced by the job's own stage timings + the advisory benchmark; no flaky CI wall-clock gate), with create-once/idempotent/concurrency-safe creation preserved (J-41) and progress honest (J-34/J-37/J-38 intact); the job status payload + the `/data` job card now surface **per-stage timings** (fetch vs backfill: elapsed, items processed, concurrency used) as descriptive operational metadata; any new concurrency knob lives in `config` (no magic numbers) |
| Backend readiness state + warm-up progress (`ready`/`initializing`/`unavailable` + n/m) | `readiness:compute_readiness` (+ `warmup` controller) | `GET /api/health` (the ONE readiness read) | built |
| **J-44/J-45 [built iter-2] — Regime history series** (date → stored regime label + score) | `regime_history:get_regime_history` (read-only over immutable `scanner_runs`; labels/scores read VERBATIM, never recomputed) | `GET /api/regime-history` | built iter-2. Consumed by BOTH the dashboard index-chart bands AND the stock-detail chart bands via ONE shared `apps/frontend/lib/regime.ts` mapping — same label/color per date; honest step function; never rendered past the resolved as-of. **J-49 [TARGET — iter-6 in flight]:** the DASHBOARD card renders the FULL stored regime history (the as-of clamp becomes OPTIONAL for this surface — same stored labels/scores, nothing recomputed, no second path) with a clearly visible vertical as-of MARKER drawn at D while historical (the J-20 divider treatment), no marker at latest; **J-45 is NOT amended** — the stock-detail regime bands still stop at the resolved as-of |
| **J-44 [built iter-2] — Normalized index display series** (config-listed index ETFs as % lines rebased to range start) | `indexes:compute_index_series` (server-side from stored bars; symbols/names/range presets from `config.index_chart`) | `GET /api/indexes` | built iter-2. Presentation series, not a canonical score; a series without stored bars (DIA) is omitted honestly; frontend only re-formats. **J-49 [TARGET — iter-6 in flight]:** the dashboard card charts ALL stored bars (full history) regardless of the global as-of — the as-of clamp is optional for this surface — with a vertical as-of marker at D while historical; range presets re-normalize per J-44 and the marker stays at D; display-only market context (no post-as-of bar feeds any as-of-scoped score/count/gate/evidence — no-lookahead intact) |
| **J-42 [built iter-1] — Displayed date format** (`yyyy-MM-dd` everywhere) | ONE shared frontend formatter `apps/frontend/lib/dates.ts` (`ISO_DATE_FORMAT`, `formatIsoDate`, `formatIsoDateTime`, `isValidIsoDate`); `/data` date fields are validated ISO TEXT inputs | every surface displaying a calendar date (presentation contract — no endpoint) | built (verified + coherence-audited iter-1: no per-component format literals, no locale-dependent widget output; API/DB/config dates ISO unchanged) |

## Coherence invariants (the auditor hard-fails on these)

1. **Single source of truth** — six scores + bucket + setup computed once; read identically everywhere (J-06). *(critical)*
2. **No recompute in the read path** — reads serve persisted-snapshot values; create-once on first view is the only blessed compute. *(critical)*
3. **Snapshots immutable** — `scanner_runs`/`scanner_results`/`*_scores` never mutated; `forward_returns` separate append-only. Job-control tables (`data_provider_runs`, `import_checkpoints`) are legitimately mutable, NOT snapshots. *(critical)*
4. **No lookahead** — as-of-D uses bars ≤ D; forward returns bars > D; unit-tested. Post-D chart region is labelled display-only. *(critical)*
5. **Exactly one date selector** — the global as-of control drives every date-scoped page; `?asof` (J-43) is its SERIALIZATION, never a second state; Research as-of toggle is a mode; import/remove dates are job parameters. *(critical)*
6. **Patterns are patterns, not statuses** — never enter the setup enum, never alone promote Actionable. *(critical)*
7. **Risk-Off gates Actionable** — zero Actionable in Risk-Off. *(critical)*
8. **No fabricated data** — provider failure → explicit error; partial horizons/low samples → NA + n; a configured index series without bars is omitted, never synthesized. *(critical)*
9. **Attribution & lab analytics read-only** — derived from stored returns/excursions/factor values; risk-adjusted uses downside only.
10. **No magic numbers** — weights/thresholds/edges/universe/themes/providers/chunking/startup/range-presets/glossary (and the J-46/J-53 worker-pool + parallel-backfill concurrency) from `config.yaml`.
11. **No order/execution path** — research-only. *(critical)*
12. **Every feature navigable** from the sidebar; no second home for an existing entity; regime label/color identical on every surface for the same date. The J-51 samples drill-down is link-reached under the existing Research home (not a new top-level section).
13. **View transforms & drill-downs never recompute (J-48/J-51/J-52/J-54)** — J-48 leaderboard sorting re-orders the rendered list ONLY (each row's `#`, three scores/buckets, setup, and pattern flags read exactly as served; the `#` column restores the scanner's stored rank); the J-51 samples drill-down is a SELECT-only exposure whose total **equals the published N** it was reached from; new-tab opens (J-50/J-52/J-54) carry `?asof` in the `href` and restore it through the ONE global control — never a second date state (J-06/J-18 hold). *(critical)*
