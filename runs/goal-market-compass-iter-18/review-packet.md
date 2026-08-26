# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` (22 lines not shown)

```diff
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index c3b4513c..303f155a 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -50,6 +50,7 @@ from sqlalchemy.exc import IntegrityError
 from sqlmodel import Session, select
 
 from app.config import Config, get_config
+from app.engine import j11_preboot_guard
 from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.engine.setups import ALL_STATUSES
@@ -538,8 +539,23 @@ def _backfill(session: Session, cfg: Config) -> dict:
 
     # (1)+(2): ensure a persisted immutable snapshot for every cadence as-of date. run_scan is
     # idempotent and recomputes nothing — the snapshot is the canonical bucket/setup/sector source.
+    #
+    # goal-market-compass iter-18 (J-11 step 11 ruling requirement 7): `_backfill` is reachable ONLY
+    # via `backfill_forward_returns`, which in production is called ONLY from
+    # `warmup._run_warmup` — i.e. this loop is a SECOND boot-initiated `run_scan` call site distinct
+    # from `_run_warmup`'s own cadence loop (their two date sets are independently derived and need not
+    # be identical), and it was not previously guarded. Same fail-closed check, same skip-and-continue
+    # behavior, same true no-op when no boundary is registered.
     asof_dates = walk_forward_asof_dates(session, cfg)
     for asof in asof_dates:
+        boundary = j11_preboot_guard.evaluate_boundary_for_date_fail_closed(session, asof)
+        if boundary["blocked"]:
+            logger.warning(
+                "walk-forward backfill: skipping canonical snapshot write for %s -- blocked by an "
+                "ACTIVE maintenance boundary %r: %s. No ScannerRun was created for this date.",
+                asof, boundary.get("boundary_name"), boundary.get("reason"),
+            )
+            continue
         run_scan(session, asof, cfg)
 
     # Idempotency: only INSERT (run, symbol, horizon) keys that do not already exist. iter-47 (J-105):
diff --git a/apps/backend/app/engine/j11_maintenance.py b/apps/backend/app/engine/j11_maintenance.py
index 370a6f89..c0fb7a79 100644
--- a/apps/backend/app/engine/j11_maintenance.py
+++ b/apps/backend/app/engine/j11_maintenance.py
@@ -34,7 +34,7 @@ from datetime import date, datetime, timezone
 from pathlib import Path
 from typing import Any, Optional, Union
 
-from sqlalchemy import func
+from sqlalchemy import func, text
 from sqlmodel import Session, select
 
 from app.config import Config, get_config
@@ -228,6 +228,83 @@ def freeze_attempt_identity(session: Session, config: Optional[Config] = None) -
     }
 
 
+def capture_full_table_sweep(session: Session) -> dict:
+    """goal-market-compass iter-18 -- a schema-agnostic, read-only row-count-and-content-fingerprint
+    sweep over EVERY table currently listed in `sqlite_master`. This is the J-11 table-create + arm live
+    sequence's mutation-accounting evidence (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact
+    maintenance-boundary table creation and live arm AUTHORIZED", implementation requirement 4: "capture
+    before/after evidence proving no unrelated application state changed").
+
+    For each table, computes the SAME cheap SQL-side aggregate this module's own `_count`/
+    `capture_pre_reset_inventory` idiom already relies on for the narrower per-population case (count + a
+    bounded set of aggregates -> sha256, never a full ORM hydration of a multi-million-row table -- AG-8)
+    -- generalized here to SQLite's own hidden `rowid` so it needs no per-table column knowledge at all.
+    Every table in this schema is an ordinary rowid table (a plain `id INTEGER PRIMARY KEY` column with
+    no `AUTOINCREMENT`, verified against the live schema for all 24 pre-existing tables, including empty
+    ones) -- none is declared `WITHOUT ROWID`, so `rowid` is universally available and requires no schema
+    introspection per table.
+
+    This is a CORROBORATING check, never the PRIMARY instrument: a same-rowid content UPDATE (e.g. a
+    non-key column changed on an existing row) would NOT move `count`/`min`/`max`/`sum` of `rowid` and so
+    would NOT be caught by this sweep alone -- the whole-file mtime/size/`-wal` bracket
+    (`j11_stage_c.db_file_fingerprint`, captured by the calling script at the TRUE process start and TRUE
+    process end) is the PRIMARY instrument that would catch that, per iter-12/13's established "mtime+WAL
+    as primary instrument, corroborated NOT replaced by a narrower fingerprint" precedent. Read-only --
+    never writes; never touches `maintenance_boundaries` specially (a caller comparing before/after
+    naturally sees it appear between the two sweeps, with a fingerprint of its own)."""
+    table_names = sorted(
+        row[0]
+        for row in session.exec(
+            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
+        ).all()
+    )
+    per_table: dict[str, dict] = {}
+    for name in table_names:
+        # Table names here come ONLY from `sqlite_master` itself (never user input) -- safe to interpolate
+        # into the FROM clause; every bind-able value (there are none here) would still go through
+        # parameters. Double-quoted identifier so a table name is never ambiguous with a keyword.
+        count, min_rowid, max_rowid, sum_rowid = session.exec(
+            text(f'SELECT COUNT(*), MIN(rowid), MAX(rowid), SUM(rowid) FROM "{name}"')
+        ).one()
+        payload = {
+            "count": int(count or 0),
+            "min_rowid": int(min_rowid) if min_rowid is not None else None,
+            "max_rowid": int(max_rowid) if max_rowid is not None else None,
+            "sum_rowid": int(sum_rowid) if sum_rowid is not None else None,
+        }
+        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
+        per_table[name] = {**payload, "fingerprint": fingerprint}
+    return {
+        "captured_at": datetime.now(timezone.utc).isoformat(),
+        "table_names": table_names,
+        "table_count": len(table_names),
+        "per_table": per_table,
+    }
+
+
+def diff_full_table_sweeps(before: dict, after: dict, *, expected_new_tables: tuple[str, ...] = ()) -> dict:
+    """Compares two `capture_full_table_sweep(...)` results. `expected_new_tables` names tables that are
+    PERMITTED to be new in `after` (e.g. `("maintenance_boundaries",)`) -- any OTHER new or removed table,
+    or ANY fingerprint change on a table present in BOTH sweeps, is an unexpected mutation. Never mutates
+    its inputs; pure comparison."""
+    before_tables = set(before["per_table"])
+    after_tables = set(after["per_table"])
+    unexpected_new = sorted((after_tables - before_tables) - set(expected_new_tables))
+    unexpected_removed = sorted(before_tables - after_tables)  # no table may ever disappear
+    changed_existing = sorted(
+        name
+        for name in (before_tables & after_tables)
+        if before["per_table"][name]["fingerprint"] != after["per_table"][name]["fingerprint"]
+    )
+    return {
+        "unexpected_new_tables": unexpected_new,
+        "unexpected_removed_tables": unexpected_removed,
+        "changed_existing_tables": changed_existing,
+        "expected_new_tables_present": sorted(t for t in expected_new_tables if t in after_tables),
+        "clean": not unexpected_new and not unexpected_removed and not changed_existing,
+    }
+
+
 def check_attempt_identity_consistency(
     frozen_identity: Union[dict, str], run_identity: Optional[str]
 ) -> bool:
diff --git a/apps/backend/app/engine/j11_preboot_guard.py b/apps/backend/app/engine/j11_preboot_guard.py
index a5f6bf79..15edf564 100644
--- a/apps/backend/app/engine/j11_preboot_guard.py
+++ b/apps/backend/app/engine/j11_preboot_guard.py
@@ -261,3 +261,38 @@ def evaluate_boundary_for_date(session: Session, one_date: date) -> dict:
             "ambiguous": True,
         }
     return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+
+# ----------------------------------------------------------------------------------------------
+# goal-market-compass iter-18 -- the ONE shared fail-closed entry point every boot-initiated
+# `run_scan` call site uses (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact maintenance-boundary
+# table creation and live arm AUTHORIZED", implementation requirement 7).
+# ----------------------------------------------------------------------------------------------
+
+
+def evaluate_boundary_for_date_fail_closed(session: Session, one_date: date) -> dict:
+    """`evaluate_boundary_for_date` above already fails CLOSED on unreadable/ambiguous ROW state (a
+    row whose `active`/`quarantined_dates_json` cannot be parsed cleanly). This wrapper additionally
+    fails CLOSED if the EVALUATION CALL ITSELF raises an unexpected exception (a transient DB error, a
+    bug, anything) -- the exact defensive shape `warmup.ensure_latest_snapshot` has used inline since
+    iteration 16 (`warmup.py` lines 106-113 at the time): never let an exception from this check escape
+    to its caller, and never treat "the check itself failed" as "not blocked".
+
+    goal-market-compass iter-18 factors this OUT of `ensure_latest_snapshot`'s inline try/except (left
+    untouched -- it already does the same thing and already has passing tests; touching it would be
+    unnecessary risk to already-correct code) so every OTHER boot-initiated call site that reaches
+    `run_scan` can share exactly ONE fail-closed wrapper instead of a THIRD/FOURTH hand-rolled copy of
+    the same six-line try/except: `warmup._run_warmup`'s own cadence loop, and (via
+    `forward_testing._backfill`, reachable ONLY from that same background warm-up thread --
+    `backfill_forward_returns` has no other production caller) its walk-forward snapshot loop. This is
+    also the ONE function a non-booting live-verification tool calls to prove the background-warmup call
+    site's OWN guard check works -- not merely that `evaluate_boundary_for_date` in isolation is correct,
+    but that this SAME wrapper (the literal object both call sites invoke) reports blocked for a
+    quarantined date. Read-only -- never writes."""
+    try:
+        return evaluate_boundary_for_date(session, one_date)
+    except Exception as exc:  # fail CLOSED: an unevaluable boundary state is never treated as clear
+        return {
+            "blocked": True, "boundary_name": None,
+            "reason": f"maintenance boundary check raised {exc!r} -- failing closed", "ambiguous": True,
+        }
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index 726e058d..1e3fb0a2 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -350,7 +350,24 @@ def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -
             # dies with the `with Session` block; the warm-up adds no bars, so no read sees a stale series.
             with bar_cache(session):
                 for index, asof in enumerate(dates, start=1):
-                    run_scan(session, asof, cfg)  # canonical engine; idempotent + concurrency-safe
+                    # goal-market-compass iter-18 (J-11 step 11 ruling requirement 7): the SAME
+                    # persisted-boundary check `ensure_latest_snapshot` already performs before ITS OWN
+                    # `run_scan` call, applied here too — this cadence loop is a SECOND boot-initiated
+                    # path capable of writing a canonical ScannerRun and was not previously guarded.
+                    # An active matching boundary skips ONLY this date's write (never aborts the whole
+                    # warm-up job); an ambiguous/unreadable boundary state fails CLOSED the same way
+                    # (skip, continue); no registered boundary — the common, no-incident case — leaves
+                    # this branch byte-identical to the pre-iteration-18 unconditional `run_scan` call.
+                    boundary = j11_preboot_guard.evaluate_boundary_for_date_fail_closed(session, asof)
+                    if boundary["blocked"]:
+                        logger.warning(
+                            "background warm-up: skipping canonical snapshot write for %s -- blocked by "
+                            "an ACTIVE maintenance boundary %r: %s. No ScannerRun was created for this "
+                            "date; the warm-up continues with the remaining dates.",
+                            asof, boundary.get("boundary_name"), boundary.get("reason"),
+                        )
+                    else:
+                        run_scan(session, asof, cfg)  # canonical engine; idempotent + concurrency-safe
                     prog.dates_done = index
                     prog.snapshots_created = index
                     # tick the message on each batch boundary (and the final date) so progress is live
diff --git a/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py b/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py
index 10873494..f3c2d3fe 100644
--- a/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py
+++ b/apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py
@@ -1,23 +1,43 @@
-"""goal-market-compass iter-17 -- TC-11/TC-12: strictly READ-ONLY live verification of the AG-8-fixed
-`evaluate_boundary_for_date` against the real `apps/backend/data/trendora.db`, plus the zero-live-writes
-proof (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED",
-implementation requirement 7: "verify through the same production guard entry point using a non-writing
-diagnostic/test harness").
+"""goal-market-compass iter-17/iter-18 -- strictly READ-ONLY live verification of
+`evaluate_boundary_for_date` (and, from iter-18, `evaluate_boundary_for_date_fail_closed`) against the
+real `apps/backend/data/trendora.db`, plus the zero-live-writes proof (docs/goal.md J-11 step 11).
+
+Iteration 17 built this to prove the boundary was NOT yet armed (the table did not exist). Iteration 18's
+"OWNER RULING -- J-11 exact maintenance-boundary table creation and live arm AUTHORIZED" implementation
+requirement 6 now requires the OPPOSITE direction: after the table-create + arm steps run, prove ARMED --
+all eleven canonical incident dates blocked, a non-incident control date NOT blocked, the current latest
+stored date (one of the eleven) blocked, PLUS that the background-warmup call site's own guard check
+(added in iter-18, `j11_preboot_guard.evaluate_boundary_for_date_fail_closed` -- the literal function both
+`warmup._run_warmup`'s cadence loop and `forward_testing._backfill`'s cadence loop call) ALSO reports
+blocked for a quarantined date -- not merely that the synchronous-path function agrees with itself. This
+script is EXTENDED in place (never replaced) to serve BOTH iterations honestly: it reports the ACTUAL live
+result rather than asserting a hardcoded expectation baked in at iter-17 time, so `J-11 MAINTENANCE
+BOUNDARY` / `J-11 LIVE PRE-BOOT GUARD` print ACTIVE/ARMED or NOT ACTIVE/NOT ARMED based on what the live
+database actually shows today.
 
 This script performs ZERO writes of any kind. It opens the live database through an ACTUAL read-only
 SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom
 `run_j11_iter16_stage_d_readiness.py` already established -- copied here unchanged, never imported cross-
 script since no shared utility module holds it today), calls the REAL, unmodified
-`app.engine.j11_preboot_guard.evaluate_boundary_for_date` for 2026-08-12, and independently confirms via a
-companion `sqlite_master` query that `maintenance_boundaries` does not exist. The database file's mtime +
-size + `-wal` sidecar size are fingerprinted at the TRUE start and TRUE end of the process (iteration-12's
-lesson: this bracket, not a narrow internal one, is the proof that matters) and written to their own
-before/after evidence files, mirroring `run_j11_stage_c_bounded_clear.py`'s / `run_j11_iter16_stage_d_
-readiness.py`'s established naming.
+`app.engine.j11_preboot_guard.evaluate_boundary_for_date` / `evaluate_boundary_for_date_fail_closed` for
+every canonical incident date plus one control date, and independently confirms via `sqlite_master` +
+direct row inspection that `maintenance_boundaries` exists (or does not) and, if present, that its
+`j11-incident-recovery` row's persisted date set matches the canonical `INCIDENT_DATES` exactly. The
+database file's mtime + size + `-wal` sidecar size are fingerprinted at the TRUE start and TRUE end of
+THIS SCRIPT's own process (iteration-12's lesson: this bracket, not a narrow internal one, is the proof
+that matters for THIS script's own zero-write claim -- the broader before/after-the-WHOLE-live-sequence
+mutation accounting is a separate, wider bracket captured by the dev handoff's own evidence, per Goal 5).
+
+goal-market-compass iter-18 rider (docs/goal.md J-11 step 11 ruling, iteration-17's own filed
+recommendation -- "one can overwrite three of iteration 16's saved evidence files if its destination
+folder is mistyped"): before ANY read or write, refuses (exits non-zero, touches nothing) if ANY of this
+invocation's own output filenames ALREADY EXISTS under `--evidence-dir` -- catching exactly a mistyped
+`--evidence-dir` pointed at an earlier iteration's already-populated evidence folder. A fresh, not-yet-
+written directory (the normal case) never trips this.
 
 Usage:
     apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py \\
-        --evidence-dir runs/goal-market-compass-iter-17
+        --evidence-dir runs/goal-market-compass-iter-18
 """
 from __future__ import annotations
 
@@ -37,10 +57,22 @@ from sqlmodel import Session  # noqa: E402
 
 from app.config import load_config  # noqa: E402
 from app.db import resolve_database_url  # noqa: E402
+from app.engine import j11_maintenance as jm  # noqa: E402
 from app.engine import j11_preboot_guard as guard  # noqa: E402
 from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.models import MaintenanceBoundary, ScannerRun  # noqa: E402
+
+# phase spec TC-3's own example: "a surviving, non-incident date" -- reused unchanged from iter-17's test
+# file convention (`test_j11_preboot_guard.py`'s `NON_INCIDENT_DATE`).
+CONTROL_DATE = date(2026, 7, 23)
 
-TARGET_DATE = date(2026, 8, 12)
+# This invocation's own output filenames -- the rider 6a collision-refusal check enumerates exactly these
+# BEFORE touching the database at all.
+OUTPUT_FILENAMES = (
+    "j11-iter17-readiness-db-file-true-start.json",
+    "j11-iter17-readiness-db-file-true-end.json",
+    "j11-iter18-live-preboot-guard-verification.json",
+)
 
 
 def _db_file_path(database_url: str) -> "Path | None":
@@ -66,12 +98,43 @@ def _read_only_engine(db_path: Path):
     return engine
 
 
+def _wal_effectively_unchanged(start_wal, end_wal) -> bool:
+    """goal-market-compass iter-18 fix: a plain `start_wal == end_wal` (iter-17's original check) is too
+    strict. `db_file_fingerprint`'s OWN docstring already documents why: "SQLite touches the WAL file on
+    any connection open in WAL mode, including read-only ones" -- so if NO `-wal` sidecar exists yet the
+    instant this script's read-only engine first connects, SQLite creates an empty one as a side effect of
+    the connection itself, which is a harmless bookkeeping artifact, never a data write (the WAL file
+    holds PENDING writes; a 0-byte WAL has none). Iter-17's own live run never exercised this branch
+    (its `-wal` sidecar already existed, unchanged, at both ends) -- this iteration's live sequence is the
+    first to hit it, because the table-create + arm steps immediately before this script apparently left
+    SQLite's own auto-checkpoint with no `-wal` file present at all by the time their connections closed.
+    Effectively unchanged means: the two dicts are identical (the common case), OR the transition is
+    EXACTLY absent -> present-with-zero-bytes (the harmless connect-time artifact). Any OTHER difference
+    (a WAL that grew past 0 bytes, one that disappeared, or a present-but-different one) still fails this
+    check -- this fix narrows the false positive, it does not blunt the detector."""
+    if start_wal == end_wal:
+        return True
+    start_exists = bool(start_wal) and start_wal.get("exists")
+    end_exists = bool(end_wal) and end_wal.get("exists")
+    return (not start_exists) and end_exists and end_wal.get("size_bytes") == 0
+
+
 def _write_json(path: Path, payload) -> None:
     path.parent.mkdir(parents=True, exist_ok=True)
     path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
     print(f"wrote {path}", file=sys.stderr)
 
 
+def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
+    """goal-market-compass iter-18 rider: the destination-collision guard every J-11 evidence-writing
+    script now carries. Returns the (possibly empty) list of filenames that ALREADY EXIST under
+    `evidence_dir` -- a non-empty result means "refuse before writing anything, this destination has
+    already been used" (catches a mistyped `--evidence-dir` pointed at an earlier iteration's populated
+    folder; a fresh, not-yet-written directory never collides). Pure filesystem check -- no database
+    interaction of any kind."""
+    return [name for name in filenames if (evidence_dir / name).exists()]
+
+
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
     parser.add_argument(
@@ -90,6 +153,19 @@ def main() -> int:
 
     evidence_dir: Path = args.evidence_dir
 
+    # --- rider 6a: refuse BEFORE any read or write if the destination already holds any of THIS run's ----
+    # --- own output filenames (a mistyped --evidence-dir pointed at an earlier iteration's folder). ------
+    colliding = _refuse_if_evidence_files_exist(evidence_dir, OUTPUT_FILENAMES)
+    if colliding:
+        print(
+            f"refusing to run: --evidence-dir {evidence_dir} already contains {colliding} -- this looks "
+            "like a mistyped destination pointed at an existing, already-populated evidence folder rather "
+            "than a fresh one for this run. No database interaction, not even a read, has occurred, and "
+            "no existing file has been touched.",
+            file=sys.stderr,
+        )
+        return 2
+
     cfg = load_config()
     resolved_url = resolve_database_url(cfg.database.url)
     db_path = _db_file_path(resolved_url)
@@ -110,7 +186,39 @@ def main() -> int:
                 "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='maintenance_boundaries'"
             )
         ).one()[0]
-        guard_result = guard.evaluate_boundary_for_date(session, TARGET_DATE)
+        scanner_run_count_before = session.exec(text("SELECT count(*) FROM scanner_runs")).one()[0]
+        latest_daily_price_date_raw = session.exec(text("SELECT max(date) FROM daily_prices")).one()[0]
+
+        boundary_row = None
+        if table_count:
+            row = session.exec(
+                text(
+                    "SELECT id, name, active, quarantined_dates_json, reason, updated_at "
+                    "FROM maintenance_boundaries WHERE name = :name"
+                ).bindparams(name=guard.J11_INCIDENT_BOUNDARY_NAME)
+            ).first()
+            if row is not None:
+                boundary_row = {
+                    "id": row[0], "name": row[1], "active": bool(row[2]),
+                    "quarantined_dates_json": row[3], "reason": row[4], "updated_at": str(row[5]),
+                }
+
+        # --- the SIX live-verification conditions (ruling requirement 6), through the SAME production ---
+        # --- guard entry points every boot-initiated path actually calls -- never re-derived logic. -----
+        incident_date_results = {
+            d.isoformat(): guard.evaluate_boundary_for_date(session, d) for d in jm.INCIDENT_DATES
+        }
+        control_result = guard.evaluate_boundary_for_date(session, CONTROL_DATE)
+
+        latest_incident_date = jm.INCIDENT_DATES[-1]  # 2026-08-12, the current latest stored incident date
+        latest_date_blocked = incident_date_results[latest_incident_date.isoformat()]["blocked"]
+
+        # The background-warmup call site's OWN guard check (iter-18's new call sites in `warmup._run_
+        # warmup` and `forward_testing._backfill` both call this EXACT function) -- exercised directly
+        # against the live read-only session, never by starting FastAPI or running either loop for real.
+        background_warmup_site_result = guard.evaluate_boundary_for_date_fail_closed(session, latest_incident_date)
+
+        scanner_run_count_after = session.exec(text("SELECT count(*) FROM scanner_runs")).one()[0]
 
     # --- TRUE process end: captured LAST, after every read above -------------------------------------
     db_file_true_end = jsc.db_file_fingerprint(db_path)
