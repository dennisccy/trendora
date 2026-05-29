"""DB layer: create_all produces exactly the iter-1 tables; seed load is idempotent."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlmodel import Session, SQLModel

from app.models import DailyPrice, DataProviderRun, Stock, ThemeMember
from app.seed_loader import load_seed

ITER1_TABLES = {
    "sectors",
    "industries",
    "stocks",
    "etfs",
    "themes",
    "theme_members",
    "daily_prices",
    "data_provider_runs",
}


def test_create_all_produces_exactly_iter1_tables():
    assert set(SQLModel.metadata.tables.keys()) == ITER1_TABLES


def test_daily_prices_has_unique_symbol_date_constraint():
    constraints = {c.name for c in DailyPrice.__table__.constraints}
    assert "uq_daily_prices_symbol_date" in constraints


def _counts(engine):
    with Session(engine) as session:
        return {
            "prices": session.scalar(select(func.count()).select_from(DailyPrice)),
            "stocks": session.scalar(select(func.count()).select_from(Stock)),
            "members": session.scalar(select(func.count()).select_from(ThemeMember)),
            "runs": session.scalar(select(func.count()).select_from(DataProviderRun)),
        }


def test_seed_load_is_idempotent(loaded_engine, config):
    """loaded_engine already loaded the seed once. A second load must be a no-op and must
    not change any row counts (the (symbol, date) uniqueness + the empty-DB guard protect it)."""
    before = _counts(loaded_engine)
    result = load_seed(loaded_engine, config)
    assert result["loaded"] is False
    after = _counts(loaded_engine)
    assert before == after
    assert before["prices"] > 0
    assert before["stocks"] == len(config.universe.symbols)
    assert before["members"] > 0
    assert before["runs"] == 1  # exactly one provider run from the single real load


def test_seed_load_populates_reference_and_prices(loaded_engine):
    counts = _counts(loaded_engine)
    assert counts["prices"] > 100_000  # ~158 symbols x ~1.3k bars
    assert counts["stocks"] >= 100
