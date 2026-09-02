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
from app.engine.session_delta import (
    KIND_BREADTH,
    KIND_MARKET,
    KIND_SECTOR,
    KIND_STOCK,
    KIND_THEME,
    compute_delta,
    find_previous_run,
    sector_rank_pairs,
    theme_rank_pairs,
)
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


# --- iter-36 (J-13): signed delta + sector/theme rank-pair builders -----------------------------


def test_sector_theme_change_entries_carry_signed_delta(engine, cfg, two_runs):
    """`session_delta.changes` sector/theme-kind entries now carry a SIGNED `delta` (`cur_rank -
    prev_rank`) alongside the existing unsigned `magnitude` -- other kinds (market/breadth/stock) are
    untouched (no `delta` key at all)."""
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    sector_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_SECTOR)}
    # Technology XLK: rank 1 -> 3 (rose, worse -> positive delta); Energy XLE: rank 3 -> 1 (fell, better -> negative)
    assert sector_changes["Technology"]["delta"] == 2
    assert sector_changes["Energy"]["delta"] == -2
    theme_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_THEME)}
    # Artificial Intelligence: rank 1 -> 3 (delta +2)
    assert theme_changes["Artificial Intelligence"]["delta"] == 2
    for kind in (KIND_MARKET, KIND_BREADTH, KIND_STOCK):
        for entry in _by_kind(result["changes"], kind):
            assert "delta" not in entry


def test_sector_rank_pairs_returns_all_comparable_pairs_uncapped_and_unthresholded(engine, cfg, two_runs):
    """`sector_rank_pairs` returns EVERY comparable pair (XLK, XLF, XLE — including the below-threshold
    XLF), unlike `compute_delta`'s own `changes`/`suppressed` split, and each carries a signed `delta`."""
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        pairs = sector_rank_pairs(session, run_b, run_a, cfg)
    by_label = {entry["label"]: entry for entry, _magnitude in pairs}
    assert set(by_label) == {"Technology", "Financials", "Energy"}
    assert by_label["Technology"]["delta"] == 2
    assert by_label["Energy"]["delta"] == -2
    assert by_label["Financials"]["delta"] == 0  # below rank_move_min=2, but STILL present (not dropped)
    # most-moved-first ordering (by |delta|)
    assert [entry["label"] for entry, _m in pairs] in (
        ["Technology", "Energy", "Financials"], ["Energy", "Technology", "Financials"],
    )


def test_theme_rank_pairs_returns_all_comparable_pairs_uncapped_and_unthresholded(engine, cfg, two_runs):
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        pairs = theme_rank_pairs(session, run_b, run_a, cfg)
    by_label = {entry["label"]: entry for entry, _magnitude in pairs}
    assert set(by_label) == {"Artificial Intelligence", "Electric Vehicles"}
    assert by_label["Artificial Intelligence"]["delta"] == 2
    assert by_label["Electric Vehicles"]["delta"] == -1  # below rank_move_min=2, still present


def test_compute_delta_reuses_precomputed_pairs_no_second_query(engine, cfg, two_runs):
    """Passing precomputed `sector_pairs`/`theme_pairs` into `compute_delta` reuses the SAME entry
    objects for `session_delta.changes` (identity check) -- proof there is no second, independent
    recomputation of the pairs."""
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        precomputed_sector_pairs = sector_rank_pairs(session, run_b, run_a, cfg)
        precomputed_theme_pairs = theme_rank_pairs(session, run_b, run_a, cfg)
        result = compute_delta(
            session, run_b, run_a, cfg, sector_pairs=precomputed_sector_pairs, theme_pairs=precomputed_theme_pairs,
        )
    sector_entry_ids = {id(entry) for entry, _m in precomputed_sector_pairs if entry["magnitude"] >= cfg.compass.delta.rank_move_min}
    theme_entry_ids = {id(entry) for entry, _m in precomputed_theme_pairs if entry["magnitude"] >= cfg.compass.delta.rank_move_min}
    for entry in _by_kind(result["changes"], KIND_SECTOR):
        assert id(entry) in sector_entry_ids
    for entry in _by_kind(result["changes"], KIND_THEME):
        assert id(entry) in theme_entry_ids


