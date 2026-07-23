# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 9073651f..746382aa 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -35,6 +35,7 @@ from __future__ import annotations
 
 import json
 import random
+import threading
 from calendar import monthrange
 from collections import defaultdict
 from datetime import date as date_cls, datetime, timedelta, timezone
@@ -984,6 +985,34 @@ def compute_forward_aggregates(
     }
 
 
+# ops-hardening iter-15 (UT-04 fix) — single-flight de-dup guarding `forward_aggregates_cached`'s MISS
+# path. Root-cause evidence (see the dev handoff for the full measurement): reading the pre-iter-15
+# function directly confirmed a cache MISS always fell straight through to `compute_forward_aggregates`
+# with NO de-duplication, lock, or in-flight marker — N concurrent same-key MISSes (e.g. the ingest
+# finalize warm's sequential 5-horizon loop landing on the SAME horizon/as-of the SAME moment
+# `GET /api/backtest`'s own 5-horizon comprehension requests it) each redundantly ran the full
+# aggregation. A throwaway measurement on a 60,000-row fixture (this iteration's dev pass) reproduced
+# this directly: 5 concurrent same-key MISSes invoked `compute_forward_aggregates` 5 times (not 1) and
+# took 9.9x a single call's wall-clock (near-linear blowup, consistent with GIL-serialized redundant
+# CPU-bound work) — confirming this mechanism, not a hypothesis. This mirrors
+# `data_manager.compute_coverage`'s established J-100 per-key-lock + in-flight-event single-flight idiom
+# (no new concurrency abstraction) — the difference: `ForwardAggregateCache` is already a PERSISTED
+# cross-request cache, so a waiter does not need its own in-process result cache; it simply re-reads the
+# now-committed row with its OWN session once the owner signals completion.
+_FORWARD_AGG_LOCK = threading.Lock()
+# per-key in-flight events: (horizon, asof_key, dataset_version) -> threading.Event, set when the owner
+# finishes (success or failure) so any waiter wakes. Always removed by the owner in a `finally` — this
+# dict never accumulates entries beyond what is genuinely being computed right now (unlike
+# `_COVERAGE_RESULTS`, this is not a persistent result cache, so it needs no size bound).
+_FORWARD_AGG_INFLIGHT: dict[tuple, threading.Event] = {}
+# Bounded wait for a waiter, mirroring `test_forward_testing_concurrency.py`'s existing
+# `BOUNDED_TIMEOUT_S` (45s — "generous vs. the real `database.pragmas.busy_timeout_ms` (30s) — a hang
+# would exceed this"). TC-8: if the owner never signals (an exception still runs the `finally` below
+# almost immediately; only a genuine wedge could exhaust this), the waiter falls through and computes
+# independently rather than blocking forever — never a second producer, just a rare redundant compute.
+_FORWARD_AGG_WAIT_TIMEOUT_S = 45.0
+
+
 def forward_aggregates_cached(
     session: Session, horizon: int, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
 ) -> dict:
