# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_factor_lab_all.py` (152 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 6e73c5a1..0b9fae34 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1354,6 +1354,20 @@ class ResearchCfg(BaseModel):
     # CALC_FILE) or the component. Defaulted so a config predating it (and the inline test fixtures) still
     # loads; boot-validated `>= 1`.
     regime_phase_factor_page_size: int = 30
+    # ops-hardening iter-31 (AG-8, J-06/J-07) — the per-horizon observation-count SOFT CEILING for the
+    # all-factors Factor-Lab view's RETURN VALUE (`_all_factor_observations_by_horizon`'s `pools[h]`,
+    # `research.py:583`'s fill site — the live `MemoryError` frame iter-29/iter-30 both deferred). This is a
+    # DIFFERENT axis from `factor_join_run_chunk` (a RUN-COUNT accumulator chunk width) and `read_batch_size`
+    # (a ROW-count `yield_per` probe) — reusing either unit here would repeat the iter-29 unit-confusion
+    # lesson ("reusing another knob's unit is exactly how a prior bound went inert"). The REAL memory fix is
+    # the compact per-observation encoding (a dedup'd `core_records` table + small per-horizon tuples,
+    # replacing 5x parallel Python dict-lists that each duplicated run_id/ticker/values inline) — this field
+    # is the AG-8 disclosure net layered on top: if a future data-scale widening ever pushes a horizon's pool
+    # past this ceiling, `_all_factor_observations_by_horizon` logs a WARNING (never raises, never truncates
+    # — truncation would break the byte-identity contract) so the NEXT scale jump is an observable log line
+    # in `logs/backend.log`, not another opaque crash. Boot-validated `>= 1`; defaulted so a config (and the
+    # inline test fixtures) predating it still loads.
+    factor_pool_max_observations: int = 2_000_000
     downtrend_opportunity: "DowntrendOpportunityCfg" = Field(
         default_factory=lambda: _default_downtrend_opportunity()
     )
@@ -1374,6 +1388,8 @@ class ResearchCfg(BaseModel):
             raise ValueError("research.factor_join_run_chunk must be >= 1")
         if self.regime_phase_factor_page_size < 1:
             raise ValueError("research.regime_phase_factor_page_size must be >= 1")
+        if self.factor_pool_max_observations < 1:
+            raise ValueError("research.factor_pool_max_observations must be >= 1")
         return self
 
 
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index f27255f0..a5516caf 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -36,6 +36,8 @@ THREE non-negotiable disciplines (each unit-proved):
 from __future__ import annotations
 
 import json
+import logging
+import threading
 from collections import defaultdict
 from datetime import date as date_cls
 from datetime import datetime, timezone
