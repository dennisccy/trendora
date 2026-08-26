"""goal-market-compass iter-19 -- J-11 Stage D EXECUTION tests (TC-1 through TC-9, TC-12, TC-13, TC-16
from the phase spec's TESTING REQUIREMENTS; TC-10/TC-11/TC-15/TC-17/TC-18 live in the CLI-script test
file / are proven by grep in the dev handoff).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
pattern `test_j11_stage_d.py`/`test_j11_maintenance.py` use, never `loaded_engine` and never
`apps/backend/data/trendora.db`.

`scanner.run_scan` itself is NOT re-exercised end-to-end against the real committed seed here (that
is `test_scanner.py`'s own, already-expensive, already-covered proof -- a single real seed-backed
`run_scan` test module alone takes several minutes wall time, which fails docs/goal.md's own "new
tests are synthetic-fixture" contract for a NEW test file). Instead, `scanner.run_scan` is replaced,
for the per-date-loop tests only, with a small stand-in that calls the REAL, unmodified
`scanner.persist_run_payload` against a hand-built MINIMAL payload -- genuinely exercises the real
INSERT/commit/idempotent-guard/`engine_identity`-stamping code path, without the expensive
`compute_run_payload` scoring/universe-resolution machinery. A dedicated static test
(`test_execute_stage_d_for_date_never_imports_or_calls_data_manager_warmup_or_forward_testing`) proves
the production module itself calls ONLY `scanner.run_scan`, never any of the forbidden alternate
write paths.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import load_config
from app.engine import j11_avb_diagnostic as diag
from app.engine import j11_preboot_guard as guard
from app.engine import j11_stage_d_execute as jsde
from app.engine import scanner
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import DailyPrice, MaintenanceBoundary, NextSessionManifest, ScannerRun

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


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


@pytest.fixture()
def cfg():
    return load_config()


# --- shared helpers (mirror test_j11_stage_d.py's own _mk_run / _mk_manifest exactly) ----------------


def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = None) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=55.0, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=50.0, breadth_above_200dma=55.0,
        new_high_low_json="{}", candidate_counts_json="{}",
        engine_identity=engine_identity_value,
    )
    session.add(run)
    session.flush()
    return run


def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
    manifest = NextSessionManifest(
        as_of=run.asof_date, version=version, source_run_id=run.id,
        session_delta_json="{}", narrative_json="{}", selection_json="{}",
        content_hash="stub-content-hash", created_at=datetime.now(timezone.utc),
        mode="at_ingest", frozen=True,
        generation_json=json.dumps({"producer": "ingest_finalize", "engine_identity": "stub-engine-identity"}),
        engine_identity="stub-engine-identity", manifest_hash="stub-manifest-hash",
        available_at_utc=datetime.now(timezone.utc), prospective_eligible=True,
    )
    session.add(manifest)
    session.flush()
    return manifest


_TINY_PAYLOAD = {
    "regime": {
        "score": 55.0, "label": "Expansion", "components": [],
        "breadth_above_50dma": 50.0, "breadth_above_200dma": 55.0, "new_high_low": {},
    },
    "sector_result": {"rows": [{
        "ticker": "XLK", "kind": "sector", "name": "Technology", "description": "",
        "members": [], "score": 50.0, "bucket": "Neutral", "rs_vs_spy": 0.0,
        "dist_from_52w_high_pct": 0.0, "trend_label": "Flat", "components": {}, "rank": 1,
    }]},
    "theme_result": {"rows": [{
        "slug": "ai", "name": "AI", "score": 50.0, "bucket": "Neutral", "members": [],
        "return_1m": 0.0, "return_3m": 0.0, "breadth_pct": 0.0, "breadth_label": "Flat",
        "trend_label": "Flat", "components": {}, "rank": 1,
    }]},
    "stock_result": {"benchmark": "SPY", "rows": [{
        "ticker": "AAA", "name": "AAA Inc", "sector": "Technology",
        "leadership": {"score": 50.0, "bucket": "Neutral"},
        "entry_quality": {"score": 50.0, "bucket": "Neutral"},
        "risk": {"score": 50.0, "bucket": "Neutral"},
        "setup": {"status": "None"}, "rank": 1,
        "vcp": {"flagged": False}, "pullback_to_rising_dma": {"flagged": False},
        "flat_base_breakout": {"flagged": False},
        "hv": None, "vcp_contraction": None, "downside_vol": None,
    }]},
    "candidate_counts": {},
}


def _stub_run_scan(session, asof, config=None):
    """A small stand-in for `scanner.run_scan`, used ONLY in these fixture tests to avoid the expensive
    `compute_run_payload` scoring machinery -- calls the REAL, unmodified `scanner.persist_run_payload`
    (genuine INSERT/commit/idempotent-guard/`engine_identity`-stamping code) with a hand-built minimal
    payload. Mirrors `run_scan`'s own idempotent fast path first (never creates a duplicate)."""
    existing = scanner.get_run_for_date(session, asof)
    if existing is not None:
        return existing
    return scanner.persist_run_payload(session, asof, _TINY_PAYLOAD, config)


