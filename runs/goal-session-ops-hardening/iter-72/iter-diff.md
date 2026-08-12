# Iteration diff (bounded)

Files changed: 11. Shown in full: 11.

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 51c2df27..5ca1946b 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -109,7 +109,14 @@ def data_overview(
     J-93/J-94: `?as_of=` is the SINGLE GLOBAL as-of (the same control every date-scoped page reads — NOT a
     second date state). The coverage block's dynamic `universe_count` + per-date `universe_diagnostic` are
     resolved at this date. An absent/invalid `as_of` gracefully falls back to the latest stored run date
-    (coverage still serves — never a 4xx for a bad as-of here, since this is descriptive metadata)."""
+    (coverage still serves — never a 4xx for a bad as-of here, since this is descriptive metadata).
+
+    ops-hardening iter-72 (TC-10): a test-only fault-injection probe (`TRENDORA_FAULT_INJECT_MEMORY_ERROR=
+    data_overview_endpoint`, a no-op in every real deployment — see `data_manager._fault_inject_memory_
+    error`) fires first, deliberately UNGUARDED here (no surrounding try/except, unlike every other call
+    site this SAME hook arms), so an armed test drill makes this endpoint genuinely fail (FastAPI's default
+    500) — the mechanism this iteration's `/data` honest-fallback-message evidence is captured against."""
+    data_manager._fault_inject_memory_error("data_overview_endpoint")
     cfg = get_config()
     jp = cfg.data_manager.job_progress
     resolved_asof: Optional[date_cls] = None
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index cc1a91da..ca54c788 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -60,14 +60,21 @@ three DB reads below are unaffected (out of scope — iter-69's attribution neve
 
 ops-hardening iter-71 (J-07 closure) additively extends this SAME endpoint with `stale_for_s: float>=0` —
 seconds since the served readiness/preflight payload was computed (0 when computed synchronously for this
-request). `app.engine.readiness.get_readiness_and_preflight` now stamps every cached tick and falls back to
-a synchronous compute once a cache entry's age would exceed `readiness.max_stale_intervals ×
-readiness.refresh_interval_seconds` — the never-serve-arbitrarily-stale-data bound that closes iter-70's
-own named gap (a wedged/dead background-refresh tick thread could otherwise serve a frozen "ready" state
-forever). Also assigns `cached = None` explicitly in the readiness-fetch except block below (reviewer/audit
-MINOR from iter-70) so the preflight-fallback branch's later `cached["preflight"]` read is never an
-implicitly-unbound local — same degrade-on-error behavior, just no longer relying on an incidental
-`UnboundLocalError` being swallowed by that branch's own broad `except`.
+request). `app.engine.readiness.get_readiness_and_preflight` stamps every cached tick. Also assigns
+`cached = None` explicitly in the readiness-fetch except block below (reviewer/audit MINOR from iter-70) so
+the preflight-fallback branch's later `cached["preflight"]` read is never an implicitly-unbound local —
+same degrade-on-error behavior, just no longer relying on an incidental `UnboundLocalError` being swallowed
+by that branch's own broad `except`.
+
+ops-hardening iter-72 (J-07 self-inflicted-stall fix) REMOVES the synchronous-compute fallback iter-71 added
+for a cache entry aged past `readiness.max_stale_intervals × readiness.refresh_interval_seconds`: a real
+concurrent-load drill showed that fallback was itself slow under the SAME DB-pool starvation that ages the
+cache, so every caller queued behind `_TICK_LOCK` waiting on it, self-amplifying a 165s/58-of-900-non-answer
+outage. Once a cache entry exists it is now ALWAYS served as-is, with its real (uncapped) `stale_for_s` —
+disclosed-stale-serve, never a blocking recompute — mirroring iter-71's own lesson. The cold-start path
+(no tick has ever published in this process) is unchanged: still a synchronous compute, still
+`stale_for_s: 0.0`. See `app.engine.readiness.get_readiness_and_preflight`'s own NOTE for the full
+honesty-over-availability rationale.
 """
 from __future__ import annotations
 
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index c86ac09d..c953b34d 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -589,13 +589,15 @@ class ReadinessCfg(BaseModel):
         config fixture predating this field still loads unchanged — the established `extra="allow"`/
         back-compat-default convention this class already uses, mirroring `StartupCfg`'s own
         `background_compute_history_size` default).
-      - `max_stale_intervals` (ops-hardening iter-71, J-07 closure) — the staleness bound on the SAME
-        cache: `app.engine.readiness.get_readiness_and_preflight` falls back to a synchronous
+      - `max_stale_intervals` (ops-hardening iter-71, J-07 closure) — introduced as the staleness bound on
+        the SAME cache: `app.engine.readiness.get_readiness_and_preflight` fell back to a synchronous
         `compute_readiness`/`compute_preflight` call whenever the cached entry's age would exceed
-        `max_stale_intervals × refresh_interval_seconds` — the never-serve-arbitrarily-stale-data guard
-        for a wedged/dead background-refresh tick thread (iter-70's own named gap: "before this round the
-        endpoint could be slow but never wrong; it can now be fast and wrong"). MUST be `> 0`. Defaults to
-        `3` (same back-compat-default convention as `refresh_interval_seconds` above).
+        `max_stale_intervals × refresh_interval_seconds`. ops-hardening iter-72 REMOVED that synchronous
+        fallback (a real concurrent-load drill showed it self-amplified a live outage — see
+        `get_readiness_and_preflight`'s own NOTE) — a cache entry is now ALWAYS served as-is, however old,
+        so this field is currently unconsumed by that read path. Left typed/validated (never deleted) since
+        no journey retires the tunable itself; a future consumer may reintroduce a bound using it. MUST be
+        `> 0`. Defaults to `3` (same back-compat-default convention as `refresh_interval_seconds` above).
 
     Boot-validated: `severity` must name exactly `{servability, freshness, integrity, drift}` with every
     value one of `"degraded"`/`"no-go"`, covering both, and `refresh_interval_seconds`/`max_stale_intervals`
@@ -1991,13 +1993,20 @@ class DatabaseCfg(BaseModel):
     """iter-24 fast-platform item B — `pragmas` (sqlite-only connection tuning) + the pool sizing
     `app.db.make_engine` applies (`pool_size`/`max_overflow`, config-keyed — no inline literal). Both
     default-populated so a config/fixture predating them still loads and serves today's SQLAlchemy
-    defaults would otherwise leave implicit (`QueuePool` sizes to 5/10 by default; here made explicit)."""
+    defaults would otherwise leave implicit (`QueuePool` sizes to 5/10 by default; here made explicit).
+
+    ops-hardening iter-72: the defaults were 10/20 (sum 30) — SMALLER than `ServerOpsCfg.limit_concurrency`'s
+    own default (64), so a fixture/config predating this pair (and relying on these defaults) would starve
+    the DB pool under uvicorn's admitted concurrency exactly like the real `config.yaml` did before this
+    iteration's fix (see `Config._db_pool_covers_server_concurrency`). Raised to 24/44 (sum 68) to mirror
+    the real `config.yaml` value and keep every predating fixture passing that cross-field invariant by
+    construction, not by accident."""
 
     model_config = ConfigDict(extra="allow")
     url: str = Field(min_length=1)
     pragmas: DatabasePragmasCfg = Field(default_factory=DatabasePragmasCfg)
-    pool_size: int = 10
-    max_overflow: int = 20
+    pool_size: int = 24
+    max_overflow: int = 44
 
     @model_validator(mode="after")
     def _validate(self) -> "DatabaseCfg":
@@ -2765,6 +2774,26 @@ class Config(BaseModel):
             raise ValueError(f"methodology threshold refs are unresolvable: {sorted(set(unresolved))}")
         return self
 
+    @model_validator(mode="after")
+    def _db_pool_covers_server_concurrency(self) -> "Config":
+        """ops-hardening iter-72 (TC-1) — `database.pool_size + database.max_overflow` (the SQLAlchemy
+        `QueuePool`'s total connection ceiling, `app.db.make_engine`) must cover
+        `server.limit_concurrency` (uvicorn's own max simultaneous in-flight connections). A smaller pool
+        starves the (limit_concurrency - pool_total) extra concurrent requests: each blocks up to
+        `pool_timeout` and then raises `sqlalchemy.exc.TimeoutError: QueuePool limit ... overflow ...
+        timeout ...` — the exact live failure this boot check now prevents by construction (iter-71's real
+        drill: `config.yaml`'s prior 10+20=30 sum against a 64 limit_concurrency produced that error plus a
+        165s `GET /api/health` outage). Cross-checked here (not on `DatabaseCfg`) because a sub-model
+        cannot see `server` — same reason as the pattern/invalidation `ma_period` checks above."""
+        pool_total = self.database.pool_size + self.database.max_overflow
+        if pool_total < self.server.limit_concurrency:
+            raise ValueError(
+                f"database.pool_size + database.max_overflow ({pool_total}) must be >= "
+                f"server.limit_concurrency ({self.server.limit_concurrency}) — a smaller pool starves "
+                "concurrent requests under uvicorn's own admitted concurrency (QueuePool timeout)"
+            )
+        return self
+
 
 def _merge_committed_universe(data: dict, universe_json: Path) -> None:
     """Grow `universe.symbols` from the committed `universe.json` screen result — keeping ONE universe
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index af1b1535..18d297e4 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3468,9 +3468,18 @@ _FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
 # release isolate-and-continue site (J-07; the confirmed iter-58 crash frame,
 # `_regime_lab_members_by_horizon` retaining every horizon's pool at once). Reaches this hook via the SAME
 # lazy `from app.engine import data_manager` import `compute_factor_lab_all` already uses.
+# ops-hardening iter-72: "data_overview_endpoint" added — a DIFFERENT KIND of site than every one above
+# (which each sit INSIDE an isolate-and-continue `except MemoryError` block, so the fault degrades a
+# category to honestly-omitted and never escapes). This one fires at the very TOP of `GET /api/data`'s
+# handler (`app.api.data.data_overview`), deliberately UNGUARDED — a plain request-path function with no
+# surrounding try/except — so the injected error propagates out to FastAPI's default exception handling
+# (an honest 500), proving the FRONTEND's own existing error-boundary fallback (never a blank crash
+# overlay) renders correctly when the API call itself fails (TC-10; mirrors this SAME hook's established
+# "arm at the exact site under test" convention, applied to a request-path failure instead of an ingest
+# isolation boundary).
 _FAULT_INJECT_SITES = frozenset({
     "forward_aggregates", "drawdown_expectations", "backfill_worker", "factor_lab_all",
-    "coverage_membership_timeline", "market_phase", "regime_lab",
+    "coverage_membership_timeline", "market_phase", "regime_lab", "data_overview_endpoint",
 })
 
 
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index b2f4a548..27b21086 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -558,9 +558,35 @@ def _tick_and_cache(session: Session, cfg: Config, engine=None) -> Optional[dict
     ops-hardening iter-71 (J-07 closure): the published payload carries `computed_at`, a `time.monotonic()`
     stamp of THIS tick -- the staleness-bound input `get_readiness_and_preflight` below measures a cache
     entry's age against. Monotonic (never wall-clock) so a system clock adjustment can never manufacture or
-    hide staleness."""
+    hide staleness.
+
+    ops-hardening iter-72 (TC-4, post-lock recheck): a caller that had to genuinely QUEUE behind another
+    thread's in-flight tick (the periodic thread's own tick racing an ingest finalize hook's
+    `trigger_readiness_refresh`, the exact scenario TC-5 above already serializes -- or two concurrent
+    cold-start callers before any tick has ever published) may find, once it finally acquires the lock,
+    that the entry it was queued behind has JUST been published fresh enough to reuse -- reusing it skips a
+    fully redundant second compute. Contention is detected explicitly (a non-blocking `acquire` first; only
+    a caller whose non-blocking attempt FAILED -- i.e. someone else already held the lock -- takes the
+    recheck branch below) rather than merely comparing timestamps, so an ordinary UNCONTENDED call (the
+    common case: no other thread mid-tick) always computes its own fresh entry exactly as before, even if
+    an earlier successful tick happens to still be recent -- this keeps the existing degrade-on-error
+    contract intact (TC-6: a solo re-tick after a prior success must still actually attempt its OWN compute,
+    so a now-broken producer is truly exercised, not silently skipped). `cfg` supplies the SAME
+    `readiness.refresh_interval_seconds` a fresh periodic tick would itself be scheduled against -- a
+    just-published entry younger than one interval is, by construction, not stale enough to be worth a
+    second caller recomputing again right now. Same producers, same lock, no interface/return-shape
+    change."""
     global _READINESS_CACHE
-    with _TICK_LOCK:
+    contended = not _TICK_LOCK.acquire(blocking=False)
+    if contended:
+        _TICK_LOCK.acquire()
+    try:
+        if contended:
+            recheck = _READINESS_CACHE
+            if recheck is not None:
+                age_s = time.monotonic() - recheck["computed_at"]
+                if age_s <= cfg.readiness.refresh_interval_seconds:
+                    return recheck
         try:
             payload = _compute_tick(session, cfg, engine=engine)
         except Exception:  # pragma: no cover - a tick failure must never crash the thread or blank the cache
@@ -569,6 +595,8 @@ def _tick_and_cache(session: Session, cfg: Config, engine=None) -> Optional[dict
         payload = dict(payload, computed_at=time.monotonic())
         _READINESS_CACHE = payload
         return payload
+    finally:
+        _TICK_LOCK.release()
 
 
 def _unavailable_fallback() -> dict:
@@ -603,23 +631,35 @@ def get_readiness_and_preflight(session: Session, engine=None, config: Optional[
     unreachable at boot) degrades to the SAME honest fallback shape `compute_readiness`/`compute_preflight`
     already produce on their own internal errors -- `GET /api/health` never serves an undefined value.
 
-    ops-hardening iter-71 (J-07 closure) -- staleness bound: a wedged/dead background-refresh tick thread
-    must never let this accessor go on serving an ever-more-frozen "ready" state forever (iter-70's own
-    named gap: "before this round the endpoint could be slow but never wrong; it can now be fast and
-    wrong"). `stale_for_s` -- seconds since the served payload was computed (0 when computed synchronously
-    for THIS call) -- is always in the returned dict. When the cached entry's age would exceed
-    `readiness.max_stale_intervals x readiness.refresh_interval_seconds`, this falls back to the SAME
-    synchronous compute the cold-start path already uses, instead of serving the stale entry -- mirrors
-    the existing cold-start fallback exactly; no second implementation."""
+    ops-hardening iter-71 (J-07 closure) introduced `stale_for_s` -- seconds since the served payload was
+    computed (0 when computed synchronously for THIS call) -- always present in the returned dict.
+
+    ops-hardening iter-72 (J-07 self-inflicted-stall fix) -- REMOVES the synchronous-fallback branch iter-71
+    added for a cache entry aged past `readiness.max_stale_intervals x readiness.refresh_interval_seconds`:
+    once a cache entry exists, it is now ALWAYS served as-is, with its real (uncapped) `stale_for_s` --
+    never capped/reset to 0.0 and never traded for a blocking recompute, no matter how old. See the NOTE at
+    the `_tick_and_cache` call site below for why. The cold-start path (`cache is None` -- no tick has EVER
+    published in this process) is UNCHANGED: still a synchronous compute here, still `stale_for_s: 0.0`."""
     cfg = config or get_config()
     cache = _READINESS_CACHE
     if cache is not None:
+        # Disclosed-stale-serve, unconditionally: the cache entry's true elapsed age, however large, is
+        # returned as-is -- never traded for a synchronous recompute past some bound. See the NOTE below.
         stale_for_s = time.monotonic() - cache["computed_at"]
-        max_stale_s = cfg.readiness.max_stale_intervals * cfg.readiness.refresh_interval_seconds
-        if stale_for_s <= max_stale_s:
-            return dict(cache, stale_for_s=stale_for_s)
-        # Falls through to the synchronous-fallback path below -- the cache entry EXISTS but has aged past
-        # the bound (e.g. the background thread has stopped ticking), so it is never served as-is.
+        return dict(cache, stale_for_s=stale_for_s)
+    # NOTE (ops-hardening iter-72, honesty-over-availability): iter-71's OWN synchronous fallback past the
+    # staleness bound was the self-inflicted half of that round's live 165s/58-of-900-non-answer outage --
+    # under the SAME DB-pool starvation that ages the cache in the first place, a synchronous
+    # compute_readiness/compute_preflight call is itself slow (it does real DB reads), so EVERY caller that
+    # found the cache stale queued behind `_TICK_LOCK` waiting for that slow recompute, serializing what
+    # should have been independent fast reads and self-amplifying the very stall the bound was meant to
+    # guard against. Disclosed-stale-serve (above) never takes that lock at all on the read path -- a
+    # reader always gets an immediate answer, honestly labeled with its real age via `stale_for_s`, which is
+    # a truer trade than either (a) blocking availability for a "fresher" number under exactly the load
+    # that made it stale, or (b) silently capping `stale_for_s` to hide how old the value really is. The
+    # ONLY synchronous compute left in this function is the cold-start path immediately below, which runs
+    # at most once per process (before the background thread's first tick has ever published anything to
+    # be stale) -- never on the hot, already-cached read path a heavy background job's load lands on.
     ticked = _tick_and_cache(session, cfg, engine=engine)
     if ticked is not None:
         return dict(ticked, stale_for_s=0.0)
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 073c0b7c..32f73fcf 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -180,6 +180,42 @@ def test_get_data_overview_coverage_from_storage_empty_db_still_graceful(tmp_pat
     assert payload["coverage"]["price_start"] is None
 
 
+# ==================================================================================================
+# ops-hardening iter-72 (TC-10) — a test-only fault-injection probe makes `GET /api/data` itself fail
+# (never mocked away, unlike the other tests above), mirroring J-07's own `TRENDORA_FAULT_INJECT_MEMORY_
+# ERROR` convention — see `data_manager._fault_inject_memory_error` / `_FAULT_INJECT_SITES`. Unlike every
+# other site that hook arms (each isolate-and-continue guarded, so the injected error never escapes), this
+# site is deliberately UNGUARDED at the top of `data_overview` — the injected error propagates out exactly
+# like a real failure would, so FastAPI would answer with a 500 for a real `GET /api/data` request. The
+# frontend's OWN existing honest-fallback rendering on that 500 ("Dataset coverage could not load from the
+# API. No figures are shown rather than fabricated", `apps/frontend/app/data/page.tsx`) is captured as
+# LIVE browser evidence by QA armed with this SAME env var — this test proves the backend half of that
+# mechanism: the endpoint genuinely raises when armed, and is unaffected (byte-identical) when disarmed.
+# ==================================================================================================
+def test_get_data_overview_fault_injection_probe_makes_the_endpoint_raise(data_api_engine, monkeypatch):
+    """Armed (`TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint`): `data_overview` raises
+    `MemoryError` before doing any other work — the exact failure `GET /api/data` would surface to the
+    frontend as a 500. Disarmed: the SAME call serves its normal payload, unaffected."""
+    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "data_overview_endpoint")
+    with Session(data_api_engine) as session:
+        with pytest.raises(MemoryError):
+            data_overview(session=session)
+
+    monkeypatch.delenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", raising=False)
+    with Session(data_api_engine) as session:
+        payload = data_overview(session=session)  # disarmed — serves normally, never a leftover raise
+    assert "coverage" in payload
+
+
+def test_get_data_overview_fault_injection_probe_is_a_noop_for_an_unrelated_site(data_api_engine, monkeypatch):
+    """Arming a DIFFERENT site (e.g. `factor_lab_all`) never affects `GET /api/data` — the probe is
+    site-scoped, not a blanket kill-switch."""
+    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "factor_lab_all")
+    with Session(data_api_engine) as session:
+        payload = data_overview(session=session)  # unaffected — a different site was armed
+    assert "coverage" in payload
+
+
 def test_get_data_overview_carries_capacity_snapshot(data_api_engine):
     """Item K (iter-24 fast-platform pass): GET /api/data carries an additive `capacity` key — the DB
     storage-footprint snapshot (file size + row counts for the three largest tables), exact on the tiny
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 186d0812..55c84198 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -956,3 +956,49 @@ def test_registry_config_omitted_inside_a_present_evidence_block(tmp_path):
     cfg = load_config(_write(tmp_path, data))
     assert cfg.evidence.registry.enforce is False
     assert cfg.evidence.registry.path.endswith("pre-registrations.jsonl")
+
+
+# ==================================================================================================
+# ops-hardening iter-72 (TC-1) — `database.pool_size + database.max_overflow` must cover
+# `server.limit_concurrency`. iter-71's real concurrent-load drill reproduced the live consequence of a
+# too-small pool: `sqlalchemy.exc.TimeoutError: QueuePool limit ... overflow ... timeout ...` plus a 165s
+# `GET /api/health` outage. This boot check turns that arithmetic mismatch into a loud `ConfigError`
+# instead of a live failure discovered under load.
+# ==================================================================================================
+def test_real_config_db_pool_covers_server_concurrency():
+    """The real committed `config.yaml` satisfies the invariant with real headroom (not a razor edge)."""
+    cfg = load_config()
+    pool_total = cfg.database.pool_size + cfg.database.max_overflow
+    assert pool_total >= cfg.server.limit_concurrency
+    assert pool_total - cfg.server.limit_concurrency >= 4  # real margin, not merely "just enough"
+
+
+def test_minimal_config_defaults_satisfy_pool_invariant(tmp_path):
+    """A config/fixture that omits `database.pool_size`/`max_overflow` AND `server.limit_concurrency`
+    entirely (relying on both sections' class defaults — the MINIMAL_VALID shape most inline test fixtures
+    across the suite use) still loads: the class defaults themselves satisfy the invariant, so this cross-
+    field check never breaks a fixture that predates it."""
+    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
+    assert cfg.database.pool_size + cfg.database.max_overflow >= cfg.server.limit_concurrency
+
+
+def test_db_pool_below_server_concurrency_raises(tmp_path):
+    """An explicit pool sum smaller than `server.limit_concurrency` fails the boot loudly — the exact
+    arithmetic mismatch iter-71 found in the real config.yaml, reproduced here as a targeted fixture."""
+    data = copy.deepcopy(MINIMAL_VALID)
+    data["database"]["pool_size"] = 10
+    data["database"]["max_overflow"] = 20
+    data["server"] = {"limit_concurrency": 64}
+    with pytest.raises(ConfigError, match="database.pool_size \\+ database.max_overflow"):
+        load_config(_write(tmp_path, data))
+
+
+def test_db_pool_exactly_covering_server_concurrency_is_valid(tmp_path):
+    """The boundary case — the pool sum EXACTLY equal to `limit_concurrency` — is valid (the invariant is
+    `>=`, not a strict `>`)."""
+    data = copy.deepcopy(MINIMAL_VALID)
+    data["database"]["pool_size"] = 40
+    data["database"]["max_overflow"] = 24
+    data["server"] = {"limit_concurrency": 64}
+    cfg = load_config(_write(tmp_path, data))
+    assert cfg.database.pool_size + cfg.database.max_overflow == cfg.server.limit_concurrency
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index df60c6ac..487b5d55 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -1027,15 +1027,20 @@ def test_readiness_cache_serves_fresh_entry_with_stale_for_s_below_threshold(cac
     assert 0.0 <= result["stale_for_s"] < threshold
 
 
-def test_readiness_cache_falls_back_to_synchronous_compute_past_the_staleness_bound(
+def test_readiness_cache_serves_stale_entry_as_is_past_the_staleness_bound_no_fallback_compute(
     cache_engine, config, monkeypatch, tmp_path
 ):
-    """TC-1: given the readiness background-refresh tick thread effectively stopped (a test hook backdates
-    the cache entry's `computed_at`, simulating a wedged/dead tick thread with no live thread required),
-    when the entry's age exceeds `max_stale_intervals x refresh_interval_seconds` and a client calls
-    `GET /api/health`'s read path, then the response is produced by a SYNCHRONOUS `compute_readiness` call
-    (proven by call-count instrumentation, not the stale cache) and `stale_for_s` equals 0 -- never served
-    indefinitely stale."""
+    """TC-3 (ops-hardening iter-72 rewrite) -- given a cache entry whose age exceeds
+    `max_stale_intervals x refresh_interval_seconds` (a test hook backdates `computed_at`, simulating a
+    wedged/dead tick thread with no live thread required), `get_readiness_and_preflight` returns the
+    cached payload IMMEDIATELY with its real, UNCAPPED `stale_for_s` -- proven by call-count
+    instrumentation that NEITHER `compute_readiness` NOR `compute_preflight` fires synchronously for this
+    call. This REPLACES the iter-71 test of the same scenario (which pinned a synchronous-fallback call
+    past this bound); iter-72 REMOVED that fallback -- a real concurrent-load drill showed it was itself
+    slow under the SAME DB-pool starvation that ages the cache, serializing every caller behind
+    `_TICK_LOCK` and self-amplifying a live 165s/58-of-900-non-answer outage. A stale-but-existing cache
+    entry is now ALWAYS served as-is, never traded for a blocking recompute -- see
+    `get_readiness_and_preflight`'s own NOTE for the full rationale."""
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
     with Session(cache_engine) as session:
         readiness._tick_and_cache(session, config, engine=cache_engine)
@@ -1043,56 +1048,160 @@ def test_readiness_cache_falls_back_to_synchronous_compute_past_the_staleness_bo
 
     threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
     stale = dict(readiness._READINESS_CACHE)
-    stale["computed_at"] -= (threshold + 10.0)  # well past the bound
+    stale["computed_at"] -= (threshold + 10.0)  # well past the old bound -- no longer special-cased at all
     readiness._READINESS_CACHE = stale
 
-    # Counts `compute_preflight`, not `compute_readiness` -- `compute_preflight` itself calls
-    # `compute_readiness` a second time internally (servability reuses it verbatim), so counting
-    # `compute_readiness` directly would over-count by 2x per tick. `compute_preflight` is invoked
-    # exactly once per tick, making it the clean "did exactly one synchronous tick fire" signal.
-    calls = {"n": 0}
+    calls = {"readiness": 0, "preflight": 0}
+    real_compute_readiness = readiness.compute_readiness
     real_compute_preflight = readiness.compute_preflight
 
-    def _counting(*a, **kw):
-        calls["n"] += 1
+    def _counting_readiness(*a, **kw):
+        calls["readiness"] += 1
+        return real_compute_readiness(*a, **kw)
+
+    def _counting_preflight(*a, **kw):
+        calls["preflight"] += 1
         return real_compute_preflight(*a, **kw)
 
-    monkeypatch.setattr(readiness, "compute_preflight", _counting)
+    monkeypatch.setattr(readiness, "compute_readiness", _counting_readiness)
+    monkeypatch.setattr(readiness, "compute_preflight", _counting_preflight)
+
     with Session(cache_engine) as session:
         result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
 
-    assert calls["n"] == 1  # exactly one synchronous fallback tick fired -- the stale entry was never served
-    assert result["stale_for_s"] == 0.0
-    # the fallback also re-published a FRESH cache entry (mirrors the cold-start path) -- a later reader
-    # within the bound serves this fresh entry, not the stale one that triggered the fallback.
-    assert readiness._READINESS_CACHE["computed_at"] > stale["computed_at"]
+    assert calls == {"readiness": 0, "preflight": 0}  # no synchronous compute fired -- served straight from cache
+    assert result["readiness"] == stale["readiness"]
+    assert result["preflight"] == stale["preflight"]
+    # the real, UNCAPPED elapsed age -- strictly greater than the old bound, never clamped/reset to 0
+    assert result["stale_for_s"] >= threshold + 10.0
+    # the cache entry itself is left untouched -- no fallback tick silently republished a fresh one over it
+    assert readiness._READINESS_CACHE["computed_at"] == stale["computed_at"]
+
 
+# ==================================================================================================
+# ops-hardening iter-72 (J-07 self-inflicted-stall fix) -- TC-4: `_tick_and_cache`'s post-lock recheck.
+# Two callers racing `_tick_and_cache` (the periodic thread's own scheduled tick vs. an ingest finalize
+# hook's `trigger_readiness_refresh`, or two concurrent cold-start callers before any tick has ever
+# published) must not both pay a full compute: the SECOND to acquire `_TICK_LOCK`, finding an entry the
+# FIRST just published fresh enough to reuse (within one `refresh_interval_seconds`), returns that entry
+# instead of recomputing redundantly.
+# ==================================================================================================
+def test_tick_and_cache_post_lock_recheck_skips_redundant_compute(cache_engine, config, monkeypatch, tmp_path):
+    """A deterministic (non-racy) two-caller contention harness: the FIRST caller is made to block mid-
+    compute (holding `_TICK_LOCK` the whole time) until the test explicitly releases it; the SECOND caller
+    is started only once the first has PROVABLY entered its compute (so its own non-blocking `acquire`
+    attempt is guaranteed to fail -- genuine contention, never a timing guess) and is given a moment to
+    reach its own blocking `acquire()` before the first is released. The second caller must then reuse the
+    entry the first just published, rather than paying its own redundant compute -- proven by call-count
+    instrumentation (exactly ONE underlying tick for two racing callers), not just output equality. Blocks
+    on/counts `compute_preflight`, not `compute_readiness` -- `_compute_tick` calls `compute_readiness`
+    directly AND `compute_preflight` internally reuses it a second time (servability), so
+    `compute_preflight` is the clean "exactly once per tick" signal (mirrors the convention the staleness
+    test above already established)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    real_compute_preflight = readiness.compute_preflight
+    calls = {"n": 0}
+    first_call_started = threading.Event()
+    release_first_call = threading.Event()
 
-def test_readiness_cache_staleness_bound_never_raises_when_the_fallback_tick_also_fails(
+    def _first_blocks_then_real(*a, **kw):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            first_call_started.set()
+            assert release_first_call.wait(timeout=5.0), "test never released the first blocked call"
+        return real_compute_preflight(*a, **kw)
+
+    monkeypatch.setattr(readiness, "compute_preflight", _first_blocks_then_real)
+
+    results = [None, None]
+
+    def _first():
+        with Session(cache_engine) as session:
+            results[0] = readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    t1 = threading.Thread(target=_first)
+    t1.start()
+    assert first_call_started.wait(timeout=5.0), "the first tick never entered its compute"
+    # t1 now holds _TICK_LOCK, blocked inside its own compute -- t2's non-blocking acquire below is
+    # GUARANTEED to fail (genuine contention, not a race).
+
+    def _second():
+        with Session(cache_engine) as session:
+            results[1] = readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    t2 = threading.Thread(target=_second)
+    t2.start()
+    time.sleep(0.1)  # give t2 time to make its own (failing) non-blocking acquire and start queueing
+    release_first_call.set()
+    t1.join(timeout=5.0)
+    t2.join(timeout=5.0)
+
+    assert calls["n"] == 1, (
+        f"expected exactly ONE tick to actually run across both racing callers (the second should reuse "
+        f"the first's fresh publish via the post-lock recheck), got {calls['n']}"
+    )
+    assert results[0] is not None and results[1] is not None
+    assert results[0] == results[1]  # both callers observed the SAME published entry
+
+
+def test_tick_and_cache_post_lock_recheck_does_not_reuse_a_too_old_entry(
     cache_engine, config, monkeypatch, tmp_path
 ):
-    """A stale entry past the bound whose fallback compute ALSO fails degrades to the SAME honest
-    unavailable/NO-GO shape the cold-start path already produces -- never raises, never serves the
-    stale entry as a fallback of last resort (the whole point of the bound is to never do that)."""
+    """The post-lock recheck only reuses an entry fresher than `refresh_interval_seconds`. Deterministic
+    harness: a pre-existing cache entry is already older than the interval; the FIRST caller queues holding
+    the lock but its OWN tick FAILS (never republishing anything), so once the SECOND, genuinely-contended
+    caller finally acquires the lock, the entry it rechecks is STILL that same too-old one -- it must NOT
+    be reused; the second caller computes its own fresh entry instead. Same `compute_preflight` counting
+    convention as the test above."""
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
     with Session(cache_engine) as session:
         readiness._tick_and_cache(session, config, engine=cache_engine)
+    assert readiness._READINESS_CACHE is not None
+    old = dict(readiness._READINESS_CACHE)
+    old["computed_at"] -= (config.readiness.refresh_interval_seconds + 1.0)  # older than one tick interval
+    readiness._READINESS_CACHE = old
 
-    threshold = config.readiness.max_stale_intervals * config.readiness.refresh_interval_seconds
-    stale = dict(readiness._READINESS_CACHE)
-    stale["computed_at"] -= (threshold + 10.0)
-    readiness._READINESS_CACHE = stale
+    real_compute_preflight = readiness.compute_preflight
+    calls = {"n": 0}
+    first_call_started = threading.Event()
+    release_first_call = threading.Event()
 
-    def _boom(session, engine=None, config=None):
-        raise RuntimeError("simulated fallback compute failure")
+    def _first_fails_then_real(*a, **kw):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            first_call_started.set()
+            assert release_first_call.wait(timeout=5.0), "test never released the first blocked call"
+            raise RuntimeError("simulated failure -- the cache is never republished by this tick")
+        return real_compute_preflight(*a, **kw)
 
-    monkeypatch.setattr(readiness, "compute_readiness", _boom)
-    with Session(cache_engine) as session:
-        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+    monkeypatch.setattr(readiness, "compute_preflight", _first_fails_then_real)
 
-    assert result["readiness"]["state"] == "unavailable"
-    assert result["preflight"]["verdict"] == "NO-GO"
-    assert result["stale_for_s"] == 0.0
+    results = [None, None]
+
+    def _first():
+        with Session(cache_engine) as session:
+            results[0] = readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    t1 = threading.Thread(target=_first)
+    t1.start()
+    assert first_call_started.wait(timeout=5.0), "the first tick never entered its compute"
+
+    def _second():
+        with Session(cache_engine) as session:
+            results[1] = readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    t2 = threading.Thread(target=_second)
+    t2.start()
+    time.sleep(0.1)
+    release_first_call.set()
+    t1.join(timeout=5.0)
+    t2.join(timeout=5.0)
+
+    assert results[0] is None  # the first tick's own compute failed -- degrades to None, per TC-6
+    assert calls["n"] == 2  # the second caller did NOT reuse the too-old entry -- it ran its own tick too
+    assert results[1] is not None
+    assert results[1]["computed_at"] > old["computed_at"]  # a genuinely NEW tick ran, not the too-old entry
+    assert readiness._READINESS_CACHE == results[1]
 
 
 # ==================================================================================================
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index 532fb1da..085e3442 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -69,6 +69,10 @@ _HEAVY_TEST_PORT = 18500 + _offset
 _DEV_SCRIPT = REPO_ROOT / "scripts" / "dev.sh"
 _DEVSCRIPT_BACKEND_PORT = 18700 + _offset
 _DEVSCRIPT_FRONTEND_PORT = 19700 + _offset
+# ops-hardening iter-72: a further-distinct pair (never `+ 1`, already used by the host-guard-disabled
+# dev.sh test below) for the server-ops-flags + persistent-logfile dev.sh test (TC-5/TC-6).
+_DEVSCRIPT_OPS_FLAGS_BACKEND_PORT = _DEVSCRIPT_BACKEND_PORT + 2
+_DEVSCRIPT_OPS_FLAGS_FRONTEND_PORT = _DEVSCRIPT_FRONTEND_PORT + 2
 # A FIFTH port for the "caps absent/disabled" launcher test (TC-9) below.
 _NOCAP_TEST_PORT = 18800 + _offset
 # A SIXTH port for the ops-hardening iter-44 ServerOpsCfg-flags fast-shutdown test below.
@@ -1506,6 +1510,95 @@ def test_dev_script_applies_host_guard_caps_to_backend_only(request):
     )
 
 
+# ==================================================================================================
+# ops-hardening iter-72 (TC-5/TC-6) — `scripts/dev.sh`'s backend subshell now mirrors
+# `scripts/start-backend.sh`'s `ServerOpsCfg`-flags wiring (iter-44, `test_start_backend_wires_server_
+# ops_cfg_flags_into_uvicorn_cmdline` above) AND writes to the SAME persistent `logs/backend.log`, closing
+# the gap iter-71's live drill found (a concurrent-load measurement run on dev.sh had neither the uvicorn
+# concurrency/timeout flags nor a durable logfile). Independent of host-guard.env's presence — unlike
+# TC-8/TC-9 above, this test always runs when dev.sh + frontend node_modules are available.
+# ==================================================================================================
+def test_dev_script_wires_server_ops_flags_and_persistent_logfile(request):
+    """TC-5 — `scripts/dev.sh`'s launched uvicorn cmdline carries `--limit-concurrency` /
+    `--timeout-keep-alive` / `--timeout-graceful-shutdown` matching `get_config().server` (config-derived,
+    no magic numbers), and `logs/backend.log` receives a `"dev.sh: launching at"` boot line for THIS spawn.
+    TC-6 — the SAME spawn's frontend (`next dev`) subshell cmdline carries NONE of the three backend-only
+    flags."""
+    if not _DEV_SCRIPT.exists():
+        pytest.skip(f"{_DEV_SCRIPT} not found")
+    if not (REPO_ROOT / "apps" / "frontend" / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed — cannot start the frontend for this check")
+
+    from app.config import get_config
+
+    cfg = get_config()
+    log_offset_before = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
+
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_DEVSCRIPT_OPS_FLAGS_BACKEND_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_DEVSCRIPT_OPS_FLAGS_FRONTEND_PORT)
+    proc = subprocess.Popen(
+        ["bash", str(_DEV_SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+        preexec_fn=os.setsid,  # own process group -> teardown kills the WHOLE tree, not just this PID
+    )
+
+    def _cleanup():
+        try:
+            pgid = os.getpgid(proc.pid)
+        except ProcessLookupError:
+            return
+        for sig in (signal.SIGTERM, signal.SIGKILL):
+            try:
+                os.killpg(pgid, sig)
+            except ProcessLookupError:
+                return
+            deadline = time.monotonic() + 10.0
+            while time.monotonic() < deadline:
+                try:
+                    os.killpg(pgid, 0)
+                except ProcessLookupError:
+                    return
+                time.sleep(0.2)
+        try:
+            proc.wait(timeout=10)
+        except (ChildProcessError, subprocess.TimeoutExpired):
+            pass
+
+    request.addfinalizer(_cleanup)
+
+    _wait_for_health(_DEVSCRIPT_OPS_FLAGS_BACKEND_PORT, timeout=60.0)
+    backend_pid = _owning_pid(_DEVSCRIPT_OPS_FLAGS_BACKEND_PORT)
+
+    # TC-5: the launched uvicorn cmdline carries the 3 config-derived flags.
+    backend_cmdline = _read_proc_cmdline(backend_pid)
+
+    def _flag_value(flag: str) -> str:
+        assert flag in backend_cmdline, f"expected {flag!r} in dev.sh backend cmdline: {backend_cmdline}"
+        return backend_cmdline[backend_cmdline.index(flag) + 1]
+
+    assert _flag_value("--limit-concurrency") == str(cfg.server.limit_concurrency)
+    assert _flag_value("--timeout-keep-alive") == str(cfg.server.timeout_keep_alive_seconds)
+    assert _flag_value("--timeout-graceful-shutdown") == str(cfg.server.graceful_timeout_seconds)
+
+    # TC-5: logs/backend.log received THIS spawn's own dev.sh boot line (sliced from the pre-spawn offset
+    # — the file is persistent/append-mode by design and may already carry earlier boots' content).
+    assert LOG_FILE.exists(), f"expected a persistent logfile at {LOG_FILE}"
+    content = LOG_FILE.read_bytes()[log_offset_before:].decode(errors="replace")
+    assert "dev.sh: launching at" in content
+    assert "Uvicorn running" in content or "Application startup complete" in content
+
+    # TC-6: the SAME spawn's frontend subshell cmdline carries NONE of the 3 backend-only flags.
+    _wait_for_port_answering(_DEVSCRIPT_OPS_FLAGS_FRONTEND_PORT, timeout=90.0)
+    frontend_pid = _owning_pid(_DEVSCRIPT_OPS_FLAGS_FRONTEND_PORT)
+    frontend_cmdline = _read_proc_cmdline(frontend_pid)
+    for flag in ("--limit-concurrency", "--timeout-keep-alive", "--timeout-graceful-shutdown"):
+        assert flag not in frontend_cmdline, (
+            f"dev.sh frontend subshell must never receive {flag!r} — that flag is backend-only uvicorn "
+            f"wiring; got cmdline {frontend_cmdline}"
+        )
+
+
 def test_start_backend_host_guard_absent_starts_cleanly_with_no_caps(tmp_path):
     """TC-9 (absent) — with `HOST_GUARD_ENV_FILE` pointing at a nonexistent path (simulating
     host-guard.env being absent, WITHOUT ever touching the real committed file — see the module
diff --git a/config.yaml b/config.yaml
index e20a38d2..a5fa74fd 100644
--- a/config.yaml
+++ b/config.yaml
@@ -116,10 +116,14 @@ database:
                                  # above (demand-resident, not a virtual reservation) keeps reads fast.
     temp_store: "MEMORY"
   # Pool sized to the uvicorn worker/concurrency shape (the server: block further below allows up to
-  # server.limit_concurrency=64 simultaneous connections; pool_size + max_overflow comfortably covers
-  # that without over-provisioning idle sqlite connections).
-  pool_size: 10
-  max_overflow: 20
+  # server.limit_concurrency=64 simultaneous connections). ops-hardening iter-72: the prior 10+20=30 sum
+  # was SMALLER than limit_concurrency (64) -- the "comfortably covers" claim above was arithmetically
+  # false. A real concurrent-load drill on scripts/dev.sh (iter-71) reproduced the consequence live:
+  # sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached, timeout 30.00, plus a
+  # 165s health-poll outage as pool-starved requests queued behind the readiness cache's own lock. 24+44=68
+  # now clears 64 with real headroom (not a razor edge) without over-provisioning idle sqlite connections.
+  pool_size: 24
+  max_overflow: 44
 
 # ----------------------------------------------------------------------------------------
 # Stock universe: ~120 liquid US common stocks spanning the example themes. The filter
@@ -1346,7 +1350,7 @@ readiness:
     drift: degraded
   verdict_history_path: runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl
   refresh_interval_seconds: 0.5    # ops-hardening iter-70 (J-07): background-refresh cache tick cadence -- well under startup.health_poll_interval_seconds (2.0s)
-  max_stale_intervals: 3    # ops-hardening iter-71 (J-07 closure): synchronous-fallback threshold -- a cache entry older than max_stale_intervals x refresh_interval_seconds (1.5s) is never served; GET /api/health falls back to a synchronous compute instead
+  max_stale_intervals: 3    # ops-hardening iter-71 introduced this as a synchronous-fallback threshold; ops-hardening iter-72 REMOVED that fallback (it self-amplified the live 165s/58-of-900-non-answer outage -- see app.engine.readiness.get_readiness_and_preflight's own NOTE), so this value is CURRENTLY UNCONSUMED by the readiness read path: an existing cache entry is now ALWAYS served as-is with its real, uncapped stale_for_s, never traded for a blocking recompute, however old. Kept typed/validated (never deleted) for a future consumer -- see ReadinessCfg's docstring in apps/backend/app/config.py. [iter-72 AUDIT FIX: this comment still described the removed fallback as live -- the same false-config-comment defect the pool-sizing lines above were corrected for in this SAME iteration]
 
 # ----------------------------------------------------------------------------------------
 # iter-42 (J-100) CONSUMED — bounded-resource SERVER ops guards. The SINGLE source of the uvicorn
diff --git a/incredible_auto_dev/scripts/dev.sh b/incredible_auto_dev/scripts/dev.sh
index e16bec7a..b393e6ba 100755
--- a/incredible_auto_dev/scripts/dev.sh
+++ b/incredible_auto_dev/scripts/dev.sh
@@ -46,16 +46,37 @@ echo "Starting backend on :$BACKEND_PORT ..."
   # MALLOC_ARENA_MAX enforcement (same app.config.get_config() values — computed once here, not a
   # second derivation) in this backend subshell ONLY. The frontend (`next dev`) subshell below is
   # untouched — it needs the address space.
-  read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE <<< "$(
+  #
+  # ops-hardening iter-72: the SAME single read now also pulls `ServerOpsCfg`'s three uvicorn-facing
+  # values (`limit_concurrency` / `timeout_keep_alive_seconds` / `graceful_timeout_seconds`) --
+  # already enforced by scripts/start-backend.sh since iter-44, but never wired into THIS launcher
+  # until now. iter-71's own live concurrent-load drill ran on dev.sh and found neither these flags
+  # nor a persistent logfile present, violating J-04/J-06's own "never dev.sh for a measurement" intent
+  # by denying it the evidence to diagnose what it measured.
+  read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE LIMIT_CONCURRENCY TIMEOUT_KEEP_ALIVE GRACEFUL_TIMEOUT <<< "$(
     .venv/bin/python -c '
 from app.config import get_config
 cfg = get_config()
-print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
+print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max, cfg.server.limit_concurrency, cfg.server.timeout_keep_alive_seconds, cfg.server.graceful_timeout_seconds)
 '
   )"
   ulimit -v $((MEMORY_CAP_MB * 1024))
   export MALLOC_ARENA_MAX="$MALLOC_ARENA_MAX_VALUE"
 
