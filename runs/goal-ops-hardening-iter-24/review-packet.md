# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 14. Shown in full: 13.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (126 diff lines)

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index c1fee1b3..41e99748 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -21,6 +21,13 @@ the sibling `detail` string from `compute_readiness`'s own return (`null` except
 `awaiting_snapshot` state). Previously `compute_readiness`'s dict was discarded down to just
 `readiness["state"]`, so this value was computed correctly but never reached the frontend; this is the
 wiring fix. `readiness` itself stays the SAME bare string it always was (byte-identical contract).
+
+ops-hardening iter-24 (J-09) additively extends this SAME endpoint with the `background_compute` field —
+`compute_readiness`'s own composed `app.engine.forward_testing.get_background_compute_status()` output
+(`{active, recent_outcomes}`), disclosing the in-process historical background-compute dispatch iter-20
+introduced (previously visible only by reconstructing it from raw DB timestamps). Degrades to
+`{"active": [], "recent_outcomes": []}` on any compute error — the SAME degrade-on-error convention as
+`readiness`/`preflight` above, never a blank/fabricated field.
 """
 from __future__ import annotations
 
@@ -59,6 +66,7 @@ def health(session: Session = Depends(get_session)) -> dict:
             "state": "unavailable",
             "detail": None,
             "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
+            "background_compute": {"active": [], "recent_outcomes": []},
         }
 
     # iter-33 (J-20): the single daily preflight verdict (GO/DEGRADED/NO-GO + reasons). A compute error
@@ -94,6 +102,11 @@ def health(session: Session = Depends(get_session)) -> dict:
         # same endpoint -- `compute_readiness` already produced this; it was just never served before.
         "readiness_detail": readiness.get("detail"),
         "warmup": readiness["warmup"],
+        # ops-hardening iter-24 (J-09): the historical background-dispatch registry's disclosure --
+        # `compute_readiness` already composed this (degrading to the honest empty shape on its own
+        # compute error); `.get(...)` with the SAME empty-shape fallback covers the (currently
+        # unreachable, but defensive) case of an older cached/degraded readiness dict predating this key.
+        "background_compute": readiness.get("background_compute", {"active": [], "recent_outcomes": []}),
         # the config-derived poll cadences the frontend badge derives its interval from (no client-side
         # poll literal — anti-goal: No magic numbers). `poll_interval_seconds` is the fast cadence used
         # while warming (so the flip to Ready shows within a poll of completion); `poll_idle_interval_
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 12dda8e3..565baedc 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -520,15 +520,23 @@ class StartupCfg(BaseModel):
         completion — NOT a slow 30 s cycle). MUST be `> 0`.
       - `health_poll_idle_interval_seconds` — the slower cadence the badge MAY back off to once Ready
         (a healthy backend needs no fast poll). MUST be `>= health_poll_interval_seconds`.
+      - `background_compute_history_size` (ops-hardening iter-24, J-09) — how many completed/failed
+        historical background-compute outcomes (`app.engine.forward_testing.get_background_compute_
+        status()`'s `recent_outcomes` ring) are retained, newest-first, before the oldest is dropped.
+        Defaults to `5` (present so a config fixture predating this field still loads unchanged — the
+        established `extra="allow"`/back-compat-default convention this class already uses). MUST be
+        `>= 1`.
 
-    Boot-validated: the budget + both poll intervals MUST be `> 0`, the batch size `>= 1`, and the idle
-    interval `>= the active interval`. An invalid block raises `ConfigError`, never a silent default."""
+    Boot-validated: the budget + both poll intervals MUST be `> 0`, the batch size `>= 1`, the idle
+    interval `>= the active interval`, and `background_compute_history_size >= 1`. An invalid block
+    raises `ConfigError`, never a silent default."""
 
     model_config = ConfigDict(extra="allow")
     readiness_budget_seconds: float
     warmup_batch_size: int
     health_poll_interval_seconds: float
     health_poll_idle_interval_seconds: float
+    background_compute_history_size: int = 5
 
     @model_validator(mode="after")
     def _validate(self) -> "StartupCfg":
@@ -546,6 +554,8 @@ class StartupCfg(BaseModel):
             raise ValueError(
                 "startup.health_poll_idle_interval_seconds must be >= health_poll_interval_seconds"
             )
+        if self.background_compute_history_size < 1:
+            raise ValueError("startup.background_compute_history_size must be >= 1")
         return self
 
 
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 020b3da5..ed60e669 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -1198,8 +1198,19 @@ def forward_aggregates_ingest_cached(
 # `_FORWARD_AGG_INFLIGHT` above, no `threading.Event`/waiter is needed here: the request thread that finds
 # a key already in flight simply does nothing and returns (the already-running dispatch will land on its
 # own; the NEXT request for this identity re-reads `resolved_forward_aggregate_evidence` and sees it).
+#
+# ops-hardening iter-24 (J-09): this SAME guard now additionally carries, per in-flight identity, its
+# `started_at` (set at dispatch time) and live `horizons_done`/`horizons_total` counters (incremented as
+# `_run_historical_forward_aggregates_dispatch` completes each configured horizon below) -- so the value
+# has been in flight since iter-20, made disclosed rather than reconstructed from DB timestamps. The value
+# is a dict now (was a bare set) but the membership check/insert/discard call sites below are otherwise
+# unchanged, and `_HIST_RECENT_OUTCOMES` (also new) is a bounded, newest-first ring of completed/failed
+# dispatch outcomes, capped at `cfg.startup.background_compute_history_size` (never a hardcoded literal).
+# Both structures are read ONLY by the new `get_background_compute_status()` accessor below -- no new
+# lock: both are still guarded by this SAME `_HIST_DISPATCH_LOCK`.
 _HIST_DISPATCH_LOCK = threading.Lock()
-_HIST_DISPATCH_INFLIGHT: set[tuple[str, str]] = set()  # {(asof_key, dataset_version)} dispatched right now
+_HIST_DISPATCH_INFLIGHT: dict[tuple[str, str], dict] = {}  # {(asof_key, dataset_version): {started_at, horizons_done, horizons_total}}
+_HIST_RECENT_OUTCOMES: list[dict] = []  # newest-first, capped at startup.background_compute_history_size
 
 
 def _run_historical_forward_aggregates_dispatch(
@@ -1217,19 +1228,50 @@ def _run_historical_forward_aggregates_dispatch(
     left to crash silently or to propagate to the request thread that triggered the dispatch (TC-7): that
     thread has already returned its response long before this runs. The outer guard's slot is released in
     a `finally` on success AND on failure, so a subsequent request for the SAME identity can always
-    re-dispatch and eventually reach `"ready"` -- never a permanent wedge."""
+    re-dispatch and eventually reach `"ready"` -- never a permanent wedge.
+
+    ops-hardening iter-24 (J-09): additionally increments the guard's own `horizons_done` counter after
+    EACH configured horizon completes (so a live reader sees real progress, never a fabricated estimate),
+    and in the SAME `finally` block appends exactly one newest-first outcome record -- `{asof_key,
+    dataset_version, outcome, started_at, finished_at, duration_ms, reason}` -- to the bounded
+    `_HIST_RECENT_OUTCOMES` ring (capped at `cfg.startup.background_compute_history_size`). `reason` is
+    the caught exception's message when the dispatch failed, else `None`. This is purely additive
+    bookkeeping around the UNCHANGED compute/persist call above -- it changes no computed value."""
+    outcome = "completed"
+    reason: Optional[str] = None
     try:
         with Session(engine) as session:
             for h in cfg.walk_forward.horizons:
                 forward_aggregates_ingest_cached(session, h, cfg, as_of=as_of)
-    except Exception:
+                with _HIST_DISPATCH_LOCK:
+                    slot = _HIST_DISPATCH_INFLIGHT.get(key)
+                    if slot is not None:
+                        slot["horizons_done"] += 1
+    except Exception as exc:
+        outcome = "failed"
+        reason = str(exc)
         logger.exception(
             "historical forward-aggregate background dispatch failed (non-fatal, will re-dispatch on the "
             "next request for this identity, key=%s)", key,
         )
     finally:
         with _HIST_DISPATCH_LOCK:
-            _HIST_DISPATCH_INFLIGHT.discard(key)
+            slot = _HIST_DISPATCH_INFLIGHT.pop(key, None)
+            started_at = slot["started_at"] if slot is not None else datetime.now(timezone.utc)
+            finished_at = datetime.now(timezone.utc)
+            duration_ms = max(int((finished_at - started_at).total_seconds() * 1000), 0)
+            asof_key, dataset_version = key
+            _HIST_RECENT_OUTCOMES.insert(0, {
+                "asof_key": asof_key,
+                "dataset_version": dataset_version,
+                "outcome": outcome,
+                "started_at": _utc_isoformat(started_at),
+                "finished_at": _utc_isoformat(finished_at),
+                "duration_ms": duration_ms,
+                "reason": reason,
+            })
+            cap = cfg.startup.background_compute_history_size
+            del _HIST_RECENT_OUTCOMES[cap:]
 
 
 def ensure_historical_forward_aggregates_dispatched(
@@ -1265,7 +1307,14 @@ def ensure_historical_forward_aggregates_dispatched(
     with _HIST_DISPATCH_LOCK:
         if key in _HIST_DISPATCH_INFLIGHT:
             return  # a dispatch for this EXACT identity is already running -- no-op, never a duplicate
-        _HIST_DISPATCH_INFLIGHT.add(key)
+        # ops-hardening iter-24 (J-09): record the disclosure fields at the EXACT moment the dispatch is
+        # accepted -- `started_at` is the dispatch's own recorded start (never re-derived at read time),
+        # `horizons_done` starts at 0, `horizons_total` is the configured horizon count (never a literal).
+        _HIST_DISPATCH_INFLIGHT[key] = {
+            "started_at": datetime.now(timezone.utc),
+            "horizons_done": 0,
+            "horizons_total": len(cfg.walk_forward.horizons),
+        }
 
     engine = session.get_bind()
     thread = threading.Thread(
@@ -1277,6 +1326,32 @@ def ensure_historical_forward_aggregates_dispatched(
     thread.start()
 
 
+def get_background_compute_status() -> dict:
+    """ops-hardening iter-24 (J-09) -- the SINGLE read-only accessor for the historical dispatch
+    registry's disclosure fields: every currently in-flight `(asof_key, dataset_version)` window (with
+    `elapsed_ms` computed AT READ TIME from its recorded `started_at` -- never a fabricated estimate) plus
+    the bounded, newest-first `recent_outcomes` ring. Reuses the SAME `_HIST_DISPATCH_LOCK` that already
+    guards `_HIST_DISPATCH_INFLIGHT`/`_HIST_RECENT_OUTCOMES` for this tiny read -- no new lock semantics.
+    Never computes/recomputes evidence and issues no query: a pure in-memory snapshot of state this same
+    module's dispatch functions already maintain (composed into `app.engine.readiness.compute_readiness`
+    and served on `GET /api/health`'s new `background_compute` field)."""
+    now = datetime.now(timezone.utc)
+    with _HIST_DISPATCH_LOCK:
+        active = [
+            {
+                "asof_key": asof_key,
+                "dataset_version": dataset_version,
+                "started_at": _utc_isoformat(entry["started_at"]),
+                "elapsed_ms": max(int((now - entry["started_at"]).total_seconds() * 1000), 0),
+                "horizons_done": entry["horizons_done"],
+                "horizons_total": entry["horizons_total"],
+            }
+            for (asof_key, dataset_version), entry in _HIST_DISPATCH_INFLIGHT.items()
+        ]
+        recent_outcomes = list(_HIST_RECENT_OUTCOMES)
+    return {"active": active, "recent_outcomes": recent_outcomes}
+
+
 def _utc_isoformat(value: datetime) -> str:
     """iter-17 (audit B3): `evidence_generated_at` is contracted as an ISO-8601 UTC datetime but was
     serialized via a naive `.isoformat()` (no `Z`/offset) because SQLite reads a stored timestamp back
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index adbaab63..86a2ce26 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -238,9 +238,28 @@ def compute_readiness(
             "Run a backfill or rebuild on Data Manager to produce it."
         )
 
+    # ops-hardening iter-24 (J-09): compose the historical background-dispatch registry's own disclosure
+    # accessor into this SAME return dict, mirroring how `warmup`'s separate-module state is already
+    # composed above -- no new pattern, no DB read added (a pure in-memory registry read). Deferred import
+    # (this module has never imported `forward_testing` before; keeping it local here, rather than at
+    # module level, mirrors `forward_testing.py`'s own established deferred-import convention for its
+    # cross-module `app.engine.research._dataset_version` dependency -- avoid introducing any import-order
+    # coupling between the two engine modules for the sake of one read-only accessor call).
+    #
+    # Scoped try/except (mirrors this function's OWN db_ok guard above): a broken in-memory read here must
+    # degrade ONLY this one field to its honest empty shape -- never blank the rest of the readiness
+    # payload (`state`/`warmup` stay correct even if this accessor were to raise).
+    from app.engine import forward_testing
+
+    try:
+        background_compute = forward_testing.get_background_compute_status()
+    except Exception:  # pragma: no cover - a broken in-memory read must never blank readiness
+        background_compute = {"active": [], "recent_outcomes": []}
+
     return {
         "state": state,
         "detail": detail,
+        "background_compute": background_compute,
         "warmup": {
             "done": done,
             "total": total,
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index c26a9698..186d0812 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -376,6 +376,31 @@ def test_research_read_batch_size_loads_from_real_config():
     assert cfg.research.read_batch_size >= 1
 
 
+# ==================================================================================================
+# ops-hardening iter-24 (J-09) — startup.background_compute_history_size (the recent_outcomes ring cap
+# for the historical background-dispatch disclosure). Validated >= 1; defaults to 5 when the key is
+# absent (MINIMAL_VALID's own `startup` block predates this field, so its continued loading below also
+# proves the default keeps every pre-iter-24 config fixture valid unchanged).
+# ==================================================================================================
+def test_background_compute_history_size_defaults_to_five_when_omitted(tmp_path):
+    """MINIMAL_VALID's `startup` block does not carry this key — it must default to 5, never raise."""
+    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
+    assert cfg.startup.background_compute_history_size == 5
+
+
+def test_background_compute_history_size_below_one_raises(tmp_path):
+    data = copy.deepcopy(MINIMAL_VALID)
+    data["startup"]["background_compute_history_size"] = 0
+    with pytest.raises(ConfigError):
+        load_config(_write(tmp_path, data))
+
+
+def test_background_compute_history_size_loads_from_real_config():
+    cfg = load_config()
+    assert isinstance(cfg.startup.background_compute_history_size, int)
+    assert cfg.startup.background_compute_history_size >= 1
+
+
 # --- J-58: etfs.industry catalog + stock_industries membership validation -------------------
 def test_industry_catalog_loads_with_name_and_description(tmp_path):
     """The new etfs.industry catalog (ticker -> {name, description}) loads and exposes typed access."""
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
index bfa4859e..9e992fee 100644
--- a/apps/backend/tests/test_forward_testing_concurrency.py
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -944,3 +944,183 @@ def test_iter20_historical_dispatch_owner_failure_releases_guard_and_allows_redi
         "expected the forced first failure (call 1) AND at least one successful re-dispatch afterward -- "
         f"got {call_count['n']} total calls"
     )
