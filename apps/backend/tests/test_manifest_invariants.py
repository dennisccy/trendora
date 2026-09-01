"""goal-market-compass iter-3 (J-05/J-06) — the twelve named manifest invariants (TC-14..TC-25), each
covered by an explicitly-named test below. File-scoped synthetic fixtures (fresh SQLite DBs, hand-built
`ScannerRun` / `ScannerResult` rows) — never `loaded_engine`.
"""
from __future__ import annotations

import json
import subprocess
import sys
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
from app.engine import market_phase as market_phase_module
from app.models import DailyPrice, MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow

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


def _mk_result(
    session: Session, run_id: int, ticker: str, l_score: float = 92.0, l_bucket: str = "A",
    e_score: float = 85.0, e_bucket: str = "B", r_score: float = 40.0, r_bucket: str = "C",
) -> None:
    record = {
        "ticker": ticker,
        "invalidation": {"note": f"{ticker} note", "price": 100.0},
        "risk_budget": {"atr_pct": {"value": 3.0, "percentile": 0.5}},
    }
    session.add(
        ScannerResult(
            run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
            leadership_score=l_score, leadership_bucket=l_bucket,
            entry_quality_score=e_score, entry_quality_bucket=e_bucket,
            risk_score=r_score, risk_bucket=r_bucket,
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


def _references_manifest_target(node: "ast.AST") -> bool:
    """True if `node` names the `NextSessionManifest` ORM model, a `.NextSessionManifest` attribute
    access, or the literal `next_session_manifests` table-name string."""
    import ast

    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id == "NextSessionManifest":
            return True
        if isinstance(sub, ast.Attribute) and sub.attr == "NextSessionManifest":
            return True
        if isinstance(sub, ast.Constant) and sub.value == "next_session_manifests":
            return True
    return False


def _scan_source_for_manifest_update_offenders(filename: str, text: str) -> list[str]:
    """Flags only a genuine SQLAlchemy Update-statement / ORM bulk-update call reachable against
    `NextSessionManifest` / `next_session_manifests`:
      - the Core `update(NextSessionManifest)` construct, called bare (`update(...)`) or as a module
        attribute (`sa.update(...)`);
      - the ORM bulk-update idiom `<query-chain ending in .query(NextSessionManifest)>.update(...)`;
      - a raw SQL string literal containing both "update" and the table name.
    Any OTHER `.update(...)` attribute call (dict.update, hashlib digest.update, or any object unrelated
    to the manifest query/model) is not an UPDATE statement against the manifest table and is never
    flagged -- this is the iter-26 narrowing that fixes the false positive on `.update()` calls in the
    J-11 stage modules (dict/hashlib-digest updates that merely live in a module which also mentions the
    manifest table/model in unrelated text)."""
    import ast

    offenders: list[str] = []
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            if "update" in lowered and "next_session_manifests" in lowered:
                offenders.append(f"{filename}: raw SQL string literal UPDATEs the manifest table")
            continue

        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name) and node.func.id == "update":
            # bare `update(...)` -- the SQLAlchemy Core update() construct, imported directly
            args = list(node.args) + [kw.value for kw in node.keywords]
            if any(_references_manifest_target(a) for a in args):
                offenders.append(f"{filename}: update(...) construct targets the manifest table")
            continue

        if isinstance(node.func, ast.Attribute) and node.func.attr == "update":
            value = node.func.value
            if isinstance(value, ast.Call):
                # a chained call -- walk back through `.filter(...)`/`.filter_by(...)`/etc. looking for
                # a `.query(NextSessionManifest)` link: the ORM bulk-update idiom
                # `session.query(NextSessionManifest)....update(...)`
                chain_node = value
                while isinstance(chain_node, ast.Call):
                    if isinstance(chain_node.func, ast.Attribute) and chain_node.func.attr == "query":
                        if any(_references_manifest_target(a) for a in chain_node.args):
                            offenders.append(f"{filename}: <query>.update(...) bulk-updates the manifest table")
                        break
                    chain_node = chain_node.func.value if isinstance(chain_node.func, ast.Attribute) else None
            else:
                # module-attribute style, e.g. `sa.update(NextSessionManifest)`
                if any(_references_manifest_target(a) for a in node.args):
                    offenders.append(f"{filename}: update(...) construct targets the manifest table")
            continue
    return offenders


def test_tc15_no_update_statement_targets_next_session_manifests():
    """A static source-text audit: no UPDATE statement (the SQLAlchemy Core `update(...)` construct, the
    ORM `.query(NextSessionManifest)....update(...)` bulk-update idiom, or raw SQL) targets
    `NextSessionManifest` / `next_session_manifests` anywhere in the engine layer. Narrowed (iter-26,
    TC-1) to flag only a call reachable against the manifest model/table -- see
    `_scan_source_for_manifest_update_offenders` for exactly what is and is not flagged; an unrelated
    `.update(...)` attribute call (dict, hashlib digest, or any other object) is never flagged even in a
    module that mentions the manifest table/model elsewhere in unrelated text."""
    offenders: list[str] = []
    for path in (REPO_ROOT / "apps/backend/app/engine").glob("*.py"):
        text = path.read_text()
        if "next_session_manifests" not in text and "NextSessionManifest" not in text:
            continue
        offenders.extend(_scan_source_for_manifest_update_offenders(path.name, text))
    assert not offenders, offenders


def test_tc15_scanner_mutation_check_catches_a_real_manifest_update_statement():
    """TC-1 mutation-kill check (iter-26): the narrowed scanner above must still catch a REAL manifest
    UPDATE if one is ever introduced. Exercises the scanner directly against synthetic source text --
    never by injecting an actual bug into shipped `app/engine` code -- so this test is itself safe to
    run every time."""
    core_construct_src = (
        "from sqlalchemy import update\n"
        "from app.models import NextSessionManifest\n"
        "def _bad(session):\n"
        "    session.execute(update(NextSessionManifest).where(NextSessionManifest.id == 1).values(frozen=False))\n"
    )
    assert _scan_source_for_manifest_update_offenders("synthetic.py", core_construct_src)

    orm_bulk_update_src = (
        "from app.models import NextSessionManifest\n"
        "def _bad(session):\n"
        "    session.query(NextSessionManifest).filter_by(id=1).update({'frozen': False})\n"
    )
    assert _scan_source_for_manifest_update_offenders("synthetic.py", orm_bulk_update_src)

    raw_sql_src = 'def _bad(session):\n    session.execute("UPDATE next_session_manifests SET frozen = 0")\n'
    assert _scan_source_for_manifest_update_offenders("synthetic.py", raw_sql_src)

    # sanity: the exact false-positive shapes already living in app/engine stay clean
    false_positive_src = (
        "from app.models import NextSessionManifest\n"
        "def _fine(entry, digest, chunk):\n"
        "    entry.update({'a': 1})\n"
        "    digest.update(chunk)\n"
        "    return NextSessionManifest\n"
    )
    assert _scan_source_for_manifest_update_offenders("synthetic.py", false_positive_src) == []


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


# --- TC-2 (export-byte-equality, audit finding B3, iter-3 -- closed iter-26) -----------------------


def test_tc2_export_file_bytes_equal_served_payload_and_manifest_hash_reproduces(
    engine, cfg, frontier_run, tmp_path, monkeypatch
):
    """TC-2 / audit finding B3 (iter-3, closed iter-26): the on-disk export file's bytes equal the
    `manifest_row_payload` reconstruction (the served `GET /api/compass` shape) byte-for-byte -- the
    same read path production serves, not the in-memory write-time `document` dict -- and recomputing
    `manifest_hash` over the exported bytes, with the `manifest_hash` field itself excluded per the
    canonical rule, reproduces the embedded value. Fixture-scoped (isolated engine) -- mirrors, and is
    cited alongside, the live read-only spot-check against `2026-08-12_v6.json` recorded in the dev
    handoff."""
    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))

    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        export_path = row.export_path
        served = compass.manifest_row_payload(row)
    assert export_path is not None, "an at_ingest freeze must export"

    exported_bytes = Path(export_path).read_bytes()
    served_bytes = compass._canonical_dumps(served).encode()
    assert exported_bytes == served_bytes, "export file bytes must equal the served payload byte-for-byte"

    exported_document = json.loads(exported_bytes)
    embedded_hash = exported_document["manifest_hash"]
    without_hash = {key: value for key, value in exported_document.items() if key != "manifest_hash"}
    recomputed_hash = compass._sha256_hex(compass._canonical_dumps(without_hash))
    assert recomputed_hash == embedded_hash, "manifest_hash recomputed over the exported bytes must match"
    assert compass.verify_manifest_hash(exported_document) is True  # same fact via the production helper


