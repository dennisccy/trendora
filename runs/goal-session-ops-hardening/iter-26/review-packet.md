# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 1.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (31 diff lines)

```diff
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index daff798a..b26fdda5 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -142,6 +142,36 @@ def test_health_background_compute_is_single_source(loaded_engine, tmp_path, mon
     assert _background_compute_identity(served) == _background_compute_identity(direct)
 
 
+def test_health_background_compute_serves_failed_outcome_verbatim(loaded_engine, tmp_path, monkeypatch):
+    """goal-ops-hardening iter-26 (J-09 confirm-gap 2): a crafted `failed` outcome -- the branch every
+    captured panel state to date has never exercised -- is composed and served VERBATIM, field-for-field,
+    never dropped/re-derived/silently swallowed. Monkeypatches the ONE producer accessor
+    (`app.engine.forward_testing.get_background_compute_status`) rather than a byte-frozen module's
+    internals -- `compute_readiness`/`app/api/health.py` themselves are untouched by this iteration."""
+    import app.engine.forward_testing as forward_testing_module
+
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    crafted = {
+        "active": [],
+        "recent_outcomes": [{
+            "asof_key": "2026-01-04",
+            "dataset_version": "r1-f2",
+            "outcome": "failed",
+            "started_at": "2026-01-04T00:00:00+00:00",
+            "finished_at": "2026-01-04T00:00:05+00:00",
+            "duration_ms": 5000,
+            "reason": "forced test failure — simulated dispatch error",
+        }],
+    }
+    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", lambda: crafted)
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    served = body["background_compute"]["recent_outcomes"][0]
+    assert served == crafted["recent_outcomes"][0]
+    assert served["outcome"] == "failed"
+    assert served["reason"] == "forced test failure — simulated dispatch error"
+
+
 def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
     """A total `compute_readiness` failure degrades the WHOLE readiness payload to `unavailable` (the
     pre-existing convention) -- `background_compute` still serves the honest empty shape, never omitted
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 70 +++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |  7 +++
 runs/goal-session-ops-hardening/trace/.next-step  |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |  1 +
 4 files changed, 79 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
