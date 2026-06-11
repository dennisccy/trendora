"""API tests for GET /api/indexes and GET /api/regime-history (J-44 + J-45 / Capability 37).

Served-from-storage read paths over the real committed seed:
  - /api/indexes serves config-listed normalized-% series rebased to the range start, with DIA (a
    bar-less configured symbol) honestly omitted from the series + legend; unknown range -> 422; the
    series equals the engine output (no recompute drift); as-of bounds the series.
  - /api/regime-history serves the stored per-run label/score verbatim, bounded to the resolved as-of.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.config import load_config
from app.engine.indexes import compute_index_series
from app.engine.prices import latest_data_date
from app.engine.regime_history import get_regime_history
from app.engine.scanner import resolve_as_of_date


def _earliest_and_latest_run_dates(session):
    from app.models import ScannerRun
    from sqlmodel import select

    dates = sorted(d for d in session.exec(select(ScannerRun.asof_date)).all())
    return dates[0], dates[-1]


def test_api_indexes_equals_engine_and_omits_barless_dia(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        expected = compute_index_series(session, as_of=None, range_key=None, config=cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes")
    assert resp.status_code == 200
    served = resp.json()
    assert served == expected  # no recompute drift — served value == engine value

    symbols = [s["symbol"] for s in served["series"]]
    # the config lists SPY/QQQ/IWM/RSP/DIA; DIA has no seed bars -> honestly omitted
    assert "DIA" not in symbols
    assert "SPY" in symbols
    # default range comes from config
    assert served["range"]["key"] == cfg.index_chart.default_range
    # every series rebases to ~0% at the range start
    for s in served["series"]:
        assert s["points"][0]["pct"] == 0.0
    # the switcher options are the config presets
    assert served["ranges"] == [{"key": p.key, "label": p.label} for p in cfg.index_chart.range_presets]


def test_api_indexes_unknown_range_is_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes", params={"range": "definitely-not-a-preset"})
    assert resp.status_code == 422


def test_api_indexes_all_range_first_point_is_zero_and_bounded_to_asof(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        # pick an all-history preset key if present, else the default
        all_key = next((p.key for p in cfg.index_chart.range_presets if p.days is None),
                       cfg.index_chart.default_range)
        earliest, _latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
        resolved = resolve_as_of_date(session, d, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes", params={"range": all_key, "as_of": d})
    assert resp.status_code == 200
    served = resp.json()
    assert served["asof_date"] == resolved.isoformat()
    for s in served["series"]:
        assert s["points"][0]["pct"] == 0.0
        # no bar dated after the resolved as-of
        assert all(p["date"] <= served["asof_date"] for p in s["points"])


def test_api_regime_history_equals_engine_and_serves_stored_labels(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        expected = get_regime_history(session, as_of=None, config=cfg)
        latest = latest_data_date(session)
    with TestClient(main.app) as client:
        resp = client.get("/api/regime-history")
    assert resp.status_code == 200
    served = resp.json()
    assert served == expected  # served verbatim from storage (no recompute)
    assert served["points"], "the warm seed has at least one stored run"
    # every point carries a stored label + numeric score
    valid_labels = set(cfg.regime.labels)
    for p in served["points"]:
        assert p["label"] in valid_labels
        assert isinstance(p["score"], (int, float))
        assert p["date"] <= latest.isoformat()


def test_api_regime_history_as_of_bounds_points(loaded_engine):
    with Session(loaded_engine) as session:
        earliest, latest = _earliest_and_latest_run_dates(session)
    with TestClient(main.app) as client:
        resp_latest = client.get("/api/regime-history")
        resp_early = client.get("/api/regime-history", params={"as_of": earliest.isoformat()})
    assert resp_latest.status_code == 200 and resp_early.status_code == 200
    latest_points = resp_latest.json()["points"]
    early_points = resp_early.json()["points"]
    # the as-of-earliest series is a non-strict prefix-bounded subset of the latest series
    assert len(early_points) <= len(latest_points)
    assert all(p["date"] <= earliest.isoformat() for p in early_points)
    # and the earliest as-of has at least the earliest run
    assert early_points[0]["date"] == earliest.isoformat()


def test_api_regime_history_and_indexes_agree_on_asof(loaded_engine):
    """Both surfaces resolve the SAME as-of date for the same ?as_of= input (one resolution path)."""
    with Session(loaded_engine) as session:
        earliest, _latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
    with TestClient(main.app) as client:
        rh = client.get("/api/regime-history", params={"as_of": d}).json()
        ix = client.get("/api/indexes", params={"as_of": d}).json()
    assert rh["asof_date"] == ix["asof_date"]
