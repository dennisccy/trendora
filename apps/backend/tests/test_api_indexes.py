"""API tests for GET /api/indexes and GET /api/regime-history (J-44 + J-45 / Capability 37).

Served-from-storage read paths over the real committed seed:
  - /api/indexes serves config-listed normalized-% series rebased to the range start, with each legend
    symbol that HAS committed bars present (DIA's one-shot seed is now committed — iter-8 J-44 leg — so
    it renders; a bar-less legend symbol stays honestly omitted, proven in test_indexes.py); unknown
    range -> 422; the series equals the engine output (no recompute drift); as-of bounds the series.
  - /api/regime-history serves the stored per-run label/score verbatim, bounded to the resolved as-of.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

import main
from app.config import load_config
from app.engine import indexes as indexes_module
from app.engine.indexes import compute_index_series
from app.engine.prices import latest_data_date
from app.engine.regime_history import get_regime_history
from app.engine.scanner import resolve_as_of_date
from app.models import IndexSeriesCache


def _earliest_and_latest_run_dates(session):
    from app.models import ScannerRun
    from sqlmodel import select

    dates = sorted(d for d in session.exec(select(ScannerRun.asof_date)).all())
    return dates[0], dates[-1]


def test_api_indexes_equals_engine_and_includes_committed_dia(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        expected = compute_index_series(session, as_of=None, range_key=None, config=cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes")
    assert resp.status_code == 200
    served = resp.json()
    assert served == expected  # no recompute drift — served value == engine value

    symbols = [s["symbol"] for s in served["series"]]
    # the config lists SPY/QQQ/IWM/RSP/DIA; DIA's one-shot seed is now committed (iter-8) -> it renders.
    assert "DIA" in symbols  # the J-44 DIA legend leg, now data-backed
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


def test_api_indexes_includes_vendor_and_first_for_deep_series(loaded_engine):
    """J-14: on the real committed seed, the deep Stooq equity-index benchmark `^SPX` is configured
    (`index_chart.symbols`) and loaded -- its served `vendor`/`first` byte-match `meta.json`. The
    pre-existing SPY ETF line carries the additive keys too, honestly `vendor: None` (no manifest
    vendor record for it)."""
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes")
    assert resp.status_code == 200
    series = {s["symbol"]: s for s in resp.json()["series"]}
    assert "^SPX" in series
    assert series["^SPX"]["vendor"] == "Stooq"
    assert series["^SPX"]["first"] == "1996-01-02"
    assert "vendor" in series["SPY"] and "first" in series["SPY"]
    assert series["SPY"]["vendor"] is None


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


# --- J-49: ?full=true clamp-optional serving over the API (warm seed) -----------------------------
# The new optional `full` query param widens the SERVED window to all stored bars/runs through the
# latest date (display-only dashboard context) while still echoing the resolved as-of. Default (param
# absent) is byte-identical to today, and the overlapping <= D portion is value-identical between modes.


def test_api_indexes_full_param_default_is_byte_identical(loaded_engine):
    """`?full=false` (and the absent param) serve EXACTLY today's clamped payload — regression pin."""
    with Session(loaded_engine) as session:
        earliest, _latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
    with TestClient(main.app) as client:
        absent = client.get("/api/indexes", params={"as_of": d}).json()
        explicit_false = client.get("/api/indexes", params={"as_of": d, "full": "false"}).json()
    assert absent == explicit_false
    # clamped: no bar dated after the historical as-of
    for s in absent["series"]:
        assert all(p["date"] <= absent["asof_date"] for p in s["points"])


def test_api_indexes_full_param_serves_through_latest_and_echoes_asof(loaded_engine):
    """`?full=true` at a historical as-of serves bars dated AFTER D (display-only context) through the
    latest stored date while still echoing the resolved as-of D (the client draws the marker from it)."""
    with Session(loaded_engine) as session:
        earliest, latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
    with TestClient(main.app) as client:
        clamped = client.get("/api/indexes", params={"as_of": d, "range": "all"}).json()
        full = client.get("/api/indexes", params={"as_of": d, "range": "all", "full": "true"}).json()

    # both echo the SAME resolved as-of (the marker position is unchanged by full mode)
    assert full["asof_date"] == clamped["asof_date"] == earliest.isoformat()
    # full mode renders bars AFTER the as-of (the clamped mode does not)
    full_max = max(p["date"] for s in full["series"] for p in s["points"])
    clamped_max = max(p["date"] for s in clamped["series"] for p in s["points"])
    assert full_max > clamped_max  # the post-as-of context is present only in full mode
    assert full_max == latest.isoformat()  # ...through the latest stored date
    # value identity on the overlapping <= D range (no second compute path). A symbol whose FIRST
    # bar is after the (early) as-of is honestly omitted from the clamped series (zero bars <= D) yet
    # still appears in full mode (it has bars overall) -- e.g. ^TNX (and, on a wider ingest, SPY) at
    # an early as-of. That asymmetry is CORRECT product behavior (the honest omission is pinned by
    # test_indexes.py::test_barless_configured_symbol_omitted_from_series_and_legend). So: assert full
    # is a superset of clamped, then compare the overlap only for symbols present in BOTH modes.
    clamped_by_sym = {s["symbol"]: s["points"] for s in clamped["series"]}
    assert set(clamped_by_sym).issubset({s["symbol"] for s in full["series"]})
    for s in full["series"]:
        if s["symbol"] not in clamped_by_sym:
            continue  # honestly absent pre-first-bar in clamped mode; nothing to overlap-compare
        overlap = [p for p in s["points"] if p["date"] <= clamped["asof_date"]]
        assert overlap == clamped_by_sym[s["symbol"]]


