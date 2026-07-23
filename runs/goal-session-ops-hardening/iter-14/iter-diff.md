# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 9436658f..9073651f 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -796,36 +796,65 @@ def compute_forward_aggregates(
     `as_of` (iter-17, J-09/J-10) optionally scopes the pool to an EXPANDING WALK-FORWARD WINDOW: when
     set, ONLY snapshots with `ScannerRun.asof_date <= as_of` contribute, so a run dated > D leaks nothing
     into the as-of-D evidence (the No-lookahead / No-recompute / Single-source criticals). It is a SINGLE
-    membership filter on the `fr_rows` step, so it equally bounds `runs_with_fr`, `results`, `run_rows`,
-    and the SPY/QQQ benchmark lists (all derived from it) — the grouping / excess / control-group /
-    attribution math is untouched. `as_of=None` keeps the all-history behaviour BYTE-IDENTICAL (== the
-    latest-date case, since no run is dated after the latest). The cutoff is the resolved global as-of
-    date transmitted on the snapshot-served read — never a second date state (J-18)."""
+    membership filter on the `fr_stmt` step, so it equally bounds `runs_with_fr`, the `ScannerResult` scan,
+    `run_rows`, and the SPY/QQQ benchmark lists (all derived from it) — the grouping / excess /
+    control-group / attribution math is untouched. `as_of=None` keeps the all-history behaviour
+    BYTE-IDENTICAL (== the latest-date case, since no run is dated after the latest). The cutoff is the
+    resolved global as-of date transmitted on the snapshot-served read — never a second date state (J-18).
+
+    iter-14 (J-07, AG-8 REGRESSION recovery): the `ForwardReturn` and `ScannerResult` reads below are
+    column-projected and `yield_per`-streamed (mirroring `_streamed_existing_keys` in this same module and
+    `research._event_study_members`/`_subject_matching_result_rows`'s established precedent for these exact
+    two tables) instead of each being materialized as a whole-partition `.all()` of full ORM objects. Both
+    tables had grown ~9x since this was first written (`scanner_results` 611,689 rows, `forward_returns`
+    3,098,302 rows at the ops-hardening iter-14 measurement) and the unbounded pattern was the confirmed
+    root cause of a session-long critical AG-8 defect (a silent per-request `MemoryError` in iter-11/12,
+    escalating to a ~12-minute full-backend wedge under concurrent load in iter-13). Only the fields
+    actually read below are ever selected — no second formula, no schema change, no signature/return-shape
+    change; byte-identical to the prior whole-row materialization for the same inputs (proven by a
+    fixture-backed equality test), because the SAME filter produces the SAME row set and every downstream
+    step (dict/set construction, `_group_means`, `_control_groups`, `_attribution_slices`) is unaffected by
+    how those rows were fetched."""
     cfg = config or get_config()
     wf = cfg.walk_forward
     bm = benchmark_symbols(cfg)
+    # iter-47 (J-105)'s SINGLE source of the streaming batch size — the SAME knob
+    # `_streamed_existing_keys`/`research.py`'s heavy read-path builders already use (no second batch-size
+    # config value).
+    batch = cfg.research.read_batch_size
 
     # The SINGLE as-of membership filter (iter-17): restrict the pool to runs dated <= D by joining each
     # forward return to its run's canonical `asof_date`. `as_of=None` adds NO clause -> the query (and
     # thus every derived set) is byte-identical to the all-history path. The cutoff is read from
     # `ScannerRun.asof_date` (the canonical snapshot date) — not the denormalized `ForwardReturn.asof_date`
     # — so it is exactly the "snapshots dated <= D" membership the expanding walk-forward window requires.
-    fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
+    #
+    # iter-14: column-projected to the 4 fields actually read (run_id, symbol, realized_return,
+    # max_drawdown) and consumed via `yield_per(batch)` — bounded memory on the horizon-partition scan.
+    # `ret_by_run_symbol`/`mdd_by_run_symbol`/`runs_with_fr_set` are built incrementally per streamed row;
+    # dict/set construction is order-independent, so this is byte-identical to the prior two full-row
+    # dict comprehensions + sorted-set-of-attribute pattern.
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown,
+    ).where(ForwardReturn.horizon == horizon)
     if as_of is not None:
         fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
             ScannerRun.asof_date <= as_of
         )
-    fr_rows = session.exec(fr_stmt).all()
-    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
+    ret_by_run_symbol: dict[tuple[int, str], float] = {}
     # iter-27 (J-86): the stored max_drawdown for each (run, symbol) at this horizon, read VERBATIM — so
     # the aggregate mean-MDD is a read-only grouping of the SAME stored values (no recomputed drawdown).