@@ -1011,6 +1040,14 @@ def forward_aggregates_cached(
     concrete `ScannerRun.asof_date` first (never the bare `as_of=None` case), so `asof_key` is always a
     real ISO date.
 
+    ops-hardening iter-15 (UT-04 fix, J-06/J-07): a MISS now goes through an in-process single-flight
+    guard keyed on the SAME `(horizon, asof_key, dataset_version)` tuple — the FIRST concurrent caller
+    for a key becomes its owner and computes below; every OTHER concurrent caller for that SAME key waits
+    (bounded) on the owner's completion, then re-reads the now-persisted row with its OWN session — never
+    a second producer/compute. This is scoped ENTIRELY to this serving/caching wrapper:
+    `compute_forward_aggregates` itself, its signature, its columns read, and its streamed pattern are
+    completely unchanged (all three call sites keep calling it exactly as before).
+
     Deferred import below (not at module level): `research.py` already imports names FROM this module,
     so this module cannot import `research.py` at load time without a circular import; importing
     `_dataset_version` lazily, inside this function, breaks the cycle (the same fix has no effect on
@@ -1021,40 +1058,71 @@ def forward_aggregates_cached(
     version = _dataset_version(session)
     asof_key = as_of.isoformat() if as_of is not None else "all"
 
-    hit = session.exec(
-        select(ForwardAggregateCache).where(
-            ForwardAggregateCache.horizon == horizon,
-            ForwardAggregateCache.asof_key == asof_key,
-            ForwardAggregateCache.dataset_version == version,
-        )
-    ).first()
-    if hit is not None:
-        return json.loads(hit.payload_json)
-
-    # MISS — compute once (the SOLE producer, unchanged) and persist.
-    payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
-
-    # prune stale rows for THIS (horizon, asof_key) identity (any older dataset_version) so the cache
-    # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
-    stale = session.exec(
-        select(ForwardAggregateCache).where(
-            ForwardAggregateCache.horizon == horizon,
-            ForwardAggregateCache.asof_key == asof_key,
-            ForwardAggregateCache.dataset_version != version,
-        )
-    ).all()
-    for row in stale:
-        session.delete(row)
+    def _cached_row() -> Optional[dict]:
+        row = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == horizon,
+                ForwardAggregateCache.asof_key == asof_key,
+                ForwardAggregateCache.dataset_version == version,
+            )
+        ).first()
+        return json.loads(row.payload_json) if row is not None else None
 
-    session.add(ForwardAggregateCache(
-        horizon=horizon, asof_key=asof_key, dataset_version=version,
-        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
-    ))
+    hit = _cached_row()
+    if hit is not None:
+        return hit
+
+    # single-flight: only the FIRST caller for this key computes; concurrent same-key callers wait.
+    key = (horizon, asof_key, version)
+    with _FORWARD_AGG_LOCK:
+        event = _FORWARD_AGG_INFLIGHT.get(key)
+        is_owner = event is None
+        if is_owner:
+            event = threading.Event()
+            _FORWARD_AGG_INFLIGHT[key] = event
+
+    if not is_owner:
+        event.wait(timeout=_FORWARD_AGG_WAIT_TIMEOUT_S)
+        hit = _cached_row()
+        if hit is not None:
+            return hit
+        # TC-8: the owner failed (its `finally` already released the slot) or a genuine wedge exceeded
+        # the bounded wait without persisting — fall through and compute independently rather than
+        # blocking indefinitely. Still byte-identical (the SAME sole producer); at worst this is one
+        # redundant compute in a rare failure/timeout case, never a hang and never a second formula.
+
+    # MISS (owner path, or the rare TC-8 fallback above) — compute once and persist.
     try:
-        session.commit()
-    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
-        session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
-    return payload
+        payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+
+        # prune stale rows for THIS (horizon, asof_key) identity (any older dataset_version) so the cache
+        # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
+        stale = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == horizon,
+                ForwardAggregateCache.asof_key == asof_key,
+                ForwardAggregateCache.dataset_version != version,
+            )
+        ).all()
+        for row in stale:
+            session.delete(row)
+
+        session.add(ForwardAggregateCache(
+            horizon=horizon, asof_key=asof_key, dataset_version=version,
+            payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
+        ))
+        try:
+            session.commit()
+        except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
+            session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
+        return payload
+    finally:
+        # release the in-flight slot + wake any waiter whether we succeeded or raised (TC-8: a waiter then
+        # either finds the persisted payload or falls through and computes independently — never a hang).
+        if is_owner:
+            with _FORWARD_AGG_LOCK:
+                _FORWARD_AGG_INFLIGHT.pop(key, None)
+            event.set()
 
 
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
index 8d35d5cf..6d2feb41 100644
--- a/apps/backend/tests/test_forward_testing_concurrency.py
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -25,14 +25,23 @@ TC-4 mirrors iter-13's actual trigger shape (4 concurrent backfills' finalize ho
 not a single sequential process) with a `ThreadPoolExecutor`: each thread opens its OWN `Session` against
 a SHARED file-based engine — the same way a real multi-threaded ASGI server's request-handling threads
 each independently call into `compute_forward_aggregates`/`forward_aggregates_cached`.