@@ -119,19 +227,54 @@ def main() -> int:
     zero_write_proof = {
         "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
         "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
-        "wal_unchanged": db_file_true_start.get("wal") == db_file_true_end.get("wal"),
+        "wal_unchanged": _wal_effectively_unchanged(db_file_true_start.get("wal"), db_file_true_end.get("wal")),
     }
+    zero_scanner_runs_created = int(scanner_run_count_before) == int(scanner_run_count_after)
+
+    all_eleven_blocked = all(r["blocked"] for r in incident_date_results.values())
+    control_not_blocked = control_result["blocked"] is False
+    persisted_dates = None
+    persisted_dates_match_canonical = False
+    if boundary_row is not None:
+        try:
+            persisted_dates = sorted(json.loads(boundary_row["quarantined_dates_json"]))
+            persisted_dates_match_canonical = persisted_dates == sorted(
+                d.isoformat() for d in jm.INCIDENT_DATES
+            )
+        except (TypeError, ValueError, json.JSONDecodeError):
+            persisted_dates = None
+
+    boundary_exists_and_active = boundary_row is not None and boundary_row["active"] is True
+    armed = (
+        boundary_exists_and_active
+        and persisted_dates_match_canonical
+        and all_eleven_blocked
+        and control_not_blocked
+        and latest_date_blocked
+        and background_warmup_site_result["blocked"]
+        and zero_scanner_runs_created
+    )
 
     verification = {
         "generated_at": datetime.now(timezone.utc).isoformat(),
-        "target_date": TARGET_DATE.isoformat(),
+        "control_date": CONTROL_DATE.isoformat(),
+        "latest_incident_date": latest_incident_date.isoformat(),
+        "latest_daily_price_date": latest_daily_price_date_raw,
         "db_path": str(db_path),
         "maintenance_boundaries_table_count": int(table_count),
-        "guard_result": guard_result,
-        "expected": {"maintenance_boundaries_table_count": 0, "guard_result_blocked": False},
-        "matches_expected": (
-            int(table_count) == 0 and guard_result.get("blocked") is False
-        ),
+        "boundary_row": boundary_row,
+        "persisted_dates_match_canonical": persisted_dates_match_canonical,
+        "incident_date_results": incident_date_results,
+        "control_result": control_result,
+        "all_eleven_incident_dates_blocked": all_eleven_blocked,
+        "control_date_not_blocked": control_not_blocked,
+        "latest_incident_date_blocked": latest_date_blocked,
+        "background_warmup_site_result": background_warmup_site_result,
+        "background_warmup_site_blocked": background_warmup_site_result["blocked"],
+        "scanner_run_count_before": int(scanner_run_count_before),
+        "scanner_run_count_after": int(scanner_run_count_after),
+        "zero_scanner_runs_created_by_this_verification": zero_scanner_runs_created,
+        "armed": armed,
         "db_file_true_start": db_file_true_start,
         "db_file_true_end": db_file_true_end,
         "zero_write_proof": zero_write_proof,
@@ -141,11 +284,13 @@ def main() -> int:
             f"--evidence-dir {evidence_dir}"
         ),
     }
