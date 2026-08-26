# Iteration diff (bounded)

Files changed: 4. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_stage_d_execute.py` (171 lines not shown)
- `apps/backend/tests/test_j11_stage_d_execute.py` (326 lines not shown)

```diff
diff --git a/apps/backend/app/engine/j11_stage_d_execute.py b/apps/backend/app/engine/j11_stage_d_execute.py
new file mode 100644
index 00000000..8be314a9
--- /dev/null
+++ b/apps/backend/app/engine/j11_stage_d_execute.py
@@ -0,0 +1,565 @@
+"""app.engine.j11_stage_d_execute -- J-11 Stage D EXECUTION (goal-market-compass iter-19).
+
+`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED"
+(owner, 2026-08-26) authorizes the live canonical regeneration of the 11 incident dates'
+`ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` state. `j11_stage_d.py` stays
+COMPLETELY UNCHANGED by this module -- it is deliberately readiness-only ("It performs NO Stage D
+execution"). This module is the actual write path: it COMPOSES `j11_stage_d.py`'s already-built
+identity/preflight/check functions, `j11_avb_diagnostic.py`'s classification pipeline,
+`j11_preboot_guard.py`'s live guard, and `scanner.run_scan` -- never a second implementation of any
+of those.
+
+Sequence (mirrors the plan's own ordering, and `run_j11_stage_c_bounded_clear.py`'s "evidence
+persisted before the destructive step" idiom):
+
+  1. Fresh, READ-ONLY preflight -- `j11_stage_d.capture_stage_d_preflight` /
+     `compare_stage_d_preflight_to_certified` / `stage_d_preflight_verdict` against the certified
+     Stage-C/AVB-correction baseline, PLUS a fresh read-only AVB reclassification
+     (`run_fresh_avb_reclassification`, the SAME call sequence
+     `run_j11_iter17_stage_d_readiness.py` established) PLUS a fresh read-only re-verification that
+     the `j11-incident-recovery` maintenance boundary is active with EXACTLY
+     `j11_maintenance.INCIDENT_DATES` and the live guard blocks all of them
+     (`recheck_maintenance_boundary_and_guard`). `stage_d_execution_gate_verdict` combines the three
+     into the single go/no-go: proceed ONLY if the preflight comparison passes AND the AVB
+     classification is EXACTLY `AVB-A` AND the boundary/guard re-check agrees -- stricter than (and
+     distinct from) `j11_stage_d.stage_d_readiness_verdict`'s broader AVB-A/AVB-B "ready" concept,
+     which never authorizes anything on its own.
+  2. Freeze ONE fresh execution identity -- `freeze_fresh_stage_d_execution_identity` calls
+     `j11_stage_d.freeze_stage_d_attempt_identity` DIRECTLY (never the `readiness_time_only`
+     wrapper), immediately before the first write. `compare_identity_against_historical` reports an
+     HONEST equal-or-not comparison against every historical identity value the caller supplies --
+     see the module note below on why an EQUAL `engine_identity` value is an expected, non-blocking
+     outcome here, not a failure.
+  3. Per-date loop (`execute_stage_d_regeneration` / `execute_stage_d_for_date`) -- ascending
+     chronological order over the supplied incident dates: confirm no `ScannerRun` already exists ->
+     Check (B) `check_identity_before_date` -> `scanner.run_scan` called DIRECTLY (never through
+     `data_manager`/`warmup`/`forward_testing`) -> Check (C) `check_identity_after_persist`. STOPS
+     the WHOLE attempt at the first failing precondition/check -- no further date attempted, no
+     resume-from-next-date on any retry.
+  4. Post-execution mutation accounting (`build_stage_d_mutation_accounting`) -- proves
+     `changed_existing_tables` is a subset of exactly `{scanner_runs, scanner_results, sector_scores,
+     theme_scores}`, `next_session_manifests` is byte-unchanged, the 34 iteration-10-era
+     `6261ca17...` runs and every NULL-stamped pre-stamping-era row are byte-unchanged (by a direct
+     query, never by absence from a diff), and `daily_prices`/`data_provider_runs`/`watchlist`/
+     `maintenance_boundaries` show zero fingerprint change.
+
+**Why an EQUAL `engine_identity` value against the iteration-14/16/17 readiness observation is
+expected, not a bug (verified empirically before this module was written, 2026-08-26):**
+`engine_identity.compute_engine_identity` is a PURE function of exactly three files
+(`compass.py`, `session_delta.py`, `engine_identity.py`) plus three config keys
+(`compass.selection`, `compass.delta`, `compass.manifest`) -- none of which this iteration, or any
+of iterations 15-18 (all J-11-only maintenance), touched; the last commit to touch `compass.py` at
+all was iteration 12, already reflected in iteration 14's own frozen value. A live, independent
+recomputation on this iteration's own commit reproduces `53d2ffd1...` byte-for-byte (differs
+CORRECTLY from iteration 10's `6261ca17...`, which predates iteration 12's compass.py changes).
+This module's Guardrails explicitly forbid touching `compass.py` to manufacture a different hash.
+TC-3's own wording governs: the comparison must be "honestly compared (equal-or-not, stated either
+way)" -- never silently assumed distinct, but never required to differ either. The per-run
+consistency checks (A)/(B)/(C) this module relies on for safety compare the frozen identity against
+itself WITHIN this one attempt, never against a historical attempt's value -- an equal
+`engine_identity` carries no safety implication, since iteration 14/16/17 never wrote a single
+`ScannerRun` row (readiness-only) and so never created any ambiguity in the live data.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Any, Optional
+
+from sqlalchemy import or_
+from sqlmodel import Session, select
+
+from app.config import Config, get_config
+from app.engine import engine_identity
+from app.engine import j11_avb_diagnostic as diag
+from app.engine import j11_maintenance
+from app.engine import j11_preboot_guard as guard
+from app.engine import j11_schema_migration as migration
+from app.engine import j11_stage_d as jsd
+from app.engine import scanner
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.engine.prices import bar_cache
+from app.models import MaintenanceBoundary, ScannerRun
+
+# The five tables THIS module's one authorized write may ever touch (ruling 6: "Stage D may create
+# ONLY the canonical derived state required for the eleven authorized incident dates, through the
+# existing canonical scanner path"). Mirrors `j11_stage_c._CHILD_MODELS`'s table-name literal set.
+STAGE_D_WRITE_TABLES: tuple[str, ...] = ("scanner_runs", "scanner_results", "sector_scores", "theme_scores")
+
+# Same historical-fact literal `j11_stage_d.py` uses for the 34 surviving iteration-10 runs -- not a
+# reusable threshold (test_no_magic_numbers.CALC_FILES excludes this module for the same reason it
+# excludes every other j11_*.py file: nothing here is a scoring weight, band edge, or decision cutoff).
+_LEGACY_ATTEMPT_IDENTITY_PREFIX = "6261ca17"
+
+# The Stage D EXECUTION gate (distinct from `jsd.stage_d_readiness_verdict`'s broader "ready" concept,
+# which accepts AVB-A OR AVB-B and never authorizes anything): this iteration's own What-to-Build gate
+# requires the classification to be EXACTLY AVB-A.
+_REQUIRED_AVB_CLASSIFICATION = "AVB-A"
+
+# The fixed, literal AVB stored-series inspection window `run_j11_iter17_stage_d_readiness.py`
+# established -- a bounded historical-evidence window for THIS incident's diagnostic, not a reusable
+# threshold (same posture as `j11_avb_diagnostic.CALIBRATION_DATES`/`RECOVERED_DATES`).
+_AVB_STORED_SERIES_WINDOW_START = date(2026, 6, 1)
+_AVB_STORED_SERIES_WINDOW_END = date(2026, 12, 31)
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+# ================================================================================================
+# Step 1a -- fresh, read-only maintenance-boundary + live-guard re-verification
+# ================================================================================================
+
+
+def recheck_maintenance_boundary_and_guard(
+    session: Session,
+    incident_dates: tuple[date, ...] = INCIDENT_DATES,
+    *,
+    boundary_name: str = guard.J11_INCIDENT_BOUNDARY_NAME,
+) -> dict:
+    """Fresh, READ-ONLY re-verification that the named maintenance boundary is `active=1`, its
+    persisted date-set is EXACTLY `incident_dates`, and the live fail-closed guard
+    (`j11_preboot_guard.evaluate_boundary_for_date_fail_closed`) reports `blocked=True` for every one
+    of them. Never re-arms, never disarms, never writes anything -- read-only re-verification only,
+    mirroring every other J-11 precondition function's posture."""
+    row = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == boundary_name)).first()
+    expected_dates = sorted(d.isoformat() for d in incident_dates)
+
+    row_active = False
+    persisted_dates: list[str] = []
+    if row is not None:
+        row_active = bool(row.active)
+        try:
+            parsed = json.loads(row.quarantined_dates_json)
+            if isinstance(parsed, list) and all(isinstance(d, str) for d in parsed):
+                persisted_dates = sorted(parsed)
+        except (TypeError, ValueError, json.JSONDecodeError):
+            persisted_dates = []
+    exact_date_set_match = row is not None and persisted_dates == expected_dates
+
+    per_date_guard: dict[str, dict] = {
+        one_date.isoformat(): guard.evaluate_boundary_for_date_fail_closed(session, one_date)
+        for one_date in incident_dates
+    }
+    all_dates_blocked = bool(per_date_guard) and all(r["blocked"] for r in per_date_guard.values())
+
+    ok = row is not None and row_active and exact_date_set_match and all_dates_blocked
+    return {
+        "checked_at": _now_iso(),
+        "boundary_name": boundary_name,
+        "boundary_row_present": row is not None,
+        "boundary_active": row_active,
+        "persisted_dates": persisted_dates,
+        "expected_dates": expected_dates,
+        "exact_date_set_match": exact_date_set_match,
+        "per_date_guard_result": per_date_guard,
+        "all_dates_blocked": all_dates_blocked,
+        "ok": ok,
+    }
+
+
+# ================================================================================================
+# Step 1b -- fresh, read-only AVB reclassification (same call sequence as
+# run_j11_iter17_stage_d_readiness.py; never a second implementation of any diag.* function)
+# ================================================================================================
+
+
+def run_fresh_avb_reclassification(
+    session: Session,
+    config: Optional[Config] = None,
+    *,
+    provider_fetch_evidence_path: Path,
+    j10_evidence_path: Path,
+) -> dict:
+    """Fresh, READ-ONLY re-derivation of the AVB bridge/volume classification. Loads the
+    already-committed AG-9 dated-exception-#2 provider-fetch evidence and the persisted J-10 evidence
+    (never re-fetches -- AG-9 stays closed), classifies the stored local convention, traces the
+    decision impact through `j11_avb_diagnostic.trace_universe_resolver_impact` /
+    `trace_scoring_and_selection_impact` WITH `volume_override` on both (the SAME fix
+    `run_j11_iter17_stage_d_readiness.py` applied), then `classify_avb`. Never mutates
+    `daily_prices`; calls no fetch/recovery function of any kind."""
+    cfg = config or get_config()
+    fetch_evidence = json.loads(Path(provider_fetch_evidence_path).read_text())
+    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
+    evidence_row = diag.load_j10_avb_evidence(j10_evidence_path)
+    bridge_factor = evidence_row["bridge_factor"]
+
+    volume_override: dict = {}
+    for one_date in diag.RECOVERED_DATES:
+        entry = provider_evidence_by_date.get(one_date.isoformat())
+        if entry is not None and entry.get("volume") is not None:
+            volume_override[one_date] = entry["volume"]
+
+    stored_series = diag.fetch_avb_stored_series(
+        session, _AVB_STORED_SERIES_WINDOW_START, _AVB_STORED_SERIES_WINDOW_END
+    )
+    local_convention = diag.classify_local_convention_with_volume_evidence(
+        stored_series, evidence_row, provider_evidence_by_date
+    )
+
+    if set(volume_override) != set(diag.RECOVERED_DATES):
+        # Incomplete override evidence -- fail closed to AVB-D (insufficient evidence), never guess.
+        classification = {
+            "classification": "AVB-D",
+            "stage_d_ready_per_avb": False,
+            "reasoning": (
+                "volume_override does not cover both RECOVERED_DATES -- the committed provider-fetch "
+                "evidence is missing volume for at least one of them; refusing to classify on "
+                "incomplete override evidence"
+            ),
+        }
+        decision_impact_by_date: dict = {}
+    else:
+        decision_impact_by_date = {}
+        for one_date in diag.RECOVERED_DATES:
+            key = one_date.isoformat()
+            ur_impact = diag.trace_universe_resolver_impact(
+                session, cfg, one_date, bridge_factor, volume_override=volume_override
+            )
+            scoring_impact = diag.trace_scoring_and_selection_impact(
+                session, cfg, one_date, bridge_factor, volume_override=volume_override
+            )
+            decision_impact_by_date[key] = {
+                "universe_resolver": ur_impact, "scoring_and_selection": scoring_impact,
+            }
+        classification = diag.classify_avb(local_convention, decision_impact_by_date)
+        if not fetch_evidence.get("sufficient_evidence", False):
+            classification = dict(classification)
+            classification["classification"] = "AVB-D"
+            classification["stage_d_ready_per_avb"] = False
+            classification["reasoning"] = (
+                "the committed AG-9 dated-exception-#2 fetch evidence does not itself report "
+                "sufficient_evidence=true -- classifying AVB-D per the amendment's own fail-closed rule"
+            )
+
+    return {
+        "generated_at": _now_iso(),
+        "j10_evidence_path": str(j10_evidence_path),
+        "provider_fetch_evidence_path": str(provider_fetch_evidence_path),
+        "provider_fetch_evidence_sufficient": fetch_evidence.get("sufficient_evidence"),
+        "bridge_factor": bridge_factor,
+        "stored_series_window": {
+            "start": _AVB_STORED_SERIES_WINDOW_START.isoformat(),
+            "end": _AVB_STORED_SERIES_WINDOW_END.isoformat(),
+            "row_count": len(stored_series),
+        },
+        "local_convention": local_convention,
+        "volume_override_by_date": {d.isoformat(): v for d, v in volume_override.items()},
+        "decision_impact_by_date": decision_impact_by_date,
+        "classification": classification,
+    }
+
+
+# ================================================================================================
+# Step 1c -- the combined Stage D EXECUTION gate
+# ================================================================================================
+
+
+def stage_d_execution_gate_verdict(*, preflight_verdict: dict, avb_classification: str, boundary_recheck: dict) -> dict:
+    """The single go/no-go decision for Stage D EXECUTION -- requires the preflight comparison to
+    have passed, the AVB classification to be EXACTLY `AVB-A`, and the boundary/guard re-check to
+    agree. Any one failing means `proceed: False`, and the caller MUST perform zero writes."""
+    preflight_ok = bool(preflight_verdict.get("passed"))
+    avb_ok = avb_classification == _REQUIRED_AVB_CLASSIFICATION
+    boundary_ok = bool(boundary_recheck.get("ok"))
+    proceed = preflight_ok and avb_ok and boundary_ok
+
+    blocking_reasons: list[str] = []
+    if not preflight_ok:
+        blocking_reasons.append(f"preflight_gate_failed:{preflight_verdict.get('reason')}")
+    if not avb_ok:
+        blocking_reasons.append(f"avb_classification_not_avb_a:{avb_classification}")
+    if not boundary_ok:
+        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")
+
+    return {
+        "generated_at": _now_iso(),
+        "proceed": proceed,
+        "preflight_ok": preflight_ok,
+        "avb_classification": avb_classification,
+        "avb_ok": avb_ok,
+        "boundary_ok": boundary_ok,
+        "blocking_reasons": blocking_reasons,
+    }
+
+
+# ================================================================================================
+# Step 2 -- freeze ONE fresh execution identity + honest historical comparison
+# ================================================================================================
+
+
+def freeze_fresh_stage_d_execution_identity(
+    session: Session,
+    config: Optional[Config] = None,
+    *,
+    git_head: Optional[str] = None,
+    goal_md_text: Optional[str] = None,
+) -> dict:
+    """Freezes ONE fresh Stage D EXECUTION attempt identity, immediately before the first write --
+    calls `j11_stage_d.freeze_stage_d_attempt_identity` DIRECTLY (never the `readiness_time_only`
+    wrapper), per the owner ruling's item 2. A thin, explicitly-labeled call site; introduces no new
+    identity-computation logic of its own."""
+    frozen = jsd.freeze_stage_d_attempt_identity(session, config, git_head=git_head, goal_md_text=goal_md_text)
+    return {**frozen, "execution_identity": True, "readiness_time_only": False}
+
+
+def compare_identity_against_historical(fresh_engine_identity: str, historical: dict[str, Optional[str]]) -> dict:
+    """Honest, per-label comparison of the fresh `engine_identity` against every historical value the
+    caller supplies (e.g. `{"iteration_10": "6261ca17...", "iteration_14": "53d2ffd1...", ...}`,
+    INJECTED by the caller -- this function performs no file I/O). Every comparison is stated
+    explicitly, whichever way it falls (TC-3: "honestly compared (equal-or-not, stated either way)")
+    -- an equal value is recorded, never silently hidden or treated as an error by this function
+    itself (see the module docstring for why an equal `engine_identity` against the
+    iteration-14/16/17 readiness observation is an expected, non-blocking outcome)."""
+    comparisons = {
+        label: {
+            "historical_value": value,
+            "matches_fresh": value is not None and value == fresh_engine_identity,
+        }
+        for label, value in historical.items()
+    }
+    return {
+        "generated_at": _now_iso(),
+        "fresh_engine_identity": fresh_engine_identity,
+        "comparisons": comparisons,
+        "any_historical_match": any(c["matches_fresh"] for c in comparisons.values()),
+    }
+
+
+# ================================================================================================
+# Step 3 -- the per-date write loop (the ONE authorized write sequence)
+# ================================================================================================
+
+
+def confirm_no_existing_scanner_run(session: Session, one_date: date) -> dict:
+    """The pre-write guard every incident date must pass before Check (B)/`run_scan`: a `ScannerRun`
+    unexpectedly already existing for this date STOPS the whole attempt (the fresh preflight already
+    proved zero rows at gate time -- a row appearing here means live state moved between the gate and
+    this date's turn in the loop; never silently reused, never silently treated as this attempt's
+    own)."""
+    existing = session.exec(
+        select(ScannerRun.id, ScannerRun.engine_identity).where(ScannerRun.asof_date == one_date)
+    ).first()
+    return {
+        "date": one_date.isoformat(),
+        "already_exists": existing is not None,
+        "existing_run_id": int(existing[0]) if existing is not None else None,
+        "existing_engine_identity": existing[1] if existing is not None else None,
+    }
+
+
+def execute_stage_d_for_date(session: Session, one_date: date, frozen_identity: dict, config: Config) -> dict:
+    """The per-date sequence: the pre-existing-run guard -> Check (B) `check_identity_before_date` ->
+    `scanner.run_scan` (called DIRECTLY -- never through `data_manager`'s backfill/ingest-finalize
+    path, never through `warmup`/`forward_testing`) -> Check (C) `check_identity_after_persist`.
+    Stops (`stopped: True`) at the FIRST failing precondition/check -- never proceeds past one."""
+    pre_check = confirm_no_existing_scanner_run(session, one_date)
+    if pre_check["already_exists"]:
+        return {
+            "date": one_date.isoformat(), "stopped": True,
+            "stop_reason": "scanner_run_already_exists_before_write", "pre_check": pre_check,
+        }
+
+    current_identity = engine_identity.compute_engine_identity(config)
+    check_b = jsd.check_identity_before_date(frozen_identity, current_identity, one_date)
+    if not check_b["ok"]:
+        return {
+            "date": one_date.isoformat(), "stopped": True, "stop_reason": "check_b_failed",
+            "pre_check": pre_check, "check_b": check_b,
+        }
+
+    run = scanner.run_scan(session, one_date, config)
+
+    check_c = jsd.check_identity_after_persist(frozen_identity, run.engine_identity, run.id, one_date)
+    if not check_c["ok"]:
+        return {
+            "date": one_date.isoformat(), "stopped": True, "stop_reason": "check_c_failed",
+            "pre_check": pre_check, "check_b": check_b, "check_c": check_c, "run_id": run.id,
+        }
+
+    return {
+        "date": one_date.isoformat(), "stopped": False, "run_id": run.id,
+        "pre_check": pre_check, "check_b": check_b, "check_c": check_c,
+    }
+
+
+def execute_stage_d_regeneration(
+    session: Session, incident_dates: tuple[date, ...], frozen_identity: dict, config: Config,
+) -> dict:
+    """The whole-attempt per-date loop, ascending chronological order over EVERY date in
+    `incident_dates`. STOPS the ENTIRE attempt at the first failing date -- no further date
+    attempted, no resume-from-next-date on any later retry (a future retry is a full Stage C->G
... [diff_bound] apps/backend/app/engine/j11_stage_d_execute.py: 171 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_stage_d_execute.py b/apps/backend/scripts/run_j11_stage_d_execute.py
new file mode 100644
index 00000000..f36a9aac
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_d_execute.py
@@ -0,0 +1,370 @@
+"""goal-market-compass iter-19 -- J-11 Stage D EXECUTION: the ONE owner-authorized live canonical
+regeneration of the eleven incident dates' `ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`
+state (`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED",
+owner 2026-08-26).
+
+Mirrors `run_j11_stage_c_bounded_clear.py`'s idiom exactly: NO database interaction of any kind, not
+even a read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the destructive
+step so a mid-run crash still leaves a forensic trail; the completion/outcome marker is written ONLY
+after full post-execution verification completes (whichever of the two honest terminal states --
+`STAGE D EXECUTED: YES` or `STAGE D EXECUTED: NO` -- that verification proves). Sequence, exactly as
+the plan's ordering requires:
+
+  1. Fresh, READ-ONLY preflight (`j11_stage_d.capture_stage_d_preflight` /
+     `compare_stage_d_preflight_to_certified` / `stage_d_preflight_verdict`) + a fresh, READ-ONLY
+     maintenance-boundary/live-guard re-check + a fresh, READ-ONLY AVB reclassification, combined into
+     ONE execution gate (`j11_stage_d_execute.stage_d_execution_gate_verdict`). STOPS here (zero
+     writes of any kind) unless the gate's `proceed` is True.
+  2. Freeze ONE fresh execution identity (`freeze_fresh_stage_d_execution_identity`), immediately
+     before the first write; an honest comparison against the iteration-10/14/16-17-18 historical
+     identity values already on disk; Check (A) `check_identity_before_first_write` as a defensive
+     sanity check the plan recommends. STOPS here (still zero regeneration writes) on any failure.
+  3. THE per-date write loop (`execute_stage_d_regeneration`) over every date in
+     `app.engine.j11_maintenance.INCIDENT_DATES`, in ascending order -- the ONE authorized write
+     sequence, calling `scanner.run_scan` directly. Stops the WHOLE attempt at the first failing
+     precondition/check.
+  4. Post-execution mutation accounting (`build_stage_d_mutation_accounting`), proving every table
+     Stage D is forbidden to touch shows zero fingerprint change, and every table it IS allowed to
+     touch changed in exactly the expected way.
+  5. The final outcome (`stage_d_execution_outcome`) is written UNCONDITIONALLY as the LAST evidence
+     artifact -- unlike `run_j11_stage_c_bounded_clear.py` (which writes a completion marker only on a
+     PASS), Stage D's own contract defines TWO honest terminal states (`YES`/`NO`), and BOTH require
+     full evidence preserved (docs/goal.md item 14) -- never a bare non-zero exit with no persisted
+     outcome record.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_execute.py \\
+        --confirm \\
+        --evidence-dir runs/goal-market-compass-iter-19
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
+from sqlmodel import Session  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import get_engine, resolve_database_url  # noqa: E402
+from app.engine import engine_identity  # noqa: E402
+from app.engine import j11_avb_correction as corr  # noqa: E402
+from app.engine import j11_avb_diagnostic as diag  # noqa: E402
+from app.engine import j11_maintenance  # noqa: E402
+from app.engine import j11_schema_migration as migration  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.engine import j11_stage_d as jsd  # noqa: E402
+from app.engine import j11_stage_d_execute as jsde  # noqa: E402
+from app.engine.j11_maintenance import INCIDENT_DATES  # noqa: E402
+from app.models import DataProviderRun, MaintenanceBoundary, NextSessionManifest, Watchlist  # noqa: E402
+
+DEFAULT_CERTIFIED_BASELINE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
+)
+DEFAULT_ITERATION_10_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-frozen-identity.json"
+)
+DEFAULT_ITERATION_14_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
+)
+# iteration 16, 17, and (by citation) 18 all carry the SAME readiness-time engine_identity value
+# (verified: nothing touched compass.py/session_delta.py/engine_identity.py or the compass.selection/
+# delta/manifest config keys across any of them) -- iteration 17's own preflight capture is the LATEST
+# re-derivation, so it is the one representative file loaded here for the "16/17/18" comparison label.
+DEFAULT_ITERATION_16_17_18_PREFLIGHT_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-17" / "j11-stage-d-preflight.json"
+)
+
+OUTPUT_FILENAMES = (
+    "j11-stage-d-execute-db-file-true-start.json",
+    "j11-stage-d-execute-preflight.json",
+    "j11-stage-d-execute-preflight-gate.json",
+    "j11-stage-d-execute-boundary-recheck.json",
+    "j11-stage-d-execute-avb-reclassification.json",
+    "j11-stage-d-execute-gate-verdict.json",
+    "j11-stage-d-execute-frozen-identity.json",
+    "j11-stage-d-execute-historical-identity-comparison.json",
+    "j11-stage-d-execute-check-a.json",
+    "j11-stage-d-execute-regeneration.json",
+    "j11-stage-d-execute-mutation-accounting.json",
+    "j11-stage-d-execute-outcome.json",
+    "j11-stage-d-execute-db-file-true-end.json",
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
+    """Mirrors the SAME collision guard `run_j11_iter17_stage_d_readiness.py`/`...iter18_...py` added
+    after a mistyped `--evidence-dir` once silently overwrote committed evidence. Pure filesystem
+    check, no database interaction."""
+    return [name for name in filenames if (evidence_dir / name).exists()]
+
+
+def _load_historical_identity(path: Path, *, json_pointer: tuple[str, ...]) -> Optional[str]:
+    """Loads one historical identity artifact and walks `json_pointer` to the `engine_identity` string.
+    Never raises on a missing file or missing key -- an absent historical artifact is recorded honestly
+    as `None`, never fabricated and never a crash."""
+    if not path.exists():
+        return None
+    try:
+        payload = json.loads(path.read_text())
+    except (OSError, json.JSONDecodeError):
+        return None
+    node = payload
+    for key in json_pointer:
+        if not isinstance(node, dict) or key not in node:
+            return None
+        node = node[key]
+    return node if isinstance(node, str) else None
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
+    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
+    parser.add_argument("--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH)
+    parser.add_argument("--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH)
+    parser.add_argument("--iteration-10-identity-path", type=Path, default=DEFAULT_ITERATION_10_IDENTITY_PATH)
+    parser.add_argument("--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH)
+    parser.add_argument(
+        "--iteration-16-17-18-preflight-path", type=Path, default=DEFAULT_ITERATION_16_17_18_PREFLIGHT_PATH,
+    )
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is the ONE owner-authorized live Stage D write "
+            "this iteration -- docs/goal.md J-11 step 11's Stage D-through-G OWNER RULING). No database "
+            "interaction, not even a read, has occurred.",
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
+    _write_json(evidence_dir / "j11-stage-d-execute-db-file-true-start.json", db_file_true_start)
+
+    engine = get_engine()  # the SAME pooled writable engine the real backend uses.
+    goal_md_text = jsc.read_goal_md_text()
+    git_head = jsc.read_git_head()
+
+    def _stop(reason: str, execution_gate: dict, boundary_recheck: "dict | None" = None) -> int:
+        outcome = jsde.stage_d_execution_outcome(
+            execution_gate=execution_gate, regeneration_result=None, mutation_accounting=None,
+        )
+        _write_json(evidence_dir / "j11-stage-d-execute-outcome.json", outcome)
+        db_file_true_end = jsc.db_file_fingerprint(db_path)
+        _write_json(evidence_dir / "j11-stage-d-execute-db-file-true-end.json", db_file_true_end)
+        print(f"STOP before any write: {reason}", file=sys.stderr)
+        # `boundary_recheck` is threaded through when the caller already computed a REAL one (both stop
+        # sites below do) so the printed MAINTENANCE BOUNDARY/LIVE PRE-BOOT GUARD lines reflect the
+        # actual fresh re-verification -- never a blind assumed-True default when real evidence exists.
+        _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
+        return 1
+
+    # === Step 1: fresh, read-only preflight + boundary/guard recheck + AVB reclassification =========
+    with Session(engine) as session:
+        preflight = jsd.capture_stage_d_preflight(
+            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
+        )
+    _write_json(evidence_dir / "j11-stage-d-execute-preflight.json", preflight)
+    print(
+        f"fresh preflight captured: manifest_row_count={preflight['manifest_row_count']} "
+        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']}",
+        file=sys.stderr,
+    )
+
+    certified = json.loads(args.certified_baseline_path.read_text())
+    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
+    preflight_verdict = jsd.stage_d_preflight_verdict(gate)
+    _write_json(evidence_dir / "j11-stage-d-execute-preflight-gate.json", {"comparison": gate, "verdict": preflight_verdict})
+    print(f"preflight comparison gate: all_invariants_hold={gate['all_invariants_hold']}", file=sys.stderr)
+
+    with Session(engine) as session:
+        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session, INCIDENT_DATES)
+    _write_json(evidence_dir / "j11-stage-d-execute-boundary-recheck.json", boundary_recheck)
+    print(
+        f"boundary/guard recheck: ok={boundary_recheck['ok']} "
+        f"all_dates_blocked={boundary_recheck['all_dates_blocked']}",
+        file=sys.stderr,
+    )
+
+    with Session(engine) as session:
+        avb_result = jsde.run_fresh_avb_reclassification(
+            session, cfg,
+            provider_fetch_evidence_path=args.provider_fetch_evidence_path,
+            j10_evidence_path=args.j10_evidence_path,
+        )
+    _write_json(evidence_dir / "j11-stage-d-execute-avb-reclassification.json", avb_result)
+    avb_classification = avb_result["classification"]["classification"]
+    print(f"fresh AVB reclassification: {avb_classification}", file=sys.stderr)
+
+    execution_gate = jsde.stage_d_execution_gate_verdict(
+        preflight_verdict=preflight_verdict, avb_classification=avb_classification, boundary_recheck=boundary_recheck,
+    )
+    _write_json(evidence_dir / "j11-stage-d-execute-gate-verdict.json", execution_gate)
+    print(f"execution gate: proceed={execution_gate['proceed']} reasons={execution_gate['blocking_reasons']}", file=sys.stderr)
+
+    if not execution_gate["proceed"]:
+        return _stop("execution gate did not proceed", execution_gate, boundary_recheck)
+
+    # === Step 2: freeze ONE fresh execution identity + honest historical comparison + Check (A) ======
+    with Session(engine) as session:
+        frozen_identity = jsde.freeze_fresh_stage_d_execution_identity(
+            session, cfg, git_head=git_head, goal_md_text=goal_md_text,
+        )
+    _write_json(evidence_dir / "j11-stage-d-execute-frozen-identity.json", frozen_identity)
+    print(f"frozen execution identity: {frozen_identity['engine_identity']}", file=sys.stderr)
+
+    historical = {
+        "iteration_10": _load_historical_identity(args.iteration_10_identity_path, json_pointer=("engine_identity",)),
+        "iteration_14": _load_historical_identity(args.iteration_14_identity_path, json_pointer=("engine_identity",)),
+        "iteration_16_17_18_readiness": _load_historical_identity(
+            args.iteration_16_17_18_preflight_path, json_pointer=("attempt_identity", "engine_identity"),
+        ),
+    }
+    identity_comparison = jsde.compare_identity_against_historical(frozen_identity["engine_identity"], historical)
+    _write_json(evidence_dir / "j11-stage-d-execute-historical-identity-comparison.json", identity_comparison)
+    print(f"historical identity comparison: {identity_comparison['comparisons']}", file=sys.stderr)
+
+    current_identity_for_check_a = engine_identity.compute_engine_identity(cfg)
+    check_a = jsd.check_identity_before_first_write(frozen_identity, current_identity_for_check_a)
+    _write_json(evidence_dir / "j11-stage-d-execute-check-a.json", check_a)
+    if not check_a["ok"]:
+        return _stop(
+            "Check (A) failed immediately after freezing -- refusing to proceed to any write",
+            execution_gate, boundary_recheck,
+        )
+
+    # === Step 3: pre-write mutation-accounting captures, THEN the one authorized write sequence ======
+    with Session(engine) as session:
+        pre_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
+        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        pre_legacy_null_fp = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
+        pre_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+        pre_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
+
+    with Session(engine) as session:
+        regen = jsde.execute_stage_d_regeneration(session, INCIDENT_DATES, frozen_identity, cfg)
+    _write_json(evidence_dir / "j11-stage-d-execute-regeneration.json", regen)
+    print(
+        f"regeneration: completed={regen['completed']} stopped_at_date={regen['stopped_at_date']} "
+        f"new_run_ids={regen['new_run_ids']}",
+        file=sys.stderr,
+    )
+
+    # === Step 4: post-write captures + mutation accounting ============================================
+    with Session(engine) as session:
+        post_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
+        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        post_legacy_null_fp = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
+        post_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+        post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
+
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-d-execute-db-file-true-end.json", db_file_true_end)
+
+    mutation_accounting = jsde.build_stage_d_mutation_accounting(
+        pre_full_table_sweep=pre_full_table_sweep, post_full_table_sweep=post_full_table_sweep,
+        pre_manifest_dump=pre_manifest_dump, post_manifest_dump=post_manifest_dump,
+        pre_legacy_null_fingerprint=pre_legacy_null_fp, post_legacy_null_fingerprint=post_legacy_null_fp,
+        pre_daily_prices=pre_daily_prices, post_daily_prices=post_daily_prices,
+        pre_provider_runs=pre_provider_runs, post_provider_runs=post_provider_runs,
+        pre_watchlist=pre_watchlist, post_watchlist=post_watchlist,
+        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump, post_maintenance_boundary_dump=post_maintenance_boundary_dump,
+        db_file_true_start=db_file_true_start, db_file_true_end=db_file_true_end,
+    )
+    _write_json(evidence_dir / "j11-stage-d-execute-mutation-accounting.json", mutation_accounting)
+    print(f"mutation accounting: all_checks_pass={mutation_accounting['all_checks_pass']}", file=sys.stderr)
+    if not mutation_accounting["all_checks_pass"]:
+        failing = [k for k, v in mutation_accounting["checks"].items() if not v]
+        print(f"FAILING CHECKS: {failing}", file=sys.stderr)
+
+    # === Final outcome -- written UNCONDITIONALLY, whichever of the two honest terminal states =========
+    outcome = jsde.stage_d_execution_outcome(
+        execution_gate=execution_gate, regeneration_result=regen, mutation_accounting=mutation_accounting,
+    )
+    _write_json(evidence_dir / "j11-stage-d-execute-outcome.json", outcome)
+    _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
+    return 0 if outcome["executed"] else 1
+
+
+def _print_terminal_lines(outcome: dict, *, boundary_recheck: "dict | None") -> None:
+    executed = bool(outcome.get("executed"))
+    boundary_active = boundary_recheck.get("boundary_active") if boundary_recheck else True
+    guard_armed = boundary_recheck.get("all_dates_blocked") if boundary_recheck else True
+    print("J-11 STAGE D AUTHORIZED: YES", file=sys.stderr)
+    print(f"J-11 STAGE D EXECUTED: {'YES' if executed else 'NO'}", file=sys.stderr)
+    print("J-11 STAGE E COMPLETE: NO", file=sys.stderr)
+    print("J-11 STAGE F COMPLETE: NO", file=sys.stderr)
+    print("J-11 STAGE G VERIFIED: NO", file=sys.stderr)
+    print("J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE", file=sys.stderr)
+    print(f"J-11 MAINTENANCE BOUNDARY: {'ACTIVE' if boundary_active else 'NOT ACTIVE'}", file=sys.stderr)
+    print(f"J-11 LIVE PRE-BOOT GUARD: {'ARMED' if guard_armed else 'NOT ARMED'}", file=sys.stderr)
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_stage_d_execute.py b/apps/backend/tests/test_j11_stage_d_execute.py
new file mode 100644
index 00000000..0ed7f132
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_d_execute.py
@@ -0,0 +1,720 @@
+"""goal-market-compass iter-19 -- J-11 Stage D EXECUTION tests (TC-1 through TC-9, TC-12, TC-13, TC-16
+from the phase spec's TESTING REQUIREMENTS; TC-10/TC-11/TC-15/TC-17/TC-18 live in the CLI-script test
+file / are proven by grep in the dev handoff).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
+pattern `test_j11_stage_d.py`/`test_j11_maintenance.py` use, never `loaded_engine` and never
+`apps/backend/data/trendora.db`.
+
+`scanner.run_scan` itself is NOT re-exercised end-to-end against the real committed seed here (that
+is `test_scanner.py`'s own, already-expensive, already-covered proof -- a single real seed-backed
+`run_scan` test module alone takes several minutes wall time, which fails docs/goal.md's own "new
+tests are synthetic-fixture" contract for a NEW test file). Instead, `scanner.run_scan` is replaced,
+for the per-date-loop tests only, with a small stand-in that calls the REAL, unmodified
+`scanner.persist_run_payload` against a hand-built MINIMAL payload -- genuinely exercises the real
+INSERT/commit/idempotent-guard/`engine_identity`-stamping code path, without the expensive
+`compute_run_payload` scoring/universe-resolution machinery. A dedicated static test
+(`test_execute_stage_d_for_date_never_imports_or_calls_data_manager_warmup_or_forward_testing`) proves
+the production module itself calls ONLY `scanner.run_scan`, never any of the forbidden alternate
+write paths.
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timedelta, timezone
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine
+
+from app.config import load_config
+from app.engine import j11_avb_diagnostic as diag
+from app.engine import j11_preboot_guard as guard
+from app.engine import j11_stage_d_execute as jsde
+from app.engine import scanner
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import DailyPrice, MaintenanceBoundary, NextSessionManifest, ScannerRun
+
+pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
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
+# --- shared helpers (mirror test_j11_stage_d.py's own _mk_run / _mk_manifest exactly) ----------------
+
+
+def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = None) -> ScannerRun:
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
+_TINY_PAYLOAD = {
+    "regime": {
+        "score": 55.0, "label": "Expansion", "components": [],
+        "breadth_above_50dma": 50.0, "breadth_above_200dma": 55.0, "new_high_low": {},
+    },
+    "sector_result": {"rows": [{
+        "ticker": "XLK", "kind": "sector", "name": "Technology", "description": "",
+        "members": [], "score": 50.0, "bucket": "Neutral", "rs_vs_spy": 0.0,
+        "dist_from_52w_high_pct": 0.0, "trend_label": "Flat", "components": {}, "rank": 1,
+    }]},
+    "theme_result": {"rows": [{
+        "slug": "ai", "name": "AI", "score": 50.0, "bucket": "Neutral", "members": [],
+        "return_1m": 0.0, "return_3m": 0.0, "breadth_pct": 0.0, "breadth_label": "Flat",
+        "trend_label": "Flat", "components": {}, "rank": 1,
+    }]},
+    "stock_result": {"benchmark": "SPY", "rows": [{
+        "ticker": "AAA", "name": "AAA Inc", "sector": "Technology",
+        "leadership": {"score": 50.0, "bucket": "Neutral"},
+        "entry_quality": {"score": 50.0, "bucket": "Neutral"},
+        "risk": {"score": 50.0, "bucket": "Neutral"},
+        "setup": {"status": "None"}, "rank": 1,
+        "vcp": {"flagged": False}, "pullback_to_rising_dma": {"flagged": False},
+        "flat_base_breakout": {"flagged": False},
+        "hv": None, "vcp_contraction": None, "downside_vol": None,
+    }]},
+    "candidate_counts": {},
+}
+
+
+def _stub_run_scan(session, asof, config=None):
+    """A small stand-in for `scanner.run_scan`, used ONLY in these fixture tests to avoid the expensive
+    `compute_run_payload` scoring machinery -- calls the REAL, unmodified `scanner.persist_run_payload`
+    (genuine INSERT/commit/idempotent-guard/`engine_identity`-stamping code) with a hand-built minimal
+    payload. Mirrors `run_scan`'s own idempotent fast path first (never creates a duplicate)."""
+    existing = scanner.get_run_for_date(session, asof)
+    if existing is not None:
+        return existing
+    return scanner.persist_run_payload(session, asof, _TINY_PAYLOAD, config)
+
+
+LOOP_DATES = INCIDENT_DATES[:2]  # a 2-date real-incident-date subset, so Check (B)/(C) are
+# GENUINELY exercised (in_scope=True) rather than vacuously passed -- j11_stage_d.check_identity_before_date/
+# check_identity_after_persist scope their comparison to app.engine.j11_maintenance.INCIDENT_DATES
+# membership specifically; an isolated in-memory fixture DB using these calendar dates has zero
+# connection to the live database.
+
+
+# =======================================================================================================
+# recheck_maintenance_boundary_and_guard
+# =======================================================================================================
+
+
+def test_recheck_boundary_ok_when_armed_active_and_exact_date_set(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="j11-incident-recovery", dates=LOOP_DATES, reason="test", active=True)
+    with Session(engine) as session:
+        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
+    assert result["ok"] is True
+    assert result["boundary_active"] is True
+    assert result["exact_date_set_match"] is True
+    assert result["all_dates_blocked"] is True
+    assert all(r["blocked"] for r in result["per_date_guard_result"].values())
+
+
+def test_recheck_boundary_fails_when_no_boundary_row_registered(engine):
+    with Session(engine) as session:
+        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
+    assert result["ok"] is False
+    assert result["boundary_row_present"] is False
+    assert result["all_dates_blocked"] is False  # true no-op / unarmed -- never falsely blocked
+
+
+def test_recheck_boundary_fails_when_inactive(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="j11-incident-recovery", dates=LOOP_DATES, reason="test", active=False)
+    with Session(engine) as session:
+        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
+    assert result["ok"] is False
+    assert result["boundary_active"] is False
+    assert result["all_dates_blocked"] is False  # cleared boundary never blocks
+
+
+def test_recheck_boundary_fails_when_date_set_does_not_match_exactly(engine):
+    wrong_dates = LOOP_DATES + (date(2030, 1, 8),)
+    with Session(engine) as session:
+        guard.register_boundary(session, name="j11-incident-recovery", dates=wrong_dates, reason="test", active=True)
+    with Session(engine) as session:
+        result = jsde.recheck_maintenance_boundary_and_guard(session, LOOP_DATES)
+    assert result["exact_date_set_match"] is False
+    assert result["ok"] is False
+
+
+# =======================================================================================================
+# run_fresh_avb_reclassification -- one real small-fixture smoke test + fail-closed edge cases (mocked)
+# =======================================================================================================
+
+
+def _small_universe_cfg():
+    """Mirrors `test_j11_avb_diagnostic.py`'s own `_small_universe_cfg()` exactly -- a real Config with
+    only the thresholds a tiny synthetic series would otherwise fail reduced."""
+    c = load_config().model_copy(deep=True)
+    c = c.model_copy(update={"indicators": c.indicators.model_copy(update={
+        "min_history_bars": 30, "vol_avg_period": 20,
+    })})
+    c = c.model_copy(update={"universe": c.universe.model_copy(update={
+        "filters": c.universe.filters.model_copy(update={
+            "min_price": 1.0, "min_dollar_vol": 1000.0, "adv_window_days": 20, "max_staleness_days": 30,
+        })
+    })})
+    return c
+
+
+def _seed_avb_prices(session: Session, *, n: int, end: date) -> None:
+    for i in range(n):
+        d = end - timedelta(days=n - 1 - i)
+        close = 180.0 + 0.2 * i
+        session.add(DailyPrice(
+            symbol=diag.AVB_SYMBOL, date=d, open=close, high=close * 1.01, low=close * 0.99,
+            close=close, volume=1_000_000.0,
+        ))
+    session.commit()
+
+
+def test_run_fresh_avb_reclassification_end_to_end_smoke_on_small_fixture(engine):
+    """Genuinely exercises the real `diag.*` composition (never mocked) against a small synthetic AVB
+    series plus the REAL committed J-10/provider-fetch evidence files (small, static JSON -- the same
+    'legitimately read directly' exception test_j11_avb_diagnostic.py's own docstring documents). Does
+    not assert a specific classification label (that correctness is test_j11_avb_diagnostic.py's own,
+    already-covered surface) -- only that the composition completes and returns a well-formed result."""
+    cfg = _small_universe_cfg()
+    with Session(engine) as session:
+        _seed_avb_prices(session, n=60, end=date(2026, 8, 12))
+    with Session(engine) as session:
+        result = jsde.run_fresh_avb_reclassification(
+            session, cfg,
+            provider_fetch_evidence_path=diag.REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-provider-fetch-evidence.json",
+            j10_evidence_path=diag.DEFAULT_J10_EVIDENCE_PATH,
+        )
+    assert result["classification"]["classification"] in ("AVB-A", "AVB-B", "AVB-C", "AVB-D")
+    assert result["bridge_factor"] == pytest.approx(2.7930001225759193)
+    assert set(result["volume_override_by_date"]) == {d.isoformat() for d in diag.RECOVERED_DATES}
+
+
+def test_run_fresh_avb_reclassification_fails_closed_to_avb_d_on_incomplete_volume_override(engine, tmp_path):
+    incomplete = {
+        "sufficient_evidence": True,
+        "per_date": {diag.RECOVERED_DATES[0].isoformat(): {"close": 100.0, "volume": 1000.0}},
+        # RECOVERED_DATES[1] deliberately missing volume evidence
+    }
+    fetch_path = tmp_path / "fetch.json"
+    fetch_path.write_text(json.dumps(incomplete))
+    with Session(engine) as session:
+        _seed_avb_prices(session, n=60, end=date(2026, 8, 12))
+    with Session(engine) as session:
+        result = jsde.run_fresh_avb_reclassification(
+            session, _small_universe_cfg(),
+            provider_fetch_evidence_path=fetch_path, j10_evidence_path=diag.DEFAULT_J10_EVIDENCE_PATH,
+        )
+    assert result["classification"]["classification"] == "AVB-D"
+    assert result["classification"]["stage_d_ready_per_avb"] is False
+    assert result["decision_impact_by_date"] == {}  # no trace attempted on incomplete evidence
+
+
+def test_run_fresh_avb_reclassification_fails_closed_to_avb_d_when_evidence_marked_insufficient(engine, tmp_path):
+    fetch_evidence = json.loads(
+        (diag.REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-provider-fetch-evidence.json").read_text()
+    )
+    fetch_evidence["sufficient_evidence"] = False
+    fetch_path = tmp_path / "fetch.json"
+    fetch_path.write_text(json.dumps(fetch_evidence))
+    with Session(engine) as session:
+        _seed_avb_prices(session, n=60, end=date(2026, 8, 12))
+    with Session(engine) as session:
+        result = jsde.run_fresh_avb_reclassification(
+            session, _small_universe_cfg(),
+            provider_fetch_evidence_path=fetch_path, j10_evidence_path=diag.DEFAULT_J10_EVIDENCE_PATH,
+        )
+    assert result["classification"]["classification"] == "AVB-D"
+    assert result["classification"]["stage_d_ready_per_avb"] is False
+
+
+# =======================================================================================================
+# stage_d_execution_gate_verdict
+# =======================================================================================================
+
+
+def test_gate_proceeds_only_when_all_three_conditions_hold():
+    gate = jsde.stage_d_execution_gate_verdict(
+        preflight_verdict={"passed": True}, avb_classification="AVB-A", boundary_recheck={"ok": True},
+    )
+    assert gate["proceed"] is True
+    assert gate["blocking_reasons"] == []
+
+
+@pytest.mark.parametrize("preflight_passed,avb,boundary_ok", [
+    (False, "AVB-A", True),
+    (True, "AVB-B", True),   # AVB-B is NOT the exact required classification for EXECUTION
+    (True, "AVB-C", True),
+    (True, "AVB-A", False),
+])
+def test_gate_refuses_unless_every_condition_holds(preflight_passed, avb, boundary_ok):
+    gate = jsde.stage_d_execution_gate_verdict(
+        preflight_verdict={"passed": preflight_passed, "reason": "x"},
+        avb_classification=avb, boundary_recheck={"ok": boundary_ok},
+    )
+    assert gate["proceed"] is False
+    assert gate["blocking_reasons"]
+
+
+# =======================================================================================================
+# freeze_fresh_stage_d_execution_identity + compare_identity_against_historical
+# =======================================================================================================
+
+
+def test_freeze_fresh_execution_identity_is_independently_recomputed(engine, cfg):
+    # git_head/goal_md_text omitted -> defaults to real read-only I/O against the committed repo
+    # (jsc.read_git_head / jsc.read_goal_md_text), the SAME fallback the production CLI script's own
+    # call site relies on when it does not override them; a minimal hand-typed goal_md_text would need
+    # to reproduce j11_stage_c.py's exact anchor text, which is exactly what this test must NOT hardcode.
+    with Session(engine) as session:
+        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
+    assert frozen["execution_identity"] is True
+    assert frozen["readiness_time_only"] is False
+    from app.engine import engine_identity as ei
+    assert frozen["engine_identity"] == ei.compute_engine_identity(cfg)  # independently recomputed, matches
+
+
+def test_compare_identity_against_historical_is_stated_honestly_both_ways():
+    comparison = jsde.compare_identity_against_historical(
+        "fresh-value", {"iteration_10": "legacy-value", "iteration_14": "fresh-value", "iteration_missing": None},
+    )
+    assert comparison["comparisons"]["iteration_10"]["matches_fresh"] is False
+    assert comparison["comparisons"]["iteration_14"]["matches_fresh"] is True
+    assert comparison["comparisons"]["iteration_missing"]["matches_fresh"] is False
+    assert comparison["any_historical_match"] is True  # honestly reported -- not silently hidden
+
+
+# =======================================================================================================
+# confirm_no_existing_scanner_run
+# =======================================================================================================
+
+
+def test_confirm_no_existing_run_true_when_none_present(engine):
+    with Session(engine) as session:
+        result = jsde.confirm_no_existing_scanner_run(session, date(2030, 1, 6))
+    assert result["already_exists"] is False
+
+
+def test_confirm_no_existing_run_false_when_a_row_is_present(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2030, 1, 6), engine_identity_value="some-identity")
+        session.commit()
+        run_id = run.id  # captured before the session closes -- avoids a DetachedInstanceError
+    with Session(engine) as session:
+        result = jsde.confirm_no_existing_scanner_run(session, date(2030, 1, 6))
+    assert result["already_exists"] is True
+    assert result["existing_run_id"] == run_id
+    assert result["existing_engine_identity"] == "some-identity"
+
+
+# =======================================================================================================
+# TC-4 / TC-5 / TC-6 / TC-9 -- the per-date loop
+# =======================================================================================================
+
+
+def test_tc4_tc6_loop_creates_exactly_one_run_per_date_all_stamped_with_frozen_identity(engine, cfg, monkeypatch):
+    monkeypatch.setattr(jsde.scanner, "run_scan", _stub_run_scan)
+    with Session(engine) as session:
+        frozen = jsde.freeze_fresh_stage_d_execution_identity(session, cfg)
+    with Session(engine) as session:
+        result = jsde.execute_stage_d_regeneration(session, LOOP_DATES, frozen, cfg)
+
+    assert result["completed"] is True
+    assert result["stopped_at_date"] is None
+    assert len(result["new_run_ids"]) == len(LOOP_DATES) == 2
+
+    with Session(engine) as session:
+        from sqlalchemy import func as _func
+        from sqlmodel import select as _select
+        from app.models import ScannerResult, SectorScoreRow, ThemeScoreRow
+        for one_date in LOOP_DATES:
+            run = session.exec(_select(ScannerRun).where(ScannerRun.asof_date == one_date)).one()
+            assert run.engine_identity == frozen["engine_identity"]
+            results_count = session.exec(
+                _select(_func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run.id)
+            ).one()
+            sectors_count = session.exec(
+                _select(_func.count()).select_from(SectorScoreRow).where(SectorScoreRow.run_id == run.id)
+            ).one()
+            themes_count = session.exec(
+                _select(_func.count()).select_from(ThemeScoreRow).where(ThemeScoreRow.run_id == run.id)
+            ).one()
+            assert results_count >= 1 and sectors_count >= 1 and themes_count >= 1
+
+
+def test_tc4_loop_ascending_chronological_order(engine, cfg, monkeypatch):
+    calls: list = []
+    real_stub = _stub_run_scan
+
+    def _tracking_stub(session, asof, config=None):
+        calls.append(asof)
+        return real_stub(session, asof, config)
+
+    monkeypatch.setattr(jsde.scanner, "run_scan", _tracking_stub)
... [diff_bound] apps/backend/tests/test_j11_stage_d_execute.py: 326 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_d_execute_cli_script.py b/apps/backend/tests/test_j11_stage_d_execute_cli_script.py
new file mode 100644
index 00000000..a02d7777
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_d_execute_cli_script.py
@@ -0,0 +1,319 @@
+"""goal-market-compass iter-19 -- J-11 Stage D EXECUTION CLI control-flow tests
+(`scripts/run_j11_stage_d_execute.py`), TC-10/TC-11 plus the stop-before-write control-flow proofs.
+
+`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and every
+`jsd.*`/`jsde.*`/`j11_maintenance.*`/`migration.*`/`jsc.*` function the script calls) is patched to a
+mock before `main()` runs, mirroring `test_j11_stage_c_cli_script.py`'s exact idiom -- these tests
+exercise CONTROL FLOW only (which functions get called, in what order, and which never get called),
+never real database I/O.
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
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_d_execute.py"
+_MODULE_NAME = "run_j11_stage_d_execute_under_test"
+
+
+def _load_script_module():
+    """Mirrors `test_j11_stage_c_cli_script.py`'s own loader exactly -- a REAL module object via
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
+# --- missing --confirm: NO database interaction of any kind -----------------------------------------
+
+
+def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_execute.py"])  # no --confirm
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+
+
+# --- --confirm but no --evidence-dir: refuses, writes nothing anywhere ------------------------------
+
+
+def test_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns, capsys):
+    mock_write_json = mock.MagicMock(name="_write_json")
+    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_execute.py", "--confirm"])
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_write_json.assert_not_called()
+    mock_get_engine.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
+# --- collision guard: a pre-existing output file refuses before any DB interaction -------------------
+
+
+def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    evidence_dir.mkdir()
+    (evidence_dir / "j11-stage-d-execute-outcome.json").write_text("{}")  # a prior run's leftover
+
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_stage_d_execute.py", "--confirm", "--evidence-dir", str(evidence_dir)],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_get_engine.assert_not_called()
+    assert "already contains" in capsys.readouterr().err
+
+
+# --- shared happy-path mock rig, so individual tests only override ONE piece -------------------------
+
+
+def _install_happy_path_mocks(monkeypatch, script_ns, *, evidence_dir: Path):
+    """Patches every DB-touching / expensive name the script calls to a deterministic, fully-successful
+    default. Returns a dict of the individual mocks so a test can override exactly one to prove a
+    specific stop-before-write control-flow property."""
+    mock_engine = mock.MagicMock(name="engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
+
+    mock_session_instance = mock.MagicMock(name="session_instance")
+    mock_session_cm = mock.MagicMock()
+    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
+    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))
+
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))
+    monkeypatch.setattr(script_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="goal md text"))
+    monkeypatch.setattr(script_ns.jsc, "read_git_head", mock.MagicMock(return_value="deadbeef"))
+    monkeypatch.setattr(
+        script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}),
+    )
+
+    mock_capture_preflight = mock.MagicMock(
+        name="capture_stage_d_preflight",
+        return_value={"manifest_row_count": 24, "c1_date_set_boundary_check": {"ok": True}},
+    )
+    monkeypatch.setattr(script_ns.jsd, "capture_stage_d_preflight", mock_capture_preflight)
+
+    mock_compare_preflight = mock.MagicMock(
+        name="compare_stage_d_preflight_to_certified", return_value={"all_invariants_hold": True, "checks": {}},
+    )
+    monkeypatch.setattr(script_ns.jsd, "compare_stage_d_preflight_to_certified", mock_compare_preflight)
+
+    mock_preflight_verdict = mock.MagicMock(
+        name="stage_d_preflight_verdict", return_value={"passed": True, "reason": "all_checks_passed"},
+    )
+    monkeypatch.setattr(script_ns.jsd, "stage_d_preflight_verdict", mock_preflight_verdict)
+
+    mock_boundary_recheck = mock.MagicMock(
+        name="recheck_maintenance_boundary_and_guard",
+        return_value={"ok": True, "boundary_active": True, "all_dates_blocked": True},
+    )
+    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_boundary_recheck)
+
+    mock_avb = mock.MagicMock(
+        name="run_fresh_avb_reclassification",
+        return_value={"classification": {"classification": "AVB-A"}},
+    )
+    monkeypatch.setattr(script_ns.jsde, "run_fresh_avb_reclassification", mock_avb)
+
+    mock_gate_verdict = mock.MagicMock(
+        name="stage_d_execution_gate_verdict",
+        return_value={"proceed": True, "blocking_reasons": []},
+    )
+    monkeypatch.setattr(script_ns.jsde, "stage_d_execution_gate_verdict", mock_gate_verdict)
+
+    mock_freeze = mock.MagicMock(
+        name="freeze_fresh_stage_d_execution_identity",
+        return_value={"engine_identity": "fresh-identity-value", "attempt_id": "j11-stage-d-x"},
+    )
+    monkeypatch.setattr(script_ns.jsde, "freeze_fresh_stage_d_execution_identity", mock_freeze)
+
+    monkeypatch.setattr(
+        script_ns.jsde, "compare_identity_against_historical",
+        mock.MagicMock(return_value={"comparisons": {}, "any_historical_match": False}),
+    )
+    monkeypatch.setattr(
+        script_ns.engine_identity, "compute_engine_identity", mock.MagicMock(return_value="fresh-identity-value"),
+    )
+    mock_check_a = mock.MagicMock(name="check_identity_before_first_write", return_value={"ok": True})
+    monkeypatch.setattr(script_ns.jsd, "check_identity_before_first_write", mock_check_a)
+
+    monkeypatch.setattr(script_ns.j11_maintenance, "capture_full_table_sweep", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
+    monkeypatch.setattr(
+        script_ns.jsde, "capture_legacy_and_null_scanner_run_fingerprint",
+        mock.MagicMock(return_value={"row_count": 0, "null_count": 0, "legacy_6261ca17_count": 0, "rows": [], "fingerprint": "x"}),
+    )
+    monkeypatch.setattr(
+        script_ns.j11_maintenance, "capture_pre_reset_inventory",
+        mock.MagicMock(return_value={"daily_prices": {"fingerprint": "p"}}),
+    )
+
+    mock_regen = mock.MagicMock(
+        name="execute_stage_d_regeneration",
+        return_value={"completed": True, "stopped_at_date": None, "new_run_ids": [1, 2]},
+    )
+    monkeypatch.setattr(script_ns.jsde, "execute_stage_d_regeneration", mock_regen)
+
+    mock_mutation_accounting = mock.MagicMock(
+        name="build_stage_d_mutation_accounting",
+        return_value={"all_checks_pass": True, "checks": {}},
+    )
+    monkeypatch.setattr(script_ns.jsde, "build_stage_d_mutation_accounting", mock_mutation_accounting)
+
+    fake_certified_path = evidence_dir.parent / "certified.json"
+    fake_certified_path.write_text(json.dumps({"manifest_row_count": 24}))
+
+    return {
+        "capture_preflight": mock_capture_preflight,
+        "compare_preflight": mock_compare_preflight,
+        "preflight_verdict": mock_preflight_verdict,
+        "boundary_recheck": mock_boundary_recheck,
+        "avb": mock_avb,
+        "gate_verdict": mock_gate_verdict,
+        "freeze": mock_freeze,
+        "check_a": mock_check_a,
+        "regen": mock_regen,
+        "mutation_accounting": mock_mutation_accounting,
+        "certified_path": fake_certified_path,
+    }
+
+
+def _argv(evidence_dir: Path, certified_path: Path) -> list[str]:
+    return [
+        "run_j11_stage_d_execute.py", "--confirm",
+        "--evidence-dir", str(evidence_dir),
+        "--certified-baseline-path", str(certified_path),
+    ]
+
+
+# --- execution gate refusing to proceed: the write loop is NEVER reached -----------------------------
+
+
+def test_execution_gate_not_proceed_never_calls_regeneration(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["avb_classification_not_avb_a:AVB-B"]}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["freeze"].assert_not_called()
+    mocks["regen"].assert_not_called()
+    outcome = json.loads((evidence_dir / "j11-stage-d-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "execution_gate_did_not_proceed"
+
+
+# --- Check (A) failure: still stops before the write loop --------------------------------------------
+
+
+def test_check_a_failure_never_calls_regeneration(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["check_a"].return_value = {"ok": False}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["regen"].assert_not_called()
+    outcome = json.loads((evidence_dir / "j11-stage-d-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+
+
+# --- failed post-execution mutation accounting: outcome STILL written, exit non-zero -----------------
+
+
+def test_failed_mutation_accounting_writes_outcome_executed_false_and_returns_nonzero(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["mutation_accounting"].return_value = {"all_checks_pass": False, "checks": {"manifests_unchanged": False}}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["regen"].assert_called_once()  # the gate passed, so the write loop DID run this time...
+    outcome_path = evidence_dir / "j11-stage-d-execute-outcome.json"
+    assert outcome_path.exists()  # ...but the outcome is STILL persisted either way (unlike Stage C)
+    outcome = json.loads(outcome_path.read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "post_execution_mutation_accounting_failed"
+
+
+# --- the full successful path: exit 0, outcome executed=True -----------------------------------------
+
+
+def test_successful_full_path_returns_zero_and_writes_outcome_executed_true(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
+    exit_code = script_ns.main()
+
+    assert exit_code == 0
+    mocks["regen"].assert_called_once()
+    outcome = json.loads((evidence_dir / "j11-stage-d-execute-outcome.json").read_text())
+    assert outcome["executed"] is True
+    # every declared output filename was actually written
+    for name in script_ns.OUTPUT_FILENAMES:
+        assert (evidence_dir / name).exists(), f"missing evidence file {name}"
+
+
+def test_none_of_the_default_paths_point_outside_the_repo(script_ns):
+    """Sanity: every default evidence/identity path constant resolves under REPO_ROOT -- never an
+    absolute path escaping the repository, never a path under apps/backend/data/ (the live db dir)."""
+    repo_root = script_ns.REPO_ROOT
+    for path in (
+        script_ns.DEFAULT_CERTIFIED_BASELINE_PATH,
+        script_ns.DEFAULT_ITERATION_10_IDENTITY_PATH,
+        script_ns.DEFAULT_ITERATION_14_IDENTITY_PATH,
+        script_ns.DEFAULT_ITERATION_16_17_18_PREFLIGHT_PATH,
+    ):
+        assert str(path).startswith(str(repo_root))
+        assert "apps/backend/data" not in str(path)
```
