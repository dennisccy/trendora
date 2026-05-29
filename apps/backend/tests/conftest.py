"""Shared pytest fixtures. The committed seed must exist (built by scripts/ingest_seed.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = BACKEND_DIR / "data" / "seed"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import db as db_module  # noqa: E402
from app.config import load_config  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.seed_loader import load_seed  # noqa: E402


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def seed_dir() -> Path:
    return SEED_DIR


@pytest.fixture(scope="session")
def loaded_engine(tmp_path_factory, config, seed_dir):
    """A temp SQLite DB with the real committed seed loaded ONCE. Also registered as the
    process engine so the FastAPI app (TestClient) reads the same database."""
    db_path = tmp_path_factory.mktemp("db") / "trendora_test.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    summary = load_seed(engine, config, seed_dir)
    assert summary["loaded"] is True and summary["price_rows"] > 0
    db_module.set_engine(engine)
    return engine
