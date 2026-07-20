# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index d510b68..c1fee1b 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -15,6 +15,12 @@ GO/DEGRADED/NO-GO verdict from `app.engine.readiness.compute_preflight` (which i
 module's own `readiness`/`warmup` computation — no second computation). The layout-level
 `PreflightBanner` is the ONLY reader; existing `readiness`/`warmup`/`status`/etc. keys are unchanged
 (byte-identical — J-40 not regressed).
+
+ops-hardening iter-4 (B3 fix) additively extends this SAME endpoint with the `readiness_detail` field —
+the sibling `detail` string from `compute_readiness`'s own return (`null` except for the new
+`awaiting_snapshot` state). Previously `compute_readiness`'s dict was discarded down to just
+`readiness["state"]`, so this value was computed correctly but never reached the frontend; this is the
+wiring fix. `readiness` itself stays the SAME bare string it always was (byte-identical contract).
 """
 from __future__ import annotations
 
@@ -51,6 +57,7 @@ def health(session: Session = Depends(get_session)) -> dict:
     except Exception:  # pragma: no cover - never let a readiness error blank the health probe
         readiness = {
             "state": "unavailable",
+            "detail": None,
             "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
         }
 
@@ -82,6 +89,10 @@ def health(session: Session = Depends(get_session)) -> dict:
         "symbol_count": symbol_count,
         # iter-28 (J-40): the single canonical readiness value (state + warm-up progress).
         "readiness": readiness["state"],
+        # ops-hardening iter-4 (B3 fix): the sibling detail string -- null except for the new
+        # `awaiting_snapshot` state (naming the condition + recovery action). Same computing module,
+        # same endpoint -- `compute_readiness` already produced this; it was just never served before.
+        "readiness_detail": readiness.get("detail"),
         "warmup": readiness["warmup"],
         # the config-derived poll cadences the frontend badge derives its interval from (no client-side
         # poll literal — anti-goal: No magic numbers). `poll_interval_seconds` is the fast cadence used
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 82729c9..d1fdd8c 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3001,7 +3001,7 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
 # hot key — reusing each cache's existing compute function, never a second derivation of any of them.
 # --------------------------------------------------------------------------------------------------
 def _persist_per_date_coverage_snapshots(
-    session: Session, cfg: Config, dates: list[date_cls]
+    session: Session, cfg: Config, dates: list[date_cls], prog: JobProgress
 ) -> None:
     """Persist a byte-identical `CoverageSnapshot` row for each as-of in `dates` (the snapshot dates a
     backfill NEWLY created), so the app-wide as-of switcher serves REAL coverage for each from storage —
@@ -3015,7 +3015,16 @@ def _persist_per_date_coverage_snapshots(
     N dates costs one load, not N. Each row equals a fresh `_compute_coverage_uncached(as_of=d)`. Per-date
     isolation (log + continue) so one date's failure never drops the rest; the caller wraps this whole call
     non-fatally too. Reads only committed bars (backfill adds none), writes only `CoverageSnapshot` rows —
-    so the shared cache never serves a stale series (AG-8: no unbounded request-path load; this is ingest)."""
+    so the shared cache never serves a stale series (AG-8: no unbounded request-path load; this is ingest).
+
+    ops-hardening iter-4 (F1 fix, re-review CRITICAL): calls the bare `prog.tick()` (heartbeat-only — no
+    `activity` argument, so it stamps ONLY `last_progress_at` and never overwrites the "scanning ..." line;
+    see `_refresh_ingest_aggregates`'s docstring) once per date at the TOP of the `todo` loop, BEFORE that
+    date's heavy `refresh_coverage_snapshot_for` (`_compute_coverage_uncached`) compute. This per-date
+    coverage warm is the FIRST half of the finalize tail (the market-phase loop is the second, measured
+    together at ~729s for a full 378-date rebuild, `reports/perf-budgets.md` Item L); without a tick here
+    `last_progress_at` froze across the whole coverage half — the exact false-'possibly stalled' defect the
+    market-phase tick alone did not close."""
     if not dates:
         return
     current = _resolve_coverage_asof(session, None, cfg)
@@ -3025,6 +3034,7 @@ def _persist_per_date_coverage_snapshots(
     pool_symbols = {row["symbol"] for row in read_pool()}
     with prefilled_bar_cache(session, expected_symbols=pool_symbols):
         for d in todo:
+            prog.tick()  # F1 fix (iter-4): per-date heartbeat stamp before this date's heavy coverage compute
             try:
                 refresh_coverage_snapshot_for(session, cfg, d)
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
@@ -3039,8 +3049,21 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
     "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` ACTUALLY refreshed — never a
     fabricated category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this
-    module)."""
+    module).
+
+    ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
+    the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
+    ..." line from the main scan loop is left honest/unchanged) at this function's own start, at each
+    per-date step of the per-date COVERAGE warm loop (`_persist_per_date_coverage_snapshots`, threaded `prog`
+    — iter-4 re-review CRITICAL: this loop's per-date `_compute_coverage_uncached` is the OTHER heavy half of
+    the finalize tail, ~half of the ~729s), AND at each per-date step of the market-phase warm loop below —
+    mirroring the main scan loop's own per-date heartbeat convention (`data_manager.py:2863`). Without ticks
+    across BOTH per-date loops, `last_progress_at` freezes for the WHOLE finalize tail once the main scan
+    completes (measured ~729s for a full rebuild, `reports/perf-budgets.md` Item L), and the frontend's
+    stale-heartbeat flag (`job_progress.heartbeat_stale_seconds`) falsely renders "· possibly stalled" on a
+    perfectly healthy job."""
     refreshed: list[str] = []
+    prog.tick()  # F1 fix: heartbeat-only stamp at the start of the finalize tail — see docstring above.
 
     if prog.new_snapshot_dates:
         # this run's own date-loop already created + committed these snapshots (scanner.persist_run_payload
@@ -3065,12 +3088,13 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     # try/except (log + continue) so it never flips the job. Skips the current stamp (persisted above) and
     # is a no-op — no bar-cache load — for the common single-latest-date backfill.
     try:
-        _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates)
+        _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates, prog)
     except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
         logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)
 
     market_phase_warmed = False
     for d in prog.new_snapshot_dates:
+        prog.tick()  # F1 fix: per-date heartbeat stamp -- see function docstring above.
         try:
             market_phase.market_phase_cached(session, d, cfg)
             market_phase_warmed = True
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index bfdfbdd..adbaab6 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -1,15 +1,26 @@
-"""Readiness state producer (Data Contract: app.engine.readiness) — iter-28, J-40.
+"""Readiness state producer (Data Contract: app.engine.readiness) — iter-28, J-40; widened iter-4 (B3 fix).
 
-The SINGLE honest readiness computer. It returns ONE state ∈ {`ready`, `initializing`, `unavailable`}
-plus the background warm-up progress `{done, total}` (cadence snapshots produced / expected — "history
-n/m"), computed ONCE here and served by the SINGLE canonical readiness endpoint (the extended
-`GET /api/health`). It is descriptive operational/job-control state — NOT a canonical score/return/bucket
-and NOT a duplicate of any existing value; it recomputes nothing (anti-goal: No recompute in the read path
-does not apply — readiness is not a snapshot value, it is liveness about whether the snapshots are servable).
+The SINGLE honest readiness computer. It returns ONE state ∈ {`ready`, `initializing`, `unavailable`,
+`awaiting_snapshot`} plus the background warm-up progress `{done, total}` (cadence snapshots produced /
+expected — "history n/m") and an optional `detail` string, computed ONCE here and served by the SINGLE
+canonical readiness endpoint (the extended `GET /api/health`). It is descriptive operational/job-control
+state — NOT a canonical score/return/bucket and NOT a duplicate of any existing value; it recomputes
+nothing (anti-goal: No recompute in the read path does not apply — readiness is not a snapshot value, it
+is liveness about whether the snapshots are servable).
 
 The state is reported HONESTLY (anti-goal: Readiness is reported honestly):
-  - `unavailable` — the DB is unreachable, OR there is no latest snapshot servable yet (no price data /
-    the synchronous latest-snapshot step has not produced the latest run). NEVER a fabricated `ready`.
+  - `unavailable` — the DB is unreachable, OR no run has EVER been persisted (no price data / the
+    synchronous latest-snapshot step has not produced a first run). NEVER a fabricated `ready`. This is
+    the ONLY unconditional case — even `awaiting_snapshot` below never masks it.
+  - `awaiting_snapshot` (iter-4, B3 fix) — a run IS servable (some snapshot exists), but the BENCHMARK
+    symbol's (`cfg.etfs.index[0]` — SPY, the same symbol `_warmup_dates`/`walk_forward_asof_dates` use to
+    define the trading calendar) own latest bar has advanced past that run, with no run yet for that later
+    date — "new data landed for the calendar-defining symbol, snapshot pending." Compared via a per-symbol
+    indexed query (`_latest_benchmark_bar_date`, never a whole-table scan — AG-8), so an UNRELATED symbol's
+    ordinary fetch never produces this state (the B3 bug this fixes: the check used to compare against the
+    whole-table `latest_data_date` max, so any symbol's new bar could falsely flip the badge all the way to
+    `unavailable`). `detail` carries a non-null human-readable string naming the condition + recovery
+    action; `null` for every other state.
   - `initializing` — the latest snapshot IS servable (so the core read pages work) but the background
     historical warm-up is still in flight (or has not started / has failed): `done < total`, or the
     warm-up record reports `running`/`failed`. A still-warming backend is NEVER mislabeled `unavailable`.
