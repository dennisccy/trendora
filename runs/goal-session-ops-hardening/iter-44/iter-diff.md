# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 4ad169d8..f37bbb8e 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -306,7 +306,13 @@ def retry_job(
             status_code=400,
             detail=f"source {run.provider!r} requires a key; set ${entry.env_var} or paste a session key",
         )
-    job_id = data_manager.retry_run(run_id, api_key=api_key, config=cfg, engine=get_engine())
+    # ops-hardening iter-44 (audit B4): same honest-error contract as `start_job`/`resume_job` above — a
+    # thread-launch failure is already recorded on the retried job's run-history row by `retry_run` itself;
+    # re-raised here so this endpoint never returns a 200 over a retry that never started.
+    try:
+        job_id = data_manager.retry_run(run_id, api_key=api_key, config=cfg, engine=get_engine())
+    except (RuntimeError, MemoryError) as exc:  # iter-44 (audit B4) — see `start_job` above
+        raise HTTPException(status_code=503, detail=f"failed to launch retry worker: {exc}") from exc
     return {"run_id": run_id, "job_id": job_id, "source": run.provider, "status": "running"}
 
 
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 994bf2aa..fee08896 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -2885,8 +2885,22 @@ def _resolve_libc_malloc_trim():
             libc_name = ctypes.util.find_library("c") or "libc.so.6"
             libc = ctypes.CDLL(libc_name)
             _libc_malloc_trim_cache["fn"] = libc.malloc_trim
-        except (OSError, AttributeError):  # non-glibc / symbol absent
+        except (OSError, AttributeError):  # non-glibc / symbol absent — a PERMANENT failure, cached
             _libc_malloc_trim_cache["fn"] = None
+        except MemoryError:
+            # ops-hardening iter-44 AUDIT (B2): the resolution ITSELF allocates — `ctypes.util.find_library`
+            # forks `ldconfig` and regexes its whole stdout — so under an exhausted `ulimit -v` it raises
+            # `MemoryError`. That is precisely WHEN `_release_process_memory()` is called: from inside the
+            # per-horizon `except MemoryError` abort handler in `_refresh_ingest_aggregates`. With only
+            # `(OSError, AttributeError)` caught here, the abort handler's own cleanup re-raised and the
+            # "log + continue, never raise" contract broke — the live escape captured by
+            # `test_ingest_finalize_memory_pressure.py`'s child probe (returncode 1,
+            # `ctypes/util.py:297 in _findSoname_ldconfig` under a 750,000 KB cap). Return None WITHOUT
+            # caching it: unlike a non-glibc host this is a TRANSIENT condition, and caching would
+            # permanently disable the iter-27 `malloc_trim` memory-return path for the process's whole
+            # life (an AG-8 regression). Applies the binding iter-43 lesson — key the guard to the whole
+            # exception set the incident actually produces, not its headline exception.
+            return None
     return _libc_malloc_trim_cache["fn"]
 
 
@@ -3617,9 +3631,18 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
             # appended ONLY when this call actually persisted a new row this run (`persisted` is False on a
             # cache HIT — an honest "was skipped" omission, never a fabricated refresh, mirroring every other
             # category's honesty gate above).
-            from app.engine import indexes  # deferred: see comment above (breaks a module-load cycle)
-
             try:
+                # ops-hardening iter-44 AUDIT (B2): the deferred import stays INSIDE this block's guards.
+                # Sitting one line above the `try`, it was the only unguarded statement left in this
+                # otherwise fully-isolated finalize sequence — and importing a not-yet-loaded module
+                # allocates (read + compile of `indexes.py`), so under an exhausted `ulimit -v` it raised
+                # `MemoryError` and escaped `_refresh_ingest_aggregates` entirely, breaking its documented
+                # "log + continue, never raise" contract. Live-captured by
+                # `test_ingest_finalize_memory_pressure.py`'s child probe (`<frozen
+                # importlib._bootstrap_external>:1191 in get_data`, returncode 1). Import position is
+                # unchanged in every other respect — still deferred, still breaking the module-load cycle.
+                from app.engine import indexes  # deferred: see comment above (breaks a module-load cycle)
+
                 _, index_series_persisted = indexes.index_series_cached_with_status(session, cfg)
                 if index_series_persisted:
                     refreshed.append("index_series")
