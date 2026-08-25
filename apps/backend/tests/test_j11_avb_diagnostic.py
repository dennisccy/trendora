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


# --- TC-12/13: counterfactual representations A/B/C -- iter-15 fix: B is genuinely fetched, fails ------
# --- closed when evidence is unavailable, never a stored-volume tautology -----------------------------


def test_tc22_representation_a_and_c_formulas_unchanged():
    bridge_factor = 2.7930001225759193
    stored_close, stored_volume = 189.61, 500_000.0
    rep = diag.compute_counterfactual_representations(bridge_factor, stored_close, stored_volume)
    assert rep["A"]["close"] == stored_close
    assert rep["A"]["volume"] == stored_volume
    assert rep["C"]["volume"] == pytest.approx(stored_volume * bridge_factor)
    assert rep["C"]["close"] == stored_close  # C only changes volume, never close -- unchanged from iter-14


def test_tc12_representation_b_uses_fetched_provider_volume_never_a_stored_volume_copy():
    bridge_factor = 2.7930001225759193
    stored_close, stored_volume = 189.61, 500_000.0
    provider_evidence = {"close": 67.89, "volume": 350_000.0}  # DELIBERATELY != stored_volume
    rep = diag.compute_counterfactual_representations(
        bridge_factor, stored_close, stored_volume, provider_evidence=provider_evidence
    )
    assert rep["evidence_available"] is True
    assert rep["B"]["close"] == 67.89
    assert rep["B"]["volume"] == 350_000.0  # the FETCHED value, never stored_volume (500_000.0)
    # the genuine, non-tautological comparison: two INDEPENDENTLY-sourced values, provably unequal.
    assert rep["volume_a_equals_b"] is False
    # the old arithmetic derivation is still recorded, but ONLY as a documented cross-check field --
    # never as B's own close.
    assert rep["close_b_arithmetic_fallback"] == pytest.approx(stored_close / bridge_factor)
    assert rep["B"]["close"] != rep["close_b_arithmetic_fallback"]


def test_representation_b_can_also_prove_volume_a_equals_b_true_when_fetched_volume_matches():
    bridge_factor = 2.7930001225759193
    stored_close, stored_volume = 189.61, 500_000.0
    provider_evidence = {"close": 67.89, "volume": 500_000.0}  # DELIBERATELY == stored_volume this time
    rep = diag.compute_counterfactual_representations(
        bridge_factor, stored_close, stored_volume, provider_evidence=provider_evidence
    )
    # still a GENUINE comparison of two independently-sourced values -- it happens to agree this time,
    # never true by construction the way iter-14 left it (rep["B"]["volume"] IS the fetched value, not a
    # hardcoded copy of stored_volume).
    assert rep["B"]["volume"] == provider_evidence["volume"]
    assert rep["volume_a_equals_b"] is True


def test_tc13_representation_b_fails_closed_when_provider_evidence_is_unavailable():
    bridge_factor = 2.7930001225759193
    stored_close, stored_volume = 189.61, 500_000.0
    rep = diag.compute_counterfactual_representations(bridge_factor, stored_close, stored_volume, provider_evidence=None)
    assert rep["evidence_available"] is False
    assert rep["B"]["close"] is None
    assert rep["B"]["volume"] is None
    assert rep["B"]["close_times_volume"] is None
    assert rep["volume_a_equals_b"] is None  # cannot be compared -- never assumed True or False
    # the arithmetic value is STILL recorded (documented fallback/cross-check), but never promoted into B.
    assert rep["close_b_arithmetic_fallback"] == pytest.approx(stored_close / bridge_factor)


def test_tc13_representation_b_fails_closed_on_partial_provider_evidence():
    bridge_factor = 2.7930001225759193
    rep = diag.compute_counterfactual_representations(
        bridge_factor, 189.61, 500_000.0, provider_evidence={"close": 67.89, "volume": None}
    )
    assert rep["evidence_available"] is False
    assert rep["B"]["volume"] is None


