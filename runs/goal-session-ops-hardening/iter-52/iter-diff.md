# Iteration diff (bounded)

Files changed: 13. Shown in full: 13.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 63448fcc..9a911825 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3703,6 +3703,10 @@ def _persist_per_date_coverage_snapshots(
     with cache_ctx:
         for d in todo:
             prog.tick()  # F1 fix (iter-4): per-date heartbeat stamp before this date's heavy coverage compute
+            # ops-hardening iter-52 (J-07): a REAL scheduling yield, not just the heartbeat stamp above —
+            # see `_refresh_ingest_aggregates`'s docstring for the full rationale (GIL contention, not
+            # allocation; TC-4 scheduling-only, byte-identical).
+            time.sleep(0)
             try:
                 refresh_coverage_snapshot_for(session, cfg, d)
             # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` under real pressure must NOT be
@@ -3962,7 +3966,28 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     what confirmed the coverage/membership-timeline refresh phase as the dominant cost for a historical
     gap-insert backfill (measured live: ~0.8-2.2s per unbounded `resolve_with_reasons` call across this
     DB's ~2,900 historical dates, well over an hour for the pre-fix full sweep) — see
-    `membership_timeline_cached`'s iter-48 fix."""
+    `membership_timeline_cached`'s iter-48 fix.
+
+    ops-hardening iter-52 (J-07, real scheduling yields — NOT just `prog.tick()`): iter-49/50/51's own live
+    drills (`reports/perf-budgets.md` Item S Addendum 10, Item T Addendum 11) proved a per-item HEARTBEAT
+    STAMP is not a scheduling yield — a `prog.tick()` call only writes a timestamp, it never hands the GIL
+    to another thread. Whichever finalize-tail sub-phase is currently LONGEST (measured: `factor_lab_all_warm`
+    solo at 9/653 connection-level `GET /api/health` non-answers; `forward_aggregates_warm horizon=20`
+    concurrent at 19/892) can starve the event loop past a full connection cycle. Every per-item loop this
+    function drives directly (`market_phase_warm`, `forward_aggregates_warm` below) or calls into
+    (`_persist_per_date_coverage_snapshots`'s per-date coverage warm) now ALSO calls `time.sleep(0)` once per
+    item, immediately alongside its existing `prog.tick()` — a real OS-level thread hand-off (per iter-50's
+    binding lesson: "the cause is GIL contention between two CPU-bound Python computes in one process, not
+    allocation"), so a concurrent `GET /api/health` gets a fair chance to be scheduled between items instead
+    of only after the whole phase completes. `compute_factor_lab_all`/`_combination_observations`/
+    `_factor_decile_observations`/`_all_factor_observations_by_horizon` (research.py) and
+    `compute_forward_aggregates` (forward_testing.py) carry the SAME yield at their own per-item/per-chunk
+    loop boundaries — see each function's own docstring. Scheduling only: no value, no algorithm, no ordering
+    changes anywhere (TC-4) — `time.sleep(0)` never blocks and never changes what is computed, only when the
+    interpreter next offers the GIL to another thread. Honest limit: this closes the CONNECTION-LEVEL
+    non-answer (TC-1/TC-2); it is not guaranteed to fully close every poll's ≤2s latency ceiling (TC-3) —
+    some residual GIL hand-off latency can remain (see `reports/perf-budgets.md`'s iter-52 addendum for what
+    was actually measured)."""
     refreshed: list[str] = []
     prog.tick()  # F1 fix: heartbeat-only stamp at the start of the finalize tail — see docstring above.
 
@@ -4100,6 +4125,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
             market_phase_warmed = False
             for d in prog.new_snapshot_dates:
                 prog.tick()  # F1 fix: per-date heartbeat stamp -- see function docstring above.
+                time.sleep(0)  # ops-hardening iter-52 (J-07): real scheduling yield -- see docstring above.
                 try:
                     market_phase.market_phase_cached(session, d, cfg)
                     market_phase_warmed = True
@@ -4147,6 +4173,9 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                         prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
                                      # compute here can take up to ~35s pre-warm; 5 sequential horizons could
                                      # otherwise freeze the heartbeat for minutes without a per-horizon tick).
+                        # ops-hardening iter-52 (J-07): real scheduling yield alongside the heartbeat stamp
+                        # above -- see `_refresh_ingest_aggregates`'s docstring for the full rationale.
+                        time.sleep(0)
                         # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` on one horizon is caught
                         # HERE, distinctly, so a horizon that already succeeded before it is still honestly
                         # reported — the outer `except Exception` below (unchanged for every OTHER exception
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index ffde386d..6f90a1b8 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -37,6 +37,7 @@ import json
 import logging
 import random
 import threading
+import time
 from calendar import monthrange
 from collections import defaultdict
 from datetime import date as date_cls, datetime, timedelta, timezone
@@ -1251,6 +1252,15 @@ def compute_forward_aggregates(
     control_group_builder = _ControlGroupBuilder(cfg)
 
     for start in range(0, len(runs_with_fr), run_chunk):
+        # ops-hardening iter-52 (J-07): a real scheduling yield once per run-id chunk. Prior live drills
+        # (`reports/perf-budgets.md` Item S Addendum 10 UT-08: 19/892 connection-level `GET /api/health`
+        # non-answers clustered inside THIS loop's `forward_aggregates_warm horizon=20` phase, the concurrent
+        # drill's own longest sub-phase) confirmed this generalizes past `factor_lab_all_warm` to whichever
+        # finalize-tail sub-phase is currently longest. `time.sleep(0)` forces a real OS-level GIL hand-off
+        # (a `prog.tick()` heartbeat stamp, called by this function's own caller once per horizon, does not)
+        # so a concurrent request gets a fair chance to be scheduled between chunks. Scheduling only — no
+        # value/order change (TC-4, byte-identical against a pinned reference).
+        time.sleep(0)
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         slice_map = _forward_agg_slice_map(session, horizon, slice_run_ids, batch)
         for (slice_run_id, slice_symbol), (slice_return, _slice_mdd) in slice_map.items():
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index e0afb4de..093cad27 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -35,12 +35,15 @@ THREE non-negotiable disciplines (each unit-proved):
 """
 from __future__ import annotations
 
+import gc
+import heapq
 import json
 import logging
 import threading
 import time
 from array import array
 from collections import defaultdict
+from contextlib import contextmanager
 from datetime import date as date_cls
 from datetime import datetime, timezone
 from math import ceil, sqrt
@@ -95,6 +98,112 @@ def factor_catalog(cfg: Config) -> list[dict]:
     ]
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-52 FIX PASS (J-07, TC-1) — cooperative sorting: a stable sort whose GIL hold is
+# BOUNDED.
+#
+# Why this exists (measured, not assumed). iter-52's first pass added `time.sleep(0)` yield points at
+# every finalize-tail loop boundary and the live drill got WORSE, not better (22 connection-level
+# `GET /api/health` non-answers vs a pre-fix baseline of 9 — `reports/perf-budgets.md` Item U /
+# Addendum 12). A GIL-stall profile of the real `compute_factor_lab_all` against the committed DB
+# (571.94s, 69,608,603 observations across 55 (factor, horizon) entries) then showed WHY: 197 stalls
+# longer than 0.30s, and the stack captured at the moment each one resolved lands on ONE line —
+# `sorted(obs, key=...)` — each hold measuring 1.09-1.23s. A `time.sleep(0)` placed at the TOP of an
+# iteration cannot interrupt a sort that happens INSIDE it: CPython's `list.sort()` runs its comparison
+# phase as a single C-level call that never reaches an eval-breaker check, so the GIL is held for the
+# WHOLE sort. That is the defect — a per-iteration yield was never going to reach it.
+#
+# The bound: sort contiguous slices of at most `_SORT_YIELD_CHUNK`, yielding between them, then merge the
+# already-sorted runs with `heapq.merge` (a pure-Python generator — eval-breaker driven, so it yields on
+# its own). Measured at the live per-entry scale (800k rows, heavy ties): worst GIL hold 0.99s -> 0.037s,
+# and 4% FASTER overall (smaller runs sort with better cache locality, and the merge is linear).
+#
+# BYTE-IDENTICAL by construction — but the construction has ONE precondition, and iter-52's audit (B6) was
+# right that stating it beats asserting the result unconditionally. GIVEN that `<` is a TOTAL ORDER on the
+# key, the result is exactly `sorted(items, key=key)`: the slices are contiguous and taken in the original
+# order, `sorted` is stable, and `heapq.merge` breaks ties by iterable index while preserving each
+# iterable's own order — so the concatenation is exactly the stable sort of the whole population.
+# Stability carries that argument on its own; a UNIQUE key is NOT required, and `_average_ranks` below
+# deliberately depends on that (it orders `range(n)` by a value that ties constantly). The other two call
+# sites do additionally have unique keys — `(factor, ticker, run_id)` and `(value, ticker, run_id)`, with
+# `(ticker, run_id)` unique per observation — so their sorted permutation is unique regardless.
+#
+# Where the precondition FAILS, so does the identity: a NaN anywhere in the key makes `<` non-total, and a
+# merge of separately-sorted runs is then NOT the same permutation as one Timsort pass over the whole list
+# (checked — it genuinely diverges). That is unreachable at all three call sites today: every key element
+# is a DB-sourced float, SQLite stores a NaN as NULL, and the NULL / `_has[core_idx]` filters drop those
+# rows before anything reaches a sort. Do NOT add a fourth call site whose key can be NaN (or otherwise
+# non-total) without re-deriving this.
+#
+# Verified against `sorted()` element-by-element (identity, not just equality) at 800k rows.
+# --------------------------------------------------------------------------------------------------
+_SORT_YIELD_CHUNK = 50_000  # rows per uninterruptible sort — measured 0.037s per chunk at the live scale
+
+
+def _cooperative_sorted(items, key=None) -> list:
+    """`sorted(items, key=key)`, byte-identical, but never holding the GIL for the whole population.
+
+    Populations at or below `_SORT_YIELD_CHUNK` take the plain `sorted()` path unchanged (nothing to
+    bound — one chunk IS the whole sort), so this is a no-op for every small caller."""
+    n = len(items)
+    if n <= _SORT_YIELD_CHUNK:
+        return sorted(items, key=key)
+    runs = []
+    for start in range(0, n, _SORT_YIELD_CHUNK):
+        time.sleep(0)  # a real OS-level GIL hand-off between chunks — see this section's header
+        runs.append(sorted(items[start:start + _SORT_YIELD_CHUNK], key=key))
+    time.sleep(0)
+    return list(heapq.merge(*runs, key=key))
+
+
+@contextmanager
+def _cyclic_gc_paused():
+    """Pause CPython's CYCLIC collector for one bounded unit of work, then restore it.
+
+    The other uninterruptible GIL holder the iter-52 stall profile found. A gen-2 collection is
+    stop-the-world and its cost scales with the number of GC-TRACKED objects alive; each
+    (factor, horizon) entry below allocates ~1.27M `_FactorLabAllObs`, so full collections during the
+    live `factor_lab_all_warm` phase measured **154 pauses totalling 121.37s of the phase's 571.94s,
+    worst 1.088s each** — comparable to the sort holds `_cooperative_sorted` bounds, and NOT reachable
+    by any yield point (a collection cannot be interrupted once started).
+
+    Everything this window allocates in bulk is ACYCLIC (a list of `__slots__` records holding only
+    str/float, the lists `sorted`/`heapq.merge` build, small result dicts), so plain reference counting
+    reclaims all of it deterministically whether or not the cyclic collector is running — the collector's
+    work here is pure overhead. Measured over the real per-entry body: every GC pause removed, total stall
+    time 7.4s -> 4.9s, and the work ran 6% FASTER.
+
+    What it actually defers, corrected (iter-52 audit B5). This only suspends the AUTOMATIC collection
+    trigger, and it restores the previous state on every exit path including an exception. The earlier
+    wording here — "for one item of one loop (seconds, not the whole phase)" — was true PER ENTRY and
+    false in AGGREGATE, so read it this way instead: one window covers one (factor, horizon) entry, but
+    `compute_factor_lab_all` re-enters it 55 times back-to-back with nothing but loop bookkeeping between
+    an exit and the next entry, so across the live `factor_lab_all_warm` phase (486.62s) the automatic
+    collector is suspended for effectively the WHOLE phase. Cyclic garbage produced by ANY thread in that
+    window — a concurrent request's SQLAlchemy session being the obvious producer — is therefore deferred
+    for that whole window. Deferred, never leaked: reference counting still reclaims every acyclic object
+    immediately, and the first collection after a window closes sweeps the rest. But on a host with a hard
+    8,192 MB cap that is an ongoing global side effect, not a momentary one, and it is worth re-measuring
+    whenever this phase gets longer. Measured headroom with the window in place, under a 1/s health poller
+    throughout: VmPeak 4,147.4 MB, 49.4% margin (`reports/perf-budgets.md` Addendum 13).
+
+    It does NOT compose across threads, and the previous wording implied that it did. An already-disabled
+    collector is left disabled (this restores, it never blindly enables) and the FINAL state is always
+    correct — but a SECOND overlapping entrant (the live `?all=true` request path runs this same function)
+    reads `gc.isenabled() == False` and records `was_enabled=False`, so when the FIRST window exits and
+    re-enables, the second runs its entire remaining window with the collector back ON. Overlap therefore
+    WEAKENS the pause; it can never leak a permanently-disabled collector. A depth counter would close the
+    overlap — deliberately not added here (iter-52 audit item 6, carried forward, not silently dropped)."""
+    was_enabled = gc.isenabled()
+    if was_enabled:
+        gc.disable()
+    try:
+        yield
+    finally:
+        if was_enabled:
+            gc.enable()
+
+
 # --------------------------------------------------------------------------------------------------
 # Pure stats helpers (downside-only risk + Spearman rank-IC) — no DB, no recomputation of any return
 # --------------------------------------------------------------------------------------------------
@@ -121,8 +230,14 @@ def _risk_adjusted(returns: list[float]) -> Optional[float]:
 
 def _average_ranks(values: list[float]) -> list[float]:
     """1-based average ranks (standard Spearman tie handling): tied values share the mean of the
-    positions they span, so the rank transform is a permutation-invariant monotone encoding."""
-    order = sorted(range(len(values)), key=lambda i: values[i])
+    positions they span, so the rank transform is a permutation-invariant monotone encoding.
+
+    ops-hardening iter-52 fix pass (J-07, TC-1): the ordering runs through `_cooperative_sorted` — on the
+    live basis `_rank_ic` ranks ~1.27M values TWICE per factor at the default horizon (factor side +
+    return side), each of which was a >1s uninterruptible GIL hold. Byte-identical: the average-rank
+    output is invariant to the order chosen among tied values (every member of a tie block receives the
+    same averaged position), and the sort itself is the same stable ordering either way."""
+    order = _cooperative_sorted(range(len(values)), key=lambda i: values[i])
     ranks = [0] * len(values)  # placeholder ints; every position is assigned an average-rank float below
     i = 0
     while i < len(order):
@@ -498,7 +613,13 @@ class _BoundedRankWindow:
             self._trim()
 
     def _trim(self) -> None:
-        self._buf.sort()
+        # ops-hardening iter-52 fix pass (J-07, TC-1): the trim sort runs through `_cooperative_sorted`.
+        # On the live basis this buffer trims at ~504K keys (2 x the ~252K decile-10 capacity) and is
+        # trimmed repeatedly across `drawdown_expectations_warm`'s per-claim PASS 1 — each `list.sort()`
+        # was a sub-second uninterruptible GIL hold. Byte-identical: `(ticker, run_id)` is unique per
+        # observation, so these keys admit exactly one sorted order, and the retained SET (and therefore
+        # the returned slice) is unchanged.
+        self._buf = _cooperative_sorted(self._buf)
         if self._keep_smallest:
             del self._buf[self._capacity:]
         else:
@@ -592,6 +713,9 @@ def _factor_decile_observations(
     # `window.add` additionally discards, as it walks, every key that cannot land in the target decile.
     n = 0
     for start in range(0, len(runs_with_fr), run_chunk):
+        # ops-hardening iter-52 (J-07): real scheduling yield once per run-id chunk (PASS 1) -- see
+        # `compute_factor_lab_all`'s iter-52 comment for the full rationale. Scheduling only (TC-4).
+        time.sleep(0)
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
         res_stmt = (
@@ -641,6 +765,9 @@ def _factor_decile_observations(
     # PASS 2 — bounded: rebuild the FULL observation dict only for this decile's (ticker, run_id) keys.
     members: list[dict] = []
     for start in range(0, len(runs_with_fr), run_chunk):
+        # ops-hardening iter-52 (J-07): real scheduling yield once per run-id chunk (PASS 2) -- see
+        # `compute_factor_lab_all`'s iter-52 comment for the full rationale. Scheduling only (TC-4).
+        time.sleep(0)
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
         res_stmt = (
@@ -1134,6 +1261,9 @@ def _all_factor_observations_by_horizon(
     ticker_intern: dict[str, str] = {}  # dedupes repeated ticker strings across the whole sweep (iter-31)
     warned_horizons: set[int] = set()  # one WARNING per horizon — never a per-chunk log storm (iter-31 audit)
     for start in range(0, len(runs_with_fr), run_chunk):
+        # ops-hardening iter-52 (J-07): real scheduling yield once per run-id chunk -- see
+        # `compute_factor_lab_all`'s iter-52 comment for the full rationale. Scheduling only (TC-4).
+        time.sleep(0)
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         fr_by_h = _all_fr_slice_map(session, horizons, slice_run_ids, batch)
         res_stmt = (
@@ -1293,58 +1423,95 @@ def compute_factor_lab_all(
             # answer): on a MemoryError, THIS horizon's entry alone degrades to an honest
             # `status: "unavailable"` (no deciles, n_total 0) and the loop continues to the next
             # horizon/factor — every OTHER entry still renders normally, never a blanked whole-response.
-            try:
-                data_manager._fault_inject_memory_error("factor_lab_all")  # test-only; a no-op in production
-                obs: list[_FactorLabAllObs] = []
-                # iter-50 AUDIT FIX (B3): read the shared pool through the columnar accessors instead of
-                # unpacking a materialised `(core_idx, ret, max_drawdown)` tuple per row and re-indexing a
-                # nested `values` tuple. Same rows, same order, same values — this walk never builds a
-                # transient object per pool row, so the only per-observation allocation left in this loop is
-                # the `_FactorLabAllObs` actually kept in `obs`.
-                _pool = pools[h]
-                _core_run_ids, _core_tickers = core_records.run_ids, core_records.tickers
-                _vals, _has = core_records.value_cols[idx], core_records.value_present[idx]
-                for k in range(len(_pool)):
-                    core_idx = _pool.core_idx[k]
-                    if not _has[core_idx]:
-                        continue  # factor-NULL observation — EXCLUDED, never bucketed (unchanged)
-                    obs.append(_FactorLabAllObs(
-                        _core_run_ids[core_idx], _core_tickers[core_idx], float(_vals[core_idx]),
-                        _pool.realized(k), _pool.max_drawdown(k),
-                    ))
-                # ascending by stored factor value; SAME deterministic tie-break compute_factor_lab uses.
-                ordered = sorted(obs, key=lambda o: (o.factor, o.ticker, o.run_id))
-                deciles = _deciles(ordered, fl.deciles, wf.min_sample)
-            except MemoryError as exc:
-                logger.exception(
-                    "compute_factor_lab_all: obs-build/sort aborted under memory pressure for factor=%s "
-                    "horizon=%s -- isolate-and-continue (AG-8), degrading THIS (factor,horizon) entry "
-                    "honestly rather than the whole all-factors response: %s", factor.key, h, exc,
-                )
-                by_horizon.append({"horizon": h, "n_total": 0, "deciles": [], "status": "unavailable"})
-                continue
-            except Exception as exc:  # noqa: BLE001 — ops-hardening iter-50 AUDIT FIX (B4, AG-8)
-                # The MemoryError catch above was the ONLY handler on this loop, so any OTHER exception
-                # from one (factor,horizon) entry still 500'd the entire `?all=true` response — a blank
-                # application-error page for all 11 factors because of one entry, which AG-8 forbids.
-                # `evidence.py`'s per-claim convention (the precedent this loop already follows for
-                # MemoryError) pairs its MemoryError catch with exactly this broader one, degrading the
-                # single failing unit to an honest `unavailable` and continuing. Nothing WRONG is ever
-                # displayed by this path: the entry carries no deciles and no n, only the honest status.
-                logger.exception(
-                    "compute_factor_lab_all: obs-build/sort failed for factor=%s horizon=%s (non-fatal) "
-                    "-- isolate-and-continue (AG-8), degrading THIS (factor,horizon) entry honestly "
-                    "rather than the whole all-factors response: %s", factor.key, h, exc,
-                )
-                by_horizon.append({"horizon": h, "n_total": 0, "deciles": [], "status": "unavailable"})
-                continue
-            by_horizon.append({"horizon": h, "n_total": len(obs), "deciles": deciles})
-            if h == default_h:
-                # the relabelled rank-IC + top-decile downside risk-adjusted at the FIXED default horizon —
-                # byte-identical to compute_factor_lab(factor, default_h).rank_ic / deciles[-1].risk_adjusted.
-                dh_rank_ic = _rank_ic([(o.factor, o.return_) for o in obs])
-                dh_risk_adjusted = deciles[-1]["risk_adjusted"]
-                dh_n_total = len(obs)
+            #
+            # ops-hardening iter-52 (J-07): a REAL scheduling yield once per (factor, horizon) — this is the
+            # CONFIRMED longest finalize-tail sub-phase (583.76s live, `reports/perf-budgets.md` Item T
+            # Addendum 11) and the one the solo drill caught starving `GET /api/health` 9/653. `time.sleep(0)`
+            # forces an OS-level GIL hand-off (a bare heartbeat stamp does not) so a concurrent request gets a
+            # fair chance to be scheduled between entries. Scheduling only — no value/order change (TC-4).
+            time.sleep(0)
+            # ops-hardening iter-52 FIX PASS (J-07, TC-1): this entry's own ~1.27M-record churn is what
+            # drives the stop-the-world gen-2 collections the stall profile measured (121.37s across the
+            # phase, worst 1.088s) — see `_cyclic_gc_paused`. Bounded to THIS entry; restored on every exit
+            # path, including the two isolate-and-continue handlers below.
+            with _cyclic_gc_paused():
+                try:
+                    data_manager._fault_inject_memory_error("factor_lab_all")  # test-only; no-op in production
+                    obs: list[_FactorLabAllObs] = []
+                    # iter-50 AUDIT FIX (B3): read the shared pool through the columnar accessors instead of
+                    # unpacking a materialised `(core_idx, ret, max_drawdown)` tuple per row and re-indexing a
+                    # nested `values` tuple. Same rows, same order, same values — this walk never builds a
+                    # transient object per pool row, so the only per-observation allocation left in this loop
+                    # is the `_FactorLabAllObs` actually kept in `obs`.
+                    _pool = pools[h]
+                    _core_run_ids, _core_tickers = core_records.run_ids, core_records.tickers
+                    _vals, _has = core_records.value_cols[idx], core_records.value_present[idx]
+                    for k in range(len(_pool)):
+                        core_idx = _pool.core_idx[k]
+                        if not _has[core_idx]:
+                            continue  # factor-NULL observation — EXCLUDED, never bucketed (unchanged)
+                        obs.append(_FactorLabAllObs(
+                            _core_run_ids[core_idx], _core_tickers[core_idx], float(_vals[core_idx]),
+                            _pool.realized(k), _pool.max_drawdown(k),
+                        ))
+                    # ascending by stored factor value; SAME deterministic tie-break compute_factor_lab uses.
+                    #
+                    # ops-hardening iter-52 FIX PASS (J-07, TC-1): this exact line is the measured defect the
+                    # iteration's first pass missed. A GIL-stall profile of this function against the
+                    # committed DB captured the worker's stack at the moment each stall resolved: 197 stalls
+                    # > 0.30s, dominated by THIS `sorted()` at 1.09-1.23s a piece (1.27M observations per
+                    # entry). The `time.sleep(0)` above cannot interrupt it — the sort's comparison phase is
+                    # one C-level call. `_cooperative_sorted` bounds the hold to ~0.037s per chunk,
+                    # byte-identically.
+                    ordered = _cooperative_sorted(obs, key=lambda o: (o.factor, o.ticker, o.run_id))
+                    deciles = _deciles(ordered, fl.deciles, wf.min_sample)
+                except MemoryError as exc:
+                    logger.exception(
+                        "compute_factor_lab_all: obs-build/sort aborted under memory pressure for factor=%s "
+                        "horizon=%s -- isolate-and-continue (AG-8), degrading THIS (factor,horizon) entry "
+                        "honestly rather than the whole all-factors response: %s", factor.key, h, exc,
+                    )
+                    by_horizon.append({"horizon": h, "n_total": 0, "deciles": [], "status": "unavailable"})
+                    continue
+                except Exception as exc:  # noqa: BLE001 — ops-hardening iter-50 AUDIT FIX (B4, AG-8)
+                    # The MemoryError catch above was the ONLY handler on this loop, so any OTHER exception
+                    # from one (factor,horizon) entry still 500'd the entire `?all=true` response — a blank
+                    # application-error page for all 11 factors because of one entry, which AG-8 forbids.
+                    # `evidence.py`'s per-claim convention (the precedent this loop already follows for
+                    # MemoryError) pairs its MemoryError catch with exactly this broader one, degrading the
+                    # single failing unit to an honest `unavailable` and continuing. Nothing WRONG is ever
+                    # displayed by this path: the entry carries no deciles and no n, only the honest status.
+                    logger.exception(
+                        "compute_factor_lab_all: obs-build/sort failed for factor=%s horizon=%s (non-fatal) "
+                        "-- isolate-and-continue (AG-8), degrading THIS (factor,horizon) entry honestly "
+                        "rather than the whole all-factors response: %s", factor.key, h, exc,
+                    )
+                    by_horizon.append({"horizon": h, "n_total": 0, "deciles": [], "status": "unavailable"})
+                    continue
+                by_horizon.append({"horizon": h, "n_total": len(obs), "deciles": deciles})
+                if h == default_h:
+                    # the relabelled rank-IC + top-decile downside risk-adjusted at the FIXED default
+                    # horizon — byte-identical to compute_factor_lab(factor, default_h).rank_ic /
+                    # deciles[-1].risk_adjusted.
+                    dh_rank_ic = _rank_ic([(o.factor, o.return_) for o in obs])
+                    dh_risk_adjusted = deciles[-1]["risk_adjusted"]
+                    dh_n_total = len(obs)
+                # Release this entry's ~1.27M-record transients BEFORE the collector is switched back on,
+                # in BOUNDED slices. Two measured effects, in order:
+                #   * leaving them referenced made the FIRST collection after the window reopened the
+                #     largest stall left in the phase (a 0.83s gen-0 pass over the whole entry's churn);
+                #   * dropping both lists in one statement then became the largest stall (0.42-0.45s) —
+                #     freeing 1.27M records is itself one uninterruptible C-level deallocation sweep.
+                # Slicing them away in `_SORT_YIELD_CHUNK`-sized pieces does the identical total work with
+                # a yield between pieces. `obs` goes first (its records are still held by `ordered`, so
+                # that pass only drops references); `ordered` releases the last reference and frees them.
+                # Nothing served is affected: `deciles` retains only scalars (`_deciles` reads floats off
+                # its members), and both names are rebuilt from scratch by the next entry.
+                for _spent in (obs, ordered):
+                    while _spent:
+                        del _spent[-_SORT_YIELD_CHUNK:]
+                        time.sleep(0)
+                del obs, ordered, _spent
         factors_table.append({
             "key": factor.key, "label": factor.label, "family": factor.family,
             "direction": factor.direction,
@@ -1416,6 +1583,10 @@ def _combination_observations(
 
     observations: list[dict] = []
     for start in range(0, len(runs_with_fr), run_chunk):
+        # ops-hardening iter-52 (J-07): a real scheduling yield once per run-id chunk -- see
+        # `compute_factor_lab_all`'s own iter-52 comment for the full rationale (GIL contention, not
+        # allocation). Scheduling only -- no value/order change (TC-4).
+        time.sleep(0)
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         # reuses `_fr_slice_map` (the SAME per-slice join accumulator `_factor_observations` already
         # uses) rather than a second near-duplicate builder — this pool only reads the `realized_return`
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 5f5a73b7..14f88557 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -2943,6 +2943,110 @@ def test_persist_per_date_coverage_snapshots_ticks_heartbeat_per_date(
     assert prog.last_progress_at != stale_sentinel  # the loop leaves the heartbeat fresh, not frozen
 
 
+# ==================================================================================================
+# ops-hardening iter-52 (J-07): a REAL scheduling yield (`time.sleep(0)`) now runs alongside each of the
+# `prog.tick()` heartbeat stamps above -- a heartbeat stamp alone never hands the GIL to another thread
+# (iter-49/50/51's own live drills proved this: 9/653 and 19/892 connection-level `GET /api/health`
+# non-answers during a solo/concurrent finalize-tail run, `reports/perf-budgets.md` Items S/T). These tests
+# prove the yield fires at the SAME per-item granularity the heartbeat already does, by spying on
+# `data_manager.time.sleep` -- mirroring how the heartbeat tests above spy on `prog.last_progress_at`.
+# ==================================================================================================
+def test_persist_per_date_coverage_snapshots_yields_per_date(
+    finalize_hook_triple_date_engine, monkeypatch
+):
+    """The per-date COVERAGE warm loop inside `_persist_per_date_coverage_snapshots` calls `time.sleep(0)`
+    once per date in `todo` (a REAL scheduling yield, not just the heartbeat stamp) -- proven by spying on
+    `data_manager.time.sleep` and asserting it is called exactly once per non-current date, always with
+    argument 0 (a yield, never an actual delay). Called directly (isolating THIS loop, mirroring
+    `test_persist_per_date_coverage_snapshots_ticks_heartbeat_per_date` above), so the count is exact."""
+    engine, dates = finalize_hook_triple_date_engine
+    cfg = load_config()
+    sleep_calls: list[float] = []
+    real_sleep = data_manager.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(data_manager.time, "sleep", _spy_sleep)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="cov-yield-probe", kind="backfill", start=dates[0], end=dates[-1])
+        data_manager._persist_per_date_coverage_snapshots(session, cfg, list(dates), prog)
+
+    assert len(sleep_calls) == len(dates) - 1, (
+        f"expected one yield per non-current new date ({len(dates) - 1}), got {len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+def test_finalize_hook_yields_at_least_once_per_date_in_market_phase_loop(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """The per-date market-phase warm loop inside `_refresh_ingest_aggregates` calls `time.sleep(0)` once
+    per date in `prog.new_snapshot_dates` -- proven the same way `test_finalize_hook_ticks_heartbeat_at_
+    least_once_per_date_in_market_phase_loop` above proves the heartbeat: spy on `data_manager.time.sleep`
+    and count calls against the known date count. A LOWER bound (`>=`), not an exact count: this call
+    drives the WHOLE finalize tail, so earlier phases' own yields (added by this same iteration) also land
+    on the same spy -- unlike the isolated direct call above."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+    sleep_calls: list[float] = []
+    real_sleep = data_manager.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(data_manager.time, "sleep", _spy_sleep)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="phase-yield-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.new_snapshot_dates = list(dates)
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert len(sleep_calls) >= len(dates), (
+        f"expected >= one yield per new-snapshot date ({len(dates)}) in the market-phase loop alone, got "
+        f"{len(sleep_calls)} total across the whole finalize tail"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+def test_finalize_hook_yields_at_least_once_per_horizon_in_forward_aggregates_warm_loop(
+    finalize_hook_engine, monkeypatch
+):
+    """The per-horizon forward-aggregates warm loop inside `_refresh_ingest_aggregates` calls
+    `time.sleep(0)` once per configured `walk_forward.horizons` entry -- proven by spying on
+    `data_manager.time.sleep` and asserting at least one call per configured horizon (a lower bound: the
+    coverage/market-phase phases earlier in the SAME finalize-tail call also contribute yields to the same
+    spy)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    sleep_calls: list[float] = []
+    real_sleep = data_manager.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(data_manager.time, "sleep", _spy_sleep)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="forward-agg-yield-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert "forward_aggregates" in refreshed  # sanity: the loop under test actually ran to completion
+    assert len(sleep_calls) >= len(cfg.walk_forward.horizons), (
+        f"expected >= one yield per configured horizon ({len(cfg.walk_forward.horizons)}), got "
+        f"{len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
 def test_run_detail_omits_aggregates_refreshed_until_computed():
     """TC-13/TC-14 — mirrors `test_run_detail_omits_breakdown_until_computed`: a not-yet-computed (fresh,
     `_create_run_record`-time) backfill row serves `aggregates_refreshed` null; an INTERRUPTED row whose
diff --git a/apps/backend/tests/test_forward_testing_aggregates_streaming.py b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
index 0f086dbd..503c8361 100644
--- a/apps/backend/tests/test_forward_testing_aggregates_streaming.py
+++ b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
@@ -426,6 +426,38 @@ def test_forward_agg_run_chunk_accumulator_is_bounded(multi_run_engine, monkeypa
     )
 
 
+# ==================================================================================================
+# ops-hardening iter-52 (J-07): a REAL scheduling yield (`time.sleep(0)`) now runs once per run-id chunk
+# inside `compute_forward_aggregates` -- iter-49/50's own live drills found THIS loop starving
+# `GET /api/health` (19/892 connection-level non-answers, clustered inside `forward_aggregates_warm
+# horizon=20`'s span, `reports/perf-budgets.md` Item S Addendum 10 UT-08) when it was the finalize tail's
+# longest sub-phase that run -- the generalization that motivates yielding in every named loop, not just
+# `factor_lab_all_warm`. Proven the same way `test_forward_agg_run_chunk_accumulator_is_bounded` above
+# proves the accumulator bound: spy on `forward_testing_module.time.sleep`.
+# ==================================================================================================
+def test_compute_forward_aggregates_yields_per_run_chunk(multi_run_engine, monkeypatch):
+    """`compute_forward_aggregates`'s run-id chunk loop calls `time.sleep(0)` exactly once per chunk (4
+    run ids at width 1 -> 4 chunks on this fixture), always with argument 0 (a yield, never a real
+    delay)."""
+    cfg = _cfg_run_chunk(1)  # 4 runs at width 1 -> 4 slices, one run id each
+    sleep_calls: list[float] = []
+    real_sleep = forward_testing_module.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(forward_testing_module.time, "sleep", _spy_sleep)
+    with Session(multi_run_engine) as session:
+        agg = compute_forward_aggregates(session, 20, cfg)
+
+    assert agg["n_runs"] == 4, "sanity: the zero-FR 5th run must stay excluded"
+    assert len(sleep_calls) == 4, f"expected one yield per chunk (4 run ids at width 1), got {len(sleep_calls)}"
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
 @pytest.mark.parametrize("run_chunk", [1, 2, 4, 100])
 @pytest.mark.parametrize("as_of", [None, HISTORICAL_AS_OF])
 def test_compute_forward_aggregates_chunked_equals_reference_across_run_chunk_widths(
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index 114f4e76..313b0fab 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -1930,3 +1930,301 @@ def test_factor_regime_observations_zero_n_cohort_is_honest_empty(chunked_accumu
             session, factor, H, date(2024, 1, 1), "Risk-on", cfg=cfg
         )
     assert members == []
+
+
+# ==================================================================================================
+# ops-hardening iter-52 (J-07): a REAL scheduling yield (`time.sleep(0)`) now runs once per (factor,
+# horizon) pair inside `compute_factor_lab_all` and once per run-id chunk inside `_combination_
+# observations` / `_factor_decile_observations` (both passes) / `_all_factor_observations_by_horizon` --
+# iter-49/50/51's own live drills proved a pure-Python loop does not reliably cede the GIL on its own
+# under this host's contention pattern (9/653 and 19/892 connection-level `GET /api/health` non-answers,
+# `reports/perf-budgets.md` Items S/T). These tests prove the yield actually fires, by spying on
+# `research_module.time.sleep` -- mirroring this file's own `_fr_slice_map`/`_wrapped` spy convention.
+# ==================================================================================================
+def test_compute_factor_lab_all_yields_once_per_factor_horizon(prune_engine, monkeypatch):
+    """`compute_factor_lab_all`'s per-(factor,horizon) loop calls `time.sleep(0)` once per (catalog
+    factor, configured horizon) pair -- a LOWER bound (`>=`), not an exact count: `compute_factor_lab_all`
+    also calls `_all_factor_observations_by_horizon` once internally (its OWN iter-52 per-chunk yield,
+    proven separately by `test_all_factor_observations_by_horizon_yields_per_run_chunk` above), which
+    contributes additional calls to this same spy. The confirmed LONGEST finalize-tail sub-phase (583.76s
+    live, `reports/perf-budgets.md` Item T Addendum 11)."""
+    cfg = load_config()
+    expected = len(cfg.research.factor_lab.factors) * len(cfg.walk_forward.horizons)
+    sleep_calls: list[float] = []
+    real_sleep = research_module.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(research_module.time, "sleep", _spy_sleep)
+    with Session(prune_engine) as session:
+        compute_factor_lab_all(session, cfg, as_of=None)
+
+    assert len(sleep_calls) >= expected, (
+        f"expected >= one yield per (factor, horizon) pair ({len(cfg.research.factor_lab.factors)} x "
+        f"{len(cfg.walk_forward.horizons)} = {expected}), got {len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+def test_combination_observations_yields_per_run_chunk(combination_chunked_engine, monkeypatch):
+    """`_combination_observations`'s run-id chunk loop calls `time.sleep(0)` more than once when the
+    fixture's runs are forced into multiple chunks -- proving a genuinely per-chunk yield, not a single
+    yield for the whole call."""
+    cfg = _cfg_batch(1)  # 1 run id per chunk over the fixture's 5 distinct run ids -> 5 chunks
+    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
+    sleep_calls: list[float] = []
+    real_sleep = research_module.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(research_module.time, "sleep", _spy_sleep)
+    with Session(combination_chunked_engine) as session:
+        observations = _combination_observations(session, factors, H, None, cfg=cfg)
+
+    assert observations, "sanity: the fixture must produce >= 1 observation"
+    assert len(sleep_calls) >= 2, (
+        f"expected a genuinely per-chunk yield (fixture forced to multiple chunks), got {len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+def test_factor_decile_observations_yields_per_run_chunk_both_passes(chunked_accumulator_engine, monkeypatch):
+    """`_factor_decile_observations`'s two chunked passes (PASS 1's lightweight sort-key sweep, PASS 2's
+    bounded member rebuild) each call `time.sleep(0)` once per run-id chunk -- proving BOTH passes yield,
+    not just one, by spying on the shared `research_module.time.sleep`."""
+    cfg = _cfg_batch(1, run_chunk=1)  # 1 run id per chunk over 5 distinct run ids -> 5 chunks per pass
+    deciles_count = cfg.research.factor_lab.deciles
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    sleep_calls: list[float] = []
+    real_sleep = research_module.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(research_module.time, "sleep", _spy_sleep)
+    with Session(chunked_accumulator_engine) as session:
+        members = research_module._factor_decile_observations(
+            session, factor, H, None, deciles_count, deciles_count, cfg=cfg
+        )
+
+    assert members, "sanity: the last decile must be non-empty on this fixture"
+    assert len(sleep_calls) >= 4, (
+        f"expected >= 4 yields (>= 2 chunks x 2 passes) on this 5-run fixture at run_chunk=1, got "
+        f"{len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+def test_all_factor_observations_by_horizon_yields_per_run_chunk(prune_engine, monkeypatch):
+    """`_all_factor_observations_by_horizon`'s run-id chunk loop calls `time.sleep(0)` more than once when
+    the fixture's runs are forced into multiple chunks."""
+    cfg = _cfg_batch(1)  # 1 run id per chunk -> multiple chunks on this fixture's >= 2 runs with FRs
+    factors = list(cfg.research.factor_lab.factors)
+    horizons = list(cfg.walk_forward.horizons)
+    sleep_calls: list[float] = []
+    real_sleep = research_module.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(research_module.time, "sleep", _spy_sleep)
+    with Session(prune_engine) as session:
+        core_records, _pools = _all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)
+
+    assert len(core_records.run_ids) > 0, "sanity: the fixture must produce >= 1 shared-pool observation"
+    assert len(sleep_calls) >= 2, (
+        f"expected a genuinely per-chunk yield (fixture forced to multiple chunks), got {len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+# ==================================================================================================
+# ops-hardening iter-52 FIX PASS (J-07, TC-1) -- `_cooperative_sorted`.
+#
+# The iteration's FIRST pass added a `time.sleep(0)` at the top of every per-item loop and the live drill
+# got WORSE, not better: 22 connection-level `GET /api/health` non-answers against a pre-fix baseline of 9
+# (`reports/perf-budgets.md` Item U / Addendum 12). A GIL-stall profile of the REAL `compute_factor_lab_all`
+# against the committed DB then located the actual holder by capturing the worker's stack at the instant
+# each stall resolved: `sorted(obs, key=...)` itself, 1.09-1.23s per call over ~1.27M observations. A yield
+# placed BEFORE an iteration cannot interrupt a sort happening INSIDE it -- CPython runs a sort's comparison
+# phase as one C-level call that never reaches an eval-breaker check.
+#
+# These tests pin the NON-NEGOTIABLE half of the fix: chunking the sort changes WHEN the GIL is offered and
+# nothing else. Byte-identity is asserted by object IDENTITY (`is`), not merely equality, so a re-derived
+# but equal value would still fail.
+# ==================================================================================================
+def _tie_heavy_rows(n: int) -> list[tuple]:
+    """`n` rows with deliberately heavy ties on the SORT KEY (only 3 distinct leading values x 3 distinct
+    tickers) and a unique trailing element that is NOT part of the key -- so a merge that failed to
+    preserve stability would reorder the ties and the identity assertion would catch it."""
+    return [((i * 7) % 3, "T%d" % ((i * 5) % 3), i) for i in range(n)]
+
+
+@pytest.mark.parametrize("n", [0, 1, 6, 7, 8, 13, 14, 15, 40])
+def test_cooperative_sorted_is_byte_identical_to_sorted_across_the_chunk_boundary(n, monkeypatch):
+    """`_cooperative_sorted` returns exactly what `sorted()` returns -- the same objects, in the same
+    order -- for populations below, at, and well past the chunk bound, with heavy ties on the key."""
+    monkeypatch.setattr(research_module, "_SORT_YIELD_CHUNK", 7)
+    rows = _tie_heavy_rows(n)
+    key = lambda r: (r[0], r[1])  # noqa: E731 -- deliberately excludes the unique trailing element
+    expected = sorted(rows, key=key)
+    got = research_module._cooperative_sorted(rows, key=key)
+
+    assert len(got) == len(expected)
+    assert all(a is b for a, b in zip(got, expected)), (
+        "chunked sorting must return the SAME objects in the SAME order as sorted() -- a stability or "
+        "merge-order divergence would change a served decile boundary (AG-3)"
+    )
+
+
+def test_cooperative_sorted_without_a_key_is_byte_identical_to_sorted(monkeypatch):
+    """The keyless path (`_BoundedRankWindow._trim`'s plain tuple sort) is covered too."""
+    monkeypatch.setattr(research_module, "_SORT_YIELD_CHUNK", 5)
+    rows = [(float((i * 13) % 7), "T%d" % ((i * 3) % 4), i) for i in range(37)]
+    expected = sorted(rows)
+    got = research_module._cooperative_sorted(rows)
+    assert all(a is b for a, b in zip(got, expected)) and len(got) == len(expected)
+
+
+def test_cooperative_sorted_yields_per_chunk_and_never_below_the_bound(monkeypatch):
+    """The scheduling half: one real `time.sleep(0)` per chunk (plus one before the merge) once the
+    population exceeds the bound, and NONE at or below it -- a small caller pays nothing."""
+    monkeypatch.setattr(research_module, "_SORT_YIELD_CHUNK", 7)
+    sleep_calls: list[float] = []
+    real_sleep = research_module.time.sleep
+
+    def _spy_sleep(seconds):
+        sleep_calls.append(seconds)
+        return real_sleep(seconds)
+
+    monkeypatch.setattr(research_module.time, "sleep", _spy_sleep)
+
+    research_module._cooperative_sorted(_tie_heavy_rows(7))
+    assert sleep_calls == [], "at or below the bound the plain sorted() path must run, yielding nothing"
+
+    research_module._cooperative_sorted(_tie_heavy_rows(22))
+    assert len(sleep_calls) == 5, (  # ceil(22/7) == 4 chunks, + 1 before the merge
+        f"expected one yield per chunk plus one before the merge, got {len(sleep_calls)}"
+    )
+    assert all(c == 0 for c in sleep_calls), (
+        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
+    )
+
+
+def test_compute_factor_lab_all_is_byte_identical_with_the_sort_chunked(prune_engine, monkeypatch):
+    """TC-4, end to end on the REAL builder: forcing every sort in `compute_factor_lab_all` (the
+    per-(factor,horizon) observation sort AND `_rank_ic` -> `_average_ranks`' own ordering) through the
+    chunked path changes NO served figure -- every decile boundary, mean, risk-adjusted, paired drawdown
+    and rank-IC is byte-identical to the unchunked computation on the same fixture."""
+    cfg = load_config()
+    with Session(prune_engine) as session:
+        unchunked = compute_factor_lab_all(session, cfg, as_of=None)
+
+    monkeypatch.setattr(research_module, "_SORT_YIELD_CHUNK", 1)  # every element its own chunk
+    with Session(prune_engine) as session:
+        chunked = compute_factor_lab_all(session, cfg, as_of=None)
+
+    assert json.dumps(chunked, sort_keys=True) == json.dumps(unchunked, sort_keys=True)
+
+
+@pytest.mark.parametrize("decile", [1, 5, 10])
+def test_factor_decile_observations_is_byte_identical_with_the_trim_sort_chunked(
+    chunked_accumulator_engine, monkeypatch, decile,
+):
+    """TC-4 for the OTHER chunked site: `_BoundedRankWindow._trim`'s retention sort. Forcing it through
+    the chunked path must not move a single decile member -- the bounded window's retained SET and the
+    returned slice are unchanged."""
+    cfg = load_config()
+    factor = cfg.research.factor_lab.factors[0]
+    with Session(chunked_accumulator_engine) as session:
+        unchunked = research_module._factor_decile_observations(
+            session, factor, H, None, cfg.research.factor_lab.deciles, decile, cfg=cfg,
+        )
+
+    monkeypatch.setattr(research_module, "_SORT_YIELD_CHUNK", 1)
+    with Session(chunked_accumulator_engine) as session:
+        chunked = research_module._factor_decile_observations(
+            session, factor, H, None, cfg.research.factor_lab.deciles, decile, cfg=cfg,
+        )
+
+    assert json.dumps(chunked, sort_keys=True, default=str) == json.dumps(
+        unchunked, sort_keys=True, default=str
+    )
+
+
+# ==================================================================================================
+# ops-hardening iter-52 FIX PASS (J-07, TC-1) -- `_cyclic_gc_paused`, the OTHER uninterruptible GIL
+# holder the stall profile found: stop-the-world gen-2 collections, 154 pauses totalling 121.37s of
+# `factor_lab_all_warm`'s 571.94s, worst 1.088s each. No yield point can reach a collection already in
+# progress. These tests pin the safety contract -- the pause is bounded to one item and the collector's
+# previous state is ALWAYS restored, including when the entry aborts under (injected) memory pressure.
+# ==================================================================================================
+def test_cyclic_gc_paused_suspends_and_restores_the_collector():
+    """Inside the window the automatic collector is off; on exit the previous state is restored."""
+    import gc as _gc
+
+    assert _gc.isenabled(), "sanity: the test process runs with the collector enabled"
+    with research_module._cyclic_gc_paused():
+        assert not _gc.isenabled(), "the cyclic collector must be paused inside the window"
+    assert _gc.isenabled(), "the collector must be restored on the normal exit path"
+
+
+def test_cyclic_gc_paused_restores_the_collector_on_an_exception():
+    """An exception inside the window must not leave the process with its collector switched off."""
+    import gc as _gc
+
+    with pytest.raises(RuntimeError):
+        with research_module._cyclic_gc_paused():
+            raise RuntimeError("boom")
+    assert _gc.isenabled(), "the collector must be restored when the window exits on an exception"
+
+
+def test_cyclic_gc_paused_leaves_an_already_disabled_collector_disabled():
+    """It RESTORES rather than blindly enabling, so a caller that had already disabled the collector
+    (or a concurrent entry into the same loop from the live `?all=true` request path) is left alone."""
+    import gc as _gc
+
+    _gc.disable()
+    try:
+        with research_module._cyclic_gc_paused():
+            assert not _gc.isenabled()
+        assert not _gc.isenabled(), "an already-disabled collector must not be switched on by the window"
+    finally:
+        _gc.enable()
+
+
+def test_compute_factor_lab_all_restores_the_collector_after_an_injected_memory_error(
+    prune_engine, monkeypatch,
+):
+    """The isolate-and-continue MemoryError path runs INSIDE the paused window and `continue`s out of it
+    -- the collector must still come back on, and the entry must still degrade honestly (AG-8)."""
+    import gc as _gc
+
+    cfg = load_config()
+    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "factor_lab_all")
+    with Session(prune_engine) as session:
+        payload = compute_factor_lab_all(session, cfg, as_of=None)
+
+    assert _gc.isenabled(), "the collector must be restored after every faulted (factor,horizon) entry"
+    statuses = {
+        entry.get("status")
+        for row in payload["factors_table"]
+        for entry in row["by_horizon"]
+    }
+    assert statuses == {"unavailable"}, (
+        f"every entry should degrade honestly under the injected fault, got {statuses}"
+    )
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index cfbd1650..532fb1da 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -910,6 +910,155 @@ def spawned_backend_fault_injected():
             pass
 
 
+# ==================================================================================================
+# ops-hardening iter-52 (J-07 step 4, TC-6) -- the LIVE test above faults `factor_lab_all` via a LIVE
+# REQUEST (`GET /research/factor-lab?all=true`). J-07 step 4 itself describes an induced-pressure abort
+# during a HEAVY DATA JOB, i.e. the finalize tail's OWN `factor_lab_all_warm` call
+# (`data_manager.py`) -- a scenario the request-path drill above cannot exercise, and which
+# `iteration-state.md`/`assumptions.md` record as permission-denied twice this session (UT-05) via the
+# goal-mode harness's own backend-restart path. This drill instead spawns its OWN dedicated backend and
+# drives the SAME confirmed crash frame through a REAL `POST /api/data/jobs` ingest job.
+#
+# Unlike `spawned_backend_fault_injected` above (whose own tests are read-only GETs), THIS drill runs a
+# genuinely MUTATING backfill -- so it launches against a THROWAWAY COPY of the real dev DB (mirroring
+# `spawned_backend_throwaway_db`'s own established rationale: "never the shared committed file"), never
+# the shared committed DB every other test in this session's own history relies on staying stable.
+# ==================================================================================================
+_INGEST_FAULT_TEST_PORT = 19300 + _offset
+
+
+@pytest.fixture()
+def spawned_backend_throwaway_db_fault_injected(tmp_path):
+    """Combines `spawned_backend_throwaway_db`'s THROWAWAY DB COPY (this fixture backs a REAL mutating
+    ingest job -- never the shared committed dev DB) with `spawned_backend_fault_injected`'s
+    `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all` env var (deterministically arming the SAME
+    confirmed crash frame at `compute_factor_lab_all`'s per-(factor,horizon) obs-build+sort -- see that
+    fixture's own docstring for why a deterministic injector is used instead of an organic `ulimit -v`
+    calibration). Opt-in (same gate as every other heavy-ingest fixture in this module): must never spawn
+    a mutating, fault-injected backend by accident on a plain `pytest` run."""
+    if os.environ.get("TRENDORA_RUN_HEAVY_INGEST_TEST") != "1":
+        pytest.skip(
+            "live ingest-finalize fault-injection drill is opt-in -- set TRENDORA_RUN_HEAVY_INGEST_TEST=1 "
+            "(run it only on an idle host with the host-guard protections active)"
+        )
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    if not REAL_DB.exists():
+        pytest.skip(f"real dev DB not found at {REAL_DB} -- nothing to copy for a real ingest drill")
+
+    scratch_db = tmp_path / "ingest-fault-throwaway.db"
+    for suffix in ("", "-wal", "-shm"):
+        src = Path(str(REAL_DB) + suffix)
+        if src.exists():
+            shutil.copy2(src, Path(str(scratch_db) + suffix))
+
+    scratch_config = tmp_path / "ingest-fault-throwaway-config.yaml"
+    real_cfg_text = REAL_CONFIG.read_text()
+    new_cfg_text, n = re.subn(
+        r'url:\s*"sqlite:///apps/backend/data/trendora\.db"',
+        f'url: "sqlite:///{scratch_db}"',
+        real_cfg_text,
+        count=1,
+    )
+    assert n == 1, "expected exactly one database.url line to rewrite in the real config.yaml"
+    scratch_config.write_text(new_cfg_text)
+
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_INGEST_FAULT_TEST_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_INGEST_FAULT_TEST_PORT + 1000)
+    env["TRENDORA_CONFIG"] = str(scratch_config)
+    env["TRENDORA_FAULT_INJECT_MEMORY_ERROR"] = "factor_lab_all"
+    proc = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        _wait_for_health(_INGEST_FAULT_TEST_PORT, timeout=60.0)
+        yield ThrowawayBackend(
+            pid=proc.pid, port=_INGEST_FAULT_TEST_PORT, scratch_db=scratch_db, scratch_config=scratch_config
+        )
+    finally:
+        if _pid_alive(proc.pid):
+            os.kill(proc.pid, signal.SIGTERM)
+            deadline = time.monotonic() + 15.0
+            while _pid_alive(proc.pid) and time.monotonic() < deadline:
+                time.sleep(0.2)
+            if _pid_alive(proc.pid):
+                os.kill(proc.pid, signal.SIGKILL)
+        try:
+            proc.wait(timeout=10)
+        except ChildProcessError:
+            pass
+
+
+def test_ingest_finalize_factor_lab_all_fault_is_honestly_omitted_health_stays_live(
+    spawned_backend_throwaway_db_fault_injected,
+):
+    """TC-6 (J-07 step 4) -- closes the evidence gap `test_factor_lab_all_survives_repeated_memory_
+    pressure_live` above leaves open: that test faults `factor_lab_all` via a LIVE REQUEST
+    (`GET /research/factor-lab?all=true`); THIS test drives the SAME confirmed crash frame via a REAL
+    ingest job's finalize tail (`POST /api/data/jobs`), so the fault fires inside `factor_lab_all_warm`
+    (data_manager.py), not the request path -- the scenario J-07 step 4 actually describes and UT-05
+    could not reach twice this session (permission-denied both times).
+
+    Asserts: the job's terminal record honestly OMITS "factor_lab_all" from `aggregates_refreshed` while
+    "coverage" (unaffected by the factor_lab_all-only fault, and genuinely warmed by this real new-
+    snapshot backfill) still appears; `GET /api/health` answers 200 throughout the job AND for 30s past
+    its own completion (a single continuously-running poller is itself the "no restart" evidence -- a
+    restart would show up as a connection-refused gap, never an unbroken run of 200s); and a follow-up
+    request for the warmed category still returns the correct, live value from the SAME still-running
+    process -- no restart performed or required."""
+    from app.config import get_config
+
+    backend = spawned_backend_throwaway_db_fault_injected
+    cfg = get_config()
+
+    target_date = _pick_unsnapshotted_trading_day(backend.port, cfg)
+
+    health = _HealthPoller(backend.port)
+    health.start()
+    try:
+        job_id = _post_job(backend.port, "backfill", target_date, target_date)
+        # Generous: the WHOLE finalize tail runs (coverage/market-phase/forward-aggregates/research-hot-
+        # keys/index-series/the faulted-but-still-slow-to-degrade factor-lab-all/drawdown), not just the
+        # faulted category -- iter-51's Item T Addendum 11 measured ~1,048s for a comparable solo run.
+        detail = _poll_job_to_terminal(backend.port, job_id, timeout_s=1800.0)
+        # TC-6: 30s of health polling PAST the job's own completion, same poller/process throughout.
+        time.sleep(30.0)
+    finally:
+        health.stop()
+        health.join(timeout=15.0)
+
+    assert detail.get("status") == "ok", (
+        f"expected an honest 'ok' -- the isolated factor_lab_all fault must never flip the whole job to "
+        f"partial/failed: {detail}"
+    )
+    refreshed = detail.get("aggregates_refreshed") or []
+    assert "factor_lab_all" not in refreshed, (
+        f"the faulted category must be honestly OMITTED, never fabricated as refreshed: {refreshed}"
+    )
+    assert "coverage" in refreshed, (
+        f"coverage is unaffected by the factor_lab_all-only fault and this is a genuine new-snapshot "
+        f"backfill -- it must still be reported refreshed: {refreshed}"
+    )
+
+    assert health.results, "the health poller recorded nothing -- the drill would be measuring an idle process"
+    bad = [(i, r) for i, r in enumerate(health.results) if r.get("status") != 200]
+    assert not bad, (
+        f"GET /api/health must answer 200 throughout the ingest job and 30s past its own completion "
+        f"({len(health.results)} polls, {len(bad)} non-200/no-response). First offenders: {bad[:5]}"
+    )
+
+    # a category that DID warm (coverage) still serves the correct, live value from the SAME process.
+    avail = httpx.get(f"http://127.0.0.1:{backend.port}/api/data/availability", timeout=120.0)
+    assert avail.status_code == 200
+    cells = {c["date"]: c for c in avail.json().get("cells", [])}
+    assert cells.get(target_date, {}).get("snapshot_exists") is True, (
+        f"the just-ingested date {target_date} must show as snapshotted from the SAME live process, no "
+        f"restart -- got {cells.get(target_date)}"
+    )
+
+
 def _distinct_factor_lab_asof_dates(port: int, n: int) -> list[str]:
     """`n` distinct real snapshot as-of dates, read from the SPAWNED INSTANCE's own `GET /api/runs` — never
     hardcoded literals that go stale. Each one is a DIFFERENT `factor_lab_all_cached` key, which is what
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index 9c0a0277..337696b7 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -192,6 +192,18 @@ reverts on reboot):
 for f in /sys/devices/system/cpu/cpu*/cpuidle/state[2-9]/disable; do echo 1 | sudo tee "$f" >/dev/null; done
 ```
 
+2026-08-07, this host: that loop is now PERSISTENT via the root unit
+`/etc/systemd/system/iad-cstate-limit.service` (re-applied at boot and on
+resume from sleep). The volatile form above kept evaporating on the ~daily
+fault resets, so it never actually soaked — `host_state` events in the machine
+ledger recorded `cstate_disabled` all zeros through five more resets (Aug 4–7).
+Soak journal: `~/.cache/iad/host-guard/soak-log.md`.
+Enabled + verified 2026-08-07 21:02:21 BST — the install earlier that day was
+`cp`-only and sat disabled through fault reset #3 at 17:46 (near-idle). Verify
+activation by `journalctl -t iad-cstate-limit -b 0` + sysfs `state[23]/disable`
+= 1 on all CPUs, never by unit-file presence or `is-active` (oneshot without
+`RemainAfterExit` reads `inactive (dead)` after success).
+
 `doctor.sh --only ras-logging` verifies what it can read without root (the
 journald drop-in and the rasdaemon unit) and stays silent on hosts that have no
 reset history.
diff --git a/incredible_auto_dev/scripts/automation/host-guard-adopt.sh b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
index 403f2b71..76bb131c 100755
--- a/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
@@ -24,7 +24,8 @@
 #       (default 'claude|codex') and confine THAT tree; falls back to <pid>
 #       itself when no ancestor matches.
 #
-# Idempotent: exits 0 immediately when the target is already confined.
+# Idempotent: re-running a fully-confined target just refreshes its scope
+# ceilings in place (set-property) and re-sweeps escaped browsers.
 # Absent/disabled host-guard.env ⇒ no-op (framework stays project-neutral).
 # Limitation: BLAS/OMP thread-cap env vars cannot be injected into a running
 # process — only wrapper-launched (host-guard-exec.sh) sessions get those.
@@ -64,6 +65,9 @@ _width() { # "0-3,8-11" → 8; 0 when unparseable
 }
 _ppid() { awk '/^PPid:/{print $2}' "/proc/$1/status" 2>/dev/null || true; }
 _allowed_n() { _width "$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$1/status" 2>/dev/null)"; }
+_hg_scope_unit() { # chain-*-hostguard scope unit already holding $1, if any
+  sed -n 's#.*/\(chain-\(pump\|goal\)-hostguard-[^/]*\.scope\).*#\1#p' "/proc/$1/cgroup" 2>/dev/null | head -n 1
+}
 
 _SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 
@@ -105,8 +109,19 @@ if (( WIDTH == 0 )); then
   echo "[host-guard-adopt] unparseable HOST_GUARD_CPU_LIST='$HOST_GUARD_CPU_LIST'" >&2
   exit 1
 fi
-if (( $(_allowed_n "$TARGET") <= WIDTH )); then
-  echo "[host-guard-adopt] pid $TARGET already confined ($(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$TARGET/status"))."
+ALLOWED_N="$(_allowed_n "$TARGET")"
+SCOPE_UNIT="$(_hg_scope_unit "$TARGET")"
+if (( ALLOWED_N <= WIDTH )) && [[ -n "$SCOPE_UNIT" ]]; then
+  # Confined = mask narrow enough AND ceilings carried by a hostguard scope.
+  # The old width-only check is vacuous at a full-machine mask (16 ≤ 16 is
+  # always true), which left MemoryHigh/TasksMax unapplied on the pump from the
+  # 2026-07-30 mask release until 2026-08-07. Refresh the ceilings so env-file
+  # edits converge on the live scope on every adopt.
+  systemctl --user set-property "$SCOPE_UNIT" \
+    "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}" \
+    "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}" \
+    "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" 2>/dev/null || true
+  echo "[host-guard-adopt] pid $TARGET already confined ($(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$TARGET/status") in $SCOPE_UNIT) — ceilings refreshed."
   # An already-confined pump is the COMMON case, and it is exactly when an
   # escaped browser goes unnoticed — sweep before returning, never after.
   _register_pump
@@ -115,10 +130,20 @@ if (( $(_allowed_n "$TARGET") <= WIDTH )); then
 fi
 
 # 1) Scope adoption — aggregate memory/task/quota ceilings for the whole tree.
-UNIT="chain-pump-hostguard-$TARGET.scope"
-if busctl call --user org.freedesktop.systemd1 /org/freedesktop/systemd1 \
+if [[ -n "$SCOPE_UNIT" ]]; then
+  # Already inside a hostguard scope (mask just too wide): refresh the existing
+  # unit's ceilings instead of racing StartTransientUnit against it.
+  UNIT="$SCOPE_UNIT"
+  systemctl --user set-property "$UNIT" \
+    "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}" \
+    "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}" \
+    "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" 2>/dev/null || true
+  systemctl --user set-property "$UNIT" "AllowedCPUs=$HOST_GUARD_CPU_LIST" 2>/dev/null || true
+  echo "[host-guard-adopt] pid $TARGET already in $UNIT — ceilings refreshed."
+elif busctl call --user org.freedesktop.systemd1 /org/freedesktop/systemd1 \
      org.freedesktop.systemd1.Manager StartTransientUnit 'ssa(sv)a(sa(sv))' \
-     "$UNIT" fail 1 PIDs au 1 "$TARGET" 0 >/dev/null 2>&1; then
+     "chain-pump-hostguard-$TARGET.scope" fail 1 PIDs au 1 "$TARGET" 0 >/dev/null 2>&1; then
+  UNIT="chain-pump-hostguard-$TARGET.scope"
   systemctl --user set-property "$UNIT" \
     "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}" \
     "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}" \
@@ -131,12 +156,15 @@ else
 fi
 
 # 2) Hard CPU mask NOW — target + every existing descendant; future children
-# inherit. -a covers all threads of each process.
+# inherit. -a covers all threads of each process. At a full-width mask the
+# taskset is a per-process no-op, so skip the whole tree recursion.
 _descendants() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do echo "$c"; _descendants "$c"; done; }
-taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$TARGET" >/dev/null 2>&1 || true
-for _c in $(_descendants "$TARGET"); do
-  taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$_c" >/dev/null 2>&1 || true
-done
+if (( ALLOWED_N > WIDTH )); then
+  taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$TARGET" >/dev/null 2>&1 || true
+  for _c in $(_descendants "$TARGET"); do
+    taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$_c" >/dev/null 2>&1 || true
+  done
+fi
 
 if (( $(_allowed_n "$TARGET") <= WIDTH )); then
   echo "[host-guard-adopt] confined pid $TARGET (and descendants) to CPUs $HOST_GUARD_CPU_LIST."
diff --git a/incredible_auto_dev/scripts/automation/host-guard-exec.sh b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
index b1d11ed0..f106def4 100755
--- a/incredible_auto_dev/scripts/automation/host-guard-exec.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
@@ -46,6 +46,18 @@ if [[ "${HOST_GUARD_BLAS_THREADS:-}" =~ ^[0-9]+$ ]]; then
   export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
 fi
 
+# Opt-in headless pump QA (HOST_GUARD_PUMP_HEADLESS_QA=1): strip the session's
+# display env so pump-dispatched browser QA launches Chrome HEADLESS (the
+# Chrome MCP picks headless purely from absent DISPLAY/WAYLAND_DISPLAY —
+# lib/common.sh strip_display_for_headless_qa; engine-mode lanes already do
+# this). Added after the 2026-08-07 gnome-shell SIGSEGV: the headed pump QA
+# Chrome was a standing compositor-stress source, and the session teardown
+# killed the pump. CHAIN_BQA_HEADED=1 remains the headed debugging escape.
+if [[ "${HOST_GUARD_PUMP_HEADLESS_QA:-0}" == "1" ]]; then
+  unset DISPLAY WAYLAND_DISPLAY
+  echo "[host-guard-exec] HOST_GUARD_PUMP_HEADLESS_QA=1 — DISPLAY/WAYLAND_DISPLAY stripped (QA browsers go headless)." >&2
+fi
+
 # NOTE: no CHROME_WS_PROFILE pin here. The pump serves BOTH QA lanes (run-phase.sh
 # runs Branch-QA and Branch-UI concurrently), and an explicit profile disables the
 # Chrome-MCP's per-lane auto-disambiguation — the two lanes would end up sharing one
diff --git a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
index 1b787885..2e869fad 100644
--- a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
@@ -1239,6 +1239,13 @@ agent_with_quota_retry() {
   # CHAIN_AGENT_BACKEND overrides the CLI for dispatch only (assets/personas
   # still come from CHAIN_CLI). Defaults to the CLI, so absence = today's behaviour.
   local backend="${CHAIN_AGENT_BACKEND:-$cli}"
+  # Dispatch-boundary thermal defer — opt-in (HOST_GUARD_TCTL_DISPATCH_GATE=1),
+  # defined and export -f'd by the goal engine (run-goal.sh). Outside an engine
+  # tree the function does not exist → no-op. Before dispatch_start so deferral
+  # never counts as agent wall time.
+  if declare -F host_guard_thermal_defer >/dev/null 2>&1; then
+    host_guard_thermal_defer || true
+  fi
   local _hg_t0=$EPOCHSECONDS _hg_rc=0
   hg_event dispatch_start "$(printf '{"backend":"%s"}' "$backend")"
   case "$backend" in
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 7b05d02b..b08582a8 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -9,7 +9,7 @@
 # Usage:
 #   ./scripts/automation/run-goal.sh [--session-id <id>] [--max-iter N]
 #                                    [--stall-window N] [--resume] [--reset]
-#                                    [--auto-release]
+#                                    [--headless] [--auto-release]
 #                                    [--acknowledge-regression]
 #                                    [--require-blueprint-approval]
 #                                    [--intent-checkpoint] [--intent-checkpoint-at N]
@@ -21,6 +21,12 @@
 #   --max-iter N                 Optional hard cap on iterations (default: unlimited; 0 = no cap)
 #   --stall-window N             Halt if last N iterations show no journey progress (default: 3)
 #   --resume                     Resume an existing session
+#   --headless                   With --resume: force headless dispatch for THIS run instead of
+#                                adopting the session's persisted interactive backend. One-run
+#                                override — session.json keeps its agent_backend, so the next
+#                                plain --resume is interactive again. For unattended/auto-resume
+#                                contexts where no pump session exists; headless agents run as
+#                                `claude -p` (Agent SDK billing — docs/goal-mode-interactive.md).
 #   --reset                      Discard the named session and start fresh
 #   --auto-release               On GOAL_ACHIEVED, run release-manager once for the whole session
 #   --acknowledge-regression     Continue past a prior REGRESSION_HALT
@@ -176,6 +182,9 @@ AUTO_APPROVE_BLUEPRINT=true
 # `claude -p`, so the work bills to the interactive plan allowance. Pinned
 # per-session (like --cli). Off by default (headless / Agent SDK path).
 INTERACTIVE=false
+# --headless: one-run resume override — skip adopting the session's persisted
+# interactive backend (unattended/auto-resume runs have no pump session).
+FORCE_HEADLESS=false
 # Per-iter push is ON by default for new sessions. Pass --no-push-per-iter to
 # opt out. On resume, the persisted session.json value wins unless overridden
 # by an explicit CLI flag (--push-per-iter or --no-push-per-iter).
@@ -207,6 +216,7 @@ while [[ $# -gt 0 ]]; do
     --auto-approve-blueprint)  AUTO_APPROVE_BLUEPRINT=true; shift ;;   # now the default; kept for back-compat
     --require-blueprint-approval) AUTO_APPROVE_BLUEPRINT=false; shift ;;
     --interactive)             INTERACTIVE=true; shift ;;
+    --headless)                FORCE_HEADLESS=true; shift ;;
     --intent-checkpoint)       INTENT_CHECKPOINT=true; shift ;;
     --intent-checkpoint-at)    INTENT_CHECKPOINT_AT="$2"; shift 2 ;;
     --push-per-iter)           PUSH_PER_ITER=true;  PUSH_FLAG_USER="yes"; shift ;;
@@ -291,10 +301,18 @@ fi
 # ── Resolve the agent dispatch backend (interactive vs headless) ───────────
 # Pinned per-session like --cli: on resume, adopt the persisted backend unless
 # --interactive is re-asserted on the command line.
+if [[ "$FORCE_HEADLESS" == "true" && "$INTERACTIVE" == "true" ]]; then
+  echo "Error: --headless and --interactive are mutually exclusive." >&2
+  exit 2
+fi
 if [[ "$RESUME" == "true" && -f "$SESSION_JSON" && "$INTERACTIVE" != "true" ]]; then
   PERSISTED_BACKEND=$(python3 -c "import json;print(json.load(open('$SESSION_JSON')).get('agent_backend',''))" 2>/dev/null || echo "")
   if [[ "$PERSISTED_BACKEND" == "interactive" ]]; then
-    INTERACTIVE=true
+    if [[ "$FORCE_HEADLESS" == "true" ]]; then
+      echo "[run-goal] --headless: not adopting the session's persisted interactive backend for this run (one-run override; session.json unchanged)."
+    else
+      INTERACTIVE=true
+    fi
   fi
 fi
 if [[ "$INTERACTIVE" == "true" ]]; then
@@ -961,6 +979,47 @@ _host_guard_latest_tctl() { # newest Tctl (°C) from a FRESH sampler csv; empty
   done
   return 0
 }
+# Dispatch-boundary thermal defer — opt-in via HOST_GUARD_TCTL_DISPATCH_GATE=1.
+# The iteration gate cools BETWEEN iterations only; a full iteration dispatches
+# many agents and can hold Tctl in the high 80s for hours (the 2026-08-07 15:18
+# compositor crash rode 84-89 °C for its final minutes, below the boundary
+# gate's threshold). This defers the NEXT dispatch while Tctl ≥ PAUSE — it
+# never interrupts a running agent and proceeds loudly after DISPATCH_MAX_WAIT.
+# agent_with_quota_retry (lib/quota-retry.sh) calls it via declare -F, and the
+# export -f below is what makes it visible there: dispatch happens in child
+# step scripts, not in this shell. Outside an engine tree the function does not
+# exist and the hook is a no-op.
+host_guard_thermal_defer() {
+  local hg_env="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+  [[ -f "$hg_env" ]] || return 0
+  # shellcheck disable=SC1090
+  source "$hg_env"
+  [[ "${HOST_GUARD_ENABLED:-0}" == "1" && "${HOST_GUARD_TCTL_DISPATCH_GATE:-0}" == "1" ]] || return 0
+  local pause_c="${HOST_GUARD_TCTL_PAUSE:-90}" resume_c="${HOST_GUARD_TCTL_RESUME:-80}"
+  local poll="${HOST_GUARD_TCTL_POLL:-15}" max_wait="${HOST_GUARD_TCTL_DISPATCH_MAX_WAIT:-600}"
+  local waited=0 tctl
+  while :; do
+    tctl="$(_host_guard_latest_tctl)"
+    [[ "$tctl" =~ ^[0-9]+$ ]] || break   # no fresh telemetry → nothing to gate on
+    if (( waited == 0 )); then
+      if (( tctl < pause_c )); then break; fi
+      echo "[run-goal] host-guard: Tctl ${tctl}°C ≥ ${pause_c}°C — deferring next dispatch (resumes ≤ ${resume_c}°C, max ${max_wait}s)."
+      hg_event thermal_defer "$(printf '{"tctl_c":%s}' "$tctl")" 2>/dev/null || true
+    else
+      if (( tctl <= resume_c )); then
+        echo "[run-goal] host-guard: cooled to ${tctl}°C after ${waited}s — dispatching."
+        break
+      fi
+      if (( waited >= max_wait )); then
+        echo "[run-goal] host-guard: still ${tctl}°C after ${waited}s (max ${max_wait}s) — dispatching anyway; check cooling."
+        break
+      fi
+    fi
+    sleep "$poll"; waited=$(( waited + poll ))
+  done
+  return 0
+}
+export -f host_guard_thermal_defer _host_guard_latest_tctl
 # Read the platform's OWN postmortem register and freeze the evidence. Runs
 # before every other host-guard check because check 4's hg_sweep deletes the
 # registry records of the dead boot — the only on-disk record of which projects
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
index 7a05494d..b69c62f6 100644
--- a/project-extensions/host-guard/host-guard.env
+++ b/project-extensions/host-guard/host-guard.env
@@ -103,11 +103,29 @@ HOST_GUARD_MARKER_FILES="scripts/dev.sh scripts/start-backend.sh scripts/start-f
 # HOST_GUARD_CLI_PATTERN="claude|codex" (session-root detection).
 HOST_GUARD_REQUIRE_PUMP_CONFINED=1
 
-# Thermal iteration gate (framework defaults shown; uncomment to tune): when
-# the hwmon csv is fresh and Tctl ≥ PAUSE at an iteration boundary, the engine
-# waits until ≤ RESUME (bounded by MAX_WAIT seconds, then proceeds loudly)
-# before dispatching the next iteration — heat-soak protection between
-# iterations, never a mid-iteration halt.
-#HOST_GUARD_TCTL_PAUSE=90
-#HOST_GUARD_TCTL_RESUME=80
+# Thermal iteration gate (framework defaults 90/80/1800): when the hwmon csv
+# is fresh and Tctl ≥ PAUSE at an iteration boundary, the engine waits until
+# ≤ RESUME (bounded by MAX_WAIT seconds, then proceeds loudly) before
+# dispatching the next iteration.
+# 2026-08-07: set explicitly at 85/75 and extended to DISPATCH boundaries
+# (HOST_GUARD_TCTL_DISPATCH_GATE below). The 15:18 gnome-shell SIGSEGV — whose
+# session teardown killed the pump mid-iter-52 — rode Tctl 84-89 °C for its
+# final minutes, below the old boundary-only 90 °C gate. Heat did NOT cause
+# the hardware resets (26-37 W / 65-74 °C at those deaths — see header); this
+# trims coincident stress on marginal silicon while the C-state soak runs
+# (~/.cache/iad/host-guard/soak-log.md).
+HOST_GUARD_TCTL_PAUSE=85
+HOST_GUARD_TCTL_RESUME=75
 #HOST_GUARD_TCTL_MAX_WAIT=1800
+# Defer the NEXT agent dispatch (never interrupts a running one) while Tctl ≥
+# PAUSE, bounded by HOST_GUARD_TCTL_DISPATCH_MAX_WAIT (default 600 s, then
+# proceeds loudly). Emits thermal_defer events to the machine ledger.
+HOST_GUARD_TCTL_DISPATCH_GATE=1
+
+# Pump-dispatched QA browsers run HEADLESS: host-guard-exec.sh strips
+# DISPLAY/WAYLAND_DISPLAY so the Chrome MCP picks headless (lib/common.sh
+# semantics; engine lanes already do this). The headed pump QA Chrome was a
+# standing compositor-stress source — hours of Wayland frame-error spam before
+# the 2026-08-07 15:18 gnome-shell crash. CHAIN_BQA_HEADED=1 remains the
+# headed debugging escape.
+HOST_GUARD_PUMP_HEADLESS_QA=1
```
