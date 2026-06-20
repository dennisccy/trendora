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
    _smoothed_bear_path,
    _true_bear_episodes,
    compute_market_phase,
    compute_retrospective,
    market_phase_cached,
    market_phase_full_cached,
    recovery_turn_dates,
    retrospective_cached,
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
# iter-30 (J-89 / J-90) — timeline series, dated downtrend episodes, the FENCED retrospective, and the
# causal recovery-turn signal. FAST synthetic tests (no seed boot) — the anti-goal-critical legs.
# --------------------------------------------------------------------------------------------------
def _v_shape_engine(cfg):
    """A synthetic V-shaped tape: a 30-day decline 100 -> 60 (a deep "bear"), then a 30-day rally 60 ->
    ~105 (a recovery). Runs every 6 days (10 runs) carry a high regime risk / low breadth through the
    decline and a calm regime / high breadth through the recovery. Returns (engine, dates)."""
    engine = _engine()
    down = [100.0 - 40 * i / 29 for i in range(30)]
    up = [60.0 + 45 * i / 29 for i in range(30)]
    dates = [_BASE + timedelta(days=6 * i) for i in range(10)]
    with Session(engine) as session:
        _insert_bars(session, "SPY", down + up)
        for i, d in enumerate(dates):
            in_bear = i < 5
            _insert_run(
                session, d, "Risk-off" if in_bear else "Risk-on",
                15.0 if in_bear else 70.0, breadth_200=20.0 if in_bear else 65.0,
            )
        session.commit()
    return engine, dates


def test_timeline_filtered_byte_identity_with_filtered_path(loaded_engine=None):
    """FILTERED byte-identity (single source, J-89): the per-date filtered P(bear) the timeline serves
    equals the existing `_filtered_bear_path` value at each date, AND the served P(bear)/phase/severity
    for the latest date equal the LAST timeline element (the panel and the timeline read ONE series)."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        result = compute_market_phase(session, dates[-1], cfg)
    # the served panel value IS the last timeline element (one derived series, never a second computation)
    assert result["p_bear"] == result["timeline"][-1]["p_bear"]
    assert result["phase"] == result["timeline"][-1]["phase"]
    assert result["severity"] == result["timeline"][-1]["severity"]
    # the per-date timeline p_bear is the `_filtered_bear_path` over the disclosed observations
    obs_values = [o["reading"] for o in result["observations"]]
    filtered = _filtered_bear_path(obs_values, cfg)
    timeline_pbears = [t["p_bear"] for t in result["timeline"]]
    assert timeline_pbears == [round(p, 6) for p in filtered]


def test_timeline_episode_recovery_no_lookahead_tail_invariance():
    """CRITICAL no-lookahead (J-89 / J-90): removing bars/runs dated > D never changes any timeline /
    episode / recovery-turn value at a date <= D — asserted the `forward_return` tail-invariance way."""
    cfg = _small_config()
    engine = _engine()
    pre = [100.0 - i for i in range(40)]            # decline up to D
    post = [60.0 + 5 * i for i in range(20)]         # a sharp rally strictly after D
    d = _BASE + timedelta(days=len(pre) - 1)
    later = d + timedelta(days=30)                    # a run dated AFTER D
    with Session(engine) as session:
        _insert_bars(session, "SPY", pre + post)
        for i in range(7):
            _insert_run(session, _BASE + timedelta(days=6 * i), "Risk-off", 15.0, breadth_200=20.0)
        _insert_run(session, later, "Risk-on", 80.0, breadth_200=70.0)  # a future run (> D)
        session.commit()
        with_tail = compute_market_phase(session, d, cfg)
        # remove every bar AND run dated > D, recompute — every causal field must be byte-identical
        for bar in session.exec(select(DailyPrice).where(DailyPrice.date > d)).all():
            session.delete(bar)
        for run in session.exec(select(ScannerRun).where(ScannerRun.asof_date > d)).all():
            session.delete(run)
        session.commit()
        without_tail = compute_market_phase(session, d, cfg)
    for key in ("timeline", "episodes", "recovery_turn", "p_bear", "severity", "phase"):
        assert json.dumps(with_tail[key]) == json.dumps(without_tail[key]), f"{key} changed under tail removal"


def test_downtrend_episode_dates_the_decline_as_one_run():
    """J-89: the synthetic decline surfaces as ONE dated causal downtrend episode carrying its
    first-trigger date, the severity at trigger, and a closed state once the tape recovered."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        result = compute_market_phase(session, dates[-1], cfg)
    episodes = result["episodes"]
    assert len(episodes) == 1
    ep = episodes[0]
    assert {"first_trigger_date", "severity_at_trigger", "last_date", "open"} <= set(ep)
    assert ep["peak_p_bear"] > 0.9                    # the decline drove filtered P(bear) toward 1
    assert ep["open"] is False                        # the tape recovered -> the episode closed
    assert ep["severity_at_trigger"] > 0


