# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 5fa1bb33..391f1e49 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -817,7 +817,35 @@ class NextSessionManifest(SQLModel, table=True):
     # iter-3: version starts at 1 (the finalize freeze or the first historical on-demand GET); a
     # confirm-gated regenerate mints version N+1 for an existing as_of. Pre-iter-3 rows backfill 1.
     version: int = Field(default=1)
-    source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)
+    # goal-market-compass iter-10 (J-11 Stage B1): the LIVE `FOREIGN KEY(source_run_id) REFERENCES
+    # scanner_runs (id)` DDL is DROPPED from the model declaration here (model-declaration change only --
+    # no live-DB migration; the already-created live table keeps its existing DDL untouched, per
+    # `.claude/project-template.md`'s additive-ALTER-only schema-evolution rule). This was a LATENT
+    # contradiction, not a new one: enforcement was already OFF on the live DB (`PRAGMA foreign_keys` reads
+    # `0` -- `app.db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`), and
+    # `PRAGMA foreign_key_check(next_session_manifests)` already reports 12 violations on the live DB
+    # today, all on incident-dated manifests -- so the FK declaration was never actually enforced; it was
+    # only ever aspirational. Declaring it here as `foreign_key=...` documents a contract the design does
+    # NOT want: AG-12 (manifest immutability) requires a manifest to survive its source `ScannerRun` being
+    # deleted and canonically rebuilt (J-11 Stages C/D, a LATER iteration), and a rebuilt run legitimately
+    # gets a fresh row (or, since `scanner_runs.id` is a plain SQLite rowid alias with no `AUTOINCREMENT`
+    # and no `sqlite_sequence` table, can even REUSE a freed numeric id).
+    #
+    # Intended end state (docs/goal.md J-11 step 11, verbatim): "`source_run_id` remains stored historical
+    # provenance; it is not required to dereference to a live `ScannerRun` forever; manifest survival must
+    # not depend on foreign-key enforcement being off; current-run reconciliation is by `as_of` + frozen
+    # source timing/provenance, never by FK rebinding; a rebuilt run may legitimately carry a different id;
+    # and even when it reuses the same numeric id it is still a rebuilt run whenever the frozen
+    # timestamp/provenance differs. Never mutate a manifest to 'repair' an orphaned foreign key."
+    #
+    # Reconciliation after a delete/rebuild is therefore by `as_of` + `source_run_created_at` (carried
+    # inside `generation_json`) + the frozen `engine_identity` -- NEVER by dereferencing `source_run_id`.
+    # `app.engine.compass.basis_disclosure` already implements exactly this (it resolves the CURRENT run
+    # by `as_of` and compares `source_run_created_at` against that run's `created_at` -- it never reads
+    # `source_run_id` at all) and needs NO change here. `source_run_id` stays `index=True` (still a useful
+    # lookup/audit column) and its VALUE is still written once and never mutated (AG-12) -- only the live
+    # `FOREIGN KEY` constraint declaration is removed.
+    source_run_id: int = Field(index=True)
     session_delta_json: str
     narrative_json: str
     selection_json: str
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     | 11 ++-
 .../goal-session-market-compass/.engine.lock/epoch |  2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |  2 +-
 runs/goal-session-market-compass/engine.pid        |  2 +-
 runs/goal-session-market-compass/session.json      |  8 +-
 .../state/assumptions.md                           | 92 ---------------------
 .../state/assumptions.md.archive.md                | 95 ++++++++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  | 22 +----
 .../state/lessons.md.archive.md                    | 31 +++++++
 runs/goal-session-market-compass/summary.md        | 91 ++++++++++++++++-----
 runs/goal-session-market-compass/telemetry.jsonl   | 27 ++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  2 +
 .../state/preflight-verdict-history.jsonl          |  2 +
 14 files changed, 245 insertions(+), 144 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
