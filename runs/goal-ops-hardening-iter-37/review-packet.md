# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 0.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/data_manager.py` (147 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index a8c67716..b63b8581 100644
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
... [diff_bound] apps/backend/app/engine/data_manager.py: 147 more diff lines omitted — Read the file for full detail
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 224 +++++++++++++++++++++
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   9 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   2 +
 5 files changed, 237 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
