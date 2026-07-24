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
each independently call into `compute_forward_aggregates`/`forward_aggregates_ingest_cached`.

ops-hardening iter-15 (UT-04 fix) ADDS a second, clearly-separated test group at the bottom of this file
(see the banner comment below) proving the single-flight de-dup this iteration adds to the ingest-time
cache's MISS path: TC-1 (same-key concurrent-MISS de-dup), TC-2 (concurrent-write-during-read wall-clock
ratio — isolates candidate (c), WAL/session contention, from candidate (a)), and TC-8 (the fix's own
failure path never deadlocks a waiter). These are a DIFFERENT iteration's TC numbering than iter-14's OWN
TC-3/TC-4 above — named descriptively (never `test_tc1_`/`test_tc2_`) to avoid any ambiguity with
iter-14's existing test names.

ops-hardening iter-16 (J-08) renamed the function under test here: the former single `forward_aggregates_
cached` (no "_ingest_") split into an ingest-only compute-and-persist half (`forward_aggregates_ingest_
cached`, exercised below — the single-flight guard's home, UNCHANGED by the split) and a new read-only
serving half (`resolved_forward_aggregate_evidence`, covered by `test_forward_testing_serving_split.py`).
Every test in this file now proves iter-16's TC-17 ("single-flight still holds on the ingest-only path
post-split") by construction — same guard, same tests, new function name.
"""
from __future__ import annotations

import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import compute_forward_aggregates, forward_aggregates_ingest_cached
from app.models import DailyPrice, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun

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
        forward_aggregates_ingest_cached(session, HORIZON, cfg, as_of=None)


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
        return forward_aggregates_ingest_cached(session, horizon, cfg, as_of=None)


def _direct_caller(engine, horizon: int) -> dict:
    cfg = load_config()
    with Session(engine) as session:
        return compute_forward_aggregates(session, horizon, cfg, as_of=None)


def test_tc4_concurrent_callers_all_complete_within_bounded_timeout(memory_pressure_db):
    """TC-4: 4 concurrent `forward_aggregates_ingest_cached` callers (mirroring 4 concurrent backfills' finalize
    hooks, all racing to warm/serve the SAME `(horizon, asof_key, dataset_version)` cache key — the
    `ForwardAggregateCache` unique-constraint race `forward_aggregates_ingest_cached`'s own
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


# ======================================================================================================
# ops-hardening iter-15 (UT-04 fix) tests below — concurrency-safety of `forward_aggregates_ingest_cached`'s
# MISS path (a DIFFERENT iteration's TC numbering than iter-14's OWN TC-3/TC-4 above; named
# descriptively, never `test_tc1_`/`test_tc2_`, to avoid any ambiguity with iter-14's existing names).
#
# Root cause (measured during this iteration's development — see the dev handoff for the full write-up):
# reading the pre-fix `forward_aggregates_ingest_cached` directly confirmed NO de-duplication existed — a MISS
# always fell straight through to `compute_forward_aggregates` with no lock/in-flight marker. On this
# exact 60,000-row fixture shape, 5 concurrent same-key MISSes measured 5 real `compute_forward_
# aggregates` invocations and a 9.9x wall-clock blowup vs. a single baseline call PRE-fix; POST-fix (the
# de-dup test below), exactly 1 invocation and ~1.0x. A SEPARATE probe isolating candidate (c)
# (WAL/session contention, no redundant recomputation involved — the concurrent-write-during-read test
# below) measured only a 1.59x ratio under an aggressive concurrent-write load — well inside TC-2's 5.0x
# smoke-guard bound — so `app.db`'s session/WAL configuration is NOT touched this iteration.
# ======================================================================================================
TC2_N_ROWS = 100_000  # sized so a SINGLE uncontended compute_forward_aggregates call clears >=1.0s wall-
                      # clock with comfortable margin (measured ~1.7-1.8s at this size on this host) — a
                      # DISTINCT empirical sizing task from memory_pressure_db's memory-cap calibration
                      # above (iter-14's TC-3), so this is its OWN fixture rather than reusing/resizing it.


def _build_write_contention_db(db_path: Path) -> None:
    """`TC2_N_ROWS` `ScannerResult` + `ForwardReturn` rows at `HORIZON` — large enough that a single
    uncontended `compute_forward_aggregates` call takes >=1.0s wall-clock (empirically measured), so a
    background writer thread has a real window to contend with the read."""
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    padding = "x" * RECORD_JSON_BYTES
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
            for i in range(TC2_N_ROWS)
        ]
        session.execute(insert(ScannerResult.__table__), result_rows)
        fr_rows = [
            dict(
                run_id=run_id, symbol=f"SYM{i:06d}", horizon=HORIZON, asof_date=date(2025, 1, 15),
                entry_close=100.0, measured_date=date(2025, 2, 15), realized_return=0.01, max_drawdown=-0.02,
            )
            for i in range(TC2_N_ROWS)
        ]
        session.execute(insert(ForwardReturn.__table__), fr_rows)
        session.commit()


@pytest.fixture(scope="module")
def write_contention_engine(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("write_contention") / "wc.db"
    _build_write_contention_db(db_path)
    return make_engine(f"sqlite:///{db_path}")


def test_forward_aggregates_ingest_cached_dedups_concurrent_same_key_miss_to_one_compute(memory_pressure_db):
    """TC-1 (iter-15, UT-04 fix): N=5 concurrent `forward_aggregates_ingest_cached` callers requesting the SAME
    never-yet-cached `(horizon, asof_key, dataset_version)` key invoke the underlying heavy aggregation
    body (`compute_forward_aggregates`) EXACTLY ONCE for that key (call-count instrumentation) — proving
    the single-flight de-dup holds, not just that concurrent callers happen to agree on an answer (TC-4
    above already proved byte-identity without proving de-duplication — this is the missing proof). All
    N callers still return byte-identical payloads."""
    import app.engine.forward_testing as forward_testing_module

    engine = make_engine(f"sqlite:///{memory_pressure_db}")
    cfg = load_config()
    as_of = date(2025, 7, 1)  # a DISTINCT as_of — a genuine, still-uncached MISS on this shared fixture
    n_callers = 5

    call_count = {"n": 0}
    real = forward_testing_module.compute_forward_aggregates

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return real(*args, **kwargs)

    def _caller():
        with Session(engine) as session:
            return forward_testing_module.forward_aggregates_ingest_cached(session, HORIZON, cfg, as_of=as_of)

    forward_testing_module.compute_forward_aggregates = _counting
    try:
        with ThreadPoolExecutor(max_workers=n_callers) as pool:
            futures = [pool.submit(_caller) for _ in range(n_callers)]
            results = [f.result() for f in as_completed(futures, timeout=BOUNDED_TIMEOUT_S)]
    finally:
        forward_testing_module.compute_forward_aggregates = real

    assert len(results) == n_callers, "not every caller completed — a caller hung"
    assert call_count["n"] == 1, (
        f"expected compute_forward_aggregates to run exactly once for {n_callers} concurrent same-key "
        f"MISSes; it ran {call_count['n']} times — the single-flight de-dup did not hold"
    )
    first = results[0]
    for payload in results[1:]:
        assert payload == first, "concurrent callers returned DIFFERENT payloads for the same key"
    assert first["overall"]["n"] == N_ROWS


def test_compute_forward_aggregates_concurrent_write_during_read_ratio_bounded(write_contention_engine):
    """TC-2 (iter-15, UT-04 fix): isolates candidate (c) (WAL/session contention) from candidate (a)
    (redundant recomputation, proven separately by the de-dup test above) — a SINGLE
    `compute_forward_aggregates` call (never routed through the cache/single-flight wrapper) timed alone
    vs. timed while a background thread issues repeated committed writes throughout (mirrors ingest-warm
    write activity: new `DailyPrice` bars for an unrelated symbol, inserted and committed one at a time
    via its OWN session on the SAME shared engine). The ratio is a smoke guard against a gross
    regression, not a tight bound — TC-4's operator-supervised live pass on the full deep basis is the
    authoritative measurement."""
    cfg = load_config()

    with Session(write_contention_engine) as session:
        t0 = time.monotonic()
        baseline_payload = compute_forward_aggregates(session, HORIZON, cfg, as_of=None)
        baseline = time.monotonic() - t0
    assert baseline >= 1.0, (
        f"fixture too small for this host — baseline={baseline:.3f}s, need >=1.0s (bump TC2_N_ROWS)"
    )

    stop_event = threading.Event()
    write_count = {"n": 0}

    def _writer():
        with Session(write_contention_engine) as wsession:
            i = 0
            while not stop_event.is_set():
                wsession.add(DailyPrice(
                    symbol="ZZZWRITER", date=date(2020, 1, 1) + timedelta(days=i),
                    open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
                ))
                wsession.commit()
                write_count["n"] += 1
                i += 1

    writer_thread = threading.Thread(target=_writer, daemon=True)
    writer_thread.start()
    try:
        with Session(write_contention_engine) as session:
            t0 = time.monotonic()
            concurrent_payload = compute_forward_aggregates(session, HORIZON, cfg, as_of=None)
            concurrent = time.monotonic() - t0
    finally:
        stop_event.set()
        writer_thread.join(timeout=10)

    ratio = concurrent / baseline
    assert write_count["n"] > 0, (
        "the background writer never got a chance to commit — test is not exercising contention"
    )
    assert concurrent_payload == baseline_payload, (
        "concurrent writes to an UNRELATED symbol changed compute_forward_aggregates's own result"
    )
    assert ratio <= 5.0, (
        f"concurrent-vs-baseline ratio {ratio:.2f}x exceeds the 5.0x smoke-guard bound "
        f"(baseline={baseline:.3f}s, concurrent={concurrent:.3f}s, writes_during={write_count['n']})"
    )


def test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises(memory_pressure_db):
    """TC-8 (iter-15, UT-04 fix): when the OWNER of a same-key MISS's in-flight computation raises, a
    concurrent WAITING caller for that SAME key never blocks past the bounded timeout — it either raises
    its own clean, isolated error or independently recomputes and returns a byte-identical payload.
    Proves the single-flight fix's failure path cannot wedge a waiter (the fix's own `finally` releases
    the in-flight slot and wakes waiters on ANY exit, success or failure)."""
    import app.engine.forward_testing as forward_testing_module

    engine = make_engine(f"sqlite:///{memory_pressure_db}")
    cfg = load_config()
    as_of = date(2025, 6, 1)  # a DISTINCT as_of — a genuine, still-uncached MISS on this shared fixture

    owner_started = threading.Event()
    owner_may_raise = threading.Event()
    real = forward_testing_module.compute_forward_aggregates
    call_count = {"n": 0}

    def _owner_then_recover(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            owner_started.set()
            owner_may_raise.wait(timeout=10)
            raise RuntimeError("forced owner failure (TC-8 probe)")
        return real(*args, **kwargs)

    owner_result: dict = {}
    waiter_result: dict = {}

    def _owner_call():
        with Session(engine) as session:
            try:
                forward_testing_module.forward_aggregates_ingest_cached(session, HORIZON, cfg, as_of=as_of)
            except Exception as exc:  # noqa: BLE001 — captured for the assertion below, never swallowed silently
                owner_result["error"] = exc

    def _waiter_call():
        with Session(engine) as session:
            try:
                waiter_result["payload"] = forward_testing_module.forward_aggregates_ingest_cached(
                    session, HORIZON, cfg, as_of=as_of
                )
            except Exception as exc:  # noqa: BLE001
                waiter_result["error"] = exc

    forward_testing_module.compute_forward_aggregates = _owner_then_recover
    start = time.monotonic()
    try:
        owner_thread = threading.Thread(target=_owner_call)
        waiter_thread = threading.Thread(target=_waiter_call)
        owner_thread.start()
        assert owner_started.wait(timeout=10), "owner never claimed the in-flight slot"
        waiter_thread.start()
        time.sleep(0.2)  # let the waiter register as a non-owner before the owner is allowed to raise
        owner_may_raise.set()
        owner_thread.join(timeout=BOUNDED_TIMEOUT_S)
        waiter_thread.join(timeout=BOUNDED_TIMEOUT_S)
    finally:
        forward_testing_module.compute_forward_aggregates = real
    elapsed = time.monotonic() - start

    assert not owner_thread.is_alive(), "owner thread did not finish — treat as a hang"
    assert not waiter_thread.is_alive(), "waiter thread did not finish — treat as a hang"
    assert elapsed < BOUNDED_TIMEOUT_S, f"resolution took {elapsed:.1f}s — treat as a hang, not a slow pass"
    assert "error" in owner_result, "expected the owner's own forced exception to propagate to its caller"

    assert "error" in waiter_result or "payload" in waiter_result, (
        "the waiter neither raised a clean error nor returned a payload — the failure path is broken"
    )
    if "payload" in waiter_result:
        with Session(engine) as session:
            direct = real(session, HORIZON, cfg, as_of=as_of)
        assert waiter_result["payload"] == direct, "waiter's fallback payload was not byte-identical"


# ======================================================================================================
# ops-hardening iter-19 (J-06/J-07/J-08) TC-4 — concurrency-race safety for `backfill_run_forward_
# returns`'s NEW zero-write guard (forward_testing.py ~line 1365, added this iteration). This is a
# DISTINCT fixture/mechanism from every test group above: those all exercise `compute_forward_aggregates`
# / `forward_aggregates_ingest_cached` (the `forward_aggregate_cache` table). The test below exercises
# `backfill_run_forward_returns` (the SEPARATE, append-only `forward_returns` table), reached only via
# `GET /api/backtest`'s create-once population step (~line 140) — a different function, a different
# table, a different request-path mechanism entirely.
# ======================================================================================================
def test_iter19_concurrent_missing_run_backtest_calls_no_duplicate_rows_and_rollback_path_exercised(
    tmp_path,
):
    """iter-19 TC-4 (mandatory concurrency test, spec DoD): 5 concurrent `GET /api/backtest` calls for
    the SAME as-of whose forward returns are genuinely missing at request time. A `threading.Barrier`
    forces all 5 threads to finish their OWN pre-insert idempotency read (the `existing` SELECT inside
    `backfill_run_forward_returns`, immediately before it calls `_insert_run_forward_returns`) before ANY
    of them proceeds to stage or flush a single write — guaranteeing every caller's `existing` read saw
    the SAME empty state for the one genuinely-missing symbol, so all N stage the SAME rows and race at
    commit time, deterministically reproducing the concurrent-INSERT race
    `_commit_forward_returns_concurrency_safe` exists to absorb (iter-28, J-41) rather than leaving it to
    scheduling luck. The fixture pre-seeds every OTHER symbol this run would process (the benchmark ETFs
    `forward_symbols_for_run` always appends) as ALREADY complete, so `_insert_run_forward_returns`'s
    per-symbol loop `continue`s past every one of them without a further read — isolating the race to the
    ONE genuinely-missing scored ticker and to the explicit final commit this iteration's guard gates,
    rather than an unrelated mid-loop SQLAlchemy autoflush (see the dev handoff's Known Issues for that
    separate, pre-existing finding, out of scope here).

    Asserts: (a) all 5 calls complete with no unhandled exception, (b) `forward_returns` ends with no
    duplicate `(run_id, symbol, horizon)` key, and (c) the pre-existing `IntegrityError`-tolerant rollback
    path is ACTUALLY exercised at least once (call-count instrumented — proven by assertion, not merely
    reachable in theory)."""
    import app.api.backtest as backtest_module
    import app.engine.forward_testing as forward_testing_module

    engine = make_engine(f"sqlite:///{tmp_path / 'tc4_missing_run.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    horizons = cfg.walk_forward.horizons
    max_h = max(horizons)
    asof = date(2025, 3, 1)
    with Session(engine) as session:
        run = ScannerRun(
            asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.flush()
        run_id = run.id
        session.add(ScannerResult(
            run_id=run_id, ticker="AAA", name="AAA", sector="Technology", leadership_score=50.0,
            leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
            risk_bucket="C", setup_status="Actionable", rank=1, record_json="{}", is_vcp=False,
            is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
        ))
        session.add(DailyPrice(
            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        for i in range(1, max_h + 1):
            session.add(DailyPrice(
                symbol="AAA", date=asof + timedelta(days=i), open=100.0, high=101.0, low=99.0,
                close=100.0 + i, volume=1.0,
            ))
        session.flush()
        # Pre-seed every OTHER symbol this run's own `forward_symbols_for_run` would process (the
        # benchmark ETFs) as already fully backfilled -- see the docstring above for why.
        other_symbols = [
            s for s in forward_testing_module.forward_symbols_for_run(session, run, cfg) if s != "AAA"
        ]
        for sym in other_symbols:
            for h in horizons:
                session.add(ForwardReturn(
                    run_id=run_id, symbol=sym, horizon=h, asof_date=asof, entry_close=100.0,
                    measured_date=asof, realized_return=0.0,
                ))
        session.commit()

    n_callers = 5
    barrier = threading.Barrier(n_callers)
    real_insert = forward_testing_module._insert_run_forward_returns
    real_commit_safe = forward_testing_module._commit_forward_returns_concurrency_safe
    rollback_count = {"n": 0}

    def _synced_insert(*args, **kwargs):
        """Blocks every caller at a barrier BEFORE staging/flushing a single write (all 5 have already
        completed their OWN pre-insert `existing` read, taken by the unpatched caller just before this),
        then calls the real idempotency-check-and-insert step -- guaranteeing every caller saw the SAME
        empty state for the missing symbol and all N stage the SAME rows, so the race lands at the
        explicit commit below rather than resolving silently via natural scheduling."""
        barrier.wait(timeout=BOUNDED_TIMEOUT_S)
        return real_insert(*args, **kwargs)

    def _instrumented_commit(session):
        """Byte-for-byte the real `_commit_forward_returns_concurrency_safe` body, with a counter added
        so the IntegrityError-tolerant branch's use is PROVEN, not merely reachable in theory."""
        try:
            session.commit()
        except IntegrityError:
            rollback_count["n"] += 1
            session.rollback()

    def _caller(as_of_str: str) -> dict:
        with Session(engine) as thread_session:
            return backtest_module.backtest(as_of=as_of_str, session=thread_session)

    forward_testing_module._insert_run_forward_returns = _synced_insert
    forward_testing_module._commit_forward_returns_concurrency_safe = _instrumented_commit
    try:
        with ThreadPoolExecutor(max_workers=n_callers) as pool:
            futures = [pool.submit(_caller, asof.isoformat()) for _ in range(n_callers)]
            results = []
            errors = []
            for future in as_completed(futures, timeout=BOUNDED_TIMEOUT_S):
                try:
                    results.append(future.result())
                except Exception as exc:  # noqa: BLE001 -- captured for the assertion below, never swallowed
                    errors.append(exc)
    finally:
        forward_testing_module._insert_run_forward_returns = real_insert
        forward_testing_module._commit_forward_returns_concurrency_safe = real_commit_safe

    assert len(results) + len(errors) == n_callers, "not every caller completed -- treat as a hang"
    assert not errors, f"expected every caller to complete without an unhandled exception; got {errors}"
    assert all(r["is_latest"] is True for r in results)

    with Session(engine) as session:
        fr_rows = session.exec(
            select(ForwardReturn).where(ForwardReturn.run_id == run_id, ForwardReturn.symbol == "AAA")
        ).all()
    keys = [(fr.run_id, fr.symbol, fr.horizon) for fr in fr_rows]
    assert len(keys) == len(set(keys)), f"duplicate (run_id, symbol, horizon) key(s) found: {keys}"
    assert len(fr_rows) == len(horizons), (
        f"expected exactly one row per configured horizon for the one genuinely-missing scored ticker; "
        f"got {len(fr_rows)}"
    )

    assert rollback_count["n"] >= 1, (
        "expected the IntegrityError-tolerant rollback path to be exercised by at least one of the 5 "
        "concurrent callers racing to backfill the SAME genuinely-missing run"
    )


# ======================================================================================================
# ops-hardening iter-20 (J-06/J-07/J-08) — the NEW outer single-flight dispatch guard that takes the
# historical (`is_latest == False`) carve-out's compute OFF the request thread entirely
# (`forward_testing.py`'s `ensure_historical_forward_aggregates_dispatched` /
# `_run_historical_forward_aggregates_dispatch`, `_HIST_DISPATCH_LOCK` / `_HIST_DISPATCH_INFLIGHT`). A
# DIFFERENT guard from every group above (those all exercise the INNER per-horizon lock
# `forward_aggregates_ingest_cached` itself owns — unchanged by this iteration): this one decides whether
# the REQUEST THREAD spawns a background dispatch AT ALL, so the request thread never calls `event.wait()`
# on the inner lock in the first place.
# ======================================================================================================
def _seed_historical_run(session: Session, asof: date, ticker: str = "AAA") -> ScannerRun:
    """A minimal historical `ScannerRun` + one `ScannerResult` + its entry-day `DailyPrice` bar — enough
    for `resolved_run`'s `latest_data_date` check and for the historical dispatch to have something to
    compute (an all-NA horizon set is a legitimate, honest result; these tests assert compute-COUNT and
    dispatch-behavior, not non-empty content, mirroring `test_forward_testing_serving_split.py`'s own
    `endpoint_engine`-based historical tests)."""
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    session.add(ScannerResult(
        run_id=run.id, ticker=ticker, name=ticker, sector="Technology", leadership_score=50.0,
        leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
        risk_bucket="C", setup_status="Actionable", rank=1, record_json="{}", is_vcp=False,
        is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
    ))
    session.add(DailyPrice(
        symbol=ticker, date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
    ))
    return run


# Sized like this file's OWN `write_contention_engine` calibration (TC2_N_ROWS, module docstring): large
# enough IN TOTAL that a SINGLE uncontended `compute_forward_aggregates` call at this horizon clears
# >=1.0s wall-clock, so TC-3's "never blocks the request thread" claim is a REAL, measurable discriminator
# between the OLD synchronous ensure-loop (every one of the 5 concurrent requests would take >=1s: the
# owner computing, the other 4 waiting on the existing inner per-horizon lock) and the NEW dispatch (every
# request returns near-instantly regardless).
#
# Spread across `_TC20_FILLER_RUNS` SEPARATE runs (never attached to the ONE run actually requested) --
# `compute_forward_aggregates`'s cost scales with the TOTAL row count across the whole expanding window,
# but `compute_run_scorecard` / `backfill_run_forward_returns` (called on EVERY /backtest request
# regardless of this iteration's dispatch mechanism -- unrelated, unchanged code) are each scoped to ONE
# run's OWN rows. Attaching all the volume to the requested run itself (an earlier draft of this fixture)
# made THOSE two calls slow too, confounding the measurement: the request would be slow via a totally
# different, already-existing, out-of-scope code path (a real, reproducible finding, but not what TC-3
# tests) rather than via the historical ensure-loop this iteration actually changes. Spreading the volume
# across OTHER, older runs keeps the requested run's own per-request cost negligible while still making
# `compute_forward_aggregates`'s expanding-window aggregate genuinely slow. `record_json` is NOT padded
# (unlike `memory_pressure_db`/`write_contention_engine`, which pad it for a DIFFERENT concern -- real
# per-row memory footprint): `compute_forward_aggregates`'s own `ScannerResult` read is column-projected
# and never selects `record_json`, so the slow part (proven by `write_contention_engine`'s own
# measurement) is the CPU-bound Python-side grouping over N rows, not disk I/O for a column never read.
_TC20_FILLER_RUNS = 10
_TC20_ROWS_PER_FILLER_RUN = 10_000  # 10 * 10,000 = 100,000 total, matching write_contention_engine's own N


def test_iter20_concurrent_first_touch_historical_requests_dispatch_exactly_once(tmp_path):
    """TC-3 (mandatory concurrency test, spec DoD): N=5 concurrent `GET /api/backtest` calls for the SAME
    never-before-warmed historical `as_of` invoke `compute_forward_aggregates` EXACTLY `len(horizons)`
    times IN TOTAL (never `5 * len(horizons)` — the old per-request synchronous ensure-loop's bug this
    iteration fixes — never zero), and every one of the 5 calls returns FAST: the request thread never
    waits on the dispatched compute (proven by each call's own wall-clock against a fixture sized so the
    compute itself provably takes >=1s -- not just proven by the aggregate call-count)."""
    import app.api.backtest as backtest_module
    import app.engine.forward_testing as forward_testing_module

    engine = make_engine(f"sqlite:///{tmp_path / 'tc20_dispatch_once.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    asof = date(2024, 3, 1)
    latest_asof = date(2025, 1, 10)  # strictly LATER -> `asof` resolves is_latest=False
    heavy_horizon = cfg.walk_forward.horizons[0]
    with Session(engine) as session:
        _seed_historical_run(session, asof)
        # A strictly LATER run (bare -- no ScannerResult, no DailyPrice of its own) purely so `asof` above
        # is NOT the latest stored date (`_latest_stored_run_date` = max(ScannerRun.asof_date) only;
        # "AAA"'s own entry-day bar at `asof` already satisfies `latest_data_date`'s "a bar exists at all"
        # check). Deliberately NO post-`asof` DailyPrice bar anywhere: that keeps `observable_days == 0`
        # for `asof`'s own `backfill_run_forward_returns` create-once step, so it stays a cheap no-op for
        # every symbol -- isolating this test from the SEPARATE, already-flagged, out-of-scope
        # `_insert_run_forward_returns` concurrent-autoflush race (iter-19 dev handoff's Known Issues;
        # iter-19's own TC-4 sidesteps the identical hazard by pre-seeding its "other" symbols instead).
        session.add(ScannerRun(
            asof_date=latest_asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.flush()

        # `_TC20_FILLER_RUNS` SEPARATE, older runs (all strictly < `asof`, so all fall inside its expanding
        # window) each carrying `_TC20_ROWS_PER_FILLER_RUN` rows at `heavy_horizon` -- see the module note
        # above for why this volume lives on OTHER runs, never on the one actually requested.
        filler_run_ids: list[int] = []
        for f in range(_TC20_FILLER_RUNS):
            filler_run = ScannerRun(
                asof_date=date(2020, 1, 1) + timedelta(days=f), created_at=datetime.now(timezone.utc),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Risk-on",
                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(filler_run)
            session.flush()
            filler_run_ids.append(filler_run.id)
        session.commit()

        result_rows = [
            dict(
                run_id=filler_run_ids[i // _TC20_ROWS_PER_FILLER_RUN], ticker=f"SYM{i:06d}", name=f"SYM{i:06d}",
                sector="Technology", leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
                entry_quality_bucket="E", risk_score=0.0, risk_bucket="E", setup_status="Actionable",
                rank=(i % 500) + 1, record_json="{}", is_vcp=False,
                is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
            )
            for i in range(_TC20_FILLER_RUNS * _TC20_ROWS_PER_FILLER_RUN)
        ]
        session.execute(insert(ScannerResult.__table__), result_rows)
        fr_rows = [
            dict(
                run_id=filler_run_ids[i // _TC20_ROWS_PER_FILLER_RUN], symbol=f"SYM{i:06d}", horizon=heavy_horizon,
                asof_date=date(2020, 1, 1) + timedelta(days=i // _TC20_ROWS_PER_FILLER_RUN),
                entry_close=100.0, measured_date=date(2020, 1, 1) + timedelta(days=i // _TC20_ROWS_PER_FILLER_RUN),
                realized_return=0.01, max_drawdown=-0.02,
            )
            for i in range(_TC20_FILLER_RUNS * _TC20_ROWS_PER_FILLER_RUN)
        ]
        session.execute(insert(ForwardReturn.__table__), fr_rows)
        session.commit()

    # Calibration check (not the test's own claim): confirm THIS fixture actually makes a single
    # uncontended compute genuinely slow on this host -- if it does not, the "fast response" assertion
    # below would pass VACUOUSLY (true under both the old and new code) rather than as a real proof. Calls
    # the PURE `compute_forward_aggregates` directly (never the persisting `forward_aggregates_ingest_
    # cached` wrapper), so this has NO side effect on `ForwardAggregateCache` -- the concurrency test below
    # still observes a genuine never-before-warmed MISS, exactly as a real first-ever page view would.
    with Session(engine) as session:
        t0 = time.monotonic()
        compute_forward_aggregates(session, heavy_horizon, cfg, as_of=asof)
        calibration_elapsed = time.monotonic() - t0
    assert calibration_elapsed >= 1.0, (
        f"fixture too small for this host to prove non-blocking dispatch — a single uncontended "
        f"compute_forward_aggregates call took only {calibration_elapsed:.3f}s (need >= 1.0s); "
        f"bump _TC20_ROWS_PER_FILLER_RUN"
    )

    call_count = {"n": 0}
    real = forward_testing_module.compute_forward_aggregates

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return real(*args, **kwargs)

    def _caller():
        with Session(engine) as session:
            t0 = time.monotonic()
            result = backtest_module.backtest(as_of=asof.isoformat(), session=session)
            elapsed = time.monotonic() - t0
            return result, elapsed

    n_callers = 5
    forward_testing_module.compute_forward_aggregates = _counting
    try:
        with ThreadPoolExecutor(max_workers=n_callers) as pool:
            futures = [pool.submit(_caller) for _ in range(n_callers)]
            outcomes = [f.result() for f in as_completed(futures, timeout=BOUNDED_TIMEOUT_S)]

        assert len(outcomes) == n_callers, "not every concurrent caller completed — treat as a hang"
        results = [r for r, _elapsed in outcomes]
        elapsed_times = [elapsed for _r, elapsed in outcomes]
        assert all(r["is_latest"] is False for r in results)
        # the "never blocking" half: every one of the 5 requests returned fast — well under the >=1.0s the
        # calibration above just proved the compute itself genuinely costs, so none of them waited on it
        # (the OLD synchronous ensure-loop would have made every one of them take >=1.0s: the owner
        # computing, the other 4 waiting on the existing inner per-horizon lock).
        assert max(elapsed_times) < 0.5, (
            f"expected every concurrent request to return fast (never waiting on the >={calibration_elapsed:.2f}s "
            f"dispatched compute); slowest was {max(elapsed_times):.3f}s"
        )

        # Bounded poll for the single dispatched background compute to land, re-triggering a (harmless,
        # single-flight-guarded) dispatch on each iteration that is not yet ready — see the TC-7 test
        # below for why this is safe and cannot mask a real duplicate-compute bug.
        deadline = time.monotonic() + BOUNDED_TIMEOUT_S
        with Session(engine) as session:
            final = backtest_module.backtest(as_of=asof.isoformat(), session=session)
        while final["evidence_status"] != "ready":
            assert time.monotonic() < deadline, (
                f"evidence never reached 'ready' within {BOUNDED_TIMEOUT_S}s "
                f"(last evidence_status={final['evidence_status']!r}) — treat as a hang/regression"
            )
            time.sleep(0.02)
            with Session(engine) as session:
                final = backtest_module.backtest(as_of=asof.isoformat(), session=session)
    finally:
        forward_testing_module.compute_forward_aggregates = real

    assert final["evidence_asof"] == asof.isoformat()
    assert call_count["n"] == len(cfg.walk_forward.horizons), (
        f"expected compute_forward_aggregates to run exactly once per configured horizon "
        f"({len(cfg.walk_forward.horizons)}) across all {n_callers} concurrent first-touch requests; "
        f"it ran {call_count['n']} times — the outer dispatch guard did not de-duplicate correctly"
    )


def test_iter20_historical_dispatch_owner_failure_releases_guard_and_allows_redispatch(tmp_path):
    """TC-7 (spec DoD): when the dispatched background compute's OWNER raises before completing (a forced
    failure, mirroring `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`
    above), the outer guard is released (never a permanent wedge) so a SUBSEQUENT dispatch for the SAME
    identity can run, and this date eventually reaches `"ready"` — never a stuck `"not_yet_computed"`."""
    import app.engine.forward_testing as forward_testing_module

    engine = make_engine(f"sqlite:///{tmp_path / 'tc20_owner_raises.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    asof = date(2023, 2, 1)
    with Session(engine) as session:
        _seed_historical_run(session, asof)
        session.commit()

    real_ingest_cached = forward_testing_module.forward_aggregates_ingest_cached
    call_count = {"n": 0}

    def _boom_once_then_real(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("forced dispatch-owner failure (TC-7 probe)")
        return real_ingest_cached(*args, **kwargs)

    forward_testing_module.forward_aggregates_ingest_cached = _boom_once_then_real
    evidence = None
    try:
        with Session(engine) as session:
            forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)

        # Poll: read the evidence, and re-trigger a dispatch whenever it is not yet ready. A re-trigger is
        # a harmless no-op while a dispatch is still in flight (the outer guard's own single-flight
        # contract, unchanged) and a genuine re-dispatch the instant the guard clears — so this loop
        # cannot falsely pass on scheduling luck: it converges to "ready" iff the guard was actually
        # released after the forced failure, and times out (a real regression -- a permanent wedge) iff
        # it was not.
        deadline = time.monotonic() + BOUNDED_TIMEOUT_S
        while evidence is None or evidence["evidence_status"] != "ready":
            last_status = evidence["evidence_status"] if evidence is not None else None
            assert time.monotonic() < deadline, (
                f"never reached 'ready' within {BOUNDED_TIMEOUT_S}s after the forced owner failure -- "
                f"treat as a permanent wedge (last evidence_status={last_status!r})"
            )
            time.sleep(0.02)
            with Session(engine) as session:
                evidence = forward_testing_module.resolved_forward_aggregate_evidence(session, asof, cfg)
                if evidence["evidence_status"] != "ready":
                    forward_testing_module.ensure_historical_forward_aggregates_dispatched(session, asof, cfg)
    finally:
        forward_testing_module.forward_aggregates_ingest_cached = real_ingest_cached

    assert evidence["evidence_status"] == "ready"
    assert evidence["evidence_asof"] == asof.isoformat()
    assert call_count["n"] >= 2, (
        "expected the forced first failure (call 1) AND at least one successful re-dispatch afterward -- "
        f"got {call_count['n']} total calls"
    )