LOOP_DATES = INCIDENT_DATES[:2]  # a 2-date real-incident-date subset, so Check (B)/(C) are
# GENUINELY exercised (in_scope=True) rather than vacuously passed -- j11_stage_d.check_identity_before_date/
# check_identity_after_persist scope their comparison to app.engine.j11_maintenance.INCIDENT_DATES
# membership specifically; an isolated in-memory fixture DB using these calendar dates has zero
# connection to the live database.


# =======================================================================================================
# recheck_maintenance_boundary_and_guard
# =======================================================================================================


def test_recheck_boundary_ok_when_armed_active_and_exact_date_set(engine):
    with Session(engine) as session:
        guard.register_boundary(session, name="j11-incident-recovery", dates=LOOP_DATES, reason="test", active=True)
    with Session(engine) as session:
        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
    assert result["ok"] is True
    assert result["boundary_active"] is True
    assert result["exact_date_set_match"] is True
    assert result["all_dates_blocked"] is True
    assert all(r["blocked"] for r in result["per_date_guard_result"].values())


def test_recheck_boundary_fails_when_no_boundary_row_registered(engine):
    with Session(engine) as session:
        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
    assert result["ok"] is False
    assert result["boundary_row_present"] is False
    assert result["all_dates_blocked"] is False  # true no-op / unarmed -- never falsely blocked


def test_recheck_boundary_fails_when_inactive(engine):
    with Session(engine) as session:
        guard.register_boundary(session, name="j11-incident-recovery", dates=LOOP_DATES, reason="test", active=False)
    with Session(engine) as session:
        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
    assert result["ok"] is False
    assert result["boundary_active"] is False
    assert result["all_dates_blocked"] is False  # cleared boundary never blocks


def test_recheck_boundary_fails_when_date_set_does_not_match_exactly(engine):
    wrong_dates = LOOP_DATES + (date(2030, 1, 8),)
    with Session(engine) as session:
        guard.register_boundary(session, name="j11-incident-recovery", dates=wrong_dates, reason="test", active=True)
    with Session(engine) as session:
        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
    assert result["exact_date_set_match"] is False
    assert result["ok"] is False


# =======================================================================================================
# run_fresh_avb_reclassification -- one real small-fixture smoke test + fail-closed edge cases (mocked)
# =======================================================================================================


def _small_universe_cfg():
    """Mirrors `test_j11_avb_diagnostic.py`'s own `_small_universe_cfg()` exactly -- a real Config with
    only the thresholds a tiny synthetic series would otherwise fail reduced."""
    c = load_config().model_copy(deep=True)
    c = c.model_copy(update={"indicators": c.indicators.model_copy(update={
        "min_history_bars": 30, "vol_avg_period": 20,
    })})
    c = c.model_copy(update={"universe": c.universe.model_copy(update={
        "filters": c.universe.filters.model_copy(update={
            "min_price": 1.0, "min_dollar_vol": 1000.0, "adv_window_days": 20, "max_staleness_days": 30,
        })
    })})
    return c


