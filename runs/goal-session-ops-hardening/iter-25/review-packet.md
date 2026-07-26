# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 2.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (79 diff lines)

```diff
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index 137cc6a8..daff798a 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -110,16 +110,36 @@ def test_health_carries_additive_background_compute_field(loaded_engine, tmp_pat
     assert isinstance(bg["recent_outcomes"], list)
 
 
+def _background_compute_identity(status: dict) -> dict:
+    """Reduce a `background_compute` payload to the parts two back-to-back LIVE reads of the SAME
+    process-lifetime registry can be compared on without flaking (audit T1 fix): `elapsed_ms` on each
+    active entry is computed fresh at READ TIME from its own `started_at`, so it can legitimately grow
+    between two reads of a genuinely in-flight window -- it is excluded here. `recent_outcomes` is
+    reduced to its ordering/length (the identifying `(asof_key, dataset_version)` sequence), since a
+    window completing between the two reads would append a new entry -- a real state change, not a
+    flake, but also not what this test is pinning."""
+    return {
+        "active": [{k: v for k, v in entry.items() if k != "elapsed_ms"} for entry in status["active"]],
+        "recent_outcomes_order": [(o["asof_key"], o["dataset_version"]) for o in status["recent_outcomes"]],
+        "recent_outcomes_count": len(status["recent_outcomes"]),
+    }
+
+
 def test_health_background_compute_is_single_source(loaded_engine, tmp_path, monkeypatch):
-    """The served `background_compute` field equals a DIRECT `compute_readiness` call's own composed
-    value for the same session/config -- re-displayed verbatim, never re-derived by the endpoint."""
+    """The served `background_compute` field matches a DIRECT `compute_readiness` call's own composed
+    value for the same session/config -- re-displayed verbatim, never re-derived by the endpoint.
+    Compared on identity/shape (active-window keys/count, recent_outcomes ordering/length) excluding the
+    read-time-volatile `elapsed_ms` field, rather than raw equality of two live reads (closes audit T1 --
+    a false-alarm risk whenever an earlier test in the same whole-file run left a real background
+    compute in flight)."""
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
     cfg = load_config()
     with TestClient(main.app) as client:
         served = client.get("/api/health").json()["background_compute"]
     with Session(loaded_engine) as session:
         direct = readiness.compute_readiness(session, config=cfg)["background_compute"]
-    assert served == direct
+    assert len(served["active"]) == len(direct["active"])
+    assert _background_compute_identity(served) == _background_compute_identity(direct)
 
 
 def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index 3475706d..ac64458a 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -289,9 +289,25 @@ def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
 # registry's OWN bookkeeping (started_at/horizons_done/ring cap/failure path) is covered in
 # test_forward_testing_concurrency.py, the producer module's own test file.
 # ==================================================================================================
+def _background_compute_identity(status: dict) -> dict:
+    """Reduce a `background_compute` payload to the parts two back-to-back LIVE reads of the SAME
+    process-lifetime registry can be compared on without flaking (audit T1 fix): `elapsed_ms` on each
+    active entry is computed fresh at READ TIME from its own `started_at`, so it can legitimately grow
+    between two reads of a genuinely in-flight window -- it is excluded here. `recent_outcomes` is
+    reduced to its ordering/length (the identifying `(asof_key, dataset_version)` sequence)."""
+    return {
+        "active": [{k: v for k, v in entry.items() if k != "elapsed_ms"} for entry in status["active"]],
+        "recent_outcomes_order": [(o["asof_key"], o["dataset_version"]) for o in status["recent_outcomes"]],
+        "recent_outcomes_count": len(status["recent_outcomes"]),
+    }
+
+
 def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine):
     """A process that has never dispatched a historical background compute reports the honest empty
-    shape -- never omitted, never fabricated non-empty."""
+    shape -- never omitted, never fabricated non-empty. Compares two back-to-back live reads of the SAME
+    registry on identity/shape rather than raw equality, excluding the read-time-volatile `elapsed_ms`
+    field (closes audit T1 -- a false-alarm risk on any whole-file run where a background thread left by
+    an earlier test may still be in flight between the two reads below)."""
     import app.engine.forward_testing as forward_testing_module
 
     cfg = load_config()
@@ -301,9 +317,11 @@ def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine
         # compute_readiness composes it VERBATIM regardless of what it currently holds.
         direct = forward_testing_module.get_background_compute_status()
         result = compute_readiness(session, config=cfg)
-    assert result["background_compute"] == direct
-    assert isinstance(result["background_compute"]["active"], list)
-    assert isinstance(result["background_compute"]["recent_outcomes"], list)
+    composed = result["background_compute"]
+    assert isinstance(composed["active"], list)
+    assert isinstance(composed["recent_outcomes"], list)
+    assert len(composed["active"]) == len(direct["active"])
+    assert _background_compute_identity(composed) == _background_compute_identity(direct)
 
 
 def test_compute_readiness_composes_background_compute_active_entry(loaded_engine, monkeypatch):
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-demo.json       | 48 ++++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |  1 +
 runs/goal-session-ops-hardening/telemetry.jsonl    |  7 ++++
 runs/goal-session-ops-hardening/trace/.next-step   |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  1 +
 5 files changed, 58 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
