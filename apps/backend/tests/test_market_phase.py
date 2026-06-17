"""Unit + integration tests for the Market Phase & Severity layer (iter-29 goal mode, J-87 + J-88).

Covers the anti-goal-bearing behaviors of `app.engine.market_phase`:
  - **No-lookahead tail-invariance** (critical): removing bars dated > D never changes D's phase /
    severity / filtered P(bear).
  - **Determinism:** fixed config params + fixed bars/runs -> byte-identical severity + filtered P(bear)
    (the filter is NEVER EM-fit at serve time).
  - **Filter causality:** the FILTERED P(bear) at D is a function of observations <= D only; a later
    observation never changes a past date's filtered value.
  - **Config validation:** severity weights rejected at load if they don't sum ~1.0 / are incomplete; a
    malformed transition matrix or missing emission param is rejected at load.
  - **Cache correctness:** computed once per resolved-as-of, served from cache, refreshes on a
    dataset_version change; cached == uncached byte-for-byte.
  - **2022-bear reproduction:** a 2022-window as-of -> Bear / high severity / P(bear) toward 1; a
    2026 as-of -> Expansion/Recovery / low P(bear).
  - **Single-source / gate invariance:** the panel's regime input equals the stored ScannerRun regime;
    no canonical stock score / setup / Risk-Off gate changes (a Risk-Off date still has ZERO Actionable).
  - **Error / NA cases:** an early window with no stored run -> NA; the API degrades an invalid as-of like
    the sibling endpoints (422/400) and never fabricates a phase/severity/probability.
"""
from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import insert
from sqlmodel import Session, select

import main
from app.config import ConfigError, load_config
from app.db import create_db_and_tables, make_engine
from app.engine.market_phase import (
    PHASE_RECOVERY,
    _filtered_bear_path,
    compute_market_phase,
    market_phase_cached,
)
from app.engine.research import _dataset_version
from app.models import DailyPrice, ForwardReturn, MarketPhaseCache, ScannerResult, ScannerRun

# --------------------------------------------------------------------------------------------------
# Synthetic in-memory scenarios (controllable benchmark bars + stored runs) — fast, deterministic.
# --------------------------------------------------------------------------------------------------
_BASE = date(2024, 1, 1)


def _engine():
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    return engine


def _insert_bars(session, symbol, closes_list, start=_BASE):
    """Insert daily bars for `symbol` with the given ascending closes (high=low=open=close so the
    drawdown/MDD math is unambiguous in the test)."""
    rows = [
        {
            "symbol": symbol, "date": start + timedelta(days=i),
            "open": c, "high": c, "low": c, "close": c, "volume": 1000.0,
        }
        for i, c in enumerate(closes_list)
    ]
    session.execute(insert(DailyPrice.__table__), rows)


def _insert_run(session, d, label, score, breadth_200=None):
    session.add(
        ScannerRun(
            asof_date=d, created_at=datetime(2024, 1, 1, 12, 0, 0),
            provider="seed", benchmark="SPY",
            regime_score=score, regime_label=label, regime_components_json="{}",
            breadth_above_50dma=None, breadth_above_200dma=breadth_200,
            new_high_low_json="{}", candidate_counts_json="{}",
        )
    )


def _small_config():
    """A minimal market_phase/regime_switching config with a SHORT min_history_bars so synthetic windows
    (a few dozen bars) are sufficient. Everything else mirrors the real config shape."""
    cfg = load_config()
    cfg = copy.deepcopy(cfg)
    cfg.market_phase.min_history_bars = 5
    cfg.market_phase.lookback_days = 10000  # never clips the synthetic window
    return cfg


def test_na_when_no_stored_run_before_asof():
    """An as-of with NO stored run <= D yields an honest NA payload — never a fabricated phase/severity/
    probability (anti-goal: No fabricated data)."""
    cfg = _small_config()
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0 + i for i in range(40)])
        # a run dated AFTER the queried as-of must not contribute
        _insert_run(session, _BASE + timedelta(days=30), "Risk-on", 75.0, breadth_200=60.0)
        session.commit()
        result = compute_market_phase(session, _BASE + timedelta(days=5), cfg)
    assert result["available"] is False
    assert result["phase"] is None and result["severity"] is None and result["p_bear"] is None
    assert result["observations"] == []


