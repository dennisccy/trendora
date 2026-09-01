"""app.engine.compass (goal-market-compass iter-2, J-03/J-04) — narrative, selection, manifest assembly.

File-scoped synthetic fixtures (fresh in-memory SQLite DB, hand-built `ScannerRun` / `ScannerResult` /
`MarketPhaseCache` rows) — never `loaded_engine`. `MarketPhaseCache` is pre-populated directly (keyed via
the SAME `_cache_version` the real cache uses) so these tests need no real price history at all.
"""
from __future__ import annotations

import ast
import hashlib
import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import load_config
from app.engine import compass
from app.engine import market_phase as market_phase_module
from app.models import MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow


@pytest.fixture()
def cfg():
    return load_config()


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng


def _mk_run(session: Session, asof: date, regime_score: float = 60.0, regime_label: str = "Expansion") -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=regime_score, regime_label=regime_label, regime_components_json="[]",
        breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _mk_result(
    session: Session, run_id: int, ticker: str, l_score: float, l_bucket: str,
    e_score: float, e_bucket: str, r_score: float, r_bucket: str,
    atr_value=3.0, atr_pct=0.5, invalidation_note=None,
) -> None:
    record = {
        "ticker": ticker,
        "invalidation": {
            "basis": "50-DMA", "ma_period": 50, "level": 100.0, "price": 110.0,
            "note": invalidation_note or f"{ticker} invalidates below its 50-DMA (100.00).",
        },
    }
    if atr_value is not None:
        record["risk_budget"] = {"atr_pct": {"value": atr_value, "percentile": atr_pct}}
    session.add(
        ScannerResult(
            run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
            leadership_score=l_score, leadership_bucket=l_bucket,
            entry_quality_score=e_score, entry_quality_bucket=e_bucket,
            risk_score=r_score, risk_bucket=r_bucket,
            setup_status="Breakout-watch", rank=1, record_json=json.dumps(record),
        )
    )


def _seed_phase_cache(session: Session, as_of: date, available: bool, severity=30.0, phase="Expansion", p_bear=0.15) -> None:
    version = market_phase_module._cache_version(session)
    payload = {"available": available}
    if available:
        payload.update({"severity": severity, "phase": phase, "p_bear": p_bear})
    session.add(
        MarketPhaseCache(
            asof_key=as_of.isoformat(), dataset_version=version,
            payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
        )
    )
    session.commit()


@pytest.fixture()
def selection_run(engine, cfg):
    """One run with a deliberately varied cross-section for J-04 selection tests:
      AAA: L=92 A, E=85 B, R=40 C  -> qualifies (clears all three)
      BBB: L=88 A, E=78 B, R=45 C  -> qualifies
      CCC: L=77 B, E=55 D, R=50 C  -> below the leadership floor (80) -> near-miss why-not (>= why_not_floor 75)
      DDD: L=30 E, E=20 E, R=90 E  -> far below floor -> tally only, no individual why-not entry
      EEE: L=95 A, E=90 A, R=35 B  -> qualifies, no risk_budget key at all (honest-NA caution path)
      HPE: L=92.7 A, E=21.5 E, R=58.9 C -> goal-market-compass iter-35 (J-12): the real HPE shape from
        the frontier export's mislabel -- leadership CLEARS the floor but the entry qualifier fails. Is a
        CANDIDATE (leadership_min_score is the only candidacy gate) carrying an advisory caution, never
        `below_selection_floor` despite failing a qualifier -- the exact case the prior buggy code got
        wrong (BACKGROUND: CCC, the suite's only other qualifier-failing row, is ALSO below the floor, so
        it alone never exercised this path).
    """
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 3, 1))
        _mk_result(session, run.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
        _mk_result(session, run.id, "BBB", 88.0, "A", 78.0, "B", 45.0, "C")
        _mk_result(session, run.id, "CCC", 77.0, "B", 55.0, "D", 50.0, "C")
        _mk_result(session, run.id, "DDD", 30.0, "E", 20.0, "E", 90.0, "E")
        _mk_result(session, run.id, "EEE", 95.0, "A", 90.0, "A", 35.0, "B", atr_value=None)
        _mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 58.9, "C")
        session.commit()
        session.refresh(run)
        return run.id


# --- selection (J-04) ---------------------------------------------------------------------------


