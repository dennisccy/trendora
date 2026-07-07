"""iter-27 (J-85 + J-86) — confirm-gated regenerate-from-scratch snapshot rebuild + coverage diagnostic,
and the max-drawdown column stored once and surfaced everywhere.

J-85 proofs:
  - the rebuild CLEARS the snapshot set then CREATE-ONCE recomputes every covered date (no in-place UPDATE);
  - the committed PRICE seed (`daily_prices`) is UNTOUCHED by the rebuild;
  - determinism — a rebuild's snapshot fingerprints are byte-identical to a fresh from-seed compute;
  - the coverage diagnostic counts the universe members ABSENT from the latest snapshot (correct N; 0 full).

J-86 proofs:
  - `forward_returns.max_drawdown` is NULL exactly when `realized_return` is absent (the same NA gate);
  - the served `/api/stocks` + detail rows carry five paired `max_drawdown` values read VERBATIM;
  - the served theme/sector MDD is byte-identical to Backtest's `_leadership_returns` projection (J-06);
  - the Backtest + Research aggregates carry a mean-MDD beside each return stat.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import forward_testing, scanner
from app.engine.data_manager import (
    _coverage_diagnostic_absent,
    _trading_days,
    clear_snapshot_set,
    compute_coverage,
    create_job,
    run_data_job,
)
from app.engine.forward_testing import (
    backfill_forward_returns,
    compute_forward_aggregates,
    compute_run_scorecard,
)
from app.engine.scanner import bootstrap_runs
from app.engine.snapshot_serving import sectors_payload, stocks_payload, themes_payload
from app.engine.research import compute_event_study, compute_regime_setup_pattern_study, subject_catalog
from app.models import DailyPrice, ForwardReturn, ScannerResult, ScannerRun
from app.seed_loader import load_seed


# ==================================================================================================
# A warm seed DB shared by the read-side proofs (built once)
# ==================================================================================================
@pytest.fixture(scope="module")
def warm_engine(tmp_path_factory):
    """The committed seed loaded + warmed to the full walk-forward cadence ONCE (the same canonical
    engines the lifespan warm-up uses), so the read-side MDD proofs run against a fully-warm DB."""
    cfg = load_config()
    db_path = tmp_path_factory.mktemp("iter27_db") / "warm.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    summary = load_seed(engine, cfg, None)
    assert summary["loaded"] is True and summary["price_rows"] > 0
    bootstrap_runs(engine, cfg)
    backfill_forward_returns(engine, cfg)
    return engine, cfg


def _historical_run(session: Session) -> ScannerRun:
    """A historical run (the EARLIEST as-of date) so it has a full post-snapshot forward window — its
    forward returns / drawdowns are realized (not NA), unlike the latest seed-date run."""
    return session.exec(select(ScannerRun).order_by(ScannerRun.asof_date)).first()


# ==================================================================================================
# J-86 — max_drawdown stored once, NA exactly when realized_return is absent
# ==================================================================================================
def test_max_drawdown_null_exactly_when_realized_return_absent(warm_engine):
    """Every stored forward_returns row has a non-None realized_return (the table only stores realized
    rows), and a non-None max_drawdown — proving the MDD shares the EXACT NA gate (a row exists iff the
    realized return does; a short window inserts NO row, never a fabricated 0)."""
    engine, cfg = warm_engine
    with Session(engine) as session:
        rows = session.exec(select(ForwardReturn)).all()
    assert rows
    for r in rows:
        assert r.realized_return is not None
        assert r.max_drawdown is not None  # non-None iff realized_return is
        assert r.max_drawdown <= 1e-12     # <= 0 always (true peak-to-trough drop)


# ==================================================================================================
# J-86 — served stocks/detail rows carry five paired MDD values (verbatim); leaderboard==detail (J-06)
# ==================================================================================================
def test_stocks_rows_carry_paired_max_drawdown_columns(warm_engine):
    """Each served `/api/stocks` row carries `forward_returns` with one entry per configured horizon, and
    every entry carries BOTH `return` and `max_drawdown` (paired). The MDD is NA exactly where the return
    is NA, and <= 0 where present — read verbatim from the stored table, never fabricated."""
    engine, cfg = warm_engine
    horizons = list(cfg.walk_forward.horizons)
    with Session(engine) as session:
        run = _historical_run(session)
        payload = stocks_payload(session, run, cfg)
    assert payload["rows"]
    for row in payload["rows"]:
        frs = row["forward_returns"]
        assert [fr["horizon"] for fr in frs] == horizons  # one per configured horizon, in order
        for fr in frs:
            assert "max_drawdown" in fr  # paired column present on every entry
            if fr["return"] is None:
                assert fr["max_drawdown"] is None  # NA exactly where the return is NA
            elif fr["max_drawdown"] is not None:
                assert fr["max_drawdown"] <= 1e-12  # <= 0 where present


def test_stock_detail_mdd_identical_to_leaderboard(warm_engine):
    """J-06 single-source: the Stock-Detail forward_returns (incl. max_drawdown) for a ticker are
    byte-identical to that ticker's row on the leaderboard — one stored source, no recompute."""
    from app.engine.snapshot_serving import stock_detail_payload

    engine, cfg = warm_engine
    with Session(engine) as session:
        run = _historical_run(session)
        stocks = stocks_payload(session, run, cfg)
        ticker = stocks["rows"][0]["ticker"]
        leaderboard_frs = stocks["rows"][0]["forward_returns"]
        detail = stock_detail_payload(session, run, ticker, cfg)
    assert detail["row"]["forward_returns"] == leaderboard_frs