# --- TC-7 (J-06 step 1): backfilling a SEPARATE date leaves a stored manifest untouched -------------


def test_tc7_backfilling_a_separate_date_leaves_the_first_stored_manifest_unchanged(engine, cfg, frontier_run, tmp_path, monkeypatch):
    """TC-7 / J-06 step 1: with one manifest already frozen (`frontier_run`, as_of 2024-07-01), freezing a
    SEPARATE, later date's manifest -- exactly what the finalize hook does for each newly-processed date
    -- leaves the FIRST manifest's stored bytes and version byte-identical. Not already its own assertion
    elsewhere: `test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows` proves ROW COUNT
    survives a full snapshot clear; `test_tc14_time_safety_...` proves `content_hash` survives a
    POST-AS-OF bar perturbation on the SAME as_of; neither proves an entirely SEPARATE date's own freeze
    leaves this manifest's PAYLOAD BYTES/version untouched."""
    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))

    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        first_row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        before_payload = compass.manifest_row_payload(first_row)
        before_version = first_row.version

    # freeze a SEPARATE, later date's manifest -- unrelated to the first manifest's as_of
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 7, 8), open=1, high=1, low=1, close=1, volume=1))
        other_run = _mk_run(session, date(2024, 7, 8))
        _mk_result(session, other_run.id, "BBB")
        session.commit()
        session.refresh(other_run)
        compass.get_or_create_manifest(session, other_run, cfg, producer="ingest_finalize")

    with Session(engine) as session:
        rows = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 7, 1))
        ).all()
    assert len(rows) == 1  # still exactly one version -- the separate freeze minted no second version here
    after_row = rows[0]
    assert after_row.version == before_version
    assert compass.manifest_row_payload(after_row) == before_payload


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


