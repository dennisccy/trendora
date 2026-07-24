# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index 5f57a527..f90f1573 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -20,14 +20,24 @@ Backtest) under the single global as-of control; it recomputes no return/score/b
 `forward_returns` exactly as System Health did — now filtered to <= D.
 
 ops-hardening iter-16 (J-08): for the LATEST view (`is_latest == True`) this endpoint NEVER triggers a
-forward-aggregate compute on the request — `evidence_by_horizon` (plus the new `evidence_status` /
+forward-aggregate compute on the request — `evidence_by_horizon` (plus `evidence_status` /
 `evidence_generated_at`) comes ONLY from `resolved_forward_aggregate_evidence`, a pure reader that is
 structurally incapable of calling `compute_forward_aggregates`. A HISTORICAL (`is_latest == False`)
 `?as_of=` request keeps its pre-existing lazy create-once-and-cache behavior UNCHANGED (an explicit,
-logged interpretation call — see the iter-16 dev handoff): this endpoint first ensures every configured
+logged interpretation call — see the iter-16 dev handoff): this endpoint resolves first, and only when
+that read is not already `"ready"` (audit B5 — never unconditionally) does it ensure every configured
 horizon is cached for that date (computing any still-missing one via `forward_aggregates_ingest_cached`,
-exactly as before iter-16), then reads the result back through the SAME resolver, so both branches share
-one code path for building the response's evidence fields.
+exactly as before iter-16) and re-resolve, so both branches still share ONE code path for building the
+response's evidence fields.
+
+ops-hardening iter-17 (audit B1): the resolver's OWN fallback now crosses `asof_key` boundaries — when
+the resolved as-of has never had a complete forward-aggregate version of its own (the common shape right
+after a new latest trading day lands and its ingest-finalize warm has not yet completed), it serves the
+most recent OLDER as-of's complete evidence, labeled `"refreshing"` with the NEW `evidence_asof` field
+disclosing WHICH as-of's evidence is actually being shown (never mixed with a newer, incomplete version —
+AG-5 preserved: the fallback never serves a row dated after the request). `evidence_asof` equals the
+resolved `asof_date` itself when `evidence_status == "ready"`, an older date when `"refreshing"` crosses
+an as-of boundary, and `null` when `"not_yet_computed"`.
 
 It serves the per-date SCORECARD + the as-of-scoped evidence aggregate. Regime / sector / theme / stock
 values stay single-sourced on their own endpoints (`/api/dashboard`, `/api/sectors`, `/api/themes`,
@@ -72,23 +82,33 @@ def backtest(
     card = compute_run_scorecard(session, run, cfg)  # SINGLE canonical per-date scorecard (reads stored)
     # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
     is_latest = run.asof_date == _latest_stored_run_date(session)
-    # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
-    # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
-    # for this date (a no-op for an already-warmed date). For the LATEST view this loop never runs, so
-    # this request path never reaches `forward_aggregates_ingest_cached` — let alone
-    # `compute_forward_aggregates` — under any circumstance (J-08's zero-compute-on-request guarantee).
-    if not is_latest:
-        for h in cfg.walk_forward.horizons:
-            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
     # iter-17 (J-09/J-10) + iter-16 (J-08): the as-of-scoped forward-tested evidence aggregate, ALL
     # configured horizons resolved together in ONE call (never a per-horizon-independent read — the read
     # path can otherwise observe a mixed-dataset_version row set, see the resolver's own docstring) plus
-    # the honest `evidence_status` / `evidence_generated_at` disclosure.
+    # the honest `evidence_status` / `evidence_generated_at` / `evidence_asof` disclosure.
     evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+    # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
+    # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
+    # for this date, then re-resolve. For the LATEST view this never runs, so this request path never
+    # reaches `forward_aggregates_ingest_cached` — let alone `compute_forward_aggregates` — under any
+    # circumstance (J-08's zero-compute-on-request guarantee).
+    #
+    # iter-17 (audit B5): gated on the resolver's OWN first read rather than unconditional — on an
+    # already-warmed historical date (the common repeat-view case for the Backtest/Time-Machine
+    # workspace) the resolver above already found `evidence_status == "ready"`, so the ensure loop below
+    # is skipped entirely, avoiding a redundant per-horizon cache-hit read+deserialize immediately
+    # followed by the SAME resolver re-reading and re-parsing those same rows a second time. Byte-
+    # identical either way (still one producer, one serving read): a cold historical date still ensures
+    # every horizon is cached (computing any still-missing one) and re-resolves once, exactly as before.
+    if not is_latest and evidence["evidence_status"] != "ready":
+        for h in cfg.walk_forward.horizons:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
+        evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
     return {
         **card,
         "is_latest": is_latest,
         "evidence_by_horizon": evidence["evidence_by_horizon"],
         "evidence_status": evidence["evidence_status"],
         "evidence_generated_at": evidence["evidence_generated_at"],
+        "evidence_asof": evidence["evidence_asof"],
     }
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index dd90d47a..03564121 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -1160,38 +1160,76 @@ def forward_aggregates_ingest_cached(
             event.set()
 
 
+def _utc_isoformat(value: datetime) -> str:
+    """iter-17 (audit B3): `evidence_generated_at` is contracted as an ISO-8601 UTC datetime but was
+    serialized via a naive `.isoformat()` (no `Z`/offset) because SQLite reads a stored timestamp back
+    without tzinfo even though it is always WRITTEN as `datetime.now(timezone.utc)`. Attaching
+    `timezone.utc` to an already-naive value (never converting a genuinely tz-aware one) restores the
+    missing designator without touching how any OTHER timestamp in this codebase is stored or
+    serialized — scoped to this one young field, per the audit's own explicit narrowing (fixing the
+    naive-UTC convention everywhere would be a cross-cutting change, not a surgical one)."""
+    return (value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)).isoformat()
+
+
 def resolved_forward_aggregate_evidence(
     session: Session, as_of: date_cls, config: Optional[Config] = None,
 ) -> dict:
-    """The READ-ONLY serving path (ops-hardening iter-16, J-08) — the ONLY code `GET /api/backtest` and
-    the MCP `query_backtest` tool call for their `is_latest == True` view. Structurally incapable of
-    calling `compute_forward_aggregates` under ANY circumstance, including a would-be lock-wait timeout:
-    there is no compute-fallback branch here at all (that fallback stays on `forward_aggregates_ingest_
-    cached` only, scoped to the producer-vs-producer ingest race, never reachable from a request).
+    """The READ-ONLY serving path (ops-hardening iter-16, J-08; widened iter-17, audit B1) — the ONLY
+    code `GET /api/backtest` and the MCP `query_backtest` tool call for their `is_latest == True` view.
+    Structurally incapable of calling `compute_forward_aggregates` under ANY circumstance, including a
+    would-be lock-wait timeout: there is no compute-fallback branch here at all (that fallback stays on
+    `forward_aggregates_ingest_cached` only, scoped to the producer-vs-producer ingest race, never
+    reachable from a request).
 
     Resolves, for `as_of`, the latest `dataset_version` whose stored rows cover EVERY horizon in
     `config.walk_forward.horizons` ("complete") for this `asof_key` — never a per-horizon-independent
     read (the bug this closes: a naive "latest row per horizon, ignoring version" read can already serve
     a MIXED-version payload today — confirmed live, the non-latest `asof_key='2026-07-17'` is split
-    across two `dataset_version` stamps across its 5 rows). Returns
-    `{"evidence_status", "evidence_generated_at", "evidence_by_horizon"}`:
+    across two `dataset_version` stamps across its 5 rows). Returns `{"evidence_status",
+    "evidence_generated_at", "evidence_by_horizon", "evidence_asof"}`:
 
       - `"ready"` — the complete version found IS the current global `_dataset_version` stamp; serves
         it, keyed by horizon (int), byte-identical to a fresh `compute_forward_aggregates` call.
-      - `"refreshing"` — the current stamp's row set is not yet complete (an ingest warm is mid-flight),
-        but a PRIOR complete version's full row set survives (the iter-16 cutover-pruning contract keeps
-        it until the new version's own set lands) — serves that older version's rows, ALL from the SAME
-        version (never mixed with the incomplete new one), labeled with that version's OWN
-        `created_at` (the max across its horizon rows).
-      - `"not_yet_computed"` — no complete version has EVER existed for this `asof_key`:
-        `evidence_by_horizon = {}`, `evidence_generated_at = None`. Still HTTP 200 at the caller (an
-        honest empty state) — never a synchronous compute, never 500/503.
-
-    The completeness-lookup query is filtered by `asof_key` ALONE (never an unfiltered scan of the whole
-    `forward_aggregate_cache` table — AG-8 spirit, TC-18): it touches only the handful of rows already
-    belonging to this ONE identity, regardless of how many other historical `asof_key`s the table has
-    accumulated over the session. The result set is inherently small (at most ~2 `dataset_version`s'
-    worth of rows per identity under the cutover contract above), so a plain `.all()` needs no streaming.
+        `evidence_asof` equals `as_of` itself.
+      - `"refreshing"` — the current stamp's row set for the resolved identity is not yet complete, but
+        a last-good complete version survives at or before `as_of` — serves that version's rows, ALL
+        from the SAME version (never mixed), labeled with that version's OWN `created_at` (the max
+        across its horizon rows). Two sub-cases, both legitimate:
+          (a) SAME `asof_key`, a PRIOR `dataset_version` (the iter-16 cutover-pruning contract keeps a
+              complete prior version's rows until the new version's own set lands) — `evidence_asof`
+              equals `as_of` (the served evidence genuinely IS for this date, just from an older compute
+              of it).
+          (b) iter-17 (audit B1): THIS `asof_key` has NEVER had a complete version of its own (0 rows,
+              or an in-flight partial warm only) — widen the search to STRICTLY OLDER `asof_key`s (never
+              a later one — AG-5 no-lookahead) and serve the most recent one that DOES have a complete
+              version; `evidence_asof` is that OLDER date. This is the common single-latest-date
+              backfill shape: a brand-new latest `ScannerRun` lands with zero forward-aggregate rows
+              while its ingest-finalize warm is still running (or has not yet started), and before this
+              fix the resolver fell straight through to `not_yet_computed` for the WHOLE warm window
+              instead of serving yesterday's still-good evidence (verified live by the iter-16 audit: a
+              throwaway probe showed `asof=2025-01-10 status='ready'` flip straight to
+              `asof=2025-01-13 status='not_yet_computed'` the moment the new latest run committed, with
+              zero unit or live test coverage of this shape until this iteration's TC-1/TC-4/TC-8).
+      - `"not_yet_computed"` — NO `asof_key` at or before `as_of` has EVER had a complete version (the
+        true fresh-install shape): `evidence_by_horizon = {}`, `evidence_generated_at = None`,
+        `evidence_asof = None`. Still HTTP 200 at the caller (an honest empty state) — never a
+        synchronous compute, never 500/503.
+
+    The completeness-lookup query for THIS `asof_key` is filtered by `asof_key` ALONE (never an
+    unfiltered scan of the whole `forward_aggregate_cache` table — AG-8 spirit, TC-18): it touches only
+    the handful of rows already belonging to this ONE identity. The result set is inherently small (at
+    most ~2 `dataset_version`s' worth of rows per identity under the cutover contract above), so a plain
+    `.all()` needs no streaming.
+
+    The iter-17 widened fallback below runs ONLY when that first, cheap, single-identity query comes up
+    with no complete version at all — its own query is filtered to `asof_key < :requested` (a real
+    filter, never `>=` — AG-5, and never the WHOLE table: this table is bounded by the count of as-of
+    identities ever selected across the app's lifetime, never `daily_prices` scale, consistent with
+    AG-8). Its rows are grouped by the PAIR `(asof_key, dataset_version)`, never `dataset_version`
+    alone: the version stamp is a GLOBAL fingerprint shared across every as-of identity (any new
+    `ScannerRun`/`ForwardReturn` bumps it, everywhere), so two DIFFERENT dates can carry the IDENTICAL
+    stamp — collapsing by version alone would risk mixing horizon rows from two different dates into one
+    served payload, the same class of bug the per-identity cutover contract above exists to prevent.
 
     Deferred import (not at module level): mirrors `forward_aggregates_ingest_cached`'s own established
     reason (`research.py` imports FROM this module, so a module-level import back would be circular)."""
@@ -1201,45 +1239,80 @@ def resolved_forward_aggregate_evidence(
     configured_horizons = set(cfg.walk_forward.horizons)
     asof_key = as_of.isoformat()
 
-    # asof_key-filtered read (TC-18) — bounded to this one identity's rows, never the whole table.
-    rows = session.exec(
-        select(
-            ForwardAggregateCache.horizon, ForwardAggregateCache.dataset_version,
-            ForwardAggregateCache.payload_json, ForwardAggregateCache.created_at,
-        ).where(ForwardAggregateCache.asof_key == asof_key)
-    ).all()
-
-    by_version: dict[str, dict[int, tuple[str, datetime]]] = defaultdict(dict)
-    for row_horizon, row_version, payload_json, created_at in rows:
-        by_version[row_version][row_horizon] = (payload_json, created_at)
-
-    complete = {
-        version: horizon_map
-        for version, horizon_map in by_version.items()
-        if set(horizon_map) >= configured_horizons
-    }
+    def _complete_versions(rows) -> dict[str, dict[int, tuple[str, datetime]]]:
+        by_version: dict[str, dict[int, tuple[str, datetime]]] = defaultdict(dict)
+        for row_horizon, row_version, payload_json, created_at in rows:
+            by_version[row_version][row_horizon] = (payload_json, created_at)
+        return {
+            version: horizon_map
+            for version, horizon_map in by_version.items()
+            if set(horizon_map) >= configured_horizons
+        }
 
-    def _serve(version: str, status: str) -> dict:
-        horizon_map = complete[version]
+    def _serve(horizon_map: dict[int, tuple[str, datetime]], status: str, evidence_asof: Optional[str]) -> dict:
         evidence_by_horizon = {h: json.loads(horizon_map[h][0]) for h in sorted(horizon_map)}
         generated_at = max(created_at for _payload_json, created_at in horizon_map.values())
         return {
             "evidence_status": status,
-            "evidence_generated_at": generated_at.isoformat(),
+            "evidence_generated_at": _utc_isoformat(generated_at),
             "evidence_by_horizon": evidence_by_horizon,
+            "evidence_asof": evidence_asof,
         }
 
+    # asof_key-filtered read (TC-18) — bounded to this one identity's rows, never the whole table.
+    same_key_rows = session.exec(
+        select(
+            ForwardAggregateCache.horizon, ForwardAggregateCache.dataset_version,
+            ForwardAggregateCache.payload_json, ForwardAggregateCache.created_at,
+        ).where(ForwardAggregateCache.asof_key == asof_key)
+    ).all()
+    complete = _complete_versions(same_key_rows)
+
     current_version = _dataset_version(session)
     if current_version in complete:
-        return _serve(current_version, "ready")
+        return _serve(complete[current_version], "ready", asof_key)
 
     if complete:
         # a PRIOR complete version survives the cutover (never mixed with the incomplete current one) —
-        # the "latest" surviving prior version, tie-broken by its own newest row's created_at.
+        # the "latest" surviving prior version, tie-broken by its own newest row's created_at. Still
+        # THIS asof_key's own evidence (an older compute of the SAME date), so evidence_asof is unchanged.
         stale_version = max(complete, key=lambda v: max(ca for _p, ca in complete[v].values()))
-        return _serve(stale_version, "refreshing")
+        return _serve(complete[stale_version], "refreshing", asof_key)
+
+    # iter-17 (audit B1): THIS asof_key has never had a complete version of its own (0 rows, or a
+    # partial warm only) — widen the search to STRICTLY OLDER asof_keys (never a later one, AG-5) and
+    # serve the most recent one that DOES have a complete version. See the docstring above for why
+    # grouping is keyed by (asof_key, dataset_version) rather than dataset_version alone.
+    older_rows = session.exec(
+        select(
+            ForwardAggregateCache.asof_key, ForwardAggregateCache.horizon,
+            ForwardAggregateCache.dataset_version, ForwardAggregateCache.payload_json,
+            ForwardAggregateCache.created_at,
+        ).where(ForwardAggregateCache.asof_key < asof_key)
+    ).all()
 
-    return {"evidence_status": "not_yet_computed", "evidence_generated_at": None, "evidence_by_horizon": {}}
+    by_key: dict[str, list] = defaultdict(list)
+    for row_key, row_horizon, row_version, payload_json, created_at in older_rows:
+        by_key[row_key].append((row_horizon, row_version, payload_json, created_at))
+
+    complete_by_key = {
+        row_key: versions
+        for row_key, rows in by_key.items()
+        if (versions := _complete_versions(rows))
+    }
+
+    if complete_by_key:
+        best_key = max(complete_by_key)  # ISO-8601 strings sort chronologically -- the closest older date
+        versions_at_best_key = complete_by_key[best_key]
+        best_version = max(
+            versions_at_best_key, key=lambda v: max(ca for _p, ca in versions_at_best_key[v].values())
+        )
+        return _serve(versions_at_best_key[best_version], "refreshing", best_key)
+
+    return {
+        "evidence_status": "not_yet_computed", "evidence_generated_at": None,
+        "evidence_by_horizon": {}, "evidence_asof": None,
+    }
 
 
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index b5df7072..1ef4dc35 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -192,33 +192,42 @@ def get_market_phase(
 def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     """`GET /api/backtest` — the per-date forward-test scorecard (cohort return + excess vs SPY/QQQ/
     sector + the control cohorts, each with sample size `n`) plus the as-of-scoped `evidence_by_horizon`
-    aggregate, `evidence_status`, `evidence_generated_at`, and `is_latest`. Mirrors the endpoint exactly,
-    including the read-path *create-once* population of this run's realized forward returns (INSERT-only
-    into the append-only table; a no-op once warmed) — it recomputes no score / bucket / return.
+    aggregate, `evidence_status`, `evidence_generated_at`, `evidence_asof`, and `is_latest`. Mirrors the
+    endpoint exactly, including the read-path *create-once* population of this run's realized forward
+    returns (INSERT-only into the append-only table; a no-op once warmed) — it recomputes no
+    score / bucket / return.
 
     ops-hardening iter-16 (J-08): mirrors the endpoint's own compute-vs-serve split exactly — for the
     LATEST view this tool never reaches `forward_aggregates_ingest_cached` (let alone
     `compute_forward_aggregates`); a historical `asof` keeps the pre-existing lazy create-once-and-cache
