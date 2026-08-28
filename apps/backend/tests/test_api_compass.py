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


# --- TC-8 / TC-9 (route-level basis disclosure, iter-26) ------------------------------------------
#
# test_manifest_invariants.py already covers `basis_disclosure()` directly at the UNIT level (calling it
# with a hand-built row + session where the current run has been deleted / recreated) --
# `test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone` and
# `test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated`. What was NOT previously proven
# is what `GET /api/compass` ITSELF observes end-to-end when the underlying run is actually removed --
# the route calls `resolved_run()` (snapshot_serving -> scanner.resolve_run -> scanner.run_scan) BEFORE
# `get_or_create_manifest`/`basis_disclosure` ever run, and `run_scan` SELF-HEALS: if the requested as_of
# still resolves to a valid date (any earlier bar exists), a missing `ScannerRun` is silently
# RECREATED right there, so by the time `basis_disclosure` looks up "the current run for this as_of" it
# is never actually absent. The test below proves this empirically (RE-VERIFIED, iter-26 -- iter-3's own
# audit flagged this exact mechanism as finding B2 and it was never fixed): the live route can reach
# "available" or "rebuilt", but "unavailable" is structurally UNREACHABLE through this endpoint as
# currently wired -- it is real, correct, unit-tested code that a request can never actually observe.
# This is a genuine, pre-existing finding (not a regression introduced this iteration, and fixing the
# self-heal ordering is a deliberate change outside this iteration's IN SCOPE list) -- recorded here and
# in the dev handoff for reviewer/auditor visibility. What IS safety-critical and IS proven here: the
# route never 404s, never crashes, and the frozen manifest's payload/version/manifest_hash stay
# BYTE-IDENTICAL across the self-heal (AG-12) -- only the read-time basis disclosure differs.


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

    with Session(compass_engine) as session:
        after = compass_route("2024-06-08", session)  # must NEVER 404, NEVER raise

    assert after["manifest_hash"] == before_hash  # AG-12: the frozen manifest payload is byte-unchanged
    assert after["version"] == before_version
    # the re-verified finding: self-heal recreates the run before basis_disclosure runs, so the live
    # route observes "rebuilt", never "unavailable" -- see the block docstring above.
    assert after["basis"]["status"] == "rebuilt"

    with Session(compass_engine) as session:
        healed = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
    assert healed is not None  # confirms the self-heal actually fired (not merely absent-run tolerance)
