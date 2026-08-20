# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/tests/test_evidence_drawdown_memory_pressure.py b/apps/backend/tests/test_evidence_drawdown_memory_pressure.py
index ef985e1e..6c40f1c0 100644
--- a/apps/backend/tests/test_evidence_drawdown_memory_pressure.py
+++ b/apps/backend/tests/test_evidence_drawdown_memory_pressure.py
@@ -27,7 +27,7 @@ absolute KB values are calibrated to THIS host/Python build, following that same
 convention of host-measured absolute caps."""
 from __future__ import annotations
 
-import shutil
+import os
 import subprocess
 import sys
 import time
@@ -35,10 +35,23 @@ from pathlib import Path
 
 import pytest
 
+from _seed_subset import build_research_subset_db, real_db_available
+
 REPO_ROOT = Path(__file__).resolve().parents[3]
 REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
 BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
 
+# goal-market-compass iter-5 (goal.md Constraint (a) / host resource-fit, owner 2026-08-20): this
+# module's real-subprocess `ulimit -v` induction is a genuinely heavy drill (multiple fresh DB builds +
+# subprocess spawns) — opt-in only, so a plain `pytest` collection of this file never pays that cost by
+# accident. TC-1: WITHOUT the env var, every test below reports SKIPPED at setup, before any DB is
+# touched, in seconds.
+pytestmark = pytest.mark.skipif(
+    os.environ.get("TRENDORA_MEMORY_PRESSURE") != "1",
+    reason="opt-in only — set TRENDORA_MEMORY_PRESSURE=1 to run this real-subprocess memory-pressure "
+    "induction drill (multiple DB builds + ulimit -v subprocess spawns; run on an idle host)",
+)
+
 _CLAIM = {"kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": 20, "direction": "positive"}
 
 # Measured this iteration (see module docstring): the window that reproducibly discriminates reference
@@ -53,21 +66,24 @@ BOUNDED_TIMEOUT_S = 120.0
 
 
 def _skip_if_no_real_db() -> None:
-    if not REAL_DB.exists():
+    if not real_db_available():
         pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to reproduce against")
 
 
 def _fresh_seed_copy(tmp_path: Path, name: str) -> Path:
-    """A FRESH, never-cache-polluted disposable copy of the live committed seed DB, ONE PER CALL.
+    """A FRESH, never-cache-polluted disposable SUBSET DB, ONE PER CALL — goal-market-compass iter-5
+    (Constraint (a)): built via `_seed_subset.build_research_subset_db` (an `ATTACH`-and-`INSERT
+    ... SELECT` read-only extraction of just the horizon=20 population this module's `_CLAIM` needs),
+    never a `shutil.copy*` of the live 7.8 GB `apps/backend/data/trendora.db` — see that helper's
+    docstring for exactly which rows/tables are carried and which are honestly dropped.
     `compute_drawdown_expectations_cached` (the real `/api/evidence` entry point this drill exercises)
-    WRITES an `EventStudyCache` row on a MISS — so a copy REUSED across sub-calls would silently turn a
+    WRITES an `EventStudyCache` row on a MISS — so a DB REUSED across sub-calls would silently turn a
     later "reference"/"starved" probe into a trivial cache HIT (never re-invoking the compute this drill
     exists to pressure-test) the moment an EARLIER probe on the SAME copy succeeded. Each probe therefore
-    gets its OWN fresh copy (a local-disk copy of the seed DB measures ~1-2s — cheap relative to the ~20s+
-    compute each probe pays). Never touches the actual committed `apps/backend/data/trendora.db` file."""
+    gets its OWN fresh subset build."""
     _skip_if_no_real_db()
     dest = tmp_path / name
-    shutil.copyfile(REAL_DB, dest)
+    build_research_subset_db(dest, horizons=[_CLAIM["horizon"]])
     return dest
 
 
diff --git a/apps/backend/tests/test_ingest_finalize_memory_pressure.py b/apps/backend/tests/test_ingest_finalize_memory_pressure.py
index ffe376ad..c68c2da9 100644
--- a/apps/backend/tests/test_ingest_finalize_memory_pressure.py
+++ b/apps/backend/tests/test_ingest_finalize_memory_pressure.py
@@ -34,6 +34,7 @@ except -- the first thing to fail, never exercising the iter-8 forward_aggregate
 targets)."""
 from __future__ import annotations
 
