# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 6c3fd6ad..6f1d0f18 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -5198,6 +5198,48 @@ def _has_open_run_record(engine: Engine, job_id: Optional[str]) -> bool:
         return _open_run_record(session, job_id) is not None
 
 
+def _reopen_interrupted_run_record(engine: Engine, job_id: Optional[str]) -> bool:
+    """ops-hardening iter-66 (J-05, TC-7 — the iter-64/d duplicate-run-row fix): a `kill -9` mid-job
+    leaves its `data_provider_runs` row `running`; the NEXT boot's `sweep_orphaned_runs` (the ONLY writer
+    of the `interrupted` status — see that function's own docstring) honestly closes it `interrupted`
+    since nothing more is known. That status is NOT a deliberate terminal outcome the way `failed`/
+    `failed_backfill` are (both are set by an in-process handler that had the chance to run — a SIGKILL
+    never gives one) — it is exactly the row a checkpoint-driven Resume of the SAME `job_id` is trying to
+    continue (`_progress_from_checkpoint` always seeds `job_id=cp.import_id`, the ORIGINAL job's id).
+
+    Before this fix, `_run_job`'s `_has_open_run_record` gate treated `interrupted` identically to a
+    genuinely terminal row and always fell through to `_create_run_record`, inserting a SECOND
+    `data_provider_runs` row for the resume attempt — iter-64/d's observed pattern: one `job_id`
+    producing both an `interrupted` row (the dead attempt) and a post-restart `ok` row (the resumed one),
+    5 occurrences all-time. Reopening the SAME interrupted row here (status back to `running`,
+    `finished_at` cleared — mirroring `_create_run_record`'s own fresh-row shape) instead of inserting a
+    new one restores the "one record per job_id, one honest transition" contract `DataProviderRun`'s own
+    docstring already claims: `_finalize_run_record`'s existing `_open_run_record` lookup then finds and
+    UPDATEs this SAME row when the resume reaches its terminal state, exactly as it already does for a
+    graceful 429 `resumable` pause (unchanged).
+
+    Returns True iff a row was reopened (so the caller skips its own `_create_run_record` call); False
+    when no `interrupted` row exists for this job_id — the ordinary "already-terminal (failed/
+    failed_backfill-driven), fresh Retry audit row" path is completely unchanged (J-38 Retry's documented
+    "the audit trail of every attempt stays complete" intent — untouched by this fix)."""
+    if not job_id:
+        return False
+    with Session(engine) as session:
+        row = session.exec(
+            select(DataProviderRun)
+            .where(DataProviderRun.job_id == job_id)
+            .where(DataProviderRun.status == "interrupted")
+            .order_by(DataProviderRun.id.desc())
+        ).first()
+        if row is None:
+            return False
+        row.status = "running"
+        row.finished_at = None
+        session.add(row)
+        session.commit()
+    return True
+
+
 # ops-hardening iter-9 (F1) — how often a long-running backfill re-writes its CURRENT progress onto its
 # OPEN run-history row. One small UPDATE per interval bounds the write amplification regardless of how
 # fast dates complete, while keeping a killed job's persisted progress at most one interval stale.
