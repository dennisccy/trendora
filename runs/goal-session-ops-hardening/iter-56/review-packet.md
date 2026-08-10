# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index f37bbb8e..51c2df27 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -160,8 +160,17 @@ def data_availability(session: Session = Depends(get_session)) -> dict:
     derived over the SAME stored bars + stored runs `compute_coverage` reads (never a second derivation of
     a coverage figure, never a canonical-value recompute). An empty / bars-less DB returns an empty-but-
     valid payload (`cells: []`, `total_symbols: 0`) — no fabricated cells, no 500. The `/api/data` overview
-    and every existing data endpoint are byte-unchanged; this is one additive read-only route."""
-    return data_manager.compute_availability(session, get_config())
+    and every existing data endpoint are byte-unchanged; this is one additive read-only route.
+
+    ops-hardening iter-56 (J-06 closure): served ONLY from the persisted `AvailabilityCache` row for the
+    current dataset-version stamp — never a live `compute_availability` call on this request path (the
+    unbounded, uncached full-history `GROUP BY daily_prices.date` scan that measured 15.1-21.2s live
+    against the committed <=1.5s budget, `reports/perf-budgets.md` Addendum 18/20). A genuinely missing
+    row serves the honest not-yet-computed empty payload — never a 500, never a fabricated cell. The row
+    is written by the ingest finalize hook (`app.engine.data_manager._refresh_ingest_aggregates`).
+    `compute_availability` itself is UNCHANGED and still used directly by that finalize hook / tests that
+    want a genuine live compute."""
+    return data_manager.availability_from_storage(session, get_config())
 
 
 @router.post("/data/jobs")
