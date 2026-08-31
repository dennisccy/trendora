"""GET /api/compass (goal-market-compass iter-2) — API-layer contract: create-once-on-GET / serve-from-
storage (TC-1), every new field present at the response layer directly, and honest as-of error mapping.

`compass_engine` is a small hand-built DB (mirrors `test_api_runs.py`'s `multi_run_engine` style) —
deliberately NOT the session-scoped `loaded_engine`. The route function is called DIRECTLY with a
session (the SAME lightweight pattern `test_api_runs.py::test_api_runs_n_stocks_single_grouped_query_not_per_run`
uses) rather than through a full TestClient/lifespan, since these are query-shape/contract proofs, not
browser-facing checks (those are QA's job).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import delete as sa_delete
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import compass as compass_module
from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun


@pytest.fixture()
def cfg():
    return load_config()


@pytest.fixture()
def compass_engine(tmp_path):
    """Two `ScannerRun` rows (so a "prior session" exists) each carrying one `ScannerResult`, plus the
    `DailyPrice` bars `resolve_as_of_date`/`latest_data_date` need to resolve `as_of` at all."""
    engine = make_engine(f"sqlite:///{tmp_path / 'compass_api.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for bar_date in (date(2024, 6, 1), date(2024, 6, 8)):
            session.add(DailyPrice(
                symbol="SPY", date=bar_date, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
            ))
        session.commit()
        for i, (asof, regime_score) in enumerate(((date(2024, 6, 1), 50.0), (date(2024, 6, 8), 58.0))):
            run = ScannerRun(
                asof_date=asof, created_at=datetime(2024, 6, 1 + i * 7, tzinfo=timezone.utc),
                provider="seed", benchmark="SPY", regime_score=regime_score, regime_label="Expansion",
                regime_components_json="[]", breadth_above_50dma=55.0, breadth_above_200dma=60.0,
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            session.add(ScannerResult(
                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=92.0, leadership_bucket="A",
                entry_quality_score=85.0, entry_quality_bucket="B", risk_score=40.0, risk_bucket="C",
                setup_status="Breakout-watch", rank=1,
                record_json=json.dumps({"ticker": "AAA", "invalidation": {"note": "AAA note"}}),
            ))
            session.commit()
    return engine


def _scanner_run_count(engine) -> int:
    """Read-only row count on `scanner_runs` -- used by the iter-27 tests to prove the reordered route
    never mints a new `ScannerRun` when a manifest already exists for the resolved as-of."""
    with Session(engine) as session:
        return len(session.exec(select(ScannerRun)).all())


def _manifest_count(engine) -> int:
    """Read-only row count on `next_session_manifests` (iter-27 audit, TC-5/TC-9)."""
    with Session(engine) as session:
        return len(session.exec(select(NextSessionManifest)).all())


def _freeze_frontier(engine, cfg) -> None:
    """iter-3: the route can no longer auto-mint the CURRENT frontier's manifest (J-05 step 7) -- tests
    that exercise the WARM-HIT/served-fields behavior must first simulate the ingest-finalize freeze the
    same way `data_manager._refresh_ingest_aggregates` does."""
    with Session(engine) as session:
        run = session.exec(
            __import__("sqlmodel").select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))
        ).first()
        compass_module.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")


def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
    from app.api.compass import compass as compass_route

    _freeze_frontier(compass_engine, cfg)
    with Session(compass_engine) as session:
        result = compass_route(None, session)

    # NOTES: assert every new field at the response layer itself -- never behind a fixture-data gate.
    assert result["as_of"] == "2024-06-08"
    assert isinstance(result["session_delta"], dict)
    for key in ("prior_as_of", "gap_days", "changes", "suppressed", "suppressed_count"):
        assert key in result["session_delta"]
    assert isinstance(result["narrative"], dict) and "sentences" in result["narrative"]
    assert isinstance(result["selection"], dict)
    for key in ("candidates", "why_not", "disposition_tally", "candidates_empty_reason"):
        assert key in result["selection"]
    assert isinstance(result["content_hash"], str) and len(result["content_hash"]) == 64  # sha256 hex
    # iter-3 (J-05/J-06) freeze/integrity fields -- every one served at the response layer directly.
    assert result["mode"] == "at_ingest"
    assert result["version"] == 1
    assert result["frozen"] is True
    assert result["prospective_eligible"] is True
    assert result["generation"]["producer"] == "ingest_finalize"
    assert result["generation"]["engine_identity"]
    assert result["candidate_rule_hash"] and result["cohort_rule_hash"] and result["manifest_config_hash"]
    assert result["dataset"]["stamp"]
    assert result["universe"]["member_count"] == 1
    assert isinstance(result["comparison_cohort"], list)
    assert isinstance(result["near_threshold_shadow"], list)
    assert result["caveats"]["cohort_semantics"]
    assert result["available_at_utc"]
    assert isinstance(result["manifest_hash"], str) and len(result["manifest_hash"]) == 64
    # `basis`/`versions` are READ-TIME-ONLY additions the API layer attaches AFTER manifest_row_payload()
    # -- they were never part of what got hashed at write time, so verification runs over the pure
    # reconstructed document (TC-4's exact contract), not the full API response shape.
    hashed_document = {k: v for k, v in result.items() if k not in ("basis", "versions")}
    assert compass_module.verify_manifest_hash(hashed_document)
    assert result["basis"]["status"] == "available"
    assert result["versions"] == [
        {
            "version": 1, "mode": "at_ingest", "frozen": True, "prospective_eligible": True,
            "generated_at": result["generation"]["generated_at"],
        }
    ]


def test_compass_route_computes_once_serves_from_storage_after(compass_engine, cfg, monkeypatch):
    """TC-1: once frozen, the SECOND call for the same as-of returns byte-identical content with ZERO
    additional producer calls (get_or_create_manifest short-circuits on the stored row)."""
    from app.api.compass import compass as compass_route

    _freeze_frontier(compass_engine, cfg)

    calls = {"n": 0}
    original = compass_module.build_manifest_payload

    def counting_build(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(compass_module, "build_manifest_payload", counting_build)

    with Session(compass_engine) as session:
        first = compass_route(None, session)
    assert calls["n"] == 0  # already frozen by _freeze_frontier -- this call is a pure warm read

    with Session(compass_engine) as session:
        second = compass_route(None, session)
    assert calls["n"] == 0  # no additional producer call on the second, separate-request hit

    assert first == second

    with Session(compass_engine) as session:
        rows = session.exec(
            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
        ).all()
    assert len(rows) == 1


def test_compass_route_frontier_with_no_manifest_yet_returns_honest_404(compass_engine, cfg):
    """J-05 step 7 / TC-8: a plain GET for the CURRENT frontier with no manifest yet never mints one --
    an honest 404, never a fabricated payload."""
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as exc_info:
            compass_route(None, session)
    assert exc_info.value.status_code == 404

    with Session(compass_engine) as session:
        rows = session.exec(
            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
        ).all()
    assert rows == []  # no partial/fabricated row was written


def test_compass_route_unknown_asof_returns_honest_error_never_fabricated(compass_engine, cfg):
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as exc_info:
            compass_route("2099-01-01", session)  # far future -- no stored run for this as-of
    assert exc_info.value.status_code in (400, 404, 422, 503)  # snapshot_serving's honest as-of mapping
    assert exc_info.value.detail  # a real message, never a silent/empty fabricated body


def test_compass_route_historical_asof_serves_that_dates_own_manifest(compass_engine, cfg):
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        result = compass_route("2024-06-01", session)
    assert result["as_of"] == "2024-06-01"
    assert result["session_delta"]["prior_as_of"] is None  # earliest stored run -- explicit no-prior-run state


# --- state_band (goal-market-compass iter-28, J-07) -----------------------------------------------


def test_compass_route_serves_state_band_directly(compass_engine, cfg):
    """iter-28 (J-07): `state_band` is present at the response layer, additive alongside
    `session_delta`/`narrative`/`selection`. `compass_engine` seeds no `MarketPhaseCache` row, so
    `stress` honestly reads the no-comparison NA state (never fabricated); `regime` (50.0 -> 58.0) and
    `breadth` (55.0 -> 55.0, unchanged) compute directly from the two stored runs."""
    from app.api.compass import compass as compass_route

    _freeze_frontier(compass_engine, cfg)
    with Session(compass_engine) as session:
        result = compass_route(None, session)

    assert "state_band" in result
    state_band = result["state_band"]
    for band in ("regime", "stress", "breadth"):
        assert band in state_band
        assert set(state_band[band]) == {"direction_word", "delta"}
    assert state_band["regime"]["delta"] == pytest.approx(8.0)  # 58.0 - 50.0
    assert state_band["regime"]["direction_word"] == cfg.compass.vocabulary.direction_words["up"]
    assert state_band["breadth"]["delta"] == pytest.approx(0.0)
    assert state_band["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["flat"]
    assert state_band["stress"] == {"direction_word": None, "delta": None}  # no MarketPhaseCache seeded


def test_compass_route_state_band_null_on_pre_iter28_row(compass_engine, cfg):
    """A manifest row minted before `state_band_json` existed (simulated by clearing the column, which
    is exactly the shape every one of the 26+ live pre-iter-28 rows has -- AG-12: never backfilled)
    serves `state_band: None` honestly -- never fabricated, never crashes the route."""
    from app.api.compass import compass as compass_route

    _freeze_frontier(compass_engine, cfg)
    with Session(compass_engine) as session:
        row = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
        ).first()
        row.state_band_json = None
        session.add(row)
        session.commit()

    with Session(compass_engine) as session:
        result = compass_route(None, session)
    assert result["state_band"] is None


# --- POST /api/compass/regenerate (iter-3, J-05/J-06) --------------------------------------------


def test_regenerate_route_requires_confirm_flag(compass_engine, cfg):
    """TC-13 / Error cases: called without confirm=true, no row is created."""
    from app.api.compass import compass_regenerate

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as exc_info:
            compass_regenerate("2024-06-01", False, session)
    assert exc_info.value.status_code == 400

    with Session(compass_engine) as session:
        rows = session.exec(
            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
        ).all()
    assert rows == []


def test_regenerate_route_missing_manifest_returns_honest_404(compass_engine, cfg):
    """Error cases: regenerate for an as_of with no existing manifest returns an honest 4xx, never
    fabricates a version."""
    from app.api.compass import compass_regenerate

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as exc_info:
            compass_regenerate("2024-06-01", True, session)
    assert exc_info.value.status_code == 404


def test_regenerate_route_mints_version_2_leaves_version_1_untouched(compass_engine, cfg):
    """TC-12: version 2 carries its own generation/available_at_utc/manifest_hash, prospective_eligible
    False even though a historical as_of's mode also computes at_ingest-ineligible (retrospective);
    version 1 stays byte-identical."""
    from app.api.compass import compass as compass_route
    from app.api.compass import compass_regenerate

    with Session(compass_engine) as session:
        v1 = compass_route("2024-06-01", session)

    with Session(compass_engine) as session:
        v2 = compass_regenerate("2024-06-01", True, session)

    assert v2["version"] == 2
    assert v2["prospective_eligible"] is False
    assert v2["manifest_hash"] != v1["manifest_hash"]
    assert v2["generation"]["producer"] == "regenerate"

    with Session(compass_engine) as session:
        v1_reread = compass_route("2024-06-01", session)
    # re-reading after a regenerate still serves the LATEST version by default...
    assert v1_reread["version"] == 2
    # ...but version 1's own row is untouched -- fetch it explicitly via list_manifest_versions
    with Session(compass_engine) as session:
        versions = compass_module.list_manifest_versions(session, date(2024, 6, 1))
    assert [v.version for v in versions] == [1, 2]
    assert versions[0].manifest_hash == v1["manifest_hash"]
    assert versions[0].content_hash == v1["content_hash"]
    assert versions[0].prospective_eligible is False  # historical as_of was never eligible either


# --- TC-8 / TC-9 (route-level basis disclosure, iter-26/iter-27) ------------------------------------
#
# test_manifest_invariants.py already covers `basis_disclosure()` directly at the UNIT level (calling it
# with a hand-built row + session where the current run has been deleted / recreated) --
# `test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone` and
# `test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated`. What was NOT previously proven
# is what `GET /api/compass` ITSELF observes end-to-end when the underlying run is actually removed.
#
# iter-3/iter-26 finding (B2, re-confirmed twice): the route called `resolved_run()`
# (snapshot_serving -> scanner.resolve_run -> scanner.run_scan) BEFORE `get_or_create_manifest`/
# `basis_disclosure` ever ran, and `run_scan` SELF-HEALS -- a missing `ScannerRun` was silently
# RECREATED right there, so `basis_disclosure` could only ever observe "available" or "rebuilt", never
# "unavailable" -- a real, correct, unit-tested branch a live request could never actually reach (an
# honesty gap, not coverage, per the iter-26 lesson).
#
# iter-27 FIX (this iteration): the route now resolves the as-of date via `resolved_date` (validates
# only, never self-heals) and looks up `latest_manifest_for_date` FIRST. When a manifest already exists
# for that date, it is served directly -- `resolved_run`/`run_scan` are never called on that branch, so
# a removed source run stays removed and `basis_disclosure`'s pure read-only `ScannerRun` SELECT can
# honestly observe "unavailable". The test below proves this empirically through the real route
# function (not a new isolated unit branch, per the iter-26 lesson): the route never 404s, never
# crashes, the frozen manifest's payload/version/manifest_hash stay BYTE-IDENTICAL across the removal
# (AG-12), and the removed `ScannerRun` stays absent -- no self-heal fires on this branch.


def test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run(compass_engine, cfg, monkeypatch, tmp_path):
    from app.api.compass import compass as compass_route

    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))

    # freeze 2024-06-08's manifest while it is still the frontier (mirrors the ingest-finalize freeze)
    _freeze_frontier(compass_engine, cfg)
    with Session(compass_engine) as session:
        before = compass_route("2024-06-08", session)
    assert before["mode"] == "at_ingest"
    before_hash = before["manifest_hash"]
    before_version = before["version"]

    # push the frontier forward with a THIRD, LATER run -- 2024-06-08 becomes a historical as_of, and
    # 2024-06-01's earlier bar stays in place so as-of resolution for 2024-06-08 still succeeds after its
    # own bar is removed below (has_bar_on_or_before)
    with Session(compass_engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 6, 15), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        session.add(ScannerRun(
            asof_date=date(2024, 6, 15), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=61.0, regime_label="Expansion", regime_components_json="[]",
            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()

    # remove 2024-06-08's ScannerRun (+ children) + its own DailyPrice bar -- mirrors remove_data's cascade
    with Session(compass_engine) as session:
        removed_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
        session.execute(sa_delete(ScannerResult).where(ScannerResult.run_id == removed_run.id))
        session.execute(sa_delete(ScannerRun).where(ScannerRun.id == removed_run.id))
        session.execute(sa_delete(DailyPrice).where(DailyPrice.date == date(2024, 6, 8)))
        session.commit()

    with Session(compass_engine) as session:
        gone = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
    assert gone is None  # confirmed removed immediately before the route call below

    scanner_runs_before = _scanner_run_count(compass_engine)

    with Session(compass_engine) as session:
        after = compass_route("2024-06-08", session)  # must NEVER 404, NEVER raise

    assert after["manifest_hash"] == before_hash  # AG-12: the frozen manifest payload is byte-unchanged
    assert after["version"] == before_version
    assert after["content_hash"] == before["content_hash"]
    assert after["selection"] == before["selection"]  # includes candidates, why_not, disposition_tally
    assert after["comparison_cohort"] == before["comparison_cohort"]
    assert after["near_threshold_shadow"] == before["near_threshold_shadow"]
    # iter-27 fix: the route now checks `latest_manifest_for_date` BEFORE ever calling
    # `resolved_run`/`run_scan`, so the removed source run is never self-healed on this branch, and
    # `basis_disclosure`'s read-only SELECT honestly observes "unavailable".
    assert after["basis"]["status"] == "unavailable"
    assert after["basis"]["detail"]  # a real message, never a silent/empty fabricated detail
    assert "no longer stored" in after["basis"]["detail"]

    with Session(compass_engine) as session:
        healed = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
    assert healed is None  # no self-heal fired -- the removed run stays removed
    assert _scanner_run_count(compass_engine) == scanner_runs_before  # zero new ScannerRun rows minted


def test_compass_route_restore_path_flips_basis_back_to_available_or_rebuilt(compass_engine, cfg, monkeypatch, tmp_path):
    """Restore-path (J-06 step 3): starting from the state left by the removal test above (manifest still
    serving "unavailable"), re-creating the `ScannerRun` for that as_of with the SAME recorded
    `created_at` flips `basis.status` back to "available"; re-creating it with a DIFFERENT `created_at`
    yields "rebuilt" instead. In both cases the manifest's `manifest_hash`/`version`/full payload stay
    byte-identical to the pre-removal capture."""
    from app.api.compass import compass as compass_route

    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))

    _freeze_frontier(compass_engine, cfg)
    with Session(compass_engine) as session:
        before = compass_route("2024-06-08", session)

    with Session(compass_engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 6, 15), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        session.add(ScannerRun(
            asof_date=date(2024, 6, 15), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=61.0, regime_label="Expansion", regime_components_json="[]",
            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()

    with Session(compass_engine) as session:
        removed_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
        session.execute(sa_delete(ScannerResult).where(ScannerResult.run_id == removed_run.id))
        session.execute(sa_delete(ScannerRun).where(ScannerRun.id == removed_run.id))
        session.execute(sa_delete(DailyPrice).where(DailyPrice.date == date(2024, 6, 8)))
        session.commit()

    with Session(compass_engine) as session:
        gone = compass_route("2024-06-08", session)
    assert gone["basis"]["status"] == "unavailable"

    recorded_created_at = datetime.fromisoformat(before["generation"]["source_run_created_at"])

    # (a) re-create with the SAME recorded created_at -> "available", bytes unchanged
    with Session(compass_engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 6, 8), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.add(ScannerRun(
            asof_date=date(2024, 6, 8), created_at=recorded_created_at, provider="seed", benchmark="SPY",
            regime_score=58.0, regime_label="Expansion", regime_components_json="[]",
            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()

    with Session(compass_engine) as session:
        restored_same = compass_route("2024-06-08", session)
    assert restored_same["basis"]["status"] == "available"
    assert restored_same["manifest_hash"] == before["manifest_hash"]
    assert restored_same["version"] == before["version"]
    assert restored_same["content_hash"] == before["content_hash"]

    # remove again and re-create with a DIFFERENT created_at -> "rebuilt", bytes still unchanged
    with Session(compass_engine) as session:
        recreated_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
        session.execute(sa_delete(ScannerRun).where(ScannerRun.id == recreated_run.id))
        session.commit()
        session.add(ScannerRun(
            asof_date=date(2024, 6, 8), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=58.0, regime_label="Expansion", regime_components_json="[]",
            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()

    with Session(compass_engine) as session:
        restored_different = compass_route("2024-06-08", session)
    assert restored_different["basis"]["status"] == "rebuilt"
    assert restored_different["manifest_hash"] == before["manifest_hash"]
    assert restored_different["version"] == before["version"]
    assert restored_different["content_hash"] == before["content_hash"]


def test_compass_route_warm_path_is_inert_two_gets_are_byte_identical_zero_new_runs(compass_engine, cfg):
    """Warm-path regression: with an existing manifest and its run intact, two consecutive `GET` calls
    through the route function return byte-identical responses and add zero new `ScannerRun` rows --
    proves the new fast-path branch (`latest_manifest_for_date` before `resolved_run`) is inert on the
    common, already-working case."""
    from app.api.compass import compass as compass_route

    _freeze_frontier(compass_engine, cfg)

    scanner_runs_before = _scanner_run_count(compass_engine)

    with Session(compass_engine) as session:
        first = compass_route("2024-06-08", session)
    with Session(compass_engine) as session:
        second = compass_route("2024-06-08", session)

    assert first == second
    assert first["basis"]["status"] == "available"
    assert _scanner_run_count(compass_engine) == scanner_runs_before


# --- TC-5 / TC-9 (iter-27 audit: the two test-first contract items the iteration specified but did not
# actually write — the dev handoff and QA report both claimed them PASS by citing tests that do not
# assert them). Added by the auditor so the DEFINITION OF DONE's "TC-1..TC-5, TC-9, TC-10 all pass" is
# backed by executed assertions rather than a structural argument. --------------------------------


def test_tc5_create_once_on_get_for_a_historical_asof_with_no_manifest_yet(compass_engine, cfg):
    """TC-5 (as written in the iter-27 spec): a historical, non-frontier as_of with NO manifest yet and no
    prior GET. The FIRST call through the reordered route mints exactly one row (`mode: retrospective`);
    the SECOND adds ZERO further rows. This is the create branch the reorder was most likely to break —
    it is the only branch that may still create a `ScannerRun` or mint a manifest."""
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        pre = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
        ).all()
    assert pre == []  # no manifest yet, no prior GET

    with Session(compass_engine) as session:
        first = compass_route("2024-06-01", session)
    assert first["as_of"] == "2024-06-01"
    assert first["mode"] == "retrospective"
    assert first["version"] == 1
    with Session(compass_engine) as session:
        after_first = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
        ).all()
    assert len(after_first) == 1  # exactly one row minted

    with Session(compass_engine) as session:
        second = compass_route("2024-06-01", session)
    with Session(compass_engine) as session:
        after_second = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
        ).all()
    assert len(after_second) == 1  # ZERO further rows -- create-once survives the reorder
    assert second["manifest_hash"] == first["manifest_hash"]
    assert second["version"] == 1


def test_tc5_create_branch_still_runs_when_neither_run_nor_manifest_exists(compass_engine, cfg):
    """TC-5, harder limb: an as-of that resolves but has NEITHER a `ScannerRun` NOR a manifest. This is the
    only path on which the route may still create BOTH, and the one the fast-path reorder skips past when
    a manifest exists — so it must be proven to still fire."""
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        assert session.exec(
            select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 5))
        ).first() is None
        assert session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 5))
        ).all() == []

    with Session(compass_engine) as session:
        result = compass_route("2024-06-05", session)

    assert result["as_of"] == "2024-06-05"
    assert result["mode"] == "retrospective"
    assert result["version"] == 1
    with Session(compass_engine) as session:
        assert session.exec(
            select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 5))
        ).first() is not None  # the slow path created the run, exactly as before the reorder
        assert len(session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 5))
        ).all()) == 1


@pytest.mark.parametrize("frozen_first", [False, True])
def test_tc9_asof_error_status_codes_are_exact_on_both_branches(compass_engine, cfg, frozen_first):
    """TC-9 (as written in the iter-27 spec): unparseable -> EXACTLY 422, future -> EXACTLY 400, on BOTH
    the fast (a manifest already exists for the frontier) and slow (none does) branches. The pre-existing
    error test asserts only `status_code in (400, 404, 422, 503)` on a single future date, which would
    pass even if the reorder had changed the mapping; these assert the exact codes and prove no row is
    written on either error path."""
    from app.api.compass import compass as compass_route

    if frozen_first:
        _freeze_frontier(compass_engine, cfg)

    manifests_before = _manifest_count(compass_engine)
    runs_before = _scanner_run_count(compass_engine)

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as unparseable:
            compass_route("not-a-date", session)
    assert unparseable.value.status_code == 422
    assert unparseable.value.detail

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as future:
            compass_route("2099-01-01", session)
    assert future.value.status_code == 400
    assert future.value.detail

    assert _manifest_count(compass_engine) == manifests_before  # no fabricated row on either error path
    assert _scanner_run_count(compass_engine) == runs_before