+
+
+# ======================================================================================================
+# ops-hardening iter-24 (J-09) -- disclosure of the SAME iter-20 dispatch registry above: per-identity
+# `started_at`/`horizons_done`/`horizons_total` bookkeeping, the bounded newest-first `recent_outcomes`
+# ring (config-capped), `get_background_compute_status()`'s shapes, and the failure-releases-guard-and-
+# redispatches contract additionally recording an honest `outcome: "failed"` entry. A NEW, purely additive
+# read surface over `_HIST_DISPATCH_LOCK`/`_HIST_DISPATCH_INFLIGHT`/`_HIST_RECENT_OUTCOMES` -- every test
+# above this banner (the iter-20 keying/dispatch-decision contract) is unaffected by any test below.
+# ======================================================================================================
+def test_get_background_compute_status_shape_is_always_active_and_recent_outcomes_lists():
+    """`get_background_compute_status()` always returns exactly `{"active": [...], "recent_outcomes":
+    [...]}` -- both plain lists, regardless of what the process-lifetime registry currently holds (this
+    module-global registry may carry state left behind by an earlier test in this same process; this pins
+    the SHAPE, not "nothing has ever dispatched")."""
+    import app.engine.forward_testing as forward_testing_module
+
+    status = forward_testing_module.get_background_compute_status()
+    assert set(status) == {"active", "recent_outcomes"}
+    assert isinstance(status["active"], list)
+    assert isinstance(status["recent_outcomes"], list)
+
+
+def test_ensure_dispatch_records_started_at_and_live_horizons_progress(tmp_path, monkeypatch):
+    """TC-2/TC-3 (spec DoD): dispatching a historical as-of records exactly one `active` entry with
+    `horizons_total == len(cfg.walk_forward.horizons)`, `horizons_done` starting at 0 and staying
+    `0 <= horizons_done < horizons_total` while the FIRST configured horizon is still in flight, and a
+    `started_at` matching the dispatch's own recorded start (within 1s). On completion the identity is
+    released from `active` and appears FIRST in `recent_outcomes` with `outcome == "completed"`,
+    `duration_ms >= 0`, and a null `reason`."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'progress.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    asof = date(2021, 5, 1)
+    n_horizons = len(cfg.walk_forward.horizons)
+    assert n_horizons >= 2, "need >= 2 configured horizons to observe live in-between progress"
+
+    first_horizon_started = threading.Event()
+    proceed = threading.Event()
+    call_count = {"n": 0}
+
+    def _fake_ingest(session, h, cfg_, *, as_of):
+        call_count["n"] += 1
+        if call_count["n"] == 1:
+            first_horizon_started.set()
+            proceed.wait(timeout=BOUNDED_TIMEOUT_S)
+
+    monkeypatch.setattr(forward_testing_module, "forward_aggregates_ingest_cached", _fake_ingest)
+
+    before_dispatch = datetime.now(timezone.utc)
+    with Session(engine) as session:
+        forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)
+    assert first_horizon_started.wait(timeout=BOUNDED_TIMEOUT_S), "dispatch never started"
+
+    status = forward_testing_module.get_background_compute_status()
+    matching = [e for e in status["active"] if e["asof_key"] == asof.isoformat()]
+    assert len(matching) == 1, f"expected exactly one active entry for this identity; got {status['active']}"
+    entry = matching[0]
+    assert entry["horizons_total"] == n_horizons
+    assert 0 <= entry["horizons_done"] < entry["horizons_total"]
+    started_at = datetime.fromisoformat(entry["started_at"])
+    assert abs((started_at - before_dispatch).total_seconds()) < 1.0
+    assert entry["elapsed_ms"] >= 0
+
+    proceed.set()  # let the (fake) first horizon finish; the remaining configured horizons are no-ops
+    deadline = time.monotonic() + BOUNDED_TIMEOUT_S
+    while any(e["asof_key"] == asof.isoformat() for e in forward_testing_module.get_background_compute_status()["active"]):
+        assert time.monotonic() < deadline, "dispatch never completed -- treat as a hang"
+        time.sleep(0.02)
+
+    final_status = forward_testing_module.get_background_compute_status()
+    assert not any(e["asof_key"] == asof.isoformat() for e in final_status["active"])
+    outcome = final_status["recent_outcomes"][0]
+    assert outcome["asof_key"] == asof.isoformat()
+    assert outcome["outcome"] == "completed"
+    assert outcome["reason"] is None
+    assert outcome["duration_ms"] >= 0
+    assert call_count["n"] == n_horizons
+
+
+def test_recent_outcomes_ring_capped_and_newest_first(tmp_path, monkeypatch):
+    """TC-9 (spec DoD): once more than `startup.background_compute_history_size` dispatches have
+    completed, `recent_outcomes` never exceeds that cap, and the newest completed dispatch is always
+    first."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'ring.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    cap = cfg.startup.background_compute_history_size
+
+    # Isolate this test from whatever the process-lifetime ring already holds (an established pattern in
+    # this file -- e.g. the save/restore of `compute_forward_aggregates`/`forward_aggregates_ingest_cached`
+    # above); `monkeypatch` restores the original list object on teardown.
+    monkeypatch.setattr(forward_testing_module, "_HIST_RECENT_OUTCOMES", [])
+    monkeypatch.setattr(forward_testing_module, "forward_aggregates_ingest_cached", lambda *a, **k: None)
+
+    n_dispatches = cap + 3
+    for i in range(n_dispatches):
+        asof_key = f"2020-01-{i + 1:02d}"
+        key = (asof_key, "ring-test-v1")
+        with forward_testing_module._HIST_DISPATCH_LOCK:
+            forward_testing_module._HIST_DISPATCH_INFLIGHT[key] = {
+                "started_at": datetime.now(timezone.utc), "horizons_done": 0,
+                "horizons_total": len(cfg.walk_forward.horizons),
+            }
+        forward_testing_module._run_historical_forward_aggregates_dispatch(
+            engine, date.fromisoformat(asof_key), cfg, key
+        )
+
+    status = forward_testing_module.get_background_compute_status()
+    assert len(status["recent_outcomes"]) == cap, (
+        f"expected the ring capped at {cap} after {n_dispatches} completions; got "
+        f"{len(status['recent_outcomes'])}"
+    )
+    assert status["recent_outcomes"][0]["asof_key"] == f"2020-01-{n_dispatches:02d}", (
+        "expected the MOST RECENTLY completed dispatch first (newest-first)"
+    )
+    assert status["recent_outcomes"][-1]["asof_key"] == f"2020-01-{n_dispatches - cap + 1:02d}", (
+        "expected only the cap's-worth of most recent entries retained (oldest beyond the cap dropped)"
+    )
+    assert all(o["outcome"] == "completed" for o in status["recent_outcomes"])
+    assert status["active"] == []
+
+
+def test_historical_dispatch_failure_records_failed_outcome_and_releases_guard_for_redispatch(tmp_path, monkeypatch):
+    """Error-case contract (spec DoD, mirrors the existing TC-7 owner-failure test above): a test-injected
+    exception inside ONE horizon's compute is caught, recorded as `outcome: "failed"` with a non-null
+    `reason`, releases the `active` slot (never a permanent wedge), and a SUBSEQUENT dispatch for the SAME
+    identity runs again and eventually records `outcome: "completed"`."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'failure.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    asof = date(2022, 8, 1)
+
+    call_count = {"n": 0}
+
+    def _fail_once_then_succeed(session, h, cfg_, *, as_of):
+        call_count["n"] += 1
+        if call_count["n"] == 1:
+            raise RuntimeError("forced horizon-compute failure (iter-24 J-09 probe)")
+
+    monkeypatch.setattr(forward_testing_module, "forward_aggregates_ingest_cached", _fail_once_then_succeed)
+
+    with Session(engine) as session:
+        forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)
+
+    # Bounded poll: re-trigger a dispatch whenever the identity is not currently active (a harmless no-op
+    # while one is genuinely in flight; a real re-dispatch the instant the guard clears) -- mirrors the
+    # existing TC-7 test's own convergence-polling idiom above.
+    deadline = time.monotonic() + BOUNDED_TIMEOUT_S
+    while True:
+        status = forward_testing_module.get_background_compute_status()
+        active_match = [e for e in status["active"] if e["asof_key"] == asof.isoformat()]
+        outcomes_for_key = [o for o in status["recent_outcomes"] if o["asof_key"] == asof.isoformat()]
+        if not active_match and any(o["outcome"] == "completed" for o in outcomes_for_key):
+            break
+        assert time.monotonic() < deadline, (
+            f"never converged to a completed re-dispatch within {BOUNDED_TIMEOUT_S}s -- treat as a "
+            f"permanent wedge (last status={status})"
+        )
+        time.sleep(0.02)
+        if not active_match:
+            with Session(engine) as session:
+                forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)
+
+    final_outcomes = [
+        o for o in forward_testing_module.get_background_compute_status()["recent_outcomes"]
+        if o["asof_key"] == asof.isoformat()
+    ]
+    failed = [o for o in final_outcomes if o["outcome"] == "failed"]
+    completed = [o for o in final_outcomes if o["outcome"] == "completed"]
+    assert failed, f"expected at least one recorded failed outcome for this identity; got {final_outcomes}"
+    assert failed[0]["reason"], "a failed outcome must carry a non-null/non-empty reason string"
+    assert completed, "expected the re-dispatch to eventually record a completed outcome (no permanent wedge)"
+    assert call_count["n"] >= 2, "expected the forced first failure AND at least one successful re-dispatch"
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index eaeb141e..137cc6a8 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -87,6 +87,57 @@ def test_health_preflight_is_single_source(loaded_engine, tmp_path, monkeypatch)
     assert served == direct
 
 
+# ==================================================================================================
+# ops-hardening iter-24 (J-09) -- the additive `background_compute` field: the historical background-
+# dispatch registry's disclosure, composed by compute_readiness and re-served here verbatim.
+# ==================================================================================================
+def test_health_carries_additive_background_compute_field(loaded_engine, tmp_path, monkeypatch):
+    """TC-1 shape check: `background_compute` is ADDITIVE -- every existing key stays present, and the
+    new field carries exactly the `{active, recent_outcomes}` shape `get_background_compute_status()`
+    produces (never a second/divergent read path)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    existing_keys = {
+        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
+        "readiness", "readiness_detail", "warmup", "poll_interval_seconds", "poll_idle_interval_seconds",
+        "preflight",
+    }
+    assert existing_keys <= set(body)  # every pre-iter-24 key is still present, unchanged
+    bg = body["background_compute"]
+    assert set(bg) == {"active", "recent_outcomes"}
+    assert isinstance(bg["active"], list)
+    assert isinstance(bg["recent_outcomes"], list)
+
+
+def test_health_background_compute_is_single_source(loaded_engine, tmp_path, monkeypatch):
+    """The served `background_compute` field equals a DIRECT `compute_readiness` call's own composed
+    value for the same session/config -- re-displayed verbatim, never re-derived by the endpoint."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    cfg = load_config()
+    with TestClient(main.app) as client:
+        served = client.get("/api/health").json()["background_compute"]
+    with Session(loaded_engine) as session:
+        direct = readiness.compute_readiness(session, config=cfg)["background_compute"]
+    assert served == direct
+
+
+def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
+    """A total `compute_readiness` failure degrades the WHOLE readiness payload to `unavailable` (the
+    pre-existing convention) -- `background_compute` still serves the honest empty shape, never omitted
+    and never left dangling on a partially-constructed fallback dict."""
+    import app.api.health as health_module
+
+    def _boom(session, engine=None, config=None):
+        raise RuntimeError("simulated readiness failure")
+
+    monkeypatch.setattr(health_module, "compute_readiness", _boom)
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    assert body["readiness"] == "unavailable"
+    assert body["background_compute"] == {"active": [], "recent_outcomes": []}
+
+
 # ==================================================================================================
 # iter-24 fast-platform item G — cheap readiness probe (memoized cadence dates + one grouped query)
 # ==================================================================================================
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index ca9ebb63..3475706d 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -267,18 +267,83 @@ def test_preflight_servability_reuses_compute_readiness_verbatim(loaded_engine,
 
 def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
     """`compute_preflight` is ADDITIVE — `compute_readiness`'s own return shape is untouched BY IT (J-40
