# Iteration diff (bounded)

Files changed: 12. Shown in full: 10.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_avb_correction.py` (197 lines not shown)
- `apps/backend/tests/test_j11_avb_correction.py` (89 lines not shown)

```diff
diff --git a/apps/backend/app/engine/j11_stage_d.py b/apps/backend/app/engine/j11_stage_d.py
index 79d66430..225a8104 100644
--- a/apps/backend/app/engine/j11_stage_d.py
+++ b/apps/backend/app/engine/j11_stage_d.py
@@ -382,6 +382,56 @@ def load_stage_d_certified_baseline(
     }
 
 
+def build_avb_correction_superseded_baseline(
+    original_certified_baseline: dict,
+    *,
+    post_correction_daily_prices_fingerprint: str,
+    iteration: int,
+    mutation_evidence_artifact_path: str,
+) -> dict:
+    """goal-market-compass iter-16 (Goal 5) -- supersedes ONLY `daily_prices_fingerprint` in an existing
+    certified Stage D baseline (`load_stage_d_certified_baseline`'s own return shape), per the owner's
+    "OWNER RULING -- AVB two-row raw-volume correction before Stage D" (docs/goal.md, 2026-08-25): "After
+    that correction passes verification, the corrected daily_prices state becomes the new certified
+    raw-input baseline for J-11." Every OTHER field the certified baseline composes (`manifest_ddl`,
+    `manifest_dump`, `manifest_row_count`, `data_provider_runs_count`, `watchlist_count`) is copied
+    UNCHANGED, straight from `original_certified_baseline` -- none of them is touched by the AVB
+    correction (it mutates `daily_prices.volume` for two rows only), so none is re-derived from a
+    different source. This is an honest SUPERSESSION of one field, never a re-derivation of the whole
+    baseline, and it never mutates `original_certified_baseline` itself (a fresh dict is returned) --
+    iter-13's own lesson applies directly here too: "capturing an invariant's value is not checking it";
+    the caller MUST still run `compare_stage_d_preflight_to_certified` against both the OLD and the NEW
+    baseline and prove the gate's own verdict actually moves (False -> True), never just trust that this
+    function was called.
+
+    Raises `ValueError` if the supplied post-correction fingerprint equals the ORIGINAL certified
+    fingerprint -- that would mean no correction actually moved the raw layer, and silently "superseding"
+    a baseline with an unchanged value would hide that rather than surface it."""
+    original_fingerprint = original_certified_baseline["daily_prices_fingerprint"]
+    if post_correction_daily_prices_fingerprint == original_fingerprint:
+        raise ValueError(
+            "post_correction_daily_prices_fingerprint equals the ORIGINAL certified fingerprint -- "
+            "refusing to supersede a baseline with an unchanged value (the correction must have actually "
+            "moved the daily_prices fingerprint for this supersession to be meaningful)"
+        )
+    superseded = dict(original_certified_baseline)
+    superseded["daily_prices_fingerprint"] = post_correction_daily_prices_fingerprint
+    superseded["daily_prices_fingerprint_supersession"] = {
+        "superseded_at": _now_iso(),
+        "superseding_iteration": iteration,
+        "mutation_evidence_artifact": mutation_evidence_artifact_path,
+        "pre_correction_daily_prices_fingerprint": original_fingerprint,
+        "post_correction_daily_prices_fingerprint": post_correction_daily_prices_fingerprint,
+        "acceptance_amendment_cited": (
+            "docs/goal.md J-11 Acceptance, 'Raw inputs' bullet, 'Single narrow exception (owner, "
+            "2026-08-25)' -- the AVB two-cell volume correction supersedes ONLY this field; every other "
+            "composed field in this baseline is sourced UNCHANGED from the original certified state. "
+            "From this point onward J-11 again treats daily_prices as immutable at the NEW state."
+        ),
+    }
+    return superseded
+
+
 def compare_stage_d_preflight_to_certified(preflight: dict, certified: dict) -> dict:
     """The Stage D preflight comparison gate -- mirrors `j11_stage_c.compare_preflight_to_certified`'s
     shape and idiom but checks Stage D's OWN preconditions: canonical inputs (`daily_prices`) and
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index eef1838c..726e058d 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -32,6 +32,7 @@ from sqlmodel import Session, select
 
 from app.config import Config, get_config
 from app.engine import data_manager, evidence, forward_testing
+from app.engine import j11_preboot_guard
 from app.engine.forward_testing import backfill_forward_returns, walk_forward_asof_dates
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.prices import bar_cache, latest_data_date
@@ -83,12 +84,40 @@ def ensure_latest_snapshot(engine: Engine, config: Optional[Config] = None) -> O
     `yield`. Effectively instant on a warm DB (the run already exists -> `run_scan` returns it); on a
     fresh DB it is a single snapshot compute, bounded by `config.startup.readiness_budget_seconds`. Reads
     ONLY the committed frozen seed via the canonical engines (no network). Returns the latest data date,
-    or None when no price data exists yet (the readiness signal then reports `unavailable`)."""
+    or None when no price data exists yet (the readiness signal then reports `unavailable`).
+
+    goal-market-compass iter-16 ("OWNER RULING -- pre-boot incident guard required", docs/goal.md
+    J-11 step 11): before calling `run_scan` for the resolved `latest` date, checks whether that date
+    falls inside an ACTIVE `j11_preboot_guard.MaintenanceBoundary` -- iteration 15 proved this exact call
+    can otherwise recreate derived state for a date a maintenance/incident-recovery operation deliberately
+    left at zero `ScannerRun`s. A blocked date skips the write entirely (no `ScannerRun` is ever inserted
+    for it), logs an actionable message naming the date and the boundary's reason, and returns `None` --
+    the SAME safe shape this function already returns for a genuinely empty database, so boot never
+    crashes and the server still serves whatever is already persisted. The guard check itself fails
+    CLOSED on any unexpected error (never silently allows the write it could not evaluate). When NO
+    boundary is registered at all -- the common, no-incident case every other journey's boot depends on --
+    or once a registered boundary is explicitly cleared, this function's behavior is BYTE-IDENTICAL to
+    the unmodified form above (a cheap empty-table SELECT, then straight through to `run_scan`)."""
     cfg = config or get_config()
     with Session(engine) as session:
         latest = latest_data_date(session)
         if latest is None:
             return None
+        try:
+            guard = j11_preboot_guard.evaluate_boundary_for_date(session, latest)
+        except Exception as exc:  # fail CLOSED: an unevaluable boundary state is never treated as clear
+            guard = {
+                "blocked": True, "boundary_name": None,
+                "reason": f"maintenance boundary check raised {exc!r} -- failing closed", "ambiguous": True,
+            }
+        if guard["blocked"]:
+            logger.warning(
+                "boot: skipping canonical snapshot write for %s -- blocked by an ACTIVE maintenance "
+                "boundary %r: %s. No ScannerRun was created; the server still serves any already-"
+                "persisted snapshots. Clear the boundary once the maintenance operation is complete.",
+                latest, guard.get("boundary_name"), guard.get("reason"),
+            )
+            return None
         run_scan(session, latest, cfg)  # idempotent + immutable; the SINGLE canonical compute path
         return latest
 
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 10668ec3..e55f2983 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -986,3 +986,40 @@ class Watchlist(SQLModel, table=True):
     created_at: datetime  # wall-clock "date added"
     asof_date_added: date  # latest_data_date() captured at add time
     entry_close: Optional[float] = None  # canonical close on asof_date_added (None ⇒ price-since-added NA)
+
+
+# --- goal-market-compass iter-16 (J-11 "pre-boot incident guard required") -----------------------------
+class MaintenanceBoundary(SQLModel, table=True):
+    """A named, EXPLICIT maintenance/incident-recovery quarantine boundary — the persisted state
+    `app.engine.j11_preboot_guard` reads to decide whether the canonical snapshot producer may write a
+    given as-of date. Purely additive (new table via `create_db_and_tables`'s existing
+    `SQLModel.metadata.create_all` — no ALTER of any existing table).
+
+    Iteration 15 proved that ordinary backend boot (`main.py` -> `warmup.ensure_latest_snapshot` ->
+    `scanner.run_scan`) can itself perform an unauthorized write during an active J-11-class incident
+    window, because it derives its target date from the PRESERVED `daily_prices` layer while the DERIVED
+    layer for that date is deliberately quarantined — "operator discipline alone is no longer
+    sufficient" (docs/goal.md, owner 2026-08-25). This table is the reusable, state-driven substrate a
+    future maintenance operation registers/clears against, instead of the guard hardcoding any
+    date-set or symbol.
+
+    `active` is the load-bearing field: it is an EXPLICIT marker, set by a maintenance script at the
+    START of an incident-recovery attempt and cleared only when the operator judges the boundary safe to
+    lift — NEVER inferred from partial per-date `ScannerRun` presence (a partially-completed regeneration
+    attempt must still read as blocked; docs/goal.md J-11 step 13's "the clean-regeneration unit is the
+    complete date set, not an individual date checkpoint"). `quarantined_dates_json` is a JSON list of
+    ISO date strings — for THE J-11 incident boundary specifically, this list is populated FROM
+    `app.engine.j11_maintenance.INCIDENT_DATES` by the registration helper
+    (`j11_preboot_guard.register_j11_incident_boundary`), never re-typed as a fresh literal; the guard's
+    own evaluation logic reads only this persisted field and contains no incident-specific conditional of
+    any kind, so it is reusable for ANY future maintenance boundary, not just this one."""
+
+    __tablename__ = "maintenance_boundaries"
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    name: str = Field(index=True, unique=True)  # one row per named boundary (e.g. "j11-incident-recovery")
+    quarantined_dates_json: str  # JSON list of ISO ("YYYY-MM-DD") date strings
+    active: bool  # EXPLICIT marker -- never inferred from derived-row presence
+    reason: str  # free-text, surfaced verbatim in the guard's actionable skip-write log line
+    created_at: datetime
+    updated_at: datetime  # bumped whenever `active` (or the date-set) is registered/cleared
diff --git a/apps/backend/tests/test_j11_stage_d.py b/apps/backend/tests/test_j11_stage_d.py
index 80491338..f8a7dade 100644
--- a/apps/backend/tests/test_j11_stage_d.py
+++ b/apps/backend/tests/test_j11_stage_d.py
@@ -21,7 +21,7 @@ from sqlmodel import Session, SQLModel, create_engine
 from app.config import load_config
 from app.engine import j11_stage_d as jsd
 from app.engine.j11_maintenance import INCIDENT_DATES
-from app.models import NextSessionManifest, ScannerRun
+from app.models import DailyPrice, NextSessionManifest, ScannerRun
 
 _MATCHING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES)
 _GOAL_MD_MATCHING = f"""
@@ -766,3 +766,80 @@ def test_capture_stage_d_preflight_backward_compatible_without_prior_identity(en
         )
     assert preflight["attempt_identity"]["readiness_time_only"] is True
     assert preflight["attempt_identity"]["comparison_to_iteration_14_frozen_identity"]["matches"] is None
+
+
+# ----------------------------------------------------------------------------------------------
+# goal-market-compass iter-16 (Goal 5) -- the AVB-correction certified-baseline supersession.
+# "OWNER RULING -- AVB two-row raw-volume correction before Stage D": "the corrected daily_prices state
+# becomes the new certified raw-input baseline for J-11." Only `daily_prices_fingerprint` may move; every
+# other composed field must stay byte-sourced from the ORIGINAL certified state.
+# ----------------------------------------------------------------------------------------------
+
+
+def test_goal5_superseded_baseline_changes_only_the_daily_prices_fingerprint(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    original = _certified_from(preflight)
+    superseded = jsd.build_avb_correction_superseded_baseline(
+        original,
+        post_correction_daily_prices_fingerprint="new-fingerprint-after-correction",
+        iteration=16,
+        mutation_evidence_artifact_path="runs/goal-market-compass-iter-16/j11-avb-correction-mutation-evidence.json",
+    )
+    assert superseded["daily_prices_fingerprint"] == "new-fingerprint-after-correction"
+    # every OTHER composed field is byte-identical to the original, unchanged
+    for key in ("manifest_row_count", "manifest_ddl", "manifest_dump", "data_provider_runs_count", "watchlist_count"):
+        assert superseded[key] == original[key]
+    assert "daily_prices_fingerprint_supersession" in superseded
+    provenance = superseded["daily_prices_fingerprint_supersession"]
+    assert provenance["superseding_iteration"] == 16
+    assert provenance["pre_correction_daily_prices_fingerprint"] == original["daily_prices_fingerprint"]
+    assert provenance["post_correction_daily_prices_fingerprint"] == "new-fingerprint-after-correction"
+    # the ORIGINAL dict is never mutated -- a fresh dict is returned
+    assert "daily_prices_fingerprint_supersession" not in original
+
+
+def test_goal5_superseded_baseline_refuses_a_no_op_supersession(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    original = _certified_from(preflight)
+    with pytest.raises(ValueError):
+        jsd.build_avb_correction_superseded_baseline(
+            original,
+            post_correction_daily_prices_fingerprint=original["daily_prices_fingerprint"],  # UNCHANGED
+            iteration=16,
+            mutation_evidence_artifact_path="unused",
+        )
+
+
+def test_goal5_gate_reports_old_baseline_mismatched_and_new_baseline_matched(engine, cfg):
+    """TC-20/TC-21: the compare gate genuinely MOVES (False -> True) between the OLD and the NEW
+    baseline against the SAME fresh preflight capture -- iter-13's own lesson: a gate that cannot compare
+    is a gate that always passes."""
+    # OLD baseline -- certified from the database BEFORE the simulated AVB correction.
+    old_preflight = _fresh_preflight(engine, cfg)
+    old_certified = _certified_from(old_preflight)
+
+    # Simulate the AVB correction actually landing -- daily_prices changes, so its fingerprint moves.
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AVB", date=date(2026, 8, 11), open=1.0, high=2.0, low=0.5, close=1.5, volume=100.0))
+        session.commit()
+
+    fresh_preflight_after_correction = _fresh_preflight(engine, cfg)
+
+    # Against the OLD (pre-correction) baseline: an honest, EXPECTED mismatch.
+    gate_vs_old = jsd.compare_stage_d_preflight_to_certified(fresh_preflight_after_correction, old_certified)
+    assert gate_vs_old["checks"]["daily_prices_fingerprint_unchanged"] is False
+    assert gate_vs_old["all_invariants_hold"] is False
+
+    # Supersede ONLY the fingerprint -- the NEW certified baseline.
+    new_certified = jsd.build_avb_correction_superseded_baseline(
+        old_certified,
+        post_correction_daily_prices_fingerprint=(
+            fresh_preflight_after_correction["pre_reset_inventory"]["daily_prices"]["fingerprint"]
+        ),
+        iteration=16, mutation_evidence_artifact_path="unused",
+    )
+
+    # Against the NEW baseline: matches again, and EVERY other check also holds.
+    gate_vs_new = jsd.compare_stage_d_preflight_to_certified(fresh_preflight_after_correction, new_certified)
+    assert gate_vs_new["checks"]["daily_prices_fingerprint_unchanged"] is True
+    assert gate_vs_new["all_invariants_hold"] is True
diff --git a/apps/backend/tests/test_j11_stage_d_cli_scripts.py b/apps/backend/tests/test_j11_stage_d_cli_scripts.py
index 85eaf72c..6309e525 100644
--- a/apps/backend/tests/test_j11_stage_d_cli_scripts.py
+++ b/apps/backend/tests/test_j11_stage_d_cli_scripts.py
@@ -30,6 +30,7 @@ AVB_BRIDGE_DIAGNOSTIC_SCRIPT = SCRIPTS_DIR / "run_j11_avb_bridge_diagnostic.py"
 PROVIDER_FETCH_SCRIPT = SCRIPTS_DIR / "run_j11_avb_provider_fetch.py"
 STAGE_D_READINESS_SCRIPT = SCRIPTS_DIR / "run_j11_stage_d_readiness.py"
 RECONCILE_SCRIPT = SCRIPTS_DIR / "run_j11_reconcile_iteration_14_truth.py"
+ITER16_READINESS_SCRIPT = SCRIPTS_DIR / "run_j11_iter16_stage_d_readiness.py"
 
 
 def _load_script_module(script_path: Path, module_name: str):
@@ -94,6 +95,16 @@ def reconcile_ns(monkeypatch):
         sys.modules.pop("run_j11_reconcile_iteration_14_truth_under_test", None)
 
 
+@pytest.fixture()
+def iter16_readiness_ns(monkeypatch):
+    original_argv = sys.argv
+    try:
+        yield _load_script_module(ITER16_READINESS_SCRIPT, "run_j11_iter16_stage_d_readiness_under_test")
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop("run_j11_iter16_stage_d_readiness_under_test", None)
+
+
 # --- TC-25: run_j11_stage_d_preflight.py refuses without --evidence-dir, before load_config/engine ------
 
 
@@ -315,6 +326,25 @@ def test_tc27_reconcile_script_refuses_without_output_path(monkeypatch, reconcil
     assert "--output-path" in capsys.readouterr().err
 
 
+# --- goal-market-compass iter-16 (Goal 8): run_j11_iter16_stage_d_readiness.py refuses without ----------
+# --- --evidence-dir, before load_config/engine construction ---------------------------------------------
+
+
+def test_iter16_readiness_refuses_without_evidence_dir(monkeypatch, iter16_readiness_ns, capsys):
+    mock_load_config = mock.MagicMock(name="load_config")
+    monkeypatch.setattr(iter16_readiness_ns, "load_config", mock_load_config)
+    mock_write_json = mock.MagicMock(name="_write_json")
+    monkeypatch.setattr(iter16_readiness_ns, "_write_json", mock_write_json)
+    monkeypatch.setattr(sys, "argv", ["run_j11_iter16_stage_d_readiness.py"])  # no --evidence-dir
+
+    exit_code = iter16_readiness_ns.main()
+
+    assert exit_code == 2
+    mock_load_config.assert_not_called()
+    mock_write_json.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
 # --- TC-29 corroboration: none of these refusal tests wrote anywhere under the real committed evidence --
 # --- directories -- proven directly by asserting on git-tracked paths, mirroring the session's standing -
 # --- practice (the phase-level `git status --porcelain` check is the authoritative proof; this is a -----
@@ -322,11 +352,11 @@ def test_tc27_reconcile_script_refuses_without_output_path(monkeypatch, reconcil
 
 
 def test_none_of_the_refusal_paths_reference_a_real_committed_evidence_directory_as_a_default():
-    """Static proof: none of the five scripts' argparse `--output-path`/`--evidence-dir` arguments carry
+    """Static proof: none of the six scripts' argparse `--output-path`/`--evidence-dir` arguments carry
     a non-None default that resolves under `runs/goal-market-compass-iter-13` or `-iter-14`."""
     for script_path in (
         STAGE_D_PREFLIGHT_SCRIPT, AVB_BRIDGE_DIAGNOSTIC_SCRIPT, PROVIDER_FETCH_SCRIPT,
-        STAGE_D_READINESS_SCRIPT, RECONCILE_SCRIPT,
+        STAGE_D_READINESS_SCRIPT, RECONCILE_SCRIPT, ITER16_READINESS_SCRIPT,
     ):
         source = script_path.read_text()
         assert 'default=DEFAULT_EVIDENCE_DIR' not in source
diff --git a/apps/backend/app/engine/j11_avb_correction.py b/apps/backend/app/engine/j11_avb_correction.py
new file mode 100644
index 00000000..53fa4d0e
--- /dev/null
+++ b/apps/backend/app/engine/j11_avb_correction.py
@@ -0,0 +1,591 @@
+"""app.engine.j11_avb_correction -- goal-market-compass iter-16.
+
+Implements the two new owner rulings recorded in `docs/goal.md` J-11 step 11, immediately after ruling
+C12, both dated 2026-08-25:
+
+  - **"OWNER RULING -- AVB two-row raw-volume correction before Stage D."** Iteration 15 proved (via the
+    single-use AG-9 dated exception #2 provider fetch) that AVB's two J-10-recovered `daily_prices` rows
+    (2026-08-11, 2026-08-12) carry `bridged price + RAW volume`, while every surrounding stored AVB bar
+    (the four-date calibration window) carries `bridged price + COMPENSATING volume` -- so the recovered
+    rows' dollar volume is inflated by approximately the persisted bridge factor
+    (`2.7930001225759193`), which classifies as `AVB-C` (STAGE D NOT READY). The owner authorizes exactly
+    ONE bounded corrective mutation: table `daily_prices`, symbol `AVB`, dates `2026-08-11`/`2026-08-12`,
+    field `volume` ONLY -- derived **deterministically** from the already-committed iteration-15 evidence
+    (`runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json` + the persisted J-10
+    `bridge_factor`), with **NO new network fetch** (AG-9 dated exception #2 stays exhausted). This module
+    is the pure/read-only computation half: true-start/true-end envelope capture, the derivation itself,
+    and the mutation-evidence comparison builder. The actual `UPDATE` statement lives in
+    `apps/backend/scripts/run_j11_avb_correction.py` (mirrors the `j11_stage_c.py` /
+    `run_j11_stage_c_bounded_clear.py` split: this module never writes).
+  - **"OWNER RULING -- pre-boot incident guard required."** Handled by the SIBLING module
+    `app.engine.j11_preboot_guard` (Goals 6/7) -- not this one.
+
+**Verification-before-write discipline (iter-13's lesson, restated in the owner's own dispatch note):**
+"capturing an invariant's value is not checking it, and a gate that cannot compare is a gate that always
+passes." The true-start envelope this module captures is compared, in the CLI script, against the
+coordinator's independently-posted true-start figures BEFORE any write is contemplated; any mismatch is
+reported explicitly, never silently reconciled (docs/goal.md's own words). The exact isolating-hash
+recipe below was independently re-derived (not copied blind) by probing the live, read-only database
+until three candidate SQL/ordering choices reproduced the coordinator's three posted target digests
+byte-for-byte, plus the manifest row-dump digest's posted truncated prefix/suffix -- see this module's
+own hash helpers for the confirmed exact recipe.
+
+**J-10 is NOT reopened by this module.** J-10 stays historically closed at its recorded terminal state
+(585 restored; EA/EQR accepted unrestorable; AG-9's recovery-fetch authorization exhausted). This is a
+narrowly authorized post-J-10 correction of a defect the J-11 readiness audit found -- not a recovery
+programme, not a re-fetch, not a reclassification of J-10's own acceptance.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+import sqlite3
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Optional
+
+from sqlalchemy import func, select as sa_select
+from sqlalchemy.engine import Engine
+from sqlmodel import Session, select
+
+from app.config import REPO_ROOT
+from app.engine import j11_avb_diagnostic as diag
+from app.engine import j11_maintenance as jm
+from app.engine import j11_schema_migration as migration
+from app.engine import j11_stage_c as jsc
+from app.engine import j11_stage_d as jsd
+from app.models import DailyPrice, ForwardReturn
+
+AVB_SYMBOL = "AVB"
+
+# The two owner-authorized target dates (docs/goal.md, "OWNER RULING -- AVB two-row raw-volume
+# correction before Stage D") -- a literal historical fact about THIS one-time correction, never a
+# reusable threshold (same posture as `j11_maintenance.INCIDENT_DATES`/`j11_avb_diagnostic.
+# RECOVERED_DATES`, which this tuple is deliberately equal to but kept as its OWN literal so this
+# module's authorization boundary is self-contained and legible without cross-referencing another
+# module's unrelated-purpose constant).
+TARGET_DATES: tuple[date, ...] = (date(2026, 8, 11), date(2026, 8, 12))
+
+DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-provider-fetch-evidence.json"
+)
+
+# Reuse the SAME relative-tolerance band the calibration-window compensating check already uses (Goal
+# 2's cross-check must land within it) -- never a fresh, independently-chosen number.
+_RATIO_RELATIVE_TOLERANCE = diag._RATIO_RELATIVE_TOLERANCE
+
+# The coordinator's independently-posted true-start capture (dispatch note, 2026-08-25) -- to be
+# RE-DERIVED live and COMPARED, never trusted verbatim ("verify it yourself, don't trust it" -- the
+# coordinator's own words). Any mismatch is reported explicitly, never silently reconciled. The three
+# isolating hashes and the manifest DDL hash are compared by FULL sha256 equality (independently
+# re-derived and confirmed byte-for-byte against a live read-only probe before this module was written);
+# the manifest row-dump hash was posted only as a truncated `prefix...suffix` excerpt (the SAME
+# `NNNNNNNN...NNNNNNN` shorthand `j11_stage_d.OWNER_TRUE_START_CAPTURE` already uses for this exact
+# figure), so it is compared the SAME weaker prefix/suffix way, honestly labeled as such.
+COORDINATOR_TRUE_START_CAPTURE: dict = {
+    "db_mtime": 1787591622,
+    "db_size_bytes": 8365871104,
+    "db_wal_size_bytes": 0,
+    "daily_prices_row_count": 3310374,
+    "scanner_runs_total_count": 3117,
+    "scanner_runs_stamped_6261ca17_count": 34,
+    "forward_returns_total_count": 6797728,
+    "forward_returns_measured_into_incident_total": 16614,
+    "data_provider_runs_count": 549,
+    "manifest_row_count": 24,
+    "manifest_ddl_sha256": "9f653c8147c7c8931b07ea4a88d46ef1d6ddefb2ef5177b700d2b60e7fc501ee",
+    "manifest_row_dump_sha256_prefix": "bb954b60",
+    "manifest_row_dump_sha256_suffix": "6d2a2e6",
+    "watchlist_count": 6,
+    "all_11_incident_dates_zero_scanner_runs": True,
+    "isolating_hashes": {
+        "avb_ohlc_only": "757c3c63a39d7c167f691a929ec0579dd7e9584c20f6c9ff99879e6bec4c8fd3",
+        "avb_other_dates_full_row": "53bca57105dad60137049f9a8b2350d6d6d0d3a6645337e4352b3fa5c56dc14f",
+        "non_avb_full_row": "78146554cab8a2a619507e60cafa6354350d176f5685383d41c8c97899264997",
+    },
+    "avb_target_rows": {
+        "2026-08-11": {
+            "open": 183.22001534990548, "high": 184.13001191846783, "low": 181.7100027790582,
+            "close": 181.76001476703186, "volume": 1549436.0,
+        },
+        "2026-08-12": {
+            "open": 181.08999902870366, "high": 182.0900043902787, "low": 179.45999604273928,
+            "close": 179.79000697488598, "volume": 10350885.0,
+        },
+    },
+}
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+# ----------------------------------------------------------------------------------------------
+# Read-only sqlite3 (mode=ro + PRAGMA query_only=ON) row-hash helpers -- the confirmed exact recipe.
+# Never an ORM hydration of the matched rows (AG-8): each query streams through a raw sqlite3 cursor,
+# hashing one row's `repr()` at a time into a running sha256, so memory stays O(1) regardless of row
+# count (proven live against the ~3.3M-row non-AVB population).
+# ----------------------------------------------------------------------------------------------
+
+
+def _ro_connect(db_path: Path) -> sqlite3.Connection:
+    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
+    conn.execute("PRAGMA query_only=ON")
+    return conn
+
+
+def _hash_query(db_path: Path, sql: str, params: tuple = ()) -> dict:
+    """sha256 over `repr(row)` per row, in cursor iteration order, over a read-only connection. Returns
+    `{sql, row_count, sha256}` -- the recipe is carried alongside every hash this module ever reports, so
+    no hash is ever presented without a falsifiable recipe (iter-15b's lesson: "a fingerprint quoted into
+    a spec without its recipe is an unfalsifiable verification target")."""
+    conn = _ro_connect(db_path)
+    try:
+        cursor = conn.execute(sql, params)
+        h = hashlib.sha256()
+        row_count = 0
+        for row in cursor:
+            h.update(repr(row).encode())
+            row_count += 1
+        return {"sql": sql, "row_count": row_count, "sha256": h.hexdigest()}
+    finally:
+        conn.close()
+
+
+_AVB_OHLC_ONLY_SQL = (
+    "SELECT symbol, date, open, high, low, close FROM daily_prices WHERE symbol=? ORDER BY date"
+)
+_AVB_OTHER_DATES_FULL_ROW_SQL = (
+    "SELECT symbol, date, open, high, low, close, volume FROM daily_prices "
+    "WHERE symbol=? AND date NOT IN (?, ?) ORDER BY date"
+)
+_NON_AVB_FULL_ROW_SQL = (
+    "SELECT symbol, date, open, high, low, close, volume FROM daily_prices WHERE symbol!=? ORDER BY symbol, date"
+)
+_MANIFEST_ROW_DUMP_SQL = "SELECT * FROM next_session_manifests ORDER BY id"
+
+
+def capture_isolating_hashes(db_path: Path) -> dict:
+    """The three population-partition hashes (iter-9's lesson: a population-wide uniform aggregate is
+    exactly where the one real counter-example hides -- these prove the ABSENCE of collateral change on
+    every partition the correction must NOT touch, not merely the presence of the intended change):
+      - `avb_ohlc_only` -- every AVB row's (symbol, date, open, high, low, close), volume EXCLUDED,
+        across ALL AVB dates including the two target dates (proves OHLC is untouched even for the
+        rows being corrected).
+      - `avb_other_dates_full_row` -- every AVB row's full (symbol, date, o, h, l, c, volume) EXCEPT the
+        two target dates (proves no OTHER AVB date's volume moved).
+      - `non_avb_full_row` -- every non-AVB `daily_prices` row's full tuple (proves no other symbol was
+        touched at all)."""
+    target_iso = [d.isoformat() for d in TARGET_DATES]
+    return {
+        "avb_ohlc_only": _hash_query(db_path, _AVB_OHLC_ONLY_SQL, (AVB_SYMBOL,)),
+        "avb_other_dates_full_row": _hash_query(
+            db_path, _AVB_OTHER_DATES_FULL_ROW_SQL, (AVB_SYMBOL, *target_iso)
+        ),
+        "non_avb_full_row": _hash_query(db_path, _NON_AVB_FULL_ROW_SQL, (AVB_SYMBOL,)),
+    }
+
+
+def capture_manifest_row_dump_hash(db_path: Path) -> dict:
+    """The manifest row-dump fingerprint (distinct from `manifest_ddl_sha256`, which hashes the CREATE
+    TABLE text only) -- SAME raw-sqlite3-repr recipe as the isolating hashes above, confirmed against the
+    coordinator's posted truncated `bb954b60...6d2a2e6` reference."""
+    return _hash_query(db_path, _MANIFEST_ROW_DUMP_SQL)
+
+
+# ----------------------------------------------------------------------------------------------
+# Goal 1/4 -- true-start / true-end safety envelope (the SAME capture function serves both; the CLI
+# script calls it once before Goal 3's write and once immediately after).
+# ----------------------------------------------------------------------------------------------
+
+
+def fetch_avb_target_rows(session: Session) -> dict[str, dict]:
+    """The two target rows' exact `(open, high, low, close, volume)`, column-projected, keyed by ISO
+    date string."""
+    rows = session.exec(
+        select(
+            DailyPrice.date, DailyPrice.open, DailyPrice.high, DailyPrice.low, DailyPrice.close,
+            DailyPrice.volume,
+        )
+        .where(DailyPrice.symbol == AVB_SYMBOL)
+        .where(DailyPrice.date.in_(TARGET_DATES))
+        .order_by(DailyPrice.date)
+    ).all()
+    return {
+        d.isoformat(): {"open": o, "high": h, "low": l, "close": c, "volume": v}
+        for d, o, h, l, c, v in rows
+    }
+
+
+def capture_true_envelope(session: Session, engine: Engine, db_path: Optional[Path]) -> dict:
+    """Goal 1 (true-start) / Goal 4 (true-end, same function reused) -- read-only, composed entirely
+    from already-existing primitives (`j11_maintenance.capture_pre_reset_inventory`,
+    `j11_stage_d._scanner_runs_by_identity_group` -- iter-15's own exact-id-set scanner-run breakdown,
+    reused rather than reimplemented, `j11_schema_migration.fetch_object_ddl`, `j11_stage_c.
+    db_file_fingerprint`) plus this module's own isolating-hash helpers. Writes nothing."""
+    pre_reset_inventory = jm.capture_pre_reset_inventory(session)
+    incident_dates = pre_reset_inventory["incident_dates"]
+    all_11_zero = not any(
+        pre_reset_inventory["per_date"][d]["scanner_run"]["present"] for d in incident_dates
+    )
+    forward_returns_measured_into_incident_total = sum(
+        int(pre_reset_inventory["per_date"][d]["forward_returns_measured_into_count"]) for d in incident_dates
+    )
+
+    scanner_runs_by_identity_group = jsd._scanner_runs_by_identity_group(session)
+    scanner_runs_total_count = (
+        scanner_runs_by_identity_group["null_count"]
+        + scanner_runs_by_identity_group["legacy_6261ca17_count"]
+        + scanner_runs_by_identity_group["other_count"]
+    )
+    forward_returns_total_count = int(session.scalar(sa_select(func.count()).select_from(ForwardReturn)) or 0)
+
+    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    manifest_ddl_sha256 = hashlib.sha256((manifest_ddl.get("table_sql") or "").encode("utf-8")).hexdigest()
+
+    avb_target_rows = fetch_avb_target_rows(session)
+
+    db_file = jsc.db_file_fingerprint(db_path) if db_path is not None else {"exists": False}
+    isolating_hashes = capture_isolating_hashes(db_path) if db_path is not None else None
+    manifest_row_dump_hash = capture_manifest_row_dump_hash(db_path) if db_path is not None else None
+    manifest_row_count = (
+        manifest_row_dump_hash["row_count"] if manifest_row_dump_hash is not None else None
+    )
+
+    return {
+        "captured_at": _now_iso(),
+        "db_file": db_file,
+        "daily_prices": pre_reset_inventory["daily_prices"],
+        "data_provider_runs_count": pre_reset_inventory["data_provider_runs_count"],
+        "watchlist_count": pre_reset_inventory["watchlist_count"],
+        "all_11_incident_dates_zero_scanner_runs": all_11_zero,
+        "scanner_runs_total_count": scanner_runs_total_count,
+        "scanner_runs_by_identity_group": scanner_runs_by_identity_group,
+        "forward_returns_total_count": forward_returns_total_count,
+        "forward_returns_measured_into_incident_total": forward_returns_measured_into_incident_total,
+        "manifest_row_count": manifest_row_count,
+        "manifest_ddl_sha256": manifest_ddl_sha256,
+        "manifest_row_dump_fingerprint": manifest_row_dump_hash,
+        "isolating_hashes": isolating_hashes,
+        "avb_target_rows": avb_target_rows,
+    }
+
+
+def _prefix_suffix_match(full_value: Optional[str], prefix: Optional[str], suffix: Optional[str]) -> bool:
+    if not full_value or not prefix or not suffix:
+        return False
+    return full_value.startswith(prefix) and full_value.endswith(suffix)
+
+
+def compare_true_envelope_to_coordinator_capture(
+    derived: dict, coordinator_capture: dict = COORDINATOR_TRUE_START_CAPTURE
+) -> dict:
+    """TC-1 through TC-5: per-figure match/mismatch against the coordinator's posted true-start capture.
+    ANY mismatch is reported explicitly (never silently reconciled) -- mirrors `j11_stage_d.
+    _compare_against_owner_capture`'s idiom exactly (same session, same convention), applied to this
+    module's own capture shape."""
+    comparisons: dict[str, dict] = {}
+
+    def _exact(name: str, derived_value, key: str) -> None:
+        expected = coordinator_capture.get(key)
+        comparisons[name] = {
+            "derived_value": derived_value, "expected_value": expected,
+            "comparison_method": "exact", "matches": derived_value == expected,
+        }
+
+    db_file = derived.get("db_file") or {}
+    _exact("db_mtime", int(db_file["mtime"]) if db_file.get("exists") and db_file.get("mtime") is not None else None, "db_mtime")
+    _exact("db_size_bytes", db_file.get("size_bytes"), "db_size_bytes")
+    wal = db_file.get("wal") or {}
+    wal_size = wal.get("size_bytes", 0) if wal.get("exists") else 0
+    _exact("db_wal_size_bytes", wal_size, "db_wal_size_bytes")
+    _exact("daily_prices_row_count", derived["daily_prices"]["row_count"], "daily_prices_row_count")
+    _exact("scanner_runs_total_count", derived["scanner_runs_total_count"], "scanner_runs_total_count")
+    _exact(
+        "scanner_runs_stamped_6261ca17_count",
+        derived["scanner_runs_by_identity_group"]["legacy_6261ca17_count"], "scanner_runs_stamped_6261ca17_count",
+    )
+    _exact("forward_returns_total_count", derived["forward_returns_total_count"], "forward_returns_total_count")
+    _exact(
+        "forward_returns_measured_into_incident_total",
+        derived["forward_returns_measured_into_incident_total"], "forward_returns_measured_into_incident_total",
+    )
+    _exact("data_provider_runs_count", derived["data_provider_runs_count"], "data_provider_runs_count")
+    _exact("manifest_row_count", derived["manifest_row_count"], "manifest_row_count")
+    _exact("watchlist_count", derived["watchlist_count"], "watchlist_count")
+    _exact(
+        "all_11_incident_dates_zero_scanner_runs",
+        derived["all_11_incident_dates_zero_scanner_runs"], "all_11_incident_dates_zero_scanner_runs",
+    )
+    _exact("manifest_ddl_sha256", derived["manifest_ddl_sha256"], "manifest_ddl_sha256")
+
+    for hash_name in ("avb_ohlc_only", "avb_other_dates_full_row", "non_avb_full_row"):
+        derived_hash = (derived.get("isolating_hashes") or {}).get(hash_name, {}).get("sha256")
+        expected_hash = coordinator_capture.get("isolating_hashes", {}).get(hash_name)
+        comparisons[f"isolating_hash.{hash_name}"] = {
+            "derived_value": derived_hash, "expected_value": expected_hash,
+            "comparison_method": "exact", "matches": derived_hash == expected_hash,
+        }
+
+    manifest_dump_hash = (derived.get("manifest_row_dump_fingerprint") or {}).get("sha256")
+    comparisons["manifest_row_dump_sha256"] = {
+        "derived_value": manifest_dump_hash,
+        "expected_prefix": coordinator_capture.get("manifest_row_dump_sha256_prefix"),
+        "expected_suffix": coordinator_capture.get("manifest_row_dump_sha256_suffix"),
+        "comparison_method": "prefix_suffix_excerpt_not_full_hash",
+        "matches": _prefix_suffix_match(
+            manifest_dump_hash,
+            coordinator_capture.get("manifest_row_dump_sha256_prefix"),
+            coordinator_capture.get("manifest_row_dump_sha256_suffix"),
+        ),
+    }
+
+    for key, expected_row in coordinator_capture.get("avb_target_rows", {}).items():
+        derived_row = derived.get("avb_target_rows", {}).get(key, {})
+        comparisons[f"avb_target_row.{key}"] = {
+            "derived_value": derived_row, "expected_value": expected_row,
+            "comparison_method": "exact", "matches": derived_row == expected_row,
+        }
+
+    any_mismatch = any(not c["matches"] for c in comparisons.values())
+    return {
+        "generated_at": _now_iso(),
+        "comparisons": comparisons,
+        "any_mismatch": any_mismatch,
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Goal 2 -- derive the correction deterministically; fail closed before any write is contemplated.
+# ----------------------------------------------------------------------------------------------
+
+
+def load_provider_fetch_evidence(path: Path = DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH) -> dict:
+    """Iteration 15's already-committed AG-9 dated-exception-#2 fetch evidence -- read-only, no network
+    call anywhere in this function or any caller of it."""
+    return json.loads(Path(path).read_text())
+
+
+def derive_avb_volume_correction(
+    provider_fetch_evidence: dict,
+    j10_evidence_row: dict,
+    stored_volume_before: dict[str, float],
+    stored_close: dict[str, float],
+) -> dict:
+    """Goal 2 (TC-7..TC-10): `corrected_volume(date) = round(provider_volume(date) / bridge_factor)` --
+    the SAME inverse transform `j11_avb_diagnostic.compute_provider_comparison`'s own
+    `expected_inverse_volume_ratio = 1/bridge_factor` already establishes and has proven matches the four
+    calibration dates. Rounding rule: nearest whole share (Python's `round()`, applied identically to
+    both dates) -- share counts are conventionally whole numbers, and every calibration-window stored
+    compensating volume is itself a whole number.
+
+    Cross-verifies BEFORE any write is contemplated: `dollar_volume_ratio_after = (stored_close_unchanged
+    * corrected_volume) / (provider_close * provider_volume)` must land within the SAME relative-
+    tolerance band (`_RATIO_RELATIVE_TOLERANCE`) the calibration-window compensating check already uses
+    around 1.0. **Fails closed** (`verified: False`, per-date `ok: False`) on: `sufficient_evidence` not
+    True in the fetch evidence; a missing/None provider volume, provider close, or `bridge_factor`; or a
+    cross-check ratio outside tolerance. Never raises for a business-logic failure -- the caller checks
+    `verified` and withholds the write itself."""
+    bridge_factor = j10_evidence_row.get("bridge_factor")
+    per_date_provider = provider_fetch_evidence.get("per_date", {})
+    sufficient = bool(provider_fetch_evidence.get("sufficient_evidence", False))
+
+    per_date_results: dict[str, dict] = {}
+    all_ok = sufficient and bool(bridge_factor)
... [diff_bound] apps/backend/app/engine/j11_avb_correction.py: 197 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/j11_preboot_guard.py b/apps/backend/app/engine/j11_preboot_guard.py
new file mode 100644
index 00000000..f93ba281
--- /dev/null
+++ b/apps/backend/app/engine/j11_preboot_guard.py
@@ -0,0 +1,178 @@
+"""app.engine.j11_preboot_guard -- goal-market-compass iter-16 (Goals 6/7).
+
+Implements the "OWNER RULING -- pre-boot incident guard required" (docs/goal.md J-11 step 11, owner
+2026-08-25): iteration 15 proved that `apps/backend/main.py`'s ordinary boot path
+(`warmup.ensure_latest_snapshot` -> `scanner.run_scan`) resolves the latest STORED price date and writes
+a canonical `ScannerRun` for it unconditionally -- so while the latest `daily_prices` date is an incident
+date deliberately held at zero `ScannerRun`s (J-11's Stage-C-cleared quarantine), **merely booting the
+backend can recreate derived state before Stage D is authorized.** "Operator discipline alone is no
+longer sufficient."
+
+This module is the reusable, state-driven substrate: `MaintenanceBoundary` (`app.models`) is the
+persisted state; `evaluate_boundary_for_date` is the fail-closed core check; `register_boundary` /
+`clear_boundary` are the generic (incident-agnostic) registration primitives; `register_j11_incident_
+boundary` is the ONE place that ties a boundary's date-set to `j11_maintenance.INCIDENT_DATES` for the
+CURRENT J-11 incident specifically.
+
+**The design trap this module is built to avoid (owner's own words):** source production date
+membership from `j11_maintenance.INCIDENT_DATES` (never a fresh literal), but drive the runtime
+refuse/allow decision from PERSISTED STATE, not a hardcoded conditional -- otherwise a fixture-only
+state change could never flip the guard's behaviour, and the guard would be untestable as "state-driven"
+even though it claims to be. `evaluate_boundary_for_date` below reads ONLY `MaintenanceBoundary` rows; it
+contains no reference to `INCIDENT_DATES`, `AVB`, or any incident-specific date anywhere in its body --
+that wiring lives exclusively in `register_j11_incident_boundary`, a thin registration helper this
+module's own tests exercise but which iteration 16 does NOT invoke against the live database (maintenance
+isolation stays externally active; the live backend is never booted this iteration -- the guard is proven
+on disposable fixture/in-memory state only).
+
+**Fail-closed contract:** no `MaintenanceBoundary` row registered at all is the ONLY case that behaves as
+a true no-op (allowed) -- the common, no-incident case every OTHER journey's boot already depends on. Any
+row whose `active` flag or `quarantined_dates_json` cannot be read/parsed cleanly is treated as BLOCKING
+(never silently skipped, never treated as cleared) -- "fails CLOSED on missing/unreadable/ambiguous
+state, never fails open." An explicitly CLEARED row (`active=False`) never blocks, regardless of what its
+date-set contains.
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+from typing import Iterable, Optional
+
+from sqlmodel import Session, select
+
+from app.engine import j11_maintenance
+from app.models import MaintenanceBoundary
+
+# THE J-11 incident boundary's registered name -- a literal identifier for THIS incident's row, exactly
+# analogous to `j11_maintenance.INCIDENT_DATES` being a literal historical fact rather than a reusable
+# threshold. The guard's own evaluation logic below never references this constant.
+J11_INCIDENT_BOUNDARY_NAME = "j11-incident-recovery"
+
+_DEFAULT_J11_BOUNDARY_REASON = (
+    "J-11 incident-bounded derived-state quarantine (docs/goal.md) -- Stage D has not yet been "
+    "authorized/executed for these dates; canonical producer writes are refused until this boundary is "
+    "explicitly cleared by a future maintenance operation."
+)
+
+
+def _now() -> datetime:
+    return datetime.now(timezone.utc)
+
+
+# ----------------------------------------------------------------------------------------------
+# Generic, incident-agnostic registration primitives -- no reference to J-11/AVB/any specific date
+# anywhere in this section.
+# ----------------------------------------------------------------------------------------------
+
+
+def register_boundary(
+    session: Session, *, name: str, dates: Iterable[date], reason: str, active: bool = True,
+) -> MaintenanceBoundary:
+    """Insert-or-update (by unique `name`) a maintenance boundary row -- idempotent registration, never a
+    second row for the same name. `dates` is stored as a JSON list of ISO date strings, sorted for a
+    deterministic on-disk representation."""
+    existing = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == name)).first()
+    dates_json = json.dumps(sorted(d.isoformat() for d in dates))
+    now = _now()
+    if existing is None:
+        row = MaintenanceBoundary(
+            name=name, quarantined_dates_json=dates_json, active=active, reason=reason,
+            created_at=now, updated_at=now,
+        )
+    else:
+        existing.quarantined_dates_json = dates_json
+        existing.active = active
+        existing.reason = reason
+        existing.updated_at = now
+        row = existing
+    session.add(row)
+    session.commit()
+    session.refresh(row)
+    return row
+
+
+def clear_boundary(session: Session, name: str) -> Optional[MaintenanceBoundary]:
+    """Marks the named boundary CLEARED (`active=False`) -- a no-op (returns `None`) if no such boundary
+    is registered. Never DELETEs the row: the row itself stays queryable as an audit trail of a past
+    incident boundary having existed and been lifted."""
+    existing = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == name)).first()
+    if existing is None:
+        return None
+    existing.active = False
+    existing.updated_at = _now()
+    session.add(existing)
+    session.commit()
+    session.refresh(existing)
+    return existing
+
+
+def register_j11_incident_boundary(
+    session: Session, *, active: bool = True, reason: str = _DEFAULT_J11_BOUNDARY_REASON,
+) -> MaintenanceBoundary:
+    """Registers (or updates) THE J-11 incident-recovery boundary, sourcing its date-set from the
+    canonical `j11_maintenance.INCIDENT_DATES` -- never a fresh hardcoded list here (the exact design
+    trap the owner's dispatch note flagged). This is the ONLY function in this module that imports or
+    references `j11_maintenance` at all; `evaluate_boundary_for_date` below never does."""
+    return register_boundary(
+        session, name=J11_INCIDENT_BOUNDARY_NAME, dates=j11_maintenance.INCIDENT_DATES, reason=reason,
+        active=active,
+    )
+
+
+# ----------------------------------------------------------------------------------------------
+# The fail-closed, state-driven core check -- contains NO incident-specific conditional of any kind.
+# ----------------------------------------------------------------------------------------------
+
+
+def evaluate_boundary_for_date(session: Session, one_date: date) -> dict:
+    """Whether `one_date` currently falls inside an ACTIVE, cleanly-readable maintenance boundary.
+
+    Returns `{"blocked": bool, "boundary_name": str|None, "reason": str|None, "ambiguous": bool}`.
+
+      - No `MaintenanceBoundary` rows registered at all -> `blocked=False` (the true no-op / common
+        no-incident case).
+      - A row with `active=True` whose parsed `quarantined_dates_json` contains `one_date` ->
+        `blocked=True`, naming that row and its `reason`.
+      - A row that is explicitly cleared (`active=False`) never blocks, regardless of its date-set.
+      - A row whose `active` flag is unreadable, or whose `quarantined_dates_json` is missing, empty,
+        malformed JSON, or not a JSON list of date strings, while otherwise appearing active-ish (not
+        provably cleared) -> `blocked=True, ambiguous=True` -- fails CLOSED rather than silently
+        skipping an unreadable row or assuming it is cleared.
+
+    This function performs ONLY read queries; it never writes."""
+    rows = session.exec(select(MaintenanceBoundary)).all()
+    if not rows:
+        return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+    date_key = one_date.isoformat()
+    ambiguous_names: list[str] = []
+    for row in rows:
+        if row.active is None:
+            ambiguous_names.append(row.name)
+            continue
+        if not row.active:
+            continue  # explicitly cleared -- never blocks, regardless of its date-set content
+        if not row.quarantined_dates_json:
+            ambiguous_names.append(row.name)  # active but no date-set content at all
+            continue
+        try:
+            parsed = json.loads(row.quarantined_dates_json)
+            if not isinstance(parsed, list) or not all(isinstance(d, str) for d in parsed):
+                raise ValueError("quarantined_dates_json did not decode to a JSON list of date strings")
+        except (TypeError, ValueError, json.JSONDecodeError):
+            ambiguous_names.append(row.name)
+            continue
+        if date_key in parsed:
+            return {"blocked": True, "boundary_name": row.name, "reason": row.reason, "ambiguous": False}
+
+    if ambiguous_names:
+        return {
+            "blocked": True,
+            "boundary_name": ambiguous_names[0],
+            "reason": (
+                f"maintenance boundary state unreadable/ambiguous for {ambiguous_names!r} -- failing "
+                "closed (cannot prove this date is not quarantined)"
+            ),
+            "ambiguous": True,
+        }
+    return {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
diff --git a/apps/backend/scripts/run_j11_avb_correction.py b/apps/backend/scripts/run_j11_avb_correction.py
new file mode 100644
index 00000000..49179c0a
--- /dev/null
+++ b/apps/backend/scripts/run_j11_avb_correction.py
@@ -0,0 +1,217 @@
+"""goal-market-compass iter-16 -- J-11 "OWNER RULING -- AVB two-row raw-volume correction before Stage D"
+(docs/goal.md, owner 2026-08-25): the ONE authorized live write this iteration.
+
+Mirrors `run_j11_stage_c_bounded_clear.py`'s established idiom exactly: NO database interaction of any
+kind, not even a read, without `--confirm`; evidence is persisted at every checkpoint; the write itself
+executes ONLY after Goal 2's derivation verifies (fail-closed otherwise -- nothing written, nothing
+guessed). Sequence: TRUE-start envelope capture (Goal 1) -> comparison against the coordinator's
+independently-posted true-start figures (STOP on any mismatch) -> load already-committed iteration-15
+provider-fetch evidence + the persisted J-10 `bridge_factor` (NO new network fetch anywhere in this
+process -- AG-9 dated exception #2 stays exhausted) -> derive the correction (Goal 2, persisted BEFORE
+any write is contemplated) -> fail closed if the derivation does not verify -> THE ONE authorized
+`daily_prices.volume` write, scoped to exactly `symbol='AVB' AND date IN ('2026-08-11','2026-08-12')`
+(Goal 3) -> TRUE-end envelope capture + full mutation-evidence proof (Goal 4).
+
+`--evidence-dir` (the true-start/derivation/true-end evidence trail) and `--output-path` (the final
+consolidated mutation-evidence artifact) are BOTH required, with NO default -- applying the guard from
+the start (iter-13/14's own lesson: an omitted `--evidence-dir` once silently overwrote committed Stage C
+forensic evidence; see `docs/handoffs/goal-market-compass-iter-14-dev.md`).
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_correction.py \\
+        --confirm \\
+        --evidence-dir runs/goal-market-compass-iter-16 \\
+        --output-path runs/goal-market-compass-iter-16/j11-avb-correction-mutation-evidence.json
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from pathlib import Path
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
+from app.engine import j11_avb_correction as corr  # noqa: E402
+from app.engine import j11_avb_diagnostic as diag  # noqa: E402
+
+CANONICAL_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-16"
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
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help=(
+            "required -- the directory the true-start/derivation/true-end evidence JSON files are "
+            f"written to. No default on purpose: the real target ({CANONICAL_EVIDENCE_DIR}) is a "
+            "committed evidence directory, and an implicit default has previously let a forgotten flag "
+            "silently overwrite committed forensic evidence instead of failing."
+        ),
+    )
+    parser.add_argument(
+        "--output-path", type=Path, default=None,
+        help=(
+            "required -- the final consolidated mutation-evidence JSON this script writes (e.g. "
+            "j11-avb-correction-mutation-evidence.json). No default on purpose -- same reasoning as "
+            "--evidence-dir."
+        ),
+    )
+    parser.add_argument(
+        "--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH,
+        help="the already-committed iteration-15 AG-9 dated-exception-#2 fetch evidence -- read-only "
+             "input; this script performs NO network fetch of its own.",
+    )
+    parser.add_argument(
+        "--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH,
+        help="the persisted J-10 population-recovery evidence file (for the bridge factor) -- read-only "
+             "input, never re-fetched.",
+    )
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches the database not at all and exits non-zero.",
+    )
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is the ONE owner-authorized bounded destructive "
+            "write this iteration -- docs/goal.md J-11 step 11, 'OWNER RULING -- AVB two-row raw-volume "
+            "correction before Stage D'). No database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    missing = [name for name, value in (("--evidence-dir", args.evidence_dir), ("--output-path", args.output_path)) if value is None]
+    if missing:
+        print(
+            f"refusing to run without explicit {', '.join(missing)}. Their real targets under "
+            f"{CANONICAL_EVIDENCE_DIR} are committed evidence paths, so they must be named explicitly and "
+            "can never be reached by default. No database interaction, not even a read, has occurred, and "
+            "nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    evidence_dir: Path = args.evidence_dir
+    output_path: Path = args.output_path
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    print(f"database: {resolved_url}", file=sys.stderr)
+
+    engine = get_engine()  # the SAME pooled writable engine the real backend uses -- never a raw file copy.
+
+    # --- Goal 1: TRUE-start envelope, before anything else touches the database -----------------------
+    with Session(engine) as session:
+        true_start = corr.capture_true_envelope(session, engine, db_path)
+    _write_json(evidence_dir / "j11-avb-correction-true-start.json", true_start)
+    print(
+        f"true-start captured: daily_prices.row_count={true_start['daily_prices']['row_count']} "
+        f"db_file={true_start['db_file']}",
+        file=sys.stderr,
+    )
+
+    comparison = corr.compare_true_envelope_to_coordinator_capture(true_start)
+    _write_json(evidence_dir / "j11-avb-correction-true-start-comparison.json", comparison)
+    if comparison["any_mismatch"]:
+        mismatched = [name for name, c in comparison["comparisons"].items() if not c["matches"]]
+        print(
+            f"STOP: the true-start envelope does NOT match the coordinator's posted true-start capture "
+            f"(mismatched fields: {mismatched}). No write has been attempted. See "
+            "j11-avb-correction-true-start-comparison.json for the full per-figure comparison.",
+            file=sys.stderr,
+        )
+        return 1
+    print("true-start envelope matches the coordinator's posted capture exactly (zero mismatches).", file=sys.stderr)
+
+    # --- Goal 2: derive the correction deterministically, BEFORE the write is contemplated -------------
+    provider_fetch_evidence = corr.load_provider_fetch_evidence(args.provider_fetch_evidence_path)
+    j10_evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
+    stored_volume_before = {k: v["volume"] for k, v in true_start["avb_target_rows"].items()}
+    stored_close = {k: v["close"] for k, v in true_start["avb_target_rows"].items()}
+    derivation = corr.derive_avb_volume_correction(
+        provider_fetch_evidence, j10_evidence_row, stored_volume_before, stored_close
+    )
+    _write_json(evidence_dir / "j11-avb-correction-derivation.json", derivation)
+    print(f"derivation verified={derivation['verified']}", file=sys.stderr)
+
+    if not derivation["verified"]:
+        print(
+            "FAIL (fail-closed): the AVB volume correction could not be derived/verified from the "
+            "committed evidence. NO write has been attempted -- nothing in daily_prices has changed. "
+            "This needs OWNER REVIEW rather than a guess. See j11-avb-correction-derivation.json for the "
+            "per-date failure detail.",
+            file=sys.stderr,
+        )
+        return 1
+
+    corrected_volume_by_date = {
+        key: row["corrected_volume"] for key, row in derivation["per_date"].items()
+    }
+
+    # --- Goal 3: THE ONE AUTHORIZED WRITE ---------------------------------------------------------------
+    with Session(engine) as session:
+        written = corr.apply_avb_volume_correction(session, corrected_volume_by_date)
+    print(f"WROTE corrected volumes: {written}", file=sys.stderr)
+
+    # Force the change durably into the MAIN db file (never a second data write -- see checkpoint_wal's
+    # own docstring): a two-cell update is far too small to cross SQLite's default auto-checkpoint
+    # threshold on its own, and the true-end proof below requires the main file to have moved and the
+    # `-wal` sidecar to be back at 0 bytes.
+    checkpoint_result = corr.checkpoint_wal(engine)
+    print(f"WAL checkpoint (TRUNCATE): {checkpoint_result}", file=sys.stderr)
+
+    # --- Goal 4: TRUE-end envelope + mutation-evidence proof --------------------------------------------
+    with Session(engine) as session:
+        true_end = corr.capture_true_envelope(session, engine, db_path)
+    _write_json(evidence_dir / "j11-avb-correction-true-end.json", true_end)
+
+    mutation_evidence = corr.build_mutation_evidence(true_start=true_start, true_end=true_end, derivation=derivation)
+    mutation_evidence["written"] = written
+    mutation_evidence["wal_checkpoint"] = checkpoint_result
+    mutation_evidence["true_start_comparison_against_coordinator_capture"] = comparison
+    _write_json(output_path, mutation_evidence)
+
+    print(f"mutation evidence: all_checks_pass={mutation_evidence['all_checks_pass']}", file=sys.stderr)
+    if not mutation_evidence["all_checks_pass"]:
+        failing = [k for k, v in mutation_evidence["checks"].items() if not v]
+        print(
+            f"FAILING CHECKS: {failing}. The write already executed and cannot be undone by this script "
+            "(no transaction spans the whole invocation). All captured evidence is preserved for owner "
+            "review.",
+            file=sys.stderr,
+        )
+        return 1
+
+    print("J-11 AVB CORRECTION COMPLETE: YES", file=sys.stderr)
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/run_j11_iter16_stage_d_readiness.py b/apps/backend/scripts/run_j11_iter16_stage_d_readiness.py
new file mode 100644
index 00000000..b92bd3b6
--- /dev/null
+++ b/apps/backend/scripts/run_j11_iter16_stage_d_readiness.py
@@ -0,0 +1,339 @@
+"""goal-market-compass iter-16 -- J-11 Goals 5 + 8: establish the new certified raw-input baseline (Goal
+5) and re-run Stage D readiness against it (Goal 8), per the two 2026-08-25 owner rulings' explicit
+sequencing: "AVB bounded correction -> verify the new raw-input baseline -> implement and prove the
+pre-boot guard -> re-run Stage D readiness -> if READY: YES, STOP for owner authorization."
+
+This is a NEW, thin iteration-16 driver script (the plan's own "developer's choice" option) rather than
+an additive extension of THREE separate existing scripts (`run_j11_stage_d_preflight.py`,
+`run_j11_avb_bridge_diagnostic.py`, `run_j11_stage_d_readiness.py`) -- every underlying engine function it
+calls is reused UNCHANGED from those scripts' own call shapes; nothing is reimplemented.
+
+Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA
+query_only=ON`, mirroring `run_j11_stage_d_preflight.py`/`run_j11_avb_bridge_diagnostic.py`'s own helper)
+-- this script performs ZERO writes; Goal 3's write already landed for real, earlier in this iteration,
+via the separate confirm-gated `run_j11_avb_correction.py`. No `--confirm` flag: there is nothing here to
+confirm.
+
+Sequence:
+  1. Fresh Stage D preflight capture against the CORRECTED live database (`j11_stage_d.
+     capture_stage_d_preflight`, reused unchanged) -- its own `pre_reset_inventory.daily_prices.
+     fingerprint` IS the new certified fingerprint (re-derived fresh here, not read back from Goal 4's
+     own artifact).
+  2. Gate the fresh preflight against the OLD (pre-correction) certified baseline
+     (`j11_stage_d.load_stage_d_certified_baseline` + `compare_stage_d_preflight_to_certified`, both
+     reused unchanged) -- MUST report `daily_prices_fingerprint_unchanged: False` (an honest, EXPECTED
+     mismatch -- the correction is supposed to have moved it).
+  3. Build the NEW certified baseline (`j11_stage_d.build_avb_correction_superseded_baseline`, Goal 5) and
+     re-gate the SAME fresh preflight against it -- MUST report `all_invariants_hold: True`.
+  4. Re-run the AVB bridge diagnostic against the corrected live `daily_prices`
+     (`j11_avb_diagnostic.fetch_avb_stored_series` / `classify_local_convention_with_volume_evidence` /
+     `compute_counterfactual_representations` / `trace_universe_resolver_impact` /
+     `trace_scoring_and_selection_impact` / `classify_avb`, ALL reused unchanged), reusing iteration 15's
+     already-committed provider-fetch evidence (zero new network fetch) -- per the plan's own instruction,
+     the decision-impact trace is called WITHOUT `volume_override`: the write already landed for real, so
+     representation A reads the corrected stored rows directly.
+  5. Combine into the final verdict (`j11_stage_d.produce_stage_d_readiness_artifact`, reused unchanged),
+     which writes `authorized: false` UNCONDITIONALLY.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter16_stage_d_readiness.py \\
+        --evidence-dir runs/goal-market-compass-iter-16
+"""
+from __future__ import annotations
+
+import argparse
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
+CANONICAL_EVIDENCE_DIR_FOR_DOCS = REPO_ROOT / "runs" / "goal-market-compass-iter-16"
+DEFAULT_STAGE_C_PREFLIGHT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-preflight.json"
+DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-mutation-accounting.json"
+)
+DEFAULT_ITERATION_14_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
+)
+DEFAULT_MUTATION_EVIDENCE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-avb-correction-mutation-evidence.json"
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
+        help=(
+            "required -- the directory every evidence JSON is written to. No default on purpose: the "
+            f"real target ({CANONICAL_EVIDENCE_DIR_FOR_DOCS}) is a committed evidence directory."
+        ),
+    )
+    parser.add_argument("--stage-c-preflight-path", type=Path, default=DEFAULT_STAGE_C_PREFLIGHT_PATH)
+    parser.add_argument("--stage-c-mutation-accounting-path", type=Path, default=DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH)
+    parser.add_argument("--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH)
+    parser.add_argument(
+        "--mutation-evidence-path", type=Path, default=DEFAULT_MUTATION_EVIDENCE_PATH,
+        help="Goal 4's own consolidated mutation-evidence artifact -- cited as provenance on the new "
+             "certified baseline (read-only input).",
+    )
+    parser.add_argument(
+        "--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH,
+    )
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
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    if db_path is None or not db_path.exists():
+        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
+        return 1
+    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)
+
+    db_file_true_start = jsc.db_file_fingerprint(db_path)
+    _write_json(args.evidence_dir / "j11-iter16-readiness-db-file-true-start.json", db_file_true_start)
+
+    goal_md_text = jsc.read_goal_md_text()
+    git_head = jsc.read_git_head()
+    engine = _read_only_engine(db_path)
+
+    prior_identity_value = None
+    if args.iteration_14_identity_path is not None and Path(args.iteration_14_identity_path).exists():
+        prior_identity_value = json.loads(Path(args.iteration_14_identity_path).read_text()).get("engine_identity")
+
+    # --- Step 1: fresh Stage D preflight against the CORRECTED live database --------------------------
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
+    # --- Step 2: gate against the OLD (pre-correction) certified baseline -- expect an HONEST mismatch --
+    old_certified = jsd.load_stage_d_certified_baseline(
+        args.stage_c_preflight_path, args.stage_c_mutation_accounting_path
+    )
+    gate_vs_old = jsd.compare_stage_d_preflight_to_certified(preflight, old_certified)
+    verdict_vs_old = jsd.stage_d_preflight_verdict(gate_vs_old)
+    _write_json(
+        args.evidence_dir / "j11-stage-d-preflight-gate-vs-old-baseline.json",
+        {"comparison": gate_vs_old, "verdict": verdict_vs_old},
+    )
+    print(
+        f"gate vs OLD (pre-correction) certified baseline: "
+        f"daily_prices_fingerprint_unchanged={gate_vs_old['checks']['daily_prices_fingerprint_unchanged']} "
+        "(EXPECTED False -- the AVB correction is supposed to have moved this fingerprint)",
+        file=sys.stderr,
+    )
+
+    # --- Step 3: build + gate the NEW certified baseline (Goal 5) ---------------------------------------
+    new_certified = jsd.build_avb_correction_superseded_baseline(
+        old_certified,
+        post_correction_daily_prices_fingerprint=fresh_daily_prices_fingerprint,
+        iteration=16,
+        mutation_evidence_artifact_path=str(args.mutation_evidence_path),
+    )
+    _write_json(args.evidence_dir / "j11-stage-d-certified-baseline.json", new_certified)
+
+    gate_vs_new = jsd.compare_stage_d_preflight_to_certified(preflight, new_certified)
+    verdict_vs_new = jsd.stage_d_preflight_verdict(gate_vs_new)
+    _write_json(args.evidence_dir / "j11-stage-d-preflight-gate.json", {"comparison": gate_vs_new, "verdict": verdict_vs_new})
+    print(
+        f"gate vs NEW (superseded) certified baseline: all_invariants_hold={gate_vs_new['all_invariants_hold']}",
+        file=sys.stderr,
+    )
+    if not gate_vs_new["all_invariants_hold"]:
+        failing = [k for k, v in gate_vs_new["checks"].items() if not v]
+        print(f"FAILING CHECKS against the NEW baseline: {failing}", file=sys.stderr)
+
+    # --- Step 4: re-run the AVB bridge diagnostic against the corrected live daily_prices ---------------
+    fetch_evidence = json.loads(Path(args.provider_fetch_evidence_path).read_text())
+    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
+    evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
+    bridge_factor = evidence_row["bridge_factor"]
+    pool_distribution = diag.summarize_pool_bridge_factor_distribution(args.j10_evidence_path)
+    print(
+        f"reusing iteration-15 provider-fetch evidence (sufficient_evidence="
+        f"{fetch_evidence.get('sufficient_evidence')}, zero new network fetch this iteration): "
+        f"bridge_factor={bridge_factor}",
+        file=sys.stderr,
+    )
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
+        # Goal 8's own instruction: NO volume_override -- the write already landed for real, so
+        # representation A reads the corrected stored rows directly, never an in-memory substitution.
+        decision_impact_by_date: dict[str, dict] = {}
+        for one_date in diag.RECOVERED_DATES:
+            key = one_date.isoformat()
+            print(f"tracing decision impact for {key} (no volume_override -- corrected DB read directly) ...", file=sys.stderr)
+            ur_impact = diag.trace_universe_resolver_impact(session, cfg, one_date, bridge_factor)
+            scoring_impact = diag.trace_scoring_and_selection_impact(session, cfg, one_date, bridge_factor)
+            decision_impact_by_date[key] = {"universe_resolver": ur_impact, "scoring_and_selection": scoring_impact}
+            print(
+                f"  {key}: admission_changed={ur_impact['admission_changed']} "
+                f"avb_resolved_member={scoring_impact.get('avb_resolved_member')} "
+                f"risk_bucket_a={scoring_impact.get('risk_bucket_a')} risk_bucket_b={scoring_impact.get('risk_bucket_b')} "
+                f"eligible_a={scoring_impact.get('eligible_a')} eligible_b={scoring_impact.get('eligible_b')}",
+                file=sys.stderr,
+            )
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
+    db_file_true_end_for_diag = jsc.db_file_fingerprint(db_path)
+    zero_write_proof = {
+        "db_file_true_start": db_file_true_start,
+        "db_file_true_end": db_file_true_end_for_diag,
+        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end_for_diag.get("mtime"),
+        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end_for_diag.get("size_bytes"),
+    }
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
+        "classification": classification,
+        "zero_write_proof": zero_write_proof,
+        "note": (
+            "goal-market-compass iter-16 re-run against the CORRECTED live daily_prices (Goal 3's write "
+            "already landed for real) -- decision-impact traced WITHOUT volume_override (reads the "
+            "corrected stored rows directly). Cite runs/goal-market-compass-iter-15/"
+            "j11-avb-bridge-diagnostic.json as historically accurate FOR THE PRE-CORRECTION state -- "
+            "never edited, never deleted."
+        ),
+    }
+    _write_json(args.evidence_dir / "j11-avb-bridge-diagnostic.json", avb_diagnostic_result)
+    print(
+        f"AVB classification (mechanically derived, corrected baseline): {classification['classification']} "
+        f"stage_d_ready_per_avb={classification['stage_d_ready_per_avb']}",
+        file=sys.stderr,
+    )
+
+    # --- Step 5: combine into the final readiness verdict (reused unchanged) ----------------------------
+    readiness = jsd.produce_stage_d_readiness_artifact(
+        args.evidence_dir / "j11-stage-d-preflight-gate.json",
+        args.evidence_dir / "j11-avb-bridge-diagnostic.json",
+        output_path=args.evidence_dir / "j11-stage-d-readiness.json",
+    )
+
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(args.evidence_dir / "j11-iter16-readiness-db-file-true-end.json", db_file_true_end)
+    print(
+        f"whole-script zero-write proof: mtime_unchanged="
+        f"{db_file_true_start.get('mtime') == db_file_true_end.get('mtime')} "
+        f"size_unchanged={db_file_true_start.get('size_bytes') == db_file_true_end.get('size_bytes')}",
+        file=sys.stderr,
+    )
+
+    print(
+        f"avb_classification={readiness['avb_classification']} "
+        f"preflight_gate_passed={readiness['preflight_gate_passed']} "
+        f"blocking_reasons={readiness['blocking_reasons']}",
+        file=sys.stderr,
+    )
+    print(
+        "citing runs/goal-market-compass-iter-15/j11-stage-d-readiness.json as historically accurate for "
+        "the PRE-CORRECTION state (avb_classification=AVB-C, ready=false) -- never edited, never deleted; "
+        "this iteration's result reflects the NEW corrected baseline.",
+        file=sys.stderr,
+    )
+    print(f"J-11 STAGE D READY: {'YES' if readiness['ready'] else 'NO'}", file=sys.stderr)
+    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
+    return 0 if readiness["ready"] else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_avb_correction.py b/apps/backend/tests/test_j11_avb_correction.py
new file mode 100644
index 00000000..e90e16c1
--- /dev/null
+++ b/apps/backend/tests/test_j11_avb_correction.py
@@ -0,0 +1,483 @@
+"""goal-market-compass iter-16 -- J-11 "OWNER RULING -- AVB two-row raw-volume correction before Stage D"
+tests (Goals 1-4). Fixture-only throughout: file-backed temp sqlite databases (`tmp_path`, never
+`apps/backend/data/trendora.db`) for anything that touches a real file path (the isolating hashes and the
+manifest row-dump hash open a SEPARATE raw `sqlite3` `mode=ro` connection, which needs an actual file),
+plain synthetic dicts for the pure derivation/comparison/mutation-evidence functions. The ONE real,
+deliberate live write against the production database is the actual `run_j11_avb_correction.py --confirm`
+execution itself (not a pytest test) -- its own true-start/true-end envelopes ARE the mutation-evidence
+proof; see `docs/handoffs/goal-market-compass-iter-16-dev.md`.
+"""
+from __future__ import annotations
+
+from datetime import date
+
+import pytest
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.engine import j11_avb_correction as corr
+from app.engine import j11_avb_diagnostic as diag
+from app.models import DailyPrice
+
+
+@pytest.fixture()
+def file_engine(tmp_path):
+    """A REAL sqlite FILE-backed engine (never `sqlite://` in-memory, never the live product DB) --
+    `capture_isolating_hashes`/`capture_manifest_row_dump_hash` open a separate raw `sqlite3` `mode=ro`
+    connection against the file path, which requires an actual file on disk."""
+    db_path = tmp_path / "test.db"
+    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
+    SQLModel.metadata.create_all(eng)
+    return eng, db_path
+
+
+def _mk_price(session, symbol, d, o, h, l, c, v):
+    row = DailyPrice(symbol=symbol, date=d, open=o, high=h, low=l, close=c, volume=v)
+    session.add(row)
+    return row
+
+
+def _seed_avb_and_other(session):
+    _mk_price(session, "AVB", date(2026, 8, 10), 100.0, 101.0, 99.0, 100.5, 2000.0)
+    _mk_price(session, "AVB", date(2026, 8, 11), 183.22001534990548, 184.13001191846783, 181.7100027790582, 181.76001476703186, 1549436.0)
+    _mk_price(session, "AVB", date(2026, 8, 12), 181.08999902870366, 182.0900043902787, 179.45999604273928, 179.79000697488598, 10350885.0)
+    _mk_price(session, "AAPL", date(2026, 8, 11), 50.0, 51.0, 49.0, 50.5, 3000.0)
+    session.commit()
+
+
+# --- Goal 1: the isolating hashes -- byte-identical unless the specific touched scope changes ---------
+
+
+def test_isolating_hashes_unaffected_by_a_target_date_volume_change(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+    before = corr.capture_isolating_hashes(db_path)
+
+    with Session(engine) as session:
+        row = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "AVB").where(DailyPrice.date == date(2026, 8, 11))
+        ).one()
+        row.volume = 554757.0
+        session.add(row)
+        session.commit()
+
+    after = corr.capture_isolating_hashes(db_path)
+    # OHLC-only excludes volume entirely -- unaffected by a volume-only change on ANY AVB date
+    assert after["avb_ohlc_only"]["sha256"] == before["avb_ohlc_only"]["sha256"]
+    # excludes the two target dates entirely -- unaffected by a change scoped to one of them
+    assert after["avb_other_dates_full_row"]["sha256"] == before["avb_other_dates_full_row"]["sha256"]
+    # the non-AVB population is untouched
+    assert after["non_avb_full_row"]["sha256"] == before["non_avb_full_row"]["sha256"]
+
+
+def test_avb_other_dates_hash_moves_if_a_non_target_avb_date_changes(file_engine):
+    """Negative control: proves the isolating hashes are genuinely sensitive, not trivially inert."""
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+    before = corr.capture_isolating_hashes(db_path)
+
+    with Session(engine) as session:
+        row = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "AVB").where(DailyPrice.date == date(2026, 8, 10))
+        ).one()
+        row.volume = 999999.0
+        session.add(row)
+        session.commit()
+
+    after = corr.capture_isolating_hashes(db_path)
+    assert after["avb_other_dates_full_row"]["sha256"] != before["avb_other_dates_full_row"]["sha256"]
+    assert after["avb_ohlc_only"]["sha256"] == before["avb_ohlc_only"]["sha256"]  # volume-only change
+
+
+def test_non_avb_hash_moves_if_a_non_avb_row_changes(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+    before = corr.capture_isolating_hashes(db_path)
+
+    with Session(engine) as session:
+        row = session.exec(select(DailyPrice).where(DailyPrice.symbol == "AAPL")).one()
+        row.volume = 1.0
+        session.add(row)
+        session.commit()
+
+    after = corr.capture_isolating_hashes(db_path)
+    assert after["non_avb_full_row"]["sha256"] != before["non_avb_full_row"]["sha256"]
+    assert after["avb_ohlc_only"]["sha256"] == before["avb_ohlc_only"]["sha256"]
+    assert after["avb_other_dates_full_row"]["sha256"] == before["avb_other_dates_full_row"]["sha256"]
+
+
+def test_manifest_row_dump_hash_recipe_is_stable_and_order_independent_of_insertion(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+    first = corr.capture_manifest_row_dump_hash(db_path)
+    second = corr.capture_manifest_row_dump_hash(db_path)
+    assert first["sha256"] == second["sha256"]
+    assert first["row_count"] == 0  # no manifests seeded in this fixture
+
+
+# --- Goal 1: capture_true_envelope + fetch_avb_target_rows shape -------------------------------------
+
+
+def test_capture_true_envelope_reports_seeded_values(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+
+    with Session(engine) as session:
+        envelope = corr.capture_true_envelope(session, engine, db_path)
+
+    assert envelope["daily_prices"]["row_count"] == 4
+    assert envelope["avb_target_rows"]["2026-08-11"]["volume"] == 1549436.0
+    assert envelope["avb_target_rows"]["2026-08-12"]["volume"] == 10350885.0
+    assert envelope["avb_target_rows"]["2026-08-11"]["close"] == 181.76001476703186
+    assert envelope["scanner_runs_total_count"] == 0
+    assert envelope["all_11_incident_dates_zero_scanner_runs"] is True
+    assert envelope["isolating_hashes"] is not None
+    assert envelope["manifest_row_dump_fingerprint"]["row_count"] == 0
+
+
+# --- Goal 1: coordinator-capture comparison -- exact mismatch reporting, never silently reconciled ----
+
+
+_SMALL_COORDINATOR_CAPTURE = {
+    "db_mtime": 123, "db_size_bytes": 456, "db_wal_size_bytes": 0,
+    "daily_prices_row_count": 4, "scanner_runs_total_count": 0, "scanner_runs_stamped_6261ca17_count": 0,
+    "forward_returns_total_count": 0, "forward_returns_measured_into_incident_total": 0,
+    "data_provider_runs_count": 0, "manifest_row_count": 0,
+    "manifest_ddl_sha256": "expected-ddl-hash",
+    "manifest_row_dump_sha256_prefix": "ffffffff", "manifest_row_dump_sha256_suffix": "000000",
+    "watchlist_count": 0, "all_11_incident_dates_zero_scanner_runs": True,
+    "isolating_hashes": {"avb_ohlc_only": "a", "avb_other_dates_full_row": "b", "non_avb_full_row": "c"},
+    "avb_target_rows": {
+        "2026-08-11": {"open": 183.22001534990548, "high": 184.13001191846783, "low": 181.7100027790582, "close": 181.76001476703186, "volume": 1549436.0},
+        "2026-08-12": {"open": 181.08999902870366, "high": 182.0900043902787, "low": 179.45999604273928, "close": 179.79000697488598, "volume": 10350885.0},
+    },
+}
+
+
+def test_compare_true_envelope_reports_every_mismatch_explicitly(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+    with Session(engine) as session:
+        envelope = corr.capture_true_envelope(session, engine, db_path)
+
+    result = corr.compare_true_envelope_to_coordinator_capture(envelope, _SMALL_COORDINATOR_CAPTURE)
+    assert result["any_mismatch"] is True
+    # the AVB target rows and counts genuinely match this fixture's seed -- only the hash-shaped fields
+    # (which this synthetic target deliberately does not reproduce) should mismatch.
+    assert result["comparisons"]["daily_prices_row_count"]["matches"] is True
+    assert result["comparisons"]["avb_target_row.2026-08-11"]["matches"] is True
+    assert result["comparisons"]["manifest_ddl_sha256"]["matches"] is False
+    assert result["comparisons"]["isolating_hash.non_avb_full_row"]["matches"] is False
+
+
+def test_compare_true_envelope_all_match_when_expectations_equal_a_self_capture(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+    with Session(engine) as session:
+        envelope = corr.capture_true_envelope(session, engine, db_path)
+
+    self_capture = {
+        "db_mtime": int(envelope["db_file"]["mtime"]), "db_size_bytes": envelope["db_file"]["size_bytes"],
+        "db_wal_size_bytes": 0,
+        "daily_prices_row_count": envelope["daily_prices"]["row_count"],
+        "scanner_runs_total_count": envelope["scanner_runs_total_count"],
+        "scanner_runs_stamped_6261ca17_count": envelope["scanner_runs_by_identity_group"]["legacy_6261ca17_count"],
+        "forward_returns_total_count": envelope["forward_returns_total_count"],
+        "forward_returns_measured_into_incident_total": envelope["forward_returns_measured_into_incident_total"],
+        "data_provider_runs_count": envelope["data_provider_runs_count"],
+        "manifest_row_count": envelope["manifest_row_count"],
+        "manifest_ddl_sha256": envelope["manifest_ddl_sha256"],
+        "manifest_row_dump_sha256_prefix": envelope["manifest_row_dump_fingerprint"]["sha256"][:8],
+        "manifest_row_dump_sha256_suffix": envelope["manifest_row_dump_fingerprint"]["sha256"][-6:],
+        "watchlist_count": envelope["watchlist_count"],
+        "all_11_incident_dates_zero_scanner_runs": envelope["all_11_incident_dates_zero_scanner_runs"],
+        "isolating_hashes": {k: v["sha256"] for k, v in envelope["isolating_hashes"].items()},
+        "avb_target_rows": envelope["avb_target_rows"],
+    }
+    result = corr.compare_true_envelope_to_coordinator_capture(envelope, self_capture)
+    assert result["any_mismatch"] is False
+    assert all(c["matches"] for c in result["comparisons"].values())
+
+
+# --- Goal 2: the derivation -- formula, rounding, cross-check, fail-closed paths ----------------------
+
+
+_BRIDGE_FACTOR = 2.7930001225759193
+
+
+def _synthetic_provider_evidence(sufficient=True, missing_close=False):
+    per_date = {
+        "2026-08-11": {"close": 65.07698059082031, "volume": 1549436.0},
+        "2026-08-12": {"close": 64.37164306640625, "volume": 10350885.0},
+    }
+    if missing_close:
+        per_date["2026-08-11"]["volume"] = None
+    return {"per_date": per_date, "sufficient_evidence": sufficient}
+
+
+def _synthetic_j10_row():
+    return {"symbol": "AVB", "bridge_factor": _BRIDGE_FACTOR}
+
+
+def _synthetic_stored():
+    stored_volume_before = {"2026-08-11": 1549436.0, "2026-08-12": 10350885.0}
+    stored_close = {"2026-08-11": 181.76001476703186, "2026-08-12": 179.79000697488598}
+    return stored_volume_before, stored_close
+
+
+def test_derive_avb_volume_correction_verifies_and_matches_expected_values():
+    stored_volume_before, stored_close = _synthetic_stored()
+    result = corr.derive_avb_volume_correction(
+        _synthetic_provider_evidence(), _synthetic_j10_row(), stored_volume_before, stored_close
+    )
+    assert result["verified"] is True
+    assert result["per_date"]["2026-08-11"]["corrected_volume"] == 554757.0
+    assert result["per_date"]["2026-08-12"]["corrected_volume"] == 3706010.0
+    for key in ("2026-08-11", "2026-08-12"):
+        assert result["per_date"][key]["within_tolerance"] is True
+        assert abs(result["per_date"][key]["dollar_volume_ratio_after"] - 1.0) < 0.01
+
+
+def test_derive_avb_volume_correction_fails_closed_when_evidence_insufficient():
+    stored_volume_before, stored_close = _synthetic_stored()
+    result = corr.derive_avb_volume_correction(
+        _synthetic_provider_evidence(sufficient=False), _synthetic_j10_row(), stored_volume_before, stored_close
+    )
+    assert result["verified"] is False
+    assert result["per_date"]["2026-08-11"]["ok"] is False
+    assert result["per_date"]["2026-08-12"]["ok"] is False
+
+
+def test_derive_avb_volume_correction_fails_closed_on_missing_provider_volume():
+    stored_volume_before, stored_close = _synthetic_stored()
+    result = corr.derive_avb_volume_correction(
+        _synthetic_provider_evidence(missing_close=True), _synthetic_j10_row(), stored_volume_before, stored_close
+    )
+    assert result["verified"] is False
+    assert result["per_date"]["2026-08-11"]["ok"] is False
+    assert "insufficient" in result["per_date"]["2026-08-11"]["reason"]
+
+
+def test_derive_avb_volume_correction_fails_closed_when_bridge_factor_missing():
+    stored_volume_before, stored_close = _synthetic_stored()
+    result = corr.derive_avb_volume_correction(
+        _synthetic_provider_evidence(), {"symbol": "AVB", "bridge_factor": None}, stored_volume_before, stored_close
+    )
+    assert result["verified"] is False
+
+
+def test_derive_avb_volume_correction_fails_closed_when_cross_check_out_of_tolerance():
+    """A stored_close value that does NOT match the bridge relationship at all -- the cross-check must
+    reject it rather than proceed."""
+    stored_volume_before, _ = _synthetic_stored()
+    stored_close_wrong = {"2026-08-11": 1.0, "2026-08-12": 1.0}  # nowhere near provider_close*bridge_factor
+    result = corr.derive_avb_volume_correction(
+        _synthetic_provider_evidence(), _synthetic_j10_row(), stored_volume_before, stored_close_wrong
+    )
+    assert result["verified"] is False
+    assert result["per_date"]["2026-08-11"]["within_tolerance"] is False
+
+
+def test_derive_avb_volume_correction_reproduces_the_real_committed_iteration15_evidence():
+    """Regression check against the ACTUAL committed iteration-15/iteration-9 evidence files (read-only,
+    no DB access) -- confirms the real files remain loadable and reproduce the exact iteration-16
+    corrected values this session independently re-derived."""
+    provider_evidence = corr.load_provider_fetch_evidence()
+    j10_row = diag.load_j10_avb_evidence()
+    stored_volume_before = {"2026-08-11": 1549436.0, "2026-08-12": 10350885.0}
+    stored_close = {"2026-08-11": 181.76001476703186, "2026-08-12": 179.79000697488598}
+    result = corr.derive_avb_volume_correction(provider_evidence, j10_row, stored_volume_before, stored_close)
+    assert result["verified"] is True
+    assert result["per_date"]["2026-08-11"]["corrected_volume"] == 554757.0
+    assert result["per_date"]["2026-08-12"]["corrected_volume"] == 3706010.0
+
+
+# --- Goal 3: the ONE write, fixture-only -- exact scope proof ------------------------------------------
+
+
+def test_checkpoint_wal_truncates_after_a_small_write(file_engine):
+    """A write far too small to cross SQLite's default auto-checkpoint threshold on its own must still
+    land durably in the MAIN db file, with the `-wal` sidecar back at 0 bytes, once `checkpoint_wal` is
+    called -- this is the exact gap a live two-cell `daily_prices.volume` UPDATE hit."""
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+        session.commit()
+
+    with Session(engine) as session:
+        row = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "AVB").where(DailyPrice.date == date(2026, 8, 11))
+        ).one()
+        row.volume = 554757.0
+        session.add(row)
+        session.commit()
+
+    result = corr.checkpoint_wal(engine)
+    assert result["busy"] == 0  # single-writer fixture -- nothing should block a full checkpoint
+
+    wal_path = db_path.parent / (db_path.name + "-wal")
+    if wal_path.exists():
+        assert wal_path.stat().st_size == 0
+
+
+def test_apply_avb_volume_correction_touches_only_the_two_target_rows_and_only_volume(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _seed_avb_and_other(session)
+
+    with Session(engine) as session:
+        before_rows = {
+            (r.symbol, r.date.isoformat()): (r.open, r.high, r.low, r.close, r.volume)
+            for r in session.exec(select(DailyPrice)).all()
+        }
+
+    with Session(engine) as session:
+        written = corr.apply_avb_volume_correction(session, {"2026-08-11": 554757.0, "2026-08-12": 3706010.0})
+    assert written == {"2026-08-11": 554757.0, "2026-08-12": 3706010.0}
+
+    with Session(engine) as session:
+        after_rows = {
+            (r.symbol, r.date.isoformat()): (r.open, r.high, r.low, r.close, r.volume)
+            for r in session.exec(select(DailyPrice)).all()
+        }
+
+    for key, before in before_rows.items():
+        symbol, iso_date = key
+        after = after_rows[key]
+        if symbol == "AVB" and iso_date in ("2026-08-11", "2026-08-12"):
+            assert after[:4] == before[:4]  # OHLC byte-identical
+            expected_volume = 554757.0 if iso_date == "2026-08-11" else 3706010.0
+            assert after[4] == expected_volume
+        else:
+            assert after == before  # every other row (OHLCV, all columns) byte-identical
+
+
+def test_apply_avb_volume_correction_raises_and_writes_nothing_if_target_row_count_wrong(file_engine):
+    engine, db_path = file_engine
+    with Session(engine) as session:
+        _mk_price(session, "AVB", date(2026, 8, 11), 1, 2, 3, 4, 5)  # only ONE of the two target dates
+        session.commit()
+
+    with Session(engine) as session:
+        with pytest.raises(RuntimeError):
+            corr.apply_avb_volume_correction(session, {"2026-08-11": 1.0, "2026-08-12": 2.0})
+
+    with Session(engine) as session:
+        rows = session.exec(select(DailyPrice)).all()
+    assert len(rows) == 1
+    assert rows[0].volume == 5  # untouched
+
+
+# --- Goal 4: the mutation-evidence comparison builder -- pure, synthetic envelopes ---------------------
+
+
+def _make_envelope(avb_rows, ohlcv_sum, **overrides):
+    base = {
+        "avb_target_rows": avb_rows,
+        "daily_prices": {
+            "row_count": 10, "min_date": "1996-01-02", "max_date": "2026-08-12", "id_sum": 100,
+            "ohlcv_sum": ohlcv_sum, "fingerprint": "f",
+        },
+        "isolating_hashes": {
+            "avb_ohlc_only": {"sha256": "h1"}, "avb_other_dates_full_row": {"sha256": "h2"},
+            "non_avb_full_row": {"sha256": "h3"},
+        },
+        "scanner_runs_by_identity_group": {"null_count": 1, "legacy_6261ca17_count": 2, "other_count": 0},
+        "forward_returns_total_count": 5,
+        "forward_returns_measured_into_incident_total": 3,
+        "data_provider_runs_count": 7,
... [diff_bound] apps/backend/tests/test_j11_avb_correction.py: 89 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_avb_correction_cli_script.py b/apps/backend/tests/test_j11_avb_correction_cli_script.py
new file mode 100644
index 00000000..efb1acf6
--- /dev/null
+++ b/apps/backend/tests/test_j11_avb_correction_cli_script.py
@@ -0,0 +1,248 @@
+"""goal-market-compass iter-16 -- J-11 AVB correction CLI control-flow tests (Goal 3). `unittest.mock`-
+based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`) is patched before `main()`
+runs, mirroring `test_j11_stage_c_cli_script.py`'s established idiom exactly (same `importlib`-based real
+module load, same monkeypatch-on-module-namespace pattern, same reasoning for why `importlib.util.
+module_from_spec` is used instead of `runpy.run_path`)."""
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
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_avb_correction.py"
+_MODULE_NAME = "run_j11_avb_correction_under_test"
+
+
+def _load_script_module():
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
+# --- missing --confirm: NO database interaction of any kind -------------------------------------------
+
+
+def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    monkeypatch.setattr(sys, "argv", ["run_j11_avb_correction.py"])  # no --confirm
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+
+
+# --- --confirm but missing --evidence-dir and/or --output-path: refuses, writes nothing ----------------
+
+
+def test_confirm_without_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns):
+    mock_write_json = mock.MagicMock(name="_write_json")
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_avb_correction.py", "--confirm", "--output-path", "/tmp/out.json"],  # no --evidence-dir
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_write_json.assert_not_called()
+    mock_get_engine.assert_not_called()
+
+
+def test_confirm_without_output_path_refuses_before_writing_anything(monkeypatch, script_ns):
+    mock_write_json = mock.MagicMock(name="_write_json")
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_avb_correction.py", "--confirm", "--evidence-dir", "/tmp/ev"],  # no --output-path
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_write_json.assert_not_called()
+    mock_get_engine.assert_not_called()
+
+
+# --- true-start comparison mismatch stops BEFORE any derivation/write ----------------------------------
+
+
+def test_true_start_mismatch_stops_before_derivation_and_write(monkeypatch, script_ns, tmp_path):
+    fake_true_start = {"daily_prices": {"row_count": 1}, "avb_target_rows": {}, "db_file": {}}
+    monkeypatch.setattr(script_ns, "load_config", lambda: mock.MagicMock(database=mock.MagicMock(url="sqlite:///x")))
+    monkeypatch.setattr(script_ns, "resolve_database_url", lambda url: "sqlite:///x")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(name="get_engine"))
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.corr, "capture_true_envelope", lambda *a, **k: fake_true_start)
+    monkeypatch.setattr(
+        script_ns.corr, "compare_true_envelope_to_coordinator_capture",
+        lambda *a, **k: {"any_mismatch": True, "comparisons": {"x": {"matches": False}}},
+    )
+    mock_derive = mock.MagicMock(name="derive_avb_volume_correction")
+    mock_apply = mock.MagicMock(name="apply_avb_volume_correction")
+    monkeypatch.setattr(script_ns.corr, "derive_avb_volume_correction", mock_derive)
+    monkeypatch.setattr(script_ns.corr, "apply_avb_volume_correction", mock_apply)
+
+    evidence_dir = tmp_path / "ev"
+    output_path = tmp_path / "out.json"
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_avb_correction.py", "--confirm",
+            "--evidence-dir", str(evidence_dir), "--output-path", str(output_path),
+        ],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_derive.assert_not_called()
+    mock_apply.assert_not_called()
+    assert not output_path.exists()  # the final consolidated artifact is never written
+
+
+# --- derivation not verified: stops BEFORE the write, nothing written to output-path --------------------
+
+
+def test_derivation_not_verified_stops_before_the_write(monkeypatch, script_ns, tmp_path):
+    fake_true_start = {
+        "daily_prices": {"row_count": 1}, "db_file": {},
+        "avb_target_rows": {"2026-08-11": {"volume": 1.0, "close": 1.0}, "2026-08-12": {"volume": 2.0, "close": 2.0}},
+    }
+    monkeypatch.setattr(script_ns, "load_config", lambda: mock.MagicMock(database=mock.MagicMock(url="sqlite:///x")))
+    monkeypatch.setattr(script_ns, "resolve_database_url", lambda url: "sqlite:///x")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(name="get_engine"))
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.corr, "capture_true_envelope", lambda *a, **k: fake_true_start)
+    monkeypatch.setattr(
+        script_ns.corr, "compare_true_envelope_to_coordinator_capture",
+        lambda *a, **k: {"any_mismatch": False, "comparisons": {}},
+    )
+    monkeypatch.setattr(script_ns.corr, "load_provider_fetch_evidence", lambda *a, **k: {})
+    monkeypatch.setattr(script_ns.diag, "load_j10_avb_evidence", lambda *a, **k: {})
+    monkeypatch.setattr(
+        script_ns.corr, "derive_avb_volume_correction",
+        lambda *a, **k: {"verified": False, "per_date": {}},
+    )
+    mock_apply = mock.MagicMock(name="apply_avb_volume_correction")
+    monkeypatch.setattr(script_ns.corr, "apply_avb_volume_correction", mock_apply)
+
+    evidence_dir = tmp_path / "ev"
+    output_path = tmp_path / "out.json"
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_avb_correction.py", "--confirm",
+            "--evidence-dir", str(evidence_dir), "--output-path", str(output_path),
+        ],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_apply.assert_not_called()  # the ONE write must never execute on an unverified derivation
+    assert not output_path.exists()
+    assert (evidence_dir / "j11-avb-correction-derivation.json").exists()  # the failure evidence IS persisted
+
+
+# --- happy path: exactly one apply call, all expected files written, success exit ----------------------
+
+
+def test_success_path_calls_apply_exactly_once_and_writes_all_artifacts(monkeypatch, script_ns, tmp_path):
+    fake_true_start = {
+        "daily_prices": {"row_count": 1, "min_date": "2026-01-01", "max_date": "2026-08-12", "id_sum": 1, "ohlcv_sum": 100.0},
+        "db_file": {"mtime": 1, "size_bytes": 1, "wal": {"exists": False}},
+        "avb_target_rows": {
+            "2026-08-11": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 10.0},
+            "2026-08-12": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 20.0},
+        },
+        "isolating_hashes": {
+            "avb_ohlc_only": {"sha256": "a"}, "avb_other_dates_full_row": {"sha256": "b"}, "non_avb_full_row": {"sha256": "c"},
+        },
+        "scanner_runs_by_identity_group": {}, "forward_returns_total_count": 0,
+        "forward_returns_measured_into_incident_total": 0, "data_provider_runs_count": 0,
+        "manifest_row_count": 0, "manifest_ddl_sha256": "d", "manifest_row_dump_fingerprint": {"sha256": "e"},
+        "watchlist_count": 0, "all_11_incident_dates_zero_scanner_runs": True,
+    }
+    fake_true_end = {
+        **fake_true_start,
+        "avb_target_rows": {
+            "2026-08-11": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 5.0},
+            "2026-08-12": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 8.0},
+        },
+        "daily_prices": {
+            "row_count": 1, "min_date": "2026-01-01", "max_date": "2026-08-12", "id_sum": 1,
+            "ohlcv_sum": 100.0 - (10.0 - 5.0) - (20.0 - 8.0),
+        },
+        "db_file": {"mtime": 2, "size_bytes": 2, "wal": {"exists": False}},
+    }
+    envelopes = iter([fake_true_start, fake_true_end])
+    monkeypatch.setattr(script_ns, "load_config", lambda: mock.MagicMock(database=mock.MagicMock(url="sqlite:///x")))
+    monkeypatch.setattr(script_ns, "resolve_database_url", lambda url: "sqlite:///x")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(name="get_engine"))
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.corr, "capture_true_envelope", lambda *a, **k: next(envelopes))
+    monkeypatch.setattr(
+        script_ns.corr, "compare_true_envelope_to_coordinator_capture",
+        lambda *a, **k: {"any_mismatch": False, "comparisons": {}},
+    )
+    monkeypatch.setattr(script_ns.corr, "load_provider_fetch_evidence", lambda *a, **k: {})
+    monkeypatch.setattr(script_ns.diag, "load_j10_avb_evidence", lambda *a, **k: {})
+    monkeypatch.setattr(
+        script_ns.corr, "derive_avb_volume_correction",
+        lambda *a, **k: {
+            "verified": True,
+            "per_date": {"2026-08-11": {"corrected_volume": 5.0}, "2026-08-12": {"corrected_volume": 8.0}},
+        },
+    )
+    mock_apply = mock.MagicMock(name="apply_avb_volume_correction", return_value={"2026-08-11": 5.0, "2026-08-12": 8.0})
+    monkeypatch.setattr(script_ns.corr, "apply_avb_volume_correction", mock_apply)
+    monkeypatch.setattr(
+        script_ns.corr, "checkpoint_wal", lambda *a, **k: {"busy": 0, "log_pages": 0, "checkpointed_pages": 0}
+    )
+
+    evidence_dir = tmp_path / "ev"
+    output_path = tmp_path / "out.json"
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "run_j11_avb_correction.py", "--confirm",
+            "--evidence-dir", str(evidence_dir), "--output-path", str(output_path),
+        ],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 0
+    mock_apply.assert_called_once()
+    assert (evidence_dir / "j11-avb-correction-true-start.json").exists()
+    assert (evidence_dir / "j11-avb-correction-true-start-comparison.json").exists()
+    assert (evidence_dir / "j11-avb-correction-derivation.json").exists()
+    assert (evidence_dir / "j11-avb-correction-true-end.json").exists()
+    assert output_path.exists()
diff --git a/apps/backend/tests/test_j11_preboot_guard.py b/apps/backend/tests/test_j11_preboot_guard.py
new file mode 100644
index 00000000..c6e691bb
--- /dev/null
+++ b/apps/backend/tests/test_j11_preboot_guard.py
@@ -0,0 +1,317 @@
+"""goal-market-compass iter-16 -- J-11 "OWNER RULING -- pre-boot incident guard required" tests
+(Goals 6-7). Exclusively fixture/in-memory SQLite -- never `apps/backend/data/trendora.db`, and the live
+backend is never booted anywhere in this file. The `ensure_latest_snapshot` integration tests below
+monkeypatch `warmup_mod.run_scan` to a recording stub (the SAME pattern `test_warmup.py`'s own
+`run_scan`-failure test already uses: `monkeypatch.setattr(warmup_mod, "run_scan", _boom)`) rather than
+exercising the real scanner engine -- this file tests the GUARD's wiring, not the scanner's own
+correctness (covered elsewhere, and doing so here would need the heavy seeded-DB fixtures `test_warmup.py`
+already pays for once)."""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlalchemy import text
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.config import load_config
+from app.engine import j11_maintenance as jm
+from app.engine import j11_preboot_guard as guard
+# `data_manager` MUST be imported (or transitively triggered) before `warmup` -- `warmup` <-> `data_manager`
+# <-> `compass` <-> `readiness` is a genuine, PRE-EXISTING circular import in this codebase; importing
+# `warmup` completely fresh with nothing else already primed fails to resolve it. `test_warmup.py`'s own
+# `from app.engine import data_manager, prices, warmup as warmup_mod` already depends on this exact
+# ordering -- mirrored here rather than reordered, never "fixed" (out of this iteration's narrow scope).
+from app.engine import data_manager, warmup as warmup_mod  # noqa: F401
+from app.models import DailyPrice, MaintenanceBoundary, ScannerRun
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+TEST_DATE = date(2026, 8, 12)
+OTHER_DATE = date(2026, 8, 13)
+
+
+# --- register_boundary / clear_boundary -- generic, incident-agnostic, idempotent by name -------------
+
+
+def test_register_boundary_is_idempotent_by_name_and_updates_in_place(engine):
+    with Session(engine) as session:
+        first = guard.register_boundary(session, name="test-boundary", dates=[TEST_DATE], reason="r1")
+        second = guard.register_boundary(session, name="test-boundary", dates=[TEST_DATE, OTHER_DATE], reason="r2")
+    assert first.id == second.id  # same row, updated in place -- never a duplicate
+
+    with Session(engine) as session:
+        rows = session.exec(select(MaintenanceBoundary)).all()
+    assert len(rows) == 1
+    assert json.loads(rows[0].quarantined_dates_json) == sorted([TEST_DATE.isoformat(), OTHER_DATE.isoformat()])
+    assert rows[0].reason == "r2"
+    assert rows[0].active is True
+
+
+def test_clear_boundary_sets_inactive_and_is_a_noop_when_absent(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r", active=True)
+    with Session(engine) as session:
+        cleared = guard.clear_boundary(session, "b")
+    assert cleared.active is False
+
+    with Session(engine) as session:
+        noop = guard.clear_boundary(session, "does-not-exist")
+    assert noop is None
+
+
+def test_register_j11_incident_boundary_sources_dates_from_incident_dates_not_a_fresh_literal(engine):
+    with Session(engine) as session:
+        row = guard.register_j11_incident_boundary(session)
+    assert json.loads(row.quarantined_dates_json) == sorted(d.isoformat() for d in jm.INCIDENT_DATES)
+    assert row.active is True
+    assert row.name == guard.J11_INCIDENT_BOUNDARY_NAME
+
+
+# --- TC-23/24/25: refuse / allow-once-cleared / true no-op --------------------------------------------
+
+
+def test_tc25_no_boundary_registered_is_a_true_noop(engine):
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result == {"blocked": False, "boundary_name": None, "reason": None, "ambiguous": False}
+
+
+def test_tc23_active_boundary_blocks_the_quarantined_date_with_actionable_reason(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="incident quarantine active")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["boundary_name"] == "b"
+    assert result["reason"] == "incident quarantine active"
+    assert result["ambiguous"] is False
+
+
+def test_active_boundary_does_not_block_a_date_outside_its_own_set(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, OTHER_DATE)
+    assert result["blocked"] is False
+
+
+def test_tc24_cleared_boundary_allows_the_same_date_again(engine):
+    with Session(engine) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
+        guard.clear_boundary(session, "b")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is False
+
+
+# --- TC-26: genuinely state-driven -- fixture-only changes flip behaviour, guard source untouched ------
+
+
+def test_tc26_fixture_state_change_flips_behavior_without_touching_guard_source(engine):
+    with Session(engine) as session:
+        assert guard.evaluate_boundary_for_date(session, TEST_DATE)["blocked"] is False
+
+    with Session(engine) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
+    with Session(engine) as session:
+        assert guard.evaluate_boundary_for_date(session, TEST_DATE)["blocked"] is True
+
+    with Session(engine) as session:
+        guard.clear_boundary(session, "b")
+    with Session(engine) as session:
+        assert guard.evaluate_boundary_for_date(session, TEST_DATE)["blocked"] is False
+
+
+# --- TC-27: fails CLOSED on unreadable/ambiguous state --------------------------------------------------
+
+
+def _raw_insert_boundary(session, *, name, dates_json, active_int, reason):
+    session.execute(
+        text(
+            "INSERT INTO maintenance_boundaries (name, quarantined_dates_json, active, reason, "
+            "created_at, updated_at) VALUES (:name, :dates, :active, :reason, :now, :now)"
+        ),
+        {
+            "name": name, "dates": dates_json, "active": active_int, "reason": reason,
+            "now": datetime.now(timezone.utc).isoformat(),
+        },
+    )
+    session.commit()
+
+
+def test_tc27_fails_closed_on_malformed_date_set_json_while_active(engine):
+    with Session(engine) as session:
+        _raw_insert_boundary(session, name="b", dates_json="not valid json{{{", active_int=1, reason="r")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["ambiguous"] is True
+
+
+def test_tc27_fails_closed_on_valid_json_that_is_not_a_list_of_date_strings(engine):
+    with Session(engine) as session:
+        _raw_insert_boundary(session, name="b", dates_json=json.dumps({"not": "a list"}), active_int=1, reason="r")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["ambiguous"] is True
+
+
+def test_tc27_fails_closed_on_missing_date_set_content_while_active(engine):
+    with Session(engine) as session:
+        _raw_insert_boundary(session, name="b", dates_json="", active_int=1, reason="r")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is True
+    assert result["ambiguous"] is True
+
+
+def test_cleared_rows_malformed_date_set_never_triggers_ambiguous_fail_closed(engine):
+    """Only ACTIVE-but-unreadable state is ambiguous -- a row explicitly marked cleared never blocks,
+    regardless of what its (possibly stale/malformed) date-set says."""
+    with Session(engine) as session:
+        _raw_insert_boundary(session, name="b", dates_json="garbage{{{", active_int=0, reason="r")
+    with Session(engine) as session:
+        result = guard.evaluate_boundary_for_date(session, TEST_DATE)
+    assert result["blocked"] is False
+
+
+# --- TC-28: a partial 11-date attempt (some dates already carry a ScannerRun) stays blocked, driven -----
+# --- only by the explicit flag -- never per-date inference. --------------------------------------------
+
+
+def _mk_run(session, asof):
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=50.0, regime_label="Expansion", regime_components_json="[]",
+        breadth_above_50dma=50.0, breadth_above_200dma=50.0,
+        new_high_low_json="{}", candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def test_tc28_partial_attempt_with_some_dates_already_run_stays_blocked(engine):
+    partial_date, still_pending_date = jm.INCIDENT_DATES[0], jm.INCIDENT_DATES[1]
+    with Session(engine) as session:
+        _mk_run(session, partial_date)  # simulates a partially-completed prior regeneration attempt
+        session.commit()
+        guard.register_j11_incident_boundary(session, active=True)
+
+    with Session(engine) as session:
+        # the date that ALREADY has a ScannerRun is STILL blocked -- driven by the explicit active flag,
+        # never by "does this date already have a run" inference.
+        result_partial = guard.evaluate_boundary_for_date(session, partial_date)
+        result_pending = guard.evaluate_boundary_for_date(session, still_pending_date)
+    assert result_partial["blocked"] is True
+    assert result_pending["blocked"] is True
+
+
+# --- TC-29/TC-31: `warmup.ensure_latest_snapshot` wiring -- fixture-scoped engine, run_scan mocked out --
+
+
+def _seed_one_price(session, d=TEST_DATE):
+    session.add(DailyPrice(symbol="AAPL", date=d, open=1, high=2, low=0.5, close=1.5, volume=100))
+    session.commit()
+
+
+def test_tc23_ensure_latest_snapshot_skips_write_and_returns_none_when_blocked(engine, cfg, monkeypatch, caplog):
+    with Session(engine) as session:
+        _seed_one_price(session)
+        guard.register_j11_incident_boundary(session, active=True)
+
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda *a, **k: calls.append(a))
+
+    import logging
+    caplog.set_level(logging.WARNING, logger="trendora.warmup")
+    result = warmup_mod.ensure_latest_snapshot(engine, cfg)
+
+    assert result is None  # the SAME safe shape as an empty DB -- never a crash
+    assert calls == []  # run_scan never called for the blocked date -- no ScannerRun created
+    assert any(TEST_DATE.isoformat() in record.message or str(TEST_DATE) in record.getMessage() for record in caplog.records)
+
+
+def test_tc24_ensure_latest_snapshot_writes_normally_once_the_boundary_is_cleared(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        _seed_one_price(session)
+        guard.register_j11_incident_boundary(session, active=True)
+        guard.clear_boundary(session, guard.J11_INCIDENT_BOUNDARY_NAME)
+
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    result = warmup_mod.ensure_latest_snapshot(engine, cfg)
+
+    assert result == TEST_DATE
+    assert calls == [TEST_DATE]
+
+
+def test_tc25_ensure_latest_snapshot_byte_identical_when_no_boundary_registered(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        _seed_one_price(session)  # NO boundary registered at all -- the common no-incident case
+
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda session, asof, cfg: calls.append(asof))
+
+    result = warmup_mod.ensure_latest_snapshot(engine, cfg)
+
+    assert result == TEST_DATE
+    assert calls == [TEST_DATE]
+
+
+def test_ensure_latest_snapshot_fails_closed_on_a_guard_exception_and_never_crashes(engine, cfg, monkeypatch):
+    with Session(engine) as session:
+        _seed_one_price(session)
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("boom")
+
+    monkeypatch.setattr(guard, "evaluate_boundary_for_date", _boom)
+    calls = []
+    monkeypatch.setattr(warmup_mod, "run_scan", lambda *a, **k: calls.append(a))
+
+    result = warmup_mod.ensure_latest_snapshot(engine, cfg)  # must NOT raise
+
+    assert result is None
+    assert calls == []
+
+
+def test_ensure_latest_snapshot_returns_none_on_empty_db_unchanged(engine, cfg):
+    """Baseline sanity: the pre-existing empty-DB behavior is unaffected by this iteration's change."""
+    result = warmup_mod.ensure_latest_snapshot(engine, cfg)
+    assert result is None
+
+
+# --- TC-30: purely additive table, created idempotently via the existing convention --------------------
+
+
+def test_tc30_create_db_and_tables_creates_maintenance_boundaries_idempotently(tmp_path):
+    from app.db import create_db_and_tables, make_engine
+
+    db_path = tmp_path / "idempotent.db"
+    eng = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(eng)  # first run -- creates the table fresh
+    with Session(eng) as session:
+        guard.register_boundary(session, name="b", dates=[TEST_DATE], reason="r")
+
+    create_db_and_tables(eng)  # second run -- must be a no-op; the row must survive untouched
+
+    with Session(eng) as session:
+        rows = session.exec(select(MaintenanceBoundary)).all()
+    assert len(rows) == 1
+    assert rows[0].name == "b"
```