-    carve-out (TC-13), unchanged."""
+    carve-out (TC-13), unchanged.
+
+    ops-hardening iter-17 (audit B1/B5): mirrors the endpoint's widened cross-`asof_key` last-good
+    fallback (the new `evidence_asof` field discloses which as-of's evidence is actually served) and its
+    B5 gate — the historical ensure-loop below runs ONLY when the resolver's first read is not already
+    `"ready"`, never unconditionally, avoiding a redundant per-horizon cache-hit read+deserialize
+    immediately followed by the same resolver re-reading those same rows."""
     cfg = get_config()
     run = resolved_run(session, asof, cfg)
     backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
     card = compute_run_scorecard(session, run, cfg)
     is_latest = run.asof_date == _latest_stored_run_date(session)
-    if not is_latest:
+    # ops-hardening iter-5 (J-06) + iter-16 (J-08) + iter-17 (J-08/B1): served from the SAME read-only
+    # resolver `GET /api/backtest` now uses (this function's own docstring says it "mirrors the endpoint
+    # exactly" — kept true for the compute-vs-serve split AND its iter-17 widened fallback; byte-identical
+    # output, `compute_forward_aggregates` itself is unchanged).
+    evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+    if not is_latest and evidence["evidence_status"] != "ready":
         for h in cfg.walk_forward.horizons:
             forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