# --- TC-11/14/15/16: compute_provider_comparison + classify_date_from_provider_comparison ---------------


def test_tc11_compute_provider_comparison_records_every_required_field():
    bridge_factor = 2.7930001225759193
    cmp = diag.compute_provider_comparison(189.61, 1_549_436.0, 67.89, 554_756.0, bridge_factor)
    for key in (
        "stored_close", "stored_volume", "provider_close", "provider_volume", "close_ratio", "volume_ratio",
        "bridge_factor", "expected_inverse_volume_ratio", "stored_dollar_volume", "provider_dollar_volume",
        "bridge_adjusted_compensation_test",
    ):
        assert key in cmp, f"missing {key}"
    assert cmp["close_ratio"] == pytest.approx(189.61 / 67.89)
    assert cmp["volume_ratio"] == pytest.approx(1_549_436.0 / 554_756.0)
    assert cmp["expected_inverse_volume_ratio"] == pytest.approx(1.0 / bridge_factor)
    assert cmp["stored_dollar_volume"] == pytest.approx(189.61 * 1_549_436.0)
    assert cmp["provider_dollar_volume"] == pytest.approx(67.89 * 554_756.0)


def test_tc14_bridged_compensating_is_genuinely_reachable_from_real_evidence_shapes():
    """Price rebased by EXACTLY bridge_factor, volume rebased by EXACTLY 1/bridge_factor -- dollar volume
    conserved. Proves the ONE label iter-14's tautology could never produce is now mechanically reachable."""
    bridge_factor = 2.793
    provider_close, provider_volume = 100.0, 1_000_000.0
    stored_close = provider_close * bridge_factor
    stored_volume = provider_volume / bridge_factor  # the compensating hypothesis, exactly
    cmp = diag.compute_provider_comparison(stored_close, stored_volume, provider_close, provider_volume, bridge_factor)
    assert cmp["bridge_adjusted_compensation_test"]["compensates"] is True
    assert diag.classify_date_from_provider_comparison(cmp) == "bridged+compensating"


def test_tc15_bridged_raw_is_reachable_when_volume_is_untransformed():
    """Price rebased by bridge_factor, volume left EXACTLY on the provider's raw scale -- dollar volume
    inflated by ~bridge_factor, not conserved."""
    bridge_factor = 2.793
    provider_close, provider_volume = 100.0, 1_000_000.0
    stored_close = provider_close * bridge_factor
    stored_volume = provider_volume  # untransformed
    cmp = diag.compute_provider_comparison(stored_close, stored_volume, provider_close, provider_volume, bridge_factor)
    assert cmp["bridge_adjusted_compensation_test"]["matches_raw_volume_dollar_shift"] is True
    assert diag.classify_date_from_provider_comparison(cmp) == "bridged+raw"


def test_raw_plus_raw_is_reachable_when_neither_side_was_rebased():
    bridge_factor = 2.793
    cmp = diag.compute_provider_comparison(100.2, 1_000_500.0, 100.0, 1_000_000.0, bridge_factor)
    assert diag.classify_date_from_provider_comparison(cmp) == "raw+raw"


def test_mixed_indeterminate_when_evidence_matches_no_hypothesis():
    bridge_factor = 2.793
    # close bridged, but volume neither raw (~1) nor compensating (~1/bridge_factor) -- a genuine
    # inconsistency, never silently forced into the nearest label.
    cmp = diag.compute_provider_comparison(279.3, 1_000_000.0, 100.0, 500_000.0, bridge_factor)
    assert diag.classify_date_from_provider_comparison(cmp) == "mixed/indeterminate"


def test_classify_date_from_provider_comparison_fails_closed_on_missing_fields():
    assert diag.classify_date_from_provider_comparison({"close_ratio": None, "volume_ratio": 1.0, "bridge_factor": 2.0, "expected_inverse_volume_ratio": 0.5}) == "mixed/indeterminate"
    assert diag.classify_date_from_provider_comparison({"close_ratio": 1.0, "volume_ratio": 1.0, "bridge_factor": 0, "expected_inverse_volume_ratio": None}) == "mixed/indeterminate"


