# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 13. Shown in full: 13.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index 41e99748..1b29309a 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -32,7 +32,7 @@ introduced (previously visible only by reconstructing it from raw DB timestamps)
 from __future__ import annotations
 
 from fastapi import APIRouter, Depends
-from sqlalchemy import distinct, func, select
+from sqlalchemy import func, select, text
 from sqlmodel import Session
 
 from app.config import get_config
@@ -42,6 +42,37 @@ from app.models import DailyPrice
 
 router = APIRouter(tags=["health"])
 
+# ops-hardening iter-57 (J-06 closure): a plain `SELECT COUNT(DISTINCT symbol) FROM daily_prices` makes
+# SQLite do a full COVERING INDEX SCAN of every (symbol, date) row to compute the distinct count — live
+# profiling on the grown 8.37 GB dev DB (3.3M rows) measured this ALONE at 0.117-0.119s (`EXPLAIN QUERY
+# PLAN`: `SCAN daily_prices USING COVERING INDEX ...`), the confirmed majority of this endpoint's
+# 0.16-0.241s steady-state latency against the committed <=0.1s budget (`reports/perf-budgets.md`, new
+# dated addendum). `symbol` is the LEADING column of that same unique index, so a recursive-CTE "walk
+# the index for the next distinct value" query (the standard SQLite loose-index-scan idiom) makes SQLite
+# do ~591 indexed SEARCHes (one per distinct symbol) instead of a 3.3M-row scan — confirmed live:
+# `EXPLAIN QUERY PLAN` shows `SEARCH daily_prices USING COVERING INDEX ... (symbol>?)`, same exact
+# result (591), 0.001-0.003s (roughly 100x). This is a pure query-SHAPE change — still a fully live,
+# request-time count (no staleness introduced, no persisted/cached value, no response field/shape
+# change) — the SAME "keep it lazy/indexed, never precomputed-and-stale" convention this endpoint's
+# contract already commits to.
+_DISTINCT_SYMBOL_COUNT_SQL = text(
+    """
+    WITH RECURSIVE syms(sym) AS (
+        SELECT (SELECT MIN(symbol) FROM daily_prices)
+        UNION ALL
+        SELECT (SELECT MIN(symbol) FROM daily_prices WHERE symbol > sym) FROM syms WHERE sym IS NOT NULL
+    )
+    SELECT COUNT(*) FROM syms WHERE sym IS NOT NULL
+    """
+)
+
+
+def _distinct_symbol_count(session: Session) -> int:
+    """The distinct count of symbols with >= 1 stored `daily_prices` bar — byte-identical to
+    `SELECT COUNT(DISTINCT symbol) FROM daily_prices` for the SAME DB state, via the fast indexed-walk
+    query above instead of a full covering-index scan."""
+    return int(session.execute(_DISTINCT_SYMBOL_COUNT_SQL).scalar_one() or 0)
+
 
 @router.get("/health")
 def health(session: Session = Depends(get_session)) -> dict:
@@ -49,7 +80,7 @@ def health(session: Session = Depends(get_session)) -> dict:
     provider = cfg.provider
     try:
         latest = session.scalar(select(func.max(DailyPrice.date)))
