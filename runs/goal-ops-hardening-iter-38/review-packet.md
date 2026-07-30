# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 2928dc37..566b5277 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -648,11 +648,15 @@ def membership_timeline_cached(
         return json.loads(hit.payload_json)
 
     # MISS — compute once (the cold, BOUNDED compute) and persist under the current stamp.
-    # `_membership_timeline` runs its per-date loop inside a `prefilled_bar_cache` (one query loads every
-    # symbol's full series), and the resolver sources each date's trailing-bar count from that once-loaded
-    # series via `trailing_count` — so the cold compute pays ONE prefill + in-memory bisects, NOT one
-    # grouped-count round-trip per date (the O(dates) cost that hung the endpoint). The warm-up daemon
-    # precomputes this off the boot path so the FIRST request after a boot/rebuild is already a hit.
+    # ops-hardening iter-38 (audit B7, iter-36 — stale-docstring fix): `_membership_timeline`'s per-date
+    # excluded-by-reason counts are sourced via `_excluded_counts_by_date` (above), which reuses an ACTIVE
+    # outer job-scoped bar cache when one is already open (e.g. a `_do_backfill`/`_persist_per_date_
+    # coverage_snapshots` caller), or else walks the candidate pool in `membership_timeline_batch_symbols`-
+    # wide batches — ONE `_BarCache` instance whose contents are REPLACED per batch, never a single
+    # whole-pool `prefilled_bar_cache` scan — so peak resident bar data is bounded by batch width, not by
+    # the full candidate pool's price history (the O(dates) grouped-count round-trip this replaced no
+    # longer runs either way). The warm-up daemon precomputes this off the boot path so the FIRST request
+    # after a boot/rebuild is already a hit.
     payload = _membership_timeline(session, cfg, snapshot_dates)
 
     # prune stale rows (any older dataset_version) so the cache table does not grow unbounded as the
@@ -3107,7 +3111,17 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
             # already isolated inside `_run_targets` (never raised out of this `with` block), so reaching
             # this line only fails for a whole-stage exception (e.g. `read_pool()`/`prefill` itself), which
             # is caught below and releases the cache immediately instead of leaving it stashed.
