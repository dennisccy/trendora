"""goal-market-compass iter-16 -- J-11 "OWNER RULING -- pre-boot incident guard required" tests
(Goals 6-7). Exclusively fixture/in-memory SQLite -- never `apps/backend/data/trendora.db`, and the live
backend is never booted anywhere in this file. The `ensure_latest_snapshot` integration tests below
monkeypatch `warmup_mod.run_scan` to a recording stub (the SAME pattern `test_warmup.py`'s own
`run_scan`-failure test already uses: `monkeypatch.setattr(warmup_mod, "run_scan", _boom)`) rather than
exercising the real scanner engine -- this file tests the GUARD's wiring, not the scanner's own
correctness (covered elsewhere, and doing so here would need the heavy seeded-DB fixtures `test_warmup.py`
already pays for once).

goal-market-compass iter-17 additions (below, `test_iter17_*` naming -- deliberately a NEW numbering
space, never reusing this file's existing `tc23`-`tc30` labels, which key to iter-16's OWN internal
numbering; reusing "tc4"/"tc5" etc. against two different meanings in the same file would be a
readability trap): the owner's 9 lettered test cases (A)-(I) from "OWNER RULING -- J-11
maintenance-boundary lifecycle AUTHORIZED" (docs/goal.md J-11 step 11), mapped to THIS iteration's own
phase-spec TC-1 through TC-5 (TC-6 through TC-10, cases D/H/I, live in
`test_j11_preboot_guard_cli_scripts.py` -- they need the new arm/disarm scripts). Cases (A)/(C)/(G) are
already covered by the iter-16 tests above (`test_tc25_no_boundary_registered_is_a_true_noop` /
`test_active_boundary_does_not_block_a_date_outside_its_own_set` /
`test_tc23_ensure_latest_snapshot_skips_write_and_returns_none_when_blocked` + siblings) and are
deliberately NOT duplicated here."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import load_config
from app.engine import j11_maintenance as jm
from app.engine import j11_preboot_guard as guard
# `data_manager` MUST be imported (or transitively triggered) before `warmup` -- `warmup` <-> `data_manager`
# <-> `compass` <-> `readiness` is a genuine, PRE-EXISTING circular import in this codebase; importing
# `warmup` completely fresh with nothing else already primed fails to resolve it. `test_warmup.py`'s own
# `from app.engine import data_manager, prices, warmup as warmup_mod` already depends on this exact
# ordering -- mirrored here rather than reordered, never "fixed" (out of this iteration's narrow scope).
from app.engine import data_manager, warmup as warmup_mod  # noqa: F401
from app.models import DailyPrice, MaintenanceBoundary, ScannerRun


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture()
def cfg():
    return load_config()


TEST_DATE = date(2026, 8, 12)
OTHER_DATE = date(2026, 8, 13)


# --- register_boundary / clear_boundary -- generic, incident-agnostic, idempotent by name -------------


def test_register_boundary_is_idempotent_by_name_and_updates_in_place(engine):
    with Session(engine) as session:
        first = guard.register_boundary(session, name="test-boundary", dates=[TEST_DATE], reason="r1")
        second = guard.register_boundary(session, name="test-boundary", dates=[TEST_DATE, OTHER_DATE], reason="r2")
    assert first.id == second.id  # same row, updated in place -- never a duplicate

    with Session(engine) as session:
        rows = session.exec(select(MaintenanceBoundary)).all()
    assert len(rows) == 1
    assert json.loads(rows[0].quarantined_dates_json) == sorted([TEST_DATE.isoformat(), OTHER_DATE.isoformat()])
    assert rows[0].reason == "r2"
    assert rows[0].active is True


def test_clear_boundary_sets_inactive_and_is_a_noop_when_absent(engine):
    with Session(engine) as session:
        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r", active=True)
    with Session(engine) as session:
        cleared = guard.clear_boundary(session, "b")
    assert cleared.active is False

    with Session(engine) as session:
        noop = guard.clear_boundary(session, "does-not-exist")
    assert noop is None


def test_register_j11_incident_boundary_sources_dates_from_incident_dates_not_a_fresh_literal(engine):
    with Session(engine) as session:
        row = guard.register_j11_incident_boundary(session)
    assert json.loads(row.quarantined_dates_json) == sorted(d.isoformat() for d in jm.INCIDENT_DATES)
    assert row.active is True
    assert row.name == guard.J11_INCIDENT_BOUNDARY_NAME


# --- TC-23/24/25: refuse / allow-once-cleared / true no-op --------------------------------------------


def test_tc25_no_boundary_registered_is_a_true_noop(engine):
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result == {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}


def test_tc23_active_boundary_blocks_the_quarantined_date_with_actionable_reason(engine):
    with Session(engine) as session:
        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="incident quarantine active")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["boundary_name"] == "b"
    assert result["reason"] == "incident quarantine active"
    assert result["ambiguous"] is False


def test_active_boundary_does_not_block_a_date_outside_its_own_set(engine):
    with Session(engine) as session:
        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, OTHER_DATE)
    assert result["blocked"] is False


def test_tc24_cleared_boundary_allows_the_same_date_again(engine):
    with Session(engine) as session:
        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
        guard.clear_boundary(session, "b")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is False


# --- TC-26: genuinely state-driven -- fixture-only changes flip behaviour, guard source untouched ------


def test_tc26_fixture_state_change_flips_behavior_without_touching_guard_source(engine):
    with Session(engine) as session:
        assert guard.evaluate_boundary_for_date(session, TEST_DATE)["blocked"] is False

    with Session(engine) as session:
        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
    with Session(engine) as session:
        assert guard.evaluate_boundary_for_date(session, TEST_DATE)["blocked"] is True

    with Session(engine) as session:
        guard.clear_boundary(session, "b")
    with Session(engine) as session:
        assert guard.evaluate_boundary_for_date(session, TEST_DATE)["blocked"] is False


# --- TC-27: fails CLOSED on unreadable/ambiguous state --------------------------------------------------


def _raw_insert_boundary(session, *, name, dates_json, active_int, reason):
    session.execute(
        text(
            "INSERT INTO maintenance_boundaries (name, quarantined_dates_json, active, reason, "
            "created_at, updated_at) VALUES (:name, :dates, :active, :reason, :now, :now)"
        ),
        {
            "name": name, "dates": dates_json, "active": active_int, "reason": reason,
            "now": datetime.now(timezone.utc).isoformat(),
        },
    )
    session.commit()


def test_tc27_fails_closed_on_malformed_date_set_json_while_active(engine):
    with Session(engine) as session:
        _raw_insert_boundary(session, name="b", dates_json="not valid json{{{", active_int=1, reason="r")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["ambiguous"] is True


def test_tc27_fails_closed_on_valid_json_that_is_not_a_list_of_date_strings(engine):
    with Session(engine) as session:
        _raw_insert_boundary(session, name="b", dates_json=json.dumps({"not": "a list"}), active_int=1, reason="r")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["ambiguous"] is True


def test_tc27_fails_closed_on_missing_date_set_content_while_active(engine):
    with Session(engine) as session:
        _raw_insert_boundary(session, name="b", dates_json="", active_int=1, reason="r")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["ambiguous"] is True


def test_cleared_rows_malformed_date_set_never_triggers_ambiguous_fail_closed(engine):
    """Only ACTIVE-but-unreadable state is ambiguous -- a row explicitly marked cleared never blocks,
    regardless of what its (possibly stale/malformed) date-set says."""
    with Session(engine) as session:
        _raw_insert_boundary(session, name="b", dates_json="garbage{{{", active_int=0, reason="r")
    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is False


# --- TC-28: a partial 11-date attempt (some dates already carry a ScannerRun) stays blocked, driven -----
# --- only by the explicit flag -- never per-date inference. --------------------------------------------


def _mk_run(session, asof):
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=50.0, breadth_above_200dma=50.0,
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def test_tc28_partial_attempt_with_some_dates_already_run_stays_blocked(engine):
    partial_date, still_pending_date = jm.INCIDENT_DATES[0], jm.INCIDENT_DATES[1]
    with Session(engine) as session:
        _mk_run(session, partial_date)  # simulates a partially-completed prior regeneration attempt
        session.commit()
        guard.register_j11_incident_boundary(session, active=True)

    with Session(engine) as session:
        # the date that ALREADY has a ScannerRun is STILL blocked -- driven by the explicit active flag,
        # never by "does this date already have a run" inference.
        result_partial = guard.evaluate_boundary_for_date(session, partial_date)
        result_pending = guard.evaluate_boundary_for_date(session, still_pending_date)
    assert result_partial["blocked"] is True
    assert result_pending["blocked"] is True


# --- TC-29/TC-31: `warmup.ensure_latest_snapshot` wiring -- fixture-scoped engine, run_scan mocked out --


def _seed_one_price(session, d=TEST_DATE):
    session.add(DailyPrice(symbol="AAPL", date=d, open=1, high=2, low=0.5, close=1.5, volume=100))
    session.commit()


def test_tc23_ensure_latest_snapshot_skips_write_and_returns_none_when_blocked(engine, cfg, monkeypatch, caplog):
    with Session(engine) as session:
        _seed_one_price(session)
        guard.register_j11_incident_boundary(session, active=True)

    calls = []
    monkeypatch.setattr(warmup_mod, "run_scan", lambda *a, **k: calls.append(a))

    import logging
    caplog.set_level(logging.WARNING, logger="trendora.warmup")
    result = warmup_mod.ensure_latest_snapshot(engine, cfg)

    assert result is None  # the SAME safe shape as an empty DB -- never a crash
    assert calls == []  # run_scan never called for the blocked date -- no ScannerRun created
    assert any(TEST_DATE.isoformat() in record.message or str(TEST_DATE) in record.getMessage() for record in caplog.records)


def test_tc24_ensure_latest_snapshot_writes_normally_once_the_boundary_is_cleared(engine, cfg, monkeypatch):
    with Session(engine) as session:
        _seed_one_price(session)
        guard.register_j11_incident_boundary(session, active=True)
        guard.clear_boundary(session, guard.J11_INCIDENT_BOUNDARY_NAME)

    calls = []
    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))

    result = warmup_mod.ensure_latest_snapshot(engine, cfg)

    assert result == TEST_DATE
    assert calls == [TEST_DATE]


def test_tc25_ensure_latest_snapshot_byte_identical_when_no_boundary_registered(engine, cfg, monkeypatch):
    with Session(engine) as session:
        _seed_one_price(session)  # NO boundary registered at all -- the common no-incident case

    calls = []
    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))

    result = warmup_mod.ensure_latest_snapshot(engine, cfg)

    assert result == TEST_DATE
    assert calls == [TEST_DATE]


def test_ensure_latest_snapshot_fails_closed_on_a_guard_exception_and_never_crashes(engine, cfg, monkeypatch):
    with Session(engine) as session:
        _seed_one_price(session)

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(guard, "evaluate_boundary_for_date", _boom)
    calls = []
    monkeypatch.setattr(warmup_mod, "run_scan", lambda *a, **k: calls.append(a))

    result = warmup_mod.ensure_latest_snapshot(engine, cfg)  # must NOT raise

    assert result is None
    assert calls == []


def test_ensure_latest_snapshot_returns_none_on_empty_db_unchanged(engine, cfg):
    """Baseline sanity: the pre-existing empty-DB behavior is unaffected by this iteration's change."""
    result = warmup_mod.ensure_latest_snapshot(engine, cfg)
    assert result is None


