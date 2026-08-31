"""Database engine + session helpers.

Engine URL comes from config (`database.url`) so SQLite -> Postgres is a config-only
switch. A relative `sqlite:///` path is resolved against the repository root so the engine
is correct regardless of the process working directory. `create_db_and_tables()` runs
`SQLModel.metadata.create_all()` on startup (no Alembic — see project-template).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  -- ensure all tables are registered on SQLModel.metadata
from app.config import REPO_ROOT, Config, DatabasePragmasCfg, get_config

_engine: Optional[Engine] = None

_SQLITE_PREFIX = "sqlite:///"


def resolve_database_url(url: str, repo_root: Path = REPO_ROOT) -> str:
    """Resolve a relative sqlite path against the repo root (and ensure its dir exists).
    Non-sqlite URLs (e.g. postgresql://...) pass through unchanged."""
    if url.startswith(_SQLITE_PREFIX):
        raw = url[len(_SQLITE_PREFIX):]
        if raw and raw != ":memory:":
            path = Path(raw)
            if not path.is_absolute():
                path = (repo_root / raw).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"{_SQLITE_PREFIX}{path}"
    return url


def _is_sqlite_url(url: str) -> bool:
    """Whether `url` gets sqlite-specific engine treatment (connect_args + the PRAGMA hook) — the ONE
    dialect-specific gate in this module. Matches a bare `sqlite` prefix (covers both a file path and
    the in-memory `sqlite://`/`sqlite:///:memory:` forms)."""
    return url.startswith("sqlite")


def _apply_sqlite_pragmas(engine: Engine, pragmas: DatabasePragmasCfg) -> None:
    """iter-24 fast-platform item B — register a `connect` event so EVERY new DBAPI connection this
    engine opens (i.e. every pooled connection) gets the configured PRAGMAs applied once, before any
    query runs on it. Config-sourced (`database.pragmas`) — no PRAGMA value is a literal here. WAL +
    synchronous=NORMAL is SQLite's own documented safe pairing for a single-host app: the trade-off
    (accepted, documented in `DatabasePragmasCfg`) is that the last commit can be lost on a power loss /
    OS crash — never on an ordinary process crash — which is acceptable for this local research app."""

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"PRAGMA journal_mode={pragmas.journal_mode}")
            cursor.execute(f"PRAGMA synchronous={pragmas.synchronous}")
            cursor.execute(f"PRAGMA busy_timeout={pragmas.busy_timeout_ms}")
            cursor.execute(f"PRAGMA cache_size={pragmas.cache_size}")
            cursor.execute(f"PRAGMA mmap_size={pragmas.mmap_size_bytes}")
            cursor.execute(f"PRAGMA temp_store={pragmas.temp_store}")
        finally:
            cursor.close()


def make_engine(url: str, config: Optional[Config] = None) -> Engine:
    is_sqlite = _is_sqlite_url(url)
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine_kwargs: dict = {}
    # Pool-size kwargs only apply to a pool class that accepts them (QueuePool — SQLAlchemy's default for
    # a FILE-based sqlite URL and for every other dialect); the in-memory sqlite forms
    # (`sqlite://`/`sqlite:///:memory:`, used only by ad-hoc scripts/tests, never this app's real DB) get
    # `SingletonThreadPool` by default, which rejects them — so they are skipped for those URLs only.
    if url not in ("sqlite://", "sqlite:///:memory:"):
        cfg = config or get_config()
        engine_kwargs["pool_size"] = cfg.database.pool_size
        engine_kwargs["max_overflow"] = cfg.database.max_overflow
    engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
    if is_sqlite:
        cfg = config or get_config()
        _apply_sqlite_pragmas(engine, cfg.database.pragmas)
    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = make_engine(resolve_database_url(get_config().database.url))
    return _engine


def set_engine(engine: Engine) -> None:
    """Override the process engine (used by tests to point at a temp database)."""
    global _engine
    _engine = engine


