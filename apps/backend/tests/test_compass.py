"""app.engine.compass (goal-market-compass iter-2, J-03/J-04) — narrative, selection, manifest assembly.

File-scoped synthetic fixtures (fresh in-memory SQLite DB, hand-built `ScannerRun` / `ScannerResult` /
`MarketPhaseCache` rows) — never `loaded_engine`. `MarketPhaseCache` is pre-populated directly (keyed via
the SAME `_cache_version` the real cache uses) so these tests need no real price history at all.
"""
from __future__ import annotations

import ast
import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import load_config
from app.engine import compass
from app.engine import market_phase as market_phase_module
from app.models import MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun


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
      CCC: L=77 B, E=55 D, R=50 C  -> fails entry_min_score (70) -> near-miss why-not (leadership 77 >= floor 75)
      DDD: L=30 E, E=20 E, R=90 E  -> fails everything, leadership far below why_not_floor -> tally only, no entry
      EEE: L=95 A, E=90 A, R=35 B  -> qualifies, no risk_budget key at all (honest-NA caution path)
    """
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 3, 1))
        _mk_result(session, run.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
        _mk_result(session, run.id, "BBB", 88.0, "A", 78.0, "B", 45.0, "C")
        _mk_result(session, run.id, "CCC", 77.0, "B", 55.0, "D", 50.0, "C")
        _mk_result(session, run.id, "DDD", 30.0, "E", 20.0, "E", 90.0, "E")
        _mk_result(session, run.id, "EEE", 95.0, "A", 90.0, "A", 35.0, "B", atr_value=None)
        session.commit()
        session.refresh(run)
        return run.id


# --- selection (J-04) ---------------------------------------------------------------------------


def test_candidates_match_stored_scores_and_word_maps(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    by_ticker = {c["ticker"]: c for c in result["candidates"]}
    assert set(by_ticker) == {"AAA", "BBB", "EEE"}
    aaa = by_ticker["AAA"]
    assert aaa["leadership_score"] == 92.0
    assert aaa["leadership_word"] == cfg.compass.vocabulary.leadership_words["A"]
    assert aaa["entry_word"] == cfg.compass.vocabulary.entry_words["B"]
    assert aaa["risk_word"] == cfg.compass.vocabulary.risk_words["C"]
    assert aaa["invalidation"] == "AAA invalidates below its 50-DMA (100.00)."


def test_checklist_verdicts_reproduce_inclusion(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    for candidate in result["candidates"]:
        assert all(row["verdict"] == "Pass" for row in candidate["checklist"])
        assert {row["condition"] for row in candidate["checklist"]} == {
            "leadership_min_score", "entry_min_score", "risk_max_score",
        }
        assert all(row["met"] is True for row in candidate["what_would_change"])


def test_why_not_near_miss_has_failed_conditions_with_distance(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
    assert "CCC" in why_not_by_ticker  # leadership 77 >= why_not_floor 75 -> near-miss, individually listed
    failed = why_not_by_ticker["CCC"]["failed_conditions"]
    assert any(f["condition"] == "entry_min_score" for f in failed)
    entry_fail = next(f for f in failed if f["condition"] == "entry_min_score")
    assert entry_fail["actual"] == 55.0
    assert entry_fail["threshold"] == cfg.compass.selection.entry_min_score
    assert entry_fail["distance"] == pytest.approx(cfg.compass.selection.entry_min_score - 55.0)
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
    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, capped_cfg)
    assert len(result["candidates"]) == 2
    assert result["disposition_tally"]["excluded_by_cap"] == 1  # AAA/BBB/EEE qualify, cap keeps top 2
    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
    cut_ticker = ({"AAA", "BBB", "EEE"} - {c["ticker"] for c in result["candidates"]}).pop()
    assert why_not_by_ticker[cut_ticker]["failed_conditions"] == []  # passed everything; only the cap cut it


def test_candidates_empty_reason_when_nothing_qualifies(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 3, 8))
        _mk_result(session, run.id, "ZZZ", 10.0, "E", 10.0, "E", 95.0, "E")
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    assert result["candidates"] == []
    assert isinstance(result["candidates_empty_reason"], str) and result["candidates_empty_reason"]


def test_risk_off_regime_adds_caution_to_every_candidate(engine, cfg, selection_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        run.regime_label = "Risk-off"
        session.add(run)
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    assert len(result["candidates"]) == 3
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


def test_shadow_cohort_never_appears_in_selection_payload(engine, cfg, selection_run):
    """TC-20 / the shadow key is reserved (config only) but computes/renders nothing this iteration."""
    with Session(engine) as session:
        run = session.get(ScannerRun, selection_run)
        result = compass.evaluate_selection(session, run, cfg)
    serialized = json.dumps(result).lower()
    assert "shadow" not in serialized


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
    assert facts["candidate_count"] == len(selection["candidates"]) == 3
    assert "3" in focus["text"]


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
    run_a_id, run_b_id = two_runs_with_phase
    calls = {"n": 0}
    original = compass.build_manifest_payload

    def counting_build(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(compass, "build_manifest_payload", counting_build)

    with Session(engine) as session:
        run_b = session.get(ScannerRun, run_b_id)
        first_row = compass.get_or_create_manifest(session, run_b, cfg)
        assert calls["n"] == 1
        second_row = compass.get_or_create_manifest(session, run_b, cfg)
        assert calls["n"] == 1  # TC-1: zero ADDITIONAL producer calls on the warm hit
        assert first_row.id == second_row.id
        assert first_row.content_hash == second_row.content_hash

    with Session(engine) as session:
        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 4, 8))).all()
        assert len(rows) == 1  # never duplicated


def test_manifest_row_payload_matches_build_manifest_payload_content(engine, cfg, two_runs_with_phase):
    run_a_id, run_b_id = two_runs_with_phase
    with Session(engine) as session:
        run_a = session.get(ScannerRun, run_a_id)
        run_b = session.get(ScannerRun, run_b_id)
        built = compass.build_manifest_payload(session, run_b, run_a, cfg)
        row = compass.get_or_create_manifest(session, run_b, cfg)
        served = compass.manifest_row_payload(row)
    assert served["session_delta"] == built["session_delta"]
    assert served["narrative"] == built["narrative"]
    assert served["selection"] == built["selection"]
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