+import os
 import subprocess
 import sys
 import time
@@ -48,6 +49,19 @@ from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.models import ForwardReturn, ScannerResult, ScannerRun
 
+# goal-market-compass iter-5 (goal.md Constraint (a) / host resource-fit, owner 2026-08-20): opt-in
+# only, mirroring the sibling drawdown/samples memory-pressure files — see their `pytestmark` for the
+# full rationale. This file never touched the live `apps/backend/data/trendora.db` (its fixture is
+# already a from-scratch synthetic DB, below) but the drill itself is still a real `ulimit -v`
+# subprocess induction against 600K synthesized tickers x every configured horizon — heavy enough that
+# a plain `pytest` collection of this file must not pay it by accident. TC-1: WITHOUT the env var, both
+# tests below report SKIPPED at setup, in seconds.
+pytestmark = pytest.mark.skipif(
+    os.environ.get("TRENDORA_MEMORY_PRESSURE") != "1",
+    reason="opt-in only — set TRENDORA_MEMORY_PRESSURE=1 to run this real-subprocess memory-pressure "
+    "induction drill (a synthesized 600K-row fixture + ulimit -v subprocess spawn; run on an idle host)",
+)
+
 BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)  # apps/backend -- for the child subprocess's sys.path
 N_TICKERS = 600_000
 RECORD_JSON_BYTES = 4_000  # mirrors test_forward_testing_concurrency.py's per-row cost convention
diff --git a/apps/backend/tests/test_samples_memory_pressure.py b/apps/backend/tests/test_samples_memory_pressure.py
index ea8d1a47..2fb9a918 100644
--- a/apps/backend/tests/test_samples_memory_pressure.py
+++ b/apps/backend/tests/test_samples_memory_pressure.py
@@ -30,17 +30,28 @@ likelihood at a given pressure level, not immunity to arbitrarily severe pressur
 drill's own disclosed residual)."""
 from __future__ import annotations
 
-import shutil
+import os
 import subprocess
 import sys
 from pathlib import Path
 
 import pytest
 
+from _seed_subset import build_research_subset_db, real_db_available
+
 REPO_ROOT = Path(__file__).resolve().parents[3]
 REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
 BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
 
+# goal-market-compass iter-5 (goal.md Constraint (a) / host resource-fit, owner 2026-08-20): opt-in
+# only — see test_evidence_drawdown_memory_pressure.py's sibling `pytestmark` for the full rationale.
+# TC-1: WITHOUT the env var, every test below reports SKIPPED at setup, before any DB is touched.
+pytestmark = pytest.mark.skipif(
+    os.environ.get("TRENDORA_MEMORY_PRESSURE") != "1",
+    reason="opt-in only — set TRENDORA_MEMORY_PRESSURE=1 to run this real-subprocess memory-pressure "
+    "induction drill (multiple DB builds + ulimit -v subprocess spawns; run on an idle host)",
+)
+
 # The live ledger's OWN leadership_score/decile-10/horizon-20 claim (`runs/goal-session-mcp-loop/state/
 # certified-claims.jsonl`) — the real shape `compute_drawdown_expectations_cached` resolves for every
 # `GET /api/evidence` request, and the exact call chain the iter-46 audit's live `MemoryError` traced.
@@ -79,27 +90,39 @@ BOUNDED_TIMEOUT_S = 150.0
 
 
 def _skip_if_no_real_db() -> None:
-    if not REAL_DB.exists():
+    if not real_db_available():
         pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to reproduce against")
 
 
