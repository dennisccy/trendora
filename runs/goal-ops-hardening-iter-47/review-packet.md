# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 12. Shown in full: 12.

```diff
diff --git a/apps/backend/app/engine/evidence.py b/apps/backend/app/engine/evidence.py
index d21ff81c..3b692014 100644
--- a/apps/backend/app/engine/evidence.py
+++ b/apps/backend/app/engine/evidence.py
@@ -158,14 +158,20 @@ def build_evidence_payload(
         if session is not None:
             # lazy import — app.engine.forward_testing sits BELOW this module in the dependency graph
             # (this module never imported it before), so a module-level import is safe here; kept lazy
-            # anyway so the session-less (majority of existing) call sites pay no import cost. The CACHED
-            # entry point (not the pure `compute_drawdown_expectations`) — /api/evidence renders EVERY
-            # claim's panel on one page load, so an uncached per-claim cohort resolution multiplies the
-            # J-15 latency budget by the claim count (see the cache's own docstring for the measurement).
-            from app.engine.forward_testing import compute_drawdown_expectations_cached
+            # anyway so the session-less (majority of existing) call sites pay no import cost. The
+            # SERVING wrapper (ops-hardening iter-47, audit B2) — not the plain cached entry point —
+            # because /api/evidence renders EVERY claim's panel on one page load: an uncached per-claim
+            # cohort resolution multiplies the J-15 latency budget by the claim count, and a cache MISS
+            # caused by an UNRELATED concurrent ingest (any new forward_returns row bumps every claim's
+            # dataset-version stamp) must never fall onto that same multi-minute cold-recompute tail — the
+            # wrapper serves the last-good generation behind an honest `expectations_status: "refreshing"`
+            # label instead, while a background re-warm catches up (see the wrapper's own docstring).
+            from app.engine.forward_testing import compute_drawdown_expectations_cached_with_status
 
             try:
-                expectations = compute_drawdown_expectations_cached(session, row["claim"], config)
+                expectations, status = compute_drawdown_expectations_cached_with_status(
+                    session, row["claim"], config
+                )
             except MemoryError as exc:
                 # isolate-and-continue (AG-8): unlike the ingest warm loop's break-on-MemoryError, a live
                 # `/evidence` response must still render every OTHER claim — never abort the rest of the
@@ -184,6 +190,11 @@ def build_evidence_payload(
             else:
                 if expectations is not None:
                     row["expectations"] = expectations
+                    # additive ONLY when a previous generation is being served (ops-hardening iter-47) —
+                    # mirrors the "unavailable" convention above: a claim serving its CURRENT generation
+                    # carries no status key at all (TC-3: "expectations_status absent or 'ready'").
+                    if status == "refreshing":
+                        row["expectations_status"] = "refreshing"
         claims.append(row)
         signal = row["signal"]
         if row["proven"] and signal:
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 62d51885..7dc1ed7e 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -2267,21 +2267,66 @@ def _loss_streak_cell(dated_returns: list[tuple], floor: int) -> dict:
     return {"value": _longest_negative_streak(ordered), "n": n, "insufficient": False}
 
 
+# ops-hardening iter-47 FIX PASS (audit finding B7): SQLite's SQLITE_LIMIT_VARIABLE_NUMBER is 32,766 on
+# this host's 3.53.1, but only 999 on builds predating 3.32 — an `IN (…)` list sized by the DATA (a
+# claim's snapshot dates, which grow as history deepens) must not silently depend on that. Every
+# date IN-list below is emitted in batches of this many binds.
+_MAX_IN_PARAMS = 900
+
+
 def _drawdown_ticker_slice_map(
     session: Session, horizon: int, slice_tickers: list[str], batch: int,
+    dates_by_ticker: Optional[dict] = None,
 ) -> dict[tuple[str, str], tuple]:
     """ops-hardening iter-46 (AG-8): the `(symbol, asof_date_iso) -> (max_drawdown, underwater_days,
     time_to_recover_days)` read for ONE bounded SLICE of tickers — `compute_drawdown_expectations`'s chunk
     axis (`research.drawdown_expectations_ticker_chunk`), mirroring `research.py`'s `_fr_slice_map`. A
     named function (not an inlined loop body) so a test can wrap/instrument it to observe the live
-    per-slice size directly (TC-2)."""
-    fr_stmt = select(
+    per-slice size directly (TC-2).
+
+    ops-hardening iter-47 (AG-8, iter-46 audit B4): `dates_by_ticker` (`{ticker: frozenset[date]}`,
+    OPTIONAL — `None` preserves the pre-iter-47 unfiltered read byte-for-byte, the default every OTHER
+    caller/test still gets) scopes the read to exactly the `(symbol, asof_date)` pairs the caller's lookup
+    loop will ever ask for via `stored_by_key.get((ticker, date_iso))`. PROVABLY byte-identical, never a
+    freshness compromise: every row this filter excludes is a pair the loop would never have queried
+    anyway (a stored ForwardReturn at this horizon/symbol on a date OUTSIDE that ticker's own resolved
+    cohort dates is simply never read), and every pair it WILL ask for is included by construction —
+    the map is built from the very rows the loop iterates.
+
+    ops-hardening iter-47 FIX PASS (audit finding B2): the filter first shipped as ONE date set per
+    50-ticker CHUNK — the UNION of the chunk's cohort dates. On an all-history decile cohort that union is
+    nearly the whole snapshot history, so the bound bound almost nothing: measured live, it removed 4.4 %
+    of rows on the flagship `leadership_score` D10 h=20 claim (2,812 of 2,869 dates survived the union).
+    That is the same "bound sized against the wrong axis" shape `_factor_observations`' own docstring
+    records from iter-29. Scoping is now PER TICKER — each ticker is read with only its OWN cohort dates,
+    the axis the lookup key is actually built on. The iter-46 audit measured the UNFILTERED read at
+    7,994,388 rows across 71 calls to serve 7 live claims; the per-ticker reduction is measured and
+    recorded in `reports/perf-budgets.md` Item P (TC-5)."""
+    stored_by_key: dict[tuple[str, str], tuple] = {}
+    cols = (
         ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
         ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
-    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(slice_tickers))
-    stored_by_key: dict[tuple[str, str], tuple] = {}
-    for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).yield_per(batch):
-        stored_by_key[(symbol, asof_date.isoformat())] = (mdd, uw, ttr)
+    )
+    if dates_by_ticker is None:
+        fr_stmt = select(*cols).where(
+            ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(slice_tickers)
+        )
+        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).yield_per(batch):
+            stored_by_key[(symbol, asof_date.isoformat())] = (mdd, uw, ttr)
+        return stored_by_key
+    for ticker in slice_tickers:
+        ticker_dates = dates_by_ticker.get(ticker)
+        if not ticker_dates:
+            continue  # this ticker contributes no cohort row -> no key of its will ever be looked up
+        ordered_dates = sorted(ticker_dates)
+        for i in range(0, len(ordered_dates), _MAX_IN_PARAMS):
+            fr_stmt = select(*cols).where(
+                ForwardReturn.horizon == horizon,
+                ForwardReturn.symbol == ticker,
+                ForwardReturn.asof_date.in_(ordered_dates[i: i + _MAX_IN_PARAMS]),
+            )
+            for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).yield_per(batch):
+                stored_by_key[(symbol, asof_date.isoformat())] = (mdd, uw, ttr)
     return stored_by_key
 
 
@@ -2378,9 +2423,25 @@ def compute_drawdown_expectations(
     by_phase_ttr: dict[str, list[float]] = defaultdict(list)
     by_phase_returns: dict[str, list[tuple]] = defaultdict(list)
 
+    # ops-hardening iter-47 (AG-8, iter-46 audit B4) + FIX PASS (audit B2): scope each ticker's read to
+    # exactly ITS OWN cohort dates — the only keys `stored_by_key.get((ticker, date_iso))` below will ever
+    # ask for — narrowing `_drawdown_ticker_slice_map`'s query without touching a single served value
+    # (provably byte-identical: an excluded row's key is never looked up either way). Built ONCE here, not
+    # per chunk: the date objects are interned through `_dates` so the whole map costs one object per
+    # distinct snapshot date, not one per cohort row. The first shipped version of this filter used the
+    # per-CHUNK UNION of these sets, which on an all-history cohort is nearly the full snapshot history
+    # and removed only 4.4 % of rows (audit B2) — the union axis is not the axis the lookup key uses.
+    _dates: dict[str, date_cls] = {}
+    dates_by_ticker: dict[str, frozenset] = {}
+    for ticker, ticker_rows in rows_by_ticker.items():
+        dates_by_ticker[ticker] = frozenset(
+            _dates.setdefault(row["snapshot_date"], date_cls.fromisoformat(row["snapshot_date"]))
+            for row in ticker_rows
+        )
+
     for i in range(0, len(tickers), chunk_width):
         chunk = tickers[i : i + chunk_width]
-        stored_by_key = _drawdown_ticker_slice_map(session, horizon, chunk, read_batch)
+        stored_by_key = _drawdown_ticker_slice_map(session, horizon, chunk, read_batch, dates_by_ticker)
 
         # fold THIS chunk's rows into the by-phase accumulators immediately, then let `stored_by_key`
         # go out of scope (rebound next iteration) before the next chunk's query starts (TC-2's bound).
@@ -2513,3 +2574,154 @@ def compute_drawdown_expectations_cached(
     except Exception:  # a concurrent writer raced us to the same key — best-effort cache, not a source of
         session.rollback()  # truth; the freshly computed payload is still byte-identical, so return it
     return payload
+
+
+# --- serve-stale-behind-a-label (ops-hardening iter-47, audit B2) ---------------------------------------
+# The iter-46 audit's own recommended fix: `compute_drawdown_expectations_cached`'s stamp is the GLOBAL
+# `_dataset_version` (`r{max(scanner_runs.id)}-f{count(forward_returns)}`, research.py:1705), which folds
+# in EVERY forward_returns row in the DB — not only rows relevant to a given claim's own cohort. A single
+# ingest can therefore invalidate ALL 7 live claims' cache rows at once, forcing the NEXT `/api/evidence`
+# request onto the ~163s-idle / >300s-loaded cold-recompute tail this whole cache exists to avoid.
+#
+# A cohort-scoped (narrower) cache key was investigated first, per the phase spec's own preference — but a
+# claim's cohort (tickers) is data-DERIVED (5 of the 7 live claims are factor-decile cohorts: "the top
+# decile of leadership_score", not an explicit ticker list), so determining "this claim's own relevant
+# rows" requires resolving the cohort — the SAME expensive `compute_samples` call this cache exists to
+# avoid paying synchronously. A cheaper HORIZON-only-scoped stamp was also examined: it is provably safe
+# (a forward_returns row at a horizon a claim never reads genuinely cannot affect that claim's output —
+# `compute_samples(horizon=...)` and `_drawdown_ticker_slice_map(horizon=...)` both filter by horizon
+# exclusively), but it does not close the REAL production scenario this iteration must fix: every
+# `walk_forward.underwater_horizons` value (`config.yaml`) already equals every configured forward-return
+# horizon, and a single ingest day's `_do_backfill` computes forward returns across the FULL configured
+# horizon set for the tickers it touches — so a horizon-only-scoped stamp still invalidates on almost any
+# real ingest, same as the unscoped one, while adding a second stamp function to maintain. Serving the
+# previous generation behind an honest label — this iteration's shipped fix — is the ONLY option that
+# provably satisfies "answers within budget during a concurrent heavy ingest" (TC-3) regardless of which
+# rows changed, and it has a direct, already-registered precedent (`/backtest`'s
+# `evidence_status: "ready"|"refreshing"|"not_yet_computed"`, `apps/frontend/app/backtest/page.tsx`).
+#
+# CONTRACT: on a HIT for the CURRENT dataset version, behavior is UNCHANGED — `(payload, "ready")`, the
+# SAME payload `compute_drawdown_expectations_cached` alone would return. On a MISS, if a PREVIOUS
+# generation's row still exists for this exact claim, it is served IMMEDIATELY as `(payload, "refreshing")`
+# — never mixed with the incoming generation's fields (TC-3's no-generation-mixing requirement: the served
+# payload is ALWAYS exactly one EventStudyCache row's `payload_json`, deserialized whole, never merged) —
+# while a SINGLE-FLIGHT background thread (mirrors `warmup.py`'s own `_WARMUP_LOCK`/`_WARMUP_THREAD`
+# convention) re-warms EVERY claim on the ledger on its OWN session, pruning each stale row when its new
+# generation lands (the SAME prune-then-insert `compute_drawdown_expectations_cached` already does). When
+# NO prior generation exists at all (first-ever resolution for this claim — normally pre-empted by the boot
+# warm), falls back to the synchronous cached compute, unchanged, returning `(payload, "ready")` — there is
+# nothing honest to serve in its place, so the ORIGINAL cold-compute contract stands.
+#
+# ONE GLOBAL worker, not one per claim (live-drilled 2026-08-04): a single unrelated forward_returns row
+# invalidates ALL 7 live claims' cache rows at once (this is exactly the bug being fixed), so the FIRST
+# implementation spawned ONE re-warm thread PER stale claim — up to 7 concurrent CPU-bound Python threads
+# fighting over the GIL, measurably slowing `/api/evidence` and `/api/health` far more than the ORIGINAL
+# single-threaded sequential boot warm ever did (confirmed live: `/api/health` degraded from ~0.1s to
+# 0.1-0.4s under the 7-thread swarm — still within the relaxed bounded-compute-window budget, but needless
+# self-inflicted GIL contention). The single-flight key is now a GLOBAL sentinel (never per-claim), and the
+# spawned worker calls `warmup._warm_drawdown_expectations` (lazy import — `warmup.py` imports this module,
+# so a module-level import back would be circular; this mirrors the file's other lazy imports) — the SAME
+# sequential, ledger-driven, per-claim-isolated loop the boot warm already uses, so a burst of concurrent
+# MISSes across every stale claim collapses into ONE background worker doing the SAME efficient sequential
+# work the boot warm always did, instead of N threads duplicating and contending with each other.
+_REWARM_LOCK = threading.Lock()
+_REWARM_IN_FLIGHT = False
+_REWARM_WORKER_NAME = "dd-expectations-rewarm"
+
+
+def _spawn_drawdown_expectations_rewarm(cfg: Config) -> None:
+    """Single-flight background re-warm (GLOBAL, not per-claim — see the module note above): re-warms
+    EVERY claim on the evidence ledger via `warmup._warm_drawdown_expectations`, on its OWN engine/session,
+    never blocking the caller. A re-warm already in flight (from an earlier stale request, for ANY claim)
+    means a NEW stale request never spawns a second worker — it simply keeps serving its own last-good
+    generation until the one in-flight worker settles ALL claims, including this one. NON-FATAL end to end
+    — a failed re-warm (including a failure to even START the thread, mirroring `data_manager.py`'s own
+    `RuntimeError`/`MemoryError` dual-exit guard on `Thread.start()`) simply leaves every stale claim
+    serving its last-good generation until the NEXT miss retries; it never surfaces to the request that
+    triggered it (that request already returned its own response)."""
+    global _REWARM_IN_FLIGHT
+    with _REWARM_LOCK:
+        if _REWARM_IN_FLIGHT:
+            return  # a re-warm is already running (for every stale claim, not just this one) — no duplicate
+        _REWARM_IN_FLIGHT = True
+
+    def _run() -> None:
+        from app.engine import data_manager  # lazy — avoids a module-load-time cycle (this module's convention)
+        global _REWARM_IN_FLIGHT
+        try:
+            from app.db import get_engine
+            from app.engine import warmup  # lazy — warmup.py imports THIS module; see the module note above
+
+            warmup._warm_drawdown_expectations(get_engine(), cfg)
+        except Exception as exc:  # noqa: BLE001 — NON-FATAL: never let a background re-warm crash the process
+            data_manager._log_isolation_failure(
+                "evidence drawdown-expectations background re-warm failed (non-fatal): %r", exc,
+            )
+        finally:
+            with _REWARM_LOCK:
+                _REWARM_IN_FLIGHT = False
+
+    try:
+        threading.Thread(target=_run, daemon=True, name=_REWARM_WORKER_NAME).start()
+    except Exception as exc:  # noqa: BLE001 — mirrors data_manager.py's Thread.start() dual-exit guard
+        from app.engine import data_manager
+
+        data_manager._log_isolation_failure(
+            "evidence drawdown-expectations background re-warm could not START: %r", exc,
+        )
+        with _REWARM_LOCK:
+            _REWARM_IN_FLIGHT = False
+
+
+def compute_drawdown_expectations_cached_with_status(
+    session: Session, claim: dict, config: Optional[Config] = None,
+) -> tuple[Optional[dict], str]:
+    """The `/api/evidence` SERVING entry point (ops-hardening iter-47, audit B2) — wraps
+    `compute_drawdown_expectations_cached` with the serve-stale-behind-a-label contract documented in the
+    module note above. Returns `(payload, status)` where `status` is `"ready"` (current-version HIT, or
+    the cold-start fallback) or `"refreshing"` (a previous generation served while a background re-warm
+    completes). `status` is a SERVING-layer concept only — it is never persisted inside
+    `EventStudyCache.payload_json`, so the underlying cached compute stays byte-identical either way."""
+    cfg = config or get_config()
+    horizon = claim.get("horizon")
+    if horizon not in cfg.walk_forward.underwater_horizons:
+        return None, "ready"
+
+    from app.engine.research import _dataset_version  # lazy — see this module's existing lazy-import note
+
+    subject = _drawdown_expectations_cache_subject(claim)
+    version = _dataset_version(session)
+
+    hit = session.exec(
+        select(EventStudyCache).where(
+            EventStudyCache.subject == subject,
+            EventStudyCache.view == _DD_EXPECTATIONS_VIEW,
+            EventStudyCache.asof_key == _DD_EXPECTATIONS_ASOF_KEY,
+            EventStudyCache.dataset_version == version,
+            EventStudyCache.horizon == horizon,
+        )
+    ).first()
+    if hit is not None:
+        return json.loads(hit.payload_json), "ready"
+
+    # MISS at the current version — serve the most recent PRIOR generation (if any) instead of paying the
+    # cold compute on this request. `created_at DESC` picks the newest stale row when more than one exists
+    # (there is normally at most one — see the module note's prune-then-insert contract).
+    stale = session.exec(
+        select(EventStudyCache)
+        .where(
+            EventStudyCache.subject == subject,
+            EventStudyCache.view == _DD_EXPECTATIONS_VIEW,
+            EventStudyCache.asof_key == _DD_EXPECTATIONS_ASOF_KEY,
+            EventStudyCache.horizon == horizon,
+        )
+        .order_by(EventStudyCache.created_at.desc())
+    ).first()
+
+    if stale is None:
+        # nothing to serve stale (first-ever resolution for this claim) — fall back to the synchronous
+        # cached compute exactly as before this iteration (normally pre-empted by the boot warm).
+        return compute_drawdown_expectations_cached(session, claim, cfg), "ready"
+
+    _spawn_drawdown_expectations_rewarm(cfg)
+    return json.loads(stale.payload_json), "refreshing"
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index 9f53baf4..11bdefad 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -326,6 +326,236 @@ def _factor_observations(
     return observations
 
 
+def _decile_population_upper_bound(session: Session, runs_with_fr: list[int], run_chunk: int) -> int:
+    """ops-hardening iter-47 FIX PASS (audit B3): a PROVEN upper bound on the number of observations
+    `_factor_decile_observations`' PASS 1 can produce, read with COUNT-only queries (no row is
+    materialized, no factor is extracted).
+
+    The bound is the number of `ScannerResult` rows in the SAME runs PASS 1 walks. It is airtight by
+    construction rather than by a data property: PASS 1 iterates exactly those rows and appends AT MOST
+    one key per row (it can only skip — no forward return at this horizon, or a factor-NULL value), so
+    `n <= this count` always holds, whatever the join multiplicity or the null density. Measured on the
+    live basis (h=20, all history): 1,260,994 vs an actual population of 1,251,211 — 0.8 % slack, 0.03 s.
+
+    Chunked over the SAME `run_chunk` width the two data passes use, so the `IN (…)` bind-parameter count
+    per query stays exactly as bounded as theirs (audit B7)."""
+    total = 0
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        total += int(session.exec(
+            select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id.in_(slice_run_ids))
+        ).one())
+    return total
+
+
+class _BoundedRankWindow:
+    """ops-hardening iter-47 FIX PASS (audit B3): the bounded retention window `_factor_decile_observations`
+    PASS 1 streams into, replacing its whole-population `sort_keys` list + whole-population sort.
+
+    The final answer is `all_keys_sorted[lo:hi]` with `lo = (d-1)*n//count`, `hi = d*n//count`. Only two
+    prefixes of the total order can contain that slice: the `hi` SMALLEST keys, or the `n - lo` LARGEST.
+    Both are computable from an UPPER bound on `n` alone, because both are non-decreasing in `n`:
+    `hi(n) <= hi(n_max)` and `n - lo(n) <= n_max - lo(n_max)`. So the narrower of the two is a capacity
+    this window can commit to BEFORE the first key arrives, and every key outside it is provably
+    non-surviving and is dropped during the walk.
+
+    Retention is bounded by `2 x capacity` (a sort-and-truncate buffer, trimmed back to `capacity`
+    whenever it doubles — amortized O(n log capacity), the same total comparison count the single
+    whole-population sort paid). For the live decile-10 claims that is ~252 K tuples at peak instead of
+    ~1.25 M, and the bound now scales with the REQUESTED DECILE's own member count — the size of the value
+    the caller must return anyway — not with the population.
+
+    Byte-identical by construction: the retained keys are ordered with the IDENTICAL plain tuple ordering
+    (`(factor, ticker, run_id)`, the same key `sorted()` used), and (ticker, run_id) is unique per
+    observation, so the total order is strict and "the k smallest/largest" is a unique set — the surviving
+    window contains the target slice with the same members in the same order the whole-population sort
+    produced."""
+
+    __slots__ = ("_capacity", "_keep_smallest", "_buf", "_trim_at")
+
+    def __init__(self, n_max: int, deciles_count: int, decile: int) -> None:
+        lo_max = (decile - 1) * n_max // deciles_count
+        hi_max = decile * n_max // deciles_count
+        keep_smallest_cap = hi_max
+        keep_largest_cap = n_max - lo_max
+        self._keep_smallest = keep_smallest_cap <= keep_largest_cap
+        self._capacity = max(1, min(keep_smallest_cap, keep_largest_cap))
+        self._buf: list[tuple[float, str, int]] = []
+        self._trim_at = 2 * self._capacity
+
+    def add(self, key: tuple[float, str, int]) -> None:
+        self._buf.append(key)
+        if len(self._buf) >= self._trim_at:
+            self._trim()
+
+    def _trim(self) -> None:
+        self._buf.sort()
+        if self._keep_smallest:
+            del self._buf[self._capacity:]
+        else:
+            del self._buf[: max(0, len(self._buf) - self._capacity)]
+
+    def slice(self, n: int, lo: int, hi: int) -> "Optional[list[tuple[float, str, int]]]":
+        """The retained keys occupying global ranks `[lo, hi)`, or None when the requested window is not
+        fully inside what was retained (the caller then degrades to the exact unbounded computation —
+        unreachable when `n <= n_max`, see the class docstring's monotonicity argument)."""
+        self._trim()
+        base = 0 if self._keep_smallest else n - len(self._buf)
+        if lo < base or hi - base > len(self._buf) or lo > hi:
+            return None
+        return self._buf[lo - base: hi - base]
+
+
+def _factor_decile_observations(
+    session: Session, factor, horizon: int, as_of: Optional[date_cls], deciles_count: int, decile: int,
+    *, cfg: Optional[Config] = None,
+) -> list[dict]:
+    """ops-hardening iter-47 (AG-8, iter-46 audit B3): bounded ONE-decile member resolution for
+    `app.engine.samples._factor_samples`'s "decile" branch — the SAME result
+    `_decile_member_slice(sorted(_factor_observations(session, factor, horizon, as_of), key=lambda o:
+    (o["factor"], o["ticker"], o["run_id"])), deciles_count, decile)` would produce, without ever holding
+    the FULL population's per-observation dicts in memory at once.
+
+    WHY: correctly ranking a decile needs every observation's factor value (a population-wide rank), but
+    does NOT need retaining every observation's OTHER fields (ticker/return/max_drawdown/regime) for the
+    ~(deciles_count-1)/deciles_count of the population that lands OUTSIDE the requested decile. The
+    pre-fix `_factor_samples` built the FULL 6-field dict for every observation at a horizon (up to
+    ~800K-observation pools measured live) just to discard 9/10 of them after sorting — reached via
+    `evidence.py` -> `compute_drawdown_expectations_cached` -> `compute_drawdown_expectations` ->
+    `compute_samples` -> `_factor_samples` for every decile-scoped certified claim (5 of the 7 live
+    claims), and independently caught `MemoryError`-ing at `logs/backend.log` 2026-08-04 02:20:31.
+
+    TWO bounded passes over the SAME chunked `_runs_with_fr` / `_fr_slice_map` join `_factor_observations`
+    (its unbounded sibling) uses — byte-identical row discovery, same fr/factor-NULL exclusion rules:
+
+      PASS 1 (lightweight): walks the SAME `runs_with_fr` chunk loop, but accumulates ONLY the
+        `(factor_value, ticker, run_id)` triple per observation — the exact three fields the tie-break
+        sort key reads — discarding each chunk's join map before the next (same bound
+        `_factor_observations` already applies to the join map; this ALSO avoids ever building the
+        heavier 6-field dict for the ~90% of observations that will not survive the decile slice). Sorting
+        this lightweight list with the IDENTICAL key, then slicing with the IDENTICAL
+        `_decile_member_slice` boundary arithmetic (`lo = (decile-1)*n//deciles_count`,
+        `hi = decile*n//deciles_count`, `n` = the total observation count — identical by construction,
+        since this pass walks the SAME chunk loop under the SAME exclusion rules), yields the EXACT
+        `(run_id, ticker)` key set the unbounded computation would have selected for this decile.
+      PASS 2 (bounded): re-walks the SAME chunk loop, rebuilding the FULL `_factor_observations`-shaped
+        dict per observation, but KEEPS it only when its `(ticker, run_id)` is in PASS 1's target-decile
+        key set — every other observation is discarded immediately, before the next chunk's query even
+        starts. Peak live size is bounded by (one chunk's join map + the target decile's member count),
+        never by the population.
+
+    Two DB passes trade CPU/IO for bounded memory — the SAME trade-off `compute_drawdown_expectations`'s
+    iter-46 fix already accepted for its own by-phase accumulators. Returns the SAME dict shape
+    `_factor_observations` returns (`run_id`, `ticker`, `factor`, `return`, `max_drawdown`, `regime`),
+    already restricted to ONE decile, sorted by the SAME ascending-by-factor tie-break so iterating this
+    return value in order reproduces the SAME sequence `_decile_member_slice` would have handed back
+    (byte-identical, TC-4).
+
+    ops-hardening iter-47 FIX PASS (audit finding B3): PASS 1's own `sort_keys` accumulator used to retain
+    ONE tuple per observation for the WHOLE population (~1.25 M tuples ≈ 155 MB on today's basis) and then
+    sort it whole — a bounded READ with unbounded RETENTION, the exact shape iter-40's lesson names, and
+    the reason the audit judged `samples.py:156` "reduced, not bounded". PASS 1 now retains a bounded
+    WINDOW instead (`_BoundedRankWindow` below): the only keys that can survive the final `[lo:hi]` slice
+    are either the `hi` smallest or the `n - lo` largest, whichever side is narrower, so everything else
+    can be discarded DURING the walk. Peak retention is therefore O(the requested decile's own member
+    count) — the size of the value this function must return anyway — instead of O(population)."""
+    parsed = parse_factor_source(factor.source)
+    research_cfg = (cfg or get_config()).research
+    batch = research_cfg.read_batch_size
+    run_chunk = research_cfg.factor_join_run_chunk
+
+    runs_with_fr = _runs_with_fr(session, [horizon], as_of)
+
+    # PASS 0 (count-only, no rows materialized) — the retention window PASS 1 may size itself against.
+    # See `_decile_population_upper_bound`: provably >= the observation count, measured at 0.03 s / 0.8%
+    # slack on the live basis.
+    n_max = _decile_population_upper_bound(session, runs_with_fr, run_chunk)
+    window = _BoundedRankWindow(n_max, deciles_count, decile)
+
+    # PASS 1 — lightweight (factor, ticker, run_id) sort keys only; the join map + ScannerResult stream are
+    # chunk-and-discarded exactly like `_factor_observations`, and the accumulator here never carries the
+    # heavier return/max_drawdown/regime fields a non-surviving 9/10 of the population would otherwise pay.
+    # `window.add` additionally discards, as it walks, every key that cannot land in the target decile.
+    n = 0
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult)
+            .where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            if (res.run_id, res.ticker) not in ret_by_run_symbol:
+                continue
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                continue  # factor-NULL observation EXCLUDED (never bucketed) — mirrors _factor_observations
+            n += 1
+            window.add((float(value), res.ticker, res.run_id))
+
+    lo = (decile - 1) * n // deciles_count
+    hi = decile * n // deciles_count
+    ranked = window.slice(n, lo, hi)
+    if ranked is None:
+        # UNREACHABLE by construction (`_decile_population_upper_bound` returns a proven upper bound, and
+        # `_BoundedRankWindow` sizes its capacity from it) — but a wrong slice would be a WRONG SERVED
+        # NUMBER (AG-3), so if the invariant is ever violated this degrades to the exact unbounded
+        # computation instead of returning a silently-truncated decile. Covered by a dedicated test that
+        # forces the violation with a deliberately too-small upper bound.
+        logger.warning(
+            "factor decile window underflow (n=%s lo=%s decile=%s/%s, upper bound %s) — "
+            "falling back to the unbounded exact computation",
+            n, lo, decile, deciles_count, n_max,
+        )
+        ordered = sorted(
+            _factor_observations(session, factor, horizon, as_of, cfg=cfg),
+            key=lambda o: (o["factor"], o["ticker"], o["run_id"]),
+        )
+        return _decile_member_slice(ordered, deciles_count, decile)
+    target_keys = {(ticker, run_id) for _factor_val, ticker, run_id in ranked}
+
+    if not target_keys:
+        return []
+
+    run_rows = (
+        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    regime_by_run = {run.id: run.regime_label for run in run_rows}
+
+    # PASS 2 — bounded: rebuild the FULL observation dict only for this decile's (ticker, run_id) keys.
+    members: list[dict] = []
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult)
+            .where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            if (res.ticker, res.run_id) not in target_keys:
+                continue  # not a member of the target decile — discarded immediately, never retained
+            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+            if fr is None:
+                continue
+            realized, max_drawdown = fr
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                continue
+            members.append({
+                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+                "max_drawdown": max_drawdown,
+                "regime": regime_by_run.get(res.run_id),
+            })
+
+    # sort the bounded members by the SAME ascending-by-factor tie-break (pass-2's own chunk order is
+    # (run_id, id) — NOT the factor-ascending order the decile slice is defined in).
+    members.sort(key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
+    return members
+
+
 def _decile_member_slice(ordered: list[dict], count: int, decile: int) -> list[dict]:
     """The EXACT `ordered[lo:hi]` member slice the `_deciles` aggregate assigns to a 1-based `decile`
     (D1…D`count`). The lo/hi quantile edges are the SAME integer-arithmetic boundaries `_deciles` uses
diff --git a/apps/backend/app/engine/samples.py b/apps/backend/app/engine/samples.py
index 333e446a..858efc41 100644
--- a/apps/backend/app/engine/samples.py
+++ b/apps/backend/app/engine/samples.py
@@ -56,6 +56,7 @@ from app.engine.research import (
     _downtrend_member_dimension_value,
     _downtrend_opportunity_observation_set,
     _event_study_observation_set,
+    _factor_decile_observations,
     _factor_observations,
     _assign_triple_deciles,
     _phase_severity_lab_observation_set,
@@ -142,26 +143,29 @@ def _factor_samples(
             f"unknown factor {factor_key!r}; valid factors are {[f.key for f in fl.factors]}"
         )
 
-    observations = _factor_observations(session, factor, horizon, as_of)
-
-    if slice_kind == "total":
-        members = observations
-    elif slice_kind == "decile":
+    if slice_kind == "decile":
         if decile is None or not (1 <= decile <= fl.deciles):
             raise ValueError(
                 f"decile {decile!r} out of range [1, {fl.deciles}] for a factor decile cohort"
             )
-        # the SAME ascending-by-factor ordering + deterministic tie-break compute_factor_lab uses, then
-        # the SAME quantile-edge slice — so this decile's member list reproduces the aggregate's n exactly.
-        ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
-        members = _decile_member_slice(ordered, fl.deciles, decile)
+        # ops-hardening iter-47 (AG-8, iter-46 audit B3): bounded two-pass decile resolution — see
+        # `research._factor_decile_observations`'s docstring. Byte-identical to
+        # `_decile_member_slice(sorted(_factor_observations(...), key=lambda o: (o["factor"], o["ticker"],
+        # o["run_id"])), fl.deciles, decile)` (proven by a pinned-reference test), without ever
+        # materializing the population's full per-observation dict list — this is the decile-scoped
+        # branch every drawdown-expectations factor claim (5 of 7 live certified claims) exercises via
+        # `compute_drawdown_expectations`, and the ONLY branch the iter-46 audit's live `MemoryError`
+        # traced through.
+        members = _factor_decile_observations(session, factor, horizon, as_of, fl.deciles, decile, cfg=cfg)
+    elif slice_kind == "total":
+        members = _factor_observations(session, factor, horizon, as_of)
     elif slice_kind == "regime":
         if regime is None or regime not in cfg.regime.labels:
             raise ValueError(
                 f"regime {regime!r} is not a configured regime label {list(cfg.regime.labels)}"
             )
         # the SAME stored-regime grouping `_regime_effectiveness` uses (regime read verbatim, never recomputed)
-        members = [o for o in observations if o["regime"] == regime]
+        members = [o for o in _factor_observations(session, factor, horizon, as_of) if o["regime"] == regime]
     else:
         raise ValueError(f"unknown factor slice {slice_kind!r}; valid slices are {list(_FACTOR_SLICES)}")
 
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index 1e42db48..57a18558 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -202,14 +202,18 @@ def _warm_drawdown_expectations(engine: Engine, cfg: Config) -> None:
                 # distinctly from the generic per-claim continue below, and tested against a TEXTLESS
                 # `MemoryError` (`str(MemoryError())` is `""`).
                 except MemoryError as exc:
-                    logger.exception(
+                    # ops-hardening iter-47 (carried from iter-44/45/46): `_log_isolation_failure`, NOT a
+                    # bare `logger.exception` — under the SAME exhausted `ulimit -v` cap that raised this
+                    # `MemoryError`, rendering the full traceback can itself allocate and raise a SECOND
+                    # exception that would escape this handler before `_release_process_memory()` runs.
+                    data_manager._log_isolation_failure(
                         "evidence drawdown-expectations warm aborted — memory pressure, stopping remaining "
                         "claims: %r", exc,
                     )
                     data_manager._release_process_memory()
                     break
                 except Exception as exc:  # NON-FATAL: one bad claim never blocks the others
-                    logger.exception(
+                    data_manager._log_isolation_failure(
                         "evidence drawdown-expectations warm failed for one claim (non-fatal): %r", exc
                     )
         logger.info("evidence drawdown-expectations cache warmed (%d claim panels)", warmed)
diff --git a/apps/backend/tests/test_evidence.py b/apps/backend/tests/test_evidence.py
index e6ded870..65b1b949 100644
--- a/apps/backend/tests/test_evidence.py
+++ b/apps/backend/tests/test_evidence.py
@@ -19,7 +19,7 @@ from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
 import pytest
-from sqlmodel import Session
+from sqlmodel import Session, select
 
 import app.engine.forward_testing as forward_testing
 import app.engine.market_phase as market_phase
@@ -695,14 +695,17 @@ def test_build_payload_per_claim_compute_failure_is_isolated(
     append_entry(str(ledger), _pass_entry("leadership_score"))
     append_entry(str(ledger), _pass_entry("entry_quality_score", factor="entry_quality_score"))
 
-    real_cached = forward_testing.compute_drawdown_expectations_cached
+    # ops-hardening iter-47: `build_evidence_payload` now calls the SERVING wrapper
+    # `compute_drawdown_expectations_cached_with_status` (audit B2, serve-stale-behind-a-label), not the
+    # plain cached function directly — the monkeypatch target moves with it.
+    real_cached = forward_testing.compute_drawdown_expectations_cached_with_status
 
     def _flaky_cached(session, claim, config=None):
         if claim.get("factor") == "leadership_score":
             raise MemoryError("synthetic TC-4 failure")
         return real_cached(session, claim, config)
 
-    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _flaky_cached)
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached_with_status", _flaky_cached)
 
     with Session(evidence_dd_two_claims_engine) as session:
         payload = build_evidence_payload(str(ledger), session=session, config=load_config())
@@ -722,6 +725,89 @@ def test_build_payload_per_claim_compute_failure_is_isolated(
     assert exp_phase["n"] == 1
 
 
+# ==================================================================================================
+# ops-hardening iter-47 (audit B2) — the serve-stale-behind-a-label fix: `GET /api/evidence` must survive
+# an UNRELATED concurrent ingest (any new forward_returns row bumps every claim's dataset-version stamp)
+# without falling onto the multi-minute cold-recompute tail. `build_evidence_payload` now calls
+# `compute_drawdown_expectations_cached_with_status`; a claim serving a stale (last-good) generation
+# additively carries `expectations_status: "refreshing"` alongside its (real, honest) `expectations` —
+# never mixed with the newer generation's fields.
+# ==================================================================================================
+def test_build_payload_serves_stale_expectations_as_refreshing_after_dataset_change(
+    tmp_path, evidence_dd_engine, monkeypatch,
+):
+    """TC-3: after the dataset changes (an unrelated new forward_returns row lands, exactly like a
+    concurrent ingest), the row's `expectations` still renders — the LAST-GOOD pre-change payload,
+    byte-identical to what was served before the change — with an ADDITIVE `expectations_status:
+    "refreshing"` label. The pre-existing 'ready' shape (no status key at all) is unaffected when there is
+    no dataset change."""
+    import app.db as db_module
+    import app.engine.forward_testing as forward_testing_module
+
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), _pass_entry("leadership_score"))
+    cfg = load_config()
+
+    with Session(evidence_dd_engine) as session:
+        before = build_evidence_payload(str(ledger), session=session, config=cfg)
+    before_row = before["claims"][0]
+    assert "expectations_status" not in before_row  # the pre-existing 'ready' shape: no status key at all
+
+    # change the dataset: a second, UNRELATED symbol's forward return on the SAME run (mirrors a concurrent
+    # ingest landing a new row that has nothing to do with this claim's own cohort membership).
+    with Session(evidence_dd_engine) as session:
+        run = session.exec(select(ScannerRun)).one()
+        session.add(ScannerResult(
+            run_id=run.id, ticker="ZZZ", name="ZZZ", sector="Technology",
+            leadership_score=10.0, leadership_bucket="C",
+            entry_quality_score=50.0, entry_quality_bucket="C",
+            risk_score=50.0, risk_bucket="C",
+            setup_status="Actionable", rank=2, record_json="{}",
+        ))
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="ZZZ", horizon=20, asof_date=run.asof_date, entry_close=100.0,
+            measured_date=run.asof_date + timedelta(days=40), realized_return=-0.01,
+            max_drawdown=-0.09, underwater_days=7, time_to_recover_days=None,
+        ))
+        session.commit()
+
+    prev_engine = db_module._engine
+    db_module.set_engine(evidence_dd_engine)
+    monkeypatch.setattr(forward_testing_module.threading, "Thread", _NoOpThread)
+    # iter-47 AUDIT (T1): `_NoOpThread.start()` never runs `_spawn_drawdown_expectations_rewarm`'s worker
+    # body, so its `finally: _REWARM_IN_FLIGHT = False` never fires and the module GLOBAL would stay True
+    # for the rest of the pytest process — poisoning the single-flight guard for every later test in the
+    # SAME session (proven: with this line absent, running this file before
+    # `test_forward_testing.py::test_cached_with_status_dataset_change_serves_stale_refreshing_then_settles_ready`
+    # makes that test fail with `assert 'refreshing' == 'ready'`). `monkeypatch.setattr` records the
+    # pre-test value and restores it at teardown, so the guard is always left as it was found.
+    monkeypatch.setattr(forward_testing_module, "_REWARM_IN_FLIGHT", False)
+    try:
+        with Session(evidence_dd_engine) as session:
+            after = build_evidence_payload(str(ledger), session=session, config=cfg)
+    finally:
+        db_module.set_engine(prev_engine)
+
+    after_row = after["claims"][0]
+    assert after_row.get("expectations_status") == "refreshing"
+    assert "expectations" in after_row
+    assert after_row["expectations"] == before_row["expectations"], (
+        "a refreshing row must serve the LAST-GOOD pre-change generation verbatim — never a mix"
+    )
+
+
+class _NoOpThread:
+    """A `threading.Thread` stand-in whose `start()` does NOTHING — this test only needs to prove the
+    REQUEST-PATH behavior (immediate stale-serve + label), not the background re-warm's own eventual-
+    consistency mechanics (already proven directly in test_forward_testing.py)."""
+
+    def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
+        pass
+
+    def start(self):
+        pass
+
+
 def test_resolve_ledger_path_env_override(tmp_path, monkeypatch):
     override = tmp_path / "override-ledger.jsonl"
     monkeypatch.setenv(LEDGER_PATH_ENV, str(override))
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 44f83e2d..e18f0845 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -32,6 +32,7 @@ from app.engine.forward_testing import (
     backfill_forward_returns,
     compute_drawdown_expectations,
     compute_drawdown_expectations_cached,
+    compute_drawdown_expectations_cached_with_status,
     compute_forward_aggregates,
     forward_aggregates_ingest_cached,
     forward_excursions,
@@ -1730,6 +1731,172 @@ def test_compute_drawdown_expectations_cached_none_when_horizon_outside_scope_sk
         assert session.scalar(select(func.count()).select_from(EventStudyCache)) == 0
 
 
+# ==================================================================================================
+# compute_drawdown_expectations_cached_with_status — the /api/evidence SERVING wrapper (ops-hardening
+# iter-47, audit B2): serve-stale-behind-a-label. `_dataset_version` folds in EVERY forward_returns row in
+# the DB, so ANY ingest anywhere invalidates every claim's cache row at once; this wrapper closes the TC-2
+# scenario (an unrelated new row must never force the page onto the multi-minute cold-recompute tail) by
+# serving the LAST-GOOD generation immediately (labeled "refreshing") while a single-flight background
+# thread re-warms the current version, instead of blocking the request on the cold compute.
+#
+# A synchronous stand-in for `threading.Thread` makes the background re-warm deterministic in these tests
+# (runs inline, on its OWN session against the SAME test engine via `app.db.set_engine`) — it still
+# exercises the real `_run` body (compute + persist + prune), so these are NOT a mocked-out no-op proof.
+# ==================================================================================================
+class _SyncThread:
+    """A `threading.Thread` stand-in whose `start()` runs the target INLINE, synchronously — makes the
+    background re-warm's effects observable immediately within a test, while still exercising the real
+    `_run` closure (compute + persist + prune), not a mocked-out no-op."""
+
+    def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
+        self._target = target
+
+    def start(self):
+        self._target()
+
+    def join(self, timeout=None):
+        pass
+
+
+def test_cached_with_status_cold_start_falls_back_to_synchronous_ready(dd_expectations_engine):
+    """TC-1/first-ever resolution: with NO prior generation cached at all (normally pre-empted by the boot
+    warm), the wrapper falls back to the synchronous cached compute exactly as before this iteration —
+    `(payload, "ready")`, byte-identical to calling `compute_drawdown_expectations_cached` directly."""
+    cfg = _dd_cfg()
+    with Session(dd_expectations_engine) as session:
+        direct = compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)
+    with Session(dd_expectations_engine) as session:
+        payload, status = compute_drawdown_expectations_cached_with_status(session, _FACTOR_CLAIM, cfg)
+    assert status == "ready"
+    assert json.dumps(payload, sort_keys=True) == json.dumps(direct, sort_keys=True)
+
+
+def test_cached_with_status_hit_is_ready_with_no_recompute(dd_expectations_engine, monkeypatch):
+    """TC-1: a HIT for the CURRENT dataset version returns `(payload, "ready")` without ever re-invoking
+    the uncached `compute_drawdown_expectations` (a call-count proof, not just a byte-match)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    cfg = _dd_cfg()
+    with Session(dd_expectations_engine) as session:
+        compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)  # warm the current-version row
+
+    call_count = {"n": 0}
+    real = forward_testing_module.compute_drawdown_expectations
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(forward_testing_module, "compute_drawdown_expectations", _counting)
+    with Session(dd_expectations_engine) as session:
+        payload, status = compute_drawdown_expectations_cached_with_status(session, _FACTOR_CLAIM, cfg)
+    assert status == "ready"
+    assert payload is not None
+    assert call_count["n"] == 0, "a current-version HIT must never recompute"
+
+
+def test_cached_with_status_dataset_change_serves_stale_refreshing_then_settles_ready(
+    dd_expectations_engine, monkeypatch,
+):
+    """TC-2/TC-3: after the dataset changes (bumping `_dataset_version`, exactly like an unrelated ingest
+    landing a new forward_returns row), the wrapper serves the LAST-GOOD (pre-change) payload IMMEDIATELY
+    as `(payload, "refreshing")` — byte-identical to the pre-change value, never blocking on the cold
+    recompute — while a single-flight background re-warm computes+persists the new generation. Once that
+    re-warm has settled, the NEXT call is a genuine HIT: `(new_payload, "ready")`, matching a fresh
+    uncached compute of the CHANGED cohort — proving no two generations' fields were ever mixed in one
+    response (each response is exactly ONE EventStudyCache row's payload, deserialized whole)."""
+    import app.db as db_module
+    import app.engine.forward_testing as forward_testing_module
+    from app.engine import warmup as warmup_module
+
+    # the GLOBAL background worker (`_spawn_drawdown_expectations_rewarm`) re-warms EVERY claim on the
+    # EVIDENCE LEDGER via `warmup._warm_drawdown_expectations` — stub the ledger to hold exactly this
+    # test's `_FACTOR_CLAIM` (mirrors test_warmup.py's `_stub_ledger` convention) so the worker actually
+    # re-warms the subject this test observes, instead of the real production ledger's unrelated claims.
+    monkeypatch.setattr(warmup_module, "read_entries", lambda _path: [{"type": "claim", "claim": _FACTOR_CLAIM}])
+    monkeypatch.setattr(warmup_module.evidence, "resolve_ledger_path", lambda *_a, **_k: "unused.jsonl")
+
+    cfg = _dd_cfg()
+    with Session(dd_expectations_engine) as session:
+        before = compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)  # warm v_before
+
+        # change the dataset: one more leadership_score observation on the FIRST Expansion date (mirrors
+        # `test_compute_drawdown_expectations_cached_refreshes_on_dataset_version_change` exactly).
+        existing_run = session.exec(
+            select(ScannerRun).where(ScannerRun.asof_date == _EXP_DATES[0])
+        ).one()
+        _add_result(session, existing_run.id, "ZZZ", "A", "Actionable", "Technology", 2)
+        _add_dd_fr(session, existing_run, "ZZZ", DD_H, 0.05, mdd=-0.01, uw=1, ttr=1)
+        session.commit()
+
+    with Session(dd_expectations_engine) as session:
+        fresh_after = compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg)  # the true post-change value
+    assert _by_phase(fresh_after, "Expansion")["n"] == 5  # sanity: the dataset genuinely changed
+
+    prev_engine = db_module._engine
+    db_module.set_engine(dd_expectations_engine)  # the background re-warm resolves its OWN session via get_engine()
+    monkeypatch.setattr(forward_testing_module.threading, "Thread", _SyncThread)
+    try:
+        with Session(dd_expectations_engine) as session:
+            payload, status = compute_drawdown_expectations_cached_with_status(session, _FACTOR_CLAIM, cfg)
+    finally:
+        db_module.set_engine(prev_engine)
+
+    assert status == "refreshing"
+    assert json.dumps(payload, sort_keys=True) == json.dumps(before, sort_keys=True), (
+        "a refreshing response must serve the LAST-GOOD (pre-change) generation verbatim — never a mix"
+    )
+
+    # the single-flight background re-warm (run synchronously via _SyncThread above) has now settled —
+    # the NEXT call must be a genuine HIT on the NEW generation.
+    with Session(dd_expectations_engine) as session:
+        payload2, status2 = compute_drawdown_expectations_cached_with_status(session, _FACTOR_CLAIM, cfg)
+        subject = _drawdown_expectations_cache_subject(_FACTOR_CLAIM)
+        rows = session.exec(select(EventStudyCache).where(EventStudyCache.subject == subject)).all()
+    assert status2 == "ready"
+    assert json.dumps(payload2, sort_keys=True) == json.dumps(fresh_after, sort_keys=True)
+    assert len(rows) == 1, "the stale pre-change row must be pruned once the re-warm lands the new one"
+
+
+def test_cached_with_status_single_flight_no_duplicate_rewarm(dd_expectations_engine, monkeypatch):
+    """A re-warm already in flight (the GLOBAL single-flight guard — one worker re-warms EVERY stale
+    claim, not one per claim; see the module note above `_spawn_drawdown_expectations_rewarm`) is never
+    duplicated — a second concurrent MISS for ANY claim while one worker is already running must not spawn
+    a second background thread."""
+    import app.engine.forward_testing as forward_testing_module
+
+    cfg = _dd_cfg()
+    with Session(dd_expectations_engine) as session:
+        compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)  # warm v_before
+        existing_run = session.exec(
+            select(ScannerRun).where(ScannerRun.asof_date == _EXP_DATES[0])
+        ).one()
+        _add_result(session, existing_run.id, "ZZZ", "A", "Actionable", "Technology", 2)
+        _add_dd_fr(session, existing_run, "ZZZ", DD_H, 0.05, mdd=-0.01, uw=1, ttr=1)
+        session.commit()
+
+    thread_starts = {"n": 0}
+
+    class _CountingSyncThread(_SyncThread):
+        def start(self):
+            thread_starts["n"] += 1
+            super().start()
+
+    monkeypatch.setattr(forward_testing_module.threading, "Thread", _CountingSyncThread)
+    # pre-mark a re-warm as already in-flight — simulates a concurrent request's own worker still running
+    # when a second request (for the SAME or a DIFFERENT claim) lands.
+    forward_testing_module._REWARM_IN_FLIGHT = True
+    try:
+        with Session(dd_expectations_engine) as session:
+            payload, status = compute_drawdown_expectations_cached_with_status(session, _FACTOR_CLAIM, cfg)
+    finally:
+        forward_testing_module._REWARM_IN_FLIGHT = False
+
+    assert status == "refreshing"
+    assert payload is not None
+    assert thread_starts["n"] == 0, "a re-warm already in flight must never be duplicated by a second stale claim"
+
+
 # ==================================================================================================
 # ops-hardening iter-36 (J-07 evidence-serving-path memory bound, ledger finding iter-35/k) —
 # `compute_drawdown_expectations`'s `stored_by_key` `ForwardReturn` read (forward_testing.py:2320-2333)