@@ -44,6 +55,11 @@ from app.models import DailyPrice, ScannerRun
 READY = "ready"
 INITIALIZING = "initializing"
 UNAVAILABLE = "unavailable"
+# ops-hardening iter-4 (B3 fix): a run IS servable, but the benchmark symbol's (`cfg.etfs.index[0]`) own
+# latest bar has advanced past it with no run yet for that date -- distinct from `unavailable` (nothing
+# servable at all) and `initializing` (cadence warm-up in flight). See `_latest_benchmark_bar_date` below
+# and the module docstring above.
+AWAITING_SNAPSHOT = "awaiting_snapshot"
 
 # The three composite preflight verdicts (iter-33, J-20 / backlog B-301). String values are the exact
 # DoD-mandated spelling ("NO-GO", hyphenated) — never re-derived elsewhere.
@@ -59,6 +75,16 @@ def _latest_run_date(session: Session):
     return session.scalar(select(func.max(ScannerRun.asof_date)))
 
 
+def _latest_benchmark_bar_date(session: Session, cfg: Config):
+    """ops-hardening iter-4 (B3 fix) — the BENCHMARK symbol's (`cfg.etfs.index[0]`, SPY — the exact same
+    symbol `forward_testing.walk_forward_asof_dates` / `warmup._warmup_dates` already use to define the
+    trading calendar) own latest bar date. ONE indexed max query filtered to a single symbol (mirrors
+    `latest_data_date`'s shape, AG-8) — never a whole-table scan across all symbols. None when the
+    benchmark itself has no stored bars."""
+    benchmark = cfg.etfs.index[0]
+    return session.scalar(select(func.max(DailyPrice.date)).where(DailyPrice.symbol == benchmark))
+
+
 # --------------------------------------------------------------------------------------------------
 # iter-24 fast-platform item G — memoize the cadence-date set `/api/health` re-derives on every poll.
 #
