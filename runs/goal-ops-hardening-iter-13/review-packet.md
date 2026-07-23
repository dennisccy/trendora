# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/api/indexes.py b/apps/backend/app/api/indexes.py
index 356da846..c3d6b822 100644
--- a/apps/backend/app/api/indexes.py
+++ b/apps/backend/app/api/indexes.py
@@ -15,8 +15,9 @@ from typing import Optional
 from fastapi import APIRouter, Depends, HTTPException, Query
 from sqlmodel import Session
 
+from app.config import get_config
 from app.db import get_session
-from app.engine.indexes import UnknownRangeError, compute_index_series
+from app.engine.indexes import UnknownRangeError, compute_index_series, index_series_cached
 from app.engine.scanner import AsOfError
 from app.engine.snapshot_serving import _http
 
@@ -38,7 +39,17 @@ def indexes(
     session: Session = Depends(get_session),
 ) -> dict:
     try:
-        return compute_index_series(session, as_of=as_of, range_key=range, full=full)
+        cfg = get_config()
+        # ops-hardening iter-13 (J-06): the SINGLE unparameterized default hot key
+        # (no/default range, full=True, no explicit historical as_of) is served from the ingest-warmed
+        # `IndexSeriesCache` (PhaseCrossViewCard `/` and IndexVendorPanel `/data` both request exactly
+        # this, unparameterized, on mount). Every other combination — an explicit non-default range, or
+        # an explicit historical as_of — keeps calling `compute_index_series` directly, unchanged, lazy
+        # (the existing "cannot be precomputed — user-parameterized" carve-out).
+        is_hot_key = full and as_of is None and (range is None or range == cfg.index_chart.default_range)
+        if is_hot_key:
+            return index_series_cached(session, config=cfg)
+        return compute_index_series(session, as_of=as_of, range_key=range, config=cfg, full=full)
     except UnknownRangeError as exc:
         raise HTTPException(status_code=422, detail=str(exc))
     except AsOfError as exc:
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index b38e047f..f6e03c1f 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1886,9 +1886,10 @@ class JobProgress:
     # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
-    # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]` it
-    # actually refreshed — empty/default until the hook has actually run (never fabricated on an
-    # interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc. already are).
+    # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
+    # "index_series"]` it actually refreshed — empty/default until the hook has actually run (never
+    # fabricated on an interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc.
+    # already are).
     new_snapshot_dates: list[date_cls] = field(default_factory=list)
     aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
@@ -3120,8 +3121,8 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
     "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    "drawdown_expectations"]` ACTUALLY refreshed — never a fabricated category (mirrors the
