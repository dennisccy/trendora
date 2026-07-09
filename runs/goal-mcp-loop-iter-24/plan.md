# goal-mcp-loop-iter-24 Execution Plan

## Alignment check
Directly implements goal.md's "Improvement direction (engineering): fast platform on the deep basis"
section, items **B/C/D/G/H/K**, surfacing target journey **J-15**. No drift from goal.md. The session
blueprint (`runs/goal-session-mcp-loop/state/blueprint.md`, tail) already carries a full "iter-24
clarification" paragraph written by the goal-decomposer registering the new `capacity` Data Contract
value — **no developer edit to blueprint.md is needed**, only consistency with it (same pattern as the
iter-20 handoff: "no action needed — already recorded by the decomposer").

Two things worth flagging, found while reading the live code (not blocking, just precision vs. the
spec's own prose):
- `config.yaml:1200`'s `server.memory_cap_mb` comment was **already fixed in iter-19** (it cites the real
  ~3.27M-row figure, not "~1.3M-row"). Item K's conditional fix ("if it still says…") is already
  satisfied — verify only, no edit expected.
- `models.py` today has only **one** redundant `forward_returns` index beyond the unique constraint —
  `Index("ix_forward_returns_run_symbol", "run_id", "symbol")` at `:362` (a prefix of
  `UNIQUE(run_id,symbol,horizon)`). The goal.md/blueprint prose says "prefix index(es)" (plural,
  anticipating two); only drop what is actually redundant — verify with `EXPLAIN QUERY PLAN`, don't
  invent a second index to remove.

## What to Build
- **Item B (SQLite tuning):** a sqlite-only `event.listen(engine, "connect")` pragma hook in
  `app/db.py:make_engine` applying `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=30000`,
  `cache_size=-262144`, `mmap_size=1073741824`, `temp_store=MEMORY` — all sourced from a new
  `database.pragmas` config block (no inline literals); pool sized from config
  (`pool_size`/`max_overflow`). Document the WAL+NORMAL durability trade-off in a docstring/comment.
- **Item C (index hygiene):** drop the duplicate `Index("ix_daily_prices_symbol_date", "symbol", "date")`
  (`models.py:86`, redundant with the unique-constraint index at `:85`) and the redundant
  `Index("ix_forward_returns_run_symbol", "run_id", "symbol")` (`models.py:362`); add
  `Index("ix_daily_prices_date", "date")`. Apply via a guarded `DROP INDEX IF EXISTS` /
  `CREATE INDEX IF NOT EXISTS` step in `app/db.py` run right after `create_db_and_tables` (no Alembic in
  this repo — mirrors the existing `_ensure_additive_columns` guarded-migration pattern). Verify with
  `EXPLAIN QUERY PLAN` that `bars_asof` still hits the unique index and `max(date)`/availability hit the
  new one.
- **Item D (filtered stock fetch):** a ticker-filtered sibling of `snapshot_serving.stored_stock_rows`
  (`:156`) that queries `select(ScannerResult).where(ScannerResult.run_id == run.id,
  ScannerResult.ticker.in_(tickers))` — `ScannerResult.ticker` is already an indexed column
  (`models.py:245`), so this is a direct, efficient filter, not a new capability. Use it from
  `stock_detail_payload` (`:213`, today calls `stored_stock_rows` then linear-scans all rows for one
  ticker) and from `watchlist._canonical_rows` (`watchlist.py:53`, today calls `stocks_payload` →
  `stored_stock_rows` for the whole universe just to build a ticker-keyed dict). Same serializer
  (`json.loads(result.record_json)` + the same `forward_returns` attachment) — byte-identical payload
  shape; preserve `stock_detail_payload`'s case-insensitive ticker match + 404-on-unknown behavior.
- **Item G (cheap readiness probe):** in `app/engine/readiness.py:compute_readiness`, column-project the
  SPY warmup calendar (`select(DailyPrice.date).where(symbol=='SPY')`, not the ORM-row
  `walk_forward_asof_dates` — `forward_testing.py:254` — that `_warmup_dates` (`warmup.py:64`) currently
  uses) and memoize it keyed on `(latest_date, cfg)`. Replace the per-date existence loop at
  `readiness.py:80` (`done = sum(1 for d in cadence_dates if get_run_for_date(session, d) is not None)`)
  with ONE `select(ScannerRun.asof_date).where(asof_date.in_(cadence_dates))` + a set-diff. Budget
  `/api/health` ≤ 0.1 s. Keep the returned `{state, warmup:{done,total,status,message}}` shape and values
  unchanged.