+# goal-market-compass iter-5 (Constraint (a)): every claim in this file (decile/total/regime) is
+# horizon=20 today (see `_CLAIM`/`_TOTAL_CLAIM`/`_REGIME_CLAIM` below) — resolved as a set so a future
+# claim added at a different horizon is automatically carried into the subset instead of silently
+# missing its population. Referenced (not defined) by `_fresh_seed_copy`, so its own definition further
+# down the module is fine — Python resolves module globals at CALL time.
+def _all_claim_horizons() -> list[int]:
+    return sorted({_CLAIM["horizon"], _TOTAL_CLAIM["horizon"], _REGIME_CLAIM["horizon"]})
+
+
 def _fresh_seed_copy(tmp_path: Path, name: str) -> Path:
-    """A FRESH, never-cache-polluted disposable copy of the live committed seed DB, ONE PER CALL — mirrors
-    `test_evidence_drawdown_memory_pressure.py`'s own rationale: `compute_drawdown_expectations_cached`
-    WRITES an `EventStudyCache` row on a MISS, so a copy reused across probes would silently turn a later
-    probe into a trivial cache HIT. Never touches the actual committed `apps/backend/data/trendora.db`."""
+    """A FRESH, never-cache-polluted disposable SUBSET DB, ONE PER CALL — goal-market-compass iter-5
+    (Constraint (a)): built via `_seed_subset.build_research_subset_db` (an `ATTACH`-and-`INSERT
+    ... SELECT` read-only extraction — see that helper's docstring), never a `shutil.copy*` of the live
+    7.8 GB `apps/backend/data/trendora.db`. Mirrors `test_evidence_drawdown_memory_pressure.py`'s own
+    rationale: `compute_drawdown_expectations_cached` WRITES an `EventStudyCache` row on a MISS, so a DB
+    reused across probes would silently turn a later probe into a trivial cache HIT."""
     _skip_if_no_real_db()
     dest = tmp_path / name
-    shutil.copyfile(REAL_DB, dest)
+    build_research_subset_db(dest, horizons=_all_claim_horizons())
     return dest
 
 
 def _delete_copy(path: Path) -> None:
-    """ops-hardening iter-48: the total/regime drills below run TWICE as many DB-copy probes as the
-    existing decile drill (two variants x the same battery) — at ~8.4 GB per copy that is a real disk
-    concern (not merely a slow test), so each copy is deleted immediately after its probe subprocess
-    returns rather than left for `tmp_path`'s end-of-session cleanup. Best-effort: a failed cleanup must
-    never fail the test that already got its result."""
+    """ops-hardening iter-48 (pre-iter-5: sized against the old raw-file-copy fixture, ~8.4 GB per
+    copy): the total/regime drills below run TWICE as many DB-build probes as the existing decile drill
+    (two variants x the same battery), so each build is deleted immediately after its probe subprocess
+    returns rather than left for `tmp_path`'s end-of-session cleanup — still worth doing even at the
+    iter-5 subset DB's much smaller size (many probes x this file's own battery still adds up).
+    Best-effort: a failed cleanup must never fail the test that already got its result."""
     for suffix in ("", "-wal", "-shm"):
         p = Path(str(path) + suffix)
         if p.exists():
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index e5cb255e..a1afa0a8 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -50,7 +50,6 @@ import json
 import os
 import random
 import re
-import shutil
 import signal
 import subprocess
 import threading
@@ -61,6 +60,8 @@ from pathlib import Path
 import httpx
 import pytest
 
+from _seed_subset import build_windowed_subset_db, real_db_available
+
 # apps/backend/tests/test_start_backend_script.py -> tests -> backend -> apps -> <repo root>
 REPO_ROOT = Path(__file__).resolve().parents[3]
 SCRIPT = REPO_ROOT / "scripts" / "start-backend.sh"
@@ -415,14 +416,13 @@ def spawned_backend_fast_graceful_timeout(tmp_path):
         )
     if not SCRIPT.exists():
         pytest.skip(f"{SCRIPT} not found")
-    if not REAL_DB.exists():
-        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to copy for a real capacity measurement")
+    if not real_db_available():
+        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to subset for a real capacity measurement")
 