-    `omitted`/`passers` honesty convention already used elsewhere in this module).
+    "drawdown_expectations", "index_series"]` ACTUALLY refreshed — never a fabricated category (mirrors
+    the `omitted`/`passers` honesty convention already used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -3251,6 +3252,39 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
         logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)
 
+    # ops-hardening iter-13 (J-06, aggregation candidate #7): warm the SINGLE unparameterized default
+    # hot key for `GET /api/indexes` (`range_key=cfg.index_chart.default_range`, `full=True` —
+    # `PhaseCrossViewCard` on `/` and `IndexVendorPanel` on `/data` both request exactly this,
+    # unparameterized, on mount). Mirrors the `research_hot_keys` block just above: a single-key warm,
+    # unconditional (NOT gated on `prog.new_snapshot_dates`) because `IndexSeriesCache`'s
+    # dataset-version stamp is scoped to the configured `index_chart.symbols`' bar freshness (not to
+    # "this run's new snapshot dates") — ANY ingest that lands a bar for a configured index symbol,
+    # anywhere, must invalidate it, mirroring `forward_aggregates`'s "the stamp is global" reasoning
+    # above. Deferred import (not at module level): `indexes.py` already imports `load_seed_meta` FROM
+    # this module at ITS OWN module level, so importing `indexes` back here at data_manager's module
+    # scope would cycle; the deferred, function-scoped import breaks the cycle exactly like
+    # `forward_aggregates_cached`'s own deferred `_dataset_version` import from `research.py`.
+    #
+    # iter-8 MemoryError-isolation convention: caught distinctly from the generic exception below, stops
+    # immediately (a single key, not a loop — nothing further to attempt) and calls
+    # `_release_process_memory()` before moving on to the next aggregate category. "index_series" is
+    # appended ONLY when this call actually persisted a new row this run (`persisted` is False on a
+    # cache HIT — an honest "was skipped" omission, never a fabricated refresh, mirroring every other
+    # category's honesty gate above).
+    from app.engine import indexes  # deferred: see comment above (breaks a module-load cycle)
+
+    try:
+        _, index_series_persisted = indexes.index_series_cached_with_status(session, cfg)
+        if index_series_persisted:
+            refreshed.append("index_series")
+    except MemoryError as exc:
+        logger.exception(
+            "ingest index-series warm aborted — memory pressure: %s", exc,
+        )
+        _release_process_memory()
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest index-series warm failed (non-fatal): %s", exc)
+
     # ops-hardening iter-7 (J-06 closeout, audit B1): warm the per-claim `drawdown_expectations`
     # EventStudyCache view slot — the SAME cache slot `build_evidence_payload` looks up lazily via
     # `forward_testing.compute_drawdown_expectations_cached` on a live `/api/evidence` request. Without
diff --git a/apps/backend/app/engine/indexes.py b/apps/backend/app/engine/indexes.py
index 663f9336..a48ca395 100644
--- a/apps/backend/app/engine/indexes.py
+++ b/apps/backend/app/engine/indexes.py
@@ -23,16 +23,19 @@ explicit 422 — never a silent fallback to a fabricated range).
 """
 from __future__ import annotations
 
-from datetime import date as date_cls, timedelta
+import json
+from datetime import date as date_cls, datetime, timedelta, timezone
 from pathlib import Path
 from typing import Optional
 
-from sqlmodel import Session
+from sqlalchemy import func
+from sqlmodel import Session, select
 
 from app.config import Config, IndexRangePreset, get_config
 from app.engine.data_manager import load_seed_meta
 from app.engine.prices import bars_asof, bars_through_latest
 from app.engine.scanner import resolve_as_of_date
+from app.models import DailyPrice, IndexSeriesCache
 
 # iter-22 (J-14) — the honest display label for each committed-seed manifest vendor key (`data/seed/
 # meta.json` `symbols[].vendor`). A key with no mapping falls back to the raw key itself (never a crash,
@@ -174,3 +177,115 @@ def compute_index_series(
         "ranges": [{"key": p.key, "label": p.label} for p in cfg.index_chart.range_presets],
         "series": series,
     }
