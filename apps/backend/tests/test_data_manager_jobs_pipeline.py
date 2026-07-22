"""iter-29 jobs-pipeline cluster (J-59 / J-60 / J-66) — the stage-resume + lifecycle + honest-progress
contracts, all provable OFFLINE with injected counting/fault providers + tiny DBs (no network, no
wall-clock). J-67 (transaction-sound parallel backfill + per-date isolation) lives in
`test_data_manager_backfill_parallel.py`.

  - J-59: stage-aware checkpoint records fetch completion; Resume after a forced backfill fault performs
          ZERO provider calls and re-runs only backfill; the checkpoint survives a simulated restart;
          the covered-range fetch planner skips a fully-covered (symbol, window); a partial window still
          fetches; per-(symbol, date) INSERT-new-only idempotency holds (no duplicate rows).
  - J-60: a job creates its DataProviderRun `running` row at START; exactly ONE terminal transition;
          the boot sweep marks an orphaned `running` row `interrupted`; counts/summary match the job
          payload; the session key never reaches the record/checkpoint/detail JSON/log.
  - J-66: the per-symbol completion counter counts DISTINCT symbols and never exceeds its total across a
          multi-window plan (the explicit `318/159` regression); heartbeat + current-activity present in
          the payload; the speedup figure is present in the BACKEND stages payload.
"""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.data_providers.seed_provider import symbol_to_filename
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager, scanner
from app.engine.data_manager import (
    JobProgress,
    RESUMABLE_CHECKPOINT_STATUSES,
    create_job,
    get_checkpoint,
    recent_runs,
    resume_data_job,
    run_data_job,
    sweep_orphaned_runs,
    unfinished_imports,
)
from app.engine.drift import read_drift_report
from app.models import DailyPrice, DataProviderRun, ImportCheckpoint, ScannerRun
from app.seed_loader import load_seed, price_load_symbols


def _noop_sleep(_seconds: float) -> None:
    """Zero-wall-clock sleep."""


# ==================================================================================================
# providers
# ==================================================================================================
class _CountingProvider(PriceProvider):
    """Returns one bar per (symbol, window start) and COUNTS every `get_daily` call so a test can assert
    ZERO provider calls on a resume-at-backfill."""

    def __init__(self):
        self.calls = 0
        self.symbols: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.calls += 1
        self.symbols.append(symbol)
        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def _fresh_seed_engine(tmp_path, name: str):
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine(f"sqlite:///{tmp_path / f'{name}.db'}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    return cfg, engine


def _with_backfill_workers(cfg, n: int):
    ic = cfg.data_manager.import_chunking.model_copy(update={"backfill_workers": n})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    return cfg.model_copy(update={"data_manager": dm})


def _seed_calendar(engine, dates) -> None:
    """A few SPY bars so a trading calendar / latest date exists for the fetch."""
    with Session(engine) as session:
        for d in dates:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()


# ==================================================================================================
# J-60 — lifecycle record created at START + one terminal transition + boot sweep
# ==================================================================================================
def test_job_creates_running_run_record_at_start(tmp_path):
    """J-60 — starting a backfill job creates its DataProviderRun `running` row IMMEDIATELY (the row
    exists before the job is registered finished), then UPDATEs that SAME row to its terminal `ok` state —
    one record, one transition (no second row)."""
    cfg, engine = _fresh_seed_engine(tmp_path, "lifecycle")
    # a future-dated range → no in-range trading days → a clean no-op backfill (fast + deterministic).
    job = create_job("backfill", date(2099, 1, 1), date(2099, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine)

    assert summary["status"] == "ok"
    with Session(engine) as session:
        rows = session.exec(
            select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)
        ).all()
    assert len(rows) == 1, "exactly ONE run-history record per job (created at start, UPDATEd at terminal)"
    row = rows[0]
    assert row.status == "ok"  # the single honest terminal transition
    assert row.finished_at is not None
    assert row.job_id == job.job_id


def test_running_row_visible_in_run_history_before_finish(tmp_path):
    """J-60 — the `running` row is visible in Run history the moment it is created (proved by inspecting
    the DB directly after `_create_run_record`, before the terminal UPDATE)."""
    cfg, engine = _fresh_seed_engine(tmp_path, "running_visible")
    prog = JobProgress(job_id="job-x", kind="backfill", start=date(2099, 1, 1), end=date(2099, 1, 2))
    data_manager._create_run_record(engine, cfg, prog)
    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "job-x")).first()
    assert row is not None
    assert row.status == "running"  # appears in history as in-flight from the start
    assert row.finished_at is None
    # it surfaces through recent_runs (the Run history list the UI reads)
    with Session(engine) as session:
        runs = recent_runs(session, cfg)
    assert any(r["status"] == "running" and r["kind"] == "backfill" for r in runs)