+    # goal-market-compass iter-5 (Constraint (a)): a real, functioning windowed SUBSET of the live DB
+    # (see `_seed_subset.build_windowed_subset_db`), never a `shutil.copy2` of the full 7.8 GB file.
     scratch_db = tmp_path / "throwaway_fast_shutdown.db"
-    for suffix in ("", "-wal", "-shm"):
-        src = Path(str(REAL_DB) + suffix)
-        if src.exists():
-            shutil.copy2(src, Path(str(scratch_db) + suffix))
+    build_windowed_subset_db(scratch_db)
 
     scratch_config = tmp_path / "throwaway-fast-shutdown-config.yaml"
     real_cfg_text = REAL_CONFIG.read_text()
@@ -552,14 +552,13 @@ def spawned_backend_throwaway_db(tmp_path):
         )
     if not SCRIPT.exists():
         pytest.skip(f"{SCRIPT} not found")
-    if not REAL_DB.exists():
-        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to copy for a real capacity measurement")
+    if not real_db_available():
+        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to subset for a real capacity measurement")
 
+    # goal-market-compass iter-5 (Constraint (a)): a real, functioning windowed SUBSET of the live DB
+    # (see `_seed_subset.build_windowed_subset_db`), never a `shutil.copy2` of the full 7.8 GB file.
     scratch_db = tmp_path / "throwaway.db"
-    for suffix in ("", "-wal", "-shm"):
-        src = Path(str(REAL_DB) + suffix)
-        if src.exists():
-            shutil.copy2(src, Path(str(scratch_db) + suffix))
+    build_windowed_subset_db(scratch_db)
 
     scratch_config = tmp_path / "throwaway-config.yaml"
     real_cfg_text = REAL_CONFIG.read_text()
@@ -1582,14 +1581,13 @@ def spawned_backend_throwaway_db_fault_injected(tmp_path):
         )
     if not SCRIPT.exists():
         pytest.skip(f"{SCRIPT} not found")
-    if not REAL_DB.exists():
-        pytest.skip(f"real dev DB not found at {REAL_DB} -- nothing to copy for a real ingest drill")
+    if not real_db_available():
+        pytest.skip(f"real dev DB not found at {REAL_DB} -- nothing to subset for a real ingest drill")
 
+    # goal-market-compass iter-5 (Constraint (a)): a real, functioning windowed SUBSET of the live DB
+    # (see `_seed_subset.build_windowed_subset_db`), never a `shutil.copy2` of the full 7.8 GB file.
     scratch_db = tmp_path / "ingest-fault-throwaway.db"
-    for suffix in ("", "-wal", "-shm"):
-        src = Path(str(REAL_DB) + suffix)
-        if src.exists():
-            shutil.copy2(src, Path(str(scratch_db) + suffix))
+    build_windowed_subset_db(scratch_db)
 
     scratch_config = tmp_path / "ingest-fault-throwaway-config.yaml"
     real_cfg_text = REAL_CONFIG.read_text()
diff --git a/apps/frontend/next.config.mjs b/apps/frontend/next.config.mjs
index 19c8dd9c..1227ee94 100644
--- a/apps/frontend/next.config.mjs
+++ b/apps/frontend/next.config.mjs
@@ -155,5 +155,13 @@ export default function nextConfig(phase) {
     // Type-checking stays ON (the frontend "test" is `npm run build` = compile + typecheck).
     eslint: { ignoreDuringBuilds: true },
     distDir,
+    // goal.md Constraint (b) / AG-10 (host resource-fit, owner 2026-08-20): production `next build`
+    // otherwise fans out to `os.cpus().length - 1` static-worker processes (16-way on this host) —
+    // real concurrent CPU/memory pressure the 2026-08-20 desktop-freeze incident named as a
+    // contributing factor when a full-depth iteration runs alongside other host activity. Bounding
+    // `experimental.cpus` (the exact knob `getNumberOfWorkers` in Next's build pipeline reads — see
+    // `node_modules/next/dist/build/index.js`) caps the static-worker fan-out at 4 without touching
+    // `next start`/`next dev` (this same config, unaffected — Next only consults `cpus` at build time).
+    experimental: { cpus: 4 },
   };
 }
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index bbe63841..ec6c8b78 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -951,6 +951,14 @@ class _FakeLocator:
     def first(self):
         return self
 