def test_candidates_match_stored_scores_and_word_maps(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    by_ticker = {c["ticker"]: c for c in result["candidates"]}
    assert set(by_ticker) == {"AAA", "BBB", "EEE", "HPE"}
    aaa = by_ticker["AAA"]
    assert aaa["leadership_score"] == 92.0
    assert aaa["leadership_word"] == cfg.compass.vocabulary.leadership_words["A"]
    assert aaa["entry_word"] == cfg.compass.vocabulary.entry_words["B"]
    assert aaa["risk_word"] == cfg.compass.vocabulary.risk_words["C"]
    assert aaa["invalidation"] == "AAA invalidates below its 50-DMA (100.00)."


def test_checklist_verdicts_reproduce_inclusion(engine, cfg, selection_run):
    """iter-35 (J-12, TC-6/TC-14): the GATING check (leadership_min_score) ALONE reproduces inclusion --
    every candidate's gating verdict is Pass and is tagged `gating: True` -- while ADVISORY checks
    (entry_min_score/risk_max_score) are tagged `gating: False` and may legitimately Miss (HPE clears
    leadership but misses its entry qualifier) without affecting candidacy."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    for candidate in result["candidates"]:
        assert {row["condition"] for row in candidate["checklist"]} == {
            "leadership_min_score", "entry_min_score", "risk_max_score",
        }
        for row in candidate["checklist"]:
            assert row["gating"] == (row["condition"] == "leadership_min_score")
        gating_rows = [row for row in candidate["checklist"] if row["gating"]]
        assert len(gating_rows) == 1
        assert gating_rows[0]["verdict"] == "Pass"  # the gating verdict ALONE reproduces inclusion
    # HPE: leadership (gating) Pass, entry (advisory) Miss -- proves an advisory Miss never excludes.
    hpe = next(c for c in result["candidates"] if c["ticker"] == "HPE")
    entry_row = next(row for row in hpe["checklist"] if row["condition"] == "entry_min_score")
    assert entry_row["verdict"] == "Miss" and entry_row["gating"] is False
    # every OTHER candidate in this fixture clears every qualifier -- what_would_change stays all-met there
    for candidate in result["candidates"]:
        if candidate["ticker"] == "HPE":
            continue
        assert all(row["met"] is True for row in candidate["what_would_change"])


def test_why_not_near_miss_has_failed_conditions_with_distance(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
    assert "CCC" in why_not_by_ticker  # leadership 77 >= why_not_floor 75 -> near-miss, individually listed
    ccc = why_not_by_ticker["CCC"]
    assert ccc["reason"] == "below_selection_floor"  # goal-market-compass iter-38 (J-14)
    assert ccc["cap_rank"] is None and ccc["cap"] is None
    failed = ccc["failed_conditions"]
    assert any(f["condition"] == "entry_min_score" for f in failed)
    entry_fail = next(f for f in failed if f["condition"] == "entry_min_score")
    assert entry_fail["actual"] == 55.0
    assert entry_fail["threshold"] == cfg.compass.selection.entry_min_score
    assert entry_fail["distance"] == pytest.approx(cfg.compass.selection.entry_min_score - 55.0)
    assert entry_fail["gating"] is False
    # CCC also fails the GATING leadership check (77 < 80) -- it is why it is below_selection_floor.
    leadership_fail = next(f for f in failed if f["condition"] == "leadership_min_score")
    assert leadership_fail["gating"] is True
    # DDD is far below why_not_floor -> counted in the tally, but NOT given an individual why-not entry
    assert "DDD" not in why_not_by_ticker


def test_disposition_tally_partitions_member_count_minus_candidates(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        member_count = len(session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all())
        result = compass.evaluate_selection(session, run, cfg)
    tally = result["disposition_tally"]
    candidate_count = len(result["candidates"])
    assert tally["below_selection_floor"] + tally["excluded_by_cap"] == member_count - candidate_count
    assert tally["below_selection_floor"] == 2  # CCC, DDD
    assert tally["excluded_by_cap"] == 0  # only 3 qualify, cap (10) never binds here


def test_excluded_by_cap_get_empty_failed_conditions(engine, cfg, selection_run):
    """goal-market-compass iter-38 (J-14): extended -- a cap-excluded row that truly passed every
    qualifier now ALSO carries `reason == "excluded_by_cap"` and a non-null `cap_rank`/`cap` (the row's
    1-based rank among all above-floor qualifying rows, and the configured cap value)."""
    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, capped_cfg)
    assert len(result["candidates"]) == 2
    # AAA/BBB/EEE/HPE all clear the leadership floor (qualify); cap keeps only the top 2 by leadership.
    assert {c["ticker"] for c in result["candidates"]} == {"EEE", "HPE"}
    assert result["disposition_tally"]["excluded_by_cap"] == 2
    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
    cut_tickers = {"AAA", "BBB", "EEE", "HPE"} - {c["ticker"] for c in result["candidates"]}
    assert cut_tickers == {"AAA", "BBB"}
    # Qualifying order (leadership desc): EEE(95) rank1, HPE(92.7) rank2, AAA(92) rank3, BBB(88) rank4.
    expected_cap_rank = {"AAA": 3, "BBB": 4}
    for cut_ticker in cut_tickers:
        entry = why_not_by_ticker[cut_ticker]
        assert entry["failed_conditions"] == []  # passed everything; only the cap cut it
        assert entry["reason"] == "excluded_by_cap"
        assert entry["cap_rank"] == expected_cap_rank[cut_ticker]
        assert entry["cap"] == 2


@pytest.fixture()
def why_not_reasons_run(engine, cfg):
    """goal-market-compass iter-38 (J-14): isolating fixture rows for the why-not reason split -- each
    row fails (or clears) exactly one condition so a single assertion can attribute a why-not entry's
    shape to ONE cause (iter-35 lesson, applied one level below its own TC-24 fixture-confound finding:
    `selection_run`'s only above-floor qualifier-failing row, HPE, is ALWAYS inside a max_candidates=2
    cap because its leadership score is so high -- so no existing fixture ever produced a cap-excluded
    row that ALSO missed a qualifier, BACKGROUND):
      CAND1/CAND2: L=95/90 -> always candidates (top of the leadership order).
      PASS_CUT: L=85, E=80, R=40 -> qualifies (clears leadership/entry/risk), ranked beyond a
        max_candidates=2 cap -> excluded_by_cap with failed_conditions == [] (TC-2).
      DXCM: L=84.98, E=26.53, R=57.63 -> the real DXCM shape (BACKGROUND): clears the leadership floor
        and the risk ceiling but fails the entry_min_score (70.0) ADVISORY qualifier, ranked beyond the
        same cap -> excluded_by_cap with exactly one failed_conditions entry (entry_min_score,
        gating: False) (TC-1).
      NEARMISS: L=76.0, E=75.0, R=55.0 -> below leadership_min_score (80) but at/above why_not_floor
        (75), clearing BOTH advisory qualifiers -> below_selection_floor with failed_conditions
        containing ONLY the leadership_min_score check (gating: True) -- isolates the floor miss from
        any advisory one (TC-3).
      FARBELOW: L=50.0, E=80.0, R=40.0 -> far below why_not_floor -> tally-only, no individual why-not
        entry (mirrors selection_run's DDD).
    """
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 5, 1))
        _mk_result(session, run.id, "CAND1", 95.0, "A", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "CAND2", 90.0, "A", 88.0, "B", 38.0, "B")
        _mk_result(session, run.id, "PASS_CUT", 85.0, "A", 80.0, "B", 40.0, "C")
        _mk_result(session, run.id, "DXCM", 84.98, "A", 26.53, "E", 57.63, "C")
        _mk_result(session, run.id, "NEARMISS", 76.0, "B", 75.0, "B", 55.0, "C")
        _mk_result(session, run.id, "FARBELOW", 50.0, "E", 80.0, "B", 40.0, "C")
        session.commit()
        session.refresh(run)
        return run.id


def test_why_not_reasons_and_cap_rank_isolate_each_condition(engine, cfg, why_not_reasons_run):
    """J-14 step 7 / TC-1 / TC-2 / TC-3: the two isolating fixtures the prior suite lacked -- an
    above-floor, qualifier-failing, cap-excluded row (DXCM-shaped) and a below-floor near-miss that
    clears every advisory qualifier. No entry is ever served as passing a qualifier its stored row
    fails, and both reason classes appear together in this fixture universe."""
    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
    with Session(engine) as session:
        run = session.get(ScannerRun, why_not_reasons_run)
        result = compass.evaluate_selection(session, run, capped_cfg)

    assert {c["ticker"] for c in result["candidates"]} == {"CAND1", "CAND2"}
    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}

    # TC-2: PASS_CUT clears every qualifier -- cap-excluded, empty failed_conditions, ranked #3 of cap 2.
    pass_cut = why_not_by_ticker["PASS_CUT"]
    assert pass_cut["reason"] == "excluded_by_cap"
    assert pass_cut["failed_conditions"] == []
    assert pass_cut["cap_rank"] == 3
    assert pass_cut["cap"] == 2

    # TC-1: DXCM clears leadership + risk but misses the entry_min_score advisory qualifier -- served as
    # excluded_by_cap (never as though it "passed every qualifier"), exactly one failed condition.
    dxcm = why_not_by_ticker["DXCM"]
    assert dxcm["reason"] == "excluded_by_cap"
    assert dxcm["cap_rank"] == 4
    assert dxcm["cap"] == 2
    assert len(dxcm["failed_conditions"]) == 1
    entry_fail = dxcm["failed_conditions"][0]
    assert entry_fail["condition"] == "entry_min_score"
    assert entry_fail["gating"] is False
    assert entry_fail["threshold"] == 70.0
    assert entry_fail["actual"] == 26.53
    assert entry_fail["distance"] == pytest.approx(70.0 - 26.53)

    # TC-3: NEARMISS is below the leadership floor but clears both advisory qualifiers -- served as
    # below_selection_floor with EXACTLY the gating leadership_min_score miss, cap_rank/cap both null.
    nearmiss = why_not_by_ticker["NEARMISS"]
    assert nearmiss["reason"] == "below_selection_floor"
    assert nearmiss["cap_rank"] is None
    assert nearmiss["cap"] is None
    assert len(nearmiss["failed_conditions"]) == 1
    leadership_fail = nearmiss["failed_conditions"][0]
    assert leadership_fail["condition"] == "leadership_min_score"
    assert leadership_fail["gating"] is True
    assert leadership_fail["threshold"] == 80.0
    assert leadership_fail["actual"] == 76.0
    assert leadership_fail["distance"] == pytest.approx(4.0)

    # FARBELOW is far below why_not_floor -- tally-only, no individual why-not entry.
    assert "FARBELOW" not in why_not_by_ticker

    # No entry is ever served as passing a qualifier its stored row fails (J-14 acceptance): every
    # failed_conditions item's `actual` genuinely misses its own `threshold` in the failing direction.
    for entry in result["why_not"]:
        for failed in entry["failed_conditions"]:
            if failed["condition"] == "risk_max_score":
                assert failed["actual"] > failed["threshold"]
            else:
                assert failed["actual"] < failed["threshold"]

    # Both reason classes appear together when both exist in the fixture universe.
    assert {w["reason"] for w in result["why_not"]} == {"excluded_by_cap", "below_selection_floor"}


def test_why_not_totals_uncapped_before_display_truncation(engine, cfg, why_not_reasons_run):
    """TC-4 / TC-11: `why_not_totals` counts the FULL pool per reason, computed from the SAME
    non_qualifying/excluded_by_cap_pairs partitions BEFORE `why_not_cap` truncates the display list --
    and reads an explicit 0, never a missing field, when one reason class is empty (TC-11: zero
    cap-excluded names)."""
    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
    with Session(engine) as session:
        run = session.get(ScannerRun, why_not_reasons_run)
        capped_result = compass.evaluate_selection(session, run, capped_cfg)
    assert capped_result["why_not_totals"] == {
        "excluded_by_cap_uncapped": 2,  # PASS_CUT, DXCM
        "below_floor_in_band_uncapped": 1,  # NEARMISS (FARBELOW is below why_not_floor)
    }

    # TC-11: default cfg (max_candidates=10) -- all 4 qualifying rows become candidates, so ZERO rows
    # are excluded_by_cap; the total is an explicit 0, never a missing/null field.
    with Session(engine) as session:
        run = session.get(ScannerRun, why_not_reasons_run)
        uncapped_result = compass.evaluate_selection(session, run, cfg)
    assert uncapped_result["disposition_tally"]["excluded_by_cap"] == 0
    assert uncapped_result["why_not_totals"]["excluded_by_cap_uncapped"] == 0
    assert uncapped_result["why_not_totals"]["below_floor_in_band_uncapped"] == 1


def test_why_not_display_reserves_slots_for_the_scarcer_reason(engine, cfg):
    """J-14's core functional fix: `excluded_by_cap` rows are ALWAYS at/above `leadership_min_score` by
    construction, so a plain leadership-desc sort over the combined pool always outranks every
    `below_selection_floor` row -- on the real committed 2026-08-12 frontier this alone (27 cap-excluded
    vs a why_not_cap of 20) makes the near-miss band entirely unlistable no matter how each entry's
    `reason`/`failed_conditions` are labeled (BACKGROUND). Reproduces that shape at unit scale: 5
    cap-excluded rows (94/92/90/88/85, all clearing every qualifier) outrank all 3 below-floor near-miss
    rows (79/77/76) on raw leadership score -- a naive top-`why_not_cap` sort would show ZERO near-miss
    names. With `why_not_cap_per_reason` reserving slots per class, the near-miss band is restored."""
    narrowed = cfg.compass.selection.model_copy(
        update={"why_not_cap": 4, "why_not_cap_per_reason": 2, "max_candidates": 1}
    )
    narrowed_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": narrowed})})
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 6, 1))
        _mk_result(session, run.id, "CAND", 99.0, "A", 90.0, "A", 35.0, "B")  # the sole candidate (max_candidates=1)
        _mk_result(session, run.id, "CAP1", 94.0, "A", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "CAP2", 92.0, "A", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "CAP3", 90.0, "A", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "CAP4", 88.0, "A", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "CAP5", 85.0, "A", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "NM1", 79.0, "B", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "NM2", 77.0, "B", 90.0, "A", 35.0, "B")
        _mk_result(session, run.id, "NM3", 76.0, "B", 90.0, "A", 35.0, "B")
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, narrowed_cfg)

    assert result["why_not_totals"] == {"excluded_by_cap_uncapped": 5, "below_floor_in_band_uncapped": 3}
    shown_tickers = {w["ticker"] for w in result["why_not"]}
    assert len(shown_tickers) == 4  # why_not_cap
    # The reservation guarantees the TOP 2 (by leadership) of EACH reason class -- never zero near-miss
    # names despite 5 cap-excluded rows outranking every below-floor row on raw leadership score.
    assert shown_tickers == {"CAP1", "CAP2", "NM1", "NM2"}
    reasons_shown = {w["ticker"]: w["reason"] for w in result["why_not"]}
    assert reasons_shown["CAP1"] == reasons_shown["CAP2"] == "excluded_by_cap"
    assert reasons_shown["NM1"] == reasons_shown["NM2"] == "below_selection_floor"


def test_candidates_empty_reason_when_nothing_qualifies(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 3, 8))
        _mk_result(session, run.id, "ZZZ", 10.0, "E", 10.0, "E", 95.0, "E")
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    assert result["candidates"] == []
    assert isinstance(result["candidates_empty_reason"], str) and result["candidates_empty_reason"]
    # iter-35 (J-12, TC-7): names ONLY the gating rule (leadership) -- never entry/risk as though they gated.
    reason_lower = result["candidates_empty_reason"].lower()
    assert "entry_min_score" not in reason_lower
    assert "risk_max_score" not in reason_lower
    assert "entry quality" not in reason_lower
    assert "risk" not in reason_lower
    assert "leadership" in reason_lower


def test_risk_off_regime_adds_caution_to_every_candidate(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        run.regime_label = "Risk-off"
        session.add(run)
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    assert len(result["candidates"]) == 4
    for candidate in result["candidates"]:
        assert any(c.startswith("REGIME_RISK_OFF") for c in candidate["cautions"])
        assert not any("buy" in c.lower() or "sell" in c.lower() for c in candidate["cautions"])


def test_missing_risk_budget_renders_honest_na_caution_never_crashes(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    eee = next(c for c in result["candidates"] if c["ticker"] == "EEE")
    assert any("not available" in c for c in eee["cautions"])
    assert any(c.startswith("ATR_RISK_BUDGET") for c in eee["cautions"])


def test_no_composite_score_field_anywhere(engine, cfg, selection_run):
    """AG-11: only the three existing scores/buckets (via word maps) may appear — no new blended number."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    allowed_numeric_keys = {"leadership_score", "entry_quality_score", "risk_score"}
    for candidate in result["candidates"]:
        numeric_keys = {k for k, v in candidate.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        assert numeric_keys <= allowed_numeric_keys, f"unexpected numeric field(s) on candidate: {numeric_keys - allowed_numeric_keys}"


def test_comparison_cohort_covers_every_non_candidate_with_disposition(engine, cfg, selection_run):
    """iter-3 (J-05/J-06, TC-19/TC-24): comparison_cohort holds EVERY non-candidate member (member_count
    minus candidate_count), each carrying exactly one closed-vocabulary disposition, tallies partitioning
    the cohort exactly."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        member_count = len(session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all())
        result = compass.evaluate_selection(session, run, cfg)
    cohort = result["comparison_cohort"]
    assert len(cohort) == member_count - len(result["candidates"])
    by_ticker = {row["ticker"]: row for row in cohort}
    assert by_ticker["CCC"]["selection_disposition"] == "below_selection_floor"
    assert by_ticker["DDD"]["selection_disposition"] == "below_selection_floor"
    dispositions = {row["selection_disposition"] for row in cohort}
    assert dispositions <= {"below_selection_floor", "excluded_by_cap"}
    tally = result["disposition_tally"]
    below = sum(1 for row in cohort if row["selection_disposition"] == "below_selection_floor")
    capped = sum(1 for row in cohort if row["selection_disposition"] == "excluded_by_cap")
    assert below == tally["below_selection_floor"]
    assert capped == tally["excluded_by_cap"]
    # every candidate ticker is ticker-disjoint from the cohort (never both selected AND non-selected)
    assert {c["ticker"] for c in result["candidates"]}.isdisjoint(by_ticker)


def test_comparison_cohort_row_carries_frozen_context_fields(engine, cfg, selection_run):
    """iter-3 (J-05/J-06): every cohort row's context is read from the run's own stored record_json —
    close (invalidation.price), atr_pct {value, percentile}, sector, setup_status, rank_in_run."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    ccc = next(row for row in result["comparison_cohort"] if row["ticker"] == "CCC")
    assert ccc["close"] == 110.0  # _mk_result's invalidation.price fixture value
    assert ccc["atr_pct"] == {"value": 3.0, "percentile": 0.5}
    assert ccc["sector"] == "Technology"
    assert ccc["setup_status"] == "Breakout-watch"
    assert ccc["rank_in_run"] == 1
    assert ccc["theme_memberships"] == []  # no themes configured on this synthetic fixture row


def test_excluded_by_cap_cohort_rows_carry_that_disposition(engine, cfg, selection_run):
    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, capped_cfg)
    cut_tickers = {"AAA", "BBB", "EEE", "HPE"} - {c["ticker"] for c in result["candidates"]}
    for cut_ticker in cut_tickers:
        cohort_row = next(row for row in result["comparison_cohort"] if row["ticker"] == cut_ticker)
        assert cohort_row["selection_disposition"] == "excluded_by_cap"


# --- iter-35 (J-12): leadership_min_score is the ONLY candidacy gate --------------------------------


def test_hpe_shape_row_clears_floor_never_below_selection_floor_and_carries_caution(engine, cfg, selection_run):
    """TC-2/TC-5/TC-9: the real HPE shape (leadership clears the floor, entry qualifier fails) is a
    CANDIDATE -- never `below_selection_floor` -- and carries an advisory caution citing `entry_min_score`
    and the row's actual `entry_quality_score` value, never a reason claiming it clears that qualifier.
    This is the EXACT case the prior buggy code mislabeled on the frontier export (37/539 rows, HPE
    92.71 highest)."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    hpe = next(c for c in result["candidates"] if c["ticker"] == "HPE")
    assert not any(row["ticker"] == "HPE" for row in result["comparison_cohort"])  # never a non-candidate here
    assert not any(reason.startswith("Entry Quality") for reason in hpe["reasons"])  # never claims it clears entry
    assert any(reason.startswith("Leadership") for reason in hpe["reasons"])  # the gating check IS a reason
    caution = next(c for c in hpe["cautions"] if c.startswith("ENTRY_QUALITY_QUALIFIER"))
    assert "21.5" in caution  # the row's actual stored entry_quality_score value
    assert f"{cfg.compass.selection.entry_min_score:.1f}" in caution  # the threshold


def test_disposition_predicate_holds_for_every_comparison_cohort_row(engine, cfg, selection_run):
    """iter-35 (J-12): `selection_disposition` is truthful BY CONSTRUCTION -- every row's OWN predicate
    holds (below_selection_floor => leadership < floor; excluded_by_cap => leadership >= floor). Zero
    comparison_cohort rows at/above the floor are mislabeled below_selection_floor (TC-2/TC-9's
    zero-mislabel requirement, exercised directly rather than only via the internal runtime assertion)."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    floor = cfg.compass.selection.leadership_min_score
    assert result["comparison_cohort"]  # the fixture has non-candidate rows -- a non-vacuous check
    for row in result["comparison_cohort"]:
        if row["selection_disposition"] == "below_selection_floor":
            assert row["leadership_score"] < floor
        elif row["selection_disposition"] == "excluded_by_cap":
            assert row["leadership_score"] >= floor
        else:
            pytest.fail(f"unexpected disposition {row['selection_disposition']!r}")
    assert not any(
        row["leadership_score"] >= floor and row["selection_disposition"] == "below_selection_floor"
        for row in result["comparison_cohort"]
    )


def test_perturbing_advisory_qualifiers_leaves_hashes_membership_and_dispositions_unchanged(engine, cfg, selection_run):
    """iter-35 (J-12, TC-4/TC-15): completes the counter-test J-06 already specified but the suite never
    implemented (the suite's only other qualifier-failing row, CCC, was ALSO below the leadership floor,
    so it alone never exercised this path). Perturbing entry_min_score/risk_max_score moves NEITHER
    candidate_rule_hash NOR cohort_rule_hash, and leaves the candidate list (tickers, in order), the
    comparison_cohort (membership AND every selection_disposition), and the near-threshold shadow cohort
    byte-identical -- proving the two advisory qualifiers no longer gate membership at all."""
    perturbed_selection = cfg.compass.selection.model_copy(
        update={
            "entry_min_score": cfg.compass.selection.entry_min_score + 15.0,
            "risk_max_score": cfg.compass.selection.risk_max_score - 15.0,
        }
    )
    perturbed_cfg = cfg.model_copy(
        update={"compass": cfg.compass.model_copy(update={"selection": perturbed_selection})}
    )
    # sanity: the perturbation is real (manifest_config_hash DOES move) -- otherwise this test proves nothing.
    assert compass._hash_subset(compass._manifest_config_subset(cfg)) != compass._hash_subset(
        compass._manifest_config_subset(perturbed_cfg)
    )

    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        before = compass.evaluate_selection(session, run, cfg)
        after = compass.evaluate_selection(session, run, perturbed_cfg)

    assert compass._hash_subset(compass._candidate_rule_subset(cfg)) == compass._hash_subset(
        compass._candidate_rule_subset(perturbed_cfg)
    )
    assert compass._hash_subset(compass._cohort_rule_subset(cfg)) == compass._hash_subset(
        compass._cohort_rule_subset(perturbed_cfg)
    )
    assert [c["ticker"] for c in before["candidates"]] == [c["ticker"] for c in after["candidates"]]
    assert before["comparison_cohort"] == after["comparison_cohort"]  # membership AND every disposition
    assert before["near_threshold_shadow"] == after["near_threshold_shadow"]
    assert before["disposition_tally"] == after["disposition_tally"]


def test_near_threshold_shadow_is_half_open_band_below_floor(engine, cfg, selection_run):
    """iter-3 (J-05/J-06, TC-19): near_threshold_shadow = leadership in [shadow.min_score,
    leadership_min_score) -- half-open, deterministic order (leadership desc, ticker), a subset of
    comparison_cohort with no selection_disposition key. CCC (leadership 77.0, in [75.0, 80.0)) is
    shadow-eligible; DDD (30.0) is not; nothing at/above the 80.0 floor is ever shadow."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    shadow = result["near_threshold_shadow"]
    assert [row["ticker"] for row in shadow] == ["CCC"]
    assert "selection_disposition" not in shadow[0]
    assert shadow[0]["leadership_score"] == 77.0
    # never contains a candidate-eligible name (score >= floor) nor DDD (far below the shadow floor)
    shadow_tickers = {row["ticker"] for row in shadow}
    assert shadow_tickers.isdisjoint({c["ticker"] for c in result["candidates"]})
    assert "DDD" not in shadow_tickers


def test_near_threshold_shadow_is_subset_of_comparison_cohort(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    cohort_tickers = {row["ticker"] for row in result["comparison_cohort"]}
    shadow_tickers = {row["ticker"] for row in result["near_threshold_shadow"]}
    assert shadow_tickers <= cohort_tickers


def test_selection_language_scan_covers_candidate_and_why_not_strings(engine, cfg, monkeypatch):
    """TC-35: the SAME banned-language guard build_narrative uses now also scans evaluate_selection's
    candidate reason/caution/invalidation/why-not strings -- a banned term anywhere in them raises."""
    from app.engine import compass as compass_module

    original = compass_module._candidate_payload

    def poisoned(row, checks, detail, run, cfg_arg):
        payload = original(row, checks, detail, run, cfg_arg)
        if payload["ticker"] == "AAA":
            payload["cautions"] = payload["cautions"] + ["You should buy this now."]
        return payload

    monkeypatch.setattr(compass_module, "_candidate_payload", poisoned)
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 3, 20))
        _mk_result(session, run.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
        session.commit()
        session.refresh(run)
        with pytest.raises(ValueError, match="banned language"):
            compass_module.evaluate_selection(session, run, cfg)


# --- narrative (J-03) ---------------------------------------------------------------------------


@pytest.fixture()
def two_runs_with_phase(engine, cfg):
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 4, 1), regime_score=50.0)
        run_b = _mk_run(session, date(2024, 4, 8), regime_score=58.0)
        _mk_result(session, run_a.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
        _mk_result(session, run_b.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        _seed_phase_cache(session, run_a.asof_date, available=True, severity=25.0, phase="Expansion", p_bear=0.10)
        _seed_phase_cache(session, run_b.asof_date, available=True, severity=45.0, phase="Pullback", p_bear=0.35)
        return run_a.id, run_b.id


def test_state_sentence_facts_match_dashboard_and_market_phase(engine, cfg, two_runs_with_phase):
    from app.engine.snapshot_serving import dashboard_payload

    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_b = session.get(ScannerRun, run_b_id)
        selection = compass.evaluate_selection(session, run_b, cfg)
        narrative = compass.build_narrative(session, run_b, session.get(ScannerRun, run_a_id), selection, cfg)
        phase_payload = market_phase_module.market_phase_cached(session, run_b.asof_date, cfg)
        dashboard = dashboard_payload(run_b)

    state = next(s for s in narrative["sentences"] if s["template_id"] == "state")
    facts = {f["name"]: f["value"] for f in state["facts"]}
    assert facts["regime_score"] == dashboard["regime"]["score"] == 58.0
    assert facts["severity"] == phase_payload["severity"] == 45.0
    assert "cautious" in state["text"] or "tense" in state["text"]  # p_bear 0.35 -> "tense" band


def test_direction_no_prior_run_variant(engine, cfg, two_runs_with_phase):
    run_a_id, _run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        selection = compass.evaluate_selection(session, run_a, cfg)
        narrative = compass.build_narrative(session, run_a, None, selection, cfg)
    direction = next(s for s in narrative["sentences"] if s["template_id"].startswith("direction"))
    assert direction["template_id"] == "direction_no_prior_run"
    assert "earliest" in direction["text"].lower()


def test_direction_na_velocity_variant_when_phase_unavailable(engine, cfg):
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 5, 1))
        run_b = _mk_run(session, date(2024, 5, 8))
        _mk_result(session, run_b.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        # deliberately NO MarketPhaseCache row seeded -> market_phase_cached computes over an empty DB and
        # must degrade to available=False (insufficient history), never crash
        selection = compass.evaluate_selection(session, run_b, cfg)
        narrative = compass.build_narrative(session, run_b, run_a, selection, cfg)
    direction = next(s for s in narrative["sentences"] if s["template_id"].startswith("direction"))
    assert direction["template_id"] == "direction_na_velocity"


def test_focus_count_sentence_matches_candidate_count(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        selection = compass.evaluate_selection(session, run, cfg)
        _seed_phase_cache(session, run.asof_date, available=False)
        narrative = compass.build_narrative(session, run, None, selection, cfg)
    focus = next(s for s in narrative["sentences"] if s["template_id"] == "focus_count")
    facts = {f["name"]: f["value"] for f in focus["facts"]}
    assert facts["candidate_count"] == len(selection["candidates"]) == 4
    assert "4" in focus["text"]


def test_banned_language_scan_raises_on_violation(cfg):
    with pytest.raises(ValueError, match="banned language"):
        compass._assert_no_banned_language(
            [{"template_id": "x", "text": "You should buy this now.", "facts": []}], cfg
        )


def test_retrospective_stamp_appears_only_for_non_frontier_asof(engine, cfg, two_runs_with_phase):
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        selection_a = compass.evaluate_selection(session, run_a, cfg)
        selection_b = compass.evaluate_selection(session, run_b, cfg)
        narrative_a = compass.build_narrative(session, run_a, None, selection_a, cfg)  # run_a has a LATER run (run_b) -> retrospective
        narrative_b = compass.build_narrative(session, run_b, run_a, selection_b, cfg)  # run_b IS the frontier -> not retrospective
    assert any(s["template_id"] == "retrospective_stamp" for s in narrative_a["sentences"])
    assert not any(s["template_id"] == "retrospective_stamp" for s in narrative_b["sentences"])


# --- state_band (goal-market-compass iter-28, J-07) -----------------------------------------------


def test_state_band_no_prior_run_renders_null_for_all_three(engine, cfg, two_runs_with_phase):
    """TC-4: the earliest stored run (no previous run) renders an explicit null/no-comparison state for
    ALL THREE bands -- never a fabricated word."""
    run_a_id, _run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        state_band = compass.build_state_band(session, run_a, None, cfg)
    for band in ("regime", "stress", "breadth"):
        assert state_band[band] == {"direction_word": None, "delta": None}


def test_state_band_regime_matches_direction_word_and_stress_flips_polarity(engine, cfg, two_runs_with_phase):
    """TC-1/TC-2: `two_runs_with_phase` has regime_score 50.0 -> 58.0 (+8.0, well above the 2.0 flat
    band) and severity 25.0 -> 45.0 (+20.0, well above the 5.0 flat band -- severity ROSE, i.e. stress
    WORSENED). `state_band.regime.delta` equals `current.regime_score - previous.regime_score` exactly
    and its word is the SAME word `_direction_word` (the narrative's own direction sentence) already
    produces for this pair -- one shared computation, not a second one. `state_band.stress.delta` is the
    LITERAL `current_severity - previous_severity` (+20.0, unflipped -- TC-2's exact equation), but
    because a RISING severity is deteriorating (not improving), its WORD is the OPPOSITE polarity of
    regime's: regime reads "improving", stress reads "deteriorating" for this SAME pair of runs, proving
    the sign transform is deliberate and not an accidental copy of regime's polarity."""
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        expected_regime_word, expected_regime_delta = compass._direction_word(run_b, run_a, cfg)
        state_band = compass.build_state_band(session, run_b, run_a, cfg)
    assert state_band["regime"]["delta"] == pytest.approx(8.0) == expected_regime_delta
    assert state_band["regime"]["direction_word"] == expected_regime_word == cfg.compass.vocabulary.direction_words["up"]
    assert state_band["stress"]["delta"] == pytest.approx(20.0)  # current_severity - previous_severity, literal
    assert state_band["stress"]["direction_word"] == cfg.compass.vocabulary.direction_words["down"]
    assert state_band["regime"]["direction_word"] != state_band["stress"]["direction_word"]


def test_state_band_breadth_flat_when_unchanged(engine, cfg, two_runs_with_phase):
    """TC-3: `_mk_run`'s fixture rows both carry `breadth_above_50dma=55.0` (unchanged) -- delta 0.0 is
    well within the reused `breadth_min_change_pts` (5.0) flat band, so the word is "flat", never
    fabricated as up/down from a zero delta."""
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        state_band = compass.build_state_band(session, run_b, run_a, cfg)
    assert state_band["breadth"]["delta"] == pytest.approx(0.0)
    assert state_band["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["flat"]


def test_state_band_breadth_up_and_down_bands(engine, cfg):
    """TC-3 at the config edge: a breadth move well above `breadth_min_change_pts` (5.0) reads up/down by
    sign; a move well below it reads flat -- all three read straight off the SAME config threshold
    `session_delta._breadth_changes` uses for its own breadth-kind gate (one threshold, two producers)."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 6, 1))
        run_a.breadth_above_50dma = 40.0
        run_b = _mk_run(session, date(2024, 6, 8))
        run_b.breadth_above_50dma = 55.0  # +15.0, well above the 5.0 flat band
        run_c = _mk_run(session, date(2024, 6, 15))
        run_c.breadth_above_50dma = 42.0  # -13.0 vs run_b, well above the flat band (down)
        session.add_all([run_a, run_b, run_c])
        session.commit()
        up = compass.build_state_band(session, run_b, run_a, cfg)
        down = compass.build_state_band(session, run_c, run_b, cfg)
    assert up["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["up"]
    assert down["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["down"]


def test_state_band_stress_na_when_phase_unavailable(engine, cfg):
    """A missing/NA severity input on EITHER side renders `stress` as an explicit no-comparison state --
    never a guessed word -- while `regime`/`breadth` (unaffected inputs) still compute normally. Mirrors
    `test_direction_na_velocity_variant_when_phase_unavailable`'s "no MarketPhaseCache row seeded" setup."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 7, 1), regime_score=50.0)
        run_b = _mk_run(session, date(2024, 7, 8), regime_score=60.0)
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        # deliberately NO MarketPhaseCache row seeded -> market_phase_cached degrades to available=False
        state_band = compass.build_state_band(session, run_b, run_a, cfg)
    assert state_band["stress"] == {"direction_word": None, "delta": None}
    assert state_band["regime"]["direction_word"] is not None
    assert state_band["breadth"]["direction_word"] is not None


def test_state_band_breadth_na_when_either_side_missing(engine, cfg):
    """A missing `breadth_above_50dma` on EITHER stored run renders `breadth` as an explicit
    no-comparison state -- never a guessed word -- while `regime` (unaffected input) still computes."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 8, 1), regime_score=50.0)
        run_a.breadth_above_50dma = None
        run_b = _mk_run(session, date(2024, 8, 8), regime_score=55.0)
        session.add_all([run_a, run_b])
        session.commit()
        state_band = compass.build_state_band(session, run_b, run_a, cfg)
    assert state_band["breadth"] == {"direction_word": None, "delta": None}
    assert state_band["regime"]["direction_word"] is not None


def test_state_band_is_wired_into_manifest_payload_and_content_hash(engine, cfg, two_runs_with_phase):
    """`state_band` is a top-level content block alongside `session_delta`/`narrative`/`selection` (same
    `content_hash` scope) -- flipping it changes `content_hash` (proving it is actually inside the
    hashed scope, not decorative)."""
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    assert "state_band" in payload
    assert payload["state_band"] == compass.build_state_band(session, run_b, run_a, cfg)
    tampered_content = {
        "session_delta": payload["session_delta"], "narrative": payload["narrative"],
        "selection": payload["selection"],
        "state_band": {**payload["state_band"], "regime": {"direction_word": "improving", "delta": 999.0}},
    }
    tampered_hash = hashlib.sha256(
        json.dumps(tampered_content, sort_keys=True, default=str).encode()
    ).hexdigest()
    assert tampered_hash != payload["content_hash"]


def test_state_band_served_verbatim_by_manifest_row_payload(engine, cfg, two_runs_with_phase):
    """`manifest_row_payload` reconstructs `state_band` verbatim from its own storage column (a read,
    never a recompute) -- mirrors `test_manifest_row_payload_matches_build_manifest_payload_content`."""
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        built = compass.build_manifest_payload(session, run_b, run_a, cfg)
        row = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
        served = compass.manifest_row_payload(row)
    assert served["state_band"] == built["state_band"]


def test_state_band_stress_threshold_is_config_driven(cfg):
    """The new `stress_velocity_flat_band` threshold lives ONLY in `compass.delta.*` (anti-goal: No
    magic numbers) -- a direct typed-config read, never a literal in the engine module."""
    assert cfg.compass.delta.stress_velocity_flat_band > 0


# --- manifest assembly + storage -----------------------------------------------------------------


def test_content_hash_stable_across_identical_rebuilds(engine, cfg, two_runs_with_phase):
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        first = compass.build_manifest_payload(session, run_b, run_a, cfg)
        second = compass.build_manifest_payload(session, run_b, run_a, cfg)
    assert first == second
    assert first["content_hash"] == second["content_hash"]
    assert first["narrative"]["sentences"] == second["narrative"]["sentences"]


def test_get_or_create_manifest_computes_once_then_serves_from_storage(engine, cfg, two_runs_with_phase, monkeypatch):
    """iter-3: run_b is the FRONTIER of this fixture -- get_or_create_manifest now requires
    producer="ingest_finalize" to mint the frontier's version 1 (J-05 step 7); TC-1's "zero ADDITIONAL
    producer calls on the warm hit" property is unchanged once minted."""
    run_a_id, run_b_id = two_runs_with_phase
    calls = {"n": 0}
    original = compass.build_manifest_payload

    def counting_build(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(compass, "build_manifest_payload", counting_build)

    with Session(engine) as session:
        run_b = session.get(ScannerRun, run_b_id)
        first_row = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
        assert calls["n"] == 1
        second_row = compass.get_or_create_manifest(session, run_b, cfg)
        assert calls["n"] == 1  # TC-1: zero ADDITIONAL producer calls on the warm hit
        assert first_row.id == second_row.id
        assert first_row.content_hash == second_row.content_hash

    with Session(engine) as session:
        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 4, 8))).all()
        assert len(rows) == 1  # never duplicated


def test_get_or_create_manifest_never_mints_frontier_on_plain_get(engine, cfg, two_runs_with_phase):
    """J-05 step 7 / TC-8: a plain (non-finalize) call for the CURRENT frontier with no manifest yet
    raises ManifestNotYetFrozen -- never silently fabricates one."""
    _run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_b = session.get(ScannerRun, run_b_id)
        with pytest.raises(compass.ManifestNotYetFrozen):
            compass.get_or_create_manifest(session, run_b, cfg)
    with Session(engine) as session:
        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 4, 8))).all()
        assert rows == []  # no partial/fabricated row was written


