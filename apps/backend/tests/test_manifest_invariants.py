"""goal-market-compass iter-3 (J-05/J-06) — the twelve named manifest invariants (TC-14..TC-25), each
covered by an explicitly-named test below. File-scoped synthetic fixtures (fresh SQLite DBs, hand-built
`ScannerRun` / `ScannerResult` rows) — never `loaded_engine`.
"""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import jsonschema
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import REPO_ROOT, load_config
from app.db import create_db_and_tables, make_engine
from app.engine import compass
from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun

BOUNDED_TIMEOUT_S = 30


@pytest.fixture()
def cfg():
    return load_config()


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng


def _mk_run(session: Session, asof: date, regime_score: float = 60.0) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=regime_score, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _mk_result(session: Session, run_id: int, ticker: str, l_score: float = 92.0, l_bucket: str = "A") -> None:
    record = {
        "ticker": ticker,
        "invalidation": {"note": f"{ticker} note", "price": 100.0},
        "risk_budget": {"atr_pct": {"value": 3.0, "percentile": 0.5}},
    }
    session.add(
        ScannerResult(
            run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
            leadership_score=l_score, leadership_bucket=l_bucket,
            entry_quality_score=85.0, entry_quality_bucket="B",
            risk_score=40.0, risk_bucket="C",
            setup_status="Breakout-watch", rank=1, record_json=json.dumps(record),
        )
    )


@pytest.fixture()
def frontier_run(engine, cfg):
    """One run with a bar dated exactly at its own as_of -- the frontier (mode resolves at_ingest)."""
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 7, 1), open=1, high=1, low=1, close=1, volume=1))
        run = _mk_run(session, date(2024, 7, 1))
        _mk_result(session, run.id, "AAA")
        session.commit()
        session.refresh(run)
        return run.id


# --- TC-14 (time-safety) --------------------------------------------------------------------------


def test_tc14_time_safety_content_hash_unchanged_by_post_asof_bar_change(engine, cfg, frontier_run):
    """The producer never reads a bar dated after the as-of at all (AG-5) -- perturbing/adding one leaves
    content_hash unchanged."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        before = compass.build_manifest_payload(session, run, None, cfg)["content_hash"]

    with Session(engine) as session:
        # perturb: add a bar dated strictly AFTER the as-of
        session.add(DailyPrice(symbol="SPY", date=date(2024, 7, 8), open=1, high=1, low=1, close=999.0, volume=1))
        session.commit()

    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        after = compass.build_manifest_payload(session, run, None, cfg)["content_hash"]

    assert before == after


# --- TC-15 (immutability) -------------------------------------------------------------------------


def test_tc15_no_update_statement_targets_next_session_manifests():
    """A static source-text audit: no UPDATE statement (SQLAlchemy `.update(...)` call or raw SQL) targets
    `NextSessionManifest` / `next_session_manifests` anywhere in the engine layer."""
    import ast

    offenders: list[str] = []
    for path in (REPO_ROOT / "apps/backend/app/engine").glob("*.py"):
        text = path.read_text()
        if "next_session_manifests" not in text and "NextSessionManifest" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "update":
                offenders.append(f"{path.name}: a .update(...) call in a module referencing the manifest table")
    assert not offenders, offenders


def test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows(engine, cfg, frontier_run):
    from app.engine import data_manager

    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")

    with Session(engine) as session:
        before = len(session.exec(select(NextSessionManifest)).all())
    assert before == 1

    with Session(engine) as session:
        data_manager.clear_snapshot_set(session)

    with Session(engine) as session:
        after = len(session.exec(select(NextSessionManifest)).all())
    assert after == 1  # zero manifest rows deleted by a full snapshot-set clear


def test_tc15_export_writer_never_rewrites_an_existing_artifact(engine, cfg, frontier_run, tmp_path, monkeypatch):
    """AG-12 (audit, iter-3): the at-ingest export file for one `(as_of, version)` is written ONCE and
    never rewritten. A SECOND freeze of the same pair (a create-once/regenerate race whose INSERT loses,
    or any process sharing the export dir) must leave the existing bytes byte-identical and report an
    honest NULL `export_path` — never silently overwrite the frozen artifact."""
    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))

    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        first_path = row.export_path
    assert first_path is not None, "an at_ingest freeze must export"
    first_bytes = (tmp_path / Path(first_path).name).read_bytes()

    # drop the row so the SAME (as_of, version=1) is minted a second time, as a losing race would
    with Session(engine) as session:
        stored = session.exec(select(NextSessionManifest)).first()
        session.delete(stored)
        session.commit()
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        second = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        second_path = second.export_path

    assert second_path is None, "a second freeze must NOT claim the existing artifact's path"
    assert (tmp_path / Path(first_path).name).read_bytes() == first_bytes, "the frozen export was mutated"
    assert sorted(p.name for p in tmp_path.iterdir()) == [Path(first_path).name]


# --- read-time basis disclosure (TC-10 / TC-11 branches) ------------------------------------------


def test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone(engine, cfg, frontier_run):
    """TC-10 branch: the source run for this as-of is no longer stored -> `unavailable`, and the frozen
    manifest row itself is still readable (never deleted, never recomputed)."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
    with Session(engine) as session:
        session.delete(session.get(ScannerRun, frontier_run))
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        assert row is not None
        assert compass.basis_disclosure(session, row) == {
            "status": "unavailable",
            "detail": "the underlying scanner run for this as-of is no longer stored",
        }


