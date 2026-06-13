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

import json
from datetime import date

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
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
from app.models import DailyPrice, DataProviderRun, ImportCheckpoint, ScannerRun
from app.seed_loader import all_seed_symbols, load_seed


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
    # force a small window so the range splits into >= 2 windows per symbol → the multi-window plan.
    ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": 10, "symbol_batch_size": 25})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    cfg = cfg.model_copy(update={"data_manager": dm})

    engine = make_engine(f"sqlite:///{tmp_path / 'multiwindow.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine, [date(2024, 1, 2), date(2024, 1, 3)])
    n_symbols = len(all_seed_symbols(cfg))

    # a ~30-day range with window_days=10 → 3 windows per symbol-batch (the multi-window fan-out).
    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 31), source="yahoo")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_CountingProvider(), sleep_fn=_noop_sleep)

    assert summary["symbols_total"] == n_symbols
    assert summary["symbols_ok"] == n_symbols  # DISTINCT — not n_symbols * windows (the 318/159 bug)
    assert summary["symbols_ok"] <= summary["symbols_total"]  # monotone, never exceeds the total


def test_progress_payload_has_heartbeat_and_activity(tmp_path):
    """J-66 — the job payload carries a last-progress HEARTBEAT timestamp and a CURRENT-ACTIVITY line
    (the UI renders "updated Ns ago" + what is being worked on). Honest metadata — present and non-empty
    after work ran."""
    cfg, engine = _fresh_seed_engine(tmp_path, "heartbeat")
    with Session(engine) as session:
        trading = data_manager._trading_days(session, cfg)
    r_start, r_end = trading[305], trading[306]
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
    r_start, r_end = trading[305], trading[308]
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
    ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": 90, "symbol_batch_size": 25})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    cfg = cfg.model_copy(update={"data_manager": dm})

    engine = make_engine(f"sqlite:///{tmp_path / 'covered.db'}")
    create_db_and_tables(engine)
    # build a real trading calendar: SPY bars across the fetch range (so the calendar covers the window).
    cal_dates = [date(2024, 1, d) for d in range(2, 31)]
    _seed_calendar(engine, cal_dates)
    symbols = all_seed_symbols(cfg)
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
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=counting, sleep_fn=_noop_sleep)

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
    ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": 90, "symbol_batch_size": 25})
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    cfg = cfg.model_copy(update={"data_manager": dm})

    engine = make_engine(f"sqlite:///{tmp_path / 'partial.db'}")
    create_db_and_tables(engine)
    cal_dates = [date(2024, 1, d) for d in range(2, 6)]  # 4 trading days
    _seed_calendar(engine, cal_dates)
    symbols = all_seed_symbols(cfg)
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
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep)

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
    r_start, r_end = trading[305], trading[307]
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