+
+
+# --------------------------------------------------------------------------------------------------
+# Ingest-time serving cache for the SINGLE unparameterized default hot key (ops-hardening iter-13,
+# J-06 — aggregation candidate #7): `range_key=cfg.index_chart.default_range`, `full=True`, no explicit
+# `as_of`. Every other request combination (a user-selected non-default range, an explicit historical
+# as-of) stays on the lazy, uncached `compute_index_series` call above — unchanged.
+# --------------------------------------------------------------------------------------------------
+
+
+def index_series_dataset_version(session: Session, config: Optional[Config] = None) -> str:
+    """A NARROW cache stamp for `IndexSeriesCache`, scoped ONLY to the inputs the hot-key series
+    actually reads: the configured `index_chart.symbols`' stored bars. Deliberately NOT the broad
+    `research._dataset_version` (which folds in the `forward_returns` row count and would invalidate on
+    unrelated ingest activity that never touches an index symbol's bars) — mirrors
+    `research._membership_dataset_version`'s own narrow-stamp precedent (scope the stamp to only what
+    the cache reads).
+
+    A single bounded, indexed read (`max(date)` + `count(*)` filtered to the configured index symbols,
+    served by the existing `uq_daily_prices_symbol_date` / `ix_daily_prices_date` indexes) — never a
+    whole-`daily_prices`-table scan. Changes whenever a configured index symbol gains, loses, or has a
+    bar altered anywhere in its history; unaffected by ingest activity for any OTHER symbol or by a pure
+    forward-return insert."""
+    cfg = config or get_config()
+    symbols = [entry.symbol for entry in cfg.index_chart.symbols]
+    if not symbols:
+        return "none"
+    max_date = session.exec(
+        select(func.max(DailyPrice.date)).where(DailyPrice.symbol.in_(symbols))
+    ).one()
+    if isinstance(max_date, tuple):
+        max_date = max_date[0]
+    count = session.exec(
+        select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol.in_(symbols))
+    ).one()
+    if isinstance(count, tuple):
+        count = count[0]
+    date_stamp = max_date.isoformat() if max_date is not None else "none"
+    return f"d{date_stamp}-c{count or 0}"
+
+
+def index_series_cached_with_status(
+    session: Session, config: Optional[Config] = None, seed_dir: Optional[str | Path] = None,
+) -> tuple[dict, bool]:
+    """Serve the hot-key `compute_index_series(as_of=None, range_key=cfg.index_chart.default_range,
+    full=True)` payload from `IndexSeriesCache`, returning `(payload, persisted_this_call)`: on a cache
+    HIT for the current `(range_key, full, dataset_version)` key, deserialize the stored payload (NO
+    recompute), re-derive the CURRENT resolved `as_of` and overwrite the echoed `asof_date` with it (see
+    `IndexSeriesCache`'s own docstring — the only as-of-dependent part of this response), and return
+    `persisted_this_call=False`; on a MISS or a stale dataset-version stamp, compute ONCE via the
+    UNCHANGED `compute_index_series` (the SOLE producer — this function is a pure serving/persistence
+    wrapper, never a second derivation), persist it under the current stamp, prune any stale rows for
+    this `(range_key, full)` identity, and return `persisted_this_call=True`. The returned payload is
+    BYTE-IDENTICAL to `compute_index_series(...)` for the same inputs (No recompute in the read path).
+
+    `persisted_this_call` is the honesty gate the ingest finalize hook's `aggregates_refreshed` reads:
+    "index_series" is reported ONLY when this call actually wrote a new row — a cache HIT (nothing new
+    to persist) is an honest skip, mirroring the "was skipped" omission every other warm category
+    already follows, never a fabricated refresh."""
+    cfg = config or get_config()
+    range_key = cfg.index_chart.default_range
+    version = index_series_dataset_version(session, cfg)
+
+    hit = session.exec(
+        select(IndexSeriesCache).where(
+            IndexSeriesCache.range_key == range_key,
+            IndexSeriesCache.full == True,  # noqa: E712 — SQLAlchemy column comparison, not a bool identity check
+            IndexSeriesCache.dataset_version == version,
+        )
+    ).first()
+    if hit is not None:
+        resolved = resolve_as_of_date(session, None, cfg)  # re-derived fresh, never trusted from storage
+        payload = json.loads(hit.payload_json)
+        payload["asof_date"] = resolved.isoformat()
+        return payload, False
+
+    # MISS — compute once (the SOLE producer, unchanged) and persist.
+    payload = compute_index_series(
+        session, as_of=None, range_key=range_key, config=cfg, full=True, seed_dir=seed_dir
+    )
+
+    # prune stale rows for THIS (range_key, full) identity (any older dataset_version) so the cache
+    # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
+    stale = session.exec(
+        select(IndexSeriesCache).where(
+            IndexSeriesCache.range_key == range_key,
+            IndexSeriesCache.full == True,  # noqa: E712
+            IndexSeriesCache.dataset_version != version,
+        )
+    ).all()
+    for row in stale:
+        session.delete(row)
+
+    session.add(IndexSeriesCache(
+        range_key=range_key, full=True, dataset_version=version,
+        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
+    ))
+    try:
+        session.commit()
+    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
+        session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
+    return payload, True
+
+
+def index_series_cached(
+    session: Session, config: Optional[Config] = None, seed_dir: Optional[str | Path] = None,
+) -> dict:
+    """The `GET /api/indexes` hot-key route's own entry point: the payload half of
+    `index_series_cached_with_status` (drops the `persisted_this_call` flag, which only the ingest
+    finalize hook's honesty gate needs)."""
+    payload, _persisted = index_series_cached_with_status(session, config, seed_dir)
+    return payload
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 73f3fa05..9ce98d6f 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -559,6 +559,68 @@ class ForwardAggregateCache(SQLModel, table=True):
     created_at: datetime
 
 
