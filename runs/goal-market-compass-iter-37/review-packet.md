# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index b97754f5..c1325e6f 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -593,15 +593,17 @@ def _assert_disposition_predicate(comparison_cohort: list[dict], sel) -> None:
         disposition = row["selection_disposition"]
         cleared_floor = row["leadership_score"] >= sel.leadership_min_score
         if disposition == _DISPOSITION_BELOW_FLOOR:
-            assert not cleared_floor, (
-                f"{row['ticker']}: selection_disposition=below_selection_floor but leadership_score "
-                f"{row['leadership_score']} >= leadership_min_score {sel.leadership_min_score}"
-            )
+            if cleared_floor:
+                raise AssertionError(
+                    f"{row['ticker']}: selection_disposition=below_selection_floor but leadership_score "
+                    f"{row['leadership_score']} >= leadership_min_score {sel.leadership_min_score}"
+                )
         elif disposition == _DISPOSITION_EXCLUDED_BY_CAP:
-            assert cleared_floor, (
-                f"{row['ticker']}: selection_disposition=excluded_by_cap but leadership_score "
-                f"{row['leadership_score']} < leadership_min_score {sel.leadership_min_score}"
-            )
+            if not cleared_floor:
+                raise AssertionError(
+                    f"{row['ticker']}: selection_disposition=excluded_by_cap but leadership_score "
+                    f"{row['leadership_score']} < leadership_min_score {sel.leadership_min_score}"
+                )
 
 
 def _scan_selection_language(candidates: list[dict], why_not: list[dict], cfg: Config) -> None:
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index 8bac3ac8..53806be8 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -5,6 +5,8 @@ covered by an explicitly-named test below. File-scoped synthetic fixtures (fresh
 from __future__ import annotations
 
 import json
+import subprocess
+import sys
 import threading
 from concurrent.futures import ThreadPoolExecutor, as_completed
 from datetime import date, datetime, timedelta, timezone
@@ -930,17 +932,60 @@ def test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers(eng
     score. Mirrors the frontier export's measured defect (37/539 rows, HPE 92.71 highest, BACKGROUND)."""
     with Session(engine) as session:
         run = _mk_run(session, date(2024, 12, 8))
-        _mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 58.9, "C")  # clears floor, fails BOTH qualifiers
+        _mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 65.0, "C")  # clears floor, fails BOTH qualifiers
         _mk_result(session, run.id, "LOW", 30.0, "E", 90.0, "A", 10.0, "A")  # below floor, clears BOTH qualifiers
         session.commit()
         session.refresh(run)
         result = compass.evaluate_selection(session, run, cfg)
     candidate_tickers = {c["ticker"] for c in result["candidates"]}
+    candidate_by_ticker = {c["ticker"]: c for c in result["candidates"]}
     cohort_by_ticker = {row["ticker"]: row for row in result["comparison_cohort"]}
     assert "HPE" in candidate_tickers or cohort_by_ticker.get("HPE", {}).get("selection_disposition") == "excluded_by_cap"
     assert "HPE" not in cohort_by_ticker or cohort_by_ticker["HPE"]["selection_disposition"] != "below_selection_floor"
     assert cohort_by_ticker["LOW"]["selection_disposition"] == "below_selection_floor"
     assert "LOW" not in candidate_tickers
+    # TC-1 (iter-37): the corrected fixture must genuinely fail BOTH advisory qualifiers -- not merely
+    # carry a comment claiming so (the confound this fixture previously had, iter-35/36 fixture bug).
+    hpe_checks = {check["condition"]: check for check in candidate_by_ticker["HPE"]["what_would_change"]}
+    assert hpe_checks["entry_min_score"]["met"] is False
+    assert hpe_checks["risk_max_score"]["met"] is False
+
+
+# --- TC-2 (iter-37): _assert_disposition_predicate survives -O -------------------------------------
+
+
+def test_assert_disposition_predicate_raises_under_dash_o(cfg):
+    """goal-market-compass iter-37: `_assert_disposition_predicate`'s two guard statements were converted
+    from bare `assert` to explicit `if not cond: raise AssertionError(msg)` so Python's `-O`/`-OO` flags
+    (which strip bare `assert` statements entirely) can no longer silently defeat the guard. Since pytest
+    itself never runs under `-O`, the only way to prove this from inside a pytest process is a subprocess:
+    spawn `python -O -c "..."`, feed it a comparison-cohort row that deliberately violates the predicate
+    (labeled `below_selection_floor` while its leadership_score clears the floor), and assert the child
+    process still raises AssertionError and exits non-zero."""
+    backend_dir = REPO_ROOT / "apps" / "backend"
+    script = (
+        "from app.config import load_config\n"
+        "from app.engine.compass import _assert_disposition_predicate\n"
+        "cfg = load_config()\n"
+        "sel = cfg.compass.selection\n"
+        "bad_row = {\n"
+        "    'ticker': 'BAD',\n"
+        "    'leadership_score': sel.leadership_min_score + 1.0,\n"
+        "    'selection_disposition': 'below_selection_floor',\n"
+        "}\n"
+        "_assert_disposition_predicate([bad_row], sel)\n"
+        "print('NO_RAISE')\n"
+    )
+    proc = subprocess.run(
+        [sys.executable, "-O", "-c", script],
+        cwd=str(backend_dir),
+        capture_output=True,
+        text=True,
+        timeout=BOUNDED_TIMEOUT_S,
+    )
+    assert proc.returncode != 0, f"guard did not raise under -O; stdout={proc.stdout!r} stderr={proc.stderr!r}"
+    assert "AssertionError" in proc.stderr, f"expected AssertionError in stderr, got: {proc.stderr!r}"
+    assert "NO_RAISE" not in proc.stdout
 
 
 # --- TC-25 (schema conformance) ---------------------------------------------------------------------
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/telemetry.jsonl   | 7 +++++++
 runs/goal-session-market-compass/trace/.next-step  | 2 +-
 runs/goal-session-market-compass/trace/trace.jsonl | 2 ++
 3 files changed, 10 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