@@ -62,6 +64,12 @@ from app.engine.forward_testing import (
 from app.engine.setups import ALL_STATUSES
 from app.models import DailyPrice, EventStudyCache, ForwardReturn, ScannerResult, ScannerRun
 
+# ops-hardening iter-31 (AG-8) — the all-factors Factor-Lab return-value pool-bound WARNING (never raised,
+# never truncates a payload — see `_all_factor_observations_by_horizon`) and the `factor_lab_all_cached`
+# single-flight guard's failure-path fallback both log through this, mirroring the established
+# "trendora.<module>" convention (`data_manager.py`, `forward_testing.py`, `evidence.py`).
+logger = logging.getLogger("trendora.research")
+
 # The honest "descriptive, not predictive / universe-relative" caveat carried on every Factor-Lab
 # payload alongside the (reused, single-source) survivorship-bias label (anti-goals: Research lab is
 # read-only, honest & not predictive + Honest limitations surfaced).
@@ -502,27 +510,49 @@ def _all_fr_slice_map(
 def _all_factor_observations_by_horizon(
     session: Session, factors: list, horizons: list[int], as_of: Optional[date_cls] = None,
     *, cfg: Optional[Config] = None,
-) -> dict[int, list[dict]]:
+) -> tuple[list[tuple[int, str, tuple]], dict[int, list[tuple[int, float, Optional[float]]]]]:
     """The read-only SHARED per-observation pools for the all-factors view across EVERY horizon in
     `horizons` (J-109), built from ONE run-chunked sweep: per slice of run ids, one `ForwardReturn` SELECT
     covering all horizons (`horizon IN horizons`, column-projected to run_id/symbol/realized_return/
     max_drawdown) and one `ScannerResult` stream. Every ScannerResult row is still visited EXACTLY ONCE
     across the whole call (the slices partition the run-id space), so the per-result `record_json` parse
-    count is unchanged. Returns `{horizon: [observations]}` where each observation is
-    `{run_id, ticker, return, max_drawdown, values: {factor_key: float|None}}` (every catalog factor's
-    stored value read VERBATIM — typed column or `record_json` component `raw`; recomputes NO factor and NO
-    return). The `values` dict is read once per ScannerResult and SHARED across that result's per-horizon
-    observations (the factor value is horizon-independent).
-
-    BYTE-IDENTITY keystone: `{horizon: pools}[h]` is byte-identical (row-for-row, same `(run_id, id)` order)
-    to `_all_factor_observations(factors, h, as_of)` would have produced for a single horizon — and so each
-    factor's non-null subset of `pools[h]` EQUALS `_factor_observations(factor, h, as_of)` row-for-row, the
-    property `compute_factor_lab_all` relies on for per-(factor,horizon,decile) byte-identity. A NULL in one
-    factor does NOT drop the observation (unlike `_combination_observations`): the pool keeps
-    `values[key] = None`, so each factor filters to ITS OWN non-null subset. An observation is kept for
-    horizon h ONLY when a realized return exists at h (the SAME n=0 exclusion as `_factor_observations`); a
-    ScannerResult whose run has FRs at some other horizon but not at h simply contributes nothing to
-    `pools[h]` (the per-horizon `fr is None` gate), exactly as the single-horizon builder dropped it.
+    count is unchanged.
+
+    ops-hardening iter-31 (AG-8, J-06/J-07) — RETURN-VALUE memory bound. iter-29 fix-2 (below) bounded the
+    JOIN ACCUMULATOR (`fr_by_h`) but left this function's OWN return shape unbounded "by design": the OLD
+    `{horizon: [{run_id, ticker, return, max_drawdown, values} for every observation]}` held FIVE parallel
+    Python lists of 5-key dicts, each dict INLINING its own copy of `run_id`/`ticker` on top of the
+    (already-shared) `values` reference — duplicating run_id+ticker once per horizon a result touches
+    (typically all 5) plus the per-dict container overhead. That duplication is `research.py:583`'s
+    `pools[h].append` fill site — the live `MemoryError` frame both iter-29 and iter-30 reproduced and
+    deferred (771,629-804,372 observations PER horizon on the live basis — `config.yaml`'s
+    `research.factor_pool_max_observations` comment).
+
+    Returns `(core_records, pools)` — a genuine memory-representation redesign, not a smaller constant:
+      - `core_records`: ONE entry per ScannerResult with a realized return at >= 1 horizon —
+        `(run_id, ticker, values)`, where `values` is a TUPLE (not a dict) of every catalog factor's stored
+        value, ORDERED to match `factors` (so `values[i]` is `factors[i]`'s value — `compute_factor_lab_all`
+        looks it up by a precomputed index, never by string key). `ticker` is INTERNED against a local cache
+        scoped to this call, so the (far smaller) set of distinct ticker strings is held ONCE rather than
+        once per horizon-observation.
+      - `pools[h]`: a list of SMALL `(core_idx, realized_return, max_drawdown)` tuples — the genuinely
+        per-horizon-specific data (a result's realized return / drawdown differ by horizon; its identity and
+        factor values do not) — replacing the old per-horizon 5-key dict. `core_idx` indexes `core_records`.
+      Neither the run-id chunking below nor the "ONE shared read serves every factor at every horizon"
+      property changes: `core_records` is built lazily on the FIRST horizon a result has an FR at (same
+      trigger the old `values` dict used), so this remains ONE pass over `ScannerResult`, never a per-horizon
+      re-read (`test_all_factors_fires_one_shared_pool_read_not_n`).
+
+    BYTE-IDENTITY keystone (same data, compacted container): for factor `f` at its precomputed index `idx`
+    and horizon `h`, `[(core_records[i][0], core_records[i][1], core_records[i][2][idx], ret, mdd)
+    for (i, ret, mdd) in pools[h] if core_records[i][2][idx] is not None]` reproduces EXACTLY the rows
+    `_all_factor_observations(f, h, as_of)` would have produced — same values, same `(run_id, id)` traversal
+    order — the property `compute_factor_lab_all` relies on for per-(factor,horizon,decile) byte-identity. A
+    NULL in one factor does NOT drop the observation (unlike `_combination_observations`): `values[idx]`
+    stays `None` for that factor's own filter. An observation is kept for horizon h ONLY when a realized
+    return exists at h (the SAME n=0 exclusion as `_factor_observations`); a ScannerResult whose run has FRs
+    at some other horizon but not at h simply contributes nothing to `pools[h]` (the per-horizon `fr is None`
+    gate), exactly as the single-horizon builder dropped it.
 
     `as_of` (J-32) scopes ALL horizons' pools to snapshots with `ScannerRun.asof_date <= as_of` (the SAME
     single membership filter); `as_of=None` adds NO clause -> byte-identical all-history.
@@ -553,16 +583,24 @@ def _all_factor_observations_by_horizon(
     `UNIQUE (run_id, symbol, horizon)`. No-lookahead is preserved because the `as_of` cutoff moved UP into
     `_runs_with_fr`, upstream of every derived structure.
 
-    NOT bounded here (deliberate, same call the single-factor builder makes): the returned `pools` are this
-    function's return shape — `compute_factor_lab_all` needs each horizon's pool whole to derive its
-    deciles. Only the accumulator's peak is bounded."""
+    iter-31 AG-8 disclosure net (NOT the memory fix itself — see above): if any horizon's `pools[h]` ever
+    exceeds `research.factor_pool_max_observations` (a soft ceiling, set with headroom above today's live
+    max per `config.yaml`'s comment), this logs a WARNING and keeps going — NEVER raises, NEVER truncates
+    (truncation would break the byte-identity contract this function exists to preserve). The check runs
+    PER RUN-CHUNK inside the sweep, once per horizon (iter-31 audit): a widening large enough to exhaust
+    memory raises inside that loop, so an after-the-loop check could never fire on the very crash this net
+    exists to pre-announce."""
     parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
     research_cfg = (cfg or get_config()).research
     batch = research_cfg.read_batch_size          # ROW count — the `yield_per` size of each stream
     run_chunk = research_cfg.factor_join_run_chunk  # RUN count — the accumulator's slice width
+    pool_cap = research_cfg.factor_pool_max_observations  # AG-8 disclosure ceiling — never truncates
 
     runs_with_fr = _runs_with_fr(session, horizons, as_of)
-    pools: dict[int, list[dict]] = {h: [] for h in horizons}
+    core_records: list[tuple[int, str, tuple]] = []
+    pools: dict[int, list[tuple[int, float, Optional[float]]]] = {h: [] for h in horizons}
+    ticker_intern: dict[str, str] = {}  # dedupes repeated ticker strings across the whole sweep (iter-31)
+    warned_horizons: set[int] = set()  # one WARNING per horizon — never a per-chunk log storm (iter-31 audit)
     for start in range(0, len(runs_with_fr), run_chunk):
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         fr_by_h = _all_fr_slice_map(session, horizons, slice_run_ids, batch)
@@ -572,21 +610,39 @@ def _all_factor_observations_by_horizon(
             .order_by(ScannerResult.run_id, ScannerResult.id)
         )
         for res in session.exec(res_stmt).yield_per(batch):
-            values: Optional[dict] = None  # parsed lazily on the first horizon that has an FR for this result
+            core_idx: Optional[int] = None  # assigned lazily on the first horizon that has an FR
             for h in horizons:
                 fr = fr_by_h[h].get((res.run_id, res.ticker))
                 if fr is None:
                     continue  # no realized return at this horizon (n=0) — same exclusion as per-factor
-                if values is None:
-                    values = {key: _extract_factor_value(res, parsed) for key, parsed in parsed_by_key.items()}
+                if core_idx is None:
+                    values = tuple(_extract_factor_value(res, parsed) for parsed in parsed_by_key.values())
+                    ticker = ticker_intern.setdefault(res.ticker, res.ticker)
+                    core_idx = len(core_records)
+                    core_records.append((res.run_id, ticker, values))
                 realized, max_drawdown = fr
-                pools[h].append({
-                    "run_id": res.run_id, "ticker": res.ticker, "return": realized,
-                    "max_drawdown": max_drawdown, "values": values,
-                })
+                pools[h].append((core_idx, realized, max_drawdown))
         # `fr_by_h` is rebound (not accumulated into) on the next iteration — this slice's maps are eligible
-        # for GC before the next chunk's query even starts (the bounded-memory guarantee).
-    return pools
+        # for GC before the next chunk's query even starts (the bounded-memory guarantee, unchanged iter-29).
+        #
+        # iter-31 AUDIT FIX: the ceiling is checked HERE, per run-chunk, NOT after the sweep. The scenario
+        # `config.yaml`'s comment promises to pre-announce ("a future data-scale widening logs a WARNING
+        # instead of silently repeating this crash at a larger scale") is precisely the one in which the
+        # build never reaches its own end: a widening big enough to exhaust memory raises MemoryError
+        # INSIDE this loop, so an after-the-loop check could never fire on the very crash it disclaims.
+        # Per-chunk costs O(len(runs)/run_chunk) length reads (a handful on the live basis) and lands the
+        # line in `logs/backend.log` while the build is still running. Still never raises, never truncates.
+        for h, pool in pools.items():
+            if len(pool) > pool_cap and h not in warned_horizons:
+                warned_horizons.add(h)
+                logger.warning(
+                    "research.factor_pool_max_observations exceeded: horizon=%s observations=%d cap=%d — a "
+                    "data-scale widening past the documented live basis (config.yaml comment); the payload "
+                    "is still computed and served correctly, this is AG-8 disclosure only, never a "
+                    "truncation",
+                    h, len(pool), pool_cap,
+                )
+    return core_records, pools
 
 
 def compute_factor_lab_all(
@@ -621,10 +677,14 @@ def compute_factor_lab_all(
     horizons = list(wf.horizons)
     default_h = wf.default_horizon
 
-    pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
+    core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
+    # position of each factor inside `core_records[i][2]`'s values tuple — built from the SAME `factors`
+    # list (in the SAME order) `_all_factor_observations_by_horizon` used to build that tuple (iter-31).
+    factor_index = {f.key: i for i, f in enumerate(factors)}
 
     factors_table: list[dict] = []
     for factor in factors:
+        idx = factor_index[factor.key]
         by_horizon: list[dict] = []
         dh_rank_ic: dict = {"value": None, "n": 0}
         dh_risk_adjusted: Optional[float] = None
@@ -632,16 +692,19 @@ def compute_factor_lab_all(
         for h in horizons:
             # ITS non-null subset at horizon h, in the pool's order (== `_factor_observations(factor, h)`
             # order), so the rank-IC pearson summation order — and thus the byte value — matches
-            # compute_factor_lab(factor, h) exactly. The paired drawdown rides along verbatim.
-            obs = [
-                {
-                    "run_id": o["run_id"], "ticker": o["ticker"],
-                    "factor": float(o["values"][factor.key]), "return": o["return"],
-                    "max_drawdown": o["max_drawdown"],
-                }
-                for o in pools[h]
-                if o["values"][factor.key] is not None
-            ]
+            # compute_factor_lab(factor, h) exactly. The paired drawdown rides along verbatim. `core_records`
+            # holds the (run_id, ticker, values) identity SHARED across every horizon a result touches — only
+            # `ret`/`max_drawdown` are genuinely per-horizon (iter-31 compact-encoding return-value bound).
+            obs = []
+            for core_idx, ret, max_drawdown in pools[h]:
+                factor_value = core_records[core_idx][2][idx]
+                if factor_value is None:
+                    continue
+                run_id, ticker, _values = core_records[core_idx]
+                obs.append({
+                    "run_id": run_id, "ticker": ticker,
+                    "factor": float(factor_value), "return": ret, "max_drawdown": max_drawdown,
+                })
             # ascending by stored factor value; SAME deterministic tie-break compute_factor_lab uses.
             ordered = sorted(obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
             deciles = _deciles(ordered, fl.deciles, wf.min_sample)
@@ -2989,6 +3052,38 @@ _ALL_FACTORS_VIEW = "factors_table"
 # shape. The view is horizon-independent now, so the cache `horizon` slot is pinned to `default_horizon`.
 _ALL_FACTORS_SCHEMA_TOKEN = "allh-mdd-v1"
 
+# ops-hardening iter-31 (audit finding B5, AG-8) — single-flight de-dup guarding `factor_lab_all_cached`'s
+# cache-MISS path, mirroring `data_manager.compute_coverage`'s established per-key-lock + in-flight-event
+# idiom (never a new concurrency abstraction) with `forward_testing.forward_aggregates_ingest_cached`'s
+# bounded-wait failure-path convention (iter-15, UT-04). Root cause: the audit observed a concurrent
+# duplicate `compute_factor_lab_all` invocation for the SAME `(asof_key, dataset_version+token, horizon)`
+# identity complete while another was already in flight and about to write the same row — no lock, unlike
+# every sibling all-horizons cache (`forward_aggregates_ingest_cached`, `compute_coverage`) — wasting exactly
+# the memory headroom the return-value bound above exists to create. The FIRST caller for a key computes
+# below; every OTHER concurrent caller for that SAME key waits (bounded), then re-reads the now-persisted
+# row with its OWN session — never a second producer. A waiter whose bounded wait elapses (the owner raised,
+# or a genuine wedge) falls through and computes independently rather than hanging — never a deadlock, never
+# a raise of its own.
+_FACTOR_LAB_ALL_LOCK = threading.Lock()
+# per-key in-flight events: (asof_key, dataset_version+token, horizon) -> Event, set when the owner finishes
+# (success or failure) so any waiter wakes. Always removed by the owner in a `finally`.
+_FACTOR_LAB_ALL_INFLIGHT: dict[tuple, threading.Event] = {}
+# Bounded wait for a NON-owner caller. It must be sized against THIS call's OWN compute duration — the
+# first cut of this guard copied `forward_testing._FORWARD_AGG_WAIT_TIMEOUT_S` (45s, tuned for that
+# module's much faster aggregate compute) and was rejected in review for exactly that reason: one full
+# cold-MISS `compute_factor_lab_all` on the live deep basis, under the mandatory host-guard CPU caps
+# (AG-10 — a permanent physical constraint of this host, never removable), was measured at ~2-4 min and
+# ~4-5 min across two independent backend restarts (2026-07-29, iter-31 dev handoff) => worst observed
+# ~300s. A 45s ceiling would therefore ALWAYS elapse mid-compute, sending every waiter off to start its
+# own duplicate compute — precisely the audit-B5 waste this guard exists to close. The owner ALWAYS sets
+# the event in its `finally` (success OR raise), so this ceiling is only ever reached by a genuinely
+# wedged owner: sizing it generously costs a healthy request nothing, while sizing it below the real
+# compute duration silently disables the de-dup. Integer seconds (`Event.wait` accepts an int) so the
+# derivation stays literal-free under the no-magic-numbers engine rule.
+_FACTOR_LAB_ALL_MEASURED_COLD_MISS_S = 300  # worst observed live cold-MISS compute (2026-07-29 measurement)
+_FACTOR_LAB_ALL_WAIT_SAFETY_FACTOR = 3      # headroom for a slower/more loaded host than the measured one
+_FACTOR_LAB_ALL_WAIT_TIMEOUT_S = _FACTOR_LAB_ALL_MEASURED_COLD_MISS_S * _FACTOR_LAB_ALL_WAIT_SAFETY_FACTOR
+
 
 def factor_lab_all_cached(
     session: Session, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
@@ -3003,48 +3098,90 @@ def factor_lab_all_cached(
     MISS, compute it ONCE via `compute_factor_lab_all`, persist under the current stamp, prune any stale rows
     for this identity, and return it. BYTE-IDENTICAL to a fresh compute; the cache REFRESHES after any
     dataset change via the dataset-version key. `as_of` is folded into the `asof_key` slot (a pure
-    observation-set FILTER)."""
+    observation-set FILTER).
+
+    iter-31 (audit B5, AG-8): a MISS now goes through the module-level single-flight guard above, keyed on
+    the SAME `(asof_key, version, horizon)` tuple used for the cache row itself — concurrent same-key MISSes
+    share ONE `compute_factor_lab_all` invocation instead of racing duplicate computes onto the same row."""
     cfg = config or get_config()
     version = f"{_dataset_version(session)}-{_ALL_FACTORS_SCHEMA_TOKEN}"
     asof_key = _cache_asof_key(as_of)
     horizon = cfg.walk_forward.default_horizon  # the horizon-independent view pins the cache horizon slot
 
-    hit = session.exec(
-        select(EventStudyCache).where(
-            EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
-            EventStudyCache.view == _ALL_FACTORS_VIEW,
-            EventStudyCache.asof_key == asof_key,
-            EventStudyCache.dataset_version == version,
-            EventStudyCache.horizon == horizon,
-        )
-    ).first()
-    if hit is not None:
-        return json.loads(hit.payload_json)
-
-    payload = compute_factor_lab_all(session, cfg, as_of=as_of)
+    def _cached_row() -> Optional[dict]:
+        row = session.exec(
+            select(EventStudyCache).where(
+                EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
+                EventStudyCache.view == _ALL_FACTORS_VIEW,
+                EventStudyCache.asof_key == asof_key,
+                EventStudyCache.dataset_version == version,
+                EventStudyCache.horizon == horizon,
+            )
+        ).first()
+        return json.loads(row.payload_json) if row is not None else None
 
-    stale = session.exec(
-        select(EventStudyCache).where(
-            EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
-            EventStudyCache.view == _ALL_FACTORS_VIEW,
-            EventStudyCache.asof_key == asof_key,
-            EventStudyCache.horizon == horizon,
-            EventStudyCache.dataset_version != version,
+    hit = _cached_row()
+    if hit is not None:
+        return hit
+
+    # single-flight: only the FIRST caller for this key computes; concurrent same-key callers wait.
+    key = (asof_key, version, horizon)
+    with _FACTOR_LAB_ALL_LOCK:
+        event = _FACTOR_LAB_ALL_INFLIGHT.get(key)
+        is_owner = event is None
+        if is_owner:
+            event = threading.Event()
+            _FACTOR_LAB_ALL_INFLIGHT[key] = event
+
+    if not is_owner:
+        event.wait(timeout=_FACTOR_LAB_ALL_WAIT_TIMEOUT_S)
+        hit = _cached_row()
+        if hit is not None:
+            return hit
+        # the owner failed (its `finally` already released the slot) or a genuine wedge exceeded the
+        # bounded wait without persisting — fall through and compute independently rather than blocking
+        # indefinitely. Still byte-identical (the SAME sole producer); at worst a rare redundant compute.
+        # The wait ceiling is sized well above the measured real compute (above), so reaching it is an
+        # abnormal event: log it, so a duplicate compute can never happen SILENTLY (audit B5 was found by
+        # observing one, and this is the only path that can still start one).
+        logger.warning(
+            "factor_lab_all single-flight wait elapsed or owner failed for key=%s after %ss — computing "
+            "independently (duplicate compute possible)", key, _FACTOR_LAB_ALL_WAIT_TIMEOUT_S,
         )
-    ).all()
-    for row in stale:
-        session.delete(row)
 
-    session.add(EventStudyCache(
-        subject=_ALL_FACTORS_SUBJECT, view=_ALL_FACTORS_VIEW, asof_key=asof_key, dataset_version=version,
-        horizon=horizon, payload_json=json.dumps(payload),
-        created_at=datetime.now(timezone.utc),
-    ))
+    # MISS (owner path, or the rare fallback above) — compute once and persist.
     try:
-        session.commit()
-    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
-        session.rollback()
-    return payload
+        payload = compute_factor_lab_all(session, cfg, as_of=as_of)
+
+        stale = session.exec(
+            select(EventStudyCache).where(
+                EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
+                EventStudyCache.view == _ALL_FACTORS_VIEW,
+                EventStudyCache.asof_key == asof_key,
+                EventStudyCache.horizon == horizon,
+                EventStudyCache.dataset_version != version,
+            )
+        ).all()
+        for row in stale:
+            session.delete(row)
+
+        session.add(EventStudyCache(
+            subject=_ALL_FACTORS_SUBJECT, view=_ALL_FACTORS_VIEW, asof_key=asof_key, dataset_version=version,
+            horizon=horizon, payload_json=json.dumps(payload),
+            created_at=datetime.now(timezone.utc),
+        ))
+        try:
+            session.commit()
+        except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
+            session.rollback()
+        return payload
+    finally:
+        # release the in-flight slot + wake any waiter whether we succeeded or raised — a waiter then either
+        # finds the persisted payload or falls through and computes independently — never a hang.
+        if is_owner:
+            with _FACTOR_LAB_ALL_LOCK:
+                _FACTOR_LAB_ALL_INFLIGHT.pop(key, None)
+            event.set()
 
 
 def regime_setup_pattern_cached(
diff --git a/apps/backend/tests/test_factor_lab_all.py b/apps/backend/tests/test_factor_lab_all.py
index 91508648..ff76cafd 100644
--- a/apps/backend/tests/test_factor_lab_all.py
+++ b/apps/backend/tests/test_factor_lab_all.py
@@ -33,6 +33,9 @@ from __future__ import annotations
 
 import inspect
 import json
+import sys
+import threading
+from concurrent.futures import ThreadPoolExecutor, as_completed
 from datetime import date, datetime, timedelta, timezone
 
 import pytest
@@ -54,6 +57,12 @@ from app.engine.research import (
 from app.engine.samples import KIND_FACTOR, compute_samples
 from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun
 
+# Hang detector for the concurrency tests below. Deliberately FAR BELOW the shipped
+# `research._FACTOR_LAB_ALL_WAIT_TIMEOUT_S` (900s): every scenario exercised here resolves in well under a
+# second of real work, so a caller that is still alive after a minute has wedged — and this fails it as a
+# hang instead of letting it "pass slowly" by riding the production wait ceiling.
+BOUNDED_TIMEOUT_S = 60.0
+
 DEFAULT_H = 20  # config walk_forward.default_horizon
 POPULATED_HORIZONS = (1, 5, 20)  # horizons with FRs AND a paired max_drawdown
 NO_MDD_HORIZON = 60  # has FRs but max_drawdown=None (NA-honest mean-MDD leg)
@@ -427,18 +436,64 @@ def _all_pools_reference_unchunked(session, factors, horizons, as_of, cfg):
     return pools
 
 
+def _materialize_compact_pools(core_records, pools) -> dict:
+    """iter-31 test-only adapter: expands the compact `(core_records, pools)` return shape back into the OLD
+    pinned-reference shape (`{horizon: [{run_id, ticker, return, max_drawdown, values}, ...]}`) so the
+    byte-identity oracle (`_all_pools_reference_unchunked`, deliberately left UNCHANGED — it is the pinned
+    pre-fix reference, not something this iteration should touch) can compare like-for-like. `values` is
+    rebuilt as a dict keyed positionally 0..N-1 (the pinned reference's `values` dict is keyed by factor
+    KEY, not position — so this test instead compares the VALUES TUPLE contents in factor order, which is
+    exactly what the pinned reference's dict.values() would iterate in, since both are built from the SAME
+    `factors` list order). Proves the DATA is unchanged; the representation is intentionally different."""
+    out: dict[int, list[dict]] = {}
+    for h, pool in pools.items():
+        rows = []
+        for core_idx, ret, mdd in pool:
+            run_id, ticker, values = core_records[core_idx]
+            rows.append({
+                "run_id": run_id, "ticker": ticker, "return": ret, "max_drawdown": mdd,
+                "values": list(values),  # positional, factor-order — compared against the reference below
+            })
+        out[h] = rows
+    return out
+
+
+def _reference_as_positional(reference: dict, factors: list) -> dict:
+    """Re-key the pinned reference's per-observation `values` dict (keyed by factor KEY) into the SAME
+    factor-order positional list `_materialize_compact_pools` produces, so the two shapes compare byte-for-
+    byte without asserting anything about dict-vs-tuple representation itself (iter-31 — representation is
+    allowed to change; the underlying data must not)."""
+    keys = [f.key for f in factors]
+    out: dict[int, list[dict]] = {}
+    for h, rows in reference.items():
+        out[h] = [
+            {
+                "run_id": r["run_id"], "ticker": r["ticker"], "return": r["return"],
+                "max_drawdown": r["max_drawdown"], "values": [r["values"][k] for k in keys],
+            }
+            for r in rows
+        ]
+    return out
+
+
 @pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
 def test_shared_pools_chunked_equal_the_pinned_unchunked_reference(lab_engine, as_of):
     """The run-chunked shared-pool build is byte-identical to the pinned pre-fix single-accumulator
     reference — same rows, same per-horizon order, same factor values — for all-history AND an as-of window
-    that splits the fixture's two runs."""
+    that splits the fixture's two runs. iter-31: the chunked build now returns the compact
+    `(core_records, pools)` shape (a return-value memory-representation redesign); materialized back to the
+    old per-observation shape, the DATA is still byte-identical to the pinned reference."""
     cfg = _cfg_batch(2, run_chunk=1)  # 1 run id per slice over the fixture's 2 runs -> real chunking
     factors = list(cfg.research.factor_lab.factors)
     horizons = list(cfg.walk_forward.horizons)
     with Session(lab_engine) as session:
-        chunked = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
+        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
         reference = _all_pools_reference_unchunked(session, factors, horizons, as_of, cfg)
-    assert _bytes(chunked) == _bytes(reference), f"chunked pools != pinned pre-fix pools (as_of={as_of})"
+    materialized = _materialize_compact_pools(core_records, pools)
+    positional_reference = _reference_as_positional(reference, factors)
+    assert _bytes(materialized) == _bytes(positional_reference), (
+        f"chunked compact pools != pinned pre-fix pools (as_of={as_of})"
+    )
 
 
 def test_shared_pool_accumulator_is_chunk_bounded_at_the_shipped_config(tmp_path, monkeypatch):
@@ -477,7 +532,9 @@ def test_shared_pool_accumulator_is_chunk_bounded_at_the_shipped_config(tmp_path
     factors = list(cfg.research.factor_lab.factors)
     horizons = list(cfg.walk_forward.horizons)
     with Session(engine) as session:
-        pools = research._all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)
+        _core_records, pools = research._all_factor_observations_by_horizon(
+            session, factors, horizons, None, cfg=cfg
+        )
 
     total_pairs = n_runs * len(tickers) * len(POPULATED_HORIZONS)
     assert sum(len(p) for p in pools.values()) == total_pairs, "sanity: every fixture pair must surface"
@@ -544,3 +601,445 @@ def test_all_factors_fires_one_shared_pool_read_not_n(lab_engine, monkeypatch):
     with Session(lab_engine) as session:
         research.compute_factor_lab_all(session, load_config())
     assert calls["n"] == 1, f"expected ONE shared pool read, got {calls['n']}"
+
+
+# ==================================================================================================
+# 5. iter-31 (AG-8, deferred-twice finding) — the RETURN-VALUE pool bound + the `factor_lab_all_cached`
+# single-flight guard (audit B5). Two causally-linked fixes: a concurrent duplicate compute doubles the
+# exact peak the pool bound is trying to create, so this iteration closes both together (session rule 5).
+# ==================================================================================================
+
+# Live basis measured 2026-07-29 (apps/backend/data/trendora.db, ~4.97 GB): per-horizon forward_returns /
+# pool sizes range from 771,629 (h=60) to 804,372 (h=1) across the 5 configured horizons — the SAME figures
+# documented in `config.yaml`'s `factor_pool_max_observations` comment (781,965 scanner_results total,
+# 781,417 with a realized return at >= 1 horizon). A ceiling BELOW this range would fire the AG-8 disclosure
+# warning on every normal request (noise, not signal); a ceiling so large it could never realistically bind
+# (e.g. 10**12) would be a disconnected, meaningless "shipped-config" number in the same spirit as the
+# iter-29 lesson. This bounds the shipped value to a sane window.
+_LIVE_POOL_OBSERVATIONS_MAX = 804_372
+_MAX_MEANINGFUL_POOL_CEILING = _LIVE_POOL_OBSERVATIONS_MAX * 20
+
+
+def test_shipped_factor_pool_max_observations_actually_covers_the_live_basis():
+    """iter-31 TC-6: the SHIPPED `research.factor_pool_max_observations` must sit ABOVE today's live
+    per-horizon observation count (documented above) — otherwise the AG-8 disclosure warning would fire on
+    EVERY normal request (noise, not signal) — but not so large it is a disconnected, meaningless number.
+    Mirrors `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`'s shipped-vs-fixture-width
+    convention (`test_research_streaming.py`), applied to a CEILING instead of a chunk WIDTH: no
+    `_cfg_batch`-style override, the REAL `config.yaml` value, checked against the REAL measured basis."""
+    research_cfg = load_config().research
+    cap = research_cfg.factor_pool_max_observations
+    assert _LIVE_POOL_OBSERVATIONS_MAX <= cap <= _MAX_MEANINGFUL_POOL_CEILING, (
+        f"research.factor_pool_max_observations={cap} does not sanely cover the live basis "
+        f"({_LIVE_POOL_OBSERVATIONS_MAX} observations measured on the live DB, 2026-07-29): it must satisfy "
+        f"{_LIVE_POOL_OBSERVATIONS_MAX} <= cap <= {_MAX_MEANINGFUL_POOL_CEILING}"
+    )
+
+
+def test_factor_pool_cap_exceeded_logs_a_warning_and_never_truncates(lab_engine, caplog):
+    """iter-31: when a horizon's pool genuinely exceeds the configured `factor_pool_max_observations`
+    ceiling, `_all_factor_observations_by_horizon` logs a WARNING naming the horizon/count/cap — and still
+    returns the FULL, untruncated pool (AG-8: disclosure only; truncating would break the byte-identity
+    contract the whole module exists to preserve). Uses a tiny overridden cap on the cheap `lab_engine`
+    fixture — the SEPARATE test above proves the SHIPPED value's real-world adequacy; this one proves the
+    mechanism actually fires and never truncates."""
+    cfg = load_config()
+    tiny_cap_cfg = cfg.model_copy(update={"research": cfg.research.model_copy(update={
+        "factor_pool_max_observations": 1,
+    })})
+    factors = list(tiny_cap_cfg.research.factor_lab.factors)
+    horizons = list(tiny_cap_cfg.walk_forward.horizons)
+    with Session(lab_engine) as session:
+        with caplog.at_level("WARNING", logger="trendora.research"):
+            core_records, pools = _all_factor_observations_by_horizon(
+                session, factors, horizons, None, cfg=tiny_cap_cfg
+            )
+    # sanity: the fixture genuinely exceeds the tiny cap at every populated horizon (test not vacuous).
+    for h in POPULATED_HORIZONS:
+        assert len(pools[h]) > 1, f"fixture too small to exceed cap=1 at horizon {h} — test is vacuous"
+    assert "factor_pool_max_observations exceeded" in caplog.text, (
+        "expected a WARNING when a horizon's pool exceeds the configured cap"
+    )
+    # never truncated: full pools + full core_records are returned untouched by the disclosure net.
+    assert core_records, "core_records must not be truncated away by the disclosure net"
+    for h in POPULATED_HORIZONS:
+        assert len(pools[h]) > tiny_cap_cfg.research.factor_pool_max_observations, (
+            f"horizon {h} pool was truncated down to the tiny cap — must never truncate"
+        )
+
+
+def test_factor_lab_all_cached_single_flight_dedups_concurrent_miss_to_one_compute(lab_engine):
+    """iter-31 TC-3 (audit B5, AG-8): N concurrent `factor_lab_all_cached` MISS callers for the SAME identity
+    trigger the underlying heavy `compute_factor_lab_all` EXACTLY ONCE (call-count instrumentation, mirrors
+    `test_forward_aggregates_ingest_cached_dedups_concurrent_same_key_miss_to_one_compute` in
+    `test_forward_testing_concurrency.py`) — not merely that concurrent callers happen to agree on an
+    answer. All N callers still return byte-identical payloads, and none hangs."""
+    import app.engine.research as research
+
+    cfg = load_config()
+    n_callers = 5
+    call_count = {"n": 0}
+    real = research.compute_factor_lab_all
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    def _caller():
+        with Session(lab_engine) as session:
+            return research.factor_lab_all_cached(session, cfg)
+
+    research.compute_factor_lab_all = _counting
+    try:
+        with ThreadPoolExecutor(max_workers=n_callers) as pool:
+            futures = [pool.submit(_caller) for _ in range(n_callers)]
+            results = [f.result() for f in as_completed(futures, timeout=BOUNDED_TIMEOUT_S)]
+    finally:
+        research.compute_factor_lab_all = real
+
+    assert len(results) == n_callers, "not every caller completed — a caller hung"
+    assert call_count["n"] == 1, (
+        f"expected compute_factor_lab_all to run exactly once for {n_callers} concurrent same-key MISSes; "
+        f"it ran {call_count['n']} times — the single-flight de-dup did not hold (audit B5 regression)"
+    )
+    first = _bytes(results[0])
+    for payload in results[1:]:
+        assert _bytes(payload) == first, "concurrent callers returned DIFFERENT payloads for the same key"
+
+
+# The bounded wait a NON-owner caller spends before giving up and computing independently must exceed
+# THIS call's own compute duration, not a sibling module's. One full cold-MISS `compute_factor_lab_all` on
+# the live deep basis, under the mandatory host-guard CPU caps (AG-10, permanent on this host), was measured
+# at ~2-4 min and ~4-5 min across two independent backend restarts (2026-07-29, iter-31 dev handoff) —
+# worst observed ~300s. The FIRST cut of the guard shipped a 45s wait copied from
+# `forward_testing._FORWARD_AGG_WAIT_TIMEOUT_S` (a much faster compute): with 45s << 300s EVERY waiter would
+# have timed out mid-compute and started its own duplicate compute — the guard would have been inert
+# exactly where audit B5 needed it. The two tests below lock that in: the shipped constant against the
+# measured duration, and the de-dup behaviour across a compute that runs PAST the old 45s ceiling.
+_MEASURED_LIVE_COLD_MISS_S = 300.0
+_PRE_FIX_WAIT_TIMEOUT_S = 45.0
+_MAX_MEANINGFUL_WAIT_S = 60.0 * 60.0
+
+
+def test_shipped_factor_lab_all_wait_timeout_covers_the_measured_live_cold_miss_compute():
+    """iter-31 (review fix): the SHIPPED `_FACTOR_LAB_ALL_WAIT_TIMEOUT_S` must sit ABOVE the MEASURED live
+    cold-MISS compute duration (~300s worst observed), with headroom — otherwise a waiter gives up while the
+    owner is still legitimately computing and starts the duplicate compute audit B5 requires eliminated.
+    Same shipped-value-vs-live-measurement convention as
+    `test_shipped_factor_pool_max_observations_actually_covers_the_live_basis` above and
+    `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis` (`test_research_streaming.py`):
+    the REAL shipped constant, checked against a REAL measurement, not a fixture-sized proxy. The upper
+    bound keeps it a bounded wait rather than an effectively-infinite one (the failure path must stay
+    reachable within an hour, never a hang)."""
+    import app.engine.research as research
+
+    shipped = research._FACTOR_LAB_ALL_WAIT_TIMEOUT_S
+    assert shipped > _PRE_FIX_WAIT_TIMEOUT_S, (
+        f"_FACTOR_LAB_ALL_WAIT_TIMEOUT_S={shipped}s is back at (or below) the rejected pre-fix 45s value "
+        f"copied from forward_testing — it must be sized against THIS call's own compute duration"
+    )
+    assert shipped >= 2 * _MEASURED_LIVE_COLD_MISS_S, (
+        f"_FACTOR_LAB_ALL_WAIT_TIMEOUT_S={shipped}s leaves no margin over the measured live cold-MISS "
+        f"compute ({_MEASURED_LIVE_COLD_MISS_S}s, 2026-07-29): a waiter would time out mid-compute and "
+        f"start a duplicate compute (audit B5 regression). Require >= {2 * _MEASURED_LIVE_COLD_MISS_S}s."
+    )
+    assert shipped <= _MAX_MEANINGFUL_WAIT_S, (
+        f"_FACTOR_LAB_ALL_WAIT_TIMEOUT_S={shipped}s is so large the wait is no longer meaningfully bounded; "
+        f"the independent-compute fallback must stay reachable (<= {_MAX_MEANINGFUL_WAIT_S}s)"
+    )
+
+
+def test_factor_lab_all_single_flight_holds_across_a_compute_past_the_pre_fix_timeout(lab_engine):
+    """iter-31 (review fix), SLOW BY DESIGN (~48s): the de-dup must hold across a compute that lasts LONGER
+    than the rejected 45s wait — the property TC-3 above cannot prove, because its owner compute finishes in
+    milliseconds and never approaches the ceiling. The owner's compute here is stretched past the pre-fix
+    timeout with a real sleep while the SHIPPED wait constant is left untouched; the waiter must still be
+    waiting when the owner persists, so `compute_factor_lab_all` runs EXACTLY ONCE. Teeth: at the pre-fix
+    45s value the waiter would wake at 45s, find no persisted row, and compute independently — this test
+    would then observe 2 computes and fail. Real time is used deliberately (no patched clock, no scaled
+    proxy): the finding was that the constant was untested against a realistic duration."""
+    import time
+
+    import app.engine.research as research
+
+    cfg = load_config()
+    slow_compute_s = _PRE_FIX_WAIT_TIMEOUT_S + 3.0
+    hang_after_s = slow_compute_s + BOUNDED_TIMEOUT_S
+    owner_claimed = threading.Event()
+    call_count = {"n": 0}
+    real = research.compute_factor_lab_all
+
+    def _slow_compute(*args, **kwargs):
+        call_count["n"] += 1
+        owner_claimed.set()
+        time.sleep(slow_compute_s)  # stand-in for the real ~2-5 min live cold-MISS compute
+        return real(*args, **kwargs)
+
+    results: dict[str, dict] = {}
+
+    def _call(tag: str):
+        with Session(lab_engine) as session:
+            results[tag] = research.factor_lab_all_cached(session, cfg)
+
+    research.compute_factor_lab_all = _slow_compute
+    start = time.monotonic()
+    try:
+        owner_thread = threading.Thread(target=_call, args=("owner",))
+        owner_thread.start()
+        assert owner_claimed.wait(timeout=BOUNDED_TIMEOUT_S), "owner never entered the compute"
+        waiter_thread = threading.Thread(target=_call, args=("waiter",))
+        waiter_thread.start()
+        owner_thread.join(timeout=hang_after_s)
+        waiter_thread.join(timeout=hang_after_s)
+    finally:
+        research.compute_factor_lab_all = real
+    elapsed = time.monotonic() - start
+
+    assert not owner_thread.is_alive() and not waiter_thread.is_alive(), "a caller hung"
+    assert call_count["n"] == 1, (
+        f"compute_factor_lab_all ran {call_count['n']} times for one slow ({slow_compute_s}s) same-key "
+        f"MISS: the waiter's bounded wait elapsed BEFORE the owner finished and it started a duplicate "
+        f"compute — the single-flight guard is inert at this call's real compute duration (audit B5)"
+    )
+    assert elapsed < 2 * slow_compute_s, (
+        f"resolution took {elapsed:.1f}s for a single {slow_compute_s}s compute — the waiter serialised "
+        f"behind a SECOND compute instead of sharing the owner's result"
+    )
+    assert set(results) == {"owner", "waiter"}, "a caller returned nothing"
+    assert _bytes(results["waiter"]) == _bytes(results["owner"]), (
+        "the waiter's payload differs from the owner's for the same cache identity"
+    )
+
+
+def test_factor_lab_all_cached_waiter_does_not_deadlock_when_owner_raises(lab_engine):
+    """iter-31 TC-4 (audit B5): when the OWNER of a same-key MISS's in-flight computation raises, a
+    concurrent WAITING caller for that SAME key never blocks past the bounded timeout — it either raises its
+    own clean, isolated error or independently recomputes and returns a byte-identical payload. Mirrors
+    `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`. Proves the
+    single-flight fix's failure path cannot wedge a waiter (its `finally` releases the in-flight slot and
+    wakes waiters on ANY exit, success or failure)."""
+    import time
+
+    import app.engine.research as research
+
+    cfg = load_config()
+    owner_started = threading.Event()
+    owner_may_raise = threading.Event()
+    real = research.compute_factor_lab_all
+    call_count = {"n": 0}
+
+    def _owner_then_recover(*args, **kwargs):
+        call_count["n"] += 1
+        if call_count["n"] == 1:
+            owner_started.set()
+            owner_may_raise.wait(timeout=10)
+            raise RuntimeError("forced owner failure (iter-31 TC-4 probe)")
+        return real(*args, **kwargs)
+
+    owner_result: dict = {}
+    waiter_result: dict = {}
+
+    def _owner_call():
+        with Session(lab_engine) as session:
+            try:
+                research.factor_lab_all_cached(session, cfg)
+            except Exception as exc:  # noqa: BLE001 — captured for the assertion below, never swallowed
+                owner_result["error"] = exc
+
+    def _waiter_call():
+        with Session(lab_engine) as session:
+            try:
+                waiter_result["payload"] = research.factor_lab_all_cached(session, cfg)
+            except Exception as exc:  # noqa: BLE001
+                waiter_result["error"] = exc
+
+    research.compute_factor_lab_all = _owner_then_recover
+    start = time.monotonic()
+    try:
+        owner_thread = threading.Thread(target=_owner_call)
+        waiter_thread = threading.Thread(target=_waiter_call)
+        owner_thread.start()
+        assert owner_started.wait(timeout=10), "owner never claimed the in-flight slot"
+        waiter_thread.start()
+        time.sleep(0.2)  # let the waiter register as a non-owner before the owner is allowed to raise
+        owner_may_raise.set()
+        owner_thread.join(timeout=BOUNDED_TIMEOUT_S)
+        waiter_thread.join(timeout=BOUNDED_TIMEOUT_S)
+    finally:
+        research.compute_factor_lab_all = real
+    elapsed = time.monotonic() - start
+
+    assert not owner_thread.is_alive(), "owner thread did not finish — treat as a hang"
+    assert not waiter_thread.is_alive(), "waiter thread did not finish — treat as a hang"
+    assert elapsed < BOUNDED_TIMEOUT_S, f"resolution took {elapsed:.1f}s — treat as a hang, not a slow pass"
+    assert "error" in owner_result, "expected the owner's own forced exception to propagate to its caller"
+
+    assert "error" in waiter_result or "payload" in waiter_result, (
+        "the waiter neither raised a clean error nor returned a payload — the failure path is broken"
+    )
+    if "payload" in waiter_result:
+        with Session(lab_engine) as session:
+            direct = real(session, cfg)
+        assert _bytes(waiter_result["payload"]) == _bytes(direct), (
+            "waiter's fallback payload was not byte-identical to a direct compute"
+        )
+
+
+# ==================================================================================================
+# 6. iter-31 AUDIT — the two proofs the shipped suite was missing:
+#    (a) TC-6 as the phase spec actually words it ("observes the peak resident size of the RETURNED pools
+#        structure and asserts it is bounded — proven against the real run count, not a fixture-sized
+#        width"). The shipped `test_shipped_factor_pool_max_observations_actually_covers_the_live_basis`
+#        only range-checks a config INTEGER; it never looks at the returned structure at all, so a revert
... [diff_bound] apps/backend/tests/test_factor_lab_all.py: 152 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index 5559a3b4..a0bf48f7 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -518,21 +518,29 @@ def test_all_factor_observations_by_horizon_matches_per_factor_per_horizon(prune
     """For EVERY catalog factor and EVERY config horizon, the all-horizons shared pool's non-null subset at
     horizon h (with `max_drawdown` dropped — it rides additively) equals `_factor_observations(factor, h)`
     row-for-row on the discriminating reorder fixture (multi-horizon FRs, a non-subject symbol with FRs, a
-    factor-NULL column). Proves the one-sweep all-horizons read is byte-identical per (factor, horizon)."""
+    factor-NULL column). Proves the one-sweep all-horizons read is byte-identical per (factor, horizon).
+    iter-31: `_all_factor_observations_by_horizon` now returns the compact `(core_records, pools)` shape (a
+    return-value memory-representation redesign) — `core_records[core_idx]` is `(run_id, ticker, values)`
+    with `values` a TUPLE positioned by `factors` order (never a dict keyed by factor.key)."""
     cfg = load_config()
     factors = list(cfg.research.factor_lab.factors)
     horizons = list(cfg.walk_forward.horizons)
