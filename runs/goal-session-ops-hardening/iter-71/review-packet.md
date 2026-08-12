# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index f9a9291d..cc1a91da 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -57,6 +57,17 @@ functions, the SAME one endpoint, no second implementation. Under the new cached
 `preflight_s` (above) time a cache-dict read, not a compute call — near-zero in steady state (TC-7), which
 is what keeps this endpoint answering promptly during a heavy background aggregate warm (J-07 step 2). The
 three DB reads below are unaffected (out of scope — iter-69's attribution never implicated them).
+
+ops-hardening iter-71 (J-07 closure) additively extends this SAME endpoint with `stale_for_s: float>=0` —
+seconds since the served readiness/preflight payload was computed (0 when computed synchronously for this
+request). `app.engine.readiness.get_readiness_and_preflight` now stamps every cached tick and falls back to
+a synchronous compute once a cache entry's age would exceed `readiness.max_stale_intervals ×
+readiness.refresh_interval_seconds` — the never-serve-arbitrarily-stale-data bound that closes iter-70's
+own named gap (a wedged/dead background-refresh tick thread could otherwise serve a frozen "ready" state
+forever). Also assigns `cached = None` explicitly in the readiness-fetch except block below (reviewer/audit
+MINOR from iter-70) so the preflight-fallback branch's later `cached["preflight"]` read is never an
+implicitly-unbound local — same degrade-on-error behavior, just no longer relying on an incidental
+`UnboundLocalError` being swallowed by that branch's own broad `except`.
 """
 from __future__ import annotations
 
@@ -163,6 +174,10 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
         cached = get_readiness_and_preflight(session, engine=get_engine(), config=cfg)
         readiness = cached["readiness"]
     except Exception:  # pragma: no cover - never let a readiness error blank the health probe
+        # ops-hardening iter-71 (reviewer/audit MINOR from iter-70): explicit, not implicitly-unbound --
+        # the preflight-fallback branch below reads `cached` next, and leaving it undefined here relied on
+        # an UnboundLocalError being silently caught by that branch's own broad `except Exception`.
+        cached = None
         readiness = {
             "state": "unavailable",
             "detail": None,
@@ -189,6 +204,11 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
         }
     preflight_s = (time.monotonic() - _t_preflight_start) if watchdog_active else None
 
+    # ops-hardening iter-71 (J-07 closure): the staleness-bound diagnostic -- a bare dict-key read off the
+    # SAME `cached` payload fetched above (no second call). `cached` is `None` only on the readiness-fetch
+    # failure path above, where nothing was computed for THIS request either -- 0.0 is the honest value.
+    stale_for_s = cached.get("stale_for_s", 0.0) if cached is not None else 0.0
+
     # ops-hardening iter-68 (J-07): the third sample, handler_compute_s -- t_handler_start (above) to
     # HERE, immediately before the response is constructed/returned, after every readiness/preflight
     # computation and DB read above (all already error-guarded, so this line is always reached whenever
@@ -236,4 +256,7 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
         # iter-33 (J-20): the single daily preflight verdict (additive) -- the layout-level
         # PreflightBanner's ONLY read path (see app.engine.readiness.compute_preflight).
         "preflight": preflight,
+        # ops-hardening iter-71 (J-07 closure): seconds since this payload was computed (0 when computed
+        # synchronously for THIS request) -- see app.engine.readiness.get_readiness_and_preflight.
+        "stale_for_s": stale_for_s,
     }
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index cebf864d..c86ac09d 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -589,16 +589,24 @@ class ReadinessCfg(BaseModel):
         config fixture predating this field still loads unchanged — the established `extra="allow"`/
         back-compat-default convention this class already uses, mirroring `StartupCfg`'s own
         `background_compute_history_size` default).
+      - `max_stale_intervals` (ops-hardening iter-71, J-07 closure) — the staleness bound on the SAME
+        cache: `app.engine.readiness.get_readiness_and_preflight` falls back to a synchronous
+        `compute_readiness`/`compute_preflight` call whenever the cached entry's age would exceed
+        `max_stale_intervals × refresh_interval_seconds` — the never-serve-arbitrarily-stale-data guard
+        for a wedged/dead background-refresh tick thread (iter-70's own named gap: "before this round the
+        endpoint could be slow but never wrong; it can now be fast and wrong"). MUST be `> 0`. Defaults to
+        `3` (same back-compat-default convention as `refresh_interval_seconds` above).
 
     Boot-validated: `severity` must name exactly `{servability, freshness, integrity, drift}` with every
-    value one of `"degraded"`/`"no-go"`, covering both, and `refresh_interval_seconds` must be `> 0`. An
-    invalid block raises `ConfigError`, never a silent default."""
+    value one of `"degraded"`/`"no-go"`, covering both, and `refresh_interval_seconds`/`max_stale_intervals`
+    must both be `> 0`. An invalid block raises `ConfigError`, never a silent default."""
 
     model_config = ConfigDict(extra="allow")
     freshness_max_age_days: int
     severity: dict[str, str]
     verdict_history_path: str
     refresh_interval_seconds: float = 0.5
+    max_stale_intervals: int = 3
 
     @model_validator(mode="after")
     def _validate(self) -> "ReadinessCfg":
@@ -617,6 +625,8 @@ class ReadinessCfg(BaseModel):
             )
         if self.refresh_interval_seconds <= 0:
             raise ValueError("readiness.refresh_interval_seconds must be > 0")
+        if self.max_stale_intervals <= 0:
+            raise ValueError("readiness.max_stale_intervals must be > 0")
         return self
 
 
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index 319b0074..b2f4a548 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -37,6 +37,7 @@ import json
 import logging
 import os
 import threading
+import time
 from datetime import date as date_cls
 from pathlib import Path
 from typing import Optional
@@ -552,7 +553,12 @@ def _tick_and_cache(session: Session, cfg: Config, engine=None) -> Optional[dict
     interleave a compute or double-write a verdict transition (TC-5). Degrade-on-error (TC-6): a raising
     compute is caught, logged, and leaves the PRIOR cache (if any) completely untouched -- the caller keeps
     serving the last-known-good value, never a blank/partial one. Returns the fresh payload on success, or
-    `None` when the tick itself failed."""
+    `None` when the tick itself failed.
+
+    ops-hardening iter-71 (J-07 closure): the published payload carries `computed_at`, a `time.monotonic()`
+    stamp of THIS tick -- the staleness-bound input `get_readiness_and_preflight` below measures a cache
+    entry's age against. Monotonic (never wall-clock) so a system clock adjustment can never manufacture or
+    hide staleness."""
     global _READINESS_CACHE
     with _TICK_LOCK:
         try:
@@ -560,25 +566,16 @@ def _tick_and_cache(session: Session, cfg: Config, engine=None) -> Optional[dict
         except Exception:  # pragma: no cover - a tick failure must never crash the thread or blank the cache
             _log_tick_failure("readiness refresh tick failed (non-fatal) -- serving last-known-good cache")
             return None
+        payload = dict(payload, computed_at=time.monotonic())
         _READINESS_CACHE = payload
         return payload
 
 
-def get_readiness_and_preflight(session: Session, engine=None, config: Optional[Config] = None) -> dict:
-    """The SINGLE read accessor `GET /api/health` calls: serves `{"readiness": ..., "preflight": ...}`
-    from the shared cache. Cold-start fallback (TC-1): before the background thread's first tick
-    completes (boot, or a direct `health(session)` call with no thread running), computes once
-    synchronously here -- byte-identical to the pre-cache per-request behavior, so boot-time and
-    unit-test call shapes are unaffected. Never raises: even a first-ever tick failure (e.g. DB
-    unreachable at boot) degrades to the SAME honest fallback shape `compute_readiness`/`compute_preflight`
-    already produce on their own internal errors -- `GET /api/health` never serves an undefined value."""
-    cache = _READINESS_CACHE
-    if cache is not None:
-        return cache
-    cfg = config or get_config()
-    ticked = _tick_and_cache(session, cfg, engine=engine)
-    if ticked is not None:
-        return ticked
+def _unavailable_fallback() -> dict:
+    """The honest failure-fallback shape `get_readiness_and_preflight` serves when NEITHER a cache entry
+    NOR a synchronous tick is available (e.g. the very first call in a process whose first tick itself
+    failed). A FRESH dict every call (never a shared/reused reference) -- `stale_for_s: 0.0` (honestly
+    "just computed," never a stale reading, since no real payload exists to measure an age against)."""
     return {
         "readiness": {
             "state": UNAVAILABLE,
@@ -593,9 +590,42 @@ def get_readiness_and_preflight(session: Session, engine=None, config: Optional[
             "as_of": None,
             "reference": None,
         },
+        "stale_for_s": 0.0,
     }
 
 
+def get_readiness_and_preflight(session: Session, engine=None, config: Optional[Config] = None) -> dict:
+    """The SINGLE read accessor `GET /api/health` calls: serves `{"readiness": ..., "preflight": ...,
+    "stale_for_s": ...}` from the shared cache. Cold-start fallback (TC-1): before the background thread's
+    first tick completes (boot, or a direct `health(session)` call with no thread running), computes once
+    synchronously here -- byte-identical to the pre-cache per-request behavior, so boot-time and
+    unit-test call shapes are unaffected. Never raises: even a first-ever tick failure (e.g. DB
+    unreachable at boot) degrades to the SAME honest fallback shape `compute_readiness`/`compute_preflight`
+    already produce on their own internal errors -- `GET /api/health` never serves an undefined value.
+
+    ops-hardening iter-71 (J-07 closure) -- staleness bound: a wedged/dead background-refresh tick thread
+    must never let this accessor go on serving an ever-more-frozen "ready" state forever (iter-70's own
+    named gap: "before this round the endpoint could be slow but never wrong; it can now be fast and
+    wrong"). `stale_for_s` -- seconds since the served payload was computed (0 when computed synchronously
+    for THIS call) -- is always in the returned dict. When the cached entry's age would exceed
+    `readiness.max_stale_intervals x readiness.refresh_interval_seconds`, this falls back to the SAME
+    synchronous compute the cold-start path already uses, instead of serving the stale entry -- mirrors
+    the existing cold-start fallback exactly; no second implementation."""
+    cfg = config or get_config()
+    cache = _READINESS_CACHE
+    if cache is not None:
+        stale_for_s = time.monotonic() - cache["computed_at"]
+        max_stale_s = cfg.readiness.max_stale_intervals * cfg.readiness.refresh_interval_seconds
+        if stale_for_s <= max_stale_s:
+            return dict(cache, stale_for_s=stale_for_s)
+        # Falls through to the synchronous-fallback path below -- the cache entry EXISTS but has aged past
+        # the bound (e.g. the background thread has stopped ticking), so it is never served as-is.
+    ticked = _tick_and_cache(session, cfg, engine=engine)
+    if ticked is not None:
+        return dict(ticked, stale_for_s=0.0)
+    return _unavailable_fallback()
+
+
 def trigger_readiness_refresh(session: Session, config: Optional[Config] = None, engine=None) -> None:
     """Immediate-refresh trigger (TC-4): called from `data_manager._refresh_ingest_aggregates`'s own
     finalize hook -- the SAME finalize hook every other ingest-time aggregate already refreshes from --
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 9f3ee9c5..906af9b7 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1463,6 +1463,94 @@ def test_finalize_hook_triggers_immediate_readiness_refresh(finalize_hook_engine
         assert calls[0] is session  # the SAME session -- sees this job's just-persisted rows immediately
 
 
+@pytest.fixture
+def state_flip_engine(tmp_path):
+    """A DB shaped to force a REAL `readiness.state` transition when a finalize hook lands a new run for a
+    benchmark bar that had already outrun the prior run -- the SAME B3-fix condition `compute_readiness`
+    checks (`readiness.py`'s `awaiting_snapshot` derivation): `d0` has both a bar and a persisted run
+    (servable); `d1`'s SPY bar already exists but NO run exists for it yet -- exactly the
+    `awaiting_snapshot` condition, computed honestly with no finalize hook having run at all."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'state_flip.db'}")
+    create_db_and_tables(engine)
+    d0 = date(2024, 3, 4)
+    d1 = date(2024, 3, 5)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d0, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        run0 = ScannerRun(
+            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run0)
+        session.commit()
+        session.refresh(run0)
+        session.add(ScannerResult(
+            run_id=run0.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        # d1: the benchmark's own bar has already landed, but no run exists for it yet.
+        session.add(DailyPrice(symbol="SPY", date=d1, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    return engine, d0, d1
+
+
+def test_finalize_hook_state_flip_served_by_health_within_one_tick(state_flip_engine, tmp_path, monkeypatch):
+    """ops-hardening iter-71 (audit T1) -- composes TC-4's two previously-separate halves into ONE real
+    integration path: the finalize hook's immediate-refresh trigger (test_finalize_hook_triggers_
+    immediate_readiness_refresh above, which only proves the trigger FIRES) actually publishes a REAL
+    `readiness.state` transition (`awaiting_snapshot` -> a servable state) to the cache, and `GET
+    /api/health` served right after reflects the NEW state -- not the stale pre-finalize one -- within
+    one tick (here, immediately: the trigger runs synchronously inside the finalize hook, before it
+    returns, so no wait is needed for the periodic tick to catch up)."""
+    import app.api.health as health_module
+    import app.engine.readiness as readiness_module
+
+    engine, d0, d1 = state_flip_engine
+    cfg = load_config()
+    monkeypatch.setenv(readiness_module.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness_module.stop_readiness_refresh()
+    readiness_module.reset_readiness_refresh_cache()
+    try:
+        # Prime the cache with the PRE-finalize state -- `awaiting_snapshot`, since d1's benchmark bar has
+        # already landed but no run exists for it yet (no finalize hook has run at this point).
+        with Session(engine) as session:
+            before = readiness_module.get_readiness_and_preflight(session, engine=engine, config=cfg)
+        assert before["readiness"]["state"] == readiness_module.AWAITING_SNAPSHOT
+
+        # The ingest job creates the new run for d1 (what a real backfill does BEFORE calling the finalize
+        # hook), then the finalize hook runs -- firing the immediate-refresh trigger at its end (for real,
+        # unlike the mocked-trigger test above).
+        with Session(engine) as session:
+            run1 = ScannerRun(
+                asof_date=d1, created_at=datetime(2024, 3, 5), provider="seed", benchmark="SPY",
+                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run1)
+            session.commit()
+            session.refresh(run1)
+            session.add(ScannerResult(
+                run_id=run1.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+                setup_status="Actionable", rank=1, record_json="{}",
+            ))
+            session.commit()
+            prog = JobProgress(job_id="state-flip-probe", kind="backfill", start=d1, end=d1)
+            prog.new_snapshot_dates = [d1]
+            data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+        # GET /api/health (direct handler call) reflects the NEW state immediately -- the finalize hook's
+        # trigger already published it; no periodic-tick wait needed.
+        with Session(engine) as session:
+            body = health_module.health(session)
+        assert body["readiness"] != readiness_module.AWAITING_SNAPSHOT
+        assert body["readiness"] in {readiness_module.READY, readiness_module.INITIALIZING}
+    finally:
+        readiness_module.stop_readiness_refresh()
+        readiness_module.reset_readiness_refresh_cache()
+
+
 def test_finalize_hook_index_series_memory_error_isolated_and_not_reported(
     finalize_hook_engine, monkeypatch
 ):
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index eb8ed0a2..1c8e29dd 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -1,8 +1,10 @@
 """GET /api/health via FastAPI TestClient against the loaded temp DB."""
 from __future__ import annotations
 
-from datetime import date
+import time
+from datetime import date, datetime
 
+import pytest
 from fastapi.testclient import TestClient
 from sqlalchemy import event, func, select as sa_select
 from sqlmodel import Session, select
@@ -213,6 +215,49 @@ def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded
     assert body["background_compute"] == {"active": [], "recent_outcomes": []}
 
 
+@pytest.fixture
+def tiny_engine(tmp_path):
+    """A tiny, fast, dedicated DB (one bar + one run) for tests that call `health(session)` DIRECTLY --
+    not through `TestClient(main.app)`'s lifespan, so no process-engine registration is needed. Keeps the
+    readiness-cache-focused tests below independent of the committed-seed `loaded_engine` fixture (~1h to
+    build) — they only exercise the cache read/fallback path, not real seed data."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'tiny_health.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 3, 4)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.add(ScannerRun(
+            asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+    return engine
+
+
+def test_health_preflight_fallback_assigns_cached_none_explicitly_no_name_error(tiny_engine, monkeypatch):
+    """ops-hardening iter-71 (TC-3, reviewer/audit MINOR from iter-70): when the readiness-cache read
+    itself fails, `health.py`'s except block assigns `cached = None` explicitly (not implicitly-unbound)
+    before the preflight-fallback branch reads `cached` next. This exact branch never raises `NameError`
+    (or anything else), and the response's `preflight` field equals the documented NO-GO fallback shape."""
+    import app.api.health as health_module
+
+    def _boom(session, engine=None, config=None):
+        raise RuntimeError("simulated readiness-cache read failure")
+
+    monkeypatch.setattr(health_module, "get_readiness_and_preflight", _boom)
+    with Session(tiny_engine) as session:
+        body = health(session)  # must not raise NameError -- exercises the preflight-fallback branch
+    assert body["preflight"] == {
+        "verdict": "NO-GO",
+        "reasons": ["The preflight check itself failed to run."],
+        "components": {},
+        "as_of": None,
+        "reference": None,
+    }
+    assert body["stale_for_s"] == 0.0
+
+
 # ==================================================================================================
 # iter-24 fast-platform item G — cheap readiness probe (memoized cadence dates + one grouped query)
 # ==================================================================================================
@@ -397,3 +442,73 @@ def test_health_repeated_calls_serve_cache_not_recompute(loaded_engine, tmp_path
             health(session)
 
     assert calls == {"readiness": 0, "preflight": 0}
+
+
+# ==================================================================================================
+# ops-hardening iter-71 (J-07 closure) -- `GET /api/health` gains the additive `stale_for_s: float>=0`
+# diagnostic field, and a wedged/dead tick thread falls back to a synchronous compute past the bound.
+# ==================================================================================================
+def test_health_carries_additive_stale_for_s_field(loaded_engine, tmp_path, monkeypatch):
+    """`stale_for_s` is ADDITIVE -- every existing key stays present -- and is a real non-negative float,
+    0 immediately after a cold-start synchronous compute (this call's own fresh tick)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness.reset_readiness_refresh_cache()
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    existing_keys = {
+        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
+        "readiness", "readiness_detail", "warmup", "background_compute", "poll_interval_seconds",
+        "poll_idle_interval_seconds", "preflight",
+    }
+    assert existing_keys <= set(body)
+    assert isinstance(body["stale_for_s"], (int, float))
+    assert body["stale_for_s"] >= 0.0
+
+
+def test_health_stale_for_s_reflects_cache_age_within_the_bound(tiny_engine, tmp_path, monkeypatch):
+    """A repeated call against an already-warm (fresh) cache reports a real, small `stale_for_s` -- not
+    always 0 -- proving the value is measured against the cache entry's actual age, not hard-coded."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness.reset_readiness_refresh_cache()
+    with Session(tiny_engine) as session:
+        health(session)  # warms the cache via the cold-start path
+        time.sleep(0.05)
+        body = health(session)
+    cfg = load_config()
+    threshold = cfg.readiness.max_stale_intervals * cfg.readiness.refresh_interval_seconds
+    assert 0.0 < body["stale_for_s"] < threshold
+
+
+def test_health_falls_back_to_synchronous_compute_past_the_staleness_bound(tiny_engine, tmp_path, monkeypatch):
+    """TC-1 at the handler level: a cache entry backdated past `max_stale_intervals x
+    refresh_interval_seconds` (simulating a wedged/dead tick thread) is never served -- `GET /api/health`
+    falls back to a synchronous compute instead, and the response's `stale_for_s` is 0."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness.reset_readiness_refresh_cache()
+    with Session(tiny_engine) as session:
+        health(session)  # warms the cache via the cold-start path
+    assert readiness._READINESS_CACHE is not None
+
+    cfg = load_config()
+    threshold = cfg.readiness.max_stale_intervals * cfg.readiness.refresh_interval_seconds
+    stale = dict(readiness._READINESS_CACHE)
+    stale["computed_at"] -= (threshold + 10.0)
+    readiness._READINESS_CACHE = stale
+
+    # Counts `compute_preflight` (invoked exactly once per tick) rather than `compute_readiness` --
+    # `compute_preflight` itself calls `compute_readiness` a second time internally for servability, so
+    # counting `compute_readiness` directly would over-count by 2x per tick (see test_readiness.py's
+    # sibling test for the same note).
+    calls = {"n": 0}
+    real_compute_preflight = readiness.compute_preflight
+
+    def _counting(*a, **kw):
+        calls["n"] += 1
+        return real_compute_preflight(*a, **kw)
+
+    monkeypatch.setattr(readiness, "compute_preflight", _counting)
+    with Session(tiny_engine) as session:
+        body = health(session)
+
+    assert calls["n"] == 1  # exactly one synchronous fallback tick fired -- the stale entry was never served
+    assert body["stale_for_s"] == 0.0
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index 6699a29a..df60c6ac 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -713,6 +713,32 @@ def test_readiness_cfg_rejects_nonpositive_refresh_interval():
         )
 
 
+# ==================================================================================================
+# ops-hardening iter-71 (J-07 closure) -- the readiness-cache staleness bound's config knob.
+# ==================================================================================================
+def test_readiness_cfg_max_stale_intervals_defaults_to_three():
+    from app.config import ReadinessCfg
+
+    cfg = ReadinessCfg(
+        freshness_max_age_days=5,
+        severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
+        verdict_history_path="x.jsonl",
+    )
+    assert cfg.max_stale_intervals == 3
+
+
+def test_readiness_cfg_rejects_nonpositive_max_stale_intervals():
+    from app.config import ReadinessCfg
+
+    with pytest.raises(ValueError, match="max_stale_intervals must be > 0"):
+        ReadinessCfg(
+            freshness_max_age_days=5,
+            severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
+            verdict_history_path="x.jsonl",
+            max_stale_intervals=0,
+        )
+
+
 # ==================================================================================================
 # ops-hardening iter-70 (J-07) -- bounded-interval background-refresh cache: cold-start fallback (TC-1),
 # steady-state cache-read vs. recompute (TC-2), concurrency/atomic-swap, degrade-on-error (TC-6), the
@@ -812,7 +838,11 @@ def test_readiness_cache_steady_state_reads_do_not_recompute(cache_engine, confi
     readiness.stop_readiness_refresh()  # before the NEXT (interval-away) tick could fire and get counted
 
     assert calls == {"readiness": 0, "preflight": 0}
-    assert all(r == results[0] for r in results)
+    # ops-hardening iter-71: `stale_for_s` is a REAL elapsed-time measurement (re-derived every call
+    # against `computed_at`), so it legitimately differs call-to-call even when served from the SAME
+    # cache entry -- compare the entry's actual content (readiness/preflight), not the whole dict.
+    assert all(r["readiness"] == results[0]["readiness"] for r in results)
+    assert all(r["preflight"] == results[0]["preflight"] for r in results)
 
 
 def test_readiness_cache_degrades_to_last_known_good_on_tick_failure(cache_engine, config, monkeypatch, tmp_path):
@@ -836,7 +866,12 @@ def test_readiness_cache_degrades_to_last_known_good_on_tick_failure(cache_engin
 
     with Session(cache_engine) as session:
         served = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
-    assert served == good  # a reader still gets the last-known-good value -- HTTP 200 shape intact
+    # a reader still gets the last-known-good value -- HTTP 200 shape intact. `stale_for_s` (ops-hardening
+    # iter-71) is compared separately: it's an ADDITIVE, real elapsed-time reading, not part of `good`'s
+    # own identity (`_tick_and_cache`'s raw return has no `stale_for_s` key at all).
+    assert served["readiness"] == good["readiness"]
+    assert served["preflight"] == good["preflight"]
+    assert served["stale_for_s"] >= 0.0
 
     monkeypatch.setattr(readiness, "compute_readiness", real_compute_readiness)  # the failure clears
     with Session(cache_engine) as session:
@@ -962,6 +997,104 @@ def test_start_readiness_refresh_is_single_flight(cache_engine, config):
     assert readiness._REFRESH_THREAD.is_alive() is False
 
 
+# ==================================================================================================
+# ops-hardening iter-71 (J-07 closure) -- the readiness-cache staleness bound: a wedged/dead
+# background-refresh tick thread must never let `get_readiness_and_preflight` go on serving an
+# ever-more-frozen cache entry forever. TC-1 (synchronous fallback past the bound) and TC-2 (a fresh
+# entry is still served as-is, with a real `stale_for_s` reading) both live here.
+# ==================================================================================================
+def test_readiness_cache_serves_fresh_entry_with_stale_for_s_below_threshold(cache_engine, config, monkeypatch, tmp_path):
+    """TC-2: a cache entry younger than `max_stale_intervals x refresh_interval_seconds` is served AS-IS
+    -- `stale_for_s` is a real, non-negative measurement strictly below that threshold, and NO synchronous
+    compute fires (call-count instrumentation, not just output-value equality)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    with Session(cache_engine) as session:
+        readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    calls = {"n": 0}
+    real_compute_readiness = readiness.compute_readiness
+
+    def _counting(*a, **kw):
+        calls["n"] += 1
+        return real_compute_readiness(*a, **kw)
+
+    monkeypatch.setattr(readiness, "compute_readiness", _counting)
+    with Session(cache_engine) as session:
+        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+
+    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
+    assert calls["n"] == 0  # served straight from the cache -- no fallback compute
+    assert 0.0 <= result["stale_for_s"] < threshold
+
+
+def test_readiness_cache_falls_back_to_synchronous_compute_past_the_staleness_bound(
+    cache_engine, config, monkeypatch, tmp_path
+):
+    """TC-1: given the readiness background-refresh tick thread effectively stopped (a test hook backdates
+    the cache entry's `computed_at`, simulating a wedged/dead tick thread with no live thread required),
+    when the entry's age exceeds `max_stale_intervals x refresh_interval_seconds` and a client calls
+    `GET /api/health`'s read path, then the response is produced by a SYNCHRONOUS `compute_readiness` call
+    (proven by call-count instrumentation, not the stale cache) and `stale_for_s` equals 0 -- never served
+    indefinitely stale."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    with Session(cache_engine) as session:
+        readiness._tick_and_cache(session, config, engine=cache_engine)
+    assert readiness._READINESS_CACHE is not None
+
+    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
+    stale = dict(readiness._READINESS_CACHE)
+    stale["computed_at"] -= (threshold + 10.0)  # well past the bound
+    readiness._READINESS_CACHE = stale
+
+    # Counts `compute_preflight`, not `compute_readiness` -- `compute_preflight` itself calls
+    # `compute_readiness` a second time internally (servability reuses it verbatim), so counting
+    # `compute_readiness` directly would over-count by 2x per tick. `compute_preflight` is invoked
+    # exactly once per tick, making it the clean "did exactly one synchronous tick fire" signal.
+    calls = {"n": 0}
+    real_compute_preflight = readiness.compute_preflight
+
+    def _counting(*a, **kw):
+        calls["n"] += 1
+        return real_compute_preflight(*a, **kw)
+
+    monkeypatch.setattr(readiness, "compute_preflight", _counting)
+    with Session(cache_engine) as session:
+        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+
+    assert calls["n"] == 1  # exactly one synchronous fallback tick fired -- the stale entry was never served
+    assert result["stale_for_s"] == 0.0
+    # the fallback also re-published a FRESH cache entry (mirrors the cold-start path) -- a later reader
+    # within the bound serves this fresh entry, not the stale one that triggered the fallback.
+    assert readiness._READINESS_CACHE["computed_at"] > stale["computed_at"]
+
+
+def test_readiness_cache_staleness_bound_never_raises_when_the_fallback_tick_also_fails(
+    cache_engine, config, monkeypatch, tmp_path
+):
+    """A stale entry past the bound whose fallback compute ALSO fails degrades to the SAME honest
+    unavailable/NO-GO shape the cold-start path already produces -- never raises, never serves the
+    stale entry as a fallback of last resort (the whole point of the bound is to never do that)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    with Session(cache_engine) as session:
+        readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
+    stale = dict(readiness._READINESS_CACHE)
+    stale["computed_at"] -= (threshold + 10.0)
+    readiness._READINESS_CACHE = stale
+
+    def _boom(session, engine=None, config=None):
+        raise RuntimeError("simulated fallback compute failure")
+
+    monkeypatch.setattr(readiness, "compute_readiness", _boom)
+    with Session(cache_engine) as session:
+        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+
+    assert result["readiness"]["state"] == "unavailable"
+    assert result["preflight"]["verdict"] == "NO-GO"
+    assert result["stale_for_s"] == 0.0
+
+
 # ==================================================================================================
 # ops-hardening iter-70 AUDIT (finding B1) -- a tick failure whose OWN `logger.exception` render also
 # raises (the `MemoryError`-under-an-exhausted-`ulimit -v` class `data_manager._log_isolation_failure`
diff --git a/config.yaml b/config.yaml
index 291f5b77..e20a38d2 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1346,6 +1346,7 @@ readiness:
     drift: degraded
   verdict_history_path: runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl
   refresh_interval_seconds: 0.5    # ops-hardening iter-70 (J-07): background-refresh cache tick cadence -- well under startup.health_poll_interval_seconds (2.0s)
+  max_stale_intervals: 3    # ops-hardening iter-71 (J-07 closure): synchronous-fallback threshold -- a cache entry older than max_stale_intervals x refresh_interval_seconds (1.5s) is never served; GET /api/health falls back to a synchronous compute instead
 
 # ----------------------------------------------------------------------------------------
 # iter-42 (J-100) CONSUMED — bounded-resource SERVER ops guards. The SINGLE source of the uvicorn
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-ops-hardening/telemetry.jsonl   | 7 +++++++
 runs/goal-session-ops-hardening/trace/.next-step  | 2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl | 1 +
 3 files changed, 9 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
