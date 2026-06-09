"""DB layer: create_all produces exactly the expected tables; seed load is idempotent."""
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

# iter-5 append-only scanner-snapshot tables + iter-6 append-only forward_returns (created by
# create_all on startup).
SNAPSHOT_TABLES = {
    "scanner_runs",
    "scanner_results",
    "sector_scores",
    "theme_scores",
    "forward_returns",
}

# iter-7 user-mutable watchlist (the product's first user-write table; created by create_all). It is
# explicitly NOT a snapshot table — additive to the data model, separate from the append-only set.
WATCHLIST_TABLES = {"watchlist"}

# iter-22 (J-34) durable, MUTABLE chunked-import job-control state (created by create_all). Like
# data_provider_runs it is legitimately mutable job-control — explicitly NOT a snapshot table.
IMPORT_TABLES = {"import_checkpoints"}

# iter-25 (J-38): `DataProviderRun.dismissed` is a MUTABLE job-control COLUMN added to the existing
# data_provider_runs table — it adds NO new table, so the expected-tables set below is unchanged. The
# explicit assertion in test_data_provider_run_has_dismissed_column verifies the column exists.


def test_create_all_produces_expected_tables():
    assert (
        set(SQLModel.metadata.tables.keys())
        == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES | IMPORT_TABLES
    )


def test_daily_prices_has_unique_symbol_date_constraint():
    constraints = {c.name for c in DailyPrice.__table__.constraints}
    assert "uq_daily_prices_symbol_date" in constraints


def test_data_provider_run_has_dismissed_column():
    """iter-25 (J-38): the soft-dismiss flag is a MUTABLE column on the existing data_provider_runs
    table (not a new table); it defaults False so existing/audit rows are never auto-dismissed."""
    cols = {c.name for c in DataProviderRun.__table__.columns}
    assert "dismissed" in cols
    assert DataProviderRun.model_fields["dismissed"].default is False


def test_additive_migration_backfills_dismissed_on_existing_db(tmp_path):
    """iter-25 (J-38): an EXISTING data_provider_runs table that PREDATES the `dismissed` column gains it
    in place on startup (no Alembic; create_all never ALTERs) — so an existing offline-first DB is not
    regenerated. The backfill is idempotent and defaults existing rows to 0/False (never auto-dismissed)."""
    from sqlalchemy import inspect, text

    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "legacy.db"
    engine = make_engine(f"sqlite:///{db}")
    # Build a LEGACY data_provider_runs table WITHOUT the dismissed column (the pre-iter-25 shape).
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE data_provider_runs ("
            "id INTEGER PRIMARY KEY, provider TEXT, started_at DATETIME, finished_at DATETIME, "
            "symbols_ok INTEGER, symbols_failed INTEGER, status TEXT, message TEXT)"
        ))
        conn.execute(text(
            "INSERT INTO data_provider_runs (provider, started_at, symbols_ok, symbols_failed, status) "
            "VALUES ('yahoo', '2024-01-01 00:00:00', 1, 0, 'partial')"
        ))
    before = {c["name"] for c in inspect(engine).get_columns("data_provider_runs")}
    assert "dismissed" not in before

    create_db_and_tables(engine)  # applies the additive backfill
    after = {c["name"] for c in inspect(make_engine(f"sqlite:///{db}")).get_columns("data_provider_runs")}
    assert "dismissed" in after
    # the pre-existing row defaults to not-dismissed (0/False) — never auto-dismissed
    with engine.begin() as conn:
        val = conn.execute(text("SELECT dismissed FROM data_provider_runs")).scalar()
    assert val in (0, False)
    create_db_and_tables(make_engine(f"sqlite:///{db}"))  # idempotent — a second run must not error


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