-    not regressed): exactly `{"state", "detail", "warmup"}` (ops-hardening iter-4's B3 fix adds the
-    `detail` sibling alongside `state`/`warmup`), `warmup` exactly
-    `{"done","total","status","message"}`. This warmed, fully-caught-up fixture never produces the new
-    `awaiting_snapshot` state, so `detail` is null here (see the dedicated B3 fixture-matrix below for the
-    non-null case)."""
+    not regressed): exactly `{"state", "detail", "warmup", "background_compute"}` (ops-hardening iter-4's
+    B3 fix added the `detail` sibling alongside `state`/`warmup`; ops-hardening iter-24, J-09, additively
+    added `background_compute`), `warmup` exactly `{"done","total","status","message"}`. This warmed,
+    fully-caught-up fixture never produces the new `awaiting_snapshot` state, so `detail` is null here (see
+    the dedicated B3 fixture-matrix below for the non-null case)."""
     cfg = load_config()
     with Session(loaded_engine) as session:
         result = compute_readiness(session, config=cfg)
-    assert set(result) == {"state", "detail", "warmup"}
+    assert set(result) == {"state", "detail", "warmup", "background_compute"}
     assert result["state"] in {"ready", "initializing", "unavailable", "awaiting_snapshot"}
     assert result["detail"] is None
     assert set(result["warmup"]) == {"done", "total", "status", "message"}