def test_boot_sweep_marks_orphaned_running_as_interrupted(tmp_path):
    """J-60 boot sweep — an orphaned `running` row (a job whose process died) is marked `interrupted` (an
    honest terminal state), never left stuck `running`, never deleted. Idempotent: a second sweep is a
    no-op. A terminal row is untouched."""
    cfg, engine = _fresh_seed_engine(tmp_path, "sweep")
    with Session(engine) as session:
        session.add(DataProviderRun(
            provider="yahoo", started_at=data_manager._utcnow(), status="running", job_id="orphan-1",
            message=json.dumps({"kind": "both", "start": "2024-01-01", "end": "2024-01-31"}),
        ))
        session.add(DataProviderRun(
            provider="yahoo", started_at=data_manager._utcnow(), finished_at=data_manager._utcnow(),
            status="ok", job_id="done-1", message=json.dumps({"kind": "backfill"}),
        ))
        session.commit()

    swept = sweep_orphaned_runs(engine)
    assert swept == 1  # only the orphaned running row
    with Session(engine) as session:
        orphan = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "orphan-1")).first()
        done = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "done-1")).first()
    assert orphan.status == "interrupted" and orphan.finished_at is not None
    assert done.status == "ok"  # a terminal row is untouched

    assert sweep_orphaned_runs(engine) == 0  # idempotent — nothing left running


def test_lifecycle_counts_match_job_payload(tmp_path):
    """J-60 — the terminal run record's counts/summary match the job's OWN payload (one bookkeeping
    source). A failed fetch records `failed` with the same symbol counts the job reports."""
    cfg, engine = _fresh_seed_engine(tmp_path, "counts")

    class _AllFail(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise ProviderUnavailableError(f"down for {symbol}")

    # a window BEYOND the seed range (2021..2026-05) so the covered-range planner skips nothing — every
    # symbol genuinely fetches and fails (→ `failed`), exercising the honest count match.
    job = create_job("fetch", date(2026, 9, 1), date(2026, 9, 2), source="yahoo")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_AllFail(), sleep_fn=_noop_sleep)
    assert summary["status"] == "failed"
    with Session(engine) as session:
        rows = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.status == "failed"
    assert row.symbols_failed == summary["symbols_failed"]
    assert row.symbols_ok == summary["symbols_ok"]