# ==================================================================================================
# J-86 / J-06 — themes/sectors served MDD == Backtest leadership_returns projection (identical)
# ==================================================================================================
def test_theme_sector_mdd_matches_backtest_leadership_returns(warm_engine):
    """The theme/sector forward-return columns' max_drawdown reads identically on the leaderboard and on
    Backtest's `leadership_returns` projection for the same date+horizon — proving one builder, one stored
    source (J-06), no second computation."""
    engine, cfg = warm_engine
    with Session(engine) as session:
        run = _historical_run(session)
        themes = themes_payload(session, run, cfg)
        sectors = sectors_payload(session, run, cfg)
        scorecard = compute_run_scorecard(session, run, cfg)

    # {(slug, horizon): max_drawdown} from Backtest's leadership_returns.themes
    bt_themes = {}
    bt_sectors = {}
    for h in scorecard["scorecard"]["by_horizon"]:
        for t in h["leadership_returns"]["themes"]:
            bt_themes[(t["slug"], h["horizon"])] = t["max_drawdown"]
        for s in h["leadership_returns"]["sectors"]:
            bt_sectors[(s["sector_etf"], h["horizon"])] = s["max_drawdown"]

    checked = 0
    for theme in themes["rows"]:
        for fr in theme["forward_returns"]:
            key = (theme["slug"], fr["horizon"])
            assert key in bt_themes, f"theme {key} missing from Backtest leadership_returns"
            assert fr["max_drawdown"] == bt_themes[key], f"{key}: leaderboard MDD != Backtest MDD"
            checked += 1
    for sector in sectors["rows"]:
        for fr in sector["forward_returns"]:
            key = (sector["ticker"], fr["horizon"])
            if key in bt_sectors:  # industry-ETF rows without a config sector mapping render NA, skip
                assert fr["max_drawdown"] == bt_sectors[key], f"{key}: leaderboard MDD != Backtest MDD"
                checked += 1
    assert checked > 0  # not vacuous


