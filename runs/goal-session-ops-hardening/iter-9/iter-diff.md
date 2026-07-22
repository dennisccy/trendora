# Iteration diff (bounded)

Files changed: 6. Shown in full: 5.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_start_backend_script.py` (260 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 0612d34a..b38e047f 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1943,6 +1943,10 @@ class JobProgress:
     # concurrency the pool used (min(config workers, target dates)).
     _backfill_per_date_seconds_sum: float = 0.0
     _backfill_concurrency: int = 0
+    # ops-hardening iter-9 (F1 / J-04 step 6) — `time.monotonic()` of the last durable progress checkpoint
+    # written onto this job's OPEN run-history row (NOT serialized — internal throttle scratch, like the
+    # two accumulators above). 0.0 means "never checkpointed", so the first advance always writes.
+    _last_checkpoint_monotonic: float = 0.0
 
     def tick(self, activity: Optional[str] = None) -> None:
         """J-66 — stamp the last-progress HEARTBEAT (and optionally the current-activity line) on a
@@ -2725,6 +2729,28 @@ def _cleanup_orphan_run(session: Session, d: date_cls) -> None:
         session.rollback()
 
 
+_libc_malloc_trim_cache: dict = {}
+
+
+def _resolve_libc_malloc_trim():
+    """ops-hardening iter-9 (B2) — resolve the libc `malloc_trim` handle AT MOST ONCE per process
+    (module-level, first-call-cached), instead of re-running `ctypes.util.find_library` +
+    `ctypes.CDLL` — each its own library-resolution fork/exec on some platforms — on EVERY
+    `_release_process_memory()` call. This matters most on the exact memory-pressure path this session
+    hardened: a warm loop's `MemoryError`-abort calls `_release_process_memory()` once per aborted loop,
+    so a single heavy ingest can invoke it several times. Caches a permanent resolution FAILURE too
+    (non-glibc / symbol absent) so it is never retried either. Returns the cached `libc.malloc_trim`
+    callable, or `None` when unavailable."""
+    if "fn" not in _libc_malloc_trim_cache:
+        try:
+            libc_name = ctypes.util.find_library("c") or "libc.so.6"
+            libc = ctypes.CDLL(libc_name)
+            _libc_malloc_trim_cache["fn"] = libc.malloc_trim
+        except (OSError, AttributeError):  # non-glibc / symbol absent
+            _libc_malloc_trim_cache["fn"] = None
+    return _libc_malloc_trim_cache["fn"]
+
+
 def _release_process_memory() -> None:
     """iter-27 (J-16, anti-goal #8) — after a heavy full-universe backfill/rebuild stage finishes, return
     the just-freed memory to the OS so a SECOND consecutive full-universe rebuild in the SAME long-lived
@@ -2745,14 +2771,18 @@ def _release_process_memory() -> None:
     the start script exports (which bounds how many independently-fragmenting arenas glibc creates across the
     server's worker threads on a many-core host — the dominant VSZ lever), consecutive rebuilds stay under
     the cap with margin. `malloc_trim` is glibc-only; on any other libc the `gc.collect()` still runs and the
-    trim is silently skipped."""
+    trim is silently skipped.
+
+    ops-hardening iter-9 (B2): the libc handle resolution itself is memoized by `_resolve_libc_malloc_trim`
+    (module-level, first-call-cached) — this function's own `gc.collect()` + `malloc_trim(0)` timing and
+    effect are unchanged; only the redundant repeated resolution is removed."""
     gc.collect()
-    try:
-        libc_name = ctypes.util.find_library("c") or "libc.so.6"
-        libc = ctypes.CDLL(libc_name)
-        libc.malloc_trim(0)  # glibc: return free heap/arena pages to the OS (no-op elsewhere)
-    except (OSError, AttributeError):  # non-glibc / symbol absent — gc.collect() above already ran
-        pass
+    malloc_trim = _resolve_libc_malloc_trim()
+    if malloc_trim is not None:
+        try:
+            malloc_trim(0)  # glibc: return free heap/arena pages to the OS (no-op elsewhere)
+        except OSError:  # defensive — a resolved-but-failing call still must never mask the caller
+            pass
 
 
 def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engine) -> None:
@@ -2839,6 +2869,16 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
         prog.error_other = prog.date_failures_total  # 0 — no per-date attempt was made
         return
 
+    # ops-hardening iter-9 AUDIT (F1 completion / J-04 step 6): checkpoint the PLAN the moment it is
+    # known — BEFORE the shared bar-cache prefill below, which on the deep basis runs for minutes. The
+    # per-date checkpoint in `_persist_isolated` only starts writing once the FIRST date has been
+    # persisted, so a process killed during the prefill window would otherwise still leave the very
+    # "0 snapshots · 0 trading days in range" row this fix exists to remove. This one write makes the
+    # honest range/plan (`calendar_days`/`dates_total`/`non_trading_days`/`already_snapshotted`) durable
+    # from the start; the counts it carries are the ones this function just computed — no second
+    # derivation, same throttled writer, same open row.
+    _checkpoint_run_record(eng, prog)
+
     def _persist(d: date_cls, payload: Optional[dict], per_date_seconds: float) -> None:
         """Apply ONE date's result on the orchestrating thread (serial, in date order): persist the
         snapshot (or read the existing one — create-once) then INSERT its forward returns. The ONLY
@@ -2911,13 +2951,18 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
         if compute_error is not None:
             prog._backfill_per_date_seconds_sum += secs
             _record_date_failure(prog, d, compute_error)
-            return
-        try:
-            _persist(d, payload, secs)
-        except Exception as exc:  # noqa: BLE001 — isolate this date; the stage continues
-            # the per-date write session (owned inside `_persist`) is already rolled back + closed by its
-            # `with` block; the shared orchestrating session is left untouched (never rolled back post-commit).
-            _record_date_failure(prog, d, str(exc))
+        else:
+            try:
+                _persist(d, payload, secs)
+            except Exception as exc:  # noqa: BLE001 — isolate this date; the stage continues
+                # the per-date write session (owned inside `_persist`) is already rolled back + closed by
+                # its `with` block; the shared orchestrating session is left untouched (never rolled back
+                # post-commit).
+                _record_date_failure(prog, d, str(exc))
+        # ops-hardening iter-9 (F1 / J-04 step 6): freeze this date's progress onto the job's OPEN
+        # run-history row (throttled — see `_checkpoint_run_record`), so a process killed mid-backfill
+        # leaves an `interrupted` row carrying the progress it really reached instead of zeros.
+        _checkpoint_run_record(eng, prog)
 
     # J-46/J-53: pre-fill ONE shared bar cache on the orchestrating session (every symbol's full series
     # loaded ONCE in one query). Workers ATTACH this same cache (read-only) so the whole K-date job does
@@ -3623,6 +3668,50 @@ def _has_open_run_record(engine: Engine, job_id: Optional[str]) -> bool:
         return _open_run_record(session, job_id) is not None
 
 
+# ops-hardening iter-9 (F1) — how often a long-running backfill re-writes its CURRENT progress onto its
+# OPEN run-history row. One small UPDATE per interval bounds the write amplification regardless of how
+# fast dates complete, while keeping a killed job's persisted progress at most one interval stale.
+_RUN_RECORD_CHECKPOINT_INTERVAL_S = 10.0
+
+
+def _checkpoint_run_record(engine: Engine, prog: JobProgress) -> None:
+    """ops-hardening iter-9 (F1 — J-04 step 6): freeze the job's CURRENT progress onto its OPEN
+    (`running`/`resumable`) run-history row, so a process that dies mid-run leaves an `interrupted` row
+    carrying its LAST PERSISTED PROGRESS.
+
+    Why this exists: the numeric detail fields were previously written into the persisted row exactly
+    ONCE, by `_finalize_run_record` — which a `kill -9`/host reset never reaches. The boot sweep
+    (`sweep_orphaned_runs`) only flips `status`/`finished_at` and never touches `message`, so an
+    interrupted row's detail stayed at its creation-time defaults and rendered as "0 snapshots · 0 trading
+    days in range" no matter how far the job actually got (live-verified: J-04 step 6 / UT-10).
+
+    Contract: this writes ONLY `message` (the detail JSON `_finalize_run_record` and `_create_run_record`
+    already serialize — one representation, no second derivation). It never sets `status`/`finished_at`,
+    so the row stays OPEN and the boot sweep can still claim it, and it never INSERTs — a job with no open
+    row (already terminal) is a silent no-op. Throttled to one write per
+    `_RUN_RECORD_CHECKPOINT_INTERVAL_S`. Best-effort telemetry: a write failure is logged and swallowed,
+    never propagated into the backfill loop (the job's own outcome must not depend on its progress
+    bookkeeping)."""
+    now = time.monotonic()
+    if (now - prog._last_checkpoint_monotonic) < _RUN_RECORD_CHECKPOINT_INTERVAL_S:
+        return
+    prog._last_checkpoint_monotonic = now
+    # Keep the breakdown internally consistent at the checkpoint instant: `error_other` is derived from
+    # the SAME uncapped `date_failures_total` the end of `_do_backfill` uses (one derivation, applied
+    # earlier), so a checkpointed row never shows failures in its summary and 0 in its breakdown.
+    prog.error_other = prog.date_failures_total
+    try:
+        with Session(engine) as session:
+            row = _open_run_record(session, prog.job_id)
+            if row is None:
+                return
+            row.message = json.dumps(_run_detail(prog))
+            session.add(row)
+            session.commit()
+    except Exception as exc:  # noqa: BLE001 — progress bookkeeping must never fail the job
+        logger.warning("run-record progress checkpoint failed for job %s (non-fatal): %s", prog.job_id, exc)
+
+
 def _finalize_run_record(engine: Engine, cfg: Config, prog: JobProgress) -> None:
     """J-60 — close the job's run-history record with ONE honest transition. UPDATEs the OPEN (running/
     resumable) row this job runs under (found by `job_id`) to its new status / finished_at / counts /
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index e39932b0..40fabd10 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1822,6 +1822,76 @@ def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises_non_memo
     assert "drawdown_expectations" in refreshed
 
 
+# ==================================================================================================
+# ops-hardening iter-9 (B2): the resolved libc `CDLL` handle inside `_release_process_memory()` is
+# memoized module-level (first-call-cached) instead of re-resolved via `ctypes.util.find_library` +
+# `ctypes.CDLL` on EVERY call — the exact memory-pressure `MemoryError`-abort path this session hardened
+# can call `_release_process_memory()` several times in one heavy ingest.
+# ==================================================================================================
+def test_release_process_memory_memoizes_libc_handle_across_calls(monkeypatch):
+    """TC-13 — `ctypes.util.find_library` / `ctypes.CDLL` resolve at most ONCE across repeated
+    `_release_process_memory()` calls in the same process; every call still performs `gc.collect()` +
+    `malloc_trim()` with unchanged effect (no change to timing/effect, fewer redundant resolutions only)."""
+    import ctypes
+
+    # A fresh cache dict for this test only — monkeypatch restores the ORIGINAL dict object at teardown,
+    # so this never leaks state into (or out of) any other test's view of the real module cache.
+    monkeypatch.setattr(data_manager, "_libc_malloc_trim_cache", {})
+
+    find_calls = {"n": 0}
+    cdll_calls = {"n": 0}
+    trim_calls = {"n": 0}
+    gc_calls = {"n": 0}
+
+    class _FakeLibc:
+        def malloc_trim(self, _pad):
+            trim_calls["n"] += 1
+
+    def _fake_find_library(_name):
+        find_calls["n"] += 1
+        return "libfake-c.so.6"
+
+    def _fake_cdll(_name):
+        cdll_calls["n"] += 1
+        return _FakeLibc()
+
+    monkeypatch.setattr(ctypes.util, "find_library", _fake_find_library)
+    monkeypatch.setattr(ctypes, "CDLL", _fake_cdll)
+    monkeypatch.setattr(data_manager.gc, "collect", lambda: gc_calls.update(n=gc_calls["n"] + 1))
+
+    for _ in range(5):
+        data_manager._release_process_memory()
+
+    assert find_calls["n"] == 1, "find_library must resolve at most once across repeated calls"
+    assert cdll_calls["n"] == 1, "CDLL must be constructed at most once across repeated calls"
+    assert trim_calls["n"] == 5, "malloc_trim must still run on EVERY call — unchanged effect"
+    assert gc_calls["n"] == 5, "gc.collect() must still run on EVERY call — unchanged effect"
+
+
+def test_release_process_memory_caches_permanent_resolution_failure(monkeypatch):
+    """TC-13 companion — a non-glibc / symbol-absent failure on the FIRST call is cached too (never
+    retried): `find_library`/`CDLL` are still invoked only once across repeated calls, and every call's
+    `gc.collect()` still runs unchanged even though no `malloc_trim` is ever available."""
+    import ctypes
+
+    monkeypatch.setattr(data_manager, "_libc_malloc_trim_cache", {})
+    find_calls = {"n": 0}
+    gc_calls = {"n": 0}
+
+    def _fake_find_library(_name):
+        find_calls["n"] += 1
+        raise OSError("simulated: no libc resolvable on this platform")
+
+    monkeypatch.setattr(ctypes.util, "find_library", _fake_find_library)
+    monkeypatch.setattr(data_manager.gc, "collect", lambda: gc_calls.update(n=gc_calls["n"] + 1))
+
+    for _ in range(3):
+        data_manager._release_process_memory()  # must not raise
+
+    assert find_calls["n"] == 1, "a resolution failure must be cached — never retried on later calls"
+    assert gc_calls["n"] == 3, "gc.collect() must still run on every call despite the cached failure"
+
+
 # ==================================================================================================
 # ops-hardening iter-4 (F1 fix): the finalize hook's own heartbeat -- `last_progress_at` must advance
 # through the WHOLE finalize tail (not just the main scan loop), or the frontend's stale-heartbeat flag
diff --git a/apps/backend/tests/test_data_manager_jobs_pipeline.py b/apps/backend/tests/test_data_manager_jobs_pipeline.py
index 5f67437c..ec6d0fb6 100644
--- a/apps/backend/tests/test_data_manager_jobs_pipeline.py
+++ b/apps/backend/tests/test_data_manager_jobs_pipeline.py
@@ -668,3 +668,127 @@ def test_drift_stage_does_not_rerun_on_skip_fetch_backfill_only_resume(tmp_path,
         )
     assert telltale.calls == 0, "resume-at-backfill must perform ZERO provider calls (fetch stage skipped)"
     assert read_drift_report() == first_report, "a skip-fetch resume must leave the drift artifact untouched"
+
+
+# ==================================================================================================
+# ops-hardening iter-9 (F1 — J-04 step 6): an INTERRUPTED job keeps its LAST PERSISTED PROGRESS.
+# Before this iteration the numeric detail fields were written into the persisted row exactly ONCE, by
+# `_finalize_run_record` — which a `kill -9` never reaches — so the boot sweep's `interrupted` row always
+# carried the creation-time defaults and rendered as "0 snapshots · 0 trading days in range" no matter how
+# far the job actually got (browser-verified live: J-04 step 6 / UT-10). A throttled checkpoint now freezes
+# the CURRENT progress onto the still-OPEN `running` row as the backfill advances.
+# ==================================================================================================
+def _run_detail_json(engine, job_id: str) -> dict:
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job_id)).one()
+    return json.loads(row.message)
+
+
+def test_interrupted_job_keeps_its_last_checkpointed_progress(tmp_path, monkeypatch):
+    """J-04 step 6 — a job whose process dies mid-run leaves an `interrupted` row carrying the progress it
+    had actually reached, NOT zeros. The death is simulated the only honest way an in-process test can: the
+    terminal transition (`_finalize_run_record`) never runs, exactly as it never runs under `kill -9`."""
+    cfg, engine = _fresh_seed_engine(tmp_path, "checkpoint_progress")
+    with Session(engine) as session:
+        trading = data_manager._trading_days(session, cfg)
+    _base = _daily_region_start(trading, cfg)
+    r_start, r_end = trading[_base + 305], trading[_base + 307]  # 3 trading days
+    # The production checkpoint is time-throttled; a sub-second test would otherwise only ever record the
+    # FIRST date. Zero interval => checkpoint after every date (the same code path, just unthrottled).
+    monkeypatch.setattr(data_manager, "_RUN_RECORD_CHECKPOINT_INTERVAL_S", 0.0)
+    monkeypatch.setattr(data_manager, "_finalize_run_record", lambda *a, **k: None)
+
+    job = create_job("backfill", r_start, r_end)
+    run_data_job(job.job_id, config=_with_backfill_workers(cfg, 1), engine=engine)
+
+    assert sweep_orphaned_runs(engine) == 1  # the boot sweep claims the orphaned `running` row
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+    assert row.status == "interrupted"
+    assert row.finished_at is not None
+
+    detail = json.loads(row.message)
+    assert detail["dates_total"] == 3           # trading days in the requested range — was 0
+    assert detail["dates_done"] == 3            # progress actually reached — was 0
+    assert detail["snapshots_created"] == 3     # snapshots genuinely persisted — was 0
+    assert detail["calendar_days"] == (r_end - r_start).days + 1
+    assert detail["already_snapshotted"] == 0
+    assert detail["error_other"] == 0
+    # the finalize hook never ran on this dead job — its output stays honestly absent, never fabricated
+    assert detail["aggregates_refreshed"] is None
+
+
+def test_run_record_checkpoint_is_throttled_open_ended_and_never_fatal(tmp_path, monkeypatch):
+    """The checkpoint writer's own contract: bounded write amplification (at most one UPDATE per interval),
+    the row stays OPEN (`running`, no `finished_at`) so the boot sweep can still claim it, a job with no
+    open row is a silent no-op (never a second row), and a write failure is never fatal to the job."""
+    cfg, engine = _fresh_seed_engine(tmp_path, "checkpoint_unit")
+    prog = JobProgress(job_id="job-cp", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 3))
+    data_manager._create_run_record(engine, cfg, prog)
+    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 0  # creation-time defaults
+
+    prog.calendar_days, prog.dates_total, prog.dates_done, prog.snapshots_created = 3, 3, 1, 1
+    data_manager._checkpoint_run_record(engine, prog)  # nothing checkpointed yet -> always writes
+    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 1
+    assert _run_detail_json(engine, "job-cp")["dates_done"] == 1
+
+    prog.dates_done, prog.snapshots_created = 2, 2
+    data_manager._checkpoint_run_record(engine, prog)  # INSIDE the throttle window -> not written
+    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 1
+
+    monkeypatch.setattr(data_manager, "_RUN_RECORD_CHECKPOINT_INTERVAL_S", 0.0)  # interval elapsed
+    data_manager._checkpoint_run_record(engine, prog)
+    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 2
+
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "job-cp")).one()
+    assert row.status == "running" and row.finished_at is None  # still OPEN for the boot sweep
+
+    # a write failure is telemetry, not job control: a broken engine must not raise into the backfill loop
+    data_manager._checkpoint_run_record(
+        make_engine("sqlite:////nonexistent-dir-for-checkpoint-test/x.db"), prog
+    )
+
+    # once the row is terminal there is no open row to checkpoint -> silent no-op, never a second record
+    prog.status, prog.finished_at = "ok", data_manager._utcnow()
+    data_manager._finalize_run_record(engine, cfg, prog)
+    prog.snapshots_created = 99
+    data_manager._checkpoint_run_record(engine, prog)
+    with Session(engine) as session:
+        rows = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "job-cp")).all()
+    assert len(rows) == 1
+    assert rows[0].status == "ok"
+    assert json.loads(rows[0].message)["snapshots_created"] == 2  # the terminal value, not the post-hoc 99
+
+
+def test_interrupted_before_first_date_still_keeps_the_computed_range(tmp_path, monkeypatch):
+    """ops-hardening iter-9 AUDIT (F1 completion) — a job killed BEFORE its first date is persisted (the
+    shared bar-cache prefill window, minutes long on the deep basis) must still show the range it had
+    already computed, not "0 trading days in range". The per-date checkpoint alone cannot cover this
+    window: it only writes once a date has been persisted."""
+    cfg, engine = _fresh_seed_engine(tmp_path, "checkpoint_preloop")
+    with Session(engine) as session:
+        trading = data_manager._trading_days(session, cfg)
+    _base = _daily_region_start(trading, cfg)
+    r_start, r_end = trading[_base + 305], trading[_base + 307]  # 3 trading days
+
+    # Death during the prefill: the bar-cache load never returns, and the terminal transition
+    # (`_finalize_run_record`) never runs — exactly what `kill -9` does at that instant.
+    def _die_in_prefill(*_a, **_k):
+        raise RuntimeError("simulated process death during the shared bar-cache prefill")
+
+    monkeypatch.setattr(data_manager, "prefilled_bar_cache", _die_in_prefill)
+    monkeypatch.setattr(data_manager, "_finalize_run_record", lambda *a, **k: None)
+
+    job = create_job("backfill", r_start, r_end)
+    run_data_job(job.job_id, config=_with_backfill_workers(cfg, 1), engine=engine)
+
+    assert sweep_orphaned_runs(engine) == 1
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+    assert row.status == "interrupted"
+    detail = json.loads(row.message)
+    assert detail["dates_total"] == 3                                   # the real range — was 0
+    assert detail["calendar_days"] == (r_end - r_start).days + 1        # the real span — was null
+    assert detail["snapshots_created"] == 0                             # honest: none were created yet
+    assert detail["aggregates_refreshed"] is None                       # the finalize hook never ran
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index 60078a66..074cb433 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -18,9 +18,24 @@ scenario that made `GET /api/health` hang 7+ minutes with a worker-thread `Memor
 methodology) via a dedicated `spawned_backend_throwaway_db` fixture. This is a genuinely slow, heavy test
 (a full rebuild alone measures ~16 minutes on the real dev DB's current size, Item L) — an accepted cost
 for a real-process capacity proof, consistent with this project's existing slow real-engine tests (e.g.
-`test_forward_testing.py`'s session-scoped 30-year seed rebuild)."""
+`test_forward_testing.py`'s session-scoped 30-year seed rebuild).
+
+ops-hardening iter-9 (AG-10 launcher-cap closure) adds TC-7/TC-8/TC-9: real-process verification that
+`scripts/start-backend.sh` AND `scripts/dev.sh`'s backend subshell apply the SMT-aware `taskset` CPU-
+affinity mask + BLAS/OMP/numexpr thread caps declared in `project-extensions/host-guard/host-guard.env`
+(TC-7/TC-8), that `dev.sh`'s frontend (`next dev`) subshell never receives any of them (TC-8), and that
+both scripts still start cleanly with zero caps applied when host-guard.env is absent or disabled (TC-9).
+Every TC-7/8/9 test resolves the launched process's PID via `lsof` on its listening port rather than
+trusting a launching shell's own PID — `uvicorn --reload` (dev.sh) and `next dev` both fork a further
+worker/server subprocess that is the one actually bound to the port, and CPU affinity / environment are
+inherited across that `fork()` regardless of which PID in the chain is checked. Tests that need to prove
+"no cap was added" compare against THIS TEST PROCESS'S OWN unmodified affinity/environment (not a
+hardcoded assumption about the host's full CPU set or ambient env), since goal-mode's own engine-wrap can
+already confine the whole session to the same mask host-guard.env declares — a coincidental match must
+never be misread as "dev.sh applied it independently"."""
 from __future__ import annotations
 
+import csv
 import hashlib
 import os
 import re
@@ -50,6 +65,94 @@ _TEST_PORT = 18000 + _offset
 # A THIRD, further-distinct port for the throwaway-DB heavy-ingest test below — never shared with the
 # other tests in this module (which may run in the same session) or with a real dev/QA instance.
 _HEAVY_TEST_PORT = 18500 + _offset
+# A FOURTH pair of ports for the dev.sh launcher-cap test (TC-8) below.
+_DEV_SCRIPT = REPO_ROOT / "scripts" / "dev.sh"
+_DEVSCRIPT_BACKEND_PORT = 18700 + _offset
+_DEVSCRIPT_FRONTEND_PORT = 19700 + _offset
+# A FIFTH port for the "caps absent/disabled" launcher test (TC-9) below.
+_NOCAP_TEST_PORT = 18800 + _offset
+
+# ops-hardening iter-9 (AG-10): the real, committed host-guard config this project runs under.
+HOST_GUARD_ENV_FILE = REPO_ROOT / "project-extensions" / "host-guard" / "host-guard.env"
+
+# ops-hardening iter-9 (T4): the finalize hook's full aggregate-category vocabulary
+# (`_refresh_ingest_aggregates`'s own docstring, `apps/backend/app/engine/data_manager.py`) — asserted
+# complete for BOTH the rebuild and the backfill job below (iter-8's own live measurement observed all 7
+# categories for both job kinds on this real DB; a job that early-aborted a warm loop on `MemoryError`
+# would honestly omit one or more of these, which is exactly what this tightened assertion catches).
+_ALL_AGGREGATE_CATEGORIES = frozenset(
+    {
+        "latest_snapshot",
+        "coverage",
+        "membership_timeline",
+        "market_phase",
+        "forward_aggregates",
+        "research_hot_keys",
+        "drawdown_expectations",
+    }
+)
+
+# ops-hardening iter-9 AUDIT (T3): the two categories the finalize hook can only refresh when the job
+# actually PERSISTED at least one new snapshot — `latest_snapshot` is gated on `if prog.new_snapshot_dates:`
+# and `market_phase` iterates `for d in prog.new_snapshot_dates:` (`data_manager._refresh_ingest_aggregates`).
+# A ZERO-WORK job (every requested date already snapshotted) therefore honestly reports only the other five;
+# demanding all seven of it would be a FALSE regression signal, not a caught early-abort. The test below
+# keeps the full seven-category bar wherever real snapshot work happened, and separately asserts that the
+# backfill job it controls DID do real work — so "my scenario went stale" fails loudly and specifically
+# instead of masquerading as a MemoryError early-abort.
+_SNAPSHOT_DEPENDENT_CATEGORIES = frozenset({"latest_snapshot", "market_phase"})
+
+
+def _expected_aggregate_categories(job: dict) -> frozenset[str]:
+    """The categories `_refresh_ingest_aggregates` can honestly have refreshed for THIS job's outcome:
+    all seven when the job created >= 1 new snapshot, otherwise the five that do not depend on
+    `prog.new_snapshot_dates`."""
+    return (
+        _ALL_AGGREGATE_CATEGORIES
+        if (job.get("snapshots_created") or 0) > 0
+        else _ALL_AGGREGATE_CATEGORIES - _SNAPSHOT_DEPENDENT_CATEGORIES
+    )
+
+
+def _read_host_guard_env(path: Path) -> dict[str, str]:
+    """Parse the plain `KEY=VALUE` (optionally quoted) lines of a host-guard.env-shaped file — no shell
+    evaluation, just enough to compare a launched process's real /proc state against the declared values."""
+    values: dict[str, str] = {}
+    for line in path.read_text().splitlines():
+        line = line.strip()
+        if not line or line.startswith("#") or "=" not in line:
+            continue
+        key, _, val = line.partition("=")
+        val = val.strip().strip('"').strip("'")
+        values[key.strip()] = val
+    return values
+
+
+def _parse_cpu_list(spec: str) -> set[int]:
+    """Parse a `/proc/<pid>/status` `Cpus_allowed_list` (or a `HOST_GUARD_CPU_LIST`) value like
+    `"0-3,8-11"` into the set of individual CPU indices `{0,1,2,3,8,9,10,11}`."""
+    cpus: set[int] = set()
+    spec = spec.strip()
+    if not spec:
+        return cpus
+    for part in spec.split(","):
+        part = part.strip()
+        if not part:
+            continue
+        if "-" in part:
+            lo, _, hi = part.partition("-")
+            cpus.update(range(int(lo), int(hi) + 1))
+        else:
+            cpus.add(int(part))
+    return cpus
+
+
+def _read_proc_status_cpus_allowed(pid: int) -> str:
+    with open(f"/proc/{pid}/status") as fh:
+        for line in fh:
+            if line.startswith("Cpus_allowed_list:"):
+                return line.split(":", 1)[1].strip()
+    raise AssertionError(f"no 'Cpus_allowed_list' row in /proc/{pid}/status")
 
 
 def _read_proc_limits_max_address_space_bytes(pid: int) -> int:
@@ -63,6 +166,17 @@ def _read_proc_limits_max_address_space_bytes(pid: int) -> int:
     raise AssertionError(f"no 'Max address space' row in /proc/{pid}/limits")
 
 
+def _read_proc_limits_max_address_space_raw(pid: int) -> str:
+    """Like `_read_proc_limits_max_address_space_bytes`, but returns the RAW soft-limit field
+    ("unlimited" or a byte string) instead of parsing it as an int — for callers that only need to
+    compare against/detect the unrestricted case, which is not itself a number."""
+    with open(f"/proc/{pid}/limits") as fh:
+        for line in fh:
+            if line.startswith("Max address space"):
+                return line.split()[3]
+    raise AssertionError(f"no 'Max address space' row in /proc/{pid}/limits")
+
+
 def _read_proc_environ(pid: int) -> dict[str, str]:
     with open(f"/proc/{pid}/environ", "rb") as fh:
         raw = fh.read()
@@ -335,6 +449,7 @@ class _MemSampler(threading.Thread):
         while not self._stop_event.is_set():
             row = _read_proc_status_kb(self.pid)
             if row:
+                row["ts"] = time.time()
                 self.samples.append(row)
             time.sleep(0.25)
 
@@ -369,6 +484,26 @@ class _HealthPoller(threading.Thread):
         self._stop_event.set()
 
 
+def _write_run_evidence(base: Path, mem: "_MemSampler", health: "_HealthPoller") -> None:
+    """ops-hardening iter-9 (DoD item 5): retain THIS run's raw samples as CSV next to the iteration's
+    other artifacts. `base` is the path named by TRENDORA_HEAVY_INGEST_SAMPLER_CSV; the health-poll
+    timings are written beside it as `<stem>-health.csv`. Written from the test's `finally` block, so the
+    evidence survives a failing assertion (a failed heavy run is exactly when the samples matter most)."""
+    base.parent.mkdir(parents=True, exist_ok=True)
+    with base.open("w", newline="") as fh:
+        w = csv.writer(fh)
+        w.writerow(["epoch", "vmpeak_kb", "vmsize_kb", "vmrss_kb", "vmhwm_kb"])
+        for s in mem.samples:
+            w.writerow([f"{s.get('ts', 0):.3f}", s.get("VmPeak", ""), s.get("VmSize", ""),
+                        s.get("VmRSS", ""), s.get("VmHWM", "")])
+    health_csv = base.with_name(base.stem + "-health.csv")
+    with health_csv.open("w", newline="") as fh:
+        w = csv.writer(fh)
+        w.writerow(["poll_index", "http_status", "elapsed_s", "error"])
+        for i, r in enumerate(health.results):
+            w.writerow([i, r.get("status", ""), f"{r.get('elapsed', 0):.3f}", r.get("error", "")])
+
+
 def _post_job(port: int, kind: str, start: str, end: str) -> str:
     resp = httpx.post(
         f"http://127.0.0.1:{port}/api/data/jobs", json={"kind": kind, "start": start, "end": end},
@@ -378,6 +513,39 @@ def _post_job(port: int, kind: str, start: str, end: str) -> str:
     return resp.json()["job_id"]
 
 
+def _pick_unsnapshotted_trading_day(port: int, cfg) -> str:
+    """ops-hardening iter-9 AUDIT (T3) — choose the heavy backfill's target date AT RUN TIME instead of
+    hardcoding one that silently goes stale.
+
+    A hardcoded date (previously `2010-07-15`) stops being new work the moment anything snapshots it: the
+    ingest orchestrator drops already-snapshotted dates from `targets` and returns early when none remain
+    (`data_manager._backfill_snapshots`), so the job becomes a zero-work no-op that can never exercise the
+    per-item warm loops this test exists to measure — and the seven-category completeness assertion below
+    then fails for a reason that has nothing to do with a `MemoryError` early-abort.
+
+    The candidate set is read from the SPAWNED INSTANCE's own `GET /api/data/availability`, i.e. the same
+    benchmark trading calendar (`_trading_days`) and the same `ScannerRun.asof_date` snapshot set the
+    orchestrator's target selection reads — never a second derivation here. Candidates keep at least
+    `max(walk_forward.horizons)` trading days of calendar after them so the finalize hook's forward-return
+    and forward-aggregate work is real rather than truncated at the end of the calendar, and the LATEST
+    such day is chosen (maximum available history for the scan). No date literal, no magic number."""
+    resp = httpx.get(f"http://127.0.0.1:{port}/api/data/availability", timeout=120.0)
+    resp.raise_for_status()
+    cells = resp.json().get("cells") or []
+    lookahead = max(cfg.walk_forward.horizons)
+    candidates = [
+        c for c in cells[:-lookahead]
+        if not c.get("snapshot_exists") and (c.get("symbols_with_bars") or 0) > 0
+    ]
+    if not candidates:
+        pytest.skip(
+            f"no unsnapshotted trading day with bars and >= {lookahead} trading days of following calendar "
+            f"remains in this DB copy ({len(cells)} trading days) — there is no genuine new-snapshot work "
+            "left for the second heavy job, so this run could only measure a zero-work no-op"
+        )
+    return candidates[-1]["date"]
+
+
 def _poll_job_to_terminal(port: int, job_id: str, timeout_s: float) -> dict:
     deadline = time.monotonic() + timeout_s
     last: dict = {}
@@ -396,13 +564,16 @@ def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawn
     `rebuild` (exercises the finalize hook's per-date coverage/market-phase loops + all configured
     forward-aggregate horizons + every ledger claim's drawdown-expectations warm at full scale — Item L
     measured ~378 snapshot dates / ~16 min on this real DB) immediately followed by a second heavy
-    `backfill` for a genuine non-cadence historical date (`2010-07-15` — the SAME date iter-7's browser-qa
-    session used, which the rebuild's monthly/daily cadence does not itself touch, so this creates real new
-    snapshot/forward-return work through the SAME finalize hook a second time) in the SAME spawned process.
+    `backfill` for a genuine non-cadence historical date, SELECTED AT RUN TIME from the spawned instance's
+    own availability map (ops-hardening iter-9 audit T3 — a hardcoded date silently decays into a zero-work
+    no-op as soon as anything snapshots it), so this creates real new snapshot/forward-return work through
+    the SAME finalize hook a second time in the SAME spawned process.
     `/proc/<pid>/status` is sampled every 0.25s throughout both jobs; `GET /api/health` is polled every 2s
-    throughout. Asserts: both jobs reach a terminal (non-`failed`) status, peak VmPeak/VmSize stay under
-    `server.memory_cap_mb` with margin, and every health poll returns HTTP 200 (zero timeouts, zero
-    hangs)."""
+    throughout. Asserts: both jobs reach status `"ok"` — NOT `"partial"` (ops-hardening iter-9, T4: a
+    `"partial"` result here would mean a per-item warm loop silently early-aborted on `MemoryError` during
+    THIS run, which is exactly the failure this test exists to catch, not tolerate) — with a COMPLETE
+    `aggregates_refreshed` list for each job's kind, peak VmPeak/VmSize under `server.memory_cap_mb` with
+    margin, and every health poll returning HTTP 200 (zero timeouts, zero hangs)."""
     from app.config import get_config
 
     backend = spawned_backend_throwaway_db
@@ -416,11 +587,23 @@ def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawn
     try:
         job_id_1 = _post_job(backend.port, "rebuild", "2024-01-01", "2024-01-01")
         job1 = _poll_job_to_terminal(backend.port, job_id_1, timeout_s=1800.0)
-        assert job1.get("status") in ("ok", "partial"), f"rebuild job did not succeed: {job1}"
-
-        job_id_2 = _post_job(backend.port, "backfill", "2010-07-15", "2010-07-15")
+        # ops-hardening iter-9 (T4): reject "partial" — a partial status here means a per-item warm loop
+        # early-aborted on MemoryError during THIS live run, which this test exists to catch, not accept.
+        assert job1.get("status") == "ok", f"rebuild job did not reach status 'ok': {job1}"
+
+        # ops-hardening iter-9 AUDIT (T3): pick the second job's date AFTER the rebuild has committed its
+        # own snapshots, so the choice reflects the DB state this backfill will actually face.
+        backfill_date = _pick_unsnapshotted_trading_day(backend.port, cfg)
+        job_id_2 = _post_job(backend.port, "backfill", backfill_date, backfill_date)
         job2 = _poll_job_to_terminal(backend.port, job_id_2, timeout_s=600.0)
-        assert job2.get("status") in ("ok", "partial"), f"second backfill job did not succeed: {job2}"
+        assert job2.get("status") == "ok", f"second backfill job did not reach status 'ok': {job2}"
+        # The scenario-integrity guard: this job was aimed at a date with no snapshot, so it MUST have
+        # created one. A zero-work no-op here would exercise none of the per-item warm loops this test
+        # measures — fail loudly on that, rather than letting it surface later as a missing-category error.
+        assert (job2.get("snapshots_created") or 0) >= 1, (
+            f"backfill of {backfill_date} created no snapshot ({job2.get('snapshots_created')}) — the "
+            f"second heavy job did zero work, so this run proves nothing about warm-loop survival: {job2}"
+        )
 
         time.sleep(3.0)  # settle window so any tail allocation/gc shows up in the sampled peak too
     finally:
@@ -428,6 +611,34 @@ def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawn
         mem.join(timeout=5)
         health.stop()
         health.join(timeout=5)
+        sampler_csv = os.environ.get("TRENDORA_HEAVY_INGEST_SAMPLER_CSV")
+        if sampler_csv:
+            _write_run_evidence(Path(sampler_csv), mem, health)
+        print(
+            f"\n[heavy-ingest] samples={len(mem.samples)} peak_VmPeak_kb={mem.peak('VmPeak')} "
+            f"peak_VmSize_kb={mem.peak('VmSize')} peak_VmRSS_kb={mem.peak('VmRSS')} "
+            f"cap_kb={cap_kb} health_polls={len(health.results)} "
+            f"health_non_200={len([r for r in health.results if r['status'] != 200])} "
+            f"health_max_elapsed_s={max((r['elapsed'] for r in health.results), default=0):.3f}"
+        )
+
+    # ops-hardening iter-9 (T4): each job's persisted `aggregates_refreshed` list must contain EVERY
+    # category the finalize hook can refresh FOR THAT JOB'S OUTCOME — a partial list (even with status
+    # "ok", which the honesty gate allows since aggregate-refresh failures are non-fatal to the job) would
+    # mean one of the four per-item warm loops silently early-aborted on MemoryError during this run
+    # without failing the job. The expected set is all seven whenever the job persisted a new snapshot and
+    # the five snapshot-independent ones otherwise (audit T3 — see `_expected_aggregate_categories`); job2
+    # is asserted above to have done real work, so it is always held to the full seven.
+    missing_1 = _expected_aggregate_categories(job1) - set(job1.get("aggregates_refreshed") or [])
+    assert not missing_1, (
+        f"rebuild job's aggregates_refreshed is missing categories: {sorted(missing_1)} "
+        f"(got {job1.get('aggregates_refreshed')}) — a per-item warm loop may have early-aborted"
+    )
+    missing_2 = _expected_aggregate_categories(job2) - set(job2.get("aggregates_refreshed") or [])
+    assert not missing_2, (
+        f"backfill job's aggregates_refreshed is missing categories: {sorted(missing_2)} "
+        f"(got {job2.get('aggregates_refreshed')}) — a per-item warm loop may have early-aborted"
+    )
 
     peak_vmpeak = mem.peak("VmPeak")
     peak_vmsize = mem.peak("VmSize")
@@ -444,3 +655,355 @@ def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawn
         f"expected EVERY health poll to be HTTP 200 with zero timeouts/hangs; got "
         f"{len(non_200_or_error)}/{len(health.results)} non-200-or-error polls: {non_200_or_error[:5]}"
     )
+
+
+# ==================================================================================================
+# ops-hardening iter-9 (AG-10 launcher-cap closure) — TC-7 / TC-8 / TC-9.
+# ==================================================================================================
+
+_HOST_GUARD_BLAS_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
+
+
+def _owning_pid(port: int, timeout: float = 20.0) -> int:
+    """The PID actually bound to `port`'s listening socket — the robust way to find the real worker
+    process regardless of how many `fork`/`exec` hops a launcher's supervisor (uvicorn `--reload`,
+    `next dev`) put between the launching shell and it. Tries `lsof` first (works for the uvicorn
+    reloader/worker); a Next.js dev server's listening socket is not always attributable via `lsof -ti`
+    on this platform, so `ss -tlnp` (own-process sockets are visible without root) is the fallback.
+    Retries briefly either way: a dev frontend can briefly hand the listening socket to a different
+    process right around its first response (HMR-related rebuild)."""
+    deadline = time.monotonic() + timeout
+    ss_pattern = re.compile(rf":{port}\s.*pid=(\d+)")
+    while True:
+        out = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5)
+        pids = [int(p) for p in out.stdout.split() if p.strip()]
+        if pids:
+            return pids[0]
+        ss_out = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
+        for line in ss_out.stdout.splitlines():
+            m = ss_pattern.search(line)
+            if m:
+                return int(m.group(1))
+        if time.monotonic() >= deadline:
+            raise AssertionError(
+                f"no process found listening on :{port} (lsof and `ss -tlnp` both empty) within {timeout}s"
+            )
+        time.sleep(0.5)
+
+
+def _wait_for_port_answering(port: int, timeout: float) -> None:
+    """Wait until ANY HTTP response (even non-200 — a dev frontend's first request can 404/redirect
+    before it has fully settled) comes back from `port` — proof something is bound and serving."""
+    deadline = time.monotonic() + timeout
+    last_exc: Exception | None = None
+    while time.monotonic() < deadline:
+        try:
+            httpx.get(f"http://127.0.0.1:{port}/", timeout=2.0)
+            return
+        except Exception as exc:  # noqa: BLE001 — keep polling until the deadline
+            last_exc = exc
+        time.sleep(0.5)
+    raise AssertionError(f"nothing answered on :{port} within {timeout}s (last error: {last_exc})")
+
+
+def test_start_backend_applies_host_guard_caps_when_enabled(spawned_backend):
+    """TC-7 — with the committed `project-extensions/host-guard/host-guard.env` present and
+    `HOST_GUARD_ENABLED=1`, `scripts/start-backend.sh`'s launched process's `Cpus_allowed_list` matches
+    `HOST_GUARD_CPU_LIST` and its environment carries the BLAS/OMP/numexpr thread-cap vars set to
+    `HOST_GUARD_BLAS_THREADS`."""
+    if not HOST_GUARD_ENV_FILE.exists():
+        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present — host-guard is optional, nothing to verify")
+    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
+    if hg.get("HOST_GUARD_ENABLED") != "1":
+        pytest.skip("HOST_GUARD_ENABLED != 1 in the committed host-guard.env — nothing to verify")
+
+    pid = spawned_backend.pid
+    expected_cpus = _parse_cpu_list(hg["HOST_GUARD_CPU_LIST"])
+    actual_cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
+    assert actual_cpus == expected_cpus, (
+        f"expected Cpus_allowed_list to match HOST_GUARD_CPU_LIST {hg['HOST_GUARD_CPU_LIST']!r} "
+        f"({sorted(expected_cpus)}), got {sorted(actual_cpus)}"
+    )
+    env = _read_proc_environ(pid)
+    for var in _HOST_GUARD_BLAS_VARS:
+        assert env.get(var) == hg["HOST_GUARD_BLAS_THREADS"], (
+            f"expected {var}={hg['HOST_GUARD_BLAS_THREADS']!r} (HOST_GUARD_BLAS_THREADS), "
+            f"got {env.get(var)!r}"
+        )
+
+
+def test_dev_script_applies_host_guard_caps_to_backend_only(request):
+    """TC-8 — with the committed host-guard.env present and enabled, `scripts/dev.sh`'s backend subshell
+    launches uvicorn under the SAME CPU-affinity mask + BLAS/OMP/numexpr thread caps as
+    `scripts/start-backend.sh`, plus the mirrored `ulimit -v` / `MALLOC_ARENA_MAX` enforcement — while the
+    SAME script's frontend (`next dev`) subshell shows none of the host-guard caps and no memory/arena
+    restriction."""
+    if not HOST_GUARD_ENV_FILE.exists():
+        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present — host-guard is optional, nothing to verify")
+    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
+    if hg.get("HOST_GUARD_ENABLED") != "1":
+        pytest.skip("HOST_GUARD_ENABLED != 1 in the committed host-guard.env — nothing to verify")
+    if not _DEV_SCRIPT.exists():
+        pytest.skip(f"{_DEV_SCRIPT} not found")
+    if not (REPO_ROOT / "apps" / "frontend" / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed — cannot start the frontend for this check")
... [diff_bound] apps/backend/tests/test_start_backend_script.py: 260 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/dev.sh b/incredible_auto_dev/scripts/dev.sh
index bf37d604..e16bec7a 100755
--- a/incredible_auto_dev/scripts/dev.sh
+++ b/incredible_auto_dev/scripts/dev.sh
@@ -41,7 +41,41 @@ echo "Starting backend on :$BACKEND_PORT ..."
   cd "$ROOT_DIR/apps/backend"
   source .venv/bin/activate
   export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:${FRONTEND_PORT},http://localhost:3000,http://localhost:3001}"
-  uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT
+
+  # ops-hardening iter-9 (AG-10): mirror scripts/start-backend.sh's config-derived ulimit -v /
+  # MALLOC_ARENA_MAX enforcement (same app.config.get_config() values — computed once here, not a
+  # second derivation) in this backend subshell ONLY. The frontend (`next dev`) subshell below is
+  # untouched — it needs the address space.
+  read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE <<< "$(
+    .venv/bin/python -c '
+from app.config import get_config
+cfg = get_config()
+print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
+'
+  )"
+  ulimit -v $((MEMORY_CAP_MB * 1024))
+  export MALLOC_ARENA_MAX="$MALLOC_ARENA_MAX_VALUE"
+
+  # ==== HOST-GUARD (goal.md AG-10) — backend subshell ONLY, DO NOT REMOVE OR WEAKEN ================
+  # Same SMT-aware taskset CPU-affinity mask + BLAS/OMP/numexpr thread caps `scripts/start-backend.sh`
+  # applies, from the SAME host-guard.env (no second computation of the values). Absent file or
+  # HOST_GUARD_ENABLED=0 -> zero behavior change. Never applied to the frontend subshell below.
+  HOST_GUARD_ENV="${HOST_GUARD_ENV_FILE:-$ROOT_DIR/project-extensions/host-guard/host-guard.env}"
+  HOST_GUARD_CMD_PREFIX=()
+  if [[ -f "$HOST_GUARD_ENV" ]]; then
+    # shellcheck disable=SC1090
+    source "$HOST_GUARD_ENV"
+    if [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]]; then
+      export OMP_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+      export OPENBLAS_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+      export MKL_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+      export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+      HOST_GUARD_CMD_PREFIX=(taskset -c "$HOST_GUARD_CPU_LIST")
+    fi
+  fi
+  # ==== end HOST-GUARD ==============================================================================
+
+  exec "${HOST_GUARD_CMD_PREFIX[@]}" uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT
 ) &
 BACKEND_PID=$!
 