def test_get_or_create_manifest_historical_asof_still_create_once_mints(engine, cfg, two_runs_with_phase):
    """A HISTORICAL (non-frontier) as_of still create-once-mints on a plain GET-style call (path b) --
    only the CURRENT frontier is guarded."""
    run_a_id, _run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        row = compass.get_or_create_manifest(session, run_a, cfg)
    assert row.mode == "retrospective"
    assert row.prospective_eligible is False


def test_manifest_row_payload_matches_build_manifest_payload_content(engine, cfg, two_runs_with_phase):
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        built = compass.build_manifest_payload(session, run_b, run_a, cfg)
        row = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
        served = compass.manifest_row_payload(row)
    assert served["session_delta"] == built["session_delta"]
    assert served["narrative"] == built["narrative"]
    # iter-3: comparison_cohort/near_threshold_shadow/member_count are LIFTED OUT of the served
    # "selection" block into their own top-level keys (universe.member_count) -- reassemble built's
    # shape the SAME way before comparing (single source, not a shape mismatch).
    built_selection = dict(built["selection"])
    built_comparison_cohort = built_selection.pop("comparison_cohort")
    built_near_threshold_shadow = built_selection.pop("near_threshold_shadow")
    built_member_count = built_selection.pop("member_count")
    assert served["selection"] == built_selection
    assert served["comparison_cohort"] == built_comparison_cohort
    assert served["near_threshold_shadow"] == built_near_threshold_shadow
    assert served["universe"]["member_count"] == built_member_count
    assert served["content_hash"] == built["content_hash"]


