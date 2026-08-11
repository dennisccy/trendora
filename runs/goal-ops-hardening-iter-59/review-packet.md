# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index b92d42c8..3f78703e 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3442,9 +3442,13 @@ _FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
 # see `resolve_with_reasons`'s own comment for the full finding). It now fires from directly inside THIS
 # module's `_refresh_ingest_aggregates`, at the top of that phase's own block — no lazy import needed
 # (same module).
+# ops-hardening iter-59: "regime_lab" added — `research.compute_regime_lab`'s per-horizon build-process-
+# release isolate-and-continue site (J-07; the confirmed iter-58 crash frame,
+# `_regime_lab_members_by_horizon` retaining every horizon's pool at once). Reaches this hook via the SAME
+# lazy `from app.engine import data_manager` import `compute_factor_lab_all` already uses.
 _FAULT_INJECT_SITES = frozenset({
     "forward_aggregates", "drawdown_expectations", "backfill_worker", "factor_lab_all",
-    "coverage_membership_timeline", "market_phase",
+    "coverage_membership_timeline", "market_phase", "regime_lab",
 })
 
 
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index 093cad27..ef78fb1f 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -4358,6 +4358,30 @@ def _regime_lab_observation_set(
     return _collapse_to_episodes(members, run_position)  # first-trigger episode collapse (J-63)
 
 
+def _degrade_regime_lab_horizon(
+    h: int, labels: list[str], deciles: int,
+    by_horizon_per_label: dict[str, list[dict]], by_horizon_per_decile: dict[int, list[dict]],
+    rank_ic_by_horizon: list[dict],
+) -> None:
+    """Append an honest `status: "unavailable"` entry for horizon `h` to every by-label / by-decile /
+    rank-IC accumulator — the SAME schema a completed horizon's entry carries (`n`/`low_sample`/
+    `mean_return`/`mean_max_drawdown`[/`score_min`/`score_max`]), so no consumer needs a second shape to
+    handle (mirrors `compute_factor_lab_all`'s degraded-entry convention, research.py:1474). `n=0` and
+    `low_sample=True` are honestly true (zero usable observations this call), never fabricated; `status`
+    is the signal a consumer checks to tell this apart from a genuinely sparse-but-computed horizon."""
+    for label in labels:
+        by_horizon_per_label[label].append({
+            "horizon": h, "n": 0, "low_sample": True, "mean_return": None, "mean_max_drawdown": None,
+            "status": "unavailable",
+        })
+    for d in range(1, deciles + 1):
+        by_horizon_per_decile[d].append({
+            "horizon": h, "n": 0, "low_sample": True, "mean_return": None, "mean_max_drawdown": None,
+            "score_min": None, "score_max": None, "status": "unavailable",
+        })
+    rank_ic_by_horizon.append({"horizon": h, "rank_ic": {"value": None, "n": 0}, "status": "unavailable"})
+
+
 def compute_regime_lab(
     session: Session, config: Optional[Config] = None, *,
     view: str = VIEW_EPISODES, as_of: Optional[date_cls] = None,
@@ -4377,12 +4401,32 @@ def compute_regime_lab(
       - `rank_ic_by_horizon` — the Spearman rank-IC of the regime score vs the realized forward return, per
         horizon (the decile table's header figure; `{value, n}`, NA when n < 2 or zero rank variance).
 
-    Every figure is byte-identical to the reference aggregation over `_regime_lab_observation_set(horizon,
-    view)` (the SAME builders the samples drill-down reads — one computation path, no number recomputed). The
-    view shows ALL horizons at once (paired columns), so it takes NO `horizon` argument. `as_of` (J-32) scopes
-    the observation set to snapshots dated <= D (a pure FILTER — recomputes nothing); `as_of=None` is the
-    all-history aggregate. The payload echoes the resolved cutoff as `asof_date` (ISO) when scoped, else
-    `null`. Raises `ValueError` for an unknown view (the API pre-validates -> 422)."""
+    Every figure that completes is byte-identical to the reference aggregation over
+    `_regime_lab_observation_set(horizon, view)` (the SAME builders the samples drill-down reads — one
+    computation path, no number recomputed). The view shows ALL horizons at once (paired columns), so it
+    takes NO `horizon` argument. `as_of` (J-32) scopes the observation set to snapshots dated <= D (a pure
+    FILTER — recomputes nothing); `as_of=None` is the all-history aggregate. The payload echoes the resolved
+    cutoff as `asof_date` (ISO) when scoped, else `null`. Raises `ValueError` for an unknown view (the API
+    pre-validates -> 422).
+
+    ops-hardening iter-59 (J-07, AG-8) — bounded, isolate-and-continue per horizon: the pre-iter-59 shape
+    called `_regime_lab_members_by_horizon` ONCE for every configured horizon and retained EVERY horizon's
+    observation pool (then every horizon's post-episode-collapse set) simultaneously for the whole by-label
+    + by-decile aggregation — the same all-at-once-retention shape iter-46/49/50/51 already bounded for the
+    Factor Lab's `_all_factor_observations_by_horizon` / `compute_factor_lab_all` (the confirmed iter-58
+    crash frame: a concurrent forward-aggregate warm plus this all-horizons retention landed VmPeak exactly
+    on the declared 8192 MB ceiling with a live `MemoryError` traceback naming this function). Each horizon
+    is now built via the SAME `_regime_lab_members_by_horizon` builder called with a SINGLE-element
+    `horizons` list — its own documented byte-identity keystone guarantees that call is byte-identical to
+    that horizon's slice of the old all-horizons call — aggregated into that horizon's by-label / by-decile
+    / rank-IC rows, then released before the next horizon starts. A horizon whose build or aggregation step
+    raises under memory pressure (or any other failure) degrades ONLY that horizon to an honest
+    `status: "unavailable"` entry (mirrors `compute_factor_lab_all`'s per-(factor,horizon) isolate-and-
+    continue, including its `except Exception` pairing per the iter-50 audit B4 lesson: one entry's OTHER
+    failure must not 500 the whole response either) and the loop continues — never an uncaught exception
+    reaching `GET /api/research/regime-lab` as a 500. The whole-response `regime_lab_status: "unavailable"`
+    flag is present ONLY when at least one horizon degraded (mirrors the Factor Lab's `factors_status`
+    sibling field, research.py ~4092) — absent, never a fabricated "ok", on a clean compute."""
     cfg = config or get_config()
     wf = cfg.walk_forward
     fl = cfg.research.factor_lab
@@ -4393,65 +4437,114 @@ def compute_regime_lab(
 
     labels = list(cfg.regime.labels)
 
-    # ONE heavy read builds the per-observation pools for ALL horizons (the bounded, byte-identity-preserving
-    # keystone); the episode collapse (when the view is episodes) is a pure in-memory grouping of those SAME
-    # stored rows, computed ONCE per horizon and shared by both the by-label and by-decile groupings.
-    pools = _regime_lab_members_by_horizon(session, horizons, as_of, cfg=cfg)
-    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
-    members_by_h: dict[int, list[dict]] = {}
-    for h in horizons:
-        members = pools[h]
-        members_by_h[h] = members if view == VIEW_POOLED else _collapse_to_episodes(members, run_position)
+    # lazy import — app.engine.data_manager imports FROM this module, so a module-level import back would
+    # be circular (mirrors compute_factor_lab_all's own lazy import). Used only for the test-only
+    # `_fault_inject_memory_error` hook below (a no-op in production).
+    from app.engine import data_manager
 
-    # (a) by-label: every configured regime label emits a row even at n=0 (honest empty row — never omitted,
-    # never fabricated). The paired mean max-drawdown uses the SAME NA convention as the Factor Lab / forward
-    # scorecard (mean over only the members with a stored drawdown; None when none).
-    by_label: list[dict] = []
-    for label in labels:
-        by_horizon: list[dict] = []
-        for h in horizons:
-            label_members = [m for m in members_by_h[h] if m["regime_label"] == label]
-            returns = [m["return"] for m in label_members]
-            mdds = [m["max_drawdown"] for m in label_members if m["max_drawdown"] is not None]
-            n = len(label_members)
-            by_horizon.append({
-                "horizon": h,
-                "n": n,
-                "low_sample": n < wf.min_sample,
-                "mean_return": mean(returns) if returns else None,
-                "mean_max_drawdown": _mean_or_none(mdds),
-            })
-        by_label.append({"regime": label, "by_horizon": by_horizon})
+    # the run-ordinal index is bounded by TOTAL RUN COUNT (a lightweight two-column read over every stored
+    # `scanner_runs` row, never the heavy FR/ScannerResult tables) — shared across horizons, built once.
+    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
 
-    # (b) by-decile of the 0–100 regime score (the generic `_deciles` machinery) + the per-horizon rank-IC of
-    # the regime score vs the realized forward return.
-    decile_rows_by_h: dict[int, list[dict]] = {}
+    by_horizon_per_label: dict[str, list[dict]] = {label: [] for label in labels}
+    by_horizon_per_decile: dict[int, list[dict]] = {d: [] for d in range(1, fl.deciles + 1)}
     rank_ic_by_horizon: list[dict] = []
+    any_degraded = False
+
     for h in horizons:
-        ordered = _regime_score_ordered(members_by_h[h])
-        decile_rows_by_h[h] = _deciles(ordered, fl.deciles, wf.min_sample)
-        rank_ic_by_horizon.append({
-            "horizon": h,
-            "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
-        })
-    by_decile: list[dict] = []
-    for d in range(1, fl.deciles + 1):
-        by_horizon = []
-        for h in horizons:
-            drow = decile_rows_by_h[h][d - 1]
-            by_horizon.append({
+        # a real scheduling yield once per horizon, mirrors compute_factor_lab_all's own iter-52 per-entry
+        # yield (forces an OS-level GIL hand-off so a concurrent request gets a fair chance to be scheduled).
+        time.sleep(0)
+        try:
+            data_manager._fault_inject_memory_error("regime_lab")  # test-only; no-op in production
+            pool = _regime_lab_members_by_horizon(session, [h], as_of, cfg=cfg)[h]
+            members = pool if view == VIEW_POOLED else _collapse_to_episodes(pool, run_position)
+
+            # (a) by-label: every configured regime label emits a row even at n=0 (honest empty row — never
+            # omitted, never fabricated). The paired mean max-drawdown uses the SAME NA convention as the
+            # Factor Lab / forward scorecard (mean over only members with a stored drawdown; None when none).
+            #
+            # iter-59 REVIEW FIX (CRITICAL): this horizon's rows are built into LOCAL buffers and committed
+            # to the shared accumulators in exactly ONE place, only after the try/except succeeds (the same
+            # "compute into locals, append once" discipline `compute_factor_lab_all` follows,
+            # research.py:1409-1491). Appending straight into the shared accumulators here meant a failure
+            # raised AFTER the by-label loop but BEFORE the by-decile/rank-IC work finished (e.g. a real
+            # MemoryError inside `_deciles`/`_regime_score_ordered`) left this horizon's REAL by-label
+            # entries in place and then `_degrade_regime_lab_horizon` appended a SECOND, degraded entry for
+            # the SAME horizon — a by_horizon list with a duplicated horizon and mismatched lengths across
+            # by-label vs by-decile rows.
+            label_entries: dict[str, dict] = {}
+            for label in labels:
+                label_members = [m for m in members if m["regime_label"] == label]
+                returns = [m["return"] for m in label_members]
+                mdds = [m["max_drawdown"] for m in label_members if m["max_drawdown"] is not None]
+                n = len(label_members)
+                label_entries[label] = {
+                    "horizon": h,
+                    "n": n,
+                    "low_sample": n < wf.min_sample,
+                    "mean_return": mean(returns) if returns else None,
+                    "mean_max_drawdown": _mean_or_none(mdds),
+                }
+
+            # (b) by-decile of the 0–100 regime score (the generic `_deciles` machinery) + this horizon's
+            # rank-IC of the regime score vs the realized forward return.
+            ordered = _regime_score_ordered(members)
+            decile_rows = _deciles(ordered, fl.deciles, wf.min_sample)
+            decile_entries: dict[int, dict] = {}
+            for d in range(1, fl.deciles + 1):
+                drow = decile_rows[d - 1]
+                decile_entries[d] = {
+                    "horizon": h,
+                    "n": drow["n"],
+                    "low_sample": drow["low_sample"],
+                    "mean_return": drow["mean_return"],
+                    "mean_max_drawdown": drow["mean_max_drawdown"],
+                    # the decile's regime-score range (the `_deciles` factor bounds, re-labelled to "score").
+                    "score_min": drow["factor_min"],
+                    "score_max": drow["factor_max"],
+                }
+            rank_ic_entry = {
                 "horizon": h,
-                "n": drow["n"],
-                "low_sample": drow["low_sample"],
-                "mean_return": drow["mean_return"],
-                "mean_max_drawdown": drow["mean_max_drawdown"],
-                # the decile's regime-score range (the `_deciles` factor bounds, re-labelled to "score").
-                "score_min": drow["factor_min"],
-                "score_max": drow["factor_max"],
-            })
-        by_decile.append({"decile": d, "by_horizon": by_horizon})
+                "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
+            }
+        except MemoryError as exc:
+            logger.exception(
+                "compute_regime_lab: horizon=%s aborted under memory pressure -- isolate-and-continue "
+                "(AG-8), degrading THIS horizon honestly rather than the whole all-horizons response: %s",
+                h, exc,
+            )
+            any_degraded = True
+            _degrade_regime_lab_horizon(
+                h, labels, fl.deciles, by_horizon_per_label, by_horizon_per_decile, rank_ic_by_horizon,
+            )
+            continue
+        except Exception as exc:  # noqa: BLE001 — mirrors compute_factor_lab_all's broader catch (AG-8,
+            # iter-50 audit B4 lesson: the MemoryError-only catch left any OTHER exception from one entry
+            # free to 500 the whole response; pairing it with this broader catch closes that gap here too).
+            logger.exception(
+                "compute_regime_lab: horizon=%s failed (non-fatal) -- isolate-and-continue (AG-8), "
+                "degrading THIS horizon honestly rather than the whole all-horizons response: %s", h, exc,
+            )
+            any_degraded = True
+            _degrade_regime_lab_horizon(
+                h, labels, fl.deciles, by_horizon_per_label, by_horizon_per_decile, rank_ic_by_horizon,
+            )
+            continue
 
-    return {
+        # COMMIT POINT — reached only on a fully successful horizon, so every accumulator gains EXACTLY one
+        # entry per horizon (either these real rows or, on the degrade paths above, the honest `unavailable`
+        # ones — never both).
+        for label in labels:
+            by_horizon_per_label[label].append(label_entries[label])
+        for d in range(1, fl.deciles + 1):
+            by_horizon_per_decile[d].append(decile_entries[d])
+        rank_ic_by_horizon.append(rank_ic_entry)
+
+    by_label = [{"regime": label, "by_horizon": by_horizon_per_label[label]} for label in labels]
+    by_decile = [{"decile": d, "by_horizon": by_horizon_per_decile[d]} for d in range(1, fl.deciles + 1)]
+
+    payload = {
         "view": view,  # J-63: the resolved overlap-honesty view (episodes default | pooled)
         # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode.
         "asof_date": as_of.isoformat() if as_of is not None else None,
@@ -4466,6 +4559,9 @@ def compute_regime_lab(
         "by_decile": by_decile,
         "rank_ic_by_horizon": rank_ic_by_horizon,
     }
+    if any_degraded:
+        payload["regime_lab_status"] = "unavailable"
+    return payload
 
 
 # The all-horizons Regime-Lab view is served through the SHARED `EventStudyCache` under a fixed sentinel
@@ -4492,7 +4588,17 @@ def regime_lab_cached(
     the stored payload (NO recompute); on a MISS, compute it ONCE via `compute_regime_lab` (which validates
     the view, raising before any write), persist under the current stamp, prune any stale rows for this
     identity, and return it. BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any dataset change
-    via the dataset-version key. `as_of` is folded into the `asof_key` slot (a pure observation-set FILTER)."""
+    via the dataset-version key. `as_of` is folded into the `asof_key` slot (a pure observation-set FILTER).
+
+    ops-hardening iter-59 (J-07, AG-8): a payload where at least one horizon degraded under memory pressure
+    (`compute_regime_lab`'s own per-horizon isolate-and-continue bound) is honest partial data for THIS
+    caller, but must NEVER be persisted as if it were the canonical cached value — a later request under the
+    SAME dataset-version stamp (e.g. once the concurrent warm that caused the pressure has finished) would
+    otherwise be served this stale degraded payload until the NEXT dataset change, instead of getting a
+    fresh attempt. Mirrors `factor_lab_all_cached`'s own never-cache-degraded guard (iter-50 audit B4) —
+    deliberately WITHOUT its single-flight/cooldown apparatus (no live reproduction here has shown the same
+    repeated-doomed-compute amplification risk; `compute_regime_lab` never raises past this guard, so a
+    simple skip-the-write is the smaller, sufficient fix)."""
     cfg = config or get_config()
     version = f"{_dataset_version(session)}-{_REGIME_LAB_SCHEMA_TOKEN}"
     asof_key = _cache_asof_key(as_of)
@@ -4513,6 +4619,13 @@ def regime_lab_cached(
     # MISS — compute once (this also validates the view, raising before any write) and persist.
     payload = compute_regime_lab(session, cfg, view=view, as_of=as_of)
 
+    if payload.get("regime_lab_status") == "unavailable":
+        logger.warning(
+            "regime_lab_cached: at least one horizon degraded under memory pressure for "
+            "(view=%s, asof_key=%s) -- serving this response but NOT caching it", view, asof_key,
+        )
+        return payload
+
     stale = session.exec(
         select(EventStudyCache).where(
             EventStudyCache.subject == _REGIME_LAB_SUBJECT,
diff --git a/apps/backend/tests/test_api_research.py b/apps/backend/tests/test_api_research.py
index 8be6f447..b6f774ff 100644
--- a/apps/backend/tests/test_api_research.py
+++ b/apps/backend/tests/test_api_research.py
@@ -352,6 +352,61 @@ def test_regime_lab_invalid_view_422(loaded_engine):
         assert client.get("/api/research/regime-lab", params={"view": "nope"}).status_code == 422
 
 
+def test_regime_lab_never_500s_under_injected_memory_pressure(loaded_engine, monkeypatch):
+    """Error case (ops-hardening iter-59, J-07/AG-8): an uncaught `MemoryError` inside `compute_regime_lab`
+    must never reach FastAPI as a raw 500. This is the HTTP-layer complement to `test_regime_lab.py`'s
+    compute-level isolate-and-continue tests — it proves the FULL stack (endpoint -> `regime_lab_cached` ->
+    `compute_regime_lab`) never lets the fault escape as a 500, using the SAME test-only
+    `_fault_inject_memory_error("regime_lab")` hook `compute_factor_lab_all` already uses (data_manager.py),
+    forced to fire on EVERY horizon. The live response still answers 200 with an honest
+    `regime_lab_status: "unavailable"` and a per-horizon `status: "unavailable"` marker on every
+    `by_label`/`by_decile`/`rank_ic_by_horizon` entry — never a 500, never a dropped connection, never a
+    fabricated number.
+
+    The request deliberately uses a cache key NO other test in this module writes (`view=pooled` scoped to
+    the oldest run date — the other pooled test is all-history, the other as-of test uses the default
+    episodes view), so `regime_lab_cached` is guaranteed to MISS and actually ENTER `compute_regime_lab`
+    where the fault fires. Without that, the earlier `?view=pooled` test's clean cached row answers this
+    request as a HIT, the injected fault never fires, and the request returns 200 for the wrong reason —
+    proving nothing about the fault path. The `regime_lab_status` assertion below is itself the guard
+    against that: a HIT serves a clean payload with no such key, so a future key collision fails loudly
+    here rather than passing silently. The final assertion additionally proves the never-cache-degraded
+    guard end-to-end over HTTP: a degraded response adds NO cache row."""
+    from sqlmodel import select
+
+    from app.engine import data_manager
+    from app.engine.research import _REGIME_LAB_SUBJECT
+    from app.models import EventStudyCache
+
+    def _cache_keys():
+        """The Regime-Lab cache rows' identity keys — compared before/after to prove nothing was written."""
+        with Session(loaded_engine) as session:
+            return sorted(
+                (r.view, r.asof_key, r.dataset_version, r.horizon)
+                for r in session.exec(
+                    select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
+                ).all()
+            )
+
+    before = _cache_keys()
+    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "regime_lab")
+    with TestClient(main.app) as client:
+        oldest = _oldest_research_date(client)
+        resp = client.get("/api/research/regime-lab", params={"view": "pooled", "as_of": oldest})
+    assert resp.status_code == 200, f"must degrade honestly, never 500: got {resp.status_code}"
+    data = resp.json()
+    assert data["asof_date"] == oldest, "fixture sanity: the scoped (guaranteed-MISS) key was served"
+    assert data["regime_lab_status"] == "unavailable"
+    for row in data["by_label"] + data["by_decile"]:
+        for b in row["by_horizon"]:
+            assert b["status"] == "unavailable"
+    for r in data["rank_ic_by_horizon"]:
+        assert r["status"] == "unavailable"
+    assert _cache_keys() == before, (
+        "the degraded payload must never be persisted to the cache (never-cache-degraded guard, over HTTP)"
+    )
+
+
 def test_regime_lab_samples_count_coherent_over_http(loaded_engine):
     """J-51/J-65 over HTTP: a Regime-Lab `N=` chip's samples drill-down `total` equals the published bucket n
     for both a regime LABEL and a regime-score DECILE, in the SAME view — and every displayable bucket
diff --git a/apps/backend/tests/test_regime_lab.py b/apps/backend/tests/test_regime_lab.py
index 26912968..e2bab233 100644
--- a/apps/backend/tests/test_regime_lab.py
+++ b/apps/backend/tests/test_regime_lab.py
@@ -19,9 +19,14 @@ NON-NEGOTIABLE contracts proven here:
   - **Cache schema token (iter-38/39/44).** A pre-iter-53 OLD-SHAPE cache row (keyed by the bare
     `_dataset_version`) is a guaranteed MISS and is PRUNED on the next write — tested against a real already-
     populated old-schema row, not a fresh compute. HIT == MISS == fresh; refreshes on a real dataset change.
-  - **Bounded read (J-105 / iter-46/47/48 OOM lesson).** The shared pool is built ONCE for all horizons (one
-    heavy read), `yield_per`-streamed (no unbounded `.all()`), ordering the ScannerResult side by
-    `(run_id, id)`. Chunk-independent (batch=1 vs huge).
+  - **Bounded read (J-105 / iter-46/47/48 OOM lesson; iter-59 per-horizon bound).** The shared pool builder
+    issues ONE batched heavy read per call, `yield_per`-streamed (no unbounded `.all()`), ordering the
+    ScannerResult side by `(run_id, id)`; chunk-independent (batch=1 vs huge). Since iter-59
+    `compute_regime_lab` calls that builder with a SINGLE-element horizons list inside its per-horizon loop
+    (build → process → release one horizon at a time) instead of retaining every horizon's pool at once —
+    byte-identically, per the builder's own single-horizon/all-horizons-slice identity, and with each
+    horizon's rows committed to the shared accumulators in ONE atomic step only on success, so a horizon
+    that degrades contributes exactly one honest `unavailable` entry and never a duplicate.
   - **Samples count-coherence (J-51/J-65).** Every displayable bucket's samples `total` equals its published
     n in BOTH views and BOTH scopes; every displayable bucket resolves without a 4xx; an unknown label /
     out-of-range decile / unknown view raises (an honest 4xx at the API).
@@ -43,17 +48,20 @@ from sqlmodel import Session, select
 
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
+from app.engine import data_manager
 from app.engine.research import (
     _REGIME_LAB_SCHEMA_TOKEN,
     _REGIME_LAB_SUBJECT,
     VIEW_EPISODES,
     VIEW_POOLED,
+    _collapse_to_episodes,
     _dataset_version,
     _deciles,
     _rank_ic,
     _regime_lab_members_by_horizon,
     _regime_lab_observation_set,
     _regime_score_ordered,
+    _run_position_index,
     compute_regime_lab,
     regime_lab_cached,
 )
@@ -551,3 +559,244 @@ def test_compute_unknown_view_raises(lab_engine):
     with Session(lab_engine) as session:
         with pytest.raises(ValueError):
             compute_regime_lab(session, cfg, view="not-a-view")
+
+
+# ==================================================================================================
+# 6. Memory-bounded, isolate-and-continue per horizon (ops-hardening iter-59, J-07/AG-8)
+#
+# The pre-iter-59 `compute_regime_lab` called `_regime_lab_members_by_horizon` ONCE for every configured
+# horizon and retained every horizon's pool (then every horizon's post-episode-collapse set) simultaneously
+# for the whole by-label + by-decile aggregation — the confirmed iter-58 crash frame under a concurrent
+# forward-aggregate warm (VmPeak landed exactly on the declared 8192 MB ceiling, live MemoryError traceback
+# naming this function). iter-59 applies the SAME proven isolate-and-continue pattern iter-46/49/50/51
+# already used for the Factor Lab's `compute_factor_lab_all`: build ONE horizon's pool, aggregate it,
+# release it, before the next horizon starts; a horizon that fails degrades ONLY itself.
+# ==================================================================================================
+def _compute_regime_lab_pinned_pre_iter59(
+    session: Session, config, *, view: str = VIEW_EPISODES, as_of=None,
+) -> dict:
+    """A byte-for-byte copy of `compute_regime_lab`'s PRE-iter-59 by-label / by-decile / rank-IC
+    aggregation — the all-horizons-retained-`pools` shape iter-58's live incident implicated — pinned here
+    as the reference oracle the iter-59 per-horizon bound is proven against. Deliberately does NOT call the
+    current `compute_regime_lab` (that would prove nothing). Returns only the three aggregation keys the
+    bound could possibly have changed (the top-level metadata fields are untouched by the refactor)."""
+    cfg = config
+    wf = cfg.walk_forward
+    fl = cfg.research.factor_lab
+    horizons = list(wf.horizons)
+    labels = list(cfg.regime.labels)
+
+    pools = _regime_lab_members_by_horizon(session, horizons, as_of, cfg=cfg)
+    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
+    members_by_h: dict[int, list[dict]] = {}
+    for h in horizons:
+        members = pools[h]
+        members_by_h[h] = members if view == VIEW_POOLED else _collapse_to_episodes(members, run_position)
+
+    by_label: list[dict] = []
+    for label in labels:
+        by_horizon: list[dict] = []
+        for h in horizons:
+            label_members = [m for m in members_by_h[h] if m["regime_label"] == label]
+            returns = [m["return"] for m in label_members]
+            mdds = [m["max_drawdown"] for m in label_members if m["max_drawdown"] is not None]
+            n = len(label_members)
+            by_horizon.append({
+                "horizon": h, "n": n, "low_sample": n < wf.min_sample,
+                "mean_return": mean(returns) if returns else None,
+                "mean_max_drawdown": mean(mdds) if mdds else None,
+            })
+        by_label.append({"regime": label, "by_horizon": by_horizon})
+
+    decile_rows_by_h: dict[int, list[dict]] = {}
+    rank_ic_by_horizon: list[dict] = []
+    for h in horizons:
+        ordered = _regime_score_ordered(members_by_h[h])
+        decile_rows_by_h[h] = _deciles(ordered, fl.deciles, wf.min_sample)
+        rank_ic_by_horizon.append({
+            "horizon": h, "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
+        })
+    by_decile: list[dict] = []
+    for d in range(1, fl.deciles + 1):
+        by_horizon = []
+        for h in horizons:
+            drow = decile_rows_by_h[h][d - 1]
+            by_horizon.append({
+                "horizon": h, "n": drow["n"], "low_sample": drow["low_sample"],
+                "mean_return": drow["mean_return"], "mean_max_drawdown": drow["mean_max_drawdown"],
+                "score_min": drow["factor_min"], "score_max": drow["factor_max"],
+            })
+        by_decile.append({"decile": d, "by_horizon": by_horizon})
+
+    return {"by_label": by_label, "by_decile": by_decile, "rank_ic_by_horizon": rank_ic_by_horizon}
+
+
+@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
+@pytest.mark.parametrize("as_of", [None, date(2025, 2, 15)])
+def test_compute_regime_lab_matches_pinned_pre_iter59_reference(lab_engine, view, as_of):
+    """TC-6 — the bounded (per-horizon build-process-release) `compute_regime_lab` is byte-identical to a
+    PINNED COPY of the pre-iter-59 all-horizons-retained implementation, for every horizon's by-label /
+    by-decile / rank-IC figures, both views, both all-history and a historical as_of — proving the iter-59
+    memory bound changed only WHEN each horizon's pool is built and released, never a value or an ordering."""
+    cfg = load_config()
+    with Session(lab_engine) as session:
+        got = compute_regime_lab(session, cfg, view=view, as_of=as_of)
+        want = _compute_regime_lab_pinned_pre_iter59(session, cfg, view=view, as_of=as_of)
+        assert _bytes(got["by_label"]) == _bytes(want["by_label"]), (
+            "by-label diverges from the pinned pre-iter-59 reference"
+        )
+        assert _bytes(got["by_decile"]) == _bytes(want["by_decile"]), (
+            "by-decile diverges from the pinned pre-iter-59 reference"
+        )
+        assert _bytes(got["rank_ic_by_horizon"]) == _bytes(want["rank_ic_by_horizon"]), (
+            "rank-IC diverges from the pinned pre-iter-59 reference"
+        )
+
+
+def test_compute_regime_lab_builds_one_horizon_at_a_time():
+    """Source-level guard: `compute_regime_lab` no longer retains every horizon's pool simultaneously — it
+    calls the shared builder with a SINGLE-element horizons list inside its per-horizon loop, so at most one
+    horizon's pool is alive at once (the iter-59 memory bound)."""
+    src = inspect.getsource(compute_regime_lab)
+    assert "_regime_lab_members_by_horizon(session, [h]" in src, (
+        "compute_regime_lab must build each horizon's pool with a single-element horizons list"
+    )
+    assert "_regime_lab_members_by_horizon(session, horizons" not in src, (
+        "compute_regime_lab must not retain every horizon's pool via one all-horizons call"
+    )
+
+
+def test_compute_regime_lab_isolates_memory_pressure_per_horizon(lab_engine, monkeypatch):
+    """TC-3 (fast/deterministic leg) — a MemoryError injected at the confirmed iter-58 crash frame (reached
+    via the per-horizon `_fault_inject_memory_error("regime_lab")` hook, the SAME test-only convention
+    `compute_factor_lab_all` uses) is caught by the per-horizon isolate-and-continue bound: THAT horizon
+    alone degrades to an honest `status: "unavailable"` entry on every by-label/by-decile row and the
+    rank-IC row — `compute_regime_lab` itself never raises, so a live request can still answer. Control arm
+    first (env unset -> no `status`/`regime_lab_status` anywhere, proving a silently-disabled injector
+    cannot pass as a green result), then the armed leg (the injector fires unconditionally on every call, so
+    EVERY horizon degrades — exercising the catch under maximum, repeated, consecutive stress)."""
+    cfg = load_config()
+
+    with Session(lab_engine) as session:
+        control = compute_regime_lab(session, cfg, view=VIEW_POOLED)
+    assert "regime_lab_status" not in control, "control run must have no degraded horizons"
+    for row in control["by_label"] + control["by_decile"]:
+        for bh in row["by_horizon"]:
+            assert "status" not in bh, f"control run must have no degraded entries; got {bh}"
+
+    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "regime_lab")
+    with Session(lab_engine) as session:
+        payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)  # must not raise
+
+    assert payload["regime_lab_status"] == "unavailable"
+    assert payload["by_label"], "the label vocabulary must still be listed even when every horizon degrades"
+    assert payload["by_decile"], "the decile vocabulary must still be listed even when every horizon degrades"
+    for row in payload["by_label"] + payload["by_decile"]:
+        for bh in row["by_horizon"]:
+            assert bh["status"] == "unavailable"
+            assert bh["n"] == 0
+            assert bh["mean_return"] is None and bh["mean_max_drawdown"] is None
+    for r in payload["rank_ic_by_horizon"]:
+        assert r["status"] == "unavailable"
+        assert r["rank_ic"] == {"value": None, "n": 0}
+
+
+def test_compute_regime_lab_one_horizon_non_memory_failure_degrades_only_that_horizon(
+    lab_engine, monkeypatch, caplog,
+):
+    """iter-59, mirrors `compute_factor_lab_all`'s iter-50 audit B4 (second half): the per-horizon loop
+    pairs its MemoryError catch with a broader `except Exception` so any OTHER failure from ONE horizon's
+    aggregation still degrades honestly instead of raising out and 500ing the whole all-horizons response.
+
+    Teeth: the fault fires on exactly one `_deciles` call (one specific horizon, deterministically the
+    first one processed), so a handler that blanked the whole response — or no handler at all, the pre-fix
+    behavior, which raises straight out of this function — fails one of the assertions below."""
+    import app.engine.research as research
+
+    cfg = load_config()
+    horizons = list(cfg.walk_forward.horizons)
+    assert len(horizons) >= 2, "fixture sanity: need >= 2 horizons to prove isolation"
+    real_deciles = research._deciles
+    calls = {"n": 0}
+    fault_on_call = 1  # the first horizon processed, deterministically
+
+    def _boom_on_one_call(ordered, n_deciles, min_sample):
+        calls["n"] += 1
+        if calls["n"] == fault_on_call:
+            raise RuntimeError("simulated non-memory failure inside one horizon's aggregation")
+        return real_deciles(ordered, n_deciles, min_sample)
+
+    monkeypatch.setattr(research, "_deciles", _boom_on_one_call)
+    with caplog.at_level("ERROR", logger="trendora.research"):
+        with Session(lab_engine) as session:
+            payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)
+
+    assert calls["n"] > fault_on_call, (
+        "the loop stopped at the injected failure instead of continuing to the next horizon — "
+        "isolate-and-continue means CONTINUE"
+    )
+    # iter-59 REVIEW FIX (the regression this test previously missed): the fault fires AFTER the faulted
+    # horizon's by-label rows are built but BEFORE its by-decile/rank-IC rows are — exactly the window in
+    # which an implementation that appended into the shared accumulators during the try would leave the
+    # horizon's REAL by-label entry in place and then append a SECOND, degraded entry for the same horizon.
+    # Every row must carry EXACTLY one entry per configured horizon, in configured order, degraded or not.
+    for row in payload["by_label"]:
+        assert [bh["horizon"] for bh in row["by_horizon"]] == horizons, (
+            f"by_label row {row['regime']!r} must carry exactly one entry per horizon in config order; "
+            f"got {[bh['horizon'] for bh in row['by_horizon']]!r}"
+        )
+    for row in payload["by_decile"]:
+        assert [bh["horizon"] for bh in row["by_horizon"]] == horizons, (
+            f"by_decile row D{row['decile']} must carry exactly one entry per horizon in config order; "
+            f"got {[bh['horizon'] for bh in row['by_horizon']]!r}"
+        )
+    assert [r["horizon"] for r in payload["rank_ic_by_horizon"]] == horizons, (
+        "rank_ic_by_horizon must carry exactly one entry per horizon in config order; "
+        f"got {[r['horizon'] for r in payload['rank_ic_by_horizon']]!r}"
+    )
+    degraded_horizons = {
+        bh["horizon"] for row in payload["by_label"] for bh in row["by_horizon"]
+        if bh.get("status") == "unavailable"
+    }
+    assert degraded_horizons == {horizons[0]}, (
+        f"exactly the faulted (first) horizon must degrade; got {degraded_horizons!r}"
+    )
+    assert payload["regime_lab_status"] == "unavailable"
+    assert any(
+        bh.get("status") != "unavailable" and bh["horizon"] != horizons[0] and bh["horizon"] in horizons
+        for row in payload["by_label"] for bh in row["by_horizon"]
+    ), "no OTHER horizon survived — the isolation is not contained, which is the failure this test forbids"
+    assert "isolate-and-continue" in caplog.text, (
+        "the isolated failure must be logged, never swallowed silently"
+    )
+
+
+def test_regime_lab_cached_never_persists_a_degraded_payload(lab_engine, monkeypatch):
+    """A payload where at least one horizon degraded under memory pressure (the isolate-and-continue bound
+    inside `compute_regime_lab`, which returns NORMALLY rather than raising) must NEVER be persisted to the
+    cache — otherwise a LATER request under the SAME dataset-version stamp would be served this stale
+    degraded payload until the next dataset change, instead of getting a fresh attempt once the memory
+    pressure has actually cleared. Proven by injecting the fault for exactly one call, confirming the served
+    response is honestly degraded, confirming NO EventStudyCache row was written, then clearing the fault
+    and confirming the NEXT call computes fresh (not a stale degraded HIT)."""
+    cfg = load_config()
+
+    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "regime_lab")
+    with Session(lab_engine) as session:
+        degraded = regime_lab_cached(session, cfg, view=VIEW_POOLED)
+    assert degraded["regime_lab_status"] == "unavailable", "fixture sanity: the injected fault must degrade"
+    with Session(lab_engine) as session:
+        rows = session.exec(
+            select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
+        ).all()
+    assert rows == [], "a degraded response must never be persisted to the cache"
+
+    monkeypatch.delenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, raising=False)
+    with Session(lab_engine) as session:
+        recovered = regime_lab_cached(session, cfg, view=VIEW_POOLED)  # must not hang, must not serve stale
+    assert "regime_lab_status" not in recovered, "a follow-up call after the fault clears must compute fresh"
+    with Session(lab_engine) as session:
+        rows = session.exec(
+            select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
+        ).all()
+    assert len(rows) == 1, "the clean recovered payload must be cached normally"
diff --git a/apps/frontend/app/research/_labs.tsx b/apps/frontend/app/research/_labs.tsx
index e2af8cda..a69f58b4 100644
--- a/apps/frontend/app/research/_labs.tsx
+++ b/apps/frontend/app/research/_labs.tsx
@@ -3839,12 +3839,24 @@ function regimeCellAt<T extends RegimeLabHorizonCell>(byHorizon: T[], h: number)
 }
 
 /** Whether a cell renders NA for a metric — the SAME `low_sample || n===0 || value===null` rule the cell
- *  uses, so the sort NA-set == the visual NA-set (NA-last in both directions, J-82 predicate). */
+ *  uses (a degraded `status === "unavailable"` cell also has n===0, so it is NA under this same rule; the
+ *  cell components below give it a DISTINCT tooltip), so the sort NA-set == the visual NA-set (NA-last in
+ *  both directions, J-82 predicate). */
 function regimeCellIsNa(cell: RegimeLabHorizonCell | undefined, metric: "fwd" | "mdd"): boolean {
-  if (!cell || cell.low_sample || cell.n === 0) return true;
+  if (!cell || cell.status === "unavailable" || cell.low_sample || cell.n === 0) return true;
   return metric === "fwd" ? cell.mean_return === null : cell.mean_max_drawdown === null;
 }
 
+/** ops-hardening iter-59 (J-07/AG-8, TC-11): the honest NA tooltip for a Regime-Lab cell, distinguishing a
+ *  horizon that DEGRADED under memory pressure (`status === "unavailable"`) from a genuinely low-sample or
+ *  empty cohort — never the same wording, never reassurance language (AG's "never hype" rule), never a
+ *  fabricated number either way. */
+function regimeNaTitle(cell: RegimeLabHorizonCell, min: number, emptyLabel: string): string {
+  if (cell.status === "unavailable") return "Temporarily unavailable — degraded under memory pressure";
+  if (cell.low_sample) return `Low sample — n below the ${min} minimum`;
+  return emptyLabel;
+}
+
 /** The numeric sort value for a metric (NA rows are pushed last by the comparator regardless of sign). */
 function regimeCellValue(cell: RegimeLabHorizonCell | undefined, metric: "fwd" | "mdd"): number {
   if (!cell) return 0;
@@ -3921,13 +3933,13 @@ function RegimeReturnCell({
   chipLabel: string;
   rangeTitle?: string;
 }) {
-  const na = cell.low_sample || cell.n === 0 || cell.mean_return === null;
+  const na = cell.status === "unavailable" || cell.low_sample || cell.n === 0 || cell.mean_return === null;
   return (
     <span className="inline-flex items-center justify-end gap-2">
       {na ? (
         <span
           className="num font-semibold text-text-muted"
-          title={cell.low_sample ? `Low sample — n below the ${min} minimum` : "No observations"}
+          title={regimeNaTitle(cell, min, "No observations")}
         >
           NA
         </span>
@@ -3944,12 +3956,12 @@ function RegimeReturnCell({
 /** A Regime-Lab paired max-drawdown cell at one horizon: mdd-color-graded value (a deeper drawdown reads
  *  more severe), or explicit NA when low-sample / empty / null — never a fabricated 0. */
 function RegimeMddCell({ cell, min }: { cell: RegimeLabHorizonCell; min: number }) {
-  const na = cell.low_sample || cell.n === 0 || cell.mean_max_drawdown === null;
+  const na = cell.status === "unavailable" || cell.low_sample || cell.n === 0 || cell.mean_max_drawdown === null;
   if (na) {
     return (
       <span
         className="num font-semibold text-text-muted"
-        title={cell.low_sample ? `Low sample — n below the ${min} minimum` : "No stored drawdown — NA"}
+        title={regimeNaTitle(cell, min, "No stored drawdown — NA")}
       >
         NA
       </span>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 1bc9b3a5..b41f2e43 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -1485,13 +1485,20 @@ export async function fetchFactorLabAll(
 // --- research / Regime Lab (iter-53, J-110) ------------------------------------------------
 /** One regime-LABEL or regime-score-DECILE bucket's paired figures at ONE horizon: the mean realized
  *  forward return + paired mean max-drawdown + sample size `n`. `low_sample` (n < min_sample) flags the
- *  cell the UI renders as NA + n. Re-formatted only — the page recomputes no return/drawdown. */
+ *  cell the UI renders as NA + n. Re-formatted only — the page recomputes no return/drawdown.
+ *
+ *  `status` (ops-hardening iter-59, J-07/AG-8) is ADDITIVE and OPTIONAL: `"unavailable"` means THIS
+ *  horizon's aggregation degraded under memory pressure (`compute_regime_lab`'s per-horizon isolate-and-
+ *  continue bound) — `n`/`mean_return`/`mean_max_drawdown` are honest zero/NA placeholders, not a
+ *  genuinely empty cohort. Absent on a clean compute — mirrors the Factor Lab's own `by_horizon[].status`
+ *  sibling field (never fabricated). */
 export interface RegimeLabHorizonCell {
   horizon: number; // the forward window (trading days)
   n: number;
   low_sample: boolean; // n < min_sample — render NA + n, never a fabricated number
   mean_return: number | null; // raw mean forward return (fraction); null when n === 0
   mean_max_drawdown: number | null; // paired mean max-drawdown (fraction, <= 0); null = NA (none stored)
+  status?: "unavailable"; // this horizon degraded under memory pressure — DISTINCT from a genuine NA
 }
 
 /** A regime-score DECILE bucket's per-horizon cell additionally carries the decile's regime-score range. */
@@ -1537,6 +1544,10 @@ export interface RegimeLabResponse {
   by_decile: RegimeLabDecileRow[]; // D1..D`deciles` of the regime score
   rank_ic_by_horizon: RegimeLabRankIcRow[]; // regime score vs forward return, per horizon
   asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
+  // ops-hardening iter-59 (J-07/AG-8): present ONLY when at least one horizon degraded under memory
+  // pressure — mirrors the Factor Lab's own (currently unconsumed) `factors_status` sibling field. Absent
+  // on a clean compute, never a fabricated "ok".
+  regime_lab_status?: "unavailable";
 }
 
 /** Canonical Regime-Lab source: GET /api/research/regime-lab. Throws on non-200 so the page renders an
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 460 +++++++++++++++++++++
 .../.engine.lock/boot_id                           |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 .../dispatch/.keepalive.sh                         |   2 +-
 .../dispatch/.pump-alive                           |   4 +-
 .../dispatch/req.5-pbwWYt.out                      |   9 -
 .../dispatch/req.5-pbwWYt.res                      |   1 -
 .../dispatch/req.5-pbwWYt.usage                    |  11 -
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 .../journey-scripts/J-05.json                      | 209 +++++++++-
 .../state/assumptions.md                           | 178 --------
 .../state/assumptions.md.archive.md                | 181 ++++++++
 runs/goal-session-ops-hardening/state/lessons.md   |  51 +--
 .../state/lessons.md.archive.md                    |  66 +++
 runs/goal-session-ops-hardening/telemetry.jsonl    |  60 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  11 +
 18 files changed, 982 insertions(+), 271 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
