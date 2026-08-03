# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 24505691..6b83c145 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -188,11 +188,19 @@ def start_job(payload: JobCreate, session: Session = Depends(get_session)) -> di
     symbols = None
     if payload.symbols:
         symbols = [s.strip() for s in payload.symbols if s and s.strip()] or None
-    job_id = data_manager.start_data_job(
-        payload.kind, payload.start, payload.end,
-        source=source, api_key=payload.api_key, config=cfg, engine=get_engine(),
-        symbols=symbols,
-    )
+    # ops-hardening iter-43 (J-05 regression fix): a failure to LAUNCH the worker thread (e.g.
+    # `RuntimeError: can't start new thread`) is recorded honestly on the job by `start_data_job` itself
+    # (status `failed`, a descriptive message) and re-raised here so this endpoint returns an explicit
+    # error — never a 200 `"status": "running"` over a job that never started (goal.md's "Zero silent
+    # zero-work jobs"). Mirrors the file's own existing idiom two lines above `start_job`'s own 503.
+    try:
+        job_id = data_manager.start_data_job(
+            payload.kind, payload.start, payload.end,
+            source=source, api_key=payload.api_key, config=cfg, engine=get_engine(),
+            symbols=symbols,
+        )
+    except RuntimeError as exc:
+        raise HTTPException(status_code=503, detail=f"failed to launch job worker: {exc}") from exc
     return {
         "job_id": job_id,
         "kind": payload.kind,
@@ -251,7 +259,14 @@ def resume_job(
             status_code=400,
             detail=f"source {checkpoint.source!r} requires a key; set ${entry.env_var} or paste a session key",
         )
-    data_manager.start_resume_job(import_id, api_key=api_key, config=cfg, engine=get_engine())
+    # ops-hardening iter-43 (J-05 regression fix): same honest-error contract as `start_job` above — a
+    # thread-launch failure is already recorded on the resumed job's run-history row by
+    # `start_resume_job`/`_fail_unlaunched_resume`; re-raised here so this endpoint never returns a 200
+    # over a resume that never started.
+    try:
+        data_manager.start_resume_job(import_id, api_key=api_key, config=cfg, engine=get_engine())
+    except RuntimeError as exc:
+        raise HTTPException(status_code=503, detail=f"failed to launch resume worker: {exc}") from exc
     return {"import_id": import_id, "source": checkpoint.source, "status": "running"}
 
 
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 08b63ea3..7f155c9a 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -4640,6 +4640,55 @@ def resume_data_job(
     )
 
 
+def _fail_unlaunched_job(prog: JobProgress, cfg: Config, eng: Engine, exc: BaseException) -> None:
+    """ops-hardening iter-43 (J-05 regression fix) — a `threading.Thread(...).start()` failure (the live
+    incident: `RuntimeError: can't start new thread`) happens OUTSIDE `_run_job`'s own outer `except
+    Exception` handler (`:4504-4506`), which only ever runs INSIDE the thread body once it is running.
+    Left unguarded, the just-created job stays at its `create_job()`-time `running` default forever — a
+    silent zero-work job goal.md's own "Zero silent zero-work jobs" promise forbids. Mirrors `_run_job`'s
+    OWN failure mechanism (`prog.status = "failed"` + `_record_error`) so both the live in-memory registry
+    (a poller's `GET /api/data/jobs/{id}`) and the persisted run-history row read the SAME honest outcome
+    every other job failure already produces. `_finalize_run_record`'s own documented no-open-row fallback
+    (an INSERT, not an UPDATE) is exactly the right shape here, since a launch failure never reaches
+    `_create_run_record` (that only runs inside `_run_job`, on the thread that never started)."""
+    prog.status = "failed"
+    _record_error(prog, f"failed to launch job worker thread: {exc}")
+    prog.finished_at = _utcnow()
+    with _LOCK:
+        # Ensures a live poller sees the failure even when the caller (a resume) never registered this
+        # `prog` itself — see `_fail_unlaunched_resume`. A no-op re-assignment for the normal
+        # `start_data_job` case, where `create_job()` already registered this exact object.
+        _JOBS[prog.job_id] = prog
+    try:
+        _finalize_run_record(eng, cfg, prog)
+    except Exception:  # noqa: BLE001 — persistence failure must not crash the launch-failure path further
+        logger.exception("failed to persist run summary for unlaunched job %s", prog.job_id)
+
+
+def _fail_unlaunched_resume(import_id: str, cfg: Config, eng: Engine, exc: BaseException) -> None:
+    """The RESUME sibling of `_fail_unlaunched_job`. Unlike `start_data_job` (whose `create_job()` already
+    registered a `JobProgress` before `thread.start()` is attempted), a resume's `JobProgress` is normally
+    built INSIDE `resume_data_job` (the thread target) from the durable checkpoint — since the thread never
+    ran, nothing has built or registered one yet. Rebuilds the SAME minimal shape `resume_data_job` itself
+    would have (`JobProgress(job_id=cp.import_id, kind=cp.kind, start=cp.start, end=cp.end,
+    source=cp.source)`) so the EXISTING open run-history row (left `resumable`/`running` by the paused
+    attempt this resume was trying to continue) is closed to `failed` via the same mechanism, instead of
+    staying open forever. The caller (`POST /api/data/jobs/{import_id}/resume`) already validated the
+    checkpoint exists and is resumable before calling `start_resume_job`, so a missing checkpoint here is
+    defensive only."""
+    try:
+        with Session(eng) as session:
+            cp = _load_checkpoint(session, import_id)
+        if cp is None:
+            logger.error("cannot record unlaunched-resume failure — unknown checkpoint %s", import_id)
+            return
+        prog = JobProgress(job_id=cp.import_id, kind=cp.kind, start=cp.start, end=cp.end, source=cp.source)
+    except Exception:  # noqa: BLE001 — never let this bookkeeping path itself crash the launch-failure path
+        logger.exception("failed to rebuild job progress for unlaunched resume %s", import_id)
+        return
+    _fail_unlaunched_job(prog, cfg, eng, exc)
+
+
 def start_data_job(
     kind: str,
     start: date_cls,
@@ -4679,7 +4728,13 @@ def start_data_job(
         daemon=True,
         name=f"data-job-{job.job_id}",
     )
-    thread.start()
+    try:
+        thread.start()
+    except RuntimeError as exc:
+        # ops-hardening iter-43 (J-05 regression fix) — see `_fail_unlaunched_job`. Re-raised so the
+        # caller (`POST /api/data/jobs`) can return an honest error instead of a 200 over a dead job.
+        _fail_unlaunched_job(job, cfg, eng, exc)
+        raise
     return job.job_id
 
 
@@ -4702,7 +4757,14 @@ def start_resume_job(
         daemon=True,
         name=f"data-resume-{import_id}",
     )
-    thread.start()
+    try:
+        thread.start()
+    except RuntimeError as exc:
+        # ops-hardening iter-43 (J-05 regression fix) — see `_fail_unlaunched_resume`. Re-raised so the
+        # caller (`POST /api/data/jobs/{import_id}/resume`) can return an honest error instead of a 200
+        # over a resume that never started.
+        _fail_unlaunched_resume(import_id, cfg, eng, exc)
+        raise
     return import_id
 
 
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index 8f4e4774..1752e7aa 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -239,41 +239,56 @@ class _BarCache:
         `.prefill(session)` call with no argument) keeps the prior unconditional whole-table scan,
         byte-identical to before this change. An empty (but non-None) `expected_symbols` short-circuits to
         zero rows without issuing a malformed `WHERE symbol IN ()` — mirrors `load_only`'s own empty-list
-        guard."""
+        guard. [Superseded by iter-43 below — the filter this paragraph documents is REVERTED; kept as the
+        historical record of what was tried.]
+
+        iter-43 (REVERT, this iteration): the `WHERE symbol IN (...)` filter above is REMOVED — `prefill`
+        is back to the unconditional whole-table scan for EVERY `expected_symbols` value (`None`, a
+        non-empty list, or `[]`), byte-identical to the pre-iter-42 shape (proven by `test_bar_cache.py`'s
+        byte-identity oracle, TC-1). The iter-42 auditor's finding B2 (`reports/perf-budgets.md`,
+        iteration-42 section, "AUDIT CORRECTION") re-measured the filter's cost over the WHOLE job it runs
+        inside, not `prefill` in isolation: the 36 excluded ETF/index/sector symbols (SPY, QQQ, the XL*
+        sector SPDRs, `^VIX`, etc.) that `sectors.py`/`themes.py`/`regime.py`/`market_phase.py` read on
+        every snapshot date fell into the lazy per-symbol `list[Bar]` path iter-41's `_SymbolColumns` (B5)
+        specifically exists to avoid (~3.3x more bytes/row) — a net **+5.1% peak-memory REGRESSION**, not
+        the 2.5% reduction iter-42's own narrower measurement claimed. `_SymbolColumns` (B5) and the
+        NULL-tolerance sentinel substitution (B6) are UNCHANGED by this revert — only the filtering layer
+        comes out. `_BarCache.prefill` remains a COMPRESSION of the whole-table load (smaller bytes/row
+        than `list[Bar]`), not a BOUND on row count — the owner's separate 2026-07-31 `memory_cap_mb`
+        6144->8192 amendment is what restores headroom for the reverted unconditional scan; this revert
+        does not itself change the function's O(table) footprint."""
         with self._load_lock:
             need_scan = not self._prefilled
         if need_scan:
             batch = get_config().research.read_batch_size
-            symbol_filter = sorted(set(expected_symbols)) if expected_symbols is not None else None
             by_symbol: dict[str, _SymbolColumns] = {}
-            if symbol_filter is None or symbol_filter:
-                stmt = (
-                    select(
-                        DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
-                        DailyPrice.low, DailyPrice.close, DailyPrice.volume,
-                    )
-                    .order_by(DailyPrice.symbol, DailyPrice.date)
+            # iter-43 (REVERT): unconditional whole-table scan regardless of `expected_symbols` — the
+            # iter-42 `WHERE symbol IN (...)` filter is removed (see the docstring's iter-43 paragraph).
+            stmt = (
+                select(
+                    DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
+                    DailyPrice.low, DailyPrice.close, DailyPrice.volume,
                 )
-                if symbol_filter is not None:
-                    stmt = stmt.where(DailyPrice.symbol.in_(symbol_filter))
-                for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
-                    cols = by_symbol.get(symbol)
-                    if cols is None:
-                        cols = _SymbolColumns(
-                            [], array.array("d"), array.array("d"), array.array("d"),
-                            array.array("d"), array.array("d"),
-                        )
-                        by_symbol[symbol] = cols
-                    cols.dates.append(d)
-                    # iter-42 (B6, AG-8): substitute the honest NA sentinel for a NULL numeric field
-                    # instead of letting `array.array('d').append(None)` raise `TypeError` — see the
-                    # module-level `_NULL_NUMERIC_SENTINEL` comment. Unreachable on the current NOT
-                    # NULL schema; a defensive degrade for a future widening, not a live bug fix.
-                    cols.opens.append(o if o is not None else _NULL_NUMERIC_SENTINEL)
-                    cols.highs.append(h if h is not None else _NULL_NUMERIC_SENTINEL)
-                    cols.lows.append(lo if lo is not None else _NULL_NUMERIC_SENTINEL)
-                    cols.closes.append(c if c is not None else _NULL_NUMERIC_SENTINEL)
-                    cols.volumes.append(v if v is not None else _NULL_NUMERIC_SENTINEL)
+                .order_by(DailyPrice.symbol, DailyPrice.date)
+            )
+            for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
+                cols = by_symbol.get(symbol)
+                if cols is None:
+                    cols = _SymbolColumns(
+                        [], array.array("d"), array.array("d"), array.array("d"),
+                        array.array("d"), array.array("d"),
+                    )
+                    by_symbol[symbol] = cols
+                cols.dates.append(d)
+                # iter-42 (B6, AG-8): substitute the honest NA sentinel for a NULL numeric field
+                # instead of letting `array.array('d').append(None)` raise `TypeError` — see the
+                # module-level `_NULL_NUMERIC_SENTINEL` comment. Unreachable on the current NOT
+                # NULL schema; a defensive degrade for a future widening, not a live bug fix.
+                cols.opens.append(o if o is not None else _NULL_NUMERIC_SENTINEL)
+                cols.highs.append(h if h is not None else _NULL_NUMERIC_SENTINEL)
+                cols.lows.append(lo if lo is not None else _NULL_NUMERIC_SENTINEL)
+                cols.closes.append(c if c is not None else _NULL_NUMERIC_SENTINEL)
+                cols.volumes.append(v if v is not None else _NULL_NUMERIC_SENTINEL)
             # publish atomically under the lock so a concurrent reader sees a fully-built map, not a
             # partial one; re-check `_prefilled` in case another thread raced us to the scan (rare —
             # `_BarCache` is normally driven by one orchestrating thread — but the merge below is
diff --git a/apps/backend/tests/test_bar_cache.py b/apps/backend/tests/test_bar_cache.py
index 48510dbf..869faf09 100644
--- a/apps/backend/tests/test_bar_cache.py
+++ b/apps/backend/tests/test_bar_cache.py
@@ -145,16 +145,16 @@ def test_prefill_old_vs_new_implementation_byte_identical(tiny_engine):
         assert list(new_by_symbol[symbol]) == list(old_by_symbol[symbol])
 
 
-def test_prefill_symbol_filtered_query_when_expected_symbols_given(tiny_engine):
-    """iter-42 (bound attempt #5, AG-8): `prefill(expected_symbols=...)` issues a `WHERE symbol IN
-    (...)`-filtered query -- mirroring `load_only`'s already-proven shape -- instead of the
-    unconditional whole-table scan `expected_symbols=None` still uses. Proves the filtered path is
-    GENUINELY engaged (the iter-37 lesson: assert the condition was actually live, not merely present
-    in the code): SPY has real bars in this fixture but is NOT named in `expected_symbols`, so it must
-    be entirely ABSENT from the cache immediately after `prefill` -- the eager scan really did skip
-    it, this isn't a no-op filter. SPY then falls back to the EXISTING lazy per-symbol load on first
-    access (unchanged by this iteration), loading with exactly ONE additional query and serving a
-    value byte-identical to a full-scan prefill's own result for that symbol."""
+def test_prefill_expected_symbols_no_longer_filters_the_eager_scan(tiny_engine):
+    """iter-43 (REVERT): `prefill(expected_symbols=...)` no longer filters its SELECT — TC-1's
+    byte-identity oracle against the pre-iter-42 (unfiltered) reference body. Proves the revert is
+    GENUINELY engaged (the iter-37 lesson, applied in reverse this time: assert the REMOVED condition
+    is truly gone, not merely absent from the diff): SPY has real bars in this fixture and is NOT named
+    in `expected_symbols=["AAA"]`, yet it must be FULLY PRESENT in the cache immediately after
+    `prefill` returns — the eager scan loads the whole table regardless of `expected_symbols`, exactly
+    like the `expected_symbols=None` case. A subsequent `bars_asof(session, "SPY", ...)` read issues
+    ZERO additional queries (SPY was never lazily loaded — it was already eagerly scanned), unlike the
+    iter-42 shape this test replaces (which required exactly one lazy-load query for SPY)."""
     engine, days = tiny_engine
     with Session(engine) as reference_session:
         reference_spy = [
@@ -172,17 +172,20 @@ def test_prefill_symbol_filtered_query_when_expected_symbols_given(tiny_engine):
     with Session(engine) as session:
         cache = prices._BarCache()
         cache.prefill(session, expected_symbols=["AAA"])
-        # LIVE proof the filter genuinely engaged: SPY has real bars in this fixture but was excluded
-        # from expected_symbols, so it must be ABSENT from the eager scan's result set.
-        assert set(cache._by_symbol) == {"AAA"}, (
-            f"SPY should be excluded from the filtered eager scan, got {set(cache._by_symbol)}"
+        # LIVE proof the filter is genuinely gone: SPY was excluded from expected_symbols but must be
+        # present anyway — the eager scan is unconditional again, byte-identical to expected_symbols=None.
+        assert set(cache._by_symbol) == {"AAA", "SPY"}, (
+            f"SPY must be present after the revert (no filtering), got {set(cache._by_symbol)}"
         )
         aaa_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in cache._by_symbol["AAA"]]
+        spy_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in cache._by_symbol["SPY"]]
         assert aaa_bars == reference_aaa
+        assert spy_bars == reference_spy
         assert all(isinstance(b, prices.Bar) for b in cache._by_symbol["AAA"])
+        assert all(isinstance(b, prices.Bar) for b in cache._by_symbol["SPY"])
 
-        # SPY was never in expected_symbols -> the unchanged lazy per-symbol path loads it on first
-        # access: exactly ONE additional query, byte-identical result.
+        # SPY was never in expected_symbols, but it was already eagerly loaded -> reading it now issues
+        # ZERO additional queries (no lazy per-symbol fallback needed, unlike the pre-revert shape).
         calls = {"n": 0}
         orig_exec = session.exec
 
@@ -195,23 +198,42 @@ def test_prefill_symbol_filtered_query_when_expected_symbols_given(tiny_engine):
             (b.date, b.open, b.high, b.low, b.close, b.volume)
             for b in cache.bars_asof(session, "SPY", days[-1])
         ]
-        assert calls["n"] == 1, "SPY must lazy-load with exactly one query (the eager scan skipped it)"
+        assert calls["n"] == 0, (
+            f"SPY was already eagerly loaded by the unconditional scan — a read must issue no query, "
+            f"got {calls['n']}"
+        )
         assert spy_via_cache == reference_spy
-        cache.bars_asof(session, "SPY", days[-1])  # second access: load-once holds, no re-query
-        assert calls["n"] == 1
 
 
-def test_prefill_empty_expected_symbols_loads_nothing_no_malformed_query(tiny_engine):
-    """`expected_symbols=[]` (a genuinely empty, but non-None, candidate set) must short-circuit to
-    zero eagerly-loaded rows without ever issuing a malformed `WHERE symbol IN ()` -- mirrors
-    `load_only`'s own empty-list guard. Distinct from `expected_symbols=None` (unconditional full scan,
-    proven by other tests in this file)."""
+def test_prefill_empty_expected_symbols_still_loads_full_table(tiny_engine):
+    """iter-43 (REVERT): `expected_symbols=[]` (a genuinely empty, but non-None, candidate set) no
+    longer short-circuits to zero eagerly-loaded rows -- that iter-42 guard is removed along with the
+    filter it protected. Post-revert, `[]` behaves EXACTLY like `expected_symbols=None`: the
+    unconditional whole-table scan still runs and loads every symbol (byte-identical to the reference
+    query), and the empty `expected_symbols` list only affects the SEPARATE "record a zero-bar
+    candidate" bookkeeping loop at the end of `prefill` (a no-op here, since the list is empty) --
+    never the SELECT itself."""
     engine, days = tiny_engine
+    with Session(engine) as reference_session:
+        reference = [
+            (bar.symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
+            for bar in reference_session.exec(
+                select(DailyPrice).order_by(DailyPrice.symbol, DailyPrice.date)
+            ).all()
+        ]
     with Session(engine) as session:
         cache = prices._BarCache()
         cache.prefill(session, expected_symbols=[])
-        assert cache._by_symbol == {}
-        assert cache._prefilled is True  # the (empty) scan still ran/completed once
+        assert set(cache._by_symbol) == {"AAA", "SPY"}, (
+            f"the full table must load even with an empty expected_symbols list, got {set(cache._by_symbol)}"
+        )
+        loaded = [
+            (symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
+            for symbol in sorted(cache._by_symbol)
+            for bar in cache._by_symbol[symbol]
+        ]
+        assert loaded == reference
+        assert cache._prefilled is True  # the (now-unconditional) scan still ran/completed once
 
 
 def test_prefill_null_numeric_column_degrades_without_crashing(tiny_engine):
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 0fa5ec17..5a35693c 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -5000,6 +5000,84 @@ def unfinished_engine(tmp_path):
     return engine
 
 
+# ==================================================================================================
+# ops-hardening iter-43 (J-05 regression fix) — a `threading.Thread.start()` launch failure must not
+# orphan a job at its `create_job()`-time `running` default forever.
+# ==================================================================================================
+def test_start_data_job_thread_launch_failure_marks_job_failed(tmp_path, monkeypatch):
+    """TC-3: `threading.Thread.start()` raising `RuntimeError` (the live incident: "can't start new
+    thread", `logs/backend.log:153050-153075`) inside `start_data_job` must not leave the just-created
+    job at `running` with zero further updates. The failure reaches BOTH the live in-memory registry (a
+    poller's `GET /api/data/jobs/{id}`) and the persisted run-history row (`GET /api/data`'s Run history
+    panel) as `failed`, with a message naming the thread-launch failure — and the original exception
+    propagates to the caller so the HTTP layer can return an honest error instead of a 200."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'launch_fail.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    created: dict = {}
+    real_create_job = data_manager.create_job
+
+    def _spy_create_job(*a, **kw):
+        job = real_create_job(*a, **kw)
+        created["job"] = job
+        return job
+
+    def _raise_cannot_start_thread(self):
+        raise RuntimeError("can't start new thread")
+
+    monkeypatch.setattr(data_manager, "create_job", _spy_create_job)
+    monkeypatch.setattr("threading.Thread.start", _raise_cannot_start_thread)
+
+    with pytest.raises(RuntimeError, match="can't start new thread"):
+        data_manager.start_data_job("backfill", date(2024, 1, 2), date(2024, 1, 2), config=cfg, engine=engine)
+
+    assert "job" in created, "create_job must have run (and been captured) before the launch failure"
+    prog = created["job"]
+    assert prog.status == "failed"
+    assert any("failed to launch job worker thread" in e for e in prog.errors), prog.errors
+    assert prog.finished_at is not None
+    # the live in-memory registry (what a concurrent poller sees) reflects the SAME object.
+    assert data_manager.get_job(prog.job_id)["status"] == "failed"
+
+    with Session(engine) as session:
+        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == prog.job_id)).one()
+    assert row.status == "failed"
+    assert row.finished_at is not None
+
+
+def test_start_resume_job_thread_launch_failure_marks_job_failed(unfinished_engine, monkeypatch):
+    """TC-4: the same mocked `threading.Thread.start()` failure inside `start_resume_job` closes the
+    resumed import's run-history row to `failed` with a descriptive message via the SAME mechanism.
+    `resume_data_job` (the thread target) is normally what builds this job's `JobProgress` from its
+    checkpoint — since the thread never starts, the guard rebuilds the same minimal shape from the
+    checkpoint directly, so the row is honestly closed instead of staying open (`resumable`/`running`)
+    forever."""
+    engine = unfinished_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        _add_resumable_checkpoint(session, "cp-launch-fail")
+
+    def _raise_cannot_start_thread(self):
+        raise RuntimeError("can't start new thread")
+
+    monkeypatch.setattr("threading.Thread.start", _raise_cannot_start_thread)
+
+    with pytest.raises(RuntimeError, match="can't start new thread"):
+        data_manager.start_resume_job("cp-launch-fail", config=cfg, engine=engine)
+
+    # the live in-memory registry now carries the failure too (nothing registered it before the launch
+    # attempt — the guard is what creates this entry).
+    assert data_manager.get_job("cp-launch-fail")["status"] == "failed"
+
+    with Session(engine) as session:
+        row = session.exec(
+            select(DataProviderRun).where(DataProviderRun.job_id == "cp-launch-fail")
+        ).one()
+    assert row.status == "failed"
+    assert row.finished_at is not None
+
+
 def test_unfinished_imports_union(unfinished_engine):
     """The union = resumable checkpoints + partial/failed runs, MINUS soft-dismissed runs and MINUS a
     plain seed-load (non-job) row. Each carries a plain-language state + the right actions."""
diff --git a/apps/backend/tests/test_start_frontend_script.py b/apps/backend/tests/test_start_frontend_script.py
index 30f26927..7b39960d 100644
--- a/apps/backend/tests/test_start_frontend_script.py
+++ b/apps/backend/tests/test_start_frontend_script.py
@@ -524,3 +524,186 @@ def test_broken_source_fails_build_and_leaves_no_stray_process(launcher):
 
     with pytest.raises(AssertionError):
         _owning_pid(_TC3_PORT, timeout=3.0)
+
+
+# ==================================================================================================
+# ops-hardening iter-43 (goal.md "Additional binding notes", the iter-33/i owner item) -- TC-5:
+# start-frontend.sh now carries the SAME HOST-GUARD cap block scripts/start-backend.sh already applies.
+# Mirrors test_start_backend_script.py's own `_read_host_guard_env` / `_parse_cpu_list` /
+# `_read_proc_status_cpus_allowed` / `_read_proc_environ` helpers exactly (duplicated, not imported --
+# this module's own established convention; see e.g. `_owning_pid` above).
+# ==================================================================================================
+HOST_GUARD_ENV_FILE = REPO_ROOT / "project-extensions" / "host-guard" / "host-guard.env"
+_HOST_GUARD_BLAS_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
+_HG_TEST_PORT = 21300 + _offset
+
+
+def _read_host_guard_env(path: Path) -> dict[str, str]:
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
+
+
+def _read_proc_environ(pid: int) -> dict[str, str]:
+    with open(f"/proc/{pid}/environ", "rb") as fh:
+        raw = fh.read()
+    env: dict[str, str] = {}
+    for entry in raw.split(b"\x00"):
+        if b"=" in entry:
+            k, _, v = entry.partition(b"=")
+            env[k.decode(errors="replace")] = v.decode(errors="replace")
+    return env
+
+
+def test_start_frontend_applies_host_guard_and_skips_when_absent_or_disabled(tmp_path):
+    """TC-5 -- `scripts/start-frontend.sh` carries the SAME HOST-GUARD cap block
+    `scripts/start-backend.sh` already applies. Three cases share ONE real `next build` (against a
+    single scratch dist dir) so only the FIRST boot pays the full build cost -- every later boot in
+    this test takes the existing skip-rebuild fast path (seconds, not minutes):
+
+      1. enabled (the real committed host-guard.env) -> the `next start` worker's CPU affinity matches
+         `HOST_GUARD_CPU_LIST` and its environment carries the BLAS/OMP/numexpr thread-cap vars.
+      2. absent (HOST_GUARD_ENV_FILE points at a nonexistent path, never the real committed file) -> no
+         CPU-affinity restriction, no BLAS/OMP env change.
+      3. disabled (a scratch copy of the real file with ONLY HOST_GUARD_ENABLED=0 changed) -> same as (2).
+    """
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+    if not HOST_GUARD_ENV_FILE.exists():
+        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present -- host-guard is optional, nothing to verify")
+    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
+    if hg.get("HOST_GUARD_ENABLED") != "1":
+        pytest.skip("HOST_GUARD_ENABLED != 1 in the committed host-guard.env -- nothing to verify")
+
+    dist_rel = _scratch_dist_name("hg")
+    own_cpus = os.sched_getaffinity(0)
+    ambient_blas = {v: os.environ.get(v) for v in _HOST_GUARD_BLAS_VARS}
+
+    def _boot(port: int, log_name: str, extra_env: dict) -> _Launcher:
+        log_path = tmp_path / log_name
+        env = dict(os.environ)
+        env["CHAIN_FRONTEND_PORT"] = str(port)
+        env["CHAIN_BACKEND_PORT"] = str(port + 1000)
+        env["NEXT_DIST_DIR"] = dist_rel
+        env.update(extra_env)
+        log_fh = open(log_path, "wb")
+        proc = subprocess.Popen(
+            ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+            stdout=log_fh, stderr=subprocess.STDOUT, preexec_fn=os.setsid,
+        )
+        return _Launcher(proc, log_path, log_fh, FRONTEND_DIR / dist_rel)
+
+    # --- case 1: enabled (real committed host-guard.env) -- pays for the one real build in this test ---
+    launched = _boot(_HG_TEST_PORT, "hg-enabled.log", {})
+    try:
+        _wait_for_port_answering(
+            _HG_TEST_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
+        )
+        assert (launched.dist_abs / "BUILD_ID").exists(), "expected the shared build to produce a BUILD_ID"
+        pid = _owning_pid(_HG_TEST_PORT)
+        expected_cpus = _parse_cpu_list(hg["HOST_GUARD_CPU_LIST"])
+        actual_cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
+        assert actual_cpus == expected_cpus, (
+            f"expected Cpus_allowed_list {sorted(expected_cpus)}, got {sorted(actual_cpus)}"
+        )
+        env = _read_proc_environ(pid)
+        for var in _HOST_GUARD_BLAS_VARS:
+            assert env.get(var) == hg["HOST_GUARD_BLAS_THREADS"], (
+                f"expected {var}={hg['HOST_GUARD_BLAS_THREADS']!r}, got {env.get(var)!r}"
+            )
+    finally:
+        launched.stop()
+
+    # --- case 2: absent (nonexistent HOST_GUARD_ENV_FILE, never the real committed file) ---
+    missing = tmp_path / "no-such-host-guard.env"
+    assert not missing.exists()
+    launched = _boot(_HG_TEST_PORT + 1, "hg-absent.log", {"HOST_GUARD_ENV_FILE": str(missing)})
+    try:
+        _wait_for_port_answering(
+            _HG_TEST_PORT + 1, timeout=_START_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
+        )
+        pid = _owning_pid(_HG_TEST_PORT + 1)
+        cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
+        assert cpus == own_cpus, "no CPU-affinity restriction should apply when host-guard.env is absent"
+        penv = _read_proc_environ(pid)
+        for var, ambient_val in ambient_blas.items():
+            assert penv.get(var) == ambient_val, (
+                f"host-guard.env absent must not change {var} (ambient {ambient_val!r}, got {penv.get(var)!r})"
+            )
+    finally:
+        launched.stop()
+
+    # --- case 3: disabled (scratch copy, ONLY HOST_GUARD_ENABLED=0 changed) ---
+    real_text = HOST_GUARD_ENV_FILE.read_text()
+    disabled_text, n = re.subn(
+        r"^HOST_GUARD_ENABLED=.*$", "HOST_GUARD_ENABLED=0", real_text, count=1, flags=re.MULTILINE
+    )
+    assert n == 1, "expected exactly one HOST_GUARD_ENABLED= line in the committed host-guard.env"
+    scratch = tmp_path / "host-guard-disabled.env"
+    scratch.write_text(disabled_text)
+    launched = _boot(_HG_TEST_PORT + 2, "hg-disabled.log", {"HOST_GUARD_ENV_FILE": str(scratch)})
+    try:
+        _wait_for_port_answering(
+            _HG_TEST_PORT + 2, timeout=_START_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
+        )
+        pid = _owning_pid(_HG_TEST_PORT + 2)
+        cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
+        assert cpus == own_cpus, "no CPU-affinity restriction should apply when HOST_GUARD_ENABLED=0"
+        penv = _read_proc_environ(pid)
+        for var, ambient_val in ambient_blas.items():
+            assert penv.get(var) == ambient_val, (
+                f"HOST_GUARD_ENABLED=0 must not change {var} (ambient {ambient_val!r}, got {penv.get(var)!r})"
+            )
+    finally:
+        launched.stop()
+
+
+def test_host_guard_marker_files_lists_start_frontend():
+    """TC-5 (marker registration) -- `project-extensions/host-guard/host-guard.env`'s
+    `HOST_GUARD_MARKER_FILES` lists `scripts/start-frontend.sh` alongside the two pre-existing launchers,
+    so the framework's own generic marker check (`grep -q "HOST-GUARD" <file>`,
+    `incredible_auto_dev/scripts/automation/run-goal.sh`) covers it too."""
+    if not HOST_GUARD_ENV_FILE.exists():
+        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present -- nothing to verify")
+    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
+    markers = (hg.get("HOST_GUARD_MARKER_FILES") or "").split()
+    assert "scripts/start-frontend.sh" in markers, f"HOST_GUARD_MARKER_FILES={markers!r}"
+    assert "scripts/dev.sh" in markers and "scripts/start-backend.sh" in markers, (
+        "the two pre-existing launchers must still be listed too — never a replacement, an addition"
+    )
+    # the marker check itself is a plain substring grep — confirm the block is genuinely present, not
+    # merely declared in the list above.
+    assert "HOST-GUARD" in SCRIPT.read_text()
diff --git a/incredible_auto_dev/scripts/start-frontend.sh b/incredible_auto_dev/scripts/start-frontend.sh
index e2075b6c..0250cce6 100755
--- a/incredible_auto_dev/scripts/start-frontend.sh
+++ b/incredible_auto_dev/scripts/start-frontend.sh
@@ -25,6 +25,38 @@ cd "$REPO_ROOT/apps/frontend"
 export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}"
 export NEXT_PUBLIC_API_PORT="${BACKEND_PORT}"
 
+# ==== HOST-GUARD (goal.md AG-10) — DO NOT REMOVE OR WEAKEN ==========================================
+# ops-hardening iter-43 (goal.md "Additional binding notes", the iter-33/i owner item): apply this
+# host's declared CPU-affinity mask + BLAS/OMP/numexpr thread caps to whatever this script launches —
+# mirrors scripts/start-backend.sh's own block (env var names, HOST_GUARD_ENV_FILE test seam, and the
+# "prefix the launched process with taskset" mechanism) byte-for-byte in structure. Placed BEFORE the
+# build-if-stale section below (not just around the final `next start`) because a stale-build path
+# execs a real `next build`, which spins up its own multi-worker TypeScript/webpack compile — genuine
+# CPU/thread pressure from the QA / demo lanes that this project's host-guard envelope must cover, not
+# only the eventual long-lived server. Absent file or HOST_GUARD_ENABLED=0 -> zero behavior change —
+# host-guard stays fully project-neutral per its own header contract
+# (project-extensions/host-guard/host-guard.env). Every value below comes from that file; no magic
+# numbers here. Stripping this block is a REGRESSION regardless of test outcome (goal.md AG-10) — the
+# caps are a physical hardware constraint (two instant hard resets under all-core vectorized ingest
+# bursts, 2026-07-20/21), not a perf knob. HOST_GUARD_ENV_FILE lets tests point at a scratch copy (to
+# exercise the absent/disabled branches without ever touching the real, safety-critical committed
+# file) — unset in every real launch, so production always resolves to the committed path below.
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
+    echo "[start-frontend.sh] host-guard: cpu_list=$HOST_GUARD_CPU_LIST blas_threads=$HOST_GUARD_BLAS_THREADS" >&2
+  fi
+fi
+# ==== end HOST-GUARD =================================================================================
+
 # ==== build-if-stale, then serve PRODUCTION mode (ops-hardening iter-33) ============================
 # Previously this script execed `npx next dev` unconditionally, despite every other doc calling it
 # "prod mode" (measure-perf.sh's own header, goal.md's J-06 step-1 text) — two consecutive evaluators
@@ -53,7 +85,7 @@ _build_is_stale_or_missing() {
 
 if _build_is_stale_or_missing; then
   echo "[start-frontend.sh] '$DIST_DIR' build missing or stale relative to sources — running 'next build'..." >&2
-  if ! npx next build; then
+  if ! "${HOST_GUARD_CMD_PREFIX[@]}" npx next build; then
     echo "[start-frontend.sh] next build FAILED (see output above) — refusing to fall back to" \
          "'next dev' or serve a stale build." >&2
     exit 1
@@ -63,4 +95,4 @@ else
 fi
 # ==== end build-if-stale =============================================================================
 
-exec npx next start -p "$FRONTEND_PORT"
+exec "${HOST_GUARD_CMD_PREFIX[@]}" npx next start -p "$FRONTEND_PORT"
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
index 25105760..7a05494d 100644
--- a/project-extensions/host-guard/host-guard.env
+++ b/project-extensions/host-guard/host-guard.env
@@ -83,7 +83,10 @@ HOST_GUARD_REQUIRE_MARKERS=1
 # Which launcher files must carry the HOST-GUARD cap block (repo-relative,
 # space-separated). The marker check itself is generic in the framework now
 # (2026-07-28 upstream); the file list is project knowledge and lives here.
-HOST_GUARD_MARKER_FILES="scripts/dev.sh scripts/start-backend.sh"
+# ops-hardening iter-43 (goal.md "Additional binding notes", the iter-33/i owner item):
+# scripts/start-frontend.sh joins the list — it can trigger a multi-worker `next build`
+# from the QA / demo lanes, so it now carries a HOST-GUARD block like the other launchers.
+HOST_GUARD_MARKER_FILES="scripts/dev.sh scripts/start-backend.sh scripts/start-frontend.sh"
 
 # Require the interactive pump (the foreground Claude/Codex session) to be
 # cpuset-confined. Added 2026-07-28 after resets #3-#5 (Jul 25 13:09, Jul 27
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-index.html      |   4 +-
 reports/goal-session-ops-hardening-retro.md        |  67 ++-
 reports/perf-budgets.md                            | 226 ++++++++
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 runs/goal-session-ops-hardening/session.json       |   8 +-
 .../state/assumptions.md                           | 316 ++---------
 .../state/assumptions.md.archive.md                | 287 ++++++++++
 runs/goal-session-ops-hardening/state/blueprint.md |   2 +
 runs/goal-session-ops-hardening/state/lessons.md   | 108 +---
 .../state/lessons.md.archive.md                    | 132 +++++
 .../state/retro-input.md                           | 587 +++++++++++++++++----
 runs/goal-session-ops-hardening/summary.md         | 147 ++++--
 runs/goal-session-ops-hardening/telemetry.jsonl    |  26 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   4 +
 17 files changed, 1380 insertions(+), 542 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