@@ -4511,7 +4534,29 @@ def _run_job(
             prog.status = final_status
     except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job (scrubbed)
         prog.status = "failed"
-        _record_error(prog, scrub(str(exc)))
+        # ops-hardening iter-44 AUDIT (B1): `str(MemoryError())` is the EMPTY STRING — and `MemoryError`
+        # is THE exception class this session's real failures actually raise (see `logs/backend.log`'s
+        # caught-MemoryError storm during the 2026-08-03 browser-lane incident). With a bare
+        # `scrub(str(exc))` the whole honesty fix below collapsed for exactly that class: `prog.message`
+        # became `""`, whose falsiness sends `_run_detail`'s `prog.message if (... and prog.message)`
+        # guard straight back to `_final_summary`'s generic "0 snapshots over N dates" text — the precise
+        # string this iteration's TC-10 exists to eliminate (live-observed on run 272). Name the
+        # exception TYPE when it carries no text, so a failed job's persisted reason is never blank.
+        # Applies the binding iter-43 lesson: key the guard to the WHOLE exception set the diagnosed
+        # incident produces, not its headline (text-carrying) exception.
+        reason = scrub(str(exc)) or f"{type(exc).__name__} (no message)"
+        _record_error(prog, reason)
+        # ops-hardening iter-44 (reviewer MINOR, carried from iter-43 B5): capture the REAL reason on
+        # `prog.message` itself (not just `prog.errors`) so the `finally` block below — which no longer
+        # unconditionally overwrites a failed job's message with `_final_summary` (a summary of WORK DONE,
+        # which structurally cannot name a failure that happened before any work was recorded) — has
+        # something honest to preserve. This is also what makes the iter-43 audit's `_run_detail` B2 fix
+        # (line ~4037, `"summary": prog.message if (prog.status == "failed" and prog.message) else
+        # _final_summary(prog)`) stop being a no-op: that guard already special-cased a failed status, but
+        # until now `prog.message` at that point was ALWAYS `_final_summary(prog)` too (assigned
+        # unconditionally by this same `finally` block), so the two branches collided and always produced
+        # the identical string (audit B5's finding).
+        prog.message = reason
         # J-59: a `both`/`backfill` job whose FETCH completed but whose BACKFILL failed is marked
         # `failed_backfill` on its durable checkpoint, so Unfinished-imports offers it as "failed at
         # backfill — resumable from the backfill stage" (a Resume skips the completed fetch — zero
@@ -4540,7 +4585,13 @@ def _run_job(
         if prog._shared_bar_cache is not None:
             prog._shared_bar_cache = None
             _release_process_memory()
-        prog.message = _final_summary(prog)
+        # ops-hardening iter-44 (reviewer MINOR, carried from iter-43 B5): a job that failed via the outer
+        # exception handler above already has its real captured reason on `prog.message` (set at the
+        # `except Exception as exc` block, alongside `_record_error`) — do NOT clobber it with
+        # `_final_summary`'s generic "work done" text. Every other terminal status (`ok`/`partial`/
+        # `resumable`) keeps getting `_final_summary`'s descriptive summary, byte-identical to before.
+        if prog.status != "failed":
+            prog.message = _final_summary(prog)
         # J-60: close the SAME run-history record this job created at start (one record per job, one
         # transition). A graceful `resumable` pause is NOT a terminal state — its run row is UPDATEd to
         # `resumable` (so it shows that way in Run history AND is skipped by the boot sweep, which only
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 57e7b4a0..157914a5 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -811,6 +811,37 @@ def test_retry_needs_key_source_without_key_is_400(data_api_engine, monkeypatch)
     assert "requires a key" in str(exc.value.detail)
 
 
+@pytest.mark.parametrize("launch_exc", [RuntimeError("can't start new thread"), MemoryError()])
+def test_retry_thread_launch_failure_is_503(data_api_engine, monkeypatch, launch_exc):
+    """TC-9 (ops-hardening iter-44, audit B4) — a `data_manager.retry_run` thread-launch failure
+    (`RuntimeError`/`MemoryError`, the same two exits `threading.Thread.start()` takes under the
+    `ulimit -v` ceiling — see `start_job`'s iter-43 AUDIT B3 comment) must return an explicit 503, never a
+    bare 500 or a fabricated 200 `"status": "running"`, matching `start_job`/`resume_job`'s existing
+    contract so all three job-launch endpoints share one honest-error contract."""
+    from app.api.data import retry_job
+    with Session(data_api_engine) as session:
+        run = DataProviderRun(
+            provider="yahoo", started_at=datetime(2024, 1, 3), finished_at=datetime(2024, 1, 3),
+            symbols_ok=1, symbols_failed=1, status="partial",
+            message=json.dumps({"kind": "fetch", "start": "2024-01-02", "end": "2024-01-03", "summary": "partial"}),
+        )
+        session.add(run)
+        session.commit()
+        session.refresh(run)
+        run_id = run.id
+
+    def _raise(*_a, **_k):
+        raise launch_exc
+
+    monkeypatch.setattr(data_manager, "retry_run", _raise)
+
+    with Session(data_api_engine) as session:
+        with pytest.raises(HTTPException) as exc:
+            retry_job(run_id, payload=ResumeRequest(), session=session)
+    assert exc.value.status_code == 503
+    assert "retry" in str(exc.value.detail).lower()
+
+
 def test_dismiss_run_endpoint_soft_dismisses(data_api_engine):
     """POST /api/data/jobs/{id}/dismiss (record_type=run) soft-dismisses; the run leaves unfinished_imports
     but stays in Run history."""
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index d8926495..3b8e46a6 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -5396,3 +5396,100 @@ def test_retry_run_unknown_and_non_retryable(tmp_path):
         ok_id = run.id
     with pytest.raises(ValueError):
         retry_run(ok_id, config=cfg, engine=engine)
+
+
+# ==================================================================================================
+# ops-hardening iter-44 (reviewer MINOR, carried from iter-43 B5) — TC-10: `_run_job`'s `finally` block
+# must not clobber a `failed` job's real captured-exception message with `_final_summary`'s generic
+# "work done" text; a normally-completed job's `_final_summary` text is unaffected.
+# ==================================================================================================
+def test_run_job_outer_exception_preserves_real_message_not_final_summary(tmp_path, monkeypatch):
+    """TC-10 — a job that fails via `_run_job`'s OUTER exception handler (a whole-stage exception, not a
+    per-date J-67-isolated one) must persist a `message` naming the REAL captured exception text, not
+    `_final_summary`'s generic "no work performed"/all-zeros summary. `_trading_days` is monkeypatched to
+    raise: it is the very first call `_do_backfill` makes (`data_manager.py`'s own docstring names it as
+    the canonical "whole-stage exception" example), well before any per-date failure isolation engages —
+    so this genuinely exercises the OUTER handler, not a graded `partial`. Before this iteration,
+    `_run_job`'s `finally` unconditionally set `prog.message = _final_summary(prog)`, so this assertion
+    would have failed (iter-43 audit B5: the two expressions were byte-identical on every path)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'run_job_failed.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    def _boom(_session, _cfg):
+        raise RuntimeError("simulated trading-calendar read failure")
+
+    monkeypatch.setattr(data_manager, "_trading_days", _boom)
+
+    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
+    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)
+
+    assert summary["status"] == "failed"
+    assert "simulated trading-calendar read failure" in summary["message"]
+    assert "no work performed" not in summary["message"]
+
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+    assert row.status == "failed"
+    persisted_message = summarize_provider_run(row)["message"]
+    assert "simulated trading-calendar read failure" in persisted_message
+    assert "no work performed" not in persisted_message
+
+
+def test_run_job_normal_completion_still_gets_final_summary(tmp_path):
+    """TC-10 (unchanged half) — a job that completes normally (status `ok`) still gets `_final_summary`'s
+    descriptive summary, byte-identical to before this iteration's `finally`-block change (the conditional
+    only skips the assignment on the `failed` path)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'run_job_ok.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+    cfg = load_config()
+    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
+    cfg = cfg.model_copy(update={"scanner": _sc})
+
+    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
+    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)
+
+    assert summary["status"] == "ok"
+    from app.engine.data_manager import _final_summary as _fs
+
+    prog = data_manager._JOBS[job.job_id]
+    assert summary["message"] == _fs(prog)
+
+
+def test_run_job_textless_exception_still_names_a_real_reason(tmp_path, monkeypatch):
+    """ops-hardening iter-44 AUDIT (B1) — TC-10 for the exception class this session's failures ACTUALLY
+    raise. `str(MemoryError())` is the EMPTY STRING, so the iteration's original `prog.message =
+    scrub(str(exc))` produced `""`, whose falsiness sent `_run_detail`'s `prog.message if (prog.status ==
+    "failed" and prog.message)` guard straight back to `_final_summary`'s generic text — reproducing the
+    EXACT "backfill: 0 snapshots over N dates, 0 forward returns" message the browser lane observed on
+    the live failed run 272 (2026-08-03), i.e. TC-10's fix was a no-op for MemoryError. A textless
+    exception must still persist a reason naming the exception TYPE, never the generic work summary and
+    never a blank error entry."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'run_job_textless.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    def _boom(_session, _cfg):
+        raise MemoryError()  # noqa: RSE102 — the textless-exception case under test
+
+    monkeypatch.setattr(data_manager, "_trading_days", _boom)
+
+    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
+    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)
+
+    assert summary["status"] == "failed"
+    assert "MemoryError" in summary["message"]
+    assert "snapshots over" not in summary["message"]  # never `_final_summary`'s generic text
+    assert summary["errors"] and all(e.strip() for e in summary["errors"])  # never a blank error entry
+
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+    assert row.status == "failed"
+    persisted_message = summarize_provider_run(row)["message"]
+    assert "MemoryError" in persisted_message
+    assert "snapshots over" not in persisted_message
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index 074cb433..ec002443 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -71,6 +71,8 @@ _DEVSCRIPT_BACKEND_PORT = 18700 + _offset
 _DEVSCRIPT_FRONTEND_PORT = 19700 + _offset
 # A FIFTH port for the "caps absent/disabled" launcher test (TC-9) below.
 _NOCAP_TEST_PORT = 18800 + _offset
+# A SIXTH port for the ops-hardening iter-44 ServerOpsCfg-flags fast-shutdown test below.
+_FAST_SHUTDOWN_TEST_PORT = 18900 + _offset
 
 # ops-hardening iter-9 (AG-10): the real, committed host-guard config this project runs under.
 HOST_GUARD_ENV_FILE = REPO_ROOT / "project-extensions" / "host-guard" / "host-guard.env"
@@ -332,6 +334,167 @@ def test_start_backend_logfile_ends_abruptly_after_simulated_crash(spawned_backe
         )
 
 
+def _read_proc_cmdline(pid: int) -> list[str]:
+    with open(f"/proc/{pid}/cmdline", "rb") as fh:
+        raw = fh.read()
+    return [part.decode(errors="replace") for part in raw.split(b"\x00") if part]
+
+
+def test_start_backend_wires_server_ops_cfg_flags_into_uvicorn_cmdline(spawned_backend):
+    """ops-hardening iter-44 TC-1 — `ServerOpsCfg`'s three previously-unwired values
+    (`limit_concurrency` / `timeout_keep_alive_seconds` / `graceful_timeout_seconds`, declared since the
+    mcp-loop session J-100 but never enforced by any launch script until now — a direct read of the
+    `exec` line before this iteration passed only --host/--port/--app-dir) reach the REAL launched
+    uvicorn process's own command line as `--limit-concurrency` / `--timeout-keep-alive` /
+    `--timeout-graceful-shutdown`, each matching `get_config().server` — verified against `/proc/<pid>/
+    cmdline`, never the script's source text."""
+    from app.config import get_config
+
+    cfg = get_config()
+    cmdline = _read_proc_cmdline(spawned_backend.pid)
+
+    def _flag_value(flag: str) -> str:
+        assert flag in cmdline, f"expected {flag!r} in the launched process's cmdline: {cmdline}"
+        return cmdline[cmdline.index(flag) + 1]
+
+    assert _flag_value("--limit-concurrency") == str(cfg.server.limit_concurrency)
+    assert _flag_value("--timeout-keep-alive") == str(cfg.server.timeout_keep_alive_seconds)
+    assert _flag_value("--timeout-graceful-shutdown") == str(cfg.server.graceful_timeout_seconds)
+
+
+# ==================================================================================================
+# ops-hardening iter-44 TC-2 — a backend launched via `start-backend.sh` with a REAL stuck in-flight
+# background task (a heavy backfill's finalize-tail forward-aggregate warm on the throwaway-DB copy —
+# the SAME class of long-running daemon-thread compute J-07 step 1 exercises) self-terminates on SIGTERM
+# within its configured `graceful_timeout_seconds` window, WITHOUT a manual `kill -9`. Uses a scratch
+# config that overrides ONLY `server.graceful_timeout_seconds` to a small test value (never the real
+# committed 120s — this test's own SIGTERM-to-exit budget scales off THAT overridden value, not a
+# hardcoded literal) so the assertion stays fast; every other setting (memory_cap_mb, snapshot_cadence,
+# walk_forward.horizons, etc.) is the REAL committed config, unchanged — mirrors
+# `spawned_backend_throwaway_db`'s own "everything but one field is real" methodology above.
+# ==================================================================================================
+_FAST_GRACEFUL_TIMEOUT_SECONDS = 8
+
+
+@dataclass
+class FastShutdownBackend:
+    pid: int
+    port: int
+
+
+@pytest.fixture()
+def spawned_backend_fast_graceful_timeout(tmp_path):
+    """Like `spawned_backend_throwaway_db`, but ALSO rewrites `server.graceful_timeout_seconds` to
+    `_FAST_GRACEFUL_TIMEOUT_SECONDS` in the scratch config, so a SIGTERM-to-exit test does not have to
+    wait out the real committed 120s. Opt-in via the SAME `TRENDORA_RUN_HEAVY_INGEST_TEST=1` gate as the
+    existing heavy-ingest fixture (a real backfill against a real DB copy is not a fast default-suite
+    test) — never starts by accident, consistent with that fixture's own documented rationale."""
+    if os.environ.get("TRENDORA_RUN_HEAVY_INGEST_TEST") != "1":
+        pytest.skip(
+            "heavy real-process SIGTERM-under-stuck-task test is opt-in — set "
+            "TRENDORA_RUN_HEAVY_INGEST_TEST=1 (run it only on an idle host with the host-guard "
+            "protections active)"
+        )
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    if not REAL_DB.exists():
+        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to copy for a real capacity measurement")
+
+    scratch_db = tmp_path / "throwaway_fast_shutdown.db"
+    for suffix in ("", "-wal", "-shm"):
+        src = Path(str(REAL_DB) + suffix)
+        if src.exists():
+            shutil.copy2(src, Path(str(scratch_db) + suffix))
+
+    scratch_config = tmp_path / "throwaway-fast-shutdown-config.yaml"
+    real_cfg_text = REAL_CONFIG.read_text()
+    new_cfg_text, n_db = re.subn(
+        r'url:\s*"sqlite:///apps/backend/data/trendora\.db"',
+        f'url: "sqlite:///{scratch_db}"',
+        real_cfg_text,
+        count=1,
+    )
+    assert n_db == 1, "expected exactly one database.url line to rewrite in the real config.yaml"
+    new_cfg_text, n_gt = re.subn(
+        r"^(\s*graceful_timeout_seconds:\s*)\d+",
+        rf"\g<1>{_FAST_GRACEFUL_TIMEOUT_SECONDS}",
+        new_cfg_text,
+        count=1,
+        flags=re.MULTILINE,
+    )
+    assert n_gt == 1, "expected exactly one server.graceful_timeout_seconds line to rewrite"
+    scratch_config.write_text(new_cfg_text)
+
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_FAST_SHUTDOWN_TEST_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_FAST_SHUTDOWN_TEST_PORT + 1000)
+    env["TRENDORA_CONFIG"] = str(scratch_config)
+    proc = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        _wait_for_health(_FAST_SHUTDOWN_TEST_PORT, timeout=60.0)
+        yield FastShutdownBackend(pid=proc.pid, port=_FAST_SHUTDOWN_TEST_PORT)
+    finally:
+        if _pid_alive(proc.pid):
+            os.kill(proc.pid, signal.SIGKILL)
+            deadline = time.monotonic() + 10.0
+            while _pid_alive(proc.pid) and time.monotonic() < deadline:
+                time.sleep(0.2)
+        try:
+            proc.wait(timeout=10)
+        except ChildProcessError:
+            pass
+
+
+def test_start_backend_self_terminates_on_sigterm_with_stuck_background_task(
+    spawned_backend_fast_graceful_timeout,
+):
+    """ops-hardening iter-44 TC-2 — with a REAL heavy backfill's finalize-tail forward-aggregate warm
+    in flight (a genuine long-running daemon-thread compute, launched moments before via the real
+    `/api/data/jobs` endpoint), sending SIGTERM to the `start-backend.sh`-launched process makes it exit
+    within `_FAST_GRACEFUL_TIMEOUT_SECONDS` + a small scheduling margin — never requiring a manual
+    `kill -9`. Before this iteration's TC-1 wiring, `--timeout-graceful-shutdown` was never passed to
+    uvicorn at all, so a stuck background task could hold the process hostage indefinitely (the live
+    iter-43 incident this closes: `logs/backend.log`, "the process needed kill -9")."""
+    from app.config import get_config
+
+    backend = spawned_backend_fast_graceful_timeout
+    cfg = get_config()
+
+    # Trigger a REAL backfill for a genuinely unsnapshotted trading day (selected at run time from this
+    # spawned instance's own availability map — a hardcoded date silently decays into a zero-work no-op
+    # the moment anything snapshots it, mirroring the existing heavy-ingest fixture's own T3 audit fix).
+    backfill_date = _pick_unsnapshotted_trading_day(backend.port, cfg)
+    job_id = _post_job(backend.port, "backfill", backfill_date, backfill_date)
+
+    # Give the job a moment to genuinely be mid-flight (past its cheap validation, into real per-date
+    # compute) before sending SIGTERM — this is a "stuck in-flight background task" test, not a "job
+    # never started" test.
+    time.sleep(2.0)
+    status_before = httpx.get(f"http://127.0.0.1:{backend.port}/api/data/jobs/{job_id}", timeout=10.0)
+    assert status_before.json().get("status") == "running", (
+        f"expected the backfill to still be running 2s after trigger (a genuine in-flight task), "
+        f"got {status_before.json()}"
+    )
+
+    t0 = time.monotonic()
+    os.kill(backend.pid, signal.SIGTERM)
+    deadline = t0 + _FAST_GRACEFUL_TIMEOUT_SECONDS + 15.0  # generous scheduling margin, never a kill -9
+    while _pid_alive(backend.pid) and time.monotonic() < deadline:
+        time.sleep(0.2)
+    elapsed = time.monotonic() - t0
+
+    assert not _pid_alive(backend.pid), (
+        f"process (pid {backend.pid}) was still alive {elapsed:.1f}s after SIGTERM — exceeded its own "
+        f"configured graceful_timeout_seconds={_FAST_GRACEFUL_TIMEOUT_SECONDS}s + margin; a manual "
+        f"kill -9 would have been required (the exact TC-2 regression)"
+    )
+    print(f"\n[TC-2] SIGTERM-to-exit elapsed={elapsed:.2f}s (configured graceful_timeout_seconds="
+          f"{_FAST_GRACEFUL_TIMEOUT_SECONDS}s)")
+
+
 # ==================================================================================================
 # ops-hardening iter-8 (J-05 REGRESSION recovery, TC-1/TC-2): a REAL back-to-back heavy ingest — a
 # full-universe `rebuild` immediately followed by a second heavy `backfill` in the SAME long-lived
