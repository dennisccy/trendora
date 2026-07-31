# Iteration diff (bounded)

Files changed: 32. Shown in full: 31.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh` (49 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 566b5277..34438519 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -2902,6 +2902,43 @@ def _release_process_memory() -> None:
             pass
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-39 (audit finding B3 / J-07 step 4) — TEST-ONLY `MemoryError` fault injection.
+#
+# J-07 step 4's own text sanctions exactly this: "Induce memory pressure during a warm (TEST HOOK or a
+# tightened cap in a throwaway process)". Three live calibration trials this iteration (3420/2700/2650 MB)
+# failed to reach the two NAMED per-item aggregate-warm handlers, because `_missing_data_diagnostic`'s
+# whole-`daily_prices` materialization runs EARLIER in the same finalize sequence and exhausts any cap
+# tight enough to threaten them first (audit B3). Continuing to tune the cap is the wrong-direction
+# pattern in `.claude/judgment-rubrics.md` §4; this hook makes the same proof DETERMINISTIC — and, because
+# it induces no real memory pressure at all, it is also strictly safer for this host (AG-10).
+#
+# Contract: unset in every real deployment (the env var is read once per warm call and is absent, so the
+# behavior is byte-identical to before this hook existed — no second code path, no config surface). Same
+# class of test-only env escape hatch as `TRENDORA_FORCE_LEGACY_BAR_CACHE` (iter-38), and it is deliberately
+# NOT a config.yaml key: a fault injector must not be reachable through the product's own configuration.
+# --------------------------------------------------------------------------------------------------
+_FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
+# The call sites this hook understands. Each is the exact per-item boundary whose `except MemoryError`
+# handler J-07's acceptance names; an unknown name in the env var injects nothing (a typo must not
+# silently look like a passing drill).
+_FAULT_INJECT_SITES = frozenset({"forward_aggregates", "drawdown_expectations", "backfill_worker"})
+
+
+def _fault_inject_memory_error(site: str) -> None:
+    """Raise `MemoryError` at `site` when this process was started with `site` listed in
+    `TRENDORA_FAULT_INJECT_MEMORY_ERROR` (comma-separated). A no-op — one `os.environ.get` — otherwise.
+
+    The raised exception carries the site name so the drill/test asserts WHICH stage aborted from a direct
+    read of the log line, never inferring it from "a `MemoryError` fired somewhere" (the binding iter-37/38
+    lesson). An unrecognized site name is ignored (see `_FAULT_INJECT_SITES`)."""
+    if site not in _FAULT_INJECT_SITES:
+        return
+    raw = os.environ.get(_FAULT_INJECT_MEMORY_ERROR_ENV, "")
+    if site in {token.strip() for token in raw.split(",") if token.strip()}:
+        raise MemoryError(f"injected at fault-injection site {site!r} ({_FAULT_INJECT_MEMORY_ERROR_ENV})")
+
+
 def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engine) -> None:
     """For each in-range trading day with bars but NO snapshot, create the immutable snapshot then INSERT
     its realized forward returns (bars > D). No scan/return math is re-implemented and no snapshot is
@@ -3120,9 +3157,74 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
             # `prog._shared_bar_cache is not None` check (`_persist_per_date_coverage_snapshots`,
             # `_refresh_ingest_aggregates`) falls back to its own independent `prefilled_bar_cache`/
             # `nullcontext()` path, unchanged from pre-iter-37 behavior — no second code path needed.
-            if not os.environ.get("TRENDORA_FORCE_LEGACY_BAR_CACHE"):
+            #
+            # ops-hardening iter-39 (audit B5 fix): the prior `if not os.environ.get(...)` treated ANY
+            # non-empty value as "force legacy" — including `"0"`/`"false"`, so a caller trying to
+            # explicitly DISABLE the toggle by setting it to `"0"` silently ENABLED legacy mode instead.
+            # An explicit truthy allowlist closes that: only a recognized truthy token forces legacy mode;
+            # unset, empty, `"0"`, or any other value takes the normal (live shared-cache) path.
+            if os.environ.get("TRENDORA_FORCE_LEGACY_BAR_CACHE", "").strip().lower() not in (
+                "1", "true", "yes",
+            ):
                 prog._shared_bar_cache = shared_cache
 
+            # ops-hardening iter-39 (audit finding B2) — per-JOB memory-pressure latch for the per-date
+            # compute. Set by `_compute_one_isolated` the first time any date's compute raises
+            # `MemoryError`; every date still pending then short-circuits without attempting its own
+            # allocation. This is the iter-8 finalize-tail convention ("on the first `MemoryError` that ONE
+            # loop stops attempting further items, instead of hammering the next item's allocation under
+            # real pressure — the confirmed root cause of iter-7's 7+ minute health hang") applied to the
+            # ONE per-item loop that never carried it: `_do_backfill`'s per-date compute. A `threading.Event`
+            # rather than a plain bool because the parallel arm reads/writes it from `backfill_workers`
+            # threads concurrently.
+            memory_pressure = threading.Event()
+
+            def _compute_one_isolated(
+                d: date_cls,
+            ) -> tuple[date_cls, Optional[dict], float, Optional[str]]:
+                """Compute ONE date INSIDE the calling (worker) thread with per-item failure isolation,
+                returning `(d, payload, seconds, compute_error)` — never raising.
+
+                ops-hardening iter-39 (audit finding B2): before this, `_compute_one_backfill_date` was
+                submitted to the pool bare, so a `MemoryError` in a worker was stored on its `Future` —
+                WITH its `__traceback__`, which pins every frame's locals (the half-materialized payload,
+                the ORM result buffers) alive until the orchestrating thread drains that future — while the
+                worker thread immediately picked up the NEXT date and started allocating again. Under
+                genuine pressure that is the amplifier, not the accident: N workers each retaining a failing
+                frame chain while N more allocations are attempted. Catching in the worker's own frame ends
+                both — the traceback dies with the `except` block and only a plain string crosses the thread
+                boundary, and the latch stops the remaining dates from piling on.
+
+                HONESTY: a short-circuited date is recorded as a per-date FAILURE (`error_other`), never as
+                a success and never silently dropped — so `snapshots_created + already_snapshotted +
+                error_other == dates_total` still holds exactly (the run-summary contract in goal.md).
+
+                Deviation from the finalize-tail loops' `logger.exception(...)`-then-`_release_process_
+                memory()` order, deliberately: formatting a traceback ALLOCATES, and this iteration's own
+                trial-3 evidence shows that failing under real exhaustion
+                (`runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:50` —
+                "Exception ignored in thread started by: <object repr() failed>"). Freeing first buys the
+                headroom the log line needs, and the log line is what makes the abort diagnosable at all."""
+                if memory_pressure.is_set():
+                    return d, None, 0.0, (
+                        "skipped — this job already aborted a date for memory pressure "
+                        "(remaining dates not attempted)"
+                    )
+                try:
+                    _fault_inject_memory_error("backfill_worker")
+                    _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
+                    return d, payload, secs, None
+                except MemoryError:
+                    memory_pressure.set()  # latch FIRST so in-flight siblings stop allocating immediately
+                    _release_process_memory()
+                    logger.exception(
+                        "backfill per-date compute aborted at %s — memory pressure, skipping the remaining "
+                        "dates in this job", d,
+                    )
+                    return d, None, 0.0, f"aborted for memory pressure at {d.isoformat()}"
+                except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure (unchanged)
+                    return d, None, 0.0, str(exc)
+
             def _run_targets(window_targets: list[date_cls]) -> None:
                 """Compute + persist exactly this window's target dates — serial (workers<=1 or a single
                 date) or fanned-out parallel, byte-identical to the pre-chunking body (only the INPUT
@@ -3131,13 +3233,7 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
                     # serial baseline — compute + persist inline, one date at a time, in order. A per-date
                     # compute failure is caught here (isolated), not raised — the rest still run.
                     for d in window_targets:
-                        compute_error: Optional[str] = None
-                        payload: Optional[dict] = None
-                        secs = 0.0
-                        try:
-                            _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
-                        except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure
-                            compute_error = str(exc)
+                        _, payload, secs, compute_error = _compute_one_isolated(d)
                         _persist_isolated(d, payload, secs, compute_error)
                     return
                 # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as
@@ -3147,16 +3243,22 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
                 pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
                 next_idx = 0
                 with ThreadPoolExecutor(max_workers=min(workers, len(window_targets))) as pool:
+                    # iter-39 (audit B2): submit the ISOLATING wrapper, not the bare compute — a worker's
+                    # `MemoryError` is now caught in that worker's own frame (traceback dropped there,
+                    # memory released there, latch set there) and arrives here as a plain error string.
                     future_to_date = {
-                        pool.submit(_compute_one_backfill_date, eng, cfg, d, shared_cache): d
+                        pool.submit(_compute_one_isolated, d): d
                         for d in window_targets
                     }
                     for future in as_completed(future_to_date):
                         d = future_to_date[future]
                         try:
-                            _, payload, secs = future.result()
-                            pending[d] = (payload, secs, None)
-                        except Exception as exc:  # noqa: BLE001 — capture this date's failure, keep draining
+                            _, payload, secs, compute_error = future.result()
+                            pending[d] = (payload, secs, compute_error)
+                        except Exception as exc:  # noqa: BLE001 — defensive: `_compute_one_isolated` never
+                            # raises, so this can now only fire for a pool-level fault (e.g. the
+                            # `RuntimeError: can't start new thread` iter-38's drill hit at the `ulimit -v`
+                            # ceiling). Still captured per date so the drain loop never deadlocks.
                             pending[d] = (None, 0.0, str(exc))
                         # drain any now-contiguous prefix in target (date) order — writes stay strictly
                         # ordered within the window.
@@ -3354,11 +3456,13 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     # binding iter-37 lesson is that a drill on a conditional path (a stashed reference, an attach/fallback
     # context) must ASSERT the condition was live, never assume it from the lexical `with cache_ctx:` wrap
     # alone. One line per job, corroborable against a bounded range of the live `logs/backend.log`.
