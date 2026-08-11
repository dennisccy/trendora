# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 2.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (41 diff lines)

```diff
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 3488cb96..de61529e 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -68,6 +68,7 @@ from app.engine.evidence import LEDGER_PATH_ENV
 from app.engine.forward_testing import compute_forward_aggregates
 from app.engine.ledger import append_entry
 from app.engine.scoring import score_stocks
+from app.api.data import data_overview
 from app.models import (
     AvailabilityCache,
     CoverageSnapshot,
@@ -4188,6 +4189,98 @@ def test_coverage_from_storage_serves_stale_prior_snapshot_when_default_view_sta
     assert _strip_coverage_status(served) == real_payload
 
 
+def test_data_overview_serves_freshest_ingested_coverage_after_unrelated_dataset_version_bump(tmp_path):
+    """goal-ops-hardening iter-61 (J-05 TC-1/TC-2) — the exact evaluator-reported scenario: a REAL ingest
+    finalize hook (`_refresh_ingest_aggregates`, not a hand-called shortcut) persists a fresh
+    `coverage_snapshot` row for the newly-created latest date; an UNRELATED request-path event (a
+    historical `/backtest` create-once view — `scanner.resolve_run`, the real code path, not a raw
+    `session.add(ScannerRun(...))`) then creates a new `ScannerRun` for an EARLIER date, bumping
+    `_membership_dataset_version` (the iter-27 stale-row fallback's trigger condition). The API-layer
+    function `app.api.data.data_overview` (not just `coverage_from_storage` in isolation) must still
+    serve the JUST-INGESTED date's exact `snapshot_count`/`gap_count`/`snapshot_dates` — the freshest
+    persisted row for that `asof_key` — never a value from BEFORE the ingest."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'coverage_freshness.db'}")
+    create_db_and_tables(engine)
+    d_pre = date(2024, 1, 2)  # already-snapshotted BEFORE the ingest under test (the pre-ingest total)
+    d_new = date(2024, 3, 4)  # the ingest's own newly-created latest date
+    d_unrelated = date(2023, 6, 1)  # the unrelated request-path event's target -- earlier than BOTH above
+    with Session(engine) as session:
+        for d in (d_pre, d_new, d_unrelated):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        run = ScannerRun(
+            asof_date=d_pre, created_at=datetime(2024, 1, 2), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.commit()
+        session.refresh(run)
+        session.add(ScannerResult(
+            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.commit()
+
+    cfg = load_config()
+    # (1) the REAL ingest: `d_new`'s own ScannerRun/ScannerResult are created first (mirroring `_do_backfill`'s
+    # own date-loop, which persists the snapshot BEFORE the finalize hook runs -- `prog.new_snapshot_dates`
+    # documents exactly that "already committed" precondition), THEN the finalize hook persists coverage.
+    with Session(engine) as session:
+        run_new = ScannerRun(
+            asof_date=d_new, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+            regime_score=55.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run_new)
+        session.commit()
+        session.refresh(run_new)
+        session.add(ScannerResult(
+            run_id=run_new.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.commit()
+        prog = JobProgress(job_id="freshness-probe", kind="backfill", start=d_new, end=d_new)
+        prog.new_snapshot_dates = [d_new]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "coverage" in refreshed
+
+    with Session(engine) as session:
+        fresh_row = session.exec(
+            select(CoverageSnapshot).where(CoverageSnapshot.asof_key == d_new.isoformat())
+        ).one()
+        v_ingest = fresh_row.dataset_version
+        assert fresh_row.payload_json  # sanity: a real payload was persisted
+    ingest_snapshot_count = json.loads(fresh_row.payload_json)["snapshot_count"]
+    ingest_gap_count = json.loads(fresh_row.payload_json)["gap_count"]
+    assert ingest_snapshot_count == 2  # d_pre + d_new -- the CORRECT post-ingest total
+
+    # (2) the unrelated request-path event: a historical /backtest create-once view for `d_unrelated`,
+    # through the REAL `scanner.resolve_run` path (never touches CoverageSnapshot) -- bumps
+    # `_membership_dataset_version` while leaving "latest" (`d_new`) and the fresh row's OWN payload
+    # completely untouched.
+    with Session(engine) as session:
+        scanner.resolve_run(session, d_unrelated.isoformat(), cfg)
+    with Session(engine) as session:
+        v_after = data_manager._membership_dataset_version(session, cfg)
+        assert v_after != v_ingest  # the stamp genuinely advanced from the unrelated event alone
+        resolved = data_manager._resolve_coverage_asof(session, None, cfg)
+        assert resolved == d_new  # "latest" is unaffected -- the unrelated run is for an EARLIER date
+
+        # (3) the actual API-layer function -- not just coverage_from_storage in isolation -- must still
+        # serve the freshest ingested row's exact counts, never the pre-ingest pair.
+        payload = data_overview(session=session)
+    cov = payload["coverage"]
+    assert cov["snapshot_count"] == ingest_snapshot_count == 2  # never the pre-ingest 1
+    assert cov["gap_count"] == ingest_gap_count
+    assert d_new.isoformat() in cov["snapshot_dates"]
+    assert cov["coverage_status"] in ("current", "stale")  # either is honest; the VALUES must be fresh
+    if cov["coverage_status"] == "stale":
+        assert cov["stale_dataset_version"] == v_ingest
+
+
 # ==================================================================================================
 # iter-21 (J-33): import-source catalog availability (env-detected) — descriptive metadata, NO key
 # ==================================================================================================
diff --git a/apps/frontend/components/readiness-provider.tsx b/apps/frontend/components/readiness-provider.tsx
index 8928f5a3..821d440b 100644
--- a/apps/frontend/components/readiness-provider.tsx
+++ b/apps/frontend/components/readiness-provider.tsx
@@ -41,6 +41,12 @@ export interface ReadinessContextValue {
   backgroundCompute: BackgroundComputeStatus | null;
   /** True until the first poll has resolved (so callers can show a neutral "checking" state). */
   loading: boolean;
+  /** goal-ops-hardening iter-61 (J-05) — the config-derived idle cadence (seconds) this SAME poll backs
+   *  off to once `ready` (`GET /api/health`'s `poll_idle_interval_seconds`), exposed so a page can run its
+   *  OWN ambient/ idle-cadence refresh (e.g. `/data`'s coverage reload) without a second poll literal or a
+   *  second fetch. Null before the first poll resolves / on a failed poll (mirrors every sibling field's
+   *  honesty convention) — callers must gate their own interval on a non-null value. */
+  pollIdleIntervalSeconds: number | null;
 }
 
 const ReadinessContext = createContext<ReadinessContextValue | null>(null);
@@ -56,6 +62,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   const [preflight, setPreflight] = useState<PreflightStatus | null>(null);
   const [backgroundCompute, setBackgroundCompute] = useState<BackgroundComputeStatus | null>(null);
   const [loading, setLoading] = useState(true);
+  const [pollIdleIntervalSeconds, setPollIdleIntervalSeconds] = useState<number | null>(null);
   // the config-derived cadences (seconds) from the latest payload; refs so the polling loop reads the
   // freshest value without re-subscribing.
   const activeMs = useRef(BOOTSTRAP_ACTIVE_MS);
@@ -74,6 +81,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setWarmup(data.warmup);
         setPreflight(data.preflight);
         setBackgroundCompute(data.background_compute);
+        setPollIdleIntervalSeconds(data.poll_idle_interval_seconds);
         // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
         activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
         idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
@@ -85,6 +93,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setWarmup(null);
         setPreflight(null); // honest — the banner renders its own NO-GO for a null preflight, never blank
         setBackgroundCompute(null); // honest — readers render their own empty/idle state, never fabricated
+        setPollIdleIntervalSeconds(null); // honest — a caller's own idle-refresh loop must not schedule on this
         nextDelay = activeMs.current; // keep retrying at the active cadence until the backend answers
       } finally {
         if (active) {
@@ -102,8 +111,8 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   }, []);
 
   const value = useMemo<ReadinessContextValue>(
-    () => ({ state, warmup, preflight, backgroundCompute, loading }),
-    [state, warmup, preflight, backgroundCompute, loading],
+    () => ({ state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds }),
+    [state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds],
   );
 
   return <ReadinessContext.Provider value={value}>{children}</ReadinessContext.Provider>;
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 55 ++++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |  2 +
 runs/goal-session-ops-hardening/telemetry.jsonl    |  9 ++++
 runs/goal-session-ops-hardening/trace/.next-step   |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  2 +
 5 files changed, 69 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
