# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/session.json      |  2 +-
 .../state/assumptions.md                           | 90 ++++++----------------
 .../state/assumptions.md.archive.md                | 70 +++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  | 17 +---
 .../state/lessons.md.archive.md                    | 23 ++++++
 runs/goal-session-market-compass/telemetry.jsonl   | 15 ++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  3 +
 8 files changed, 137 insertions(+), 85 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