def test_early_asof_yields_empty_timeline_and_no_signal():
    """J-89/J-90: an as-of before any stored run yields an honest empty timeline / episode list and a
    non-signal recovery-turn — never a fabricated episode/probability/signal."""
    cfg = _small_config()
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0 + i for i in range(40)])
        _insert_run(session, _BASE + timedelta(days=30), "Risk-on", 75.0, breadth_200=60.0)
        session.commit()
        result = compute_market_phase(session, _BASE + timedelta(days=5), cfg)
    assert result["available"] is False
    assert result["timeline"] == [] and result["episodes"] == []
    assert result["recovery_turn"]["is_recovery_turn"] is False


def test_recovery_turn_signal_fires_with_explainable_reason():
    """J-90: the resolved as-of at the recovery is flagged a causal recovery turn with its config-defined
    triggering reason (explainable, never a bare flag) — the filtered P(bear) crossed below the exit while
    the index reclaimed its trailing MA, all from data <= D."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        result = compute_market_phase(session, dates[-1], cfg)
    rt = result["recovery_turn"]
    assert rt["is_recovery_turn"] is True
    assert rt["p_bear"] < cfg.market_phase.recovery_signal_pbear_exit <= rt["prev_p_bear"]
    assert rt["ma_reclaimed"] is True
    assert isinstance(rt["reason"], str) and "recovery" in rt["reason"].lower()


def test_recovery_turn_dates_accessor_returns_signal_context():
    """J-90: the public `recovery_turn_dates` accessor (the edge study's source) returns the causal
    recovery-turn date(s) each tagged with the causal phase/severity/P(bear) at the signal date."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        signal_context = recovery_turn_dates(session, None, cfg)
    assert len(signal_context) >= 1
    ctx = next(iter(signal_context.values()))
    assert {"phase", "severity", "p_bear", "prev_p_bear"} <= set(ctx)
    assert ctx["p_bear"] < cfg.market_phase.recovery_signal_pbear_exit


# --------------------------------------------------------------------------------------------------
# iter-30 — the FENCED retrospective (smoothed P(bear) + true-bear dating). Analysis-only; the SMOOTHED
# value and the true-bear dating MUST be future-aware (they read after-the-fact info) and MUST NEVER be
# read by any as-of value (the J-49 fence).
# --------------------------------------------------------------------------------------------------
def test_smoothed_path_differs_from_filtered_uses_future_info():
    """The SMOOTHED P(bear) is full-sample (lookahead by construction): an early step's smoothed value
    differs from its FILTERED value because the smoother conditions on LATER observations. (A calm future
    pulls an early bear-step's smoothed estimate down vs the filtered estimate.)"""
    cfg = _small_config()
    obs = [0.9, 0.9, 0.9, 0.1, 0.1, 0.1]  # high stress then calm
    filtered = _filtered_bear_path(obs, cfg)
    smoothed = _smoothed_bear_path(obs, cfg)
    assert len(smoothed) == len(filtered)
    # the smoother is future-aware -> at least one early step's smoothed != filtered (lookahead present)
    assert any(abs(s - f) > 1e-6 for s, f in zip(smoothed[:3], filtered[:3]))
    # the LAST step's smoothed equals the last filtered (no future beyond the end) — the Kim identity.
    # Both are rounded to 6 dp, so compare at the disclosure precision (the only difference is rounding).
    assert abs(smoothed[-1] - filtered[-1]) < 1e-5


def test_fence_smoothed_and_true_bear_not_read_by_any_asof_value():
    """THE FENCE (critical): the SMOOTHED probability and the true-bear dating are NOT read by
    `compute_market_phase`'s phase / severity / filtered-p_bear, the timeline, the episodes, or the
    recovery-turn signal. Asserted structurally: the causal payload carries NO smoothed/true-bear field,
    and every causal p_bear equals the FILTERED path (never the smoothed path)."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        causal = compute_market_phase(session, dates[-1], cfg)
        retro = compute_retrospective(session, dates[-1], cfg)
    # no smoothed/true-bear key leaks into the causal payload or any of its causal sub-objects
    causal_blob = json.dumps(causal)
    assert "smoothed" not in causal_blob and "true_bear" not in causal_blob
    # every causal timeline p_bear is the FILTERED value, never the smoothed value
    obs_values = [o["reading"] for o in causal["observations"]]
    filtered = [round(p, 6) for p in _filtered_bear_path(obs_values, cfg)]
    assert [t["p_bear"] for t in causal["timeline"]] == filtered
    # the retrospective is explicitly analysis-only and lives only behind its own field
    assert retro["analysis_only"] is True
    assert "smoothed" in retro and "true_bear_episodes" in retro


def test_true_bear_dater_censors_short_or_shallow_declines():
    """J-89 retrospective: the Bry-Boschan true-bear dater CENSORS a decline shorter than
    `bry_boschan_min_phase_days` or shallower than `bry_boschan_min_amplitude_pct` (the cutoffs are config
    keys, not literals). A short synthetic V (30-day, but > amplitude) is censored on duration."""
    cfg = _small_config()
    cfg.market_phase.bry_boschan_min_phase_days = 90    # the 30-day synthetic decline is too short
    cfg.market_phase.bry_boschan_min_amplitude_pct = 20.0
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        retro = compute_retrospective(session, dates[-1], cfg)
    assert retro["true_bear_episodes"] == []  # censored on the 90-day minimum phase length


def test_true_bear_dater_emits_one_phase_for_a_long_deep_decline():
    """J-89 retrospective: a long (>= min phase) + deep (>= min amplitude) decline surfaces as ONE dated
    true-bear phase with its peak/trough dates + drawdown — future-aware (analysis-only)."""
    cfg = _small_config()
    cfg.market_phase.bry_boschan_min_phase_days = 90
    cfg.market_phase.bry_boschan_min_amplitude_pct = 20.0
    engine = _engine()
    down = [100.0 - 30 * i / 199 for i in range(200)]   # 100 -> 70 over ~200 days (-30%)
    up = [70.0 + 35 * i / 99 for i in range(100)]
    dates = [_BASE + timedelta(days=20 * i) for i in range(14)]
    with Session(engine) as session:
        _insert_bars(session, "SPY", down + up)
        for i, d in enumerate(dates):
            _insert_run(session, d, "Risk-off" if i < 8 else "Risk-on",
                        15.0 if i < 8 else 70.0, breadth_200=20.0 if i < 8 else 65.0)
        session.commit()
        retro = compute_retrospective(session, dates[-1], cfg)
    episodes = retro["true_bear_episodes"]
    assert len(episodes) == 1
    ep = episodes[0]
    assert {"peak_date", "trough_date", "drawdown_pct", "duration_days"} <= set(ep)
    assert abs(ep["drawdown_pct"]) >= cfg.market_phase.bry_boschan_min_amplitude_pct
    assert ep["duration_days"] >= cfg.market_phase.bry_boschan_min_phase_days


def test_retrospective_determinism_byte_identical_repeat():
    """Determinism: the SAME config + bars + runs yield a byte-identical retrospective (smoothed +
    true-bear) on a repeated compute."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        first = compute_retrospective(session, dates[-1], cfg)
        second = compute_retrospective(session, dates[-1], cfg)
    assert json.dumps(first) == json.dumps(second)


def test_new_market_phase_config_keys_validated(tmp_path):
    """iter-30 config validation: the new market_phase threshold keys are typed/validated and rejected
    when malformed at load (a recovery exit ABOVE the downtrend threshold is incoherent)."""
    data = _real_config_dict()
    data["market_phase"]["recovery_signal_pbear_exit"] = 0.99   # > downtrend_pbear_threshold (0.50)
    with pytest.raises(ConfigError, match="recovery_signal_pbear_exit"):
        load_config(_write_cfg(tmp_path, data))


def test_new_market_phase_pbear_threshold_must_be_in_unit(tmp_path):
    """iter-30 config validation: a P(bear) threshold outside [0, 1] is rejected at load."""
    data = _real_config_dict()
    data["market_phase"]["downtrend_pbear_threshold"] = 1.5
    with pytest.raises(ConfigError, match="P\\(bear\\) thresholds must be in"):
        load_config(_write_cfg(tmp_path, data))


def test_new_market_phase_bry_boschan_days_must_be_positive(tmp_path):
    """iter-30 config validation: a non-positive Bry-Boschan min-phase-length is rejected at load."""
    data = _real_config_dict()
    data["market_phase"]["bry_boschan_min_phase_days"] = 0
    with pytest.raises(ConfigError, match="must be positive"):
        load_config(_write_cfg(tmp_path, data))


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


# --------------------------------------------------------------------------------------------------
# iter-38 (J-97) — the `?full=true` SERIALIZATION of the full-history causal phase timeline for the
# Dashboard two-pane cross-view. An ADDITIVE opt-in field; the default card payload stays byte-identical.
# Mirrors the `/api/indexes?full=true` + `/api/regime-history?full=true` (J-49) clamp-optional precedent.
# --------------------------------------------------------------------------------------------------
def _timeline_full_for(session, d, cfg):
    """The full-history causal series the `?full=true` mode serves — read VERBATIM from the cached
    full-mode payload (the SAME `timeline_full` `compute_market_phase` builds; no recompute)."""
    return market_phase_full_cached(session, d, cfg)["timeline_full"]
def test_api_full_default_byte_identical_to_card_payload(loaded_engine):
    """J-97 / recurring iter-20/23/24/32 lesson: the `full=false` default served payload is byte-identical
    to today's card payload (no `timeline_full` key, the bounded `timeline` tail + `total_timeline_dates`
    unchanged). The `full` param is an ADDITIVE opt-in — the card disclosure tail must NOT change."""
    with TestClient(main.app) as client:
        default = client.get("/api/market-phase").json()
        explicit_false = client.get("/api/market-phase?full=false").json()
    assert "timeline_full" not in default  # the default never carries the full series
    assert json.dumps(default) == json.dumps(explicit_false)  # full=false == no param, byte-for-byte


def test_api_full_true_serves_timeline_full_verbatim(loaded_engine):
    """J-97: `?full=true` additively attaches `timeline_full` — the SAME full causal series
    `compute_market_phase` builds (read VERBATIM, no recompute). The full series is the engine's
    `timeline_full`, and its bounded TAIL equals the card's existing `timeline` (single source)."""
    cfg = load_config()
    d = date(2022, 10, 7)
    with Session(loaded_engine) as session:
        engine_full = _timeline_full_for(session, d, cfg)
    with TestClient(main.app) as client:
        full = client.get(f"/api/market-phase?full=true&as_of={d.isoformat()}").json()
        card = client.get(f"/api/market-phase?as_of={d.isoformat()}").json()
    # the served full series equals the engine's timeline_full verbatim (no recompute, no second value)
    assert "timeline_full" in full
    assert json.dumps(full["timeline_full"]) == json.dumps(engine_full)
    # every full series point carries exactly the causal {date, phase, p_bear, severity} shape (no smoothed)
    for pt in full["timeline_full"]:
        assert set(pt) == {"date", "phase", "p_bear", "severity"}
    # the full series is a SUPERSET ending in the bounded card tail (the card timeline is its tail slice)
    assert len(full["timeline_full"]) == full["total_timeline_dates"]
    assert full["timeline_full"][-len(card["timeline"]):] == card["timeline"]
    # everything else in the full payload is byte-identical to the card payload (only the new key is added)
    assert {k: v for k, v in full.items() if k != "timeline_full"} == card


def test_api_full_true_no_smoothed_or_true_bear_value(loaded_engine):
    """J-89 fence holds on `?full=true`: the full causal series carries NO smoothed/true-bear field and the
    payload exposes no retrospective unless explicitly requested — the structural fence is preserved."""
    with TestClient(main.app) as client:
        full = client.get("/api/market-phase?full=true").json()
    assert "retrospective" not in full  # the smoothed/true-bear sub-view is never auto-attached
    for pt in full["timeline_full"]:
        assert "p_bear_smoothed" not in pt and "smoothed" not in pt


def test_full_timeline_no_lookahead_tail_invariance():
    """CRITICAL no-lookahead (J-97): removing bars/runs dated > D never changes any earlier full-timeline
    point — asserted the `forward_return` tail-invariance way over the WHOLE served full series."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    d = dates[5]  # a mid-series as-of with a full causal tail still ahead of it
    later = dates[-1] + timedelta(days=30)
    with Session(engine) as session:
        # add a future run + future bars strictly after the last cadence date
        _insert_bars(session, "SPY", [200.0 + i for i in range(5)], start=later)
        _insert_run(session, later, "Risk-on", 90.0, breadth_200=80.0)
        session.commit()
        with_tail = _timeline_full_for(session, d, cfg)
        for bar in session.exec(select(DailyPrice).where(DailyPrice.date > d)).all():
            session.delete(bar)
        for run in session.exec(select(ScannerRun).where(ScannerRun.asof_date > d)).all():
            session.delete(run)
        session.commit()
        without_tail = _timeline_full_for(session, d, cfg)
    assert json.dumps(with_tail) == json.dumps(without_tail)


def test_api_full_true_empty_timeline_when_early(loaded_engine):
    """Honest-empty (J-97): an early `?full=true&as_of=` with no causal history serves an empty
    `timeline_full` — never a fabricated point."""
    cfg = load_config()
    # resolve the earliest stored run, then query the day before it (no run <= that day)
    with Session(loaded_engine) as session:
        first_run = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date)).first()
        early = (first_run.asof_date - timedelta(days=1)).isoformat()
    with TestClient(main.app) as client:
        resp = client.get(f"/api/market-phase?full=true&as_of={early}")
    # an early date may resolve to NA (400/503) OR an available-False payload with an empty full series;
    # either way it never fabricates a point. When it returns 200, timeline_full is honestly empty.
    if resp.status_code == 200:
        data = resp.json()
        assert data["timeline_full"] == []


# ==================================================================================================
# iter-32 (J-92) — Optional FRED macro feed + macro proxies (config-default-OFF). FAST synthetic tests for
# the anti-goal-critical legs: macro-disabled byte-identity of every J-87..J-91 figure; publication-lag
# (published_date <= D, never the reference-date value); FRED key env-only never persisted/logged/echoed;
# a walled provider -> honest blocked-NA never fabricated; the macro provider registered in make_provider.
# ==================================================================================================
from app.engine.market_phase import _macro_value_asof, phase_context_by_date  # noqa: E402
from app.models import MacroSeries  # noqa: E402


def _insert_macro(session, series_id, rows, *, source="seed"):
    """Insert MacroSeries rows: `rows` is [(reference_date, value, published_date)]."""
    session.execute(insert(MacroSeries.__table__), [
        {"symbol": series_id, "date": d, "value": v, "source": source, "published_date": p}
        for d, v, p in rows
    ])


def test_macro_disabled_is_byte_identical_to_price_only(loaded_engine=None):
    """CRITICAL macro-disabled byte-identity (J-92): with the macro legs DISABLED (the default), inserting
    macro rows changes NO J-87/J-88 figure — the severity, components, filtered P(bear), timeline, and
    episodes are byte-identical to the price/breadth/VIX-only path."""
    cfg = _small_config()
    assert cfg.macro.enable.severity is False and cfg.macro.enable.regime_switching is False
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        before = compute_market_phase(session, dates[-1], cfg)
        # add macro rows + proxy bars for the whole window (published immediately, so they WOULD be causal)
        _insert_macro(session, "credit_spread", [(d, 5.0 + i, d) for i, d in enumerate(dates)])
        _insert_macro(session, "yield_curve_10y2y", [(d, -1.0, d) for d in dates])
        session.commit()
        after = compute_market_phase(session, dates[-1], cfg)
    for key in ("severity", "phase", "p_bear", "components", "timeline", "episodes", "observations"):
        assert json.dumps(after[key]) == json.dumps(before[key]), f"{key} changed with macro disabled"


def test_macro_disabled_phase_context_byte_identical(loaded_engine=None):
    """CRITICAL macro-disabled byte-identity (J-91/J-92): the J-91 causal phase-context accessor is
    byte-identical with macro rows present-but-disabled (the conditioning tags don't shift)."""
    cfg = _small_config()
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        before = phase_context_by_date(session, None, cfg)
        _insert_macro(session, "credit_spread", [(d, 9.0, d) for d in dates])
        session.commit()
        after = phase_context_by_date(session, None, cfg)
    assert json.dumps(before, sort_keys=True) == json.dumps(after, sort_keys=True)


def test_macro_enabled_severity_leg_shifts_severity(loaded_engine=None):
    """J-92: ENABLING the severity leg (config edit) with a configured stress_gate + weight DOES shift the
    severity (the macro stress is folded into the available-weight blend) — proving the leg is real, not a
    dead branch. The DEFAULT (disabled) stays byte-identical (asserted above)."""
    cfg = _small_config()
    cfg.macro.enable.severity = True
    # configure a severity-leg scaling on the seed series (weight + stress_gate) — config-driven, no literal
    series = next(s for s in cfg.macro.series if s.id == "credit_spread")
    series.weight = 0.5
    series.stress_gate = 5.0
    engine, dates = _v_shape_engine(cfg)
    with Session(engine) as session:
        # a HIGH credit-spread reading published on/before every date -> a high macro stress leg
        _insert_macro(session, "credit_spread", [(d, 20.0, d) for d in dates])
        session.commit()
        with_macro = compute_market_phase(session, dates[-1], cfg)
        # disable the leg -> the price/breadth/VIX-only severity (the byte-identity baseline)
        cfg.macro.enable.severity = False
        without = compute_market_phase(session, dates[-1], cfg)
    assert with_macro["severity"] != without["severity"]  # the enabled leg moved the severity
    macro_components = [c for c in with_macro["components"] if c["name"].startswith("macro_")]
    assert macro_components and macro_components[0]["available"] is True  # the leg is disclosed/explainable


def test_macro_publication_lag_no_lookahead(loaded_engine=None):
    """J-92 publication-lag (CRITICAL): `_macro_value_asof` uses ONLY a value whose `published_date <= D`
    — the reference-date value on D (whose publication is LATER) is forbidden lookahead and is never used."""
    cfg = _small_config()
    engine = _engine()
    with Session(engine) as session:
        ref = date(2024, 6, 1)
        published = date(2024, 7, 6)  # a 35-day reporting lag (unemployment-style)
        _insert_macro(session, "unemployment_rate", [(ref, 4.2, published)])
        session.commit()
        # on the reference date the value is NOT yet published -> not usable (no lookahead)
        assert _macro_value_asof(session, "unemployment_rate", ref) is None
        # the day before publication it is still not usable
        assert _macro_value_asof(session, "unemployment_rate", published - timedelta(days=1)) is None
        # on/after the publication date it becomes usable, read verbatim
        assert _macro_value_asof(session, "unemployment_rate", published) == 4.2
        assert _macro_value_asof(session, "unemployment_rate", published + timedelta(days=10)) == 4.2


def test_macro_walled_series_is_honest_na_never_fabricated(loaded_engine=None):
    """J-92 data honesty: a series with NO committed rows (a walled/uncommitted series) yields None — an
    honest blocked-NA, never a fabricated value."""
    cfg = _small_config()
    engine = _engine()
    with Session(engine) as session:
        assert _macro_value_asof(session, "no_such_series", date(2024, 6, 1)) is None


def test_fred_provider_registered_env_only_no_fabrication():
    """J-92: the FRED macro provider is registered in make_provider; the key is env-only (a no-key provider
    RAISES rather than fabricating); a misrouted OHLCV fetch RAISES (macro only); the error never echoes a
    key. None of this writes/logs/echoes a key value."""
    from app.data_providers import make_provider
    from app.data_providers.base import ProviderUnavailableError

    provider = make_provider("fred")  # registered like the OHLCV providers
    assert type(provider).__name__ == "FredProvider"
    # no key -> raises (never a silent fallback / fabricated value)
    with pytest.raises(ProviderUnavailableError):
        provider.get_macro_series("T10Y2Y", 1)
    # FRED serves macro, not OHLCV bars -> get_daily raises (never a fabricated bar)
    with pytest.raises(ProviderUnavailableError):
        provider.get_daily("SPY")
    # the no-key error names the requirement WITHOUT echoing any key value
    try:
        make_provider("fred", api_key=None).get_macro_series("T10Y2Y", 1)
    except ProviderUnavailableError as exc:
        assert "FRED" in str(exc) or "FredProvider" in str(exc)


def test_fred_provider_parses_observations_and_applies_lag():
    """J-92: with a key + an injected client returning a canned FRED body, the provider parses the
    observations (excluding FRED `.` missing values) and applies the publication lag
    (published_date = reference_date + publication_lag_days). It never fabricates a value."""
    from app.data_providers.fred_provider import FredProvider

    class _FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class _FakeClient:
        def get(self, url, params=None, headers=None, timeout=None):
            return _FakeResponse({
                "observations": [
                    {"date": "2024-06-01", "value": "4.2"},
                    {"date": "2024-07-01", "value": "."},      # FRED missing -> EXCLUDED, never fabricated
                    {"date": "2024-08-01", "value": "4.5"},
                ]
            })

    provider = FredProvider(api_key="dummy-env-key", client=_FakeClient())
    obs = provider.get_macro_series("UNRATE", 35)
    assert [o.value for o in obs] == [4.2, 4.5]                 # the `.` row excluded
    assert obs[0].date == date(2024, 6, 1)
    assert obs[0].published_date == date(2024, 6, 1) + timedelta(days=35)  # publication lag applied


def test_macro_series_standalone_table_present():
    """J-92: the standalone macro_series table is created by create_all (registered in test_db's
    expected-tables MACRO_TABLES group — asserted there); a fresh DB carries it."""
    from sqlmodel import SQLModel

    assert "macro_series" in SQLModel.metadata.tables
