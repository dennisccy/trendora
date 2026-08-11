# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (35 diff lines)

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index 1b29309a..340c0151 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -38,7 +38,7 @@ from sqlmodel import Session
 from app.config import get_config
 from app.db import get_engine, get_session
 from app.engine.readiness import compute_preflight, compute_readiness, record_verdict_transition
-from app.models import DailyPrice
+from app.models import DailyPrice, ScannerRun
 
 router = APIRouter(tags=["health"])
 
@@ -81,10 +81,15 @@ def health(session: Session = Depends(get_session)) -> dict:
     try:
         latest = session.scalar(select(func.max(DailyPrice.date)))
         symbol_count = _distinct_symbol_count(session)
+        # goal-ops-hardening iter-62: the SAME query shape `app.engine.data_manager` already uses to
+        # resolve the latest scanner run date (e.g. its `latest_run_date` reads) -- no second derivation.
+        # Null on an empty DB (no scanner run yet), matching this module's own docstring contract.
+        last_run_date = session.scalar(select(func.max(ScannerRun.asof_date)))
         db_ok = True
     except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
         latest = None
         symbol_count = 0
+        last_run_date = None
         db_ok = False
 
     # The single honest readiness state + warm-up progress (computed once by the readiness producer).
@@ -123,7 +128,7 @@ def health(session: Session = Depends(get_session)) -> dict:
         "status": "ok" if db_ok else "degraded",
         "db_ok": db_ok,
         "provider": provider,
-        "last_run_date": None,
+        "last_run_date": last_run_date.isoformat() if last_run_date else None,
         "seed_latest_date": latest.isoformat() if latest else None,
         "symbol_count": symbol_count,
         # iter-28 (J-40): the single canonical readiness value (state + warm-up progress).
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index 719d2dac..ede652bb 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -8,7 +8,7 @@ from sqlalchemy import event, func, select as sa_select
 from sqlmodel import Session, select
 
 import main
-from app.api.health import _distinct_symbol_count
+from app.api.health import _distinct_symbol_count, health
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine import readiness
@@ -18,6 +18,12 @@ from app.models import DailyPrice, ScannerRun
 
 
 def test_health_returns_ok_shape(loaded_engine):
+    # TC-1: `last_run_date` reflects the real latest scanner run -- read directly via the same query
+    # shape the endpoint uses (`select(func.max(ScannerRun.asof_date))`), against the SAME loaded_engine,
+    # which genuinely carries ScannerRun rows (iter-9/iter-28 warm-up fixture history).
+    with Session(loaded_engine) as session:
+        expected_last_run_date = session.scalar(sa_select(func.max(ScannerRun.asof_date)))
+    assert expected_last_run_date is not None  # the fixture is not vacuously empty here
     # loaded_engine registers the temp DB as the process engine (see conftest).
     with TestClient(main.app) as client:
         resp = client.get("/api/health")
@@ -26,11 +32,24 @@ def test_health_returns_ok_shape(loaded_engine):
     assert body["status"] == "ok"
     assert body["db_ok"] is True
     assert body["provider"] == "seed"
-    assert body["last_run_date"] is None
+    assert body["last_run_date"] == expected_last_run_date.isoformat()
     assert body["seed_latest_date"] is not None
     assert body["symbol_count"] > 100
 
 
