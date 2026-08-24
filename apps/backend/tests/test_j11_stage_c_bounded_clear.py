"""goal-market-compass iter-13 -- J-11 Stage C bounded-clear tests (TC-4, TC-5, TC-6).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`, hand-built rows)
-- the SAME pattern `test_j11_maintenance.py` uses, never `loaded_engine` and never
`apps/backend/data/trendora.db` (docs/goal.md: "NEVER copy, move, or open-for-write trendora.db"; the
resource contract this whole session runs under).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from unittest import mock

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.engine import compass, scanner
from app.engine.data_manager import clear_snapshot_dates
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import (
    DailyPrice,
    ForwardReturn,
    NextSessionManifest,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)


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


def _mk_run(session: Session, asof: date, *, created_at: datetime | None = None) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof,
        created_at=created_at or datetime.now(timezone.utc),
        provider="seed",
        benchmark="SPY",
        regime_score=55.0,
        regime_label="Expansion",
        regime_components_json="[]",
        breadth_above_50dma=50.0,
        breadth_above_200dma=55.0,
        new_high_low_json="{}",
        candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _mk_children(session: Session, run: ScannerRun, *, n: int = 2) -> dict:
    """Inserts `n` rows into each of the four Layer-2 child tables owned by `run` and returns their ids."""
    ids: dict[str, list[int]] = {"scanner_results": [], "sector_scores": [], "theme_scores": [], "forward_returns": []}
    for i in range(n):
        result = ScannerResult(
            run_id=run.id, ticker=f"T{run.id}{i}", name="Test Co", leadership_score=50.0,
            leadership_bucket="C", entry_quality_score=50.0, entry_quality_bucket="C",
            risk_score=50.0, risk_bucket="C", setup_status="none", rank=i + 1, record_json="{}",
        )
        session.add(result)
        sector = SectorScoreRow(
            run_id=run.id, ticker=f"XL{run.id}{i}", kind="sector", name="Test Sector",
            score=50.0, bucket="C", trend_label="flat", components_json="{}", rank=i + 1,
        )
        session.add(sector)
        theme = ThemeScoreRow(
            run_id=run.id, slug=f"theme-{run.id}-{i}", name="Test Theme", score=50.0, bucket="C",
            members_json="[]", breadth_label="flat", trend_label="flat", components_json="{}", rank=i + 1,
        )
        session.add(theme)
        fwd = ForwardReturn(
            run_id=run.id, symbol=f"T{run.id}{i}", horizon=5, asof_date=run.asof_date,
            entry_close=100.0, measured_date=run.asof_date, realized_return=0.01,
        )
        session.add(fwd)
        session.flush()
        ids["scanner_results"].append(result.id)
        ids["sector_scores"].append(sector.id)
        ids["theme_scores"].append(theme.id)
        ids["forward_returns"].append(fwd.id)
    return ids


def _mk_prices(session: Session, n: int = 5) -> int:
    for i in range(n):
        session.add(
            DailyPrice(
                symbol="SPY", date=date(2020, 1, 1 + i), open=1.0, high=1.0, low=1.0, close=1.0, volume=100,
            )
        )
    session.flush()
    return n


# --- TC-4: bounded-date deletion at the id level; non-incident rows survive with identical ids --------


def test_tc4_bounded_deletion_only_incident_dates_touched_non_incident_ids_survive(engine):
    with Session(engine) as session:
        bars_before = _mk_prices(session, 7)

        incident_run_a = _mk_run(session, INCIDENT_DATES[0])  # 2026-05-12
        incident_ids_a = _mk_children(session, incident_run_a, n=2)
        incident_run_b = _mk_run(session, INCIDENT_DATES[-1])  # 2026-08-12
        incident_ids_b = _mk_children(session, incident_run_b, n=3)

        non_incident_date = date(2026, 8, 15)
        assert non_incident_date not in INCIDENT_DATES
        non_incident_run = _mk_run(session, non_incident_date)
        non_incident_ids = _mk_children(session, non_incident_run, n=2)
        session.commit()

        non_incident_run_id = non_incident_run.id

        result = clear_snapshot_dates(session, INCIDENT_DATES)

        # the two incident-date runs and every one of their children are gone.
        assert session.get(ScannerRun, incident_run_a.id) is None
        assert session.get(ScannerRun, incident_run_b.id) is None
        for model, ids_a, ids_b in (
            (ScannerResult, incident_ids_a["scanner_results"], incident_ids_b["scanner_results"]),
            (SectorScoreRow, incident_ids_a["sector_scores"], incident_ids_b["sector_scores"]),
            (ThemeScoreRow, incident_ids_a["theme_scores"], incident_ids_b["theme_scores"]),
            (ForwardReturn, incident_ids_a["forward_returns"], incident_ids_b["forward_returns"]),
        ):
            for row_id in ids_a + ids_b:
                assert session.get(model, row_id) is None

        # the non-incident-date run and every one of its children survive with their EXACT original ids.
        assert session.get(ScannerRun, non_incident_run_id) is not None
        for model, ids in (
            (ScannerResult, non_incident_ids["scanner_results"]),
            (SectorScoreRow, non_incident_ids["sector_scores"]),
            (ThemeScoreRow, non_incident_ids["theme_scores"]),
            (ForwardReturn, non_incident_ids["forward_returns"]),
        ):
            for row_id in ids:
                assert session.get(model, row_id) is not None

        # daily_prices invariant: identical row count before/after, table never referenced by a DELETE.
        assert result["bars_before"] == bars_before
        assert result["bars_after"] == bars_before

        # totals reconcile with the two incident runs' own child counts.
        assert result["totals"]["scanner_runs"] == 2
        assert result["totals"]["scanner_results"] == 5  # 2 + 3
        assert result["totals"]["sector_scores"] == 5
        assert result["totals"]["theme_scores"] == 5
        assert result["totals"]["forward_returns"] == 5


# --- TC-5: a date with no existing ScannerRun is a documented no-op, never an error --------------------


def test_tc5_no_op_on_absent_run_never_raises(engine):
    with Session(engine) as session:
        _mk_prices(session, 3)
        # only ONE incident date carries a run; the other 10 have none.
        run = _mk_run(session, INCIDENT_DATES[0])
        _mk_children(session, run, n=1)
        session.commit()

        result = clear_snapshot_dates(session, INCIDENT_DATES)  # must not raise

        for one_date in INCIDENT_DATES[1:]:
            key = one_date.isoformat()
            assert result["per_date"][key]["run_id"] is None
            assert result["per_date"][key]["deleted"] == {
                "scanner_runs": 0, "forward_returns": 0, "scanner_results": 0,
                "sector_scores": 0, "theme_scores": 0,
            }

        key0 = INCIDENT_DATES[0].isoformat()
        assert result["per_date"][key0]["run_id"] == run.id
        assert result["per_date"][key0]["deleted"]["scanner_runs"] == 1


# --- TC-6: never calls get_or_create_manifest / run_scan / persist_run_payload; manifest byte-unchanged


def test_tc6_never_calls_manifest_or_scan_paths_manifest_row_byte_unchanged(engine):
    with Session(engine) as session:
        _mk_prices(session, 2)
        run = _mk_run(session, INCIDENT_DATES[0])
        _mk_children(session, run, n=1)

        # a manifest referencing the soon-to-be-deleted run -- the exact FK-orphaning scenario Stage C
        # must leave completely untouched (never "repaired", never rebound, never regenerated).
        manifest = NextSessionManifest(
            as_of=run.asof_date,
            version=1,
            source_run_id=run.id,
            session_delta_json="{}",
            narrative_json="{}",
            selection_json="{}",
            content_hash="stub-content-hash",
            created_at=datetime.now(timezone.utc),
            mode="at_ingest",
            frozen=True,
            generation_json=json.dumps({"producer": "ingest_finalize", "source_run_created_at": compass._utc_isoformat(run.created_at)}),
            manifest_hash="stub-manifest-hash",
            prospective_eligible=True,
        )
        session.add(manifest)
        session.commit()

        manifest_before = json.loads(json.dumps({c: getattr(manifest, c) for c in manifest.__class__.model_fields}, default=str))

        with (
            mock.patch.object(compass, "get_or_create_manifest") as mock_get_or_create,
            mock.patch.object(scanner, "run_scan") as mock_run_scan,
            mock.patch.object(scanner, "persist_run_payload") as mock_persist,
        ):
            clear_snapshot_dates(session, INCIDENT_DATES)

        mock_get_or_create.assert_not_called()
        mock_run_scan.assert_not_called()
        mock_persist.assert_not_called()

        # the manifest row itself: still present, every column byte-unchanged (never UPDATEd/"repaired").
        session.expire_all()
        refreshed = session.get(NextSessionManifest, manifest.id)
        assert refreshed is not None
        manifest_after = json.loads(json.dumps({c: getattr(refreshed, c) for c in refreshed.__class__.model_fields}, default=str))
        assert manifest_after == manifest_before

        # and its source_run_id is now a genuine orphan (the run it pointed to is gone) -- proof this
        # scenario was actually exercised, not accidentally skipped.
        assert session.get(ScannerRun, manifest.source_run_id) is None