+# --- ops-hardening iter-13 (J-06) index-series ingest-time serving cache -------------------------
+class IndexSeriesCache(SQLModel, table=True):
+    """A STANDALONE, create_all-managed cache of the derived J-44 major-indexes normalized-% display
+    series (`app.engine.indexes.compute_index_series`), served on `GET /api/indexes`'s SINGLE
+    unparameterized default hot key (ops-hardening iter-13, J-06) — the request `PhaseCrossViewCard`
+    (`/`) and `IndexVendorPanel` (`/data`) both issue unparameterized on mount.
+
+    Like `EventStudyCache` / `MarketPhaseCache` / `ForwardAggregateCache`, this is EXPLICITLY NOT a
+    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
+    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
+    state: it stores the SERIALIZED `compute_index_series(...)` payload keyed by the request identity
+    plus a dataset-version stamp, so a read serves the stored payload instead of re-deriving it (No
+    recompute in the read path). The cached figures are BYTE-IDENTICAL to a fresh compute — a cache of
+    the deterministic read-only derivation, never a second computation.
+
+    WHY: `compute_index_series(..., full=True)` hydrates each `index_chart.symbols` ETF's FULL stored
+    price history via `bars_through_latest` on EVERY request — measured live (`reports/perf-budgets.md`,
+    iter-11/iter-12): 2138.7-2257.7ms for one request against its committed <=1.5s budget — the
+    confirmed J-06 violation this cache fixes.
+
+    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
+    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
+    existing table gains a column.
+
+    CACHE KEY: `(range_key, full, dataset_version)`:
+      - `range_key` + `full` are the request identity — this cache ONLY ever stores the SINGLE
+        unparameterized default hot key (`range_key=cfg.index_chart.default_range`, `full=True`); every
+        other range/as-of combination stays on the existing lazy, uncached `compute_index_series` path
+        (the "cannot be precomputed — user-parameterized" carve-out).
+      - `dataset_version` is a NARROW stamp scoped ONLY to the inputs this series actually reads — the
+        configured `index_chart.symbols`' stored bars (`max(date)` + `count(*)`, filtered to those few
+        symbols, a bounded indexed read) — deliberately NOT the broad `research._dataset_version` (which
+        folds in the `forward_returns` row count and would invalidate on unrelated ingest activity that
+        never touches an index symbol's bars), mirroring `_membership_dataset_version`'s own narrow-stamp
+        precedent. A read computes the CURRENT stamp and looks up THIS exact key; a stale row keyed to an
+        older stamp is never hit (and is pruned on write), so the cache can NEVER serve a stale figure —
+        it refreshes the moment any configured index symbol gains a new bar, anywhere.
+
+    The echoed `asof_date` field is RE-DERIVED at read time (never trusted from the stored payload): for
+    this specific hot key (`range_key="all"`, i.e. `days=None`), `compute_index_series`'s own series
+    computation does not depend on the resolved as-of at all (`bars_through_latest` ignores it, and
+    `start` is `None` for the all-history preset) — the ONLY as-of-dependent part of the response is the
+    echoed `asof_date`. Re-deriving it at read time (rather than baking a stale one into the stored
+    payload) avoids an unnecessary correctness trap on a cache HIT (goal.md iter-13's own technical note).
+
+    `payload_json` is the serialized `series`/`range`/`ranges` (the `asof_date` field it may also carry
+    is overwritten at read time, never trusted from storage). Unique on the composite key so a write is
+    an idempotent upsert."""
+
+    __tablename__ = "index_series_cache"
+    __table_args__ = (
+        UniqueConstraint("range_key", "full", "dataset_version", name="uq_index_series_cache_key"),
+    )
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    range_key: str = Field(index=True)
+    full: bool
+    dataset_version: str  # narrow stamp: max(date)+count(*) over index_chart.symbols' stored bars
+    payload_json: str  # the serialized compute_index_series(...) payload (asof_date re-derived at read)
+    created_at: datetime
+
+
 class MacroSeries(SQLModel, table=True):
     """A STANDALONE, create_all-managed table of optional FRED macro-feed observations (iter-32, J-92).
 
diff --git a/apps/backend/tests/test_api_indexes.py b/apps/backend/tests/test_api_indexes.py
index 3be60260..be949c64 100644
--- a/apps/backend/tests/test_api_indexes.py
+++ b/apps/backend/tests/test_api_indexes.py
@@ -10,14 +10,16 @@ Served-from-storage read paths over the real committed seed:
 from __future__ import annotations
 
 from fastapi.testclient import TestClient
-from sqlmodel import Session
+from sqlmodel import Session, select
 
 import main
 from app.config import load_config
+from app.engine import indexes as indexes_module
 from app.engine.indexes import compute_index_series
 from app.engine.prices import latest_data_date
 from app.engine.regime_history import get_regime_history
 from app.engine.scanner import resolve_as_of_date
+from app.models import IndexSeriesCache
 
 
 def _earliest_and_latest_run_dates(session):
@@ -223,3 +225,75 @@ def test_api_regime_history_full_param_serves_through_latest(loaded_engine):
     # value identity on the overlapping <= D range (verbatim stored values, no recompute)
     overlap = [p for p in full["points"] if p["date"] <= clamped["asof_date"]]
     assert overlap == clamped["points"]
+
+
+# --- ops-hardening iter-13 (J-06): GET /api/indexes' SINGLE unparameterized default hot key
+# (no/default range, full=True, no as_of) is served from IndexSeriesCache; every other combination
+# stays on the pre-existing, unchanged, uncached compute_index_series path. -------------------------
+
+
+def test_api_indexes_hot_key_full_true_served_from_cache_and_matches_engine(loaded_engine):
+    """The hot key is byte-identical to a fresh, direct `compute_index_series` call on the same DB
+    state (AG-3), and persists exactly one `IndexSeriesCache` row for the current dataset-version key."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        expected = compute_index_series(
+            session, as_of=None, range_key=cfg.index_chart.default_range, config=cfg, full=True
+        )
+    with TestClient(main.app) as client:
+        resp = client.get("/api/indexes", params={"full": "true"})
+    assert resp.status_code == 200
+    assert resp.json() == expected
+
+    with Session(loaded_engine) as session:
+        rows = session.exec(
+            select(IndexSeriesCache).where(
+                IndexSeriesCache.range_key == cfg.index_chart.default_range,
+                IndexSeriesCache.full == True,  # noqa: E712
+            )
+        ).all()
+    assert len(rows) == 1
+
+
+def test_api_indexes_hot_key_second_request_hits_cache_without_recompute(loaded_engine, monkeypatch):
+    with TestClient(main.app) as client:
+        first = client.get("/api/indexes", params={"full": "true"}).json()
+
+    calls = {"n": 0}
+    real = indexes_module.compute_index_series
+
+    def _counting(*args, **kwargs):
+        calls["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(indexes_module, "compute_index_series", _counting)
+    with TestClient(main.app) as client:
+        second = client.get("/api/indexes", params={"full": "true"}).json()
+    assert calls["n"] == 0, "the second hot-key request must serve from IndexSeriesCache, not recompute"
+    assert second["series"] == first["series"]
+    assert second["range"] == first["range"]
+    assert second["ranges"] == first["ranges"]
+
+
+def test_api_indexes_non_hot_key_bypasses_cache_and_stays_byte_identical(loaded_engine):
+    """An explicit non-default range OR an explicit historical as_of never touches `IndexSeriesCache` --
+    byte-identical to the unchanged, uncached `compute_index_series` output for the same inputs (TC-6),
+    and neither request writes a new cache row."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        earliest, _latest = _earliest_and_latest_run_dates(session)
+        d = earliest.isoformat()
+        expected_range = compute_index_series(session, as_of=None, range_key="3M", config=cfg, full=True)
+        expected_asof = compute_index_series(
+            session, as_of=d, range_key=cfg.index_chart.default_range, config=cfg, full=True
+        )
+        rows_before = session.exec(select(IndexSeriesCache)).all()
+    with TestClient(main.app) as client:
+        by_range = client.get("/api/indexes", params={"range": "3M", "full": "true"}).json()
+        by_asof = client.get("/api/indexes", params={"as_of": d, "full": "true"}).json()
+    assert by_range == expected_range
+    assert by_asof == expected_asof
+
+    with Session(loaded_engine) as session:
+        rows_after = session.exec(select(IndexSeriesCache)).all()
+    assert len(rows_after) == len(rows_before)  # neither non-hot-key request wrote a cache row
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 40fabd10..08caa034 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -31,7 +31,7 @@ from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
 from app.engine import data_manager
-from app.engine import forward_testing, market_phase, scanner
+from app.engine import forward_testing, indexes, market_phase, scanner
 from app.engine.data_manager import (
     JobProgress,
     _chunk_plan,
@@ -74,6 +74,7 @@ from app.models import (
     ForwardAggregateCache,
     ForwardReturn,
     ImportCheckpoint,
+    IndexSeriesCache,
     ScannerResult,
     ScannerRun,
     SectorScoreRow,
@@ -1047,7 +1048,9 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
     `coverage_snapshot` row for the current stamp and reports every category this fixture's data supports
     as refreshed: `latest_snapshot` (this run created a snapshot), `coverage` + `membership_timeline` (one
     compute warms both), `market_phase` (the new date), `forward_aggregates` (ops-hardening iter-5: the
-    current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key)."""
+    current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key),
+    `index_series` (ops-hardening iter-13: the fixture's own `SPY` bar is one of `index_chart.symbols`, so
+    the hot-key warm has real bars to compute from)."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     with Session(engine) as session:
@@ -1056,7 +1059,7 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
     assert set(refreshed) == {
         "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
-        "research_hot_keys",
+        "research_hot_keys", "index_series",
     }
     with Session(engine) as session:
         rows = session.exec(select(CoverageSnapshot)).all()