-    # ops-hardening iter-5 (J-06) + iter-16 (J-08): served from the SAME read-only resolver
-    # `GET /api/backtest` now uses (this function's own docstring says it "mirrors the endpoint exactly"
-    # — kept true for the compute-vs-serve split too; byte-identical output, `compute_forward_aggregates`
-    # itself is unchanged).
-    evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
+        evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
     return {
         **card,
         "is_latest": is_latest,
         "evidence_by_horizon": evidence["evidence_by_horizon"],
         "evidence_status": evidence["evidence_status"],
         "evidence_generated_at": evidence["evidence_generated_at"],
+        "evidence_asof": evidence["evidence_asof"],
     }
 
 
diff --git a/apps/backend/tests/test_api_backtest.py b/apps/backend/tests/test_api_backtest.py
index 42786e24..da09560a 100644
--- a/apps/backend/tests/test_api_backtest.py
+++ b/apps/backend/tests/test_api_backtest.py
@@ -184,12 +184,13 @@ def test_backtest_does_not_reserve_regime_or_stock_values(loaded_engine):
     """The endpoint serves the per-date scorecard + the as-of-scoped evidence aggregate ONLY — it does
     not re-serve regime/sector/theme/stock values (those stay single-sourced on their own endpoints).
     The payload's top-level keys are exactly the scorecard contract plus `evidence_by_horizon` (iter-17)
-    plus `evidence_status` / `evidence_generated_at` (iter-16, J-08)."""
+    plus `evidence_status` / `evidence_generated_at` (iter-16, J-08) plus `evidence_asof` (iter-17,
+    audit B1)."""
     with TestClient(main.app) as client:
         data = client.get("/api/backtest").json()
     assert set(data) == {
         "asof_date", "is_latest", "min_sample", "horizons", "survivorship_bias",
-        "scorecard", "evidence_by_horizon", "evidence_status", "evidence_generated_at",
+        "scorecard", "evidence_by_horizon", "evidence_status", "evidence_generated_at", "evidence_asof",
     }
 
 
diff --git a/apps/backend/tests/test_forward_testing_serving_split.py b/apps/backend/tests/test_forward_testing_serving_split.py
index f97214b5..714142a6 100644
--- a/apps/backend/tests/test_forward_testing_serving_split.py
+++ b/apps/backend/tests/test_forward_testing_serving_split.py
@@ -24,6 +24,13 @@ This file proves:
 All fixtures here are small, hand-built SQLite engines (a handful of rows) — never the ~80-minute
 `loaded_engine` seed+warm fixture (out of scope for this session; see docs/handoffs/goal-ops-hardening-
 iter-16-dev.md).
+
+iter-17 (audit B1) widens the resolver's fallback ACROSS `asof_key` boundaries: when the REQUESTED
+identity has never had a complete version of its own, the resolver now searches strictly OLDER
+identities and serves the most recent complete one, disclosing WHICH as-of via the new `evidence_asof`
+field. The new tests below (iter-17 TC-1/2/4/5/6) all use an AS-OF-ADVANCING new `ScannerRun` — a
+genuinely later date — never a historical gap date, per iter-16's own lesson that a gap date cannot
+exercise this path (the identity resolved never changes, only the dataset stamp does).
 """
 from __future__ import annotations
 
