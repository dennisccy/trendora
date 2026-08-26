"""goal-market-compass iter-10 -- J-11 Stage B/B1/B2 precondition tests (TC-3..TC-7).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`, hand-built rows)
-- the SAME pattern `test_manifest_invariants.py` uses, never `loaded_engine`. Two lessons from the
session's own `lessons.md` shape these tests directly (docs/goal.md BACKGROUND, iter-7/iter-9):
  - iter-7: a fail-closed gate proven only against complete fixtures can silently agree on a degenerate/
    empty input -- `test_tc5_degenerate_orphan...` below is exactly that missing case (a manifest whose
    source run was deleted with NO replacement ever created).
  - iter-9: a population-wide "all N matched" claim is where the one real counter-example hides --
    `test_tc7_...` asserts a MATCHING and a MISMATCHED run as two explicit, separate assertions, never
    one aggregate flag.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import load_config
from app.engine import compass, j11_maintenance
from app.models import NextSessionManifest, ScannerRun


@pytest.fixture()
def cfg():
    return load_config()


@pytest.fixture()
def engine():
    """A fresh in-memory SQLite DB built from the CURRENT SQLModel metadata, with `PRAGMA
    foreign_keys=ON` explicitly issued on every connection this engine ever opens -- via a `connect`
    event listener, the SAME mechanism `app.db._apply_sqlite_pragmas` uses for the real backend.
    (SQLite ignores `PRAGMA foreign_keys` if issued inside an already-open transaction, which a
    Session-level `session.exec(text(...))` would be -- the connect-time listener is the only place
    that reliably lands it BEFORE any transaction begins.)"""
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(eng)
    return eng


def _mk_run(
    session: Session, asof: date, *, created_at: datetime, engine_identity_value: str | None = None
) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=created_at, provider="seed", benchmark="SPY",
        regime_score=60.0, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=55.0, breadth_above_200dma=60.0,
        new_high_low_json="{}", candidate_counts_json="{}",
        engine_identity=engine_identity_value,
    )
    session.add(run)
    session.flush()
    return run


def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
    """A hand-built manifest row referencing `run` -- the TEST DOUBLE the phase spec's steps (a)-(d)
    literally describe ("insert a ScannerRun + a NextSessionManifest row referencing it"), never routed
    through the full `compass._freeze_manifest` selection/candidate pipeline (that content-computation
    path is already covered end-to-end by `test_manifest_invariants.py`; these tests are about the
    schema/FK relationship + `basis_disclosure`'s read-time comparison only)."""
    manifest = NextSessionManifest(
        as_of=run.asof_date,
        version=version,
        source_run_id=run.id,
        session_delta_json="{}",
        narrative_json="{}",
        selection_json="{}",
        content_hash="stub-content-hash",
        created_at=datetime.now(timezone.utc),
        mode="at_ingest",
        frozen=True,
        generation_json=json.dumps({
            "producer": "ingest_finalize",
            "engine_identity": "stub-engine-identity",
            "source_run_created_at": compass._utc_isoformat(run.created_at),
        }),
        engine_identity="stub-engine-identity",
        manifest_hash="stub-manifest-hash",
        available_at_utc=datetime.now(timezone.utc),
        prospective_eligible=True,
    )
    session.add(manifest)
    session.flush()
    return manifest


# --- TC-3: PRAGMA foreign_keys=ON, delete the source run -- no violation, manifest untouched ------


def test_tc3_fk_on_delete_source_run_no_violation_manifest_untouched(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 11), created_at=datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc))
        session.commit()
        run_id = run.id
        manifest = _mk_manifest(session, run)
        session.commit()
        manifest_id = manifest.id
        before = {
            "source_run_id": manifest.source_run_id, "content_hash": manifest.content_hash,
            "manifest_hash": manifest.manifest_hash, "version": manifest.version,
            "available_at_utc": manifest.available_at_utc, "prospective_eligible": manifest.prospective_eligible,
            "generation_json": manifest.generation_json,
        }

    with Session(engine) as session:
        row = session.get(ScannerRun, run_id)
        session.delete(row)
        session.commit()  # must NOT raise an IntegrityError

    with Session(engine) as session:
        after_row = session.get(NextSessionManifest, manifest_id)
        assert after_row is not None
        after = {
            "source_run_id": after_row.source_run_id, "content_hash": after_row.content_hash,
            "manifest_hash": after_row.manifest_hash, "version": after_row.version,
            "available_at_utc": after_row.available_at_utc, "prospective_eligible": after_row.prospective_eligible,
            "generation_json": after_row.generation_json,
        }
    assert after == before
    assert after["source_run_id"] == run_id