# --- classify_local_convention_with_volume_evidence -- end-to-end window classification -----------------


def _series_row(iso_date: str, close: float, volume: float) -> dict:
    return {"date": iso_date, "close": close, "volume": volume, "close_times_volume": close * volume}


def test_classify_local_convention_with_volume_evidence_reaches_bridged_compensating_end_to_end():
    bridge_factor = 2.793
    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
    provider_by_date = {}
    stored_series = []
    provider_close = 100.0
    for one_date in diag.CALIBRATION_DATES + diag.RECOVERED_DATES:
        key = one_date.isoformat()
        provider_volume = 1_000_000.0
        stored_close = provider_close * bridge_factor
        stored_volume = provider_volume / bridge_factor  # compensating, exactly, every date
        provider_by_date[key] = {"close": provider_close, "volume": provider_volume}
        stored_series.append(_series_row(key, stored_close, stored_volume))
        provider_close += 0.1  # small drift so dates are distinguishable; ratio math stays exact per-date

    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
    assert result["windows"]["calibration_window"]["classification"] == "bridged+compensating"
    assert result["windows"]["recovered_dates"]["classification"] == "bridged+compensating"
    assert result["indeterminate"] is False
    assert result["internally_consistent"] is True
    assert result["overall_classification"] == "bridged+compensating"


def test_classify_local_convention_with_volume_evidence_reaches_bridged_raw_end_to_end():
    bridge_factor = 2.793
    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
    provider_by_date = {}
    stored_series = []
    provider_close = 100.0
    for one_date in diag.CALIBRATION_DATES + diag.RECOVERED_DATES:
        key = one_date.isoformat()
        provider_volume = 1_000_000.0
        stored_close = provider_close * bridge_factor
        stored_volume = provider_volume  # untransformed, every date
        provider_by_date[key] = {"close": provider_close, "volume": provider_volume}
        stored_series.append(_series_row(key, stored_close, stored_volume))
        provider_close += 0.1

    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
    assert result["windows"]["calibration_window"]["classification"] == "bridged+raw"
    assert result["windows"]["recovered_dates"]["classification"] == "bridged+raw"
    assert result["internally_consistent"] is True
    assert result["overall_classification"] == "bridged+raw"


def test_tc20_classify_local_convention_with_volume_evidence_indeterminate_on_missing_evidence():
    """A date missing from the fetched evidence never falls back to the OLD price-only continuity
    method -- it classifies mixed/indeterminate directly, naming that date's own entry."""
    bridge_factor = 2.793
    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
    stored_series = [
        _series_row(d.isoformat(), 279.3, 358_000.0) for d in diag.CALIBRATION_DATES + diag.RECOVERED_DATES
    ]
    provider_by_date = {
        d.isoformat(): {"close": 100.0, "volume": 358_000.0}
        for d in diag.CALIBRATION_DATES  # RECOVERED_DATES deliberately absent -- insufficient evidence
    }
    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
    assert result["windows"]["recovered_dates"]["classification"] == "mixed/indeterminate"
    missing_entries = [
        r for r in result["windows"]["recovered_dates"]["per_date"] if r["classification"] == "mixed/indeterminate"
    ]
    assert {r["date"] for r in missing_entries} == {d.isoformat() for d in diag.RECOVERED_DATES}
    assert result["indeterminate"] is True


