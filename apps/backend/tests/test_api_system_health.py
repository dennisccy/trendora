"""GET /api/system-health — the forward-tested evidence endpoint (iter-6, J-09 + J-10 at API level).

The app lifespan now also runs `backfill_forward_returns` on startup, so by the time a `TestClient`
context opens the shared `loaded_engine` has the walk-forward snapshots + their forward_returns
persisted. These tests prove: the payload carries by-bucket (A-E) / by-setup / by-regime breakdowns,
excess vs SPY & QQQ, and the control-group cohorts — each with a sample size `n` and a survivorship
label — for a default and a non-default horizon; an out-of-range horizon is 422; no price data is 503;
and the iter-1..iter-5 endpoints (J-01..J-08) are unaffected by the new lifespan wiring.

This is the iteration's one heavy integration boot (the first TestClient pays the walk-forward backfill
once; later contexts reuse the populated DB).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date

_GROUP_KEYS = {"mean_return", "n"}


def test_system_health_default_horizon_full_payload(loaded_engine):
    """J-09 + J-10 at the API level: the default-horizon payload carries every breakdown with `n`."""
    cfg = load_config()
    with TestClient(main.app) as client:
        resp = client.get("/api/system-health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["horizon"] == cfg.walk_forward.default_horizon
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert "survivorship" in data["survivorship_bias"].lower()
    assert data["n_runs"] >= 1

    # by-bucket A..E — each row numeric-or-null with n (J-09)
    buckets = [r["bucket"] for r in data["by_bucket"]]
    assert buckets == ["A", "B", "C", "D", "E"]
    assert all(_GROUP_KEYS <= set(r) for r in data["by_bucket"])
    assert any(r["n"] > 0 and isinstance(r["mean_return"], (int, float)) for r in data["by_bucket"])

    # by-setup + by-regime each render numbers with n (J-09)
    assert data["by_setup"] and all(_GROUP_KEYS <= set(r) and "setup" in r for r in data["by_setup"])
    assert data["by_regime"] and all(_GROUP_KEYS <= set(r) and "regime" in r for r in data["by_regime"])

    # excess vs SPY and QQQ render numbers (J-09)
    assert data["excess"]["vs_spy"]["benchmark"] == cfg.etfs.index[0]
    assert data["excess"]["vs_qqq"]["benchmark"] == cfg.etfs.index[1]
    assert isinstance(data["excess"]["vs_spy"]["mean_excess"], (int, float))
    assert isinstance(data["excess"]["vs_spy"]["n"], int)

    # control-group cohorts: top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF, each numeric+n (J-10)
    cohorts = {c["key"]: c for c in data["control_group"]}
    assert set(cohorts) == {"top_ranked", "random_same_sector", "spy", "qqq", "sector_etf"}
    for cohort in cohorts.values():
        assert "label" in cohort and _GROUP_KEYS <= set(cohort)
    assert cohorts["top_ranked"]["n"] > 0
    assert isinstance(cohorts["top_ranked"]["mean_return"], (int, float))


def test_system_health_by_vcp_breakdown_present(loaded_engine):
    """J-16 at the API level: the payload carries a VCP-vs-non-VCP forward-return breakdown — both
    cohorts labelled, each with mean_return + n (None/NA when a cohort is empty), derived from the
    stored `is_vcp` flag (never re-detected in the read path)."""
    with TestClient(main.app) as client:
        data = client.get("/api/system-health").json()
    assert "by_vcp" in data
    by_vcp = {r["vcp"]: r for r in data["by_vcp"]}
    assert set(by_vcp) == {"VCP", "non-VCP"}                       # both cohorts always present
    for cohort in by_vcp.values():
        assert _GROUP_KEYS <= set(cohort)                          # each carries mean_return + n
    assert sum(c["n"] for c in by_vcp.values()) > 0                # the seed yields >=1 observation


def test_system_health_by_new_pattern_breakdowns_present(loaded_engine):
    """J-28 at the API level: the payload carries a pattern-vs-non-pattern forward-return breakdown for
    EACH new detected pattern — both cohorts labelled, each with mean_return + n — derived from the
    stored `is_<name>` flag (never re-detected in the read path)."""
    with TestClient(main.app) as client:
        data = client.get("/api/system-health").json()
    for key, flagged_label, non_label in [
        ("by_pullback_to_rising_dma", "Pullback-to-DMA", "non-Pullback"),
        ("by_flat_base_breakout", "Flat-base", "non-Flat-base"),
    ]:
        assert key in data
        cohorts = {r[key.removeprefix("by_")]: r for r in data[key]}
        assert set(cohorts) == {flagged_label, non_label}         # both cohorts always present
        for cohort in cohorts.values():
            assert _GROUP_KEYS <= set(cohort)                      # each carries mean_return + n
        assert sum(c["n"] for c in cohorts.values()) > 0           # the seed yields >=1 observation


def test_system_health_carries_attribution(loaded_engine):
    """J-19 at the API level: the served payload carries the four attribution slices for the horizon —
    per-stock contributors / detractors (named tickers + realized return + n + sector), by-sector,
    by-rank-band (the config bands), and a distribution panel (mean / median / % positive / dispersion,
    with n). The distribution mean equals the existing `overall` mean (read-only consistency)."""
    cfg = load_config()
    band_labels = [b.label for b in cfg.walk_forward.attribution.rank_bands]
    with TestClient(main.app) as client:
        data = client.get("/api/system-health").json()

    attr = data["attribution"]
    assert {"per_stock", "by_sector", "by_rank_band", "distribution"} <= set(attr)

    dist = attr["distribution"]
    assert {"mean_return", "median", "pct_positive", "dispersion", "n"} == set(dist)
    assert dist["mean_return"] == pytest.approx(data["overall"]["mean_return"])  # read-only consistency
    assert dist["n"] == data["overall"]["n"]

    assert attr["per_stock"]["contributors"], "expected >=1 contributor on the seed"
    top = attr["per_stock"]["contributors"][0]
    assert {"ticker", "mean_return", "n", "sector"} <= set(top)
    assert isinstance(top["ticker"], str) and isinstance(top["mean_return"], (int, float))
    assert len(attr["per_stock"]["contributors"]) <= cfg.walk_forward.attribution.top_contributors_k

    assert [r["rank_band"] for r in attr["by_rank_band"]] == band_labels  # config bands, complete
    # consistency: by-sector and by-rank-band sample sizes each sum to overall.n
    assert sum(r["n"] for r in attr["by_sector"]) == data["overall"]["n"]
    assert sum(r["n"] for r in attr["by_rank_band"]) == data["overall"]["n"]


def test_system_health_both_regimes_present(loaded_engine):
    """The by-regime breakdown carries BOTH a Risk-on and a Risk-off entry (the seeded walk-forward
    spans both regimes) — neither fabricated, both derived from real snapshots."""
    with TestClient(main.app) as client:
        data = client.get("/api/system-health").json()
    regimes = {r["regime"] for r in data["by_regime"]}
    assert "Risk-on" in regimes
    assert "Risk-off" in regimes


def test_system_health_non_default_horizon_changes_payload(loaded_engine):
    """A non-default horizon is served and reported; the figures are the aggregation at THAT horizon."""
    with TestClient(main.app) as client:
        long_h = client.get("/api/system-health", params={"horizon": 60}).json()
        short_h = client.get("/api/system-health", params={"horizon": 5}).json()
    assert long_h["horizon"] == 60
    assert short_h["horizon"] == 5
    # different horizons generally yield different overall means (different realized windows)
    assert long_h["overall"]["mean_return"] != short_h["overall"]["mean_return"]


def test_system_health_invalid_horizon_422(loaded_engine):
    """An out-of-range horizon is rejected (422) — no fabricated horizon."""
    with TestClient(main.app) as client:
        resp = client.get("/api/system-health", params={"horizon": 7})
    assert resp.status_code == 422


def test_system_health_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 (never a fabricated evidence row). The handler is called directly
    against an empty DB session, leaving the process engine untouched."""
    from app.api.system_health import system_health

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            system_health(horizon=None, session=session)
        assert exc.value.status_code == 503


def test_iter1_to_iter5_endpoints_unaffected_j01_to_j08(loaded_engine):
    """Regression guard (J-01..J-08): the live + run endpoints still serve their canonical shapes after
    the iter-6 lifespan wiring — the walk-forward backfill re-points / mutates none of them."""
    n_universe = len(load_config().universe.symbols)
    with TestClient(main.app) as client:
        runs = client.get("/api/runs")
        dashboard = client.get("/api/dashboard")
        stocks = client.get("/api/stocks")
        sectors = client.get("/api/sectors")
        themes = client.get("/api/themes")

    assert runs.status_code == 200 and len(runs.json()["runs"]) >= 2  # J-08 history intact
    assert dashboard.status_code == 200 and dashboard.json()["regime"]["label"]  # J-01
    assert stocks.status_code == 200 and len(stocks.json()["rows"]) == n_universe  # J-02
    assert sectors.status_code == 200 and sectors.json()["rows"]  # J-04
    assert themes.status_code == 200 and themes.json()["rows"]  # J-03