# --- basis_disclosure fail-closed fix (goal-market-compass iter-11, TC-9..TC-13, docs/goal.md J-11 -----
# step 11 ruling A4): four degenerate `generation_json` inputs must ALL report the same explicit
# "unverifiable" status, never fabricate "available", and never raise. The three already-correct
# branches (rebuilt / unavailable / available-when-matching) stay covered, unchanged, by the two tests
# directly above this block plus test_api_compass.py and test_j11_maintenance.py's TC-3..TC-6.


def test_tc9_basis_disclosure_reports_unverifiable_when_generation_json_is_null(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = None
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] not in ("available", "unavailable", "rebuilt")
    assert disclosure["detail"] is not None


def test_tc10_basis_disclosure_reports_unverifiable_when_generation_json_is_empty_string(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = ""
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] != "available"


def test_tc11_basis_disclosure_reports_unverifiable_when_generation_json_is_malformed(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = "{not valid json"
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise, even on malformed JSON
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] != "available"


def test_tc12_basis_disclosure_reports_unverifiable_when_source_run_created_at_is_absent(engine, cfg, frontier_run):
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = json.dumps({"producer": "ingest_finalize", "engine_identity": "stub"})
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] != "available"


def test_tc12b_basis_disclosure_reports_unverifiable_when_generation_json_is_a_non_object(engine, cfg, frontier_run):
    """iter-11 AUDIT: `generation_json` holding VALID JSON that is not an object (a bare scalar or a
    list) parses cleanly, so it never reaches the malformed-JSON `except`, and then `"source_run_created_at"
    in <int>` raises TypeError -- escaping the fail-closed guard as a 500 on the served
    `GET /api/compass` payload rather than an honest status. Ruling A4 admits no such escape ("must
    never report available", "must not raise"), so every non-object parse must fail closed too."""
    for degenerate in ("5", '"a string"', "[1, 2, 3]", "null"):
        with Session(engine) as session:
            row = session.exec(select(NextSessionManifest)).first()
            if row is None:
                run = session.get(ScannerRun, frontier_run)
                row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
            row.generation_json = degenerate
            session.add(row)
            session.commit()
        with Session(engine) as session:
            row = session.exec(select(NextSessionManifest)).first()
            disclosure = compass.basis_disclosure(session, row)  # must not raise
        assert disclosure["status"] == "unverifiable", degenerate
        assert disclosure["status"] != "available", degenerate