@@ -1129,6 +1132,76 @@ def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finaliz
     assert stored == fresh
 
 
+# ==================================================================================================
+# ops-hardening iter-13 (J-06, aggregation candidate #7): the finalize hook's NEW index-series warm --
+# mirrors the `research_hot_keys`/`forward_aggregates` proofs above, for the SINGLE unparameterized
+# default hot key `GET /api/indexes` serves from `IndexSeriesCache`.
+# ==================================================================================================
+def test_finalize_hook_warms_index_series_hot_key(finalize_hook_engine):
+    """A finalize hook call persists exactly one `IndexSeriesCache` row for the current hot key and
+    reports "index_series" as refreshed — the fixture's own SPY bar is a configured `index_chart`
+    symbol, so the warm step has real bars to compute from."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="index-series-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "index_series" in refreshed
+    with Session(engine) as session:
+        rows = session.exec(select(IndexSeriesCache)).all()
+    assert len(rows) == 1
+    assert rows[0].range_key == cfg.index_chart.default_range
+    assert rows[0].full is True
+
+
+def test_finalize_hook_index_series_second_run_hit_not_reported_as_refreshed(finalize_hook_engine):
+    """Honesty gate (TC-5) — a SECOND finalize hook call with no intervening ingest to any configured
+    index symbol is a genuine cache HIT (nothing new persisted this run): "index_series" is honestly
+    ABSENT the second time, mirroring the "was skipped" omission every other warm category follows."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog1 = JobProgress(job_id="index-series-first", kind="backfill", start=d, end=d)
+        prog1.new_snapshot_dates = [d]
+        first = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
+    assert "index_series" in first
+
+    with Session(engine) as session:
+        prog2 = JobProgress(job_id="index-series-second", kind="backfill", start=d, end=d)
+        prog2.new_snapshot_dates = [d]
+        second = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
+    assert "index_series" not in second  # a genuine HIT — nothing new persisted this run
+    with Session(engine) as session:
+        rows = session.exec(select(IndexSeriesCache)).all()
+    assert len(rows) == 1  # still exactly one row — the second run never wrote a duplicate
+
+
+def test_finalize_hook_index_series_memory_error_isolated_and_not_reported(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-7 — a `MemoryError` raised while warming the index-series cache is isolated to that one warm
+    step: it never flips the ingest job's own status (this function never raises), the OTHER aggregates
+    (`coverage`/`membership_timeline`/`market_phase`/`forward_aggregates`/`research_hot_keys`) still
+    refresh normally, and "index_series" is honestly absent (never fabricated)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise MemoryError("forced index-series memory pressure")
+
+    monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="index-series-oom-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert "index_series" not in refreshed
+    assert {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys",
+    } <= set(refreshed)
+
+
 def test_finalize_hook_market_phase_computed_exactly_once_not_on_subsequent_read(
     finalize_hook_engine, monkeypatch
 ):
@@ -1206,6 +1279,7 @@ def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_eng
     monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
     monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _boom)
     monkeypatch.setattr(data_manager, "event_study_cached", _boom)
