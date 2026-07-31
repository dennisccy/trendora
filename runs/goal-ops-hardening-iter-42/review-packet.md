# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index edb84c33..c5cad8a1 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -30,6 +30,17 @@ from app.config import get_config
 from app.models import DailyPrice
 
 
+# ops-hardening iter-42 (B6, AG-8): the honest NA sentinel `_BarCache.prefill`'s row loop substitutes
+# for a NULL numeric column instead of letting `array.array('d').append(None)` raise `TypeError`.
+# `app/models.py`'s five `DailyPrice` numeric columns are all currently declared NOT NULL (this
+# cannot fire against today's schema), but AG-8 explicitly names "new nulls" as a data-shape widening
+# every existing consumer must survive without crashing — this is that defensive fix, ahead of the
+# widening actually landing. `float("nan")` degrades every downstream float computation honestly (NaN
+# propagates through arithmetic/comparisons instead of raising) rather than dropping the bar entirely,
+# which would silently shift a symbol's bar count out from under its date-aligned columns.
+_NULL_NUMERIC_SENTINEL = float("nan")
+
+
 class Bar(NamedTuple):
     """A lightweight, immutable row-slice used by the load-once bar cache (J-46) instead of a full
     `DailyPrice` ORM instance (iter-19 — the OOM fix). Exposes EXACTLY the attributes every downstream
@@ -205,33 +216,64 @@ class _BarCache:
         through the exact same `full[:cut]` / `full[cut-1]` / `len(full)` operations it already used, and
         `_SymbolColumns` implements the full `Sequence` protocol those operations need — so none of those
         methods change. The `.yield_per(batch)` cursor streaming above is unchanged (already bounded since
-        before iter-35); this closes the OTHER half — the destination the streamed rows accumulate into."""
+        before iter-35); this closes the OTHER half — the destination the streamed rows accumulate into.
+
+        iter-42 (bound attempt #5, AG-8): when `expected_symbols` is given, the SELECT is now filtered
+        `WHERE symbol IN (expected_symbols)` — the same shape `load_only` (below) already proves — instead
+        of an unconditional whole-table scan. Every real caller (`_do_backfill`, `_persist_per_date_
+        coverage_snapshots`'s fallback) already passes `expected_symbols=pool_symbols` (the candidate-pool
+        listing), so this is not a theoretical lever: measured against the live basis, `daily_prices` (591
+        symbols) is a STRICT superset of the candidate pool (548 symbols) — 43 symbols with bars (index/
+        sector/thematic ETFs: SPY, QQQ, ^VIX, the XL* sector ETFs, etc. — never candidate-pool members,
+        only read for regime/market-phase inputs) are NOT in `expected_symbols`, accounting for 195,457 of
+        3,301,686 rows (~5.9%) — see `reports/perf-budgets.md`'s iteration-42 section for the live
+        measurement and the row/symbol counts this docstring's numbers are drawn from. Those excluded
+        symbols are NOT dropped from the cache: any consumer that reads one (`bars_asof`/`bars_asof_window`
+        via the module-level functions, which route through THIS cache when a `bar_cache` context is
+        active — confirmed by inspection: `regime.py`'s MA-stack/VIX-gate reads and `market_phase.py`'s
+        benchmark/^VIX reads both go through `bars_asof`/`bars_asof_window`) falls into the EXISTING lazy
+        per-symbol load path below (`if full is None: ... one per-symbol query`), which loads and memoizes
+        that ONE symbol's full series exactly once for the life of the cache — the SAME load-once-per-job
+        guarantee, served byte-identically, just via the lazy branch instead of the eager scan for the
+        handful of non-pool names actually touched. `expected_symbols is None` (every test-only direct
+        `.prefill(session)` call with no argument) keeps the prior unconditional whole-table scan,
+        byte-identical to before this change. An empty (but non-None) `expected_symbols` short-circuits to
+        zero rows without issuing a malformed `WHERE symbol IN ()` — mirrors `load_only`'s own empty-list
+        guard."""
         with self._load_lock:
             need_scan = not self._prefilled
         if need_scan:
             batch = get_config().research.read_batch_size
-            stmt = (
-                select(
-                    DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
-                    DailyPrice.low, DailyPrice.close, DailyPrice.volume,
-                )
-                .order_by(DailyPrice.symbol, DailyPrice.date)
-            )
+            symbol_filter = sorted(set(expected_symbols)) if expected_symbols is not None else None
             by_symbol: dict[str, _SymbolColumns] = {}
-            for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
-                cols = by_symbol.get(symbol)
-                if cols is None:
-                    cols = _SymbolColumns(
-                        [], array.array("d"), array.array("d"), array.array("d"),
-                        array.array("d"), array.array("d"),
+            if symbol_filter is None or symbol_filter:
+                stmt = (
+                    select(
+                        DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
+                        DailyPrice.low, DailyPrice.close, DailyPrice.volume,
                     )
-                    by_symbol[symbol] = cols
-                cols.dates.append(d)
-                cols.opens.append(o)
-                cols.highs.append(h)
-                cols.lows.append(lo)
-                cols.closes.append(c)
-                cols.volumes.append(v)
+                    .order_by(DailyPrice.symbol, DailyPrice.date)
+                )
+                if symbol_filter is not None:
+                    stmt = stmt.where(DailyPrice.symbol.in_(symbol_filter))
+                for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
+                    cols = by_symbol.get(symbol)
+                    if cols is None:
+                        cols = _SymbolColumns(
+                            [], array.array("d"), array.array("d"), array.array("d"),
+                            array.array("d"), array.array("d"),
+                        )
+                        by_symbol[symbol] = cols
+                    cols.dates.append(d)
+                    # iter-42 (B6, AG-8): substitute the honest NA sentinel for a NULL numeric field
+                    # instead of letting `array.array('d').append(None)` raise `TypeError` — see the
+                    # module-level `_NULL_NUMERIC_SENTINEL` comment. Unreachable on the current NOT
+                    # NULL schema; a defensive degrade for a future widening, not a live bug fix.
+                    cols.opens.append(o if o is not None else _NULL_NUMERIC_SENTINEL)
+                    cols.highs.append(h if h is not None else _NULL_NUMERIC_SENTINEL)
+                    cols.lows.append(lo if lo is not None else _NULL_NUMERIC_SENTINEL)
+                    cols.closes.append(c if c is not None else _NULL_NUMERIC_SENTINEL)
+                    cols.volumes.append(v if v is not None else _NULL_NUMERIC_SENTINEL)
             # publish atomically under the lock so a concurrent reader sees a fully-built map, not a
             # partial one; re-check `_prefilled` in case another thread raced us to the scan (rare —
             # `_BarCache` is normally driven by one orchestrating thread — but the merge below is
diff --git a/apps/backend/tests/test_bar_cache.py b/apps/backend/tests/test_bar_cache.py
index df590c08..4efa497e 100644
--- a/apps/backend/tests/test_bar_cache.py
+++ b/apps/backend/tests/test_bar_cache.py
@@ -16,6 +16,7 @@ These run on a SINGLE module-scoped seed load (the real engines), so the equalit
 """
 from __future__ import annotations
 
+import math
 from datetime import date
 
 import pytest
@@ -144,6 +145,126 @@ def test_prefill_old_vs_new_implementation_byte_identical(tiny_engine):
         assert list(new_by_symbol[symbol]) == list(old_by_symbol[symbol])
 
 
+def test_prefill_symbol_filtered_query_when_expected_symbols_given(tiny_engine):
+    """iter-42 (bound attempt #5, AG-8): `prefill(expected_symbols=...)` issues a `WHERE symbol IN
+    (...)`-filtered query -- mirroring `load_only`'s already-proven shape -- instead of the
+    unconditional whole-table scan `expected_symbols=None` still uses. Proves the filtered path is
+    GENUINELY engaged (the iter-37 lesson: assert the condition was actually live, not merely present
+    in the code): SPY has real bars in this fixture but is NOT named in `expected_symbols`, so it must
+    be entirely ABSENT from the cache immediately after `prefill` -- the eager scan really did skip
+    it, this isn't a no-op filter. SPY then falls back to the EXISTING lazy per-symbol load on first
+    access (unchanged by this iteration), loading with exactly ONE additional query and serving a
+    value byte-identical to a full-scan prefill's own result for that symbol."""
+    engine, days = tiny_engine
+    with Session(engine) as reference_session:
+        reference_spy = [
+            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
+            for bar in reference_session.exec(
+                select(DailyPrice).where(DailyPrice.symbol == "SPY").order_by(DailyPrice.date)
+            ).all()
+        ]
+        reference_aaa = [
+            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
+            for bar in reference_session.exec(
+                select(DailyPrice).where(DailyPrice.symbol == "AAA").order_by(DailyPrice.date)
+            ).all()
+        ]
+    with Session(engine) as session:
+        cache = prices._BarCache()
+        cache.prefill(session, expected_symbols=["AAA"])
+        # LIVE proof the filter genuinely engaged: SPY has real bars in this fixture but was excluded
+        # from expected_symbols, so it must be ABSENT from the eager scan's result set.
+        assert set(cache._by_symbol) == {"AAA"}, (
+            f"SPY should be excluded from the filtered eager scan, got {set(cache._by_symbol)}"
+        )
+        aaa_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in cache._by_symbol["AAA"]]
+        assert aaa_bars == reference_aaa
+        assert all(isinstance(b, prices.Bar) for b in cache._by_symbol["AAA"])
+
+        # SPY was never in expected_symbols -> the unchanged lazy per-symbol path loads it on first
+        # access: exactly ONE additional query, byte-identical result.
+        calls = {"n": 0}
+        orig_exec = session.exec
+
+        def _counting_exec(stmt, *a, **kw):
+            calls["n"] += 1
+            return orig_exec(stmt, *a, **kw)
+
+        session.exec = _counting_exec  # type: ignore[assignment]
+        spy_via_cache = [
+            (b.date, b.open, b.high, b.low, b.close, b.volume)
+            for b in cache.bars_asof(session, "SPY", days[-1])
+        ]
+        assert calls["n"] == 1, "SPY must lazy-load with exactly one query (the eager scan skipped it)"
+        assert spy_via_cache == reference_spy
+        cache.bars_asof(session, "SPY", days[-1])  # second access: load-once holds, no re-query
+        assert calls["n"] == 1
+
+
+def test_prefill_empty_expected_symbols_loads_nothing_no_malformed_query(tiny_engine):
+    """`expected_symbols=[]` (a genuinely empty, but non-None, candidate set) must short-circuit to
+    zero eagerly-loaded rows without ever issuing a malformed `WHERE symbol IN ()` -- mirrors
+    `load_only`'s own empty-list guard. Distinct from `expected_symbols=None` (unconditional full scan,
+    proven by other tests in this file)."""
+    engine, days = tiny_engine
+    with Session(engine) as session:
+        cache = prices._BarCache()
+        cache.prefill(session, expected_symbols=[])
+        assert cache._by_symbol == {}
+        assert cache._prefilled is True  # the (empty) scan still ran/completed once
+
+
+def test_prefill_null_numeric_column_degrades_without_crashing(tiny_engine):
+    """B6 (AG-8): a NULL numeric column in a `daily_prices` row -- a data-shape widening not
+    reachable against the current schema's NOT NULL columns, but one AG-8 requires surviving --
+    must not crash `_BarCache.prefill` with `array.array('d').append(None)`'s `TypeError`. Simulates
+    the NULL by tampering with ONE row's `close` value as it streams out of the REAL query (the exact
+    boundary this fix hardens) instead of fighting the DB's own NOT NULL constraint, which would
+    reject the insert before `prefill` ever runs."""
+    engine, days = tiny_engine
+
+    class _NullInjectingResult:
+        """Proxies every attribute to the real SQLAlchemy result except `yield_per`, whose stream it
+        taps to null out exactly one row's `close` value -- an honest simulation of a NULL numeric
+        column arriving from the DB, without needing to defeat the model's NOT NULL constraint."""
+
+        def __init__(self, real):
+            self._real = real
+
+        def yield_per(self, n):
+            tampered = False
+            for row in self._real.yield_per(n):
+                row = list(row)
+                # prefill's own column-projected query yields 7-tuples (symbol, date, open, high,
+                # low, close, volume); a per-symbol lazy load yields 6 (no symbol) -- so this only
+                # ever tampers with prefill's accumulation loop, never the lazy fallback.
+                if not tampered and len(row) == 7 and row[0] == "AAA" and row[1] == days[0]:
+                    row[5] = None  # close
+                    tampered = True
+                yield tuple(row)
+
+        def __getattr__(self, name):
+            return getattr(self._real, name)
+
+    with Session(engine) as session:
+        orig_exec = session.exec
+
+        def _exec_with_one_null_close(stmt, *a, **kw):
+            return _NullInjectingResult(orig_exec(stmt, *a, **kw))
+
+        session.exec = _exec_with_one_null_close  # type: ignore[assignment]
+        cache = prices._BarCache()
+        cache.prefill(session)  # must NOT raise TypeError
+
+    bars = list(cache._by_symbol["AAA"])
+    assert math.isnan(bars[0].close), f"a NULL close should degrade to the NA sentinel, got {bars[0].close!r}"
+    # every OTHER field on that same row is unaffected.
+    assert bars[0].date == days[0] and bars[0].open == 10.0 and bars[0].high == 11.0 and bars[0].low == 9.0
+    # every other row/symbol is unaffected.
+    assert not math.isnan(bars[1].close)
+    assert all(not math.isnan(b.close) for b in cache._by_symbol["SPY"])
+
+
 def test_lazy_load_returns_bar_records_matching_plain_query_row_level(tiny_engine):
     """The lazy per-symbol fallback inside `bars_asof` (already per-symbol-bounded — iter-19 only changes
     its record type, never its bounding) also returns `Bar` records whose values match a plain reference
@@ -423,7 +544,21 @@ def test_kdate_backfill_loads_each_symbol_at_most_once(seed_engine, monkeypatch)
     every full-series bar-store load (the orchestrator's `prefill` up front + any lazy load) and
     asserting no symbol is loaded twice, while >= K dates are scanned (without the cache each symbol
     would be loaded >= K times). The shared pre-filled cache is what preserves load-once under the
-    parallel build (workers READ the orchestrator's pre-loaded immutable series)."""
+    parallel build (workers READ the orchestrator's pre-loaded immutable series).
+
+    iter-42 (bound attempt #5) instrumentation note: `prefill` now eager-loads only the candidate-pool
+    subset (`expected_symbols`); a handful of non-pool symbols (SPY, QQQ, ^VIX, sector/thematic ETFs —
+    read by regime/market-phase inputs) fall into the EXISTING lazy per-symbol path in `bars_asof`
+    instead, and — for the FIRST time — that lazy path is now genuinely reachable from MULTIPLE
+    parallel worker threads racing to read the SAME not-yet-loaded symbol during this job. A
+    check-then-count wrapper around `bars_asof` (`if symbol not in self._by_symbol: count()`, called
+    BEFORE the real load) races against that same concurrency: two threads can both observe "not yet
+    loaded" before either has stored it, over-counting a symbol whose real, `_load_lock`-guarded
+    assignment only ever happens once. Instrumenting the ACTUAL write to `_by_symbol` instead (a
+    dict-subclass `__setitem__` hook — a single GIL-atomic operation, so it cannot double-fire even
+    under concurrent access) removes that false-positive risk while proving the identical, real
+    invariant: every entry in `_by_symbol` is written exactly once for the whole job, whichever of
+    `prefill`'s eager scan, `prefill`'s no-bar bookkeeping, or `bars_asof`'s lazy fallback wrote it."""
     engine, cfg, trading = seed_engine
     # three CONSECUTIVE gap dates (no snapshot yet) → K = 3. iter-18: the snapshot cadence bounds the
     # DEEP region to monthly, so pick the K dates inside the config daily-density region (>= daily_start)
@@ -437,31 +572,34 @@ def test_kdate_backfill_loads_each_symbol_at_most_once(seed_engine, monkeypatch)
     # ensure the parallel path is actually exercised (workers > 1 over a >1-date range).
     assert cfg.data_manager.import_chunking.backfill_workers > 1
 
-    # instrument EVERY full-series bar-store load — both the eager `prefill` and the lazy `bars_asof`
-    # fallback push rows into `_by_symbol`, so a per-symbol DB query is exactly an entry appearing there.
+    # instrument the ACTUAL write to `_by_symbol` — race-free (see the docstring above) — rather than a
+    # racy check-then-call wrapper around the read side.
     load_counts: dict[str, int] = {}
     lock = __import__("threading").Lock()
-    orig_bars_asof = prices._BarCache.bars_asof
-    orig_prefill = prices._BarCache.prefill
 
     def _count(symbol):
         with lock:
             load_counts[symbol] = load_counts.get(symbol, 0) + 1
 
-    def _counting_bars_asof(self, session, symbol, d):
-        if symbol not in self._by_symbol:  # a real lazy bar-store load is about to happen
-            _count(symbol)
-        return orig_bars_asof(self, session, symbol, d)
+    class _CountingBySymbol(dict):
+        """A `_by_symbol` dict subclass that counts each key's FIRST write exactly once — the real load
+        event, whichever code path performs it. `__setitem__` is one dict-level operation (GIL-atomic),
+        so this cannot double-count even when several worker threads race to lazy-load the same symbol
+        (only the one thread inside `_load_lock`'s critical section ever assigns a genuinely new key)."""
 
-    def _counting_prefill(self, session, expected_symbols=None):
-        before = set(self._by_symbol)
-        orig_prefill(self, session, expected_symbols=expected_symbols)
-        for symbol in self._by_symbol:
-            if symbol not in before:  # newly loaded by this prefill (incl. a no-bar candidate as [])
-                _count(symbol)
+        def __setitem__(self, key, value):
+            is_new = key not in self
+            super().__setitem__(key, value)
+            if is_new:
+                _count(key)
+
+    orig_init = prices._BarCache.__init__
+
+    def _counting_init(self, *a, **kw):
+        orig_init(self, *a, **kw)
+        self._by_symbol = _CountingBySymbol()  # swap in the counting dict right after construction
 
-    monkeypatch.setattr(prices._BarCache, "bars_asof", _counting_bars_asof)
-    monkeypatch.setattr(prices._BarCache, "prefill", _counting_prefill)
+    monkeypatch.setattr(prices._BarCache, "__init__", _counting_init)
 
     job = create_job("backfill", r_start, r_end)
     summary = run_data_job(job.job_id, config=cfg, engine=engine)
diff --git a/incredible_auto_dev/.claude/agents/ui-test-designer.md b/incredible_auto_dev/.claude/agents/ui-test-designer.md
index 041ce3ea..2c188f00 100644
--- a/incredible_auto_dev/.claude/agents/ui-test-designer.md
+++ b/incredible_auto_dev/.claude/agents/ui-test-designer.md
@@ -24,8 +24,8 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 7. `.claude/skills/what-to-click-writer.md` — how to write the operator guide
 8. `docs/goal.md`'s "Must-have user journeys" section (or a token-lean goal-slice file, when the
    dispatch prompt points at one) — ONLY when the phase spec is backend-only AND names
-   required-still-passing journeys (see "Backend-only phase handling" below); read ONLY the named
-   journeys' own Steps/Acceptance text, not the whole file. Skip entirely otherwise.
+   required-still-passing and/or target journeys (see "Backend-only phase handling" below); read
+   ONLY the named journeys' own Steps/Acceptance text, not the whole file. Skip entirely otherwise.
 
 ## Process
 
@@ -84,26 +84,31 @@ Each step must have:
 If `Frontend Present: no` or if user-visible-changes report says N/A, `Frontend Present: no`
 suppresses NEW-surface UI test-case generation ONLY (Step 1's smoke/happy-path/validation/
 error/UX cases for a UI surface map row) — it never suppresses regression coverage for a
-required-still-passing journey (ops-hardening iter-40/41 lesson, binding: a required-still-passing
-journey shipping with ZERO evidence — this exact stub, applied blindly — was the root cause of a
-5-consecutive-ESCALATE session where every gate reported clean while journeys silently rotted
-unverified).
+required-still-passing journey OR the iteration's own target journeys (ops-hardening iter-40/41
+lesson, binding: a required-still-passing journey shipping with ZERO evidence — this exact stub,
+applied blindly — was the root cause of a 5-consecutive-ESCALATE session where every gate reported
+clean while journeys silently rotted unverified; iter-41's own audit found the SAME gap on the
+`Target journeys:` line — promoting a journey to a phase/iteration's own target silently REMOVED
+its verification, because this exact handling covered `Required-still-passing journeys:` only).
 
 1. Read the phase spec (`docs/phases/<phase>.md`) for a `**Required-still-passing journeys:**`
