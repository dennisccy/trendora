# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index ed559158..63448fcc 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -93,6 +93,7 @@ from app.engine.research import (
     _dataset_version,  # single-sourced cache stamp (J-72/J-87) — never duplicated
     _membership_dataset_version,  # J-100: the NARROW membership-cache stamp (no forward-return term)
     event_study_cached,  # ops-hardening iter-2 (J-05): the ingest finalize hook warms one default hot key
+    factor_lab_all_cached,  # ops-hardening iter-51 (J-05/J-06/J-07): warms the Factor Lab default all-history key
     subject_catalog,
 )
 from app.seed_loader import price_load_symbols
@@ -2271,9 +2272,9 @@ class JobProgress:
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
     # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    # "index_series"]` it actually refreshed — empty/default until the hook has actually run (never
-    # fabricated on an interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc.
-    # already are).
+    # "drawdown_expectations", "index_series", "factor_lab_all"]` it actually refreshed — empty/default
+    # until the hook has actually run (never fabricated on an interrupted/failed row; gated in
+    # `_run_detail()` the SAME way `calendar_days` etc. already are).
     new_snapshot_dates: list[date_cls] = field(default_factory=list)
     aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
@@ -3928,8 +3929,8 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
     "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    "drawdown_expectations", "index_series"]` ACTUALLY refreshed — never a fabricated category (mirrors