@@ -118,15 +144,30 @@ def compute_readiness(
     try:
         latest_data = latest_data_date(session)
         latest_run = _latest_run_date(session)
+        # ops-hardening iter-4 (B3 fix): the benchmark's OWN latest bar (one indexed per-symbol query,
+        # AG-8) is the ONLY input compared against `latest_run` below -- never `latest_data`'s whole-table
+        # max. `latest_data` is still read (unchanged) for the cadence/warm-up total further down; an
+        # unrelated symbol's fetch can move IT but no longer touches servability at all.
+        latest_benchmark_bar = _latest_benchmark_bar_date(session, cfg)
         db_ok = True
     except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
         latest_data = None
         latest_run = None
+        latest_benchmark_bar = None
         db_ok = False
 
-    # The latest snapshot is "servable" when the latest data date has a persisted run (the synchronous
-    # boot's `ensure_latest_snapshot` produced it). No data / no latest run -> not yet servable.
-    latest_servable = bool(latest_data is not None and latest_run is not None and latest_run >= latest_data)
+    # A servable run exists iff ANY run has ever been persisted -- the ONLY unconditional case: a true
+    # never-scanned DB (`latest_run is None`) is ALWAYS unavailable, regardless of benchmark bar data
+    # (regression guard for the pre-existing `unscanned_engine` fixture / J-04 crash detection).
+    has_servable_run = latest_run is not None
+
+    # B3 fix: the benchmark's own latest bar has advanced past the last persisted run, with no run yet
+    # for that later date -- "new data landed for the symbol that defines the trading calendar, but the
+    # snapshot hasn't caught up." Compared via the per-symbol query above, never the whole-table
+    # `latest_data` -- so an unrelated symbol's ordinary fetch can NEVER produce this state.
+    awaiting_snapshot = bool(
+        has_servable_run and latest_benchmark_bar is not None and latest_benchmark_bar > latest_run
+    )
 
     # The honest cadence-warm-up progress. The expected `total` is the full historical cadence set (the
     # background warm-up's denominator); `done` is how many of those snapshots are ACTUALLY persisted in
@@ -167,22 +208,39 @@ def compute_readiness(
 
     message = f"history {done}/{total}"
 
-    # The honest state. unavailable dominates (no servable latest). Otherwise ready iff the historical
-    # warm-up is COMPLETE (every cadence snapshot persisted) AND the warm-up is not still actively running
-    # and did not fail — so the badge truthfully shows the flip to Ready only once warm-up settles. A
-    # `running` record stays `initializing` even when its snapshots are all present (its forward-returns
-    # backfill may still be in flight); a `failed` record never reports `ready` (honest, not a silent
-    # green); `pending` (no in-process warm-up / DB-derived-complete on a warm DB) with all snapshots
-    # present is ready. A still-warming / failed backend is NEVER mislabeled unavailable.
-    if not db_ok or not latest_servable:
+    # The honest state. unavailable dominates (no servable run at all -- the ONLY unconditional case).
+    # Otherwise awaiting_snapshot when the benchmark's own bar has outrun the last run (B3 fix, iter-4).
+    # Otherwise ready iff the historical warm-up is COMPLETE (every cadence snapshot persisted) AND the
+    # warm-up is not still actively running and did not fail — so the badge truthfully shows the flip to
+    # Ready only once warm-up settles. A `running` record stays `initializing` even when its snapshots are
+    # all present (its forward-returns backfill may still be in flight); a `failed` record never reports
+    # `ready` (honest, not a silent green); `pending` (no in-process warm-up / DB-derived-complete on a
+    # warm DB) with all snapshots present is ready. A still-warming / failed / awaiting-snapshot backend is
+    # NEVER mislabeled unavailable.
+    if not db_ok or not has_servable_run:
         state = UNAVAILABLE
+    elif awaiting_snapshot:
+        state = AWAITING_SNAPSHOT
     elif done >= total and status in ("ok", "pending"):
         state = READY
     else:
         state = INITIALIZING
 
+    # ops-hardening iter-4 (B3 fix): the honest, human-readable detail -- non-null ONLY for the new
+    # state (mirrors the `PreflightComponent.detail` naming precedent), naming the condition + the
+    # recovery action (an operator-run backfill/rebuild on Data Manager produces the missing snapshot).
+    detail: Optional[str] = None
+    if state == AWAITING_SNAPSHOT:
+        benchmark = cfg.etfs.index[0]
+        detail = (
+            f"New data has landed for the benchmark ({benchmark}) through "
+            f"{latest_benchmark_bar.isoformat()}, but no snapshot has been produced for that date yet. "
+            "Run a backfill or rebuild on Data Manager to produce it."
+        )
+
     return {
         "state": state,
+        "detail": detail,
         "warmup": {
             "done": done,
             "total": total,
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 9b02846..bb6aa77 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -19,7 +19,7 @@ from __future__ import annotations
 import json
 import socket
 import time
-from datetime import date, datetime, timedelta
+from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
 import httpx
@@ -1177,6 +1177,137 @@ def test_finalize_hook_makes_no_network_call(finalize_hook_engine, monkeypatch):
     assert refreshed  # completed successfully with zero socket.connect calls
 
 
+# ==================================================================================================
+# ops-hardening iter-4 (F1 fix): the finalize hook's own heartbeat -- `last_progress_at` must advance
+# through the WHOLE finalize tail (not just the main scan loop), or the frontend's stale-heartbeat flag
+# falsely renders "· possibly stalled" on a perfectly healthy job.
+# ==================================================================================================
+@pytest.fixture()
+def finalize_hook_multi_date_engine(tmp_path):
+    """Like `finalize_hook_engine` but with TWO stored dates — enough to prove the F1 fix ticks the
+    heartbeat AT LEAST ONCE PER DATE in the market-phase warm loop, not just once for the whole call."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_multi.db'}")
+    create_db_and_tables(engine)
+    dates = [date(2024, 3, 4), date(2024, 3, 5)]
+    with Session(engine) as session:
+        for i, d in enumerate(dates):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+            run = ScannerRun(
+                asof_date=d, created_at=datetime(2024, 3, 4 + i), provider="seed", benchmark="SPY",
+                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.commit()
+            session.refresh(run)
+            session.add(ScannerResult(
+                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+                setup_status="Actionable", rank=1, record_json="{}",
+            ))
+            session.commit()
+    return engine, dates
+
+
+def test_finalize_hook_ticks_heartbeat_at_least_once_per_date_in_market_phase_loop(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """F1 fix: `_refresh_ingest_aggregates` calls the bare `prog.tick()` (heartbeat-only, never
+    overwriting `current_activity` — see its docstring) at its own start AND inside the per-date
+    market-phase warm loop (`data_manager.py:3072-3078`), so `last_progress_at` advances through the
+    WHOLE finalize tail — not just the main scan loop (`:2863`). Instrumented by spying on
+    `market_phase.market_phase_cached` to capture `prog.last_progress_at` at the moment EACH date's
+    compute is about to run, proving the heartbeat had already advanced past a deliberately stale
+    sentinel before EVERY date — not merely once, somewhere, for the whole function."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+    stale_sentinel = datetime(2000, 1, 1, tzinfo=timezone.utc)
+    seen_at_call: list[datetime] = []
+    real_market_phase_cached = market_phase.market_phase_cached
+
+    def _spy(session, as_of, config=None):
+        seen_at_call.append(prog.last_progress_at)
+        return real_market_phase_cached(session, as_of, config)
+
+    monkeypatch.setattr(market_phase, "market_phase_cached", _spy)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="heartbeat-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.new_snapshot_dates = list(dates)
+        prog.last_progress_at = stale_sentinel
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert len(seen_at_call) == len(dates), "expected one market-phase compute per new snapshot date"
+    for i, seen in enumerate(seen_at_call):
+        assert seen != stale_sentinel, f"date index {i}: heartbeat had not advanced before this date's compute"
+    assert prog.last_progress_at != stale_sentinel  # the whole call leaves the heartbeat fresh, not frozen
+
+
+@pytest.fixture()
+def finalize_hook_triple_date_engine(tmp_path):
+    """Like `finalize_hook_multi_date_engine` but with THREE stored dates. The per-date COVERAGE warm loop
+    inside `_persist_per_date_coverage_snapshots` skips the CURRENT resolved as-of (the latest stored date),
+    so three dates leaves TWO in its `todo` — enough to prove the F1 re-review fix ticks the heartbeat at
+    least once PER DATE in THAT loop (not just the later market-phase loop, and not merely once for the whole
+    call)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_triple.db'}")
+    create_db_and_tables(engine)
+    dates = [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6)]
+    with Session(engine) as session:
+        for i, d in enumerate(dates):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+            run = ScannerRun(
+                asof_date=d, created_at=datetime(2024, 3, 4 + i), provider="seed", benchmark="SPY",
+                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.commit()
+            session.refresh(run)
+            session.add(ScannerResult(
+                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+                setup_status="Actionable", rank=1, record_json="{}",
+            ))
+            session.commit()
+    return engine, dates
+
+
+def test_persist_per_date_coverage_snapshots_ticks_heartbeat_per_date(
+    finalize_hook_triple_date_engine, monkeypatch
+):
+    """F1 fix (iter-4 re-review CRITICAL): the per-date COVERAGE warm loop inside
+    `_persist_per_date_coverage_snapshots` — the FIRST heavy half of the finalize tail, one
+    `_compute_coverage_uncached` per date (378 calls on a full rebuild) — must stamp the heartbeat before
+    EACH date's compute, or `last_progress_at` freezes across all of it (the market-phase tick alone runs
+    only AFTER this loop, so it cannot cover it). Calls the function directly to isolate ITS loop, and spies
+    on `refresh_coverage_snapshot_for` (the way `..._in_market_phase_loop` spies on `market_phase_cached`) to
+    capture `prog.last_progress_at` at the moment EACH date's compute is about to run — proving it had
+    already advanced past a deliberately stale sentinel before EVERY date, not merely once for the call."""
+    engine, dates = finalize_hook_triple_date_engine
+    cfg = load_config()
+    stale_sentinel = datetime(2000, 1, 1, tzinfo=timezone.utc)
+    seen_at_call: list[datetime] = []
+    real_refresh_for = data_manager.refresh_coverage_snapshot_for
+
+    def _spy(session, config, resolved_asof):
+        seen_at_call.append(prog.last_progress_at)
+        return real_refresh_for(session, config, resolved_asof)
+
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _spy)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="cov-heartbeat-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.last_progress_at = stale_sentinel
+        # the latest date (dates[-1]) is the current stamp the loop SKIPS -> todo = the two earlier dates.
+        data_manager._persist_per_date_coverage_snapshots(session, cfg, list(dates), prog)
+
+    assert len(seen_at_call) == len(dates) - 1, "expected one coverage compute per non-current new date"
+    for i, seen in enumerate(seen_at_call):
+        assert seen != stale_sentinel, (
+            f"date index {i}: heartbeat had not advanced before this date's coverage compute"
+        )
+    assert prog.last_progress_at != stale_sentinel  # the loop leaves the heartbeat fresh, not frozen
+
+
 def test_run_detail_omits_aggregates_refreshed_until_computed():
     """TC-13/TC-14 — mirrors `test_run_detail_omits_breakdown_until_computed`: a not-yet-computed (fresh,
     `_create_run_record`-time) backfill row serves `aggregates_refreshed` null; an INTERRUPTED row whose
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index 058f422..ca9ebb6 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -16,9 +16,10 @@ and that `record_verdict_transition` appends ONLY on a verdict change (bounded g
 """
 from __future__ import annotations
 
-from datetime import date
+from datetime import date, datetime, timedelta
 
 import pytest
+from sqlalchemy import event
 from sqlmodel import Session
 
 from app.config import load_config
@@ -34,7 +35,7 @@ from app.engine.readiness import (
     record_verdict_transition,
     resolve_verdict_history_path,
 )
-from app.models import DailyPrice
+from app.models import DailyPrice, ScannerRun
 
 
 def _readiness_cfg(cfg, **overrides):
@@ -265,16 +266,166 @@ def test_preflight_servability_reuses_compute_readiness_verbatim(loaded_engine,
 
 
 def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
-    """`compute_preflight` is ADDITIVE — `compute_readiness`'s own return shape is untouched (J-40 not
-    regressed): exactly `{"state", "warmup"}`, `warmup` exactly `{"done","total","status","message"}`."""
+    """`compute_preflight` is ADDITIVE — `compute_readiness`'s own return shape is untouched BY IT (J-40
+    not regressed): exactly `{"state", "detail", "warmup"}` (ops-hardening iter-4's B3 fix adds the
+    `detail` sibling alongside `state`/`warmup`), `warmup` exactly
+    `{"done","total","status","message"}`. This warmed, fully-caught-up fixture never produces the new
+    `awaiting_snapshot` state, so `detail` is null here (see the dedicated B3 fixture-matrix below for the
+    non-null case)."""
     cfg = load_config()
     with Session(loaded_engine) as session:
         result = compute_readiness(session, config=cfg)
-    assert set(result) == {"state", "warmup"}
-    assert result["state"] in {"ready", "initializing", "unavailable"}
+    assert set(result) == {"state", "detail", "warmup"}
+    assert result["state"] in {"ready", "initializing", "unavailable", "awaiting_snapshot"}
+    assert result["detail"] is None
     assert set(result["warmup"]) == {"done", "total", "status", "message"}
 
 
+# ==================================================================================================
+# ops-hardening iter-4 (B3 fix): compute_readiness's servability check is benchmark-scoped, never a
+# whole-table `daily_prices` scan -- an unrelated symbol's ordinary fetch must never flip the badge to
+# `unavailable`; the BENCHMARK's own latest bar outrunning the last run gets its own honest new state.
+# ==================================================================================================
+@pytest.fixture(scope="module")
+def non_benchmark_ahead_engine(tmp_path_factory, config):
+    """A `ScannerRun` persisted for date D, alongside the BENCHMARK's own single bar also dated D — the
+    ordinary "caught up" baseline (TC-1). Mutated in-test by landing a NON-benchmark symbol's bar at D+1
+    (an ordinary fetch) to reproduce B3's exact trigger shape (TC-2): the benchmark's own latest bar stays
+    put, so this must change NOTHING about `state`."""
+    db_path = tmp_path_factory.mktemp("non_benchmark_ahead_db") / "non_benchmark_ahead.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    benchmark = config.etfs.index[0]
+    d0 = date(2024, 3, 4)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol=benchmark, date=d0, open=1, high=1, low=1, close=1, volume=1))
+        session.add(ScannerRun(
+            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark=benchmark,
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+    return engine, benchmark, d0
+
+
+def test_non_benchmark_symbol_fetch_never_affects_servability(non_benchmark_ahead_engine):
+    """TC-1 + TC-2: the baseline "benchmark caught up" case reads ready/initializing (never unavailable,
+    never awaiting_snapshot) — and landing an ORDINARY fetch for an unrelated symbol dated AFTER the last
+    run (the actual B3 reproduction: an ordinary "Fetch EOD prices" job for some other ticker) changes
+    `state`/`warmup` NOT AT ALL, because the new per-symbol query never reads that unrelated symbol."""
+    engine, benchmark, d0 = non_benchmark_ahead_engine
+    cfg = load_config()
+    readiness.reset_readiness_cache()
+    with Session(engine) as session:
+        before = compute_readiness(session, config=cfg)
+    assert before["state"] in {"ready", "initializing"}
+    assert before["detail"] is None
+
+    d1 = d0 + timedelta(days=1)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="ZZZ", date=d1, open=1, high=1, low=1, close=1, volume=1))
+        session.commit()
+    readiness.reset_readiness_cache()  # force a fresh derive -- a stale memo hit could mask a real bug
+    with Session(engine) as session:
+        after = compute_readiness(session, config=cfg)
+
+    assert after["state"] == before["state"] != "unavailable"
+    assert after["detail"] is None
+    assert after["warmup"] == before["warmup"]
+
+
+@pytest.fixture(scope="module")
+def benchmark_ahead_engine(tmp_path_factory, config):
+    """A `ScannerRun` persisted for date D, then the BENCHMARK symbol's OWN latest bar advances to D+1
+    with no run yet for D+1 — the exact `awaiting_snapshot` condition (TC-3, B3 fix): a servable last run
+    exists, but new data has landed for the symbol that defines the trading calendar."""
+    db_path = tmp_path_factory.mktemp("awaiting_snapshot_db") / "benchmark_ahead.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    benchmark = config.etfs.index[0]
+    d0 = date(2024, 3, 4)
+    d1 = date(2024, 3, 5)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol=benchmark, date=d0, open=1, high=1, low=1, close=1, volume=1))
+        session.add(DailyPrice(symbol=benchmark, date=d1, open=1, high=1, low=1, close=1, volume=1))
+        session.add(ScannerRun(
+            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark=benchmark,
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+    return engine, benchmark, d0, d1
+
+
+def test_awaiting_snapshot_when_benchmark_own_bar_outruns_last_run(benchmark_ahead_engine):
+    """TC-3: the BENCHMARK's own latest bar advancing past the last persisted run (no run yet for that
+    date) is the new honest `awaiting_snapshot` state — distinct from unavailable/ready/initializing —
+    with a non-null detail naming the condition and the recovery action."""
+    engine, benchmark, d0, d1 = benchmark_ahead_engine
+    cfg = load_config()
+    readiness.reset_readiness_cache()
+    with Session(engine) as session:
+        result = compute_readiness(session, config=cfg)
+    assert result["state"] == "awaiting_snapshot"
+    assert result["detail"] is not None
+    assert benchmark in result["detail"]
+    assert d1.isoformat() in result["detail"]
+
+
+def test_awaiting_snapshot_never_masks_true_unavailability(unscanned_engine):
+    """TC-6 regression guard: `latest_run is None` (no ScannerRun ever persisted) MUST still resolve
+    unconditionally to `unavailable`, even on a DB with real price data — the one case where "nothing is
+    servable" must never be softened by the new state."""
+    cfg = load_config()
+    readiness.reset_readiness_cache()
+    with Session(unscanned_engine) as session:
+        result = compute_readiness(session, config=cfg)
+    assert result["state"] == "unavailable"
+    assert result["detail"] is None
+
+
+def test_preflight_servability_ok_for_awaiting_snapshot_state(benchmark_ahead_engine, tmp_path_factory, monkeypatch):
+    """TC-5: `compute_preflight`'s servability component stays `ok` (verdict GO, not forced to
+    NO-GO/DEGRADED) when readiness is `awaiting_snapshot` alone — `compute_preflight`'s existing
+    `!= UNAVAILABLE` check already treats the new state as non-breaching; this pins that it stays true
+    without re-deriving it."""
+    engine, benchmark, d0, d1 = benchmark_ahead_engine
+    cfg = load_config()
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("awaiting_snapshot_preflight"), ok=True)
+    readiness.reset_readiness_cache()
+    with Session(engine) as session:
+        readiness_result = compute_readiness(session, config=cfg)
+        assert readiness_result["state"] == "awaiting_snapshot"  # sanity: this IS the target condition
+        preflight_result = compute_preflight(session, config=cfg)
+    assert preflight_result["components"]["servability"]["ok"] is True
+    assert preflight_result["verdict"] == GO
+
+
+def test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan(loaded_engine):
+    """TC-10 (AG-8): the new benchmark-scoped latest-bar query filters to ONE symbol via a WHERE clause
+    on `daily_prices.symbol` — never an unfiltered whole-table scan. Captured at the SQL-statement level
+    (mirrors test_health.py's query-shape instrumentation) so this is a structural guarantee, not merely
+    an accidental byte-identical result."""
+    cfg = load_config()
+    captured: list[str] = []
+
+    def _capture(conn, cursor, statement, parameters, context, executemany):
+        lowered = statement.lower()
+        if "daily_prices" in lowered and lowered.strip().startswith("select"):
+            captured.append(statement)
+
+    event.listen(loaded_engine, "before_cursor_execute", _capture)
+    try:
+        with Session(loaded_engine) as session:
+            readiness._latest_benchmark_bar_date(session, cfg)
+    finally:
+        event.remove(loaded_engine, "before_cursor_execute", _capture)
+
+    assert len(captured) == 1, f"expected exactly one query, got: {captured}"
+    statement = captured[0].lower()
+    assert "where" in statement and "symbol" in statement, f"expected a symbol-filtered WHERE clause, got: {statement}"
+
+
 # ==================================================================================================
 # iter-35 (J-21/B-304): the `drift` component -- ok when absent/clean, breached on a written artifact,
 # worst-severity composition across all FOUR components still correct