-   metadata line (goal mode only; a plain phase-mode spec, or a goal-mode spec with no such line
-   or whose line reads `none`, has nothing to regress here).
-2. If that line names one or more journey IDs (e.g. `J-01, J-03, J-04`): for EACH one, write
-   exactly one regression test case using **Test ID `UT-<journey-id>`** (e.g. `UT-J-01`, not the
-   sequential `UT-01` scheme) into the UI test plan, `Type: regression`, `Priority: P1`. Steps and
-   Expected Result come from that journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s
-   "Must-have user journeys" section (or the token-lean goal slice this phase's inputs point at,
-   when one is supplied) — read the journey's numbered steps and acceptance criteria and translate
-   them into the SAME exact-URL/exact-click/exact-expected format Step 2 above requires; do not
-   invent a generic "re-check journey X" placeholder. Do NOT emit a NEW-surface case for anything
-   else (there is no UI surface map row to derive one from on a backend-only phase).
-3. Still write the What-to-Click operator guide, scoped to the same required-still-passing
-   journeys (skip the "New capability" prioritization — there is none this phase).
-4. If that metadata line is absent, empty, or reads `none`: write the minimal N/A stubs below and
+   metadata line AND a `**Target journeys:**` metadata line (goal mode only; a plain phase-mode
+   spec, or a goal-mode spec where BOTH lines are absent, empty, or read `none`, has nothing to
+   regress here).
+2. For EACH journey ID named on EITHER line (e.g. `Required-still-passing journeys: J-01, J-03,
+   J-04` and `Target journeys: J-05, J-07` together name five journeys; a journey named on both
+   lines gets exactly one row — do not duplicate it): write exactly one regression test case using
+   **Test ID `UT-<journey-id>`** (e.g. `UT-J-01`, not the sequential `UT-01` scheme) into the UI
+   test plan, `Type: regression`, `Priority: P1`. Steps and Expected Result come from that
+   journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s "Must-have user journeys" section
+   (or the token-lean goal slice this phase's inputs point at, when one is supplied) — read the
+   journey's numbered steps and acceptance criteria and translate them into the SAME
+   exact-URL/exact-click/exact-expected format Step 2 above requires; do not invent a generic
+   "re-check journey X" placeholder. Do NOT emit a NEW-surface case for anything else (there is no
+   UI surface map row to derive one from on a backend-only phase).
+3. Still write the What-to-Click operator guide, scoped to the same required-still-passing +
+   target journeys (skip the "New capability" prioritization — there is none this phase).
+4. If BOTH metadata lines are absent, empty, or read `none`: write the minimal N/A stubs below and
    STOP — there is genuinely nothing to test.
 
 ```
diff --git a/incredible_auto_dev/agents/ui-test-designer/body.md b/incredible_auto_dev/agents/ui-test-designer/body.md
index ed96d4f3..0e7d2011 100644
--- a/incredible_auto_dev/agents/ui-test-designer/body.md
+++ b/incredible_auto_dev/agents/ui-test-designer/body.md
@@ -16,8 +16,8 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 7. `.claude/skills/what-to-click-writer.md` — how to write the operator guide
 8. `docs/goal.md`'s "Must-have user journeys" section (or a token-lean goal-slice file, when the
    dispatch prompt points at one) — ONLY when the phase spec is backend-only AND names
-   required-still-passing journeys (see "Backend-only phase handling" below); read ONLY the named
-   journeys' own Steps/Acceptance text, not the whole file. Skip entirely otherwise.
+   required-still-passing and/or target journeys (see "Backend-only phase handling" below); read
+   ONLY the named journeys' own Steps/Acceptance text, not the whole file. Skip entirely otherwise.
 
 ## Process
 
@@ -76,26 +76,31 @@ Each step must have:
 If `Frontend Present: no` or if user-visible-changes report says N/A, `Frontend Present: no`
 suppresses NEW-surface UI test-case generation ONLY (Step 1's smoke/happy-path/validation/
 error/UX cases for a UI surface map row) — it never suppresses regression coverage for a
-required-still-passing journey (ops-hardening iter-40/41 lesson, binding: a required-still-passing
-journey shipping with ZERO evidence — this exact stub, applied blindly — was the root cause of a
-5-consecutive-ESCALATE session where every gate reported clean while journeys silently rotted
-unverified).
+required-still-passing journey OR the iteration's own target journeys (ops-hardening iter-40/41
+lesson, binding: a required-still-passing journey shipping with ZERO evidence — this exact stub,
+applied blindly — was the root cause of a 5-consecutive-ESCALATE session where every gate reported
+clean while journeys silently rotted unverified; iter-41's own audit found the SAME gap on the
+`Target journeys:` line — promoting a journey to a phase/iteration's own target silently REMOVED
+its verification, because this exact handling covered `Required-still-passing journeys:` only).
 
 1. Read the phase spec (`docs/phases/<phase>.md`) for a `**Required-still-passing journeys:**`
-   metadata line (goal mode only; a plain phase-mode spec, or a goal-mode spec with no such line
-   or whose line reads `none`, has nothing to regress here).
-2. If that line names one or more journey IDs (e.g. `J-01, J-03, J-04`): for EACH one, write
-   exactly one regression test case using **Test ID `UT-<journey-id>`** (e.g. `UT-J-01`, not the
-   sequential `UT-01` scheme) into the UI test plan, `Type: regression`, `Priority: P1`. Steps and
-   Expected Result come from that journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s
-   "Must-have user journeys" section (or the token-lean goal slice this phase's inputs point at,
-   when one is supplied) — read the journey's numbered steps and acceptance criteria and translate
-   them into the SAME exact-URL/exact-click/exact-expected format Step 2 above requires; do not
-   invent a generic "re-check journey X" placeholder. Do NOT emit a NEW-surface case for anything
-   else (there is no UI surface map row to derive one from on a backend-only phase).
-3. Still write the What-to-Click operator guide, scoped to the same required-still-passing
-   journeys (skip the "New capability" prioritization — there is none this phase).
-4. If that metadata line is absent, empty, or reads `none`: write the minimal N/A stubs below and
+   metadata line AND a `**Target journeys:**` metadata line (goal mode only; a plain phase-mode
+   spec, or a goal-mode spec where BOTH lines are absent, empty, or read `none`, has nothing to
+   regress here).
+2. For EACH journey ID named on EITHER line (e.g. `Required-still-passing journeys: J-01, J-03,
+   J-04` and `Target journeys: J-05, J-07` together name five journeys; a journey named on both
+   lines gets exactly one row — do not duplicate it): write exactly one regression test case using
+   **Test ID `UT-<journey-id>`** (e.g. `UT-J-01`, not the sequential `UT-01` scheme) into the UI
+   test plan, `Type: regression`, `Priority: P1`. Steps and Expected Result come from that
+   journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s "Must-have user journeys" section
+   (or the token-lean goal slice this phase's inputs point at, when one is supplied) — read the
+   journey's numbered steps and acceptance criteria and translate them into the SAME
+   exact-URL/exact-click/exact-expected format Step 2 above requires; do not invent a generic
+   "re-check journey X" placeholder. Do NOT emit a NEW-surface case for anything else (there is no
+   UI surface map row to derive one from on a backend-only phase).
+3. Still write the What-to-Click operator guide, scoped to the same required-still-passing +
+   target journeys (skip the "New capability" prioritization — there is none this phase).
+4. If BOTH metadata lines are absent, empty, or read `none`: write the minimal N/A stubs below and
    STOP — there is genuinely nothing to test.
 
 ```
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index fbcfda4f..518f0553 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -279,6 +279,11 @@ if [[ "$PHASE" =~ ^goal-(.+)-iter-[0-9]+$ ]]; then
   # the post-merge writer below appends the DEFERRED-BUDGET rows. Targets are
   # excluded from deferral — they are dispatched regardless.
   _bqa_targets="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
+  # ops-hardening iter-42: mirror into the shared TARGET_JOURNEYS global name goal-iter-lean.sh
+  # already uses -- replay_lane_merge_results (lib/replay-lane.sh) reads this ONE name from both
+  # callers to thread `--target` into the merger, mirroring REQUIRED_JOURNEYS -> --required exactly.
+  # shellcheck disable=SC2034
+  TARGET_JOURNEYS="$_bqa_targets"
   REPLAY_DEFERRED_BUDGET="$(replay_lane_deferred_budget_set "$_bqa_targets")"
   if [[ -n "${REPLAY_DEFERRED_BUDGET// /}" ]]; then
     echo "[browser-qa] iter-budget trim (rung 2): deferring no-golden regression journey(s) this iteration: ${REPLAY_DEFERRED_BUDGET% }— targets + replay-FAIL re-confirms are never deferred."
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 99889ab8..98840b27 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -1282,6 +1282,26 @@ ensure_services_running() {
       2) export QA_FRONTEND_UP="slow" ;;   # alive, still compiling — gate re-probes
       *) export QA_FRONTEND_UP="no" ;;
     esac