-        symbol_count = int(session.scalar(select(func.count(distinct(DailyPrice.symbol)))) or 0)
+        symbol_count = _distinct_symbol_count(session)
         db_ok = True
     except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
         latest = None
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 5126346a..010a9c30 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1661,36 +1661,69 @@ def availability_cached_with_status(
         session.commit()
     except Exception:  # a concurrent writer raced us to the same key — best-effort, not a source of truth
         session.rollback()
+        # ops-hardening iter-57 (AG-3 honesty fix): a rolled-back commit did NOT durably persist —
+        # `persisted_this_call=True` here would be a false claim that fed the `aggregates_refreshed`
+        # list's "availability_heatmap" entry even though nothing was written. The freshly computed
+        # `payload` is still returned (byte-identical to `compute_availability`, still correct to serve
+        # THIS call), only the honesty flag changes.
+        return payload, False
     return payload, True
 
 
 def _availability_not_yet_computed_payload() -> dict:
-    """The honest 'not yet computed' availability sentinel `availability_from_storage` serves when no
-    `AvailabilityCache` row exists yet for the current dataset_version (before the first ingest finalize
-    hook has run, or a warm the MemoryError-isolation convention skipped under memory pressure) —
-    mirrors `_coverage_not_yet_computed_payload`'s honesty convention. Issues ZERO database queries —
-    never the full-history `GROUP BY` scan `compute_availability` exists to avoid on this path (AG-8)."""
-    return {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+    """The honest 'not yet computed' availability sentinel `availability_from_storage` serves when NO
+    `AvailabilityCache` row has EVER been persisted (before the first ingest finalize hook has ever run,
+    or a warm the MemoryError-isolation convention skipped under memory pressure on a DB with no prior
+    row) — mirrors `_coverage_not_yet_computed_payload`'s honesty convention. Issues ZERO database
+    queries — never the full-history `GROUP BY` scan `compute_availability` exists to avoid on this path
+    (AG-8). ops-hardening iter-57: carries the SAME two additive `stale`/`served_dataset_version` keys
+    `availability_from_storage` adds to every response shape — `stale: False` (there is no prior payload
+    to be stale relative to) and `served_dataset_version: None` (no stamp has ever been served)."""
+    return {
+        "total_symbols": 0, "trading_day_count": 0, "cells": [],
+        "stale": False, "served_dataset_version": None,
+    }
 
 
 def availability_from_storage(session: Session, config: Optional[Config] = None) -> dict:
     """`GET /api/data/availability`'s serving path — REPLACES the former request-path call straight to
     `compute_availability` (an unbounded, uncached full-history `GROUP BY daily_prices.date` scan on
     EVERY request — the confirmed J-06 latency source, `reports/perf-budgets.md` Addendum 18/20:
-    15.1-21.2s against the committed <=1.5s budget). Reads the persisted `AvailabilityCache` row for the
-    current `_membership_dataset_version` stamp; a genuinely missing row (no ingest has warmed it yet,
-    or a warm was skipped under memory pressure) serves the honest not-yet-computed empty payload —
-    NEVER a live full-table compute on this default request path (AG-8). `compute_availability` itself
-    is UNCHANGED and still used directly by the ingest finalize hook / tests that want a genuine live
-    compute."""
+    15.1-21.2s against the committed <=1.5s budget). `compute_availability` itself is UNCHANGED and
+    still used directly by the ingest finalize hook / tests that want a genuine live compute.
+
+    ops-hardening iter-57 (J-06 closure, this iteration's headline fix): the iter-56 MISS-fallback only
+    ever checked the row for the CURRENT `_membership_dataset_version` stamp, so ANY stamp mismatch
+    (true for the ENTIRE duration of a mid-flight ingest job — the stamp folds in `count(daily_prices)`,
+    which bumps on the job's FIRST committed bar, while the ONLY writer is the finalize-tail warm at the
+    job's END) served the not-yet-computed empty sentinel over a multi-million-row DB — a false "no
+    data" claim (AG-3/AG-8). `AvailabilityCache` is unique on `dataset_version` and pruned-on-write by
+    `availability_cached_with_status` (every MISS write deletes every OTHER-stamped row first), so it
+    holds AT MOST ONE row at any time — "the most recent persisted row" is simply "the row, if any",
+    with no need for a second ORDER BY/created_at tie-break.
+
+    Three cases, by row presence + stamp:
+      - NO row exists at all (no ingest has EVER completed a warm): the honest not-yet-computed empty
+        sentinel (`stale: False`, `served_dataset_version: None`) — UNCHANGED from iter-56, and the
+        ONLY case that payload is honest for (never conflated with the stale-serving case below).
+      - A row exists and its stamp MATCHES the current one (idle/warm, byte-identical to iter-56):
+        `stale: False`, `served_dataset_version` equal to the current (== the row's) stamp.
+      - A row exists but its stamp does NOT match the current one (a stamp mismatch — an ingest is
+        mid-flight and the finalize-tail warm has not yet re-run): serve THAT row's real
+        `cells`/`total_symbols`/`trading_day_count` (never empty) with `stale: True` and
+        `served_dataset_version` set to the row's OWN (prior, not current) stamp, so the UI can render
+        the real previous heatmap plus an honest "as of / updating" banner instead of a false "no data"
+        claim. Still ZERO recompute — the payload is the SAME stored JSON blob deserialized, never a
+        live `compute_availability` call on this default request path (AG-8)."""
     cfg = config or get_config()
     version = _membership_dataset_version(session, cfg)
-    row = session.exec(
-        select(AvailabilityCache).where(AvailabilityCache.dataset_version == version)
-    ).first()
-    if row is not None:
-        return json.loads(row.payload_json)
-    return _availability_not_yet_computed_payload()
+    row = session.exec(select(AvailabilityCache)).first()
+    if row is None:
+        return _availability_not_yet_computed_payload()
+    payload = json.loads(row.payload_json)
+    payload["stale"] = row.dataset_version != version
+    payload["served_dataset_version"] = row.dataset_version
+    return payload
 
 
 def compute_capacity(session: Session, config: Optional[Config] = None) -> dict:
diff --git a/apps/backend/app/engine/indexes.py b/apps/backend/app/engine/indexes.py
index a48ca395..4174deb3 100644
--- a/apps/backend/app/engine/indexes.py
+++ b/apps/backend/app/engine/indexes.py
@@ -278,6 +278,12 @@ def index_series_cached_with_status(
         session.commit()
     except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
         session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
+        # ops-hardening iter-57 (AG-3 honesty fix, mirrors the SAME fix on data_manager.py's sibling
+        # `availability_cached_with_status`): a rolled-back commit did NOT durably persist —
+        # `persisted_this_call=True` here would be a false claim feeding the `aggregates_refreshed`
+        # list's "index_series" entry even though nothing was written. `payload` is still returned
+        # (byte-identical to `compute_index_series`, still correct to serve THIS call).
+        return payload, False
     return payload, True
 
 
diff --git a/apps/backend/app/engine/indicators.py b/apps/backend/app/engine/indicators.py
index 7d988673..d2428f89 100644
--- a/apps/backend/app/engine/indicators.py
+++ b/apps/backend/app/engine/indicators.py
@@ -52,10 +52,22 @@ def sma_series(values: Sequence[float], period: int) -> list[Optional[float]]:
     `period` values ending at `i`, or NA (`None`) for the warm-up prefix with fewer than `period`
     prior values. Built by reusing `sma` over each prefix, so there is ONE MA definition and the
     invariant `sma_series(values, p)[-1] == sma(values, p)` holds by construction (single source:
-    the chart overlay, the invalidation level and the scoring MA components never disagree)."""
+    the chart overlay, the invalidation level and the scoring MA components never disagree).
+
+    ops-hardening iter-57 (J-06 closure): each call is bounded to AT MOST the last `period` values
+    (`values[max(0, i + 1 - period) : i + 1]`) instead of the full prefix (`values[: i + 1]`). `sma`
+    itself only ever reads its own trailing `period` values (`values[-period:]`), so passing it the
+    full ever-growing prefix on every one of `len(values)` calls was pure waste — an O(n) list COPY on
+    every iteration made the whole series O(n^2). Byte-identical output for every input (proven by a
+    dedicated regression test): the bounded slice's `[-period:]` inside `sma` is the SAME window
+    content either way, and the NA/warm-up length check (`len(...) < period`) triggers at the exact
+    same `i` in both forms. Confirmed live (`reports/perf-budgets.md`, dated addendum): the profiled
+    `GET /api/stocks/{ticker}/bars?through=latest` bottleneck (this function, called once per
+    configured `indicators.ma_periods` entry over the full as-of-bounded series) dropped from
+    ~0.178s to ~0.038s for AAPL's real 7,695-bar history across the 4 configured periods."""
     if period <= 0:
         raise ValueError(f"sma_series period must be positive, got {period}")
-    return [sma(values[: i + 1], period) for i in range(len(values))]
+    return [sma(values[max(0, i + 1 - period): i + 1], period) for i in range(len(values))]
 
 
 def rs_vs(series: Sequence[float], benchmark: Sequence[float], window: int) -> Optional[float]:
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 0e21c6d0..b9867692 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -709,15 +709,28 @@ def list_runs(session: Session) -> dict:
 
     NOTE: `/api/runs` keeps its read inline in the router (no engine function to delegate to), so this
     is the one tool that MIRRORS the router's stored-row read rather than calling a shared engine helper
-    — it still recomputes nothing (a plain SELECT over the immutable snapshot rows)."""
+    — it still recomputes nothing (a plain SELECT over the immutable snapshot rows).
+
+    ops-hardening iter-57 (coherence-auditor iter-56 advisory, closed as a low-risk rider): `n_stocks`
+    is now read from ONE grouped `GROUP BY ScannerResult.run_id` aggregate query, mirroring the SAME
+    fix `app.api.runs.runs` already applied in iter-56 — replacing the per-run `ScannerResult` COUNT
+    query that used to run once PER stored `ScannerRun` row (the exact N+1 pattern iter-56's live
+    profiling measured issuing one query per row; the coherence audit separately measured this tool's
+    own un-fixed copy at 6.8-10.7s on the live DB). Same tool, same response shape, byte-identical
+    `n_stocks` per run — a run with zero stored results is honestly `0` (absent from the grouped
+    result, defaulted below), exactly as the old per-run `COUNT()` returned for it."""
     if latest_data_date(session) is None:
         raise ValueError("no price data available")
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
@@ -725,7 +738,7 @@ def list_runs(session: Session) -> dict:
                 "created_at": run.created_at.isoformat(),
                 "regime": {"label": run.regime_label, "score": run.regime_score},
                 "candidate_counts": json.loads(run.candidate_counts_json),
-                "n_stocks": int(n_stocks or 0),
+                "n_stocks": int(counts_by_run_id.get(run.id, 0) or 0),
             }
         )
     return {"runs": out}
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 295b3ff0..5224c5ab 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -226,14 +226,21 @@ def test_get_data_availability_shape(data_api_engine):
     """J-61 — GET /api/data/availability returns the per-trading-date availability payload over the SAME
     bars `compute_coverage` reads. On the tiny fixture (two SPY days, no other symbols, no snapshots):
     two cells (one per trading day), each SPY-only (`symbols_with_bars == 1`) with `snapshot_exists`
-    false, and `total_symbols == 1` (== the coverage symbol_count). The `/api/data` overview is unchanged."""
+    false, and `total_symbols == 1` (== the coverage symbol_count). The `/api/data` overview is unchanged.
+
+    ops-hardening iter-57 (TC-3): the fixture warms the cache once with no DB mutation afterward, so the
+    stamp still matches — `stale: False` and `served_dataset_version` equal to the current stamp (the
+    two new additive iter-57 fields)."""
     with Session(data_api_engine) as session:
         payload = data_availability(session=session)
         overview = data_overview(session=session)
+        current_version = data_manager._membership_dataset_version(session, get_config())
 
-    assert set(payload) == {"total_symbols", "trading_day_count", "cells"}
+    assert set(payload) == {"total_symbols", "trading_day_count", "cells", "stale", "served_dataset_version"}
     assert payload["total_symbols"] == overview["coverage"]["symbol_count"] == 1
     assert payload["trading_day_count"] == overview["coverage"]["trading_day_count"] == 2
+    assert payload["stale"] is False
+    assert payload["served_dataset_version"] == current_version
     cells = payload["cells"]
     assert len(cells) == 2
     for c in cells:
@@ -246,20 +253,24 @@ def test_get_data_availability_shape(data_api_engine):
 
 def test_get_data_availability_empty_db_is_graceful(tmp_path):
     """J-61 — on an empty / bars-less DB the availability endpoint returns an empty-but-valid payload
-    (no 500, no fabricated cells), mirroring the honest empty coverage payload."""
+    (no 500, no fabricated cells), mirroring the honest empty coverage payload. TC-2: `stale: False`,
+    `served_dataset_version: None` — no `AvailabilityCache` row has EVER been persisted."""
     engine = make_engine(f"sqlite:///{tmp_path / 'avail_empty.db'}")
     create_db_and_tables(engine)
     with Session(engine) as session:
         payload = data_availability(session=session)
-    assert payload == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+    assert payload == {
+        "total_symbols": 0, "trading_day_count": 0, "cells": [],
+        "stale": False, "served_dataset_version": None,
+    }
 
 
 def test_get_data_availability_no_warm_serves_honest_not_yet_computed(tmp_path):
-    """ops-hardening iter-56 (TC-8) — real bars/snapshot exist, but the ingest finalize hook's
-    availability-heatmap warm has never run (no `AvailabilityCache` row): the endpoint returns HTTP 200
-    with the honest not-yet-computed empty payload — NEVER a live `compute_availability` full-history
-    scan on this default request path (AG-8), even though a live compute here would produce non-empty
-    cells."""
+    """ops-hardening iter-56 (TC-8) / iter-57 (TC-2) — real bars/snapshot exist, but the ingest finalize
+    hook's availability-heatmap warm has never run (no `AvailabilityCache` row EVER persisted): the
+    endpoint returns HTTP 200 with the honest not-yet-computed empty payload (`stale: False`,
+    `served_dataset_version: None`) — NEVER a live `compute_availability` full-history scan on this
+    default request path (AG-8), even though a live compute here would produce non-empty cells."""
     engine = make_engine(f"sqlite:///{tmp_path / 'avail_no_warm.db'}")
     create_db_and_tables(engine)
     with Session(engine) as session:
@@ -269,7 +280,37 @@ def test_get_data_availability_no_warm_serves_honest_not_yet_computed(tmp_path):
     # deliberately NO data_manager.availability_cached_with_status(...) warm call here.
     with Session(engine) as session:
         payload = data_availability(session=session)
-    assert payload == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+    assert payload == {
+        "total_symbols": 0, "trading_day_count": 0, "cells": [],
+        "stale": False, "served_dataset_version": None,
+    }
+
+
+def test_get_data_availability_stale_serves_prior_row_on_stamp_mismatch(tmp_path):
+    """ops-hardening iter-57 (TC-1, at the API layer) — a warm has already run (V1), then a new bar
+    lands WITHOUT the finalize-tail warm re-running (simulating a mid-flight ingest job's first
+    committed bar): the endpoint serves the PRIOR row's real, non-empty cells with `stale: True` and
+    `served_dataset_version` equal to the PRIOR (not current) stamp — never the not-yet-computed empty
+    sentinel while real data exists."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'avail_stale.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (date(2024, 1, 2), date(2024, 1, 3)):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    with Session(engine) as session:
+        data_manager.availability_cached_with_status(session, get_config())  # warm it (V1)
+        prior_version = data_manager._membership_dataset_version(session, get_config())
+    with Session(engine) as session:
+        # a new bar lands — bumps the stamp — but no re-warm runs (mid-flight ingest, finalize pending)
+        session.add(DailyPrice(symbol="AAA", date=date(2024, 1, 2), open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
+        session.commit()
+    with Session(engine) as session:
+        payload = data_availability(session=session)
+    assert payload["stale"] is True
+    assert payload["served_dataset_version"] == prior_version
+    assert payload["cells"] != []
+    assert payload["total_symbols"] == 1  # the PRIOR row's count (SPY only) — not the post-bar count
 
 
 def test_post_job_defaults_source_when_omitted(data_api_engine):
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 97a07eec..c0aada5d 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -380,24 +380,58 @@ def test_availability_cached_with_status_hit_returns_stored_payload_no_recompute
     assert second_payload == first_payload
 
 
+def test_availability_cached_with_status_rollback_reports_not_persisted(coverage_engine, monkeypatch):
+    """TC-10 — a forced `session.commit()` failure inside `availability_cached_with_status`'s MISS path
+    rolls back (the existing `except: session.rollback()` branch) and MUST report
+    `persisted_this_call=False` — never `True` for a write that did not durably persist (the AG-3
+    honesty gap this iteration closes on the existing `aggregates_refreshed` field). The freshly
+    computed payload is still returned (byte-identical to `compute_availability`), only the honesty flag
+    changes."""
+    engine, _spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        fresh = compute_availability(session, cfg)
+
+    with Session(engine) as session:
+        def _boom_commit():
+            raise RuntimeError("forced commit failure (TC-10 fault injection)")
+
+        monkeypatch.setattr(session, "commit", _boom_commit)
+        payload, persisted = data_manager.availability_cached_with_status(session, cfg)
+
+    assert persisted is False
+    assert payload == fresh
+    # nothing durably persisted — a fresh read finds no row
+    with Session(engine) as session:
+        rows = session.exec(select(AvailabilityCache)).all()
+    assert rows == []
+
+
 def test_availability_from_storage_serves_persisted_row(coverage_engine):
-    """`availability_from_storage` (the `GET /api/data/availability` serving path) reads the persisted
-    row byte-identical to a fresh `compute_availability` call, once a warm has run."""
+    """TC-3 — `availability_from_storage` (the `GET /api/data/availability` serving path) reads the
+    persisted row byte-identical to a fresh `compute_availability` call, once a warm has run, PLUS the
+    two new additive iter-57 fields: `stale: False` (the stored row's stamp matches the CURRENT
+    `_membership_dataset_version`) and `served_dataset_version` equal to that current stamp (regression
+    guard for the idle/matching-stamp case — the byte-identity contract predating this iteration is
+    unchanged for every pre-existing field)."""
     engine, _spy_days = coverage_engine
     cfg = load_config()
     with Session(engine) as session:
         fresh = compute_availability(session, cfg)
         data_manager.availability_cached_with_status(session, cfg)  # warm it
+        current_version = data_manager._membership_dataset_version(session, cfg)
     with Session(engine) as session:
         served = data_manager.availability_from_storage(session, cfg)
-    assert served == fresh
+    assert served == {**fresh, "stale": False, "served_dataset_version": current_version}
 
 
 def test_availability_from_storage_missing_row_serves_honest_not_yet_computed(coverage_engine, monkeypatch):
-    """TC-8 — a genuinely missing `AvailabilityCache` row (real bars present, but no warm has ever run)
-    serves the honest not-yet-computed empty payload — NEVER a live `compute_availability` call on this
-    default request path (AG-8), even though this fixture has real SPY/AAA bars that WOULD produce
-    non-empty cells if computed live."""
+    """TC-2 (TC-8 predecessor) — a genuinely missing `AvailabilityCache` row (real bars present, but no
+    warm has EVER run) serves the honest not-yet-computed empty payload — NEVER a live
+    `compute_availability` call on this default request path (AG-8), even though this fixture has real
+    SPY/AAA bars that WOULD produce non-empty cells if computed live. `stale` is `False` and
+    `served_dataset_version` is `None` — the empty sentinel is reserved strictly for "no row has ever
+    been persisted", not conflated with the mid-ingest stale-serving case."""
     engine, _spy_days = coverage_engine
     cfg = load_config()
 
@@ -407,18 +441,83 @@ def test_availability_from_storage_missing_row_serves_honest_not_yet_computed(co
     monkeypatch.setattr(data_manager, "compute_availability", _boom)
     with Session(engine) as session:
         served = data_manager.availability_from_storage(session, cfg)
-    assert served == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+    assert served == {
+        "total_symbols": 0, "trading_day_count": 0, "cells": [],
+        "stale": False, "served_dataset_version": None,
+    }
 
 
 def test_availability_from_storage_empty_db_matches_honest_fallback():
-    """A genuinely empty / bars-less DB (no cache row, no bars) serves the SAME honest empty payload —
-    coincidentally identical to `compute_availability`'s own empty-DB return, but served with ZERO
-    database queries via the fallback, never a live compute."""
+    """TC-2 — a genuinely empty / bars-less DB (no cache row, no bars) serves the SAME honest empty
+    payload — coincidentally identical to `compute_availability`'s own empty-DB return plus `stale:
+    False`/`served_dataset_version: None`, served with ZERO database queries via the fallback, never a
+    live compute."""
     engine = make_engine("sqlite:///:memory:")
     create_db_and_tables(engine)
     with Session(engine) as session:
         served = data_manager.availability_from_storage(session, load_config())
-    assert served == {"total_symbols": 0, "trading_day_count": 0, "cells": []}
+    assert served == {
+        "total_symbols": 0, "trading_day_count": 0, "cells": [],
+        "stale": False, "served_dataset_version": None,
+    }
+
+
+def test_availability_from_storage_stale_serves_prior_row_on_stamp_mismatch(coverage_engine):
+    """TC-1 — the iter-57 J-06 during-a-job honesty fix: once a row exists but a NEW bar has landed
+    without the finalize-tail warm re-running yet (the `_membership_dataset_version` stamp folds in
+    `count(daily_prices)`, so a bare INSERT bumps it — exactly what a mid-flight ingest's first
+    committed bar does), `availability_from_storage` serves the PRIOR persisted row — non-empty cells,
+    `stale: True`, `served_dataset_version` equal to the OLD (pre-bar) stamp, never the current one and
+    never the not-yet-computed empty sentinel."""
+    engine, spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
+        prior_version = data_manager._membership_dataset_version(session, cfg)
+
+    # Simulate an ingest job's first committed bar landing WITHOUT the finalize-tail warm re-running —
+    # bumps _membership_dataset_version (count(daily_prices) changes) but leaves AvailabilityCache at V1.
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
+        ))
+        session.commit()
+
+    with Session(engine) as session:
+        current_version = data_manager._membership_dataset_version(session, cfg)
+        served = data_manager.availability_from_storage(session, cfg)
+
+    assert current_version != prior_version  # the stamp genuinely moved (sanity check on the setup)
+    assert served["stale"] is True
+    assert served["served_dataset_version"] == prior_version
+    # the PRIOR row's real cells/total_symbols/trading_day_count — never the empty sentinel
+    assert served["cells"] == prior_payload["cells"]
+    assert served["total_symbols"] == prior_payload["total_symbols"]
+    assert served["trading_day_count"] == prior_payload["trading_day_count"]
+    assert served["cells"] != []
+
+
+def test_availability_from_storage_stale_fallback_never_recomputes(coverage_engine, monkeypatch):
+    """The stale-serving fallback (TC-1) reads ONLY the persisted row — never a live
+    `compute_availability` call on this default request path (AG-8), exactly like the not-yet-computed
+    fallback it extends."""
+    engine, spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
+        ))
+        session.commit()
+
+    def _boom(*_a, **_k):
+        raise AssertionError("a stale-serving fallback must never trigger a live compute_availability call")
+
+    monkeypatch.setattr(data_manager, "compute_availability", _boom)
+    with Session(engine) as session:
+        served = data_manager.availability_from_storage(session, cfg)
+    assert served["stale"] is True
 
 
 # ==================================================================================================
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index b26fdda5..719d2dac 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -1,16 +1,20 @@
 """GET /api/health via FastAPI TestClient against the loaded temp DB."""
 from __future__ import annotations
 