# --- iter-40 (J-15): stock-kind accounting (shown / suppressed / residual close against evaluated) ----


def test_stock_accounting_present_and_closes_exactly_on_two_runs_fixture(engine, cfg, two_runs):
    """`two_runs` has exactly one bucket crossing (AAPL, above threshold) and one new-to-universe member
    (NEWC, outside the accounting) -- well under `max_stock_items` (10), so nothing is bounded: the whole
    crossing is shown, nothing suppressed or residual."""
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    accounting = result["stock_accounting"]
    assert accounting == {
        "evaluated_count": 1, "shown_count": 1, "suppressed_count": 0, "residual_count": 0,
    }
    assert accounting["evaluated_count"] == (
        accounting["shown_count"] + accounting["suppressed_count"] + accounting["residual_count"]
    )


def test_no_prior_run_state_has_no_stock_accounting_key(engine, cfg):
    """The explicit no-prior-run early return stays byte-identical to before this iteration -- no
    `stock_accounting` key is fabricated when there is nothing to account for (mirrors `rotation`'s own
    no-prior-run absence, iter-36)."""
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 1, 1), 50.0, 40.0, 45.0)
        session.commit()
        session.refresh(run)
        result = compute_delta(session, run, None, cfg)
    assert "stock_accounting" not in result


def test_zero_stock_crossings_yields_explicit_zero_accounting(engine, cfg):
    """Fixture (c) from the goal text step 8: zero stock-kind crossings evaluated -> an explicit,
    honest all-zero `stock_accounting`, never a blank/missing block."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 3, 1), 50.0, 40.0, 45.0)
        run_b = _mk_run(session, date(2024, 3, 8), 50.0, 40.0, 45.0)  # no ScannerResult rows on either side
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        result = compute_delta(session, run_b, run_a, cfg)
    assert result["stock_accounting"] == {
        "evaluated_count": 0, "shown_count": 0, "suppressed_count": 0, "residual_count": 0,
    }


@pytest.fixture()
def many_crossings_run(engine, cfg):
    """Fixture (a) from the goal text step 8: MORE above-threshold bucket crossings (12) than
    `max_stock_items` (10, the live config value) plus 3 below-threshold crossings -- so the accounting
    must show exactly 10, hold 2 back as residual (never dropped uncounted), and count the 3 as
    suppressed. All 15 tickers get a DISTINCT magnitude so shown-vs-residual is unambiguous
    (most-moved-first, ties never arise)."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 4, 1), 50.0, 40.0, 45.0)
        run_b = _mk_run(session, date(2024, 4, 8), 50.0, 40.0, 45.0)
        # 12 above-threshold crossings (magnitude 8.5 .. 19.5, all >= stock_score_min_change 8.0), bucket C -> A
        for i in range(12):
            ticker = f"X{i:02d}"
            _mk_result(session, run_a.id, ticker, 50.0, "C")
            _mk_result(session, run_b.id, ticker, 50.0 + 8.5 + i, "A")
        # 3 below-threshold crossings (magnitude 1.0 .. 3.0, all < 8.0), bucket C -> B
        for i in range(3):
            ticker = f"Y{i:02d}"
            _mk_result(session, run_a.id, ticker, 50.0, "C")
            _mk_result(session, run_b.id, ticker, 50.0 + 1.0 + i, "B")
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        return run_a.id, run_b.id