+    factor_index = {f.key: i for i, f in enumerate(factors)}
     with Session(prune_engine) as session:
-        pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
+        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
         for factor in factors:
+            idx = factor_index[factor.key]
             for h in horizons:
-                subset = [
-                    {"run_id": o["run_id"], "ticker": o["ticker"],
-                     "factor": float(o["values"][factor.key]), "return": o["return"],
-                     "max_drawdown": o["max_drawdown"], "regime": None}
-                    for o in pools[h]
-                    if o["values"][factor.key] is not None
-                ]
+                subset = []
+                for core_idx, ret, mdd in pools[h]:
+                    run_id, ticker, values = core_records[core_idx]
+                    factor_value = values[idx]
+                    if factor_value is None:
+                        continue
+                    subset.append({
+                        "run_id": run_id, "ticker": ticker, "factor": float(factor_value),
+                        "return": ret, "max_drawdown": mdd, "regime": None,
+                    })
                 per = _factor_observations(session, factor, h, as_of, cfg=cfg)
                 # compare on the shared keys (the all-horizons pool carries no per-obs regime label, which
                 # compute_factor_lab_all does not use); assert the factor/return/max_drawdown identity.
diff --git a/config.yaml b/config.yaml
index 26ba6f96..c5bbb01b 100644
--- a/config.yaml
+++ b/config.yaml
@@ -900,6 +900,19 @@ research:
   # pagination is a pure client-side view transform; this is the SINGLE source of the 30-rows/page
   # constant (served in the lab payload so the frontend reads it — no `30` literal in research.py).
   regime_phase_factor_page_size: 30
