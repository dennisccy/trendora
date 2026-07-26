# Iteration diff (bounded)

Files changed: 122. Shown in full: 103.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (126 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-evidence/UT-01-summary-mixed.png` (3 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-evidence/UT-02-summary-empty.png` (3 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/docs/improvement-roadmap.md` (217 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/render_iteration_summary.py` (121 lines not shown)
- `incredible_auto_dev/scripts/automation/phase-audit.sh` (12 lines not shown)
- `incredible_auto_dev/scripts/automation/qa-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/render-summary.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/review-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/run-evals.sh` (51 lines not shown)
- `incredible_auto_dev/scripts/automation/run-goal.sh` (281 lines not shown)
- `incredible_auto_dev/scripts/automation/run-judgment-evals.sh` (30 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (71 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-test-design-phase.sh` (13 lines not shown)
- `incredible_auto_dev/skills/goal-authoring.md` (13 lines not shown)
- `incredible_auto_dev/skills/plain-language.md` (78 lines not shown)
- `incredible_auto_dev/tests/automation/test-doc-drift.sh` (120 lines not shown)
- `incredible_auto_dev/tests/automation/test-escalation-warn.sh` (90 lines not shown)
- `incredible_auto_dev/tests/automation/test-plain-language.sh` (172 lines not shown)

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
diff --git a/incredible_auto_dev/.claude/agents/demo-narrator.md b/incredible_auto_dev/.claude/agents/demo-narrator.md
index 3cc275c2..c7c82d6b 100644
--- a/incredible_auto_dev/.claude/agents/demo-narrator.md
+++ b/incredible_auto_dev/.claude/agents/demo-narrator.md
@@ -4,8 +4,8 @@ description: Per-iteration product demonstrator. Authors a machine-executable de
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.0.0
-last_updated: 2026-05-22
+version: 2.1.0
+last_updated: 2026-07-26
 ---
 
 # Demo Narrator — demo-script author
@@ -26,6 +26,9 @@ testing. Favor the flows that were already verified working this iteration.
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
+1. `.claude/skills/plain-language.md` — the shared plain-writing standard. It
+   governs every `title` and `narration` field you write.
+
 The dispatch wrapper passes you: a `mode` (`record`, `live`, or `session`), a
 `phase-id` (or a session `sid` in session mode), the `FRONTEND_URL`, and the
 **Demo JSON output path** to write.
diff --git a/incredible_auto_dev/.claude/agents/developer.md b/incredible_auto_dev/.claude/agents/developer.md
index b6615cb1..6908d46f 100644
--- a/incredible_auto_dev/.claude/agents/developer.md
+++ b/incredible_auto_dev/.claude/agents/developer.md
@@ -3,8 +3,8 @@ name: developer
 description: Implementation agent. Reads the execution plan from runs/<phase>/plan.md, implements changes following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and fixes only the listed issues. Writes dev handoff when complete.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.1
-last_updated: 2026-07-03
+version: 1.1.2
+last_updated: 2026-07-25
 ---
 
 # Developer Agent
@@ -17,7 +17,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — understand the project's overall goal before implementing
 2. `.claude/project-template.md` — stack configuration, test commands, architecture principles
-3. `docs/architecture/*.md` — understand existing project architecture
+3. `docs/architecture/*.md` — existing project architecture (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `runs/<phase>/plan.md` — execution plan (what to build)
 5. Phase spec at `docs/phases/<phase>.md` — requirements and definition of done
 6. Relevant existing code in the project
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index ed57bbe8..27b15acf 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.7.0
-last_updated: 2026-07-18
+version: 1.8.0
+last_updated: 2026-07-26
 ---
 
 # Goal Evaluator Agent
@@ -207,6 +207,17 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 <only present when verdict is GOAL_ACHIEVED, REGRESSION, or STALLED — explain why halting>
 ```
 
+### 6b. Plain-language rule for prose fields
+
+The session owner is not a native English reader. In the PROSE fields only — `Reasoning` and `Next-step recommendation` in evaluator-log.md (step 4), and the `## Summary`, `## Next-Step Recommendation`, and `## Halt Justification` sections of eval.md (step 6) — write plain English:
+
+- Short sentences. Everyday words. No idioms.
+- Whenever you name a journey ID, put its short name next to it: J-04 "Sign in with email" — never a bare ID list.
+- Describe what the user would see, not internal code: "the login page rejects a correct password", not a function, class, or variable name. (Evidence references keep their file paths — that rule is unchanged.)
+- End the recommendation with one sentence saying what should happen next, phrased so a non-programmer could act on it or approve it.
+
+This rule changes WORDING ONLY. It does not change any machine-parsed format: the verdict lines and their allowed values defined elsewhere in this document, the depth-recommendation line, all headings, table shapes, JSON schemas, and file paths stay exactly as specified.
+
 ### 7. Overwrite iteration-state.md (the next planner's digest)
 
 After eval.md is written (so your fresh verdict is its newest entry), write
diff --git a/incredible_auto_dev/.claude/agents/iteration-summarizer.md b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
index a449407d..756b5314 100644
--- a/incredible_auto_dev/.claude/agents/iteration-summarizer.md
+++ b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
@@ -4,8 +4,8 @@ description: Post-iteration summarizer. Reads the iteration's artifacts (dev han
 model: claude-sonnet-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.0
-last_updated: 2026-07-07
+version: 1.2.0
+last_updated: 2026-07-26
 ---
 
 # Iteration Summarizer
@@ -30,6 +30,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `templates/iteration-summary.md` — the exact section structure your output must follow
 2. `.claude/skills/visible-change-summarizer.md` — tone and brevity guidance for user-facing summaries
+3. `.claude/skills/plain-language.md` — the shared plain-writing standard (short sentences, IDs always with friendly names, the status word table). It governs the `## In plain words` block, the project story, and the delivered wrap.
 
 ## Input files (read only what exists)
 
diff --git a/incredible_auto_dev/.claude/agents/orchestrator.md b/incredible_auto_dev/.claude/agents/orchestrator.md
index 5fe2a2ed..cf2fadae 100644
--- a/incredible_auto_dev/.claude/agents/orchestrator.md
+++ b/incredible_auto_dev/.claude/agents/orchestrator.md
@@ -3,8 +3,8 @@ name: orchestrator
 description: Phase execution planner. When invoked by run-phase.sh, reads CLAUDE.md and the phase spec, then writes a concise execution plan to runs/<phase>/plan.md. The shell script (run-phase.sh) drives the dev/review/QA loop; the orchestrator's job is planning only.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-05-04
+version: 1.0.1
+last_updated: 2026-07-25
 ---
 
 # Orchestrator Agent
@@ -17,7 +17,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — project goal, vision, success criteria (ensure phase aligns with this)
 2. `.claude/project-template.md` — project-specific stack, architecture principles
-3. `docs/architecture/` — project architecture docs (understand what already exists)
+3. `docs/architecture/` — project architecture docs (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `docs/handoffs/*-dev.md` — prior phase handoffs (what was already built)
 5. The phase spec at `docs/phases/<phase>.md`
 
diff --git a/incredible_auto_dev/.claude/agents/readme-maintainer.md b/incredible_auto_dev/.claude/agents/readme-maintainer.md
index 6f849bba..c533bcfb 100644
--- a/incredible_auto_dev/.claude/agents/readme-maintainer.md
+++ b/incredible_auto_dev/.claude/agents/readme-maintainer.md
@@ -4,8 +4,8 @@ description: Project README maintainer (goal mode). After each iteration, refres
 model: claude-sonnet-5
 tools: [Read, Write, Edit, Glob, Grep]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-06-04
+version: 1.1.0
+last_updated: 2026-07-26
 ---
 
 # README Maintainer
@@ -31,6 +31,8 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. The existing `README.md` at the repo root, if present.
 4. `templates/project-readme.md` — the skeleton to start from **only if `README.md`
    is absent**.
+5. `.claude/skills/plain-language.md` — the shared plain-writing standard for
+   everything you write into the AUTO blocks.
 
 ## Capability inputs (read what exists, skip what doesn't)
 
diff --git a/incredible_auto_dev/.claude/agents/retro-analyst.md b/incredible_auto_dev/.claude/agents/retro-analyst.md
index 5661985e..4125bdf2 100644
--- a/incredible_auto_dev/.claude/agents/retro-analyst.md
+++ b/incredible_auto_dev/.claude/agents/retro-analyst.md
@@ -4,8 +4,8 @@ description: Post-session retrospective analyst. Reads ONLY the frozen retro-inp
 model: claude-haiku-4-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-07-10
+version: 1.1.0
+last_updated: 2026-07-26
 ---
 
 # Retro Analyst
@@ -47,6 +47,14 @@ Number items RETRO-1 … RETRO-5, at most 5, each ≤20 lines, in this exact sha
 
 Hard rule: no Evidence line → no item. Every Evidence entry names the digest section and quotes the line(s) verbatim, e.g. `Evidence: Friction counters — "Quota pauses: 3"`. Zero items is a valid output: when nothing recurred, the Candidate items body is exactly `nothing recurred worth proposing` plus one sentence saying why (e.g. all counters zero, lessons product-only).
 
+Plain-writing rules (the report is read by a non-developer owner first):
+- The FIRST sentence of every **Problem:** must be plain English: short, everyday
+  words, says who hits the pain and when. Technical detail goes in the second
+  sentence.
+- Never use a bare internal codename (EVO-1, §16, REL-n, a lane or tripwire name)
+  without saying in words what it is.
+- Keep the header's code legend line exactly as the skeleton shows it.
+
 ## Output
 
 Write exactly ONE file — the output path from your dispatch prompt (`reports/goal-session-<sid>-retro.md`), overwriting any existing file:
@@ -54,8 +62,11 @@ Write exactly ONE file — the output path from your dispatch prompt (`reports/g
 ```
 # Session retro — <sid>
 
-> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
-> per EVO-1; nothing here is scheduled work.
+> **Ideas only — nothing here is scheduled work.** These are suggestions for
+> improving the build system itself, not your product. A human reviews them and
+> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
+> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
+> = chance a change breaks something else.
 
 **Session:** <sid> · **Terminal status:** <from Outcome> · **Iterations:** <from Outcome>
 
diff --git a/incredible_auto_dev/.claude/anti-patterns.md b/incredible_auto_dev/.claude/anti-patterns.md
deleted file mode 100644
index aeefc2b0..00000000
--- a/incredible_auto_dev/.claude/anti-patterns.md
+++ /dev/null
@@ -1,368 +0,0 @@
-# Anti-Patterns
-
-Failure modes observed in production multi-agent development pipelines.
-Each entry includes: the pattern, why it fails, and how to prevent it.
-
----
-
-## 1. Vague acceptance criteria cause infinite review loops
-
-**Pattern:** Phase specs contain requirements like "works correctly", "handles all cases", or "the UI should look nice."
-
-**Why it fails:** The reviewer and the developer use different interpretations of "correct". Each review cycle produces a FAIL for a different reason. After 3 loops the pipeline halts with no clear fix.
-
-**Prevention:** Every item in DEFINITION OF DONE must be:
-- Specific: "POST /api/items returns 201 with the created item's ID"
-- Testable: a concrete pass/fail condition, not a judgment
-- Scoped: tied to this phase only, not aspirational future state
-
-**Example (bad):** "The form submission should work."
-**Example (good):** "Submitting a valid form creates a record in the database and redirects to the detail page. Submitting an invalid form shows field-level error messages and does not create a record."
-
----
-
-## 2. Hardcoded stack paths in agent prompts break portability
-
-**Pattern:** Agent definitions or scripts contain paths like `apps/backend/.venv/bin/python -m pytest` or `cd apps/backend && alembic upgrade head` embedded directly.
-
-**Why it fails:** When the framework is adopted by a new project, every agent file needs manual editing. Agents in the pipeline inherit the wrong paths and fail silently.
-
-**Prevention:** All stack-specific commands live in `.claude/project-template.md`. Agent definitions reference the template: "Run the test command from project-template.md." Scripts use env vars (`CHAIN_START_BACKEND_CMD`) or conventionally-named scripts (`scripts/start-backend.sh`).
-
----
-
-## 3. Merged backend+frontend into one developer agent reduces flexibility
-
-**Pattern (anti):** Splitting implementation into separate backend-only and frontend-only agents with separate model invocations.
-
-**Why it's a false economy:** The backend agent writes the handoff, then the frontend agent reads it and adds another handoff. Two sequential long-context invocations for work that shares context. Each agent re-reads the spec, plan, and existing code from scratch.
-
-**Prevention:** A single developer agent handles both. The plan marks `Frontend Present: yes/no`. On yes, the agent implements backend first, then frontend in the same session. Alternatively, run two passes of the same developer agent (backend pass, then frontend pass) using the same agent definition with different context flags.
-
----
-
-## 4. UI evolution is an afterthought, not a pipeline gate
-
-**Pattern:** QA runs unit tests, they pass, phase is declared done. Three phases later the product manager notices the user can't access the new feature because no navigation link was added.
-
-**Why it fails:** Unit tests don't check whether the UI exposes the capability. A backend feature is invisible until the UI surfaces it.
-
-**Prevention:** The UI Evolution Audit is part of every phase with `Frontend Present: yes`. `UI-FAIL` blocks overall QA PASS. Review checklist explicitly checks for navigation updates and detail/list pages.
-
----
-
-## 5. Quota exhaustion mid-pipeline without retry causes data loss
-
-**Pattern:** A 6-stage pipeline runs unattended. At stage 4 (QA), Claude hits the usage quota and exits. The partial run state is lost. The pipeline must restart from scratch.
-
-**Why it fails:** Wasted compute. Worse, if stage 3 (dev) made changes that weren't committed, the developer re-implements the same code differently on retry, causing drift.
-
-**Prevention:**
-- Checkpoint/resume via `runs/<phase>/status.json` — completed stages are skipped on re-run
-- `quota-retry.sh` wraps every Claude invocation — detects quota messages, parses the reset time, sleeps and retries automatically
-- Never start a long pipeline before verifying quota headroom
-
----
-
-## 6. Review reports without file:line references are useless
-
-**Pattern:** Review report says "the validation logic has issues" or "error handling could be improved."
-
-**Why it fails:** The developer reads the report, doesn't know which file or line to fix, makes a guess, and the reviewer flags the same "issue" again in the next loop.
-
-**Prevention:** Every finding in a review report MUST include:
-- Exact file path
-- Line number or function name
-- Specific problem description
-- Specific fix description
-
-**Example (bad):** "Error handling is insufficient."
-**Example (good):** "`apps/backend/routers/items.py:47` — `create_item` does not catch `IntegrityError` from SQLAlchemy. Add a try/except that returns 409 Conflict when a duplicate key is detected."
-
----
-
-## 7. Reviewer and QA validator that fix code bypass the feedback loop
-
-**Pattern:** The reviewer notices a bug and edits the file to fix it "since it's obvious." The QA validator notices a test failure and patches the test to pass.
-
-**Why it fails:** The developer agent doesn't learn from the correction. On the next phase, the same mistake recurs because the developer never saw it as a fix — only the reviewer did. More critically: reviewer fixes can silently introduce new bugs that QA was supposed to catch, but QA didn't see the reviewer's changes.
-
-**Prevention:**
-- Reviewer NEVER edits source files — writes the report only
-- QA NEVER fixes test failures — writes them as blockers
-- Only the developer (and auditor, for critical post-QA issues) modifies source code
-
----
-
-## 8. Free-form agent conversation leads to hallucinated agreements
-
-**Pattern:** Two agents "discuss" a design decision in chat. Agent B says "OK I'll implement it your way." Agent B then implements something different because its actual context window didn't include the full conversation.
-
-**Why it fails:** Chat messages between agents are not in each agent's context window. Agents only have access to what was in their initial prompt and what they've read from files in the current session.
-
-**Prevention:** Agents communicate ONLY through filesystem artifacts. No "pass a message to the next agent." The orchestrator writes a plan to a file; the developer reads that file. The developer writes a handoff; the reviewer reads that file. This is the only reliable inter-agent communication.
-
----
-
-## 9. Missing functional test plans make QA rubber-stamp
-
-**Pattern:** QA runs `pytest` and reports PASS. The test suite covers internal functions but doesn't verify the user-facing feature works end-to-end. A critical API endpoint is broken but no test covers it.
-
-**Why it fails:** "Tests pass" and "the feature works for a user" are different claims. Without a functional test plan derived from the spec, QA only validates what the developer chose to test, not what the spec required.
-
-**Prevention:** The test plan generator runs BEFORE QA, deriving explicit test cases from the spec's DEFINITION OF DONE and REQUIRED USER FLOWS. QA must execute each TC-01, TC-02, ... test case and record actual vs expected outcomes. A test case failure is a blocker.
-
----
-
-## 10. Supply-chain attacks target autonomous agents
-
-**Pattern:** A compromised PyPI or npm package gets installed by an agent during a phase run. The agent has no reason to be suspicious — it's just running the install command from the spec.
-
-**Why it fails:** Autonomous agents install packages without human review. A single compromised dependency can exfiltrate secrets, modify the codebase, or establish persistence — all while the pipeline continues normally.
-
-**Prevention:** The install security gate intercepts every `pip install`, `npm install`, `git clone`, and `curl|bash` command. On Claude Code it reads the PreToolUse JSON from stdin (`.tool_input.command` — `$CLAUDE_TOOL_INPUT_COMMAND` never existed; SEC-7 fixed the plumbing) and enforces via an agent-visible `permissionDecision:"deny"` with the remediation in the reason (pin the version / edit the `config/install-security-policy.json` allowlist / `CHAIN_INSTALL_GATE_BYPASS=true`) — never a user prompt. Registry packages are warn-mode (SEC-6: proceed + logged banner); direct URLs, tarballs, custom indexes, denylist hits, unknown requirements files, unpinned git clones, and real (unquoted — quoted mentions pass) `curl|bash` deny. All decisions are logged to `reports/security/install-decisions.jsonl`. The gate is a non-negotiable pipeline component — it is not "paranoia."
-
----
-
-## 11. One large phase spec with no DEFINITION OF DONE
-
-**Pattern:** A phase spec describes 8 features in general terms, with no numbered acceptance checklist.
-
-**Why it fails:** The orchestrator doesn't know what "done" looks like. The developer implements 5 of the 8 things. The reviewer gives PASS_WITH_NOTES on the missing 3. QA gives PASS because tests pass. The audit gives FAIL because the spec goal wasn't reached. The pipeline re-runs from dev — wasting 3 cycles that could have been avoided.
-
-**Prevention:** Every phase spec MUST have a numbered DEFINITION OF DONE checklist. Each item is specific and testable. The auditor's primary job is to verify this checklist against actual code, not summaries.
-
----
-
-## 12. Agents that "summarize" instead of reading source code
-
-**Pattern:** The auditor reads the dev handoff and QA report, concludes "tests pass and the handoff describes the implementation," and gives PASS.
-
-**Why it fails:** The handoff is a summary written by the agent that implemented the code. It naturally omits mistakes. The QA report validates what the developer chose to test. Neither is a substitute for reading the actual source files.
-
-**Prevention:** Auditor instructions explicitly state: "Read actual source files, not summaries. If you cannot verify a claim from code, trace through the implementation. Never trust a handoff summary alone."
-
----
-
-## 13. Backend capabilities without UI verification leads to invisible features
-
-**Pattern:** A phase adds 3 new API endpoints. Unit tests pass. QA validates the APIs. Audit gives PASS. But no one verified that the user can actually reach these features from the UI. Three phases later, someone clicks through the app and discovers half the features have no navigation path.
-
-**Why it fails:** "Tests pass" and "the feature works for a user" are completely different claims. A feature that exists in the backend but has no UI entry point is invisible product capability — it was built but cannot be used.
-
-**Prevention:** The UI visibility system produces 6 artifacts per phase:
-- `implementation-summary` — what was built
-- `user-visible-changes` — what users can now do
-- `ui-surface-map` — which routes/components changed and what to test
-- `ui-test-plan` — exact click paths and expected outcomes
-- `ui-test-results` — browser automation evidence
-- `what-to-click` — 5-minute operator verification guide
-
-The phase closure auditor blocks completion when these artifacts are missing or vague. Browser QA must test actual user workflows, not just that pages render.
-
----
-
-## 14. Vague test steps make test plans useless
-
-**Pattern:** A test plan says "test the form submission" or "verify results are correct." The browser QA agent cannot execute this. A human tester cannot follow this. The plan exists but adds no value.
-
-**Why it fails:** Vague test steps produce vague results. "Tested and it works" is not evidence. A test plan that cannot produce reproducible pass/fail evidence is not a test plan.
-
-**Prevention:** Every test step must specify: exact URL, exact element to interact with (by name or visible label), exact value to input, and exact expected outcome. The `post-write-artifact-quality.sh` hook warns when phase report files contain vague placeholder lines. The `what-to-click-writer` skill enforces concrete step writing.
-
----
-
-## 15. Mocked-only tests for external integrations pass while live adapter is broken
-
-**Pattern:** Adapter tests mock all HTTP/browser calls. Tests pass. But the real site changed its HTML structure, blocks headless browsers, or requires auth. No one discovers this until manual testing.
-
-**Why it fails:** Mocked tests validate the parsing logic against a frozen snapshot of the external system. They never detect selector drift, bot detection, geo-blocking, or TLS fingerprint rejection. 100% mocked test coverage gives false confidence that the integration works.
-
-**Prevention:** For phases that add external integrations (scrapers, APIs, webhooks), the developer must include at least one test marked `@pytest.mark.integration` (or equivalent) that hits the real external system. QA functional test plan must include a live integration test case. These tests may be slow/flaky and skipped in CI, but must exist and be run at least once during the phase. The dev handoff must explicitly state whether live testing was successful or document the blocker if it wasn't.
-
-**Example (bad):** All Tesco adapter tests use `_build_tile_html()` fixtures. Tests pass. Tesco changes its CSS classes → live adapter returns 0 results. Bot detection blocks headless Playwright → adapter gets HTTP 403. Neither is caught until a human clicks through the UI.
-
-**Example (good):** One test marked `@pytest.mark.integration` calls `TescoAdapter().search("milk")` against the real Tesco site and asserts `len(results) > 0`. This test is slow but catches selector drift, bot detection, and infrastructure issues immediately.
-
----
-
-## 16. Hardcoded localhost in service configuration breaks non-local access
-
-**Pattern:** API URLs, CORS origins, and service bindings all use `localhost` or `127.0.0.1`. Works on the dev machine's browser. Breaks when accessed from another machine via private IP, from a VM host, through Docker, or behind a reverse proxy.
-
-**Why it fails:** The frontend sends API requests to the hardcoded `localhost:8000`. A user on another machine resolves `localhost` to their own loopback — the backend isn't there. Even if the backend is reachable by IP, restrictive CORS blocks the request. Even if CORS allows it, the backend only listens on `127.0.0.1` and rejects non-loopback connections.
-
-**Prevention:** Reviewer checklist flags any hardcoded `localhost`/`127.0.0.1` in:
-- API client URLs → must be configurable via env var or derived dynamically (e.g., `window.location.hostname`)
-- CORS origins → must use `*`, a port-range regex (e.g. `http://(localhost|127\.0\.0\.1):\d+`), or be configurable in dev mode
-- Service bindings → dev scripts must bind to `0.0.0.0`, not `127.0.0.1`
-- Dev scripts (`dev.sh`, `start-frontend.sh`) → must pass host/port via env var, not hardcoded URL strings
-
-**Sub-pattern — auto-dev-chain port drift:** `ensure_phase_ports` in `lib/common.sh` assigns a hashed preferred port and falls back to the next free port if taken (e.g., 3101 → 3102 when a stale server holds 3101). A CORS whitelist of specific ports (e.g. `[..., "http://localhost:3101"]`) will reject the fallback port and the QA/browser-QA frontend will fail to fetch data, while `curl` still works. Use a regex or env-driven allowlist so any dev port works.
-
-**Example (bad):** `const API_BASE = "http://localhost:8000"` — works only from the same machine.
-**Example (good):** `const API_BASE = \`http://${window.location.hostname}:${API_PORT}\`` — works from any hostname the user accesses the frontend with.
-**Example (CORS bad):** `allow_origins=["http://localhost:3101"]` — breaks when chain falls back to 3102.
-**Example (CORS good, FastAPI):** `allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+"`.
-
----
-
-## 17. Long `sleep` blocks the chain across system suspend/resume
-
-**Pattern:** Quota-retry logic calls `sleep 11137` (e.g. 3 hours) to wait for the Anthropic reset. The user closes the laptop lid, system suspends. On wake the next day, the sleep continues ticking monotonically instead of noticing that wall-clock time already passed the reset — the chain blocks for many hours past the intended wake-up.
-
-**Why it fails:** On Linux, `sleep N` in coreutils may sleep against the monotonic clock (pauses during suspend) or depend on the kernel honoring RTC wake-up. Across suspend/hibernate, neither guarantee is reliable: a 3-hour sleep that straddles an overnight suspend can block for 12+ hours. The pipeline is not crashed — it is silently wedged in a sleep that the user can only detect by inspecting `/proc/<pid>/wchan`.
-
-**Prevention:** Long waits must target an absolute wall-clock epoch, not a duration. `lib/quota-retry.sh::_sleep_until_epoch` polls `date +%s` against the target epoch in ≤60-second chunks — on resume, the very next poll sees the epoch has passed and the sleep exits. Any new pipeline script that needs to wait more than ~60 seconds MUST use `_sleep_until_epoch` rather than `sleep $secs`.
-
-**Example (bad):** `sleep "$sleep_secs"` where `sleep_secs` may be hours — stuck indefinitely if the laptop suspends.
-**Example (good):** `_sleep_until_epoch "$reset_epoch"` — guaranteed to return within 60s of wall clock reaching the target.
-
----
-
-## 18. Goal mode without Must-have journeys or Anti-goals
-
-**Pattern:** A user authors `docs/goal.md` from the template but skips or leaves placeholder content in the **Must-have user journeys** and **Anti-goals** sections, then runs `./scripts/automation/run-goal.sh`. The goal-decomposer produces vague iter specs and the goal-evaluator has no concrete evidence to anchor its `GOAL_ACHIEVED` decision.
-
-**Why it fails:** Goal mode uses an AI evaluator to decide when the loop terminates. Without specific journeys, the evaluator falls back on subjective judgment — best case it loops forever (related to anti-pattern #1), worst case it declares done prematurely on something that doesn't actually work for users. Anti-goals serve as veto criteria; without them the evaluator may rubber-stamp a violation (committed credentials, paid-SaaS dependency, accessibility regression) just because the journeys click through.
-
-**Prevention:**
-- `run-goal.sh` validates `docs/goal.md` on first run: it MUST contain a non-empty Must-have user journeys section with at least one journey, and a non-empty Anti-goals section. The script aborts with a clear error message if either is empty or contains only the template placeholders.
-- Each journey in goal.md MUST have an ID (`J-NN`), numbered click/type/assert steps the browser-qa-agent can execute, and an "Acceptance" line describing the observable end state. The goal-evaluator references these by ID, so missing IDs break the journey-history tracking.
-- Anti-goals MUST be concrete, checkable rules (e.g., "no hard-coded credentials in source files"), not aspirations ("be secure"). Concrete rules let the evaluator classify violations as critical (halts loop) vs minor (continues with fix recommendation).
-
-**Example (bad):**
-```
-## Must-have user journeys
-- TODO: fill in later
-
-## Anti-goals
-- Be secure.
-- Be fast.
-```
-
-**Example (good):**
-```
-## Must-have user journeys
-- **J-01: Sign up and log in**
-  - Steps: 1. visit /signup  2. enter email+password  3. submit  4. expect /dashboard  5. log out  6. log in again  7. expect /dashboard
-  - Acceptance: dashboard greeting shows the user's email
-
-## Anti-goals
-- No hard-coded credentials, API keys, or tokens in source.
-- Auth tokens MUST NOT be stored in localStorage (httpOnly cookies only).
-- No dependency on a paid SaaS service unless explicitly listed in Constraints.
-```
-
----
-
-## 19. `timeout`-wrapped child swallows terminal Ctrl-C
-
-**Pattern:** A long-running command is wrapped with GNU `timeout` for a runtime cap (e.g. `timeout 7200 claude --print "$prompt"`). The user presses Ctrl-C in the terminal and… nothing happens. The shell prints no abort message, no trap fires, and the prompt does not return for many seconds — sometimes minutes — until the wrapped command happens to finish on its own.
-
-**Why it fails:** GNU `timeout` defaults to placing its child in a **new process group** via `setpgid(2)`. Terminal Ctrl-C delivers SIGINT to the foreground process group only, which now contains just the parent shell — *not* the wrapped command. The shell receives the signal and queues the trap, but then has to wait for the pipeline to complete before running the trap; the wrapped command never received SIGINT, so it keeps running. From the user's perspective the script is unresponsive. Eventually the command exits naturally and only then does the queued trap fire — by which point the user has assumed Ctrl-C was lost and probably reached for `kill -9` or closed the terminal.
-
-This is especially bad for AI-agent scripts: the wrapped `claude` keeps consuming API credits long after the user thought they aborted.
-
-**Prevention:** pass `--foreground` to `timeout` (or otherwise keep the child in the parent's process group). With `--foreground`, the wrapped command stays in the parent's pgrp and terminal Ctrl-C reaches it directly. The documented downside — grandchildren of the wrapped command are not timed out — is acceptable for harness use cases where the wrapped command (e.g., `claude`) manages its own subprocesses.
-
-**Example (bad):** `timeout --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C does NOT reach claude. Trap is queued but blocked.
-**Example (good):** `timeout --foreground --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C reaches claude immediately; trap fires within milliseconds.
-
-**Detection:** if `kill -INT $shell_pid` exits the shell quickly but terminal Ctrl-C feels "stuck", that's the smoking gun. Confirm with `ps -o pid,pgid,cmd <child_pid>` — if the child's PGID differs from the parent shell's, you've got the bug.
-
----
-
-## 20. `next build` against a live `next dev` corrupts `.next` and SKIPs the demo
-
-**Pattern:** A production `next build` (or a typecheck/lint step that triggers a build) runs while the demo/QA `next dev` server is up. Both write the **same** `apps/frontend/.next` directory, so the build deletes/renames the webpack chunks the dev server is serving. The dev server then answers **every** request with HTTP 500 (`MODULE_NOT_FOUND`, a require stack through `.next/server/...`/`webpack-runtime.js`) and never recovers on its own. The per-iteration demo / browser-QA then report "Frontend did not respond after 90s of retries" and record **SKIPPED**, even though the server is up — it is just 500ing.
-
-**Why it fails:** `next dev` lazily reads compiled chunks from `.next`; a concurrent `next build` clobbers them. The corruption is sticky — only removing `.next` and letting `next dev` rebuild fixes it. In the post-dev fanout this cascades: the shared-services boot tries to start the frontend, fails on the corrupt build, kills it, and every parallel branch (demo, browser-qa) then waits out its readiness budget against a dead port.
-
-**Prevention (harness side, already done):** the harness now self-heals. `_start_service_with_retries` (in `scripts/automation/lib/common.sh`) detects the corrupt-`.next` signature, clears `.next`, and grants one guaranteed-cold rebuild attempt with a longer budget (`CHAIN_FRONTEND_HEAL_TIMEOUT`, default 180s) instead of killing a still-compiling server; `_kill_pid_tree` now escalates TERM→KILL so a surviving worker can't re-corrupt `.next` or squat the port; and the readiness gate `_wait_for_frontend_ready` heals once on the standalone path. Recovery costs a full cold compile per occurrence, so it is a cost, not a free pass.
-
-**Prevention (project side, optional but better):** give build/QA/typecheck commands their own dist dir so they never touch the dev build. Next.js reads `distDir` from `next.config.{js,ts}` (NOT an env var by default), so wire it through config — e.g. `distDir: process.env.NEXT_DIST_DIR || '.next'` — and run builds with `NEXT_DIST_DIR=.next-qa next build`. Agents MUST NOT run a production `next build` while the demo/QA `next dev` is up unless the build is isolated this way.
-
-**Detection:** the frontend start log (`$QA_FRONTEND_LOG` — under the run's `CHAIN_TMPDIR`, e.g. `.../fanout-frontend-<port>.log`) showing `MODULE_NOT_FOUND` / `Cannot find module` with a `GET / 500` and a `.next/server/...` require stack is the signature. `_next_build_is_corrupt` in `common.sh` greps for exactly this.
-
----
-
-## 21. Shared /tmp accumulation and cross-job pytest tmp races
-
-**Pattern:** Nothing sets `TMPDIR`, so every tool the agents run (pytest, playwright/chromium, `mktemp`) writes into shared `/tmp`. pytest's default basetemp `/tmp/pytest-of-<user>/` is keyed on the USER, not the run — concurrent pipeline jobs (different projects, same machine, same user) share it and race pytest's own "keep last 3, rmtree older" pruning (`Directory not empty`, lock races, stale undeletable dirs). Meanwhile the harness's own temp files pile up forever: kept-on-failure `claude-quota-*.log`s, telemetry usage sidecars leaked on every non-success path, and per-role service logs (`fanout-*`, `demo-*`, `goal-iter-*`) that no cleanup path ever targeted. Cleanup ran only on run-phase.sh's success path — never on `fail()`, quota/transport/signal exits, or lean goal iterations.
-
-**Why it fails:** `/tmp` is a shared namespace with no run identifier, so no cleanup step can safely delete anything (it might belong to a concurrent job) — and agents could not delete anyway (see the rm-ban fix: deny-rule over-match + Claude Code's built-in rm working-directory containment). The only "cleanup" was pytest pruning itself, which is exactly the thing that races.
-
-**Prevention:** per-run tmp isolation via `lib/chain-tmp.sh` (REL-13 moved the root OFF /tmp entirely — on this class of machine `/tmp` is a quota'd tmpfs that EDQUOTs long before it looks full):
-- Every entry script (run-phase.sh, run-goal.sh, goal-iter-lean.sh) calls `chain_tmp_init <run-id>`, which creates `$CHAIN_TMP_ROOT/iad.<id>.<pid>` (root default `~/.cache/iad`: big un-quota'd ext4, NOT /tmp) and exports it as `TMPDIR`/`TMP`/`TEMP`; a nested script ADOPTS the inherited dir (owner-guarded, and only while the recorded owner pid is still alive). The WHOLE TMPDIR is kept ≤62 chars (Chromium's 108-char unix-socket limit); long run-ids are shortened to `<prefix>-<sha256-first8>` with the raw id in `.chain-run-id`. NEW pipeline entry scripts MUST do the same.
-- Cleanup is an EXIT trap (fires on success, fail(), quota 75, transport 70, signal exits) plus `chain_tmp_rotate` at the goal-mode iteration boundary — after `_join_showcase_tail`, never right after the evaluator (the async showcase tail still writes there).
-- New `mktemp` calls MUST use a `"${TMPDIR:-/tmp}/…"` template, never a hardcoded `/tmp/...` template. Standalone scratch roots (benchmarks, judgment sandboxes) use `"${CHAIN_TMP_ROOT:-${TMPDIR:-$HOME/.cache/iad}}"` and write an `.owner-pid` file so the janitor can tell live from leaked.
-- Files deliberately kept for debugging MUST be moved to `$CHAIN_TRACE_DIR` (`_quota_preserve_failure_log`), never left in tmp.
-- The ONLY sanctioned fixed-name /tmp files are the two quota sentinels (`/tmp/{claude,codex}-quota-exhausted`) — quota is account-global, every concurrent job must see the same sentinel, and `chain_tmp_janitor` never matches their names.
-- `chain_tmp_janitor` (entry-script start) reaps strays across `$CHAIN_TMP_ROOT` AND the legacy roots (`CHAIN_TMP_LEGACY_ROOTS`, default `/tmp`): `iad.*` dirs whose owner pid is dead (age-gated normally; ANY age under `--aggressive`), `bench-*` scratch beyond the newest `CHAIN_BENCH_KEEP=2`, `judgment-*` sandboxes, legacy loose temp files, `pytest-of-$USER` entries, and `$CHAIN_TMP_ROOT/shared` entries older than `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72`. Tests that call the janitor MUST pass `CHAIN_TMP_LEGACY_ROOTS=""` or they will sweep the real /tmp.
-- `chain_tmp_disk_guard` (engine preflight + top of every goal iteration) checks free space (statvfs on the root; a WRITE PROBE on /tmp because statvfs cannot see tmpfs user quotas) and runs the aggressive janitor under pressure. Only a still-critical `CHAIN_TMP_ROOT` filesystem pauses the session (resumable `AWAITING_DISK`); /tmp pressure alone is warn-only.
-- Interactive/subagent runs get TMPDIR from the user-global `~/.claude/settings.json` `env` block (`TMPDIR=~/.cache/iad/shared`). Verified empirically 2026-07-14: settings-env **overrides** even a parent-exported TMPDIR for `claude -p` children, so engine-dispatched agents also write to `shared/` — per-iteration rotation does not apply to agent-side writes; the 72h `shared/` sweep (24h for pytest basetemps inside) is their reaper. Both lanes land on the big disk, which is the point.
-
-**AGENT RULE — disk-full errors are self-service, never a user interrupt:** on `No space left on device` or `Disk quota exceeded`, run `bash scripts/automation/tmp-doctor.sh --aggressive`, retry the failed command ONCE, and continue. NEVER `rm` arbitrary /tmp files (concurrent sessions own some of them), and NEVER halt the chain to ask the user about disk space.
-
-**Example (bad):** `tmp_log=$(mktemp /tmp/claude-quota-XXXXXX.log)` + keep-on-failure with no reaper — one leaked file per failed/quota invocation, forever.
-**Example (good):** `tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")`; on failure `_quota_preserve_failure_log "$tmp_log" claude-failure` moves it under `runs/<phase>/trace/`.
-
-**Detection:** `bash scripts/automation/tmp-doctor.sh --status` prints per-root usage with live/dead ownership. Suspicious signs: many numbered dirs under `pytest-of-$(id -un)`, `bench-*`/`judgment-*` dirs with a dead `.owner-pid`, or more than one `iad.*` dir per live pipeline job. A healthy run owns exactly ONE `iad.*` dir, and it disappears when the run exits.
-
----
-
-## 22. A scanner that reads the pipeline's own output flags itself forever
-
-**Pattern:** The goal-mode secret scan built its input as `git diff <snapshot>` plus EVERY untracked file — no path exclusion. Goal mode commits only after evaluation, so the harness's own generated artifacts (`runs/<sid>/iter-N/scan-report.md` — the scanner's previous output, which lists the matched token excerpts — plus `iter-diff.md`, `runs/<sid>/trace/`, `reports/**`, handoffs) were untracked at scan time and got scanned. Each build re-detected the tokens quoted in the previous build's report; agents then *explained* the false positive in prose, planting more copies in evaluator logs, summaries, and specs.
-
-**Why it fails:** Self-referential and monotonically growing — the finding count compounds every iteration (observed 1 → 3 → rising in tapeology session `yahoo_fetch`) and permanently blocks the GOAL_ACHIEVED gate on a product whose real diff is clean. Two iterations spent "fixing" it made it worse: every explanation or allowlist edit that quotes the token is new scan input. A second-order effect: the two per-iteration artifact builds (lean-path early build vs. the pre-evaluator rebuild) scanned different snapshots of the accumulating bookkeeping, so consumers reported CLEAN while the canonical report said CRITICAL. A third: bookkeeping could exhaust the untracked-file cap (200), silently hiding product files from the scan entirely.
-
-**Prevention:** Verifiers scan the PRODUCT, never the pipeline's bookkeeping. `goal_gate_build_diff_artifacts` applies `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` (default `runs reports docs/handoffs docs/phases`, mirroring `CHAIN_STEP_HASH_EXCLUDES`) as a `:(exclude)` pathspec on BOTH the tracked diff and the untracked enumeration; the scan-report footer records the active scope. Do NOT fix this class of bug with value-based allowlists ("this token is a known fake") — that blinds the detector to the same token in real source and breaks the case-05 judgment fixture, which plants a fake credential in product code precisely to prove detection. The distinction is path-based (generated output vs. source), never value-based. Any file a pipeline stage GENERATES that can quote findings (reports, traces, logs, specs, handoffs) must be excluded from every scanner/verifier input, and fixture secrets inside scanner code itself must be assembled at runtime (keyword and value split) so the scanner's own diff can never trip it — both enforced by self-tests (`scan_diff.py self-test` self-scan guard; `goal-gates.sh --self-test` cases 11/12).
-
----
-
-## 23. Prompt-sized content crossing execve as a single argv/env string
-
-**Pattern:** The interactive dispatch builder passed the full agent prompt to `jq` as one `--arg` value (argv), with a python3 fallback that env-prefixed it (`_ID_P="$prompt"`, envp); the headless backends passed it as `claude -p "<prompt>"` / `codex exec "<prompt>"` argv. Linux caps every SINGLE argv/envp string at MAX_ARG_STRLEN (32 pages = 128 KiB), independent of total ARG_MAX — past it execve fails with E2BIG (`Argument list too long`) and the child never runs. Goal-mode prompt templates inlined line-capped-but-not-byte-capped evaluator-log/assumption tails, which crossed 128 KiB around iteration 40 of a 43-iteration production session: EVERY decomposer/evaluator/summarizer dispatch from there failed until a human pump operator hand-reconstructed prompts from on-disk artifacts. The bug survived at least one refactor because nothing regression-tested oversized prompts.
-
-**Why it fails:** Three compounding mistakes. (1) The per-string cap is invisible in testing — normal prompts are tens of KB, and the failure appears only when ONE string crosses it. (2) The shell performs the `> "$req"` redirect in the forked child BEFORE the exec attempt, so the failed builder still creates a 0-byte file. (3) The builder's exit status was never checked, so the empty request was atomically PUBLISHED — the pump claimed a payload with no agent/prompt/res_path and the engine sat in the inflight wait (24 h in production config). The requeue path rebuilt the same oversized prompt and failed deterministically; the python3 fallback could never rescue the jq branch because envp shares the same per-string cap as argv.
-
-**Prevention:** Applies to any code handing agent prompts (or other unbounded content) to a child process, and to any code publishing channel artifacts.
-- Unbounded content NEVER crosses execve as one argv/env string. Route it via a file written by the shell builtin `printf` (no exec, no cap) + `jq --rawfile`, via stdin (`< file`, or `< <(printf '%s' "$var")` from a NON-exported shell variable), or a heredoc. Exporting the variable — including an `X="$big" cmd` env-prefix — re-introduces the same E2BIG via envp.
-- Validate channel artifacts BEFORE publishing: non-empty (`[[ -s f ]]`) FIRST — a broken builder that exits 0 writing nothing also defeats tool-based validation — then a JSON parse; on failure log loudly (agent + prompt size) and return WITHOUT publishing. (`lib/interactive-dispatch.sh` publish guard; self-tests 13–15.)
-- Producer side: byte-cap inlined log tails, not just line-cap (`_tail_or_placeholder`, `CHAIN_INLINE_TAIL_MAX_BYTES` default 48 KiB, marker names the on-disk file). The dispatch layer must still handle arbitrary sizes — the cap is bloat/token control, not the fix.
-- Headless: prompts past `CHAIN_PROMPT_ARGV_MAX` (default 100000 bytes) are fed on stdin (`claude -p` reads the prompt from stdin; `codex exec -` is the stdin sentinel); below the threshold argv is used exactly as before (`_invoke_with_prompt_stdin`; oversized-routing tests in test-quota-retry.sh).
-
-**Example (bad):** `jq -cn --arg p "$prompt" '{prompt:$p}' > req.json; mv req.json req.json.ready` — a 200 KB prompt means jq never execs, yet the 0-byte redirect target is still created and published.
-**Example (good):** `printf '%s' "$prompt" > "$pf"; jq -cn --rawfile p "$pf" '{prompt:$p}' > req.json 2>/dev/null; [[ -s req.json ]] && jq -e . req.json >/dev/null 2>&1 || { echo "build failed" >&2; return 2; }`
-
-**Detection:** `bash: …: Argument list too long` in engine stderr; a 0-byte `req.*.ready` in the channel dir; the pump claiming a request whose JSON has no fields. 30-second repro: `p="$(head -c 200000 /dev/zero | tr '\0' x)"; jq -cn --arg p "$p" . > /tmp/r.json` fails and leaves `/tmp/r.json` at 0 bytes.
-
----
-
-## 24. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
-
-**Applies to:** any parser that extracts machine verdicts (PASS/FAIL/SKIP) from agent-written markdown, and any gate that consumes the parsed result.
-
-**Pattern:** `merge_ui_test_results.py` matched verdict cells with `cell.strip().upper() in ("PASS","FAIL",...)`. Agents legitimately write `**FAIL**`, `` `SKIPPED` ``, or `PASS (with caveat)` — none of which match, so the cell parsed as NO verdict and silently dropped out of `compute_overall()`. With the FAIL rows invisible, the surviving PASS rows made the merged headline PASS while the raw lane file said FAIL — observed live twice (ops-hardening iter-9: 2 bold FAILs → merged PASS handed to the achievement gate; iter-12: header undercount). Auditors caught it both times only by re-reading the raw files.
-
-**Why it fails:** The parser treated "doesn't match my exact format" as "carries no information" at exactly the layer where a dropped FAIL flips a gate outcome. Absence-of-verdict and PASS must never be conflated by a downstream `any(FAIL)` reduction; and agent output formats drift (bold, backticks, annotations) faster than parsers pin them.
-
-**Prevention:** Normalize markdown emphasis (`c.strip().strip("*_`~")`) before matching; accept annotated verdicts via a word-boundary prefix match (`^(PASS|FAIL|SKIPPED|SKIP)\b`) scanned in REVERSE cell order so the verdict column outranks free-prose columns; keep bare-word prose non-matching. Every such parser carries a self-test case with bold/backtick/annotated verdicts wired into `run-evals.sh` (`merge_ui_test_results.py self-test`, cases `bold_verdicts` / `annotated_verdicts`). Rule: a verdict parser change ships with a fixture of REAL agent output that previously mis-parsed.
-
-**Detection:** merged headline disagrees with a raw lane file's headline; `compute_overall` counter shows empty-string verdicts (`Counter({'PASS': n, '': k})`) for rows that visibly carry verdicts.
-
----
-
-## 25. A plan metadata line can silently suppress an entire verification lane
-
-**Applies to:** goal mode; any pipeline step whose execution is gated on a model-written metadata line rather than on the work the spec demands.
-
-**Pattern:** The browser-QA lane ran only when the orchestrator's plan contained `Frontend Present: yes` (`detect_frontend_in_plan`). In ops-hardening iter-8 the spec itself mis-wrote `Frontend Present: no` while its own DoD named browser journeys to verify — so the ENTIRE browser lane (browser-qa, ui artifacts) was skipped, journeys J-01/J-03/J-04 fell to `unknown`, J-05 stayed `regressed` unverified, and the iteration closed CLOSURE-FAIL. Every later iteration worked around it by hand-writing `Frontend Present: yes` into specs whose diffs contained zero frontend files — a standing landmine had anyone written the honest-looking "no".
-
-**Why it fails:** The gate keyed on a MODEL-authored line (twice removed from ground truth) instead of the engine's own knowledge that this iteration names user journeys — which are user-visible by contract and therefore always need browser evidence. One wrong word in generated prose disabled a verification lane with no error, no log line, and downstream artifacts (`N/A stubs`) that look intentional.
-
-**Prevention:** The engine exports its parsed journey list (`CHAIN_GOAL_TARGET_JOURNEYS`, run-goal.sh) and `detect_frontend_in_plan` (lib/common.sh) force-returns frontend-present whenever it is non-empty, logging the override (`forcing browser lane despite plan`). Phase mode is untouched (the variable is only set by run-goal.sh). Rule: a lane that produces required evidence must be gated on engine-parsed facts (journey list, diff contents), never solely on model-written plan prose; when prose and facts disagree, run the lane and log the contradiction.
-
-**Detection:** a goal iteration whose spec/DoD names `J-` journeys but whose reports directory has `N/A` browser stubs; journeys dropping to `unknown` after an iteration that claimed completion.
diff --git a/incredible_auto_dev/.claude/anti-patterns/01-vague-acceptance-criteria.md b/incredible_auto_dev/.claude/anti-patterns/01-vague-acceptance-criteria.md
new file mode 100644
index 00000000..79126bf6
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/01-vague-acceptance-criteria.md
@@ -0,0 +1,16 @@
+## 1. Vague acceptance criteria cause infinite review loops
+
+**Pattern:** Phase specs contain requirements like "works correctly", "handles all cases", or "the UI should look nice."
+
+**Why it fails:** The reviewer and the developer use different interpretations of "correct". Each review cycle produces a FAIL for a different reason. After 3 loops the pipeline halts with no clear fix.
+
+**Prevention:** Every item in DEFINITION OF DONE must be:
+- Specific: "POST /api/items returns 201 with the created item's ID"
+- Testable: a concrete pass/fail condition, not a judgment
+- Scoped: tied to this phase only, not aspirational future state
+
+**Example (bad):** "The form submission should work."
+**Example (good):** "Submitting a valid form creates a record in the database and redirects to the detail page. Submitting an invalid form shows field-level error messages and does not create a record."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/02-hardcoded-stack-paths.md b/incredible_auto_dev/.claude/anti-patterns/02-hardcoded-stack-paths.md
new file mode 100644
index 00000000..a49dd163
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/02-hardcoded-stack-paths.md
@@ -0,0 +1,10 @@
+## 2. Hardcoded stack paths in agent prompts break portability
+
+**Pattern:** Agent definitions or scripts contain paths like `apps/backend/.venv/bin/python -m pytest` or `cd apps/backend && alembic upgrade head` embedded directly.
+
+**Why it fails:** When the framework is adopted by a new project, every agent file needs manual editing. Agents in the pipeline inherit the wrong paths and fail silently.
+
+**Prevention:** All stack-specific commands live in `.claude/project-template.md`. Agent definitions reference the template: "Run the test command from project-template.md." Scripts use env vars (`CHAIN_START_BACKEND_CMD`) or conventionally-named scripts (`scripts/start-backend.sh`).
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/03-merged-developer-agent.md b/incredible_auto_dev/.claude/anti-patterns/03-merged-developer-agent.md
new file mode 100644
index 00000000..8f6b9475
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/03-merged-developer-agent.md
@@ -0,0 +1,10 @@
+## 3. Merged backend+frontend into one developer agent reduces flexibility
+
+**Pattern (anti):** Splitting implementation into separate backend-only and frontend-only agents with separate model invocations.
+
+**Why it's a false economy:** The backend agent writes the handoff, then the frontend agent reads it and adds another handoff. Two sequential long-context invocations for work that shares context. Each agent re-reads the spec, plan, and existing code from scratch.
+
+**Prevention:** A single developer agent handles both. The plan marks `Frontend Present: yes/no`. On yes, the agent implements backend first, then frontend in the same session. Alternatively, run two passes of the same developer agent (backend pass, then frontend pass) using the same agent definition with different context flags.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/04-ui-evolution-afterthought.md b/incredible_auto_dev/.claude/anti-patterns/04-ui-evolution-afterthought.md
new file mode 100644
index 00000000..b4902b0c
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/04-ui-evolution-afterthought.md
@@ -0,0 +1,10 @@
+## 4. UI evolution is an afterthought, not a pipeline gate
+
+**Pattern:** QA runs unit tests, they pass, phase is declared done. Three phases later the product manager notices the user can't access the new feature because no navigation link was added.
+
+**Why it fails:** Unit tests don't check whether the UI exposes the capability. A backend feature is invisible until the UI surfaces it.
+
+**Prevention:** The UI Evolution Audit is part of every phase with `Frontend Present: yes`. `UI-FAIL` blocks overall QA PASS. Review checklist explicitly checks for navigation updates and detail/list pages.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/05-quota-exhaustion-no-retry.md b/incredible_auto_dev/.claude/anti-patterns/05-quota-exhaustion-no-retry.md
new file mode 100644
index 00000000..60d4d51f
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/05-quota-exhaustion-no-retry.md
@@ -0,0 +1,13 @@
+## 5. Quota exhaustion mid-pipeline without retry causes data loss
+
+**Pattern:** A 6-stage pipeline runs unattended. At stage 4 (QA), Claude hits the usage quota and exits. The partial run state is lost. The pipeline must restart from scratch.
+
+**Why it fails:** Wasted compute. Worse, if stage 3 (dev) made changes that weren't committed, the developer re-implements the same code differently on retry, causing drift.
+
+**Prevention:**
+- Checkpoint/resume via `runs/<phase>/status.json` — completed stages are skipped on re-run
+- `quota-retry.sh` wraps every Claude invocation — detects quota messages, parses the reset time, sleeps and retries automatically
+- Never start a long pipeline before verifying quota headroom
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/06-review-without-file-line.md b/incredible_auto_dev/.claude/anti-patterns/06-review-without-file-line.md
new file mode 100644
index 00000000..2c156686
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/06-review-without-file-line.md
@@ -0,0 +1,17 @@
+## 6. Review reports without file:line references are useless
+
+**Pattern:** Review report says "the validation logic has issues" or "error handling could be improved."
+
+**Why it fails:** The developer reads the report, doesn't know which file or line to fix, makes a guess, and the reviewer flags the same "issue" again in the next loop.
+
+**Prevention:** Every finding in a review report MUST include:
+- Exact file path
+- Line number or function name
+- Specific problem description
+- Specific fix description
+
+**Example (bad):** "Error handling is insufficient."
+**Example (good):** "`apps/backend/routers/items.py:47` — `create_item` does not catch `IntegrityError` from SQLAlchemy. Add a try/except that returns 409 Conflict when a duplicate key is detected."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/07-reviewer-qa-fixing-code.md b/incredible_auto_dev/.claude/anti-patterns/07-reviewer-qa-fixing-code.md
new file mode 100644
index 00000000..ca3e741c
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/07-reviewer-qa-fixing-code.md
@@ -0,0 +1,13 @@
+## 7. Reviewer and QA validator that fix code bypass the feedback loop
+
+**Pattern:** The reviewer notices a bug and edits the file to fix it "since it's obvious." The QA validator notices a test failure and patches the test to pass.
+
+**Why it fails:** The developer agent doesn't learn from the correction. On the next phase, the same mistake recurs because the developer never saw it as a fix — only the reviewer did. More critically: reviewer fixes can silently introduce new bugs that QA was supposed to catch, but QA didn't see the reviewer's changes.
+
+**Prevention:**
+- Reviewer NEVER edits source files — writes the report only
+- QA NEVER fixes test failures — writes them as blockers
+- Only the developer (and auditor, for critical post-QA issues) modifies source code
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/08-freeform-agent-conversation.md b/incredible_auto_dev/.claude/anti-patterns/08-freeform-agent-conversation.md
new file mode 100644
index 00000000..fd08a08a
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/08-freeform-agent-conversation.md
@@ -0,0 +1,10 @@
+## 8. Free-form agent conversation leads to hallucinated agreements
+
+**Pattern:** Two agents "discuss" a design decision in chat. Agent B says "OK I'll implement it your way." Agent B then implements something different because its actual context window didn't include the full conversation.
+
+**Why it fails:** Chat messages between agents are not in each agent's context window. Agents only have access to what was in their initial prompt and what they've read from files in the current session.
+
+**Prevention:** Agents communicate ONLY through filesystem artifacts. No "pass a message to the next agent." The orchestrator writes a plan to a file; the developer reads that file. The developer writes a handoff; the reviewer reads that file. This is the only reliable inter-agent communication.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/09-missing-functional-test-plans.md b/incredible_auto_dev/.claude/anti-patterns/09-missing-functional-test-plans.md
new file mode 100644
index 00000000..801af056
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/09-missing-functional-test-plans.md
@@ -0,0 +1,10 @@
+## 9. Missing functional test plans make QA rubber-stamp
+
+**Pattern:** QA runs `pytest` and reports PASS. The test suite covers internal functions but doesn't verify the user-facing feature works end-to-end. A critical API endpoint is broken but no test covers it.
+
+**Why it fails:** "Tests pass" and "the feature works for a user" are different claims. Without a functional test plan derived from the spec, QA only validates what the developer chose to test, not what the spec required.
+
+**Prevention:** The test plan generator runs BEFORE QA, deriving explicit test cases from the spec's DEFINITION OF DONE and REQUIRED USER FLOWS. QA must execute each TC-01, TC-02, ... test case and record actual vs expected outcomes. A test case failure is a blocker.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/10-supply-chain-attacks.md b/incredible_auto_dev/.claude/anti-patterns/10-supply-chain-attacks.md
new file mode 100644
index 00000000..f29535e1
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/10-supply-chain-attacks.md
@@ -0,0 +1,10 @@
+## 10. Supply-chain attacks target autonomous agents
+
+**Pattern:** A compromised PyPI or npm package gets installed by an agent during a phase run. The agent has no reason to be suspicious — it's just running the install command from the spec.
+
+**Why it fails:** Autonomous agents install packages without human review. A single compromised dependency can exfiltrate secrets, modify the codebase, or establish persistence — all while the pipeline continues normally.
+
+**Prevention:** The install security gate intercepts every `pip install`, `npm install`, `git clone`, and `curl|bash` command. On Claude Code it reads the PreToolUse JSON from stdin (`.tool_input.command` — `$CLAUDE_TOOL_INPUT_COMMAND` never existed; SEC-7 fixed the plumbing) and enforces via an agent-visible `permissionDecision:"deny"` with the remediation in the reason (pin the version / edit the `config/install-security-policy.json` allowlist / `CHAIN_INSTALL_GATE_BYPASS=true`) — never a user prompt. Registry packages are warn-mode (SEC-6: proceed + logged banner); direct URLs, tarballs, custom indexes, denylist hits, unknown requirements files, unpinned git clones, and real (unquoted — quoted mentions pass) `curl|bash` deny. All decisions are logged to `reports/security/install-decisions.jsonl`. The gate is a non-negotiable pipeline component — it is not "paranoia."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/11-spec-without-definition-of-done.md b/incredible_auto_dev/.claude/anti-patterns/11-spec-without-definition-of-done.md
new file mode 100644
index 00000000..33875fa7
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/11-spec-without-definition-of-done.md
@@ -0,0 +1,10 @@
+## 11. One large phase spec with no DEFINITION OF DONE
+
+**Pattern:** A phase spec describes 8 features in general terms, with no numbered acceptance checklist.
+
+**Why it fails:** The orchestrator doesn't know what "done" looks like. The developer implements 5 of the 8 things. The reviewer gives PASS_WITH_NOTES on the missing 3. QA gives PASS because tests pass. The audit gives FAIL because the spec goal wasn't reached. The pipeline re-runs from dev — wasting 3 cycles that could have been avoided.
+
+**Prevention:** Every phase spec MUST have a numbered DEFINITION OF DONE checklist. Each item is specific and testable. The auditor's primary job is to verify this checklist against actual code, not summaries.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/12-agents-summarize-not-read.md b/incredible_auto_dev/.claude/anti-patterns/12-agents-summarize-not-read.md
new file mode 100644
index 00000000..7285a9ac
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/12-agents-summarize-not-read.md
@@ -0,0 +1,10 @@
+## 12. Agents that "summarize" instead of reading source code
+
+**Pattern:** The auditor reads the dev handoff and QA report, concludes "tests pass and the handoff describes the implementation," and gives PASS.
+
+**Why it fails:** The handoff is a summary written by the agent that implemented the code. It naturally omits mistakes. The QA report validates what the developer chose to test. Neither is a substitute for reading the actual source files.
+
+**Prevention:** Auditor instructions explicitly state: "Read actual source files, not summaries. If you cannot verify a claim from code, trace through the implementation. Never trust a handoff summary alone."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/13-backend-without-ui-verification.md b/incredible_auto_dev/.claude/anti-patterns/13-backend-without-ui-verification.md
new file mode 100644
index 00000000..824696a2
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/13-backend-without-ui-verification.md
@@ -0,0 +1,18 @@
+## 13. Backend capabilities without UI verification leads to invisible features
+
+**Pattern:** A phase adds 3 new API endpoints. Unit tests pass. QA validates the APIs. Audit gives PASS. But no one verified that the user can actually reach these features from the UI. Three phases later, someone clicks through the app and discovers half the features have no navigation path.
+
+**Why it fails:** "Tests pass" and "the feature works for a user" are completely different claims. A feature that exists in the backend but has no UI entry point is invisible product capability — it was built but cannot be used.
+
+**Prevention:** The UI visibility system produces 6 artifacts per phase:
+- `implementation-summary` — what was built
+- `user-visible-changes` — what users can now do
+- `ui-surface-map` — which routes/components changed and what to test
+- `ui-test-plan` — exact click paths and expected outcomes
+- `ui-test-results` — browser automation evidence
+- `what-to-click` — 5-minute operator verification guide
+
+The phase closure auditor blocks completion when these artifacts are missing or vague. Browser QA must test actual user workflows, not just that pages render.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/14-vague-test-steps.md b/incredible_auto_dev/.claude/anti-patterns/14-vague-test-steps.md
new file mode 100644
index 00000000..bc165007
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/14-vague-test-steps.md
@@ -0,0 +1,10 @@
+## 14. Vague test steps make test plans useless
+
+**Pattern:** A test plan says "test the form submission" or "verify results are correct." The browser QA agent cannot execute this. A human tester cannot follow this. The plan exists but adds no value.
+
+**Why it fails:** Vague test steps produce vague results. "Tested and it works" is not evidence. A test plan that cannot produce reproducible pass/fail evidence is not a test plan.
+
+**Prevention:** Every test step must specify: exact URL, exact element to interact with (by name or visible label), exact value to input, and exact expected outcome. The `post-write-artifact-quality.sh` hook warns when phase report files contain vague placeholder lines. The `what-to-click-writer` skill enforces concrete step writing.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/15-mocked-only-external-tests.md b/incredible_auto_dev/.claude/anti-patterns/15-mocked-only-external-tests.md
new file mode 100644
index 00000000..b09a99be
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/15-mocked-only-external-tests.md
@@ -0,0 +1,14 @@
+## 15. Mocked-only tests for external integrations pass while live adapter is broken
+
+**Pattern:** Adapter tests mock all HTTP/browser calls. Tests pass. But the real site changed its HTML structure, blocks headless browsers, or requires auth. No one discovers this until manual testing.
+
+**Why it fails:** Mocked tests validate the parsing logic against a frozen snapshot of the external system. They never detect selector drift, bot detection, geo-blocking, or TLS fingerprint rejection. 100% mocked test coverage gives false confidence that the integration works.
+
+**Prevention:** For phases that add external integrations (scrapers, APIs, webhooks), the developer must include at least one test marked `@pytest.mark.integration` (or equivalent) that hits the real external system. QA functional test plan must include a live integration test case. These tests may be slow/flaky and skipped in CI, but must exist and be run at least once during the phase. The dev handoff must explicitly state whether live testing was successful or document the blocker if it wasn't.
+
+**Example (bad):** All Tesco adapter tests use `_build_tile_html()` fixtures. Tests pass. Tesco changes its CSS classes → live adapter returns 0 results. Bot detection blocks headless Playwright → adapter gets HTTP 403. Neither is caught until a human clicks through the UI.
+
+**Example (good):** One test marked `@pytest.mark.integration` calls `TescoAdapter().search("milk")` against the real Tesco site and asserts `len(results) > 0`. This test is slow but catches selector drift, bot detection, and infrastructure issues immediately.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/16-hardcoded-localhost.md b/incredible_auto_dev/.claude/anti-patterns/16-hardcoded-localhost.md
new file mode 100644
index 00000000..db0cbfd2
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/16-hardcoded-localhost.md
@@ -0,0 +1,21 @@
+## 16. Hardcoded localhost in service configuration breaks non-local access
+
+**Pattern:** API URLs, CORS origins, and service bindings all use `localhost` or `127.0.0.1`. Works on the dev machine's browser. Breaks when accessed from another machine via private IP, from a VM host, through Docker, or behind a reverse proxy.
+
+**Why it fails:** The frontend sends API requests to the hardcoded `localhost:8000`. A user on another machine resolves `localhost` to their own loopback — the backend isn't there. Even if the backend is reachable by IP, restrictive CORS blocks the request. Even if CORS allows it, the backend only listens on `127.0.0.1` and rejects non-loopback connections.
+
+**Prevention:** Reviewer checklist flags any hardcoded `localhost`/`127.0.0.1` in:
+- API client URLs → must be configurable via env var or derived dynamically (e.g., `window.location.hostname`)
+- CORS origins → must use `*`, a port-range regex (e.g. `http://(localhost|127\.0\.0\.1):\d+`), or be configurable in dev mode
+- Service bindings → dev scripts must bind to `0.0.0.0`, not `127.0.0.1`
+- Dev scripts (`dev.sh`, `start-frontend.sh`) → must pass host/port via env var, not hardcoded URL strings
+
+**Sub-pattern — auto-dev-chain port drift:** `ensure_phase_ports` in `lib/common.sh` assigns a hashed preferred port and falls back to the next free port if taken (e.g., 3101 → 3102 when a stale server holds 3101). A CORS whitelist of specific ports (e.g. `[..., "http://localhost:3101"]`) will reject the fallback port and the QA/browser-QA frontend will fail to fetch data, while `curl` still works. Use a regex or env-driven allowlist so any dev port works.
+
+**Example (bad):** `const API_BASE = "http://localhost:8000"` — works only from the same machine.
+**Example (good):** `const API_BASE = \`http://${window.location.hostname}:${API_PORT}\`` — works from any hostname the user accesses the frontend with.
+**Example (CORS bad):** `allow_origins=["http://localhost:3101"]` — breaks when chain falls back to 3102.
+**Example (CORS good, FastAPI):** `allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+"`.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/17-long-sleep-suspend.md b/incredible_auto_dev/.claude/anti-patterns/17-long-sleep-suspend.md
new file mode 100644
index 00000000..92e8bf05
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/17-long-sleep-suspend.md
@@ -0,0 +1,13 @@
+## 17. Long `sleep` blocks the chain across system suspend/resume
+
+**Pattern:** Quota-retry logic calls `sleep 11137` (e.g. 3 hours) to wait for the Anthropic reset. The user closes the laptop lid, system suspends. On wake the next day, the sleep continues ticking monotonically instead of noticing that wall-clock time already passed the reset — the chain blocks for many hours past the intended wake-up.
+
+**Why it fails:** On Linux, `sleep N` in coreutils may sleep against the monotonic clock (pauses during suspend) or depend on the kernel honoring RTC wake-up. Across suspend/hibernate, neither guarantee is reliable: a 3-hour sleep that straddles an overnight suspend can block for 12+ hours. The pipeline is not crashed — it is silently wedged in a sleep that the user can only detect by inspecting `/proc/<pid>/wchan`.
+
+**Prevention:** Long waits must target an absolute wall-clock epoch, not a duration. `lib/quota-retry.sh::_sleep_until_epoch` polls `date +%s` against the target epoch in ≤60-second chunks — on resume, the very next poll sees the epoch has passed and the sleep exits. Any new pipeline script that needs to wait more than ~60 seconds MUST use `_sleep_until_epoch` rather than `sleep $secs`.
+
+**Example (bad):** `sleep "$sleep_secs"` where `sleep_secs` may be hours — stuck indefinitely if the laptop suspends.
+**Example (good):** `_sleep_until_epoch "$reset_epoch"` — guaranteed to return within 60s of wall clock reaching the target.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/18-goal-journeys-anti-goals.md b/incredible_auto_dev/.claude/anti-patterns/18-goal-journeys-anti-goals.md
new file mode 100644
index 00000000..5469fc46
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/18-goal-journeys-anti-goals.md
@@ -0,0 +1,36 @@
+## 18. Goal mode without Must-have journeys or Anti-goals
+
+**Pattern:** A user authors `docs/goal.md` from the template but skips or leaves placeholder content in the **Must-have user journeys** and **Anti-goals** sections, then runs `./scripts/automation/run-goal.sh`. The goal-decomposer produces vague iter specs and the goal-evaluator has no concrete evidence to anchor its `GOAL_ACHIEVED` decision.
+
+**Why it fails:** Goal mode uses an AI evaluator to decide when the loop terminates. Without specific journeys, the evaluator falls back on subjective judgment — best case it loops forever (related to anti-pattern #1), worst case it declares done prematurely on something that doesn't actually work for users. Anti-goals serve as veto criteria; without them the evaluator may rubber-stamp a violation (committed credentials, paid-SaaS dependency, accessibility regression) just because the journeys click through.
+
+**Prevention:**
+- `run-goal.sh` validates `docs/goal.md` on first run: it MUST contain a non-empty Must-have user journeys section with at least one journey, and a non-empty Anti-goals section. The script aborts with a clear error message if either is empty or contains only the template placeholders.
+- Each journey in goal.md MUST have an ID (`J-NN`), numbered click/type/assert steps the browser-qa-agent can execute, and an "Acceptance" line describing the observable end state. The goal-evaluator references these by ID, so missing IDs break the journey-history tracking.
+- Anti-goals MUST be concrete, checkable rules (e.g., "no hard-coded credentials in source files"), not aspirations ("be secure"). Concrete rules let the evaluator classify violations as critical (halts loop) vs minor (continues with fix recommendation).
+
+**Example (bad):**
+```
+## Must-have user journeys
+- TODO: fill in later
+
+## Anti-goals
+- Be secure.
+- Be fast.
+```
+
+**Example (good):**
+```
+## Must-have user journeys
+- **J-01: Sign up and log in**
+  - Steps: 1. visit /signup  2. enter email+password  3. submit  4. expect /dashboard  5. log out  6. log in again  7. expect /dashboard
+  - Acceptance: dashboard greeting shows the user's email
+
+## Anti-goals
+- No hard-coded credentials, API keys, or tokens in source.
+- Auth tokens MUST NOT be stored in localStorage (httpOnly cookies only).
+- No dependency on a paid SaaS service unless explicitly listed in Constraints.
+```
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/19-timeout-swallows-ctrl-c.md b/incredible_auto_dev/.claude/anti-patterns/19-timeout-swallows-ctrl-c.md
new file mode 100644
index 00000000..0e5060be
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/19-timeout-swallows-ctrl-c.md
@@ -0,0 +1,17 @@
+## 19. `timeout`-wrapped child swallows terminal Ctrl-C
+
+**Pattern:** A long-running command is wrapped with GNU `timeout` for a runtime cap (e.g. `timeout 7200 claude --print "$prompt"`). The user presses Ctrl-C in the terminal and… nothing happens. The shell prints no abort message, no trap fires, and the prompt does not return for many seconds — sometimes minutes — until the wrapped command happens to finish on its own.
+
+**Why it fails:** GNU `timeout` defaults to placing its child in a **new process group** via `setpgid(2)`. Terminal Ctrl-C delivers SIGINT to the foreground process group only, which now contains just the parent shell — *not* the wrapped command. The shell receives the signal and queues the trap, but then has to wait for the pipeline to complete before running the trap; the wrapped command never received SIGINT, so it keeps running. From the user's perspective the script is unresponsive. Eventually the command exits naturally and only then does the queued trap fire — by which point the user has assumed Ctrl-C was lost and probably reached for `kill -9` or closed the terminal.
+
+This is especially bad for AI-agent scripts: the wrapped `claude` keeps consuming API credits long after the user thought they aborted.
+
+**Prevention:** pass `--foreground` to `timeout` (or otherwise keep the child in the parent's process group). With `--foreground`, the wrapped command stays in the parent's pgrp and terminal Ctrl-C reaches it directly. The documented downside — grandchildren of the wrapped command are not timed out — is acceptable for harness use cases where the wrapped command (e.g., `claude`) manages its own subprocesses.
+
+**Example (bad):** `timeout --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C does NOT reach claude. Trap is queued but blocked.
+**Example (good):** `timeout --foreground --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C reaches claude immediately; trap fires within milliseconds.
+
+**Detection:** if `kill -INT $shell_pid` exits the shell quickly but terminal Ctrl-C feels "stuck", that's the smoking gun. Confirm with `ps -o pid,pgid,cmd <child_pid>` — if the child's PGID differs from the parent shell's, you've got the bug.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/20-next-build-against-dev.md b/incredible_auto_dev/.claude/anti-patterns/20-next-build-against-dev.md
new file mode 100644
index 00000000..5186dc9f
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/20-next-build-against-dev.md
@@ -0,0 +1,14 @@
+## 20. `next build` against a live `next dev` corrupts `.next` and SKIPs the demo
+
+**Pattern:** A production `next build` (or a typecheck/lint step that triggers a build) runs while the demo/QA `next dev` server is up. Both write the **same** `apps/frontend/.next` directory, so the build deletes/renames the webpack chunks the dev server is serving. The dev server then answers **every** request with HTTP 500 (`MODULE_NOT_FOUND`, a require stack through `.next/server/...`/`webpack-runtime.js`) and never recovers on its own. The per-iteration demo / browser-QA then report "Frontend did not respond after 90s of retries" and record **SKIPPED**, even though the server is up — it is just 500ing.
+
+**Why it fails:** `next dev` lazily reads compiled chunks from `.next`; a concurrent `next build` clobbers them. The corruption is sticky — only removing `.next` and letting `next dev` rebuild fixes it. In the post-dev fanout this cascades: the shared-services boot tries to start the frontend, fails on the corrupt build, kills it, and every parallel branch (demo, browser-qa) then waits out its readiness budget against a dead port.
+
+**Prevention (harness side, already done):** the harness now self-heals. `_start_service_with_retries` (in `scripts/automation/lib/common.sh`) detects the corrupt-`.next` signature, clears `.next`, and grants one guaranteed-cold rebuild attempt with a longer budget (`CHAIN_FRONTEND_HEAL_TIMEOUT`, default 180s) instead of killing a still-compiling server; `_kill_pid_tree` now escalates TERM→KILL so a surviving worker can't re-corrupt `.next` or squat the port; and the readiness gate `_wait_for_frontend_ready` heals once on the standalone path. Recovery costs a full cold compile per occurrence, so it is a cost, not a free pass.
+
+**Prevention (project side, optional but better):** give build/QA/typecheck commands their own dist dir so they never touch the dev build. Next.js reads `distDir` from `next.config.{js,ts}` (NOT an env var by default), so wire it through config — e.g. `distDir: process.env.NEXT_DIST_DIR || '.next'` — and run builds with `NEXT_DIST_DIR=.next-qa next build`. Agents MUST NOT run a production `next build` while the demo/QA `next dev` is up unless the build is isolated this way.
+
+**Detection:** the frontend start log (`$QA_FRONTEND_LOG` — under the run's `CHAIN_TMPDIR`, e.g. `.../fanout-frontend-<port>.log`) showing `MODULE_NOT_FOUND` / `Cannot find module` with a `GET / 500` and a `.next/server/...` require stack is the signature. `_next_build_is_corrupt` in `common.sh` greps for exactly this.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/21-shared-tmp-accumulation.md b/incredible_auto_dev/.claude/anti-patterns/21-shared-tmp-accumulation.md
new file mode 100644
index 00000000..bd97a01f
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/21-shared-tmp-accumulation.md
@@ -0,0 +1,25 @@
+## 21. Shared /tmp accumulation and cross-job pytest tmp races
+
+**Pattern:** Nothing sets `TMPDIR`, so every tool the agents run (pytest, playwright/chromium, `mktemp`) writes into shared `/tmp`. pytest's default basetemp `/tmp/pytest-of-<user>/` is keyed on the USER, not the run — concurrent pipeline jobs (different projects, same machine, same user) share it and race pytest's own "keep last 3, rmtree older" pruning (`Directory not empty`, lock races, stale undeletable dirs). Meanwhile the harness's own temp files pile up forever: kept-on-failure `claude-quota-*.log`s, telemetry usage sidecars leaked on every non-success path, and per-role service logs (`fanout-*`, `demo-*`, `goal-iter-*`) that no cleanup path ever targeted. Cleanup ran only on run-phase.sh's success path — never on `fail()`, quota/transport/signal exits, or lean goal iterations.
+
+**Why it fails:** `/tmp` is a shared namespace with no run identifier, so no cleanup step can safely delete anything (it might belong to a concurrent job) — and agents could not delete anyway (see the rm-ban fix: deny-rule over-match + Claude Code's built-in rm working-directory containment). The only "cleanup" was pytest pruning itself, which is exactly the thing that races.
+
+**Prevention:** per-run tmp isolation via `lib/chain-tmp.sh` (REL-13 moved the root OFF /tmp entirely — on this class of machine `/tmp` is a quota'd tmpfs that EDQUOTs long before it looks full):
+- Every entry script (run-phase.sh, run-goal.sh, goal-iter-lean.sh) calls `chain_tmp_init <run-id>`, which creates `$CHAIN_TMP_ROOT/iad.<id>.<pid>` (root default `~/.cache/iad`: big un-quota'd ext4, NOT /tmp) and exports it as `TMPDIR`/`TMP`/`TEMP`; a nested script ADOPTS the inherited dir (owner-guarded, and only while the recorded owner pid is still alive). The WHOLE TMPDIR is kept ≤62 chars (Chromium's 108-char unix-socket limit); long run-ids are shortened to `<prefix>-<sha256-first8>` with the raw id in `.chain-run-id`. NEW pipeline entry scripts MUST do the same.
+- Cleanup is an EXIT trap (fires on success, fail(), quota 75, transport 70, signal exits) plus `chain_tmp_rotate` at the goal-mode iteration boundary — after `_join_showcase_tail`, never right after the evaluator (the async showcase tail still writes there).
+- New `mktemp` calls MUST use a `"${TMPDIR:-/tmp}/…"` template, never a hardcoded `/tmp/...` template. Standalone scratch roots (benchmarks, judgment sandboxes) use `"${CHAIN_TMP_ROOT:-${TMPDIR:-$HOME/.cache/iad}}"` and write an `.owner-pid` file so the janitor can tell live from leaked.
+- Files deliberately kept for debugging MUST be moved to `$CHAIN_TRACE_DIR` (`_quota_preserve_failure_log`), never left in tmp.
+- The ONLY sanctioned fixed-name /tmp files are the two quota sentinels (`/tmp/{claude,codex}-quota-exhausted`) — quota is account-global, every concurrent job must see the same sentinel, and `chain_tmp_janitor` never matches their names.
+- `chain_tmp_janitor` (entry-script start) reaps strays across `$CHAIN_TMP_ROOT` AND the legacy roots (`CHAIN_TMP_LEGACY_ROOTS`, default `/tmp`): `iad.*` dirs whose owner pid is dead (age-gated normally; ANY age under `--aggressive`), `bench-*` scratch beyond the newest `CHAIN_BENCH_KEEP=2`, `judgment-*` sandboxes, legacy loose temp files, `pytest-of-$USER` entries, and `$CHAIN_TMP_ROOT/shared` entries older than `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72`. Tests that call the janitor MUST pass `CHAIN_TMP_LEGACY_ROOTS=""` or they will sweep the real /tmp.
+- `chain_tmp_disk_guard` (engine preflight + top of every goal iteration) checks free space (statvfs on the root; a WRITE PROBE on /tmp because statvfs cannot see tmpfs user quotas) and runs the aggressive janitor under pressure. Only a still-critical `CHAIN_TMP_ROOT` filesystem pauses the session (resumable `AWAITING_DISK`); /tmp pressure alone is warn-only.
+- Interactive/subagent runs get TMPDIR from the user-global `~/.claude/settings.json` `env` block (`TMPDIR=~/.cache/iad/shared`). Verified empirically 2026-07-14: settings-env **overrides** even a parent-exported TMPDIR for `claude -p` children, so engine-dispatched agents also write to `shared/` — per-iteration rotation does not apply to agent-side writes; the 72h `shared/` sweep (24h for pytest basetemps inside) is their reaper. Both lanes land on the big disk, which is the point.
+
+**AGENT RULE — disk-full errors are self-service, never a user interrupt:** on `No space left on device` or `Disk quota exceeded`, run `bash scripts/automation/tmp-doctor.sh --aggressive`, retry the failed command ONCE, and continue. NEVER `rm` arbitrary /tmp files (concurrent sessions own some of them), and NEVER halt the chain to ask the user about disk space.
+
+**Example (bad):** `tmp_log=$(mktemp /tmp/claude-quota-XXXXXX.log)` + keep-on-failure with no reaper — one leaked file per failed/quota invocation, forever.
+**Example (good):** `tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")`; on failure `_quota_preserve_failure_log "$tmp_log" claude-failure` moves it under `runs/<phase>/trace/`.
+
+**Detection:** `bash scripts/automation/tmp-doctor.sh --status` prints per-root usage with live/dead ownership. Suspicious signs: many numbered dirs under `pytest-of-$(id -un)`, `bench-*`/`judgment-*` dirs with a dead `.owner-pid`, or more than one `iad.*` dir per live pipeline job. A healthy run owns exactly ONE `iad.*` dir, and it disappears when the run exits.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/22-scanner-flags-own-output.md b/incredible_auto_dev/.claude/anti-patterns/22-scanner-flags-own-output.md
new file mode 100644
index 00000000..7cd69cbe
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/22-scanner-flags-own-output.md
@@ -0,0 +1,10 @@
+## 22. A scanner that reads the pipeline's own output flags itself forever
+
+**Pattern:** The goal-mode secret scan built its input as `git diff <snapshot>` plus EVERY untracked file — no path exclusion. Goal mode commits only after evaluation, so the harness's own generated artifacts (`runs/<sid>/iter-N/scan-report.md` — the scanner's previous output, which lists the matched token excerpts — plus `iter-diff.md`, `runs/<sid>/trace/`, `reports/**`, handoffs) were untracked at scan time and got scanned. Each build re-detected the tokens quoted in the previous build's report; agents then *explained* the false positive in prose, planting more copies in evaluator logs, summaries, and specs.
+
+**Why it fails:** Self-referential and monotonically growing — the finding count compounds every iteration (observed 1 → 3 → rising in tapeology session `yahoo_fetch`) and permanently blocks the GOAL_ACHIEVED gate on a product whose real diff is clean. Two iterations spent "fixing" it made it worse: every explanation or allowlist edit that quotes the token is new scan input. A second-order effect: the two per-iteration artifact builds (lean-path early build vs. the pre-evaluator rebuild) scanned different snapshots of the accumulating bookkeeping, so consumers reported CLEAN while the canonical report said CRITICAL. A third: bookkeeping could exhaust the untracked-file cap (200), silently hiding product files from the scan entirely.
+
+**Prevention:** Verifiers scan the PRODUCT, never the pipeline's bookkeeping. `goal_gate_build_diff_artifacts` applies `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` (default `runs reports docs/handoffs docs/phases`, mirroring `CHAIN_STEP_HASH_EXCLUDES`) as a `:(exclude)` pathspec on BOTH the tracked diff and the untracked enumeration; the scan-report footer records the active scope. Do NOT fix this class of bug with value-based allowlists ("this token is a known fake") — that blinds the detector to the same token in real source and breaks the case-05 judgment fixture, which plants a fake credential in product code precisely to prove detection. The distinction is path-based (generated output vs. source), never value-based. Any file a pipeline stage GENERATES that can quote findings (reports, traces, logs, specs, handoffs) must be excluded from every scanner/verifier input, and fixture secrets inside scanner code itself must be assembled at runtime (keyword and value split) so the scanner's own diff can never trip it — both enforced by self-tests (`scan_diff.py self-test` self-scan guard; `goal-gates.sh --self-test` cases 11/12).
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/23-prompt-argv-execve.md b/incredible_auto_dev/.claude/anti-patterns/23-prompt-argv-execve.md
new file mode 100644
index 00000000..c723698a
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/23-prompt-argv-execve.md
@@ -0,0 +1,16 @@
+## 23. Prompt-sized content crossing execve as a single argv/env string
+
+**Pattern:** The interactive dispatch builder passed the full agent prompt to `jq` as one `--arg` value (argv), with a python3 fallback that env-prefixed it (`_ID_P="$prompt"`, envp); the headless backends passed it as `claude -p "<prompt>"` / `codex exec "<prompt>"` argv. Linux caps every SINGLE argv/envp string at MAX_ARG_STRLEN (32 pages = 128 KiB), independent of total ARG_MAX — past it execve fails with E2BIG (`Argument list too long`) and the child never runs. Goal-mode prompt templates inlined line-capped-but-not-byte-capped evaluator-log/assumption tails, which crossed 128 KiB around iteration 40 of a 43-iteration production session: EVERY decomposer/evaluator/summarizer dispatch from there failed until a human pump operator hand-reconstructed prompts from on-disk artifacts. The bug survived at least one refactor because nothing regression-tested oversized prompts.
+
+**Why it fails:** Three compounding mistakes. (1) The per-string cap is invisible in testing — normal prompts are tens of KB, and the failure appears only when ONE string crosses it. (2) The shell performs the `> "$req"` redirect in the forked child BEFORE the exec attempt, so the failed builder still creates a 0-byte file. (3) The builder's exit status was never checked, so the empty request was atomically PUBLISHED — the pump claimed a payload with no agent/prompt/res_path and the engine sat in the inflight wait (24 h in production config). The requeue path rebuilt the same oversized prompt and failed deterministically; the python3 fallback could never rescue the jq branch because envp shares the same per-string cap as argv.
+
+**Prevention:** Applies to any code handing agent prompts (or other unbounded content) to a child process, and to any code publishing channel artifacts.
+- Unbounded content NEVER crosses execve as one argv/env string. Route it via a file written by the shell builtin `printf` (no exec, no cap) + `jq --rawfile`, via stdin (`< file`, or `< <(printf '%s' "$var")` from a NON-exported shell variable), or a heredoc. Exporting the variable — including an `X="$big" cmd` env-prefix — re-introduces the same E2BIG via envp.
+- Validate channel artifacts BEFORE publishing: non-empty (`[[ -s f ]]`) FIRST — a broken builder that exits 0 writing nothing also defeats tool-based validation — then a JSON parse; on failure log loudly (agent + prompt size) and return WITHOUT publishing. (`lib/interactive-dispatch.sh` publish guard; self-tests 13–15.)
+- Producer side: byte-cap inlined log tails, not just line-cap (`_tail_or_placeholder`, `CHAIN_INLINE_TAIL_MAX_BYTES` default 48 KiB, marker names the on-disk file). The dispatch layer must still handle arbitrary sizes — the cap is bloat/token control, not the fix.
+- Headless: prompts past `CHAIN_PROMPT_ARGV_MAX` (default 100000 bytes) are fed on stdin (`claude -p` reads the prompt from stdin; `codex exec -` is the stdin sentinel); below the threshold argv is used exactly as before (`_invoke_with_prompt_stdin`; oversized-routing tests in test-quota-retry.sh).
+
+**Example (bad):** `jq -cn --arg p "$prompt" '{prompt:$p}' > req.json; mv req.json req.json.ready` — a 200 KB prompt means jq never execs, yet the 0-byte redirect target is still created and published.
+**Example (good):** `printf '%s' "$prompt" > "$pf"; jq -cn --rawfile p "$pf" '{prompt:$p}' > req.json 2>/dev/null; [[ -s req.json ]] && jq -e . req.json >/dev/null 2>&1 || { echo "build failed" >&2; return 2; }`
+
+**Detection:** `bash: …: Argument list too long` in engine stderr; a 0-byte `req.*.ready` in the channel dir; the pump claiming a request whose JSON has no fields. 30-second repro: `p="$(head -c 200000 /dev/zero | tr '\0' x)"; jq -cn --arg p "$p" . > /tmp/r.json` fails and leaves `/tmp/r.json` at 0 bytes.
diff --git a/incredible_auto_dev/.claude/anti-patterns/24-styled-verdict-cells-unparsed.md b/incredible_auto_dev/.claude/anti-patterns/24-styled-verdict-cells-unparsed.md
new file mode 100644
index 00000000..36f04850
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/24-styled-verdict-cells-unparsed.md
@@ -0,0 +1,11 @@
+## 24. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
+
+**Applies to:** any parser that extracts machine verdicts (PASS/FAIL/SKIP) from agent-written markdown, and any gate that consumes the parsed result.
+
+**Pattern:** `merge_ui_test_results.py` matched verdict cells with `cell.strip().upper() in ("PASS","FAIL",...)`. Agents legitimately write `**FAIL**`, `` `SKIPPED` ``, or `PASS (with caveat)` — none of which match, so the cell parsed as NO verdict and silently dropped out of `compute_overall()`. With the FAIL rows invisible, the surviving PASS rows made the merged headline PASS while the raw lane file said FAIL — observed live twice (ops-hardening iter-9: 2 bold FAILs → merged PASS handed to the achievement gate; iter-12: header undercount). Auditors caught it both times only by re-reading the raw files.
+
+**Why it fails:** The parser treated "doesn't match my exact format" as "carries no information" at exactly the layer where a dropped FAIL flips a gate outcome. Absence-of-verdict and PASS must never be conflated by a downstream `any(FAIL)` reduction; and agent output formats drift (bold, backticks, annotations) faster than parsers pin them.
+
+**Prevention:** Normalize markdown emphasis (`c.strip().strip("*_`~")`) before matching; accept annotated verdicts via a word-boundary prefix match (`^(PASS|FAIL|SKIPPED|SKIP)\b`) scanned in REVERSE cell order so the verdict column outranks free-prose columns; keep bare-word prose non-matching. Every such parser carries a self-test case with bold/backtick/annotated verdicts wired into `run-evals.sh` (`merge_ui_test_results.py self-test`, cases `bold_verdicts` / `annotated_verdicts`). Rule: a verdict parser change ships with a fixture of REAL agent output that previously mis-parsed.
+
+**Detection:** merged headline disagrees with a raw lane file's headline; `compute_overall` counter shows empty-string verdicts (`Counter({'PASS': n, '': k})`) for rows that visibly carry verdicts.
diff --git a/incredible_auto_dev/.claude/anti-patterns/25-plan-line-suppresses-lane.md b/incredible_auto_dev/.claude/anti-patterns/25-plan-line-suppresses-lane.md
new file mode 100644
index 00000000..535bdbf1
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/25-plan-line-suppresses-lane.md
@@ -0,0 +1,11 @@
+## 25. A plan metadata line can silently suppress an entire verification lane
+
+**Applies to:** goal mode; any pipeline step whose execution is gated on a model-written metadata line rather than on the work the spec demands.
+
+**Pattern:** The browser-QA lane ran only when the orchestrator's plan contained `Frontend Present: yes` (`detect_frontend_in_plan`). In ops-hardening iter-8 the spec itself mis-wrote `Frontend Present: no` while its own DoD named browser journeys to verify — so the ENTIRE browser lane (browser-qa, ui artifacts) was skipped, journeys J-01/J-03/J-04 fell to `unknown`, J-05 stayed `regressed` unverified, and the iteration closed CLOSURE-FAIL. Every later iteration worked around it by hand-writing `Frontend Present: yes` into specs whose diffs contained zero frontend files — a standing landmine had anyone written the honest-looking "no".
+
+**Why it fails:** The gate keyed on a MODEL-authored line (twice removed from ground truth) instead of the engine's own knowledge that this iteration names user journeys — which are user-visible by contract and therefore always need browser evidence. One wrong word in generated prose disabled a verification lane with no error, no log line, and downstream artifacts (`N/A stubs`) that look intentional.
+
+**Prevention:** The engine exports its parsed journey list (`CHAIN_GOAL_TARGET_JOURNEYS`, run-goal.sh) and `detect_frontend_in_plan` (lib/common.sh) force-returns frontend-present whenever it is non-empty, logging the override (`forcing browser lane despite plan`). Phase mode is untouched (the variable is only set by run-goal.sh). Rule: a lane that produces required evidence must be gated on engine-parsed facts (journey list, diff contents), never solely on model-written plan prose; when prose and facts disagree, run the lane and log the contradiction.
+
+**Detection:** a goal iteration whose spec/DoD names `J-` journeys but whose reports directory has `N/A` browser stubs; journeys dropping to `unknown` after an iteration that claimed completion.
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
new file mode 100644
index 00000000..1fb0a016
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -0,0 +1,35 @@
+# Anti-Patterns — documented failure modes (index)
+
+One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
+only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
+nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
+headings; the next new entry takes the next free number (26) as `<NN>-<slug>.md` plus a
+row here (maintenance protocol §2).
+
+| # | Entry | Applies when | Rule (one line) |
+|---|-------|--------------|-----------------|
+| 1 | [01-vague-acceptance-criteria.md](01-vague-acceptance-criteria.md) | authoring phase specs | Every DEFINITION OF DONE item must be specific and testable |
+| 2 | [02-hardcoded-stack-paths.md](02-hardcoded-stack-paths.md) | editing agent bodies/prompts | Stack commands live in project-template.md; agents reference, never inline |
+| 3 | [03-merged-developer-agent.md](03-merged-developer-agent.md) | restructuring agents | One developer handles backend+frontend, driven by `Frontend Present:` |
+| 4 | [04-ui-evolution-afterthought.md](04-ui-evolution-afterthought.md) | frontend-affecting phases | UI Evolution Audit gates QA; UI-FAIL blocks overall PASS |
+| 5 | [05-quota-exhaustion-no-retry.md](05-quota-exhaustion-no-retry.md) | dispatch/retry plumbing | Checkpoint and resume on quota exits; never restart from scratch |
+| 6 | [06-review-without-file-line.md](06-review-without-file-line.md) | writing review reports | Every finding carries file:line and a concrete fix task |
+| 7 | [07-reviewer-qa-fixing-code.md](07-reviewer-qa-fixing-code.md) | reviewer/qa behavior | Judges report; only the developer fixes |
+| 8 | [08-freeform-agent-conversation.md](08-freeform-agent-conversation.md) | inter-agent communication | Filesystem artifacts only; no agent-to-agent chat |
+| 9 | [09-missing-functional-test-plans.md](09-missing-functional-test-plans.md) | QA pipeline | Derive an explicit test plan from the spec before QA runs |
+| 10 | [10-supply-chain-attacks.md](10-supply-chain-attacks.md) | package installs | Every install goes through the security gate |
+| 11 | [11-spec-without-definition-of-done.md](11-spec-without-definition-of-done.md) | phase spec authoring | Numbered, testable DEFINITION OF DONE in every spec |
+| 12 | [12-agents-summarize-not-read.md](12-agents-summarize-not-read.md) | audit/review evidence | Verify claims from actual source code, not summaries |
+| 13 | [13-backend-without-ui-verification.md](13-backend-without-ui-verification.md) | user-facing phases | 6 UI artifacts required; invisible features fail closure |
+| 14 | [14-vague-test-steps.md](14-vague-test-steps.md) | test plan authoring | Exact URL, element, input, and expected outcome per step |
+| 15 | [15-mocked-only-external-tests.md](15-mocked-only-external-tests.md) | external integrations | At least one live integration test; mocks alone prove nothing |
+| 16 | [16-hardcoded-localhost.md](16-hardcoded-localhost.md) | service configuration | Bind addresses and URLs configurable; no localhost literals |
+| 17 | [17-long-sleep-suspend.md](17-long-sleep-suspend.md) | wait/retry code | Sleep toward an absolute epoch with polling, never one long duration |
+| 18 | [18-goal-journeys-anti-goals.md](18-goal-journeys-anti-goals.md) | goal.md authoring | Goal mode refuses to start without Must-have journeys + Anti-goals |
+| 19 | [19-timeout-swallows-ctrl-c.md](19-timeout-swallows-ctrl-c.md) | timeout-wrapped dispatch | Use `timeout --foreground` so Ctrl-C reaches the child |
+| 20 | [20-next-build-against-dev.md](20-next-build-against-dev.md) | Next.js projects | Never `next build` against a live `next dev`; separate distDir |
+| 21 | [21-shared-tmp-accumulation.md](21-shared-tmp-accumulation.md) | temp files | Per-run TMPDIR isolation via chain-tmp.sh; never raw shared /tmp |
+| 22 | [22-scanner-flags-own-output.md](22-scanner-flags-own-output.md) | scan scoping | Scan the product; exclude the pipeline's own bookkeeping paths |
+| 23 | [23-prompt-argv-execve.md](23-prompt-argv-execve.md) | passing prompts to child processes | Prompt-sized content goes via stdin or file, never argv/env |
+| 24 | [24-styled-verdict-cells-unparsed.md](24-styled-verdict-cells-unparsed.md) | parsing verdicts out of agent markdown | Normalize emphasis and annotations; absence-of-verdict is never PASS |
+| 25 | [25-plan-line-suppresses-lane.md](25-plan-line-suppresses-lane.md) | gating a verification lane | Gate lanes on engine-parsed facts, not model-written plan prose |
diff --git a/incredible_auto_dev/.claude/architecture/README.md b/incredible_auto_dev/.claude/architecture/README.md
index aaac9f49..e96b8219 100644
--- a/incredible_auto_dev/.claude/architecture/README.md
+++ b/incredible_auto_dev/.claude/architecture/README.md
@@ -9,9 +9,9 @@ This directory contains the framework's architecture documentation. These docs d
 | [system-overview.md](system-overview.md) | Design philosophy, component taxonomy, how components relate, mode comparison |
 | [pipeline.md](pipeline.md) | 11-step phase pipeline with data flow, retry loops, checkpoint/resume |
 | [goal-mode.md](goal-mode.md) | Goal-mode architecture: outer loop, halt logic, decomposer + evaluator, state |
-| [agents.md](agents.md) | All 19 agents: role, model tier, inputs, outputs |
+| [agents.md](agents.md) | All 20 agents: role, model tier, inputs, outputs |
 | [artifacts.md](artifacts.md) | Complete artifact map with paths, producers, and consumers (phase + goal modes) |
-| [skills-and-hooks.md](skills-and-hooks.md) | 13 skills and 5 hooks: purpose, consuming agent, trigger |
+| [skills-and-hooks.md](skills-and-hooks.md) | 16 skills and 5 hooks: purpose, consuming agent, trigger |
 | [configuration.md](configuration.md) | All config surfaces: project-template, agent-models, security policy |
 | [adoption-guide.md](adoption-guide.md) | Step-by-step guide to adopting this framework in a project (phase and goal modes) |
 
@@ -21,7 +21,7 @@ This directory contains the framework's architecture documentation. These docs d
 - **.claude/core.md** -- universal quality rules, testing requirements, security baseline.
 - **.claude/workflow.md** -- pipeline stages, retry policy, verdict formats.
 - **.claude/project-template.md** -- project-specific config (filled in per project).
-- **.claude/anti-patterns.md** -- 18 documented failure modes.
+- **.claude/anti-patterns/** -- failure-mode tree: README index + one file per numbered entry.
 - **docs/goal.md** -- project vision and success criteria (filled in per project).
 - **docs/architecture/** -- project-specific architecture docs (auto-updated per phase).
 
diff --git a/incredible_auto_dev/.claude/architecture/adoption-guide.md b/incredible_auto_dev/.claude/architecture/adoption-guide.md
index 949606ee..88525fe8 100644
--- a/incredible_auto_dev/.claude/architecture/adoption-guide.md
+++ b/incredible_auto_dev/.claude/architecture/adoption-guide.md
@@ -62,7 +62,7 @@ Every phase spec must have:
 - A numbered DEFINITION OF DONE checklist
 - Specific, testable acceptance criteria
 
-See `.claude/anti-patterns.md` (pattern 1) for why vague acceptance criteria cause problems.
+See `.claude/anti-patterns/01-vague-acceptance-criteria.md` for why vague acceptance criteria cause problems.
 
 ## Step 5: Run the Pipeline
 
@@ -182,12 +182,12 @@ your-project/
     core.md                          # Universal rules
     workflow.md                      # Pipeline definition
     project-template.md              # Project config (you fill this in)
-    anti-patterns.md                 # Failure modes
-    agents/                          # 14 agent definitions (12 phase + 2 goal)
-    skills/                          # 13 skills
+    anti-patterns/                   # Failure modes (README index + per-entry files)
+    agents/                          # agent definitions (rendered from agents/<name>/)
+    skills/                          # 16 skills
     hooks/                           # 5 hooks
     architecture/                    # Framework architecture docs (incl. goal-mode.md)
-  scripts/automation/                # 18 automation scripts (incl. run-goal.sh, goal-iter-lean.sh)
+  scripts/automation/                # automation scripts (incl. run-goal.sh, goal-iter-lean.sh)
     lib/                             # quota-retry.sh, common.sh, telemetry.sh
   config/                            # model-tiers.yaml, security policy
   templates/                         # 15 artifact templates
diff --git a/incredible_auto_dev/.claude/architecture/agents.md b/incredible_auto_dev/.claude/architecture/agents.md
index e16d4476..1b17c4be 100644
--- a/incredible_auto_dev/.claude/architecture/agents.md
+++ b/incredible_auto_dev/.claude/architecture/agents.md
@@ -4,11 +4,10 @@ The framework defines 20 agents in `.claude/agents/` (rendered from `agents/<nam
 
 ## Model Tiers
 
-| Tier | Model | Used for |
-|------|-------|----------|
-| strong | claude-opus-5 | Judgment: goal evaluation/decomposition, skeptical audit, confirms |
-| standard | claude-sonnet-5 | Solid tasks: code review, UI analysis, test design |
-| light | claude-haiku-4-5 | Routine workflow: QA execution, git operations |
+Tier→model resolution lives in `config/model-tiers.yaml` (via `model_tier` in each
+`agents/<name>/agent.yaml`); the prose rationale table — which model, which class of
+work, why — is maintained once, in `.claude/model-orchestration.md` §1. The per-agent
+tier notes below restate the agent.yaml facts only.
 
 ## Core Pipeline Agents (7)
 
diff --git a/incredible_auto_dev/.claude/architecture/artifacts.md b/incredible_auto_dev/.claude/architecture/artifacts.md
index 4a20e850..eb2eab54 100644
--- a/incredible_auto_dev/.claude/architecture/artifacts.md
+++ b/incredible_auto_dev/.claude/architecture/artifacts.md
@@ -1,41 +1,17 @@
 # Artifacts
 
-All inter-agent communication happens through filesystem artifacts. This document maps every artifact type, its path, producer, consumers, and format.
+All inter-agent communication happens through filesystem artifacts. The runtime-routed
+artifact tables — core pipeline, UI visibility (6 per phase), and goal-mode artifacts,
+each with producers and consumers — are maintained ONCE in `.claude/workflow.md`
+(§Communication Model and §Goal Mode Pipeline): that is the copy agents read, and it
+wins on any disagreement. This document adds only what workflow.md does not carry —
+the showcase/security artifact inventory, backend-only stubs, and the goal-mode
+schemas.
 
-## Core Pipeline Artifacts
+## Showcase, Security, and Standalone Artifacts
 
 | Artifact | Path | Producer | Consumers |
 |----------|------|----------|-----------|
-| Phase spec | `docs/phases/<phase>.md` | Human | All agents |
-| Execution plan | `runs/<phase>/plan.md` | orchestrator | developer, reviewer, qa, auditor, all UI agents |
-| Test plan | `reports/qa/<phase>-test-plan.md` | qa (generate mode) | qa (validate mode), ui-test-designer |
-| Dev handoff | `docs/handoffs/<phase>-dev.md` | developer | reviewer, qa, auditor, ui-impact-analyst |
-| Frontend handoff | `docs/handoffs/<phase>-frontend.md` | developer | reviewer, qa, auditor, ui-impact-analyst |
-| Review report | `reports/reviews/<phase>-review.md` | reviewer | qa, developer (fix mode) |
-| QA report | `reports/qa/<phase>-qa.md` | qa (validate mode) | auditor, release-manager |
-| Audit report | `docs/handoffs/<phase>-audit.md` | auditor | release-manager, phase-closure-auditor |
-| Phase status | `runs/<phase>/status.json` | scripts + agents | scripts (checkpoint/resume) |
-| Phase summary | `runs/<phase>/summary.json` | finalize-phase.sh | release-manager |
-| Project goal | `docs/goal.md` | Human | orchestrator, developer, reviewer, qa |
-| Project architecture | `docs/architecture/*.md` | update-docs.sh | orchestrator, developer |
-
-## UI Visibility Artifacts (6 per phase)
-
-| Artifact | Path | Producer | Consumers |
-|----------|------|----------|-----------|
-| Implementation summary | `reports/phase-{N}-implementation-summary.md` | developer | ui-impact-analyst, phase-closure-auditor |
-| User-visible changes | `reports/phase-{N}-user-visible-changes.md` | ui-impact-analyst | ui-test-designer, ux-regression-reviewer, phase-closure-auditor |
-| UI surface map | `reports/phase-{N}-ui-surface-map.md` | ui-impact-analyst | ui-test-designer, browser-qa-agent, ux-regression-reviewer |
-| UI test plan | `reports/phase-{N}-ui-test-plan.md` | ui-test-designer | browser-qa-agent, phase-closure-auditor |
-| UI test results | `reports/phase-{N}-ui-test-results.md` | browser-qa-agent | ux-regression-reviewer, phase-closure-auditor |
-| What to click | `reports/phase-{N}-what-to-click.md` | ui-test-designer | operator (human), phase-closure-auditor |
-
-## Additional Artifacts
-
-| Artifact | Path | Producer | Consumers |
-|----------|------|----------|-----------|
-| UX regression report | `reports/phase-{N}-ux-regression.md` | ux-regression-reviewer | phase-closure-auditor |
-| Closure verdict | `reports/phase-{N}-closure-verdict.md` | phase-closure-auditor | finalize-phase.sh |
 | UI audit report | `reports/qa/<phase>-ui-audit.md` | ui-audit-phase.sh | qa (standalone) |
 | Browser evidence | `reports/qa/<phase>-evidence/*.png` | browser-qa-agent | phase-closure-auditor |
 | Iteration summary (MD) | `reports/phase-<phase>-iteration-summary.md` | iteration-summarizer | render_iteration_summary.py, human |
@@ -49,23 +25,15 @@ All inter-agent communication happens through filesystem artifacts. This documen
 | Delivered wrap (MD) | `reports/goal-session-<sid>-delivered.md` | iteration-summarizer (delivered mode, GOAL_ACHIEVED only) | render_iteration_summary.py, human |
 | Delivered wrap (HTML) | `reports/goal-session-<sid>-delivered.html` | render_iteration_summary.py (`delivered` command) | human |
 | Install decisions | `reports/security/install-decisions.jsonl` | install-security-gate.sh | human review |
-| Framework architecture | `.claude/architecture/*.md` | update-docs.sh | all agents (reference) |
 
 ## Verdict Formats
 
-All verdicts use the prefix `**Verdict:**` followed by the exact value. Scripts parse this line by machine via `verdicts.py`.
-
-| Report | Valid Verdicts |
-|--------|---------------|
-| Review | `PASS`, `PASS_WITH_NOTES`, `FAIL` |
-| QA | `PASS`, `PASS_WITH_NOTES`, `FAIL` |
-| Audit | `PASS`, `PASS_WITH_GAPS`, `FAIL` |
-| UI Evolution (in QA) | `UI-PASS`, `UI-PASS-WITH-GAPS`, `UI-FAIL` |
-| Browser QA | `PASS`, `FAIL`, `SKIPPED` |
-| Phase Closure | `CLOSURE-PASS`, `CLOSURE-FAIL` |
-| UX Regression | `UX-REGRESSION-PASS`, `UX-REGRESSION-WARN`, `UX-REGRESSION-FAIL` |
-| Iteration summary | `GOAL_ACHIEVED`, `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`, `PASS`, `FAIL`, `IN-PROGRESS` |
-| Demo results | `RECORDED`, `RECORDED_WITH_NOTES`, `SKIPPED`, `NOT_YET` (showcase, never blocks the pipeline) |
+Machine-parsed: every verdict is a `**Verdict:**` line with an exact value. The
+complete vocabulary lives in code — `scripts/automation/lib/verdicts.py` (one enum per
+report class) — validated at write time by `lib/artifact_schemas.py`. The runtime-routed
+prose copy of the core report classes is `.claude/workflow.md` §Verdict Formats; each
+emitting agent's body names its own enum values (enforced by `lib/lint_contracts.py`).
+Emit verdict lines EXACTLY as those sources specify.
 
 ## Backend-Only N/A Stubs
 
@@ -77,19 +45,12 @@ When `Frontend Present: no`, the pipeline writes N/A stub files for the 6 UI vis
 
 ## Goal-Mode Artifacts
 
-Goal mode adds a parallel artifact tree under `runs/goal-session-<sid>/`. Per-iteration code/test artifacts still use the existing `runs/<iter-name>/` and `reports/...<iter-name>...` paths, where the iteration name `goal-<sid>-iter-<N>` is treated as a "phase name" — so all phase-mode artifacts above are produced for goal-mode iterations too.
+Goal mode adds a parallel artifact tree under `runs/goal-session-<sid>/`. Per-iteration code/test artifacts still use the existing `runs/<iter-name>/` and `reports/...<iter-name>...` paths, where the iteration name `goal-<sid>-iter-<N>` is treated as a "phase name" — so all phase-mode artifacts are produced for goal-mode iterations too. The goal-mode artifact table and both verdict tables (evaluator + loop-level halts) live in `.claude/workflow.md` §Goal Mode Pipeline. Not listed there:
 
 | Artifact | Path | Producer | Consumers |
 |----------|------|----------|-----------|
 | Goal spec (extended) | `docs/goal.md` (with Must-have user journeys + Anti-goals sections) | Human | goal-decomposer, goal-evaluator, all phase agents |
-| Iteration spec | `docs/phases/goal-<sid>-iter-<N>.md` | goal-decomposer | run-phase.sh (full) or goal-iter-lean.sh (lean), then all downstream agents |
-| Session state | `runs/goal-session-<sid>/session.json` | run-goal.sh | run-goal.sh (resume, halt arithmetic) |
-| Journey history | `runs/goal-session-<sid>/state/journey-history.json` | goal-evaluator | goal-decomposer (next-step planning), goal-evaluator (regression detection), run-goal.sh (stall detection via hash) |
-| Evaluator log | `runs/goal-session-<sid>/state/evaluator-log.md` | goal-evaluator (append-only) | goal-decomposer (read last 3 entries) |
-| Iter eval | `runs/goal-session-<sid>/iter-<N>/eval.md` | goal-evaluator | run-goal.sh (verdict parsing) |
-| Telemetry | `runs/goal-session-<sid>/telemetry.jsonl` | run-goal.sh + goal-iter-lean.sh + lib/telemetry.sh | analysis tools (jq), future self-evolution loop (deferred) |
 | History hashes | `runs/goal-session-<sid>/.history-hashes` | run-goal.sh | run-goal.sh (stall detection) |
-| Session summary | `runs/goal-session-<sid>/summary.md` | run-goal.sh (on halt) | Human |
 
 ### journey-history.json schema
 
@@ -125,13 +86,6 @@ See [`docs/goal-mode-telemetry.md`](../../docs/goal-mode-telemetry.md). Each lin
 
 ### Goal-mode verdicts
 
-The goal-evaluator emits one of:
-| Verdict | Meaning |
-|---|---|
-| `GOAL_ACHIEVED` | All Must-have journeys pass, no critical anti-goal violations. Loop halts with success. |
-| `CONTINUE` | Progress made or actionable next work identified. Loop continues. |
-| `ESCALATE` | Lean iteration uncovered ambiguity; next iteration MUST run as full. |
-| `REGRESSION` | A previously-passing journey now fails OR a critical anti-goal was violated. Halts for human review. |
-| `STALLED` | Evaluator-side judgment that no productive next work is identifiable. Halts. |
-
-The outer loop also emits halt verdicts of its own (`BUDGET_EXHAUSTED`, `STALLED` via hash detection, `REGRESSION_HALT`, `ABORTED`) into `session.json.status`.
+Evaluator verdicts (`GOAL_ACHIEVED` / `CONTINUE` / `ESCALATE` / `REGRESSION` /
+`STALLED`) and the loop-level halt verdicts are specified in `.claude/workflow.md`
+§Goal Mode Pipeline (vocabulary: `lib/verdicts.py` `GoalEvalVerdict`).
diff --git a/incredible_auto_dev/.claude/architecture/configuration.md b/incredible_auto_dev/.claude/architecture/configuration.md
index 8a3e1884..5a278e6e 100644
--- a/incredible_auto_dev/.claude/architecture/configuration.md
+++ b/incredible_auto_dev/.claude/architecture/configuration.md
@@ -25,7 +25,7 @@ Agents reference this file for stack-specific commands (test runner, package man
 
 ## config/model-tiers.yaml (+ agents/*/agent.yaml `model_tier`)
 
-Maps each of the 19 agents to a model tier (12 phase-mode + 2 goal-mode).
+Maps each of the 20 agents to a model tier (12 phase-pipeline + 4 goal-mode + 4 showcase/maintenance).
 
 ```yaml
 tiers:
diff --git a/incredible_auto_dev/.claude/architecture/goal-mode.md b/incredible_auto_dev/.claude/architecture/goal-mode.md
index aa269a24..12796972 100644
--- a/incredible_auto_dev/.claude/architecture/goal-mode.md
+++ b/incredible_auto_dev/.claude/architecture/goal-mode.md
@@ -85,7 +85,7 @@ After the evaluator runs, the verdict directly drives the loop:
 
 **Quota exhaustion is NOT a halt.** The wrapped `claude_with_quota_retry` library transparently sleeps until the quota resets, then resumes the same agent invocation. Telemetry records the quota pause for observability.
 
-**Per-iteration tmp hygiene.** The engine owns a per-run tmp dir (`lib/chain-tmp.sh`, exported as `TMPDIR`): session-scoped at startup, then rotated to `$CHAIN_TMP_ROOT/iad.goal-<sid>-iter-<N>.<pid>` (root default `~/.cache/iad`, not the quota'd tmpfs `/tmp`; ≤62-char TMPDIR, long ids hash-shortened) at each iteration boundary — immediately after `_join_showcase_tail`, because the previous iteration's async showcase tail keeps writing demo logs until that join (never clean right after the evaluator). The `[run-goal] Tmp cleanup: cleared …` log line marks the step. Both dispatch depths adopt the engine's dir (owner-guarded), and the engine's EXIT trap removes the final dir on any halt. A startup janitor reaps strays from crashed sessions across the root and legacy `/tmp`. See `.claude/anti-patterns.md` #21.
+**Per-iteration tmp hygiene.** The engine owns a per-run tmp dir (`lib/chain-tmp.sh`, exported as `TMPDIR`): session-scoped at startup, then rotated to `$CHAIN_TMP_ROOT/iad.goal-<sid>-iter-<N>.<pid>` (root default `~/.cache/iad`, not the quota'd tmpfs `/tmp`; ≤62-char TMPDIR, long ids hash-shortened) at each iteration boundary — immediately after `_join_showcase_tail`, because the previous iteration's async showcase tail keeps writing demo logs until that join (never clean right after the evaluator). The `[run-goal] Tmp cleanup: cleared …` log line marks the step. Both dispatch depths adopt the engine's dir (owner-guarded), and the engine's EXIT trap removes the final dir on any halt. A startup janitor reaps strays from crashed sessions across the root and legacy `/tmp`. See `.claude/anti-patterns/21-shared-tmp-accumulation.md`.
 
 **Disk-space guard (`AWAITING_DISK`).** `chain_tmp_disk_guard` runs once at preflight (next to the GitHub preflight) and again at the top of every iteration, with the other halt checks — never mid-iteration. Under pressure (root fs below `CHAIN_TMP_MIN_FREE_MB`, or a `/tmp` write-probe hitting ENOSPC/EDQUOT — statvfs cannot see tmpfs user quotas) it runs the aggressive janitor: dead-pid run dirs at any age, stale `bench-*`/`judgment-*`/`shared/` entries. Only when the ROOT filesystem is still below `CHAIN_TMP_HARD_MIN_FREE_MB` after sweeping does the engine pause: `session.json.status = AWAITING_DISK`, exit 0, resumable exactly like the auth pause (fix: `scripts/automation/tmp-doctor.sh --aggressive`, then `--resume`). /tmp pressure alone is warn-only — agent-side writes land in `~/.cache/iad/shared` via the user-global settings `env` TMPDIR (verified: settings-env overrides even a parent-exported TMPDIR for dispatched agents, so their reaper is the 72h `shared/` sweep, not per-iteration rotation).
 
@@ -196,4 +196,4 @@ Telemetry capture is a foundation for a future "self-evolution" loop where this
 - [`docs/goal-mode-telemetry.md`](../../docs/goal-mode-telemetry.md) — telemetry schema
 - [`agents.md`](agents.md) — full agent inventory
 - [`pipeline.md`](pipeline.md) — phase-mode pipeline (the "full" inner pipeline of goal mode)
-- [`.claude/anti-patterns.md`](../anti-patterns.md) — anti-pattern #18 covers goal-mode authoring
+- [`.claude/anti-patterns/18-goal-journeys-anti-goals.md`](../anti-patterns/18-goal-journeys-anti-goals.md) — the goal-mode authoring failure mode
diff --git a/incredible_auto_dev/.claude/architecture/pipeline.md b/incredible_auto_dev/.claude/architecture/pipeline.md
index 77e76669..ea4d7b34 100644
--- a/incredible_auto_dev/.claude/architecture/pipeline.md
+++ b/incredible_auto_dev/.claude/architecture/pipeline.md
@@ -54,7 +54,7 @@ Phase spec (docs/phases/<phase>.md)
     |
     v
 [Step 9] auditor --> audit-report
-         (loop: max 2 attempts on FAIL)
+         (loop: max 3 attempts on FAIL; retry caps authoritative in workflow.md §Retry Policy)
     |
     v
 [Step 10] phase-closure-auditor --> closure-verdict
@@ -141,4 +141,4 @@ Key contracts:
 
 Goal mode: full iterations dispatch through `run-phase.sh --no-finalize`, so the fanout runs there too. Lean iterations (`goal-iter-lean.sh`) have no parallelisable surface — dev → review → browser-qa → demo is strictly sequential — and run as today.
 
-**Per-run tmp isolation** (`lib/chain-tmp.sh`): `run-phase.sh` initializes `$CHAIN_TMP_ROOT/iad.<phase>.<pid>` (root default `~/.cache/iad` — big un-quota'd disk, NOT the quota'd tmpfs `/tmp`; the whole TMPDIR stays ≤62 chars for Chromium's unix-socket limit, long ids hash-shortened with the raw id in `.chain-run-id`) and exports it as `TMPDIR`, so pytest basetemps, chromium profiles, dispatch temp logs, and `_qa_log_path` service logs all land in one per-run dir (adopted, not re-created, when nested under run-goal.sh — and only while the recorded owner pid is alive). The un-numbered cleanup block after Step 10.5 announces the dir; the actual removal happens in an EXIT trap that fires on EVERY exit path (success, `fail()`, quota 75, transport 70, signal aborts) and, on non-success, first archives bounded service-log tails to `runs/<phase>/service-logs/`. A janitor at startup reaps strays from crashed runs across the root AND legacy `/tmp` (age- and pid-liveness-gated; also `bench-*`/`judgment-*` scratch and the `shared/` interactive-TMPDIR dir), and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (warn-only here; the goal engine owns the pause). See `.claude/anti-patterns.md` #21 and `scripts/automation/tmp-doctor.sh`.
+**Per-run tmp isolation** (`lib/chain-tmp.sh`): `run-phase.sh` initializes `$CHAIN_TMP_ROOT/iad.<phase>.<pid>` (root default `~/.cache/iad` — big un-quota'd disk, NOT the quota'd tmpfs `/tmp`; the whole TMPDIR stays ≤62 chars for Chromium's unix-socket limit, long ids hash-shortened with the raw id in `.chain-run-id`) and exports it as `TMPDIR`, so pytest basetemps, chromium profiles, dispatch temp logs, and `_qa_log_path` service logs all land in one per-run dir (adopted, not re-created, when nested under run-goal.sh — and only while the recorded owner pid is alive). The un-numbered cleanup block after Step 10.5 announces the dir; the actual removal happens in an EXIT trap that fires on EVERY exit path (success, `fail()`, quota 75, transport 70, signal aborts) and, on non-success, first archives bounded service-log tails to `runs/<phase>/service-logs/`. A janitor at startup reaps strays from crashed runs across the root AND legacy `/tmp` (age- and pid-liveness-gated; also `bench-*`/`judgment-*` scratch and the `shared/` interactive-TMPDIR dir), and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (warn-only here; the goal engine owns the pause). See `.claude/anti-patterns/21-shared-tmp-accumulation.md` and `scripts/automation/tmp-doctor.sh`.
diff --git a/incredible_auto_dev/.claude/architecture/skills-and-hooks.md b/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
index 4fc2040c..ad3060ad 100644
--- a/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
+++ b/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
@@ -1,6 +1,6 @@
 # Skills and Hooks
 
-## Skills (9 total, in `.claude/skills/`)
+## Skills (in `.claude/skills/`)
 
 Skills are reusable instruction files that agents read during their workflow. They are not agents -- they are methodologies.
 
@@ -9,6 +9,7 @@ Skills are reusable instruction files that agents read during their workflow. Th
 | Diff-to-UI Impact | `diff-to-ui-impact.md` | ui-impact-analyst | Classify file changes by UI impact type (frontend-direct, backend-api, backend-internal, config, full-stack) |
 | UI Workflow Inference | `ui-workflow-inference.md` | ui-impact-analyst | Infer user journeys from changed routes, components, and entry points |
 | Visible Change Summarizer | `visible-change-summarizer.md` | ui-impact-analyst | Write plain-language user-facing change summaries for operators |
+| Plain Language | `plain-language.md` | iteration-summarizer, demo-narrator, readme-maintainer | Shared plain-English writing standard for owner-facing prose: short sentences, IDs with friendly names, the canonical status/verdict word table (single source: `lib/plain-language.sh`) |
 | Manual UI Test Plan Generator | `manual-ui-test-plan-generator.md` | ui-test-designer | Create human-executable test plans with exact steps and expected outcomes |
 | What-to-Click Writer | `what-to-click-writer.md` | ui-test-designer | Write fast operator verification guides (5-minute check) |
 | Browser Workflow Executor | `browser-workflow-executor.md` | browser-qa-agent | Execute browser flows via Chrome MCP (navigate, click, type, screenshot) |
diff --git a/incredible_auto_dev/.claude/architecture/system-overview.md b/incredible_auto_dev/.claude/architecture/system-overview.md
index f8991870..f1168217 100644
--- a/incredible_auto_dev/.claude/architecture/system-overview.md
+++ b/incredible_auto_dev/.claude/architecture/system-overview.md
@@ -28,9 +28,9 @@ The framework consists of 6 component types:
 
 Markdown files that define each agent's role, inputs, outputs, and rules. Agents are invoked by automation scripts. Each agent has a model tier assignment (strong/standard/light) — `model_tier` in `agents/<name>/agent.yaml`, resolved via `config/model-tiers.yaml`.
 
-Twelve agents serve the phase pipeline (orchestrator, developer, reviewer, qa, auditor, release-manager, product-manager, ui-impact-analyst, ui-test-designer, browser-qa-agent, ux-regression-reviewer, phase-closure-auditor). Two agents are specific to goal mode (goal-decomposer, goal-evaluator). Goal mode reuses all twelve phase agents unchanged.
+Twelve agents serve the phase pipeline (orchestrator, developer, reviewer, qa, auditor, release-manager, product-manager, ui-impact-analyst, ui-test-designer, browser-qa-agent, ux-regression-reviewer, phase-closure-auditor). Four are specific to goal mode (goal-decomposer, goal-evaluator, coherence-auditor, goal-proposer) and four are showcase/maintenance agents (iteration-summarizer, demo-narrator, readme-maintainer, retro-analyst). Goal mode reuses the twelve phase agents unchanged.
 
-### 2. Skills (9 total, in `.claude/skills/`)
+### 2. Skills (in `.claude/skills/`)
 
 Reusable instruction files that agents read during their workflow. Skills are not agents -- they are methodologies that agents consume. For example, the `diff-to-ui-impact` skill teaches the ui-impact-analyst how to classify file changes.
 
@@ -65,11 +65,11 @@ CLAUDE.md (constitution)
     +-- .claude/core.md (universal rules)
     +-- .claude/workflow.md (pipeline definition)
     +-- .claude/project-template.md (project config)
-    +-- .claude/anti-patterns.md (failure modes)
+    +-- .claude/anti-patterns/ (failure modes: index + per-entry files)
     |
     +-- .claude/agents/*.md (12 agent definitions)
     |       |
-    |       +-- read .claude/skills/*.md (13 skills)
+    |       +-- read .claude/skills/*.md (16 skills)
     |
     +-- .claude/hooks/*.sh (5 hooks, triggered by Claude Code)
     |
diff --git a/incredible_auto_dev/.claude/commands/goal-status.md b/incredible_auto_dev/.claude/commands/goal-status.md
index f318de03..ebcfada4 100644
--- a/incredible_auto_dev/.claude/commands/goal-status.md
+++ b/incredible_auto_dev/.claude/commands/goal-status.md
@@ -27,3 +27,7 @@ the engine, dispatch agents, or write anything.
    the opt-in `--intent-checkpoint` "is this the product you wanted?" pause —
    resuming acknowledges it), **orphaned** (dead engine PID — `/goal-resume`),
    or **finished** (and the final verdict).
+7. **Plain words first:** lead the summary with the status translated into a
+   plain sentence (the wording table lives in `docs/READING-REPORTS.md`), with
+   the raw code in parentheses — e.g. "The chain is paused and waiting for your
+   blueprint review (`AWAITING_BLUEPRINT_APPROVAL`)." Same for the last verdict.
diff --git a/incredible_auto_dev/.claude/core.md b/incredible_auto_dev/.claude/core.md
index 83c73813..7e4eed2f 100644
--- a/incredible_auto_dev/.claude/core.md
+++ b/incredible_auto_dev/.claude/core.md
@@ -69,7 +69,7 @@ On `No space left on device` / `Disk quota exceeded`: run
 `bash scripts/automation/tmp-doctor.sh --aggressive`, retry the failed command
 ONCE, and continue. Never `rm` arbitrary `/tmp` files (concurrent sessions own
 some of them) and never halt to ask the user about disk space — the doctor
-only removes temp dirs proven dead or stale (`.claude/anti-patterns.md` #21).
+only removes temp dirs proven dead or stale (`.claude/anti-patterns/21-shared-tmp-accumulation.md`).
 
 ---
 
@@ -117,7 +117,7 @@ When a phase introduces or modifies code that calls external systems (scrapers,
 - [ ] Known failures (bot detection, geo-blocking, auth requirements) are documented in the dev handoff as "Known Issues" — not silently passed over
 - [ ] The dev handoff explicitly states whether live testing was successful or not
 
-See anti-patterns #15 and #16 for detailed failure modes and prevention strategies.
+See `.claude/anti-patterns/15-mocked-only-external-tests.md` and `16-hardcoded-localhost.md` for detailed failure modes and prevention strategies.
 
 ---
 
diff --git a/incredible_auto_dev/.claude/hooks/post-edit-lint.sh b/incredible_auto_dev/.claude/hooks/post-edit-lint.sh
index 2081eb86..90f3b6d2 100644
--- a/incredible_auto_dev/.claude/hooks/post-edit-lint.sh
+++ b/incredible_auto_dev/.claude/hooks/post-edit-lint.sh
@@ -1,6 +1,23 @@
 #!/usr/bin/env bash
 # Post-edit hook: run lightweight syntax validation on edited source files
-FILE="$1"
+#
+# Two input modes (SEC-7 pattern, mirrors guard-dangerous-commands.sh):
+#   argv mode  — file path as $1 (run-evals, test harness, Codex).
+#   stdin mode — the Claude Code PostToolUse protocol: JSON on stdin
+#     (.tool_input.file_path; $CLAUDE_TOOL_INPUT_FILE_PATH never existed).
+# Advisory only: warnings to stderr, always exit 0.
+FILE="${1:-}"
+if [[ -z "$FILE" && ! -t 0 ]]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [[ -n "$_payload" ]]; then
+    if command -v jq >/dev/null 2>&1; then
+      FILE=$(printf '%s' "$_payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null) || FILE=""
+    else
+      FILE=$(printf '%s' "$_payload" | python3 -c 'import json,sys; ti=json.load(sys.stdin).get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")' 2>/dev/null) || FILE=""
+    fi
+  fi
+fi
+[[ -z "$FILE" ]] && exit 0
 
 if [[ "$FILE" == *.py ]]; then
   if command -v python3 &>/dev/null; then
diff --git a/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh b/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh
index 57aaf7ae..c2926343 100755
--- a/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh
+++ b/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh
@@ -10,6 +10,20 @@ set -e
 
 FILE_PATH="${1:-}"
 
+# Claude Code PostToolUse passes JSON on stdin (.tool_input.file_path);
+# $CLAUDE_TOOL_INPUT_FILE_PATH never existed. argv ($1) remains the
+# test-harness / Codex path (SEC-7 pattern, mirrors guard-dangerous-commands.sh).
+if [[ -z "$FILE_PATH" && ! -t 0 ]]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [[ -n "$_payload" ]]; then
+    if command -v jq >/dev/null 2>&1; then
+      FILE_PATH=$(printf '%s' "$_payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null) || FILE_PATH=""
+    else
+      FILE_PATH=$(printf '%s' "$_payload" | python3 -c 'import json,sys; ti=json.load(sys.stdin).get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")' 2>/dev/null) || FILE_PATH=""
+    fi
+  fi
+fi
+
 if [[ -z "$FILE_PATH" ]]; then exit 0; fi
 if [[ ! -f "$FILE_PATH" ]]; then exit 0; fi
 
diff --git a/incredible_auto_dev/.claude/letter-to-future-sessions.md b/incredible_auto_dev/.claude/letter-to-future-sessions.md
index de29b24a..f7d3bb8a 100644
--- a/incredible_auto_dev/.claude/letter-to-future-sessions.md
+++ b/incredible_auto_dev/.claude/letter-to-future-sessions.md
@@ -51,9 +51,11 @@ pain into its §16 staging section.
   (`claude -p --model <id> 'reply OK'`), flip the tier, resync, update
   `.claude/model-orchestration.md`'s table in the same commit. Never re-pin a per-agent
   `model_override` except as a commented temporary exception — the evals fail on it.
-- **Append-only files grow until they poison prompts.** `lessons.md`, `anti-patterns.md`,
-  goal.md journeys. The dispatch wrappers pre-trim/slice the big ones, but condensation
-  (maintenance protocol §4) still has to happen — a 500-line lessons file is a smell.
+- **Append-only files grow until they poison prompts.** `lessons.md`, the
+  anti-patterns index, goal.md journeys. The dispatch wrappers pre-trim/slice the big
+  ones, but condensation (maintenance protocol §4) still has to happen — a 500-line
+  lessons file is a smell. (The anti-patterns monolith itself was split into
+  `.claude/anti-patterns/` per-entry files for this reason.)
 - **Skills edited without version bumps.** The rendered agent frontmatter carries
   `version:`; bump it with every body/skill change so drift between what an agent file says
   and what a long-running session loaded is diagnosable.
diff --git a/incredible_auto_dev/.claude/maintenance-protocol.md b/incredible_auto_dev/.claude/maintenance-protocol.md
index a2155734..fbf9491a 100644
--- a/incredible_auto_dev/.claude/maintenance-protocol.md
+++ b/incredible_auto_dev/.claude/maintenance-protocol.md
@@ -28,9 +28,11 @@ state files. When this protocol and momentum conflict, the protocol wins.
 
 - **Goal-session lessons** (product/project-specific): the evaluator appends to
   `runs/goal-session-<sid>/state/lessons.md` per its format. Signal only — no routine entries.
-- **Framework lessons** (pipeline/tooling pitfalls that transcend one project): append a
-  numbered entry to `.claude/anti-patterns.md` following its existing format (symptom → root
-  cause → rule). One entry per distinct failure mode; cite the session/iteration where it bit.
+- **Framework lessons** (pipeline/tooling pitfalls that transcend one project): create the
+  next-numbered file under `.claude/anti-patterns/` (`<NN>-<slug>.md` — numbering is frozen,
+  take one past the highest) following the existing format (symptom → root cause → rule),
+  AND add its row to the `README.md` index there (the index↔entries eval enforces the pair).
+  One entry per distinct failure mode; cite the session/iteration where it bit.
 - Format discipline: every lesson states (a) the trigger condition ("Applies to:"), (b) the
   concrete mistake, (c) the checkable rule that prevents it. A lesson without a checkable
   rule is a war story — rewrite it until it's a rule.
@@ -57,7 +59,7 @@ sync is a no-op when the mirrors already exist, so:
 ## 4. Condensation rule (growth control)
 
 When any append-only knowledge file exceeds **~200 lines** (`lessons.md`,
-`.claude/anti-patterns.md`, `letter-to-future-sessions.md` handoff section):
+`letter-to-future-sessions.md` handoff section):
 1. Condense duplicate/superseded entries into their general rule (keep the rule, drop the
    retelling); move historical examples to `<file>.archive.md` beside the original.
 2. Do it in a dedicated commit touching nothing else, message `chore(<file>): condense`.
@@ -69,10 +71,10 @@ When any append-only knowledge file exceeds **~200 lines** (`lessons.md`,
    `**AGENT RULE …:**`) stay in place, no LLM involved. The goal engine runs it warn-only
    at session start for session state files (`lessons.md`, `assumptions.md`) over 200
    lines (knob `CHAIN_AUTO_CONDENSE`, default true). It structurally REFUSES paths under
-   `.claude/` unless `--human` is passed — so `.claude/anti-patterns.md` is condensed
-   ONLY by a human running
-   `bash scripts/automation/lib/condense.sh --human .claude/anti-patterns.md`
-   in its own dedicated commit per rule 2; it also refuses rule 3's files outright.
+   `.claude/` unless `--human` is passed; it also refuses rule 3's files outright.
+   (The anti-patterns monolith this clause used to govern was split into the per-entry
+   tree `.claude/anti-patterns/` — entries stay small, so condensation no longer
+   applies there.)
 
 ## 5. Cache stability
 
@@ -96,4 +98,4 @@ The full ordered checklist — spend gates, per-step evidence, rollback — is `
 2. `./scripts/automation/run-evals.sh` must be green before commit.
 3. If the change alters an artifact format (verdict line, report path, JSON schema): grep for
    every reader of that artifact and update them in the SAME commit (see
-   `.claude/anti-patterns.md` — writer/reader drift is a documented failure class).
+   `.claude/anti-patterns/` — writer/reader drift is a documented failure class).
diff --git a/incredible_auto_dev/.claude/settings.json b/incredible_auto_dev/.claude/settings.json
index d09eb58b..6b806499 100644
--- a/incredible_auto_dev/.claude/settings.json
+++ b/incredible_auto_dev/.claude/settings.json
@@ -370,7 +370,7 @@
         "hooks": [
           {
             "type": "command",
-            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-lint.sh\" \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
+            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-lint.sh\" 2>/dev/null || true"
           }
         ]
       },
@@ -379,7 +379,7 @@
         "hooks": [
           {
             "type": "command",
-            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-write-artifact-quality.sh\" \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
+            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-write-artifact-quality.sh\" 2>/dev/null || true"
           }
         ]
       }
