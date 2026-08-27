# Iteration diff (bounded)

Files changed: 4. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_stage_e_execute.py` (207 lines not shown)
- `apps/backend/tests/test_j11_stage_e_execute.py` (446 lines not shown)

```diff
diff --git a/apps/backend/app/engine/j11_stage_e_execute.py b/apps/backend/app/engine/j11_stage_e_execute.py
new file mode 100644
index 00000000..2c6197d0
--- /dev/null
+++ b/apps/backend/app/engine/j11_stage_e_execute.py
@@ -0,0 +1,601 @@
+"""app.engine.j11_stage_e_execute -- J-11 Stage E EXECUTION (goal-market-compass iter-20).
+
+`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED" (owner,
+2026-08-26) item 7 authorizes Stage E, unconditionally, once Stage D has succeeded (iteration 19 --
+`runs/goal-market-compass-iter-19/j11-stage-d-execute-outcome.json`: `executed: true`). Stage E is the
+GLOBAL create-once forward-return hole repair: fill every derivable `forward_returns` gap on the eleven
+Stage-D-regenerated incident-date runs AND on any retained (non-incident) run whose forward-return rows
+the original incident cascade deleted -- through the EXISTING canonical machinery only, with zero write
+to any table other than `forward_returns`.
+
+**The one write-scope risk this module exists to avoid (see the iteration-20 spec's BACKGROUND, and the
+plan's Alignment check, both independently confirmed by reading `forward_testing._backfill()` directly):**
+`forward_testing.backfill_forward_returns()` -- the WHOLE-DATABASE entry point -- delegates to `_backfill`,
+which, BEFORE inserting a single forward return, calls `scanner.run_scan` for any `walk_forward_asof_dates()`
+date lacking a `ScannerRun` (a `quarterly`, 30-year cadence grid independent of the scanner's own `monthly`
+snapshot schedule). Calling it here risks minting a `ScannerRun` OUTSIDE the eleven-date incident boundary
+as an undocumented side effect -- exactly what ruling item 7 forbids ("Stage E may not ... broaden into
+unrelated historical cleanup"). This module therefore calls ONLY
+`forward_testing.backfill_run_forward_returns(session, run, config)` -- the per-run, create-once,
+INSERT-only path that never touches `scanner_runs`/`scanner_results`/`*_scores` -- once per row currently
+in `scanner_runs`. `test_j11_stage_e_execute.py::test_tc3_module_never_references_backfill_forward_returns`
+and `::test_tc3_cli_script_never_references_backfill_forward_returns` prove this statically (AST-walked,
+not a docstring/code-review claim).
+
+Sequence:
+
+  1. Fresh, READ-ONLY preflight -- before any write: `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`
+     (REUSED directly, never reimplemented) re-verifies the `j11-incident-recovery` boundary is `active=1`
+     covering exactly `INCIDENT_DATES` and the live guard blocks all 11; `confirm_stage_d_runs_present_unrestamped`
+     re-derives, per incident date, that Stage D's OWN recorded run id is still the live row's id, still
+     stamped with Stage D's frozen `engine_identity`, and currently carries ZERO `ForwardReturn` rows;
+     `check_engine_identity_matches_stage_d` recomputes `engine_identity.compute_engine_identity(config)`
+     fresh and asserts it equals the value Stage D froze (per ruling item 2, a mismatch means the whole D-G
+     attempt has drifted and is incomplete -- STOP, never proceed under a new identity);
+     `confirm_manifests_unchanged` re-dumps `next_session_manifests` and diffs it against the SAME certified
+     baseline (`runs/goal-market-compass-iter-16/j11-stage-d-certified-baseline.json`) Stage D's own preflight
+     compared against -- transitively valid because Stage D's own post-execution mutation accounting already
+     proved manifests were unchanged THROUGH Stage D, and maintenance isolation (one controlled writer) means
+     nothing else could have touched them since. `stage_e_preflight_gate_verdict` combines all four into one
+     go/no-go: proceed ONLY if every check agrees.
+  2. The ONE authorized write sequence -- `execute_stage_e_repair_loop`: every row currently in `scanner_runs`
+     (the full retained-plus-Stage-D-rebuilt population), ascending `asof_date`, gets exactly one
+     `forward_testing.backfill_run_forward_returns(session, run, config)` call, inside ONE shared
+     `prices.prefilled_bar_cache(session, expected_symbols=<the resolved candidate pool>)` context (iter-19
+     audit finding B3: the columnar `_SymbolColumns` shape this loads into is ~3.3x more memory-efficient
+     than the lazy per-symbol `list[Bar]` path for a loop that -- given ~3,100+ runs spanning 30 years --
+     will eventually touch nearly every symbol in `daily_prices` regardless of which path is chosen; one
+     bulk streamed query beats thousands of small per-symbol ones on both memory and I/O). A B4-style hard
+     assertion proves the iterated row set is exactly the live `scanner_runs` table, never a caller-narrowed
+     subset.
+  3. Live, read-only re-verification of the three populations `docs/goal.md` step 5 names, by DIRECT QUERY
+     against `forward_returns` -- never merely asserted from the loop's own in-process diff
+     (`live_verify_three_populations`).
+  4. Post-execution mutation accounting (`build_stage_e_mutation_accounting`) -- proves
+     `changed_existing_tables` is a subset of exactly `{forward_returns}`, the 8 named out-of-scope tables
+     (`daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, `data_provider_runs`,
+     `watchlist`, `maintenance_boundaries`) show zero fingerprint change, `next_session_manifests` stays
+     byte-identical, and the loop's self-reported total reconciles exactly against the live
+     `COUNT(*)` delta.
+
+Never touches (imports nothing from, calls nothing in): `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`,
+`data_manager.py`'s write paths, or `scanner.resolve_run`. Does not modify `forward_testing.py`, `scanner.py`,
+`prices.py`, `j11_maintenance.py`, `j11_stage_d.py`, or `j11_stage_d_execute.py` -- this module COMPOSES
+their existing functions as-is.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Any, Iterable, Optional
+
+from sqlalchemy import func
+from sqlmodel import Session, select
+
+from app.config import Config, get_config
+from app.engine import engine_identity
+from app.engine import forward_testing
+from app.engine import j11_maintenance
+from app.engine import j11_schema_migration as migration
+from app.engine import j11_stage_d_execute as jsde
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.engine.prices import prefilled_bar_cache
+from app.engine.universe_screen import read_pool
+from app.models import DailyPrice, ForwardReturn, NextSessionManifest, ScannerRun
+
+# The ONE table this module's one authorized write may ever touch (ruling item 7: Stage E "may fill
+# derivable missing forward-return rows ... may not ... broaden into unrelated historical cleanup").
+STAGE_E_WRITE_TABLES: tuple[str, ...] = ("forward_returns",)
+
+# The 8 named tables the DoD requires proven at zero fingerprint change (TC-18) -- everything Stage E
+# reads but must never write, spelled out explicitly rather than derived, so a future schema addition
+# does not silently narrow this list.
+OUT_OF_SCOPE_TABLES: tuple[str, ...] = (
+    "daily_prices", "scanner_runs", "scanner_results", "sector_scores", "theme_scores",
+    "data_provider_runs", "watchlist", "maintenance_boundaries",
+)
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+def _count(session: Session, model: Any, **filters: Any) -> int:
+    """A column-projected `COUNT(*)` -- never an ORM hydration of the matched rows (AG-8). Mirrors
+    `j11_maintenance._count`'s idiom (not imported cross-module -- each j11_*.py module carries its own
+    trivial copy, the established convention in this file family)."""
+    stmt = select(func.count()).select_from(model)
+    for key, value in filters.items():
+        stmt = stmt.where(getattr(model, key) == value)
+    return int(session.scalar(stmt) or 0)
+
+
+# ================================================================================================
+# Step 1 -- fresh, read-only preflight (boundary/guard reuse + three Stage-E-specific checks)
+# ================================================================================================
+
+
+def confirm_stage_d_runs_present_unrestamped(
+    session: Session,
+    *,
+    expected_run_id_by_date: dict[str, int],
+    frozen_engine_identity: str,
+) -> dict:
+    """For every one of Stage D's 11 rebuilt incident dates, confirm the live `ScannerRun` row is
+    present, carries the SAME `id` Stage D's own recorded regeneration evidence assigned to that date
+    (proving it was never deleted/recreated since), carries the SAME frozen `engine_identity` Stage D
+    stamped, and currently has ZERO `ForwardReturn` rows (Stage E's own starting-state precondition).
+    Read-only -- never writes, never restamps."""
+    per_date: dict[str, dict] = {}
+    for date_str, expected_run_id in sorted(expected_run_id_by_date.items()):
+        one_date = date.fromisoformat(date_str)
+        row = session.exec(
+            select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
+            .where(ScannerRun.asof_date == one_date)
+        ).first()
+        present = row is not None
+        observed_id = int(row[0]) if present else None
+        observed_identity = row[2] if present else None
+        fr_count = _count(session, ForwardReturn, run_id=observed_id) if present else None
+        id_matches = present and observed_id == expected_run_id
+        identity_matches = present and observed_identity == frozen_engine_identity
+        zero_forward_returns = present and fr_count == 0
+        per_date[date_str] = {
+            "expected_run_id": expected_run_id,
+            "present": present,
+            "observed_run_id": observed_id,
+            "id_matches": id_matches,
+            "observed_engine_identity": observed_identity,
+            "identity_matches": identity_matches,
+            "observed_created_at": row[3].isoformat() if present and row[3] is not None else None,
+            "forward_return_count": fr_count,
+            "zero_forward_returns": zero_forward_returns,
+            "ok": present and id_matches and identity_matches and zero_forward_returns,
+        }
+    ok = bool(per_date) and all(v["ok"] for v in per_date.values())
+    return {"checked_at": _now_iso(), "per_date": per_date, "ok": ok}
+
+
+def check_engine_identity_matches_stage_d(fresh_identity: str, stage_d_frozen_identity: Optional[str]) -> dict:
+    """A fresh, honestly-stated (equal-or-not, either way) comparison of the LIVE recomputed
+    `engine_identity` against Stage D's frozen value. UNLIKE Stage D's own historical comparison (where
+    an equal value against an OLDER attempt was an expected non-failure), inequality HERE is a hard
+    blocker -- per ruling item 2, a drift since Stage D makes the whole D-G attempt incomplete."""
+    matches = stage_d_frozen_identity is not None and fresh_identity == stage_d_frozen_identity
+    return {
+        "checked_at": _now_iso(),
+        "fresh_engine_identity": fresh_identity,
+        "stage_d_frozen_engine_identity": stage_d_frozen_identity,
+        "matches": matches,
+        "ok": matches,
+    }
+
+
+def confirm_manifests_unchanged(engine: Any, *, certified_manifest_dump: list[dict]) -> dict:
+    """Fresh live dump of `next_session_manifests`, diffed against the SAME certified baseline dump
+    Stage D's own preflight compared against (`runs/goal-market-compass-iter-16/
+    j11-stage-d-certified-baseline.json`'s `manifest_dump`) -- valid transitively because Stage D's own
+    post-execution mutation accounting already proved zero manifest change THROUGH Stage D, and
+    maintenance isolation (one controlled writer, no boot warmup) means nothing else could have written
+    since. Reuses `j11_schema_migration.dump_table`/`diff_dumps` -- never a second comparison
+    implementation."""
+    live_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    diff = migration.diff_dumps(certified_manifest_dump, live_dump)
+    return {
+        "checked_at": _now_iso(),
+        "certified_row_count": len(certified_manifest_dump),
+        "live_row_count": len(live_dump),
+        "diff": diff,
+        "ok": diff["equal"],
+    }
+
+
+def stage_e_preflight_gate_verdict(
+    *, boundary_recheck: dict, runs_check: dict, identity_check: dict, manifest_check: dict,
+) -> dict:
+    """The single go/no-go decision for Stage E EXECUTION. Any one of the four checks failing means
+    `proceed: False`, and the caller MUST perform zero writes to any table."""
+    boundary_ok = bool(boundary_recheck.get("ok"))
+    runs_ok = bool(runs_check.get("ok"))
+    identity_ok = bool(identity_check.get("ok"))
+    manifest_ok = bool(manifest_check.get("ok"))
+    proceed = boundary_ok and runs_ok and identity_ok and manifest_ok
+
+    blocking_reasons: list[str] = []
+    if not boundary_ok:
+        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")
+    if not runs_ok:
+        blocking_reasons.append("stage_d_runs_not_present_unrestamped_and_zero_forward_returns")
+    if not identity_ok:
+        blocking_reasons.append("engine_identity_drifted_since_stage_d")
+    if not manifest_ok:
+        blocking_reasons.append("next_session_manifests_changed_since_stage_d")
+
+    return {
+        "generated_at": _now_iso(),
+        "proceed": proceed,
+        "boundary_ok": boundary_ok,
+        "runs_ok": runs_ok,
+        "identity_ok": identity_ok,
+        "manifest_ok": manifest_ok,
+        "blocking_reasons": blocking_reasons,
+    }
+
+
+# ================================================================================================
+# Step 2 -- pre/post captures reused by the CLI script for mutation accounting
+# ================================================================================================
+
+
+def capture_all_scanner_run_fingerprint(session: Session) -> dict:
+    """A full, column-projected (id, asof_date, engine_identity, created_at) snapshot of EVERY
+    `ScannerRun` row -- Stage E must never touch ANY of them (unlike Stage D's narrower legacy/null
+    population, Stage E's write is confined to `forward_returns` alone, so the WHOLE table must be
+    byte-unchanged). ~3,100+ rows is small and bounded (never a multi-million-row hydration -- AG-8),
+    mirroring `j11_stage_d_execute.capture_legacy_and_null_scanner_run_fingerprint`'s exact shape widened
+    to every row instead of a filtered subset."""
+    rows = session.exec(
+        select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
+        .order_by(ScannerRun.id)
+    ).all()
+    payload = [
+        {
+            "id": int(r[0]),
+            "asof_date": r[1].isoformat() if r[1] is not None else None,
+            "engine_identity": r[2],
+            "created_at": r[3].isoformat() if r[3] is not None else None,
+        }
+        for r in rows
+    ]
+    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
+    return {"captured_at": _now_iso(), "row_count": len(payload), "rows": payload, "fingerprint": fingerprint}
+
+
+def capture_retained_incident_hole_counts(session: Session, *, incident_run_ids: Iterable[int]) -> dict:
+    """Per-`run_id` counts of `ForwardReturn` rows whose `measured_date` lands on one of the 11 incident
+    dates but whose `run_id` is NOT one of Stage D's 11 rebuilt runs -- the "holes on retained runs"
+    population (b) `docs/goal.md` step 5 names, first sized in Stage B's pre-reset inventory. ONE grouped
+    scan (mirrors `j11_maintenance.capture_pre_reset_inventory`'s own `measured_into_counts` idiom -- a
+    single bounded aggregation, never a per-date or per-run repeated full-table scan)."""
+    excluded = set(incident_run_ids)
+    rows = session.exec(
+        select(ForwardReturn.run_id, func.count())
+        .where(ForwardReturn.measured_date.in_(INCIDENT_DATES))
+        .group_by(ForwardReturn.run_id)
+    ).all()
+    counts = {int(run_id): int(n) for run_id, n in rows if int(run_id) not in excluded}
+    return {
+        "captured_at": _now_iso(),
+        "per_run_id_counts": counts,
+        "total": sum(counts.values()),
+        "run_count": len(counts),
+    }
+
+
+# ================================================================================================
+# Step 3 -- the per-run write loop (the ONE authorized write sequence)
+# ================================================================================================
+
+
+def resolve_pool_symbols() -> set[str]:
+    """The candidate-pool symbol set, read from the SAME committed `universe_pool.csv` parser
+    `data_manager.py`'s own `_do_backfill`/`_persist_per_date_coverage_snapshots` already use for their
+    `prefilled_bar_cache(session, expected_symbols=pool_symbols)` call (`pool_symbols = {row["symbol"]
+    for row in read_pool()}`) -- a pure, offline, local file read (no network, no DB). A thin, separately
+    named wrapper so a test can inject a small synthetic pool instead of reading the real committed CSV."""
+    return {row["symbol"] for row in read_pool()}
+
+
+def execute_stage_e_repair_loop(
+    session: Session, config: Config, *, pool_symbols: Optional[set[str]] = None,
+) -> dict:
+    """The whole-attempt per-run loop: every row CURRENTLY in `scanner_runs` (ascending `asof_date`),
+    each getting exactly one `forward_testing.backfill_run_forward_returns(session, run, config)` call --
+    the create-once, INSERT-only path. NEVER calls or imports `forward_testing.backfill_forward_returns`
+    (the whole-database entry point -- see the module docstring). Runs inside ONE shared
+    `prices.prefilled_bar_cache(session, expected_symbols=<resolved pool>)` context so every symbol's
+    price series loads at most once for the whole loop, however many of the ~3,100+ runs touch it.
+
+    B4-style hard assertion: the iterated row set is exactly the live `scanner_runs` table at the moment
+    the loop starts (never a caller-narrowed subset) -- a plain `COUNT(*)` compared against the fetched
+    row count, both read from the same open session before the loop begins."""
+    live_total = _count(session, ScannerRun)
+    runs = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date)).all()
+    if len(runs) != live_total:
+        raise RuntimeError(
+            f"execute_stage_e_repair_loop: fetched {len(runs)} ScannerRun rows but a fresh COUNT(*) on "
+            f"the same session reports {live_total} -- refusing to proceed on an inconsistent row set "
+            "(B4 hard assertion; this loop must always receive exactly the live scanner_runs table)."
+        )
+
+    incident_date_set = set(INCIDENT_DATES)
+    symbols = pool_symbols if pool_symbols is not None else resolve_pool_symbols()
+
+    per_run_results: list[dict] = []
+    with prefilled_bar_cache(session, expected_symbols=symbols):
+        for run in runs:
+            result = forward_testing.backfill_run_forward_returns(session, run, config)
+            classification = "rebuilt_incident_run" if run.asof_date in incident_date_set else "retained_run"
+            per_run_results.append({**result, "classification": classification})
+
+    total_inserted = sum(r["rows_inserted"] for r in per_run_results)
+    incident_inserted = sum(r["rows_inserted"] for r in per_run_results if r["classification"] == "rebuilt_incident_run")
+    retained_inserted = sum(r["rows_inserted"] for r in per_run_results if r["classification"] == "retained_run")
+    return {
+        "generated_at": _now_iso(),
+        "total_runs_processed": len(per_run_results),
+        "total_rows_inserted": total_inserted,
+        "rows_inserted_on_rebuilt_incident_runs": incident_inserted,
+        "rows_inserted_on_retained_runs": retained_inserted,
+        "per_run_results": per_run_results,
+    }
+
+
+# ================================================================================================
+# Step 4 -- live, read-only re-verification of the three named populations
+# ================================================================================================
+
+
+def live_verify_three_populations(
+    session: Session,
+    *,
+    incident_run_ids: list[int],
+    pre_retained_hole_counts_by_run: dict[int, int],
+) -> dict:
+    """Live, read-only re-derivation of the three populations `docs/goal.md` step 5 names, by DIRECT
+    query against `forward_returns` -- never merely asserted from the write loop's own in-process diff
+    (DoD: "proven by live read-only query, not asserted from a diff").
+
+    (a) rows now present for the 11 Stage-D-rebuilt runs (pre-Stage-E count was proven zero by the
+        preflight gate, so `post` IS the newly-inserted count).
+    (b) rows on retained (non-incident) runs whose `measured_date` lands on an incident date --
+        never decreases from its pre-Stage-E per-run value (TC-6).
+    (c) the not-yet-mature population: two live structural proofs that no immature combination was ever
+        fabricated -- no stored `measured_date` exceeds the latest stored `daily_prices` date (a
+        `ForwardReturn` can only ever be measured against an already-stored bar), and the run with the
+        single LATEST `asof_date` in the whole table (the run with the least, often zero, observable
+        post-snapshot history) carries no MORE forward-return rows than its own live-computed
+        observable-horizon ceiling allows."""
+    incident_ids = set(incident_run_ids)
+
+    post_a_rows = session.exec(
+        select(ForwardReturn.run_id, func.count())
+        .where(ForwardReturn.run_id.in_(incident_run_ids))
+        .group_by(ForwardReturn.run_id)
+    ).all()
+    post_a_counts = {int(run_id): int(n) for run_id, n in post_a_rows}
+    population_a = {
+        str(rid): {"pre": 0, "post": post_a_counts.get(rid, 0), "newly_inserted": post_a_counts.get(rid, 0)}
+        for rid in incident_run_ids
+    }
+    population_a_total_newly_inserted = sum(v["newly_inserted"] for v in population_a.values())
+
+    post_b_rows = session.exec(
+        select(ForwardReturn.run_id, func.count())
+        .where(ForwardReturn.measured_date.in_(INCIDENT_DATES))
+        .group_by(ForwardReturn.run_id)
+    ).all()
+    post_b_counts = {int(run_id): int(n) for run_id, n in post_b_rows if int(run_id) not in incident_ids}
+    never_decreased = all(
+        post_b_counts.get(run_id, 0) >= pre_count for run_id, pre_count in pre_retained_hole_counts_by_run.items()
+    )
+    population_b_total_pre = sum(pre_retained_hole_counts_by_run.values())
+    population_b_total_post = sum(post_b_counts.values())
+
+    max_measured_date = session.exec(select(func.max(ForwardReturn.measured_date))).first()
+    max_measured_date = max_measured_date[0] if isinstance(max_measured_date, tuple) else max_measured_date
+    max_price_date = session.exec(select(func.max(DailyPrice.date))).first()
+    max_price_date = max_price_date[0] if isinstance(max_price_date, tuple) else max_price_date
+    no_row_beyond_stored_prices = (
+        max_measured_date is None or max_price_date is None or max_measured_date <= max_price_date
+    )
+
... [diff_bound] apps/backend/app/engine/j11_stage_e_execute.py: 207 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_stage_e_execute.py b/apps/backend/scripts/run_j11_stage_e_execute.py
new file mode 100644
index 00000000..be9967e4
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_e_execute.py
@@ -0,0 +1,379 @@
+"""goal-market-compass iter-20 -- J-11 Stage E EXECUTION: the ONE owner-authorized live, global,
+create-once forward-return hole repair over the retained + Stage-D-rebuilt `scanner_runs` population
+(`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED", owner
+2026-08-26, item 7 -- authorized unconditionally following a successful Stage D regeneration; iteration
+19 already executed and independently-evaluator-verified Stage D).
+
+Mirrors `run_j11_stage_d_execute.py`'s idiom exactly: NO database interaction of any kind, not even a
+read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the write so a mid-run crash
+still leaves a forensic trail; the completion/outcome marker is written ONLY after full post-execution
+verification completes (whichever of the two honest terminal states -- `STAGE E COMPLETE: YES` or
+`STAGE E COMPLETE: NO` -- that verification proves). Sequence:
+
+  1. Fresh, READ-ONLY preflight: boundary/guard re-check (`j11_stage_d_execute.
+     recheck_maintenance_boundary_and_guard`, REUSED directly -- never reimplemented), the 11
+     Stage-D-rebuilt runs present/unrestamped/zero-`ForwardReturn` check, a fresh `engine_identity`
+     equality check against Stage D's frozen value, and a `next_session_manifests` unchanged check
+     against the same certified baseline Stage D's own preflight used -- combined into ONE execution
+     gate. STOPS here (zero writes of any kind) unless the gate's `proceed` is True.
+  2. Pre-write captures for mutation accounting (full table sweep, the full `scanner_runs` fingerprint,
+     `daily_prices`/`data_provider_runs`/`watchlist`/`maintenance_boundaries`/`next_session_manifests`
+     snapshots, the retained-run incident-hole population count, and the `forward_returns` row count).
+  3. THE per-run write loop (`j11_stage_e_execute.execute_stage_e_repair_loop`) over EVERY row currently
+     in `scanner_runs`, ascending `asof_date` -- the ONE authorized write sequence, calling ONLY
+     `forward_testing.backfill_run_forward_returns` (never `backfill_forward_returns`, the whole-database
+     entry point -- see the module docstring).
+  4. Live, read-only re-verification of the three named populations, directly against `forward_returns`.
+  5. Post-execution mutation accounting, proving every out-of-scope table shows zero fingerprint change
+     and the `forward_returns` delta reconciles exactly with the loop's own self-reported total.
+  6. The final outcome, written UNCONDITIONALLY as the LAST evidence artifact -- Stage E's own contract
+     defines TWO honest terminal states (`YES`/`NO`), and BOTH require full evidence preserved
+     (docs/goal.md item 14) -- never a bare non-zero exit with no persisted outcome record.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_e_execute.py \\
+        --confirm \\
+        --evidence-dir runs/goal-market-compass-iter-20
+
+Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
+non-zero. `--evidence-dir` is REQUIRED and has no implicit default (mirrors every other J-11
+evidence-writing script -- an omitted flag must never fall back to overwriting a committed evidence
+directory).
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from pathlib import Path
+from typing import Optional
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
+from app.engine import engine_identity  # noqa: E402
+from app.engine import j11_maintenance  # noqa: E402
+from app.engine import j11_schema_migration as migration  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.engine import j11_stage_d_execute as jsde  # noqa: E402
+from app.engine import j11_stage_e_execute as jsee  # noqa: E402
+from app.models import DataProviderRun, ForwardReturn, MaintenanceBoundary, NextSessionManifest, Watchlist  # noqa: E402
+
+DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-frozen-identity.json"
+)
+DEFAULT_STAGE_D_REGENERATION_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-regeneration.json"
+)
+DEFAULT_CERTIFIED_BASELINE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
+)
+
+OUTPUT_FILENAMES = (
+    "j11-stage-e-execute-db-file-true-start.json",
+    "j11-stage-e-execute-boundary-recheck.json",
+    "j11-stage-e-execute-runs-check.json",
+    "j11-stage-e-execute-identity-comparison.json",
+    "j11-stage-e-execute-manifest-check.json",
+    "j11-stage-e-execute-preflight-gate.json",
+    "j11-stage-e-execute-repair-loop.json",
+    "j11-stage-e-execute-population-report.json",
+    "j11-stage-e-execute-memory-check.json",
+    "j11-stage-e-execute-mutation-accounting.json",
+    "j11-stage-e-execute-outcome.json",
+    "j11-stage-e-execute-db-file-true-end.json",
+)
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
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
+    """Mirrors the SAME collision guard `run_j11_stage_d_execute.py` uses -- a pure filesystem check, no
+    database interaction."""
+    return [name for name in filenames if (evidence_dir / name).exists()]
+
+
+def _load_json(path: Path) -> Optional[dict]:
+    """Loads one historical evidence artifact. Never raises on a missing/malformed file -- an absent
+    cross-iteration artifact is recorded honestly as `None`, never fabricated and never a crash."""
+    if not path.exists():
+        return None
+    try:
+        return json.loads(path.read_text())
+    except (OSError, json.JSONDecodeError):
+        return None
+
+
+def _load_stage_d_frozen_identity(path: Path) -> Optional[str]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return None
+    value = payload.get("engine_identity")
+    return value if isinstance(value, str) else None
+
+
+def _load_expected_run_id_by_date(path: Path) -> dict[str, int]:
+    """`{iso_date: run_id}` from Stage D's own recorded regeneration evidence
+    (`per_date_results[*].date`/`.run_id`) -- never a fresh hardcoded literal. An absent/malformed file
+    yields an empty mapping (the runs-check then honestly reports every date as `present: False` and the
+    gate refuses to proceed -- fail closed, never fabricated)."""
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return {}
+    entries = payload.get("per_date_results")
+    if not isinstance(entries, list):
+        return {}
+    out: dict[str, int] = {}
+    for entry in entries:
+        if isinstance(entry, dict) and isinstance(entry.get("date"), str) and isinstance(entry.get("run_id"), int):
+            out[entry["date"]] = entry["run_id"]
+    return out
+
+
+def _load_certified_manifest_dump(path: Path) -> list[dict]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return []
+    dump = payload.get("manifest_dump")
+    return dump if isinstance(dump, list) else []
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
+    )
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches the database not at all and exits non-zero.",
+    )
+    parser.add_argument("--stage-d-frozen-identity-path", type=Path, default=DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH)
+    parser.add_argument("--stage-d-regeneration-path", type=Path, default=DEFAULT_STAGE_D_REGENERATION_PATH)
+    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is the ONE owner-authorized live Stage E write "
+            "this iteration -- docs/goal.md J-11 step 11's Stage D-through-G OWNER RULING, item 7). No "
+            "database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. No database interaction, not even a "
+            "read, has occurred, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    evidence_dir: Path = args.evidence_dir
+    colliding = _refuse_if_evidence_files_exist(evidence_dir, OUTPUT_FILENAMES)
+    if colliding:
+        print(
+            f"refusing to run: --evidence-dir {evidence_dir} already contains {colliding} -- this looks "
+            "like a re-run pointed at an already-populated evidence folder rather than a fresh one. No "
+            "database interaction, not even a read, has occurred, and no existing file has been touched.",
+            file=sys.stderr,
+        )
+        return 2
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    print(f"database: {resolved_url}", file=sys.stderr)
+
+    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it ---
+    db_file_true_start = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-e-execute-db-file-true-start.json", db_file_true_start)
+
+    engine = get_engine()  # the SAME pooled writable engine the real backend uses.
+
+    stage_d_frozen_identity = _load_stage_d_frozen_identity(args.stage_d_frozen_identity_path)
+    expected_run_id_by_date = _load_expected_run_id_by_date(args.stage_d_regeneration_path)
+    certified_manifest_dump = _load_certified_manifest_dump(args.certified_baseline_path)
+
+    def _stop(reason: str, preflight_gate: dict, boundary_recheck: "dict | None" = None) -> int:
+        outcome = jsee.stage_e_execution_outcome(
+            preflight_gate=preflight_gate, repair_loop_result=None,
+            population_verification=None, mutation_accounting=None,
+        )
+        _write_json(evidence_dir / "j11-stage-e-execute-outcome.json", outcome)
+        db_file_true_end = jsc.db_file_fingerprint(db_path)
+        _write_json(evidence_dir / "j11-stage-e-execute-db-file-true-end.json", db_file_true_end)
+        print(f"STOP before any write: {reason}", file=sys.stderr)
+        _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
+        return 1
+
+    # === Step 1: fresh, read-only preflight (boundary/guard + Stage-E-specific checks) ================
+    with Session(engine) as session:
+        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
+    _write_json(evidence_dir / "j11-stage-e-execute-boundary-recheck.json", boundary_recheck)
+    print(
+        f"boundary/guard recheck: ok={boundary_recheck['ok']} "
+        f"all_dates_blocked={boundary_recheck['all_dates_blocked']}",
+        file=sys.stderr,
+    )
+
+    with Session(engine) as session:
+        runs_check = jsee.confirm_stage_d_runs_present_unrestamped(
+            session,
+            expected_run_id_by_date=expected_run_id_by_date,
+            frozen_engine_identity=stage_d_frozen_identity or "",
+        )
+    _write_json(evidence_dir / "j11-stage-e-execute-runs-check.json", runs_check)
+    print(f"Stage D runs check: ok={runs_check['ok']}", file=sys.stderr)
+
+    fresh_identity = engine_identity.compute_engine_identity(cfg)
+    identity_check = jsee.check_engine_identity_matches_stage_d(fresh_identity, stage_d_frozen_identity)
+    _write_json(evidence_dir / "j11-stage-e-execute-identity-comparison.json", identity_check)
+    print(f"engine_identity check: ok={identity_check['ok']} fresh={fresh_identity}", file=sys.stderr)
+
+    manifest_check = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=certified_manifest_dump)
+    _write_json(evidence_dir / "j11-stage-e-execute-manifest-check.json", manifest_check)
+    print(f"manifest check: ok={manifest_check['ok']}", file=sys.stderr)
+
+    preflight_gate = jsee.stage_e_preflight_gate_verdict(
+        boundary_recheck=boundary_recheck, runs_check=runs_check,
+        identity_check=identity_check, manifest_check=manifest_check,
+    )
+    _write_json(evidence_dir / "j11-stage-e-execute-preflight-gate.json", preflight_gate)
+    print(f"preflight gate: proceed={preflight_gate['proceed']} reasons={preflight_gate['blocking_reasons']}", file=sys.stderr)
+
+    if not preflight_gate["proceed"]:
+        return _stop("preflight gate did not proceed", preflight_gate, boundary_recheck)
+
+    incident_run_ids = sorted(expected_run_id_by_date.values())
+
+    # === Step 2: pre-write captures ====================================================================
+    with Session(engine) as session:
+        pre_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
+        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        pre_all_scanner_run_fp = jsee.capture_all_scanner_run_fingerprint(session)
+        pre_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+        pre_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
+        pre_retained_hole_counts = jsee.capture_retained_incident_hole_counts(
+            session, incident_run_ids=incident_run_ids,
+        )
+        pre_forward_returns_count = int(
+            session.scalar(select(func.count()).select_from(ForwardReturn)) or 0
+        )
+
+    print(
+        f"pre-write captures done: scanner_runs={pre_all_scanner_run_fp['row_count']} "
+        f"forward_returns={pre_forward_returns_count} retained_hole_runs={pre_retained_hole_counts['run_count']}",
+        file=sys.stderr,
+    )
+
+    # === Step 3: THE per-run write loop -- the ONE authorized write sequence ==========================
+    with Session(engine) as session:
+        repair_loop_result = jsee.execute_stage_e_repair_loop(session, cfg)
+    _write_json(evidence_dir / "j11-stage-e-execute-repair-loop.json", repair_loop_result)
+    print(
+        f"repair loop: runs_processed={repair_loop_result['total_runs_processed']} "
+        f"total_inserted={repair_loop_result['total_rows_inserted']} "
+        f"incident={repair_loop_result['rows_inserted_on_rebuilt_incident_runs']} "
+        f"retained={repair_loop_result['rows_inserted_on_retained_runs']}",
+        file=sys.stderr,
+    )
+
+    vm_peak_kb = jsee.read_process_vm_peak_kb()
+    memory_check = jsee.build_memory_check(vm_peak_kb=vm_peak_kb, memory_cap_mb=cfg.server.memory_cap_mb)
+    _write_json(evidence_dir / "j11-stage-e-execute-memory-check.json", memory_check)
+    print(f"memory check: vm_peak_mb={memory_check['vm_peak_mb']} within_cap={memory_check['within_cap']}", file=sys.stderr)
+
+    # === Step 4: live, read-only re-verification of the three named populations =======================
+    with Session(engine) as session:
+        population_report = jsee.live_verify_three_populations(
+            session, incident_run_ids=incident_run_ids,
+            pre_retained_hole_counts_by_run=pre_retained_hole_counts["per_run_id_counts"],
+        )
+    _write_json(evidence_dir / "j11-stage-e-execute-population-report.json", population_report)
+    print(f"population report: all_checks_pass={population_report['all_checks_pass']}", file=sys.stderr)
+
+    # === Step 5: post-write captures + mutation accounting =============================================
+    with Session(engine) as session:
+        post_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
+        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        post_all_scanner_run_fp = jsee.capture_all_scanner_run_fingerprint(session)
+        post_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+        post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
+        post_forward_returns_count = int(
+            session.scalar(select(func.count()).select_from(ForwardReturn)) or 0
+        )
+
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-e-execute-db-file-true-end.json", db_file_true_end)
+
+    mutation_accounting = jsee.build_stage_e_mutation_accounting(
+        pre_full_table_sweep=pre_full_table_sweep, post_full_table_sweep=post_full_table_sweep,
+        pre_manifest_dump=pre_manifest_dump, post_manifest_dump=post_manifest_dump,
+        pre_all_scanner_run_fingerprint=pre_all_scanner_run_fp, post_all_scanner_run_fingerprint=post_all_scanner_run_fp,
+        pre_daily_prices=pre_daily_prices, post_daily_prices=post_daily_prices,
+        pre_provider_runs=pre_provider_runs, post_provider_runs=post_provider_runs,
+        pre_watchlist=pre_watchlist, post_watchlist=post_watchlist,
+        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump, post_maintenance_boundary_dump=post_maintenance_boundary_dump,
+        pre_forward_returns_count=pre_forward_returns_count, post_forward_returns_count=post_forward_returns_count,
+        self_reported_total_inserted=repair_loop_result["total_rows_inserted"],
+        db_file_true_start=db_file_true_start, db_file_true_end=db_file_true_end,
+    )
+    _write_json(evidence_dir / "j11-stage-e-execute-mutation-accounting.json", mutation_accounting)
+    print(f"mutation accounting: all_checks_pass={mutation_accounting['all_checks_pass']}", file=sys.stderr)
+    if not mutation_accounting["all_checks_pass"]:
+        failing = [k for k, v in mutation_accounting["checks"].items() if not v]
+        print(f"FAILING CHECKS: {failing}", file=sys.stderr)
+
+    # === Final outcome -- written UNCONDITIONALLY, whichever of the two honest terminal states =========
+    outcome = jsee.stage_e_execution_outcome(
+        preflight_gate=preflight_gate, repair_loop_result=repair_loop_result,
+        population_verification=population_report, mutation_accounting=mutation_accounting,
+    )
+    _write_json(evidence_dir / "j11-stage-e-execute-outcome.json", outcome)
+    _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
+    return 0 if outcome["executed"] else 1
+
+
+def _print_terminal_lines(outcome: dict, *, boundary_recheck: "dict | None") -> None:
+    executed = bool(outcome.get("executed"))
+    boundary_active = boundary_recheck.get("boundary_active") if boundary_recheck else True
+    guard_armed = boundary_recheck.get("all_dates_blocked") if boundary_recheck else True
+    print("J-11 STAGE D EXECUTED: YES", file=sys.stderr)
+    print(f"J-11 STAGE E COMPLETE: {'YES' if executed else 'NO'}", file=sys.stderr)
+    print("J-11 STAGE F COMPLETE: NO", file=sys.stderr)
+    print("J-11 STAGE G VERIFIED: NO", file=sys.stderr)
+    print("J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE", file=sys.stderr)
+    print(f"J-11 MAINTENANCE BOUNDARY: {'ACTIVE' if boundary_active else 'NOT ACTIVE'}", file=sys.stderr)
+    print(f"J-11 LIVE PRE-BOOT GUARD: {'ARMED' if guard_armed else 'NOT ARMED'}", file=sys.stderr)
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_stage_e_execute.py b/apps/backend/tests/test_j11_stage_e_execute.py
new file mode 100644
index 00000000..00945e7f
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_e_execute.py
@@ -0,0 +1,840 @@
+"""goal-market-compass iter-20 -- J-11 Stage E EXECUTION tests (TC-1 through TC-9, TC-12, TC-15, TC-16
+from the phase spec's TESTING REQUIREMENTS; TC-10/TC-11/TC-13/TC-14/TC-17/TC-18/TC-19/TC-20 live in the
+CLI-script test file / are proven by grep in the dev handoff).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
+pattern `test_j11_stage_d_execute.py` uses, never `loaded_engine` and never `apps/backend/data/trendora.db`.
+
+`scanner.run_scan`/`compute_run_payload` are NOT exercised here -- fixture `ScannerRun`/`ScannerResult`
+rows are built directly (mirroring `test_j11_stage_d_execute.py`'s `_mk_run` idiom), so
+`forward_testing.backfill_run_forward_returns` runs against real, small, hand-built price/snapshot data.
+"""
+from __future__ import annotations
+
+import ast
+import json
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.config import load_config
+from app.engine import j11_stage_e_execute as jsee
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import DailyPrice, ForwardReturn, MaintenanceBoundary, NextSessionManifest, ScannerResult, ScannerRun
+
+pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+MODULE_PATH = BACKEND_DIR / "app" / "engine" / "j11_stage_e_execute.py"
+CLI_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_e_execute.py"
+
+
+@pytest.fixture()
+def engine():
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
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+# --- shared fixture helpers -----------------------------------------------------------------------
+
+
+def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = "stub-identity") -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=55.0, regime_label="Expansion", regime_components_json="[]",
+        breadth_above_50dma=50.0, breadth_above_200dma=55.0,
+        new_high_low_json="{}", candidate_counts_json="{}",
+        engine_identity=engine_identity_value,
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _mk_result(session: Session, run: ScannerRun, ticker: str, rank: int = 1) -> ScannerResult:
+    result = ScannerResult(
+        run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
+        leadership_score=50.0, leadership_bucket="Neutral",
+        entry_quality_score=50.0, entry_quality_bucket="Neutral",
+        risk_score=50.0, risk_bucket="Neutral", setup_status="None", rank=rank,
+        record_json="{}",
+    )
+    session.add(result)
+    session.flush()
+    return result
+
+
+def _mk_prices(session: Session, symbol: str, start: date, n_days: int, *, price: float = 100.0) -> None:
+    """N consecutive calendar-day bars (fine for these fixture tests -- no trading-calendar gaps needed;
+    forward_testing counts DISTINCT stored dates, not real trading-day semantics)."""
+    d = start
+    for i in range(n_days):
+        session.add(DailyPrice(symbol=symbol, date=d, open=price, high=price, low=price, close=price, volume=1000))
+        d = d + timedelta(days=1)
+    session.flush()
+
+
+def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
+    manifest = NextSessionManifest(
+        as_of=run.asof_date, version=version, source_run_id=run.id,
+        session_delta_json="{}", narrative_json="{}", selection_json="{}",
+        content_hash="stub-content-hash", created_at=datetime.now(timezone.utc),
+        mode="at_ingest", frozen=True,
+        generation_json=json.dumps({"producer": "ingest_finalize", "engine_identity": "stub-engine-identity"}),
+        engine_identity="stub-engine-identity", manifest_hash="stub-manifest-hash",
+        available_at_utc=datetime.now(timezone.utc), prospective_eligible=True,
+    )
+    session.add(manifest)
+    session.flush()
+    return manifest
+
+
+LOOP_DATES = INCIDENT_DATES[:2]  # a 2-date real-incident-date subset
+
+
+# =======================================================================================================
+# TC-3 -- static/import-level proof: backfill_forward_returns is NEVER imported or called
+# =======================================================================================================
+
+
+def _collect_all_identifiers(tree: ast.AST) -> set[str]:
+    """Every `Name.id`, `Attribute.attr`, and `alias.name`/`alias.asname` in the file -- covers BOTH a
+    direct `from ... import backfill_forward_returns` AND a `forward_testing.backfill_forward_returns(...)`
+    attribute-call form. Deliberately walks the WHOLE tree, not just top-level `Import` nodes -- an
+    attribute access is not an import statement."""
+    names: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Name):
+            names.add(node.id)
+        elif isinstance(node, ast.Attribute):
+            names.add(node.attr)
+        elif isinstance(node, (ast.Import, ast.ImportFrom)):
+            for alias in node.names:
+                names.add(alias.name)
+                if alias.asname:
+                    names.add(alias.asname)
+    return names
+
+
+def test_tc3_module_never_references_backfill_forward_returns():
+    tree = ast.parse(MODULE_PATH.read_text())
+    identifiers = _collect_all_identifiers(tree)
+    assert "backfill_forward_returns" not in identifiers
+    # sanity: the module DOES reference the correct, per-run, create-once sibling function
+    assert "backfill_run_forward_returns" in identifiers
+
+
+def test_tc3_cli_script_never_references_backfill_forward_returns():
+    tree = ast.parse(CLI_SCRIPT_PATH.read_text())
+    identifiers = _collect_all_identifiers(tree)
+    assert "backfill_forward_returns" not in identifiers
+
+
+# =======================================================================================================
+# TC-20 -- static proof: zero network-capable call appears anywhere in the diff
+# =======================================================================================================
+
+
+_NETWORK_TOKENS = ("requests", "httpx", "urllib", "socket", "yfinance", "aiohttp", "http.client")
+
+
+def test_tc20_module_imports_no_network_capable_library():
+    tree = ast.parse(MODULE_PATH.read_text())
+    imported_roots = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                imported_roots.add(alias.name.split(".")[0])
+        elif isinstance(node, ast.ImportFrom) and node.module:
+            imported_roots.add(node.module.split(".")[0])
+    assert not (imported_roots & set(_NETWORK_TOKENS))
+
+
+def test_tc20_cli_script_imports_no_network_capable_library():
+    tree = ast.parse(CLI_SCRIPT_PATH.read_text())
+    imported_roots = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                imported_roots.add(alias.name.split(".")[0])
+        elif isinstance(node, ast.ImportFrom) and node.module:
+            imported_roots.add(node.module.split(".")[0])
+    assert not (imported_roots & set(_NETWORK_TOKENS))
+
+
+# =======================================================================================================
+# recheck reuse -- confirm the module reuses j11_stage_d_execute's function rather than reimplementing it
+# =======================================================================================================
+
+
+def test_reuses_stage_d_boundary_recheck_never_reimplements_it():
+    """Neither the module nor the CLI script may DEFINE a competing
+    `recheck_maintenance_boundary_and_guard` (that would be reimplementation), but the reused identifier
+    must be REFERENCED somewhere across the Stage E deliverable (module + CLI script) -- whichever file
+    actually calls into `j11_stage_d_execute`'s already-built function, per the plan's Alignment check."""
+    module_source = MODULE_PATH.read_text()
+    cli_source = CLI_SCRIPT_PATH.read_text()
+    assert "def recheck_maintenance_boundary_and_guard(" not in module_source
+    assert "def recheck_maintenance_boundary_and_guard(" not in cli_source
+
+    module_identifiers = _collect_all_identifiers(ast.parse(module_source))
+    cli_identifiers = _collect_all_identifiers(ast.parse(cli_source))
+    assert "recheck_maintenance_boundary_and_guard" in (module_identifiers | cli_identifiers)
+
+
+# =======================================================================================================
+# confirm_stage_d_runs_present_unrestamped
+# =======================================================================================================
+
+
+def test_runs_check_ok_when_present_matching_id_and_identity_and_zero_forward_returns(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="53d2ffd1...")
+        session.commit()
+        run_id = run.id
+
+    with Session(engine) as session:
+        result = jsee.confirm_stage_d_runs_present_unrestamped(
+            session,
+            expected_run_id_by_date={LOOP_DATES[0].isoformat(): run_id},
+            frozen_engine_identity="53d2ffd1...",
+        )
+    assert result["ok"] is True
+    entry = result["per_date"][LOOP_DATES[0].isoformat()]
+    assert entry["present"] is True
+    assert entry["id_matches"] is True
+    assert entry["identity_matches"] is True
+    assert entry["zero_forward_returns"] is True
+
+
+def test_runs_check_fails_when_run_missing(engine):
+    with Session(engine) as session:
+        result = jsee.confirm_stage_d_runs_present_unrestamped(
+            session,
+            expected_run_id_by_date={LOOP_DATES[0].isoformat(): 999},
+            frozen_engine_identity="53d2ffd1...",
+        )
+    assert result["ok"] is False
+    assert result["per_date"][LOOP_DATES[0].isoformat()]["present"] is False
+
+
+def test_runs_check_fails_when_id_does_not_match_expected(engine):
+    """A different id at the same asof_date than Stage D recorded -- the row was deleted and recreated
+    since Stage D, even if its engine_identity happens to match (the exact 'restamped' trap)."""
+    with Session(engine) as session:
+        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="53d2ffd1...")
+        session.commit()
+        real_id = run.id
+
+    with Session(engine) as session:
+        result = jsee.confirm_stage_d_runs_present_unrestamped(
+            session,
+            expected_run_id_by_date={LOOP_DATES[0].isoformat(): real_id + 1000},  # wrong expected id
+            frozen_engine_identity="53d2ffd1...",
+        )
+    assert result["ok"] is False
+    assert result["per_date"][LOOP_DATES[0].isoformat()]["id_matches"] is False
+
+
+def test_runs_check_fails_when_identity_does_not_match(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="some-other-identity")
+        session.commit()
+        run_id = run.id
+
+    with Session(engine) as session:
+        result = jsee.confirm_stage_d_runs_present_unrestamped(
+            session,
+            expected_run_id_by_date={LOOP_DATES[0].isoformat(): run_id},
+            frozen_engine_identity="53d2ffd1...",  # does not match the row's stamped identity
+        )
+    assert result["ok"] is False
+    entry = result["per_date"][LOOP_DATES[0].isoformat()]
+    assert entry["present"] is True
+    assert entry["id_matches"] is True
+    assert entry["identity_matches"] is False
+
+
+def test_runs_check_fails_when_forward_return_already_present(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="53d2ffd1...")
+        session.flush()
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="AAA", horizon=5, asof_date=LOOP_DATES[0],
+            entry_close=100.0, measured_date=LOOP_DATES[0] + timedelta(days=10), realized_return=0.01,
+        ))
+        session.commit()
+        run_id = run.id
+
+    with Session(engine) as session:
+        result = jsee.confirm_stage_d_runs_present_unrestamped(
+            session,
+            expected_run_id_by_date={LOOP_DATES[0].isoformat(): run_id},
+            frozen_engine_identity="53d2ffd1...",
+        )
+    assert result["ok"] is False
+    entry = result["per_date"][LOOP_DATES[0].isoformat()]
+    assert entry["zero_forward_returns"] is False
+    assert entry["forward_return_count"] == 1
+
+
+# =======================================================================================================
+# check_engine_identity_matches_stage_d
+# =======================================================================================================
+
+
+def test_identity_check_ok_when_equal():
+    result = jsee.check_engine_identity_matches_stage_d("abc123", "abc123")
+    assert result["ok"] is True
+    assert result["matches"] is True
+
+
+def test_identity_check_fails_when_different_stated_honestly_both_ways():
+    result = jsee.check_engine_identity_matches_stage_d("abc123", "def456")
+    assert result["ok"] is False
+    assert result["fresh_engine_identity"] == "abc123"
+    assert result["stage_d_frozen_engine_identity"] == "def456"
+
+
+def test_identity_check_fails_when_historical_value_missing():
+    result = jsee.check_engine_identity_matches_stage_d("abc123", None)
+    assert result["ok"] is False
+
+
+# =======================================================================================================
+# confirm_manifests_unchanged
+# =======================================================================================================
+
+
+def test_manifest_check_ok_when_live_dump_matches_certified(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2029, 12, 1))
+        _mk_manifest(session, run)
+        session.commit()
+
+    from app.engine import j11_schema_migration as migration
+    live_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+
+    result = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=live_dump)
+    assert result["ok"] is True
+    assert result["live_row_count"] == 1
+
+
+def test_manifest_check_fails_when_live_dump_diverges_from_certified(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2029, 12, 1))
+        _mk_manifest(session, run)
+        session.commit()
+
+    result = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=[])  # certified says 0 rows
+    assert result["ok"] is False
+    assert result["diff"]["equal"] is False
+
+
+# =======================================================================================================
+# stage_e_preflight_gate_verdict
+# =======================================================================================================
+
+
+@pytest.mark.parametrize(
+    "boundary_ok,runs_ok,identity_ok,manifest_ok,expected",
+    [
+        (True, True, True, True, True),
+        (False, True, True, True, False),
+        (True, False, True, True, False),
+        (True, True, False, True, False),
+        (True, True, True, False, False),
+    ],
+)
+def test_preflight_gate_requires_all_four_checks(boundary_ok, runs_ok, identity_ok, manifest_ok, expected):
+    verdict = jsee.stage_e_preflight_gate_verdict(
+        boundary_recheck={"ok": boundary_ok}, runs_check={"ok": runs_ok},
+        identity_check={"ok": identity_ok}, manifest_check={"ok": manifest_ok},
+    )
+    assert verdict["proceed"] is expected
+    if not expected:
+        assert verdict["blocking_reasons"]
+
+
+# =======================================================================================================
+# TC-5, TC-6, TC-8 -- the three-population classification, TC-4/TC-7 -- byte-unchanged proofs
+# =======================================================================================================
+
+
+def test_tc5_tc8_repair_loop_fills_rebuilt_run_visits_retained_and_leaves_immature_absent(engine, cfg):
+    """A Stage-D-shaped fixture: one 'rebuilt incident' run (an INCIDENT_DATES member, zero ForwardReturn
+    rows to start), one RETAINED (non-incident) run, and the frontier (latest) run whose horizons are all
+    not-yet-mature. Reproduces TC-5 and TC-8 end-to-end; TC-6's retained-run REFILL is covered separately
+    by `test_tc6_retained_run_incident_dated_hole_is_refilled_and_reported_in_population_b`."""
+    incident_asof = LOOP_DATES[0]
+    retained_asof = incident_asof - timedelta(days=40)  # earlier -- a RETAINED (non-incident) run
+    frontier_asof = date(2030, 6, 1)  # the LATEST run in the fixture -- no post-snapshot bars at all
+
+    with Session(engine) as session:
+        # enough daily bars for AAA/SPY spanning both runs' as-of dates and forward windows
+        _mk_prices(session, "AAA", retained_asof - timedelta(days=5), 400)
+        _mk_prices(session, "SPY", retained_asof - timedelta(days=5), 400)
+
+        incident_run = _mk_run(session, incident_asof, engine_identity_value="53d2ffd1...")
... [diff_bound] apps/backend/tests/test_j11_stage_e_execute.py: 446 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_e_execute_cli_script.py b/apps/backend/tests/test_j11_stage_e_execute_cli_script.py
new file mode 100644
index 00000000..12f3c488
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_e_execute_cli_script.py
@@ -0,0 +1,391 @@
+"""goal-market-compass iter-20 -- J-11 Stage E EXECUTION CLI control-flow tests
+(`scripts/run_j11_stage_e_execute.py`), TC-10/TC-13/TC-14/TC-17/TC-18 plus the stop-before-write
+control-flow proofs.
+
+`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and every
+`jsee.*`/`jsde.*`/`j11_maintenance.*`/`migration.*`/`jsc.*` function the script calls) is patched to a
+mock before `main()` runs, mirroring `test_j11_stage_d_execute_cli_script.py`'s exact idiom -- these
+tests exercise CONTROL FLOW only (which functions get called, in what order, and which never get
+called), never real database I/O.
+"""
+from __future__ import annotations
+
+import importlib.util
+import json
+import sys
+from pathlib import Path
+from unittest import mock
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_e_execute.py"
+_MODULE_NAME = "run_j11_stage_e_execute_under_test"
+
+
+def _load_script_module():
+    """Mirrors `test_j11_stage_d_execute_cli_script.py`'s own loader exactly -- a REAL module object via
+    `importlib` (never `runpy.run_path`), so `monkeypatch.setattr(module, name, mock)` genuinely
+    intercepts every call the script's top-level code makes to that name."""
+    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[_MODULE_NAME] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def script_ns():
+    original_argv = sys.argv
+    try:
+        module = _load_script_module()
+        yield module
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop(_MODULE_NAME, None)
+
+
+# --- TC-13: missing --confirm -- NO database interaction of any kind ---------------------------------
+
+
+def test_tc13_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_e_execute.py"])  # no --confirm
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+
+
+# --- TC-14: --confirm but no --evidence-dir -- refuses, writes nothing anywhere ----------------------
+
+
+def test_tc14_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns, capsys):
+    mock_write_json = mock.MagicMock(name="_write_json")
+    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_e_execute.py", "--confirm"])
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_write_json.assert_not_called()
+    mock_get_engine.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
+# --- collision guard: a pre-existing output file refuses before any DB interaction --------------------
+
+
+def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    evidence_dir.mkdir()
+    (evidence_dir / "j11-stage-e-execute-outcome.json").write_text("{}")  # a prior run's leftover
+
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_stage_e_execute.py", "--confirm", "--evidence-dir", str(evidence_dir)],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_get_engine.assert_not_called()
+    assert "already contains" in capsys.readouterr().err
+
+
+# --- shared happy-path mock rig, so individual tests only override ONE piece --------------------------
+
+
+def _install_happy_path_mocks(monkeypatch, script_ns, *, evidence_dir: Path):
+    """Patches every DB-touching / expensive name the script calls to a deterministic, fully-successful
+    default. Returns a dict of the individual mocks so a test can override exactly one to prove a
+    specific stop-before-write control-flow property. Mirrors Stage D's CLI test rig: the LEAF checks
+    are mocked, but the REAL `jsee.stage_e_execution_outcome` composition logic runs (already separately
+    unit-tested for its own correctness in `test_j11_stage_e_execute.py`)."""
+    mock_engine = mock.MagicMock(name="engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
+
+    mock_session_instance = mock.MagicMock(name="session_instance")
+    # the script's own `int(session.scalar(select(func.count())...) or 0)` calls (pre/post
+    # forward_returns row count) need a REAL int back, not an auto-generated MagicMock (which has no
+    # usable `__int__`) -- `select`/`func` themselves are left real (harmless: `session.scalar` is what's
+    # actually mocked, so the real SQLAlchemy statement-building code runs but is never executed against
+    # a real connection).
+    mock_session_instance.scalar = mock.MagicMock(return_value=100)
+    mock_session_cm = mock.MagicMock()
+    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
+    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))
+
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))
+    monkeypatch.setattr(
+        script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}),
+    )
+
+    mock_boundary_recheck = mock.MagicMock(
+        name="recheck_maintenance_boundary_and_guard",
+        return_value={"ok": True, "boundary_active": True, "all_dates_blocked": True},
+    )
+    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_boundary_recheck)
+
+    mock_runs_check = mock.MagicMock(
+        name="confirm_stage_d_runs_present_unrestamped", return_value={"ok": True, "per_date": {}},
+    )
+    monkeypatch.setattr(script_ns.jsee, "confirm_stage_d_runs_present_unrestamped", mock_runs_check)
+
+    monkeypatch.setattr(
+        script_ns.engine_identity, "compute_engine_identity", mock.MagicMock(return_value="fresh-identity-value"),
+    )
+    mock_identity_check = mock.MagicMock(
+        name="check_engine_identity_matches_stage_d", return_value={"ok": True, "matches": True},
+    )
+    monkeypatch.setattr(script_ns.jsee, "check_engine_identity_matches_stage_d", mock_identity_check)
+
+    mock_manifest_check = mock.MagicMock(name="confirm_manifests_unchanged", return_value={"ok": True})
+    monkeypatch.setattr(script_ns.jsee, "confirm_manifests_unchanged", mock_manifest_check)
+
+    mock_gate_verdict = mock.MagicMock(
+        name="stage_e_preflight_gate_verdict", return_value={"proceed": True, "blocking_reasons": []},
+    )
+    monkeypatch.setattr(script_ns.jsee, "stage_e_preflight_gate_verdict", mock_gate_verdict)
+
+    monkeypatch.setattr(script_ns.j11_maintenance, "capture_full_table_sweep", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
+    monkeypatch.setattr(
+        script_ns.jsee, "capture_all_scanner_run_fingerprint",
+        mock.MagicMock(return_value={"row_count": 0, "rows": [], "fingerprint": "x"}),
+    )
+    monkeypatch.setattr(
+        script_ns.j11_maintenance, "capture_pre_reset_inventory",
+        mock.MagicMock(return_value={"daily_prices": {"fingerprint": "p"}}),
+    )
+    mock_retained_holes = mock.MagicMock(
+        name="capture_retained_incident_hole_counts",
+        return_value={"per_run_id_counts": {}, "total": 0, "run_count": 0},
+    )
+    monkeypatch.setattr(script_ns.jsee, "capture_retained_incident_hole_counts", mock_retained_holes)
+
+    mock_repair_loop = mock.MagicMock(
+        name="execute_stage_e_repair_loop",
+        return_value={
+            "total_runs_processed": 2, "total_rows_inserted": 5,
+            "rows_inserted_on_rebuilt_incident_runs": 3, "rows_inserted_on_retained_runs": 2,
+            "per_run_results": [],
+        },
+    )
+    monkeypatch.setattr(script_ns.jsee, "execute_stage_e_repair_loop", mock_repair_loop)
+
+    monkeypatch.setattr(script_ns.jsee, "read_process_vm_peak_kb", mock.MagicMock(return_value=500_000))
+    monkeypatch.setattr(
+        script_ns.jsee, "build_memory_check",
+        mock.MagicMock(return_value={"vm_peak_mb": 488.3, "within_cap": True}),
+    )
+
+    mock_population_report = mock.MagicMock(
+        name="live_verify_three_populations", return_value={"all_checks_pass": True},
+    )
+    monkeypatch.setattr(script_ns.jsee, "live_verify_three_populations", mock_population_report)
+
+    mock_mutation_accounting = mock.MagicMock(
+        name="build_stage_e_mutation_accounting",
+        return_value={"all_checks_pass": True, "checks": {}},
+    )
+    monkeypatch.setattr(script_ns.jsee, "build_stage_e_mutation_accounting", mock_mutation_accounting)
+
+    fake_frozen_identity_path = evidence_dir.parent / "frozen-identity.json"
+    fake_frozen_identity_path.write_text(json.dumps({"engine_identity": "fresh-identity-value"}))
+    fake_regeneration_path = evidence_dir.parent / "regeneration.json"
+    fake_regeneration_path.write_text(json.dumps({"per_date_results": [
+        {"date": "2026-05-12", "run_id": 3148}, {"date": "2026-05-13", "run_id": 3149},
+    ]}))
+    fake_certified_path = evidence_dir.parent / "certified.json"
+    fake_certified_path.write_text(json.dumps({"manifest_dump": []}))
+
+    return {
+        "boundary_recheck": mock_boundary_recheck,
+        "runs_check": mock_runs_check,
+        "identity_check": mock_identity_check,
+        "manifest_check": mock_manifest_check,
+        "gate_verdict": mock_gate_verdict,
+        "repair_loop": mock_repair_loop,
+        "population_report": mock_population_report,
+        "mutation_accounting": mock_mutation_accounting,
+        "frozen_identity_path": fake_frozen_identity_path,
+        "regeneration_path": fake_regeneration_path,
+        "certified_path": fake_certified_path,
+    }
+
+
+def _argv(evidence_dir: Path, mocks: dict) -> list[str]:
+    return [
+        "run_j11_stage_e_execute.py", "--confirm",
+        "--evidence-dir", str(evidence_dir),
+        "--stage-d-frozen-identity-path", str(mocks["frozen_identity_path"]),
+        "--stage-d-regeneration-path", str(mocks["regeneration_path"]),
+        "--certified-baseline-path", str(mocks["certified_path"]),
+    ]
+
+
+# --- TC-2-adjacent: preflight gate refusing to proceed -- the write loop is NEVER reached -------------
+
+
+def test_preflight_gate_not_proceed_never_calls_repair_loop(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["engine_identity_drifted_since_stage_d"]}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["repair_loop"].assert_not_called()
+    outcome = json.loads((evidence_dir / "j11-stage-e-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "preflight_gate_did_not_proceed"
+
+
+# --- TC-18/TC-9: failed post-execution mutation accounting -- outcome STILL written, exit non-zero ----
+
+
+def test_failed_mutation_accounting_writes_outcome_executed_false_and_returns_nonzero(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["mutation_accounting"].return_value = {"all_checks_pass": False, "checks": {"daily_prices_unchanged": False}}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["repair_loop"].assert_called_once()  # the gate passed, so the write loop DID run this time...
+    outcome_path = evidence_dir / "j11-stage-e-execute-outcome.json"
+    assert outcome_path.exists()  # ...but the outcome is STILL persisted either way
+    outcome = json.loads(outcome_path.read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "post_execution_mutation_accounting_failed"
+
+
+# --- failed live population verification -- outcome executed=False, exact reason ----------------------
+
+
+def test_failed_population_verification_writes_outcome_executed_false(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["population_report"].return_value = {"all_checks_pass": False}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    outcome = json.loads((evidence_dir / "j11-stage-e-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "live_population_verification_failed"
+
+
+# --- the full successful path: exit 0, outcome executed=True, every declared file written -------------
+
+
+def test_successful_full_path_returns_zero_and_writes_outcome_executed_true(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code == 0
+    mocks["repair_loop"].assert_called_once()
+    outcome = json.loads((evidence_dir / "j11-stage-e-execute-outcome.json").read_text())
+    assert outcome["executed"] is True
+    # every declared output filename was actually written
+    for name in script_ns.OUTPUT_FILENAMES:
+        assert (evidence_dir / name).exists(), f"missing evidence file {name}"
+
+
+# --- TC-16: terminal vocabulary -- exact required lines, both outcomes --------------------------------
+
+
+def test_tc16_terminal_lines_success(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+
+    script_ns.main()
+    err = capsys.readouterr().err
+
+    assert "J-11 STAGE D EXECUTED: YES" in err
+    assert "J-11 STAGE E COMPLETE: YES" in err
+    assert "J-11 STAGE F COMPLETE: NO" in err
+    assert "J-11 STAGE G VERIFIED: NO" in err
+    assert "J-11 INCIDENT STATUS: NOT REPAIRED" in err
+    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in err
+    assert "J-11 LIVE PRE-BOOT GUARD: ARMED" in err
+
+
+def test_tc16_terminal_lines_blocked_at_preflight(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["x"]}
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+
+    script_ns.main()
+    err = capsys.readouterr().err
+
+    assert "J-11 STAGE D EXECUTED: YES" in err
+    assert "J-11 STAGE E COMPLETE: NO" in err
+    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in err
+    assert "J-11 LIVE PRE-BOOT GUARD: ARMED" in err
+
+
+# --- TC-19-adjacent static safety net: no default path escapes the repo -------------------------------
+
+
+def test_none_of_the_default_paths_point_outside_the_repo(script_ns):
+    repo_root = script_ns.REPO_ROOT
+    for path in (
+        script_ns.DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH,
+        script_ns.DEFAULT_STAGE_D_REGENERATION_PATH,
+        script_ns.DEFAULT_CERTIFIED_BASELINE_PATH,
+    ):
+        assert str(path).startswith(str(repo_root))
+
+
+# --- helper-function unit tests (pure, no mocking needed) ----------------------------------------------
+
+
+def test_load_expected_run_id_by_date_honest_empty_on_missing_file(script_ns, tmp_path):
+    result = script_ns._load_expected_run_id_by_date(tmp_path / "does-not-exist.json")
+    assert result == {}
+
+
+def test_load_expected_run_id_by_date_parses_real_shape(script_ns, tmp_path):
+    path = tmp_path / "regen.json"
+    path.write_text(json.dumps({"per_date_results": [
+        {"date": "2026-05-12", "run_id": 3148}, {"date": "2026-05-13", "run_id": 3149},
+    ]}))
+    result = script_ns._load_expected_run_id_by_date(path)
+    assert result == {"2026-05-12": 3148, "2026-05-13": 3149}
+
+
+def test_load_stage_d_frozen_identity_honest_none_on_missing_file(script_ns, tmp_path):
+    assert script_ns._load_stage_d_frozen_identity(tmp_path / "nope.json") is None
+
+
+def test_load_stage_d_frozen_identity_parses_real_shape(script_ns, tmp_path):
+    path = tmp_path / "identity.json"
+    path.write_text(json.dumps({"engine_identity": "abc123"}))
+    assert script_ns._load_stage_d_frozen_identity(path) == "abc123"
```