# ==================================================================================================
# J-86 — Backtest + Research aggregates carry a mean-MDD beside each return stat
# ==================================================================================================
def test_backtest_aggregate_has_mean_max_drawdown(warm_engine):
    """compute_forward_aggregates carries a `mean_max_drawdown` on overall + every grouped row (by_bucket /
    by_setup / by_regime / by_vcp), with the SAME NA discipline as the return aggregate."""
    engine, cfg = warm_engine
    horizon = cfg.walk_forward.default_horizon
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, horizon, cfg)
    assert "mean_max_drawdown" in agg["overall"]
    if agg["overall"]["n"] > 0 and agg["overall"]["mean_max_drawdown"] is not None:
        assert agg["overall"]["mean_max_drawdown"] <= 1e-12
    for key in ("by_bucket", "by_setup", "by_regime", "by_vcp"):
        assert all("mean_max_drawdown" in row for row in agg[key]), f"{key} rows missing mean_max_drawdown"


def test_research_aggregates_have_mean_max_drawdown(warm_engine):
    """The event study per-horizon rows AND the Regime×Setup×Pattern combination stats carry a
    `mean_max_drawdown` beside the return stats (read-only over the stored values)."""
    engine, cfg = warm_engine
    horizon = cfg.walk_forward.default_horizon
    subject = subject_catalog(cfg)[0]["key"]
    with Session(engine) as session:
        study = compute_event_study(session, subject, horizon, cfg)
        rsp = compute_regime_setup_pattern_study(session, horizon, cfg)
    assert all("mean_max_drawdown" in row for row in study["by_horizon"])
    assert all("mean_max_drawdown" in row["stats"] for row in rsp["rows"])


# ==================================================================================================
# J-85 — coverage diagnostic: absent-member count (correct N; 0 when full)
# ==================================================================================================
def test_coverage_diagnostic_zero_when_universe_fully_scored(warm_engine):
    """With the committed seed fully warmed, the resolved universe is scored in the latest snapshot, so the
    absent-member count is 0 (the UI shows NO banner). The denominator equals the universe size."""
    engine, cfg = warm_engine
    with Session(engine) as session:
        diag = _coverage_diagnostic_absent(session, cfg)
        cov = compute_coverage(session, cfg)
    # iter-33 (J-93): universe_count is the members RESOLVED at the latest snapshot date (the dynamic
    # point-in-time membership drawn from the committed candidate pool via `read_pool`), bounded by the
    # candidate-pool denominator carried beside it. iter-18 broadened the servable pool far beyond the
    # legacy static `cfg.universe.symbols` screen result, so the resolved membership is bounded by
    # `candidate_pool_count` (the pool it is drawn from) — NOT by `len(cfg.universe.symbols)`. Every
    # resolved member IS in the latest snapshot, so absent_count is still 0.
    assert 0 < diag["universe_count"] <= diag["candidate_pool_count"]
    assert diag["absent_count"] == 0  # every resolved-universe member is in the latest snapshot
    assert diag["absent_preview"] == []
    assert diag["latest_snapshot_date"] is not None
    # served on the SAME coverage block (no new endpoint)
    assert cov["absent_from_latest_snapshot"] == diag


