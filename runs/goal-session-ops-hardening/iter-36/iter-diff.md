# Iteration diff (bounded)

Files changed: 13. Shown in full: 13.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 0b9fae34..d5e5ca4c 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1368,6 +1368,26 @@ class ResearchCfg(BaseModel):
     # in `logs/backend.log`, not another opaque crash. Boot-validated `>= 1`; defaulted so a config (and the
     # inline test fixtures) predating it still loads.
     factor_pool_max_observations: int = 2_000_000
+    # ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — the SYMBOLS-axis batch width
+    # `_membership_timeline` (data_manager.py) loads the candidate pool's bars in, when no OUTER
+    # job-scoped bar cache is already active (the standalone / ingest-finalize coverage-compute entry
+    # point). A DIFFERENT axis from `read_batch_size` (a ROWS knob for `yield_per`) and from
+    # `factor_join_run_chunk` (a RUN-count width) — this counts CANDIDATE-POOL SYMBOLS, and reusing
+    # either neighbor's unit here would repeat the iter-29 unit-confusion lesson (a knob sized for one
+    # axis silently going inert on another). One batch's full price history (all ~30 years) is loaded,
+    # every snapshot date is resolved against it, then it is DISCARDED before the next batch loads — so
+    # peak resident bar data scales with this width, not with the full candidate-pool size (today ~590).
+    # Boot-validated `>= 1`; defaulted so a config (and inline test fixtures) predating it still loads.
+    membership_timeline_batch_symbols: int = 50
+    # ops-hardening iter-36 (J-07 evidence-serving-path memory bound) — the TICKER-axis chunk width
+    # `compute_drawdown_expectations` (forward_testing.py) partitions a claim's resolved cohort into
+    # before reading each chunk's `stored_by_key` `ForwardReturn` rows (each chunk's own
+    # `yield_per(read_batch_size)`-streamed query — reusing `read_batch_size` THERE is its own designed
+    # purpose, the per-query row-stream size; it is NOT reused as this chunk's own width). A DIFFERENT
+    # axis from `read_batch_size` and `factor_join_run_chunk` — this counts TICKERS in one claim's own
+    # cohort, so a broad claim's stored-return read never pays one unbounded `.all()` in one shot.
+    # Boot-validated `>= 1`; defaulted so a config (and inline test fixtures) predating it still loads.
+    drawdown_expectations_ticker_chunk: int = 50
     downtrend_opportunity: "DowntrendOpportunityCfg" = Field(
         default_factory=lambda: _default_downtrend_opportunity()
     )
@@ -1390,6 +1410,10 @@ class ResearchCfg(BaseModel):
             raise ValueError("research.regime_phase_factor_page_size must be >= 1")
         if self.factor_pool_max_observations < 1:
             raise ValueError("research.factor_pool_max_observations must be >= 1")
+        if self.membership_timeline_batch_symbols < 1:
+            raise ValueError("research.membership_timeline_batch_symbols must be >= 1")
+        if self.drawdown_expectations_ticker_chunk < 1:
+            raise ValueError("research.drawdown_expectations_ticker_chunk must be >= 1")
         return self
 
 
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 7459f0fa..a8c67716 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -57,7 +57,15 @@ from app.engine import evidence  # ops-hardening iter-7 (J-06): the finalize hoo
 from app.engine import forward_testing, scanner
 from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
