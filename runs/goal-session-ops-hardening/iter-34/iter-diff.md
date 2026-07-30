# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/tests/test_ingest_finalize_memory_pressure.py b/apps/backend/tests/test_ingest_finalize_memory_pressure.py
new file mode 100644
index 00000000..ffe376ad
--- /dev/null
+++ b/apps/backend/tests/test_ingest_finalize_memory_pressure.py
@@ -0,0 +1,221 @@
+"""ops-hardening iter-34 (J-07 step 4) -- a REAL, non-monkeypatched induction test for the ingest
+finalize hook's forward-aggregate memory-pressure abort: `data_manager._refresh_ingest_aggregates`'s
+per-horizon `except MemoryError` catch (ops-hardening iter-8), the EXACT mechanism J-07 step 4 must
+exercise per the binding iter-30 lesson ("do not substitute a different, easier-to-trigger failure mode
+and call it equivalent").
+
+WHY A REAL SUBPROCESS INDUCTION, NOT A MONKEYPATCH: mirrors `test_forward_testing_concurrency.py`'s TC-3
+rationale (see that module's docstring) -- a `monkeypatch`-injected `MemoryError` proves the exception
+HANDLER's code path but never proves the mechanism actually triggers under genuine OS-level virtual-memory
+exhaustion. This spawns a real Python subprocess under a genuinely tightened `ulimit -v` (RLIMIT_AS)
+against a fixture sized so `_refresh_ingest_aggregates`'s forward-aggregate loop (all 5 configured
+horizons, `compute_forward_aggregates` via `forward_aggregates_ingest_cached`) needs materially more
+virtual memory than the tightened cap allows, while a generous cap (the CONTROL) lets the identical call
+complete normally -- proving the abort is attributable to the cap, not an unrelated bug (the DoD's
+explicit "control assertion... caught as a test-setup failure rather than silently passing" requirement).
+
+CALIBRATION (measured on this host, `.venv` Python 3.12, one `ScannerRun` with 600,000 `ScannerResult` +
+3,000,000 `ForwardReturn` rows -- one ticker/observation per configured horizon, `record_json` padded to
+4,000 bytes -- mirroring `test_forward_testing_concurrency.py`'s existing per-row cost convention): a bare
+`import app + call _refresh_ingest_aggregates` subprocess completes the WHOLE finalize hook (coverage,
+membership_timeline, forward_aggregates x5 horizons, research_hot_keys) cleanly under a generous
+2,000,000 KB cap; under a `TIGHT_CAP_KB` of 750,000 KB (squarely inside a measured 600,000-900,000 KB
+window that reproducibly aborts forward_aggregates specifically, with NO cascading crash on either
+boundary) the SAME call cleanly catches a `MemoryError` at horizon 1 and stops that loop, per the iter-8
+isolation contract, while `_refresh_ingest_aggregates` itself still returns normally (never raises) and
+the SAME process can still open a fresh session and read the database afterward.
+
+`setup_status="Avoid"` (deliberately NOT "Actionable", `setups.ACTIONABLE` -- the FIRST `subject_catalog`
+entry `research_hot_keys`'s own warm targets by default) keeps this fixture's high-cardinality rows
+invisible to the event-study hot-key warm, so the cap specifically isolates `forward_aggregates`'s own
+memory need rather than `research_hot_keys`'s (confirmed live during this iteration's calibration: without
+this, the SAME fixture at "Actionable" made `research_hot_keys` -- a GENERIC, non-`MemoryError`-specific
+except -- the first thing to fail, never exercising the iter-8 forward_aggregates-specific catch this test
+targets)."""
+from __future__ import annotations
+
+import subprocess
+import sys
+import time
+from datetime import date, datetime, timezone
+from pathlib import Path
+
+import pytest
+from sqlalchemy import insert
+from sqlmodel import Session
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.models import ForwardReturn, ScannerResult, ScannerRun
+
+BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)  # apps/backend -- for the child subprocess's sys.path
+N_TICKERS = 600_000
+RECORD_JSON_BYTES = 4_000  # mirrors test_forward_testing_concurrency.py's per-row cost convention
+ASOF = date(2020, 1, 2)
+# Measured this iteration (see module docstring): a wide, crash-free window (600,000-900,000 KB) where
+# forward_aggregates specifically aborts with a clean, caught MemoryError; 750,000 KB sits centered in it
+# with margin on both sides against machine-to-machine allocator variance.
+TIGHT_CAP_KB = 750_000
+# Comfortably clears the whole finalize hook (measured ~78s, ~590 MB peak) -- the CONTROL cap.
+CONTROL_CAP_KB = 2_000_000
+BOUNDED_TIMEOUT_S = 300.0  # generous: the control pass alone measured ~78s on this host
+
+
+def _build_memory_pressure_finalize_db(db_path: Path) -> int:
+    """One `ScannerRun` with `N_TICKERS` `ScannerResult` rows and `N_TICKERS` `ForwardReturn` rows PER
+    configured horizon (mirrors the real ingest finalize hook's shape: one run, every horizon populated).
+    Returns the run id."""
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    padding = "x" * RECORD_JSON_BYTES
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=ASOF, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label=cfg.regime.labels[0], regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        run_id = run.id
+        result_rows = [
+            dict(
+                run_id=run_id, ticker=f"MPT{i:07d}", name=f"MPT{i:07d}", sector="Technology",
+                leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
+                entry_quality_bucket="E", risk_score=0.0, risk_bucket="E",
+                # NOT "Actionable" -- see module docstring (avoids contaminating research_hot_keys's warm).
+                setup_status="Avoid", rank=(i % 500) + 1, record_json=padding, is_vcp=False,
+                is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
+            )
+            for i in range(N_TICKERS)
+        ]
+        session.execute(insert(ScannerResult.__table__), result_rows)
+        for h in cfg.walk_forward.horizons:
+            fr_rows = [
+                dict(
+                    run_id=run_id, symbol=f"MPT{i:07d}", horizon=h, asof_date=ASOF, entry_close=100.0,
+                    measured_date=ASOF, realized_return=0.01, max_drawdown=-0.02,
+                )
+                for i in range(N_TICKERS)
+            ]
+            session.execute(insert(ForwardReturn.__table__), fr_rows)
+        session.commit()
+        return run_id
+
+
+@pytest.fixture(scope="module")
+def finalize_memory_pressure_db(tmp_path_factory) -> Path:
+    db_path = tmp_path_factory.mktemp("finalize_mem_pressure") / "mem.db"
+    _build_memory_pressure_finalize_db(db_path)
+    return db_path
+
+
+# --------------------------------------------------------------------------------------------------
+# Child-process probe: calls `_refresh_ingest_aggregates` directly (the exact function/call the ingest
+# finalize hook itself uses -- `data_manager.py`'s `_run_job`), under a `ulimit -v` set by the caller, then
+# proves the SAME process can still open a fresh session and read the database afterward (no leaked
+# lock/open transaction).
+# --------------------------------------------------------------------------------------------------
+_CHILD_PROBE_TEMPLATE = '''
+import sys
+sys.path.insert(0, "__BACKEND_ROOT__")
+from datetime import date
+from sqlmodel import Session, select
+from app.config import load_config
+from app.db import make_engine
+from app.engine import data_manager
+from app.engine.data_manager import JobProgress
+from app.models import ScannerRun
+
+db_path = sys.argv[1]
+engine = make_engine(f"sqlite:///{db_path}")
+cfg = load_config()
+d = date(2020, 1, 2)
+
+with Session(engine) as session:
+    prog = JobProgress(job_id="mem-pressure-probe", kind="backfill", start=d, end=d)
+    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise
+print("REFRESHED=" + ",".join(refreshed))
+
+# same-process, fresh-session read afterward -- proves no leaked lock / open transaction blocks recovery.
+with Session(engine) as session:
+    n = len(session.exec(select(ScannerRun)).all())
+print(f"SUBSEQUENT_READ_OK n={n}")
+'''
+
+
+def _write_child_probe(tmp_path: Path) -> Path:
+    script_path = tmp_path / "_finalize_mem_probe_child.py"
+    script_path.write_text(_CHILD_PROBE_TEMPLATE.replace("__BACKEND_ROOT__", BACKEND_ROOT))
+    return script_path
+
+
+def _run_child_probe(script_path: Path, db_path: Path, cap_kb: int) -> subprocess.CompletedProcess:
+    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path}"
+    return subprocess.run(
+        ["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S,
+    )
+
+
+def test_tight_cap_aborts_forward_aggregates_with_caught_memory_error_and_recovers(
+    finalize_memory_pressure_db, tmp_path
+):
+    """TC-2 (J-07 step 4): under a REAL, non-monkeypatched `ulimit -v` cap sized below what the
+    finalize hook's forward-aggregate warm needs, `_refresh_ingest_aggregates` catches a genuine
+    `MemoryError` at the per-horizon boundary (iter-8's SPECIFIC catch, never a substituted mechanism):
+    "forward_aggregates" is honestly absent from the refreshed-categories list, the function itself does
+    not raise (exit 0, no crash/hang), and the SAME process can still open a fresh session and read the
+    database immediately afterward -- no leaked lock, no wedge, no restart needed."""
+    script_path = _write_child_probe(tmp_path)
+    start = time.monotonic()
+    result = _run_child_probe(script_path, finalize_memory_pressure_db, TIGHT_CAP_KB)
+    elapsed = time.monotonic() - start
+
+    assert elapsed < BOUNDED_TIMEOUT_S, f"child probe took {elapsed:.1f}s -- treat as a hang, not a slow pass"
+    assert result.returncode == 0, (
+        f"_refresh_ingest_aggregates must never raise -- child probe crashed uncaught "
+        f"(cap {TIGHT_CAP_KB} KB may be miscalibrated too tight); "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+    assert "ingest forward-aggregate warm aborted at horizon" in result.stdout + result.stderr, (
+        f"expected the iter-8 forward_aggregates-specific MemoryError log line to fire under this cap "
+        f"(the cap may be miscalibrated too loose -- a control-assertion failure, not a silent pass); "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+    refreshed_line = next(line for line in result.stdout.splitlines() if line.startswith("REFRESHED="))
+    refreshed = set(refreshed_line[len("REFRESHED="):].split(",")) - {""}
+    assert "forward_aggregates" not in refreshed, (
+        f"forward_aggregates must be honestly absent (aborted) under the tight cap; refreshed={refreshed}"
+    )
+    assert "SUBSEQUENT_READ_OK" in result.stdout, (
+        f"expected the same-process subsequent read to succeed after the MemoryError; "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+
+
+def test_control_generous_cap_completes_forward_aggregates_normally(
+    finalize_memory_pressure_db, tmp_path
+):
+    """Control assertion (DoD: "a control assertion that the SAME override, if set too high to trigger
+    the error, is caught as a test-setup failure rather than silently passing"): the IDENTICAL fixture and
+    call, under a generous cap, completes `forward_aggregates` normally with NO MemoryError -- proving the
+    tight-cap test's abort above is attributable to the tightened cap, not an unrelated bug or a
+    permanently-broken code path."""
+    script_path = _write_child_probe(tmp_path)
+    start = time.monotonic()
+    result = _run_child_probe(script_path, finalize_memory_pressure_db, CONTROL_CAP_KB)
+    elapsed = time.monotonic() - start
+
+    assert elapsed < BOUNDED_TIMEOUT_S, f"child probe took {elapsed:.1f}s -- treat as a hang, not a slow pass"
+    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    assert "ingest forward-aggregate warm aborted at horizon" not in result.stdout + result.stderr, (
+        f"the generous CONTROL cap unexpectedly triggered the same abort as the tight-cap test -- "
+        f"the tight-cap result above cannot be trusted as cap-attributable until this is fixed; "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+    refreshed_line = next(line for line in result.stdout.splitlines() if line.startswith("REFRESHED="))
+    refreshed = set(refreshed_line[len("REFRESHED="):].split(",")) - {""}
+    assert "forward_aggregates" in refreshed, (
+        f"expected forward_aggregates to complete normally under the generous control cap; "
+        f"refreshed={refreshed}"
+    )
```