-    mdd_by_run_symbol = {(fr.run_id, fr.symbol): fr.max_drawdown for fr in fr_rows}
-    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
-
-    results = (
-        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
-        if runs_with_fr else []
-    )
+    mdd_by_run_symbol: dict[tuple[int, str], Optional[float]] = {}
+    runs_with_fr_set: set[int] = set()
+    for fr_run_id, fr_symbol, fr_realized_return, fr_max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        ret_by_run_symbol[(fr_run_id, fr_symbol)] = fr_realized_return
+        mdd_by_run_symbol[(fr_run_id, fr_symbol)] = fr_max_drawdown
+        runs_with_fr_set.add(fr_run_id)
+    runs_with_fr = sorted(runs_with_fr_set)
+
+    # NOTE: `run_rows` stays a materialized `.all()` (unchanged, iter-14 scope) — one `ScannerRun` per
+    # cadence date (bounded, small; ~180+ total on the current deep basis), not one of the two named
+    # unbounded offenders this iteration fixes.
     run_rows = (
         session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
         if runs_with_fr else []
@@ -834,28 +863,47 @@ def compute_forward_aggregates(
 
     # Per-stock observations: each stored result joined to its stored realized return at this horizon.
     # The bucket / setup / sector / rank / regime are READ from the snapshot — never recomputed here.
+    #
+    # iter-14: column-projected to the 8 fields actually read below and consumed via `yield_per(batch)` —
+    # bounded memory on the `ScannerResult` scan (the largest table, `record_json` blobs excluded from the
+    # projection entirely). Ordered by `ScannerResult.id` — mirroring `research._subject_matching_result_
+    # rows`'s established precedent for this exact table/concern — so the streamed scan reproduces the
+    # SAME row order the prior un-ordered `.all()` naturally returned (SQLite's default rowid-ascending
+    # scan for a simple single-table `WHERE run_id IN (...)` query), keeping `stock_obs`'s content AND
+    # order byte-identical. `stock_obs` is built directly in the loop with the SAME `if realized is None:
+    # continue` NA gate as before.
     stock_obs: list[dict] = []
-    for res in results:
-        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
-        if realized is None:
-            continue  # this stock has no realized return at this horizon in this run (n=0 contribution)
-        stock_obs.append({
-            "run_id": res.run_id,
-            "ticker": res.ticker,
-            "return": realized,
-            # iter-27 (J-86): the stored max_drawdown for this observation (read verbatim) — paired to the
-            # return so the aggregate mean-MDD groups exactly the same observation set as the mean return.
-            "max_drawdown": mdd_by_run_symbol.get((res.run_id, res.ticker)),
-            "bucket": res.leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
-            "setup": res.setup_status,         # stored canonical setup status (verbatim)
-            "sector": res.sector,
-            "rank": res.rank,
-            "regime": regime_by_run.get(res.run_id),  # stored regime label for the run
-            "is_vcp": res.is_vcp,              # stored VCP flag (verbatim — never re-detected here)
-            # stored new-pattern flags (verbatim — never re-detected here), iter-9
-            "is_pullback_to_rising_dma": res.is_pullback_to_rising_dma,
-            "is_flat_base_breakout": res.is_flat_base_breakout,
-        })
+    if runs_with_fr:
+        res_stmt = select(
+            ScannerResult.run_id, ScannerResult.ticker, ScannerResult.leadership_bucket,
+            ScannerResult.setup_status, ScannerResult.sector, ScannerResult.rank,
+            ScannerResult.is_vcp, ScannerResult.is_pullback_to_rising_dma, ScannerResult.is_flat_base_breakout,
+        ).where(ScannerResult.run_id.in_(runs_with_fr)).order_by(ScannerResult.id)
+        for (
+            res_run_id, ticker, leadership_bucket, setup_status, sector, rank,
+            is_vcp, is_pullback_to_rising_dma, is_flat_base_breakout,
+        ) in session.exec(res_stmt).yield_per(batch):
+            realized = ret_by_run_symbol.get((res_run_id, ticker))
+            if realized is None:
+                continue  # this stock has no realized return at this horizon in this run (n=0 contribution)
+            stock_obs.append({
+                "run_id": res_run_id,
+                "ticker": ticker,
+                "return": realized,
+                # iter-27 (J-86): the stored max_drawdown for this observation (read verbatim) — paired to
+                # the return so the aggregate mean-MDD groups exactly the same observation set as the mean
+                # return.
+                "max_drawdown": mdd_by_run_symbol.get((res_run_id, ticker)),
+                "bucket": leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
+                "setup": setup_status,         # stored canonical setup status (verbatim)
+                "sector": sector,
+                "rank": rank,
+                "regime": regime_by_run.get(res_run_id),  # stored regime label for the run
+                "is_vcp": is_vcp,              # stored VCP flag (verbatim — never re-detected here)
+                # stored new-pattern flags (verbatim — never re-detected here), iter-9
+                "is_pullback_to_rising_dma": is_pullback_to_rising_dma,
+                "is_flat_base_breakout": is_flat_base_breakout,
+            })
 
     stock_returns = [o["return"] for o in stock_obs]
     overall_mean = _mean_or_none(stock_returns)
diff --git a/apps/backend/tests/test_forward_testing_aggregates_streaming.py b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
new file mode 100644
index 00000000..6e3745b0
--- /dev/null
+++ b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
@@ -0,0 +1,303 @@
+"""ops-hardening iter-14 (J-07, AG-8 REGRESSION recovery) — byte-identity proof for the bounded/streamed
+rewrite of `compute_forward_aggregates`'s two whole-partition ORM reads
+(`apps/backend/app/engine/forward_testing.py`): the `ForwardReturn` scan (`fr_stmt` / `.all()`) and the
+`ScannerResult` scan (`select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`). Both
+were replaced with column-projected, `yield_per(cfg.research.read_batch_size)`-streamed reads (mirroring
+this module's own `_streamed_existing_keys` and `research.py`'s `_subject_matching_result_rows` /
+`_event_study_members` precedent) because both tables had grown ~9x since first measured and the unbounded
+pattern was the confirmed root cause of this session's two full-availability outages (iter-7, iter-13).
+
+`_reference_compute_forward_aggregates` below is a PINNED COPY of the pre-rewrite function body (the two
+whole-partition `.all()` reads), calling the SAME unchanged downstream helpers
+(`benchmark_symbols`/`_group_means`/`_control_groups`/`_attribution_slices`/`_mean_or_none`) the real,
+rewritten function still uses. Any divergence between the real function's output and this reference can
+therefore only come from the two rewritten read steps, never from a second aggregation formula — this is
+the "capture the original's output ... or keep a reference implementation in the test" fixture-backed
+equality proof the iter-14 plan calls for (TC-1/TC-2).
+"""
+from __future__ import annotations
+
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine.forward_testing import (
+    BUCKET_ORDER,
+    FLAT_BASE_LABELS,
+    PULLBACK_LABELS,
+    SURVIVORSHIP_BIAS_LABEL,
+    VCP_LABELS,
+    _attribution_slices,
+    _control_groups,
+    _group_means,
+    _mean_or_none,
+    benchmark_symbols,
+    compute_forward_aggregates,
+)
+from app.engine.setups import ALL_STATUSES
+from app.models import ForwardReturn, ScannerResult, ScannerRun
+
+# --------------------------------------------------------------------------------------------------
+# Pinned pre-rewrite reference implementation (the two `.all()` reads this iteration replaces)
+# --------------------------------------------------------------------------------------------------
+def _reference_compute_forward_aggregates(session: Session, horizon: int, config, *, as_of=None) -> dict:
+    cfg = config
+    bm = benchmark_symbols(cfg)
+
+    fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
+    if as_of is not None:
+        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+            ScannerRun.asof_date <= as_of
+        )
+    fr_rows = session.exec(fr_stmt).all()
+    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
+    mdd_by_run_symbol = {(fr.run_id, fr.symbol): fr.max_drawdown for fr in fr_rows}
+    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
+
+    results = (
+        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    run_rows = (
+        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    regime_by_run = {run.id: run.regime_label for run in run_rows}
+
+    stock_obs: list[dict] = []
+    for res in results:
+        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
+        if realized is None:
+            continue
+        stock_obs.append({
+            "run_id": res.run_id,
+            "ticker": res.ticker,
+            "return": realized,
+            "max_drawdown": mdd_by_run_symbol.get((res.run_id, res.ticker)),
+            "bucket": res.leadership_bucket,
+            "setup": res.setup_status,
+            "sector": res.sector,
+            "rank": res.rank,
+            "regime": regime_by_run.get(res.run_id),
+            "is_vcp": res.is_vcp,
+            "is_pullback_to_rising_dma": res.is_pullback_to_rising_dma,
+            "is_flat_base_breakout": res.is_flat_base_breakout,
+        })
+
+    stock_returns = [o["return"] for o in stock_obs]
+    overall_mean = _mean_or_none(stock_returns)
+    overall_mdds = [o["max_drawdown"] for o in stock_obs if o["max_drawdown"] is not None]
+    overall_mean_mdd = _mean_or_none(overall_mdds)
+    spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
+    qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]
+    spy_mean = _mean_or_none(spy_returns)
+    qqq_mean = _mean_or_none(qqq_returns)
+
+    excess = {
+        "vs_spy": {
+            "benchmark": bm["spy"],
+            "mean_excess": (overall_mean - spy_mean) if (overall_mean is not None and spy_mean is not None) else None,
+            "stock_mean": overall_mean,
+            "benchmark_mean": spy_mean,
+            "n": len(stock_returns),
+            "benchmark_n": len(spy_returns),
+        },
+        "vs_qqq": {
+            "benchmark": bm["qqq"],
+            "mean_excess": (overall_mean - qqq_mean) if (overall_mean is not None and qqq_mean is not None) else None,
+            "stock_mean": overall_mean,
+            "benchmark_mean": qqq_mean,
+            "n": len(stock_returns),
+            "benchmark_n": len(qqq_returns),
+        },
+    }
+
+    asof_dates = sorted((run.asof_date.isoformat() for run in run_rows), reverse=True)
+
+    by_vcp = [
+        {"vcp": VCP_LABELS[row["vcp"]], "mean_return": row["mean_return"],
+         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
+        for row in _group_means(stock_obs, "is_vcp", "vcp", [True, False], pad=True)
+    ]
+    by_pullback_to_rising_dma = [
+        {"pullback_to_rising_dma": PULLBACK_LABELS[row["pullback_to_rising_dma"]], "mean_return": row["mean_return"],
+         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
+        for row in _group_means(stock_obs, "is_pullback_to_rising_dma", "pullback_to_rising_dma", [True, False], pad=True)
+    ]
+    by_flat_base_breakout = [
+        {"flat_base_breakout": FLAT_BASE_LABELS[row["flat_base_breakout"]], "mean_return": row["mean_return"],
+         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
+        for row in _group_means(stock_obs, "is_flat_base_breakout", "flat_base_breakout", [True, False], pad=True)
+    ]
+
+    return {
+        "horizon": horizon,
+        "horizons": list(cfg.walk_forward.horizons),
+        "default_horizon": cfg.walk_forward.default_horizon,
+        "min_sample": cfg.walk_forward.min_sample,
+        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
+        "n_runs": len(runs_with_fr),
+        "asof_dates": asof_dates,
+        "overall": {"mean_return": overall_mean, "mean_max_drawdown": overall_mean_mdd, "n": len(stock_returns)},
+        "by_bucket": _group_means(stock_obs, "bucket", "bucket", BUCKET_ORDER, pad=True),
+        "by_setup": _group_means(stock_obs, "setup", "setup", ALL_STATUSES, pad=False),
+        "by_regime": _group_means(stock_obs, "regime", "regime", cfg.regime.labels, pad=False),
+        "by_vcp": by_vcp,
+        "by_pullback_to_rising_dma": by_pullback_to_rising_dma,
+        "by_flat_base_breakout": by_flat_base_breakout,
+        "excess": excess,
+        "control_group": _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg),
+        "attribution": _attribution_slices(stock_obs, cfg),
+    }
+
+
+# --------------------------------------------------------------------------------------------------
+# Fixture: multi-run, multi-sector, multi-horizon snapshot basis (small, hand-built — no seed load)
+# --------------------------------------------------------------------------------------------------
+HORIZONS = (1, 5, 10, 20, 60)
+# ticker -> (sector, bucket, setup, rank, is_vcp, is_pullback, is_flat_base) — CONSTANT across every run
+# this ticker appears in (a real stock's sector/pattern-detector identity does not flip run to run; this
+# also sidesteps the one theoretical order-sensitivity this file's plan review flagged: `_per_stock_
+# attribution`'s `sector_by_ticker.setdefault` picks whichever occurrence is seen FIRST — with a single
+# constant sector per ticker, every occurrence agrees, so stream order can never change the result).
+_STOCKS = {
+    "AAA": ("Technology", "A", "Actionable", 1, True, False, False),
+    "BBB": ("Technology", "A", "Breakout-watch", 5, False, True, False),
+    "CCC": ("Energy", "B", "Pullback-watch", 12, True, False, False),
+    "DDD": ("Energy", "C", "Avoid", 25, False, True, False),
+    "EEE": ("Financials", "D", "Risk-off-watchlist", 45, False, False, True),
+    "FFF": ("Financials", "E", "Avoid", 60, False, False, False),
+    "GGG": ("Technology", "B", "Actionable", 90, False, False, True),
+    "HHH": ("Energy", "E", "Extended", 150, False, False, False),
+}
+_BENCHMARKS = ("SPY", "QQQ", "XLK", "XLE")
+# (asof_date, regime_label) — r4 is the newest snapshot; a historical as_of at r3's date excludes it.
+_RUNS = (
+    (date(2024, 1, 15), "Risk-off"),
+    (date(2024, 4, 15), "Risk-on"),
+    (date(2024, 7, 15), "Risk-on"),
+    (date(2025, 1, 15), "Risk-off"),
+)
+HISTORICAL_AS_OF = date(2024, 7, 15)  # == r3's date; excludes r4 (the newest snapshot)
+
+
+def _utc() -> datetime:
+    return datetime.now(timezone.utc)
+
+
+def _fr_value(run_idx: int, key_idx: int, horizon: int) -> float:
+    """A deterministic, distinct-per-(run, key, horizon) pseudo-return — no two cells collide, so a
+    misaligned column projection or a dropped row would show up as a wrong mean rather than a coincidental
+    match."""
+    return round(0.01 * (run_idx + 1) + 0.002 * key_idx - 0.0001 * horizon, 6)
+
+
+@pytest.fixture()
+def multi_run_engine(tmp_path):
+    """4 runs across distinct dates, 8 stocks over 3 real config sectors (Technology/Energy/Financials),
+    ranks spanning all 3 config rank bands, a mix of VCP/pullback/flat-base flags, both Risk-on and
+    Risk-off regimes, and forward returns at all 5 configured horizons for every stock + the 4 benchmark
+    symbols (SPY/QQQ/XLK/XLE) in every run — plus a 5th run with ScannerResults but NO forward returns at
+    all (the n=0 / zero-post-bar case, `runs_with_fr` must exclude it)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'multi.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for run_idx, (asof, regime) in enumerate(_RUNS):
+            run = ScannerRun(
+                asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
+                regime_score=50.0, regime_label=regime, regime_components_json="[]",
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.flush()
+            for ticker, (sector, bucket, setup, rank, is_vcp, is_pullback, is_flat_base) in _STOCKS.items():
+                session.add(ScannerResult(
+                    run_id=run.id, ticker=ticker, name=ticker, sector=sector,
+                    leadership_score=50.0, leadership_bucket=bucket,
+                    entry_quality_score=0.0, entry_quality_bucket="E",
+                    risk_score=0.0, risk_bucket="E",
+                    setup_status=setup, rank=rank, record_json="{}",
+                    is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback, is_flat_base_breakout=is_flat_base,
+                ))
+            for key_idx, symbol in enumerate(list(_STOCKS) + list(_BENCHMARKS)):
+                for horizon in HORIZONS:
+                    session.add(ForwardReturn(
+                        run_id=run.id, symbol=symbol, horizon=horizon,
+                        asof_date=asof, entry_close=100.0, measured_date=date(2025, 12, 31),
+                        realized_return=_fr_value(run_idx, key_idx, horizon),
+                        max_drawdown=-abs(_fr_value(run_idx, key_idx, horizon)) / 2,
+                    ))
+        # 5th run: ScannerResults exist but ZERO forward returns (the honest n=0 case) — dated even later
+        # than r4 so it is also excluded by HISTORICAL_AS_OF, and its own bucket/rank should never
+        # contribute to any as_of=None aggregate either (no realized return -> the NA gate drops it).
+        r5 = ScannerRun(
+            asof_date=date(2025, 6, 15), created_at=_utc(), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(r5)
+        session.flush()
+        session.add(ScannerResult(
+            run_id=r5.id, ticker="AAA", name="AAA", sector="Technology",
+            leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0, entry_quality_bucket="E",
+            risk_score=0.0, risk_bucket="E", setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.commit()
+    return engine
+
+
+# --------------------------------------------------------------------------------------------------
+# TC-1 / TC-2 — byte-identity across all 5 horizons x {as_of=None, a historical as_of}, at several
+# streaming batch sizes (proves the rewrite's behavior is independent of the chunk size)
+# --------------------------------------------------------------------------------------------------
+@pytest.mark.parametrize("batch", [1, 3, 1_000_000])
+@pytest.mark.parametrize("horizon", HORIZONS)
+@pytest.mark.parametrize("as_of", [None, HISTORICAL_AS_OF])
+def test_compute_forward_aggregates_byte_identical_to_pre_rewrite_reference(
+    multi_run_engine, batch, horizon, as_of
+):
+    """TC-1/TC-2: the rewritten (column-projected, `yield_per`-streamed) `compute_forward_aggregates`
+    returns a dict `==` to the pinned pre-rewrite reference implementation, for every configured horizon,
+    with `as_of=None` and with a historical `as_of` that excludes the newest snapshot — at streaming batch
+    sizes smaller than, equal to, and far larger than the fixture's row count, so the equality does not
+    depend on any particular chunking."""
+    cfg = load_config()
+    cfg = cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})
+    with Session(multi_run_engine) as session:
+        new_payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+        reference_payload = _reference_compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+
+    assert new_payload == reference_payload, (
+        f"byte-identity broken at horizon={horizon} as_of={as_of} batch={batch}"
+    )
+    # sanity: the fixture is non-trivial for every horizon/as_of combination exercised here (a passing
+    # equality check on two empty dicts would prove nothing about the rewrite).
+    assert new_payload["overall"]["n"] > 0
+    assert new_payload["n_runs"] > 0
+
+
+def test_compute_forward_aggregates_as_of_excludes_newest_snapshot_from_reference_too(multi_run_engine):
+    """Sanity check on the fixture's own `as_of` design: the historical cutoff genuinely narrows the pool
+    relative to `as_of=None` (both on the new function and the reference), so the parametrized byte-
+    identity test above is not silently comparing two identical all-history reads under the "as_of" label."""
+    cfg = load_config()
+    with Session(multi_run_engine) as session:
+        all_history = compute_forward_aggregates(session, 20, cfg, as_of=None)
+        scoped = compute_forward_aggregates(session, 20, cfg, as_of=HISTORICAL_AS_OF)
+    assert scoped["n_runs"] < all_history["n_runs"]
+    assert scoped["overall"]["n"] < all_history["overall"]["n"]
+
+
+def test_compute_forward_aggregates_zero_fr_run_excluded_from_runs_with_fr(multi_run_engine):
+    """The 5th run (ScannerResults but zero ForwardReturn rows) never enters `runs_with_fr` — its
+    `asof_date` (2025-06-15, the actual latest ScannerRun) must not appear in `asof_dates`, on both the
+    rewritten function and the reference."""
+    cfg = load_config()
+    with Session(multi_run_engine) as session:
+        new_payload = compute_forward_aggregates(session, 20, cfg, as_of=None)
+        reference_payload = _reference_compute_forward_aggregates(session, 20, cfg, as_of=None)
+    assert "2025-06-15" not in new_payload["asof_dates"]
+    assert new_payload == reference_payload
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
new file mode 100644
index 00000000..8d35d5cf
--- /dev/null
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -0,0 +1,280 @@
+"""ops-hardening iter-14 (J-07, AG-8 REGRESSION recovery) — TC-3 (a REAL, non-monkeypatched tightened-
+`ulimit -v` memory-pressure induction) and TC-4 (a concurrent-caller regression) for the bounded/streamed
+`compute_forward_aggregates` rewrite in `apps/backend/app/engine/forward_testing.py`.
+
+WHY A REAL SUBPROCESS INDUCTION (TC-3), NOT A MONKEYPATCH: the repo's existing
+`test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds`-style tests
+(`test_data_manager.py`) all `monkeypatch`-inject a `MemoryError` at a chosen call boundary — that style
+did NOT catch iter-11's live 500s or iter-13's live ~12-minute wedge, because it never exercises a real
+OS-level virtual-memory exhaustion inside SQLAlchemy/sqlite's own internals. TC-3 spawns a real Python
+subprocess under a genuinely tightened `ulimit -v` (RLIMIT_AS) against a fixture sized so the PRE-REWRITE
+unbounded `.all()` pattern needs materially more virtual memory than the cap allows, while the REWRITTEN
+column-projected/streamed pattern comfortably fits under the SAME cap — proving both (a) the fix actually
+closes the gap, and (b) even the pattern that DOES still fail under real memory pressure fails HONESTLY
+(a clean `MemoryError`, no hang) with the DB still usable afterward.
+
+CALIBRATION (measured on this host, `.venv` Python 3.12, 60,000 `ScannerResult`+`ForwardReturn` rows at
+one horizon, `record_json` padded to 4,000 bytes — mirroring the real table's dominant per-row cost, the
+reason `scanner_results` is this project's largest table): baseline (import app + open session) VmPeak
+~99-100 MB; the OLD pre-rewrite whole-partition `.all()` pattern measured ~587 MB (601,524 KB); the NEW
+rewritten column-projected + `yield_per`-streamed pattern measured ~255 MB (260,720 KB). `CAP_KB` below
+(420,000 KB / ~410 MB) sits comfortably between the two — OLD is short by ~181,524 KB, NEW has ~159,280 KB
+of margin — and is verified empirically by the tests below (not just asserted).
+
+TC-4 mirrors iter-13's actual trigger shape (4 concurrent backfills' finalize hooks + a diagnostic read,
+not a single sequential process) with a `ThreadPoolExecutor`: each thread opens its OWN `Session` against
+a SHARED file-based engine — the same way a real multi-threaded ASGI server's request-handling threads
+each independently call into `compute_forward_aggregates`/`forward_aggregates_cached`.
+"""
+from __future__ import annotations
+
+import subprocess
+import sys
+import time
+from concurrent.futures import ThreadPoolExecutor, as_completed
+from datetime import date, datetime, timezone
+from pathlib import Path
+
+import pytest
+from sqlalchemy import insert
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine.forward_testing import compute_forward_aggregates, forward_aggregates_cached
+from app.models import ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
+
+BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)  # apps/backend — for the child subprocess's sys.path
+HORIZON = 20  # cfg.walk_forward.default_horizon
+N_ROWS = 60_000
+RECORD_JSON_BYTES = 4_000  # mirrors the real table's dominant per-row cost (record_json blobs)
+# Empirically measured cap (see module docstring): traps the OLD unbounded `.all()` pattern (~587 MB
+# need) while the NEW streamed pattern (~255 MB need) comfortably fits under it, with margin on both sides.
+CAP_KB = 420_000
+# Generous vs. the real `database.pragmas.busy_timeout_ms` (30s) — a hang would exceed this; a clean
+# failure or success (even one that legitimately waits out a SQLite busy-timeout) will not.
+BOUNDED_TIMEOUT_S = 45.0
+
+
+def _build_memory_pressure_db(db_path: Path) -> None:
+    """60,000 `ScannerResult` + `ForwardReturn` rows at `HORIZON`, bulk-inserted (mirrors this test
+    suite's own `insert(Table.__table__)` convention, e.g. `test_indexes.py`/`test_sectors.py`) for
+    build speed, plus ONE pre-populated `ForwardAggregateCache` row (via the real, unconstrained
+    rewritten path) so TC-3's "subsequent read... re-reading an existing ForwardAggregateCache row" has
+    a real row to target."""
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    padding = "x" * RECORD_JSON_BYTES
+    cfg = load_config()
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
+            for i in range(N_ROWS)
+        ]
+        session.execute(insert(ScannerResult.__table__), result_rows)
+        fr_rows = [
+            dict(
+                run_id=run_id, symbol=f"SYM{i:06d}", horizon=HORIZON, asof_date=date(2025, 1, 15),
+                entry_close=100.0, measured_date=date(2025, 2, 15), realized_return=0.01, max_drawdown=-0.02,
+            )
+            for i in range(N_ROWS)
+        ]
+        session.execute(insert(ForwardReturn.__table__), fr_rows)
+        session.commit()
+        forward_aggregates_cached(session, HORIZON, cfg, as_of=None)
+
+
+@pytest.fixture(scope="module")
+def memory_pressure_db(tmp_path_factory) -> Path:
+    db_path = tmp_path_factory.mktemp("mem_pressure") / "mem.db"
+    _build_memory_pressure_db(db_path)
+    return db_path
+
+
+# --------------------------------------------------------------------------------------------------
+# TC-3 child-process probe: written to a temp .py file and run via
+# `bash -c "ulimit -v <cap>; exec <python> <script> <db> <mode>"` (the plan's own suggested spawn shape)
+# so the cap applies to the CHILD subprocess only, never to this pytest process itself.
+# --------------------------------------------------------------------------------------------------
+_CHILD_PROBE_TEMPLATE = '''
+import sys
+sys.path.insert(0, "__BACKEND_ROOT__")
+from sqlmodel import Session, select
+from app.config import load_config
+from app.db import make_engine
+from app.models import ForwardReturn, ScannerResult, ForwardAggregateCache
+from app.engine.forward_testing import compute_forward_aggregates
+
+db_path, mode, horizon = sys.argv[1], sys.argv[2], int(sys.argv[3])
+engine = make_engine(f"sqlite:///{db_path}")
+cfg = load_config()
+
+
+def old_unbounded_read(session, horizon):
+    """A verbatim copy of the PRE-rewrite whole-partition `.all()` pattern this iteration replaced —
+    kept here only to prove the induced memory pressure is real (the defect this iteration fixes), never
+    reintroduced into the shipped module."""
+    fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
+    fr_rows = session.exec(fr_stmt).all()
+    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
+    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
+    results = (
+        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    stock_obs = [
+        {"ticker": res.ticker, "return": ret_by_run_symbol.get((res.run_id, res.ticker))}
+        for res in results
+    ]
+    return len(stock_obs)
+
+
+if mode == "old":
+    try:
+        with Session(engine) as session:
+            n = old_unbounded_read(session, horizon)
+        print(f"UNEXPECTED_SUCCESS n={n}")
+    except MemoryError:
+        print("GOT_MEMORYERROR")
+        # a fresh session, in the SAME process, re-reading an EXISTING ForwardAggregateCache row —
+        # proves no leaked lock/open transaction blocks recovery without a process restart.
+        with Session(engine) as session:
+            row = session.exec(
+                select(ForwardAggregateCache).where(ForwardAggregateCache.horizon == horizon)
+            ).first()
+        print("SUBSEQUENT_READ_OK" if row is not None else "SUBSEQUENT_READ_FAILED_NO_ROW")
+else:
+    try:
+        with Session(engine) as session:
+            agg = compute_forward_aggregates(session, horizon, cfg, as_of=None)
+        n = agg["overall"]["n"]
+        print(f"SUCCESS n={n}")
+    except MemoryError:
+        print("UNEXPECTED_MEMORYERROR")
+'''
+
+
+def _write_child_probe(tmp_path: Path) -> Path:
+    script_path = tmp_path / "_mem_probe_child.py"
+    script_path.write_text(_CHILD_PROBE_TEMPLATE.replace("__BACKEND_ROOT__", BACKEND_ROOT))
+    return script_path
+
+
+def _run_child_probe(script_path: Path, db_path: Path, mode: str, cap_kb: int) -> subprocess.CompletedProcess:
+    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path} {mode} {HORIZON}"
+    return subprocess.run(
+        ["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S,
+    )
+
+
+def test_tc3_old_unbounded_pattern_fails_honestly_under_real_memory_cap_and_recovers(
+    memory_pressure_db, tmp_path
+):
+    """TC-3 (part 1): under a REAL, non-monkeypatched `ulimit -v` cap sized below what the pre-rewrite
+    unbounded pattern needs, invoking that pattern raises `MemoryError` cleanly — no hang, no timeout —
+    and a subsequent fresh-session read of an EXISTING `ForwardAggregateCache` row, in the SAME process,
+    succeeds immediately afterward (no leaked lock / open transaction blocks recovery)."""
+    script_path = _write_child_probe(tmp_path)
+    start = time.monotonic()
+    result = _run_child_probe(script_path, memory_pressure_db, "old", CAP_KB)
+    elapsed = time.monotonic() - start
+
+    assert elapsed < BOUNDED_TIMEOUT_S, f"child probe took {elapsed:.1f}s — treat as a hang, not a slow pass"
+    assert "UNEXPECTED_SUCCESS" not in result.stdout, (
+        f"the OLD unbounded pattern completed successfully under a {CAP_KB} KB cap — the cap is "
+        f"miscalibrated (too loose) for this fixture; stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+    assert "GOT_MEMORYERROR" in result.stdout, (
+        f"expected an honest MemoryError under the tightened cap; stdout={result.stdout!r} "
+        f"stderr={result.stderr!r}"
+    )
+    assert "SUBSEQUENT_READ_OK" in result.stdout, (
+        f"expected the same-process subsequent read to succeed after the MemoryError; "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+
+
+def test_tc3_rewritten_pattern_succeeds_under_the_same_cap_that_broke_the_old_one(
+    memory_pressure_db, tmp_path
+):
+    """TC-3 (part 2, the fix proof): the REWRITTEN `compute_forward_aggregates`, invoked under the
+    IDENTICAL `ulimit -v` cap that just broke the pre-rewrite pattern (previous test) against the SAME
+    fixture, completes successfully — the bounded/streamed read needs materially less virtual memory."""
+    script_path = _write_child_probe(tmp_path)
+    start = time.monotonic()
+    result = _run_child_probe(script_path, memory_pressure_db, "new", CAP_KB)
+    elapsed = time.monotonic() - start
+
+    assert elapsed < BOUNDED_TIMEOUT_S, f"child probe took {elapsed:.1f}s — treat as a hang, not a slow pass"
+    assert "UNEXPECTED_MEMORYERROR" not in result.stdout, (
+        f"the REWRITTEN bounded/streamed path hit MemoryError under the same {CAP_KB} KB cap the OLD "
+        f"path needed to fail at — the fix does not hold at this fixture size; "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+    assert f"SUCCESS n={N_ROWS}" in result.stdout, (
+        f"expected the rewritten path to succeed with all {N_ROWS} observations; "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+
+
+# --------------------------------------------------------------------------------------------------
+# TC-4 — concurrent-caller regression (mirrors iter-13's actual trigger shape: 4 concurrent backfills'
+# finalize hooks + a diagnostic read, all targeting the SAME horizon's cache key at once)
+# --------------------------------------------------------------------------------------------------
+def _cached_caller(engine, horizon: int) -> dict:
+    cfg = load_config()
+    with Session(engine) as session:
+        return forward_aggregates_cached(session, horizon, cfg, as_of=None)
+
+
+def _direct_caller(engine, horizon: int) -> dict:
+    cfg = load_config()
+    with Session(engine) as session:
+        return compute_forward_aggregates(session, horizon, cfg, as_of=None)
+
+
+def test_tc4_concurrent_callers_all_complete_within_bounded_timeout(memory_pressure_db):
+    """TC-4: 4 concurrent `forward_aggregates_cached` callers (mirroring 4 concurrent backfills' finalize
+    hooks, all racing to warm/serve the SAME `(horizon, asof_key, dataset_version)` cache key — the
+    `ForwardAggregateCache` unique-constraint race `forward_aggregates_cached`'s own
+    `except Exception: session.rollback()` is designed to absorb) plus 1 direct/uncached
+    `compute_forward_aggregates` caller (the 'diagnostic read' in iter-13's own trigger shape) — every
+    caller returns within a bounded timeout, none left blocked, and every returned payload is byte-
+    identical (the cache race changes WHO persists, never WHAT is computed)."""
+    engine = make_engine(f"sqlite:///{memory_pressure_db}")
+    n_cached_callers = 4
+
+    with ThreadPoolExecutor(max_workers=n_cached_callers + 1) as pool:
+        futures = [pool.submit(_cached_caller, engine, HORIZON) for _ in range(n_cached_callers)]
+        futures.append(pool.submit(_direct_caller, engine, HORIZON))
+
+        results = []
+        errors = []
+        for future in as_completed(futures, timeout=BOUNDED_TIMEOUT_S):
+            try:
+                results.append(future.result())
+            except Exception as exc:  # a clean, isolated failure is acceptable — a hang is not
+                errors.append(exc)
+
+    assert len(results) + len(errors) == n_cached_callers + 1, "not every future completed — a caller hung"
+    assert not errors, f"expected every caller to succeed cleanly (or at least return); got errors: {errors}"
+    # byte-identity across all 5 concurrent callers: the cache-race changes only WHO persists the row,
+    # never the computed VALUE — every payload must be identical to the direct/uncached read.
+    first = results[0]
+    for payload in results[1:]:
+        assert payload == first, "concurrent callers returned DIFFERENT payloads for the same horizon/as_of"
+    assert first["overall"]["n"] == N_ROWS
```