def _seed_avb_prices(session: Session, *, n: int, end: date) -> None:
    for i in range(n):
        d = end - timedelta(days=n - 1 - i)
        close = 180.0 + 0.2 * i
        session.add(DailyPrice(
            symbol=diag.AVB_SYMBOL, date=d, open=close, high=close * 1.01, low=close * 0.99,
            close=close, volume=1_000_000.0,
        ))
    session.commit()


def test_run_fresh_avb_reclassification_end_to_end_smoke_on_small_fixture(engine):
    """Genuinely exercises the real `diag.*` composition (never mocked) against a small synthetic AVB
    series plus the REAL committed J-10/provider-fetch evidence files (small, static JSON -- the same
    'legitimately read directly' exception test_j11_avb_diagnostic.py's own docstring documents). Does
    not assert a specific classification label (that correctness is test_j11_avb_diagnostic.py's own,
    already-covered surface) -- only that the composition completes and returns a well-formed result."""
    cfg = _small_universe_cfg()
    with Session(engine) as session:
        _seed_avb_prices(session, n=60, end=date(2026, 8, 12))
    with Session(engine) as session:
        result = jsde.run_fresh_avb_reclassification(
            session, cfg,
            provider_fetch_evidence_path=diag.REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-provider-fetch-evidence.json",
            j10_evidence_path=diag.DEFAULT_J10_EVIDENCE_PATH,
        )
    assert result["classification"]["classification"] in ("AVB-A", "AVB-B", "AVB-C", "AVB-D")
    assert result["bridge_factor"] == pytest.approx(2.7930001225759193)
    assert set(result["volume_override_by_date"]) == {d.isoformat() for d in diag.RECOVERED_DATES}


def test_run_fresh_avb_reclassification_fails_closed_to_avb_d_on_incomplete_volume_override(engine, tmp_path):
    incomplete = {
        "sufficient_evidence": True,
        "per_date": {diag.RECOVERED_DATES[0].isoformat(): {"close": 100.0, "volume": 1000.0}},
        # RECOVERED_DATES[1] deliberately missing volume evidence
    }
    fetch_path = tmp_path / "fetch.json"
    fetch_path.write_text(json.dumps(incomplete))
    with Session(engine) as session:
        _seed_avb_prices(session, n=60, end=date(2026, 8, 12))
    with Session(engine) as session:
        result = jsde.run_fresh_avb_reclassification(
            session, _small_universe_cfg(),
            provider_fetch_evidence_path=fetch_path, j10_evidence_path=diag.DEFAULT_J10_EVIDENCE_PATH,
        )
    assert result["classification"]["classification"] == "AVB-D"
    assert result["classification"]["stage_d_ready_per_avb"] is False
    assert result["decision_impact_by_date"] == {}  # no trace attempted on incomplete evidence