-    # `logger.warning` (not `.info`): this app never configures a root-logger handler/level, so uvicorn's
-    # last-resort handler — the ONLY thing writing `trendora.data_manager` records into `logs/backend.log`
-    # — only surfaces WARNING and above (confirmed live: an `.info` call here was silently dropped, never
-    # once appearing in the log across a full drilled job).
-    logger.warning(
+    # ops-hardening iter-39: downgraded `.warning` -> `.info`, its honest level — this is routine liveness
+    # telemetry, not a warning condition. Safe now that `app.logging_config.configure_app_logging()` (wired
+    # from `main.py` at import time) attaches a root-logger handler at INFO, so this no longer needs to
+    # masquerade as a warning to reach `logs/backend.log` (iter-38's workaround; confirmed live via TC-12 —
+    # see `test_data_manager.py` — that an `.info`-level record from this logger now reaches the configured
+    # handler).
+    logger.info(
         "J-07 finalize-tail cache_ctx liveness: job=%s resolved=%s",
         prog.job_id,
         "attach_shared_cache(live shared cache)" if shared is not None else "nullcontext(no shared cache)",
@@ -3440,6 +3544,10 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                         # this loop stops immediately (no further horizons attempted) and forces memory back
                         # to the OS.
                         try:
+                            # iter-39 (audit B3 / J-07 step 4): test-only injection point — a no-op unless
+                            # this process was started with the env var naming this site. See
+                            # `_fault_inject_memory_error`.
+                            _fault_inject_memory_error("forward_aggregates")
                             forward_testing.forward_aggregates_ingest_cached(
                                 session, h, cfg, as_of=latest_run_date
                             )
@@ -3529,6 +3637,9 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
                 prog.tick()  # heartbeat stamp before each claim's warm call — see docstring above.
                 try:
+                    # iter-39 (audit B3 / J-07 step 4): test-only injection point — see
+                    # `_fault_inject_memory_error` (a no-op unless this process names this site in the env).
+                    _fault_inject_memory_error("drawdown_expectations")
                     result = forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)
                     # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an
                     # out-of-scope horizon or an unresolvable cohort returns None honestly and must NOT be
diff --git a/apps/backend/main.py b/apps/backend/main.py
index c0bb5317..1fcb03df 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -40,8 +40,14 @@ from app.config import load_config
 from app.db import create_db_and_tables, get_engine
 from app.engine.data_manager import sweep_orphaned_runs
 from app.engine.warmup import ensure_latest_snapshot, start_warmup
+from app.logging_config import configure_app_logging
 from app.seed_loader import load_seed
 
+# ops-hardening iter-39: attach a root-logger handler at INFO level BEFORE any `trendora.*`
+# logger is used below (or by any imported engine module) — see `app.logging_config`'s own
+# docstring for why this was needed (routine `.info()` calls were previously dropped silently).
+configure_app_logging()
+
 logger = logging.getLogger("trendora.lifespan")
 
 
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 52400b8a..0a34b6ce 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -2214,6 +2214,40 @@ def test_do_backfill_whole_stage_exception_releases_shared_cache_and_reraises(ba
     assert release_calls, "a whole-stage exception must call _release_process_memory() before re-raising"
 
 
+def test_do_backfill_env_toggle_falsy_value_keeps_shared_cache(backfilled_job, monkeypatch):
+    """TC-10 (audit B5 fix) — `TRENDORA_FORCE_LEGACY_BAR_CACHE=0` must be treated as FALSY: legacy mode is
+    NOT forced, so `prog._shared_bar_cache` is stashed to the real shared cache (not skipped). Before this
+    fix, `if not os.environ.get(...)` treated ANY non-empty string — including `"0"` — as truthy, so this
+    exact case silently forced legacy mode instead of leaving it disabled."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    monkeypatch.setenv("TRENDORA_FORCE_LEGACY_BAR_CACHE", "0")
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in trading if d not in snapshotted)
+    prog = JobProgress(job_id="env-toggle-falsy-probe", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog, eng=engine)
+    assert prog._shared_bar_cache is not None, "a falsy toggle value ('0') must NOT force legacy mode"
+
+
+def test_do_backfill_env_toggle_truthy_value_forces_legacy(backfilled_job, monkeypatch):
+    """TC-11 — `TRENDORA_FORCE_LEGACY_BAR_CACHE=1` is treated as TRUTHY: legacy mode IS forced, so the
+    shared-cache stash is skipped and `prog._shared_bar_cache` stays `None`."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    monkeypatch.setenv("TRENDORA_FORCE_LEGACY_BAR_CACHE", "1")
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in trading if d not in snapshotted)
+    prog = JobProgress(job_id="env-toggle-truthy-probe", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog, eng=engine)
+    assert prog._shared_bar_cache is None, "a truthy toggle value ('1') must force legacy mode (stash skipped)"
+
+
 def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job, monkeypatch):
     """ops-hardening iter-2 (J-05) end-to-end: a real backfill job dispatched through `run_data_job` (the
     SAME path the API uses) reaches the finalize hook, persists a `coverage_snapshot` row, and the job's
diff --git a/apps/backend/tests/test_data_manager_backfill_parallel.py b/apps/backend/tests/test_data_manager_backfill_parallel.py
index 02633e44..cee518df 100644
--- a/apps/backend/tests/test_data_manager_backfill_parallel.py
+++ b/apps/backend/tests/test_data_manager_backfill_parallel.py
@@ -28,7 +28,7 @@ from sqlmodel import Session, select
 
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
-from app.engine import forward_testing, scanner
+from app.engine import data_manager, forward_testing, scanner
 from app.engine.data_manager import _trading_days, create_job, get_job, run_data_job
 from app.models import ForwardReturn, ScannerResult, ScannerRun
 from app.seed_loader import load_seed
@@ -316,6 +316,114 @@ def test_backfill_single_date_failure_isolated_others_complete(tmp_path, monkeyp
                 assert run is not None
 
 
+# ==================================================================================================
+# ops-hardening iter-39 FIX PASS (audit finding B2) — per-WORKER-THREAD MemoryError isolation.
+#
+# The audit found the one per-item loop that never carried iter-8's `except MemoryError` convention:
+# `_do_backfill`'s per-date compute. Submitted bare, a worker's `MemoryError` was stored on its `Future`
+# WITH its traceback (pinning every failing frame's locals alive until the orchestrator drained it) while
+# that worker immediately picked up the next date and allocated again — the same "hammer the next
+# allocation under pressure" amplifier iter-8 identified as the confirmed root cause of iter-7's 7+ minute
+# health hang, and the shape trial 3 reproduced this iteration
+# (`runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt`).
+# ==================================================================================================
+def test_backfill_worker_memory_error_caught_in_worker_thread_not_drain_loop(tmp_path, monkeypatch):
+    """A `MemoryError` in the PARALLEL per-date compute is caught inside the worker's own frame — proven
+    by the recorded per-date error carrying the WRAPPER's wording ("aborted for memory pressure at <date>")
+    rather than the raw exception text the old drain-loop `except Exception: str(exc)` would have recorded.
+    The job ends an honest `partial` (never a crash, a hang, or a stuck `running`), fabricates no snapshot,
+    calls `_release_process_memory()`, and keeps the run-summary invariant exact."""
+    cfg, engine = _fresh_seed_engine(tmp_path, "worker_mem")
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+    _base = _daily_region_start(trading, cfg)
+    r_start, r_end = trading[_base + 305], trading[_base + 308]
+    in_range = [d for d in trading if r_start <= d <= r_end]
+    assert len(in_range) == 4  # a real fan-out across the worker pool
+
+    release_calls: list[str] = []
+    real_release = data_manager._release_process_memory
+    monkeypatch.setattr(
+        data_manager, "_release_process_memory",
+        lambda: (release_calls.append("released"), real_release())[1],
+    )
+    # the test-only injector at the worker call site — deterministic, and (unlike a tightened cap) it
+    # induces no real memory pressure on this host at all (AG-10).
+    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "backfill_worker")
+
+    job = create_job("backfill", r_start, r_end)
+    summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, 4), engine=engine)
+
+    assert summary["status"] == "partial", "isolated per-date failures → partial, never a crash or stuck run"
+    assert summary["snapshots_created"] == 0, "nothing may be fabricated for a date whose compute aborted"
+    assert summary["error_other"] == len(in_range), "every unattempted/aborted date must be counted honestly"
+    # the run-summary contract in goal.md ("Canonical values"): the breakdown still partitions the range.
+    assert (
+        summary["snapshots_created"] + summary["already_snapshotted"] + summary["error_other"]
+        == summary["dates_total"]
+    )
+    errors = [f["error"] for f in summary["date_failures"]]
+    assert len(errors) == len(in_range)
+    assert all(
+        ("aborted for memory pressure at" in e) or ("already aborted a date for memory pressure" in e)
+        for e in errors
+    ), (
+        "every recorded error must come from the worker-frame isolation wrapper (abort or latch-skip); a "
+        f"raw injected-exception string would mean the MemoryError escaped to the drain loop: {errors}"
+    )
+    assert any("aborted for memory pressure at" in e for e in errors), (
+        f"at least one date must record the worker-frame MemoryError abort itself: {errors}"
+    )
+    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"
+    with Session(engine) as session:
+        for d in in_range:
+            assert scanner.get_run_for_date(session, d) is None
+
+
+def test_backfill_memory_pressure_latch_stops_remaining_dates(tmp_path, monkeypatch):
+    """The latch half of the convention, asserted DETERMINISTICALLY on the serial arm (workers=1, so date
+    order is fixed and there is no in-flight-sibling race): once the FIRST date's compute raises
+    `MemoryError`, the remaining dates are NOT attempted — they are recorded as honest skips instead of
+    each firing its own large allocation under pressure. Load-bearing: `compute_run_payload` raises for the
+    first date ONLY, so without the latch the later dates would have succeeded and produced snapshots."""
+    cfg, engine = _fresh_seed_engine(tmp_path, "mem_latch")
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+    _base = _daily_region_start(trading, cfg)
+    r_start, r_end = trading[_base + 305], trading[_base + 307]
+    in_range = [d for d in trading if r_start <= d <= r_end]
+    assert len(in_range) == 3
+    first_date = in_range[0]
+
+    real_compute = scanner.compute_run_payload
+    attempted: list[date] = []
+
+    def _fail_first_only(session_arg, asof, config=None):
+        attempted.append(asof)
+        if asof == first_date:
+            raise MemoryError("simulated allocation failure on the first date")
+        return real_compute(session_arg, asof, config)
+
+    monkeypatch.setattr(scanner, "compute_run_payload", _fail_first_only)
+
+    job = create_job("backfill", r_start, r_end)
+    summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, 1), engine=engine)
+
+    assert attempted == [first_date], (
+        "after the first date's MemoryError the latch must stop the remaining dates from ATTEMPTING their "
+        f"own compute; dates that reached compute_run_payload: {attempted}"
+    )
+    assert summary["status"] == "partial"
+    assert summary["snapshots_created"] == 0
+    assert summary["error_other"] == len(in_range)  # skipped dates are failures, never silently dropped
+    errors = {f["date"]: f["error"] for f in summary["date_failures"]}
+    assert "aborted for memory pressure at" in errors[first_date.isoformat()]
+    for d in in_range[1:]:
+        assert "already aborted a date for memory pressure" in errors[d.isoformat()], (
+            f"a latch-skipped date must say so honestly, not masquerade as a compute failure: {errors}"
+        )
+
+
 def test_backfill_progress_never_exceeds_total(tmp_path):
     """Under the parallel build, the final dates_done never exceeds dates_total, and the live job is
     reachable through the registry — progress stays honest (counts monotonic, bounded by the plan)."""
diff --git a/incredible_auto_dev/.claude/anti-patterns/27-software-guards-without-reset-reason.md b/incredible_auto_dev/.claude/anti-patterns/27-software-guards-without-reset-reason.md
new file mode 100644
index 00000000..2ed0f1a3
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/27-software-guards-without-reset-reason.md
@@ -0,0 +1,9 @@
+## 27. Iterating on software guards without reading the hardware's own reset-reason register
+
+**Pattern:** A machine keeps failing in a way that looks like a resource problem, and each occurrence produces a more elaborate software mitigation — while the platform has been recording, and printing, the actual cause the whole time. Observed: a host hard-reset seven times in eleven days under goal-mode load. Reset #6 produced the machine-global aggregate bound (anti-pattern 26); reset #7 on 2026-07-30 17:14:08 then happened with that bound deployed to both projects, armed, and green on every single check — masks inside the machine budget, `10G + 10G` under a 22G budget, boost off *and* persisted, QA browsers confined, both engines visible to each other in the registry. The 1 Hz sampler recorded 65 °C, 26 W, load 6.54 on 8 threads, 11.5 GB free and memory PSI 0.00 at T-1s. Every software hypothesis was refuted, and the answer was one `journalctl -k` line that had been printed on every boot since the first reset: `x86/amd: Previous system reset reason [0x08000800]: an uncorrected error caused a data fabric sync flood event` — an uncorrectable SoC/Infinity-Fabric error, present on seven of the last ten boots, one of which fired at load 1.53 and 22 W.
+
+**Why it fails:** A hardware-asserted reset leaves exactly the same evidence as a mysterious software crash — nothing. No panic, no OOM kill, no thermal event, no watchdog, no vmcore, and (because journald syncs every five minutes by default) not even the last minutes of log. That absence reads as "we haven't instrumented enough yet", which is why the natural response is another guard rather than another *source*. Meanwhile the platform's postmortem registers — the AMD reset-reason MSR, `/sys/fs/pstore`, RAS/MCE logs — sit outside the process the investigation is looking at, and no amount of care inside the software layer can reach them. The failure compounds: each new guard passes its own tests, gets certified, and becomes evidence that the *next* reset must have a subtler software cause. A near-idle occurrence (load 1.53) should have falsified the load hypothesis outright, but a guard already built is hard to argue with. Load correlation was real yet incidental — concurrency changes how often marginal hardware trips, not whether it is marginal.
+
+**Prevention:** When a machine fails as a machine — resets, freezes, spontaneous reboots, corruption — read the platform's own postmortem **first**, before writing a single mitigation: `journalctl -k -b 0 | grep -i 'reset reason'`, `/sys/fs/pstore`, `rasdaemon`/`mcelog`, `dmidecode` for firmware age. One line there outranks any amount of software telemetry, because it is the only witness that survives the OS never being notified. Then make it automatic and self-documenting, so the register is read for you and the next incident arrives with evidence attached: a reader wired into preflight and the doctor (`host-guard/reset-forensics.sh`, doctor row `reset-reason`), an idempotent postmortem bundle captured *before* anything sweeps the state that says who was running, fsync'd recording that outlives a power cut (1 Hz sampler, machine-wide event ledger, `journald SyncIntervalSec=15s`), and boot-id-keyed staleness so locks and pidfiles from the dead boot self-clear instead of being silently believed. Two discipline rules follow. **Distinguish "unreadable" from "clean"** — a checker that cannot read the register must report UNKNOWN, never PASS, or it certifies every host as healthy; and classify what it reads, since an ordinary `reboot` also writes a reset reason (`software wrote 0x6 to reset control register 0xCF9`) and counting it would cry wolf forever. **State plainly what software can and cannot do**: once the cause is hardware, the honest mitigations are firmware/BIOS updates, memory-timing changes, memtest and RMA — plus, at most, capping concurrency to shrink the exposure window. Tightening a CPU mask further, on a fault that fires at idle, is theatre that costs throughput and buys nothing.
+
+---
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index fe0a4aab..02ec6267 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -3,7 +3,7 @@
 One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
 only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
 nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
-headings; the next new entry takes the next free number (29) as `<NN>-<slug>.md` plus a
+headings; the next new entry takes the next free number (28) as `<NN>-<slug>.md` plus a
 row here (maintenance protocol §2).
 
 | # | Entry | Applies when | Rule (one line) |
@@ -34,5 +34,4 @@ row here (maintenance protocol §2).
 | 24 | [24-evidence-chasing-iterations.md](24-evidence-chasing-iterations.md) | evaluator/decomposer evidence demands | Evidence expires with change, not time; capture gaps ride the make-up lane or Depth: evidence — never an iteration goal |
 | 25 | [25-self-justifying-governor-bypass.md](25-self-justifying-governor-bypass.md) | gates on agent behavior | A governor must validate against signals the governed agent cannot author; a self-written justification line is a suggestion, not a gate |
 | 26 | [26-per-scope-caps-no-machine-aggregate.md](26-per-scope-caps-no-machine-aggregate.md) | resource caps on shared hardware | Per-scope ceilings need a machine-level aggregate over a registry of live consumers, plus verification of every host assumption they rest on |
-| 27 | [27-styled-verdict-cells-unparsed.md](27-styled-verdict-cells-unparsed.md) | parsing verdicts out of agent markdown | Normalize emphasis and annotations; absence-of-verdict is never PASS |
-| 28 | [28-plan-line-suppresses-lane.md](28-plan-line-suppresses-lane.md) | gating a verification lane | Gate lanes on engine-parsed facts, not model-written plan prose |
+| 27 | [27-software-guards-without-reset-reason.md](27-software-guards-without-reset-reason.md) | a machine resets, freezes, or reboots itself | Read the platform's own postmortem registers (reset reason, pstore, RAS) BEFORE building another software guard; "unreadable" is never "clean" |
diff --git a/incredible_auto_dev/.claude/commands/goal-status.md b/incredible_auto_dev/.claude/commands/goal-status.md
index ebcfada4..0feaaf61 100644
--- a/incredible_auto_dev/.claude/commands/goal-status.md
+++ b/incredible_auto_dev/.claude/commands/goal-status.md
@@ -21,6 +21,21 @@ the engine, dispatch agents, or write anything.
    interrupted/orphaned (e.g. a Ctrl+C that never reached the detached engine) —
    say so and point to `/goal-resume <sid>`. Also point the user at the full
    timestamped log: `tail -f runs/goal-session-<sid>/engine.log`.
+   **Distinguish a machine reset from an orphan.** Compare the pid file's mtime
+   against this boot: `ls -l --time-style=+%s runs/goal-session-<sid>/engine.pid`
+   versus `awk '/^btime /{print $2}' /proc/stat`. A pid file written BEFORE the
+   boot means the machine went down under the engine — a hardware event, not
+   something the session did wrong. Report it that way, with:
+   - **when** it died — the last pre-boot row of `~/.cache/iad/host-guard/hwmon/hwmon.csv`
+     (or `logs/hwmon/hwmon.csv`), which is fsync'd per second and outlives the journal;
+   - **what it was doing** — `current_iter` from `session.json` plus the last line
+     of `runs/goal-session-<sid>/telemetry.jsonl`, and the machine-wide ledger
+     `~/.cache/iad/host-guard/events.jsonl` for the cross-repo picture;
+   - **why** — `scripts/automation/host-guard/reset-forensics.sh check` and the
+     postmortem at `~/.cache/iad/host-guard/postmortems/latest.md`.
+   Then point at `/goal-resume <sid>`, which clears the stale locks itself. Say
+   plainly that a reset of this class is a hardware fault (see `docs/host-guard.md`
+   § After a hardware reset), so resuming is safe and the iteration is not lost.
 6. Summarize plainly whether the session is **running**, **paused** (and exactly
    how to resume — e.g. review the blueprint then `/goal-resume`; for
    `AWAITING_INTENT_REVIEW` point at `runs/goal-session-<sid>/intent-review.md`,
diff --git a/incredible_auto_dev/commands/goal-status.md b/incredible_auto_dev/commands/goal-status.md
index ebcfada4..0feaaf61 100644
--- a/incredible_auto_dev/commands/goal-status.md
+++ b/incredible_auto_dev/commands/goal-status.md
@@ -21,6 +21,21 @@ the engine, dispatch agents, or write anything.
    interrupted/orphaned (e.g. a Ctrl+C that never reached the detached engine) —
    say so and point to `/goal-resume <sid>`. Also point the user at the full
    timestamped log: `tail -f runs/goal-session-<sid>/engine.log`.
+   **Distinguish a machine reset from an orphan.** Compare the pid file's mtime
+   against this boot: `ls -l --time-style=+%s runs/goal-session-<sid>/engine.pid`
+   versus `awk '/^btime /{print $2}' /proc/stat`. A pid file written BEFORE the
+   boot means the machine went down under the engine — a hardware event, not
+   something the session did wrong. Report it that way, with:
+   - **when** it died — the last pre-boot row of `~/.cache/iad/host-guard/hwmon/hwmon.csv`
+     (or `logs/hwmon/hwmon.csv`), which is fsync'd per second and outlives the journal;
+   - **what it was doing** — `current_iter` from `session.json` plus the last line
+     of `runs/goal-session-<sid>/telemetry.jsonl`, and the machine-wide ledger
+     `~/.cache/iad/host-guard/events.jsonl` for the cross-repo picture;
+   - **why** — `scripts/automation/host-guard/reset-forensics.sh check` and the
+     postmortem at `~/.cache/iad/host-guard/postmortems/latest.md`.
+   Then point at `/goal-resume <sid>`, which clears the stale locks itself. Say
+   plainly that a reset of this class is a hardware fault (see `docs/host-guard.md`
+   § After a hardware reset), so resuming is safe and the iteration is not lost.
 6. Summarize plainly whether the session is **running**, **paused** (and exactly
    how to resume — e.g. review the blueprint then `/goal-resume`; for
    `AWAITING_INTENT_REVIEW` point at `runs/goal-session-<sid>/intent-review.md`,
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index faadd1f5..9c0a0277 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -51,9 +51,23 @@ So a second file, owned by the machine rather than by any repo, declares what
 HOST_GUARD_GLOBAL_CPU_LIST="0-3,8-11"   # every session's mask must be a SUBSET
 HOST_GUARD_GLOBAL_MEMORY_BUDGET="22G"   # Σ over projects of max(MemoryHigh)
 HOST_GUARD_REQUIRE_BOOST_OFF=1          # /sys/.../cpufreq/boost must read 0
-HOST_GUARD_GLOBAL_ON_CONFLICT=pause     # only 'pause' is implemented
+HOST_GUARD_MAX_ENGINES=1                # concurrent goal engines (absent = unlimited)
 ```
 
+`HOST_GUARD_MAX_ENGINES` caps how many goal-mode engines may run at once across
+the whole machine. Over the cap, the **junior** engine takes the ordinary
+resumable `AWAITING_HOST_GUARD` pause and continues when the senior finishes;
+the senior only warns. Absent ⇒ unlimited.
+
+It exists for one situation: a host whose resets turn out to be **hardware**
+(see § After a hardware reset). Nothing a guard can do prevents those, so a
+narrower CPU mask is theatre — but be clear-eyed that this knob is not a fix
+either. It buys **exposure time, not prevention**: fewer hours under load means
+fewer chances to trip, and nothing more. On the incident host the fault fired at
+load 1.53 as readily as under two concurrent sessions, so the cap was released
+within hours in favour of the real remediation. Its durable use is narrower and
+better: pinning a soak week to a single project so one variable moves at a time.
+
 Every guarded context publishes a record (pid, start time, boot id, project,
 mask, memory ceiling) into a registry under
 `${CHAIN_TMP_ROOT:-~/.cache/iad}/host-guard/registry/`, so any session can see
@@ -106,6 +120,115 @@ cat /sys/devices/system/cpu/cpufreq/boost      # must print 0
 `scripts/automation/doctor.sh --only cpu-boost` reports both the live knob and
 whether the rule that survives a reboot exists.
 
+## After a hardware reset — root-cause runbook
+
+**Read this before tightening anything.** On 2026-07-30 17:14:08 this host reset
+with every host-guard mitigation in force: both projects inside `0-3,8-11`,
+10G+10G against a 22G budget, boost off and persisted, QA browsers confined,
+both engines registered in the machine-global registry, every check green. At
+T-1s the 1 Hz sampler recorded 65 °C, 26 W, load 6.54, 11.5 GB free, memory PSI
+0.00. The cause was never visible to any software check — the CPU printed it on
+the next boot:
+
+```
+x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+         caused a data fabric sync flood event
+```
+
+A data fabric sync flood is an **uncorrectable SoC/Infinity-Fabric error**. The
+hardware asserts reset immediately; the kernel is never notified, so there is no
+panic, no OOM, no thermal event and no log — which is exactly why six earlier
+resets were misread as load problems. Seven of the last ten boots carried a
+fault-class line, and one of them fired at load 1.53 and 22 W: this is hardware
+**marginality**, not a load limit. Concurrency only changes how often it trips.
+
+The chain's job is therefore to surface, preserve, recover and cap — never to
+pretend it can prevent this:
+
+```bash
+scripts/automation/host-guard/reset-forensics.sh check       # what the platform says
+scripts/automation/host-guard/reset-forensics.sh report      # the newest postmortem
+scripts/automation/doctor.sh --only reset-reason             # same verdict as a row
+```
+
+Every engine preflight writes one idempotent bundle per dead boot into
+`~/.cache/iad/host-guard/postmortems/<boot-id>.md`: the verbatim reset line, the
+fault streak, the registry records naming which projects and sessions were
+running, the final pre-reset second of hardware telemetry from every sampler,
+those sessions' telemetry/engine-log tails, and the machine-wide event ledger.
+Run it **before** resuming a session — the preflight registry sweep is what
+erases the "who was running" evidence.
+
+### Fixing it (all need root; run them yourself, one change per soak week)
+
+```bash
+# 1. journald syncs every 5 min by default — the 07-30 reset erased the final
+#    3m42s of journal. 15 s keeps the tail.
+sudo mkdir -p /etc/systemd/journald.conf.d \
+  && printf '[Journal]\nSyncIntervalSec=15s\n' | sudo tee /etc/systemd/journald.conf.d/99-iad-sync.conf \
+  && sudo systemctl restart systemd-journald
+
+# 2. rasdaemon records the memory/fabric error itself (address, DIMM) — this is
+#    what turns "sync flood" into an actionable RMA or firmware bug report.
+sudo apt-get install -y rasdaemon && sudo systemctl enable --now rasdaemon
+
+# 3. One-time: firmware crash records the kernel could not write.
+sudo sh -c 'ls -la /sys/fs/pstore/ && head -c 4000 /sys/fs/pstore/* 2>/dev/null'
+
+# 4. BIOS/AGESA age is the single most common fix for this signature.
+sudo dmidecode -s bios-version && sudo dmidecode -s bios-release-date
+
+# 5. The definitive DRAM check — run a full pass overnight.
+sudo apt-get install -y memtest86+ && sudo update-grub
+```
+
+Then, in this order, one per week so causality stays readable: **update the
+BIOS**; set memory to **baseline JEDEC** instead of the EXPO/XMP profile; if
+memtest reports errors, reseat/swap the SO-DIMM and RMA. A commonly reported
+workaround for this signature is limiting deep C-states (it costs idle power and
+reverts on reboot):
+
+```bash
+for f in /sys/devices/system/cpu/cpu*/cpuidle/state[2-9]/disable; do echo 1 | sudo tee "$f" >/dev/null; done
+```
+
+`doctor.sh --only ras-logging` verifies what it can read without root (the
+journald drop-in and the rasdaemon unit) and stays silent on hosts that have no
+reset history.
+
+**Acceptance:** seven consecutive days with `reset-reason` reporting CLEAN on
+every boot. That replaces the "7-day zero-unclean-shutdown soak" HOST-1 claimed,
+which reset #7 refuted.
+
+## Machine-global hardware sampler
+
+One 1 Hz sampler covers the machine — it is the only artifact that survives a
+power-cut with its last second intact, because it fsyncs every line.
+
+```bash
+cp scripts/automation/host-guard/iad-hwmon.service ~/.config/systemd/user/
+systemctl --user daemon-reload && systemctl --user enable --now iad-hwmon.service
+loginctl show-user "$USER" --property=Linger      # must print Linger=yes
+tail -2 ~/.cache/iad/host-guard/hwmon/hwmon.csv
+```
+
+No root is needed (it is a `--user` unit). It writes
+`~/.cache/iad/host-guard/hwmon/hwmon.csv`, restarts itself after every reset,
+and keeps two rotated generations (~8 days). Per-repo samplers remain as a
+fallback: an engine preflight only starts one when no machine-global sampler is
+fresh, so migrating a project is just retiring its old unit. If a project still
+runs its own `hwmon-log.service`, disable it after enabling this one.
+
+## Machine-wide event ledger
+
+`~/.cache/iad/host-guard/events.jsonl` — one fsync'd JSON line per chain event
+for the WHOLE machine (engine start/stop, iteration start, every agent dispatch
+and its exit code, each healthy aggregate verdict, every pause). It exists
+because after a reset nothing could answer "what were both repos doing in the
+final seconds?": the aggregate verdict was silent when it passed,
+`telemetry.jsonl` is per-session and never fsync'd, and `engine.log` only exists
+in interactive mode. Filter by `.project` for one repo, `.boot` for one boot.
+
 ## Browser QA confinement
 
 Confining process *trees* is not enough for browser QA. The Chrome MCP does not
@@ -191,10 +314,19 @@ Pump browsers are made safe by affinity instead, which needs no name.
 7. **Browser confinement** (`host-guard/browser-confine.sh`) — QA browsers and
    Chrome-MCP servers that escaped the process tree, see below.
 8. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
-   pressure/memory to `<repo>/logs/hwmon/hwmon.csv`, fsync per line, so the
-   final pre-reset second survives a hard reset. `{run|start|stop|status|watch}`;
-   `status`/`start` recognize an externally-run sampler (e.g. a systemd user
-   unit running `run`) by csv freshness and never double-run.
+   pressure/memory/clock, fsync per line, so the final pre-reset second survives
+   a hard reset. Writes `~/.cache/iad/host-guard/hwmon/hwmon.csv` under the
+   machine-global unit, else `<repo>/logs/hwmon/hwmon.csv`.
+   `{run|start|stop|status|watch}`; `status`/`start` recognize an externally-run
+   sampler — including the machine-global one — by csv freshness and never
+   double-run.
+9. **Reset-reason forensics** (`host-guard/reset-forensics.sh`) — reads the
+   platform's own reset register each boot and freezes a postmortem bundle when
+   the last boot died. `{check|ensure-postmortem|report}`; doctor row
+   `reset-reason`. The only layer that can explain a reset no software caused.
+10. **Machine event ledger** (`hg_event`, `lib/host-guard-registry.sh`) — one
+   fsync'd line per chain event for the whole machine, including the healthy
+   aggregate verdict that used to be silent.
 
 ## When `AWAITING_HOST_GUARD` fires
 
@@ -219,3 +351,19 @@ still collectively unbounded, a QA browser could keep a pre-confinement CPU
 mask, and the boost mitigation had silently lapsed at a reboot. Incident
 forensics and the cap-widening verification ladder live in the originating
 project: `trendora/project-extensions/host-guard/README.md`.
+
+A **seventh** reset on 2026-07-30 17:14:08 ended that line of reasoning. It
+happened with the machine-global layer deployed to both projects, armed, and
+green on every check. The answer had been in the kernel log the whole time —
+`Previous system reset reason [0x08000800]: an uncorrected error caused a data
+fabric sync flood event`, present on seven of the last ten boots, once at load
+1.53. The root cause is **hardware** (DDR5/Infinity-Fabric marginality on
+non-ECC SO-DIMMs, BIOS 1.26 dated 09/2025), and no CPU mask, memory ceiling or
+browser confinement can prevent it.
+
+Three generations of guard were built to stop something the CPU was already
+naming on every boot. That is the lesson recorded as anti-pattern 27: **read the
+platform's own postmortem registers before iterating on software mitigations.**
+Since then these layers surface the hardware's verdict, preserve the evidence,
+recover honestly, and cap concurrency — see § After a hardware reset for the
+remediation that actually applies.
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index 557ba36b..a678f754 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -4349,8 +4349,191 @@ Machine-global aggregate bound + QA-browser confinement + host-assumption verifi
   (`run-phase.sh` Branch-QA + Branch-UI) onto one shared browser. Pump browsers are made
   safe by affinity instead, which needs no name.
 - **Failure-mode entry:** `.claude/anti-patterns/26-per-scope-caps-no-machine-aggregate.md`.
-- **Owner action outstanding:** re-apply and PERSIST boost-off (docs/host-guard.md
-  § Boost persistence). Until then the engine pauses `AWAITING_HOST_GUARD` by design.
-- **Verification still owed (G8-class):** subtree-pull both projects, a supervised
-  concurrent `/goal-step` per project verifying the live union stays inside `0-3,8-11`,
-  then the 7-day zero-unclean-shutdown soak (trendora README Stage E).
+- **Owner action outstanding:** ~~re-apply and PERSIST boost-off~~ — **DONE 2026-07-29
+  19:40**: `/etc/tmpfiles.d/cpufreq-boost.conf` installed and the knob reads 0 (verified
+  on-disk 2026-07-30).
+- **Verification still owed (G8-class):** ~~subtree-pull both projects~~ — **DONE
+  2026-07-29** (tapeology `8c737c1` 19:45, trendora `e402ce9b` 19:58; all 13 files
+  byte-identical). ~~7-day zero-unclean-shutdown soak~~ — **REFUTED, see addendum.**
+
+**ADDENDUM 2026-07-30 — the soak failed and the root cause is HARDWARE.**
+
+Reset #7 at **2026-07-30 17:14:08** happened with everything above deployed, armed and
+green: both projects inside `0-3,8-11`, `10G+10G` under the 22G budget, boost off and
+persisted, QA browsers and MCP servers confined, both engines registered in the
+machine-global registry, `AWAITING_HOST_GUARD` count 0. At T-1s the 1 Hz sampler recorded
+65 °C, 26 W, load 6.54 on 8 threads, 11.5 GB free, memory PSI 0.00. Machine back up 21 s
+later.
+
+The cause was never visible to any software check. The CPU prints it on every boot:
+
+```
+x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+         caused a data fabric sync flood event
+```
+
+Present on **7 of the last 10 boots**; one of those resets fired at load 1.53 / 22 W, which
+falsifies the load hypothesis outright. This is an uncorrectable SoC/Infinity-Fabric error
+— DDR5/fabric marginality on non-ECC SO-DIMMs, BIOS 1.26 dated 09/2025 — and the hardware
+asserts reset with the kernel never notified. **No CPU mask, memory ceiling, or browser
+confinement can prevent this class.** HOST-1's mitigations were correct as far as they go
+(the mask union and memory sum WERE real defects) but they were never sufficient, and
+tightening them further is theatre.
+
+Recorded as `.claude/anti-patterns/27-software-guards-without-reset-reason.md`: read the
+platform's own postmortem registers BEFORE iterating on software guards. Remediation is
+firmware/hardware and belongs to the operator (docs/host-guard.md § After a hardware
+reset). The framework's job is now surface / preserve / recover / cap — HOST-2..HOST-9.
+
+- **Honesty note:** `HOST_GUARD_GLOBAL_ON_CONFLICT` shipped in 8a7a400 as a documented
+  knob that NO code ever read. It was deleted rather than implemented — pause is the only
+  sane semantic and is already hardwired.
+- **New acceptance test** (replaces the refuted soak): 7 consecutive days with
+  `doctor.sh --only reset-reason` reporting CLEAN on every boot.
+
+### HOST-2 — IN-PROGRESS 2026-07-30 · P1 · M · LOW
+
+- **Problem:** seven resets were debugged as software load problems while the kernel
+  printed the cause on every boot. Nothing read it, and nothing preserved the evidence:
+  the engine preflight's `hg_sweep` deletes exactly the registry records that say which
+  projects and sessions were running when the machine died.
+- **Current state:** `scripts/automation/host-guard/reset-forensics.sh` (new);
+  `doctor.sh` row `reset-reason`; `run-goal.sh:1026` `_host_guard_reset_forensics` called
+  at the TOP of `preflight_host_guard`, before the sweep at `:1088`.
+- **Change spec:** read the current boot's `Previous system reset reason` line
+  (journalctl → `/var/log/kern.log` → UNKNOWN; never dmesg, `dmesg_restrict` is on).
+  Classify fault vs planned reboot (`software wrote 0x6 to reset control register 0xCF9`
+  is a normal reboot and must NOT raise an alarm). On a fault, write one idempotent bundle
+  per dead boot to `~/.cache/iad/host-guard/postmortems/<boot-id>.md`: verbatim line, fault
+  streak over the last 10 boots, every registry record from the dead boot, the final
+  PRE-BOOT second of each sampler's telemetry (boot-relative — a sampler that restarted
+  would otherwise present live idle data as the time of death), session telemetry/engine.log
+  /session.json tails, ledger tail, journal tail.
+- **DoD:** `check` classifies fault/reboot/clean/unreadable; "unreadable" is never
+  reported as clean; bundle idempotent; no-op on hosts with no reset-reason line.
+- **Verify:** `bash tests/automation/test-reset-forensics.sh` (52/52);
+  `bash scripts/automation/host-guard/reset-forensics.sh ensure-postmortem` on this host
+  reproduces the 07-30 bundle with both dead engines and tapeology's 17:14:08 final sample.
+- **Files:** `scripts/automation/host-guard/reset-forensics.sh`, `doctor.sh`,
+  `run-goal.sh`, `tests/automation/test-reset-forensics.sh`.
+- **Rollback:** delete the script, the doctor row, and the single preflight call.
+
+### HOST-3 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Problem:** the remediation for a hardware fault needs root, which the chain does not
+  have and must not take; and the next postmortem will be just as thin unless the host's
+  own recording is improved first (journald lost the final 3m42s of the 07-30 reset; no
+  rasdaemon, so the fabric error itself was never recorded).
+- **Change spec:** `docs/host-guard.md` § After a hardware reset — copy-paste one-liners
+  the OWNER runs (journald `SyncIntervalSec=15s`, rasdaemon, pstore peek, BIOS version vs
+  GEEKOM support, memtest86+, optional C-state limiting), plus the one-change-per-soak-week
+  discipline. Doctor row `ras-logging` verifies read-only what it can and stays PASS on
+  hosts with no reset history.
+- **DoD/Verify:** row WARNs only with reset history; `test-reset-forensics.sh` § C.
+- **Files:** `docs/host-guard.md`, `doctor.sh`, `tests/automation/test-doctor.sh`.
+
+### HOST-4 — IN-PROGRESS 2026-07-30 · P1 · M · LOW
+
+- **Problem:** after the reset nothing could answer "what were BOTH repos doing in the
+  final seconds?". The aggregate verdict was silent when it passed, `telemetry.jsonl` is
+  per-session and never fsync'd, and `engine.log` exists only in interactive mode.
+- **Change spec:** `hg_event` in `lib/host-guard-registry.sh` → one fsync'd JSON line per
+  chain event into `~/.cache/iad/host-guard/events.jsonl` (machine-wide, `.project`/`.boot`
+  fields for filtering, 5 MiB ring). Seven call sites: engine start/stop, iteration start,
+  dispatch start/end (`agent_with_quota_retry` — the single chokepoint for all three
+  backends, so every agent in every repo is bracketed), the HEALTHY `aggregate_ok` verdict,
+  and pause. Oversized payloads are DROPPED, never truncated.
+- **DoD/Verify:** `test-host-guard.sh` §A (92/92) — valid JSON, no-op rule, rotation,
+  20 concurrent appenders → 20 valid lines.
+- **Files:** `lib/host-guard-registry.sh`, `lib/quota-retry.sh`, `run-goal.sh`.
+
+### HOST-5 — IN-PROGRESS 2026-07-30 · P1 · S · LOW-MED
+
+- **Problem:** the sampler was started per repo by each engine's preflight, so the machine
+  had two half-histories and an asymmetry that cost evidence — after the 07-30 reset only
+  trendora's sampler restarted; tapeology's stayed dead.
+- **Change spec:** `host-guard/iad-hwmon.service` (new, `--user`, `Restart=always`,
+  writes `~/.cache/iad/host-guard/hwmon/hwmon.csv`); `HOST_GUARD_HWMON_DIR` seam;
+  `status`/`start` recognize a fresh machine-global csv and never double-run (so the
+  per-repo preflight fallback simply stops firing); ring → 2 generations (~8 days);
+  append-only new column `cpu_mhz`. No `ac_online` — `/sys/class/power_supply` is empty on
+  this host, the column would be permanently blank.
+- **DoD/Verify:** 15-field v2 header; global-sampler detection; `.1`+`.2` rotation.
+- **Files:** `host-guard/hwmon-log.sh`, `host-guard/iad-hwmon.service`, `run-goal.sh`
+  (`_host_guard_latest_tctl` reads the machine csv first so the thermal gate survives).
+
+### HOST-6 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Problem:** a machine reset reuses the pid space, so locks and heartbeats left by the
+  dead boot can name a pid that is alive NOW — and `engine_lock_classify`'s cmdline check
+  can even confirm it, wedging a session that is not actually held.
+- **Change spec:** record `boot_id` in `acquire_engine_lock` metadata and classify a
+  foreign boot id as STALE (covers `.engine.lock` AND `runs/.phase.lock` AND the doctor row
+  in one edit); `hg_pid_matches <pid> <starttime>`; the iteration gate discards a
+  `.pump-alive` whose recorded start time no longer matches.
+- **Deliberately NOT done:** `trace/.lock` is a kernel flock — it dies with its holder and
+  a leftover file can never block. `engine.pid` already self-heals on resume
+  (`run-goal.sh:257-269`); its honesty half is HOST-7.
+- **DoD/Verify:** `test-engine-lock.sh` §A1b (44/44) — foreign boot id + live pid → STALE;
+  locks without the field keep old behaviour.
+
+### HOST-7 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Problem:** both sessions killed by the reset still read `in_progress` with no halt
+  marker. A session that silently reappears mid-iteration teaches the operator that
+  iterations vanish at random, when the truth is one hardware event with a postmortem
+  on disk.
+- **Change spec:** `hg_boot_epoch`/`hg_file_predates_boot` (`HOST_GUARD_BTIME_OVERRIDE`
+  test seam); `run-goal.sh` resume prints the reset banner + postmortem pointer and emits a
+  one-time `halt {"reason":"machine_reset"}` (env-prefixed with the session dir —
+  `telemetry_enabled` silently returns false before `GOAL_SESSION_DIR` is exported, so
+  without the prefix the event would never be written); `commands/goal-status.md` step 5
+  reports when/what/why with the hwmon, ledger and postmortem pointers.
+- **Files:** `lib/host-guard-registry.sh`, `run-goal.sh`, `commands/goal-status.md` (+
+  `.claude/commands/` mirror via `sync-cli-assets.py`).
+
+### HOST-8 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Change spec:** `HOST_GUARD_MAX_ENGINES` in the machine env — over the cap, the junior
+  engine takes the existing resumable `AWAITING_HOST_GUARD` pause via the extracted
+  `_hg_arbitrate` (same total order as every other breach class); the senior warns. Checked
+  BEFORE the no-budget early return so a machine can configure only the cap. Absent or
+  invalid ⇒ unlimited ⇒ today's behaviour (§20 no-op rule).
+- **Released same-day (2026-07-30, owner decision):** set to 1 on this host, then unset a
+  few hours later along with boost-off and the CPU mask. The honest reading is that all
+  three bought *exposure time*, never prevention — the fault fired at load 1.53 as readily
+  as under two concurrent sessions, and BIOS 1.26 turned out to be the latest, so the
+  remediation moved to C-state limiting and then memtest/RMA. The knob remains the way to
+  isolate a soak week to one project. Attribution is preserved regardless: every engine
+  start records the live mitigation set as a `host_state` ledger event (HOST-4), so the
+  next postmortem names the combination that was running. `HOST_GUARD_GLOBAL_ON_CONFLICT` deleted from env + docs.
+- **DoD/Verify:** `test-host-guard.sh` §A15 — junior PAUSE naming the knob, senior WARN,
+  cap=2 OK, absent/junk/0 OK, pump records don't count as engines.
+
+### HOST-9 — IN-PROGRESS 2026-07-30 · P1 · S · LOW (docs only)
+
+HOST-1 addendum above; anti-pattern 27; `docs/host-guard.md` root-cause rewrite + runbook;
+these items. **Stop-and-ask:** none (docs).
+
+### Known gaps — deliberately NOT fixed in this package (TODO)
+
+Each is real but none is on the path of a hardware-caused reset; fixing them alongside the
+forensics work would have blurred what this package is for.
+
+- **Demo-runner browsers escape every guard.** `lib/demo_runner.py:918-930` launches a
+  Playwright Chromium with no `--user-data-dir` under the superpowers profile root, so
+  `browser-confine.sh` Pass A/D cannot see it and `doctor.sh` classifies it as harmless
+  desktop Chrome. It inherits the engine's mask when spawned by a confined engine, but NOT
+  when `demo.sh --live` runs standalone.
+- **Registry dir is per-session overridable.** `hg_registry_dir` honours
+  `HOST_GUARD_REGISTRY_DIR`/`CHAIN_TMP_ROOT`; a project that sets either gets a PRIVATE
+  registry and silently drops out of the machine view — with no warning, because an empty
+  registry reads as "one live session, all fine". A machine-global facility should not be
+  addressable by a per-project variable.
+- **Registry heartbeat only refreshes at iteration boundaries.** `hg_register` runs at
+  preflight and each gate, so a record's mtime can be hours stale while live (07-30:
+  tapeology's engine record was last touched 81 minutes before the reset). Correspondingly
+  a project that starts mid-iteration is invisible until the current iteration ends.
+- **Trendora carries two un-upstreamed framework patches** worth reverse-porting:
+  `lib/common.sh` (force the browser lane when `CHAIN_GOAL_TARGET_JOURNEYS` is set) and
+  `lib/replay-lane.sh` (rc=7 backend-unreachable handling).
diff --git a/incredible_auto_dev/scripts/automation/doctor.sh b/incredible_auto_dev/scripts/automation/doctor.sh
old mode 100644
new mode 100755
index d2215a28..375126a6
--- a/incredible_auto_dev/scripts/automation/doctor.sh
+++ b/incredible_auto_dev/scripts/automation/doctor.sh
@@ -57,9 +57,20 @@ source "$SCRIPT_DIR/lib/common.sh"
 source "$SCRIPT_DIR/lib/engine-lock.sh"
 ROOT="${CHAIN_DOCTOR_REPO_ROOT:-$REPO_ROOT}"
 
+# Running the doctor under sudo is always a mistake, and a quiet one. sudo
+# resets HOME, so every check reads ROOT's world instead of yours: no machine
+# budget file, an empty host-guard registry, the wrong plugin cache — and the
+# table comes back looking healthy about a machine that is not the one you run
+# sessions on. With `sudo -E` it is worse: the postmortem write lands in YOUR
+# cache owned by root, and every later user-run forensics call fails on it.
+# Warn rather than refuse — the doctor is advisory by construction.
+if [[ "${EUID:-$(id -u)}" -eq 0 && -z "${CHAIN_DOCTOR_ALLOW_ROOT:-}" ]]; then
+  echo "[doctor] WARNING: running as root (HOME=$HOME). This table describes root's environment, not yours — host-guard, tmp-health and the reset-reason rows will all be wrong. Re-run it as your own user: bash scripts/automation/doctor.sh" >&2
+fi
+
 CHECKS=(python3 node playwright chrome-mcp gh-auth git-remote disk timeout jq
         pump-heartbeat engine-lock tmp-health chrome-exclusive mcp-affinity
-        host-guard cpu-boost ambient-env)
+        host-guard cpu-boost reset-reason ras-logging ambient-env)
 
 # Run a command under GNU/uutils timeout when available (network probes must
 # degrade, never hang). $1 = seconds, rest = command.
@@ -483,8 +494,15 @@ check_host_guard() {
       return
     fi
     verdict="$(hg_aggregate_verdict "")"
+    local n_eng=0 cap
+    while read -r r; do
+      [[ -n "$r" ]] || continue
+      [[ "$(_hg_rec_field "$r" kind)" == "engine" ]] && n_eng=$(( n_eng + 1 ))
+    done < <(hg_live_records)
+    cap="${HOST_GUARD_MAX_ENGINES:-}"
+    [[ "$cap" =~ ^[0-9]+$ ]] || cap="unlimited"
     case "$verdict" in
-      OK) echo "PASS|mask=$mask mem=$mem inside machine budget ${HOST_GUARD_GLOBAL_CPU_LIST}/${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-unset}; $n live guarded context(s): ${roots:-none}" ;;
+      OK) echo "PASS|mask=$mask mem=$mem inside machine budget ${HOST_GUARD_GLOBAL_CPU_LIST}/${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-unset}; engines=$n_eng/$cap; $n live guarded context(s): ${roots:-none}" ;;
       *)  echo "WARN|${verdict#*|}" ;;
     esac
   )
@@ -523,6 +541,82 @@ check_cpu_boost() {
   fi
 }
 
+# EVIDENCE (2026-07-30 17:14:08, reset #7): the machine hard-reset with EVERY
+# host-guard mitigation in force — masks inside the machine budget, 10G+10G under
+# a 22G budget, boost off and persisted, QA browsers confined — at 65 °C, 26 W,
+# 11.5 GB free, memory PSI 0.00. The cause was never visible to any of those
+# checks; it was printed by the CPU itself on the next boot:
+#   x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+#            caused a data fabric sync flood event
+# Seven of the last ten boots carried a fault-class line. This row surfaces the
+# hardware's own verdict, which no software-side check can infer.
+#
+# FAIL (not WARN) when the last boot died: a host that resets under load is the
+# single most destructive environment fact there is — it destroys whole
+# iterations. The doctor still never gates (exit 0 by construction), so FAIL here
+# costs nothing but attention, which is exactly what it should cost.
+#
+# This row is the doctor's SECOND sanctioned write (after the tmp-health probe):
+# ensure-postmortem freezes the evidence bundle. It is idempotent, lives in the
+# cache root, never touches a repo — and "the operator ran doctor right after a
+# crash" is precisely when the bundle must be created, because the next engine
+# preflight sweeps the registry records that say who was running.
+check_reset_reason() {
+  local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" verdict pm path
+  [[ -f "$script" ]] || { echo "PASS|reset-forensics.sh not present — no reset-reason reader on this install"; return; }
+  verdict="$(_bounded 20 bash "$script" check 2>/dev/null)"
+  case "$verdict" in
+    RESET\|*)
+      local hex cause streak prev
+      IFS='|' read -r _ hex cause streak prev <<< "$verdict"
+      : "$prev"
+      pm="$(_bounded 30 bash "$script" ensure-postmortem 2>/dev/null)"
+      path="${pm#POSTMORTEM|}"; path="${path%|*}"
+      [[ "$pm" == POSTMORTEM\|* ]] || path="(bundle unavailable: ${pm})"
+      echo "FAIL|the previous boot ended in a HARDWARE-asserted reset: $cause ($hex); $streak recent boots. No CPU mask or memory ceiling can prevent this — postmortem: $path (docs/host-guard.md § After a hardware reset)"
+      ;;
+    CLEAN\|*)  echo "PASS|${verdict#CLEAN|}" ;;
+    UNKNOWN\|*) echo "WARN|${verdict#UNKNOWN|}" ;;
+    *)         echo "WARN|reset-forensics.sh returned an unparseable verdict: ${verdict:-<empty>}" ;;
+  esac
+}
+
+# Two host-level recording facilities that only matter once a machine HAS had a
+# hardware reset, and that the chain cannot install for itself (both need root):
+#   - journald's default SyncIntervalSec is 5 minutes, so the 2026-07-30 reset
+#     erased the final 3m42s of journal; only the 1 Hz fsync'd hwmon csv survived.
+#   - rasdaemon records the memory/fabric error itself (address, DIMM), which is
+#     what turns "sync flood" into an actionable RMA or BIOS bug report.
+# WARN, never FAIL: these improve the NEXT postmortem, they do not make the host
+# unsafe. And on a machine with no reset history the row stays PASS — a framework
+# must not nag hosts that never had the incident.
+check_ras_logging() {
+  local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" hist=0 jdir ras missing=""
+  if [[ -f "$script" ]] && [[ "$(_bounded 20 bash "$script" check 2>/dev/null)" == RESET\|* ]]; then
+    hist=1
+  fi
+  jdir="${CHAIN_DOCTOR_JOURNALD_DIR:-/etc/systemd/journald.conf.d}"
+  if ! grep -rqs 'SyncIntervalSec' "$jdir" 2>/dev/null; then
+    missing+="journald SyncIntervalSec drop-in ($jdir); "
+  fi
+  # `systemctl is-active` PRINTS its verdict and exits non-zero for anything but
+  # "active", so a `|| echo` fallback would append a second line and smuggle a
+  # newline into this row (the wrapper reads only the last line and would call
+  # the whole check crashed). First line only, always.
+  ras="${CHAIN_DOCTOR_RAS_STATE:-$(systemctl is-active rasdaemon 2>/dev/null | head -n 1)}"
+  [[ -n "$ras" ]] || ras="unknown"
+  [[ "$ras" == "active" ]] || missing+="rasdaemon (is-active=$ras); "
+  if [[ -z "$missing" ]]; then
+    echo "PASS|crash recording hardened: journald sync drop-in present and rasdaemon active"
+    return
+  fi
+  if (( hist == 0 )); then
+    echo "PASS|no hardware-reset history on this host — journald/rasdaemon hardening is optional (missing: ${missing%; })"
+    return
+  fi
+  echo "WARN|this host HAS hardware-reset history but the next postmortem will be poorer: ${missing%; }— see docs/host-guard.md § After a hardware reset (both need one sudo command)"
+}
+
 # EVIDENCE (§9 measurement discipline): benchmark/measurement runs record
 # "no ambient CHAIN_* vars" as a precondition — stray knobs silently alter
 # engine behavior. The engine snapshots names BEFORE its own exports
diff --git a/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
index e5632fd5..ec921f5c 100755
--- a/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
@@ -40,11 +40,24 @@ ENV_FILE="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
 
 INTERVAL="${HOST_GUARD_SAMPLER_INTERVAL:-1}"
 MAX_BYTES="${HOST_GUARD_SAMPLER_MAX_BYTES:-10485760}"
-LOG_DIR="$REPO_ROOT/logs/hwmon"
+# HOST_GUARD_HWMON_DIR lets the machine-global systemd user unit
+# (iad-hwmon.service) put the csv in the cache root instead of one repo's logs/.
+# Unset ⇒ per-repo placement, exactly as before.
+LOG_DIR="${HOST_GUARD_HWMON_DIR:-$REPO_ROOT/logs/hwmon}"
 CSV="$LOG_DIR/hwmon.csv"
 PIDFILE="$LOG_DIR/hwmon.pid"
 DAEMON_LOG="$LOG_DIR/hwmon.log"
-HEADER="epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10"
+# Where the machine-global sampler writes. One 1 Hz sampler is enough for the
+# whole machine; a per-repo engine must not start a second writer when it is
+# already running (that is how two repos ended up with two half-histories).
+GLOBAL_CSV="${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv"
+# Schema is APPEND-ONLY: new columns go at the END so every existing reader
+# (field 1 = epoch, field 2 = tctl) keeps working against old and new files.
+# cpu_mhz was added after the 2026-07-30 sync-flood reset — clock behaviour is
+# the cheapest signal correlated with fabric/VRM transients that the previous
+# schema could not see. (No ac_online column: /sys/class/power_supply is empty
+# on this class of mini-PC, so it would be a permanently blank field.)
+HEADER="epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10,cpu_mhz"
 
 # ── Sensor resolution (by hwmon name, once at startup) ─────────────────────
 TCTL="" GPU_TEMP="" PPT_NOW="" PPT_AVG="" NVME_T="" DIMM0="" DIMM1="" ACPITZ=""
@@ -89,6 +102,18 @@ _psi_avg10() { # $1 /proc/pressure/{cpu,memory} → the "some avg10" value
   printf '%s' "${line%% *}"
   return 0
 }
+_cpu_mhz() { # mean current core clock in MHz ("" when cpufreq is unavailable)
+  local sum=0 n=0 v f
+  for f in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq; do
+    [[ -r "$f" ]] || continue
+    IFS= read -r v < "$f" 2>/dev/null || continue
+    [[ "$v" =~ ^[0-9]+$ ]] || continue
+    sum=$(( sum + v )); n=$(( n + 1 ))
+  done
+  (( n > 0 )) || return 0
+  printf '%s' $(( sum / n / 1000 ))
+  return 0
+}
 MEM_AVAIL_MB="" SWAP_FREE_MB=""
 _mem_fields() {
   MEM_AVAIL_MB="" SWAP_FREE_MB=""
@@ -107,7 +132,7 @@ cmd_run() {
   mkdir -p "$LOG_DIR"
   resolve_sensors
   [[ -f "$CSV" ]] || printf '%s\n' "$HEADER" > "$CSV"
-  local ts tctl gpu ppt pavg nvt d0 d1 az load1 rest psic psim size
+  local ts tctl gpu ppt pavg nvt d0 d1 az load1 rest psic psim size mhz
   while :; do
     ts=$EPOCHSECONDS
     tctl=$(_read_scaled "$TCTL" 1000)
@@ -122,14 +147,19 @@ cmd_run() {
     _mem_fields
     psic=$(_psi_avg10 /proc/pressure/cpu)
     psim=$(_psi_avg10 /proc/pressure/memory)
-    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
+    mhz=$(_cpu_mhz)
+    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
       "$ts" "$tctl" "$gpu" "$ppt" "$pavg" "$nvt" "$d0" "$d1" "$az" \
-      "$load1" "$MEM_AVAIL_MB" "$SWAP_FREE_MB" "$psic" "$psim" >> "$CSV"
+      "$load1" "$MEM_AVAIL_MB" "$SWAP_FREE_MB" "$psic" "$psim" "$mhz" >> "$CSV"
     # fsync the csv so the last pre-crash line survives an instant reset
     # (uutils-compatible file-arg form; plain `sync` as fallback).
     sync "$CSV" 2>/dev/null || sync 2>/dev/null || true
     size=$(stat -c %s "$CSV" 2>/dev/null || echo 0)
     if [[ "$size" =~ ^[0-9]+$ ]] && (( size > MAX_BYTES )); then
+      # Two generations, not one: at 1 Hz a 10 MiB file is ~4 days, and the
+      # incident history that matters spans more than one reset. tapeology's
+      # ring was 99.3% full when the machine went down.
+      if [[ -f "$CSV.1" ]]; then mv -f "$CSV.1" "$CSV.2"; fi
       mv -f "$CSV" "$CSV.1"
       printf '%s\n' "$HEADER" > "$CSV"
     fi
@@ -137,12 +167,17 @@ cmd_run() {
   done
 }
 
-_csv_fresh() { # true iff the csv was written within the last INTERVAL+5 s
-  local mtime
-  [[ -f "$CSV" ]] || return 1
-  mtime=$(stat -c %Y "$CSV" 2>/dev/null || echo 0)
+_file_fresh() { # true iff $1 was written within the last INTERVAL+5 s
+  local f="${1:-}" mtime
+  [[ -f "$f" ]] || return 1
+  mtime=$(stat -c %Y "$f" 2>/dev/null || echo 0)
   (( EPOCHSECONDS - mtime <= INTERVAL + 5 ))
 }
+_csv_fresh() { _file_fresh "$CSV"; }
+# A live machine-global sampler covers this repo too — the hardware it samples
+# is the same hardware. Distinct file only; when this process IS the global
+# sampler the two paths are identical and this is never consulted.
+_global_fresh() { [[ "$GLOBAL_CSV" != "$CSV" ]] && _file_fresh "$GLOBAL_CSV"; }
 
 cmd_start() {
   mkdir -p "$LOG_DIR"
@@ -158,6 +193,10 @@ cmd_start() {
     echo "hwmon-log: already running (external sampler, csv fresh)"
     return 0
   fi
+  if _global_fresh; then
+    echo "hwmon-log: already running (machine-global sampler → $GLOBAL_CSV)"
+    return 0
+  fi
   nohup env HOST_GUARD_ROOT="$REPO_ROOT" bash "$HERE/hwmon-log.sh" run >> "$DAEMON_LOG" 2>&1 &
   pid=$!
   disown "$pid" 2>/dev/null || true
@@ -202,6 +241,11 @@ cmd_status() {
     echo "hwmon-log: running (external sampler), csv fresh: $last"
     return 0
   fi
+  if _global_fresh; then
+    IFS= read -r last < <(tail -n 1 "$GLOBAL_CSV" 2>/dev/null) || last=""
+    echo "hwmon-log: running (machine-global sampler), csv fresh: $last"
+    return 0
+  fi
   echo "hwmon-log: not running"
   return 1
 }
diff --git a/incredible_auto_dev/scripts/automation/host-guard/iad-hwmon.service b/incredible_auto_dev/scripts/automation/host-guard/iad-hwmon.service
new file mode 100644
index 00000000..085f825c
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/iad-hwmon.service
@@ -0,0 +1,29 @@
+[Unit]
+# Machine-global 1 Hz hardware sampler for host-guard crash forensics.
+#
+# WHY A MACHINE UNIT: the sampler used to be started per repo by each engine's
+# preflight. That produced two half-histories and an asymmetry that cost real
+# evidence — after the 2026-07-30 hardware reset only one project's sampler came
+# back, so the other repo's csv stayed frozen and its post-reset behaviour was
+# unrecorded. The hardware is one machine; one sampler covers it, restarts
+# itself after every reset, and writes outside every repo.
+#
+# INSTALL (no root — this is a --user unit; see docs/host-guard.md):
+#   cp scripts/automation/host-guard/iad-hwmon.service ~/.config/systemd/user/
+#   systemctl --user daemon-reload && systemctl --user enable --now iad-hwmon.service
+#   loginctl show-user "$USER" --property=Linger   # must be Linger=yes
+# Edit ExecStart if your framework clone is not at ~/Git/incredible_auto_dev.
+Description=iad host-guard hwmon sampler (1 Hz, machine-global crash forensics)
+
+[Service]
+Type=simple
+Environment=HOST_GUARD_HWMON_DIR=%h/.cache/iad/host-guard/hwmon
+ExecStart=/usr/bin/bash %h/Git/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh run
+Restart=always
+RestartSec=5
+# Never let the forensics sampler become the thing that hurts the host.
+Nice=10
+IOSchedulingClass=idle
+
+[Install]
+WantedBy=default.target
diff --git a/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh b/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
new file mode 100755
index 00000000..80118cc3
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
@@ -0,0 +1,443 @@
+#!/usr/bin/env bash
+# reset-forensics.sh — the platform's own postmortem, read at every boot.
+#
+# WHY: seven hard resets on this host were debugged as software load problems
+# through three generations of guard (per-scope caps → machine-global aggregate
+# → QA-browser confinement) while the CPU had been printing the answer into the
+# kernel log on every single boot:
+#
+#   x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+#            caused a data fabric sync flood event
+#
+# A data fabric sync flood is an uncorrectable SoC/Infinity-Fabric error: the
+# hardware asserts reset immediately, the OS is never notified, and NOTHING
+# software does can prevent it. The 2026-07-30 17:14:08 reset happened with the
+# machine-global aggregate bound armed and every check green — both projects
+# inside 0-3,8-11, 10G+10G under a 22G budget, boost off and persisted, QA
+# browsers confined — at 65 °C, 26 W, 11.5 GB free, memory PSI 0.00.
+#
+# So this script does not try to PREVENT anything. It makes every reset
+# self-documenting: read the register, and when the last boot died, freeze what
+# the chain was doing into a bundle BEFORE the engine's own registry sweep
+# (run-goal.sh preflight) erases the only record of who was running.
+#
+# Usage / stdout contract — exactly one line, ALWAYS exit 0 (advisory by
+# construction, like doctor.sh; a broken forensics reader must never stop a run):
+#   check              RESET|<hex>|<cause>|<hits>/<boots>|<prev_boot_id>
+#                      CLEAN|<why>
+#                      UNKNOWN|<why>
+#   ensure-postmortem  POSTMORTEM|<path>|new   POSTMORTEM|<path>|existing
+#                      NONE|<why>              UNKNOWN|<why>
+#   report             print the newest bundle (rc 1 when there is none)
+#
+# NO-OP RULE (roadmap §20): a host whose kernel prints no reset-reason line —
+# every non-AMD box, and every AMD box that has never reset — reports CLEAN and
+# writes nothing at all. No config file is required for the read-only paths.
+#
+# Injection seams (how tests fake the world — no root, no journal, no API):
+#   HOST_GUARD_RESET_KLOG_FILE       stands in for `journalctl -k -b 0`
+#   HOST_GUARD_RESET_KLOG_DIR        per-boot logs: <dir>/<boot-id>.klog (streak)
+#   HOST_GUARD_RESET_BOOTS_FILE      stands in for `journalctl --list-boots`
+#   HOST_GUARD_RESET_JOURNAL_TAIL_FILE  stands in for `journalctl -b -1 -n 80`
+#   HOST_GUARD_POSTMORTEM_DIR        bundle dir (default <tmp-root>/host-guard/postmortems)
+#   HOST_GUARD_RESET_BOOT_WINDOW     how many recent boots the streak scans (10)
+#   HOST_GUARD_REGISTRY_DIR / CHAIN_TMP_ROOT / HOST_GUARD_EVENTS_FILE (via the lib)
+#
+# COST: every kernel-log read is a STREAM into `grep -m1`/`grep -q`, which exits
+# at the first hit and SIGPIPEs the producer, so nothing is ever slurped into
+# memory. Measured on the incident host: ~10 ms per boot, ~120 ms for a 10-boot
+# streak. Do NOT "optimize" this with a head bound — the line lands at kernel
+# log line 942 here, and a bound short enough to matter would report CLEAN on a
+# machine that had just reset.
+#
+# No `set -e` and no `pipefail`: SIGPIPE on the producer is EXPECTED, and every
+# failure path degrades to UNKNOWN rather than to a dead script.
+set -u
+
+HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+
+# The registry library owns the paths this bundle joins over (registry dir,
+# record fields, boot id, events ledger). Source it when present; keep tiny
+# local fallbacks so a vendored copy that is missing the lib still reports.
+if [[ -f "$HERE/../lib/host-guard-registry.sh" ]]; then
+  # shellcheck source=../lib/host-guard-registry.sh
+  source "$HERE/../lib/host-guard-registry.sh"
+fi
+if ! declare -f hg_registry_dir >/dev/null 2>&1; then
+  hg_registry_dir() { echo "${HOST_GUARD_REGISTRY_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/registry}"; }
+  _hg_rec_field() { sed -n "s/^$2=//p" "$1" 2>/dev/null | head -n 1; }
+  _hg_boot_id() { cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo "unknown"; }
+  hg_boot_epoch() { awk '/^btime /{print $2; exit}' /proc/stat 2>/dev/null || echo 0; }
+fi
+
+RESET_PAT='Previous system reset reason'
+# NOT every reset-reason line is an incident. An ordinary `reboot` writes 0x6 to
+# the legacy reset control register 0xCF9, and the SoC dutifully reports it on
+# the next boot ("[0x00080800]: software wrote 0x6 to reset control register
+# 0xCF9"). Counting that as a fault would make every planned reboot look like a
+# crash and would cry wolf on hosts that never had an incident.
+BENIGN_PAT='software wrote|reset control register'
+WINDOW="${HOST_GUARD_RESET_BOOT_WINDOW:-10}"
+POSTMORTEM_DIR="${HOST_GUARD_POSTMORTEM_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/postmortems}"
+EVENTS_FILE="${HOST_GUARD_EVENTS_FILE:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/events.jsonl}"
+GLOBAL_HWMON="${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv"
+
+# ── Boot enumeration ────────────────────────────────────────────────────────
+
+_boots_stream() { # `journalctl --list-boots` text; rc 1 when unavailable
+  local out=""
+  if [[ -n "${HOST_GUARD_RESET_BOOTS_FILE:-}" ]]; then
+    [[ -r "$HOST_GUARD_RESET_BOOTS_FILE" ]] || return 1
+    cat "$HOST_GUARD_RESET_BOOTS_FILE"
+    return 0
+  fi
+  command -v journalctl >/dev/null 2>&1 || return 1
+  out="$(journalctl --list-boots --no-pager 2>/dev/null)"
+  [[ -n "$out" ]] || return 1
+  printf '%s\n' "$out"
+}
+
+# Rows only (drop the "IDX BOOT ID …" header): "<idx> <boot-id> <rest…>".
+_boot_rows() { _boots_stream | awk '$1 ~ /^-?[0-9]+$/ {print}'; }
+
+_prev_boot_id() { _boot_rows | awk '$1 == "-1" {print $2; exit}'; }
+
+_is_benign() { grep -qiE "$BENIGN_PAT" <<< "${1:-}"; }
+
+_boot_reset_line() { # $1 boot id → that boot's reset-reason line (empty if none)
+  local bid="${1:-}" f
+  if [[ -n "${HOST_GUARD_RESET_KLOG_DIR:-}" ]]; then
+    f="$HOST_GUARD_RESET_KLOG_DIR/$bid.klog"
+    [[ -r "$f" ]] || return 1
+    grep -i -m1 "$RESET_PAT" "$f" 2>/dev/null
+    return 0
+  fi
+  command -v journalctl >/dev/null 2>&1 || return 1
+  journalctl -k -b "$bid" --no-pager 2>/dev/null | grep -i -m1 "$RESET_PAT"
+  return 0
+}
+
+# ── Detection (sets globals; both subcommands share it) ─────────────────────
+
+_DET_STATUS="" _DET_LINE="" _DET_HEX="" _DET_CAUSE="" _DET_WHY=""
+_DET_HITS=0 _DET_TOTAL=0 _DET_PREV="" _DET_ROWS=""
+
+_streak() { # fills _DET_HITS/_DET_TOTAL/_DET_ROWS over the last $WINDOW boots
+  # _DET_HITS counts FAULT-class boots only; a planned reboot is recorded in the
+  # table as "reboot" so the history stays readable without inflating the count.
+  local idx bid rest row hit line
+  _DET_HITS=0 _DET_TOTAL=0 _DET_ROWS=""
+  while read -r row; do
+    [[ -n "$row" ]] || continue
+    idx="$(awk '{print $1}' <<< "$row")"
+    bid="$(awk '{print $2}' <<< "$row")"
+    rest="$(awk '{$1=""; $2=""; sub(/^ +/, ""); print}' <<< "$row")"
+    _DET_TOTAL=$(( _DET_TOTAL + 1 ))
+    line="$(_boot_reset_line "$bid")"
+    if [[ -z "$line" ]]; then
+      hit="no"
+    elif _is_benign "$line"; then
+      hit="reboot"
+    else
+      hit="**FAULT**"; _DET_HITS=$(( _DET_HITS + 1 ))
+    fi
+    _DET_ROWS+="$hit|$idx|$bid|$rest"$'\n'
+  done < <(_boot_rows | tail -n "$WINDOW")
+  return 0
+}
+
+_detect() {
+  _DET_STATUS="" _DET_LINE="" _DET_HEX="" _DET_CAUSE="" _DET_WHY=""
+  local n=0
+
+  if [[ -n "${HOST_GUARD_RESET_KLOG_FILE:-}" ]]; then
+    if [[ ! -r "$HOST_GUARD_RESET_KLOG_FILE" ]]; then
+      _DET_STATUS="UNKNOWN"
+      _DET_WHY="HOST_GUARD_RESET_KLOG_FILE=$HOST_GUARD_RESET_KLOG_FILE is not readable"
+      return 0
+    fi
+    _DET_LINE="$(grep -i -m1 "$RESET_PAT" "$HOST_GUARD_RESET_KLOG_FILE" 2>/dev/null)"
+  elif command -v journalctl >/dev/null 2>&1; then
+    # Liveness probe first: journalctl can exist and still return nothing when
+    # this user cannot read the kernel log. Without the probe, "no permission"
+    # and "no reset line" would both look CLEAN — the exact false negative this
+    # whole script exists to prevent.
+    if [[ -z "$(journalctl -k -b 0 --no-pager -n 1 2>/dev/null)" ]]; then
+      _DET_STATUS="UNKNOWN"
+      _DET_WHY="journalctl returned no kernel log for this boot — this user probably cannot read it; fix with: sudo usermod -aG systemd-journal \$USER (then log out and back in)"
+      return 0
+    fi
+    _DET_LINE="$(journalctl -k -b 0 --no-pager 2>/dev/null | grep -i -m1 "$RESET_PAT")"
+  elif [[ -r /var/log/kern.log ]]; then
+    # kern.log carries history but cannot be scoped to THIS boot, so a hit here
+    # is not evidence that the LAST boot died. Report honestly, never guess.
+    n="$(grep -c -i "$RESET_PAT" /var/log/kern.log 2>/dev/null)"
+    [[ "$n" =~ ^[0-9]+$ ]] || n=0
+    _DET_STATUS="UNKNOWN"
+    _DET_WHY="journalctl is unavailable; /var/log/kern.log carries $n reset-reason line(s) but cannot be scoped to the current boot — install systemd-journal access for an authoritative read"
+    return 0
+  else
+    _DET_STATUS="UNKNOWN"
+    _DET_WHY="no readable kernel log (no journalctl, no /var/log/kern.log) — the platform reset-reason register cannot be read on this host"
+    return 0
+  fi
+
+  if [[ -z "$_DET_LINE" ]]; then
+    _DET_STATUS="CLEAN"
+    _DET_WHY="no reset-reason line in this boot's kernel log — the previous shutdown was orderly (or this platform exposes no reset-reason register)"
+    return 0
+  fi
+  if _is_benign "$_DET_LINE"; then
+    _DET_STATUS="CLEAN"
+    _DET_WHY="previous boot ended in a software-initiated reboot, not a fault (${_DET_LINE#*: })"
+    return 0
+  fi
+
+  _DET_STATUS="RESET"
+  _DET_HEX="$(sed -n 's/.*reset reason \[\([^]]*\)\].*/\1/p' <<< "$_DET_LINE")"
+  _DET_CAUSE="$(sed -n 's/.*reset reason \[[^]]*\]:[[:space:]]*//p' <<< "$_DET_LINE")"
+  [[ -n "$_DET_CAUSE" ]] || _DET_CAUSE="$_DET_LINE"
+  _streak
+  _DET_PREV="$(_prev_boot_id)"
+  return 0
+}
+
+# ── Bundle rendering ────────────────────────────────────────────────────────
+
+_STALE_ROOTS=""   # newline-separated project roots seen in stale records
+_STALE_SESSIONS="" # newline-separated "<root>|<sid>" for stale ENGINE records
+
+_render_records() { # section 3 — and harvest roots/sessions for 4 and 5
+  local dir cur r bid kind root sid
+  dir="$(hg_registry_dir)"
+  cur="$(_hg_boot_id)"
+  _STALE_ROOTS="" _STALE_SESSIONS=""
+  local found=0
+  for r in "$dir"/*.rec; do
+    [[ -e "$r" ]] || continue
+    bid="$(_hg_rec_field "$r" boot_id)"
+    # Records from the CURRENT boot belong to something running right now —
+    # they are not evidence about the boot that died.
+    [[ "$bid" != "$cur" ]] || continue
+    found=$(( found + 1 ))
+    kind="$(_hg_rec_field "$r" kind)"
+    root="$(_hg_rec_field "$r" project_root)"
+    sid="$(_hg_rec_field "$r" session_id)"
+    printf '### %s\n\n' "$(basename "$r")"
+    printf '```\n'
+    cat "$r" 2>/dev/null
+    printf '```\n\n'
+    [[ -z "$root" ]] || _STALE_ROOTS+="$root"$'\n'
+    if [[ "$kind" == "engine" && -n "$root" && -n "$sid" ]]; then
+      _STALE_SESSIONS+="$root|$sid"$'\n'
+    fi
+  done
+  if (( found == 0 )); then
+    printf 'No registry records from a previous boot survive in `%s`.\n' "$dir"
+    printf 'Either nothing was running, or an engine preflight already swept them\n'
+    printf '(the sweep is boot-id keyed — run this script BEFORE resuming a session).\n\n'
+  fi
+  _STALE_ROOTS="$(printf '%s' "$_STALE_ROOTS" | sort -u)"
+  _STALE_SESSIONS="$(printf '%s' "$_STALE_SESSIONS" | sort -u)"
+  return 0
+}
+
+_render_csv_tail() { # $1 csv path, $2 label — the samples that PRECEDE this boot
+  local csv="$1" label="$2" bt rows last mt
+  [[ -f "$csv" ]] || return 0
+  bt="$(hg_boot_epoch)"
+  # Boot-relative, never a plain tail: a sampler that restarted after the reboot
+  # keeps appending, and tailing it would label live idle data "time of death".
+  rows="$(awk -F, -v b="$bt" '$1 ~ /^[0-9]+$/ && $1 + 0 < b' "$csv" 2>/dev/null | tail -n 20)"
+  printf '### %s\n\n' "$label"
+  printf -- '- file: `%s`\n' "$csv"
+  if [[ -z "$rows" ]]; then
+    mt="$(date -d "@$(stat -c %Y "$csv" 2>/dev/null || echo 0)" '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null)"
+    printf -- '- no samples from before this boot survive here (rotated away, or this sampler only started after the reboot). Last written %s.\n\n' "${mt:-unknown}"
+    return 0
+  fi
+  last="$(tail -n 1 <<< "$rows" | cut -d, -f1)"
+  printf -- '- **final sample before the reset: %s** — the closest thing to a time of death\n\n' \
+    "$(date -d "@$last" '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || echo "epoch $last")"
+  printf '```\n%s\n```\n\n' "$rows"
+  return 0
+}
+
+_render() {
+  local now
+  now="$(date '+%Y-%m-%d %H:%M:%S %Z')"
+
+  printf '# Machine reset postmortem — boot %s\n\n' "${_DET_PREV:-unknown}"
+  printf 'Generated %s by `scripts/automation/host-guard/reset-forensics.sh`.\n\n' "$now"
+  printf 'The previous boot did not shut down. The platform reset-reason register says\n'
+  printf 'the HARDWARE asserted reset, so the kernel was never notified and no software\n'
+  printf 'guard — CPU mask, memory ceiling, browser confinement — could have prevented\n'
+  printf 'it. Remediation is firmware/hardware: see `docs/host-guard.md` §\n'
+  printf 'After a hardware reset — root-cause runbook.\n\n'
+
+  printf '## 1. Reset reason (the platform, verbatim)\n\n```\n%s\n```\n\n' "$_DET_LINE"
+  printf -- '- code: `%s`\n' "${_DET_HEX:-unknown}"
+  printf -- '- cause: %s\n' "${_DET_CAUSE:-unknown}"
+  printf -- '- hardware-fault resets among the last %s boots: **%s** (planned reboots excluded)\n\n' "$_DET_TOTAL" "$_DET_HITS"
+
+  printf '## 2. Recent boot history\n\n'
+  if [[ -n "$_DET_ROWS" ]]; then
+    printf '| verdict | idx | boot id | first → last entry |\n|---|---|---|---|\n'
+    local hit idx bid rest
+    while IFS='|' read -r hit idx bid rest; do
+      [[ -n "$idx" ]] || continue
+      printf '| %s | %s | `%s` | %s |\n' "$hit" "$idx" "$bid" "$rest"
+    done <<< "$_DET_ROWS"
+    printf '\n'
+  else
+    printf 'Boot history unavailable (`journalctl --list-boots` returned nothing).\n\n'
+  fi
+
+  printf '## 3. What was running (registry records from the dead boot)\n\n'
+  _render_records
+
+  printf '## 4. Hardware telemetry, final seconds (1 Hz, fsync per line)\n\n'
+  _render_csv_tail "$GLOBAL_HWMON" "machine-global sampler"
+  local root
+  while read -r root; do
+    [[ -n "$root" ]] || continue
+    _render_csv_tail "$root/logs/hwmon/hwmon.csv" "$(basename "$root")"
+    [[ -f "$root/logs/hwmon/hwmon.csv" ]] || _render_csv_tail "$root/logs/hwmon/hwmon.csv.1" "$(basename "$root") (rotated)"
+  done <<< "$_STALE_ROOTS"
+  printf 'Columns: `%s`\n\n' "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10[,cpu_mhz]"
+
+  printf '## 5. Session artifacts at the moment of death\n\n'
+  local sid sdir
+  while IFS='|' read -r root sid; do
+    [[ -n "$root" && -n "$sid" ]] || continue
+    sdir="$root/runs/goal-session-$sid"
+    printf '### %s — session `%s`\n\n' "$(basename "$root")" "$sid"
+    if [[ -f "$sdir/telemetry.jsonl" ]]; then
+      printf 'telemetry.jsonl (last 20):\n\n```\n'
+      tail -n 20 "$sdir/telemetry.jsonl" 2>/dev/null
+      printf '```\n\n'
+    fi
+    if [[ -f "$sdir/engine.log" ]]; then
+      printf 'engine.log (last 40):\n\n```\n'
+      tail -n 40 "$sdir/engine.log" 2>/dev/null
+      printf '```\n\n'
+    fi
+    if [[ -f "$sdir/session.json" ]]; then
+      printf 'session.json:\n\n```json\n'
+      cat "$sdir/session.json" 2>/dev/null
+      printf '```\n\n'
+    fi
+  done <<< "$_STALE_SESSIONS"
+  [[ -n "$_STALE_SESSIONS" ]] || printf 'No engine session could be identified from the surviving records.\n\n'
+
+  printf '## 6. Machine-wide chain event ledger (previous boot)\n\n'
+  if [[ -f "$EVENTS_FILE" ]]; then
+    printf 'Last 40 events not belonging to the current boot — `%s`:\n\n```\n' "$EVENTS_FILE"
+    grep -v "$(_hg_boot_id)" "$EVENTS_FILE" 2>/dev/null | tail -n 40
+    printf '```\n\n'
+  else
+    printf 'No event ledger at `%s` yet (written by hg_event once a guarded engine runs).\n\n' "$EVENTS_FILE"
+  fi
+
+  printf '## 6b. Host mitigations — which experiment was running?\n\n'
+  printf 'Read NOW (the boot after the reset), so PERSISTED settings are accurate and a\n'
+  printf 'runtime-only change has already reverted. For what was truly in force during the\n'
+  printf 'run, use the `host_state` event in §6 — the engine records it at start.\n\n'
+  if declare -f hg_host_mitigations >/dev/null 2>&1; then
+    printf '```json\n%s\n```\n\n' "$(hg_host_mitigations)"
+  fi
+  local hostenv
+  hostenv="${HOST_GUARD_HOST_ENV_FILE:-$HOME/.config/iad/host-guard-host.env}"
+  if [[ -f "$hostenv" ]]; then
+    printf 'Machine budget (`%s`):\n\n```\n' "$hostenv"
+    grep -vE '^\s*#|^\s*$' "$hostenv" 2>/dev/null
+    printf '```\n\n'
+  fi
+
+  printf '## 7. Journal tail of the dead boot\n\n'
+  printf 'NOTE: journald syncs every 5 minutes by default, so the last minutes before a\n'
+  printf 'hard reset are usually MISSING here — trust §4 for the time of death.\n\n```\n'
+  if [[ -n "${HOST_GUARD_RESET_JOURNAL_TAIL_FILE:-}" ]]; then
+    tail -n 80 "$HOST_GUARD_RESET_JOURNAL_TAIL_FILE" 2>/dev/null
+  elif command -v journalctl >/dev/null 2>&1; then
+    journalctl -b -1 -n 80 --no-pager 2>/dev/null
+  fi
+  printf '```\n\n'
+
+  printf '## Next steps\n\n'
+  printf '1. Run the root-cause runbook in `docs/host-guard.md` (journald sync interval,\n'
+  printf '   rasdaemon, pstore, BIOS version, overnight memtest).\n'
+  printf '2. Change ONE hardware variable per soak week so causality stays readable.\n'
+  printf '3. Acceptance: seven consecutive days with `doctor.sh --only reset-reason`\n'
+  printf '   reporting CLEAN on every boot.\n'
+  return 0
+}
+
+_link_latest() {
+  local target="$1"
+  ln -sfn "$(basename "$target")" "$POSTMORTEM_DIR/latest.md" 2>/dev/null || true
+}
+
+# ── Subcommands ─────────────────────────────────────────────────────────────
+
+cmd_check() {
+  _detect
+  case "$_DET_STATUS" in
+    RESET) printf 'RESET|%s|%s|%s/%s|%s\n' "${_DET_HEX:-unknown}" "$_DET_CAUSE" \
+             "$_DET_HITS" "$_DET_TOTAL" "${_DET_PREV:-unknown}" ;;
+    CLEAN) printf 'CLEAN|%s\n' "$_DET_WHY" ;;
+    *)     printf 'UNKNOWN|%s\n' "$_DET_WHY" ;;
+  esac
+  return 0
+}
+
+cmd_ensure_postmortem() {
... [diff_bound] incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh: 49 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index 349cd0a9..f262b76f 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -19,7 +19,13 @@ Self-test (no browser, no network):
 
 Exit codes: 0 ok/soft-skip · 2 bad args/JSON · 3 playwright missing · 4 no DISPLAY (live)
 · 5 verify found ≥1 FAIL · 6 browser infrastructure failure (launch/crash — verify only;
-callers route replay journeys back to the LLM lane so nothing is silently unverified).
+callers route replay journeys back to the LLM lane so nothing is silently unverified)
+· 7 verify: backend unreachable BEFORE any journey ran — every journey is written BLOCKED
+(never FAIL; ops-hardening iter-39, see `probe_backend_health`/run_verify). Distinct from rc 6
+(a browser that launched and then died mid-run): rc 7 means the browser was never even asked to
+navigate anywhere, because the backend the app depends on never answered its own health check.
+Callers route BLOCKED journeys back to the LLM lane exactly like rc 6, so nothing is silently
+unverified — see the generic non-zero-rc fallback in lib/replay-lane.sh.
 """
 from __future__ import annotations
 