diff --git a/apps/backend/app/api/runs.py b/apps/backend/app/api/runs.py
index f2da2772..249a8bbf 100644
--- a/apps/backend/app/api/runs.py
+++ b/apps/backend/app/api/runs.py
@@ -25,15 +25,27 @@ router = APIRouter(tags=["runs"])
 @router.get("/runs")
 def runs(session: Session = Depends(get_session)) -> dict:
     """List persisted runs, descending by as-of date, each with its regime label/score, stored
-    candidate counts, and stock count — so the Risk-Off row is identifiable and the history is dated."""
+    candidate counts, and stock count — so the Risk-Off row is identifiable and the history is dated.
+
+    ops-hardening iter-56 (J-06 closure): `n_stocks` for EVERY run is read from ONE grouped aggregate
+    query (`GROUP BY ScannerResult.run_id`) instead of one `COUNT` query issued PER stored run inside
+    the loop — the confirmed N+1 pattern this iteration's live profiling measured issuing one query per
+    of the DB's 2,937 `scanner_runs` rows (6.8-10.7s against the committed <=1.5s budget,
+    `reports/perf-budgets.md` Addendum 18/20). Same endpoint, same response shape, byte-identical
+    `n_stocks` per run — no second producer; a run with zero stored results is honestly `0` (absent from
+    the grouped result, defaulted below), exactly as the old per-run `COUNT` returned `0` for it."""
     if latest_data_date(session) is None:
         raise HTTPException(status_code=503, detail="no price data available")
     run_rows = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date.desc())).all()
+    counts_by_run_id = dict(
+        session.exec(
+            select(ScannerResult.run_id, func.count())
+            .select_from(ScannerResult)
+            .group_by(ScannerResult.run_id)
+        ).all()
+    )
     out = []
     for run in run_rows:
-        n_stocks = session.scalar(
-            select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run.id)
-        )
         out.append(
             {
                 "run_id": run.id,
@@ -41,7 +53,7 @@ def runs(session: Session = Depends(get_session)) -> dict:
                 "created_at": run.created_at.isoformat(),
                 "regime": {"label": run.regime_label, "score": run.regime_score},
                 "candidate_counts": json.loads(run.candidate_counts_json),
-                "n_stocks": int(n_stocks or 0),
+                "n_stocks": int(counts_by_run_id.get(run.id, 0) or 0),
             }
         )
     return {"runs": out}
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index cb990e76..5126346a 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -76,6 +76,7 @@ from app.engine.universe_screen import (
     screen_reasons,
 )
 from app.models import (
+    AvailabilityCache,
     CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
@@ -1605,6 +1606,93 @@ def compute_availability(session: Session, config: Optional[Config] = None) -> d
     }
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-56 (J-06 closure): `AvailabilityCache` ingest-time serving cache for
+# `compute_availability` — replaces the unbounded, uncached full-history `GROUP BY daily_prices.date`
+# scan `GET /api/data/availability` used to run on EVERY request (measured 15.1-21.2s live against the
+# <=1.5s budget on the grown 8.37 GB dev DB, `reports/perf-budgets.md` Addendum 18/20). Mirrors the
+# `index_series_cached_with_status`/`membership_timeline_cached` convention: `compute_availability`
+# itself is UNCHANGED (same producer, same signature) — this is a pure serving/persistence wrapper.
+# --------------------------------------------------------------------------------------------------
+def availability_cached_with_status(
+    session: Session, config: Optional[Config] = None,
+) -> tuple[dict, bool]:
+    """Serve `compute_availability`'s payload from `AvailabilityCache`, returning `(payload,
+    persisted_this_call)` — mirrors `indexes.index_series_cached_with_status`'s honesty-gate contract
+    exactly (the SAME pattern the ingest finalize hook's `aggregates_refreshed` list already reads for
+    every other single-key hot-cache category: `index_series`, `factor_lab_all`).
+
+    On a HIT for the current `_membership_dataset_version` stamp (the SAME narrow stamp
+    `CoverageSnapshot`/`MembershipTimelineCache` already key on — `compute_availability` reads ONLY the
+    stored bars manifest + the `ScannerRun` snapshot set, exactly what that stamp encodes), deserialize
+    the stored payload (NO recompute) and return `persisted_this_call=False`. On a MISS, compute ONCE
+    via the UNCHANGED `compute_availability` (the SOLE producer — this function is a pure serving/
+    persistence wrapper, never a second derivation), persist it under the current stamp, prune any
+    stale rows (any older `dataset_version` — this cache holds exactly one row at a time, mirroring
+    `MembershipTimelineCache`'s single-row-per-dataset-version convention, since `compute_availability`
+    has no as-of/range parameter to key on), and return `persisted_this_call=True`. The returned
+    payload is BYTE-IDENTICAL to `compute_availability(...)` for the same DB state (No recompute in the
+    read path)."""
+    cfg = config or get_config()
+    version = _membership_dataset_version(session, cfg)
+
+    hit = session.exec(
+        select(AvailabilityCache).where(AvailabilityCache.dataset_version == version)
+    ).first()
+    if hit is not None:
+        return json.loads(hit.payload_json), False
+
+    # MISS — compute once (the SOLE producer, unchanged) and persist.
+    payload = compute_availability(session, cfg)
+
+    # prune stale rows (any older dataset_version) so the cache table does not grow unbounded as the
+    # dataset matures; the current-version row is then inserted (idempotent upsert on the unique key).
+    stale = session.exec(
+        select(AvailabilityCache).where(AvailabilityCache.dataset_version != version)
+    ).all()
+    for row in stale:
+        session.delete(row)
+
+    session.add(AvailabilityCache(
+        dataset_version=version, payload_json=json.dumps(payload),
+        created_at=datetime.now(timezone.utc),
+    ))
+    try:
+        session.commit()
+    except Exception:  # a concurrent writer raced us to the same key — best-effort, not a source of truth
+        session.rollback()
+    return payload, True
+
+
+def _availability_not_yet_computed_payload() -> dict:
+    """The honest 'not yet computed' availability sentinel `availability_from_storage` serves when no
+    `AvailabilityCache` row exists yet for the current dataset_version (before the first ingest finalize
+    hook has run, or a warm the MemoryError-isolation convention skipped under memory pressure) —
+    mirrors `_coverage_not_yet_computed_payload`'s honesty convention. Issues ZERO database queries —
+    never the full-history `GROUP BY` scan `compute_availability` exists to avoid on this path (AG-8)."""
+    return {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+
+
+def availability_from_storage(session: Session, config: Optional[Config] = None) -> dict:
+    """`GET /api/data/availability`'s serving path — REPLACES the former request-path call straight to
+    `compute_availability` (an unbounded, uncached full-history `GROUP BY daily_prices.date` scan on
+    EVERY request — the confirmed J-06 latency source, `reports/perf-budgets.md` Addendum 18/20:
+    15.1-21.2s against the committed <=1.5s budget). Reads the persisted `AvailabilityCache` row for the
+    current `_membership_dataset_version` stamp; a genuinely missing row (no ingest has warmed it yet,
+    or a warm was skipped under memory pressure) serves the honest not-yet-computed empty payload —
+    NEVER a live full-table compute on this default request path (AG-8). `compute_availability` itself
+    is UNCHANGED and still used directly by the ingest finalize hook / tests that want a genuine live
+    compute."""
+    cfg = config or get_config()
+    version = _membership_dataset_version(session, cfg)
+    row = session.exec(
+        select(AvailabilityCache).where(AvailabilityCache.dataset_version == version)
+    ).first()
+    if row is not None:
+        return json.loads(row.payload_json)
+    return _availability_not_yet_computed_payload()
+
+
 def compute_capacity(session: Session, config: Optional[Config] = None) -> dict:
     """iter-24 fast-platform item K — the DB storage-footprint snapshot: on-disk file size + row counts
     for the three largest tables (`daily_prices` / `scanner_results` / `forward_returns`). PURE DB
@@ -2296,9 +2384,9 @@ class JobProgress:
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
     # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    # "drawdown_expectations", "index_series", "factor_lab_all"]` it actually refreshed — empty/default