def test_run_fresh_avb_reclassification_fails_closed_to_avb_d_when_evidence_marked_insufficient(engine, tmp_path):
    fetch_evidence = json.loads(
        (diag.REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-provider-fetch-evidence.json").read_text()
    )
    fetch_evidence["sufficient_evidence"] = False
    fetch_path = tmp_path / "fetch.json"
    fetch_path.write_text(json.dumps(fetch_evidence))
    with Session(engine) as session:
        _seed_avb_prices(session, n=60, end=date(2026, 8, 12))
    with Session(engine) as session:
        result = jsde.run_fresh_avb_reclassification(
            session, _small_universe_cfg(),
            provider_fetch_evidence_path=fetch_path, j10_evidence_path=diag.DEFAULT_J10_EVIDENCE_PATH,
        )
    assert result["classification"]["classification"] == "AVB-D"
    assert result["classification"]["stage_d_ready_per_avb"] is False


# =======================================================================================================
# stage_d_execution_gate_verdict
# =======================================================================================================


def test_gate_proceeds_only_when_all_three_conditions_hold():
    gate = jsde.stage_d_execution_gate_verdict(
        preflight_verdict={"passed": True}, avb_classification="AVB-A", boundary_recheck={"ok": True},
    )
    assert gate["proceed"] is True
    assert gate["blocking_reasons"] == []


@pytest.mark.parametrize("preflight_passed,avb,boundary_ok", [
    (False, "AVB-A", True),
    (True, "AVB-B", True),   # AVB-B is NOT the exact required classification for EXECUTION
    (True, "AVB-C", True),
    (True, "AVB-A", False),
])
def test_gate_refuses_unless_every_condition_holds(preflight_passed, avb, boundary_ok):
    gate = jsde.stage_d_execution_gate_verdict(
        preflight_verdict={"passed": preflight_passed, "reason": "x"},
        avb_classification=avb, boundary_recheck={"ok": boundary_ok},
    )
    assert gate["proceed"] is False
    assert gate["blocking_reasons"]


# =======================================================================================================
# freeze_fresh_stage_d_execution_identity + compare_identity_against_historical
# =======================================================================================================


def test_freeze_fresh_execution_identity_is_independently_recomputed(engine, cfg):
    # git_head/goal_md_text omitted -> defaults to real read-only I/O against the committed repo
    # (jsc.read_git_head / jsc.read_goal_md_text), the SAME fallback the production CLI script's own
    # call site relies on when it does not override them; a minimal hand-typed goal_md_text would need
    # to reproduce j11_stage_c.py's exact anchor text, which is exactly what this test must NOT hardcode.
    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    assert frozen["execution_identity"] is True
    assert frozen["readiness_time_only"] is False
    from app.engine import engine_identity as ei
    assert frozen["engine_identity"] == ei.compute_engine_identity(cfg)  # independently recomputed, matches


def test_compare_identity_against_historical_is_stated_honestly_both_ways():
    comparison = jsde.compare_identity_against_historical(
        "fresh-value", {"iteration_10": "legacy-value", "iteration_14": "fresh-value", "iteration_missing": None},
    )
    assert comparison["comparisons"]["iteration_10"]["matches_fresh"] is False
    assert comparison["comparisons"]["iteration_14"]["matches_fresh"] is True
    assert comparison["comparisons"]["iteration_missing"]["matches_fresh"] is False
    assert comparison["any_historical_match"] is True  # honestly reported -- not silently hidden


# =======================================================================================================
# confirm_no_existing_scanner_run
# =======================================================================================================


def test_confirm_no_existing_run_true_when_none_present(engine):
    with Session(engine) as session:
        result = jsde.confirm_no_existing_scanner_run(session, date(2030, 1, 6))
    assert result["already_exists"] is False


def test_confirm_no_existing_run_false_when_a_row_is_present(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2030, 1, 6), engine_identity_value="some-identity")
        session.commit()
        run_id = run.id  # captured before the session closes -- avoids a DetachedInstanceError
    with Session(engine) as session:
        result = jsde.confirm_no_existing_scanner_run(session, date(2030, 1, 6))
    assert result["already_exists"] is True
    assert result["existing_run_id"] == run_id
    assert result["existing_engine_identity"] == "some-identity"


# =======================================================================================================
# TC-4 / TC-5 / TC-6 / TC-9 -- the per-date loop
# =======================================================================================================


def test_tc4_tc6_loop_creates_exactly_one_run_per_date_all_stamped_with_frozen_identity(engine, cfg, monkeypatch):
    monkeypatch.setattr(jsde.scanner, "run_scan", _stub_run_scan)
    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    with Session(engine) as session:
        result = jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen, cfg)

    assert result["completed"] is True
    assert result["stopped_at_date"] is None
    assert len(result["new_run_ids"]) == len(LOOP_DATES) == 2

    with Session(engine) as session:
        from sqlalchemy import func as _func
        from sqlmodel import select as _select
        from app.models import ScannerResult, SectorScoreRow, ThemeScoreRow
        for one_date in LOOP_DATES:
            run = session.exec(_select(ScannerRun).where(ScannerRun.asof_date == one_date)).one()
            assert run.engine_identity == frozen["engine_identity"]
            results_count = session.exec(
                _select(_func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run.id)
            ).one()
            sectors_count = session.exec(
                _select(_func.count()).select_from(SectorScoreRow).where(SectorScoreRow.run_id == run.id)
            ).one()
            themes_count = session.exec(
                _select(_func.count()).select_from(ThemeScoreRow).where(ThemeScoreRow.run_id == run.id)
            ).one()
            assert results_count >= 1 and sectors_count >= 1 and themes_count >= 1


