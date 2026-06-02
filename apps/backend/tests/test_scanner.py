"""Scanner snapshots — the persistence-spine critical-anti-goal proofs (iter-5).

Each test below is a named proof of a critical anti-goal:
  - persists-complete-snapshot — a run writes its run + result/sector/theme child rows.
  - idempotent-and-immutable   — a second scan for a date never duplicates or mutates. *(Snapshots immutable)*
  - no-lookahead               — a run dated D is unaffected by bars dated > D.            *(No lookahead)*
  - latest-run-faithful        — the stored snapshot == the live engine output, field-by-field. *(Single source)*
  - risk-off-zero-actionable   — a "Risk-off" date stores 0 Actionable results.            *(Risk-Off gates Actionable → J-07)*
  - distinct-as-of-snapshots   — a common ticker's stored Leadership differs across dates.  *(J-08)*

The scanner is exercised through `run_scan` / `bootstrap_runs` with explicit (session, asof, cfg),
so these tests run on isolated temp engines and never touch the shared process engine.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import delete
from sqlmodel import Session, select

from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.scanner import bootstrap_runs, run_scan
from app.models import DailyPrice, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow
from app.seed_loader import load_seed


@pytest.fixture(scope="module")
def scanner_engine(tmp_path_factory, config, seed_dir):
    """An isolated temp DB with the real committed seed loaded ONCE for this module. Independent
    of the process engine (does not call set_engine), so scanner writes here don't affect other
    tests. `run_scan` is idempotent, so each test ensures its own runs without conflict."""
    db_path = tmp_path_factory.mktemp("scanner_db") / "scanner.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    summary = load_seed(engine, config, seed_dir)
    assert summary["loaded"] is True and summary["price_rows"] > 0
    return engine


def _child_snapshot(session: Session, run_id: int) -> dict:
    """A content-only fingerprint of a run's child rows (EXCLUDING auto PKs / run_id FK), so two
    runs of the same as-of date — even in different databases — compare byte-identically."""
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run_id).order_by(ScannerResult.rank)
    ).all()
    sectors = session.exec(
        select(SectorScoreRow).where(SectorScoreRow.run_id == run_id).order_by(SectorScoreRow.rank)
    ).all()
    themes = session.exec(
        select(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id).order_by(ThemeScoreRow.rank)
    ).all()
    return {
        # record_json is the complete canonical row dict (ticker/scores/setup/rank/…), so it is a
        # full content key for a result on its own.
        "results": [r.record_json for r in results],
        "sectors": [
            (s.ticker, s.kind, s.name, s.score, s.bucket, s.rs_vs_spy,
             s.dist_from_52w_high_pct, s.trend_label, s.components_json, s.rank)
            for s in sectors
        ],
        "themes": [
            (t.slug, t.name, t.score, t.bucket, t.members_json, t.return_1m, t.return_3m,
             t.breadth_pct, t.breadth_label, t.trend_label, t.components_json, t.rank)
            for t in themes
        ],
    }


def _risk_off_date(session: Session, config):
    """A configured bootstrap date the regime engine labels exactly 'Risk-off' (>=1 required)."""
    for d in config.scanner.bootstrap_dates:
        if score_regime(session, d, config)["label"] == "Risk-off":
            return d
    return None


def test_run_scan_persists_complete_snapshot(scanner_engine, config):
    with Session(scanner_engine) as session:
        asof = latest_data_date(session)
        run = run_scan(session, asof, config)
        assert run.id is not None
        assert run.asof_date == asof

        results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
        sectors = session.exec(select(SectorScoreRow).where(SectorScoreRow.run_id == run.id)).all()
        themes = session.exec(select(ThemeScoreRow).where(ThemeScoreRow.run_id == run.id)).all()

    # one result per universe stock; sectors = 11 GICS + industry ETFs; one theme row per theme
    assert len(results) == len(config.universe.symbols)
    assert len(sectors) == len(config.etfs.sector) + len(config.etfs.industry)
    assert len(themes) == len(config.themes)

    # typed columns + the lossless record_json agree (record_json is the complete canonical row)
    top = min(results, key=lambda r: r.rank)
    record = json.loads(top.record_json)
    assert record["ticker"] == top.ticker
    assert record["leadership"]["score"] == top.leadership_score
    assert record["leadership"]["bucket"] == top.leadership_bucket
    assert record["setup"]["status"] == top.setup_status
    assert record["rank"] == top.rank == 1


def test_run_scan_idempotent_and_immutable(scanner_engine, config):
    """Snapshots-immutable critical: a second scan for the same date yields exactly ONE run with
    the same id/created_at and byte-identical children — no duplicate, no mutation."""
    with Session(scanner_engine) as session:
        asof = latest_data_date(session)
        run_scan(session, asof, config)

    # capture the persisted state from a clean session
    with Session(scanner_engine) as session:
        run_a = session.exec(select(ScannerRun).where(ScannerRun.asof_date == asof)).one()
        id_a, created_a = run_a.id, run_a.created_at
        snap_a = _child_snapshot(session, id_a)

    # scan AGAIN for the same date
    with Session(scanner_engine) as session:
        run_b = run_scan(session, asof, config)
        assert run_b.id == id_a  # returned the existing run, not a new one

    # re-capture — still exactly one run, same created_at, byte-identical children
    with Session(scanner_engine) as session:
        runs_for_date = session.exec(select(ScannerRun).where(ScannerRun.asof_date == asof)).all()
        assert len(runs_for_date) == 1
        assert runs_for_date[0].created_at == created_a  # not mutated
        snap_c = _child_snapshot(session, id_a)
    assert snap_a == snap_c


def test_run_scan_no_lookahead(tmp_path, config, seed_dir):
    """No-lookahead critical: a run dated D computed against the FULL seed equals the run computed
    against a DB truncated to bars with date <= D — future bars (date > D) cannot influence it."""
    asof = max(config.scanner.bootstrap_dates)  # a historical as-of date well within the seed

    full = make_engine(f"sqlite:///{tmp_path / 'full.db'}")
    create_db_and_tables(full)
    load_seed(full, config, seed_dir)

    trunc = make_engine(f"sqlite:///{tmp_path / 'trunc.db'}")
    create_db_and_tables(trunc)
    load_seed(trunc, config, seed_dir)
    with Session(trunc) as session:
        session.execute(delete(DailyPrice).where(DailyPrice.date > asof))
        session.commit()
        assert latest_data_date(session) <= asof  # the truncation really removed future bars

    with Session(full) as session:
        run_full = run_scan(session, asof, config)
        snap_full = _child_snapshot(session, run_full.id)
    with Session(trunc) as session:
        run_trunc = run_scan(session, asof, config)
        snap_trunc = _child_snapshot(session, run_trunc.id)

    assert snap_full == snap_trunc


def test_latest_run_faithful_to_live_computation(scanner_engine, config):
    """Single-source critical: the latest persisted run is a FAITHFUL copy of the live engine —
    its per-stock record_json equals score_stocks(latest)["rows"] and its regime_* equals
    score_regime(latest), field-by-field. One value, two read paths — never two computations."""
    with Session(scanner_engine) as session:
        asof = latest_data_date(session)
        live_rows = score_stocks(session, asof, config)["rows"]
        live_regime = score_regime(session, asof, config)
        run = run_scan(session, asof, config)
        stored = session.exec(
            select(ScannerResult).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
        ).all()
        regime_score, regime_label = run.regime_score, run.regime_label
        regime_components = json.loads(run.regime_components_json)

    stored_rows = [json.loads(r.record_json) for r in stored]
    live_sorted = sorted(live_rows, key=lambda r: r["rank"])
    assert stored_rows == live_sorted  # faithful per-stock copy (no divergence)

    assert regime_score == live_regime["score"]
    assert regime_label == live_regime["label"]
    assert regime_components == live_regime["components"]


def test_risk_off_run_has_zero_actionable(scanner_engine, config):
    """Risk-Off-gates-Actionable critical (J-07 at unit level): a configured 'Risk-off' date stores
    regime_label == 'Risk-off' and ZERO results with setup_status == 'Actionable'."""
    with Session(scanner_engine) as session:
        riskoff = _risk_off_date(session, config)
        assert riskoff is not None, "expected >=1 configured bootstrap date labelled 'Risk-off'"
        run = run_scan(session, riskoff, config)
        results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
        label = run.regime_label

    assert label == "Risk-off"
    assert len(results) == len(config.universe.symbols)
    assert sum(1 for r in results if r.setup_status == "Actionable") == 0


def test_is_vcp_mirrors_record_json_flag(scanner_engine, config):
    """iter-11: the denormalized `is_vcp` column is a faithful MIRROR of `record_json`'s vcp.flagged
    for EVERY stored result — one `detect_vcp` output stored twice (typed column + lossless record),
    never a second computation. No row's flag is NULL/missing."""
    with Session(scanner_engine) as session:
        asof = latest_data_date(session)
        run = run_scan(session, asof, config)
        results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
    assert len(results) == len(config.universe.symbols)
    for r in results:
        assert isinstance(r.is_vcp, bool)
        assert r.is_vcp == json.loads(r.record_json)["vcp"]["flagged"]  # faithful mirror


