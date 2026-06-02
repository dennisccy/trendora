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
from app.engine.prices import bars_asof, bars_through_latest, closes, latest_data_date

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


# --- iter-6 (J-20): full-path-through-latest display extension (opt-in ?through=latest) ---------
def test_bars_through_latest_marks_forward_region_and_boundary(loaded_engine):
    """`?through=latest` at a historical D renders the FULL path: bars with date > D appear, each bar
    carries `is_forward` (True iff date > D), the payload exposes `latest_date`, and the <= D region is
    byte-identical to the default (<= D) response — a display-only forward extension, no lookahead."""
    cfg = load_config()
    target = max(cfg.scanner.bootstrap_dates)  # a historical seed date (post-D bars exist)
    with Session(loaded_engine) as session:
        full_len = len(bars_through_latest(session, "NVDA"))
        asof_len = len(bars_asof(session, "NVDA", target))
    with TestClient(main.app) as client:
        full = client.get(f"/api/stocks/NVDA/bars?as_of={target.isoformat()}&through=latest").json()
        default = client.get(f"/api/stocks/NVDA/bars?as_of={target.isoformat()}").json()

    assert full["asof_date"] == target.isoformat()          # the as-of boundary D is still echoed
    assert full["latest_date"] == full["bars"][-1]["date"]  # right-hand boundary = last bar shown
    assert len(full["bars"]) == full_len > asof_len         # the full series includes the forward region

    forward = [b for b in full["bars"] if b["is_forward"]]
    le_d = [b for b in full["bars"] if not b["is_forward"]]
    assert len(forward) > 0                                          # there IS a post-D region here
    assert all(b["date"] > target.isoformat() for b in forward)     # forward = strictly after D
    assert all(b["date"] <= target.isoformat() for b in le_d)       # <= D region = on/before D
    assert len(le_d) == asof_len
    # the <= D region is byte-identical to the default response (same OHLCV) — the extension is additive
    assert [{k: b[k] for k in BAR_KEYS} for b in le_d] == default["bars"]


def test_bars_through_latest_ma_le_d_region_matches_default(loaded_engine):
    """The <= D MA values are byte-identical with vs without the forward extension (a trailing SMA only
    depends on prior closes), so the forward path never alters the as-of MA the chart shows for <= D."""
    cfg = load_config()
    target = max(cfg.scanner.bootstrap_dates)
    with TestClient(main.app) as client:
        full = client.get(f"/api/stocks/NVDA/bars?as_of={target.isoformat()}&through=latest").json()
        default = client.get(f"/api/stocks/NVDA/bars?as_of={target.isoformat()}").json()
    n_le_d = len(default["bars"])
    for period in cfg.indicators.ma_periods:
        assert full["ma"][str(period)][:n_le_d] == default["ma"][str(period)]   # <= D MA unchanged


def test_bars_through_latest_at_latest_asof_has_no_forward_region(loaded_engine):
    """At the LATEST as-of (no post-D bars) the full path has NO forward region — every bar is
    is_forward=False — so the chart is visually unchanged (the latest-as-of edge case)."""
    with TestClient(main.app) as client:
        full = client.get("/api/stocks/NVDA/bars?through=latest").json()
    assert len(full["bars"]) > 0
    assert all(b["is_forward"] is False for b in full["bars"])
    assert full["latest_date"] == full["bars"][-1]["date"]


def test_bars_default_contract_unchanged_no_forward_fields(loaded_engine):
    """Default contract (no `?through`) stays <= D and byte-identical: bars carry EXACTLY the six OHLCV
    keys (no `is_forward`) and there is no `latest_date` — the no-lookahead default boundary is obvious."""
    cfg = load_config()
    target = max(cfg.scanner.bootstrap_dates)
    with TestClient(main.app) as client:
        body = client.get(f"/api/stocks/NVDA/bars?as_of={target.isoformat()}").json()
    assert "latest_date" not in body
    assert all(set(b) == BAR_KEYS for b in body["bars"])               # no extra is_forward key
    assert all(b["date"] <= target.isoformat() for b in body["bars"])  # still <= D (no lookahead)


def test_bars_through_latest_keeps_error_contract(loaded_engine):
    """The forward extension preserves the existing explicit error contract — never a fabricated row:
    unknown ticker -> 404; future `as_of` -> 400; unparseable `as_of` -> 422."""
    with TestClient(main.app) as client:
        assert client.get("/api/stocks/NOTREAL/bars?through=latest").status_code == 404
        assert client.get("/api/stocks/NVDA/bars?as_of=2999-01-01&through=latest").status_code == 400
        assert client.get("/api/stocks/NVDA/bars?as_of=not-a-date&through=latest").status_code == 422


def test_bars_through_latest_not_in_scoring_path_source_seam():
    """No-lookahead seam (critical): the display-only full-path helper is referenced ONLY by the price
    accessor module and the chart endpoint — NEVER by the scoring/scanner/pattern engines (which keep
    reading `bars_asof`, date <= D). Proven in source so post-D bars can never feed a score/bucket/VCP."""
    import inspect

    import app.engine.patterns as patterns_mod
    import app.engine.scanner as scanner_mod
    import app.engine.scoring as scoring_mod

    for mod in (scanner_mod, scoring_mod, patterns_mod):
        assert "bars_through_latest" not in inspect.getsource(mod), (
            f"{mod.__name__} must not use the display-only full-path helper (no-lookahead seam)"
        )
