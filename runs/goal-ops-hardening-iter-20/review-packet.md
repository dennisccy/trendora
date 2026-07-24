# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index bab9c19f..47702b1a 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -23,12 +23,24 @@ ops-hardening iter-16 (J-08): for the LATEST view (`is_latest == True`) this end
 forward-aggregate compute on the request — `evidence_by_horizon` (plus `evidence_status` /
 `evidence_generated_at`) comes ONLY from `resolved_forward_aggregate_evidence`, a pure reader that is
 structurally incapable of calling `compute_forward_aggregates`. A HISTORICAL (`is_latest == False`)
-`?as_of=` request keeps its pre-existing lazy create-once-and-cache behavior UNCHANGED (an explicit,
-logged interpretation call — see the iter-16 dev handoff): this endpoint resolves first, and only when
-that read is not already `"ready"` (audit B5 — never unconditionally) does it ensure every configured
-horizon is cached for that date (computing any still-missing one via `forward_aggregates_ingest_cached`,
-exactly as before iter-16) and re-resolve, so both branches still share ONE code path for building the
-response's evidence fields.
+`?as_of=` request keeps its pre-existing lazy create-once-and-cache behavior — this endpoint resolves
+first, and only when that read is not already `"ready"` (audit B5 — never unconditionally) does it ensure
+every configured horizon gets cached for that date (computing any still-missing one), so both branches
+still share ONE code path for building the response's evidence fields. iter-20 changed WHO/WHEN performs
+that compute (see immediately below) — never the gate itself, never the resolver's own read logic.
+
+ops-hardening iter-20 (J-06/J-07/J-08): the historical branch's compute moved OFF the request thread. It
+no longer calls `forward_aggregates_ingest_cached` in a loop itself; instead it calls
+`ensure_historical_forward_aggregates_dispatched`, which is a single-flight-guarded trigger for a
+BACKGROUND daemon thread (its own DB session) that does the same per-horizon
+`forward_aggregates_ingest_cached` loop off-thread. The request thread never waits on it — this endpoint
+still returns the SAME pre-dispatch `evidence` read from `resolved_forward_aggregate_evidence` above (the
+honest interim state: `"refreshing"` or `"not_yet_computed"`), so a first-ever view of a not-yet-warmed
+historical date now renders within budget instead of blocking up to ~54s (live UT-04 evidence). A LATER
+request for the SAME date, once the background compute lands, serves `"ready"` — byte-identical to what
+the old synchronous path produced. The create-once/cache substance is unchanged (still lazy, still
+computed exactly once per identity); only the timing of WHEN the compute runs relative to the request
+changed. See `docs/handoffs/goal-ops-hardening-iter-20-dev.md` for the full write-up.
 
 ops-hardening iter-17 (audit B1): the resolver's OWN fallback now crosses `asof_key` boundaries — when
 the resolved as-of has never had a complete forward-aggregate version of its own (the common shape right
@@ -59,6 +71,7 @@ from app.db import get_session
 from app.engine.forward_testing import (
     backfill_run_forward_returns,
     compute_run_scorecard,
+    ensure_historical_forward_aggregates_dispatched,
     forward_aggregates_ingest_cached,
     resolved_forward_aggregate_evidence,
 )
@@ -96,15 +109,22 @@ def _log_backtest_timing(
     """One INFO-level, key=value structured timing line per `/backtest` request: an ISO-8601 wall-clock
     timestamp plus the elapsed-ms breakdown the iter-18 spec calls for -- run resolution, the
     `backfill_run_forward_returns` step, `compute_run_scorecard`, and `resolved_forward_aggregate_
-    evidence`. `ensure_loop_ms` (the historical/non-`is_latest` ensure-loop's `forward_aggregates_
-    ingest_cached` calls plus its re-resolve) is present ONLY when that branch actually ran -- never a
-    fabricated 0 for the `is_latest` request path, which never reaches it. `write_taken` (iter-19,
-    J-06/J-07/J-08) records whether `backfill_run_forward_returns`'s create-once write was actually
-    committed this request (`True`, the genuinely-missing case) or skipped entirely because every row
-    already existed (`False`, the new zero-write guard's common warm-path outcome) -- appended LAST so
-    the pre-existing field positions/regex this line's own consumers already rely on are undisturbed.
-    Purely an operational log line for the iter-18/iter-19 latency diagnosis -- never a served/displayed
-    value (Data Contract untouched)."""
+    evidence`. `ensure_loop_ms` is present ONLY when the historical/non-`is_latest` branch actually ran --
+    never a fabricated 0 for the `is_latest` request path, which never reaches it.
+
+    ops-hardening iter-20 (J-06/J-07/J-08): `ensure_loop_ms` is REPURPOSED (field name kept unchanged so
+    every existing consumer/regex of this log line -- `test_backtest_timing.py` included -- keeps matching
+    verbatim) from timing a synchronous per-horizon compute-and-wait loop to timing the sub-millisecond
+    dispatch-DECISION cost only (`ensure_historical_forward_aggregates_dispatched`'s lock-check-and-maybe-
+    spawn-a-thread call) -- it is NEVER again a multi-second compute-wait duration, because the request
+    thread no longer waits on the compute at all (TC-2).
+
+    `write_taken` (iter-19, J-06/J-07/J-08) records whether `backfill_run_forward_returns`'s create-once
+    write was actually committed this request (`True`, the genuinely-missing case) or skipped entirely
+    because every row already existed (`False`, the new zero-write guard's common warm-path outcome) --
+    appended LAST so the pre-existing field positions/regex this line's own consumers already rely on are
+    undisturbed. Purely an operational log line for the iter-18/iter-19/iter-20 latency diagnosis -- never
+    a served/displayed value (Data Contract untouched)."""
     fields = [
         f"ts={datetime.now(timezone.utc).isoformat()}",
         f"is_latest={is_latest}",
@@ -166,28 +186,29 @@ def backtest(
     evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
     evidence_ms = (time.perf_counter() - t0) * 1000.0
     # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
-    # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
-    # for this date, then re-resolve. For the LATEST view this never runs, so this request path never
-    # reaches `forward_aggregates_ingest_cached` — let alone `compute_forward_aggregates` — under any
-    # circumstance (J-08's zero-compute-on-request guarantee).
+    # lazy create-once-and-cache behavior (TC-13). For the LATEST view this branch never runs, so this
+    # request path never reaches `ensure_historical_forward_aggregates_dispatched` — let alone
+    # `compute_forward_aggregates` — under any circumstance (J-08's zero-compute-on-request guarantee).
     #
     # iter-17 (audit B5): gated on the resolver's OWN first read rather than unconditional — on an
     # already-warmed historical date (the common repeat-view case for the Backtest/Time-Machine
-    # workspace) the resolver above already found `evidence_status == "ready"`, so the ensure loop below
-    # is skipped entirely, avoiding a redundant per-horizon cache-hit read+deserialize immediately
-    # followed by the SAME resolver re-reading and re-parsing those same rows a second time. Byte-
-    # identical either way (still one producer, one serving read): a cold historical date still ensures
-    # every horizon is cached (computing any still-missing one) and re-resolves once, exactly as before.
+    # workspace) the resolver above already found `evidence_status == "ready"`, so the dispatch below is
+    # skipped entirely — no lock touched, no thread spawned, nothing to do.
     #
-    # ops-hardening iter-18: `ensure_loop_ms` times this WHOLE block (the per-horizon
-    # `forward_aggregates_ingest_cached` calls plus the re-resolve) — present in the timing log line ONLY
-    # when this branch actually runs, mirroring exactly when `forward_aggregates_ingest_cached` fires.
+    # ops-hardening iter-20 (J-06/J-07/J-08): this branch NO LONGER computes/waits on the request thread.
+    # It triggers `ensure_historical_forward_aggregates_dispatched` — a single-flight-guarded BACKGROUND
+    # dispatch (own DB session; a no-op if a dispatch for this identity is already in flight) — and does
+    # NOT re-resolve: `evidence` stays the PRE-dispatch read above (the honest interim state: `"refreshing"`
+    # or `"not_yet_computed"`), served immediately. A LATER request for this SAME date, once the background
+    # compute lands, will find the resolver's own read already `"ready"` and skip this branch entirely.
+    #
+    # ops-hardening iter-18: `ensure_loop_ms` times this block — present in the timing log line ONLY when
+    # this branch actually runs. iter-20 repurposed its MEANING (see `_log_backtest_timing`'s docstring):
+    # now the dispatch-DECISION cost only (sub-millisecond, TC-2), never a compute-wait duration.
     ensure_loop_ms: Optional[float] = None
     if not is_latest and evidence["evidence_status"] != "ready":
         t0 = time.perf_counter()
-        for h in cfg.walk_forward.horizons:
-            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
-        evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+        ensure_historical_forward_aggregates_dispatched(session, run.asof_date, cfg)
         ensure_loop_ms = (time.perf_counter() - t0) * 1000.0
 
     total_ms = (time.perf_counter() - t_request_start) * 1000.0
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index f8ec95b8..020b3da5 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -34,6 +34,7 @@ benchmark symbols) comes from config — no walk-forward literal lives here (ant
 from __future__ import annotations
 
 import json
+import logging
 import random
 import threading
 from calendar import monthrange
@@ -59,6 +60,11 @@ from app.models import (
     ScannerRun,
 )
 
+# ops-hardening iter-20 (J-06/J-07/J-08) -- the historical background-dispatch worker's own non-fatal
+# exception log (mirrors `warmup.py`'s established "trendora.<module>" + `logger.exception(...)` convention
+# for a daemon-thread worker body; see `_run_historical_forward_aggregates_dispatch` below).
+logger = logging.getLogger("trendora.forward_testing")
+
 # The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). iter-18: the
 # basis now spans ~30 years (1996 -> present, per-name real listing depth) over the broadened
 # point-in-time candidate pool — but the pool itself is built from CURRENT index constituents, so
@@ -1167,6 +1173,110 @@ def forward_aggregates_ingest_cached(
             event.set()
 
 
+# ops-hardening iter-20 (J-06/J-07/J-08) -- the OUTER single-flight dispatch guard that takes the
+# historical (`is_latest == False`) carve-out's own compute OFF the request thread entirely. Root cause
+# (see the iter-20 dev handoff): `GET /api/backtest` / MCP `query_backtest` used to call
+# `forward_aggregates_ingest_cached` SYNCHRONOUSLY, in a loop over every configured horizon, on the
+# request thread itself, whenever a historical as-of's evidence was not already `"ready"` -- live UT-04
+# evidence showed this stalling the request 9.6-54s (a bounded 45s single-flight WAIT on the existing
+# per-horizon lock above, plus a redundant compute on timeout, under concurrency).
+#
+# This guard sits ONE LEVEL ABOVE that existing per-horizon lock (`_FORWARD_AGG_LOCK` /
+# `_FORWARD_AGG_INFLIGHT`, unchanged above -- it still protects `forward_aggregates_ingest_cached`'s own
+# MISS path exactly as before, including against a concurrent INGEST warm racing this dispatch for the
+# same key). Its job is narrower: decide whether a BACKGROUND dispatch is already in flight for this
+# `(asof_key, dataset_version)` identity BEFORE the request thread ever touches the per-horizon lock at
+# all -- so the request thread never calls `event.wait()`, never computes, never blocks. Keyed on the
+# SAME `(asof_key, dataset_version)` identity `resolved_forward_aggregate_evidence` already resolves by
+# (the iter-16 lesson: "enumerate the ways the identity can move, not just the ways the value can go
+# stale" -- never a new axis).
+#
+# A key is inserted by whichever request thread wins the race to dispatch (holding `_HIST_DISPATCH_LOCK`
+# only for the tiny check-and-insert -- sub-millisecond, TC-2) and removed by the BACKGROUND thread itself
+# in a `finally`, on success AND on an owner exception (TC-7) -- so a later request for the same identity
+# can always re-dispatch; this guard is structurally incapable of a permanent wedge. Unlike
+# `_FORWARD_AGG_INFLIGHT` above, no `threading.Event`/waiter is needed here: the request thread that finds
+# a key already in flight simply does nothing and returns (the already-running dispatch will land on its
+# own; the NEXT request for this identity re-reads `resolved_forward_aggregate_evidence` and sees it).
+_HIST_DISPATCH_LOCK = threading.Lock()
+_HIST_DISPATCH_INFLIGHT: set[tuple[str, str]] = set()  # {(asof_key, dataset_version)} dispatched right now
+
+
+def _run_historical_forward_aggregates_dispatch(
+    engine: Engine, as_of: date_cls, cfg: Config, key: tuple[str, str],
+) -> None:
+    """The background worker body -- runs in its OWN daemon thread, opens its OWN `Session(engine)`
+    (mirrors `data_manager.start_data_job` / `warmup.start_warmup`'s established thread-plus-own-session
+    idiom: a daemon thread that owns its own DB session rather than sharing the request's). Computes every
+    configured horizon for `as_of` via the UNCHANGED `forward_aggregates_ingest_cached` -- this function
+    decides ONLY *when* to call it, never *how*: the per-horizon single-flight lock, the cutover-pruning
+    completeness contract, and the persistence are all reused verbatim (no second producer), so a
+    concurrent ingest warm for the SAME identity still de-dups correctly against this dispatch too.
+
+    Any exception is CAUGHT + logged (mirrors `warmup._run_warmup`'s own non-fatal convention) -- never
+    left to crash silently or to propagate to the request thread that triggered the dispatch (TC-7): that
+    thread has already returned its response long before this runs. The outer guard's slot is released in
+    a `finally` on success AND on failure, so a subsequent request for the SAME identity can always
+    re-dispatch and eventually reach `"ready"` -- never a permanent wedge."""
+    try:
+        with Session(engine) as session:
+            for h in cfg.walk_forward.horizons:
+                forward_aggregates_ingest_cached(session, h, cfg, as_of=as_of)
+    except Exception:
+        logger.exception(
+            "historical forward-aggregate background dispatch failed (non-fatal, will re-dispatch on the "
+            "next request for this identity, key=%s)", key,
+        )
+    finally:
+        with _HIST_DISPATCH_LOCK:
+            _HIST_DISPATCH_INFLIGHT.discard(key)
+
+
+def ensure_historical_forward_aggregates_dispatched(
+    session: Session, as_of: date_cls, config: Optional[Config] = None,
+) -> None:
+    """ops-hardening iter-20 (J-06/J-07/J-08) -- the request-triggered, single-flight-guarded BACKGROUND
+    dispatch for the historical (`is_latest == False`) carve-out's own compute. `GET /api/backtest` / MCP
+    `query_backtest` (identical call in both) call this ONLY when the resolver's own first read already
+    found this identity is not `"ready"` (the SAME `!= "ready"` gate as before iter-20 -- unchanged).
+
+    Uses the CALLING session ONLY to read the CURRENT `dataset_version` (a cheap read within the
+    already-open request transaction, no write) to decide the dispatch key. If a background compute is
+    already in flight for this EXACT `(asof_key, dataset_version)` identity, this is a sub-millisecond
+    no-op (TC-2) -- the already-running dispatch will reach `"ready"` on its own. Otherwise it spawns a NEW
+    daemon thread with its OWN `Session` bound to the SAME engine the calling session is bound to
+    (`session.get_bind()` -- so a caller passing a private test engine or the process-global engine both
+    dispatch against the SAME database the resolver will later re-read; mirrors `data_manager.py`'s own
+    `session.get_bind()` idiom) and returns IMMEDIATELY. The request thread never calls
+    `compute_forward_aggregates`, never waits on the per-horizon lock, never blocks (J-08's literal "never
+    a request-path recompute").
+
+    This function itself never computes, never re-resolves, and never returns the dispatched result -- the
+    caller already read `resolved_forward_aggregate_evidence` before calling this (and returns THAT read,
+    the honest interim state -- `"refreshing"` or `"not_yet_computed"`) and will see the completed evidence
+    only on a LATER request, once the background thread's own commit lands (TC-1/TC-3/TC-4)."""
+    from app.engine.research import _dataset_version  # deferred: avoids a forward_testing<->research cycle
+
+    cfg = config or get_config()
+    version = _dataset_version(session)
+    asof_key = as_of.isoformat()
+    key = (asof_key, version)
+
+    with _HIST_DISPATCH_LOCK:
+        if key in _HIST_DISPATCH_INFLIGHT:
+            return  # a dispatch for this EXACT identity is already running -- no-op, never a duplicate
+        _HIST_DISPATCH_INFLIGHT.add(key)
+
+    engine = session.get_bind()
+    thread = threading.Thread(
+        target=_run_historical_forward_aggregates_dispatch,
+        args=(engine, as_of, cfg, key),
+        daemon=True,
+        name=f"backtest-hist-dispatch-{asof_key}",
+    )
+    thread.start()
+
+
 def _utc_isoformat(value: datetime) -> str:
     """iter-17 (audit B3): `evidence_generated_at` is contracted as an ISO-8601 UTC datetime but was
     serialized via a naive `.isoformat()` (no `Z`/offset) because SQLite reads a stored timestamp back
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 68c054f0..0e21c6d0 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -34,6 +34,7 @@ from app.engine.forward_testing import (
     backfill_run_forward_returns,
     benchmark_symbols,
     compute_run_scorecard,
+    ensure_historical_forward_aggregates_dispatched,
     forward_aggregates_ingest_cached,
     resolved_forward_aggregate_evidence,
 )
@@ -244,19 +245,24 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     score / bucket / return.
 
     ops-hardening iter-16 (J-08): mirrors the endpoint's own compute-vs-serve split exactly — for the
-    LATEST view this tool never reaches `forward_aggregates_ingest_cached` (let alone
+    LATEST view this tool never reaches `ensure_historical_forward_aggregates_dispatched` (let alone
     `compute_forward_aggregates`); a historical `asof` keeps the pre-existing lazy create-once-and-cache
-    carve-out (TC-13), unchanged.
+    carve-out (TC-13).
 
     ops-hardening iter-17 (audit B1/B5): mirrors the endpoint's widened cross-`asof_key` last-good
     fallback (the new `evidence_asof` field discloses which as-of's evidence is actually served) and its
-    B5 gate — the historical ensure-loop below runs ONLY when the resolver's first read is not already
-    `"ready"`, never unconditionally, avoiding a redundant per-horizon cache-hit read+deserialize
-    immediately followed by the same resolver re-reading those same rows.
+    B5 gate — the historical dispatch below runs ONLY when the resolver's first read is not already
+    `"ready"`, never unconditionally.
 
     ops-hardening iter-18: wrapped in per-request, phase-broken-down wall-clock timing instrumentation
     (`_log_query_backtest_timing`) mirroring `app.api.backtest.backtest`'s own — observability only, the
-    returned payload stays byte-identical (TC-6)."""
+    returned payload stays byte-identical (TC-6).
+
+    ops-hardening iter-20 (J-06/J-07/J-08): mirrors the endpoint's own change identically — the historical
+    branch no longer computes/waits on the request thread. It triggers
+    `ensure_historical_forward_aggregates_dispatched` (single-flight-guarded BACKGROUND dispatch, own DB
+    session) and does NOT re-resolve: `evidence` stays the PRE-dispatch read (the honest interim state),
+    served immediately, byte-identical to the HTTP endpoint's own behavior for the same inputs (TC-6)."""
     t_request_start = time.perf_counter()
     cfg = get_config()
 
@@ -284,12 +290,13 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     t0 = time.perf_counter()
     evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
     evidence_ms = (time.perf_counter() - t0) * 1000.0
+    # ops-hardening iter-20 (J-06/J-07/J-08): mirrors `app.api.backtest.backtest`'s own change exactly —
+    # triggers the single-flight-guarded BACKGROUND dispatch (a no-op if already in flight or already
+    # `"ready"`) and does NOT re-resolve; `evidence` stays the PRE-dispatch read (the honest interim state).
     ensure_loop_ms: Optional[float] = None
     if not is_latest and evidence["evidence_status"] != "ready":
         t0 = time.perf_counter()
-        for h in cfg.walk_forward.horizons:
-            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
-        evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+        ensure_historical_forward_aggregates_dispatched(session, run.asof_date, cfg)
         ensure_loop_ms = (time.perf_counter() - t0) * 1000.0
 
     total_ms = (time.perf_counter() - t_request_start) * 1000.0
diff --git a/apps/backend/tests/test_api_backtest.py b/apps/backend/tests/test_api_backtest.py
index da09560a..66b1c577 100644
--- a/apps/backend/tests/test_api_backtest.py
+++ b/apps/backend/tests/test_api_backtest.py
@@ -11,6 +11,8 @@ backfill, so every stored run already has its forward returns (the create-once p
 """
 from __future__ import annotations
 
+import time
+
 import pytest
 from fastapi import HTTPException
 from fastapi.testclient import TestClient
@@ -239,11 +241,29 @@ def test_backtest_evidence_is_as_of_scoped_expanding_window(loaded_engine):
     """J-09 expanding window at the API level: the evidence is scoped to snapshots dated <= the resolved
     as-of date. At the OLDEST date only that one run contributes (n_runs == 1); at the latest (default)
     every run contributes and the sample is strictly larger — n is non-decreasing toward latest and no
-    run dated > D leaks in (every contributing as-of date <= the cutoff)."""
+    run dated > D leaks in (every contributing as-of date <= the cutoff).
+
+    ops-hardening iter-20: the oldest date's own evidence was never precomputed at ingest (only the LATEST
+    date is warmed by the fixture, mirroring the real ingest finalize hook — see `loaded_engine`'s own
+    docstring) and this historical view's compute now runs OFF the request thread, dispatched in the
+    background rather than awaited synchronously. The first request therefore returns an honest interim
+    state immediately; this test polls (bounded) for that dispatched compute to land before asserting the
+    SAME expanding-window/no-lookahead guarantees it has always encoded (TC-11, AG-5)."""
     h = str(load_config().walk_forward.default_horizon)
     with TestClient(main.app) as client:
         oldest = _oldest_date(client)
-        at_oldest = client.get(f"/api/backtest?as_of={oldest}").json()["evidence_by_horizon"][h]
+
+        deadline = time.monotonic() + 10.0
+        payload = client.get(f"/api/backtest?as_of={oldest}").json()
+        while payload["evidence_status"] != "ready":
+            assert time.monotonic() < deadline, (
+                f"the oldest date's own dispatched evidence never reached 'ready' within 10s "
+                f"(last evidence_status={payload['evidence_status']!r})"
+            )
+            time.sleep(0.05)
+            payload = client.get(f"/api/backtest?as_of={oldest}").json()
+        at_oldest = payload["evidence_by_horizon"][h]
+
         at_latest = client.get("/api/backtest").json()["evidence_by_horizon"][h]
     assert at_oldest["n_runs"] == 1                    # only the oldest snapshot is <= the oldest date
     assert at_latest["n_runs"] > at_oldest["n_runs"]   # the window expands toward latest
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
index 8fa56470..bfa4859e 100644
--- a/apps/backend/tests/test_forward_testing_concurrency.py
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -679,3 +679,268 @@ def test_iter19_concurrent_missing_run_backtest_calls_no_duplicate_rows_and_roll
         "expected the IntegrityError-tolerant rollback path to be exercised by at least one of the 5 "
         "concurrent callers racing to backfill the SAME genuinely-missing run"
     )
+
+
+# ======================================================================================================
+# ops-hardening iter-20 (J-06/J-07/J-08) — the NEW outer single-flight dispatch guard that takes the
+# historical (`is_latest == False`) carve-out's compute OFF the request thread entirely
+# (`forward_testing.py`'s `ensure_historical_forward_aggregates_dispatched` /
+# `_run_historical_forward_aggregates_dispatch`, `_HIST_DISPATCH_LOCK` / `_HIST_DISPATCH_INFLIGHT`). A
+# DIFFERENT guard from every group above (those all exercise the INNER per-horizon lock
+# `forward_aggregates_ingest_cached` itself owns — unchanged by this iteration): this one decides whether
+# the REQUEST THREAD spawns a background dispatch AT ALL, so the request thread never calls `event.wait()`
+# on the inner lock in the first place.
+# ======================================================================================================
+def _seed_historical_run(session: Session, asof: date, ticker: str = "AAA") -> ScannerRun:
+    """A minimal historical `ScannerRun` + one `ScannerResult` + its entry-day `DailyPrice` bar — enough
+    for `resolved_run`'s `latest_data_date` check and for the historical dispatch to have something to
+    compute (an all-NA horizon set is a legitimate, honest result; these tests assert compute-COUNT and
+    dispatch-behavior, not non-empty content, mirroring `test_forward_testing_serving_split.py`'s own
+    `endpoint_engine`-based historical tests)."""
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+        new_high_low_json="{}", candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.flush()
+    session.add(ScannerResult(
+        run_id=run.id, ticker=ticker, name=ticker, sector="Technology", leadership_score=50.0,
+        leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
+        risk_bucket="C", setup_status="Actionable", rank=1, record_json="{}", is_vcp=False,
+        is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
+    ))
+    session.add(DailyPrice(
+        symbol=ticker, date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+    ))
+    return run
+
+
+# Sized like this file's OWN `write_contention_engine` calibration (TC2_N_ROWS, module docstring): large
+# enough IN TOTAL that a SINGLE uncontended `compute_forward_aggregates` call at this horizon clears
+# >=1.0s wall-clock, so TC-3's "never blocks the request thread" claim is a REAL, measurable discriminator
+# between the OLD synchronous ensure-loop (every one of the 5 concurrent requests would take >=1s: the
+# owner computing, the other 4 waiting on the existing inner per-horizon lock) and the NEW dispatch (every
+# request returns near-instantly regardless).
+#
+# Spread across `_TC20_FILLER_RUNS` SEPARATE runs (never attached to the ONE run actually requested) --
+# `compute_forward_aggregates`'s cost scales with the TOTAL row count across the whole expanding window,
+# but `compute_run_scorecard` / `backfill_run_forward_returns` (called on EVERY /backtest request
+# regardless of this iteration's dispatch mechanism -- unrelated, unchanged code) are each scoped to ONE
+# run's OWN rows. Attaching all the volume to the requested run itself (an earlier draft of this fixture)
+# made THOSE two calls slow too, confounding the measurement: the request would be slow via a totally
+# different, already-existing, out-of-scope code path (a real, reproducible finding, but not what TC-3
+# tests) rather than via the historical ensure-loop this iteration actually changes. Spreading the volume
+# across OTHER, older runs keeps the requested run's own per-request cost negligible while still making
+# `compute_forward_aggregates`'s expanding-window aggregate genuinely slow. `record_json` is NOT padded
+# (unlike `memory_pressure_db`/`write_contention_engine`, which pad it for a DIFFERENT concern -- real
+# per-row memory footprint): `compute_forward_aggregates`'s own `ScannerResult` read is column-projected
+# and never selects `record_json`, so the slow part (proven by `write_contention_engine`'s own
+# measurement) is the CPU-bound Python-side grouping over N rows, not disk I/O for a column never read.
+_TC20_FILLER_RUNS = 10
+_TC20_ROWS_PER_FILLER_RUN = 10_000  # 10 * 10,000 = 100,000 total, matching write_contention_engine's own N
+
+
+def test_iter20_concurrent_first_touch_historical_requests_dispatch_exactly_once(tmp_path):
+    """TC-3 (mandatory concurrency test, spec DoD): N=5 concurrent `GET /api/backtest` calls for the SAME
+    never-before-warmed historical `as_of` invoke `compute_forward_aggregates` EXACTLY `len(horizons)`
+    times IN TOTAL (never `5 * len(horizons)` — the old per-request synchronous ensure-loop's bug this
+    iteration fixes — never zero), and every one of the 5 calls returns FAST: the request thread never
+    waits on the dispatched compute (proven by each call's own wall-clock against a fixture sized so the
+    compute itself provably takes >=1s -- not just proven by the aggregate call-count)."""
+    import app.api.backtest as backtest_module
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'tc20_dispatch_once.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    asof = date(2024, 3, 1)
+    latest_asof = date(2025, 1, 10)  # strictly LATER -> `asof` resolves is_latest=False
+    heavy_horizon = cfg.walk_forward.horizons[0]
+    with Session(engine) as session:
+        _seed_historical_run(session, asof)
+        # A strictly LATER run (bare -- no ScannerResult, no DailyPrice of its own) purely so `asof` above
+        # is NOT the latest stored date (`_latest_stored_run_date` = max(ScannerRun.asof_date) only;
+        # "AAA"'s own entry-day bar at `asof` already satisfies `latest_data_date`'s "a bar exists at all"
+        # check). Deliberately NO post-`asof` DailyPrice bar anywhere: that keeps `observable_days == 0`
+        # for `asof`'s own `backfill_run_forward_returns` create-once step, so it stays a cheap no-op for
+        # every symbol -- isolating this test from the SEPARATE, already-flagged, out-of-scope
+        # `_insert_run_forward_returns` concurrent-autoflush race (iter-19 dev handoff's Known Issues;
+        # iter-19's own TC-4 sidesteps the identical hazard by pre-seeding its "other" symbols instead).
+        session.add(ScannerRun(
+            asof_date=latest_asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.flush()
+
+        # `_TC20_FILLER_RUNS` SEPARATE, older runs (all strictly < `asof`, so all fall inside its expanding
+        # window) each carrying `_TC20_ROWS_PER_FILLER_RUN` rows at `heavy_horizon` -- see the module note
+        # above for why this volume lives on OTHER runs, never on the one actually requested.
+        filler_run_ids: list[int] = []
+        for f in range(_TC20_FILLER_RUNS):
+            filler_run = ScannerRun(
+                asof_date=date(2020, 1, 1) + timedelta(days=f), created_at=datetime.now(timezone.utc),
+                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Risk-on",
+                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(filler_run)
+            session.flush()
+            filler_run_ids.append(filler_run.id)
+        session.commit()
+
+        result_rows = [
+            dict(
+                run_id=filler_run_ids[i // _TC20_ROWS_PER_FILLER_RUN], ticker=f"SYM{i:06d}", name=f"SYM{i:06d}",
+                sector="Technology", leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
+                entry_quality_bucket="E", risk_score=0.0, risk_bucket="E", setup_status="Actionable",
+                rank=(i % 500) + 1, record_json="{}", is_vcp=False,
+                is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
+            )
+            for i in range(_TC20_FILLER_RUNS * _TC20_ROWS_PER_FILLER_RUN)
+        ]
+        session.execute(insert(ScannerResult.__table__), result_rows)
+        fr_rows = [
+            dict(
+                run_id=filler_run_ids[i // _TC20_ROWS_PER_FILLER_RUN], symbol=f"SYM{i:06d}", horizon=heavy_horizon,
+                asof_date=date(2020, 1, 1) + timedelta(days=i // _TC20_ROWS_PER_FILLER_RUN),
+                entry_close=100.0, measured_date=date(2020, 1, 1) + timedelta(days=i // _TC20_ROWS_PER_FILLER_RUN),
+                realized_return=0.01, max_drawdown=-0.02,
+            )
+            for i in range(_TC20_FILLER_RUNS * _TC20_ROWS_PER_FILLER_RUN)
+        ]
+        session.execute(insert(ForwardReturn.__table__), fr_rows)
+        session.commit()
+
+    # Calibration check (not the test's own claim): confirm THIS fixture actually makes a single
+    # uncontended compute genuinely slow on this host -- if it does not, the "fast response" assertion
+    # below would pass VACUOUSLY (true under both the old and new code) rather than as a real proof. Calls
+    # the PURE `compute_forward_aggregates` directly (never the persisting `forward_aggregates_ingest_
+    # cached` wrapper), so this has NO side effect on `ForwardAggregateCache` -- the concurrency test below
+    # still observes a genuine never-before-warmed MISS, exactly as a real first-ever page view would.
+    with Session(engine) as session:
+        t0 = time.monotonic()
+        compute_forward_aggregates(session, heavy_horizon, cfg, as_of=asof)
+        calibration_elapsed = time.monotonic() - t0
+    assert calibration_elapsed >= 1.0, (
+        f"fixture too small for this host to prove non-blocking dispatch — a single uncontended "
+        f"compute_forward_aggregates call took only {calibration_elapsed:.3f}s (need >= 1.0s); "
+        f"bump _TC20_ROWS_PER_FILLER_RUN"
+    )
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
+            t0 = time.monotonic()
+            result = backtest_module.backtest(as_of=asof.isoformat(), session=session)
+            elapsed = time.monotonic() - t0
+            return result, elapsed
+
+    n_callers = 5
+    forward_testing_module.compute_forward_aggregates = _counting
+    try:
+        with ThreadPoolExecutor(max_workers=n_callers) as pool:
+            futures = [pool.submit(_caller) for _ in range(n_callers)]
+            outcomes = [f.result() for f in as_completed(futures, timeout=BOUNDED_TIMEOUT_S)]
+
+        assert len(outcomes) == n_callers, "not every concurrent caller completed — treat as a hang"
+        results = [r for r, _elapsed in outcomes]
+        elapsed_times = [elapsed for _r, elapsed in outcomes]
+        assert all(r["is_latest"] is False for r in results)
+        # the "never blocking" half: every one of the 5 requests returned fast — well under the >=1.0s the
+        # calibration above just proved the compute itself genuinely costs, so none of them waited on it
+        # (the OLD synchronous ensure-loop would have made every one of them take >=1.0s: the owner
+        # computing, the other 4 waiting on the existing inner per-horizon lock).
+        assert max(elapsed_times) < 0.5, (
+            f"expected every concurrent request to return fast (never waiting on the >={calibration_elapsed:.2f}s "
+            f"dispatched compute); slowest was {max(elapsed_times):.3f}s"
+        )
+
+        # Bounded poll for the single dispatched background compute to land, re-triggering a (harmless,
+        # single-flight-guarded) dispatch on each iteration that is not yet ready — see the TC-7 test
+        # below for why this is safe and cannot mask a real duplicate-compute bug.
+        deadline = time.monotonic() + BOUNDED_TIMEOUT_S
+        with Session(engine) as session:
+            final = backtest_module.backtest(as_of=asof.isoformat(), session=session)
+        while final["evidence_status"] != "ready":
+            assert time.monotonic() < deadline, (
+                f"evidence never reached 'ready' within {BOUNDED_TIMEOUT_S}s "
+                f"(last evidence_status={final['evidence_status']!r}) — treat as a hang/regression"
+            )
+            time.sleep(0.02)
+            with Session(engine) as session:
+                final = backtest_module.backtest(as_of=asof.isoformat(), session=session)
+    finally:
+        forward_testing_module.compute_forward_aggregates = real
+
+    assert final["evidence_asof"] == asof.isoformat()
+    assert call_count["n"] == len(cfg.walk_forward.horizons), (
+        f"expected compute_forward_aggregates to run exactly once per configured horizon "
+        f"({len(cfg.walk_forward.horizons)}) across all {n_callers} concurrent first-touch requests; "
+        f"it ran {call_count['n']} times — the outer dispatch guard did not de-duplicate correctly"
+    )
+
+
+def test_iter20_historical_dispatch_owner_failure_releases_guard_and_allows_redispatch(tmp_path):
+    """TC-7 (spec DoD): when the dispatched background compute's OWNER raises before completing (a forced
+    failure, mirroring `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`
+    above), the outer guard is released (never a permanent wedge) so a SUBSEQUENT dispatch for the SAME
+    identity can run, and this date eventually reaches `"ready"` — never a stuck `"not_yet_computed"`."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'tc20_owner_raises.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    asof = date(2023, 2, 1)
+    with Session(engine) as session:
+        _seed_historical_run(session, asof)
+        session.commit()
+
+    real_ingest_cached = forward_testing_module.forward_aggregates_ingest_cached
+    call_count = {"n": 0}
+
+    def _boom_once_then_real(*args, **kwargs):
+        call_count["n"] += 1
+        if call_count["n"] == 1:
+            raise RuntimeError("forced dispatch-owner failure (TC-7 probe)")
+        return real_ingest_cached(*args, **kwargs)
+
+    forward_testing_module.forward_aggregates_ingest_cached = _boom_once_then_real
+    evidence = None
+    try:
+        with Session(engine) as session:
+            forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)
+
+        # Poll: read the evidence, and re-trigger a dispatch whenever it is not yet ready. A re-trigger is
+        # a harmless no-op while a dispatch is still in flight (the outer guard's own single-flight
+        # contract, unchanged) and a genuine re-dispatch the instant the guard clears — so this loop
+        # cannot falsely pass on scheduling luck: it converges to "ready" iff the guard was actually
+        # released after the forced failure, and times out (a real regression -- a permanent wedge) iff
+        # it was not.
+        deadline = time.monotonic() + BOUNDED_TIMEOUT_S
+        while evidence is None or evidence["evidence_status"] != "ready":
+            last_status = evidence["evidence_status"] if evidence is not None else None
+            assert time.monotonic() < deadline, (
+                f"never reached 'ready' within {BOUNDED_TIMEOUT_S}s after the forced owner failure -- "
+                f"treat as a permanent wedge (last evidence_status={last_status!r})"
+            )
+            time.sleep(0.02)
+            with Session(engine) as session:
+                evidence = forward_testing_module.resolved_forward_aggregate_evidence(session, asof, cfg)
+                if evidence["evidence_status"] != "ready":
+                    forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)
+    finally:
+        forward_testing_module.forward_aggregates_ingest_cached = real_ingest_cached
+
+    assert evidence["evidence_status"] == "ready"
+    assert evidence["evidence_asof"] == asof.isoformat()
+    assert call_count["n"] >= 2, (
+        "expected the forced first failure (call 1) AND at least one successful re-dispatch afterward -- "
+        f"got {call_count['n']} total calls"
+    )
diff --git a/apps/backend/tests/test_forward_testing_serving_split.py b/apps/backend/tests/test_forward_testing_serving_split.py
index f5a53dc5..fd6391a6 100644
--- a/apps/backend/tests/test_forward_testing_serving_split.py
+++ b/apps/backend/tests/test_forward_testing_serving_split.py
@@ -36,6 +36,7 @@ from __future__ import annotations
 
 import json
 import logging
+import time
 from datetime import date, datetime, timedelta, timezone
 
 import pytest
@@ -755,11 +756,36 @@ def test_backtest_route_and_mcp_tool_serve_older_evidence_asof_across_boundary(e
     assert api_result["evidence_asof"] == mcp_result["evidence_asof"]
 
 
+def _poll_until_ready(call, timeout: float = 5.0, interval: float = 0.01) -> dict:
+    """ops-hardening iter-20: `call()` (a zero-arg callable re-invoking the route/tool) is polled, bounded,
+    until its `evidence_status` reaches `"ready"`. The historical branch's compute is now DISPATCHED to a
+    background thread rather than awaited on the request thread, so the first call after a dispatch
+    returns an honest interim state — this is what a real page's "reload after a moment" does, and mirrors
+    this test suite's own bounded-wait convention (e.g. `test_forward_testing_concurrency.py`'s
+    `BOUNDED_TIMEOUT_S`). Raises via assertion (never hangs) if `timeout` is exceeded — a genuine
+    regression, not a slow pass, on these small in-memory fixtures."""
+    deadline = time.monotonic() + timeout
+    result = call()
+    while result["evidence_status"] != "ready":
+        assert time.monotonic() < deadline, (
+            f"evidence never reached 'ready' within {timeout}s (last evidence_status="
+            f"{result['evidence_status']!r}) — treat as a hang/regression, not a slow pass"
+        )
+        time.sleep(interval)
+        result = call()
+    return result
+
+
 def test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior(endpoint_engine, monkeypatch):
-    """TC-13: a historical (`is_latest == False`) `?as_of=` request still computes-once-and-caches on
-    first view (UNCHANGED, the explicit carve-out) — a SECOND, older run with no forward-aggregate warm
+    """TC-10/TC-13: a historical (`is_latest == False`) `?as_of=` request still computes-once-and-caches
+    (the explicit carve-out's SUBSTANCE, unchanged) — a SECOND, older run with no forward-aggregate warm
     at all is requested (is_latest is False since a later run exists): a real compute happens once per
-    configured horizon on the FIRST call and NOT AT ALL on the second (cached) call."""
+    configured horizon IN TOTAL, and never again on a later (cached) view.
+
+    ops-hardening iter-20: the compute is now DISPATCHED to a background thread rather than run
+    synchronously on the request thread, so the FIRST call returns an honest INTERIM state immediately
+    (never blocking) — this test waits (bounded) for that dispatched compute to land before asserting the
+    SAME compute-count/byte-identity guarantees this test has always encoded (TC-10)."""
     import app.api.backtest as backtest_module
     import app.engine.forward_testing as ft_module
 
@@ -784,19 +810,31 @@ def test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior(endpoin
         return real(*a, **kw)
 
     monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
-    with Session(engine) as session:
-        first = backtest_module.backtest(as_of=older_asof.isoformat(), session=session)
-    first_calls = call_count["n"]
-    with Session(engine) as session:
-        second = backtest_module.backtest(as_of=older_asof.isoformat(), session=session)
 
+    def _call() -> dict:
+        with Session(engine) as session:
+            return backtest_module.backtest(as_of=older_asof.isoformat(), session=session)
+
+    first = _call()
     assert first["is_latest"] is False
+    # iter-20: the compute is dispatched, never awaited — nothing has EVER been computed anywhere in this
+    # fixture yet, so the honest PRE-dispatch read is "not_yet_computed" (never "ready" on this first call).
+    assert first["evidence_status"] == "not_yet_computed", (
+        "the first view must return immediately with the honest interim state, never block for the "
+        "dispatched background compute"
+    )
+
+    ready = _poll_until_ready(_call)
+    first_calls = call_count["n"]
+    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon, dispatched once"
+    assert ready["is_latest"] is False
+    assert ready["evidence_status"] == "ready"
+    assert ready["evidence_asof"] == older_asof.isoformat()
+
+    second = _call()
     assert second["is_latest"] is False
-    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon on first view"
-    assert call_count["n"] == first_calls, "the second (cached) view must trigger zero MORE computes"
-    assert first["evidence_status"] == "ready"
-    assert first["evidence_asof"] == older_asof.isoformat()
-    assert second["evidence_by_horizon"] == first["evidence_by_horizon"]
+    assert call_count["n"] == first_calls, "the cached (ready) view must trigger zero MORE computes"
+    assert second["evidence_by_horizon"] == ready["evidence_by_horizon"]
 
 
 def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists(
@@ -804,11 +842,16 @@ def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_e
 ):
     """iter-17 TC-6 (regression guard, mirrors `test_historical_asof_keeps_pre_iter16_create_once_and_
     cache_behavior` above): a historical (`is_latest == False`) `?as_of=` request still computes-once-
-    and-caches ITS OWN evidence on first view, and must NEVER be short-circuited by the iter-17 widened
+    and-caches ITS OWN evidence, and must NEVER be permanently short-circuited by the iter-17 widened
     fallback finding an UNRELATED older `asof_key`'s complete evidence first. `backtest.py`'s audit-B5
     gate is `evidence_status != "ready"` — which `"refreshing"` also satisfies — deliberately NOT
-    `== "not_yet_computed"`, which would wrongly skip the ensure-loop and serve the fallback's stale,
-    wrong-date evidence instead of computing this date's own."""
+    `== "not_yet_computed"`, which would wrongly skip the dispatch and serve the fallback's stale,
+    wrong-date evidence forever instead of ever computing this date's own.
+
+    ops-hardening iter-20: the FIRST call returns the honest PRE-dispatch read (the widened fallback's
+    `"refreshing"` at `fallback_asof`) immediately, while the SAME call's dispatch computes this date's
+    OWN evidence in the background — this test waits (bounded) for that to land, then re-confirms the SAME
+    "never permanently short-circuited, never re-computed" guarantees TC-6/TC-10 have always encoded."""
     import app.api.backtest as backtest_module
     import app.engine.forward_testing as ft_module
 
@@ -830,7 +873,7 @@ def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_e
     # the requested historical date: strictly AFTER fallback_asof (so the widened fallback lands on it)
     # and strictly BEFORE the fixture's own latest date (so is_latest stays False); its own
     # forward-aggregate cache is EMPTY, so the resolver's FIRST read must land on "refreshing" via the
-    # widened fallback to fallback_asof, never "ready", before the ensure-loop below ever runs.
+    # widened fallback to fallback_asof, never "ready", before this date's own dispatched compute lands.
     requested_asof = date(2024, 6, 1)
     with Session(engine) as session:
         req_run = _add_run(session, requested_asof, "Risk-off")
@@ -848,22 +891,36 @@ def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_e
         return real(*a, **kw)
 
     monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
-    with Session(engine) as session:
-        first = backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)
-    first_calls = call_count["n"]
-    with Session(engine) as session:
-        second = backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)
 
+    def _call() -> dict:
+        with Session(engine) as session:
+            return backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)
+
+    first = _call()
     assert first["is_latest"] is False
-    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon on first view"
-    assert call_count["n"] == first_calls, "the second (cached) view must trigger zero MORE computes"
-    assert first["evidence_status"] == "ready"
-    assert first["evidence_asof"] == requested_asof.isoformat(), (
-        "the historical view must serve ITS OWN freshly computed evidence, never the fallback's older date"
+    assert first["evidence_status"] == "refreshing", (
+        "the first read must serve the widened cross-asof_key fallback honestly, before this date's own "
+        "dispatched compute lands"
+    )
+    assert first["evidence_asof"] == fallback_asof.isoformat(), (
+        "must not be short-circuited by == 'not_yet_computed' — the != 'ready' gate must still dispatch "
+        "this date's own compute even though the first read already found 'refreshing'"
+    )
+
+    ready = _poll_until_ready(_call)
+    first_calls = call_count["n"]
+    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon, dispatched once"
+    assert ready["evidence_status"] == "ready"
+    assert ready["evidence_asof"] == requested_asof.isoformat(), (
+        "the historical view must eventually serve ITS OWN freshly computed evidence, never stay stuck on "
+        "the fallback's older date"
     )
+
+    second = _call()
+    assert call_count["n"] == first_calls, "the cached (ready) view must trigger zero MORE computes"
     assert second["evidence_status"] == "ready"
     assert second["evidence_asof"] == requested_asof.isoformat()
-    assert second["evidence_by_horizon"] == first["evidence_by_horizon"]
+    assert second["evidence_by_horizon"] == ready["evidence_by_horizon"]
 
 
 # ======================================================================================================
diff --git a/apps/frontend/app/backtest/page.tsx b/apps/frontend/app/backtest/page.tsx
index 8aefcefc..fc0612ba 100644
--- a/apps/frontend/app/backtest/page.tsx
+++ b/apps/frontend/app/backtest/page.tsx
@@ -231,12 +231,22 @@ function BacktestResults({
           ops-hardening iter-16 (J-08): the evidence panel never blocks on a cold recompute — the served
           `evidence_status` (computed server-side, never derived here) honestly discloses whether this is
           the current version (`ready`, unchanged from before), a labeled last-good prior version while a
-          newer one warms (`refreshing`), or a never-warmed store (`not_yet_computed`). */}
+          newer one warms (`refreshing`), or a never-warmed store (`not_yet_computed`).
+          ops-hardening iter-20 (J-06/J-07/J-08, TC-8/TC-9): a HISTORICAL view (`is_latest === false`) of
+          either state below now ALSO means viewing this page itself just triggered a background compute
+          for this date (the new request-triggered dispatch) — distinct from the LATEST view's pre-existing
+          triggers (a version-bump ingest, or a true fresh-install where only backfilling/fetching starts
+          one). `backtest.is_latest` (already fetched, no new field) picks the copy that is actually true
+          for the cause the reader is looking at. */}
       {backtest.evidence_status === "not_yet_computed" ? (
         <EmptyState
           icon={FlaskConical}
           title="Backtest evidence not yet computed"
-          description="No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers it will compute this evidence — no numbers are fabricated in the meantime."
+          description={
+            backtest.is_latest
+              ? "No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers it will compute this evidence — no numbers are fabricated in the meantime."
+              : "No forward-tested evidence exists yet for this date. Viewing this page has started computing it in the background — reload shortly to see it. No numbers are fabricated in the meantime."
+          }
         />
       ) : evidence ? (
         <>
@@ -244,6 +254,7 @@ function BacktestResults({
             <RefreshingEvidenceBanner
               generatedAt={backtest.evidence_generated_at}
               evidenceAsof={backtest.evidence_asof}
+              isLatest={backtest.is_latest}
             />
           ) : null}
           {/* iter-17 audit fix (J-08/AG-3): this section's OWN copy states a factual window claim —
@@ -268,23 +279,32 @@ function BacktestResults({
 // --- Refreshing-evidence disclosure (ops-hardening iter-16, J-08; evidenceAsof added iter-17, J-08 audit
 // B1): a small, calm, factual banner shown ABOVE the still-fully-populated evidence section while the
 // newer dataset version's evidence is not yet complete. The copy states ONLY what the resolver actually
-// knows (the stamp changed; the new version is incomplete; WHICH as-of's evidence this is; and when it
-// was generated) — it must never assert that a warm is currently in flight (a stamp bump from any new
-// ScannerRun/ForwardReturn row leaves this state standing with no warm running) nor promise an automatic
+// knows (WHICH as-of's evidence this is, and when it was generated) — it must never promise an automatic
 // update (this page refetches only on mount / an as-of change / a readiness transition — there is no
 // poll; see the effect deps in BacktestPage). `evidenceAsof` (iter-17) discloses WHICH as-of's evidence is
 // being shown — equal to the page's own resolved date when the resolver served an older *version* of this
-// SAME date, or a genuinely OLDER date when the fallback crossed an as-of boundary (the common shape
-// right after a new latest trading day lands and its ingest warm has not finished, audit B1). Borrows the
-// Card + Loader2 warn-toned LOOK already established by WarmingState/SurvivorshipBanner on this same page
-// — but this is a DISTINCT, request-scoped disclosure (the served evidence's own status) and must NOT
-// wire to useReadiness() (that hook is the boot-time warm-up concept, unrelated to this per-request state).
+// SAME date, or a genuinely OLDER date when the fallback crossed an as-of boundary. Borrows the Card +
+// Loader2 warn-toned LOOK already established by WarmingState/SurvivorshipBanner on this same page — but
+// this is a DISTINCT, request-scoped disclosure (the served evidence's own status) and must NOT wire to
+// useReadiness() (that hook is the boot-time warm-up concept, unrelated to this per-request state).
+//
+// ops-hardening iter-20 (J-06/J-07/J-08, TC-8): `isLatest` (already-fetched `backtest.is_latest`, no new
+// field) picks between TWO genuinely different causes this SAME `"refreshing"` status now covers:
+//   - LATEST view (unchanged since iter-16/17): the cause is ALWAYS a dataset change elsewhere (a new
+//     ingest bumped the version stamp) — the LATEST branch never dispatches anything itself, so "reload
+//     after the next ingest finishes" stays literally true.
+//   - HISTORICAL view (new this iteration): viewing THIS page is what triggered (or re-triggered) this
+//     date's own background compute — no ingest is necessarily involved at all, and "the dataset has
+//     changed" would often be false here (the identity may simply have never been computed before this
+//     view). The copy for this branch names the ACTUAL cause instead.
 function RefreshingEvidenceBanner({
   generatedAt,
   evidenceAsof,
+  isLatest,
 }: {
   generatedAt: string | null;
   evidenceAsof: string | null;
+  isLatest: boolean;
 }) {
   return (
     <Card
@@ -295,12 +315,16 @@ function RefreshingEvidenceBanner({
       <div className="space-y-1">
         <p className="font-medium text-warn">Refreshing — showing the last complete evidence</p>
         <p className="text-text-muted">
-          The dataset has changed since this evidence was generated, and the newer version is not
-          complete yet. The forward-tested evidence below is the last complete version — evidence as of{" "}
+          {isLatest
+            ? "The dataset has changed since this evidence was generated, and the newer version is not complete yet."
+            : "This date's own evidence is being computed in the background (started by viewing this page) and is not complete yet."}{" "}
+          The forward-tested evidence below is the last complete version — evidence as of{" "}
           <span className="num">{formatIsoDate(evidenceAsof)}</span>, generated{" "}
           <span className="num">{formatIsoDateTime(generatedAt)}</span> — no partial or fabricated
-          figures are shown in the meantime. Reload this page after the next ingest finishes to pick up
-          the new version.
+          figures are shown in the meantime.{" "}
+          {isLatest
+            ? "Reload this page after the next ingest finishes to pick up the new version."
+            : "Reload this page shortly to pick up this date's own evidence once the background compute finishes."}
         </p>
       </div>
     </Card>
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-ops-hardening/telemetry.jsonl   | 4 ++++
 runs/goal-session-ops-hardening/trace/.next-step  | 2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl | 3 +++
 3 files changed, 8 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