def test_session_key_never_persisted_in_lifecycle_record(tmp_path):
    """J-60 / anti-goal — the SESSION-ONLY pasted key never reaches the run-history record, the checkpoint,
    or the detail JSON (the `running` record carries kind/range/source, never the key)."""
    cfg, engine = _fresh_seed_engine(tmp_path, "nokey")
    secret = "super-secret-key-zzz"

    class _AllFail(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise ProviderUnavailableError(f"down for {symbol}")

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    run_data_job(job.job_id, config=cfg, engine=engine, provider=_AllFail(), api_key=secret, sleep_fn=_noop_sleep)
    with Session(engine) as session:
        rows = session.exec(select(DataProviderRun)).all()
        cps = session.exec(select(ImportCheckpoint)).all()
    blob = json.dumps([r.message for r in rows] + [r.provider for r in rows] + [c.symbol_plan_json for c in cps])
    assert secret not in blob


# ==================================================================================================
# J-66 — distinct-symbol completion counter (the 318/159 fix) + heartbeat + activity + speedup
# ==================================================================================================
def test_symbols_counter_distinct_across_multi_window_plan(tmp_path):
    """J-66 — the 318/159 regression: a fetch plan spanning 2+ date WINDOWS over the symbol set counts
    each symbol's `symbols_ok` ONCE (distinct), so `symbols_ok` never exceeds `symbols_total`
    (distinct-symbol count). With a 24-day window over a ~30-day range there are 2 windows per symbol; the
    OLD per-(symbol, window) increment would read 2x the symbol count."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    # force a small window so the range splits into >= 2 windows per symbol → the multi-window plan.
    ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": 10, "symbol_batch_size": 25})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    cfg = cfg.model_copy(update={"data_manager": dm})

    engine = make_engine(f"sqlite:///{tmp_path / 'multiwindow.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine, [date(2024, 1, 2), date(2024, 1, 3)])
    # J-13 (iter-20): a generic fetch now targets `price_load_symbols(cfg, seed_dir)` (context ∪ pool). Pin
    # an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) so it degrades honestly to the
    # SAME context-only set `all_seed_symbols` gave before — keeping this test fast/deterministic.
    n_symbols = len(price_load_symbols(cfg, tmp_path))

    # a ~30-day range with window_days=10 → 3 windows per symbol-batch (the multi-window fan-out).
    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 31), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_CountingProvider(), sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )

    assert summary["symbols_total"] == n_symbols
    assert summary["symbols_ok"] == n_symbols  # DISTINCT — not n_symbols * windows (the 318/159 bug)
    assert summary["symbols_ok"] <= summary["symbols_total"]  # monotone, never exceeds the total




def _daily_region_start(trading, cfg):
    """iter-18: the snapshot cadence bounds the DEEP region to monthly targets, so job-range tests pick
    their dates inside the config daily-density region (>= scanner.snapshot_cadence.daily_start), where
    every trading day is a valid backfill target — these proofs are cadence-independent."""
    start = cfg.scanner.snapshot_cadence.daily_start or trading[0]
    return next(i for i, d in enumerate(trading) if d >= start)

def test_progress_payload_has_heartbeat_and_activity(tmp_path):
    """J-66 — the job payload carries a last-progress HEARTBEAT timestamp and a CURRENT-ACTIVITY line
    (the UI renders "updated Ns ago" + what is being worked on). Honest metadata — present and non-empty
    after work ran."""
    cfg, engine = _fresh_seed_engine(tmp_path, "heartbeat")
    with Session(engine) as session:
        trading = data_manager._trading_days(session, cfg)
    _base = _daily_region_start(trading, cfg)
    r_start, r_end = trading[_base + 305], trading[_base + 306]
    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, 2), engine=engine)

    assert summary["last_progress_at"] is not None  # the heartbeat timestamp
    assert summary["current_activity"]  # a non-empty current-activity line
    assert "scanning" in summary["current_activity"]  # backfill names the date being scanned


def test_backfill_speedup_factor_in_backend_stages_payload(tmp_path):
    """J-66 — the SERVER computes the backfill speedup figure into the stages payload (the frontend only
    re-formats it; no client-side division). The figure is present and coherent (the per-date sum / the
    parallel wall-clock)."""
    cfg, engine = _fresh_seed_engine(tmp_path, "speedup")
    with Session(engine) as session:
        trading = data_manager._trading_days(session, cfg)
    _base = _daily_region_start(trading, cfg)
    r_start, r_end = trading[_base + 305], trading[_base + 308]
    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, 4), engine=engine)

    bf = summary["stages"]["backfill"]
    assert "speedup_factor" in bf  # the SERVER-side derivation (J-66 coherence-WARN residual cleared)
    if bf["speedup_factor"] is not None:  # honest NA possible on a tiny range; when present it is coherent
        expected = round(bf["per_date_seconds_sum"] / bf["elapsed_seconds"], 4)
        assert abs(bf["speedup_factor"] - expected) < 1e-6


def test_compute_speedup_honest_na():
    """J-66 — `_compute_speedup` returns None (honest NA) when either figure is missing/zero — never a
    fabricated ratio."""
    assert data_manager._compute_speedup(None, 1.0) is None
    assert data_manager._compute_speedup(1.0, None) is None
    assert data_manager._compute_speedup(0.0, 1.0) is None
    assert data_manager._compute_speedup(1.0, 0.0) is None
    assert data_manager._compute_speedup(4.0, 2.0) == 2.0


# ==================================================================================================
# J-59 — covered-range fetch planner (skip fully-covered (symbol, window); partial still fetches)
# ==================================================================================================
def test_covered_range_rerun_zero_provider_calls(tmp_path):
    """J-59 — a re-run of a fetch over an ALREADY fully-covered range performs ZERO provider calls for the
    covered symbols (the covered-range planner skips them against the trading calendar), reaching the end
    in seconds with `0 new bars` — never re-fetching a covered window."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": 90, "symbol_batch_size": 25})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    cfg = cfg.model_copy(update={"data_manager": dm})

    engine = make_engine(f"sqlite:///{tmp_path / 'covered.db'}")
    create_db_and_tables(engine)
    # build a real trading calendar: SPY bars across the fetch range (so the calendar covers the window).
    cal_dates = [date(2024, 1, d) for d in range(2, 31)]
    _seed_calendar(engine, cal_dates)
    # J-13 (iter-20): a generic fetch now targets `price_load_symbols(cfg, seed_dir)` (context ∪ pool). Pin
    # an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) so it degrades honestly to the
    # SAME context-only set `all_seed_symbols` gave before — keeping this test fast/deterministic.
    symbols = price_load_symbols(cfg, tmp_path)
    # pre-store EVERY symbol's bars across the whole calendar → the range is fully covered. SPY is already
    # seeded by `_seed_calendar` (the calendar anchor), so skip it to avoid a UNIQUE collision.
    with Session(engine) as session:
        for sym in symbols:
            if sym == "SPY":
                continue
            for d in cal_dates:
                session.add(DailyPrice(symbol=sym, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        bars_before = session.scalar(select(func.count()).select_from(DailyPrice))

    counting = _CountingProvider()
    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 30), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=counting, sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )

    assert counting.calls == 0, "a fully-covered range must perform ZERO provider calls (J-59 planner)"
    assert summary["status"] == "ok"
    assert summary["bars_fetched"] == 0  # 0 new bars
    assert summary["symbols_ok"] == len(symbols)  # the covered symbols are credited as done
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(DailyPrice)) == bars_before  # no duplicate rows


