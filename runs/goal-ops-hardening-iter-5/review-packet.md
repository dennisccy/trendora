# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index 0a20a844..82c2b785 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -36,8 +36,8 @@ from app.config import Config, get_config
 from app.db import get_session
 from app.engine.forward_testing import (
     backfill_run_forward_returns,
-    compute_forward_aggregates,
     compute_run_scorecard,
+    forward_aggregates_cached,
 )
 from app.engine.scanner import _latest_stored_run_date
 from app.engine.snapshot_serving import resolved_run
@@ -65,8 +65,11 @@ def backtest(
     # is scoped to the EXPANDING WINDOW of snapshots dated <= the resolved run's asof_date (the SAME global
     # as-of already resolved — no second date control, J-18). Read-only grouping over the stored
     # forward_returns — recomputes no return/score/bucket (the same model the retired System Health used).
+    # ops-hardening iter-5 (J-06): served from the ingest-warmed cache (byte-identical to a fresh compute;
+    # `compute_forward_aggregates` itself is unchanged and stays the sole producer) — a live 5-horizon
+    # request here measured 34.77s pre-fix (reports/perf-budgets.md).
     evidence_by_horizon = {
-        h: compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)
+        h: forward_aggregates_cached(session, h, cfg, as_of=run.asof_date)
         for h in cfg.walk_forward.horizons
     }
     # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index d1fdd8ce..ef226f09 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1884,9 +1884,9 @@ class JobProgress:
     # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
-    # "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` it actually refreshed —
-    # empty/default until the hook has actually run (never fabricated on an interrupted/failed row; gated
-    # in `_run_detail()` the SAME way `calendar_days` etc. already are).
+    # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]` it
+    # actually refreshed — empty/default until the hook has actually run (never fabricated on an
+    # interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc. already are).
     new_snapshot_dates: list[date_cls] = field(default_factory=list)
     aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
