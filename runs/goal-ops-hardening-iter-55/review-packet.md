# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 4a55f74e..cb990e76 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -4231,7 +4231,18 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
             try:
                 latest_run_date = scanner._latest_stored_run_date(session)
                 if latest_run_date is not None:
-                    forward_aggregates_warmed = False
+                    # ops-hardening iter-55 (honest-status fix): count horizons that ACTUALLY completed
+                    # rather than latching a single bool True the moment any one horizon succeeds. Live
+                    # incident evidence (run 351, logs/backend.log:233042): horizons 1/5/10 succeeded,
+                    # horizon 20 raised MemoryError, horizon 60 was never attempted — the OLD single-bool
+                    # gate (set True inside the per-horizon try, never reset on the later break) still
+                    # appended "forward_aggregates" to `refreshed`, claiming full completion for a warm
+                    # that aborted 2 of 5 configured horizons short. `cfg.walk_forward.horizons` is a
+                    # small, fixed, known-in-advance list (unlike the variable-length per-date/per-claim
+                    # loops this function also runs), so "warmed" now means ALL of them completed this
+                    # run, not merely "at least one did."
+                    _forward_horizons_total = len(cfg.walk_forward.horizons)
+                    _forward_horizons_completed = 0
                     for h in cfg.walk_forward.horizons:
                         prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
                                      # compute here can take up to ~35s pre-warm; 5 sequential horizons could
@@ -4239,9 +4250,12 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                         # ops-hardening iter-52 (J-07): real scheduling yield alongside the heartbeat stamp
                         # above -- see `_refresh_ingest_aggregates`'s docstring for the full rationale.
                         time.sleep(0)
-                        # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` on one horizon is caught
-                        # HERE, distinctly, so a horizon that already succeeded before it is still honestly
-                        # reported — the outer `except Exception` below (unchanged for every OTHER exception
+                        # ops-hardening iter-8 (J-05 REGRESSION fix), iter-55 (honest-status fix): a
+                        # `MemoryError` on one horizon is caught HERE, distinctly, so horizons that already
+                        # completed before it still count toward `_forward_horizons_completed` — but (iter-55)
+                        # the aggregate-level completeness claim below now requires ALL configured horizons
+                        # to have completed, so a partial count no longer reports "forward_aggregates" as
+                        # refreshed. The outer `except Exception` below (unchanged for every OTHER exception
                         # type) has no per-horizon granularity, so a non-memory failure still aborts the whole
                         # block exactly as before (no regression to that existing behavior). On MemoryError
                         # this loop stops immediately (no further horizons attempted) and forces memory back
@@ -4264,7 +4278,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                                 forward_testing.forward_aggregates_ingest_cached(
                                     session, h, cfg, as_of=latest_run_date
                                 )
-                                forward_aggregates_warmed = True
+                                _forward_horizons_completed += 1
                             except MemoryError as exc:
                                 _log_isolation_failure(
                                     "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
@@ -4277,6 +4291,13 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                                 "J-05 finalize-tail sub-phase timing: job=%s phase=%s horizon=%s elapsed=%.2fs",
                                 prog.job_id, "forward_aggregates_warm", h, time.monotonic() - _horizon_t0,
                             )
