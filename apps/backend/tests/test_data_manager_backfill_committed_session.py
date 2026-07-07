"""J-68 — the multi-month backfill `'committed'`-session regression (closing the J-67 gap).

J-67 was marked passing in iter-12 on the offline parallel-vs-sequential equality + per-date COMPUTE
failure-isolation tests. But the LIVE multi-month Data Manager `backfill`/`both` job still crashed with
`This session is in 'committed' state` — because those tests only ever failed the per-date COMPUTE
(handled cleanly via the worker `compute_error` path, which never rolls back the orchestrating session),
never the per-date PERSIST after a PRIOR date had already committed on the SHARED orchestrating session.

Root cause (confirmed in source): the old `_persist` ran two inner commits on the SHARED orchestrating
`session` — `scanner.persist_run_payload` (commits at scanner.py:205) then
`forward_testing.backfill_run_forward_returns` (commits at forward_testing.py:289). When a LATER date's
persist raised AFTER a prior date had committed, the failure-isolation handler `_persist_isolated` called
`session.rollback()` on that already-committed shared session — the invalid `'committed'`-state path.

These tests drive the REAL `_do_backfill` orchestration (the exact path `start_data_job`
`backfill`/`both` uses) over a MULTI-MONTH range, OFFLINE, INCLUDING the failure-isolation branch on a
per-date PERSIST failure that fires only AFTER an earlier date committed — the case the iter-12 tests did
not exercise. They assert:

  (1) a multi-month range completes with NO committed-session error;
  (2) a forced SINGLE-date PERSIST failure (after earlier dates committed) is ISOLATED — that date
      `failed` with its error, the OTHER dates complete, terminal `partial`, no committed-session crash;
  (3) a re-run of the same range creates 0 new snapshots and raises no UNIQUE error (create-once / J-41);
  (4) outputs byte-identical to the `backfill_workers == 1` sequential run (J-53 equality preserved).

The seed-backed fixtures pay the heavy compute once per worker setting (module-scoped where shared).
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import forward_testing, scanner
from app.engine.data_manager import _trading_days, create_job, run_data_job
from app.models import ForwardReturn, ScannerResult, ScannerRun
from app.seed_loader import load_seed


def _with_backfill_workers(cfg, n: int):
    """A config copy overriding ONLY the J-53 backfill-pool size (the rest unchanged)."""
    ic = cfg.data_manager.import_chunking.model_copy(update={"backfill_workers": n})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    return cfg.model_copy(update={"data_manager": dm})


def _fresh_seed_engine(tmp_path, name: str):
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    db_path = tmp_path / f"{name}.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    return cfg, engine




def _daily_region_start(trading, cfg):
    """iter-18: the snapshot cadence bounds the DEEP region to monthly targets, so job-range tests pick
    their dates inside the config daily-density region (>= scanner.snapshot_cadence.daily_start), where
    every trading day is a valid backfill target — these proofs are cadence-independent."""
    start = cfg.scanner.snapshot_cadence.daily_start or trading[0]
    return next(i for i, d in enumerate(trading) if d >= start)

def _multi_month_range(engine, cfg, n_dates: int):
    """A contiguous range of `n_dates` trading days from deep in the seed calendar — long enough that
    several dates commit on the orchestrating session BEFORE a forced later-date failure (so the old
    `_persist_isolated` rollback would have hit an already-committed session)."""
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    assert len(trading) > 320, "seed should provide a long trading calendar"
    start_idx = _daily_region_start(trading, cfg) + 250
    in_range = trading[start_idx : start_idx + n_dates]
    assert len(in_range) == n_dates
    return in_range[0], in_range[-1], in_range


def _snapshot_facts(engine, in_range):
    """Row-level canonical facts per backfilled date — for the byte-identical parallel==sequential proof."""
    facts: dict = {}
    with Session(engine) as session:
        for d in in_range:
            run = scanner.get_run_for_date(session, d)
            if run is None:
                facts[d] = None
                continue
            results = session.exec(
                select(ScannerResult).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
            ).all()
            frs = session.exec(
                select(ForwardReturn)
                .where(ForwardReturn.run_id == run.id)
                .order_by(ForwardReturn.symbol, ForwardReturn.horizon)
            ).all()
            facts[d] = {
                "regime_score": run.regime_score,
                "regime_label": run.regime_label,
                "records": [r.record_json for r in results],
                "frs": [(fr.symbol, fr.horizon, fr.realized_return, fr.mae, fr.mfe,
                         fr.measured_date.isoformat(), fr.entry_close) for fr in frs],
            }
    return facts


# ==================================================================================================
# (1) the multi-month happy path completes with NO committed-session error — parallel AND sequential
# ==================================================================================================
@pytest.mark.parametrize("workers", [1, 4])
def test_multi_month_backfill_completes_no_committed_session_error(tmp_path, workers):
    """A MULTI-MONTH (12-trading-day) backfill driven through the REAL `_do_backfill` orchestration
    completes cleanly — every in-range date backfilled, terminal `ok`, NO committed-session crash — for
    BOTH the sequential (workers=1) and the parallel (workers=4) engine."""
    cfg, engine = _fresh_seed_engine(tmp_path, f"happy_{workers}")
    r_start, r_end, in_range = _multi_month_range(engine, cfg, 12)

    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, workers), engine=engine)

    assert summary["status"] == "ok", summary
    assert summary["dates_total"] == len(in_range)
    assert summary["dates_done"] == len(in_range)
    assert summary["snapshots_created"] == len(in_range)
    assert summary["date_failures"] == []
    # the error stream is clean — no committed-session message leaked through.
    joined = " ".join(summary.get("errors", []))
    assert "committed" not in joined.lower(), joined
    with Session(engine) as session:
        for d in in_range:
            assert scanner.get_run_for_date(session, d) is not None


# ==================================================================================================
# (2) a forced PERSIST failure on a LATER date (after earlier dates committed) is ISOLATED — the
#     exact case the iter-12 tests missed (they only failed the per-date COMPUTE).
# ==================================================================================================
@pytest.mark.parametrize("workers", [1, 4])
def test_persist_failure_after_prior_commit_is_isolated_not_committed_crash(tmp_path, monkeypatch, workers):
    """The J-68 crux: force the per-date PERSIST (`forward_testing.backfill_run_forward_returns`) to raise
    for ONE date that is NOT the first in the range — so earlier dates have ALREADY committed on the
    orchestrating boundary when the failure-isolation branch runs. The old code called `session.rollback()`
    on that already-committed SHARED session → `This session is in 'committed' state`. The fix must isolate
    the bad date (`failed` + honest error), let the OTHER dates complete, end `partial`, and NEVER raise a
    committed-session error. Runs for BOTH the sequential and the parallel engine (the parallel path's
    persist is still serialized on the orchestrating thread, so it exercises the same boundary)."""
    cfg, engine = _fresh_seed_engine(tmp_path, f"persist_boom_{workers}")
    r_start, r_end, in_range = _multi_month_range(engine, cfg, 8)
    bad_date = in_range[5]  # NOT the first — earlier dates commit before this one fails

    real_backfill_fr = forward_testing.backfill_run_forward_returns

    def _selective_fr(session, run, config=None):
        if run.asof_date == bad_date:
            raise RuntimeError(f"synthetic persist failure for {bad_date.isoformat()}")
        return real_backfill_fr(session, run, config)

    # patch the symbol the data_manager module actually calls (it imports the module, not the name).
    monkeypatch.setattr(forward_testing, "backfill_run_forward_returns", _selective_fr)

    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, workers), engine=engine)

    # the bad date isolated; the rest completed; terminal partial; NO committed-session crash.
    assert summary["status"] == "partial", summary
    assert summary["dates_total"] == len(in_range)
    assert summary["snapshots_created"] == len(in_range) - 1  # all but the one bad date
    assert len(summary["date_failures"]) == 1
    assert summary["date_failures"][0]["date"] == bad_date.isoformat()
    assert f"synthetic persist failure for {bad_date.isoformat()}" in summary["date_failures"][0]["error"]
    # the committed-session error must NOT appear anywhere in the failure detail or errors.
    blob = (summary["date_failures"][0]["error"] + " " + " ".join(summary.get("errors", []))).lower()
    assert "committed" not in blob, blob

    # the OTHER dates DID get a fully-persisted snapshot; the bad date did NOT (never fabricated). The
    # bad date's snapshot row must also be GONE — its isolated failure rolled back its OWN write, leaving
    # no half-written ScannerRun behind (a stranded run would crash a later create-once re-run on UNIQUE).
    with Session(engine) as session:
        for d in in_range:
            run = scanner.get_run_for_date(session, d)
            if d == bad_date:
                assert run is None, "the failed date must leave NO half-written snapshot"
            else:
                assert run is not None, d
                # the completed dates carry their forward returns too (full persist, not just the run row).
                fr_n = session.scalar(
                    select(func.count(ForwardReturn.id)).where(ForwardReturn.run_id == run.id)
                )
                assert fr_n > 0, f"a completed date should have forward returns: {d}"


# ==================================================================================================
# (3) create-once / idempotent re-run after a partial — the failed date now backfills, no UNIQUE crash
# ==================================================================================================
def test_rerun_after_isolated_failure_is_create_once(tmp_path, monkeypatch):
    """After an isolated persist failure leaves one date un-backfilled, a clean RE-RUN of the same range
    creates ONLY the missing date's snapshot (0 duplicate snapshots for the already-completed dates, no
    UNIQUE crash) — the J-41 create-once guard holds across the partial→retry boundary."""
    cfg, engine = _fresh_seed_engine(tmp_path, "rerun")
    r_start, r_end, in_range = _multi_month_range(engine, cfg, 6)
    bad_date = in_range[4]

    real_backfill_fr = forward_testing.backfill_run_forward_returns
    fail_enabled = {"on": True}

    def _selective_fr(session, run, config=None):
        if fail_enabled["on"] and run.asof_date == bad_date:
            raise RuntimeError("synthetic persist failure")
        return real_backfill_fr(session, run, config)

    monkeypatch.setattr(forward_testing, "backfill_run_forward_returns", _selective_fr)

    # first run — one date fails, the rest complete (partial).
    job1 = create_job("backfill", r_start, r_end)
    s1 = run_data_job(job1.job_id, config=_with_backfill_workers(cfg, 4), engine=engine)
    assert s1["status"] == "partial"
    assert s1["snapshots_created"] == len(in_range) - 1
    with Session(engine) as session:
        runs_after_first = session.scalar(select(func.count()).select_from(ScannerRun))
        created_before = {
            d: r.created_at
            for d in in_range
            if (r := scanner.get_run_for_date(session, d)) is not None
        }

    # re-run — the failure is now disabled; only the missing date is backfilled, no UNIQUE crash.
    fail_enabled["on"] = False
    job2 = create_job("backfill", r_start, r_end)
    s2 = run_data_job(job2.job_id, config=_with_backfill_workers(cfg, 4), engine=engine)

    assert s2["status"] == "ok", s2
    assert s2["dates_total"] == 1  # only the previously-failed date remains to backfill
    assert s2["snapshots_created"] == 1
    assert s2["date_failures"] == []
    with Session(engine) as session:
        runs_after_second = session.scalar(select(func.count()).select_from(ScannerRun))
        # exactly one NEW snapshot row added (the bad date) — nothing duplicated/overwritten.
        assert runs_after_second == runs_after_first + 1
        # every in-range date now has a snapshot, and the previously-completed ones were NOT overwritten.
        for d in in_range:
            run = scanner.get_run_for_date(session, d)
            assert run is not None, d
            if d in created_before:
                assert run.created_at == created_before[d], f"immutable: {d} must not be re-created"


# ==================================================================================================
# (4) parallel == sequential over a MULTI-MONTH range — the J-53 byte-identical guarantee survives the
#     transaction-ownership rewrite (a per-date write session must store the SAME canonical rows).
# ==================================================================================================
@pytest.fixture(scope="module")
def multi_month_equality(tmp_path_factory):
    """Backfill the SAME ~10-trading-day range on two fresh seed DBs — workers=4 (parallel) and workers=1
    (sequential) — through the rewired per-date-session orchestration, and capture row-level facts."""
    base = tmp_path_factory.mktemp("dm_committed_eq")
    cfg, par_engine = _fresh_seed_engine(base, "parallel")
    _, seq_engine = _fresh_seed_engine(base, "sequential")
    r_start, r_end, in_range = _multi_month_range(par_engine, cfg, 10)

    par_job = create_job("backfill", r_start, r_end)
    par_summary = run_data_job(par_job.job_id, config=_with_backfill_workers(cfg, 4), engine=par_engine)
    seq_job = create_job("backfill", r_start, r_end)
    seq_summary = run_data_job(seq_job.job_id, config=_with_backfill_workers(cfg, 1), engine=seq_engine)

    return {
        "in_range": in_range,
        "par_summary": par_summary,
        "seq_summary": seq_summary,
        "par_facts": _snapshot_facts(par_engine, in_range),
        "seq_facts": _snapshot_facts(seq_engine, in_range),
    }


def test_multi_month_parallel_equals_sequential(multi_month_equality):
    """Over a multi-month range, the parallel (workers=4) backfill stores BYTE-IDENTICAL ScannerRun +
    ScannerResult + ForwardReturn rows to the sequential (workers=1) baseline — the transaction-ownership
    rewrite (per-date write session) preserves the J-53 equality contract."""
    f = multi_month_equality
    assert f["par_summary"]["status"] == "ok"
    assert f["seq_summary"]["status"] == "ok"
    for d in f["in_range"]:
        par, seq = f["par_facts"][d], f["seq_facts"][d]
        assert par is not None and seq is not None, d
        assert par["regime_score"] == seq["regime_score"], d
        assert par["regime_label"] == seq["regime_label"], d
        assert par["records"] == seq["records"], d  # the lossless canonical row dict, verbatim
        assert par["frs"] == seq["frs"], d  # every realized forward return identical