@@ -3047,9 +3047,9 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
-    "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` ACTUALLY refreshed — never a
-    fabricated category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this
-    module).
+    "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]`
+    ACTUALLY refreshed — never a fabricated category (mirrors the `omitted`/`passers` honesty convention
+    already used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -3103,6 +3103,32 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     if market_phase_warmed:
         refreshed.append("market_phase")
 
+    # ops-hardening iter-5 (J-06): warm the CURRENT latest stored run's per-horizon forward-aggregate
+    # cache (GET /api/backtest's `evidence_by_horizon`, ~34.77s pre-fix over all 5 configured horizons —
+    # reports/perf-budgets.md). Unconditional (not gated on `prog.new_snapshot_dates`, unlike the
+    # per-date coverage/market-phase loops above): the dataset-version stamp is GLOBAL, so ANY ingest
+    # anywhere (even a historical-gap backfill far from the latest date) can invalidate the latest run's
+    # already-cached aggregate — e.g. a backfilled EARLIER date's forward returns newly enter the
+    # latest as-of's expanding "<= D" window. Warming only the ONE current-latest key (not every
+    # historical as-of) mirrors the "research_hot_keys" default-key philosophy just below, not the
+    # per-date coverage/market-phase sweep — each per-horizon compute can itself be as expensive as the
+    # measured 34.77s violation, so sweeping every `new_snapshot_dates` entry here (as coverage/
+    # market_phase do) would risk turning a full-universe rebuild's finalize tail into a multi-hour
+    # operation instead of the intended fix. A user-navigated HISTORICAL as-of on `/backtest` still
+    # computes-once-and-caches on first view (the same cold-miss contract EventStudyCache/
+    # MarketPhaseCache already carry) — never pre-warmed here.
+    try:
+        latest_run_date = scanner._latest_stored_run_date(session)
+        if latest_run_date is not None:
+            for h in cfg.walk_forward.horizons:
+                prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
+                             # compute here can take up to ~35s pre-warm; 5 sequential horizons could
+                             # otherwise freeze the heartbeat for minutes without a per-horizon tick).
+                forward_testing.forward_aggregates_cached(session, h, cfg, as_of=latest_run_date)
+            refreshed.append("forward_aggregates")
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest forward-aggregate warm failed (non-fatal): %s", exc)
+
     try:
         subjects = subject_catalog(cfg)
         if subjects:
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 043c6936..9436658f 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -49,7 +49,7 @@ from app.config import Config, get_config
 from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.engine.setups import ALL_STATUSES
-from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun
+from app.models import EventStudyCache, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
 
 # The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). iter-18: the
 # basis now spans ~30 years (1996 -> present, per-name real listing depth) over the broadened
@@ -936,6 +936,79 @@ def compute_forward_aggregates(
     }
 
 
+def forward_aggregates_cached(
+    session: Session, horizon: int, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
+) -> dict:
+    """Serve `compute_forward_aggregates` from an ingest-time warm cache (ops-hardening iter-5, J-06),
+    mirroring `research.event_study_cached` / `market_phase.market_phase_cached`: on a cache HIT for the
+    current `(horizon, asof_key, dataset_version)` key, deserialize and return the stored aggregate (NO
+    recompute); on a MISS, compute it ONCE via `compute_forward_aggregates` (the SOLE producer — this
+    function is a pure serving/persistence wrapper, never a second derivation), persist it under the
+    current dataset-version stamp, prune any stale rows for this `(horizon, asof_key)` identity, and
+    return it. The returned payload is BYTE-IDENTICAL to `compute_forward_aggregates(...)` (No recompute
+    in the read path).
+
+    WHY: `GET /api/backtest` called `compute_forward_aggregates` once per configured horizon (5) on
+    EVERY request — each call scans the WHOLE horizon-partition of `forward_returns` (~1.5-1.7M rows /
+    5 horizons at the current DB depth) and groups it in Python. Measured live
+    (`reports/perf-budgets.md`, iter-5): 34.77s for one `GET /api/backtest` request — the confirmed J-06
+    violation this cache fixes.
+
+    Because the key carries the `dataset_version` stamp (the SAME stamp `research._dataset_version`
+    produces — single-sourced with J-72/J-87/J-96/J-100), the cache REFRESHES automatically after any
+    dataset change (a backfill add or a removal, anywhere in the dataset — not just at this `as_of`,
+    since a backfilled EARLIER date can newly enter an already-cached LATER as-of's expanding window) —
+    a stale row is never hit. Unlike `EventStudyCache`/`MarketPhaseCache`, this cache carries no separate
+    "all-history" sentinel: `compute_forward_aggregates`'s one call site always resolves `as_of` to a
+    concrete `ScannerRun.asof_date` first (never the bare `as_of=None` case), so `asof_key` is always a
+    real ISO date.
+
+    Deferred import below (not at module level): `research.py` already imports names FROM this module,
+    so this module cannot import `research.py` at load time without a circular import; importing
+    `_dataset_version` lazily, inside this function, breaks the cycle (the same fix has no effect on
+    behavior — both modules are fully loaded by the time this function actually runs)."""
+    from app.engine.research import _dataset_version  # deferred: avoids a forward_testing<->research cycle
+
+    cfg = config or get_config()
+    version = _dataset_version(session)
+    asof_key = as_of.isoformat() if as_of is not None else "all"
+
+    hit = session.exec(
+        select(ForwardAggregateCache).where(
+            ForwardAggregateCache.horizon == horizon,
+            ForwardAggregateCache.asof_key == asof_key,
+            ForwardAggregateCache.dataset_version == version,
+        )
+    ).first()
+    if hit is not None:
+        return json.loads(hit.payload_json)
+
+    # MISS — compute once (the SOLE producer, unchanged) and persist.
+    payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+
+    # prune stale rows for THIS (horizon, asof_key) identity (any older dataset_version) so the cache
+    # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
+    stale = session.exec(
+        select(ForwardAggregateCache).where(
+            ForwardAggregateCache.horizon == horizon,
+            ForwardAggregateCache.asof_key == asof_key,
+            ForwardAggregateCache.dataset_version != version,
+        )
+    ).all()
+    for row in stale:
+        session.delete(row)
+
+    session.add(ForwardAggregateCache(
+        horizon=horizon, asof_key=asof_key, dataset_version=version,
+        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
+    ))
+    try:
+        session.commit()
+    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
+        session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
+    return payload
+
+
 # --------------------------------------------------------------------------------------------------
 # Per-date scorecard (J-14) — create-once population + the SINGLE per-date forward-test read
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 815bf9ff..39721ecd 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -31,8 +31,8 @@ from app.engine import online_fdr
 from app.engine.forward_testing import (
     backfill_run_forward_returns,
     benchmark_symbols,
-    compute_forward_aggregates,
     compute_run_scorecard,
+    forward_aggregates_cached,
 )
 from app.engine.referee import (
     DEFAULT_ALPHA_BUDGET,
@@ -198,8 +198,11 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     run = resolved_run(session, asof, cfg)
     backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
     card = compute_run_scorecard(session, run, cfg)
+    # ops-hardening iter-5 (J-06): served from the SAME ingest-warmed cache GET /api/backtest now uses
+    # (this function's own docstring says it "mirrors the endpoint exactly" — kept true for the cache
+    # swap too; byte-identical output, `compute_forward_aggregates` itself is unchanged).
     evidence_by_horizon = {
-        h: compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)
+        h: forward_aggregates_cached(session, h, cfg, as_of=run.asof_date)
         for h in cfg.walk_forward.horizons
     }
     return {
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index f09fc157..73f3fa05 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -504,6 +504,61 @@ class MarketPhaseCache(SQLModel, table=True):
     created_at: datetime
 
 
+# --- ops-hardening iter-5 (J-06) forward-aggregate derived-cache ---------------------------------
+class ForwardAggregateCache(SQLModel, table=True):
+    """A STANDALONE, create_all-managed cache of the derived per-horizon forward-return aggregate
+    (`app.engine.forward_testing.compute_forward_aggregates`), served on `GET /api/backtest`'s
+    `evidence_by_horizon` (ops-hardening iter-5, J-06).
+
+    Like `EventStudyCache` / `MarketPhaseCache` / `CoverageSnapshot`, this is EXPLICITLY NOT a scanner
+    snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
+    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
+    state: it stores the SERIALIZED `compute_forward_aggregates(...)` payload (forward return by
+    bucket/setup/regime, excess vs SPY/QQQ, VCP/new-pattern breakdowns, control-group cohorts — each
+    with `n`) keyed by the horizon + the resolved as-of cutoff + a dataset-version stamp, so a read
+    serves the stored aggregate instead of re-deriving it per request (No recompute in the read path).
+    The cached figures are BYTE-IDENTICAL to a fresh compute — a cache of the deterministic read-only
+    aggregation, never a second computation.
+
+    WHY: `compute_forward_aggregates` scans the WHOLE horizon-partition of `forward_returns`
+    (`select(ForwardReturn).where(horizon == h)`, then groups it in Python) — `GET /api/backtest`
+    called it once per configured horizon (5) on EVERY request. Measured live at the current DB depth
+    (`reports/perf-budgets.md`, iter-5): 34.77s for one request — the confirmed J-06 violation.
+
+    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
+    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
+    existing table gains a column.
+
+    CACHE KEY: `(horizon, asof_key, dataset_version)`:
+      - `horizon` is the requested horizon (one of `config.walk_forward.horizons`).
+      - `asof_key` is the resolved as-of cutoff ISO date — `compute_forward_aggregates`'s `as_of` is
+        always a concrete date at its one call site (`GET /api/backtest` always resolves `?as_of=` to a
+        real `ScannerRun.asof_date` before calling it — never the bare `as_of=None` all-history case),
+        so unlike `EventStudyCache`/`MarketPhaseCache` this key carries no separate "all" sentinel.
+      - `dataset_version` is the SAME stamp `app.engine.research._dataset_version` produces
+        (single-sourced with J-72/J-87/J-96/J-100) — a read computes the current stamp and looks up
+        THIS exact key; a stale row keyed to an older stamp is never hit (and is pruned on write), so
+        the cache can NEVER serve a stale figure (it refreshes after any dataset change — a backfill
+        that adds runs/returns anywhere changes the global stamp, correctly invalidating even an
+        unrelated as-of's cached row, since an expanding as-of window can gain new in-range runs from a
+        backfill dated earlier than it).
+
+    `payload_json` is the full serialized aggregate. Unique on the composite key so a write is an
+    idempotent upsert."""
+
+    __tablename__ = "forward_aggregate_cache"
+    __table_args__ = (
+        UniqueConstraint("horizon", "asof_key", "dataset_version", name="uq_forward_aggregate_cache_key"),
+    )
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    horizon: int = Field(index=True)
+    asof_key: str  # resolved as-of ISO cutoff date (compute_forward_aggregates's concrete `as_of`)
+    dataset_version: str  # the SAME stamp research._dataset_version produces; changes on any dataset change
+    payload_json: str  # the serialized compute_forward_aggregates(...) aggregate (byte-identical to a fresh compute)
+    created_at: datetime
+
+
 class MacroSeries(SQLModel, table=True):
     """A STANDALONE, create_all-managed table of optional FRED macro-feed observations (iter-32, J-92).
 
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index bb6aa772..0e45a424 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -68,6 +68,7 @@ from app.models import (
     CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
+    ForwardAggregateCache,
     ForwardReturn,
     ImportCheckpoint,
     ScannerResult,
@@ -1042,7 +1043,8 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
     """TC-1/TC-5 — a finalize hook call for a job that newly created a snapshot on `d` persists exactly one
     `coverage_snapshot` row for the current stamp and reports every category this fixture's data supports
     as refreshed: `latest_snapshot` (this run created a snapshot), `coverage` + `membership_timeline` (one
-    compute warms both), `market_phase` (the new date), `research_hot_keys` (the default hot key)."""
+    compute warms both), `market_phase` (the new date), `forward_aggregates` (ops-hardening iter-5: the
+    current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key)."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     with Session(engine) as session:
@@ -1050,7 +1052,8 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         prog.new_snapshot_dates = [d]
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
     assert set(refreshed) == {
-        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys",
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys",
     }
     with Session(engine) as session:
         rows = session.exec(select(CoverageSnapshot)).all()
@@ -1060,6 +1063,52 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)
 
 
+def test_finalize_hook_warms_forward_aggregates_for_every_configured_horizon(finalize_hook_engine):
+    """ops-hardening iter-5 (J-06) — the finalize hook warms `ForwardAggregateCache` for the CURRENT
+    latest stored run's as-of, once per configured `walk_forward.horizons` — proven directly: after the
+    hook runs, exactly one cached row exists per configured horizon at that as-of."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="forward-agg-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "forward_aggregates" in refreshed
+    with Session(engine) as session:
+        rows = session.exec(
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == d.isoformat())
+        ).all()
+    assert {row.horizon for row in rows} == set(cfg.walk_forward.horizons)
+
+
+def test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read(
+    finalize_hook_engine, monkeypatch
+):
+    """A `GET /api/backtest`-shaped read for the SAME (horizon, as-of) the finalize hook just warmed
+    hits the cache — zero further `compute_forward_aggregates` calls. This is the actual perf fix this
+    iteration makes: a live request no longer pays the 5-horizon full-table scan the finalize hook
+    already paid at ingest (measured 34.77s pre-fix for one request, `reports/perf-budgets.md`)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="forward-agg-hit-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    call_count = {"n": 0}
+    real = forward_testing.compute_forward_aggregates
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(forward_testing, "compute_forward_aggregates", _counting)
+    with Session(engine) as session:
+        for h in cfg.walk_forward.horizons:
+            forward_testing.forward_aggregates_cached(session, h, cfg, as_of=d)
+    assert call_count["n"] == 0, "the finalize hook's warm should have already cached every horizon"
+
+
 def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finalize_hook_engine):
     """TC-8 — the persisted payload_json is byte-identical (field-by-field) to a direct fresh
     `_compute_coverage_uncached` call for the same session state (AG-3: storage is re-served, never
@@ -1152,6 +1201,7 @@ def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_eng
 
     monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _boom)
     monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _boom)
     monkeypatch.setattr(data_manager, "event_study_cached", _boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 51bc5bcd..397576cd 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -33,6 +33,7 @@ from app.engine.forward_testing import (
     compute_drawdown_expectations,
     compute_drawdown_expectations_cached,
     compute_forward_aggregates,
+    forward_aggregates_cached,
     forward_excursions,
     forward_return,
     max_drawdown,
@@ -45,6 +46,7 @@ from app.engine.scanner import run_scan
 from app.models import (
     DailyPrice,
     EventStudyCache,
+    ForwardAggregateCache,
     ForwardReturn,
     ScannerResult,
     ScannerRun,
@@ -810,6 +812,99 @@ def test_aggregates_as_of_scoped_consistency_invariant_relocated(aggregates_engi
     assert sum(r["n"] for r in attr["by_rank_band"]) == overall["n"]
 
 
+# ==================================================================================================
+# forward_aggregates_cached (ops-hardening iter-5, J-06) — the ForwardAggregateCache performance layer.
+# GET /api/backtest called compute_forward_aggregates once per configured horizon (5) on EVERY request;
+# measured live at 34.77s for one request (reports/perf-budgets.md). This cache mirrors
+# research.event_study_cached / market_phase.market_phase_cached / this module's own
+# compute_drawdown_expectations_cached exactly.
+# ==================================================================================================
+def test_forward_aggregates_cached_byte_identical_and_single_row(aggregates_engine):
+    """A cache MISS then HIT both return a payload BYTE-IDENTICAL to a fresh uncached
+    `compute_forward_aggregates` call, and exactly ONE `ForwardAggregateCache` row is written for this
+    (horizon, as_of) (no duplicate insert on the second call)."""
+    engine, H = aggregates_engine
+    cfg = load_config()
+    as_of = date(2025, 1, 10)
+    with Session(engine) as session:
+        fresh = compute_forward_aggregates(session, H, cfg, as_of=as_of)
+        miss = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        hit = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        rows = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == H,
+                ForwardAggregateCache.asof_key == as_of.isoformat(),
+            )
+        ).all()
+    assert json.dumps(fresh, sort_keys=True) == json.dumps(miss, sort_keys=True) == json.dumps(hit, sort_keys=True)
+    assert len(rows) == 1
+
+
+def test_forward_aggregates_cached_avoids_recompute_on_hit(aggregates_engine, monkeypatch):
+    """The SECOND call for the SAME (horizon, as_of) never re-invokes the uncached
+    `compute_forward_aggregates` — proven by monkeypatching it to count calls (a call-count proof, not
+    just a byte-match, so a bug that silently recomputed-but-still-matched would still fail this test)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine, H = aggregates_engine
+    cfg = load_config()
+    as_of = date(2025, 1, 10)
+    call_count = {"n": 0}
+    real = forward_testing_module.compute_forward_aggregates
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(forward_testing_module, "compute_forward_aggregates", _counting)
+    with Session(engine) as session:
+        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # MISS -> 1 call
+        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
+        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
+    assert call_count["n"] == 1
+
+
+def test_forward_aggregates_cached_refreshes_on_dataset_version_change(aggregates_engine):
+    """The cache refreshes when the dataset changes (no stale figure): adding one more forward-return
+    observation on the SAME already-included run bumps `_dataset_version`, so the next call for the SAME
+    (horizon, as_of) recomputes (a genuinely larger cohort) rather than serving the pre-change payload,
+    and the stale row is pruned (iter-2 B1 lesson: a fingerprint-only invalidation must not serve a
+    false/stale figure — this reuses the SAME already-hardened `research._dataset_version` stamp, never
+    a new invalidation mechanism)."""
+    engine, H = aggregates_engine
+    cfg = load_config()
+    as_of = date(2025, 1, 10)
+    with Session(engine) as session:
+        before = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        from app.engine.research import _dataset_version
+        v_before = _dataset_version(session)
+        rows_before = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == H, ForwardAggregateCache.asof_key == as_of.isoformat(),
+            )
+        ).all()
+        assert len(rows_before) == 1 and rows_before[0].dataset_version == v_before
+
+        # change the dataset: one more forward-return observation on run1 (the already-included latest
+        # run) -- a genuinely different cohort at the SAME (horizon, as_of) key.
+        run1 = session.exec(select(ScannerRun).where(ScannerRun.asof_date == as_of)).one()
+        _add_result(session, run1.id, "ZZZ", "A", "Actionable", "Technology", 5)
+        _add_fr(session, run1.id, "ZZZ", H, 1.00)
+        session.commit()
+        v_after = _dataset_version(session)
+        assert v_after != v_before
+
+        after = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        rows_after = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == H, ForwardAggregateCache.asof_key == as_of.isoformat(),
+            )
+        ).all()
+    assert len(rows_after) == 1 and rows_after[0].dataset_version == v_after
+    assert before["overall"]["n"] == 6
+    assert after["overall"]["n"] == 7  # the recompute picked up the new ZZZ observation
+
+
 # ==================================================================================================
 # walk-forward as-of date set (real seed trading calendar; no run_scan -> cheap)
 # ==================================================================================================
diff --git a/incredible_auto_dev/scripts/measure-perf.sh b/incredible_auto_dev/scripts/measure-perf.sh
index e3bdbb5d..4c70c70a 100755
--- a/incredible_auto_dev/scripts/measure-perf.sh
+++ b/incredible_auto_dev/scripts/measure-perf.sh
@@ -9,18 +9,38 @@
 # reports/perf-budgets.md so the growth/perf slope is visible run-over-run (goal.md J-15/J-16).
 #
 # Runs against PROD MODE ONLY (scripts/start-backend.sh / scripts/start-frontend.sh — this script does
-# NOT start them; bring them up first). `next dev`'s per-route compile is not product latency, so this
-# script refuses to measure against a `next dev` frontend (no reliable way to detect that from here, so
-# it just documents the requirement — see the header + --help).
+# NOT start them; bring them up first, UNLESS you pass --boot, see below). `next dev`'s per-route
+# compile is not product latency, so this script refuses to measure against a `next dev` frontend (no
+# reliable way to detect that from here, so it just documents the requirement — see the header + --help).
+#
+# iter-5 (J-06 capstone) additions:
+#   --boot   TC-1: measure backend cold-boot wall time (process start -> first GET /api/health HTTP
+#            200) on the warm committed-seed DB. Off by default (a normal run still expects the
+#            backend already warm/running, unchanged). When passed, this script refuses to run if
+#            something already answers on the backend port (a cold-boot measurement needs a REAL
+#            process start — never stomping a live instance), then launches
+#            scripts/start-backend.sh itself and leaves it running afterward so the rest of this
+#            script's warm measurements proceed normally against it. The frontend is still never
+#            started by this script — bring it up yourself.
+#   Also captures the 7 previously-unmeasured pages/endpoints named in goal.md J-06: the Dashboard
+#   cluster (/api/dashboard, /api/market-phase, /api/sectors, /api/themes, /api/indexes?full=true,
+#   /api/regime-history?full=true, /api/market-phase?full=true — the cross-view chart's own calls),
+#   /api/sectors, /api/themes, /api/runs, /api/backtest, /api/watchlist, /api/research/event-study —
+#   and their pages (/, /sectors, /themes, /scanner-runs, /backtest, /watchlist,
+#   /research/event-study).
 #
 # Usage:
 #   bash scripts/start-backend.sh &
 #   bash scripts/start-frontend.sh &
 #   # wait for both to answer 200, then:
 #   bash scripts/measure-perf.sh [--ticker AAPL] [--backfill-days 5] [--out reports/perf-budgets.md]
+#   # OR, to also measure cold-boot (TC-1) and let this script start the backend itself:
+#   bash scripts/start-frontend.sh &
+#   bash scripts/measure-perf.sh --boot [--out reports/perf-budgets.md]
 #
-# Every bound/scope this script uses (the backfill window size, the default ticker) is a NAMED
-# default below or a flag override — never a bare literal buried in logic (goal.md item K's own rule).
+# Every bound/scope this script uses (the backfill window size, the default ticker, the boot poll
+# interval/timeout/budget) is a NAMED default below or a flag override — never a bare literal buried
+# in logic (goal.md item K's own rule).
 set -euo pipefail
 
 REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
@@ -40,11 +60,23 @@ DEFAULT_TICKER="AAPL"
 DEFAULT_BACKFILL_DAYS=5
 DEFAULT_OUT="$REPO_ROOT/reports/perf-budgets.md"
 DEFAULT_BACKFILL_POLL_TIMEOUT_S=120
+# iter-5 TC-1: cold-boot measurement bounds. TIMEOUT is this SCRIPT's own safety bound (so a wedged
+# boot fails loud instead of polling forever); BUDGET is the PRODUCT's committed ceiling (goal.md
+# Success Criteria: "process start -> first GET /api/health HTTP 200 in <= 5 seconds").
+DEFAULT_BOOT_TIMEOUT_S=30
+DEFAULT_BOOT_POLL_INTERVAL_S=0.1
+DEFAULT_BOOT_BUDGET_S=5
+# iter-5 TC-2/TC-5/TC-6/TC-9/TC-10/TC-11/TC-12: the generic newly-committed budgets, matching every
+# existing non-tiny-payload endpoint/page already on file (e.g. `/api/stocks`/`/api/data` <= 1.5 s;
+# `/stocks`/`/data`/`/evidence` <= 3 s) — a single named default, not 11 more hand-copied numbers.
+DEFAULT_API_BUDGET_S=1.5
+DEFAULT_PAGE_BUDGET_S=3
 
 TICKER="$DEFAULT_TICKER"
 BACKFILL_DAYS="$DEFAULT_BACKFILL_DAYS"
 OUT_FILE="$DEFAULT_OUT"
 SKIP_BACKFILL=0
+MEASURE_BOOT=0
 
 while [[ $# -gt 0 ]]; do
   case "$1" in
@@ -52,8 +84,9 @@ while [[ $# -gt 0 ]]; do
     --backfill-days) BACKFILL_DAYS="$2"; shift 2 ;;
     --out) OUT_FILE="$2"; shift 2 ;;
     --skip-backfill) SKIP_BACKFILL=1; shift ;;
+    --boot) MEASURE_BOOT=1; shift ;;
     -h|--help)
-      sed -n '2,25p' "$0"
+      sed -n '2,43p' "$0"
       exit 0
       ;;
     *)
@@ -84,6 +117,40 @@ _require_200() {
 
 echo "== measure-perf.sh — backend :${BACKEND_PORT}, frontend :${FRONTEND_PORT} ==" >&2
 
+# iter-5 TC-1: backend cold-boot wall time (process start -> first GET /api/health HTTP 200) on the
+# warm committed-seed DB. Off by default — see --boot in --help.
+boot_line="skipped (pass --boot to measure cold-boot-to-health)"
+if [[ "$MEASURE_BOOT" -eq 1 ]]; then
+  echo "-- TC-1: backend cold-boot timing (process start -> first GET /api/health HTTP 200) --" >&2
+  # Refuse to stomp a live instance — a cold-boot measurement needs a REAL process start; if something
+  # already answers here, this script would either fail to bind the port or (worse) silently measure
+  # the wrong process's startup.
+  existing_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 1 "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
+  if [[ "$existing_code" == "200" ]]; then
+    echo "measure-perf.sh --boot: $BACKEND_URL/api/health already answers 200 — stop the running backend first (this measurement needs a real cold process start)." >&2
+    exit 1
+  fi
+  boot_start=$(date +%s.%N)
+  bash "$REPO_ROOT/scripts/start-backend.sh" >/dev/null 2>&1 &
+  boot_pid=$!
+  boot_code="000"
+  boot_deadline=$(( $(date +%s) + DEFAULT_BOOT_TIMEOUT_S ))
+  while [[ "$boot_code" != "200" && $(date +%s) -lt $boot_deadline ]]; do
+    sleep "$DEFAULT_BOOT_POLL_INTERVAL_S"
+    boot_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 0.5 "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
+  done
+  boot_end=$(date +%s.%N)
+  boot_elapsed=$(awk "BEGIN {printf \"%.3f\", $boot_end - $boot_start}")
+  if [[ "$boot_code" == "200" ]]; then
+    boot_holds=$(awk "BEGIN {print ($boot_elapsed <= $DEFAULT_BOOT_BUDGET_S) ? \"yes\" : \"NO\"}")
+    boot_line="**${boot_elapsed}s** (process start -> first HTTP 200), launcher pid ${boot_pid} — holds <= ${DEFAULT_BOOT_BUDGET_S}s budget: ${boot_holds}"
+    echo "  boot-to-health: ${boot_elapsed}s (holds <= ${DEFAULT_BOOT_BUDGET_S}s: ${boot_holds})" >&2
+  else
+    boot_line="FAILED — no HTTP 200 within ${DEFAULT_BOOT_TIMEOUT_S}s of process start (last code: ${boot_code})"
+    echo "  measure-perf.sh --boot: $boot_line" >&2
+  fi
+fi
+
 # Confirm both services are reachable BEFORE measuring (never silently measure a dead endpoint as 0s).
 for probe in "$BACKEND_URL/api/health" "$FRONTEND_URL/"; do
   code=$(curl -s -o /dev/null -w "%{http_code}" "$probe" || echo "000")
@@ -122,6 +189,64 @@ _require_200 "/data (page)" "$data_page_s" "$data_page_code"
 read -r evidence_page_s evidence_page_code <<<"$(_curl_timed "$FRONTEND_URL/evidence")"
 _require_200 "/evidence (page)" "$evidence_page_s" "$evidence_page_code"
 
+# --- iter-5 (J-06 capstone): the 7 previously-unmeasured pages' backing endpoints + their pages ----
+# NAMED endpoint/page maps (label -> URL), measured with the SAME warm-up-then-timed pattern as the
+# endpoints above — a loop rather than 18 more hand-copied blocks (TC-2..TC-12 name this many pairs at
+# once; this is the 3rd+ occurrence of the identical warm+timed-hit shape). Order is a fixed array
+# (bash associative arrays are unordered) so the appended table always reads in the TC-2..TC-12 sequence.
+NEW_ENDPOINT_ORDER=(
+  "GET /api/dashboard" "GET /api/market-phase" "GET /api/sectors" "GET /api/themes"
+  "GET /api/indexes?full=true" "GET /api/regime-history?full=true" "GET /api/market-phase?full=true"
+  "GET /api/runs" "GET /api/backtest" "GET /api/watchlist" "GET /api/research/event-study"
+)
+declare -A NEW_ENDPOINT_URL=(
+  ["GET /api/dashboard"]="$BACKEND_URL/api/dashboard"
+  ["GET /api/market-phase"]="$BACKEND_URL/api/market-phase"
+  ["GET /api/sectors"]="$BACKEND_URL/api/sectors"
+  ["GET /api/themes"]="$BACKEND_URL/api/themes"
+  ["GET /api/indexes?full=true"]="$BACKEND_URL/api/indexes?full=true"
+  ["GET /api/regime-history?full=true"]="$BACKEND_URL/api/regime-history?full=true"
+  ["GET /api/market-phase?full=true"]="$BACKEND_URL/api/market-phase?full=true"
+  ["GET /api/runs"]="$BACKEND_URL/api/runs"
+  ["GET /api/backtest"]="$BACKEND_URL/api/backtest"
+  ["GET /api/watchlist"]="$BACKEND_URL/api/watchlist"
+  # the real first-load call: no subject/horizon (backend picks the default) — `view=episodes` is the
+  # page's own initial state (apps/frontend/app/research/_labs.tsx's EventStudyLab effect).
+  ["GET /api/research/event-study"]="$BACKEND_URL/api/research/event-study?view=episodes"
+)
+NEW_PAGE_ORDER=(
+  "/ (Dashboard)" "/sectors" "/themes" "/scanner-runs" "/backtest" "/watchlist" "/research/event-study"
+)
+declare -A NEW_PAGE_URL=(
+  ["/ (Dashboard)"]="$FRONTEND_URL/"
+  ["/sectors"]="$FRONTEND_URL/sectors"
+  ["/themes"]="$FRONTEND_URL/themes"
+  ["/scanner-runs"]="$FRONTEND_URL/scanner-runs"
+  ["/backtest"]="$FRONTEND_URL/backtest"
+  ["/watchlist"]="$FRONTEND_URL/watchlist"
+  ["/research/event-study"]="$FRONTEND_URL/research/event-study"
+)
+
+echo "-- iter-5: warm-up hits (the 11 not-yet-measured endpoints/pages) --" >&2
+for label in "${NEW_ENDPOINT_ORDER[@]}"; do curl -s -o /dev/null "${NEW_ENDPOINT_URL[$label]}" || true; done
+for label in "${NEW_PAGE_ORDER[@]}"; do curl -s -o /dev/null "${NEW_PAGE_URL[$label]}" || true; done
+
+echo "-- iter-5: warm endpoint latencies (TC-2, TC-5, TC-6, TC-9, TC-10, TC-11, TC-12) --" >&2
+declare -A NEW_ENDPOINT_RESULT=()
+for label in "${NEW_ENDPOINT_ORDER[@]}"; do
+  read -r seconds code <<<"$(_curl_timed "${NEW_ENDPOINT_URL[$label]}")"
+  _require_200 "$label" "$seconds" "$code"
+  NEW_ENDPOINT_RESULT["$label"]="${seconds}|${code}"
+done
+
+echo "-- iter-5: warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity) --" >&2
+declare -A NEW_PAGE_RESULT=()
+for label in "${NEW_PAGE_ORDER[@]}"; do
+  read -r seconds code <<<"$(_curl_timed "${NEW_PAGE_URL[$label]}")"
+  _require_200 "$label (page)" "$seconds" "$code"
+  NEW_PAGE_RESULT["$label"]="${seconds}|${code}"
+done
+
 echo "-- DB capacity snapshot (from GET /api/data's additive 'capacity' field) --" >&2
 data_body=$(curl -s "$BACKEND_URL/api/data")
 db_file_bytes=$(echo "$data_body" | jq -r '.capacity.db_file_bytes')
@@ -188,7 +313,12 @@ host_info="$(uname -srm 2>/dev/null || echo unknown)"
 
 {
   echo ""
-  echo "## Items B/C/D/G/H/K — mechanical backend pass + storage-footprint card (iter-24)"
+  # iter-5: this title used to hardcode "(iter-24)" regardless of which iteration actually ran the
+  # script, so every re-run silently mislabeled its own fresh measurements as iter-24's (iter-25's own
+  # dev handoff had to work around this by transcribing to a scratch file instead of appending
+  # directly). Fixed here: the title now carries the real measurement timestamp instead of a frozen
+  # iteration number — the "items B/C/D/G/H/K" methodology reference is historical and stays accurate.
+  echo "## Mechanical backend + page pass — items B/C/D/G/H/K methodology, re-measured $timestamp"
   echo ""
   echo "Measured $timestamp on this host ($host_info) via \`scripts/measure-perf.sh\` against PROD MODE"
   echo "(\`start-backend.sh\`/\`start-frontend.sh\`, backend :${BACKEND_PORT} / frontend :${FRONTEND_PORT})."
@@ -224,4 +354,42 @@ host_info="$(uname -srm 2>/dev/null || echo unknown)"
   echo ""
 } >> "$OUT_FILE"
 
+# iter-5 (J-06 capstone): a SEPARATE, freshly-dated section for the boot timing + the 7
+# previously-unmeasured pages — appended to the SAME file (TC-15: no second budgets artifact anywhere).
+{
+  echo ""
+  echo "## J-06 capstone — boot-to-health + the 7 previously-unmeasured pages (iter-5)"
+  echo ""
+  echo "Measured $timestamp on this host ($host_info) via \`scripts/measure-perf.sh\` (extended this"
+  echo "iteration) against PROD MODE (\`start-backend.sh\`/\`start-frontend.sh\`, backend"
+  echo ":${BACKEND_PORT} / frontend :${FRONTEND_PORT})."
+  echo ""
+  echo "**TC-1 — backend cold-boot wall time (process start -> first \`GET /api/health\` HTTP 200):**"
+  echo ""
+  echo "${boot_line}"
+  echo ""
+  echo "**Warm endpoint latencies (TC-2, TC-5, TC-6, TC-9, TC-10, TC-11, TC-12 — generic <= ${DEFAULT_API_BUDGET_S}s"
+  echo "API budget, matching this file's existing \`/api/stocks\`/\`/api/data\` budgets):**"
+  echo ""
+  echo "| Endpoint | Wall time | Budget | Holds? |"
+  echo "|---|---|---|---|"
+  for label in "${NEW_ENDPOINT_ORDER[@]}"; do
+    IFS='|' read -r seconds code <<<"${NEW_ENDPOINT_RESULT[$label]}"
+    holds=$(awk "BEGIN {print ($seconds <= $DEFAULT_API_BUDGET_S) ? \"yes\" : \"NO\"}")
+    echo "| \`${label}\` | ${seconds}s | <= ${DEFAULT_API_BUDGET_S} s | ${holds} (HTTP ${code}) |"
+  done
+  echo ""
+  echo "**Warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity —"
+  echo "TC-2's Dashboard TTI budget is <= 3 s; the rest share the generic <= ${DEFAULT_PAGE_BUDGET_S}s page budget):**"
+  echo ""
+  echo "| Page | Wall time | Budget | Holds? |"
+  echo "|---|---|---|---|"
+  for label in "${NEW_PAGE_ORDER[@]}"; do
+    IFS='|' read -r seconds code <<<"${NEW_PAGE_RESULT[$label]}"
+    holds=$(awk "BEGIN {print ($seconds <= $DEFAULT_PAGE_BUDGET_S) ? \"yes\" : \"NO\"}")
+    echo "| \`${label}\` | ${seconds}s | <= ${DEFAULT_PAGE_BUDGET_S} s | ${holds} (HTTP ${code}) |"
+  done
+  echo ""
+} >> "$OUT_FILE"
+
 echo "== appended measurements to $OUT_FILE ==" >&2
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 310 ++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |   6 +
 runs/goal-session-ops-hardening/trace/.next-step  |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |   3 +
 4 files changed, 320 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