def test_na_when_insufficient_benchmark_history():
    """A stored run whose benchmark window has fewer than min_history_bars bars <= D yields NA (partial),
    never a fabricated severity."""
    cfg = _small_config()  # min_history_bars = 5
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0, 102.0])  # only 3 bars (< 5)
        _insert_run(session, _BASE + timedelta(days=2), "Risk-on", 75.0, breadth_200=60.0)
        session.commit()
        result = compute_market_phase(session, _BASE + timedelta(days=2), cfg)
    assert result["available"] is False
    assert result["severity"] is None


def test_no_lookahead_tail_invariance():
    """CRITICAL no-lookahead: removing bars dated > D never changes D's phase / severity / filtered
    P(bear). Asserted the way `forward_return` proves tail-invariance — compute at D with the full series,
    then with the post-D bars deleted; both must be byte-identical."""
    cfg = _small_config()
    engine = _engine()
    # a decline then a sharp rally AFTER D — the post-D rally must not leak into D's reading.
    pre = [100.0 - i for i in range(30)]          # 100 -> 71 (a sustained decline up to D)
    post = [71.0 + 5 * i for i in range(20)]       # a strong rally strictly after D
    d = _BASE + timedelta(days=len(pre) - 1)       # D = the last pre-bar's date
    with Session(engine) as session:
        _insert_bars(session, "SPY", pre + post)
        _insert_run(session, d, "Risk-off", 15.0, breadth_200=20.0)
        session.commit()
        with_tail = compute_market_phase(session, d, cfg)
        # delete every bar dated > D and recompute — the result MUST be unchanged
        for bar in session.exec(select(DailyPrice).where(DailyPrice.date > d)).all():
            session.delete(bar)
        session.commit()
        without_tail = compute_market_phase(session, d, cfg)
    assert json.dumps(with_tail) == json.dumps(without_tail)
    assert with_tail["available"] is True


def test_determinism_byte_identical_repeat():
    """Determinism: the SAME config + bars + runs yield a byte-identical severity AND filtered P(bear)
    on a repeated compute (the filter is a closed-form recursion over committed config params — never
    EM-fit at serve time)."""
    cfg = _small_config()
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0 - 0.5 * i for i in range(40)])
        _insert_run(session, _BASE + timedelta(days=20), "Defensive", 35.0, breadth_200=40.0)
        _insert_run(session, _BASE + timedelta(days=39), "Risk-off", 12.0, breadth_200=18.0)
        session.commit()
        d = _BASE + timedelta(days=39)
        first = compute_market_phase(session, d, cfg)
        second = compute_market_phase(session, d, cfg)
    assert json.dumps(first) == json.dumps(second)
    assert first["p_bear"] is not None


def test_filter_causality_past_value_unchanged_by_later_observation():
    """Filter causality: the FILTERED P(bear) at observation k is a function of observations <= k only —
    appending a LATER observation never changes an earlier element of the filtered path."""
    cfg = _small_config()
    obs = [0.9, 0.85, 0.8]
    path_short = _filtered_bear_path(obs, cfg)
    path_long = _filtered_bear_path(obs + [0.1, 0.05], cfg)  # two calm observations appended AFTER
    # the first len(obs) filtered values must be byte-identical (the later obs cannot revise the past)
    assert path_long[: len(obs)] == path_short


def test_filter_high_stress_drives_pbear_up_calm_drives_down():
    """A run of HIGH-stress observations drives the filtered P(bear) toward 1; a subsequent run of CALM
    observations pulls it back down (deterministic, from committed params)."""
    cfg = _small_config()
    high = _filtered_bear_path([0.9, 0.9, 0.9], cfg)
    assert high[-1] > 0.9  # sustained high stress -> P(bear) toward 1
    recovered = _filtered_bear_path([0.9, 0.9, 0.9, 0.1, 0.1, 0.1], cfg)
    assert recovered[-1] < high[-1]  # calm observations pull P(bear) back down
    assert recovered[-1] < 0.5


def test_filtered_path_empty_for_no_observations():
    """No observations -> empty filtered path (the caller maps that to NA, never a fabricated probability)."""
    assert _filtered_bear_path([], _small_config()) == []