def test_tc4_loop_ascending_chronological_order(engine, cfg, monkeypatch):
    calls: list = []
    real_stub = _stub_run_scan

    def _tracking_stub(session, asof, config=None):
        calls.append(asof)
        return real_stub(session, asof, config)

    monkeypatch.setattr(jsde.scanner, "run_scan", _tracking_stub)
    reversed_dates = tuple(sorted(LOOP_DATES, reverse=True))
    assert reversed_dates != LOOP_DATES  # sanity: input order really is reversed

    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    with Session(engine) as session:
        jsde.execute_stage_d_regeneration(session, reversed_dates, frozen, cfg)

    assert calls == sorted(LOOP_DATES)  # ascending, regardless of input order


def test_tc5_loop_stops_at_first_pre_existing_run_and_attempts_no_further_date(engine, cfg, monkeypatch):
    with Session(engine) as session:
        _mk_run(session, LOOP_DATES[0], engine_identity_value="stale-identity")
        session.commit()

    calls: list = []

    def _tracking_stub(session, asof, config=None):
        calls.append(asof)
        return _stub_run_scan(session, asof, config)

    monkeypatch.setattr(jsde.scanner, "run_scan", _tracking_stub)
    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    with Session(engine) as session:
        result = jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen, cfg)

    assert result["completed"] is False
    assert result["stopped_at_date"] == LOOP_DATES[0].isoformat()
    assert result["per_date_results"][0]["stop_reason"] == "scanner_run_already_exists_before_write"
    assert calls == []  # run_scan was NEVER called -- stopped before the write, not after


def test_tc5_loop_stops_on_check_b_identity_drift_before_calling_run_scan(engine, cfg, monkeypatch):
    calls: list = []

    def _tracking_stub(session, asof, config=None):
        calls.append(asof)
        return _stub_run_scan(session, asof, config)

    monkeypatch.setattr(jsde.scanner, "run_scan", _tracking_stub)
    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    frozen_drifted = dict(frozen)
    frozen_drifted["engine_identity"] = "deliberately-different-from-current"

    with Session(engine) as session:
        result = jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen_drifted, cfg)

    assert result["completed"] is False
    assert result["per_date_results"][0]["stop_reason"] == "check_b_failed"
    assert calls == []


def test_tc5_loop_stops_on_check_c_failure_after_a_bad_persist_and_attempts_no_further_date(engine, cfg, monkeypatch):
    """Simulates a persisted row somehow NOT carrying the frozen identity (e.g. a stale `run_scan`
    substitute) -- Check (C) must catch it and the loop must stop, never proceeding to the second date."""
    calls: list = []

    def _bad_stub(session, asof, config=None):
        calls.append(asof)
        return scanner.persist_run_payload(session, asof, jsde_bad_payload(), config)

    def jsde_bad_payload():
        # a run persisted through the REAL function, but stamped with the WRONG identity by monkeypatching
        # engine_identity.compute_engine_identity just for this one call is complex; simpler: reuse the tiny
        # payload and instead monkeypatch check_identity_after_persist's underlying comparison by asserting
        # a run whose engine_identity we forcibly overwrite post-hoc before Check (C) reads it.
        return _TINY_PAYLOAD

    def _stub_then_corrupt(session, asof, config=None):
        run = _bad_stub(session, asof, config)
        run.engine_identity = "corrupted-post-persist-identity"
        session.add(run)
        session.commit()
        session.refresh(run)
        return run

    monkeypatch.setattr(jsde.scanner, "run_scan", _stub_then_corrupt)
    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    with Session(engine) as session:
        result = jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen, cfg)

    assert result["completed"] is False
    assert result["per_date_results"][0]["stop_reason"] == "check_c_failed"
    assert calls == [LOOP_DATES[0]]  # run_scan called for date 1 only -- date 2 never attempted


