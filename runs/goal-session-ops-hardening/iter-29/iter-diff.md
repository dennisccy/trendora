# Iteration diff (bounded)

Files changed: 100. Shown in full: 64.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/scripts/automation/lib/closure_gate.py` (770 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/common.sh` (94 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/goal-gates.sh` (32 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/goal_gate.py` (21 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh` (243 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/quota-retry.sh` (81 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/telemetry.sh` (41 lines not shown)
- `incredible_auto_dev/scripts/automation/phase-audit.sh` (26 lines not shown)
- `incredible_auto_dev/scripts/automation/phase-closure-check.sh` (101 lines not shown)
- `incredible_auto_dev/scripts/automation/qa-phase.sh` (31 lines not shown)
- `incredible_auto_dev/scripts/automation/render-summary.sh` (19 lines not shown)
- `incredible_auto_dev/scripts/automation/review-phase.sh` (25 lines not shown)
- `incredible_auto_dev/scripts/automation/run-evals.sh` (21 lines not shown)
- `incredible_auto_dev/scripts/automation/run-goal.sh` (678 lines not shown)
- `incredible_auto_dev/scripts/automation/run-judgment-evals.sh` (43 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (47 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-audit-phase.sh` (26 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-impact-phase.sh` (22 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-test-design-phase.sh` (22 lines not shown)
- `incredible_auto_dev/scripts/automation/ux-regression-phase.sh` (26 lines not shown)
- `incredible_auto_dev/skills/browser-workflow-executor.md` (51 lines not shown)
- `incredible_auto_dev/skills/goal-evaluation-methodology.md` (38 lines not shown)
- `incredible_auto_dev/skills/goal-interactive-dispatch.md` (36 lines not shown)
- `incredible_auto_dev/skills/plain-language.md` (13 lines not shown)
- `incredible_auto_dev/templates/iteration-summary.md` (28 lines not shown)
- `incredible_auto_dev/tests/automation/test-closure-gate.sh` (256 lines not shown)
- `incredible_auto_dev/tests/automation/test-depth-cadence.sh` (56 lines not shown)
- `incredible_auto_dev/tests/automation/test-evidence-depth.sh` (121 lines not shown)
- `incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh` (59 lines not shown)
- `incredible_auto_dev/tests/automation/test-iter-budget.sh` (133 lines not shown)
- `incredible_auto_dev/tests/automation/test-pump-liveness.sh` (16 lines not shown)
- `incredible_auto_dev/tests/automation/test-quota-retry.sh` (17 lines not shown)
- `incredible_auto_dev/tests/automation/test-zero-change-guard.sh` (118 lines not shown)
- `project-extensions/host-guard/README.md` (123 lines not shown)
- `project-extensions/host-guard/host-guard.env` (50 lines not shown)
- `project-extensions/host-guard/hwmon-log.sh` (216 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 49b613bc..0f390020 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1325,6 +1325,15 @@ class ResearchCfg(BaseModel):
     model_config = ConfigDict(extra="allow")
     factor_lab: FactorLabCfg
     read_batch_size: int
+    # iter-29 audit (AG-8) — the RUN-COUNT width of `_factor_observations`'s join-accumulator chunk. It is a
+    # DIFFERENT unit from `read_batch_size` (which counts ROWS for `yield_per`), and reusing the row knob as
+    # a run width is exactly how the iter-29 bound came to be inert: at 2000 runs/chunk against a live basis
+    # of 1,812-1,871 distinct runs per horizon, the loop degenerated to ONE chunk and the accumulator still
+    # held every (run_id, symbol) pair at once (792,507 measured at h=20 — 0% below the pre-fix peak). The
+    # peak accumulator is `this x symbols-per-run` (~429 today), so this must stay WELL below the live run
+    # count to bind at all. Boot-validated `>= 1`; defaulted so a config (and the inline test fixtures)
+    # predating it still loads — the SINGLE source of the width (no literal in research.py, a CALC_FILE).
+    factor_join_run_chunk: int = 100
     # iter-55 (J-112) — the rows-per-page of the Regime × Phase × Factor ranked combination table. The
     # pagination is a pure CLIENT-SIDE view transform (re-orders/pages only — recomputes/refetches nothing);
     # this is the SINGLE source of the 30-rows/page constant (goal.md), served in the lab payload so the
@@ -1348,6 +1357,8 @@ class ResearchCfg(BaseModel):
     def _validate(self) -> "ResearchCfg":
         if self.read_batch_size < 1:
             raise ValueError("research.read_batch_size must be >= 1")
+        if self.factor_join_run_chunk < 1:
+            raise ValueError("research.factor_join_run_chunk must be >= 1")
         if self.regime_phase_factor_page_size < 1:
             raise ValueError("research.regime_phase_factor_page_size must be >= 1")
         return self
diff --git a/apps/backend/app/engine/evidence.py b/apps/backend/app/engine/evidence.py
index 08093e1f..d21ff81c 100644
--- a/apps/backend/app/engine/evidence.py
+++ b/apps/backend/app/engine/evidence.py
@@ -32,6 +32,7 @@ This module consumes `app.engine.ledger` (read) + `app.engine.referee` (the PASS
 """
 from __future__ import annotations
 
+import logging
 import os
 from pathlib import Path
 from typing import Optional
@@ -42,6 +43,8 @@ from app.config import REPO_ROOT, Config, get_config
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.referee import STATUS_PASS
 
+logger = logging.getLogger("trendora.evidence")
+
 # The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime ledger
 # path may be overridden with. Forward-looking; the config default already points at the gate's ledger.
 LEDGER_PATH_ENV = "TRENDORA_LEDGER_PATH"
@@ -134,7 +137,18 @@ def build_evidence_payload(
     phase-conditional drawdown/dry-spell `expectations` payload from
     `app.engine.forward_testing.compute_drawdown_expectations` (an honestly-absent key when that returns
     `None` — an unresolvable cohort or a zero-observation cohort — never a crash, never a fabricated
-    panel)."""
+    panel).
+
+    ops-hardening iter-29 (AG-8): the per-claim compute call is wrapped in an isolate-and-continue guard,
+    mirroring the EXISTING per-claim `MemoryError`-then-continue convention `data_manager.py`'s
+    drawdown-expectations ingest warm loop already uses (`data_manager.py:3361`) — but, unlike that
+    BACKGROUND warm loop (which may abort its remaining claims under memory pressure), this is a LIVE
+    request path: a compute failure (`MemoryError` or any other exception) for one claim NEVER aborts the
+    rest of this response, so it always logs + continues to the next entry, never breaks. On a caught
+    failure that claim's row omits `expectations` and instead carries `expectations_status: "unavailable"`
+    — additive ONLY on the exception path; the pre-existing honest-`None` case (an unresolvable cohort or a
+    zero-observation cohort, returned without raising) is UNCHANGED — no `expectations` key, no
+    `expectations_status` key, exactly as before this iteration."""
     claims: list[dict] = []
     proven_signals: dict[str, dict] = {}
     for entry in read_entries(ledger_path):
@@ -150,9 +164,26 @@ def build_evidence_payload(
             # J-15 latency budget by the claim count (see the cache's own docstring for the measurement).
             from app.engine.forward_testing import compute_drawdown_expectations_cached
 
-            expectations = compute_drawdown_expectations_cached(session, row["claim"], config)
-            if expectations is not None:
-                row["expectations"] = expectations
+            try:
+                expectations = compute_drawdown_expectations_cached(session, row["claim"], config)
+            except MemoryError as exc:
+                # isolate-and-continue (AG-8): unlike the ingest warm loop's break-on-MemoryError, a live
+                # `/evidence` response must still render every OTHER claim — never abort the rest of the
+                # page over one claim's compute pressure.
+                logger.exception(
+                    "evidence per-claim drawdown-expectations compute aborted — memory pressure, "
+                    "continuing to the next claim: %s", exc,
+                )
+                row["expectations_status"] = "unavailable"
+            except Exception as exc:  # noqa: BLE001 — isolate-and-continue: one claim's failure must
+                # never blank the whole /evidence response for every other claim.
+                logger.exception(
+                    "evidence per-claim drawdown-expectations compute failed (non-fatal): %s", exc,
+                )
+                row["expectations_status"] = "unavailable"
+            else:
+                if expectations is not None:
+                    row["expectations"] = expectations
         claims.append(row)
         signal = row["signal"]
         if row["proven"] and signal:
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index 1e041eea..f27255f0 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -174,6 +174,47 @@ def _extract_factor_value(res: ScannerResult, parsed: dict) -> Optional[float]:
     return None
 
 
+def _runs_with_fr(
+    session: Session, horizons: list[int], as_of: Optional[date_cls],
+) -> list[int]:
+    """The sorted DISTINCT `forward_returns.run_id`s carrying a return at ANY of `horizons` — the chunk axis
+    BOTH factor-observation builders walk (`_factor_observations` passes a single-horizon list;
+    `_all_factor_observations_by_horizon` passes every config horizon). A DISTINCT-projected read, so the
+    returned list is bounded by the RUN count (1,812-1,871 live) and never by the (run_id, symbol) PAIR count
+    the join accumulators used to materialize whole (AG-8).
+
+    `as_of` (J-32) scopes membership to snapshots with `ScannerRun.asof_date <= as_of`; `as_of=None` adds NO
+    clause -> byte-identical all-history. Applying the cutoff HERE, upstream of every derived structure,
+    is what keeps the per-slice reads below (which filter only on `run_id.in_(slice)`) no-lookahead-correct:
+    a run dated after D never enters `runs_with_fr`, so it can never enter a slice."""
+    stmt = select(ForwardReturn.run_id).where(ForwardReturn.horizon.in_(horizons))
+    if as_of is not None:
+        stmt = stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+            ScannerRun.asof_date <= as_of
+        )
+    return sorted(session.exec(stmt.distinct()).all())
+
+
+def _fr_slice_map(
+    session: Session, horizon: int, slice_run_ids: list[int], batch: int,
+) -> dict[tuple[int, str], tuple[float, Optional[float]]]:
+    """iter-29 (AG-8): the `(run_id, symbol) -> (realized_return, max_drawdown)` join map for ONE bounded
+    SLICE of run ids — `_factor_observations`'s chunk axis. Column-projected + `yield_per`-streamed exactly
+    like the pre-chunk single-pass read; the only difference is the added `run_id.in_(slice_run_ids)`
+    scope, which is what bounds this dict's LIVE size to (len(slice_run_ids) x symbols-per-run) instead of
+    the full horizon's distinct (run_id, symbol) pair count (803,042 measured live at iter-28, one horizon,
+    as_of=None — an unbounded whole-history materialization in substance, since the prior accumulator held
+    one entry per pair across ALL of `runs_with_fr` at once). A named function (not an inlined loop body)
+    so a test can wrap/instrument it to observe the live per-slice size directly (TC-1)."""
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.run_id.in_(slice_run_ids))
+    ret_by_run_symbol: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
+    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
+    return ret_by_run_symbol
+
+
 def _factor_observations(
     session: Session, factor, horizon: int, as_of: Optional[date_cls] = None,
     *, cfg: Optional[Config] = None,
@@ -189,32 +230,44 @@ def _factor_observations(
 
     `as_of` (iter-19, J-32) optionally scopes the pool to the EXPANDING WALK-FORWARD WINDOW: when set,
     ONLY snapshots with `ScannerRun.asof_date <= as_of` contribute (no run dated > D leaks). It is a
-    SINGLE membership filter on the `fr_rows` step — identical to `forward_testing.py` — so it equally
-    bounds `runs_with_fr`, `results`, `run_rows`, and the regime map (all derived from it). The cutoff is
-    the canonical `ScannerRun.asof_date` (not the denormalized `ForwardReturn.asof_date`). `as_of=None`
-    adds NO clause → byte-identical all-history."""
+    SINGLE membership filter on the `runs_with_fr` discovery step below — identical to `forward_testing.py`
+    — so it equally bounds `runs_with_fr`, every chunk's `results`, `run_rows`, and the regime map (all
+    derived from it). The cutoff is the canonical `ScannerRun.asof_date` (not the denormalized
+    `ForwardReturn.asof_date`). `as_of=None` adds NO clause → byte-identical all-history.
+
+    iter-29 (AG-8): the join accumulator used to be ONE dict holding every distinct (run_id, symbol) pair
+    across the FULL horizon's history at once (803,042 pairs measured live at iter-28, as_of=None) even
+    though the SOURCE query was already `yield_per`-streamed — an unbounded whole-history materialization
+    in substance. `runs_with_fr` is now discovered via a lightweight DISTINCT-projected query (bounded by
+    run count, never by pair count), then walked in bounded SLICES of `research.factor_join_run_chunk` run
+    ids: each slice rebuilds its own `_fr_slice_map` accumulator, streams+joins that slice's
+    `ScannerResult`s, extends `observations`, and discards the slice's dict before the next — so peak LIVE
+    accumulator size is bounded by (chunk x symbols-per-run), never by the full history. Slices walk the
+    sorted `runs_with_fr` list in non-overlapping, increasing contiguous ranges, so concatenating each
+    slice's (run_id, id)-ordered `ScannerResult` output reproduces the SAME global order the prior
+    single-pass implementation produced — byte-identical (TC-2), never re-derived.
+
+    iter-29 AUDIT: the chunk width is `research.factor_join_run_chunk` (a RUN COUNT), NOT `read_batch_size`
+    (a ROW count for `yield_per`). As first shipped this loop reused the row knob (2000) as its run width,
+    and with only 1,812-1,871 distinct runs per horizon on the live basis it produced exactly ONE chunk —
+    a bound that bound nothing (792,507-entry peak at h=20, 0% below the pre-fix figure). The two knobs are
+    now separate so the accumulator width can be sized against the RUN count it actually indexes."""
     parsed = parse_factor_source(factor.source)
     # iter-47 (J-105): column-project + stream the (possibly huge) forward-return scan so the read path is
     # bounded by config (`yield_per`) instead of materializing the whole table as ORM rows. We read only the
     # three fields the join consumes (run_id, symbol, realized_return) — projected Row values are the EXACT
     # same Python types as ORM attribute access (no coercion → byte-identical served value).
-    batch = (cfg or get_config()).research.read_batch_size
-    # iter-52 (J-109): the FR scan ALSO projects the stored `max_drawdown` (the J-86 column, read VERBATIM)
-    # so each observation carries the realized return AND its paired post-snapshot drawdown — both fed to
-    # `_deciles` (the per-decile mean-MDD beside the mean return). One added projected column; no extra read.
-    fr_stmt = select(
-        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
-    ).where(ForwardReturn.horizon == horizon)
-    if as_of is not None:
-        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
-            ScannerRun.asof_date <= as_of
-        )
-    ret_by_run_symbol: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
-    runs_with_fr_set: set[int] = set()
-    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
-        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
-        runs_with_fr_set.add(run_id)
-    runs_with_fr = sorted(runs_with_fr_set)
+    research_cfg = (cfg or get_config()).research
+    batch = research_cfg.read_batch_size
+    # iter-29 AUDIT (AG-8): the accumulator chunk width is a RUN COUNT, read from its OWN config key —
+    # `read_batch_size` counts ROWS (the `yield_per` size above) and reusing it here as a run width made the
+    # bound inert on the live basis (2000 runs/chunk vs 1,812-1,871 real runs -> one chunk, no reduction).
+    run_chunk = research_cfg.factor_join_run_chunk
+
+    # iter-29 (AG-8): the distinct run ids at this horizon, via the shared DISTINCT-projected discovery —
+    # bounded by run count, never by (run, symbol) pair count (the dimension `_fr_slice_map` below chunks
+    # over). The `as_of` cutoff lives in that ONE helper, so both builders scope membership identically.
+    runs_with_fr = _runs_with_fr(session, [horizon], as_of)
     run_rows = (
         session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
         if runs_with_fr else []
@@ -231,29 +284,37 @@ def _factor_observations(
     # rides that SAME index (no `USE TEMP B-TREE FOR ORDER BY`), so the sort never spills a temp file to a
     # nearly-full disk; a bare `ORDER BY id` would force a full temp-B-tree sort over ~598K rows that can
     # exhaust disk. Factor Lab is UNCACHED (recomputes every request) → this is the genuine OOM site.
-    res_stmt = (
-        select(ScannerResult)
-        .where(ScannerResult.run_id.in_(runs_with_fr))
-        .order_by(ScannerResult.run_id, ScannerResult.id)
-    )
-    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
-
+    #
+    # iter-29 (AG-8): this scan now runs PER CHUNK (`runs_with_fr[start:start+run_chunk]`), scoped by the
+    # SAME `run_id.in_(slice_run_ids)` filter every chunk's `_fr_slice_map` join uses, so a chunk's
+    # ScannerResult rows and its accumulator cover the identical run-id set — the join lookup never misses.
     observations: list[dict] = []
-    for res in results:
-        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
-        if fr is None:
-            continue  # no realized return at this horizon for this stock (n=0 contribution)
-        realized, max_drawdown = fr
-        value = _extract_factor_value(res, parsed)
-        if value is None:
-            continue  # factor-NULL observation EXCLUDED (never bucketed) — honest, not fabricated
-        observations.append({
-            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
-            # iter-27/52 (J-86/J-109): the stored max_drawdown read VERBATIM — aggregated read-only into the
-            # per-decile mean-MDD beside the mean return; None on a short window (honest NA, never a 0).
-            "max_drawdown": max_drawdown,
-            "regime": regime_by_run.get(res.run_id),  # stored regime label for the run (J-27)
-        })
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult)
+            .where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+            if fr is None:
+                continue  # no realized return at this horizon for this stock (n=0 contribution)
+            realized, max_drawdown = fr
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                continue  # factor-NULL observation EXCLUDED (never bucketed) — honest, not fabricated
+            observations.append({
+                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+                # iter-27/52 (J-86/J-109): the stored max_drawdown read VERBATIM — aggregated read-only into
+                # the per-decile mean-MDD beside the mean return; None on a short window (honest NA, never a
+                # fabricated 0).
+                "max_drawdown": max_drawdown,
+                "regime": regime_by_run.get(res.run_id),  # stored regime label for the run (J-27)
+            })
+        # `ret_by_run_symbol` is rebound (not accumulated into) on the next iteration — this slice's dict is
+        # eligible for GC before the next chunk's query even starts (the bounded-memory guarantee, TC-1).
     return observations
 
 
@@ -416,14 +477,38 @@ def compute_factor_lab(
 # tuple (same `_deciles` / `_rank_ic` builders over the same per-horizon observation set). NO new served
 # value — every figure is a re-presentation of an existing `compute_factor_lab` output across all horizons.
 # --------------------------------------------------------------------------------------------------
+def _all_fr_slice_map(
+    session: Session, horizons: list[int], slice_run_ids: list[int], batch: int,
+) -> dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]]:
+    """iter-29 fix-2 (AG-8): the per-horizon `(run_id, symbol) -> (realized_return, max_drawdown)` join maps
+    for ONE bounded SLICE of run ids — `_all_factor_observations_by_horizon`'s chunk axis, and the
+    all-horizons sibling of `_fr_slice_map`. Column-projected + `yield_per`-streamed exactly like the
+    pre-chunk single-pass read; the only difference is the added `run_id.in_(slice_run_ids)` scope, which
+    bounds the LIVE size of these dicts to (horizons x len(slice_run_ids) x symbols-per-run) instead of
+    (horizons x full-history distinct pairs) — ~4.0M entries across the 5 config horizons on the live basis,
+    the structure whose fill site (`research.py:497`/`:508` in the shipped tracebacks) raised the live
+    `MemoryError` that made `/research/factor-lab` return 500 on EVERY visit. A named function (not an
+    inlined loop body) so a test can wrap/instrument it to observe the live per-slice size directly."""
+    fr_stmt = select(
+        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
+        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
+    ).where(ForwardReturn.horizon.in_(horizons), ForwardReturn.run_id.in_(slice_run_ids))
+    fr_by_h: dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]] = {h: {} for h in horizons}
+    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
+    return fr_by_h
+
+
 def _all_factor_observations_by_horizon(
     session: Session, factors: list, horizons: list[int], as_of: Optional[date_cls] = None,
     *, cfg: Optional[Config] = None,
 ) -> dict[int, list[dict]]:
     """The read-only SHARED per-observation pools for the all-factors view across EVERY horizon in
-    `horizons` (J-109), built from a SINGLE batched read: ONE `ForwardReturn` SELECT covering all horizons
-    (`horizon IN horizons`, column-projected to run_id/symbol/realized_return/max_drawdown), and ONE
-    `ScannerResult` stream. Returns `{horizon: [observations]}` where each observation is
+    `horizons` (J-109), built from ONE run-chunked sweep: per slice of run ids, one `ForwardReturn` SELECT
+    covering all horizons (`horizon IN horizons`, column-projected to run_id/symbol/realized_return/
+    max_drawdown) and one `ScannerResult` stream. Every ScannerResult row is still visited EXACTLY ONCE
+    across the whole call (the slices partition the run-id space), so the per-result `record_json` parse
+    count is unchanged. Returns `{horizon: [observations]}` where each observation is
     `{run_id, ticker, return, max_drawdown, values: {factor_key: float|None}}` (every catalog factor's
     stored value read VERBATIM — typed column or `record_json` component `raw`; recomputes NO factor and NO
     return). The `values` dict is read once per ScannerResult and SHARED across that result's per-horizon
@@ -447,44 +532,60 @@ def _all_factor_observations_by_horizon(
     ScannerResult side is `yield_per`-streamed in `(run_id, id)` order (rides `ix_scanner_results_run_id`,
     so no `USE TEMP B-TREE FOR ORDER BY` spills a temp file). ONE heavy read serves ALL N factors at ALL
     horizons (not N×H reads) — and there is NO unbounded `.all()` over `ForwardReturn` or `ScannerResult`.
-    The same one-sweep-for-all-horizons pattern as `_event_study_members_by_horizon`."""
+    The same one-sweep-for-all-horizons pattern as `_event_study_members_by_horizon`.
+
+    iter-29 fix-2 (AG-8): streaming the two SOURCE queries was never enough — the JOIN ACCUMULATOR
+    (`fr_by_h`) was one map per horizon holding every distinct (run_id, symbol) pair of the FULL history at
+    once, ~4.0M entries across the 5 config horizons on the live basis. That is what raised the live
+    `MemoryError` (against `start-backend.sh`'s `ulimit -v` cap) which made `GET /research/factor-lab?all=
+    true` return 500 on EVERY visit — 4 of 4 requests in `logs/backend.log`, the page's only consumer, since
+    `FactorLabPage` requests `?all=true` on mount. `runs_with_fr` is now discovered up front via the shared
+    `_runs_with_fr` DISTINCT-projected query (bounded by RUN count, never by pair count) and walked in
+    bounded SLICES of `research.factor_join_run_chunk` run ids — the SAME chunk axis and the SAME config
+    knob `_factor_observations` uses. Each slice builds its own `_all_fr_slice_map`, streams+joins that
+    slice's `ScannerResult`s, extends the pools, and discards the slice's maps before the next.
+
+    BYTE-IDENTITY under chunking: `runs_with_fr` is sorted and the slices are non-overlapping contiguous
+    increasing ranges, each `ScannerResult` scan re-applies the SAME `ORDER BY run_id, id`, and a slice's
+    accumulator and its `ScannerResult` filter use the identical `run_id.in_(slice_run_ids)` set (so the
+    join can never miss) — concatenating the slices reproduces the prior single-pass global order exactly.
+    Per-slice last-write-wins cannot diverge from global last-write-wins because `forward_returns` carries
+    `UNIQUE (run_id, symbol, horizon)`. No-lookahead is preserved because the `as_of` cutoff moved UP into
+    `_runs_with_fr`, upstream of every derived structure.
+
+    NOT bounded here (deliberate, same call the single-factor builder makes): the returned `pools` are this
+    function's return shape — `compute_factor_lab_all` needs each horizon's pool whole to derive its
+    deciles. Only the accumulator's peak is bounded."""
     parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
-    batch = (cfg or get_config()).research.read_batch_size
-    fr_stmt = select(
-        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
-        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
-    ).where(ForwardReturn.horizon.in_(horizons))
-    if as_of is not None:
-        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
-            ScannerRun.asof_date <= as_of
-        )
-    fr_by_h: dict[int, dict[tuple[int, str], tuple[float, Optional[float]]]] = {h: {} for h in horizons}
-    runs_with_fr_set: set[int] = set()
-    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
-        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
-        runs_with_fr_set.add(run_id)
-    runs_with_fr = sorted(runs_with_fr_set)
-    res_stmt = (
-        select(ScannerResult)
-        .where(ScannerResult.run_id.in_(runs_with_fr))
-        .order_by(ScannerResult.run_id, ScannerResult.id)
-    )
-    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
+    research_cfg = (cfg or get_config()).research
+    batch = research_cfg.read_batch_size          # ROW count — the `yield_per` size of each stream
+    run_chunk = research_cfg.factor_join_run_chunk  # RUN count — the accumulator's slice width
 
+    runs_with_fr = _runs_with_fr(session, horizons, as_of)
     pools: dict[int, list[dict]] = {h: [] for h in horizons}
-    for res in results:
-        values: Optional[dict] = None  # parsed lazily on the first horizon that has an FR for this result
-        for h in horizons:
-            fr = fr_by_h[h].get((res.run_id, res.ticker))
-            if fr is None:
-                continue  # no realized return at this horizon (n=0) — same exclusion as per-factor
-            if values is None:
-                values = {key: _extract_factor_value(res, parsed) for key, parsed in parsed_by_key.items()}
-            realized, max_drawdown = fr
-            pools[h].append({
-                "run_id": res.run_id, "ticker": res.ticker, "return": realized,
-                "max_drawdown": max_drawdown, "values": values,
-            })
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        fr_by_h = _all_fr_slice_map(session, horizons, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult)
+            .where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            values: Optional[dict] = None  # parsed lazily on the first horizon that has an FR for this result
+            for h in horizons:
+                fr = fr_by_h[h].get((res.run_id, res.ticker))
+                if fr is None:
+                    continue  # no realized return at this horizon (n=0) — same exclusion as per-factor
+                if values is None:
+                    values = {key: _extract_factor_value(res, parsed) for key, parsed in parsed_by_key.items()}
+                realized, max_drawdown = fr
+                pools[h].append({
+                    "run_id": res.run_id, "ticker": res.ticker, "return": realized,
+                    "max_drawdown": max_drawdown, "values": values,
+                })
+        # `fr_by_h` is rebound (not accumulated into) on the next iteration — this slice's maps are eligible
+        # for GC before the next chunk's query even starts (the bounded-memory guarantee).
     return pools
 
 
diff --git a/apps/backend/tests/test_evidence.py b/apps/backend/tests/test_evidence.py
index 512e6e5d..e6ded870 100644
--- a/apps/backend/tests/test_evidence.py
+++ b/apps/backend/tests/test_evidence.py
@@ -21,6 +21,7 @@ from pathlib import Path
 import pytest
 from sqlmodel import Session
 
+import app.engine.forward_testing as forward_testing
 import app.engine.market_phase as market_phase
 from app.config import REPO_ROOT, load_config
 from app.db import create_db_and_tables, make_engine
@@ -615,6 +616,110 @@ def test_build_payload_session_provided_unresolvable_claim_no_expectations_key(t
     with Session(evidence_dd_engine) as session:
         payload = build_evidence_payload(str(ledger), session=session, config=load_config())
     assert "expectations" not in payload["claims"][0]
+    # ops-hardening iter-29 (AG-8) error-case regression: the pre-existing HONEST-None path (an
+    # unresolvable cohort, `compute_drawdown_expectations` returning None WITHOUT raising) must stay
+    # byte-unchanged by the new per-claim failure guard below — no `expectations_status` field either.
+    # This is what proves the new field is ADDITIVE (only on a caught exception), never a replacement of
+    # the pre-existing silent-omission behavior.
+    assert "expectations_status" not in payload["claims"][0]
+
+
+# ==================================================================================================
+# ops-hardening iter-29 (AG-8) — a per-claim `compute_drawdown_expectations_cached` failure
+# (`MemoryError` or otherwise) must never abort the response for the OTHER claims: the failing claim's row
+# omits `expectations` and carries the new `expectations_status: "unavailable"` field; every other claim's
+# row is byte-unchanged (isolate-and-continue, mirroring the EXISTING per-claim `MemoryError`-then-continue
+# convention `data_manager.py`'s drawdown-expectations ingest warm loop already uses near
+# `data_manager.py:3361` — TC-4).
+# ==================================================================================================
+@pytest.fixture()
+def evidence_dd_two_claims_engine(tmp_path, monkeypatch):
+    """TWO independently resolvable claims in ONE fixture, dedicated (not a mutation of `evidence_dd_engine`
+    above, so its own two existing tests stay untouched): AAA (leadership_score, decile 10, horizon 20 —
+    byte-identical setup to `evidence_dd_engine`) plus BBB (entry_quality_score, decile 10, horizon 20) in
+    the SAME run/date. BBB's high `entry_quality_score` / baseline `leadership_score` (and AAA's inverse)
+    mean each name is the SOLE decile-10 member of its OWN factor's single-observation cohort — adding BBB
+    does not disturb AAA's leadership_score decile-10 membership (still {AAA} alone, n=1)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'evidence_dd_two.db'}")
+    create_db_and_tables(engine)
+    d = date(2025, 1, 10)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        session.add(ScannerResult(
+            run_id=run.id, ticker="AAA", name="AAA", sector="Technology",
+            leadership_score=90.0, leadership_bucket="A",
+            entry_quality_score=50.0, entry_quality_bucket="C",
+            risk_score=50.0, risk_bucket="C",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="AAA", horizon=20, asof_date=d, entry_close=100.0,
+            measured_date=d + timedelta(days=40), realized_return=0.02,
+            max_drawdown=-0.05, underwater_days=3, time_to_recover_days=5,
+        ))
+        session.add(ScannerResult(
+            run_id=run.id, ticker="BBB", name="BBB", sector="Technology",
+            leadership_score=50.0, leadership_bucket="C",
+            entry_quality_score=90.0, entry_quality_bucket="A",
+            risk_score=50.0, risk_bucket="C",
+            setup_status="Actionable", rank=2, record_json="{}",
+        ))
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="BBB", horizon=20, asof_date=d, entry_close=100.0,
+            measured_date=d + timedelta(days=40), realized_return=0.03,
+            max_drawdown=-0.04, underwater_days=2, time_to_recover_days=4,
+        ))
+        session.commit()
+
+    def _fake_ctx(session=None, as_of=None, config=None):
+        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_ctx)
+    return engine
+
+
+def test_build_payload_per_claim_compute_failure_is_isolated(
+    tmp_path, evidence_dd_two_claims_engine, monkeypatch
+):
+    """TC-4: `compute_drawdown_expectations_cached` monkeypatched to raise `MemoryError` for exactly ONE of
+    two resolvable claims. The failing claim's row carries `expectations_status: "unavailable"` and no
+    `expectations` key; the OTHER claim's row carries its normal `expectations` key, fully unaffected —
+    proving one claim's compute failure never blanks the rest of the `/evidence` response."""
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), _pass_entry("leadership_score"))
+    append_entry(str(ledger), _pass_entry("entry_quality_score", factor="entry_quality_score"))
+
+    real_cached = forward_testing.compute_drawdown_expectations_cached
+
+    def _flaky_cached(session, claim, config=None):
+        if claim.get("factor") == "leadership_score":
+            raise MemoryError("synthetic TC-4 failure")
+        return real_cached(session, claim, config)
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _flaky_cached)
+
+    with Session(evidence_dd_two_claims_engine) as session:
+        payload = build_evidence_payload(str(ledger), session=session, config=load_config())
+
+    rows = payload["claims"]
+    assert len(rows) == 2
+    failed_row = next(r for r in rows if r["claim"]["factor"] == "leadership_score")
+    ok_row = next(r for r in rows if r["claim"]["factor"] == "entry_quality_score")
+
+    assert failed_row.get("expectations_status") == "unavailable"
+    assert "expectations" not in failed_row
+
+    assert "expectations_status" not in ok_row
+    assert "expectations" in ok_row
+    assert ok_row["expectations"]["horizon"] == 20
+    exp_phase = next(p for p in ok_row["expectations"]["by_phase"] if p["phase"] == "Expansion")
+    assert exp_phase["n"] == 1
 
 
 def test_resolve_ledger_path_env_override(tmp_path, monkeypatch):
diff --git a/apps/backend/tests/test_factor_lab_all.py b/apps/backend/tests/test_factor_lab_all.py
index 9a2a8692..91508648 100644
--- a/apps/backend/tests/test_factor_lab_all.py
+++ b/apps/backend/tests/test_factor_lab_all.py
@@ -33,7 +33,7 @@ from __future__ import annotations
 
 import inspect
 import json
-from datetime import date, datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 
 import pytest
 from sqlmodel import Session, select
@@ -140,9 +140,16 @@ def lab_engine(tmp_path):
     return engine
 
 
-def _cfg_batch(batch: int):
+def _cfg_batch(batch: int, run_chunk: int | None = None):
+    """The real config with `research.read_batch_size` overridden to `batch` (the ROW-count `yield_per`
+    probe) and `research.factor_join_run_chunk` (the iter-29 RUN-COUNT accumulator width — a DIFFERENT unit)
+    overridden to `run_chunk`, defaulting to the same value so every pre-existing chunk-independence probe
+    varies BOTH knobs (a huge value collapses the shared pool build back to the pre-iter-29 single sweep)."""
     cfg = load_config()
-    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})
+    return cfg.model_copy(update={"research": cfg.research.model_copy(update={
+        "read_batch_size": batch,
+        "factor_join_run_chunk": batch if run_chunk is None else run_chunk,
+    })})
 
 
 def _bytes(obj) -> str:
@@ -362,6 +369,130 @@ def test_shared_pool_read_is_bounded_and_run_id_id_ordered():
     assert ").all()" not in src, "shared pool must not materialize an unbounded .all()"
 
 
+# ==================================================================================================
+# 4b. iter-29 fix-2 (AG-8) — the JOIN ACCUMULATOR is run-chunked, not just the source streams
+#
+# Streaming both source queries was never enough: `fr_by_h` was one map per horizon holding every distinct
+# (run_id, symbol) pair of the FULL history at once (~4.0M entries across the 5 config horizons on the live
+# basis). That accumulator's fill site is where `logs/backend.log` recorded the live `MemoryError` that made
+# `GET /research/factor-lab?all=true` return 500 on 4 of 4 visits — the page's ONLY consumer, since
+# `FactorLabPage` requests `?all=true` on mount. The proofs below pin the bound at the SHIPPED width and
+# pin that the chunking changed no value.
+# ==================================================================================================
+def _all_pools_reference_unchunked(session, factors, horizons, as_of, cfg):
+    """A pinned copy of the PRE-FIX `_all_factor_observations_by_horizon` body: ONE unbounded `fr_by_h`
+    accumulator built from a SINGLE un-sliced FR scan over the whole history, and ONE un-sliced
+    `ScannerResult` sweep (no `_all_fr_slice_map`, no chunk loop). The regression oracle for the chunked
+    rewrite's byte-identity proof — it calls the SAME unchanged `_extract_factor_value` /
+    `parse_factor_source` helpers the real function still uses, so any divergence can only come from the
+    chunking itself."""
+    from app.engine.research import _extract_factor_value, parse_factor_source
+
+    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
+    batch = cfg.research.read_batch_size
+    fr_stmt = select(
+        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
+        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
+    ).where(ForwardReturn.horizon.in_(horizons))
+    if as_of is not None:
+        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+            ScannerRun.asof_date <= as_of
+        )
+    fr_by_h = {h: {} for h in horizons}
+    runs_with_fr_set = set()
+    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
+        runs_with_fr_set.add(run_id)
+    runs_with_fr = sorted(runs_with_fr_set)
+    res_stmt = (
+        select(ScannerResult)
+        .where(ScannerResult.run_id.in_(runs_with_fr))
+        .order_by(ScannerResult.run_id, ScannerResult.id)
+    )
+    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
+    pools = {h: [] for h in horizons}
+    for res in results:
+        values = None
+        for h in horizons:
+            fr = fr_by_h[h].get((res.run_id, res.ticker))
+            if fr is None:
+                continue
+            if values is None:
+                values = {key: _extract_factor_value(res, parsed) for key, parsed in parsed_by_key.items()}
+            realized, max_drawdown = fr
+            pools[h].append({
+                "run_id": res.run_id, "ticker": res.ticker, "return": realized,
+                "max_drawdown": max_drawdown, "values": values,
+            })
+    return pools
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
+def test_shared_pools_chunked_equal_the_pinned_unchunked_reference(lab_engine, as_of):
+    """The run-chunked shared-pool build is byte-identical to the pinned pre-fix single-accumulator
+    reference — same rows, same per-horizon order, same factor values — for all-history AND an as-of window
+    that splits the fixture's two runs."""
+    cfg = _cfg_batch(2, run_chunk=1)  # 1 run id per slice over the fixture's 2 runs -> real chunking
+    factors = list(cfg.research.factor_lab.factors)
+    horizons = list(cfg.walk_forward.horizons)
+    with Session(lab_engine) as session:
+        chunked = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
+        reference = _all_pools_reference_unchunked(session, factors, horizons, as_of, cfg)
+    assert _bytes(chunked) == _bytes(reference), f"chunked pools != pinned pre-fix pools (as_of={as_of})"
+
+
+def test_shared_pool_accumulator_is_chunk_bounded_at_the_shipped_config(tmp_path, monkeypatch):
+    """The all-horizons join accumulator is bounded at the SHIPPED `research.factor_join_run_chunk` — no
+    `_cfg_batch` override, because an override is exactly how the first iter-29 bound shipped inert. Builds
+    a fixture with (shipped width + 3) runs so real chunking is REQUIRED, then asserts the builder made >= 2
+    slice reads and that no single slice's maps ever held the whole fixture's (run_id, symbol) pairs."""
+    import app.engine.research as research
+
+    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
+    width = cfg.research.factor_join_run_chunk
+    n_runs, tickers = width + 3, ("AA", "BB")
+    engine = make_engine(f"sqlite:///{tmp_path / 'all_shipped_chunk.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for i in range(n_runs):
+            run = _add_run(session, date(2025, 1, 1) + timedelta(days=i), regime_label="Risk-on")
+            for j, base in enumerate(tickers):
+                ticker = f"{base}{i}"
+                _add_result(session, run.id, ticker, rank=j + 1, lead=float(50 + (i % 7) + j),
+                            entry=float(40 + j), risk=float(30 + j),
+                            rs_spy_3m=float(j) / 10.0, atr_pct=float(j) / 100.0)
+                for h in POPULATED_HORIZONS:
+                    _add_fr(session, run.id, ticker, ret=0.01 * (i + 1), horizon=h, mdd=-0.03)
+        session.commit()
+
+    observed_sizes: list[int] = []
+    real_slice_map = research._all_fr_slice_map
+
+    def _wrapped(session, horizons, slice_run_ids, batch):
+        result = real_slice_map(session, horizons, slice_run_ids, batch)
+        observed_sizes.append(sum(len(m) for m in result.values()))
+        return result
+
+    monkeypatch.setattr(research, "_all_fr_slice_map", _wrapped)
+    factors = list(cfg.research.factor_lab.factors)
+    horizons = list(cfg.walk_forward.horizons)
+    with Session(engine) as session:
+        pools = research._all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)
+
+    total_pairs = n_runs * len(tickers) * len(POPULATED_HORIZONS)
+    assert sum(len(p) for p in pools.values()) == total_pairs, "sanity: every fixture pair must surface"
+    assert len(observed_sizes) >= 2, (
+        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the all-horizons "
+        f"accumulator bound is inert at the real configuration (width={width})"
+    )
+    assert max(observed_sizes) <= width * len(tickers) * len(POPULATED_HORIZONS), (
+        f"a slice exceeded its configured run-chunk width: {max(observed_sizes)} entries"
+    )
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
+    )
+
+
 @pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
 def test_all_factors_chunk_independent(lab_engine, as_of):
     """The full all-horizons payload is byte-identical under read_batch_size=1 vs a huge batch — the stream
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index f6ccdc7b..5559a3b4 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -23,11 +23,12 @@ sort_keys=True)` byte-identity, the repo convention (cf. test_market_phase.py /
 from __future__ import annotations
 
 import json
-from datetime import date, datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 
 import pytest
-from sqlmodel import Session
+from sqlmodel import Session, select
 
+import app.engine.research as research_module
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.research import (
@@ -134,10 +135,16 @@ def prune_engine(tmp_path):
     return engine
 
 
-def _cfg_batch(batch: int):
-    """The real config with `research.read_batch_size` overridden to `batch` (chunk-size probe)."""
+def _cfg_batch(batch: int, run_chunk: int | None = None):
+    """The real config with `research.read_batch_size` overridden to `batch` (chunk-size probe), and
+    `research.factor_join_run_chunk` (the iter-29-audit RUN-COUNT accumulator width — a DIFFERENT unit)
+    overridden to `run_chunk`, defaulting to the same value so every existing probe keeps varying BOTH the
+    `yield_per` row batch and the join-accumulator chunking exactly as it did before the two knobs split."""
     cfg = load_config()
-    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})
+    return cfg.model_copy(update={"research": cfg.research.model_copy(update={
+        "read_batch_size": batch,
+        "factor_join_run_chunk": batch if run_chunk is None else run_chunk,
+    })})
 
 
 def _eq(a, b) -> bool:
@@ -566,3 +573,228 @@ def test_compute_factor_lab_all_chunk_independent_component(component_engine, as
         small = compute_factor_lab_all(session, _cfg_batch(1), as_of=as_of)
         big = compute_factor_lab_all(session, _cfg_batch(1_000_000), as_of=as_of)
         assert _eq(small, big), f"factor-lab-all payload differs by batch (as_of={as_of})"
+
+
+# ==================================================================================================
+# ops-hardening iter-29 (AG-8): `_factor_observations`'s join accumulator (`ret_by_run_symbol`) used to
+# hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history for
+# as_of=None (803,042 pairs / 3,964,725 rows measured live at iter-28) even though the SOURCE query was
+# already `yield_per`-streamed — an unbounded whole-history materialization in substance (AG-8). The fix
+# chunks `runs_with_fr` (the sorted distinct run-id list, now discovered via a lightweight DISTINCT query
+# instead of as a side effect of building the full accumulator) into bounded slices, rebuilding the
+# accumulator ONE slice at a time via the new `_fr_slice_map` helper — so its LIVE size is bounded by
+# (chunk width x symbols-per-run), never by the full history's distinct-pair count. These proofs pin:
+#   1. TC-1: the live accumulator (`_fr_slice_map`'s return value) never holds more than one chunk's worth
+#      of entries at any point during a call, on a fixture whose rows span more than one chunk across >=2
+#      distinct run ids.
+#   2. TC-2: the chunked rewrite is byte-identical to a pinned copy of the PRE-FIX (single-accumulator)
+#      implementation, for both as_of=None and a historical as_of=D.
+#   3. TC-3: the as_of=D call returns zero observations from a run dated after D (no-lookahead preserved).
+# ==================================================================================================
+@pytest.fixture()
+def chunked_accumulator_engine(tmp_path):
+    """5 distinct ScannerRuns (one per month, Jan-May 2025), each with 3 tickers carrying a forward return
+    at horizon H — 15 total distinct (run_id, symbol) pairs, spanning 5 distinct run ids. Dedicated (not
+    reused from `prune_engine`/`component_engine`) so the chunk-boundary proof (TC-1) and the as_of cutoff
+    proof (TC-3) have a fixture shaped exactly for them: enough runs to force multiple chunks at a small
+    `read_batch_size`, and dates that cleanly split into an early/late group around a chosen as_of."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'chunked.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        runs = [
+            _add_run(session, date(2025, m, 10), regime_label="Risk-on" if m % 2 else "Risk-off")
+            for m in range(1, 6)  # r0=Jan .. r4=May 2025
+        ]
+        session.flush()
+        for i, run in enumerate(runs):
+            for j, base in enumerate(("AA", "BB", "CC")):
+                ticker = f"{base}{i}"  # distinct symbol per run -> 15 genuinely distinct (run_id, symbol) pairs
+                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
+                            lead=50.0 + i + j)
+                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
+                        mae=-0.02, mfe=0.05, mdd=-0.03 - 0.001 * j)
+        session.commit()
+    return engine
+
+
+def _factor_observations_reference_unchunked(session, factor, horizon, as_of, cfg):
+    """A pinned copy of iter-29's PRE-FIX `_factor_observations` body: ONE unbounded `ret_by_run_symbol`
+    accumulator built from a SINGLE un-sliced `fr_stmt` covering the FULL `runs_with_fr` set at once (no
+    `_fr_slice_map`, no chunk loop) — the regression oracle for the iter-29 chunked rewrite's byte-identity
+    proof (TC-2). Calls the SAME unchanged helpers (`parse_factor_source`, `_extract_factor_value`) the real,
+    rewritten function still uses, so any divergence can only come from the chunking itself."""
+    from app.engine.research import _extract_factor_value, parse_factor_source
+    parsed = parse_factor_source(factor.source)
+    batch = cfg.research.read_batch_size
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
+    ).where(ForwardReturn.horizon == horizon)
+    if as_of is not None:
+        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+            ScannerRun.asof_date <= as_of
+        )
+    ret_by_run_symbol = {}
+    runs_with_fr_set = set()
+    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
+        runs_with_fr_set.add(run_id)
+    runs_with_fr = sorted(runs_with_fr_set)
+    run_rows = (
+        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    regime_by_run = {run.id: run.regime_label for run in run_rows}
+    res_stmt = (
+        select(ScannerResult)
+        .where(ScannerResult.run_id.in_(runs_with_fr))
+        .order_by(ScannerResult.run_id, ScannerResult.id)
+    )
+    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
+    observations = []
+    for res in results:
+        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+        if fr is None:
+            continue
+        realized, max_drawdown = fr
+        value = _extract_factor_value(res, parsed)
+        if value is None:
+            continue
+        observations.append({
+            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+            "max_drawdown": max_drawdown,
+            "regime": regime_by_run.get(res.run_id),
+        })
+    return observations
+
+
+def test_factor_observations_accumulator_is_chunk_bounded(chunked_accumulator_engine, monkeypatch):
+    """TC-1: `_factor_observations`'s join accumulator (`_fr_slice_map`'s return value, wrapped/observed via
+    monkeypatch) never holds more entries than ONE bounded chunk at any point during the call — never one
+    entry per distinct (run_id, symbol) pair in the whole fixture (15 pairs across 5 run ids)."""
+    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
+    observed_sizes: list[int] = []
+    real_fr_slice_map = research_module._fr_slice_map
+
+    def _wrapped(session, horizon, slice_run_ids, batch):
+        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
+    with Session(chunked_accumulator_engine) as session:
+        # chunk width = 2 run ids/slice over 5 distinct run ids -> 3 slices (2, 2, 1 run ids each)
+        observations = research_module._factor_observations(session, factor, H, None, cfg=_cfg_batch(2))
+
+    total_pairs = 15  # 5 runs x 3 tickers, by fixture construction
+    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
+    assert len(observed_sizes) == 3, f"expected 3 chunks (5 run ids at width 2), got {len(observed_sizes)}"
+    assert max(observed_sizes) <= 6, (
+        f"a single slice must never exceed 2 run ids x 3 tickers = 6 entries, got {max(observed_sizes)}"
+    )
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once"
+    )
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
+def test_factor_observations_chunked_equals_unchunked_reference(chunked_accumulator_engine, as_of):
+    """TC-2: the iter-29 chunked `_factor_observations` is byte-identical to the pinned pre-fix
+    (single-accumulator) reference — for as_of=None (all-history) AND a historical as_of=D (2025-03-15) that
+    splits the 5-run fixture into an early (Jan-Mar) / late (Apr-May) group."""
+    cfg = _cfg_batch(2)
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        chunked = _factor_observations(session, factor, H, as_of, cfg=cfg)
+        reference = _factor_observations_reference_unchunked(session, factor, H, as_of, cfg)
+    assert _eq(chunked, reference), f"chunked output != pinned pre-fix reference (as_of={as_of})"
+
+
+def test_factor_observations_chunked_as_of_excludes_runs_after_cutoff(chunked_accumulator_engine):
+    """TC-3: for the as_of=D-scoped chunked call, zero returned observations reference a run dated after D
+    (no-lookahead preserved through the chunk rewrite)."""
+    d = date(2025, 3, 15)  # between run r2 (Mar 10) and run r3 (Apr 10)
+    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        observations = _factor_observations(session, factor, H, d, cfg=_cfg_batch(2))
+        run_dates = {run.id: run.asof_date for run in session.exec(select(ScannerRun)).all()}
+    assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
+    for obs in observations:
+        assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"
+
+
+# ==================================================================================================
+# iter-29 AUDIT (AG-8): the two proofs above pin the chunking MECHANISM, but both drive it through an
+# artificially small `_cfg_batch(2)` override — so they pass no matter what the SHIPPED config does. As
+# first shipped, iter-29's loop reused `research.read_batch_size` (2000, a ROW count) as its RUN-COUNT
+# chunk width; the live basis carries only 1,812-1,871 distinct runs per horizon, so the loop produced
+# exactly ONE chunk and the accumulator still held every pair at once (792,507 measured at h=20 via
+# `SELECT ... WHERE horizon=20 AND run_id IN (<first 2000 sorted run ids>)` — 0% below the pre-fix peak,
+# i.e. a bound that bound nothing). The two tests below pin the property at the REAL configuration, which
+# is what AG-8 is actually about.
+# ==================================================================================================
+
+# The live basis measured during the iter-29 audit: 1,812-1,871 distinct scanner runs per horizon, ~429
+# symbols per run. A run-chunk width at/above the run count degenerates to a single chunk, so the shipped
+# width must stay well below it with room for years of further daily-cadence growth; 500 is the loosest
+# ceiling that still forces real chunking on today's basis (>=4 chunks) and would have caught the shipped
+# 2000. Peak accumulator = width x symbols-per-run, so the shipped 100 holds ~43-55K pairs, not ~800K.
+_MAX_MEANINGFUL_RUN_CHUNK = 500
+
+
+def test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis():
+    """The SHIPPED `research.factor_join_run_chunk` must be small enough to produce real chunking against
+    a multi-year daily-cadence basis. This is the regression guard for the iter-29 audit finding: a width
+    of 2000 runs (the row knob, reused) against 1,812-1,871 live runs per horizon meant one chunk and zero
+    peak reduction, while every unit proof still passed because it overrode the knob to 2."""
+    research_cfg = load_config().research
+    width = research_cfg.factor_join_run_chunk
+    assert 1 <= width <= _MAX_MEANINGFUL_RUN_CHUNK, (
+        f"research.factor_join_run_chunk={width} cannot bound the join accumulator on the live basis "
+        f"(1,812-1,871 distinct runs/horizon): it must be <= {_MAX_MEANINGFUL_RUN_CHUNK}"
+    )
+
+
+def test_factor_observations_chunks_at_the_shipped_config(tmp_path, monkeypatch):
+    """The accumulator is chunk-bounded under the SHIPPED config — no `_cfg_batch` override. Builds a
+    fixture with (shipped width + 3) runs so real chunking is REQUIRED, then asserts `_factor_observations`
+    made >= 2 slice reads and that no single slice ever held the whole fixture's (run_id, symbol) pairs."""
+    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
+    width = cfg.research.factor_join_run_chunk
+    n_runs, tickers = width + 3, ("AA", "BB")
+    engine = make_engine(f"sqlite:///{tmp_path / 'shipped_chunk.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for i in range(n_runs):
+            run = _add_run(session, date(2025, 1, 1) + timedelta(days=i), regime_label="Risk-on")
+            session.flush()
+            for j, base in enumerate(tickers):
+                ticker = f"{base}{i}"
+                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
+                            lead=50.0 + (i % 7) + j)
+                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
+                        mae=-0.02, mfe=0.05, mdd=-0.03)
+        session.commit()
+
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    observed_sizes: list[int] = []
+    real_fr_slice_map = research_module._fr_slice_map
+
+    def _wrapped(session, horizon, slice_run_ids, batch):
+        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
+    with Session(engine) as session:
+        observations = research_module._factor_observations(session, factor, H, None, cfg=cfg)
+
+    total_pairs = n_runs * len(tickers)
+    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
+    assert len(observed_sizes) >= 2, (
+        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the accumulator "
+        f"bound is inert at the real configuration (width={width})"
+    )
+    assert max(observed_sizes) <= width * len(tickers), "a slice exceeded its configured run-chunk width"
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
+    )
diff --git a/apps/frontend/app/evidence/page.tsx b/apps/frontend/app/evidence/page.tsx
index cf22310f..4bdf60a3 100644
--- a/apps/frontend/app/evidence/page.tsx
+++ b/apps/frontend/app/evidence/page.tsx
@@ -16,8 +16,8 @@ import {
   formatStreak,
   insufficientLabel,
   regimeLabel,
+  resolveDrawdownExpectationsPanelState,
   type DistributionCell,
-  type DrawdownExpectations,
   type LossStreakCell,
 } from "@/lib/evidence";
 import { fetchEvidence, type CertifiedClaim, type EvidenceLedgerResponse } from "@/lib/api";
