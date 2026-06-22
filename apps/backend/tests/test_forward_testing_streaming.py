"""iter-47 (J-105) — the warm-up backfill builds its forward-return idempotency set by STREAMING
column-projected keys (`select(ForwardReturn.run_id, .symbol, .horizon)` consumed with `yield_per`)
instead of materializing every stored `ForwardReturn` ORM row at once. These tests pin that the streamed
key set is IDENTICAL to the full-table set (so idempotency + the INSERT-only/append-only contract are
preserved — no duplicate insert, no overwrite) and that the streaming is chunk-independent.

The fast proofs use a hand-built `forward_returns` table (no slow seed boot); the slow end-to-end
idempotency (`a second backfill inserts 0 rows`) stays covered by `test_forward_testing.py`'s
`test_backfill_is_idempotent` (which now exercises this streamed scan through `_backfill`).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import _streamed_existing_keys
from app.models import ForwardReturn


def _add_fr(session, run_id, symbol, horizon, ret):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret,
        mae=-0.05, mfe=0.15, max_drawdown=-0.08,
    ))


@pytest.fixture()
def fr_engine(tmp_path):
    """A hand-built `forward_returns` table with several (run, symbol, horizon) keys across multiple runs
    and horizons — so the streamed key scan must reproduce the full distinct key set exactly."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fr.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for run_id in (1, 2, 3):
            for symbol in ("AA", "BB", "SPY"):
                for horizon in (1, 5, 20):
                    _add_fr(session, run_id, symbol, horizon, 0.01 * run_id)
        session.commit()
    return engine


@pytest.mark.parametrize("batch", [1, 2, 7, 1_000_000])
def test_streamed_existing_keys_equals_full_table_set(fr_engine, batch):
    """The streamed/projected idempotency key set equals the full-table `{(run_id, symbol, horizon)}` set,
    independent of the streaming batch size — so the backfill's idempotency decision is unchanged."""
    with Session(fr_engine) as session:
        reference = {
            (fr.run_id, fr.symbol, fr.horizon)
            for fr in session.exec(select(ForwardReturn)).all()
        }
        streamed = _streamed_existing_keys(session, batch)
        assert streamed == reference, f"streamed key set differs at batch={batch}"
        assert len(streamed) == 27  # 3 runs x 3 symbols x 3 horizons, distinct by construction


def test_streamed_existing_keys_are_plain_tuples(fr_engine):
    """The streamed keys are plain `(int, str, int)` tuples (projected Row values), NOT ORM rows — the
    representation that bounds memory on the grown table."""
    with Session(fr_engine) as session:
        keys = _streamed_existing_keys(session, load_config().research.read_batch_size)
    sample = next(iter(keys))
    assert isinstance(sample, tuple) and len(sample) == 3
    run_id, symbol, horizon = sample
    assert isinstance(run_id, int) and isinstance(symbol, str) and isinstance(horizon, int)
