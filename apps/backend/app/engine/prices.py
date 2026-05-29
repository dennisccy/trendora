"""bars_asof — the no-lookahead boundary (anti-goal: No lookahead).

`bars_asof(session, symbol, d)` returns the symbol's `daily_prices` rows with **date <= d**,
ascending by date. EVERY engine computation (regime, sectors, and later scoring/walk-forward)
reads bars through this accessor and never touches a bar with date > d, so a snapshot dated D
is computed only from information available on D. The full walk-forward proof arrives in
iter-6; this accessor + its boundary test are the groundwork.

Also provides the tiny ascending-series extractors the indicator functions consume.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import DailyPrice


def latest_data_date(session: Session) -> Optional[date_cls]:
    """The latest date present in `daily_prices` = the deterministic as-of date for a request.
    None when no price data exists (callers surface an explicit unavailable state)."""
    return session.scalar(select(func.max(DailyPrice.date)))


def bars_asof(session: Session, symbol: str, d: date_cls) -> list[DailyPrice]:
    """All bars for `symbol` with date <= `d`, ascending. The no-lookahead boundary."""
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date <= d)
        .order_by(DailyPrice.date)
    )
    return list(session.exec(stmt).all())


# --- ascending-series extractors (the indicator functions take plain float lists) ----------
def closes(bars: list[DailyPrice]) -> list[float]:
    return [b.close for b in bars]


def highs(bars: list[DailyPrice]) -> list[float]:
    return [b.high for b in bars]


def lows(bars: list[DailyPrice]) -> list[float]:
    return [b.low for b in bars]


def volumes(bars: list[DailyPrice]) -> list[float]:
    return [b.volume for b in bars]