-    the `omitted`/`passers` honesty convention already used elsewhere in this module).
+    "drawdown_expectations", "index_series", "factor_lab_all"]` ACTUALLY refreshed — never a fabricated
+    category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -4257,6 +4258,58 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 prog.job_id, "index_series_warm", time.monotonic() - _phase_t0,
             )
 
+            # ops-hardening iter-51 (J-05/J-06/J-07): warm the Factor Lab's default all-history hot key
+            # (`factor_lab_all_cached` -> `compute_factor_lab_all`, the SAME `EventStudyCache` sentinel
+            # namespace `research_hot_keys_warm` above uses for the event-study default key) so
+            # `GET /api/research/factor-lab?all=true`'s first post-ingest view is always a stored-row cache
+            # HIT — never the 578-875s live compute the iter-50 audit measured on the request path (its own
+            # verbatim recommendation: "serve /research/factor-lab from an ingest-time artifact instead of
+            # computing it on the request path"). Unconditional (not gated on `prog.new_snapshot_dates`),
+            # mirroring `forward_aggregates`/`index_series` above: the dataset-version stamp is GLOBAL, so
+            # ANY ingest anywhere can invalidate the one all-history key. A single default-key warm (never a
+            # per-as-of sweep), mirroring `research_hot_keys_warm`'s own "warm default keys only" philosophy.
+            #
+            # `prog.tick()` stamps the heartbeat immediately before this call — this single call can itself
+            # run for several minutes (measured 578-875s cold-MISS, `reports/perf-budgets.md` Addendum 8),
+            # so a tick right before it starts keeps `last_progress_at` from reading stale relative to the
+            # OTHER per-item loops in this tail, mirroring their own per-item tick convention.
+            #
+            # Honesty gate: `factor_lab_all_cached` never lets a MemoryError from `compute_factor_lab_all`
+            # escape — it catches it INTERNALLY and returns an honest degraded payload (`factors_status:
+            # "unavailable"`, or a per-(factor,horizon) `by_horizon[].status: "unavailable"`) WITHOUT
+            # persisting to `EventStudyCache` (see that function's own "never cached" degrade contract). So
+            # "the call didn't raise" is NOT sufficient proof a fresh row was written — this phase inspects
+            # the SAME degrade signals `factor_lab_all_cached` uses internally before claiming the category,
+            # mirroring `index_series_warm`'s "persisted this run" honesty gate just above (never a
+            # fabricated refresh for a degraded response). The outer `except MemoryError`/`except Exception`
+            # below still guard the rarer case of a MemoryError escaping BEFORE that internal catch (e.g.
+            # the dataset-version stamp read) — mirroring every other phase's per-item isolation convention.
+            _phase_t0 = time.monotonic()
+            try:
+                prog.tick()
+                factor_lab_all_payload = factor_lab_all_cached(session, cfg, as_of=None)
+                _factor_lab_all_degraded = (
+                    factor_lab_all_payload.get("factors_status") == "unavailable"
+                    or any(
+                        bh.get("status") == "unavailable"
+                        for entry in factor_lab_all_payload.get("factors_table", [])
+                        for bh in entry.get("by_horizon", [])
+                    )
+                )
+                if not _factor_lab_all_degraded:
+                    refreshed.append("factor_lab_all")
+            except MemoryError as exc:
+                _log_isolation_failure(
+                    "ingest factor-lab-all warm aborted — memory pressure: %s", exc,
+                )
+                _release_process_memory()
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+                _log_isolation_failure("ingest factor-lab-all warm failed (non-fatal): %s", exc)
+            logger.info(
+                "J-05 finalize-tail phase timing: job=%s phase=%s elapsed=%.2fs",
+                prog.job_id, "factor_lab_all_warm", time.monotonic() - _phase_t0,
+            )
+
             # ops-hardening iter-7 (J-06 closeout, audit B1): warm the per-claim `drawdown_expectations`
             # EventStudyCache view slot — the SAME cache slot `build_evidence_payload` looks up lazily via
             # `forward_testing.compute_drawdown_expectations_cached` on a live `/api/evidence` request.
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index 3e7af44c..e0afb4de 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -1537,8 +1537,6 @@ def _combination_cohort_members(pool: list[dict], resolved: list[dict], comb) ->
     list) call THIS function, so a cohort's drill-down total EQUALS its published N by construction
     (count-coherence keystone, invariant 13 — never a second membership rule). Pure index arithmetic over
     the already-built pool; recomputes no factor and no return."""
-    pool_n = len(pool)
-
     # per-condition membership (a set of pool indices) using each condition's nearest-rank quantile cutoff
     # over the SHARED pool's values for that factor; strict_overlap = the exact AND-intersection of singles.
     single_members: list[set[int]] = []
@@ -1559,9 +1557,22 @@ def _combination_cohort_members(pool: list[dict], resolved: list[dict], comb) ->
 
     # SECONDARY strict-overlap cohort: the exact AND-intersection of all single memberships (the demoted
     # iter-12 cohort) — empty for many selections (then NA + n, never a fabricated 0).
-    strict_members: set[int] = set(range(pool_n))
-    for members in single_members:
-        strict_members &= members
+    #
+    # ops-hardening iter-51 (J-05/J-06/J-07 fix, the exact frame logged before the 2026-08-05 17m30s
+    # wedge): start the intersection from the FIRST single-condition membership set (copied — `&=` mutates
+    # in place, and `single_members[0]` is a shared reference returned to every caller below, so intersecting
+    # the ORIGINAL object would corrupt it) instead of unconditionally allocating `set(range(pool_n))` and
+    # reducing it by intersection. Intersecting the full range with every `single_members` entry is exactly
+    # the intersection of those entries alone (the full range is the identity element under `&`), so this is
+    # a pure allocation-strategy change — byte-identical `strict` for every existing caller. No conditions ->
+    # an empty set (never a fabricated full-pool cohort).
+    strict_members: set[int]
+    if single_members:
+        strict_members = set(single_members[0])
+        for members in single_members[1:]:
+            strict_members &= members
+    else:
+        strict_members = set()
 
     # HEADLINE composite cohort: the top config-quantile of the pool by a config-weighted blend of the
     # conditions' oriented percentile ranks of the STORED values (REUSE `_composite_scores` +
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index d67041f7..5f5a73b7 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -32,7 +32,7 @@ from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
 from app.engine import data_manager
-from app.engine import forward_testing, indexes, market_phase, scanner, warmup
+from app.engine import forward_testing, indexes, market_phase, research, scanner, warmup
 from app.engine.data_manager import (
     JobProgress,
     _chunk_plan,
@@ -1052,7 +1052,8 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
     compute warms both), `market_phase` (the new date), `forward_aggregates` (ops-hardening iter-5: the
     current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key),
     `index_series` (ops-hardening iter-13: the fixture's own `SPY` bar is one of `index_chart.symbols`, so
-    the hot-key warm has real bars to compute from)."""
+    the hot-key warm has real bars to compute from), `factor_lab_all` (ops-hardening iter-51: the Factor
+    Lab's default all-history hot key)."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     with Session(engine) as session:
@@ -1061,7 +1062,7 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
     assert set(refreshed) == {
         "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
-        "research_hot_keys", "index_series",
+        "research_hot_keys", "index_series", "factor_lab_all",
     }
     with Session(engine) as session:
         rows = session.exec(select(CoverageSnapshot)).all()
@@ -1211,6 +1212,182 @@ def test_finalize_hook_index_series_memory_error_isolated_and_not_reported(
     } <= set(refreshed)
 
 
+# ==================================================================================================
+# ops-hardening iter-51 (J-05/J-06/J-07): the finalize hook's NEW `factor_lab_all` warm — mirrors the
+# `research_hot_keys`/`index_series` proofs above for the SINGLE unparameterized default all-history hot
+# key `GET /api/research/factor-lab?all=true` serves from `EventStudyCache` (`factor_lab_all_cached` /
+# `_ALL_FACTORS_SUBJECT` / `_ALL_FACTORS_VIEW` sentinel namespace).
+# ==================================================================================================
+def test_finalize_hook_warms_factor_lab_all_hot_key(finalize_hook_engine):
+    """TC-1 — a finalize hook call persists exactly one `EventStudyCache` row for the default all-history
+    Factor Lab key (`subject=_ALL_FACTORS_SUBJECT`, `view=_ALL_FACTORS_VIEW`, `asof_key=None`,
+    `horizon=default_horizon`) and reports "factor_lab_all" as refreshed."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="factor-lab-all-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "factor_lab_all" in refreshed
+    with Session(engine) as session:
+        rows = session.exec(select(EventStudyCache)).all()
+    all_factors_rows = [
+        r for r in rows
+        if r.subject == research._ALL_FACTORS_SUBJECT and r.view == research._ALL_FACTORS_VIEW
+    ]
+    assert len(all_factors_rows) == 1
+    # `_cache_asof_key(None)` (research.py) serializes an all-history (no as_of) key as the sentinel
+    # string "all", not a bare None column value -- the pre-existing (iter-31) `factor_lab_all_cached`
+    # contract, unchanged by this iteration.
+    assert all_factors_rows[0].asof_key == "all"
+    assert all_factors_rows[0].horizon == cfg.walk_forward.default_horizon
+
+
+def test_finalize_hook_factor_lab_all_unconditional_even_with_no_new_snapshot(finalize_hook_engine):
+    """Unconditional (not gated on `new_snapshot_dates`), mirroring `forward_aggregates`/`index_series`
+    above: the dataset-version stamp is GLOBAL, so this key is warmed even on a zero-new-snapshot
+    (already-current) finalize call."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="factor-lab-all-zero-work-probe", kind="backfill", start=d, end=d)
+        # prog.new_snapshot_dates deliberately left empty.
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "factor_lab_all" in refreshed
+
+
+def test_finalize_hook_factor_lab_all_second_run_still_reported_on_cache_hit(finalize_hook_engine):
+    """A SECOND finalize hook call with no intervening dataset change is a genuine cache HIT for the SAME
+    key — still honestly reported as "factor_lab_all" (mirrors `research_hot_keys_warm`'s own "call
+    succeeded, non-degraded" gate, not `index_series_warm`'s "persisted this run" gate — a clean HIT is not
+    a degrade). Exactly one `EventStudyCache` row for this key exists after both calls -- the second call
+    never writes a duplicate."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog1 = JobProgress(job_id="factor-lab-all-first", kind="backfill", start=d, end=d)
+        prog1.new_snapshot_dates = [d]
+        first = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
+    assert "factor_lab_all" in first
+
+    with Session(engine) as session:
+        prog2 = JobProgress(job_id="factor-lab-all-second", kind="backfill", start=d, end=d)
+        prog2.new_snapshot_dates = [d]
+        second = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
+    assert "factor_lab_all" in second
+    with Session(engine) as session:
+        rows = session.exec(select(EventStudyCache)).all()
+    all_factors_rows = [
+        r for r in rows
+        if r.subject == research._ALL_FACTORS_SUBJECT and r.view == research._ALL_FACTORS_VIEW
+    ]
+    assert len(all_factors_rows) == 1  # the second call never wrote a duplicate row
+
+
+def test_finalize_hook_factor_lab_all_memory_error_isolated_and_not_reported(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-error-case — a `MemoryError` escaping `factor_lab_all_cached` (e.g. before its own internal
+    catch) is isolated to that one warm step: it never flips the ingest job's own status, the OTHER
+    aggregates still refresh normally, "factor_lab_all" is honestly absent (never fabricated), and
+    `_release_process_memory()` runs (the iter-8 per-item isolation convention)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    release_calls: list[str] = []
+
+    def _boom(*_a, **_k):
+        raise MemoryError("forced factor-lab-all memory pressure")
+
+    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
+    monkeypatch.setattr(
+        data_manager, "_release_process_memory", lambda: release_calls.append("called"),
+    )
+    with Session(engine) as session:
+        prog = JobProgress(job_id="factor-lab-all-oom-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert "factor_lab_all" not in refreshed
+    assert {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys", "index_series",
+    } <= set(refreshed)
+    assert release_calls, "_release_process_memory() must be called on the MemoryError abort path"
+
+
+def test_finalize_hook_factor_lab_all_generic_failure_isolated_other_aggregates_still_refresh(
+    finalize_hook_engine, monkeypatch
+):
+    """A non-memory exception from `factor_lab_all_cached` (forced) does not prevent the OTHER aggregates
+    from refreshing — log + continue, never raise (mirrors the sibling per-item isolation tests above)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced factor-lab-all failure")
+
+    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="factor-lab-all-failure-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "factor_lab_all" not in refreshed
+    assert {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys", "index_series",
+    } <= set(refreshed)
+
+
+def test_finalize_hook_factor_lab_all_never_reported_on_whole_response_degrade(
+    finalize_hook_engine, monkeypatch
+):
+    """Honesty gate distinct from a plain exception: `factor_lab_all_cached` NEVER lets a MemoryError from
+    `compute_factor_lab_all` escape — it catches it INTERNALLY and returns an honest degraded dict
+    (`factors_status: "unavailable"`) WITHOUT persisting to `EventStudyCache`. A naive "the call didn't
+    raise -> append" gate would wrongly claim a refresh that never happened. This forces exactly that
+    degraded-but-non-raising return and asserts "factor_lab_all" is still honestly omitted."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    degraded_payload = {
+        "asof_date": None, "factors": [], "horizons": list(cfg.walk_forward.horizons),
+        "default_horizon": cfg.walk_forward.default_horizon, "deciles_count": cfg.research.factor_lab.deciles,
+        "min_sample": cfg.walk_forward.min_sample, "survivorship_bias": "x", "descriptive_caveat": "x",
+        "factors_table": [], "factors_status": "unavailable",
+    }
+
+    def _degraded(*_a, **_k):
+        return degraded_payload
+
+    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _degraded)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="factor-lab-all-degrade-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert "factor_lab_all" not in refreshed, (
+        "a whole-response degraded payload must never be claimed as a refresh, even though the call itself "
+        "did not raise"
+    )
+    assert {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys", "index_series",
+    } <= set(refreshed)
+
+
+def test_finalize_hook_factor_lab_all_phase_timing_log_line_present(finalize_hook_engine, caplog):
+    """The `factor_lab_all_warm` phase logs its own wall-clock "J-05 finalize-tail phase timing" line
+    unconditionally, mirroring every sibling phase (iter-48 diagnosis instrumentation convention)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with caplog.at_level("INFO", logger="trendora.data_manager"):
+        with Session(engine) as session:
+            prog = JobProgress(job_id="factor-lab-all-timing-probe", kind="backfill", start=d, end=d)
+            prog.new_snapshot_dates = [d]
+            data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert (
+        "J-05 finalize-tail phase timing: job=factor-lab-all-timing-probe phase=factor_lab_all_warm"
+        in caplog.text
+    ), caplog.text
+
+
 def test_finalize_hook_market_phase_computed_exactly_once_not_on_subsequent_read(
     finalize_hook_engine, monkeypatch
 ):
@@ -1289,6 +1466,7 @@ def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_eng
     monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
     monkeypatch.setattr(data_manager, "event_study_cached", _boom)
     monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
+    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
         prog.new_snapshot_dates = [d]
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index 57ab3d12..114f4e76 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -940,6 +940,128 @@ def test_single_flight_wait_ceiling_clears_the_measured_cold_compute(component_e
     )
 
 
+# ==================================================================================================
+# ops-hardening iter-51 (TC-4): `_combination_cohort_members`'s `strict_members` construction no longer
+# unconditionally allocates `set(range(pool_n))` before reducing it by intersection — the exact frame
+# logged immediately before the 2026-08-05 17m30s wedge. Two proofs, on a representative-size synthetic
+# pool (no DB needed — this is a pure index-arithmetic function over an already-built `pool`):
+#   1. byte-identical `single`/`strict`/`composite` outputs vs. a pinned pre-iter-51 reference oracle that
+#      keeps the original `set(range(pool_n))` behavior.
+#   2. `range` is never called with `pool_n` inside `_combination_cohort_members`'s own `strict_members`
+#      construction — intercepted via monkeypatch (LOAD_GLOBAL resolves a module-level `range` override
+#      before falling through to the builtin).
+# ==================================================================================================
+def _combination_cohort_members_pinned_pre_iter51(pool: list[dict], resolved: list[dict], comb) -> dict:
+    """A byte-for-byte copy of `_combination_cohort_members`'s PRE-iter-51 `strict_members` construction —
+    the unconditional `set(range(pool_n))` scratch allocation, reduced by intersection — pinned here as the
+    reference oracle the bounded version is proven against. Every other line is identical to the current
+    function (never calls the current `_combination_cohort_members`, which would prove nothing)."""
+    pool_n = len(pool)
+    single_members: list[set[int]] = []
+    for cond in resolved:
+        key = cond["factor"].key
+        fraction = cond["quantile"].fraction
+        ordered = sorted(obs["values"][key] for obs in pool)
+        if not ordered:
+            single_members.append(set())
+            continue
+        if cond["side"] == "top":
+            cutoff = research_module._quantile_cutoff(ordered, 1 - fraction)
+            members = {i for i, obs in enumerate(pool) if obs["values"][key] >= cutoff}
+        else:
+            cutoff = research_module._quantile_cutoff(ordered, fraction)
+            members = {i for i, obs in enumerate(pool) if obs["values"][key] <= cutoff}
+        single_members.append(members)
+
+    strict_members: set[int] = set(range(pool_n))  # the PRE-fix allocation, pinned verbatim
+    for members in single_members:
+        strict_members &= members
+
+    comp = comb.composite
+    composite_quantile = next(q for q in comb.quantiles if q.key == comp.quantile)
+    base_weights = [comp.weighting.default_weight] * len(resolved)
+    weight_total = sum(base_weights)
+    weights = [w / weight_total for w in base_weights]
+    composite_scores = research_module._composite_scores(pool, resolved, weights)
+    if composite_scores:
+        cutoff = research_module._quantile_cutoff(sorted(composite_scores), 1 - composite_quantile.fraction)
+        composite_members = {i for i, score in enumerate(composite_scores) if score >= cutoff}
+    else:
+        composite_members = set()
+
+    return {"single": single_members, "strict": strict_members, "composite": composite_members}
+
+
+def _combination_cohort_members_synthetic_fixture(pool_n: int):
+    """A deterministic (non-random), representative-size synthetic pool + 2-condition `resolved` +the
+    real shipped `combination` config — big enough (pool_n) to make an unbounded `set(range(pool_n))`
+    allocation observable, small enough to run in well under a second either way."""
+    cfg = load_config()
+    fl = cfg.research.factor_lab
+    comb = fl.combination
+    factors = fl.factors[:2]
+    assert len(factors) == 2, "sanity: the shipped catalog must carry >= 2 factors"
+    quantile = comb.quantiles[0]
+    resolved = [
+        {"factor": factors[0], "side": "top", "quantile": quantile},
+        {"factor": factors[1], "side": "bottom", "quantile": quantile},
+    ]
+    pool = [
+        {"values": {
+            factors[0].key: float((i * 37 + 11) % 997),
+            factors[1].key: float((i * 53 + 7) % 991),
+        }}
+        for i in range(pool_n)
+    ]
+    return pool, resolved, comb
+
+
+def test_combination_cohort_members_strict_matches_pinned_pre_iter51_reference():
+    """TC-4 (part 1) — the bounded `_combination_cohort_members` is byte-identical to the pinned
+    pre-iter-51 `set(range(pool_n))` reference, for `single`/`strict`/`composite`, on a representative
+    (pool_n=5,000) synthetic pool."""
+    pool, resolved, comb = _combination_cohort_members_synthetic_fixture(5_000)
+    got = research_module._combination_cohort_members(pool, resolved, comb)
+    want = _combination_cohort_members_pinned_pre_iter51(pool, resolved, comb)
+    assert got["strict"] == want["strict"], "strict membership diverges from the pinned pre-iter-51 reference"
+    assert got["composite"] == want["composite"], (
+        "composite membership diverges from the pinned pre-iter-51 reference"
+    )
+    assert len(got["single"]) == len(want["single"]) == len(resolved)
+    for got_members, want_members in zip(got["single"], want["single"]):
+        assert got_members == want_members, "single-condition membership diverges from the pinned reference"
+    assert want["strict"], "sanity: this fixture's two conditions must overlap (a non-empty strict cohort)"
+
+
+def test_combination_cohort_members_strict_no_full_range_allocation(monkeypatch):
+    """TC-4 (part 2) — for a representative pool_n, `_combination_cohort_members` never calls
+    `set(range(pool_n))`: intercepted by overriding `research.py`'s module-level `set` name (LOAD_GLOBAL
+    resolves it before falling through to the builtin) and recording any call whose sole argument is a
+    `range` object of length `pool_n`. The only bare `set(...)`/`set(range(...))` calls inside this
+    function's own body (never inside `_quantile_cutoff`/`_composite_scores`, neither of which calls
+    `set`) are the empty-cohort sentinels and the (now-removed) `strict_members` scratch allocation, so
+    this assertion is unambiguous for this call."""
+    pool_n = 5_000
+    pool, resolved, comb = _combination_cohort_members_synthetic_fixture(pool_n)
+
+    real_set = set
+    offending_calls: list[int] = []
+
+    def _counting_set(*args, **kwargs):
+        if args and isinstance(args[0], range) and len(args[0]) == pool_n:
+            offending_calls.append(len(args[0]))
+        return real_set(*args, **kwargs)
+
+    monkeypatch.setattr(research_module, "set", _counting_set, raising=False)
+    result = research_module._combination_cohort_members(pool, resolved, comb)
+
+    assert offending_calls == [], (
+        f"_combination_cohort_members must never call set(range(pool_n={pool_n})) -- "
+        f"observed {len(offending_calls)} such call(s)"
+    )
+    assert result["strict"], "sanity: this fixture's two conditions must overlap (a non-empty strict cohort)"
+
+
 # ==================================================================================================
 # ops-hardening iter-29 (AG-8): `_factor_observations`'s join accumulator (`ret_by_run_symbol`) used to
 # hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history for
```
