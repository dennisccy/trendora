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
from app.engine.prices import bars_after, bars_asof, bars_through_latest, closes, highs, lows, volumes
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


# --- iter-6 (J-20): full-path display accessor (NOT bounded by D) -------------------------------
def test_bars_through_latest_is_full_unbounded_ascending():
    """`bars_through_latest` returns the symbol's ENTIRE history, ascending — NOT bounded by any as-of
    date (distinct from `bars_asof`). This is the display-only full path the chart renders."""
    session = _fresh_session()
    _insert(session, "TEST", [("2026-01-01", 10), ("2026-01-03", 12), ("2026-01-02", 11)])
    rows = bars_through_latest(session, "TEST")
    assert [r.date.isoformat() for r in rows] == ["2026-01-01", "2026-01-02", "2026-01-03"]  # ALL, ascending
    assert closes(rows) == [10.0, 11.0, 12.0]


def test_bars_through_latest_empty_for_unknown_symbol():
    session = _fresh_session()
    _insert(session, "TEST", [("2026-01-01", 10)])
    assert bars_through_latest(session, "NOPE") == []


def test_bars_through_latest_equals_asof_plus_after_partition():
    """J-20 no-lookahead: the full display path partitions EXACTLY at D into `bars_asof` (<= D) ++
    `bars_after` (> D), with no overlap and no gap — so the forward region the chart labels is precisely
    the post-D bars the scoring path (which reads only `bars_asof`) never sees."""
    session = _fresh_session()
    _insert(session, "TEST", [("2026-01-01", 10), ("2026-01-02", 11), ("2026-01-03", 12), ("2026-01-06", 13)])
    d = date(2026, 1, 2)
    full = [r.date for r in bars_through_latest(session, "TEST")]
    asof = [r.date for r in bars_asof(session, "TEST", d)]
    after = [r.date for r in bars_after(session, "TEST", d)]
    assert full == asof + after                              # exact partition (ordered, no overlap/gap)
    assert all(x <= d for x in asof) and all(x > d for x in after)


def test_post_d_bars_do_not_change_bars_asof_the_scoring_input():
    """J-20 no-lookahead (scoring seam): inserting bars with date > D leaves `bars_asof(symbol, D)` —
    the EXACT input every score/VCP computation reads — byte-identical. The display-only forward path
    adds post-D bars for the chart; because scoring reads `bars_asof` (<= D), they can never move a score."""
    session = _fresh_session()
    _insert(session, "TEST", [("2026-01-01", 10), ("2026-01-02", 11)])
    d = date(2026, 1, 2)
    before = [(r.date, r.close) for r in bars_asof(session, "TEST", d)]
    _insert(session, "TEST", [("2026-01-03", 99), ("2026-01-06", 123)])  # post-D bars (the forward region)
    after = [(r.date, r.close) for r in bars_asof(session, "TEST", d)]
    assert before == after  # the scoring input is unchanged by the forward extension