@@ -118,6 +125,7 @@ def test_evidence_not_yet_computed_before_any_warm(evidence_engine, monkeypatch)
 
     assert evidence == {
         "evidence_status": "not_yet_computed", "evidence_generated_at": None, "evidence_by_horizon": {},
+        "evidence_asof": None,
     }
     assert call_count["n"] == 0
 
@@ -154,6 +162,9 @@ def test_evidence_ready_after_full_warm_is_byte_identical_and_zero_compute(evide
         assert evidence["evidence_status"] == "ready"
         assert evidence["evidence_generated_at"] is not None
         assert evidence["evidence_by_horizon"] == direct
+        # ops-hardening iter-17 (J-08, Data Contract): evidence_asof equals the requested as-of itself
+        # when the served version IS the current stamp.
+        assert evidence["evidence_asof"] == asof.isoformat()
 
 
 def test_evidence_refreshing_serves_prior_complete_version_never_mixed(evidence_engine):
@@ -205,8 +216,16 @@ def test_evidence_refreshing_serves_prior_complete_version_never_mixed(evidence_
         assert evidence["evidence_by_horizon"][h] == json.loads(v1_rows[h][0]), (
             f"horizon {h} did not come from V1 — a response mixed two dataset_versions"
         )
-    expected_generated_at = max(created_at for _payload, created_at in v1_rows.values()).isoformat()
+    # ops-hardening iter-17 (audit B3): evidence_generated_at now carries an explicit UTC designator —
+    # attach it to the SAME raw (naive) created_at before formatting, mirroring the production fix, so
+    # this expectation does not regress to the pre-B3 naive string.
+    expected_generated_at = max(
+        created_at for _payload, created_at in v1_rows.values()
+    ).replace(tzinfo=timezone.utc).isoformat()
     assert evidence["evidence_generated_at"] == expected_generated_at
+    # ops-hardening iter-17 (J-08, Data Contract): a SAME-asof_key stale version is still THIS date's own
+    # evidence (an older compute of it, not a different date) — evidence_asof is unchanged from `asof`.
+    assert evidence["evidence_asof"] == asof.isoformat()
 
 
 def test_evidence_cutover_prunes_old_version_once_new_version_completes(evidence_engine):
@@ -287,6 +306,161 @@ def test_completeness_query_is_filtered_by_asof_key(evidence_engine):
     )
 
 
+# ======================================================================================================
+# iter-17 (audit B1, the load-bearing fix) — the cross-`asof_key` last-good fallback. All three tests
+# below use an AS-OF-ADVANCING new `ScannerRun` (a genuinely LATER date), never a historical gap date:
+# iter-16's own lesson is that a gap-date live/unit test structurally cannot exercise this path, because
+# the identity being resolved never changes — only the dataset stamp does.
+# ======================================================================================================
+def test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows(evidence_engine):
+    """iter-17 TC-1: an older `asof_key` (2025-01-10) has a COMPLETE version; a NEWER `asof_key`
+    (2025-01-13, a genuinely later `ScannerRun`) has ZERO forward-aggregate rows of any version — the
+    common single-latest-date-backfill shape, where the newest trading day lands before its
+    ingest-finalize warm has run. Resolving at the NEWER date must serve the older date's complete
+    evidence, labeled `refreshing` with `evidence_asof` set to the OLDER date — never `not_yet_computed`."""
+    engine, older_asof = evidence_engine  # 2025-01-10
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=older_asof)
+        session.commit()
+        older_rows = {
+            row.horizon: (row.payload_json, row.created_at)
+            for row in session.exec(
+                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == older_asof.isoformat())
+            ).all()
+        }
+        assert set(older_rows) == set(HORIZONS)
+
+        # a genuinely LATER run — the as-of identity itself advances, not just the dataset stamp.
+        newer_asof = date(2025, 1, 13)
+        run2 = _add_run(session, newer_asof, "Risk-off")
+        _add_result(session, run2.id, "BBB")
+        _add_fr_every_horizon(session, run2.id, newer_asof, "BBB", ret=0.10)
+        session.commit()
+
+        # sanity: the newer identity has ZERO ForwardAggregateCache rows of any version.
+        assert session.exec(
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == newer_asof.isoformat())
+        ).all() == []
+
+        evidence = resolved_forward_aggregate_evidence(session, newer_asof, cfg)
+
+    assert evidence["evidence_status"] == "refreshing"
+    assert evidence["evidence_asof"] == older_asof.isoformat()
+    assert set(evidence["evidence_by_horizon"]) == set(HORIZONS)
+    for h in HORIZONS:
+        assert evidence["evidence_by_horizon"][h] == json.loads(older_rows[h][0]), (
+            f"horizon {h} did not come from the older asof_key's own stored rows"
+        )
+
+
+def test_evidence_crosses_asof_key_boundary_picks_more_recent_of_two_older_complete_keys(evidence_engine):
+    """iter-17 TC-4: with TWO older, independently-complete `asof_key`s (2025-01-08 and 2025-01-10) and
+    the requested `asof_key` (2025-01-13) itself carrying zero rows, the served `evidence_asof` is the
+    MORE RECENT of the two (2025-01-10) — never the older one (2025-01-08), and never a response mixing
+    rows from both dates."""
+    engine, asof_1_10 = evidence_engine  # 2025-01-10
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof_1_10)
+        session.commit()
+        rows_1_10 = {
+            row.horizon: (row.payload_json, row.created_at)
+            for row in session.exec(
+                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == asof_1_10.isoformat())
+            ).all()
+        }
+
+        # a SECOND, independent older identity (2025-01-08, strictly before 2025-01-10) with its OWN
+        # complete row set, from a different cohort so its aggregate genuinely differs from 2025-01-10's.
+        asof_1_08 = date(2025, 1, 8)
+        run_08 = _add_run(session, asof_1_08, "Risk-on")
+        _add_result(session, run_08.id, "CCC")
+        _add_fr_every_horizon(session, run_08.id, asof_1_08, "CCC", ret=0.02)
+        session.commit()
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof_1_08)
+        session.commit()
+
+        # the requested identity: a genuinely later run, zero forward-aggregate rows of its own.
+        newer_asof = date(2025, 1, 13)
+        run_newer = _add_run(session, newer_asof, "Risk-off")
+        _add_result(session, run_newer.id, "DDD")
+        _add_fr_every_horizon(session, run_newer.id, newer_asof, "DDD", ret=0.10)
+        session.commit()
+
+        evidence = resolved_forward_aggregate_evidence(session, newer_asof, cfg)
+
+    assert evidence["evidence_status"] == "refreshing"
+    assert evidence["evidence_asof"] == asof_1_10.isoformat(), "must serve the MORE RECENT older key"
+    for h in HORIZONS:
+        assert evidence["evidence_by_horizon"][h] == json.loads(rows_1_10[h][0]), (
+            f"horizon {h} leaked a row from the OTHER older asof_key (2025-01-08) — versions mixed across dates"
+        )
+
+
+def test_evidence_fallback_never_reads_a_row_dated_after_the_requested_as_of(evidence_engine):
+    """iter-17 TC-5 (AG-5 no-lookahead): once the fallback crosses to older `asof_key`s, it never reads
+    or serves a row dated AFTER the requested as-of — verified via the same `before_cursor_execute`
+    SQL-inspection technique `test_completeness_query_is_filtered_by_asof_key` (TC-18) already uses.
+    Seeded with a LATER-dated, fully-complete identity that must never be selected for an earlier
+    request; the outcome assertion (`evidence_asof` resolving to the OLDER date, never the future one) is
+    the strongest proof — if the future row had been read and let into the tie-break, it would win
+    (its `asof_key` string sorts higher), so a wrong `evidence_asof` would itself expose a lookahead bug."""
+    engine, older_asof = evidence_engine  # 2025-01-10
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=older_asof)
+        session.commit()
+
+        # a LATER-dated, fully complete identity that must NEVER be read for the earlier request below.
+        future_asof = date(2025, 6, 1)
+        run_future = _add_run(session, future_asof, "Risk-off")
+        _add_result(session, run_future.id, "EEE")
+        _add_fr_every_horizon(session, run_future.id, future_asof, "EEE", ret=0.20)
+        session.commit()
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=future_asof)
+        session.commit()
+
+        # the actual request: a genuinely new latest run, strictly BETWEEN older_asof and future_asof,
+        # with zero forward-aggregate rows of its own — must fall back to older_asof, never future_asof.
+        requested_asof = date(2025, 2, 1)
+        run_req = _add_run(session, requested_asof, "Risk-on")
+        _add_result(session, run_req.id, "FFF")
+        _add_fr_every_horizon(session, run_req.id, requested_asof, "FFF", ret=0.03)
+        session.commit()
+
+        captured: list[str] = []
+
+        def _capture(conn, cursor, statement, parameters, context, executemany):
+            captured.append(statement)
+
+        event.listen(engine, "before_cursor_execute", _capture)
+        try:
+            evidence = resolved_forward_aggregate_evidence(session, requested_asof, cfg)
+        finally:
+            event.remove(engine, "before_cursor_execute", _capture)
+
+    assert evidence["evidence_status"] == "refreshing"
+    assert evidence["evidence_asof"] == older_asof.isoformat(), "must serve the older key, never the future one"
+
+    cache_selects = [
+        stmt for stmt in captured
+        if "forward_aggregate_cache" in stmt.lower() and stmt.strip().lower().startswith("select")
+    ]
+    assert cache_selects, "expected at least one SELECT against forward_aggregate_cache"
+    assert not any(">" in stmt for stmt in cache_selects), (
+        f"a forward_aggregate_cache query used a >/>= comparison — possible lookahead: {cache_selects}"
+    )
+    assert any("<" in stmt for stmt in cache_selects), (
+        "expected the widened fallback's completeness query to filter with asof_key < :requested"
+    )
+
+
 # ======================================================================================================
 # Request-serving entry points (app.api.backtest.backtest, app.mcp.tools.query_backtest) — called
 # directly as plain functions (no TestClient/`loaded_engine` app boot) to prove the WIRING: the
