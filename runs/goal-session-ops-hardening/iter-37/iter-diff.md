# Iteration diff (bounded)

Files changed: 2. Shown in full: 1.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/data_manager.py` (169 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index a8c67716..2928dc37 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -38,6 +38,7 @@ import threading
 import time
 import uuid
 from concurrent.futures import ThreadPoolExecutor, as_completed
+from contextlib import nullcontext
 from dataclasses import dataclass, field
 from datetime import date as date_cls, datetime, timedelta, timezone
 from pathlib import Path
@@ -2043,6 +2044,18 @@ class JobProgress:
     # concurrency the pool used (min(config workers, target dates)).
     _backfill_per_date_seconds_sum: float = 0.0
     _backfill_concurrency: int = 0
+    # ops-hardening iter-37 (J-07 closure) — the ONE prefilled `_BarCache` `_do_backfill` builds for the
+    # whole job (NOT serialized — internal scratch, like the two accumulators above): stashed here instead
+    # of being dropped/released the moment `_do_backfill` returns, so the ingest finalize hook's per-date
+    # coverage warm (`_persist_per_date_coverage_snapshots`) can ATTACH the SAME already-loaded cache
+    # (`attach_shared_cache`) instead of opening a SECOND independent whole-table `daily_prices` load for
+    # the same job. None until `_do_backfill` populates it on a successful run with >= 1 in-range target
+    # (a fetch/expand-only job, or a backfill with no targets, never sets it — nothing to share; a whole-
+    # stage `_do_backfill` failure releases it immediately instead of stashing it — see `_do_backfill`).
+    # The finalize hook nulls this out immediately before releasing it back to the OS
+    # (`_release_process_memory`) so `gc.collect()` can actually reclaim it — a lingering reference here
+    # would defeat that release entirely (iter-27's "second consecutive rebuild starts lean" guarantee).
+    _shared_bar_cache: Optional["_BarCache"] = None
     # ops-hardening iter-9 (F1 / J-04 step 6) — `time.monotonic()` of the last durable progress checkpoint
     # written onto this job's OPEN run-history row (NOT serialized — internal throttle scratch, like the
     # two accumulators above). 0.0 means "never checkpointed", so the first advance always writes.
@@ -3083,6 +3096,18 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
     # chunks the requested range is split into (J-03 chunking is an execution/progress concept only).
     try:
         with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
+            # ops-hardening iter-37 (J-07 closure): the same `shared_cache` this `with` block just built
+            # is what the ingest finalize hook's per-date coverage warm needs next (`_refresh_ingest_
+            # aggregates` -> `_persist_per_date_coverage_snapshots`, reached after this function returns).
+            # Stash the reference on `prog` NOW (before the `with` block exits and pops it from the
+            # per-session registry) so that hook can `attach_shared_cache` it to ITS OWN session instead of
+            # opening a SECOND independent whole-table `daily_prices` prefill for the same job — closing
+            # the exact gap `test_kdate_backfill_loads_each_symbol_at_most_once` measures. Deliberately set
+            # unconditionally here (not only after the loop below): a per-date compute/persist failure is
+            # already isolated inside `_run_targets` (never raised out of this `with` block), so reaching
+            # this line only fails for a whole-stage exception (e.g. `read_pool()`/`prefill` itself), which
+            # is caught below and releases the cache immediately instead of leaving it stashed.
+            prog._shared_bar_cache = shared_cache
 
             def _run_targets(window_targets: list[date_cls]) -> None:
                 """Compute + persist exactly this window's target dates — serial (workers<=1 or a single
@@ -3134,8 +3159,25 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
                 if window_targets:
                     _run_targets(window_targets)
                 prog.chunk_index += 1
-    finally:
+    except Exception:
+        # ops-hardening iter-37 (J-07 closure): a whole-stage exception here (e.g. `read_pool()`/`prefill`
+        # itself faulting — every per-date compute/persist failure below this point is already isolated
+        # inside `_run_targets`, never raised out of the `with` block) means the ingest finalize hook that
+        # would otherwise reuse and release `prog._shared_bar_cache` never runs for this job. Release
+        # immediately — same discipline as before this change — and clear the stashed reference so nothing
+        # downstream mistakes it for a still-usable cache.
+        prog._shared_bar_cache = None
         _release_process_memory()
+        raise
+    # success: deliberately NOT released here. `prog._shared_bar_cache` (stashed above, before the `with`
+    # block exited) is now the ONLY reference keeping this ~1.13 GB whole-table cache alive — kept alive on
+    # purpose so the ingest finalize hook (`_refresh_ingest_aggregates` -> `_persist_per_date_coverage_
+    # snapshots`, this job's ONLY other bar-cache consumer, reached after this function returns) can
+    # ATTACH the same already-loaded cache instead of opening a SECOND whole-table `daily_prices` prefill
+    # for the same job. That hook's own `finally` releases it (nulling the reference first so `gc.collect()`
+    # can actually reclaim it) once it is done — iter-27's "second consecutive rebuild starts lean"
+    # guarantee still holds; only the release's TIMING moves, from immediately here to right after that
+    # hook finishes.
     # UNCAPPED total (not `len(date_failures)`, a bounded sample) so `error_other` — and the invariant
     # `snapshots_created + already_snapshotted + error_other == dates_total` — stays exact past 20 failures.
     prog.error_other = prog.date_failures_total
@@ -3157,12 +3199,22 @@ def _persist_per_date_coverage_snapshots(
 
     The CURRENT resolved as-of is skipped (already persisted by `refresh_coverage_snapshot`), so the common
     single-latest-date backfill filters to nothing and pays NO bar-cache load at all. When there IS extra
-    work, ONE shared, re-entrant `prefilled_bar_cache` covers the whole loop — the whole-table bar scan runs
-    at most once regardless of date count (each per-date `_compute_coverage_uncached` reuses it), so warming
-    N dates costs one load, not N. Each row equals a fresh `_compute_coverage_uncached(as_of=d)`. Per-date
-    isolation (log + continue) so one date's failure never drops the rest; the caller wraps this whole call
-    non-fatally too. Reads only committed bars (backfill adds none), writes only `CoverageSnapshot` rows —
-    so the shared cache never serves a stale series (AG-8: no unbounded request-path load; this is ingest).
+    work, ONE shared bar cache covers the whole loop — the whole-table bar scan runs at most once regardless
+    of date count (each per-date `_compute_coverage_uncached` reuses it), so warming N dates costs one load,
+    not N. Each row equals a fresh `_compute_coverage_uncached(as_of=d)`. Per-date isolation (log + continue)
+    so one date's failure never drops the rest; the caller wraps this whole call non-fatally too. Reads only
+    committed bars (backfill adds none), writes only `CoverageSnapshot` rows — so the shared cache never
+    serves a stale series (AG-8: no unbounded request-path load; this is ingest).
+
+    ops-hardening iter-37 (J-07 closure): when `prog` carries a `_shared_bar_cache` (stashed by `_do_backfill`
+    right before it returns — the common case: this hook always runs after a `_do_backfill` call for the
+    SAME job), this function ATTACHES that already-loaded cache to `session` instead of opening its OWN
+    `prefilled_bar_cache` — closing the "loaded twice per job" gap `test_kdate_backfill_loads_each_symbol_
+    at_most_once` measures (previously TWO independent whole-table `daily_prices` prefills ran per backfill
+    job: one here, one in `_do_backfill`). `_refresh_ingest_aggregates` (the caller) releases the shared
+    cache once this loop returns. When no shared cache is present — this function called directly (e.g. a
+    unit test), or a backfill with zero in-range targets whose `_do_backfill` never built one — it falls
+    back to opening its own `prefilled_bar_cache`, byte-identical to this function's pre-iter-37 behavior.
 
     ops-hardening iter-4 (F1 fix, re-review CRITICAL): calls the bare `prog.tick()` (heartbeat-only — no
     `activity` argument, so it stamps ONLY `last_progress_at` and never overwrites the "scanning ..." line;
@@ -3178,9 +3230,17 @@ def _persist_per_date_coverage_snapshots(
     todo = [d for d in dates if d != current]
     if not todo:
         return  # the only newly-created date IS the current stamp (already persisted) — no extra load
-    pool_symbols = {row["symbol"] for row in read_pool()}
     aborted_for_memory = False
-    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
+    shared = prog._shared_bar_cache
+    if shared is not None:
+        # iter-37: reuse the ONE cache `_do_backfill` already built for this job (zero re-scan) — released
+        # later by `_refresh_ingest_aggregates`'s own `finally`, not by this function.
+        cache_ctx = attach_shared_cache(session, shared)
+    else:
+        # no shared cache handed down — fall back to this function's own prefill, unchanged from before.
+        pool_symbols = {row["symbol"] for row in read_pool()}
+        cache_ctx = prefilled_bar_cache(session, expected_symbols=pool_symbols)
+    with cache_ctx:
         for d in todo:
             prog.tick()  # F1 fix (iter-4): per-date heartbeat stamp before this date's heavy coverage compute
             try:
@@ -3202,13 +3262,15 @@ def _persist_per_date_coverage_snapshots(
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
                 logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
     # iter-8 AUDIT (B1 fix): the `_release_process_memory()` inside the loop above necessarily runs while
-    # this function's OWN prefilled `_BarCache` (~1.5 GB — see `_release_process_memory`'s docstring) is
-    # still referenced by the enclosing `with`, so the single largest freeable block cannot be trimmed
-    # there and the caller's NEXT independent warm block (market-phase, forward-aggregates, drawdown)
-    # would start on the same un-trimmed arena — i.e. without the headroom this fix exists to restore.
-    # Trim again AFTER the context manager drops the cache, mirroring `_do_backfill`'s own post-
-    # `prefilled_bar_cache` `_release_process_memory()`. Memory-abort path only: the normal completion
-    # path keeps its pre-existing behavior byte-unchanged.
+    # `cache_ctx`'s cache is still referenced by the enclosing `with`, so the single largest freeable block
+    # cannot be trimmed there and the caller's NEXT independent warm block (market-phase, forward-
+    # aggregates, drawdown) would start on the same un-trimmed arena — i.e. without the headroom this fix
+    # exists to restore. Trim again AFTER the context manager exits. Own-cache (fallback) path: this
+    # actually reclaims the ~1.5 GB block, mirroring `_do_backfill`'s own post-`prefilled_bar_cache`
+    # release. Shared-cache path (iter-37, the common case): `prog._shared_bar_cache` still references the
+    # cache at this point, so this trim reclaims only OTHER freed garbage — the shared block itself is
+    # reclaimed later by `_refresh_ingest_aggregates`'s own release, after nulling that reference. Memory-
+    # abort path only: the normal completion path keeps its pre-existing behavior byte-unchanged.
     if aborted_for_memory:
         _release_process_memory()
 
@@ -3254,183 +3316,231 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
         # here; just acknowledge honestly that a fresh snapshot now exists.
         refreshed.append("latest_snapshot")
 
+    # ops-hardening iter-37 (J-07 closure): attach `_do_backfill`'s already-loaded shared `_BarCache` (if
+    # any — stashed on `prog`, see `_do_backfill`'s own docstring) to THIS session for the WHOLE finalize
+    # tail below, not just the coverage sub-call. `bar_cache`/`prefilled_bar_cache` are RE-ENTRANT on
+    # session id (see `bar_cache`'s own docstring): every warm call this function drives that internally
+    # opens `with bar_cache(session):` on a cache miss — `market_phase.market_phase_cached` ->
+    # `compute_market_phase`, and `forward_testing.compute_drawdown_expectations_cached` ->
+    # `phase_context_by_date` -> `_causal_timeline`, both of which read the benchmark (SPY) series per
+    # date/claim — finds THIS session's id already registered and transparently REUSES the one pre-loaded
+    # cache instead of opening its own fresh (unprefilled) one and lazily reloading SPY on every call. That
+    # was the remaining gap `test_kdate_backfill_loads_each_symbol_at_most_once` measured beyond the
+    # coverage-snapshot double-load this iteration's other fix (`_persist_per_date_coverage_snapshots`)
+    # closes: SPY has real bars, so it is already loaded from `_do_backfill`'s single whole-table prefill —
+    # every OTHER caller just needs to find that cache instead of not knowing it exists. `_persist_per_date_
+    # coverage_snapshots` below ALSO re-checks `prog._shared_bar_cache` itself for its own direct-call
+    # test-compat fallback; attaching it here first is harmless/idempotent (`attach_shared_cache` is
+    # re-entrant-safe on an already-registered session id — see its own docstring). A no-op (`nullcontext`)
+    # when no shared cache was ever stashed (fetch/expand-only job, or a backfill with zero in-range
+    # targets) — every warm call below then falls back to its own pre-iter-37 behavior, unchanged.
+    shared = prog._shared_bar_cache
+    cache_ctx = attach_shared_cache(session, shared) if shared is not None else nullcontext()
     try:
-        payload = refresh_coverage_snapshot(session, cfg)
-        if payload is not None:
-            refreshed.append("coverage")
-            # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
-            # `membership_timeline_cached` internally as part of computing the payload just persisted above
-            # — warmed for free by that SAME call, never a second/separate derivation.
-            refreshed.append("membership_timeline")
-    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
-        logger.exception("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
-
-    # iter-2 review (CRITICAL): also persist a per-date coverage_snapshot for every date THIS run newly
-    # created, so the app-wide as-of switcher serves REAL coverage for each historical date from storage —
-    # not the all-zero "not yet computed" sentinel. Still the "coverage" category (no new one); own
-    # try/except (log + continue) so it never flips the job. Skips the current stamp (persisted above) and
-    # is a no-op — no bar-cache load — for the common single-latest-date backfill.
-    try:
-        _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates, prog)
-    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
-        logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)
+        with cache_ctx:
+            try:
+                payload = refresh_coverage_snapshot(session, cfg)
+                if payload is not None:
+                    refreshed.append("coverage")
+                    # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
+                    # `membership_timeline_cached` internally as part of computing the payload just persisted
+                    # above — warmed for free by that SAME call, never a second/separate derivation.
+                    refreshed.append("membership_timeline")
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+                logger.exception("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
+
+            # iter-2 review (CRITICAL): also persist a per-date coverage_snapshot for every date THIS run
+            # newly created, so the app-wide as-of switcher serves REAL coverage for each historical date
+            # from storage — not the all-zero "not yet computed" sentinel. Still the "coverage" category
+            # (no new one); own try/except (log + continue) so it never flips the job. Skips the current
+            # stamp (persisted above) and is a no-op — no bar-cache load — for the common single-latest-
+            # date backfill.
+            try:
+                _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates, prog)
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+                logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)
 
-    market_phase_warmed = False
-    for d in prog.new_snapshot_dates:
-        prog.tick()  # F1 fix: per-date heartbeat stamp -- see function docstring above.
-        try:
-            market_phase.market_phase_cached(session, d, cfg)
-            market_phase_warmed = True
-        # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-date isolate-and-
-        # continue below — a `MemoryError` stops THIS loop immediately (no further dates attempted) and
-        # forces memory back to the OS, instead of hammering the next date's allocation under pressure.
-        # `market_phase_warmed` already honestly reflects any dates that succeeded before the abort.
-        except MemoryError as exc:
-            logger.exception(
-                "ingest market-phase warm aborted at %s — memory pressure, stopping remaining dates in "
-                "this loop: %s", d, exc,
-            )
-            _release_process_memory()
-            break
-        except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
-            logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
-    if market_phase_warmed:
-        refreshed.append("market_phase")
-
-    # ops-hardening iter-5 (J-06): warm the CURRENT latest stored run's per-horizon forward-aggregate
-    # cache (GET /api/backtest's `evidence_by_horizon`, ~34.77s pre-fix over all 5 configured horizons —
-    # reports/perf-budgets.md). Unconditional (not gated on `prog.new_snapshot_dates`, unlike the
-    # per-date coverage/market-phase loops above): the dataset-version stamp is GLOBAL, so ANY ingest
-    # anywhere (even a historical-gap backfill far from the latest date) can invalidate the latest run's
-    # already-cached aggregate — e.g. a backfilled EARLIER date's forward returns newly enter the
-    # latest as-of's expanding "<= D" window. Warming only the ONE current-latest key (not every
-    # historical as-of) mirrors the "research_hot_keys" default-key philosophy just below, not the
-    # per-date coverage/market-phase sweep — each per-horizon compute can itself be as expensive as the
-    # measured 34.77s violation, so sweeping every `new_snapshot_dates` entry here (as coverage/
-    # market_phase do) would risk turning a full-universe rebuild's finalize tail into a multi-hour
-    # operation instead of the intended fix. A user-navigated HISTORICAL as-of on `/backtest` still
-    # computes-once-and-caches on first view (the same cold-miss contract EventStudyCache/
-    # MarketPhaseCache already carry) — never pre-warmed here.
-    try:
-        latest_run_date = scanner._latest_stored_run_date(session)
-        if latest_run_date is not None:
-            forward_aggregates_warmed = False
-            for h in cfg.walk_forward.horizons:
-                prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
-                             # compute here can take up to ~35s pre-warm; 5 sequential horizons could
-                             # otherwise freeze the heartbeat for minutes without a per-horizon tick).
-                # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` on one horizon is caught
-                # HERE, distinctly, so a horizon that already succeeded before it is still honestly
-                # reported — the outer `except Exception` below (unchanged for every OTHER exception
-                # type) has no per-horizon granularity, so a non-memory failure still aborts the whole
-                # block exactly as before (no regression to that existing behavior). On MemoryError this
-                # loop stops immediately (no further horizons attempted) and forces memory back to the OS.
+            market_phase_warmed = False
+            for d in prog.new_snapshot_dates:
+                prog.tick()  # F1 fix: per-date heartbeat stamp -- see function docstring above.
                 try:
-                    forward_testing.forward_aggregates_ingest_cached(session, h, cfg, as_of=latest_run_date)
-                    forward_aggregates_warmed = True
+                    market_phase.market_phase_cached(session, d, cfg)
+                    market_phase_warmed = True
+                # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-date isolate-and-
+                # continue below — a `MemoryError` stops THIS loop immediately (no further dates attempted)
+                # and forces memory back to the OS, instead of hammering the next date's allocation under
+                # pressure. `market_phase_warmed` already honestly reflects any dates that succeeded before
+                # the abort.
                 except MemoryError as exc:
                     logger.exception(
-                        "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
-                        "stopping remaining horizons in this loop: %s", h, exc,
+                        "ingest market-phase warm aborted at %s — memory pressure, stopping remaining dates "
+                        "in this loop: %s", d, exc,
                     )
                     _release_process_memory()
                     break
-            if forward_aggregates_warmed:
-                refreshed.append("forward_aggregates")
-    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
-        logger.exception("ingest forward-aggregate warm failed (non-fatal): %s", exc)
+                except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
+                    logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
+            if market_phase_warmed:
+                refreshed.append("market_phase")
+
+            # ops-hardening iter-5 (J-06): warm the CURRENT latest stored run's per-horizon forward-aggregate
+            # cache (GET /api/backtest's `evidence_by_horizon`, ~34.77s pre-fix over all 5 configured horizons
+            # — reports/perf-budgets.md). Unconditional (not gated on `prog.new_snapshot_dates`, unlike the
+            # per-date coverage/market-phase loops above): the dataset-version stamp is GLOBAL, so ANY ingest
+            # anywhere (even a historical-gap backfill far from the latest date) can invalidate the latest
+            # run's already-cached aggregate — e.g. a backfilled EARLIER date's forward returns newly enter
+            # the latest as-of's expanding "<= D" window. Warming only the ONE current-latest key (not every
+            # historical as-of) mirrors the "research_hot_keys" default-key philosophy just below, not the
+            # per-date coverage/market-phase sweep — each per-horizon compute can itself be as expensive as
+            # the measured 34.77s violation, so sweeping every `new_snapshot_dates` entry here (as coverage/
+            # market_phase do) would risk turning a full-universe rebuild's finalize tail into a multi-hour
+            # operation instead of the intended fix. A user-navigated HISTORICAL as-of on `/backtest` still
+            # computes-once-and-caches on first view (the same cold-miss contract EventStudyCache/
+            # MarketPhaseCache already carry) — never pre-warmed here.
+            try:
+                latest_run_date = scanner._latest_stored_run_date(session)
+                if latest_run_date is not None:
+                    forward_aggregates_warmed = False
+                    for h in cfg.walk_forward.horizons:
+                        prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
+                                     # compute here can take up to ~35s pre-warm; 5 sequential horizons could
+                                     # otherwise freeze the heartbeat for minutes without a per-horizon tick).
+                        # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` on one horizon is caught
+                        # HERE, distinctly, so a horizon that already succeeded before it is still honestly
+                        # reported — the outer `except Exception` below (unchanged for every OTHER exception
+                        # type) has no per-horizon granularity, so a non-memory failure still aborts the whole
+                        # block exactly as before (no regression to that existing behavior). On MemoryError
+                        # this loop stops immediately (no further horizons attempted) and forces memory back
+                        # to the OS.
+                        try:
+                            forward_testing.forward_aggregates_ingest_cached(
+                                session, h, cfg, as_of=latest_run_date
+                            )
+                            forward_aggregates_warmed = True
+                        except MemoryError as exc:
+                            logger.exception(
+                                "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
+                                "stopping remaining horizons in this loop: %s", h, exc,
+                            )
+                            _release_process_memory()
+                            break
+                    if forward_aggregates_warmed:
+                        refreshed.append("forward_aggregates")
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+                logger.exception("ingest forward-aggregate warm failed (non-fatal): %s", exc)
 
-    try:
-        subjects = subject_catalog(cfg)
-        if subjects:
-            # the SAME default (first catalog subject, config default_horizon, episodes view, all-history)
-            # a fresh `/research/event-study` page load with no query params would request — the one hot
-            # key worth warming at ingest (goal.md: "warm default (subject,horizon,all-history) keys").
-            event_study_cached(session, subjects[0]["key"], cfg.walk_forward.default_horizon, cfg)
-            refreshed.append("research_hot_keys")
-    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
-        logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)
-
-    # ops-hardening iter-13 (J-06, aggregation candidate #7): warm the SINGLE unparameterized default
-    # hot key for `GET /api/indexes` (`range_key=cfg.index_chart.default_range`, `full=True` —
-    # `PhaseCrossViewCard` on `/` and `IndexVendorPanel` on `/data` both request exactly this,
-    # unparameterized, on mount). Mirrors the `research_hot_keys` block just above: a single-key warm,
-    # unconditional (NOT gated on `prog.new_snapshot_dates`) because `IndexSeriesCache`'s
-    # dataset-version stamp is scoped to the configured `index_chart.symbols`' bar freshness (not to
-    # "this run's new snapshot dates") — ANY ingest that lands a bar for a configured index symbol,
-    # anywhere, must invalidate it, mirroring `forward_aggregates`'s "the stamp is global" reasoning
-    # above. Deferred import (not at module level): `indexes.py` already imports `load_seed_meta` FROM
-    # this module at ITS OWN module level, so importing `indexes` back here at data_manager's module
-    # scope would cycle; the deferred, function-scoped import breaks the cycle exactly like
-    # `forward_aggregates_ingest_cached`'s own deferred `_dataset_version` import from `research.py`.
-    #
-    # iter-8 MemoryError-isolation convention: caught distinctly from the generic exception below, stops
-    # immediately (a single key, not a loop — nothing further to attempt) and calls
-    # `_release_process_memory()` before moving on to the next aggregate category. "index_series" is
-    # appended ONLY when this call actually persisted a new row this run (`persisted` is False on a
-    # cache HIT — an honest "was skipped" omission, never a fabricated refresh, mirroring every other
-    # category's honesty gate above).
-    from app.engine import indexes  # deferred: see comment above (breaks a module-load cycle)
+            try:
+                subjects = subject_catalog(cfg)
+                if subjects:
+                    # the SAME default (first catalog subject, config default_horizon, episodes view,
+                    # all-history) a fresh `/research/event-study` page load with no query params would
+                    # request — the one hot key worth warming at ingest (goal.md: "warm default
+                    # (subject,horizon,all-history) keys").
+                    event_study_cached(session, subjects[0]["key"], cfg.walk_forward.default_horizon, cfg)
+                    refreshed.append("research_hot_keys")
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
+                logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)
+
+            # ops-hardening iter-13 (J-06, aggregation candidate #7): warm the SINGLE unparameterized default
+            # hot key for `GET /api/indexes` (`range_key=cfg.index_chart.default_range`, `full=True` —
+            # `PhaseCrossViewCard` on `/` and `IndexVendorPanel` on `/data` both request exactly this,
+            # unparameterized, on mount). Mirrors the `research_hot_keys` block just above: a single-key warm,
+            # unconditional (NOT gated on `prog.new_snapshot_dates`) because `IndexSeriesCache`'s
+            # dataset-version stamp is scoped to the configured `index_chart.symbols`' bar freshness (not to
+            # "this run's new snapshot dates") — ANY ingest that lands a bar for a configured index symbol,
+            # anywhere, must invalidate it, mirroring `forward_aggregates`'s "the stamp is global" reasoning
+            # above. Deferred import (not at module level): `indexes.py` already imports `load_seed_meta` FROM
+            # this module at ITS OWN module level, so importing `indexes` back here at data_manager's module
+            # scope would cycle; the deferred, function-scoped import breaks the cycle exactly like
+            # `forward_aggregates_ingest_cached`'s own deferred `_dataset_version` import from `research.py`.
+            #
+            # iter-8 MemoryError-isolation convention: caught distinctly from the generic exception below,
... [diff_bound] apps/backend/app/engine/data_manager.py: 169 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_backfill_coverage_shared_cache.py b/apps/backend/tests/test_backfill_coverage_shared_cache.py
new file mode 100644
index 00000000..13423846
--- /dev/null
+++ b/apps/backend/tests/test_backfill_coverage_shared_cache.py
@@ -0,0 +1,285 @@
+"""ops-hardening iter-37 (J-07 closure) — the shared-cache fix for the last unbounded whole-table
+`daily_prices` prefill on the multi-date backfill finalize path.
+
+Root cause (iter-36/l): `_do_backfill` (`data_manager.py:2888`) and `_persist_per_date_coverage_snapshots`
+(`data_manager.py:3191`, invoked from `_refresh_ingest_aggregates` for the SAME job) each opened their OWN
+independent `prefilled_bar_cache` — the whole `daily_prices` table (~1.13 GB at the live basis) was loaded
+TWICE per K-date backfill job instead of once (`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_
+at_most_once` measured this directly: every symbol loaded exactly 2x pre-fix). This iteration's fix has
+`_do_backfill` stash its already-loaded `_BarCache` onto `JobProgress._shared_bar_cache`, and
+`_persist_per_date_coverage_snapshots` (plus every other warm call `_refresh_ingest_aggregates` drives —
+market-phase, forward-aggregates, research hot-keys, index-series, drawdown-expectations) ATTACH that same
+pre-loaded cache instead of opening a fresh one.
+
+Named proofs (binding iter-29/32 lesson: pin the OLD code TEXT for a byte-identity oracle — never call the
+NEW code from both sides of the comparison; binding iter-29/31/32 lesson: a byte-identity oracle must also
+prove it is load-bearing via a mutation that would NOT be caught if the fix were reverted):
+
+  TC-7 byte-identity  — the pinned PRE-FIX body of `_persist_per_date_coverage_snapshots` (`git show
+                        HEAD:apps/backend/app/engine/data_manager.py` at the iter-37 dispatch commit —
+                        ALWAYS opened its own independent `prefilled_bar_cache`, `prog._shared_bar_cache`
+                        did not exist) produces a BYTE-IDENTICAL persisted `CoverageSnapshot` payload to
+                        the shipped implementation (which attaches a pre-loaded shared cache via
+                        `prog._shared_bar_cache`), for the SAME K real snapshot dates.
+  TC-8 mutation-style — poisoning ONE symbol's series inside the shared cache handed to the SHIPPED
+                        function changes its persisted output relative to a clean run (proving the shipped
+                        code genuinely READS bar values FROM `prog._shared_bar_cache`, not from a silent
+                        independent reload that would mask a broken wiring); the SAME poisoned cache handed
+                        to the PINNED REFERENCE (which never looks at `_shared_bar_cache` at all) produces
+                        the SAME output as an unpoisoned reference run — proving this exact mutation would
+                        NOT be caught if the shared-cache fix were reverted to the old always-own-prefill
+                        behavior (the oracle is load-bearing, not a rubber stamp).
+
+`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` (separate file, unmodified this
+iteration) independently covers the load-COUNT invariant this fix targets (max 1 load per symbol for the
+whole job) via a full end-to-end `run_data_job` — this module isolates the coverage-warm VALUE correctness
+specifically, calling `_persist_per_date_coverage_snapshots` directly per the plan's documented test-compat
+contract ("any test that calls `_persist_per_date_coverage_snapshots` directly, without going through
+`_do_backfill` first, keeps working unchanged").
+"""
+from __future__ import annotations
+
+import json
+import logging
+
+import pytest
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine import data_manager
+from app.engine import universe_resolver
+from app.engine.data_manager import (
+    JobProgress,
+    _release_process_memory,
+    _resolve_coverage_asof,
+    _trading_days,
+    create_job,
+    refresh_coverage_snapshot_for,
+    run_data_job,
+)
+from app.engine.prices import _BarCache, prefilled_bar_cache
+from app.engine.universe_screen import read_pool
+from app.models import CoverageSnapshot
+
+logger = logging.getLogger(__name__)
+
+
+# ====================================================================================================
+# Pinned PRE-FIX reference implementation of `_persist_per_date_coverage_snapshots`
+# (`git show HEAD:apps/backend/app/engine/data_manager.py` at the iter-37 dispatch commit — the tree
+# BEFORE this iteration's shared-cache edits), verbatim body. Binding iter-29/32 lesson: pin the OLD code
+# TEXT, never call the NEW code from both sides of a byte-identity comparison. `prog._shared_bar_cache`
+# did not exist pre-fix, so this reference NEVER reads it — it always opens its own independent cache.
+# ====================================================================================================
+def _reference_persist_per_date_coverage_snapshots(
+    session: Session, cfg, dates: list, prog: JobProgress
+) -> None:
+    if not dates:
+        return
+    current = _resolve_coverage_asof(session, None, cfg)
+    todo = [d for d in dates if d != current]
+    if not todo:
+        return  # the only newly-created date IS the current stamp (already persisted) — no extra load
+    pool_symbols = {row["symbol"] for row in read_pool()}
+    aborted_for_memory = False
+    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
+        for d in todo:
+            prog.tick()
+            try:
+                refresh_coverage_snapshot_for(session, cfg, d)
+            except MemoryError as exc:
+                logger.exception(
+                    "ingest per-date coverage warm aborted at %s — memory pressure, stopping remaining "
+                    "dates in this loop: %s", d, exc,
+                )
+                _release_process_memory()
+                aborted_for_memory = True
+                break
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
+                logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
+    if aborted_for_memory:
+        _release_process_memory()
+
+
+def _read_coverage_payloads(session: Session, cfg, dates: list) -> dict:
+    """Read back the persisted `CoverageSnapshot.payload_json` for each date (keyed by ISO date), parsed
+    to a dict so the comparison is over VALUES, not JSON-string formatting."""
+    dataset_version = data_manager._membership_dataset_version(session, cfg)
+    out = {}
+    for d in dates:
+        row = session.exec(
+            select(CoverageSnapshot).where(
+                CoverageSnapshot.asof_key == d.isoformat(),
+                CoverageSnapshot.dataset_version == dataset_version,
+            )
+        ).first()
+        assert row is not None, f"expected a persisted CoverageSnapshot row for {d.isoformat()}"
+        out[d.isoformat()] = json.loads(row.payload_json)
+    return out
+
+
+@pytest.fixture(scope="module")
+def snapshot_dates_engine(tmp_path_factory):
+    """A seeded DB with K=3 REAL snapshot dates already committed via a real, unmodified backfill job
+    (`run_data_job` — its per-date compute/persist logic, `scanner.compute_run_payload` /
+    `scanner.persist_run_payload`, is untouched by this iteration's fix; only the bar-cache ACQUISITION
+    mechanism changed). The 3 dates are comfortably before the resolved 'current' as-of (the latest
+    trading day), so `_persist_per_date_coverage_snapshots`'s own `todo` filter keeps all three across
+    every test below. Module-scoped: built once; `CoverageSnapshot` rows are idempotent upserts, so the
+    tests below repeatedly overwrite (never accumulate) the same keys."""
+    cfg = load_config()
+    _sc = cfg.scanner.model_copy(
+        update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})}
+    )
+    cfg = cfg.model_copy(update={"scanner": _sc})
+    from app.seed_loader import load_seed
+
+    db_path = tmp_path_factory.mktemp("shared_cache_seed") / "sc.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    load_seed(engine, cfg)
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+    daily_start = cfg.scanner.snapshot_cadence.daily_start or trading[0]
+    daily_idx = next(i for i, d in enumerate(trading) if d >= daily_start)
+    assert daily_idx + 3 <= len(trading)
+    r_start, r_end = trading[daily_idx], trading[daily_idx + 2]
+    dates = [d for d in trading if r_start <= d <= r_end]
+    assert len(dates) == 3
+    assert trading[-1] not in dates, "sanity: the picked dates must exclude the resolved current as-of"
+
+    job = create_job("backfill", r_start, r_end)
+    summary = run_data_job(job.job_id, config=cfg, engine=engine)
+    assert summary["status"] == "ok"
+    assert summary["snapshots_created"] == 3
+    return engine, cfg, dates
+
+
+# ====================================================================================================
+# TC-7 — byte-identity, real K-date snapshot inputs
+# ====================================================================================================
+def test_shared_cache_coverage_byte_identical_to_pinned_reference(snapshot_dates_engine):
+    engine, cfg, dates = snapshot_dates_engine
+
+    # REFERENCE: the pinned pre-iter-37 body — always opens its OWN independent prefilled_bar_cache.
+    with Session(engine) as session:
+        prog_ref = JobProgress(job_id="ref", kind="backfill", start=dates[0], end=dates[-1])
+        _reference_persist_per_date_coverage_snapshots(session, cfg, dates, prog_ref)
+        reference_payloads = _read_coverage_payloads(session, cfg, dates)
+
+    # SHIPPED: reuses a pre-loaded shared cache via `prog._shared_bar_cache` — the iter-37 mechanism
+    # `_do_backfill` wires up for real; here it is built directly, exercising the SAME attach path.
+    with Session(engine) as session:
+        pool_symbols = {row["symbol"] for row in read_pool()}
+        with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
+            prog_shipped = JobProgress(job_id="shipped", kind="backfill", start=dates[0], end=dates[-1])
+            prog_shipped._shared_bar_cache = shared_cache
+            data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog_shipped)
+        shipped_payloads = _read_coverage_payloads(session, cfg, dates)
+
+    assert shipped_payloads == reference_payloads, (
+        "the shipped shared-cache _persist_per_date_coverage_snapshots diverged from the pinned pre-fix "
+        "reference for the same K real snapshot-date inputs — the shared-cache fix must be a pure "
+        "performance refactor (byte-identical persisted CoverageSnapshot payloads)"
+    )
+
+
+# ====================================================================================================
+# TC-8 — mutation-style: the byte-identity oracle above is load-bearing, not a rubber stamp
+# ====================================================================================================
+def test_shared_cache_mutation_caught_as_failure(snapshot_dates_engine):
+    engine, cfg, dates = snapshot_dates_engine
+    pool_symbols = {row["symbol"] for row in read_pool()}
+
+    with Session(engine) as session:
+        # a victim symbol confirmed ADMITTED at the last target date — poisoning it must therefore be
+        # observable as an admitted->excluded flip (universe_count / universe_diagnostic / membership
+        # timeline all change), not a no-op against an already-excluded candidate.
+        resolved = universe_resolver.resolve_with_reasons(session, dates[-1], cfg)
+        assert resolved["admitted"], "sanity: the live pool must admit at least one candidate at this date"
+        victim = resolved["admitted"][0]
+
+        poisoned_cache = _BarCache()
+        poisoned_cache.prefill(session, expected_symbols=pool_symbols)
+        assert poisoned_cache._by_symbol.get(victim), "sanity: the victim symbol must have real bars"
+        # poison EVERY bar of the victim's series into a worthless penny/no-volume stock — comfortably
+        # below every configured `universe.filters` admission threshold (min_price / min_dollar_vol).
+        poisoned_cache._by_symbol[victim] = [
+            bar._replace(close=0.0001, open=0.0001, high=0.0001, low=0.0001, volume=1.0)
+            for bar in poisoned_cache._by_symbol[victim]
+        ]
+
+        prog_shipped_poisoned = JobProgress(
+            job_id="shipped-poisoned", kind="backfill", start=dates[0], end=dates[-1]
+        )
+        prog_shipped_poisoned._shared_bar_cache = poisoned_cache
+        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog_shipped_poisoned)
+        shipped_poisoned_payloads = _read_coverage_payloads(session, cfg, dates)
+
+        # the SAME poisoned cache, handed to the PINNED REFERENCE — which never reads `_shared_bar_cache`
+        # at all (the field did not exist pre-fix) and always opens its OWN independent, correct prefill.
+        prog_ref_poisoned = JobProgress(
+            job_id="ref-poisoned", kind="backfill", start=dates[0], end=dates[-1]
+        )
+        prog_ref_poisoned._shared_bar_cache = poisoned_cache
+        _reference_persist_per_date_coverage_snapshots(session, cfg, dates, prog_ref_poisoned)
+        reference_poisoned_payloads = _read_coverage_payloads(session, cfg, dates)
+
+        # a clean reference run (no poisoning) — the "what an unpoisoned run looks like" baseline.
+        prog_ref_clean = JobProgress(job_id="ref-clean", kind="backfill", start=dates[0], end=dates[-1])
+        _reference_persist_per_date_coverage_snapshots(session, cfg, dates, prog_ref_clean)
+        reference_clean_payloads = _read_coverage_payloads(session, cfg, dates)
+
+    assert shipped_poisoned_payloads != reference_clean_payloads, (
+        f"poisoning {victim!r} inside the shared cache produced NO observable change in the SHIPPED "
+        f"function's persisted output — the byte-identity oracle above would not actually catch a broken "
+        f"shared-cache wiring (either the shipped code never reads bar VALUES from `prog._shared_bar_cache`, "
+        f"or the poisoning failed to cross an admission threshold)"
+    )
+    assert reference_poisoned_payloads == reference_clean_payloads, (
+        "the PINNED pre-fix reference must be BLIND to a poisoned `prog._shared_bar_cache` (that field did "
+        "not exist before this iteration's fix, and the reference body never reads it) — this exact "
+        "mutation would therefore NOT be caught if the shared-cache fix were reverted to the old "
+        "always-own-prefill behavior, proving the TC-7 oracle above is load-bearing, not a rubber stamp"
+    )
+
+
+# ====================================================================================================
+# AUDIT B1 — the deferred release must never leak the ~1.13 GB shared cache onto a retained JobProgress
+# ====================================================================================================
+def test_shared_cache_released_even_when_finalize_hook_never_runs(snapshot_dates_engine, monkeypatch):
+    """iter-37 AUDIT (B1): `_do_backfill` no longer releases its shared `_BarCache` on the SUCCESS path —
+    it stashes it on `prog._shared_bar_cache` and defers the release to `_refresh_ingest_aggregates`'s own
+    `finally`. `_JOBS` never evicts a finished job, so if that hook is ever skipped after a SUCCESSFUL
+    backfill (a `_finalize_checkpoint`/`record_stage` write or `Session(eng)` faulting between the two —
+    e.g. a `MemoryError` under real pressure), the reference would pin the whole-table cache for the LIFE
+    of the process. Simulates that exact window by making the finalize hook raise before it can release,
+    and asserts the job runner still clears the reference (and that the failure stays non-fatal — the job
+    is still `ok`, matching the hook's pre-existing log-and-continue contract)."""
+    engine, cfg, dates = snapshot_dates_engine
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(data_manager.ScannerRun.asof_date)).all())
+    # a fresh (not-yet-snapshotted) date => >= 1 in-range target => `_do_backfill` really builds + stashes
+    # the shared cache (a 0-target backfill returns before the prefill and stashes nothing).
+    fresh_date = next(d for d in reversed(trading) if d not in snapshotted)
+
+    def _boom(*_args, **_kwargs):
+        raise MemoryError("simulated pressure between a successful backfill and the finalize hook")
+
+    monkeypatch.setattr(data_manager, "_refresh_ingest_aggregates", _boom)
+
+    job = create_job("backfill", fresh_date, fresh_date)
+    summary = run_data_job(job.job_id, config=cfg, engine=engine)
+
+    assert summary["snapshots_created"] == 1, "sanity: the backfill itself must have really done work"
+    assert summary["status"] == "ok", (
+        "a finalize-hook failure must stay non-fatal (pre-existing log-and-continue contract)"
+    )
+    assert job._shared_bar_cache is None, (
+        "the shared whole-table `_BarCache` is STILL referenced by the finished job's retained "
+        "`JobProgress` — `_JOBS` never evicts it, so this pins ~1.13 GB for the life of the process "
+        "(AG-8/J-07 regression: the release must happen on EVERY exit path, not only when "
+        "`_refresh_ingest_aggregates` runs to completion)"
+    )
```
