# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_forward_testing_serving_split.py` (134 lines not shown)

```diff
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index 416ca308..bab9c19f 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -91,15 +91,20 @@ def _log_backtest_timing(
     scorecard_ms: float,
     evidence_ms: float,
     ensure_loop_ms: Optional[float],
+    write_taken: bool,
 ) -> None:
     """One INFO-level, key=value structured timing line per `/backtest` request: an ISO-8601 wall-clock
     timestamp plus the elapsed-ms breakdown the iter-18 spec calls for -- run resolution, the
     `backfill_run_forward_returns` step, `compute_run_scorecard`, and `resolved_forward_aggregate_
     evidence`. `ensure_loop_ms` (the historical/non-`is_latest` ensure-loop's `forward_aggregates_
     ingest_cached` calls plus its re-resolve) is present ONLY when that branch actually ran -- never a
-    fabricated 0 for the `is_latest` request path, which never reaches it. Purely an operational log
-    line for the iter-18/iter-19 latency diagnosis -- never a served/displayed value (Data Contract
-    untouched)."""
+    fabricated 0 for the `is_latest` request path, which never reaches it. `write_taken` (iter-19,
+    J-06/J-07/J-08) records whether `backfill_run_forward_returns`'s create-once write was actually
+    committed this request (`True`, the genuinely-missing case) or skipped entirely because every row
+    already existed (`False`, the new zero-write guard's common warm-path outcome) -- appended LAST so
+    the pre-existing field positions/regex this line's own consumers already rely on are undisturbed.
+    Purely an operational log line for the iter-18/iter-19 latency diagnosis -- never a served/displayed
+    value (Data Contract untouched)."""
     fields = [
         f"ts={datetime.now(timezone.utc).isoformat()}",
         f"is_latest={is_latest}",
@@ -111,6 +116,7 @@ def _log_backtest_timing(
     ]
     if ensure_loop_ms is not None:
         fields.append(f"ensure_loop_ms={ensure_loop_ms:.2f}")
+    fields.append(f"write_taken={write_taken}")
     logger.info("backtest_timing %s", " ".join(fields))
 
 
@@ -137,8 +143,14 @@ def backtest(
     resolved_run_ms = (time.perf_counter() - t0) * 1000.0
 
     t0 = time.perf_counter()
-    backfill_run_forward_returns(session, run, cfg)  # create-once: INSERT-only realized forward returns
+    # create-once: INSERT-only realized forward returns. ops-hardening iter-19: the return value is
+    # captured ONLY to read `rows_inserted` (already computed by the function's own idempotency check,
+    # no new query) for the timing log's `write_taken` field below -- the call itself is unchanged:
+    # same function, same arguments, unconditional, no caller-side guard (single-producer discipline;
+    # the skip-vs-take decision lives entirely inside `backfill_run_forward_returns`).
+    backfill_result = backfill_run_forward_returns(session, run, cfg)
     backfill_forward_returns_ms = (time.perf_counter() - t0) * 1000.0
+    write_taken = backfill_result["rows_inserted"] > 0
 
     t0 = time.perf_counter()
     card = compute_run_scorecard(session, run, cfg)  # SINGLE canonical per-date scorecard (reads stored)
@@ -181,7 +193,7 @@ def backtest(
     total_ms = (time.perf_counter() - t_request_start) * 1000.0
     _log_backtest_timing(
         is_latest, total_ms, resolved_run_ms, backfill_forward_returns_ms, scorecard_ms, evidence_ms,
-        ensure_loop_ms,
+        ensure_loop_ms, write_taken,
     )
     return {
         **card,
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 8c1af4dc..f8ec95b8 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -50,7 +50,14 @@ from app.config import Config, get_config
 from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.engine.setups import ALL_STATUSES
-from app.models import EventStudyCache, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
+from app.models import (
+    DailyPrice,
+    EventStudyCache,
+    ForwardAggregateCache,
+    ForwardReturn,
+    ScannerResult,
+    ScannerRun,
+)
 
 # The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). iter-18: the
 # basis now spans ~30 years (1996 -> present, per-name real listing depth) over the broadened
@@ -1370,7 +1377,53 @@ def backfill_run_forward_returns(
     forward-return formula). INSERT-only + idempotent — a 2nd call inserts 0 rows and it never UPDATEs
     a `scanner_runs` / `scanner_results` / `*_scores` row (anti-goal: Snapshots immutable). Frozen-seed-
     only. This is the "first view computes once" path the No-recompute-in-the-read-path anti-goal
-    explicitly permits; for a run the iter-6 boot backfill already covered it inserts nothing."""
+    explicitly permits; for a run the iter-6 boot backfill already covered it inserts nothing.
+
+    ops-hardening iter-19 (J-06/J-07/J-08, the shared `/backtest` latency blocker) — THREE cooperating
+    changes make the WARM request (a run whose forward returns are already fully backfilled — the common
+    shape, since the ingest finalize path `data_manager.py` `_persist` backfills every run at creation)
+    do negligible work:
+      1. UN-ELAPSED HORIZONS ARE SHORT-CIRCUITED GLOBALLY — the change that actually collapses the phase
+         (attempts 1-2 left it at ~877ms). A horizon h is only realizable once at least h trading days
+         exist AFTER the run's as-of date D. The DEFAULT `/backtest` resolves to the LATEST run
+         (asof == the data end, 0 elapsed days), so its longer horizons can NEVER produce a row for ANY
+         symbol — yet the prior code still re-attempted a `close_on`+`bars_after` price-fetch PAIR per
+         (symbol, un-elapsed-horizon) on EVERY request (~545 symbols × 2 queries ≈ 1090 wasted queries,
+         ~115ms single / ~877ms of the request under 6× concurrency — the actual 82% cost the reviewer
+         pinned live). We now count ONCE, before the per-symbol loop, how many post-D trading days are
+         observable (`observable_days` = distinct `daily_prices.date > D`, bounded to max(horizons) via
+         the `ix_daily_prices_date` covering index — this IS the module's trading calendar, the same
+         calendar `walk_forward_asof_dates` reads off the benchmark; counting distinct DATES is
+         benchmark-symbol-agnostic, so it equals SPY's post-D bar count wherever SPY defines the calendar
+         yet is still correct on a seed/fixture that never populated SPY) and pass only
+         `[h for h in horizons if h <= observable_days]` into `_insert_run_forward_returns`. For the
+         latest run `observable_days == 0` → no horizons → every symbol's `needed` list is empty → the
+         per-symbol loop short-circuits with ZERO price fetches, collapsing the phase to the ~3ms an
+         already-elapsed run pays. Byte-identical by construction (AG-3): h > observable_days means fewer
+         than h post-D bars exist on the shared calendar for every symbol, so `forward_return`'s
+         `len(post_bars) < horizon` NA gate already stored nothing for that (symbol, h) — pre-filtering
+         matches the per-symbol NA gate exactly, every horizon, with/without `as_of`. No-lookahead
+         preserved (AG-5): only already-stored bars with date > D are counted, never a future/synthesized
+         bar. Bounded to ≤ max(horizons) index rows, no whole-table scan (AG-8).
+      2. The idempotency existence read is COLUMN-PROJECTED (`select(ForwardReturn.symbol, .horizon)`),
+         never a full-row `select(ForwardReturn)` materialization — retained (a correct ~0.06ms
+         covering-index read), but it was NOT the latency driver: attempts 1-2 stayed at ~877ms because
+         the real cost was the per-symbol fetches that change 1 eliminates, not this read.
+      3. `_commit_forward_returns_concurrency_safe` (and its `session.commit()`) is skipped when
+         `_insert_run_forward_returns` stages nothing (`inserted == 0`) — so a warm request acquires no
+         SQLite write lock. Retained; correct but never the bottleneck on its own.
+    The genuinely-missing ELAPSED case (`inserted > 0` — a horizon that IS observable but not yet stored)
+    is UNCHANGED: it still inserts synchronously and commits — idempotent, INSERT-only, race-tolerant via
+    the unchanged `_commit_forward_returns_concurrency_safe`. Proven zero-write by SQL-inspection
+    (TC-1/TC-2), completeness-preserving under a partial backfill
+    (`test_iter19_partial_backfill_run_is_detected_incomplete_and_completed`), horizon short-circuit
+    correct + byte-identical to the unfiltered path by
+    `test_iter19_latest_run_unelapsed_horizons_short_circuit_no_price_fetches`,
+    `test_iter19_partially_elapsed_run_processes_only_elapsed_horizons_byte_identical`, and
+    `test_iter19_fully_elapsed_run_processes_all_horizons_unaffected`; byte-identical served payload
+    (TC-5, `test_forward_testing_serving_split.py`), and race-safe under concurrent genuinely-missing
+    callers (TC-4, `test_forward_testing_concurrency.py`) — see the iter-19 dev handoff for the live TC-6
+    re-measurement."""
     cfg = config or get_config()
     wf = cfg.walk_forward
     horizons = wf.horizons
@@ -1378,12 +1431,57 @@ def backfill_run_forward_returns(
     # J-93: this run's OWN resolved membership ∪ benchmarks (its stored ScannerResult tickers — single
     # source), not the global universe list. A name absent from the run's snapshot stores no return (n=0).
     symbols = forward_symbols_for_run(session, run, cfg)
+    # iter-19 (J-06/J-07/J-08, the PROVEN TC-6 latency fix): before the per-symbol loop, count ONCE how
+    # many trading days are actually OBSERVABLE after this run's as-of date D. A horizon h can only ever
+    # produce a row when >= h post-D bars exist; the per-symbol loop below otherwise pays a wasted
+    # `close_on`+`bars_after` fetch pair for every (symbol, un-elapsed-horizon) even though `forward_return`'s
+    # NA gate will store nothing (~545 symbols x 2 queries on the default latest-run `/backtest`). We measure
+    # the module's trading calendar as the distinct `daily_prices.date > D` count, bounded to max_h through
+    # the `ix_daily_prices_date` covering index (<=0.5ms even at the 30y basis floor; 0 rows / instant for the
+    # latest run) — a whole-calendar count, not a per-symbol scan (AG-8), reading only already-stored bars
+    # with date > D (no lookahead, AG-5). Counting distinct DATES (not one benchmark symbol's bars) equals
+    # SPY's post-D bar count wherever SPY defines the calendar but is ALSO correct on a seed/fixture that
+    # never populated SPY. Filtering out every horizon h > observable_days is byte-identical to the
+    # per-symbol NA gate (h > observable_days => < h post-D bars for EVERY symbol => forward_return None),
+    # so for the latest run observable_horizons is empty, every `needed` list is empty, and the per-symbol
+    # loop short-circuits with ZERO price fetches — collapsing the ~115ms (877ms under 6x concurrency) phase
+    # to the ~3ms floor an already-elapsed run pays.
+    observable_days = len(
+        session.exec(
+            select(DailyPrice.date)
+            .where(DailyPrice.date > run.asof_date)
+            .distinct()
+            .order_by(DailyPrice.date)
+            .limit(max_h)
+        ).all()
+    )
+    observable_horizons = [h for h in horizons if h <= observable_days]
+    # iter-19 (retained micro-optimization, NOT the latency driver): COLUMN-PROJECT the idempotency key set
+    # instead of materializing every full `ForwardReturn` ORM row for the run. Attempt-2 introduced this to
+    # avoid hydrating one full ORM object per stored (symbol, horizon) just to read three key columns; it is
+    # a correct ~0.06ms covering-index read, but the reviewer's live EXPLAIN/re-measurement showed it did
+    # NOT move the phase (attempts 1-2 stayed at ~877ms) — the real cost was the per-symbol price fetches for
+    # un-elapsed horizons, now eliminated by the observable_horizons short-circuit above. Kept because it is
+    # strictly cheaper and correct. The projected `(symbol, horizon)` Row values are the EXACT same plain
+    # `(str, int)` tuples ORM attribute access returns, so `existing` is byte-identical to the prior set and
+    # the create-once/idempotent completeness semantics are UNCHANGED (`_insert_run_forward_returns` still
+    # detects and fills any genuinely-missing ELAPSED key at the (symbol, horizon) grain). `run_id` is
+    # constant (= run.id) for this run-filtered read. Bounded to ONE run's own rows (symbols x horizons;
+    # deeper history adds runs, not rows-per-run), never a whole-table load (AG-8). Mirrors the module's own
+    # `_streamed_existing_keys` projection idiom.
     existing = {
-        (fr.run_id, fr.symbol, fr.horizon)
-        for fr in session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()
+        (run.id, symbol, horizon)
+        for symbol, horizon in session.exec(
+            select(ForwardReturn.symbol, ForwardReturn.horizon).where(ForwardReturn.run_id == run.id)
+        ).all()
     }
-    inserted = _insert_run_forward_returns(session, run, symbols, horizons, max_h, existing)
-    _commit_forward_returns_concurrency_safe(session)  # iter-28 (J-41): tolerate a concurrent INSERT race
+    # Pass ONLY the elapsed/observable horizons: an un-elapsed horizon (h > observable_days) can produce no
+    # row for any symbol, so skipping it here is byte-identical to the per-symbol NA gate but avoids the
+    # per-symbol price fetches it would otherwise trigger. max_h (the full-set max) stays as the bars_after
+    # limit — only reached when a symbol genuinely needs an elapsed horizon, and identical to before.
+    inserted = _insert_run_forward_returns(session, run, symbols, observable_horizons, max_h, existing)
+    if inserted:
+        _commit_forward_returns_concurrency_safe(session)  # iter-28 (J-41): tolerate a concurrent INSERT race
     return {"run_id": run.id, "asof_date": run.asof_date.isoformat(), "rows_inserted": inserted}
 
 
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 4ecfdceb..68c054f0 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -212,10 +212,14 @@ def _log_query_backtest_timing(
     scorecard_ms: float,
     evidence_ms: float,
     ensure_loop_ms: Optional[float],
+    write_taken: bool,
 ) -> None:
     """Mirrors `app.api.backtest._log_backtest_timing` field-for-field (TC-3: same field names) — one
     INFO-level, key=value structured timing line per `query_backtest` call. `ensure_loop_ms` is present
-    only when the historical/non-`is_latest` ensure-loop branch ran."""
+    only when the historical/non-`is_latest` ensure-loop branch ran. `write_taken` (iter-19, J-06/J-07/
+    J-08) mirrors the API route's own field: whether `backfill_run_forward_returns`'s create-once write
+    was committed (`True`) or skipped because every row already existed (`False`) -- appended LAST so
+    existing field positions are undisturbed."""
     fields = [
         f"ts={datetime.now(timezone.utc).isoformat()}",
         f"is_latest={is_latest}",
@@ -227,6 +231,7 @@ def _log_query_backtest_timing(
     ]
     if ensure_loop_ms is not None:
         fields.append(f"ensure_loop_ms={ensure_loop_ms:.2f}")
+    fields.append(f"write_taken={write_taken}")
     logger.info("query_backtest_timing %s", " ".join(fields))
 
 
@@ -260,8 +265,12 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     resolved_run_ms = (time.perf_counter() - t0) * 1000.0
 
     t0 = time.perf_counter()
-    backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
+    # create-once realized forward returns (as the endpoint does). ops-hardening iter-19: the return
+    # value is captured ONLY to read `rows_inserted` for the timing log's `write_taken` field below --
+    # the call itself is unchanged (same function, same arguments, unconditional).
+    backfill_result = backfill_run_forward_returns(session, run, cfg)
     backfill_forward_returns_ms = (time.perf_counter() - t0) * 1000.0
+    write_taken = backfill_result["rows_inserted"] > 0
 
     t0 = time.perf_counter()
     card = compute_run_scorecard(session, run, cfg)
@@ -286,7 +295,7 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     total_ms = (time.perf_counter() - t_request_start) * 1000.0
     _log_query_backtest_timing(
         is_latest, total_ms, resolved_run_ms, backfill_forward_returns_ms, scorecard_ms, evidence_ms,
-        ensure_loop_ms,
+        ensure_loop_ms, write_taken,
     )
     return {
         **card,
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
index 858dba76..8fa56470 100644
--- a/apps/backend/tests/test_forward_testing_concurrency.py
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -53,6 +53,7 @@ from pathlib import Path
 
 import pytest
 from sqlalchemy import insert
+from sqlalchemy.exc import IntegrityError
 from sqlmodel import Session, select
 
 from app.config import load_config
@@ -536,3 +537,145 @@ def test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_ra
         with Session(engine) as session:
             direct = real(session, HORIZON, cfg, as_of=as_of)
         assert waiter_result["payload"] == direct, "waiter's fallback payload was not byte-identical"
+
+
+# ======================================================================================================
+# ops-hardening iter-19 (J-06/J-07/J-08) TC-4 — concurrency-race safety for `backfill_run_forward_
+# returns`'s NEW zero-write guard (forward_testing.py ~line 1365, added this iteration). This is a
+# DISTINCT fixture/mechanism from every test group above: those all exercise `compute_forward_aggregates`
+# / `forward_aggregates_ingest_cached` (the `forward_aggregate_cache` table). The test below exercises
+# `backfill_run_forward_returns` (the SEPARATE, append-only `forward_returns` table), reached only via
+# `GET /api/backtest`'s create-once population step (~line 140) — a different function, a different
+# table, a different request-path mechanism entirely.
+# ======================================================================================================
+def test_iter19_concurrent_missing_run_backtest_calls_no_duplicate_rows_and_rollback_path_exercised(
+    tmp_path,
+):
+    """iter-19 TC-4 (mandatory concurrency test, spec DoD): 5 concurrent `GET /api/backtest` calls for
+    the SAME as-of whose forward returns are genuinely missing at request time. A `threading.Barrier`
+    forces all 5 threads to finish their OWN pre-insert idempotency read (the `existing` SELECT inside
+    `backfill_run_forward_returns`, immediately before it calls `_insert_run_forward_returns`) before ANY
+    of them proceeds to stage or flush a single write — guaranteeing every caller's `existing` read saw
+    the SAME empty state for the one genuinely-missing symbol, so all N stage the SAME rows and race at
+    commit time, deterministically reproducing the concurrent-INSERT race
+    `_commit_forward_returns_concurrency_safe` exists to absorb (iter-28, J-41) rather than leaving it to
+    scheduling luck. The fixture pre-seeds every OTHER symbol this run would process (the benchmark ETFs
+    `forward_symbols_for_run` always appends) as ALREADY complete, so `_insert_run_forward_returns`'s
+    per-symbol loop `continue`s past every one of them without a further read — isolating the race to the
+    ONE genuinely-missing scored ticker and to the explicit final commit this iteration's guard gates,
+    rather than an unrelated mid-loop SQLAlchemy autoflush (see the dev handoff's Known Issues for that
+    separate, pre-existing finding, out of scope here).
+
+    Asserts: (a) all 5 calls complete with no unhandled exception, (b) `forward_returns` ends with no
+    duplicate `(run_id, symbol, horizon)` key, and (c) the pre-existing `IntegrityError`-tolerant rollback
+    path is ACTUALLY exercised at least once (call-count instrumented — proven by assertion, not merely
+    reachable in theory)."""
+    import app.api.backtest as backtest_module
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'tc4_missing_run.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    horizons = cfg.walk_forward.horizons
+    max_h = max(horizons)
+    asof = date(2025, 3, 1)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        run_id = run.id
+        session.add(ScannerResult(
+            run_id=run_id, ticker="AAA", name="AAA", sector="Technology", leadership_score=50.0,
+            leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
+            risk_bucket="C", setup_status="Actionable", rank=1, record_json="{}", is_vcp=False,
+            is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
+        ))
+        session.add(DailyPrice(
+            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+        ))
+        for i in range(1, max_h + 1):
+            session.add(DailyPrice(
+                symbol="AAA", date=asof + timedelta(days=i), open=100.0, high=101.0, low=99.0,
+                close=100.0 + i, volume=1.0,
+            ))
+        session.flush()
+        # Pre-seed every OTHER symbol this run's own `forward_symbols_for_run` would process (the
+        # benchmark ETFs) as already fully backfilled -- see the docstring above for why.
+        other_symbols = [
+            s for s in forward_testing_module.forward_symbols_for_run(session, run, cfg) if s != "AAA"
+        ]
+        for sym in other_symbols:
+            for h in horizons:
+                session.add(ForwardReturn(
+                    run_id=run_id, symbol=sym, horizon=h, asof_date=asof, entry_close=100.0,
+                    measured_date=asof, realized_return=0.0,
+                ))
+        session.commit()
+
+    n_callers = 5
+    barrier = threading.Barrier(n_callers)
+    real_insert = forward_testing_module._insert_run_forward_returns
+    real_commit_safe = forward_testing_module._commit_forward_returns_concurrency_safe
+    rollback_count = {"n": 0}
+
+    def _synced_insert(*args, **kwargs):
+        """Blocks every caller at a barrier BEFORE staging/flushing a single write (all 5 have already
+        completed their OWN pre-insert `existing` read, taken by the unpatched caller just before this),
+        then calls the real idempotency-check-and-insert step -- guaranteeing every caller saw the SAME
+        empty state for the missing symbol and all N stage the SAME rows, so the race lands at the
+        explicit commit below rather than resolving silently via natural scheduling."""
+        barrier.wait(timeout=BOUNDED_TIMEOUT_S)
+        return real_insert(*args, **kwargs)
+
+    def _instrumented_commit(session):
+        """Byte-for-byte the real `_commit_forward_returns_concurrency_safe` body, with a counter added
+        so the IntegrityError-tolerant branch's use is PROVEN, not merely reachable in theory."""
+        try:
+            session.commit()
+        except IntegrityError:
+            rollback_count["n"] += 1
+            session.rollback()
+
+    def _caller(as_of_str: str) -> dict:
+        with Session(engine) as thread_session:
+            return backtest_module.backtest(as_of=as_of_str, session=thread_session)
+
+    forward_testing_module._insert_run_forward_returns = _synced_insert
+    forward_testing_module._commit_forward_returns_concurrency_safe = _instrumented_commit
+    try:
+        with ThreadPoolExecutor(max_workers=n_callers) as pool:
+            futures = [pool.submit(_caller, asof.isoformat()) for _ in range(n_callers)]
+            results = []
+            errors = []
+            for future in as_completed(futures, timeout=BOUNDED_TIMEOUT_S):
+                try:
+                    results.append(future.result())
+                except Exception as exc:  # noqa: BLE001 -- captured for the assertion below, never swallowed
+                    errors.append(exc)
+    finally:
+        forward_testing_module._insert_run_forward_returns = real_insert
+        forward_testing_module._commit_forward_returns_concurrency_safe = real_commit_safe
+
+    assert len(results) + len(errors) == n_callers, "not every caller completed -- treat as a hang"
+    assert not errors, f"expected every caller to complete without an unhandled exception; got {errors}"
+    assert all(r["is_latest"] is True for r in results)
+
+    with Session(engine) as session:
+        fr_rows = session.exec(
+            select(ForwardReturn).where(ForwardReturn.run_id == run_id, ForwardReturn.symbol == "AAA")
+        ).all()
+    keys = [(fr.run_id, fr.symbol, fr.horizon) for fr in fr_rows]
+    assert len(keys) == len(set(keys)), f"duplicate (run_id, symbol, horizon) key(s) found: {keys}"
+    assert len(fr_rows) == len(horizons), (
+        f"expected exactly one row per configured horizon for the one genuinely-missing scored ticker; "
+        f"got {len(fr_rows)}"
+    )
+
+    assert rollback_count["n"] >= 1, (
+        "expected the IntegrityError-tolerant rollback path to be exercised by at least one of the 5 "
+        "concurrent callers racing to backfill the SAME genuinely-missing run"
+    )
diff --git a/apps/backend/tests/test_forward_testing_serving_split.py b/apps/backend/tests/test_forward_testing_serving_split.py
index 4161f54c..f5a53dc5 100644
--- a/apps/backend/tests/test_forward_testing_serving_split.py
+++ b/apps/backend/tests/test_forward_testing_serving_split.py
@@ -36,7 +36,7 @@ from __future__ import annotations
 
 import json
 import logging