+
+ops-hardening iter-15 (UT-04 fix) ADDS a second, clearly-separated test group at the bottom of this file
+(see the banner comment below) proving the single-flight de-dup this iteration adds to
+`forward_aggregates_cached`'s MISS path: TC-1 (same-key concurrent-MISS de-dup), TC-2 (concurrent-write-
+during-read wall-clock ratio — isolates candidate (c), WAL/session contention, from candidate (a)), and
+TC-8 (the fix's own failure path never deadlocks a waiter). These are a DIFFERENT iteration's TC numbering
+than iter-14's OWN TC-3/TC-4 above — named descriptively (never `test_tc1_`/`test_tc2_`) to avoid any
+ambiguity with iter-14's existing test names.
 """
 from __future__ import annotations
 
 import subprocess
 import sys
+import threading
 import time
 from concurrent.futures import ThreadPoolExecutor, as_completed
-from datetime import date, datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
 import pytest
@@ -42,7 +51,7 @@ from sqlmodel import Session, select
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.forward_testing import compute_forward_aggregates, forward_aggregates_cached
-from app.models import ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
+from app.models import DailyPrice, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
 
 BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)  # apps/backend — for the child subprocess's sys.path
 HORIZON = 20  # cfg.walk_forward.default_horizon
@@ -278,3 +287,245 @@ def test_tc4_concurrent_callers_all_complete_within_bounded_timeout(memory_press
     for payload in results[1:]:
         assert payload == first, "concurrent callers returned DIFFERENT payloads for the same horizon/as_of"
     assert first["overall"]["n"] == N_ROWS
+
+
+# ======================================================================================================
+# ops-hardening iter-15 (UT-04 fix) tests below — concurrency-safety of `forward_aggregates_cached`'s
+# MISS path (a DIFFERENT iteration's TC numbering than iter-14's OWN TC-3/TC-4 above; named
+# descriptively, never `test_tc1_`/`test_tc2_`, to avoid any ambiguity with iter-14's existing names).
+#
+# Root cause (measured during this iteration's development — see the dev handoff for the full write-up):
+# reading the pre-fix `forward_aggregates_cached` directly confirmed NO de-duplication existed — a MISS
+# always fell straight through to `compute_forward_aggregates` with no lock/in-flight marker. On this
+# exact 60,000-row fixture shape, 5 concurrent same-key MISSes measured 5 real `compute_forward_
+# aggregates` invocations and a 9.9x wall-clock blowup vs. a single baseline call PRE-fix; POST-fix (the
+# de-dup test below), exactly 1 invocation and ~1.0x. A SEPARATE probe isolating candidate (c)
+# (WAL/session contention, no redundant recomputation involved — the concurrent-write-during-read test
+# below) measured only a 1.59x ratio under an aggressive concurrent-write load — well inside TC-2's 5.0x
+# smoke-guard bound — so `app.db`'s session/WAL configuration is NOT touched this iteration.
+# ======================================================================================================
+TC2_N_ROWS = 100_000  # sized so a SINGLE uncontended compute_forward_aggregates call clears >=1.0s wall-
+                      # clock with comfortable margin (measured ~1.7-1.8s at this size on this host) — a
+                      # DISTINCT empirical sizing task from memory_pressure_db's memory-cap calibration
+                      # above (iter-14's TC-3), so this is its OWN fixture rather than reusing/resizing it.
+
+
+def _build_write_contention_db(db_path: Path) -> None:
+    """`TC2_N_ROWS` `ScannerResult` + `ForwardReturn` rows at `HORIZON` — large enough that a single
+    uncontended `compute_forward_aggregates` call takes >=1.0s wall-clock (empirically measured), so a
+    background writer thread has a real window to contend with the read."""
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    padding = "x" * RECORD_JSON_BYTES
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=date(2025, 1, 15), created_at=datetime.now(timezone.utc), provider="seed",
+            benchmark="SPY", regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        run_id = run.id
+        result_rows = [
+            dict(
+                run_id=run_id, ticker=f"SYM{i:06d}", name=f"SYM{i:06d}", sector="Technology",
+                leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
+                entry_quality_bucket="E", risk_score=0.0, risk_bucket="E", setup_status="Actionable",
+                rank=(i % 500) + 1, record_json=padding, is_vcp=False,
+                is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
+            )
+            for i in range(TC2_N_ROWS)
+        ]
+        session.execute(insert(ScannerResult.__table__), result_rows)
+        fr_rows = [
+            dict(
+                run_id=run_id, symbol=f"SYM{i:06d}", horizon=HORIZON, asof_date=date(2025, 1, 15),
+                entry_close=100.0, measured_date=date(2025, 2, 15), realized_return=0.01, max_drawdown=-0.02,
+            )
+            for i in range(TC2_N_ROWS)
+        ]
+        session.execute(insert(ForwardReturn.__table__), fr_rows)
+        session.commit()
+
+
+@pytest.fixture(scope="module")
+def write_contention_engine(tmp_path_factory):
+    db_path = tmp_path_factory.mktemp("write_contention") / "wc.db"
+    _build_write_contention_db(db_path)
+    return make_engine(f"sqlite:///{db_path}")
+
+
+def test_forward_aggregates_cached_dedups_concurrent_same_key_miss_to_one_compute(memory_pressure_db):
+    """TC-1 (iter-15, UT-04 fix): N=5 concurrent `forward_aggregates_cached` callers requesting the SAME
+    never-yet-cached `(horizon, asof_key, dataset_version)` key invoke the underlying heavy aggregation
+    body (`compute_forward_aggregates`) EXACTLY ONCE for that key (call-count instrumentation) — proving
+    the single-flight de-dup holds, not just that concurrent callers happen to agree on an answer (TC-4
+    above already proved byte-identity without proving de-duplication — this is the missing proof). All
+    N callers still return byte-identical payloads."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{memory_pressure_db}")
+    cfg = load_config()
+    as_of = date(2025, 7, 1)  # a DISTINCT as_of — a genuine, still-uncached MISS on this shared fixture
+    n_callers = 5
+
+    call_count = {"n": 0}
+    real = forward_testing_module.compute_forward_aggregates
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    def _caller():
+        with Session(engine) as session:
+            return forward_testing_module.forward_aggregates_cached(session, HORIZON, cfg, as_of=as_of)
+
+    forward_testing_module.compute_forward_aggregates = _counting
+    try:
+        with ThreadPoolExecutor(max_workers=n_callers) as pool:
+            futures = [pool.submit(_caller) for _ in range(n_callers)]
+            results = [f.result() for f in as_completed(futures, timeout=BOUNDED_TIMEOUT_S)]
+    finally:
+        forward_testing_module.compute_forward_aggregates = real
+
+    assert len(results) == n_callers, "not every caller completed — a caller hung"
+    assert call_count["n"] == 1, (
+        f"expected compute_forward_aggregates to run exactly once for {n_callers} concurrent same-key "
+        f"MISSes; it ran {call_count['n']} times — the single-flight de-dup did not hold"
+    )
+    first = results[0]
+    for payload in results[1:]:
+        assert payload == first, "concurrent callers returned DIFFERENT payloads for the same key"
+    assert first["overall"]["n"] == N_ROWS
+
+
+def test_compute_forward_aggregates_concurrent_write_during_read_ratio_bounded(write_contention_engine):
+    """TC-2 (iter-15, UT-04 fix): isolates candidate (c) (WAL/session contention) from candidate (a)
+    (redundant recomputation, proven separately by the de-dup test above) — a SINGLE
+    `compute_forward_aggregates` call (never routed through the cache/single-flight wrapper) timed alone
+    vs. timed while a background thread issues repeated committed writes throughout (mirrors ingest-warm
+    write activity: new `DailyPrice` bars for an unrelated symbol, inserted and committed one at a time
+    via its OWN session on the SAME shared engine). The ratio is a smoke guard against a gross
+    regression, not a tight bound — TC-4's operator-supervised live pass on the full deep basis is the
+    authoritative measurement."""
+    cfg = load_config()
+
+    with Session(write_contention_engine) as session:
+        t0 = time.monotonic()
+        baseline_payload = compute_forward_aggregates(session, HORIZON, cfg, as_of=None)
+        baseline = time.monotonic() - t0
+    assert baseline >= 1.0, (
+        f"fixture too small for this host — baseline={baseline:.3f}s, need >=1.0s (bump TC2_N_ROWS)"
+    )
+
+    stop_event = threading.Event()
+    write_count = {"n": 0}
+
+    def _writer():
+        with Session(write_contention_engine) as wsession:
+            i = 0
+            while not stop_event.is_set():
+                wsession.add(DailyPrice(
+                    symbol="ZZZWRITER", date=date(2020, 1, 1) + timedelta(days=i),
+                    open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+                ))
+                wsession.commit()
+                write_count["n"] += 1
+                i += 1
+
+    writer_thread = threading.Thread(target=_writer, daemon=True)
+    writer_thread.start()
+    try:
+        with Session(write_contention_engine) as session:
+            t0 = time.monotonic()
+            concurrent_payload = compute_forward_aggregates(session, HORIZON, cfg, as_of=None)
+            concurrent = time.monotonic() - t0
+    finally:
+        stop_event.set()
+        writer_thread.join(timeout=10)
+
+    ratio = concurrent / baseline
+    assert write_count["n"] > 0, (
+        "the background writer never got a chance to commit — test is not exercising contention"
+    )
+    assert concurrent_payload == baseline_payload, (
+        "concurrent writes to an UNRELATED symbol changed compute_forward_aggregates's own result"
+    )
+    assert ratio <= 5.0, (
+        f"concurrent-vs-baseline ratio {ratio:.2f}x exceeds the 5.0x smoke-guard bound "
+        f"(baseline={baseline:.3f}s, concurrent={concurrent:.3f}s, writes_during={write_count['n']})"
+    )
+
+
+def test_forward_aggregates_cached_waiter_does_not_deadlock_when_owner_raises(memory_pressure_db):
+    """TC-8 (iter-15, UT-04 fix): when the OWNER of a same-key MISS's in-flight computation raises, a
+    concurrent WAITING caller for that SAME key never blocks past the bounded timeout — it either raises
+    its own clean, isolated error or independently recomputes and returns a byte-identical payload.
+    Proves the single-flight fix's failure path cannot wedge a waiter (the fix's own `finally` releases
+    the in-flight slot and wakes waiters on ANY exit, success or failure)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{memory_pressure_db}")
+    cfg = load_config()
+    as_of = date(2025, 6, 1)  # a DISTINCT as_of — a genuine, still-uncached MISS on this shared fixture
+
+    owner_started = threading.Event()
+    owner_may_raise = threading.Event()
+    real = forward_testing_module.compute_forward_aggregates
+    call_count = {"n": 0}
+
+    def _owner_then_recover(*args, **kwargs):
+        call_count["n"] += 1
+        if call_count["n"] == 1:
+            owner_started.set()
+            owner_may_raise.wait(timeout=10)
+            raise RuntimeError("forced owner failure (TC-8 probe)")
+        return real(*args, **kwargs)
+
+    owner_result: dict = {}
+    waiter_result: dict = {}
+
+    def _owner_call():
+        with Session(engine) as session:
+            try:
+                forward_testing_module.forward_aggregates_cached(session, HORIZON, cfg, as_of=as_of)
+            except Exception as exc:  # noqa: BLE001 — captured for the assertion below, never swallowed silently
+                owner_result["error"] = exc
+
+    def _waiter_call():
+        with Session(engine) as session:
+            try:
+                waiter_result["payload"] = forward_testing_module.forward_aggregates_cached(
+                    session, HORIZON, cfg, as_of=as_of
+                )
+            except Exception as exc:  # noqa: BLE001
+                waiter_result["error"] = exc
+
+    forward_testing_module.compute_forward_aggregates = _owner_then_recover
+    start = time.monotonic()
+    try:
+        owner_thread = threading.Thread(target=_owner_call)
+        waiter_thread = threading.Thread(target=_waiter_call)
+        owner_thread.start()
+        assert owner_started.wait(timeout=10), "owner never claimed the in-flight slot"
+        waiter_thread.start()
+        time.sleep(0.2)  # let the waiter register as a non-owner before the owner is allowed to raise
+        owner_may_raise.set()
+        owner_thread.join(timeout=BOUNDED_TIMEOUT_S)
+        waiter_thread.join(timeout=BOUNDED_TIMEOUT_S)
+    finally:
+        forward_testing_module.compute_forward_aggregates = real
+    elapsed = time.monotonic() - start
+
+    assert not owner_thread.is_alive(), "owner thread did not finish — treat as a hang"
+    assert not waiter_thread.is_alive(), "waiter thread did not finish — treat as a hang"
+    assert elapsed < BOUNDED_TIMEOUT_S, f"resolution took {elapsed:.1f}s — treat as a hang, not a slow pass"
+    assert "error" in owner_result, "expected the owner's own forced exception to propagate to its caller"
+
+    assert "error" in waiter_result or "payload" in waiter_result, (
+        "the waiter neither raised a clean error nor returned a payload — the failure path is broken"
+    )
+    if "payload" in waiter_result:
+        with Session(engine) as session:
+            direct = real(session, HORIZON, cfg, as_of=as_of)
+        assert waiter_result["payload"] == direct, "waiter's fallback payload was not byte-identical"
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 389 +++++++++++++++++++++
 runs/goal-session-ops-hardening/state/blueprint.md |  44 ++-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   7 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   3 +
 5 files changed, 429 insertions(+), 16 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