+  # ops-hardening iter-72: a PERSISTENT backend logfile, mirroring scripts/start-backend.sh's EXACT
+  # append-only pattern (same fixed repo-relative path, same header shape — never a second log path).
+  # A dev-mode boot/crash is now discoverable after the launching terminal closes, and a dev-mode drill
+  # has real evidence to diagnose from (iter-71's own outage was measured on this launcher with no
+  # logfile at all).
+  LOG_DIR="$ROOT_DIR/logs"
+  mkdir -p "$LOG_DIR"
+  LOG_FILE="$LOG_DIR/backend.log"
+  {
+    echo ""
+    echo "=== dev.sh: launching at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
+    echo "    port=$BACKEND_PORT memory_cap_mb=$MEMORY_CAP_MB malloc_arena_max=$MALLOC_ARENA_MAX_VALUE"
+  } >> "$LOG_FILE"
+
   # ==== HOST-GUARD (goal.md AG-10) — backend subshell ONLY, DO NOT REMOVE OR WEAKEN ================
   # Same SMT-aware taskset CPU-affinity mask + BLAS/OMP/numexpr thread caps `scripts/start-backend.sh`
   # applies, from the SAME host-guard.env (no second computation of the values). Absent file or
@@ -75,7 +96,11 @@ print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
   fi
   # ==== end HOST-GUARD ==============================================================================
 
-  exec "${HOST_GUARD_CMD_PREFIX[@]}" uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT
+  exec "${HOST_GUARD_CMD_PREFIX[@]}" uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT \
+    --limit-concurrency "$LIMIT_CONCURRENCY" \
+    --timeout-keep-alive "$TIMEOUT_KEEP_ALIVE" \
+    --timeout-graceful-shutdown "$GRACEFUL_TIMEOUT" \
+    >> "$LOG_FILE" 2>&1
 ) &
 BACKEND_PID=$!
 
```