-from datetime import date, datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 
 import pytest
 from sqlalchemy import event
@@ -45,7 +45,9 @@ from sqlmodel import Session, select
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.forward_testing import (
+    backfill_run_forward_returns,
     compute_forward_aggregates,
+    compute_run_scorecard,
     forward_aggregates_ingest_cached,
     resolved_forward_aggregate_evidence,
 )
@@ -862,3 +864,510 @@ def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_e
     assert second["evidence_status"] == "ready"
     assert second["evidence_asof"] == requested_asof.isoformat()
     assert second["evidence_by_horizon"] == first["evidence_by_horizon"]
+
+
+# ======================================================================================================
+# ops-hardening iter-19 (J-06/J-07/J-08 shared latency blocker) — `backfill_run_forward_returns`'s new
+# zero-write guard (forward_testing.py ~line 1365). Iter-18's operator-supervised TC-9 re-measurement
+# (966 requests, host-guard-confined) pinned this function as the phase costing 881ms mean / 999ms max
+# under 6x concurrency (82.2% of each slow request) — it was invoked UNCONDITIONALLY on every
+# `GET /api/backtest` / MCP `query_backtest` request, including the common case where the run's forward
+# returns are ALREADY fully backfilled (the ingest finalize path, data_manager.py:2918, already does this
+# at creation). The fix: skip the write-lock-acquiring commit entirely when the pre-existing idempotency
+# check (`_insert_run_forward_returns`'s own return count) finds zero rows missing — no new query. The
+# genuinely-missing case is UNCHANGED (still inserts + commits synchronously, idempotent, race-tolerant).
+#
+# TC-1/TC-2/TC-3/TC-5 below; TC-4 (the mandatory concurrency proof) lives in
+# test_forward_testing_concurrency.py, co-located with but DISTINCT from that file's existing
+# forward-*aggregate* concurrency tests (this guards forward-*returns* — a different table/function).
+# ======================================================================================================
+def test_backtest_route_zero_write_when_forward_returns_already_complete(endpoint_engine, caplog):
+    """iter-19 TC-1: given a run whose forward returns are already fully backfilled for every configured
+    horizon (the scored ticker "AAA" — the benchmark ETFs have no price data in this fixture, so they
+    contribute nothing: an honest NA gap, never a partial insert), `GET /api/backtest`'s route function
+    issues ZERO INSERT/UPDATE/DELETE statements during the request (SQL-inspected via the SAME
+    `before_cursor_execute` technique `test_completeness_query_is_filtered_by_asof_key` already uses),
+    HTTP 200 (a clean plain-function return), and the extended `backtest_timing` log line records the
+    write as skipped (`write_taken=False`)."""
+    import app.api.backtest as backtest_module
+
+    engine, asof = endpoint_engine  # "AAA" already has a ForwardReturn row at every configured horizon
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+    captured: list[str] = []
+
+    def _capture(conn, cursor, statement, parameters, context, executemany):
+        captured.append(statement)
+
+    caplog.set_level(logging.INFO, logger="trendora.backtest")
+    with Session(engine) as session:
+        event.listen(engine, "before_cursor_execute", _capture)
+        try:
+            result = backtest_module.backtest(as_of=None, session=session)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture)
+
+    assert result["is_latest"] is True
+    write_statements = [
+        stmt for stmt in captured if stmt.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
+    ]
+    assert write_statements == [], (
+        f"expected zero write statements on the already-complete path; got {write_statements}"
+    )
+
+    timing_records = [
+        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
+    ]
+    assert len(timing_records) == 1, f"expected exactly one timing log line; got {len(timing_records)}"
+    assert "write_taken=False" in timing_records[0].getMessage(), (
+        f"expected the timing log to record the skipped write; got {timing_records[0].getMessage()!r}"
+    )
+
+
+def test_query_backtest_mcp_tool_zero_write_when_forward_returns_already_complete(endpoint_engine, caplog):
+    """iter-19 TC-2: mirrors TC-1 for the MCP `query_backtest` tool — zero write statements on the
+    already-complete path, the timing log records `write_taken=False` too, and its returned scorecard +
+    evidence_* fields are byte-identical to `GET /api/backtest`'s response for the SAME inputs (the two
+    callers share the exact same underlying guarded function; this proves cross-entry-point parity
+    survives the new guard)."""
+    import app.api.backtest as backtest_module
+    import app.mcp.tools as tools_module
+
+    engine, asof = endpoint_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+    with Session(engine) as session:
+        api_result = backtest_module.backtest(as_of=None, session=session)
+
+    captured: list[str] = []
+
+    def _capture(conn, cursor, statement, parameters, context, executemany):
+        captured.append(statement)
+
+    caplog.set_level(logging.INFO, logger="trendora.mcp_backtest")
+    with Session(engine) as session:
+        event.listen(engine, "before_cursor_execute", _capture)
+        try:
+            mcp_result = tools_module.query_backtest(session, asof=None)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture)
+
+    write_statements = [
+        stmt for stmt in captured if stmt.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
+    ]
+    assert write_statements == [], (
+        f"expected zero write statements on the already-complete path; got {write_statements}"
+    )
+    assert mcp_result["is_latest"] is True
+    assert mcp_result == api_result, "MCP query_backtest must serve byte-identical output to the API route"
+
+    timing_records = [
+        r for r in caplog.records
+        if r.name == "trendora.mcp_backtest" and "query_backtest_timing" in r.getMessage()
+    ]
+    assert len(timing_records) == 1
+    assert "write_taken=False" in timing_records[0].getMessage()
+
+
+def test_backfill_still_inserts_when_genuinely_missing_then_zero_write_on_repeat(tmp_path, caplog):
+    """iter-19 TC-3: given a run whose forward returns have NEVER been backfilled, `GET /api/backtest`
+    still INSERTs the missing rows exactly as before this iteration (idempotent, INSERT-only — the one
+    scored ticker "AAA" has sufficient post-snapshot bars for every configured horizon, so its row count
+    equals `len(HORIZONS)`; the benchmark ETFs have no price data in this fixture, an honest NA gap, not
+    a partial insert), and a SECOND call for the SAME as-of issues ZERO further write statements (the new
+    guard's zero-write path) — with the timing log recording `write_taken=True` on the first call and
+    `write_taken=False` on the second."""
+    import app.api.backtest as backtest_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'tc3_missing.db'}")
+    create_db_and_tables(engine)
+    asof = date(2025, 1, 10)
+    max_h = max(HORIZONS)
+    with Session(engine) as session:
+        run = _add_run(session, asof)
+        run_id = run.id
+        _add_result(session, run_id, "AAA")
+        session.add(DailyPrice(
+            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+        ))
+        for i in range(1, max_h + 1):
+            session.add(DailyPrice(
+                symbol="AAA", date=asof + timedelta(days=i), open=100.0, high=101.0, low=99.0,
+                close=100.0 + i, volume=1.0,
+            ))
+        session.commit()
+
+    caplog.set_level(logging.INFO, logger="trendora.backtest")
+    first_captured: list[str] = []
+
+    def _capture_first(conn, cursor, statement, parameters, context, executemany):
+        first_captured.append(statement)
+
+    with Session(engine) as session:
+        event.listen(engine, "before_cursor_execute", _capture_first)
+        try:
+            first = backtest_module.backtest(as_of=asof.isoformat(), session=session)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture_first)
+
+    insert_statements = [s for s in first_captured if s.strip().upper().startswith("INSERT")]
+    assert insert_statements, "expected the genuinely-missing case to still INSERT forward-return rows"
+
+    with Session(engine) as session:
+        fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
+    assert len(fr_rows) == len(HORIZONS), (
+        f"expected exactly one row per configured horizon for the one scored ticker with price data "
+        f"(benchmarks have no price data in this fixture, an honest NA gap); got {len(fr_rows)}"
+    )
+    assert {fr.horizon for fr in fr_rows} == set(HORIZONS)
+    assert {fr.symbol for fr in fr_rows} == {"AAA"}
+
+    first_timing = [
+        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
+    ]
+    assert len(first_timing) == 1
+    assert "write_taken=True" in first_timing[0].getMessage(), (
+        f"expected the first (genuinely-missing) call to record a taken write; got "
+        f"{first_timing[0].getMessage()!r}"
+    )
+
+    caplog.clear()
+    second_captured: list[str] = []
+
+    def _capture_second(conn, cursor, statement, parameters, context, executemany):
+        second_captured.append(statement)
+
+    with Session(engine) as session:
+        event.listen(engine, "before_cursor_execute", _capture_second)
+        try:
+            second = backtest_module.backtest(as_of=asof.isoformat(), session=session)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture_second)
+
+    second_write_statements = [
+        s for s in second_captured if s.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
+    ]
+    assert second_write_statements == [], (
+        f"expected zero write statements on the second (repeat) view; got {second_write_statements}"
+    )
+    second_timing = [
+        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
+    ]
+    assert len(second_timing) == 1
+    assert "write_taken=False" in second_timing[0].getMessage()
+    assert first["is_latest"] is True
+    assert second["is_latest"] is True
+    assert second["scorecard"] == first["scorecard"], "the repeat view must serve the SAME stored scorecard"
+
+
+def test_scorecard_and_evidence_byte_identical_with_and_without_explicit_as_of(endpoint_engine):
+    """iter-19 TC-5 (AG-3): `compute_run_scorecard` plus the evidence_* fields served by `GET
+    /api/backtest` for the already-backfilled TC-1 fixture are byte-for-byte identical to a DIRECT,
+    independent call to `compute_run_scorecard` / `resolved_forward_aggregate_evidence` for the same
+    as-of — proving the new zero-write guard changes ONLY whether a redundant commit happens, never a
+    served value. Checked BOTH with `as_of` omitted (defaults to latest) and with the SAME date passed
+    explicitly, across every configured horizon."""
+    import app.api.backtest as backtest_module
+
+    engine, asof = endpoint_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == asof)).one()
+        direct_card = compute_run_scorecard(session, run, cfg)
+        direct_evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
+
+    with Session(engine) as session:
+        omitted_result = backtest_module.backtest(as_of=None, session=session)
+    with Session(engine) as session:
+        explicit_result = backtest_module.backtest(as_of=asof.isoformat(), session=session)
+
+    assert set(direct_evidence["evidence_by_horizon"]) == set(HORIZONS)
+    for label, result in (("omitted", omitted_result), ("explicit", explicit_result)):
+        assert result["scorecard"] == direct_card["scorecard"], f"{label}: scorecard differs"
+        assert result["asof_date"] == direct_card["asof_date"], f"{label}: asof_date differs"
+        assert result["min_sample"] == direct_card["min_sample"], f"{label}: min_sample differs"
+        assert result["horizons"] == direct_card["horizons"], f"{label}: horizons differ"
+        assert result["survivorship_bias"] == direct_card["survivorship_bias"], (
+            f"{label}: survivorship_bias differs"
+        )
+        assert result["evidence_status"] == direct_evidence["evidence_status"], (
+            f"{label}: evidence_status differs"
+        )
+        assert result["evidence_generated_at"] == direct_evidence["evidence_generated_at"], (
+            f"{label}: evidence_generated_at differs"
+        )
+        assert result["evidence_asof"] == direct_evidence["evidence_asof"], f"{label}: evidence_asof differs"
+        assert result["evidence_by_horizon"] == direct_evidence["evidence_by_horizon"], (
+            f"{label}: evidence_by_horizon differs"
+        )
+
+
+def test_iter19_partial_backfill_run_is_detected_incomplete_and_completed(tmp_path):
+    """iter-19 completeness-preservation (guards the column-projected idempotency read): the cheaper
+    existence check must still detect a PARTIALLY-backfilled run as incomplete at the (symbol, horizon)
+    grain and fill EXACTLY the gap — proving projecting `(symbol, horizon)` instead of materializing full
+    `ForwardReturn` ORM rows did not change create-once / idempotent completeness semantics. A run is
+    fully backfilled, a proper SUBSET of horizons is then deleted (simulating a partial backfill), and
+    `backfill_run_forward_returns` must re-insert exactly the deleted keys (not all, not none), with a
+    subsequent call inserting zero (the pure warm read the TC-6 fix targets)."""
+    if len(HORIZONS) < 2:
+        pytest.skip("needs >= 2 configured horizons to delete a proper subset")
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'iter19_partial.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    asof = date(2025, 1, 10)
+    max_h = max(HORIZONS)
+    deleted_horizons = set(HORIZONS[: len(HORIZONS) // 2])  # a non-empty proper subset, e.g. {1, 5}
+
+    with Session(engine) as session:
+        run = _add_run(session, asof)
+        run_id = run.id
+        _add_result(session, run_id, "AAA")
+        # Entry close ON D plus max_h post-D bars so EVERY configured horizon can produce a row (only the
+        # scored "AAA" has price data; benchmark ETFs are an honest NA gap, mirroring TC-3's fixture).
+        session.add(DailyPrice(
+            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+        ))
+        for i in range(1, max_h + 1):
+            session.add(DailyPrice(
+                symbol="AAA", date=asof + timedelta(days=i), open=100.0, high=101.0, low=99.0,
+                close=100.0 + i, volume=1.0,
+            ))
+        session.commit()
+
+    # 1. Full backfill: one row per configured horizon for the one scored ticker.
+    with Session(engine) as session:
+        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
+        full = backfill_run_forward_returns(session, run, cfg)
+    assert full["rows_inserted"] == len(HORIZONS)
+
+    # 2. Delete a proper SUBSET of horizons -> a genuinely partial run.
+    with Session(engine) as session:
+        for fr in session.exec(
+            select(ForwardReturn).where(
+                ForwardReturn.run_id == run_id,
+                ForwardReturn.horizon.in_(sorted(deleted_horizons)),
+            )
+        ).all():
+            session.delete(fr)
+        session.commit()
+        remaining = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
+    assert len(remaining) == len(HORIZONS) - len(deleted_horizons)
+    assert {fr.horizon for fr in remaining} == set(HORIZONS) - deleted_horizons
+
+    # 3. Re-backfill: the projected existence read must detect the partial state and fill EXACTLY the gap.
+    with Session(engine) as session:
+        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
+        refill = backfill_run_forward_returns(session, run, cfg)
+    assert refill["rows_inserted"] == len(deleted_horizons), (
+        f"expected exactly the {len(deleted_horizons)} deleted (symbol, horizon) keys to be re-inserted; "
+        f"got {refill['rows_inserted']}"
+    )
+    with Session(engine) as session:
+        restored = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
+    assert {fr.horizon for fr in restored} == set(HORIZONS)
+    assert len(restored) == len(HORIZONS)
+    assert {fr.symbol for fr in restored} == {"AAA"}
+
+    # 4. A subsequent call is now a pure zero-write warm read (nothing missing -> inserted == 0).
+    with Session(engine) as session:
+        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
+        warm = backfill_run_forward_returns(session, run, cfg)
+    assert warm["rows_inserted"] == 0
+
+
+# ======================================================================================================
+# iter-19 (attempt 3) — the PROVEN TC-6 latency fix: un-elapsed horizons are short-circuited GLOBALLY
+# before the per-symbol loop, so a run within max(horizons) trading days of the data end (the default
+# `/backtest` latest run) pays ZERO per-symbol close_on/bars_after fetches for horizons that cannot yet
+# produce a row. These tests prove the short-circuit is byte-identical to the old unfiltered path while
+# eliminating the wasted fetches (the ~1090 queries that were 82% of each request under 6x concurrency).
+# ======================================================================================================
+def _seed_run_with_post_window(engine, asof: date, symbol: str, n_post_bars: int) -> int:
+    """Seed ONE run at `asof` with a single scored `symbol` carrying an entry bar ON asof (close 100.0)
+    plus `n_post_bars` consecutive post-asof daily bars (close = 100 + i). These are the ONLY post-asof
+    price rows in the DB, so the module's observable trading-day count for this run == min(n_post_bars,
+    max_h). Benchmark ETFs are unseeded (an honest NA gap), mirroring the partial-backfill fixture."""
+    with Session(engine) as session:
+        run = _add_run(session, asof)
+        rid = run.id
+        _add_result(session, rid, symbol)
+        session.add(DailyPrice(
+            symbol=symbol, date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+        ))
+        for i in range(1, n_post_bars + 1):
+            close = 100.0 + i
+            session.add(DailyPrice(
+                symbol=symbol, date=asof + timedelta(days=i), open=close, high=close + 1.0,
+                low=close - 1.0, close=close, volume=1.0,
+            ))
+        session.commit()
+    return rid
+
+
+def _fr_rows_sorted(session, run_id: int) -> list:
+    """A deterministic projection of EVERY stored ForwardReturn column for a run, sorted — the full
+    served-value surface, for a byte-identity assertion between the filtered and unfiltered paths."""
+    rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
+    return sorted(
+        (r.symbol, r.horizon, r.realized_return, r.entry_close, r.measured_date.isoformat(),
+         r.mae, r.mfe, r.max_drawdown, r.underwater_days, r.time_to_recover_days)
+        for r in rows
+    )
+
+
+def test_iter19_latest_run_unelapsed_horizons_short_circuit_no_price_fetches(tmp_path, monkeypatch):
+    """iter-19 TC-6 mechanism (the k==0 case the reviewer named): for the LATEST run (asof == the data
+    end, 0 observable post-D trading days) EVERY configured horizon is un-elapsed, so
+    `backfill_run_forward_returns` must short-circuit the per-symbol loop with ZERO `close_on`/`bars_after`
+    fetches and insert nothing — yet stay byte-identical to the OLD unfiltered path (which also inserted
+    nothing here, only after paying the wasted per-symbol fetches)."""
+    import app.engine.forward_testing as ft
+
+    cfg = load_config()
... [diff_bound] apps/backend/tests/test_forward_testing_serving_split.py: 134 more diff lines omitted — Read the file for full detail
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            |  83 ++++
 .../dispatch/prompt-req.D2j2mK.md                  | 540 ---------------------
 .../dispatch/req.D2j2mK.ready                      |   1 -
 .../dispatch/req.D2j2mK.started                    |   3 -
 .../dispatch/req.D2j2mK.usage                      |   1 -
 runs/goal-session-ops-hardening/telemetry.jsonl    |  10 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   7 +
 8 files changed, 101 insertions(+), 546 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