-from app.engine.prices import attach_shared_cache, bar_cache, bars_asof, latest_data_date, prefilled_bar_cache
+from app.engine.prices import (
+    _BarCache,
+    active_bar_cache,
+    attach_shared_cache,
+    bar_cache,
+    bars_asof,
+    latest_data_date,
+    prefilled_bar_cache,
+)
 from app.engine import universe_resolver
 from app.engine.universe_screen import (
     DEFAULT_SEED_DIR,
@@ -508,11 +516,14 @@ def _membership_timeline(
                             below_adv) from the resolver over the SAME candidate pool + bars <= that date.
 
     Strictly causal: each date is observed from its OWN <= D snapshot + bars <= D (no future leakage).
-    Deterministic. An empty DB / no snapshots → an empty-but-valid timeline (no fabricated dates/members)."""
+    Deterministic. An empty DB / no snapshots → an empty-but-valid timeline (no fabricated dates/members).
+
+    ops-hardening iter-36 (J-07/J-96 AG-8 memory bound): the per-date excluded-by-reason counts are now
+    sourced via `_excluded_counts_by_date` (below), which BOUNDS peak resident bar data to a config-driven
+    symbol-batch width instead of the full candidate pool's whole price history, WHEN no outer job-scoped
+    bar cache is already active (see that helper's docstring). `entries`/`exits`/`size` are unaffected —
+    they read only the persisted `members_by_date` membership, never a bar."""
     dates = sorted(snapshot_dates)
-    # the committed candidate-pool symbols the per-date resolver will ask `trailing_count` about — passed
-    # to `prefilled_bar_cache` so a no-bar candidate is recorded as an empty series up front and never
-    # lazy re-loaded per date (iter-37 load-once restored; byte-identical: empty series ⇒ 0 trailing bars).
     pool_symbols = {row["symbol"] for row in read_pool()}
     pool_count = len(pool_symbols)
     points: list[dict] = []
@@ -529,36 +540,22 @@ def _membership_timeline(
     for asof_date, ticker in rows:
         members_by_date.setdefault(asof_date, set()).add(ticker.upper())
 
-    # J-46 load-once bar cache: the per-date resolver re-reads the SAME pool symbols across every snapshot
-    # date, so caching each symbol's full series once turns each `bars_asof` into an in-memory slice (a
-    # whole-calendar rebuild's timeline stays tractable). The cache reads the committed bars (adds none)
-    # and dies with this block — never serving a stale series.
-    #
-    # iter-36 (J-96 cold-miss bound): use `prefilled_bar_cache` — it loads EVERY symbol's full series in
-    # ONE query up front, so the per-date `resolve_with_reasons` sources its trailing-bar counts from the
-    # once-loaded series (via the cache's `trailing_count`) instead of issuing one grouped-count query PER
-    # DATE. On the post-rebuild DB this turns ~1369 per-date grouped-count round-trips into a single
-    # prefill + in-memory bisects, bounding the cold (cache-miss) `GET /api/data` cost. Byte-identical to
-    # the lazy `bar_cache` path: same rows, same admission, same excluded counts — only the loading
-    # changes. (This is the cold path; a warm cache hit skips this loop entirely.)
-    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
-        for d in dates:
-            members = members_by_date.get(d, set())
-            # entries = members never seen on any earlier observed date; exits = prior members now gone.
-            entries = sorted(m for m in members if m not in seen)
-            exits = sorted(m for m in prev_members if m not in members)
-            seen |= members
-            prev_members = members
-            # the per-date excluded-by-reason counts from the resolver over bars <= d (causal). This is a
-            # read-only descriptive derivation (no canonical-value recompute) over the candidate pool.
-            diag = universe_resolver.resolve_with_reasons(session, d, cfg)
-            points.append({
-                "date": d.isoformat(),
-                "size": len(members),
-                "entries": entries,
-                "exits": exits,
-                "excluded": dict(diag["excluded_counts"]),
-            })
+    excluded_by_date = _excluded_counts_by_date(session, cfg, dates, pool_symbols)
+
+    for d in dates:
+        members = members_by_date.get(d, set())
+        # entries = members never seen on any earlier observed date; exits = prior members now gone.
+        entries = sorted(m for m in members if m not in seen)
+        exits = sorted(m for m in prev_members if m not in members)
+        seen |= members
+        prev_members = members
+        points.append({
+            "date": d.isoformat(),
+            "size": len(members),
+            "entries": entries,
+            "exits": exits,
+            "excluded": excluded_by_date[d],
+        })
 
     return {
         "candidate_pool_count": pool_count,
@@ -568,6 +565,56 @@ def _membership_timeline(
     }
 
 
+def _excluded_counts_by_date(
+    session: Session, cfg: Config, dates: list[date_cls], pool_symbols: set[str],
+) -> dict[date_cls, dict[str, int]]:
+    """ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — the per-date excluded-by-reason tally
+    `_membership_timeline`'s points read, computed one of two ways depending on whether an OUTER
+    job-scoped bar cache is already active on `session`:
+
+      - ACTIVE outer cache (e.g. `_do_backfill` / `_persist_per_date_coverage_snapshots`, which each open
+        their OWN `prefilled_bar_cache` around a whole multi-date job before ever reaching this function):
+        reuse it exactly as before — no new loading, no batching. That whole-job-scoped cost is already
+        paid/accepted by the caller's own job and amortized across every date + aggregate it computes;
+        this iteration does not touch it.
+      - NO active cache (the standalone entry point — `_compute_coverage_uncached` called directly, e.g.
+        by `refresh_coverage_snapshot`'s ingest-finalize call for the CURRENT date, or a cold `/data`-class
+        read): the committed candidate pool is walked in `research.membership_timeline_batch_symbols`-wide
+        batches. ONE `_BarCache` instance is created and its contents REPLACED per batch (`load_only`) —
+        never a second instance, never `prefill`'s whole-table scan — so peak resident bar data scales
+        with the batch width, not the full ~590-symbol pool. Each batch resolves EVERY snapshot date
+        before the next batch loads (so a batch's bars are read `len(dates)` times, then discarded).
+
+    Byte-identical either way: `resolve_with_reasons`'s excluded tally is a pure per-symbol classification
+    with no cross-symbol interaction, so summing it over disjoint symbol batches equals resolving the
+    whole pool at once (and the active-cache branch is the SAME unbatched call this function replaces)."""
+    totals: dict[date_cls, dict[str, int]] = {
+        d: {reason: 0 for reason in universe_resolver.EXCLUSION_REASONS} for d in dates
+    }
+    if active_bar_cache(session) is not None:
+        for d in dates:
+            diag = universe_resolver.resolve_with_reasons(session, d, cfg)
+            for reason, n in diag["excluded_counts"].items():
+                totals[d][reason] += n
+        return totals
+
+    batch_width = max(1, cfg.research.membership_timeline_batch_symbols)
+    ordered_pool = sorted(pool_symbols)
+    if not ordered_pool:
+        return totals
+    batch_cache = _BarCache()  # ONE instance for the whole loop below — its contents are REPLACED per
+    # batch (`load_only`), never a second cache instance and never the whole-table `prefill` scan.
+    with attach_shared_cache(session, batch_cache):
+        for i in range(0, len(ordered_pool), batch_width):
+            batch = ordered_pool[i : i + batch_width]
+            batch_cache.load_only(session, batch)  # discards the PRIOR batch's bars, loads only this one
+            for d in dates:
+                diag = universe_resolver.resolve_with_reasons(session, d, cfg, symbols=batch)
+                for reason, n in diag["excluded_counts"].items():
+                    totals[d][reason] += n
+    return totals
+
+
 def membership_timeline_cached(
     session: Session, cfg: Config, snapshot_dates: list[date_cls]
 ) -> dict:
@@ -799,28 +846,33 @@ def _compute_coverage_uncached(
     resolved-size step function + entries/exits + per-date excluded counts. Every figure is read-only
     descriptive metadata over the stored bars + config thresholds (recomputes no canonical score/return).
 
-    iter-42 (J-100), scope (c): the WHOLE descriptive derivation runs inside ONE shared process-level
-    `prefilled_bar_cache` (load-once) — so `_resolved_universe`'s `resolve_with_reasons` sources its
-    trailing-bar counts from a single once-loaded copy of every symbol's series (memory bounded to one
-    copy regardless of concurrency), the membership cold-compute reuses that SAME cache (the inner
-    `prefilled_bar_cache` is re-entrant for this session — it never re-loads an already-loaded series),
-    and a no-bar candidate is recorded as an empty series up front (the iter-37 J-46 load-once invariant,
-    preserved). The cache reads the committed bars (adds none) and dies with the `with` block — never a
-    stale series. Byte-identical to the pre-change per-request path: same rows, same admission, same
-    figures — only HOW bars are loaded changes (a pure performance refactor)."""
-    # the committed candidate-pool symbols the resolver + the membership derivation ask `trailing_count`
-    # about — recorded (incl. no-bar names as []) up front so the read path is load-once (iter-37 J-46).
-    pool_symbols = {row["symbol"] for row in read_pool()}
-    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
-        return _compute_coverage_body(session, cfg, as_of=as_of)
+    iter-42 (J-100), scope (c): when this call is reached from WITHIN an outer job-scoped
+    `prefilled_bar_cache` context (e.g. `_do_backfill` / `_persist_per_date_coverage_snapshots`, each
+    already wrapping a whole multi-date job before calling this function per date), `_resolved_universe`'s
+    `resolve_with_reasons` and the membership cold-compute both reuse that SAME already-loaded cache
+    (`active_bar_cache`) — no new loading, one load amortized across the whole job, unchanged from before.
+
+    ops-hardening iter-36 (J-07 AG-8 memory bound): this function no longer opens its OWN whole-table
+    `prefilled_bar_cache` when called standalone (e.g. `refresh_coverage_snapshot`'s ingest-finalize call
+    for the CURRENT date, or a cold test/tooling call with no outer job context) — that unconditional
+    eager whole-candidate-pool prefill was the confirmed peak-memory driver for exactly this scenario
+    (TC-1). `_resolved_universe`'s single-date resolve now runs the resolver's own default (no active
+    context) per-symbol-bounded path in that case (already byte-identical and already the resolver's own
+    documented fallback — see `resolve_with_reasons`); the membership cold-compute bounds its OWN loading
+    via `_excluded_counts_by_date`'s config-driven symbol batching (see that helper). Byte-identical
+    figures either way: only HOW bars are loaded changes (a pure performance/memory refactor), never what
+    is computed."""
+    return _compute_coverage_body(session, cfg, as_of=as_of)
 
 
 def _compute_coverage_body(
     session: Session, cfg: Config, *, as_of: Optional[date_cls] = None
 ) -> dict:
-    """The coverage derivation body (runs inside the shared bar-cache context from
-    `_compute_coverage_uncached`). Split out so the cache context wraps EVERY read below (the resolver +
-    the membership cold-compute + the per-symbol table) with no signature change at the call sites."""
+    """The coverage derivation body. When an outer job-scoped bar cache is already active on `session`
+    (see `_compute_coverage_uncached`'s docstring), every read below (the resolver + the membership
+    cold-compute + the per-symbol table) reuses it automatically (`active_bar_cache`) — no signature
+    change at any call site. With no outer cache active, each heavy sub-derivation bounds its OWN loading
+    independently (the resolver's default per-symbol path; `_excluded_counts_by_date`'s symbol batching)."""
     price_min = session.scalar(select(func.min(DailyPrice.date)))
     price_max = session.scalar(select(func.max(DailyPrice.date)))
     symbol_count = session.scalar(select(func.count(func.distinct(DailyPrice.symbol))))
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 7ac6f8e1..5c062804 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -2316,15 +2316,31 @@ def compute_drawdown_expectations(
     # `compute_samples`'s own row shape does not carry. `ForwardReturn.asof_date` is stored verbatim on
     # each row (no ScannerRun join needed) and is the SAME date `_run_date_map` derives `snapshot_date`
     # from, so the (symbol, asof_date-ISO) key matches every `compute_samples` row exactly.
+    #
+    # ops-hardening iter-36 (J-07 evidence-serving-path memory bound, ledger finding iter-35/k): the
+    # single `session.exec(fr_stmt).all()` read materialized the WHOLE cohort's stored rows as a Python
+    # list in one shot before building `stored_by_key` — for a broad claim (many tickers x a long
+    # snapshot history) this doubled as a live `MemoryError` source under concurrent load
+    # (`/api/evidence`'s serving path, distinct from the analogous `research.py` accumulator iter-29 fixed
+    # at a different call site). Partitioned into `research.drawdown_expectations_ticker_chunk`-wide
+    # ticker chunks (a DIFFERENT axis from `read_batch_size` — see that config key's own doc comment), each
+    # chunk's own query `yield_per(read_batch_size)`-streamed (mirroring `_BarCache.prefill`'s /
+    # `research.py`'s iter-29 `_factor_observations` fix — `read_batch_size` reused here for ITS OWN
+    # designed purpose, the per-query row-stream size, never as the chunk width). The chunks partition
+    # `tickers` disjointly, so the built dict is byte-identical to the single-query version (same keys,
+    # same values — chunking only changes how many rows are in flight from the DB at once).
     tickers = sorted({r["ticker"] for r in rows})
-    fr_stmt = select(
-        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
-        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
-    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(tickers))
-    stored_by_key = {
-        (symbol, asof_date.isoformat()): (mdd, uw, ttr)
-        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).all()
-    }
+    chunk_width = max(1, cfg.research.drawdown_expectations_ticker_chunk)
+    read_batch = cfg.research.read_batch_size
+    stored_by_key: dict[tuple[str, str], tuple] = {}
+    for i in range(0, len(tickers), chunk_width):
+        chunk = tickers[i : i + chunk_width]
+        fr_stmt = select(
+            ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
+            ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
+        ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(chunk))
+        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).yield_per(read_batch):
+            stored_by_key[(symbol, asof_date.isoformat())] = (mdd, uw, ttr)
 
     # the SAME causal timeline `compute_market_phase` reads (all-history — the expectations panel is
     # descriptive over the claim's WHOLE tested cohort, not scoped to a single "today" as-of).
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index deb2079d..9c6e73d1 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -161,6 +161,48 @@ class _BarCache:
                         self._by_symbol[symbol] = []
                         self._dates_by_symbol[symbol] = []
 
+    def load_only(self, session: Session, symbols: Iterable[str]) -> None:
+        """ops-hardening iter-36 (J-07/J-96 AG-8 memory bound): REPLACE this cache's contents with ONLY
+        the given `symbols`' full date-ordered series — a column-projected, symbol-filtered
+        (`WHERE symbol IN (...)`), `yield_per`-streamed query, the batched sibling of `prefill`'s
+        whole-table scan. Any previously-loaded symbols are DROPPED first, so a caller iterating a large
+        candidate pool in successive batches (one `load_only` call per batch, reusing the SAME `_BarCache`
+        instance rather than allocating a second one) never holds more than ONE batch's bar data resident
+        at a time — the memory-bounding mechanism `_membership_timeline` uses when no outer job-scoped
+        cache is already active.
+
+        Deliberately independent of `prefill`/`_prefilled`: that flag guards ONLY the separate
+        whole-table scan (and its own re-entrancy/no-rescan guarantee for a job-scoped cache); a cache
+        driven by `load_only` is never also driven by `prefill`, so the two mechanisms never interact.
+        A symbol with zero stored bars is recorded as an EMPTY series (mirrors `prefill`'s
+        `expected_symbols` bookkeeping) so a no-bar candidate resolves to a trailing count of 0 with no
+        crash and no further query — byte-identical to the lazy per-symbol path's result for that symbol.
+
+        Not thread-shared (unlike the `prefill`-driven job-scoped cache): a `load_only`-driven instance is
+        owned by ONE orchestrating loop iterating batches serially, so no lock is needed around the
+        replace."""
+        symbol_list = sorted(set(symbols))
+        self._by_symbol = {}
+        self._dates_by_symbol = {}
+        if not symbol_list:
+            return
+        batch = get_config().research.read_batch_size
+        stmt = (
+            select(
+                DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
+                DailyPrice.low, DailyPrice.close, DailyPrice.volume,
+            )
+            .where(DailyPrice.symbol.in_(symbol_list))
+            .order_by(DailyPrice.symbol, DailyPrice.date)
+        )
+        by_symbol: dict[str, list[Bar]] = {}
+        for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
+            by_symbol.setdefault(symbol, []).append(Bar(d, o, h, lo, c, v))
+        for symbol in symbol_list:
+            full = by_symbol.get(symbol, [])
+            self._by_symbol[symbol] = full
+            self._dates_by_symbol[symbol] = [bar.date for bar in full]
+
     def bars_asof(self, session: Session, symbol: str, d: date_cls) -> list[Bar]:
         full = self._by_symbol.get(symbol)
         if full is None:
diff --git a/apps/backend/app/engine/universe_resolver.py b/apps/backend/app/engine/universe_resolver.py
index d25eda58..4966b162 100644
--- a/apps/backend/app/engine/universe_resolver.py
+++ b/apps/backend/app/engine/universe_resolver.py
@@ -37,7 +37,7 @@ from __future__ import annotations
 
 from dataclasses import dataclass
 from datetime import date as date_cls
-from typing import Optional
+from typing import Iterable, Optional
 
 from sqlalchemy import func
 from sqlmodel import Session, select
@@ -122,24 +122,39 @@ def resolve_with_reasons(
     config: Optional[Config] = None,
     *,
     seed_dir=None,
+    symbols: Optional[Iterable[str]] = None,
 ) -> dict:
-    """Resolve the full candidate pool at `asof` → the descriptive resolution the J-94 diagnostic /
+    """Resolve the candidate pool at `asof` → the descriptive resolution the J-94 diagnostic /
     J-96 timeline serve:
 
       {
         "asof": "YYYY-MM-DD",
-        "candidate_pool_count": <int>,         # the committed pool size (the denominator)
+        "candidate_pool_count": <int>,         # the resolved symbol set's size (the denominator)
         "admitted": [<symbol>, ...],           # the resolved members at D (alphabetical)
         "admitted_count": <int>,
         "excluded_counts": {below_history, stale_series, below_price, below_adv},
-        "resolutions": [CandidateResolution-as-dict, ...]  # one per pool candidate, alphabetical
+        "resolutions": [CandidateResolution-as-dict, ...]  # one per resolved candidate, alphabetical
       }
 
     Reads ONLY `bars_asof` (date <= D) per candidate — no lookahead. Recomputes no score/return; this
-    is descriptive membership metadata over the stored bars + config thresholds."""
+    is descriptive membership metadata over the stored bars + config thresholds.
+
+    `symbols` (ops-hardening iter-36, J-07/J-96 AG-8 memory bound): OPTIONAL — when given, restricts
+    resolution to that SUBSET of the committed pool (e.g. one batch of a symbol-batched multi-date
+    derivation — `_membership_timeline`'s memory-bounded loop). The per-symbol classification itself
+    (`resolve_candidate`) is unchanged; only which candidates get resolved this call. Every EXISTING
+    caller passes no `symbols` (`None` -> resolves the FULL committed pool exactly as before —
+    byte-identical, unchanged default behavior). Summing `excluded_counts` across a batched sequence of
+    disjoint `symbols` subsets equals resolving the whole pool at once (a per-symbol classification tally
+    has no cross-symbol interaction)."""
     cfg = config or get_config()
     pool = read_pool(seed_dir)
-    symbols = sorted({row["symbol"] for row in pool})
+    pool_symbols = sorted({row["symbol"] for row in pool})
+    if symbols is not None:
+        wanted = set(symbols)
+        resolve_symbols = [s for s in pool_symbols if s in wanted]
+    else:
+        resolve_symbols = pool_symbols
     min_history = cfg.indicators.min_history_bars
 
     # PERFORMANCE: the trailing-bar count (date <= asof) per priced symbol — only a symbol that clears
@@ -157,18 +172,18 @@ def resolve_with_reasons(
     # the original grouped-count query runs — that path is completely unchanged / byte-identical.
     cache = active_bar_cache(session)
     if cache is not None:
-        bar_count_by_symbol = {sym: cache.trailing_count(session, sym, asof) for sym in symbols}
+        bar_count_by_symbol = {sym: cache.trailing_count(session, sym, asof) for sym in resolve_symbols}
     else:
         counts_rows = session.exec(
             select(DailyPrice.symbol, func.count(DailyPrice.id))
-            .where(DailyPrice.symbol.in_(symbols))
+            .where(DailyPrice.symbol.in_(resolve_symbols))
             .where(DailyPrice.date <= asof)
             .group_by(DailyPrice.symbol)
         ).all()
         bar_count_by_symbol = {sym: int(n or 0) for sym, n in counts_rows}
 
     resolutions: list[CandidateResolution] = []
-    for symbol in symbols:
+    for symbol in resolve_symbols:
         bar_count = bar_count_by_symbol.get(symbol, 0)
         if bar_count < min_history:
             # below the history gate — the first gate; no need to materialize the full series.
@@ -187,7 +202,7 @@ def resolve_with_reasons(
 
     return {
         "asof": asof.isoformat(),
-        "candidate_pool_count": len(symbols),
+        "candidate_pool_count": len(resolve_symbols),
         "admitted": admitted,
         "admitted_count": len(admitted),
         "excluded_counts": excluded_counts,
diff --git a/apps/backend/tests/test_bar_cache.py b/apps/backend/tests/test_bar_cache.py
index cffc788f..629fc5e2 100644
--- a/apps/backend/tests/test_bar_cache.py
+++ b/apps/backend/tests/test_bar_cache.py
@@ -253,6 +253,73 @@ def test_cache_sees_new_bars_in_a_fresh_context(tiny_engine):
             assert len(bars_asof(session, "AAA", new_day)) == len(days) + 1
 
 
+# ==================================================================================================
+# ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — `_BarCache.load_only()`, the batched-REPLACE
+# sibling of `prefill()` used by `_membership_timeline`'s memory-bounded loop (data_manager.py) when no
+# outer job-scoped cache is already active.
+# ==================================================================================================
+def test_load_only_loads_exactly_the_given_symbols_byte_identical_to_lazy_path(tiny_engine):
+    """`load_only(symbols)` loads ONLY the requested symbols, with values byte-identical to the default
+    (uncached) per-symbol query — same rows, same order, same values."""
+    engine, days = tiny_engine
+    with Session(engine) as reference_session:
+        reference = [
+            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
+            for bar in reference_session.exec(
+                select(DailyPrice).where(DailyPrice.symbol == "AAA").order_by(DailyPrice.date)
+            ).all()
+        ]
+    with Session(engine) as session:
+        cache = prices._BarCache()
+        cache.load_only(session, ["AAA"])
+        assert set(cache._by_symbol) == {"AAA"}  # ONLY the requested symbol loaded — never SPY too
+        loaded = [
+            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
+            for bar in cache._by_symbol["AAA"]
+        ]
+    assert loaded == reference
+    assert all(isinstance(bar, prices.Bar) for bar in cache._by_symbol["AAA"])
+
+
+def test_load_only_records_zero_bar_symbol_as_empty_series(tiny_engine):
+    """A symbol with no `daily_prices` rows at all is recorded as an EMPTY series (mirrors `prefill`'s
+    `expected_symbols` bookkeeping) — `trailing_count` reads 0 with no crash and no further query."""
+    engine, days = tiny_engine
+    with Session(engine) as session:
+        cache = prices._BarCache()
+        cache.load_only(session, ["AAA", "ZZZ_NO_BARS"])
+        assert cache._by_symbol["ZZZ_NO_BARS"] == []
+        assert cache._dates_by_symbol["ZZZ_NO_BARS"] == []
+        assert cache.trailing_count(session, "ZZZ_NO_BARS", days[-1]) == 0
+        assert cache.trailing_count(session, "AAA", days[-1]) == len(days)
+
+
+def test_load_only_replaces_prior_contents_never_accumulates_across_batches(tiny_engine):
+    """A SECOND `load_only` call on the SAME instance (a later batch of a symbol-batched loop) DROPS the
+    first batch's symbol entirely — the mechanism `_membership_timeline` relies on to bound peak resident
+    bar data to one batch at a time, reusing ONE `_BarCache` instance rather than allocating a second."""
+    engine, days = tiny_engine
+    with Session(engine) as session:
+        cache = prices._BarCache()
+        cache.load_only(session, ["AAA"])
+        assert set(cache._by_symbol) == {"AAA"}
+        cache.load_only(session, ["SPY"])
+        assert set(cache._by_symbol) == {"SPY"}, "the prior batch (AAA) must be dropped, not accumulated"
+        assert len(cache._by_symbol["SPY"]) == len(days)
+
+
+def test_load_only_does_not_touch_prefilled_flag_or_interact_with_prefill(tiny_engine):
+    """`load_only` is independent of `prefill`'s whole-table-scan guard: it never sets `_prefilled`, and a
+    cache driven by `load_only` never triggers (or is triggered by) `prefill`'s re-entrancy mechanics —
+    the two loading mechanisms coexist without interaction."""
+    engine, days = tiny_engine
+    with Session(engine) as session:
+        cache = prices._BarCache()
+        assert cache._prefilled is False
+        cache.load_only(session, ["AAA"])
+        assert cache._prefilled is False, "load_only must never mark the whole-table scan as done"
+
+
 # --- a small instrument: count per-symbol bar-store loads (the per-symbol DailyPrice SELECT) ----------
 class _SymbolLoadCounter:
     """Wraps `session.exec` and tallies the bar-store loads per symbol (a SELECT over `daily_prices`
diff --git a/apps/backend/tests/test_data_manager_membership_cache.py b/apps/backend/tests/test_data_manager_membership_cache.py
index 4a0c58c9..92eaf16a 100644
--- a/apps/backend/tests/test_data_manager_membership_cache.py
+++ b/apps/backend/tests/test_data_manager_membership_cache.py
@@ -328,45 +328,51 @@ def test_empty_db_caches_empty_but_valid_timeline(tmp_path):
 
 
 # ==================================================================================================
-# iter-19 — the coverage COLD PATH prefills the bar cache exactly ONCE (the OOM fix's data_manager-level
-# proof, on top of prices.py's own unit tests in test_bar_cache.py)
+# ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — supersedes the iter-19 "exactly one whole-table
+# scan" proof above: a standalone COLD `compute_coverage()` call (no outer job-scoped bar cache active)
+# no longer scans the whole table AT ALL. iter-19's underlying INTENT ("never pay the full-table scan more
+# than necessary") still holds — it is now satisfied by never doing the unbounded scan in the first place.
 # ==================================================================================================
-def test_cold_compute_coverage_prefills_bar_cache_exactly_once(tmp_path, monkeypatch):
-    """iter-19: a COLD `compute_coverage()` call (membership-timeline cache MISS) opens its OWN
-    `prefilled_bar_cache` (in `_compute_coverage_uncached`), and `_membership_timeline` — called from
-    inside `_compute_coverage_body`, via `membership_timeline_cached` on the miss — opens a NESTED
-    `prefilled_bar_cache` on the SAME session. `bar_cache`'s re-entrancy means both contexts share the SAME
-    `_BarCache` instance, but before iter-19, `_BarCache.prefill()` re-ran its expensive whole-table scan
-    UNCONDITIONALLY on every call regardless of instance state — so this ONE coverage request paid the
-    full-table scan TWICE. Invisible at ~122 symbols/5 years; a doubled contribution to the OOM at 583
-    symbols/30 years. Proven by counting how many of the (>= 2) `prefill()` calls actually reach the DB —
-    exactly one, after the fix."""
+def test_cold_compute_coverage_never_prefills_whole_table_and_batches_by_symbol(tmp_path, monkeypatch):
+    """iter-36: a COLD, standalone `compute_coverage()` call (membership-timeline cache MISS, no outer
+    job-scoped `prefilled_bar_cache` active — the SAME shape `refresh_coverage_snapshot`'s ingest-finalize
+    call for the CURRENT date reaches) must NEVER call `_BarCache.prefill()` (the whole-candidate-pool
+    scan iter-19 bounded to at-most-once but iter-36 removes altogether for this entry point). Instead the
+    membership cold-compute walks the candidate pool via `_BarCache.load_only()` in
+    `research.membership_timeline_batch_symbols`-wide batches — proven by asserting every `load_only` call
+    loads AT MOST the configured batch width, and that MULTIPLE batches ran (the real committed pool is
+    wider than the default batch width, so single-batch coverage would silently prove nothing)."""
     cfg = load_config()
     engine = _three_snapshot_engine(tmp_path)
     reset_coverage_cache()  # start cold so this call is guaranteed to be a real (uncached) compute
 
-    prefill_calls = {"total": 0, "real_scans": 0}
-    orig_prefill = prices_module._BarCache.prefill
+    def _boom_prefill(self, session, expected_symbols=None):
+        raise AssertionError(
+            "a standalone cold compute_coverage() call must never scan the whole daily_prices table "
+            "(_BarCache.prefill) — the membership cold-compute must batch by symbol instead"
+        )
 
-    def _counting_prefill(self, session, expected_symbols=None):
-        prefill_calls["total"] += 1
-        was_prefilled = self._prefilled
-        orig_prefill(self, session, expected_symbols=expected_symbols)
-        if not was_prefilled:
-            prefill_calls["real_scans"] += 1
+    monkeypatch.setattr(prices_module._BarCache, "prefill", _boom_prefill)
 
-    monkeypatch.setattr(prices_module._BarCache, "prefill", _counting_prefill)
+    load_only_calls: list[int] = []
+    orig_load_only = prices_module._BarCache.load_only
+
+    def _counting_load_only(self, session, symbols):
+        symbol_list = list(symbols)
+        load_only_calls.append(len(symbol_list))
+        return orig_load_only(self, session, symbol_list)
+
+    monkeypatch.setattr(prices_module._BarCache, "load_only", _counting_load_only)
 
     with Session(engine) as session:
         compute_coverage(session, cfg)
 
-    # both the outer coverage context AND the nested membership-timeline context call `.prefill()` on the
-    # SAME cache instance (the cache-miss path) — but only ONE of those calls may reach the DB.
-    assert prefill_calls["total"] >= 2, (
-        f"expected >= 2 prefill() calls (outer coverage + nested membership timeline), "
-        f"got {prefill_calls['total']} — the nested-call shape this test targets did not occur"
+    assert load_only_calls, "expected at least one batched load_only() call for the membership cold-compute"
+    batch_width = cfg.research.membership_timeline_batch_symbols
+    assert all(n <= batch_width for n in load_only_calls), (
+        f"a load_only() call exceeded the configured batch width {batch_width}: {load_only_calls}"
     )
-    assert prefill_calls["real_scans"] == 1, (
-        f"expected exactly ONE real bar-store scan across the nested prefill calls, "
-        f"got {prefill_calls['real_scans']}"
+    assert len(load_only_calls) > 1, (
+        "expected multiple batches (the real committed candidate pool is wider than the default batch "
+        f"width {batch_width}) — got only {load_only_calls}, so this test would not catch an un-batched load"
     )
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index e7463c1f..30c09fb5 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -1728,3 +1728,152 @@ def test_compute_drawdown_expectations_cached_none_when_horizon_outside_scope_sk
     with Session(dd_expectations_engine) as session:
         assert compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg) is None
         assert session.scalar(select(func.count()).select_from(EventStudyCache)) == 0
+
+
+# ==================================================================================================
+# ops-hardening iter-36 (J-07 evidence-serving-path memory bound, ledger finding iter-35/k) —
+# `compute_drawdown_expectations`'s `stored_by_key` `ForwardReturn` read (forward_testing.py:2320-2333)
+# is now partitioned into `research.drawdown_expectations_ticker_chunk`-wide ticker chunks, each
+# `yield_per(read_batch_size)`-streamed, instead of ONE `session.exec(fr_stmt).all()` over the WHOLE
+# cohort — a live `MemoryError` source for a broad claim's cohort under concurrent load (distinct call
+# site from the `research.py` accumulator iter-29 fixed). Proven here: byte-identical to a pinned
+# pre-fix reference across several chunk widths (including widths narrower than the fixture's own
+# ticker count, forcing multiple real chunks).
+# ==================================================================================================
+def _reference_compute_drawdown_expectations(session: Session, claim: dict, config=None) -> "dict | None":
+    """Verbatim pre-fix `compute_drawdown_expectations` body (`git show HEAD:apps/backend/app/engine/
+    forward_testing.py` at the iter-36 dispatch commit, lines 2270-2376) — ONE unchunked
+    `session.exec(fr_stmt).all()` builds `stored_by_key` for the WHOLE cohort in one shot. Every helper it
+    calls (`_claim_samples_kwargs`, `_distribution_cell`, `_loss_streak_cell`, `phase_context_by_date`,
+    `compute_samples`) is UNCHANGED by this iteration (verified by diff) and reused directly from the real
+    module — never re-pinned (iter-32 lesson: reusing an unchanged helper is safe; re-pinning a CHANGED one
+    into an edited copy is not)."""
+    from collections import defaultdict
+
+    import app.engine.forward_testing as forward_testing_module
+    from app.config import get_config
+
+    cfg = config or get_config()
+    wf = cfg.walk_forward
+    horizon = claim.get("horizon")
+    if horizon not in wf.underwater_horizons:
+        return None
+    kwargs = _claim_samples_kwargs(claim)
+    if kwargs is None:
+        return None
+
+    from app.engine.market_phase import phase_context_by_date
+    from app.engine.samples import compute_samples
+
+    try:
+        samples = compute_samples(
+            session, kind=claim.get("kind"), horizon=horizon, config=cfg, as_of=None, **kwargs
+        )
+    except ValueError:
+        return None
+
+    rows = [r for r in samples["rows"] if r.get("snapshot_date") and r.get("forward_return") is not None]
+    if not rows:
+        return None
+
+    tickers = sorted({r["ticker"] for r in rows})
+    fr_stmt = select(
+        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
+        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(tickers))
+    stored_by_key = {
+        (symbol, asof_date.isoformat()): (mdd, uw, ttr)
+        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).all()
+    }
+
+    phases = phase_context_by_date(session, as_of=None, config=cfg)
+
+    by_phase_mdd: dict = defaultdict(list)
+    by_phase_uw: dict = defaultdict(list)
+    by_phase_ttr: dict = defaultdict(list)
+    by_phase_returns: dict = defaultdict(list)
+
+    for row in rows:
+        date_iso = row["snapshot_date"]
+        ctx = phases.get(date_iso)
+        if ctx is None:
+            continue
+        phase = ctx["phase"]
+        by_phase_returns[phase].append((date_iso, row["forward_return"]))
+        stored = stored_by_key.get((row["ticker"], date_iso))
+        if stored is None:
+            continue
+        mdd, uw, ttr = stored
+        if mdd is not None:
+            by_phase_mdd[phase].append(mdd)
+        if uw is not None:
+            by_phase_uw[phase].append(uw)
+        if ttr is not None:
+            by_phase_ttr[phase].append(ttr)
+
+    by_phase = [
+        {
+            "phase": phase,
+            "n": len(by_phase_returns.get(phase, [])),
+            "max_drawdown": forward_testing_module._distribution_cell(by_phase_mdd.get(phase, []), wf.min_sample),
+            "underwater_days": forward_testing_module._distribution_cell(by_phase_uw.get(phase, []), wf.min_sample),
+            "time_to_recover_days": forward_testing_module._distribution_cell(
+                by_phase_ttr.get(phase, []), wf.min_sample
+            ),
+            "loss_streak": forward_testing_module._loss_streak_cell(by_phase_returns.get(phase, []), wf.streak_min_n),
+        }
+        for phase in cfg.market_phase.labels
+    ]
+
+    return {
+        "horizon": horizon,
+        "min_sample": wf.min_sample,
+        "streak_min_n": wf.streak_min_n,
+        "survivorship_bias": forward_testing_module.SURVIVORSHIP_BIAS_LABEL,
+        "method_note": forward_testing_module.LOSS_STREAK_METHOD_NOTE,
+        "by_phase": by_phase,
+    }
+
+
+@pytest.mark.parametrize("chunk_width", [1, 2, 3, 50])
+def test_drawdown_expectations_chunked_byte_identical_to_pinned_reference(dd_expectations_engine, chunk_width):
+    """The shipped chunked `stored_by_key` read is byte-identical to the pinned pre-fix (unchunked)
+    reference at every chunk width — including widths (1, 2, 3) narrower than this fixture's 4 distinct
+    tickers (AAA/BBB/CCC/DDD), which force MULTIPLE real chunks (not a vacuous single-chunk pass-through)."""
+    cfg = load_config()
+    research_cfg = cfg.research.model_copy(update={"drawdown_expectations_ticker_chunk": chunk_width})
+    cfg = cfg.model_copy(update={"research": research_cfg})
+    with Session(dd_expectations_engine) as session:
+        shipped = compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg)
+    with Session(dd_expectations_engine) as session:
+        reference = _reference_compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg)
+    assert shipped == reference
+
+
+def test_drawdown_expectations_chunk_width_one_issues_multiple_queries(dd_expectations_engine, monkeypatch):
+    """A mutation-style sanity check that the chunking is actually EXERCISED (not dead code): at
+    `drawdown_expectations_ticker_chunk=1` against this fixture's 4 distinct tickers, the chunked read
+    issues MORE THAN ONE `ForwardReturn` query — proving a reverted (unchunked) implementation would be
+    trivially distinguishable from the shipped one by query count, not just by (unchanged) final values."""
+    cfg = load_config()
+    research_cfg = cfg.research.model_copy(update={"drawdown_expectations_ticker_chunk": 1})
+    cfg = cfg.model_copy(update={"research": research_cfg})
+
+    query_count = {"n": 0}
+    with Session(dd_expectations_engine) as session:
+        orig_exec = session.exec
+
+        def _counting_exec(stmt, *a, **kw):
+            text = str(stmt)
+            if "forward_returns" in text and "max_drawdown" in text:
+                query_count["n"] += 1
+            return orig_exec(stmt, *a, **kw)
+
+        session.exec = _counting_exec  # type: ignore[assignment]
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg)
+
+    assert payload is not None
+    assert query_count["n"] > 1, (
+        f"expected multiple chunked ForwardReturn queries at chunk_width=1 over 4 distinct tickers, "
+        f"got {query_count['n']}"
+    )
diff --git a/apps/frontend/app/research/_labs.tsx b/apps/frontend/app/research/_labs.tsx
index f5594c35..e2af8cda 100644
--- a/apps/frontend/app/research/_labs.tsx
+++ b/apps/frontend/app/research/_labs.tsx
@@ -267,7 +267,12 @@ export function FactorLabPage() {
   // badge reads "Not yet proven" (never a fabricated "Proven", never a 500). The badge resolves its status
   // from this list — it computes nothing.
   const [evidenceClaims, setEvidenceClaims] = useState<CertifiedClaim[]>([]);
+  // ops-hardening iter-36 (J-06): a manual re-fetch counter — the SAME `attempt` pattern Regime Lab already
+  // proved (iter-33, UT-11), so a genuine backend-unavailable condition gets a working Retry instead of a
+  // frozen error card.
+  const [attempt, setAttempt] = useState(0);
   const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
+  const elapsedSeconds = useElapsedSeconds(state.kind === "loading");
 
   useEffect(() => {
     const controller = new AbortController();
@@ -278,7 +283,7 @@ export function FactorLabPage() {
         if (!controller.signal.aborted) setState({ kind: "error" });
       });
     return () => controller.abort();
-  }, [asofCutoff, readiness]);
+  }, [asofCutoff, readiness, attempt]);
 
   useEffect(() => {
     const controller = new AbortController();
@@ -293,6 +298,10 @@ export function FactorLabPage() {
   }, []);
 
   const data = state.kind === "ok" ? state.data : null;
+  // ops-hardening iter-36 (J-06): the SAME honest pre-data state Regime Lab already renders
+  // (lib/lab-load-panel.ts) — a brief load stays a plain skeleton; a wait past the grace window becomes an
+  // explicit, time-stamped "still computing" notice; a failure becomes a retryable error card.
+  const panel = resolveLabLoadPanel(state.kind, elapsedSeconds);
 
   return (
     <div className="space-y-4">
@@ -308,8 +317,16 @@ export function FactorLabPage() {
         <WarmingState what="The Factor Lab" />
       ) : (
         <>
-          {state.kind === "loading" ? <LabSkeleton /> : null}
-          {state.kind === "error" ? <ResearchError what="The Factor-Lab evidence" /> : null}
+          {panel.kind === "computing" ? (
+            <SlowComputeNotice what="The Factor Lab" elapsedSeconds={panel.elapsedSeconds} />
+          ) : null}
+          {panel.kind === "skeleton" || panel.kind === "computing" ? <LabSkeleton /> : null}
+          {panel.kind === "error" ? (
+            <ResearchError
+              what="The Factor-Lab evidence"
+              onRetry={() => setAttempt((previous) => previous + 1)}
+            />
+          ) : null}
           {data ? <FactorsTable data={data} scope={scope} evidenceClaims={evidenceClaims} /> : null}
         </>
       )}
@@ -4528,7 +4545,12 @@ type PhaseSeverityLabState =
  *  re-presented; the page recomputes nothing and the sort is a pure view transform. */
 export function PhaseSeverityLabPage() {
   const [state, setState] = useState<PhaseSeverityLabState>({ kind: "loading" });
+  // ops-hardening iter-36 (J-06): a manual re-fetch counter — the SAME `attempt` pattern Regime Lab already
+  // proved (iter-33, UT-11), so a genuine backend-unavailable condition gets a working Retry instead of a
+  // frozen error card.
+  const [attempt, setAttempt] = useState(0);
   const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
+  const elapsedSeconds = useElapsedSeconds(state.kind === "loading");
 
   useEffect(() => {
     const controller = new AbortController();
@@ -4539,9 +4561,13 @@ export function PhaseSeverityLabPage() {
         if (!controller.signal.aborted) setState({ kind: "error" });
       });
     return () => controller.abort();
-  }, [asofCutoff, readiness]);
+  }, [asofCutoff, readiness, attempt]);
 
   const data = state.kind === "ok" ? state.data : null;
+  // ops-hardening iter-36 (J-06): the SAME honest pre-data state Regime Lab already renders
+  // (lib/lab-load-panel.ts) — a brief load stays a plain skeleton; a wait past the grace window becomes an
+  // explicit, time-stamped "still computing" notice; a failure becomes a retryable error card.
+  const panel = resolveLabLoadPanel(state.kind, elapsedSeconds);
 
   return (
     <div className="space-y-4">
@@ -4557,8 +4583,16 @@ export function PhaseSeverityLabPage() {
         <WarmingState what="The Market Phase & Severity Lab" />
       ) : (
         <>
-          {state.kind === "loading" ? <LabSkeleton /> : null}
-          {state.kind === "error" ? <ResearchError what="The Market Phase & Severity-Lab evidence" /> : null}
+          {panel.kind === "computing" ? (
+            <SlowComputeNotice what="The Market Phase & Severity Lab" elapsedSeconds={panel.elapsedSeconds} />
+          ) : null}
+          {panel.kind === "skeleton" || panel.kind === "computing" ? <LabSkeleton /> : null}
+          {panel.kind === "error" ? (
+            <ResearchError
+              what="The Market Phase & Severity-Lab evidence"
+              onRetry={() => setAttempt((previous) => previous + 1)}
+            />
+          ) : null}
           {data ? (
             <>
               <PhaseSeverityLabByLabelTable data={data} scope={scope} />
@@ -4863,6 +4897,11 @@ export function RegimePhaseFactorPage() {
   const [factorFilter, setFactorFilter] = useState<string>(RPF_FILTER_ALL);
   const { sortKey, sortDir, onSort } = useRpfSort("");
   const [pageIndex, setPageIndex] = useState(0);
+  // ops-hardening iter-36 (J-06): a manual re-fetch counter — the SAME `attempt` pattern Regime Lab already
+  // proved (iter-33, UT-11), so a genuine backend-unavailable condition gets a working Retry instead of a
+  // frozen error card.
+  const [attempt, setAttempt] = useState(0);
+  const elapsedSeconds = useElapsedSeconds(state.kind === "loading");
 
   useEffect(() => {
     const controller = new AbortController();
@@ -4873,9 +4912,15 @@ export function RegimePhaseFactorPage() {
         if (!controller.signal.aborted) setState({ kind: "error" });
       });
     return () => controller.abort();
-  }, [factor, asofCutoff, readiness]);
+  }, [factor, asofCutoff, readiness, attempt]);
 
   const data = state.kind === "ok" ? state.data : null;
+  // ops-hardening iter-36 (J-06): the SAME honest pre-data state Regime Lab already renders
+  // (lib/lab-load-panel.ts) — a brief load stays a plain skeleton; a wait past the grace window becomes an
+  // explicit, time-stamped "still computing" notice. This page keeps its OWN inline error card (below) and
+  // `CombinationSkeleton` shape rather than switching to `ResearchError`/`LabSkeleton` — only the
+  // computing/retry SEMANTICS are shared, not the markup.
+  const panel = resolveLabLoadPanel(state.kind, elapsedSeconds);
 
   // a pure client-side filter (the three "All"-default decile dropdowns) → sort (NA-last) → page slice. None
   // refetch or recompute a stored value (J-48/J-56 view-transform contract).
@@ -4986,18 +5031,34 @@ export function RegimePhaseFactorPage() {
             ) : null}
 
             {state.kind === "error" ? (
-              <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
-                <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
-                <div>
+              <div className="flex items-start gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
+                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
+                <div className="space-y-2">
                   <p className="font-medium">Backend unavailable</p>
                   <p className="text-text-muted">
                     The Regime × Phase × Factor study could not load from the API. No figures are shown rather
                     than fabricated values — confirm the backend is running and retry.
                   </p>
+                  <button
+                    type="button"
+                    onClick={() => setAttempt((previous) => previous + 1)}
+                    data-testid="rpf-error-retry"
+                    className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface-2 px-3 text-xs font-medium text-text transition-colors hover:border-border-strong hover:bg-surface focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent active:bg-border"
+                  >
+                    Retry
+                  </button>
                 </div>
               </div>
             ) : !data ? (
-              <CombinationSkeleton />
+              <>
+                {panel.kind === "computing" ? (
+                  <SlowComputeNotice
+                    what="The Regime × Phase × Factor study"
+                    elapsedSeconds={panel.elapsedSeconds}
+                  />
+                ) : null}
+                <CombinationSkeleton />
+              </>
             ) : data.rows.length === 0 ? (
               <EmptyState
                 icon={Microscope}
diff --git a/apps/frontend/app/research/severity-velocity/page.tsx b/apps/frontend/app/research/severity-velocity/page.tsx
index 0e659910..0bd86fe8 100644
--- a/apps/frontend/app/research/severity-velocity/page.tsx
+++ b/apps/frontend/app/research/severity-velocity/page.tsx
@@ -22,8 +22,13 @@ import {
   ResearchCaveat,
   ResearchControls,
   ResearchError,
+  SlowComputeNotice,
+  useElapsedSeconds,
   useResearchControls,
 } from "../_labs";
+// ops-hardening iter-36 (J-06): `resolveLabLoadPanel` is not re-exported from `_labs.tsx` (it is imported
+// there, not re-exported) — sourced directly from its own module, the same way `_labs.tsx` itself does.
+import { resolveLabLoadPanel } from "@/lib/lab-load-panel";
 import { WarmingState, shouldShowWarming } from "@/components/warming-state";
 
 type State =
@@ -46,6 +51,11 @@ export default function SeverityVelocityPage() {
   const [horizon, setHorizon] = useState<number | undefined>(undefined);
   const [state, setState] = useState<State>({ kind: "loading" });
   const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
+  // ops-hardening iter-36 (J-06): a manual re-fetch counter — the SAME `attempt` pattern Regime Lab already
+  // proved (iter-33, UT-11), so a genuine backend-unavailable condition gets a working Retry instead of a
+  // frozen error card.
+  const [attempt, setAttempt] = useState(0);
+  const elapsedSeconds = useElapsedSeconds(state.kind === "loading");
 
   useEffect(() => {
     const controller = new AbortController();
@@ -56,10 +66,14 @@ export default function SeverityVelocityPage() {
         if (!controller.signal.aborted) setState({ kind: "error" });
       });
     return () => controller.abort();
-  }, [horizon, asofCutoff, readiness]);
+  }, [horizon, asofCutoff, readiness, attempt]);
 
   const data = state.kind === "ok" ? state.data : null;
   const selectedHorizon = horizon ?? data?.horizon;
+  // ops-hardening iter-36 (J-06): the SAME honest pre-data state Regime Lab already renders
+  // (lib/lab-load-panel.ts) — a brief load stays a plain skeleton; a wait past the grace window becomes an
+  // explicit, time-stamped "still computing" notice; a failure becomes a retryable error card.
+  const panel = resolveLabLoadPanel(state.kind, elapsedSeconds);
 
   return (
     <div className="space-y-4">
@@ -87,9 +101,18 @@ export default function SeverityVelocityPage() {
         <WarmingState what="The Severity-velocity × Regime study" />
       ) : (
         <>
-          {state.kind === "loading" ? <LabSkeleton /> : null}
-          {state.kind === "error" ? (
-            <ResearchError what="The Severity-velocity × Regime study" />
+          {panel.kind === "computing" ? (
+            <SlowComputeNotice
+              what="The Severity-velocity × Regime study"
+              elapsedSeconds={panel.elapsedSeconds}
+            />
+          ) : null}
+          {panel.kind === "skeleton" || panel.kind === "computing" ? <LabSkeleton /> : null}
+          {panel.kind === "error" ? (
+            <ResearchError
+              what="The Severity-velocity × Regime study"
+              onRetry={() => setAttempt((previous) => previous + 1)}
+            />
           ) : null}
           {data ? <SeverityVelocityBody data={data} scope={scope} /> : null}
         </>
diff --git a/config.yaml b/config.yaml
index c5bbb01b..3f03ec32 100644
--- a/config.yaml
+++ b/config.yaml
@@ -913,6 +913,19 @@ research:
   # normal operation never trips it, but a future data-scale widening logs a WARNING (never raises, never
   # truncates a payload) instead of silently repeating this crash at a larger scale. Boot-validated >= 1.
   factor_pool_max_observations: 2000000
+  # ops-hardening iter-36 (J-07/J-96 AG-8) — the candidate-pool SYMBOLS-axis batch width
+  # `_membership_timeline` loads bars in in-memory-bounded batches (a DIFFERENT unit from
+  # `read_batch_size`/`factor_join_run_chunk` — never reuse either here). 50 symbols/batch against the
+  # live ~590-symbol pool holds ~1/12 of the full price history resident at once instead of the whole
+  # 30-year x 590-symbol product, while still keeping the per-batch query count small (~12 batches).
+  membership_timeline_batch_symbols: 50
+  # ops-hardening iter-36 (J-07 evidence-serving-path) — the TICKER-axis chunk width
+  # `compute_drawdown_expectations` partitions a claim's resolved cohort into before reading each
+  # chunk's stored ForwardReturn rows (each chunk still `yield_per(read_batch_size)`-streamed — that
+  # reuse is `read_batch_size`'s own designed purpose, not this chunk's own width). A DIFFERENT unit
+  # from its neighbors; 50 tickers/chunk bounds a broad claim's cohort read to small chunks instead of
+  # one unbounded `.all()`.
+  drawdown_expectations_ticker_chunk: 50
   factor_lab:
     deciles: 10
     factors:
diff --git a/apps/backend/tests/test_evidence_drawdown_memory_pressure.py b/apps/backend/tests/test_evidence_drawdown_memory_pressure.py
new file mode 100644
index 00000000..ef985e1e
--- /dev/null
+++ b/apps/backend/tests/test_evidence_drawdown_memory_pressure.py
@@ -0,0 +1,262 @@
+"""ops-hardening iter-36 (J-07 evidence-serving-path memory bound, ledger finding iter-35/k) — a REAL,
+non-monkeypatched induction test for `compute_drawdown_expectations`'s `stored_by_key` read, the
+`/api/evidence` serving-path `MemoryError` source iter-35's live run reproduced twice.
+
+WHY A REAL SUBPROCESS INDUCTION, NOT A MONKEYPATCH: mirrors `test_ingest_finalize_memory_pressure.py`'s
+established rationale (this module's sibling drill for the analogous ingest-finalize `MemoryError` catch) —
+a `monkeypatch`-injected `MemoryError` proves the exception HANDLER's code path but never proves the
+mechanism actually triggers under genuine OS-level virtual-memory exhaustion. This spawns real Python
+subprocesses under a genuinely tightened `ulimit -v` (RLIMIT_AS), running the PINNED pre-fix reference
+`compute_drawdown_expectations` body (unchunked `stored_by_key`) against the shipped chunked
+implementation, both against a broad REAL claim's cohort on a disposable COPY of the live committed seed DB
+(544 distinct tickers, 771,662 (ticker, snapshot-date) forward-return pairs at horizon=20 — the exact scale
+class ledger finding iter-35/k's live run hit).
+
+CALIBRATION (measured on this host, `.venv` Python 3.12, claim
+`{kind: factor, factor: leadership_score, slice_kind: total, horizon: 20}` against the live committed seed):
+an unbounded run measures peak RSS ~1,215,052 KB for the pinned reference (unchunked) vs ~1,165,092 KB for
+the shipped (chunked, `research.drawdown_expectations_ticker_chunk=50`) implementation — a real but MODEST
+~50 MB / ~4% reduction (unlike item 1's `_membership_timeline` fix, which is a large architectural bound;
+this fix is the smaller, `.all()` -> chunked-`yield_per` idiom, and `compute_samples`'s own UNCHANGED
+771,662-row materialization dominates the call's total footprint — the residual this iteration's own NOTES
+section calls for disclosing rather than silently rounding away). A `ulimit -v` window of
+1,210,000-1,220,000 KB reproducibly discriminates: the reference aborts with a caught `MemoryError`, the
+shipped implementation completes normally, at EVERY cap tested in that window (repeated). This is a
+NARROWER, more host-sensitive window than `test_ingest_finalize_memory_pressure.py`'s 300 MB window — the
+absolute KB values are calibrated to THIS host/Python build, following that same module's own established
+convention of host-measured absolute caps."""
+from __future__ import annotations
+
+import shutil
+import subprocess
+import sys
+import time
+from pathlib import Path
+
+import pytest
+
+REPO_ROOT = Path(__file__).resolve().parents[3]
+REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
+BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
+
+_CLAIM = {"kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": 20, "direction": "positive"}
+
+# Measured this iteration (see module docstring): the window that reproducibly discriminates reference
+# (unchunked, aborts) from shipped (chunked, completes) on this host.
+TIGHT_CAP_KB = 1_215_000
+# Deep enough that BOTH implementations starve — proves the shipped code still degrades honestly (never a
+# crash/wedge) rather than merely moving the failure point.
+STARVED_CAP_KB = 1_000_000
+# Comfortably clears the whole claim compute for EITHER implementation — the CONTROL cap.
+CONTROL_CAP_KB = 1_600_000
+BOUNDED_TIMEOUT_S = 120.0
+
+
+def _skip_if_no_real_db() -> None:
+    if not REAL_DB.exists():
+        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to reproduce against")
+
+
+def _fresh_seed_copy(tmp_path: Path, name: str) -> Path:
+    """A FRESH, never-cache-polluted disposable copy of the live committed seed DB, ONE PER CALL.
+    `compute_drawdown_expectations_cached` (the real `/api/evidence` entry point this drill exercises)
+    WRITES an `EventStudyCache` row on a MISS — so a copy REUSED across sub-calls would silently turn a
+    later "reference"/"starved" probe into a trivial cache HIT (never re-invoking the compute this drill
+    exists to pressure-test) the moment an EARLIER probe on the SAME copy succeeded. Each probe therefore
+    gets its OWN fresh copy (a local-disk copy of the seed DB measures ~1-2s — cheap relative to the ~20s+
+    compute each probe pays). Never touches the actual committed `apps/backend/data/trendora.db` file."""
+    _skip_if_no_real_db()
+    dest = tmp_path / name
+    shutil.copyfile(REAL_DB, dest)
+    return dest
+
+
+# --------------------------------------------------------------------------------------------------
+# Child-process probe: mirrors evidence.py's OWN isolate-and-continue guard (`build_evidence_payload`,
+# UNTOUCHED by this iteration) — calls `compute_drawdown_expectations_cached` (the exact entry point
+# `GET /api/evidence` uses) wrapped in the SAME `except MemoryError` pattern, printing an honest sentinel
+# either way. `--reference` swaps in the pinned pre-fix (unchunked) implementation via a module-level
+# monkeypatch BEFORE the call — `compute_drawdown_expectations_cached` resolves `compute_drawdown_
+# expectations` by plain module-level name each call, so the swap is picked up with no other change.
+# --------------------------------------------------------------------------------------------------
+_CHILD_PROBE_TEMPLATE = '''
+import sys, json
+sys.path.insert(0, "__BACKEND_ROOT__")
+from sqlmodel import Session, select
+from app.config import load_config
+from app.db import make_engine
+import app.engine.forward_testing as ft
+from app.models import ForwardReturn
+
+db_path = sys.argv[1]
+mode = sys.argv[2]  # "reference" or "shipped"
+claim = __CLAIM__
+
+def _reference_compute_drawdown_expectations(session, claim, config=None):
+    """Pinned pre-fix body (git show HEAD:apps/backend/app/engine/forward_testing.py, iter-36 dispatch
+    commit): ONE unchunked session.exec(fr_stmt).all() builds stored_by_key for the WHOLE cohort at once."""
+    from collections import defaultdict
+    cfg = config or ft.get_config()
+    wf = cfg.walk_forward
+    horizon = claim.get("horizon")
+    if horizon not in wf.underwater_horizons:
+        return None
+    kwargs = ft._claim_samples_kwargs(claim)
+    if kwargs is None:
+        return None
+    from app.engine.market_phase import phase_context_by_date
+    from app.engine.samples import compute_samples
+    try:
+        samples = compute_samples(session, kind=claim.get("kind"), horizon=horizon, config=cfg, as_of=None, **kwargs)
+    except ValueError:
+        return None
+    rows = [r for r in samples["rows"] if r.get("snapshot_date") and r.get("forward_return") is not None]
+    if not rows:
+        return None
+    tickers = sorted({r["ticker"] for r in rows})
+    fr_stmt = select(
+        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
+        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(tickers))
+    stored_by_key = {
+        (symbol, asof_date.isoformat()): (mdd, uw, ttr)
+        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).all()
+    }
+    phases = phase_context_by_date(session, as_of=None, config=cfg)
+    by_phase_mdd, by_phase_uw, by_phase_ttr, by_phase_returns = (defaultdict(list) for _ in range(4))
+    for row in rows:
+        date_iso = row["snapshot_date"]
+        ctx = phases.get(date_iso)
+        if ctx is None:
+            continue
+        phase = ctx["phase"]
+        by_phase_returns[phase].append((date_iso, row["forward_return"]))
+        stored = stored_by_key.get((row["ticker"], date_iso))
+        if stored is None:
+            continue
+        mdd, uw, ttr = stored
+        if mdd is not None: by_phase_mdd[phase].append(mdd)
+        if uw is not None: by_phase_uw[phase].append(uw)
+        if ttr is not None: by_phase_ttr[phase].append(ttr)
+    by_phase = [
+        {
+            "phase": phase, "n": len(by_phase_returns.get(phase, [])),
+            "max_drawdown": ft._distribution_cell(by_phase_mdd.get(phase, []), wf.min_sample),
+            "underwater_days": ft._distribution_cell(by_phase_uw.get(phase, []), wf.min_sample),
+            "time_to_recover_days": ft._distribution_cell(by_phase_ttr.get(phase, []), wf.min_sample),
+            "loss_streak": ft._loss_streak_cell(by_phase_returns.get(phase, []), wf.streak_min_n),
+        }
+        for phase in cfg.market_phase.labels
+    ]
+    return {
+        "horizon": horizon, "min_sample": wf.min_sample, "streak_min_n": wf.streak_min_n,
+        "survivorship_bias": ft.SURVIVORSHIP_BIAS_LABEL, "method_note": ft.LOSS_STREAK_METHOD_NOTE,
+        "by_phase": by_phase,
+    }
+
+if mode == "reference":
+    ft.compute_drawdown_expectations = _reference_compute_drawdown_expectations
+
+cfg = load_config()
+engine = make_engine(f"sqlite:///{db_path}")
+
+# mirrors app.engine.evidence.build_evidence_payload's UNTOUCHED isolate-and-continue guard exactly.
+with Session(engine) as session:
+    try:
+        payload = ft.compute_drawdown_expectations_cached(session, claim, cfg)
+    except MemoryError:
+        print("RESULT=UNAVAILABLE_MEMORYERROR")
+    except Exception as exc:  # noqa: BLE001
+        print(f"RESULT=UNAVAILABLE_OTHER exc={exc!r}")
+    else:
+        has_panel = payload is not None and "by_phase" in payload
+        print(f"RESULT=OK has_panel={has_panel}")
+
+# same-process, fresh-session read afterward -- proves no leaked lock / open transaction blocks recovery.
+with Session(engine) as session:
+    n = len(session.exec(select(ForwardReturn.id).limit(1)).all())
+print(f"SUBSEQUENT_READ_OK n={n}")
+'''
+
+
+def _write_child_probe(tmp_path: Path) -> Path:
+    script_path = tmp_path / "_dd_mem_probe_child.py"
+    text = _CHILD_PROBE_TEMPLATE.replace("__BACKEND_ROOT__", BACKEND_ROOT).replace("__CLAIM__", repr(_CLAIM))
+    script_path.write_text(text)
+    return script_path
+
+
+def _run_child_probe(script_path: Path, db_path: Path, mode: str, cap_kb: int) -> subprocess.CompletedProcess:
+    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path} {mode}"
+    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S)
+
+
+def test_tight_cap_reference_aborts_shipped_completes(tmp_path):
+    """TC-8: at the SAME tight `ulimit -v` cap, the pinned pre-fix (unchunked) reference implementation
+    aborts with a caught `MemoryError` (the exact live iter-35 abort, reproduced), while the shipped
+    (chunked) implementation completes and serves the real computed panel — the measurable failure-rate
+    reduction TC-8 asks for, at the real per-claim live-basis scale (771,662 cohort rows / 544 tickers).
+    Each sub-call gets its OWN fresh DB copy (never reused) so an earlier success can never turn a later
+    probe into a trivial `EventStudyCache` hit."""
+    script_path = _write_child_probe(tmp_path)
+
+    ref_db = _fresh_seed_copy(tmp_path, "ref.db")
+    ref_result = _run_child_probe(script_path, ref_db, "reference", TIGHT_CAP_KB)
+    assert ref_result.returncode == 0, (
+        f"the reference probe must never crash uncaught; stdout={ref_result.stdout!r} stderr={ref_result.stderr!r}"
+    )
+    assert "RESULT=UNAVAILABLE_MEMORYERROR" in ref_result.stdout, (
+        f"expected the pre-fix reference to abort with a caught MemoryError under the tight cap "
+        f"(cap may be miscalibrated too loose — a control-assertion failure, not a silent pass); "
+        f"stdout={ref_result.stdout!r} stderr={ref_result.stderr!r}"
+    )
+    assert "SUBSEQUENT_READ_OK" in ref_result.stdout
+
+    shipped_db = _fresh_seed_copy(tmp_path, "shipped.db")
+    shipped_result = _run_child_probe(script_path, shipped_db, "shipped", TIGHT_CAP_KB)
+    assert shipped_result.returncode == 0, (
+        f"stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
+    )
+    assert "RESULT=OK has_panel=True" in shipped_result.stdout, (
+        f"expected the shipped chunked implementation to complete normally under the SAME tight cap that "
+        f"aborted the reference (cap may be miscalibrated too tight for the shipped code); "
+        f"stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
+    )
+    assert "SUBSEQUENT_READ_OK" in shipped_result.stdout
+
+
+def test_control_generous_cap_both_complete_normally(tmp_path):
+    """Control assertion (mirrors the sibling ingest-finalize drill's own DoD requirement): the IDENTICAL
+    claim/cohort, under a generous cap, completes normally for BOTH implementations — proving the tight-cap
+    abort above is attributable to the cap, not an unrelated bug. A fresh DB copy per mode (see
+    `_fresh_seed_copy`)."""
+    script_path = _write_child_probe(tmp_path)
+    for mode in ("reference", "shipped"):
+        db_copy = _fresh_seed_copy(tmp_path, f"control_{mode}.db")
+        result = _run_child_probe(script_path, db_copy, mode, CONTROL_CAP_KB)
+        assert result.returncode == 0, f"mode={mode} stdout={result.stdout!r} stderr={result.stderr!r}"
+        assert "RESULT=OK has_panel=True" in result.stdout, (
+            f"the generous CONTROL cap unexpectedly failed mode={mode} — the tight-cap result cannot be "
+            f"trusted as cap-attributable until this is fixed; stdout={result.stdout!r} stderr={result.stderr!r}"
+        )
+
+
+def test_starved_cap_shipped_still_degrades_honestly_never_crashes(tmp_path):
+    """Under pressure severe enough that the SHIPPED (chunked) implementation ALSO starves, it still
+    degrades exactly as honestly as the reference — a caught MemoryError, never an uncaught crash/wedge —
+    the residual this iteration's NOTES section calls for disclosing rather than silently claiming a full
+    bound (the chunking reduces failure likelihood at a given pressure level; it does not make the read
+    immune to arbitrarily severe pressure, since `stored_by_key`'s FINAL size is unchanged by chunking)."""
+    script_path = _write_child_probe(tmp_path)
+    db_copy = _fresh_seed_copy(tmp_path, "starved.db")
+    result = _run_child_probe(script_path, db_copy, "shipped", STARVED_CAP_KB)
+    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    assert "RESULT=UNAVAILABLE_MEMORYERROR" in result.stdout, (
+        f"expected the shipped implementation to ALSO honestly degrade under severe enough pressure "
+        f"(never a silent success that would suggest an unrealistic full bound); "
+        f"stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
+    assert "SUBSEQUENT_READ_OK" in result.stdout, (
+        "expected the SAME process to still serve a fresh read after the caught MemoryError — never a "
+        f"wedge; stdout={result.stdout!r} stderr={result.stderr!r}"
+    )
diff --git a/apps/backend/tests/test_membership_timeline_batch_bound.py b/apps/backend/tests/test_membership_timeline_batch_bound.py
new file mode 100644
index 00000000..dc37e924
--- /dev/null
+++ b/apps/backend/tests/test_membership_timeline_batch_bound.py
@@ -0,0 +1,336 @@
+"""ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — the batched-by-symbol bound on
+`_membership_timeline`'s (`app.engine.data_manager`, lines 497-544 pre-fix) candidate-pool bar loading.
+
+Ledger finding iter-29/d: `_membership_timeline`'s cold-compute called `prefilled_bar_cache(session,
+expected_symbols=pool_symbols)`, which loads EVERY symbol's FULL date-ordered series in ONE unbounded
+streamed query REGARDLESS of `expected_symbols` (`prices.py::_BarCache.prefill` scans the whole
+`daily_prices` table; `expected_symbols` only back-fills empty series for names the scan didn't find) — so
+peak resident bar data scaled with the full candidate pool x its whole price history (measured live:
+~548-591 symbols, ~3.3M rows, 1996-01-02 -> 2026-07-22, ~1880 snapshot dates). `_compute_coverage_uncached`
+ALSO opened its own such context around the whole coverage derivation (including this same cold-compute),
+so the peak-memory cost was paid on EVERY standalone coverage compute (e.g. `refresh_coverage_snapshot`'s
+ingest-finalize call for the current date), not merely on a rare cold `/data` page load.
+
+This iteration bounds it: the candidate pool is walked in `research.membership_timeline_batch_symbols`-wide
+batches, each batch's bars loaded via `_BarCache.load_only` (REPLACING the same instance's contents, never a
+second cache instance), resolved against every snapshot date, then discarded before the next batch loads
+(`data_manager._excluded_counts_by_date`). `_compute_coverage_uncached` no longer opens its own eager
+whole-table context (`data_manager.py`, iter-36 docstring) — an outer job-scoped cache (e.g. `_do_backfill`,
+which legitimately wants the whole pool resident across a multi-date job) is still reused unchanged when
+already active.
+
+Named proofs, each guarding a DoD/TC line — ALL THREE reuse the SAME pair of live-DB computations (one
+reference call, one shipped call, each paid exactly ONCE via the module-scoped fixture below) rather than
+re-running the ~10-30s live-basis compute per assertion:
+
+  TC-2 byte-identity   — the pinned PRE-FIX body (`git show HEAD:apps/backend/app/engine/data_manager.py`
+                        at the iter-36 dispatch commit) produces a BYTE-IDENTICAL `_membership_timeline`
+                        payload to the shipped post-fix implementation, on the live committed seed DB.
+  TC-3 mutation-style   — against the REAL `config.universe.symbols`-scale live basis (not a fixture-sized
+                        substitute), the shipped batch width actually bounds peak resident bar data (every
+                        `load_only` batch <= the configured width, > 1 batch used); the SAME instrumentation
+                        applied to the reference implementation shows it would NOT satisfy that bound
+                        (proving the assertion fails if the fix were reverted).
+  TC-1 peak measurement — a `tracemalloc` peak comparison (reference vs shipped) on the live basis, printed
+                        for `reports/perf-budgets.md` and asserted to show a real reduction.
+
+Fast-skips when the committed seed DB is absent (matches the established `REAL_DB`/`test_start_backend_
+script.py` convention — this is a live-basis proof, not a hand-built-fixture unit test).
+"""
+from __future__ import annotations
+
+import tracemalloc
+from pathlib import Path
+
+import pytest
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import make_engine
+from app.engine import prices as prices_module
+from app.engine import universe_resolver
+from app.engine.data_manager import _membership_labels, _membership_timeline, _trading_days
+from app.engine.prices import _BarCache, attach_shared_cache, prefilled_bar_cache
+from app.engine.universe_screen import read_pool
+from app.models import ScannerResult, ScannerRun
+
+REPO_ROOT = Path(__file__).resolve().parents[3]
+REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
+
+# every `stride`-th real snapshot date (always including the first and last). Peak resident bar data is
+# driven by the CANDIDATE-POOL x PRICE-HISTORY load, not by how many dates are then resolved against it, so
+# a stride sample over the real ~1880-date range still exercises the real ~548-symbol/30-year price basis
+# this iteration bounds, while keeping this module's total live-DB wall-clock cost bounded.
+_DATE_STRIDE = 61
+
+
+# ====================================================================================================
+# Pinned PRE-FIX reference implementation (`git show HEAD:apps/backend/app/engine/data_manager.py` at the
+# iter-36 dispatch commit — the tree BEFORE this iteration's edits), verbatim.
+# ====================================================================================================
+def _reference_membership_timeline(session: Session, cfg, snapshot_dates: list) -> dict:
+    """Verbatim pre-fix `_membership_timeline` body (data_manager.py:497-544 before this iteration): ONE
+    unbounded `prefilled_bar_cache(expected_symbols=pool_symbols)` call loads EVERY candidate-pool symbol's
+    FULL series up front; every snapshot date's excluded-by-reason tally is then read from that single,
+    never-discarded, whole-pool-resident cache."""
+    dates = sorted(snapshot_dates)
+    pool_symbols = {row["symbol"] for row in read_pool()}
+    pool_count = len(pool_symbols)
+    points: list[dict] = []
+    seen: set = set()
+    prev_members: set = set()
+
+    rows = session.exec(
+        select(ScannerRun.asof_date, ScannerResult.ticker)
+        .join(ScannerResult, ScannerResult.run_id == ScannerRun.id)
+    ).all()
+    members_by_date: dict = {}
+    for asof_date, ticker in rows:
+        members_by_date.setdefault(asof_date, set()).add(ticker.upper())
+
+    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
+        for d in dates:
+            members = members_by_date.get(d, set())
+            entries = sorted(m for m in members if m not in seen)
+            exits = sorted(m for m in prev_members if m not in members)
+            seen |= members
+            prev_members = members
+            diag = universe_resolver.resolve_with_reasons(session, d, cfg)
+            points.append({
+                "date": d.isoformat(),
+                "size": len(members),
+                "entries": entries,
+                "exits": exits,
+                "excluded": dict(diag["excluded_counts"]),
+            })
+
+    return {
+        "candidate_pool_count": pool_count,
+        "points": points,
+        "labels": _membership_labels(session, cfg),
+    }
+
+
+def _skip_if_no_real_db() -> None:
+    if not REAL_DB.exists():
+        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to measure against")
+
+
+@pytest.fixture(scope="module")
+def live_comparison():
+    """Runs the reference (pre-fix, unbounded) and shipped (post-fix, batched) `_membership_timeline`
+    implementations EXACTLY ONCE EACH against the live committed seed DB, for the same sampled snapshot
+    dates — capturing everything TC-1/TC-2/TC-3 need from those two calls (payload, tracemalloc peak, and
+    the `_BarCache.load_only`/`prefill` batch sizes each call issued) so no test below re-pays the ~10-30s
+    live-basis compute."""
+    _skip_if_no_real_db()
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{REAL_DB}")
+
+    with Session(engine) as session:
+        pool_size = len({row["symbol"] for row in read_pool()})
+        all_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
+    sample = all_dates[::_DATE_STRIDE]
+    if all_dates and sample[-1] != all_dates[-1]:
+        sample.append(all_dates[-1])
+    assert len(sample) >= 5, "sanity: the live seed must carry a real multi-date snapshot history"
+
+    batch_width = cfg.research.membership_timeline_batch_symbols
+    assert pool_size > batch_width, (
+        f"sanity: the live candidate pool ({pool_size} symbols) must exceed the configured batch width "
+        f"({batch_width}) — otherwise this module cannot distinguish batched from unbounded loading"
+    )
+
+    # --- REFERENCE: instrument `_BarCache.prefill` (its own loading call) -------------------------------
+    prefill_sizes: list[int] = []
+    orig_prefill = prices_module._BarCache.prefill
+
+    def _counting_prefill(self, session, expected_symbols=None):
+        orig_prefill(self, session, expected_symbols=expected_symbols)
+        prefill_sizes.append(len(self._by_symbol))
+
+    with Session(engine) as session:
+        prices_module._BarCache.prefill = _counting_prefill
+        try:
+            tracemalloc.start()
+            reference_payload = _reference_membership_timeline(session, cfg, sample)
+            _, reference_peak = tracemalloc.get_traced_memory()
+        finally:
+            tracemalloc.stop()
+            prices_module._BarCache.prefill = orig_prefill
+
+    # --- SHIPPED: instrument `_BarCache.load_only` (its own loading call) -------------------------------
+    load_only_sizes: list[int] = []
+    orig_load_only = prices_module._BarCache.load_only
+
+    def _counting_load_only(self, session, symbols):
+        symbol_list = list(symbols)
+        load_only_sizes.append(len(symbol_list))
+        return orig_load_only(self, session, symbol_list)
+
+    with Session(engine) as session:
+        prices_module._BarCache.load_only = _counting_load_only
+        try:
+            tracemalloc.start()
+            shipped_payload = _membership_timeline(session, cfg, sample)
+            _, shipped_peak = tracemalloc.get_traced_memory()
+        finally:
+            tracemalloc.stop()
+            prices_module._BarCache.load_only = orig_load_only
+
+    return {
+        "cfg": cfg,
+        "batch_width": batch_width,
+        "pool_size": pool_size,
+        "reference_payload": reference_payload,
+        "shipped_payload": shipped_payload,
+        "reference_peak": reference_peak,
+        "shipped_peak": shipped_peak,
+        "prefill_sizes": prefill_sizes,
+        "load_only_sizes": load_only_sizes,
+    }
+
+
+# ====================================================================================================
+# TC-2 — byte-identity, live seed DB
+# ====================================================================================================
+def test_membership_timeline_byte_identical_to_pinned_reference_on_live_seed(live_comparison):
+    assert live_comparison["shipped_payload"] == live_comparison["reference_payload"], (
+        "the shipped batched _membership_timeline diverged from the pinned pre-fix reference on the live "
+        "seed DB — the batched loading must be a pure performance/memory refactor (byte-identical output)"
+    )
+
+
+# ====================================================================================================
+# TC-2, COVERAGE-PAYLOAD half (added by the iter-36 audit, finding B1)
+#
+# The TC-2 test ABOVE pins only `_membership_timeline`'s own dict (candidate_pool_count / points /
+# labels). The phase spec's TC-2 and its Definition of Done name the WHOLE served coverage payload
+# (`universe_count`, `per_symbol`, `membership_timeline`, `gaps`, `capacity`), and this iteration's
+# SECOND data_manager edit — `_compute_coverage_uncached` no longer opening its own outer
+# `prefilled_bar_cache` around `_compute_coverage_body` — is precisely what the test above does NOT
+# cover. That removal changes which BRANCH two coverage readers take on the standalone entry point
+# (`refresh_coverage_snapshot`'s ingest-finalize call, the boot warm-up safety net, a cold tooling call):
+#
+#   `_resolved_universe` -> `universe_resolver.resolve_with_reasons`   (feeds `universe_count`,
+#        `universe_asof`, `candidate_pool_count`, `universe_diagnostic`, `absent_from_latest_snapshot`)
+#        — was: `active_bar_cache` HIT -> `trailing_count` over the once-loaded series + cached
+#               `bars_asof` (lightweight `Bar` records)
+#        — now: no active cache -> the grouped `count(DailyPrice.id) WHERE date <= asof` prefilter +
+#               the per-symbol `DailyPrice` ORM `bars_asof` query
+#   `_trading_days` -> `bars_asof(benchmark, latest)`   (feeds `trading_day_count`, `gap_count`,
+#        `gap_first`/`gap_last`, `gaps_preview`, and the intra-series-gap diagnostic's calendar)
+#
+# Every OTHER field in `_compute_coverage_body` (`per_symbol`, the missing-data diagnostic, the
+# snapshot/price aggregates) is derived from grouped SQL that never consults the bar cache, so it cannot
+# differ between the two conditions; the membership timeline itself is already covered by TC-2 above.
+# This test therefore pins exactly the two cache-sensitive readers, on the LIVE seed DB.
+#
+# Bounded by construction (this module must not add a second whole-table prefill): the cached side is
+# built one shipped-width batch at a time via `_BarCache.load_only` — never `prefill`. That is a SOUND
+# proof of the full-pool claim because `resolve_with_reasons` classifies each candidate INDEPENDENTLY
+# (per-symbol trailing count -> per-symbol gates -> a per-reason tally with no cross-symbol interaction),
+# so branch-agreement on every symbol of a batch is branch-agreement on any union of batches.
+# ====================================================================================================
+def test_coverage_payload_bar_readers_byte_identical_with_and_without_outer_cache():
+    _skip_if_no_real_db()
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{REAL_DB}")
+
+    pool = sorted({row["symbol"] for row in read_pool()})
+    width = cfg.research.membership_timeline_batch_symbols
+    with Session(engine) as session:
+        all_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
+    assert len(all_dates) >= 4 and len(pool) > width, (
+        "sanity: this proof needs the real multi-date live basis and a pool wider than one batch"
+    )
+    # an early date (almost nothing admitted yet), two interior dates, and the latest — the as-of
+    # `_resolved_universe` itself resolves at by default. Different admission regimes exercise all four
+    # gates (below_history / stale_series / below_price / below_adv) across the two branches.
+    probe_dates = [
+        all_dates[0], all_dates[len(all_dates) // 3], all_dates[2 * len(all_dates) // 3], all_dates[-1],
+    ]
+
+    compared = 0
+    for batch_index in range(4):
+        batch = pool[batch_index * width : (batch_index + 1) * width]
+        if not batch:
+            break
+        for d in probe_dates:
+            # SHIPPED condition: no bar cache active (the branch the removed outer prefill now leaves).
+            with Session(engine) as uncached_session:
+                uncached = universe_resolver.resolve_with_reasons(uncached_session, d, cfg, symbols=batch)
+            # PRE-FIX condition: the outer `prefilled_bar_cache` the removed wrap used to hold open —
+            # reproduced batch-bounded (`load_only`), which loads the SAME full per-symbol series
+            # `prefill` would have, for these symbols.
+            with Session(engine) as cached_session:
+                cache = _BarCache()
+                with attach_shared_cache(cached_session, cache):
+                    cache.load_only(cached_session, batch)
+                    cached = universe_resolver.resolve_with_reasons(
+                        cached_session, d, cfg, symbols=batch
+                    )
+            assert uncached == cached, (
+                f"the coverage path's universe resolution diverged between the pre-fix (bar-cache-active) "
+                f"and shipped (no-cache) branches at asof={d} for symbols {batch[0]}..{batch[-1]} — "
+                f"removing `_compute_coverage_uncached`'s outer prefill must be byte-identical"
+            )
+            compared += 1
+    assert compared >= 8, f"expected a real multi-batch/multi-date comparison, ran only {compared}"
+
+    # `_trading_days` — the other cache-sensitive coverage reader (benchmark series only, so this side
+    # is inherently bounded). Feeds trading_day_count / gap_count / gap_first / gap_last / gaps_preview.
+    with Session(engine) as uncached_session:
+        days_uncached = _trading_days(uncached_session, cfg)
+    with Session(engine) as cached_session:
+        cache = _BarCache()
+        with attach_shared_cache(cached_session, cache):
+            cache.load_only(cached_session, [cfg.etfs.index[0]])
+            days_cached = _trading_days(cached_session, cfg)
+    assert days_uncached, "sanity: the live seed must carry a benchmark calendar"
+    assert days_uncached == days_cached, (
+        "the coverage trading calendar diverged between the pre-fix (bar-cache-active) and shipped "
+        "(no-cache) branches — gap_count/gaps_preview/trading_day_count would not be byte-identical"
+    )
+
+
+# ====================================================================================================
+# TC-3 — mutation-style regression: the shipped batch width bounds peak resident symbols at the REAL live
+# basis; the SAME instrumentation applied to the reference implementation shows the assertion would FAIL
+# if the fix were reverted (binding iter-31 lesson: "would this fail if the fix were reverted?").
+# ====================================================================================================
+def test_shipped_batch_width_bounds_peak_resident_symbols_fails_if_reverted(live_comparison):
+    load_only_sizes = live_comparison["load_only_sizes"]
+    batch_width = live_comparison["batch_width"]
+    assert load_only_sizes, "expected the shipped bound to issue at least one load_only() batch"
+    assert max(load_only_sizes) <= batch_width, (
+        f"a shipped load_only() batch exceeded the configured width {batch_width}: max={max(load_only_sizes)}"
+    )
+    assert len(load_only_sizes) > 1, "expected multiple batches at this live pool scale — got only one"
+
+    prefill_sizes = live_comparison["prefill_sizes"]
+    assert prefill_sizes, "expected the reference implementation to prefill at least once"
+    assert max(prefill_sizes) > batch_width, (
+        f"the reverted/pre-fix reference loaded only {max(prefill_sizes)} symbols at once, not exceeding "
+        f"the batch width {batch_width} — this test would not actually catch a revert (not a real mutation "
+        f"proof); expected it to load the whole live pool ({live_comparison['pool_size']} symbols) at once"
+    )
+
+
+# ====================================================================================================
+# TC-1 — peak-memory measurement (reference vs shipped), printed for reports/perf-budgets.md
+# ====================================================================================================
+def test_peak_memory_reduced_vs_pinned_reference_on_live_seed(live_comparison, capsys):
+    reference_peak = live_comparison["reference_peak"]
+    shipped_peak = live_comparison["shipped_peak"]
+    with capsys.disabled():
+        print(
+            f"\n[perf-budgets] _membership_timeline peak tracemalloc bytes — "
+            f"reference (unbounded, pre-fix): {reference_peak:,}  |  "
+            f"shipped (batch_symbols={live_comparison['batch_width']}): {shipped_peak:,}  |  "
+            f"reduction: {100 * (1 - shipped_peak / reference_peak):.1f}%"
+        )
+    assert shipped_peak < reference_peak * 0.7, (
+        f"expected a real peak-memory reduction from batching: reference={reference_peak:,} bytes, "
+        f"shipped={shipped_peak:,} bytes (only {100 * (1 - shipped_peak / reference_peak):.1f}% reduction)"
+    )
```
