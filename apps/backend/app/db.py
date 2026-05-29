"""Database engine + session helpers.

Engine URL comes from config (`database.url`) so SQLite -> Postgres is a config-only
switch. A relative `sqlite:///` path is resolved against the repository root so the engine
is correct regardless of the process working directory. `create_db_and_tables()` runs
`SQLModel.metadata.create_all()` on startup (no Alembic — see project-template).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

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


def create_db_and_tables(engine: Optional[Engine] = None) -> None:
    SQLModel.metadata.create_all(engine or get_engine())


def get_session():
    """FastAPI dependency yielding a session bound to the process engine."""
    with Session(get_engine()) as session:
        yield session