@@ -233,26 +233,44 @@ function ClaimRow({ claim }: { claim: CertifiedClaim }) {
           </Field>
         </dl>
 
-        <DrawdownExpectationsPanel expectations={claim.expectations} />
+        <DrawdownExpectationsPanel claim={claim} />
       </CardContent>
     </Card>
   );
 }
 
 /** J-25 — the phase-conditional drawdown & dry-spell expectations panel: an additive section inside the
- *  SAME claim card, below the existing field grid. Renders NOTHING when `expectations` is absent/null
- *  (mirrors the Stock-detail RiskBudgetCard's "return null when absent" precedent, iter-40) — never an
- *  error boundary, never a blank placeholder. Reads `claim.expectations` VERBATIM — no client-side
- *  recompute; every figure is the served median/p90/streak, re-formatted only. Renders for ANY claim
- *  regardless of its PASS/FAIL verdict (outcome-neutral, J-25) — descriptive history, never a forecast. */
-function DrawdownExpectationsPanel({
-  expectations,
-}: {
-  expectations: DrawdownExpectations | null | undefined;
-}) {
-  if (!expectations) {
+ *  SAME claim card, below the existing field grid. Renders NOTHING when `expectations` is absent/null with
+ *  no status field (mirrors the Stock-detail RiskBudgetCard's "return null when absent" precedent,
+ *  iter-40) — never an error boundary, never a blank placeholder. Reads `claim.expectations` VERBATIM — no
+ *  client-side recompute; every figure is the served median/p90/streak, re-formatted only. Renders for ANY
+ *  claim regardless of its PASS/FAIL verdict (outcome-neutral, J-25) — descriptive history, never a
+ *  forecast.
+ *
+ *  ops-hardening iter-29 (AG-8): branches on `resolveDrawdownExpectationsPanelState` (the single, pure
+ *  authority) so a genuine per-claim compute failure THIS request (`expectations_status === "unavailable"`)
+ *  renders a calm inline note instead of being indistinguishable from the pre-existing "not applicable"
+ *  (absent) case. */
+function DrawdownExpectationsPanel({ claim }: { claim: CertifiedClaim }) {
+  const state = resolveDrawdownExpectationsPanelState(claim);
+  if (state.kind === "absent") {
     return null;
   }
+  if (state.kind === "unavailable") {
+    // A routine transient-failure disclosure, not an error banner — same calm `text-text-faint` treatment
+    // the "Pending — monitored as new data matures" forward-walk cell above already uses on this card.
+    return (
+      <div className="border-t border-border pt-3" data-testid="evidence-expectations-unavailable">
+        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
+          Historical drawdown &amp; dry-spell expectations
+        </h3>
+        <p className="mt-0.5 text-xs text-text-faint">
+          Unavailable — monitored and refreshed as new data arrives.
+        </p>
+      </div>
+    );
+  }
+  const { expectations } = state;
   return (
     <div className="space-y-2 border-t border-border pt-3" data-testid="evidence-expectations-panel">
       <div>
diff --git a/apps/frontend/lib/evidence.test.ts b/apps/frontend/lib/evidence.test.ts
index c17f852d..46b188a0 100644
--- a/apps/frontend/lib/evidence.test.ts
+++ b/apps/frontend/lib/evidence.test.ts
@@ -43,9 +43,11 @@ import {
   regimeLabel,
   resolveCohortEvidence,
   resolveCombinationEvidence,
+  resolveDrawdownExpectationsPanelState,
   resolveEvidenceStatus,
   type CertifiedClaim,
   type CombinationCohort,
+  type DrawdownExpectations,
   type FactorCohort,
   type ProvenSignal,
 } from "./evidence.ts";
@@ -981,4 +983,58 @@ check("formatStreak renders a rounded integer, and an em dash for null/undefined
   assert.strictEqual(formatStreak(undefined), "—");
 });
 
+// --- drawdown-expectations panel state resolver (ops-hardening iter-29, AG-8 residual-failure disclosure,
+// TC-5) — the pure decision function `DrawdownExpectationsPanel` (app/evidence/page.tsx) branches on. Three
+// states: the pre-existing "present" (a table renders) and "absent" (no expectations, no status field —
+// renders nothing, unchanged honest-None cohort-unresolvable case) plus the NEW "unavailable" (a per-claim
+// compute failure this request — an inline note, no table). Mirrors the extracted-decision-function pattern
+// `lib/background-compute-panel-branch.ts` established (iter-24/25, J-09).
+const SAMPLE_EXPECTATIONS: DrawdownExpectations = {
+  horizon: 20,
+  min_sample: 5,
+  streak_min_n: 3,
+  survivorship_bias: "Current-membership seed; survivorship bias not corrected for.",
+  method_note: "Median/p90 by market phase at entry.",
+  by_phase: [],
+};
+
+check("resolveDrawdownExpectationsPanelState: expectations present => 'present', carrying it verbatim", () => {
+  const claim: CertifiedClaim = { ...provenRow("leadership_score"), expectations: SAMPLE_EXPECTATIONS };
+  const state = resolveDrawdownExpectationsPanelState(claim);
+  assert.strictEqual(state.kind, "present");
+  if (state.kind === "present") {
+    assert.strictEqual(state.expectations, SAMPLE_EXPECTATIONS); // read verbatim, never recomputed
+  }
+});
+
+check("resolveDrawdownExpectationsPanelState: expectations_status='unavailable' => 'unavailable' (TC-5)", () => {
+  const claim: CertifiedClaim = { ...provenRow("leadership_score"), expectations_status: "unavailable" };
+  const state = resolveDrawdownExpectationsPanelState(claim);
+  assert.strictEqual(state.kind, "unavailable");
+});
+
+check(
+  "resolveDrawdownExpectationsPanelState: no expectations + no status field => 'absent' (pre-existing " +
+    "honest-None case, unchanged, TC-5)",
+  () => {
+    const claim: CertifiedClaim = provenRow("leadership_score"); // no expectations, no expectations_status
+    const state = resolveDrawdownExpectationsPanelState(claim);
+    assert.strictEqual(state.kind, "absent");
+  },
+);
+
+check(
+  "resolveDrawdownExpectationsPanelState: 'unavailable' is DISTINCT from the pre-existing absent case (TC-5)",
+  () => {
+    const unavailable = resolveDrawdownExpectationsPanelState({
+      ...provenRow("leadership_score"),
+      expectations_status: "unavailable",
+    });
+    const absent = resolveDrawdownExpectationsPanelState(provenRow("leadership_score"));
+    assert.notStrictEqual(unavailable.kind, absent.kind);
+    assert.strictEqual(unavailable.kind, "unavailable");
+    assert.strictEqual(absent.kind, "absent");
+  },
+);
+
 console.log(`\n${passed} evidence-badge resolver checks passed.`);
diff --git a/apps/frontend/lib/evidence.ts b/apps/frontend/lib/evidence.ts
index cea8c8d8..de18d546 100644
--- a/apps/frontend/lib/evidence.ts
+++ b/apps/frontend/lib/evidence.ts
@@ -74,7 +74,13 @@ export interface DrawdownExpectations {
  *  PASS backs (null for a real signal-less writer entry — fail-safe). `forward_walk` is the forward-walk
  *  score-to-date (null until a certified claim is monitored). `expectations` (iter-41, J-25) is ADDITIVE
  *  and OPTIONAL — the backend omits the key entirely (never a fabricated panel) when the cohort could not
- *  be resolved; a `null`/`undefined` value must render nothing for the panel section (never an error). */
+ *  be resolved; a `null`/`undefined` value must render nothing for the panel section (never an error).
+ *  `expectations_status` (ops-hardening iter-29, AG-8) is ALSO additive and OPTIONAL — present ONLY when
+ *  this request's per-claim `expectations` compute raised an exception (`"unavailable"`, the one legal
+ *  value today); absent for a successful compute AND for every pre-existing honest-None case (an
+ *  out-of-scope horizon, an unresolvable cohort, a zero-observation cohort) — those keep rendering nothing,
+ *  byte-unchanged. `resolveDrawdownExpectationsPanelState` below is the single place that distinguishes
+ *  the three states. */
 export interface CertifiedClaim {
   signal: string | null;
   claim: Record<string, unknown>;
@@ -86,6 +92,7 @@ export interface CertifiedClaim {
   proven: boolean;
   forward_walk: unknown | null;
   expectations?: DrawdownExpectations | null;
+  expectations_status?: "unavailable";
 }
 
 /** A proven claim row, as stored in the served `proven_signals` map (keyed by signal). Same shape as a
@@ -277,6 +284,39 @@ export function formatStreak(value: number | null | undefined): string {
   return `${Math.round(value)}`;
 }
 
+// --- drawdown-expectations PANEL state resolver (ops-hardening iter-29, AG-8 residual-failure disclosure) -
+// PURE, read-only: the SINGLE authority for which of the THREE states `DrawdownExpectationsPanel`
+// (app/evidence/page.tsx) renders for one claim. No React, no DOM types, so it is unit-testable under
+// `node`/`tsx` (mirrors `lib/background-compute-panel-branch.ts`'s extracted-decision-function pattern,
+// iter-24/25 J-09). Reads `claim.expectations` / `claim.expectations_status` VERBATIM — recomputes nothing.
+
+/** Which state the drawdown-expectations panel renders for ONE claim:
+ *   - "present"     — a resolved `expectations` payload exists; the table renders (pre-existing, unchanged).
+ *   - "unavailable" — this request's per-claim compute raised an exception (`expectations_status ===
+ *                     "unavailable"`); a calm inline note renders instead of a table (NEW, iter-29).
+ *   - "absent"      — no `expectations` and no `expectations_status` (the pre-existing honest-None cohort-
+ *                     unresolvable case); the panel renders nothing (unchanged). */
+export type DrawdownExpectationsPanelState =
+  | { kind: "present"; expectations: DrawdownExpectations }
+  | { kind: "unavailable" }
+  | { kind: "absent" };
+
+/**
+ * Resolve which state `DrawdownExpectationsPanel` should render for one claim (PURE, read-only — no
+ * client-side recompute of anything). `"unavailable"` (a genuine per-claim compute failure THIS request)
+ * is DISTINCT from `"absent"` (the pre-existing, unaffected "no expectations, no status field" case) so the
+ * panel can disclose a transient failure honestly instead of rendering it identically to "not applicable".
+ */
+export function resolveDrawdownExpectationsPanelState(claim: CertifiedClaim): DrawdownExpectationsPanelState {
+  if (claim.expectations) {
+    return { kind: "present", expectations: claim.expectations };
+  }
+  if (claim.expectations_status === "unavailable") {
+    return { kind: "unavailable" };
+  }
+  return { kind: "absent" };
+}
+
 // --- claim-row presentation (goal-mcp-loop iter-4) — regime label + honest title/linkback --------------
 // PURE, read-only helpers the `/evidence` ClaimRow consumes to deliver J-04 (regime-conditioned evidence,
 // "clearly labeled with the regime it holds in") WITHOUT regressing J-05 (the leadership score row's title
diff --git a/config.yaml b/config.yaml
index 1951bde6..40125bd7 100644
--- a/config.yaml
+++ b/config.yaml
@@ -881,6 +881,13 @@ research:
   # the research read path), NOT a displayed value. Boot-validated `>= 1`; the SINGLE source of this batch
   # size — there is NO inline batch literal in research.py / forward_testing.py (no-magic-numbers).
   read_batch_size: 2000
+  # iter-29 audit (AG-8) — the RUN-COUNT width of `_factor_observations`'s join-accumulator chunk (a
+  # different unit from `read_batch_size`, which counts ROWS for `yield_per`). Peak live accumulator =
+  # this x symbols-per-run (~429 on the current basis), so 100 runs/chunk holds ~55K pairs instead of the
+  # full 792,507 (measured h=20, 19 chunks, SQL wall time UNCHANGED — the scoped index seeks are no slower
+  # than the single covering-index scan). Must stay well below the live distinct-run count per horizon
+  # (1,812-1,871 today) or the loop degenerates to one chunk and bounds nothing. Boot-validated `>= 1`.
+  factor_join_run_chunk: 100
   # iter-55 (J-112) — rows-per-page of the Regime × Phase × Factor ranked combination table. The
   # pagination is a pure client-side view transform; this is the SINGLE source of the 30-rows/page
   # constant (served in the lab payload so the frontend reads it — no `30` literal in research.py).
diff --git a/incredible_auto_dev/.claude/agents/auditor.md b/incredible_auto_dev/.claude/agents/auditor.md
index 3be57d3c..f8b6c6c0 100644
--- a/incredible_auto_dev/.claude/agents/auditor.md
+++ b/incredible_auto_dev/.claude/agents/auditor.md
@@ -3,8 +3,8 @@ name: auditor
 description: Post-QA auditor. Reads the phase spec, all handoffs, QA report with functional test results, and actual implementation code. Skeptically assesses whether the phase goal was truly achieved. Applies fixes for critical issues found. Writes audit report with PASS, PASS_WITH_GAPS, or FAIL verdict.
 model: claude-opus-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.1
-last_updated: 2026-07-03
+version: 1.2.0
+last_updated: 2026-07-28
 ---
 
 # Auditor Agent
@@ -32,13 +32,35 @@ You perform a post-QA audit to determine whether the phase truly achieved its in
 
 ## Process
 
-### 1. Verify DEFINITION OF DONE
-
-For each numbered item in the spec's DEFINITION OF DONE, verify it is actually implemented:
-- Trace through the actual code, not just the handoff description
-- Check state transitions are enforced in backend logic, not just frontend
-- Verify API endpoints exist and return the right shapes
-- Verify the acceptance criteria are genuinely met, not just partially addressed
+### 1. Verify DEFINITION OF DONE (risk-ranked spot-verification)
+
+<!-- SPEED-19: the exhaustive per-item re-trace duplicated work the reviewer
+     (code-level) and QA (live functional rows) already did — a third full
+     spec-compliance pass. The full trace now goes where audit judgment adds
+     value; mechanical items already verified twice are accepted WITH CITATION. -->
+
+For each numbered item in the spec's DEFINITION OF DONE, run the FULL code trace
+(through the actual code, not the handoff description) when ANY of these holds:
+
+- **(a) Risk class** — the item involves state transitions, data mutation or
+  persistence, auth/security, or money.
+- **(b) Contradiction** — any artifact contradicts another about it (spec vs
+  dev handoff vs review report vs a QA row). The contradiction itself is the
+  trigger, even when QA is green.
+- **(c) Review doubt** — the reviewer marked `spec_alignment: partial` or filed
+  a spec-category issue touching the item.
+- **(d) Your own leads** — your Steps 2-4 work surfaced a suspicious path
+  through it.
+
+For the REMAINING mechanical items (endpoint exists, page renders, field
+displayed) that a QA functional-test row executed against the RUNNING system:
+accept the reviewer's PASS plus that QA row as verification — and CITE both
+(the review report's issue-list state and the exact QA row) next to the item in
+your report. An item with neither citation gets the full trace; so does any
+item you cannot map to a specific QA row. When tracing, still check state
+transitions are enforced in backend logic (not just frontend), API endpoints
+return the right shapes, and acceptance criteria are genuinely met — not just
+partially addressed.
 
 ### 2. Assess user workflow completeness
 
@@ -188,7 +210,7 @@ The dev handoff claimed the Stooq ingest tool was safe: "the API key is read fro
 - Do NOT pass a phase just because QA passed. QA tests what was implemented; you assess whether what was implemented is correct.
 - Do NOT mark FAIL for OBSERVATION-level issues.
 - Do NOT rewrite working implementations. Fix surgical issues only.
-- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone.
+- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone; for MECHANICAL DoD items only (Step 1), a reviewer PASS plus an executed QA row together are citable verification — a prose claim never is.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/.claude/agents/browser-qa-agent.md b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
index 749d9bdf..e3f1763e 100644
--- a/incredible_auto_dev/.claude/agents/browser-qa-agent.md
+++ b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
@@ -3,8 +3,8 @@ name: browser-qa-agent
 description: Browser QA agent. Executes user-visible UI tests through browser automation using Chrome MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer completes.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.2
-last_updated: 2026-07-04
+version: 1.1.0
+last_updated: 2026-07-28
 ---
 
 # Browser QA Agent
@@ -33,14 +33,20 @@ Before running any tests:
 
 For each UT-XX test case:
 1. Read the preconditions — ensure state is correct before starting
-2. Execute each step using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
+2. Execute the plan's steps exactly using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
 3. After each step, verify the expected state before proceeding
 4. At the end, record: PASS or FAIL
 
+Per-test budget (hard rules):
+- Execute the plan's steps exactly — never browse pages the plan does not name.
+- A failing selector gets at most 2 recovery attempts: one alternative locator, then one `get_text` to confirm the element truly is not rendered. Then record FAIL with evidence and move to the next test. If a selector fails because the page genuinely changed this iteration, that is a finding — record it; the budget exists to stop exploratory wandering, not to suppress real failures.
+- Never debug or restart the app — that is a SKIPPED with reason, per the skill rules.
+- Never re-run a test that already passed this invocation.
+
 For PASS: note what was verified (e.g., "button 'Create Item' clicked, redirected to /items/1, 'Item saved' toast visible")
 For FAIL: note exact failure with evidence (e.g., "Form submitted but no validation message appeared, console error: TypeError at line 42")
 
-Take screenshots of key states and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
+Take ONE screenshot per test, at the acceptance state (the state the expected-result describes), plus one on failure, and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
 
 ### Step 2: Write results
 
@@ -88,7 +94,8 @@ Wait for page load after navigation and after actions that trigger page changes.
 
 Screenshots directory: `reports/qa/<phase>-evidence/`
 Create it with `mkdir -p` before taking screenshots.
-Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
+ONE screenshot per test, taken at the acceptance state; add one more only on failure.
+Naming: `UT-01-result.png` (pass), `UT-02-fail.png` (failure), etc.
 
 ## Rules
 
@@ -101,6 +108,13 @@ Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
 
 ## Golden replay script (goal mode only)
 
+**Golden-first setup:** before driving any journey, list
+`runs/goal-session-<sid>/journey-scripts/`. If a golden covers the journey's
+setup prefix (sign-in, seed navigation to the working surface), replay its
+exact steps verbatim instead of re-deriving selectors, and do not re-verify
+intermediate states the golden already asserts — your judgment starts where
+the plan's NEW steps start.
+
 In goal mode the dispatch wrapper gives you a **golden-script directory**
 (`runs/goal-session-<sid>/journey-scripts/`). For **every journey you verify
 PASS**, also write a self-contained deterministic replay script to
diff --git a/incredible_auto_dev/.claude/agents/demo-narrator.md b/incredible_auto_dev/.claude/agents/demo-narrator.md
index c7c82d6b..f7b271d0 100644
--- a/incredible_auto_dev/.claude/agents/demo-narrator.md
+++ b/incredible_auto_dev/.claude/agents/demo-narrator.md
@@ -1,11 +1,11 @@
 ---
 name: demo-narrator
 description: Per-iteration product demonstrator. Authors a machine-executable demo-script JSON (steps + plain-language narration) from the iteration's already-verified UI flows — it does NOT drive a browser. The deterministic Playwright runner (demo_runner.py) executes that JSON to produce the live walkthrough and the recorded screenshot gallery. Flags steps added or changed this iteration as `[NEW]`. Showcase, not QA — a failed step is a soft note, never a hard pipeline fail. Modes (selected by the dispatch wrapper) - record / live (this iteration's working surface) and session (the whole working product across iterations).
-model: claude-sonnet-5
+model: claude-haiku-4-5
 tools: [Read, Glob, Grep, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.1.0
-last_updated: 2026-07-26
+version: 2.2.0
+last_updated: 2026-07-28
 ---
 
 # Demo Narrator — demo-script author
diff --git a/incredible_auto_dev/.claude/agents/goal-decomposer.md b/incredible_auto_dev/.claude/agents/goal-decomposer.md
index d666788a..fb64ccc1 100644
--- a/incredible_auto_dev/.claude/agents/goal-decomposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-decomposer.md
@@ -1,11 +1,11 @@
 ---
 name: goal-decomposer
-description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals), the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md. Picks lean or full depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only spec.
+description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals), the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md. Picks lean, full, or evidence depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only spec.
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.3.0
-last_updated: 2026-07-17
+version: 2.4.0
+last_updated: 2026-07-28
 ---
 
 # Goal Decomposer Agent
@@ -26,15 +26,15 @@ The invocation prompt communicates which mode you are in via a `Mode:` line:
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
-1. `.claude/project-template.md` — project stack, architecture principles
-2. `.claude/core.md` and `.claude/workflow.md` — universal rules and pipeline semantics
+1. `.claude/project-template.md` — read ONLY the stack and architecture-principles sections: Grep for those section headers first, then Read just those sections. The rest of the file (test commands, run commands, never-commit list) is for executing agents, not for planning.
+2. Do NOT read `.claude/core.md` or `.claude/workflow.md`. Every pipeline semantic you need — depth rules, the spec format, verdict flow — is in THIS body. Consult `workflow.md` only when you need a specific section this body does not cover, and read only that section.
 3. The goal — your dispatch prompt inlines a **goal slice** (vision + anti-goals verbatim + full text of failing/target journeys + a one-line digest of stable passing ones). Use it as your primary goal source. Read the full `docs/goal.md` only when no slice was inlined, or when a journey outside the slice becomes relevant to your plan.
 4. Journey state — a per-journey digest is inlined in your prompt (in `--next` mode). Read `runs/goal-session-<sid>/state/journey-history.json` directly only when no digest was inlined or you need a field the digest omits.
 5. Iteration state — `runs/goal-session-<sid>/state/iteration-state.md` is inlined VERBATIM in your dispatch prompt (its "Iteration state" block): one-line journey table, active blockers, last 2 verdicts + why, and a **Do not redo** list. Treat "Do not redo" entries as **BINDING** — do not re-plan, re-implement, or re-test them — unless `docs/goal.md` changed for that item. An absent file (iteration 0) inlines as "(first iteration — no prior state)". Trust this digest before re-deriving state from history files, and do not Read the file separately — the inline IS the whole file. Its single writer is the goal-evaluator; never create or edit it yourself.
 6. `runs/goal-session-<sid>/state/blueprint.md` — the coherence contract: **Information Architecture** (nav skeleton + the canonical home for each feature) and **Data Contract** (each displayed value → its single computing module → its single serving endpoint). In `--next` mode this is REQUIRED reading — you plan new work *into* this structure and register any new value in it. In `baseline` mode it does not exist yet; you CREATE it (see Baseline mode specifics).
 7. `runs/goal-session-<sid>/iter-<N-1>/eval.md` — most recent evaluator verdict and recommendation (in `--next` mode)
 8. `runs/goal-session-<sid>/iter-<N-1>/coherence.md` — last coherence verdict (in `--next` mode). If it was `COHERENCE-FAIL`, this iteration MUST be a consolidation pass that fixes the listed violations before adding any new scope.
-9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work
+9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work. Scope this exploration to the target journeys' surfaces only; the blueprint and the iteration-state "Do not redo" list are authoritative for what already exists — never re-walk the app tree to rediscover it.
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md` or `runs/goal-session-<sid>/state/lessons.md`. The orchestrator script (`run-goal.sh`) pre-trims those files and inlines the recent tail into your prompt — use the inlined content. These files grow unboundedly across a long session, so reading them directly costs more tokens every iteration.
 
@@ -53,7 +53,8 @@ Write the iteration spec to `docs/phases/goal-<sid>-iter-<N>.md`. The file MUST
 - **Session ID:** <sid>
 - **Iteration:** <N>
 - **Mode:** baseline | next
-- **Depth:** lean | full
+- **Depth:** lean | full | evidence
+- **Full trigger:** <1|2|3|4> — <one-line reason>  (REQUIRED when Depth is full; omit at other depths)
 - **Target journeys:** J-01, J-03, J-07
 - **Required-still-passing journeys:** J-02, J-04
 - **Anti-goal reminders:**
@@ -136,6 +137,8 @@ separate functional test plan, so these lines are that plan's seed.
 
 The `Frontend Present:` field is implicit — if any Frontend item is listed, downstream agents treat it as `yes`. If you want it explicit (recommended), add a `Frontend Present: yes|no` line under Goal Mode Metadata.
 
+Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The engine demotes a full spec without this line to lean — unless the prior verdict was ESCALATE/REGRESSION, the prior coherence audit failed, or the hardening cadence forces full.
+
 ## Picking target journeys (priority rubric — apply top-down)
 
 1. **Regressed journeys first.** Anything `regressed` outranks all new work — a shrinking product is worse than a slowly-growing one.
@@ -144,6 +147,8 @@ The `Frontend Present:` field is implicit — if any Frontend item is listed, do
 4. **Smallest spec wins ties.** Among equals, pick the journey with the smallest concrete change set — small iterations are easier to score and revert.
 5. **Never bundle two risky journeys.** One iteration may carry several trivial journeys OR one risky journey (data-model change, provider integration, cross-cutting refactor) — never two risky ones; a joint failure is undiagnosable.
 6. **Don't pick a human-blocked journey.** If the evaluator marked a blocker human-owned (STALLED-class: credentials, network access, sanction), do not re-plan the same blocked work — plan a different journey, or if none exists, write the one-line "all remaining work is human-blocked" spec so the evaluator can halt honestly.
+<!-- rule 5 is SPEED-8's territory; rule 7 (SPEED-9) composes with it -->
+7. **Never plan an evidence-only iteration.** An iteration whose ONLY deliverable is evidence capture, screenshot retakes, or demo recording is not a plan — evidence gaps ride the make-up lane instead (the `evidence_makeup` / `pending_infra` booleans in journey-history), piggybacking on whatever real iteration runs next. The one exception: when the prior evaluator's next-step asks ONLY for evidence on already-passing journeys, write the iteration as `Depth: evidence` (capture + evaluate only — the engine skips developer/reviewer).
 
 Mini example — good vs bad target selection with the same state (J-03 regressed, J-07 failing-and-unblocks-J-08/J-09, J-11 failing, big):
 - ✚ Target `J-03` alone (rule 1), depth lean, Required-still-passing = the journeys sharing J-03's contract values + smoke set. Next iter: J-07.
@@ -168,12 +173,14 @@ Mini example — good vs bad target selection with the same state (J-03 regresse
      value's computing module or serving endpoint.
   3. **Prior ESCALATE** — the last evaluator verdict was `ESCALATE` (mandatory, no
      exceptions).
-  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 4)
+  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 6)
      consecutive dispatched iterations were all lean (the engine inlines
      "Consecutive lean iterations" in your prompt; the count resets on any full).
      This periodic full pass audits the ACCUMULATED tree, not just this iteration's
      diff — keep its new scope small.
 
+- **evidence** — all Target journeys are already recorded passing and the deliverable is visual evidence only (fresh screenshots / walkthrough recording); the engine dispatches capture + evaluation only, skipping developer and reviewer. Use it only in the rule-7 exception case above — never as a substitute for real work.
+
 "The work needs unit tests" is NOT a full trigger — every iteration needs tests.
 When no trigger holds, lean is not a risk you are taking; it is the design.
 
@@ -232,7 +239,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND; lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
@@ -250,6 +257,8 @@ If any check fails, fix the spec before writing it — downstream agents execute
 - **Log interpretation calls to the assumption ledger.** When a spec decision required interpreting the goal — the goal/journey text is ambiguous about X and you chose reading Y — append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use; never rewrite prior entries), formatted exactly as: `## iter-<N> — goal-decomposer` on its own line, then `**Ambiguity:** <what the goal leaves open>`, `**We chose:** <the reading this iteration builds on>`, `**Reversible:** yes|no`, each on its own line. Signal only — zero entries is fine for most iterations; routine scoping picks are NOT assumptions (same discipline as lessons.md). Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
 - **Conform to the blueprint, and keep it current.** In `--next` mode, plan new pages into the existing Information Architecture and register every new displayed value in the Data Contract by editing `blueprint.md` directly. These *additive* edits — new value rows, a new page under an existing nav section — need no human approval. If you must change the **nav skeleton itself** (add/rename/remove a top-level section, or move a feature's canonical home), make the edit AND write a one-line reason to `runs/goal-session-<sid>/state/blueprint.reapproval-requested`. By default `run-goal.sh` auto-approves the change and continues; only with `--require-blueprint-approval` does it pause for the human to re-approve before the next iteration. Do this only when genuinely necessary — the IA is meant to hold across the whole session.
 - **Never duplicate a contract value.** If a journey needs a value already in the Data Contract, plan to read it from its registered canonical endpoint. Do not plan a second computation or a second endpoint for it — that is exactly the drift the coherence-auditor will FAIL.
+- **Do not restate stable journeys' full `goal.md` text.** Reference journey IDs plus the acceptance delta — the goal slice in your prompt already digests them; copying their full text back into the spec is pure duplication.
+- **Do not paste blueprint content into the spec.** Reference the Information Architecture section / Data-Contract row by name. Both anti-restatement rules cut duplication ONLY — they NEVER mean shortening TC- test scenarios or interface/data-contract definitions (D6 forbids length budgets on those).
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index 27b15acf..87c0a43c 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.8.0
-last_updated: 2026-07-26
+version: 1.9.0
+last_updated: 2026-07-28
 ---
 
 # Goal Evaluator Agent
@@ -19,20 +19,19 @@ Your methodology is `.claude/skills/goal-evaluation-methodology.md` — read it
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — especially **Must-have user journeys** and **Anti-goals**
-2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders)
-3. `runs/<iter-name>/plan.md` — execution plan (full mode only; absent in lean iterations)
-4. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
-5. `docs/handoffs/<iter-name>-dev.md` — dev handoff
-6. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only)
-7. `reports/reviews/<iter-name>-review.md` — review verdict
-8. `reports/qa/<iter-name>-qa.md` — QA verdict (full mode only)
-9. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
-10. `reports/qa/<iter-name>-evidence/` — screenshots
-11. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
-12. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
-13. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
-14. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
-15. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
+2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders). The spec is authoritative for targets — do NOT also read `runs/<iter-name>/plan.md` (the orchestrator's restatement for the developer; SPEED-9 dropped it from your inputs).
+3. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
+4. `docs/handoffs/<iter-name>-dev.md` — dev handoff
+5. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only). Read ONLY its Executive Verdict and Findings sections — its verdict already gated the pipeline; re-reading the full trace re-derives judgment that already fired.
+6. `reports/reviews/<iter-name>-review.md` — review verdict
+7. `reports/qa/<iter-name>-qa.md` — QA report (full mode only). Read ONLY the verdict line, the UI Evolution Audit block, and any FAIL rows — same already-gated rule as the audit handoff.
+8. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
+9. `reports/qa/<iter-name>-evidence/` — screenshots
+10. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
+11. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
+12. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
+13. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
+14. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md`. The orchestrator script (`run-goal.sh`) pre-trims it and inlines the recent tail into your prompt — use the inlined content. The file grows unboundedly across a long session.
 
@@ -110,6 +109,16 @@ the second consecutive infra failure: stop treating it as transient — the brow
 infrastructure is a human-owned blocker (STALLED-class, decision tree C.2); never loop a
 third silent retry.
 
+**`evidence_makeup` (SPEED-9, optional boolean).** Set `"evidence_makeup": true` on a
+journey whose product behavior is confirmed but whose capture artifact is cosmetically
+defective (methodology A.7: wrong-but-valid data range in the screenshot, missing or
+mis-cropped walkthrough recording). Keep the journey's evidence-based status — this flag
+never downgrades it; it asks the next iteration to re-capture as a passenger task or via
+`Depth: evidence`, never as an iteration goal. Clear the field (omit it) the moment a
+fresh capture lands — whatever the outcome. Do not conflate with `pending_infra` above:
+that flag means the browser infrastructure OWES evidence; this one means the evidence
+exists and only its presentation is wrong.
+
 **`spec_hash` — the goal-edit drift record.** Once per evaluation, run `python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md` (prints `{"J-NN": "<sha256>"}`). For every journey whose status you set from THIS iteration's evidence (`passing`, `failing`, `partial`, and baseline `already_passing`), record its current hash as `spec_hash`. For journeys you did not verify this iteration, carry the existing `spec_hash` forward unchanged — or leave it absent (pre-NEED-9 histories have none; never invent one). Never copy a new hash onto a journey you did not re-verify: the hash asserts "this status was verified against exactly this goal text", and the deterministic achievement gate audits it.
 
 **When `iter-<N>/journeys-changed.md` exists:** each listed journey's goal.md text changed AFTER its recorded pass, so that pass is void. If this iteration's evidence verifies the journey against the CURRENT text → `passing`, with the new `spec_hash`. Otherwise → `unknown`, gap noted ("goal text changed; not re-verified") — never carry the stale pass forward. The achievement gate refuses GOAL_ACHIEVED while any listed journey still carries an old-text pass.
@@ -123,7 +132,7 @@ Append a new entry to `runs/goal-session-<sid>/state/evaluator-log.md`:
 
 **Date:** <ISO timestamp>
 **Verdict:** <VERDICT>
-**Depth dispatched:** lean | full
+**Depth dispatched:** lean | full | evidence
 **Journey deltas:**
 - Newly passing: J-XX, J-YY
 - Newly failing: <none or list>
@@ -178,7 +187,7 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 # Iteration <N> Evaluation
 
 **Verdict:** <VERDICT>
-**Depth Recommendation For Next Iteration:** lean | full
+**Depth Recommendation For Next Iteration:** lean | full | evidence
 
 ## Summary
 
@@ -245,7 +254,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 
 - **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, this iteration's `coherence.md` is not `COHERENCE-FAIL`, AND no journey listed in `journeys-changed.md` remains un-re-verified against the current goal text. Loop halts with success.
 
-- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
+- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Recommend `evidence` depth when EVERY remaining gap is a capture/recording task on already-working features (`evidence_makeup`/`capture-defect` gaps) — the engine then runs capture + evaluation only, no developer/reviewer. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
 
 - **ESCALATE** — a lean iteration uncovered ambiguity, complexity, or an issue that warrants the full pipeline (audit, ux-regression, closure). The next iteration MUST run as `full`. Use sparingly — escalating every iter defeats the purpose of adaptive depth.
 
@@ -272,6 +281,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
 - If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
+- Never recommend — and never score as blocking — a next iteration whose only content is evidence capture, screenshot retakes, or demo recording. Evidence gaps on working features ride the make-up lane (`evidence_makeup`, methodology A.7) or a `Depth: evidence` recommendation; prior evidence for unchanged code stays valid (methodology A.6). Goal-edit drift (`journeys-changed.md`) always outranks evidence durability.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/.claude/agents/iteration-summarizer.md b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
index 756b5314..02f863b2 100644
--- a/incredible_auto_dev/.claude/agents/iteration-summarizer.md
+++ b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
@@ -4,8 +4,8 @@ description: Post-iteration summarizer. Reads the iteration's artifacts (dev han
 model: claude-sonnet-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.2.0
-last_updated: 2026-07-26
+version: 1.3.0
+last_updated: 2026-07-28
 ---
 
 # Iteration Summarizer
@@ -104,14 +104,14 @@ Write exactly this skeleton — keep the labels and the order:
 ```
 ## In plain words
 
-**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, aggregate every currently-passing journey. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
+**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, re-derive this EVERY iteration from the `name` fields of the currently-passing journeys in `journey-history.json` — never copy the previous summary's sentence verbatim, and any journey whose status changed this iteration must appear or disappear from the list accordingly. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
 
-**What changed this time:** <Plain-language description of what is newly available or fixed this iteration. Tie back to user experience ("You can now invite a teammate by email"). If nothing user-facing changed, write: "Behind-the-scenes work — nothing visibly new this round" and name the area in friendly terms (e.g. "made the app faster", "tightened security").>
+**What changed this time:** <MUST name the concrete user-visible change: the screen or page by its visible name and what the user now sees or does there ("The Watchlist page now has an 'Export CSV' button that downloads your list."). Never open with a generic sentence like "improvements were made". The sentence "Behind-the-scenes work — nothing visibly new this round" is permitted ONLY when the iteration changed zero product source files — check `status.json` `changed_files` and the dev handoff's Files Changed list before using it — and even then it must name the concrete area that was worked on ("sped up the price-history loading code", "captured fresh proof screenshots of the Desk screen").>
 
 **What's next:** <Plain-language version of the Next step. Phrase as the next thing the product will gain ("Next we'll let you reset a forgotten password"). One short sentence.>
 ```
 
-**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): write "Behind-the-scenes work — nothing visibly new this round." in **What changed this time**, keep the cumulative "What you can do now" unchanged from the prior iteration's plain-words block if you can read it (look at `reports/phase-<prev-phase-id>-iteration-summary.md` if obvious from context; otherwise describe the latest known capabilities or write "Same as before — no user-facing change.").
+**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): first check `status.json` `changed_files` and the dev handoff's Files Changed list. If product source files DID change, do NOT use the generic behind-the-scenes sentence — say in friendly words what part of the product the work touched and what it does now ("the price history behind the Desk screen now loads faster"). Only if zero product source files changed may **What changed this time** read "Behind-the-scenes work — nothing visibly new this round" — and it must still name the concrete area worked on ("captured fresh proof screenshots of the Desk screen"). For **What you can do now**, re-derive the list from the passing-journey names in `journey-history.json` EVERY iteration (phase mode: from the cumulative artifacts) — never copy the previous summary's sentence verbatim; a journey whose status changed this iteration must appear or disappear accordingly.
 
 **First iteration of a goal session** (no prior summaries, journey-history may be empty or have only `unknown` statuses): write "Just getting started — nothing for users to try yet." in **What you can do now**, and describe groundwork in **What changed this time**.
 
@@ -147,7 +147,12 @@ Numbers come from counting deltas in the evaluator-log entries. Do not invent jo
 
 ## What was done
 
-3–8 bullets, terse, action-oriented. Sources:
+The FIRST bullet is fixed-format. It MUST be one of these two — nothing else may be first:
+
+- `Product changes: <comma-separated changed product files and/or routes>` — sourced from `status.json` `changed_files` and the dev handoff's Files Changed list (e.g. `Product changes: apps/frontend/app/desk/page.tsx, /api/desk/topup`)
+- exactly `No product change this iteration.` — when neither source lists a changed product file
+
+Then 3–8 further bullets, terse, action-oriented. Sources:
 
 - `implementation-summary.md` "Features Implemented" if present (highest fidelity)
 - else `dev-handoff.md` "Summary" + a synthesized 1-bullet-per-major-file-or-area from "Files Changed"
diff --git a/incredible_auto_dev/.claude/agents/readme-maintainer.md b/incredible_auto_dev/.claude/agents/readme-maintainer.md
index c533bcfb..0daa7d35 100644
--- a/incredible_auto_dev/.claude/agents/readme-maintainer.md
+++ b/incredible_auto_dev/.claude/agents/readme-maintainer.md
@@ -1,11 +1,11 @@
 ---
 name: readme-maintainer
 description: Project README maintainer (goal mode). After each iteration, refreshes the project-root README.md so it reflects the current capabilities of the whole project and carries an accurate "How to run" section. Edits only marker-delimited AUTO blocks so hand-written prose is preserved, and grounds every install/run/test command in .claude/project-template.md. Non-blocking showcase/maintenance step — never gates the pipeline.
-model: claude-sonnet-5
+model: claude-haiku-4-5
 tools: [Read, Write, Edit, Glob, Grep]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.0
-last_updated: 2026-07-26
+version: 1.2.0
+last_updated: 2026-07-28
 ---
 
 # README Maintainer
diff --git a/incredible_auto_dev/.claude/agents/reviewer.md b/incredible_auto_dev/.claude/agents/reviewer.md
index 4ffd14f6..cb3016e6 100644
--- a/incredible_auto_dev/.claude/agents/reviewer.md
+++ b/incredible_auto_dev/.claude/agents/reviewer.md
@@ -4,8 +4,8 @@ description: Code reviewer. Reads dev handoffs and diffs to assess implementatio
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write, Edit]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.2.1
-last_updated: 2026-07-16
+version: 1.3.0
+last_updated: 2026-07-28
 ---
 
 # Reviewer Agent
@@ -79,9 +79,12 @@ For each changed file, verify:
 - [ ] No refactoring of code outside the task scope
 
 ### UI quality (if frontend was changed)
-- [ ] UI evolved to reflect the new backend capability (per workflow.md UI EVOLUTION POLICY)
-- [ ] New entity types have list + detail pages reachable from navigation
-- [ ] Sidebar updated if a new top-level workflow was introduced
+<!-- SPEED-18: the UI-EVOLUTION/reachability questions (did the UI evolve, are new
+     entities reachable, was the sidebar updated) are owned by qa's live UI
+     Evolution Audit (browser + screenshot evidence, gating) and the
+     coherence-auditor's blueprint-grounded Step 2 — a code reviewer answers
+     them by guessing at runtime behavior. This checklist keeps only what CODE
+     review can actually verify. -->
 - [ ] Frontend does not contain business logic (calls backend APIs only)
 - [ ] Uses component library from DESIGN SYSTEM — no raw HTML where components exist
 - [ ] Colors, spacing, and typography use token values from DESIGN SYSTEM — no arbitrary values
@@ -138,8 +141,6 @@ standards:
   test_quality: pass
   no_dead_code: pass
   no_hardcoded_localhost: pass
-  ui_evolved_with_capability: pass
-  navigation_updated: n/a
   architecture_principles: pass
 ```
 ````
@@ -175,8 +176,6 @@ standards:
   test_quality: pass | fail | n/a
   no_dead_code: pass | fail | n/a
   no_hardcoded_localhost: pass | fail | n/a
-  ui_evolved_with_capability: pass | fail | n/a
-  navigation_updated: pass | fail | n/a
   architecture_principles: pass | fail | n/a
 fix_tasks:                            # ONLY when verdict == FAIL
   - file: path/to/file.py
@@ -195,7 +194,7 @@ Per-file, max 80 words each. Skip files with no issues. No headers below H3.
 - The verdict line is required and parsed by scripts. Keep the exact `**Verdict:** ...` format.
 - `issues` must be a YAML list. Use `[]` if empty.
 - Every CRITICAL or MINOR issue must have `file`, `line`, and `fix`.
-- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `ui_evolved_with_capability` on a backend-only phase).
+- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `test_quality` on a docs-only phase).
 - Do NOT write a "## Standards Compliance" markdown checkbox section. The YAML `standards` field replaces it.
 - Do NOT write "## Issues Found" as a markdown table. The YAML `issues` field replaces it.
 - If verdict is PASS, omit `## Detailed Findings` entirely. No filler.
