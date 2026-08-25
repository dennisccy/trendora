# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/scripts/run_j11_stage_c_bounded_clear.py b/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
index 54827076..12fb5198 100644
--- a/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
+++ b/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
@@ -21,11 +21,16 @@ anywhere in this process, never a raw file copy of the 7.8+ GB database.
 Usage:
     apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_c_bounded_clear.py \\
         --confirm \\
-        [--evidence-dir runs/goal-market-compass-iter-13] \\
+        --evidence-dir runs/goal-market-compass-iter-13 \\
         [--certified-state-path runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json]
 
 Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
-non-zero.
+non-zero. `--evidence-dir` is REQUIRED and has no implicit default: it used to default to
+`runs/goal-market-compass-iter-13`, a real committed evidence directory, so any caller that forgot the
+flag silently overwrote committed Stage C forensic evidence instead of failing loudly (this actually
+happened -- iteration 14's own CLI test omitted the flag and truncated three iteration-13 evidence files;
+see docs/handoffs/goal-market-compass-iter-14-dev.md). A committed evidence directory is now only ever
+written when it is named explicitly on the command line.
 """
 from __future__ import annotations
 
@@ -49,7 +54,9 @@ from app.engine.j11_maintenance import INCIDENT_DATES, capture_pre_reset_invento
 from app.engine import j11_schema_migration as migration  # noqa: E402
 from app.models import DataProviderRun, NextSessionManifest, Watchlist  # noqa: E402
 
-DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-13"
+# The directory this script's evidence BELONGS in when it is run for real. Deliberately NOT an argparse
+# default: an omitted --evidence-dir must FAIL, never silently write over these committed files.
+CANONICAL_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-13"
 DEFAULT_CERTIFIED_STATE_PATH = (
     REPO_ROOT / "runs" / "goal-market-compass-iter-12" / "j11-stage-b1-cleanup-fingerprint-after.json"
 )
@@ -75,7 +82,14 @@ def _write_json(path: Path, payload) -> None:
 
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
-    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help=(
+            "required -- the directory every evidence JSON is written to. Has NO default on purpose: the "
+            f"real target ({CANONICAL_EVIDENCE_DIR}) is a committed evidence directory, and an implicit "
+            "default meant a forgotten flag overwrote committed forensic evidence instead of failing."
+        ),
+    )
     parser.add_argument("--certified-state-path", type=Path, default=DEFAULT_CERTIFIED_STATE_PATH)
     parser.add_argument(
         "--confirm", action="store_true",
@@ -92,6 +106,16 @@ def main() -> int:
         )
         return 2
 
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. This script writes forensic evidence "
+            f"JSON into that directory; its real target ({CANONICAL_EVIDENCE_DIR}) is a COMMITTED "
+            "evidence directory, so it must be named explicitly and can never be reached by default. "
+            "No database interaction, not even a read, has occurred, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
     evidence_dir: Path = args.evidence_dir
 
     cfg = load_config()
diff --git a/apps/backend/tests/test_j11_stage_c_preflight.py b/apps/backend/tests/test_j11_stage_c_preflight.py
index 9a38c9bc..5e3d509e 100644
--- a/apps/backend/tests/test_j11_stage_c_preflight.py
+++ b/apps/backend/tests/test_j11_stage_c_preflight.py
@@ -159,6 +159,89 @@ def test_tc2_comparison_gate_stops_on_material_mismatch_manifest_row_count(engin
     assert gate["checks"]["manifest_row_count_matches_certified"] is False
 
 
+def test_tc14_comparison_gate_stops_on_manifest_ddl_drift(engine, cfg):
+    """goal-market-compass iter-14, Goal 3b -- `compare_preflight_to_certified`'s
+    `manifest_ddl_unchanged_from_certified` check already exists (j11_stage_c.py) but was never exercised
+    by a fixture until now."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    certified["manifest_ddl"]["table_sql"] = (certified["manifest_ddl"]["table_sql"] or "") + " -- drifted clause"
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["material_mismatch"] is True
+    assert gate["checks"]["manifest_ddl_unchanged_from_certified"] is False
+
+
+def test_tc15_comparison_gate_stops_on_manifest_index_set_drift(engine, cfg):
+    """`manifest_indexes_unchanged` -- an index name/sql appearing in the certified baseline but not the
+    fresh capture (or vice versa) is a material mismatch."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    certified["manifest_ddl"]["index_names"] = list(certified["manifest_ddl"]["index_names"]) + ["ix_drifted"]
+    certified["manifest_ddl"]["index_sqls"] = list(certified["manifest_ddl"]["index_sqls"]) + [
+        "CREATE INDEX ix_drifted ON next_session_manifests (id)"
+    ]
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["manifest_indexes_unchanged"] is False
+
+
+def test_tc16_comparison_gate_stops_on_manifest_value_drift(engine, cfg):
+    """`manifest_values_unchanged` -- one manifest row's stored value differing from the certified dump is
+    a material mismatch (never an aggregate-only "row count matches" check, iter-9's lesson)."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    # simulate ONE stored manifest row whose value drifted -- the certified baseline recorded a row this
+    # fresh capture's dump does not carry the same value for.
+    certified["manifest_dump"] = [{"id": 1, "source_run_id": 7, "content_hash": "certified-value"}]
+    preflight_copy = copy.deepcopy(preflight)
+    preflight_copy["manifest_dump"] = [{"id": 1, "source_run_id": 7, "content_hash": "drifted-value"}]
+    gate = jsc.compare_preflight_to_certified(preflight_copy, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["manifest_values_unchanged"] is False
+    assert gate["manifest_dump_diff"]["mismatches"]
+
+
+def test_tc17_comparison_gate_stops_on_source_run_id_provenance_drift(engine, cfg):
+    """`source_run_id_values_unchanged` -- a manifest row's `source_run_id` differing from the certified
+    value is a material mismatch even when every other column matches (provenance drift specifically)."""
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    certified["manifest_dump"] = [{"id": 1, "source_run_id": 7, "content_hash": "same-value"}]
+    preflight_copy = copy.deepcopy(preflight)
+    preflight_copy["manifest_dump"] = [{"id": 1, "source_run_id": 999, "content_hash": "same-value"}]
+    gate = jsc.compare_preflight_to_certified(preflight_copy, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["source_run_id_values_unchanged"] is False
+    # the value drifted too (source_run_id is a manifest_dump column) -- both checks correctly fire
+    # together; this test isolates the PROVENANCE-specific check's own independent failure.
+
+
+def test_tc18_comparison_gate_stops_on_daily_prices_provider_runs_and_watchlist_drift(engine, cfg):
+    """`daily_prices_fingerprint_unchanged`, `data_provider_runs_count_unchanged`, and
+    `watchlist_count_unchanged` -- each asserted as an independent, separately-failing check (never one
+    combined canonical-inputs flag)."""
+    preflight = _fresh_preflight(engine, cfg)
+
+    certified_prices_drift = copy.deepcopy(preflight)
+    certified_prices_drift["pre_reset_inventory"]["daily_prices"]["fingerprint"] = "a-different-fingerprint"
+    gate = jsc.compare_preflight_to_certified(preflight, certified_prices_drift)
+    assert gate["checks"]["daily_prices_fingerprint_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+    certified_provider_drift = copy.deepcopy(preflight)
+    certified_provider_drift["pre_reset_inventory"]["data_provider_runs_count"] += 1
+    gate = jsc.compare_preflight_to_certified(preflight, certified_provider_drift)
+    assert gate["checks"]["data_provider_runs_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+    certified_watchlist_drift = copy.deepcopy(preflight)
+    certified_watchlist_drift["pre_reset_inventory"]["watchlist_count"] += 1
+    gate = jsc.compare_preflight_to_certified(preflight, certified_watchlist_drift)
+    assert gate["checks"]["watchlist_count_unchanged"] is False
+    assert gate["material_mismatch"] is True
+
+
 def test_tc2_comparison_gate_stops_on_per_date_scanner_run_drift(engine, cfg):
     preflight = _fresh_preflight(engine, cfg)
     certified = copy.deepcopy(preflight)
diff --git a/docs/goal.md b/docs/goal.md
index 2a4f56ce..85300d83 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1445,6 +1445,21 @@ manifest artifact (it must be self-describing and self-caveating).
        the relevant config/rule identity into the pre-reset inventory for **this attempt**. Invariant:
        > Every `ScannerRun` recreated by one J-11 regeneration attempt MUST carry the same
        > `engine_identity`, equal to the identity frozen in that attempt's pre-reset inventory.
+       **Clarification — which attempt, and which frozen identity (owner, 2026-08-24).** Read "that
+       attempt's" strictly: **Stage D begins a FRESH regeneration attempt from the successfully cleared
+       Stage C baseline; its frozen identity is computed immediately before Stage D and applies only to
+       the 11 rebuilt incident-date runs. Surviving historical runs retain their existing stamps.**
+       Iteration 10's frozen value (`6261ca17…`) is the historical identity of an EARLIER attempt; the
+       drift away from it is real and code-side (`compass.py` is a configured `provenance.engine_files`
+       member and changed after that freeze, while `config_subset_hash` is unchanged). That drift does
+       **not** invalidate the completed Stage C boundary. Therefore: do **not** force the new runs to
+       use `6261ca17…`; do **not** mutate, restamp or otherwise touch the 34 surviving runs that carry
+       it — they are not members of the new 11-date attempt; do **not** rewrite manifests; and do
+       **not** redo Stage C merely because the old attempt identity drifted. The new attempt's identity
+       must be recomputed with the canonical `app.engine.engine_identity.compute_engine_identity` at
+       freeze time and recorded honestly, never hardcoded. Stage E/F/G may cite that same attempt
+       identity for provenance, but Stage E's forward-return repair gets **no** permission to restamp
+       any `ScannerRun`.
        A run of "dates 1–5 under engine A → code or config changes → dates 6–11 under engine B" is
        **not** a successful clean regeneration and must not be recorded as one. If the code or config
        identity changes before an attempt finishes, the attempt must **not** be resumed piecemeal — it
```

## Excluded-path stat (dependency/lockfile visibility)

 .../state/assumptions.md                           | 234 ++++-----------------
 .../state/assumptions.md.archive.md                | 194 +++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  |  27 +--
 .../state/lessons.md.archive.md                    |  37 ++++
 runs/goal-session-market-compass/telemetry.jsonl   |  23 ++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   5 +
 7 files changed, 305 insertions(+), 217 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