diff --git a/apps/frontend/components/health-badge.tsx b/apps/frontend/components/health-badge.tsx
index e75d2d8..f4fc3d5 100644
--- a/apps/frontend/components/health-badge.tsx
+++ b/apps/frontend/components/health-badge.tsx
@@ -12,16 +12,24 @@ type Detail =
   | { kind: "error" };
 
 /** Live backend readiness badge (iter-28, J-40): the visible truth about backend state — Ready,
- *  Initializing… (with live "history n/m" warm-up progress), or Unavailable. It reads the SINGLE shared
- *  readiness value from `useReadiness` (one client-side readiness read; the frontend never computes
- *  readiness itself). The provider/seed/symbol detail badges fetch the rest of the health payload once
- *  for context. Re-checks happen via the readiness provider's config-derived poll. */
+ *  Initializing…, Snapshot pending (ops-hardening iter-4, B3 fix), or Unavailable. It reads the SINGLE
+ *  shared readiness value from `useReadiness` (one client-side readiness read; the frontend never
+ *  computes readiness itself). The provider/seed/symbol/recovery-detail badges fetch the rest of the
+ *  health payload for context, re-fetching whenever the shared `state` transitions (see the effect below)
+ *  so the `awaiting_snapshot` recovery-pointer text stays in sync with the SAME transition the pill
+ *  re-renders for, without a second polling loop. Re-checks of `state`/`warmup` themselves happen via the
+ *  readiness provider's own config-derived poll. */
 export function HealthBadge() {
   const { state, warmup, loading } = useReadiness();
   const [detail, setDetail] = useState<Detail>({ kind: "loading" });
 
-  // The static-ish context detail (provider / seed date / symbol count). Fetched once; it does not
-  // need the fast readiness cadence. If it fails, the readiness badge still renders honestly.
+  // The context detail (provider / seed date / symbol count / the `awaiting_snapshot` recovery-pointer
+  // string). Re-fetched whenever the shared readiness `state` transitions -- state changes are
+  // infrequent, so this stays cheap, and it keeps the recovery-pointer text synced to the exact moment
+  // the pill below flips to `awaiting_snapshot` (rather than only refreshing once on mount, which could
+  // show the new pill with a stale/missing detail until some unrelated future reload). If it fails, the
+  // readiness pill still renders honestly — it reads `state`/`warmup` from `useReadiness()` directly,
+  // never from this fetch.
   useEffect(() => {
     let active = true;
     fetchHealth()
@@ -34,9 +42,9 @@ export function HealthBadge() {
     return () => {
       active = false;
     };
-  }, []);
+  }, [state]);
 
