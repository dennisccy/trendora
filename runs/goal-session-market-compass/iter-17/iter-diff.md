# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/engine/j11_preboot_guard.py b/apps/backend/app/engine/j11_preboot_guard.py
index f93ba281..a5f6bf79 100644
--- a/apps/backend/app/engine/j11_preboot_guard.py
+++ b/apps/backend/app/engine/j11_preboot_guard.py
@@ -31,6 +31,20 @@ row whose `active` flag or `quarantined_dates_json` cannot be read/parsed cleanl
 (never silently skipped, never treated as cleared) -- "fails CLOSED on missing/unreadable/ambiguous
 state, never fails open." An explicitly CLEARED row (`active=False`) never blocks, regardless of what its
 date-set contains.
+
+**goal-market-compass iter-17 (AG-8 fix).** The owner's "OWNER RULING -- J-11 maintenance-boundary
+lifecycle AUTHORIZED" (docs/goal.md J-11 step 11, implementation requirement 3) flagged
+`evaluate_boundary_for_date`'s original `select(MaintenanceBoundary)` as an unbounded whole-table ORM
+load on a path every boot crosses. It is now (a) filtered to only the rows that can possibly matter --
+`active IS NOT FALSE`, never `active == True` alone (SQL's three-valued comparison logic silently drops
+`active IS NULL` rows under plain equality -- the exact trap the ruling names; `IS NOT` never yields NULL,
+so an unreadable/NULL-active row is always fetched, never silently excluded); (b) column-projected to
+only the four fields the decision needs; and (c) deterministically bounded via `.limit(...)`, failing
+CLOSED (blocked, ambiguous) if the bound is exceeded rather than silently truncating a real match away.
+Table-absence (the additive `maintenance_boundaries` table simply never created, because ordinary boot's
+`create_db_and_tables()` never ran while maintenance isolation kept the live backend un-booted) is treated
+as the SAME true no-op as "table exists, zero rows" -- `select(...)` against an absent table raises
+`OperationalError`, which is checked for explicitly rather than allowed to propagate.
 """
 from __future__ import annotations
 
@@ -38,6 +52,7 @@ import json
 from datetime import date, datetime, timezone
 from typing import Iterable, Optional
 
+from sqlalchemy import inspect as sa_inspect
 from sqlmodel import Session, select
 
 from app.engine import j11_maintenance
@@ -123,35 +138,105 @@ def register_j11_incident_boundary(
 # The fail-closed, state-driven core check -- contains NO incident-specific conditional of any kind.
 # ----------------------------------------------------------------------------------------------
 
+# goal-market-compass iter-17 -- AG-8 fix (owner ruling, docs/goal.md J-11 step 11, implementation
+# requirement 3: "apply a deterministic finite bound ... and fail closed if the bound is exceeded").
+# Generous headroom over any realistic number of named maintenance boundaries this project will ever
+# register at once (today: exactly one, "j11-incident-recovery") -- deterministic and finite, never an
+# unbounded whole-table scan. No `j11_*.py` module is in `test_no_magic_numbers.CALC_FILES` (verified);
+# this is boot-path plumbing, not a scoring/decision threshold, so -- following the established precedent
+# of inline module constants elsewhere in this same file family (e.g.
+# `j11_avb_correction._RATIO_RELATIVE_TOLERANCE`) -- this bound is a plain module constant here, not a
+# new `config.yaml` entry.
+_MAX_RELEVANT_BOUNDARY_ROWS = 100
+
+
+def _relevant_boundary_rows_statement():
+    """The bounded, filtered, column-projected statement the boot path actually runs -- factored out as
+    its own pure statement-builder (no session, no execution) so a test can inspect the emitted SQL/LIMIT
+    clause directly, never only the boolean result of running it.
+
+    Filter: `active IS NOT FALSE` (SQLAlchemy `.isnot(False)`) -- NEVER `active == True` alone. Under
+    SQL's three-valued comparison logic, `NULL = TRUE` evaluates to NULL/unknown (not TRUE), so plain
+    equality SILENTLY DROPS `active IS NULL` rows -- the exact regression trap the owner's ruling names.
+    `IS NOT` is defined to never itself yield NULL: `NULL IS NOT FALSE` evaluates to true, so an
+    unreadable/NULL-active row is always fetched here and always reaches the ambiguous/fail-closed branch
+    below in `evaluate_boundary_for_date` -- never silently excluded by the query itself. An explicitly
+    cleared row (`active=False`) IS excluded here -- by design; clearing is authoritative (docs above).
+
+    Projection: only the four fields the decision logic reads (`name`, `active`,
+    `quarantined_dates_json`, `reason`) -- never `id`/`created_at`/`updated_at`, which this function never
+    inspects (owner requirement 3: "project only the fields the decision needs where practical").
+
+    Bound: `.limit(_MAX_RELEVANT_BOUNDARY_ROWS + 1)` -- fetches ONE row past the bound so the caller can
+    distinguish "exactly at the bound" from "more matching rows exist than the bound allows" and fail
+    closed on the latter, rather than silently truncating away a row that might have matched."""
+    return (
+        select(
+            MaintenanceBoundary.name,
+            MaintenanceBoundary.active,
+            MaintenanceBoundary.quarantined_dates_json,
+            MaintenanceBoundary.reason,
+        )
+        .where(MaintenanceBoundary.active.isnot(False))
+        .limit(_MAX_RELEVANT_BOUNDARY_ROWS + 1)
+    )
+
 
 def evaluate_boundary_for_date(session: Session, one_date: date) -> dict:
     """Whether `one_date` currently falls inside an ACTIVE, cleanly-readable maintenance boundary.
 
     Returns `{"blocked": bool, "boundary_name": str|None, "reason": str|None, "ambiguous": bool}`.
 
+      - The `maintenance_boundaries` table does not exist at all -> `blocked=False` -- the SAME true
+        no-op as "table exists, zero rows" (iter-17: the table is purely additive and normally minted by
+        ordinary boot, which maintenance isolation deliberately prevents; its absence is a consequence of
+        the quarantine itself, never an error state).
       - No `MaintenanceBoundary` rows registered at all -> `blocked=False` (the true no-op / common
         no-incident case).
+      - More than `_MAX_RELEVANT_BOUNDARY_ROWS` active-or-ambiguous rows exist -> `blocked=True,
+        ambiguous=True` -- the deterministic bound was exceeded; fails CLOSED rather than scanning an
+        unbounded set (AG-8).
       - A row with `active=True` whose parsed `quarantined_dates_json` contains `one_date` ->
         `blocked=True`, naming that row and its `reason`.