@@ -1898,8 +2065,8 @@ def test_drawdown_expectations_stored_by_key_accumulator_is_chunk_bounded(dd_exp
     observed_sizes: list[int] = []
     real_slice_map = forward_testing_module._drawdown_ticker_slice_map
 
-    def _wrapped(session, horizon, slice_tickers, batch):
-        result = real_slice_map(session, horizon, slice_tickers, batch)
+    def _wrapped(session, horizon, slice_tickers, batch, dates_by_ticker=None):
+        result = real_slice_map(session, horizon, slice_tickers, batch, dates_by_ticker)
         observed_sizes.append(len(result))
         return result
 
@@ -1921,3 +2088,128 @@ def test_drawdown_expectations_stored_by_key_accumulator_is_chunk_bounded(dd_exp
         f"the live accumulator must never hold the whole cohort's rows at once — got {observed_sizes!r}"
     )
     assert max(observed_sizes) <= 4, f"a single ticker's own slice must not exceed its own row count, got {observed_sizes!r}"
+
+
+# ==================================================================================================
+# ops-hardening iter-47 (AG-8, iter-46 audit B4): `_drawdown_ticker_slice_map`'s query was
+# `(horizon, symbol)`-filtered only — never on the cohort's own snapshot dates — so it read every stored
+# ForwardReturn for the chunk's tickers at this horizon, INCLUDING dates the claim's cohort never resolved
+# (a ticker can carry forward returns on many more snapshot dates than any one claim's cohort ever uses).
+# The iter-46 audit measured this at 7,994,388 rows across 71 calls to serve 7 live claims. The filter
+# narrows the query to exactly the (symbol, date) pairs the caller's lookup loop will ever ask for —
+# provably byte-identical (an excluded row's key is never queried either way) with a measured, real
+# row-count reduction (TC-5).
+#
+# ops-hardening iter-47 FIX PASS (audit finding B2): the filter first shipped scoped by the per-CHUNK
+# UNION of the chunk's cohort dates, which on a real all-history cohort removed only 4.4 % of rows — and
+# the test below could not see that, because it ran at chunk width 1 (where a chunk IS one ticker, so the
+# union is trivially the right axis). It now runs at chunk width 2 with AAA and BBB in the SAME chunk and
+# noise rows placed on the OTHER ticker's cohort date: the per-chunk-union implementation passes those
+# rows through, the per-ticker implementation excludes them. This test FAILS against the union version.
+# ==================================================================================================
+def test_drawdown_ticker_slice_map_date_filter_reduces_rows_and_stays_byte_identical(
+    dd_expectations_engine, monkeypatch,
+):
+    """TC-5: extra ForwardReturn rows for an existing cohort ticker (AAA) at dates OUTSIDE its own resolved
+    cohort (no matching ScannerResult, so `compute_samples` never surfaces them) prove the date filter
+    (a) EXCLUDES those rows from the query — a measured row-count reduction, INCLUDING a noise row sitting
+    on a CHUNK-SIBLING's cohort date, which only per-ticker scoping can exclude — and (b) leaves
+    `compute_drawdown_expectations`'s served payload byte-identical to the pre-fix unfiltered read (the
+    excluded rows were never looked up by either implementation)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    # `_CORR_DATES[0]` is BBB's OWN cohort date — AAA's noise row there is inside the {AAA,BBB} chunk's
+    # date UNION, so only PER-TICKER scoping can exclude it (audit B2's discriminator).
+    noise_dates = [date(2025, 8, 10), date(2025, 9, 10), _CORR_DATES[0]]
+    with Session(dd_expectations_engine) as session:
+        for i, d in enumerate(noise_dates):
+            # a bare ForwardReturn row for AAA at a date with NO ScannerResult for AAA -> never enters the
+            # claim's cohort (compute_samples never surfaces it), but WOULD be read by an unfiltered
+            # `_drawdown_ticker_slice_map` query (same symbol + horizon, no date scope).
+            session.add(ForwardReturn(
+                run_id=999_000 + i, symbol="AAA", horizon=DD_H, asof_date=d,
+                entry_close=100.0, measured_date=d + timedelta(days=DD_H * 2),
+                realized_return=0.01, max_drawdown=-0.5, underwater_days=99, time_to_recover_days=1,
+            ))
+        session.commit()
+
+    cfg = load_config()
+    real_slice_map = forward_testing_module._drawdown_ticker_slice_map
+
+    # baseline sanity: an UNFILTERED read (dates_by_ticker=None, the pre-iter-47 behavior) sees the noise
+    # rows too — proves the fixture actually exercises the reduction this test measures.
+    with Session(dd_expectations_engine) as session:
+        unfiltered = real_slice_map(session, DD_H, ["AAA"], cfg.research.read_batch_size, None)
+    assert len(unfiltered) == 4 + len(noise_dates), "sanity: the noise rows must be visible to an unfiltered read"
+
+    observed_sizes: list[int] = []
+
+    def _wrapped(session, horizon, slice_tickers, batch, dates_by_ticker=None):
+        result = real_slice_map(session, horizon, slice_tickers, batch, dates_by_ticker)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(forward_testing_module, "_drawdown_ticker_slice_map", _wrapped)
+    # chunk width 2 -> tickers sort AAA/BBB/CCC/DDD, so chunk 1 is {AAA, BBB}: AAA's noise row on BBB's own
+    # cohort date is inside the chunk's date UNION and outside AAA's own date set.
+    research_cfg = cfg.research.model_copy(update={"drawdown_expectations_ticker_chunk": 2})
+    filtered_cfg = cfg.model_copy(update={"research": research_cfg})
+    with Session(dd_expectations_engine) as session:
+        filtered_payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, filtered_cfg)
+
+    assert filtered_payload is not None
+    # chunk 1 = {AAA (4 cohort dates), BBB (1)} -> exactly 5 rows when each ticker is scoped to its OWN
+    # dates; 6 under the per-chunk-union scoping (AAA's noise row on BBB's date survives the union).
+    assert observed_sizes[0] == 5, (
+        f"expected the {{AAA,BBB}} chunk to read exactly each ticker's OWN cohort dates (5 rows), got "
+        f"{observed_sizes[0]} — a per-chunk-union date scope reads 6 (audit B2)"
+    )
+    assert observed_sizes[0] < len(unfiltered), (
+        f"the date filter must reduce the read's row count vs the unfiltered read "
+        f"({observed_sizes[0]} !< {len(unfiltered)})"
+    )
+
+    # byte-identity: recompute forcing dates_by_ticker=None at every call (the exact pre-iter-47 behavior),
+    # then diff the served payloads.
+    def _reference_unfiltered(session, horizon, slice_tickers, batch, dates_by_ticker=None):
+        return real_slice_map(session, horizon, slice_tickers, batch, None)
+
+    monkeypatch.setattr(forward_testing_module, "_drawdown_ticker_slice_map", _reference_unfiltered)
+    with Session(dd_expectations_engine) as session:
+        reference_payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, filtered_cfg)
+
+    assert json.dumps(filtered_payload, sort_keys=True, default=str) == json.dumps(
+        reference_payload, sort_keys=True, default=str
+    ), "date-filtered payload must be byte-identical to the unfiltered pre-fix reference"
+
+
+def test_drawdown_ticker_slice_map_batches_date_binds_and_keeps_every_row(dd_expectations_engine, monkeypatch):
+    """ops-hardening iter-47 FIX PASS (audit finding B7): a ticker's date IN-list is emitted in
+    `_MAX_IN_PARAMS`-sized batches, so the query never depends on this host's SQLite variable limit
+    (32,766 on 3.53.1, but 999 on builds predating 3.32 — and the list is sized by the DATA, growing as
+    history deepens). Proven by shrinking the batch to 2 against AAA's 4 cohort dates: MORE THAN ONE query
+    is issued and the returned map still holds ALL FOUR rows (no row silently dropped at a batch seam)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    monkeypatch.setattr(forward_testing_module, "_MAX_IN_PARAMS", 2)
+    cfg = load_config()
+    dates_by_ticker = {"AAA": frozenset(_EXP_DATES)}
+
+    query_count = {"n": 0}
+    with Session(dd_expectations_engine) as session:
+        orig_exec = session.exec
+
+        def _counting_exec(stmt, *a, **kw):
+            if "forward_returns" in str(stmt):
+                query_count["n"] += 1
+            return orig_exec(stmt, *a, **kw)
+
+        session.exec = _counting_exec  # type: ignore[assignment]
+        batched = forward_testing_module._drawdown_ticker_slice_map(
+            session, DD_H, ["AAA"], cfg.research.read_batch_size, dates_by_ticker
+        )
+
+    assert query_count["n"] == 2, f"4 dates at a 2-bind batch must issue 2 queries, got {query_count['n']}"
+    assert sorted(batched) == sorted((("AAA", d.isoformat()) for d in _EXP_DATES)), (
+        f"every batch's rows must survive into the same map, got {sorted(batched)!r}"
+    )
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index 4fe947f2..9c3ac859 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -977,3 +977,191 @@ def test_combination_observations_chunked_as_of_excludes_runs_after_cutoff(combi
     assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
     for obs in observations:
         assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"
+
+
+# ==================================================================================================
+# ops-hardening iter-47 (AG-8, iter-46 audit B3): `app.engine.samples._factor_samples`'s "decile" branch
+# used to build the FULL `_factor_observations` list (whole horizon population, up to ~800K observations
+# measured live) and `sorted()` it WHOLE just to discard 9/10 of it after slicing one decile — the third
+# unbounded whole-cohort materialization on the `/api/evidence` serving path (5 of the 7 live certified
+# claims are decile-scoped factor claims; `logs/backend.log` caught it `MemoryError`-ing at 02:20:31 on
+# 2026-08-04, reached via `evidence.py` -> `compute_drawdown_expectations_cached` -> `compute_samples` ->
+# `_factor_samples`). `research._factor_decile_observations` (new) resolves the SAME decile membership in
+# two BOUNDED passes (a lightweight population-wide sort-key pass, then a bounded rebuild restricted to the
+# target decile's keys) instead of materializing + sorting the whole population's full dicts. These proofs
+# pin byte-identity against the PRE-FIX approach (the exact `_factor_samples` decile branch used to run) —
+# the memory-BOUND claim itself is proven live by `test_samples_memory_pressure.py`'s real subprocess
+# induction (this repo's established convention for a boundedness claim, mirroring
+# `test_evidence_drawdown_memory_pressure.py`).
+# ==================================================================================================
+def _factor_decile_observations_reference(session, factor, horizon, as_of, deciles_count, decile, cfg):
+    """The PRE-FIX `_factor_samples` decile branch, pinned verbatim: the FULL `_factor_observations` list,
+    sorted whole by the SAME tie-break key, then `_decile_member_slice`d — the regression oracle for the
+    iter-47 two-pass bounded rewrite."""
+    from app.engine.research import _decile_member_slice, _factor_observations
+
+    observations = _factor_observations(session, factor, horizon, as_of, cfg=cfg)
+    ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
+    return _decile_member_slice(ordered, deciles_count, decile)
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
+@pytest.mark.parametrize("decile", [1, 5, 10])
+def test_factor_decile_observations_equals_pre_fix_reference(chunked_accumulator_engine, as_of, decile):
+    """TC-4 (byte-identity leg): the bounded two-pass `_factor_decile_observations` is byte-identical to
+    the pinned pre-fix (whole-population sort + slice) reference — across the first/middle/last decile and
+    both all-history and a historical as_of that splits the 5-run fixture into an early/late group — under
+    a chunk width small enough to force multiple slices in BOTH passes."""
+    cfg = _cfg_batch(2)
+    deciles_count = cfg.research.factor_lab.deciles
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        bounded = research_module._factor_decile_observations(
+            session, factor, H, as_of, deciles_count, decile, cfg=cfg
+        )
+        reference = _factor_decile_observations_reference(
+            session, factor, H, as_of, deciles_count, decile, cfg
+        )
+    assert _eq(bounded, reference), (
+        f"bounded decile {decile} (as_of={as_of}) != pre-fix whole-population reference"
+    )
+
+
+def test_factor_decile_observations_union_covers_whole_pool_no_double_count(chunked_accumulator_engine):
+    """Sanity/coherence companion to the byte-identity leg: the union of every D1..D10 bounded call's
+    members equals the whole 15-pair fixture pool exactly once each — no member dropped, none duplicated,
+    across the decile boundary arithmetic."""
+    cfg = _cfg_batch(2)
+    deciles_count = cfg.research.factor_lab.deciles
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    seen: list[tuple[int, str]] = []
+    with Session(chunked_accumulator_engine) as session:
+        for d in range(1, deciles_count + 1):
+            members = research_module._factor_decile_observations(
+                session, factor, H, None, deciles_count, d, cfg=cfg
+            )
+            seen.extend((m["run_id"], m["ticker"]) for m in members)
+    assert len(seen) == 15, f"expected all 15 fixture pairs covered exactly once, got {len(seen)}"
+    assert len(set(seen)) == 15, "a (run_id, ticker) pair was double-counted across deciles"
+
+
+def test_factor_decile_observations_chunk_independent(chunked_accumulator_engine):
+    """The bounded decile resolution is batch/chunk-independent — read_batch_size AND
+    factor_join_run_chunk both varied — never a value/order change, only a memory-shape change."""
+    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        small = research_module._factor_decile_observations(
+            session, factor, H, None, 10, 10, cfg=_cfg_batch(1, run_chunk=1)
+        )
+        big = research_module._factor_decile_observations(
+            session, factor, H, None, 10, 10, cfg=_cfg_batch(1_000_000, run_chunk=1_000_000)
+        )
+    assert small, "sanity: decile 10 must be non-empty on this fixture"
+    assert _eq(small, big), "bounded decile resolution differs by chunk width"
+
+
+def test_factor_decile_pass1_retention_is_bounded_not_whole_population(chunked_accumulator_engine, monkeypatch):
+    """ops-hardening iter-47 FIX PASS (audit finding B3): PASS 1 must not RETAIN one sort key per
+    observation for the whole population (~1.25 M tuples ≈ 155 MB live) just to sort it whole — the
+    "bounded READ, unbounded RETENTION" shape iter-40's lesson names, and the reason the audit judged
+    `samples.py:156` reduced rather than bounded. Instrumenting the real `_BoundedRankWindow` records the
+    live buffer length at every trim (its true momentary peak): the peak must stay inside `2 x capacity`
+    and STRICTLY below the population, and `capacity` itself must be derived from the requested decile's
+    own share — for D10 of 10 that is ~1/10 of the population, not the population."""
+    cfg = _cfg_batch(2)
+    deciles_count = cfg.research.factor_lab.deciles
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+
+    peaks: list[int] = []
+    caps: list[int] = []
+    real_window = research_module._BoundedRankWindow
+
+    class _ObservingWindow(real_window):
+        def __init__(self, n_max, dc, d):
+            super().__init__(n_max, dc, d)
+            caps.append(self._capacity)
+
+        def _trim(self):
+            peaks.append(len(self._buf))  # the momentary peak: `add` trims the instant it is reached
+            super()._trim()
+
+    monkeypatch.setattr(research_module, "_BoundedRankWindow", _ObservingWindow)
+    with Session(chunked_accumulator_engine) as session:
+        members = research_module._factor_decile_observations(
+            session, factor, H, None, deciles_count, deciles_count, cfg=cfg
+        )
+        population = len(_factor_observations(session, factor, H, None, cfg=cfg))
+
+    assert members, "sanity: the top decile must be non-empty on this fixture"
+    assert population == 15, f"sanity: this fixture's population is 15 observations, got {population}"
+    assert caps == [2], (
+        f"D10 of 10 over a 15-observation population must commit to a ~1/10 capacity, got {caps!r}"
+    )
+    assert peaks, "the window must actually trim (otherwise nothing is bounded)"
+    assert max(peaks) <= 2 * caps[0], (
+        f"peak retention {max(peaks)} exceeded the 2x-capacity bound ({2 * caps[0]})"
+    )
+    assert max(peaks) < population, (
+        f"peak retention {max(peaks)} is not below the population {population} — this is the unbounded "
+        f"whole-population accumulator the fix removes"
+    )
+
+
+def test_factor_decile_window_underflow_degrades_to_exact_computation(chunked_accumulator_engine, monkeypatch):
+    """ops-hardening iter-47 FIX PASS (audit finding B3): the retention window is sized from a PROVEN
+    upper bound, so it cannot underflow — but a truncated decile would be a WRONG SERVED NUMBER (AG-3),
+    so the underflow branch degrades to the exact unbounded computation instead. Forced here with a
+    deliberately too-small upper bound (1 against a 15-observation pool): the returned members must still
+    be byte-identical to the pinned pre-fix reference, and the degrade must be logged, never silent."""
+    cfg = _cfg_batch(2)
+    deciles_count = cfg.research.factor_lab.deciles
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    monkeypatch.setattr(research_module, "_decile_population_upper_bound", lambda *a, **kw: 1)
+
+    records: list[str] = []
+    monkeypatch.setattr(
+        research_module.logger, "warning",
+        lambda msg, *args, **kw: records.append(str(msg) % args if args else str(msg)),
+    )
+    with Session(chunked_accumulator_engine) as session:
+        members = research_module._factor_decile_observations(
+            session, factor, H, None, deciles_count, deciles_count, cfg=cfg
+        )
+        reference = _factor_decile_observations_reference(
+            session, factor, H, None, deciles_count, deciles_count, cfg
+        )
+    assert members, "the degrade path must still return the decile's real members"
+    assert _eq(members, reference), "the degraded (exact) path must stay byte-identical to the reference"
+    assert any("window underflow" in r for r in records), (
+        f"the degrade must be logged, never silent — got {records!r}"
+    )
+
+
+def test_factor_decile_population_upper_bound_is_never_below_the_real_population(chunked_accumulator_engine):
+    """The window's capacity is only sound while `_decile_population_upper_bound(...) >= n`. Pinned
+    directly against the real population this fixture produces (and against the as_of-scoped one, which
+    the bound must track because it reads the SAME as_of-filtered run set)."""
+    cfg = _cfg_batch(2)
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    run_chunk = cfg.research.factor_join_run_chunk
+    with Session(chunked_accumulator_engine) as session:
+        for as_of in (None, date(2025, 3, 15)):
+            runs = research_module._runs_with_fr(session, [H], as_of)
+            bound = research_module._decile_population_upper_bound(session, runs, run_chunk)
+            population = len(_factor_observations(session, factor, H, as_of, cfg=cfg))
+            assert bound >= population, (
+                f"upper bound {bound} < real population {population} at as_of={as_of} — the bounded "
+                f"window could then discard a genuine decile member"
+            )
+
+
+def test_factor_decile_observations_zero_n_cohort_is_honest_empty(chunked_accumulator_engine):
+    """An as_of before any snapshot resolves an honest empty decile — never a crash, never a fabricated
+    member — under the two-pass bounded path (PASS 1's empty `sort_keys` short-circuits before PASS 2)."""
+    cfg = _cfg_batch(2)
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        members = research_module._factor_decile_observations(
+            session, factor, H, date(2024, 1, 1), cfg.research.factor_lab.deciles, 10, cfg=cfg
+        )
+    assert members == []
diff --git a/apps/backend/tests/test_warmup.py b/apps/backend/tests/test_warmup.py
index b19750ce..85d9a1a5 100644
--- a/apps/backend/tests/test_warmup.py
+++ b/apps/backend/tests/test_warmup.py
@@ -805,6 +805,77 @@ def test_warmup_drawdown_expectations_failure_is_nonfatal_on_textless_memoryerro
     warmup_mod._WARMUP_THREAD = None
 
 
+# ==================================================================================================
+# ops-hardening iter-47 (TC-6, carried from iter-44/45/46): `_warm_drawdown_expectations`'s two per-claim
+# exception handlers (warmup.py:205 MemoryError, :212 generic Exception) called a BARE `logger.exception`
+# — under the SAME exhausted `ulimit -v` cap that raised the original exception, rendering the full
+# traceback can itself allocate and raise a SECOND exception that escapes the handler before
+# `_release_process_memory()` runs (the module-wide isolation convention 19+ other sites already apply).
+# These proofs are DIRECT: they monkeypatch `_log_isolation_failure` itself and assert it was invoked — a
+# caplog text check cannot discriminate a guarded call from a bare one, because `_log_isolation_failure`
+# ALSO calls `logger.exception` internally on its own happy path.
+# ==================================================================================================
+def test_warmup_drawdown_memoryerror_calls_log_isolation_failure_not_bare_exception(early_engine, monkeypatch):
+    """TC-6 (warmup.py:205): the per-claim `MemoryError` handler calls `data_manager._log_isolation_failure`
+    — proven directly, not inferred from a log message — on a TEXTLESS `MemoryError`
+    (`str(MemoryError())` is `""`, this session's standing honesty rule for every new handler)."""
+    engine, cfg = early_engine
+    _stub_ledger(monkeypatch, [{"type": "claim", "claim": {"signal": "boom", "horizon": 20}}])
+
+    def _boom(*_args, **_kwargs):
+        raise MemoryError()  # TEXTLESS on purpose
+
+    monkeypatch.setattr(warmup_mod.forward_testing, "compute_drawdown_expectations_cached", _boom)
+    monkeypatch.setattr(warmup_mod.data_manager, "_release_process_memory", lambda: None)
+    calls: list[tuple] = []
+    monkeypatch.setattr(
+        warmup_mod.data_manager, "_log_isolation_failure",
+        lambda msg, *args, **kwargs: calls.append((msg, args)),
+    )
+
+    warmup_mod._warm_drawdown_expectations(engine, cfg)
+
+    assert len(calls) == 1, f"expected exactly one _log_isolation_failure call, got {calls}"
+    assert "memory pressure" in calls[0][0].lower(), calls[0]
+
+
+def test_warmup_drawdown_generic_exception_calls_log_isolation_failure_not_bare_exception(
+    early_engine, monkeypatch,
+):
+    """TC-6 (warmup.py:212): the per-claim GENERIC exception handler (one bad claim never blocks the
+    others) also calls `data_manager._log_isolation_failure` — proven directly — and, unlike the
+    `MemoryError` branch, must NOT abort the loop: a second, healthy claim after the failing one still
+    warms."""
+    engine, cfg = early_engine
+    claim_bad = {"signal": "bad-claim", "horizon": 20}
+    claim_good = {"signal": "good-claim", "horizon": 60}
+    _stub_ledger(monkeypatch, [
+        {"type": "claim", "claim": claim_bad},
+        {"type": "claim", "claim": claim_good},
+    ])
+
+    warmed: list[dict] = []
+
+    def _per_claim(_session, claim, _cfg):
+        if claim is claim_bad:
+            raise RuntimeError("boom")
+        warmed.append(claim)
+        return {"by_phase": []}
+
+    monkeypatch.setattr(warmup_mod.forward_testing, "compute_drawdown_expectations_cached", _per_claim)
+    calls: list[tuple] = []
+    monkeypatch.setattr(
+        warmup_mod.data_manager, "_log_isolation_failure",
+        lambda msg, *args, **kwargs: calls.append((msg, args)),
+    )
+
+    warmup_mod._warm_drawdown_expectations(engine, cfg)
+
+    assert len(calls) == 1, f"expected exactly one _log_isolation_failure call, got {calls}"
+    assert "non-fatal" in calls[0][0].lower(), calls[0]
+    assert warmed == [claim_good], "a generic per-claim failure must not block the NEXT claim from warming"
+
+
 def test_warmup_evidence_warm_runs_only_after_readiness_reaches_ok(early_engine, monkeypatch):
     """SEQUENCING PROOF (protects J-04 and J-07 step 1): the evidence warm is expensive (163.3s measured
     live for 7 claims), so it must run strictly AFTER the warm-up record has settled `ok` — the readiness
diff --git a/apps/frontend/app/evidence/page.tsx b/apps/frontend/app/evidence/page.tsx
index 4bdf60a3..df048c84 100644
--- a/apps/frontend/app/evidence/page.tsx
+++ b/apps/frontend/app/evidence/page.tsx
@@ -250,7 +250,13 @@ function ClaimRow({ claim }: { claim: CertifiedClaim }) {
  *  ops-hardening iter-29 (AG-8): branches on `resolveDrawdownExpectationsPanelState` (the single, pure
  *  authority) so a genuine per-claim compute failure THIS request (`expectations_status === "unavailable"`)
  *  renders a calm inline note instead of being indistinguishable from the pre-existing "not applicable"
- *  (absent) case. */
+ *  (absent) case.
+ *
+ *  ops-hardening iter-47 (audit B2): the SAME resolver also distinguishes `"refreshing"` — a resolved,
+ *  real, honest table (the last-good prior generation) is still rendered in full, with an ADDITIVE calm
+ *  warn-toned `Badge` beside the heading (mirrors `/backtest`'s `evidence_status: "refreshing"` pattern —
+ *  no new component). Never a blank/loading placeholder: the values shown are genuine and were never
+ *  mixed with a newer generation's fields (a single `EventStudyCache` row, deserialized whole). */
 function DrawdownExpectationsPanel({ claim }: { claim: CertifiedClaim }) {
   const state = resolveDrawdownExpectationsPanelState(claim);
   if (state.kind === "absent") {
@@ -271,15 +277,26 @@ function DrawdownExpectationsPanel({ claim }: { claim: CertifiedClaim }) {
     );
   }
   const { expectations } = state;
+  const isRefreshing = state.kind === "refreshing";
   return (
     <div className="space-y-2 border-t border-border pt-3" data-testid="evidence-expectations-panel">
       <div>
-        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
-          Historical drawdown &amp; dry-spell expectations ({expectations.horizon}-day hold)
-        </h3>
+        <div className="flex flex-wrap items-center gap-2">
+          <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
+            Historical drawdown &amp; dry-spell expectations ({expectations.horizon}-day hold)
+          </h3>
+          {isRefreshing ? (
+            <Badge variant="warn" data-testid="evidence-expectations-refreshing">
+              Refreshing
+            </Badge>
+          ) : null}
+        </div>
         <p className="mt-0.5 text-xs text-text-faint">
           What following this cohort&rsquo;s methodology has historically felt like, by market phase at
           entry — descriptive history only, never a forecast or a promise.
+          {isRefreshing
+            ? " A newer version is computing in the background after a recent data update — the table below is the last complete version, not a partial or fabricated one."
+            : null}
         </p>
       </div>
       <div className="overflow-x-auto">
diff --git a/apps/frontend/lib/evidence.test.ts b/apps/frontend/lib/evidence.test.ts
index 46b188a0..5181db6d 100644
--- a/apps/frontend/lib/evidence.test.ts
+++ b/apps/frontend/lib/evidence.test.ts
@@ -1037,4 +1037,63 @@ check(
   },
 );
 
+// --- ops-hardening iter-47 (audit B2, TC-3): a FOURTH state — "refreshing" — a resolved, REAL last-good
+// prior-generation `expectations` payload served while a newer generation (an unrelated ingest bumped the
+// shared dataset-version stamp) computes in the background. Distinct from BOTH "present" (current
+// generation, no status field) and "unavailable" (no expectations at all).
+check(
+  "resolveDrawdownExpectationsPanelState: expectations + expectations_status='refreshing' => 'refreshing', " +
+    "carrying the served (last-good) payload verbatim (TC-3)",
+  () => {
+    const claim: CertifiedClaim = {
+      ...provenRow("leadership_score"),
+      expectations: SAMPLE_EXPECTATIONS,
+      expectations_status: "refreshing",
+    };
+    const state = resolveDrawdownExpectationsPanelState(claim);
+    assert.strictEqual(state.kind, "refreshing");
+    if (state.kind === "refreshing") {
+      assert.strictEqual(state.expectations, SAMPLE_EXPECTATIONS); // read verbatim, never recomputed
+    }
+  },
+);
+
+check(
+  "resolveDrawdownExpectationsPanelState: 'refreshing' is DISTINCT from 'present' and from 'unavailable' (TC-3)",
+  () => {
+    const refreshing = resolveDrawdownExpectationsPanelState({
+      ...provenRow("leadership_score"),
+      expectations: SAMPLE_EXPECTATIONS,
+      expectations_status: "refreshing",
+    });
+    const present = resolveDrawdownExpectationsPanelState({
+      ...provenRow("leadership_score"),
+      expectations: SAMPLE_EXPECTATIONS,
+    });
+    const unavailable = resolveDrawdownExpectationsPanelState({
+      ...provenRow("leadership_score"),
+      expectations_status: "unavailable",
+    });
+    assert.strictEqual(refreshing.kind, "refreshing");
+    assert.strictEqual(present.kind, "present");
+    assert.strictEqual(unavailable.kind, "unavailable");
+    assert.notStrictEqual(refreshing.kind, present.kind);
+    assert.notStrictEqual(refreshing.kind, unavailable.kind);
+  },
+);
+
+check(
+  "resolveDrawdownExpectationsPanelState: no expectations but expectations_status='refreshing' (an " +
+    "impossible-in-practice payload shape) resolves to 'absent', never 'refreshing' without a payload to " +
+    "show — the resolver checks `claim.expectations` FIRST",
+  () => {
+    const claim: CertifiedClaim = {
+      ...provenRow("leadership_score"),
+      expectations_status: "refreshing",
+    };
+    const state = resolveDrawdownExpectationsPanelState(claim);
+    assert.strictEqual(state.kind, "absent");
+  },
+);
+
 console.log(`\n${passed} evidence-badge resolver checks passed.`);
diff --git a/apps/frontend/lib/evidence.ts b/apps/frontend/lib/evidence.ts
index de18d546..6858af3a 100644
--- a/apps/frontend/lib/evidence.ts
+++ b/apps/frontend/lib/evidence.ts
@@ -75,12 +75,16 @@ export interface DrawdownExpectations {
  *  score-to-date (null until a certified claim is monitored). `expectations` (iter-41, J-25) is ADDITIVE
  *  and OPTIONAL — the backend omits the key entirely (never a fabricated panel) when the cohort could not
  *  be resolved; a `null`/`undefined` value must render nothing for the panel section (never an error).
- *  `expectations_status` (ops-hardening iter-29, AG-8) is ALSO additive and OPTIONAL — present ONLY when
- *  this request's per-claim `expectations` compute raised an exception (`"unavailable"`, the one legal
- *  value today); absent for a successful compute AND for every pre-existing honest-None case (an
- *  out-of-scope horizon, an unresolvable cohort, a zero-observation cohort) — those keep rendering nothing,
- *  byte-unchanged. `resolveDrawdownExpectationsPanelState` below is the single place that distinguishes
- *  the three states. */
+ *  `expectations_status` is ALSO additive and OPTIONAL. `"unavailable"` (ops-hardening iter-29, AG-8) is
+ *  present ONLY when this request's per-claim `expectations` compute raised an exception; absent for a
+ *  successful compute AND for every pre-existing honest-None case (an out-of-scope horizon, an
+ *  unresolvable cohort, a zero-observation cohort) — those keep rendering nothing, byte-unchanged.
+ *  `"refreshing"` (ops-hardening iter-47, audit B2) is present ONLY when the served `expectations` payload
+ *  is the last-good PRIOR generation while a newer one (an unrelated ingest bumped the shared dataset-
+ *  version stamp) computes in the background — the values shown are still real, honest, and were never
+ *  mixed with the newer generation's fields; absent or omitted once the current generation is served
+ *  (mirrors `/backtest`'s `evidence_status: "ready"|"refreshing"|"not_yet_computed"` sibling pattern).
+ *  `resolveDrawdownExpectationsPanelState` below is the single place that distinguishes all four states. */
 export interface CertifiedClaim {
   signal: string | null;
   claim: Record<string, unknown>;
@@ -92,7 +96,7 @@ export interface CertifiedClaim {
   proven: boolean;
   forward_walk: unknown | null;
   expectations?: DrawdownExpectations | null;
-  expectations_status?: "unavailable";
+  expectations_status?: "unavailable" | "refreshing";
 }
 
 /** A proven claim row, as stored in the served `proven_signals` map (keyed by signal). Same shape as a
@@ -291,13 +295,19 @@ export function formatStreak(value: number | null | undefined): string {
 // iter-24/25 J-09). Reads `claim.expectations` / `claim.expectations_status` VERBATIM — recomputes nothing.
 
 /** Which state the drawdown-expectations panel renders for ONE claim:
- *   - "present"     — a resolved `expectations` payload exists; the table renders (pre-existing, unchanged).
+ *   - "present"     — a resolved, CURRENT-generation `expectations` payload exists; the table renders
+ *                     (pre-existing, unchanged).
+ *   - "refreshing"  — a resolved but STALE (last-good prior generation) `expectations` payload exists
+ *                     while a newer one computes in the background (NEW, ops-hardening iter-47, audit
+ *                     B2); the table STILL renders (the values are real and honest) with an additional
+ *                     calm "Refreshing" label — never silently indistinguishable from "present".
  *   - "unavailable" — this request's per-claim compute raised an exception (`expectations_status ===
  *                     "unavailable"`); a calm inline note renders instead of a table (NEW, iter-29).
  *   - "absent"      — no `expectations` and no `expectations_status` (the pre-existing honest-None cohort-
  *                     unresolvable case); the panel renders nothing (unchanged). */
 export type DrawdownExpectationsPanelState =
   | { kind: "present"; expectations: DrawdownExpectations }
+  | { kind: "refreshing"; expectations: DrawdownExpectations }
   | { kind: "unavailable" }
   | { kind: "absent" };
 
@@ -306,9 +316,14 @@ export type DrawdownExpectationsPanelState =
  * client-side recompute of anything). `"unavailable"` (a genuine per-claim compute failure THIS request)
  * is DISTINCT from `"absent"` (the pre-existing, unaffected "no expectations, no status field" case) so the
  * panel can disclose a transient failure honestly instead of rendering it identically to "not applicable".
+ * `"refreshing"` (ops-hardening iter-47) is DISTINCT from `"present"` for the SAME reason — a claim serving
+ * its last-good prior generation must never look identical to one serving its current generation.
  */
 export function resolveDrawdownExpectationsPanelState(claim: CertifiedClaim): DrawdownExpectationsPanelState {
   if (claim.expectations) {
+    if (claim.expectations_status === "refreshing") {
+      return { kind: "refreshing", expectations: claim.expectations };
+    }
     return { kind: "present", expectations: claim.expectations };
   }
   if (claim.expectations_status === "unavailable") {
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 357 +++++++++++++++++++++
 .../journey-scripts/J-01.json                      | 195 ++++++++++-
 .../journey-scripts/J-03.json                      |   6 +-
 .../journey-scripts/J-05.json                      |  14 +-
 .../journey-scripts/J-08.json                      |   9 +-
 .../journey-scripts/J-09.json                      |   6 +-
 .../J-04.json.retired}                             |   0
 .../J-07.json.retired}                             |   0
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |  43 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   9 +
 12 files changed, 616 insertions(+), 27 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
