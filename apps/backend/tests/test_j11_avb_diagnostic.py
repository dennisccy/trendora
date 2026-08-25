"""goal-market-compass iter-14 -- J-11 Stage D readiness, Goal 4: the read-only AVB bridge/volume
diagnostic tests (TC-20..24).

File-scoped, mostly fixture-DB-only (fresh `sqlite://` engine, small synthetic series, following
`test_universe_resolver.py`'s reduced-threshold `Config.model_copy` pattern) -- never
`apps/backend/data/trendora.db`. The one exception is `load_j10_avb_evidence`/
`summarize_pool_bridge_factor_distribution`, which legitimately read the COMMITTED, already-persisted
`runs/goal-market-compass-iter-9/j10-population-evidence.json` evidence file -- a static seed-adjacent
artifact, not the live database.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import load_config
from app.engine import j11_avb_diagnostic as diag
from app.engine.prices import Bar
from app.models import DailyPrice


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(eng)
    return eng


def _small_universe_cfg():
    """A real Config, reduced ONLY on the thresholds this test's tiny synthetic series would otherwise
    fail (mirrors `test_universe_resolver.py`'s `_cfg()` pattern) -- every other value stays the real
    committed config, so `resolve_candidate`/`score_stocks` exercise the REAL rule shape, not a
    reinvented one."""
    cfg = load_config().model_copy(deep=True)
    cfg = cfg.model_copy(update={"indicators": cfg.indicators.model_copy(update={
        "min_history_bars": 30, "vol_avg_period": 20,
    })})
    cfg = cfg.model_copy(update={"universe": cfg.universe.model_copy(update={
        "filters": cfg.universe.filters.model_copy(update={
            "min_price": 1.0, "min_dollar_vol": 1000.0, "adv_window_days": 20, "max_staleness_days": 30,
        })
    })})
    return cfg


def _seed_daily_prices(session: Session, symbol: str, *, n: int, end: date, close_start: float, close_step: float, volume: float) -> None:
    """`n` consecutive daily bars ENDING at `end` (ascending) with a simple deterministic close ramp --
    enough for the reduced-threshold config's gates and windowed indicators to have real (non-NA) values
    without needing hundreds of days."""
    for i in range(n):
        d = end - timedelta(days=n - 1 - i)
        close = close_start + close_step * i
        session.add(DailyPrice(
            symbol=symbol, date=d, open=close, high=close * 1.01, low=close * 0.99, close=close, volume=volume,
        ))
    session.commit()


AVB_TEST_DATES_END = date(2026, 8, 12)


# --- TC-20: bridge factor + calibration pairs reproduce EXACTLY from the persisted J-10 evidence -----


def test_tc20_load_j10_avb_evidence_reproduces_persisted_bridge_factor_and_pairs():
    row = diag.load_j10_avb_evidence()
    assert row["bridge_factor"] == pytest.approx(2.7930001225759193)
    pair_dates = sorted(p["trading_date"] for p in row["pairs"])
    assert pair_dates == ["2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10"]


def test_avb_is_the_unique_material_bridge_factor_outlier_in_the_persisted_pool():
    dist = diag.summarize_pool_bridge_factor_distribution()
    assert dist["avb_is_unique_material_outlier"] is True
    assert diag.AVB_SYMBOL in dist["materially_bridged_symbols"]


def test_load_j10_avb_evidence_raises_on_missing_symbol(tmp_path):
    import json
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({"symbols": [{"symbol": "AAPL", "bridge_factor": 1.0, "pairs": []}]}))
    with pytest.raises(ValueError):
        diag.load_j10_avb_evidence(path)


# --- TC-21: local-convention classification -- from the stored series, never convention alone --------


def test_tc21_classify_local_convention_bridged_raw_when_calibration_ratios_agree():
    bridge_factor = 2.793
    evidence_row = {
        "pairs": [
            {"trading_date": "2026-08-05", "fallback_close": 100 / bridge_factor, "ratio": bridge_factor},
            {"trading_date": "2026-08-06", "fallback_close": 101 / bridge_factor, "ratio": bridge_factor},
            {"trading_date": "2026-08-07", "fallback_close": 102 / bridge_factor, "ratio": bridge_factor},
            {"trading_date": "2026-08-10", "fallback_close": 103 / bridge_factor, "ratio": bridge_factor},
        ]
    }
    # a continuous, unbroken stored series across the whole window -- no anomalous jump anywhere,
    # including at the 08-10 -> 08-11 -> 08-12 recovery boundary.
    stored_series = [
        {"date": "2026-08-04", "close": 99.0, "volume": 1000.0, "close_times_volume": 99000.0},
        {"date": "2026-08-05", "close": 100.0, "volume": 1000.0, "close_times_volume": 100000.0},
        {"date": "2026-08-06", "close": 101.0, "volume": 1000.0, "close_times_volume": 101000.0},
        {"date": "2026-08-07", "close": 102.0, "volume": 1000.0, "close_times_volume": 102000.0},
        {"date": "2026-08-10", "close": 103.0, "volume": 1000.0, "close_times_volume": 103000.0},
        {"date": "2026-08-11", "close": 104.0, "volume": 1000.0, "close_times_volume": 104000.0},
        {"date": "2026-08-12", "close": 105.0, "volume": 1000.0, "close_times_volume": 105000.0},
        {"date": "2026-08-13", "close": 106.0, "volume": 1000.0, "close_times_volume": 106000.0},
    ]
    result = diag.classify_local_convention(stored_series, evidence_row)
    assert result["windows"]["calibration_window"]["classification"] == "bridged+raw"
    assert result["indeterminate"] is False
    assert result["internally_consistent"] is True
    assert result["overall_classification"] == "bridged+raw"


def test_classify_local_convention_detects_a_discontinuity_at_the_recovery_boundary():
    bridge_factor = 2.793
    evidence_row = {
        "pairs": [
            {"trading_date": "2026-08-05", "fallback_close": 100 / bridge_factor, "ratio": bridge_factor},
            {"trading_date": "2026-08-06", "fallback_close": 101 / bridge_factor, "ratio": bridge_factor},
            {"trading_date": "2026-08-07", "fallback_close": 102 / bridge_factor, "ratio": bridge_factor},
            {"trading_date": "2026-08-10", "fallback_close": 103 / bridge_factor, "ratio": bridge_factor},
        ]
    }
    # an ARTIFICIAL scale break exactly at 2026-08-11 -- close jumps from 103 to 400 (the ~2.79x-scale
    # jump a genuine mismatch would show), then continues smoothly from the new (wrong) scale.
    stored_series = [
        {"date": "2026-08-10", "close": 103.0, "volume": 1000.0, "close_times_volume": 103000.0},
        {"date": "2026-08-11", "close": 400.0, "volume": 1000.0, "close_times_volume": 400000.0},
        {"date": "2026-08-12", "close": 404.0, "volume": 1000.0, "close_times_volume": 404000.0},
    ]
    result = diag.classify_local_convention(stored_series, evidence_row)
    assert result["anomalous_jump_count"] >= 1
    assert result["internally_consistent"] is False
    assert result["windows"]["recovered_dates"]["boundary_jumps"]


def test_classify_local_convention_indeterminate_when_calibration_pairs_missing():
    result = diag.classify_local_convention([], {"pairs": []})
    assert result["indeterminate"] is True


# --- TC-22: counterfactual representations A/B/C -- exact formulas, B's volume equals A's -----------


def test_tc22_representations_a_b_c_formulas_and_volume_equality():
    bridge_factor = 2.7930001225759193
    stored_close, stored_volume = 189.61, 500_000.0
    rep = diag.compute_counterfactual_representations(bridge_factor, stored_close, stored_volume)
    assert rep["A"]["close"] == stored_close
    assert rep["A"]["volume"] == stored_volume
    assert rep["B"]["close"] == pytest.approx(stored_close / bridge_factor)
    assert rep["B"]["volume"] == stored_volume  # stated explicitly: volume was never transformed by J-10
    assert rep["volume_a_equals_b"] is True
    assert rep["C"]["volume"] == pytest.approx(stored_volume * bridge_factor)
    assert rep["C"]["close"] == stored_close  # C only changes volume, never close
    assert rep["A"]["close_times_volume"] > rep["B"]["close_times_volume"]  # A > B since bridge_factor > 1


# --- _build_bars_with_transformed_close -- never mutates the input bars, only the targeted dates ------


def test_build_bars_with_transformed_close_only_touches_target_dates():
    bars = [
        Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=100.0, volume=10.0),
        Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=200.0, volume=20.0),
        Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=300.0, volume=30.0),
    ]
    out = diag._build_bars_with_transformed_close(bars, {date(2026, 8, 11), date(2026, 8, 12)}, 2.0)
    assert out[0].close == 100.0  # untouched date, unchanged
    assert out[1].close == 100.0  # 200 / 2.0
    assert out[2].close == 150.0  # 300 / 2.0
    assert out[0].volume == 10.0 and out[1].volume == 20.0 and out[2].volume == 30.0  # volume NEVER touched
    # the original list's own Bar objects are untouched (new tuples returned, never mutated in place --
    # NamedTuples are immutable anyway, but this also proves no accidental aliasing/identity confusion).
    assert bars[1].close == 200.0


# --- TC-23: decision-impact trace through universe_resolver -- fixture DB, reduced thresholds ---------


def test_tc23_trace_universe_resolver_impact_admission_and_adv_shift(engine):
    cfg = _small_universe_cfg()
    bridge_factor = 2.793
    with Session(engine) as session:
        _seed_daily_prices(
            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
            close_start=180.0, close_step=0.5, volume=1_000_000.0,
        )

    with Session(engine) as session:
        impact = diag.trace_universe_resolver_impact(session, cfg, date(2026, 8, 11), bridge_factor)

    assert impact["adv_dollar_a"] is not None and impact["adv_dollar_b"] is not None
    # representation B divides the two most-recent bars' close by bridge_factor -- a LOWER close for
    # those days pulls the trailing-window ADV average DOWN relative to A.
    assert impact["adv_dollar_b"] < impact["adv_dollar_a"]
    assert impact["resolution_a"]["admitted"] is True  # comfortably above the reduced $1,000 floor either way
    assert impact["resolution_b"]["admitted"] is True
    assert impact["admission_changed"] is False


def test_trace_universe_resolver_impact_detects_admission_change_when_b_crosses_the_floor(engine):
    cfg = _small_universe_cfg()
    # a min_dollar_vol floor placed BETWEEN A's and B's ADV -- proves the admission gate genuinely reacts
    # to the counterfactual, not just carries a static "admitted" value through.
    with Session(engine) as session:
        _seed_daily_prices(
            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
            close_start=180.0, close_step=0.0, volume=1_000_000.0,
        )
        session.commit()

    with Session(engine) as session:
        # peek the real ADV values at the reduced config first, to place the floor precisely between them
        preview = diag.trace_universe_resolver_impact(session, cfg, date(2026, 8, 11), 2.793)
    floor = (preview["adv_dollar_a"] + preview["adv_dollar_b"]) / 2
    cfg_with_floor = cfg.model_copy(update={"universe": cfg.universe.model_copy(update={
        "filters": cfg.universe.filters.model_copy(update={"min_dollar_vol": floor})
    })})

    with Session(engine) as session:
        impact = diag.trace_universe_resolver_impact(session, cfg_with_floor, date(2026, 8, 11), 2.793)
    assert impact["resolution_a"]["admitted"] is True
    assert impact["resolution_b"]["admitted"] is False
    assert impact["resolution_b"]["reason"] == "below_adv"
    assert impact["admission_changed"] is True


# --- TC-23 (scoring half): the honest empty state when AVB is not a resolved member -------------------


def test_trace_scoring_and_selection_impact_honest_empty_when_avb_not_resolved(engine):
    """On an otherwise-empty fixture DB (no DailyPrice rows at all), AVB clears no history gate under the
    REAL committed default config -- `score_stocks` resolves an empty membership set, and the trace
    reports the honest `avb_resolved_member: False` state rather than fabricating a score."""
    cfg = load_config()
    with Session(engine) as session:
        impact = diag.trace_scoring_and_selection_impact(session, cfg, date(2026, 8, 11), 2.793)
    assert impact["avb_resolved_member"] is False
    assert "not a point-in-time-resolved universe member" in impact["note"]


# --- TC-24: overall classification -- exactly one of AVB-A/B/C/D, reasoning names the evidence --------


def test_tc24_classify_avb_lands_in_avb_a_with_no_material_signal():
    local_convention = {"indeterminate": False, "internally_consistent": True, "reasoning": "consistent"}
    decision_impact = {
        "2026-08-11": {
            "universe_resolver": {"admission_changed": False},
            "scoring_and_selection": {
                "avb_resolved_member": True, "risk_bucket_a": "E", "risk_bucket_b": "E",
                "setup_status_a": "Avoid", "setup_status_b": "Avoid",
                "eligible_a": False, "eligible_b": False, "other_ticker_percentile_shifts": {},
            },
        }
    }
    result = diag.classify_avb(local_convention, decision_impact)
    assert result["classification"] == "AVB-A"
    assert result["stage_d_ready_per_avb"] is True
    assert result["material_signals"] == []


def test_classify_avb_lands_in_avb_b_when_material_but_internally_consistent():
    local_convention = {"indeterminate": False, "internally_consistent": True, "reasoning": "consistent"}
    decision_impact = {
        "2026-08-11": {
            "universe_resolver": {"admission_changed": False},
            "scoring_and_selection": {
                "avb_resolved_member": True, "risk_bucket_a": "E", "risk_bucket_b": "D",
                "setup_status_a": "Avoid", "setup_status_b": "Avoid",
                "eligible_a": False, "eligible_b": False, "other_ticker_percentile_shifts": {"HAS": {}},
            },
        }
    }
    result = diag.classify_avb(local_convention, decision_impact)
    assert result["classification"] == "AVB-B"
    assert result["stage_d_ready_per_avb"] is True
    assert result["material_signals"]  # names the specific evidence, never a bare label
    assert "Risk bucket changed" in result["material_signals"][0] or any(
        "Risk bucket changed" in s for s in result["material_signals"]
    )


def test_classify_avb_lands_in_avb_c_when_inconsistent_regardless_of_impact():
    local_convention = {"indeterminate": False, "internally_consistent": False, "reasoning": "discontinuity found"}
    result = diag.classify_avb(local_convention, {})
    assert result["classification"] == "AVB-C"
    assert result["stage_d_ready_per_avb"] is False


def test_classify_avb_lands_in_avb_d_when_indeterminate():
    local_convention = {"indeterminate": True, "internally_consistent": False, "reasoning": "insufficient evidence"}
    result = diag.classify_avb(local_convention, {})
    assert result["classification"] == "AVB-D"
    assert result["stage_d_ready_per_avb"] is False


# --- fetch_avb_stored_series -- small fixture read-only column-projected query -------------------------


def test_fetch_avb_stored_series_reads_close_volume_and_product(engine):
    with Session(engine) as session:
        _seed_daily_prices(
            session, diag.AVB_SYMBOL, n=5, end=date(2026, 8, 12),
            close_start=100.0, close_step=1.0, volume=10.0,
        )
    with Session(engine) as session:
        series = diag.fetch_avb_stored_series(session, date(2026, 8, 8), date(2026, 8, 12))
    assert len(series) == 5
    assert series[0]["close"] == 100.0
    assert series[0]["close_times_volume"] == 1000.0
    assert [row["date"] for row in series] == sorted(row["date"] for row in series)
