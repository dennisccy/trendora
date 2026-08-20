"""app.engine.session_delta (goal-market-compass iter-2, J-02) — session-over-session change detection.

File-scoped synthetic fixture (a fresh in-memory SQLite DB with hand-built `ScannerRun` /
`ScannerResult` / `SectorScoreRow` / `ThemeScoreRow` rows) — never `loaded_engine` (the full 30y-basis
fixture is a multi-hour cost this module's pure comparison logic does not need).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import load_config
from app.engine.session_delta import KIND_BREADTH, KIND_MARKET, KIND_SECTOR, KIND_STOCK, KIND_THEME, compute_delta, find_previous_run
from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow


@pytest.fixture()
def cfg():
    return load_config()


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng


def _mk_run(session: Session, asof: date, regime_score: float, b50, b200) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof,
        created_at=datetime.now(timezone.utc),
        provider="seed",
        benchmark="SPY",
        regime_score=regime_score,
        regime_label="Expansion",
        regime_components_json="[]",
        breadth_above_50dma=b50,
        breadth_above_200dma=b200,
        new_high_low_json="{}",
        candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _mk_result(session: Session, run_id: int, ticker: str, score: float, bucket: str) -> None:
    session.add(
        ScannerResult(
            run_id=run_id,
            ticker=ticker,
            name=ticker,
            sector="Technology",
            leadership_score=score,
            leadership_bucket=bucket,
            entry_quality_score=70.0,
            entry_quality_bucket="B",
            risk_score=40.0,
            risk_bucket="C",
            setup_status="Breakout-watch",
            rank=1,
            record_json=json.dumps({
                "ticker": ticker,
                "invalidation": {"basis": "50-DMA", "ma_period": 50, "level": 100.0, "price": 110.0, "note": f"{ticker} invalidation note"},
                "risk_budget": {"atr_pct": {"value": 3.0, "percentile": 0.5}},
            }),
        )
    )


def _mk_sector(session: Session, run_id: int, ticker: str, name: str, rank: int) -> None:
    session.add(
        SectorScoreRow(
            run_id=run_id, ticker=ticker, kind="sector", name=name, members_json="[]",
            score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=rank,
        )
    )


def _mk_theme(session: Session, run_id: int, slug: str, name: str, rank: int) -> None:
    session.add(
        ThemeScoreRow(
            run_id=run_id, slug=slug, name=name, score=80.0, bucket="A",
            members_json="[]", breadth_label="universe-relative", trend_label="Uptrend",
            components_json="{}", rank=rank,
        )
    )


@pytest.fixture()
def two_runs(engine, cfg):
    """run_a (earliest) -> run_b (7 days later) with hand-picked, KNOWN deltas:
      market:  50 -> 58   (delta 8,  >= threshold 5  -> CHANGE)
      breadth 50dma: 40 -> 44 (delta 4, <  threshold 5 -> SUPPRESSED)
      breadth 200dma: 45 -> 52 (delta 7, >= threshold 5 -> CHANGE)
      sector XLK: rank 1 -> 3 (delta 2, >= threshold 2 -> CHANGE)
      sector XLF: rank 2 -> 2 (delta 0, <  threshold 2 -> SUPPRESSED)
      sector XLE: rank 3 -> 1 (delta 2, >= threshold 2 -> CHANGE)
      theme  ai:  rank 1 -> 3 (delta 2, >= threshold 2 -> CHANGE)
      theme  ev:  rank 2 -> 1 (delta 1, <  threshold 2 -> SUPPRESSED)
      stock AAPL: bucket C -> A, score 60 -> 85 (delta 25, >= threshold 8, bucket crossed -> CHANGE)
      stock MSFT: bucket A -> A, score 90 -> 91 (unchanged bucket -> not reported at all)
      stock NEWC: absent -> present, score 70, bucket C -> CHANGE (new-to-universe, unconditional)
    """
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 1, 1), 50.0, 40.0, 45.0)
        run_b = _mk_run(session, date(2024, 1, 8), 58.0, 44.0, 52.0)

        _mk_sector(session, run_a.id, "XLK", "Technology", 1)
        _mk_sector(session, run_a.id, "XLF", "Financials", 2)
        _mk_sector(session, run_a.id, "XLE", "Energy", 3)
        _mk_sector(session, run_b.id, "XLK", "Technology", 3)
        _mk_sector(session, run_b.id, "XLF", "Financials", 2)
        _mk_sector(session, run_b.id, "XLE", "Energy", 1)

        _mk_theme(session, run_a.id, "ai", "Artificial Intelligence", 1)
        _mk_theme(session, run_a.id, "ev", "Electric Vehicles", 2)
        _mk_theme(session, run_b.id, "ai", "Artificial Intelligence", 3)
        _mk_theme(session, run_b.id, "ev", "Electric Vehicles", 1)

        _mk_result(session, run_a.id, "AAPL", 60.0, "C")
        _mk_result(session, run_a.id, "MSFT", 90.0, "A")
        _mk_result(session, run_b.id, "AAPL", 85.0, "A")
        _mk_result(session, run_b.id, "MSFT", 91.0, "A")
        _mk_result(session, run_b.id, "NEWC", 70.0, "C")

        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        return run_a.id, run_b.id


def _by_kind(changes: list[dict], kind: str) -> list[dict]:
    return [c for c in changes if c["kind"] == kind]


def test_no_prior_run_state_is_explicit(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 1, 1), 50.0, 40.0, 45.0)
        session.commit()
        session.refresh(run)
        assert find_previous_run(session, run) is None
        result = compute_delta(session, run, None, cfg)
    assert result == {
        "prior_as_of": None, "gap_days": None, "changes": [], "suppressed": [], "suppressed_count": 0,
    }


def test_prior_as_of_and_gap_days_match_immediately_preceding_run(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        assert find_previous_run(session, run_b).id == run_a_id
        result = compute_delta(session, run_b, run_a, cfg)
    assert result["prior_as_of"] == "2024-01-01"
    assert result["gap_days"] == 7


def test_changes_ordered_market_breadth_sector_theme_stock(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    kinds_seen = [c["kind"] for c in result["changes"]]
    expected_order = [KIND_MARKET, KIND_BREADTH, KIND_SECTOR, KIND_THEME, KIND_STOCK]
    # every kind present must appear in this relative order (some kinds may be entirely absent)
    positions = [expected_order.index(k) for k in kinds_seen]
    assert positions == sorted(positions)


def test_market_change_matches_hand_picked_delta(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    market = _by_kind(result["changes"], KIND_MARKET)
    assert len(market) == 1
    assert market[0]["from"] == 50.0 and market[0]["to"] == 58.0
    assert market[0]["magnitude"] == pytest.approx(8.0)
    assert market[0]["drill_href"] == "/?asof=2024-01-08"


def test_breadth_below_threshold_is_suppressed_not_dropped(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    breadth_changes = _by_kind(result["changes"], KIND_BREADTH)
    assert len(breadth_changes) == 1
    assert breadth_changes[0]["label"] == "Breadth above 200-DMA"
    suppressed_breadth = [s for s in result["suppressed"] if s["kind"] == KIND_BREADTH]
    assert len(suppressed_breadth) == 1
    assert suppressed_breadth[0]["magnitude"] == pytest.approx(4.0)
    assert result["suppressed_count"] == len(result["suppressed"])


def test_sector_rank_moves_match_stored_ranks_both_dates(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
        # independently re-read the stored rank rows the same way GET /api/sectors would
        stored_a = {t: r for t, r in session.exec(select(SectorScoreRow.ticker, SectorScoreRow.rank).where(SectorScoreRow.run_id == run_a_id))}
        stored_b = {t: r for t, r in session.exec(select(SectorScoreRow.ticker, SectorScoreRow.rank).where(SectorScoreRow.run_id == run_b_id))}
    sector_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_SECTOR)}
    assert sector_changes["Technology"]["from"] == stored_a["XLK"] == 1
    assert sector_changes["Technology"]["to"] == stored_b["XLK"] == 3
    assert sector_changes["Energy"]["from"] == stored_a["XLE"] == 3
    assert sector_changes["Energy"]["to"] == stored_b["XLE"] == 1
    # XLF (unchanged rank) must not appear as a change
    assert "Financials" not in sector_changes
    suppressed_sector = [s for s in result["suppressed"] if s["kind"] == KIND_SECTOR]
    assert len(suppressed_sector) == 1
    assert suppressed_sector[0]["magnitude"] == 0.0


def test_theme_rank_move_reported(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    theme_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_THEME)}
    assert theme_changes["Artificial Intelligence"]["from"] == 1
    assert theme_changes["Artificial Intelligence"]["to"] == 3
    assert "Electric Vehicles" not in theme_changes  # delta 1 < threshold 2 -> suppressed


def test_stock_bucket_crossing_matches_leaderboard_values(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    stock_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_STOCK)}
    assert stock_changes["AAPL leadership bucket"]["from"] == "C"
    assert stock_changes["AAPL leadership bucket"]["to"] == "A"
    assert stock_changes["AAPL leadership bucket"]["drill_href"] == "/stocks/AAPL?asof=2024-01-08"
    # MSFT's bucket did not cross (A -> A) -- must not appear as a change, even though its score moved
    assert "MSFT leadership bucket" not in stock_changes


def test_new_to_universe_reported_distinctly_never_as_score_change(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    new_entries = [c for c in _by_kind(result["changes"], KIND_STOCK) if c["from"] == "new"]
    assert len(new_entries) == 1
    assert new_entries[0]["label"] == "NEWC new to universe"
    assert new_entries[0]["to"] == "C"  # the bucket, not a "from bucket -> to bucket" score-change framing


def test_quiet_pair_yields_no_changes_but_nonzero_suppressed(engine, cfg):
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 2, 1), 50.0, 40.0, 45.0)
        run_b = _mk_run(session, date(2024, 2, 8), 50.5, 40.5, 45.5)  # every delta well under threshold
        _mk_sector(session, run_a.id, "XLK", "Technology", 1)
        _mk_sector(session, run_b.id, "XLK", "Technology", 1)
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        result = compute_delta(session, run_b, run_a, cfg)
    assert result["changes"] == []
    assert result["suppressed_count"] > 0
    assert result["suppressed_count"] == len(result["suppressed"])


def test_column_projected_reads_only_no_full_record_json_sweep(engine, cfg, two_runs, monkeypatch):
    """AG-8: the delta producer must never deserialize `record_json` — it reads typed columns only."""
    import app.engine.session_delta as sd

    original_exec = Session.exec

    def _guarded_exec(self, statement, *args, **kwargs):
        compiled = str(statement)
        assert "record_json" not in compiled, f"session_delta issued a record_json-touching query: {compiled}"
        return original_exec(self, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "exec", _guarded_exec)
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        sd.compute_delta(session, run_b, run_a, cfg)


def test_no_forward_returns_or_lookahead_import(engine, cfg):
    """AG-5: static guarantee that the producer module's CODE (not its prose comments) never names
    `ForwardReturn` / `forward_returns` / a bars-after accessor — it compares two already-stored runs
    only. Parsed via `ast` so this scans identifiers actually used by the code, not docstring prose."""
    import ast

    import app.engine.session_delta as sd

    tree = ast.parse(open(sd.__file__).read())
    banned = {"ForwardReturn", "forward_returns", "bars_after"}
    offenders = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in banned:
            offenders.add(node.id)
        if isinstance(node, ast.Attribute) and node.attr in banned:
            offenders.add(node.attr)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name in banned:
                    offenders.add(alias.name)
    assert not offenders, f"session_delta.py's code references banned lookahead identifiers: {offenders}"