+from datetime import date
+
 from fastapi.testclient import TestClient
-from sqlalchemy import event
+from sqlalchemy import event, func, select as sa_select
 from sqlmodel import Session, select
 
 import main
+from app.api.health import _distinct_symbol_count
 from app.config import load_config
+from app.db import create_db_and_tables, make_engine
 from app.engine import readiness
 from app.engine.scanner import get_run_for_date
 from app.engine.warmup import _warmup_dates
-from app.models import ScannerRun
+from app.models import DailyPrice, ScannerRun
 
 
 def test_health_returns_ok_shape(loaded_engine):
@@ -261,3 +265,60 @@ def test_readiness_grouped_existence_query_matches_per_date_check(loaded_engine)
             session.exec(select(ScannerRun.asof_date).where(ScannerRun.asof_date.in_(cadence_dates))).all()
         )
     assert grouped_persisted == manual_persisted
+
+
+# ==================================================================================================
+# ops-hardening iter-57 (TC-5) -- `_distinct_symbol_count`'s fast indexed-walk replaces the per-request
+# `COUNT(DISTINCT symbol)` covering-index scan (0.117-0.119s live on the grown dev DB, the confirmed
+# majority of GET /api/health's steady-state latency against the committed <=0.1s budget). Fast,
+# hand-built fixtures -- NOT `loaded_engine` -- so these run in milliseconds, mirroring `coverage_engine`
+# in test_data_manager.py rather than the slow 30-year-seed session fixture.
+# ==================================================================================================
+def test_distinct_symbol_count_byte_identical_to_naive_count_distinct(tmp_path):
+    """TC-5 byte-identity: the fast indexed-walk query returns the SAME value as a plain
+    `SELECT COUNT(DISTINCT symbol)` for the same DB state -- multiple symbols, multiple dates per
+    symbol, and one symbol repeated across every date (proving it counts distinct SYMBOLS, not rows)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'symcount.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for sym in ("SPY", "AAA", "BBB"):
+            for d in (date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)):
+                session.add(DailyPrice(symbol=sym, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+
+    with Session(engine) as session:
+        fast = _distinct_symbol_count(session)
+        naive = int(session.execute(sa_select(func.count(func.distinct(DailyPrice.symbol)))).scalar_one() or 0)
+    assert fast == naive == 3
+
+
+def test_distinct_symbol_count_empty_db_is_zero(tmp_path):
+    """An empty / bars-less DB reports 0 -- never an error, never a fabricated count."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'symcount_empty.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        assert _distinct_symbol_count(session) == 0
+
+
+def test_distinct_symbol_count_single_symbol(tmp_path):
+    """A DB with exactly one symbol across several dates counts 1, not the row count (4)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'symcount_one.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    with Session(engine) as session:
+        assert _distinct_symbol_count(session) == 1
+
+
+def test_health_symbol_count_matches_naive_count_distinct_on_loaded_engine(loaded_engine):
+    """TC-5 byte-identity on the realistic seeded fixture: `GET /api/health`'s `symbol_count` (now served
+    by `_distinct_symbol_count`) equals a plain `COUNT(DISTINCT symbol)` for the SAME DB state -- proving
+    the query-shape change introduced no value drift on real data, not just the small hand-built cases
+    above."""
+    with Session(loaded_engine) as session:
+        naive = int(session.execute(sa_select(func.count(func.distinct(DailyPrice.symbol)))).scalar_one() or 0)
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    assert body["symbol_count"] == naive
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index 79975b79..c0832fc2 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -651,6 +651,36 @@ def test_index_series_cached_miss_computes_persists_and_matches_engine_output(tm
     assert rows[0].full is True
 
 
+def test_index_series_cached_rollback_reports_not_persisted(tmp_path, monkeypatch):
+    """TC-10 — ops-hardening iter-57 AG-3 honesty fix: a forced `session.commit()` failure inside
+    `index_series_cached_with_status`'s MISS path rolls back (the existing `except: session.rollback()`
+    branch) and MUST report `persisted_this_call=False` — never `True` for a write that did not durably
+    persist (mirrors the SAME fix on `data_manager.availability_cached_with_status`, the sibling
+    contract). The freshly computed payload is still returned; only the honesty flag changes."""
+    cfg = _cfg(tmp_path)
+    engine = _engine_with_bars()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0, 101.0, 102.0])
+        _insert_bars(session, "QQQ", [50.0, 51.0, 52.0])
+        session.commit()
+        expected = compute_index_series(
+            session, as_of=None, range_key=cfg.index_chart.default_range, config=cfg, full=True
+        )
+
+    with Session(engine) as session:
+        def _boom_commit():
+            raise RuntimeError("forced commit failure (TC-10 fault injection)")
+
+        monkeypatch.setattr(session, "commit", _boom_commit)
+        payload, persisted = index_series_cached_with_status(session, cfg)
+
+    assert persisted is False
+    assert payload == expected
+    with Session(engine) as session:
+        rows = session.exec(select(IndexSeriesCache)).all()
+    assert rows == []
+
+
 def test_index_series_cached_hit_serves_without_recompute(tmp_path, monkeypatch):
     cfg = _cfg(tmp_path)
     engine = _engine_with_bars()
diff --git a/apps/backend/tests/test_indicators.py b/apps/backend/tests/test_indicators.py
index 5f8de0fc..99c06e95 100644
--- a/apps/backend/tests/test_indicators.py
+++ b/apps/backend/tests/test_indicators.py
@@ -54,6 +54,25 @@ def test_sma_series_rejects_nonpositive_period():
         ind.sma_series([1, 2, 3], 0)
 
 
+def test_sma_series_byte_identical_to_original_unbounded_prefix_implementation():
+    """ops-hardening iter-57 (TC-9, the J-06 `bars?through=latest` latency fix): `sma_series` now
+    bounds each call's slice to `values[max(0, i+1-period):i+1]` instead of the full-growing prefix
+    `values[:i+1]` -- an O(n) copy on every one of `len(values)` iterations that made the whole series
+    O(n^2) (profiled: ~0.178s -> ~0.038s for a real 7,695-bar history across 4 configured MA periods,
+    `reports/perf-budgets.md`). Per the iter-53 lesson ("compare against the ORIGINAL implementation,
+    never another instance of the new one"), this test keeps a literal copy of the PRE-iter-57
+    unbounded-prefix implementation and asserts byte-identity against it -- not merely against a second
+    call of the current function -- across several periods and a warm-up-spanning, non-trivial series."""
+    def _sma_series_original_unbounded_prefix(values, period):
+        return [ind.sma(values[: i + 1], period) for i in range(len(values))]
+
+    values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0, 9.0, 7.0, 9.0, 3.0]
+    for period in (1, 2, 3, 5, 8, 16, 20):
+        assert ind.sma_series(values, period) == _sma_series_original_unbounded_prefix(values, period)
+    # the empty-series edge case both forms must agree on
+    assert ind.sma_series([], 3) == _sma_series_original_unbounded_prefix([], 3) == []
+
+
 # --- rs_vs ---------------------------------------------------------------------------------
 def test_rs_vs_exact():
     # series +50% over 1 bar, benchmark flat -> RS 1.5
diff --git a/apps/backend/tests/test_mcp_window.py b/apps/backend/tests/test_mcp_window.py
index 466ea72a..154609df 100644
--- a/apps/backend/tests/test_mcp_window.py
+++ b/apps/backend/tests/test_mcp_window.py
@@ -11,11 +11,14 @@ the committed seed once).
 from __future__ import annotations
 
 import json
+from datetime import date, datetime, timedelta
 
 from fastapi.testclient import TestClient
-from sqlmodel import Session
+from sqlalchemy import event, func
+from sqlmodel import Session, select
 
 import main
+from app.db import create_db_and_tables, make_engine
 from app.engine import ledger as ledger_mod
 from app.engine.snapshot_serving import (
     dashboard_payload,
@@ -26,6 +29,7 @@ from app.engine.snapshot_serving import (
     themes_payload,
 )
 from app.mcp import tools
+from app.models import DailyPrice, ScannerResult, ScannerRun
 
 
 def _json(obj):
@@ -249,6 +253,94 @@ def test_verify_edge_certifies_a_real_factor_cohort(loaded_engine, tmp_path):
     assert ledger_mod.count_trials(ledger_path) == 2
 
 
+# ==================================================================================================
+# ops-hardening iter-57 (TC-11) — `tools.list_runs`'s `n_stocks` grouped-aggregate fix (closes the
+# coherence-auditor's iter-56 advisory: this MCP tool still ran the pre-iter-56 per-run `ScannerResult`
+# COUNT-in-a-loop pattern `app.api.runs.runs` already fixed). A fast, hand-built fixture (mirrors
+# `multi_run_engine` in test_api_runs.py) — NOT `loaded_engine` — so these run in milliseconds.
+# ==================================================================================================
+def _multi_run_engine(tmp_path):
+    """THREE `ScannerRun` rows carrying 3/0/2 `ScannerResult` children respectively — deliberately
+    includes a ZERO-result run so the grouped query's "absent from GROUP BY" default path is exercised."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'mcp_multi_run.db'}")
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
+def test_list_runs_n_stocks_single_grouped_query_not_per_run(tmp_path):
+    """TC-11 — the number of `ScannerResult` queries issued for ONE `list_runs` call is a small constant
+    that does NOT scale with the number of stored runs (never one COUNT query per run — the exact
+    stale-duplicate pattern the coherence audit flagged)."""
+    engine = _multi_run_engine(tmp_path)
+    statements: list[str] = []
+
+    def _capture(conn, cursor, statement, parameters, context, executemany):
+        if "scanner_results" in statement.lower():
+            statements.append(statement)
+
+    event.listen(engine, "before_cursor_execute", _capture)
+    try:
+        with Session(engine) as session:
+            n_runs = session.exec(select(func.count()).select_from(ScannerRun)).one()
+            if isinstance(n_runs, tuple):
+                n_runs = n_runs[0]
+            result = tools.list_runs(session)
+    finally:
+        event.remove(engine, "before_cursor_execute", _capture)
+
+    assert n_runs == 3  # sanity: this fixture's own 3 runs
+    assert len(result["runs"]) == n_runs
+    assert len(statements) == 1, (
+        f"expected exactly 1 grouped ScannerResult query, saw {len(statements)} for {n_runs} stored runs"
+    )
+
+
+def test_list_runs_n_stocks_byte_identical_to_per_run_count(tmp_path):
+    """TC-11 — every stored run's `n_stocks` from `list_runs` is byte-identical to a direct per-run
+    COUNT (the pre-fix per-run computation) — the grouped-query rewrite changes only the query plan,
+    never the served value. Exercises the 3/0/2-result spread, including the ZERO-result run."""
+    engine = _multi_run_engine(tmp_path)
+    with Session(engine) as session:
+        result = tools.list_runs(session)
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
+    assert result["runs"]
+    assert len(result["runs"]) == len(expected_by_run_id) == 3
+    assert sorted(expected_by_run_id.values()) == [0, 2, 3]  # the fixture's own 3/0/2 spread, sanity
+    for row in result["runs"]:
+        assert row["n_stocks"] == expected_by_run_id[row["run_id"]]
+
+
 # ==================================================================================================
 # Additional read-only mirrors: regime-history, indexes, methodology, runs (+ detail)
 # ==================================================================================================
diff --git a/apps/frontend/components/availability-heatmap.tsx b/apps/frontend/components/availability-heatmap.tsx
index 455c2611..a95a0ff6 100644
--- a/apps/frontend/components/availability-heatmap.tsx
+++ b/apps/frontend/components/availability-heatmap.tsx
@@ -42,6 +42,15 @@ import type { AvailabilityCell, AvailabilityResponse } from "@/lib/api";
  *
  * iter-5 nested-interactive guard: each day is a single `<button>` (the click target); the snapshot
  * marker and the hover tooltip are non-interactive `<span>`s INSIDE it — no nested interactive element.
+ *
+ * ops-hardening iter-57 (J-06 closure): the payload now carries `stale`/`served_dataset_version` (see
+ * `AvailabilityResponse` in `lib/api.ts`). `stale: true` means the backend served the MOST RECENT
+ * persisted reading rather than the current in-flight one (an ingest is mid-flight; the payload's real
+ * cells are shown, exactly as before) — this component now renders a calm "Data as of
+ * `<served_dataset_version>` — updating" notice above the grid in that case (mirrors the Coverage
+ * panel's existing `coverage-stale-notice` treatment, same tone, same tokens). `stale: false` with
+ * non-empty cells renders unchanged; `stale: false` with empty cells is still the ONLY case the "No
+ * availability yet" empty state below is honest for (a DB where no row has ever been persisted).
  */
 
 type DensityBucket = 0 | 1 | 2 | 3 | 4 | 5;
@@ -212,6 +221,15 @@ export function AvailabilityHeatmap({
         </p>
       </div>
 
+      {state.kind === "ok" && state.data.stale ? (
+        <p
+          className="border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted"
+          data-testid="availability-stale-notice"
+        >
+          Data as of {state.data.served_dataset_version} — updating
+        </p>
+      ) : null}
+
       {state.kind === "loading" ? (
         <div className="flex items-center gap-2 p-6 text-sm text-text-muted" data-testid="availability-loading">
           <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 0b1e0a8c..1bc9b3a5 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -2715,11 +2715,24 @@ export interface AvailabilityCell {
 
 /** J-61: the per-trading-date availability payload (GET /api/data/availability). `cells` is one entry per
  *  benchmark trading day, ascending. An empty / bars-less DB → `cells: []`, `total_symbols: 0` (no
- *  fabricated cells). Descriptive metadata only — no canonical value is recomputed. */
+ *  fabricated cells). Descriptive metadata only — no canonical value is recomputed.
+ *
+ *  ops-hardening iter-57 (J-06 closure): two additive fields close the during-a-job honesty gap where the
+ *  backend used to serve the not-yet-computed empty sentinel for the ENTIRE duration of any ingest job
+ *  (the cache's dataset-version stamp bumps on the job's first committed bar, but the cache row is only
+ *  re-warmed at the job's END) — falsely telling the operator no data exists over a multi-million-row DB.
+ *  `stale: true` now means: this `cells`/`total_symbols`/`trading_day_count` payload is the MOST RECENT
+ *  persisted reading, not the current in-flight one (an ingest is mid-flight and its finalize warm has not
+ *  yet re-run). `served_dataset_version` is the dataset_version stamp that payload actually reflects —
+ *  `null` only when NO `AvailabilityCache` row has EVER been persisted (the genuinely never-ingested case,
+ *  the ONLY case the empty sentinel remains honest for). `stale: false` (the pre-existing, unchanged
+ *  behavior) means the payload matches the CURRENT dataset version. */
 export interface AvailabilityResponse {
   total_symbols: number;
   trading_day_count: number;
   cells: AvailabilityCell[];
+  stale: boolean;
+  served_dataset_version: string | null;
 }
 
 /** J-61: GET /api/data/availability — the per-trading-date availability heatmap source. Throws on a
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 428 +++++++++++++++++++++
 .../journey-scripts/J-06.json                      |  32 +-
 .../state/assumptions.md                           |  71 ++++
 runs/goal-session-ops-hardening/state/blueprint.md |   2 +-
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |  52 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  11 +
 8 files changed, 585 insertions(+), 15 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