def test_observation_disclosure_capped_but_filter_consumes_all():
    """The payload discloses only the most-recent `observation_disclosure_limit` observations, but the
    filter still consumes EVERY observation <= D: `total_observations` is the full count and the served
    p_bear matches a full-history filter over ALL stored runs (the cap is presentation-only)."""
    cfg = _small_config()
    cfg.market_phase.observation_disclosure_limit = 2  # force a tail smaller than the run count
    engine = _engine()
    # 5 stored runs, each with >= min_history_bars (5) bars <= its date: place the first run on day 5 so
    # its window already has 6 bars, then every 10 days.
    dates = [_BASE + timedelta(days=5 + 10 * i) for i in range(5)]
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0 - 0.2 * i for i in range(60)])
        for i, d in enumerate(dates):
            _insert_run(session, d, "Choppy", 50.0 - i, breadth_200=40.0)
        session.commit()
        result = compute_market_phase(session, dates[-1], cfg)
    assert result["total_observations"] == 5  # all 5 stored runs were observed
    assert len(result["observations"]) == 2   # only the latest 2 disclosed
    assert result["observations"][-1]["date"] == dates[-1].isoformat()
    # the served p_bear equals the last disclosed observation's step p_bear (the filter ran over all 5)
    assert result["p_bear"] == result["observations"][-1]["p_bear"]


def test_recovery_override_when_off_trough_while_underwater():
    """The Recovery STATE override: a still-underwater tape that has rebounded >= recovery_min_off_trough
    off its trough reads Recovery (not the deep edge band). A V-shaped path: down to a trough, then a
    partial rebound that stays below the prior peak."""
    cfg = _small_config()
    # peak 100, trough 70 (-30%), then rebound to 85 (still below 100 -> underwater; +21% off the trough)
    down = [100.0 - i for i in range(31)]       # 100 -> 70
    up = [71.0 + i for i in range(15)]          # 71 -> 85 (off-trough rebound, still < 100)
    engine = _engine()
    d = _BASE + timedelta(days=len(down + up) - 1)
    with Session(engine) as session:
        _insert_bars(session, "SPY", down + up)
        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
        session.commit()
        result = compute_market_phase(session, d, cfg)
    assert result["off_trough_pct"] >= cfg.market_phase.recovery_min_off_trough_pct
    assert result["drawdown_pct"] < 0  # still underwater
    assert result["phase"] == PHASE_RECOVERY


def test_components_breakdown_disclosed_and_explainable():
    """The severity carries its named component breakdown (explainable — never a bare number): every
    configured weight key appears with its value + weight + contribution, and the available contributions
    sum to ~severity (the blend is transparent)."""
    cfg = _small_config()
    engine = _engine()
    d = _BASE + timedelta(days=39)
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0 - 0.4 * i for i in range(40)])
        _insert_run(session, d, "Defensive", 35.0, breadth_200=40.0)
        session.commit()
        result = compute_market_phase(session, d, cfg)
    names = {c["name"] for c in result["components"]}
    assert names == set(cfg.market_phase.weights)  # every configured component disclosed
    contribs = [c["contribution"] for c in result["components"] if c["available"]]
    assert abs(sum(contribs) - result["severity"]) < 0.1  # contributions reconstruct the severity


# --------------------------------------------------------------------------------------------------
# Config validation (mirrors regime.weights / regime_switching boot validation).
# --------------------------------------------------------------------------------------------------
def _write_cfg(tmp_path, data):
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def _real_config_dict():
    """The real config.yaml as a plain dict, so a test can mutate ONE section and re-load it."""
    from app.config import DEFAULT_CONFIG_PATH
    return yaml.safe_load(DEFAULT_CONFIG_PATH.read_text())


def test_severity_weights_must_sum_to_one(tmp_path):
    """The severity weights must sum ~1.0 or the config is rejected at load (mirrors regime.weights)."""
    data = _real_config_dict()
    data["market_phase"]["weights"]["drawdown_depth"] = 0.99  # now the set sums far from 1.0
    with pytest.raises(ConfigError, match="market_phase.weights must sum"):
        load_config(_write_cfg(tmp_path, data))


def test_severity_weights_must_be_complete(tmp_path):
    """A missing severity component fails the boot loudly (never a silent default)."""
    data = _real_config_dict()
    del data["market_phase"]["weights"]["vix_gate"]
    with pytest.raises(ConfigError, match="market_phase.weights missing"):
        load_config(_write_cfg(tmp_path, data))