@@ -5395,11 +5437,21 @@ def _run_job(
     # `running`/`resumable`) reuses that row; a resume of an ALREADY-TERMINAL record (a `failed_backfill`
     # whose `both`-job row finalized to `failed`) is a fresh attempt and writes its OWN honest record
     # (like J-38 Retry) — so the audit trail of every attempt stays complete.
+    #
+    # ops-hardening iter-66 (J-05, TC-7 — iter-64/d fix): a THIRD case existed between these two, unhandled
+    # until now — a resume whose row is `interrupted` (a `kill -9` mid-job, swept by the boot sweep, NEVER
+    # a deliberate terminal outcome the way `failed`/`failed_backfill` are). That row is not "open" per
+    # `_has_open_run_record`, so this gate always fell through to `_create_run_record` for it too, inserting
+    # a SECOND row that shares the interrupted row's `job_id` (the observed duplicate-row pattern).
+    # `_reopen_interrupted_run_record` reclaims that SAME interrupted row (status back to `running`) when
+    # one exists for this job_id, so the gate below only creates a fresh row for a genuinely fresh job OR a
+    # genuinely terminal (failed/failed_backfill-driven) Retry — both unchanged from before this fix.
     if not is_resume or not _has_open_run_record(eng, prog.job_id):
-        try:
-            _create_run_record(eng, cfg, prog)
-        except Exception as exc:  # noqa: BLE001 — a bookkeeping failure must not crash the worker
-            _record_error(prog, scrub(f"failed to create run record: {exc}"))
+        if not (is_resume and _reopen_interrupted_run_record(eng, prog.job_id)):
+            try:
+                _create_run_record(eng, cfg, prog)
+            except Exception as exc:  # noqa: BLE001 — a bookkeeping failure must not crash the worker
+                _record_error(prog, scrub(f"failed to create run record: {exc}"))
     try:
         with Session(eng) as session:
             if (prog.kind in _FETCH_KINDS or is_expand) and not skip_fetch:
diff --git a/apps/backend/tests/test_data_manager_jobs_pipeline.py b/apps/backend/tests/test_data_manager_jobs_pipeline.py
index ec6d0fb6..48d3057e 100644
--- a/apps/backend/tests/test_data_manager_jobs_pipeline.py
+++ b/apps/backend/tests/test_data_manager_jobs_pipeline.py
@@ -162,6 +162,118 @@ def test_boot_sweep_marks_orphaned_running_as_interrupted(tmp_path):
     assert sweep_orphaned_runs(engine) == 0  # idempotent — nothing left running
 
 
+def test_reopen_interrupted_run_record_reuses_row_never_a_genuinely_terminal_one(tmp_path):
+    """ops-hardening iter-66 (J-05, TC-7 — iter-64/d fix) — `_reopen_interrupted_run_record` reopens ONLY a
+    row whose status is exactly `interrupted` (the boot sweep's own honest, non-deliberate outcome — see
+    `sweep_orphaned_runs`'s docstring, its only writer). A genuinely terminal row (`ok`/`failed`/`partial`)
+    is left completely untouched — the documented "fresh Retry audit row" path this fix must not disturb —
+    and an unknown job_id returns False."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'reopen.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DataProviderRun(
+            provider="tiingo", started_at=data_manager._utcnow(), finished_at=data_manager._utcnow(),
+            status="interrupted", job_id="job-interrupted",
+        ))
+        session.add(DataProviderRun(
+            provider="tiingo", started_at=data_manager._utcnow(), finished_at=data_manager._utcnow(),
+            status="failed", job_id="job-failed",
+        ))
+        session.commit()
+
+    assert data_manager._reopen_interrupted_run_record(engine, "job-interrupted") is True
+    assert data_manager._reopen_interrupted_run_record(engine, "job-failed") is False  # genuinely terminal
+    assert data_manager._reopen_interrupted_run_record(engine, "job-does-not-exist") is False
+
+    with Session(engine) as session:
+        reopened = session.exec(
+            select(DataProviderRun).where(DataProviderRun.job_id == "job-interrupted")
+        ).one()
+        untouched = session.exec(
+            select(DataProviderRun).where(DataProviderRun.job_id == "job-failed")
+        ).one()
+        # still exactly one row each — reopening never inserts a second row
+        assert len(session.exec(select(DataProviderRun)).all()) == 2
+    assert reopened.status == "running" and reopened.finished_at is None
+    assert untouched.status == "failed"  # genuinely terminal — untouched by this fix
+
+
+class _AllThenPersistent429(PriceProvider):
+    """Every symbol 429s immediately — the fetch pauses gracefully at chunk 0 (`next_chunk_index` stays
+    0), so the durable checkpoint reaches `resumable` in ONE commit, distinct from the run-history row's
+    OWN status (a separate table/commit — see `_reopen_interrupted_run_record`'s docstring)."""
+
+    def get_daily(self, symbol, start=None, end=None):
+        raise RateLimitError("HTTP 429 at https://provider/x")
+
+
+class _AlwaysOk(PriceProvider):
+    """Every symbol succeeds — a recovered provider for a resume."""
+
+    def get_daily(self, symbol, start=None, end=None):
+        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]
+
+
+def test_resume_of_a_row_left_running_by_a_kill_reopens_it_not_a_duplicate(tmp_path):
+    """ops-hardening iter-66 (J-05, TC-7 — iter-64/d fix, end to end). Reproduces the exact race a
+    `kill -9` can hit: a graceful 429 pause durably commits the CHECKPOINT `resumable` (its own
+    table/commit) before `_finalize_run_record`'s separate UPDATE ever mirrors that status onto the
+    `data_provider_runs` row — if the process dies in that narrow window, the checkpoint is genuinely
+    resumable but the run-history row is left at its creation-time `running` default. The NEXT boot's
+    `sweep_orphaned_runs` honestly closes that orphaned `running` row `interrupted` (never a deliberate
+    terminal outcome). Before this fix, resuming that SAME job_id fell through `_run_job`'s
+    `_has_open_run_record` gate straight to `_create_run_record`, inserting a SECOND row — iter-64/d's
+    observed pattern: one job_id producing both an `interrupted` row and a post-restart `ok` row. This
+    test constructs that exact end state directly (a genuinely resumable checkpoint, the run record forced
+    to `running` as it would sit mid-race, then boot-swept) and asserts the resume reuses the SAME row."""
+    cfg = load_config()
+    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
+    cfg = cfg.model_copy(update={"scanner": _sc})
+    engine = make_engine(f"sqlite:///{tmp_path / 'resume_dup.db'}")
+    create_db_and_tables(engine)
+    _seed_calendar(engine, [date(2024, 1, 2)])
+
+    fetch_day = date(2024, 3, 1)
+    job = create_job("fetch", fetch_day, fetch_day, source="tiingo")
+    summary1 = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_AllThenPersistent429(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary1["status"] == "resumable"
+    with Session(engine) as session:
+        cp = get_checkpoint(session, job.job_id)
+        assert cp is not None and cp.status == "resumable"  # durably paused — genuinely resumable
+        run = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+        assert run.status == "resumable"  # the normal (non-race) outcome, before this test's own fault injection
+
+    # Simulate the exact race: force the run-history row back to `running`, as it would sit if the process
+    # died BEFORE `_finalize_run_record`'s own UPDATE reached it (the checkpoint's commit above already
+    # landed independently — untouched by this).
+    with Session(engine) as session:
+        run = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+        run.status = "running"
+        session.add(run)
+        session.commit()
+
+    swept = sweep_orphaned_runs(engine)  # the next boot's own sweep — the ONLY writer of "interrupted"
+    assert swept == 1
+    with Session(engine) as session:
+        run = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
+        assert run.status == "interrupted"
+
+    # Resume: the checkpoint is still genuinely resumable (sweep_orphaned_runs only ever touches
+    # data_provider_runs, never import_checkpoints) — before this fix, this step created a second row.
+    summary2 = resume_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_AlwaysOk(), sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary2["status"] == "ok"
+    with Session(engine) as session:
+        rows = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).all()
+    assert len(rows) == 1, "resume of an interrupted-but-resumable job reuses its row — no duplicate"
+    assert rows[0].status == "ok"
+    assert rows[0].finished_at is not None
+
+
 def test_lifecycle_counts_match_job_payload(tmp_path):
     """J-60 — the terminal run record's counts/summary match the job's OWN payload (one bookkeeping
     source). A failed fetch records `failed` with the same symbol counts the job reports."""
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 207 +++++++++++++++++++++
 .../journey-scripts/J-05.json                      |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   7 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   1 +
 5 files changed, 217 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
