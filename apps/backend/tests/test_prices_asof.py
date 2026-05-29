"""bars_asof — the no-lookahead boundary (anti-goal: No lookahead).

Proves the as-of accessor returns bars with date <= d (INCLUDING date == d) and EXCLUDES
any bar with date > d. All engine math reads bars through this accessor, so this boundary is
the groundwork for the walk-forward no-lookahead proof (full proof lands iter-6).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import insert
from sqlmodel import Session

from app.db import create_db_and_tables, make_engine
from app.engine.prices import bars_asof, closes, highs, lows, volumes
from app.models import DailyPrice


def _fresh_session() -> Session:
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    return Session(engine)


def _insert(session: Session, symbol: str, rows: list[tuple[str, float]]) -> None:
    payload = [
        {
            "symbol": symbol,
            "date": date.fromisoformat(d),
            "open": c,
            "high": c,
            "low": c,
            "close": c,
            "volume": 1000.0,
        }
        for d, c in rows
    ]
    session.execute(insert(DailyPrice.__table__), payload)
    session.commit()


def test_bars_asof_includes_d_excludes_future():
    session = _fresh_session()
    _insert(
        session,
        "TEST",
        [("2026-01-01", 10), ("2026-01-02", 11), ("2026-01-03", 12)],
    )
    rows = bars_asof(session, "TEST", date(2026, 1, 2))
    got = [r.date.isoformat() for r in rows]
    assert got == ["2026-01-01", "2026-01-02"]  # includes d=01-02, excludes future 01-03


def test_bars_asof_returns_ascending():
    session = _fresh_session()
    # insert out of order; accessor must return ascending by date
    _insert(session, "TEST", [("2026-01-03", 12), ("2026-01-01", 10), ("2026-01-02", 11)])
    rows = bars_asof(session, "TEST", date(2026, 1, 3))
    assert [r.date.isoformat() for r in rows] == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert closes(rows) == [10.0, 11.0, 12.0]


def test_bars_asof_empty_for_unknown_symbol():
    session = _fresh_session()
    _insert(session, "TEST", [("2026-01-01", 10)])
    assert bars_asof(session, "NOPE", date(2026, 1, 1)) == []


def test_series_extractors():
    session = _fresh_session()
    _insert(session, "TEST", [("2026-01-01", 10), ("2026-01-02", 20)])
    rows = bars_asof(session, "TEST", date(2026, 1, 2))
    assert closes(rows) == [10.0, 20.0]
    assert highs(rows) == [10.0, 20.0]
    assert lows(rows) == [10.0, 20.0]
    assert volumes(rows) == [1000.0, 1000.0]
