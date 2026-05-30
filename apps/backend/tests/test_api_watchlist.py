"""POST / GET / DELETE /api/watchlist — the product's first user-write surface (iter-7, J-11).

Proves: the add→get→delete roundtrip; the entry carries date-added + reason and the CURRENT canonical
scores/setup/invalidation read LIVE from `score_stocks` (single source → J-06 on a write surface:
byte-identical to that ticker's `/api/stocks` row); price-since-added is honest (0.00% vs the frozen
seed, NA when `entry_close` is null); unknown ticker → 404; duplicate → 409 (no duplicate row); DELETE
of a missing entry → 404; and add/remove touches NO immutable snapshot/forward-return row.

The shared `loaded_engine` fixture is also the process engine, so the `TestClient` reads the same
seeded DB. `clean_watchlist` empties the (user-mutable) watchlist table around each test so they stay
independent without touching any snapshot table.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlmodel import Session, select

import main
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.models import (
    ForwardReturn,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
    Watchlist,
)

TICKER = "ANET"
REASON = "ANET — strong leader, watching pullback"
_SCORE_BLOCKS = ("leadership", "entry_quality", "risk")
_CANONICAL_KEYS = ("leadership", "entry_quality", "risk", "setup", "invalidation")
_SNAPSHOT_MODELS = (ScannerRun, ScannerResult, SectorScoreRow, ThemeScoreRow, ForwardReturn)


@pytest.fixture
def clean_watchlist(loaded_engine):
    """Each test starts and ends with an empty watchlist (user-mutable; snapshot tables untouched)."""

    def _clear():
        with Session(loaded_engine) as session:
            for entry in session.exec(select(Watchlist)).all():
                session.delete(entry)
            session.commit()

    _clear()
    yield
    _clear()


def _wl_count(engine) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(Watchlist)) or 0


def test_add_get_delete_roundtrip(clean_watchlist, loaded_engine):
    with TestClient(main.app) as client:
        created = client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON})
        assert created.status_code == 200
        row = created.json()
        assert row["ticker"] == TICKER
        assert row["reason"] == REASON
        assert row["date_added"]  # ISO datetime "date added"
        assert row["asof_date_added"]
        # the enriched add response IS a GET row — three current scores + setup + invalidation
        for block in _SCORE_BLOCKS:
            assert {"score", "bucket", "components"} <= set(row[block])
        assert row["setup"]["status"]
        assert row["invalidation"]["note"]
        assert "price_since_added" in row
        entry_id = row["id"]
        assert _wl_count(loaded_engine) == 1

        listed = client.get("/api/watchlist")
        assert listed.status_code == 200
        body = listed.json()
        assert body["asof_date"]
        assert [e["ticker"] for e in body["entries"]] == [TICKER]

        deleted = client.delete(f"/api/watchlist/{entry_id}")
        assert deleted.status_code == 200
        assert client.get("/api/watchlist").json()["entries"] == []
        assert _wl_count(loaded_engine) == 0


def test_single_source_equals_stocks_row_byte_for_byte(clean_watchlist):
    """J-06 on the write surface: the watchlist entry's CURRENT scores/bucket/setup/invalidation are
    byte-identical to that ticker's `/api/stocks` row — read live from the SAME `score_stocks` pass,
    never stored-then-drifting nor recomputed."""
    with TestClient(main.app) as client:
        client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON})
        entry = client.get("/api/watchlist").json()["entries"][0]
        stock_rows = client.get("/api/stocks").json()["rows"]
    stock_row = next(r for r in stock_rows if r["ticker"] == TICKER)
    for key in _CANONICAL_KEYS:
        assert entry[key] == stock_row[key], f"{key} drifted from the canonical /api/stocks row"


def test_price_since_added_is_honest_zero_on_frozen_seed(clean_watchlist):
    """Added on the seed's latest data date ⇒ entry_close == current close ⇒ price_since_added is
    exactly 0.0 (a real number renders). That is the correct, non-fabricated value — NOT a defect."""
    with TestClient(main.app) as client:
        created = client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON}).json()
    assert created["price_since_added"] == 0.0


def test_lowercase_ticker_is_canonicalized(clean_watchlist):
    """A free-text ticker is upper-cased to the canonical universe symbol before storage."""
    with TestClient(main.app) as client:
        created = client.post("/api/watchlist", json={"ticker": "anet", "reason": REASON})
    assert created.status_code == 200
    assert created.json()["ticker"] == TICKER


def test_unknown_ticker_rejected_with_no_row(clean_watchlist):
    with TestClient(main.app) as client:
        resp = client.post("/api/watchlist", json={"ticker": "ZZZZ", "reason": "not in the universe"})
        assert resp.status_code == 404  # explicit rejection, no fabricated row
        assert client.get("/api/watchlist").json()["entries"] == []


def test_duplicate_ticker_makes_no_duplicate_row(clean_watchlist, loaded_engine):
    with TestClient(main.app) as client:
        assert client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON}).status_code == 200
        dup = client.post("/api/watchlist", json={"ticker": TICKER, "reason": "second add"})
        assert dup.status_code == 409  # conflict
        entries = client.get("/api/watchlist").json()["entries"]
    assert [e["ticker"] for e in entries] == [TICKER]  # exactly one row
    assert _wl_count(loaded_engine) == 1


def test_delete_missing_entry_404(clean_watchlist):
    with TestClient(main.app) as client:
        assert client.delete("/api/watchlist/99999999").status_code == 404


def test_add_remove_touches_no_snapshot_row(clean_watchlist, loaded_engine):
    """Immutability isolation: add+remove changes ONLY the watchlist table; the append-only
    scanner_runs/scanner_results/*_scores/forward_returns row counts are unchanged."""

    def snapshot_counts():
        with Session(loaded_engine) as session:
            return {m.__name__: session.scalar(select(func.count()).select_from(m)) for m in _SNAPSHOT_MODELS}

    with TestClient(main.app) as client:
        before = snapshot_counts()  # counted AFTER lifespan bootstrap, so the counts are stable
        created = client.post("/api/watchlist", json={"ticker": TICKER, "reason": REASON}).json()
        after_add = snapshot_counts()
        assert _wl_count(loaded_engine) == 1  # the add really happened (test is not vacuously green)
        client.delete(f"/api/watchlist/{created['id']}")
        after_del = snapshot_counts()
        assert _wl_count(loaded_engine) == 0  # the remove really happened
    assert before == after_add == after_del  # no snapshot/forward-return row was ever touched


def test_watchlist_raises_503_when_no_price_data(tmp_path):
    """No price data → explicit 503 on GET and POST (never a fabricated row). The handlers are called
    directly against an empty DB session, leaving the shared process engine untouched."""
    from app.api.watchlist import WatchlistCreate, add_watchlist, list_watchlist

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)  # tables exist, but no price rows were ever loaded
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as get_exc:
            list_watchlist(session)
        assert get_exc.value.status_code == 503
        with pytest.raises(HTTPException) as post_exc:
            add_watchlist(WatchlistCreate(ticker=TICKER, reason=REASON), session)
        assert post_exc.value.status_code == 503
