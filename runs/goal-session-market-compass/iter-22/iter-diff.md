# Iteration diff (bounded)

Files changed: 5. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_stage_g_verify.py` (1032 lines not shown)
- `apps/backend/scripts/run_j11_stage_g_verify.py` (221 lines not shown)
- `apps/backend/tests/test_j11_stage_g_verify.py` (1087 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 6ddc9599..419c9cd8 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -59,6 +59,7 @@ from app.engine import evidence  # ops-hardening iter-7 (J-06): the finalize hoo
 from app.engine import forward_testing, scanner
 from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
 from app.engine import compass  # goal-market-compass iter-2 (J-02/J-03/J-04): the finalize hook warms this
+from app.engine import j11_preboot_guard  # goal-market-compass iter-22 (J-11 Stage G): guards coverage_from_storage's self-heal write
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.prices import (
     _BarCache,
@@ -1544,8 +1545,15 @@ def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date
             return _tag_coverage_status(json.loads(row.payload_json), "current")
         # no persisted row: heal an explicit switcher selection of a real already-ingested historical date
         # (see docstring) — real coverage, self-healed to storage — rather than a false empty-DB sentinel.
+        # goal-market-compass iter-22 (J-11 Stage G): guarded by the SAME already-tested fail-closed idiom
+        # already live at warmup.py/forward_testing.py — a page visit to a date an ACTIVE maintenance
+        # boundary quarantines (e.g. a J-11 incident date whose ScannerRun exists but whose derived cache
+        # layer was deliberately cleared) must never repopulate coverage_snapshot via this request-path
+        # write. When blocked, fall through unchanged to the existing stale/all-zero fallback chain below.
         if as_of is not None and _scanner_run_exists(session, resolved_asof):
-            return _tag_coverage_status(refresh_coverage_snapshot_for(session, cfg, resolved_asof), "current")
+            boundary = j11_preboot_guard.evaluate_boundary_for_date_fail_closed(session, resolved_asof)
+            if not boundary["blocked"]:
+                return _tag_coverage_status(refresh_coverage_snapshot_for(session, cfg, resolved_asof), "current")
         # iter-27: the exact-match key missed (current stamp) — check for a real row under an OLDER stamp
         # for this SAME asof_key before conceding to the all-zero sentinel (see docstring above).
         stale_row = session.exec(
diff --git a/apps/backend/app/engine/j11_stage_g_verify.py b/apps/backend/app/engine/j11_stage_g_verify.py
new file mode 100644
index 00000000..7c8f6f88
--- /dev/null
+++ b/apps/backend/app/engine/j11_stage_g_verify.py
@@ -0,0 +1,1426 @@
+"""app.engine.j11_stage_g_verify -- J-11 Stage G FULL VERIFICATION (goal-market-compass iter-22).
+
+`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED" (owner,
+2026-08-26) item 9 authorizes Stage G, unconditionally, once Stage F has succeeded (iteration 21 --
+`runs/goal-market-compass-iter-21/j11-stage-f-execute-outcome.json`: `executed: true`). **Stage G is the
+terminal acceptance gate -- only Stage G may declare the incident fully repaired.** It performs NO
+regeneration, NO repair, NO cache warm: every check below is either a read-only SQLite query, a
+fixture-scoped unit test, or (on a full PASS only) a single-row `UPDATE` flipping
+`maintenance_boundaries.active` from `1` to `0`.
+
+**The one new finding this iteration closes (iteration 21's evaluator, not reported by any earlier lane):**
+`data_manager.coverage_from_storage`'s self-heal branch calls `refresh_coverage_snapshot_for` --  a
+request-path INSERT into `coverage_snapshot` -- whenever an explicit `?as_of=` names a date backed by a
+real `ScannerRun`, with no boundary-guard import anywhere in `data_manager.py`. Because Stage D gave all
+11 incident dates real runs, a single future page visit would silently repopulate the row Stage F
+deliberately cleared. This module's sibling edit (the ONE surgical change to `data_manager.py`) closes
+that path with the SAME already-tested `j11_preboot_guard.evaluate_boundary_for_date_fail_closed` idiom
+already live at `warmup.py:361` and `forward_testing.py:551`. This module itself only VERIFIES the
+closure (fixture-scoped tests + a fresh, AST-based call-site re-enumeration) -- it contains no part of the
+edit itself.
+
+**Binding facts this module must honour (owner-relayed, 2026-08-26/27, independently re-derivable from
+docs/goal.md):**
+  1. Attempt membership is `j11_maintenance.INCIDENT_DATES` (11 dates) mapped 1:1 onto Stage D's OWN
+     recorded run ids (3148-3158, loaded from evidence by the CALLER, never hardcoded here) -- **never**
+     `engine_identity` alone (`compute_engine_identity` stamps every run identically regardless of which
+     attempt created it, and `scanner.resolve_run` is unguarded, so identity alone cannot carry
+     membership -- iter-19 auditor finding B1). `verify_snapshot_scope` below enforces this by
+     construction: it only ever looks up runs BY DATE for the dates in the caller-supplied
+     `expected_run_id_by_date` mapping -- it never scans for "any row sharing a given identity".
+  2. Population (b) -- forward-return holes on RETAINED (non-rebuilt) runs -- is **structurally zero**,
+     not a missing repair: `data_manager._cascade_targets`/`remove_price_data` delete an affected run's
+     `ForwardReturn` rows WHOLE, so a partial hole cannot survive on a retained run (iteration 20's
+     re-derivation). `verify_forward_returns` below scores a zero delta as the CORRECT, expected outcome.
+  3. `docs/goal.md` ruling item 5 explicitly defers two named request-path gaps --
+     `scanner.py::resolve_run` and "ordinary Data Manager persistence paths capable of calling
+     `run_scan()`/`persist_run_payload()`" -- to post-J-11 hardening work AFTER Stage G. This module's
+     write-path re-enumeration (`enumerate_write_path_call_sites`/`classify_write_path_call_sites`)
+     records both as `still_open_and_deferred`, never `guarded`, and never silently omits them.
+
+**A resolved textual ambiguity, recorded honestly (developer judgment call, this iteration).** The phase
+spec's preflight bullet names `j11_stage_e_execute.confirm_stage_d_runs_present_unrestamped` for the
+run-presence/identity re-check, but that function's OWN documented contract asserts the run "currently has
+ZERO `ForwardReturn` rows" -- Stage E's OWN pre-write precondition. By Stage G's time the 11 rebuilt runs
+carry 16,592 real forward-return rows (Stage E's own successful fill), so reusing that exact function here
+would deterministically report `ok: False` on every legitimate PASS, which cannot be the intended contract
+for a spec whose own DoD requires reaching `FULLY REPAIRED`. The SAME paragraph's next sentence separately
+and unambiguously describes "`a fresh comparison of the 11 runs' ForwardReturn counts against ...
+recorded per-run outcome (including run 3158's own recorded 0)`" -- this is *exactly*
+`j11_stage_f_execute.confirm_stage_e_complete_and_unrestamped`'s documented behaviour (run
+presence + id + identity + EXACT recorded forward-return count, never zero). This module therefore reuses
+`jsfe.confirm_stage_e_complete_and_unrestamped` for the preflight's run-state check -- the only reading of
+the two overlapping instructions that is both internally consistent and actually satisfiable. Recorded here
+and in the dev handoff so a reviewer can independently evaluate the same judgment call.
+
+**Fix-mode correction (reviewer FAIL, this same iteration).** The first version of this module computed
+`membership_timeline_reconciled` by testing `membership_timeline_check["disposition"]` against the only two
+strings that field can ever hold -- an unconditional-pass tautology the reviewer caught, compounded by
+`run_j11_stage_g_verify.py` computing and persisting `stage_g_verdict` (and `finalize_stage_g`'s irrevocable
+boundary-deactivation write) BEFORE the one real reconciliation check (`membership_timeline_delete_
+reconciles`) even ran. `stage_g_verdict` now takes a `membership_timeline_deletion_check` argument -- the
+output of the new `confirm_membership_timeline_deletion_matches_verification`, which is genuinely failable
+-- and the CLI script now computes the delete-if-stale action and this confirmation BEFORE calling
+`stage_g_verdict`/`finalize_stage_g`, never after. See both functions' own docstrings for the exact
+semantics, and the dev handoff for the mutation-test proof that the fixed check can actually fail.
+
+Never touches (imports nothing from, calls nothing in that writes): `scanner.py`, `compass.py`,
+`sectors.py`, `scoring.py`, `j10_recovery.py`, or any canonical producer/serving function's CODE. This
+module COMPOSES already-existing, already-tested J-11 functions -- it introduces no second computation of
+any scored/derived value.
+"""
+from __future__ import annotations
+
+import ast
+import json
+import socket
+from datetime import date as date_cls
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any, Optional
+
+from sqlalchemy import func
+from sqlmodel import Session, select
+
+from app.config import Config
+from app.engine import data_manager
+from app.engine import indexes
+from app.engine import j11_maintenance
+from app.engine import j11_preboot_guard as guard
+from app.engine import j11_schema_migration as migration
+from app.engine import j11_stage_e_execute as jsee
+from app.engine import j11_stage_f_execute as jsfe
+from app.engine import research
+from app.engine.evidence import resolve_ledger_path
+from app.engine.graveyard import resolve_staging_ledger_path
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.engine.ledger import read_entries
+from app.engine.registry import resolve_registry_path
+from app.models import (
+    AvailabilityCache,
+    CoverageSnapshot,
+    DataProviderRun,
+    EventStudyCache,
+    ForwardAggregateCache,
+    IndexSeriesCache,
+    MarketPhaseCache,
+    MembershipTimelineCache,
+    NextSessionManifest,
+    ScannerRun,
+    Watchlist,
+)
+
+# The seven acceptance-relevant DB tables Stage G's OWN checks may ever touch with a write -- exactly the
+# two conditional actions the phase spec authorizes. Every other table must show zero write (enforced by
+# `build_stage_g_cross_iteration_mutation_accounting`).
+STAGE_G_CONDITIONAL_WRITE_TABLES: tuple[str, ...] = ("membership_timeline_cache", "maintenance_boundaries")
+
+# The J-11 stage-module family this module's evidence-reinterpretation static check covers -- every module
+# that has ever performed a J-11 write, plus this one. A future stage module joining the family should be
+# added here (fail-closed in spirit: the caller passes the list explicitly, this module invents nothing).
+_FORBIDDEN_REINTERPRETATION_TOKENS: tuple[str, ...] = (
+    "forward_walk", "verify_edge", "ledger.append_entry",
+)
+
+# AG-9 self-check token list. Deliberately NARROWER than the identical idiom in
+# `test_j11_stage_f_execute.py` (which also bans `socket`): `verify_operational_isolation` below uses the
+# stdlib `socket` module for a LOCAL loopback listening-port probe (never an outbound data fetch), so
+# banning `socket` here would be a false positive against this module's own legitimate, documented,
+# non-network use. The remaining tokens are the actual live-data-fetch-capable libraries AG-9 guards
+# against.
+_NETWORK_TOKENS: tuple[str, ...] = ("requests", "httpx", "urllib", "yfinance", "aiohttp", "http.client")
+
+# The three write-path function NAMES this module's call-site re-enumeration tracks -- the exact three
+# named in docs/goal.md's IN SCOPE bullet ("close_coverage_snapshot_self_heal_write_path").
+_WRITE_PATH_FUNCTION_NAMES: tuple[str, ...] = (
+    "run_scan", "get_or_create_manifest", "refresh_coverage_snapshot_for",
+)
+
+# The hand-reviewed classification of every call site `enumerate_write_path_call_sites` is expected to
+# find under `apps/backend/app` (verified live, 2026-08-27, via the SAME AST walk this module performs --
+# see the dev handoff for the full grep transcript). Keyed by (relative file path, enclosing function
+# qualname, matched name) so a LINE-NUMBER shift (which the phase spec itself warns "has moved before")
+# never breaks the mapping. A call site the live re-enumeration finds that is NOT a key in this table is
+# reported `unclassified` -- the check fails closed rather than silently accepting an unreviewed new call
+# site (e.g. a future PR adding a new `run_scan(` call without updating this table).
+WRITE_PATH_CLASSIFICATION: dict[tuple[str, str, str], dict] = {
+    ("app/engine/warmup.py", "ensure_latest_snapshot", "run_scan"): {
+        "classification": "guarded",
+        "note": (
+            "the synchronous latest-snapshot boot path -- j11_preboot_guard.evaluate_boundary_for_date "
+            "checked inline immediately before this call (iteration 16)."
+        ),
+    },
+    ("app/engine/warmup.py", "_run_warmup", "run_scan"): {
+        "classification": "guarded",
+        "note": (
+            "the background historical warm-up cadence loop -- "
+            "j11_preboot_guard.evaluate_boundary_for_date_fail_closed checked per-date before this call "
+            "(iteration 18)."
+        ),
+    },
+    ("app/engine/forward_testing.py", "_backfill", "run_scan"): {
+        "classification": "guarded",
+        "note": (
+            "the walk-forward asof-date loop reachable only from warmup._run_warmup -- "
+            "j11_preboot_guard.evaluate_boundary_for_date_fail_closed checked per-date before this call "
+            "(iteration 18)."
+        ),
+    },
+    ("app/engine/data_manager.py", "coverage_from_storage", "refresh_coverage_snapshot_for"): {
+        "classification": "guarded",
+        "note": (
+            "THIS iteration's own edit -- j11_preboot_guard.evaluate_boundary_for_date_fail_closed "
+            "checked immediately before the self-heal write; on blocked=True it falls through unchanged "
+            "to the function's existing stale/all-zero fallback chain."
+        ),
+    },
+    ("app/engine/j11_stage_d_execute.py", "execute_stage_d_for_date", "run_scan"): {
+        "classification": "stage_d_authorized_write",
+        "note": "Stage D's own owner-authorized regeneration write (iteration 19); not a request-path gap.",
+    },
+    ("app/engine/scanner.py", "resolve_run", "run_scan"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "docs/goal.md ruling item 5's FIRST named deferred gap, verbatim -- an explicit `?as_of=` "
+            "request can reach this unguarded call. Deliberately NOT touched this iteration (OUT OF "
+            "SCOPE; scanner.py shows zero diff -- TC-21)."
+        ),
+    },
+    ("app/engine/scanner.py", "_bootstrap", "run_scan"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "reachable only via scanner.bootstrap_runs, which has ZERO production call sites anywhere in "
+            "apps/backend/app (verified by the SAME live grep/AST re-enumeration this table is built "
+            "from) -- a latent, currently-unreachable gap, not an active one. Recorded honestly rather "
+            "than omitted merely because it is dormant today."
+        ),
+    },
+    ("app/engine/data_manager.py", "_do_backfill._persist", "run_scan"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "docs/goal.md ruling item 5's SECOND named deferred gap ('ordinary Data Manager persistence "
+            "paths capable of calling run_scan()') -- the ordinary backfill/import job's per-date "
+            "worker-fast-path race branch. Deliberately NOT touched this iteration."
+        ),
+    },
+    ("app/api/compass.py", "compass", "get_or_create_manifest"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "the GET /api/compass request-path call site of compass.get_or_create_manifest -- the SAME "
+            "species of gap as the two ruling-item-5-named ones, but not itself named by ruling item 5's "
+            "text or this iteration's coordinator note as something Stage G must resolve (see the "
+            "iteration's own scoping decision, logged to assumptions.md). Deliberately NOT touched "
+            "(compass.py shows zero diff -- TC-21)."
+        ),
+    },
+    ("app/engine/data_manager.py", "_refresh_ingest_aggregates", "get_or_create_manifest"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "the ingest-finalize manifest-freeze call site (the legitimate, ordinary producer of new "
+            "manifests). Self-limiting by create-once + prog.new_snapshot_dates semantics (only fires "
+            "for a date THIS SAME ingest job just created), but not itself boundary-guarded -- same "
+            "family as the two named gaps, recorded honestly rather than silently treated as safe merely "
+            "because it is lower-probability."
+        ),
+    },
+    ("app/engine/data_manager.py", "refresh_coverage_snapshot", "refresh_coverage_snapshot_for"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "reachable only via the ingest-finalize hook or the boot warm-up safety net (both externally "
+            "unreachable during maintenance isolation, and both gated by the SAME create-once/latest-"
+            "date semantics as above) -- not itself boundary-guarded. Same coverage-write family as this "
+            "iteration's OWN closed gap, but a DIFFERENT call site; not touched this iteration."
+        ),
+    },
+    ("app/engine/data_manager.py", "_persist_per_date_coverage_snapshots", "refresh_coverage_snapshot_for"): {
+        "classification": "still_open_and_deferred",
+        "note": (
+            "the ingest-finalize per-date coverage warm loop -- same family and same reasoning as the "
+            "two coverage-write entries directly above; not touched this iteration."
+        ),
+    },
+}
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+def _count(session: Session, model: Any, **filters: Any) -> int:
+    """A column-projected `COUNT(*)` -- never an ORM hydration of the matched rows (AG-8). Mirrors every
+    other `j11_*.py` module's own trivial per-module copy of this idiom."""
+    stmt = select(func.count()).select_from(model)
+    for key, value in filters.items():
+        stmt = stmt.where(getattr(model, key) == value)
+    return int(session.scalar(stmt) or 0)
+
+
+def _iso_or_none(value: Optional[datetime]) -> Optional[str]:
+    if value is None:
+        return None
+    if value.tzinfo is None:
+        value = value.replace(tzinfo=timezone.utc)
+    return value.astimezone(timezone.utc).isoformat()
+
+
+# ================================================================================================
+# Step 1 -- the fresh, read-only Stage G preflight (re-derives Stage D/E/F's certified end state)
+# ================================================================================================
+
+
+def stage_g_preflight_gate_verdict(
+    *, boundary_recheck: dict, stage_d_e_check: dict, identity_check: dict, manifest_check: dict,
+) -> dict:
+    """The single go/no-go decision BEFORE any Stage G acceptance check runs. Any one of the four checks
+    failing means `proceed: False`, and the caller MUST perform zero further checks and zero writes
+    (docs/goal.md: "Any drift -> zero further checks, zero writes, STOP with the exact blocker named").
+    Every input is produced by REUSING an already-existing, already-tested function -- see the module
+    docstring for exactly which one and why."""
+    boundary_ok = bool(boundary_recheck.get("ok"))
+    stage_d_e_ok = bool(stage_d_e_check.get("ok"))
+    identity_ok = bool(identity_check.get("ok"))
+    manifest_ok = bool(manifest_check.get("ok"))
+    proceed = boundary_ok and stage_d_e_ok and identity_ok and manifest_ok
+
+    blocking_reasons: list[str] = []
+    if not boundary_ok:
+        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")
+    if not stage_d_e_ok:
+        blocking_reasons.append("stage_d_runs_not_present_unrestamped_or_forward_return_count_mismatch")
+    if not identity_ok:
+        blocking_reasons.append("engine_identity_drifted_since_stage_d")
+    if not manifest_ok:
+        blocking_reasons.append("next_session_manifests_changed_since_stage_d")
+
+    return {
+        "generated_at": _now_iso(),
+        "proceed": proceed,
+        "boundary_ok": boundary_ok,
+        "stage_d_e_ok": stage_d_e_ok,
+        "identity_ok": identity_ok,
+        "manifest_ok": manifest_ok,
+        "blocking_reasons": blocking_reasons,
+    }
+
+
+# ================================================================================================
+# Step 2a -- raw inputs (daily_prices unchanged against the certified post-AVB-correction baseline)
+# ================================================================================================
+
+
+def verify_raw_inputs(
+    session: Session, *, certified_daily_prices_fingerprint: str, module_and_script_paths: tuple[Path, ...],
+) -> dict:
+    """`daily_prices` row count + content fingerprint, re-derived fresh via the SAME
+    `j11_maintenance.capture_pre_reset_inventory` recipe every earlier J-11 stage already uses (never a
+    second fingerprint formula), compared against the certified post-AVB-correction baseline value (the
+    recipe is stated beside the value below -- never a bare number, per iter-15b's lesson). J-10's
+    recovered 2026-08-11/2026-08-12 rows are covered transitively: they are ordinary rows of the SAME
+    `daily_prices` table this fingerprint spans in full, and the certified baseline value itself IS the
+    post-AVB-correction fingerprint (the one authorized `daily_prices` mutation this whole J-11 contract
+    permits) -- a changed fingerprint would already catch any row-level regression to them specifically.
+    Also runs the AG-9 self-check (`confirm_no_network_capable_import`) over the supplied module/script
+    paths, recorded as part of THIS check's own evidence (never merely a separate test claim)."""
+    fresh = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+    fingerprint_matches = fresh["fingerprint"] == certified_daily_prices_fingerprint
+    network_scan = confirm_no_network_capable_import(*module_and_script_paths)
+    ok = fingerprint_matches and network_scan["clean"]
+    return {
+        "generated_at": _now_iso(),
+        "recipe": (
+            "j11_maintenance.capture_pre_reset_inventory(session)['daily_prices']['fingerprint'] == "
+            "sha256(sorted-key JSON of {row_count, min_date, max_date, id_sum, sum(open+high+low+close+"
+            "volume)}) -- the SAME recipe every earlier J-11 stage's own preflight already reuses."
+        ),
+        "certified_daily_prices_fingerprint": certified_daily_prices_fingerprint,
+        "fresh_daily_prices": fresh,
+        "fingerprint_matches": fingerprint_matches,
+        "network_scan": network_scan,
+        "ok": ok,
+    }
+
+
+# ================================================================================================
+# Step 2b -- snapshot scope (membership via ids + evidence, never engine_identity alone)
+# ================================================================================================
+
+
+def verify_snapshot_scope(
+    session: Session,
+    *,
+    expected_run_id_by_date: dict[str, int],
+    iter18_pre_stage_d_sweep: dict,
+    live_full_table_sweep: dict,
+) -> dict:
+    """Confirms the live `ScannerRun` id for every one of Stage D's 11 incident dates is EXACTLY the id
+    Stage D's OWN recorded execution evidence assigned to it -- one-to-one, 11 dates, 11 ids. Deliberately
+    looks up membership ONLY by iterating `expected_run_id_by_date`'s own keys (Stage D's evidence): it
+    NEVER scans the table for "any row sharing the frozen engine_identity", which is exactly the owner's
+    binding membership rule (see the module docstring) -- a 12th fixture run sharing the identical frozen
+    identity but a different date is structurally invisible to this function (proven in
+    test_j11_stage_g_verify.py's TC-4 test). ALSO confirms, via the SAME `scanner_runs` slice of a
+    cross-iteration full-table-sweep diff against iteration 18's pre-Stage-D baseline, that the table's
+    only change since iteration 18 is consistent with EXACTLY these 11 new rows (a corroborating,
+    rowid-based signal -- Stage D's own already-certified `capture_legacy_and_null_scanner_run_fingerprint`
+    full-content proof is the PRIMARY guarantee that no EXISTING row was rewritten)."""
+    expected_dates = {d.isoformat() for d in INCIDENT_DATES}
+    per_date: dict[str, dict] = {}
+    for iso, expected_id in sorted(expected_run_id_by_date.items()):
+        one_date = date_cls.fromisoformat(iso)
+        rows = session.exec(select(ScannerRun.id).where(ScannerRun.asof_date == one_date)).all()
+        observed_ids = sorted(int(r) for r in rows)
+        exactly_one = len(observed_ids) == 1
+        matches = exactly_one and observed_ids[0] == expected_id
+        per_date[iso] = {
+            "expected_id": expected_id, "observed_ids": observed_ids, "exactly_one_row": exactly_one,
+            "ok": matches,
+        }
+    complete_11_of_11 = set(per_date) == expected_dates == set(expected_run_id_by_date)
+    per_date_ok = bool(per_date) and all(v["ok"] for v in per_date.values())
+
+    sweep_diff = j11_maintenance.diff_full_table_sweeps(iter18_pre_stage_d_sweep, live_full_table_sweep)
+    scanner_runs_changed = "scanner_runs" in sweep_diff["changed_existing_tables"]
+    live_scanner_runs_count = live_full_table_sweep["per_table"].get("scanner_runs", {}).get("count")
+    pre_scanner_runs_count = iter18_pre_stage_d_sweep["per_table"].get("scanner_runs", {}).get("count")
+    count_delta = (
+        (live_scanner_runs_count - pre_scanner_runs_count)
+        if live_scanner_runs_count is not None and pre_scanner_runs_count is not None else None
+    )
+    sweep_delta_matches_11_new_rows = count_delta == len(expected_run_id_by_date)
+
+    ok = complete_11_of_11 and per_date_ok and scanner_runs_changed and sweep_delta_matches_11_new_rows
+    return {
+        "generated_at": _now_iso(),
... [diff_bound] apps/backend/app/engine/j11_stage_g_verify.py: 1032 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_stage_g_verify.py b/apps/backend/scripts/run_j11_stage_g_verify.py
new file mode 100644
index 00000000..6e057947
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_g_verify.py
@@ -0,0 +1,615 @@
+"""goal-market-compass iter-22 -- J-11 Stage G FULL VERIFICATION: the terminal, owner-authorized
+acceptance gate proving the whole D->G recovery arc holds against the live database
+(`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED", owner
+2026-08-26, item 9 -- authorized unconditionally following a successful Stage F; iteration 21 already
+executed and independently-evaluator-verified Stage F).
+
+Mirrors `run_j11_stage_f_execute.py`'s idiom exactly: NO database interaction of any kind, not even a
+read, without `--confirm`; every checkpoint is persisted BEFORE the next step runs so a mid-run crash
+still leaves a forensic trail; the outcome/terminal-lines marker is written LAST, UNCONDITIONALLY,
+whichever of Stage G's two honest terminal states verification proves. Sequence:
+
+  1. Fresh, READ-ONLY preflight -- boundary/guard re-check (`j11_stage_d_execute.
+     recheck_maintenance_boundary_and_guard`, REUSED directly), the 11 incident runs' presence + identity
+     + EXACT recorded ForwardReturn count (`j11_stage_f_execute.confirm_stage_e_complete_and_unrestamped`,
+     REUSED directly -- see `j11_stage_g_verify`'s module docstring for why this function, not
+     `j11_stage_e_execute.confirm_stage_d_runs_present_unrestamped`, is the correct reuse here), a fresh
+     `engine_identity` equality check against Stage D's frozen value (`j11_stage_e_execute.
+     check_engine_identity_matches_stage_d`, REUSED directly), and a `next_session_manifests` unchanged
+     check against the certified iter-16 baseline (`j11_stage_e_execute.confirm_manifests_unchanged`,
+     REUSED directly) -- combined into ONE preflight gate. STOPS here (zero further checks, zero writes)
+     unless the gate's `proceed` is True.
+  2. Every acceptance-category check, read-only: raw inputs, snapshot scope (ids 3148-3158 + Stage D's own
+     execution evidence -- never `engine_identity` alone), forward-return populations (a)/(b)/(c) (population
+     (b) = 0 scored as CORRECT, not a gap), manifests (direct SQL only -- never `get_or_create_manifest`),
+     audit/evidence/user-state, cache dispositions, the `membership_timeline_cache` B2 per-date
+     recompute-and-compare, the 18 named traps, a fresh write-path call-site re-enumeration + classification,
+     an evidence-reinterpretation static check, and operational isolation.
+  3. The ONE conditional corrective write this iteration may perform outside `finalize_stage_g` itself: if
+     the membership-timeline B2 check found a stale row, delete it now (Stage F's own pre-approved
+     fallback) -- this happens regardless of the overall verdict (a stale cache row is repaired either way,
+     per the phase spec's own wording: "the membership-timeline delete already covered above if that
+     specific check is what failed" is explicitly still authorized on a FAIL attempt), followed immediately
+     by a live, post-action `COUNT(*)` proving the delete genuinely took effect
+     (`confirm_membership_timeline_deletion_matches_verification`). **This runs BEFORE the aggregate
+     verdict below (review FAIL fix, iter-22 -- was formerly computed only after the verdict/finalize had
+     already run, too late to affect anything) so a corrective write that silently fails can actually block
+     the FULLY REPAIRED declaration.**
+  4. Aggregate verdict (`stage_g_verdict`) -- no boolean permitted to pass by construction; folds in step
+     3's real, failable delete-reconciliation result as `membership_timeline_reconciled`.
+  5. `finalize_stage_g` -- the ONE further conditional write: on a full PASS, deactivate (never delete) the
+     `j11-incident-recovery` boundary; on any FAIL, zero further writes, boundary stays `active=1`.
+  6. Post-write, read-only cross-iteration mutation accounting -- reconciles every changed table's delta
+     since iteration 18's pre-Stage-D baseline sweep to exactly Stage D + Stage E + Stage F + this
+     iteration's own two possible conditional writes, and takes a SECOND, independent confirming
+     measurement of the membership-timeline delete (step 3 already gated the verdict on the first). Written
+     LAST, alongside the final terminal-outcome block, unconditionally.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_g_verify.py \\
+        --confirm \\
+        --evidence-dir runs/goal-market-compass-iter-22
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
+import os
+import sys
+from pathlib import Path
+from typing import Optional
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from sqlalchemy import func as sa_func  # noqa: E402
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
+from app.engine import j11_stage_f_execute as jsfe  # noqa: E402
+from app.engine import j11_stage_g_verify as jsgv  # noqa: E402
+from app.models import MaintenanceBoundary, MembershipTimelineCache  # noqa: E402
+
+DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-frozen-identity.json"
+)
+DEFAULT_STAGE_D_REGENERATION_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-regeneration.json"
+)
+DEFAULT_STAGE_E_POPULATION_REPORT_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-20" / "j11-stage-e-execute-population-report.json"
+)
+DEFAULT_STAGE_F_DISPOSITIONS_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-21" / "j11-stage-f-execute-dispositions.json"
+)
+DEFAULT_CERTIFIED_BASELINE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
+)
+DEFAULT_PRE_RESET_INVENTORY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-pre-reset-inventory.json"
+)
+DEFAULT_ITER18_PRE_STAGE_D_SWEEP_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-18" / "j11-iter18-full-table-sweep-after.json"
+)
+
+TESTS_DIR = BACKEND_DIR / "tests"
+APP_DIR = BACKEND_DIR / "app"
+THIS_MODULE_PATH = APP_DIR / "engine" / "j11_stage_g_verify.py"
+THIS_SCRIPT_PATH = Path(__file__).resolve()
+
+OUTPUT_FILENAMES = (
+    "j11-stage-g-verify-db-file-true-start.json",
+    "j11-stage-g-verify-boundary-recheck.json",
+    "j11-stage-g-verify-stage-d-e-check.json",
+    "j11-stage-g-verify-identity-comparison.json",
+    "j11-stage-g-verify-manifest-preflight-check.json",
+    "j11-stage-g-verify-preflight-gate.json",
+    "j11-stage-g-verify-raw-inputs.json",
+    "j11-stage-g-verify-snapshot-scope.json",
+    "j11-stage-g-verify-forward-returns.json",
+    "j11-stage-g-verify-manifests.json",
+    "j11-stage-g-verify-audit-evidence-and-user-state.json",
+    "j11-stage-g-verify-cache-dispositions.json",
+    "j11-stage-g-verify-membership-timeline-check.json",
+    "j11-stage-g-verify-membership-timeline-delete-action.json",
+    "j11-stage-g-verify-membership-timeline-deletion-check.json",
+    "j11-stage-g-verify-named-traps.json",
+    "j11-stage-g-verify-write-path-sites.json",
+    "j11-stage-g-verify-write-path-classification.json",
+    "j11-stage-g-verify-evidence-reinterpretation-check.json",
+    "j11-stage-g-verify-network-import-check.json",
+    "j11-stage-g-verify-operational-isolation.json",
+    "j11-stage-g-verify-verdict.json",
+    "j11-stage-g-verify-finalize.json",
+    "j11-stage-g-verify-memory-check.json",
+    "j11-stage-g-verify-mutation-accounting.json",
+    "j11-stage-g-verify-outcome.json",
+    "j11-stage-g-verify-db-file-true-end.json",
+)
+
+
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
+    return [name for name in filenames if (evidence_dir / name).exists()]
+
+
+def _load_json(path: Path) -> Optional[dict]:
+    if not path.exists():
+        return None
+    try:
+        return json.loads(path.read_text())
+    except (OSError, json.JSONDecodeError):
+        return None
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
+def _load_stage_d_frozen_identity(path: Path) -> Optional[str]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return None
+    value = payload.get("engine_identity")
+    return value if isinstance(value, str) else None
+
+
+def _load_expected_run_id_by_date(path: Path) -> dict[str, int]:
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
+def _load_expected_forward_return_count_by_run_id(path: Path) -> dict[str, int]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return {}
+    population_a = payload.get("population_a_rebuilt_incident_runs")
+    if not isinstance(population_a, dict):
+        return {}
+    out: dict[str, int] = {}
+    for run_id_str, entry in population_a.items():
+        if isinstance(entry, dict) and isinstance(entry.get("post"), int):
+            out[run_id_str] = entry["post"]
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
+def _load_stage_f_new_dates(path: Path) -> list[str]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return []
+    mt = payload.get("membership_timeline_cache")
+    if not isinstance(mt, dict):
+        return []
+    reuse_eval = mt.get("membership_reuse_evaluation")
+    if not isinstance(reuse_eval, dict):
+        return []
+    new_dates = reuse_eval.get("new_dates")
+    return new_dates if isinstance(new_dates, list) else []
+
+
+def _print_terminal_lines(terminal_lines: str) -> None:
+    print(terminal_lines, file=sys.stderr)
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
+    parser.add_argument("--stage-e-population-report-path", type=Path, default=DEFAULT_STAGE_E_POPULATION_REPORT_PATH)
+    parser.add_argument("--stage-f-dispositions-path", type=Path, default=DEFAULT_STAGE_F_DISPOSITIONS_PATH)
+    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
+    parser.add_argument("--pre-reset-inventory-path", type=Path, default=DEFAULT_PRE_RESET_INVENTORY_PATH)
+    parser.add_argument("--iter18-pre-stage-d-sweep-path", type=Path, default=DEFAULT_ITER18_PRE_STAGE_D_SWEEP_PATH)
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is J-11's terminal Stage G verification -- "
+            "docs/goal.md's Stage D-through-G OWNER RULING, item 9). No database interaction, not even a "
+            "read, has occurred.",
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
+    _write_json(evidence_dir / "j11-stage-g-verify-db-file-true-start.json", db_file_true_start)
+
+    engine = get_engine()  # the SAME pooled writable engine the real backend uses.
+
+    stage_d_frozen_identity = _load_stage_d_frozen_identity(args.stage_d_frozen_identity_path)
+    expected_run_id_by_date = _load_expected_run_id_by_date(args.stage_d_regeneration_path)
+    expected_forward_return_count_by_run_id = _load_expected_forward_return_count_by_run_id(args.stage_e_population_report_path)
+    stage_e_population_report = _load_json(args.stage_e_population_report_path) or {}
+    stage_f_dispositions = _load_json(args.stage_f_dispositions_path) or {}
+    stage_f_new_dates = _load_stage_f_new_dates(args.stage_f_dispositions_path)
+    certified_baseline = _load_json(args.certified_baseline_path) or {}
+    certified_manifest_dump = _load_certified_manifest_dump(args.certified_baseline_path)
+    certified_pre_reset_inventory = _load_json(args.pre_reset_inventory_path) or {}
+    iter18_pre_stage_d_sweep_wrapper = _load_json(args.iter18_pre_stage_d_sweep_path) or {}
+    iter18_pre_stage_d_sweep = iter18_pre_stage_d_sweep_wrapper.get("sweep") or {}
+    incident_run_ids = sorted(expected_run_id_by_date.values())
+
+    missing_inputs = []
+    if stage_d_frozen_identity is None:
+        missing_inputs.append("stage_d_frozen_identity")
+    if not expected_run_id_by_date:
+        missing_inputs.append("expected_run_id_by_date")
+    if not expected_forward_return_count_by_run_id:
+        missing_inputs.append("expected_forward_return_count_by_run_id")
+    if not certified_manifest_dump:
+        missing_inputs.append("certified_manifest_dump")
+    if not certified_pre_reset_inventory:
+        missing_inputs.append("certified_pre_reset_inventory")
+    if not iter18_pre_stage_d_sweep:
+        missing_inputs.append("iter18_pre_stage_d_sweep")
+
+    def _stop(reason: str, preflight_gate: dict) -> int:
+        finalize = {
+            "generated_at": None, "outcome": "NOT_REPAIRED_ATTEMPT_INCOMPLETE",
+            "boundary_deactivated": False,
+            "terminal_lines": (
+                "J-11 STAGE D EXECUTED: YES\n"
+                "J-11 STAGE E COMPLETE: YES\n"
+                "J-11 STAGE F COMPLETE: YES\n"
+                "J-11 STAGE G VERIFIED: NO\n"
+                "J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE\n"
+                "J-11 MAINTENANCE BOUNDARY: ACTIVE"
+            ),
+        }
+        _write_json(evidence_dir / "j11-stage-g-verify-finalize.json", finalize)
+        outcome = {"generated_at": None, "reason": reason, "preflight_gate": preflight_gate}
+        _write_json(evidence_dir / "j11-stage-g-verify-outcome.json", outcome)
+        db_file_true_end = jsc.db_file_fingerprint(db_path)
+        _write_json(evidence_dir / "j11-stage-g-verify-db-file-true-end.json", db_file_true_end)
+        print(f"STOP before any write: {reason}", file=sys.stderr)
+        _print_terminal_lines(finalize["terminal_lines"])
+        return 1
+
+    if missing_inputs:
+        return _stop(f"missing/unloadable required historical evidence inputs: {missing_inputs}", {"proceed": False})
+
+    # === Step 1: fresh, read-only preflight ============================================================
+    with Session(engine) as session:
+        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
+    _write_json(evidence_dir / "j11-stage-g-verify-boundary-recheck.json", boundary_recheck)
+    print(f"boundary/guard recheck: ok={boundary_recheck['ok']}", file=sys.stderr)
+
+    with Session(engine) as session:
+        stage_d_e_check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session,
+            expected_run_id_by_date=expected_run_id_by_date,
+            expected_forward_return_count_by_run_id=expected_forward_return_count_by_run_id,
+            frozen_engine_identity=stage_d_frozen_identity or "",
+        )
+    _write_json(evidence_dir / "j11-stage-g-verify-stage-d-e-check.json", stage_d_e_check)
+    print(f"Stage D/E end-state check: ok={stage_d_e_check['ok']}", file=sys.stderr)
+
+    fresh_identity = engine_identity.compute_engine_identity(cfg)
+    identity_check = jsee.check_engine_identity_matches_stage_d(fresh_identity, stage_d_frozen_identity)
+    _write_json(evidence_dir / "j11-stage-g-verify-identity-comparison.json", identity_check)
+    print(f"engine_identity check: ok={identity_check['ok']} fresh={fresh_identity}", file=sys.stderr)
+
+    manifest_preflight_check = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=certified_manifest_dump)
+    _write_json(evidence_dir / "j11-stage-g-verify-manifest-preflight-check.json", manifest_preflight_check)
+    print(f"manifest preflight check: ok={manifest_preflight_check['ok']}", file=sys.stderr)
+
+    preflight_gate = jsgv.stage_g_preflight_gate_verdict(
+        boundary_recheck=boundary_recheck, stage_d_e_check=stage_d_e_check,
+        identity_check=identity_check, manifest_check=manifest_preflight_check,
+    )
+    _write_json(evidence_dir / "j11-stage-g-verify-preflight-gate.json", preflight_gate)
+    print(f"preflight gate: proceed={preflight_gate['proceed']} reasons={preflight_gate['blocking_reasons']}", file=sys.stderr)
+
+    if not preflight_gate["proceed"]:
+        return _stop("preflight gate did not proceed", preflight_gate)
+
+    # === Step 2: every acceptance-category check, read-only ============================================
+    with Session(engine) as session:
+        raw_inputs = jsgv.verify_raw_inputs(
+            session,
+            certified_daily_prices_fingerprint=certified_baseline.get("daily_prices_fingerprint", ""),
+            module_and_script_paths=(THIS_MODULE_PATH, THIS_SCRIPT_PATH),
+        )
+    _write_json(evidence_dir / "j11-stage-g-verify-raw-inputs.json", raw_inputs)
+    print(f"raw inputs: ok={raw_inputs['ok']}", file=sys.stderr)
+
+    with Session(engine) as session:
+        live_full_table_sweep_pre = j11_maintenance.capture_full_table_sweep(session)
+        snapshot_scope = jsgv.verify_snapshot_scope(
... [diff_bound] apps/backend/scripts/run_j11_stage_g_verify.py: 221 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_g_verify.py b/apps/backend/tests/test_j11_stage_g_verify.py
new file mode 100644
index 00000000..9d628f58
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_g_verify.py
@@ -0,0 +1,1481 @@
+"""goal-market-compass iter-22 -- J-11 Stage G FULL VERIFICATION tests (TC-1 through TC-19, TC-22,
+TC-24, TC-25, TC-26, TC-29 from the phase spec's TESTING REQUIREMENTS; TC-20/TC-21/TC-27/TC-28/TC-30 are
+proven by a fresh live grep/`git status`/`git diff` cited in the dev handoff, or live in the CLI-script
+test file).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
+pattern `test_j11_stage_e_execute.py`/`test_j11_stage_f_execute.py` use, never `loaded_engine` and never
+`apps/backend/data/trendora.db`.
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.config import load_config
+from app.engine import data_manager
+from app.engine import j11_stage_g_verify as jsgv
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import (
+    AvailabilityCache,
+    CoverageSnapshot,
+    DailyPrice,
+    EventStudyCache,
+    ForwardAggregateCache,
+    ForwardReturn,
+    IndexSeriesCache,
+    MaintenanceBoundary,
+    MarketPhaseCache,
+    MembershipTimelineCache,
+    NextSessionManifest,
+    ScannerResult,
+    ScannerRun,
+)
+
+pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+MODULE_PATH = BACKEND_DIR / "app" / "engine" / "j11_stage_g_verify.py"
+CLI_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_g_verify.py"
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
+# --- shared fixture helpers (mirrors test_j11_stage_e_execute.py/test_j11_stage_f_execute.py's idiom) ---
+
+
+def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = "stub-identity", created_at=None) -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=created_at or datetime.now(timezone.utc), provider="seed", benchmark="SPY",
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
+def _mk_forward_return(session: Session, run: ScannerRun, symbol: str, *, horizon: int = 1, measured_date=None) -> ForwardReturn:
+    fr = ForwardReturn(
+        run_id=run.id, symbol=symbol, horizon=horizon, asof_date=run.asof_date,
+        entry_close=100.0, measured_date=measured_date or (run.asof_date + timedelta(days=horizon)),
+        realized_return=0.01,
+    )
+    session.add(fr)
+    session.flush()
+    return fr
+
+
+def _mk_prices(session: Session, symbol: str, start: date, n_days: int, *, price: float = 100.0) -> None:
+    d = start
+    for _ in range(n_days):
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
+def _mk_boundary(session: Session, *, dates=INCIDENT_DATES, active: bool = True) -> MaintenanceBoundary:
+    from app.engine import j11_preboot_guard as guard
+    return guard.register_boundary(session, name=guard.J11_INCIDENT_BOUNDARY_NAME, dates=dates, reason="fixture", active=active)
+
+
+def _mk_membership_timeline_row(session, *, dataset_version, created_at=None, points=None):
+    payload = {"candidate_pool_count": 1, "points": points or [], "labels": {}}
+    row = MembershipTimelineCache(
+        dataset_version=dataset_version, payload_json=json.dumps(payload),
+        created_at=created_at or datetime.now(timezone.utc),
+    )
+    session.add(row); session.flush(); return row
+
+
+def _empty_sweep() -> dict:
+    """A minimal `capture_full_table_sweep`-shaped dict with zero tables -- for tests that need a valid
+    shape but do not care about its content."""
+    return {"captured_at": "2020-01-01T00:00:00+00:00", "table_names": [], "table_count": 0, "per_table": {}}
+
+
+# =======================================================================================================
+# TC-19-style static proof: zero network-capable call appears in this module or the CLI script
+# =======================================================================================================
+
+
+def test_module_imports_no_network_capable_import():
+    result = jsgv.confirm_no_network_capable_import(MODULE_PATH)
+    assert result["clean"], result
+
+
+def test_cli_script_imports_no_network_capable_import():
+    result = jsgv.confirm_no_network_capable_import(CLI_SCRIPT_PATH)
+    assert result["clean"], result
+
+
+def test_network_capable_import_check_FAILS_on_a_file_that_imports_a_network_library(tmp_path):
+    """iter-22 AUDIT: the two AG-9 tests above only ever assert `clean is True`, so hardwiring
+    `confirm_no_network_capable_import` to return `clean: True` left the whole suite green (proven by the
+    audit's own mutation run). AG-9 is a *critical* anti-goal and this check feeds `verify_raw_inputs`'s
+    `ok` -- it must be provably falsifiable, not merely correct-looking."""
+    offender = tmp_path / "networky.py"
+    offender.write_text("import requests\nfrom urllib import request\n")
+    result = jsgv.confirm_no_network_capable_import(offender)
+    assert result["clean"] is False
+    assert result["per_file"][str(offender)]["network_hits"] == ["requests", "urllib"]
+    # and the clean/dirty distinction really is per-file, not a global constant
+    mixed = jsgv.confirm_no_network_capable_import(MODULE_PATH, offender)
+    assert mixed["clean"] is False
+    assert mixed["per_file"][str(MODULE_PATH)]["clean"] is True
+
+
+# =======================================================================================================
+# TC-1 / TC-2 -- preflight gate
+# =======================================================================================================
+
+
+@pytest.mark.parametrize(
+    "boundary_ok, stage_d_e_ok, identity_ok, manifest_ok, expected",
+    [
+        (True, True, True, True, True),
+        (False, True, True, True, False),
+        (True, False, True, True, False),
+        (True, True, False, True, False),
+        (True, True, True, False, False),
+    ],
+)
+def test_preflight_gate_requires_all_four_checks(boundary_ok, stage_d_e_ok, identity_ok, manifest_ok, expected):
+    gate = jsgv.stage_g_preflight_gate_verdict(
+        boundary_recheck={"ok": boundary_ok}, stage_d_e_check={"ok": stage_d_e_ok},
+        identity_check={"ok": identity_ok}, manifest_check={"ok": manifest_ok},
+    )
+    assert gate["proceed"] is expected
+    if not expected:
+        assert gate["blocking_reasons"]
+    else:
+        assert gate["blocking_reasons"] == []
+
+
+# =======================================================================================================
+# TC-3 -- verify_raw_inputs
+# =======================================================================================================
+
+
+def test_tc3_raw_inputs_matches_when_fingerprint_equal(engine, cfg):
+    with Session(engine) as session:
+        _mk_prices(session, "AAA", date(2024, 1, 1), 5)
+        certified = data_manager if False else None  # noqa: F841 -- placeholder, replaced below
+    with Session(engine) as session:
+        from app.engine import j11_maintenance
+        fresh = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        result = jsgv.verify_raw_inputs(
+            session, certified_daily_prices_fingerprint=fresh["fingerprint"],
+            module_and_script_paths=(MODULE_PATH,),
+        )
+    assert result["ok"] is True
+    assert result["fingerprint_matches"] is True
+    assert "recipe" in result and result["recipe"]
+
+
+def test_tc3_raw_inputs_fails_when_fingerprint_mismatched(engine):
+    with Session(engine) as session:
+        _mk_prices(session, "AAA", date(2024, 1, 1), 5)
+        result = jsgv.verify_raw_inputs(
+            session, certified_daily_prices_fingerprint="not-the-real-fingerprint",
+            module_and_script_paths=(MODULE_PATH,),
+        )
+    assert result["ok"] is False
+    assert result["fingerprint_matches"] is False
+
+
+# =======================================================================================================
+# TC-4 -- verify_snapshot_scope, the ids+evidence membership rule (never identity alone)
+# =======================================================================================================
+
+
+def test_tc4_snapshot_scope_maps_expected_ids_one_to_one(engine):
+    frozen_identity = "frozen-abc"
+    expected_run_id_by_date = {}
+    with Session(engine) as session:
+        for one_date in INCIDENT_DATES:
+            run = _mk_run(session, one_date, engine_identity_value=frozen_identity)
+            expected_run_id_by_date[one_date.isoformat()] = run.id
+        session.commit()
+    with Session(engine) as session:
+        from app.engine import j11_maintenance
+        sweep = j11_maintenance.capture_full_table_sweep(session)
+        result = jsgv.verify_snapshot_scope(
+            session, expected_run_id_by_date=expected_run_id_by_date,
+            iter18_pre_stage_d_sweep=_empty_sweep(), live_full_table_sweep=sweep,
+        )
+    assert result["complete_11_of_11"] is True
+    assert result["per_date_ok"] is True
+    for iso, rec in result["per_date"].items():
+        assert rec["ok"] is True
+
+
+def test_tc4_a_twelfth_run_sharing_the_frozen_identity_but_a_different_date_is_excluded(engine):
+    """The owner's binding membership rule: identity alone can never carry membership. A 12th run sharing
+    the IDENTICAL frozen engine_identity but whose date is NOT one of the 11 incident dates must be
+    structurally invisible to verify_snapshot_scope -- proven here by constructing exactly that fixture
+    and asserting the function's result never references it."""
+    frozen_identity = "frozen-abc"
+    expected_run_id_by_date = {}
+    with Session(engine) as session:
+        for one_date in INCIDENT_DATES:
+            run = _mk_run(session, one_date, engine_identity_value=frozen_identity)
+            expected_run_id_by_date[one_date.isoformat()] = run.id
+        # the 12th run: SAME identity, a date well outside the incident set
+        outsider = _mk_run(session, date(2027, 1, 4), engine_identity_value=frozen_identity)
+        session.commit()
+        outsider_id = outsider.id
+    with Session(engine) as session:
+        from app.engine import j11_maintenance
+        sweep = j11_maintenance.capture_full_table_sweep(session)
+        result = jsgv.verify_snapshot_scope(
+            session, expected_run_id_by_date=expected_run_id_by_date,
+            iter18_pre_stage_d_sweep=_empty_sweep(), live_full_table_sweep=sweep,
+        )
+    assert result["complete_11_of_11"] is True
+    assert result["per_date_ok"] is True
+    assert len(result["per_date"]) == 11
+    assert all(rec["observed_ids"] != [outsider_id] for rec in result["per_date"].values())
+    assert outsider_id not in {v for rec in result["per_date"].values() for v in rec["observed_ids"]}
+
+
+def test_tc4_snapshot_scope_fails_when_an_incident_date_maps_to_the_wrong_id(engine):
+    expected_run_id_by_date = {}
+    with Session(engine) as session:
+        for one_date in INCIDENT_DATES:
+            run = _mk_run(session, one_date)
+            expected_run_id_by_date[one_date.isoformat()] = run.id + 999  # deliberately wrong
+        session.commit()
+    with Session(engine) as session:
+        from app.engine import j11_maintenance
+        sweep = j11_maintenance.capture_full_table_sweep(session)
+        result = jsgv.verify_snapshot_scope(
+            session, expected_run_id_by_date=expected_run_id_by_date,
+            iter18_pre_stage_d_sweep=_empty_sweep(), live_full_table_sweep=sweep,
+        )
+    assert result["per_date_ok"] is False
+    assert result["ok"] is False
+
+
+# =======================================================================================================
+# TC-6 -- verify_forward_returns: population (a) matches, population (b) zero delta is CORRECT
+# =======================================================================================================
+
+
+def test_tc6_forward_returns_population_b_zero_delta_scored_as_correct(engine, cfg):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 8, 12))
+        # enough post-run trading days for horizon=1 to be genuinely observable (otherwise
+        # population_c_latest_run_observable_ceiling_respected correctly flags an inconsistent fixture --
+        # a forward-return row existing with zero observable days after it -- as a real failure).
+        _mk_prices(session, "AAA", date(2026, 8, 13), 5)
+        _mk_forward_return(session, run, "AAA", horizon=1)
+        session.commit()
+        run_id = run.id
+
+    stage_e_report = {
+        "population_a_rebuilt_incident_runs": {str(run_id): {"pre": 0, "post": 1, "newly_inserted": 1}},
+        "population_a_total_newly_inserted": 1,
+        "population_b_retained_run_holes": {"pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {}},
+    }
+    with Session(engine) as session:
+        result = jsgv.verify_forward_returns(
+            session, incident_run_ids=[run_id], stage_e_population_report=stage_e_report,
+        )
+    assert result["population_b_is_zero_correct_outcome"] is True
+    assert result["population_b_delta_from_pre_stage_e_baseline"] == 0
+    assert result["checks"]["population_a_matches_stage_e_recorded_fill"] is True
+    assert result["ok"] is True
+
+
+def test_tc6_forward_returns_fails_when_population_a_count_drifts_from_recorded(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 8, 12))
+        # NO forward return inserted -- live count 0, but the recorded baseline claims 1
+        session.commit()
+        run_id = run.id
+
+    stage_e_report = {
+        "population_a_rebuilt_incident_runs": {str(run_id): {"pre": 0, "post": 1, "newly_inserted": 1}},
+        "population_a_total_newly_inserted": 1,
+        "population_b_retained_run_holes": {"pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {}},
+    }
+    with Session(engine) as session:
+        result = jsgv.verify_forward_returns(
+            session, incident_run_ids=[run_id], stage_e_population_report=stage_e_report,
+        )
+    assert result["checks"]["population_a_matches_stage_e_recorded_fill"] is False
+    assert result["ok"] is False
+
+
+def test_forward_returns_fails_when_a_new_hole_appears_since_stage_e(engine):
+    """A NON-zero population (b) delta -- something wrote a forward return on a retained run measuring
+    into an incident date SINCE Stage E's own recorded baseline -- must be a real, falsifiable FAIL, never
+    silently treated as fine."""
+    incident_date = INCIDENT_DATES[0]
+    with Session(engine) as session:
+        retained_run = _mk_run(session, date(2026, 1, 1))
+        _mk_forward_return(session, retained_run, "AAA", measured_date=incident_date)
+        session.commit()
+        retained_run_id = retained_run.id
+
+    stage_e_report = {
+        "population_a_rebuilt_incident_runs": {},
+        "population_a_total_newly_inserted": 0,
+        "population_b_retained_run_holes": {
+            "pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {},
+        },
+    }
+    with Session(engine) as session:
+        result = jsgv.verify_forward_returns(
+            session, incident_run_ids=[], stage_e_population_report=stage_e_report,
+        )
+    assert result["population_b_delta_from_pre_stage_e_baseline"] == 1
+    assert result["population_b_is_zero_correct_outcome"] is False
+    assert result["ok"] is False
+
+
+# =======================================================================================================
+# TC-7 -- verify_manifests: direct SQL only, minting trap avoided
+# =======================================================================================================
+
+
... [diff_bound] apps/backend/tests/test_j11_stage_g_verify.py: 1087 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_g_verify_cli_script.py b/apps/backend/tests/test_j11_stage_g_verify_cli_script.py
new file mode 100644
index 00000000..097242f5
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_g_verify_cli_script.py
@@ -0,0 +1,176 @@
+"""goal-market-compass iter-22 -- J-11 Stage G FULL VERIFICATION CLI control-flow tests
+(`scripts/run_j11_stage_g_verify.py`), TC-27 plus the stop-before-write control-flow proofs this
+iteration's own dev handoff relies on.
+
+`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and
+`jsc.db_file_fingerprint`) is patched to a mock before `main()` runs, mirroring
+`test_j11_stage_f_execute_cli_script.py`'s exact idiom. These tests exercise CONTROL FLOW only (the
+argparse gating, the collision guard, and the missing-required-evidence stop) -- never real database I/O,
+and never the full happy-path pipeline (that composition is already unit-tested function-by-function in
+`test_j11_stage_g_verify.py`, and integration-proven by the live --confirm run cited in the dev handoff)."""
+from __future__ import annotations
+
+import importlib.util
+import sys
+from pathlib import Path
+from unittest import mock
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_g_verify.py"
+_MODULE_NAME = "run_j11_stage_g_verify_under_test"
+
+
+def _load_script_module():
+    """A REAL module object via `importlib` (never `runpy.run_path`), so
+    `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the script's top-level code
+    makes to that name -- mirrors `test_j11_stage_f_execute_cli_script.py`'s own loader exactly."""
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
+# --- TC-27: missing --confirm -- NO database interaction of any kind -----------------------------------
+
+
+def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_g_verify.py"])  # no --confirm
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+
+
+def test_missing_confirm_never_calls_load_config(monkeypatch, script_ns):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_g_verify.py", "--evidence-dir", "/tmp/whatever"])
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_load_config.assert_not_called()
+
+
+# --- TC-27: --confirm but no --evidence-dir -- refuses before config/engine construction ----------------
+
+
+def test_confirm_without_explicit_evidence_dir_refuses_before_config_construction(monkeypatch, script_ns, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_g_verify.py", "--confirm"])
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    mock_get_engine.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
+# --- collision guard: a pre-existing output file refuses before any DB interaction -----------------------
+
+
+def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    evidence_dir.mkdir()
+    (evidence_dir / "j11-stage-g-verify-outcome.json").write_text("{}")  # a prior run's leftover
+
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_stage_g_verify.py", "--confirm", "--evidence-dir", str(evidence_dir)],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    mock_get_engine.assert_not_called()
+    assert "already contains" in capsys.readouterr().err
+
+
+def test_collision_guard_checks_every_declared_output_filename(script_ns, tmp_path):
+    """Every filename this script promises to write (OUTPUT_FILENAMES) is actually covered by the
+    collision guard -- a filename added to one list but not the other would silently let a stale file
+    survive a "fresh evidence dir" run, exactly the class of bug iterations 19-21 were flagged for."""
+    for name in script_ns.OUTPUT_FILENAMES:
+        evidence_dir = tmp_path / f"evidence_{name}"
+        evidence_dir.mkdir()
+        (evidence_dir / name).write_text("{}")
+        colliding = script_ns._refuse_if_evidence_files_exist(evidence_dir, script_ns.OUTPUT_FILENAMES)
+        assert name in colliding
+
+
+# --- missing required historical evidence inputs -- stops before the preflight even reads the DB --------
+
+
+def test_missing_required_evidence_inputs_stops_before_boundary_recheck(monkeypatch, script_ns, tmp_path, capsys):
+    """When the caller-supplied historical evidence paths (Stage D's frozen identity, Stage D's
+    regeneration, Stage E's population report, the certified baseline, iteration 18's sweep, iteration
+    10's pre-reset inventory) cannot ALL be loaded, the script must stop before EVEN the first read-only
+    preflight check runs -- never proceed on partial/fabricated evidence."""
+    evidence_dir = tmp_path / "evidence"
+
+    mock_load_config = mock.MagicMock(name="load_config")
+    mock_load_config.return_value.database.url = "sqlite:///:memory:"
+    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
+    monkeypatch.setattr(script_ns, "resolve_database_url", mock.MagicMock(return_value="sqlite:///:memory:"))
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    mock_recheck = mock.MagicMock(name="recheck_maintenance_boundary_and_guard")
+    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_recheck)
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))
+
+    # every --*-path flag points at a nonexistent file -- _load_json returns None for all of them
+    nonexistent = tmp_path / "does-not-exist.json"
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_stage_g_verify.py", "--confirm", "--evidence-dir", str(evidence_dir),
+            "--stage-d-frozen-identity-path", str(nonexistent),
+            "--stage-d-regeneration-path", str(nonexistent),
+            "--stage-e-population-report-path", str(nonexistent),
+            "--stage-f-dispositions-path", str(nonexistent),
+            "--certified-baseline-path", str(nonexistent),
+            "--pre-reset-inventory-path", str(nonexistent),
+            "--iter18-pre-stage-d-sweep-path", str(nonexistent),
+        ],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 1
+    mock_recheck.assert_not_called()  # the preflight's first read-only check never even ran
+    stderr = capsys.readouterr().err
+    assert "missing" in stderr.lower()
```