-    # until the hook has actually run (never fabricated on an interrupted/failed row; gated in
-    # `_run_detail()` the SAME way `calendar_days` etc. already are).
+    # "drawdown_expectations", "index_series", "factor_lab_all", "availability_heatmap"]` it actually
+    # refreshed — empty/default until the hook has actually run (never fabricated on an
+    # interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc. already are).
     new_snapshot_dates: list[date_cls] = field(default_factory=list)
     aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
@@ -3970,8 +4058,9 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
     "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    "drawdown_expectations", "index_series", "factor_lab_all"]` ACTUALLY refreshed — never a fabricated
-    category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this module).
+    "drawdown_expectations", "index_series", "factor_lab_all", "availability_heatmap"]` ACTUALLY
+    refreshed — never a fabricated category (mirrors the `omitted`/`passers` honesty convention already
+    used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -4371,6 +4460,42 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 prog.job_id, "index_series_warm", time.monotonic() - _phase_t0,
             )
 
+            # ops-hardening iter-56 (J-06 closure): warm `AvailabilityCache`'s single dataset-version-
+            # keyed row for `GET /api/data/availability`'s per-trading-date heatmap (`compute_availability`
+            # — an unbounded, uncached full-history `GROUP BY daily_prices.date` scan on EVERY request,
+            # measured 15.1-21.2s live against the <=1.5s budget on the grown 8.37 GB dev DB,
+            # `reports/perf-budgets.md` Addendum 18/20). Mirrors `index_series_warm` immediately above:
+            # unconditional (not gated on `prog.new_snapshot_dates`), because the `_membership_dataset_
+            # version` stamp is GLOBAL — ANY ingest that lands a bar or a snapshot, anywhere, must
+            # invalidate it. A single-key warm (never a per-as-of sweep): `compute_availability` has no
+            # as-of parameter, so there is exactly one row to keep fresh, mirroring `MembershipTimelineCache`'s
+            # single-row convention. `availability_cached_with_status` lives in THIS SAME module (unlike
+            # `indexes.index_series_cached_with_status`), so no deferred import is needed to break a
+            # module-load cycle.
+            #
+            # iter-8 MemoryError-isolation convention: caught distinctly from the generic exception below,
+            # stops immediately (a single key, not a loop — nothing further to attempt) and calls
+            # `_release_process_memory()` before moving on to the next aggregate category.
+            # "availability_heatmap" is appended ONLY when this call actually persisted a new row this run
+            # (`persisted` is False on a cache HIT — an honest "was skipped" omission, never a fabricated
+            # refresh, mirroring `index_series_warm`'s own honesty gate above).
+            _phase_t0 = time.monotonic()
+            try:
+                _, availability_persisted = availability_cached_with_status(session, cfg)
+                if availability_persisted:
+                    refreshed.append("availability_heatmap")
+            except MemoryError as exc:
+                _log_isolation_failure(
+                    "ingest availability-heatmap warm aborted — memory pressure: %s", exc,
+                )
+                _release_process_memory()
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+                _log_isolation_failure("ingest availability-heatmap warm failed (non-fatal): %s", exc)
+            logger.info(
+                "J-05 finalize-tail phase timing: job=%s phase=%s elapsed=%.2fs",
+                prog.job_id, "availability_heatmap_warm", time.monotonic() - _phase_t0,
+            )
+
             # ops-hardening iter-51 (J-05/J-06/J-07): warm the Factor Lab's default all-history hot key
             # (`factor_lab_all_cached` -> `compute_factor_lab_all`, the SAME `EventStudyCache` sentinel
             # namespace `research_hot_keys_warm` above uses for the event-study default key) so
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 9ce98d6f..93b56deb 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -707,6 +707,56 @@ class MembershipTimelineCache(SQLModel, table=True):
     created_at: datetime
 
 