def test_missing_required_compass_config_key_fails_closed():
    """A missing required `compass.*` key raises at config load, never silently falls back."""
    from pydantic import ValidationError

    from app.config import CompassSelectionCfg

    with pytest.raises(ValidationError):
        CompassSelectionCfg(rule_version="v1")  # missing every required threshold


def test_no_network_or_lookahead_imports_in_compass_module():
    """AG-9 (no live network call) + AG-5 (no lookahead) as a static guarantee over the module's actual
    code (via ast, so docstring prose is never a false positive)."""
    tree = ast.parse(open(compass.__file__).read())
    banned = {"requests", "httpx", "urllib", "ForwardReturn", "forward_returns", "bars_after"}
    offenders = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            names = [alias.name for alias in node.names]
            for candidate in [module, *names]:
                if candidate in banned or candidate.split(".")[0] in banned:
                    offenders.add(candidate)
        if isinstance(node, ast.Attribute) and node.attr in banned:
            offenders.add(node.attr)
    assert not offenders, f"compass.py references banned identifiers: {offenders}"


# --- rotation (goal-market-compass iter-36, J-13) ------------------------------------------------


def _mk_sector_row(session: Session, run_id: int, ticker: str, rank: int, kind: str = "sector") -> None:
    session.add(SectorScoreRow(
        run_id=run_id, ticker=ticker, kind=kind, name=ticker, members_json="[]",
        score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=rank,
    ))