# --- TC-30: purely additive table, created idempotently via the existing convention --------------------


def test_tc30_create_db_and_tables_creates_maintenance_boundaries_idempotently(tmp_path):
    from app.db import create_db_and_tables, make_engine

    db_path = tmp_path / "idempotent.db"
    eng = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(eng)  # first run -- creates the table fresh
    with Session(eng) as session:
        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")

    create_db_and_tables(eng)  # second run -- must be a no-op; the row must survive untouched

    with Session(eng) as session:
        rows = session.exec(select(MaintenanceBoundary)).all()
    assert len(rows) == 1
    assert rows[0].name == "b"


# ==========================================================================================================
# goal-market-compass iter-17 -- AG-8 fix + owner cases (B)/(E)/(F) + the table-absent regression.
# ==========================================================================================================

NON_INCIDENT_DATE = date(2026, 7, 23)  # phase spec TC-3's own example: "a surviving, non-incident date"


# --- TC-2/TC-3 (owner case B + the already-covered case C, re-exercised against the REAL J-11 boundary) --


def test_iter17_tc2_tc3_all_eleven_incident_dates_blocked_and_one_non_incident_date_is_not(engine):
    """Owner case (B): "once armed, all 11 incident dates are blocked" -- the iter-16 coverage only
    looped a single arbitrary date; this loops every one of `jm.INCIDENT_DATES` individually, armed via
    the REAL `register_j11_incident_boundary` (not an arbitrary single-date boundary), and also serves as
    a regression guard that the AG-8 bounded-query rewrite changed no observable behavior. TC-3's
    surviving non-incident date is asserted in the SAME armed state."""
    with Session(engine) as session:
        guard.register_j11_incident_boundary(session, active=True)

    with Session(engine) as session:
        for one_date in jm.INCIDENT_DATES:
            result = guard.evaluate_boundary_for_date(session, one_date)
            assert result["blocked"] is True, f"{one_date} should be blocked"
            assert result["boundary_name"] == guard.J11_INCIDENT_BOUNDARY_NAME
            assert result["ambiguous"] is False

        non_incident_result = guard.evaluate_boundary_for_date(session, NON_INCIDENT_DATE)
    assert non_incident_result["blocked"] is False


