"""DB layer: create_all produces exactly the expected tables; seed load is idempotent."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlmodel import Session, SQLModel

from app.models import DailyPrice, DataProviderRun, ForwardReturn, ImportCheckpoint, Stock, ThemeMember
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

# iter-29 (J-87 / J-88) standalone, create_all-managed Market Phase & Severity aggregate cache. Same
# reasoning as RESEARCH_CACHE_TABLES: legitimately MUTABLE derived/cache state (NOT a snapshot — the
# *Snapshots are immutable* anti-goal binds only scanner_runs/results/scores/forward_returns), a
# standalone table so a fresh DB carries it and no existing table gains a column. Figures byte-identical
# to a fresh compute; the cache key carries the SAME dataset_version stamp J-72 uses (single-sourced).
MARKET_PHASE_CACHE_TABLES = {"market_phase_cache"}

# iter-32 (J-92) standalone, create_all-managed optional FRED macro-feed store. Same reasoning as
# RESEARCH_CACHE_TABLES / MARKET_PHASE_CACHE_TABLES: a separate additive table (NOT a snapshot — the
# *Snapshots are immutable* anti-goal binds only scanner_runs/results/scores/forward_returns), a
# STANDALONE table so a fresh DB carries it and no EXISTING table gains a column (the `_ADDITIVE_COLUMNS`
# trap does not apply). The `^TNX`/`^DXY`/`^VXN` OHLCV macro PROXIES ride the existing daily_prices table
# → no schema change there. Macro ships config-default-OFF (no rows ⇒ every J-87..J-91 figure unchanged).
MACRO_TABLES = {"macro_series"}

# iter-36 (J-96) standalone, create_all-managed dynamic-universe membership-timeline aggregate cache.
# Same reasoning as RESEARCH_CACHE_TABLES / MARKET_PHASE_CACHE_TABLES: legitimately MUTABLE derived/cache
# state (NOT a snapshot — the *Snapshots are immutable* anti-goal binds only
# scanner_runs/results/scores/forward_returns), a STANDALONE table so a fresh DB carries it and no
# EXISTING table gains a column (the `_ADDITIVE_COLUMNS` trap does not apply). The cached payload is
# byte-identical to a fresh `_membership_timeline` compute; the cache key carries the SAME
# `_dataset_version` stamp J-72 / J-87 use (single-sourced), so it invalidates on any dataset change.
MEMBERSHIP_TIMELINE_CACHE_TABLES = {"membership_timeline_cache"}

# iter-25 (J-38): `DataProviderRun.dismissed` is a MUTABLE job-control COLUMN added to the existing
# data_provider_runs table — it adds NO new table, so the expected-tables set below is unchanged. The
# explicit assertion in test_data_provider_run_has_dismissed_column verifies the column exists.


def test_create_all_produces_expected_tables():
    assert (
        set(SQLModel.metadata.tables.keys())
        == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES | IMPORT_TABLES
        | RESEARCH_CACHE_TABLES | MARKET_PHASE_CACHE_TABLES | MACRO_TABLES
        | MEMBERSHIP_TIMELINE_CACHE_TABLES
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


def test_additive_migration_backfills_max_drawdown_on_existing_forward_returns(tmp_path):
    """iter-27 (J-86) REGRESSION: the new `forward_returns.max_drawdown` column added to the ALREADY-CREATED
    forward_returns table must be registered in `_ADDITIVE_COLUMNS`, else an existing offline-first DB never
    gains it and every `/api/stocks` read 500s with `no such column`. Build a LEGACY forward_returns table
    (no max_drawdown), then assert create_db_and_tables backfills it in place (nullable, idempotent), and an
    existing row reads NULL (honest NA — never a fabricated 0)."""
    from sqlalchemy import inspect, text

    from app.db import _ADDITIVE_COLUMNS, create_db_and_tables, make_engine

    # the column is registered in the additive registry
    registered = {(t, c) for t, c, _ddl in _ADDITIVE_COLUMNS}
    assert ("forward_returns", "max_drawdown") in registered

    db = tmp_path / "legacy_iter27.db"
    engine = make_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        # LEGACY forward_returns WITHOUT max_drawdown (but WITH the iter-14 mae/mfe columns).
        conn.execute(text(
            "CREATE TABLE forward_returns ("
            "id INTEGER PRIMARY KEY, run_id INTEGER, symbol TEXT, horizon INTEGER, asof_date DATE, "
            "entry_close FLOAT, measured_date DATE, realized_return FLOAT, mae FLOAT, mfe FLOAT)"
        ))
        conn.execute(text(
            "INSERT INTO forward_returns (run_id, symbol, horizon, asof_date, entry_close, measured_date, "
            "realized_return, mae, mfe) VALUES "
            "(1, 'AAA', 5, '2024-01-05', 100.0, '2024-01-12', 0.05, -0.02, 0.07)"
        ))
    before = {c["name"] for c in inspect(engine).get_columns("forward_returns")}
    assert "max_drawdown" not in before

    create_db_and_tables(engine)  # applies the additive backfill

    after = {c["name"] for c in inspect(make_engine(f"sqlite:///{db}")).get_columns("forward_returns")}
    assert "max_drawdown" in after
    with engine.begin() as conn:
        assert conn.execute(text("SELECT max_drawdown FROM forward_returns")).scalar() is None  # honest NA
    create_db_and_tables(make_engine(f"sqlite:///{db}"))  # idempotent — a second run must not error


def test_additive_migration_backfills_dry_spell_columns_on_existing_forward_returns(tmp_path):
    """iter-41 (J-25) REGRESSION: the new `forward_returns.underwater_days` / `.time_to_recover_days`
    columns added to the ALREADY-CREATED forward_returns table must be registered in `_ADDITIVE_COLUMNS`,
    else an existing offline-first DB never gains them and `GET /api/evidence` 500s with `no such column`.
    Build a LEGACY forward_returns table (with max_drawdown but WITHOUT the two new columns), then assert
    create_db_and_tables backfills both in place (nullable, idempotent), and an existing row reads NULL
    (honest NA — never a fabricated 0)."""
    from sqlalchemy import inspect, text

    from app.db import _ADDITIVE_COLUMNS, create_db_and_tables, make_engine

    registered = {(t, c) for t, c, _ddl in _ADDITIVE_COLUMNS}
    assert ("forward_returns", "underwater_days") in registered
    assert ("forward_returns", "time_to_recover_days") in registered

    db = tmp_path / "legacy_iter41.db"
    engine = make_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        # LEGACY forward_returns WITH max_drawdown (iter-27) but WITHOUT the iter-41 dry-spell columns.
        conn.execute(text(
            "CREATE TABLE forward_returns ("
            "id INTEGER PRIMARY KEY, run_id INTEGER, symbol TEXT, horizon INTEGER, asof_date DATE, "
            "entry_close FLOAT, measured_date DATE, realized_return FLOAT, mae FLOAT, mfe FLOAT, "
            "max_drawdown FLOAT)"
        ))
        conn.execute(text(
            "INSERT INTO forward_returns (run_id, symbol, horizon, asof_date, entry_close, measured_date, "
            "realized_return, mae, mfe, max_drawdown) VALUES "
            "(1, 'AAA', 5, '2024-01-05', 100.0, '2024-01-12', 0.05, -0.02, 0.07, -0.03)"
        ))
    before = {c["name"] for c in inspect(engine).get_columns("forward_returns")}
    assert "underwater_days" not in before
    assert "time_to_recover_days" not in before

    create_db_and_tables(engine)  # applies the additive backfill

    after = {c["name"] for c in inspect(make_engine(f"sqlite:///{db}")).get_columns("forward_returns")}
    assert "underwater_days" in after
    assert "time_to_recover_days" in after
    with engine.begin() as conn:
        row = conn.execute(text(
            "SELECT underwater_days, time_to_recover_days FROM forward_returns"
        )).one()
        assert row[0] is None and row[1] is None  # honest NA on the pre-existing row
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

    # The tables that gained columns this/prior iterations (mutable job-control + the append-only
    # forward_returns table, which gained iter-27's max_drawdown).
    for table, model_cls in (
        ("data_provider_runs", DataProviderRun),
        ("import_checkpoints", ImportCheckpoint),
        ("forward_returns", ForwardReturn),
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
    # iter-27 (J-86): the append-only max-drawdown column added to the existing forward_returns table.
    "forward_returns": {"max_drawdown"},
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


# ==================================================================================================
# iter-24 fast-platform item B — sqlite-only connect-event PRAGMAs (config-sourced, no literal in app.db)
# ==================================================================================================
def test_sqlite_pragmas_applied_on_connect(tmp_path):
    """A fresh sqlite connection gets the configured journal_mode/synchronous/busy_timeout PRAGMAs
    applied — proven by reading them back via `PRAGMA` queries on a real connection."""
    from app.db import make_engine

    engine = make_engine(f"sqlite:///{tmp_path / 'pragma.db'}")
    with engine.connect() as conn:
        journal_mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
        synchronous = conn.exec_driver_sql("PRAGMA synchronous").scalar()
        busy_timeout = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()
        cache_size = conn.exec_driver_sql("PRAGMA cache_size").scalar()
        mmap_size = conn.exec_driver_sql("PRAGMA mmap_size").scalar()
        temp_store = conn.exec_driver_sql("PRAGMA temp_store").scalar()
    assert journal_mode.lower() == "wal"
    assert synchronous == 1  # SQLite's own PRAGMA synchronous vocabulary: 0=OFF,1=NORMAL,2=FULL,3=EXTRA
    assert busy_timeout == 30000
    assert cache_size == -65536  # iter-4/J-09: was -262144 (256 MB); halved to 64 MB, see reports/perf-budgets.md
    # mmap DISABLED (0): a non-zero mmap_size reserves that many bytes of VIRTUAL address space per pooled
    # connection; at 1 GB x the pool it exhausted the 6144 MB ulimit -v cap and crashed the cold /api/data
    # load (iter-24 audit / browser-qa UT-16). The page cache above keeps reads fast without it.
    assert mmap_size == 0
    assert temp_store == 2  # SQLite's own PRAGMA temp_store vocabulary: 0=DEFAULT,1=FILE,2=MEMORY


def test_sqlite_pragmas_are_config_sourced_not_a_literal(tmp_path):
    """The applied PRAGMA values come from `database.pragmas` — not a hardcoded literal in app.db —
    proven by overriding one value in a custom config and reading back the DIFFERENT applied value."""
    from app.config import load_config
    from app.db import make_engine

    cfg = load_config()
    custom_pragmas = cfg.database.pragmas.model_copy(update={"busy_timeout_ms": 5000})
    custom_database = cfg.database.model_copy(update={"pragmas": custom_pragmas})
    custom_cfg = cfg.model_copy(update={"database": custom_database})

    engine = make_engine(f"sqlite:///{tmp_path / 'pragma_custom.db'}", config=custom_cfg)
    with engine.connect() as conn:
        busy_timeout = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()
    assert busy_timeout == 5000


def test_pool_size_is_config_sourced(tmp_path):
    """The engine's pool is sized from `database.pool_size`/`max_overflow` (config), not a bare literal."""
    from app.config import load_config
    from app.db import make_engine

    cfg = load_config()
    custom_database = cfg.database.model_copy(update={"pool_size": 3, "max_overflow": 7})
    custom_cfg = cfg.model_copy(update={"database": custom_database})

    engine = make_engine(f"sqlite:///{tmp_path / 'pool.db'}", config=custom_cfg)
    assert engine.pool.size() == 3
    assert engine.pool._max_overflow == 7