+# --- ops-hardening iter-56 (J-06) availability-heatmap ingest-time serving cache ------------------
+class AvailabilityCache(SQLModel, table=True):
+    """A STANDALONE, create_all-managed cache of the J-61 per-trading-date availability heatmap
+    (`app.engine.data_manager.compute_availability`), served on `GET /api/data/availability` (the
+    `/data` heatmap widget).
+
+    Like `IndexSeriesCache` / `MembershipTimelineCache` / `CoverageSnapshot`, this is EXPLICITLY NOT a
+    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
+    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
+    state: it stores the SERIALIZED `compute_availability(...)` payload keyed by a single
+    dataset-version stamp, so a read serves the stored payload instead of re-deriving it (No recompute
+    in the read path). The cached payload is BYTE-IDENTICAL to a fresh `compute_availability(...)`
+    compute — a cache of the deterministic read-only derivation, never a second computation.
+
+    WHY: `compute_availability` runs an unbounded, uncached `GROUP BY daily_prices.date` scan across
+    the FULL benchmark trading calendar on EVERY request — measured live (`reports/perf-budgets.md`
+    Addendum 18/20): 15.1-21.2s against the committed <=1.5s budget on the grown 8.37 GB dev DB, the
+    confirmed J-06 latency source this cache fixes (goal.md's aggregation candidate #7).
+
+    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
+    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
+    existing table gains a column.
+
+    CACHE KEY: `(dataset_version)`:
+      - `compute_availability` has NO as-of/range parameter (it always spans the WHOLE benchmark
+        trading calendar), so there is no as-of slot — exactly one row per dataset version, mirroring
+        `MembershipTimelineCache`'s single-row convention (never `IndexSeriesCache`'s multi-key shape,
+        which exists only because THAT function is parameterized by `range_key`/`full`).
+      - `dataset_version` reuses the SAME narrow `_membership_dataset_version` stamp (J-100)
+        `CoverageSnapshot`/`MembershipTimelineCache` already key on — the snapshot set + bars manifest
+        (`max(daily_prices.date)` + `count(*)`), exactly what `compute_availability` reads (ALL stored
+        bars for `symbols_with_bars`/`total_symbols`, plus the `ScannerRun.asof_date` set for
+        `snapshot_exists`). A read computes the CURRENT stamp and looks up THIS exact key; a stale row
+        keyed to an older stamp is never hit (and is pruned on write), so the cache can NEVER serve a
+        stale heatmap.
+
+    `payload_json` is the full serialized `total_symbols`/`trading_day_count`/`cells` payload. Unique
+    on `dataset_version` so a write is an idempotent upsert."""
+
+    __tablename__ = "availability_cache"
+    __table_args__ = (
+        UniqueConstraint("dataset_version", name="uq_availability_cache_key"),
+    )
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    dataset_version: str = Field(index=True)  # the SAME narrow stamp _membership_dataset_version produces
+    payload_json: str  # the serialized compute_availability(...) payload (byte-identical to a fresh compute)
+    created_at: datetime
+
+
 # --- ops-hardening iter-2 (J-05) coverage derived-aggregate snapshot (a PERFORMANCE cache, not a
 # snapshot) -----------------------------------------------------------------------------------
 class CoverageSnapshot(SQLModel, table=True):
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 157914a5..295b3ff0 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -49,7 +49,13 @@ def data_api_engine(tmp_path):
     has already been through an ingest, so it seeds that row here (via the SAME `refresh_coverage_snapshot`
     the real ingest finalize hook / boot warm-up safety net use — never a second derivation), keeping
     every existing coverage-shape assertion in this file reading the SAME live-equivalent numbers as
-    before this iteration."""
+    before this iteration.
+
+    ops-hardening iter-56 (J-06 closure): `GET /api/data/availability` is now served ONLY from the
+    persisted `AvailabilityCache` row (never a live `compute_availability` call on the request path) —
+    this fixture also warms that row here (via the SAME `availability_cached_with_status` the real
+    ingest finalize hook uses — never a second derivation), so `test_get_data_availability_shape` keeps
+    reading the SAME live-equivalent payload as before this iteration."""
     prev = db_module._engine
     engine = make_engine(f"sqlite:///{tmp_path / 'data_api.db'}")
     create_db_and_tables(engine)