# --- TC-4 (owner case E, part 1): SQL NULL `active` -- reachable ONLY via a schema that permits it --------


def _engine_with_nullable_active_column():
    """`MaintenanceBoundary.active` is declared as a plain (non-Optional) `bool`, which SQLModel maps to a
    DB-level `NOT NULL` column -- verified directly: a raw parameterized `INSERT ... VALUES (NULL)` against
    a table created by `SQLModel.metadata.create_all` raises `sqlite3.IntegrityError: NOT NULL constraint
    failed`, so TC-4's scenario is NOT reachable through the model layer at all on today's schema (the
    plan's own "confirm this before assuming the scenario is even reachable" instruction, confirmed
    negative). A NULL nonetheless models a real class of future risk this guard must survive -- e.g. an
    ADDITIVE `ALTER TABLE ... ADD COLUMN` on an existing table (this project's OWN documented migration
    convention, `.claude/project-template.md` "Schema evolves via additive ALTER TABLE... add-column
    only") leaves existing rows NULL for any new required column unless a server default is given, or a
    row written by a future/older schema variant. The fixture constructs that STATE directly: a hand-rolled
    `CREATE TABLE maintenance_boundaries` matching the real DDL exactly except `active` carries no `NOT
    NULL`, created BEFORE `SQLModel.metadata.create_all` (which has `checkfirst=True` by default and will
    skip a table that already exists), so every OTHER table still gets the normal, fully-constrained
    schema."""
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    with eng.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE maintenance_boundaries (
                id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                quarantined_dates_json VARCHAR NOT NULL,
                active BOOLEAN,
                reason VARCHAR NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
            """
        )
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX ix_maintenance_boundaries_name ON maintenance_boundaries (name)"
        )
    SQLModel.metadata.create_all(eng)  # skips maintenance_boundaries (already exists); creates everything else
    return eng


def test_null_active_row_is_not_constructible_through_the_normal_schema():
    """Documents the negative finding the fixture helper's docstring above claims -- a normal
    `SQLModel.metadata.create_all` schema genuinely rejects a NULL `active` value, so TC-4 below is
    deliberately exercised against a DIFFERENT, hand-rolled schema, never silently against the real one."""
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    with Session(eng) as session:
        with pytest.raises(Exception):
            _raw_insert_boundary(session, name="x", dates_json="[]", active_int=None, reason="r")


def test_iter17_tc4_null_active_row_blocks_and_is_flagged_ambiguous():
    eng = _engine_with_nullable_active_column()
    with Session(eng) as session:
        _raw_insert_boundary(
            session, name="null-active-boundary", dates_json=json.dumps([TEST_DATE.isoformat()]),
            active_int=None, reason="r",
        )
    with Session(eng) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["ambiguous"] is True
    assert result["boundary_name"] == "null-active-boundary"

    # the row is NOT silently excluded for a date OUTSIDE its own (unreadable) date-set either -- an
    # ambiguous row's unreadable active flag makes EVERY date unprovable, not just the ones its date-set
    # happens to name.
    with Session(eng) as session:
        other_result = guard.evaluate_boundary_for_date(session, OTHER_DATE)
    assert other_result["blocked"] is True
    assert other_result["ambiguous"] is True


# --- TC-5 (owner cases E/F): many irrelevant rows + the query itself is bounded, not just the boolean -----


def test_iter17_tc5_many_irrelevant_rows_plus_one_real_match_stays_correct_and_bounded(engine):
    with Session(engine) as session:
        for i in range(25):
            guard.register_boundary(
                session, name=f"cleared-{i}", dates=[TEST_DATE], reason="r", active=False,
            )
        for i in range(25):
            guard.register_boundary(
                session, name=f"unrelated-active-{i}", dates=[date(2030, 1, 1)], reason="r", active=True,
            )
        guard.register_boundary(session, name="the-real-one", dates=[TEST_DATE], reason="incident quarantine")

    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["boundary_name"] == "the-real-one"
    assert result["ambiguous"] is False

    # the resulting BOOLEAN alone is not sufficient evidence the query is bounded (TC-5's own wording) --
    # inspect the compiled SQL of the actual statement-builder the guard runs, independent of any fixture
    # data, and assert it carries a LIMIT clause.
    compiled_sql = str(
        guard._relevant_boundary_rows_statement().compile(compile_kwargs={"literal_binds": True})
    )
    assert "LIMIT" in compiled_sql.upper()
    assert str(guard._MAX_RELEVANT_BOUNDARY_ROWS + 1) in compiled_sql


def test_iter17_bound_exceeded_fails_closed(engine):
    """The overflow branch itself -- more active/ambiguous rows exist than the deterministic bound allows
    -- must fail CLOSED (blocked, ambiguous), never silently truncate away a row that might have matched."""
    with Session(engine) as session:
        for i in range(guard._MAX_RELEVANT_BOUNDARY_ROWS + 5):
            guard.register_boundary(
                session, name=f"filler-{i}", dates=[date(2030, 1, 1)], reason="r", active=True,
            )

    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["ambiguous"] is True


def test_iter17_two_different_active_boundaries_covering_the_same_date_still_blocks(engine):
    """Owner requirement 2 / case (E): "unexpectedly duplicated ... active-boundary state must fail
    CLOSED. Ambiguous maintenance state is never silently treated as 'not blocked'." Two DIFFERENTLY
    NAMED boundaries (the `name` column is unique, so a literal duplicate row is impossible) both
    independently covering the SAME date is exactly this shape -- the date must stay blocked regardless
    of which of the two rows the loop happens to name."""
    with Session(engine) as session:
        guard.register_boundary(session, name="overlap-a", dates=[TEST_DATE], reason="first")
        guard.register_boundary(session, name="overlap-b", dates=[TEST_DATE], reason="second")

    with Session(engine) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result["blocked"] is True
    assert result["boundary_name"] in ("overlap-a", "overlap-b")


# --- Known crux #2: table-absent (not merely table-empty) must clean-no-op, never raise -------------------


def test_iter17_table_absent_evaluates_cleanly_as_unblocked():
    """`select(MaintenanceBoundary)` against a database where `maintenance_boundaries` was never created
    at all raises `sqlalchemy.exc.OperationalError` ("no such table"), not an empty list. Every OTHER test
    in this file runs against a fixture DB where `SQLModel.metadata.create_all` already ran (the `engine`
    fixture), so none of them exercise this. This is the live-database shape TC-11 depends on: the real
    `apps/backend/data/trendora.db` currently has ZERO tables named `maintenance_boundaries`."""
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    # Deliberately NO create_all() call at all -- not even the OTHER tables exist on this engine.
    with Session(eng) as session:
        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
    assert result == {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
