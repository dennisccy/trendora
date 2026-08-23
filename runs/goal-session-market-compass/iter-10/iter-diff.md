# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 5fa1bb33..391f1e49 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -817,7 +817,35 @@ class NextSessionManifest(SQLModel, table=True):
     # iter-3: version starts at 1 (the finalize freeze or the first historical on-demand GET); a
     # confirm-gated regenerate mints version N+1 for an existing as_of. Pre-iter-3 rows backfill 1.
     version: int = Field(default=1)
-    source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)
+    # goal-market-compass iter-10 (J-11 Stage B1): the LIVE `FOREIGN KEY(source_run_id) REFERENCES
+    # scanner_runs (id)` DDL is DROPPED from the model declaration here (model-declaration change only --
+    # no live-DB migration; the already-created live table keeps its existing DDL untouched, per
+    # `.claude/project-template.md`'s additive-ALTER-only schema-evolution rule). This was a LATENT
+    # contradiction, not a new one: enforcement was already OFF on the live DB (`PRAGMA foreign_keys` reads
+    # `0` -- `app.db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`), and
+    # `PRAGMA foreign_key_check(next_session_manifests)` already reports 12 violations on the live DB
+    # today, all on incident-dated manifests -- so the FK declaration was never actually enforced; it was
+    # only ever aspirational. Declaring it here as `foreign_key=...` documents a contract the design does
+    # NOT want: AG-12 (manifest immutability) requires a manifest to survive its source `ScannerRun` being
+    # deleted and canonically rebuilt (J-11 Stages C/D, a LATER iteration), and a rebuilt run legitimately
+    # gets a fresh row (or, since `scanner_runs.id` is a plain SQLite rowid alias with no `AUTOINCREMENT`
+    # and no `sqlite_sequence` table, can even REUSE a freed numeric id).
+    #
+    # Intended end state (docs/goal.md J-11 step 11, verbatim): "`source_run_id` remains stored historical
+    # provenance; it is not required to dereference to a live `ScannerRun` forever; manifest survival must
+    # not depend on foreign-key enforcement being off; current-run reconciliation is by `as_of` + frozen
+    # source timing/provenance, never by FK rebinding; a rebuilt run may legitimately carry a different id;
+    # and even when it reuses the same numeric id it is still a rebuilt run whenever the frozen
+    # timestamp/provenance differs. Never mutate a manifest to 'repair' an orphaned foreign key."
+    #
+    # Reconciliation after a delete/rebuild is therefore by `as_of` + `source_run_created_at` (carried
+    # inside `generation_json`) + the frozen `engine_identity` -- NEVER by dereferencing `source_run_id`.
+    # `app.engine.compass.basis_disclosure` already implements exactly this (it resolves the CURRENT run
+    # by `as_of` and compares `source_run_created_at` against that run's `created_at` -- it never reads
+    # `source_run_id` at all) and needs NO change here. `source_run_id` stays `index=True` (still a useful
+    # lookup/audit column) and its VALUE is still written once and never mutated (AG-12) -- only the live
+    # `FOREIGN KEY` constraint declaration is removed.
+    source_run_id: int = Field(index=True)
     session_delta_json: str
     narrative_json: str
     selection_json: str