diff --git a/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md b/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
index 9ffc6ccc..46063f71 100644
--- a/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
+++ b/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
@@ -3,8 +3,8 @@ name: ux-regression-reviewer
 description: UX regression reviewer. Checks whether the UI evolved appropriately with the phase's new capabilities. Flags features that exist in backend but are invisible or undiscoverable in the UI. Flags existing user journeys that may have regressed. Runs after browser QA and before the main auditor.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-05-04
+version: 1.1.0
+last_updated: 2026-07-28
 ---
 
 # UX Regression Reviewer
@@ -20,27 +20,34 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. `reports/phase-{N}-user-visible-changes.md` — what changed for users
 4. `reports/phase-{N}-ui-surface-map.md` — affected surfaces
 5. `reports/phase-{N}-ui-test-results.md` — what was tested and found
-6. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
-7. `.claude/skills/ui-regression-scout.md` — methodology
+6. `reports/qa/<phase>-qa.md` — qa's UI Evolution Audit block (live-browser reachability evidence — cite it, don't re-derive it)
+7. In goal mode: `runs/goal-session-<sid>/iter-<N>/coherence.md` — the blueprint-grounded navigation/duplicate-home audit (read when present)
+8. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
+9. `.claude/skills/ui-regression-scout.md` — methodology
 
 ## Process
 
-### Step 1: Check UI evolution adequacy
+### Step 1: Check UI evolution adequacy (consume, don't re-derive)
 
-For each new capability listed in `user-visible-changes.md`:
-- Is there a navigation path to reach it? (Sidebar link, button, menu item)
-- Is it reachable within 2 clicks from the home page?
-- Is its label clear to a non-technical user?
-- Is there visual feedback when the capability is used?
+<!-- SPEED-18: reachability/click-depth/duplicate-home used to be asked FOUR
+     times per full iteration. The two best-evidenced askers own them now: qa's
+     live UI Evolution Audit (browser + screenshots, gating) and the
+     coherence-auditor's blueprint-grounded Step 2. Your Step 1 CONSUMES their
+     results and judges only what neither covers. -->
 
-Flag: "hidden capability" if it exists but has no navigation path.
-Flag: "undiscoverable capability" if it requires developer knowledge to find.
-Flag: "label confusion" if the UI label doesn't match what the feature does.
+Read qa's UI Evolution Audit result (and, in goal mode, `coherence.md`). Do NOT
+re-trace navigation paths or click-depth — cite their findings. Your own Step 1
+judgment covers what neither asker sees:
+- Is each new capability's label clear to a non-technical user?
+- Is there visual feedback when the capability is used?
 - Does the new UI follow the DESIGN SYSTEM tokens (colors, spacing, typography)?
-- Is the visual style consistent with pages from prior phases?
+- Is the rendered visual style consistent with pages from prior phases?
 - Are effects (glassmorphism, glows, gradients) applied consistently, not just on some pages?
 
+Flag: "label confusion" if the UI label doesn't match what the feature does.
 Flag: "visual inconsistency" if new pages deviate from the DESIGN SYSTEM or established style.
+Flag: "audit contradiction" if qa's UI audit or coherence.md flagged a reachability
+problem the other artifacts treat as resolved — quote both sides; do not re-test.
 
 ### Step 2: Check for regression in existing journeys
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/24-evidence-chasing-iterations.md b/incredible_auto_dev/.claude/anti-patterns/24-evidence-chasing-iterations.md
new file mode 100644
index 00000000..2ef89748
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/24-evidence-chasing-iterations.md
@@ -0,0 +1,9 @@
+## 24. Whole iterations spent chasing evidence for already-working features
+
+**Pattern:** The evaluator withholds a pass because the *capture artifact* is imperfect — a screenshot shows a different-but-valid data range than the spec's example numbers, or the walkthrough recording is missing — while the code, tests, and replay all confirm the behavior. The decomposer then plans an entire iteration whose only deliverable is retaking the photo or re-recording the video, and the engine runs the full developer→reviewer→browser-qa→judges pipeline around a no-op change. Worse, in lean depth the walkthrough used to be recorded in the showcase tail AFTER scoring, so a lean spec whose deliverable was "record the walkthrough" was structurally unpassable — it could only ESCALATE into an even more expensive full pass. Observed: tapeology `desk` iterations 10, 12, 13 (~6h of agent time; one screenshot, one impossible lean, one 3h full re-record) — only 1 of the last 5 iterations shipped product code.
+
+**Why it fails:** Evidence demands recurse into pipeline runs, but the pipeline's cost is sized for CODE change, not capture. Each recapture iteration produces the full artifact set (~30-40 reports) around zero product change, burying the signal a human reads; the verification chain (54% of all agent minutes in the desk session) re-verifies journeys whose code is byte-identical; and the demo-after-scoring ordering turns one cosmetic gap into an unbounded ESCALATE loop.
+
+**Prevention:** Three rails, all landed in the SPEED-9 package (2026-07-28). (1) *Evidence expires with change, not time* — methodology A.6: unchanged product code keeps prior screenshots/results/recordings valid (the engine feeds the evaluator deterministic `Prior walkthrough recording` + `Product diff this iteration` lines); goal-edit drift always outranks durability, and the no-screenshot rail still demands a citation. (2) *Capture defect ≠ product failure* — methodology A.7: score from the evidence that exists, record gap `capture-defect`, set `evidence_makeup: true`; the make-up capture rides the next iteration as a passenger or a `Depth: evidence` dispatch — NEVER as an iteration goal (decomposer rubric rule 7 enforces the planning side). (3) *The `evidence` micro-path records BEFORE scoring* — `CHAIN_LEAN_EVIDENCE_ONLY` skips developer/reviewer, runs browser capture, then demo-phase.sh, then evaluation, so an evidence gap costs ~30-40 min, not a pipeline. If you see an iteration spec whose deliverable is a screenshot or recording, the answer is `Depth: evidence` or the make-up lane — never a lean/full dispatch.
+
+---
diff --git a/incredible_auto_dev/.claude/anti-patterns/24-styled-verdict-cells-unparsed.md b/incredible_auto_dev/.claude/anti-patterns/25-styled-verdict-cells-unparsed.md
similarity index 96%
rename from incredible_auto_dev/.claude/anti-patterns/24-styled-verdict-cells-unparsed.md
rename to incredible_auto_dev/.claude/anti-patterns/25-styled-verdict-cells-unparsed.md
index 36f04850..aa993855 100644
--- a/incredible_auto_dev/.claude/anti-patterns/24-styled-verdict-cells-unparsed.md
+++ b/incredible_auto_dev/.claude/anti-patterns/25-styled-verdict-cells-unparsed.md
@@ -1,4 +1,4 @@
-## 24. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
+## 25. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
 
 **Applies to:** any parser that extracts machine verdicts (PASS/FAIL/SKIP) from agent-written markdown, and any gate that consumes the parsed result.
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/25-plan-line-suppresses-lane.md b/incredible_auto_dev/.claude/anti-patterns/26-plan-line-suppresses-lane.md
similarity index 96%
rename from incredible_auto_dev/.claude/anti-patterns/25-plan-line-suppresses-lane.md
rename to incredible_auto_dev/.claude/anti-patterns/26-plan-line-suppresses-lane.md
index 535bdbf1..a0d50b29 100644
--- a/incredible_auto_dev/.claude/anti-patterns/25-plan-line-suppresses-lane.md
+++ b/incredible_auto_dev/.claude/anti-patterns/26-plan-line-suppresses-lane.md
@@ -1,4 +1,4 @@
-## 25. A plan metadata line can silently suppress an entire verification lane
+## 26. A plan metadata line can silently suppress an entire verification lane
 
 **Applies to:** goal mode; any pipeline step whose execution is gated on a model-written metadata line rather than on the work the spec demands.
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index 1fb0a016..09161744 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -3,7 +3,7 @@
 One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
 only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
 nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
-headings; the next new entry takes the next free number (26) as `<NN>-<slug>.md` plus a
+headings; the next new entry takes the next free number (27) as `<NN>-<slug>.md` plus a
 row here (maintenance protocol §2).
 
 | # | Entry | Applies when | Rule (one line) |
@@ -31,5 +31,6 @@ row here (maintenance protocol §2).
 | 21 | [21-shared-tmp-accumulation.md](21-shared-tmp-accumulation.md) | temp files | Per-run TMPDIR isolation via chain-tmp.sh; never raw shared /tmp |
 | 22 | [22-scanner-flags-own-output.md](22-scanner-flags-own-output.md) | scan scoping | Scan the product; exclude the pipeline's own bookkeeping paths |
 | 23 | [23-prompt-argv-execve.md](23-prompt-argv-execve.md) | passing prompts to child processes | Prompt-sized content goes via stdin or file, never argv/env |
-| 24 | [24-styled-verdict-cells-unparsed.md](24-styled-verdict-cells-unparsed.md) | parsing verdicts out of agent markdown | Normalize emphasis and annotations; absence-of-verdict is never PASS |
-| 25 | [25-plan-line-suppresses-lane.md](25-plan-line-suppresses-lane.md) | gating a verification lane | Gate lanes on engine-parsed facts, not model-written plan prose |
+| 24 | [24-evidence-chasing-iterations.md](24-evidence-chasing-iterations.md) | evaluator/decomposer evidence demands | Evidence expires with change, not time; capture gaps ride the make-up lane or Depth: evidence — never an iteration goal |
+| 25 | [25-styled-verdict-cells-unparsed.md](25-styled-verdict-cells-unparsed.md) | parsing verdicts out of agent markdown | Normalize emphasis and annotations; absence-of-verdict is never PASS |
+| 26 | [26-plan-line-suppresses-lane.md](26-plan-line-suppresses-lane.md) | gating a verification lane | Gate lanes on engine-parsed facts, not model-written plan prose |
diff --git a/incredible_auto_dev/.claude/commands/goal.md b/incredible_auto_dev/.claude/commands/goal.md
index c779238a..5d2834ec 100644
--- a/incredible_auto_dev/.claude/commands/goal.md
+++ b/incredible_auto_dev/.claude/commands/goal.md
@@ -1,7 +1,7 @@
 ---
 description: Run Goal Mode until the goal is achieved or an existing rule halts/pauses it, inside this Claude Code session (interactive dispatch — bills to your interactive plan allowance).
 argument-hint: "[session-id] [extra run-goal.sh flags]"
-allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Read, Task, Write
+allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(scripts/automation/host-guard-adopt.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
 ---
 You are the **pump** for goal mode. Run the EXISTING goal-mode engine until the
 goal is achieved, blocked, halted, or paused by its existing rules. Do NOT add
@@ -12,10 +12,19 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
 1. **Session id:** parse `$ARGUMENTS`. The first token is the session id; if there
    is no first token, generate one like `interactive-<YYYY-MM-DD>-<short>` and
    tell the user what you chose. Any remaining tokens are passthrough flags.
-2. **Launch the engine** in the background (Bash with run_in_background) and
+2. **Host-guard confinement** (only when `project-extensions/host-guard/host-guard.env`
+   exists with `HOST_GUARD_ENABLED=1`): run
+   `scripts/automation/host-guard-adopt.sh --cli-root-of $$` — it confines THIS
+   already-running CLI session (and everything it will spawn) to the declared
+   caps, in place; instant and idempotent when already confined. No special
+   launch command is required. Only if it prints `FAILED`, tell the user to
+   relaunch via `scripts/automation/host-guard-exec.sh claude` (the from-birth
+   wrapper) — the engine's iteration gate re-verifies each iteration and would
+   pause (AWAITING_HOST_GUARD, resumable) on an unconfinable pump.
+3. **Launch the engine** in the background (Bash with run_in_background) and
    capture its PID:
    `./scripts/automation/run-goal.sh --session-id <sid> --interactive <passthrough flags>`
-3. **Run the pump loop** from the skill: await requests with
+4. **Run the pump loop** from the skill: await requests with
    `scripts/automation/goal-await-dispatch.sh` (foreground, `--max-wait 500`),
    dispatch each returned request as a subagent (`subagent_type` = the request's
    `agent`, `prompt` passed verbatim; pass the request's `model` as the Agent
@@ -29,7 +38,7 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
    pauses, and in the final status block. The full chain narrative is in the
    timestamped `runs/goal-session-<sid>/engine.log` (tell the user to `tail -f`
    it); you do not read it.
-4. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
+5. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
    `status` and the next step.
 
 This runs the work as interactive subagents in THIS session (billed to your
diff --git a/incredible_auto_dev/.claude/model-orchestration.md b/incredible_auto_dev/.claude/model-orchestration.md
index 02222742..5137bb5d 100644
--- a/incredible_auto_dev/.claude/model-orchestration.md
+++ b/incredible_auto_dev/.claude/model-orchestration.md
@@ -22,8 +22,8 @@ from it). Update this table in the same commit that changes the tier map.
 | Tier | Claude model | Used for | Why |
 |------|--------------|----------|-----|
 | strong | `claude-opus-5` | goal-evaluator, auditor, goal-proposer, two-key confirms, escalated retries | Judgment: verdicts, scoping, skeptical audit. Mistakes here mis-certify or mis-direct whole sessions |
-| standard | `claude-sonnet-5` | goal-decomposer (TOKEN-2 experiment 2026-07-15; effort stays max, D4 guard still covers it), developer, orchestrator, product-manager, reviewer, browser-qa, coherence-auditor, all showcase agents | Building and structured review. High volume — this tier dominates token spend |
-| light | `claude-haiku-4-5` | qa (procedural mode), release-manager | Fully proceduralized tasks with exact steps and output formats |
+| standard | `claude-sonnet-5` | goal-decomposer (TOKEN-2 experiment 2026-07-15; effort stays max, D4 guard still covers it), developer, orchestrator, product-manager, reviewer, browser-qa, coherence-auditor, iteration-summarizer | Building and structured review. High volume — this tier dominates token spend. The summarizer deliberately STAYS here: REP-4 raised its concreteness bar, and it is the human's primary reading surface |
+| light | `claude-haiku-4-5` | qa (procedural mode), release-manager, demo-narrator + readme-maintainer (TOKEN-9 experiment 2026-07-28: schema-constrained writers with deterministic safety nets — demo JSON is linted/executed by demo_runner.py, README edits are marker-scoped; revert per-agent on lint failures or AUTO-block corruption) | Fully proceduralized tasks with exact steps and output formats |
 
 Effort: headless dispatches get `--effort` from `scripts/automation/lib/agent_permissions.py`
 (`EFFORT_DEFAULT=max`). At `max`: goal-evaluator, goal-decomposer, auditor, goal-proposer,
diff --git a/incredible_auto_dev/.claude/skills/browser-workflow-executor.md b/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
index 1c11b2c8..a8293a94 100644
--- a/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
+++ b/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
@@ -41,7 +41,7 @@ First click the field, then type.
   "action": "screenshot"
 }
 ```
-Take screenshots at key states: before action, after action, on error.
+Take ONE screenshot per test, at the acceptance state (the state the expected-result describes), plus one on failure.
 
 ### Get page text content
 ```json
@@ -59,7 +59,7 @@ For each test case UT-XX:
 2. Execute each step from the test plan
 3. After each action, verify the expected intermediate state
 4. At the end, verify the expected final state
-5. Take a screenshot of the final state
+5. Take ONE screenshot at the acceptance state (add one more only on failure)
 6. Record: PASS or FAIL with evidence
 
 ## Evidence Collection
@@ -67,14 +67,16 @@ For each test case UT-XX:
 Screenshots directory: `reports/qa/<phase>-evidence/`
 Create before taking screenshots: `mkdir -p reports/qa/<phase>-evidence/`
 
+One screenshot per test, taken at the acceptance state; add one more only on failure.
+
 Naming convention:
-- `UT-01-initial.png` — state before test
-- `UT-01-action.png` — during the test (after key action)
-- `UT-01-result.png` — final state
+- `UT-01-result.png` — acceptance state (one per test)
 - `UT-02-fail.png` — failure state (for FAIL tests)
 
 ## Verification Techniques
 
+Batch assertions: verify ALL of a state's expected strings in ONE `get_text` call over the relevant container — never one call per assertion.
+
 ### Verify text is present
 Get page text and check for the expected string.
 
@@ -96,7 +98,7 @@ Navigate to list page, check that item name appears in the page text.
 Wait and retry the get_text action. If still not loaded after 3 attempts, mark as SKIPPED — timeout.
 
 ### Element not found
-Try alternative selectors. If still not found, mark specific step as failed with "element not found: <description>".
+A failing selector gets at most 2 recovery attempts: one alternative locator, then one `get_text` to confirm the element truly is not rendered. If still not found, mark specific step as failed with "element not found: <description>". If a selector fails because the page genuinely changed this iteration, that is a finding — record it; the budget exists to stop exploratory wandering, not to suppress real failures.
 
 ### Console error
 Note it as WARN in test results. Only mark as FAIL if it prevents the test from completing.
diff --git a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
index 73598aaf..c4a7c81c 100644
--- a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
@@ -60,6 +60,33 @@ your overall impression of the iteration.
    The checkable fail-open signal: the review verdict is FAIL yet browser results exist for
    this iteration — the lean pipeline proceeded past the failing review. That is an
    ESCALATE signal (tree below).
+6. **Evidence durability (SPEED-9).** Evidence does not expire with time — it expires with
+   CHANGE. When a journey's product code is unchanged since the iteration where its passing
+   evidence was captured, that evidence remains valid: the `last_evidence_path` screenshot,
+   its results row, AND the prior iteration's walkthrough recording (your dispatch prompt's
+   "Prior walkthrough recording" line names the newest one). Check change against
+   `iter-diff.md`'s file list vs the journey's surfaces; when the prompt's "Product diff
+   this iteration" line says EMPTY, ALL prior evidence is automatically still valid. Do not
+   demand a re-capture, and never downgrade a status for evidence age alone.
+   Two precedence rails: (a) goal-edit drift ALWAYS wins over durability — a journey listed
+   in `journeys-changed.md` needs fresh evidence against the CURRENT goal text no matter how
+   unchanged the code is (A.1 rule, unchanged); (b) the no-screenshot rail (A.3) demands a
+   screenshot EXISTS with a citation — durability only relaxes WHICH iteration it may come
+   from, never whether one is needed.
+7. **Capture defect ≠ product failure (SPEED-9).** When the code, tests, and/or replay
+   confirm the behavior but the capture ARTIFACT itself is cosmetically defective — the
+   screenshot shows a different-but-equally-valid data range than the spec's example
+   numbers, the walkthrough recording is missing or badly cropped — score the journey from
+   the code/replay/screenshot evidence that does exist, record the gap as `capture-defect`,
+   and set `evidence_makeup: true` on the journey in journey-history (same shape and
+   clearing rule as `pending_infra`: any fresh capture, pass or fail, clears it). The
+   make-up capture rides the next iteration as a passenger task or a `Depth: evidence`
+   recommendation — NEVER as a new iteration's goal.
+   Distinction: `pending_infra` = the browser infrastructure failed and evidence is OWED;
+   `evidence_makeup` = evidence exists and the product works — only the artifact's
+   presentation is wrong. Rail: this never applies when the asserted BEHAVIOR is unmet — a
+   screenshot showing wrong behavior is a failure, not a capture defect; only presentation
+   (range choice, crop, missing recording) can be defective while the behavior is confirmed.
 
 ## B. Anti-goal checklist (per category — answer each with yes/no + citation)
 
diff --git a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
index 44f43c18..1e25ebb5 100644
--- a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
+++ b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
@@ -146,6 +146,31 @@ one `goal-await-dispatch.sh` call together (multiple Agent calls in one message)
 then write all of their `.res` files. Request file names are unique, so two
 concurrent requests never collide.
 