+    assert set(result["background_compute"]) == {"active", "recent_outcomes"}
+
+
+# ==================================================================================================
+# ops-hardening iter-24 (J-09) — compute_readiness composes app.engine.forward_testing.
+# get_background_compute_status()'s output into its own return dict as the new `background_compute`
+# sibling key. These tests pin the composition itself (empty/active shapes, degrade-on-error); the
+# registry's OWN bookkeeping (started_at/horizons_done/ring cap/failure path) is covered in
+# test_forward_testing_concurrency.py, the producer module's own test file.
+# ==================================================================================================
+def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine):
+    """A process that has never dispatched a historical background compute reports the honest empty
+    shape -- never omitted, never fabricated non-empty."""
+    import app.engine.forward_testing as forward_testing_module
+
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        # A previous test in this same process could have left dispatch state behind (the registry is a
+        # process-lifetime global, by design -- J-09 step 6). Reading the SAME accessor directly proves
+        # compute_readiness composes it VERBATIM regardless of what it currently holds.
+        direct = forward_testing_module.get_background_compute_status()
+        result = compute_readiness(session, config=cfg)
+    assert result["background_compute"] == direct
+    assert isinstance(result["background_compute"]["active"], list)
+    assert isinstance(result["background_compute"]["recent_outcomes"], list)
+
+
+def test_compute_readiness_composes_background_compute_active_entry(loaded_engine, monkeypatch):
+    """A crafted non-empty `get_background_compute_status()` return is composed VERBATIM (read-only,
+    single source -- no re-derivation) into `compute_readiness`'s own `background_compute` key."""
+    import app.engine.forward_testing as forward_testing_module
+
+    crafted = {
+        "active": [{
+            "asof_key": "2026-01-05", "dataset_version": "r1-f2", "started_at": "2026-01-05T00:00:00+00:00",
+            "elapsed_ms": 1234, "horizons_done": 1, "horizons_total": 5,
+        }],
+        "recent_outcomes": [{
+            "asof_key": "2026-01-04", "dataset_version": "r1-f2", "outcome": "completed",
+            "started_at": "2026-01-04T00:00:00+00:00", "finished_at": "2026-01-04T00:00:05+00:00",
+            "duration_ms": 5000, "reason": None,
+        }],
+    }
+    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", lambda: crafted)
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        result = compute_readiness(session, config=cfg)
+    assert result["background_compute"] == crafted
+
+
+def test_compute_readiness_background_compute_degrades_honestly_on_error(loaded_engine, monkeypatch):
+    """A broken registry read degrades ONLY `background_compute` to the honest empty shape -- it must
+    never blank/raise the surrounding `state`/`warmup` (mirrors this module's own db_ok degrade
+    convention)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    def _boom():
+        raise RuntimeError("simulated registry read failure")
+
+    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", _boom)
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        result = compute_readiness(session, config=cfg)  # must not raise
+    assert result["background_compute"] == {"active": [], "recent_outcomes": []}
+    assert result["state"] in {"ready", "initializing", "unavailable", "awaiting_snapshot"}
 
 
 # ==================================================================================================
diff --git a/apps/frontend/components/health-badge.tsx b/apps/frontend/components/health-badge.tsx
index f4fc3d51..0d767cc8 100644
--- a/apps/frontend/components/health-badge.tsx
+++ b/apps/frontend/components/health-badge.tsx
@@ -20,7 +20,7 @@ type Detail =
  *  re-renders for, without a second polling loop. Re-checks of `state`/`warmup` themselves happen via the
  *  readiness provider's own config-derived poll. */
 export function HealthBadge() {
-  const { state, warmup, loading } = useReadiness();
+  const { state, warmup, backgroundCompute, loading } = useReadiness();
   const [detail, setDetail] = useState<Detail>({ kind: "loading" });
 
   // The context detail (provider / seed date / symbol count / the `awaiting_snapshot` recovery-pointer
@@ -94,9 +94,21 @@ export function HealthBadge() {
     );
   }
 
+  // ops-hardening iter-24 (J-09): the historical background-compute disclosure -- one additional inline
+  // element, present alongside the pill in ANY readiness state whenever a window is in flight, absent
+  // entirely when none is (never replaces/hides the pill above). Reads the SAME shared readiness poll
+  // (`useReadiness()`) -- no second fetch.
+  const activeComputeCount = backgroundCompute?.active.length ?? 0;
+
   return (
     <div className="flex flex-wrap items-center gap-2">
       {pill}
+      {activeComputeCount > 0 ? (
+        <Badge variant="accent" className="num gap-1.5" data-testid="background-compute-indicator">
+          <span className="h-2 w-2 animate-pulse rounded-full bg-accent" aria-hidden />
+          background compute running ({activeComputeCount})
+        </Badge>
+      ) : null}
       {detail.kind === "ok" ? (
         <>
           <Badge variant="accent">provider: {detail.data.provider}</Badge>
diff --git a/apps/frontend/components/readiness-provider.tsx b/apps/frontend/components/readiness-provider.tsx
index f2e66f8a..8928f5a3 100644
--- a/apps/frontend/components/readiness-provider.tsx
+++ b/apps/frontend/components/readiness-provider.tsx
@@ -2,7 +2,13 @@
 
 import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
 
-import { fetchHealth, type PreflightStatus, type ReadinessState, type WarmupProgress } from "@/lib/api";
+import {
+  fetchHealth,
+  type BackgroundComputeStatus,
+  type PreflightStatus,
+  type ReadinessState,
+  type WarmupProgress,
+} from "@/lib/api";
 
 /**
  * Global backend readiness state (iter-28, J-40). A single client context, mounted in the app shell, that
@@ -17,6 +23,10 @@ import { fetchHealth, type PreflightStatus, type ReadinessState, type WarmupProg
  *
  * iter-33 (J-20): the SAME poll also carries the daily preflight verdict (`preflight`) — the layout-level
  * `PreflightBanner`'s ONLY read path (no second fetch, no per-page recompute).
+ *
+ * ops-hardening iter-24 (J-09): the SAME poll also carries `background_compute` — the historical
+ * background-dispatch disclosure (`HealthBadge`'s conditional indicator + `/data`'s
+ * `BackgroundComputePanel` are its ONLY readers; no second fetch, no client-side derivation).
  */
 export interface ReadinessContextValue {
   /** The honest backend readiness state, or null before the first poll resolves. */
@@ -26,6 +36,9 @@ export interface ReadinessContextValue {
   /** The single GO/DEGRADED/NO-GO preflight verdict, or null before the first poll resolves / on a
    *  failed poll (the backend is unreachable — the banner renders its own honest NO-GO in that case). */
   preflight: PreflightStatus | null;
+  /** The historical background-compute dispatch disclosure, or null before the first poll resolves / on
+   *  a failed poll (readers render their own honest empty/idle state in that case — never fabricated). */
+  backgroundCompute: BackgroundComputeStatus | null;
   /** True until the first poll has resolved (so callers can show a neutral "checking" state). */
   loading: boolean;
 }
@@ -41,6 +54,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   const [state, setState] = useState<ReadinessState | null>(null);
   const [warmup, setWarmup] = useState<WarmupProgress | null>(null);
   const [preflight, setPreflight] = useState<PreflightStatus | null>(null);
+  const [backgroundCompute, setBackgroundCompute] = useState<BackgroundComputeStatus | null>(null);
   const [loading, setLoading] = useState(true);
   // the config-derived cadences (seconds) from the latest payload; refs so the polling loop reads the
   // freshest value without re-subscribing.
@@ -59,6 +73,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setState(data.readiness);
         setWarmup(data.warmup);
         setPreflight(data.preflight);
+        setBackgroundCompute(data.background_compute);
         // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
         activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
         idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
@@ -69,6 +84,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setState("unavailable"); // honest — never a fabricated ok
         setWarmup(null);
         setPreflight(null); // honest — the banner renders its own NO-GO for a null preflight, never blank
+        setBackgroundCompute(null); // honest — readers render their own empty/idle state, never fabricated
         nextDelay = activeMs.current; // keep retrying at the active cadence until the backend answers
       } finally {
         if (active) {
@@ -86,8 +102,8 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   }, []);
 
   const value = useMemo<ReadinessContextValue>(
-    () => ({ state, warmup, preflight, loading }),
-    [state, warmup, preflight, loading],
+    () => ({ state, warmup, preflight, backgroundCompute, loading }),
+    [state, warmup, preflight, backgroundCompute, loading],
   );
 
   return <ReadinessContext.Provider value={value}>{children}</ReadinessContext.Provider>;
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 0e760a86..ac60778e 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -150,6 +150,40 @@ export interface PreflightStatus {
   reference: string | null;
 }
 
+// --- background compute disclosure (ops-hardening iter-24, J-09) --------------------------
+/** One currently in-flight historical background-compute window (the iter-20 dispatch, made visible).
+ *  `elapsed_ms` is computed server-side AT READ TIME from the dispatch's own recorded `started_at` --
+ *  never derived client-side (single source, never a fabricated estimate). */
+export interface BackgroundComputeActive {
+  asof_key: string;
+  dataset_version: string;
+  started_at: string;
+  elapsed_ms: number;
+  horizons_done: number;
+  horizons_total: number;
+}
+
+/** One completed/failed historical background-compute dispatch outcome (newest-first; the ring is
+ *  bounded by the backend's `startup.background_compute_history_size`). `reason` is non-null ONLY when
+ *  `outcome === "failed"`. */
+export interface BackgroundComputeOutcome {
+  asof_key: string;
+  dataset_version: string;
+  outcome: "completed" | "failed";
+  started_at: string;
+  finished_at: string;
+  duration_ms: number;
+  reason: string | null;
+}
+
+/** The honest disclosure of the in-process historical background-compute dispatch (iter-20's
+ *  `_HIST_DISPATCH_INFLIGHT`, previously invisible except by reconstructing it from raw DB timestamps).
+ *  Read-only, process-lifetime state -- `active`/`recent_outcomes` both clear on a backend restart. */
+export interface BackgroundComputeStatus {
+  active: BackgroundComputeActive[];
+  recent_outcomes: BackgroundComputeOutcome[];
+}
+
 export interface HealthStatus {
   status: string;
   db_ok: boolean;
@@ -169,6 +203,8 @@ export interface HealthStatus {
   poll_idle_interval_seconds: number;
   // iter-33 (J-20): the single daily preflight verdict (additive).
   preflight: PreflightStatus;
+  // ops-hardening iter-24 (J-09): the historical background-compute dispatch disclosure (additive).
+  background_compute: BackgroundComputeStatus;
 }
 
 /** Fetch backend health + readiness. Throws on network error or non-200 so callers can render an
diff --git a/config.yaml b/config.yaml
index cc581f1e..2400f102 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1280,6 +1280,7 @@ startup:
   warmup_batch_size: 1                     # cadence as-of dates the background warm-up persists per progress tick
   health_poll_interval_seconds: 2.0        # badge poll cadence while warming (fast flip to Ready, not a 30s cycle)
   health_poll_idle_interval_seconds: 30.0  # slower poll cadence the badge backs off to once Ready (>= active)
+  background_compute_history_size: 5       # ops-hardening iter-24 (J-09): recent_outcomes ring cap (>= 1)
 
 # ----------------------------------------------------------------------------------------
 # goal-mcp-loop iter-33 CONSUMED — the daily preflight verdict (J-20 / backlog B-301).
diff --git a/docs/goal.md b/docs/goal.md
index 64641bc1..2b75523b 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -332,6 +332,65 @@ no-ops or arbitrary limits.
      between the two markers below (see the goal-self-extension skill). The human-authored journeys
      above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
 <!-- AUTO:journeys -->
+
+- **J-09: The backend discloses its own background-compute activity**
+  - Steps:
+    1. With a warm backend in prod mode (`scripts/start-backend.sh`), open any page and note the
+       top-bar readiness badge reads `Ready`; poll `GET /api/health` and record the steady-state
+       payload plus its latency
+    2. Trigger exactly one background-compute window (BCW) the way a user does — load `/backtest`
+       for a historical trading day whose forward-aggregate evidence is not yet complete for the
+       current dataset version; assert the request still returns immediately (J-08 unchanged) while
+       the compute is dispatched to the background thread
+    3. While that window is in flight, poll `GET /api/health`; assert the SAME payload now carries an
+       explicit background-activity field naming what is running (the as-of key(s) computing, how
+       many are in flight, horizons done/total, when the window started), and assert the top-bar
+       badge polled in that same window shows a calm, explicit "background compute running" detail
+       alongside `Ready` — never a bare `Ready` that hides it, never a misstated
+       `initializing`/`Backend unavailable`
+    4. On `/data`, assert a panel renders that same field from that same poll: the in-flight
+       window(s) with elapsed time and horizons done/total, plus the last completed or failed
+       background compute with its outcome and, on failure, the recorded reason (the dispatch
+       already catches and logs its exceptions) — never a silent failure, never an unexplained
+       forever-refreshing state
+    5. After the window completes, poll again and assert the field returns to an explicit idle state
+       ("no background compute running") and the `/data` panel moves that window into its
+       last-outcome row with a real measured duration
+    6. Assert the disclosure is honest about its own scope: it is process-lifetime (a backend restart
+       clears it, and the panel says so) and it never claims progress it did not observe — no
+       fabricated percentages, no estimated finish times
+  - Acceptance:
+    - **Consistency (single source):** background-compute activity is a NEW Data Contract value with
+      exactly ONE producer — the in-process dispatch registry inside `app.engine.forward_testing`
+      (its existing single-flight guard stays the only writer) exposed through one read-only
+      accessor and composed into the payload by `app.engine.readiness.compute_readiness` — and
+      exactly ONE serving endpoint, `GET /api/health` (the same additive pattern the `preflight`
+      field used). The badge and the `/data` panel both read the existing single `ReadinessProvider`
+      poll and re-format only: no second endpoint, no second poll, no client-side derivation. Ingest
+      jobs keep their own single source (`GET /api/data` run records) and boot warm-up keeps
+      `warmup` — this value never restates either. Any new threshold or retained-record count comes
+      from `config.yaml`, never a literal.
+    - **Correctness:** the disclosed identities, counts, horizon progress, timestamps and outcomes
+      match the dispatch's own record for the same window (AG-3), cross-checkable against
+      `forward_aggregate_cache` commit timestamps and the backend logfile; a read taken during a
+      disclosed window is classifiable as a BCW read from the payload alone, so budget scoring no
+      longer depends on post-hoc forensic reconstruction.
+    - **No behavior change:** `ensure_historical_forward_aggregates_dispatched`'s keying and
+      single-flight semantics, `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
+      and J-08's `ready`/`refreshing`/`not_yet_computed` state machine and served values are
+      semantically unchanged — this journey adds disclosure only. Bounding concurrency stays out of
+      scope (owner-deferred backlog card B-1107), as do the declined off-process-compute and
+      precompute-all-historical-dates redesigns.
+    - **Honest status & anti-goals:** the new field costs `GET /api/health` no database work (an
+      in-memory read under the existing lock) and steady-state `/api/health` stays within its
+      UNCHANGED ≤ 0.1 s budget, re-measured and recorded in `reports/perf-budgets.md` (the single
+      budgets artifact; steady-state and BCW ceilings are not amended by this journey); no frozen or
+      blank frame; copy stays factual with no reassurance language; no proven-language and no
+      Evidence Claim is introduced (AG-1/AG-4/AG-6), and AG-8/AG-10 are untouched.
+    - **Walkthrough:** a `[NEW]`-flagged walkthrough of steady-state `Ready` → a disclosed
+      background-compute window (badge detail + `/data` panel) → the honest idle/last-outcome state
+      after it completes, viewable via `demo.sh ops-hardening --session-live`.
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            |  59 ++++++++++
 reports/security/install-decisions.jsonl           |   2 +
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 .../state/assumptions.md                           | 128 ++++-----------------
 .../state/assumptions.md.archive.md                | 109 ++++++++++++++++++
 runs/goal-session-ops-hardening/state/blueprint.md |   3 +-
 runs/goal-session-ops-hardening/state/lessons.md   |  47 +-------
 .../state/lessons.md.archive.md                    |  63 ++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl    |  22 ++++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   5 +
 14 files changed, 294 insertions(+), 156 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