@@ -59,6 +65,8 @@ def data_api_engine(tmp_path):
         session.commit()
     with Session(engine) as session:
         data_manager.refresh_coverage_snapshot(session, get_config())
+    with Session(engine) as session:
+        data_manager.availability_cached_with_status(session, get_config())
     db_module.set_engine(engine)
     yield engine
     db_module.set_engine(prev)
@@ -246,6 +254,24 @@ def test_get_data_availability_empty_db_is_graceful(tmp_path):
     assert payload == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
 
 
+def test_get_data_availability_no_warm_serves_honest_not_yet_computed(tmp_path):
+    """ops-hardening iter-56 (TC-8) — real bars/snapshot exist, but the ingest finalize hook's
+    availability-heatmap warm has never run (no `AvailabilityCache` row): the endpoint returns HTTP 200
+    with the honest not-yet-computed empty payload — NEVER a live `compute_availability` full-history
+    scan on this default request path (AG-8), even though a live compute here would produce non-empty
+    cells."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'avail_no_warm.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (date(2024, 1, 2), date(2024, 1, 3)):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    # deliberately NO data_manager.availability_cached_with_status(...) warm call here.
+    with Session(engine) as session:
+        payload = data_availability(session=session)
+    assert payload == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+
+
 def test_post_job_defaults_source_when_omitted(data_api_engine):
     """A job that omits `source` resolves the config `default_source` (J-17 fetch behavior preserved); the
     response echoes it (not secret) and carries NO key. A backfill job needs no network."""
diff --git a/apps/backend/tests/test_api_runs.py b/apps/backend/tests/test_api_runs.py
index 89ef0501..68dfdb14 100644
--- a/apps/backend/tests/test_api_runs.py
+++ b/apps/backend/tests/test_api_runs.py
@@ -8,16 +8,20 @@ run carries zero Actionable; unknown run -> 404; no price data -> 503.
 """
 from __future__ import annotations
 
+from datetime import date, datetime, timedelta
+
 import pytest
 from fastapi import HTTPException
 from fastapi.testclient import TestClient
-from sqlmodel import Session
+from sqlalchemy import event, func
+from sqlmodel import Session, select
 
 import main
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.prices import latest_data_date
 from app.engine.universe_screen import read_pool
+from app.models import DailyPrice, ScannerResult, ScannerRun
 
 _RUN_SUMMARY_FIELDS = {"run_id", "asof_date", "created_at", "regime", "candidate_counts", "n_stocks"}
 
@@ -118,3 +122,112 @@ def test_runs_endpoints_raise_503_when_no_price_data(tmp_path):
             with pytest.raises(HTTPException) as exc:
                 call()
             assert exc.value.status_code == 503