def test_partially_covered_window_still_fetches(tmp_path):
    """J-59 — a partially-covered window still FETCHES (a single missing trading day forces the fetch), and
    the per-(symbol, date) INSERT-new-only guard fills only the missing bars (no duplicate rows)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": 90, "symbol_batch_size": 25})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    cfg = cfg.model_copy(update={"data_manager": dm})

    engine = make_engine(f"sqlite:///{tmp_path / 'partial.db'}")
    create_db_and_tables(engine)
    cal_dates = [date(2024, 1, d) for d in range(2, 6)]  # 4 trading days
    _seed_calendar(engine, cal_dates)
    # J-13 (iter-20): a generic fetch now targets `price_load_symbols(cfg, seed_dir)` (context ∪ pool). Pin
    # an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) so it degrades honestly to the
    # SAME context-only set `all_seed_symbols` gave before — keeping this test fast/deterministic.
    symbols = price_load_symbols(cfg, tmp_path)
    # pre-store only the FIRST trading day for every symbol → each window is PARTIALLY covered. SPY's
    # day-0 bar is already seeded by `_seed_calendar`; skip it to avoid a UNIQUE collision.
    with Session(engine) as session:
        for sym in symbols:
            if sym == "SPY":
                continue
            session.add(DailyPrice(symbol=sym, date=cal_dates[0], open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    class _CalendarProvider(PriceProvider):
        """Returns a bar for every calendar date in the window so the gap is filled."""
        def __init__(self):
            self.calls = 0
        def get_daily(self, symbol, start=None, end=None):
            self.calls += 1
            return [Bar(date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0) for d in cal_dates]

    provider = _CalendarProvider()
    job = create_job("fetch", cal_dates[0], cal_dates[-1], source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )

    assert provider.calls > 0, "a partially-covered window must still fetch (J-59)"
    assert summary["status"] == "ok"
    # idempotency: each (symbol, date) appears once (the pre-stored day-0 bar is NOT duplicated).
    with Session(engine) as session:
        for sym in symbols[:5]:
            n = session.scalar(
                select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol == sym)
            )
            assert n == len(cal_dates)  # exactly the calendar — no duplicate of the pre-stored day


# ==================================================================================================
# J-59 — stage-aware checkpoint + zero-provider-call resume-at-backfill (+ restart survival)
# ==================================================================================================
def _both_job_fetch_done_backfill_fails(tmp_path, monkeypatch, name: str):
    """Run a `both` job over a real seed backfill range whose FETCH completes but whose BACKFILL fails
    (forced fault). Returns (cfg, engine, job_id, in_range). The fetch uses a counting provider; the
    backfill fault is injected via scanner.compute_run_payload raising."""
    cfg, engine = _fresh_seed_engine(tmp_path, name)
    with Session(engine) as session:
        trading = data_manager._trading_days(session, cfg)
    _base = _daily_region_start(trading, cfg)
    r_start, r_end = trading[_base + 305], trading[_base + 307]
    in_range = [d for d in trading if r_start <= d <= r_end]

    # FETCH leg: a counting provider that succeeds (the seed range is already covered → 0 calls anyway,
    # but the fetch STAGE still completes). BACKFILL leg: force every per-date compute to raise.
    def _boom(*_a, **_k):
        raise RuntimeError("forced backfill fault")
    monkeypatch.setattr(scanner, "compute_run_payload", _boom)

    counting = _CountingProvider()
    job = create_job("both", r_start, r_end, source="yahoo")
    summary = run_data_job(
        job.job_id, config=_with_backfill_workers(cfg, 4), engine=engine,
        provider=counting, sleep_fn=_noop_sleep,
    )
    return cfg, engine, job.job_id, in_range, summary


def test_both_job_backfill_fault_marks_failed_backfill_resumable(tmp_path, monkeypatch):
    """J-59 — a `both` job whose fetch completed but whose backfill failed leaves a `failed_backfill`
    durable checkpoint (resumable from the backfill stage), with `fetch` recorded in completed_stages. The
    Unfinished-imports surface offers it with the plain-language "failed at backfill — resumable from the
    backfill stage" state + the Resume action."""
    cfg, engine, job_id, in_range, summary = _both_job_fetch_done_backfill_fails(tmp_path, monkeypatch, "fb1")
    assert summary["status"] == "partial" or summary["status"] == "failed"

    with Session(engine) as session:
        cp = get_checkpoint(session, job_id)
        assert cp is not None
        assert cp.status == "failed_backfill"
        stages = json.loads(cp.completed_stages_json)
        assert "fetch" in stages and "backfill" not in stages
        # it is offered in the unified Unfinished-imports list as a resume-at-backfill row.
        rows = unfinished_imports(session, cfg)
    fb = [r for r in rows if r.get("import_id") == job_id]
    assert fb, "the failed-at-backfill job is offered in Unfinished imports"
    assert "resumable from the backfill stage" in fb[0]["state"].lower()
    assert "resume" in fb[0]["actions"]
    assert cp.status in RESUMABLE_CHECKPOINT_STATUSES