+                    # ops-hardening iter-55: "forward_aggregates" is refreshed ONLY when every configured
+                    # horizon completed this run — a mid-loop MemoryError break leaves this False even
+                    # though one or more EARLIER horizons genuinely succeeded (their compute results are
+                    # still cached/persisted by `forward_aggregates_ingest_cached` itself; only the
+                    # run-level COMPLETENESS claim in `aggregates_refreshed` is corrected). The run's own
+                    # overall `status` field is untouched — isolate-and-continue behavior is unchanged.
+                    forward_aggregates_warmed = _forward_horizons_completed == _forward_horizons_total
                     if forward_aggregates_warmed:
                         refreshed.append("forward_aggregates")
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 6f90a1b8..c3b4513c 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -1118,6 +1118,27 @@ def _forward_agg_runs_with_fr(session: Session, horizon: int, as_of: Optional[da
     return sorted(session.exec(stmt.distinct()).all())
 
 
+# ops-hardening iter-55 (J-05/J-07): row-count width for the periodic INTRA-chunk yield below. The
+# existing per-CHUNK `time.sleep(0)` in `compute_forward_aggregates`'s outer loop (iter-52) only hands
+# off the GIL BETWEEN chunks — one chunk (`walk_forward.forward_agg_run_chunk` = 100 runs) measured
+# 24,272-51,778 rows live against the real committed DB (iter-55 profiling note, `reports/perf-
+# budgets.md`), with ZERO yield points inside it. This is the exact non-yielding stretch the iter-54
+# concurrent drill localized six connection-level `/api/health` non-answers to (Addendum 17,
+# `forward_aggregates_warm`, t+699.1s-783.6s, landing between the h5 and h10 sub-phase boundaries) —
+# under concurrent load (a live drill's second CPU-bound request racing the SAME GIL) a single chunk's
+# processing time was observed to balloon 10-20x past its solo baseline (backend.log: horizon=10 taking
+# 336-438s vs. a 19-21s same-horizon solo baseline elsewhere in the SAME log), consistent with the CPython
+# GIL-convoy effect: infrequent yield points give a waiting thread infrequent, easily-missed chances to
+# actually acquire the GIL. Mirrors `research._SORT_YIELD_CHUNK`'s own already-proven bounded-hold
+# convention (a real OS-level GIL hand-off every N rows of otherwise-uninterrupted pure-Python work) —
+# sized so one interval's own wall time stays the same order of magnitude as that sort's measured
+# ~0.037s/50K-row bound: this loop's own per-row cost profiled roughly 8x heavier (dict build + up to 7
+# accumulator adds vs. one comparison), so a proportionally narrower row width keeps the same bound.
+# Scheduling only — no value, order, or output change (TC-4/TC-7: byte-identical against a pinned
+# pre-fix reference oracle).
+_FORWARD_AGG_ROW_YIELD_CHUNK = 5_000
+
+
 def _forward_agg_slice_map(
     session: Session, horizon: int, slice_run_ids: list[int], batch: int,
 ) -> dict[tuple[int, str], tuple[float, Optional[float]]]:
@@ -1130,13 +1151,23 @@ def _forward_agg_slice_map(
     pair count (770K-803K measured live per horizon, iter-29's audit — the SAME join-accumulator shape iter-29
     fixed one function over in `research.py`, now confirmed live in THIS function's own `forward_testing.py:965`
     frame per the iter-29 evaluator's browser-QA finding). The caller discards this dict before the next
-    chunk — it never again holds the full horizon-partition at once."""
+    chunk — it never again holds the full horizon-partition at once.
+
+    ops-hardening iter-55 (J-05/J-07): a `time.sleep(0)` real GIL hand-off every
+    `_FORWARD_AGG_ROW_YIELD_CHUNK` rows — this loop previously ran the WHOLE slice (up to ~52K rows live)
+    with no yield point at all, one half of the non-yielding stretch this iteration bounds (the other half
+    is `compute_forward_aggregates`'s own per-observation loop just below, which reads the SAME chunk's
+    `ScannerResult` rows). See that constant's own docstring for the full rationale."""
     fr_stmt = select(
         ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown,
     ).where(ForwardReturn.horizon == horizon, ForwardReturn.run_id.in_(slice_run_ids))
     slice_map: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
-    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+    for row_i, (run_id, symbol, realized_return, max_drawdown) in enumerate(
+        session.exec(fr_stmt).yield_per(batch)
+    ):
         slice_map[(run_id, symbol)] = (realized_return, max_drawdown)
+        if row_i and row_i % _FORWARD_AGG_ROW_YIELD_CHUNK == 0:
+            time.sleep(0)  # iter-55: intra-chunk GIL hand-off — see `_FORWARD_AGG_ROW_YIELD_CHUNK` above.
     return slice_map
 
 
@@ -1280,11 +1311,19 @@ def compute_forward_aggregates(
         # the SAME bound `_forward_agg_slice_map` already established (iter-30). Feeds
         # `_ControlGroupBuilder`'s per-run RNG sampling below, then is discarded before the next chunk —
         # it never holds more than one chunk's observations at a time (TC-1).
+        #
+        # ops-hardening iter-55 (J-05/J-07): a `time.sleep(0)` real GIL hand-off every
+        # `_FORWARD_AGG_ROW_YIELD_CHUNK` rows — see that constant's docstring (above `_forward_agg_slice_
+        # map`) for the full rationale. Previously this loop ran the WHOLE chunk (up to ~52K rows live)
+        # with no yield point between the outer per-chunk `time.sleep(0)` calls at all — the exact stretch
+        # the iter-54 concurrent drill localized six connection-level `/api/health` non-answers to.
         chunk_obs_by_run: dict[int, list[dict]] = defaultdict(list)
-        for (
+        for row_i, (
             res_run_id, ticker, leadership_bucket, setup_status, sector, rank,
             is_vcp, is_pullback_to_rising_dma, is_flat_base_breakout,
-        ) in session.exec(res_stmt).yield_per(batch):
+        ) in enumerate(session.exec(res_stmt).yield_per(batch)):
+            if row_i and row_i % _FORWARD_AGG_ROW_YIELD_CHUNK == 0:
+                time.sleep(0)  # intra-chunk GIL hand-off — see `_FORWARD_AGG_ROW_YIELD_CHUNK` above.
             fr = slice_map.get((res_run_id, ticker))
             if fr is None:
                 continue  # this stock has no realized return at this horizon in this run (n=0 contribution)
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 450e2b0d..989ba815 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -2054,9 +2054,16 @@ def test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_l
 def test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly(
     finalize_hook_engine, monkeypatch
 ):
-    """TC-5 — a MemoryError on the SECOND of N configured horizons: the first horizon's real warm still
-    counts (honest partial report — 'forward_aggregates' IS in `refreshed`), and no horizon after the
-    second is attempted."""
+    """TC-1/TC-4 (iter-55 INVERTED from the pre-fix behavior this test used to encode) — a MemoryError on
+    the SECOND of N configured horizons: the FIRST horizon's real warm still ran, but completeness (ALL
+    configured horizons), not any-succeeded, is now the bar for claiming 'forward_aggregates' was
+    refreshed. Before iter-55 this test asserted `"forward_aggregates" in refreshed` after only 1 of
+    N>=3 horizons completed — i.e. it encoded the PRE-FIX (buggy) behavior as correct: the live-incident
+    evidence (run 351, `logs/backend.log:233042`) showed exactly this shape (some early horizons succeed,
+    a later one aborts under memory pressure, the rest are never attempted) still being reported as a full
+    refresh. This test now asserts the OPPOSITE: `"forward_aggregates"` is OMITTED whenever fewer than
+    ALL configured horizons complete, even though the first horizon's compute genuinely ran and its
+    result is still cached/persisted — only the run-level completeness CLAIM changes."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     n_horizons = len(cfg.walk_forward.horizons)
@@ -2076,7 +2083,56 @@ def test_finalize_hook_forward_aggregates_memory_error_after_partial_success_rep
         prog.new_snapshot_dates = [d]
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
     assert calls["n"] == 2, "the loop must stop right after the SECOND (raising) horizon"
-    assert "forward_aggregates" in refreshed  # the FIRST horizon's real warm still counts honestly
+    assert "forward_aggregates" not in refreshed, (
+        "iter-55: a mid-loop MemoryError must omit forward_aggregates even though the FIRST horizon "
+        f"completed successfully -- completeness (ALL horizons), not any-succeeded, is the bar: {refreshed}"
+    )
+
+
+def test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-1/TC-2/TC-4 — the EXACT live-incident shape (run 351, `logs/backend.log:233042`): with
+    `cfg.walk_forward.horizons == [1, 5, 10, 20, 60]` (config.yaml:777, 5 configured horizons), horizons
+    1, 5, and 10 succeed, horizon 20 raises `MemoryError`, and horizon 60 is never attempted. TC-1/TC-4:
+    `aggregates_refreshed` OMITS `"forward_aggregates"` even though 3 of 5 horizons genuinely completed;
+    the run's own `status` field is unaffected (isolate-and-continue unchanged -- this fixture's hook call
+    itself must not raise). TC-2: every OTHER finalize-tail member this fixture's data legitimately warms
+    (`coverage`, `membership_timeline`, `market_phase`, `latest_snapshot`, `research_hot_keys`,
+    `index_series`, `factor_lab_all`) is STILL present in `refreshed` -- the fix narrows only the
+    `forward_aggregates` gate, never any sibling gate."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    assert cfg.walk_forward.horizons == [1, 5, 10, 20, 60], (
+        "this test's live-incident shape (3 succeed, 1 MemoryErrors, 1 never attempted) is pinned to the "
+        f"real config.yaml:777 horizon list; got {cfg.walk_forward.horizons}"
+    )
+    real = forward_testing.forward_aggregates_ingest_cached
+    calls = {"n": 0}
+
+    def _three_succeed_then_boom(session, horizon, config=None, *, as_of=None):
+        calls["n"] += 1
+        if calls["n"] <= 3:  # horizons 1, 5, 10
+            return real(session, horizon, config, as_of=as_of)
+        raise MemoryError("simulated memory pressure at horizon 20")  # horizon 60 never reached
+
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _three_succeed_then_boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="fa-live-incident-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 4, "3 horizons succeed (1/5/10), the 4th call (horizon 20) raises and stops the loop"
+    assert "forward_aggregates" not in refreshed, (
+        f"TC-1/TC-4: 3 of 5 horizons completing is still incomplete -- must be omitted: {refreshed}"
+    )
+    for sibling in (
+        "coverage", "membership_timeline", "market_phase", "latest_snapshot", "research_hot_keys",
+        "index_series", "factor_lab_all",
+    ):
+        assert sibling in refreshed, (
+            f"TC-2: sibling aggregate {sibling!r} must remain refreshed -- the fix narrows ONLY the "
+            f"forward_aggregates gate: {refreshed}"
+        )
 
 
 def test_finalize_hook_drawdown_expectations_memory_error_on_first_claim_aborts_loop(
diff --git a/apps/backend/tests/test_forward_testing_aggregates_streaming.py b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
index 503c8361..94081fc2 100644
--- a/apps/backend/tests/test_forward_testing_aggregates_streaming.py
+++ b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
@@ -375,6 +375,42 @@ def test_compute_forward_aggregates_zero_fr_run_excluded_from_runs_with_fr(multi
     assert new_payload == reference_payload
 
 
+# ====================================================================================================
+# ops-hardening iter-55 (J-05/J-07, TC-7) — the intra-chunk `time.sleep(0)` yield bound.
+#
+# `_FORWARD_AGG_ROW_YIELD_CHUNK` (forward_testing.py, above `_forward_agg_slice_map`) inserts a real
+# GIL hand-off every N rows inside BOTH `_forward_agg_slice_map`'s row loop and `compute_forward_
+# aggregates`'s own per-observation loop -- the fix for the six connection-level `/api/health`
+# non-answers the iter-54 concurrent drill localized to this exact non-yielding stretch. The
+# TC-1/TC-2 tests above already prove byte-identity at the shipped chunk width (5,000 rows), but this
+# fixture (4-5 runs, 12 symbols/run) never reaches even ONE full row-yield-chunk, so those tests never
+# actually exercise the new `time.sleep(0)` call. This test monkeypatches the row-yield width down to 1
+# so EVERY row triggers a yield, then re-runs the SAME byte-identity comparison against the pinned
+# pre-rewrite reference oracle for every configured horizon, with and without `as_of` -- proving the
+# yield is scheduling-only (a `time.sleep(0)` call has no side effect on any computed value, order, or
+# output; this test makes that explicit rather than relying on it never firing).
+# ====================================================================================================
+@pytest.mark.parametrize("horizon", HORIZONS)
+@pytest.mark.parametrize("as_of", [None, HISTORICAL_AS_OF])
+def test_compute_forward_aggregates_byte_identical_with_row_yield_firing_every_row(
+    multi_run_engine, monkeypatch, horizon, as_of
+):
+    """TC-7: with `_FORWARD_AGG_ROW_YIELD_CHUNK` forced to 1 (a `time.sleep(0)` GIL hand-off after
+    EVERY row in both the slice-map build and the per-observation loop), `compute_forward_aggregates`
+    still returns a dict `==` to the pinned pre-rewrite reference implementation, for every configured
+    horizon (1/5/10/20/60) and both `as_of=None` and a historical `as_of` — the intra-chunk yield never
+    changes a computed value, only how often the GIL is handed off."""
+    monkeypatch.setattr(forward_testing_module, "_FORWARD_AGG_ROW_YIELD_CHUNK", 1)
+    cfg = load_config()
+    with Session(multi_run_engine) as session:
+        new_payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+        reference_payload = _reference_compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+    assert new_payload == reference_payload, (
+        f"row-yield-every-row broke byte-identity at horizon={horizon} as_of={as_of}"
+    )
+    assert new_payload["overall"]["n"] > 0  # sanity: this comparison is non-trivial
+
+
 # ====================================================================================================
 # ops-hardening iter-30 (AG-8, J-07) — `compute_forward_aggregates`'s OWN join-accumulator chunking.
 #
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 111 +++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |   1 +
 .../journey-scripts/J-04.json                      |  10 +-
 runs/goal-session-ops-hardening/state/blueprint.md |   4 +-
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   9 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   2 +
 8 files changed, 133 insertions(+), 8 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