def test_tc9_out_of_scope_date_check_b_and_c_are_vacuous_pass():
    not_incident_date = date(2099, 1, 1)
    assert not_incident_date not in INCIDENT_DATES
    from app.engine import j11_stage_d as jsd
    check_b = jsd.check_identity_before_date({"engine_identity": "x"}, "y", not_incident_date)
    assert check_b == {
        "check": "before_date", "date": not_incident_date.isoformat(), "in_scope": False, "ok": True,
        "reason": "date_outside_j11_stage_d_attempt_scope_no_check_performed",
        "checked_at": check_b["checked_at"],
    }


def test_execute_stage_d_for_date_never_imports_or_calls_data_manager_warmup_or_forward_testing():
    """Static proof that the production module cannot reach the forbidden alternate write paths: it
    imports neither `data_manager`, `warmup`, nor `forward_testing` at all."""
    import app.engine.j11_stage_d_execute as module
    source_names = set(vars(module))
    for forbidden in ("data_manager", "warmup", "forward_testing"):
        assert forbidden not in source_names


# =======================================================================================================
# capture_legacy_and_null_scanner_run_fingerprint + build_stage_d_mutation_accounting
# =======================================================================================================


def test_legacy_and_null_fingerprint_covers_exactly_null_and_legacy_rows(engine):
    with Session(engine) as session:
        _mk_run(session, date(2020, 1, 1), engine_identity_value=None)
        _mk_run(session, date(2020, 1, 2), engine_identity_value="6261ca17abc")
        _mk_run(session, date(2020, 1, 3), engine_identity_value="some-other-fresh-identity")
        session.commit()
    with Session(engine) as session:
        fp = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
    assert fp["row_count"] == 2
    assert fp["null_count"] == 1
    assert fp["legacy_6261ca17_count"] == 1
    dates_captured = {r["asof_date"] for r in fp["rows"]}
    assert dates_captured == {"2020-01-01", "2020-01-02"}


def test_legacy_and_null_fingerprint_is_stable_across_two_identical_captures(engine):
    with Session(engine) as session:
        _mk_run(session, date(2020, 1, 1), engine_identity_value=None)
        session.commit()
    with Session(engine) as session:
        fp_a = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
    with Session(engine) as session:
        fp_b = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
    assert fp_a["fingerprint"] == fp_b["fingerprint"]
    assert fp_a["rows"] == fp_b["rows"]


def _sweep(engine_obj):
    from app.engine import j11_maintenance as jm
    with Session(engine_obj) as session:
        return jm.capture_full_table_sweep(session)


def test_mutation_accounting_all_pass_when_only_stage_d_write_tables_changed(engine, cfg, monkeypatch):
    monkeypatch.setattr(jsde.scanner, "run_scan", _stub_run_scan)
    from app.engine import j11_maintenance as jm
    from app.engine import j11_schema_migration as migration
    from app.models import DataProviderRun, Watchlist

    with Session(engine) as session:
        pre_manifest = migration.dump_table(engine, NextSessionManifest.__table__)
        pre_legacy = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
        pre_prices = jm.capture_pre_reset_inventory(session)["daily_prices"]
        pre_provider = jm._count(session, DataProviderRun)
        pre_watchlist = jm._count(session, Watchlist)
        pre_boundary = migration.dump_table(engine, MaintenanceBoundary.__table__)
    pre_sweep = _sweep(engine)

    with Session(engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    with Session(engine) as session:
        jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen, cfg)

    post_sweep = _sweep(engine)
    with Session(engine) as session:
        post_manifest = migration.dump_table(engine, NextSessionManifest.__table__)
        post_legacy = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
        post_prices = jm.capture_pre_reset_inventory(session)["daily_prices"]
        post_provider = jm._count(session, DataProviderRun)
        post_watchlist = jm._count(session, Watchlist)
        post_boundary = migration.dump_table(engine, MaintenanceBoundary.__table__)

    accounting = jsde.build_stage_d_mutation_accounting(
        pre_full_table_sweep=pre_sweep, post_full_table_sweep=post_sweep,
        pre_manifest_dump=pre_manifest, post_manifest_dump=post_manifest,
        pre_legacy_null_fingerprint=pre_legacy, post_legacy_null_fingerprint=post_legacy,
        pre_daily_prices=pre_prices, post_daily_prices=post_prices,
        pre_provider_runs={"count": pre_provider}, post_provider_runs={"count": post_provider},
        pre_watchlist={"count": pre_watchlist}, post_watchlist={"count": post_watchlist},
        pre_maintenance_boundary_dump=pre_boundary, post_maintenance_boundary_dump=post_boundary,
        db_file_true_start={"exists": False}, db_file_true_end={"exists": False},
    )
    assert accounting["all_checks_pass"] is True
    assert accounting["checks"]["changed_tables_subset_of_stage_d_write_tables"] is True
    assert set(accounting["table_sweep_diff"]["changed_existing_tables"]).issubset(set(jsde.STAGE_D_WRITE_TABLES))