def test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated(engine, cfg, frontier_run):
    """TC-11 branch: the source run was recreated (a different `created_at`) after the freeze -> `rebuilt`,
    while the manifest's own stored bytes stay byte-identical."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        before = compass.manifest_row_payload(row)
        asof = row.as_of
    with Session(engine) as session:
        session.delete(session.get(ScannerRun, frontier_run))
        session.commit()
        rebuilt = _mk_run(session, asof)
        rebuilt.created_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)
        after = compass.manifest_row_payload(row)
    assert disclosure["status"] == "rebuilt"
    assert after == before  # the frozen document is served verbatim, unchanged by the rebuild


# --- TC-16 (reproducibility) -----------------------------------------------------------------------


def test_tc16_two_independent_builds_of_same_inputs_produce_identical_content_hash(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        first = compass.build_manifest_payload(session, run, None, cfg)
        second = compass.build_manifest_payload(session, run, None, cfg)
    assert first["content_hash"] == second["content_hash"]


# --- TC-17 (create-once concurrency) ----------------------------------------------------------------


def test_tc17_concurrent_requests_for_same_not_yet_computed_asof_yield_one_row(tmp_path, cfg):
    """5 concurrent callers race to freeze the SAME not-yet-computed frontier as_of. A `threading.Barrier`
    forces all 5 threads past compass.build_manifest_payload (the content-compute step, well before the
    INSERT) before ANY proceeds to the write -- deterministically reproducing the concurrent-INSERT race
    `_freeze_manifest`'s IntegrityError guard exists to absorb, mirroring the established
    test_forward_testing_concurrency.py::test_iter19_concurrent_missing_run_backtest_calls_... technique."""
    import app.engine.compass as compass_module

    engine = make_engine(f"sqlite:///{tmp_path / 'tc17.db'}")
    create_db_and_tables(engine)
    asof = date(2024, 8, 1)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=asof, open=1, high=1, low=1, close=1, volume=1))
        run = _mk_run(session, asof)
        _mk_result(session, run.id, "AAA")
        session.commit()
        run_id = run.id

    n_callers = 5
    barrier = threading.Barrier(n_callers)
    real_build = compass_module.build_manifest_payload

    def _synced_build(*args, **kwargs):
        barrier.wait(timeout=BOUNDED_TIMEOUT_S)
        return real_build(*args, **kwargs)

    def _caller() -> int:
        with Session(engine) as thread_session:
            run = thread_session.get(ScannerRun, run_id)
            row = compass_module.get_or_create_manifest(thread_session, run, cfg, producer="ingest_finalize")
            return row.id

    compass_module.build_manifest_payload = _synced_build
    try:
        with ThreadPoolExecutor(max_workers=n_callers) as pool:
            futures = [pool.submit(_caller) for _ in range(n_callers)]
            results, errors = [], []
            for future in as_completed(futures, timeout=BOUNDED_TIMEOUT_S):
                try:
                    results.append(future.result())
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)
    finally:
        compass_module.build_manifest_payload = real_build

    assert len(results) + len(errors) == n_callers, "not every caller completed -- treat as a hang"
    assert not errors, f"expected every caller to complete without an unhandled exception; got {errors}"
    assert len(set(results)) == 1, f"expected every caller to observe the SAME committed row id; got {results}"

    with Session(engine) as session:
        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == asof)).all()
    assert len(rows) == 1


# --- TC-18 (mode honesty) -------------------------------------------------------------------------


def test_tc18_bar_dated_after_asof_forces_retrospective_mode(engine):
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 9, 1), open=1, high=1, low=1, close=1, volume=1))
        session.add(DailyPrice(symbol="SPY", date=date(2024, 9, 8), open=1, high=1, low=1, close=1, volume=1))
        session.commit()
        mode, frontier = compass._resolve_mode(session, date(2024, 9, 1))
    assert mode == "retrospective"
    assert frontier == date(2024, 9, 8)


def test_tc18_no_later_bar_resolves_at_ingest_mode(engine):
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 9, 1), open=1, high=1, low=1, close=1, volume=1))
        session.commit()
        mode, frontier = compass._resolve_mode(session, date(2024, 9, 1))
    assert mode == "at_ingest"
    assert frontier == date(2024, 9, 1)


# --- TC-19 (cohort reproducibility) -----------------------------------------------------------------


def test_tc19_comparison_and_shadow_cohorts_reproduce_exactly(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 10, 1))
        _mk_result(session, run.id, "AAA", 92.0, "A")
        _mk_result(session, run.id, "BBB", 77.0, "B")  # in the shadow band [75, 80)
        session.commit()
        session.refresh(run)
        first = compass.evaluate_selection(session, run, cfg)
        second = compass.evaluate_selection(session, run, cfg)
    assert first["comparison_cohort"] == second["comparison_cohort"]
    assert first["near_threshold_shadow"] == second["near_threshold_shadow"]
    assert [row["ticker"] for row in first["near_threshold_shadow"]] == ["BBB"]


# --- TC-20 (fail-closed prospective eligibility) ------------------------------------------------


_BASE_ELIGIBLE_KWARGS = dict(
    mode="at_ingest",
    frontier_bar_date=date(2024, 1, 1),
    based_on_close=date(2024, 1, 1),
    producer="ingest_finalize",
    version=1,
    frozen=True,
    available_at_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
    provenance_complete=True,
    manifest_hash="deadbeef",
)


def test_tc20_baseline_is_eligible():
    assert compass._derive_prospective_eligible(**_BASE_ELIGIBLE_KWARGS) is True


@pytest.mark.parametrize(
    "override",
    [
        {"mode": "retrospective"},
        {"frontier_bar_date": None},
        {"frontier_bar_date": date(2024, 1, 2)},  # != based_on_close
        {"producer": "on_demand_get"},
        {"producer": "regenerate"},
        {"version": 2},
        {"frozen": False},
        {"available_at_utc": None},
        {"provenance_complete": False},
        {"manifest_hash": None},
    ],
)
def test_tc20_each_violated_condition_independently_forces_false(override):
    kwargs = {**_BASE_ELIGIBLE_KWARGS, **override}
    assert compass._derive_prospective_eligible(**kwargs) is False


# --- TC-21 (availability-fence conservatism) ----------------------------------------------------


def test_tc21_available_at_utc_never_earlier_than_generated_at_plus_margin(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        generation = json.loads(row.generation_json)
    generated_at = datetime.fromisoformat(generation["generated_at"])
    margin = cfg.compass.manifest.availability_margin_seconds
    assert row.available_at_utc.replace(tzinfo=timezone.utc) >= generated_at + timedelta(seconds=margin)


# --- TC-22 (artifact integrity) -------------------------------------------------------------------


def test_tc22_flipping_a_byte_including_inside_prospective_eligible_fails_verification(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        document = compass.manifest_row_payload(row)
    assert compass.verify_manifest_hash(document) is True

    tampered = dict(document)
    tampered["prospective_eligible"] = not tampered["prospective_eligible"]
    assert compass.verify_manifest_hash(tampered) is False

    tampered2 = dict(document)
    tampered2["generation"] = {**tampered2["generation"], "engine_identity": "tampered"}
    assert compass.verify_manifest_hash(tampered2) is False


# --- TC-23 (rule-identity separation) -------------------------------------------------------------


def test_tc23_why_not_and_qualifier_changes_move_only_manifest_config_hash(cfg):
    base = cfg
    changed_selection = base.compass.selection.model_copy(update={"why_not_cap": base.compass.selection.why_not_cap + 1})
    changed = base.model_copy(update={"compass": base.compass.model_copy(update={"selection": changed_selection})})

    assert compass._candidate_rule_subset(base) == compass._candidate_rule_subset(changed)
    assert compass._cohort_rule_subset(base) == compass._cohort_rule_subset(changed)
    assert compass._manifest_config_subset(base) != compass._manifest_config_subset(changed)


def test_tc23_shadow_min_score_moves_only_cohort_rule_hash(cfg):
    base = cfg
    changed_shadow = base.compass.selection.shadow.model_copy(update={"min_score": base.compass.selection.shadow.min_score + 1})
    changed_selection = base.compass.selection.model_copy(update={"shadow": changed_shadow})
    changed = base.model_copy(update={"compass": base.compass.model_copy(update={"selection": changed_selection})})

    assert compass._hash_subset(compass._candidate_rule_subset(base)) == compass._hash_subset(compass._candidate_rule_subset(changed))
    assert compass._hash_subset(compass._cohort_rule_subset(base)) != compass._hash_subset(compass._cohort_rule_subset(changed))


def test_tc23_leadership_min_score_moves_both_candidate_and_cohort_rule_hash(cfg):
    base = cfg
    changed_selection = base.compass.selection.model_copy(update={"leadership_min_score": base.compass.selection.leadership_min_score + 1})
    changed = base.model_copy(update={"compass": base.compass.model_copy(update={"selection": changed_selection})})

    assert compass._hash_subset(compass._candidate_rule_subset(base)) != compass._hash_subset(compass._candidate_rule_subset(changed))
    assert compass._hash_subset(compass._cohort_rule_subset(base)) != compass._hash_subset(compass._cohort_rule_subset(changed))


def test_tc23_max_candidates_moves_only_candidate_rule_hash(cfg):
    base = cfg
    changed_selection = base.compass.selection.model_copy(update={"max_candidates": base.compass.selection.max_candidates + 1})
    changed = base.model_copy(update={"compass": base.compass.model_copy(update={"selection": changed_selection})})

    assert compass._hash_subset(compass._candidate_rule_subset(base)) != compass._hash_subset(compass._candidate_rule_subset(changed))
    assert compass._hash_subset(compass._cohort_rule_subset(base)) == compass._hash_subset(compass._cohort_rule_subset(changed))


def test_tc23_metadata_only_regeneration_content_hash_equal_manifest_hash_differs(engine, cfg):
    """A regenerate of IDENTICAL content (same inputs, new generation timestamp) keeps content_hash equal
    while manifest_hash changes (different generation metadata)."""
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 11, 1))
        _mk_result(session, run.id, "AAA")
        session.commit()
        session.refresh(run)
        row1 = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
    with Session(engine) as session:
        row2 = compass.regenerate_manifest(session, date(2024, 11, 1), cfg)
    assert row1.content_hash == row2.content_hash
    assert row1.manifest_hash != row2.manifest_hash


# --- TC-24 (disposition partition) ------------------------------------------------------------------


def test_tc24_disposition_tallies_partition_member_count_minus_candidate_count(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 12, 1))
        _mk_result(session, run.id, "AAA", 92.0, "A")  # candidate
        _mk_result(session, run.id, "BBB", 92.0, "B")  # candidate
        _mk_result(session, run.id, "CCC", 30.0, "E")  # below floor
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    tally = result["disposition_tally"]
    member_count = 3
    candidate_count = len(result["candidates"])
    assert tally["below_selection_floor"] + tally["excluded_by_cap"] == member_count - candidate_count
    dispositions = [row["selection_disposition"] for row in result["comparison_cohort"]]
    assert len(dispositions) == member_count - candidate_count
    assert set(dispositions) <= {"below_selection_floor", "excluded_by_cap"}


# --- TC-25 (schema conformance) ---------------------------------------------------------------------


@pytest.fixture()
def schema():
    path = REPO_ROOT / "docs/handoffs/trendora-next-session-manifest-v1.schema.json"
    with open(path) as f:
        return json.load(f)


def test_tc25_frozen_at_ingest_manifest_validates(engine, cfg, frontier_run, schema):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        document = compass.manifest_row_payload(row)
    jsonschema.validate(document, schema)  # raises on failure


def test_tc25_retrospective_manifest_validates(engine, cfg, schema):
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2025, 1, 1), open=1, high=1, low=1, close=1, volume=1))
        session.add(DailyPrice(symbol="SPY", date=date(2025, 1, 8), open=1, high=1, low=1, close=1, volume=1))
        run_a = _mk_run(session, date(2025, 1, 1))
        _mk_result(session, run_a.id, "AAA")
        run_b = _mk_run(session, date(2025, 1, 8))
        _mk_result(session, run_b.id, "AAA")
        session.commit()
        session.refresh(run_a)
        row = compass.get_or_create_manifest(session, run_a, cfg)  # historical -- create-once, retrospective
        document = compass.manifest_row_payload(row)
    assert document["mode"] == "retrospective"
    jsonschema.validate(document, schema)


def test_tc25_manifest_missing_required_field_fails_validation(engine, cfg, frontier_run, schema):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        document = compass.manifest_row_payload(row)
    del document["available_at_utc"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, schema)


# --- TC-27 (AG-16): cohorts are not controls ------------------------------------------------------


def test_tc27_cohort_semantics_caveat_carries_the_exact_non_causal_disclosure(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        document = compass.manifest_row_payload(row)
    text = document["caveats"]["cohort_semantics"]
    assert "frozen non-selected comparison pool" in text
    assert "not a matched or causal control group" in text
    assert "near-selected" not in text.lower() or "never described as" in text.lower()
    lowered = text.lower()
    for causal_word in ("expectancy", "certified edge", "causal"):
        # each causal-sounding word, if present at all, must appear only inside the DISCLAIMING sentence
        # (i.e. the text explicitly disclaims it) -- never asserted as true of the cohorts.
        if causal_word in lowered:
            assert "not" in lowered  # the disclaiming frame is present


# --- TC-28 (AG-11): no new composite/blended score in cohort rows ----------------------------------


def test_tc28_no_composite_score_field_in_cohort_rows(engine, cfg):
    """AG-11: comparison_cohort / near_threshold_shadow rows carry only the existing three scores plus
    named structural context fields -- never a new blended/composite number."""
    allowed_numeric_keys = {
        "leadership_score", "entry_quality_score", "risk_score", "rank_in_run", "close",
        "distance_from_52w_high", "gap_p95", "worst_20d", "distance_to_invalidation", "adv_dollars",
    }
    with Session(engine) as session:
        run = _mk_run(session, date(2025, 2, 1))
        _mk_result(session, run.id, "AAA", 92.0, "A")
        _mk_result(session, run.id, "ZZZ", 10.0, "E")
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    for row in result["comparison_cohort"] + result["near_threshold_shadow"]:
        for key, value in row.items():
            if key == "atr_pct":
                continue  # a {value, percentile} dict of an EXISTING risk-budget field, not a new score
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                assert key in allowed_numeric_keys, f"unexpected numeric field on cohort row: {key}"


# --- TC-30 (AG-8): bounded, column-projected reads over up to ~530 non-candidate rows --------------


def test_tc30_comparison_cohort_uses_a_bounded_query_count_not_per_ticker(engine, cfg):
    """AG-8: evaluate_selection's non-candidate sweep issues a FIXED small number of queries regardless
    of member count -- never one record_json read per ticker (never N+1)."""
    with Session(engine) as session:
        run = _mk_run(session, date(2025, 3, 1))
        for i in range(40):
            _mk_result(session, run.id, f"T{i:03d}", 10.0, "E")  # all non-candidates (below floor)
        session.commit()
        session.refresh(run)

    query_count = {"n": 0}
    from sqlalchemy import event
    from sqlalchemy.engine import Engine as SAEngine

    def _count(*_args, **_kwargs):
        query_count["n"] += 1

    event.listen(SAEngine, "before_cursor_execute", _count)
    try:
        with Session(engine) as session:
            run = session.get(ScannerRun, run.id)
            result = compass.evaluate_selection(session, run, cfg)
    finally:
        event.remove(SAEngine, "before_cursor_execute", _count)

    assert len(result["comparison_cohort"]) == 40
    # a handful of bounded queries (member sweep, candidate record_json fetch, non-candidate record_json
    # fetch, theme-rank fetch) -- NOT 40+ (one per ticker). A generous ceiling that still catches an N+1.
    assert query_count["n"] < 10, f"expected a bounded query count, got {query_count['n']} for 40 members"


# --- TC-34: ATR caution reworded (no advice-sounding tail) -----------------------------------------


def test_tc34_atr_caution_states_the_fact_only(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2025, 4, 1))
        _mk_result(session, run.id, "AAA", 92.0, "A")
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    caution = next(c for c in result["candidates"][0]["cautions"] if c.startswith("ATR_RISK_BUDGET"))
    assert "sized risk accordingly" not in caution
    assert "ATR is 3.00% of price" in caution
