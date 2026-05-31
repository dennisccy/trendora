"""POST / GET / DELETE /api/watchlist — the product's FIRST user-write surface (iter-7, J-11).

The watchlist is a persistent **research save-list**, not an order/position path: there is no
quantity, cost-basis, P&L, or order/buy/sell/broker concept anywhere here (*No order/execution
path*, critical). It is also NOT a snapshot table — adding/removing an entry only INSERTs/DELETEs a
`watchlist` row and NEVER touches a `scanner_runs` / `scanner_results` / `*_scores` /
`forward_returns` row (*Snapshots are immutable*, critical).

Single source of truth (J-06 on a write surface): an entry stores ONLY
`{ticker, reason, created_at, asof_date_added, entry_close}`. Its *current* Leadership / Entry
Quality / Risk `{score, bucket}`, setup `{status, reason}`, and `invalidation` are READ at serve time
from the LATEST persisted IMMUTABLE snapshot row — the SAME stored row `GET /api/stocks` serves at the
latest date (iter-8: snapshot-served, not a live `score_stocks` recompute) — and taken **verbatim**, so
they can never become a second, drifting source. `price_since_added` is the only per-entry derived
figure: the canonical current close ÷ the
stored `entry_close` − 1 (an honest 0.00% against the frozen seed when no post-add bars exist; NA
when `entry_close` is null — never fabricated). This file holds NO scoring/threshold literal — it
reads everything canonical.

Status contract: `404` for a ticker outside `config.universe.symbols` (no fabricated row); `409`
for a duplicate add (the unique `ticker` guarantees no duplicate row); `503` when no price data
exists; `404` deleting a missing entry.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import Config, get_config
from app.db import get_session
from app.engine.prices import close_on, latest_data_date
from app.engine.snapshot_serving import resolved_run, stocks_payload
from app.models import Watchlist

router = APIRouter(tags=["watchlist"])

# Canonical fields read VERBATIM from the score_stocks row (single source — never recomputed/stored).
_CANONICAL_FIELDS = ("sector", "leadership", "entry_quality", "risk", "setup", "invalidation")


class WatchlistCreate(BaseModel):
    """POST body — a ticker (validated against the universe, upper-cased) and a free-text reason."""

    ticker: str
    reason: str


def _canonical_rows(session: Session, cfg: Config) -> dict[str, dict]:
    """The SAME stored snapshot rows `/api/stocks` serves at the latest date, indexed by ticker
    (single source → J-06). iter-8: read from the latest persisted IMMUTABLE snapshot — never a live
    `score_stocks` recompute (anti-goal: No recompute in the read path)."""
    rows = stocks_payload(session, resolved_run(session, None, cfg))["rows"]
    return {row["ticker"]: row for row in rows}


def _price_since_added(session: Session, ticker: str, asof, entry_close: Optional[float]) -> Optional[float]:
    """Current canonical close ÷ stored `entry_close` − 1, from the canonical price series. NA (None)
    when `entry_close` is null or no current close exists — never fabricated. 0.0 (honest) when the
    entry was added on the latest data date (entry_close == current close)."""
    if not entry_close:  # None or 0.0 → cannot form an honest ratio
        return None
    current = close_on(session, ticker, asof)
    if current is None:
        return None
    return current / entry_close - 1


def _enrich(entry: Watchlist, rows_by_ticker: dict[str, dict], session: Session, asof) -> dict:
    """Build the served entry: stored user/identity fields + price-since-added, plus the CURRENT
    canonical scores/setup/invalidation read verbatim from the `score_stocks` row (single source)."""
    canonical = rows_by_ticker.get(entry.ticker)
    row = {
        "id": entry.id,
        "ticker": entry.ticker,
        "date_added": entry.created_at.isoformat(),
        "asof_date_added": entry.asof_date_added.isoformat(),
        "reason": entry.reason,
        "price_since_added": _price_since_added(session, entry.ticker, asof, entry.entry_close),
    }
    for field in _CANONICAL_FIELDS:
        row[field] = canonical[field] if canonical else None
    return row


@router.get("/watchlist")
def list_watchlist(session: Session = Depends(get_session)) -> dict:
    """Every watchlist entry (newest first), each enriched LIVE with its current canonical
    scores/setup/invalidation and an honest price-since-added. `503` when no price data exists."""
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    rows_by_ticker = _canonical_rows(session, get_config())
    entries = session.exec(
        select(Watchlist).order_by(Watchlist.created_at.desc(), Watchlist.id.desc())
    ).all()
    return {
        "asof_date": asof.isoformat(),
        "entries": [_enrich(entry, rows_by_ticker, session, asof) for entry in entries],
    }


@router.post("/watchlist")
def add_watchlist(payload: WatchlistCreate, session: Session = Depends(get_session)) -> dict:
    """Add a stock to the watchlist. Validates the ticker against `config.universe.symbols`
    (`404` if unknown — no fabricated row), captures `asof_date_added` + canonical `entry_close`
    ONCE, rejects a duplicate (`409` — no duplicate row), and returns the enriched GET-shaped row.
    `503` when no price data exists."""
    cfg = get_config()
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")

    requested = payload.ticker.strip().upper()
    symbol = next((s for s in cfg.universe.symbols if s.upper() == requested), None)
    if symbol is None:
        raise HTTPException(status_code=404, detail=f"unknown ticker: {payload.ticker}")

    if session.exec(select(Watchlist).where(Watchlist.ticker == symbol)).first() is not None:
        raise HTTPException(status_code=409, detail=f"{symbol} is already on the watchlist")

    entry = Watchlist(
        ticker=symbol,
        reason=payload.reason,
        created_at=datetime.now(timezone.utc),
        asof_date_added=asof,
        entry_close=close_on(session, symbol, asof),  # captured once (parallel to ForwardReturn)
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _enrich(entry, _canonical_rows(session, cfg), session, asof)


@router.delete("/watchlist/{entry_id}")
def remove_watchlist(entry_id: int, session: Session = Depends(get_session)) -> dict:
    """Remove an entry by id. `404` if absent (never a silent no-op)."""
    entry = session.get(Watchlist, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown watchlist entry: {entry_id}")
    session.delete(entry)
    session.commit()
    return {"id": entry_id, "deleted": True}