# Additive, idempotent column backfills for an EXISTING database (no Alembic in this project — see
# project-template). `SQLModel.metadata.create_all` creates MISSING TABLES but never ALTERs an existing
# one, so a column added to an already-created table (e.g. iter-25 `data_provider_runs.dismissed`) must be
# backfilled here. Each entry is `(table, column, "ADD COLUMN" DDL)` — only applied when the table exists
# and the column is absent (a fresh DB already has the column from the model and is skipped). The DDL adds
# a NULLABLE/DEFAULTED column only — it never drops/rewrites data, so existing rows are untouched (a
# soft-dismiss flag defaults to 0/False, so no historical run is auto-dismissed). This keeps the
# offline-first "no DB regen" guarantee: an existing live DB gains the column in place.
_ADDITIVE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("data_provider_runs", "dismissed", "ALTER TABLE data_provider_runs ADD COLUMN dismissed BOOLEAN NOT NULL DEFAULT 0"),
    # iter-29 (J-60): job-control correlation id linking a run-history row to its in-memory JobProgress.
    # Nullable (NULL for seed-load + legacy rows) — matches `job_id: Optional[str] = Field(default=None, index=True)`.
    ("data_provider_runs", "job_id", "ALTER TABLE data_provider_runs ADD COLUMN job_id VARCHAR"),
    # iter-29 (J-59): JSON list of COMPLETED pipeline stages for the zero-provider-call resume-at-backfill
    # path. NOT NULL DEFAULT '[]' — matches `completed_stages_json: str = "[]"` (a legacy/fresh row reads an
    # empty stage set, never NULL).
    ("import_checkpoints", "completed_stages_json", "ALTER TABLE import_checkpoints ADD COLUMN completed_stages_json VARCHAR NOT NULL DEFAULT '[]'"),
    # iter-27 (J-86): the append-only max-drawdown column on the forward_returns table — the worst
    # peak-to-trough decline over the first `horizon` post-snapshot bars (<= 0). NULLABLE FLOAT (matches
    # `max_drawdown: Optional[float] = Field(default=None)` — a fresh DB carries it from the model; an
    # existing live DB gains it in place so a non-fresh read of /api/stocks does not 500). It NEVER drops
    # or rewrites data; existing forward_returns rows read NULL until the next confirm-gated rebuild
    # repopulates them (the J-85 rebuild is the create-once path that recomputes forward returns).
    ("forward_returns", "max_drawdown", "ALTER TABLE forward_returns ADD COLUMN max_drawdown FLOAT"),
    # iter-41 (J-25): the two append-only "dry spell" columns on forward_returns — days below the running
    # high-water mark, and days from the max-drawdown trough back to the entry level (<= 0 case handled by
    # NULL, never a fabricated sentinel). NULLABLE INTEGER (matches `Optional[int] = Field(default=None)` —
    # a fresh DB carries them from the model; an existing live DB gains them in place so a non-fresh read of
    # /api/evidence does not 500). Existing forward_returns rows read NULL until the next confirm-gated
    # rebuild repopulates them (mirrors the max_drawdown / J-86 precedent directly above).
    ("forward_returns", "underwater_days", "ALTER TABLE forward_returns ADD COLUMN underwater_days INTEGER"),
    ("forward_returns", "time_to_recover_days", "ALTER TABLE forward_returns ADD COLUMN time_to_recover_days INTEGER"),
    # goal-market-compass iter-3 (J-05/J-06): the engine-identity stamp on newly created scanner_runs rows
    # only. NULLABLE VARCHAR (matches `engine_identity: Optional[str] = Field(default=None)`) — an
    # existing live DB gains the column in place; every pre-iter-3 row reads NULL forever ("pre-stamping
    # era" — never backfilled).
    ("scanner_runs", "engine_identity", "ALTER TABLE scanner_runs ADD COLUMN engine_identity VARCHAR"),
    # goal-market-compass iter-3 (J-05/J-06): the freeze/integrity block on next_session_manifests, all
    # ADDITIVE and NULLABLE/DEFAULTED so an existing live DB's pre-iter-3 rows backfill the documented
    # "pre-freeze era" honesty marker (version=1, frozen=False, prospective_eligible=False, every hash /
    # JSON block NULL) — never retroactively marked frozen or eligible. `version` NOT NULL DEFAULT 1
    # satisfies "existing pre-iter-3 rows backfill version=1" directly at the DDL level; `frozen` and
    # `prospective_eligible` NOT NULL DEFAULT 0 satisfy the fail-closed "absent field reads false" rule
    # even before any Python-level default is consulted.
    ("next_session_manifests", "version", "ALTER TABLE next_session_manifests ADD COLUMN version INTEGER NOT NULL DEFAULT 1"),
    ("next_session_manifests", "mode", "ALTER TABLE next_session_manifests ADD COLUMN mode VARCHAR"),
    ("next_session_manifests", "frozen", "ALTER TABLE next_session_manifests ADD COLUMN frozen BOOLEAN NOT NULL DEFAULT 0"),
    ("next_session_manifests", "generation_json", "ALTER TABLE next_session_manifests ADD COLUMN generation_json VARCHAR"),
    ("next_session_manifests", "engine_identity", "ALTER TABLE next_session_manifests ADD COLUMN engine_identity VARCHAR"),
    ("next_session_manifests", "candidate_rule_hash", "ALTER TABLE next_session_manifests ADD COLUMN candidate_rule_hash VARCHAR"),
    ("next_session_manifests", "candidate_rule_config_json", "ALTER TABLE next_session_manifests ADD COLUMN candidate_rule_config_json VARCHAR"),
    ("next_session_manifests", "cohort_rule_hash", "ALTER TABLE next_session_manifests ADD COLUMN cohort_rule_hash VARCHAR"),
    ("next_session_manifests", "cohort_rule_config_json", "ALTER TABLE next_session_manifests ADD COLUMN cohort_rule_config_json VARCHAR"),
    ("next_session_manifests", "manifest_config_hash", "ALTER TABLE next_session_manifests ADD COLUMN manifest_config_hash VARCHAR"),
    ("next_session_manifests", "manifest_config_subset_json", "ALTER TABLE next_session_manifests ADD COLUMN manifest_config_subset_json VARCHAR"),
    ("next_session_manifests", "dataset_json", "ALTER TABLE next_session_manifests ADD COLUMN dataset_json VARCHAR"),
    ("next_session_manifests", "universe_json", "ALTER TABLE next_session_manifests ADD COLUMN universe_json VARCHAR"),
    ("next_session_manifests", "comparison_cohort_json", "ALTER TABLE next_session_manifests ADD COLUMN comparison_cohort_json VARCHAR"),
    ("next_session_manifests", "near_threshold_shadow_json", "ALTER TABLE next_session_manifests ADD COLUMN near_threshold_shadow_json VARCHAR"),
    ("next_session_manifests", "caveats_json", "ALTER TABLE next_session_manifests ADD COLUMN caveats_json VARCHAR"),
    ("next_session_manifests", "prospective_eligible", "ALTER TABLE next_session_manifests ADD COLUMN prospective_eligible BOOLEAN NOT NULL DEFAULT 0"),
    ("next_session_manifests", "available_at_utc", "ALTER TABLE next_session_manifests ADD COLUMN available_at_utc DATETIME"),
    ("next_session_manifests", "manifest_hash", "ALTER TABLE next_session_manifests ADD COLUMN manifest_hash VARCHAR"),
    ("next_session_manifests", "export_path", "ALTER TABLE next_session_manifests ADD COLUMN export_path VARCHAR"),
    # goal-market-compass iter-28 (J-07): the state_band CONTENT block (regime/stress/breadth direction
    # words + deltas). NULLABLE VARCHAR (matches `state_band_json: Optional[str] = Field(default=None)`)
    # — every row minted before this iteration reads NULL forever ("pre-state_band era", AG-12: never
    # backfilled). A fresh DB gets the column from the model directly (create_all); an existing live DB
    # gains it in place.
    ("next_session_manifests", "state_band_json", "ALTER TABLE next_session_manifests ADD COLUMN state_band_json VARCHAR"),
)


