"""GET /api/backtest — the per-date forward-test scorecard endpoint (iter-10, J-14 at API level).

The endpoint resolves ?as_of= to its IMMUTABLE stored snapshot via the iter-8 resolver (default =
latest stored run; create-once for a not-yet-stored date; invalid -> explicit 4xx/503), populates that
run's forward returns create-once, and serves the per-date scorecard (cohort return, excess vs
SPY/QQQ/sector, the 5 control cohorts) — each figure with a sample size `n` and honest NA. It serves
the scorecard ONLY; regime/sector/theme/stock values stay single-sourced on their own endpoints.

By the time a TestClient context opens, the shared `loaded_engine` lifespan has run the walk-forward
backfill, so every stored run already has its forward returns (the create-once path is then a no-op).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlmodel import Session, select

import main
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.models import ForwardReturn, ScannerResult


def _runs(client) -> list[dict]:
    return client.get("/api/runs").json()["runs"]


def _oldest_date(client) -> str:
    return min(_runs(client), key=lambda r: r["asof_date"])["asof_date"]


def _by_horizon(card: dict, h: int) -> dict:
    return next(row for row in card["scorecard"]["by_horizon"] if row["horizon"] == h)


def test_backtest_default_resolves_latest_and_is_all_na(loaded_engine):
    """No ?as_of= -> the latest stored run (is_latest True). The latest seed-date run has zero
    post-snapshot bars, so every horizon is honest NA (cohort mean null, n 0) — never fabricated."""
    cfg = load_config()
    with TestClient(main.app) as client:
        runs = _runs(client)
        latest_date = max(r["asof_date"] for r in runs)
        resp = client.get("/api/backtest")
    assert resp.status_code == 200
    data = resp.json()

    assert data["asof_date"] == latest_date
    assert data["is_latest"] is True
    assert data["horizons"] == list(cfg.walk_forward.horizons)
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert "survivorship" in data["survivorship_bias"].lower()
    # latest run -> no post-bars -> all-NA (no fabricated number)
    for row in data["scorecard"]["by_horizon"]:
        assert row["cohort"]["n"] == 0 and row["cohort"]["mean_return"] is None


def test_backtest_historical_full_window_is_numeric_with_n(loaded_engine):
    """A genuinely historical date (the oldest run, >=60 post-bars) renders a NUMERIC per-horizon
    scorecard: cohort return + excess vs SPY/QQQ/sector + the random-same-sector control, each with n."""
    with TestClient(main.app) as client:
        oldest = _oldest_date(client)
        latest_date = max(r["asof_date"] for r in _runs(client))
        assert oldest != latest_date  # genuinely historical
        data = client.get(f"/api/backtest?as_of={oldest}").json()

    assert data["asof_date"] == oldest
    assert data["is_latest"] is False

    h20 = _by_horizon(data, 20)
    assert h20["cohort"]["n"] > 0
    assert isinstance(h20["cohort"]["mean_return"], (int, float))
    cg = {c["key"]: c for c in h20["control_group"]}
    assert set(cg) == {"top_ranked", "random_same_sector", "spy", "qqq", "sector_etf"}
    assert cg["top_ranked"]["n"] > 0 and isinstance(cg["top_ranked"]["mean_return"], (int, float))
    assert cg["random_same_sector"]["n"] > 0
    # excess figures present, each with its cohort sample size and a benchmark label
    for key in ("vs_spy", "vs_qqq", "vs_sector"):
        assert "mean_excess" in h20["excess"][key]
        assert h20["excess"][key]["n"] == h20["cohort"]["n"]
        assert h20["excess"][key]["benchmark"]


def test_backtest_historical_carries_per_horizon_attribution(loaded_engine):
    """J-19 per-date at the API level: a historical date's scorecard carries an `attribution` block
    inside each by_horizon entry — named contributors / detractors (ticker + realized return + n +
    sector), by-sector, by-rank-band (the config bands), and a distribution panel — each derived from
    the stored observations (no recomputed return)."""
    cfg = load_config()
    band_labels = [b.label for b in cfg.walk_forward.attribution.rank_bands]
    with TestClient(main.app) as client:
        oldest = _oldest_date(client)
        data = client.get(f"/api/backtest?as_of={oldest}").json()
    h20 = _by_horizon(data, 20)
    attr = h20["attribution"]
    assert {"per_stock", "by_sector", "by_rank_band", "distribution"} <= set(attr)
    assert attr["distribution"]["n"] > 0
    assert isinstance(attr["distribution"]["mean_return"], (int, float))
    assert [r["rank_band"] for r in attr["by_rank_band"]] == band_labels
    assert attr["per_stock"]["contributors"]
    top = attr["per_stock"]["contributors"][0]
    assert {"ticker", "mean_return", "n", "sector"} <= set(top)
    assert isinstance(top["ticker"], str)


def test_backtest_keystone_serves_persisted_date_without_recompute(loaded_engine, monkeypatch):
    """KEYSTONE (no recompute, iter-8 lesson — patch-to-raise seam, not value-equality): after a date is
    populated, patch the forward-return math AND the scoring/regime/sector/theme engines to RAISE, then
    assert GET /api/backtest?as_of=D STILL serves the scorecard from the stored rows."""
    with TestClient(main.app) as client:
        oldest = _oldest_date(client)
        client.get(f"/api/backtest?as_of={oldest}")  # ensure the date is fully populated (create-once)

        def boom(*args, **kwargs):
            raise AssertionError("a live engine must not run for an already-populated as-of date")

        monkeypatch.setattr("app.engine.forward_testing.forward_return", boom)
        for name in ("score_stocks", "score_regime", "score_sectors", "score_themes"):
            monkeypatch.setattr(f"app.engine.scanner.{name}", boom)

        resp = client.get(f"/api/backtest?as_of={oldest}")
    assert resp.status_code == 200
    assert isinstance(_by_horizon(resp.json(), 20)["cohort"]["mean_return"], (int, float))


def test_backtest_create_once_inserts_nothing_and_mutates_no_snapshot(loaded_engine):
    """Create-once + immutable: a 2nd view of the same date INSERTs ZERO new forward_returns and performs
    NO UPDATE on the stored scanner_results (the run's result fingerprint is byte-identical)."""
    with TestClient(main.app) as client:
        oldest = _oldest_date(client)
        run_id = next(r["run_id"] for r in _runs(client) if r["asof_date"] == oldest)
        client.get(f"/api/backtest?as_of={oldest}")  # first view (already populated by lifespan)

        with Session(loaded_engine) as session:
            fr_before = session.scalar(
                select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == run_id)
            )
            results_before = [
                (r.ticker, r.rank, r.leadership_bucket, r.record_json)
                for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == run_id)).all()
            ]

        client.get(f"/api/backtest?as_of={oldest}")  # second view

        with Session(loaded_engine) as session:
            fr_after = session.scalar(
                select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == run_id)
            )
            results_after = [
                (r.ticker, r.rank, r.leadership_bucket, r.record_json)
                for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == run_id)).all()
            ]

    assert fr_after == fr_before          # no new forward_returns inserted on the 2nd view
    assert results_after == results_before  # the immutable snapshot was NOT mutated