diff --git a/incredible_auto_dev/.claude/skills/goal-authoring.md b/incredible_auto_dev/.claude/skills/goal-authoring.md
index 29af29e0..6c93c132 100644
--- a/incredible_auto_dev/.claude/skills/goal-authoring.md
+++ b/incredible_auto_dev/.claude/skills/goal-authoring.md
@@ -4,7 +4,7 @@ Used by `/goal-init` (interview → author) and, once it ships, by `/goal-lint`
 reuse). `docs/goal.md` is the product constitution: the goal-evaluator treats its
 Must-have journeys as objective ground truth and its Anti-goals as veto rules, so its
 quality decides every downstream iteration. Vague journeys are the documented #1
-failure mode (`.claude/anti-patterns.md` #1, #18).
+failure mode (`.claude/anti-patterns/01-vague-acceptance-criteria.md`, `18-goal-journeys-anti-goals.md`).
 
 ## Interview ground rules
 
diff --git a/incredible_auto_dev/.claude/skills/plain-language.md b/incredible_auto_dev/.claude/skills/plain-language.md
new file mode 100644
index 00000000..44f749c7
--- /dev/null
+++ b/incredible_auto_dev/.claude/skills/plain-language.md
@@ -0,0 +1,72 @@
+# Skill: Plain Language
+
+How to write the prose a product owner reads. This is the shared writing standard
+for owner-facing sections (plain-words blocks, stories, narrations, README text,
+recommendations). It does not change any machine-parsed format.
+
+## Who you are writing for
+
+- The product owner. Not a developer.
+- Not a native English reader. Dense English costs them real effort.
+- They have two questions: "is my product OK?" and "what should I do next?"
+- They do not know the pipeline's internal names, and they should not need to.
+
+## Hard rules
+
+1. **Short sentences.** One idea per sentence. Prefer under ~20 words. Split long
+   sentences instead of chaining clauses with dashes and parentheses.
+2. **Everyday words.** "stopped" not "halted"; "broken" not "regressed" (say
+   "worked before, broken now"); "check" not "audit" — unless the code word itself
+   is the subject, then explain it once.
+3. **No bare internal names in plain sections.** No agent names, no file paths, no
+   environment variables, no ticket codes (REL-14, EVO-1, §16). If one must
+   appear, say in words what it is: "the roadmap's staging list (§16), which a
+   human reviews".
+4. **Every ID carries its friendly name.** Write `J-04 "Sign in with email"`,
+   never a bare ID list. Same for UT-nn tests: say what the test checks.
+5. **Describe what the user sees, not the code.** "The login page rejects a
+   correct password", not a function, class, endpoint, or stack trace.
+6. **End with an action.** Say what happens next, or what the owner should do,
+   in one sentence a non-programmer could act on.
+
+## Status words (single source)
+
+The canonical plain sentences for every session status and evaluator verdict live
+in `scripts/automation/lib/plain-language.sh`, and the owner-facing glossary is
+`docs/READING-REPORTS.md`. Reuse those words; do not invent new translations.
+Quick table for the most common codes:
+
+| Code | Plain words |
+|---|---|
+| CONTINUE | normal progress — the chain builds the next piece by itself |
+| ESCALATE | something tricky came up; the next round is slower and more careful |
+| REGRESSION | something that worked before is broken now |
+| STALLED | the chain cannot make progress alone and is asking for help |
+| GOAL_ACHIEVED | every must-have journey works; the session finishes |
+| passing / failing / regressed | working / broken / worked before, broken now |
+
+## Three examples
+
+- Bad: "Added POST /api/v1/items endpoint with SQLAlchemy persistence."
+  Good: "You can now create new items, and they are saved."
+- Bad: "J-02, J-05 remain failing; BQA lane SKIPPED-INFRA."
+  Good: "Two journeys are not working yet: J-02 \"Mark an item done\" and J-05
+  \"Filter the list\". The browser test could not run this round, so J-05 was
+  not re-checked."
+- Bad: "Iter-4 verdict demoted per gate; see eval.md."
+  Good: "A safety rule overrode the evaluator's claim this round — the stricter
+  answer wins. The evaluation file explains which rule fired."
+
+## Never simplify these
+
+Machine-parsed surfaces must stay byte-identical. Plain language is added NEXT TO
+them, never instead of them:
+
+- Verdict lines (the bold `Verdict:` marker lines scripts grep) and their
+  ALL-CAPS values.
+- Required section headings (H2 names like `In plain words`), the three
+  `What you can do now / What changed this time / What's next` labels, and any
+  field label a template marks as required.
+- JSON files, keys, and schemas; artifact file names and paths; exit codes.
+- Evidence references: keep exact file paths and screenshot names in evidence
+  fields — precision there is the point.
diff --git a/incredible_auto_dev/.claude/workflow.md b/incredible_auto_dev/.claude/workflow.md
index f223303d..429e5edb 100644
--- a/incredible_auto_dev/.claude/workflow.md
+++ b/incredible_auto_dev/.claude/workflow.md
@@ -14,7 +14,7 @@ Plan → Test Plan → Dev+Review loop → QA loop → Audit loop → Finalize
 
 | Stage | Script | Agent | Output |
 |-------|--------|-------|--------|
-| 1. Plan | `run-phase.sh` (internal) | orchestrator | `runs/<phase>/plan.md` (reads `docs/goal.md` + `docs/architecture/` + `.claude/architecture/` + prior handoffs first) |
+| 1. Plan | `run-phase.sh` (internal) | orchestrator | `runs/<phase>/plan.md` (reads `docs/goal.md` + prior handoffs + `docs/architecture/` if present — created by update-docs.sh after the first finalized phase) |
 | 2. Test Plan | `generate-test-plan.sh` | qa (mode: generate) | `reports/qa/<phase>-test-plan.md` — dispatch skipped (loudly logged) when the spec already lists its own tests (`## Test`-titled section or ≥3 `TC-` lines) and `CHAIN_SKIP_TESTPLAN_IF_PRESENT=true` (default `false`; TOKEN-3) |
 | 3. Dev + Review | `dev-phase.sh` + `review-phase.sh` | developer, reviewer | `docs/handoffs/<phase>-dev.md`, `reports/phase-{N}-implementation-summary.md` |
 | 4. UI Impact Analysis | `ui-impact-phase.sh` | ui-impact-analyst | `reports/phase-{N}-user-visible-changes.md`, `reports/phase-{N}-ui-surface-map.md` |
@@ -66,8 +66,8 @@ Agents ONLY communicate through filesystem artifacts. No free-form messages betw
 | UX regression report | `reports/phase-{N}-ux-regression.md` | ux-regression-reviewer | phase-closure-auditor |
 | Closure verdict | `reports/phase-{N}-closure-verdict.md` | phase-closure-auditor | finalize-phase.sh |
 | Project goal | `docs/goal.md` | Human | orchestrator, developer, reviewer, qa |
-| Project architecture | `docs/architecture/*.md` | update-docs.sh | orchestrator, developer |
-| Framework architecture | `.claude/architecture/*.md` | update-docs.sh | All agents (reference) |
+| Project architecture | `docs/architecture/*.md` (if present; created after the first finalized phase — absence is normal early on) | update-docs.sh | orchestrator, developer |
+| Framework architecture | `.claude/architecture/*.md` | update-docs.sh | Framework maintainers (reference) |
 
 ---
 
@@ -237,13 +237,12 @@ The `Frontend Present:` line is machine-read by `qa-phase.sh` to decide whether
 
 ## Model Tier Rationale
 
-| Tier | Model | Used for |
-|------|-------|----------|
-| strong | claude-opus-5 | Judgment: goal evaluation/decomposition, skeptical audit, confirms |
-| standard | claude-sonnet-5 | Solid tasks: code review, test plan generation |
-| light | claude-haiku-4-5 | Routine workflow: QA execution, git/GitHub operations |
-
-Model assignments: each agent picks a tier (`model_tier`) in `agents/<name>/agent.yaml`; the tier resolves to a concrete model in `config/model-tiers.yaml`. Edit those, then re-render with `python3 scripts/automation/sync-cli-assets.py --cli claude` and commit the regenerated `.claude/agents/*.md`.
+Each agent picks a tier (`model_tier`) in `agents/<name>/agent.yaml`; the tier resolves
+to a concrete model in `config/model-tiers.yaml` — the ONLY place model ids live. The
+prose tier table (which model, which class of work, why) is maintained once, in
+`.claude/model-orchestration.md` §1, kept current per maintenance-protocol §6. After
+editing tiers: re-render with `python3 scripts/automation/sync-cli-assets.py --cli claude`
+and commit the regenerated `.claude/agents/*.md`.
 
 ---
 
diff --git a/incredible_auto_dev/CLAUDE.md b/incredible_auto_dev/CLAUDE.md
index 80a83f26..0153396e 100644
--- a/incredible_auto_dev/CLAUDE.md
+++ b/incredible_auto_dev/CLAUDE.md
@@ -24,15 +24,15 @@ Both modes run on **Claude Code** (default) or **OpenAI Codex CLI** (`--cli code
 | File | Contents | Who reads it |
 |------|----------|--------------|
 | `.claude/core.md` | Universal quality rules, testing checklist, security baseline, token policy | **All agents** |
-| `.claude/workflow.md` | Pipeline stages, retry policy, artifact locations, verdict formats, UI evolution policy | **All agents** |
+| `.claude/workflow.md` | Pipeline stages, retry policy, artifact locations, verdict formats, UI evolution policy | goal-decomposer, reviewer; on-demand pipeline reference for any other agent |
 | `.claude/project-template.md` | Project stack, test/run commands, architecture principles | **All agents** |
 | `.claude/model-orchestration.md` | Model×effort table, delegation package, reporting contract, escalation ladder, non-self-verification rules | Orchestrator, pump, anyone dispatching agents |
-| `.claude/judgment-rubrics.md` | Executable judgment criteria (escalation, definition-of-done, stop-and-ask, wrong-direction signals, evidence floors, honesty) with ✚/✖ examples | Judges (evaluator, auditor, decomposer, reviewer) and anyone making verdict-class calls |
-| `.claude/delegation-templates.md` | Fill-in dispatch templates (search/implement/refactor/research/review) | Anyone dispatching agents |
+| `.claude/judgment-rubrics.md` | Executable judgment criteria (escalation, definition-of-done, stop-and-ask, wrong-direction signals, evidence floors, honesty) with ✚/✖ examples | auditor (direct); goal-evaluator (via its methodology skill); anyone making verdict-class calls |
+| `.claude/delegation-templates.md` | Fill-in dispatch templates (search/implement/refactor/research/review) | Interactive maintainer sessions dispatching ad-hoc subagents |
 | `.claude/maintenance-protocol.md` | Which files may be edited autonomously vs. need the user; the resync invariant; lessons format; condensation rule | Anyone editing framework/instruction files |
-| `.claude/anti-patterns.md` | Documented failure modes from production use | Orchestrator, reviewer, auditor; add new ones per maintenance protocol §2 |
+| `.claude/anti-patterns/` | Failure-mode tree: README index + one file per numbered entry — scan the index, open only matching entries | Orchestrator, reviewer, auditor; add new ones per maintenance protocol §2 |
 | `.claude/letter-to-future-sessions.md` | How this system degrades and what to check first | New sessions doing framework work |
-| `.claude/architecture/` | System architecture, agent catalog, pipeline flow, artifact map | Reference (all agents) |
+| `.claude/architecture/` | System architecture, agent catalog, pipeline flow, artifact map | Framework maintainers only — pipeline agents must NOT read these (orchestrator rule) |
 
 ## AGENTS AND SKILLS
 
diff --git a/incredible_auto_dev/README.md b/incredible_auto_dev/README.md
index 0538b136..418800e7 100644
--- a/incredible_auto_dev/README.md
+++ b/incredible_auto_dev/README.md
@@ -38,7 +38,7 @@ The multi-CLI infrastructure is in place and the Claude path is verified non-reg
 - [ ] **Real Codex end-to-end run + hardening.** `_codex_invoke` quota/error regexes in `lib/quota-retry.sh` are best-guess. First real `--cli codex` run will reveal the actual OpenAI rate-limit/error wording to match. Expect 1–2 tightening passes.
 - [ ] **Codex stream parsing.** `lib/codex_stream_renderer.py` handles several plausible event shapes; confirm against real `codex exec --json` NDJSON and trim to the actual schema.
 - [ ] **Retire legacy `.claude/` files from git.** `.claude/agents/*.md`, `.claude/settings.json`, `.claude/hooks/*`, `.claude/skills/*` are still tracked and regenerated on sync (producing small, functionally-identical cosmetic diffs). Move them to `.gitignore` and `git rm --cached` once the Claude no-regression run passes.
-- [ ] **`hooks/lib/normalize-input.sh` / `normalize-output.sh`.** Planned shims so one hook script reads a uniform input schema and writes a uniform allow/block decision across both CLIs. SEC-7 inlined the normalization in the two Bash guards (argv → stdin `.tool_input.command` fallback + Claude `permissionDecision` deny-JSON); the shim remains TODO for deduplication and for the PostToolUse hooks (`$CLAUDE_TOOL_INPUT_FILE_PATH` is equally nonexistent — they need the stdin `.tool_input.file_path` treatment; advisory-only, so inert ≠ security hole).
+- [ ] **`hooks/lib/normalize-input.sh` / `normalize-output.sh`.** Planned shims so one hook script reads a uniform input schema and writes a uniform allow/block decision across both CLIs. SEC-7 inlined the normalization in the two Bash guards (argv → stdin `.tool_input.command` fallback + Claude `permissionDecision` deny-JSON) and CTX-1 did the same for the PostToolUse pair (stdin `.tool_input.file_path`, advisory); the shim remains TODO purely for deduplication.
 - [ ] **Architecture docs.** `.claude/architecture/*.md` still describe the pre-migration Claude-only layout; update for the neutral source + adapter model.
 - [ ] **MCP servers in neutral source.** `policy/mcp-servers.yaml` is a stub; Claude MCP/plugins currently live in `adapters/claude/passthrough/`. Promote to neutral source when a shared MCP definition is actually needed.
 - [ ] **Mixed-CLI runs (per-agent override).** Architecture supports a per-agent `cli:` field in `agent.yaml`; not wired up. Deferred until there's a real use case.
@@ -230,6 +230,10 @@ means it's an early or backend-only iteration with no features to walk through.
 
 ### Outputs produced
 
+**New to these files and the status codes inside them?** Read
+[`docs/READING-REPORTS.md`](docs/READING-REPORTS.md) — a plain-language guide to
+which report to open and what every code means.
+
 | Artifact | Where | Audience |
 |----------|-------|----------|
 | Plain-language section + Watch-it-work gallery + technical accordions | `reports/phase-<phase>-summary.html` | Everyone |
@@ -445,7 +449,7 @@ bash scripts/automation/render-summary.sh --session-index <sid>        # re-rend
 | `runs/goal-session-<sid>/state/journey-history.json` | Per-journey pass/fail/regressed status across iterations |
 | `runs/goal-session-<sid>/telemetry.jsonl` | Structured event log for the session — see [`docs/goal-mode-telemetry.md`](docs/goal-mode-telemetry.md) |
 
-**Temp-file hygiene:** every run gets its own `$CHAIN_TMP_ROOT/iad.<run-id>.<pid>` dir (root default `~/.cache/iad` — a big un-quota'd disk, NOT the quota'd tmpfs `/tmp`), exported as `TMPDIR`, so pytest/playwright/service-log temp files are isolated per run and removed on exit (goal mode clears the previous iteration's dir at each iteration boundary). A startup janitor sweeps strays from crashed runs across the root and legacy `/tmp` — stale `iad.*` dirs, `bench-*`/`judgment-*` scratch, `pytest-of-$USER` entries, and the `shared/` interactive-TMPDIR dir — and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (goal mode pauses as resumable `AWAITING_DISK` only when the root filesystem stays critically low). Self-service cleanup any agent can run: `./scripts/automation/tmp-doctor.sh [--status|--clean|--aggressive]`. Knobs: `CHAIN_TMPDIR_DISABLE=true` (leave the environment alone), `CHAIN_TMP_JANITOR=false` (skip the sweep), `CHAIN_TMP_ROOT` (base dir), `CHAIN_TMP_LEGACY_ROOTS` (extra janitor roots, default `/tmp`), `CHAIN_TMP_MAX_AGE_HOURS=24` / `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72` (age gates), `CHAIN_BENCH_KEEP=2` (bench scratch retention), `CHAIN_TMP_MIN_FREE_MB=2048` / `CHAIN_TMP_HARD_MIN_FREE_MB=512` / `CHAIN_TMP_PROBE_MB=32` (disk guard), `CHAIN_TMP_DISK_GUARD=false` (disable the guard). See `.claude/anti-patterns.md` #21.
+**Temp-file hygiene:** every run gets its own `$CHAIN_TMP_ROOT/iad.<run-id>.<pid>` dir (root default `~/.cache/iad` — a big un-quota'd disk, NOT the quota'd tmpfs `/tmp`), exported as `TMPDIR`, so pytest/playwright/service-log temp files are isolated per run and removed on exit (goal mode clears the previous iteration's dir at each iteration boundary). A startup janitor sweeps strays from crashed runs across the root and legacy `/tmp` — stale `iad.*` dirs, `bench-*`/`judgment-*` scratch, `pytest-of-$USER` entries, and the `shared/` interactive-TMPDIR dir — and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (goal mode pauses as resumable `AWAITING_DISK` only when the root filesystem stays critically low). Self-service cleanup any agent can run: `./scripts/automation/tmp-doctor.sh [--status|--clean|--aggressive]`. Knobs: `CHAIN_TMPDIR_DISABLE=true` (leave the environment alone), `CHAIN_TMP_JANITOR=false` (skip the sweep), `CHAIN_TMP_ROOT` (base dir), `CHAIN_TMP_LEGACY_ROOTS` (extra janitor roots, default `/tmp`), `CHAIN_TMP_MAX_AGE_HOURS=24` / `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72` (age gates), `CHAIN_BENCH_KEEP=2` (bench scratch retention), `CHAIN_TMP_MIN_FREE_MB=2048` / `CHAIN_TMP_HARD_MIN_FREE_MB=512` / `CHAIN_TMP_PROBE_MB=32` (disk guard), `CHAIN_TMP_DISK_GUARD=false` (disable the guard). See `.claude/anti-patterns/21-shared-tmp-accumulation.md`.
 
 ## Subrepo Usage
 
diff --git a/incredible_auto_dev/adapters/claude/sync.py b/incredible_auto_dev/adapters/claude/sync.py
index 8167f718..c9be2ab2 100644
--- a/incredible_auto_dev/adapters/claude/sync.py
+++ b/incredible_auto_dev/adapters/claude/sync.py
@@ -9,7 +9,7 @@ Generates:
   .claude/commands/<name>.md   (slash commands, mirrored from commands/)
 
 Leaves alone:
-  .claude/core.md, workflow.md, anti-patterns.md, project-template.md
+  .claude/core.md, workflow.md, the anti-patterns/ tree, project-template.md
   .claude/architecture/
   .claude/settings.local.json, .example
 """
@@ -191,31 +191,27 @@ def _hooks_block_for_claude() -> dict:
         entries = []
         for matcher, basename in by_event[event]:
             # Claude Code passes hook input as JSON on stdin (.tool_input.*);
-            # $CLAUDE_TOOL_INPUT_COMMAND was never a real env var, so the Bash
-            # guards read stdin themselves (argv remains the test-harness /
-            # Codex path) and return decisions as hookSpecificOutput JSON on
-            # stdout with exit 0 (SEC-7). Every hook is wrapped `|| true`: on
-            # Claude the exit code carries no signal (exit 1 is a NON-blocking
-            # error; the stdout JSON is the decision channel) and a hook crash
-            # must never surface into the transcript. install-security-gate
-            # keeps stderr un-redirected so its warn banners reach debug logs.
+            # $CLAUDE_TOOL_INPUT_COMMAND / $CLAUDE_TOOL_INPUT_FILE_PATH were
+            # never real env vars, so every hook reads stdin itself (argv
+            # remains the test-harness / Codex path): the PreToolUse guards
+            # extract .tool_input.command and return decisions as
+            # hookSpecificOutput JSON on stdout with exit 0 (SEC-7); the
+            # PostToolUse hooks extract .tool_input.file_path and stay
+            # advisory (stderr warnings only, CTX-1). Every hook is wrapped
+            # `|| true`: on Claude the exit code carries no signal (exit 1 is
+            # a NON-blocking error; stdout JSON is the decision channel) and a
+            # hook crash must never surface into the transcript.
+            # install-security-gate keeps stderr un-redirected so its warn
+            # banners reach debug logs.
             tail = " || true" if basename == "install-security-gate.sh" else " 2>/dev/null || true"
             cmd_path = f"$CLAUDE_PROJECT_DIR/.claude/hooks/{basename}"
-            if event == "PostToolUse":
-                # FIXME(follow-up): $CLAUDE_TOOL_INPUT_FILE_PATH is likewise not
-                # a real env var — the PostToolUse hooks need the stdin
-                # (.tool_input.file_path) treatment; they are advisory-only, so
-                # their inertness is not a security hole (roadmap SEC-7 note).
-                arg = ' "$CLAUDE_TOOL_INPUT_FILE_PATH"'
-            else:
-                arg = ""
             entries.append(
                 {
                     "matcher": matcher,
                     "hooks": [
                         {
                             "type": "command",
-                            "command": f'bash "{cmd_path}"{arg}{tail}',
+                            "command": f'bash "{cmd_path}"{tail}',
                         }
                     ],
                 }
diff --git a/incredible_auto_dev/agents/demo-narrator/agent.yaml b/incredible_auto_dev/agents/demo-narrator/agent.yaml
index 899e091f..72280d68 100644
--- a/incredible_auto_dev/agents/demo-narrator/agent.yaml
+++ b/incredible_auto_dev/agents/demo-narrator/agent.yaml
@@ -12,6 +12,6 @@ tools_allowed:
 - Glob
 - Grep
 - Write
-version: 2.0.0
-last_updated: '2026-05-22'
+version: 2.1.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/demo-narrator/body.md b/incredible_auto_dev/agents/demo-narrator/body.md
index e112c77d..f8d89290 100644
--- a/incredible_auto_dev/agents/demo-narrator/body.md
+++ b/incredible_auto_dev/agents/demo-narrator/body.md
@@ -17,6 +17,9 @@ testing. Favor the flows that were already verified working this iteration.
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
+1. `.claude/skills/plain-language.md` — the shared plain-writing standard. It
+   governs every `title` and `narration` field you write.
+
 The dispatch wrapper passes you: a `mode` (`record`, `live`, or `session`), a
 `phase-id` (or a session `sid` in session mode), the `FRONTEND_URL`, and the
 **Demo JSON output path** to write.
diff --git a/incredible_auto_dev/agents/developer/agent.yaml b/incredible_auto_dev/agents/developer/agent.yaml
index 87b31360..02ec5694 100644
--- a/incredible_auto_dev/agents/developer/agent.yaml
+++ b/incredible_auto_dev/agents/developer/agent.yaml
@@ -3,6 +3,6 @@ description: Implementation agent. Reads the execution plan from runs/<phase>/pl
   following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and
   fixes only the listed issues. Writes dev handoff when complete.
 model_tier: standard
-version: 1.1.1
-last_updated: '2026-07-03'
+version: 1.1.2
+last_updated: '2026-07-25'
 body: body.md
diff --git a/incredible_auto_dev/agents/developer/body.md b/incredible_auto_dev/agents/developer/body.md
index ec668225..9ac5e845 100644
--- a/incredible_auto_dev/agents/developer/body.md
+++ b/incredible_auto_dev/agents/developer/body.md
@@ -9,7 +9,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — understand the project's overall goal before implementing
 2. `.claude/project-template.md` — stack configuration, test commands, architecture principles
-3. `docs/architecture/*.md` — understand existing project architecture
+3. `docs/architecture/*.md` — existing project architecture (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `runs/<phase>/plan.md` — execution plan (what to build)
 5. Phase spec at `docs/phases/<phase>.md` — requirements and definition of done
 6. Relevant existing code in the project
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index e6f8c5b4..7b816063 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.7.0
-last_updated: '2026-07-18'
+version: 1.8.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index 128bf3c9..ae726d57 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -198,6 +198,17 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 <only present when verdict is GOAL_ACHIEVED, REGRESSION, or STALLED — explain why halting>
 ```
 
+### 6b. Plain-language rule for prose fields
+
+The session owner is not a native English reader. In the PROSE fields only — `Reasoning` and `Next-step recommendation` in evaluator-log.md (step 4), and the `## Summary`, `## Next-Step Recommendation`, and `## Halt Justification` sections of eval.md (step 6) — write plain English:
+
+- Short sentences. Everyday words. No idioms.
+- Whenever you name a journey ID, put its short name next to it: J-04 "Sign in with email" — never a bare ID list.
+- Describe what the user would see, not internal code: "the login page rejects a correct password", not a function, class, or variable name. (Evidence references keep their file paths — that rule is unchanged.)
+- End the recommendation with one sentence saying what should happen next, phrased so a non-programmer could act on it or approve it.
+
+This rule changes WORDING ONLY. It does not change any machine-parsed format: the verdict lines and their allowed values defined elsewhere in this document, the depth-recommendation line, all headings, table shapes, JSON schemas, and file paths stay exactly as specified.
+
 ### 7. Overwrite iteration-state.md (the next planner's digest)
 
 After eval.md is written (so your fresh verdict is its newest entry), write
diff --git a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
index 883df498..f75428e9 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
+++ b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
@@ -8,6 +8,6 @@ model_tier: standard
 tools_allowed:
 - Read
 - Write
-version: 1.1.0
-last_updated: '2026-07-07'
+version: 1.2.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/iteration-summarizer/body.md b/incredible_auto_dev/agents/iteration-summarizer/body.md
index b6879536..b242f264 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/body.md
+++ b/incredible_auto_dev/agents/iteration-summarizer/body.md
@@ -21,6 +21,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `templates/iteration-summary.md` — the exact section structure your output must follow
 2. `.claude/skills/visible-change-summarizer.md` — tone and brevity guidance for user-facing summaries
+3. `.claude/skills/plain-language.md` — the shared plain-writing standard (short sentences, IDs always with friendly names, the status word table). It governs the `## In plain words` block, the project story, and the delivered wrap.
 
 ## Input files (read only what exists)
 
diff --git a/incredible_auto_dev/agents/orchestrator/agent.yaml b/incredible_auto_dev/agents/orchestrator/agent.yaml
index b861b3d8..8d5c092f 100644
--- a/incredible_auto_dev/agents/orchestrator/agent.yaml
+++ b/incredible_auto_dev/agents/orchestrator/agent.yaml
@@ -3,6 +3,6 @@ description: Phase execution planner. When invoked by run-phase.sh, reads CLAUDE
   then writes a concise execution plan to runs/<phase>/plan.md. The shell script (run-phase.sh) drives
   the dev/review/QA loop; the orchestrator's job is planning only.
 model_tier: standard
-version: 1.0.0
-last_updated: '2026-05-04'
+version: 1.0.1
+last_updated: '2026-07-25'
 body: body.md
diff --git a/incredible_auto_dev/agents/orchestrator/body.md b/incredible_auto_dev/agents/orchestrator/body.md
index 139cb8fd..42e14ff6 100644
--- a/incredible_auto_dev/agents/orchestrator/body.md
+++ b/incredible_auto_dev/agents/orchestrator/body.md
@@ -9,7 +9,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — project goal, vision, success criteria (ensure phase aligns with this)
 2. `.claude/project-template.md` — project-specific stack, architecture principles
-3. `docs/architecture/` — project architecture docs (understand what already exists)
+3. `docs/architecture/` — project architecture docs (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `docs/handoffs/*-dev.md` — prior phase handoffs (what was already built)
 5. The phase spec at `docs/phases/<phase>.md`
 
diff --git a/incredible_auto_dev/agents/readme-maintainer/agent.yaml b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
index 57ec9fc1..57d070fd 100644
--- a/incredible_auto_dev/agents/readme-maintainer/agent.yaml
+++ b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Edit
 - Glob
 - Grep
-version: 1.0.0
-last_updated: '2026-06-04'
+version: 1.1.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/readme-maintainer/body.md b/incredible_auto_dev/agents/readme-maintainer/body.md
index 25ab2154..51d06b52 100644
--- a/incredible_auto_dev/agents/readme-maintainer/body.md
+++ b/incredible_auto_dev/agents/readme-maintainer/body.md
@@ -22,6 +22,8 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. The existing `README.md` at the repo root, if present.
 4. `templates/project-readme.md` — the skeleton to start from **only if `README.md`
    is absent**.
+5. `.claude/skills/plain-language.md` — the shared plain-writing standard for
+   everything you write into the AUTO blocks.
 
 ## Capability inputs (read what exists, skip what doesn't)
 
diff --git a/incredible_auto_dev/agents/retro-analyst/agent.yaml b/incredible_auto_dev/agents/retro-analyst/agent.yaml
index 3aa43e00..580d6006 100644
--- a/incredible_auto_dev/agents/retro-analyst/agent.yaml
+++ b/incredible_auto_dev/agents/retro-analyst/agent.yaml
@@ -6,6 +6,6 @@ model_tier: light
 tools_allowed:
 - Read
 - Write
-version: 1.0.0
-last_updated: '2026-07-10'
+version: 1.1.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/retro-analyst/body.md b/incredible_auto_dev/agents/retro-analyst/body.md
index deb5a3d6..7c9d511c 100644
--- a/incredible_auto_dev/agents/retro-analyst/body.md
+++ b/incredible_auto_dev/agents/retro-analyst/body.md
@@ -38,6 +38,14 @@ Number items RETRO-1 … RETRO-5, at most 5, each ≤20 lines, in this exact sha
 
 Hard rule: no Evidence line → no item. Every Evidence entry names the digest section and quotes the line(s) verbatim, e.g. `Evidence: Friction counters — "Quota pauses: 3"`. Zero items is a valid output: when nothing recurred, the Candidate items body is exactly `nothing recurred worth proposing` plus one sentence saying why (e.g. all counters zero, lessons product-only).
 
+Plain-writing rules (the report is read by a non-developer owner first):
+- The FIRST sentence of every **Problem:** must be plain English: short, everyday
+  words, says who hits the pain and when. Technical detail goes in the second
+  sentence.
+- Never use a bare internal codename (EVO-1, §16, REL-n, a lane or tripwire name)
+  without saying in words what it is.
+- Keep the header's code legend line exactly as the skeleton shows it.
+
 ## Output
 
 Write exactly ONE file — the output path from your dispatch prompt (`reports/goal-session-<sid>-retro.md`), overwriting any existing file:
@@ -45,8 +53,11 @@ Write exactly ONE file — the output path from your dispatch prompt (`reports/g
 ```
 # Session retro — <sid>
 
-> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
-> per EVO-1; nothing here is scheduled work.
+> **Ideas only — nothing here is scheduled work.** These are suggestions for
+> improving the build system itself, not your product. A human reviews them and
+> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
+> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
+> = chance a change breaks something else.
 
 **Session:** <sid> · **Terminal status:** <from Outcome> · **Iterations:** <from Outcome>
 
diff --git a/incredible_auto_dev/commands/goal-status.md b/incredible_auto_dev/commands/goal-status.md
index f318de03..ebcfada4 100644
--- a/incredible_auto_dev/commands/goal-status.md
+++ b/incredible_auto_dev/commands/goal-status.md
@@ -27,3 +27,7 @@ the engine, dispatch agents, or write anything.
    the opt-in `--intent-checkpoint` "is this the product you wanted?" pause —
    resuming acknowledges it), **orphaned** (dead engine PID — `/goal-resume`),
    or **finished** (and the final verdict).
+7. **Plain words first:** lead the summary with the status translated into a
+   plain sentence (the wording table lives in `docs/READING-REPORTS.md`), with
+   the raw code in parentheses — e.g. "The chain is paused and waiting for your
+   blueprint review (`AWAITING_BLUEPRINT_APPROVAL`)." Same for the last verdict.
diff --git a/incredible_auto_dev/docs/READING-REPORTS.md b/incredible_auto_dev/docs/READING-REPORTS.md
new file mode 100644
index 00000000..c87148eb
--- /dev/null
+++ b/incredible_auto_dev/docs/READING-REPORTS.md
@@ -0,0 +1,187 @@
+# Reading the chain's output — a plain guide
+
+This page explains, in plain words, everything the chain prints and writes for you:
+which file to open, what each status code means, and what the short codes stand for.
+Keep it open the first few times you run the chain.
+
+(For how to *start* a run, see [`goal-mode-quickstart.md`](goal-mode-quickstart.md).
+This page is only about reading what comes out.)
+
+---
+
+## 1. Which file do I open?
+
+Start at the top of this list. The first two cover 90% of what you need.
+
+### `reports/goal-session-<sid>-index.html` — the session page (open this first)
+The one-page overview of a goal session. It leads with "The story so far" (a plain
+narrative of how your product has grown), then the latest demo gallery with
+screenshots, a journey progress matrix, and one card per iteration.
+**Check three things:** does the story match what you wanted? are the journey rows
+turning green over time? does the newest card's badge look healthy?
+
+### `reports/phase-<iter>-summary.html` — one iteration, one page
+The per-iteration view. It leads with **"In plain words"** (what you can do now, what
+changed this time, what's next) and a "Watch it work" screenshot gallery. Technical
+sections sit below, collapsed — you can ignore them.
+**Check three things:** the "In plain words" block, the verdict badge, the gallery.
+
+### `reports/phase-<iter>-what-to-click.md` — try it yourself in 5 minutes
+A short numbered guide: exact pages to open, buttons to press, and what you should
+see. No developer knowledge needed. Written for full iterations and phases.
+
+### `runs/goal-session-<sid>/iter-<N>/eval.md` — why the loop stopped
+The evaluator's explanation for an iteration: a summary, evidence per journey, and a
+recommendation. The terminal points you here when the chain halts. Read the
+`## Summary` and `## Next-Step Recommendation` sections; skip the tables unless
+you're curious.
+
+### `runs/goal-session-<sid>/state/blueprint.md` — the app's floor plan (pause: review it)
+When the chain pauses with "blueprint approval needed", it wants you to check two
+things it drafted: the navigation plan (does every feature have an obvious home?)
+and the data contract (each shared number has exactly one source). Edit the file
+directly — your edits ARE the approval — then resume.
+
+### `runs/goal-session-<sid>/state/intent-review.md` — mid-session checkpoint (pause: answer it)
+Appears only if you enabled the intent checkpoint. It shows progress and asks: is
+this still the product you wanted? Edit `docs/goal.md` if the direction drifted,
+then resume.
+
+### `reports/goal-session-<sid>-delivered.html` — the finish-line page
+Written once, when the goal is achieved. A friendly wrap-up of everything the
+product can do, with the final walkthrough embedded. The `.md` next to it is the
+text version.
+
+### `reports/phase-<iter>-demo-script.md` and `-demo-results.md` — the guided tour
+The narrated walkthrough behind the gallery: each step has a plain sentence, the
+exact action taken, and a screenshot (`reports/demo/<iter>/step-NN.png`). Steps
+marked `[NEW]` were added this iteration. A failed demo step is a soft note, never
+a failure of your product's tests.
+
+### `reports/phase-<iter>-user-visible-changes.md` — what users can now do
+A plain list of new abilities, visible UI changes, changed behavior, and things
+built in the backend that have no UI yet ("not visible yet").
+
+### `reports/goal-session-<sid>-retro.md` — ideas for improving the chain itself
+Written after a session ends. Suggestions for the framework (not your product),
+for a human to accept or ignore. Nothing in it is scheduled work.
+
+### Deeper, technical reports (fine to skip)
+Written for the pipeline and for developers; the summary pages above already
+digest them:
+- `reports/reviews/<iter>-review.md` — code review, verdict PASS / FAIL.
+- `reports/qa/<iter>-qa.md` and `-test-plan.md` — test runs (test cases are `TC-nn`).
+- `reports/phase-<iter>-ui-test-plan.md` / `-ui-test-results.md` — browser tests (`UT-nn`)
+  with screenshots as evidence.
+- `reports/phase-<iter>-ui-surface-map.md`, `-ux-regression.md`, `-closure-verdict.md`,
+  `reports/qa/<iter>-ui-audit.md` — UI coverage and closure gates.
+- `docs/handoffs/<iter>-dev.md` / `-audit.md`, `reports/phase-<iter>-implementation-summary.md`
+  — developer handoffs and the auditor's report.
+- `runs/goal-session-<sid>/iter-<N>/coherence.md` — checks new code didn't duplicate
+  data sources or hide features outside the navigation.
+- `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — appears only if you edited
+  `docs/goal.md` mid-session; lists journeys that must be re-verified.
+- `runs/<...>/status.json`, `session.json`, `summary.json`, `plan.md`,
+  `journey-history.json`, `state/project-story.md` — machine state and sources the
+  HTML pages are built from. You never need to open them.
+
+---
+
+## 2. What the status codes mean
+
+These appear in the terminal, in `session.json`, and on the HTML badges. The
+terminal prints the same plain sentences next to them; this is the full list.
+
+### Session end / pause statuses (goal mode)
+
+| Code | In plain words |
+|---|---|
+| `GOAL_ACHIEVED` | The goal is complete: every must-have journey works and no rule was broken. |
+| `BUDGET_EXHAUSTED` | The session stopped because it reached the iteration limit you set (`--max-iter`). Nothing is broken. Resume with a higher limit to build more. |
+| `STALLED` | The chain stopped because it could not make progress on its own. What was built so far still works. Read the last evaluation, unblock the problem (or edit `docs/goal.md`), then resume. |
+| `REGRESSION_HALT` | Something that worked before is broken now, so the chain stopped to protect your product. After you fix or accept the break, resume with `--acknowledge-regression`. |
+| `ABORTED` | The run was interrupted before it finished the iteration. Nothing is lost — resume when ready. |
+| `ABORT_MALFORMED` | The evaluator wrote an unreadable verdict twice in a row, so the chain stopped instead of guessing. Your product is unchanged. |
+| `GATE_BLOCKED` | A project rule (gate) rejected this iteration's plan, so the chain paused before building anything. |
+| `AWAITING_BLUEPRINT_APPROVAL` | Paused, not broken — waiting for you to review `state/blueprint.md` and resume. |
+| `AWAITING_INTENT_REVIEW` | Paused, not broken — waiting for you to finish the intent checkpoint and resume. |
+| `AWAITING_PUMP` | The Claude Code session that runs the agents went away, so the engine paused safely. Re-open Claude Code in this repo and run `/goal-resume`. |
+| `AWAITING_GITHUB_AUTH` | Paused because the chain cannot push to GitHub (login missing or expired). Run `gh auth login`, then resume. |
+| `AWAITING_DISK` | Paused because this computer is low on disk space — the chain never builds in that state. Free space, then resume. |
+| `AWAITING_HOST_GUARD` | Paused because this computer's hardware protection is not in place — the chain never builds unprotected. Fix the printed reason (`project-extensions/host-guard/README.md`), then resume. |
+| `in_progress` | The session is running normally. |
+
+### The evaluator's per-iteration verdict
+
+Printed after every iteration as `Verdict: <code>`.
+
+| Code | In plain words |
+|---|---|
+| `CONTINUE` | Normal progress — the chain plans and builds the next piece by itself. |
+| `ESCALATE` | The last round found something tricky, so the next round uses the slower, more careful pipeline. |
+| `REGRESSION` | Something that worked before is broken — the chain is stopping so you can look. |
+| `STALLED` | The evaluator sees no useful next step it can do alone — it is stopping to ask for your help. |
+| `GOAL_ACHIEVED` | Every must-have journey now works, so the session will finish. |
+
+"Next depth" after the verdict: `lean` = a quick build-and-check round; `full` = a
+full round with extra review, audit and UX checks.
+
+### Other verdict words you'll see inside reports
+
+| Code | In plain words |
+|---|---|
+| `PASS` / `FAIL` | The check passed / found problems (the pipeline fixes and retries by itself). |
+| `PASS_WITH_NOTES` | Passed; small non-blocking remarks attached. |
+| `PASS_WITH_GAPS` | Passed overall, but the auditor found real gaps worth reading. |
+| `SKIPPED` | The check didn't run (usually: no browser or no frontend this round). |
+| `COHERENCE-PASS / WARN / FAIL` | New code kept / strained / broke the app's structure rules (one source per value, every feature reachable in the navigation). |
+| `CLOSURE-PASS / CLOSURE-FAIL` | The final completeness gate for an iteration passed / blocked it. |
+| `UI-PASS / UI-PASS-WITH-GAPS / UI-FAIL` | The UI evolved properly with the new capability / partially / not at all. |
+| `RECORDED / RECORDED_WITH_NOTES / NOT_YET` | The demo tour was captured / captured with soft notes / there is nothing to demo yet. |
+| `IN-PROGRESS` | The session hasn't ended; this iteration is a normal middle step. |
+
+### Journey status words (the pills and the matrix)
+
+`passing` / `already_passing` = ✓ working · `failing` = ✗ broken (not built or not
+working yet) · `regressed` = ⚠ worked before, broken now · `partial` = ~ partly
+working · `unknown` = ? not verified yet · `pending_infra` = the test could not run
+(browser/infrastructure problem), the feature itself may be fine.
+
+---
+
+## 3. Short codes and chain words
+
+**ID families**
+- `J-01, J-02…` — your **user journeys** from `docs/goal.md` (things a user can do,
+  e.g. J-04 "Sign in with email"). The product is done when all of them pass.
+- `UT-01…` — **browser tests**, each checking one journey through a real browser.
+- `TC-01…` — **QA test cases** from the test plan.
+- `P0 / P1 / P2` — how urgent (P0 = most urgent).
+- `Effort S / M / L` — how much work (small / one session / multiple sessions).
+- `Risk LOW / MED / HIGH` — chance the change breaks something else.
+- `CRITICAL / IMPORTANT / GAP / OBSERVATION` — audit findings, most to least serious.
+- `RETRO-1…` — numbered suggestions in a retro report.
+- `CTX-8, REL-14, SPEED-2, EVO-1, §16…` — internal improvement tickets and section
+  numbers for the framework itself (`docs/improvement-roadmap.md`). Maintainer
+  bookkeeping — safe to ignore while running your product.
+
+**Chain words**
+- **journey** — one thing a user can do, written as steps with an observable result.
+- **iteration** — one loop of plan → build → check. **baseline** — iteration 0, which
+  only verifies the starting state and builds nothing.
+- **lean / full depth** — quick round vs. full-rigor round (see above).
+- **evaluator** — the agent that judges each iteration and writes `eval.md`.
+- **gate** — a mechanical safety check that can override an agent's claim. If a gate
+  demotes a verdict, the stricter answer wins.
+- **blueprint** — the app's floor plan you approve once (navigation + data contract).
+- **pump** — the Claude Code session that actually runs the agents when you use the
+  interactive `/goal` commands. If it disappears, the engine pauses (`AWAITING_PUMP`).
+- **showcase** — the non-blocking tail of each iteration that produces the demo,
+  summary, README refresh, and HTML pages. It can fail without failing your build.
+- **anti-goal** — a thing you told the chain never to do (`docs/goal.md`).
+
+---
+
+*Single source note (for maintainers): the plain sentences for statuses and verdicts
+are defined in `scripts/automation/lib/plain-language.sh` and mirrored here and in
+`skills/plain-language.md`. If wording changes, change it in all three together.*
diff --git a/incredible_auto_dev/docs/goal-mode-interactive.md b/incredible_auto_dev/docs/goal-mode-interactive.md
index 56dee7cd..4d5d0c40 100644
--- a/incredible_auto_dev/docs/goal-mode-interactive.md
+++ b/incredible_auto_dev/docs/goal-mode-interactive.md
@@ -105,10 +105,11 @@ programmatic path with an API key** (`run-goal.sh` without `--interactive`).
   the run pauses; continue after it resets. (The headless path's
   sleep-until-reset does **not** apply in interactive mode.)
 - **Model tiering becomes live.** Each agent runs on its `.claude/agents/<name>.md`
-  model tier (Opus for strong agents, Sonnet for standard, Haiku for light), so
-  cost follows the tier. The **strong tier is Opus 4.8** — Anthropic's most capable
-  Opus-tier model. It runs on Max; Pro may not grant it. If a
-  tier's model is unavailable, set an interactive tier override (see Troubleshooting).
+  model tier, so cost follows the tier. The **strong tier** resolves via
+  `config/model-tiers.yaml` (`python3 scripts/automation/lib/agent_permissions.py
+  tier-model strong` prints the current id). Strong-tier models run on Max; Pro may
+  not grant them. If a tier's model is unavailable, set an interactive tier override
+  (see Troubleshooting).
   Do **not** set
   `CLAUDE_CODE_SUBAGENT_MODEL` — it overrides every subagent and flattens the tiers.
 - **Fidelity gaps vs headless.** The per-agent `--effort` downgrade is **not**
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index a32b5dc9..d4e3029a 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -4,6 +4,10 @@ Goal mode is an autonomous, continuous mode of the AI Multi-Agent Dev Chain. You
 
 For phase-by-phase mode (still fully supported), see the main [README](../README.md). For the architecture details, see [`.claude/architecture/goal-mode.md`](../.claude/architecture/goal-mode.md).
 
+New to the terms and status codes (STALLED, `J-01`, lean/full…)? Keep
+[`READING-REPORTS.md`](READING-REPORTS.md) open next to your first run — it explains
+every report file and every code in plain words.
+
 ## When to use goal mode vs phase mode
 
 | Use **phase mode** when … | Use **goal mode** when … |
@@ -347,4 +351,4 @@ Then:
 - [`templates/project-goal.md`](../templates/project-goal.md) — full goal template with all required sections
 - [`.claude/architecture/goal-mode.md`](../.claude/architecture/goal-mode.md) — internal architecture
 - [`docs/goal-mode-telemetry.md`](goal-mode-telemetry.md) — telemetry event schema
-- [`.claude/anti-patterns.md`](../.claude/anti-patterns.md) — common authoring pitfalls (especially #18)
+- [`.claude/anti-patterns/`](../.claude/anti-patterns/) — common authoring pitfalls (especially `18-goal-journeys-anti-goals.md`)
diff --git a/incredible_auto_dev/docs/goal.md b/incredible_auto_dev/docs/goal.md
index 5475c1ed..784fb31f 100644
--- a/incredible_auto_dev/docs/goal.md
+++ b/incredible_auto_dev/docs/goal.md
@@ -20,11 +20,41 @@ Developers and teams who want to automate their development lifecycle with AI ag
 6. Artifact-based inter-agent communication (no free-form conversation)
 7. Configurable model tiers (strong/standard/light) per agent
 
-## Non-Goals
-
-- Being a general-purpose coding assistant — this is a structured, phase-gated pipeline, not a freeform agent
-- Replacing human judgment on architecture, product direction, or critical design decisions
-- Supporting non-Claude AI providers (Gemini, GPT, etc.) — Claude-only by design
+## Must-have user journeys
+
+The framework's own acceptance journeys — operator-observable and evidence-backed. They
+also make this file pass the same validation (`run-goal.sh validate_goal_file`) the
+framework enforces on every adopter's goal.md.
+
+- **J-01: Adopter ships phase 1**
+  1. Fill `.claude/project-template.md` and author `docs/phases/phase-1.md` from `templates/phase-spec.md`.
+  2. Run `./scripts/automation/run-phase.sh phase-1`.
+  Acceptance: the run ends with CLOSURE-PASS; `runs/phase-1/status.json` reaches the
+  final step; all 6 `reports/phase-1-*` UI-visibility artifacts exist.
+- **J-02: Goal session achieves a demo goal**
+  1. Author a small adopter-style `docs/goal.md` (journeys + anti-goals).
+  2. Run `./scripts/automation/run-goal.sh --session-id demo`.
+  Acceptance: the session halts GOAL_ACHIEVED only through the deterministic gates plus
+  the two-key confirm — `telemetry.jsonl` halt event, `iter-<N>/gate-report.md`, and the
+  CONFIRM_ACHIEVED verdict line all present.
+- **J-03: Interrupted session resumes**
+  1. Ctrl-C a running goal session mid-iteration.
+  2. Relaunch `./scripts/automation/run-goal.sh --session-id <same-sid>`.
+  Acceptance: the engine resumes from checkpoint without repeating completed steps —
+  checkpoint markers present in the session dir; `engine.log` shows completed steps
+  skipped on re-entry.
+- **J-04: Offline evals protect edits**
+  1. Run `./scripts/automation/run-evals.sh` with no API access.
+  2. Seed a mirror edit (hand-edit one `.claude/agents/*.md`), run it again, then resync
+     with `python3 scripts/automation/sync-cli-assets.py --cli claude` and run it a third time.
+  Acceptance: exit 0 on the clean tree, exit 1 on the seeded drift, exit 0 again after
+  the resync.
+
+## Anti-goals
+
+- No freeform-assistant mode: every change enters through a phase spec or a goal-mode iteration spec — work with no spec behind it is rejected in review
+- No autonomous decisions on what the product IS: changes to `CLAUDE.md`, `docs/goal.md` journeys/anti-goals, model spend, or gate defaults require explicit human approval (maintenance-protocol §1) — an agent-made change there without a matching approved task is a violation
+- No third AI provider: the backends are exactly Claude Code and OpenAI Codex CLI (`docs/cli-providers.md`) — a change adding another provider integration is out of scope
 
 ## Note for Projects Using This Framework
 
diff --git a/incredible_auto_dev/docs/improvement-roadmap.archive.md b/incredible_auto_dev/docs/improvement-roadmap.archive.md
index 4365dc5f..c855db9a 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.archive.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.archive.md
@@ -713,3 +713,133 @@ legend: active file §4.
   `run-evals.sh` §2c: suite went 83 → 84 pass / 0 fail, verbose line
   `PASS: unit: tests/automation/test-doc-drift.sh`. Effort S → self-verified per
   §2.7/G8 (fresh-session rule is M/L only).
+
+### DOC-5 · "Reading the reports" guide
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** absorbed into PLAIN-1 (§19) 2026-07-26
+- **Problem:** the chain produces MD summaries, HTML reports, demo galleries, a session
+  index, gate reports — nothing tells the owner which one to open and what to look for.
+- **Current state:** partial coverage spread across README sections + `runs/SCHEMA.md`
+  (machine-oriented).
+- **Change spec:** `docs/READING-REPORTS.md`: per artifact — what it is, who it's for
+  (owner vs maintainer), when it appears, the 3 things to check (e.g. session index:
+  journey matrix trend, latest verdict, assumptions section once NEED-6 lands).
+  One screenshot-free page; link from README "Outputs" table and the session-index
+  footer if the renderer has one.
+- **DoD:** every report artifact in `runs/SCHEMA.md`'s human-facing set has an entry.
+- **Verify:** cross-check list vs `runs/SCHEMA.md`; link greps.
+- **Files:** `docs/READING-REPORTS.md` (new), README.
+- **Rollback:** docs-only.
+- **Absorption note (2026-07-26):** delivered as PLAIN-1 slice 1 — the guide gained a
+  status/verdict glossary and a code legend, and the renderer footer link became part
+  of PLAIN-1 slice 4 (renderer commit).
+
+### PLAIN-1 · Plain-English explanation layer (absorbs DOC-5)
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** DONE (2026-07-26)
+- **Verified (2026-07-26, fresh non-implementer session per G8, at 138982c):** DoD
+  checked line by line. Verify block re-run green: evals 136 pass / 0 fail
+  (`test-plain-language.sh` in the §2c list; 59 pass / 0 fail standalone),
+  `sync-cli-assets.py --check` 0 drift, renderer self-test passed (updated pins + the
+  MD-contract assertions), lib smoke prints the three-part plain block ending in the
+  `docs/READING-REPORTS.md` pointer. Call-sites: 22 `explain_goal_status`/`_verdict`
+  sites in run-goal.sh (every anchored halt — BUDGET_EXHAUSTED, STALLED ×2,
+  REGRESSION_HALT, ABORT_MALFORMED — all pauses, GOAL_ACHIEVED, the verdict line
+  `:2246`) + 5 `explain_phase` sites in run-phase.sh (Review/QA pass+fail, final
+  banner). Glossary: all 12 statuses + 5 verdicts appear in READING-REPORTS.md, which
+  is linked from README and the quickstart top. Writer wiring: iteration-summarizer /
+  demo-narrator / readme-maintainer name the skill (agent.yaml bumps 2.0.0→2.1.0,
+  1.1.0→1.2.0, 1.0.0→1.1.0), retro-analyst carries the rules inline by design (no
+  skill line), goal-status translates with the raw code in parentheses. Evaluator:
+  §6b at body.md:201, agent.yaml 1.8.0; spot-run evidenced by the kept
+  `judgment-goal-evaluator-*` sandboxes (shared temp root): both bracketing cases ran
+  WITH the §6b body (v1.8.0 confirmed inside each sandbox), GOT == EXPECTED
+  (GOAL_ACHIEVED / REGRESSION), prose follows the new rule, `**Verdict:**` markers
+  byte-exact — in fact the full 6-case goal-evaluator suite was green (the a87a59f
+  14/14 re-baseline run carried the §6b working tree). Architecture skill-count
+  claims read 16 in all three docs plus the skills-and-hooks row.
+- **Problem:** every surface the owner actually reads is written for the machine or for
+  maintainer AIs: ~20 SHOUTING status/verdict codes with no gloss at point of use
+  (STALLED vs AWAITING_PUMP vs REGRESSION_HALT vs ABORT_MALFORMED all mean "stopped"
+  with different remedies), roadmap codenames leaking into terminal output and retros
+  (REL-14, EVO-1, §16), 35–50-word sentences with env-vars inline, five unlegended
+  severity scales (P0-2 / S-M-L / LOW-MED-HIGH / CRITICAL-IMPORTANT-GAP-OBSERVATION /
+  anti-goal critical-minor). The friendly layer that exists (`## In plain words`, HTML
+  story pages, pause banners) reaches only 2 of 20 agents, and nothing tells the owner
+  which file to open.
+- **Current state:** (anchors @ 4181629) run-goal.sh: 253 ad-hoc echo sites, no style
+  policy, halt lines are bare codes (`:1458` BUDGET_EXHAUSTED, `:1465`/`:2448` STALLED,
+  `:2442` REGRESSION_HALT, `:2458` ABORT_MALFORMED); only the pause banners
+  (`:1511-1532`, `:1581-1596`) are owner-readable. The ONLY enum→sentence translation
+  in the repo is `skills/goal-interactive-dispatch.md:242-254` (pump-only).
+  goal-evaluator body: zero style guidance; `## Next-Step Recommendation` mandates
+  ID-speak. Renderer prints raw enums in hero/cover/pills
+  (`render_iteration_summary.py:1355`, `:1875`, `:1326-1334`) though a plain-word pill
+  map already exists (`:1586-1592`). Style guidance overall: 2 UI-scoped skills + one
+  core.md line — no shared standard, no glossary doc.
+- **Change spec:** six commits, each independently eval-green:
+  1. this roadmap entry (+ DOC-5 absorbed → archive).
+  2. `docs/READING-REPORTS.md` (new; DOC-5's guide + status/verdict glossary + code
+     legend), linked from README outputs area + `docs/goal-mode-quickstart.md` top.
+  3. NEW `scripts/automation/lib/plain-language.sh` (`explain_goal_status STATUS [SID]
+     [ROOT]`, `explain_goal_verdict VERDICT DEPTH`, `explain_phase KEY`, `plain_*_keys`
+     list fns; case-based; every fn `return 0`) + additive call-sites at every
+     run-goal.sh halt/pause/verdict echo and run-phase.sh Review/QA/final-banner lines
+     (existing echoes byte-untouched; `run-goal.sh:1793` is test-pinned) + NEW
+     `tests/automation/test-plain-language.sh` (map completeness; coverage of every
+     `write_session_summary "X"` / `d["status"] = "X"` status; output purity — no
+     `**Verdict:**`/`## `/parse-marker strings; pinned-literal re-asserts) wired into
+     the `run-evals.sh` §2c list.
+  4. renderer: `_PLAIN_BADGE` map + `badge-enum` suffix at hero/cover, plain pill text
+     with raw status in `title=`, session-index footer link to READING-REPORTS.md;
+     update the 4 affected self-test expect-list pins in the same commit
+     (`"J-04 · passing"` → `"J-04 · ✓ working"` etc.); the `:2402-2438` MD-contract
+     assertions must pass UNCHANGED.
+  5. NEW `skills/plain-language.md` (audience profile, hard rules, plain-word table
+     copied from the lib, 3 bad→good pairs, never-simplify list) wired via one
+     "always read" line into iteration-summarizer, demo-narrator, readme-maintainer.
+     retro-analyst gets NO skill line (light tier + its one-file evidence boundary):
+     instead its body inlines the literal rules — a code-legend line in the report
+     skeleton, "first Problem sentence is plain English", no bare codenames.
+     `commands/goal-status.md` gains "translate the
+     status, raw code in parentheses"; bump each touched agent.yaml version; fix the
+     eval-enforced "15 skills" claims → 16 (architecture README/adoption-guide/
+     system-overview) + skills-and-hooks row; resync mirrors.
+  6. goal-evaluator: ONE additive block `### 6b. Plain-language rule for prose fields`
+     (scope: Reasoning / Next-step recommendation / `## Summary` /
+     `## Next-Step Recommendation` / `## Halt Justification` ONLY; short sentences;
+     journey IDs always carry their short name; describe what the user would see; the
+     block must NOT contain a literal verdict-marker string, lint_contracts
+     `:169-199`); agent.yaml 1.7.0 → 1.8.0; resync; then the judgment spot-run below
+     BEFORE push.
+- **Spot-run gate (commit 6):** `run-judgment-evals.sh --list --judge goal-evaluator`
+  first (free); STOP if 2 × per-case estimate > ~US$5. Then exactly two bracketing
+  cases with `--keep-sandbox`: `case-01-clean-goal-achieved` and
+  `case-03-regression-broken-journey` (≈ $4.76 projected). Both must exit 0 with
+  GOT == EXPECTED; eyeball sandbox eval.md for the new style. Any class flip →
+  `git revert` commit 6 + resync, stop.
+- **DoD:** every terminal halt/pause and the per-iteration verdict line print a plain
+  what-happened / is-the-product-OK / what-to-do block + a `docs/READING-REPORTS.md`
+  pointer; every status in READING-REPORTS.md glossary; renderer hero/cover/pills show
+  plain words (enum still visible); the 4 writer agents name the skill; evaluator
+  prose rule landed with spot-run green; evals green; machine contracts byte-identical
+  (self-test (c) proves it).
+- **Verify:** `./scripts/automation/run-evals.sh` after every commit;
+  `python3 scripts/automation/sync-cli-assets.py --cli claude --check`;
+  `bash -c 'source scripts/automation/lib/plain-language.sh; explain_goal_status
+  STALLED demo /tmp'`; renderer self-test; the spot-run.
+- **Files:** `docs/improvement-roadmap.md`, `docs/READING-REPORTS.md` (new), README,
+  `docs/goal-mode-quickstart.md`, `scripts/automation/lib/plain-language.sh` (new),
+  `scripts/automation/{run-goal.sh,run-phase.sh,run-evals.sh}`,
+  `tests/automation/test-plain-language.sh` (new),
+  `scripts/automation/lib/render_iteration_summary.py`, `skills/plain-language.md`
+  (new), `agents/{iteration-summarizer,retro-analyst,demo-narrator,readme-maintainer,
+  goal-evaluator}/{body.md,agent.yaml}`, `commands/goal-status.md`,
+  `.claude/architecture/{README,adoption-guide,system-overview,skills-and-hooks}.md`,
+  regenerated mirrors.
+- **Rollback:** per-commit `git revert` (each slice is independent); commit 6 revert
+  must be followed by a resync.
+- **Stop-and-ask:** spot-run projected cost > ~US$5; any golden verdict class flip;
+  any place where a plain line cannot be ADDED without editing a test-pinned or
+  machine-parsed line.
+- **Non-goals:** diagnostic/tripwire console lines; enum/schema/path renames; length
+  budgets on specs (D6); reviewer/auditor bodies; roadmap/commit-message prose; a
+  中文 layer (possible later on top of the same single-source table).
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index 3c0d0dcf..0e583ad4 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -14,7 +14,7 @@ codebase and a feasibility review of every P0 design. Line anchors reference com
 ## 1. Purpose & audience
 
 - **Audience:** future maintainer sessions — interactive Claude Code sessions on
-  Opus 4.8 / Sonnet 5 (or whatever `config/model-tiers.yaml` says when you read this).
+  whatever models `config/model-tiers.yaml` names when you read this.
   Items are written so you do NOT need to re-derive context: each one carries its own
   problem statement, evidence anchors, change spec, definition of done, verification
   commands, and rollback.
@@ -133,6 +133,13 @@ signal that says "do this now").
    sign-off = EVO-1 promotion + G6 multi-S exception). **SPEED-8** waits for SPEED-4
    to bed in one real session; **REL-14** (absorbs CAND-BQA-PREFLIGHT) schedules
    with the REL block — both are weaker-model-ready mini-specs.
+9. **CTX-1…14** — context engineering (§18, promoted 2026-07-25 as a user-approved
+   package): S items CTX-1/2/4/5/6/8/13 first, then CTX-3 and CTX-12; CTX-7 requires
+   its judgment spot-run; CTX-9/10/11/14 as capacity allows. CTX-15 staged as
+   CAND-RICHREF in §16.
+10. **PLAIN-1** — plain-language output (§19, promoted 2026-07-26 by direct user
+    request; absorbs DOC-5). Shipped 2026-07-26 in one bundled session; judgment
+    spot-run green; certified DONE per G8 same day.
 
 ---
 
@@ -2850,21 +2857,7 @@ territory).
 - **Files:** `docs/FIRST-RUN.md` (new), README link.
 - **Rollback:** docs-only.
 
-### DOC-5 · "Reading the reports" guide
-- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** TODO
-- **Problem:** the chain produces MD summaries, HTML reports, demo galleries, a session
-  index, gate reports — nothing tells the owner which one to open and what to look for.
-- **Current state:** partial coverage spread across README sections + `runs/SCHEMA.md`
-  (machine-oriented).
-- **Change spec:** `docs/READING-REPORTS.md`: per artifact — what it is, who it's for
-  (owner vs maintainer), when it appears, the 3 things to check (e.g. session index:
-  journey matrix trend, latest verdict, assumptions section once NEED-6 lands).
-  One screenshot-free page; link from README "Outputs" table and the session-index
-  footer if the renderer has one.
-- **DoD:** every report artifact in `runs/SCHEMA.md`'s human-facing set has an entry.
-- **Verify:** cross-check list vs `runs/SCHEMA.md`; link greps.
-- **Files:** `docs/READING-REPORTS.md` (new), README.
-- **Rollback:** docs-only.
+### DOC-5 — absorbed into PLAIN-1 (§19) 2026-07-26, archived
 
 ### DOC-6 · Architecture docs refresh
 - **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** TODO
@@ -3199,6 +3192,73 @@ but appreciated.
   hand-worked around it (fixture relocation; path-prefix splitting by convention) —
   cheap to close structurally, and the scan stays CRITICAL-capable on product paths.
 
+### CAND-JUDGE-REBASE · Judge goldens never re-validated on the Opus-5 cutover (staged — evidence attached)
+- *(Staged 2026-07-25 by the CTX package session after its G9-approved judgment spot-run;
+  promotion human, EVO-1.)*
+- **Proposed:** P1 · Effort S (1 diagnostic dispatch + triage) or M (full re-baseline) ·
+  Risk LOW (spend-gated).
+- **Evidence:** `398bff9` moved the strong tier to `claude-opus-5` but its verification
+  was `run-judgment-evals.sh --list` — an enumeration, not a dispatch; the 14 golden
+  cases have NEVER been dispatched on Opus 5. The 2026-07-25 spot-run: goal-evaluator
+  case-01 PASS (GOAL_ACHIEVED, 240 s); auditor case-01 expected PASS, got
+  PASS_WITH_GAPS (247 s). The auditor's own verdict text shows it independently
+  re-verified the product end-to-end ("confirmed the served HTML … across five states
+  plus an HTML-injection attempt"), agreed the product is correct, and downgraded SOLELY
+  on fixture-evidence fidelity (the planted QA screenshots are "stylized, annotated
+  renderings rather than faithful captures") — precisely the over-verification the
+  cutover commit's follow-up note predicted ("Opus 5 self-verifies without being told;
+  the explicit 'verify your work' scaffolding in the judge bodies may now cause
+  over-verification"). CTX-8's removed dispatch line has no plausible causal path to
+  screenshot skepticism, and the goal-evaluator — same class of prompt edit —
+  reproduced its golden exactly. Kept sandbox:
+  `~/.cache/iad/shared/judgment-auditor-case-01-clean-pass-XhPIFr` (dispatch.log +
+  verdict artifact).
+- **Sketch:** (a) counterfactual first (~$2.38): re-run auditor case-01 with the
+  pre-CTX-8 prompt line restored — same PASS_WITH_GAPS formally exonerates CTX-8;
+  (b) full 14-case run on Opus 5 (~$29.52 est) to re-baseline the goldens;
+  (c) per-failure triage: stale fixture evidence (upgrade the planted screenshots to
+  faithful captures) vs judge-body "verify your work" scaffolding trimming per the
+  cutover note — any judge-body edit then requires the full-run validation (G9/D4).
+- **Why staged:** spend-class (G9) and judge-body scope — human promotion required.
+- **RESOLVED (user-promoted 2026-07-25, executed 2026-07-25/26):**
+  - Counterfactual (auditor case-01, pre-CTX-8 prompt restored): **FAIL** (316 s) —
+    WORSE than the current prompt's PASS_WITH_GAPS ⇒ **CTX-8 formally exonerated**.
+  - Full 14-case re-baseline on claude-opus-5: **13/14 PASS** — goal-evaluator 6/6,
+    reviewer 4/4, auditor 3/4. Sole failure: auditor case-01-clean-pass (expected PASS,
+    got PASS_WITH_GAPS, 270 s — same evidence-fidelity downgrade as the spot-run).
+    Judges are stable on Opus 5; NO judge-body changes warranted.
+  - Fixture fix: the case's two planted screenshots were regenerated as faithful
+    Playwright captures of the fixture app's real states (UT-02 fresh-db
+    `0 open · 0 done`; UT-01 seeded `1 open · 1 done` with Milk×2 open + Eggs×1 done) —
+    all three of the auditor's cited objections addressed (missing "Open only" control,
+    text the app never emits, styling the CSS cannot produce). Capture script:
+    session scratchpad `capture_fixture_screens.py` (boots the fixture app, asserts the
+    summary text, screenshots via headless chromium).
+  - Confirmation dispatch (2026-07-26, user-approved): auditor case-01 on the fixed
+    fixture → **PASS** (228 s). The golden suite stands **14/14 validated on
+    claude-opus-5**. This candidate is CLOSED — the only surviving follow-up idea from
+    the cutover note (trimming judge-body "verify your work" scaffolding) is NOT
+    warranted on this evidence: the judges hold their goldens; only the fixture was
+    stale. · Rich-reference fields: spec mockups + journey-tagged failing tests (staged — do not start)
+- *(Staged 2026-07-25 by the context-engineering planning session — §18's source plan;
+  blog rule 6 "simple specs → rich references"; promotion human, EVO-1.)*
+- **Proposed:** P2 · Effort M · Risk MED.
+- **Sketch (two independent halves):** (a) an optional
+  `Reference: <path-to-html-mockup-or-screenshot>` line in the phase-spec header and in
+  the decomposer's Goal Mode Metadata block — always its OWN line (the REL-14/CAND
+  precedent: never annotate machine-parsed lines like `Target journeys:`);
+  `ui-test-designer` + `browser-qa-agent` bodies gain "when a Reference is present,
+  compare the rendered UI against it and cite divergences". Old specs parse unchanged
+  (spec-optional = naturally inert). (b) the developer — NOT the decomposer, whose Rules
+  (`agents/goal-decomposer/body.md:234`) forbid writing code — materializes
+  journey-tagged TCs as failing tests first, named `tests/journeys/j<NN>_*`, making
+  journeys executable acceptance (a TDD extension, not a new mechanism).
+- **Why staged:** both halves touch dispatch-adjacent agent bodies and the spec grammar;
+  promotion needs a fixture spec proving the Reference line flows through
+  `goal_gate.py goal-slice` unchanged (G3) and a decision on where mockups live.
+- **Verify idea:** run-evals + one fixture goal-iteration dry parse with a Reference
+  line present and absent.
+
 ---
 
 ## 17. Absorbed-from-README ledger (traceability)
@@ -3228,3 +3288,492 @@ Also absorbed from `.claude/letter-to-future-sessions.md` "known limitations we
 not to fix": pump PID-liveness → **REL-3**; cross-session lock → **REL-4**; scan_diff
 is regex-grade → **SEC-1**; stall-detector blind spot → noted, no item (the evaluator's
 STALLED judgment covers it; revisit only if it bites in practice → §16).
+
+---
+
+## 18. P1 — Context engineering (CTX-*, promoted 2026-07-25)
+
+Source: Anthropic's blog "The new rules of context engineering for Claude 5 generation
+models" (claude.com/blog, 2026-07-24) — six rule inversions: rules→judgment (delete
+guardrail piles and conflicting directives), examples→interface design,
+upfront→progressive disclosure, repetition→concision, manual memory→auto-memory,
+simple specs→rich references. Mapped against this repo by the 2026-07-25 Fable-5
+planning session; user approval of that plan = EVO-1 promotion of this section
+(SPEED-4…7 approved-package precedent for the G6 multi-item exception).
+
+Two constraints every CTX item respects: (1) **tier-aware relaxation** — standard
+(sonnet-5) and strong (opus-5) are 5-gen models where judgment-style applies; the light
+tier (haiku-4-5: qa, release-manager, retro-analyst) is NOT — literal checklists stay
+literal for anything light-tier agents execute. (2) **Judges are protected** —
+goal-evaluator, reviewer, auditor get NO semantic body edits in this series; changes to
+the context they receive are validated by a G9-approved judgment spot-run (1 golden
+case × 3 judges, abort if the printed estimate exceeds ~US$5). Frozen surfaces no CTX
+item may touch: verdict formats (`.claude/workflow.md` §Verdict Formats,
+`lib/verdicts.py`, `**Verdict:**` templates), the `Agent instructions:
+.claude/agents/<name>.md` dispatch line (pump parses it,
+`skills/goal-interactive-dispatch.md:130-139`), the `## Token and Questioning Policy`
+heading in core.md, and the security hooks' deny logic.
+
+### CTX-1 · Revive the PostToolUse hooks on Claude (stdin protocol, SEC-7 pattern)
+- **Priority:** P0 · **Effort:** S · **Risk:** MED · **Status:** DONE 2026-07-25
+- **Problem:** both PostToolUse hooks no-op on every fire on the Claude backend: the
+  rendered settings pass `"$CLAUDE_TOOL_INPUT_FILE_PATH"` — an env var that never
+  existed — so the hooks see an empty path and exit. The live artifact-schema feedback
+  channel (schema warnings at the point of tool use — blog rule 2) is dead; it fires
+  only inside run-evals, never in a real session.
+- **Current state:** fake arg emitted by `_hooks_block_for_claude`
+  (`adapters/claude/sync.py:204-209`, known FIXME; rendered into
+  `.claude/settings.json` PostToolUse entries). Hooks read `$1` only:
+  `hooks/post-edit-lint.sh:3`, `hooks/post-write-artifact-quality.sh:11-14`. The
+  PreToolUse pair already has the fix pattern (SEC-7): argv `$1` preserved for
+  Codex/tests, stdin JSON `.tool_input.command` with jq-primary/python3-fallback
+  (`hooks/guard-dangerous-commands.sh:17-31`). Eval coverage for the PostToolUse pair
+  is argv-only (`run-evals.sh` §5 ~:405-443).
+- **Change spec:** (1) in `hooks/post-edit-lint.sh` and
+  `hooks/post-write-artifact-quality.sh` add the guard's dual-mode input block: use
+  `$1` when non-empty (Codex/argv contract unchanged), else read stdin JSON and extract
+  `.tool_input.file_path // .tool_input.path // empty` (jq primary, python3 fallback);
+  empty result → exit 0. Hooks stay advisory — warnings to stderr, always exit 0,
+  NO decision JSON. (2) in `adapters/claude/sync.py` `_hooks_block_for_claude` delete
+  the fake-arg branch so the rendered command is
+  `bash "$CLAUDE_PROJECT_DIR/.claude/hooks/<name>" 2>/dev/null || true`; remove the
+  FIXME. (3) resync. (4) add 4 stdin smokes to `run-evals.sh` §5: well-formed review
+  via stdin → silent; malformed review via stdin → schema warning on stderr;
+  syntax-error `.py` via stdin → lint warning; garbage/empty stdin → silent exit 0.
+  Keep every existing argv smoke.
+- **DoD:** printf-pipe smoke surfaces the schema warning; argv behavior byte-identical;
+  evals green including the new checks.
+- **Verify:** `printf '{"tool_input":{"file_path":"<bad-review-fixture>"}}' | bash
+  .claude/hooks/post-write-artifact-quality.sh` shows the warning; then
+  `./scripts/automation/run-evals.sh && python3 scripts/automation/sync-cli-assets.py
+  --cli claude --check`
+- **Files:** `hooks/post-edit-lint.sh`, `hooks/post-write-artifact-quality.sh`,
+  `adapters/claude/sync.py`, `scripts/automation/run-evals.sh`, regenerated
+  `.claude/hooks/*` + `.claude/settings.json` (+ codex mirrors via default sync).
+- **Rollback:** revert hooks + adapter, resync — settings regenerate to the prior
+  (inert) form.
+- **Stop-and-ask:** if the live PostToolUse stdin payload turns out not to carry
+  `.tool_input.file_path` for Write/Edit; if any smoke would require changing the
+  PreToolUse guards' deny-JSON protocol.
+
+### CTX-2 · Routing-table truth pass (CLAUDE.md "who reads what")
+- **Priority:** P1 · **Effort:** S · **Risk:** MED · **Status:** DONE 2026-07-25
+- **Problem:** the constitution's routing table over-claims readership, so agents hold
+  contradictory directives (blog rule 1): "all agents read X" vs their own bodies.
+- **Current state:** `CLAUDE.md` INSTRUCTION FILES table: workflow.md row says "All
+  agents" (real inbound: `agents/goal-decomposer/body.md:21`,
+  `agents/reviewer/body.md:73`, `ui-audit-phase.sh`); judgment-rubrics row says
+  "evaluator, auditor, decomposer, reviewer" (real: `agents/auditor/body.md:177`
+  direct; goal-evaluator transitively via `skills/goal-evaluation-methodology.md`);
+  architecture/ row says "Reference (all agents)" — directly contradicted by
+  `agents/orchestrator/body.md:16` "Do NOT read `.claude/architecture/*.md`";
+  delegation-templates row says "Anyone dispatching agents" (real inbound:
+  `model-orchestration.md:63` only). `.claude/workflow.md:70` artifact row claims
+  architecture docs are read by "All agents (reference)".
+- **Change spec:** edit the four CLAUDE.md reader cells to verified truth: workflow.md →
+  "goal-decomposer, reviewer; on-demand pipeline reference for others";
+  judgment-rubrics → "auditor (direct); goal-evaluator (via its methodology skill);
+  anyone making verdict-class calls"; architecture/ → "framework maintainers only —
+  pipeline agents must NOT read these (orchestrator rule)"; delegation-templates →
+  "interactive maintainer sessions dispatching ad-hoc subagents". Same commit: fix
+  `.claude/workflow.md:70` readers cell to "framework maintainers (reference)".
+  `docs/cli-providers.md`: only if it claims AGENTS.md is committed, correct it
+  (AGENTS.md is gitignored — `.gitignore:3-4` — and rendered at sync). Truth-only
+  edits; no format churn.
+- **DoD:** every "Who reads it" cell backed by a grep hit in a body/skill/script or
+  explicitly marked on-demand; no cell contradicts an agent body.
+- **Verify:** `./scripts/automation/run-evals.sh` (includes doc-drift checks).
+- **Files:** `CLAUDE.md`, `.claude/workflow.md`, possibly `docs/cli-providers.md`.
+- **Rollback:** revert.
+- **Stop-and-ask:** CLAUDE.md is ask-first class — the 2026-07-25 plan approval is that
+  ask; STOP if the edit grows beyond reader cells. Land between sessions (cache prefix).
+
+### CTX-3 · Single-source the three duplicated tables + stale-value sweep
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** IN-PROGRESS — implemented 2026-07-25, awaiting fresh-session verify (G8). Note: the DoD's "Opus 4.8 → 0" grep is satisfied for live docs; the only remaining hits are this item's own defect quotes in this file.
+- **Problem:** the model-tier table is restated 4×, the pipeline stage table and the
+  artifact map 2× each — and the copies have already diverged (decomposer tier, audit
+  retry count), so different agents read contradictory facts (blog rules 1+4).
+- **Current state:** tier table: `config/model-tiers.yaml` (authoritative) +
+  `.claude/model-orchestration.md:22-26` (correct, reflects TOKEN-2
+  decomposer=standard) + `.claude/workflow.md:238-246` (:242 wrongly lists
+  decomposition under strong) + `.claude/architecture/agents.md:7-11` (:9 same
+  staleness; `agents/goal-decomposer/agent.yaml` says `model_tier: standard`). Stage
+  table: `.claude/workflow.md:15-29` (has the TOKEN-3 skip note) duplicated by
+  `.claude/architecture/pipeline.md` (:57 "max 2 attempts" contradicts
+  `run-phase.sh:102` `MAX_AUDIT_RETRIES=3`). Artifact map: `.claude/workflow.md:46-71`
+  duplicated by `.claude/architecture/artifacts.md`. Stale model name:
+  `docs/goal-mode-interactive.md:109-110` "strong tier is Opus 4.8".
+- **Change spec:** direction — runtime copies live in `.claude/workflow.md` +
+  `.claude/model-orchestration.md`; `architecture/` docs point, never restate.
+  (1) workflow.md:238-246 tier table → 3-line pointer (resolution: `agent.yaml
+  model_tier` → `config/model-tiers.yaml`; prose table only in model-orchestration §1,
+  maintained per maintenance-protocol §6). (2) architecture/agents.md:7-11 → same
+  pointer; spot-fix any stale per-agent tier in the catalog below (decomposer =
+  standard). (3) architecture/pipeline.md → drop duplicated stage/retry specifics,
+  point to workflow.md §Pipeline + §Retry Policy; fix or delete the ":57 max 2" text.
+  (4) architecture/artifacts.md → drop rows verbatim-duplicating workflow.md:48-71;
+  keep goal-mode-only rows + a pointer. (5) goal-mode-interactive.md:109-110 →
+  tier-neutral wording ("the strong tier resolves via config/model-tiers.yaml").
+  NEVER touch workflow.md §Verdict Formats. Pre-check
+  `grep -rn "workflow.md" scripts/` for any cell-text dependency first.
+- **DoD:** exactly one prose tier table remains (model-orchestration.md); no
+  stage/artifact/tier fact stated in two files; decomposer shown standard everywhere or
+  nowhere; `grep -rn "Opus 4.8" docs/ .claude/` → 0.
+- **Verify:** the grep above + `./scripts/automation/run-evals.sh`.
+- **Files:** `.claude/workflow.md`, `.claude/architecture/{agents,pipeline,artifacts}.md`,
+  `docs/goal-mode-interactive.md` (all hand-authored — direct edits; default sync
+  refreshes the AGENTS.md embed).
+- **Rollback:** revert files.
+- **Stop-and-ask:** any script found grepping workflow.md stage-table cell text.
+
+### CTX-4 · Count-claims fix + doc-drift eval extended to `.claude/architecture/`
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** DONE 2026-07-25
+- **Problem:** architecture docs assert wrong inventory numbers and nothing gates them,
+  so they re-rot after every agent/skill addition.
+- **Current state:** real counts: 20 `agents/*/` dirs, 15 `skills/*.md`, 5 `hooks/*.sh`,
+  7 `commands/*.md`. Wrong: `.claude/architecture/README.md:12` "All 19 agents", `:14`
+  "13 skills and 5 hooks"; `configuration.md:28` "19 agents … (12 phase-mode + 2 goal
+  -mode)"; `skills-and-hooks.md:3` "Skills (9 total)"; `system-overview.md:~37` same
+  "9 total" + the :35 grouping paragraph (real grouping per agents.md:3: 12 phase +
+  4 goal + 4 showcase). `tests/automation/test-doc-drift.sh` scans README.md +
+  CLAUDE.md only.
+- **Change spec:** (1) fix every count to match the tree; prefer deleting hard numbers
+  where they add nothing (rule 4), keep them where the doc is an inventory. (2) extend
+  `test-doc-drift.sh` to scan `.claude/architecture/*.md` "N agents/skills/commands/
+  hooks" claims against neutral-source counts, with a broken-fixture assertion first
+  (file's existing pattern); it is already wired into run-evals §2c.
+- **DoD:** drift test red on a seeded wrong count, green on the fixed tree.
+- **Verify:** `bash tests/automation/test-doc-drift.sh && ./scripts/automation/run-evals.sh`
+- **Files:** `.claude/architecture/{README,configuration,skills-and-hooks,system-overview}.md`,
+  `tests/automation/test-doc-drift.sh`.
+- **Rollback:** revert.
+
+### CTX-5 · Stop requiring reads of nonexistent `docs/architecture/`
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** DONE 2026-07-25
+- **Problem:** three "always read first" lists and two workflow rows require
+  `docs/architecture/*.md`, but the directory does not exist until `update-docs.sh`
+  creates it after the first finalized phase — every early dispatch burns a failed
+  lookup plus "am I missing context?" doubt.
+- **Current state:** required by `agents/developer/body.md:12`,
+  `agents/orchestrator/body.md:12`, `.claude/workflow.md:17` and `:69`. Producer:
+  `scripts/automation/update-docs.sh` (project mode, header :5-8).
+- **Change spec:** append to all four sites: "(if present; created by update-docs.sh
+  from the first finalized phase — absence is normal early on, skip silently)".
+  Version-bump `agents/{developer,orchestrator}/agent.yaml`, resync.
+- **DoD:** no instruction file lists docs/architecture/ as unconditional; mirrors
+  regenerated.
+- **Verify:** `python3 scripts/automation/sync-cli-assets.py --cli claude --check &&
+  ./scripts/automation/run-evals.sh`
+- **Files:** `agents/developer/body.md`, `agents/orchestrator/body.md`,
+  `.claude/workflow.md`, two `agent.yaml` bumps, regenerated mirrors.
+- **Rollback:** revert + resync.
+
+### CTX-6 · Make the repo's own `docs/goal.md` pass its own validator (dogfooding)
+- **Priority:** P1 · **Effort:** S · **Risk:** MED · **Status:** DONE 2026-07-25
+- **Problem:** the framework hard-fails adopters whose goal.md lacks `## Must-have user
+  journeys` + `## Anti-goals` (anti-pattern #18), yet this repo's own `docs/goal.md`
+  has neither — `/goal` on this repo dies at validation, and the in-repo exemplar
+  teaches the wrong shape (blog rule 6: the spec artifact IS the reference).
+- **Current state:** `docs/goal.md` (1,705 B) has `## Non-Goals`, no journeys section.
+  Validator: `validate_goal_file`, `run-goal.sh:658-699` (error strings :667/:673,
+  journey-entry check ending :695). `render_iteration_summary.py:110-113` reads
+  `## Vision` + `## Must-have user journeys` when present.
+- **Change spec:** keep Vision/Target Users/Key Capabilities and the adopter note;
+  rename `## Non-Goals` → `## Anti-goals` (entries already are veto-class); add
+  `## Must-have user journeys` with the four journeys approved in the 2026-07-25 plan,
+  in the exact `- **J-NN: <name>**` format, each with a verify: line naming observable
+  evidence: J-01 adopter ships phase-1 to CLOSURE-PASS with all 6 UI artifacts
+  (evidence: `runs/phase-1/status.json` + `reports/phase-1-*`); J-02 a goal session on
+  a small goal reaches GOAL_ACHIEVED only through deterministic gates + two-key confirm
+  (evidence: telemetry halt event + `gate-report.md` + confirm verdict); J-03 an
+  interrupted session resumes from checkpoint without repeating completed steps
+  (evidence: checkpoint markers + engine log skips); J-04 `run-evals.sh` runs offline
+  <30 s, red on seeded mirror drift, green after resync (evidence: exit codes both
+  states).
+- **DoD:** the three validator greps pass; goal-lint deterministic pass clean.
+- **Verify:** `grep -q '^## Must-have user journeys' docs/goal.md && grep -q
+  '^## Anti-goals' docs/goal.md && grep -qE '^- \*\*J-[0-9]+:' docs/goal.md &&
+  ./scripts/automation/run-evals.sh`
+- **Files:** `docs/goal.md`.
+- **Rollback:** revert file.
+- **Stop-and-ask:** goal.md journeys/anti-goals are ask-first class — the 2026-07-25
+  plan approval covered these four drafts; STOP if changing them materially.
+
+### CTX-7 · core.md restructure: intent + gotchas + tier-aware checklists (~10.8 KB → ≤6 KB)
+- **Priority:** P1 · **Effort:** M · **Risk:** HIGH · **Status:** TODO
+- **Problem:** ~17 dispatch sites and all agent bodies route to `.claude/core.md`
+  (10,775 B ≈ 2.7 K tokens per dispatch), and roughly a third of it duplicates content
+  owned elsewhere. Anthropic removed >80% of Claude Code's system prompt for 5-gen
+  models with no eval loss — this is the repo's equivalent move (rules 1+3+4).
+- **Current state (measured section map):** behavioral principles :1-48 (2,153 B);
+  code-quality checklist :50-63 (729 B); env-errors gotcha :66-73 (395 B); visual
+  checklist :76-90 (1,038 B); testing :93-108 (773 B); external-integration :111-121
+  (655 B); security :124-134 (531 B); `## Token and Questioning Policy` :137-163
+  (1,224 B — HEADING IS LOAD-BEARING, named by ~20 dispatch sites + agent bodies);
+  Definition of Done :166-189 (1,406 B — duplicates workflow.md verdict gates +
+  judgment-rubrics §2); Handoff Requirements :192-203 (521 B — duplicates
+  `agents/developer/body.md` handoff format); UI Visibility Rules :206-220 (1,304 B —
+  overlaps workflow.md §UI Evolution Policy + UI-chain bodies/skills). No script greps
+  any core.md section name except the policy heading.
+- **Change spec:** rewrite `.claude/core.md` (hand-authored, direct edit):
+  (1) behavioral principles → ~6 intent lines ("write code that reads like the
+  surrounding code; build only what the spec names; when uncertain, state the
+  assumption in the plan artifact and proceed unless it's irreversible…").
+  (2) KEEP verbatim in checklist form — light-tier agents execute these literally:
+  Code Quality, Visual Quality, Testing Requirements, External Integration Testing,
+  Security Baseline, env-errors gotcha. (3) KEEP the `## Token and Questioning Policy`
+  heading EXACTLY; trim its body to ~900 B. (4) DELETE Definition of Done (→ 2-line
+  pointer to workflow.md §Verdict Formats + judgment-rubrics §2) and Handoff
+  Requirements (developer body owns it); compress UI Visibility Rules to ~4 intent
+  lines + pointer to workflow.md §UI Evolution Policy. (5) keep anti-pattern cites
+  (#21, #15/#16) — pointing at the CTX-12 tree paths if that landed first. Target
+  ≤6 KB. Default sync afterwards (AGENTS.md embeds core.md).
+- **DoD:** `grep -c '^## Token and Questioning Policy' .claude/core.md` = 1;
+  `wc -c` ≤ 6000; every deleted fact has a named live single source (commit message
+  lists them); evals green; judgment spot-run shows no verdict-class flip.
+- **Verify:** the two greps + `./scripts/automation/run-evals.sh` + the G9-approved
+  spot-run (1 case × 3 judges); G8: pre-register predicted ~−1.2 K tokens/dispatch in
+  `benchmarks/experiments.md` before a real-session/benchmark observation.
+- **Files:** `.claude/core.md` (+ AGENTS.md regenerates via sync).
+- **Rollback:** revert core.md, resync.
+- **Stop-and-ask:** any script grepping core.md section names beyond the policy
+  heading; any verdict-class flip in the spot-run; land between sessions (cache).
+
+### CTX-8 · Dispatch-prompt concision + pump no-reread note
+- **Priority:** P1 · **Effort:** S · **Risk:** MED · **Status:** DONE 2026-07-25 — refinement found during implementation: the pump note is CONDITIONAL on the `Agent instructions: .claude/agents/` pointer being present in the prompt, so non-agent dispatches (two-key confirms, ad-hoc) and the self-test's byte-exact round-trips stay untouched. G9 spot-run (2 of 3 judges, $4.76 est ≤ the $5 guard; reviewer covered by the offline verbatim-parity eval instead): goal-evaluator case-01 PASS; auditor case-01 flipped PASS→PASS_WITH_GAPS. User-promoted follow-up (2026-07-25/26): counterfactual with the old prompt scored WORSE (FAIL) and the full 14-case Opus-5 re-baseline passed 13/14 with the same single fixture-evidence failure — CTX-8 exonerated, fixture screenshots regenerated as faithful captures (see CAND-JUDGE-REBASE, §16).
+- **Problem:** every dispatch prompt repeats "Apply the TOKEN AND QUESTIONING POLICY
+  from .claude/core.md strictly." although all 18 agent bodies already carry that exact
+  directive (rule 4). Separately, on the interactive backend the subagent's system
+  prompt IS `.claude/agents/<name>.md`, yet the prompt still says "read this first" —
+  pump-path agents re-Read their own 8-20 KB definition every dispatch.
+- **Current state:** 17 engine sites: `dev-phase.sh:101`, `review-phase.sh:63`,
+  `qa-phase.sh:147`, `generate-test-plan.sh:53`, `phase-audit.sh:80`,
+  `run-phase.sh:168`, `render-summary.sh:91`, `finalize-phase.sh:161`,
+  `goal-iter-lean.sh:840`, `run-goal.sh:300,365,433,476,1785,2092,2387`,
+  `lib/common.sh:552`; plus 3 verbatim-parity copies in
+  `run-judgment-evals.sh:293,375,449`. The `Agent instructions:` line is load-bearing
+  (pump identity derivation) — untouchable. Backend-conditional prompt-note precedent:
+  the TMPDIR bridge in `lib/interactive-dispatch.sh:183-185`.
+- **Change spec:** (1) delete the policy line at all 17 engine sites AND the 3
+  judgment-builder sites in the SAME commit (verbatim parity). (2) in
+  `_interactive_invoke` (`lib/interactive-dispatch.sh`, directly after the TMPDIR
+  bridge) append to the prompt: "Note: your agent definition (.claude/agents/… named
+  above) is already loaded as your system prompt — do not Read it again; treat its
+  'read this first' pointer as satisfied." (3) no other prompt-template changes.
... [diff_bound] incredible_auto_dev/docs/improvement-roadmap.md: 217 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/feedback/README.md b/incredible_auto_dev/feedback/README.md
index b5269b09..3b1dc6ea 100644
--- a/incredible_auto_dev/feedback/README.md
+++ b/incredible_auto_dev/feedback/README.md
@@ -12,7 +12,7 @@ That loop is **not implemented yet**. The current goal-mode pipeline only writes
 ## What is deferred (Part B, separate plan)
 
 - An opt-in `--telemetry github` flag on `run-goal.sh` that posts a sanitized digest of the JSONL as a GitHub issue or `feedback/incoming/` PR against this repo.
-- A `framework-improvement-proposer` agent that periodically reads accumulated `feedback/incoming/` and proposes targeted changes to `.claude/agents/*.md`, `.claude/anti-patterns.md`, default halt config, etc.
+- A `framework-improvement-proposer` agent that periodically reads accumulated `feedback/incoming/` and proposes targeted changes to `.claude/agents/*.md`, `.claude/anti-patterns/`, default halt config, etc.
 - PR-only application: the proposer's output is always a PR against `main`, never a direct commit. Existing reviewer/auditor agents review it. A human merges. There is no auto-merge of framework changes.
 
 These were intentionally deferred because:
diff --git a/incredible_auto_dev/hooks/post-edit-lint.sh b/incredible_auto_dev/hooks/post-edit-lint.sh
index 2081eb86..90f3b6d2 100644
--- a/incredible_auto_dev/hooks/post-edit-lint.sh
+++ b/incredible_auto_dev/hooks/post-edit-lint.sh
@@ -1,6 +1,23 @@
 #!/usr/bin/env bash
 # Post-edit hook: run lightweight syntax validation on edited source files
-FILE="$1"
+#
+# Two input modes (SEC-7 pattern, mirrors guard-dangerous-commands.sh):
+#   argv mode  — file path as $1 (run-evals, test harness, Codex).
+#   stdin mode — the Claude Code PostToolUse protocol: JSON on stdin
+#     (.tool_input.file_path; $CLAUDE_TOOL_INPUT_FILE_PATH never existed).
+# Advisory only: warnings to stderr, always exit 0.
+FILE="${1:-}"
+if [[ -z "$FILE" && ! -t 0 ]]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [[ -n "$_payload" ]]; then
+    if command -v jq >/dev/null 2>&1; then
+      FILE=$(printf '%s' "$_payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null) || FILE=""
+    else
+      FILE=$(printf '%s' "$_payload" | python3 -c 'import json,sys; ti=json.load(sys.stdin).get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")' 2>/dev/null) || FILE=""
+    fi
+  fi
+fi
+[[ -z "$FILE" ]] && exit 0
 
 if [[ "$FILE" == *.py ]]; then
   if command -v python3 &>/dev/null; then
diff --git a/incredible_auto_dev/hooks/post-write-artifact-quality.sh b/incredible_auto_dev/hooks/post-write-artifact-quality.sh
index 57aaf7ae..c2926343 100755
--- a/incredible_auto_dev/hooks/post-write-artifact-quality.sh
+++ b/incredible_auto_dev/hooks/post-write-artifact-quality.sh
@@ -10,6 +10,20 @@ set -e
 
 FILE_PATH="${1:-}"
 
+# Claude Code PostToolUse passes JSON on stdin (.tool_input.file_path);
+# $CLAUDE_TOOL_INPUT_FILE_PATH never existed. argv ($1) remains the
+# test-harness / Codex path (SEC-7 pattern, mirrors guard-dangerous-commands.sh).
+if [[ -z "$FILE_PATH" && ! -t 0 ]]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [[ -n "$_payload" ]]; then
+    if command -v jq >/dev/null 2>&1; then
+      FILE_PATH=$(printf '%s' "$_payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null) || FILE_PATH=""
+    else
+      FILE_PATH=$(printf '%s' "$_payload" | python3 -c 'import json,sys; ti=json.load(sys.stdin).get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")' 2>/dev/null) || FILE_PATH=""
+    fi
+  fi
+fi
+
 if [[ -z "$FILE_PATH" ]]; then exit 0; fi
 if [[ ! -f "$FILE_PATH" ]]; then exit 0; fi
 
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 28b705ee..16f4b1a4 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -367,7 +367,7 @@ fi
 # the step but closure-check would flag the stub as missing real content. By
 # exiting without stubs, the working tree is unchanged so resume re-runs the
 # step and run-phase.sh's signal-aware retry guard aborts the run cleanly.
-# See .claude/anti-patterns.md #20.
+# See .claude/anti-patterns/20-next-build-against-dev.md.
 if [[ $_bqa_rc -eq 130 || $_bqa_rc -eq 137 || $_bqa_rc -eq 143 ]]; then
   echo "[browser-qa] Killed by signal (exit $_bqa_rc) — leaving artifacts untouched so resume can re-run this step." >&2
   exit "$_bqa_rc"
diff --git a/incredible_auto_dev/scripts/automation/dev-phase.sh b/incredible_auto_dev/scripts/automation/dev-phase.sh
index cb392d17..9756b1a2 100755
--- a/incredible_auto_dev/scripts/automation/dev-phase.sh
+++ b/incredible_auto_dev/scripts/automation/dev-phase.sh
@@ -98,8 +98,6 @@ Execution plan: $PLAN_FILE  <-- read this to understand what to build
 $FIX_CONTEXT
 Mode: $MODE_LABEL
 
-Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
-
 When complete:
 - Write dev handoff to: docs/handoffs/${PHASE}-dev.md
 - If frontend work was done, also write: docs/handoffs/${PHASE}-frontend.md
diff --git a/incredible_auto_dev/scripts/automation/finalize-phase.sh b/incredible_auto_dev/scripts/automation/finalize-phase.sh
index 1e65f6b9..ecbcabe3 100755
--- a/incredible_auto_dev/scripts/automation/finalize-phase.sh
+++ b/incredible_auto_dev/scripts/automation/finalize-phase.sh
@@ -158,8 +158,6 @@ Agent instructions: .claude/agents/release-manager.md  <-- read this first
 
 GH_AUTH_AVAILABLE: $GH_AUTH_AVAILABLE
 
-Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
-
 Perform the release flow:
 1. Create branch: phase/$PHASE  (if not already on it)
 2. Stage and commit all phase changes (read dev handoff for file list)
diff --git a/incredible_auto_dev/scripts/automation/generate-test-plan.sh b/incredible_auto_dev/scripts/automation/generate-test-plan.sh
index 827bf1f3..5226efcf 100755
--- a/incredible_auto_dev/scripts/automation/generate-test-plan.sh
+++ b/incredible_auto_dev/scripts/automation/generate-test-plan.sh
@@ -50,7 +50,6 @@ Agent instructions: .claude/agents/qa.md  <-- read this first, follow MODE 1 ins
 
 Frontend Present for this phase: $FRONTEND_PRESENT
 
-Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
 Do not ask questions — derive all test cases from the phase spec.
 
 Write the functional test plan to: $TEST_PLAN
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 5d1a4bcb..4a5351a6 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -837,8 +837,6 @@ Bounded diff packet (read FIRST if present): $REVIEW_PACKET — hunks capped, no
 Run these only for files the packet marks truncated or excluded (or if the packet file is absent):
 $(review_diff_hint HEAD)
 
-Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
-
 Write your review report to: $REVIEW_REPORT
 
 The report MUST start with a line matching exactly:
diff --git a/incredible_auto_dev/scripts/automation/harvest-lessons.sh b/incredible_auto_dev/scripts/automation/harvest-lessons.sh
index b1ae1adc..ea07bd09 100755
--- a/incredible_auto_dev/scripts/automation/harvest-lessons.sh
+++ b/incredible_auto_dev/scripts/automation/harvest-lessons.sh
@@ -15,7 +15,7 @@
 # READ-ONLY AND JUDGMENT-FREE by contract (roadmap EVO-5): the script writes
 # nothing anywhere and draws no conclusions — it is a digest for a human+session
 # to review. Recurring symptoms across repos become either numbered
-# .claude/anti-patterns.md entries (maintenance protocol §2 format: symptom →
+# .claude/anti-patterns/ entries (maintenance protocol §2 format: symptom →
 # root cause → checkable rule) or docs/improvement-roadmap.md §16 staging items,
 # drafted by the reviewing session and promoted only by the human (EVO-1).
 #
diff --git a/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh b/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh
index 382a31a6..22cb65f8 100644
--- a/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh
+++ b/incredible_auto_dev/scripts/automation/lib/chain-tmp.sh
@@ -7,7 +7,7 @@
 # machine as the same user. Tools the agents run (pytest, playwright/chromium,
 # mktemp) used to write to shared /tmp — on some machines a QUOTA'D tmpfs
 # (EDQUOT long before the fs looks full) — and race each other's pruning (see
-# .claude/anti-patterns.md #21). Each run now gets its own short-lived dir
+# .claude/anti-patterns/21-shared-tmp-accumulation.md). Each run now gets its own short-lived dir
 # under CHAIN_TMP_ROOT (default ~/.cache/iad: big, unquota'd disk — NOT /tmp),
 # exported as TMPDIR, so cleanup is a single owner-guarded rm. /tmp remains a
 # LEGACY janitor root so pre-relocation strays still get reaped.
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index e5ff9547..fe3e4761 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -549,8 +549,6 @@ $(review_diff_hint "${_snap:-HEAD~1}")
 (Also \`git status\` for uncommitted changes. If the snapshot SHA is empty, diff against HEAD~1.)
 UI surface map (read if it exists): reports/phase-${_name}-ui-surface-map.md
 
-Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
-
 Write your verdict to: $_out
 The verdict line MUST appear first and start exactly with:
 **Verdict:** COHERENCE-PASS
@@ -864,6 +862,13 @@ escalate_model_on() {
     if declare -F record_telemetry_event >/dev/null 2>&1; then
       record_telemetry_event "model_escalation" "$(jq -cn --arg m "$_m" '{model:$m, escalated:true}' 2>/dev/null || printf '{"model":"%s","escalated":true}' "$_m")" || true
     fi
+  else
+    # CTX-13: fail LOUD — a silent no-op here means the fix-mode retry runs on
+    # the default tier while everyone believes it escalated.
+    echo "[escalation] WARNING: strong-tier model resolution FAILED — retry continues on the agent's default tier (check config/model-tiers.yaml and scripts/automation/lib/agent_permissions.py)" >&2
+    if declare -F record_telemetry_event >/dev/null 2>&1; then
+      record_telemetry_event "model_escalation" '{"escalated":false,"reason":"tier-resolution-failed"}' || true
+    fi
   fi
   return 0
 }
diff --git a/incredible_auto_dev/scripts/automation/lib/condense.sh b/incredible_auto_dev/scripts/automation/lib/condense.sh
index 127d0d6c..5890cb7a 100644
--- a/incredible_auto_dev/scripts/automation/lib/condense.sh
+++ b/incredible_auto_dev/scripts/automation/lib/condense.sh
@@ -11,10 +11,13 @@
 #     ## iter-<N> — <ISO timestamp>     state/lessons.md      (evaluator body §5)
 #     ## iter-<N> — <agent>             state/assumptions.md  (evaluator body §5b)
 #     ## Iteration <N> — <phase>        iteration-keyed logs
-#     ## <N>. <title>                   .claude/anti-patterns.md numbering
+#     ## <N>. <title>                   numbered-entry style (the retired
+#                                       anti-patterns monolith; now a per-entry
+#                                       tree at .claude/anti-patterns/, which
+#                                       never needs condensing)
 #   A block runs to the next unfenced `## ` heading or EOF. Everything before
 #   the first `## ` heading (title/preamble) is never touched. `## ` lines
-#   inside ``` fences are content, not boundaries (anti-patterns quotes goal.md
+#   inside ``` fences are content, not boundaries (entries may quote goal.md
 #   sections inside fences).
 #
 # WHAT MOVES: blocks whose key is NOT among the newest KEEP distinct keys in the
diff --git a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
index 02e0dcac..796a0ba4 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
+++ b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
@@ -42,7 +42,7 @@ _GOAL_GATES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 # Harness bookkeeping namespaces NEVER fed to the secret scanner: the gate must
 # scan product changes, not the pipeline's own generated output (scan-report /
 # iter-diff / trace / summaries quote findings → self-referential CRITICAL
-# recursion; see .claude/anti-patterns.md). Same set as CHAIN_STEP_HASH_EXCLUDES
+# recursion; see .claude/anti-patterns/22-scanner-flags-own-output.md). Same set as CHAIN_STEP_HASH_EXCLUDES
 # (lib/checkpoint.sh). Space-separated, env-overridable; note ':=' re-applies
 # the default when the var is exported EMPTY (a single space means "no
 # exclusions").
diff --git a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
index af382804..30a3e749 100644
--- a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
+++ b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
@@ -184,6 +184,16 @@ _interactive_invoke() {
     prompt+=$'\n\n'"Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR=\"$CHAIN_TMPDIR\" TMP=\"$CHAIN_TMPDIR\" TEMP=\"$CHAIN_TMPDIR\""
   fi
 
+  # CTX-8: on this backend the subagent's system prompt IS its rendered
+  # .claude/agents/<name>.md definition — stop it re-Reading its own 8-20 KB
+  # file every dispatch. Conditional on the pointer line being present so
+  # non-agent prompts (two-key confirms, ad-hoc dispatches — and the
+  # self-test's byte-exact round-trips) pass through untouched. Headless
+  # prompts keep the pointer as-is (there the file is NOT pre-loaded).
+  if [[ "$prompt" == *"Agent instructions: .claude/agents/"* ]]; then
+    prompt+=$'\n\n'"Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied."
+  fi
+
   # Optional per-dispatch model override (escalation ladder / two-key confirm).
   # Empty means "no override — the subagent's frontmatter tier applies".
   local model_override="${CHAIN_MODEL_OVERRIDE:-}"
diff --git a/incredible_auto_dev/scripts/automation/lib/plain-language.sh b/incredible_auto_dev/scripts/automation/lib/plain-language.sh
new file mode 100644
index 00000000..bc359fa1
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/plain-language.sh
@@ -0,0 +1,157 @@
+#!/usr/bin/env bash
+# plain-language.sh — PLAIN-1: plain-English explanations for status/verdict codes.
+#
+# Sourced by run-goal.sh and run-phase.sh. Every function ADDS lines next to the
+# existing code lines; nothing here may print a machine-parsed marker (**Verdict:**,
+# H2 headings, Depth Recommendation, Target journeys:) — tests/automation/
+# test-plain-language.sh enforces that, plus full key coverage.
+#
+# Single source of truth for the plain wording. docs/READING-REPORTS.md and
+# skills/plain-language.md mirror these sentences; change them together.
+#
+# All functions print to stdout and return 0 (callers add >&2 when the
+# neighbouring banner writes to stderr); unknown keys are safe no-ops so a new
+# status can never crash an engine running under set -euo pipefail.
+
+PLAIN_LANG_GUIDE="docs/READING-REPORTS.md"
+
+plain_goal_status_keys() {
+  cat <<'KEYS'
+GOAL_ACHIEVED
+BUDGET_EXHAUSTED
+STALLED
+REGRESSION_HALT
+ABORTED
+ABORT_MALFORMED
+GATE_BLOCKED
+AWAITING_BLUEPRINT_APPROVAL
+AWAITING_INTENT_REVIEW
+AWAITING_PUMP
+AWAITING_GITHUB_AUTH
+AWAITING_DISK
+AWAITING_HOST_GUARD
+KEYS
+  return 0
+}
+
+plain_goal_verdict_keys() {
+  cat <<'KEYS'
+GOAL_ACHIEVED
+CONTINUE
+ESCALATE
+REGRESSION
+STALLED
+KEYS
+  return 0
+}
+
+plain_phase_keys() {
+  cat <<'KEYS'
+review_pass
+review_fail
+qa_pass
+qa_fail
+all_passed
+KEYS
+  return 0
+}
+
+# explain_goal_status STATUS [SESSION_ID] [REPO_ROOT]
+# Prints 1-2 plain sentences for STATUS, a stable pointer to the reading guide,
+# and (when the args are given and the file exists) the friendliest artifact.
+explain_goal_status() {
+  local _st="${1:-}" _sid="${2:-}" _root="${3:-}"
+  case "$_st" in
+    GOAL_ACHIEVED)
+      echo "  The goal is complete: every must-have journey works and no rule was broken."
+      echo "  Nothing to fix — open the Session HTML above to see what was delivered."
+      ;;
+    BUDGET_EXHAUSTED)
+      echo "  The session stopped because it reached the iteration limit you set (--max-iter). Nothing is broken."
+      echo "  To build more: resume this session with a higher --max-iter."
+      ;;
+    STALLED)
+      echo "  The chain stopped because it could not make progress on its own. What was built so far still works."
+      echo "  Read the last evaluation, unblock the problem (or edit docs/goal.md), then resume."
+      ;;
+    REGRESSION_HALT)
+      echo "  Something that worked before is broken now, so the chain stopped to protect your product."
+      echo "  Read the evaluation named above; after you fix or accept the break, resume with --acknowledge-regression."
+      ;;
+    ABORTED)
+      echo "  The run was interrupted before it finished this iteration. Nothing is lost."
+      echo "  Resume when ready — it continues from the last saved point."
+      ;;
+    ABORT_MALFORMED)
+      echo "  The evaluator wrote an unreadable verdict twice in a row, so the chain stopped instead of guessing. Your product is unchanged."
+      echo "  Inspect the eval file named above, then resume."
+      ;;
+    GATE_BLOCKED)
+      echo "  A project rule (gate) rejected this iteration's plan, so the chain paused before building anything."
+      echo "  Check the gate verdict file above, fix the input, then resume."
+      ;;
+    AWAITING_BLUEPRINT_APPROVAL)
+      echo "  The chain is paused, not broken — nothing runs until you review the blueprint and resume."
+      ;;
+    AWAITING_INTENT_REVIEW)
+      echo "  The chain is paused, not broken — nothing runs until you finish this checkpoint and resume."
+      ;;
+    AWAITING_PUMP)
+      echo "  The Claude Code session that runs the agents went away, so the engine paused safely."
+      echo "  Re-open Claude Code in this repo and run /goal-resume — it repeats the interrupted iteration."
+      ;;
+    AWAITING_GITHUB_AUTH)
+      echo "  The chain paused because it cannot push to GitHub (login missing or expired). Your product is fine."
+      echo "  Run 'gh auth login', then resume."
+      ;;
+    AWAITING_DISK)
+      echo "  The chain paused because this computer is low on disk space — it never builds in that state."
+      echo "  Free some space (the command above helps), then resume."
+      ;;
+    AWAITING_HOST_GUARD)
+      echo "  The chain paused because this computer's hardware protection is not in place — it never builds unprotected."
+      echo "  Follow the reason printed above (project-extensions/host-guard/README.md), then resume."
+      ;;
+  esac
+  echo "  Read more: ${PLAIN_LANG_GUIDE}  (what each status and verdict means)"
+  if [[ -n "$_sid" && -n "$_root" && -f "$_root/reports/goal-session-${_sid}-index.html" ]]; then
+    echo "  Friendly overview: file://$_root/reports/goal-session-${_sid}-index.html"
+  fi
+  return 0
+}
+
+# explain_goal_verdict VERDICT NEXT_DEPTH
+# One added line under the per-iteration "Verdict:" line. Unknown verdict: silent.
+explain_goal_verdict() {
+  local _v="${1:-}" _depth="${2:-}" _gloss="" _next=""
+  case "$_v" in
+    GOAL_ACHIEVED) _gloss="every must-have journey now works, so the session will finish." ;;
+    CONTINUE)      _gloss="normal progress — the chain plans and builds the next piece by itself." ;;
+    ESCALATE)      _gloss="the last round found something tricky, so the next round uses the slower, more careful pipeline." ;;
+    REGRESSION)    _gloss="something that worked before is broken — the chain is stopping so you can look." ;;
+    STALLED)       _gloss="the evaluator sees no useful next step it can do alone — it is stopping to ask for your help." ;;
+    *) return 0 ;;
+  esac
+  case "$_v" in
+    CONTINUE|ESCALATE)
+      case "$_depth" in
+        lean) _next=" Next: a quick build-and-check round." ;;
+        full) _next=" Next: a full round with extra review, audit and UX checks." ;;
+      esac
+      ;;
+  esac
+  echo "  In plain words: ${_gloss}${_next}"
+  return 0
+}
+
+# explain_phase KEY — one plain line for run-phase.sh call sites.
+explain_phase() {
+  case "${1:-}" in
+    review_pass) echo "In plain words: the reviewer checked the new code and approved it." ;;
+    review_fail) echo "In plain words: the reviewer found problems. The developer agent will fix them and try again — you do not need to do anything." ;;
+    qa_pass)     echo "In plain words: all automated tests and checks passed." ;;
+    qa_fail)     echo "In plain words: testing found problems. The developer agent will fix them and the checks run again — you do not need to do anything." ;;
+    all_passed)  echo "  In plain words: this phase is done — code written, reviewed, and tested, and everything passed. Start with the 'What to click' file below to try it yourself." ;;
+  esac
+  return 0
+}
```