diff --git a/incredible_auto_dev/scripts/start-backend.sh b/incredible_auto_dev/scripts/start-backend.sh
index f277e24c..446ae0c0 100755
--- a/incredible_auto_dev/scripts/start-backend.sh
+++ b/incredible_auto_dev/scripts/start-backend.sh
@@ -34,11 +34,19 @@ fi
 # anywhere in it) — do not trust reports/perf-budgets.md's or config.yaml's prose claiming otherwise; this
 # is where the enforcement actually lives now. Values come from config.yaml via the venv Python (No magic
 # numbers — the same `app.config.get_config()` every engine reads).
-read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE <<< "$(
+#
+# ops-hardening iter-44 — same read now also pulls `ServerOpsCfg`'s three uvicorn-facing values
+# (`limit_concurrency` / `timeout_keep_alive_seconds` / `graceful_timeout_seconds`), declared since the
+# mcp-loop session (J-100) but never enforced by any launch script until now (a direct read of the `exec`
+# line below, prior to this change, passed only --host/--port/--app-dir). Wiring these gives a stuck
+# in-flight task's shutdown a deadline (`--timeout-graceful-shutdown`) instead of holding the process
+# hostage forever, and bounds concurrent connections/idle keep-alive the same way the memory cap bounds
+# RAM — additive to, never a replacement for, the ulimit/host-guard enforcement below (AG-10).
+read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE LIMIT_CONCURRENCY TIMEOUT_KEEP_ALIVE GRACEFUL_TIMEOUT <<< "$(
   "$REPO_ROOT/apps/backend/.venv/bin/python" -c '
 from app.config import get_config
 cfg = get_config()
-print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
+print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max, cfg.server.limit_concurrency, cfg.server.timeout_keep_alive_seconds, cfg.server.graceful_timeout_seconds)
 '
 )"
 
@@ -96,4 +104,7 @@ exec "${HOST_GUARD_CMD_PREFIX[@]}" "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" m
   --host 0.0.0.0 \
   --port "$PORT" \
   --app-dir "$REPO_ROOT/apps/backend" \
+  --limit-concurrency "$LIMIT_CONCURRENCY" \
+  --timeout-keep-alive "$TIMEOUT_KEEP_ALIVE" \
+  --timeout-graceful-shutdown "$GRACEFUL_TIMEOUT" \
   >> "$LOG_FILE" 2>&1
```