- **Item H (kill the `/api/data` N+1):** the actual per-member loop is inside
  `data_manager._missing_data_diagnostic` (`:200`) at the "(c) intra-series gap" step — the `for symbol in
  sorted(universe_set):` loop (`:244`) issues one `select(DailyPrice.date).where(symbol==symbol,
  date BETWEEN first AND last)` query per member that has data (`:276-281`, up to the 122
  `config.universe.symbols` members). Consolidate into ONE query bounded to `universe`
  (`.where(DailyPrice.symbol.in_(universe))`, no unbounded whole-table scan), grouping the returned
  `(symbol, date)` rows in Python into per-symbol date sets before the existing gap-diff logic. (The
  sibling `_per_symbol_coverage` `group_by` at `:142-171` is the pattern to mirror for structure, though
  that one returns aggregates, not raw dates — this fix needs per-date presence, so it is one bulk
  fetch-then-group rather than a `GROUP BY`.) Alternative worth checking: if this runs inside an active
  `prefilled_bar_cache` context, `_BarCache._dates_by_symbol` (`prices.py:83`) may already hold the same
  per-symbol date lists in memory — reuse it instead of a fresh query if available. Byte-identical
  `no_history`/`thin`/`intra_series_gaps`/`affected_count` output either way.
- **Item K (backend) — DB capacity snapshot:** new `compute_capacity(session, config=None)` in
  `app.engine.data_manager` — DB file size (resolve via `session.get_bind().url.database`, the path
  `db.resolve_database_url` already resolved; do not re-implement path resolution) + row counts for
  `daily_prices` / `scanner_results` / `forward_returns` (`select(func.count()).select_from(Model)`,
  mirrors the `_counts` helper pattern in `tests/test_db.py:275-282`). Pure DB introspection, no
  canonical value recomputed; honest zero snapshot (file size 0 or absent, all counts 0) on a cold/empty
  DB — never an error. Serve as an **additive `capacity` key** on the existing `GET /api/data` payload
  (`api/data.py:94-138`, alongside `coverage`/`runs`/`sources`/`macro`/...).
- **Item K (harness):** new `scripts/measure-perf.sh` — curl-timed **warm** latencies for
  `GET /api/stocks`, `/api/stocks/{ticker}`, `/api/data`, `/api/health`, one bounded K-date backfill
  timing via the existing jobs API (`POST /api/data/jobs` + poll `GET /api/data/jobs/{job_id}`), and the
  DB capacity snapshot — appended to `reports/perf-budgets.md`. Must run against **prod mode**
  (`scripts/start-backend.sh` / `scripts/start-frontend.sh` — confirmed these exist; never `scripts/dev.sh`,
  whose `--reload`/`next dev` compile is not product latency). Respect the same `CHAIN_BACKEND_PORT`/
  `CHAIN_FRONTEND_PORT` env-var convention `start-backend.sh`/`start-frontend.sh` already use (don't
  hardcode a port). Any bound/batch/scope (e.g. how many K dates) comes from a script flag or config
  default, never a bare literal buried in logic.
- **Frontend — storage card on `/data`:** a small read-only card rendering `capacity`'s file size + three
  row counts, honest zero state on a cold DB. This is fast-platform's only user-visible surface this
  iteration.
- **Fresh measurements:** re-run and record in `reports/perf-budgets.md` the before/after for page
  time-to-interactive (`/stocks`, `/stocks/AAPL` incl. Full-history toggle, `/data`, `/evidence`) and warm
  endpoint latency (the four endpoints above), plus a re-verification that the cold `/api/data` path
  still completes ≤ 60 s without OOM (item A, iter-19) now that C/G/H change its query plans.

## Out of scope (do not implement this iteration)
Per the phase spec's own OUT OF SCOPE section — flagging so implementation doesn't creep into goal.md's
adjacent items while "in the area":
- Item E (lean `/api/stocks` summary DTO) and item J (`record_json` compression) — later payload/storage pass.
- Item I (frontend interaction costs — heatmap memo, leaderboard debounce, chart reuse) — later frontend pass.
- Item F (window the scoring inputs) and **J-16** (data-jobs ≥30% improvement) — a distinct risky
  byte-identity-gated change; its own iteration (never bundled with this one — rubric rule against two
  risky journeys in one diff).
- Any `## Evidence Claim` / ledger change (J-02/J-06/J-07/J-08/J-09 stay sanctioned-partial, untouched).
- Any change to a displayed number. If a test needs its expectation edited to pass, that's a regression
  signal — stop and diagnose, don't refresh the golden.