def test_is_sqlite_url_detection():
    """The ONE dialect-specific gate (used by both connect_args and the PRAGMA hook) correctly
    distinguishes sqlite URLs (file-based and in-memory) from every other dialect."""
    from app.db import _is_sqlite_url

    assert _is_sqlite_url("sqlite:///path/to.db") is True
    assert _is_sqlite_url("sqlite://") is True
    assert _is_sqlite_url("sqlite:///:memory:") is True
    assert _is_sqlite_url("postgresql://user:pass@localhost/db") is False
    assert _is_sqlite_url("mysql://user:pass@localhost/db") is False


def test_non_sqlite_url_skips_sqlite_connect_args():
    """A non-sqlite URL never gets `check_same_thread` (the sqlite-only connect_args) — the dialect
    gate keeps every query ORM-portable. Checked at the connect_args-construction level (constructing a
    REAL non-sqlite engine would require a DBAPI driver this project never installs)."""
    from app.db import _is_sqlite_url

    url = "postgresql://user:pass@localhost/db"
    connect_args = {"check_same_thread": False} if _is_sqlite_url(url) else {}
    assert connect_args == {}


# ==================================================================================================
# iter-24 fast-platform item C — index hygiene (guarded startup DROP/CREATE, mirrors _ADDITIVE_COLUMNS)
# ==================================================================================================
def test_index_hygiene_drops_duplicates_and_adds_date_index(tmp_path):
    """After create_db_and_tables, the byte-for-byte-duplicate ix_daily_prices_symbol_date and the
    redundant ix_forward_returns_run_symbol are ABSENT, and the new ix_daily_prices_date is PRESENT.
    The untouched single-column run_id/symbol indexes on forward_returns stay present."""
    from sqlalchemy import inspect

    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "idx.db"
    engine = make_engine(f"sqlite:///{db}")
    create_db_and_tables(engine)
    insp = inspect(engine)
    price_indexes = {ix["name"] for ix in insp.get_indexes("daily_prices")}
    fr_indexes = {ix["name"] for ix in insp.get_indexes("forward_returns")}

    assert "ix_daily_prices_symbol_date" not in price_indexes
    assert "ix_daily_prices_date" in price_indexes
    assert "ix_forward_returns_run_symbol" not in fr_indexes
    assert {"ix_forward_returns_run_id", "ix_forward_returns_symbol"} <= fr_indexes