def test_phase_edges_must_cover_zero(tmp_path):
    """The phase edges must cover down to 0 (a coverage gap is rejected at load)."""
    data = _real_config_dict()
    data["market_phase"]["phase_edges"] = [{"min": 70, "label": "Bear"}]  # no edge at 0
    with pytest.raises(ConfigError):
        load_config(_write_cfg(tmp_path, data))


def test_transition_row_must_sum_to_one(tmp_path):
    """A regime-switching transition row that doesn't sum ~1.0 is rejected at load."""
    data = _real_config_dict()
    data["regime_switching"]["transition"]["bear"] = {"bear": 0.5, "risk_on": 0.2}  # sums 0.7
    with pytest.raises(ConfigError, match="transition.*must sum"):
        load_config(_write_cfg(tmp_path, data))


def test_missing_emission_param_rejected(tmp_path):
    """A missing per-state emission param is rejected at load (the filter never EM-fits a default)."""
    data = _real_config_dict()
    del data["regime_switching"]["emissions"]["bear"]
    with pytest.raises(ConfigError, match="emissions missing"):
        load_config(_write_cfg(tmp_path, data))


def test_emission_std_must_be_positive(tmp_path):
    """A non-positive emission std is rejected at load (a Gaussian needs a positive spread)."""
    data = _real_config_dict()
    data["regime_switching"]["emissions"]["bear"]["std"] = 0
    with pytest.raises(ConfigError, match="emission std must be positive"):
        load_config(_write_cfg(tmp_path, data))