def test_resume_at_backfill_zero_provider_calls_completes(tmp_path, monkeypatch):
    """J-59 — Resuming a `failed_backfill` job (after CLEARING the backfill fault) performs ZERO provider
    calls (the fetch stage is skipped entirely) and re-runs ONLY the backfill, which now completes; the
    snapshots are created and the job ends `ok`."""
    cfg, engine, job_id, in_range, _ = _both_job_fetch_done_backfill_fails(tmp_path, monkeypatch, "fb2")
    # clear the backfill fault (restore the real compute) so the Resume's backfill succeeds.
    monkeypatch.undo()

    counting = _CountingProvider()
    resumed = resume_data_job(
        job_id, config=_with_backfill_workers(cfg, 4), engine=engine,
        provider=counting, sleep_fn=_noop_sleep,
    )
    assert counting.calls == 0, "resume-at-backfill must perform ZERO provider calls (fetch skipped)"
    assert resumed["status"] == "ok"
    assert resumed["snapshots_created"] == len(in_range)
    with Session(engine) as session:
        for d in in_range:
            assert scanner.get_run_for_date(session, d) is not None  # snapshots created on resume


def test_stage_checkpoint_survives_restart_resume_at_backfill(tmp_path, monkeypatch):
    """J-59 — the stage checkpoint SURVIVES a simulated process restart: after the failed-at-backfill job,
    a FRESH engine handle (new connection — the in-memory job is gone) reads the durable `failed_backfill`
    checkpoint and a Resume still starts at the backfill stage with zero provider calls."""
    cfg, engine, job_id, in_range, _ = _both_job_fetch_done_backfill_fails(tmp_path, monkeypatch, "fb3")
    monkeypatch.undo()
    db_path = str(engine.url).replace("sqlite:///", "")

    # simulate a restart: a brand-new engine pointed at the same on-disk DB (in-memory _JOBS is empty).
    fresh_engine = make_engine(f"sqlite:///{db_path}")
    with Session(fresh_engine) as session:
        cp = get_checkpoint(session, job_id)
        assert cp is not None and cp.status == "failed_backfill"  # the durable row survived

    counting = _CountingProvider()
    resumed = resume_data_job(
        job_id, config=_with_backfill_workers(cfg, 4), engine=fresh_engine,
        provider=counting, sleep_fn=_noop_sleep,
    )
    assert counting.calls == 0  # still zero provider calls after the restart
    assert resumed["status"] == "ok"
    with Session(fresh_engine) as session:
        for d in in_range:
            assert scanner.get_run_for_date(session, d) is not None