def test_api_indexes_full_param_unknown_range_still_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes", params={"range": "nope", "full": "true"})
    assert resp.status_code == 422


def test_api_regime_history_full_param_default_is_byte_identical(loaded_engine):
    with Session(loaded_engine) as session:
        earliest, _latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
    with TestClient(main.app) as client:
        absent = client.get("/api/regime-history", params={"as_of": d}).json()
        explicit_false = client.get("/api/regime-history", params={"as_of": d, "full": "false"}).json()
    assert absent == explicit_false
    assert all(p["date"] <= absent["asof_date"] for p in absent["points"])


def test_api_regime_history_full_param_serves_through_latest(loaded_engine):
    with Session(loaded_engine) as session:
        earliest, latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
    with TestClient(main.app) as client:
        clamped = client.get("/api/regime-history", params={"as_of": d}).json()
        full = client.get("/api/regime-history", params={"as_of": d, "full": "true"}).json()
    # the resolved as-of echo is unchanged by full mode
    assert full["asof_date"] == clamped["asof_date"] == earliest.isoformat()
    # full mode includes runs dated after the as-of, through the latest run
    assert len(full["points"]) >= len(clamped["points"])
    assert full["points"][-1]["date"] == latest.isoformat()
    # value identity on the overlapping <= D range (verbatim stored values, no recompute)
    overlap = [p for p in full["points"] if p["date"] <= clamped["asof_date"]]
    assert overlap == clamped["points"]


# --- ops-hardening iter-13 (J-06): GET /api/indexes' SINGLE unparameterized default hot key
# (no/default range, full=True, no as_of) is served from IndexSeriesCache; every other combination
# stays on the pre-existing, unchanged, uncached compute_index_series path. -------------------------


def test_api_indexes_hot_key_full_true_served_from_cache_and_matches_engine(loaded_engine):
    """The hot key is byte-identical to a fresh, direct `compute_index_series` call on the same DB
    state (AG-3), and persists exactly one `IndexSeriesCache` row for the current dataset-version key."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        expected = compute_index_series(
            session, as_of=None, range_key=cfg.index_chart.default_range, config=cfg, full=True
        )
    with TestClient(main.app) as client:
        resp = client.get("/api/indexes", params={"full": "true"})
    assert resp.status_code == 200
    assert resp.json() == expected

    with Session(loaded_engine) as session:
        rows = session.exec(
            select(IndexSeriesCache).where(
                IndexSeriesCache.range_key == cfg.index_chart.default_range,
                IndexSeriesCache.full == True,  # noqa: E712
            )
        ).all()
    assert len(rows) == 1


def test_api_indexes_hot_key_second_request_hits_cache_without_recompute(loaded_engine, monkeypatch):
    with TestClient(main.app) as client:
        first = client.get("/api/indexes", params={"full": "true"}).json()

    calls = {"n": 0}
    real = indexes_module.compute_index_series

    def _counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(indexes_module, "compute_index_series", _counting)
    with TestClient(main.app) as client:
        second = client.get("/api/indexes", params={"full": "true"}).json()
    assert calls["n"] == 0, "the second hot-key request must serve from IndexSeriesCache, not recompute"
    assert second["series"] == first["series"]
    assert second["range"] == first["range"]
    assert second["ranges"] == first["ranges"]


def test_api_indexes_non_hot_key_bypasses_cache_and_stays_byte_identical(loaded_engine):
    """An explicit non-default range OR an explicit historical as_of never touches `IndexSeriesCache` --
    byte-identical to the unchanged, uncached `compute_index_series` output for the same inputs (TC-6),
    and neither request writes a new cache row."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        earliest, _latest = _earliest_and_latest_run_dates(session)
        d = earliest.isoformat()
        expected_range = compute_index_series(session, as_of=None, range_key="3M", config=cfg, full=True)
        expected_asof = compute_index_series(
            session, as_of=d, range_key=cfg.index_chart.default_range, config=cfg, full=True
        )
        rows_before = session.exec(select(IndexSeriesCache)).all()
    with TestClient(main.app) as client:
        by_range = client.get("/api/indexes", params={"range": "3M", "full": "true"}).json()
        by_asof = client.get("/api/indexes", params={"as_of": d, "full": "true"}).json()
    assert by_range == expected_range
    assert by_asof == expected_asof

    with Session(loaded_engine) as session:
        rows_after = session.exec(select(IndexSeriesCache)).all()
    assert len(rows_after) == len(rows_before)  # neither non-hot-key request wrote a cache row