+
+
+# ==================================================================================================
+# ops-hardening iter-56 (J-06 closure) -- GET /api/runs's n_stocks N+1 fix. Live profiling against the
+# grown 8.37 GB dev DB (2,937 stored ScannerRun rows) confirmed one ScannerResult COUNT query issued
+# PER stored run inside a Python loop (see the dev handoff for the exact profiled query count) -- fixed
+# with a single grouped aggregate query. Same endpoint, same response shape, byte-identical n_stocks.
+#
+# `multi_run_engine` is a small hand-built DB (mirrors `test_data_manager.py`'s `coverage_engine`/
+# `finalize_hook_engine` style) — deliberately NOT the session-scoped `loaded_engine` (a full 30-year
+# committed-seed backfill+warm, far more setup cost than these query-shape/byte-identity proofs need).
+# ==================================================================================================
+@pytest.fixture()
+def multi_run_engine(tmp_path):
+    """THREE `ScannerRun` rows carrying 3/0/2 `ScannerResult` children respectively — deliberately
+    includes a ZERO-result run so the grouped query's "absent from GROUP BY" default path is exercised
+    by the SAME fixture every test in this section shares."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'multi_run.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+        for i, n_results in enumerate((3, 0, 2)):
+            run = ScannerRun(
+                asof_date=date(2024, 1, 2) + timedelta(days=i), created_at=datetime(2024, 1, 2 + i),
+                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Choppy",
+                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.commit()
+            session.refresh(run)
+            for j in range(n_results):
+                session.add(ScannerResult(
+                    run_id=run.id, ticker=f"T{i}{j}", name=f"T{i}{j} Corp", leadership_score=1.0,
+                    leadership_bucket="Leader", entry_quality_score=1.0, entry_quality_bucket="Good",
+                    risk_score=1.0, risk_bucket="Low", setup_status="Actionable", rank=j + 1,
+                    record_json="{}",
+                ))
+            session.commit()
+    return engine
+
+
+def test_api_runs_n_stocks_single_grouped_query_not_per_run(multi_run_engine):
+    """TC-2 -- the number of ScannerResult queries issued for ONE GET /api/runs request is a small
+    constant that does NOT scale with the number of stored runs (never one COUNT query per run)."""
+    from app.api.runs import runs as runs_route
+
+    statements: list[str] = []
+
+    def _capture(conn, cursor, statement, parameters, context, executemany):
+        if "scanner_results" in statement.lower():
+            statements.append(statement)
+
+    event.listen(multi_run_engine, "before_cursor_execute", _capture)
+    try:
+        with Session(multi_run_engine) as session:
+            n_runs = session.exec(select(func.count()).select_from(ScannerRun)).one()
+            if isinstance(n_runs, tuple):
+                n_runs = n_runs[0]
+            result = runs_route(session)
+    finally:
+        event.remove(multi_run_engine, "before_cursor_execute", _capture)
+
+    assert n_runs == 3  # sanity: this fixture's own 3 runs
+    assert len(result["runs"]) == n_runs
+    # exactly one grouped query, regardless of n_runs -- would be n_runs under the old per-run COUNT loop
+    assert len(statements) == 1, (
+        f"expected exactly 1 grouped ScannerResult query, saw {len(statements)} for {n_runs} stored runs"
+    )
+
+
+def test_api_runs_n_stocks_byte_identical_to_per_run_count(multi_run_engine):
+    """TC-3 -- every stored run's served n_stocks is byte-identical to a direct per-run COUNT (the
+    pre-fix per-run computation) -- the grouped-query rewrite changes only the query plan, never the
+    served value. Exercises the 3/0/2-result spread, including the ZERO-result run."""
+    from app.api.runs import runs as runs_route
+
+    with Session(multi_run_engine) as session:
+        result = runs_route(session)
+        run_ids = [r.id for r in session.exec(select(ScannerRun)).all()]
+        expected_by_run_id = {
+            rid: int(
+                session.scalar(
+                    select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == rid)
+                ) or 0
+            )
+            for rid in run_ids
+        }
+
+    assert result["runs"]  # sanity: non-empty
+    assert len(result["runs"]) == len(expected_by_run_id) == 3
+    assert sorted(expected_by_run_id.values()) == [0, 2, 3]  # the fixture's own 3/0/2 spread, sanity
+    for row in result["runs"]:
+        assert row["n_stocks"] == expected_by_run_id[row["run_id"]]
+
+
+def test_api_runs_n_stocks_zero_for_run_with_no_stored_results(multi_run_engine):
+    """A ScannerRun with zero child ScannerResult rows reads n_stocks == 0 -- the grouped query's honest
+    default for a run absent from the GROUP BY result, exactly what the old per-run COUNT() returned for
+    an empty run (never a KeyError, never a fabricated count)."""
+    from app.api.runs import runs as runs_route
+
+    with Session(multi_run_engine) as session:
+        result = runs_route(session)
+
+    zero_result_rows = [row for row in result["runs"] if row["n_stocks"] == 0]
+    assert len(zero_result_rows) == 1  # exactly the one 0-result run the fixture built
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 989ba815..97a07eec 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -69,6 +69,7 @@ from app.engine.forward_testing import compute_forward_aggregates
 from app.engine.ledger import append_entry
 from app.engine.scoring import score_stocks
 from app.models import (
+    AvailabilityCache,
     CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
@@ -341,6 +342,85 @@ def test_compute_availability_byte_identical_after_fetch_scope_widening(coverage
     }
 
 
+# ==================================================================================================
+# ops-hardening iter-56 (J-06 closure) — `availability_cached_with_status` / `availability_from_storage`,
+# the `AvailabilityCache` ingest-time serving cache for `compute_availability` (mirrors the
+# `index_series_cached_with_status`/`coverage_from_storage` proofs above).
+# ==================================================================================================
+def test_availability_cached_with_status_miss_computes_and_persists(coverage_engine):
+    """A cache MISS (no `AvailabilityCache` row yet) computes once via the unchanged `compute_availability`
+    (byte-identical), persists it, and reports `persisted_this_call=True`."""
+    engine, _spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        fresh = compute_availability(session, cfg)
+        payload, persisted = data_manager.availability_cached_with_status(session, cfg)
+    assert persisted is True
+    assert payload == fresh
+    with Session(engine) as session:
+        rows = session.exec(select(AvailabilityCache)).all()
+    assert len(rows) == 1
+
+
+def test_availability_cached_with_status_hit_returns_stored_payload_no_recompute(coverage_engine, monkeypatch):
+    """A cache HIT for the current dataset-version stamp returns the stored payload WITHOUT calling
+    `compute_availability` again (No recompute in the read path) and reports `persisted_this_call=False`."""
+    engine, _spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        first_payload, _ = data_manager.availability_cached_with_status(session, cfg)
+
+    def _boom(*_a, **_k):
+        raise AssertionError("a cache HIT must never call compute_availability again")
+
+    monkeypatch.setattr(data_manager, "compute_availability", _boom)
+    with Session(engine) as session:
+        second_payload, persisted = data_manager.availability_cached_with_status(session, cfg)
+    assert persisted is False
+    assert second_payload == first_payload
+
+
+def test_availability_from_storage_serves_persisted_row(coverage_engine):
+    """`availability_from_storage` (the `GET /api/data/availability` serving path) reads the persisted
+    row byte-identical to a fresh `compute_availability` call, once a warm has run."""
+    engine, _spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        fresh = compute_availability(session, cfg)
+        data_manager.availability_cached_with_status(session, cfg)  # warm it
+    with Session(engine) as session:
+        served = data_manager.availability_from_storage(session, cfg)
+    assert served == fresh
+
+
+def test_availability_from_storage_missing_row_serves_honest_not_yet_computed(coverage_engine, monkeypatch):
+    """TC-8 — a genuinely missing `AvailabilityCache` row (real bars present, but no warm has ever run)
+    serves the honest not-yet-computed empty payload — NEVER a live `compute_availability` call on this
+    default request path (AG-8), even though this fixture has real SPY/AAA bars that WOULD produce
+    non-empty cells if computed live."""
+    engine, _spy_days = coverage_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise AssertionError("a missing cache row must never trigger a live compute_availability call")
+
+    monkeypatch.setattr(data_manager, "compute_availability", _boom)
+    with Session(engine) as session:
+        served = data_manager.availability_from_storage(session, cfg)
+    assert served == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+
+
+def test_availability_from_storage_empty_db_matches_honest_fallback():
+    """A genuinely empty / bars-less DB (no cache row, no bars) serves the SAME honest empty payload —
+    coincidentally identical to `compute_availability`'s own empty-DB return, but served with ZERO
+    database queries via the fallback, never a live compute."""
+    engine = make_engine("sqlite:///:memory:")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        served = data_manager.availability_from_storage(session, load_config())
+    assert served == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+
+
 # ==================================================================================================
 # J-36 — per-symbol / per-universe-member coverage table (read-only descriptive metadata)
 # ==================================================================================================
@@ -1053,7 +1133,8 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
     current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key),
     `index_series` (ops-hardening iter-13: the fixture's own `SPY` bar is one of `index_chart.symbols`, so
     the hot-key warm has real bars to compute from), `factor_lab_all` (ops-hardening iter-51: the Factor
-    Lab's default all-history hot key)."""
+    Lab's default all-history hot key), `availability_heatmap` (ops-hardening iter-56: the SAME fixture
+    data gives the availability-heatmap warm real bars/snapshot to compute from)."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     with Session(engine) as session:
@@ -1062,7 +1143,7 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
     assert set(refreshed) == {
         "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
-        "research_hot_keys", "index_series", "factor_lab_all",
+        "research_hot_keys", "index_series", "factor_lab_all", "availability_heatmap",
     }
     with Session(engine) as session:
         rows = session.exec(select(CoverageSnapshot)).all()
