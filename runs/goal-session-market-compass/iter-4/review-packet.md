# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/tests/test_db.py b/apps/backend/tests/test_db.py
index 562840c5..930fc674 100644
--- a/apps/backend/tests/test_db.py
+++ b/apps/backend/tests/test_db.py
@@ -368,10 +368,10 @@ def test_sqlite_pragmas_applied_on_connect(tmp_path):
     assert journal_mode.lower() == "wal"
     assert synchronous == 1  # SQLite's own PRAGMA synchronous vocabulary: 0=OFF,1=NORMAL,2=FULL,3=EXTRA
     assert busy_timeout == 30000
-    assert cache_size == -262144
+    assert cache_size == -65536  # iter-4/J-09: was -262144 (256 MB); halved to 64 MB, see reports/perf-budgets.md
     # mmap DISABLED (0): a non-zero mmap_size reserves that many bytes of VIRTUAL address space per pooled
     # connection; at 1 GB x the pool it exhausted the 6144 MB ulimit -v cap and crashed the cold /api/data
-    # load (iter-24 audit / browser-qa UT-16). The 256 MB page cache above keeps reads fast without it.
+    # load (iter-24 audit / browser-qa UT-16). The page cache above keeps reads fast without it.
     assert mmap_size == 0
     assert temp_store == 2  # SQLite's own PRAGMA temp_store vocabulary: 0=DEFAULT,1=FILE,2=MEMORY
 
diff --git a/config.yaml b/config.yaml
index e16db5cb..52cf1586 100644
--- a/config.yaml
+++ b/config.yaml
@@ -106,7 +106,8 @@ database:
     journal_mode: "WAL"
     synchronous: "NORMAL"
     busy_timeout_ms: 30000
-    cache_size: -262144          # negative = KiB -> 256 MB page cache
+    cache_size: -65536           # negative = KiB -> 64 MB page cache (iter-4/J-09: was -262144/256 MB;
+                                 # halved standing pool memory, see reports/perf-budgets.md)
     mmap_size_bytes: 0           # mmap DISABLED (iter-24 audit). A non-zero mmap_size reserves that many
                                  # bytes of VIRTUAL address space PER pooled connection; at 1 GB x the
                                  # pool (pool_size 10 + max_overflow 20) just ~6 connections exhausted the
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 123 +++++++++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl   |   7 ++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   1 +
 4 files changed, 132 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
