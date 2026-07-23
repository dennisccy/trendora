"""ops-hardening iter-14 (J-07, AG-8 REGRESSION recovery) — TC-3 (a REAL, non-monkeypatched tightened-
`ulimit -v` memory-pressure induction) and TC-4 (a concurrent-caller regression) for the bounded/streamed
`compute_forward_aggregates` rewrite in `apps/backend/app/engine/forward_testing.py`.

WHY A REAL SUBPROCESS INDUCTION (TC-3), NOT A MONKEYPATCH: the repo's existing
`test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds`-style tests
(`test_data_manager.py`) all `monkeypatch`-inject a `MemoryError` at a chosen call boundary — that style
did NOT catch iter-11's live 500s or iter-13's live ~12-minute wedge, because it never exercises a real
OS-level virtual-memory exhaustion inside SQLAlchemy/sqlite's own internals. TC-3 spawns a real Python
subprocess under a genuinely tightened `ulimit -v` (RLIMIT_AS) against a fixture sized so the PRE-REWRITE
unbounded `.all()` pattern needs materially more virtual memory than the cap allows, while the REWRITTEN
column-projected/streamed pattern comfortably fits under the SAME cap — proving both (a) the fix actually
closes the gap, and (b) even the pattern that DOES still fail under real memory pressure fails HONESTLY
(a clean `MemoryError`, no hang) with the DB still usable afterward.

CALIBRATION (measured on this host, `.venv` Python 3.12, 60,000 `ScannerResult`+`ForwardReturn` rows at
one horizon, `record_json` padded to 4,000 bytes — mirroring the real table's dominant per-row cost, the
reason `scanner_results` is this project's largest table): baseline (import app + open session) VmPeak
~99-100 MB; the OLD pre-rewrite whole-partition `.all()` pattern measured ~587 MB (601,524 KB); the NEW
rewritten column-projected + `yield_per`-streamed pattern measured ~255 MB (260,720 KB). `CAP_KB` below
(420,000 KB / ~410 MB) sits comfortably between the two — OLD is short by ~181,524 KB, NEW has ~159,280 KB
of margin — and is verified empirically by the tests below (not just asserted).

TC-4 mirrors iter-13's actual trigger shape (4 concurrent backfills' finalize hooks + a diagnostic read,
not a single sequential process) with a `ThreadPoolExecutor`: each thread opens its OWN `Session` against
a SHARED file-based engine — the same way a real multi-threaded ASGI server's request-handling threads
each independently call into `compute_forward_aggregates`/`forward_aggregates_cached`.
"""
from __future__ import annotations

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import insert
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import compute_forward_aggregates, forward_aggregates_cached
from app.models import ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun

BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)  # apps/backend — for the child subprocess's sys.path
HORIZON = 20  # cfg.walk_forward.default_horizon
N_ROWS = 60_000
RECORD_JSON_BYTES = 4_000  # mirrors the real table's dominant per-row cost (record_json blobs)
# Empirically measured cap (see module docstring): traps the OLD unbounded `.all()` pattern (~587 MB
# need) while the NEW streamed pattern (~255 MB need) comfortably fits under it, with margin on both sides.
CAP_KB = 420_000
# Generous vs. the real `database.pragmas.busy_timeout_ms` (30s) — a hang would exceed this; a clean
# failure or success (even one that legitimately waits out a SQLite busy-timeout) will not.
BOUNDED_TIMEOUT_S = 45.0