def test_tc19_classify_local_convention_with_volume_evidence_inconsistent_across_windows():
    """The calibration window proves bridged+compensating but the recovered-dates window proves
    bridged+raw -- a genuine, evidence-backed inconsistency (never silently reconciled)."""
    bridge_factor = 2.793
    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
    stored_series = []
    provider_by_date = {}
    for one_date in diag.CALIBRATION_DATES:
        key = one_date.isoformat()
        provider_by_date[key] = {"close": 100.0, "volume": 1_000_000.0}
        stored_series.append(_series_row(key, 100.0 * bridge_factor, 1_000_000.0 / bridge_factor))
    for one_date in diag.RECOVERED_DATES:
        key = one_date.isoformat()
        provider_by_date[key] = {"close": 100.0, "volume": 1_000_000.0}
        stored_series.append(_series_row(key, 100.0 * bridge_factor, 1_000_000.0))  # untransformed here

    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
    assert result["windows"]["calibration_window"]["classification"] == "bridged+compensating"
    assert result["windows"]["recovered_dates"]["classification"] == "bridged+raw"
    assert result["internally_consistent"] is False
    assert result["indeterminate"] is False  # both windows individually determinate, just DISAGREE


def test_tc16_boundary_jumps_are_corroborating_narrative_never_a_classification_override():
    """Even when the legacy continuity check flags a boundary jump, the WINDOW classifications stay
    exactly what the direct fetched comparison proves -- the jump is reported, not substituted."""
    bridge_factor = 2.793
    evidence_row = {"bridge_factor": bridge_factor, "pairs": []}
    provider_by_date = {
        d.isoformat(): {"close": 100.0, "volume": 1_000_000.0}
        for d in diag.CALIBRATION_DATES + diag.RECOVERED_DATES
    }
    stored_series = [
        _series_row(d.isoformat(), 100.0 * bridge_factor, 1_000_000.0 / bridge_factor)
        for d in diag.CALIBRATION_DATES
    ]
    # an EXTRA synthetic row (NOT one of the six evidence dates) with an anomalous close, positioned
    # immediately before 2026-08-11 in the list -- creates a day-over-day "jump" whose to_date is a
    # recovered date (a boundary jump), WITHOUT touching 2026-08-11's OWN stored value, so its direct
    # fetched comparison stays completely clean.
    stored_series.append(_series_row("2026-08-09", 900.0, 1_000_000.0 / bridge_factor))
    stored_series.append(_series_row("2026-08-11", 100.0 * bridge_factor, 1_000_000.0 / bridge_factor))
    stored_series.append(_series_row("2026-08-12", 100.0 * bridge_factor, 1_000_000.0 / bridge_factor))

    result = diag.classify_local_convention_with_volume_evidence(stored_series, evidence_row, provider_by_date)
    assert result["anomalous_jump_count"] >= 1
    assert result["windows"]["recovered_dates"]["boundary_jumps"]
    # the per-date evidence-backed classification is UNCHANGED by the continuity narrative -- it is
    # computed purely from compute_provider_comparison/classify_date_from_provider_comparison.
    per_date = {r["date"]: r["classification"] for r in result["windows"]["recovered_dates"]["per_date"]}
    assert per_date["2026-08-11"] == "bridged+compensating"
    assert per_date["2026-08-12"] == "bridged+compensating"
    # but internally_consistent still honestly reflects the boundary jump as a safety-net signal.
    assert result["internally_consistent"] is False


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


# --- goal-market-compass iter-15 (Goal 5): _build_bars_with_transformed_close's NEW volume_override ------


def test_build_bars_with_transformed_close_volume_override_is_backward_compatible_when_omitted():
    """Iteration 14's exact test, unmodified call shape -- proves the new optional kwarg changes NOTHING
    when omitted."""
    bars = [
        Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=100.0, volume=10.0),
        Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=200.0, volume=20.0),
        Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=300.0, volume=30.0),
    ]
    out = diag._build_bars_with_transformed_close(bars, {date(2026, 8, 11), date(2026, 8, 12)}, 2.0)
    assert out[0].close == 100.0 and out[0].volume == 10.0
    assert out[1].close == 100.0 and out[1].volume == 20.0  # volume unchanged -- no override supplied
    assert out[2].close == 150.0 and out[2].volume == 30.0