+## Host-guard confinement (interactive pump)
+
+The engine's own self-wrap (run-goal.sh) confines only the HEADLESS engine tree.
+Interactive dispatches — every subagent, and every `pytest`/build/browser those
+subagents run through Bash — execute as descendants of THIS foreground CLI
+session and inherit ITS confinement. When the project declares host caps
+(`project-extensions/host-guard/host-guard.env`), that confinement is applied
+automatically — no special launch command is required:
+
+- the `/goal` command runs `scripts/automation/host-guard-adopt.sh
+  --cli-root-of $$` at session start, which confines the RUNNING CLI process
+  tree in place (scope adoption for memory/task/quota ceilings + a hard
+  `taskset` CPU mask on the tree, inherited by all future children);
+- with `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine re-verifies the pump at
+  every iteration boundary (via the `pid=` line in `.pump-alive` or the CLI
+  root it captured at launch) and auto-confines it again if needed, pausing
+  (`AWAITING_HOST_GUARD`, resumable) only when in-place confinement fails.
+
+Optional belt-and-braces: launching the CLI through
+`scripts/automation/host-guard-exec.sh claude` confines it from birth and also
+sets the BLAS/OMP thread-cap env vars (those cannot be injected into a running
+process). If the pause ever fires, relaunch via that wrapper and `/goal-resume`
+— do not disable the flag to make the pause go away; the caps exist because
+unconfined goal-mode load has hard-reset the host.
+
 ## Usage sidecar (token telemetry — protocol v2, optional, best-effort)
 
 Headless dispatches record per-invocation token usage (`claude_usage` telemetry
diff --git a/incredible_auto_dev/.claude/skills/plain-language.md b/incredible_auto_dev/.claude/skills/plain-language.md
index 44f749c7..d3312ace 100644
--- a/incredible_auto_dev/.claude/skills/plain-language.md
+++ b/incredible_auto_dev/.claude/skills/plain-language.md
@@ -28,6 +28,8 @@ recommendations). It does not change any machine-parsed format.
    correct password", not a function, class, endpoint, or stack trace.
 6. **End with an action.** Say what happens next, or what the owner should do,
    in one sentence a non-programmer could act on.
+7. **Concrete beats generic:** name the screen and the value the user sees, not
+   "improvements were made".
 
 ## Status words (single source)
 
diff --git a/incredible_auto_dev/.claude/workflow.md b/incredible_auto_dev/.claude/workflow.md
index 429e5edb..346308b0 100644
--- a/incredible_auto_dev/.claude/workflow.md
+++ b/incredible_auto_dev/.claude/workflow.md
@@ -23,7 +23,7 @@ Plan → Test Plan → Dev+Review loop → QA loop → Audit loop → Finalize
 | 7. QA | `qa-phase.sh` | qa (mode: validate) | `reports/qa/<phase>-qa.md` |
 | 8. UX Regression Review | `ux-regression-phase.sh` | ux-regression-reviewer | `reports/phase-{N}-ux-regression.md` |
 | 9. Audit | `phase-audit.sh` | auditor | `docs/handoffs/<phase>-audit.md` |
-| 10. Phase Closure | `phase-closure-check.sh` | phase-closure-auditor | `reports/phase-{N}-closure-verdict.md` |
+| 10. Phase Closure | `phase-closure-check.sh` | phase-closure-auditor (deterministic since 2026-07-28 — `closure_gate.py`; `CHAIN_CLOSURE_LLM=true` restores the agent dispatch) | `reports/phase-{N}-closure-verdict.md` |
 | 11. Finalize | `finalize-phase.sh` | release-manager | `runs/<phase>/summary.json`, PR (then updates `docs/architecture/` via `update-docs.sh`, non-blocking) |
 
 *Stages 5, 6, 8 are skipped for backend-only phases (`Frontend Present: no`) — N/A stubs are written automatically.*
@@ -64,7 +64,7 @@ Agents ONLY communicate through filesystem artifacts. No free-form messages betw
 | UI test results | `reports/phase-{N}-ui-test-results.md` | browser-qa-agent | ux-regression-reviewer, phase-closure-auditor |
 | What to click | `reports/phase-{N}-what-to-click.md` | ui-test-designer | operator (human), phase-closure-auditor |
 | UX regression report | `reports/phase-{N}-ux-regression.md` | ux-regression-reviewer | phase-closure-auditor |
-| Closure verdict | `reports/phase-{N}-closure-verdict.md` | phase-closure-auditor | finalize-phase.sh |
+| Closure verdict | `reports/phase-{N}-closure-verdict.md` | closure_gate.py (phase-closure-auditor when `CHAIN_CLOSURE_LLM=true`) | finalize-phase.sh |
 | Project goal | `docs/goal.md` | Human | orchestrator, developer, reviewer, qa |
 | Project architecture | `docs/architecture/*.md` (if present; created after the first finalized phase — absence is normal early on) | update-docs.sh | orchestrator, developer |
 | Framework architecture | `.claude/architecture/*.md` | update-docs.sh | Framework maintainers (reference) |
diff --git a/incredible_auto_dev/agents/auditor/agent.yaml b/incredible_auto_dev/agents/auditor/agent.yaml
index 3309c591..4fb7bedb 100644
--- a/incredible_auto_dev/agents/auditor/agent.yaml
+++ b/incredible_auto_dev/agents/auditor/agent.yaml
@@ -3,6 +3,6 @@ description: Post-QA auditor. Reads the phase spec, all handoffs, QA report with
   and actual implementation code. Skeptically assesses whether the phase goal was truly achieved. Applies
   fixes for critical issues found. Writes audit report with PASS, PASS_WITH_GAPS, or FAIL verdict.
 model_tier: strong
-version: 1.1.1
-last_updated: '2026-07-03'
+version: 1.2.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/auditor/body.md b/incredible_auto_dev/agents/auditor/body.md
index bf319805..e0a4fcbf 100644
--- a/incredible_auto_dev/agents/auditor/body.md
+++ b/incredible_auto_dev/agents/auditor/body.md
@@ -24,13 +24,35 @@ You perform a post-QA audit to determine whether the phase truly achieved its in
 
 ## Process
 
-### 1. Verify DEFINITION OF DONE
-
-For each numbered item in the spec's DEFINITION OF DONE, verify it is actually implemented:
-- Trace through the actual code, not just the handoff description
-- Check state transitions are enforced in backend logic, not just frontend
-- Verify API endpoints exist and return the right shapes
-- Verify the acceptance criteria are genuinely met, not just partially addressed
+### 1. Verify DEFINITION OF DONE (risk-ranked spot-verification)
+
+<!-- SPEED-19: the exhaustive per-item re-trace duplicated work the reviewer
+     (code-level) and QA (live functional rows) already did — a third full
+     spec-compliance pass. The full trace now goes where audit judgment adds
+     value; mechanical items already verified twice are accepted WITH CITATION. -->
+
+For each numbered item in the spec's DEFINITION OF DONE, run the FULL code trace
+(through the actual code, not the handoff description) when ANY of these holds:
+
+- **(a) Risk class** — the item involves state transitions, data mutation or
+  persistence, auth/security, or money.
+- **(b) Contradiction** — any artifact contradicts another about it (spec vs
+  dev handoff vs review report vs a QA row). The contradiction itself is the
+  trigger, even when QA is green.
+- **(c) Review doubt** — the reviewer marked `spec_alignment: partial` or filed
+  a spec-category issue touching the item.
+- **(d) Your own leads** — your Steps 2-4 work surfaced a suspicious path
+  through it.
+
+For the REMAINING mechanical items (endpoint exists, page renders, field
+displayed) that a QA functional-test row executed against the RUNNING system:
+accept the reviewer's PASS plus that QA row as verification — and CITE both
+(the review report's issue-list state and the exact QA row) next to the item in
+your report. An item with neither citation gets the full trace; so does any
+item you cannot map to a specific QA row. When tracing, still check state
+transitions are enforced in backend logic (not just frontend), API endpoints
+return the right shapes, and acceptance criteria are genuinely met — not just
+partially addressed.
 
 ### 2. Assess user workflow completeness
 
@@ -180,7 +202,7 @@ The dev handoff claimed the Stooq ingest tool was safe: "the API key is read fro
 - Do NOT pass a phase just because QA passed. QA tests what was implemented; you assess whether what was implemented is correct.
 - Do NOT mark FAIL for OBSERVATION-level issues.
 - Do NOT rewrite working implementations. Fix surgical issues only.
-- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone.
+- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone; for MECHANICAL DoD items only (Step 1), a reviewer PASS plus an executed QA row together are citable verification — a prose claim never is.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/agents/browser-qa-agent/agent.yaml b/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
index 58aaad92..76d80514 100644
--- a/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
+++ b/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
@@ -3,6 +3,6 @@ description: Browser QA agent. Executes user-visible UI tests through browser au
   MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer
   completes.
 model_tier: standard
-version: 1.0.2
-last_updated: '2026-07-04'
+version: 1.1.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/browser-qa-agent/body.md b/incredible_auto_dev/agents/browser-qa-agent/body.md
index 344b6a02..16dd3a95 100644
--- a/incredible_auto_dev/agents/browser-qa-agent/body.md
+++ b/incredible_auto_dev/agents/browser-qa-agent/body.md
@@ -25,14 +25,20 @@ Before running any tests:
 
 For each UT-XX test case:
 1. Read the preconditions — ensure state is correct before starting
-2. Execute each step using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
+2. Execute the plan's steps exactly using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
 3. After each step, verify the expected state before proceeding
 4. At the end, record: PASS or FAIL
 
+Per-test budget (hard rules):
+- Execute the plan's steps exactly — never browse pages the plan does not name.
+- A failing selector gets at most 2 recovery attempts: one alternative locator, then one `get_text` to confirm the element truly is not rendered. Then record FAIL with evidence and move to the next test. If a selector fails because the page genuinely changed this iteration, that is a finding — record it; the budget exists to stop exploratory wandering, not to suppress real failures.
+- Never debug or restart the app — that is a SKIPPED with reason, per the skill rules.
+- Never re-run a test that already passed this invocation.
+
 For PASS: note what was verified (e.g., "button 'Create Item' clicked, redirected to /items/1, 'Item saved' toast visible")
 For FAIL: note exact failure with evidence (e.g., "Form submitted but no validation message appeared, console error: TypeError at line 42")
 
-Take screenshots of key states and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
+Take ONE screenshot per test, at the acceptance state (the state the expected-result describes), plus one on failure, and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
 
 ### Step 2: Write results
 
@@ -80,7 +86,8 @@ Wait for page load after navigation and after actions that trigger page changes.
 
 Screenshots directory: `reports/qa/<phase>-evidence/`
 Create it with `mkdir -p` before taking screenshots.
-Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
+ONE screenshot per test, taken at the acceptance state; add one more only on failure.
+Naming: `UT-01-result.png` (pass), `UT-02-fail.png` (failure), etc.
 
 ## Rules
 
@@ -93,6 +100,13 @@ Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
 
 ## Golden replay script (goal mode only)
 
+**Golden-first setup:** before driving any journey, list
+`runs/goal-session-<sid>/journey-scripts/`. If a golden covers the journey's
+setup prefix (sign-in, seed navigation to the working surface), replay its
+exact steps verbatim instead of re-deriving selectors, and do not re-verify
+intermediate states the golden already asserts — your judgment starts where
+the plan's NEW steps start.
+
 In goal mode the dispatch wrapper gives you a **golden-script directory**
 (`runs/goal-session-<sid>/journey-scripts/`). For **every journey you verify
 PASS**, also write a self-contained deterministic replay script to
diff --git a/incredible_auto_dev/agents/demo-narrator/agent.yaml b/incredible_auto_dev/agents/demo-narrator/agent.yaml
index 72280d68..f4528336 100644
--- a/incredible_auto_dev/agents/demo-narrator/agent.yaml
+++ b/incredible_auto_dev/agents/demo-narrator/agent.yaml
@@ -6,12 +6,12 @@ description: Per-iteration product demonstrator. Authors a machine-executable de
   added or changed this iteration as `[NEW]`. Showcase, not QA — a failed step is a soft note,
   never a hard pipeline fail. Modes (selected by the dispatch wrapper) - record / live (this
   iteration's working surface) and session (the whole working product across iterations).
-model_tier: standard
+model_tier: light
 tools_allowed:
 - Read
 - Glob
 - Grep
 - Write
-version: 2.1.0
-last_updated: '2026-07-26'
+version: 2.2.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/agent.yaml b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
index 4a11daec..5d865aac 100644
--- a/incredible_auto_dev/agents/goal-decomposer/agent.yaml
+++ b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
@@ -1,7 +1,7 @@
 name: goal-decomposer
 description: 'Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals),
   the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md.
-  Picks lean or full depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only
+  Picks lean, full, or evidence depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only
   spec.'
 model_tier: standard
 tools_allowed:
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 2.3.0
-last_updated: '2026-07-17'
+version: 2.4.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/body.md b/incredible_auto_dev/agents/goal-decomposer/body.md
index 70778115..917fc656 100644
--- a/incredible_auto_dev/agents/goal-decomposer/body.md
+++ b/incredible_auto_dev/agents/goal-decomposer/body.md
@@ -17,15 +17,15 @@ The invocation prompt communicates which mode you are in via a `Mode:` line:
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
-1. `.claude/project-template.md` — project stack, architecture principles
-2. `.claude/core.md` and `.claude/workflow.md` — universal rules and pipeline semantics
+1. `.claude/project-template.md` — read ONLY the stack and architecture-principles sections: Grep for those section headers first, then Read just those sections. The rest of the file (test commands, run commands, never-commit list) is for executing agents, not for planning.
+2. Do NOT read `.claude/core.md` or `.claude/workflow.md`. Every pipeline semantic you need — depth rules, the spec format, verdict flow — is in THIS body. Consult `workflow.md` only when you need a specific section this body does not cover, and read only that section.
 3. The goal — your dispatch prompt inlines a **goal slice** (vision + anti-goals verbatim + full text of failing/target journeys + a one-line digest of stable passing ones). Use it as your primary goal source. Read the full `docs/goal.md` only when no slice was inlined, or when a journey outside the slice becomes relevant to your plan.
 4. Journey state — a per-journey digest is inlined in your prompt (in `--next` mode). Read `runs/goal-session-<sid>/state/journey-history.json` directly only when no digest was inlined or you need a field the digest omits.
 5. Iteration state — `runs/goal-session-<sid>/state/iteration-state.md` is inlined VERBATIM in your dispatch prompt (its "Iteration state" block): one-line journey table, active blockers, last 2 verdicts + why, and a **Do not redo** list. Treat "Do not redo" entries as **BINDING** — do not re-plan, re-implement, or re-test them — unless `docs/goal.md` changed for that item. An absent file (iteration 0) inlines as "(first iteration — no prior state)". Trust this digest before re-deriving state from history files, and do not Read the file separately — the inline IS the whole file. Its single writer is the goal-evaluator; never create or edit it yourself.
 6. `runs/goal-session-<sid>/state/blueprint.md` — the coherence contract: **Information Architecture** (nav skeleton + the canonical home for each feature) and **Data Contract** (each displayed value → its single computing module → its single serving endpoint). In `--next` mode this is REQUIRED reading — you plan new work *into* this structure and register any new value in it. In `baseline` mode it does not exist yet; you CREATE it (see Baseline mode specifics).
 7. `runs/goal-session-<sid>/iter-<N-1>/eval.md` — most recent evaluator verdict and recommendation (in `--next` mode)
 8. `runs/goal-session-<sid>/iter-<N-1>/coherence.md` — last coherence verdict (in `--next` mode). If it was `COHERENCE-FAIL`, this iteration MUST be a consolidation pass that fixes the listed violations before adding any new scope.
-9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work
+9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work. Scope this exploration to the target journeys' surfaces only; the blueprint and the iteration-state "Do not redo" list are authoritative for what already exists — never re-walk the app tree to rediscover it.
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md` or `runs/goal-session-<sid>/state/lessons.md`. The orchestrator script (`run-goal.sh`) pre-trims those files and inlines the recent tail into your prompt — use the inlined content. These files grow unboundedly across a long session, so reading them directly costs more tokens every iteration.
 
@@ -44,7 +44,8 @@ Write the iteration spec to `docs/phases/goal-<sid>-iter-<N>.md`. The file MUST
 - **Session ID:** <sid>
 - **Iteration:** <N>
 - **Mode:** baseline | next
-- **Depth:** lean | full
+- **Depth:** lean | full | evidence
+- **Full trigger:** <1|2|3|4> — <one-line reason>  (REQUIRED when Depth is full; omit at other depths)
 - **Target journeys:** J-01, J-03, J-07
 - **Required-still-passing journeys:** J-02, J-04
 - **Anti-goal reminders:**
@@ -127,6 +128,8 @@ separate functional test plan, so these lines are that plan's seed.
 
 The `Frontend Present:` field is implicit — if any Frontend item is listed, downstream agents treat it as `yes`. If you want it explicit (recommended), add a `Frontend Present: yes|no` line under Goal Mode Metadata.
 
+Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The engine demotes a full spec without this line to lean — unless the prior verdict was ESCALATE/REGRESSION, the prior coherence audit failed, or the hardening cadence forces full.
+
 ## Picking target journeys (priority rubric — apply top-down)
 
 1. **Regressed journeys first.** Anything `regressed` outranks all new work — a shrinking product is worse than a slowly-growing one.
@@ -135,6 +138,8 @@ The `Frontend Present:` field is implicit — if any Frontend item is listed, do
 4. **Smallest spec wins ties.** Among equals, pick the journey with the smallest concrete change set — small iterations are easier to score and revert.
 5. **Never bundle two risky journeys.** One iteration may carry several trivial journeys OR one risky journey (data-model change, provider integration, cross-cutting refactor) — never two risky ones; a joint failure is undiagnosable.
 6. **Don't pick a human-blocked journey.** If the evaluator marked a blocker human-owned (STALLED-class: credentials, network access, sanction), do not re-plan the same blocked work — plan a different journey, or if none exists, write the one-line "all remaining work is human-blocked" spec so the evaluator can halt honestly.
+<!-- rule 5 is SPEED-8's territory; rule 7 (SPEED-9) composes with it -->
+7. **Never plan an evidence-only iteration.** An iteration whose ONLY deliverable is evidence capture, screenshot retakes, or demo recording is not a plan — evidence gaps ride the make-up lane instead (the `evidence_makeup` / `pending_infra` booleans in journey-history), piggybacking on whatever real iteration runs next. The one exception: when the prior evaluator's next-step asks ONLY for evidence on already-passing journeys, write the iteration as `Depth: evidence` (capture + evaluate only — the engine skips developer/reviewer).
 
 Mini example — good vs bad target selection with the same state (J-03 regressed, J-07 failing-and-unblocks-J-08/J-09, J-11 failing, big):
 - ✚ Target `J-03` alone (rule 1), depth lean, Required-still-passing = the journeys sharing J-03's contract values + smoke set. Next iter: J-07.
@@ -159,12 +164,14 @@ Mini example — good vs bad target selection with the same state (J-03 regresse
      value's computing module or serving endpoint.
   3. **Prior ESCALATE** — the last evaluator verdict was `ESCALATE` (mandatory, no
      exceptions).
-  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 4)
+  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 6)
      consecutive dispatched iterations were all lean (the engine inlines
      "Consecutive lean iterations" in your prompt; the count resets on any full).
      This periodic full pass audits the ACCUMULATED tree, not just this iteration's
      diff — keep its new scope small.
 
+- **evidence** — all Target journeys are already recorded passing and the deliverable is visual evidence only (fresh screenshots / walkthrough recording); the engine dispatches capture + evaluation only, skipping developer and reviewer. Use it only in the rule-7 exception case above — never as a substitute for real work.
+
 "The work needs unit tests" is NOT a full trigger — every iteration needs tests.
 When no trigger holds, lean is not a risk you are taking; it is the design.
 
@@ -223,7 +230,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND; lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
@@ -241,6 +248,8 @@ If any check fails, fix the spec before writing it — downstream agents execute
 - **Log interpretation calls to the assumption ledger.** When a spec decision required interpreting the goal — the goal/journey text is ambiguous about X and you chose reading Y — append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use; never rewrite prior entries), formatted exactly as: `## iter-<N> — goal-decomposer` on its own line, then `**Ambiguity:** <what the goal leaves open>`, `**We chose:** <the reading this iteration builds on>`, `**Reversible:** yes|no`, each on its own line. Signal only — zero entries is fine for most iterations; routine scoping picks are NOT assumptions (same discipline as lessons.md). Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
 - **Conform to the blueprint, and keep it current.** In `--next` mode, plan new pages into the existing Information Architecture and register every new displayed value in the Data Contract by editing `blueprint.md` directly. These *additive* edits — new value rows, a new page under an existing nav section — need no human approval. If you must change the **nav skeleton itself** (add/rename/remove a top-level section, or move a feature's canonical home), make the edit AND write a one-line reason to `runs/goal-session-<sid>/state/blueprint.reapproval-requested`. By default `run-goal.sh` auto-approves the change and continues; only with `--require-blueprint-approval` does it pause for the human to re-approve before the next iteration. Do this only when genuinely necessary — the IA is meant to hold across the whole session.
 - **Never duplicate a contract value.** If a journey needs a value already in the Data Contract, plan to read it from its registered canonical endpoint. Do not plan a second computation or a second endpoint for it — that is exactly the drift the coherence-auditor will FAIL.
+- **Do not restate stable journeys' full `goal.md` text.** Reference journey IDs plus the acceptance delta — the goal slice in your prompt already digests them; copying their full text back into the spec is pure duplication.
+- **Do not paste blueprint content into the spec.** Reference the Information Architecture section / Data-Contract row by name. Both anti-restatement rules cut duplication ONLY — they NEVER mean shortening TC- test scenarios or interface/data-contract definitions (D6 forbids length budgets on those).
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index 7b816063..a20bbd18 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.8.0
-last_updated: '2026-07-26'
+version: 1.9.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index ae726d57..bb57fa50 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -10,20 +10,19 @@ Your methodology is `.claude/skills/goal-evaluation-methodology.md` — read it
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — especially **Must-have user journeys** and **Anti-goals**
-2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders)
-3. `runs/<iter-name>/plan.md` — execution plan (full mode only; absent in lean iterations)
-4. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
-5. `docs/handoffs/<iter-name>-dev.md` — dev handoff
-6. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only)
-7. `reports/reviews/<iter-name>-review.md` — review verdict
-8. `reports/qa/<iter-name>-qa.md` — QA verdict (full mode only)
-9. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
-10. `reports/qa/<iter-name>-evidence/` — screenshots
-11. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
-12. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
-13. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
-14. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
-15. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
+2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders). The spec is authoritative for targets — do NOT also read `runs/<iter-name>/plan.md` (the orchestrator's restatement for the developer; SPEED-9 dropped it from your inputs).
+3. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
+4. `docs/handoffs/<iter-name>-dev.md` — dev handoff
+5. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only). Read ONLY its Executive Verdict and Findings sections — its verdict already gated the pipeline; re-reading the full trace re-derives judgment that already fired.
+6. `reports/reviews/<iter-name>-review.md` — review verdict
+7. `reports/qa/<iter-name>-qa.md` — QA report (full mode only). Read ONLY the verdict line, the UI Evolution Audit block, and any FAIL rows — same already-gated rule as the audit handoff.
+8. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
+9. `reports/qa/<iter-name>-evidence/` — screenshots
+10. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
+11. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
+12. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
+13. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
+14. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md`. The orchestrator script (`run-goal.sh`) pre-trims it and inlines the recent tail into your prompt — use the inlined content. The file grows unboundedly across a long session.
 
@@ -101,6 +100,16 @@ the second consecutive infra failure: stop treating it as transient — the brow
 infrastructure is a human-owned blocker (STALLED-class, decision tree C.2); never loop a
 third silent retry.
 
+**`evidence_makeup` (SPEED-9, optional boolean).** Set `"evidence_makeup": true` on a
+journey whose product behavior is confirmed but whose capture artifact is cosmetically
+defective (methodology A.7: wrong-but-valid data range in the screenshot, missing or
+mis-cropped walkthrough recording). Keep the journey's evidence-based status — this flag
+never downgrades it; it asks the next iteration to re-capture as a passenger task or via
+`Depth: evidence`, never as an iteration goal. Clear the field (omit it) the moment a
+fresh capture lands — whatever the outcome. Do not conflate with `pending_infra` above:
+that flag means the browser infrastructure OWES evidence; this one means the evidence
+exists and only its presentation is wrong.
+
 **`spec_hash` — the goal-edit drift record.** Once per evaluation, run `python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md` (prints `{"J-NN": "<sha256>"}`). For every journey whose status you set from THIS iteration's evidence (`passing`, `failing`, `partial`, and baseline `already_passing`), record its current hash as `spec_hash`. For journeys you did not verify this iteration, carry the existing `spec_hash` forward unchanged — or leave it absent (pre-NEED-9 histories have none; never invent one). Never copy a new hash onto a journey you did not re-verify: the hash asserts "this status was verified against exactly this goal text", and the deterministic achievement gate audits it.
 
 **When `iter-<N>/journeys-changed.md` exists:** each listed journey's goal.md text changed AFTER its recorded pass, so that pass is void. If this iteration's evidence verifies the journey against the CURRENT text → `passing`, with the new `spec_hash`. Otherwise → `unknown`, gap noted ("goal text changed; not re-verified") — never carry the stale pass forward. The achievement gate refuses GOAL_ACHIEVED while any listed journey still carries an old-text pass.
@@ -114,7 +123,7 @@ Append a new entry to `runs/goal-session-<sid>/state/evaluator-log.md`:
 
 **Date:** <ISO timestamp>
 **Verdict:** <VERDICT>
-**Depth dispatched:** lean | full
+**Depth dispatched:** lean | full | evidence
 **Journey deltas:**
 - Newly passing: J-XX, J-YY
 - Newly failing: <none or list>
@@ -169,7 +178,7 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 # Iteration <N> Evaluation
 
 **Verdict:** <VERDICT>
-**Depth Recommendation For Next Iteration:** lean | full
+**Depth Recommendation For Next Iteration:** lean | full | evidence
 
 ## Summary
 
@@ -236,7 +245,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 
 - **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, this iteration's `coherence.md` is not `COHERENCE-FAIL`, AND no journey listed in `journeys-changed.md` remains un-re-verified against the current goal text. Loop halts with success.
 
-- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
+- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Recommend `evidence` depth when EVERY remaining gap is a capture/recording task on already-working features (`evidence_makeup`/`capture-defect` gaps) — the engine then runs capture + evaluation only, no developer/reviewer. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
 
 - **ESCALATE** — a lean iteration uncovered ambiguity, complexity, or an issue that warrants the full pipeline (audit, ux-regression, closure). The next iteration MUST run as `full`. Use sparingly — escalating every iter defeats the purpose of adaptive depth.
 
@@ -263,6 +272,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
 - If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
+- Never recommend — and never score as blocking — a next iteration whose only content is evidence capture, screenshot retakes, or demo recording. Evidence gaps on working features ride the make-up lane (`evidence_makeup`, methodology A.7) or a `Depth: evidence` recommendation; prior evidence for unchanged code stays valid (methodology A.6). Goal-edit drift (`journeys-changed.md`) always outranks evidence durability.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
index f75428e9..0a338bf4 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
+++ b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
@@ -8,6 +8,6 @@ model_tier: standard
 tools_allowed:
 - Read
 - Write
-version: 1.2.0
-last_updated: '2026-07-26'
+version: 1.3.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/iteration-summarizer/body.md b/incredible_auto_dev/agents/iteration-summarizer/body.md
index b242f264..2aaeb76b 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/body.md
+++ b/incredible_auto_dev/agents/iteration-summarizer/body.md
@@ -95,14 +95,14 @@ Write exactly this skeleton — keep the labels and the order:
 ```
 ## In plain words
 
-**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, aggregate every currently-passing journey. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
+**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, re-derive this EVERY iteration from the `name` fields of the currently-passing journeys in `journey-history.json` — never copy the previous summary's sentence verbatim, and any journey whose status changed this iteration must appear or disappear from the list accordingly. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
 
-**What changed this time:** <Plain-language description of what is newly available or fixed this iteration. Tie back to user experience ("You can now invite a teammate by email"). If nothing user-facing changed, write: "Behind-the-scenes work — nothing visibly new this round" and name the area in friendly terms (e.g. "made the app faster", "tightened security").>
+**What changed this time:** <MUST name the concrete user-visible change: the screen or page by its visible name and what the user now sees or does there ("The Watchlist page now has an 'Export CSV' button that downloads your list."). Never open with a generic sentence like "improvements were made". The sentence "Behind-the-scenes work — nothing visibly new this round" is permitted ONLY when the iteration changed zero product source files — check `status.json` `changed_files` and the dev handoff's Files Changed list before using it — and even then it must name the concrete area that was worked on ("sped up the price-history loading code", "captured fresh proof screenshots of the Desk screen").>
 
 **What's next:** <Plain-language version of the Next step. Phrase as the next thing the product will gain ("Next we'll let you reset a forgotten password"). One short sentence.>
 ```
 
-**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): write "Behind-the-scenes work — nothing visibly new this round." in **What changed this time**, keep the cumulative "What you can do now" unchanged from the prior iteration's plain-words block if you can read it (look at `reports/phase-<prev-phase-id>-iteration-summary.md` if obvious from context; otherwise describe the latest known capabilities or write "Same as before — no user-facing change.").
+**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): first check `status.json` `changed_files` and the dev handoff's Files Changed list. If product source files DID change, do NOT use the generic behind-the-scenes sentence — say in friendly words what part of the product the work touched and what it does now ("the price history behind the Desk screen now loads faster"). Only if zero product source files changed may **What changed this time** read "Behind-the-scenes work — nothing visibly new this round" — and it must still name the concrete area worked on ("captured fresh proof screenshots of the Desk screen"). For **What you can do now**, re-derive the list from the passing-journey names in `journey-history.json` EVERY iteration (phase mode: from the cumulative artifacts) — never copy the previous summary's sentence verbatim; a journey whose status changed this iteration must appear or disappear accordingly.
 
 **First iteration of a goal session** (no prior summaries, journey-history may be empty or have only `unknown` statuses): write "Just getting started — nothing for users to try yet." in **What you can do now**, and describe groundwork in **What changed this time**.
 
@@ -138,7 +138,12 @@ Numbers come from counting deltas in the evaluator-log entries. Do not invent jo
 
 ## What was done
 
-3–8 bullets, terse, action-oriented. Sources:
+The FIRST bullet is fixed-format. It MUST be one of these two — nothing else may be first:
+
+- `Product changes: <comma-separated changed product files and/or routes>` — sourced from `status.json` `changed_files` and the dev handoff's Files Changed list (e.g. `Product changes: apps/frontend/app/desk/page.tsx, /api/desk/topup`)
+- exactly `No product change this iteration.` — when neither source lists a changed product file
+
+Then 3–8 further bullets, terse, action-oriented. Sources:
 
 - `implementation-summary.md` "Features Implemented" if present (highest fidelity)
 - else `dev-handoff.md` "Summary" + a synthesized 1-bullet-per-major-file-or-area from "Files Changed"
diff --git a/incredible_auto_dev/agents/readme-maintainer/agent.yaml b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
index 57d070fd..b70b9c31 100644
--- a/incredible_auto_dev/agents/readme-maintainer/agent.yaml
+++ b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
@@ -3,13 +3,13 @@ description: Project README maintainer (goal mode). After each iteration, refres
   so it reflects the current capabilities of the whole project and carries an accurate "How to run" section.
   Edits only marker-delimited AUTO blocks so hand-written prose is preserved, and grounds every install/run/test
   command in .claude/project-template.md. Non-blocking showcase/maintenance step — never gates the pipeline.
-model_tier: standard
+model_tier: light
 tools_allowed:
 - Read
 - Write
 - Edit
 - Glob
 - Grep
-version: 1.1.0
-last_updated: '2026-07-26'
+version: 1.2.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/reviewer/agent.yaml b/incredible_auto_dev/agents/reviewer/agent.yaml
index f4c23abe..82128db3 100644
--- a/incredible_auto_dev/agents/reviewer/agent.yaml
+++ b/incredible_auto_dev/agents/reviewer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Bash
 - Write
 - Edit
-version: 1.2.1
-last_updated: '2026-07-16'
+version: 1.3.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/reviewer/body.md b/incredible_auto_dev/agents/reviewer/body.md
index 3fabff61..c78644f5 100644
--- a/incredible_auto_dev/agents/reviewer/body.md
+++ b/incredible_auto_dev/agents/reviewer/body.md
@@ -70,9 +70,12 @@ For each changed file, verify:
 - [ ] No refactoring of code outside the task scope
 
 ### UI quality (if frontend was changed)
-- [ ] UI evolved to reflect the new backend capability (per workflow.md UI EVOLUTION POLICY)
-- [ ] New entity types have list + detail pages reachable from navigation
-- [ ] Sidebar updated if a new top-level workflow was introduced
+<!-- SPEED-18: the UI-EVOLUTION/reachability questions (did the UI evolve, are new
+     entities reachable, was the sidebar updated) are owned by qa's live UI
+     Evolution Audit (browser + screenshot evidence, gating) and the
+     coherence-auditor's blueprint-grounded Step 2 — a code reviewer answers
+     them by guessing at runtime behavior. This checklist keeps only what CODE
+     review can actually verify. -->
 - [ ] Frontend does not contain business logic (calls backend APIs only)
 - [ ] Uses component library from DESIGN SYSTEM — no raw HTML where components exist
 - [ ] Colors, spacing, and typography use token values from DESIGN SYSTEM — no arbitrary values
@@ -129,8 +132,6 @@ standards:
   test_quality: pass
   no_dead_code: pass
   no_hardcoded_localhost: pass
-  ui_evolved_with_capability: pass
-  navigation_updated: n/a
   architecture_principles: pass
 ```
 ````
@@ -166,8 +167,6 @@ standards:
   test_quality: pass | fail | n/a
   no_dead_code: pass | fail | n/a
   no_hardcoded_localhost: pass | fail | n/a
-  ui_evolved_with_capability: pass | fail | n/a
-  navigation_updated: pass | fail | n/a
   architecture_principles: pass | fail | n/a
 fix_tasks:                            # ONLY when verdict == FAIL
   - file: path/to/file.py
@@ -186,7 +185,7 @@ Per-file, max 80 words each. Skip files with no issues. No headers below H3.
 - The verdict line is required and parsed by scripts. Keep the exact `**Verdict:** ...` format.
 - `issues` must be a YAML list. Use `[]` if empty.
 - Every CRITICAL or MINOR issue must have `file`, `line`, and `fix`.
-- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `ui_evolved_with_capability` on a backend-only phase).
+- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `test_quality` on a docs-only phase).
 - Do NOT write a "## Standards Compliance" markdown checkbox section. The YAML `standards` field replaces it.
 - Do NOT write "## Issues Found" as a markdown table. The YAML `issues` field replaces it.
 - If verdict is PASS, omit `## Detailed Findings` entirely. No filler.
diff --git a/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml b/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml
index c0bb2885..a598742c 100644
--- a/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml
+++ b/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml
@@ -3,6 +3,6 @@ description: UX regression reviewer. Checks whether the UI evolved appropriately
   capabilities. Flags features that exist in backend but are invisible or undiscoverable in the UI. Flags
   existing user journeys that may have regressed. Runs after browser QA and before the main auditor.
 model_tier: standard
-version: 1.0.0
-last_updated: '2026-05-04'
+version: 1.1.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/ux-regression-reviewer/body.md b/incredible_auto_dev/agents/ux-regression-reviewer/body.md
index 555f6e3a..63789f8f 100644
--- a/incredible_auto_dev/agents/ux-regression-reviewer/body.md
+++ b/incredible_auto_dev/agents/ux-regression-reviewer/body.md
@@ -12,27 +12,34 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. `reports/phase-{N}-user-visible-changes.md` — what changed for users
 4. `reports/phase-{N}-ui-surface-map.md` — affected surfaces
 5. `reports/phase-{N}-ui-test-results.md` — what was tested and found
-6. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
-7. `.claude/skills/ui-regression-scout.md` — methodology
+6. `reports/qa/<phase>-qa.md` — qa's UI Evolution Audit block (live-browser reachability evidence — cite it, don't re-derive it)
+7. In goal mode: `runs/goal-session-<sid>/iter-<N>/coherence.md` — the blueprint-grounded navigation/duplicate-home audit (read when present)
+8. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
+9. `.claude/skills/ui-regression-scout.md` — methodology
 
 ## Process
 
-### Step 1: Check UI evolution adequacy
+### Step 1: Check UI evolution adequacy (consume, don't re-derive)
 
-For each new capability listed in `user-visible-changes.md`:
-- Is there a navigation path to reach it? (Sidebar link, button, menu item)
-- Is it reachable within 2 clicks from the home page?
-- Is its label clear to a non-technical user?
-- Is there visual feedback when the capability is used?
+<!-- SPEED-18: reachability/click-depth/duplicate-home used to be asked FOUR
+     times per full iteration. The two best-evidenced askers own them now: qa's
+     live UI Evolution Audit (browser + screenshots, gating) and the
+     coherence-auditor's blueprint-grounded Step 2. Your Step 1 CONSUMES their
+     results and judges only what neither covers. -->
 
-Flag: "hidden capability" if it exists but has no navigation path.
-Flag: "undiscoverable capability" if it requires developer knowledge to find.
-Flag: "label confusion" if the UI label doesn't match what the feature does.
+Read qa's UI Evolution Audit result (and, in goal mode, `coherence.md`). Do NOT
+re-trace navigation paths or click-depth — cite their findings. Your own Step 1
+judgment covers what neither asker sees:
+- Is each new capability's label clear to a non-technical user?
+- Is there visual feedback when the capability is used?
 - Does the new UI follow the DESIGN SYSTEM tokens (colors, spacing, typography)?
-- Is the visual style consistent with pages from prior phases?
+- Is the rendered visual style consistent with pages from prior phases?
 - Are effects (glassmorphism, glows, gradients) applied consistently, not just on some pages?
 
+Flag: "label confusion" if the UI label doesn't match what the feature does.
 Flag: "visual inconsistency" if new pages deviate from the DESIGN SYSTEM or established style.
+Flag: "audit contradiction" if qa's UI audit or coherence.md flagged a reachability
+problem the other artifacts treat as resolved — quote both sides; do not re-test.
 
 ### Step 2: Check for regression in existing journeys
 
diff --git a/incredible_auto_dev/benchmarks/experiments.md b/incredible_auto_dev/benchmarks/experiments.md
index 9c379a1b..9dbb672a 100644
--- a/incredible_auto_dev/benchmarks/experiments.md
+++ b/incredible_auto_dev/benchmarks/experiments.md
@@ -937,3 +937,10 @@ Entry format contract (grep-able; pinned by
   framework-gap candidate as run E flagged: the forked/scripted browser-qa
   Chrome outlives the engine. Kept scratch:
   /home/dennis-chan/.cache/iad/shared/bench-bench-20260716-1436.dNHg0w
+
+## PRE speed-package-20260728 · 2026-07-28T15:30:00Z
+- framework-sha: e619138 (+ the SPEED-12/15/17/18/19/TOKEN-9 commits landing the same day; dirty during authoring)
+- fixture: next REAL tapeology goal session (or an EVO-3 benchmark rerun) vs the desk-session baseline recorded below
+- hypothesis: the SPEED-9..19 + REP-4 + TOKEN-9 package cuts typical goal-mode iteration wall time under 60 min without journey-quality regressions. Baseline (desk, 15 iters): ~153 agent-min/iter; verification = 54% of agent minutes; full depth 4 of last 6 iters; browser-qa >100 turns/invocation; 3 of last 5 iterations were evidence-only waste (~6h); zero quota-pause events recorded (attribution bug).
+- metrics + prediction (manual grading): median wall for lean/evidence/zero-change iterations < 60m; evidence-class gaps resolved in < 45m via the evidence micro-path (no developer dispatch); full-depth ratio <= 1 in 6; browser-qa <= 60 turns/invocation; demo-narrator+readme token cost ~1/3 of sonnet baseline; NO journey regressions or golden verdict-class flips attributable to the package; summaries name concrete files/screens (grep for 'Product changes:' rows).
+- note: pre-registered manually (G8) — the package is engine+contract work, not a run-benchmark.sh invocation; grade against the next session's telemetry with analyze_telemetry.py --wall.
diff --git a/incredible_auto_dev/commands/goal.md b/incredible_auto_dev/commands/goal.md
index c779238a..5d2834ec 100644
--- a/incredible_auto_dev/commands/goal.md
+++ b/incredible_auto_dev/commands/goal.md
@@ -1,7 +1,7 @@
 ---
 description: Run Goal Mode until the goal is achieved or an existing rule halts/pauses it, inside this Claude Code session (interactive dispatch — bills to your interactive plan allowance).
 argument-hint: "[session-id] [extra run-goal.sh flags]"
-allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Read, Task, Write
+allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(scripts/automation/host-guard-adopt.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
 ---
 You are the **pump** for goal mode. Run the EXISTING goal-mode engine until the
 goal is achieved, blocked, halted, or paused by its existing rules. Do NOT add
@@ -12,10 +12,19 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
 1. **Session id:** parse `$ARGUMENTS`. The first token is the session id; if there
    is no first token, generate one like `interactive-<YYYY-MM-DD>-<short>` and
    tell the user what you chose. Any remaining tokens are passthrough flags.
-2. **Launch the engine** in the background (Bash with run_in_background) and
+2. **Host-guard confinement** (only when `project-extensions/host-guard/host-guard.env`
+   exists with `HOST_GUARD_ENABLED=1`): run
+   `scripts/automation/host-guard-adopt.sh --cli-root-of $$` — it confines THIS
+   already-running CLI session (and everything it will spawn) to the declared
+   caps, in place; instant and idempotent when already confined. No special
+   launch command is required. Only if it prints `FAILED`, tell the user to
+   relaunch via `scripts/automation/host-guard-exec.sh claude` (the from-birth
+   wrapper) — the engine's iteration gate re-verifies each iteration and would
+   pause (AWAITING_HOST_GUARD, resumable) on an unconfinable pump.
+3. **Launch the engine** in the background (Bash with run_in_background) and
    capture its PID:
    `./scripts/automation/run-goal.sh --session-id <sid> --interactive <passthrough flags>`
-3. **Run the pump loop** from the skill: await requests with
+4. **Run the pump loop** from the skill: await requests with
    `scripts/automation/goal-await-dispatch.sh` (foreground, `--max-wait 500`),
    dispatch each returned request as a subagent (`subagent_type` = the request's
    `agent`, `prompt` passed verbatim; pass the request's `model` as the Agent
@@ -29,7 +38,7 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
    pauses, and in the final status block. The full chain narrative is in the
    timestamped `runs/goal-session-<sid>/engine.log` (tell the user to `tail -f`
    it); you do not read it.
-4. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
+5. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
    `status` and the next step.
 
 This runs the work as interactive subagents in THIS session (billed to your
diff --git a/incredible_auto_dev/docs/goal-mode-interactive.md b/incredible_auto_dev/docs/goal-mode-interactive.md
index 4d5d0c40..24565027 100644
--- a/incredible_auto_dev/docs/goal-mode-interactive.md
+++ b/incredible_auto_dev/docs/goal-mode-interactive.md
@@ -178,6 +178,8 @@ programmatic path with an API key** (`run-goal.sh` without `--interactive`).
 |---|---|---|
 | `CHAIN_PUMP_HEARTBEAT_TIMEOUT` | `1800` | PICKUP window only: seconds a *not-yet-claimed* request waits for the pump to take it before concluding the pump died. An alive idle pump refreshes the heartbeat every poll, so this no longer needs to cover a long agent's runtime — a claimed agent is governed by the inflight cap below. (Also how long an untouched orphan engine waits before self-aborting.) |
 | `CHAIN_DISPATCH_INFLIGHT_TIMEOUT` | `7200` (= `CHAIN_CLAUDE_MAX_RUNTIME_SECONDS`) | Hard cap on a single **claimed**, in-flight subagent, measured from when the pump took the request (`dispatch/req.*.started`). This is what lets a legitimately long agent — e.g. the developer's INITIAL BUILD, routinely > 30 min — run without being mistaken for a dead pump. `0` = unlimited. |
+| `CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT` | `= CHAIN_DISPATCH_INFLIGHT_TIMEOUT` (`7200`) | SPEED-12: bound on an **unclaimed** request's wait while the pump is alive but busy on another request. Before this, that wait was unbounded — one stale sibling claim from a dead pump could block the engine for 18 h. Provably-dead sibling claims are also cleared on the spot, and an iteration-boundary janitor sweeps stale claims. `0` = unlimited (old behavior). |
+| `CHAIN_DISPATCH_LANE` | `5` | SPEED-12 priority lane digit in the request filename (`req.<lane>-XXXXXX`). The pump serves the sorted glob, so lower lanes are picked up first; the background showcase tail dispatches on lane `9` so next-iteration spine work never queues behind it. |
 | `CHAIN_DISPATCH_POLL_SECONDS` | `1` | Channel poll interval. |
 
 The pump awaits work with a **single foreground** `goal-await-dispatch.sh
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index d4e3029a..3c9f0b2b 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -109,6 +109,7 @@ Halt verdicts:
 - `AWAITING_BLUEPRINT_APPROVAL` — only when you ran with `--require-blueprint-approval`: paused after baseline (or after a structural blueprint change) for you to review `state/blueprint.md`; `--resume` to continue (counts as approval)
 - `AWAITING_INTENT_REVIEW` — only when you ran with `--intent-checkpoint` / `--intent-checkpoint-at N`: paused once mid-session for you to read `runs/goal-session-<sid>/intent-review.md` ("is this still the product you wanted?"); `--resume` to continue (counts as acknowledgment; fires once per session)
 - `AWAITING_GITHUB_AUTH` — paused at startup because per-iter push is on but a push to `origin` wouldn't authenticate (expired GitHub session, or no remote); fix auth (the run will offer to launch `gh auth login` for you when interactive) and `--resume`
+- `AWAITING_HOST_GUARD` — only on hosts that declare hardware caps (`project-extensions/host-guard/host-guard.env`): the hwmon forensics sampler could not be started, the engine's CPU-affinity wrap did not take effect, a declared launcher lost its HOST-GUARD cap block, or the interactive pump session could not be confined (the engine auto-confines a running pump in place first via `host-guard-adopt.sh`; relaunching through `scripts/automation/host-guard-exec.sh <cli>` is only needed if that fails); fix the printed reason and `--resume` — see `docs/host-guard.md`
 
 ## Common workflows
 
diff --git a/incredible_auto_dev/docs/goal-mode-telemetry.md b/incredible_auto_dev/docs/goal-mode-telemetry.md
index a7c26a16..38baf70c 100644
--- a/incredible_auto_dev/docs/goal-mode-telemetry.md
+++ b/incredible_auto_dev/docs/goal-mode-telemetry.md
@@ -74,7 +74,9 @@ Wrap each agent call inside an iteration (developer, reviewer, browser-qa-agent,
 |---|---|---|
 | `agent` | string | Agent name |
 | `exit_status` | number | (end only) Process exit code |
-| `duration_seconds` | number | (end only) Wall time |
+| `duration_seconds` | number | (end only) Wall time, INCLUDING any quota-pause sleep |
+| `quota_sleep_seconds` | number | (end only) Seconds of that wall time spent in quota-pause sleeps (SPEED-13) |
+| `active_seconds` | number | (end only) `duration_seconds − quota_sleep_seconds` — the honest work time (SPEED-13) |
 | `retries` | number | (end only) Quota-retry count for this invocation |
 
 ### `quota_pause_start`, `quota_pause_end`
@@ -83,9 +85,13 @@ Recorded around quota-exhaustion sleeps inside `claude_with_quota_retry`.
 | Field | Type | Description |
 |---|---|---|
 | `agent` | string | Agent that triggered the pause |
+| `reset_epoch` | number | (start only) Epoch the sleep targets |
 | `sleep_seconds` | number | (end only) Total seconds slept |
 
-> Note: The quota-pause events are recorded by goal-mode wrapper logic in `run-goal.sh` and `goal-iter-lean.sh`, not by `lib/quota-retry.sh` directly (so phase mode is unaffected). The wrapper observes the script's exit/retry behavior and emits these events when the wrapper detects a quota-retry path was taken.
+> Note: These events are emitted directly by `lib/quota-retry.sh` at its sleep
+> sites (both claude and codex paths; SPEED-13). They no-op outside goal mode —
+> `record_telemetry_event` is disabled when no goal session is active. The same
+> path increments the session's `.quota-pause-count` file.
 
 ### `evaluator_start`, `evaluator_end`
 Wrap the goal-evaluator agent invocation.
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
new file mode 100644
index 00000000..cd4d634d
--- /dev/null
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -0,0 +1,89 @@
+# Host-guard — hardware protection for goal-mode load
+
+Some hosts (small-form-factor mini-PCs especially) hard-reset under the bursty
+all-core load an autonomous dev chain generates: an instant power/VRM/thermal
+transient trip, with nothing in the journal. Host-guard is the framework's
+opt-in defense: a project declares resource ceilings, and every heavy execution
+path respects them. **With no declaration, every hook is a byte-for-byte no-op**
+— the framework stays project-neutral.
+
+## Activation contract
+
+Create `project-extensions/host-guard/host-guard.env` in the project repo —
+plain `KEY=VALUE` bash assignments, `HOST_GUARD_*` names only. Machine-specific;
+do not copy between checkouts. `HOST_GUARD_ENABLED=0` (or deleting the file)
+disables everything.
+
+| Knob | Meaning | Typical |
+|---|---|---|
+| `HOST_GUARD_ENABLED` | Master switch | `1` |
+| `HOST_GUARD_CPU_LIST` | SMT-aware affinity mask for all heavy work | `"0-3,8-11"` |
+| `HOST_GUARD_BLAS_THREADS` | OMP/OpenBLAS/MKL/numexpr cap per process | physical cores in mask |
+| `HOST_GUARD_CPUQUOTA` | systemd scope average-CPU backstop | `"800%"` |
+| `HOST_GUARD_MEMORY_HIGH` | scope memory ceiling (reclaim/throttle, no OOM-kill) | `"14G"` |
+| `HOST_GUARD_TASKS_MAX` | fork-storm bound | `2048` |
+| `HOST_GUARD_REQUIRE_PUMP_CONFINED` | verify + auto-confine the interactive pump session each iteration | `1` |
+| `HOST_GUARD_ADOPT` | `0` disables the in-place auto-confine (pause immediately instead) | `1` (default) |
+| `HOST_GUARD_CLI_PATTERN` | regex matching the CLI process when walking up to the session root | `claude\|codex` (default) |
+| `HOST_GUARD_REQUIRE_MARKERS` + `HOST_GUARD_MARKER_FILES` | require HOST-GUARD cap blocks in listed launcher scripts | project-specific |
+| `HOST_GUARD_TCTL_PAUSE` / `_RESUME` / `_MAX_WAIT` | thermal gate thresholds (°C, °C, s) | `90` / `80` / `1800` |
+| `HOST_GUARD_SAMPLER_INTERVAL` / `_MAX_BYTES` | forensics sampler cadence / csv ring size | `1` / `10485760` |
+
+Running two projects' goal modes on one host: give them **complementary masks**
+(e.g. `0-3,8-11` and `4-7,12-15` on an 8-core/16-thread part) so a burst can
+never light every core, and size `MEMORY_HIGH` so the sum fits in RAM.
+
+## Enforcement layers (all in `scripts/automation/`)
+
+1. **Engine self-wrap** (`run-goal.sh`, top of script) — re-execs the whole
+   engine under `systemd-run --user --scope` with `AllowedCPUs` (cgroup cpuset,
+   inherited by every descendant, cannot be widened from inside) +
+   CPUQuota/MemoryHigh/TasksMax, plus `taskset -c` (also the no-user-bus
+   fallback). Covers **headless** runs completely.
+2. **In-place adoption** (`host-guard-adopt.sh`) — interactive dispatches run
+   inside the foreground CLI session, which the self-wrap cannot reach; this
+   script retrofits the confinement onto the ALREADY-RUNNING session tree, so
+   no special launch command is needed. Mechanics: systemd scope adoption
+   (busctl `StartTransientUnit` with the `PIDs` property + `set-property`) for
+   the CPUQuota/MemoryHigh/TasksMax ceilings, plus `taskset -a -c -p` on the
+   root and every existing descendant for the hard CPU mask (all threads,
+   inherited by all future children — works with no systemd at all).
+   `--cli-root-of <pid>` walks up to the outermost ancestor matching
+   `HOST_GUARD_CLI_PATTERN`. Invoked automatically by the `/goal` command at
+   session start and by the iteration gate on an unconfined pump.
+3. **Pump wrapper** (`host-guard-exec.sh`) — optional belt-and-braces: launch
+   the CLI confined from birth (`scripts/automation/host-guard-exec.sh claude`),
+   which additionally sets the BLAS/OMP thread-cap env vars (impossible to
+   inject into a running process). The fallback when adoption fails.
+4. **Preflight** (`preflight_host_guard`) — before the loop: forensics sampler
+   alive (auto-started if not), affinity wrap took effect, launcher marker
+   blocks intact. Failure pauses the session `AWAITING_HOST_GUARD` (resumable).
+5. **Iteration gate** (`host_guard_iteration_gate`, top of loop) — thermal
+   cooldown between iterations (wait out heat-soak, bounded), and — when
+   `HOST_GUARD_REQUIRE_PUMP_CONFINED=1` — pump-cpuset verification (via the
+   `pid=` line in `.pump-alive`, or the CLI root captured at engine launch)
+   with automatic in-place re-confinement; pauses only when that fails.
+6. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
+   pressure/memory to `<repo>/logs/hwmon/hwmon.csv`, fsync per line, so the
+   final pre-reset second survives a hard reset. `{run|start|stop|status|watch}`;
+   `status`/`start` recognize an externally-run sampler (e.g. a systemd user
+   unit running `run`) by csv freshness and never double-run.
+
+## When `AWAITING_HOST_GUARD` fires
+
+Read the printed reason, fix it, then
+`./scripts/automation/run-goal.sh --resume --session-id <sid>` (or
+`/goal-resume`). Pump-related pauses are rare by construction — the engine
+auto-confines a running pump in place before ever pausing — so a pause means
+adoption itself failed: relaunch the CLI via `host-guard-exec.sh` and resume.
+Do not disable flags to silence the pause; the caps exist because unconfined
+load has hard-reset a host.
+
+## Origin
+
+Built after a GEEKOM A7 Max (Ryzen 9 7940HS) hard-reset five times in eight
+days (2026-07-20 → 2026-07-28) under goal-mode load, three of the resets
+captured at 1 Hz with benign temperatures and low package power — a
+millisecond-scale power transient. Incident forensics and the cap-widening
+verification ladder live in the originating project:
+`trendora/project-extensions/host-guard/README.md`.
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index 0e583ad4..bf3cd80f 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -140,6 +140,21 @@ signal that says "do this now").
 10. **PLAIN-1** — plain-language output (§19, promoted 2026-07-26 by direct user
     request; absorbs DOC-5). Shipped 2026-07-26 in one bundled session; judgment
     spot-run green; certified DONE per G8 same day.
+11. **SPEED-9…19 + REP-4 + TOKEN-9** — the iteration-speed package (promoted
+    2026-07-28 by direct user request after the tapeology desk-session diagnosis;
+    EVO-1 promotion + G6 multi-item exception, all three judge cuts and the
+    ask-first flips explicitly approved). Implemented 2026-07-28 in one bundled
+    session; judgment spot-run GREEN 2026-07-29 — 14/14 verdict classes
+    (auditor 4/4 incl. case-03 contradiction-still-FAILs, goal-evaluator 6/6
+    incl. case-04 drift-beats-durability and case-06 make-up-boolean
+    distinction, reviewer 4/4 with the SPEED-18 key removals). Still owed
+    before any item flips to DONE: G8 fresh-session certification and one real
+    session's before/after telemetry (PRE speed-package-20260728 in
+    benchmarks/experiments.md). SPEED-15 slice (b) (trim-mode browser
+    narrowing) stays TODO until a warn-mode session exists.
+    *G8 fresh-session certification 2026-07-29 (non-implementer): steps 1-5
+    verified green; items remain IN-PROGRESS pending the real-session
+    telemetry (PRE speed-package-20260728).*
 
 ---
 
@@ -1083,6 +1098,234 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Depends on:** SPEED-4 (the sharpened rubric defines what "trivial" means in
   practice); synergizes with §16 CAND-TIER (same complexity vocabulary).
 
+<!-- ═══ SPEED-9…19 · the 2026-07-28 iteration-speed package (user-approved
+     promotion per EVO-1 + G6 multi-item exception, same mechanism as
+     SPEED-4..7 / CTX / PLAIN-1). Diagnosis basis: tapeology desk session
+     telemetry — 15 iterations, ~153 agent-min each; verification = 54% of all
+     agent minutes; of iters 10-14 only ONE shipped product code (the rest
+     chased screenshots/recordings); iter-7 blocked 18.3h on a dead pump's
+     claim; full depth ran 4 of the last 6 iterations. Target: typical
+     iterations < 60 min without giving up the judge chain's quality. ═══ -->
+
+### SPEED-9 · Evidence fast path — `evidence` depth + evaluator evidence durability
+- **Priority:** P0 · **Effort:** L (a: engine micro-path; b: evaluator contract;
+  c: decomposer rules) · **Risk:** MED · **Status:** IN-PROGRESS — implemented
+  2026-07-28 (commits 58b93be, 8bd513f, dc86b53); G8 fresh-session certification
+  + one real-session before/after pending.
+- **Problem:** 3 of the desk session's last 5 iterations (~6h) ran full/lean
+  pipelines solely to retake a screenshot or record a walkthrough for features
+  already verified working; lean specs whose deliverable was the walkthrough were
+  structurally unpassable (recording happened AFTER scoring — iter-12 ESCALATE).
+- **Change spec (landed):** (a) third depth token `evidence`
+  (`CHAIN_EVIDENCE_MICRO_PATH`, default on): goal-iter-lean.sh skips
+  developer/reviewer with honest stubs, runs browser-qa unchanged, and records
+  the demo BEFORE returning; engine backstop demotes lean→evidence when every
+  target journey is already recorded passing (telemetry
+  `depth_evidence_override`); evaluator prompt gains deterministic
+  `Prior walkthrough recording` + `Product diff this iteration` lines
+  (judgment-eval mirror updated byte-for-byte). (b) methodology A.6 (evidence
+  expires with CHANGE, not time; goal-edit drift always outranks durability;
+  the no-screenshot rail keeps demanding a citation) + A.7 (`capture-defect`
+  gap, `evidence_makeup` journey-history boolean mirroring `pending_infra`);
+  read-list diet (plan.md dropped; audit/QA reports scoped to verdict blocks).
+  (c) decomposer rubric rule 7: never plan an evidence-only iteration;
+  anti-restatement rules (D6-safe); read-list diet.
+- **DoD:** tests green (`test-evidence-depth.sh` 16 cases); judgment goldens
+  6/6 evaluator cases on the configured model; one real session shows an
+  evidence-class gap resolved in an `evidence` dispatch < 45 min.
+- **Verify:** `bash tests/automation/test-evidence-depth.sh` ·
+  `./scripts/automation/run-evals.sh` · judgment spot-run (G9).
+- **Files:** `scripts/automation/run-goal.sh`, `goal-iter-lean.sh`,
+  `lib/common.sh`, `run-judgment-evals.sh`, `agents/goal-evaluator/*`,
+  `agents/goal-decomposer/*`, `skills/goal-evaluation-methodology.md`, mirrors.
+- **Rollback:** `CHAIN_EVIDENCE_MICRO_PATH=false` (engine); body reverts + version.
+- **Stop-and-ask:** any evaluator golden verdict-class flip (drift-beats-durability
+  case-04 above all); a demo-less project needing more than the SKIPPED-stub path.
+
+### SPEED-10 · Depth discipline — full-trigger allowlist + cadence 4→6
+- **Priority:** P0 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (58b93be); G8 certification pending.
+- **Problem:** full depth (~90-120 min over lean) ran on 4 of the desk session's
+  last 6 iterations; at most 2 were justified (one full pass existed to re-record
+  a video).
+- **Change spec (landed):** engine allowlist (`CHAIN_DEPTH_ALLOWLIST`, default
+  on): a full spec stays full only on prior ESCALATE/REGRESSION, prior-iteration
+  COHERENCE-FAIL, a machine-parseable `Full trigger: <1|2|3|4> — reason` line
+  (decomposer contract, dc86b53), or cadence-due; otherwise demoted with
+  `depth_demoted` telemetry. `CHAIN_HARDENING_CADENCE` default 4→6 (evidence
+  dispatches continue the streak).
+- **DoD:** `test-depth-cadence.sh` 23 cases green; first real session shows
+  full-ratio ≤ 1-in-6 with no ESCALATE caused by a demoted full.
+- **Verify:** `bash tests/automation/test-depth-cadence.sh` · run-evals.
+- **Files:** `scripts/automation/run-goal.sh`, `lib/common.sh`,
+  `agents/goal-decomposer/body.md`, tests.
+- **Rollback:** `CHAIN_DEPTH_ALLOWLIST=false`; `CHAIN_HARDENING_CADENCE=4`.
+- **Stop-and-ask:** a demoted-full iteration producing an ESCALATE in the first
+  real session — report before tuning anything.
+
+### SPEED-11 · Lean replay-fork default flip (off→replay)
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (58b93be); G8 certification pending.
+- **Change spec (landed):** `CHAIN_LEAN_PARALLEL_BROWSER_QA` default off→replay
+  (SPEED-2's fork: built, benchmarked, tripwired — 2-of-3 attempt-1 review FAILs
+  auto-disable per session). Test scenarios pin `off` explicitly now. Recorded
+  decisions: CAND-FULL-BQA-OVERLAP stays staged (post-SPEED-10 fulls too rare to
+  justify the port); decomposer-N+1 ∥ evaluator-N overlap REJECTED (the
+  decomposer consumes evaluator outputs).
+- **Verify:** `bash tests/automation/test-goal-parallel-bqa.sh` (92 cases).
+- **Rollback:** `CHAIN_LEAN_PARALLEL_BROWSER_QA=off`.
+- **Stop-and-ask:** tripwire firing immediately in the first post-flip session.
+
+### SPEED-12 · Dispatch/timeout hardening — busy cap, claim janitor, lanes, timeout table
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28; G8 certification pending.
+- **Problem:** iter-7 blocked 18h19m on an UNCLAIMED request while a dead pump's
+  stale sibling `.started` kept the Tier-A wait unbounded
+  (`lib/interactive-dispatch.sh` busy branch); 8 agents fell to the flat 7200s
+  cap; showcase dispatches queued ahead of spine work.
+- **Change spec (landed):** `_dispatch_claim_pump_dead` helper — provably-dead
+  sibling claims cleared on the spot; `CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT`
+  (default = flat inflight cap, 0=old unlimited) bounds the genuine-busy
+  unclaimed wait resumably (`pickup-busy-timeout` event);
+  `dispatch_channel_janitor` at the iteration boundary; per-agent timeout table
+  filled for the full-pipeline chain (each ≥2.5× observed desk maxima);
+  priority lanes — `req.<lane>-XXXXXX` filenames (`CHAIN_DISPATCH_LANE`,
+  default 5; showcase tail exports 9) ride the pump's sorted glob with zero
+  pump-side changes.
+- **Verify:** `bash scripts/automation/lib/interactive-dispatch.sh --self-test`
+  (23 cases incl. 4 new) · `goal-await-dispatch.sh --self-test` ·
+  `python3 scripts/automation/lib/agent_permissions.py self-test`.
+- **Files:** `lib/interactive-dispatch.sh`, `lib/agent_permissions.py`,
+  `run-goal.sh`, `docs/goal-mode-interactive.md`.
+- **Rollback:** `CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT=0`; unset
+  `CHAIN_DISPATCH_LANE` semantics revert by deleting the two call-site exports;
+  table rows are per-agent deletes.
+- **Stop-and-ask:** a pickup-busy-timeout pause on a HEALTHY long dispatch in a
+  real session (cap mis-sized) — report before raising it.
+
+### SPEED-13 · Telemetry honesty — quota pauses, active vs wall, full-pipeline attribution
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (adf5f22); G8 certification pending.
+- **Problem:** quota_pause_start/end documented + consumed but never emitted;
+  `.quota-pause-count` had no increment site; quota sleeps inflated agent
+  durations (the "18.7h evaluator"); full-depth iterations emitted zero
+  per-agent events and rendered as 130-190m "unattributed (glue)".
+- **Change spec (landed):** both events + counter bump at all four sleep sites in
+  `lib/quota-retry.sh`; `agent_invocation_end` gains additive
+  `quota_sleep_seconds`/`active_seconds`; all 16 phase-script dispatch sites
+  wrap with `record_agent_invocation_start/end`; analyzer consumes `engine_step`
+  events, prefers active seconds, renders an honest residual.
+- **Verify:** `bash scripts/automation/lib/telemetry.sh test` ·
+  `python3 scripts/automation/lib/analyze_telemetry.py --self-test`.
+- **Rollback:** revert (additive fields; no behavior change).
+- **Stop-and-ask:** none (measurement only).
+
+### SPEED-14 · Zero-change iteration guards
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (58b93be); G8 certification pending.
+- **Change spec (landed):** `goal_product_diff_empty` helper (fail-safe,
+  bookkeeping-excluded); readme-maintainer's empty-change hole fixed (a
+  zero-change iteration used to DISPATCH; the empty set now skips); coherence
+  zero-change deterministic PASS with text DISTINCT from the crash stub —
+  `goal_gate.py` certifies it (self-test pins both classifications); demo
+  recording reused on an empty product diff. Knob `CHAIN_ZERO_CHANGE_SKIPS`,
+  default on.
+- **Verify:** `bash tests/automation/test-zero-change-guard.sh` (13 cases) ·
+  `python3 scripts/automation/lib/goal_gate.py self-test`.
+- **Rollback:** `CHAIN_ZERO_CHANGE_SKIPS=false` (readme hole fix stays — bug fix;
+  its escape is the pre-existing `CHAIN_README_EVERY_ITER=true`).
+- **Stop-and-ask:** none.
+
+### SPEED-15 · Wall-clock iteration budget (warn-first)
+- **Priority:** P2 · **Effort:** M (slice a landed; slice b TODO) · **Risk:** LOW
+  (warn) / MED (trim) · **Status:** IN-PROGRESS — slice (a) implemented
+  2026-07-28: knobs `CHAIN_ITER_TIME_BUDGET_SECONDS` (default 0=off; suggest
+  5400) + `CHAIN_ITER_BUDGET_MODE` (warn|trim, default warn), step-boundary
+  checks (never mid-agent), one loud warn + `iter_budget` telemetry, trim ladder
+  for showcase-class steps only (defer demo+readme; summarizer kept; spine and
+  gates NEVER trimmed — grep-pinned by the test).
+- **Slice (b) TODO:** trim-mode browser-set narrowing — drop only the no-golden
+  regression re-drives with mandatory `DEFERRED-BUDGET` result rows + the
+  one-line evaluator contract ("a DEFERRED-BUDGET row keeps prior status;
+  schedule next iteration", pending_infra pattern). Requires one full warn-mode
+  session of telemetry FIRST (G8) — do not build trim-b before that exists.
+- **Verify:** `bash tests/automation/test-iter-budget.sh` (17 cases).
+- **Rollback:** default off — unset the env.
+- **Stop-and-ask:** before enabling trim as any default.
+
+### SPEED-16 · Browser-qa turn diet
+- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (b33e21d); G8 certification pending.
+- **Change spec (landed):** 2-attempt selector recovery budget then
+  FAIL-with-evidence (a page that genuinely changed stays a recorded finding);
+  ONE screenshot per test at the acceptance state (+1 on failure; triad
+  deleted); all expected strings verified in ONE get_text; golden-first setup
+  (replay `journey-scripts/` prefixes verbatim; judgment starts at NEW steps).
+- **DoD:** post-session telemetry shows browser-qa ≤ 60 turns/invocation with
+  no journey-status regressions vs the desk baseline.
+- **Verify:** sync `--check` · run-evals · next-session telemetry (TOKEN-8 rows).
+- **Rollback:** revert bodies + versions.
+- **Stop-and-ask:** journeys flipping PASS→FAIL on recovery exhaustion — raise
+  the cap to 3, never delete it.
+
+### SPEED-17 · Deterministic phase-closure gate (LLM retired to an escape hatch)
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28; G8 certification pending.
+- **Problem:** the phase-closure-auditor LLM added no new judgment — Step 1
+  re-read three already-gating verdicts; Steps 2-4 were existence/count/
+  consistency checks. ~5 min + one LLM flake source per full iteration on a
+  HARD gate.
+- **Change spec (landed):** `scripts/automation/lib/closure_gate.py` writes the
+  FROZEN CLOSURE-PASS/CLOSURE-FAIL format deterministically (verdict presence,
+  6-UI-artifact existence + substance, ≥3 numbered what-to-click steps,
+  all-SKIPPED with-reason ⇒ WARN / without ⇒ FAIL, backend-only inconsistency,
+  objective vagueness BLOCKING / subtle vagueness WARN — policed upstream by
+  qa's live audit and downstream by the evaluator's evidence walk);
+  `phase-closure-check.sh` calls it; the agent dispatch survives behind
+  `CHAIN_CLOSURE_LLM=true`.
+- **Verify:** `python3 scripts/automation/lib/closure_gate.py self-test` ·
+  `bash tests/automation/test-closure-gate.sh` · run-evals.
+- **Rollback:** `CHAIN_CLOSURE_LLM=true` (single env).
+- **Stop-and-ask:** a real session where the deterministic gate passes an
+  artifact set the LLM would have failed for a SUBSTANTIVE reason — bring the
+  case, don't widen the script silently.
+
+### SPEED-18 · UI-evolution question dedupe (4 askers → 2)
+- **Priority:** P1 · **Effort:** S · **Risk:** MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28; G8 certification pending.
+- **Problem:** "did the UI evolve / is it reachable" was asked FOUR times per
+  full iteration (reviewer checklist, qa live audit, ux-regression Step 1,
+  coherence Step 2).
+- **Change spec (landed):** owners = qa's live UI Evolution Audit (browser +
+  screenshots, gating) and coherence-auditor Step 2 (blueprint-grounded,
+  objective FAIL, GOAL_ACHIEVED veto) — both UNCHANGED. Reviewer lost its three
+  runtime-guess checklist items + the `ui_evolved_with_capability`/
+  `navigation_updated` YAML keys (verified: no script parses them; auditor
+  golden fixtures carry them only as frozen inputs). Ux-regression Step 1 now
+  CONSUMES qa's audit + coherence.md and judges only what neither covers (label
+  clarity, visual feedback, rendered consistency) + flags audit contradictions.
+  D2 intact — all agents survive; only repeated questions were removed.
+- **Verify:** reviewer judgment goldens 4/4 · sync `--check` · run-evals.
+- **Rollback:** revert bodies + versions.
+- **Stop-and-ask:** a reviewer golden verdict-class flip; a real-session UI miss
+  only the deleted reviewer items would have caught ⇒ restore the first item only.
+
+### SPEED-19 · Auditor risk-ranked spot-verification
+- **Priority:** P1 · **Effort:** S-M · **Risk:** MED-HIGH · **Status:**
+  IN-PROGRESS — implemented 2026-07-28; G8 certification pending.
+- **Problem:** auditor Step 1 re-derived the full spec-compliance trace for
+  EVERY DoD item — the third full pass over ground the reviewer (code) and QA
+  (live rows) already covered (~202 min/session).
+- **Change spec (landed):** full code trace when ANY of: (a) state/data/auth/
+  money risk class; (b) artifact contradiction (the trigger even when QA is
+  green — golden case-03's shape); (c) reviewer `spec_alignment: partial` or a
+  spec-category issue; (d) the auditor's own Steps 2-4 leads. Mechanical items
+  with reviewer PASS + an executed QA row: accepted WITH double citation; no
+  citation ⇒ full trace. Steps 2-5, severity tree, fix authority untouched.
+- **Verify:** auditor judgment goldens 4/4 (case-03 MUST still FAIL) · run-evals.
+- **Rollback:** revert body + version (single hunk).
+- **Stop-and-ask:** any auditor golden verdict-class flip ⇒ revert immediately.
+
 ### TOKEN-1 · Per-agent project-template slicing
 - **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** DONE 2026-07-14 —
   release-manager/reviewer/qa converted; developer conversion deliberately LAST per this
@@ -1609,6 +1852,28 @@ benchmark (or a real session's telemetry) before AND after (G8).
   re-ran green same day (test-phase-telemetry.sh cases 1+2 inside run-evals
   116/116). Measurement chapter closed.
 
+### TOKEN-9 · Showcase tier demotion — demo-narrator + readme-maintainer → light
+- **Priority:** P2 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (part of the SPEED-9..19 package); TOKEN-2-class
+  experiment, G8 before/after via the next real session's TOKEN-8 rows.
+- **Problem:** demo-narrator (373k output tokens/15 iters) and readme-maintainer
+  are schema-constrained procedural writers with deterministic safety nets
+  (demo JSON is linted/executed by `demo_runner.py`; README edits are
+  marker-scoped) — sonnet-priced tokens for haiku-shaped work. ~0 wall-clock
+  (both ride the forked showcase tail), pure token cost.
+- **Change spec (landed):** `model_tier: standard → light` on both agent.yamls
+  (demo-narrator 2.2.0, readme-maintainer 1.2.0); tier prose table in
+  `.claude/model-orchestration.md` updated. **iteration-summarizer deliberately
+  STAYS standard** — REP-4 raised its concreteness bar and it is the human's
+  primary reading surface; demoting it while fixing its top complaint would be
+  self-defeating.
+- **DoD:** after one real session: `demo_runner.py --mode lint` pass-rate
+  unchanged; README AUTO blocks intact; TOKEN-8 rows show the cost drop.
+- **Verify:** sync `--check` · run-evals · next-session artifact checks above.
+- **Rollback:** one-line tier revert per agent (TOKEN-2's watch-item pattern).
+- **Stop-and-ask:** haiku demo JSON failing lint more than occasionally, or ONE
+  README AUTO-block corruption of hand-written prose ⇒ revert that agent.
+
 ---
 
 ## 10. P1 — Reliability & weaker-model hardening
@@ -2814,6 +3079,28 @@ territory).
   docs (env var table).
 - **Rollback:** unset env (no-op by default).
 
+### REP-4 · Iteration summaries must name the concrete change
+- **Priority:** P0 (the user's top reporting complaint) · **Effort:** S ·
+  **Risk:** LOW · **Status:** IN-PROGRESS — implemented 2026-07-28 (e619138,
+  part of the SPEED-9..19 package); G8 certification pending.
+- **Problem:** desk-session summaries never named one source file/screen; the
+  "In plain words" opener was recycled filler ("Behind-the-scenes work —
+  nothing visibly new this round"); "What you can do now" was copied verbatim
+  from the prior summary BY INSTRUCTION.
+- **Change spec (landed):** the opener must name the screen/page and what the
+  user now sees (the generic sentence is allowed ONLY on zero-product-file
+  iterations, and must still name the concrete area); the FIRST "What was done"
+  bullet is fixed-format — `Product changes: <files/routes>` or exactly
+  `No product change this iteration.`; "What you can do now" is re-derived from
+  journey-history every iteration; plain-language skill hard rule 7 ("concrete
+  beats generic"). H2 set unchanged (schema-enforced).
+- **Verify:** run-evals (summary schema self-tests) · eyeball the next real
+  session's summary: named screen in the opener, product-change first bullet.
+- **Files:** `agents/iteration-summarizer/*`, `templates/iteration-summary.md`,
+  `skills/plain-language.md`, mirrors.
+- **Rollback:** revert three files + version.
+- **Stop-and-ask:** none.
+
 ---
 
 ## 14. P1 — Documentation & guides
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 16f4b1a4..f83e43b9 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -313,13 +313,14 @@ fi
 
 # ── Run browser QA agent ───────────────────────────────────────────────────
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=browser-qa-agent
 # Guard against `set -e` so we can inspect the exit code and fall back to
 # writing a SKIPPED stub when the agent leaves no results file.
 _bqa_rc=0
 if [[ "$_bqa_infra_blocked" == "yes" ]]; then
-  : # REL-14: dispatch skipped — preflight failure recorded above
+  : # REL-14: dispatch skipped — preflight failure recorded above (no dispatch → no agent telemetry)
 else
+record_agent_invocation_start browser-qa-agent
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
 claude_with_quota_retry -p "You are the browser-qa-agent for phased development.
 
 Phase: $PHASE
@@ -358,6 +359,7 @@ The report MUST contain a line at the top:
 **Browser QA Verdict:** SKIPPED
 
 Then STOP." || _bqa_rc=$?
+record_agent_invocation_end browser-qa-agent "$_agent_t0" "$_bqa_rc"
 fi
 
 # Signal-induced exit (Ctrl-C, SIGKILL, SIGTERM) → do NOT write SKIPPED stubs.
diff --git a/incredible_auto_dev/scripts/automation/demo-phase.sh b/incredible_auto_dev/scripts/automation/demo-phase.sh
index cd7f5566..eac5f233 100755
--- a/incredible_auto_dev/scripts/automation/demo-phase.sh
+++ b/incredible_auto_dev/scripts/automation/demo-phase.sh
@@ -248,7 +248,8 @@ if [[ "$REAUTHOR" != "yes" ]] && _demo_json_fresh "$DEMO_JSON_OUT" "${AUTHOR_INP
   echo "[demo] Reusing cached demo script: $(basename "$DEMO_JSON_OUT") (pass --reauthor to rebuild)."
 else
   require_claude
-  export CHAIN_CURRENT_AGENT=demo-narrator
+  record_agent_invocation_start demo-narrator
+  _agent_t0="$CHAIN_AGENT_START_EPOCH"
   export CHAIN_CLAUDE_PRE_RETRY_HOOK="ensure_services_running"
   _author_rc=0
   if [[ "$MODE" == "session" ]]; then
@@ -287,6 +288,7 @@ Inputs (read only what exists):
 
 Write ONLY the JSON file at the output path. Do NOT open a browser. When done, STOP." || _author_rc=$?
   fi
+  record_agent_invocation_end demo-narrator "$_agent_t0" "$_author_rc"
 
   # Signal exit — propagate unchanged (resume logic re-runs). Do not stub.
   if [[ $_author_rc -eq 130 || $_author_rc -eq 137 || $_author_rc -eq 143 ]]; then
diff --git a/incredible_auto_dev/scripts/automation/dev-phase.sh b/incredible_auto_dev/scripts/automation/dev-phase.sh
index 9756b1a2..23b18811 100755
--- a/incredible_auto_dev/scripts/automation/dev-phase.sh
+++ b/incredible_auto_dev/scripts/automation/dev-phase.sh
@@ -85,7 +85,9 @@ trap cleanup_dev_servers EXIT
 
 # ── Developer agent ──────────────────────────────────────────────────────
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=developer
+record_agent_invocation_start developer
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
+_agent_rc=0
 claude_with_quota_retry -p "You are the developer agent for phased development.
 
 Phase: $PHASE
@@ -105,6 +107,8 @@ When complete:
   Use the template at templates/implementation-summary.md.
   Include: features implemented, changed behavior, backend-only items, incomplete items, config/env changes, known limitations.
   This report is for operators, not developers — write in plain language, not code.
-- Update runs/${PHASE}/status.json with current_step: dev_complete"
+- Update runs/${PHASE}/status.json with current_step: dev_complete" || _agent_rc=$?
+record_agent_invocation_end developer "$_agent_t0" "$_agent_rc"
+(( _agent_rc == 0 )) || exit "$_agent_rc"
 
 echo "[dev-phase] Done."
diff --git a/incredible_auto_dev/scripts/automation/finalize-phase.sh b/incredible_auto_dev/scripts/automation/finalize-phase.sh
index ecbcabe3..2389d07a 100755
--- a/incredible_auto_dev/scripts/automation/finalize-phase.sh
+++ b/incredible_auto_dev/scripts/automation/finalize-phase.sh
@@ -142,7 +142,9 @@ else
 fi
 
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=release-manager   # needed for the interactive dispatch backend to map this call to a subagent
+record_agent_invocation_start release-manager   # exports CHAIN_CURRENT_AGENT — needed for the interactive dispatch backend to map this call to a subagent
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
+_agent_rc=0
 claude_with_quota_retry -p "You are the release-manager agent for phased development.
 
 Phase to finalize: $PHASE
@@ -166,7 +168,9 @@ Perform the release flow:
 4. If GH_AUTH_AVAILABLE is true: create PR with title: feat: $PHASE -- <one-line summary>
 5. If GH_AUTH_AVAILABLE is false: skip PR creation, print a clear message showing the
    manual command the user can run once they authenticate: gh pr create ...
-6. Report the PR URL (or the manual command if PR was skipped)"
+6. Report the PR URL (or the manual command if PR was skipped)" || _agent_rc=$?
+record_agent_invocation_end release-manager "$_agent_t0" "$_agent_rc"
+(( _agent_rc == 0 )) || exit "$_agent_rc"
 
 # Clean up transient agent-generated files before finalizing
 echo "[finalize] Cleanup: removing temp files..."
diff --git a/incredible_auto_dev/scripts/automation/generate-test-plan.sh b/incredible_auto_dev/scripts/automation/generate-test-plan.sh
index 5226efcf..6605ab46 100755
--- a/incredible_auto_dev/scripts/automation/generate-test-plan.sh
+++ b/incredible_auto_dev/scripts/automation/generate-test-plan.sh
@@ -40,7 +40,9 @@ echo "[generate-test-plan] Generating test plan for: $PHASE (frontend: $FRONTEND
 mkdir -p "$REPO_ROOT/reports/qa"
 
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=qa
+record_agent_invocation_start qa
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
+_agent_rc=0
 claude_with_quota_retry -p "You are the qa agent operating in TEST PLAN GENERATION mode for phased development.
 
 Phase: $PHASE
@@ -60,7 +62,9 @@ The plan must include:
 - For each test case: type, preconditions, steps, expected outcome, pass criteria
 - A summary of total test cases by type
 
-Keep it concise (1-3 pages). Write the plan and STOP."
+Keep it concise (1-3 pages). Write the plan and STOP." || _agent_rc=$?
+record_agent_invocation_end qa "$_agent_t0" "$_agent_rc"
+(( _agent_rc == 0 )) || exit "$_agent_rc"
 
 if [[ ! -f "$TEST_PLAN" ]]; then
   echo "[generate-test-plan] Warning: agent did not write test plan file." >&2
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 4a5351a6..6b31c2c8 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -35,6 +35,9 @@ set -e
 
 SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 source "$SCRIPT_DIR/lib/common.sh"
+# SPEED-15: wall-clock budget clock — measure from the engine's iteration start
+# (exported CHAIN_ITER_START_EPOCH), not this child process's start.
+if declare -F iter_budget_init >/dev/null 2>&1; then iter_budget_init; fi
 source "$SCRIPT_DIR/lib/telemetry.sh"
 # Deterministic regression-replay lane — ONE implementation shared with the
 # FULL pipeline's browser-qa step (browser-qa-phase.sh). The tag keeps this
@@ -545,13 +548,17 @@ _bqa_tripwire_active() {
   return 0
 }
 
-# Knob: CHAIN_LEAN_PARALLEL_BROWSER_QA=off|replay|full, default off (G4).
+# Knob: CHAIN_LEAN_PARALLEL_BROWSER_QA=off|replay|full, default replay
+# (SPEED-11 flipped off→replay: the fork shipped default-off per G4 in SPEED-2,
+# was benchmarked, and carries its own tripwire — 2-of-3 attempt-1 review FAILs
+# disable it for the session. The replay lane is model-free python, safe on
+# both backends; rollback = CHAIN_LEAN_PARALLEL_BROWSER_QA=off).
 # "full" (SPEED-3: fork the whole section, LLM lane included) is HEADLESS-ONLY:
 # on the interactive backend, killing the engine-side waiter would strand the
 # pump's subagent against a request nobody reads (stale req/res files are only
 # cleaned at engine start) — that cancellation gap is EXP-4's, so interactive
 # demotes full → replay with a logged warning. Unrecognized values fall to off.
-_BQA_REQUESTED="${CHAIN_LEAN_PARALLEL_BROWSER_QA:-off}"
+_BQA_REQUESTED="${CHAIN_LEAN_PARALLEL_BROWSER_QA:-replay}"
 _BQA_MODE="off"
 _BQA_OFF_REASON=""
 case "$_BQA_REQUESTED" in
@@ -579,6 +586,11 @@ if [[ "$_BQA_MODE" == "replay" || "$_BQA_MODE" == "full" ]]; then
     _BQA_MODE="off"; _BQA_OFF_REASON="no-jq"
   fi
 fi
+# SPEED-9 evidence micro-path: no review loop runs, so there is nothing for a
+# browser-qa fork to overlap — the section runs inline.
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" && "$_BQA_MODE" != "off" ]]; then
+  _BQA_MODE="off"; _BQA_OFF_REASON="evidence-mode"
+fi
 # Name the knob state every iteration (mirrors run-goal.sh's iter_config event).
 record_telemetry_event "iter_config" "$(jq -cn --arg k "CHAIN_LEAN_PARALLEL_BROWSER_QA" --arg v "$_BQA_MODE" --arg req "$_BQA_REQUESTED" --arg r "$_BQA_OFF_REASON" '{key:$k, value:$v, requested:$req, reason:$r}' 2>/dev/null || printf '{"key":"CHAIN_LEAN_PARALLEL_BROWSER_QA","value":"%s"}' "$_BQA_MODE")"
 
@@ -854,7 +866,16 @@ The report MUST start with a line matching exactly:
 # aborts the iteration as before (set -e semantics, now with the code preserved).
 # Resume-skip: handoff on disk + the tree exactly where this iteration last
 # left it → the ~41-min build is already done, don't redo it.
-if step_done_valid developer --verify-tree --dir "$ITER_DIR" "$DEV_HANDOFF"; then
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]]; then
+  # SPEED-9 evidence micro-path: the spec's only deliverable is visual evidence
+  # for already-working journeys — no build work. Stub the dev handoff so the
+  # evaluator's input set stays complete; re-runs are idempotent (no checkpoint).
+  echo "[goal-iter-lean] EVIDENCE mode: skipping developer (no code changes planned)."
+  if [[ ! -s "$DEV_HANDOFF" ]]; then
+    printf '# Dev Handoff — %s\n\nEvidence-only iteration: no code changes were planned or made.\nThe pipeline captured fresh visual evidence for the Target journeys instead;\nsee the browser test results and this iteration'"'"'s demo recording.\n' "$ITER_NAME" > "$DEV_HANDOFF"
+  fi
+  _step_skipped_event "developer"
+elif step_done_valid developer --verify-tree --dir "$ITER_DIR" "$DEV_HANDOFF"; then
   _step_skipped_event "developer"
 else
   step_invalidate_from developer "$ITER_DIR"
@@ -867,8 +888,9 @@ fi
 
 # TOKEN-7 build 1: the round-1 review packet. Ordering is load-bearing — this
 # sits BEFORE both fork spawn points below (same stale-write discipline as the
-# forks' own kill-then-invalidate rule).
-_build_review_packet_or_degrade
+# forks' own kill-then-invalidate rule). Evidence mode has no reviewer, so no
+# packet is built (SPEED-9).
+[[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]] || _build_review_packet_or_degrade
 
 # ── SPEED-2 fork: service boot + deterministic replay ∥ review ────────────
 # Forked HERE — right after the developer step settles — because review and
@@ -950,7 +972,16 @@ fi
 # Resume-skip: the marker alone is never trusted — the report must live-parse
 # to a verdict (a FAIL report still routes into the fix branch below, exactly
 # as a freshly written FAIL would).
-if { step_done_valid review-1 --dir "$ITER_DIR" "$REVIEW_REPORT" \
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]]; then
+  # SPEED-9 evidence micro-path: nothing was built, so there is nothing to
+  # review. The stub's PASS verdict line keeps every parser downstream honest
+  # about the shape while the body states no review occurred.
+  echo "[goal-iter-lean] EVIDENCE mode: skipping reviewer (no code changes to review)."
+  if [[ ! -s "$REVIEW_REPORT" ]]; then
+    printf '**Verdict:** PASS\n\nEvidence-only iteration: no code changes were made, so developer and reviewer were not dispatched. Nothing to review.\n' > "$REVIEW_REPORT"
+  fi
+  _step_skipped_event "reviewer"
+elif { step_done_valid review-1 --dir "$ITER_DIR" "$REVIEW_REPORT" \
      || step_done_valid review-2 --dir "$ITER_DIR" "$REVIEW_REPORT"; } && _review_parses; then
   _step_skipped_event "reviewer"
 else
@@ -1036,6 +1067,13 @@ if [[ "${CHAIN_LEAN_PARALLEL_COHERENCE:-true}" == "true" && -n "$ITER_DIR" \
   if step_done_valid coherence --verify-tree --dir "$ITER_DIR" "$COHERENCE_OUTPUT_LEAN" \
      && grep -qE '^\*\*Verdict:\*\* COHERENCE-(PASS|WARN|FAIL)' "$COHERENCE_OUTPUT_LEAN"; then
     _step_skipped_event "coherence-auditor"
+  elif [[ "${CHAIN_ZERO_CHANGE_SKIPS:-true}" == "true" ]] \
+       && { declare -F goal_product_diff_empty >/dev/null 2>&1 || source "$SCRIPT_DIR/lib/goal-gates.sh" 2>/dev/null; } \
+       && goal_product_diff_empty "$(cat "$ITER_DIR/snapshot-sha" 2>/dev/null || echo "")" "$REPO_ROOT"; then
+    # SPEED-14: empty product diff after the dev/review loop — nothing to
+    # audit, so don't burn a fork. run-goal.sh's sequential coherence step
+    # records the deterministic zero-change PASS for this case.
+    echo "[goal-iter-lean] coherence fork skipped — zero-change iteration (empty product diff); the engine records a deterministic PASS."
   else
     step_invalidate_from coherence "$ITER_DIR"
     rm -f "$_COH_RC_FILE"
@@ -1061,6 +1099,7 @@ if [[ "${CHAIN_LEAN_PARALLEL_COHERENCE:-true}" == "true" && -n "$ITER_DIR" \
   fi
 fi
 
+if declare -F iter_budget_check >/dev/null 2>&1; then iter_budget_check "browser-qa"; fi
 # ── Step 3: Browser QA ────────────────────────────────────────────────────
 # Determine if frontend work is implied. Lean iterations always test journeys,
 # so we always try to start the frontend; if it fails we mark all SKIPPED and
@@ -1131,6 +1170,17 @@ fi
 # never read demo artifacts, so its input set is unchanged. demo-phase.sh
 # boots its own services idempotently, so it no longer depends on this
 # script's still-warm ports.
+#
+# SPEED-9 exception — EVIDENCE mode records the walkthrough HERE, before the
+# evaluator reads. In plain lean the post-eval showcase ordering made a spec
+# whose deliverable was "record the walkthrough" structurally unpassable (the
+# desk-session iter-12 ESCALATE); the evidence micro-path exists for exactly
+# that deliverable, so the recording must precede evaluation.
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]]; then
+  echo "[goal-iter-lean] EVIDENCE mode: recording the walkthrough BEFORE evaluation..."
+  bash "$SCRIPT_DIR/demo-phase.sh" "$ITER_NAME" \
+    || echo "[goal-iter-lean] demo-phase.sh exited non-zero — continuing (the evaluator scores from whatever evidence exists)."
+fi
 
 echo "[goal-iter-lean] Done. Iteration artifacts:"
 echo "  Dev handoff:   $DEV_HANDOFF"
diff --git a/incredible_auto_dev/scripts/automation/host-guard-adopt.sh b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
new file mode 100755
index 00000000..ce754e24
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
@@ -0,0 +1,121 @@
+#!/usr/bin/env bash
+# host-guard-adopt.sh — confine an ALREADY-RUNNING process tree to the
+# project's host-guard caps, in place, no relaunch required.
+#
+# WHY: interactive-pump dispatches run inside the foreground CLI session
+# (Claude Code / Codex). host-guard-exec.sh confines that session from birth,
+# but requiring a special launch command is a footgun — this script retrofits
+# the confinement onto the live session instead:
+#
+#   1. systemd scope adoption (busctl StartTransientUnit with the PIDs
+#      property + set-property): moves the process under a transient user
+#      scope carrying CPUQuota/MemoryHigh/TasksMax (and AllowedCPUs where the
+#      cpuset controller is delegated to user units — many distros delegate
+#      only cpu/memory/pids, in which case AllowedCPUs is a silent no-op).
+#   2. taskset -a -c -p on the target AND every existing descendant: the hard
+#      CPU mask — all threads, inherited by all future children. This is the
+#      layer that actually prevents power-transient resets, and it works with
+#      no systemd at all.
+#
+# Usage:
+#   host-guard-adopt.sh <pid>                confine this pid('s tree)
+#   host-guard-adopt.sh --cli-root-of <pid>  walk UP from <pid> to the
+#       outermost ancestor whose cmdline matches HOST_GUARD_CLI_PATTERN
+#       (default 'claude|codex') and confine THAT tree; falls back to <pid>
+#       itself when no ancestor matches.
+#
+# Idempotent: exits 0 immediately when the target is already confined.
+# Absent/disabled host-guard.env ⇒ no-op (framework stays project-neutral).
+# Limitation: BLAS/OMP thread-cap env vars cannot be injected into a running
+# process — only wrapper-launched (host-guard-exec.sh) sessions get those.
+set -euo pipefail
+
+MODE_ROOT=0
+if [[ "${1:-}" == "--cli-root-of" ]]; then MODE_ROOT=1; shift; fi
+PID="${1:?usage: host-guard-adopt.sh [--cli-root-of] <pid>}"
+[[ "$PID" =~ ^[0-9]+$ && -r "/proc/$PID/status" ]] \
+  || { echo "[host-guard-adopt] pid '$PID' is not a running process" >&2; exit 1; }
+
+ROOT="${HOST_GUARD_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
+ENV_FILE="$ROOT/project-extensions/host-guard/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
+if [[ "${HOST_GUARD_ENABLED:-0}" != "1" || -z "${HOST_GUARD_CPU_LIST:-}" ]]; then
+  echo "[host-guard-adopt] no enabled host-guard.env under $ROOT — nothing to do."
+  exit 0
+fi
+command -v taskset >/dev/null 2>&1 \
+  || { echo "[host-guard-adopt] taskset not available" >&2; exit 1; }
+
+_width() { # "0-3,8-11" → 8; 0 when unparseable
+  local list="${1:-}" n=0 part a b
+  [[ -n "$list" ]] || { echo 0; return 0; }
+  local -a parts=()
+  IFS=',' read -ra parts <<< "$list"
+  for part in "${parts[@]}"; do
+    if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+      a="${part%-*}"; b="${part#*-}"
+      if (( b >= a )); then n=$(( n + b - a + 1 )); fi
+    elif [[ "$part" =~ ^[0-9]+$ ]]; then
+      n=$(( n + 1 ))
+    fi
+  done
+  echo "$n"
+}
+_ppid() { awk '/^PPid:/{print $2}' "/proc/$1/status" 2>/dev/null || true; }
+_allowed_n() { _width "$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$1/status" 2>/dev/null)"; }
+
+TARGET="$PID"
+if [[ "$MODE_ROOT" == "1" ]]; then
+  _pat="${HOST_GUARD_CLI_PATTERN:-claude|codex}" _p="$PID" _best=""
+  while [[ "$_p" =~ ^[0-9]+$ ]] && (( _p > 1 )); do
+    if tr '\0' ' ' < "/proc/$_p/cmdline" 2>/dev/null | grep -qE "$_pat"; then _best="$_p"; fi
+    _p="$(_ppid "$_p")"
+  done
+  if [[ -n "$_best" ]]; then
+    TARGET="$_best"
+  else
+    echo "[host-guard-adopt] no ancestor of $PID matches '$_pat' — confining $PID itself."
+  fi
+fi
+
+WIDTH="$(_width "$HOST_GUARD_CPU_LIST")"
+if (( WIDTH == 0 )); then
+  echo "[host-guard-adopt] unparseable HOST_GUARD_CPU_LIST='$HOST_GUARD_CPU_LIST'" >&2
+  exit 1
+fi
+if (( $(_allowed_n "$TARGET") <= WIDTH )); then
+  echo "[host-guard-adopt] pid $TARGET already confined ($(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$TARGET/status"))."
+  exit 0
+fi
+
+# 1) Scope adoption — aggregate memory/task/quota ceilings for the whole tree.
+UNIT="chain-pump-hostguard-$TARGET.scope"
+if busctl call --user org.freedesktop.systemd1 /org/freedesktop/systemd1 \
+     org.freedesktop.systemd1.Manager StartTransientUnit 'ssa(sv)a(sa(sv))' \
+     "$UNIT" fail 1 PIDs au 1 "$TARGET" 0 >/dev/null 2>&1; then
+  systemctl --user set-property "$UNIT" \
+    "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}" \
+    "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}" \
+    "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" 2>/dev/null || true
+  # Engages only where the cpuset controller is delegated to user units.
+  systemctl --user set-property "$UNIT" "AllowedCPUs=$HOST_GUARD_CPU_LIST" 2>/dev/null || true
+  echo "[host-guard-adopt] scope $UNIT adopted pid $TARGET (CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}, MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}, TasksMax=${HOST_GUARD_TASKS_MAX:-2048})."
+else
+  echo "[host-guard-adopt] scope adoption unavailable — applying the CPU mask only."
+fi
+
+# 2) Hard CPU mask NOW — target + every existing descendant; future children
+# inherit. -a covers all threads of each process.
+_descendants() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do echo "$c"; _descendants "$c"; done; }
+taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$TARGET" >/dev/null 2>&1 || true
+for _c in $(_descendants "$TARGET"); do
+  taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$_c" >/dev/null 2>&1 || true
+done
+
+if (( $(_allowed_n "$TARGET") <= WIDTH )); then
+  echo "[host-guard-adopt] confined pid $TARGET (and descendants) to CPUs $HOST_GUARD_CPU_LIST."
+  exit 0
+fi
+echo "[host-guard-adopt] FAILED to confine pid $TARGET (Cpus_allowed_list unchanged)." >&2
+exit 1
diff --git a/incredible_auto_dev/scripts/automation/host-guard-exec.sh b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
new file mode 100755
index 00000000..bb9ac601
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
@@ -0,0 +1,69 @@
+#!/usr/bin/env bash
+# host-guard-exec.sh — run ANY command under the project's host-guard caps.
+#
+# WHY: the engine's self-wrap (run-goal.sh) confines headless runs, but
+# interactive-pump dispatches execute INSIDE the foreground CLI session
+# (Claude Code / Codex) — children of a process the engine never wrapped.
+# Launch that CLI through this wrapper and every subagent, pytest, bundler,
+# and browser it spawns inherits the same cgroup/affinity confinement:
+#
+#   scripts/automation/host-guard-exec.sh claude
+#   scripts/automation/host-guard-exec.sh -- codex --some-flag
+#
+# The engine can enforce this: with HOST_GUARD_REQUIRE_PUMP_CONFINED=1 in
+# host-guard.env, run-goal.sh's iteration gate verifies the pump process's
+# cpuset and pauses (AWAITING_HOST_GUARD, resumable) if it is unconfined.
+#
+# Repo root: $HOST_GUARD_ROOT override, else git toplevel of $PWD, else $PWD.
+# Absent or disabled host-guard.env ⇒ exec the command unwrapped (with a
+# warning): the framework stays project-neutral.
+set -euo pipefail
+
+[[ "${1:-}" == "--" ]] && shift
+if [[ $# -eq 0 ]]; then
+  echo "Usage: $0 [--] <command> [args...]" >&2
+  exit 2
+fi
+
+ROOT="${HOST_GUARD_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
+ENV_FILE="$ROOT/project-extensions/host-guard/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
+
+if [[ "${HOST_GUARD_ENABLED:-0}" != "1" || -z "${HOST_GUARD_CPU_LIST:-}" ]] \
+   || ! command -v taskset >/dev/null 2>&1; then
+  echo "[host-guard-exec] no enabled host-guard.env under $ROOT (or no taskset) — running UNCONFINED." >&2
+  exec "$@"
+fi
+
+# BLAS/OpenMP/numexpr worker caps for every descendant (mirrors the launcher
+# HOST-GUARD blocks): N numpy processes must not oversubscribe the mask with
+# nested thread pools.
+if [[ "${HOST_GUARD_BLAS_THREADS:-}" =~ ^[0-9]+$ ]]; then
+  export OMP_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+  export OPENBLAS_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+  export MKL_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+  export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+fi
+
+_PROPS=( -p "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}"
+         -p "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}"
+         -p "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" )
+
+# --expand-environment=no: systemd ExecStart otherwise $-expands argv ("$$"→"$").
+if systemd-run --user --scope --quiet --expand-environment=no -p "AllowedCPUs=$HOST_GUARD_CPU_LIST" true 2>/dev/null; then
+  echo "[host-guard-exec] confining '$1' to CPUs $HOST_GUARD_CPU_LIST (cpuset + CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}, MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G})." >&2
+  exec systemd-run --user --scope --quiet --collect --expand-environment=no \
+    --unit "chain-pump-hostguard-$$" \
+    -p "AllowedCPUs=$HOST_GUARD_CPU_LIST" "${_PROPS[@]}" \
+    taskset -c "$HOST_GUARD_CPU_LIST" "$@"
+elif systemd-run --user --scope --quiet --expand-environment=no -p CPUQuota=10% true 2>/dev/null; then
+  echo "[host-guard-exec] confining '$1' to CPUs $HOST_GUARD_CPU_LIST (taskset + scope backstops; cpuset not delegated)." >&2
+  exec systemd-run --user --scope --quiet --collect --expand-environment=no \
+    --unit "chain-pump-hostguard-$$" \
+    "${_PROPS[@]}" \
+    taskset -c "$HOST_GUARD_CPU_LIST" "$@"
+else
+  echo "[host-guard-exec] confining '$1' to CPUs $HOST_GUARD_CPU_LIST (taskset only; no user manager)." >&2
+  exec taskset -c "$HOST_GUARD_CPU_LIST" "$@"
+fi
diff --git a/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
new file mode 100755
index 00000000..e5632fd5
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
@@ -0,0 +1,233 @@
+#!/usr/bin/env bash
+# hwmon-log.sh — 1 Hz hardware telemetry sampler (host-guard crash forensics).
+#
+# WHY: hosts can hard-reset under bursty all-core load with NOTHING in the
+# journal — an instant power/VRM/thermal trip. sysstat's 10-minute cadence
+# straddles the spike. This sampler records temps/power/pressure every second
+# and fsyncs each line, so the final pre-reset second survives the reboot.
+#
+# Usage: hwmon-log.sh {run|start|stop|status|watch}
+#   run    — sample in the foreground (Ctrl+C stops)
+#   start  — background daemon (nohup); pidfile logs/hwmon/hwmon.pid
+#   stop   — stop the daemon
+#   status — exit 0 iff the daemon is alive AND the csv is fresh; prints one line
+#   watch  — live view: latest sample + session max Tctl/PPT (⚠ at Tctl ≥ 90°C)
+#
+# Output: <repo>/logs/hwmon/hwmon.csv (gitignored), ring-rotated at
+# HOST_GUARD_SAMPLER_MAX_BYTES to hwmon.csv.1. Sensors are resolved BY NAME
+# (k10temp/amdgpu/nvme/spd5118/acpitz) — hwmon indexes shift across boots.
+# A missing sensor yields an empty CSV field, never a crash.
+set -euo pipefail
+
+HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+# Repo root resolution (which repo's logs/ receives the csv):
+#   1. HOST_GUARD_ROOT env override — the engine preflight passes its $REPO_ROOT;
+#   2. framework placement  <root>/scripts/automation/host-guard/ → 3 dirs up;
+#   3. project placement    <root>/project-extensions/host-guard/ → 2 dirs up.
+if [[ -n "${HOST_GUARD_ROOT:-}" ]]; then
+  REPO_ROOT="$(cd "$HOST_GUARD_ROOT" && pwd)"
+elif [[ "$HERE" == */scripts/automation/host-guard ]]; then
+  REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
+else
+  REPO_ROOT="$(cd "$HERE/../.." && pwd)"
+fi
+# Caps env: the project's declaration wins; a copy next to this script is the
+# fallback (project-extensions placement keeps them side by side).
+ENV_FILE="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+[[ -f "$ENV_FILE" ]] || ENV_FILE="$HERE/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
+
+INTERVAL="${HOST_GUARD_SAMPLER_INTERVAL:-1}"
+MAX_BYTES="${HOST_GUARD_SAMPLER_MAX_BYTES:-10485760}"
+LOG_DIR="$REPO_ROOT/logs/hwmon"
+CSV="$LOG_DIR/hwmon.csv"
+PIDFILE="$LOG_DIR/hwmon.pid"
+DAEMON_LOG="$LOG_DIR/hwmon.log"
+HEADER="epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10"
+
+# ── Sensor resolution (by hwmon name, once at startup) ─────────────────────
+TCTL="" GPU_TEMP="" PPT_NOW="" PPT_AVG="" NVME_T="" DIMM0="" DIMM1="" ACPITZ=""
+resolve_sensors() {
+  local h name
+  for h in /sys/class/hwmon/hwmon*; do
+    [[ -r "$h/name" ]] || continue
+    IFS= read -r name < "$h/name" 2>/dev/null || continue
+    case "$name" in
+      k10temp)
+        if [[ -r "$h/temp1_input" ]]; then TCTL="$h/temp1_input"; fi ;;
+      amdgpu)
+        if [[ -r "$h/temp1_input" ]]; then GPU_TEMP="$h/temp1_input"; fi
+        if [[ -r "$h/power1_input" ]]; then PPT_NOW="$h/power1_input"; fi
+        if [[ -r "$h/power1_average" ]]; then PPT_AVG="$h/power1_average"; fi ;;
+      nvme)
+        if [[ -z "$NVME_T" && -r "$h/temp1_input" ]]; then NVME_T="$h/temp1_input"; fi ;;
+      spd5118)
+        if [[ -z "$DIMM0" && -r "$h/temp1_input" ]]; then DIMM0="$h/temp1_input"
+        elif [[ -z "$DIMM1" && -r "$h/temp1_input" ]]; then DIMM1="$h/temp1_input"; fi ;;
+      acpitz)
+        if [[ -r "$h/temp1_input" ]]; then ACPITZ="$h/temp1_input"; fi ;;
+    esac
+  done
+  return 0
+}
+
+# ── Field readers (never fail, never fork; empty string on any problem) ────
+_read_scaled() { # $1 sysfs path (may be empty), $2 integer divisor
+  local p="${1:-}" div="${2:-1}" v=""
+  [[ -n "$p" ]] || return 0
+  IFS= read -r v < "$p" 2>/dev/null || v=""
+  [[ "$v" =~ ^[0-9]+$ ]] || return 0
+  printf '%s' $(( v / div ))
+  return 0
+}
+_psi_avg10() { # $1 /proc/pressure/{cpu,memory} → the "some avg10" value
+  local p="$1" line=""
+  IFS= read -r line < "$p" 2>/dev/null || line=""
+  [[ "$line" == *avg10=* ]] || return 0
+  line="${line#*avg10=}"
+  printf '%s' "${line%% *}"
+  return 0
+}
+MEM_AVAIL_MB="" SWAP_FREE_MB=""
+_mem_fields() {
+  MEM_AVAIL_MB="" SWAP_FREE_MB=""
+  local k v u
+  while IFS=' ' read -r k v u; do
+    case "$k" in
+      MemAvailable:) MEM_AVAIL_MB=$(( v / 1024 )) ;;
+      SwapFree:)     SWAP_FREE_MB=$(( v / 1024 )); break ;;
+    esac
+  done < /proc/meminfo
+  return 0
+}
+
+# ── Subcommands ────────────────────────────────────────────────────────────
+cmd_run() {
+  mkdir -p "$LOG_DIR"
+  resolve_sensors
+  [[ -f "$CSV" ]] || printf '%s\n' "$HEADER" > "$CSV"
+  local ts tctl gpu ppt pavg nvt d0 d1 az load1 rest psic psim size
+  while :; do
+    ts=$EPOCHSECONDS
+    tctl=$(_read_scaled "$TCTL" 1000)
+    gpu=$(_read_scaled "$GPU_TEMP" 1000)
+    ppt=$(_read_scaled "$PPT_NOW" 1000000)
+    pavg=$(_read_scaled "$PPT_AVG" 1000000)
+    nvt=$(_read_scaled "$NVME_T" 1000)
+    d0=$(_read_scaled "$DIMM0" 1000)
+    d1=$(_read_scaled "$DIMM1" 1000)
+    az=$(_read_scaled "$ACPITZ" 1000)
+    IFS=' ' read -r load1 rest < /proc/loadavg 2>/dev/null || load1=""
+    _mem_fields
+    psic=$(_psi_avg10 /proc/pressure/cpu)
+    psim=$(_psi_avg10 /proc/pressure/memory)
+    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
+      "$ts" "$tctl" "$gpu" "$ppt" "$pavg" "$nvt" "$d0" "$d1" "$az" \
+      "$load1" "$MEM_AVAIL_MB" "$SWAP_FREE_MB" "$psic" "$psim" >> "$CSV"
+    # fsync the csv so the last pre-crash line survives an instant reset
+    # (uutils-compatible file-arg form; plain `sync` as fallback).
+    sync "$CSV" 2>/dev/null || sync 2>/dev/null || true
+    size=$(stat -c %s "$CSV" 2>/dev/null || echo 0)
+    if [[ "$size" =~ ^[0-9]+$ ]] && (( size > MAX_BYTES )); then
+      mv -f "$CSV" "$CSV.1"
+      printf '%s\n' "$HEADER" > "$CSV"
+    fi
+    sleep "$INTERVAL"
+  done
+}
+
+_csv_fresh() { # true iff the csv was written within the last INTERVAL+5 s
+  local mtime
+  [[ -f "$CSV" ]] || return 1
+  mtime=$(stat -c %Y "$CSV" 2>/dev/null || echo 0)
+  (( EPOCHSECONDS - mtime <= INTERVAL + 5 ))
+}
+
+cmd_start() {
+  mkdir -p "$LOG_DIR"
+  local pid=""
+  if [[ -f "$PIDFILE" ]] && IFS= read -r pid < "$PIDFILE" 2>/dev/null \
+     && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+    echo "hwmon-log: already running (pid $pid)"
+    return 0
+  fi
+  # A sampler without our pidfile (e.g. the systemd user unit running `run`)
+  # is still a sampler — never start a second writer on the same csv.
+  if _csv_fresh; then
+    echo "hwmon-log: already running (external sampler, csv fresh)"
+    return 0
+  fi
+  nohup env HOST_GUARD_ROOT="$REPO_ROOT" bash "$HERE/hwmon-log.sh" run >> "$DAEMON_LOG" 2>&1 &
+  pid=$!
+  disown "$pid" 2>/dev/null || true
+  printf '%s\n' "$pid" > "$PIDFILE"
+  echo "hwmon-log: started (pid $pid) → $CSV"
+}
+
+cmd_stop() {
+  local pid=""
+  if [[ -f "$PIDFILE" ]] && IFS= read -r pid < "$PIDFILE" 2>/dev/null \
+     && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+    kill "$pid" 2>/dev/null || true
+    rm -f "$PIDFILE"
+    echo "hwmon-log: stopped (pid $pid)"
+    return 0
+  fi
+  rm -f "$PIDFILE"
+  echo "hwmon-log: not running"
+}
+
+cmd_status() {
+  local pid="" now mtime age last=""
+  if [[ -f "$PIDFILE" ]] && IFS= read -r pid < "$PIDFILE" 2>/dev/null \
+     && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+    if [[ -f "$CSV" ]]; then
+      now=$EPOCHSECONDS
+      mtime=$(stat -c %Y "$CSV" 2>/dev/null || echo 0)
+      age=$(( now - mtime ))
+      if (( age <= INTERVAL + 5 )); then
+        IFS= read -r last < <(tail -n 1 "$CSV" 2>/dev/null) || last=""
+        echo "hwmon-log: running (pid $pid), csv fresh (${age}s old): $last"
+        return 0
+      fi
+      echo "hwmon-log: running (pid $pid) but csv STALE (${age}s old)"
+      return 1
+    fi
+    echo "hwmon-log: running (pid $pid) but no csv yet"
+    return 1
+  fi
+  if _csv_fresh; then
+    IFS= read -r last < <(tail -n 1 "$CSV" 2>/dev/null) || last=""
+    echo "hwmon-log: running (external sampler), csv fresh: $last"
+    return 0
+  fi
+  echo "hwmon-log: not running"
+  return 1
+}
+
+cmd_watch() {
+  [[ -f "$CSV" ]] || { echo "hwmon-log: no csv yet — start the sampler first"; return 1; }
+  local line ts tctl gpu ppt rest maxt=0 maxp=0 mark
+  trap 'echo; exit 0' INT TERM
+  echo "$HEADER"
+  while :; do
+    line=$(tail -n 1 "$CSV" 2>/dev/null || true)
+    IFS=',' read -r ts tctl gpu ppt rest <<< "$line" || true
+    if [[ "$tctl" =~ ^[0-9]+$ ]] && (( tctl > maxt )); then maxt=$tctl; fi
+    if [[ "$ppt" =~ ^[0-9]+$ ]] && (( ppt > maxp )); then maxp=$ppt; fi
+    mark=""
+    if [[ "$tctl" =~ ^[0-9]+$ ]] && (( tctl >= 90 )); then mark=" ⚠ Tctl≥90"; fi
+    printf '\r%s  [max: Tctl %s°C, PPT %sW]%s   ' "$line" "$maxt" "$maxp" "$mark"
+    sleep "$INTERVAL"
+  done
+}
+
+case "${1:-}" in
+  run)    cmd_run ;;
+  start)  cmd_start ;;
+  stop)   cmd_stop ;;
+  status) cmd_status ;;
+  watch)  cmd_watch ;;
+  *) echo "Usage: $0 {run|start|stop|status|watch}" >&2; exit 2 ;;
+esac
diff --git a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
index 8a4a2c85..f570566a 100644
--- a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
+++ b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
@@ -104,28 +104,39 @@ EFFORT_OVERRIDES: dict[str, str] = {
 
 # Per-agent runtime caps (seconds), ~2.5-3x the typical durations measured from
 # goal-session telemetry (tape_to_profit: developer ~41m, reviewer ~21m,
-# browser-qa ~20m, evaluator ~17m, decomposer ~8m, coherence ~4m). One flat
-# 7200s cap previously let a hung 20-minute reviewer burn a full 2 hours before
-# the watchdog fired. Agents NOT listed here (the full-pipeline-only chain:
-# orchestrator, qa, ui-*, auditor, release-manager, ...) fall back to the flat
-# CHAIN_CLAUDE_MAX_RUNTIME_SECONDS / CHAIN_DISPATCH_INFLIGHT_TIMEOUT global —
-# zero behavior change for run-phase.sh.
+# browser-qa ~20m, evaluator ~17m, decomposer ~8m, coherence ~4m; desk session
+# maxima for the full-pipeline chain: orchestrator ~9.4m, qa ~18.2m,
+# ui-impact ~7.4m, ui-test-designer ~11.4m, ux-regression ~7.1m,
+# auditor ~17.7m, phase-closure ~4.8m). One flat 7200s cap previously let a
+# hung 20-minute reviewer burn a full 2 hours before the watchdog fired.
+# SPEED-12 filled the full-pipeline rows (each ≥2.5× its observed maximum);
+# any agent still absent falls back to the flat
+# CHAIN_CLAUDE_MAX_RUNTIME_SECONDS / CHAIN_DISPATCH_INFLIGHT_TIMEOUT global.
 #
 # Resolution precedence (implemented by the shell seam, lib/quota-retry.sh):
 #   CHAIN_TIMEOUT_<AGENT> env  >  agents/<name>/agent.yaml max_runtime_seconds
 #   >  this table  >  flat global. An EXPLICITLY exported flat global keeps
 #   today's meaning and disables the per-agent table entirely.
 AGENT_TIMEOUTS_SECONDS: dict[str, int] = {
-    "goal-decomposer":      1800,   # typical ~8m
-    "developer":            7200,   # typical ~41m; initial builds vary — keep 2h
-    "reviewer":             3600,   # typical ~21m (observed hang burned 7200s)
-    "browser-qa-agent":     4500,   # typical ~20m; grows with journey count
-    "coherence-auditor":    1200,   # typical ~4m
-    "goal-evaluator":       3600,   # typical ~17m
-    "goal-proposer":        3600,
-    "iteration-summarizer": 1800,
-    "readme-maintainer":    1800,
-    "demo-narrator":        1800,
+    "goal-decomposer":       1800,   # typical ~8m
+    "developer":             7200,   # typical ~41m; initial builds vary — keep 2h
+    "reviewer":              3600,   # typical ~21m (observed hang burned 7200s)
+    "browser-qa-agent":      4500,   # typical ~20m; grows with journey count
+    "coherence-auditor":     1200,   # typical ~4m
+    "goal-evaluator":        3600,   # typical ~17m
+    "goal-proposer":         3600,
+    "iteration-summarizer":  1800,
+    "readme-maintainer":     1800,
+    "demo-narrator":         1800,
+    # SPEED-12: full-pipeline chain (desk maxima in the comment above)
+    "orchestrator":          2700,   # max ~9.4m → ~4.8×
+    "qa":                    5400,   # max ~18.2m → ~4.9×
+    "ui-impact-analyst":     1800,   # max ~7.4m → ~4.1×
+    "ui-test-designer":      1800,   # max ~11.4m → ~2.6×
+    "ux-regression-reviewer": 1800,  # max ~7.1m → ~4.2×
+    "auditor":               3600,   # max ~17.7m → ~3.4×
+    "phase-closure-auditor": 1800,   # max ~4.8m → ~6.3×
+    "release-manager":       2700,   # no recent trace; procedural git/gh work
 }
 
 # Reads from the legacy `.claude/agents/<name>.md` (frontmatter) by default to
@@ -636,7 +647,11 @@ def _self_test() -> int:
         assert timeout_for("reviewer") == 3600, "reviewer cap from the builtin table"
         assert timeout_for("coherence-auditor") == 1200
         assert timeout_for("developer") == 7200
-        assert timeout_for("orchestrator") is None, "full-pipeline agents keep the flat global"
+        # SPEED-12 filled the full-pipeline rows (2.5x+ observed desk maxima);
+        # only agents absent from the table fall back to the flat global.
+        assert timeout_for("orchestrator") == 2700, "SPEED-12: orchestrator capped"
+        assert timeout_for("qa") == 5400, "SPEED-12: qa capped"
+        assert timeout_for("phase-closure-auditor") == 1800
         assert timeout_for("some-unknown-agent") is None
         neutral = d / "neutral-agents"
         (neutral / "reviewer").mkdir(parents=True)
diff --git a/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py b/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
index 6b5c016e..a4146a09 100644
--- a/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
+++ b/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
@@ -261,13 +261,15 @@ def _new_iter_record(iter_name: str, ts: float | None) -> dict[str, Any]:
         "depth": None,
         "complete": False,
         "agents": {},          # name → {seconds, calls, retries, failures}
-        "engine_steps": {},    # name → seconds (engine_step events — RETRO-1 glue attribution)
+        "engine_steps": {},    # step → seconds (non-agent engine work; NOT in agent totals —
+                               # the sub-pipeline steps CONTAIN agent invocations)
         "skipped_steps": [],
         "pump_wait_seconds": 0,
         "quota_sleep_seconds": 0,
         "review_verdicts": [], # [{verdict, attempt}]
         "knob_active": False,  # iter_config event seen (experiment running)
         "journey_deltas": {},
+        "budget_event": None,  # first iter_budget event (SPEED-15), if any
     }
 
 