def test_new_pattern_mirrors_match_record_json(scanner_engine, config):
    """iter-9: the denormalized `is_pullback_to_rising_dma` / `is_flat_base_breakout` columns are
    faithful MIRRORS of `record_json`'s `<name>.flagged` for EVERY stored result — one detector output
    stored twice (typed column + lossless record), never a second computation. No row's flag is NULL."""
    with Session(scanner_engine) as session:
        asof = latest_data_date(session)
        run = run_scan(session, asof, config)
        results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
    assert len(results) == len(config.universe.symbols)
    for r in results:
        record = json.loads(r.record_json)
        assert isinstance(r.is_pullback_to_rising_dma, bool)
        assert r.is_pullback_to_rising_dma == record["pullback_to_rising_dma"]["flagged"]
        assert isinstance(r.is_flat_base_breakout, bool)
        assert r.is_flat_base_breakout == record["flat_base_breakout"]["flagged"]


def test_risk_off_run_vcp_flagged_rows_stay_watchlist_not_actionable(scanner_engine, config):
    """VCP-is-a-pattern-not-a-status (critical) under the Risk-off gate: a VCP-flagged row is STILL
    'Risk-off-watchlist' (never Actionable) — the pattern flag never promotes a name past the gate."""
    with Session(scanner_engine) as session:
        riskoff = _risk_off_date(session, config)
        assert riskoff is not None, "expected >=1 configured bootstrap date labelled 'Risk-off'"
        run = run_scan(session, riskoff, config)
        results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
        label = run.regime_label
    assert label == "Risk-off"
    assert all(r.setup_status != "Actionable" for r in results)            # the gate holds
    flagged = [r for r in results if r.is_vcp]
    assert all(r.setup_status == "Risk-off-watchlist" for r in flagged)    # flagged rows still watchlist