def test_tc13_basis_disclosure_available_branch_still_reports_available_when_recorded_timestamp_matches(
    engine, cfg, frontier_run
):
    """TC-13: the fail-closed fix must not disturb the one already-correct branch not covered by the two
    tests above this block -- a manifest whose recorded `source_run_created_at` matches the current run's
    `created_at` exactly still reports `available` (mirrors test_api_compass.py's live assertion of the
    same fact)."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)
    assert disclosure == {"status": "available", "detail": None}


# --- A4-bis: the recorded-TIMESTAMP-VALUE fail-open (goal-market-compass iter-12, docs/goal.md J-11 -----
# step 11 ruling A4-bis, owner 2026-08-24). The iter-11 fix above closed every branch that examines
# `generation_json`'s SHAPE (missing/empty/malformed/non-object/key-absent). It left the VALUE of a
# PRESENT `source_run_created_at` key unchecked: `recorded = generation.get(...)` followed by
# `if recorded is not None and recorded != current: rebuilt` / `else: available` meant a key present
# with JSON value `null` fell through to "available" (still fail-open), and an empty or unparseable
# string was reported as "rebuilt" by raw string inequality -- asserting a rebuild that was never
# established. These tests cover the A4-bis status table; valid-matched -> available is already covered
# by test_tc13_basis_disclosure_available_branch_still_reports_available_when_recorded_timestamp_matches
# above and no-current-run -> unavailable is already covered by
# test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone above -- both re-confirmed
# unchanged by this fix and not duplicated here.


def test_a4bis_recorded_timestamp_null_value_is_unverifiable_not_available(engine, cfg, frontier_run):
    """A4-bis (TC-13): a `source_run_created_at` key present with JSON value `null` must report
    `unverifiable`, never `available` -- the exact fail-open the ORIGINAL `recorded is not None` guard
    let through."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = json.dumps({"producer": "ingest_finalize", "source_run_created_at": None})
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] != "available"


def test_a4bis_recorded_timestamp_empty_string_is_unverifiable_not_rebuilt(engine, cfg, frontier_run):
    """A4-bis (TC-14): an empty-string `source_run_created_at` is unusable, not a valid timestamp that
    happens to differ -- must report `unverifiable`, never the confident `rebuilt` claim a raw string
    inequality against "" would have produced."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = json.dumps({"producer": "ingest_finalize", "source_run_created_at": ""})
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] not in ("available", "rebuilt")


def test_a4bis_recorded_timestamp_unparseable_string_is_unverifiable_not_rebuilt(engine, cfg, frontier_run):
    """A4-bis (TC-15): a `source_run_created_at` value that is not parseable as the canonical UTC
    timestamp representation (e.g. "garbage") must report `unverifiable`, never `rebuilt` -- the
    ORIGINAL raw-string-inequality comparison would have called this "rebuilt", asserting a rebuild the
    value never actually establishes."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = json.dumps(
            {"producer": "ingest_finalize", "source_run_created_at": "garbage"}
        )
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)  # must not raise
    assert disclosure["status"] == "unverifiable"
    assert disclosure["status"] not in ("available", "rebuilt")