# ==================================================================================================
# iter-35 (J-21/B-304) — the post-fetch drift validation stage: runs end-to-end on a completed fetch,
# does NOT run on a resumable pause, does NOT re-run on a skip-fetch/backfill-only resume
# ==================================================================================================
def _light_fetch_engine(tmp_path, name: str):
    """A tiny engine for the drift-wiring tests below: schema only, NO committed-seed load. These tests
    fetch exactly one synthetic symbol and need no universe/sector/theme data, so they deliberately skip
    `load_seed`'s expensive full 30-year/590-symbol seed (unlike `_fresh_seed_engine` above) — narrower,
    faster, and avoids inflating this file's already-heavy total fixture-setup cost with four MORE full
    seed loads for tests that don't need one."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / f'{name}.db'}")
    create_db_and_tables(engine)
    return cfg, engine


class _FixedBarsProvider(PriceProvider):
    """Returns a FIXED, pre-configured set of bars per symbol (deterministic — drives a real drift
    comparison through the actual fetch pipeline, not just `build_drift_report` in isolation). Counts
    calls so a test can assert ZERO provider calls on a skip-fetch resume."""

    def __init__(self, bars_by_symbol: dict[str, list[Bar]]):
        self._bars = bars_by_symbol
        self.calls = 0

    def get_daily(self, symbol, start=None, end=None):
        self.calls += 1
        bars = self._bars.get(symbol, [])
        return [b for b in bars if (start is None or b.date >= start) and (end is None or b.date <= end)]


def _write_seed_csv(seed_dir: Path, symbol: str, bars: list[Bar]) -> None:
    """A tiny committed-seed CSV for ONE symbol, in the exact `SeedProvider`-readable shape (mirrors
    `data_manager._write_universe_csv`'s header/column shape)."""
    prices_dir = seed_dir / "prices"
    prices_dir.mkdir(parents=True, exist_ok=True)
    path = prices_dir / symbol_to_filename(symbol)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for bar in bars:
            writer.writerow({
                "date": bar.date.isoformat(), "open": bar.open, "high": bar.high,
                "low": bar.low, "close": bar.close, "volume": bar.volume,
            })


def test_drift_stage_writes_report_on_completed_fetch_end_to_end(tmp_path, monkeypatch):
    """A REAL fetch through the full `_run_job` pipeline, with a committed seed CSV re-adjusted vs the
    live provider's return, proves the drift artifact is correctly written end-to-end (not merely that
    `build_drift_report` works in isolation — this is the wiring itself)."""
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
    cfg, engine = _light_fetch_engine(tmp_path, "drift_e2e")
    d = date(2024, 3, 1)
    _seed_calendar(engine, [d])  # AAA has no prior bars -> the fetch is NOT J-59-covered, it really runs

    seed_dir = tmp_path / "seed_e2e"
    _write_seed_csv(seed_dir, "AAA", [Bar(date=d, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)])
    # the "live" fetch returns a RE-ADJUSTED close for the same date -- an adjustment seam.
    provider = _FixedBarsProvider({"AAA": [Bar(date=d, open=100.0, high=101.0, low=99.0, close=95.0, volume=1000.0)]})

    job = create_job("fetch", d, d)
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep,
        seed_dir=seed_dir, symbols=["AAA"],
    )
    assert summary["status"] == "ok"
    report = read_drift_report()
    assert report is not None
    assert report["status"] == "drift"
    assert report["affected"] == [
        {"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}
    ]


def test_drift_stage_writes_clean_report_when_fetch_matches_seed(tmp_path, monkeypatch):
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
    cfg, engine = _light_fetch_engine(tmp_path, "drift_clean_e2e")
    d = date(2024, 3, 1)
    _seed_calendar(engine, [d])

    seed_dir = tmp_path / "seed_clean_e2e"
    bar = Bar(date=d, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)
    _write_seed_csv(seed_dir, "AAA", [bar])
    provider = _FixedBarsProvider({"AAA": [bar]})  # byte-identical re-fetch

    job = create_job("fetch", d, d)
    run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep,
        seed_dir=seed_dir, symbols=["AAA"],
    )
    report = read_drift_report()
    assert report is not None and report["status"] == "clean" and report["affected"] == []


def test_drift_stage_does_not_run_on_a_resumable_pause(tmp_path, monkeypatch):
    """A persistent-429 fetch pauses `resumable` -- the chunk's bars were DISCARDED (never committed), so
    the drift stage must NOT run (there is nothing durably fetched to honestly compare)."""
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
    cfg, engine = _light_fetch_engine(tmp_path, "drift_resumable")
    d = date(2024, 3, 1)
    _seed_calendar(engine, [d])

    class _Always429(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise RateLimitError("HTTP 429 at https://provider/x")

    job = create_job("fetch", d, d)
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_Always429(), sleep_fn=_noop_sleep,
        seed_dir=tmp_path / "unused_seed", symbols=["AAA"],
    )
    assert summary["status"] == "resumable"
    assert read_drift_report() is None  # the stage never ran -- nothing written