@@ -302,21 +304,35 @@ def build_wall_report(paths: list[str]) -> dict[str, dict[str, Any]]:
                 a = event.get("agent") or "unattributed"
                 row = cur["agents"].setdefault(
                     a, {"seconds": 0, "calls": 0, "retries": 0, "failures": 0})
-                row["seconds"] += int(event.get("duration_seconds") or 0)
+                # SPEED-13: prefer active_seconds (duration minus quota sleeps)
+                # when the event carries it; quota sleep is reported separately
+                # via quota_pause_end so nothing is lost.
+                secs = event.get("active_seconds")
+                if secs is None:
+                    secs = event.get("duration_seconds")
+                row["seconds"] += int(secs or 0)
                 row["calls"] += 1
                 row["retries"] += int(event.get("retries") or 0)
                 if int(event.get("exit_status") or 0) != 0:
                     row["failures"] += 1
-            elif kind == "engine_step" and cur is not None:
-                nm = event.get("step") or "?"
-                cur["engine_steps"][nm] = (cur["engine_steps"].get(nm, 0)
-                                           + int(event.get("duration_seconds") or 0))
             elif kind == "step_skipped" and cur is not None:
                 cur["skipped_steps"].append(event.get("step") or "?")
             elif kind == "dispatch_wait" and cur is not None:
                 cur["pump_wait_seconds"] += int(event.get("wait_seconds") or 0)
             elif kind == "quota_pause_end" and cur is not None:
                 cur["quota_sleep_seconds"] += int(event.get("sleep_seconds") or 0)