@@ -332,6 +506,7 @@ def test_backtest_route_is_latest_never_reaches_ingest_or_compute(endpoint_engin
     assert all(r["is_latest"] is True for r in responses)
     assert all(r["evidence_status"] == "ready" for r in responses)
     assert all(r["evidence_generated_at"] for r in responses)
+    assert all(r["evidence_asof"] == asof.isoformat() for r in responses)
     first = responses[0]["evidence_by_horizon"]
     assert all(r["evidence_by_horizon"] == first for r in responses[1:])
     assert set(first) == set(HORIZONS)
@@ -355,6 +530,7 @@ def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine
     assert result["evidence_status"] == "not_yet_computed"
     assert result["evidence_by_horizon"] == {}
     assert result["evidence_generated_at"] is None
+    assert result["evidence_asof"] is None
 
 
 def test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute(endpoint_engine, monkeypatch):
@@ -381,6 +557,7 @@ def test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute(endpo
 
     assert all(r["is_latest"] is True for r in responses)
     assert all(r["evidence_status"] == "ready" for r in responses)
+    assert all(r["evidence_asof"] == asof.isoformat() for r in responses)
     first = responses[0]["evidence_by_horizon"]
     assert all(r["evidence_by_horizon"] == first for r in responses[1:])
 
@@ -403,6 +580,33 @@ def test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint(endpoint_engi
     assert result["evidence_status"] == "not_yet_computed"
     assert result["evidence_by_horizon"] == {}
     assert result["evidence_generated_at"] is None
+    assert result["evidence_asof"] is None
+
+
+def test_backtest_route_and_mcp_tool_serve_evidence_asof_identically(endpoint_engine):
+    """iter-17 TC-2: given the SAME fixture, `GET /api/backtest`'s route function and the MCP
+    `query_backtest` tool both surface `evidence_asof` — identically to each other, and equal to the
+    resolved as-of date when the served version is the current (`ready`) stamp."""
+    import app.api.backtest as backtest_module
+    import app.mcp.tools as tools_module
+
+    engine, asof = endpoint_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
+        session.commit()
+
+    with Session(engine) as session:
+        api_result = backtest_module.backtest(as_of=None, session=session)
+    with Session(engine) as session:
+        mcp_result = tools_module.query_backtest(session, asof=None)
+
+    assert api_result["evidence_status"] == "ready"
+    assert mcp_result["evidence_status"] == "ready"
+    assert api_result["evidence_asof"] == asof.isoformat()
+    assert mcp_result["evidence_asof"] == asof.isoformat()
+    assert api_result["evidence_asof"] == mcp_result["evidence_asof"]
 
 
 def test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior(endpoint_engine, monkeypatch):
@@ -445,4 +649,72 @@ def test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior(endpoin
     assert first_calls == len(HORIZONS), "expected one real compute per configured horizon on first view"
     assert call_count["n"] == first_calls, "the second (cached) view must trigger zero MORE computes"
     assert first["evidence_status"] == "ready"
+    assert first["evidence_asof"] == older_asof.isoformat()
+    assert second["evidence_by_horizon"] == first["evidence_by_horizon"]
+
+
+def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists(
+    endpoint_engine, monkeypatch
+):
+    """iter-17 TC-6 (regression guard, mirrors `test_historical_asof_keeps_pre_iter16_create_once_and_
+    cache_behavior` above): a historical (`is_latest == False`) `?as_of=` request still computes-once-
+    and-caches ITS OWN evidence on first view, and must NEVER be short-circuited by the iter-17 widened
+    fallback finding an UNRELATED older `asof_key`'s complete evidence first. `backtest.py`'s audit-B5
+    gate is `evidence_status != "ready"` — which `"refreshing"` also satisfies — deliberately NOT
+    `== "not_yet_computed"`, which would wrongly skip the ensure-loop and serve the fallback's stale,
+    wrong-date evidence instead of computing this date's own."""
+    import app.api.backtest as backtest_module
+    import app.engine.forward_testing as ft_module
+
+    engine, _latest_asof = endpoint_engine
+    cfg = load_config()
+
+    # an OLDER, fully-warmed complete identity the iter-17 widened fallback WOULD find first for any
+    # request whose own asof_key has zero forward-aggregate rows.
+    fallback_asof = date(2024, 1, 5)
+    with Session(engine) as session:
+        fallback_run = _add_run(session, fallback_asof, "Risk-on")
+        _add_result(session, fallback_run.id, "GGG")
+        _add_fr_every_horizon(session, fallback_run.id, fallback_asof, "GGG")
+        session.commit()
+        for h in HORIZONS:
+            forward_aggregates_ingest_cached(session, h, cfg, as_of=fallback_asof)
+        session.commit()
+
+    # the requested historical date: strictly AFTER fallback_asof (so the widened fallback lands on it)
+    # and strictly BEFORE the fixture's own latest date (so is_latest stays False); its own
+    # forward-aggregate cache is EMPTY, so the resolver's FIRST read must land on "refreshing" via the
+    # widened fallback to fallback_asof, never "ready", before the ensure-loop below ever runs.
+    requested_asof = date(2024, 6, 1)
+    with Session(engine) as session:
+        req_run = _add_run(session, requested_asof, "Risk-off")
+        _add_result(session, req_run.id, "HHH")
+        session.add(DailyPrice(
+            symbol="HHH", date=requested_asof, open=50.0, high=51.0, low=49.0, close=50.0, volume=1.0,
+        ))
+        session.commit()
+
+    call_count = {"n": 0}
+    real = ft_module.compute_forward_aggregates
+
+    def _counting(*a, **kw):
+        call_count["n"] += 1
+        return real(*a, **kw)
+
+    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
+    with Session(engine) as session:
+        first = backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)
+    first_calls = call_count["n"]
+    with Session(engine) as session:
+        second = backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)
+
+    assert first["is_latest"] is False
+    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon on first view"
+    assert call_count["n"] == first_calls, "the second (cached) view must trigger zero MORE computes"
+    assert first["evidence_status"] == "ready"
+    assert first["evidence_asof"] == requested_asof.isoformat(), (
+        "the historical view must serve ITS OWN freshly computed evidence, never the fallback's older date"
+    )
+    assert second["evidence_status"] == "ready"
+    assert second["evidence_asof"] == requested_asof.isoformat()
     assert second["evidence_by_horizon"] == first["evidence_by_horizon"]
diff --git a/apps/frontend/app/backtest/page.tsx b/apps/frontend/app/backtest/page.tsx
index fb133c95..d641a6e6 100644
--- a/apps/frontend/app/backtest/page.tsx
+++ b/apps/frontend/app/backtest/page.tsx
@@ -236,12 +236,15 @@ function BacktestResults({
         <EmptyState
           icon={FlaskConical}
           title="Backtest evidence not yet computed"
-          description="Backtest evidence not yet computed — run an ingest to populate the forward-tested evidence for this date. No numbers are fabricated in the meantime."
+          description="No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers it will compute this evidence — no numbers are fabricated in the meantime."
         />
       ) : evidence ? (
         <>
           {backtest.evidence_status === "refreshing" ? (
-            <RefreshingEvidenceBanner generatedAt={backtest.evidence_generated_at} />
+            <RefreshingEvidenceBanner
+              generatedAt={backtest.evidence_generated_at}
+              evidenceAsof={backtest.evidence_asof}
+            />
           ) : null}
           <EvidenceAggregateSection evidence={evidence} asofDate={backtest.asof_date} />
         </>
@@ -250,17 +253,27 @@ function BacktestResults({
   );
 }
 
-// --- Refreshing-evidence disclosure (ops-hardening iter-16, J-08): a small, calm, factual banner shown
-// ABOVE the still-fully-populated evidence section while the newer dataset version's evidence is not yet
-// complete. The copy states ONLY what the resolver actually knows (the stamp changed; the new version is
-// incomplete; this is the last complete version and when it was generated) — it must never assert that a
-// warm is currently in flight (a stamp bump from any new ScannerRun/ForwardReturn row leaves this state
-// standing with no warm running) nor promise an automatic update (this page refetches only on mount / an
-// as-of change / a readiness transition — there is no poll; see the effect deps in BacktestPage). Borrows the
+// --- Refreshing-evidence disclosure (ops-hardening iter-16, J-08; evidenceAsof added iter-17, J-08 audit
+// B1): a small, calm, factual banner shown ABOVE the still-fully-populated evidence section while the
+// newer dataset version's evidence is not yet complete. The copy states ONLY what the resolver actually
+// knows (the stamp changed; the new version is incomplete; WHICH as-of's evidence this is; and when it
+// was generated) — it must never assert that a warm is currently in flight (a stamp bump from any new
+// ScannerRun/ForwardReturn row leaves this state standing with no warm running) nor promise an automatic
+// update (this page refetches only on mount / an as-of change / a readiness transition — there is no
+// poll; see the effect deps in BacktestPage). `evidenceAsof` (iter-17) discloses WHICH as-of's evidence is
+// being shown — equal to the page's own resolved date when the resolver served an older *version* of this
+// SAME date, or a genuinely OLDER date when the fallback crossed an as-of boundary (the common shape
+// right after a new latest trading day lands and its ingest warm has not finished, audit B1). Borrows the
 // Card + Loader2 warn-toned LOOK already established by WarmingState/SurvivorshipBanner on this same page
 // — but this is a DISTINCT, request-scoped disclosure (the served evidence's own status) and must NOT
 // wire to useReadiness() (that hook is the boot-time warm-up concept, unrelated to this per-request state).
-function RefreshingEvidenceBanner({ generatedAt }: { generatedAt: string | null }) {
+function RefreshingEvidenceBanner({
+  generatedAt,
+  evidenceAsof,
+}: {
+  generatedAt: string | null;
+  evidenceAsof: string | null;
+}) {
   return (
     <Card
       className="flex items-start gap-3 border-warn bg-surface p-4 text-sm"
@@ -271,7 +284,8 @@ function RefreshingEvidenceBanner({ generatedAt }: { generatedAt: string | null
         <p className="font-medium text-warn">Refreshing — showing the last complete evidence</p>
         <p className="text-text-muted">
           The dataset has changed since this evidence was generated, and the newer version is not
-          complete yet. The forward-tested evidence below is the last complete version, generated{" "}
+          complete yet. The forward-tested evidence below is the last complete version — evidence as of{" "}
+          <span className="num">{formatIsoDate(evidenceAsof)}</span>, generated{" "}
           <span className="num">{formatIsoDateTime(generatedAt)}</span> — no partial or fabricated
           figures are shown in the meantime. Reload this page after the next ingest finishes to pick up
           the new version.
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 3c5bd01d..0e760a86 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -1096,6 +1096,12 @@ export interface BacktestResponse {
   // The served version's generation timestamp (ISO 8601 UTC datetime); null only when
   // evidence_status === "not_yet_computed".
   evidence_generated_at: string | null;
+  // ops-hardening iter-17 (J-08, audit B1): the as-of (ISO 8601 date) whose stored complete
+  // forward-aggregate version is actually being served — equal to `asof_date` when
+  // evidence_status === "ready", an OLDER date when "refreshing" crosses an as-of boundary (the
+  // common shape right after a new latest trading day lands and its ingest warm has not finished),
+  // and null only when evidence_status === "not_yet_computed".
+  evidence_asof: string | null;
 }
 
 /** Canonical per-date forward-test scorecard source: GET /api/backtest?as_of=. Throws on non-200 so
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 304 ++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |   7 +
 runs/goal-session-ops-hardening/trace/.next-step  |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |   3 +
 4 files changed, 315 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