def _ensure_additive_columns(engine: Engine) -> None:
    """Apply each additive column backfill that is missing from an existing table (idempotent)."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl in _ADDITIVE_COLUMNS:
            if table not in existing_tables:
                continue  # create_all just made it WITH the column (fresh DB) — nothing to backfill
            cols = {c["name"] for c in inspector.get_columns(table)}
            if column not in cols:
                conn.execute(text(ddl))


# iter-24 fast-platform item C — index hygiene. `SQLModel.metadata.create_all` creates MISSING tables but
# never drops/alters an index on an ALREADY-EXISTING one, so a duplicate/redundant index that an OLDER
# model version created (or one this session's `models.py` just stopped declaring) survives on a live DB
# forever unless swept here — the same "guarded, idempotent post-boot step" shape as `_ADDITIVE_COLUMNS`,
# applied to indexes instead of columns. `DROP INDEX IF EXISTS` on an index this DB never had (a fresh DB
# built from the CURRENT model, which no longer declares them) is a no-op; `CREATE INDEX IF NOT EXISTS` on
# one create_all already added would also be a no-op (not the case today, but kept idempotent regardless).
#
#   - `ix_daily_prices_symbol_date` — a byte-for-byte DUPLICATE of the unique index SQLite already builds
#     for `UniqueConstraint("symbol", "date")` (models.py `DailyPrice.__table_args__`): dropping it removes
#     a second index write on every bar insert with NO query-plan loss (`bars_asof`'s `symbol=? AND
#     date<=?` still hits the unique index — see `EXPLAIN QUERY PLAN` in test_db.py).
#   - `ix_forward_returns_run_symbol` — a redundant PREFIX of the `UNIQUE(run_id, symbol, horizon)`
#     autoindex (any query the prefix serves, the unique index already serves at least as well).
#   - `ix_daily_prices_date` (ADDED) — `func.max(DailyPrice.date)` (read on ~every request) and the
#     availability/coverage `group_by(date)` scans walk the whole table without a `date`-only index; this
#     one lets SQLite's MIN/MAX optimization + the group-by resolve straight from the index.
#   - `ix_next_session_manifests_as_of` (DROPPED, goal-market-compass iter-3) — the OLD single-column
#     UNIQUE index (one manifest per `as_of`, no versioning). iter-3 allows a confirm-gated regenerate to
#     mint version N+1 for the SAME `as_of`, so the uniqueness constraint must widen to the composite
#     `(as_of, version)` — `uq_next_session_manifests_as_of_version` (ADDED) below. This is the idempotent
#     guarded swap pattern (never a destructive table rewrite): an existing live DB's stored manifest rows
#     are untouched — only the index changes.
#
# Dropping a redundant index changes ONLY the query plan, never a result (No canonical value affected).
_INDEX_DROPS: tuple[str, ...] = (
    "DROP INDEX IF EXISTS ix_daily_prices_symbol_date",
    "DROP INDEX IF EXISTS ix_forward_returns_run_symbol",
    "DROP INDEX IF EXISTS ix_next_session_manifests_as_of",
)
_INDEX_ADDS: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS ix_daily_prices_date ON daily_prices (date)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_next_session_manifests_as_of_version ON next_session_manifests (as_of, version)",
)


def _ensure_index_hygiene(engine: Engine) -> None:
    """Drop the duplicate/redundant indexes and add the new date index (idempotent; safe on a fresh DB
    and on a live one still carrying the old indexes)."""
    with engine.begin() as conn:
        for ddl in _INDEX_DROPS:
            conn.execute(text(ddl))
        for ddl in _INDEX_ADDS:
            conn.execute(text(ddl))


def create_db_and_tables(engine: Optional[Engine] = None) -> None:
    eng = engine or get_engine()
    SQLModel.metadata.create_all(eng)
    _ensure_additive_columns(eng)
    _ensure_index_hygiene(eng)


def get_session():
    """FastAPI dependency yielding a session bound to the process engine."""
    with Session(get_engine()) as session:
        yield session