def test_drift_stage_does_not_rerun_on_skip_fetch_backfill_only_resume(tmp_path, monkeypatch):
    """A `both` job whose FETCH stage completes (writing a real drift artifact) but whose BACKFILL stage
    fails resumes at the backfill stage with ZERO provider calls (J-59) -- the drift stage, which lives
    entirely inside the fetch branch, must NOT re-run on that resume: a resumed fetch with a provider that
    WOULD produce a different (drift) result if the fetch stage actually re-ran must leave the ORIGINAL
    artifact byte-identical."""
    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
    cfg, engine = _light_fetch_engine(tmp_path, "drift_skip_fetch")
    d = date(2024, 3, 1)
    _seed_calendar(engine, [d])

    seed_dir = tmp_path / "seed_skip_fetch"
    bar = Bar(date=d, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)
    _write_seed_csv(seed_dir, "AAA", [bar])
    provider = _FixedBarsProvider({"AAA": [bar]})  # clean -- byte-identical re-fetch

    def _boom(*_a, **_k):
        raise RuntimeError("forced backfill fault")

    job = create_job("both", d, d)
    with monkeypatch.context() as fault_mp:  # scoped -- restores compute_run_payload without undoing
        fault_mp.setattr(scanner, "compute_run_payload", _boom)  # the env var set above
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep,
            seed_dir=seed_dir, symbols=["AAA"],
        )
    assert summary["status"] in ("partial", "failed")
    first_report = read_drift_report()
    assert first_report is not None and first_report["status"] == "clean"

    with Session(engine) as session:
        cp = get_checkpoint(session, job.job_id)
        assert cp is not None and cp.status == "failed_backfill"
        stages = json.loads(cp.completed_stages_json)
        assert "fetch" in stages and "backfill" not in stages  # confirms this IS the skip-fetch resume path

    # a TELLTALE provider that would flip the artifact to "drift" if the fetch stage re-ran (it must not).
    # This fixture's tiny DB carries no real universe/sector data, so the resumed BACKFILL is kept under
    # the SAME harmless per-date fault (isolated, caught -- see `_record_date_failure`/`_do_backfill`
    # above) as the original run, keeping this test hermetic and independent of what a REAL scanner run
    # would need; only that the fetch stage (and therefore the drift check) did NOT re-run is asserted,
    # which is this test's entire point.
    telltale = _FixedBarsProvider({"AAA": [Bar(date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]})
    with monkeypatch.context() as resume_fault_mp:
        resume_fault_mp.setattr(scanner, "compute_run_payload", _boom)
        resume_data_job(
            job.job_id, config=cfg, engine=engine, provider=telltale, sleep_fn=_noop_sleep, seed_dir=seed_dir,
        )
    assert telltale.calls == 0, "resume-at-backfill must perform ZERO provider calls (fetch stage skipped)"
    assert read_drift_report() == first_report, "a skip-fetch resume must leave the drift artifact untouched"


# ==================================================================================================
# ops-hardening iter-9 (F1 — J-04 step 6): an INTERRUPTED job keeps its LAST PERSISTED PROGRESS.
# Before this iteration the numeric detail fields were written into the persisted row exactly ONCE, by
# `_finalize_run_record` — which a `kill -9` never reaches — so the boot sweep's `interrupted` row always
# carried the creation-time defaults and rendered as "0 snapshots · 0 trading days in range" no matter how
# far the job actually got (browser-verified live: J-04 step 6 / UT-10). A throttled checkpoint now freezes
# the CURRENT progress onto the still-OPEN `running` row as the backfill advances.
# ==================================================================================================
def _run_detail_json(engine, job_id: str) -> dict:
    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job_id)).one()
    return json.loads(row.message)


def test_interrupted_job_keeps_its_last_checkpointed_progress(tmp_path, monkeypatch):
    """J-04 step 6 — a job whose process dies mid-run leaves an `interrupted` row carrying the progress it
    had actually reached, NOT zeros. The death is simulated the only honest way an in-process test can: the
    terminal transition (`_finalize_run_record`) never runs, exactly as it never runs under `kill -9`."""
    cfg, engine = _fresh_seed_engine(tmp_path, "checkpoint_progress")
    with Session(engine) as session:
        trading = data_manager._trading_days(session, cfg)
    _base = _daily_region_start(trading, cfg)
    r_start, r_end = trading[_base + 305], trading[_base + 307]  # 3 trading days
    # The production checkpoint is time-throttled; a sub-second test would otherwise only ever record the
    # FIRST date. Zero interval => checkpoint after every date (the same code path, just unthrottled).
    monkeypatch.setattr(data_manager, "_RUN_RECORD_CHECKPOINT_INTERVAL_S", 0.0)
    monkeypatch.setattr(data_manager, "_finalize_run_record", lambda *a, **k: None)

    job = create_job("backfill", r_start, r_end)
    run_data_job(job.job_id, config=_with_backfill_workers(cfg, 1), engine=engine)

    assert sweep_orphaned_runs(engine) == 1  # the boot sweep claims the orphaned `running` row
    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
    assert row.status == "interrupted"
    assert row.finished_at is not None

    detail = json.loads(row.message)
    assert detail["dates_total"] == 3           # trading days in the requested range — was 0
    assert detail["dates_done"] == 3            # progress actually reached — was 0
    assert detail["snapshots_created"] == 3     # snapshots genuinely persisted — was 0
    assert detail["calendar_days"] == (r_end - r_start).days + 1
    assert detail["already_snapshotted"] == 0
    assert detail["error_other"] == 0
    # the finalize hook never ran on this dead job — its output stays honestly absent, never fabricated
    assert detail["aggregates_refreshed"] is None