+    # ops-hardening iter-42 (B4, TC-9): _start_service_with_retries' own budget (2×60s, or up to
+    # CHAIN_FRONTEND_HEAL_TIMEOUT on a corrupt-.next heal) can still return "slow"/"no" while the
+    # frontend genuinely is mid-recompile — iter-40's actual incident (frontend read 000 at one
+    # caller's 90s probe, then answered in 0s twenty minutes later from a DIFFERENT caller). The
+    # comment above already documents the intended design ("the downstream readiness gate
+    # re-probes"), but that only helps the callers that happen to add their OWN follow-up
+    # `_wait_for_frontend_ready` call (browser-qa-phase.sh, goal-iter-lean.sh, demo-phase.sh do; the
+    # REL-5 replay retry and the REL-14 preflight retry in lib/replay-lane.sh do not — they call only
+    # `ensure_services_running` after a mid-run restart and then immediately retry, which is exactly
+    # how a still-warm frontend gets misread as unreachable and the whole regression run goes
+    # silently all-SKIP on one premature timeout, iter-41 audit B4). Doing the bounded, corruption-
+    # aware re-probe HERE — inside `ensure_services_running` itself — closes the gap for every
+    # restart path uniformly, present and future, instead of hunting down each caller. Idempotent for
+    # callers that ALSO re-probe afterward: a frontend already answering 2xx/3xx here returns on the
+    # first curl, so their own subsequent call is a fast no-op, never a double wait.
+    if [[ "$QA_FRONTEND_UP" != "yes" ]] && declare -F _wait_for_frontend_ready >/dev/null 2>&1; then
+      if _wait_for_frontend_ready "$QA_FRONTEND_URL" "frontend" 90 "ensure-services"; then
+        export QA_FRONTEND_UP="yes"
+      fi
+    fi
   fi
 
   # ALWAYS 0: the five bare call sites run under `set -e`. Failure is surfaced
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index 49e78271..c489d598 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -198,7 +198,50 @@ def skipped_required_journeys(rows: "list[dict]", required_journeys: "list[str]
     return skipped
 
 
-def merge(texts: "list[str]", required_journeys: "list[str] | None" = None) -> str:
+def missing_target_journeys(rows: "list[dict]", target_journeys: "list[str] | None") -> "list[str]":
+    """Which of `target_journeys` (bare IDs like `J-05`) have ZERO executed test cases in `rows` —
+    the sibling of `missing_required_journeys` above, for the iteration spec's `Target journeys:`
+    line instead of `Required-still-passing journeys:`. ops-hardening iter-41 audit finding B2 /
+    iter-42 fix: promoting a journey to a phase/iteration's OWN target silently REMOVED its
+    verification, because every gate in the chain (this one included, before this function existed)
+    keyed off `Required-still-passing journeys:` only — an iteration whose stated purpose was
+    re-verifying J-05/J-07 could ship a merged clean headline with zero rows for either. Kept as a
+    separate function body (not a shared helper with `missing_required_journeys`) deliberately: this
+    is correctness-critical merge-gate code, and the two guards must be independently readable and
+    independently safe to touch without risking the other's already-hardened behavior."""
+    if not target_journeys:
+        return []
+    present_ids = {r["test_id"] for r in rows}
+    missing = []
+    for jid in target_journeys:
+        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
+        if tid not in present_ids:
+            missing.append(jid)
+    return missing
+
+
+def skipped_target_journeys(rows: "list[dict]", target_journeys: "list[str] | None") -> "list[str]":
+    """Which of `target_journeys` have a row whose ONLY recorded outcome is `SKIP` — the sibling of
+    `skipped_required_journeys` above, for `Target journeys:` (see `missing_target_journeys`'s
+    docstring for the full rationale). Only a literal `SKIP` counts (not `DEFERRED-BUDGET`), matching
+    `skipped_required_journeys`'s own contract exactly."""
+    if not target_journeys:
+        return []
+    by_id = {r["test_id"]: r for r in rows}
+    skipped = []
+    for jid in target_journeys:
+        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
+        row = by_id.get(tid)
+        if row is not None and row["verdict"] == "SKIP":
+            skipped.append(jid)
+    return skipped
+
+
+def merge(
+    texts: "list[str]",
+    required_journeys: "list[str] | None" = None,
+    target_journeys: "list[str] | None" = None,
+) -> str:
     """Merge in order; later inputs win per Test ID. Returns the merged markdown
     with a single authoritative headline verdict and detail rebuilt from the
     surviving rows (no verbatim per-lane embedding → exactly one verdict line).
@@ -222,7 +265,16 @@ def merge(texts: "list[str]", required_journeys: "list[str] | None" = None) -> s
     journeys, so it still merged to a clean `SKIPPED` headline under the first implementation of
     this guard (reproduced directly against the committed iter-40 artifact). Both shapes mean the
     same thing to a reader of the headline — "this journey was not verified this iteration" — so
-    both force `BLOCKED`."""
+    both force `BLOCKED`.
+
+    `target_journeys` (ops-hardening iter-42 — the sibling gap iter-41's own audit found, B2): the
+    iteration spec's `Target journeys:` list. `required_journeys` above guards journeys that must
+    STAY passing; `target_journeys` guards the journeys THIS iteration exists to verify — the exact
+    ones iter-41 itself shipped with zero rows while its merged headline read a clean `PASS 6/6`
+    (the binding iter-41 lesson: "promoting a journey to an iteration's target silently REMOVES its
+    verification"). Same additive semantics as `required_journeys`: a missing/all-SKIP target
+    journey forces `BLOCKED` on top of (never replacing) the required-journey guard, and a headline
+    already FAIL/BLOCKED is left alone."""
     by_id: "dict[str, dict]" = {}
     order: "list[str]" = []
     file_verdicts: "list[str]" = []
@@ -237,7 +289,9 @@ def merge(texts: "list[str]", required_journeys: "list[str] | None" = None) -> s
     overall = compute_overall(rows, file_verdicts)
     missing_required = missing_required_journeys(rows, required_journeys)
     skipped_required = skipped_required_journeys(rows, required_journeys)
-    if (missing_required or skipped_required) and overall in ("PASS", "SKIPPED"):
+    missing_target = missing_target_journeys(rows, target_journeys)
+    skipped_target = skipped_target_journeys(rows, target_journeys)
+    if (missing_required or skipped_required or missing_target or skipped_target) and overall in ("PASS", "SKIPPED"):
         overall = "BLOCKED"
     n_pass = sum(1 for r in rows if r["verdict"] == "PASS")
     n_skip = sum(1 for r in rows if r["verdict"] == "SKIP")
@@ -248,6 +302,8 @@ def merge(texts: "list[str]", required_journeys: "list[str] | None" = None) -> s
     overall_line += f", {n_blocked} blocked" if n_blocked else ""
     overall_line += f", {len(missing_required)} required-missing" if missing_required else ""
     overall_line += f", {len(skipped_required)} required-unverified" if skipped_required else ""
+    overall_line += f", {len(missing_target)} target-missing" if missing_target else ""
+    overall_line += f", {len(skipped_target)} target-unverified" if skipped_target else ""
     overall_line += ")"
     out = ["# UI Test Results (merged)", "",
            f"**Date:** {_today()}",
@@ -278,6 +334,21 @@ def merge(texts: "list[str]", required_journeys: "list[str] | None" = None) -> s
         for jid in skipped_required:
             out.append(f"- `UT-{jid}` — only a SKIP row for {jid}: named but never executed")
         out.append("")
+    if missing_target or skipped_target:
+        out += ["## Missing Target Journeys", "",
+                "_Target journeys named in the iteration spec's `Target journeys:` line — the "
+                "journeys THIS iteration exists to verify — that were NOT verified this iteration, "
+                "either no lane produced a row for them at all, or the only row they have reads "
+                "SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are "
+                "present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey "
+                "to an iteration's own target silently removed its verification — iter-41 itself "
+                "shipped a clean PASS 6/6 headline while its two target journeys had zero rows "
+                "anywhere)._", ""]
+        for jid in missing_target:
+            out.append(f"- `UT-{jid}` — no test case executed for {jid} by any lane")
+        for jid in skipped_target:
+            out.append(f"- `UT-{jid}` — only a SKIP row for {jid}: named but never executed")
+        out.append("")
     if failed:
         out += ["## Failed Tests", ""]
         for r in failed:
@@ -405,7 +476,11 @@ def main(argv: "list[str]") -> int:
     # journeys, so `merge` can detect any with ZERO executed test cases. Absent (the pre-iter-41
     # call shape every existing caller still uses until its bash wiring passes this) => no change
     # in behavior, matching every pre-existing test in this file's self-test suite.
+    # ops-hardening iter-42: a sibling `--target J-05,J-07,...` flag, same parsing shape, for the
+    # iteration spec's `Target journeys:` line (see `merge`'s docstring). Absent => no change in
+    # behavior, same as `--required`.
     required: list[str] = []
+    target: list[str] = []
     rest: list[str] = []
     i = 0
     while i < len(argv):
@@ -418,12 +493,21 @@ def main(argv: "list[str]") -> int:
             required = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
             i += 1
             continue
+        if a == "--target" and i + 1 < len(argv):
+            target = [j for j in argv[i + 1].replace(",", " ").split() if j]
+            i += 2
+            continue
+        if a.startswith("--target="):
+            target = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
+            i += 1
+            continue
         rest.append(a)
         i += 1
     argv = rest
     if len(argv) < 2:
         sys.stderr.write(
-            "usage: merge_ui_test_results.py [--required J-01,J-03,...] <out.md> <in1.md> [<in2.md> ...]\n"
+            "usage: merge_ui_test_results.py [--required J-01,J-03,...] [--target J-05,J-07,...] "
+            "<out.md> <in1.md> [<in2.md> ...]\n"
         )
         return 2
     out_path = Path(argv[0])
@@ -436,7 +520,7 @@ def main(argv: "list[str]") -> int:
         sys.stderr.write("[merge_ui_test_results] no readable input files\n")
         return 2
     out_path.parent.mkdir(parents=True, exist_ok=True)
-    out_path.write_text(merge(texts, required_journeys=required), encoding="utf-8")
+    out_path.write_text(merge(texts, required_journeys=required, target_journeys=target), encoding="utf-8")
     print(f"[merge_ui_test_results] merged {len(texts)} file(s) → {out_path}")
     return 0
 
@@ -759,6 +843,93 @@ def _self_test() -> int:
             assert file_top_verdict(merged) == "BLOCKED", file_top_verdict(merged)
             assert "UT-J-03" in merged
 
+    # ==============================================================================================
+    # ops-hardening iter-42 — a TARGET journey (the iteration's own `Target journeys:` line) with
+    # ZERO executed test cases must never merge into a clean PASS/SKIPPED headline either — the
+    # sibling gap iter-41's own audit caught: iter-41 shipped a clean PASS 6/6 headline while its
+    # two target journeys (J-05, J-07) had zero rows anywhere, because nothing in the chain keyed
+    # off `Target journeys:` at all.
+    # ==============================================================================================
+    def t_missing_target_journey_blocks_clean_pass():
+        md = merge([clean_pair], target_journeys=["J-01", "J-05"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Target Journeys" in md and "UT-J-05" in md
+        assert verdict_for(md, "UT-J-01") == "PASS", verdict_for(md, "UT-J-01")
+
+    def t_all_skip_target_journeys_block_clean_skipped():
+        all_skip = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-05 | Aggregates precomputed at ingest | regression | P1 | e | frontend down | SKIP | none |\n"
+            "| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | e | frontend down | SKIP | none |\n")
+        md = merge([all_skip], target_journeys=["J-05", "J-07"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Target Journeys" in md
+        assert "only a SKIP row for J-05" in md and "only a SKIP row for J-07" in md
+
+    def t_target_and_required_guards_both_apply_independently():
+        # A required journey is fully verified (PASS) but the iteration's OWN target journey has
+        # zero rows -- the target guard alone must still force BLOCKED, with its own section, even
+        # though the required-journey guard has nothing to report.
+        md = merge([clean_pair], required_journeys=["J-01"], target_journeys=["J-05"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Target Journeys" in md and "UT-J-05" in md
+        assert "## Missing Required Journeys" not in md  # nothing missing on the required side
+        # and the reverse: a satisfied target alongside a missing required journey.
+        target_pair = (
+            "**Browser QA Verdict:** PASS\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-05 | Aggregates precomputed | regression | P1 | e | ok | PASS | a.png |\n")
+        md2 = merge([target_pair], required_journeys=["J-01"], target_journeys=["J-05"])
+        assert file_top_verdict(md2) == "BLOCKED", file_top_verdict(md2)
+        assert "## Missing Required Journeys" in md2 and "UT-J-01" in md2
+        assert "## Missing Target Journeys" not in md2
+
+    def t_all_target_present_stays_clean():
+        md = merge([clean_pair], target_journeys=["J-01"])
+        assert file_top_verdict(md) == "PASS", file_top_verdict(md)
+        assert "## Missing Target Journeys" not in md
+
+    def t_no_target_journeys_arg_unchanged():
+        assert merge([clean_pair]) == merge([clean_pair], target_journeys=None)
+        assert merge([clean_pair], target_journeys=[]) == merge([clean_pair])
+        # and with a required_journeys arg present but no target_journeys arg at all, still
+        # byte-identical to the pre-iter-42 two-arg call shape.
+        assert merge([clean_pair], required_journeys=["J-01"]) == merge(
+            [clean_pair], required_journeys=["J-01"], target_journeys=None
+        )
+
+    def t_missing_target_never_downgrades_fail_or_blocked():
+        fail_pair = (
+            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-01 | Backfill honors range | regression | P1 | e | step 2 failed | FAIL | a.png |\n")
+        md = merge([fail_pair], target_journeys=["J-01", "J-05"])
+        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
+        assert "## Missing Target Journeys" in md and "UT-J-05" in md
+
+    def t_missing_target_via_cli_target_flag():
+        import tempfile
+        with tempfile.TemporaryDirectory() as td:
+            out = f"{td}/out.md"
+            in1 = f"{td}/in1.md"
+            Path(in1).write_text(clean_pair, encoding="utf-8")
+            rc = main(["--target", "J-01,J-05", out, in1])
+            assert rc == 0, rc
+            merged = Path(out).read_text(encoding="utf-8")
+            assert file_top_verdict(merged) == "BLOCKED", file_top_verdict(merged)
+            assert "UT-J-05" in merged
+            # --required and --target may both be given at once (a real iteration passes both).
+            out2 = f"{td}/out2.md"
+            rc2 = main(["--required", "J-01", "--target", "J-05", out2, in1])
+            assert rc2 == 0, rc2
+            merged2 = Path(out2).read_text(encoding="utf-8")
+            assert file_top_verdict(merged2) == "BLOCKED", file_top_verdict(merged2)
+            assert "## Missing Target Journeys" in merged2 and "## Missing Required Journeys" not in merged2
+
     # Self-counting list (local form) rather than a hardcoded total — upstream's void
     # tests and the local verdict-normalization tests both live here, so a literal
     # count goes stale on the next pull.
@@ -783,7 +954,14 @@ def _self_test() -> int:
               ("all_required_present_stays_clean", t_all_required_present_stays_clean),
               ("no_required_journeys_arg_unchanged", t_no_required_journeys_arg_unchanged),
               ("missing_required_never_downgrades_fail_or_blocked", t_missing_required_never_downgrades_fail_or_blocked),
-              ("missing_required_via_cli_required_flag", t_missing_required_via_cli_required_flag)]
+              ("missing_required_via_cli_required_flag", t_missing_required_via_cli_required_flag),
+              ("missing_target_journey_blocks_clean_pass", t_missing_target_journey_blocks_clean_pass),
+              ("all_skip_target_journeys_block_clean_skipped", t_all_skip_target_journeys_block_clean_skipped),
+              ("target_and_required_guards_both_apply_independently", t_target_and_required_guards_both_apply_independently),
+              ("all_target_present_stays_clean", t_all_target_present_stays_clean),
+              ("no_target_journeys_arg_unchanged", t_no_target_journeys_arg_unchanged),
+              ("missing_target_never_downgrades_fail_or_blocked", t_missing_target_never_downgrades_fail_or_blocked),
+              ("missing_target_via_cli_target_flag", t_missing_target_via_cli_target_flag)]
     for name, fn in checks:
         check(name, fn)
 
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index b055798e..bd707b98 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -46,7 +46,11 @@
 # Dataflow is via GLOBALS, deliberately: goal-iter-lean.sh's SPEED-2 fork
 # serializes exactly these names through its state file (_bqa_state_save), so
 # they are a cross-process contract, not a style choice.
-#   In:  REQUIRED_JOURNEYS, FRONTEND_AVAILABLE, FRONTEND_URL, REPO_ROOT,
+#   In:  REQUIRED_JOURNEYS, TARGET_JOURNEYS (ops-hardening iter-42 — the
+#        iteration's own Target journeys:, read by replay_lane_merge_results
+#        exactly like REQUIRED_JOURNEYS; set BEFORE the SPEED-2 fork point in
+#        both callers so it needs no state-file serialization of its own),
+#        FRONTEND_AVAILABLE, FRONTEND_URL, REPO_ROOT,
 #        CHAIN_REGRESSION_REPLAY (knob, default true),
 #        REPLAY_LANE_CANARY_CAPABLE (SPEED-22; set only by goal-iter-lean.sh)
 #   Set by replay_lane_paths: EVIDENCE_DIR, SID, JOURNEY_SCRIPTS_DIR,
@@ -459,7 +463,17 @@ replay_lane_merge_results() {
   # merge()'s new check is then a no-op, unchanged behavior.
   local _rl_required_args=()
   [[ -n "${REQUIRED_JOURNEYS:-}" && -n "${REQUIRED_JOURNEYS// /}" ]] && _rl_required_args=(--required "$REQUIRED_JOURNEYS")
-  if ! python3 "$MERGE_RESULTS" "${_rl_required_args[@]}" "$_rl_out" "$REGRESSION_RESULTS" ${_rl_mid[@]+"${_rl_mid[@]}"} "$_rl_llm"; then
+  # ops-hardening iter-42: the sibling wiring for this iteration's OWN `Target journeys:` (iter-41
+  # audit finding B2 — promoting a journey to a target silently removed its verification, because
+  # nothing downstream of the spec-parse ever read TARGET_JOURNEYS). goal-iter-lean.sh already
+  # computes a global TARGET_JOURNEYS before its SPEED-2 fork point (used for its own dispatch
+  # prompt); browser-qa-phase.sh mirrors its local `_bqa_targets` into the SAME global name right
+  # after computing it, so this ONE shared merge function reads one consistent name from both
+  # callers, exactly mirroring the REQUIRED_JOURNEYS convention above. Empty/unset (plain phase
+  # mode, or a spec with no Target journeys line) is a no-op, byte-identical to before this change.
+  local _rl_target_args=()
+  [[ -n "${TARGET_JOURNEYS:-}" && -n "${TARGET_JOURNEYS// /}" ]] && _rl_target_args=(--target "$TARGET_JOURNEYS")
+  if ! python3 "$MERGE_RESULTS" "${_rl_required_args[@]}" "${_rl_target_args[@]}" "$_rl_out" "$REGRESSION_RESULTS" ${_rl_mid[@]+"${_rl_mid[@]}"} "$_rl_llm"; then
     _replay_lane_warn "results merge failed — falling back to a lane output."
     if [[ -f "$_rl_llm" ]]; then cp "$_rl_llm" "$_rl_out" 2>/dev/null || true
     elif [[ -f "$REGRESSION_RESULTS" ]]; then cp "$REGRESSION_RESULTS" "$_rl_out" 2>/dev/null || true; fi
diff --git a/incredible_auto_dev/tests/automation/test-replay-lane.sh b/incredible_auto_dev/tests/automation/test-replay-lane.sh
index ddccf7a8..b8b8f49b 100644
--- a/incredible_auto_dev/tests/automation/test-replay-lane.sh
+++ b/incredible_auto_dev/tests/automation/test-replay-lane.sh
@@ -34,6 +34,9 @@
 #  10. Merge: replay FAIL overturned by LLM PASS → merged PASS + dated
 #      reconciliation footer appended to the RAW replay artifact (companion 1:
 #      no stale FAIL survives the iteration); un-overturned FAIL → no footer.
+#      10b (ops-hardening iter-42): TARGET_JOURNEYS threads into --target the
+#      same way REQUIRED_JOURNEYS threads into --required — a missing target
+#      journey forces BLOCKED; unset TARGET_JOURNEYS stays byte-identical.
 #  11. Merge crash → lane-file cp fallback (LLM file preferred).
 #  12. REL-5 flake discipline: infra-then-success → the retry rescues the lane
 #      (normal PASS path, no SKIPPED-INFRA); infra-then-FAIL → the retry's rc=5
@@ -463,6 +466,64 @@ grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md"
   && assert "merge: no footer when nothing was overturned" fail \
   || assert "merge: no footer when nothing was overturned" pass
 
+# ── 10b. Merge: TARGET_JOURNEYS threads into --target (ops-hardening iter-42) ─
+# A target journey (this iteration's OWN Target journeys: line) with zero rows
+# forces the merged headline to BLOCKED, exactly like REQUIRED_JOURNEYS does
+# for a required-still-passing journey (section 10) -- proves TARGET_JOURNEYS
+# genuinely reaches merge_ui_test_results.py's --target flag through
+# replay_lane_merge_results (the bash wiring), not just that merge()'s own
+# Python self-test covers the guard in isolation.
+reset_goldens
+REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
+LLM="$SBX/reports/phase-$ITER-ui-test-results.llm.md"
+MERGED="$SBX/reports/phase-$ITER-ui-test-results.md"
+rm -f "$MERGED"
+cat > "$REG" <<'EOF'
+**Browser QA Verdict:** PASS
+
+## Results Table
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---|---|---|---|---|---|---|---|
+| UT-J-06 | view dashboard | regression | P1 | e | ok | PASS | none |
+EOF
+cat > "$LLM" <<'EOF'
+**Browser QA Verdict:** PASS
+
+## Results Table
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---|---|---|---|---|---|---|---|
+EOF
+(
+  set -euo pipefail
+  source "$LIB"
+  REPO_ROOT="$SBX"
+  replay_lane_paths "$ITER"
+  _use_replay=yes
+  TARGET_JOURNEYS="J-05 "   # this iteration's own target -- has ZERO rows in either lane above
+  replay_lane_merge_results "$MERGED" "$LLM"
+)
+grep -q '^\*\*Browser QA Verdict:\*\* BLOCKED' "$MERGED" \
+  && assert "merge: TARGET_JOURNEYS threads into --target -- missing target forces BLOCKED" pass \
+  || assert "merge: TARGET_JOURNEYS threads into --target -- missing target forces BLOCKED" fail
+grep -q '## Missing Target Journeys' "$MERGED" && grep -q 'UT-J-05' "$MERGED" \
+  && assert "merge: Missing Target Journeys section names J-05" pass \
+  || assert "merge: Missing Target Journeys section names J-05" fail
+
+# TARGET_JOURNEYS unset (plain phase mode / no Target journeys line) → unchanged clean PASS, so
+# every caller stays byte-identical until its own bash wiring sets TARGET_JOURNEYS.
+rm -f "$MERGED"
+(
+  set -euo pipefail
+  source "$LIB"
+  REPO_ROOT="$SBX"
+  replay_lane_paths "$ITER"
+  _use_replay=yes
+  replay_lane_merge_results "$MERGED" "$LLM"
+)
+grep -q '^\*\*Browser QA Verdict:\*\* PASS' "$MERGED" \
+  && assert "merge: TARGET_JOURNEYS unset -> unchanged clean PASS" pass \
+  || assert "merge: TARGET_JOURNEYS unset -> unchanged clean PASS" fail
+
 # ── 11. Merge crash → lane-file fallback ─────────────────────────────────────
 reset_goldens
 REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 147 ++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |   9 ++
 runs/goal-session-ops-hardening/trace/.next-step  |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |   2 +
 4 files changed, 159 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