+def test_health_last_run_date_is_null_on_empty_db(tmp_path):
+    """TC-2: a freshly created, unloaded engine (tables exist, zero ScannerRun rows) reports
+    `last_run_date: null` -- preserves the pre-existing empty-DB contract this module's own docstring
+    already promises. Calls the handler directly against an isolated session (mirrors
+    test_api_watchlist.py:173's test_watchlist_raises_503_when_no_price_data), leaving the shared
+    process engine untouched."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'health_empty.db'}")
+    create_db_and_tables(engine)  # tables exist, but no rows were ever loaded
+    with Session(engine) as session:
+        body = health(session)
+    assert body["last_run_date"] is None
+
+
 def test_health_carries_readiness_and_warmup(loaded_engine):
     """iter-28 (J-40): the single canonical readiness endpoint extends /api/health with the honest
     readiness state + warm-up progress. The TestClient runs the lifespan (fast latest-snapshot + the
diff --git a/apps/frontend/lib/data-overview-refresh.test.ts b/apps/frontend/lib/data-overview-refresh.test.ts
new file mode 100644
index 00000000..5f2218c4
--- /dev/null
+++ b/apps/frontend/lib/data-overview-refresh.test.ts
@@ -0,0 +1,37 @@
+/**
+ * Unit tests for the J-07 / auditor-F3 ambient-refresh failure helper (lib/data-overview-refresh.ts).
+ *
+ * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
+ *   node lib/data-overview-refresh.test.ts
+ * Pins the helper's three input cases (TC-6): `ok` preserved unchanged, `loading` -> `error`,
+ * `error` -> `error`.
+ */
+import assert from "node:assert";
+
+import { nextStateAfterFetchError, type FetchState } from "./data-overview-refresh.ts";
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+check("an 'ok' state is returned UNCHANGED (same reference) on a fetch failure", () => {
+  const ok: FetchState<{ n: number }> = { kind: "ok", data: { n: 42 } };
+  const result = nextStateAfterFetchError(ok);
+  assert.strictEqual(result, ok); // same object reference -- proves it is untouched, not just equal
+  assert.deepStrictEqual(result, { kind: "ok", data: { n: 42 } });
+});
+
+check("a 'loading' state (initial mount, no data yet) becomes 'error'", () => {
+  const loading: FetchState<{ n: number }> = { kind: "loading" };
+  assert.deepStrictEqual(nextStateAfterFetchError(loading), { kind: "error" });
+});
+
+check("an 'error' state stays 'error' (a repeated failure is not silently swallowed)", () => {
+  const error: FetchState<{ n: number }> = { kind: "error" };
+  assert.deepStrictEqual(nextStateAfterFetchError(error), { kind: "error" });
+});
+
+console.log(`\n${passed} passed`);
diff --git a/apps/frontend/lib/data-overview-refresh.ts b/apps/frontend/lib/data-overview-refresh.ts
new file mode 100644
index 00000000..dfe260c1
--- /dev/null
+++ b/apps/frontend/lib/data-overview-refresh.ts
@@ -0,0 +1,35 @@
+/**
+ * goal-ops-hardening iter-62 (J-07 / auditor F3 fix) — the single, pure authority for how `/data`'s
+ * ambient idle-cadence coverage/availability refresh (iter-60/61) should handle a fetch REJECTION. No
+ * React, no DOM types, so it is unit-testable under `node` (the existing frontend convention — see
+ * `lib/api-base.ts`, `lib/background-compute-panel-branch.ts`).
+ *
+ * WHY THIS EXISTS — before this fix, `app/data/page.tsx`'s `loadOverview`/`loadAvailability` `.catch`
+ * handlers unconditionally set `{kind:"error"}` on ANY fetch failure, INCLUDING the periodic 30-second
+ * ambient poll (iter-60/61). A single transient hiccup on that poll silently wiped already-rendered good
+ * coverage/availability numbers and replaced them with the "Backend unavailable" card, one poll cycle
+ * away from clearing again -- exactly the "silently discard good data" failure mode AG-8 exists to catch.
+ *
+ * The fix: once a page has SOMETHING real to show (`kind === "ok"`), a fetch failure never erases it --
+ * the stale-but-real data keeps rendering until a fetch actually succeeds again. The INITIAL-mount
+ * failure case (no data yet -- `kind === "loading"`) is unchanged: it still becomes the honest
+ * "Backend unavailable" card, exactly as today.
+ */
+
+export type FetchState<T> =
+  | { kind: "loading" }
+  | { kind: "ok"; data: T }
+  | { kind: "error" };
+
+/**
+ * Resolve the next state after a fetch REJECTS, given the state immediately before that fetch started.
+ *
+ * @param prev the state before this fetch's `.catch` fired.
+ * @returns `prev` UNCHANGED when it already carries real data (`kind === "ok"`) -- a periodic refresh's
+ *          transient failure must never erase already-displayed data; `{kind:"error"}` otherwise
+ *          (preserves today's initial-mount-failure "Backend unavailable" behavior byte-for-byte).
+ */
+export function nextStateAfterFetchError<T>(prev: FetchState<T>): FetchState<T> {
+  if (prev.kind === "ok") return prev;
+  return { kind: "error" };
+}
```
