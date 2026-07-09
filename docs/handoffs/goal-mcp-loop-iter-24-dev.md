# goal-mcp-loop-iter-24 Dev Handoff

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Agent:** developer
**Status:** complete

> **AUDIT CORRECTION (iter-24 audit, 2026-07-09).** Two claims below were invalidated by the audit and
> have been fixed:
> 1. **Item B's `mmap_size=1073741824` (1 GB) is now `mmap_size_bytes: 0` (mmap DISABLED).** The 1 GB
>    read-mmap window reserved ~1 GB of VIRTUAL address space PER pooled connection; at `pool_size=10 +
>    max_overflow=20` just ~6 live connections exhausted the `server.memory_cap_mb=6144` `ulimit -v` cap
>    BEFORE the cold `/api/data` bar prefill ran — crashing the first `/data` load after every restart
>    (`MemoryError` → PyO3 panic; browser-qa UT-16, reproduced 2/2; a critical anti-goal-#8 violation).
> 2. **The "Live verification … cold `/api/data` re-verified … no OOM" claim was false** — its evidence was
>    a `/api/health` (readiness) boot, not an actual `GET /api/data` cold request. The real cold path
>    crashed. See `reports/perf-budgets.md` (corrected) and `docs/handoffs/goal-mcp-loop-iter-24-audit.md`
>    §2 for the confirmed root cause + the controlled-ablation re-verification (mmap=0 → 471 MB peak, OK).

## What Was Built

Goal.md's fast-platform **mechanical backend pass** (items B/C/D/G/H), the measurement harness (item K),
and a read-only storage-footprint card — all byte-identity-gated (no displayed number changes).

- **Item B — SQLite tuning.** `app/db.py:make_engine` now registers a sqlite-only `event.listen(engine,
  "connect")` hook applying `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=30000`,
  `cache_size=-262144`, `mmap_size=1073741824`, `temp_store=MEMORY` — every value sourced from a new
  `database.pragmas` config block (`DatabasePragmasCfg`, boot-validated against SQLite's own PRAGMA
  vocabularies). The engine pool is sized from new `database.pool_size`/`max_overflow` config keys
  (10/20). The pragma hook and pool kwargs are gated behind the SAME `_is_sqlite_url()` check that
  already drove `check_same_thread` — the one dialect-specific site stays one site. In-memory sqlite URLs
  (`sqlite://`, `sqlite:///:memory:`) are excluded from the pool-size kwargs (their default pool class
  rejects them) but still get the pragma hook.
- **Item C — Index hygiene.** Removed the byte-for-byte-duplicate `Index("ix_daily_prices_symbol_date",
  ...)` and the redundant `Index("ix_forward_returns_run_symbol", ...)` from `models.py` (both are
  strict prefixes of an existing unique-constraint index). Added a guarded, idempotent post-boot
  migration step in `app/db.py` (`_ensure_index_hygiene`, mirrors the existing `_ensure_additive_columns`
  pattern): `DROP INDEX IF EXISTS` on the two removed indexes (a no-op on a fresh DB, a real drop on a
  live DB still carrying them) and `CREATE INDEX IF NOT EXISTS ix_daily_prices_date (date)`. Verified via
  `EXPLAIN QUERY PLAN` that `bars_asof`'s `symbol=? AND date<=?` filter still resolves through an index
  (SQLite's own autoindex for the unique constraint) and that `max(date)` now resolves through the new
  date index.
- **Item D — Ticker-filtered stock fetch.** New `filtered_stock_rows()` in `snapshot_serving.py`: queries
  `ScannerResult` filtered by `run_id` + `ticker IN (...)` (case-insensitive via `func.upper(...)`)
  instead of deserializing every row in the run. `stock_detail_payload` and the watchlist's
  `_canonical_rows` (now ticker-scoped, taking an explicit `tickers` iterable) both use it. Same
  serializer, byte-identical payload shape — `test_api_engine.py`'s and `test_api_watchlist.py`'s
  existing byte-identity tests pass **unedited**.
- **Item G — Cheap readiness probe.** `readiness.py` memoizes the cadence-date derivation
  (`_cached_warmup_dates`, single-entry, keyed on `(latest_date, id(cfg))`) so `/api/health` (polled every
  ~2s) does not re-derive the warm-up calendar on every poll; the cache-miss path wraps the derivation in
  the existing `bar_cache(session)` context so the underlying SPY-bars read is column-projected (reusing
  the iter-19 `_BarCache` machinery, not a second implementation). The per-date `get_run_for_date`
  existence loop is replaced by ONE grouped `select(ScannerRun.asof_date).where(asof_date.in_(...))` +
  a set-based count. Reported `done`/`total`/`state` values are unchanged.
- **Item H — Fixed the `/api/data` cold-path N+1.** `data_manager._missing_data_diagnostic`'s intra-
  series-gap check replaced a one-`DailyPrice.date`-query-per-universe-member loop with ONE bulk
  `select(DailyPrice.symbol, DailyPrice.date).where(symbol.in_(universe))` query, grouped into per-symbol
  date sets in Python before the existing (unchanged) gap-diff logic. Byte-identical output.
- **Item K (backend) — DB capacity snapshot.** New `compute_capacity(session, config=None)` in
  `data_manager.py`: resolves the DB file path via `session.get_bind().url.database` (reusing the
  existing `_db_identity` technique) for the on-disk file size, plus row counts for `daily_prices` /
  `scanner_results` / `forward_returns`. Pure DB introspection, no canonical value recomputed; honest
  all-zero snapshot on a cold/empty or unresolvable-path DB. Served as an additive `"capacity"` key on
  the existing `GET /api/data` payload (`api/data.py`) — no new endpoint. Also fixed a second, previously
  unnoticed stale "~1.3M-row" comment (this one in `config.py`'s `ServerOpsCfg` docstring, distinct from
  the already-fixed `config.yaml` comment the plan's alignment check had already verified).
- **Item K (harness) — `scripts/measure-perf.sh`** (new; lives at `incredible_auto_dev/scripts/
  measure-perf.sh`, reachable at the repo root via the existing `scripts -> incredible_auto_dev/scripts`
  symlink, same as `start-backend.sh`/`start-frontend.sh`). Curl-times warm latencies for the four J-15
  endpoints and pages, reads the item-K capacity snapshot, and times one bounded (`--backfill-days`,
  default 5) backfill job via the existing jobs API — appending every measurement to
  `reports/perf-budgets.md`. Uses the same deterministic port-offset convention as `start-backend.sh`/
  `dev.sh`. Ran successfully against live prod-mode services (see Tests Run below).
- **Frontend — storage card.** `apps/frontend/lib/api.ts` gained a `DataCapacity` type + the `capacity`
  field on `DataOverviewResponse`. `apps/frontend/app/data/page.tsx` gained a `StorageCapacityPanel`
  component (reusing the existing `Card`/`PanelTitle`/`DefinedMetric` composition, matching
  `CoveragePanel`'s grid pattern) placed directly after `CoveragePanel`, plus a small `fmtBytes()`
  formatter. Read-only; honest zero values render naturally since `compute_capacity` already returns 0s
  on a cold DB (no separate empty-state branch needed).

## Files Changed

- `apps/backend/app/db.py` -- sqlite pragma hook (`_apply_sqlite_pragmas`), `_is_sqlite_url` gate, pool
  sizing in `make_engine`; guarded index-hygiene migration (`_ensure_index_hygiene`) wired into
  `create_db_and_tables`
- `apps/backend/app/config.py` -- new `DatabasePragmasCfg`; `DatabaseCfg` gains `pragmas`/`pool_size`/
  `max_overflow` (all default-populated, boot-validated); fixed a second stale "~1.3M-row" comment in
  `ServerOpsCfg`
- `config.yaml` -- `database.pragmas` block + `pool_size`/`max_overflow` keys
- `apps/backend/app/models.py` -- removed `Index("ix_daily_prices_symbol_date", ...)` and
  `Index("ix_forward_returns_run_symbol", ...)`
- `apps/backend/app/engine/snapshot_serving.py` -- new `filtered_stock_rows()`; `stock_detail_payload`
  now uses it
- `apps/backend/app/api/watchlist.py` -- `_canonical_rows` now ticker-scoped via `filtered_stock_rows`
- `apps/backend/app/engine/readiness.py` -- memoized cadence-date derivation + grouped run-existence
  query
- `apps/backend/app/engine/data_manager.py` -- fixed `_missing_data_diagnostic`'s N+1 (item H); new
  `compute_capacity()` (item K)
- `apps/backend/app/api/data.py` -- additive `"capacity"` key on `data_overview`
- `incredible_auto_dev/scripts/measure-perf.sh` (NEW; repo-root symlink: `scripts/measure-perf.sh`) --
  the item-K measurement harness
- `.gitignore` -- added `*.db-shm`/`*.db-wal` (WAL mode's sidecar files, a direct consequence of item B
  that the existing `*.db`/`*.db-journal` patterns did not cover)
- `apps/frontend/lib/api.ts` -- `DataCapacity` type + `DataOverviewResponse.capacity`
- `apps/frontend/app/data/page.tsx` -- `StorageCapacityPanel` + `fmtBytes()`, wired in after
  `CoveragePanel`
- `reports/perf-budgets.md` -- appended the iter-24 measurement section (existing iter-19 content
  untouched)
- Tests -- extended `apps/backend/tests/test_db.py` (items B+C: pragma application, config-sourced
  values, pool sizing, sqlite-URL gating, index drop/add on fresh + legacy DBs, idempotency, two
  `EXPLAIN QUERY PLAN` checks), `apps/backend/tests/test_data_manager.py` (item H: query-count-does-not-
  scale-with-universe-size proof; item K: `compute_capacity` exact counts, empty-DB zero snapshot,
  no-canonical-recompute guard), `apps/backend/tests/test_health.py` (item G: memoization, config-object
  differentiation, grouped-query-vs-manual-check equivalence, query-count proof),
  `apps/backend/tests/test_api_engine.py` (item D: byte-identity + row-count-reduction proof for
  `filtered_stock_rows`), `apps/backend/tests/test_api_data.py` (item K: additive `capacity` key on
  `GET /api/data`, exact on a tiny fixture)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<selection> -v`

- `tests/test_db.py`: **19 passed** in 6332.34s (1:45:32) -- includes the one-time 30-year `loaded_engine`
  fixture build, which dominates the wall time on this host.
- `tests/test_data_manager.py tests/test_health.py tests/test_api_engine.py tests/test_api_watchlist.py
  tests/test_api_data.py` (combined, to amortize the fixture cost once): first run **1 failed, 162
  passed** in 10177.36s (2:49:37) -- the one failure was my own new test's miscounted query-count
  assertion (`test_diagnostic_issues_one_bulk_own_dates_query_not_one_per_member` forgot that
  `_missing_data_diagnostic` also calls `_trading_days`, which issues 2 more `daily_prices` queries
  before item H's own code runs -- an error in the test, not the implementation). Fixed by replacing it
  with `test_diagnostic_query_count_does_not_scale_with_universe_size` (asserts the query count is
  IDENTICAL between a 2-member and an 8-member universe -- a more robust proof that does not hard-code an
  unrelated sibling function's query count). Re-verified in isolation (no `loaded_engine` needed): **6
  passed** in 0.95s, then the full `test_data_manager.py` file: **84 passed** in 94.70s.
- No other test files were touched; `test_api_watchlist.py` and the rest of `test_api_engine.py`/
  `test_api_data.py`/`test_health.py` passed unedited in the combined run above.
- Full backend suite (~10h on this 30-year basis) was **not** run, per the phase spec's own guidance
  (targeted selections only).

Frontend: `npx tsc --noEmit` -- clean (exit 0), and `npx next build` (via `start-frontend.sh`'s rebuild
path) succeeded, producing a working production bundle.

**Live verification (prod mode, both services):**
- `start-backend.sh`/`start-frontend.sh` brought up cleanly on the deterministic ports (8255/3255);
  `/api/health` reported `readiness: ready`, `warmup: 89/89` shortly after boot against the real 1.3 GB /
  3.27M-row committed DB.
- `scripts/measure-perf.sh` ran successfully; every J-15 budget met with wide headroom (see
  `reports/perf-budgets.md`'s new section for exact numbers).
- Live byte-identity spot-check: `/api/stocks`' AAPL row == `/api/stocks/AAPL`'s row == the watchlist
  add-response's canonical fields (added then removed a real "AAPL" watchlist entry during the check).
- Live capacity snapshot: `db_file_bytes: 1307414528`, `daily_prices_rows: 3293160`,
  `scanner_results_rows: 165755`, `forward_returns_rows: 821054` -- real numbers from the live DB.
- Confirmed index hygiene applies for real: the live committed DB carried both redundant indexes before
  this boot (verified via direct `sqlite_master` query); after `create_db_and_tables` ran (1.288s on the
  full 3.27M-row table), both were dropped and `ix_daily_prices_date` was added.
- Both services stopped cleanly after verification (confirmed via HTTP connection-refused on both ports).

## Known Issues

- **`scripts/measure-perf.sh`'s backfill-timing heuristic can land on a non-cadence-eligible range.** The
  script picks a range from `coverage.gaps_preview` (every trading day with bars-but-no-snapshot), but
  the backfill job itself only targets CADENCE-ELIGIBLE dates in range (sparser for deep history --
  the coverage gap list is not cadence-filtered). On an already-fully-warmed backend (as in this
  iteration's live run), essentially every remaining "gap" is a deep-history day that was never meant to
  get a snapshot under the sparse historical cadence policy, so the harness's picked range legitimately
  resolved to "0 cadence-eligible dates" -- an honest, fast (0.23s) no-op, not a bug, and the script now
  labels this case accurately after a mid-session fix (it originally mislabeled it "a real backfill
  gap"). A future iteration wanting a truly illustrative COLD backfill timing would need to either target
  a genuinely un-warmed DB, or have the harness resolve cadence-eligible dates itself (a small addition,
  deferred -- the DoD only required "one bounded K-date backfill timing via the jobs API", which this
  delivers with an honest result either way).
- **This host is unusually slow for the 30-year `loaded_engine` fixture** (the one-time bootstrap +
  forward-return backfill it performs took ~1h45m the first time and again the second time, in a
  separate pytest process/session). This is independent of this iteration's changes -- direct timing of
  every individual piece (`create_db_and_tables`, `ensure_latest_snapshot`, `compute_readiness`,
  `_warmup_dates`, the `run_scan` idempotent-check loop, `backfill_forward_returns`,
  `_warm_membership_timeline`) against the real 1.3 GB live DB showed each completing in well under 6
  seconds; the fixture's total cost is the cumulative effect of ~90 cadence dates on this specific box,
  not a regression introduced here. Documented so a future session isn't surprised by it again.
- Per the plan's own "Out of scope" section, items E/F/I/J (lean leaderboard DTO, scoring-window
  trimming, frontend interaction costs, `record_json` compression) and J-16 (data-jobs ≥30% improvement)
  are deliberately deferred to later iterations, as are any evidence-ledger changes (none were made this
  iteration; no `## Evidence Claim` was carried, matching the plan).