+            elif kind == "engine_step" and cur is not None:
+                step = event.get("step") or "?"
+                cur["engine_steps"][step] = (
+                    cur["engine_steps"].get(step, 0)
+                    + int(event.get("duration_seconds") or 0))
+            elif kind == "iter_budget" and cur is not None:
+                if cur.get("budget_event") is None:
+                    cur["budget_event"] = {
+                        "budget": int(event.get("budget") or 0),
+                        "elapsed": int(event.get("elapsed") or 0),
+                        "mode": event.get("mode") or "warn",
+                        "at_step": event.get("at_step") or "?"}
             elif kind == "review_verdict" and cur is not None:
                 cur["review_verdicts"].append({
                     "verdict": event.get("verdict") or "?",
@@ -389,28 +405,27 @@ def render_wall_text(report: dict[str, dict[str, Any]],
                     extra += f"  retries={row['retries']}"
                 out.append(f"      {a:<24s} {_fmt_m(row['seconds']):>8s}  "
                            f"calls={row['calls']}{extra}")
-            # Engine-side steps (RETRO-1): the sub-pipeline dispatch / showcase
-            # join that previously all landed in "unattributed (glue)". These
-            # wrap the goal-level wall spans that are NOT agent-attributed at
-            # this telemetry scope, so they count toward the attributed total.
-            engine_total = 0
-            for nm, secs in sorted(rec.get("engine_steps", {}).items(),
-                                   key=lambda kv: -kv[1]):
-                engine_total += secs
-                label = f"engine:{nm}"
-                out.append(f"      {label:<24s} {_fmt_m(secs):>8s}")
+            for step, secs in sorted(rec.get("engine_steps", {}).items(),
+                                     key=lambda kv: -kv[1]):
+                out.append(f"      [engine] {step:<15s} {_fmt_m(secs):>8s}  (contains agent time above)")
             if rec["skipped_steps"]:
                 out.append(f"      (resume-skipped: {', '.join(rec['skipped_steps'])})")
             if rec["pump_wait_seconds"]:
                 out.append(f"      pump-wait              {_fmt_m(rec['pump_wait_seconds']):>8s}")
             if rec["quota_sleep_seconds"]:
                 out.append(f"      quota-pauses           {_fmt_m(rec['quota_sleep_seconds']):>8s}")
+            be = rec.get("budget_event")
+            if be:
+                out.append(f"      OVER BUDGET at {be['at_step']}: {be['elapsed']}s > {be['budget']}s (mode={be['mode']})")
             if wall is not None:
-                attributed = agent_total + engine_total
-                if attributed > wall:
-                    out.append(f"      overlap saved          {_fmt_m(attributed - wall):>8s}  (parallel steps)")
+                # SPEED-13: agent rows are active time (quota sleeps excluded),
+                # so the residual must exclude the quota-pause seconds too or
+                # every pause would be misread as glue.
+                accounted = agent_total + rec["quota_sleep_seconds"]
+                if accounted > wall:
+                    out.append(f"      overlap saved          {_fmt_m(accounted - wall):>8s}  (parallel steps)")
                 else:
-                    out.append(f"      unattributed (glue)    {_fmt_m(wall - attributed):>8s}")
+                    out.append(f"      unattributed (glue)    {_fmt_m(wall - accounted):>8s}  (wall − agents(active) − quota)")
         completed = [i for i in s["iterations"] if i["complete"] and i["wall_seconds"]]
         if completed and iter_filter is None:
             mean = sum(i["wall_seconds"] for i in completed) / len(completed)
@@ -547,14 +562,17 @@ _WALL_FIXTURE = [
      "ts": "2026-07-01T10:08:00Z"},
     {"event": "agent_invocation_end", "session_id": "w-1", "agent": "goal-decomposer",
      "exit_status": 0, "duration_seconds": 480, "retries": 0, "ts": "2026-07-01T10:08:00Z"},
+    # SPEED-13: developer hit a quota pause — duration keeps wall meaning,
+    # active_seconds excludes the sleep, quota_pause_end reports it separately.
+    {"event": "quota_pause_end", "session_id": "w-1", "agent": "developer",
+     "sleep_seconds": 600, "ts": "2026-07-01T10:40:00Z"},
     {"event": "agent_invocation_end", "session_id": "w-1", "agent": "developer",
-     "exit_status": 0, "duration_seconds": 2400, "retries": 0, "ts": "2026-07-01T10:48:00Z"},
+     "exit_status": 0, "duration_seconds": 2400, "quota_sleep_seconds": 600,
+     "active_seconds": 1800, "retries": 0, "ts": "2026-07-01T10:48:00Z"},
+    {"event": "engine_step", "session_id": "w-1", "step": "lean-pipeline",
+     "duration_seconds": 3000, "ts": "2026-07-01T10:48:00Z"},
     {"event": "step_skipped", "session_id": "w-1", "step": "reviewer",
      "iter_name": "goal-w-iter-1", "ts": "2026-07-01T10:48:01Z"},
-    {"event": "engine_step", "session_id": "w-1", "step": "lean-pipeline",
-     "duration_seconds": 900, "ts": "2026-07-01T11:03:00Z"},
-    {"event": "engine_step", "session_id": "w-1", "step": "showcase-join",
-     "duration_seconds": 60, "ts": "2026-07-01T11:04:00Z"},
     {"event": "dispatch_wait", "session_id": "w-1", "agent": "browser-qa-agent",
      "wait_seconds": 120, "run_seconds": 1100, "status": "ok", "ts": "2026-07-01T11:10:00Z"},
     {"event": "agent_invocation_end", "session_id": "w-1", "agent": "browser-qa-agent",
@@ -646,8 +664,15 @@ def _self_test() -> int:
         if it1["wall_seconds"] != 5160:  # 10:00:00 → 11:26:00
             print(f"FAIL: iter-1 wall {it1['wall_seconds']} != 5160", file=sys.stderr)
             return 1
-        if it1["agents"]["developer"]["seconds"] != 2400:
-            print("FAIL: developer seconds attribution", file=sys.stderr)
+        # SPEED-13: active_seconds (1800) preferred over duration_seconds (2400)
+        if it1["agents"]["developer"]["seconds"] != 1800:
+            print("FAIL: developer active-seconds attribution", file=sys.stderr)
+            return 1
+        if it1["quota_sleep_seconds"] != 600:
+            print("FAIL: quota_pause_end attribution", file=sys.stderr)
+            return 1
+        if it1["engine_steps"].get("lean-pipeline") != 3000:
+            print(f"FAIL: engine_steps {it1['engine_steps']}", file=sys.stderr)
             return 1
         if it1["skipped_steps"] != ["reviewer"]:
             print(f"FAIL: skipped steps {it1['skipped_steps']}", file=sys.stderr)
@@ -655,9 +680,6 @@ def _self_test() -> int:
         if it1["pump_wait_seconds"] != 120:
             print("FAIL: pump wait attribution", file=sys.stderr)
             return 1
-        if it1["engine_steps"] != {"lean-pipeline": 900, "showcase-join": 60}:
-            print(f"FAIL: engine step attribution: {it1['engine_steps']}", file=sys.stderr)
-            return 1
         if it1["depth"] != "lean" or it1["verdict"] != "CONTINUE" or not it1["complete"]:
             print("FAIL: iter-1 metadata", file=sys.stderr)
             return 1
@@ -667,18 +689,10 @@ def _self_test() -> int:
         text = render_wall_text(report)
         for needle in ("goal-w-iter-1", "developer", "resume-skipped: reviewer",
                        "pump-wait", "incomplete/interrupted",
-                       "engine:lean-pipeline", "engine:showcase-join"):
+                       "[engine] lean-pipeline", "quota-pauses"):
             if needle not in text:
                 print(f"FAIL: wall render missing '{needle}'", file=sys.stderr)
                 return 1
-        # Glue math: engine-step seconds must move OUT of the residual. iter-1
-        # wall=5160, agents=480+2400+1220+240+900=5240 > wall → without engine
-        # steps this already reads "overlap saved"; assert the attributed total
-        # includes the 960 engine seconds (overlap line grows accordingly).
-        it1_block = text.split("goal-w-iter-2")[0]
-        if "overlap saved" not in it1_block:
-            print("FAIL: iter-1 should show overlap line with engine steps counted", file=sys.stderr)
-            return 1
         only2 = render_wall_text(report, iter_filter=2)
         if "goal-w-iter-2" not in only2 or "goal-w-iter-1" in only2:
             print("FAIL: --iter filter", file=sys.stderr)
```