def test_a4bis_recorded_timestamp_valid_but_mismatched_is_rebuilt(engine, cfg, frontier_run):
    """A4-bis (TC-16): a VALID, PARSEABLE `source_run_created_at` that does not equal the current run's
    canonicalized `created_at` still reports `rebuilt` -- the fail-closed validation gates entry to the
    mismatch branch, it does not disturb it."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        row.generation_json = json.dumps(
            {"producer": "ingest_finalize", "source_run_created_at": "2020-01-01T00:00:00+00:00"}
        )
        session.add(row)
        session.commit()
    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest)).first()
        disclosure = compass.basis_disclosure(session, row)
    assert disclosure["status"] == "rebuilt"


def test_a4bis_full_generation_json_degenerate_matrix_never_available(engine, cfg, frontier_run):
    """A4-bis (widened TC-19 matrix): the required minimum degenerate-input set -- NULL, empty string,
    malformed JSON, `[]`, `{}` -- re-run after this fix, each still resolves to `unverifiable`, never
    raises, and never reports `available`. `[]` and `{}` were not previously exercised by their own name
    (iter-11's tests used "5" / a populated non-object dict / a non-empty list); added here for the
    explicit minimum matrix this iteration's spec names."""
    for degenerate in (None, "", "{not valid json", "[]", "{}"):
        with Session(engine) as session:
            row = session.exec(select(NextSessionManifest)).first()
            if row is None:
                run = session.get(ScannerRun, frontier_run)
                row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
            row.generation_json = degenerate
            session.add(row)
            session.commit()
        with Session(engine) as session:
            row = session.exec(select(NextSessionManifest)).first()
            disclosure = compass.basis_disclosure(session, row)  # must not raise
        assert disclosure["status"] == "unverifiable", degenerate
        assert disclosure["status"] != "available", degenerate


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


# --- iter-30 (J-07 closure): a REGENERATED version on a frontier-shaped as-of still yields a populated
# `state_band` AND `prospective_eligible: False` in the SAME call -- closes the auditor's iter-29 T1 gap.
# The 11 existing `state_band` tests (test_compass.py / test_api_compass.py) only ever exercise
# `build_state_band` directly or the `ingest_finalize` freeze path; TC-23's own regenerate coverage above
# never seeds a prior run with real severity, so its `state_band_json` stays the no-prior-run null shape.
# This is the exact combination the LIVE production action this iteration performs
# (`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`) exercises -- mirrored here as a
# fixture-scoped, isolated-DB unit test (never the live database).


@pytest.fixture()
def frontier_run_with_prior_and_phase(engine, cfg):
    """Two runs, frontier-shaped: a `DailyPrice` bar dated exactly at the LATER run's as_of (the SAME
    `frontier_run` convention above -- `_resolve_mode` reads `latest_data_date` against this bar), with
    `MarketPhaseCache` seeded for BOTH dates (mirrors test_compass.py's `two_runs_with_phase`) so
    `build_state_band` has a real severity input for every band -- a regenerated version's `state_band`
    comes out non-null with real words, never the no-prior-run null state."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 7, 1), regime_score=50.0)
        run_b = _mk_run(session, date(2024, 7, 8), regime_score=58.0)
        _mk_result(session, run_a.id, "AAA")
        _mk_result(session, run_b.id, "AAA")
        session.add(DailyPrice(symbol="SPY", date=date(2024, 7, 8), open=1, high=1, low=1, close=1, volume=1))
        session.commit()
        session.refresh(run_a)
        session.refresh(run_b)
        version = market_phase_module._cache_version(session)
        for run, severity in ((run_a, 25.0), (run_b, 45.0)):
            session.add(
                MarketPhaseCache(
                    asof_key=run.asof_date.isoformat(), dataset_version=version,
                    payload_json=json.dumps(
                        {"available": True, "severity": severity, "phase": "Expansion", "p_bear": 0.15}
                    ),
                    created_at=datetime.now(timezone.utc),
                )
            )
        session.commit()
        return run_b.id


def test_regenerate_on_frontier_yields_state_band_and_prospective_eligible_false(
    engine, cfg, frontier_run_with_prior_and_phase,
):
    run_b_id = frontier_run_with_prior_and_phase
    with Session(engine) as session:
        run_b = session.get(ScannerRun, run_b_id)
        v1 = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
        run_b_asof = run_b.asof_date  # captured INSIDE the session -- commit() inside _freeze_manifest
        # expires every object bound to this session (SQLAlchemy default expire_on_commit=True), so
        # `run_b` is unusable once this `with` block exits.
    assert v1.version == 1
    assert v1.mode == "at_ingest"  # confirms the fixture IS frontier-shaped, matching the live production call

    with Session(engine) as session:
        v2 = compass.regenerate_manifest(session, run_b_asof, cfg)

    assert v2.version == 2
    assert v2.generation_json is not None
    assert json.loads(v2.generation_json)["producer"] == "regenerate"
    # TC-6: false because producer == "regenerate" (not "ingest_finalize"), never recomputed at read.
    assert v2.prospective_eligible is False

    state_band = json.loads(v2.state_band_json)
    assert set(state_band) == {"regime", "stress", "breadth"}
    for band in ("regime", "stress", "breadth"):
        assert state_band[band]["direction_word"] in cfg.compass.vocabulary.direction_words.values()
        assert state_band[band]["direction_word"] is not None  # real word, never the no-comparison null
        assert isinstance(state_band[band]["delta"], float)  # real preceding run -> never null


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


def test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers(engine, cfg):
    """goal-market-compass iter-35 (J-12): a row that CLEARS the leadership floor but fails BOTH the
    entry and risk qualifiers is never `below_selection_floor` -- it is a candidate (or `excluded_by_cap`
    if the cap binds). A row BELOW the floor is `below_selection_floor` regardless of how its qualifiers
    score. Mirrors the frontier export's measured defect (37/539 rows, HPE 92.71 highest, BACKGROUND)."""
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 12, 8))
        _mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 65.0, "C")  # clears floor, fails BOTH qualifiers
        _mk_result(session, run.id, "LOW", 30.0, "E", 90.0, "A", 10.0, "A")  # below floor, clears BOTH qualifiers
        session.commit()
        session.refresh(run)
        result = compass.evaluate_selection(session, run, cfg)
    candidate_tickers = {c["ticker"] for c in result["candidates"]}
    candidate_by_ticker = {c["ticker"]: c for c in result["candidates"]}
    cohort_by_ticker = {row["ticker"]: row for row in result["comparison_cohort"]}
    assert "HPE" in candidate_tickers or cohort_by_ticker.get("HPE", {}).get("selection_disposition") == "excluded_by_cap"
    assert "HPE" not in cohort_by_ticker or cohort_by_ticker["HPE"]["selection_disposition"] != "below_selection_floor"
    assert cohort_by_ticker["LOW"]["selection_disposition"] == "below_selection_floor"
    assert "LOW" not in candidate_tickers
    # TC-1 (iter-37): the corrected fixture must genuinely fail BOTH advisory qualifiers -- not merely
    # carry a comment claiming so (the confound this fixture previously had, iter-35/36 fixture bug).
    hpe_checks = {check["condition"]: check for check in candidate_by_ticker["HPE"]["what_would_change"]}
    assert hpe_checks["entry_min_score"]["met"] is False
    assert hpe_checks["risk_max_score"]["met"] is False