# --- TC-4: rebuilt-same-as_of -- basis_disclosure reports rebuilt; manifest fields unchanged ------


def test_tc4_rebuilt_same_as_of_reports_rebuilt_fields_unchanged(engine):
    t1 = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 22, 9, 0, tzinfo=timezone.utc)
    with Session(engine) as session:
        old_run = _mk_run(session, date(2026, 8, 11), created_at=t1)
        session.commit()
        old_run_id = old_run.id
        manifest = _mk_manifest(session, old_run)
        session.commit()
        manifest_id = manifest.id
        before = {
            "source_run_id": manifest.source_run_id, "content_hash": manifest.content_hash,
            "manifest_hash": manifest.manifest_hash, "version": manifest.version,
            "available_at_utc": manifest.available_at_utc, "prospective_eligible": manifest.prospective_eligible,
        }

    with Session(engine) as session:
        old = session.get(ScannerRun, old_run_id)
        session.delete(old)
        session.commit()
        _mk_run(session, date(2026, 8, 11), created_at=t2)  # a NEW run for the SAME as_of
        session.commit()

    with Session(engine) as session:
        row = session.get(NextSessionManifest, manifest_id)
        disclosure = compass.basis_disclosure(session, row)
        assert disclosure["status"] == "rebuilt"
        assert row.source_run_id == before["source_run_id"]  # never rebound to the new run
        assert row.content_hash == before["content_hash"]
        assert row.manifest_hash == before["manifest_hash"]
        assert row.version == before["version"]
        assert row.available_at_utc == before["available_at_utc"]
        assert row.prospective_eligible == before["prospective_eligible"]


# --- TC-5 (iter-7 lesson): degenerate orphan -- no replacement run at all -- honest "unavailable" -


def test_tc5_degenerate_orphan_no_replacement_run_reports_unavailable_never_raises(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 5), created_at=datetime(2026, 8, 5, 20, 0, tzinfo=timezone.utc))
        session.commit()
        run_id = run.id
        manifest = _mk_manifest(session, run)
        session.commit()
        manifest_id = manifest.id

    with Session(engine) as session:
        old = session.get(ScannerRun, run_id)
        session.delete(old)
        session.commit()
        # deliberately NO replacement run for this as_of -- mirrors the real 2026-08-05 orphan (2
        # manifests, 0 surviving source runs, verified 2026-08-21).

    with Session(engine) as session:
        row = session.get(NextSessionManifest, manifest_id)
        disclosure = compass.basis_disclosure(session, row)  # must not raise

    assert disclosure == {
        "status": "unavailable",
        "detail": "the underlying scanner run for this as-of is no longer stored",
    }
    assert disclosure["status"] not in ("available", "rebuilt")  # never fabricated


# --- TC-6: id-reuse trap -- same numeric id, later created_at -- still `rebuilt`, never `original` -


