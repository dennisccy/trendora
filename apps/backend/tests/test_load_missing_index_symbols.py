"""J-14 -- the targeted, idempotent loader for `config.index_chart.symbols` entries missing from
`daily_prices` (`apps/backend/scripts/load_missing_index_symbols.py`).

`seed_loader.load_seed` only (re)loads prices when `daily_prices` is completely EMPTY, so an
ALREADY-BUILT local DB never picks up a symbol added to `index_chart.symbols` after the DB was created
(the `kind=rebuild` data-manager job would pick it up, but it wipes + reprocesses the whole DB -- a
multi-hour operation that destroys every existing snapshot run; forbidden for this remediation). This
script closes that gap with a small, additive, idempotent insert: only symbols with ZERO existing rows
are loaded, reading each from the SAME committed `SeedProvider` `load_prices` uses; every other
symbol/snapshot/forward-return row is untouched.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlmodel import Session

from app.config import IndexChartSymbol
from app.db import create_db_and_tables, make_engine
from app.models import DailyPrice
from scripts.load_missing_index_symbols import load_missing_index_symbols


def _fresh_engine():
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    return engine


def _row_count(session: Session, symbol: str) -> int:
    return int(
        session.scalar(select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol == symbol))
        or 0
    )


def test_loads_only_zero_row_symbols_and_skips_already_loaded(config, seed_dir):
    """On a fresh DB, a configured symbol with ZERO existing rows is loaded from the committed seed CSV
    (the real `^SPX` deep benchmark, J-14); a symbol that already has >= 1 row is left completely
    untouched (idempotent no-op) -- proven by manually seeding one SPY row and confirming it is neither
    duplicated nor reported as loaded."""
    engine = _fresh_engine()
    with Session(engine) as session:
        session.add(
            DailyPrice(symbol="SPY", date=date(2020, 1, 1), open=1, high=1, low=1, close=1, volume=1)
        )
        session.commit()

        loaded = load_missing_index_symbols(session, seed_dir, config=config)

        assert "SPY" not in loaded  # already had a row -- skipped, not reloaded
        assert _row_count(session, "SPY") == 1  # untouched

        assert "^SPX" in loaded and loaded["^SPX"] > 0  # zero rows before -> loaded from the committed CSV
        assert _row_count(session, "^SPX") == loaded["^SPX"]


def test_second_run_is_a_safe_no_op(config, seed_dir):
    """Re-running after every configured symbol has been loaded is a safe no-op -- no duplicate rows,
    nothing reported as newly loaded."""
    engine = _fresh_engine()
    with Session(engine) as session:
        first = load_missing_index_symbols(session, seed_dir, config=config)
        assert "^SPX" in first

        second = load_missing_index_symbols(session, seed_dir, config=config)

        assert second == {}  # every configured symbol now has >= 1 row -- nothing left to load
        assert _row_count(session, "^SPX") == first["^SPX"]  # unchanged by the second run


def test_symbol_with_no_committed_csv_is_skipped_honestly(config, seed_dir):
    """A configured `index_chart` symbol with NO committed seed CSV is skipped -- never fabricated,
    matching `load_prices`'s existing contract (a missing fixture is not a failure)."""
    synthetic = config.model_copy(update={
        "index_chart": config.index_chart.model_copy(update={
            "symbols": [IndexChartSymbol(symbol="^NOPE_NOT_A_REAL_SYMBOL", name="Not a real series")],
        }),
    })
    engine = _fresh_engine()
    with Session(engine) as session:
        loaded = load_missing_index_symbols(session, seed_dir, config=synthetic)

    assert loaded == {}
    assert _row_count(session, "^NOPE_NOT_A_REAL_SYMBOL") == 0


def test_dry_run_reports_without_writing(config, seed_dir):
    """`dry_run=True` reports what WOULD load without touching the database."""
    engine = _fresh_engine()
    with Session(engine) as session:
        report = load_missing_index_symbols(session, seed_dir, config=config, dry_run=True)

        assert "^SPX" in report and report["^SPX"] > 0
        total = session.scalar(select(func.count()).select_from(DailyPrice))
        assert total == 0  # nothing written in dry-run mode
