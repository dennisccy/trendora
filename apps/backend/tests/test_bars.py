"""GET /api/stocks/{ticker}/bars — the canonical price/MA/volume series for the chart.

The endpoint serves OHLCV bars read ONLY through `bars_asof` (date <= as-of, no lookahead) and a
moving-average map keyed by every `config.indicators.ma_periods` entry, each a `sma_series` aligned
1:1 with the bars. Single source of truth: the MA series is the SAME canonical `sma`/`sma_series`
that feeds the invalidation level — `ma[str(inv_period)][-1]` equals the detail row's
`invalidation.level`. Unknown ticker -> 404; no price data -> 503 (never a fabricated row).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.indicators import sma
from app.engine.prices import bars_asof, closes, latest_data_date

BAR_KEYS = {"date", "open", "high", "low", "close", "volume"}


def test_bars_ascending_all_dates_le_asof_no_lookahead(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected_len = len(bars_asof(session, "NVDA", asof))
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/NVDA/bars")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "NVDA"
    assert body["asof_date"] == asof.isoformat()

    bars = body["bars"]
    assert len(bars) == expected_len and len(bars) > 0
    assert all(set(b) == BAR_KEYS for b in bars)
    dates = [b["date"] for b in bars]
    assert dates == sorted(dates)                 # ascending
    assert all(d <= body["asof_date"] for d in dates)  # no bar after the as-of date (no lookahead)


def test_bars_ma_keyed_by_every_config_period_and_length_aligned(loaded_engine):
    cfg = load_config()
    with TestClient(main.app) as client:
        body = client.get("/api/stocks/NVDA/bars").json()
    bars, ma = body["bars"], body["ma"]

    assert set(ma) == {str(p) for p in cfg.indicators.ma_periods}   # keyed by EVERY config MA period
    for period in cfg.indicators.ma_periods:
        series = ma[str(period)]
        assert len(series) == len(bars)                              # aligned 1:1 with bars
        assert series[0] is None                                     # warm-up prefix is NA (a gap)
        assert all(v is None or isinstance(v, (int, float)) for v in series)


def test_bars_ma_series_endpoint_equals_canonical_sma_single_source(loaded_engine):
    """The chart MA and the invalidation level are ONE value: `ma[str(p)][-1] == sma(closes, p)`
    for every period, and `ma[str(inv_period)][-1]` equals the detail row's `invalidation.level`."""
    cfg = load_config()
    inv_period = cfg.decision_rules.invalidation.ma_period
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        nvda_closes = closes(bars_asof(session, "NVDA", asof))
    with TestClient(main.app) as client:
        ma = client.get("/api/stocks/NVDA/bars").json()["ma"]
        detail_inv = client.get("/api/stocks/NVDA").json()["row"]["invalidation"]

    for period in cfg.indicators.ma_periods:
        assert ma[str(period)][-1] == sma(nvda_closes, period)
    assert ma[str(inv_period)][-1] == detail_inv["level"]            # chart MA == invalidation level


def test_bars_unknown_ticker_404(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/NOTREAL/bars")
    assert resp.status_code == 404


def test_bars_case_insensitive(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/nvda/bars")
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "NVDA"


def test_bars_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 (never a fabricated/empty-but-OK row). Called at the handler
    level against an empty DB, mirroring the other stock routes' 503 contract."""
    from app.api.stocks import stock_bars

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            stock_bars("NVDA", session=session)  # iter-8: optional `as_of` first → session by keyword
        assert exc.value.status_code == 503


# --- iter-8: as-of chart (date <= D, no lookahead) -----------------------------------------
def test_bars_asof_historical_returns_only_bars_le_d(loaded_engine):
    """`/bars?as_of=D` returns only bars with date <= D (the as-of chart; no lookahead) and echoes D."""
    cfg = load_config()
    target = max(cfg.scanner.bootstrap_dates)  # a historical date within the seed
    with Session(loaded_engine) as session:
        expected_len = len(bars_asof(session, "NVDA", target))
    with TestClient(main.app) as client:
        body = client.get(f"/api/stocks/NVDA/bars?as_of={target.isoformat()}").json()
    assert body["asof_date"] == target.isoformat()
    assert len(body["bars"]) == expected_len and expected_len > 0
    assert all(b["date"] <= target.isoformat() for b in body["bars"])  # no bar after D (no lookahead)


def test_bars_asof_invalid_dates_are_4xx(loaded_engine):
    """An invalid `as_of` on the chart endpoint is an explicit 4xx — never a fabricated series."""
    with TestClient(main.app) as client:
        assert client.get("/api/stocks/NVDA/bars?as_of=2999-01-01").status_code == 400  # future
        assert client.get("/api/stocks/NVDA/bars?as_of=not-a-date").status_code == 422  # unparseable
