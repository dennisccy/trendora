"""Restart-persistence crux (J-11): a watchlist entry survives a backend "restart".

The restart is simulated at the engine layer (authoritative, deterministic, no live server needed):
create a FILE-BACKED SQLite DB — NOT ':memory:', which would vanish on reopen — INSERT a watchlist
entry through one engine, DISPOSE that engine (drop every pooled connection: the process-shutdown
analogue), then build a BRAND-NEW engine against the SAME on-disk path (the "restart") and assert the
entry is read back unchanged. This proves the watchlist is DB-backed, not an in-memory dict/module
global. The browser sweep demonstrates the same crux through a real backend restart.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.db import create_db_and_tables, make_engine
from app.models import ForwardReturn, ScannerResult, ScannerRun, Watchlist

_TICKER = "ANET"
_REASON = "ANET — strong leader, watching pullback"
_ASOF = date(2026, 5, 28)
_ENTRY_CLOSE = 123.45


def test_watchlist_entry_survives_engine_restart(tmp_path):
    db_path = tmp_path / "restart.db"
    url = f"sqlite:///{db_path}"

    # --- session 1: write an entry, then dispose the engine (the "shutdown") ---
    engine1 = make_engine(url)
    create_db_and_tables(engine1)
    with Session(engine1) as session:
        session.add(
            Watchlist(
                ticker=_TICKER,
                reason=_REASON,
                created_at=datetime.now(timezone.utc),
                asof_date_added=_ASOF,
                entry_close=_ENTRY_CLOSE,
            )
        )
        session.commit()
    engine1.dispose()

    # the data lives on disk (it was never ':memory:'), so a fresh process could read it back
    assert db_path.exists()

    # --- session 2: a brand-new engine against the SAME file (the "restart") ---
    engine2 = make_engine(url)
    with Session(engine2) as session:
        rows = session.exec(select(Watchlist)).all()
    engine2.dispose()

    assert len(rows) == 1  # the entry persisted across the restart — not in-memory only
    entry = rows[0]
    assert entry.ticker == _TICKER
    assert entry.reason == _REASON
    assert entry.asof_date_added == _ASOF
    assert entry.entry_close == _ENTRY_CLOSE


def test_persisted_watchlist_does_not_create_snapshot_rows(tmp_path):
    """Adding a watchlist entry writes ONLY the watchlist table — it never creates a snapshot or
    forward-return row (the watchlist is not a snapshot table; Snapshots-immutable is unaffected)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'isolation.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(
            Watchlist(
                ticker=_TICKER,
                reason=_REASON,
                created_at=datetime.now(timezone.utc),
                asof_date_added=_ASOF,
                entry_close=_ENTRY_CLOSE,
            )
        )
        session.commit()
        assert session.exec(select(Watchlist)).all()  # the watchlist row exists
        # …and the append-only snapshot / forward-return tables stayed empty
        assert session.exec(select(ScannerRun)).all() == []
        assert session.exec(select(ScannerResult)).all() == []
        assert session.exec(select(ForwardReturn)).all() == []
    engine.dispose()
