"""bars_asof / bars_after — the two no-lookahead boundaries (anti-goal: No lookahead).

`bars_asof(session, symbol, d)` returns the symbol's `daily_prices` rows with **date <= d**,
ascending by date. EVERY scoring/regime/sector computation reads bars through this accessor and
never touches a bar with date > d, so a snapshot dated D is computed only from information
available on D (the backward boundary — the AS-OF score side).

`bars_after(session, symbol, d)` is its strict inverse: the rows with **date > d**, ascending.
The iter-6 walk-forward forward-testing engine measures realized forward returns ONLY through
`bars_after` (date > D), so realized returns are drawn exclusively from POST-snapshot data and a
future bar can never influence an as-of score. Together the two accessors partition a symbol's
history at D with no overlap (date <= d vs date > d) — that disjointness IS the no-lookahead proof.

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
    """All bars for `symbol` with date <= `d`, ascending. The backward no-lookahead boundary."""
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date <= d)
        .order_by(DailyPrice.date)
    )
    return list(session.exec(stmt).all())


def close_on(session: Session, symbol: str, d: date_cls) -> Optional[float]:
    """The close of the latest bar with **date <= `d`** (the as-of close on D), or None when the
    symbol has no bar on/before D. This is the single-bar form of `bars_asof(session, symbol, d)[-1]
    .close` — the SAME backward boundary (date <= d, no lookahead) — but it fetches only the one bar
    instead of materializing the symbol's full pre-history, so the walk-forward backfill can read each
    forward return's entry close cheaply."""
    stmt = (
        select(DailyPrice.close)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date <= d)
        .order_by(DailyPrice.date.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def bars_after(
    session: Session, symbol: str, d: date_cls, limit: Optional[int] = None
) -> list[DailyPrice]:
    """All bars for `symbol` with **date > `d`**, ascending — the strict inverse of `bars_asof`
    and the forward no-lookahead boundary used by the walk-forward forward-testing engine.

    `limit` (optional) caps the number of leading post-snapshot bars returned. A forward return
    over `horizon` trading days only needs the first `horizon` post-bars, so the backfill passes
    `limit=max(horizons)` to avoid materializing the full multi-year tail per (symbol, run); the
    result is byte-identical to the unbounded call truncated to `limit` (the boundary is unchanged,
    only later, irrelevant bars are not fetched). The no-lookahead boundary test calls it WITHOUT a
    limit and asserts no returned bar has date <= d."""
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date > d)
        .order_by(DailyPrice.date)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(session.exec(stmt).all())


def bars_through_latest(session: Session, symbol: str) -> list[DailyPrice]:
    """All bars for `symbol`, ascending — the symbol's FULL price path, NOT bounded by any as-of date
    (distinct from `bars_asof`). DISPLAY-ONLY (J-20): the Stock-Detail chart renders this full path so a
    user viewing a historical as-of D can see what happened AFTER the snapshot, with D marked and the
    post-D region labelled forward/after-as-of.

    CRITICAL no-lookahead carve-out: the bars this returns with date > D are VISUALIZATION ONLY. They
    MUST NOT feed any score, bucket, setup status, VCP flag, factor, or ranking — all of which keep
    reading `bars_asof` (date <= D). This accessor is therefore NEVER routed into `scoring.score_stocks`
    / `patterns.detect_vcp` / `scanner.run_scan`; its sole caller is the chart endpoint. For a historical
    D the full path equals `bars_asof(symbol, D)` ++ `bars_after(symbol, D)` exactly (a disjoint partition
    at D), so the labelled forward region is precisely the post-D bars the scoring side never reads."""
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
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