-            prog._shared_bar_cache = shared_cache
+            #
+            # ops-hardening iter-38 (J-07 closure measurement): a TEST-ONLY escape hatch to force the
+            # pre-iter-37 fallback behavior (never stash/reuse the shared cache) for a genuine two-arm
+            # live-cache-vs-forced-fallback VmPeak comparison on a throwaway drill DB (see
+            # runs/goal-ops-hardening-iter-38/mem-drill/) — unset in every real deployment. This is the
+            # ONE choke point: skipping the stash here means every downstream consumer's own
+            # `prog._shared_bar_cache is not None` check (`_persist_per_date_coverage_snapshots`,
+            # `_refresh_ingest_aggregates`) falls back to its own independent `prefilled_bar_cache`/
+            # `nullcontext()` path, unchanged from pre-iter-37 behavior — no second code path needed.
+            if not os.environ.get("TRENDORA_FORCE_LEGACY_BAR_CACHE"):
+                prog._shared_bar_cache = shared_cache
 
             def _run_targets(window_targets: list[date_cls]) -> None:
                 """Compute + persist exactly this window's target dates — serial (workers<=1 or a single
@@ -3336,6 +3350,19 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     # targets) — every warm call below then falls back to its own pre-iter-37 behavior, unchanged.
     shared = prog._shared_bar_cache
     cache_ctx = attach_shared_cache(session, shared) if shared is not None else nullcontext()
+    # ops-hardening iter-38 (J-07 closure): an explicit, grep-able liveness assertion for THIS job — the
+    # binding iter-37 lesson is that a drill on a conditional path (a stashed reference, an attach/fallback
+    # context) must ASSERT the condition was live, never assume it from the lexical `with cache_ctx:` wrap
+    # alone. One line per job, corroborable against a bounded range of the live `logs/backend.log`.
+    # `logger.warning` (not `.info`): this app never configures a root-logger handler/level, so uvicorn's
+    # last-resort handler — the ONLY thing writing `trendora.data_manager` records into `logs/backend.log`
+    # — only surfaces WARNING and above (confirmed live: an `.info` call here was silently dropped, never
+    # once appearing in the log across a full drilled job).
+    logger.warning(
+        "J-07 finalize-tail cache_ctx liveness: job=%s resolved=%s",
+        prog.job_id,
+        "attach_shared_cache(live shared cache)" if shared is not None else "nullcontext(no shared cache)",
+    )
     try:
         with cache_ctx:
             try:
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 14d14f56..52400b8a 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -19,6 +19,7 @@ from __future__ import annotations
 import json
 import socket
 import time
+from contextlib import contextmanager
 from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
@@ -2164,18 +2165,78 @@ def test_do_backfill_new_snapshot_dates_tracks_genuinely_new_dates_only(backfill
     assert prog2.already_snapshotted == 1
 
 
-def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job):
+def test_do_backfill_whole_stage_exception_releases_shared_cache_and_reraises(backfilled_job, monkeypatch):
+    """TC-6 (reviewer MINOR, iter-37) — a whole-stage exception inside `_do_backfill`'s
+    `with prefilled_bar_cache(...)` block, occurring AFTER `prog._shared_bar_cache` has genuinely been
+    stashed (every per-date compute/persist failure below that point is already isolated inside
+    `_run_targets`/`_persist_isolated`, never raised out of the `with` block — see their own docstrings),
+    must set `prog._shared_bar_cache` back to `None`, call `_release_process_memory()`, and re-raise the
+    ORIGINAL exception (never swallowed) — `data_manager.py`'s `except Exception:` branch around line 3162.
+
+    Load-bearing (not vacuous): faults `_checkpoint_run_record` ONLY once `prog._shared_bar_cache` is
+    already non-None (i.e. strictly after the real stash — the real `prefilled_bar_cache`/`_compute_one_
+    backfill_date`/`_persist` calls all run for real first), so the post-fault `is None` assertion actually
+    proves the except branch's reset ran — a cache that was NEVER stashed in the first place would make
+    that assertion pass trivially even if the reset line were deleted."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in trading if d not in snapshotted)
+
+    real_checkpoint = data_manager._checkpoint_run_record
+
+    def _fault_after_stash(engine_arg, prog_arg):
+        if prog_arg._shared_bar_cache is not None:
+            raise RuntimeError("simulated whole-stage fault after cache stash")
+        return real_checkpoint(engine_arg, prog_arg)
+
+    monkeypatch.setattr(data_manager, "_checkpoint_run_record", _fault_after_stash)
+
+    release_calls: list[bool] = []
+    real_release = data_manager._release_process_memory
+
+    def _spy_release() -> None:
+        release_calls.append(True)
+        real_release()
+
+    monkeypatch.setattr(data_manager, "_release_process_memory", _spy_release)
+
+    prog = JobProgress(job_id="whole-stage-exc-probe", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        with pytest.raises(RuntimeError, match="simulated whole-stage fault after cache stash"):
+            data_manager._do_backfill(session, cfg, prog, eng=engine)
+
+    assert prog._shared_bar_cache is None, (
+        "a whole-stage exception must clear the stashed shared-cache reference, not leave it stale"
+    )
+    assert release_calls, "a whole-stage exception must call _release_process_memory() before re-raising"
+
+
+def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job, monkeypatch):
     """ops-hardening iter-2 (J-05) end-to-end: a real backfill job dispatched through `run_data_job` (the
     SAME path the API uses) reaches the finalize hook, persists a `coverage_snapshot` row, and the job's
     final summary (the SAME dict `GET /api/data/jobs/{id}` serves) carries a non-empty
     `aggregates_refreshed`. Searches from the LATEST end of the trading calendar (the other new-date test
-    above searches from the earliest) so the two never contend for the same fresh date."""
+    above searches from the earliest) so the two never contend for the same fresh date.
+
+    ops-hardening iter-38 (audit T2, iter-37 — full-comparison strengthening): the per-category warm loops
+    inside `_refresh_ingest_aggregates` each swallow non-`MemoryError` exceptions (log + continue), so a
+    break in the live-cache attach path shows up ONLY as a silently shorter `aggregates_refreshed` list —
+    the pre-existing `>=` subset assertions above would not catch that. This test also runs a SECOND job of
+    the identical shape (a different fresh date) with the shared-cache attach FORCED off
+    (`prog._shared_bar_cache` nulled right before the finalize hook runs, mirroring pre-iter-37 behavior —
+    every downstream `cache_ctx` resolves to its own independent `prefilled_bar_cache`/`nullcontext()`
+    fallback, unchanged), then asserts the two runs' `aggregates_refreshed` sets are IDENTICAL: the shared-
+    cache attach is a pure performance optimization, so it must never change which categories succeed."""
     engine = backfilled_job["engine"]
     cfg = backfilled_job["cfg"]
     with Session(engine) as session:
         trading = _trading_days(session, cfg)
         snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
-    fresh_date = next(d for d in reversed(trading) if d not in snapshotted)
+    fresh_dates = (d for d in reversed(trading) if d not in snapshotted)
+    fresh_date = next(fresh_dates)
 
     job = create_job("backfill", fresh_date, fresh_date)
     summary = run_data_job(job.job_id, config=cfg, engine=engine)
@@ -2200,6 +2261,29 @@ def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job):
     this_run = next(r for r in persisted if r["kind"] == "backfill" and r["start"] == fresh_date.isoformat())
     assert set(this_run["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}
 
+    # TC-7 (audit T2) — forced-fallback comparison, same job shape, a different fresh date.
+    fallback_fresh_date = next(fresh_dates)
+    real_refresh = data_manager._refresh_ingest_aggregates
+
+    def _forced_fallback_refresh(session_arg, cfg_arg, prog_arg):
+        # force every downstream consumer's `prog._shared_bar_cache is not None` check to miss, mirroring
+        # pre-iter-37 behavior (each warm call opens its own independent cache / no cache) — the live-cache
+        # run above already completed and returned its summary, untouched by this patch.
+        prog_arg._shared_bar_cache = None
+        return real_refresh(session_arg, cfg_arg, prog_arg)
+
+    monkeypatch.setattr(data_manager, "_refresh_ingest_aggregates", _forced_fallback_refresh)
+    fallback_job = create_job("backfill", fallback_fresh_date, fallback_fresh_date)
+    fallback_summary = run_data_job(fallback_job.job_id, config=cfg, engine=engine)
+    assert fallback_summary["status"] == "ok"
+
+    assert set(fallback_summary["aggregates_refreshed"]) == set(summary["aggregates_refreshed"]), (
+        "the forced-fallback run's aggregates_refreshed category list diverged from the live-cache run's "
+        "for the SAME job shape — the shared-cache attach must be a pure performance optimization; any "
+        "category that silently drops out under only one path (a swallowed exception in a per-category "
+        "warm loop) is exactly the regression audit finding T2 (iter-37) warned this assertion must catch"
+    )
+
 
 def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
     """TC-14 — a completed `fetch` run's persisted detail always carries `aggregates_refreshed: null` (the
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 170 ++++++++++++++++++++-
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   9 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   2 +
 5 files changed, 182 insertions(+), 3 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