def _mk_theme_row(session: Session, run_id: int, slug: str, rank: int) -> None:
    session.add(ThemeScoreRow(
        run_id=run_id, slug=slug, name=slug, score=80.0, bucket="A", members_json="[]",
        breadth_label="universe-relative", trend_label="Uptrend", components_json="{}", rank=rank,
    ))


@pytest.fixture()
def rotation_run_pair(engine, cfg):
    """A small run pair with BOTH sides populated for both kinds, plus one below-threshold (suppressed)
    pair per kind (`rank_move_min` is 2 in the real config):
      sector XLK: rank 1 -> 5 (delta +4, LOSING)   sector XLE: rank 5 -> 1 (delta -4, GAINING)
      sector XLF: rank 2 -> 2 (delta 0, suppressed)
      theme  ai:  rank 1 -> 4 (delta +3, LOSING)   theme  ev:  rank 4 -> 1 (delta -3, GAINING)
      theme  cyber: rank 2 -> 2 (delta 0, suppressed)
    """
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 5, 1))
        run_b = _mk_run(session, date(2024, 5, 8))
        _mk_sector_row(session, run_a.id, "XLK", 1)
        _mk_sector_row(session, run_b.id, "XLK", 5)
        _mk_sector_row(session, run_a.id, "XLE", 5)
        _mk_sector_row(session, run_b.id, "XLE", 1)
        _mk_sector_row(session, run_a.id, "XLF", 2)
        _mk_sector_row(session, run_b.id, "XLF", 2)
        _mk_theme_row(session, run_a.id, "ai", 1)
        _mk_theme_row(session, run_b.id, "ai", 4)
        _mk_theme_row(session, run_a.id, "ev", 4)
        _mk_theme_row(session, run_b.id, "ev", 1)
        _mk_theme_row(session, run_a.id, "cyber", 2)
        _mk_theme_row(session, run_b.id, "cyber", 2)
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        return run_a.id, run_b.id