-    _write_json(evidence_dir / "j11-iter17-live-preboot-guard-verification.json", verification)
+    _write_json(evidence_dir / "j11-iter18-live-preboot-guard-verification.json", verification)
 
     print(
-        f"maintenance_boundaries_table_count={table_count} guard_result={guard_result} "
-        f"matches_expected={verification['matches_expected']}",
+        f"maintenance_boundaries_table_count={table_count} all_eleven_blocked={all_eleven_blocked} "
+        f"control_not_blocked={control_not_blocked} latest_date_blocked={latest_date_blocked} "
+        f"background_warmup_site_blocked={background_warmup_site_result['blocked']} "
+        f"zero_scanner_runs_created={zero_scanner_runs_created} armed={armed}",
         file=sys.stderr,
     )
     print(
@@ -153,9 +298,9 @@ def main() -> int:
         f"size_unchanged={zero_write_proof['size_unchanged']} wal_unchanged={zero_write_proof['wal_unchanged']}",
         file=sys.stderr,
     )
-    print("J-11 MAINTENANCE BOUNDARY: NOT ACTIVE", file=sys.stderr)
-    print("J-11 LIVE PRE-BOOT GUARD: NOT ARMED", file=sys.stderr)
-    return 0 if verification["matches_expected"] and all(zero_write_proof.values()) else 1
+    print(f"J-11 MAINTENANCE BOUNDARY: {'ACTIVE' if boundary_exists_and_active else 'NOT ACTIVE'}", file=sys.stderr)
+    print(f"J-11 LIVE PRE-BOOT GUARD: {'ARMED' if armed else 'NOT ARMED'}", file=sys.stderr)
+    return 0 if armed and all(zero_write_proof.values()) else 1
 
 
 if __name__ == "__main__":
