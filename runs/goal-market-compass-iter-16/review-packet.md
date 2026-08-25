# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     |  4 +-
 reports/goal-session-market-compass-retro.md       | 57 +++++++-------
 runs/goal-session-market-compass/session.json      |  6 +-
 .../state/assumptions.md                           | 92 ++++++----------------
 .../state/assumptions.md.archive.md                | 71 +++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  | 14 +---
 .../state/lessons.md.archive.md                    | 21 +++++
 .../state/retro-input.md                           |  4 +-
 runs/goal-session-market-compass/summary.md        |  6 +-
 runs/goal-session-market-compass/telemetry.jsonl   | 21 +++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  4 +
 12 files changed, 183 insertions(+), 119 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