-  // --- the readiness pill (the load-bearing three-state badge) ---
+  // --- the readiness pill (the load-bearing four-state badge) ---
   let pill;
   if (loading || state === null) {
     pill = (
@@ -63,6 +71,19 @@ export function HealthBadge() {
         </span>
       </Badge>
     );
+  } else if (state === "awaiting_snapshot") {
+    // ops-hardening iter-4 (B3 fix): a servable last run exists, but new data has landed for the
+    // benchmark symbol that defines the trading calendar and no snapshot covers it yet -- a calm,
+    // honest, non-danger state (never "Backend unavailable"). The dot is static (not animate-pulse):
+    // unlike `initializing`'s self-resolving warm-up, this condition persists until an operator runs a
+    // backfill/rebuild on Data Manager, so it reads as "needs action," not "in progress automatically."
+    const recoveryDetail = detail.kind === "ok" ? detail.data.readiness_detail : null;
+    pill = (
+      <Badge variant="accent" data-testid="readiness-badge" data-state="awaiting_snapshot">
+        <span className="h-2 w-2 rounded-full bg-accent" aria-hidden />
+        <span>Snapshot pending{recoveryDetail ? ` — ${recoveryDetail}` : ""}</span>
+      </Badge>
+    );
   } else {
     // unavailable
     pill = (
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 017d1ed..54502c1 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -111,8 +111,11 @@ async function sendJSON<T>(method: "POST" | "DELETE", path: string, body?: unkno
 /** The honest backend readiness state computed ONCE by the backend (app.engine.readiness) and served
  *  on the single canonical /api/health endpoint. The frontend NEVER computes readiness itself — it
  *  renders this value. `ready` = serving + history warmed; `initializing` = latest servable but the
- *  background historical warm-up is still loading; `unavailable` = no servable snapshot / DB down. */
-export type ReadinessState = "ready" | "initializing" | "unavailable";
+ *  background historical warm-up is still loading; `unavailable` = no servable snapshot / DB down;
+ *  `awaiting_snapshot` (ops-hardening iter-4, B3 fix) = a run IS servable, but the benchmark symbol's own
+ *  latest bar has advanced past it with no run yet for that date -- distinct from `unavailable` (nothing
+ *  servable at all). */
+export type ReadinessState = "ready" | "initializing" | "unavailable" | "awaiting_snapshot";
 
 /** Background warm-up progress (cadence snapshots produced / expected — "history n/m"). `done`/`total`
  *  drive the badge progress + the Backtest/Research "warming up (n/m)" states. */
@@ -156,6 +159,10 @@ export interface HealthStatus {
   symbol_count: number;
   // iter-28 (J-40): the single canonical readiness value (state + warm-up progress).
   readiness: ReadinessState;
+  /** ops-hardening iter-4 (B3 fix): honest human-readable detail, non-null ONLY when
+   *  `readiness === "awaiting_snapshot"` (naming the condition + recovery action) -- null for the other
+   *  three states. Same computing module/endpoint as `readiness` (`compute_readiness` / `GET /api/health`). */
+  readiness_detail: string | null;
   warmup: WarmupProgress;
   // the config-derived poll cadences the badge derives its interval from (no client-side poll literal).
   poll_interval_seconds: number;
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-ops-hardening/telemetry.jsonl   | 11 +++++++++++
 runs/goal-session-ops-hardening/trace/.next-step  |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |  5 +++++
 3 files changed, 17 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