diff --git a/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py b/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py
index 794f525f..a5367696 100644
--- a/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py
+++ b/apps/backend/scripts/run_j11_iter17_stage_d_readiness.py
@@ -75,6 +75,20 @@ DEFAULT_ITERATION_14_IDENTITY_PATH = (
 )
 PERMITTED_DATES = diag.CALIBRATION_DATES + diag.RECOVERED_DATES
 
+# goal-market-compass iter-18 rider (docs/goal.md J-11 step 11 ruling; iteration-17's own filed
+# recommendation -- "one can overwrite three of iteration 16's saved evidence files if its destination
+# folder is mistyped"): every filename THIS script ever writes, checked for a pre-existing collision
+# BEFORE any other work runs. All three of `j11-stage-d-preflight.json` / `-preflight-gate.json` /
+# `j11-avb-bridge-diagnostic.json` already exist under `runs/goal-market-compass-iter-16/` -- exactly the
+# destination a mistyped `--evidence-dir` would collide with.
+OUTPUT_FILENAMES = (
+    "j11-stage-d-preflight.json",
+    "j11-stage-d-preflight-gate.json",
+    "j11-avb-bridge-diagnostic.json",
+    "j11-iter17-stage-d-readiness.json",
+    "j11-iter17-stage-d-readiness-zero-write-proof.json",
+)
+
 
 def _db_file_path(database_url: str) -> "Path | None":
     prefix = "sqlite:///"
@@ -105,6 +119,13 @@ def _write_json(path: Path, payload) -> None:
     print(f"wrote {path}", file=sys.stderr)
 
 
+def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
+    """goal-market-compass iter-18 rider: mirrors the SAME collision guard added to
+    `run_j11_iter17_live_preboot_guard_verification.py`. Returns the (possibly empty) list of filenames
+    that ALREADY EXIST under `evidence_dir` -- pure filesystem check, no database interaction."""
+    return [name for name in filenames if (evidence_dir / name).exists()]
+
+
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
     parser.add_argument(
@@ -130,6 +151,19 @@ def main() -> int:
         )
         return 2
 
+    # --- rider 6a: refuse BEFORE any other work if the destination already holds any of THIS script's ---
+    # --- own output filenames (a mistyped --evidence-dir pointed at an earlier iteration's folder). -----
+    colliding = _refuse_if_evidence_files_exist(args.evidence_dir, OUTPUT_FILENAMES)
+    if colliding:
+        print(
+            f"refusing to run: --evidence-dir {args.evidence_dir} already contains {colliding} -- this "
+            "looks like a mistyped destination pointed at an existing, already-populated evidence folder "
+            "rather than a fresh one for this run. No config has been loaded, no database engine has been "
+            "constructed, and no existing file has been touched.",
+            file=sys.stderr,
+        )
+        return 2
+
     # --- byte-unedited proof for iteration 16's own artifact, hashed BEFORE anything else runs -----------
     iter16_readiness_hash_before = hashlib.sha256(args.iteration_16_readiness_path.read_bytes()).hexdigest()
 
diff --git a/apps/backend/tests/test_j11_maintenance.py b/apps/backend/tests/test_j11_maintenance.py
index 43f6bfab..d3ac376b 100644
--- a/apps/backend/tests/test_j11_maintenance.py
+++ b/apps/backend/tests/test_j11_maintenance.py
@@ -324,3 +324,121 @@ def test_incident_dates_match_the_authoritative_removal_audit():
         "2026-08-03", "2026-08-05", "2026-08-10", "2026-08-11", "2026-08-12",
     ]
     assert [d.isoformat() for d in j11_maintenance.INCIDENT_DATES] == expected
