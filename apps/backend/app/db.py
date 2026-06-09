"""Database engine + session helpers.

Engine URL comes from config (`database.url`) so SQLite -> Postgres is a config-only
switch. A relative `sqlite:///` path is resolved against the repository root so the engine
is correct regardless of the process working directory. `create_db_and_tables()` runs
`SQLModel.metadata.create_all()` on startup (no Alembic — see project-template).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  -- ensure all tables are registered on SQLModel.metadata
from app.config import REPO_ROOT, get_config

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


def make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


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


def create_db_and_tables(engine: Optional[Engine] = None) -> None:
    eng = engine or get_engine()
    SQLModel.metadata.create_all(eng)
    _ensure_additive_columns(eng)


def get_session():
    """FastAPI dependency yielding a session bound to the process engine."""
    with Session(get_engine()) as session:
        yield session