def test_runs_are_distinct_as_of_snapshots(scanner_engine, config):
    """J-08 at unit level: a common ticker's STORED Leadership score differs between an older run
    and the latest run — each snapshot is a frozen as-of view, not a recomputation of today."""
    older = min(config.scanner.bootstrap_dates)
    with Session(scanner_engine) as session:
        latest = latest_data_date(session)
        run_old = run_scan(session, older, config)
        run_new = run_scan(session, latest, config)
        old_by_ticker = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == run_old.id)).all()
        }
        new_by_ticker = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == run_new.id)).all()
        }
        old_date, new_date = run_old.asof_date, run_new.asof_date

    assert old_date != new_date  # distinct as-of dates
    common = set(old_by_ticker) & set(new_by_ticker)
    assert common
    assert any(old_by_ticker[t] != new_by_ticker[t] for t in common)


def test_bootstrap_runs_idempotent_persists_all_dates(tmp_path, config, seed_dir):
    """`bootstrap_runs` persists a run for every configured date + the latest data date, and is
    idempotent — a second bootstrap creates nothing new and mutates nothing."""
    engine = make_engine(f"sqlite:///{tmp_path / 'boot.db'}")
    create_db_and_tables(engine)
    load_seed(engine, config, seed_dir)

    bootstrap_runs(engine, config)
    with Session(engine) as session:
        latest = latest_data_date(session)
        first = {r.asof_date: (r.id, r.created_at) for r in session.exec(select(ScannerRun)).all()}

    expected_dates = set(config.scanner.bootstrap_dates) | {latest}
    assert set(first) == expected_dates  # exactly the configured dates + latest

    bootstrap_runs(engine, config)  # second pass — must be a no-op
    with Session(engine) as session:
        second = {r.asof_date: (r.id, r.created_at) for r in session.exec(select(ScannerRun)).all()}
    assert second == first  # same ids + created_at → no duplicate, no mutation