# --------------------------------------------------------------------------------------------------
# Seed-backed reproduction + cache + gate invariance (the warm `loaded_engine` fixture).
# --------------------------------------------------------------------------------------------------
def test_2022_bear_reproduction(loaded_engine):
    """A 2022-window as-of reproduces phase=Bear, a high severity reflecting the seed's SPY peak-to-trough
    (~ -24.5%), and P(bear) trending toward 1; a 2026 as-of reads Expansion (low severity, low P(bear))."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        bear = compute_market_phase(session, date(2022, 10, 7), cfg)
        latest = compute_market_phase(session, date(2026, 5, 28), cfg)
    assert bear["available"] is True
    assert bear["phase"] == "Bear"
    assert bear["severity"] >= 70  # in the Bear edge band
    assert bear["drawdown_pct"] <= -20  # the seed's deep 2022 peak-to-trough
    assert bear["p_bear"] is not None and bear["p_bear"] > 0.9  # toward 1

    assert latest["phase"] == "Expansion"
    assert latest["severity"] < 30
    assert latest["p_bear"] is not None and latest["p_bear"] < 0.5  # falls back at the calm latest tape


def test_regime_input_equals_stored_run_regime(loaded_engine):
    """Single source: the panel's regime input is read VERBATIM from the stored ScannerRun — the
    regime_risk component value equals (100 - stored regime_score)/100 for the served-date run."""
    cfg = load_config()
    d = date(2022, 10, 7)
    with Session(loaded_engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == d)).one()
        result = compute_market_phase(session, d, cfg)
    regime_comp = next(c for c in result["components"] if c["name"] == "regime_risk")
    expected = round((100 - run.regime_score) / 100, 4)
    assert regime_comp["value"] == expected


def test_gate_invariance_risk_off_still_zero_actionable(loaded_engine):
    """Gate invariance (J-07): computing the market-phase layer changes NO canonical value — a Risk-Off
    stored run still has ZERO Actionable results after the derivation runs."""
    cfg = load_config()
    d = date(2022, 10, 7)
    with Session(loaded_engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == d)).one()
        assert run.regime_label == "Risk-off"
        compute_market_phase(session, d, cfg)  # run the layer
        results = session.exec(
            select(ScannerResult).where(ScannerResult.run_id == run.id)
        ).all()
    assert sum(1 for r in results if r.setup_status == "Actionable") == 0


def test_cache_byte_identical_and_single_row(loaded_engine):
    """Cache correctness: `market_phase_cached` returns a payload BYTE-IDENTICAL to a fresh
    `compute_market_phase`, served from cache on the second call, with exactly one cache row per as-of."""
    cfg = load_config()
    d = date(2022, 10, 7)
    with Session(loaded_engine) as session:
        fresh = compute_market_phase(session, d, cfg)
        miss = market_phase_cached(session, d, cfg)
        hit = market_phase_cached(session, d, cfg)
        rows = session.exec(
            select(MarketPhaseCache).where(MarketPhaseCache.asof_key == d.isoformat())
        ).all()
    assert json.dumps(fresh) == json.dumps(miss) == json.dumps(hit)
    assert len(rows) == 1


def test_cache_refreshes_on_dataset_version_change(loaded_engine):
    """The cache refreshes when `dataset_version` changes (no stale figure): a stored row keyed to an old
    stamp is pruned and a fresh row written when the stamp changes (a new forward_returns row added)."""
    cfg = load_config()
    d = date(2022, 10, 7)
    with Session(loaded_engine) as session:
        market_phase_cached(session, d, cfg)  # seed the cache under the current stamp
        v_before = _dataset_version(session)
        old_rows = session.exec(
            select(MarketPhaseCache).where(MarketPhaseCache.dataset_version == v_before)
        ).all()
        assert len(old_rows) >= 1
        # change the dataset: add one forward_returns row (bumps the fr-count stamp component)
        any_run = session.exec(select(ScannerRun)).first()
        session.add(ForwardReturn(
            run_id=any_run.id, symbol="ZZZZ", horizon=1, asof_date=any_run.asof_date,
            entry_close=100.0, measured_date=any_run.asof_date + timedelta(days=1),
            realized_return=0.0,
        ))
        session.commit()
        v_after = _dataset_version(session)
        assert v_after != v_before
        market_phase_cached(session, d, cfg)  # re-read under the NEW stamp
        # the old-stamp row for THIS as-of was pruned; a new-stamp row exists
        stale = session.exec(
            select(MarketPhaseCache).where(
                MarketPhaseCache.asof_key == d.isoformat(),
                MarketPhaseCache.dataset_version == v_before,
            )
        ).all()
        fresh = session.exec(
            select(MarketPhaseCache).where(
                MarketPhaseCache.asof_key == d.isoformat(),
                MarketPhaseCache.dataset_version == v_after,
            )
        ).all()
    assert stale == []
    assert len(fresh) == 1


# --------------------------------------------------------------------------------------------------
# API endpoint (GET /api/market-phase) — shape, as-of repoint, error degradation.
# --------------------------------------------------------------------------------------------------
def test_api_default_payload_shape(loaded_engine):
    """The default (latest as-of) payload carries phase + severity + components + p_bear + observations,
    and echoes the resolved asof_date — served verbatim from the cache."""
    with TestClient(main.app) as client:
        resp = client.get("/api/market-phase")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert {"asof_date", "phase", "severity", "p_bear", "components", "observations", "labels"} <= set(data)
    assert isinstance(data["severity"], (int, float))
    assert 0 <= data["p_bear"] <= 1
    # the component breakdown is disclosed (explainable — never a bare number)
    assert len(data["components"]) == 5


def test_api_as_of_repoints_to_2022_bear(loaded_engine):
    """A historical `?as_of=` into the 2022 window re-points the layer to Bear / high severity / high
    P(bear) — the single global as-of (a mode, not a second date state, J-18)."""
    with TestClient(main.app) as client:
        latest = client.get("/api/market-phase").json()
        bear = client.get("/api/market-phase?as_of=2022-10-07").json()
    assert latest["asof_date"] != bear["asof_date"]
    assert bear["phase"] == "Bear" and bear["severity"] >= 70 and bear["p_bear"] > 0.9
    assert latest["phase"] == "Expansion" and latest["p_bear"] < 0.5


def test_api_no_second_date_state(loaded_engine):
    """J-18: the payload echoes only the single resolved as-of — no second/page-local date field."""
    with TestClient(main.app) as client:
        data = client.get("/api/market-phase").json()
    assert "asof_date" in data
    assert not any(k in data for k in ("asof_dates", "date", "is_latest", "second_date"))


def test_api_unparseable_as_of_422(loaded_engine):
    """An unparseable `?as_of=` is rejected 422 (the shared resolver) — never a fabricated window."""
    with TestClient(main.app) as client:
        assert client.get("/api/market-phase?as_of=not-a-date").status_code == 422


def test_api_future_as_of_400(loaded_engine):
    """A future `?as_of=` is rejected 400 — never a fabricated forward phase."""
    with TestClient(main.app) as client:
        assert client.get("/api/market-phase?as_of=2999-01-01").status_code == 400
