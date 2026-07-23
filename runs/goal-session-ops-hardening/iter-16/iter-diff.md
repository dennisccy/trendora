# Iteration diff (bounded)

Files changed: 12. Shown in full: 11.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_forward_testing_serving_split.py` (54 lines not shown)

```diff
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index 82c2b785..5f57a527 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -11,14 +11,23 @@ canonical per-date scorecard (cohort return + excess vs SPY/QQQ/sector + the fiv
 with sample size `n` and honest NA, plus the survivorship-bias label and `min_sample` threshold) — AND
 (iter-17) the as-of-scoped forward-tested evidence aggregate.
 
-`evidence_by_horizon` (iter-17, J-09/J-10): per configured horizon, `compute_forward_aggregates(...,
-as_of=run.asof_date)` — the SINGLE canonical forward-return aggregation (by bucket / setup / regime,
-excess vs SPY/QQQ, VCP-vs-non-VCP + the new-pattern breakdowns, and the control-group cohorts, each with
-`n`) scoped to the EXPANDING WINDOW of snapshots dated <= the resolved as-of date. All horizons ride the
-one payload so the client-side horizon selector needs no refetch (J-15/J-18). This RELOCATES the value
-off the retired System Health page (its single home is now Backtest) under the single global as-of
-control; it recomputes no return/score/bucket, reading the stored `forward_returns` exactly as System
-Health did — now filtered to <= D.
+`evidence_by_horizon` (iter-17, J-09/J-10): per configured horizon, the as-of-scoped forward-return
+aggregation (by bucket / setup / regime, excess vs SPY/QQQ, VCP-vs-non-VCP + the new-pattern breakdowns,
+and the control-group cohorts, each with `n`) scoped to the EXPANDING WINDOW of snapshots dated <= the
+resolved as-of date. All horizons ride the one payload so the client-side horizon selector needs no
+refetch (J-15/J-18). This RELOCATES the value off the retired System Health page (its single home is now
+Backtest) under the single global as-of control; it recomputes no return/score/bucket, reading the stored
+`forward_returns` exactly as System Health did — now filtered to <= D.
+
+ops-hardening iter-16 (J-08): for the LATEST view (`is_latest == True`) this endpoint NEVER triggers a
+forward-aggregate compute on the request — `evidence_by_horizon` (plus the new `evidence_status` /
+`evidence_generated_at`) comes ONLY from `resolved_forward_aggregate_evidence`, a pure reader that is
+structurally incapable of calling `compute_forward_aggregates`. A HISTORICAL (`is_latest == False`)
+`?as_of=` request keeps its pre-existing lazy create-once-and-cache behavior UNCHANGED (an explicit,
+logged interpretation call — see the iter-16 dev handoff): this endpoint first ensures every configured
+horizon is cached for that date (computing any still-missing one via `forward_aggregates_ingest_cached`,
+exactly as before iter-16), then reads the result back through the SAME resolver, so both branches share
+one code path for building the response's evidence fields.
 
 It serves the per-date SCORECARD + the as-of-scoped evidence aggregate. Regime / sector / theme / stock
 values stay single-sourced on their own endpoints (`/api/dashboard`, `/api/sectors`, `/api/themes`,
@@ -37,7 +46,8 @@ from app.db import get_session
 from app.engine.forward_testing import (
     backfill_run_forward_returns,
     compute_run_scorecard,
-    forward_aggregates_cached,
+    forward_aggregates_ingest_cached,
+    resolved_forward_aggregate_evidence,
 )
 from app.engine.scanner import _latest_stored_run_date
 from app.engine.snapshot_serving import resolved_run
@@ -60,21 +70,25 @@ def backtest(
     run = resolved_run(session, as_of, cfg)          # immutable snapshot (create-once) or explicit 4xx/503
     backfill_run_forward_returns(session, run, cfg)  # create-once: INSERT-only realized forward returns
     card = compute_run_scorecard(session, run, cfg)  # SINGLE canonical per-date scorecard (reads stored)
-    # iter-17 (J-09/J-10): the as-of-scoped forward-tested evidence aggregate, per configured horizon, all
-    # in the SINGLE payload so the client-side horizon selector needs no refetch (J-15/J-18). Each aggregate
-    # is scoped to the EXPANDING WINDOW of snapshots dated <= the resolved run's asof_date (the SAME global
-    # as-of already resolved — no second date control, J-18). Read-only grouping over the stored
-    # forward_returns — recomputes no return/score/bucket (the same model the retired System Health used).
-    # ops-hardening iter-5 (J-06): served from the ingest-warmed cache (byte-identical to a fresh compute;
-    # `compute_forward_aggregates` itself is unchanged and stays the sole producer) — a live 5-horizon
-    # request here measured 34.77s pre-fix (reports/perf-budgets.md).
-    evidence_by_horizon = {
-        h: forward_aggregates_cached(session, h, cfg, as_of=run.asof_date)
-        for h in cfg.walk_forward.horizons
-    }
     # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
+    is_latest = run.asof_date == _latest_stored_run_date(session)
+    # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
+    # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
+    # for this date (a no-op for an already-warmed date). For the LATEST view this loop never runs, so
+    # this request path never reaches `forward_aggregates_ingest_cached` — let alone
+    # `compute_forward_aggregates` — under any circumstance (J-08's zero-compute-on-request guarantee).
+    if not is_latest:
+        for h in cfg.walk_forward.horizons:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
+    # iter-17 (J-09/J-10) + iter-16 (J-08): the as-of-scoped forward-tested evidence aggregate, ALL
+    # configured horizons resolved together in ONE call (never a per-horizon-independent read — the read
+    # path can otherwise observe a mixed-dataset_version row set, see the resolver's own docstring) plus
+    # the honest `evidence_status` / `evidence_generated_at` disclosure.
+    evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
     return {
         **card,
-        "is_latest": run.asof_date == _latest_stored_run_date(session),
-        "evidence_by_horizon": evidence_by_horizon,
+        "is_latest": is_latest,
+        "evidence_by_horizon": evidence["evidence_by_horizon"],
+        "evidence_status": evidence["evidence_status"],
+        "evidence_generated_at": evidence["evidence_generated_at"],
     }
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index f6e03c1f..7b15a681 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3227,7 +3227,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 # block exactly as before (no regression to that existing behavior). On MemoryError this
                 # loop stops immediately (no further horizons attempted) and forces memory back to the OS.
                 try:
-                    forward_testing.forward_aggregates_cached(session, h, cfg, as_of=latest_run_date)
+                    forward_testing.forward_aggregates_ingest_cached(session, h, cfg, as_of=latest_run_date)
                     forward_aggregates_warmed = True
                 except MemoryError as exc:
                     logger.exception(
@@ -3263,7 +3263,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     # above. Deferred import (not at module level): `indexes.py` already imports `load_seed_meta` FROM
     # this module at ITS OWN module level, so importing `indexes` back here at data_manager's module
     # scope would cycle; the deferred, function-scoped import breaks the cycle exactly like
-    # `forward_aggregates_cached`'s own deferred `_dataset_version` import from `research.py`.
+    # `forward_aggregates_ingest_cached`'s own deferred `_dataset_version` import from `research.py`.
     #
     # iter-8 MemoryError-isolation convention: caught distinctly from the generic exception below, stops
     # immediately (a single key, not a loop — nothing further to attempt) and calls
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 746382aa..dd90d47a 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -985,20 +985,27 @@ def compute_forward_aggregates(
     }
 
 
-# ops-hardening iter-15 (UT-04 fix) — single-flight de-dup guarding `forward_aggregates_cached`'s MISS
-# path. Root-cause evidence (see the dev handoff for the full measurement): reading the pre-iter-15
-# function directly confirmed a cache MISS always fell straight through to `compute_forward_aggregates`
-# with NO de-duplication, lock, or in-flight marker — N concurrent same-key MISSes (e.g. the ingest
-# finalize warm's sequential 5-horizon loop landing on the SAME horizon/as-of the SAME moment
-# `GET /api/backtest`'s own 5-horizon comprehension requests it) each redundantly ran the full
-# aggregation. A throwaway measurement on a 60,000-row fixture (this iteration's dev pass) reproduced
-# this directly: 5 concurrent same-key MISSes invoked `compute_forward_aggregates` 5 times (not 1) and
-# took 9.9x a single call's wall-clock (near-linear blowup, consistent with GIL-serialized redundant
-# CPU-bound work) — confirming this mechanism, not a hypothesis. This mirrors
-# `data_manager.compute_coverage`'s established J-100 per-key-lock + in-flight-event single-flight idiom
-# (no new concurrency abstraction) — the difference: `ForwardAggregateCache` is already a PERSISTED
-# cross-request cache, so a waiter does not need its own in-process result cache; it simply re-reads the
-# now-committed row with its OWN session once the owner signals completion.
+# ops-hardening iter-15 (UT-04 fix) — single-flight de-dup guarding the ingest-only cache's MISS path
+# (`forward_aggregates_ingest_cached`, split from this iteration's own `forward_aggregates_cached` by
+# ops-hardening iter-16, J-08 — see that function's docstring for the split). Root-cause evidence (see
+# the dev handoff for the full measurement): reading the pre-iter-15 function directly confirmed a cache
+# MISS always fell straight through to `compute_forward_aggregates` with NO de-duplication, lock, or
+# in-flight marker — N concurrent same-key MISSes (e.g. the ingest finalize warm's sequential 5-horizon
+# loop landing on the SAME horizon/as-of the SAME moment `GET /api/backtest`'s own 5-horizon
+# comprehension requests it) each redundantly ran the full aggregation. A throwaway measurement on a
+# 60,000-row fixture (this iteration's dev pass) reproduced this directly: 5 concurrent same-key MISSes
+# invoked `compute_forward_aggregates` 5 times (not 1) and took 9.9x a single call's wall-clock (near-
+# linear blowup, consistent with GIL-serialized redundant CPU-bound work) — confirming this mechanism,
+# not a hypothesis. This mirrors `data_manager.compute_coverage`'s established J-100 per-key-lock +
+# in-flight-event single-flight idiom (no new concurrency abstraction) — the difference:
+# `ForwardAggregateCache` is already a PERSISTED cross-request cache, so a waiter does not need its own
+# in-process result cache; it simply re-reads the now-committed row with its OWN session once the owner
+# signals completion.
+#
+# iter-16 (J-08): this lock/event/timeout trio is UNCHANGED by the compute-vs-serve split below — it
+# still guards ONLY `forward_aggregates_ingest_cached`'s MISS path (now the SOLE remaining caller of
+# `compute_forward_aggregates`). The new read-only serving path added below has no MISS/compute branch
+# at all, so it needs no single-flight guard of its own.
 _FORWARD_AGG_LOCK = threading.Lock()
 # per-key in-flight events: (horizon, asof_key, dataset_version) -> threading.Event, set when the owner
 # finishes (success or failure) so any waiter wakes. Always removed by the owner in a `finally` — this
@@ -1013,17 +1020,23 @@ _FORWARD_AGG_INFLIGHT: dict[tuple, threading.Event] = {}
 _FORWARD_AGG_WAIT_TIMEOUT_S = 45.0
 
 
-def forward_aggregates_cached(
+def forward_aggregates_ingest_cached(
     session: Session, horizon: int, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
 ) -> dict:
-    """Serve `compute_forward_aggregates` from an ingest-time warm cache (ops-hardening iter-5, J-06),
-    mirroring `research.event_study_cached` / `market_phase.market_phase_cached`: on a cache HIT for the
-    current `(horizon, asof_key, dataset_version)` key, deserialize and return the stored aggregate (NO
-    recompute); on a MISS, compute it ONCE via `compute_forward_aggregates` (the SOLE producer — this
-    function is a pure serving/persistence wrapper, never a second derivation), persist it under the
-    current dataset-version stamp, prune any stale rows for this `(horizon, asof_key)` identity, and
-    return it. The returned payload is BYTE-IDENTICAL to `compute_forward_aggregates(...)` (No recompute
-    in the read path).
+    """The INGEST-ONLY compute-and-persist half of the ops-hardening iter-5 `ForwardAggregateCache`
+    wrapper (split from the former single `forward_aggregates_cached` by iter-16, J-08). This is now the
+    SOLE remaining caller of `compute_forward_aggregates` (the other half is `resolved_forward_
+    aggregate_evidence` below — a pure reader that can never reach `compute_forward_aggregates`). Callers:
+    (a) the ingest finalize warm's per-horizon loop (`data_manager._refresh_ingest_aggregates`, the
+    `is_latest` producer), and (b) `GET /api/backtest` / MCP `query_backtest`'s existing, UNCHANGED
+    historical (`is_latest == False`) create-once-and-cache carve-out (TC-13) — never the `is_latest`
+    request-serving branch of either, which calls ONLY `resolved_forward_aggregate_evidence`.
+
+    On a cache HIT for the current `(horizon, asof_key, dataset_version)` key, deserialize and return the
+    stored aggregate (NO recompute); on a MISS, compute it ONCE via `compute_forward_aggregates` (the SOLE
+    producer — this function is a pure serving/persistence wrapper, never a second derivation), persist it
+    under the current dataset-version stamp, and return it. The returned payload is BYTE-IDENTICAL to
+    `compute_forward_aggregates(...)` (No recompute in the read path).
 
     WHY: `GET /api/backtest` called `compute_forward_aggregates` once per configured horizon (5) on
     EVERY request — each call scans the WHOLE horizon-partition of `forward_returns` (~1.5-1.7M rows /
@@ -1046,7 +1059,18 @@ def forward_aggregates_cached(
     (bounded) on the owner's completion, then re-reads the now-persisted row with its OWN session — never
     a second producer/compute. This is scoped ENTIRELY to this serving/caching wrapper:
     `compute_forward_aggregates` itself, its signature, its columns read, and its streamed pattern are
-    completely unchanged (all three call sites keep calling it exactly as before).
+    completely unchanged (all three call sites keep calling it exactly as before). iter-16 (J-08): this
+    guard is UNCHANGED by the split (TC-17) — it still protects only this ingest-only path.
+
+    ops-hardening iter-16 (J-08): pruning of superseded rows changed from PER-HORIZON-WRITE deletion to a
+    CUTOVER — a stale `dataset_version`'s rows for this `asof_key` are deleted in one shot ONLY once this
+    write brings the CURRENT version's configured-horizon set (`config.walk_forward.horizons`) to full
+    completeness, never before. This closes a confirmed live bug: the OLD per-horizon-write deletion fired
+    the moment ANY one horizon's new-version row landed, so a reader between horizon-writes could already
+    observe a MIXED row set (proof: a direct read-only inspection of the live DB found the non-latest
+    `asof_key='2026-07-17'` already split across two `dataset_version` stamps across its 5 rows). Retaining
+    the old version's full row set until the new one is complete is what lets `resolved_forward_aggregate_
+    evidence` below always serve either an all-old or all-new set for one `asof_key` — never mixed.
 
     Deferred import below (not at module level): `research.py` already imports names FROM this module,
     so this module cannot import `research.py` at load time without a circular import; importing
@@ -1095,17 +1119,28 @@ def forward_aggregates_cached(
     try:
         payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
 
-        # prune stale rows for THIS (horizon, asof_key) identity (any older dataset_version) so the cache
-        # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
-        stale = session.exec(
-            select(ForwardAggregateCache).where(
-                ForwardAggregateCache.horizon == horizon,
-                ForwardAggregateCache.asof_key == asof_key,
-                ForwardAggregateCache.dataset_version != version,
-            )
-        ).all()
-        for row in stale:
-            session.delete(row)
+        # iter-16 (J-08) cutover: only prune OTHER-dataset_version rows for this asof_key once THIS
+        # write brings the CURRENT version's configured-horizon set to completeness — never per-horizon.
+        # An incomplete current version leaves every prior version's rows untouched, so a concurrent
+        # reader always has either a fully-old or a fully-new (never mixed) row set to serve.
+        existing_horizons_at_version = set(
+            session.exec(
+                select(ForwardAggregateCache.horizon).where(
+                    ForwardAggregateCache.asof_key == asof_key,
+                    ForwardAggregateCache.dataset_version == version,
+                )
+            ).all()
+        )
+        would_be_complete = {horizon, *existing_horizons_at_version} >= set(cfg.walk_forward.horizons)
+        if would_be_complete:
+            stale = session.exec(
+                select(ForwardAggregateCache).where(
+                    ForwardAggregateCache.asof_key == asof_key,
+                    ForwardAggregateCache.dataset_version != version,
+                )
+            ).all()
+            for row in stale:
+                session.delete(row)
 
         session.add(ForwardAggregateCache(
             horizon=horizon, asof_key=asof_key, dataset_version=version,
@@ -1125,6 +1160,88 @@ def forward_aggregates_cached(
             event.set()
 
 
+def resolved_forward_aggregate_evidence(
+    session: Session, as_of: date_cls, config: Optional[Config] = None,
+) -> dict:
+    """The READ-ONLY serving path (ops-hardening iter-16, J-08) — the ONLY code `GET /api/backtest` and
+    the MCP `query_backtest` tool call for their `is_latest == True` view. Structurally incapable of
+    calling `compute_forward_aggregates` under ANY circumstance, including a would-be lock-wait timeout:
+    there is no compute-fallback branch here at all (that fallback stays on `forward_aggregates_ingest_
+    cached` only, scoped to the producer-vs-producer ingest race, never reachable from a request).
+
+    Resolves, for `as_of`, the latest `dataset_version` whose stored rows cover EVERY horizon in
+    `config.walk_forward.horizons` ("complete") for this `asof_key` — never a per-horizon-independent
+    read (the bug this closes: a naive "latest row per horizon, ignoring version" read can already serve
+    a MIXED-version payload today — confirmed live, the non-latest `asof_key='2026-07-17'` is split
+    across two `dataset_version` stamps across its 5 rows). Returns
+    `{"evidence_status", "evidence_generated_at", "evidence_by_horizon"}`:
+
+      - `"ready"` — the complete version found IS the current global `_dataset_version` stamp; serves
+        it, keyed by horizon (int), byte-identical to a fresh `compute_forward_aggregates` call.
+      - `"refreshing"` — the current stamp's row set is not yet complete (an ingest warm is mid-flight),
+        but a PRIOR complete version's full row set survives (the iter-16 cutover-pruning contract keeps
+        it until the new version's own set lands) — serves that older version's rows, ALL from the SAME
+        version (never mixed with the incomplete new one), labeled with that version's OWN
+        `created_at` (the max across its horizon rows).
+      - `"not_yet_computed"` — no complete version has EVER existed for this `asof_key`:
+        `evidence_by_horizon = {}`, `evidence_generated_at = None`. Still HTTP 200 at the caller (an
+        honest empty state) — never a synchronous compute, never 500/503.
+
+    The completeness-lookup query is filtered by `asof_key` ALONE (never an unfiltered scan of the whole
+    `forward_aggregate_cache` table — AG-8 spirit, TC-18): it touches only the handful of rows already
+    belonging to this ONE identity, regardless of how many other historical `asof_key`s the table has
+    accumulated over the session. The result set is inherently small (at most ~2 `dataset_version`s'
+    worth of rows per identity under the cutover contract above), so a plain `.all()` needs no streaming.
+
+    Deferred import (not at module level): mirrors `forward_aggregates_ingest_cached`'s own established
+    reason (`research.py` imports FROM this module, so a module-level import back would be circular)."""
+    from app.engine.research import _dataset_version  # deferred: avoids a forward_testing<->research cycle
+
+    cfg = config or get_config()
+    configured_horizons = set(cfg.walk_forward.horizons)
+    asof_key = as_of.isoformat()
+
+    # asof_key-filtered read (TC-18) — bounded to this one identity's rows, never the whole table.
+    rows = session.exec(
+        select(
+            ForwardAggregateCache.horizon, ForwardAggregateCache.dataset_version,
+            ForwardAggregateCache.payload_json, ForwardAggregateCache.created_at,
+        ).where(ForwardAggregateCache.asof_key == asof_key)
+    ).all()
+
+    by_version: dict[str, dict[int, tuple[str, datetime]]] = defaultdict(dict)
+    for row_horizon, row_version, payload_json, created_at in rows:
+        by_version[row_version][row_horizon] = (payload_json, created_at)
+
+    complete = {
+        version: horizon_map
+        for version, horizon_map in by_version.items()
+        if set(horizon_map) >= configured_horizons
+    }
+
+    def _serve(version: str, status: str) -> dict:
+        horizon_map = complete[version]
+        evidence_by_horizon = {h: json.loads(horizon_map[h][0]) for h in sorted(horizon_map)}
+        generated_at = max(created_at for _payload_json, created_at in horizon_map.values())
+        return {
+            "evidence_status": status,
+            "evidence_generated_at": generated_at.isoformat(),
+            "evidence_by_horizon": evidence_by_horizon,
+        }
+
+    current_version = _dataset_version(session)
+    if current_version in complete:
+        return _serve(current_version, "ready")
+
+    if complete:
+        # a PRIOR complete version survives the cutover (never mixed with the incomplete current one) —
+        # the "latest" surviving prior version, tie-broken by its own newest row's created_at.
+        stale_version = max(complete, key=lambda v: max(ca for _p, ca in complete[v].values()))
+        return _serve(stale_version, "refreshing")
+
+    return {"evidence_status": "not_yet_computed", "evidence_generated_at": None, "evidence_by_horizon": {}}
+
+
 # --------------------------------------------------------------------------------------------------
 # Per-date scorecard (J-14) — create-once population + the SINGLE per-date forward-test read
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 39721ecd..b5df7072 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -32,7 +32,8 @@ from app.engine.forward_testing import (
     backfill_run_forward_returns,
     benchmark_symbols,
     compute_run_scorecard,
-    forward_aggregates_cached,
+    forward_aggregates_ingest_cached,
+    resolved_forward_aggregate_evidence,
 )
 from app.engine.referee import (
     DEFAULT_ALPHA_BUDGET,
@@ -191,24 +192,33 @@ def get_market_phase(
 def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     """`GET /api/backtest` — the per-date forward-test scorecard (cohort return + excess vs SPY/QQQ/
     sector + the control cohorts, each with sample size `n`) plus the as-of-scoped `evidence_by_horizon`
-    aggregate and `is_latest`. Mirrors the endpoint exactly, including the read-path *create-once*
-    population of this run's realized forward returns (INSERT-only into the append-only table; a no-op
-    once warmed) — it recomputes no score / bucket / return."""
+    aggregate, `evidence_status`, `evidence_generated_at`, and `is_latest`. Mirrors the endpoint exactly,
+    including the read-path *create-once* population of this run's realized forward returns (INSERT-only
+    into the append-only table; a no-op once warmed) — it recomputes no score / bucket / return.
+
+    ops-hardening iter-16 (J-08): mirrors the endpoint's own compute-vs-serve split exactly — for the
+    LATEST view this tool never reaches `forward_aggregates_ingest_cached` (let alone
+    `compute_forward_aggregates`); a historical `asof` keeps the pre-existing lazy create-once-and-cache
+    carve-out (TC-13), unchanged."""
     cfg = get_config()
     run = resolved_run(session, asof, cfg)
     backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
     card = compute_run_scorecard(session, run, cfg)
-    # ops-hardening iter-5 (J-06): served from the SAME ingest-warmed cache GET /api/backtest now uses
-    # (this function's own docstring says it "mirrors the endpoint exactly" — kept true for the cache
-    # swap too; byte-identical output, `compute_forward_aggregates` itself is unchanged).
-    evidence_by_horizon = {
-        h: forward_aggregates_cached(session, h, cfg, as_of=run.asof_date)
-        for h in cfg.walk_forward.horizons
-    }
+    is_latest = run.asof_date == _latest_stored_run_date(session)
+    if not is_latest:
+        for h in cfg.walk_forward.horizons:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
+    # ops-hardening iter-5 (J-06) + iter-16 (J-08): served from the SAME read-only resolver
+    # `GET /api/backtest` now uses (this function's own docstring says it "mirrors the endpoint exactly"
+    # — kept true for the compute-vs-serve split too; byte-identical output, `compute_forward_aggregates`
+    # itself is unchanged).
+    evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
     return {
         **card,
-        "is_latest": run.asof_date == _latest_stored_run_date(session),
-        "evidence_by_horizon": evidence_by_horizon,
+        "is_latest": is_latest,
+        "evidence_by_horizon": evidence["evidence_by_horizon"],
+        "evidence_status": evidence["evidence_status"],
+        "evidence_generated_at": evidence["evidence_generated_at"],
     }
 
 
diff --git a/apps/backend/tests/conftest.py b/apps/backend/tests/conftest.py
index ef90ee26..86054925 100644
--- a/apps/backend/tests/conftest.py
+++ b/apps/backend/tests/conftest.py
@@ -5,6 +5,7 @@ import sys
 from pathlib import Path
 
 import pytest
+from sqlmodel import Session
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 SEED_DIR = BACKEND_DIR / "data" / "seed"
@@ -14,8 +15,8 @@ if str(BACKEND_DIR) not in sys.path:
 from app import db as db_module  # noqa: E402
 from app.config import load_config  # noqa: E402
 from app.db import create_db_and_tables, make_engine  # noqa: E402
-from app.engine.forward_testing import backfill_forward_returns  # noqa: E402
-from app.engine.scanner import bootstrap_runs  # noqa: E402
+from app.engine.forward_testing import backfill_forward_returns, forward_aggregates_ingest_cached  # noqa: E402
+from app.engine.scanner import _latest_stored_run_date, bootstrap_runs  # noqa: E402
 from app.seed_loader import load_seed  # noqa: E402
 
 
@@ -52,7 +53,18 @@ def loaded_engine(tmp_path_factory, config, seed_dir):
     (`bootstrap_runs` + `backfill_forward_returns`); `test_warmup.py::test_..._only_old_synchronous_path_is_a_noop`
     proves this is byte-identical to what the background warm-up produces (no second compute path). With
     the DB already warm, the `TestClient` lifespan's single-flight-guarded warm-up is an idempotent no-op,
-    so tests never assert against a mid-warm-up, concurrently-mutating DB."""
+    so tests never assert against a mid-warm-up, concurrently-mutating DB.
+
+    ops-hardening iter-16 (J-08): `GET /api/backtest` / MCP `query_backtest`'s LATEST (`is_latest==True`)
+    view now serves `evidence_by_horizon` ONLY from the read-only `resolved_forward_aggregate_evidence`
+    resolver, which NEVER computes on a request — so the latest run's `ForwardAggregateCache` rows must
+    already exist before any test reads them, exactly as the real ingest finalize hook
+    (`data_manager._refresh_ingest_aggregates`) would warm them at ingest time. This fixture mirrors that
+    ONE warm sub-step here (via the SAME `forward_aggregates_ingest_cached` the finalize hook calls — no
+    second compute path) so the many existing `loaded_engine`-based tests that read the latest date's
+    `evidence_by_horizon` content keep seeing the SAME byte-identical values they did before the J-08
+    split (previously warmed lazily on a test's first `/api/backtest` request; now warmed here up front,
+    since the request path itself no longer computes)."""
     db_path = tmp_path_factory.mktemp("db") / "trendora_test.db"
     engine = make_engine(f"sqlite:///{db_path}")
     create_db_and_tables(engine)
@@ -62,5 +74,10 @@ def loaded_engine(tmp_path_factory, config, seed_dir):
     # work the background warm-up does, only paid up-front + synchronously so the suite is deterministic.
     bootstrap_runs(engine, config)
     backfill_forward_returns(engine, config)
+    with Session(engine) as session:
+        latest_date = _latest_stored_run_date(session)
+        if latest_date is not None:
+            for h in config.walk_forward.horizons:
+                forward_aggregates_ingest_cached(session, h, config, as_of=latest_date)
     db_module.set_engine(engine)
     return engine
diff --git a/apps/backend/tests/test_api_backtest.py b/apps/backend/tests/test_api_backtest.py
index 9e0e06cf..42786e24 100644
--- a/apps/backend/tests/test_api_backtest.py
+++ b/apps/backend/tests/test_api_backtest.py
@@ -183,12 +183,13 @@ def test_backtest_503_when_no_price_data(tmp_path):
 def test_backtest_does_not_reserve_regime_or_stock_values(loaded_engine):
     """The endpoint serves the per-date scorecard + the as-of-scoped evidence aggregate ONLY — it does
     not re-serve regime/sector/theme/stock values (those stay single-sourced on their own endpoints).
-    The payload's top-level keys are exactly the scorecard contract plus `evidence_by_horizon` (iter-17)."""
+    The payload's top-level keys are exactly the scorecard contract plus `evidence_by_horizon` (iter-17)
+    plus `evidence_status` / `evidence_generated_at` (iter-16, J-08)."""
     with TestClient(main.app) as client:
         data = client.get("/api/backtest").json()
     assert set(data) == {
         "asof_date", "is_latest", "min_sample", "horizons", "survivorship_bias",
-        "scorecard", "evidence_by_horizon",
+        "scorecard", "evidence_by_horizon", "evidence_status", "evidence_generated_at",
     }
 
 
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 08caa034..58f2d057 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1090,10 +1090,16 @@ def test_finalize_hook_warms_forward_aggregates_for_every_configured_horizon(fin
 def test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read(
     finalize_hook_engine, monkeypatch
 ):
-    """A `GET /api/backtest`-shaped read for the SAME (horizon, as-of) the finalize hook just warmed
-    hits the cache — zero further `compute_forward_aggregates` calls. This is the actual perf fix this
-    iteration makes: a live request no longer pays the 5-horizon full-table scan the finalize hook
-    already paid at ingest (measured 34.77s pre-fix for one request, `reports/perf-budgets.md`)."""
+    """A `GET /api/backtest`-shaped read for the SAME as-of the finalize hook just warmed hits the cache
+    — zero further `compute_forward_aggregates` calls. This is the actual perf fix this iteration makes:
+    a live request no longer pays the 5-horizon full-table scan the finalize hook already paid at ingest
+    (measured 34.77s pre-fix for one request, `reports/perf-budgets.md`).
+
+    ops-hardening iter-16 (J-08): updated to call `resolved_forward_aggregate_evidence` — the actual
+    read-only serving path `GET /api/backtest` / MCP `query_backtest` use for the latest view since the
+    compute-vs-serve split (the former `forward_aggregates_cached` this test used to call directly is now
+    `forward_aggregates_ingest_cached`, the INGEST-ONLY half — no longer what a request-shaped read
+    calls, so exercising it here would no longer prove this test's own claim)."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     with Session(engine) as session:
@@ -1110,9 +1116,10 @@ def test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_rea
 
     monkeypatch.setattr(forward_testing, "compute_forward_aggregates", _counting)
     with Session(engine) as session:
-        for h in cfg.walk_forward.horizons:
-            forward_testing.forward_aggregates_cached(session, h, cfg, as_of=d)
+        evidence = forward_testing.resolved_forward_aggregate_evidence(session, d, cfg)
     assert call_count["n"] == 0, "the finalize hook's warm should have already cached every horizon"
+    assert evidence["evidence_status"] == "ready"
+    assert set(evidence["evidence_by_horizon"]) == set(cfg.walk_forward.horizons)
 
 
 def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finalize_hook_engine):
@@ -1277,7 +1284,7 @@ def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_eng
 
     monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _boom)
     monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
-    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _boom)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
     monkeypatch.setattr(data_manager, "event_study_cached", _boom)
     monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
     with Session(engine) as session:
@@ -1742,7 +1749,7 @@ def test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_l
         calls["n"] += 1
         raise MemoryError("simulated memory pressure")
 
-    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _boom)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="fa-mem-first-probe", kind="backfill", start=d, end=d)
         prog.new_snapshot_dates = [d]
@@ -1761,7 +1768,7 @@ def test_finalize_hook_forward_aggregates_memory_error_after_partial_success_rep
     cfg = load_config()
     n_horizons = len(cfg.walk_forward.horizons)
     assert n_horizons >= 3, "fixture config must configure >= 3 horizons for this test to be meaningful"
-    real = forward_testing.forward_aggregates_cached
+    real = forward_testing.forward_aggregates_ingest_cached
     calls = {"n": 0}
 
     def _succeed_then_boom(session, horizon, config=None, *, as_of=None):
@@ -1770,7 +1777,7 @@ def test_finalize_hook_forward_aggregates_memory_error_after_partial_success_rep
             return real(session, horizon, config, as_of=as_of)
         raise MemoryError("simulated memory pressure")
 
-    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _succeed_then_boom)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _succeed_then_boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="fa-mem-partial-probe", kind="backfill", start=d, end=d)
         prog.new_snapshot_dates = [d]
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 397576cd..908045ed 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -33,7 +33,7 @@ from app.engine.forward_testing import (
     compute_drawdown_expectations,
     compute_drawdown_expectations_cached,
     compute_forward_aggregates,
-    forward_aggregates_cached,
+    forward_aggregates_ingest_cached,
     forward_excursions,
     forward_return,
     max_drawdown,
@@ -813,13 +813,14 @@ def test_aggregates_as_of_scoped_consistency_invariant_relocated(aggregates_engi
 
 
 # ==================================================================================================
-# forward_aggregates_cached (ops-hardening iter-5, J-06) — the ForwardAggregateCache performance layer.
-# GET /api/backtest called compute_forward_aggregates once per configured horizon (5) on EVERY request;
-# measured live at 34.77s for one request (reports/perf-budgets.md). This cache mirrors
-# research.event_study_cached / market_phase.market_phase_cached / this module's own
-# compute_drawdown_expectations_cached exactly.
+# forward_aggregates_ingest_cached (ops-hardening iter-5, J-06; split from the former single
+# `forward_aggregates_cached` by iter-16, J-08 — see forward_testing.py's own module-level history) — the
+# ForwardAggregateCache performance layer's INGEST-ONLY compute-and-persist half. GET /api/backtest
+# called compute_forward_aggregates once per configured horizon (5) on EVERY request; measured live at
+# 34.77s for one request (reports/perf-budgets.md). This cache mirrors research.event_study_cached /
+# market_phase.market_phase_cached / this module's own compute_drawdown_expectations_cached exactly.
 # ==================================================================================================
-def test_forward_aggregates_cached_byte_identical_and_single_row(aggregates_engine):
+def test_forward_aggregates_ingest_cached_byte_identical_and_single_row(aggregates_engine):
     """A cache MISS then HIT both return a payload BYTE-IDENTICAL to a fresh uncached
     `compute_forward_aggregates` call, and exactly ONE `ForwardAggregateCache` row is written for this
     (horizon, as_of) (no duplicate insert on the second call)."""
@@ -828,8 +829,8 @@ def test_forward_aggregates_cached_byte_identical_and_single_row(aggregates_engi
     as_of = date(2025, 1, 10)
     with Session(engine) as session:
         fresh = compute_forward_aggregates(session, H, cfg, as_of=as_of)
-        miss = forward_aggregates_cached(session, H, cfg, as_of=as_of)
-        hit = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        miss = forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)
+        hit = forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)
         rows = session.exec(
             select(ForwardAggregateCache).where(
                 ForwardAggregateCache.horizon == H,
@@ -840,7 +841,7 @@ def test_forward_aggregates_cached_byte_identical_and_single_row(aggregates_engi
     assert len(rows) == 1
 
 
-def test_forward_aggregates_cached_avoids_recompute_on_hit(aggregates_engine, monkeypatch):
+def test_forward_aggregates_ingest_cached_avoids_recompute_on_hit(aggregates_engine, monkeypatch):
     """The SECOND call for the SAME (horizon, as_of) never re-invokes the uncached
     `compute_forward_aggregates` — proven by monkeypatching it to count calls (a call-count proof, not
     just a byte-match, so a bug that silently recomputed-but-still-matched would still fail this test)."""
@@ -858,32 +859,41 @@ def test_forward_aggregates_cached_avoids_recompute_on_hit(aggregates_engine, mo
 
     monkeypatch.setattr(forward_testing_module, "compute_forward_aggregates", _counting)
     with Session(engine) as session:
-        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # MISS -> 1 call
-        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
-        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
+        forward_testing_module.forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)  # MISS -> 1 call
+        forward_testing_module.forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
+        forward_testing_module.forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
     assert call_count["n"] == 1
 
 
-def test_forward_aggregates_cached_refreshes_on_dataset_version_change(aggregates_engine):
+def test_forward_aggregates_ingest_cached_refreshes_on_dataset_version_change(aggregates_engine):
     """The cache refreshes when the dataset changes (no stale figure): adding one more forward-return
     observation on the SAME already-included run bumps `_dataset_version`, so the next call for the SAME
-    (horizon, as_of) recomputes (a genuinely larger cohort) rather than serving the pre-change payload,
-    and the stale row is pruned (iter-2 B1 lesson: a fingerprint-only invalidation must not serve a
-    false/stale figure — this reuses the SAME already-hardened `research._dataset_version` stamp, never
-    a new invalidation mechanism)."""
+    (horizon, as_of) recomputes (a genuinely larger cohort) rather than serving the pre-change payload
+    (iter-2 B1 lesson: a fingerprint-only invalidation must not serve a false/stale figure — this reuses
+    the SAME already-hardened `research._dataset_version` stamp, never a new invalidation mechanism).
+
+    iter-16 (J-08) updated this test for the cutover pruning contract: a superseded version's rows now
+    survive until the NEW version's FULL configured-horizon set is complete (never per-horizon), so this
+    warms EVERY configured horizon (not just `H`) both before and after the dataset change — mirroring
+    what the real ingest finalize warm loop does — and additionally proves the mid-refresh state: with
+    only `H` refreshed at the new version (every OTHER horizon still incomplete there), the OLD version's
+    row for `H` is NOT yet pruned (the cutover has not fired) — only once every configured horizon is
+    refreshed does the old version's entire row set for this `asof_key` disappear in one shot."""
     engine, H = aggregates_engine
     cfg = load_config()
     as_of = date(2025, 1, 10)
+    horizons = cfg.walk_forward.horizons
     with Session(engine) as session:
-        before = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        for h in horizons:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=as_of)
+        before = forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)  # HIT — already warmed above
         from app.engine.research import _dataset_version
         v_before = _dataset_version(session)
         rows_before = session.exec(
-            select(ForwardAggregateCache).where(
-                ForwardAggregateCache.horizon == H, ForwardAggregateCache.asof_key == as_of.isoformat(),
-            )
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == as_of.isoformat())
         ).all()
-        assert len(rows_before) == 1 and rows_before[0].dataset_version == v_before
+        assert len(rows_before) == len(horizons)
+        assert {r.dataset_version for r in rows_before} == {v_before}
 
         # change the dataset: one more forward-return observation on run1 (the already-included latest
         # run) -- a genuinely different cohort at the SAME (horizon, as_of) key.
@@ -894,15 +904,32 @@ def test_forward_aggregates_cached_refreshes_on_dataset_version_change(aggregate
         v_after = _dataset_version(session)
         assert v_after != v_before
 
-        after = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        # refresh ONLY H at the new version — the cutover must NOT fire yet: v_before's rows for every
+        # OTHER configured horizon are still incomplete at v_after, so nothing is pruned.
+        mid_refresh = forward_aggregates_ingest_cached(session, H, cfg, as_of=as_of)
+        rows_mid = session.exec(
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == as_of.isoformat())
+        ).all()
+        by_version_mid: dict[str, set[int]] = {}
+        for row in rows_mid:
+            by_version_mid.setdefault(row.dataset_version, set()).add(row.horizon)
+        assert by_version_mid.get(v_before) == set(horizons), (
+            "the OLD version's full row set must survive an incomplete new-version refresh (cutover gate)"
+        )
+        assert by_version_mid.get(v_after) == {H}
+
+        # now refresh every OTHER configured horizon too -- the new version becomes complete, so the
+        # cutover fires and the old version's entire row set for this asof_key is pruned in one shot.
+        for h in horizons:
+            if h != H:
+                forward_aggregates_ingest_cached(session, h, cfg, as_of=as_of)
         rows_after = session.exec(
-            select(ForwardAggregateCache).where(
-                ForwardAggregateCache.horizon == H, ForwardAggregateCache.asof_key == as_of.isoformat(),
-            )
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == as_of.isoformat())
         ).all()
-    assert len(rows_after) == 1 and rows_after[0].dataset_version == v_after
+    assert {r.dataset_version for r in rows_after} == {v_after}
+    assert {r.horizon for r in rows_after} == set(horizons)
     assert before["overall"]["n"] == 6
-    assert after["overall"]["n"] == 7  # the recompute picked up the new ZZZ observation
+    assert mid_refresh["overall"]["n"] == 7  # the recompute picked up the new ZZZ observation
 
 
 # ==================================================================================================
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
index 6d2feb41..858dba76 100644
--- a/apps/backend/tests/test_forward_testing_concurrency.py
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -24,15 +24,22 @@ of margin — and is verified empirically by the tests below (not just asserted)
 TC-4 mirrors iter-13's actual trigger shape (4 concurrent backfills' finalize hooks + a diagnostic read,
 not a single sequential process) with a `ThreadPoolExecutor`: each thread opens its OWN `Session` against
 a SHARED file-based engine — the same way a real multi-threaded ASGI server's request-handling threads
-each independently call into `compute_forward_aggregates`/`forward_aggregates_cached`.
+each independently call into `compute_forward_aggregates`/`forward_aggregates_ingest_cached`.
 
 ops-hardening iter-15 (UT-04 fix) ADDS a second, clearly-separated test group at the bottom of this file
-(see the banner comment below) proving the single-flight de-dup this iteration adds to
-`forward_aggregates_cached`'s MISS path: TC-1 (same-key concurrent-MISS de-dup), TC-2 (concurrent-write-
-during-read wall-clock ratio — isolates candidate (c), WAL/session contention, from candidate (a)), and
-TC-8 (the fix's own failure path never deadlocks a waiter). These are a DIFFERENT iteration's TC numbering
-than iter-14's OWN TC-3/TC-4 above — named descriptively (never `test_tc1_`/`test_tc2_`) to avoid any
-ambiguity with iter-14's existing test names.
+(see the banner comment below) proving the single-flight de-dup this iteration adds to the ingest-time
+cache's MISS path: TC-1 (same-key concurrent-MISS de-dup), TC-2 (concurrent-write-during-read wall-clock
+ratio — isolates candidate (c), WAL/session contention, from candidate (a)), and TC-8 (the fix's own
+failure path never deadlocks a waiter). These are a DIFFERENT iteration's TC numbering than iter-14's OWN
+TC-3/TC-4 above — named descriptively (never `test_tc1_`/`test_tc2_`) to avoid any ambiguity with
+iter-14's existing test names.
+
+ops-hardening iter-16 (J-08) renamed the function under test here: the former single `forward_aggregates_
+cached` (no "_ingest_") split into an ingest-only compute-and-persist half (`forward_aggregates_ingest_
+cached`, exercised below — the single-flight guard's home, UNCHANGED by the split) and a new read-only
+serving half (`resolved_forward_aggregate_evidence`, covered by `test_forward_testing_serving_split.py`).
+Every test in this file now proves iter-16's TC-17 ("single-flight still holds on the ingest-only path
+post-split") by construction — same guard, same tests, new function name.
 """
 from __future__ import annotations
 
@@ -50,7 +57,7 @@ from sqlmodel import Session, select
 
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
-from app.engine.forward_testing import compute_forward_aggregates, forward_aggregates_cached
+from app.engine.forward_testing import compute_forward_aggregates, forward_aggregates_ingest_cached
 from app.models import DailyPrice, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
 
 BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)  # apps/backend — for the child subprocess's sys.path
@@ -104,7 +111,7 @@ def _build_memory_pressure_db(db_path: Path) -> None:
         ]
         session.execute(insert(ForwardReturn.__table__), fr_rows)
         session.commit()
-        forward_aggregates_cached(session, HORIZON, cfg, as_of=None)
+        forward_aggregates_ingest_cached(session, HORIZON, cfg, as_of=None)
 
 
 @pytest.fixture(scope="module")
@@ -247,7 +254,7 @@ def test_tc3_rewritten_pattern_succeeds_under_the_same_cap_that_broke_the_old_on
 def _cached_caller(engine, horizon: int) -> dict:
     cfg = load_config()
     with Session(engine) as session:
-        return forward_aggregates_cached(session, horizon, cfg, as_of=None)
+        return forward_aggregates_ingest_cached(session, horizon, cfg, as_of=None)
 
 
 def _direct_caller(engine, horizon: int) -> dict:
@@ -257,9 +264,9 @@ def _direct_caller(engine, horizon: int) -> dict:
 
 
 def test_tc4_concurrent_callers_all_complete_within_bounded_timeout(memory_pressure_db):
-    """TC-4: 4 concurrent `forward_aggregates_cached` callers (mirroring 4 concurrent backfills' finalize
+    """TC-4: 4 concurrent `forward_aggregates_ingest_cached` callers (mirroring 4 concurrent backfills' finalize
     hooks, all racing to warm/serve the SAME `(horizon, asof_key, dataset_version)` cache key — the
-    `ForwardAggregateCache` unique-constraint race `forward_aggregates_cached`'s own
+    `ForwardAggregateCache` unique-constraint race `forward_aggregates_ingest_cached`'s own
     `except Exception: session.rollback()` is designed to absorb) plus 1 direct/uncached
     `compute_forward_aggregates` caller (the 'diagnostic read' in iter-13's own trigger shape) — every
     caller returns within a bounded timeout, none left blocked, and every returned payload is byte-
@@ -290,12 +297,12 @@ def test_tc4_concurrent_callers_all_complete_within_bounded_timeout(memory_press
 
 
 # ======================================================================================================
-# ops-hardening iter-15 (UT-04 fix) tests below — concurrency-safety of `forward_aggregates_cached`'s
+# ops-hardening iter-15 (UT-04 fix) tests below — concurrency-safety of `forward_aggregates_ingest_cached`'s
 # MISS path (a DIFFERENT iteration's TC numbering than iter-14's OWN TC-3/TC-4 above; named
 # descriptively, never `test_tc1_`/`test_tc2_`, to avoid any ambiguity with iter-14's existing names).
 #
 # Root cause (measured during this iteration's development — see the dev handoff for the full write-up):
-# reading the pre-fix `forward_aggregates_cached` directly confirmed NO de-duplication existed — a MISS
+# reading the pre-fix `forward_aggregates_ingest_cached` directly confirmed NO de-duplication existed — a MISS
 # always fell straight through to `compute_forward_aggregates` with no lock/in-flight marker. On this
 # exact 60,000-row fixture shape, 5 concurrent same-key MISSes measured 5 real `compute_forward_
 # aggregates` invocations and a 9.9x wall-clock blowup vs. a single baseline call PRE-fix; POST-fix (the
@@ -355,8 +362,8 @@ def write_contention_engine(tmp_path_factory):
     return make_engine(f"sqlite:///{db_path}")
 
 
-def test_forward_aggregates_cached_dedups_concurrent_same_key_miss_to_one_compute(memory_pressure_db):
-    """TC-1 (iter-15, UT-04 fix): N=5 concurrent `forward_aggregates_cached` callers requesting the SAME
+def test_forward_aggregates_ingest_cached_dedups_concurrent_same_key_miss_to_one_compute(memory_pressure_db):
+    """TC-1 (iter-15, UT-04 fix): N=5 concurrent `forward_aggregates_ingest_cached` callers requesting the SAME
     never-yet-cached `(horizon, asof_key, dataset_version)` key invoke the underlying heavy aggregation
     body (`compute_forward_aggregates`) EXACTLY ONCE for that key (call-count instrumentation) — proving
     the single-flight de-dup holds, not just that concurrent callers happen to agree on an answer (TC-4
@@ -378,7 +385,7 @@ def test_forward_aggregates_cached_dedups_concurrent_same_key_miss_to_one_comput
 
     def _caller():
         with Session(engine) as session:
-            return forward_testing_module.forward_aggregates_cached(session, HORIZON, cfg, as_of=as_of)
+            return forward_testing_module.forward_aggregates_ingest_cached(session, HORIZON, cfg, as_of=as_of)
 
     forward_testing_module.compute_forward_aggregates = _counting
     try:
@@ -457,7 +464,7 @@ def test_compute_forward_aggregates_concurrent_write_during_read_ratio_bounded(w
     )
 
 
-def test_forward_aggregates_cached_waiter_does_not_deadlock_when_owner_raises(memory_pressure_db):
+def test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises(memory_pressure_db):
     """TC-8 (iter-15, UT-04 fix): when the OWNER of a same-key MISS's in-flight computation raises, a
     concurrent WAITING caller for that SAME key never blocks past the bounded timeout — it either raises
     its own clean, isolated error or independently recomputes and returns a byte-identical payload.
@@ -488,14 +495,14 @@ def test_forward_aggregates_cached_waiter_does_not_deadlock_when_owner_raises(me
     def _owner_call():
         with Session(engine) as session:
             try:
-                forward_testing_module.forward_aggregates_cached(session, HORIZON, cfg, as_of=as_of)
+                forward_testing_module.forward_aggregates_ingest_cached(session, HORIZON, cfg, as_of=as_of)
             except Exception as exc:  # noqa: BLE001 — captured for the assertion below, never swallowed silently
                 owner_result["error"] = exc
 
     def _waiter_call():
         with Session(engine) as session:
             try:
-                waiter_result["payload"] = forward_testing_module.forward_aggregates_cached(
+                waiter_result["payload"] = forward_testing_module.forward_aggregates_ingest_cached(
                     session, HORIZON, cfg, as_of=as_of
                 )
             except Exception as exc:  # noqa: BLE001
diff --git a/apps/frontend/app/backtest/page.tsx b/apps/frontend/app/backtest/page.tsx
index b917b6ba..fb133c95 100644
--- a/apps/frontend/app/backtest/page.tsx
+++ b/apps/frontend/app/backtest/page.tsx
@@ -1,7 +1,7 @@
 "use client";
 
 import { useEffect, useState } from "react";
-import { AlertTriangle, Clock, FlaskConical, History, ShieldAlert } from "lucide-react";
+import { AlertTriangle, Clock, FlaskConical, History, Loader2, ShieldAlert } from "lucide-react";
 
 import { useAsOf } from "@/components/asof-provider";
 import { EmptyState } from "@/components/empty-state";
@@ -15,7 +15,7 @@ import { shouldShowWarming, WarmingState } from "@/components/warming-state";
 import { Badge } from "@/components/ui/badge";
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
 import { TermInfo } from "@/components/ui/term-info";
-import { formatIsoDate } from "@/lib/dates";
+import { formatIsoDate, formatIsoDateTime } from "@/lib/dates";
 import { cn } from "@/lib/utils";
 import {
   fetchBacktest,
@@ -227,14 +227,60 @@ function BacktestResults({
       />
       {/* The expanding-window forward-tested evidence aggregate (J-09/J-10/J-16/J-28), relocated off the
           retired System Health. Placed at the VERY BOTTOM (after the leadership lists) so the J-21 order
-          — scorecard → Return Attribution → leadership lists — is preserved; it is the single home now. */}
-      {evidence ? (
-        <EvidenceAggregateSection evidence={evidence} asofDate={backtest.asof_date} />
+          — scorecard → Return Attribution → leadership lists — is preserved; it is the single home now.
+          ops-hardening iter-16 (J-08): the evidence panel never blocks on a cold recompute — the served
+          `evidence_status` (computed server-side, never derived here) honestly discloses whether this is
+          the current version (`ready`, unchanged from before), a labeled last-good prior version while a
+          newer one warms (`refreshing`), or a never-warmed store (`not_yet_computed`). */}
+      {backtest.evidence_status === "not_yet_computed" ? (
+        <EmptyState
+          icon={FlaskConical}
+          title="Backtest evidence not yet computed"
+          description="Backtest evidence not yet computed — run an ingest to populate the forward-tested evidence for this date. No numbers are fabricated in the meantime."
+        />
+      ) : evidence ? (
+        <>
+          {backtest.evidence_status === "refreshing" ? (
+            <RefreshingEvidenceBanner generatedAt={backtest.evidence_generated_at} />
+          ) : null}
+          <EvidenceAggregateSection evidence={evidence} asofDate={backtest.asof_date} />
+        </>
       ) : null}
     </div>
   );
 }
 
+// --- Refreshing-evidence disclosure (ops-hardening iter-16, J-08): a small, calm, factual banner shown
+// ABOVE the still-fully-populated evidence section while the newer dataset version's evidence is not yet
+// complete. The copy states ONLY what the resolver actually knows (the stamp changed; the new version is
+// incomplete; this is the last complete version and when it was generated) — it must never assert that a
+// warm is currently in flight (a stamp bump from any new ScannerRun/ForwardReturn row leaves this state
+// standing with no warm running) nor promise an automatic update (this page refetches only on mount / an
+// as-of change / a readiness transition — there is no poll; see the effect deps in BacktestPage). Borrows the
+// Card + Loader2 warn-toned LOOK already established by WarmingState/SurvivorshipBanner on this same page
+// — but this is a DISTINCT, request-scoped disclosure (the served evidence's own status) and must NOT
+// wire to useReadiness() (that hook is the boot-time warm-up concept, unrelated to this per-request state).
+function RefreshingEvidenceBanner({ generatedAt }: { generatedAt: string | null }) {
+  return (
+    <Card
+      className="flex items-start gap-3 border-warn bg-surface p-4 text-sm"
+      data-testid="evidence-refreshing"
+    >
+      <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-warn" aria-hidden />
+      <div className="space-y-1">
+        <p className="font-medium text-warn">Refreshing — showing the last complete evidence</p>
+        <p className="text-text-muted">
+          The dataset has changed since this evidence was generated, and the newer version is not
+          complete yet. The forward-tested evidence below is the last complete version, generated{" "}
+          <span className="num">{formatIsoDateTime(generatedAt)}</span> — no partial or fabricated
+          figures are shown in the meantime. Reload this page after the next ingest finishes to pick up
+          the new version.
+        </p>
+      </div>
+    </Card>
+  );
+}
+
 // --- As-of scan summary header (regime + candidate counts only; the leadership lists moved below) -
 function AsOfScanSummary({ dashboard }: { dashboard: DashboardResponse | null }) {
   if (dashboard === null) {
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 54502c15..3c5bd01d 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -1086,6 +1086,16 @@ export interface BacktestResponse {
   // config horizon), all in this one payload so the client-side horizon selector needs no refetch. Each
   // entry is scoped to the EXPANDING WINDOW of snapshots dated <= `asof_date` (relocated off System Health).
   evidence_by_horizon: Record<number, EvidenceAggregate>;
+  // ops-hardening iter-16 (J-08): the evidence's own serving status — computed ONCE server-side by the
+  // read-only resolver, never derived here. "ready" = the served version is the current dataset stamp;
+  // "refreshing" = a newer version is still warming and this is the last COMPLETE prior version (labeled
+  // with its own `evidence_generated_at`); "not_yet_computed" = no complete version has ever existed for
+  // this date (`evidence_by_horizon` is then `{}`). The historical (`is_latest === false`) path still
+  // reports "ready" once its existing lazy compute finishes (unchanged behavior).
+  evidence_status: "ready" | "refreshing" | "not_yet_computed";
+  // The served version's generation timestamp (ISO 8601 UTC datetime); null only when
+  // evidence_status === "not_yet_computed".
+  evidence_generated_at: string | null;
 }
 
 /** Canonical per-date forward-test scorecard source: GET /api/backtest?as_of=. Throws on non-200 so
diff --git a/apps/backend/tests/test_forward_testing_serving_split.py b/apps/backend/tests/test_forward_testing_serving_split.py
new file mode 100644
index 00000000..f97214b5
--- /dev/null
+++ b/apps/backend/tests/test_forward_testing_serving_split.py
@@ -0,0 +1,448 @@
+"""ops-hardening iter-16 (J-08) — the forward-aggregate compute-vs-serve split.
+
+The former single `forward_aggregates_cached` (ops-hardening iter-5, J-06) split into two roles:
+
+  - `forward_aggregates_ingest_cached` — INGEST-ONLY compute-and-persist, the SOLE remaining caller of
+    `compute_forward_aggregates`. Its single-flight guard is UNCHANGED by the split and is exercised by
+    `test_forward_testing_concurrency.py`'s renamed tests (TC-17: the guard still holds post-split).
+  - `resolved_forward_aggregate_evidence` — READ-ONLY serving, structurally incapable of calling
+    `compute_forward_aggregates` under any circumstance. Exercised here.
+
+This file proves:
+
+  - completeness/cutover correctness (TC-3/4/5/18): a partial new-version warm never leaks a mixed row
+    set; the read always serves ONE complete version's rows, never mixed; pruning only fires once the
+    new version's configured-horizon set is complete; the completeness query is `asof_key`-filtered.
+  - zero-compute correctness (TC-1/2/6/7/8): the read-only resolver AND the two request-serving entry
+    points (`app.api.backtest.backtest`, `app.mcp.tools.query_backtest`, called directly as plain
+    functions — no TestClient/`loaded_engine` app boot, per this session's host-guard-confined/targeted-
+    tests-only constraint) never invoke `compute_forward_aggregates`, in every serving state.
+  - byte-identity (TC-9, AG-3): a `ready` response's payload equals a direct fresh
+    `compute_forward_aggregates` call for the same inputs.
+  - the historical (`is_latest == False`) carve-out is unaffected (TC-13).
+
+All fixtures here are small, hand-built SQLite engines (a handful of rows) — never the ~80-minute
+`loaded_engine` seed+warm fixture (out of scope for this session; see docs/handoffs/goal-ops-hardening-
+iter-16-dev.md).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine.forward_testing import (
+    compute_forward_aggregates,
+    forward_aggregates_ingest_cached,
+    resolved_forward_aggregate_evidence,
+)
+from app.models import DailyPrice, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
+
+HORIZONS = load_config().walk_forward.horizons  # [1, 5, 10, 20, 60] today — read from config, never hard-coded
+
+
+def _utc() -> datetime:
+    return datetime.now(timezone.utc)
+
+
+def _add_run(session: Session, asof: date, regime_label: str = "Risk-on") -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY", regime_score=50.0,
+        regime_label=regime_label, regime_components_json="[]", new_high_low_json="{}",
+        candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _add_result(session: Session, run_id: int, ticker: str, rank: int = 1) -> None:
+    session.add(ScannerResult(
+        run_id=run_id, ticker=ticker, name=ticker, sector="Technology", leadership_score=50.0,
+        leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
+        risk_bucket="C", setup_status="Actionable", rank=rank, record_json="{}", is_vcp=False,
+        is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
+    ))
+
+
+def _add_fr_every_horizon(session: Session, run_id: int, asof: date, symbol: str, ret: float = 0.05) -> None:
+    for h in HORIZONS:
+        session.add(ForwardReturn(
+            run_id=run_id, symbol=symbol, horizon=h, asof_date=asof, entry_close=100.0,
+            measured_date=asof, realized_return=ret,
+        ))
+
+
+@pytest.fixture()
+def evidence_engine(tmp_path):
+    """ONE run (`asof`) with a stored forward return at EVERY configured horizon for ticker "AAA" — a
+    small, fast fixture (not `loaded_engine`) sufficient to warm/serve one `ForwardAggregateCache`
+    identity under test."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'evidence.db'}")
+    create_db_and_tables(engine)
+    asof = date(2025, 1, 10)
+    with Session(engine) as session:
+        run = _add_run(session, asof)
+        _add_result(session, run.id, "AAA")
+        _add_fr_every_horizon(session, run.id, asof, "AAA")
+        session.commit()
+    return engine, asof
+
+
+# ======================================================================================================
+# resolved_forward_aggregate_evidence — completeness / cutover / never-computed / byte-identity / TC-18
+# ======================================================================================================
+def test_evidence_not_yet_computed_before_any_warm(evidence_engine, monkeypatch):
+    """TC-6: a store where no forward-aggregate warm has EVER completed for any version at this
+    `asof_key` — the resolver returns the honest empty state (never a fabricated aggregate) with ZERO
+    `compute_forward_aggregates` invocations."""
+    import app.engine.forward_testing as ft_module
+
+    engine, asof = evidence_engine
+    cfg = load_config()
+    call_count = {"n": 0}
+    real = ft_module.compute_forward_aggregates
+
+    def _counting(*a, **kw):
+        call_count["n"] += 1
+        return real(*a, **kw)
+
+    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
+    with Session(engine) as session:
+        evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
+
+    assert evidence == {
+        "evidence_status": "not_yet_computed", "evidence_generated_at": None, "evidence_by_horizon": {},
+    }
+    assert call_count["n"] == 0
+
+
+def test_evidence_ready_after_full_warm_is_byte_identical_and_zero_compute(evidence_engine, monkeypatch):
+    """TC-1/TC-9: after the ingest warm covers every configured horizon, the resolver reports `ready`
+    with a payload byte-identical to a direct fresh `compute_forward_aggregates` call for every horizon,
+    and 10 repeated resolver calls invoke `compute_forward_aggregates` ZERO times."""
+    import app.engine.forward_testing as ft_module
+
+    engine, asof = evidence_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+        direct = {h: compute_forward_aggregates(session, h, cfg, as_of=asof) for h in HORIZONS}
+
+    call_count = {"n": 0}
+    real = ft_module.compute_forward_aggregates
+
+    def _counting(*a, **kw):
+        call_count["n"] += 1
+        return real(*a, **kw)
+
+    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
+    results = []
+    for _ in range(10):
+        with Session(engine) as session:
+            results.append(resolved_forward_aggregate_evidence(session, asof, cfg))
+
+    assert call_count["n"] == 0, f"expected 0 compute calls across 10 reads; got {call_count['n']}"
+    for evidence in results:
+        assert evidence["evidence_status"] == "ready"
+        assert evidence["evidence_generated_at"] is not None
+        assert evidence["evidence_by_horizon"] == direct
+
+
+def test_evidence_refreshing_serves_prior_complete_version_never_mixed(evidence_engine):
+    """TC-3/TC-4: with V1 complete and V2's warm only 2-of-5 horizons done (a test-injected partial-warm
+    state), the resolver serves V1's full row set byte-identically, labeled `refreshing` with V1's OWN
+    generation timestamp — never a response mixing V1 and V2 horizon payloads."""
+    engine, asof = evidence_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+        v1_rows = {
+            row.horizon: (row.payload_json, row.created_at)
+            for row in session.exec(
+                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == asof.isoformat())
+            ).all()
+        }
+        assert set(v1_rows) == set(HORIZONS)
+
+        # bump the GLOBAL dataset stamp via a genuinely new run+forward-returns dated AFTER `asof` (so it
+        # never enters this asof_key's own expanding-window pool — only the cache identity/version shifts).
+        run2 = _add_run(session, date(2025, 6, 1), "Risk-off")
+        _add_result(session, run2.id, "BBB")
+        _add_fr_every_horizon(session, run2.id, date(2025, 6, 1), "BBB", ret=0.10)
+        session.commit()
+
+        # warm only 2-of-5 horizons at the NEW version for the ORIGINAL asof_key (mirrors an ingest
+        # finalize warm loop caught mid-flight).
+        partial = HORIZONS[:2]
+        for h in partial:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+        rows_now = session.exec(
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == asof.isoformat())
+        ).all()
+        by_version: dict[str, set[int]] = {}
+        for row in rows_now:
+            by_version.setdefault(row.dataset_version, set()).add(row.horizon)
+        # V1's full row set must survive (the cutover has not fired — V2 is not yet complete).
+        assert set(HORIZONS) in by_version.values(), "V1's complete row set was pruned before V2 completed"
+
+        evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
+
+    assert evidence["evidence_status"] == "refreshing"
+    assert set(evidence["evidence_by_horizon"]) == set(HORIZONS)
+    for h in HORIZONS:
+        assert evidence["evidence_by_horizon"][h] == json.loads(v1_rows[h][0]), (
+            f"horizon {h} did not come from V1 — a response mixed two dataset_versions"
+        )
+    expected_generated_at = max(created_at for _payload, created_at in v1_rows.values()).isoformat()
+    assert evidence["evidence_generated_at"] == expected_generated_at
+
+
+def test_evidence_cutover_prunes_old_version_once_new_version_completes(evidence_engine):
+    """TC-5: once V2's warm covers every configured horizon, the resolver flips to `ready` at V2 and
+    V1's now-superseded rows for this `asof_key` are ALL pruned (0 remain for the old `dataset_version`)."""
+    engine, asof = evidence_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+        v1_version = session.exec(
+            select(ForwardAggregateCache.dataset_version)
+            .where(ForwardAggregateCache.asof_key == asof.isoformat())
+        ).first()
+
+        run2 = _add_run(session, date(2025, 6, 1), "Risk-off")
+        _add_result(session, run2.id, "BBB")
+        _add_fr_every_horizon(session, run2.id, date(2025, 6, 1), "BBB", ret=0.10)
+        session.commit()
+
+        for h in HORIZONS:  # warm EVERY configured horizon at the new version -> completes it
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+        evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
+        remaining_old = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.asof_key == asof.isoformat(),
+                ForwardAggregateCache.dataset_version == v1_version,
+            )
+        ).all()
+
+    assert evidence["evidence_status"] == "ready"
+    assert remaining_old == [], "the superseded version's rows must be pruned once the new version completes"
+
+
+def test_completeness_query_is_filtered_by_asof_key(evidence_engine):
+    """TC-18: the completeness-lookup query `resolved_forward_aggregate_evidence` issues against
+    `forward_aggregate_cache` is filtered by the requested `asof_key` — captured via SQLAlchemy's own
+    `before_cursor_execute` event (the standard, non-invasive way to inspect the real SQL a call issues;
+    TC-18 itself sanctions a "query plan ... assertion"), never an unfiltered scan of the whole table.
+    Seeded with 50 OTHER historical identities' worth of rows so an unfiltered scan would be detectable."""
+    engine, asof = evidence_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        for i in range(50):
+            session.add(ForwardAggregateCache(
+                horizon=HORIZONS[0], asof_key=f"1999-01-{(i % 28) + 1:02d}",
+                dataset_version=f"other-{i}", payload_json="{}", created_at=_utc(),
+            ))
+        session.commit()
+
+        total_rows = session.exec(select(ForwardAggregateCache)).all()
+        assert len(total_rows) == len(HORIZONS) + 50  # sanity: the seeded "noise" is really there
+
+        captured: list[str] = []
+
+        def _capture(conn, cursor, statement, parameters, context, executemany):
+            captured.append(statement)
+
+        event.listen(engine, "before_cursor_execute", _capture)
+        try:
+            evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture)
+
+    assert evidence["evidence_status"] == "ready"
+    cache_selects = [
+        stmt for stmt in captured
+        if "forward_aggregate_cache" in stmt.lower() and stmt.strip().lower().startswith("select")
+    ]
+    assert cache_selects, "expected at least one SELECT against forward_aggregate_cache"
+    assert all("asof_key" in stmt.lower() for stmt in cache_selects), (
+        f"completeness query is not asof_key-filtered: {cache_selects}"
+    )
+
+
+# ======================================================================================================
+# Request-serving entry points (app.api.backtest.backtest, app.mcp.tools.query_backtest) — called
+# directly as plain functions (no TestClient/`loaded_engine` app boot) to prove the WIRING: the
+# `is_latest` branch reaches ONLY the read-only resolver, never `forward_aggregates_ingest_cached` (and
+# therefore never `compute_forward_aggregates`), in every serving state.
+# ======================================================================================================
+@pytest.fixture()
+def endpoint_engine(evidence_engine):
+    """`evidence_engine` plus ONE `DailyPrice` bar — `resolved_run`'s `latest_data_date` check needs at
+    least one bar to exist at all (`test_backtest_503_when_no_price_data` proves the 503 path with zero);
+    `run_scan`'s existing-row fast path means no OTHER price data is needed since the run already exists."""
+    engine, asof = evidence_engine
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+        ))
+        session.commit()
+    return engine, asof
+
+
+def test_backtest_route_is_latest_never_reaches_ingest_or_compute(endpoint_engine, monkeypatch):
+    """TC-1/TC-8 (endpoint layer): for the LATEST view, `GET /api/backtest`'s route function calls ONLY
+    the read-only resolver — it never calls `forward_aggregates_ingest_cached` (and therefore never
+    `compute_forward_aggregates`), structurally, across 10 repeated `ready`-state requests."""
+    import app.api.backtest as backtest_module
+
+    engine, asof = endpoint_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+    def _boom(*a, **kw):
+        raise AssertionError("the is_latest read path must never call the ingest/compute function")
+
+    monkeypatch.setattr(backtest_module, "forward_aggregates_ingest_cached", _boom)
+    responses = []
+    for _ in range(10):
+        with Session(engine) as session:
+            responses.append(backtest_module.backtest(as_of=None, session=session))
+
+    assert all(r["is_latest"] is True for r in responses)
+    assert all(r["evidence_status"] == "ready" for r in responses)
+    assert all(r["evidence_generated_at"] for r in responses)
+    first = responses[0]["evidence_by_horizon"]
+    assert all(r["evidence_by_horizon"] == first for r in responses[1:])
+    assert set(first) == set(HORIZONS)
+
+
+def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine, monkeypatch):
+    """TC-6/TC-8 (endpoint layer): a never-warmed store still answers (no exception, no fabricated
+    evidence) with the honest empty state — and never calls the ingest/compute function."""
+    import app.api.backtest as backtest_module
+
+    engine, asof = endpoint_engine
+
+    def _boom(*a, **kw):
+        raise AssertionError("the is_latest read path must never call the ingest/compute function")
+
+    monkeypatch.setattr(backtest_module, "forward_aggregates_ingest_cached", _boom)
+    with Session(engine) as session:
+        result = backtest_module.backtest(as_of=None, session=session)
+
+    assert result["is_latest"] is True
+    assert result["evidence_status"] == "not_yet_computed"
+    assert result["evidence_by_horizon"] == {}
+    assert result["evidence_generated_at"] is None
+
+
+def test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute(endpoint_engine, monkeypatch):
+    """TC-2/TC-7 (MCP layer): mirrors the endpoint-layer proof above for the MCP `query_backtest` tool —
+    the LATEST view never calls `forward_aggregates_ingest_cached`, across both the `ready` state (warmed
+    first) and repeated calls."""
+    import app.mcp.tools as tools_module
+
+    engine, asof = endpoint_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+    def _boom(*a, **kw):
+        raise AssertionError("the is_latest read path must never call the ingest/compute function")
+
+    monkeypatch.setattr(tools_module, "forward_aggregates_ingest_cached", _boom)
+    responses = []
+    for _ in range(10):
+        with Session(engine) as session:
+            responses.append(tools_module.query_backtest(session, asof=None))
+
+    assert all(r["is_latest"] is True for r in responses)
+    assert all(r["evidence_status"] == "ready" for r in responses)
+    first = responses[0]["evidence_by_horizon"]
+    assert all(r["evidence_by_horizon"] == first for r in responses[1:])
+
+
+def test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint(endpoint_engine, monkeypatch):
+    """TC-7: the MCP tool's never-warmed shape mirrors the endpoint's (same `evidence_status` /
+    `evidence_by_horizon` / `evidence_generated_at`), with zero `compute_forward_aggregates` calls."""
+    import app.mcp.tools as tools_module
+
+    engine, asof = endpoint_engine
+
... [diff_bound] apps/backend/tests/test_forward_testing_serving_split.py: 54 more diff lines omitted — Read the file for full detail
```
