# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-index.html      |   4 +-
 reports/goal-session-ops-hardening-retro.md        |  26 +-
 reports/perf-budgets.md                            | 229 +++++++++++++++++
 reports/security/install-decisions.jsonl           |   2 +
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 .../dispatch/req.NYZt5i.out                        |  19 --
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 runs/goal-session-ops-hardening/session.json       |   8 +-
 .../state/assumptions.md                           | 286 +++------------------
 .../state/assumptions.md.archive.md                | 247 ++++++++++++++++++
 runs/goal-session-ops-hardening/state/blueprint.md |  30 ++-
 runs/goal-session-ops-hardening/state/lessons.md   | 151 +----------
 .../state/retro-input.md                           | 158 ++++++++----
 runs/goal-session-ops-hardening/summary.md         |  88 +++++--
 runs/goal-session-ops-hardening/telemetry.jsonl    |  22 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   5 +
 18 files changed, 772 insertions(+), 511 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