+    monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
         prog.new_snapshot_dates = [d]
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index 1162db90..79975b79 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -12,18 +12,24 @@ Covers the anti-goal-bearing behaviors of `app.engine.indexes.compute_index_seri
 from __future__ import annotations
 
 import json
-from datetime import date, timedelta
+from datetime import date, datetime, timedelta
 from pathlib import Path
 
 import pytest
 import yaml
 from sqlalchemy import insert
-from sqlmodel import Session
+from sqlmodel import Session, select
 
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
-from app.engine.indexes import UnknownRangeError, compute_index_series
-from app.models import DailyPrice
+from app.engine import indexes as indexes_module
+from app.engine.indexes import (
+    UnknownRangeError,
+    compute_index_series,
+    index_series_cached_with_status,
+    index_series_dataset_version,
+)
+from app.models import DailyPrice, IndexSeriesCache, ScannerRun
 
 # A synthetic config whose index_chart lists SPY, QQQ, and DIA (DIA intentionally bar-less in the DB so
 # the omission path is exercised) with three range presets including an all-history preset.
@@ -614,3 +620,147 @@ def test_missing_seed_meta_yields_null_vendor_and_first(tmp_path):
     spy = result["series"][0]
     assert spy["vendor"] is None
     assert spy["first"] is None
+
+
+# --- ops-hardening iter-13 (J-06): ingest-time hot-key serving cache ---------------------------------
+# `index_series_cached_with_status` serves the SINGLE unparameterized default hot key
+# (range_key=cfg.index_chart.default_range, full=True) from `IndexSeriesCache`: MISS computes via the
+# UNCHANGED `compute_index_series` and persists; HIT deserializes with zero recompute; the echoed
+# `asof_date` is re-derived at read time (never baked stale into the stored payload, per goal.md's own
+# technical note); `index_series_dataset_version` is scoped ONLY to `index_chart.symbols`' stored bars.
+
+
+def test_index_series_cached_miss_computes_persists_and_matches_engine_output(tmp_path):
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0, 102.0])
+        _insert_bars(session, "QQQ", [50.0, 51.0, 52.0])
+        session.commit()
+        payload, persisted = index_series_cached_with_status(session, cfg)
+        expected = compute_index_series(
+            session, as_of=None, range_key=cfg.index_chart.default_range, config=cfg, full=True
+        )
+    assert persisted is True  # a genuine MISS -> computed and persisted this call
+    assert payload == expected  # byte-identical to the uncached call on the same DB state (TC-3)
+
+    with Session(engine) as session:
+        rows = session.exec(select(IndexSeriesCache)).all()
+    assert len(rows) == 1
+    assert rows[0].range_key == cfg.index_chart.default_range
+    assert rows[0].full is True
+
+
+def test_index_series_cached_hit_serves_without_recompute(tmp_path, monkeypatch):
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0])
+        session.commit()
+        index_series_cached_with_status(session, cfg)  # warm (MISS)
+
+    calls = {"n": 0}
+    real = indexes_module.compute_index_series
+
+    def _counting(*args, **kwargs):
+        calls["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(indexes_module, "compute_index_series", _counting)
+    with Session(engine) as session:
+        payload, persisted = index_series_cached_with_status(session, cfg)
+        expected = compute_index_series(
+            session, as_of=None, range_key=cfg.index_chart.default_range, config=cfg, full=True
+        )
+    assert persisted is False  # a genuine HIT -> nothing new persisted
+    assert calls["n"] == 0, "a cache HIT must never call compute_index_series"
+    assert payload["series"] == expected["series"]
+    assert payload["range"] == expected["range"]
+    assert payload["ranges"] == expected["ranges"]
+
+
+def test_index_series_cached_invalidates_after_new_bar_for_configured_symbol(tmp_path):
+    """TC-4-shaped unit proof: a new bar for a configured `index_chart` symbol changes the narrow
+    dataset-version stamp, so the next hot-key request is a genuine MISS whose series includes the new
+    bar's date (never a stale pre-ingest snapshot)."""
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0])
+        session.commit()
+        first, first_persisted = index_series_cached_with_status(session, cfg)
+    assert first_persisted is True
+
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [103.0], start=_BASE + timedelta(days=5))
+        session.commit()
+        second, second_persisted = index_series_cached_with_status(session, cfg)
+    assert second_persisted is True  # the new bar bumped the stamp -> a genuine second MISS
+
+    spy_first = next(s for s in first["series"] if s["symbol"] == "SPY")
+    spy_second = next(s for s in second["series"] if s["symbol"] == "SPY")
+    assert len(spy_second["points"]) > len(spy_first["points"])
+    assert spy_second["points"][-1]["date"] == (_BASE + timedelta(days=5)).isoformat()
+
+    with Session(engine) as session:
+        # the stale (older-dataset_version) row is pruned on write -- exactly one row survives.
+        rows = session.exec(select(IndexSeriesCache)).all()
+    assert len(rows) == 1
+
+
+def test_index_series_cached_hit_re_derives_current_asof_not_stale(tmp_path):
+    """Technical note (goal.md iter-13): on a HIT, the echoed `asof_date` is RE-DERIVED at read time,
+    never baked into the stored payload -- a later change that shifts the resolved as-of (a NEW
+    `ScannerRun` landing, with no change to any `index_chart` symbol's bars) is reflected honestly even
+    though the narrow dataset-version stamp (bar-scoped only) is unchanged, so this is still a HIT."""
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0])
+        session.commit()
+        first, first_persisted = index_series_cached_with_status(session, cfg)
+    assert first_persisted is True
+
+    with Session(engine) as session:
+        session.add(ScannerRun(
+            asof_date=_BASE + timedelta(days=10), created_at=datetime(2026, 1, 11), provider="seed",
+            benchmark="SPY", regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+        second, second_persisted = index_series_cached_with_status(session, cfg)
+    assert second_persisted is False  # the index-scoped stamp is untouched by a new ScannerRun -> HIT
+    assert second["asof_date"] == (_BASE + timedelta(days=10)).isoformat()
+    assert second["asof_date"] != first["asof_date"]
+    # everything else is served verbatim from the SAME stored row (unchanged)
+    assert second["series"] == first["series"]
+    assert second["range"] == first["range"]
+
+
+def test_index_series_dataset_version_changes_on_new_bar_for_configured_symbol(tmp_path):
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0])
+        session.commit()
+        before = index_series_dataset_version(session, cfg)
+        _insert_bars(session, "SPY", [103.0], start=_BASE + timedelta(days=5))
+        session.commit()
+        after = index_series_dataset_version(session, cfg)
+    assert before != after
+
+
+def test_index_series_dataset_version_unaffected_by_unrelated_symbol(tmp_path):
+    """Narrow scoping (mirrors `research._membership_dataset_version`'s own narrow-stamp precedent): a
+    bar for a symbol NOT in `index_chart.symbols` (e.g. a scored universe stock) never bumps this
+    cache's stamp -- an ingest that never touches an index symbol must not invalidate it."""
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0])
+        session.commit()
+        before = index_series_dataset_version(session, cfg)
+        _insert_bars(session, "AAA", [10.0, 11.0])  # AAA is not in index_chart.symbols
+        session.commit()
+        after = index_series_dataset_version(session, cfg)
+    assert before == after
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 71 +++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |  6 ++
 runs/goal-session-ops-hardening/trace/.next-step  |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |  3 +
 4 files changed, 81 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