- Deleting the dead-duplicate dashboard components (coherence-WARN carry-forward) — unrelated to `/data` perf.

## Agents Required
- backend-data: yes -- implement items B, C, D, G, H, K(backend)+K(harness) in
  `apps/backend/app/{db.py,config.py,models.py,engine/snapshot_serving.py,engine/readiness.py,
  engine/data_manager.py,api/data.py,api/watchlist.py}` + `config.yaml`; add/extend targeted tests; run
  `scripts/measure-perf.sh` against prod mode and record `reports/perf-budgets.md`; write the dev handoff.
- frontend-ux: yes -- add the storage card to `apps/frontend/app/data/page.tsx` + the `capacity` type to
  `apps/frontend/lib/api.ts`, consuming the additive `GET /api/data` field.

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/db.py` -- sqlite-only connect-event pragma hook in `make_engine`; guarded post-boot
  index drop/add step (mirrors the existing `_ensure_additive_columns` guarded-migration pattern)
- `apps/backend/app/config.py` -- extend `DatabaseCfg` (`:1652`, currently just `url: str`) with a typed
  `pragmas` sub-block + pool-sizing fields (style precedent: `ProviderCatalogEntry`/`ImportChunkingCfg`
  nearby); note `DatabaseCfg` already has `model_config = ConfigDict(extra="allow")`
- `config.yaml` -- add `database.pragmas` block + pool-sizing keys under the existing `database:` section
  (`:95-96`)
- `apps/backend/app/models.py` -- remove `Index("ix_daily_prices_symbol_date", ...)` (`:86`) and
  `Index("ix_forward_returns_run_symbol", ...)` (`:362`)
- `apps/backend/app/engine/snapshot_serving.py` -- add the ticker-filtered row fetch near
  `stored_stock_rows` (`:156`); wire it into `stock_detail_payload` (`:213`)
- `apps/backend/app/api/watchlist.py` -- wire `_canonical_rows` (`:53`) to the filtered fetch for its
  ticker set (currently calls `stocks_payload` for the whole universe)
- `apps/backend/app/engine/readiness.py` -- column-project + memoize the SPY calendar; replace the
  per-date loop (`:78-80`) with one grouped existence query
- `apps/backend/app/engine/data_manager.py` -- fix the per-member intra-series-gap query inside
  `_missing_data_diagnostic` (loop at `:244`, N+1 query at `:276-281`); add `compute_capacity()`
- `apps/backend/app/api/data.py` -- add `"capacity": data_manager.compute_capacity(...)` to
  `data_overview` (`:94-138`)
- `scripts/measure-perf.sh` -- NEW ops script (curl timings + bounded backfill timing + capacity
  snapshot; appends to `reports/perf-budgets.md`). Distinct from the existing
  `apps/backend/scripts/benchmark_pipeline.py`, which is an offline in-process advisory benchmark against
  a throwaway temp DB — not a curl/HTTP prod-mode measurement; don't conflate the two.
- `reports/perf-budgets.md` -- append the new before/after measurement section (existing file, iter-19's
  item-A section stays; do not overwrite it)
- `apps/frontend/lib/api.ts` -- add a `capacity` field to `DataOverviewResponse` (`:2285`)
- `apps/frontend/app/data/page.tsx` -- new small storage card placed after `CoveragePanel` (`:655-728`)
- Backend tests -- extend `apps/backend/tests/test_db.py` (pragma hook applies only for sqlite URLs;
  index drop/add; `EXPLAIN QUERY PLAN` — this is a genuinely new test technique, no existing precedent in
  the suite to copy), `apps/backend/tests/test_data_manager.py` (`compute_capacity`; the diagnostic
  byte-identity before/after the N+1 fix), `apps/backend/tests/test_health.py` (readiness memoization +
  single grouped query; existing readiness tests live here, no `test_readiness.py` file exists), and
  confirm `apps/backend/tests/test_api_engine.py` + `test_api_watchlist.py` (the `/api/stocks/{ticker}` +
  watchlist byte-identity gates for item D) pass **unedited**.
- `docs/handoffs/goal-mcp-loop-iter-24-dev.md` -- dev handoff (DoD requirement)

## UI Evolution
- New user-facing capability: the user can see the platform's current data-storage footprint on the Data
  Manager; core pages/APIs are measurably faster (not independently visible as a "feature" beyond feeling
  snappier — the proof lives in `reports/perf-budgets.md`, not new UI).
- New information displayed: DB file size + row counts for `daily_prices` / `scanner_results` /
  `forward_returns` on a new `/data` card.
- New user actions: none — the card is read-only; `scripts/measure-perf.sh` is an ops script, not a UI control.
- UI surface changes: one new read-only card on the EXISTING `/data` page. No new page.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing `Card` + `PanelTitle` + `DefinedMetric` composition already used
  by `CoveragePanel` (`app/data/page.tsx:655-728`) — don't introduce a new card primitive for this.
- Layout: place the new card directly after `CoveragePanel` in the existing `/data` page flow (same
  column as `MembershipTimelinePanel`/`SurvivorshipDisclosure`); a small `DefinedMetric` grid (file size +
  3 row counts), matching `CoveragePanel`'s `grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3` pattern.
- Key visual effects: none new — match the existing Data Manager panel styling; this is a small
  descriptive card, not a hero surface.
- States to handle: honest zero state on a cold/empty DB (0 B / 0 rows, not an error); on a backend-fetch
  failure, fold into the page's existing "Dataset coverage could not load from the API" treatment rather
  than fabricating a second error UI.

## Key Test Scenarios
- Item B: a test asserts the sqlite `connect` hook applies the configured pragmas (`journal_mode=wal`,
  `synchronous`, `busy_timeout` readable via `PRAGMA` queries on the connection) and that a non-sqlite URL
  is unaffected (no dialect-specific code runs).
- Item C: after startup, `ix_daily_prices_symbol_date` and `ix_forward_returns_run_symbol` are absent,
  `ix_daily_prices_date` is present; `EXPLAIN QUERY PLAN` shows `bars_asof` using the unique index and
  `max(date)`/availability using the new date index.
- Item D: the ticker-filtered fetch returns a payload byte-identical to the prior full-deserialize path
  for both `stock_detail_payload` and the watchlist path; `test_api_engine.py` + `test_api_watchlist.py`
  pass **unedited**.
- Item G: readiness memoizes the SPY calendar (no re-materialization on repeated calls with the same
  `(latest_date, cfg)`), issues one grouped run-existence query instead of N, and the reported readiness
  figure (`done`/`total`/`state`) is unchanged from before.
- Item H: `_missing_data_diagnostic` issues one bounded query (not one per universe member) and returns a
  byte-identical `no_history`/`thin`/`intra_series_gaps`/`affected_count` shape vs. the pre-fix version.
- Item K: `compute_capacity` reports correct row counts + file size on a loaded DB, is additive on
  `GET /api/data` (existing keys unchanged), recomputes no canonical value, and serves a valid all-zero
  snapshot on an empty DB (no crash).
- Error cases: a cold `/api/data` still completes ≤ 60 s without OOM under the 6144 MB cap post-C/G/H; an
  invalid `as_of` on `/api/data` still falls back gracefully; the WAL pragma hook fires ONLY for sqlite URLs.
- Browser (canonical J-15 lane, live, non-empty evidence dir): `/stocks`, `/stocks/AAPL` (incl.
  Full-history toggle), `/data` (incl. the new storage card showing real numbers), `/evidence` render and
  are interactive within budget (pages ≤ 3 s warm; never a blank/frozen/application-error frame on a slow
  load — an honest initializing/progress state instead). Live-replay required-still-passing J-01, J-03,
  J-04, J-05, J-10, J-12, J-13, J-14.
- Budgets recorded in `reports/perf-budgets.md`: pages ≤ 3 s warm; `GET /api/stocks` ≤ 1.5 s;
  `/api/stocks/{ticker}` ≤ 0.3 s; `/api/data` ≤ 1.5 s warm, cold path ≤ 60 s no OOM; `/api/health` ≤ 0.1 s.
  If a budget proves infeasible without a correctness trade-off, record the measured value as the new
  contract explicitly (don't silently omit it).

## Operational hygiene (carried from the phase spec's Notes)
- Before browser QA: `rm -rf apps/frontend/.next`; bring up both services in **prod mode**
  (`start-backend.sh` / `start-frontend.sh`) and confirm HTTP-200 on both before measuring or testing.
- Clear `/tmp/pytest-of-*` before any test phase (the 30-year fixture exhausts `/tmp` every ~2-3 phases —
  known operator hazard this session).
- Do not pin the full ~10 h 30-year pytest suite as a gate — targeted/affected tests + a bounded run only.
- New bounds/batches (e.g. K in the bounded backfill timing) come from config or a script flag, never a
  bare literal.