def test_backtest_invalid_asof_is_explicit_4xx_never_fabricated(loaded_engine):
    """Invalid as-of -> explicit 4xx via the iter-8 _STATUS_BY_KIND map (never a fabricated scorecard):
    future -> 400, before history -> 400, unparseable -> 422."""
    with TestClient(main.app) as client:
        assert client.get("/api/backtest?as_of=2999-01-01").status_code == 400   # future
        assert client.get("/api/backtest?as_of=1900-01-01").status_code == 400   # before history
        assert client.get("/api/backtest?as_of=not-a-date").status_code == 422   # unparseable


def test_backtest_503_when_no_price_data(tmp_path):
    """No price data at all -> explicit 503 (never a fabricated scorecard). The handler is called
    directly against an empty DB session, leaving the process engine untouched."""
    from app.api.backtest import backtest

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            backtest(as_of=None, session=session)
        assert exc.value.status_code == 503


def test_backtest_does_not_reserve_regime_or_stock_values(loaded_engine):
    """The endpoint serves the scorecard ONLY — it does not re-serve regime/sector/theme/stock values
    (those stay single-sourced on their own endpoints). The payload's top-level keys are exactly the
    scorecard contract."""
    with TestClient(main.app) as client:
        data = client.get("/api/backtest").json()
    assert set(data) == {"asof_date", "is_latest", "min_sample", "horizons", "survivorship_bias", "scorecard"}
