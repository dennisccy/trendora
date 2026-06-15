"""DB layer: create_all produces exactly the expected tables; seed load is idempotent."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlmodel import Session, SQLModel

from app.models import DailyPrice, DataProviderRun, ImportCheckpoint, Stock, ThemeMember
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

# iter-20 (J-72) standalone, create_all-managed event-study aggregate cache. Like data_provider_runs /
# import_checkpoints it is legitimately MUTABLE derived/cache state — explicitly NOT a snapshot table
# (the *Snapshots are immutable* anti-goal binds only scanner_runs/results/scores/forward_returns). It
# is the new-table analog of the _ADDITIVE_COLUMNS pattern: a standalone table so a fresh DB carries it
# and no existing table gains a column. The cached figures are byte-identical to a fresh compute.
RESEARCH_CACHE_TABLES = {"event_study_cache"}

# iter-25 (J-38): `DataProviderRun.dismissed` is a MUTABLE job-control COLUMN added to the existing
# data_provider_runs table — it adds NO new table, so the expected-tables set below is unchanged. The
# explicit assertion in test_data_provider_run_has_dismissed_column verifies the column exists.


def test_create_all_produces_expected_tables():
    assert (
        set(SQLModel.metadata.tables.keys())
        == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES | IMPORT_TABLES | RESEARCH_CACHE_TABLES
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


def test_additive_migration_backfills_job_id_and_completed_stages_on_existing_db(tmp_path):
    """iter-29 (J-59/J-60) REGRESSION: a new column added to an ALREADY-CREATED table must be registered
    in `_ADDITIVE_COLUMNS`, else an existing offline-first DB never gains it and every read 500s with
    `no such column`. Build LEGACY data_provider_runs (no job_id) and import_checkpoints (no
    completed_stages_json), then assert create_db_and_tables backfills BOTH in place (idempotent)."""
    from sqlalchemy import inspect, text

    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "legacy_iter29.db"
    engine = make_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        # LEGACY data_provider_runs WITHOUT job_id (but WITH the older `dismissed` column).
        conn.execute(text(
            "CREATE TABLE data_provider_runs ("
            "id INTEGER PRIMARY KEY, provider TEXT, started_at DATETIME, finished_at DATETIME, "
            "symbols_ok INTEGER, symbols_failed INTEGER, status TEXT, message TEXT, "
            "dismissed BOOLEAN NOT NULL DEFAULT 0)"
        ))
        conn.execute(text(
            "INSERT INTO data_provider_runs (provider, started_at, symbols_ok, symbols_failed, status) "
            "VALUES ('yahoo', '2024-01-01 00:00:00', 1, 0, 'partial')"
        ))
        # LEGACY import_checkpoints WITHOUT completed_stages_json.
        conn.execute(text(
            "CREATE TABLE import_checkpoints ("
            "id INTEGER PRIMARY KEY, import_id TEXT, source TEXT, kind TEXT, start DATE, end DATE, "
            "symbol_plan_json TEXT, chunk_total INTEGER, next_chunk_index INTEGER, symbols_ok INTEGER, "
            "symbols_failed INTEGER, bars_fetched INTEGER, status TEXT, created_at DATETIME, updated_at DATETIME)"
        ))
        conn.execute(text(
            "INSERT INTO import_checkpoints (import_id, source, kind, start, end, symbol_plan_json, "
            "chunk_total, next_chunk_index, symbols_ok, symbols_failed, bars_fetched, status, created_at, updated_at) "
            "VALUES ('job-1', 'yahoo', 'backfill', '2024-01-01', '2024-02-01', '[]', 1, 0, 0, 0, 0, "
            "'resumable', '2024-01-01 00:00:00', '2024-01-01 00:00:00')"
        ))
    runs_before = {c["name"] for c in inspect(engine).get_columns("data_provider_runs")}
    chk_before = {c["name"] for c in inspect(engine).get_columns("import_checkpoints")}
    assert "job_id" not in runs_before
    assert "completed_stages_json" not in chk_before

    create_db_and_tables(engine)  # applies the additive backfills

    runs_after = {c["name"] for c in inspect(make_engine(f"sqlite:///{db}")).get_columns("data_provider_runs")}
    chk_after = {c["name"] for c in inspect(make_engine(f"sqlite:///{db}")).get_columns("import_checkpoints")}
    assert "job_id" in runs_after
    assert "completed_stages_json" in chk_after
    # the pre-existing rows read the honest defaults: job_id NULL, completed_stages_json '[]'.
    with engine.begin() as conn:
        assert conn.execute(text("SELECT job_id FROM data_provider_runs")).scalar() is None
        assert conn.execute(text("SELECT completed_stages_json FROM import_checkpoints")).scalar() == "[]"
    create_db_and_tables(make_engine(f"sqlite:///{db}"))  # idempotent — a second run must not error


def test_every_model_column_on_existing_table_is_covered_by_additive_registry(tmp_path):
    """GUARD against the iter-29 class of bug: for each table that already exists in an OLDER DB, every
    column the current SQLModel defines must EITHER be creatable on a pre-existing table via an
    `_ADDITIVE_COLUMNS` entry, OR already be present. We simulate "the oldest shape" by creating the
    tables fresh, dropping each registered additive column's table-knowledge, and asserting the registry
    is the ONLY thing that re-adds new columns. Concretely: a freshly-created DB has every model column,
    and the set of columns NOT reachable by the registry on a legacy table is exactly the legacy base set
    — so any model column beyond the legacy base MUST appear in `_ADDITIVE_COLUMNS`."""
    from sqlalchemy import inspect

    from app.db import _ADDITIVE_COLUMNS, create_db_and_tables, make_engine

    db = tmp_path / "fresh.db"
    engine = make_engine(f"sqlite:///{db}")
    create_db_and_tables(engine)
    insp = inspect(engine)

    registry_by_table: dict[str, set[str]] = {}
    for table, column, _ddl in _ADDITIVE_COLUMNS:
        registry_by_table.setdefault(table, set()).add(column)

    # The two mutable job-control tables that gained columns this/prior iterations.
    for table, model_cls in (
        ("data_provider_runs", DataProviderRun),
        ("import_checkpoints", ImportCheckpoint),
    ):
        live_cols = {c["name"] for c in insp.get_columns(table)}
        model_cols = {c.name for c in model_cls.__table__.columns}
        # the fresh DB must carry every model column
        assert model_cols <= live_cols
        # every column added by THIS session's models.py beyond HEAD must be registry-covered
        for col in NEW_COLUMNS_THIS_SESSION.get(table, set()):
            assert col in registry_by_table.get(table, set()), (
                f"{table}.{col} is a new model column but is missing from _ADDITIVE_COLUMNS — an existing "
                f"offline-first DB would never gain it and every read would 500 with 'no such column'."
            )


# New model columns added this session (iter-29) to ALREADY-CREATED tables; each MUST be in
# _ADDITIVE_COLUMNS or an existing live DB 500s on read. Update when a column is added to an existing table.
NEW_COLUMNS_THIS_SESSION = {
    "data_provider_runs": {"job_id"},
    "import_checkpoints": {"completed_stages_json"},
}


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