def test_build_bars_with_transformed_close_applies_volume_override_only_to_overridden_dates():
    bars = [
        Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=100.0, volume=10.0),
        Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=200.0, volume=20.0),
        Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=300.0, volume=30.0),
    ]
    override = {date(2026, 8, 11): 999.0}  # ONLY 08-11 has fetched evidence; 08-12 does not
    out = diag._build_bars_with_transformed_close(
        bars, {date(2026, 8, 11), date(2026, 8, 12)}, 2.0, volume_override=override
    )
    assert out[0].volume == 10.0  # untouched date -- unaffected regardless
    assert out[1].close == 100.0 and out[1].volume == 999.0  # BOTH close and volume substituted
    assert out[2].close == 150.0 and out[2].volume == 30.0  # close substituted, volume passes through (no evidence)


# --- TC-22/23/24: decision-impact trace with a genuine volume_override -----------------------------------


def test_tc22_trace_universe_resolver_impact_with_volume_override_changes_adv_b(engine):
    cfg = _small_universe_cfg()
    bridge_factor = 2.793
    with Session(engine) as session:
        _seed_daily_prices(
            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
            close_start=180.0, close_step=0.5, volume=1_000_000.0,
        )

    with Session(engine) as session:
        impact_no_override = diag.trace_universe_resolver_impact(session, cfg, date(2026, 8, 11), bridge_factor)
    with Session(engine) as session:
        impact_with_override = diag.trace_universe_resolver_impact(
            session, cfg, date(2026, 8, 11), bridge_factor,
            volume_override={date(2026, 8, 11): 250_000.0},  # materially different fetched volume
        )

    assert impact_with_override["volume_override_applied"] == {"2026-08-11": 250_000.0}
    # the override materially changes B's ADV relative to the no-override (volume-held-fixed) trace --
    # proving the override genuinely participates in the computation, not merely recorded and ignored.
    assert impact_with_override["adv_dollar_b"] != impact_no_override["adv_dollar_b"]


def test_tc23_trace_is_read_only_creates_no_scanner_run(engine):
    """Grep-verifiable in the module source (zero calls to `scanner.persist_run_payload`/`session.add`/
    `session.commit` anywhere in `j11_avb_diagnostic.py`); this test is the behavioral proof: after
    tracing both representations, the fixture DB still has zero ScannerRun rows."""
    from sqlalchemy import func as _func
    from sqlmodel import select as _select
    from app.models import ScannerRun

    cfg = _small_universe_cfg()
    bridge_factor = 2.793
    with Session(engine) as session:
        _seed_daily_prices(
            session, diag.AVB_SYMBOL, n=40, end=AVB_TEST_DATES_END,
            close_start=180.0, close_step=0.5, volume=1_000_000.0,
        )

    with Session(engine) as session:
        diag.trace_universe_resolver_impact(
            session, cfg, date(2026, 8, 11), bridge_factor, volume_override={date(2026, 8, 11): 250_000.0},
        )
        diag.trace_scoring_and_selection_impact(
            session, cfg, date(2026, 8, 11), bridge_factor, volume_override={date(2026, 8, 11): 250_000.0},
        )

    with Session(engine) as session:
        count = session.exec(_select(_func.count()).select_from(ScannerRun)).one()
    assert count == 0


def test_tc24_trace_scoring_and_selection_impact_reports_volume_override_applied(engine):
    cfg = _small_universe_cfg()
    bridge_factor = 2.793
    with Session(engine) as session:
        _seed_daily_prices(
            session, diag.AVB_SYMBOL, n=60, end=AVB_TEST_DATES_END,
            close_start=180.0, close_step=0.2, volume=1_000_000.0,
        )
    with Session(engine) as session:
        impact = diag.trace_scoring_and_selection_impact(
            session, cfg, date(2026, 8, 11), bridge_factor, volume_override={date(2026, 8, 11): 250_000.0},
        )
    assert impact["volume_override_applied"] == {"2026-08-11": 250_000.0}