+
+
+# ==========================================================================================================
+# goal-market-compass iter-18 -- `capture_full_table_sweep` / `diff_full_table_sweeps`: the schema-agnostic
+# mutation-accounting evidence for the J-11 table-create + arm live sequence (docs/goal.md J-11 step 11
+# ruling requirement 4).
+# ==========================================================================================================
+
+
+def test_capture_full_table_sweep_covers_every_table_including_empty_ones(engine):
+    with Session(engine) as session:
+        sweep = j11_maintenance.capture_full_table_sweep(session)
+
+    live_table_names = {t.name for t in SQLModel.metadata.sorted_tables}
+    assert set(sweep["table_names"]) == live_table_names
+    assert sweep["table_count"] == len(live_table_names)
+    # an empty table (every table in a fresh fixture) reports count=0 and None aggregates, never an error
+    for name in sweep["table_names"]:
+        row = sweep["per_table"][name]
+        assert row["count"] == 0
+        assert row["min_rowid"] is None
+        assert row["max_rowid"] is None
+        assert row["fingerprint"]  # still hashes cleanly on an all-None payload
+
+
+def test_capture_full_table_sweep_fingerprint_changes_when_a_row_is_added(engine):
+    with Session(engine) as session:
+        before = j11_maintenance.capture_full_table_sweep(session)
+
+    with Session(engine) as session:
+        session.add(
+            ScannerRun(
+                asof_date=date(2026, 1, 2), created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
+                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Expansion",
+                regime_components_json="[]", breadth_above_50dma=50.0, breadth_above_200dma=50.0,
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+        )
+        session.commit()
+
+    with Session(engine) as session:
+        after = j11_maintenance.capture_full_table_sweep(session)
+
+    assert before["per_table"]["scanner_runs"]["fingerprint"] != after["per_table"]["scanner_runs"]["fingerprint"]
+    assert after["per_table"]["scanner_runs"]["count"] == 1
+    # every OTHER table's fingerprint is untouched
+    for name in before["table_names"]:
+        if name == "scanner_runs":
+            continue
+        assert before["per_table"][name]["fingerprint"] == after["per_table"][name]["fingerprint"]
+
+
+def test_diff_full_table_sweeps_clean_when_nothing_changed(engine):
+    with Session(engine) as session:
+        before = j11_maintenance.capture_full_table_sweep(session)
+        after = j11_maintenance.capture_full_table_sweep(session)
+
+    diff = j11_maintenance.diff_full_table_sweeps(before, after)
+    assert diff == {
+        "unexpected_new_tables": [], "unexpected_removed_tables": [], "changed_existing_tables": [],
+        "expected_new_tables_present": [], "clean": True,
+    }
+
+
+def test_diff_full_table_sweeps_flags_an_unexpected_new_table_and_an_unexpected_change(engine):
+    with Session(engine) as session:
+        before = j11_maintenance.capture_full_table_sweep(session)
+
+    with engine.begin() as conn:
+        conn.exec_driver_sql("CREATE TABLE surprise_table (id INTEGER PRIMARY KEY)")
+    with Session(engine) as session:
+        session.add(
+            ScannerRun(
+                asof_date=date(2026, 1, 2), created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
+                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Expansion",
+                regime_components_json="[]", breadth_above_50dma=50.0, breadth_above_200dma=50.0,
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+        )
+        session.commit()
+
+    with Session(engine) as session:
+        after = j11_maintenance.capture_full_table_sweep(session)
+
+    diff = j11_maintenance.diff_full_table_sweeps(before, after)
+    assert diff["unexpected_new_tables"] == ["surprise_table"]
+    assert diff["changed_existing_tables"] == ["scanner_runs"]
+    assert diff["unexpected_removed_tables"] == []
+    assert diff["clean"] is False
+
+
+def test_diff_full_table_sweeps_expected_new_table_is_not_flagged():
+    """The exact shape the live J-11 sequence needs: `maintenance_boundaries` appearing between the
+    before/after sweeps is EXPECTED (it's the one authorized new table), and must not itself flag the
+    diff unclean when nothing else changed. Exercised against SYNTHETIC sweep dicts (`diff_full_table_
+    sweeps` is a pure function) rather than a live fixture engine -- the `engine` fixture above already
+    creates `maintenance_boundaries` via `SQLModel.metadata.create_all` (it is now a real committed
+    model), so a live DB cannot model "table genuinely absent, then created" for THIS one table name."""
+    unrelated = {"count": 0, "min_rowid": None, "max_rowid": None, "sum_rowid": None, "fingerprint": "x"}
+    before = {
+        "table_names": ["scanner_runs"], "table_count": 1,
+        "per_table": {"scanner_runs": unrelated},
+    }
+    after = {
+        "table_names": ["maintenance_boundaries", "scanner_runs"], "table_count": 2,
+        "per_table": {
+            "scanner_runs": unrelated,
+            "maintenance_boundaries": {
+                "count": 1, "min_rowid": 1, "max_rowid": 1, "sum_rowid": 1, "fingerprint": "y",
+            },
+        },
+    }
+
+    diff = j11_maintenance.diff_full_table_sweeps(before, after, expected_new_tables=("maintenance_boundaries",))
+    assert diff["unexpected_new_tables"] == []
+    assert diff["expected_new_tables_present"] == ["maintenance_boundaries"]
+    assert diff["changed_existing_tables"] == []
+    assert diff["clean"] is True
diff --git a/apps/backend/tests/test_j11_preboot_guard.py b/apps/backend/tests/test_j11_preboot_guard.py
index e3573f23..e5f20341 100644
--- a/apps/backend/tests/test_j11_preboot_guard.py
+++ b/apps/backend/tests/test_j11_preboot_guard.py
@@ -509,3 +509,213 @@ def test_iter17_table_absent_evaluates_cleanly_as_unblocked():
     with Session(eng) as session:
         result = guard.evaluate_boundary_for_date(session, TEST_DATE)
     assert result == {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+
+# ==========================================================================================================
+# goal-market-compass iter-18 -- TC-1 through TC-4: the `evaluate_boundary_for_date_fail_closed` wrapper
+# itself, then the background warm-up's TWO boot-initiated `run_scan` call sites (docs/goal.md J-11 step
+# 11, "OWNER RULING -- J-11 exact maintenance-boundary table creation and live arm AUTHORIZED",
+# implementation requirement 7: "ensure every boot-initiated path capable of creating a canonical
+# ScannerRun respects the same persisted maintenance-boundary contract").
+#
+# `warmup._run_warmup`'s own cadence loop is the FIRST (named directly in the ruling). Re-deriving the
+# boot/warmup call graph (grep for every production caller of `run_scan`) surfaces a SECOND, previously
+# unguarded one: `forward_testing._backfill`'s own cadence loop, reachable in production ONLY via
+# `backfill_forward_returns(session, cfg)` -- called ONLY from `warmup._run_warmup` (verified: no other
+# production caller exists). Both are exercised below by calling the REAL production function directly
+# (`_run_warmup` / `_backfill`), never a reimplementation of either loop -- `run_scan` and (for
+# `_run_warmup`) `backfill_forward_returns`/`_warmup_dates` are monkeypatched so each test isolates the
+# guard-wiring under test from unrelated complexity (the real config's `scanner.bootstrap_dates` /
+# `walk_forward` cadence, and the scanner engine's own correctness, both covered elsewhere).
+# ==========================================================================================================
+
+
+def test_iter18_fail_closed_wrapper_passes_through_a_normal_result(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="incident quarantine active")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date_fail_closed(session, TEST_DATE)
+    assert result == {
+        "blocked": True, "boundary_name": "b", "reason": "incident quarantine active", "ambiguous": False,
+    }
+
+
+def test_iter18_fail_closed_wrapper_catches_an_unexpected_exception(engine, monkeypatch):
+    def _boom(_session, _one_date):
+        raise RuntimeError("boom")
+
+    monkeypatch.setattr(guard, "evaluate_boundary_for_date", _boom)
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date_fail_closed(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["ambiguous"] is True
+    assert result["boundary_name"] is None
+
+
+# --- warmup._run_warmup's cadence loop (the FIRST call site, named in the ruling) ------------------------
+
+
+def _mk_warmup_prog():
+    return data_manager.JobProgress(
+        job_id="test-iter18-warmup", kind=warmup_mod.WARMUP_KIND, start=TEST_DATE, end=TEST_DATE,
+    )
+
+
+def test_iter18_tc1_warmup_cadence_loop_skips_a_blocked_date_no_run_created_logs_it(engine, cfg, monkeypatch, caplog):
+    blocked_date = jm.INCIDENT_DATES[0]
+    with Session(engine) as session:
+        guard.register_j11_incident_boundary(session, active=True)
+
+    monkeypatch.setattr(warmup_mod, "_warmup_dates", lambda session, cfg: [blocked_date])
+    monkeypatch.setattr(warmup_mod, "backfill_forward_returns", lambda session, cfg: {"rows_inserted": 0})
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    import logging
+    caplog.set_level(logging.WARNING, logger="trendora.warmup")
+    prog = _mk_warmup_prog()
+    warmup_mod._run_warmup(engine, cfg, prog)
+
+    assert calls == []  # run_scan never called for the blocked date
+    with Session(engine) as session:
+        assert warmup_mod.get_run_for_date(session, blocked_date) is None  # no ScannerRun created
+    assert prog.status == "ok"  # a blocked date never aborts the whole warm-up job
+    assert any(
+        blocked_date.isoformat() in record.getMessage() and guard.J11_INCIDENT_BOUNDARY_NAME in record.getMessage()
+        for record in caplog.records
+    )
+
+
+def test_iter18_tc2_warmup_cadence_loop_writes_normally_for_a_non_blocked_date(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        guard.register_j11_incident_boundary(session, active=True)  # armed, but OTHER_DATE isn't covered
+
+    monkeypatch.setattr(warmup_mod, "_warmup_dates", lambda session, cfg: [OTHER_DATE])
+    monkeypatch.setattr(warmup_mod, "backfill_forward_returns", lambda session, cfg: {"rows_inserted": 0})
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    prog = _mk_warmup_prog()
+    warmup_mod._run_warmup(engine, cfg, prog)
+
+    assert calls == [OTHER_DATE]  # run_scan DOES fire -- unchanged from pre-iteration-18 behavior
+    assert prog.dates_done == 1
+    assert prog.snapshots_created == 1
+
+
+def test_iter18_tc3_warmup_cadence_loop_fails_closed_on_a_guard_exception_and_continues(engine, cfg, monkeypatch):
+    monkeypatch.setattr(warmup_mod, "_warmup_dates", lambda session, cfg: [TEST_DATE, OTHER_DATE])
+    monkeypatch.setattr(warmup_mod, "backfill_forward_returns", lambda session, cfg: {"rows_inserted": 0})
+
+    def _boom(_session, one_date):
+        if one_date == TEST_DATE:
+            raise RuntimeError("boom")
+        return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+    monkeypatch.setattr(guard, "evaluate_boundary_for_date", _boom)
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    prog = _mk_warmup_prog()
+    warmup_mod._run_warmup(engine, cfg, prog)  # must NOT raise / must NOT crash the worker thread
+
+    assert calls == [OTHER_DATE]  # TEST_DATE skipped (fail closed); the loop continues to OTHER_DATE
+    assert prog.status == "ok"
+
+
+def test_iter18_tc4_warmup_zero_boundaries_registered_is_unchanged(engine, cfg, monkeypatch):
+    """No `MaintenanceBoundary` rows at all (the common no-incident case) -- every date's `run_scan` call
+    fires and the final dates_done/snapshots_created/forward_returns_inserted figures are exactly what the
+    pre-iteration-18 unconditional loop would have produced."""
+    monkeypatch.setattr(warmup_mod, "_warmup_dates", lambda session, cfg: [TEST_DATE, OTHER_DATE])
+    monkeypatch.setattr(warmup_mod, "backfill_forward_returns", lambda session, cfg: {"rows_inserted": 7})
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    prog = _mk_warmup_prog()
+    warmup_mod._run_warmup(engine, cfg, prog)
+
+    assert calls == [TEST_DATE, OTHER_DATE]  # every date processed, in order -- unchanged
+    assert prog.dates_total == 2
+    assert prog.dates_done == 2
+    assert prog.snapshots_created == 2
+    assert prog.forward_returns_inserted == 7
+    assert prog.status == "ok"
+
+
+# --- forward_testing._backfill's cadence loop (the SECOND call site, found on re-derivation) --------------
+
+from app.engine import forward_testing as ft_mod  # noqa: E402
+
+
+def test_iter18_backfill_loop_skips_a_blocked_date_no_run_created_logs_it(engine, cfg, monkeypatch, caplog):
+    blocked_date = jm.INCIDENT_DATES[0]
+    with Session(engine) as session:
+        _seed_one_price(session)  # _backfill's own early "no price data" guard needs latest_data_date != None
+        guard.register_j11_incident_boundary(session, active=True)
+
+    monkeypatch.setattr(ft_mod, "walk_forward_asof_dates", lambda session, cfg: [blocked_date])
+    calls = []
+    monkeypatch.setattr(ft_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    import logging
+    caplog.set_level(logging.WARNING, logger="trendora.forward_testing")
+    with Session(engine) as session:
+        result = ft_mod._backfill(session, cfg)
+
+    assert calls == []  # run_scan never called for the blocked date
+    with Session(engine) as session:
+        assert warmup_mod.get_run_for_date(session, blocked_date) is None
+    assert result["rows_inserted"] == 0
+    assert any(
+        blocked_date.isoformat() in record.getMessage() and guard.J11_INCIDENT_BOUNDARY_NAME in record.getMessage()
+        for record in caplog.records
+    )
+
+
+def test_iter18_backfill_loop_writes_normally_for_a_non_blocked_date(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        _seed_one_price(session)
+        guard.register_j11_incident_boundary(session, active=True)  # armed, but OTHER_DATE isn't covered
+
+    monkeypatch.setattr(ft_mod, "walk_forward_asof_dates", lambda session, cfg: [OTHER_DATE])
+    calls = []
+    monkeypatch.setattr(ft_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    with Session(engine) as session:
+        ft_mod._backfill(session, cfg)
+
+    assert calls == [OTHER_DATE]
+
+
+def test_iter18_backfill_loop_fails_closed_on_a_guard_exception_and_continues(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        _seed_one_price(session)
+    monkeypatch.setattr(ft_mod, "walk_forward_asof_dates", lambda session, cfg: [TEST_DATE, OTHER_DATE])
+
+    def _boom(_session, one_date):
+        if one_date == TEST_DATE:
+            raise RuntimeError("boom")
+        return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+    monkeypatch.setattr(guard, "evaluate_boundary_for_date", _boom)
+    calls = []
+    monkeypatch.setattr(ft_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    with Session(engine) as session:
+        ft_mod._backfill(session, cfg)  # must NOT raise
+
+    assert calls == [OTHER_DATE]  # TEST_DATE skipped (fail closed); OTHER_DATE still processed
+
+
+def test_iter18_backfill_loop_zero_boundaries_registered_is_unchanged(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        _seed_one_price(session)
+    monkeypatch.setattr(ft_mod, "walk_forward_asof_dates", lambda session, cfg: [TEST_DATE, OTHER_DATE])
+    calls = []
+    monkeypatch.setattr(ft_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    with Session(engine) as session:
+        ft_mod._backfill(session, cfg)
+
+    assert calls == [TEST_DATE, OTHER_DATE]  # every date processed -- unchanged from pre-iteration-18
diff --git a/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py b/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py
index dfcad2df..b8c22af2 100644
--- a/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py
+++ b/apps/backend/tests/test_j11_preboot_guard_cli_scripts.py
@@ -361,3 +361,417 @@ def test_disarm_is_noop_when_named_boundary_not_registered(tmp_path):
 # `test_disarm_confirm_and_url_without_name_refuses`, which assert `make_engine` is never called at all
 # when `--database-url`/`--name` is omitted -- goal-market-compass iter-14's lesson: a silently-defaulted
 # path/target argument is how committed evidence/state gets touched by accident.)
+
+
+# ==========================================================================================================
+# goal-market-compass iter-18 -- TC-5 through TC-8: the new table-create-or-verify entrypoint
+# (`run_j11_maintenance_boundary_table_create.py`, docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact
+# maintenance-boundary table creation and live arm AUTHORIZED", implementation requirements 1-2).
+# ==========================================================================================================
+
+TABLE_CREATE_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_maintenance_boundary_table_create.py"
+
+
+@pytest.fixture()
+def table_create_ns():
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test", None)
+
+
+def test_table_create_missing_confirm_never_touches_database(monkeypatch, table_create_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(
+        sys, "argv", ["run_j11_maintenance_boundary_table_create.py", "--database-url", "sqlite:///x.db"],
+    )
+
+    exit_code = table_create_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+    assert "--confirm" in capsys.readouterr().err
+
+
+def test_table_create_confirm_without_database_url_refuses(monkeypatch, table_create_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_table_create.py", "--confirm"])
+
+    exit_code = table_create_ns.main()
+
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+    assert "--database-url" in capsys.readouterr().err
+
+
+# --- TC-5: table absent -> created, schema-exact, no other table touched ----------------------------------
+
+
+def test_tc5_table_create_creates_exact_schema_when_absent_and_touches_nothing_else(tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc5.db")
+    # `create_db_and_tables` creates EVERY SQLModel table, `MaintenanceBoundary` included -- so, to model
+    # "every OTHER table exists, maintenance_boundaries does not" (proving the create is scoped to ONLY
+    # that one table, not a side effect of "some table is missing"), create normally then drop back to
+    # absent. This fixture-setup DROP is not the script under test.
+    create_db_and_tables(make_engine(db_url))
+    with make_engine(db_url).begin() as conn:
+        conn.exec_driver_sql("DROP TABLE maintenance_boundaries")
+    with Session(make_engine(db_url)) as session:
+        before = _seed_other_tables(session)
+
+    from sqlalchemy import inspect as sa_inspect
+    assert not sa_inspect(make_engine(db_url)).has_table("maintenance_boundaries")
+
+    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
+    ns = _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_tc5")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_tc5", None)
+    assert exit_code == 0
+
+    engine = make_engine(db_url)
+    assert sa_inspect(engine).has_table("maintenance_boundaries")
+    live_cols = {c["name"] for c in sa_inspect(engine).get_columns("maintenance_boundaries")}
+    expected_cols = {c.name for c in MaintenanceBoundary.__table__.columns}
+    assert live_cols == expected_cols
+    with Session(engine) as session:
+        assert session.exec(select(MaintenanceBoundary)).all() == []  # created empty -- arming is separate
+        after = _snapshot_other_tables(session)
+    assert before == after  # no other table's rows changed
+
+
+# --- TC-6: table present and exact -> idempotent no-op ------------------------------------------------------
+
+
+def test_tc6_table_create_is_a_noop_when_already_exact(tmp_path, capsys):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc6.db")
+    create_db_and_tables(make_engine(db_url))  # maintenance_boundaries already created, schema-exact
+    with Session(make_engine(db_url)) as session:
+        guard.register_boundary(session, name="pre-existing", dates=[date(2027, 1, 4)], reason="r")
+
+    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
+    ns = _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_tc6")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_tc6", None)
+    assert exit_code == 0
+    assert "already correct, no action taken" in capsys.readouterr().err
+
+    with Session(make_engine(db_url)) as session:
+        rows = session.exec(select(MaintenanceBoundary)).all()
+    assert len(rows) == 1
+    assert rows[0].name == "pre-existing"  # untouched -- a no-op writes nothing, not even a re-save
+
+
+# --- TC-7: table present but mismatched (missing a column) -> STOP, zero write, names the column -----------
+
+
+def _create_mismatched_table(db_url: str) -> None:
+    """A `maintenance_boundaries` table missing the `reason` column -- everything else matches exactly."""
+    engine = make_engine(db_url)
+    with engine.begin() as conn:
+        conn.exec_driver_sql(
+            """
+            CREATE TABLE maintenance_boundaries (
+                id INTEGER NOT NULL,
+                name VARCHAR NOT NULL,
+                quarantined_dates_json VARCHAR NOT NULL,
+                active BOOLEAN NOT NULL,
+                created_at DATETIME NOT NULL,
+                updated_at DATETIME NOT NULL,
+                PRIMARY KEY (id)
+            )
+            """
+        )
+
+
+def test_tc7_table_create_stops_on_mismatch_and_names_the_missing_column(tmp_path, capsys):
+    db_url, db_path = _fixture_db_url(tmp_path, "tc7.db")
+    create_db_and_tables(make_engine(db_url))
+    # Replace the just-created exact table with a deliberately mismatched one (drop it first -- this
+    # fixture setup step, not the script under test, performs the drop).
+    with make_engine(db_url).begin() as conn:
+        conn.exec_driver_sql("DROP TABLE maintenance_boundaries")
+    _create_mismatched_table(db_url)
+    with Session(make_engine(db_url)) as session:
+        before = _seed_other_tables(session)
+
+    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
+    ns = _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_tc7")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_tc7", None)
+
+    assert exit_code != 0
+    stderr = capsys.readouterr().err
+    assert "STOP" in stderr
+    assert "reason" in stderr  # the exact missing column is named
+
+    with Session(make_engine(db_url)) as session:
+        after = _snapshot_other_tables(session)
+    assert before == after  # zero write of any kind -- not even to the mismatched table itself
+    from sqlalchemy import inspect as sa_inspect
+    live_cols = {c["name"] for c in sa_inspect(make_engine(db_url)).get_columns("maintenance_boundaries")}
+    assert "reason" not in live_cols  # untouched -- never ALTERed to "fix" the mismatch
+
+
+# --- TC-8: refuse without --confirm / --database-url, zero interaction (already covered above by the two ---
+# --- `test_table_create_*_never_touches_database` tests; this pair adds the SAME assertions phrased ------
+# --- against TC-8's own two separate invocations for direct traceability). ---------------------------------
+
+
+def test_tc8_missing_confirm_refuses_with_zero_database_interaction(monkeypatch, table_create_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_maintenance_boundary_table_create.py", "--database-url", "sqlite:///should-never-open.db"],
+    )
+    exit_code = table_create_ns.main()
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+
+
+def test_tc8_missing_database_url_refuses_with_zero_database_interaction(monkeypatch, table_create_ns, capsys):
+    mock_make_engine = mock.MagicMock(name="make_engine")
+    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
+    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_table_create.py", "--confirm"])
+    exit_code = table_create_ns.main()
+    assert exit_code != 0
+    mock_make_engine.assert_not_called()
+
+
+# ==========================================================================================================
+# goal-market-compass iter-18 -- TC-13 (rider 6a): both `run_j11_iter17_live_preboot_guard_verification.py`
+# and `run_j11_iter17_stage_d_readiness.py` refuse to write -- and touch nothing at all -- when their
+# `--evidence-dir` already contains one of their own output filenames (iteration-17's own filed
+# recommendation: "one can overwrite three of iteration 16's saved evidence files if its destination
+# folder is mistyped").
+# ==========================================================================================================
+
+LIVE_VERIFICATION_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_iter17_live_preboot_guard_verification.py"
+STAGE_D_READINESS_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_iter17_stage_d_readiness.py"
+
+
+def test_tc13_live_verification_refuses_on_evidence_destination_collision(tmp_path, capsys):
+    evidence_dir = tmp_path / "colliding-evidence"
+    evidence_dir.mkdir()
+    colliding_path = evidence_dir / "j11-iter17-readiness-db-file-true-start.json"
+    original_content = '{"already": "here", "from": "a prior run"}'
+    colliding_path.write_text(original_content)
+
+    sys.argv = [
+        "run_j11_iter17_live_preboot_guard_verification.py", "--evidence-dir", str(evidence_dir),
+    ]
+    ns = _load_script_module(LIVE_VERIFICATION_SCRIPT_PATH, "run_j11_iter17_live_preboot_guard_verification_under_test_tc13")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_tc13", None)
+
+    assert exit_code != 0
+    assert colliding_path.read_text() == original_content  # byte-unchanged
+    # no OTHER output file was written either -- the refusal happens before ANY write, not just this one
+    assert not (evidence_dir / "j11-iter17-readiness-db-file-true-end.json").exists()
+    assert not (evidence_dir / "j11-iter18-live-preboot-guard-verification.json").exists()
+    assert "mistyped" in capsys.readouterr().err
+
+
+def test_tc13_live_verification_collision_guard_does_not_fire_on_a_fresh_dir(monkeypatch, tmp_path, capsys):
+    """The refusal is narrowly scoped -- a genuinely FRESH, empty --evidence-dir (the normal case for a
+    new iteration) must not be refused merely for existing as a directory. This script has no fixture-DB
+    argument (it always resolves the live configured database path), so `_db_file_path` is monkeypatched
+    to return None -- the SAME "could not resolve a live sqlite db file" branch the script already has
+    for a genuinely missing/non-sqlite URL -- so this test proves the collision guard specifically did
+    NOT fire, without opening `apps/backend/data/trendora.db` (this test file's own docstring: "never
+    opened, copied, or referenced anywhere in this file")."""
+    evidence_dir = tmp_path / "fresh-evidence"
+    evidence_dir.mkdir()
+
+    sys.argv = ["run_j11_iter17_live_preboot_guard_verification.py", "--evidence-dir", str(evidence_dir)]
+    ns = _load_script_module(LIVE_VERIFICATION_SCRIPT_PATH, "run_j11_iter17_live_preboot_guard_verification_under_test_fresh")
+    try:
+        monkeypatch.setattr(ns, "_db_file_path", lambda _url: None)
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_fresh", None)
+
+    assert exit_code == 1  # the LATER "could not resolve a live sqlite db file" branch, not the refusal
+    assert "mistyped" not in capsys.readouterr().err
+    # the collision guard did not write anything either (it never got that far) -- confirms the refusal
+    # branch and the "could not resolve" branch are genuinely different code paths, not the same message
+    assert not (evidence_dir / "j11-iter17-readiness-db-file-true-start.json").exists()
+
+
+def test_tc13_stage_d_readiness_refuses_on_evidence_destination_collision(tmp_path, capsys):
+    evidence_dir = tmp_path / "colliding-evidence"
+    evidence_dir.mkdir()
+    colliding_path = evidence_dir / "j11-avb-bridge-diagnostic.json"
+    original_content = '{"already": "here", "from": "a prior run"}'
+    colliding_path.write_text(original_content)
+
+    sys.argv = ["run_j11_iter17_stage_d_readiness.py", "--evidence-dir", str(evidence_dir)]
+    ns = _load_script_module(STAGE_D_READINESS_SCRIPT_PATH, "run_j11_iter17_stage_d_readiness_under_test_tc13")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_iter17_stage_d_readiness_under_test_tc13", None)
+
+    assert exit_code != 0
+    assert colliding_path.read_text() == original_content  # byte-unchanged
+    # no OTHER output file was written -- the refusal fires before the iteration-16 hash read, before
+    # config load, before any database engine is constructed
+    assert not (evidence_dir / "j11-stage-d-preflight.json").exists()
+    assert not (evidence_dir / "j11-stage-d-preflight-gate.json").exists()
+    assert not (evidence_dir / "j11-iter17-stage-d-readiness.json").exists()
+    assert "mistyped" in capsys.readouterr().err
+
+
+def test_tc13_stage_d_readiness_collision_check_runs_before_reading_iteration_16_files(monkeypatch, tmp_path, capsys):
+    """Proves the refusal is checked BEFORE `hashlib.sha256(args.iteration_16_readiness_path.read_bytes())`
+    -- pointing `--iteration-16-readiness-path` at a nonexistent file would otherwise raise FileNotFoundError
+    before the collision check ever ran, which would be a DIFFERENT (and misleading) failure mode."""
+    evidence_dir = tmp_path / "colliding-evidence"
+    evidence_dir.mkdir()
+    (evidence_dir / "j11-stage-d-preflight.json").write_text('{"already": "here"}')
+
+    sys.argv = [
+        "run_j11_iter17_stage_d_readiness.py", "--evidence-dir", str(evidence_dir),
+        "--iteration-16-readiness-path", str(tmp_path / "does-not-exist.json"),
+    ]
+    ns = _load_script_module(STAGE_D_READINESS_SCRIPT_PATH, "run_j11_iter17_stage_d_readiness_under_test_tc13b")
+    try:
+        exit_code = ns.main()  # must return the refusal code, NOT raise FileNotFoundError
+    finally:
+        sys.modules.pop("run_j11_iter17_stage_d_readiness_under_test_tc13b", None)
+
+    assert exit_code != 0
+    assert "mistyped" in capsys.readouterr().err
+
+
+# ==========================================================================================================
+# goal-market-compass iter-18 -- `run_j11_iter18_full_table_sweep.py`: the mutation-accounting evidence
+# capture used to bracket the whole live table-create + arm + verify sequence (docs/goal.md J-11 step 11
+# ruling requirement 4). Not one of the phase spec's own numbered TC scenarios (it is this developer's own
+# evidence-capture tooling, layered on the already-tested `j11_maintenance.capture_full_table_sweep`) --
+# proportionate coverage: the one genuinely new behavior here (the CLI wrapper + its collision refusal),
+# not a re-test of the sweep function itself.
+# ==========================================================================================================
+
+FULL_TABLE_SWEEP_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_iter18_full_table_sweep.py"
+
+
+def test_full_table_sweep_missing_evidence_dir_or_label_refuses(tmp_path, capsys):
+    for argv in (
+        ["run_j11_iter18_full_table_sweep.py", "--label", "before"],
+        ["run_j11_iter18_full_table_sweep.py", "--evidence-dir", str(tmp_path)],
+    ):
+        sys.argv = argv
+        ns = _load_script_module(FULL_TABLE_SWEEP_SCRIPT_PATH, "run_j11_iter18_full_table_sweep_under_test_refuse")
+        try:
+            exit_code = ns.main()
+        finally:
+            sys.modules.pop("run_j11_iter18_full_table_sweep_under_test_refuse", None)
+        assert exit_code != 0
+
+
+def test_full_table_sweep_refuses_on_output_collision(tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    evidence_dir.mkdir()
+    colliding = evidence_dir / "j11-iter18-full-table-sweep-before.json"
+    colliding.write_text('{"already": "here"}')
+
+    sys.argv = [
+        "run_j11_iter18_full_table_sweep.py", "--evidence-dir", str(evidence_dir), "--label", "before",
+    ]
+    ns = _load_script_module(FULL_TABLE_SWEEP_SCRIPT_PATH, "run_j11_iter18_full_table_sweep_under_test_collision")
+    try:
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_iter18_full_table_sweep_under_test_collision", None)
+
+    assert exit_code != 0
+    assert colliding.read_text() == '{"already": "here"}'
+
+
+def test_full_table_sweep_writes_expected_shape_against_a_fixture_db(monkeypatch, tmp_path):
+    db_url, db_path = _fixture_db_url(tmp_path, "sweep-fixture.db")
+    create_db_and_tables(make_engine(db_url))
+    evidence_dir = tmp_path / "evidence"
+
+    sys.argv = ["run_j11_iter18_full_table_sweep.py", "--evidence-dir", str(evidence_dir), "--label", "before"]
+    ns = _load_script_module(FULL_TABLE_SWEEP_SCRIPT_PATH, "run_j11_iter18_full_table_sweep_under_test_shape")
+    try:
+        monkeypatch.setattr(ns, "resolve_database_url", lambda _url: db_url)
+        exit_code = ns.main()
+    finally:
+        sys.modules.pop("run_j11_iter18_full_table_sweep_under_test_shape", None)
+
+    assert exit_code == 0
+    payload = json.loads((evidence_dir / "j11-iter18-full-table-sweep-before.json").read_text())
+    assert payload["label"] == "before"
+    assert "maintenance_boundaries" in payload["sweep"]["table_names"]
+    assert payload["zero_write_proof"]["mtime_unchanged"] is True
+    assert payload["zero_write_proof"]["size_unchanged"] is True
+
+
+# ==========================================================================================================
+# goal-market-compass iter-18 -- `_wal_effectively_unchanged`: discovered live, during this iteration's OWN
+# authorized live sequence (docs/goal.md J-11 step 11 ruling requirement 6's zero-write proof). A naive
+# `start_wal == end_wal` (iter-17's original check) false-flagged the harmless "no -wal sidecar existed yet,
+# a read-only connection created an empty one" artifact `db_file_fingerprint`'s own docstring already
+# documents. Fixed in `run_j11_iter17_live_preboot_guard_verification.py`; tested here directly (pure
+# function, no database needed).
+# ==========================================================================================================
+
+
+def _load_live_verification_module():
+    return _load_script_module(LIVE_VERIFICATION_SCRIPT_PATH, "run_j11_iter17_live_preboot_guard_verification_under_test_wal")
+
+
+def test_wal_effectively_unchanged_identical_dicts_is_true():
+    ns = _load_live_verification_module()
+    try:
+        wal = {"exists": True, "mtime": 123.0, "size_bytes": 0}
+        assert ns._wal_effectively_unchanged(wal, dict(wal)) is True
+        assert ns._wal_effectively_unchanged({"exists": False}, {"exists": False}) is True
+    finally:
+        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_wal", None)
+
+
+def test_wal_effectively_unchanged_absent_to_present_zero_bytes_is_true():
+    """The exact shape this iteration's own live run hit: no -wal sidecar existed at true-start, and a
+    read-only connect created an empty one by true-end -- a harmless artifact, not a write."""
+    ns = _load_live_verification_module()
+    try:
+        assert ns._wal_effectively_unchanged(
+            {"exists": False}, {"exists": True, "mtime": 999.0, "size_bytes": 0},
... [diff_bound] apps/backend/tests/test_j11_preboot_guard_cli_scripts.py: 22 more diff lines omitted — Read the file for full detail
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     |  13 +-
 ...ase-goal-market-compass-iter-17-ui-test-plan.md |  13 ++
 .../j11-avb-bridge-diagnostic.json                 |   4 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-market-compass/session.json      |   8 +-
 .../state/assumptions.md                           | 202 +++------------------
 .../state/assumptions.md.archive.md                | 179 ++++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  |  29 +--
 .../state/lessons.md.archive.md                    |  40 ++++
 .../state/retro-input.md                           |   4 +-
 runs/goal-session-market-compass/summary.md        |  28 ++-
 runs/goal-session-market-compass/telemetry.jsonl   |  43 +++++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   3 +
 14 files changed, 348 insertions(+), 224 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