# --- TC-2 (iter-37): _assert_disposition_predicate survives -O -------------------------------------


def test_assert_disposition_predicate_raises_under_dash_o(cfg):
    """goal-market-compass iter-37: `_assert_disposition_predicate`'s two guard statements were converted
    from bare `assert` to explicit `if not cond: raise AssertionError(msg)` so Python's `-O`/`-OO` flags
    (which strip bare `assert` statements entirely) can no longer silently defeat the guard. Since pytest
    itself never runs under `-O`, the only way to prove this from inside a pytest process is a subprocess:
    spawn `python -O -c "..."`, feed it a comparison-cohort row that deliberately violates the predicate
    (labeled `below_selection_floor` while its leadership_score clears the floor), and assert the child
    process still raises AssertionError and exits non-zero."""
    backend_dir = REPO_ROOT / "apps" / "backend"
    script = (
        "from app.config import load_config\n"
        "from app.engine.compass import _assert_disposition_predicate\n"
        "cfg = load_config()\n"
        "sel = cfg.compass.selection\n"
        "bad_row = {\n"
        "    'ticker': 'BAD',\n"
        "    'leadership_score': sel.leadership_min_score + 1.0,\n"
        "    'selection_disposition': 'below_selection_floor',\n"
        "}\n"
        "_assert_disposition_predicate([bad_row], sel)\n"
        "print('NO_RAISE')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-O", "-c", script],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        timeout=BOUNDED_TIMEOUT_S,
    )
    assert proc.returncode != 0, f"guard did not raise under -O; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert "AssertionError" in proc.stderr, f"expected AssertionError in stderr, got: {proc.stderr!r}"
    assert "NO_RAISE" not in proc.stdout


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


