# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 010a9c30..b92d42c8 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1708,24 +1708,56 @@ def availability_from_storage(session: Session, config: Optional[Config] = None)
         ONLY case that payload is honest for (never conflated with the stale-serving case below).
       - A row exists and its stamp MATCHES the current one (idle/warm, byte-identical to iter-56):
         `stale: False`, `served_dataset_version` equal to the current (== the row's) stamp.
-      - A row exists but its stamp does NOT match the current one (a stamp mismatch — an ingest is
-        mid-flight and the finalize-tail warm has not yet re-run): serve THAT row's real
+      - A row exists but its stamp does NOT match the current one AND an ingest job is genuinely in
+        flight (`_ingest_job_in_flight` below): serve THAT row's real
         `cells`/`total_symbols`/`trading_day_count` (never empty) with `stale: True` and
         `served_dataset_version` set to the row's OWN (prior, not current) stamp, so the UI can render
         the real previous heatmap plus an honest "as of / updating" banner instead of a false "no data"
         claim. Still ZERO recompute — the payload is the SAME stored JSON blob deserialized, never a
-        live `compute_availability` call on this default request path (AG-8)."""
+        live `compute_availability` call on this default request path (AG-8).
+      - A row exists, its stamp does NOT match the current one, but NO ingest job is in flight (iter-58,
+        B2 fix): serve the SAME stored row with `stale: False`. A stamp bump with nothing running to
+        chase it (a request-path historical view creating a new `ScannerRun`, the boot warm-up's own
+        cadence snapshots, or a finalize warm that was skipped/crashed without landing) is honestly
+        "this is the current best-known reading", not "an update is coming" — the mirror-image honesty
+        fix of the stale-serving case above: iter-57 stopped this endpoint from lying "no data" while a
+        job runs; this stops it lying "updating" when nothing does.
+
+    ops-hardening iter-58 (audit B2): `stale` used to be pure stamp inequality, so ANY stamp bump left
+    the page reading "Data as of `<stamp>` — updating" indefinitely with nothing in flight. `stale` is
+    now (stamp mismatch) AND (a job is genuinely running), gated by `_ingest_job_in_flight` — see that
+    function's own docstring for why it reads `data_provider_runs.status` rather than the in-memory
+    `_JOBS` registry."""
     cfg = config or get_config()
     version = _membership_dataset_version(session, cfg)
     row = session.exec(select(AvailabilityCache)).first()
     if row is None:
         return _availability_not_yet_computed_payload()
     payload = json.loads(row.payload_json)
-    payload["stale"] = row.dataset_version != version
+    stamp_mismatch = row.dataset_version != version
+    payload["stale"] = stamp_mismatch and _ingest_job_in_flight(session)
     payload["served_dataset_version"] = row.dataset_version
     return payload
 
 
+def _ingest_job_in_flight(session: Session) -> bool:
+    """True iff at least one `data_provider_runs` row currently has `status == "running"` — the SAME
+    DB-status-only signal `sweep_orphaned_runs` (this module) already reads to detect an in-flight job.
+
+    ops-hardening iter-58 (`availability_from_storage`'s stale-gating fix, audit B2): DELIBERATELY reads
+    `data_provider_runs.status` rather than the in-memory `_JOBS` registry. The two signals diverge on
+    exactly one case, and it decides which one is safe: a job whose WORKER crashed mid-run leaves its
+    `data_provider_runs` row stuck at `status == "running"` (no terminal transition ever wrote) while the
+    in-memory `_JOBS` entry for it may already be gone (process-local; `_JOBS` is empty on a fresh boot —
+    see `sweep_orphaned_runs`'s own docstring — and a crash never guarantees the entry survives either).
+    An `_JOBS`-only signal would false-negative there: "no live job" while a genuinely stuck/unresolved
+    run sits in the DB, which would let the stale banner disappear on a row nobody is actually finishing.
+    The DB-status-only signal never false-negatives on that case — a stuck `running` row keeps reading as
+    "in flight" until an operator resolves it (the boot sweep, or a terminal transition), which is the
+    conservative, honest reading. One indexed-status read, zero writes."""
+    return session.exec(select(DataProviderRun.id).where(DataProviderRun.status == "running")).first() is not None
+
+
 def compute_capacity(session: Session, config: Optional[Config] = None) -> dict:
     """iter-24 fast-platform item K — the DB storage-footprint snapshot: on-disk file size + row counts
     for the three largest tables (`daily_prices` / `scanner_results` / `forward_returns`). PURE DB
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 93b56deb..050f1e7b 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -739,9 +739,12 @@ class AvailabilityCache(SQLModel, table=True):
         `CoverageSnapshot`/`MembershipTimelineCache` already key on — the snapshot set + bars manifest
         (`max(daily_prices.date)` + `count(*)`), exactly what `compute_availability` reads (ALL stored
         bars for `symbols_with_bars`/`total_symbols`, plus the `ScannerRun.asof_date` set for
-        `snapshot_exists`). A read computes the CURRENT stamp and looks up THIS exact key; a stale row
-        keyed to an older stamp is never hit (and is pruned on write), so the cache can NEVER serve a
-        stale heatmap.
+        `snapshot_exists`). A read computes the CURRENT stamp and looks up THIS exact key; a stamp
+        mismatch is the EXPECTED, tested, INTENDED case while an ingest job is genuinely in flight
+        (`app.engine.data_manager.availability_from_storage`, iter-57 J-06 / iter-58 B2 fix) — the
+        stamp-mismatched row IS served (with `stale=true`, `served_dataset_version` set to the row's own
+        prior stamp), not skipped. It is pruned on write (this table holds at most one row at a time),
+        so the cache never serves a heatmap OLDER than its own most recent successful warm.
 
     `payload_json` is the full serialized `total_symbols`/`trading_day_count`/`cells` payload. Unique
     on `dataset_version` so a write is an idempotent upsert."""
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 5224c5ab..073c0b7c 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -287,11 +287,12 @@ def test_get_data_availability_no_warm_serves_honest_not_yet_computed(tmp_path):
 
 
 def test_get_data_availability_stale_serves_prior_row_on_stamp_mismatch(tmp_path):
-    """ops-hardening iter-57 (TC-1, at the API layer) — a warm has already run (V1), then a new bar
-    lands WITHOUT the finalize-tail warm re-running (simulating a mid-flight ingest job's first
-    committed bar): the endpoint serves the PRIOR row's real, non-empty cells with `stale: True` and
-    `served_dataset_version` equal to the PRIOR (not current) stamp — never the not-yet-computed empty
-    sentinel while real data exists."""
+    """ops-hardening iter-57 (TC-2, at the API layer), gated (iter-58, audit B2 fix) on a job GENUINELY
+    being in flight: a warm has already run (V1), a `data_provider_runs` row has `status == "running"`,
+    then a new bar lands WITHOUT the finalize-tail warm re-running (simulating a mid-flight ingest job's
+    first committed bar): the endpoint serves the PRIOR row's real, non-empty cells with `stale: True`
+    and `served_dataset_version` equal to the PRIOR (not current) stamp — never the not-yet-computed
+    empty sentinel while real data exists."""
     engine = make_engine(f"sqlite:///{tmp_path / 'avail_stale.db'}")
     create_db_and_tables(engine)
     with Session(engine) as session:
@@ -301,6 +302,9 @@ def test_get_data_availability_stale_serves_prior_row_on_stamp_mismatch(tmp_path
     with Session(engine) as session:
         data_manager.availability_cached_with_status(session, get_config())  # warm it (V1)
         prior_version = data_manager._membership_dataset_version(session, get_config())
+        # a job genuinely in flight (the iter-58 precondition `stale` now requires)
+        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
+        session.commit()
     with Session(engine) as session:
         # a new bar lands — bumps the stamp — but no re-warm runs (mid-flight ingest, finalize pending)
         session.add(DailyPrice(symbol="AAA", date=date(2024, 1, 2), open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
@@ -313,6 +317,33 @@ def test_get_data_availability_stale_serves_prior_row_on_stamp_mismatch(tmp_path
     assert payload["total_symbols"] == 1  # the PRIOR row's count (SPY only) — not the post-bar count
 
 
+def test_get_data_availability_stamp_mismatch_without_job_running_is_not_stale(tmp_path):
+    """TC-1, at the API layer (iter-58, audit B2 fix) — the SAME stamp-bumping setup as the sibling test
+    above, but with NO `data_provider_runs` row at `status == "running"`: the endpoint now serves
+    `stale: False`. The prior row's real cells are still served (never the not-yet-computed empty
+    sentinel) — only the honesty flag changes, so `/data` never renders the false '— updating' banner
+    with nothing actually running."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'avail_not_stale.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (date(2024, 1, 2), date(2024, 1, 3)):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    with Session(engine) as session:
+        data_manager.availability_cached_with_status(session, get_config())  # warm it (V1)
+        prior_version = data_manager._membership_dataset_version(session, get_config())
+    with Session(engine) as session:
+        # a new bar lands — bumps the stamp — but no job is running at all
+        session.add(DailyPrice(symbol="AAA", date=date(2024, 1, 2), open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
+        session.commit()
+    with Session(engine) as session:
+        payload = data_availability(session=session)
+    assert payload["stale"] is False
+    assert payload["served_dataset_version"] == prior_version
+    assert payload["cells"] != []
+    assert payload["total_symbols"] == 1  # the PRIOR row's count (SPY only) — not the post-bar count
+
+
 def test_post_job_defaults_source_when_omitted(data_api_engine):
     """A job that omits `source` resolves the config `default_source` (J-17 fetch behavior preserved); the
     response echoes it (not secret) and carries NO key. A backfill job needs no network."""
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index c0aada5d..3488cb96 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -463,17 +463,22 @@ def test_availability_from_storage_empty_db_matches_honest_fallback():
 
 
 def test_availability_from_storage_stale_serves_prior_row_on_stamp_mismatch(coverage_engine):
-    """TC-1 — the iter-57 J-06 during-a-job honesty fix: once a row exists but a NEW bar has landed
+    """TC-2 — the iter-57 J-06 during-a-job honesty fix, gated (iter-58, audit B2 fix) on a job
+    GENUINELY being in flight as well as the stamp mismatch: once a row exists, a NEW bar has landed
     without the finalize-tail warm re-running yet (the `_membership_dataset_version` stamp folds in
     `count(daily_prices)`, so a bare INSERT bumps it — exactly what a mid-flight ingest's first
-    committed bar does), `availability_from_storage` serves the PRIOR persisted row — non-empty cells,
-    `stale: True`, `served_dataset_version` equal to the OLD (pre-bar) stamp, never the current one and
-    never the not-yet-computed empty sentinel."""
+    committed bar does), AND a `data_provider_runs` row genuinely has `status == "running"`,
+    `availability_from_storage` serves the PRIOR persisted row — non-empty cells, `stale: True`,
+    `served_dataset_version` equal to the OLD (pre-bar) stamp, never the current one and never the
+    not-yet-computed empty sentinel."""
     engine, spy_days = coverage_engine
     cfg = load_config()
     with Session(engine) as session:
         prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
         prior_version = data_manager._membership_dataset_version(session, cfg)
+        # a job genuinely in flight (the iter-58 precondition `stale` now requires)
+        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
+        session.commit()
 
     # Simulate an ingest job's first committed bar landing WITHOUT the finalize-tail warm re-running —
     # bumps _membership_dataset_version (count(daily_prices) changes) but leaves AvailabilityCache at V1.
@@ -497,14 +502,76 @@ def test_availability_from_storage_stale_serves_prior_row_on_stamp_mismatch(cove
     assert served["cells"] != []
 
 
+def test_availability_from_storage_stamp_mismatch_without_job_running_is_not_stale(coverage_engine):
+    """TC-1 (iter-58, audit B2 fix) — a stamp mismatch ALONE is no longer enough to mark the served row
+    stale. The SAME stamp-bumping event as the sibling test above (a bare `DailyPrice` INSERT — standing
+    in for any stamp bump with nothing in flight to finish it: a request-path historical view creating a
+    new `ScannerRun`, the boot warm-up's own cadence snapshots, or a finalize warm that was
+    skipped/crashed without landing) now serves `stale: False`, because this fixture has NO
+    `data_provider_runs` row with `status == "running"`. `served_dataset_version` still reads the row's
+    OWN (prior) stamp and the real prior cells are still served — only the honesty flag changes; the
+    page never renders the false '— updating' banner with nothing actually running."""
+    engine, spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
+        prior_version = data_manager._membership_dataset_version(session, cfg)
+
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
+        ))
+        session.commit()
+
+    with Session(engine) as session:
+        current_version = data_manager._membership_dataset_version(session, cfg)
+        served = data_manager.availability_from_storage(session, cfg)
+
+    assert current_version != prior_version  # sanity: the stamp genuinely moved
+    assert served["stale"] is False  # no job in flight — the iter-58 fix
+    assert served["served_dataset_version"] == prior_version
+    assert served["cells"] == prior_payload["cells"]  # the real prior row, never the empty sentinel
+
+
+def test_availability_from_storage_stuck_running_row_from_crashed_process_still_reads_as_in_flight(coverage_engine):
+    """Error case (iter-58 testing requirements): a `data_provider_runs` row stuck at `status ==
+    "running"` from a process that crashed mid-job — with NO corresponding entry in the in-memory
+    `_JOBS` registry, since that registry is process-local and this test never populates it — must NOT
+    be misread as "no job running". `_ingest_job_in_flight` is DB-status-only (never reads `_JOBS`), so
+    it does not false-negative on this exact case: the stuck row alone is enough to keep `stale: True`
+    honest until an operator resolves it (the boot sweep, or a terminal transition)."""
+    engine, spy_days = coverage_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        assert data_manager._JOBS == {}  # sanity: no live in-memory job registered anywhere in this process
+        prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
+        # a row orphaned by a crashed worker — no finished_at, no terminal transition ever landed
+        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
+        session.commit()
+
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
+        ))
+        session.commit()
+
+    with Session(engine) as session:
+        served = data_manager.availability_from_storage(session, cfg)
+
+    assert served["stale"] is True  # the stuck DB row alone is enough — no _JOBS entry needed
+    assert served["cells"] == prior_payload["cells"]
+
+
 def test_availability_from_storage_stale_fallback_never_recomputes(coverage_engine, monkeypatch):
-    """The stale-serving fallback (TC-1) reads ONLY the persisted row — never a live
+    """The stale-serving fallback (TC-2) reads ONLY the persisted row — never a live
     `compute_availability` call on this default request path (AG-8), exactly like the not-yet-computed
     fallback it extends."""
     engine, spy_days = coverage_engine
     cfg = load_config()
     with Session(engine) as session:
         data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
+        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
+        session.commit()
     with Session(engine) as session:
         session.add(DailyPrice(
             symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
diff --git a/apps/frontend/components/availability-heatmap.tsx b/apps/frontend/components/availability-heatmap.tsx
index a95a0ff6..ed49a760 100644
--- a/apps/frontend/components/availability-heatmap.tsx
+++ b/apps/frontend/components/availability-heatmap.tsx
@@ -5,6 +5,7 @@ import { CalendarDays, Loader2 } from "lucide-react";
 
 import { Card } from "@/components/ui/card";
 import { EmptyState } from "@/components/empty-state";
+import { shouldShowAvailabilityEmptyState } from "@/lib/availability-empty-state";
 import { cn } from "@/lib/utils";
 import { formatIsoDate } from "@/lib/dates";
 import type { AvailabilityCell, AvailabilityResponse } from "@/lib/api";
@@ -46,11 +47,19 @@ import type { AvailabilityCell, AvailabilityResponse } from "@/lib/api";
  * ops-hardening iter-57 (J-06 closure): the payload now carries `stale`/`served_dataset_version` (see
  * `AvailabilityResponse` in `lib/api.ts`). `stale: true` means the backend served the MOST RECENT
  * persisted reading rather than the current in-flight one (an ingest is mid-flight; the payload's real
- * cells are shown, exactly as before) — this component now renders a calm "Data as of
- * `<served_dataset_version>` — updating" notice above the grid in that case (mirrors the Coverage
- * panel's existing `coverage-stale-notice` treatment, same tone, same tokens). `stale: false` with
- * non-empty cells renders unchanged; `stale: false` with empty cells is still the ONLY case the "No
- * availability yet" empty state below is honest for (a DB where no row has ever been persisted).
+ * cells are shown, exactly as before) — this component now renders a calm stale notice above the grid
+ * in that case (mirrors the Coverage panel's existing `coverage-stale-notice` treatment, same tone, same
+ * tokens, and — iter-58 — the SAME wording pattern: "as of a prior scan (version …) — refreshes on the
+ * next data job"). `stale: false` with non-empty cells renders unchanged.
+ *
+ * ops-hardening iter-58 (audit B2 + B5 fixes): the backend now only reports `stale: true` when a job is
+ * GENUINELY in flight (`app.engine.data_manager.availability_from_storage`), so this notice can no
+ * longer persist indefinitely with nothing running. Separately (B5), the empty-state gate below no
+ * longer reads `cells.length === 0` alone — it reads the extracted, unit-tested
+ * `shouldShowAvailabilityEmptyState` (`lib/availability-empty-state.ts`), which also requires `!stale`.
+ * A persisted row that happens to be BOTH stale and empty (a narrow precondition) now falls through to
+ * the stale banner above with no grid below it, rather than the "No availability yet" empty state —
+ * that message stays reserved strictly for a DB where no row has ever been persisted.
  */
 
 type DensityBucket = 0 | 1 | 2 | 3 | 4 | 5;
@@ -226,7 +235,7 @@ export function AvailabilityHeatmap({
           className="border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted"
           data-testid="availability-stale-notice"
         >
-          Data as of {state.data.served_dataset_version} — updating
+          Data as of a prior scan (version {state.data.served_dataset_version}) — refreshes on the next data job
         </p>
       ) : null}
 
@@ -245,7 +254,7 @@ export function AvailabilityHeatmap({
         </div>
       ) : null}
 
-      {state.kind === "ok" && state.data.cells.length === 0 ? (
+      {state.kind === "ok" && shouldShowAvailabilityEmptyState(state.data) ? (
         <div className="p-4">
           <EmptyState
             icon={CalendarDays}
```

## Excluded-path stat (dependency/lockfile visibility)

 docs/handoffs/goal-ops-hardening-iter-57-dev.md    |  13 ++
 reports/perf-budgets.md                            | 131 +++++++++++++++++++++
 runs/goal-ops-hardening-iter-57/status.json        |  10 +-
 .../journey-scripts/J-05.json                      |  14 ++-
 runs/goal-session-ops-hardening/state/blueprint.md |   2 +-
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   7 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   1 +
 9 files changed, 172 insertions(+), 10 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