def test_more_crossings_than_cap_close_via_shown_suppressed_residual(engine, cfg, many_crossings_run):
    assert cfg.compass.delta.max_stock_items == 10  # the live config value this fixture is built against
    assert cfg.compass.delta.stock_score_min_change == 8.0
    run_a_id, run_b_id = many_crossings_run
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        result = compute_delta(session, run_b, run_a, cfg)
    accounting = result["stock_accounting"]
    assert accounting == {
        "evaluated_count": 15, "shown_count": 10, "suppressed_count": 3, "residual_count": 2,
    }
    stock_changes = _by_kind(result["changes"], KIND_STOCK)
    assert len(stock_changes) == 10  # display cap held, exactly as before this iteration
    shown_labels = {c["label"] for c in stock_changes}
    # the two LOWEST-magnitude above-threshold movers (X00 magnitude 8.5, X01 magnitude 9.5) are bumped
    # into the residual bucket -- never shown, never silently dropped, never counted as suppressed
    assert "X00 leadership bucket" not in shown_labels
    assert "X01 leadership bucket" not in shown_labels
    # the highest-magnitude mover (X11, magnitude 19.5) is always shown
    assert "X11 leadership bucket" in shown_labels
    # the 3 below-threshold crossings are counted as suppressed, never shown, never residual
    suppressed_stock = [s for s in result["suppressed"] if s["kind"] == KIND_STOCK]
    assert len(suppressed_stock) == 3
    assert all(s["magnitude"] < cfg.compass.delta.stock_score_min_change for s in suppressed_stock)


def test_new_to_universe_reduces_available_display_slots_for_crossings(engine, cfg):
    """Fixture (b) from the goal text step 8: new-to-universe members keep their existing unconditional
    display priority -- they consume display slots ahead of crossings, so they reduce how many above-
    threshold crossings can be SHOWN, but they never appear in `stock_accounting` (only crossings are
    "evaluated" against the threshold) and never turn a crossing into a fabricated suppression."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 5, 1), 50.0, 40.0, 45.0)
        run_b = _mk_run(session, date(2024, 5, 8), 50.0, 40.0, 45.0)
        # 2 new-to-universe members (present only in run_b) -- unconditional priority, outside accounting
        for i in range(2):
            _mk_result(session, run_b.id, f"NEW{i}", 70.0, "C")
        # 12 above-threshold crossings (magnitude 8.5 .. 19.5)
        for i in range(12):
            ticker = f"X{i:02d}"
            _mk_result(session, run_a.id, ticker, 50.0, "C")
            _mk_result(session, run_b.id, ticker, 50.0 + 8.5 + i, "A")
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        result = compute_delta(session, run_b, run_a, cfg)
    accounting = result["stock_accounting"]
    # 2 display slots go to the new-to-universe members first (unconditional), leaving 8 of the 10
    # max_stock_items slots for crossings -- so 8 shown, 4 residual, 0 suppressed (all 12 clear threshold)
    assert accounting == {
        "evaluated_count": 12, "shown_count": 8, "suppressed_count": 0, "residual_count": 4,
    }
    stock_changes = _by_kind(result["changes"], KIND_STOCK)
    assert len(stock_changes) == 10  # 2 new-to-universe + 8 shown crossings, display cap unchanged
    new_entries = [c for c in stock_changes if c["from"] == "new"]
    assert len(new_entries) == 2


def test_compute_delta_without_precomputed_pairs_matches_precomputed_call(engine, cfg, two_runs):
    """Omitting `sector_pairs`/`theme_pairs` (every pre-iter-36 caller) yields the SAME `changes`/
    `suppressed` values as passing them explicitly -- backward-compatible default."""
    run_a_id, run_b_id = two_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        implicit = compute_delta(session, run_b, run_a, cfg)
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        sector_pairs = sector_rank_pairs(session, run_b, run_a, cfg)
        theme_pairs = theme_rank_pairs(session, run_b, run_a, cfg)
        explicit = compute_delta(session, run_b, run_a, cfg, sector_pairs=sector_pairs, theme_pairs=theme_pairs)
    assert implicit == explicit
