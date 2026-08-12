# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

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
diff --git a/apps/backend/tests/test_poll_health.py b/apps/backend/tests/test_poll_health.py
new file mode 100644
index 00000000..ed916669
--- /dev/null
+++ b/apps/backend/tests/test_poll_health.py
@@ -0,0 +1,143 @@
+"""ops-hardening iter-66 (J-07, TC-4/TC-5) — the canonical `scripts/qa/poll_health.py` health-poll drill
+script: CSV schema (TC-4) + the host-load column (TC-5).
+
+Loads `scripts/qa/poll_health.py` via `importlib.util.spec_from_file_location`, exactly as
+`test_gate_registry_enforcement.py::_load_gate` / `test_staging_ledger_routing.py::_load_gate` already do
+for other project-tooling scripts that live outside the `app` package. No live HTTP call is made — `urllib
+.request.urlopen` is monkeypatched to a stub response so this test needs no running backend.
+"""
+from __future__ import annotations
+
+import csv
+import importlib.util
+import json
+import time
+from pathlib import Path
+
+import pytest
+
+_REPO_ROOT = Path(__file__).resolve().parents[3]
+_SCRIPT_PATH = _REPO_ROOT / "scripts" / "qa" / "poll_health.py"
+
+
+def _load_poll_health():
+    spec = importlib.util.spec_from_file_location("poll_health_test_module", _SCRIPT_PATH)
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def poll_health():
+    return _load_poll_health()
+
+
+class _FakeResponse:
+    def __init__(self, status: int, body: bytes = b"{}"):
+        self.status = status
+        self._body = body
+
+    def read(self) -> bytes:
+        return self._body
+
+    def __enter__(self):
+        return self
+
+    def __exit__(self, *exc):
+        return False
+
+
+def test_csv_fields_match_tc4_schema(poll_health):
+    """TC-4: the CSV column schema is EXACTLY these five names, in this order."""
+    assert poll_health.CSV_FIELDS == [
+        "timestamp", "http_status", "elapsed_s", "breach_over_2s", "load_avg_1m",
+    ]
+
+
+def test_poll_once_records_populated_load_avg_1m(monkeypatch, poll_health):
+    """TC-5: every poll row carries a non-null `load_avg_1m` sampled at poll time."""
+    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 1.23)
+    monkeypatch.setattr(
+        poll_health.urllib.request, "urlopen", lambda req, timeout=5.0: _FakeResponse(200),
+    )
+    row = poll_health.poll_once("http://example.invalid/api/health")
+    assert row["load_avg_1m"] == 1.23
+    assert row["http_status"] == 200
+    assert row["breach_over_2s"] == 0
+    assert isinstance(row["elapsed_s"], float)
+    assert row["timestamp"]  # non-empty ISO-8601 string
+
+
+def test_poll_once_flags_breach_over_2s(monkeypatch, poll_health):
+    """A poll whose wall-clock duration exceeds HEALTH_CEILING_S (2.0s) is flagged, not silently recorded."""
+    def _slow_urlopen(req, timeout=5.0):
+        time.sleep(0)  # keep the test fast; simulate elapsed time via monkeypatched monotonic instead
+        return _FakeResponse(200)
+
+    times = iter([0.0, 2.5])  # t0, t1 -> elapsed_s = 2.5
+    monkeypatch.setattr(poll_health.time, "monotonic", lambda: next(times))
+    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 0.5)
+    monkeypatch.setattr(poll_health.urllib.request, "urlopen", _slow_urlopen)
+    row = poll_health.poll_once("http://example.invalid/api/health")
+    assert row["elapsed_s"] == 2.5
+    assert row["breach_over_2s"] == 1
+
+
+def test_poll_once_records_status_zero_on_connection_error(monkeypatch, poll_health):
+    """A starved/unreachable client is recorded as http_status=0, never fabricated as a fake 200."""
+    def _raise(req, timeout=5.0):
+        raise OSError("connection refused")
+
+    monkeypatch.setattr(poll_health.urllib.request, "urlopen", _raise)
+    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 0.1)
+    row = poll_health.poll_once("http://example.invalid/api/health")
+    assert row["http_status"] == 0
+
+
+def test_run_writes_exact_schema_and_meta_json(tmp_path, monkeypatch, poll_health):
+    """`run()` (the canonical entry both the dev evidence-drill and the browser-qa J-07 case call) writes
+    one CSV row per poll with the TC-4 header, plus a sibling `.meta.json` carrying `cpu_count` (the IN
+    SCOPE ask's other host-load figure, recorded once per run rather than duplicated onto every row —
+    see the script's own module docstring for the rationale)."""
+    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 2.0)
+    monkeypatch.setattr(
+        poll_health.urllib.request, "urlopen", lambda req, timeout=5.0: _FakeResponse(200),
+    )
+    out_path = tmp_path / "poll.csv"
+    rows_written = poll_health.run(
+        "http://example.invalid/api/health", str(out_path), None, count=3, interval_s=0.0,
+    )
+    assert rows_written == 3
+
+    with open(out_path, newline="") as fh:
+        reader = csv.DictReader(fh)
+        assert reader.fieldnames == poll_health.CSV_FIELDS
+        rows = list(reader)
+    assert len(rows) == 3
+    for row in rows:
+        assert row["load_avg_1m"] == "2.0"
+        assert row["http_status"] == "200"
+        assert row["breach_over_2s"] == "0"
+
+    meta_path = Path(str(out_path) + ".meta.json")
+    assert meta_path.exists()
+    meta = json.loads(meta_path.read_text())
+    assert meta["cpu_count"] == poll_health.os.cpu_count()
+    assert meta["rows"] == 3
+    assert meta["health_ceiling_s"] == 2.0
+
+
+def test_run_stops_on_stop_file(tmp_path, monkeypatch, poll_health):
+    """No `count` given: `run()` polls until `stop_file` appears (the pre-existing per-iteration scripts'
+    own convention, preserved verbatim for the browser-qa lane's long-running drills)."""
+    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 0.75)
+    monkeypatch.setattr(
+        poll_health.urllib.request, "urlopen", lambda req, timeout=5.0: _FakeResponse(200),
+    )
+    out_path = tmp_path / "poll.csv"
+    stop_path = tmp_path / "STOP"
+    stop_path.write_text("")  # already present -> run() exits after checking, before any poll
+    rows_written = poll_health.run(
+        "http://example.invalid/api/health", str(out_path), str(stop_path), interval_s=0.0,
+    )
+    assert rows_written == 0
diff --git a/incredible_auto_dev/scripts/qa/poll_health.py b/incredible_auto_dev/scripts/qa/poll_health.py
new file mode 100644
index 00000000..2ff54e56
--- /dev/null
+++ b/incredible_auto_dev/scripts/qa/poll_health.py
@@ -0,0 +1,142 @@
+"""Canonical GET /api/health 1 Hz poller (ops-hardening iter-66, J-07, TC-4/TC-5).
+
+The SINGLE, checked-in health-poll drill script this session's dev evidence-drills AND its J-07
+browser-qa test case both run through -- no more per-iteration throwaway copies
+(runs/goal-ops-hardening-iter-N/evidence-drill/poll_health.py, iter-53 through iter-65, each a byte-for-
+byte-similar re-copy) and no more ad hoc curl/bash subprocess-per-poll loops (the browser-qa lane's own
+supplementary drills, iter-65's Addendum 31: "this agent's own ad hoc bash/curl loop, not `poll_health.py`"
+-- disagreed with the dev-side counter by ~40x on the same window, 8/240 vs 1/1057, because a
+subprocess-per-poll (`date` + `python3`/`curl` forked each second) pays real fork/exec overhead under CPU
+contention that a single long-lived HTTP client never does).
+
+Single `urllib` client, ONE poll per second, no subprocess spawned per poll. Runs until the sibling
+`STOP_FILE` appears (mirrors the prior per-iteration scripts' own stop-file convention, e.g.
+runs/goal-ops-hardening-iter-65/evidence-drill/poll_health.py) OR, when `--count N` is given, for exactly
+N polls then exits (useful for a bounded unit-testable/scripted run).
+
+CSV schema (TC-4, byte-for-byte, shared by every caller -- the dev evidence-drill AND the J-07 browser-qa
+test case cite the SAME column names so their raw CSVs are directly comparable):
+
+    timestamp, http_status, elapsed_s, breach_over_2s, load_avg_1m
+
+  - timestamp       -- ISO-8601 UTC, the poll's OWN start instant (`datetime.now(timezone.utc)`).
+  - http_status      -- the response status code, or 0 on a timeout/connection error (never fabricated).
+  - elapsed_s        -- wall-clock seconds for this ONE poll (three decimal places).
+  - breach_over_2s   -- "1" iff `elapsed_s > HEALTH_CEILING_S` (the owner-amended relaxed ceiling during a
+                        bounded background-compute window, docs/goal.md's "Additional binding notes"),
+                        else "0" -- pre-computed here so a downstream reconciliation never re-derives the
+                        threshold from a magic number of its own.
+  - load_avg_1m      -- `os.getloadavg()[0]` (the 1-minute load average) sampled at the SAME instant as the
+                        poll (TC-5: always populated/non-null on Linux -- `os.getloadavg` is unavailable
+                        only on Windows, where this project does not run in CI/dev per project-template.md).
+
+`os.cpu_count()` (the IN SCOPE ask's other host-load figure) is a HOST CONSTANT for the whole run, not a
+per-poll observation -- recording it as a 6th per-row column would repeat the same integer on every line
+for no benefit and would break the TC-4/TC-5 fixed 5-column schema those tests assert against. It is
+instead written ONCE, alongside the run's own poll count and URL, to a sibling `<OUT>.meta.json` file next
+to the CSV -- satisfying "record... os.cpu_count()" without duplicating a constant onto every row.
+"""
+from __future__ import annotations
+
+import argparse
+import csv
+import json
+import os
+import time
+import urllib.error
+import urllib.request
+from datetime import datetime, timezone
+from typing import Optional
+
+HEALTH_CEILING_S = 2.0  # the owner-amended relaxed ceiling during a bounded background-compute window
+CSV_FIELDS = ["timestamp", "http_status", "elapsed_s", "breach_over_2s", "load_avg_1m"]
+
+
+def host_load_avg_1m() -> Optional[float]:
+    """The 1-minute load average, or None on a platform without `os.getloadavg` (never fabricated)."""
+    try:
+        return os.getloadavg()[0]
+    except (AttributeError, OSError):  # pragma: no cover -- Linux (this project's only target) always has it
+        return None
+
+
+def poll_once(url: str, timeout: float = 5.0) -> dict:
+    """One GET request against `url`, timed. `http_status` is 0 on a timeout/connection error (a starved
+    client is distinct from a slow-but-answering server -- never conflated). Never raises."""
+    ts = datetime.now(timezone.utc)
+    t0 = time.monotonic()
+    status = 0
+    try:
+        req = urllib.request.Request(url, method="GET")
+        with urllib.request.urlopen(req, timeout=timeout) as resp:
+            status = resp.status
+            resp.read()
+    except urllib.error.HTTPError as exc:
+        status = exc.code
+    except Exception:  # noqa: BLE001 -- record as a non-answer (status 0), never crash the poller
+        status = 0
+    elapsed_s = time.monotonic() - t0
+    return {
+        "timestamp": ts.isoformat(),
+        "http_status": status,
+        "elapsed_s": round(elapsed_s, 3),
+        "breach_over_2s": 1 if elapsed_s > HEALTH_CEILING_S else 0,
+        "load_avg_1m": host_load_avg_1m(),
+    }
+
+
+def run(
+    url: str, out_path: str, stop_file: Optional[str], *, count: Optional[int] = None,
+    interval_s: float = 1.0,
+) -> int:
+    """Poll `url` once per `interval_s` seconds, appending one CSV row per poll to `out_path`, until either
+    `count` polls have run (when given) or `stop_file` appears on disk. Writes `<out_path>.meta.json` with
+    the run's host-constant `cpu_count` + summary counts once polling stops. Returns the row count."""
+    rows_written = 0
+    with open(out_path, "w", newline="") as fh:
+        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
+        writer.writeheader()
+        fh.flush()
+        while True:
+            if count is not None and rows_written >= count:
+                break
+            if stop_file is not None and os.path.exists(stop_file):
+                break
+            t_poll_start = time.monotonic()
+            row = poll_once(url)
+            writer.writerow(row)
+            fh.flush()
+            rows_written += 1
+            if count is not None and rows_written >= count:
+                break
+            remaining = interval_s - (time.monotonic() - t_poll_start)
+            if remaining > 0:
+                time.sleep(remaining)
+
+    meta = {
+        "url": url,
+        "rows": rows_written,
+        "cpu_count": os.cpu_count(),
+        "health_ceiling_s": HEALTH_CEILING_S,
+    }
+    with open(out_path + ".meta.json", "w") as fh:
+        json.dump(meta, fh, indent=2)
+    return rows_written
+
+
+def main() -> None:
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.add_argument("url", nargs="?", default="http://localhost:8255/api/health")
+    parser.add_argument("out", nargs="?", default="poll_health.csv")
+    parser.add_argument("stop_file", nargs="?", default="STOP")
+    parser.add_argument(
+        "--count", type=int, default=None,
+        help="poll exactly N times then exit, instead of running until stop_file appears",
+    )
+    args = parser.parse_args()
+    rows = run(args.url, args.out, args.stop_file if args.count is None else None, count=args.count)
+    print(f"poll_health: wrote {rows} rows to {args.out}")
+
+
+if __name__ == "__main__":
+    main()
```