@@ -1212,6 +1293,100 @@ def test_finalize_hook_index_series_memory_error_isolated_and_not_reported(
     } <= set(refreshed)
 
 
+# ==================================================================================================
+# ops-hardening iter-56 (J-06 closure): the finalize hook's NEW `availability_heatmap` warm — mirrors
+# the `index_series` proofs above for the SINGLE dataset-version-keyed `AvailabilityCache` row
+# `GET /api/data/availability`'s per-trading-date heatmap serves from (`compute_availability` has no
+# as-of/range parameter, so there is exactly one row to keep fresh, unlike `IndexSeriesCache`'s
+# multi-key shape).
+# ==================================================================================================
+def test_finalize_hook_warms_availability_heatmap(finalize_hook_engine):
+    """TC-5 — a finalize hook call persists exactly one `AvailabilityCache` row for the current
+    dataset-version stamp and reports "availability_heatmap" as refreshed — the fixture's own SPY bar
+    and stored snapshot give the warm real data to compute from."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="availability-heatmap-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "availability_heatmap" in refreshed
+    with Session(engine) as session:
+        rows = session.exec(select(AvailabilityCache)).all()
+        assert len(rows) == 1
+        assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)
+
+
+def test_finalize_hook_availability_heatmap_byte_identical_to_fresh_compute(finalize_hook_engine):
+    """TC-6 — the persisted payload is byte-identical (field-by-field) to a direct fresh
+    `compute_availability` call for the same session state (AG-3: storage is re-served, never
+    re-derived)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="availability-byte-identity-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    with Session(engine) as session:
+        row = session.exec(select(AvailabilityCache)).one()
+        stored = json.loads(row.payload_json)
+        fresh = data_manager.compute_availability(session, cfg)
+    assert stored == fresh
+
+
+def test_finalize_hook_availability_heatmap_second_run_hit_not_reported_as_refreshed(
+    finalize_hook_engine,
+):
+    """Honesty gate — a SECOND finalize hook call with no intervening ingest to any bar/snapshot is a
+    genuine cache HIT (nothing new persisted this run): "availability_heatmap" is honestly ABSENT the
+    second time, mirroring `index_series_warm`'s "was skipped" omission convention."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog1 = JobProgress(job_id="availability-heatmap-first", kind="backfill", start=d, end=d)
+        prog1.new_snapshot_dates = [d]
+        first = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
+    assert "availability_heatmap" in first
+
+    with Session(engine) as session:
+        prog2 = JobProgress(job_id="availability-heatmap-second", kind="backfill", start=d, end=d)
+        prog2.new_snapshot_dates = [d]
+        second = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
+    assert "availability_heatmap" not in second  # a genuine HIT — nothing new persisted this run
+    with Session(engine) as session:
+        rows = session.exec(select(AvailabilityCache)).all()
+    assert len(rows) == 1  # still exactly one row — the second run never wrote a duplicate
+
+
+def test_finalize_hook_availability_heatmap_memory_error_isolated_and_not_reported(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-9 — a `MemoryError` raised while warming the availability-heatmap cache is isolated to that
+    one warm step: it never flips the ingest job's own status (this function never raises), the OTHER
+    aggregates (`coverage`/`membership_timeline`/`market_phase`/`forward_aggregates`/`research_hot_keys`/
+    `index_series`) still refresh normally, no other finalize-tail item's own completeness flag is
+    altered, and "availability_heatmap" is honestly absent (never fabricated)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise MemoryError("forced availability-heatmap memory pressure")
+
+    monkeypatch.setattr(data_manager, "availability_cached_with_status", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="availability-heatmap-oom-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert "availability_heatmap" not in refreshed
+    assert {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys", "index_series",
+    } <= set(refreshed)
+    with Session(engine) as session:
+        rows = session.exec(select(AvailabilityCache)).all()
+    assert rows == []  # the aborted warm never persisted a row
+
+
 # ==================================================================================================
 # ops-hardening iter-51 (J-05/J-06/J-07): the finalize hook's NEW `factor_lab_all` warm — mirrors the
 # `research_hot_keys`/`index_series` proofs above for the SINGLE unparameterized default all-history hot
@@ -1466,6 +1641,7 @@ def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_eng
     monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
     monkeypatch.setattr(data_manager, "event_study_cached", _boom)
     monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
+    monkeypatch.setattr(data_manager, "availability_cached_with_status", _boom)
     monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 91 ++++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |  1 +
 .../journey-scripts/J-05.json                      | 13 ++--
 runs/goal-session-ops-hardening/state/blueprint.md |  4 +-
 .../state/drift-report.json                        |  2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |  7 ++
 runs/goal-session-ops-hardening/trace/.next-step   |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  1 +
 8 files changed, 111 insertions(+), 10 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