def test_coverage_diagnostic_counts_absent_members():
    """A universe member that is NOT in the latest snapshot's scored set is counted as absent (correct N).
    Built on a tiny hand-made DB: one snapshot scoring only AAA, with a config universe of {AAA, BBB} →
    BBB is absent (N=1)."""
    cfg = load_config()
    # shrink the resolved universe to two names so the absent set is deterministic
    cfg = cfg.model_copy(deep=True)
    cfg.universe.symbols = ["AAA", "BBB"]
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    from datetime import datetime, timezone

    with Session(engine) as session:
        run = ScannerRun(
            asof_date=date(2024, 1, 5), created_at=datetime.now(timezone.utc), provider="seed",
            benchmark="SPY", regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="Aaa", sector="Technology",
            leadership_score=1.0, leadership_bucket="A", entry_quality_score=1.0, entry_quality_bucket="A",
            risk_score=1.0, risk_bucket="A", setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.commit()
        # iter-33 (J-93): pass the explicit hand-made universe — this test exercises the absent-COMPARISON
        # logic against a known set, not the point-in-time resolver (which would read the real seed pool).
        diag = _coverage_diagnostic_absent(session, cfg, universe=list(cfg.universe.symbols))
    assert diag["absent_count"] == 1
    assert diag["absent_preview"] == ["BBB"]
    assert diag["latest_snapshot_date"] == "2024-01-05"


def test_coverage_diagnostic_all_absent_when_no_snapshot():
    """No snapshot at all → every universe member is absent (nothing scored), latest_snapshot_date None —
    honest, never a fabricated coverage."""
    cfg = load_config().model_copy(deep=True)
    cfg.universe.symbols = ["AAA", "BBB", "CCC"]
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        diag = _coverage_diagnostic_absent(session, cfg, universe=list(cfg.universe.symbols))
    assert diag["absent_count"] == 3
    assert diag["latest_snapshot_date"] is None


# ==================================================================================================
# J-85 — the rebuild clears then create-once recomputes; the price seed is untouched; deterministic
# ==================================================================================================
def _snapshot_fingerprint(session: Session) -> dict:
    """A deterministic fingerprint of the snapshot set: per as-of date, the stored leadership scores by
    ticker — so two builds can be compared byte-for-byte (determinism / no-formula-change)."""
    fp: dict = {}
    for run in session.exec(select(ScannerRun).order_by(ScannerRun.asof_date)).all():
        rows = session.exec(
            select(ScannerResult.ticker, ScannerResult.leadership_score).where(ScannerResult.run_id == run.id)
        ).all()
        fp[run.asof_date.isoformat()] = sorted((t, s) for t, s in rows)
    return fp


def _reduced_seed_engine(tmp_path_factory, name: str, keep_days: int = 40):
    """A FILE-BACKED seeded DB whose trading calendar is reduced to the LAST `keep_days` trading days (so
    the full-calendar rebuild is fast while still exercising the REAL engines over multiple dates). A file
    DB is required because the rebuild's worker threads open their own connections — a `:memory:` DB is
    per-connection and the workers would see no tables. The bars BEFORE the cutoff are deleted (the rest of
    the committed seed is the price floor the scans read)."""
    cfg = load_config()
    db_path = tmp_path_factory.mktemp(name) / f"{name}.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg, None)
    with Session(engine) as session:
        from sqlalchemy import delete as _delete
        td = _trading_days(session, cfg)
        cutoff = td[-keep_days]
        session.execute(_delete(DailyPrice).where(DailyPrice.date < cutoff))
        session.commit()
    return cfg, engine


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory):
    """Build a seeded DB (reduced calendar), populate the snapshot set via a FIRST rebuild, capture its
    fingerprint + bar count + run ids, then run a SECOND `kind="rebuild"` job and capture the same — so the
    proofs can assert clear-then-create-once (new run ids), seed-untouched (bar count stable), and
    determinism (identical fingerprints across two from-scratch builds)."""
    cfg, engine = _reduced_seed_engine(tmp_path_factory, "rebuild_db", keep_days=40)

    # FIRST rebuild — builds the snapshot set from scratch over the full (reduced) calendar.
    job0 = create_job("rebuild", date(2024, 1, 1), date(2024, 1, 1))
    summary0 = run_data_job(job0.job_id, config=cfg, engine=engine)

    with Session(engine) as session:
        before = {
            "fingerprint": _snapshot_fingerprint(session),
            "bars": session.scalar(select(func.count()).select_from(DailyPrice)),
            "runs": session.scalar(select(func.count()).select_from(ScannerRun)),
            "created_at": {
                r.asof_date.isoformat(): r.created_at.isoformat()
                for r in session.exec(select(ScannerRun)).all()
            },
        }

    import time as _time
    _time.sleep(1.1)  # ensure a measurably-later wall clock so the rebuilt rows' created_at differ

    # SECOND rebuild — clears the first build's snapshot set and recreates it from scratch.
    job = create_job("rebuild", date(2024, 1, 1), date(2024, 1, 1))  # dates ignored by a rebuild
    summary = run_data_job(job.job_id, config=cfg, engine=engine)

    with Session(engine) as session:
        after = {
            "fingerprint": _snapshot_fingerprint(session),
            "bars": session.scalar(select(func.count()).select_from(DailyPrice)),
            "runs": session.scalar(select(func.count()).select_from(ScannerRun)),
            "created_at": {
                r.asof_date.isoformat(): r.created_at.isoformat()
                for r in session.exec(select(ScannerRun)).all()
            },
        }
    assert summary0["status"] in ("ok", "partial")
    return cfg, engine, before, after, summary