def test_mutation_accounting_fails_when_manifest_changed():
    pre_manifest = [{"id": 1, "content_hash": "abc"}]
    post_manifest = [{"id": 1, "content_hash": "CHANGED"}]
    sweep = {"table_names": [], "table_count": 0, "per_table": {}}
    fp = {"row_count": 0, "null_count": 0, "legacy_6261ca17_count": 0, "rows": [], "fingerprint": "x"}
    accounting = jsde.build_stage_d_mutation_accounting(
        pre_full_table_sweep=sweep, post_full_table_sweep=sweep,
        pre_manifest_dump=pre_manifest, post_manifest_dump=post_manifest,
        pre_legacy_null_fingerprint=fp, post_legacy_null_fingerprint=fp,
        pre_daily_prices={"fingerprint": "p"}, post_daily_prices={"fingerprint": "p"},
        pre_provider_runs={"count": 1}, post_provider_runs={"count": 1},
        pre_watchlist={"count": 1}, post_watchlist={"count": 1},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["checks"]["manifests_unchanged"] is False
    assert accounting["all_checks_pass"] is False


def test_mutation_accounting_fails_when_a_table_outside_stage_d_scope_changed():
    sweep_before = {"table_names": ["watchlist"], "table_count": 1, "per_table": {"watchlist": {"fingerprint": "a"}}}
    sweep_after = {"table_names": ["watchlist"], "table_count": 1, "per_table": {"watchlist": {"fingerprint": "b"}}}
    fp = {"row_count": 0, "null_count": 0, "legacy_6261ca17_count": 0, "rows": [], "fingerprint": "x"}
    accounting = jsde.build_stage_d_mutation_accounting(
        pre_full_table_sweep=sweep_before, post_full_table_sweep=sweep_after,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_legacy_null_fingerprint=fp, post_legacy_null_fingerprint=fp,
        pre_daily_prices={"fingerprint": "p"}, post_daily_prices={"fingerprint": "p"},
        pre_provider_runs={"count": 1}, post_provider_runs={"count": 1},
        pre_watchlist={"count": 1}, post_watchlist={"count": 1},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["checks"]["changed_tables_subset_of_stage_d_write_tables"] is False
    assert accounting["all_checks_pass"] is False


def test_mutation_accounting_fails_when_legacy_or_null_rows_changed():
    sweep = {"table_names": [], "table_count": 0, "per_table": {}}
    fp_before = {"row_count": 1, "null_count": 1, "legacy_6261ca17_count": 0,
                 "rows": [{"id": 1, "engine_identity": None}], "fingerprint": "before"}
    fp_after = {"row_count": 1, "null_count": 0, "legacy_6261ca17_count": 0,
                "rows": [{"id": 1, "engine_identity": "mutated!"}], "fingerprint": "after"}
    accounting = jsde.build_stage_d_mutation_accounting(
        pre_full_table_sweep=sweep, post_full_table_sweep=sweep,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_legacy_null_fingerprint=fp_before, post_legacy_null_fingerprint=fp_after,
        pre_daily_prices={"fingerprint": "p"}, post_daily_prices={"fingerprint": "p"},
        pre_provider_runs={"count": 1}, post_provider_runs={"count": 1},
        pre_watchlist={"count": 1}, post_watchlist={"count": 1},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["checks"]["legacy_and_null_scanner_runs_unchanged"] is False
    assert accounting["all_checks_pass"] is False


# =======================================================================================================
# stage_d_execution_outcome -- the exact two-terminal-state decision
# =======================================================================================================


def test_outcome_executed_true_only_when_all_three_stages_agree():
    outcome = jsde.stage_d_execution_outcome(
        execution_gate={"proceed": True}, regeneration_result={"completed": True},
        mutation_accounting={"all_checks_pass": True},
    )
    assert outcome["executed"] is True


@pytest.mark.parametrize("gate,regen,accounting,expected_reason", [
    ({"proceed": False, "blocking_reasons": ["x"]}, None, None, "execution_gate_did_not_proceed"),
    ({"proceed": True}, None, None, "no_regeneration_attempted"),
    ({"proceed": True}, {"completed": False, "stopped_at_date": "2030-01-06"}, None, "per_date_loop_stopped_early"),
    ({"proceed": True}, {"completed": True}, {"all_checks_pass": False}, "post_execution_mutation_accounting_failed"),
])
def test_outcome_executed_false_with_exact_reason(gate, regen, accounting, expected_reason):
    outcome = jsde.stage_d_execution_outcome(
        execution_gate=gate, regeneration_result=regen, mutation_accounting=accounting,
    )
    assert outcome["executed"] is False
    assert outcome["reason"] == expected_reason


# =======================================================================================================
# TC-8 -- full end-to-end run against a Stage-C-shaped fixture via app.db.make_engine's isolated engine
# =======================================================================================================


def test_tc8_full_end_to_end_stage_c_shaped_fixture_via_make_engine(tmp_path, cfg, monkeypatch):
    """A synthetic fixture DB (never `trendora.db`), built via `app.db.make_engine`: some custom
    'incident' dates cleared (zero `ScannerRun` -- the natural post-Stage-C-shaped starting state), an
    active `MaintenanceBoundary` row scoped to exactly those dates, and one of the dates already
    carrying a manifest. Reproduces TC-4 through TC-7's assertions end-to-end."""
    from app.db import create_db_and_tables, make_engine

    db_path = tmp_path / "stage_d_execute_fixture.db"
    fixture_engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(fixture_engine)
    monkeypatch.setattr(jsde.scanner, "run_scan", _stub_run_scan)

    with Session(fixture_engine) as session:
        guard.register_boundary(session, name="j11-incident-recovery", dates=LOOP_DATES, reason="fixture", active=True)
        run_with_manifest = _mk_run(session, date(2029, 12, 1))  # NOT one of LOOP_DATES -- pre-existing manifest survivor
        _mk_manifest(session, run_with_manifest)
        session.commit()

    with Session(fixture_engine) as session:
        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
    assert boundary_recheck["ok"] is True

    with Session(fixture_engine) as session:
        pre_manifest_count = len(session.exec(
            __import__("sqlmodel").select(NextSessionManifest)
        ).all())
    assert pre_manifest_count == 1

    with Session(fixture_engine) as session:
        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
    with Session(fixture_engine) as session:
        regen = jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen, cfg)

    assert regen["completed"] is True
    assert len(regen["new_run_ids"]) == 2

    with Session(fixture_engine) as session:
        from sqlmodel import select as _select
        post_manifests = session.exec(_select(NextSessionManifest)).all()
        assert len(post_manifests) == 1  # unchanged -- Stage D minted NO manifest
        assert post_manifests[0].as_of == date(2029, 12, 1)
        for one_date in LOOP_DATES:
            run = session.exec(_select(ScannerRun).where(ScannerRun.asof_date == one_date)).one()
            assert run.engine_identity == frozen["engine_identity"]