+  # ops-hardening iter-31 (AG-8, J-06/J-07) — per-horizon observation-count SOFT CEILING for the
+  # all-factors Factor-Lab view's RETURN VALUE (`_all_factor_observations_by_horizon`'s `pools[h]` —
+  # `research.py:583`'s fill site, the live MemoryError frame iter-29/iter-30 both deferred). A DIFFERENT
+  # unit from `factor_join_run_chunk` (a run-count accumulator width) and `read_batch_size` (a row-count
+  # yield_per probe) — never reuse either here (the iter-29 unit-confusion lesson). Measured live basis
+  # (2026-07-29, apps/backend/data/trendora.db, ~4.97 GB): per-horizon forward_returns/pool sizes range
+  # 771,629 (h=60) to 804,372 (h=1) across the 5 configured horizons (781,965 scanner_results total,
+  # 781,417 with a realized return at >=1 horizon). The REAL memory fix is the compact per-observation
+  # encoding (a dedup'd core-record table + small per-horizon tuples, replacing 5x parallel Python
+  # dict-lists) — this ceiling is an AG-8 disclosure net: set with ~2.5x headroom above today's live max so
+  # normal operation never trips it, but a future data-scale widening logs a WARNING (never raises, never
+  # truncates a payload) instead of silently repeating this crash at a larger scale. Boot-validated >= 1.
+  factor_pool_max_observations: 2000000
   factor_lab:
     deciles: 10
     factors:
```
