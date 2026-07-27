# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 565baedc..49b613bc 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -2283,7 +2283,7 @@ class RegistryCfg(BaseModel):
     enforce: bool = False
 
 
-_DEFAULT_DRIFT_REPORT_PATH = "runs/goal-session-mcp-loop/state/drift-report.json"
+_DEFAULT_DRIFT_REPORT_PATH = "runs/goal-session-ops-hardening/state/drift-report.json"
 
 
 class DriftCfg(BaseModel):
diff --git a/config.yaml b/config.yaml
index 2400f102..1951bde6 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1149,7 +1149,7 @@ data_quality:
   drift:
     enabled: true
     overlap_days: 20                                          # bounded per-symbol compare window (anti-goal #8 — never the whole history)
-    report_path: runs/goal-session-mcp-loop/state/drift-report.json
+    report_path: runs/goal-session-ops-hardening/state/drift-report.json
 
 # ----------------------------------------------------------------------------------------
 # Analyst-loop triad scan (app.engine.triad_scan / scan_product_triad). Tunables for the
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 .../iter-28/goal-slice.md                          | 123 +--------------------
 .../journey-scripts/J-05.json                      |   6 +-
 .../journey-scripts/J-06.json                      |   2 +-
 .../state/assumptions.md                           |  93 ++++++----------
 .../state/assumptions.md.archive.md                |  62 +++++++++++
 .../state/drift-report.json                        |   0
 .../state/evaluator-log.md                         |  72 ++++++++++++
 .../state/journey-history.json                     |  78 ++++++-------
 runs/goal-session-ops-hardening/state/lessons.md   |  48 +++-----
 .../state/lessons.md.archive.md                    |  42 +++++++
 runs/goal-session-ops-hardening/telemetry.jsonl    |  33 ++++++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   4 +
 16 files changed, 317 insertions(+), 254 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