def test_tc6_id_reuse_trap_still_reports_rebuilt_not_original(engine):
    t1 = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 22, 9, 0, tzinfo=timezone.utc)
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 11), created_at=t1)
        session.commit()
        run_id = run.id
        manifest = _mk_manifest(session, run)
        session.commit()
        manifest_id = manifest.id
        before_source_run_id = manifest.source_run_id
        before_content_hash = manifest.content_hash
        before_manifest_hash = manifest.manifest_hash

    with Session(engine) as session:
        old = session.get(ScannerRun, run_id)
        session.delete(old)
        session.commit()
        # explicitly REUSE the same numeric id N -- scanner_runs.id is a plain SQLite rowid alias (no
        # AUTOINCREMENT, no sqlite_sequence), so a real delete/recreate can land here incidentally
        # (docs/goal.md J-11 step 11). Constructed directly/deterministically rather than relying on
        # SQLite's max(rowid)+1 timing.
        reused = ScannerRun(
            id=run_id, asof_date=date(2026, 8, 11), created_at=t2, provider="seed", benchmark="SPY",
            regime_score=60.0, regime_label="Expansion", regime_components_json="[]",
            breadth_above_50dma=55.0, breadth_above_200dma=60.0,
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(reused)
        session.commit()

    with Session(engine) as session:
        current_run = session.get(ScannerRun, run_id)
        assert current_run.id == run_id  # numeric id genuinely reused

        row = session.get(NextSessionManifest, manifest_id)
        assert row.source_run_id == run_id == before_source_run_id  # id equality alone -- unchanged
        assert row.content_hash == before_content_hash
        assert row.manifest_hash == before_manifest_hash

        disclosure = compass.basis_disclosure(session, row)
        # id equality is NOT treated as proof of original identity -- the frozen source_run_created_at
        # (t1) differs from the reused row's actual created_at (t2), so this must read `rebuilt`.
        assert disclosure["status"] == "rebuilt"
        assert disclosure["status"] != "available"


# --- TC-7 (iter-9 lesson): per-run identity consistency -- matching AND mismatched, as two cases ---


def test_tc7_attempt_identity_consistency_matching_case(engine, cfg):
    with Session(engine) as session:
        frozen = j11_maintenance.freeze_attempt_identity(session, cfg)
    matching_run_identity = frozen["engine_identity"]
    assert j11_maintenance.check_attempt_identity_consistency(frozen, matching_run_identity) is True
    # the bare-string form of frozen_identity is accepted identically to the dict form
    assert j11_maintenance.check_attempt_identity_consistency(frozen["engine_identity"], matching_run_identity) is True


def test_tc7_attempt_identity_consistency_mismatched_case(engine, cfg):
    with Session(engine) as session:
        frozen = j11_maintenance.freeze_attempt_identity(session, cfg)
    mismatched_run_identity = "definitely-not-" + frozen["engine_identity"]
    assert j11_maintenance.check_attempt_identity_consistency(frozen, mismatched_run_identity) is False
    # fail-closed: a run with NO stamped identity (pre-stamping era / not yet persisted) is never
    # silently treated as consistent.
    assert j11_maintenance.check_attempt_identity_consistency(frozen, None) is False


# --- freeze_attempt_identity: reproducible from the SAME config, and matches compute_engine_identity --


def test_freeze_attempt_identity_matches_compute_engine_identity_and_is_reproducible(engine, cfg):
    from app.engine.engine_identity import compute_engine_identity

    with Session(engine) as session:
        first = j11_maintenance.freeze_attempt_identity(session, cfg)
        second = j11_maintenance.freeze_attempt_identity(session, cfg)

    assert first["engine_identity"] == compute_engine_identity(cfg)
    assert first["engine_identity"] == second["engine_identity"]  # same code+config -> same identity
    assert first["config_subset_hash"] == second["config_subset_hash"]


# --- capture_pre_reset_inventory: shape + counts on a small synthetic slice of the incident set -----


def test_capture_pre_reset_inventory_shape_and_counts(engine):
    covered_date = j11_maintenance.INCIDENT_DATES[0]
    absent_date = j11_maintenance.INCIDENT_DATES[1]
    with Session(engine) as session:
        run = _mk_run(session, covered_date, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        session.commit()
        _mk_manifest(session, run)
        session.commit()

    with Session(engine) as session:
        inventory = j11_maintenance.capture_pre_reset_inventory(session)

    assert inventory["incident_dates"] == [d.isoformat() for d in j11_maintenance.INCIDENT_DATES]
    covered = inventory["per_date"][covered_date.isoformat()]
    assert covered["scanner_run"]["present"] is True
    assert len(covered["manifests"]) == 1
    absent = inventory["per_date"][absent_date.isoformat()]
    assert absent["scanner_run"]["present"] is False
    assert absent["scanner_results_count"] == 0
    assert absent["manifests"] == []
    assert inventory["daily_prices"]["row_count"] == 0  # no DailyPrice rows in this tiny fixture
    assert inventory["watchlist_count"] == 0
    assert inventory["data_provider_runs_count"] == 0
    assert "zero_write_proof" not in inventory  # the CLI script adds this, not the pure function itself


def test_incident_dates_match_the_authoritative_removal_audit():
    """Guards against a transcription slip in the literal 11-date list (docs/goal.md J-11, the incident
    date set from `data_provider_runs` id=538's own cascade record)."""
    expected = [
        "2026-05-12", "2026-05-13", "2026-07-10", "2026-07-13", "2026-07-24", "2026-07-27",
        "2026-08-03", "2026-08-05", "2026-08-10", "2026-08-11", "2026-08-12",
    ]
    assert [d.isoformat() for d in j11_maintenance.INCIDENT_DATES] == expected


# ==========================================================================================================
# goal-market-compass iter-18 -- `capture_full_table_sweep` / `diff_full_table_sweeps`: the schema-agnostic
# mutation-accounting evidence for the J-11 table-create + arm live sequence (docs/goal.md J-11 step 11
# ruling requirement 4).
# ==========================================================================================================


def test_capture_full_table_sweep_covers_every_table_including_empty_ones(engine):
    with Session(engine) as session:
        sweep = j11_maintenance.capture_full_table_sweep(session)

    live_table_names = {t.name for t in SQLModel.metadata.sorted_tables}
    assert set(sweep["table_names"]) == live_table_names
    assert sweep["table_count"] == len(live_table_names)
    # an empty table (every table in a fresh fixture) reports count=0 and None aggregates, never an error
    for name in sweep["table_names"]:
        row = sweep["per_table"][name]
        assert row["count"] == 0
        assert row["min_rowid"] is None
        assert row["max_rowid"] is None
        assert row["fingerprint"]  # still hashes cleanly on an all-None payload


def test_capture_full_table_sweep_fingerprint_changes_when_a_row_is_added(engine):
    with Session(engine) as session:
        before = j11_maintenance.capture_full_table_sweep(session)

    with Session(engine) as session:
        session.add(
            ScannerRun(
                asof_date=date(2026, 1, 2), created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Expansion",
                regime_components_json="[]", breadth_above_50dma=50.0, breadth_above_200dma=50.0,
                new_high_low_json="{}", candidate_counts_json="{}",
            )
        )
        session.commit()

    with Session(engine) as session:
        after = j11_maintenance.capture_full_table_sweep(session)

    assert before["per_table"]["scanner_runs"]["fingerprint"] != after["per_table"]["scanner_runs"]["fingerprint"]
    assert after["per_table"]["scanner_runs"]["count"] == 1
    # every OTHER table's fingerprint is untouched
    for name in before["table_names"]:
        if name == "scanner_runs":
            continue
        assert before["per_table"][name]["fingerprint"] == after["per_table"][name]["fingerprint"]


def test_diff_full_table_sweeps_clean_when_nothing_changed(engine):
    with Session(engine) as session:
        before = j11_maintenance.capture_full_table_sweep(session)
        after = j11_maintenance.capture_full_table_sweep(session)

    diff = j11_maintenance.diff_full_table_sweeps(before, after)
    assert diff == {
        "unexpected_new_tables": [], "unexpected_removed_tables": [], "changed_existing_tables": [],
        "expected_new_tables_present": [], "clean": True,
    }


def test_diff_full_table_sweeps_flags_an_unexpected_new_table_and_an_unexpected_change(engine):
    with Session(engine) as session:
        before = j11_maintenance.capture_full_table_sweep(session)

    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE surprise_table (id INTEGER PRIMARY KEY)")
    with Session(engine) as session:
        session.add(
            ScannerRun(
                asof_date=date(2026, 1, 2), created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Expansion",
                regime_components_json="[]", breadth_above_50dma=50.0, breadth_above_200dma=50.0,
                new_high_low_json="{}", candidate_counts_json="{}",
            )
        )
        session.commit()

    with Session(engine) as session:
        after = j11_maintenance.capture_full_table_sweep(session)

    diff = j11_maintenance.diff_full_table_sweeps(before, after)
    assert diff["unexpected_new_tables"] == ["surprise_table"]
    assert diff["changed_existing_tables"] == ["scanner_runs"]
    assert diff["unexpected_removed_tables"] == []
    assert diff["clean"] is False


def test_diff_full_table_sweeps_expected_new_table_is_not_flagged():
    """The exact shape the live J-11 sequence needs: `maintenance_boundaries` appearing between the
    before/after sweeps is EXPECTED (it's the one authorized new table), and must not itself flag the
    diff unclean when nothing else changed. Exercised against SYNTHETIC sweep dicts (`diff_full_table_
    sweeps` is a pure function) rather than a live fixture engine -- the `engine` fixture above already
    creates `maintenance_boundaries` via `SQLModel.metadata.create_all` (it is now a real committed
    model), so a live DB cannot model "table genuinely absent, then created" for THIS one table name."""
    unrelated = {"count": 0, "min_rowid": None, "max_rowid": None, "sum_rowid": None, "fingerprint": "x"}
    before = {
        "table_names": ["scanner_runs"], "table_count": 1,
        "per_table": {"scanner_runs": unrelated},
    }
    after = {
        "table_names": ["maintenance_boundaries", "scanner_runs"], "table_count": 2,
        "per_table": {
            "scanner_runs": unrelated,
            "maintenance_boundaries": {
                "count": 1, "min_rowid": 1, "max_rowid": 1, "sum_rowid": 1, "fingerprint": "y",
            },
        },
    }

    diff = j11_maintenance.diff_full_table_sweeps(before, after, expected_new_tables=("maintenance_boundaries",))
    assert diff["unexpected_new_tables"] == []
    assert diff["expected_new_tables_present"] == ["maintenance_boundaries"]
    assert diff["changed_existing_tables"] == []
    assert diff["clean"] is True