@pytest.fixture()
def all_gainers_sector_run_pair(engine, cfg):
    """J-13 step 8 (dev handoff citation): EVERY threshold-crossing sector mover is a GAINER -- the losing
    side must render its explicit empty state while the gaining side is unaffected. One suppressed
    (below-threshold) row rides alongside so the fixture also proves suppressed != empty-losing."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 5, 15))
        run_b = _mk_run(session, date(2024, 5, 22))
        _mk_sector_row(session, run_a.id, "XLK", 5)
        _mk_sector_row(session, run_b.id, "XLK", 1)  # delta -4, gaining
        _mk_sector_row(session, run_a.id, "XLE", 4)
        _mk_sector_row(session, run_b.id, "XLE", 2)  # delta -2, gaining
        _mk_sector_row(session, run_a.id, "XLF", 3)
        _mk_sector_row(session, run_b.id, "XLF", 3)  # delta 0, suppressed
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        return run_a.id, run_b.id


@pytest.fixture()
def full_universe_rotation_runs(engine, cfg):
    """TC-7/TC-8/TC-15 (goal-market-compass iter-36, J-13): a run pair covering the FULL configured
    sector/industry (`config.etfs.sector` + `config.etfs.industry`) and theme (`config.themes`) universe
    on both runs, so the rotation block's accounting can close exactly against `configured_total`. Ranks
    are REVERSED between the two runs (`prev = N + 1 - cur`, N = the configured count) -- for ODD N (31
    sector/industry, 11 theme today) this deterministically yields exactly ONE exact-middle pair with
    delta 0 (below rank_move_min -- suppressed, fails the threshold OUTRIGHT) and `(N-1)/2`
    above-threshold movers on EACH side (every non-middle delta has |delta| >= 2, matching the real
    `rank_move_min`). With `rotation_top_k` (5) smaller than 15 (sector's per-side count), this isolates
    the TC-8/TC-15 condition: a row that CLEARS rank_move_min but is excluded SOLELY by rotation_top_k --
    counted in `residual_count`, distinct from the middle row that fails rank_move_min outright."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 5, 29))
        run_b = _mk_run(session, date(2024, 6, 5))
        sector_tickers = list(cfg.etfs.sector.keys()) + list(cfg.etfs.industry.keys())
        n_sector = len(sector_tickers)
        for index, ticker in enumerate(sector_tickers):
            cur_rank = index + 1
            prev_rank = n_sector + 1 - cur_rank
            kind = "sector" if ticker in cfg.etfs.sector else "industry"
            _mk_sector_row(session, run_a.id, ticker, prev_rank, kind=kind)
            _mk_sector_row(session, run_b.id, ticker, cur_rank, kind=kind)
        theme_slugs = list(cfg.themes.keys())
        n_theme = len(theme_slugs)
        for index, slug in enumerate(theme_slugs):
            cur_rank = index + 1
            prev_rank = n_theme + 1 - cur_rank
            _mk_theme_row(session, run_a.id, slug, prev_rank)
            _mk_theme_row(session, run_b.id, slug, cur_rank)
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        return run_a.id, run_b.id, n_sector, n_theme


def test_rotation_block_present_with_sector_theme_keys_and_no_stock_rows(engine, cfg, rotation_run_pair):
    """TC-1: `session_delta.rotation` carries `sector`/`theme` keys and zero stock-kind rows anywhere --
    rotation rows carry no `kind` field at all (a purely structural guarantee, not just an empty filter)."""
    run_a_id, run_b_id = rotation_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    rotation = payload["session_delta"]["rotation"]
    assert set(rotation.keys()) == {"sector", "theme"}
    for kind_block in rotation.values():
        for row in kind_block["gaining"] + kind_block["losing"]:
            assert "kind" not in row
            assert set(row.keys()) == {"label", "from", "to", "delta", "direction_word", "drill_href"}


def test_rotation_two_sides_ordered_most_moved_first_and_capped(engine, cfg, full_universe_rotation_runs):
    """TC-2: two explicitly labelled sides, each ordered most-moved-first (|delta| descending), each
    length <= `rotation_top_k`."""
    run_a_id, run_b_id, _n_sector, _n_theme = full_universe_rotation_runs
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    sector = payload["session_delta"]["rotation"]["sector"]
    assert len(sector["gaining"]) <= cfg.compass.delta.rotation_top_k
    assert len(sector["losing"]) <= cfg.compass.delta.rotation_top_k
    for side in (sector["gaining"], sector["losing"]):
        magnitudes = [abs(row["delta"]) for row in side]
        assert magnitudes == sorted(magnitudes, reverse=True)


def test_rotation_pair_below_rank_move_min_excluded_from_both_sides(engine, cfg, rotation_run_pair):
    """TC-3: XLF (delta 0, |0| < rank_move_min=2) appears in neither `gaining` nor `losing`."""
    run_a_id, run_b_id = rotation_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    sector = payload["session_delta"]["rotation"]["sector"]
    labels = {row["label"] for row in sector["gaining"] + sector["losing"]}
    assert "XLF" not in labels
    assert sector["suppressed_count"] == 1


def test_rotation_empty_losing_side_when_every_mover_is_a_gainer(engine, cfg, all_gainers_sector_run_pair):
    """TC-4 / J-13 step 8 (dev handoff citation: this fixture + test): every threshold-crossing sector
    mover is a gainer -- the losing side is an explicit empty array, the gaining side is unaffected."""
    run_a_id, run_b_id = all_gainers_sector_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    sector = payload["session_delta"]["rotation"]["sector"]
    assert sector["losing"] == []
    assert {row["label"] for row in sector["gaining"]} == {"XLK", "XLE"}
    assert sector["suppressed_count"] == 1  # XLF (delta 0) — suppressed, distinct from "empty losing"


def test_rotation_direction_word_falling_rank_number_is_improving(engine, cfg, rotation_run_pair):
    """TC-5: a FALLING rank number (`cur_rank < prev_rank`) always produces the "improving" word; a
    RISING one always produces "deteriorating" — spot-checked against the stored ranks directly (the
    same values `GET /api/sectors`/`GET /api/themes` would serve at each as-of)."""
    run_a_id, run_b_id = rotation_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
        stored_xle = list(session.exec(select(SectorScoreRow).where(SectorScoreRow.ticker == "XLE")))
    sector = payload["session_delta"]["rotation"]["sector"]
    gaining_by_label = {row["label"]: row for row in sector["gaining"]}
    losing_by_label = {row["label"]: row for row in sector["losing"]}
    xle = gaining_by_label["XLE"]  # 5 -> 1, falling
    assert xle["from"] == 5 and xle["to"] == 1
    assert xle["direction_word"] == cfg.compass.vocabulary.direction_words["up"] == "improving"
    xlk = losing_by_label["XLK"]  # 1 -> 5, rising
    assert xlk["from"] == 1 and xlk["to"] == 5
    assert xlk["direction_word"] == cfg.compass.vocabulary.direction_words["down"] == "deteriorating"
    stored_ranks = {row.run_id: row.rank for row in stored_xle}
    assert stored_ranks[run_a_id] == xle["from"] and stored_ranks[run_b_id] == xle["to"]
    # one theme row, same check
    theme = payload["session_delta"]["rotation"]["theme"]
    ev = {row["label"]: row for row in theme["gaining"]}["ev"]  # 4 -> 1, falling
    assert ev["direction_word"] == "improving"


def test_rotation_changes_entries_carry_same_delta_and_direction_word_as_rotation_rows(engine, cfg, rotation_run_pair):
    """TC-6: `session_delta.changes` sector/theme-kind entries carry the SAME signed `delta` AND the SAME
    `direction_word` as their corresponding rotation row (single computation, two placements)."""
    run_a_id, run_b_id = rotation_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    session_delta = payload["session_delta"]
    sector_rotation = session_delta["rotation"]["sector"]
    rotation_by_label = {row["label"]: row for row in sector_rotation["gaining"] + sector_rotation["losing"]}
    sector_changes = {c["label"]: c for c in session_delta["changes"] if c["kind"] == "sector"}
    for label, rotation_row in rotation_by_label.items():
        change_entry = sector_changes[label]
        assert change_entry["delta"] == rotation_row["delta"]
        assert change_entry["direction_word"] == rotation_row["direction_word"]


def test_rotation_no_prior_run_explicit_no_comparison_state(engine, cfg, rotation_run_pair):
    """TC-9: `previous_run is None` renders each kind's explicit no-prior-run state — empty sides, zero
    counts, no direction words — consistent with `session_delta`'s own top-level no-prior-run branch."""
    run_a_id, _run_b_id = rotation_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        payload = compass.build_manifest_payload(session, run_a, None, cfg)
    assert payload["session_delta"]["prior_as_of"] is None
    rotation = payload["session_delta"]["rotation"]
    for kind_block in rotation.values():
        assert kind_block["gaining"] == [] and kind_block["losing"] == []
        assert kind_block["shown_count"] == 0
        assert kind_block["suppressed_count"] == 0
        assert kind_block["residual_count"] == 0
    assert rotation["sector"]["configured_total"] == len(cfg.etfs.sector) + len(cfg.etfs.industry)
    assert rotation["theme"]["configured_total"] == len(cfg.themes)


def test_rotation_full_universe_closure_and_residual_isolation(engine, cfg, full_universe_rotation_runs):
    """TC-7 (accounting closure against the configured group counts) + TC-8/TC-15 (dev handoff citation:
    this fixture + test — an above-threshold mover excluded SOLELY by `rotation_top_k`, isolated from the
    separate `rank_move_min` condition, per iter-35's lesson). See `full_universe_rotation_runs`'s
    docstring for the exact math this test's concrete numbers depend on."""
    run_a_id, run_b_id, n_sector, n_theme = full_universe_rotation_runs
    assert cfg.compass.delta.rank_move_min == 2  # this test's concrete numbers depend on the real config
    assert cfg.compass.delta.rotation_top_k == 5
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    rotation = payload["session_delta"]["rotation"]

    sector = rotation["sector"]
    assert sector["configured_total"] == n_sector == 31
    assert len(sector["gaining"]) == 5 and len(sector["losing"]) == 5
    assert sector["shown_count"] == 10
    assert sector["suppressed_count"] == 1  # the exact-middle pair, delta 0
    assert sector["residual_count"] == 20  # 10 gainers + 10 losers cleared the threshold but beyond the cap
    assert sector["shown_count"] + sector["suppressed_count"] + sector["residual_count"] == n_sector

    theme = rotation["theme"]
    assert theme["configured_total"] == n_theme == 11
    assert len(theme["gaining"]) == 5 and len(theme["losing"]) == 5
    assert theme["shown_count"] == 10
    assert theme["suppressed_count"] == 1
    assert theme["residual_count"] == 0  # exactly at the cap on both sides here — nothing left over
    assert theme["shown_count"] + theme["suppressed_count"] + theme["residual_count"] == n_theme


def test_rotation_top_k_is_config_driven(cfg):
    """`rotation_top_k` lives ONLY in `compass.delta.*` (anti-goal: No magic numbers) — a direct typed-
    config read, never a literal in the engine module (test_no_magic_numbers.py's static scan enforces
    the code side; this proves the config wiring)."""
    assert cfg.compass.delta.rotation_top_k > 0


def test_rotation_no_composite_score_field_anywhere(engine, cfg, rotation_run_pair):
    """AG-11: a rotation row carries only the stored ranks, their signed difference, and the served word
    — no new blended/composite field."""
    run_a_id, run_b_id = rotation_run_pair
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
    allowed = {"label", "from", "to", "delta", "direction_word", "drill_href"}
    for kind_block in payload["session_delta"]["rotation"].values():
        for row in kind_block["gaining"] + kind_block["losing"]:
            assert set(row.keys()) == allowed