def test_run_record_checkpoint_is_throttled_open_ended_and_never_fatal(tmp_path, monkeypatch):
    """The checkpoint writer's own contract: bounded write amplification (at most one UPDATE per interval),
    the row stays OPEN (`running`, no `finished_at`) so the boot sweep can still claim it, a job with no
    open row is a silent no-op (never a second row), and a write failure is never fatal to the job."""
    cfg, engine = _fresh_seed_engine(tmp_path, "checkpoint_unit")
    prog = JobProgress(job_id="job-cp", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 3))
    data_manager._create_run_record(engine, cfg, prog)
    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 0  # creation-time defaults

    prog.calendar_days, prog.dates_total, prog.dates_done, prog.snapshots_created = 3, 3, 1, 1
    data_manager._checkpoint_run_record(engine, prog)  # nothing checkpointed yet -> always writes
    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 1
    assert _run_detail_json(engine, "job-cp")["dates_done"] == 1

    prog.dates_done, prog.snapshots_created = 2, 2
    data_manager._checkpoint_run_record(engine, prog)  # INSIDE the throttle window -> not written
    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 1

    monkeypatch.setattr(data_manager, "_RUN_RECORD_CHECKPOINT_INTERVAL_S", 0.0)  # interval elapsed
    data_manager._checkpoint_run_record(engine, prog)
    assert _run_detail_json(engine, "job-cp")["snapshots_created"] == 2

    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "job-cp")).one()
    assert row.status == "running" and row.finished_at is None  # still OPEN for the boot sweep

    # a write failure is telemetry, not job control: a broken engine must not raise into the backfill loop
    data_manager._checkpoint_run_record(
        make_engine("sqlite:////nonexistent-dir-for-checkpoint-test/x.db"), prog
    )

    # once the row is terminal there is no open row to checkpoint -> silent no-op, never a second record
    prog.status, prog.finished_at = "ok", data_manager._utcnow()
    data_manager._finalize_run_record(engine, cfg, prog)
    prog.snapshots_created = 99
    data_manager._checkpoint_run_record(engine, prog)
    with Session(engine) as session:
        rows = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "job-cp")).all()
    assert len(rows) == 1
    assert rows[0].status == "ok"
    assert json.loads(rows[0].message)["snapshots_created"] == 2  # the terminal value, not the post-hoc 99


def test_interrupted_before_first_date_still_keeps_the_computed_range(tmp_path, monkeypatch):
    """ops-hardening iter-9 AUDIT (F1 completion) — a job killed BEFORE its first date is persisted (the
    shared bar-cache prefill window, minutes long on the deep basis) must still show the range it had
    already computed, not "0 trading days in range". The per-date checkpoint alone cannot cover this
    window: it only writes once a date has been persisted."""
    cfg, engine = _fresh_seed_engine(tmp_path, "checkpoint_preloop")
    with Session(engine) as session:
        trading = data_manager._trading_days(session, cfg)
    _base = _daily_region_start(trading, cfg)
    r_start, r_end = trading[_base + 305], trading[_base + 307]  # 3 trading days

    # Death during the prefill: the bar-cache load never returns, and the terminal transition
    # (`_finalize_run_record`) never runs — exactly what `kill -9` does at that instant.
    def _die_in_prefill(*_a, **_k):
        raise RuntimeError("simulated process death during the shared bar-cache prefill")

    monkeypatch.setattr(data_manager, "prefilled_bar_cache", _die_in_prefill)
    monkeypatch.setattr(data_manager, "_finalize_run_record", lambda *a, **k: None)

    job = create_job("backfill", r_start, r_end)
    run_data_job(job.job_id, config=_with_backfill_workers(cfg, 1), engine=engine)

    assert sweep_orphaned_runs(engine) == 1
    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
    assert row.status == "interrupted"
    detail = json.loads(row.message)
    assert detail["dates_total"] == 3                                   # the real range — was 0
    assert detail["calendar_days"] == (r_end - r_start).days + 1        # the real span — was null
    assert detail["snapshots_created"] == 0                             # honest: none were created yet
    assert detail["aggregates_refreshed"] is None                       # the finalize hook never ran