@@ -27,6 +33,8 @@ import datetime
 import json
 import os
 import sys
+import urllib.error
+import urllib.request
 from pathlib import Path
 from urllib.parse import urlsplit, urlunsplit
 
@@ -135,18 +143,61 @@ def compute_regression_verdict(results: list[dict]) -> str:
     """Overall verdict for a deterministic regression-replay run (verify mode).
 
     Unlike the showcase verdicts above, replay treats a journey's `expect`s as
-    HARD assertions: FAIL if any journey failed; SKIPPED if none ran or all were
-    skipped (e.g. no golden script on file); otherwise PASS."""
+    HARD assertions: FAIL if any journey failed; BLOCKED if the backend was
+    unreachable before any journey ran (ops-hardening iter-39 — a DISTINCT class
+    from FAIL: a journey verdict of FAIL means "this journey's own assertions did
+    not hold", which is untrue when the backend never answered in the first
+    place; conflating the two is exactly what let a downed backend read as
+    regressions twice in this session, iter-38/t); SKIPPED if none ran or all
+    were skipped (e.g. no golden script on file); otherwise PASS."""
     verdicts = [r.get("verdict") for r in results]
     if not verdicts:
         return "SKIPPED"
     if "FAIL" in verdicts:
         return "FAIL"
+    if "BLOCKED" in verdicts:
+        return "BLOCKED"
     if all(v == "SKIP" for v in verdicts):
         return "SKIPPED"
     return "PASS"
 
 
+def resolve_backend_health_url(base_url: str, explicit: "str | None" = None) -> str:
+    """The backend readiness URL `run_verify` must probe before trusting ANY replay verdict.
+
+    Preference order: an explicit `--backend-health-url` (set by a caller, or a test), then a
+    same-host guess built from `CHAIN_BACKEND_PORT` — the SAME env var every launch/QA script in
+    this framework already uses to compute the backend's assigned port (see lib/common.sh's
+    `ensure_phase_ports`), which is present in this process's environment by the time the
+    pipeline invokes `--mode verify` — combined with this project's canonical readiness path,
+    `GET /api/health` (Trendora goal.md: "computed only in `app.engine.readiness`, served only by
+    `GET /api/health`"). Deliberately NOT the framework's generic `/health` default
+    (lib/common.sh's `bqa_services_probe`): every Trendora route is namespaced under `/api`, so a
+    bare `/health` 404s even on a perfectly healthy backend — reusing that default here would
+    BLOCK every replay run unconditionally, which is worse than the bug this closes."""
+    if explicit:
+        return explicit
+    base = urlsplit(base_url or "http://localhost:3000")
+    port = os.environ.get("CHAIN_BACKEND_PORT", "8000")
+    host = base.hostname or "localhost"
+    return urlunsplit((base.scheme or "http", f"{host}:{port}", "/api/health", "", ""))
+
+
+def probe_backend_health(url: str, timeout: float = 5.0) -> bool:
+    """True iff `url` answers with EXACTLY HTTP 200 within `timeout` seconds.
+
+    Any failure mode — connection refused, timeout, DNS error, a non-200 status — is honestly
+    False. Deliberately STRICT (unlike the framework's permissive `bqa_services_probe`, which
+    treats any 1xx-5xx as "alive" — a reasonable bar for "is uvicorn listening at all", but not
+    for "is this app genuinely ready to serve a UI replay"): a half-up or wrong-port backend must
+    BLOCK the replay lane, not silently pass it through to a false FAIL."""
+    try:
+        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 — localhost only
+            return resp.status == 200
+    except (urllib.error.URLError, OSError, ValueError):
+        return False
+
+
 def _today() -> str:
     return datetime.date.today().isoformat()
 
@@ -188,20 +239,24 @@ def render_regression_results_md(phase_id: str, frontend_url: str, iteration,
     replay — byte-shaped like templates/ui-test-results.md so the goal-evaluator
     reads it exactly like the LLM browser-qa output (top `**Browser QA Verdict:**`
     line, one `UT-<journey>` row per journey, evidence screenshots). `results` is
-    a list of {journey, name, verdict (PASS/FAIL/SKIP), expected, actual, evidence}."""
+    a list of {journey, name, verdict (PASS/FAIL/SKIP/BLOCKED), expected, actual, evidence}."""
     overall = compute_regression_verdict(results)
     total = len(results)
     n_pass = sum(1 for r in results if r.get("verdict") == "PASS")
     n_skip = sum(1 for r in results if r.get("verdict") == "SKIP")
+    n_blocked = sum(1 for r in results if r.get("verdict") == "BLOCKED")
     lines = [f"# Regression Replay — {phase_id}", ""]
     lines.append(f"**Phase:** {phase_id}")
     lines.append(f"**Date:** {_today()}")
     lines.append("**Written by:** demo_runner.py (deterministic replay)")
     if iteration is not None:
         lines.append(f"**Iteration:** {iteration}")
+    overall_line = f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped"
+    overall_line += f", {n_blocked} blocked — backend unreachable" if n_blocked else ""
+    overall_line += ")"
     lines += ["", "---", "",
               f"**Browser QA Verdict:** {overall}", "",
-              f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped)", "",
+              overall_line, "",
               "---", "", "## Results Table", "",
               "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |",
               "|---------|------|------|----------|----------|--------|---------|----------|"]
@@ -228,6 +283,16 @@ def render_regression_results_md(phase_id: str, frontend_url: str, iteration,
             lines += [f"### UT-{r.get('journey', '')} — {r.get('name', '')}", "",
                       "**Verdict:** SKIPPED",
                       f"**Reason:** {r.get('actual', '')}", ""]
+    blocked = [r for r in results if r.get("verdict") == "BLOCKED"]
+    if blocked:
+        lines += ["## Blocked Tests", "",
+                   "_Not a journey failure — the backend was unreachable before this journey (or any "
+                   "other in this run) was ever replayed. Distinct from FAIL: FAIL means the journey's "
+                   "own assertions did not hold; BLOCKED means they were never checked._", ""]
+        for r in blocked:
+            lines += [f"### UT-{r.get('journey', '')} — {r.get('name', '')}", "",
+                      "**Verdict:** BLOCKED",
+                      f"**Reason:** {r.get('actual', '')}", ""]
     lines += ["## Environment", "",
               f"- **Frontend URL:** {frontend_url}",
               f"- **Browser:** Chromium via Playwright (deterministic replay, {mode})",
@@ -402,6 +467,12 @@ def _t_regression_verdict_matrix() -> None:
     assert compute_regression_verdict([{"verdict": "SKIP"}, {"verdict": "SKIP"}]) == "SKIPPED"
     assert compute_regression_verdict([{"verdict": "SKIP"}, {"verdict": "PASS"}]) == "PASS"
     assert compute_regression_verdict([{"verdict": "FAIL"}, {"verdict": "SKIP"}]) == "FAIL"
+    # ops-hardening iter-39 (TC-5/TC-6): BLOCKED is a DISTINCT class from FAIL — an all-BLOCKED
+    # run (backend unreachable) must never present as the same overall verdict as a real
+    # regression, and a genuine FAIL must still win over a BLOCKED row if the two ever mix.
+    assert compute_regression_verdict([{"verdict": "BLOCKED"}, {"verdict": "BLOCKED"}]) == "BLOCKED"
+    assert compute_regression_verdict([{"verdict": "BLOCKED"}, {"verdict": "SKIP"}]) == "BLOCKED"
+    assert compute_regression_verdict([{"verdict": "FAIL"}, {"verdict": "BLOCKED"}]) == "FAIL"
 
 
 def _t_regression_results_md() -> None:
@@ -425,6 +496,106 @@ def _t_regression_results_md() -> None:
     assert "1/3 journeys passed (1 skipped)" in md, md
 
 
+def _t_blocked_results_md() -> None:
+    # ops-hardening iter-39 (TC-5): an all-BLOCKED run renders a BLOCKED headline (never FAIL),
+    # a distinct "## Blocked Tests" section (never conflated with "## Failed Tests"), and the
+    # blocked count in the summary line.
+    results = [
+        {"journey": "J-01", "name": "J-01", "verdict": "BLOCKED",
+         "expected": "backend answers GET http://localhost:1/api/health with HTTP 200 before replay",
+         "actual": "backend unreachable: GET http://localhost:1/api/health did not answer 200",
+         "evidence": "none"},
+        {"journey": "J-03", "name": "J-03", "verdict": "BLOCKED",
+         "expected": "backend answers GET http://localhost:1/api/health with HTTP 200 before replay",
+         "actual": "backend unreachable: GET http://localhost:1/api/health did not answer 200",
+         "evidence": "none"},
+    ]
+    md = render_regression_results_md("goal-x-iter-39", "http://localhost:3017", 39, results, "verify")
+    assert "**Browser QA Verdict:** BLOCKED" in md, md
+    assert "**Browser QA Verdict:** FAIL" not in md, md
+    assert "## Blocked Tests" in md and "## Failed Tests" not in md, md
+    assert "2 blocked — backend unreachable" in md, md
+    for tid in ("UT-J-01", "UT-J-03"):
+        assert tid in md, tid
+
+
+def _t_resolve_backend_health_url() -> None:
+    # explicit override always wins.
+    assert resolve_backend_health_url("http://localhost:3017", "http://x:9/y") == "http://x:9/y"
+    # no override, no CHAIN_BACKEND_PORT env -> falls back to the default port (8000) + this
+    # project's real health path (/api/health, NOT the framework's generic /health -- every
+    # Trendora route is namespaced under /api).
+    saved = os.environ.pop("CHAIN_BACKEND_PORT", None)
+    try:
+        url = resolve_backend_health_url("http://localhost:3017", None)
+        assert url == "http://localhost:8000/api/health", url
+        os.environ["CHAIN_BACKEND_PORT"] = "9142"
+        url2 = resolve_backend_health_url("http://localhost:3017", None)
+        assert url2 == "http://localhost:9142/api/health", url2
+    finally:
+        if saved is None:
+            os.environ.pop("CHAIN_BACKEND_PORT", None)
+        else:
+            os.environ["CHAIN_BACKEND_PORT"] = saved
+
+
+def _t_probe_backend_health() -> None:
+    # No server at all on this port (connection refused) -> honestly False, never an exception.
+    assert probe_backend_health("http://127.0.0.1:1/api/health", timeout=1.0) is False
+
+    # A real local HTTP server that answers exactly 200 -> True; a 404 (server up, wrong path,
+    # exactly the pre-fix framework-default-path bug this closes) -> False.
+    import http.server
+    import threading
+
+    class _Handler(http.server.BaseHTTPRequestHandler):
+        def do_GET(self):  # noqa: N802 - stdlib method name
+            if self.path == "/api/health":
+                self.send_response(200)
+                self.end_headers()
+                self.wfile.write(b"{}")
+            else:
+                self.send_response(404)
+                self.end_headers()
+
+        def log_message(self, *_a):  # noqa: D401 - silence per-request stderr noise
+            pass
+
+    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
+    port = server.server_address[1]
+    thread = threading.Thread(target=server.serve_forever, daemon=True)
+    thread.start()
+    try:
+        assert probe_backend_health(f"http://127.0.0.1:{port}/api/health", timeout=2.0) is True
+        assert probe_backend_health(f"http://127.0.0.1:{port}/health", timeout=2.0) is False
+    finally:
+        server.shutdown()
+        thread.join(timeout=2.0)
+
+
+def _t_run_verify_blocked_when_backend_unreachable() -> None:
+    # TC-5 end-to-end (no real browser launch reached — the probe short-circuits BEFORE
+    # Playwright ever opens a page): backend unreachable -> rc 7, every journey BLOCKED, never
+    # FAIL, and the written results file says so.
+    import argparse
+    import tempfile
+
+    with tempfile.TemporaryDirectory() as tmp:
+        results_path = os.path.join(tmp, "results.md")
+        opts = argparse.Namespace(
+            scripts_dir=tmp, journeys="J-01,J-03", phase_id="goal-x-iter-39", iteration=39,
+            evidence_dir=None, results=results_path, repo_root=tmp, timeout_ms=8000,
+            backend_health_url="http://127.0.0.1:1/api/health",  # nothing listens on port 1
+        )
+        rc = run_verify(opts, "http://localhost:3017")
+        assert rc == 7, rc
+        text = Path(results_path).read_text(encoding="utf-8")
+        assert "**Browser QA Verdict:** BLOCKED" in text, text
+        assert "**Browser QA Verdict:** FAIL" not in text, text
+        assert "UT-J-01" in text and "UT-J-03" in text, text
+        assert "| BLOCKED |" in text and "| FAIL |" not in text, text
+
+
 def _t_launch_chromium_retries() -> None:
     # A flaky launch succeeds on the retry; a dead one raises after N attempts
     # (no browser involved — fake pw objects).
@@ -550,6 +721,10 @@ _SELF_TEST_CHECKS = [
     _t_script_md_roundtrip,
     _t_regression_verdict_matrix,
     _t_regression_results_md,
+    _t_blocked_results_md,
+    _t_resolve_backend_health_url,
+    _t_probe_backend_health,
+    _t_run_verify_blocked_when_backend_unreachable,
     _t_launch_chromium_retries,
     _t_derive_happy,
     _t_derive_rejects_untagged_journey,
@@ -1121,7 +1296,11 @@ def run_verify(opts, base_url: str) -> int:
     Returns 0 when nothing failed, 5 when ≥1 journey FAILED (so the caller can
     re-confirm just those journeys with the LLM agent — guards against a brittle
     selector causing a false regression). A journey with no/invalid golden script
-    is SKIP (the caller routes those to the LLM lane)."""
+    is SKIP (the caller routes those to the LLM lane). Returns 7 when the backend
+    was unreachable BEFORE any journey ran — every journey is written BLOCKED,
+    never FAIL (ops-hardening iter-39: closes a real bug where a downed backend
+    produced false FAIL rows against every journey, twice in this session,
+    iter-38/t — see `probe_backend_health`/`resolve_backend_health_url`)."""
     from playwright.sync_api import sync_playwright
 
     scripts_dir = Path(opts.scripts_dir or ".")
@@ -1144,6 +1323,24 @@ def run_verify(opts, base_url: str) -> int:
         print("[demo_runner] verify: no journeys to replay (SKIPPED).")
         return 0
 
+    # ops-hardening iter-39: probe the backend's OWN health endpoint ONCE, before opening a
+    # browser or replaying a single journey. A journey verdict of FAIL means "this journey's own
+    # assertions did not hold" — untrue, and misleading, when the backend never answered at all.
+    # Every journey is written BLOCKED instead (a distinct verdict class the caller never confuses
+    # with a real regression signal — see compute_regression_verdict / the rc=7 contract above).
+    health_url = resolve_backend_health_url(base_url, getattr(opts, "backend_health_url", None))
+    if not probe_backend_health(health_url):
+        results = [{
+            "journey": jid, "name": jid, "verdict": "BLOCKED",
+            "expected": f"backend answers GET {health_url} with HTTP 200 before replay",
+            "actual": f"backend unreachable: GET {health_url} did not answer 200",
+            "evidence": "none",
+        } for jid in journeys]
+        _write(results)
+        print(f"[demo_runner] verify: backend unreachable ({health_url}) — "
+              f"{len(results)} journey(s) BLOCKED, not FAILed (rc 7).", file=sys.stderr)
+        return 7
+
     results: list[dict] = []
     try:
         with sync_playwright() as pw:
@@ -1256,6 +1453,9 @@ def main(argv: list[str]) -> int:
                    help="verify mode: comma-separated journey IDs to replay")
     p.add_argument("--evidence-dir", default=None,
                    help="verify mode: per-journey screenshot evidence dir")
+    p.add_argument("--backend-health-url", default=None,
+                   help="verify mode: explicit backend readiness URL to probe before replaying "
+                        "(default: guessed from CHAIN_BACKEND_PORT + this project's /api/health)")
     opts = p.parse_args(argv)
     live = opts.mode in ("live", "session-live")
     verify = opts.mode == "verify"
diff --git a/incredible_auto_dev/scripts/automation/lib/engine-lock.sh b/incredible_auto_dev/scripts/automation/lib/engine-lock.sh
index 76ad52eb..fdb374ea 100644
--- a/incredible_auto_dev/scripts/automation/lib/engine-lock.sh
+++ b/incredible_auto_dev/scripts/automation/lib/engine-lock.sh
@@ -101,6 +101,19 @@ engine_lock_classify() {
     return 0
   fi
 
+  # Recorded in a previous boot ⇒ the holder cannot possibly be alive, whatever
+  # /proc says now. Checked AFTER the cross-host branch (boot ids are only
+  # comparable on the same host) and BEFORE the pid probe, because a machine
+  # reset is exactly the case where the pid probe can be fooled. Locks written
+  # before this field existed carry no boot_id and fall through unchanged.
+  local lock_boot cur_boot
+  lock_boot="$(_engine_lock_meta "$dir" boot_id)"
+  cur_boot="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)"
+  if [[ -n "$lock_boot" && -n "$cur_boot" && "$lock_boot" != "$cur_boot" ]]; then
+    echo "STALE|$pid|${host:-$myhost}|${age:-?}|recorded in a previous boot (machine reset or reboot) — the holder cannot be alive"
+    return 0
+  fi
+
   if kill -0 "$pid" 2>/dev/null; then
     # Same-host pid is alive — but pids get recycled across crashes/reboots.
     # If /proc says the live process is something else entirely, the holder
@@ -131,6 +144,10 @@ acquire_engine_lock() {
         _engine_lock_host      > "$dir/host"
         date +%s               > "$dir/epoch"
         basename -- "$0" 2>/dev/null > "$dir/cmd"
+        # Boot id: pids are recycled across a reboot, so after a machine reset a
+        # leftover lock can name a pid that is alive and even runs a matching
+        # command. The boot id is the only field that cannot survive the reset.
+        cat /proc/sys/kernel/random/boot_id 2>/dev/null > "$dir/boot_id"
       } 2>/dev/null || true
       _ENGINE_LOCK_HELD="$dir"
       return 0
diff --git a/incredible_auto_dev/scripts/automation/lib/goal_gate.py b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
index 292dca08..1c1b1b46 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
@@ -77,6 +77,16 @@ _FAIL_CELL_RE = re.compile(r"\|\s*FAIL\s*\|")
 # this iteration — it keeps its prior status for scoring, but it must block
 # GOAL_ACHIEVED exactly like a FAIL until a later iteration re-verifies it.
 _DEFERRED_CELL_RE = re.compile(r"\|\s*DEFERRED-BUDGET\s*\|")
+# ops-hardening iter-39 audit (B2): demo_runner.py's new rc-7 path writes a BLOCKED row per
+# journey when the backend did not answer its health probe — correctly NOT a FAIL (the journey's
+# own assertions were never checked). But replay_lane_merge_results ALWAYS merges the raw replay
+# artifact into the authoritative merged results, and merge_ui_test_results.parse_rows does not
+# recognize BLOCKED, so those rows carry an empty verdict: they are excluded from the merged
+# headline, invisible to _FAIL_CELL_RE, and a run where the backend was down for every regression
+# journey could present as "**Browser QA Verdict:** PASS" with rc 0 here (reproduced during the
+# audit). BLOCKED means NOT VERIFIED — exactly the DEFERRED-BUDGET case above — so it must block
+# GOAL_ACHIEVED identically until a later iteration actually replays the journey.
+_BLOCKED_CELL_RE = re.compile(r"\|\s*BLOCKED\s*\|")
 
 
 def _load_history(path: str) -> dict | None:
@@ -137,7 +147,8 @@ def cmd_results(path: str) -> int:
         text = Path(path).read_text(encoding="utf-8")
     except OSError:
         return 2
-    return 1 if (_FAIL_CELL_RE.search(text) or _DEFERRED_CELL_RE.search(text)) else 0
+    return 1 if (_FAIL_CELL_RE.search(text) or _DEFERRED_CELL_RE.search(text)
+                 or _BLOCKED_CELL_RE.search(text)) else 0
 
 
 def cmd_regressions(pre_path: str, post_path: str) -> int:
@@ -453,6 +464,22 @@ def _self_test() -> int:
             "| UT-J-06 | J-06 regression re-check | regression | P2 | e | not run | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |\n",
             encoding="utf-8")
         assert cmd_results(str(res_def)) == 1, "DEFERRED-BUDGET must block GOAL_ACHIEVED"
+        # ops-hardening iter-39 audit (B2): a BLOCKED row (demo_runner rc 7 — the backend never
+        # answered its health probe, so the journey was never replayed) must block achievement
+        # exactly like DEFERRED-BUDGET. It reaches the MERGED results file because
+        # replay_lane_merge_results always merges the raw replay artifact, and it carries no
+        # PASS/FAIL/SKIP verdict for parse_rows — so without this the merged headline can read
+        # PASS while every regression journey went unverified.
+        res_blocked = d / "r5.md"; res_blocked.write_text(
+            "| UT-J-07 | target journey | functional | P1 | e | ok | PASS | x.png |\n"
+            "| UT-J-01 | J-01 | regression | P1 | backend answers GET /api/health with HTTP 200 "
+            "before replay | backend unreachable: did not answer 200 | BLOCKED | none |\n",
+            encoding="utf-8")
+        assert cmd_results(str(res_blocked)) == 1, "BLOCKED (unverified journey) must block GOAL_ACHIEVED"
+        res_blocked_prose = d / "r6.md"; res_blocked_prose.write_text(
+            "| T1 | the run was never BLOCKED at any point | ui | P1 | e | a | PASS | x.png |\n",
+            encoding="utf-8")
+        assert cmd_results(str(res_blocked_prose)) == 0, "BLOCKED must match a whole cell only"
 
         # regressions: J-01 passing→failing is caught; missing pre → 0
         post = d / "post.json"
diff --git a/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh b/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
index ba083006..add0adfe 100644
--- a/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
@@ -114,6 +114,38 @@ _hg_proc_starttime() {
   sed 's/.*) //' "/proc/$pid/stat" 2>/dev/null | awk '{print $20}'
 }
 
+# hg_pid_matches <pid> <starttime> — rc 0 iff that pid is alive AND is still the
+# SAME process. After a machine reset the box comes back with the same pid space,
+# so a pidfile left by the dead boot can point at an innocent live process.
+# `kill -0` alone cannot tell them apart; the start time can.
+hg_pid_matches() {
+  local pid="${1:-}" stt="${2:-}"
+  [[ "$pid" =~ ^[0-9]+$ && -n "$stt" ]] || return 1
+  kill -0 "$pid" 2>/dev/null || return 1
+  [[ "$(_hg_proc_starttime "$pid")" == "$stt" ]]
+}
+
+# hg_boot_epoch — unix time this boot started (/proc/stat btime).
+# HOST_GUARD_BTIME_OVERRIDE is the test seam: no test can reboot a machine.
+hg_boot_epoch() {
+  if [[ -n "${HOST_GUARD_BTIME_OVERRIDE:-}" ]]; then
+    echo "$HOST_GUARD_BTIME_OVERRIDE"; return 0
+  fi
+  awk '/^btime /{print $2; exit}' /proc/stat 2>/dev/null || echo 0
+}
+
+# hg_file_predates_boot <path> — rc 0 iff the file was last written BEFORE this
+# boot began, i.e. it is a leftover from a machine that went down without
+# cleaning up. rc 1 when the file is missing, unreadable, or current.
+hg_file_predates_boot() {
+  local f="${1:-}" mt bt
+  [[ -f "$f" ]] || return 1
+  mt="$(stat -c %Y "$f" 2>/dev/null)" || return 1
+  bt="$(hg_boot_epoch)"
+  [[ "$mt" =~ ^[0-9]+$ && "$bt" =~ ^[0-9]+$ ]] || return 1
+  (( mt < bt ))
+}
+
 # ── Registry ──────────────────────────────────────────────────────────────────
 
 hg_registry_dir() {
@@ -202,6 +234,112 @@ hg_release() { # drop THIS process's engine record (best effort)
   return 0
 }
 
+# ── Durable machine-wide event ledger ─────────────────────────────────────────
+# WHY: after the 2026-07-30 hardware reset nothing on disk could answer the one
+# question forensics needs — "what was the machine doing, across BOTH repos, in
+# the final seconds?". The aggregate verdict is silent when it passes,
+# telemetry.jsonl is per-session and never fsync'd, and engine.log only exists in
+# interactive mode. This ledger is one fsync'd line per chain event for the whole
+# machine, so the postmortem can reconstruct a cross-repo timeline.
+#
+# DURABILITY: `sync <file>` after each append — the same idiom that made the
+# hwmon sampler the only artifact to survive the power-cut with its last second
+# intact. Event rate is a few per minute, so the cost is irrelevant.
+#
+# CONCURRENCY: single-line O_APPEND writes from concurrent engines do not
+# interleave on a local filesystem (lines stay far below the atomic-write bound;
+# oversized payloads are dropped rather than truncated, so a reader never meets
+# half a JSON object). Same local-fs assumption the registry already makes.
+
+hg_events_file() {
+  echo "${HOST_GUARD_EVENTS_FILE:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/events.jsonl}"
+}
+
+# hg_host_mitigations — the host knobs a reset investigation actually turns on,
+# as a JSON fragment. Emitted into the ledger at engine start so a postmortem can
+# say WHICH mitigation was in force during the run. Without this the "one change
+# per soak week" discipline is unfalsifiable after the fact: the postmortem is
+# written on the NEXT boot, by which time a runtime-only change (a C-state
+# disable, a boost toggle) has already reverted and reads as though it was never
+# applied. Cheap: five small sysfs reads, once per engine.
+hg_host_mitigations() {
+  local boost cstates drv gov cmdline s name
+  boost="$(tr -dc '0-9' < "${HOST_GUARD_SYS_BOOST_PATH:-/sys/devices/system/cpu/cpufreq/boost}" 2>/dev/null)"
+  for s in /sys/devices/system/cpu/cpu0/cpuidle/state[0-9]*; do
+    [[ -r "$s/name" && -r "$s/disable" ]] || continue
+    IFS= read -r name < "$s/name" 2>/dev/null || continue
+    cstates+="${cstates:+,}$name:$(tr -dc '0-9' < "$s/disable" 2>/dev/null)"
+  done
+  IFS= read -r drv < /sys/devices/system/cpu/cpuidle/current_driver 2>/dev/null || drv=""
+  IFS= read -r gov < /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || gov=""
+  IFS= read -r cmdline < /proc/cmdline 2>/dev/null || cmdline=""
+  # Read the cap from the FILE, not the environment: the engine emits this at
+  # start, before preflight sources the machine budget, so the env var is still
+  # unset and would misreport a capped host as uncapped. Read-only sed, never a
+  # source — same rule the doctor follows for env it does not own.
+  local cap="${HOST_GUARD_MAX_ENGINES:-}"
+  if [[ -z "$cap" ]]; then
+    cap="$(sed -n 's/^[[:space:]]*HOST_GUARD_MAX_ENGINES[[:space:]]*=[[:space:]]*//p' \
+           "$(hg_host_env_file)" 2>/dev/null | tail -n 1)"
+    cap="${cap//\"/}"; cap="${cap//\'/}"
+  fi
+  printf '{"boost":"%s","cstate_disabled":"%s","idle_driver":"%s","governor":"%s","max_engines":"%s","cmdline":"%s"}' \
+    "${boost:-?}" "${cstates:-?}" "$(_hg_json_esc "$drv")" "$(_hg_json_esc "$gov")" \
+    "${cap:-unset}" "$(_hg_json_esc "${cmdline:0:200}")"
+}
+
+_hg_json_esc() { # minimal JSON string escaping for the fields we control
+  local s="${1:-}"
+  s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; s="${s//$'\n'/ }"; s="${s//$'\t'/ }"
+  printf '%s' "$s"
+}
+
+# hg_event <type> [json-object] — best effort, ALWAYS returns 0.
+# The optional second argument is a JSON OBJECT whose body is spliced into the
+# event (e.g. '{"iter":3}'). Never let a ledger problem touch the engine.
+hg_event() {
+  local type="${1:-}" payload="${2:-}"
+  [[ -n "$type" ]] || return 0
+  # NO-OP RULE (roadmap §20): no machine budget file and no project host-guard
+  # ⇒ this function writes nothing at all, on any host.
+  [[ -f "$(hg_host_env_file)" || "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+
+  local f dir extra="" iso size max
+  f="$(hg_events_file)"; dir="$(dirname "$f")"
+  mkdir -p "$dir" 2>/dev/null || return 0
+
+  if [[ "$payload" == \{*\} ]]; then
+    extra="${payload#\{}"; extra="${extra%\}}"
+    extra="${extra//$'\n'/ }"
+    if (( ${#extra} > 900 )); then
+      extra=',"payload_dropped":true'      # never emit half an object
+    elif [[ -n "$extra" ]]; then
+      extra=",$extra"
+    fi
+  fi
+
+  printf -v iso '%(%Y-%m-%dT%H:%M:%S)T' -1
+  printf '{"ts":%s,"iso":"%s","boot":"%s","host":"%s","pid":%s,"event":"%s","project":"%s","sid":"%s","agent":"%s"%s}\n' \
+    "$EPOCHSECONDS" "$iso" "$(_hg_boot_id)" \
+    "$(_hg_json_esc "${HOSTNAME:-unknown}")" "$$" "$(_hg_json_esc "$type")" \
+    "$(_hg_json_esc "${REPO_ROOT:-$PWD}")" "$(_hg_json_esc "${GOAL_SESSION_ID:-${SESSION_ID:-}}")" \
+    "$(_hg_json_esc "${CHAIN_CURRENT_AGENT:-}")" "$extra" >> "$f" 2>/dev/null || return 0
+  # fsync so the final pre-reset lines survive an instant power-cut reset
+  sync "$f" 2>/dev/null || sync 2>/dev/null || true
+
+  max="${HOST_GUARD_EVENTS_MAX_BYTES:-5242880}"
+  size="$(stat -c %s "$f" 2>/dev/null || echo 0)"
+  if [[ "$size" =~ ^[0-9]+$ && "$max" =~ ^[0-9]+$ ]] && (( size > max )); then
+    if command -v flock >/dev/null 2>&1; then
+      # A racing rotator doing the same mv is harmless; skip rather than wait.
+      ( flock -n 9 && mv -f "$f" "$f.1" ) 9>"$dir/.events.lock" 2>/dev/null || true
+    else
+      mv -f "$f" "$f.1" 2>/dev/null || true
+    fi
+  fi
+  return 0
+}
+
 # hg_self_is_junior_to <own_rec> <other_rec> — rc 0 when SELF loses.
 # Total order over (epoch, starttime, pid): both sides compute the same answer
 # from the same files, so a conflict never ends in both-pause or neither-pause.
@@ -240,6 +378,33 @@ hg_boost_ok() {
   return 0
 }
 
+# ── Arbitration ───────────────────────────────────────────────────────────────
+# _hg_arbitrate <own_rec> <detail> <live_rec>... → "PAUSE|<msg>" | "WARN|<msg>"
+# Someone has to yield. Compare against every OTHER live engine record: if we are
+# junior to all of them we pause; otherwise we warn and keep running while the
+# junior session pauses itself on its own next check. Extracted so every breach
+# class (mask, memory, engine count) yields by the same deterministic rule.
+_hg_arbitrate() {
+  local own_rec="${1:-}" detail="${2:-}"; shift 2 2>/dev/null || true
+  local other kind junior=0 senior_desc=""
+  for other in "$@"; do
+    [[ "$other" == "$own_rec" ]] && continue
+    kind="$(_hg_rec_field "$other" kind)"
+    [[ "$kind" == "engine" ]] || continue
+    if hg_self_is_junior_to "$own_rec" "$other"; then
+      junior=1
+      senior_desc="session '$(_hg_rec_field "$other" session_id)' in $(_hg_rec_field "$other" project_root) (pid $(_hg_rec_field "$other" pid))"
+      break
+    fi
+  done
+  if (( junior )); then
+    echo "PAUSE|$detail. The older session holds the budget: $senior_desc. Stop or narrow that session, or widen the budget in $(hg_host_env_file), then resume."
+  else
+    echo "WARN|$detail. This session started first, so it keeps running; the newer session is expected to pause itself."
+  fi
+  return 0
+}
+
 # ── Aggregate verdict ─────────────────────────────────────────────────────────
 # hg_aggregate_verdict <own_rec> → "OK" | "WARN|<msg>" | "PAUSE|<msg>"
 #
@@ -273,6 +438,26 @@ hg_aggregate_verdict() {
     fi
   done
 
+  # (0) Concurrent-engine cap, checked BEFORE the budget early-return so it works
+  # on a machine that configures only the cap. This is the honest mitigation for
+  # a host whose resets are HARDWARE (2026-07-30: an uncorrected data fabric sync
+  # flood with every mask/memory check green — see docs/host-guard.md § After a
+  # hardware reset): fewer simultaneous engines shrinks the exposure window, a
+  # narrower mask does not. Absent or invalid ⇒ unlimited ⇒ today's behaviour.
+  local cap="${HOST_GUARD_MAX_ENGINES:-}"
+  if [[ "$cap" =~ ^[0-9]+$ ]] && (( cap >= 1 )); then
+    local n_eng=0 er
+    for er in "${live[@]}"; do
+      [[ "$(_hg_rec_field "$er" kind)" == "engine" ]] && n_eng=$(( n_eng + 1 ))
+    done
+    if (( n_eng > cap )); then
+      _hg_arbitrate "$own_rec" \
+        "$n_eng goal-mode engines are live but this machine allows HOST_GUARD_MAX_ENGINES=$cap ($(hg_host_env_file)) — it is recovering from hardware-asserted resets, so concurrent engines are capped until the hardware soaks clean" \
+        "${live[@]}"
+      return 0
+    fi
+  fi
+
   # No machine budget configured: enforcement is off, but say so loudly once
   # two different projects are guarded at the same time — that is exactly the
   # configuration that reset this host.
@@ -318,25 +503,6 @@ hg_aggregate_verdict() {
 
   [[ -n "$detail" ]] || { echo "OK"; return 0; }
 
-  # Someone has to yield. Compare against every OTHER live engine record: if we
-  # are junior to all of them we pause; otherwise we warn and keep going while
-  # the junior session pauses itself on its own next check.
-  local other kind junior=0 senior_desc=""
-  for other in "${live[@]}"; do
-    [[ "$other" == "$own_rec" ]] && continue
-    kind="$(_hg_rec_field "$other" kind)"
-    [[ "$kind" == "engine" ]] || continue
-    if hg_self_is_junior_to "$own_rec" "$other"; then
-      junior=1
-      senior_desc="session '$(_hg_rec_field "$other" session_id)' in $(_hg_rec_field "$other" project_root) (pid $(_hg_rec_field "$other" pid))"
-      break
-    fi
-  done
-
-  if (( junior )); then
-    echo "PAUSE|$detail. The older session holds the budget: $senior_desc. Stop or narrow that session, or widen the budget in $(hg_host_env_file), then resume."
-  else
-    echo "WARN|$detail. This session started first, so it keeps running; the newer session is expected to pause itself."
-  fi
+  _hg_arbitrate "$own_rec" "$detail" "${live[@]}"
   return 0
 }
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index 4f61c184..8f925cdb 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -99,6 +99,23 @@ def file_top_verdict(text: str) -> str:
     return m.group(1) if m else ""
 
 
+def verdict_for(text: str, test_id: str) -> str:
+    """The single row's normalized verdict for `test_id` in `text` (`""` if not found) — the
+    SAME PASS/FAIL/SKIP normalization `parse_rows` already uses, so it tolerates bold cells
+    (`**FAIL**`) and ANNOTATED cells ("PASS (steps 1,2,4 verified live; step 3 not executed, see
+    UT-J-04)", "SKIPPED (partial — see Actual)").
+
+    ops-hardening iter-39 (TC-7): exists so a bash caller (replay-lane.sh's reconciliation
+    footer) never has to re-implement that matching as a raw `grep -F '| PASS |'` — which is
+    exactly what silently missed BOTH J-05 (FAIL -> PASS-with-caveat) and J-04 (FAIL -> SKIPPED-
+    with-caveat) in iter-38: neither annotated cell contains the bare substring `| PASS |` or
+    `| SKIP |` an exact-string grep requires, so the footer under-reported by omitting both."""
+    for row in parse_rows(text):
+        if row["test_id"] == test_id:
+            return row["verdict"]
+    return ""
+
+
 def compute_overall(rows: "list[dict]", file_verdicts: "list[str] | None" = None) -> str:
     """Overall verdict. Surviving rows are authoritative; only when NO rows could
     be parsed do we fall back to the input files' headline verdicts."""
@@ -243,6 +260,20 @@ def cmd_void(path: str, journeys: "list[str]") -> int:
     return 0
 
 
+def cmd_verdict_of(path: str, test_id: str) -> int:
+    """Print `test_id`'s normalized verdict word in `path` (empty line if the file is unreadable
+    or the row is not found) — a stable, tested CLI surface for a bash caller that needs the
+    SAME annotation-tolerant parsing `parse_rows` already uses (see `verdict_for`'s docstring)."""
+    p = Path(path)
+    try:
+        text = p.read_text(encoding="utf-8")
+    except OSError:
+        print("")
+        return 0
+    print(verdict_for(text, test_id))
+    return 0
+
+
 def main(argv: "list[str]") -> int:
     if argv and argv[0] in ("self-test", "--self-test"):
         return _self_test()
@@ -251,6 +282,11 @@ def main(argv: "list[str]") -> int:
             sys.stderr.write("usage: merge_ui_test_results.py void <results.md> <J-XX> [...]\n")
             return 2
         return cmd_void(argv[1], argv[2:])
+    if argv and argv[0] == "verdict-of":
+        if len(argv) < 3:
+            sys.stderr.write("usage: merge_ui_test_results.py verdict-of <results.md> <test-id>\n")
+            return 2
+        return cmd_verdict_of(argv[1], argv[2])
     if len(argv) < 2:
         sys.stderr.write("usage: merge_ui_test_results.py <out.md> <in1.md> [<in2.md> ...]\n")
         return 2
@@ -342,6 +378,25 @@ def _self_test() -> int:
         md = merge([bold])
         assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
 
+    def t_verdict_for_tolerates_annotated_cells():
+        # ops-hardening iter-39 (TC-7): verdict_for must resolve the SAME normalized verdict for
+        # an annotated cell that parse_rows already tolerates — reproduces the exact iter-38 rows
+        # that a naive `grep -F '| PASS |'` missed (J-05: FAIL -> PASS-with-caveat; a FAIL ->
+        # SKIPPED-with-caveat case mirroring J-04).
+        annotated = (
+            "**Browser QA Verdict:** PASS\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-05 | Aggregates precomputed | regression | P1 | e | steps 1,2,4 verified | "
+            "PASS (steps 1,2,4 verified live; step 3 not executed, see UT-J-04) | a.png |\n"
+            "| UT-J-04 | Non-blocking boot | regression | P1 | e | not executed live | "
+            "SKIPPED (partial — see Actual) | b.png |\n"
+            "| UT-J-02 | Still broken | regression | P1 | e | step 2 failed | FAIL | c.png |\n")
+        assert verdict_for(annotated, "UT-J-05") == "PASS", verdict_for(annotated, "UT-J-05")
+        assert verdict_for(annotated, "UT-J-04") == "SKIP", verdict_for(annotated, "UT-J-04")
+        assert verdict_for(annotated, "UT-J-02") == "FAIL", verdict_for(annotated, "UT-J-02")
+        assert verdict_for(annotated, "UT-J-99") == "", verdict_for(annotated, "UT-J-99")
+
     def t_annotated_verdicts():
         # "PASS (with caveat)" / "FAIL (see note)" must parse as their verdict; prose
         # in the Actual column that merely STARTS with a verdict word must lose to the
@@ -435,6 +490,7 @@ def _self_test() -> int:
               ("skipped_only", t_skipped_only),
               ("bold_verdicts", t_bold_verdicts),
               ("annotated_verdicts", t_annotated_verdicts),
+              ("verdict_for_tolerates_annotated_cells", t_verdict_for_tolerates_annotated_cells),
               ("tc_prefixed_fail_survives", t_tc_prefixed_fail_survives),
               ("void_rewrites_and_recomputes", t_void_rewrites_and_recomputes),
               ("void_keeps_unlisted_fail", t_void_keeps_unlisted_fail),
diff --git a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
index 72ef8471..1b787885 100644
--- a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
@@ -269,6 +269,17 @@ _agent_timeout_for() {
 _INTERACTIVE_DISPATCH_LIB="$(dirname "${BASH_SOURCE[0]}")/interactive-dispatch.sh"
 [[ -f "$_INTERACTIVE_DISPATCH_LIB" ]] && source "$_INTERACTIVE_DISPATCH_LIB"
 
+# Machine-wide durable event ledger (host-guard). Sourced here because
+# agent_with_quota_retry below is the SINGLE dispatch chokepoint for all three
+# backends — the engine AND every run-phase child — so bracketing it is what
+# lets a postmortem say which agent each repo was running at the moment the
+# machine died. Pure library, re-source guarded; a no-op stub keeps vendored
+# copies that lack the lib working unchanged.
+_HOST_GUARD_REGISTRY_LIB="$(dirname "${BASH_SOURCE[0]}")/host-guard-registry.sh"
+# shellcheck source=host-guard-registry.sh
+[[ -f "$_HOST_GUARD_REGISTRY_LIB" ]] && source "$_HOST_GUARD_REGISTRY_LIB"
+declare -f hg_event >/dev/null 2>&1 || hg_event() { :; }
+
 # Append a trace record to $CHAIN_TRACE_DIR/trace.jsonl and copy stdout into
 # $CHAIN_TRACE_DIR/<NNNN>-<agent>.log. No-op if CHAIN_TRACE_DIR is unset, the
 # directory does not exist, or is not writable. Always best-effort: failures
@@ -1228,6 +1239,8 @@ agent_with_quota_retry() {
   # CHAIN_AGENT_BACKEND overrides the CLI for dispatch only (assets/personas
   # still come from CHAIN_CLI). Defaults to the CLI, so absence = today's behaviour.
   local backend="${CHAIN_AGENT_BACKEND:-$cli}"
+  local _hg_t0=$EPOCHSECONDS _hg_rc=0
+  hg_event dispatch_start "$(printf '{"backend":"%s"}' "$backend")"
   case "$backend" in
     interactive) _interactive_invoke "$@" ;;
     claude)      _claude_invoke "$@" ;;
@@ -1237,6 +1250,10 @@ agent_with_quota_retry() {
       return 2
       ;;
   esac
+  _hg_rc=$?
+  hg_event dispatch_end \
+    "$(printf '{"backend":"%s","rc":%s,"dur_s":%s}' "$backend" "$_hg_rc" "$(( EPOCHSECONDS - _hg_t0 ))")"
+  return $_hg_rc
 }
 
 # Back-compat alias. Existing scripts call this name; behaviour now depends on
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index 00ceb3f6..4c86a2d8 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -335,8 +335,19 @@ replay_lane_partition_and_verify() {
       _replay_lane_mark_skipped_infra "$_rl_iter"
       _use_replay="no"
       R_REPLAY=""
+    elif [[ "$_replay_rc" -eq 7 ]]; then
+      # ops-hardening iter-39: demo_runner.py's OWN health probe found the backend unreachable
+      # BEFORE any journey ran (see demo_runner.py's run_verify docstring / TC-5) — every journey
+      # in $REGRESSION_RESULTS was written BLOCKED, never FAIL. Same safe fallback as any other
+      # lane failure below (route every replay journey to a genuine LLM-lane verification instead
+      # of trusting an unrun replay), logged distinctly so this reads as "the backend was down",
+      # not "the browser crashed" (rc=6) or "a selector broke" (rc=5) — exactly the ambiguity
+      # that produced iter-38/t's false-regression reports twice this session.
+      _replay_lane_warn "Replay lane: backend unreachable before any journey ran (rc=7, BLOCKED — see $REGRESSION_RESULTS) — falling back to the LLM lane for ALL regression journeys."
+      _use_replay="no"
+      R_REPLAY=""
     elif [[ "$_replay_rc" -ne 0 ]]; then
-      # Replay-lane infrastructure failure (non-6 rc = runner crash, missing
+      # Replay-lane infrastructure failure (non-6/7 rc = runner crash, missing
       # playwright, bad invocation). The replay journeys were NOT verified —
       # route ALL of them back to the LLM lane, byte-identical to running this
       # iteration with CHAIN_REGRESSION_REPLAY=false. Previously a replay crash
@@ -450,19 +461,44 @@ replay_lane_merge_results() {
 }
 
 # Reconcile the RAW replay artifact after a merge: any journey the replay lane
-# FAILed but the merged file records as PASS was overturned by the LLM lane's
-# re-confirmation (golden-script false positive — brittle selector, cleared
-# fixture, stale expected string). Append a dated footer naming those journeys
-# so no stale FAIL survives the iteration on disk: a human or fresh-context
-# evaluator reading the raw artifact must not see an uncontradicted FAIL that
-# the authoritative merged file already overturned.
+# FAILed but the merged file no longer records as FAIL was overturned by the
+# LLM lane's re-confirmation (golden-script false positive — brittle selector,
+# cleared fixture, stale expected string). Append a dated footer naming those
+# journeys so no stale FAIL survives the iteration on disk: a human or
+# fresh-context evaluator reading the raw artifact must not see an
+# uncontradicted FAIL that the authoritative merged file already overturned.
+#
+# ops-hardening iter-39 (TC-7, audit finding iter-38/T1): the overturned check delegates to
+# merge_ui_test_results.py's OWN tested `verdict-of` normalization (the same annotation-tolerant
+# parsing `parse_rows` uses) instead of a raw `grep -F '| PASS |'`. That exact-string match
+# silently missed BOTH J-05 (FAIL -> "PASS (steps 1,2,4 verified live; step 3 not executed, see
+# UT-J-04)") and J-04 (FAIL -> "SKIPPED (partial — see Actual)") in iter-38: neither annotated
+# cell contains the bare substring the old check required, and the old check only recognized a
+# flip to PASS in the first place (a flip to SKIP was never checked at all) — so the footer
+# under-reported by omitting both, even though both were genuinely overturned. "Overturned" is
+# now simply "the merged verdict for this journey exists and is no longer FAIL" — covers a flip
+# to PASS, SKIP, or any annotated variant of either.
+#
+# ops-hardening iter-39 FIX PASS (audit finding B6): the footer prose is now derived PER JOURNEY
+# from the actual new verdict instead of one fixed sentence. The fixed sentence ("were overturned
+# by the LLM lane's re-confirmation ... (golden-script false positive) ... superseded") is true
+# only of a flip to PASS. For a flip to SKIP it read as "the FAIL was disproven" when the truth is
+# "the journey was never re-verified" — the widened overturn check (correct in itself) made that
+# mis-wording reachable for the first time. A verdict that means NOT-VERIFIED must never be
+# reported in language that means VERIFIED-GOOD.
 replay_lane_reconcile_regression_artifact() {
   local _rl_merged="$1"
   [[ -f "$REGRESSION_RESULTS" && -f "$_rl_merged" ]] || return 0
-  local _rl_overturned="" _j
+  local _rl_overturned="" _rl_detail="" _j _rl_new_verdict
   for _j in $(grep -E '^\| UT-J-[0-9]+ ' "$REGRESSION_RESULTS" 2>/dev/null | grep -F '| FAIL |' | grep -oE 'J-[0-9]+' | sort -u || true); do
-    if grep -E "^\| UT-$_j " "$_rl_merged" 2>/dev/null | grep -qF '| PASS |'; then
+    _rl_new_verdict="$(python3 "$MERGE_RESULTS" verdict-of "$_rl_merged" "UT-$_j" 2>/dev/null || true)"
+    if [[ -n "$_rl_new_verdict" && "$_rl_new_verdict" != "FAIL" ]]; then
       _rl_overturned+="$_j "
+      if [[ "$_rl_new_verdict" == "PASS" ]]; then
+        _rl_detail+="**$_j -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive); "
+      else
+        _rl_detail+="**$_j -> $_rl_new_verdict** (NOT re-verified — the replay FAIL is superseded, not disproven); "
+      fi
     fi
   done
   [[ -n "${_rl_overturned// /}" ]] || return 0
@@ -470,9 +506,9 @@ replay_lane_reconcile_regression_artifact() {
     echo ""
     echo "---"
     echo ""
-    echo "_Reconciliation ($(date -u +%Y-%m-%d)): the replay FAIL row(s) for ${_rl_overturned% } above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in $(basename "$_rl_merged"); the FAIL row(s) above are superseded._"
+    echo "_Reconciliation ($(date -u +%Y-%m-%d)): the replay FAIL row(s) above no longer stand in the authoritative merged file ($(basename "$_rl_merged")), which is what the goal-evaluator and the achievement gate read. Per journey: ${_rl_detail%; }._"
   } >> "$REGRESSION_RESULTS" 2>/dev/null || true
-  _replay_lane_log "Reconciled replay artifact: FAIL overturned by LLM re-confirmation for ${_rl_overturned% }(footer appended to $(basename "$REGRESSION_RESULTS"))."
+  _replay_lane_log "Reconciled replay artifact: replay FAIL no longer stands for ${_rl_overturned% }(per-journey footer appended to $(basename "$REGRESSION_RESULTS"))."
 }
 
 # Golden coverage: every PASSing journey in results file $1 should have a
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index ed95801e..55a74b0d 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -22,6 +22,15 @@ set -euo pipefail
 REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
 cd "$REPO_ROOT"
 
+# Keep the suite out of the MACHINE's forensic state. Several tests drive real
+# dispatch paths, and hg_event writes to a machine-global ledger by design — so
+# an unredirected eval run buries the record of what the machine was actually
+# doing under hundreds of synthetic events (measured: 398 in one run). The
+# postmortem reader is only as useful as that ledger is honest.
+export HOST_GUARD_EVENTS_FILE="${TMPDIR:-/tmp}/iad-evals-events.$$.jsonl"
+export HOST_GUARD_POSTMORTEM_DIR="${TMPDIR:-/tmp}/iad-evals-postmortems.$$"
+trap 'rm -rf "$HOST_GUARD_EVENTS_FILE" "$HOST_GUARD_EVENTS_FILE.1" "$HOST_GUARD_POSTMORTEM_DIR" 2>/dev/null || true' EXIT
+
 VERBOSE=false
 [[ "${1:-}" == "--verbose" ]] && VERBOSE=true
 
@@ -175,7 +184,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh; do
+for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 3c451f27..7b05d02b 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -256,6 +256,25 @@ fi
 # check guards against a stale pidfile whose PID was reused by another process.
 if [[ "$RESUME" == "true" && -f "$ENGINE_PID_FILE" ]]; then
   _prev_pid="$(cat "$ENGINE_PID_FILE" 2>/dev/null || echo "")"
+  # A pid file older than this boot means the previous engine never got to clean
+  # up: the machine went down under it. Say so plainly — a session that silently
+  # reappears mid-iteration teaches the operator that iterations vanish at
+  # random, when the truth is one hardware event with a postmortem on disk.
+  if hg_file_predates_boot "$ENGINE_PID_FILE" \
+     && python3 -c "import json,sys; sys.exit(0 if json.load(open('$SESSION_JSON')).get('status')=='in_progress' else 1)" 2>/dev/null; then
+    _pm_dir="${HOST_GUARD_POSTMORTEM_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/postmortems}"
+    echo "[run-goal] Resume: the previous engine (pid $_prev_pid) was killed by a machine reset — its pid file predates this boot and the session was still in_progress." >&2
+    if [[ -f "$_pm_dir/latest.md" ]]; then
+      echo "[run-goal]   what the hardware said: $_pm_dir/latest.md" >&2
+    fi
+    # GOAL_SESSION_DIR is only exported much later (the loop), and
+    # telemetry_enabled silently returns false without it — so the event has to
+    # carry its own session context or it would never be written at all.
+    GOAL_SESSION_DIR="$GOAL_SESSION_DIR_LOCAL" GOAL_SESSION_ID="$SESSION_ID" \
+      record_telemetry_event "halt" '{"reason":"machine_reset","detected_at_step":"resume"}'
+    GOAL_SESSION_ID="$SESSION_ID" \
+      hg_event engine_killed_by_reset "$(printf '{"prev_pid":"%s"}' "$_prev_pid")"
+  fi
   if [[ -n "$_prev_pid" ]] && kill -0 "$_prev_pid" 2>/dev/null \
      && grep -qa "run-goal" "/proc/$_prev_pid/cmdline" 2>/dev/null; then
     echo "[run-goal] Resume: a prior engine (pid $_prev_pid) is still running — stopping it cleanly first." >&2
@@ -926,14 +945,48 @@ _host_guard_sampler_path() { # project-local copy wins; framework copy is the de
   local proj="$REPO_ROOT/project-extensions/host-guard/hwmon-log.sh"
   if [[ -f "$proj" ]]; then printf '%s' "$proj"; else printf '%s' "$SCRIPT_DIR/host-guard/hwmon-log.sh"; fi
 }
-_host_guard_latest_tctl() { # newest Tctl (°C) from the sampler csv; empty if missing/stale
-  local csv="$REPO_ROOT/logs/hwmon/hwmon.csv" mtime line t
-  [[ -f "$csv" ]] || return 0
-  mtime=$(stat -c %Y "$csv" 2>/dev/null || echo 0)
-  (( EPOCHSECONDS - mtime <= 15 )) || return 0
-  line=$(tail -n 1 "$csv" 2>/dev/null || true)
-  t="${line#*,}"; t="${t%%,*}"
-  [[ "$t" =~ ^[0-9]+$ ]] && printf '%s' "$t"
+_host_guard_latest_tctl() { # newest Tctl (°C) from a FRESH sampler csv; empty if none
+  # The machine-global sampler (systemd user unit iad-hwmon.service) wins when it
+  # is running; the per-repo csv remains the fallback so a project that has not
+  # migrated keeps its thermal gate. Whichever csv is fresh is the truth.
+  local csv mtime line t
+  for csv in "${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv" \
+             "$REPO_ROOT/logs/hwmon/hwmon.csv"; do
+    [[ -f "$csv" ]] || continue
+    mtime=$(stat -c %Y "$csv" 2>/dev/null || echo 0)
+    (( EPOCHSECONDS - mtime <= 15 )) || continue
+    line=$(tail -n 1 "$csv" 2>/dev/null || true)
+    t="${line#*,}"; t="${t%%,*}"
+    if [[ "$t" =~ ^[0-9]+$ ]]; then printf '%s' "$t"; return 0; fi
+  done
+  return 0
+}
+# Read the platform's OWN postmortem register and freeze the evidence. Runs
+# before every other host-guard check because check 4's hg_sweep deletes the
+# registry records of the dead boot — the only on-disk record of which projects
+# and sessions were running when the machine went down. Never gates: a
+# hardware-asserted reset is not this session's fault and no rerun can avoid it.
+_host_guard_reset_forensics() {
+  local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" out path state chk
+  local tag hex cause streak prev
+  [[ -f "$script" ]] || return 0
+  out="$(bash "$script" ensure-postmortem 2>/dev/null)" || return 0
+  case "$out" in
+    POSTMORTEM\|*) ;;
+    *) return 0 ;;          # CLEAN / NONE / UNKNOWN — say nothing, write nothing
+  esac
+  path="${out#POSTMORTEM|}"; path="${path%|*}"; state="${out##*|}"
+  chk="$(bash "$script" check 2>/dev/null)" || chk=""
+  IFS='|' read -r tag hex cause streak prev <<< "$chk"
+  : "$tag" "$prev"
+  echo "[run-goal] host-guard: the PREVIOUS boot ended in a HARDWARE-asserted reset — ${cause:-unknown} (${hex:-?}), ${streak:-?} of the recent boots."
+  echo "[run-goal] host-guard: this is a hardware fault, not a chain failure; no CPU mask or memory ceiling can prevent it."
+  echo "[run-goal] host-guard: postmortem → $path"
+  echo "[run-goal] host-guard: remediation → docs/host-guard.md § After a hardware reset — root-cause runbook"
+  record_telemetry_event "host_guard_reset_detected" \
+    "$(printf '{"cause":"%s","code":"%s","streak":"%s","postmortem":"%s","bundle":"%s"}' \
+       "$cause" "$hex" "$streak" "$path" "$state")"
+  hg_event reset_detected "$(printf '{"code":"%s","streak":"%s"}' "$hex" "$streak")"
   return 0
 }
 _host_guard_pause() { # $1 reason, $2 detected_at_step — pause AWAITING_HOST_GUARD (resumable) and exit
@@ -953,6 +1006,7 @@ with _os.fdopen(_fd, "w") as _f:
 _os.replace(_tmp, "$SESSION_JSON")
 PY
   record_telemetry_event "halt" "$(printf '{"reason":"AWAITING_HOST_GUARD","detected_at_step":"%s"}' "$step")"
+  hg_event engine_pause "$(printf '{"reason":"AWAITING_HOST_GUARD","step":"%s"}' "$step")"
   echo ""
   echo "Fix the host-guard issue (project-extensions/host-guard/README.md), then resume:"
   echo "  ./scripts/automation/run-goal.sh --resume --session-id $SESSION_ID"
@@ -966,6 +1020,11 @@ preflight_host_guard() {
   # shellcheck disable=SC1090
   source "$hg_env"
   [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+
+  # 0. Did the LAST boot die? Capture the postmortem BEFORE check 4 sweeps the
+  # registry records that name who was running. Idempotent: one bundle per boot.
+  _host_guard_reset_forensics
+
   local sampler fail_reason=""
   sampler="$(_host_guard_sampler_path)"
 
@@ -1082,10 +1141,19 @@ host_guard_iteration_gate() {
 
   if [[ "${HOST_GUARD_REQUIRE_PUMP_CONFINED:-0}" == "1" && "${AGENT_BACKEND:-}" == "interactive" ]]; then
     local hb="${CHAIN_DISPATCH_DIR:-$GOAL_SESSION_DIR_LOCAL/dispatch}/.pump-alive"
-    local pump_pid="" hb_age=999999 target="" width allowed_list allowed_n
+    local pump_pid="" hb_age=999999 target="" width allowed_list allowed_n hb_stt=""
     if [[ -f "$hb" ]]; then
       hb_age=$(( EPOCHSECONDS - $(stat -c %Y "$hb" 2>/dev/null || echo 0) ))
       pump_pid=$(sed -n 's/^pid=\([0-9][0-9]*\)$/\1/p' "$hb" 2>/dev/null | head -n 1)
+      # Pid-recycling defense across a machine reset: the heartbeat records the
+      # pump's start time, so a pid that now belongs to some other process — the
+      # normal case after a reboot reuses the pid space — is discarded instead of
+      # being verified, adopted, or (worse) tasksetted.
+      hb_stt=$(sed -n 's/^starttime=\([0-9][0-9]*\)$/\1/p' "$hb" 2>/dev/null | head -n 1)
+      if [[ -n "$pump_pid" && -n "$hb_stt" ]] && ! hg_pid_matches "$pump_pid" "$hb_stt"; then
+        echo "[run-goal] host-guard: .pump-alive names pid $pump_pid, but that process is gone or was recycled (a machine reset reuses pids) — ignoring the stale heartbeat."
+        pump_pid=""
+      fi
     fi
     # Verification handle: the CLI session root captured at engine launch wins
     # (it outlives short-lived heartbeat writers); else the live heartbeat pid.
@@ -1147,6 +1215,12 @@ host_guard_iteration_gate() {
       echo "[run-goal] host-guard WARNING: ${hg_verdict#WARN|}"
       record_telemetry_event "host_guard_aggregate_warn" \
         "$(python3 -c 'import json,sys; print(json.dumps({"detail": sys.argv[1]}))' "${hg_verdict#WARN|}")" ;;
+    OK)
+      # The healthy path used to be entirely silent, so after a reset nothing on
+      # disk said what the guard believed at the time — how many sessions were
+      # live, or that it had checked at all. One durable line per gate fixes it.
+      hg_event aggregate_ok \
+        "$(printf '{"live":%s,"iter":%s}' "$(hg_live_records | wc -l | tr -d ' ')" "${CURRENT_ITER:-0}")" ;;
   esac
   return 0
 }
@@ -1773,6 +1847,7 @@ _goal_engine_on_exit() {
   chain_tmp_cleanup
   # Drop this engine's host-guard registry record so a concurrent project sees
   # the freed budget immediately (the pid sweep would catch it anyway).
+  hg_event engine_stop "$(printf '{"iter":%s}' "${CURRENT_ITER:-0}")" 2>/dev/null || true
   hg_release 2>/dev/null || true
   # REL-4: release LAST so the lock covers the whole cleanup window. Owner-
   # checked no-op when this process never acquired (e.g. a refused start).
@@ -1799,6 +1874,12 @@ trap on_abort INT TERM
 # refuses fast with exit $ENGINE_LOCK_REFUSED_EXIT; a dead one is replaced
 # loudly (lib/engine-lock.sh; docs/TROUBLESHOOTING.md "lock held").
 acquire_engine_lock "$GOAL_SESSION_DIR_LOCAL/.engine.lock" "engine for goal session '$SESSION_ID'" || exit $?
+# Machine-wide durable ledger (survives a power-cut reset; see hg_event).
+hg_event engine_start "$(printf '{"resume":"%s","backend":"%s"}' "${RESUME:-false}" "${AGENT_BACKEND:-}")"
+# Which host mitigations were actually in force for THIS run — the postmortem is
+# written on the next boot, when a runtime-only knob has already reverted, so a
+# soak week is only attributable if the state is recorded while the run happens.
+hg_event host_state "$(hg_host_mitigations)"
 
 # Advisory preflight doctor (REL-2): one PASS/WARN/FAIL table of environment
 # truth into the engine log BEFORE anything mutates state (tmp init/janitor
@@ -2025,6 +2106,7 @@ PY
   PRIOR_DEPTH=$(python3 -c "import json; print(json.load(open('$SESSION_JSON')).get('next_depth') or 'lean')")
 
   record_telemetry_event "iter_start" "$(jq -cn --arg n "$ITER_NAME" --arg pv "$PRIOR_VERDICT" --arg pd "$PRIOR_DEPTH" --arg ss "$(cat "$ITER_DIR/snapshot-sha" 2>/dev/null || echo "")" '{iter_name:$n, prior_verdict:$pv, prior_depth:$pd, snapshot_sha:$ss}' 2>/dev/null || printf '{"iter_name":"%s"}' "$ITER_NAME")"
+  hg_event iter_start "$(printf '{"iter":%s,"name":"%s","depth":"%s"}' "${CURRENT_ITER:-0}" "$ITER_NAME" "$PRIOR_DEPTH")"
   # SPEED-15: wall-clock budget clock starts here; exported so the lean/full
   # executor child processes measure from the same origin.
   export CHAIN_ITER_START_EPOCH="$(date +%s)"
diff --git a/incredible_auto_dev/tests/automation/test-doctor.sh b/incredible_auto_dev/tests/automation/test-doctor.sh
index 43672904..58b59641 100644
--- a/incredible_auto_dev/tests/automation/test-doctor.sh
+++ b/incredible_auto_dev/tests/automation/test-doctor.sh
@@ -136,11 +136,19 @@ run_doctor() {
     if [[ "$a" == "--" ]]; then in_args=true; continue; fi
     $in_args && args+=("$a") || envs+=("$a")
   done
+  # The healthy fixture must stay healthy on ANY host — including one that has
+  # actually had a hardware reset. An empty kernel-log fixture pins reset-reason
+  # (and therefore ras-logging, which keys off reset history) to the clean case;
+  # the postmortem dir is redirected so the row's sanctioned write cannot escape
+  # into the real cache.
   env "PATH=$SHIMS:$FARM" "HOME=$FHOME" \
       "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
       "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+      "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+      "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
       "CHAIN_DOCTOR_AMBIENT=" "${envs[@]}" bash "$DOCTOR" "${args[@]}"
 }
+printf 'Jul 30 17:14:29 host kernel: Linux version 7.0.0-28-generic\n' > "$TMP_DIR/klog-clean"
 
 echo ""
 echo "=== doctor.sh: healthy fixture ==="
@@ -176,9 +184,9 @@ echo ""
 
 rc=0; out=$(run_doctor -- --list 2>&1) || rc=$?
 n=$(echo "$out" | grep -c '^[a-z0-9-]*$' || true)
-{ [[ $rc -eq 0 && $n -eq 17 ]]; } \
-  && assert "--list prints the 17 check keys" "pass" \
-  || assert "--list prints the 17 check keys (rc=$rc n=$n)" "fail"
+{ [[ $rc -eq 0 && $n -eq 19 ]]; } \
+  && assert "--list prints the 19 check keys" "pass" \
+  || assert "--list prints the 19 check keys (rc=$rc n=$n)" "fail"
 echo "$out" | grep -qx "tmp-health" && echo "$out" | grep -qx "chrome-exclusive" \
   && assert "--list includes the evidence-born checks" "pass" \
   || assert "--list includes the evidence-born checks" "fail"
@@ -203,6 +211,8 @@ echo ""
 rc=0; out=$(env "PATH=$SHIMS_NOJQ:$FARM" "HOME=$FHOME" \
     "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
     "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+    "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+    "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
     "CHAIN_DOCTOR_AMBIENT=" bash "$DOCTOR" 2>&1) || rc=$?
 [[ $rc -eq 0 ]] && assert "missing jq: non-strict run still exits 0 (advisory)" "pass" \
                 || assert "missing jq: non-strict run still exits 0 (got $rc)" "fail"
@@ -219,6 +229,8 @@ echo "$out" | grep -Eq '\[doctor\] summary: pass=[0-9]+ warn=0 fail=1 skip=0' \
 rc=0; env "PATH=$SHIMS_NOJQ:$FARM" "HOME=$FHOME" \
     "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
     "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+    "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+    "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
     "CHAIN_DOCTOR_AMBIENT=" bash "$DOCTOR" --strict-doctor >/dev/null 2>&1 || rc=$?
 [[ $rc -eq 1 ]] && assert "missing jq: --strict-doctor exits 1" "pass" \
                 || assert "missing jq: --strict-doctor exits 1 (got $rc)" "fail"
@@ -244,6 +256,8 @@ chmod 755 "$ROTMP"
 rc=0; out=$(env "PATH=$SHIMS_CHROME:$FARM" "HOME=$FHOME" \
     "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
     "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+    "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+    "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
     "CHAIN_DOCTOR_AMBIENT=" bash "$DOCTOR" --only chrome-exclusive 2>&1) || rc=$?
 echo "$out" | grep -Eq 'WARN +chrome-exclusive +.*4242' \
   && assert "chrome-exclusive WARNs naming competing PIDs" "pass" \
diff --git a/incredible_auto_dev/tests/automation/test-engine-lock.sh b/incredible_auto_dev/tests/automation/test-engine-lock.sh
index b5604deb..34057dc5 100644
--- a/incredible_auto_dev/tests/automation/test-engine-lock.sh
+++ b/incredible_auto_dev/tests/automation/test-engine-lock.sh
@@ -98,6 +98,35 @@ else
     assert "A1 acquire creates lock with pid/host/epoch metadata (never appeared)" "fail"
   fi
 
+  # A1b: the boot id is what survives a machine reset. A reset reuses the pid
+  # space, so a lock left by the boot that died can name a pid that is alive
+  # NOW and even runs a matching command — the pid probe would call that FRESH
+  # and refuse to start, wedging the session until someone deletes it by hand.
+  [[ -s "$L1/boot_id" ]] \
+    && assert "A1b acquire records the boot id" "pass" \
+    || assert "A1b acquire records the boot id" "fail"
+  LB="$WORK/a1b.lock"
+  mkdir -p "$LB"
+  echo "$$" > "$LB/pid"; cat /proc/sys/kernel/random/boot_id > "$LB/boot_id"
+  bash -c 'source "'"$LIB"'"; printf "%s" "$(_engine_lock_host)"' > "$LB/host"
+  date +%s > "$LB/epoch"; basename -- "$0" > "$LB/cmd"
+  V="$(bash -c 'source "'"$LIB"'"; engine_lock_classify "$1"' _ "$LB")"
+  [[ "$V" == FRESH* ]] \
+    && assert "A1b current-boot lock with a live pid is FRESH" "pass" \
+    || assert "A1b current-boot lock with a live pid is FRESH (got: $V)" "fail"
+  echo "dead-beef-from-the-boot-that-died" > "$LB/boot_id"
+  V="$(bash -c 'source "'"$LIB"'"; engine_lock_classify "$1"' _ "$LB")"
+  if [[ "$V" == STALE* && "$V" == *"previous boot"* ]]; then
+    assert "A1b lock from a previous boot is STALE even with a live pid" "pass"
+  else
+    assert "A1b lock from a previous boot is STALE even with a live pid (got: $V)" "fail"
+  fi
+  rm -f "$LB/boot_id"
+  V="$(bash -c 'source "'"$LIB"'"; engine_lock_classify "$1"' _ "$LB")"
+  [[ "$V" == FRESH* ]] \
+    && assert "A1b pre-upgrade lock without a boot id keeps old behaviour" "pass" \
+    || assert "A1b pre-upgrade lock without a boot id keeps old behaviour (got: $V)" "fail"
+
   # A2: a second process must refuse fast with the distinct code + message.
   rc=0; err="$WORK/a2.err"
   bash -c 'source "'"$LIB"'"; acquire_engine_lock "$1" "unit second"' _ "$L1" 2>"$err" || rc=$?
diff --git a/incredible_auto_dev/tests/automation/test-host-guard.sh b/incredible_auto_dev/tests/automation/test-host-guard.sh
index 70dc1155..0886a7f7 100755
--- a/incredible_auto_dev/tests/automation/test-host-guard.sh
+++ b/incredible_auto_dev/tests/automation/test-host-guard.sh
@@ -221,6 +221,119 @@ CHAIN_TMP_ROOT="$WORK/tmproot" HOST_GUARD_REGISTRY_DIR="$WORK/tmproot/host-guard
     ls \"\$HOST_GUARD_REGISTRY_DIR\"/*.rec >/dev/null 2>&1
   " && assert "registry survives the chain-tmp janitor" pass || assert "registry survives the chain-tmp janitor" fail
 
+# 12. Pid identity across a reboot (HOST-6). A machine reset reuses the pid
+# space, so `kill -0` alone will happily confirm a pid recorded by the boot that
+# died — the start time is what tells the two apart.
+setsid sleep 300 & VP=$!; _SPAWNED_PGIDS+=("$VP")
+wait_for 5 test -d "/proc/$VP"
+_VP_STT="$(_hg_proc_starttime "$VP")"
+hg_pid_matches "$VP" "$_VP_STT" && assert "pid_matches: live pid with its own starttime" pass || assert "pid_matches: live pid with its own starttime" fail
+hg_pid_matches "$VP" "1" && assert "pid_matches: recycled pid rejected" fail || assert "pid_matches: recycled pid rejected" pass
+hg_pid_matches "$VP" "" && assert "pid_matches: missing starttime rejected" fail || assert "pid_matches: missing starttime rejected" pass
+kill -KILL "$VP" 2>/dev/null; wait "$VP" 2>/dev/null
+wait_for 5 bash -c "! kill -0 $VP 2>/dev/null"
+hg_pid_matches "$VP" "$_VP_STT" && assert "pid_matches: dead pid rejected" fail || assert "pid_matches: dead pid rejected" pass
+
+# 13. Boot-relative file age (HOST-7): "was this written before the machine came
+# up?" is how a resume tells a crash from a normal stop. No test can reboot a
+# host, so the boot epoch has an override seam.
+: > "$WORK/agefile"
+HOST_GUARD_BTIME_OVERRIDE=1 hg_file_predates_boot "$WORK/agefile" \
+  && assert "predates_boot: current file is not stale" fail || assert "predates_boot: current file is not stale" pass
+HOST_GUARD_BTIME_OVERRIDE=9999999999 hg_file_predates_boot "$WORK/agefile" \
+  && assert "predates_boot: file older than boot detected" pass || assert "predates_boot: file older than boot detected" fail
+HOST_GUARD_BTIME_OVERRIDE=9999999999 hg_file_predates_boot "$WORK/nope" \
+  && assert "predates_boot: missing file is not stale" fail || assert "predates_boot: missing file is not stale" pass
+
+# 14. Durable event ledger (HOST-4). The ledger is the only cross-repo record of
+# what the machine was doing; it must be valid JSON, must respect the no-op rule,
+# and concurrent engines must not shred each other's lines.
+EVENTS="$WORK/events.jsonl"
+( export HOST_GUARD_EVENTS_FILE="$EVENTS" HOST_GUARD_HOST_ENV_FILE="$WORK/absent.env" HOST_GUARD_ENABLED=0
+  source "$LIB"; hg_event noop_check '{"x":1}' )
+[[ -f "$EVENTS" ]] && assert "event: no-op rule (no host env, not enabled) writes nothing" fail || assert "event: no-op rule (no host env, not enabled) writes nothing" pass
+
+printf 'HOST_GUARD_GLOBAL_CPU_LIST="0-3"\n' > "$WORK/host-guard-host.env"
+HOST_GUARD_EVENTS_FILE="$EVENTS" REPO_ROOT=/fake/projA GOAL_SESSION_ID=sessA \
+  CHAIN_CURRENT_AGENT=developer hg_event iter_start '{"iter":7}'
+assert_eq "event: one line written" "1" "$(wc -l < "$EVENTS" | tr -dc 0-9)"
+if command -v jq >/dev/null 2>&1; then
+  jq -e . "$EVENTS" >/dev/null 2>&1 && assert "event: valid JSON" pass || assert "event: valid JSON" fail
+  assert_eq "event: carries project"  "/fake/projA" "$(jq -r '.project' "$EVENTS")"
+  assert_eq "event: carries session"  "sessA"       "$(jq -r '.sid' "$EVENTS")"
+  assert_eq "event: carries agent"    "developer"   "$(jq -r '.agent' "$EVENTS")"
+  assert_eq "event: carries type"     "iter_start"  "$(jq -r '.event' "$EVENTS")"
+  assert_eq "event: splices payload"  "7"           "$(jq -r '.iter' "$EVENTS")"
+  assert_eq "event: carries boot id"  "$(_hg_boot_id)" "$(jq -r '.boot' "$EVENTS")"
+else
+  grep -q '"event":"iter_start"' "$EVENTS" && assert "event: carries type (no jq)" pass || assert "event: carries type (no jq)" fail
+fi
+
+# An oversized payload must be DROPPED, never truncated: half a JSON object in
+# the ledger would break every reader for every later line.
+: > "$EVENTS"
+HOST_GUARD_EVENTS_FILE="$EVENTS" hg_event big "{\"blob\":\"$(head -c 1200 /dev/zero | tr '\0' 'x')\"}"
+if command -v jq >/dev/null 2>&1; then
+  jq -e . "$EVENTS" >/dev/null 2>&1 && assert "event: oversized payload still valid JSON" pass || assert "event: oversized payload still valid JSON" fail
+fi
+grep -q 'payload_dropped' "$EVENTS" && assert "event: oversized payload dropped, not truncated" pass || assert "event: oversized payload dropped, not truncated" fail
+
+: > "$EVENTS"
+# Wait on THESE pids only: a bare `wait` would also block on the long-lived
+# `sleep 300` victim processes the registration tests keep alive, stalling the
+# suite for minutes.
+_APPENDERS=()
+for _i in $(seq 1 20); do
+  ( HOST_GUARD_EVENTS_FILE="$EVENTS" hg_event "concurrent$_i" '{"n":1}' ) &
+  _APPENDERS+=("$!")
+done
+wait "${_APPENDERS[@]}"
+assert_eq "event: 20 concurrent appenders → 20 lines" "20" "$(wc -l < "$EVENTS" | tr -dc 0-9)"
+if command -v jq >/dev/null 2>&1; then
+  assert_eq "event: every concurrent line is valid JSON" "20" "$(jq -c . "$EVENTS" 2>/dev/null | wc -l | tr -dc 0-9)"
+fi
+
+HOST_GUARD_EVENTS_FILE="$EVENTS" HOST_GUARD_EVENTS_MAX_BYTES=200 hg_event rotate_me '{"n":1}'
+[[ -f "$EVENTS.1" ]] && assert "event: ring rotation at max bytes" pass || assert "event: ring rotation at max bytes" fail
+
+# 15. Concurrent-engine cap (HOST-8). On a host whose resets are HARDWARE, the
+# honest mitigation is fewer engines, not a narrower mask.
+CAPREG="$WORK/capreg"; mkdir -p "$CAPREG"
+setsid sleep 300 & C1=$!; _SPAWNED_PGIDS+=("$C1")
+setsid sleep 300 & C2=$!; _SPAWNED_PGIDS+=("$C2")
+wait_for 5 test -d "/proc/$C1"; wait_for 5 test -d "/proc/$C2"
+CAP_SENIOR="$(HOST_GUARD_REGISTRY_DIR="$CAPREG" hg_register engine "$C1" /fake/capA sA "0-3" 4G)"
+sleep 1
+CAP_JUNIOR="$(HOST_GUARD_REGISTRY_DIR="$CAPREG" hg_register engine "$C2" /fake/capB sB "0-3" 4G)"
+_cap_verdict() { # $1 own_rec, $2 cap
+  HOST_GUARD_REGISTRY_DIR="$CAPREG" HOST_GUARD_GLOBAL_CPU_LIST="0-3" \
+    HOST_GUARD_MAX_ENGINES="$2" hg_aggregate_verdict "$1"
+}
+case "$(_cap_verdict "$CAP_JUNIOR" 1)" in
+  PAUSE\|*) assert "cap: junior engine pauses over HOST_GUARD_MAX_ENGINES=1" pass ;;
+  *)        assert "cap: junior engine pauses over HOST_GUARD_MAX_ENGINES=1" fail ;;
+esac
+_cap_verdict "$CAP_JUNIOR" 1 | grep -q 'HOST_GUARD_MAX_ENGINES=1' \
+  && assert "cap: pause message names the knob" pass || assert "cap: pause message names the knob" fail
+case "$(_cap_verdict "$CAP_SENIOR" 1)" in
+  WARN\|*) assert "cap: senior engine warns and keeps running" pass ;;
+  *)       assert "cap: senior engine warns and keeps running" fail ;;
+esac
+assert_eq "cap: cap=2 with 2 engines is OK"    "OK" "$(_cap_verdict "$CAP_JUNIOR" 2)"
+# The case that matters most on a capped host: ONE engine under cap=1 must run.
+# An off-by-one here (>= instead of >) would pause every single session forever.
+SOLOREG="$WORK/soloreg"; mkdir -p "$SOLOREG"
+CAP_SOLO="$(HOST_GUARD_REGISTRY_DIR="$SOLOREG" hg_register engine "$C1" /fake/solo s1 "0-3" 4G)"
+assert_eq "cap: the ONLY engine runs under cap=1" "OK" \
+  "$(HOST_GUARD_REGISTRY_DIR="$SOLOREG" HOST_GUARD_GLOBAL_CPU_LIST="0-3" \
+     HOST_GUARD_MAX_ENGINES=1 hg_aggregate_verdict "$CAP_SOLO")"
+assert_eq "cap: absent cap = unlimited"        "OK" "$(_cap_verdict "$CAP_JUNIOR" '')"
+assert_eq "cap: junk cap ignored"              "OK" "$(_cap_verdict "$CAP_JUNIOR" 'abc')"
+assert_eq "cap: cap=0 ignored (never lock out)" "OK" "$(_cap_verdict "$CAP_JUNIOR" 0)"
+# A pump is not an engine: only engines count toward the cap.
+HOST_GUARD_REGISTRY_DIR="$CAPREG" hg_register pump "$C1" /fake/capA sA "0-3" 4G >/dev/null
+assert_eq "cap: pump records do not count as engines" "OK" "$(_cap_verdict "$CAP_JUNIOR" 2)"
+
 echo ""
 echo "── B. run-goal.sh wiring (real engine, stub claude) ────────────────────"
 
@@ -308,7 +421,15 @@ else
   assert "engine: pause message names the senior session" fail
   assert "engine: pause message names the memory budget" fail
 fi
-[[ -d "$SBX/runs/goal-session-hg1/.engine.lock" ]] && assert "engine: lock released on host-guard pause" fail || assert "engine: lock released on host-guard pause" pass
+# The paused STATUS is written before the process exits; the lock is released in
+# the EXIT trap that follows. Polling for it is the honest assertion — checking
+# the instant the status flips races the trap, and the race widens with every
+# fsync on the cleanup path (the durable event ledger added two).
+if wait_for 20 bash -c "! [[ -d '$SBX/runs/goal-session-hg1/.engine.lock' ]]"; then
+  assert "engine: lock released on host-guard pause" pass
+else
+  assert "engine: lock released on host-guard pause" fail
+fi
 ls "$ENG_REG"/engine-*.rec 2>/dev/null | grep -qv "engine-$SENIOR-" && assert "engine: junior's own record released on pause" fail || assert "engine: junior's own record released on pause" pass
 
 # B2. With the budget raised the same session proceeds (WARN path, not PAUSE).
diff --git a/incredible_auto_dev/tests/automation/test-replay-lane.sh b/incredible_auto_dev/tests/automation/test-replay-lane.sh
index b18269e8..ddccf7a8 100644
--- a/incredible_auto_dev/tests/automation/test-replay-lane.sh
+++ b/incredible_auto_dev/tests/automation/test-replay-lane.sh
@@ -314,6 +314,21 @@ grep -q 'routed to the LLM lane' "$REG6" \
   && assert "verify rc=6 twice: raw artifact footer explains the routing" pass \
   || assert "verify rc=6 twice: raw artifact footer explains the routing" fail
 
+# ── 6b. Verify rc=7 (ops-hardening iter-39, TC-5): backend-unreachable BLOCKED,
+#        distinct from rc=6 (browser-infra) — falls back to the LLM lane on the
+#        FIRST attempt, no retry, distinct log line naming it "BLOCKED" not
+#        "browser-infra" or a real regression.
+reset_goldens
+golden "J-01"
+out="$(STUB_REPLAY_RC=7 RUN_PARTITION_LOG="$WORK/lane7.log" run_partition "J-01 J-02 ")"
+want="R_REPLAY=<>|R_LLM=<J-02 >|use=<no>|failed=<>"
+[[ "$out" == "$want" ]] \
+  && assert "verify rc=7: falls back to LLM lane for ALL regression journeys" pass \
+  || { assert "verify rc=7: falls back to LLM lane for ALL regression journeys" fail; echo "    got: $out"; }
+grep -q "backend unreachable before any journey ran (rc=7, BLOCKED" "$WORK/lane7.log" \
+  && assert "verify rc=7: greppable BLOCKED-distinct log line" pass \
+  || assert "verify rc=7: greppable BLOCKED-distinct log line" fail
+
 # ── 7. Escape hatch ──────────────────────────────────────────────────────────
 reset_goldens
 golden "J-01"
@@ -395,6 +410,46 @@ grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md"
   && assert "merge: reconciliation footer names the overturned journey (companion 1)" pass \
   || assert "merge: reconciliation footer names the overturned journey (companion 1)" fail
 
+# ops-hardening iter-39 (TC-7, audit finding iter-38/T1): reproduces the EXACT bug — a raw
+# replay FAIL overturned to an ANNOTATED verdict cell (not a bare "PASS"/"SKIP") must still be
+# named in the footer. The old exact-string `grep -F '| PASS |'` missed both J-05-style
+# (FAIL -> "PASS (steps ... verified)") and J-04-style (FAIL -> "SKIPPED (partial ...)") flips
+# in iter-38, silently under-reporting the footer by omitting both.
+merge_case '**Browser QA Verdict:** PASS
+
+## Results Table
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---|---|---|---|---|---|---|---|
+| UT-J-07 | filter table | regression | P1 | e | steps 1,2,4 verified live; step 3 not executed | PASS (steps 1,2,4 verified live; step 3 not executed, see UT-J-04) | none |'
+grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
+  && grep -q 'J-07' <(grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md") \
+  && assert "merge: reconciliation footer names an ANNOTATED PASS overturn (J-05-style, TC-7)" pass \
+  || assert "merge: reconciliation footer names an ANNOTATED PASS overturn (J-05-style, TC-7)" fail
+# ops-hardening iter-39 FIX PASS (audit finding B6): a flip to PASS — and ONLY a flip to PASS — may
+# be described as a live re-confirmation / false positive.
+grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'J-07 -> PASS' \
+  && grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'false positive' \
+  && assert "merge: footer wording for a PASS flip claims re-confirmation (B6)" pass \
+  || assert "merge: footer wording for a PASS flip claims re-confirmation (B6)" fail
+
+merge_case '**Browser QA Verdict:** SKIPPED
+
+## Results Table
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---|---|---|---|---|---|---|---|
+| UT-J-07 | filter table | regression | P1 | e | not executed live, judged unsafe to restart | SKIPPED (partial — see Actual) | none |'
+grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
+  && grep -q 'J-07' <(grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md") \
+  && assert "merge: reconciliation footer names a FAIL->SKIPPED overturn (J-04-style, TC-7)" pass \
+  || assert "merge: reconciliation footer names a FAIL->SKIPPED overturn (J-04-style, TC-7)" fail
+# ops-hardening iter-39 FIX PASS (audit finding B6): the SAME flip must NOT be described as a
+# re-confirmation / disproven FAIL — SKIP means the journey was never re-verified. This is the
+# assertion the fixed wording exists for; the pre-fix fixed sentence fails it.
+grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'NOT re-verified' \
+  && ! grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'false positive' \
+  && assert "merge: footer wording for a SKIP flip does NOT claim re-confirmation (B6)" pass \
+  || assert "merge: footer wording for a SKIP flip does NOT claim re-confirmation (B6)" fail
+
 merge_case '**Browser QA Verdict:** PASS
 
 ## Results Table
diff --git a/incredible_auto_dev/tests/automation/test-reset-forensics.sh b/incredible_auto_dev/tests/automation/test-reset-forensics.sh
new file mode 100644
index 00000000..6aa051a2
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-reset-forensics.sh
@@ -0,0 +1,265 @@
+#!/usr/bin/env bash
+# test-reset-forensics.sh — the platform's own reset-reason register (HOST-2/3/7):
+#   A. classification: fault vs planned reboot vs clean vs unreadable, and the
+#      fault streak over recent boots
+#   B. the postmortem bundle: who was running, the final pre-reset telemetry,
+#      session tails, idempotency, and the no-op rule on healthy hosts
+#   C. doctor rows (reset-reason, ras-logging) driven by the same fixtures
+#   D. engine wiring: the call sites that make any of this fire
+#
+# Offline, no root, no journal, no model calls: every kernel log, boot list and
+# registry record is a fixture, injected through the documented env seams.
+#
+# WHY THIS SUITE EXISTS: seven hard resets were investigated as software load
+# problems while the CPU printed the cause on every boot. The regression this
+# guards against is silence — a reader that reports CLEAN when it cannot read,
+# or that never gets called.
+
+set -uo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+RF="$ENGINE_ROOT/scripts/automation/host-guard/reset-forensics.sh"
+DOCTOR="$ENGINE_ROOT/scripts/automation/doctor.sh"
+
+PASS=0
+FAIL=0
+assert() {
+  if [[ "$2" == "pass" ]]; then echo "  PASS  $1"; PASS=$((PASS + 1)); else echo "  FAIL  $1"; FAIL=$((FAIL + 1)); fi
+}
+assert_eq() { # name expected actual
+  if [[ "$2" == "$3" ]]; then assert "$1" pass; else echo "  FAIL  $1 (expected '$2', got '$3')"; FAIL=$((FAIL + 1)); fi
+}
+assert_has() { # name needle haystack
+  if [[ "$3" == *"$2"* ]]; then assert "$1" pass; else echo "  FAIL  $1 (no '$2' in output)"; FAIL=$((FAIL + 1)); fi
+}
+assert_lacks() { # name needle haystack
+  if [[ "$3" != *"$2"* ]]; then assert "$1" pass; else echo "  FAIL  $1 (unexpected '$2' in output)"; FAIL=$((FAIL + 1)); fi
+}
+
+WORK="$(mktemp -d)"
+cleanup() { rm -rf "$WORK"; return 0; }
+trap cleanup EXIT
+
+# ── Fixtures ────────────────────────────────────────────────────────────────
+# The real lines this machine printed, verbatim — a paraphrase would let the
+# parser drift away from the format it actually has to read.
+FAULT_LINE='Jul 30 17:14:29 host kernel: x86/amd: Previous system reset reason [0x08000800]: an uncorrected error caused a data fabric sync flood event'
+REBOOT_LINE='Jul 21 18:40:54 host kernel: x86/amd: Previous system reset reason [0x00080800]: software wrote 0x6 to reset control register 0xCF9'
+
+mkdir -p "$WORK/klogs"
+printf 'Jul 30 17:14:29 host kernel: Linux version 7.0.0-28-generic\nJul 30 17:14:29 host kernel: Command line: ro quiet\n' > "$WORK/klog-clean"
+{ cat "$WORK/klog-clean"; printf '%s\n' "$FAULT_LINE"; }  > "$WORK/klog-fault"
+{ cat "$WORK/klog-clean"; printf '%s\n' "$REBOOT_LINE"; } > "$WORK/klog-reboot"
+
+# Four boots: two faults, one planned reboot, one clean.
+cat > "$WORK/boots" <<'EOF'
+IDX BOOT ID                          FIRST ENTRY                 LAST ENTRY
+ -3 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1 Mon 2026-07-27 20:46:48 BST Tue 2026-07-28 01:07:32 BST
+ -2 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2 Tue 2026-07-28 01:08:33 BST Wed 2026-07-29 14:00:08 BST
+ -1 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3 Wed 2026-07-29 14:03:25 BST Thu 2026-07-30 17:10:26 BST
+  0 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa4 Thu 2026-07-30 17:14:29 BST Thu 2026-07-30 20:56:10 BST
+EOF
+cp "$WORK/klog-clean"  "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1.klog"
+cp "$WORK/klog-reboot" "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2.klog"
+cp "$WORK/klog-fault"  "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3.klog"
+cp "$WORK/klog-fault"  "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa4.klog"
+
+# A dead boot's registry: two engines and a pump from a boot that no longer is.
+REG="$WORK/registry"; mkdir -p "$REG"
+BOOT_EPOCH=1785400000        # pretend the current boot started here
+_mkrec() { # <file> <kind> <pid> <root> <sid>
+  cat > "$REG/$1" <<EOF
+kind=$2
+pid=$3
+starttime=999999
+boot_id=dead-beef-from-the-boot-that-died
+host=testhost
+epoch=1785351643
+project_root=$4
+session_id=$5
+cpu_list=0-3,8-11
+memory_high=10G
+EOF
+}
+_mkrec "engine-101-999999.rec" engine 101 "$WORK/projA" desk
+_mkrec "engine-102-999999.rec" engine 102 "$WORK/projB" ops
+_mkrec "pump-103-999999.rec"   pump   103 "$WORK/projA" ""
+
+for p in projA projB; do
+  mkdir -p "$WORK/$p/logs/hwmon"
+done
+# Pre-reset samples (epoch < BOOT_EPOCH) plus, for projA, post-reboot samples a
+# restarted sampler would append — the bundle must show the former, not the latter.
+{ echo "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10,cpu_mhz"
+  for i in $(seq 1 25); do echo "$(( BOOT_EPOCH - 100 + i )),65,57,26,22,40,56,55,20,6.54,11513,28522,0.00,0.00,3900"; done
+  echo "$(( BOOT_EPOCH + 5000 )),44,40,8,5,40,45,44,20,0.10,23000,28671,0.00,0.00,1200"
+} > "$WORK/projA/logs/hwmon/hwmon.csv"
+{ echo "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10,cpu_mhz"
+  echo "$(( BOOT_EPOCH - 3 )),74,60,37,30,41,57,56,21,7.28,11424,28522,0.00,0.00,4100"
+} > "$WORK/projB/logs/hwmon/hwmon.csv"
+
+mkdir -p "$WORK/projA/runs/goal-session-desk" "$WORK/projB/runs/goal-session-ops"
+printf '{"event":"iter_start","iter":26}\n{"event":"coherence_pass","iter":26}\n' \
+  > "$WORK/projA/runs/goal-session-desk/telemetry.jsonl"
+printf '16:56:11 [browser-qa] dispatching J-05 UNIQUEMARKER_ENGINELOG\n' \
+  > "$WORK/projA/runs/goal-session-desk/engine.log"
+printf '{"status":"in_progress","current_iter":26}\n' \
+  > "$WORK/projA/runs/goal-session-desk/session.json"
+printf '{"event":"iter_start","iter":39}\n' > "$WORK/projB/runs/goal-session-ops/telemetry.jsonl"
+
+PM="$WORK/postmortems"
+export HOST_GUARD_RESET_BOOTS_FILE="$WORK/boots"
+export HOST_GUARD_RESET_KLOG_DIR="$WORK/klogs"
+export HOST_GUARD_POSTMORTEM_DIR="$PM"
+export HOST_GUARD_REGISTRY_DIR="$REG"
+export HOST_GUARD_BTIME_OVERRIDE="$BOOT_EPOCH"
+export HOST_GUARD_EVENTS_FILE="$WORK/events.jsonl"
+
+echo "── A. classification ───────────────────────────────────────────────────"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" check)"
+assert_has "check: fault reported as RESET"       "RESET|0x08000800|" "$OUT"
+assert_has "check: cause text preserved"          "data fabric sync flood" "$OUT"
+assert_has "check: streak counts fault boots only" "|2/4|" "$OUT"
+assert_has "check: names the dead boot"           "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3" "$OUT"
+
+# The single highest-value false positive to avoid: an ordinary `reboot` also
+# prints a reset-reason line. Treating it as an incident would cry wolf forever.
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-reboot" bash "$RF" check)"
+assert_has   "check: planned reboot is CLEAN"        "CLEAN|" "$OUT"
+assert_has   "check: planned reboot says why"        "software-initiated reboot" "$OUT"
+assert_lacks "check: planned reboot is not a RESET"  "RESET|" "$OUT"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" bash "$RF" check)"
+assert_has "check: clean boot reported CLEAN" "CLEAN|" "$OUT"
+
+# Unreadable ≠ clean. A reader that cannot see the register must SAY so, or it
+# silently certifies every machine as healthy.
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/does-not-exist" bash "$RF" check)"
+assert_has "check: unreadable log → UNKNOWN, never CLEAN" "UNKNOWN|" "$OUT"
+# The realistic failure: journalctl EXISTS but returns nothing because this user
+# cannot read the kernel log. Without the liveness probe that case would look
+# exactly like a healthy machine.
+mkdir -p "$WORK/bin"
+printf '#!/bin/sh\nexit 1\n' > "$WORK/bin/journalctl"; chmod +x "$WORK/bin/journalctl"
+OUT="$(PATH="$WORK/bin:$PATH" HOST_GUARD_RESET_KLOG_FILE="" bash "$RF" check 2>/dev/null)"
+assert_has   "check: silent journalctl → UNKNOWN, never CLEAN" "UNKNOWN|" "$OUT"
+assert_has   "check: UNKNOWN explains how to fix access"        "systemd-journal" "$OUT"
+
+echo ""
+echo "── B. postmortem bundle ────────────────────────────────────────────────"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" bash "$RF" ensure-postmortem)"
+assert_has "bundle: clean boot → NONE" "NONE|" "$OUT"
+[[ -d "$PM" && -n "$(ls -A "$PM" 2>/dev/null)" ]] \
+  && assert "bundle: NO-OP RULE — clean boot writes no file" fail \
+  || assert "bundle: NO-OP RULE — clean boot writes no file" pass
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" ensure-postmortem)"
+assert_has "bundle: fault → POSTMORTEM|…|new" "|new" "$OUT"
+BUNDLE="$PM/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3.md"
+[[ -f "$BUNDLE" ]] && assert "bundle: named after the dead boot" pass || assert "bundle: named after the dead boot" fail
+BODY="$(cat "$BUNDLE" 2>/dev/null)"
+
+assert_has "bundle: verbatim reset line"        "0x08000800" "$BODY"
+assert_has "bundle: boot history table"         "**FAULT**" "$BODY"
+assert_has "bundle: marks the planned reboot"   "| reboot |" "$BODY"
+assert_has "bundle: names both dead engines"    "$WORK/projA" "$BODY"
+assert_has "bundle: names the second project"   "$WORK/projB" "$BODY"
+assert_has "bundle: names the dead session"     "session_id=desk" "$BODY"
+assert_has "bundle: keeps the pump record too"  "kind=pump" "$BODY"
+assert_has "bundle: session telemetry tail"     '"event":"coherence_pass"' "$BODY"
+assert_has "bundle: engine log tail"            "UNIQUEMARKER_ENGINELOG" "$BODY"
+assert_has "bundle: session.json state"         '"status":"in_progress"' "$BODY"
+assert_has "bundle: points at the runbook"      "docs/host-guard.md" "$BODY"
+
+# The telemetry window must be BOOT-RELATIVE. A sampler that restarted after the
+# reboot keeps appending, and a plain `tail` would present live idle data as the
+# machine's dying breath.
+assert_has   "bundle: final pre-reset sample selected" "$(( BOOT_EPOCH - 75 ))" "$BODY"
+assert_lacks "bundle: post-reboot samples excluded"    "$(( BOOT_EPOCH + 5000 ))" "$BODY"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" ensure-postmortem)"
+assert_has "bundle: second run is idempotent" "|existing" "$OUT"
+BEFORE="$(stat -c %Y "$BUNDLE")"
+HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" ensure-postmortem >/dev/null
+assert_eq "bundle: existing bundle is not rewritten" "$BEFORE" "$(stat -c %Y "$BUNDLE")"
+[[ -L "$PM/latest.md" ]] && assert "bundle: latest.md points at the newest" pass || assert "bundle: latest.md points at the newest" fail
+assert_has "report: prints the bundle" "0x08000800" "$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" report 2>/dev/null)"
+
+echo ""
+echo "── C. doctor rows ──────────────────────────────────────────────────────"
+
+_doc() { # $1 check key — env overrides come from the caller's prefix
+  env CHAIN_DOCTOR_REPO_ROOT="$WORK/projA" bash "$DOCTOR" --only "$1" 2>&1
+}
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" _doc reset-reason)"
+assert_has "doctor: reset-reason FAILs after a hardware reset" "FAIL" "$OUT"
+assert_has "doctor: row carries the code"                      "0x08000800" "$OUT"
+assert_has "doctor: row points at the postmortem"              "$PM/" "$OUT"
+assert_lacks "doctor: row is one line (no crash wrapper)"      "check crashed" "$OUT"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" _doc reset-reason)"
+assert_has "doctor: clean boot PASSes" "PASS" "$OUT"
+
+# ras-logging must stay quiet on hosts that never had the incident, and must not
+# smuggle a newline into its row (systemctl prints AND exits non-zero).
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" CHAIN_DOCTOR_RAS_STATE=inactive \
+       CHAIN_DOCTOR_JOURNALD_DIR="$WORK/nojournald" _doc ras-logging)"
+assert_has   "doctor: ras-logging quiet without reset history" "PASS" "$OUT"
+assert_lacks "doctor: ras-logging never crashes the wrapper"   "check crashed" "$OUT"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" CHAIN_DOCTOR_RAS_STATE=inactive \
+       CHAIN_DOCTOR_JOURNALD_DIR="$WORK/nojournald" _doc ras-logging)"
+assert_has "doctor: ras-logging WARNs once the host has history" "WARN" "$OUT"
+assert_has "doctor: WARN names rasdaemon"                        "rasdaemon" "$OUT"
+
+mkdir -p "$WORK/journald.d"; printf '[Journal]\nSyncIntervalSec=15s\n' > "$WORK/journald.d/99-iad-sync.conf"
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" CHAIN_DOCTOR_RAS_STATE=active \
+       CHAIN_DOCTOR_JOURNALD_DIR="$WORK/journald.d" _doc ras-logging)"
+assert_has "doctor: ras-logging PASSes once both are in place" "PASS" "$OUT"
+
+assert_has "doctor: reset-reason is a registered check" "reset-reason" "$(bash "$DOCTOR" --list)"
+assert_has "doctor: ras-logging is a registered check"  "ras-logging"  "$(bash "$DOCTOR" --list)"
+
+echo ""
+echo "── D. engine wiring ────────────────────────────────────────────────────"
+
+RG="$ENGINE_ROOT/scripts/automation/run-goal.sh"
+grep -q '_host_guard_reset_forensics' "$RG" \
+  && assert "wiring: engine preflight reads the reset register" pass \
+  || assert "wiring: engine preflight reads the reset register" fail
+# Ordering is the whole point: hg_sweep deletes the records that say who was
+# running, so the postmortem has to be taken first.
+_fx="$(grep -n '^[[:space:]]*_host_guard_reset_forensics[[:space:]]*$' "$RG" | head -n 1 | cut -d: -f1)"
+_sw="$(grep -n '^[[:space:]]*hg_sweep[[:space:]]*$' "$RG" | head -n 1 | cut -d: -f1)"
+if [[ -n "$_fx" && -n "$_sw" ]] && (( _fx < _sw )); then
+  assert "wiring: forensics runs BEFORE the registry sweep" pass
+else
+  assert "wiring: forensics runs BEFORE the registry sweep" fail
+fi
+grep -q 'machine_reset' "$RG" \
+  && assert "wiring: resume reports a reset-killed session" pass \
+  || assert "wiring: resume reports a reset-killed session" fail
+grep -q 'GOAL_SESSION_DIR="$GOAL_SESSION_DIR_LOCAL" GOAL_SESSION_ID="$SESSION_ID" \\' "$RG" \
+  && assert "wiring: resume event carries its own session context" pass \
+  || assert "wiring: resume event carries its own session context" fail
+grep -q 'hg_event engine_start' "$RG" \
+  && assert "wiring: engine start is ledgered" pass || assert "wiring: engine start is ledgered" fail
+grep -q 'hg_event aggregate_ok' "$RG" \
+  && assert "wiring: the HEALTHY aggregate verdict is ledgered too" pass \
+  || assert "wiring: the HEALTHY aggregate verdict is ledgered too" fail
+QR="$ENGINE_ROOT/scripts/automation/lib/quota-retry.sh"
+grep -q 'hg_event dispatch_start' "$QR" && grep -q 'hg_event dispatch_end' "$QR" \
+  && assert "wiring: every agent dispatch is bracketed in the ledger" pass \
+  || assert "wiring: every agent dispatch is bracketed in the ledger" fail
+grep -q 'iad-hwmon.service' "$ENGINE_ROOT/docs/host-guard.md" 2>/dev/null \
+  && assert "wiring: the machine-global sampler unit is documented" pass \
+  || assert "wiring: the machine-global sampler unit is documented" fail
+
+echo ""
+echo "──────────────────────────────────────────────────────────────────────"
+echo "  PASS: $PASS   FAIL: $FAIL"
+[[ "$FAIL" -eq 0 ]]
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
index 4840e86f..d7baecb4 100644
--- a/project-extensions/host-guard/host-guard.env
+++ b/project-extensions/host-guard/host-guard.env
@@ -1,14 +1,24 @@
 # host-guard.env — per-host resource ceilings for the AI dev chain (goal.md AG-10).
 #
 # WHY THIS EXISTS: this host (GEEKOM A7 Max mini-PC, Ryzen 9 7940HS, 27 GB RAM)
-# hard-reset instantly — no OOM, no thermal log, no kernel panic — twice in two
-# days (2026-07-20 19:17, 2026-07-21 10:33), both times mid all-core vectorized
-# ingest bursts from goal-mode iterations (iter-5 measurement passes, iter-8
-# heavy-backfill baseline). Diagnosis: power/VRM/thermal transient trip in the
-# mini-PC hardware — the earlier sustained-load pytest era (8-day uptime) never
-# tripped it. These caps flatten the transient (fewer simultaneously-lit AVX
-# cores) and bound aggregate memory. Incident details + runbooks: README.md
-# next to this file; contract: docs/goal.md AG-10 + the host-guard binding note.
+# hard-reset instantly — no OOM, no thermal log, no kernel panic — seven times
+# between 2026-07-20 and 2026-07-30, often during goal-mode iterations.
+#
+# ROOT CAUSE, SETTLED 2026-07-30: it is HARDWARE, and the CPU had been naming it
+# on every boot — "x86/amd: Previous system reset reason [0x08000800]: an
+# uncorrected error caused a data fabric sync flood event", on 7 of the last 10
+# boots, once at load 1.53 and 22 W. An uncorrectable SoC/Infinity-Fabric error
+# resets the machine with the OS never notified, so NO cap in this file can
+# prevent it. Reset #7 settled it: it happened with every mitigation in force
+# and green, while this project ran memory drills at 26-37 W and 65-74 °C.
+#
+# The original diagnosis here — a "power/VRM/thermal transient" flattened by
+# lighting fewer AVX cores — was wrong, and the mask it justified was released
+# on 2026-07-30 (see below). These caps still bound memory and fork storms and
+# keep the forensics armed; the real fix is firmware/DRAM and belongs to the
+# operator: incredible_auto_dev/docs/host-guard.md § After a hardware reset.
+# Incident details + runbooks: README.md next to this file; contract:
+# docs/goal.md AG-10 + the host-guard binding note.
 #
 # CONTRACT: plain KEY=VALUE bash assignments only — this file is `source`d by
 # run-goal.sh, hwmon-log.sh, and (once the launcher caps land) scripts/dev.sh /
@@ -19,26 +29,28 @@
 # Master switch for all host-guard behavior (engine wrap, preflight, launcher caps).
 HOST_GUARD_ENABLED=1
 
-# SMT-AWARE CPU affinity mask for heavy work (engine tree + backends).
-# 7940HS sibling pairs are (0,8)(1,9)...(7,15): "0-3,8-11" = 4 physical cores
-# with both their SMT threads = 8 schedulable CPUs but ~half the simultaneously
-# AVX-lit core current — the actual reset trigger. Widen ONE notch at a time
-# ("0-5,8-13") only after a green verification ladder (README).
-# 2026-07-29: unchanged here, but tapeology moved from its complementary
-# "4-7,12-15" ONTO this same mask. Complementary masks caused reset #6 — each
-# project passed its own check while their union lit all 16 CPUs. Both projects
-# now share this mask, and it must stay a subset of HOST_GUARD_GLOBAL_CPU_LIST
-# in ~/.config/iad/host-guard-host.env (the engine pauses otherwise).
-HOST_GUARD_CPU_LIST="0-3,8-11"
+# CPU affinity mask for heavy work (engine tree + backends).
+# RELEASED TO THE WHOLE MACHINE 2026-07-30 (was "0-3,8-11"). That mask existed
+# to halve "simultaneously AVX-lit core current", described here as "the actual
+# reset trigger" — it was not. Reset #7 happened with the mask in force at
+# 26-37 W and 65-74 °C on a 35-54 W part; the fault is an uncorrected data
+# fabric error that no affinity mask can reach. The cap-widening ladder in
+# README.md is therefore moot for this knob.
+# Must remain a subset of HOST_GUARD_GLOBAL_CPU_LIST in
+# ~/.config/iad/host-guard-host.env — the engine pauses otherwise, so widen the
+# machine budget FIRST. Concurrency is now bounded by HOST_GUARD_MAX_ENGINES
+# there instead: how long the box is under load, not which cores carry it.
+HOST_GUARD_CPU_LIST="0-15"
 
 # BLAS/OpenMP/numexpr worker cap: one per physical core in the mask, so N
 # numpy processes cannot oversubscribe the mask with nested thread pools.
-HOST_GUARD_BLAS_THREADS=4
+HOST_GUARD_BLAS_THREADS=8
 
-# systemd user-scope backstops (engine wrap only; skipped when no user bus).
-# CPUQuota averages over ~100 ms so it CANNOT stop the sub-100 ms transient —
-# the taskset mask above is the real limiter; this catches sustained overshoot.
-HOST_GUARD_CPUQUOTA="800%"
+# systemd user-scope backstop (engine wrap only; skipped when no user bus).
+# Raised with the mask on 2026-07-30 (was 800%): a quota below the mask width
+# would silently re-impose the cap the mask no longer applies. This bounds
+# sustained overshoot only — it never had anything to do with the reset.
+HOST_GUARD_CPUQUOTA="1600%"
 # Aggregate memory ceiling for the whole engine tree (reclaim+throttle, never
 # OOM-kill). 18G solo → 14G on 2026-07-28 → 10G on 2026-07-29: 14G + 14G = 28G
 # was still OVER the 27.3G installed, and nothing checked the sum. 10G + 10G =
diff --git a/apps/backend/app/logging_config.py b/apps/backend/app/logging_config.py
new file mode 100644
index 00000000..e602e160
--- /dev/null
+++ b/apps/backend/app/logging_config.py
@@ -0,0 +1,78 @@
+"""Root-logger configuration for the Trendora backend (ops-hardening iter-39).
+
+Before this module existed, the app never called `logging.basicConfig` / added any handler
+anywhere (confirmed live, iter-38: a direct read of `apps/backend/main.py` showed only bare
+`logging.getLogger(...)` calls, no handler/level setup anywhere in the app). Every `trendora.*`
+logger (created via `logging.getLogger("trendora.xxx")`) therefore had no handler anywhere in
+its propagation chain up to the root logger, so Python's global `logging.lastResort` fallback
+(a `StreamHandler(sys.stderr)` PINNED to WARNING — see the stdlib `logging` module) was the ONLY
+thing ever writing those records anywhere. That is why routine `.info()` liveness lines were
+silently dropped: an `.info`-level version of the J-07 finalize-tail `cache_ctx` liveness line
+(`data_manager.py`, `_refresh_ingest_aggregates`) never once appeared in `logs/backend.log`
+across a full drilled job, forcing it to masquerade as `.warning` instead (iter-38 workaround).
+
+`configure_app_logging()` attaches one `StreamHandler` to the ROOT logger at INFO level.
+`scripts/start-backend.sh` already redirects the launched process's stdout+stderr into
+`logs/backend.log` (`>> "$LOG_FILE" 2>&1`), so this module decides ONLY the level/handler —
+never a destination file path — and every `trendora.*` `.info()`+ call now reaches that same
+persistent logfile with no further wiring. Idempotent (a second call is a no-op) so importing
+this module more than once, or under pytest's own logging setup, never doubles output or
+clobbers a caller's own root-logger configuration.
+
+CORRECTION (iter-39 audit, B1): the paragraph above overstated "no handler anywhere" — it was
+established by reading `main.py` alone. TWO modules DO attach a handler to their own logger and
+have since iter-18: `app/api/backtest.py` (`trendora.backtest`) and `app/mcp/tools.py`
+(`trendora.mcp_backtest`), each deliberately keeping `propagate = True` so `caplog`-based tests
+still observe their records. Those loggers were therefore never affected by the `lastResort`
+gap — and once a root handler exists, their records reach BOTH handlers, so every
+`backtest_timing` / `query_backtest_timing` line was written to `logs/backend.log` TWICE
+(confirmed live in this repo's own log: one bare copy from the module handler, one formatted
+copy from the root handler, same millisecond). `_already_handled_by_own_logger` below suppresses
+the root handler's duplicate copy, so a logger that carries its own handler keeps exactly its
+pre-existing single line (bare format, unchanged for every existing consumer/grep of it) while
+every other `trendora.*` logger gains the INFO-level output this module was added to provide."""
+from __future__ import annotations
+
+import logging
+
+_CONFIGURED = False
+
+
+def _already_handled_by_own_logger(record: logging.LogRecord) -> bool:
+    """True when `record` was already emitted by a handler attached to its own logger (or to an
+    ancestor below the root) — in which case this module's root handler must NOT emit a second
+    copy. Walks the propagation chain the same way `logging.Logger.callHandlers` does, stopping
+    before the root logger itself."""
+    logger = logging.getLogger(record.name)
+    while logger is not None and logger.parent is not None:  # stop before the root logger
+        if logger.handlers:
+            return True
+        if not logger.propagate:
+            return False
+        logger = logger.parent
+    return False
+
+
+def configure_app_logging(level: int = logging.INFO) -> None:
+    """Idempotently attach a root-logger `StreamHandler` at `level` so every `trendora.*`
+    logger's calls at `level`+ reach the process's stderr (and therefore `logs/backend.log`
+    under the launch scripts) instead of being silently dropped by Python's WARNING-only
+    `logging.lastResort` fallback. Safe to call more than once (e.g. re-imported under a test
+    runner) — only the FIRST call has any effect."""
+    global _CONFIGURED
+    if _CONFIGURED:
+        return
+    root = logging.getLogger()
+    # widen the root logger's own level only if it would otherwise filter OUT this handler's
+    # level (a root at the default WARNING would swallow INFO records before they ever reach
+    # the handler below) — never narrow it past what a caller may have already configured.
+    if root.level == logging.NOTSET or root.level > level:
+        root.setLevel(level)
+    handler = logging.StreamHandler()
+    handler.setLevel(level)
+    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
+    # iter-39 audit (B1): never double-write a record a logger's OWN handler already emitted
+    # (`trendora.backtest`, `trendora.mcp_backtest` — see the module docstring's CORRECTION).
+    handler.addFilter(lambda record: not _already_handled_by_own_logger(record))
+    root.addHandler(handler)
+    _CONFIGURED = True
diff --git a/apps/backend/tests/test_ingest_finalize_fault_injection.py b/apps/backend/tests/test_ingest_finalize_fault_injection.py
new file mode 100644
index 00000000..751bc0c5
--- /dev/null
+++ b/apps/backend/tests/test_ingest_finalize_fault_injection.py
@@ -0,0 +1,216 @@
+"""ops-hardening iter-39 FIX PASS (audit finding B3 / J-07 step 4) — DETERMINISTIC proof that the two
+NAMED per-item `MemoryError` isolation handlers inside the ingest finalize hook's aggregate-warm loops
+actually fire, abort only their OWN loop, and leave `_refresh_ingest_aggregates` returning normally.
+
+WHY THIS EXISTS ALONGSIDE `test_ingest_finalize_memory_pressure.py`:
+that module induces a REAL, non-monkeypatched `MemoryError` under a genuine `ulimit -v` cap and is the
+stronger proof for the mechanism it covers (`forward_aggregates`). What it cannot do — and what three
+live calibration trials at 3420 / 2700 / 2650 MB this iteration also could not do (audit B3) — is reach
+those handlers inside a LIVE server process: `_missing_data_diagnostic`'s whole-`daily_prices`
+materialization runs EARLIER in the same finalize sequence, so any cap tight enough to threaten the
+target loops exhausts the budget upstream first. Chasing that cap further is the wrong-direction pattern
+in `.claude/judgment-rubrics.md` §4; J-07 step 4's own text sanctions the alternative verbatim ("Induce
+memory pressure during a warm (TEST HOOK or a tightened cap in a throwaway process)").
+
+So these tests drive `data_manager._fault_inject_memory_error` — the env-gated, test-only injector — at
+the EXACT call sites the acceptance clause names, and assert WHICH stage aborted from a direct read of
+that stage's own distinctive log line (never inferred from "a `MemoryError` fired somewhere" — the
+binding iter-37/38 lesson). Every test carries its own control arm so a silently-disabled injector shows
+up as a failure rather than a green pass.
+"""
+from __future__ import annotations
+
+import logging
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlmodel import Session
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine import data_manager, forward_testing
+from app.engine.data_manager import JobProgress
+from app.models import ScannerRun
+
+ASOF = date(2020, 1, 2)
+FAULT_ENV = data_manager._FAULT_INJECT_MEMORY_ERROR_ENV
+# The two distinctive per-item abort log lines (`data_manager.py`) whose handlers J-07's acceptance names.
+FORWARD_AGGREGATES_ABORT = "ingest forward-aggregate warm aborted at horizon"
+DRAWDOWN_ABORT = "ingest drawdown-expectations warm aborted"
+
+
+@pytest.fixture()
+def finalize_session(tmp_path):
+    """The smallest DB `_refresh_ingest_aggregates` needs to REACH both target loops: one `ScannerRun`, so
+    `scanner._latest_stored_run_date()` is non-None and the per-horizon forward-aggregate loop runs. No
+    price/result/return rows — the injection fires BEFORE any compute, so the loop's real cost is
+    irrelevant to what is being proven here (that the handler catches, isolates, and returns honestly)."""
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_fault.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(ScannerRun(
+            asof_date=ASOF, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label=cfg.regime.labels[0], regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+    with Session(engine) as session:
+        yield session, cfg
+
+
+def _spy_release(monkeypatch) -> list[str]:
+    """Record every `_release_process_memory()` call — the second half of the iter-8 isolation convention
+    (stop the loop AND force freed memory back to the OS before moving on)."""
+    calls: list[str] = []
+    real = data_manager._release_process_memory
+
+    def _spy() -> None:
+        calls.append("released")
+        real()
+
+    monkeypatch.setattr(data_manager, "_release_process_memory", _spy)
+    return calls
+
+
+def _one_claim_ledger(monkeypatch) -> None:
+    """Give the drawdown-expectations loop exactly ONE claim to iterate, deterministically — the loop is
+    a no-op on an empty ledger, and the committed ledger's contents are not this test's subject."""
+    monkeypatch.setattr(
+        data_manager, "read_entries",
+        lambda _path: [{"type": "claim", "claim": {"signal": "fault-injection-probe", "horizon": 21}}],
+    )
+
+
+# ==================================================================================================
+# TC-1 — the NAMED forward-aggregate per-horizon handler (`data_manager.py`, iter-8 convention)
+# ==================================================================================================
+def test_forward_aggregate_warm_memory_error_is_caught_isolated_and_named(
+    finalize_session, monkeypatch, caplog
+):
+    """TC-1: a `MemoryError` raised at the per-horizon forward-aggregate call site is caught by THAT
+    loop's own `except MemoryError` — proven by its distinctive log line naming the horizon, not by a bare
+    "a MemoryError happened". The category is honestly ABSENT from the refreshed list, the loop stops at
+    the first horizon (never hammering the next allocation), `_release_process_memory()` runs, the function
+    itself never raises, and the LATER aggregate categories still execute (the abort is isolated to this
+    ONE loop, which is the whole point of the per-item convention)."""
+    session, cfg = finalize_session
+    release_calls = _spy_release(monkeypatch)
+    _one_claim_ledger(monkeypatch)
+
+    # Load-bearing isolation probe: did a LATER category still get a chance to run after the abort?
+    later_calls: list[str] = []
+    monkeypatch.setattr(
+        forward_testing, "compute_drawdown_expectations_cached",
+        lambda *_a, **_k: later_calls.append("called") or None,
+    )
+    horizon_calls: list[int] = []
+    monkeypatch.setattr(
+        forward_testing, "forward_aggregates_ingest_cached",
+        lambda *_a, **_k: horizon_calls.append(1),
+    )
+
+    monkeypatch.setenv(FAULT_ENV, "forward_aggregates")
+    prog = JobProgress(job_id="fi-fwd-agg", kind="backfill", start=ASOF, end=ASOF)
+    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise
+
+    assert FORWARD_AGGREGATES_ABORT in caplog.text, (
+        "the forward-aggregate loop's OWN per-horizon MemoryError handler must be the one that fired — "
+        f"its distinctive log line is absent; captured log was:\n{caplog.text}"
+    )
+    assert "forward_aggregates" not in refreshed, (
+        f"an aborted warm must be honestly absent from the refreshed categories; refreshed={refreshed}"
+    )
+    assert horizon_calls == [], (
+        "the injection fires BEFORE the real warm call, and the loop must stop at the first MemoryError — "
+        f"the real per-horizon compute must never have been invoked; calls={horizon_calls}"
+    )
+    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"
+    assert later_calls, (
+        "the abort must be isolated to the forward-aggregate loop — a LATER aggregate category "
+        "(drawdown-expectations) still had to run; it never did"
+    )
+
+
+def test_forward_aggregate_control_no_injection_completes_and_logs_no_abort(
+    finalize_session, monkeypatch, caplog
+):
+    """Control for the test above (so a silently-disabled injector cannot pass as a green result): the
+    IDENTICAL call with the env var UNSET logs NO forward-aggregate abort line and reports the category as
+    refreshed. If this control ever fails, the tight-arm result above cannot be trusted."""
+    session, cfg = finalize_session
+    monkeypatch.delenv(FAULT_ENV, raising=False)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", lambda *_a, **_k: None)
+
+    prog = JobProgress(job_id="fi-fwd-agg-control", kind="backfill", start=ASOF, end=ASOF)
+    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert FORWARD_AGGREGATES_ABORT not in caplog.text, (
+        f"no injection was configured, so no abort may fire; captured log was:\n{caplog.text}"
+    )
+    assert "forward_aggregates" in refreshed, f"expected a normal warm without injection; refreshed={refreshed}"
+
+
+# ==================================================================================================
+# TC-1 (second named handler) — the per-claim drawdown-expectations loop
+# ==================================================================================================
+def test_drawdown_expectations_warm_memory_error_is_caught_isolated_and_named(
+    finalize_session, monkeypatch, caplog
+):
+    """The SECOND per-item handler J-07's acceptance names (`data_manager.py`, per-claim drawdown
+    expectations): an injected `MemoryError` is caught by that loop's own `except MemoryError`, proven by
+    ITS distinctive log line — distinct from the forward-aggregate one, so the assertion cannot pass on
+    the wrong stage aborting. The category is honestly absent, `_release_process_memory()` runs, and
+    `_refresh_ingest_aggregates` returns normally."""
+    session, cfg = finalize_session
+    release_calls = _spy_release(monkeypatch)
+    _one_claim_ledger(monkeypatch)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", lambda *_a, **_k: None)
+    claim_calls: list[str] = []
+    monkeypatch.setattr(
+        forward_testing, "compute_drawdown_expectations_cached",
+        lambda *_a, **_k: claim_calls.append("called") or None,
+    )
+
+    monkeypatch.setenv(FAULT_ENV, "drawdown_expectations")
+    prog = JobProgress(job_id="fi-drawdown", kind="backfill", start=ASOF, end=ASOF)
+    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise
+
+    assert DRAWDOWN_ABORT in caplog.text, (
+        "the per-claim drawdown-expectations loop's OWN MemoryError handler must be the one that fired; "
+        f"captured log was:\n{caplog.text}"
+    )
+    assert FORWARD_AGGREGATES_ABORT not in caplog.text, (
+        "only the TARGETED stage may abort — the forward-aggregate loop must have completed normally"
+    )
+    assert "forward_aggregates" in refreshed, (
+        "the earlier, un-targeted category must still be refreshed (per-item isolation, not a cascade); "
+        f"refreshed={refreshed}"
+    )
+    assert "drawdown_expectations" not in refreshed, f"aborted category must be absent; refreshed={refreshed}"
+    assert claim_calls == [], f"the loop must stop before the real per-claim compute; calls={claim_calls}"
+    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"
+
+
+# ==================================================================================================
+# Injector contract — an unrecognized site name must NOT silently look like a configured drill
+# ==================================================================================================
+def test_unknown_fault_injection_site_is_ignored(monkeypatch):
+    """A typo'd site name injects nothing. Without this, a mistyped drill env var would produce a clean
+    run that reads exactly like "the handler was never needed" instead of "the drill never armed"."""
+    monkeypatch.setenv(FAULT_ENV, "forward_aggregates")
+    with pytest.raises(MemoryError):
+        data_manager._fault_inject_memory_error("forward_aggregates")
+    data_manager._fault_inject_memory_error("forwardaggregates")  # typo — recognized site list gates it
+    data_manager._fault_inject_memory_error("drawdown_expectations")  # armed site is a different one
+
+
+def test_fault_injection_is_a_no_op_when_env_is_unset(monkeypatch):
+    """The production contract: with the env var absent, EVERY known site is a no-op — the hook adds no
+    behavior to any real deployment."""
+    monkeypatch.delenv(FAULT_ENV, raising=False)
+    for site in sorted(data_manager._FAULT_INJECT_SITES):
+        data_manager._fault_inject_memory_error(site)  # must not raise
diff --git a/apps/backend/tests/test_logging_config.py b/apps/backend/tests/test_logging_config.py
new file mode 100644
index 00000000..bf833c2d
--- /dev/null
+++ b/apps/backend/tests/test_logging_config.py
@@ -0,0 +1,114 @@
+"""TC-12 (ops-hardening iter-39) — `app.logging_config.configure_app_logging()` actually gets an
+`.info()`-level record from a `trendora.*` logger to a configured handler, closing the gap iter-38
+discovered live: with no root-logger handler/level configured anywhere in the app, Python's global
+WARNING-only `logging.lastResort` fallback was the only thing ever writing these records, so an
+`.info()` call was silently dropped before it ever reached `logs/backend.log`."""
+from __future__ import annotations
+
+import io
+import logging
+import sys
+
+from app import logging_config
+
+
+def test_configure_app_logging_lets_info_reach_configured_handler(monkeypatch):
+    root = logging.getLogger()
+    saved_handlers = list(root.handlers)
+    saved_level = root.level
+    for h in saved_handlers:
+        root.removeHandler(h)
+    # mirror the real pre-fix starting point: an unconfigured root sits at the module default
+    # (WARNING) with zero handlers of its own.
+    root.setLevel(logging.WARNING)
+
+    stream = io.StringIO()
+    monkeypatch.setattr(sys, "stderr", stream)
+    # force a fresh configure even if some earlier test/import already ran it this session.
+    monkeypatch.setattr(logging_config, "_CONFIGURED", False)
+    try:
+        logging_config.configure_app_logging()
+
+        probe = logging.getLogger("trendora.test_logging_config")
+        probe.info("TC-12 probe line: %s", "hello")
+
+        assert "TC-12 probe line: hello" in stream.getvalue(), (
+            "an .info() call on a trendora.* logger did not reach the handler "
+            "configure_app_logging() is supposed to attach"
+        )
+    finally:
+        for h in list(root.handlers):
+            root.removeHandler(h)
+        for h in saved_handlers:
+            root.addHandler(h)
+        root.setLevel(saved_level)
+
+
+def test_configure_app_logging_does_not_double_write_self_handled_loggers(monkeypatch):
+    """iter-39 audit (B1) regression — `trendora.backtest` and `trendora.mcp_backtest` attach a
+    handler to their OWN logger (iter-18) and keep `propagate = True` for caplog. Once a root
+    handler exists, an unfiltered root handler emits a SECOND copy of each of their records: every
+    `backtest_timing` line was written to `logs/backend.log` twice (confirmed live). A logger that
+    carries its own handler must keep exactly ONE line; a logger without one must still get the
+    root handler's copy."""
+    root = logging.getLogger()
+    saved_handlers = list(root.handlers)
+    saved_level = root.level
+    for h in saved_handlers:
+        root.removeHandler(h)
+    root.setLevel(logging.WARNING)
+
+    root_stream = io.StringIO()
+    own_stream = io.StringIO()
+    monkeypatch.setattr(sys, "stderr", root_stream)
+    monkeypatch.setattr(logging_config, "_CONFIGURED", False)
+
+    # mirror app/api/backtest.py's real shape: own handler + level, propagate left True.
+    self_handled = logging.getLogger("trendora.test_self_handled")
+    self_handled.setLevel(logging.INFO)
+    own_handler = logging.StreamHandler(own_stream)
+    self_handled.addHandler(own_handler)
+    try:
+        logging_config.configure_app_logging()
+
+        self_handled.info("timing_probe one")
+        assert own_stream.getvalue().count("timing_probe one") == 1, "the logger's own handler must still emit"
+        assert "timing_probe one" not in root_stream.getvalue(), (
+            "the root handler emitted a SECOND copy of a record its own logger already handled — "
+            "this is the duplicate-line regression B1 found live in logs/backend.log"
+        )
+
+        # a logger WITHOUT its own handler must still reach the root handler.
+        logging.getLogger("trendora.test_plain").info("plain_probe two")
+        assert "plain_probe two" in root_stream.getvalue()
+    finally:
+        self_handled.removeHandler(own_handler)
+        self_handled.setLevel(logging.NOTSET)
+        for h in list(root.handlers):
+            root.removeHandler(h)
+        for h in saved_handlers:
+            root.addHandler(h)
+        root.setLevel(saved_level)
+
+
+def test_configure_app_logging_is_idempotent(monkeypatch):
+    """A second call must not attach a second handler (which would double-emit every record)."""
+    root = logging.getLogger()
+    saved_handlers = list(root.handlers)
+    saved_level = root.level
+    for h in saved_handlers:
+        root.removeHandler(h)
+    root.setLevel(logging.WARNING)
+
+    monkeypatch.setattr(logging_config, "_CONFIGURED", False)
+    try:
+        logging_config.configure_app_logging()
+        count_after_first = len(root.handlers)
+        logging_config.configure_app_logging()
+        assert len(root.handlers) == count_after_first, "a second call must be a no-op (idempotent)"
+    finally:
+        for h in list(root.handlers):
+            root.removeHandler(h)
+        for h in saved_handlers:
+            root.addHandler(h)
+        root.setLevel(saved_level)
```