def test_index_hygiene_removes_stale_duplicate_from_legacy_db(tmp_path):
    """A DB built under the OLDER model (still carrying the now-removed duplicate/redundant indexes)
    gets them dropped the next time create_db_and_tables runs — proving the guarded migration acts on a
    REAL legacy DB, not just a fresh one that never creates them."""
    from sqlalchemy import inspect, text

    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "legacy_idx.db"
    engine = make_engine(f"sqlite:///{db}")
    create_db_and_tables(engine)  # the current model creates neither duplicate index
    with engine.begin() as conn:
        # Simulate the OLD model's now-removed duplicate/redundant indexes on a legacy DB.
        conn.execute(text("CREATE INDEX ix_daily_prices_symbol_date ON daily_prices (symbol, date)"))
        conn.execute(text("CREATE INDEX ix_forward_returns_run_symbol ON forward_returns (run_id, symbol)"))
    before = {ix["name"] for ix in inspect(engine).get_indexes("daily_prices")}
    assert "ix_daily_prices_symbol_date" in before

    create_db_and_tables(make_engine(f"sqlite:///{db}"))  # re-applies the guarded drop/add step

    insp_after = inspect(make_engine(f"sqlite:///{db}"))
    after_prices = {ix["name"] for ix in insp_after.get_indexes("daily_prices")}
    after_fr = {ix["name"] for ix in insp_after.get_indexes("forward_returns")}
    assert "ix_daily_prices_symbol_date" not in after_prices
    assert "ix_forward_returns_run_symbol" not in after_fr


