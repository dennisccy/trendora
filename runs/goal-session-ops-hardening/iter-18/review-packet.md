# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index f90f1573..416ca308 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -46,6 +46,9 @@ score/bucket/return in the read path.
 """
 from __future__ import annotations
 
+import logging
+import time
+from datetime import datetime, timezone
 from typing import Optional
 
 from fastapi import APIRouter, Depends, Query
@@ -64,6 +67,52 @@ from app.engine.snapshot_serving import resolved_run
 
 router = APIRouter(tags=["backtest"])
 
+# ops-hardening iter-18 -- per-request timing instrumentation (observability only; never a served value,
+# TC-1/TC-2/TC-4/TC-8). `logs/backend.log` is populated by redirecting the uvicorn process's own
+# stdout/stderr (scripts/start-backend.sh); this process's ROOT logger carries NO handler and defaults to
+# WARNING (confirmed by direct inspection), so an otherwise-unconfigured `trendora.*` logger's
+# `.info(...)` calls are silently dropped -- Python's `logging.lastResort` fallback itself only emits
+# WARNING+. Explicitly setting THIS logger's own level to INFO and attaching a plain `StreamHandler`
+# (guarded against double-attachment across repeated imports) makes this module self-sufficient for that
+# without touching main.py's boot sequence or any global logging config (out of scope this iteration,
+# "Do not redo"). `propagate` is left at its default `True` so `caplog`-based tests (TC-4) still observe
+# these records via the root logger, exactly as production emits them via this handler.
+logger = logging.getLogger("trendora.backtest")
+logger.setLevel(logging.INFO)
+if not logger.handlers:
+    logger.addHandler(logging.StreamHandler())
+
+
+def _log_backtest_timing(
+    is_latest: bool,
+    total_ms: float,
+    resolved_run_ms: float,
+    backfill_forward_returns_ms: float,
+    scorecard_ms: float,
+    evidence_ms: float,
+    ensure_loop_ms: Optional[float],
+) -> None:
+    """One INFO-level, key=value structured timing line per `/backtest` request: an ISO-8601 wall-clock
+    timestamp plus the elapsed-ms breakdown the iter-18 spec calls for -- run resolution, the
+    `backfill_run_forward_returns` step, `compute_run_scorecard`, and `resolved_forward_aggregate_
+    evidence`. `ensure_loop_ms` (the historical/non-`is_latest` ensure-loop's `forward_aggregates_
+    ingest_cached` calls plus its re-resolve) is present ONLY when that branch actually ran -- never a
+    fabricated 0 for the `is_latest` request path, which never reaches it. Purely an operational log
+    line for the iter-18/iter-19 latency diagnosis -- never a served/displayed value (Data Contract
+    untouched)."""
+    fields = [
+        f"ts={datetime.now(timezone.utc).isoformat()}",
+        f"is_latest={is_latest}",
+        f"total_ms={total_ms:.2f}",
+        f"resolved_run_ms={resolved_run_ms:.2f}",
+        f"backfill_forward_returns_ms={backfill_forward_returns_ms:.2f}",
+        f"scorecard_ms={scorecard_ms:.2f}",
+        f"evidence_ms={evidence_ms:.2f}",
+    ]
+    if ensure_loop_ms is not None:
+        fields.append(f"ensure_loop_ms={ensure_loop_ms:.2f}")
+    logger.info("backtest_timing %s", " ".join(fields))
+
 
 @router.get("/backtest")
 def backtest(
@@ -75,18 +124,35 @@ def backtest(
     """Serve the per-date forward-test scorecard for the resolved as-of date. `as_of` omitted = the
     latest stored run; a historical date time-travels to that date's immutable snapshot; an invalid
     date raises an explicit 4xx/503 (never a fabricated scorecard). The run's forward returns are
-    populated create-once on first view, then READ; the scorecard recomputes no score/bucket/return."""
+    populated create-once on first view, then READ; the scorecard recomputes no score/bucket/return.
+
+    ops-hardening iter-18: wrapped in per-request, phase-broken-down wall-clock timing instrumentation
+    (`_log_backtest_timing`, TC-1/TC-2/TC-4/TC-8) diagnosing the still-undiagnosed <=1.5s serving-budget
+    breaches (J-06/J-07/J-08) — observability only, the returned payload stays byte-identical (TC-6)."""
+    t_request_start = time.perf_counter()
     cfg: Config = get_config()
+
+    t0 = time.perf_counter()
     run = resolved_run(session, as_of, cfg)          # immutable snapshot (create-once) or explicit 4xx/503
+    resolved_run_ms = (time.perf_counter() - t0) * 1000.0
+
+    t0 = time.perf_counter()
     backfill_run_forward_returns(session, run, cfg)  # create-once: INSERT-only realized forward returns
+    backfill_forward_returns_ms = (time.perf_counter() - t0) * 1000.0
+
+    t0 = time.perf_counter()
     card = compute_run_scorecard(session, run, cfg)  # SINGLE canonical per-date scorecard (reads stored)
+    scorecard_ms = (time.perf_counter() - t0) * 1000.0
+
     # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
     is_latest = run.asof_date == _latest_stored_run_date(session)
     # iter-17 (J-09/J-10) + iter-16 (J-08): the as-of-scoped forward-tested evidence aggregate, ALL
     # configured horizons resolved together in ONE call (never a per-horizon-independent read — the read
     # path can otherwise observe a mixed-dataset_version row set, see the resolver's own docstring) plus
     # the honest `evidence_status` / `evidence_generated_at` / `evidence_asof` disclosure.
+    t0 = time.perf_counter()
     evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+    evidence_ms = (time.perf_counter() - t0) * 1000.0
     # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
     # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
     # for this date, then re-resolve. For the LATEST view this never runs, so this request path never
@@ -100,10 +166,23 @@ def backtest(
     # followed by the SAME resolver re-reading and re-parsing those same rows a second time. Byte-
     # identical either way (still one producer, one serving read): a cold historical date still ensures
     # every horizon is cached (computing any still-missing one) and re-resolves once, exactly as before.
+    #
+    # ops-hardening iter-18: `ensure_loop_ms` times this WHOLE block (the per-horizon
+    # `forward_aggregates_ingest_cached` calls plus the re-resolve) — present in the timing log line ONLY
+    # when this branch actually runs, mirroring exactly when `forward_aggregates_ingest_cached` fires.
+    ensure_loop_ms: Optional[float] = None
     if not is_latest and evidence["evidence_status"] != "ready":
+        t0 = time.perf_counter()
         for h in cfg.walk_forward.horizons:
             forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
         evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+        ensure_loop_ms = (time.perf_counter() - t0) * 1000.0
+
+    total_ms = (time.perf_counter() - t_request_start) * 1000.0
+    _log_backtest_timing(
+        is_latest, total_ms, resolved_run_ms, backfill_forward_returns_ms, scorecard_ms, evidence_ms,
+        ensure_loop_ms,
+    )
     return {
         **card,
         "is_latest": is_latest,
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 03564121..8c1af4dc 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -1231,6 +1231,11 @@ def resolved_forward_aggregate_evidence(
     stamp — collapsing by version alone would risk mixing horizon rows from two different dates into one
     served payload, the same class of bug the per-identity cutover contract above exists to prevent.
 
+    iter-18 (cheap win): the widened fallback's own candidate-selection scan now defers loading
+    `payload_json` until AFTER the winning `(asof_key, dataset_version)` pair is chosen (see the inline
+    comment at that scan below) — an implementation-only change (fewer bytes read for discarded older
+    candidates); the served evidence for a given `as_of` is unchanged (TC-6).
+
     Deferred import (not at module level): mirrors `forward_aggregates_ingest_cached`'s own established
     reason (`research.py` imports FROM this module, so a module-level import back would be circular)."""
     from app.engine.research import _dataset_version  # deferred: avoids a forward_testing<->research cycle
@@ -1283,31 +1288,70 @@ def resolved_forward_aggregate_evidence(
     # partial warm only) — widen the search to STRICTLY OLDER asof_keys (never a later one, AG-5) and
     # serve the most recent one that DOES have a complete version. See the docstring above for why
     # grouping is keyed by (asof_key, dataset_version) rather than dataset_version alone.
+    #
+    # iter-18 (cheap win, TC-5/TC-6): this candidate-selection scan reads ONLY the identifying columns
+    # (asof_key, horizon, dataset_version, created_at) — never `payload_json`. Completeness depends
+    # solely on WHICH horizons a (asof_key, dataset_version) pair has, never on its payload content, so
+    # every OLDER candidate this scan considers except the eventual winner would otherwise have its
+    # payload materialized and discarded for nothing (today ~819 KB across 25 rows, growing ~164 KB per
+    # distinct as-of ever viewed — the iter-17 audit). Once the winning `(asof_key, dataset_version)`
+    # pair is picked below, exactly ONE targeted follow-up query selects `payload_json` filtered to that
+    # pair alone, before `_serve(...)` runs — same query intent, same winner, byte-identical served
+    # evidence (TC-6). Safe from a read-your-own-scan race: both queries run inside the SAME request
+    # session's already-open read transaction (this function issues no `commit()`), and under this app's
+    # WAL journal mode a reader's snapshot is fixed for the life of that transaction regardless of any
+    # concurrent writer elsewhere.
     older_rows = session.exec(
         select(
             ForwardAggregateCache.asof_key, ForwardAggregateCache.horizon,
-            ForwardAggregateCache.dataset_version, ForwardAggregateCache.payload_json,
-            ForwardAggregateCache.created_at,
+            ForwardAggregateCache.dataset_version, ForwardAggregateCache.created_at,
         ).where(ForwardAggregateCache.asof_key < asof_key)
     ).all()
 
     by_key: dict[str, list] = defaultdict(list)
-    for row_key, row_horizon, row_version, payload_json, created_at in older_rows:
-        by_key[row_key].append((row_horizon, row_version, payload_json, created_at))
+    for row_key, row_horizon, row_version, created_at in older_rows:
+        by_key[row_key].append((row_horizon, row_version, created_at))
+
+    def _complete_version_identities(rows) -> dict[str, dict[int, datetime]]:
+        """Identifying-columns-only sibling of `_complete_versions` above (no `payload_json`) — used
+        ONLY by the widened-fallback candidate scan, which must pick a winning identity before it is
+        worth reading any payload at all."""
+        by_version: dict[str, dict[int, datetime]] = defaultdict(dict)
+        for row_horizon, row_version, created_at in rows:
+            by_version[row_version][row_horizon] = created_at
+        return {
+            version: horizon_map
+            for version, horizon_map in by_version.items()
+            if set(horizon_map) >= configured_horizons
+        }
 
     complete_by_key = {
         row_key: versions
         for row_key, rows in by_key.items()
-        if (versions := _complete_versions(rows))
+        if (versions := _complete_version_identities(rows))
     }
 
     if complete_by_key:
         best_key = max(complete_by_key)  # ISO-8601 strings sort chronologically -- the closest older date
         versions_at_best_key = complete_by_key[best_key]
         best_version = max(
-            versions_at_best_key, key=lambda v: max(ca for _p, ca in versions_at_best_key[v].values())
+            versions_at_best_key, key=lambda v: max(versions_at_best_key[v].values())
         )
-        return _serve(versions_at_best_key[best_version], "refreshing", best_key)
+        # the ONE targeted follow-up: payload_json for the winning (asof_key, dataset_version) pair only.
+        winner_rows = session.exec(
+            select(
+                ForwardAggregateCache.horizon, ForwardAggregateCache.dataset_version,
+                ForwardAggregateCache.payload_json, ForwardAggregateCache.created_at,
+            ).where(
+                ForwardAggregateCache.asof_key == best_key,
+                ForwardAggregateCache.dataset_version == best_version,
+            )
+        ).all()
+        winner_horizon_map = {
+            row_horizon: (payload_json, created_at)
+            for row_horizon, _row_version, payload_json, created_at in winner_rows
+        }
+        return _serve(winner_horizon_map, "refreshing", best_key)
 
     return {
         "evidence_status": "not_yet_computed", "evidence_generated_at": None,
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 1ef4dc35..4ecfdceb 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -19,7 +19,9 @@ read-path *create-once* snapshot + forward-return population the matching endpoi
 from __future__ import annotations
 
 import json
-from datetime import date as date_cls
+import logging
+import time
+from datetime import date as date_cls, datetime, timezone
 from typing import Optional
 
 from sqlalchemy import func
@@ -189,6 +191,45 @@ def get_market_phase(
 # ==================================================================================================
 # Backtest — mirror /api/backtest (per-date forward-test scorecard + as-of-scoped evidence aggregate).
 # ==================================================================================================
+# ops-hardening iter-18 -- per-request timing instrumentation mirroring app.api.backtest's own
+# (TC-1/TC-2/TC-3/TC-4/TC-8, observability only, never a served value). This process's ROOT logger
+# carries NO handler and defaults to WARNING (confirmed by direct inspection), so an otherwise-
+# unconfigured `trendora.*` logger's `.info(...)` calls are silently dropped -- explicitly setting THIS
+# logger's own level to INFO and attaching a plain `StreamHandler` (guarded against double-attachment)
+# makes this module self-sufficient for that. `propagate` stays default `True` so `caplog`-based tests
+# still observe these records via the root logger, exactly as production emits them via this handler.
+logger = logging.getLogger("trendora.mcp_backtest")
+logger.setLevel(logging.INFO)
+if not logger.handlers:
+    logger.addHandler(logging.StreamHandler())
+
+
+def _log_query_backtest_timing(
+    is_latest: bool,
+    total_ms: float,
+    resolved_run_ms: float,
+    backfill_forward_returns_ms: float,
+    scorecard_ms: float,
+    evidence_ms: float,
+    ensure_loop_ms: Optional[float],
+) -> None:
+    """Mirrors `app.api.backtest._log_backtest_timing` field-for-field (TC-3: same field names) — one
+    INFO-level, key=value structured timing line per `query_backtest` call. `ensure_loop_ms` is present
+    only when the historical/non-`is_latest` ensure-loop branch ran."""
+    fields = [
+        f"ts={datetime.now(timezone.utc).isoformat()}",
+        f"is_latest={is_latest}",
+        f"total_ms={total_ms:.2f}",
+        f"resolved_run_ms={resolved_run_ms:.2f}",
+        f"backfill_forward_returns_ms={backfill_forward_returns_ms:.2f}",
+        f"scorecard_ms={scorecard_ms:.2f}",
+        f"evidence_ms={evidence_ms:.2f}",
+    ]
+    if ensure_loop_ms is not None:
+        fields.append(f"ensure_loop_ms={ensure_loop_ms:.2f}")
+    logger.info("query_backtest_timing %s", " ".join(fields))
+
+
 def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     """`GET /api/backtest` — the per-date forward-test scorecard (cohort return + excess vs SPY/QQQ/
     sector + the control cohorts, each with sample size `n`) plus the as-of-scoped `evidence_by_horizon`
@@ -206,21 +247,47 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     fallback (the new `evidence_asof` field discloses which as-of's evidence is actually served) and its
     B5 gate — the historical ensure-loop below runs ONLY when the resolver's first read is not already
     `"ready"`, never unconditionally, avoiding a redundant per-horizon cache-hit read+deserialize
-    immediately followed by the same resolver re-reading those same rows."""
+    immediately followed by the same resolver re-reading those same rows.
+
+    ops-hardening iter-18: wrapped in per-request, phase-broken-down wall-clock timing instrumentation
+    (`_log_query_backtest_timing`) mirroring `app.api.backtest.backtest`'s own — observability only, the
+    returned payload stays byte-identical (TC-6)."""
+    t_request_start = time.perf_counter()
     cfg = get_config()
+
+    t0 = time.perf_counter()
     run = resolved_run(session, asof, cfg)
+    resolved_run_ms = (time.perf_counter() - t0) * 1000.0
+
+    t0 = time.perf_counter()
     backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
+    backfill_forward_returns_ms = (time.perf_counter() - t0) * 1000.0
+
+    t0 = time.perf_counter()
     card = compute_run_scorecard(session, run, cfg)
+    scorecard_ms = (time.perf_counter() - t0) * 1000.0
+
     is_latest = run.asof_date == _latest_stored_run_date(session)
     # ops-hardening iter-5 (J-06) + iter-16 (J-08) + iter-17 (J-08/B1): served from the SAME read-only
     # resolver `GET /api/backtest` now uses (this function's own docstring says it "mirrors the endpoint
     # exactly" — kept true for the compute-vs-serve split AND its iter-17 widened fallback; byte-identical
     # output, `compute_forward_aggregates` itself is unchanged).
+    t0 = time.perf_counter()
     evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+    evidence_ms = (time.perf_counter() - t0) * 1000.0
+    ensure_loop_ms: Optional[float] = None
     if not is_latest and evidence["evidence_status"] != "ready":
+        t0 = time.perf_counter()
         for h in cfg.walk_forward.horizons:
             forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
         evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+        ensure_loop_ms = (time.perf_counter() - t0) * 1000.0
+
+    total_ms = (time.perf_counter() - t_request_start) * 1000.0
+    _log_query_backtest_timing(
+        is_latest, total_ms, resolved_run_ms, backfill_forward_returns_ms, scorecard_ms, evidence_ms,
+        ensure_loop_ms,
+    )
     return {
         **card,
         "is_latest": is_latest,
diff --git a/apps/backend/tests/test_forward_testing_serving_split.py b/apps/backend/tests/test_forward_testing_serving_split.py
index 714142a6..4161f54c 100644
--- a/apps/backend/tests/test_forward_testing_serving_split.py
+++ b/apps/backend/tests/test_forward_testing_serving_split.py
@@ -35,6 +35,7 @@ exercise this path (the identity resolved never changes, only the dataset stamp
 from __future__ import annotations
 
 import json
+import logging
 from datetime import date, datetime, timezone
 
 import pytest
@@ -461,6 +462,94 @@ def test_evidence_fallback_never_reads_a_row_dated_after_the_requested_as_of(evi
     )
 
 
+# ======================================================================================================
+# iter-18 (cheap win, TC-5/TC-6) — the widened fallback's candidate-selection scan defers `payload_json`
+# to a single winner-only follow-up query. SQL-inspected via the SAME `before_cursor_execute` technique
+# `test_completeness_query_is_filtered_by_asof_key` (TC-18) and
+# `test_evidence_fallback_never_reads_a_row_dated_after_the_requested_as_of` (iter-17 TC-5) already use.
+# ======================================================================================================
+def test_widened_fallback_defers_payload_json_to_a_single_winner_only_query(evidence_engine):
+    """iter-18 TC-5/TC-6: with SEVERAL older `(asof_key, dataset_version)` candidates and exactly ONE
+    complete, the widened fallback's initial candidate-selection scan (the `<`-filtered query) never
+    names `payload_json`; exactly ONE follow-up query, filtered to the winning `(asof_key,
+    dataset_version)` pair, selects it. Served evidence is byte-identical to the pre-iter-18 single-query
+    shape (TC-6, a regression guard mirroring `test_evidence_crosses_asof_key_boundary_when_newer_key_
+    has_zero_rows`'s own assertions) — same fixture pattern as that test, extended with two further
+    INCOMPLETE older candidates so "several ... exactly one complete" is genuinely exercised."""
+    engine, complete_asof = evidence_engine  # 2025-01-10 -- becomes the one COMPLETE older candidate
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=complete_asof)
+        session.commit()
+        complete_rows = {
+            row.horizon: (row.payload_json, row.created_at)
+            for row in session.exec(
+                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == complete_asof.isoformat())
+            ).all()
+        }
+        assert set(complete_rows) == set(HORIZONS)
+
+        # two further OLDER candidates, each genuinely INCOMPLETE (2-of-5 horizons only) -- "several"
+        # candidates get scanned, but neither can ever win, so their payload is never needed.
+        for i, partial_asof in enumerate((date(2025, 1, 2), date(2025, 1, 5))):
+            prun = _add_run(session, partial_asof, "Risk-on")
+            _add_result(session, prun.id, f"PP{i}")
+            _add_fr_every_horizon(session, prun.id, partial_asof, f"PP{i}", ret=0.01)
+            session.commit()
+            for h in HORIZONS[:2]:
+                forward_aggregates_ingest_cached(session, h, cfg, as_of=partial_asof)
+            session.commit()
+
+        # the requested identity: a genuinely later run, zero forward-aggregate rows of its own -- so
+        # the widened fallback runs.
+        requested_asof = date(2025, 1, 13)
+        req_run = _add_run(session, requested_asof, "Risk-off")
+        _add_result(session, req_run.id, "REQ")
+        _add_fr_every_horizon(session, req_run.id, requested_asof, "REQ", ret=0.05)
+        session.commit()
+
+        captured: list[str] = []
+
+        def _capture(conn, cursor, statement, parameters, context, executemany):
+            captured.append(statement)
+
+        event.listen(engine, "before_cursor_execute", _capture)
+        try:
+            evidence = resolved_forward_aggregate_evidence(session, requested_asof, cfg)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture)
+
+    # TC-6: byte-identical served evidence (never mixed, never re-derived).
+    assert evidence["evidence_status"] == "refreshing"
+    assert evidence["evidence_asof"] == complete_asof.isoformat()
+    assert set(evidence["evidence_by_horizon"]) == set(HORIZONS)
+    for h in HORIZONS:
+        assert evidence["evidence_by_horizon"][h] == json.loads(complete_rows[h][0]), (
+            f"horizon {h} did not come from the winning candidate's own stored rows"
+        )
+
+    # TC-5: the query-shape assertion — the widened candidate scan never selects payload_json; exactly
+    # one exact-match follow-up query (asof_key AND dataset_version, never a `<` range) does.
+    cache_selects = [
+        stmt for stmt in captured
+        if "forward_aggregate_cache" in stmt.lower() and stmt.strip().lower().startswith("select")
+    ]
+    widened_scan_selects = [stmt for stmt in cache_selects if "<" in stmt]
+    assert widened_scan_selects, "expected the widened fallback's candidate-selection scan to run"
+    assert all("payload_json" not in stmt.lower() for stmt in widened_scan_selects), (
+        f"the widened candidate-selection scan must not select payload_json: {widened_scan_selects}"
+    )
+    # `dataset_version = ?` (a comparison, not merely a selected column) is what distinguishes the
+    # winner-only query from the pre-existing same-key query at the top of the function, which ALSO
+    # selects `payload_json` + `dataset_version` as columns but never filters ON `dataset_version`.
+    winner_selects = [stmt for stmt in cache_selects if "payload_json" in stmt.lower() and "dataset_version = ?" in stmt.lower()]
+    assert len(winner_selects) == 1, (
+        f"expected exactly one winner-only payload_json follow-up query; got {len(winner_selects)}: {winner_selects}"
+    )
+    assert "<" not in winner_selects[0], "the winner-only follow-up must be an exact-match filter, not a range scan"
+
+
 # ======================================================================================================
 # Request-serving entry points (app.api.backtest.backtest, app.mcp.tools.query_backtest) — called
 # directly as plain functions (no TestClient/`loaded_engine` app boot) to prove the WIRING: the
@@ -512,9 +601,13 @@ def test_backtest_route_is_latest_never_reaches_ingest_or_compute(endpoint_engin
     assert set(first) == set(HORIZONS)
 
 
-def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine, monkeypatch):
-    """TC-6/TC-8 (endpoint layer): a never-warmed store still answers (no exception, no fabricated
-    evidence) with the honest empty state — and never calls the ingest/compute function."""
+def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine, monkeypatch, caplog):
+    """TC-6/TC-8 (endpoint layer, iter-16 numbering): a never-warmed store still answers (no exception,
+    no fabricated evidence) with the honest empty state — and never calls the ingest/compute function.
+
+    iter-18 TC-8 (added to this SAME test, its own separate numbering): instrumentation must never turn
+    this honest-empty-state path into a 500 or silently skip logging on it — a timing log line is still
+    emitted for the request."""
     import app.api.backtest as backtest_module
 
     engine, asof = endpoint_engine
@@ -523,6 +616,7 @@ def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine
         raise AssertionError("the is_latest read path must never call the ingest/compute function")
 
     monkeypatch.setattr(backtest_module, "forward_aggregates_ingest_cached", _boom)
+    caplog.set_level(logging.INFO, logger="trendora.backtest")
     with Session(engine) as session:
         result = backtest_module.backtest(as_of=None, session=session)
 
@@ -532,6 +626,14 @@ def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine
     assert result["evidence_generated_at"] is None
     assert result["evidence_asof"] is None
 
+    # iter-18 TC-8: the honest empty state still emits a timing log line (never silently skipped).
+    timing_records = [
+        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
+    ]
+    assert len(timing_records) == 1, (
+        f"expected a timing log line even for the not_yet_computed empty state; got {len(timing_records)}"
+    )
+
 
 def test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute(endpoint_engine, monkeypatch):
     """TC-2/TC-7 (MCP layer): mirrors the endpoint-layer proof above for the MCP `query_backtest` tool —
@@ -609,6 +711,48 @@ def test_backtest_route_and_mcp_tool_serve_evidence_asof_identically(endpoint_en
     assert api_result["evidence_asof"] == mcp_result["evidence_asof"]
 
 
+def test_backtest_route_and_mcp_tool_serve_older_evidence_asof_across_boundary(endpoint_engine):
+    """iter-18 TC-7: the ONE missing endpoint-level test for the iter-17 widened cross-`asof_key`
+    fallback — an OLDER `evidence_asof` survives end-to-end through BOTH `GET /api/backtest`'s route
+    function and the MCP `query_backtest` tool (today's cross-boundary coverage is resolver-level only —
+    every existing test exercising this shape calls `resolved_forward_aggregate_evidence` directly).
+    Mirrors `test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows`'s fixture shape,
+    calling the endpoint functions the way `test_backtest_route_and_mcp_tool_serve_evidence_asof_
+    identically` (directly above) does."""
+    import app.api.backtest as backtest_module
+    import app.mcp.tools as tools_module
+
+    engine, older_asof = endpoint_engine  # 2025-01-10, already has a DailyPrice bar for "AAA"
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=older_asof)
+        session.commit()
+
+        # a genuinely LATER run — the LATEST as-of identity itself, with zero forward-aggregate rows of
+        # its own (the common single-latest-date-backfill shape the iter-17 fix targets).
+        newer_asof = date(2025, 1, 13)
+        run2 = _add_run(session, newer_asof, "Risk-off")
+        _add_result(session, run2.id, "BBB")
+        session.add(DailyPrice(
+            symbol="BBB", date=newer_asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+        ))
+        session.commit()
+
+    with Session(engine) as session:
+        api_result = backtest_module.backtest(as_of=None, session=session)
+    with Session(engine) as session:
+        mcp_result = tools_module.query_backtest(session, asof=None)
+
+    assert api_result["is_latest"] is True
+    assert mcp_result["is_latest"] is True
+    assert api_result["evidence_status"] == "refreshing"
+    assert mcp_result["evidence_status"] == "refreshing"
+    assert api_result["evidence_asof"] == older_asof.isoformat()
+    assert mcp_result["evidence_asof"] == older_asof.isoformat()
+    assert api_result["evidence_asof"] == mcp_result["evidence_asof"]
+
+
 def test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior(endpoint_engine, monkeypatch):
     """TC-13: a historical (`is_latest == False`) `?as_of=` request still computes-once-and-caches on
     first view (UNCHANGED, the explicit carve-out) — a SECOND, older run with no forward-aggregate warm
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-index.html      |  13 +-
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 runs/goal-session-ops-hardening/session.json       |   8 +-
 .../state/assumptions.md                           | 133 --------------------
 .../state/assumptions.md.archive.md                | 136 +++++++++++++++++++++
 runs/goal-session-ops-hardening/state/blueprint.md |  31 ++++-
 runs/goal-session-ops-hardening/state/lessons.md   |  70 +----------
 .../state/lessons.md.archive.md                    |  87 +++++++++++++
 .../state/project-story.md                         |  12 +-
 runs/goal-session-ops-hardening/summary.md         |  52 +++++---
 runs/goal-session-ops-hardening/telemetry.jsonl    |  20 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   3 +
 15 files changed, 342 insertions(+), 231 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