-      - A row that is explicitly cleared (`active=False`) never blocks, regardless of its date-set.
-      - A row whose `active` flag is unreadable, or whose `quarantined_dates_json` is missing, empty,
-        malformed JSON, or not a JSON list of date strings, while otherwise appearing active-ish (not
-        provably cleared) -> `blocked=True, ambiguous=True` -- fails CLOSED rather than silently
-        skipping an unreadable row or assuming it is cleared.
+      - A row that is explicitly cleared (`active=False`) never blocks, regardless of its date-set --
+        excluded by the query's own filter before any Python-level logic runs.
+      - A row whose `active` flag is unreadable (SQL `NULL`), or whose `quarantined_dates_json` is
+        missing, empty, malformed JSON, or not a JSON list of date strings, while otherwise appearing
+        active-ish (not provably cleared) -> `blocked=True, ambiguous=True` -- fails CLOSED rather than
+        silently skipping an unreadable row or assuming it is cleared.
 
     This function performs ONLY read queries; it never writes."""
-    rows = session.exec(select(MaintenanceBoundary)).all()
+    # Table-absence check FIRST -- `select(...)` against a table that does not exist raises
+    # `sqlalchemy.exc.OperationalError` ("no such table"), not an empty result; checked explicitly here so
+    # that exception never propagates. A genuinely unexpected inspection failure (anything other than a
+    # clean "table present/absent" answer) is left to the CALLER's own fail-closed wrapping
+    # (`warmup.ensure_latest_snapshot`'s try/except already treats any exception here as blocked), never
+    # silently swallowed inside this function.
+    if not sa_inspect(session.get_bind()).has_table(MaintenanceBoundary.__tablename__):
+        return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+    rows = session.exec(_relevant_boundary_rows_statement()).all()
+    if len(rows) > _MAX_RELEVANT_BOUNDARY_ROWS:
+        return {
+            "blocked": True,
+            "boundary_name": None,
+            "reason": (
+                f"more than {_MAX_RELEVANT_BOUNDARY_ROWS} active/unreadable maintenance-boundary rows "
+                "exist -- failing closed rather than scanning an unbounded set (AG-8)"
+            ),
+            "ambiguous": True,
+        }
     if not rows:
         return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
 
     date_key = one_date.isoformat()
     ambiguous_names: list[str] = []
     for row in rows:
+        # `active=False` rows are already excluded by `_relevant_boundary_rows_statement`'s own WHERE
+        # filter above -- every row reaching this loop is either `active=True` or `active IS NULL`.
         if row.active is None:
             ambiguous_names.append(row.name)
             continue
-        if not row.active:
-            continue  # explicitly cleared -- never blocks, regardless of its date-set content
         if not row.quarantined_dates_json:
             ambiguous_names.append(row.name)  # active but no date-set content at all
             continue
diff --git a/apps/backend/tests/test_j11_preboot_guard.py b/apps/backend/tests/test_j11_preboot_guard.py
index c6e691bb..e3573f23 100644
--- a/apps/backend/tests/test_j11_preboot_guard.py
+++ b/apps/backend/tests/test_j11_preboot_guard.py
@@ -5,7 +5,19 @@ monkeypatch `warmup_mod.run_scan` to a recording stub (the SAME pattern `test_wa
 `run_scan`-failure test already uses: `monkeypatch.setattr(warmup_mod, "run_scan", _boom)`) rather than
 exercising the real scanner engine -- this file tests the GUARD's wiring, not the scanner's own
 correctness (covered elsewhere, and doing so here would need the heavy seeded-DB fixtures `test_warmup.py`
-already pays for once)."""
+already pays for once).
+
+goal-market-compass iter-17 additions (below, `test_iter17_*` naming -- deliberately a NEW numbering
+space, never reusing this file's existing `tc23`-`tc30` labels, which key to iter-16's OWN internal
+numbering; reusing "tc4"/"tc5" etc. against two different meanings in the same file would be a
+readability trap): the owner's 9 lettered test cases (A)-(I) from "OWNER RULING -- J-11
+maintenance-boundary lifecycle AUTHORIZED" (docs/goal.md J-11 step 11), mapped to THIS iteration's own
+phase-spec TC-1 through TC-5 (TC-6 through TC-10, cases D/H/I, live in
+`test_j11_preboot_guard_cli_scripts.py` -- they need the new arm/disarm scripts). Cases (A)/(C)/(G) are
+already covered by the iter-16 tests above (`test_tc25_no_boundary_registered_is_a_true_noop` /
+`test_active_boundary_does_not_block_a_date_outside_its_own_set` /
+`test_tc23_ensure_latest_snapshot_skips_write_and_returns_none_when_blocked` + siblings) and are
+deliberately NOT duplicated here."""
 from __future__ import annotations
 
 import json
@@ -315,3 +327,185 @@ def test_tc30_create_db_and_tables_creates_maintenance_boundaries_idempotently(t
         rows = session.exec(select(MaintenanceBoundary)).all()
     assert len(rows) == 1
     assert rows[0].name == "b"
+
+
+# ==========================================================================================================
+# goal-market-compass iter-17 -- AG-8 fix + owner cases (B)/(E)/(F) + the table-absent regression.
+# ==========================================================================================================
+
+NON_INCIDENT_DATE = date(2026, 7, 23)  # phase spec TC-3's own example: "a surviving, non-incident date"
+
+
+# --- TC-2/TC-3 (owner case B + the already-covered case C, re-exercised against the REAL J-11 boundary) --
+
+
+def test_iter17_tc2_tc3_all_eleven_incident_dates_blocked_and_one_non_incident_date_is_not(engine):
+    """Owner case (B): "once armed, all 11 incident dates are blocked" -- the iter-16 coverage only
+    looped a single arbitrary date; this loops every one of `jm.INCIDENT_DATES` individually, armed via
+    the REAL `register_j11_incident_boundary` (not an arbitrary single-date boundary), and also serves as
+    a regression guard that the AG-8 bounded-query rewrite changed no observable behavior. TC-3's
+    surviving non-incident date is asserted in the SAME armed state."""
+    with Session(engine) as session:
+        guard.register_j11_incident_boundary(session, active=True)
+
+    with Session(engine) as session:
+        for one_date in jm.INCIDENT_DATES:
+            result = guard.evaluate_boundary_for_date(session, one_date)
+            assert result["blocked"] is True, f"{one_date} should be blocked"
+            assert result["boundary_name"] == guard.J11_INCIDENT_BOUNDARY_NAME
+            assert result["ambiguous"] is False
+
+        non_incident_result = guard.evaluate_boundary_for_date(session, NON_INCIDENT_DATE)
+    assert non_incident_result["blocked"] is False
+
+
+# --- TC-4 (owner case E, part 1): SQL NULL `active` -- reachable ONLY via a schema that permits it --------
+
+
+def _engine_with_nullable_active_column():
+    """`MaintenanceBoundary.active` is declared as a plain (non-Optional) `bool`, which SQLModel maps to a
+    DB-level `NOT NULL` column -- verified directly: a raw parameterized `INSERT ... VALUES (NULL)` against
+    a table created by `SQLModel.metadata.create_all` raises `sqlite3.IntegrityError: NOT NULL constraint
+    failed`, so TC-4's scenario is NOT reachable through the model layer at all on today's schema (the
+    plan's own "confirm this before assuming the scenario is even reachable" instruction, confirmed
+    negative). A NULL nonetheless models a real class of future risk this guard must survive -- e.g. an
+    ADDITIVE `ALTER TABLE ... ADD COLUMN` on an existing table (this project's OWN documented migration
+    convention, `.claude/project-template.md` "Schema evolves via additive ALTER TABLE... add-column
+    only") leaves existing rows NULL for any new required column unless a server default is given, or a
+    row written by a future/older schema variant. The fixture constructs that STATE directly: a hand-rolled
+    `CREATE TABLE maintenance_boundaries` matching the real DDL exactly except `active` carries no `NOT
+    NULL`, created BEFORE `SQLModel.metadata.create_all` (which has `checkfirst=True` by default and will
+    skip a table that already exists), so every OTHER table still gets the normal, fully-constrained
+    schema."""
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+    with eng.begin() as conn:
+        conn.exec_driver_sql(
+            """
+            CREATE TABLE maintenance_boundaries (
+                id INTEGER NOT NULL,
+                name VARCHAR NOT NULL,
+                quarantined_dates_json VARCHAR NOT NULL,
+                active BOOLEAN,
+                reason VARCHAR NOT NULL,
+                created_at DATETIME NOT NULL,
+                updated_at DATETIME NOT NULL,
+                PRIMARY KEY (id)
+            )
+            """
+        )
+        conn.exec_driver_sql(
+            "CREATE UNIQUE INDEX ix_maintenance_boundaries_name ON maintenance_boundaries (name)"
+        )
+    SQLModel.metadata.create_all(eng)  # skips maintenance_boundaries (already exists); creates everything else
+    return eng
+
+
+def test_null_active_row_is_not_constructible_through_the_normal_schema():
+    """Documents the negative finding the fixture helper's docstring above claims -- a normal
+    `SQLModel.metadata.create_all` schema genuinely rejects a NULL `active` value, so TC-4 below is
+    deliberately exercised against a DIFFERENT, hand-rolled schema, never silently against the real one."""
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+    SQLModel.metadata.create_all(eng)
+    with Session(eng) as session:
+        with pytest.raises(Exception):
+            _raw_insert_boundary(session, name="x", dates_json="[]", active_int=None, reason="r")
+
+
+def test_iter17_tc4_null_active_row_blocks_and_is_flagged_ambiguous():
+    eng = _engine_with_nullable_active_column()
+    with Session(eng) as session:
+        _raw_insert_boundary(
+            session, name="null-active-boundary", dates_json=json.dumps([TEST_DATE.isoformat()]),
+            active_int=None, reason="r",
+        )
+    with Session(eng) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["ambiguous"] is True
+    assert result["boundary_name"] == "null-active-boundary"
+
+    # the row is NOT silently excluded for a date OUTSIDE its own (unreadable) date-set either -- an
+    # ambiguous row's unreadable active flag makes EVERY date unprovable, not just the ones its date-set
+    # happens to name.
+    with Session(eng) as session:
+        other_result = guard.evaluate_boundary_for_date(session, OTHER_DATE)
+    assert other_result["blocked"] is True
+    assert other_result["ambiguous"] is True
+
+
+# --- TC-5 (owner cases E/F): many irrelevant rows + the query itself is bounded, not just the boolean -----
+
+
+def test_iter17_tc5_many_irrelevant_rows_plus_one_real_match_stays_correct_and_bounded(engine):
+    with Session(engine) as session:
+        for i in range(25):
+            guard.register_boundary(
+                session, name=f"cleared-{i}", dates=[TEST_DATE], reason="r", active=False,
+            )
+        for i in range(25):
+            guard.register_boundary(
+                session, name=f"unrelated-active-{i}", dates=[date(2030, 1, 1)], reason="r", active=True,
+            )
+        guard.register_boundary(session, name="the-real-one", dates=[TEST_DATE], reason="incident quarantine")
+
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["boundary_name"] == "the-real-one"
+    assert result["ambiguous"] is False
+
+    # the resulting BOOLEAN alone is not sufficient evidence the query is bounded (TC-5's own wording) --
+    # inspect the compiled SQL of the actual statement-builder the guard runs, independent of any fixture
+    # data, and assert it carries a LIMIT clause.
+    compiled_sql = str(
+        guard._relevant_boundary_rows_statement().compile(compile_kwargs={"literal_binds": True})
+    )
+    assert "LIMIT" in compiled_sql.upper()
+    assert str(guard._MAX_RELEVANT_BOUNDARY_ROWS + 1) in compiled_sql
+
+
+def test_iter17_bound_exceeded_fails_closed(engine):
+    """The overflow branch itself -- more active/ambiguous rows exist than the deterministic bound allows
+    -- must fail CLOSED (blocked, ambiguous), never silently truncate away a row that might have matched."""
+    with Session(engine) as session:
+        for i in range(guard._MAX_RELEVANT_BOUNDARY_ROWS + 5):
+            guard.register_boundary(
+                session, name=f"filler-{i}", dates=[date(2030, 1, 1)], reason="r", active=True,
+            )
+
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["ambiguous"] is True
+
+
+def test_iter17_two_different_active_boundaries_covering_the_same_date_still_blocks(engine):
+    """Owner requirement 2 / case (E): "unexpectedly duplicated ... active-boundary state must fail
+    CLOSED. Ambiguous maintenance state is never silently treated as 'not blocked'." Two DIFFERENTLY
+    NAMED boundaries (the `name` column is unique, so a literal duplicate row is impossible) both
+    independently covering the SAME date is exactly this shape -- the date must stay blocked regardless
+    of which of the two rows the loop happens to name."""
+    with Session(engine) as session:
+        guard.register_boundary(session, name="overlap-a", dates=[TEST_DATE], reason="first")
+        guard.register_boundary(session, name="overlap-b", dates=[TEST_DATE], reason="second")
+
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["boundary_name"] in ("overlap-a", "overlap-b")
+
+
+# --- Known crux #2: table-absent (not merely table-empty) must clean-no-op, never raise -------------------
+
+
+def test_iter17_table_absent_evaluates_cleanly_as_unblocked():
+    """`select(MaintenanceBoundary)` against a database where `maintenance_boundaries` was never created
+    at all raises `sqlalchemy.exc.OperationalError` ("no such table"), not an empty list. Every OTHER test
+    in this file runs against a fixture DB where `SQLModel.metadata.create_all` already ran (the `engine`
+    fixture), so none of them exercise this. This is the live-database shape TC-11 depends on: the real
+    `apps/backend/data/trendora.db` currently has ZERO tables named `maintenance_boundaries`."""
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+    # Deliberately NO create_all() call at all -- not even the OTHER tables exist on this engine.
+    with Session(eng) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result == {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
diff --git a/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py b/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py
new file mode 100644
index 00000000..10873494
--- /dev/null
+++ b/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py
@@ -0,0 +1,162 @@
+"""goal-market-compass iter-17 -- TC-11/TC-12: strictly READ-ONLY live verification of the AG-8-fixed
+`evaluate_boundary_for_date` against the real `apps/backend/data/trendora.db`, plus the zero-live-writes
+proof (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED",
+implementation requirement 7: "verify through the same production guard entry point using a non-writing
+diagnostic/test harness").
+
+This script performs ZERO writes of any kind. It opens the live database through an ACTUAL read-only
+SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom
+`run_j11_iter16_stage_d_readiness.py` already established -- copied here unchanged, never imported cross-
+script since no shared utility module holds it today), calls the REAL, unmodified
+`app.engine.j11_preboot_guard.evaluate_boundary_for_date` for 2026-08-12, and independently confirms via a
+companion `sqlite_master` query that `maintenance_boundaries` does not exist. The database file's mtime +
+size + `-wal` sidecar size are fingerprinted at the TRUE start and TRUE end of the process (iteration-12's
+lesson: this bracket, not a narrow internal one, is the proof that matters) and written to their own
+before/after evidence files, mirroring `run_j11_stage_c_bounded_clear.py`'s / `run_j11_iter16_stage_d_
+readiness.py`'s established naming.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py \\
+        --evidence-dir runs/goal-market-compass-iter-17
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from datetime import date, datetime, timezone
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import create_engine, event, text  # noqa: E402
+from sqlmodel import Session  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import resolve_database_url  # noqa: E402
+from app.engine import j11_preboot_guard as guard  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+
+TARGET_DATE = date(2026, 8, 12)
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    path = Path(raw)
+    return path if path.is_absolute() else (REPO_ROOT / raw)
+
+
+def _read_only_engine(db_path: Path):
+    """Mirrors `run_j11_iter16_stage_d_readiness.py`'s own helper of the same name, unchanged."""
+    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
+    engine = create_engine(url, connect_args={"check_same_thread": False})
+
+    @event.listens_for(engine, "connect")
+    def _set_query_only(dbapi_connection, _record):
+        dbapi_connection.execute("PRAGMA query_only=ON")
+
+    return engine
+
+
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
+    )
+    args = parser.parse_args()
+
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. No config has been loaded, no database "
+            "engine has been constructed, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    evidence_dir: Path = args.evidence_dir
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    if db_path is None or not db_path.exists():
+        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
+        return 1
+    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)
+
+    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it -----
+    db_file_true_start = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-iter17-readiness-db-file-true-start.json", db_file_true_start)
+
+    engine = _read_only_engine(db_path)
+
+    with Session(engine) as session:
+        table_count = session.exec(
+            text(
+                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='maintenance_boundaries'"
+            )
+        ).one()[0]
+        guard_result = guard.evaluate_boundary_for_date(session, TARGET_DATE)
+
+    # --- TRUE process end: captured LAST, after every read above -------------------------------------
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-iter17-readiness-db-file-true-end.json", db_file_true_end)
+
+    zero_write_proof = {
+        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
+        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
+        "wal_unchanged": db_file_true_start.get("wal") == db_file_true_end.get("wal"),
+    }
+
+    verification = {
+        "generated_at": datetime.now(timezone.utc).isoformat(),
+        "target_date": TARGET_DATE.isoformat(),
+        "db_path": str(db_path),
+        "maintenance_boundaries_table_count": int(table_count),
+        "guard_result": guard_result,
+        "expected": {"maintenance_boundaries_table_count": 0, "guard_result_blocked": False},
+        "matches_expected": (
+            int(table_count) == 0 and guard_result.get("blocked") is False
+        ),
+        "db_file_true_start": db_file_true_start,
+        "db_file_true_end": db_file_true_end,
+        "zero_write_proof": zero_write_proof,
+        "recipe": (
+            "apps/backend/.venv/bin/python "
+            "apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py "
+            f"--evidence-dir {evidence_dir}"
+        ),
+    }
+    _write_json(evidence_dir / "j11-iter17-live-preboot-guard-verification.json", verification)
+
+    print(
+        f"maintenance_boundaries_table_count={table_count} guard_result={guard_result} "
+        f"matches_expected={verification['matches_expected']}",
+        file=sys.stderr,
+    )
+    print(
+        f"zero-write proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
+        f"size_unchanged={zero_write_proof['size_unchanged']} wal_unchanged={zero_write_proof['wal_unchanged']}",
+        file=sys.stderr,
+    )
+    print("J-11 MAINTENANCE BOUNDARY: NOT ACTIVE", file=sys.stderr)
+    print("J-11 LIVE PRE-BOOT GUARD: NOT ARMED", file=sys.stderr)
+    return 0 if verification["matches_expected"] and all(zero_write_proof.values()) else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py b/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py
new file mode 100644
index 00000000..794f525f
--- /dev/null
+++ b/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py
@@ -0,0 +1,377 @@
+"""goal-market-compass iter-17 -- J-11 Stage D readiness rider: re-run the AVB decision-impact trace WITH
+`volume_override` (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle
+AUTHORIZED" section's own rider instruction).
+
+Iteration 16 established the corrected `daily_prices` raw-input baseline (the AVB two-cell volume
+correction) and re-ran the readiness classification, but its OWN decision-impact trace call passed NO
+`volume_override` to `trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` (Goal 8's own
+instruction at the time: "representation A reads the corrected stored rows directly"). That left
+representation B pairing a COUNTERFACTUAL close (`stored_bridged_close / bridge_factor`, undoing the
+bridge on price only) with the ALREADY-CORRECTED stored volume (calibrated to compensate for the BRIDGED
+close, not the un-bridged one) -- an inconsistent hybrid whose single-bar dollar-volume ratio (A / B) lands
+EXACTLY on `bridge_factor` by construction (verified algebraically and empirically below), not because of
+any genuine material effect. That mechanical artifact is what produced classification `AVB-B` instead of
+the honest `AVB-A`.
+
+This rider supplies `volume_override` -- built from iteration-15's ALREADY-COMMITTED, already-fetched
+`j11-avb-provider-fetch-evidence.json` (`{iso_date: {"close": ..., "volume": ...}}` for the two
+RECOVERED_DATES) -- to BOTH decision-impact trace calls, unchanged function signatures, no new engine
+logic (`volume_override` has been an accepted optional parameter on both functions since iteration 15;
+iteration 16 simply never passed it). With the override, representation B pairs the SAME counterfactual
+close with the RAW fetched provider volume -- both genuinely on the un-bridged basis -- so its dollar
+volume should land near representation A's (within the calibration window's own relative tolerance), not
+on `bridge_factor`.
+
+Reused, UNCHANGED: `j11_stage_d.capture_stage_d_preflight` / `compare_stage_d_preflight_to_certified` /
+`stage_d_preflight_verdict` / `produce_stage_d_readiness_artifact`; `j11_avb_diagnostic.
+fetch_avb_stored_series` / `classify_local_convention_with_volume_evidence` /
+`trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` / `classify_avb` /
+`load_j10_avb_evidence` / `summarize_pool_bridge_factor_distribution`. This script does NOT re-run
+`run_j11_avb_correction.py` (already spent, one-time -- AG-9's dated exception #2 is exhausted) and does
+NOT edit iteration 16's `j11-stage-d-certified-baseline.json` or `j11-stage-d-readiness.json` -- both are
+loaded read-only as this iteration's certified baseline (nothing in `daily_prices` has changed since
+iteration 16 minted them, so no NEW baseline needs building; only Goal 5's own supersession is reused).
+
+Zero writes: opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` +
+`PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom `run_j11_iter16_stage_d_readiness.py` /
+`run_j11_iter17_live_preboot_guard_verification.py` already established).
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter17_stage_d_readiness.py \\
+        --evidence-dir runs/goal-market-compass-iter-17
+"""
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import sys
+from datetime import date
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import create_engine, event  # noqa: E402
+from sqlmodel import Session  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import resolve_database_url  # noqa: E402
+from app.engine import j11_avb_correction as corr  # noqa: E402
+from app.engine import j11_avb_diagnostic as diag  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.engine import j11_stage_d as jsd  # noqa: E402
+
+DEFAULT_ITERATION_16_CERTIFIED_BASELINE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
+)
+DEFAULT_ITERATION_16_READINESS_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-readiness.json"
+)
+DEFAULT_ITERATION_14_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
+)
+PERMITTED_DATES = diag.CALIBRATION_DATES + diag.RECOVERED_DATES
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    path = Path(raw)
+    return path if path.is_absolute() else (REPO_ROOT / raw)
+
+
+def _read_only_engine(db_path: Path):
+    """Mirrors `run_j11_iter16_stage_d_readiness.py`'s own helper of the same name, unchanged."""
+    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
+    engine = create_engine(url, connect_args={"check_same_thread": False})
+
+    @event.listens_for(engine, "connect")
+    def _set_query_only(dbapi_connection, _record):
+        dbapi_connection.execute("PRAGMA query_only=ON")
+
+    return engine
+
+
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
+    )
+    parser.add_argument(
+        "--iteration-16-certified-baseline-path", type=Path, default=DEFAULT_ITERATION_16_CERTIFIED_BASELINE_PATH,
+        help="iteration 16's own already-built certified baseline -- loaded READ-ONLY, never rebuilt "
+             "(nothing in daily_prices changed since iteration 16 minted it).",
+    )
+    parser.add_argument("--iteration-16-readiness-path", type=Path, default=DEFAULT_ITERATION_16_READINESS_PATH)
+    parser.add_argument("--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH)
+    parser.add_argument("--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH)
+    parser.add_argument("--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH)
+    args = parser.parse_args()
+
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. No config has been loaded, no database "
+            "engine has been constructed, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    # --- byte-unedited proof for iteration 16's own artifact, hashed BEFORE anything else runs -----------
+    iter16_readiness_hash_before = hashlib.sha256(args.iteration_16_readiness_path.read_bytes()).hexdigest()
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    if db_path is None or not db_path.exists():
+        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
+        return 1
+    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)
+
+    db_file_before = jsc.db_file_fingerprint(db_path)
+
+    goal_md_text = jsc.read_goal_md_text()
+    git_head = jsc.read_git_head()
+    engine = _read_only_engine(db_path)
+
+    prior_identity_value = None
+    if args.iteration_14_identity_path is not None and Path(args.iteration_14_identity_path).exists():
+        prior_identity_value = json.loads(Path(args.iteration_14_identity_path).read_text()).get("engine_identity")
+
+    # --- Step 1: fresh Stage D preflight against the (still-)corrected live database ---------------------
+    with Session(engine) as session:
+        preflight = jsd.capture_stage_d_preflight(
+            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
+            prior_iteration_14_identity=prior_identity_value,
+        )
+    _write_json(args.evidence_dir / "j11-stage-d-preflight.json", preflight)
+    fresh_daily_prices_fingerprint = preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"]
+    print(
+        f"fresh preflight captured: manifest_row_count={preflight['manifest_row_count']} "
+        f"daily_prices_fingerprint={fresh_daily_prices_fingerprint} "
+        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']} "
+        f"identity_check_a_ok={preflight['identity_check_a']['ok']}",
+        file=sys.stderr,
+    )
+
+    # --- Step 2: gate against iteration 16's OWN certified baseline -- expect a CLEAN match this time -----
+    # (unlike iteration 16 vs 15, which expected an honest mismatch because the correction itself moved
+    # the fingerprint that iteration -- nothing has mutated daily_prices since iteration 16 landed it).
+    certified = json.loads(args.iteration_16_certified_baseline_path.read_text())
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    verdict = jsd.stage_d_preflight_verdict(gate)
+    _write_json(args.evidence_dir / "j11-stage-d-preflight-gate.json", {"comparison": gate, "verdict": verdict})
+    print(
+        f"gate vs iteration-16 certified baseline: all_invariants_hold={gate['all_invariants_hold']} "
+        f"daily_prices_fingerprint_unchanged={gate['checks']['daily_prices_fingerprint_unchanged']} "
+        "(EXPECTED True -- no daily_prices mutation has occurred since iteration 16)",
+        file=sys.stderr,
+    )
+    if not gate["all_invariants_hold"]:
+        failing = [k for k, v in gate["checks"].items() if not v]
+        print(
+            f"UNEXPECTED: failing checks against iteration 16's certified baseline: {failing} -- something "
+            "changed the raw/manifest state since iteration 16 landed its correction. STOPPING rather than "
+            "silently proceeding to classify against a baseline that no longer matches live state.",
+            file=sys.stderr,
+        )
+        return 1
+
+    # --- Step 3: re-run the AVB bridge diagnostic WITH volume_override on BOTH decision-impact traces -----
+    fetch_evidence = json.loads(Path(args.provider_fetch_evidence_path).read_text())
+    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
+    evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
+    bridge_factor = evidence_row["bridge_factor"]
+    pool_distribution = diag.summarize_pool_bridge_factor_distribution(args.j10_evidence_path)
+
+    # The volume_override map this rider exists to supply: RAW fetched provider volume (iteration-15
+    # evidence) for exactly the RECOVERED_DATES -- never a re-derivation, never the corrected stored value.
+    volume_override: dict = {}
+    for one_date in diag.RECOVERED_DATES:
+        key = one_date.isoformat()
+        entry = provider_evidence_by_date.get(key)
+        if entry is not None and entry.get("volume") is not None:
+            volume_override[one_date] = entry["volume"]
+    print(
+        f"volume_override built from {args.provider_fetch_evidence_path} for "
+        f"{sorted(d.isoformat() for d in volume_override)}: "
+        f"{ {d.isoformat(): v for d, v in volume_override.items()} }",
+        file=sys.stderr,
+    )
+    if set(volume_override) != set(diag.RECOVERED_DATES):
+        print(
+            "FAIL: volume_override does not cover both RECOVERED_DATES -- iteration-15's provider-fetch "
+            "evidence is missing volume for at least one of them. Refusing to classify on incomplete "
+            "override evidence.",
+            file=sys.stderr,
+        )
+        return 1
+
+    with Session(engine) as session:
+        stored_series = diag.fetch_avb_stored_series(session, date(2026, 6, 1), date(2026, 12, 31))
+        local_convention = diag.classify_local_convention_with_volume_evidence(
+            stored_series, evidence_row, provider_evidence_by_date
+        )
+
+        stored_rows_by_date = {row["date"]: row for row in stored_series}
+        representations_by_date = {}
+        for one_date in PERMITTED_DATES:
+            key = one_date.isoformat()
+            stored_row = stored_rows_by_date.get(key)
+            if stored_row is None:
+                continue
+            representations_by_date[key] = diag.compute_counterfactual_representations(
+                bridge_factor, stored_row["close"], stored_row["volume"],
+                provider_evidence=provider_evidence_by_date.get(key),
+            )
+
+        # THE rider's own change: volume_override IS threaded through this time, to BOTH calls.
+        decision_impact_by_date: dict[str, dict] = {}
+        single_bar_ab_ratio_by_date: dict[str, dict] = {}
+        for one_date in diag.RECOVERED_DATES:
+            key = one_date.isoformat()
+            print(f"tracing decision impact for {key} (WITH volume_override this time) ...", file=sys.stderr)
+            ur_impact = diag.trace_universe_resolver_impact(
+                session, cfg, one_date, bridge_factor, volume_override=volume_override
+            )
+            scoring_impact = diag.trace_scoring_and_selection_impact(
+                session, cfg, one_date, bridge_factor, volume_override=volume_override
+            )
+            decision_impact_by_date[key] = {"universe_resolver": ur_impact, "scoring_and_selection": scoring_impact}
+            print(
+                f"  {key}: admission_changed={ur_impact['admission_changed']} "
+                f"avb_resolved_member={scoring_impact.get('avb_resolved_member')} "
+                f"risk_bucket_a={scoring_impact.get('risk_bucket_a')} risk_bucket_b={scoring_impact.get('risk_bucket_b')} "
+                f"eligible_a={scoring_impact.get('eligible_a')} eligible_b={scoring_impact.get('eligible_b')}",
+                file=sys.stderr,
+            )
+
+            # --- TC-13's own explicit check: the SINGLE-BAR A/B dollar-volume ratio for the target date --
+            # (a script-level composition of already-existing values, no new engine logic): representation
+            # A is the stored bar as-is (post iter-16 correction); representation B is the SAME
+            # close/bridge_factor transform `_build_bars_with_transformed_close` applies internally, paired
+            # with the override volume -- reproduced here explicitly so the ratio is a directly inspectable,
+            # persisted number rather than buried inside the window-averaged ADV fields above.
+            stored_row = stored_rows_by_date[key]
+            close_a, volume_a = stored_row["close"], stored_row["volume"]
+            close_b = close_a / bridge_factor
+            volume_b = volume_override[one_date]
+            dollar_a = close_a * volume_a
+            dollar_b = close_b * volume_b
+            ratio_a_over_b = dollar_a / dollar_b if dollar_b else None
+            single_bar_ab_ratio_by_date[key] = {
+                "close_a": close_a, "volume_a": volume_a, "dollar_a": dollar_a,
+                "close_b": close_b, "volume_b_override_applied": volume_b, "dollar_b": dollar_b,
+                "ratio_a_over_b": ratio_a_over_b,
+                "within_relative_tolerance_of_one": diag._within_relative_tolerance(ratio_a_over_b, 1.0),
+                "landed_on_bridge_factor": diag._within_relative_tolerance(ratio_a_over_b, bridge_factor),
+                "tolerance": diag._RATIO_RELATIVE_TOLERANCE,
+                "note": (
+                    "iteration 16 (no volume_override) paired counterfactual close_b=close_a/bridge_factor "
+                    "with the UNCHANGED stored (already-corrected/compensating) volume, so this exact ratio "
+                    "landed EXACTLY on bridge_factor by construction. With volume_override applying the RAW "
+                    "fetched provider volume to volume_b instead, this ratio should land near 1.0 within "
+                    "the calibration window's own relative tolerance -- both A and B now express genuinely "
+                    "independent, self-consistent (price, volume) pairs."
+                ),
+            }
+
+    classification = diag.classify_avb(local_convention, decision_impact_by_date)
+    if not fetch_evidence.get("sufficient_evidence", False):
+        classification = dict(classification)
+        classification["classification"] = "AVB-D"
+        classification["stage_d_ready_per_avb"] = False
+        classification["reasoning"] = (
+            "iteration-15's AG-9 dated-exception-#2 fetch did NOT supply sufficient evidence for all six "
+            "permitted dates; classifying AVB-D per the amendment's own fail-closed rule."
+        )
+
+    avb_diagnostic_result = {
+        "generated_at": diag._now_iso(),
+        "j10_evidence_path": str(args.j10_evidence_path),
+        "provider_fetch_evidence_path": str(args.provider_fetch_evidence_path),
+        "provider_fetch_evidence_sufficient": fetch_evidence.get("sufficient_evidence"),
+        "bridge_factor": bridge_factor,
+        "calibration_pairs": evidence_row.get("pairs"),
+        "pool_bridge_factor_distribution": pool_distribution,
+        "stored_series_window": {"start": "2026-06-01", "end": "2026-12-31", "row_count": len(stored_series)},
+        "local_convention": local_convention,
+        "counterfactual_representations_by_date": representations_by_date,
+        "decision_impact_by_date": decision_impact_by_date,
+        "volume_override_by_date": {d.isoformat(): v for d, v in volume_override.items()},
+        "single_bar_ab_dollar_volume_ratio_by_date": single_bar_ab_ratio_by_date,
+        "classification": classification,
+        "note": (
+            "goal-market-compass iter-17 rider: re-runs iteration 16's decision-impact trace WITH "
+            "volume_override supplied to both trace_universe_resolver_impact and "
+            "trace_scoring_and_selection_impact (both have accepted this optional parameter unchanged "
+            "since iteration 15; iteration 16 simply never passed it). Cite runs/goal-market-compass-"
+            "iter-16/j11-avb-bridge-diagnostic.json as historically accurate for the NO-volume_override "
+            "state -- never edited, never deleted."
+        ),
+    }
+    _write_json(args.evidence_dir / "j11-avb-bridge-diagnostic.json", avb_diagnostic_result)
+    print(
+        f"AVB classification (WITH volume_override): {classification['classification']} "
+        f"stage_d_ready_per_avb={classification['stage_d_ready_per_avb']}",
+        file=sys.stderr,
+    )
+    for key, r in single_bar_ab_ratio_by_date.items():
+        print(
+            f"  single-bar A/B dollar-volume ratio {key}: {r['ratio_a_over_b']} "
+            f"within_tolerance_of_1={r['within_relative_tolerance_of_one']} "
+            f"landed_on_bridge_factor={r['landed_on_bridge_factor']} (bridge_factor={bridge_factor})",
+            file=sys.stderr,
+        )
+
+    # --- Step 4: combine into the final readiness verdict (reused unchanged) ------------------------------
+    readiness = jsd.produce_stage_d_readiness_artifact(
+        args.evidence_dir / "j11-stage-d-preflight-gate.json",
+        args.evidence_dir / "j11-avb-bridge-diagnostic.json",
+        output_path=args.evidence_dir / "j11-iter17-stage-d-readiness.json",
+    )
+
+    db_file_after = jsc.db_file_fingerprint(db_path)
+    zero_write_proof = {
+        "db_file_before": db_file_before,
+        "db_file_after": db_file_after,
+        "mtime_unchanged": db_file_before.get("mtime") == db_file_after.get("mtime"),
+        "size_unchanged": db_file_before.get("size_bytes") == db_file_after.get("size_bytes"),
+        "wal_unchanged": db_file_before.get("wal") == db_file_after.get("wal"),
+    }
+    _write_json(args.evidence_dir / "j11-iter17-stage-d-readiness-zero-write-proof.json", zero_write_proof)
+    print(
+        f"this-script zero-write proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
+        f"size_unchanged={zero_write_proof['size_unchanged']} wal_unchanged={zero_write_proof['wal_unchanged']}",
+        file=sys.stderr,
+    )
+
+    iter16_readiness_hash_after = hashlib.sha256(args.iteration_16_readiness_path.read_bytes()).hexdigest()
+    print(
+        f"iteration-16 j11-stage-d-readiness.json hash unchanged: "
+        f"{iter16_readiness_hash_before == iter16_readiness_hash_after} "
+        f"(before={iter16_readiness_hash_before}, after={iter16_readiness_hash_after})",
+        file=sys.stderr,
+    )
+
+    print(f"avb_classification={readiness['avb_classification']} preflight_gate_passed={readiness['preflight_gate_passed']}", file=sys.stderr)
+    print(f"J-11 STAGE D READY: {'YES' if readiness['ready'] else 'NO'}", file=sys.stderr)
+    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
+    return 0 if readiness["ready"] and iter16_readiness_hash_before == iter16_readiness_hash_after else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_maintenance_boundary_arm.py b/apps/backend/scripts/run_j11_maintenance_boundary_arm.py
new file mode 100644
index 00000000..d2e7e11c
--- /dev/null
+++ b/apps/backend/scripts/run_j11_maintenance_boundary_arm.py
@@ -0,0 +1,144 @@
+"""goal-market-compass iter-17 -- J-11 maintenance-boundary lifecycle: the ARM entrypoint (docs/goal.md
+J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED", implementation
+requirement 4: "Provide an explicit arm path... a committed, production-capable path for
+registering/activating the J-11 boundary... It must not live only inside a test fixture or a one-off
+Python snippet.").
+
+Thin CLI wrapper around the ALREADY-EXISTING, unchanged `app.engine.j11_preboot_guard.
+register_j11_incident_boundary` -- this script introduces NO new registration logic. It:
+  - sources its date-set EXCLUSIVELY from `app.engine.j11_maintenance.INCIDENT_DATES` (never re-typed --
+    the exact trap the owner's dispatch note names) via that reused function, and additionally
+    cross-checks the code constant against docs/goal.md's own two 11-date lists (the existing
+    `app.engine.j11_stage_c.check_c1_date_set_boundary`, reused unchanged) BEFORE writing anything --
+    satisfies requirement 4's "must validate the exact incident-date set";
+  - is idempotent (a second identical invocation against the same database is a safe no-op on content --
+    `register_boundary` upserts by unique `name`, never inserting a duplicate row -- TC-7);
+  - writes ONLY to `maintenance_boundaries` (the reused, unchanged `register_j11_incident_boundary` /
+    `register_boundary` touch no other table -- TC-8);
+  - makes its mutation obvious: prints the boundary row before and after;
+  - REFUSES (no database write of any kind) if the target table does not already exist -- creating
+    `maintenance_boundaries` is a SEPARATE, NOT-yet-authorized decision (docs/goal.md's own "BLOCKER ON
+    RECORD" paragraph: "do not create it and do not migrate to it"). This script never calls
+    `create_db_and_tables`/`metadata.create_all`.
+
+Mirrors `run_j11_stage_c_bounded_clear.py`'s established idiom: an explicit `--confirm` gate (no database
+interaction of any kind without it, not even a read), and an explicit REQUIRED `--database-url` with NO
+default pointing at the real configured database (goal-market-compass iter-14's lesson, generalized: a
+silently-defaulted path/target argument is how committed evidence/state gets overwritten or touched by
+accident) -- so this script can NEVER reach `apps/backend/data/trendora.db` unless that exact URL is typed
+out by a caller who means it. **This iteration never invokes it against that file** -- fixture/temp-DB
+invocation only, from tests.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_maintenance_boundary_arm.py \\
+        --confirm \\
+        --database-url sqlite:////absolute/path/to/some-disposable.db
+"""
+from __future__ import annotations
+
+import argparse
+import sys
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import inspect as sa_inspect  # noqa: E402
+from sqlmodel import Session, select  # noqa: E402
+
+from app.db import make_engine  # noqa: E402
+from app.engine import j11_preboot_guard as guard  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.models import MaintenanceBoundary  # noqa: E402
+
+
+def _print_boundary_row(session: Session, label: str) -> None:
+    row = session.exec(
+        select(MaintenanceBoundary).where(MaintenanceBoundary.name == guard.J11_INCIDENT_BOUNDARY_NAME)
+    ).first()
+    if row is None:
+        print(f"{label}: no {guard.J11_INCIDENT_BOUNDARY_NAME!r} row exists", file=sys.stderr)
+    else:
+        print(
+            f"{label}: id={row.id} name={row.name!r} active={row.active} "
+            f"quarantined_dates_json={row.quarantined_dates_json} updated_at={row.updated_at}",
+            file=sys.stderr,
+        )
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--database-url", type=str, default=None,
+        help=(
+            "required -- no default on purpose. This iteration is NEVER authorized to invoke this script "
+            "against the real configured database (docs/goal.md J-11 step 11's 'BLOCKER ON RECORD' -- the "
+            "live maintenance_boundaries table does not exist and creating it is NOT authorized). Point "
+            "this at a disposable fixture/temp database only."
+        ),
+    )
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches no database at all and exits non-zero.",
+    )
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm. No database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    if args.database_url is None:
+        print(
+            "refusing to run without an explicit --database-url. There is no default -- this script must "
+            "never be able to reach the real configured database by omission. No database interaction, "
+            "not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    goal_md_text = jsc.read_goal_md_text()
+    date_set_check = jsc.check_c1_date_set_boundary(goal_md_text)
+    if not date_set_check["ok"]:
+        print(
+            "refusing to arm: the code's j11_maintenance.INCIDENT_DATES disagrees with docs/goal.md's own "
+            f"11-date lists ({date_set_check}) -- arming would risk quarantining the wrong date set. No "
+            "database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 1
+
+    engine = make_engine(args.database_url)
+    if not sa_inspect(engine).has_table(MaintenanceBoundary.__tablename__):
+        print(
+            f"STALLED: the {MaintenanceBoundary.__tablename__!r} table does not exist in "
+            f"{args.database_url!r}. Creating it is a SEPARATE, NOT-yet-authorized decision (docs/goal.md "
+            "J-11 step 11's 'BLOCKER ON RECORD' -- 'do not create it and do not migrate to it'). This "
+            "script never calls create_db_and_tables()/metadata.create_all(). No write of any kind has "
+            "occurred.",
+            file=sys.stderr,
+        )
+        return 3
+
+    with Session(engine) as session:
+        _print_boundary_row(session, "BEFORE")
+
+    with Session(engine) as session:
+        row = guard.register_j11_incident_boundary(session, active=True)
+
+    with Session(engine) as session:
+        _print_boundary_row(session, "AFTER")
+
+    print(
+        f"J-11 MAINTENANCE BOUNDARY: ACTIVE (id={row.id}, dates={row.quarantined_dates_json})",
+        file=sys.stderr,
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_maintenance_boundary_disarm.py b/apps/backend/scripts/run_j11_maintenance_boundary_disarm.py
new file mode 100644
index 00000000..29b8f707
--- /dev/null
+++ b/apps/backend/scripts/run_j11_maintenance_boundary_disarm.py
@@ -0,0 +1,137 @@
+"""goal-market-compass iter-17 -- J-11 maintenance-boundary lifecycle: the DISARM entrypoint (docs/goal.md
+J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED", implementation
+requirement 5: "Provide a future disarm/deactivation path. Production-capable, scoped to exactly the J-11
+boundary, must not delete unrelated maintenance history. Do not invoke it now.").
+
+Thin CLI wrapper around the ALREADY-EXISTING, unchanged `app.engine.j11_preboot_guard.clear_boundary` --
+this script introduces NO new deactivation logic. It:
+  - takes the boundary's `name` as an explicit, REQUIRED command-line argument -- NEVER a hardcoded
+    target (never defaults to `guard.J11_INCIDENT_BOUNDARY_NAME` or any other boundary), so a caller must
+    always say exactly which boundary they mean;
+  - is scoped strictly to that one named row: `clear_boundary` looks up by unique `name` and flips only
+    that row's `active` flag to `False` -- every OTHER registered boundary's row is left untouched in
+    every field (TC-9/TC-10);
+  - NEVER deletes a row -- `active=False` only, so the maintenance history stays auditable (the owner's
+    "Lifecycle -- deactivate, do not delete" instruction);
+  - makes its mutation obvious: prints the boundary row before and after;
+  - is a safe no-op (exit 0, nothing written) when the named boundary does not exist, OR when the
+    `maintenance_boundaries` table itself does not exist -- "nothing is armed" is not an error condition
+    for a disarm request.
+
+Mirrors `run_j11_maintenance_boundary_arm.py`'s / `run_j11_stage_c_bounded_clear.py`'s idiom: an explicit
+`--confirm` gate (no database interaction of any kind without it, not even a read), and an explicit
+REQUIRED `--database-url` with NO default pointing at the real configured database. **This iteration never
+invokes it against any live-armed state** -- nothing is live-armed yet (the arm step is itself blocked by
+the live table's absence), so there is nothing for this script to legitimately disarm against
+`apps/backend/data/trendora.db` this iteration; fixture/temp-DB invocation only, from tests.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_maintenance_boundary_disarm.py \\
+        --confirm \\
+        --database-url sqlite:////absolute/path/to/some-disposable.db \\
+        --name j11-incident-recovery
+"""
+from __future__ import annotations
+
+import argparse
+import sys
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import inspect as sa_inspect  # noqa: E402
+from sqlmodel import Session, select  # noqa: E402
+
+from app.db import make_engine  # noqa: E402
+from app.engine import j11_preboot_guard as guard  # noqa: E402
+from app.models import MaintenanceBoundary  # noqa: E402
+
+
+def _print_boundary_row(session: Session, name: str, label: str) -> None:
+    row = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == name)).first()
+    if row is None:
+        print(f"{label}: no {name!r} row exists", file=sys.stderr)
+    else:
+        print(
+            f"{label}: id={row.id} name={row.name!r} active={row.active} "
+            f"quarantined_dates_json={row.quarantined_dates_json} updated_at={row.updated_at}",
+            file=sys.stderr,
+        )
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--database-url", type=str, default=None,
+        help="required -- no default on purpose (never able to reach the real configured database by omission).",
+    )
+    parser.add_argument(
+        "--name", type=str, default=None,
+        help=(
+            "required -- the EXACT boundary name to disarm. Never defaults to "
+            f"{guard.J11_INCIDENT_BOUNDARY_NAME!r} or any other boundary; scoped strictly to whatever is "
+            "typed here, so this script can never accidentally touch an unrelated boundary."
+        ),
+    )
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches no database at all and exits non-zero.",
+    )
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm. No database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    if args.database_url is None:
+        print(
+            "refusing to run without an explicit --database-url. There is no default -- this script must "
+            "never be able to reach the real configured database by omission. No database interaction, "
+            "not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    if not args.name:
+        print(
+            "refusing to run without an explicit --name. There is no default boundary -- this script must "
+            "never guess which boundary to disarm. No database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    engine = make_engine(args.database_url)
+    if not sa_inspect(engine).has_table(MaintenanceBoundary.__tablename__):
+        print(
+            f"no-op: the {MaintenanceBoundary.__tablename__!r} table does not exist in "
+            f"{args.database_url!r} -- nothing is armed, so there is nothing to disarm. No write of any "
+            "kind has occurred.",
+            file=sys.stderr,
+        )
+        return 0
+
+    with Session(engine) as session:
+        _print_boundary_row(session, args.name, "BEFORE")
+
+    with Session(engine) as session:
+        row = guard.clear_boundary(session, args.name)
+
+    with Session(engine) as session:
+        _print_boundary_row(session, args.name, "AFTER")
+
+    if row is None:
+        print(f"no-op: no boundary named {args.name!r} was registered. No write has occurred.", file=sys.stderr)
+        return 0
+
+    print(f"J-11 MAINTENANCE BOUNDARY {args.name!r}: CLEARED (id={row.id})", file=sys.stderr)
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py b/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py
new file mode 100644
index 00000000..dfcad2df
--- /dev/null
+++ b/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py
@@ -0,0 +1,363 @@
+"""goal-market-compass iter-17 -- CLI-script tests for the J-11 maintenance-boundary arm/disarm
+entrypoints (`scripts/run_j11_maintenance_boundary_arm.py` / `_disarm.py`), covering the owner's TC-6
+through TC-10 (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle
+AUTHORIZED"). Exclusively fixture/temp-file SQLite databases -- `apps/backend/data/trendora.db` is never
+opened, copied, or referenced anywhere in this file (maintenance isolation stays active; the arm/disarm
+paths are proven on disposable state only, per the ruling's own instruction not to invoke either against
+live-armed/live state this iteration).
+
+Two test styles, mirroring `test_j11_stage_c_cli_script.py`'s established idiom:
+  - `unittest.mock`-based control-flow tests (missing `--confirm` / missing `--database-url` / missing
+    `--name`) -- prove NO database interaction of any kind occurs before the refusal, by mocking
+    `make_engine`/`Session` and asserting they are never called;
+  - real fixture-database tests (TC-6 through TC-10) -- a real temp-file SQLite database, actually
+    executed through `main()`, then independently re-opened and inspected."""
+from __future__ import annotations
+
+import importlib.util
+import json
+import sys
+from datetime import date, datetime, timezone
+from pathlib import Path
+from unittest import mock
+
+import pytest
+from sqlmodel import Session, select
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+ARM_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_maintenance_boundary_arm.py"
+DISARM_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_maintenance_boundary_disarm.py"
+
+sys.path.insert(0, str(BACKEND_DIR))
+from app.db import create_db_and_tables, make_engine  # noqa: E402
+from app.engine import j11_maintenance as jm  # noqa: E402
+from app.engine import j11_preboot_guard as guard  # noqa: E402
+from app.models import DailyPrice, MaintenanceBoundary, ScannerRun, Watchlist  # noqa: E402
+
+
+def _load_script_module(path: Path, name: str):
+    """Loads the script as a REAL module object via `importlib` (mirrors `test_j11_stage_c_cli_script.py`
+    exactly) so `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the script's
+    top-level code makes -- never executes `main()` itself at import time."""
+    spec = importlib.util.spec_from_file_location(name, path)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[name] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def arm_ns():
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test", None)
+
+
+@pytest.fixture()
+def disarm_ns():
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test", None)
+
+
+def _fixture_db_url(tmp_path: Path, name: str = "fixture.db") -> tuple[str, Path]:
+    db_path = tmp_path / name
+    return f"sqlite:///{db_path}", db_path
+
+
+# --- control-flow refusals (mock-based, mirrors test_j11_stage_c_cli_script.py) --------------------------
+
+
+def test_arm_missing_confirm_never_touches_database(monkeypatch, arm_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(arm_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_arm.py", "--database-url", "sqlite:///x.db"])
+
+    exit_code = arm_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+    assert "--confirm" in capsys.readouterr().err
+
+
+def test_arm_confirm_without_database_url_refuses(monkeypatch, arm_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(arm_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_arm.py", "--confirm"])
+
+    exit_code = arm_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+    assert "--database-url" in capsys.readouterr().err
+
+
+def test_arm_refuses_when_c1_date_set_check_fails(monkeypatch, arm_ns, tmp_path, capsys):
+    """A corrupted/disagreeing goal.md date-set check must refuse BEFORE any engine is constructed --
+    requirement 4's "must validate the exact incident-date set"."""
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(arm_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(arm_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="not the real goal.md"))
+    monkeypatch.setattr(
+        arm_ns.jsc, "check_c1_date_set_boundary",
+        mock.MagicMock(return_value={"ok": False, "extraction_error": "anchor not found"}),
+    )
+    db_url, _ = _fixture_db_url(tmp_path)
+    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url])
+
+    exit_code = arm_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+
+
+def test_disarm_missing_confirm_never_touches_database(monkeypatch, disarm_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(disarm_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_maintenance_boundary_disarm.py", "--database-url", "sqlite:///x.db", "--name", "b"],
+    )
+
+    exit_code = disarm_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+
+
+def test_disarm_confirm_and_url_without_name_refuses(monkeypatch, disarm_ns, tmp_path, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(disarm_ns, "make_engine", mock_make_engine)
+    db_url, _ = _fixture_db_url(tmp_path)
+    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url])
+
+    exit_code = disarm_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+    assert "--name" in capsys.readouterr().err
+
+
+# --- table-absent: refuse (arm) / no-op (disarm), no write of any kind ------------------------------------
+
+
+def test_arm_refuses_when_table_absent_and_writes_nothing(tmp_path, capsys):
+    db_url, db_path = _fixture_db_url(tmp_path, "no-tables.db")
+    # No create_db_and_tables() call at all -- the file may not even exist yet.
+    sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
+    ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_absent")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_absent", None)
+
+    assert exit_code != 0
+    assert "does not exist" in capsys.readouterr().err
+    if db_path.exists():
+        with Session(make_engine(db_url)) as session:
+            from sqlalchemy import inspect as sa_inspect
+            assert not sa_inspect(session.get_bind()).has_table("maintenance_boundaries")
+
+
+def test_disarm_is_noop_when_table_absent(tmp_path, capsys):
+    db_url, db_path = _fixture_db_url(tmp_path, "no-tables.db")
+    sys.argv = [
+        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url, "--name", "anything",
+    ]
+    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_absent")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_absent", None)
+
+    assert exit_code == 0
+    assert "no-op" in capsys.readouterr().err
+
+
+# --- TC-6/TC-7: arm creates exactly one row, idempotently -------------------------------------------------
+
+
+def test_tc6_arm_creates_exactly_one_row_with_correct_fields(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc6.db")
+    create_db_and_tables(make_engine(db_url))
+
+    sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
+    ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_tc6")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_tc6", None)
+    assert exit_code == 0
+
+    with Session(make_engine(db_url)) as session:
+        rows = session.exec(select(MaintenanceBoundary)).all()
+    assert len(rows) == 1
+    assert rows[0].name == guard.J11_INCIDENT_BOUNDARY_NAME
+    assert rows[0].active is True
+    assert json.loads(rows[0].quarantined_dates_json) == sorted(d.isoformat() for d in jm.INCIDENT_DATES)
+
+
+def test_tc7_arm_is_idempotent_on_second_invocation(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc7.db")
+    create_db_and_tables(make_engine(db_url))
+
+    for _ in range(2):
+        sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
+        ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_tc7")
+        try:
+            exit_code = ns.main()
+        finally:
+            sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_tc7", None)
+        assert exit_code == 0
+
+    with Session(make_engine(db_url)) as session:
+        rows = session.exec(
+            select(MaintenanceBoundary).where(MaintenanceBoundary.name == guard.J11_INCIDENT_BOUNDARY_NAME)
+        ).all()
+    assert len(rows) == 1
+    assert rows[0].active is True
+    assert json.loads(rows[0].quarantined_dates_json) == sorted(d.isoformat() for d in jm.INCIDENT_DATES)
+
+
+# --- TC-8: arm writes ONLY to maintenance_boundaries -------------------------------------------------------
+
+
+def _seed_other_tables(session: Session) -> dict:
+    session.add(DailyPrice(symbol="AAPL", date=date(2026, 8, 10), open=1, high=2, low=0.5, close=1.5, volume=100))
+    run = ScannerRun(
+        asof_date=date(2026, 8, 10), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=50.0, regime_label="Expansion", regime_components_json="[]",
+        breadth_above_50dma=50.0, breadth_above_200dma=50.0,
+        new_high_low_json="{}", candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.add(Watchlist(ticker="AAPL", reason="test", created_at=datetime.now(timezone.utc), asof_date_added=date(2026, 8, 10)))
+    session.commit()
+    return _snapshot_other_tables(session)
+
+
+def _snapshot_other_tables(session: Session) -> dict:
+    return {
+        "daily_prices": [row.model_dump() for row in session.exec(select(DailyPrice)).all()],
+        "scanner_runs": [row.model_dump() for row in session.exec(select(ScannerRun)).all()],
+        "watchlist": [row.model_dump() for row in session.exec(select(Watchlist)).all()],
+    }
+
+
+def test_tc8_arm_writes_only_to_maintenance_boundaries(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc8.db")
+    create_db_and_tables(make_engine(db_url))
+    with Session(make_engine(db_url)) as session:
+        before = _seed_other_tables(session)
+
+    sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
+    ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_tc8")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_tc8", None)
+    assert exit_code == 0
+
+    with Session(make_engine(db_url)) as session:
+        after = _snapshot_other_tables(session)
+        boundary_rows = session.exec(select(MaintenanceBoundary)).all()
+
+    assert before == after  # zero changed rows in every OTHER table
+    assert len(boundary_rows) == 1  # the ONE authorized write
+
+
+# --- TC-9/TC-10: disarm scoped strictly to the named boundary ---------------------------------------------
+
+
+def test_tc9_disarm_scoped_to_named_boundary_only(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc9.db")
+    create_db_and_tables(make_engine(db_url))
+    with Session(make_engine(db_url)) as session:
+        guard.register_j11_incident_boundary(session, active=True)
+        other = guard.register_boundary(
+            session, name="other-incident", dates=[date(2027, 1, 4)], reason="unrelated boundary",
+        )
+    other_before = other.model_dump()
+
+    sys.argv = [
+        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url,
+        "--name", guard.J11_INCIDENT_BOUNDARY_NAME,
+    ]
+    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_tc9")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_tc9", None)
+    assert exit_code == 0
+
+    with Session(make_engine(db_url)) as session:
+        j11_row = session.exec(
+            select(MaintenanceBoundary).where(MaintenanceBoundary.name == guard.J11_INCIDENT_BOUNDARY_NAME)
+        ).first()
+        other_row = session.exec(
+            select(MaintenanceBoundary).where(MaintenanceBoundary.name == "other-incident")
+        ).first()
+
+    assert j11_row.active is False
+    other_after = other_row.model_dump()
+    assert other_after == other_before  # untouched in EVERY field, including updated_at
+
+
+def test_tc10_after_disarm_incident_dates_unblocked_other_boundary_still_blocks(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc10.db")
+    create_db_and_tables(make_engine(db_url))
+    other_date = date(2027, 1, 4)
+    with Session(make_engine(db_url)) as session:
+        guard.register_j11_incident_boundary(session, active=True)
+        guard.register_boundary(session, name="other-incident", dates=[other_date], reason="unrelated boundary")
+
+    sys.argv = [
+        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url,
+        "--name", guard.J11_INCIDENT_BOUNDARY_NAME,
+    ]
+    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_tc10")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_tc10", None)
+    assert exit_code == 0
+
+    with Session(make_engine(db_url)) as session:
+        incident_result = guard.evaluate_boundary_for_date(session, jm.INCIDENT_DATES[0])
+        other_result = guard.evaluate_boundary_for_date(session, other_date)
+
+    assert incident_result["blocked"] is False
+    assert other_result["blocked"] is True
+    assert other_result["boundary_name"] == "other-incident"
+
+
+def test_disarm_is_noop_when_named_boundary_not_registered(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc-noop.db")
+    create_db_and_tables(make_engine(db_url))
+
+    sys.argv = [
+        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url, "--name", "never-armed",
+    ]
+    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_noop")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_noop", None)
+    assert exit_code == 0
+
+    with Session(make_engine(db_url)) as session:
+        rows = session.exec(select(MaintenanceBoundary)).all()
+    assert rows == []
+
+
+# --- neither script silently falls back to a real database when the flag is omitted ----------------------
+# (already proven above by `test_arm_confirm_without_database_url_refuses` and
+# `test_disarm_confirm_and_url_without_name_refuses`, which assert `make_engine` is never called at all
+# when `--database-url`/`--name` is omitted -- goal-market-compass iter-14's lesson: a silently-defaulted
+# path/target argument is how committed evidence/state gets touched by accident.)
```