diff --git a/apps/backend/app/engine/j11_maintenance.py b/apps/backend/app/engine/j11_maintenance.py
new file mode 100644
index 00000000..5dd88cbf
--- /dev/null
+++ b/apps/backend/app/engine/j11_maintenance.py
@@ -0,0 +1,236 @@
+"""app.engine.j11_maintenance -- J-11 Stages B/B1/B2 precondition tooling (goal-market-compass iter-10).
+
+J-11 repairs the derived-state fallout of the iter-5 drill (`docs/handoffs/goal-market-compass-iter-5-dev.md`)
+over 11 incident dates, but the destructive clear/regenerate (Stages C-G) is explicitly OUT OF SCOPE this
+iteration (`docs/phases/goal-market-compass-iter-10.md`). This module is read-only/pure precondition
+tooling only:
+
+  - `capture_pre_reset_inventory(session)` -- Stage B: a read-only, column-projected snapshot of every
+    row Stage C onward touches or must leave untouched. An audit checkpoint, not a second historical
+    database (docs/goal.md Stage B wording).
+  - `freeze_attempt_identity(session, config)` -- Stage B2: freezes ONE `engine_identity` (+ its decomposed
+    config subset) for the WHOLE later regeneration attempt, so Stage D can prove every rebuilt run shares
+    one identity rather than silently mixing "dates 1-5 under engine A, dates 6-11 under engine B"
+    (docs/goal.md J-11 step 12).
+  - `check_attempt_identity_consistency(frozen_identity, run_identity)` -- the PURE per-run invariant
+    helper Stage D will call once per rebuilt run. Deliberately no aggregate-only form -- iter-9's AVB
+    counter-example is the reason: a population-wide "all N matched" claim is exactly where the one real
+    mismatch hides.
+
+Nothing here deletes, updates, or inserts a snapshot/manifest/price row. `app.engine.compass.
+basis_disclosure` already resolves current-run identity by `as_of` + `source_run_created_at` and needs
+no change from this module (see the comment on `NextSessionManifest.source_run_id` in `app/models.py`).
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Any, Optional, Union
+
+from sqlalchemy import func
+from sqlmodel import Session, select
+
+from app.config import Config, get_config
+from app.engine import engine_identity
+from app.engine.evidence import resolve_ledger_path
+from app.engine.graveyard import resolve_staging_ledger_path
+from app.models import (
+    DailyPrice,
+    DataProviderRun,
+    ForwardReturn,
+    NextSessionManifest,
+    ScannerResult,
+    ScannerRun,
+    SectorScoreRow,
+    ThemeScoreRow,
+    Watchlist,
+)
+
+# The exact 11 incident dates from `data_provider_runs` id=538's own cascade record (docs/goal.md J-11,
+# "The incident date set -- all 11, not the 8 currently absent"). These are INCIDENT-SPECIFIC historical
+# facts, not a reusable threshold -- literal here for the SAME reason `app.engine.j10_recovery.
+# RECOVERY_DATES` is a literal (docs/goal.md NOTES: "promoting them to config would misrepresent a single
+# dated incident as a standing feature", contrary to AG-9's "not a standing path" framing).
+# `test_no_magic_numbers.py`'s `CALC_FILES` deliberately excludes this module for the identical reason it
+# excludes `j10_recovery.py` -- nothing here is a scoring weight, band edge, or decision cutoff.
+INCIDENT_DATES: tuple[date, ...] = (
+    date(2026, 5, 12),
+    date(2026, 5, 13),
+    date(2026, 7, 10),
+    date(2026, 7, 13),
+    date(2026, 7, 24),
+    date(2026, 7, 27),
+    date(2026, 8, 3),
+    date(2026, 8, 5),
+    date(2026, 8, 10),
+    date(2026, 8, 11),
+    date(2026, 8, 12),
+)
+
+
+def _utc_isoformat(value: Optional[datetime]) -> Optional[str]:
+    """Same tzinfo-safe re-serialization `app.engine.compass._utc_isoformat` uses (SQLite drops tzinfo on
+    round-trip) -- an honest `None` passes through unchanged, never a fabricated timestamp."""
+    if value is None:
+        return None
+    if value.tzinfo is None:
+        value = value.replace(tzinfo=timezone.utc)
+    return value.astimezone(timezone.utc).isoformat()
+
+
+def _file_sha256(path: str) -> dict:
+    """Read-only sha256 of a ledger file. A missing file records `exists: False` honestly (ledgers are
+    append-only and may legitimately not exist yet) -- never a fabricated hash, never a crash."""
+    resolved = Path(path)
+    if not resolved.exists():
+        return {"path": str(resolved), "exists": False, "sha256": None}
+    return {"path": str(resolved), "exists": True, "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest()}
+
+
+def _count(session: Session, model: Any, **filters: Any) -> int:
+    """A column-projected `COUNT(*)` -- never an ORM hydration of the matched rows (AG-8)."""
+    stmt = select(func.count()).select_from(model)
+    for key, value in filters.items():
+        stmt = stmt.where(getattr(model, key) == value)
+    return int(session.scalar(stmt) or 0)
+
+
+def capture_pre_reset_inventory(session: Session) -> dict:
+    """Stage B -- read-only snapshot of everything the later destructive stages (C onward, OUT OF SCOPE
+    this iteration) touch or must leave untouched: per-incident-date derived row counts (from BOTH
+    populations goal.md names -- rows a date's own run originated, and rows whose `measured_date` lands on
+    that date regardless of originating run, i.e. the "holes on retained runs" population Stage E must
+    repair), the `daily_prices` canonical-input coverage + a cheap SQL-side aggregate fingerprint (never a
+    full ORM hydration of the ~3.3M-row table -- AG-8), the manifest inventory for the incident dates that
+    currently carry one, and the audit/user-state row counts + ledger file hashes that must be
+    byte-identical after any future J-11 stage. Every value here is READ; nothing is written."""
+    captured_at = datetime.now(timezone.utc).isoformat()
+
+    # ONE grouped scan of forward_returns for the "measured INTO an incident date" population (the
+    # defensive-sweep hole population on possibly-RETAINED runs) -- never 11 separate full-table scans.
+    measured_into_counts: dict[date, int] = dict(
+        session.exec(
+            select(ForwardReturn.measured_date, func.count())
+            .where(ForwardReturn.measured_date.in_(INCIDENT_DATES))
+            .group_by(ForwardReturn.measured_date)
+        ).all()
+    )
+
+    manifests_by_date: dict[str, list[dict]] = {}
+    manifest_rows = session.exec(
+        select(NextSessionManifest)
+        .where(NextSessionManifest.as_of.in_(INCIDENT_DATES))
+        .order_by(NextSessionManifest.as_of, NextSessionManifest.version)
+    ).all()
+    for row in manifest_rows:
+        manifests_by_date.setdefault(row.as_of.isoformat(), []).append(
+            {
+                "version": row.version,
+                "mode": row.mode,
+                "frozen": row.frozen,
+                "source_run_id": row.source_run_id,
+                "content_hash": row.content_hash,
+                "manifest_hash": row.manifest_hash,
+                "prospective_eligible": row.prospective_eligible,
+                "available_at_utc": _utc_isoformat(row.available_at_utc),
+            }
+        )
+
+    per_date: dict[str, dict] = {}
+    for one_date in INCIDENT_DATES:
+        key = one_date.isoformat()
+        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == one_date)).first()
+        run_id = run.id if run is not None else None
+        per_date[key] = {
+            "scanner_run": {
+                "present": run is not None,
+                "run_id": run_id,
+                "created_at": _utc_isoformat(run.created_at) if run is not None else None,
+                "engine_identity": run.engine_identity if run is not None else None,
+            },
+            "scanner_results_count": _count(session, ScannerResult, run_id=run_id),
+            "sector_scores_count": _count(session, SectorScoreRow, run_id=run_id),
+            "theme_scores_count": _count(session, ThemeScoreRow, run_id=run_id),
+            "forward_returns_from_run_count": _count(session, ForwardReturn, run_id=run_id),
+            "forward_returns_measured_into_count": int(measured_into_counts.get(one_date, 0)),
+            "manifests": manifests_by_date.get(key, []),
+        }
+
+    price_row = session.exec(
+        select(
+            func.count(DailyPrice.id),
+            func.min(DailyPrice.date),
+            func.max(DailyPrice.date),
+            func.sum(DailyPrice.id),
+            func.sum(DailyPrice.open + DailyPrice.high + DailyPrice.low + DailyPrice.close + DailyPrice.volume),
+        )
+    ).one()
+    row_count, min_date, max_date, id_sum, ohlcv_sum = price_row
+    price_fingerprint_payload = {
+        "row_count": int(row_count or 0),
+        "min_date": min_date.isoformat() if min_date else None,
+        "max_date": max_date.isoformat() if max_date else None,
+        "id_sum": int(id_sum or 0),
+        "ohlcv_sum": float(ohlcv_sum or 0.0),
+    }
+    price_fingerprint = hashlib.sha256(
+        json.dumps(price_fingerprint_payload, sort_keys=True, default=str).encode()
+    ).hexdigest()
+
+    return {
+        "captured_at": captured_at,
+        "incident_dates": [d.isoformat() for d in INCIDENT_DATES],
+        "per_date": per_date,
+        "daily_prices": {**price_fingerprint_payload, "fingerprint": price_fingerprint},
+        "data_provider_runs_count": _count(session, DataProviderRun),
+        "watchlist_count": _count(session, Watchlist),
+        "certified_claims_ledger": _file_sha256(resolve_ledger_path()),
+        "staging_ledger": _file_sha256(resolve_staging_ledger_path()),
+    }
+
+
+def freeze_attempt_identity(session: Session, config: Optional[Config] = None) -> dict:
+    """Stage B2 -- freezes ONE `engine_identity` for the WHOLE later J-11 regeneration attempt (Stages
+    C-G, out of scope this iteration; docs/goal.md step 12's invariant: "Every `ScannerRun` recreated by
+    one J-11 regeneration attempt MUST carry the same `engine_identity`, equal to the identity frozen in
+    that attempt's pre-reset inventory"). `session` is accepted for call-shape symmetry with
+    `capture_pre_reset_inventory` (a uniform three-function surface for the CLI script) -- this function
+    itself performs no DB read: the frozen identity is purely code+config, via the SAME
+    `app.engine.engine_identity.compute_engine_identity` function `scanner.persist_run_payload` already
+    stamps onto every newly created `ScannerRun.engine_identity` (reused, not reimplemented -- so Stage
+    D's later per-run check compares like with like).
+
+    `config_subset`/`config_subset_hash` decompose the SAME `provenance.config_keys` values
+    `compute_engine_identity` already folds into its digest -- recorded here in cleartext (not just
+    hashed) so `j11-frozen-identity.json` is itself human-auditable: a reader can see WHICH config values
+    were frozen for this attempt, not just a hash of them."""
+    cfg = config or get_config()
+    identity = engine_identity.compute_engine_identity(cfg)
+    cfg_dict = cfg.model_dump()
+    config_subset = {key: engine_identity._config_value(cfg_dict, key) for key in cfg.provenance.config_keys}
+    config_subset_hash = hashlib.sha256(
+        json.dumps(config_subset, sort_keys=True, default=str).encode()
+    ).hexdigest()
+    return {
+        "engine_identity": identity,
+        "config_subset_hash": config_subset_hash,
+        "config_subset": config_subset,
+        "provenance_config_keys": list(cfg.provenance.config_keys),
+        "provenance_engine_files": list(cfg.provenance.engine_files),
+        "frozen_at": datetime.now(timezone.utc).isoformat(),
+    }
+
+
+def check_attempt_identity_consistency(
+    frozen_identity: Union[dict, str], run_identity: Optional[str]
+) -> bool:
+    """The PURE per-run invariant helper Stage D will call once per rebuilt run -- no aggregate-only form
+    (iter-9 lesson: a population-wide "all matched" flag is exactly where the one real mismatch hides).
+    `frozen_identity` accepts either the `dict` `freeze_attempt_identity` returns or a bare identity
+    string, so a caller holding either shape need not unpack first. `run_identity` is the run's OWN
+    stamped `ScannerRun.engine_identity` value -- fail-closed: `None` (a pre-stamping-era or
+    not-yet-persisted run) is NEVER consistent, never silently treated as a match."""
+    expected = frozen_identity.get("engine_identity") if isinstance(frozen_identity, dict) else frozen_identity
+    return run_identity is not None and run_identity == expected
diff --git a/apps/backend/scripts/run_j11_pre_reset_inventory.py b/apps/backend/scripts/run_j11_pre_reset_inventory.py
new file mode 100644
index 00000000..78624d80
--- /dev/null
+++ b/apps/backend/scripts/run_j11_pre_reset_inventory.py
@@ -0,0 +1,160 @@
+"""goal-market-compass iter-10 -- J-11 Stage B/B2 read-only pre-reset inventory + frozen-identity CLI.
+
+Wraps `app.engine.j11_maintenance.capture_pre_reset_inventory` (Stage B) and `freeze_attempt_identity`
+(Stage B2) against the LIVE production database, via the SAME `app.db` session helpers the real backend
+uses (`get_engine()` -- never a raw file copy, never `create_db_and_tables()`/`metadata.create_all()`,
+which would run additive-ALTER/index-hygiene sweeps this script has no business triggering). Every
+statement this script issues is a plain SELECT/aggregate read; it inserts, updates, and deletes nothing.
+
+This is the ONE authorized live-database interaction for goal-market-compass iter-10 (J-11 Stages B/B1/B2
+only -- the destructive clear/regenerate, Stages C-G, stays out of scope for a later iteration;
+`docs/phases/goal-market-compass-iter-10.md`). Maintenance isolation is active for this iteration: no
+backend/frontend boot, no browser QA, no replay lane -- this script is the sanctioned live-DB check.
+
+Self-proving zero-write check (TC-1/TC-2): the `daily_prices` count/date-range/fingerprint the capture
+step itself computes is re-derived a SECOND time, independently, via `_daily_prices_spot_check` (the
+identical aggregate query, run again over the pooled connection) -- and the file's own mtime is compared
+before/after. All three must match for the script to report success; the full comparison, plus the file
+mtime themselves, is written into the inventory artifact as `zero_write_proof` so the proof travels with
+the evidence rather than living only in this run's stdout.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_pre_reset_inventory.py \\
+        [--inventory-path runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json] \\
+        [--identity-path runs/goal-market-compass-iter-10/j11-frozen-identity.json]
+"""
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import sys
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import func  # noqa: E402
+from sqlmodel import Session, select  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import get_engine, resolve_database_url  # noqa: E402
+from app.engine.j11_maintenance import capture_pre_reset_inventory, freeze_attempt_identity  # noqa: E402
+from app.models import DailyPrice  # noqa: E402
+
+DEFAULT_INVENTORY_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-pre-reset-inventory.json"
+DEFAULT_IDENTITY_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-frozen-identity.json"
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    """The on-disk path a `sqlite:///...` URL resolves to, or `None` for a non-sqlite / in-memory URL
+    (no mtime to check in that case)."""
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    return Path(raw)
+
+
+def _daily_prices_spot_check(session: Session) -> dict:
+    """An INDEPENDENT re-query of the SAME daily_prices count/date-range/fingerprint the inventory
+    capture itself computed -- run a second time, over a second statement, purely to PROVE the capture
+    step wrote nothing (TC-2). Mirrors `capture_pre_reset_inventory`'s own price aggregate query exactly
+    (never a second formula -- both read `DailyPrice.id`/`.date`/OHLCV the identical way)."""
+    row = session.exec(
+        select(
+            func.count(DailyPrice.id),
+            func.min(DailyPrice.date),
+            func.max(DailyPrice.date),
+            func.sum(DailyPrice.id),
+            func.sum(DailyPrice.open + DailyPrice.high + DailyPrice.low + DailyPrice.close + DailyPrice.volume),
+        )
+    ).one()
+    row_count, min_date, max_date, id_sum, ohlcv_sum = row
+    payload = {
+        "row_count": int(row_count or 0),
+        "min_date": min_date.isoformat() if min_date else None,
+        "max_date": max_date.isoformat() if max_date else None,
+        "id_sum": int(id_sum or 0),
+        "ohlcv_sum": float(ohlcv_sum or 0.0),
+    }
+    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
+    return {**payload, "fingerprint": fingerprint}
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument("--inventory-path", type=Path, default=DEFAULT_INVENTORY_PATH)
+    parser.add_argument("--identity-path", type=Path, default=DEFAULT_IDENTITY_PATH)
+    args = parser.parse_args()
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    print(f"database (read-only queries only, never written): {resolved_url}", file=sys.stderr)
+
+    db_file = _db_file_path(resolved_url)
+    mtime_before = db_file.stat().st_mtime if db_file is not None and db_file.exists() else None
+
+    engine = get_engine()  # existing app.db session helper -- resolves the SAME committed config.yaml
+    # database.url the real backend boots against. Deliberately NOT create_db_and_tables()/
+    # metadata.create_all() (those run additive-ALTER + index-hygiene sweeps) and NEVER a raw file copy.
+
+    with Session(engine) as session:
+        inventory = capture_pre_reset_inventory(session)
+        identity = freeze_attempt_identity(session, cfg)
+        spot_check = _daily_prices_spot_check(session)
+
+    mtime_after = db_file.stat().st_mtime if db_file is not None and db_file.exists() else None
+
+    captured_prices = inventory["daily_prices"]
+    zero_write_proof = {
+        "capture_daily_prices": captured_prices,
+        "independent_spot_check": spot_check,
+        "counts_match": (
+            captured_prices["row_count"] == spot_check["row_count"]
+            and captured_prices["min_date"] == spot_check["min_date"]
+            and captured_prices["max_date"] == spot_check["max_date"]
+        ),
+        "fingerprints_match": captured_prices["fingerprint"] == spot_check["fingerprint"],
+        "db_file": str(db_file) if db_file is not None else None,
+        "mtime_before": mtime_before,
+        "mtime_after": mtime_after,
+        "mtime_unchanged": mtime_before == mtime_after,
+    }
+    inventory["zero_write_proof"] = zero_write_proof
+
+    proved_zero_write = (
+        zero_write_proof["counts_match"]
+        and zero_write_proof["fingerprints_match"]
+        and zero_write_proof["mtime_unchanged"]
+    )
+
+    args.inventory_path.parent.mkdir(parents=True, exist_ok=True)
+    args.inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True, default=str))
+    print(f"wrote {args.inventory_path}", file=sys.stderr)
+
+    if not proved_zero_write:
+        print("FAIL: the capture step did not prove zero writes -- see zero_write_proof in the "
+              "written inventory artifact. Refusing to write the identity artifact.", file=sys.stderr)
+        return 1
+
+    args.identity_path.parent.mkdir(parents=True, exist_ok=True)
+    args.identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True, default=str))
+    print(f"wrote {args.identity_path}", file=sys.stderr)
+
+    print(f"engine_identity={identity['engine_identity']}", file=sys.stderr)
+    print(
+        f"zero_write_proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
+        f"counts_match={zero_write_proof['counts_match']} "
+        f"fingerprints_match={zero_write_proof['fingerprints_match']}",
+        file=sys.stderr,
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_maintenance.py b/apps/backend/tests/test_j11_maintenance.py
new file mode 100644
index 00000000..43f6bfab
--- /dev/null
+++ b/apps/backend/tests/test_j11_maintenance.py
@@ -0,0 +1,326 @@
+"""goal-market-compass iter-10 -- J-11 Stage B/B1/B2 precondition tests (TC-3..TC-7).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`, hand-built rows)
+-- the SAME pattern `test_manifest_invariants.py` uses, never `loaded_engine`. Two lessons from the
+session's own `lessons.md` shape these tests directly (docs/goal.md BACKGROUND, iter-7/iter-9):
+  - iter-7: a fail-closed gate proven only against complete fixtures can silently agree on a degenerate/
+    empty input -- `test_tc5_degenerate_orphan...` below is exactly that missing case (a manifest whose
+    source run was deleted with NO replacement ever created).
+  - iter-9: a population-wide "all N matched" claim is where the one real counter-example hides --
+    `test_tc7_...` asserts a MATCHING and a MISMATCHED run as two explicit, separate assertions, never
+    one aggregate flag.
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine
+
+from app.config import load_config
+from app.engine import compass, j11_maintenance
+from app.models import NextSessionManifest, ScannerRun
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+@pytest.fixture()
+def engine():
+    """A fresh in-memory SQLite DB built from the CURRENT SQLModel metadata, with `PRAGMA
+    foreign_keys=ON` explicitly issued on every connection this engine ever opens -- via a `connect`
+    event listener, the SAME mechanism `app.db._apply_sqlite_pragmas` uses for the real backend.
+    (SQLite ignores `PRAGMA foreign_keys` if issued inside an already-open transaction, which a
+    Session-level `session.exec(text(...))` would be -- the connect-time listener is the only place
+    that reliably lands it BEFORE any transaction begins.)"""
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+
+    @event.listens_for(eng, "connect")
+    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
+        cursor = dbapi_connection.cursor()
+        cursor.execute("PRAGMA foreign_keys=ON")
+        cursor.close()
+
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+def _mk_run(
+    session: Session, asof: date, *, created_at: datetime, engine_identity_value: str | None = None
+) -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=created_at, provider="seed", benchmark="SPY",
+        regime_score=60.0, regime_label="Expansion", regime_components_json="[]",
+        breadth_above_50dma=55.0, breadth_above_200dma=60.0,
+        new_high_low_json="{}", candidate_counts_json="{}",
+        engine_identity=engine_identity_value,
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
+    """A hand-built manifest row referencing `run` -- the TEST DOUBLE the phase spec's steps (a)-(d)
+    literally describe ("insert a ScannerRun + a NextSessionManifest row referencing it"), never routed
+    through the full `compass._freeze_manifest` selection/candidate pipeline (that content-computation
+    path is already covered end-to-end by `test_manifest_invariants.py`; these tests are about the
+    schema/FK relationship + `basis_disclosure`'s read-time comparison only)."""
+    manifest = NextSessionManifest(
+        as_of=run.asof_date,
+        version=version,
+        source_run_id=run.id,
+        session_delta_json="{}",
+        narrative_json="{}",
+        selection_json="{}",
+        content_hash="stub-content-hash",
+        created_at=datetime.now(timezone.utc),
+        mode="at_ingest",
+        frozen=True,
+        generation_json=json.dumps({
+            "producer": "ingest_finalize",
+            "engine_identity": "stub-engine-identity",
+            "source_run_created_at": compass._utc_isoformat(run.created_at),
+        }),
+        engine_identity="stub-engine-identity",
+        manifest_hash="stub-manifest-hash",
+        available_at_utc=datetime.now(timezone.utc),
+        prospective_eligible=True,
+    )
+    session.add(manifest)
+    session.flush()
+    return manifest
+
+
+# --- TC-3: PRAGMA foreign_keys=ON, delete the source run -- no violation, manifest untouched ------
+
+
+def test_tc3_fk_on_delete_source_run_no_violation_manifest_untouched(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 8, 11), created_at=datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc))
+        session.commit()
+        run_id = run.id
+        manifest = _mk_manifest(session, run)
+        session.commit()
+        manifest_id = manifest.id
+        before = {
+            "source_run_id": manifest.source_run_id, "content_hash": manifest.content_hash,
+            "manifest_hash": manifest.manifest_hash, "version": manifest.version,
+            "available_at_utc": manifest.available_at_utc, "prospective_eligible": manifest.prospective_eligible,
+            "generation_json": manifest.generation_json,
+        }
+
+    with Session(engine) as session:
+        row = session.get(ScannerRun, run_id)
+        session.delete(row)
+        session.commit()  # must NOT raise an IntegrityError
+
+    with Session(engine) as session:
+        after_row = session.get(NextSessionManifest, manifest_id)
+        assert after_row is not None
+        after = {
+            "source_run_id": after_row.source_run_id, "content_hash": after_row.content_hash,
+            "manifest_hash": after_row.manifest_hash, "version": after_row.version,
+            "available_at_utc": after_row.available_at_utc, "prospective_eligible": after_row.prospective_eligible,
+            "generation_json": after_row.generation_json,
+        }
+    assert after == before
+    assert after["source_run_id"] == run_id
+
+
+# --- TC-4: rebuilt-same-as_of -- basis_disclosure reports rebuilt; manifest fields unchanged ------
+
+
+def test_tc4_rebuilt_same_as_of_reports_rebuilt_fields_unchanged(engine):
+    t1 = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)
+    t2 = datetime(2026, 8, 22, 9, 0, tzinfo=timezone.utc)
+    with Session(engine) as session:
+        old_run = _mk_run(session, date(2026, 8, 11), created_at=t1)
+        session.commit()
+        old_run_id = old_run.id
+        manifest = _mk_manifest(session, old_run)
+        session.commit()
+        manifest_id = manifest.id
+        before = {
+            "source_run_id": manifest.source_run_id, "content_hash": manifest.content_hash,
+            "manifest_hash": manifest.manifest_hash, "version": manifest.version,
+            "available_at_utc": manifest.available_at_utc, "prospective_eligible": manifest.prospective_eligible,
+        }
+
+    with Session(engine) as session:
+        old = session.get(ScannerRun, old_run_id)
+        session.delete(old)
+        session.commit()
+        _mk_run(session, date(2026, 8, 11), created_at=t2)  # a NEW run for the SAME as_of
+        session.commit()
+
+    with Session(engine) as session:
+        row = session.get(NextSessionManifest, manifest_id)
+        disclosure = compass.basis_disclosure(session, row)
+        assert disclosure["status"] == "rebuilt"
+        assert row.source_run_id == before["source_run_id"]  # never rebound to the new run
+        assert row.content_hash == before["content_hash"]
+        assert row.manifest_hash == before["manifest_hash"]
+        assert row.version == before["version"]
+        assert row.available_at_utc == before["available_at_utc"]
+        assert row.prospective_eligible == before["prospective_eligible"]
+
+
+# --- TC-5 (iter-7 lesson): degenerate orphan -- no replacement run at all -- honest "unavailable" -
+
+
+def test_tc5_degenerate_orphan_no_replacement_run_reports_unavailable_never_raises(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 8, 5), created_at=datetime(2026, 8, 5, 20, 0, tzinfo=timezone.utc))
+        session.commit()
+        run_id = run.id
+        manifest = _mk_manifest(session, run)
+        session.commit()
+        manifest_id = manifest.id
+
+    with Session(engine) as session:
+        old = session.get(ScannerRun, run_id)
+        session.delete(old)
+        session.commit()
+        # deliberately NO replacement run for this as_of -- mirrors the real 2026-08-05 orphan (2
+        # manifests, 0 surviving source runs, verified 2026-08-21).
+
+    with Session(engine) as session:
+        row = session.get(NextSessionManifest, manifest_id)
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+
+    assert disclosure == {
+        "status": "unavailable",
+        "detail": "the underlying scanner run for this as-of is no longer stored",
+    }
+    assert disclosure["status"] not in ("available", "rebuilt")  # never fabricated
+
+
+# --- TC-6: id-reuse trap -- same numeric id, later created_at -- still `rebuilt`, never `original` -
+
+
+def test_tc6_id_reuse_trap_still_reports_rebuilt_not_original(engine):
+    t1 = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)
+    t2 = datetime(2026, 8, 22, 9, 0, tzinfo=timezone.utc)
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 8, 11), created_at=t1)
+        session.commit()
+        run_id = run.id
+        manifest = _mk_manifest(session, run)
+        session.commit()
+        manifest_id = manifest.id
+        before_source_run_id = manifest.source_run_id
+        before_content_hash = manifest.content_hash
+        before_manifest_hash = manifest.manifest_hash
+
+    with Session(engine) as session:
+        old = session.get(ScannerRun, run_id)
+        session.delete(old)
+        session.commit()
+        # explicitly REUSE the same numeric id N -- scanner_runs.id is a plain SQLite rowid alias (no
+        # AUTOINCREMENT, no sqlite_sequence), so a real delete/recreate can land here incidentally
+        # (docs/goal.md J-11 step 11). Constructed directly/deterministically rather than relying on
+        # SQLite's max(rowid)+1 timing.
+        reused = ScannerRun(
+            id=run_id, asof_date=date(2026, 8, 11), created_at=t2, provider="seed", benchmark="SPY",
+            regime_score=60.0, regime_label="Expansion", regime_components_json="[]",
+            breadth_above_50dma=55.0, breadth_above_200dma=60.0,
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(reused)
+        session.commit()
+
+    with Session(engine) as session:
+        current_run = session.get(ScannerRun, run_id)
+        assert current_run.id == run_id  # numeric id genuinely reused
+
+        row = session.get(NextSessionManifest, manifest_id)
+        assert row.source_run_id == run_id == before_source_run_id  # id equality alone -- unchanged
+        assert row.content_hash == before_content_hash
+        assert row.manifest_hash == before_manifest_hash
+
+        disclosure = compass.basis_disclosure(session, row)
+        # id equality is NOT treated as proof of original identity -- the frozen source_run_created_at
+        # (t1) differs from the reused row's actual created_at (t2), so this must read `rebuilt`.
+        assert disclosure["status"] == "rebuilt"
+        assert disclosure["status"] != "available"
+
+
+# --- TC-7 (iter-9 lesson): per-run identity consistency -- matching AND mismatched, as two cases ---
+
+
+def test_tc7_attempt_identity_consistency_matching_case(engine, cfg):
+    with Session(engine) as session:
+        frozen = j11_maintenance.freeze_attempt_identity(session, cfg)
+    matching_run_identity = frozen["engine_identity"]
+    assert j11_maintenance.check_attempt_identity_consistency(frozen, matching_run_identity) is True
+    # the bare-string form of frozen_identity is accepted identically to the dict form
+    assert j11_maintenance.check_attempt_identity_consistency(frozen["engine_identity"], matching_run_identity) is True
+
+
+def test_tc7_attempt_identity_consistency_mismatched_case(engine, cfg):
+    with Session(engine) as session:
+        frozen = j11_maintenance.freeze_attempt_identity(session, cfg)
+    mismatched_run_identity = "definitely-not-" + frozen["engine_identity"]
+    assert j11_maintenance.check_attempt_identity_consistency(frozen, mismatched_run_identity) is False
+    # fail-closed: a run with NO stamped identity (pre-stamping era / not yet persisted) is never
+    # silently treated as consistent.
+    assert j11_maintenance.check_attempt_identity_consistency(frozen, None) is False
+
+
+# --- freeze_attempt_identity: reproducible from the SAME config, and matches compute_engine_identity --
+
+
+def test_freeze_attempt_identity_matches_compute_engine_identity_and_is_reproducible(engine, cfg):
+    from app.engine.engine_identity import compute_engine_identity
+
+    with Session(engine) as session:
+        first = j11_maintenance.freeze_attempt_identity(session, cfg)
+        second = j11_maintenance.freeze_attempt_identity(session, cfg)
+
+    assert first["engine_identity"] == compute_engine_identity(cfg)
+    assert first["engine_identity"] == second["engine_identity"]  # same code+config -> same identity
+    assert first["config_subset_hash"] == second["config_subset_hash"]
+
+
+# --- capture_pre_reset_inventory: shape + counts on a small synthetic slice of the incident set -----
+
+
+def test_capture_pre_reset_inventory_shape_and_counts(engine):
+    covered_date = j11_maintenance.INCIDENT_DATES[0]
+    absent_date = j11_maintenance.INCIDENT_DATES[1]
+    with Session(engine) as session:
+        run = _mk_run(session, covered_date, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
+        session.commit()
+        _mk_manifest(session, run)
+        session.commit()
+
+    with Session(engine) as session:
+        inventory = j11_maintenance.capture_pre_reset_inventory(session)
+
+    assert inventory["incident_dates"] == [d.isoformat() for d in j11_maintenance.INCIDENT_DATES]
+    covered = inventory["per_date"][covered_date.isoformat()]
+    assert covered["scanner_run"]["present"] is True
+    assert len(covered["manifests"]) == 1
+    absent = inventory["per_date"][absent_date.isoformat()]
+    assert absent["scanner_run"]["present"] is False
+    assert absent["scanner_results_count"] == 0
+    assert absent["manifests"] == []
+    assert inventory["daily_prices"]["row_count"] == 0  # no DailyPrice rows in this tiny fixture
+    assert inventory["watchlist_count"] == 0
+    assert inventory["data_provider_runs_count"] == 0
+    assert "zero_write_proof" not in inventory  # the CLI script adds this, not the pure function itself
+
+
+def test_incident_dates_match_the_authoritative_removal_audit():
+    """Guards against a transcription slip in the literal 11-date list (docs/goal.md J-11, the incident
+    date set from `data_provider_runs` id=538's own cascade record)."""
+    expected = [
+        "2026-05-12", "2026-05-13", "2026-07-10", "2026-07-13", "2026-07-24", "2026-07-27",
+        "2026-08-03", "2026-08-05", "2026-08-10", "2026-08-11", "2026-08-12",
+    ]
+    assert [d.isoformat() for d in j11_maintenance.INCIDENT_DATES] == expected
```