def test_rebuild_clears_then_creates_once_no_in_place_update(rebuilt):
    """The rebuild CLEARED the snapshot set then CREATE-ONCE recomputed it: every run row was freshly
    re-created (its `created_at` advanced vs the prior build — a DELETE-then-INSERT), NOT an in-place
    UPDATE of a live snapshot row (anti-goal: Snapshots immutable). The job created exactly one snapshot
    per covered date (`snapshots_created == runs`), proving it ran the full create-once path, not a no-op.
    (SQLite recycles deleted rowids, so the proof is the created_at advance, not new primary keys.)"""
    cfg, engine, before, after, summary = rebuilt
    assert before["runs"] > 0 and after["runs"] > 0
    assert after["runs"] == before["runs"]  # same number of covered dates rebuilt
    assert summary["status"] in ("ok", "partial")
    assert summary["snapshots_created"] == after["runs"]  # one fresh snapshot per covered date (not a no-op)
    # every rebuilt run was created AFTER the first build — proving a from-scratch DELETE-then-INSERT, never
    # an in-place UPDATE (an UPDATE would keep the original created_at).
    assert before["created_at"] and after["created_at"]
    for asof, ts in after["created_at"].items():
        assert asof in before["created_at"]
        assert ts > before["created_at"][asof], f"{asof}: created_at must advance on a from-scratch rebuild"


def test_rebuild_leaves_price_seed_untouched(rebuilt):
    """The committed PRICE seed (`daily_prices`) bar count is byte-identical before vs after the rebuild —
    the rebuild deletes ONLY snapshot rows, never a price bar (the committed seed is un-deletable)."""
    cfg, engine, before, after, summary = rebuilt
    assert after["bars"] == before["bars"] and after["bars"] > 0


def test_rebuild_is_deterministic(rebuilt):
    """A from-scratch rebuild reproduces the SAME snapshot fingerprints as the original build (same stored
    leadership scores per date) — it changes no canonical formula, only re-runs the create-once compute."""
    cfg, engine, before, after, summary = rebuilt
    assert after["fingerprint"] == before["fingerprint"]
    assert after["fingerprint"]  # not vacuously empty


def test_clear_snapshot_set_refuses_to_corrupt_seed(tmp_path_factory):
    """clear_snapshot_set deletes every snapshot row but reports bars_before == bars_after (the price seed
    is untouched) — the hard seed-safety invariant the rebuild relies on. (Runs on its OWN fresh file DB
    so no shared fixture is destroyed.)"""
    cfg, engine = _reduced_seed_engine(tmp_path_factory, "clear_db", keep_days=40)
    bootstrap_runs(engine, cfg)  # populate a few snapshot rows to clear
    with Session(engine) as session:
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
        result = clear_snapshot_set(session)
        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
    assert runs_before > 0
    assert result["bars_before"] == result["bars_after"] and result["bars_after"] > 0
    assert result["runs_cleared"] == runs_before
    assert runs_after == 0  # the snapshot set is fully cleared
