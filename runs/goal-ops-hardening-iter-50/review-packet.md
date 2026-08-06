# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/data_manager.py` (65 lines not shown)
- `apps/backend/app/engine/research.py` (184 lines not shown)
- `apps/backend/tests/test_data_manager.py` (44 lines not shown)
- `apps/backend/tests/test_research_streaming.py` (8 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 0d120c9f..ed559158 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -79,6 +79,7 @@ from app.models import (
     CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
+    EventStudyCache,
     ForwardReturn,
     ImportCheckpoint,
     MacroSeries,
@@ -3192,14 +3193,38 @@ def _release_process_memory() -> None:
 
     ops-hardening iter-9 (B2): the libc handle resolution itself is memoized by `_resolve_libc_malloc_trim`
     (module-level, first-call-cached) — this function's own `gc.collect()` + `malloc_trim(0)` timing and
-    effect are unchanged; only the redundant repeated resolution is removed."""
+    effect are unchanged; only the redundant repeated resolution is removed.
+
+    ops-hardening iter-50 AUDIT FIX (finding B2) — OBSERVABILITY ONLY, no behavior change. The 2026-08-05
+    outage's ~17-minute silence begins at the LAST line `_refresh_ingest_aggregates` logs (the
+    `drawdown_expectations_warm` phase-timing line), and the very next statements executed are its enclosing
+    `finally:` -> drop the shared bar cache -> THIS function. `gc.collect()` holds the GIL for its whole
+    duration, and the outage's signature (process alive, CPU 80-89%, main thread parked in `futex_do_wait`,
+    VmRSS falling 7.76 -> 5.89 GB — memory being RETURNED, not exhausted) matches that teardown rather than
+    an OOM. That frame is the only one inside the silence nobody has timed, so it is timed here: an INFO
+    line BEFORE (so a process killed or restarted mid-teardown still leaves the entry boundary in
+    `logs/backend.log`) and an INFO line after carrying each step's wall clock. The signature is
+    deliberately unchanged (no caller label) so that the ~15 existing call sites — and the zero-argument
+    spies several test modules monkeypatch over this function — keep working verbatim; each pair of lines
+    is unambiguously attributed by the caller's own surrounding log lines. No caller's behavior changes, no
+    computed value is touched, and the "log + continue, never raise" contract of the `except MemoryError`
+    handlers that call this is preserved (`logging` swallows its own emit failures)."""
+    logger.info("_release_process_memory: START (gc.collect + malloc_trim)")
+    _gc_t0 = time.monotonic()
     gc.collect()
+    _gc_s = time.monotonic() - _gc_t0
+    _trim_t0 = time.monotonic()
     malloc_trim = _resolve_libc_malloc_trim()
     if malloc_trim is not None:
         try:
             malloc_trim(0)  # glibc: return free heap/arena pages to the OS (no-op elsewhere)
         except OSError:  # defensive — a resolved-but-failing call still must never mask the caller
             pass
+    _trim_s = time.monotonic() - _trim_t0
+    logger.info(
+        "_release_process_memory: DONE gc_collect=%.2fs malloc_trim=%.2fs total=%.2fs",
+        _gc_s, _trim_s, _gc_s + _trim_s,
+    )
 
 
 # --------------------------------------------------------------------------------------------------
@@ -3222,7 +3247,14 @@ _FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
 # The call sites this hook understands. Each is the exact per-item boundary whose `except MemoryError`
 # handler J-07's acceptance names; an unknown name in the env var injects nothing (a typo must not
 # silently look like a passing drill).
-_FAULT_INJECT_SITES = frozenset({"forward_aggregates", "drawdown_expectations", "backfill_worker"})
+# ops-hardening iter-50: "factor_lab_all" added — `research.compute_factor_lab_all`'s per-(factor,horizon)
+# obs-build+sort isolate-and-continue site (the confirmed iter-49 crash frame). Lives in this SAME
+# frozenset (not a duplicate mechanism in research.py) because `research.py` reaches this hook via a lazy
+# `from app.engine import data_manager` import (research.py sits BELOW this module in the dependency
+# graph — data_manager already imports FROM research at module level, so the reverse would be circular).
+_FAULT_INJECT_SITES = frozenset({
+    "forward_aggregates", "drawdown_expectations", "backfill_worker", "factor_lab_all",
+})
 
 
 def _fault_inject_memory_error(site: str) -> None:
@@ -3753,6 +3785,142 @@ def _log_isolation_failure(msg: str, *args: object, exc_info: bool = True) -> No
             pass
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-50 (J-07): a shared warm-in-progress guard between `warmup._warm_drawdown_expectations`
+# (the boot/re-warm path) and THIS module's own `_refresh_ingest_aggregates` drawdown-expectations warm
+# phase below — the two proven-concurrent crash contributors from iter-49's own traceback read (three heavy
+# loops were live at once: the ingest finalize tail, the boot re-warm, and a live Factor Lab request; the
+# boot re-warm and finalize tail both "aborted gracefully" that time, but nothing PREVENTED them running
+# concurrently). Mirrors the `_COVERAGE_LOCK` single-flight SHAPE (one `threading.Lock`, no new concurrency
+# abstraction) but a DIFFERENT policy: `_COVERAGE_LOCK` makes late callers WAIT and share one compute;
+# this guard makes the SECOND caller DEFER instead — it does not run its own heavy per-claim loop at all,
+# logs the deferral, and relies on its own next natural trigger to retry (the boot re-warm retries on the
+# next boot/restart; the ingest finalize tail retries on the next ingest job) — never a block, never a
+# dropped claim (the deferred side's ledger claims simply stay exactly as warm/cold as they were).
+_DRAWDOWN_WARM_LOCK = threading.Lock()
+_DRAWDOWN_WARM_IN_PROGRESS = False
+
+
+def _try_acquire_drawdown_warm(caller: str) -> bool:
+    """Attempt to claim the shared drawdown-expectations warm slot for `caller` (a short label for the log
+    line, e.g. "boot_rewarm" / "ingest_finalize"). Returns True iff THIS caller won the slot and must run
+    its heavy per-claim loop; False iff another caller already holds it and THIS caller must defer (skip
+    the loop entirely, without blocking). Always pair a True result with a later `_release_drawdown_warm()`
+    call (a `finally` block), or the slot wedges for the rest of the process."""
+    global _DRAWDOWN_WARM_IN_PROGRESS
+    with _DRAWDOWN_WARM_LOCK:
+        if _DRAWDOWN_WARM_IN_PROGRESS:
+            logger.info(
+                "drawdown-expectations warm-in-progress guard: %s deferring -- another warm is already "
+                "live in this process; retrying on its own next natural trigger, never blocking", caller,
+            )
+            return False
+        _DRAWDOWN_WARM_IN_PROGRESS = True
+        return True
+
+
+def _release_drawdown_warm() -> None:
+    """Release the shared drawdown-expectations warm slot. Idempotent-safe to call even if the caller never
+    held it (a stray release just re-clears an already-False flag) — callers still gate their OWN release on
+    having actually won `_try_acquire_drawdown_warm` first, so this is never reached from a deferred path."""
+    global _DRAWDOWN_WARM_IN_PROGRESS
+    with _DRAWDOWN_WARM_LOCK:
+        _DRAWDOWN_WARM_IN_PROGRESS = False
+
+
+# ops-hardening iter-50 AUDIT FIX (finding B2) — the interlock above was aimed at the pair that did not
+# collide. It guards ONLY the two drawdown-expectations per-claim loops against each other, but the live
+# 2026-08-05 outage overlapped the boot re-warm's per-claim loop with the finalize tail's OTHER heavy
+# phases: `forward_aggregates_warm` (measured 337-385s live) and `coverage_membership_timeline_refresh`
+# (82.04s live), neither of which took the slot. `logs/backend.log` shows the narrow guard FIRING and NOT
+# HELPING at 23:04:01,255 ("drawdown-expectations warm-in-progress guard: ingest_finalize deferring") while
+# that same job's UNGUARDED `forward_aggregates_warm` had been running since 22:57:37 — the outage window
+# is precisely that overlap.
+#
+# The widened interlock covers the WHOLE ingest finalize-tail heavy-warm window, and it is deliberately
+# ASYMMETRIC rather than first-come-first-served:
+#
+#   * The ingest finalize tail is the PRIORITY producer. Its warms are the J-05 product contract itself
+#     ("computed at ingest time and persisted, never recomputed on a request path") — deferring them would
+#     push the cost onto a live request, the exact pattern this session exists to eliminate. So it never
+#     defers to the boot re-warm; it simply declares its window.
+#   * The boot re-warm (`warmup._warm_drawdown_expectations`) is a best-effort cache PRE-warm whose own
+#     contract is already "non-fatal, deferrable, retried on the next boot/restart". So it YIELDS: it does
+#     not start while an ingest heavy-warm window is open, and — because a single claim can itself run for
+#     minutes — it re-checks BEFORE EVERY CLAIM and stops early if a window opens mid-loop.
+#
+# Honest limit, disclosed rather than papered over: the yield granularity is one claim, so an ingest window
+# opening mid-claim still overlaps that claim's remaining runtime (worst observed single claim on the live
+# ledger: the ~250s `combination:composite:h20`). That is a bounded overlap in place of an unbounded one;
+# finer yielding would require an interruption seam inside `forward_testing`, which is separate work.
+_INGEST_HEAVY_WARM_DEPTH = 0  # a COUNTER, not a bool — nested/concurrent ingest jobs must not un-declare
+                              # each other's window (guarded by `_DRAWDOWN_WARM_LOCK`, same module state).
+
+
+def _enter_ingest_heavy_warm(job_id: str) -> None:
+    """Declare that an ingest finalize-tail heavy-warm window is open in this process (iter-50 audit B2).
+    Always pair with `_exit_ingest_heavy_warm()` in a `finally`."""
+    global _INGEST_HEAVY_WARM_DEPTH
+    with _DRAWDOWN_WARM_LOCK:
+        _INGEST_HEAVY_WARM_DEPTH += 1
+        depth = _INGEST_HEAVY_WARM_DEPTH
+    logger.info(
+        "ingest heavy-warm window OPEN: job=%s depth=%d -- the boot re-warm yields for its duration "
+        "(iter-50 audit B2)", job_id, depth,
+    )
+
+
+def _exit_ingest_heavy_warm(job_id: str) -> None:
+    """Close this job's ingest finalize-tail heavy-warm window. Never drops below zero, so a stray call can
+    never leave the process permanently 'not warming'."""
+    global _INGEST_HEAVY_WARM_DEPTH
+    with _DRAWDOWN_WARM_LOCK:
+        _INGEST_HEAVY_WARM_DEPTH = max(0, _INGEST_HEAVY_WARM_DEPTH - 1)
+        depth = _INGEST_HEAVY_WARM_DEPTH
+    logger.info("ingest heavy-warm window CLOSED: job=%s depth=%d", job_id, depth)
+
+
+def _ingest_heavy_warm_active() -> bool:
+    """True while at least one ingest finalize-tail heavy-warm window is open in this process."""
+    with _DRAWDOWN_WARM_LOCK:
+        return _INGEST_HEAVY_WARM_DEPTH > 0
+
+
+def _drawdown_expectations_ledger_needs_recompute(
+    session: Session, ledger_entries: list, cfg: Config,
+) -> bool:
+    """True iff at least one non-forward-walk ledger claim would actually be a cache MISS for the CURRENT
+    dataset version — i.e. `forward_testing.compute_drawdown_expectations_cached` would need to compute (not
+    just re-serve) at least one of them. Mirrors the SAME `(subject, view, asof_key, dataset_version,
+    horizon)` HIT check that function's own cache-read performs (forward_testing.py, immediately inside
+    `compute_drawdown_expectations_cached`) — read-only, one indexed row lookup per claim, never the
+    `phase_context_by_date` precompute this check exists to gate (ops-hardening iter-50, TC-6). An empty
+    ledger (after the SAME `FORWARD_WALK_TYPE` filter the warm loop below applies) is vacuously "nothing
+    needs it" -> False."""
+    version = _dataset_version(session)
+    for entry in ledger_entries:
+        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
+            continue
+        claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
+        horizon = claim.get("horizon")
+        if horizon not in cfg.walk_forward.underwater_horizons:
+            continue  # the SAME out-of-scope gate compute_drawdown_expectations_cached applies -- never
+                      # "needs" a compute; mirrors that function's own early return.
+        subject = forward_testing._drawdown_expectations_cache_subject(claim)
+        hit = session.exec(
+            select(EventStudyCache).where(
+                EventStudyCache.subject == subject,
+                EventStudyCache.view == forward_testing._DD_EXPECTATIONS_VIEW,
+                EventStudyCache.asof_key == forward_testing._DD_EXPECTATIONS_ASOF_KEY,
+                EventStudyCache.dataset_version == version,
+                EventStudyCache.horizon == horizon,
+            )
+        ).first()
+        if hit is None:
+            return True
+    return False
+
+
 def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress) -> list[str]:
     """The ingest finalize hook (J-05). Each aggregate is refreshed independently (its own try/except: log
     + continue) so one aggregate's failure never prevents another from refreshing, and this function itself
@@ -3838,6 +4006,13 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
         prog.job_id,
         "attach_shared_cache(live shared cache)" if shared is not None else "nullcontext(no shared cache)",
     )
+    # ops-hardening iter-50 AUDIT FIX (B2): declare the ingest heavy-warm window across the WHOLE finalize
+    # tail — every heavy phase below (`coverage_membership_timeline_refresh`, `per_date_coverage_warm`,
+    # `market_phase_warm`, `forward_aggregates_warm`, `research_hot_keys_warm`, `index_series_warm`,
+    # `drawdown_expectations_warm`), not just the drawdown pair the narrow slot guarded. The boot re-warm
+    # yields for its duration; this job never defers (it is the priority producer — see the guard's own
+    # comment block). Closed in the `finally` below whether any individual phase succeeded or raised.
+    _enter_ingest_heavy_warm(prog.job_id)
     try:
         with cache_ctx:
             # ops-hardening iter-48 (J-05 diagnosis): phase-level wall-clock timing across every finalize-
@@ -4105,96 +4280,124 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
 
             _phase_t0 = time.monotonic()
             drawdown_warmed = False
-            # ops-hardening iter-49 (J-05, drawdown_expectations_warm bound): `phase_context_by_date`'s
-            # all-history causal timeline is invariant across every claim in this loop (`as_of=None`
-            # always, `cfg` unchanged mid-loop) — computed ONCE here and threaded through
-            # `compute_drawdown_expectations_cached`'s new `phases` parameter, instead of once per claim (7x
-            # on the live ledger). Own try/except: a NON-MEMORY failure here degrades to every claim
-            # self-computing its own timeline below (`phases=None` falls back to the SAME per-claim
-            # behavior `compute_drawdown_expectations` always had) — never a reason to abort the whole warm.
             _dd_phases_memory_abort = False
-            try:
-                _dd_phases = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
-            # ops-hardening iter-49 AUDIT (finding B3 fix): a `MemoryError` here STOPS this phase — it does
-            # NOT fall through to the per-claim loop. Falling through set `phases=None`, which makes every
-            # one of the ledger's claims self-compute its own all-history timeline: degrading under memory
-            # pressure into the MORE allocating path, i.e. exactly the "hammering the next claim's
-            # allocation under pressure" the iter-8 convention (see the per-claim handler below) exists to
-            # prevent. Now this handler matches that convention in full — stop, release memory back to the
-            # OS, and report honestly: `drawdown_warmed` stays False, so `drawdown_expectations` is omitted
-            # from `aggregates_refreshed` rather than claimed for work that never ran.
-            except MemoryError as exc:
-                _log_isolation_failure(
-                    "ingest drawdown-expectations phase-context warm aborted — memory pressure, stopping "
-                    "the drawdown-expectations warm without attempting any claim: %s", exc,
-                )
-                _release_process_memory()
-                _dd_phases = None
-                _dd_phases_memory_abort = True
-            except Exception as exc:  # noqa: BLE001 — non-fatal: fall back to per-claim self-compute
-                _log_isolation_failure(
-                    "ingest drawdown-expectations phase-context warm failed (non-fatal, falling back to "
-                    "per-claim self-compute): %s", exc,
-                )
-                _dd_phases = None
-            # `()` (never `ledger_entries`) after a memory-pressure abort above — the loop is skipped
-            # entirely, per the iter-8 stop convention. Every other outcome (success, or a non-memory
-            # precompute failure that degraded to `phases=None`) iterates the ledger exactly as before.
-            for entry in (() if _dd_phases_memory_abort else ledger_entries):
-                if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
-                    continue
-                claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
-                prog.tick()  # heartbeat stamp before each claim's warm call — see docstring above.
-                # ops-hardening iter-49 (J-05/J-07 TC-2): a stable, honest per-claim identity for the
-                # sub-phase timing log below — kind + the claim's own discriminating selector (factor /
-                # event-study subject / combination cohort) + horizon, NEVER a raw loop index (an index is
-                # not diagnostic across runs whose ledger order can change).
-                _claim_id = "{}:{}:h{}".format(
-                    claim.get("kind", "?"),
-                    claim.get("factor") or claim.get("subject") or claim.get("cohort")
-                    or claim.get("signal") or "?",
-                    claim.get("horizon", "?"),
-                )
-                _claim_t0 = time.monotonic()
+            # ops-hardening iter-50 (J-07): the shared warm-in-progress guard — this phase and
+            # `warmup._warm_drawdown_expectations` (the boot/re-warm path) must never run their heavy
+            # per-claim loops concurrently in the same process (the second proven-concurrent crash
+            # contributor from iter-49's own traceback read). A loss here is NON-FATAL: `drawdown_warmed`
+            # stays False, so "drawdown_expectations" is honestly omitted from `refreshed` rather than
+            # claimed for work that never ran — this job's OWN next ingest naturally retries.
+            _drawdown_warm_won = _try_acquire_drawdown_warm("ingest_finalize")
+            if _drawdown_warm_won:
                 try:
-                    try:
-                        # iter-39 (audit B3 / J-07 step 4): test-only injection point — see
-                        # `_fault_inject_memory_error` (a no-op unless this process names this site in the
-                        # env).
-                        _fault_inject_memory_error("drawdown_expectations")
-                        result = forward_testing.compute_drawdown_expectations_cached(
-                            session, claim, cfg, phases=_dd_phases,
-                        )
-                        # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an
-                        # out-of-scope horizon or an unresolvable cohort returns None honestly and must NOT
-                        # be reported as refreshed (mirrors the `market_phase`/`research_hot_keys` "actually
-                        # did something" convention above).
-                        if result is not None:
-                            drawdown_warmed = True
-                    # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-claim
-                    # isolate-and-continue below — a `MemoryError` stops THIS loop immediately (no further
-                    # claims attempted) and forces memory back to the OS, instead of hammering the next
-                    # claim's allocation under pressure. `drawdown_warmed` already honestly reflects any
-                    # claim that succeeded before the abort.
-                    except MemoryError as exc:
-                        _log_isolation_failure(
-                            "ingest drawdown-expectations warm aborted — memory pressure, stopping "
-                            "remaining claims in this loop: %s", exc,
+                    # ops-hardening iter-49 (J-05, drawdown_expectations_warm bound): `phase_context_by_date`'s
+                    # all-history causal timeline is invariant across every claim in this loop (`as_of=None`
+                    # always, `cfg` unchanged mid-loop) — computed ONCE here and threaded through
+                    # `compute_drawdown_expectations_cached`'s new `phases` parameter, instead of once per claim (7x
+                    # on the live ledger). Own try/except: a NON-MEMORY failure here degrades to every claim
+                    # self-computing its own timeline below (`phases=None` falls back to the SAME per-claim
+                    # behavior `compute_drawdown_expectations` always had) — never a reason to abort the whole warm.
+                    #
+                    # ops-hardening iter-50 (TC-6): skip this precompute ENTIRELY when NO ledger claim
+                    # actually needs (re)computation (every claim is already a cache HIT for the current
+                    # dataset version) — closes the ~23.6-23.9s measured MID health-poll-stall cluster
+                    # (`reports/perf-budgets.md` Item R Addendum 6) for the common case where an ingest's
+                    # own new data never touched any drawdown-expectations claim's cohort. The per-claim
+                    # loop below still runs unconditionally over `ledger_entries` either way (a HIT claim's
+                    # own cached-read cost is unaffected by `phases`) — only this precompute is gated.
+                    if _drawdown_expectations_ledger_needs_recompute(session, ledger_entries, cfg):
+                        try:
+                            _dd_phases = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
+                        # ops-hardening iter-49 AUDIT (finding B3 fix): a `MemoryError` here STOPS this phase — it does
+                        # NOT fall through to the per-claim loop. Falling through set `phases=None`, which makes every
+                        # one of the ledger's claims self-compute its own all-history timeline: degrading under memory
+                        # pressure into the MORE allocating path, i.e. exactly the "hammering the next claim's
+                        # allocation under pressure" the iter-8 convention (see the per-claim handler below) exists to
+                        # prevent. Now this handler matches that convention in full — stop, release memory back to the
+                        # OS, and report honestly: `drawdown_warmed` stays False, so `drawdown_expectations` is omitted
+                        # from `aggregates_refreshed` rather than claimed for work that never ran.
+                        except MemoryError as exc:
+                            _log_isolation_failure(
+                                "ingest drawdown-expectations phase-context warm aborted — memory pressure, stopping "
+                                "the drawdown-expectations warm without attempting any claim: %s", exc,
+                            )
+                            _release_process_memory()
+                            _dd_phases = None
+                            _dd_phases_memory_abort = True
+                        except Exception as exc:  # noqa: BLE001 — non-fatal: fall back to per-claim self-compute
+                            _log_isolation_failure(
+                                "ingest drawdown-expectations phase-context warm failed (non-fatal, falling back to "
+                                "per-claim self-compute): %s", exc,
+                            )
+                            _dd_phases = None
+                    else:
+                        _dd_phases = None
+                        logger.info(
+                            "J-05 finalize-tail drawdown_expectations_warm: phase_context_by_date skipped -- "
+                            "every ledger claim already cache-HIT for the current dataset version (TC-6)"
                         )
-                        _release_process_memory()
-                        break
-                    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next claim
-                        _log_isolation_failure(
-                            "ingest drawdown-expectations warm failed for one claim (non-fatal): %s", exc
+                    # `()` (never `ledger_entries`) after a memory-pressure abort above — the loop is skipped
+                    # entirely, per the iter-8 stop convention. Every other outcome (success, a skipped
+                    # precompute, or a non-memory precompute failure that degraded to `phases=None`)
+                    # iterates the ledger exactly as before.
+                    for entry in (() if _dd_phases_memory_abort else ledger_entries):
+                        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
+                            continue
+                        claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
+                        prog.tick()  # heartbeat stamp before each claim's warm call — see docstring above.
+                        # ops-hardening iter-49 (J-05/J-07 TC-2): a stable, honest per-claim identity for the
+                        # sub-phase timing log below — kind + the claim's own discriminating selector (factor /
+                        # event-study subject / combination cohort) + horizon, NEVER a raw loop index (an index is
+                        # not diagnostic across runs whose ledger order can change).
+                        _claim_id = "{}:{}:h{}".format(
+                            claim.get("kind", "?"),
+                            claim.get("factor") or claim.get("subject") or claim.get("cohort")
+                            or claim.get("signal") or "?",
+                            claim.get("horizon", "?"),
                         )
+                        _claim_t0 = time.monotonic()
+                        try:
+                            try:
+                                # iter-39 (audit B3 / J-07 step 4): test-only injection point — see
+                                # `_fault_inject_memory_error` (a no-op unless this process names this site in the
+                                # env).
+                                _fault_inject_memory_error("drawdown_expectations")
+                                result = forward_testing.compute_drawdown_expectations_cached(
+                                    session, claim, cfg, phases=_dd_phases,
+                                )
+                                # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an
+                                # out-of-scope horizon or an unresolvable cohort returns None honestly and must NOT
+                                # be reported as refreshed (mirrors the `market_phase`/`research_hot_keys` "actually
+                                # did something" convention above).
+                                if result is not None:
+                                    drawdown_warmed = True
+                            # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-claim
+                            # isolate-and-continue below — a `MemoryError` stops THIS loop immediately (no further
... [diff_bound] apps/backend/app/engine/data_manager.py: 65 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index b3513c34..f95e9b1a 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -38,6 +38,8 @@ from __future__ import annotations
 import json
 import logging
 import threading
+import time
+from array import array
 from collections import defaultdict
 from datetime import date as date_cls
 from datetime import datetime, timezone
@@ -849,10 +851,183 @@ def _all_fr_slice_map(
     return fr_by_h
 
 
+# ops-hardening iter-50 AUDIT FIX (finding B3, J-07/AG-8) — the two RESIDENT accumulators below replace the
+# `list[tuple]` / `list[tuple]` shapes iter-31 shipped. WHY: iter-50's own live evidence contradicted the
+# spec's "already bounded, unaffected by this defect" carve-out for this function. Five real (un-injected)
+# `MemoryError`s under live pressure (2026-08-05 23:28:44 / 23:37:53 / 23:38:25 / 23:42:07 / 23:44:52,
+# `logs/backend.log`) all carry the SAME traceback, and NONE lands at the per-(factor,horizon) transient the
+# iteration bounded — every one lands at `pools[h].append(...)` in the sweep below. `core_records`+`pools`
+# accumulate across the WHOLE sweep and stay resident for the entire call, so they — not the per-iteration
+# transient built on top of them — dominate the peak. "Chunked source reads" bounded the QUERY side only;
+# the RETURN VALUE was never bounded, just re-encoded.
+#
+# The fix is a columnar (struct-of-arrays) encoding: fixed-width `array`/`bytearray` buffers instead of one
+# Python object per row. A pool row costs 8+8+8+1 = 25 raw bytes here versus ~128 bytes as a 3-tuple of
+# boxed floats (a tuple header + 3 pointers + 2 float objects + the list slot); a core record costs
+# 8 + 8 + (9 x n_factors) bytes versus a tuple-of-tuple-of-boxed-floats. NOTHING is truncated, dropped,
+# rounded, or reordered — the same rows in the same order, so byte-identity (AG-3) is preserved by
+# construction, and the AG-8 disclosure net still sees true `len()`s.
+#
+# Both classes implement the SEQUENCE protocol (`__len__`/`__getitem__`/`__iter__`/`__bool__`) materialising
+# the OLD tuple shape on demand, so every existing caller, oracle and test that walks the returned structure
+# keeps working unchanged; `compute_factor_lab_all`'s hot loop uses the direct column accessors instead, so
+# the hot path never pays that materialisation.
+#
+# TYPE NOTE (byte-identity): the float columns are IEEE-754 doubles, which is exactly what a Python `float`
+# already is — a stored value round-trips bit-for-bit. A value arriving as an `int` (a JSON `record_json`
+# component `raw` written without a decimal point) becomes the equal `float`; every consumer of these
+# columns already coerces (`float(factor_value)` in `compute_factor_lab_all`) or aggregates into floats
+# (`_deciles` / `_rank_ic` means), so no SERVED figure changes. `None` is carried exactly by a companion
+# presence mask — never conflated with 0.0, never with NaN.
+class _FactorCoreRecords:
+    """Columnar replacement for `list[tuple[run_id, ticker, values_tuple]]` — one entry per ScannerResult
+    with a realized return at >= 1 horizon, holding the identity + every factor's stored value.
+
+    `tickers` stays a `list[str]` on purpose: the strings are interned by the caller, so the live cost is
+    one pointer per row plus ~591 shared string objects on the live basis (the same sharing iter-31's
+    `ticker_intern` already achieved) — an array-of-offsets encoding would save nothing measurable and
+    would break the byte-identity of the ticker values."""
+
+    __slots__ = ("run_ids", "tickers", "value_cols", "value_present", "n_factors", "n_non_numeric")
+
+    def __init__(self, n_factors: int):
+        self.n_factors = n_factors
+        self.run_ids = array("q")                                        # int64 — one per core record
+        self.tickers: list[str] = []                                     # interned; one pointer per record
+        self.value_cols = [array("d") for _ in range(n_factors)]         # float64 column per factor
+        self.value_present = [bytearray() for _ in range(n_factors)]     # 1 byte per (record, factor)
+        self.n_non_numeric = 0  # AG-8 disclosure counter — see `append` below
+
+    def append(self, run_id: int, ticker: str, values) -> int:
+        """Append one core record; returns its `core_idx` (the SAME index the old `len(core_records)`
+        assignment produced, so `pools`' back-references are unchanged).
+
+        ops-hardening iter-50 AUDIT FIX (finding B4, AG-8 data-shape tolerance): a factor value reaching
+        here is either a typed `ScannerResult` column (always a real number or NULL) or a `record_json`
+        component's `raw` — free-form JSON, so it can be a string, a list, or anything else a future
+        record shape emits. `array("d").append` accepts ONLY a real number (`"3.5"` raises `TypeError`),
+        whereas the pre-columnar path stored the raw object and its sole consumer coerced it later with
+        `float(...)` — which accepted `"3.5"` fine. Applying that SAME `float(...)` coercion HERE keeps the
+        served figure byte-identical for every shape the old path served (`3 → 3.0`, `True → 1.0`,
+        `"3.5" → 3.5`, `3.5 → 3.5`) and restores the tolerance the columnar encoding had narrowed.
+
+        A value that is not a real number AT ALL (`"n/a"`, a list, a dict) is recorded as ABSENT — the
+        module's own established "excluded factor-NULL observation, never fabricated" convention
+        (`_extract_factor_value`'s docstring) — rather than raising out of the shared pool builder, where
+        no caller's handler would catch it and the whole `?all=true` response would 500 (AG-8 forbids the
+        blank application-error page). It is counted and disclosed by a WARNING in the sweep below."""
+        idx = len(self.run_ids)
+        self.run_ids.append(run_id)
+        self.tickers.append(ticker)
+        for j, v in enumerate(values):
+            if v is None:
+                self.value_cols[j].append(0.0)      # placeholder; masked out below — never read as a value
+                self.value_present[j].append(0)
+                continue
+            try:
+                fv = float(v)                        # the pre-columnar consumer's own coercion, verbatim
+            except (TypeError, ValueError):
+                self.n_non_numeric += 1
+                self.value_cols[j].append(0.0)      # placeholder; masked out — excluded, never fabricated
+                self.value_present[j].append(0)
+                continue
+            self.value_cols[j].append(fv)
+            self.value_present[j].append(1)
+        return idx
+
+    def factor_value(self, i: int, j: int) -> Optional[float]:
+        """The stored value of factor `j` on core record `i` — `None` iff the factor was NULL/absent there
+        (the excluded factor-NULL observation `_extract_factor_value` reports, never fabricated)."""
+        return self.value_cols[j][i] if self.value_present[j][i] else None
+
+    def run_id(self, i: int) -> int:
+        return self.run_ids[i]
+
+    def ticker(self, i: int) -> str:
+        return self.tickers[i]
+
+    def __len__(self) -> int:
+        return len(self.run_ids)
+
+    def __bool__(self) -> bool:
+        return len(self.run_ids) > 0
+
+    def __getitem__(self, i: int) -> tuple:
+        if i < 0:
+            i += len(self.run_ids)
+        return (
+            self.run_ids[i], self.tickers[i],
+            tuple(self.factor_value(i, j) for j in range(self.n_factors)),
+        )
+
+    def __iter__(self):
+        for i in range(len(self.run_ids)):
+            yield self[i]
+
+
+class _FactorObsPool:
+    """Columnar replacement for one horizon's `list[tuple[core_idx, realized_return, max_drawdown]]` — the
+    genuinely per-horizon part of an observation (identity + factor values live once in
+    `_FactorCoreRecords`). This is the exact `append` site of all five live `MemoryError` tracebacks.
+
+    iter-50 AUDIT FIX (B4) scope note: unlike `_FactorCoreRecords`' factor values, these two columns are
+    fed from the TYPED `ForwardReturn.realized_return` / `ForwardReturn.max_drawdown` Float columns, not
+    from free-form `record_json` — so they are already a real number or NULL by construction, and a
+    non-numeric there would equally have broken `_deciles`' mean before the columnar encoding existed. No
+    per-row coercion is applied here: it would buy no data-shape tolerance the DB schema does not already
+    give, and this `append` runs once per pool row (millions), where `_FactorCoreRecords.append` runs once
+    per core record."""
+
+    __slots__ = ("core_idx", "returns", "return_present", "max_drawdowns", "max_drawdown_present")
+
+    def __init__(self):
+        self.core_idx = array("q")               # int64 index into the shared `_FactorCoreRecords`
+        self.returns = array("d")                # float64 realized forward return
+        self.return_present = bytearray()        # realized_return is non-NULL in practice; carried exactly
+        self.max_drawdowns = array("d")          # float64 paired max drawdown (J-86)
+        self.max_drawdown_present = bytearray()  # max_drawdown IS nullable — mask, never a NaN sentinel
+
+    def append(self, core_idx: int, realized, max_drawdown) -> None:
+        self.core_idx.append(core_idx)
+        if realized is None:
+            self.returns.append(0.0)
+            self.return_present.append(0)
+        else:
+            self.returns.append(realized)
+            self.return_present.append(1)
+        if max_drawdown is None:
+            self.max_drawdowns.append(0.0)
+            self.max_drawdown_present.append(0)
+        else:
+            self.max_drawdowns.append(max_drawdown)
+            self.max_drawdown_present.append(1)
+
+    def realized(self, i: int) -> Optional[float]:
+        return self.returns[i] if self.return_present[i] else None
+
+    def max_drawdown(self, i: int) -> Optional[float]:
+        return self.max_drawdowns[i] if self.max_drawdown_present[i] else None
+
+    def __len__(self) -> int:
+        return len(self.core_idx)
+
+    def __bool__(self) -> bool:
+        return len(self.core_idx) > 0
+
+    def __getitem__(self, i: int) -> tuple:
+        if i < 0:
+            i += len(self.core_idx)
+        return (self.core_idx[i], self.realized(i), self.max_drawdown(i))
+
+    def __iter__(self):
+        for i in range(len(self.core_idx)):
+            yield (self.core_idx[i], self.realized(i), self.max_drawdown(i))
+
+
 def _all_factor_observations_by_horizon(
     session: Session, factors: list, horizons: list[int], as_of: Optional[date_cls] = None,
     *, cfg: Optional[Config] = None,
-) -> tuple[list[tuple[int, str, tuple]], dict[int, list[tuple[int, float, Optional[float]]]]]:
+) -> tuple["_FactorCoreRecords", dict[int, "_FactorObsPool"]]:
     """The read-only SHARED per-observation pools for the all-factors view across EVERY horizon in
     `horizons` (J-109), built from ONE run-chunked sweep: per slice of run ids, one `ForwardReturn` SELECT
     covering all horizons (`horizon IN horizons`, column-projected to run_id/symbol/realized_return/
@@ -870,16 +1045,27 @@ def _all_factor_observations_by_horizon(
     deferred (771,629-804,372 observations PER horizon on the live basis — `config.yaml`'s
     `research.factor_pool_max_observations` comment).
 
+    ops-hardening iter-50 AUDIT FIX (finding B3) — the SAME redesign taken from "smaller Python objects" to
+    "no per-row Python object at all". iter-31's compaction was real but still allocated one boxed tuple (and
+    its boxed floats) per row, so the RESIDENT return value remained O(observations) in Python objects — and
+    at the current live scale (6,496,075 `forward_returns` rows) that is where the process actually runs out:
+    five real, un-injected `MemoryError`s on 2026-08-05 all carry the identical traceback ending at
+    `pools[h].append(...)` HERE, none at the per-(factor,horizon) transient iter-50 originally bounded. The
+    accumulators are now COLUMNAR (`_FactorCoreRecords` / `_FactorObsPool` above): fixed-width `array`
+    buffers plus 1-byte presence masks, ~25 bytes per pool row against ~128 before. Nothing is truncated,
+    dropped, rounded, or reordered — see the byte-identity keystone below, which is unchanged.
+
     Returns `(core_records, pools)` — a genuine memory-representation redesign, not a smaller constant:
-      - `core_records`: ONE entry per ScannerResult with a realized return at >= 1 horizon —
-        `(run_id, ticker, values)`, where `values` is a TUPLE (not a dict) of every catalog factor's stored
-        value, ORDERED to match `factors` (so `values[i]` is `factors[i]`'s value — `compute_factor_lab_all`
-        looks it up by a precomputed index, never by string key). `ticker` is INTERNED against a local cache
-        scoped to this call, so the (far smaller) set of distinct ticker strings is held ONCE rather than
-        once per horizon-observation.
-      - `pools[h]`: a list of SMALL `(core_idx, realized_return, max_drawdown)` tuples — the genuinely
-        per-horizon-specific data (a result's realized return / drawdown differ by horizon; its identity and
-        factor values do not) — replacing the old per-horizon 5-key dict. `core_idx` indexes `core_records`.
+      - `core_records` (`_FactorCoreRecords`): ONE entry per ScannerResult with a realized return at >= 1
+        horizon, carrying `run_id`, `ticker`, and every catalog factor's stored value ORDERED to match
+        `factors` (so factor `i`'s value is column `i` — `compute_factor_lab_all` looks it up by a
+        precomputed index, never by string key). `ticker` is INTERNED against a local cache scoped to this
+        call, so the (far smaller) set of distinct ticker strings is held ONCE rather than once per
+        horizon-observation. Indexing/iterating it yields the historical `(run_id, ticker, values_tuple)`
+        shape on demand, so existing callers and oracles are unaffected.
+      - `pools[h]` (`_FactorObsPool`): the genuinely per-horizon-specific data — `core_idx` (indexing
+        `core_records`), `realized_return`, `max_drawdown` — held as parallel columns; iterating it yields
+        the historical `(core_idx, realized_return, max_drawdown)` tuples on demand.
       Neither the run-id chunking below nor the "ONE shared read serves every factor at every horizon"
       property changes: `core_records` is built lazily on the FIRST horizon a result has an FR at (same
       trigger the old `values` dict used), so this remains ONE pass over `ScannerResult`, never a per-horizon
@@ -939,8 +1125,12 @@ def _all_factor_observations_by_horizon(
     pool_cap = research_cfg.factor_pool_max_observations  # AG-8 disclosure ceiling — never truncates
 
     runs_with_fr = _runs_with_fr(session, horizons, as_of)
-    core_records: list[tuple[int, str, tuple]] = []
-    pools: dict[int, list[tuple[int, float, Optional[float]]]] = {h: [] for h in horizons}
+    # iter-50 AUDIT FIX (B3): columnar accumulators (see the two classes above). Same rows, same order,
+    # same values — a fixed-width encoding instead of one boxed Python object per row, because THESE two
+    # structures (not the per-(factor,horizon) transient built on top of them) are where all five live
+    # `MemoryError` tracebacks land.
+    core_records = _FactorCoreRecords(len(factors))
+    pools: dict[int, _FactorObsPool] = {h: _FactorObsPool() for h in horizons}
     ticker_intern: dict[str, str] = {}  # dedupes repeated ticker strings across the whole sweep (iter-31)
     warned_horizons: set[int] = set()  # one WARNING per horizon — never a per-chunk log storm (iter-31 audit)
     for start in range(0, len(runs_with_fr), run_chunk):
@@ -960,10 +1150,11 @@ def _all_factor_observations_by_horizon(
                 if core_idx is None:
                     values = tuple(_extract_factor_value(res, parsed) for parsed in parsed_by_key.values())
                     ticker = ticker_intern.setdefault(res.ticker, res.ticker)
-                    core_idx = len(core_records)
-                    core_records.append((res.run_id, ticker, values))
+                    # `append` returns the index it assigned — the SAME value `len(core_records)` produced
+                    # before the columnar encoding, so `pools`' back-references are byte-identical.
+                    core_idx = core_records.append(res.run_id, ticker, values)
                 realized, max_drawdown = fr
-                pools[h].append((core_idx, realized, max_drawdown))
+                pools[h].append(core_idx, realized, max_drawdown)
         # `fr_by_h` is rebound (not accumulated into) on the next iteration — this slice's maps are eligible
         # for GC before the next chunk's query even starts (the bounded-memory guarantee, unchanged iter-29).
         #
@@ -984,9 +1175,57 @@ def _all_factor_observations_by_horizon(
                     "truncation",
                     h, len(pool), pool_cap,
                 )
+    # ops-hardening iter-50 AUDIT FIX (B4) — AG-8 disclosure for the OTHER data-shape axis: a `record_json`
+    # component whose `raw` is not a real number at all is excluded exactly like a factor-NULL (see
+    # `_FactorCoreRecords.append`), never fabricated and never a 500. Unlike the pool-size ceiling above this
+    # one is safe to check after the sweep: a non-numeric value cannot raise out of the loop it would need to
+    # pre-announce — it is handled inline — so there is no crash for an after-the-loop check to miss.
+    if core_records.n_non_numeric:
+        logger.warning(
+            "research factor pool: %d stored factor value(s) were not real numbers (a record_json "
+            "component `raw` of a non-numeric shape) and were EXCLUDED as factor-NULL observations, "
+            "never fabricated — AG-8 data-shape disclosure; every other observation is unaffected",
+            core_records.n_non_numeric,
+        )
     return core_records, pools
 
 
+# ops-hardening iter-50 (J-07, AG-8): a memory-lean stand-in for the per-(factor,horizon) observation dict
+# `compute_factor_lab_all` used to build (a `__slots__` object costs roughly a third of a small dict's
+# footprint per instance — no hash table, just slot pointers) while still answering `o["key"]` / `o.get
+# ("key")` exactly the way the SHARED `_deciles` builder (untouched by this change, still a dict-contract
+# caller used by `compute_factor_lab` / `_regime_effectiveness` / the Regime & Phase-Severity labs) expects
+# — so bounding this loop's own transient footprint introduces NO second decile/rank-IC derivation (still
+# ONE computation path, per this function's own docstring). Mirrors `_SubjectResultRow`'s established
+# `__slots__` precedent (line ~1487) for the SAME class of transient-row memory bound.
+class _FactorLabAllObs:
+    __slots__ = ("run_id", "ticker", "factor", "return_", "max_drawdown")
+
+    def __init__(self, run_id, ticker, factor, return_, max_drawdown):
+        self.run_id = run_id
+        self.ticker = ticker
+        self.factor = factor
+        self.return_ = return_
+        self.max_drawdown = max_drawdown
+
+    def __getitem__(self, key):
+        # `_deciles` reads `m["return"]` / `m["factor"]` — "return" cannot be a Python attribute name (it
+        # is a reserved keyword), so the dict-style lookup maps it to the `return_` slot; every other key
+        # is a direct attribute.
+        if key == "return":
+            return self.return_
+        try:
+            return getattr(self, key)
+        except AttributeError:
+            raise KeyError(key)
+
+    def get(self, key, default=None):
+        try:
+            return self[key]
+        except KeyError:
+            return default
+
+
 def compute_factor_lab_all(
     session: Session, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
 ) -> dict:
@@ -1019,6 +1258,12 @@ def compute_factor_lab_all(
     horizons = list(wf.horizons)
     default_h = wf.default_horizon
 
+    # lazy import — app.engine.data_manager imports FROM this module (_dataset_version /
+    # _membership_dataset_version / event_study_cached / subject_catalog), so a module-level import back
+    # would be circular (mirrors forward_testing.py's own lazy import of research internals). Used only for
+    # the test-only `_fault_inject_memory_error` hook below (a no-op in production).
+    from app.engine import data_manager
+
     core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
     # position of each factor inside `core_records[i][2]`'s values tuple — built from the SAME `factors`
     # list (in the SAME order) `_all_factor_observations_by_horizon` used to build that tuple (iter-31).
@@ -1037,24 +1282,67 @@ def compute_factor_lab_all(
             # compute_factor_lab(factor, h) exactly. The paired drawdown rides along verbatim. `core_records`
             # holds the (run_id, ticker, values) identity SHARED across every horizon a result touches — only
             # `ret`/`max_drawdown` are genuinely per-horizon (iter-31 compact-encoding return-value bound).
-            obs = []
-            for core_idx, ret, max_drawdown in pools[h]:
-                factor_value = core_records[core_idx][2][idx]
-                if factor_value is None:
-                    continue
-                run_id, ticker, _values = core_records[core_idx]
-                obs.append({
-                    "run_id": run_id, "ticker": ticker,
-                    "factor": float(factor_value), "return": ret, "max_drawdown": max_drawdown,
-                })
-            # ascending by stored factor value; SAME deterministic tie-break compute_factor_lab uses.
-            ordered = sorted(obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
-            deciles = _deciles(ordered, fl.deciles, wf.min_sample)
+            #
+            # ops-hardening iter-50 (J-07, AG-8): this obs-build + sort is the CONFIRMED live crash frame
+            # (iter-49's own traceback: an uncaught MemoryError here, then a dict-based `sorted(obs, ...)`)
+            # — a live `/research/factor-lab?all=true` view can run concurrently with the boot re-warm /
+            # ingest finalize tail's own heavy loops. `_FactorLabAllObs` (a `__slots__` stand-in, above)
+            # bounds the per-observation footprint; the try/except mirrors `evidence.py`'s per-claim
+            # isolate-and-continue convention (NOT the ingest warm loops' break-on-MemoryError convention —
+            # that one is for a background loop that can defer; this is a live request that must still
+            # answer): on a MemoryError, THIS horizon's entry alone degrades to an honest
+            # `status: "unavailable"` (no deciles, n_total 0) and the loop continues to the next
+            # horizon/factor — every OTHER entry still renders normally, never a blanked whole-response.
+            try:
+                data_manager._fault_inject_memory_error("factor_lab_all")  # test-only; a no-op in production
+                obs: list[_FactorLabAllObs] = []
+                # iter-50 AUDIT FIX (B3): read the shared pool through the columnar accessors instead of
+                # unpacking a materialised `(core_idx, ret, max_drawdown)` tuple per row and re-indexing a
+                # nested `values` tuple. Same rows, same order, same values — this walk never builds a
+                # transient object per pool row, so the only per-observation allocation left in this loop is
+                # the `_FactorLabAllObs` actually kept in `obs`.
+                _pool = pools[h]
+                _core_run_ids, _core_tickers = core_records.run_ids, core_records.tickers
+                _vals, _has = core_records.value_cols[idx], core_records.value_present[idx]
+                for k in range(len(_pool)):
+                    core_idx = _pool.core_idx[k]
+                    if not _has[core_idx]:
+                        continue  # factor-NULL observation — EXCLUDED, never bucketed (unchanged)
+                    obs.append(_FactorLabAllObs(
+                        _core_run_ids[core_idx], _core_tickers[core_idx], float(_vals[core_idx]),
+                        _pool.realized(k), _pool.max_drawdown(k),
+                    ))
+                # ascending by stored factor value; SAME deterministic tie-break compute_factor_lab uses.
+                ordered = sorted(obs, key=lambda o: (o.factor, o.ticker, o.run_id))
+                deciles = _deciles(ordered, fl.deciles, wf.min_sample)
+            except MemoryError as exc:
+                logger.exception(
+                    "compute_factor_lab_all: obs-build/sort aborted under memory pressure for factor=%s "
+                    "horizon=%s -- isolate-and-continue (AG-8), degrading THIS (factor,horizon) entry "
+                    "honestly rather than the whole all-factors response: %s", factor.key, h, exc,
+                )
+                by_horizon.append({"horizon": h, "n_total": 0, "deciles": [], "status": "unavailable"})
+                continue
+            except Exception as exc:  # noqa: BLE001 — ops-hardening iter-50 AUDIT FIX (B4, AG-8)
+                # The MemoryError catch above was the ONLY handler on this loop, so any OTHER exception
+                # from one (factor,horizon) entry still 500'd the entire `?all=true` response — a blank
+                # application-error page for all 11 factors because of one entry, which AG-8 forbids.
+                # `evidence.py`'s per-claim convention (the precedent this loop already follows for
+                # MemoryError) pairs its MemoryError catch with exactly this broader one, degrading the
... [diff_bound] apps/backend/app/engine/research.py: 184 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index 57a18558..4f3bd948 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -181,11 +181,38 @@ def _warm_drawdown_expectations(engine: Engine, cfg: Config) -> None:
     step is expensive, and the readiness badge J-04 and J-07 step 1 depend on must flip `Ready` on exactly
     the schedule it did before this fix — so this warm is deliberately OUTSIDE the readiness path. The
     consequence is disclosed honestly: an Evidence view landing inside the short window between `ok` and
-    this warm's completion still pays the cold miss."""
+    this warm's completion still pays the cold miss.
+
+    ops-hardening iter-50 (J-07): guarded by `data_manager`'s shared warm-in-progress slot — this warm and
+    the ingest finalize tail's OWN drawdown-expectations warm phase (`data_manager._refresh_ingest_
+    aggregates`) must never run their heavy per-claim loops concurrently in the same process (the second
+    proven-concurrent crash contributor from iter-49's own traceback read: three heavy loops were live at
+    once — the finalize tail, this boot re-warm, and a live Factor Lab request). A loss here defers this
+    ENTIRE warm (zero claims attempted) rather than racing the finalize tail for the same memory headroom —
+    non-fatal (this function already never raises), and the next boot/restart retries.
+
+    ops-hardening iter-50 AUDIT FIX (finding B2): that slot alone was too narrow — it interlocked only the
+    two drawdown per-claim loops, while the finalize tail's `forward_aggregates_warm` (337-385s live) and
+    `coverage_membership_timeline_refresh` (82.04s live) were free to run concurrently with THIS loop, which
+    is exactly the overlap the 2026-08-05 outage window sat inside. This warm now ALSO yields to the whole
+    ingest heavy-warm window (`data_manager._ingest_heavy_warm_active`), and — because one claim can itself
+    run for minutes — it re-checks BEFORE EVERY CLAIM, stopping early if a window opens mid-loop. Yielding
+    is the right asymmetry here: the finalize tail's warms are the J-05 product contract, while this one is
+    a best-effort pre-warm whose only cost when skipped is a cold miss on the first `/evidence` view."""
+    if data_manager._ingest_heavy_warm_active():
+        logger.info(
+            "evidence drawdown-expectations warm deferred -- an ingest finalize-tail heavy-warm window is "
+            "open in this process (iter-50 audit B2); retried on the next boot/restart"
+        )
+        return
+    if not data_manager._try_acquire_drawdown_warm("boot_rewarm"):
+        return  # deferred -- another warm (the ingest finalize tail) is already live in this process;
+                # the guard's own log line records why. Retried on the next boot/restart.
     try:
         entries = read_entries(evidence.resolve_ledger_path())
     except Exception as exc:  # NON-FATAL: a missing/corrupt ledger degrades to zero warm calls
         logger.exception("evidence drawdown-expectations ledger read failed (non-fatal): %s", exc)
+        data_manager._release_drawdown_warm()
         return
     warmed = 0
     try:
@@ -193,6 +220,18 @@ def _warm_drawdown_expectations(engine: Engine, cfg: Config) -> None:
             for entry in entries:
                 if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
                     continue
+                # iter-50 AUDIT FIX (B2): re-checked BEFORE EVERY CLAIM, not just at entry. An ingest job
+                # can start its finalize tail at any point during this multi-minute loop, and a start-only
+                # check would let the rest of the loop run straight through the overlap the outage sat in.
+                # Stopping here is honest: `warmed` already reflects every claim completed before the yield,
+                # and the untouched claims stay exactly as warm/cold as they were, retried on the next boot.
+                if data_manager._ingest_heavy_warm_active():
+                    logger.info(
+                        "evidence drawdown-expectations warm yielding after %d claim panels -- an ingest "
+                        "finalize-tail heavy-warm window opened (iter-50 audit B2); the remaining claims "
+                        "are retried on the next boot/restart", warmed,
+                    )
+                    break
                 claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
                 try:
                     if forward_testing.compute_drawdown_expectations_cached(session, claim, cfg) is not None:
@@ -219,6 +258,11 @@ def _warm_drawdown_expectations(engine: Engine, cfg: Config) -> None:
         logger.info("evidence drawdown-expectations cache warmed (%d claim panels)", warmed)
     except Exception as exc:  # NON-FATAL: must never fail the otherwise-successful warm-up
         logger.exception("evidence drawdown-expectations cache warm failed (non-fatal): %s", exc)
+    finally:
+        # ops-hardening iter-50 (J-07): release the shared warm-in-progress slot whether this warm
+        # succeeded or raised — this call only runs when the acquire above actually won it (the two
+        # early-return paths above release it themselves before returning), so the slot never wedges.
+        data_manager._release_drawdown_warm()
 
 
 def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -> None:
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index a41483b6..d67041f7 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -32,7 +32,7 @@ from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
 from app.engine import data_manager
-from app.engine import forward_testing, indexes, market_phase, scanner
+from app.engine import forward_testing, indexes, market_phase, scanner, warmup
 from app.engine.data_manager import (
     JobProgress,
     _chunk_plan,
@@ -2147,6 +2147,388 @@ def test_finalize_hook_sub_phase_timing_names_each_horizon_and_claim_and_memoize
     )
 
 
+# ==================================================================================================
+# ops-hardening iter-50 (J-07): the shared warm-in-progress guard between the boot/re-warm path
+# (`warmup._warm_drawdown_expectations`) and THIS module's own `_refresh_ingest_aggregates`
+# drawdown-expectations warm phase — the two proven-concurrent crash contributors from iter-49's own
+# traceback read. TC-4/TC-5 prove the guard holds in BOTH trigger orders; TC-6 proves the
+# `phase_context_by_date` precompute is skipped entirely once the ledger is fully cache-warm.
+# ==================================================================================================
+def test_drawdown_warm_guard_boot_rewarm_defers_when_ingest_already_in_flight(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
+):
+    """TC-4 — the boot/re-warm path (`warmup._warm_drawdown_expectations`) defers ENTIRELY (no claim
+    attempted) when the ingest finalize tail's OWN drawdown-expectations warm phase already holds the
+    shared warm-in-progress slot — proven by simulating "ingest already in flight" via a direct acquire,
+    then calling the boot re-warm and asserting it neither reads the ledger's real compute path nor warms
+    anything, and logs the deferral naming which caller deferred. Once the slot is released, a normal
+    boot re-warm proceeds and actually warms the claim (proving this is a real defer, not a permanent
+    disable)."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+
+    claim_calls: list[str] = []
+    real_compute = forward_testing.compute_drawdown_expectations_cached
+
+    def _spy(*a, **k):
+        claim_calls.append("called")
+        return real_compute(*a, **k)
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _spy)
+
+    assert data_manager._try_acquire_drawdown_warm("ingest_finalize") is True  # simulate "already in flight"
+    try:
+        with caplog.at_level("INFO", logger="trendora.data_manager"):
+            warmup._warm_drawdown_expectations(engine, cfg)  # must not raise, must not block
+        assert claim_calls == [], "the boot re-warm must not attempt any claim while the guard is held"
+        assert any(
+            "deferring" in r.getMessage() and "boot_rewarm" in r.getMessage() for r in caplog.records
+        ), f"expected a deferral log line naming boot_rewarm; got {[r.getMessage() for r in caplog.records]}"
+    finally:
+        data_manager._release_drawdown_warm()
+
+    # after release, a normal boot re-warm proceeds and actually warms the claim.
+    warmup._warm_drawdown_expectations(engine, cfg)
+    assert claim_calls == ["called"], "once the slot is free, the boot re-warm must proceed normally"
+
+
+def test_drawdown_warm_guard_ingest_finalize_defers_when_boot_rewarm_already_in_flight(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
+):
+    """TC-5 — the guard holds in the OTHER trigger order: the ingest finalize tail's own
+    drawdown-expectations warm phase (inside `_refresh_ingest_aggregates`) defers when the boot/re-warm
+    path already holds the shared slot — "drawdown_expectations" is honestly absent from `refreshed` (no
+    claim attempted), `phase_context_by_date` is never called, and every OTHER finalize-hook category
+    still refreshes normally (the guard scopes ONLY this one phase). Releasing the slot lets a normal
+    finalize run warm the claim as before."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+
+    phase_ctx_calls = {"n": 0}
+    real_phase_ctx = market_phase.phase_context_by_date
+
+    def _counting_phase_ctx(session=None, as_of=None, config=None):
+        phase_ctx_calls["n"] += 1
+        return real_phase_ctx(session, as_of=as_of, config=config)
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _counting_phase_ctx)
+
+    assert data_manager._try_acquire_drawdown_warm("boot_rewarm") is True  # simulate "already in flight"
+    try:
+        with Session(engine) as session:
+            prog = JobProgress(job_id="dd-guard-ingest-defers", kind="backfill", start=d, end=d)
+            prog.new_snapshot_dates = [d]
+            with caplog.at_level("INFO", logger="trendora.data_manager"):
+                refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    finally:
+        data_manager._release_drawdown_warm()
+
+    assert "drawdown_expectations" not in refreshed, f"deferred phase must be honestly absent; got {refreshed}"
+    assert {"coverage", "membership_timeline"} <= set(refreshed), (
+        f"every OTHER category must still refresh normally; refreshed={refreshed}"
+    )
+    assert phase_ctx_calls["n"] == 0, "a deferred phase must never call phase_context_by_date"
+    assert any(
+        "deferring" in r.getMessage() and "ingest_finalize" in r.getMessage() for r in caplog.records
+    ), f"expected a deferral log line naming ingest_finalize; got {[r.getMessage() for r in caplog.records]}"
+
+    # after release, a normal finalize run proceeds and actually warms the claim as before.
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-guard-ingest-recovers", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed2 = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "drawdown_expectations" in refreshed2, "once the slot is free, the finalize phase must proceed"
+
+
+# ==================================================================================================
+# ops-hardening iter-50 AUDIT FIX (finding B2) — the interlock above was aimed at the pair that did not
+# collide. It guards ONLY the two drawdown-expectations per-claim loops against each other, while the
+# finalize tail's `forward_aggregates_warm` (measured 337-385s live) and
+# `coverage_membership_timeline_refresh` (82.04s live) stayed free to run concurrently with the boot
+# re-warm's per-claim loop — and that overlap is exactly where the 2026-08-05 outage window sat.
+# `logs/backend.log` shows the narrow guard FIRING and NOT HELPING at 23:04:01,255 ("drawdown-expectations
+# warm-in-progress guard: ingest_finalize deferring") while that same job's UNGUARDED
+# `forward_aggregates_warm` had been running since 22:57:37.
+#
+# The widened interlock covers the WHOLE ingest finalize-tail heavy-warm window and is deliberately
+# ASYMMETRIC: the finalize tail is the priority producer (its warms ARE the J-05 contract) and never
+# defers; the boot re-warm — a best-effort pre-warm that is already "non-fatal, retried next boot" —
+# yields, both at entry AND before every claim.
+# ==================================================================================================
+@pytest.fixture(autouse=True)
+def _reset_ingest_heavy_warm_window():
+    """The heavy-warm window depth is MODULE state (deliberately — it must be visible across threads in one
+    process). Reset it around every test so a failed assertion can never leave the whole file's remaining
+    tests running against a permanently-open window."""
+    data_manager._INGEST_HEAVY_WARM_DEPTH = 0
+    yield
+    data_manager._INGEST_HEAVY_WARM_DEPTH = 0
+
+
+def _write_dd_ledger(tmp_path, monkeypatch, n_claims: int = 1):
+    """A ledger carrying `n_claims` DISTINCT resolvable claims (distinct by `slice_kind`, so each is its own
+    cache subject) — `n_claims >= 2` is what makes a mid-loop yield observable."""
+    ledger = tmp_path / "certified-claims.jsonl"
+    for i in range(n_claims):
+        claim = dict(_DD_LEDGER_CLAIM)
+        if i:
+            claim["slice_kind"] = f"total_{i}"
+        append_entry(str(ledger), {
+            "claim": claim, "register_date": "2024-06-01",
+            "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+        })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    return ledger
+
+
+def test_boot_rewarm_defers_for_the_whole_ingest_heavy_warm_window(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
+):
+    """iter-50 audit B2 — the boot re-warm defers for the WHOLE ingest finalize-tail heavy-warm window, not
+    only when the narrow drawdown slot happens to be held.
+
+    Teeth: the narrow slot is deliberately left FREE here (`_try_acquire_drawdown_warm` would succeed), so
+    the pre-fix guard would have let this warm run straight through — which is precisely the overlap the
+    outage sat in (the boot re-warm running while the finalize tail's `forward_aggregates_warm` ran)."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    _write_dd_ledger(tmp_path, monkeypatch)
+
+    claim_calls: list[str] = []
+    real_compute = forward_testing.compute_drawdown_expectations_cached
+    monkeypatch.setattr(
+        forward_testing, "compute_drawdown_expectations_cached",
+        lambda *a, **k: (claim_calls.append("called"), real_compute(*a, **k))[1],
+    )
+
+    data_manager._enter_ingest_heavy_warm("job-under-test")
+    try:
+        assert not data_manager._DRAWDOWN_WARM_IN_PROGRESS, (
+            "fixture sanity: the NARROW drawdown slot must be free, so this test proves the WIDENED "
+            "window is what defers the boot re-warm"
+        )
+        with caplog.at_level("INFO", logger="trendora.warmup"):
+            warmup._warm_drawdown_expectations(engine, cfg)  # must not raise, must not block
+        assert claim_calls == [], (
+            "the boot re-warm must attempt zero claims while an ingest heavy-warm window is open"
+        )
+        assert any(
+            "deferred" in r.getMessage() and "heavy-warm window" in r.getMessage()
+            for r in caplog.records
+        ), f"expected a deferral log line naming the window; got {[r.getMessage() for r in caplog.records]}"
+    finally:
+        data_manager._exit_ingest_heavy_warm("job-under-test")
+
+    # a real defer, not a permanent disable: once the window closes the boot re-warm proceeds normally.
+    warmup._warm_drawdown_expectations(engine, cfg)
+    assert claim_calls == ["called"], "once the window closes, the boot re-warm must proceed normally"
+
+
+def test_boot_rewarm_yields_mid_loop_when_an_ingest_window_opens(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
+):
+    """iter-50 audit B2 — an entry-only check is not enough. A single claim can run for minutes (worst
+    observed on the live ledger: the ~250s `combination:composite:h20`), so an ingest job that starts its
+    finalize tail mid-loop would otherwise overlap every REMAINING claim. The boot re-warm re-checks before
+    every claim and stops early.
+
+    Teeth: the window is opened from INSIDE the first claim's compute, so a start-only check would let all
+    three claims run and this assertion would see 3 calls instead of 1."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    _write_dd_ledger(tmp_path, monkeypatch, n_claims=3)
+
+    claim_calls: list[str] = []
+    real_compute = forward_testing.compute_drawdown_expectations_cached
+
+    def _open_window_during_first_claim(*a, **k):
+        claim_calls.append("called")
+        if len(claim_calls) == 1:
+            data_manager._enter_ingest_heavy_warm("job-starting-mid-loop")
+        return real_compute(*a, **k)
+
+    monkeypatch.setattr(
+        forward_testing, "compute_drawdown_expectations_cached", _open_window_during_first_claim
+    )
+
+    try:
+        with caplog.at_level("INFO", logger="trendora.warmup"):
+            warmup._warm_drawdown_expectations(engine, cfg)
+    finally:
+        data_manager._exit_ingest_heavy_warm("job-starting-mid-loop")
+
+    assert len(claim_calls) == 1, (
+        f"the boot re-warm must yield as soon as an ingest heavy-warm window opens; it attempted "
+        f"{len(claim_calls)} claims (3 = it never re-checked after the first)"
+    )
+    assert any("yielding" in r.getMessage() for r in caplog.records), (
+        f"expected a mid-loop yield log line; got {[r.getMessage() for r in caplog.records]}"
+    )
+
+
+def test_ingest_finalize_declares_a_heavy_warm_window_across_its_whole_tail(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
+):
+    """iter-50 audit B2 — the window must span the WHOLE finalize tail, including the phases the narrow
+    drawdown slot never covered. Observed from inside `forward_aggregates_ingest_cached` (the phase measured
+    at 337-385s live, and the one that was actually running during the outage) and from inside the coverage/
+    membership refresh — a window opened only around the drawdown phase would fail both probes. Also
+    asserts the window is CLOSED again afterwards, so a finished job can never leave the boot re-warm
+    permanently deferred."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    _write_dd_ledger(tmp_path, monkeypatch)
+
+    seen: dict[str, bool] = {}
+    real_fa = forward_testing.forward_aggregates_ingest_cached
+    real_cov = data_manager.refresh_coverage_snapshot
+
+    def _probe_fa(*a, **k):
+        seen["forward_aggregates_warm"] = data_manager._ingest_heavy_warm_active()
+        return real_fa(*a, **k)
+
+    def _probe_cov(*a, **k):
+        seen["coverage_membership_timeline_refresh"] = data_manager._ingest_heavy_warm_active()
+        return real_cov(*a, **k)
+
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _probe_fa)
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _probe_cov)
+
+    assert not data_manager._ingest_heavy_warm_active(), "no window may be open before the job starts"
+    with Session(engine) as session:
+        prog = JobProgress(job_id="heavy-warm-window", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert seen.get("forward_aggregates_warm") is True, (
+        "the heavy-warm window must be OPEN during forward_aggregates_warm — the phase measured at "
+        f"337-385s live and running during the 2026-08-05 outage; observed: {seen}"
+    )
+    assert seen.get("coverage_membership_timeline_refresh") is True, (
+        f"the heavy-warm window must be OPEN during the coverage/membership refresh (82.04s live); "
+        f"observed: {seen}"
+    )
+    assert not data_manager._ingest_heavy_warm_active(), (
+        "the window must be CLOSED when the finalize tail returns — otherwise one job would defer every "
+        "future boot re-warm in this process"
+    )
+    assert data_manager._INGEST_HEAVY_WARM_DEPTH == 0, "the window depth must unwind to exactly zero"
+
+
+def test_ingest_heavy_warm_window_closes_even_when_a_phase_raises(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
+):
+    """iter-50 audit B2 — the window is closed in a `finally`. If an unexpected failure could leave it open,
+    a single bad job would silently disable the boot re-warm for the rest of the process's life (a
+    permanent, invisible regression of the J-06 post-restart Evidence warm). Teeth: the probe raises a
+    non-MemoryError from inside a heavy phase — the class `_refresh_ingest_aggregates` isolates per phase —
+    and the depth must still unwind to zero."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    _write_dd_ledger(tmp_path, monkeypatch)
+
+    def _boom(*a, **k):
+        raise RuntimeError("simulated phase failure")
+
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
+
+    with Session(engine) as session:
+        prog = JobProgress(job_id="heavy-warm-window-raises", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert "forward_aggregates" not in refreshed, "a failed phase must be honestly absent from refreshed"
+    assert data_manager._INGEST_HEAVY_WARM_DEPTH == 0, (
+        "the heavy-warm window must unwind to zero even when a phase raises — otherwise one bad job "
+        "permanently disables the boot re-warm"
+    )
+
+
+def test_drawdown_expectations_phase_context_skipped_when_ledger_fully_cache_warm(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
+):
+    """TC-6 — a SECOND finalize invocation, same ledger/claim, no new data: every claim is already a cache
+    HIT for the current dataset version, so `phase_context_by_date` is skipped ENTIRELY (never invoked) on
+    the second call — closing the ~23.6-23.9s measured MID health-poll-stall cluster (`reports/perf-
+    budgets.md` Item R Addendum 6) for the common "nothing new to compute" case. The FIRST call (a genuine
+    cache MISS) still calls it exactly once, proving this is a real skip, not a permanently-disabled
+    precompute."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+
+    phase_ctx_calls = {"n": 0}
+    real_phase_ctx = market_phase.phase_context_by_date
+
+    def _counting_phase_ctx(session=None, as_of=None, config=None):
+        phase_ctx_calls["n"] += 1
+        return real_phase_ctx(session, as_of=as_of, config=config)
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _counting_phase_ctx)
+
+    with Session(engine) as session:
+        prog1 = JobProgress(job_id="dd-skip-first", kind="backfill", start=d, end=d)
+        prog1.new_snapshot_dates = [d]
+        refreshed1 = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
+    assert "drawdown_expectations" in refreshed1, f"fixture sanity: the claim must genuinely warm; got {refreshed1}"
+    assert phase_ctx_calls["n"] == 1, "the FIRST (cache-MISS) call must compute the timeline exactly once"
+
+    with Session(engine) as session:
+        prog2 = JobProgress(job_id="dd-skip-second", kind="backfill", start=d, end=d)
+        prog2.new_snapshot_dates = [d]
+        refreshed2 = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
+    assert "drawdown_expectations" in refreshed2, (
+        f"the claim is still a HIT, still honestly reported as warm; got {refreshed2}"
+    )
+    assert phase_ctx_calls["n"] == 1, (
+        "the SECOND call (every claim already cache-HIT) must skip phase_context_by_date entirely — "
+        f"call count grew to {phase_ctx_calls['n']}"
+    )
+
+
+def test_drawdown_expectations_needs_recompute_helper_directly(finalize_hook_drawdown_engine, tmp_path, monkeypatch):
+    """TC-6 (unit-level) — `_drawdown_expectations_ledger_needs_recompute` directly: an empty ledger and a
+    ledger whose sole claim is already cache-HIT both report False (nothing needs it); a ledger with a
+    genuinely uncached claim reports True."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+
+    with Session(engine) as session:
+        assert data_manager._drawdown_expectations_ledger_needs_recompute(session, [], cfg) is False
+
+        uncached_entry = {"claim": _DD_LEDGER_CLAIM}
+        assert data_manager._drawdown_expectations_ledger_needs_recompute(
+            session, [uncached_entry], cfg
+        ) is True
+
+        # warm it for real via the canonical cached path, then re-check — must now report False.
+        forward_testing.compute_drawdown_expectations_cached(session, _DD_LEDGER_CLAIM, cfg)
+        assert data_manager._drawdown_expectations_ledger_needs_recompute(
+            session, [uncached_entry], cfg
+        ) is False
+
+        # a forward-walk monitoring record is not a claim to warm a panel for — never "needs" a compute.
+        fw_entry = {"type": "forward_walk", "claim": _DD_LEDGER_CLAIM}
+        assert data_manager._drawdown_expectations_ledger_needs_recompute(session, [fw_entry], cfg) is False
+
+
 # ==================================================================================================
... [diff_bound] apps/backend/tests/test_data_manager.py: 44 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_factor_lab_all.py b/apps/backend/tests/test_factor_lab_all.py
index ff76cafd..755417ec 100644
--- a/apps/backend/tests/test_factor_lab_all.py
+++ b/apps/backend/tests/test_factor_lab_all.py
@@ -915,7 +915,14 @@ _MIN_REDUCTION_VS_PRE_FIX = 1.5
 def _deep_size(obj) -> int:
     """Resident bytes of an object graph: every container AND the scalars it references, deduped BY IDENTITY
     (so a shared `values` tuple, an interned ticker, or a cached small int is counted ONCE — exactly how the
-    process holds them). Deterministic: no clock, no GC timing, no tracemalloc sampling."""
+    process holds them). Deterministic: no clock, no GC timing, no tracemalloc sampling.
+
+    ops-hardening iter-50 AUDIT FIX (finding B3): the walker now descends into `__slots__` objects too.
+    Without this it would stop at `sys.getsizeof(<_FactorCoreRecords instance>)` — a few dozen bytes of
+    object header, none of the buffers it points at — and every projection assertion built on it would pass
+    VACUOUSLY for any structure whose payload hangs off slots. `array.array` / `bytearray` report their whole
+    buffer through `sys.getsizeof`, so descending one level into the slots charges every byte the process
+    actually holds."""
     seen: set[int] = set()
     stack = [obj]
     total = 0
@@ -930,6 +937,13 @@ def _deep_size(obj) -> int:
             stack.extend(o.values())
         elif isinstance(o, (list, tuple, set, frozenset)):
             stack.extend(o)
+        else:
+            for cls in type(o).__mro__:
+                for slot in getattr(cls, "__slots__", ()):
+                    try:
+                        stack.append(getattr(o, slot))
+                    except AttributeError:
+                        pass
     return total
 
 
@@ -995,6 +1009,116 @@ def test_returned_pool_structure_projected_to_the_live_basis_stays_under_the_mem
     )
 
 
+# ops-hardening iter-50 AUDIT FIX (finding B3). The projection test above guards the iter-31 redesign
+# against a revert to the PRE-iter-31 dict shape — but reverting only iter-50's columnar encoding back to
+# iter-31's boxed tuples still clears its 1.5x floor comfortably, so it has no teeth on THIS fix. These
+# floors pin the columnar encoding specifically, measured against the iter-31 tuple encoding rebuilt from
+# the SAME returned data (so any divergence can only come from the encoding itself).
+#
+# Both are deliberately well BELOW the measured margins because this fixture understates the win: with 20
+# core records and 80 pool rows, the fixed ~64-byte header of each `array`/`bytearray` is amortised over
+# almost nothing, while at the live basis (781,417 core records / 3,971,375 pool rows) it vanishes and the
+# per-pool-row cost approaches its raw 8+8+1+8+1 = 26 bytes against the tuple encoding's ~128. Reverting to
+# the tuple encoding scores exactly 1.0x on both and fails here.
+_MIN_REDUCTION_VS_ITER31_TOTAL = 1.35    # measured on this fixture: ~1.67x
+_MIN_REDUCTION_VS_ITER31_POOL_ROW = 1.6  # measured on this fixture: ~2.03x
+
+
+def test_returned_pool_structure_is_columnar_not_boxed_python_objects(lab_engine):
+    """iter-50 audit B3 — the accumulators `_all_factor_observations_by_horizon` RETURNS must be columnar
+    fixed-width buffers, not one boxed Python object per row.
+
+    WHY THIS TEST EXISTS: iter-50 shipped believing this function was "already bounded … unaffected by this
+    defect" (its own phase spec's carve-out). The live evidence said otherwise — five real, un-injected
+    `MemoryError`s on 2026-08-05 (23:28:44 / 23:37:53 / 23:38:25 / 23:42:07 / 23:44:52) carry the identical
+    traceback ending at `pools[h].append(...)` in THIS function, and none at the per-(factor,horizon)
+    transient the iteration actually bounded. "Chunked source reads" bounded the QUERY side only; the
+    RETURN VALUE was O(observations) in boxed Python objects and stayed resident for the whole call.
+
+    Two independent teeth: a structural assertion (the buffers really are `array`/`bytearray`, so an
+    encoding that merely renames the tuples cannot pass) and a measured one (the resident cost per pool row
+    and the whole-structure projection must both beat the iter-31 tuple encoding by a stated factor)."""
+    from array import array as _array
+
+    cfg = load_config()
+    factors = list(cfg.research.factor_lab.factors)
+    horizons = list(cfg.walk_forward.horizons)
+    with Session(lab_engine) as session:
+        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)
+
+    pool_rows = sum(len(p) for p in pools.values())
+    assert core_records and pool_rows, "fixture produced no observations — the measurement would be vacuous"
+
+    # --- structural: fixed-width buffers, not per-row Python objects ------------------------------------
+    assert isinstance(core_records.run_ids, _array), "core-record run ids must be a fixed-width array"
+    assert all(isinstance(c, _array) for c in core_records.value_cols), "factor values must be array columns"
+    assert all(isinstance(m, bytearray) for m in core_records.value_present), "null masks must be bytearrays"
+    for h, pool in pools.items():
+        assert isinstance(pool.core_idx, _array), f"horizon {h}: pool core_idx must be a fixed-width array"
+        assert isinstance(pool.returns, _array), f"horizon {h}: pool returns must be a fixed-width array"
+        assert isinstance(pool.max_drawdowns, _array), f"horizon {h}: pool drawdowns must be an array"
+
+    # --- measured: beat the iter-31 boxed-tuple encoding rebuilt from the SAME data ---------------------
+    iter31_core = [(cr[0], cr[1], cr[2]) for cr in core_records]
+    iter31_pools = {h: [(i, ret, mdd) for (i, ret, mdd) in pool] for h, pool in pools.items()}
+
+    per_core = _deep_size(core_records) / len(core_records)
+    per_pool_row = _deep_size(pools) / pool_rows
+    iter31_per_core = _deep_size(iter31_core) / len(iter31_core)
+    iter31_per_pool_row = _deep_size(iter31_pools) / pool_rows
+
+    assert per_pool_row * _MIN_REDUCTION_VS_ITER31_POOL_ROW <= iter31_per_pool_row, (
+        f"a pool row costs {per_pool_row:.1f} B columnar vs {iter31_per_pool_row:.1f} B as an iter-31 boxed "
+        f"tuple — less than the required {_MIN_REDUCTION_VS_ITER31_POOL_ROW}x reduction at the very "
+        f"`pools[h].append` site all five live MemoryError tracebacks land on"
+    )
+
+    live_pool_rows = sum(_LIVE_POOL_ROWS_BY_HORIZON)
+    projected = per_core * _LIVE_CORE_RECORDS + per_pool_row * live_pool_rows
+    iter31_projected = iter31_per_core * _LIVE_CORE_RECORDS + iter31_per_pool_row * live_pool_rows
+    assert projected * _MIN_REDUCTION_VS_ITER31_TOTAL <= iter31_projected, (
+        f"the columnar structure projects to {projected / (1024 * 1024):.0f} MB at the live basis vs the "
+        f"iter-31 tuple encoding's {iter31_projected / (1024 * 1024):.0f} MB — less than the required "
+        f"{_MIN_REDUCTION_VS_ITER31_TOTAL}x reduction. iter-50's audit-B3 columnar encoding has been "
+        f"reverted or diluted (boxed per-row objects re-introduced?)"
+    )
+
+
+def test_columnar_accumulators_carry_null_and_value_exactly(lab_engine):
+    """iter-50 audit B3 — the columnar encoding stores `None` through a companion presence mask, never a
+    0.0 or NaN sentinel. Teeth: the catalog's unpopulated factors are genuinely NULL in this fixture, so an
+    encoding that conflated NULL with 0.0 would turn an EXCLUDED factor-NULL observation into a real 0.0
+    observation and silently change every decile it lands in (AG-3)."""
+    cfg = load_config()
+    factors = list(cfg.research.factor_lab.factors)
+    horizons = list(cfg.walk_forward.horizons)
+    with Session(lab_engine) as session:
+        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)
+
+    # at least one factor column is entirely NULL in this fixture (the catalog's volatility columns) and at
+    # least one is populated — otherwise the null-carrying assertion below would be vacuous.
+    null_cols = [j for j in range(len(factors)) if not any(core_records.value_present[j])]
+    populated_cols = [j for j in range(len(factors)) if all(core_records.value_present[j])]
+    assert null_cols and populated_cols, "fixture must mix NULL and populated factor columns"
+    for j in null_cols:
+        for i in range(len(core_records)):
+            assert core_records.factor_value(i, j) is None, (
+                f"factor column {j} is NULL for every record but reads back "
+                f"{core_records.factor_value(i, j)!r} — a NULL was conflated with a value"
+            )
+
+    # `max_drawdown` is nullable per horizon: NO_MDD_HORIZON's FRs carry None, the populated ones carry a
+    # real negative figure. Both must round-trip exactly.
+    assert all(pools[NO_MDD_HORIZON].max_drawdown(k) is None for k in range(len(pools[NO_MDD_HORIZON]))), (
+        "horizon with no stored max_drawdown must read back None, never 0.0"
+    )
+    populated = pools[POPULATED_HORIZONS[0]]
+    assert len(populated) > 0 and all(
+        populated.max_drawdown(k) is not None and populated.max_drawdown(k) < 0
+        for k in range(len(populated))
+    ), "a populated horizon's stored negative max_drawdowns must round-trip exactly"
+
+
 def test_factor_pool_cap_warning_lands_even_when_the_sweep_dies_part_way(lab_engine, caplog):
     """iter-31 (audit fix): `config.yaml` promises the ceiling turns a future data-scale widening into "an
     observable log line in logs/backend.log, not another opaque crash". That promise is only true if the
@@ -1043,3 +1167,162 @@ def test_factor_pool_cap_warning_lands_even_when_the_sweep_dies_part_way(lab_eng
     assert caplog.text.count("factor_pool_max_observations exceeded") <= len(horizons), (
         "the disclosure warning is repeating per chunk — it must be emitted once per horizon"
     )
+
+
+# ==================================================================================================
+# 12. iter-50 audit B4 — AG-8 data-shape tolerance of the columnar encoding
+#
+# The B3 columnar accumulators store factor values into `array("d")`, which accepts ONLY a real number.
+# A component factor's value is `record_json[<block>]["components"][i]["raw"]` — FREE-FORM JSON — so a
+# record shape that writes `"raw": "3.5"` (a string) rather than `3.5` used to be served fine (the sole
+# consumer coerced with `float(...)` downstream) and, after the columnar rewrite, raised `TypeError` out
+# of `_all_factor_observations_by_horizon`, where the only handlers on the request path were
+# `except MemoryError` — so it 500'd the WHOLE `?all=true` response. AG-8 forbids exactly that
+# ("must never crash an existing page ... never a blank application-error page").
+# ==================================================================================================
+def _string_raw_engine(tmp_path, *, raw_for):
+    """The SAME shape as `lab_engine` but with each result's `leadership.components.rs_spy_3m.raw` produced
+    by `raw_for(numeric_value)` — so a caller can build the numeric-raw basis and a string-raw (or
+    non-numeric-raw) basis that are otherwise identical row for row."""
+    tmp_path.mkdir(parents=True, exist_ok=True)
+    engine = make_engine(f"sqlite:///{tmp_path / 'lab_all_shape.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
+        for i in range(1, 13):
+            session.add(ScannerResult(
+                run_id=r1.id, ticker=f"A{i:02d}", name=f"A{i:02d}", sector="Technology",
+                leadership_score=float(i * 5), leadership_bucket="C",
+                entry_quality_score=float(100 - i * 3), entry_quality_bucket="C",
+                risk_score=float(i * 4), risk_bucket="C",
+                setup_status="Breakout-watch", rank=i,
+                record_json=json.dumps({
+                    "leadership": {"components": [
+                        {"name": "rs_spy_3m", "raw": raw_for(float(i) / 10.0), "available": True},
+                    ]},
+                    "risk": {"components": [
+                        {"name": "atr_pct", "raw": float(i) / 100.0, "available": True},
+                    ]},
+                }),
+            ))
+            for h in POPULATED_HORIZONS:
+                _add_fr(session, r1.id, f"A{i:02d}", ret=(i - 6) / 100.0 * h, horizon=h, mdd=-(i / 200.0))
+        session.commit()
+    return engine
+
+
+def _rs_spy_3m_entry(payload: dict) -> dict:
+    return next(e for e in payload["factors_table"] if e["key"] == "rs_spy_3m")
+
+
+def test_string_typed_component_raw_is_served_identically_to_a_numeric_raw(tmp_path):
+    """iter-50 audit B4 — a `record_json` component whose `raw` is the STRING `"0.7"` must produce the
+    byte-identical served figures to the same value written as the number `0.7`, exactly as the
+    pre-columnar path did (it stored the raw object and coerced with `float(...)` at the point of use).
+
+    Teeth: without the coercion at the columnar `append` site this does not merely differ — it raises
+    `TypeError: must be real number, not str` out of `_all_factor_observations_by_horizon`, which no
+    handler on the request path catches, so `GET /api/research/factor-lab?all=true` returns 500 for
+    EVERY viewer (AG-8's "never a blank application-error page")."""
+    numeric = _string_raw_engine(tmp_path / "num", raw_for=lambda v: v)
+    stringy = _string_raw_engine(tmp_path / "str", raw_for=lambda v: str(v))
+    cfg = load_config()
+
+    with Session(numeric) as session:
+        numeric_payload = compute_factor_lab_all(session, cfg, as_of=None)
+    with Session(stringy) as session:
+        string_payload = compute_factor_lab_all(session, cfg, as_of=None)
+
+    numeric_entry, string_entry = _rs_spy_3m_entry(numeric_payload), _rs_spy_3m_entry(string_payload)
+    assert numeric_entry["n_total"] > 0, "fixture produced no rs_spy_3m observations — the proof is vacuous"
+    assert _bytes(string_entry) == _bytes(numeric_entry), (
+        "a string-typed component `raw` must serve byte-identically to the same numeric value — the "
+        "columnar encoding must not narrow the data shapes this endpoint tolerates (AG-8)"
+    )
+    # and nothing was quietly dropped: every observation still counted.
+    assert all(
+        bh["n_total"] == next(n["n_total"] for n in numeric_entry["by_horizon"] if n["horizon"] == bh["horizon"])
+        for bh in string_entry["by_horizon"]
+    ), "string-typed raws changed an observation count — values must be coerced, never excluded"
+
+
+@pytest.mark.parametrize("bad_raw", ["n/a", [0.7], {"value": 0.7}])
+def test_non_numeric_component_raw_is_excluded_as_factor_null_never_a_500(tmp_path, caplog, bad_raw):
+    """iter-50 audit B4 — a component `raw` that is not a real number AT ALL is excluded exactly like a
+    factor-NULL observation (`_extract_factor_value`'s own "never fabricated" convention), disclosed by an
+    AG-8 WARNING, and the response still renders every OTHER factor. It must never fabricate a value and
+    must never raise out of the shared pool builder.
+
+    Teeth: the OTHER catalog factors in the same fixture stay fully populated, so a handler that blanked
+    the whole response (or a `float()` that fabricated 0.0) fails here."""
+    engine = _string_raw_engine(tmp_path, raw_for=lambda v: bad_raw)
+    cfg = load_config()
+
+    with caplog.at_level("WARNING", logger="trendora.research"):
+        with Session(engine) as session:
+            payload = compute_factor_lab_all(session, cfg, as_of=None)
+
+    entry = _rs_spy_3m_entry(payload)
+    assert entry["n_total"] == 0 and entry["rank_ic"]["n"] == 0, (
+        f"a non-numeric raw ({bad_raw!r}) must be EXCLUDED as a factor-NULL observation, never coerced "
+        f"into a fabricated number — got n_total={entry['n_total']}"
+    )
+    assert all(d["mean_return"] is None for d in entry["by_horizon"][0]["deciles"]), (
+        "an all-excluded factor must render honest NA deciles, never fabricated figures (AG-3)"
+    )
+    leadership = next(e for e in payload["factors_table"] if e["key"] == "leadership_score")
+    assert leadership["n_total"] > 0, (
+        "one factor's unusable stored shape blanked the OTHER factors' entries — AG-8 requires the "
+        "contained degrade, not a whole-response failure"
+    )
+    assert "were EXCLUDED as factor-NULL observations" in caplog.text, (
+        "the AG-8 data-shape exclusion must be disclosed in the log, never silent"
+    )
+
+
+def test_one_entry_s_non_memory_failure_degrades_only_that_entry(lab_engine, monkeypatch, caplog):
+    """iter-50 audit B4 (second half) — `compute_factor_lab_all`'s per-(factor,horizon) loop carried ONLY
+    an `except MemoryError`, so any OTHER exception from ONE entry still propagated and 500'd the whole
+    `?all=true` response for all 11 factors. `evidence.py`'s per-claim convention — the precedent this loop
+    already cites for its MemoryError catch — pairs that catch with a broader one, degrading the single
+    failing unit to an honest `status: "unavailable"` and continuing.
+
+    Teeth: the fault fires on exactly ONE `_deciles` call, so a handler that blanked the whole response
+    (or no handler at all — the pre-fix behavior, which raises straight out of this function) fails both
+    the "one entry degraded" and the "every other entry still real" assertions below."""
+    import app.engine.research as research
+
+    cfg = load_config()
+    real_deciles = research._deciles
+    calls = {"n": 0}
+    fault_on_call = 3  # a specific (factor, horizon) entry, deterministically
+
+    def _boom_on_one_entry(ordered, n_deciles, min_sample):
+        calls["n"] += 1
+        if calls["n"] == fault_on_call:
+            raise RuntimeError("simulated non-memory failure inside one (factor,horizon) entry")
+        return real_deciles(ordered, n_deciles, min_sample)
+
+    monkeypatch.setattr(research, "_deciles", _boom_on_one_entry)
+    with caplog.at_level("ERROR", logger="trendora.research"):
+        with Session(lab_engine) as session:
+            payload = compute_factor_lab_all(session, cfg, as_of=None)
+
+    degraded = [
+        (e["key"], bh["horizon"]) for e in payload["factors_table"]
+        for bh in e["by_horizon"] if bh.get("status") == "unavailable"
+    ]
+    assert calls["n"] > fault_on_call, (
+        "the loop stopped at the injected failure instead of continuing to the next entry — "
+        "isolate-and-continue means CONTINUE"
+    )
+    assert len(degraded) == 1, (
+        f"exactly the faulted (factor,horizon) entry must degrade; got {degraded!r}"
+    )
+    assert any(
+        bh.get("status") != "unavailable" and bh["n_total"] > 0
+        for e in payload["factors_table"] for bh in e["by_horizon"]
+    ), "no entry survived — the isolation is not contained, which is the failure this test forbids"
+    assert "isolate-and-continue" in caplog.text, (
+        "the isolated failure must be logged, never swallowed silently"
+    )
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index 7ee11d78..57ab3d12 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -31,22 +31,29 @@ from sqlmodel import Session, select
 import app.engine.research as research_module
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
+from app.engine import data_manager
 from app.engine.research import (
+    RESEARCH_CAVEAT,
+    SURVIVORSHIP_BIAS_LABEL,
     VIEW_EPISODES,
     VIEW_POOLED,
     _all_factor_observations_by_horizon,
     _combination_observations,
+    _deciles,
     _event_study_members,
     _event_study_members_by_horizon,
     _factor_observations,
+    _rank_ic,
     _regime_setup_pattern_observations,
     _severity_velocity_observation_set,
     compute_event_study,
     compute_factor_combination,
     compute_factor_lab,
     compute_factor_lab_all,
+    factor_catalog,
+    factor_lab_all_cached,
 )
-from app.models import ForwardReturn, ScannerResult, ScannerRun
+from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun
 
 H = 20
 
@@ -557,6 +564,19 @@ def test_all_factor_observations_by_horizon_matches_per_factor_per_horizon(prune
                 assert _eq(got, want), f"all-horizons subset != _factor_observations ({factor.key}@{h})"
 
 
+def _materialize_shared_pools(built) -> dict:
+    """iter-50 audit B3: the shared-pool builder now returns COLUMNAR accumulators
+    (`_FactorCoreRecords` / `_FactorObsPool`) instead of `list[tuple]`. Expand them through their sequence
+    protocol into plain nested lists so the byte-identity comparison below stays a comparison of DATA — a
+    raw `json.dumps(..., default=str)` on the objects themselves would compare `repr()`s (memory addresses),
+    which is never equal and would silently turn this proof into a tautological failure."""
+    core_records, pools = built
+    return {
+        "core_records": [[run_id, ticker, list(values)] for run_id, ticker, values in core_records],
+        "pools": {h: [list(row) for row in pool] for h, pool in pools.items()},
+    }
+
+
 @pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
 def test_all_factor_observations_by_horizon_chunk_independent(prune_engine, as_of):
     """The all-horizons shared pool read is byte-identical under read_batch_size=1 vs a huge batch — the
@@ -569,7 +589,9 @@ def test_all_factor_observations_by_horizon_chunk_independent(prune_engine, as_o
         big = _all_factor_observations_by_horizon(
             session, factors, horizons, as_of, cfg=_cfg_batch(1_000_000)
         )
-        assert _eq(small, big), f"all-horizons pool differs by batch (as_of={as_of})"
+        small_rows, big_rows = _materialize_shared_pools(small), _materialize_shared_pools(big)
+        assert small_rows["core_records"], "fixture produced no observations — the comparison is vacuous"
+        assert _eq(small_rows, big_rows), f"all-horizons pool differs by batch (as_of={as_of})"
 
 
 @pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
@@ -583,6 +605,341 @@ def test_compute_factor_lab_all_chunk_independent_component(component_engine, as
         assert _eq(small, big), f"factor-lab-all payload differs by batch (as_of={as_of})"
 
 
+# ==================================================================================================
+# ops-hardening iter-50 (J-07): `compute_factor_lab_all`'s per-(factor,horizon) obs-build + sort is the
+# CONFIRMED live crash frame from iter-49's own traceback (`research.py:1051`'s `sorted(obs, ...)`, an
+# uncaught MemoryError that killed the backend). Two proofs:
+#   1. TC-3: the bounded implementation (a `__slots__` `_FactorLabAllObs` stand-in for the old list-of-
+#      dicts) is byte-identical to a PINNED COPY of the pre-iter-50 dict-based implementation — mirrors
+#      this file's own established "pinned pre-fix reference oracle" pattern (see the `_fr_slice_map`
+#      TC-2 block above).
+#   2. TC-2 (fast/deterministic leg): a MemoryError injected at the confirmed crash frame via the SAME
+#      test-only `_fault_inject_memory_error` hook the ingest finalize-tail fault-injection suite already
+#      uses (test_ingest_finalize_fault_injection.py) is caught by the isolate-and-continue convention —
+#      never crashes the process, never raises out of `compute_factor_lab_all` /
+#      `factor_lab_all_cached`. A REAL `ulimit -v` drill proves the SAME contract under genuine memory
+#      pressure (test_start_backend_script.py).
+# ==================================================================================================
+def _compute_factor_lab_all_pinned_pre_iter50(session: Session, config, *, as_of=None) -> dict:
+    """A byte-for-byte copy of `compute_factor_lab_all`'s PRE-iter-50 obs-build + sort — the plain
+    list-of-dicts implementation iter-49's own traceback identified as the live crash frame — pinned here
+    as the reference oracle TC-3 proves the iter-50 `_FactorLabAllObs`-based bound against. Deliberately
+    does NOT call the current `compute_factor_lab_all` (that would prove nothing)."""
+    cfg = config
+    fl = cfg.research.factor_lab
+    wf = cfg.walk_forward
+    catalog = factor_catalog(cfg)
+    factors = list(fl.factors)
+    horizons = list(wf.horizons)
+    default_h = wf.default_horizon
+
+    core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
+    factor_index = {f.key: i for i, f in enumerate(factors)}
+
+    factors_table: list[dict] = []
+    for factor in factors:
+        idx = factor_index[factor.key]
+        by_horizon: list[dict] = []
+        dh_rank_ic: dict = {"value": None, "n": 0}
+        dh_risk_adjusted = None
+        dh_n_total = 0
+        for h in horizons:
+            obs = []
+            for core_idx, ret, max_drawdown in pools[h]:
+                factor_value = core_records[core_idx][2][idx]
+                if factor_value is None:
+                    continue
+                run_id, ticker, _values = core_records[core_idx]
+                obs.append({
+                    "run_id": run_id, "ticker": ticker,
+                    "factor": float(factor_value), "return": ret, "max_drawdown": max_drawdown,
+                })
+            ordered = sorted(obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
+            deciles = _deciles(ordered, fl.deciles, wf.min_sample)
+            by_horizon.append({"horizon": h, "n_total": len(obs), "deciles": deciles})
+            if h == default_h:
+                dh_rank_ic = _rank_ic([(o["factor"], o["return"]) for o in obs])
+                dh_risk_adjusted = deciles[-1]["risk_adjusted"]
+                dh_n_total = len(obs)
+        factors_table.append({
+            "key": factor.key, "label": factor.label, "family": factor.family,
+            "direction": factor.direction,
+            "n_total": dh_n_total,
+            "rank_ic": dh_rank_ic,
+            "risk_adjusted": dh_risk_adjusted,
+            "by_horizon": by_horizon,
+        })
+
+    return {
+        "asof_date": as_of.isoformat() if as_of is not None else None,
+        "factors": catalog,
+        "horizons": horizons,
+        "default_horizon": default_h,
+        "deciles_count": fl.deciles,
+        "min_sample": wf.min_sample,
+        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
+        "descriptive_caveat": RESEARCH_CAVEAT,
+        "factors_table": factors_table,
+    }
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
+def test_compute_factor_lab_all_matches_pinned_pre_iter50_reference(prune_engine, as_of):
+    """TC-3 (AG-3) — the bounded `compute_factor_lab_all` is byte-identical to the pinned pre-iter-50
+    reference oracle above, for every (factor, horizon, decile) figure, both all-history and a historical
+    as_of — proving the `_FactorLabAllObs` memory bound changed only the internal representation, never a
+    value or an ordering."""
+    cfg = load_config()
+    with Session(prune_engine) as session:
+        got = compute_factor_lab_all(session, cfg, as_of=as_of)
+        want = _compute_factor_lab_all_pinned_pre_iter50(session, cfg, as_of=as_of)
+        assert _eq(got, want), (
+            f"bounded compute_factor_lab_all diverges from the pinned pre-iter-50 reference (as_of={as_of})"
+        )
+
+
+def test_compute_factor_lab_all_isolates_memory_pressure_per_factor_horizon(component_engine, monkeypatch):
+    """TC-2 (fast/deterministic leg) — a MemoryError injected at the confirmed iter-49 crash frame is
+    caught by the per-(factor,horizon) isolate-and-continue convention: THAT entry alone degrades to an
+    honest `status: "unavailable"` (empty deciles, n_total 0) — `compute_factor_lab_all` itself never
+    raises, so a live request can still answer. Control arm first (env unset -> no `status` key anywhere,
+    proving a silently-disabled injector cannot pass as a green result), then the armed leg."""
+    cfg = load_config()
+
+    with Session(component_engine) as session:
+        control = compute_factor_lab_all(session, cfg, as_of=None)
+    for entry in control["factors_table"]:
+        for bh in entry["by_horizon"]:
+            assert "status" not in bh, f"control run must have no degraded entries; got {bh}"
+
+    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "factor_lab_all")
+    with Session(component_engine) as session:
+        payload = compute_factor_lab_all(session, cfg, as_of=None)  # must not raise
+
+    # the injector fires unconditionally on every call, so EVERY (factor, horizon) entry degrades —
+    # exercising the catch under maximum, repeated, consecutive stress (never accumulates, never escapes).
+    assert payload["factors_table"], "the factor catalog must still be listed even when every entry degrades"
+    for entry in payload["factors_table"]:
+        assert entry["n_total"] == 0
+        assert entry["rank_ic"] == {"value": None, "n": 0}
+        assert entry["risk_adjusted"] is None
+        for bh in entry["by_horizon"]:
+            assert bh["status"] == "unavailable"
+            assert bh["deciles"] == []
+            assert bh["n_total"] == 0
+
+
+def test_factor_lab_all_cached_degrades_honestly_on_memory_error_outside_the_per_entry_loop(
+    component_engine, monkeypatch,
+):
+    """The OUTER safety net in `factor_lab_all_cached`: a MemoryError raised OUTSIDE the per-(factor,
+    horizon) loop (e.g. the shared pool builder) is still caught — degrading the WHOLE response honestly
+    (`factors_status: "unavailable"`, empty `factors_table`) instead of propagating to FastAPI. Never
+    cached (no EventStudyCache row persisted), and the single-flight slot is not left wedged — a
+    follow-up call with the fault removed succeeds normally."""
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise MemoryError("simulated — outside the per-entry loop")
+
+    monkeypatch.setattr(research_module, "_all_factor_observations_by_horizon", _boom)
+    with Session(component_engine) as session:
+        degraded = factor_lab_all_cached(session, cfg, as_of=None)
+        assert degraded["factors_status"] == "unavailable"
+        assert degraded["factors_table"] == []
+        rows = session.exec(
+            select(EventStudyCache).where(EventStudyCache.view == "factors_table")
+        ).all()
+        assert rows == [], "a degraded response must never be persisted to the cache"
+
+    monkeypatch.undo()  # restore the real _all_factor_observations_by_horizon
+    # iter-50 AUDIT FIX (B4): the memory-pressure cooldown is what makes "never cached" safe — without it,
+    # every viewer restarts a doomed multi-GB compute. Expire it explicitly here so this test keeps proving
+    # exactly what it always proved (the single-flight slot is not wedged and a real compute still works),
+    # rather than silently measuring the cooldown instead.
+    _expire_factor_lab_cooldown()
+    with Session(component_engine) as session:
+        recovered = factor_lab_all_cached(session, cfg, as_of=None)  # must not hang — slot not wedged
+    assert recovered["factors_table"], "a follow-up call after the fault clears must compute normally"
+    assert "factors_status" not in recovered
+
+
+def test_factor_lab_all_cached_never_persists_a_per_entry_degraded_payload(component_engine, monkeypatch):
+    """A payload where a per-(factor,horizon) entry degraded under memory pressure (the INNER isolate-
+    and-continue inside `compute_factor_lab_all`, which returns NORMALLY rather than raising) must NEVER
+    be persisted to the cache — otherwise a LATER request under the SAME dataset-version stamp would be
+    served this stale degraded payload until the next dataset change, instead of getting a fresh attempt
+    once the memory pressure has actually cleared. Proven by injecting the fault for exactly one call,
+    confirming the served response is honestly degraded, confirming NO EventStudyCache row was written,
+    then clearing the fault and confirming the NEXT call computes fresh (not a stale degraded HIT)."""
+    cfg = load_config()
+
+    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "factor_lab_all")
+    with Session(component_engine) as session:
+        degraded = factor_lab_all_cached(session, cfg, as_of=None)
+    assert any(
+        bh["status"] == "unavailable"
+        for entry in degraded["factors_table"]
+        for bh in entry["by_horizon"]
+    ), "fixture sanity: the injected fault must actually degrade at least one entry"
+    with Session(component_engine) as session:
+        rows = session.exec(
+            select(EventStudyCache).where(EventStudyCache.view == "factors_table")
+        ).all()
+    assert rows == [], "a per-entry-degraded payload must never be persisted to the cache"
+
+    monkeypatch.delenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, raising=False)
+    # iter-50 AUDIT FIX (B4): expire the in-process memory-pressure cooldown so this test still measures
+    # the cache (its subject), not the cooldown — the cooldown's own behaviour is pinned separately below.
+    _expire_factor_lab_cooldown()
+    with Session(component_engine) as session:
+        recovered = factor_lab_all_cached(session, cfg, as_of=None)
+    assert all(
+        "status" not in bh for entry in recovered["factors_table"] for bh in entry["by_horizon"]
+    ), "the next call (fault cleared) must compute fresh, never serve a stale degraded HIT from the cache"
+
+
+# ==================================================================================================
+# ops-hardening iter-50 AUDIT FIX (finding B4) — the degrade path's TERMINATION CONDITION.
+#
+# "Never cache a degraded payload" is correct in intent, but on its own it removed the only thing that
+# used to stop the retries: with no persisted row, no negative cache, no backoff and no cap on concurrent
+# computes, EVERY subsequent view of `/research/factor-lab` started another full-scale, multi-minute,
+# multi-GB compute that could not succeed while the pressure lasted. On 2026-08-05 that turned one failed
+# page view into a 12-15 minute service wedge, amplified by five single-flight waiters timing out mid-
+# compute (the 900s ceiling sat inside the real 780-875s compute band) and each starting an INDEPENDENT
+# compute inside an already-exhausted process.
+# ==================================================================================================
+def _expire_factor_lab_cooldown() -> None:
+    """Force every open memory-pressure cooldown window to be expired — the deterministic stand-in for
+    "wait `_FACTOR_LAB_ALL_DEGRADED_COOLDOWN_S` seconds" (no clock manipulation, no sleep)."""
+    with research_module._FACTOR_LAB_ALL_LOCK:
+        for key, (_deadline, payload) in list(research_module._FACTOR_LAB_ALL_DEGRADED.items()):
+            research_module._FACTOR_LAB_ALL_DEGRADED[key] = (float("-inf"), payload)
+
+
+@pytest.fixture(autouse=True)
+def _clean_factor_lab_cooldown():
+    """The cooldown registry is MODULE state (deliberately: it must survive across requests inside one
+    process). Clear it around every test in this file so no test can leak a window into another."""
+    research_module._FACTOR_LAB_ALL_DEGRADED.clear()
+    yield
+    research_module._FACTOR_LAB_ALL_DEGRADED.clear()
+
+
+def test_memory_pressure_cooldown_stops_every_viewer_restarting_a_doomed_compute(
+    component_engine, monkeypatch,
+):
+    """iter-50 audit B4 — after a compute degrades under memory pressure, the NEXT viewer of the same key
+    is served that honest degraded payload from the in-process cooldown instead of launching another
+    full-scale compute. Teeth: `_all_factor_observations_by_horizon` is wrapped in a COUNTING spy, so a
+    second heavy compute cannot hide — the count must stay at exactly 1 across the repeat views."""
+    cfg = load_config()
+    calls = {"n": 0}
+    real = research_module._all_factor_observations_by_horizon
+
+    def _counting_boom(*a, **k):
+        calls["n"] += 1
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(research_module, "_all_factor_observations_by_horizon", _counting_boom)
+    with Session(component_engine) as session:
+        first = factor_lab_all_cached(session, cfg, as_of=None)
+    assert first["factors_status"] == "unavailable"
+    assert calls["n"] == 1, "the first view must actually attempt the compute"
+
+    # three more views inside the cooldown window — each served the honest degrade, none recomputing.
+    for i in range(3):
+        with Session(component_engine) as session:
+            repeat = factor_lab_all_cached(session, cfg, as_of=None)
+        assert repeat["factors_status"] == "unavailable", f"repeat {i}: must stay honestly degraded"
+        assert calls["n"] == 1, (
+            f"repeat {i}: the cooldown must serve the degraded payload, not restart the compute "
+            f"(compute attempts so far: {calls['n']})"
+        )
+
+    # still NEVER persisted — the cooldown is in-process only, never an EventStudyCache row.
+    with Session(component_engine) as session:
+        rows = session.exec(select(EventStudyCache).where(EventStudyCache.view == "factors_table")).all()
+    assert rows == [], "the cooldown must not persist a degraded payload to the cache"
+
+    # once the window expires, the next view retries for real — the cooldown is a backoff, not a wedge.
+    _expire_factor_lab_cooldown()
+    monkeypatch.setattr(research_module, "_all_factor_observations_by_horizon", real)
+    with Session(component_engine) as session:
+        recovered = factor_lab_all_cached(session, cfg, as_of=None)
+    assert recovered["factors_table"] and "factors_status" not in recovered, (
+        "after the cooldown window expires the next view must compute for real, not stay degraded forever"
+    )
+
+
+def test_memory_pressure_cooldown_is_per_key_and_cleared_by_a_successful_compute(
+    component_engine, monkeypatch,
+):
+    """iter-50 audit B4 — two independent guarantees.
+
+    (1) PER KEY: a cooldown opened for the all-history key must not silence a DIFFERENT as-of key. The key
+        already carries the dataset-version stamp, so a dataset change can never be masked either.
+    (2) CLEARED ON SUCCESS: a clean, fully-computed payload closes any window the key still carries, so
+        recovery is immediate and never has to wait out a window opened by an earlier failure."""
+    cfg = load_config()
+    other_as_of = date(2025, 3, 31)
+
+    monkeypatch.setattr(
+        research_module, "_all_factor_observations_by_horizon",
+        lambda *a, **k: (_ for _ in ()).throw(MemoryError("simulated")),
+    )
+    with Session(component_engine) as session:
+        degraded = factor_lab_all_cached(session, cfg, as_of=None)
+    assert degraded["factors_status"] == "unavailable"
+
+    # (1) a DIFFERENT as-of key is untouched by the all-history key's window.
+    monkeypatch.undo()
+    with Session(component_engine) as session:
+        other = factor_lab_all_cached(session, cfg, as_of=other_as_of)
+    assert "factors_status" not in other, (
+        "a cooldown opened for one key must never silence a different as-of key"
+    )
+    with Session(component_engine) as session:
+        still_cooled = factor_lab_all_cached(session, cfg, as_of=None)
+    assert still_cooled["factors_status"] == "unavailable", "the original key's window must still be open"
+
+    # (2) a successful compute for the key CLOSES its window immediately.
+    _expire_factor_lab_cooldown()
+    with Session(component_engine) as session:
+        recovered = factor_lab_all_cached(session, cfg, as_of=None)
+    assert "factors_status" not in recovered
+    assert not research_module._FACTOR_LAB_ALL_DEGRADED, (
+        "a clean compute must clear the key's cooldown window, so recovery never waits out a stale one"
+    )
+
+
+def test_single_flight_wait_ceiling_clears_the_measured_cold_compute(component_engine):
+    """iter-50 audit B4 (second half) — the single-flight bounded wait must sit ABOVE the real cold-compute
+    duration, not inside it. The pre-fix ceiling was 300 x 3 = 900s while a live cold compute measured
+    780.2s and 874.7s (`reports/perf-budgets.md` Addendum 8), so waiters routinely timed out MID-compute
+    and fell through to compute independently — `logs/backend.log` recorded five such fall-throughs in
+    2m16s during the outage window, each starting an additional independent multi-GB compute.
+
+    A source-level pin, deliberately: the real failure needs a 13-minute compute to reproduce, and a test
+    that sleeps for that is not a test. Teeth: restoring the old 300s base fails this."""
+    measured = research_module._FACTOR_LAB_ALL_MEASURED_COLD_MISS_S
+    ceiling = research_module._FACTOR_LAB_ALL_WAIT_TIMEOUT_S
+    worst_observed_live_cold_compute_s = 874.7  # 2026-08-05, reports/perf-budgets.md Addendum 8
+    assert measured >= worst_observed_live_cold_compute_s, (
+        f"the measured-cold-miss base ({measured}s) is below the worst observed live cold compute "
+        f"({worst_observed_live_cold_compute_s}s) — waiters will time out mid-compute and duplicate it"
+    )
+    assert ceiling > worst_observed_live_cold_compute_s, (
+        f"the single-flight wait ceiling ({ceiling}s) must clear the real compute duration "
+        f"({worst_observed_live_cold_compute_s}s); it is reached only by a genuinely wedged owner"
+    )
+    assert research_module._FACTOR_LAB_ALL_DEGRADED_COOLDOWN_S >= worst_observed_live_cold_compute_s, (
... [diff_bound] apps/backend/tests/test_research_streaming.py: 8 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index 5c303975..cfbd1650 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -850,6 +850,173 @@ def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawn
     )
 
 
+# ==================================================================================================
+# ops-hardening iter-50 (J-07, TC-2): the confirmed iter-49 crash frame — `compute_factor_lab_all`'s
+# per-(factor,horizon) obs-build+sort (research.py) — raised an UNCAUGHT MemoryError that killed a live
+# backend for 12m45s during that round's own browser lane. This drills the LIVE, spawned server process:
+# `GET /research/factor-lab?all=true` must survive REPEATED memory-pressure hits without the process ever
+# dying, and `GET /api/health` must stay 200 throughout.
+#
+# WHY THE DETERMINISTIC FAULT-INJECTOR, NOT AN ORGANIC `ulimit -v` CALIBRATION:
+# `test_ingest_finalize_fault_injection.py`'s own docstring documents why a genuinely tightened cap cannot
+# reliably reach a SPECIFIC deep call site inside a live server process for the finalize tail's two
+# per-item handlers (an earlier, unrelated allocation in the same request/boot sequence exhausts a cap
+# tight enough to threaten the target site first) — the SAME reasoning applies here, one call deeper
+# (this crash frame is reached via `GET /research/factor-lab?all=true` -> `factor_lab_all_cached` ->
+# `compute_factor_lab_all`'s per-(factor,horizon) loop, itself downstream of the shared pool builder's own
+# DB read). The fault-injector raises a REAL `MemoryError` object at the EXACT confirmed site — Python's
+# `except MemoryError:` handler behaves identically whether that object came from a failed `malloc()` or
+# an explicit `raise`, so this is the SAME code path a real `ulimit -v` exhaustion would hit, just aimed
+# reliably instead of hoping to land on it. `TRENDORA_RUN_HEAVY_INGEST_TEST`-gated like this module's
+# other real-process drills, so it never runs by accident on a plain `pytest` invocation.
+# ==================================================================================================
+_FACTOR_LAB_FAULT_TEST_PORT = 19200 + _offset
+
+
+@pytest.fixture()
+def spawned_backend_fault_injected():
+    """Like `spawned_backend`, but launched with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all` in
+    its environment — deterministically arming the test-only `_fault_inject_memory_error` hook at
+    `compute_factor_lab_all`'s per-(factor,horizon) obs-build+sort, the confirmed iter-49 crash frame.
+    Opt-in (same gate as the heavy-ingest fixtures above): a fault-injecting backend must never spawn by
+    accident on a plain `pytest tests/test_start_backend_script.py` run."""
+    if os.environ.get("TRENDORA_RUN_HEAVY_INGEST_TEST") != "1":
+        pytest.skip(
+            "live fault-injected backend drill is opt-in — set TRENDORA_RUN_HEAVY_INGEST_TEST=1 "
+            "(run it only on an idle host with the host-guard protections active)"
+        )
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_FACTOR_LAB_FAULT_TEST_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_FACTOR_LAB_FAULT_TEST_PORT + 1000)
+    env["TRENDORA_FAULT_INJECT_MEMORY_ERROR"] = "factor_lab_all"
+    proc = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        _wait_for_health(_FACTOR_LAB_FAULT_TEST_PORT, timeout=60.0)
+        yield _FACTOR_LAB_FAULT_TEST_PORT
+    finally:
+        if _pid_alive(proc.pid):
+            os.kill(proc.pid, signal.SIGKILL)
+            deadline = time.monotonic() + 10.0
+            while _pid_alive(proc.pid) and time.monotonic() < deadline:
+                time.sleep(0.1)
+        try:
+            proc.wait(timeout=10)
+        except ChildProcessError:
+            pass
+
+
+def _distinct_factor_lab_asof_dates(port: int, n: int) -> list[str]:
+    """`n` distinct real snapshot as-of dates, read from the SPAWNED INSTANCE's own `GET /api/runs` — never
+    hardcoded literals that go stale. Each one is a DIFFERENT `factor_lab_all_cached` key, which is what
+    makes the repeated-pressure drill below exercise `n` genuinely independent full-scale computes."""
+    resp = httpx.get(f"http://127.0.0.1:{port}/api/runs", timeout=120.0)
+    resp.raise_for_status()
+    dates = [r["asof_date"] for r in resp.json().get("runs", []) if r.get("asof_date")]
+    if len(dates) < n:
+        pytest.skip(f"need >= {n} persisted snapshot dates to key {n} independent computes; got {len(dates)}")
+    return dates[:n]
+
+
+# The owner-amended `GET /api/health` ceiling during a BOUNDED BACKGROUND-COMPUTE window (docs/goal.md,
+# "Additional binding notes", 2026-07-31): every poll must answer HTTP 200 within <= 2s. Steady-state reads
+# keep their own <= 0.1s ceiling — not what this drill measures.
+_HEALTH_BOUNDED_COMPUTE_CEILING_S = 2.0
+
+
+def test_factor_lab_all_survives_repeated_memory_pressure_live(spawned_backend_fault_injected):
+    """TC-2 (ops-hardening iter-50) — a REAL live server process, launched via `scripts/start-backend.sh`,
+    with the confirmed crash frame deterministically faulted on EVERY call. Every response is an honest 200
+    with every entry degraded (never a raw 500, never a dropped connection — the process staying alive to
+    answer at all IS the proof), and `GET /api/health` stays 200 THROUGHOUT.
+
+    ops-hardening iter-50 AUDIT FIX (finding T3) — this drill previously had a blind spot that was exactly
+    the defect: it issued the Factor Lab request, waited ~3m46s for it to COMPLETE, and only then checked
+    health. Across the whole 18m50s run it never once probed health while the process was busy, so it went
+    green (1 passed in 1130.35s) in the same round the live browser lane found a 12-15 minute health
+    outage. The phase's own TC-1/TC-7 are about health answering DURING the heavy work, so health is now
+    polled on a background thread FOR THE DURATION of each request and every poll is asserted.
+
+    ops-hardening iter-50 AUDIT FIX (finding B4) — the drill also now uses a DISTINCT as-of key per run, so
+    each run is a genuinely independent full-scale compute rather than a repeat that the new memory-pressure
+    cooldown would (correctly) short-circuit; the cooldown's own behaviour is then asserted explicitly at
+    the end, against a repeat of an already-degraded key."""
+    # A cold `compute_factor_lab_all` on the CURRENT live basis was measured at 780.2s and 874.7s
+    # (`reports/perf-budgets.md` Addendum 8) — the SHARED pool builder runs to completion BEFORE the
+    # per-(factor,horizon) loop this fault targets even starts, and a degraded payload is deliberately never
+    # cached, so every run below pays that full cold-read cost. Sized above the worst observed figure with
+    # the same headroom `factor_lab_all_cached`'s own `_FACTOR_LAB_ALL_WAIT_TIMEOUT_S` uses.
+    _REQUEST_TIMEOUT_S = 1200.0
+    _RUNS = 3  # iter-44 lesson: one green run proves nothing. 3 independent full-scale computes, each of
+               # which can cost ~15 minutes on this basis — the upper end of the spec's own "3-5".
+    port = spawned_backend_fault_injected
+    asof_dates = _distinct_factor_lab_asof_dates(port, _RUNS)
+
+    for i, asof in enumerate(asof_dates):
+        health = _HealthPoller(port)
+        health.start()
+        try:
+            resp = httpx.get(
+                f"http://127.0.0.1:{port}/api/research/factor-lab?all=true&as_of={asof}",
+                timeout=_REQUEST_TIMEOUT_S,
+            )
+        finally:
+            health.stop()
+            health.join(timeout=15.0)
+
+        assert resp.status_code == 200, (
+            f"run {i} (as_of={asof}): expected an honest 200 (degraded payload), got "
+            f"{resp.status_code}: {resp.text[:300]}"
+        )
+        payload = resp.json()
+        assert payload.get("factors_table"), f"run {i}: the factor catalog must still be listed"
+        for entry in payload["factors_table"]:
+            for bh in entry["by_horizon"]:
+                assert bh.get("status") == "unavailable", f"run {i}: expected a degraded entry, got {bh}"
+
+        # --- T3: the polls taken WHILE the process was busy, not after it went idle -------------------
+        assert health.results, (
+            f"run {i}: the health poller recorded nothing — the drill would be measuring an idle process"
+        )
+        bad = [
+            (j, r) for j, r in enumerate(health.results)
+            if r.get("status") != 200 or r.get("elapsed", 0) > _HEALTH_BOUNDED_COMPUTE_CEILING_S
+        ]
+        assert not bad, (
+            f"run {i} (as_of={asof}): GET /api/health must answer 200 within "
+            f"{_HEALTH_BOUNDED_COMPUTE_CEILING_S}s on EVERY poll taken DURING the heavy request "
+            f"({len(health.results)} polls, {len(bad)} bad). This is the exact failure the pre-fix drill "
+            f"could not see, because it only checked health after the request had already returned. "
+            f"First offenders: {bad[:5]}"
+        )
+
+    # --- B4: the repeat of an already-degraded key is served from the cooldown, not recomputed ---------
+    # The termination condition the audit found missing: without it, every subsequent viewer restarted a
+    # doomed multi-GB compute. A repeat must answer FAST (nowhere near a full compute) and still honestly.
+    repeat_start = time.monotonic()
+    repeat = httpx.get(
+        f"http://127.0.0.1:{port}/api/research/factor-lab?all=true&as_of={asof_dates[-1]}",
+        timeout=_REQUEST_TIMEOUT_S,
+    )
+    repeat_elapsed = time.monotonic() - repeat_start
+    assert repeat.status_code == 200, f"the cooled-down repeat must still answer 200, got {repeat.status_code}"
+    repeat_payload = repeat.json()
+    assert all(
+        bh.get("status") == "unavailable"
+        for entry in repeat_payload.get("factors_table", [])
+        for bh in entry["by_horizon"]
+    ), "the cooled-down repeat must still be honestly degraded, never a fabricated success"
+    # Generous by design: the point is "orders of magnitude below a full compute", not a latency budget.
+    assert repeat_elapsed < 60.0, (
+        f"the repeat of an already-degraded key took {repeat_elapsed:.1f}s — it restarted the compute "
+        f"instead of being served from the memory-pressure cooldown (audit B4)"
+    )
+
+
 # ops-hardening iter-48 (J-05 fix) — TC-1's own 20-minute bound, measured from the job's own acceptance
 # (a superset/stricter measurement than "from the snapshot write", since the snapshot writes only ~13s
 # after acceptance on this DB per the live drill in `reports/perf-budgets.md` Item R).
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 333 +++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |   8 +
 .../journey-scripts/J-05.json                      |  35 ++-
 runs/goal-session-ops-hardening/state/blueprint.md |   3 +
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |  62 ++++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  13 +
 8 files changed, 445 insertions(+), 13 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