diff --git a/incredible_auto_dev/scripts/start-backend.sh b/incredible_auto_dev/scripts/start-backend.sh
index 58fb00ad..f277e24c 100755
--- a/incredible_auto_dev/scripts/start-backend.sh
+++ b/incredible_auto_dev/scripts/start-backend.sh
@@ -65,7 +65,34 @@ LOG_FILE="$LOG_DIR/backend.log"
   echo "    port=$PORT memory_cap_mb=$MEMORY_CAP_MB malloc_arena_max=$MALLOC_ARENA_MAX_VALUE"
 } >> "$LOG_FILE"
 
-exec "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
+# ==== HOST-GUARD (goal.md AG-10) — DO NOT REMOVE OR WEAKEN ==========================================
+# ops-hardening iter-9: apply this host's declared CPU-affinity mask + BLAS/OMP/numexpr thread caps to
+# the launched uvicorn process, additive to the ulimit/MALLOC_ARENA_MAX enforcement above (never a
+# replacement for it). Absent file or HOST_GUARD_ENABLED=0 -> zero behavior change — host-guard stays
+# fully project-neutral per its own header contract (project-extensions/host-guard/host-guard.env).
+# Every value below comes from that file; no magic numbers here. Stripping this block is a REGRESSION
+# regardless of test outcome (goal.md AG-10) — the caps are a physical hardware constraint (two instant
+# hard resets under all-core vectorized ingest bursts, 2026-07-20/21), not a perf knob.
+# HOST_GUARD_ENV_FILE lets tests point at a scratch copy (to exercise the absent/disabled branches
+# without ever touching the real, safety-critical committed file) — unset in every real launch, so
+# production always resolves to the committed path below.
+HOST_GUARD_ENV="${HOST_GUARD_ENV_FILE:-$REPO_ROOT/project-extensions/host-guard/host-guard.env}"
+HOST_GUARD_CMD_PREFIX=()
+if [[ -f "$HOST_GUARD_ENV" ]]; then
+  # shellcheck disable=SC1090
+  source "$HOST_GUARD_ENV"
+  if [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]]; then
+    export OMP_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+    export OPENBLAS_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+    export MKL_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+    export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+    HOST_GUARD_CMD_PREFIX=(taskset -c "$HOST_GUARD_CPU_LIST")
+    echo "    host-guard: cpu_list=$HOST_GUARD_CPU_LIST blas_threads=$HOST_GUARD_BLAS_THREADS" >> "$LOG_FILE"
+  fi
+fi
+# ==== end HOST-GUARD =================================================================================
+
+exec "${HOST_GUARD_CMD_PREFIX[@]}" "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
   --host 0.0.0.0 \
   --port "$PORT" \
   --app-dir "$REPO_ROOT/apps/backend" \
```