+    def filter(self, *, visible: "bool | None" = None, **_ignored):
+        # goal-market-compass iter-5: real `_check_expect` now chains `.filter(visible=True)` before
+        # `.first` (see its docstring). This fake models exactly one candidate element per name (never
+        # the "N matches, some hidden" shape the real fix targets), so filtering is a no-op — the
+        # existing spy-recorded `.first.wait_for(...)` call sequence, and every self-test asserting on
+        # it, stays byte-identical.
+        return self
+
     def wait_for(self, state: str = "visible", timeout: float = 0):
         # ops-hardening iter-78: record the timeout each caller actually threaded through, so a
         # test can assert a step's own `timeout_ms` reaches Playwright's `.wait_for()` unclamped
@@ -1021,6 +1029,13 @@ class _FakeSettlingLocator:
     def first(self):
         return self
 
+    def filter(self, *, visible: "bool | None" = None, **_ignored):
+        # goal-market-compass iter-5: see `_FakeLocator.filter` — same no-op rationale, this fake also
+        # models exactly one candidate per text (its OWN visibility already fully encoded in `.wait_for`
+        # via `page.phase`), so `.filter(visible=True)` changes nothing about the poll sequence
+        # `_t_settle_for_capture_before_after_frames_differ_when_state_changes` depends on.
+        return self
+
     def wait_for(self, state: str = "visible", timeout: float = 0):
         page = self._page
         if self._text == page.before_text:
@@ -1470,7 +1485,25 @@ def _find(page, target: dict, timeout_ms: int):
 def _check_expect(page, exp: dict, timeout_ms: int) -> bool:
     try:
         if "text" in exp:
-            page.get_by_text(exp["text"]).first.wait_for(state="visible", timeout=timeout_ms)
+            # goal-market-compass iter-5 (J-01 replay-golden repair): `get_by_text(...).first` picks
+            # whichever DOM node containing the text comes FIRST in document order, visible or not —
+            # a raw contiguous-substring scan of the WHOLE page, not "the cell's own rendered text".
+            # J-01 step 3 (`expect.text: "Consumer Discretionary"`) produced the identical false FAIL
+            # twice (iter-3, iter-4): the /stocks sector-filter <select> renders an <option> with that
+            # exact text BEFORE the leaderboard table in DOM order, and a closed native <select>'s own
+            # <option> elements are never "visible" per Playwright's actionability rules — `.first`
+            # resolved to that hidden decoy and `.wait_for(state="visible")` timed out even though the
+            # GRMN row's own (two-line-wrapped, but textually intact) sector <td> was genuinely on
+            # screen with the identical text (confirmed by a live DOM probe: 2 matches, index 0 =
+            # hidden <option>, index 1 = the visible <td>). `.filter(visible=True)` scopes the match to
+            # elements actually rendered on screen — re-evaluated on every auto-retry, exactly like the
+            # rest of the locator chain — so `.first` now resolves to the real, visible cell instead of
+            # a same-text decoy elsewhere on the page. Playwright's own text engine already normalizes
+            # whitespace/newlines when comparing (collapses runs to one space, trims), so the cell's
+            # rendered text content is matched normalized without any extra code here.
+            page.get_by_text(exp["text"]).filter(visible=True).first.wait_for(
+                state="visible", timeout=timeout_ms
+            )
             return True
         if "target" in exp:
             _find(page, exp["target"], timeout_ms)
```

## Excluded-path stat (dependency/lockfile visibility)

 .../state/assumptions.md                           | 35 ++++++++++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl   |  7 +++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  1 +
 4 files changed, 44 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