def _build_memory_pressure_db(db_path: Path) -> None:
    """60,000 `ScannerResult` + `ForwardReturn` rows at `HORIZON`, bulk-inserted (mirrors this test
    suite's own `insert(Table.__table__)` convention, e.g. `test_indexes.py`/`test_sectors.py`) for
    build speed, plus ONE pre-populated `ForwardAggregateCache` row (via the real, unconstrained
    rewritten path) so TC-3's "subsequent read... re-reading an existing ForwardAggregateCache row" has
    a real row to target."""
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    padding = "x" * RECORD_JSON_BYTES
    cfg = load_config()
    with Session(engine) as session:
        run = ScannerRun(
            asof_date=date(2025, 1, 15), created_at=datetime.now(timezone.utc), provider="seed",
            benchmark="SPY", regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.flush()
        run_id = run.id
        result_rows = [
            dict(
                run_id=run_id, ticker=f"SYM{i:06d}", name=f"SYM{i:06d}", sector="Technology",
                leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
                entry_quality_bucket="E", risk_score=0.0, risk_bucket="E", setup_status="Actionable",
                rank=(i % 500) + 1, record_json=padding, is_vcp=False,
                is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
            )
            for i in range(N_ROWS)
        ]
        session.execute(insert(ScannerResult.__table__), result_rows)
        fr_rows = [
            dict(
                run_id=run_id, symbol=f"SYM{i:06d}", horizon=HORIZON, asof_date=date(2025, 1, 15),
                entry_close=100.0, measured_date=date(2025, 2, 15), realized_return=0.01, max_drawdown=-0.02,
            )
            for i in range(N_ROWS)
        ]
        session.execute(insert(ForwardReturn.__table__), fr_rows)
        session.commit()
        forward_aggregates_cached(session, HORIZON, cfg, as_of=None)


@pytest.fixture(scope="module")
def memory_pressure_db(tmp_path_factory) -> Path:
    db_path = tmp_path_factory.mktemp("mem_pressure") / "mem.db"
    _build_memory_pressure_db(db_path)
    return db_path


# --------------------------------------------------------------------------------------------------
# TC-3 child-process probe: written to a temp .py file and run via
# `bash -c "ulimit -v <cap>; exec <python> <script> <db> <mode>"` (the plan's own suggested spawn shape)
# so the cap applies to the CHILD subprocess only, never to this pytest process itself.
# --------------------------------------------------------------------------------------------------
_CHILD_PROBE_TEMPLATE = '''
import sys
sys.path.insert(0, "__BACKEND_ROOT__")
from sqlmodel import Session, select
from app.config import load_config
from app.db import make_engine
from app.models import ForwardReturn, ScannerResult, ForwardAggregateCache
from app.engine.forward_testing import compute_forward_aggregates

db_path, mode, horizon = sys.argv[1], sys.argv[2], int(sys.argv[3])
engine = make_engine(f"sqlite:///{db_path}")
cfg = load_config()


def old_unbounded_read(session, horizon):
    """A verbatim copy of the PRE-rewrite whole-partition `.all()` pattern this iteration replaced —
    kept here only to prove the induced memory pressure is real (the defect this iteration fixes), never
    reintroduced into the shipped module."""
    fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
    fr_rows = session.exec(fr_stmt).all()
    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
    runs_with_fr = sorted({fr.run_id for fr in fr_rows})
    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    stock_obs = [
        {"ticker": res.ticker, "return": ret_by_run_symbol.get((res.run_id, res.ticker))}
        for res in results
    ]
    return len(stock_obs)


if mode == "old":
    try:
        with Session(engine) as session:
            n = old_unbounded_read(session, horizon)
        print(f"UNEXPECTED_SUCCESS n={n}")
    except MemoryError:
        print("GOT_MEMORYERROR")
        # a fresh session, in the SAME process, re-reading an EXISTING ForwardAggregateCache row —
        # proves no leaked lock/open transaction blocks recovery without a process restart.
        with Session(engine) as session:
            row = session.exec(
                select(ForwardAggregateCache).where(ForwardAggregateCache.horizon == horizon)
            ).first()
        print("SUBSEQUENT_READ_OK" if row is not None else "SUBSEQUENT_READ_FAILED_NO_ROW")
else:
    try:
        with Session(engine) as session:
            agg = compute_forward_aggregates(session, horizon, cfg, as_of=None)
        n = agg["overall"]["n"]
        print(f"SUCCESS n={n}")
    except MemoryError:
        print("UNEXPECTED_MEMORYERROR")
'''


def _write_child_probe(tmp_path: Path) -> Path:
    script_path = tmp_path / "_mem_probe_child.py"
    script_path.write_text(_CHILD_PROBE_TEMPLATE.replace("__BACKEND_ROOT__", BACKEND_ROOT))
    return script_path


def _run_child_probe(script_path: Path, db_path: Path, mode: str, cap_kb: int) -> subprocess.CompletedProcess:
    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path} {mode} {HORIZON}"
    return subprocess.run(
        ["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S,
    )


def test_tc3_old_unbounded_pattern_fails_honestly_under_real_memory_cap_and_recovers(
    memory_pressure_db, tmp_path
):
    """TC-3 (part 1): under a REAL, non-monkeypatched `ulimit -v` cap sized below what the pre-rewrite
    unbounded pattern needs, invoking that pattern raises `MemoryError` cleanly — no hang, no timeout —
    and a subsequent fresh-session read of an EXISTING `ForwardAggregateCache` row, in the SAME process,
    succeeds immediately afterward (no leaked lock / open transaction blocks recovery)."""
    script_path = _write_child_probe(tmp_path)
    start = time.monotonic()
    result = _run_child_probe(script_path, memory_pressure_db, "old", CAP_KB)
    elapsed = time.monotonic() - start

    assert elapsed < BOUNDED_TIMEOUT_S, f"child probe took {elapsed:.1f}s — treat as a hang, not a slow pass"
    assert "UNEXPECTED_SUCCESS" not in result.stdout, (
        f"the OLD unbounded pattern completed successfully under a {CAP_KB} KB cap — the cap is "
        f"miscalibrated (too loose) for this fixture; stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "GOT_MEMORYERROR" in result.stdout, (
        f"expected an honest MemoryError under the tightened cap; stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )
    assert "SUBSEQUENT_READ_OK" in result.stdout, (
        f"expected the same-process subsequent read to succeed after the MemoryError; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_tc3_rewritten_pattern_succeeds_under_the_same_cap_that_broke_the_old_one(
    memory_pressure_db, tmp_path
):
    """TC-3 (part 2, the fix proof): the REWRITTEN `compute_forward_aggregates`, invoked under the
    IDENTICAL `ulimit -v` cap that just broke the pre-rewrite pattern (previous test) against the SAME
    fixture, completes successfully — the bounded/streamed read needs materially less virtual memory."""
    script_path = _write_child_probe(tmp_path)
    start = time.monotonic()
    result = _run_child_probe(script_path, memory_pressure_db, "new", CAP_KB)
    elapsed = time.monotonic() - start

    assert elapsed < BOUNDED_TIMEOUT_S, f"child probe took {elapsed:.1f}s — treat as a hang, not a slow pass"
    assert "UNEXPECTED_MEMORYERROR" not in result.stdout, (
        f"the REWRITTEN bounded/streamed path hit MemoryError under the same {CAP_KB} KB cap the OLD "
        f"path needed to fail at — the fix does not hold at this fixture size; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert f"SUCCESS n={N_ROWS}" in result.stdout, (
        f"expected the rewritten path to succeed with all {N_ROWS} observations; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


# --------------------------------------------------------------------------------------------------
# TC-4 — concurrent-caller regression (mirrors iter-13's actual trigger shape: 4 concurrent backfills'
# finalize hooks + a diagnostic read, all targeting the SAME horizon's cache key at once)
# --------------------------------------------------------------------------------------------------
def _cached_caller(engine, horizon: int) -> dict:
    cfg = load_config()
    with Session(engine) as session:
        return forward_aggregates_cached(session, horizon, cfg, as_of=None)


def _direct_caller(engine, horizon: int) -> dict:
    cfg = load_config()
    with Session(engine) as session:
        return compute_forward_aggregates(session, horizon, cfg, as_of=None)


def test_tc4_concurrent_callers_all_complete_within_bounded_timeout(memory_pressure_db):
    """TC-4: 4 concurrent `forward_aggregates_cached` callers (mirroring 4 concurrent backfills' finalize
    hooks, all racing to warm/serve the SAME `(horizon, asof_key, dataset_version)` cache key — the
    `ForwardAggregateCache` unique-constraint race `forward_aggregates_cached`'s own
    `except Exception: session.rollback()` is designed to absorb) plus 1 direct/uncached
    `compute_forward_aggregates` caller (the 'diagnostic read' in iter-13's own trigger shape) — every
    caller returns within a bounded timeout, none left blocked, and every returned payload is byte-
    identical (the cache race changes WHO persists, never WHAT is computed)."""
    engine = make_engine(f"sqlite:///{memory_pressure_db}")
    n_cached_callers = 4

    with ThreadPoolExecutor(max_workers=n_cached_callers + 1) as pool:
        futures = [pool.submit(_cached_caller, engine, HORIZON) for _ in range(n_cached_callers)]
        futures.append(pool.submit(_direct_caller, engine, HORIZON))

        results = []
        errors = []
        for future in as_completed(futures, timeout=BOUNDED_TIMEOUT_S):
            try:
                results.append(future.result())
            except Exception as exc:  # a clean, isolated failure is acceptable — a hang is not
                errors.append(exc)

    assert len(results) + len(errors) == n_cached_callers + 1, "not every future completed — a caller hung"
    assert not errors, f"expected every caller to succeed cleanly (or at least return); got errors: {errors}"
    # byte-identity across all 5 concurrent callers: the cache-race changes only WHO persists the row,
    # never the computed VALUE — every payload must be identical to the direct/uncached read.
    first = results[0]
    for payload in results[1:]:
        assert payload == first, "concurrent callers returned DIFFERENT payloads for the same horizon/as_of"
    assert first["overall"]["n"] == N_ROWS