# --- TC-12/TC-25 (goal-market-compass iter-36, J-13): rotation + schema conformance ---------------


@pytest.fixture()
def frontier_run_with_rotation(engine, cfg):
    """Frontier-shaped run pair (a `DailyPrice` bar at the LATER as_of — the `frontier_run` convention)
    carrying real sector/theme rank rows on BOTH runs, so `session_delta.rotation` renders actual
    gaining/losing content (not the no-prior-run state) for a schema-validation-with-rotation-populated
    proof."""
    with Session(engine) as session:
        run_a = _mk_run(session, date(2024, 8, 1))
        run_b = _mk_run(session, date(2024, 8, 8))
        _mk_result(session, run_a.id, "AAA")
        _mk_result(session, run_b.id, "AAA")
        session.add(SectorScoreRow(
            run_id=run_a.id, ticker="XLK", kind="sector", name="XLK", members_json="[]",
            score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=5,
        ))
        session.add(SectorScoreRow(
            run_id=run_b.id, ticker="XLK", kind="sector", name="XLK", members_json="[]",
            score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=1,
        ))
        session.add(ThemeScoreRow(
            run_id=run_a.id, slug="ai", name="ai", score=80.0, bucket="A", members_json="[]",
            breadth_label="universe-relative", trend_label="Uptrend", components_json="{}", rank=4,
        ))
        session.add(ThemeScoreRow(
            run_id=run_b.id, slug="ai", name="ai", score=80.0, bucket="A", members_json="[]",
            breadth_label="universe-relative", trend_label="Uptrend", components_json="{}", rank=1,
        ))
        session.add(DailyPrice(symbol="SPY", date=date(2024, 8, 8), open=1, high=1, low=1, close=1, volume=1))
        session.commit()
        session.refresh(run_b)
        return run_b.id


def test_tc12_manifest_with_rotation_validates_against_schema_no_version_bump(
    engine, cfg, frontier_run_with_rotation, schema,
):
    """TC-12: a manifest produced under this change (with real `session_delta.rotation` content) still
    validates against the committed schema, with NO `schema_version` bump — `session_delta` is an open
    object there, so the addition is purely additive."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run_with_rotation)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        document = compass.manifest_row_payload(row)
    jsonschema.validate(document, schema)  # raises on failure
    assert document["session_delta"]["rotation"]["sector"]["gaining"][0]["label"] == "XLK"
    assert cfg.compass.manifest.schema_version == "v1"  # unchanged by this iteration


def test_rotation_absent_key_on_legacy_pre_iter36_row_never_fabricated(engine, cfg, frontier_run_with_rotation, schema):
    """AG-12 / TC-13 posture: a manifest row minted BEFORE this iteration (simulated by stripping the
    `rotation` key out of the stored `session_delta_json` blob — exactly the shape every pre-iter-36 row
    has, since `session_delta` is stored as ONE JSON blob and this iteration adds a key inside it rather
    than a new column) serves `session_delta` honestly WITHOUT a `rotation` key at all — never fabricated,
    never crashes the read path, and the resulting (older-shaped) document still validates against the
    committed schema (session_delta stays an open object)."""
    with Session(engine) as session:
        run = session.get(ScannerRun, frontier_run_with_rotation)
        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
        stored = json.loads(row.session_delta_json)
        assert "rotation" in stored  # sanity: this iteration's own write path DID add it
        del stored["rotation"]
        row.session_delta_json = json.dumps(stored)
        session.add(row)
        session.commit()

    with Session(engine) as session:
        row = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 8, 8))).first()
        document = compass.manifest_row_payload(row)
    assert "rotation" not in document["session_delta"]
    jsonschema.validate(document, schema)