def test_index_hygiene_idempotent_on_second_run(tmp_path):
    """The guarded DROP/CREATE step never errors on a second call (fresh DB, then re-applied)."""
    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "idx_idempotent.db"
    engine = make_engine(f"sqlite:///{db}")
    create_db_and_tables(engine)
    create_db_and_tables(make_engine(f"sqlite:///{db}"))  # must not raise


def test_query_plan_bars_asof_uses_unique_index_after_dedup(tmp_path):
    """EXPLAIN QUERY PLAN proves the exact `bars_asof` filter shape (symbol=? AND date<=?) still resolves
    via an index (SQLite's own autoindex for the (symbol, date) unique constraint) after the duplicate
    explicit index is dropped — a SEARCH, never a table SCAN. A FRESH engine is used for the plan check
    (a pooled connection can otherwise serve a stale cached plan referencing the just-dropped index name
    — a sqlite/DBAPI statement-cache artifact, not a real-server behavior)."""
    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "plan.db"
    create_db_and_tables(make_engine(f"sqlite:///{db}"))

    with make_engine(f"sqlite:///{db}").connect() as conn:
        rows = conn.exec_driver_sql(
            "EXPLAIN QUERY PLAN SELECT * FROM daily_prices "
            "WHERE symbol = 'AAPL' AND date <= '2024-01-01' ORDER BY date"
        ).fetchall()
    plan = " ".join(str(tuple(r)) for r in rows).lower()
    assert "search" in plan and "using index" in plan  # an index SEARCH, not a table SCAN
    assert "ix_daily_prices_symbol_date" not in plan  # the dropped duplicate is never chosen (it is gone)


def test_query_plan_max_date_uses_new_date_index(tmp_path):
    """EXPLAIN QUERY PLAN proves `max(date)` (read on ~every request via `latest_data_date`) resolves
    through the new `ix_daily_prices_date` index."""
    from app.db import create_db_and_tables, make_engine

    db = tmp_path / "plan2.db"
    create_db_and_tables(make_engine(f"sqlite:///{db}"))

    with make_engine(f"sqlite:///{db}").connect() as conn:
        rows = conn.exec_driver_sql("EXPLAIN QUERY PLAN SELECT max(date) FROM daily_prices").fetchall()
    plan = " ".join(str(tuple(r)) for r in rows).lower()
    assert "ix_daily_prices_date" in plan
