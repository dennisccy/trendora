# Iteration diff (bounded)

Files changed: 99. Shown in full: 44.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `reports/goal-session-mcp-loop-index.html` (60 diff lines)
- `reports/perf-budgets.md` (94 diff lines)
- `reports/phase-goal-mcp-loop-iter-25-iteration-summary.md` (92 diff lines)
- `reports/phase-goal-mcp-loop-iter-25-summary.html` (42 diff lines)
- `runs/goal-session-mcp-loop/engine.pid` (7 diff lines)
- `runs/goal-session-mcp-loop/iter-26/.steps/decomposer.done` (7 diff lines)
- `runs/goal-session-mcp-loop/iter-26/goal-slice.md` (682 diff lines)
- `runs/goal-session-mcp-loop/iter-26/snapshot-sha` (8 diff lines)
- `runs/goal-session-mcp-loop/session.json` (17 diff lines)
- `runs/goal-session-mcp-loop/state/blueprint.md` (13 diff lines)
- `runs/goal-session-mcp-loop/state/project-story.md` (29 diff lines)
- `runs/goal-session-mcp-loop/summary.md` (92 diff lines)
- `runs/goal-session-mcp-loop/telemetry.jsonl` (29 diff lines)
- `runs/goal-session-mcp-loop/trace/.next-step` (7 diff lines)
- `runs/goal-session-mcp-loop/trace/trace.jsonl` (27 diff lines)
- `diff --git areports/demo/goal-mcp-loop-iter-26/step-01.png breports/demo/goal-mcp-loop-iter-26/step-01.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-26-evidence/UT-01-result.png breports/qa/goal-mcp-loop-iter-26-evidence/UT-01-result.png` (4 diff lines)
- `diff --git areports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.png breports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.png` (4 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/docs/improvement-roadmap.archive.md` (321 lines not shown)
- `incredible_auto_dev/docs/improvement-roadmap.md` (886 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/goal_lint.py` (142 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/lint_contracts.py` (52 lines not shown)
- `incredible_auto_dev/scripts/automation/run-goal.sh` (407 lines not shown)
- `incredible_auto_dev/skills/goal-authoring.md` (116 lines not shown)
- `incredible_auto_dev/skills/goal-evaluation-methodology.md` (17 lines not shown)
- `incredible_auto_dev/templates/iteration-summary.md` (20 lines not shown)
- `incredible_auto_dev/templates/proposer-guidance.md` (138 lines not shown)
- `incredible_auto_dev/tests/automation/test-doc-drift.sh` (254 lines not shown)
- `incredible_auto_dev/tests/automation/test-intent-checkpoint.sh` (241 lines not shown)
- `diff --git aapps/backend/tests/test_scoring_window.py bapps/backend/tests/test_scoring_window.py` (138 lines not shown)
- `diff --git adocs/handoffs/goal-mcp-loop-iter-26-audit.md bdocs/handoffs/goal-mcp-loop-iter-26-audit.md` (214 lines not shown)
- `diff --git adocs/handoffs/goal-mcp-loop-iter-26-dev.md bdocs/handoffs/goal-mcp-loop-iter-26-dev.md` (266 lines not shown)
- `diff --git adocs/phases/goal-mcp-loop-iter-26.md bdocs/phases/goal-mcp-loop-iter-26.md` (109 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-demo-results.md breports/phase-goal-mcp-loop-iter-26-demo-results.md` (28 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-demo-script.md breports/phase-goal-mcp-loop-iter-26-demo-script.md` (21 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-demo.json breports/phase-goal-mcp-loop-iter-26-demo.json` (27 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-implementation-summary.md breports/phase-goal-mcp-loop-iter-26-implementation-summary.md` (99 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-iteration-summary.md breports/phase-goal-mcp-loop-iter-26-iteration-summary.md` (81 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-summary.html breports/phase-goal-mcp-loop-iter-26-summary.html` (369 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-ui-surface-map.md breports/phase-goal-mcp-loop-iter-26-ui-surface-map.md` (70 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-ui-test-plan.md breports/phase-goal-mcp-loop-iter-26-ui-test-plan.md` (438 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-ui-test-results.md breports/phase-goal-mcp-loop-iter-26-ui-test-results.md` (267 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-user-visible-changes.md breports/phase-goal-mcp-loop-iter-26-user-visible-changes.md` (67 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-ux-regression.md breports/phase-goal-mcp-loop-iter-26-ux-regression.md` (86 lines not shown)
- `diff --git areports/phase-goal-mcp-loop-iter-26-what-to-click.md breports/phase-goal-mcp-loop-iter-26-what-to-click.md` (95 lines not shown)
- `diff --git areports/qa/goal-mcp-loop-iter-26-evidence/UT-02-backend-log-tail.txt breports/qa/goal-mcp-loop-iter-26-evidence/UT-02-backend-log-tail.txt` (206 lines not shown)
- `diff --git areports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.md breports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.md` (26 lines not shown)
- `diff --git areports/qa/goal-mcp-loop-iter-26-qa.md breports/qa/goal-mcp-loop-iter-26-qa.md` (259 lines not shown)
- `diff --git areports/qa/goal-mcp-loop-iter-26-test-plan.md breports/qa/goal-mcp-loop-iter-26-test-plan.md` (474 lines not shown)
- `diff --git areports/reviews/goal-mcp-loop-iter-26-review.md breports/reviews/goal-mcp-loop-iter-26-review.md` (46 lines not shown)
- `diff --git aruns/goal-mcp-loop-iter-26/plan.md bruns/goal-mcp-loop-iter-26/plan.md` (214 lines not shown)
- `diff --git aruns/goal-mcp-loop-iter-26/status.json bruns/goal-mcp-loop-iter-26/status.json` (78 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-26/.steps/coherence.done bruns/goal-session-mcp-loop/iter-26/.steps/coherence.done` (7 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-26/coherence.md bruns/goal-session-mcp-loop/iter-26/coherence.md` (77 lines not shown)
- `diff --git aruns/goal-session-mcp-loop/iter-26/journey-history.pre.json bruns/goal-session-mcp-loop/iter-26/journey-history.pre.json` (180 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 663545a..1316d07 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -280,6 +280,11 @@ class IndicatorsCfg(BaseModel):
     semivol_window: int
     vol_contraction_recent: int
     vol_contraction_prior: int
+    # iter-26 (J-16, fast-platform item F): the bounded trailing-window `scoring.py` slices each
+    # member's as-of bar series to (bars[-N:]) BEFORE indicator/pattern computation, so a 30-year
+    # bars_asof series is never fed whole into a ~252-bar-max indicator. Validated below to be >= every
+    # individually-configured window on THIS model; the byte-identity harness is the real authority.
+    max_lookback_bars: int
 
     @model_validator(mode="after")
     def _validate(self) -> "IndicatorsCfg":
@@ -301,10 +306,30 @@ class IndicatorsCfg(BaseModel):
             "semivol_window": self.semivol_window,
             "vol_contraction_recent": self.vol_contraction_recent,
             "vol_contraction_prior": self.vol_contraction_prior,
+            "max_lookback_bars": self.max_lookback_bars,
         }
         nonpositive = sorted(k for k, v in scalars.items() if v <= 0)
         if nonpositive:
             raise ValueError(f"indicators values must be positive: {nonpositive}")
+        # iter-26 sanity guard (not the correctness authority — the byte-identity harness is): the
+        # window must cover every consumer fed by a bars_asof-sliced series on THIS model (a
+        # different model's pattern min_history_bars is cross-checked on Config below, mirroring
+        # `_pattern_ma_period_is_an_indicator_period`'s "a sub-model cannot see indicators" note).
+        max_needed = max(
+            max(self.ma_periods),
+            max(self.rs_windows.values()) + 1,  # rs_vs needs window + 1 bars
+            self.high_window_52w,
+            2 * self.vol_avg_period,  # vol_trend needs 2 * period bars
+            self.atr_period + 1,
+            self.hv_window + 1,
+            self.semivol_window + 1,
+            self.vol_contraction_recent + self.vol_contraction_prior + 1,
+        )
+        if self.max_lookback_bars < max_needed:
+            raise ValueError(
+                f"indicators.max_lookback_bars ({self.max_lookback_bars}) must be >= the largest "
+                f"configured indicator window ({max_needed})"
+            )
         return self
 
 
@@ -2228,6 +2253,26 @@ class Config(BaseModel):
             )
         return self
 
+    @model_validator(mode="after")
+    def _max_lookback_bars_covers_pattern_history(self) -> "Config":
+        """iter-26 (J-16, fast-platform item F) sanity guard: `indicators.max_lookback_bars` — the
+        window `scoring.py` slices every as-of bar series to before indicator/pattern computation —
+        must be >= every pattern detector's own `min_history_bars`, so a detector's short-history NA
+        gate is never tripped early by an over-narrow window. Cross-checked here (not on `PatternsCfg`)
+        because a sub-model cannot see `indicators` — same reason as `_pattern_ma_period_is_an_indicator_period`
+        above. This is a sanity guard, not the correctness authority: the byte-identity harness is."""
+        needed = max(
+            self.patterns.vcp.min_history_bars,
+            self.patterns.pullback_to_rising_dma.min_history_bars,
+            self.patterns.flat_base_breakout.min_history_bars,
+        )
+        if self.indicators.max_lookback_bars < needed:
+            raise ValueError(
+                f"indicators.max_lookback_bars ({self.indicators.max_lookback_bars}) must be >= the "
+                f"largest pattern min_history_bars ({needed})"
+            )
+        return self
+
     @model_validator(mode="after")
     def _factor_lab_sources_resolve(self) -> "Config":
         """Every Factor-Lab factor `source` must resolve to a stored value at boot (anti-goal: No magic
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index 7282e39..7814045 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -190,6 +190,55 @@ class _BarCache:
         cut = bisect.bisect_right(self._dates_by_symbol[symbol], d)
         return full[:cut]
 
+    def bars_after(
+        self, session: Session, symbol: str, d: date_cls, limit: Optional[int] = None
+    ) -> list[Bar]:
+        """iter-26 (J-16, item F): the cached mirror of the module-level `bars_after` — all bars for
+        `symbol` with date > `d`, ascending, optionally truncated to the first `limit` bars. Slices with
+        the SAME `bisect.bisect_right` boundary `bars_asof` uses for its `<= d` side, so the two never
+        overlap (no-lookahead preserved). Byte-identical to the uncached query truncated to `limit` (same
+        rows, same order).
+
+        iter-26 memory fix: the load-ensuring step no longer goes through `bars_asof`, which BUILT and
+        immediately DISCARDED the whole `full[:cut]` (`<= d`) prefix on every call — up to ~5,300 `Bar`
+        tuples of transient allocation per (run, symbol) in the forward-return backfill. It uses the same
+        lightweight lazy-load `trailing_count` uses (a no-op on a prefilled cache — the crashing
+        `_do_backfill` shape never re-loads). And when `limit` is given it slices only the first `limit`
+        post-cut bars (`full[cut:cut+limit]`) rather than materializing the full multi-year post-`d` tail
+        just to truncate it — the exact "avoid the full tail" intent the module-level docstring states.
+        For every value the backfill passes (`limit` = `max(horizons)` > 0, or `None`) this is
+        byte-identical to the old `full[cut:][:limit]` and to the raw `.limit(limit)` query."""
+        dates = self._dates_by_symbol.get(symbol)
+        if dates is None:
+            # ensure the series is loaded exactly once (lazy/defensive — a prefilled cache never reaches
+            # here); the returned slice is discarded, mirroring `trailing_count`'s load-ensure idiom.
+            self.bars_asof(session, symbol, d)
+            dates = self._dates_by_symbol[symbol]
+        full = self._by_symbol[symbol]
+        cut = bisect.bisect_right(dates, d)
+        if limit is None:
+            return full[cut:]
+        return full[cut : cut + limit]
+
+    def close_on(self, session: Session, symbol: str, d: date_cls) -> Optional[float]:
+        """iter-26 memory fix (J-16): the close of the latest cached bar with date <= `d` (or None when
+        the symbol has no bar on/before `d`), read by a single `bisect` + index.
+
+        This replaces the old cache path (`bars_asof(...)[-1].close`), which materialized the whole
+        `full[:cut]` (`<= d`) prefix — up to ~5,300 `Bar` tuples on a late as-of date — ONLY to read its
+        last element and throw the rest away, once per (run, symbol) in the forward-return backfill (a
+        large per-date transient that grows VSZ under arena fragmentation). Byte-identical: the latest bar
+        with date <= d is `full[cut-1]` where `cut = bisect_right(dates, d)`; `cut == 0` (no bar on/before
+        d) -> None, exactly as the empty-slice/`session.scalar(... LIMIT 1)` paths return. Load-ensures
+        via the same lightweight lazy-load `trailing_count` uses (a no-op on a prefilled cache)."""
+        dates = self._dates_by_symbol.get(symbol)
+        if dates is None:
+            # ensure the series is loaded exactly once (lazy/defensive); the slice is discarded.
+            self.bars_asof(session, symbol, d)
+            dates = self._dates_by_symbol[symbol]
+        cut = bisect.bisect_right(dates, d)
+        return self._by_symbol[symbol][cut - 1].close if cut > 0 else None
+
     def trailing_count(self, session: Session, symbol: str, d: date_cls) -> int:
         """The number of bars for `symbol` with date <= `d` — BYTE-IDENTICAL to
         `len(self.bars_asof(session, symbol, d))` and to a `SELECT count(*) ... WHERE date <= d` grouped
@@ -330,7 +379,17 @@ def close_on(session: Session, symbol: str, d: date_cls) -> Optional[float]:
     symbol has no bar on/before D. This is the single-bar form of `bars_asof(session, symbol, d)[-1]
     .close` — the SAME backward boundary (date <= d, no lookahead) — but it fetches only the one bar
     instead of materializing the symbol's full pre-history, so the walk-forward backfill can read each
-    forward return's entry close cheaply."""
+    forward return's entry close cheaply.
+
+    iter-26 (J-16, item F): when a `bar_cache(session)` context is active, this derives the answer from
+    the once-loaded cached series (no DB round-trip) instead of issuing the raw single-row query —
+    byte-identical (same `<= d` boundary), matching the `bars_asof` cache-aware pattern above. The
+    cache path reads the single as-of close by `bisect` + index (`_BarCache.close_on`) rather than
+    materializing the whole `<= d` prefix (iter-26 memory fix). The default (no-context) path is
+    unchanged."""
+    cache = _BAR_CACHES.get(id(session))
+    if cache is not None:
+        return cache.close_on(session, symbol, d)
     stmt = (
         select(DailyPrice.close)
         .where(DailyPrice.symbol == symbol)
@@ -343,7 +402,7 @@ def close_on(session: Session, symbol: str, d: date_cls) -> Optional[float]:
 
 def bars_after(
     session: Session, symbol: str, d: date_cls, limit: Optional[int] = None
-) -> list[DailyPrice]:
+) -> list[DailyPrice] | list[Bar]:
     """All bars for `symbol` with **date > `d`**, ascending — the strict inverse of `bars_asof`
     and the forward no-lookahead boundary used by the walk-forward forward-testing engine.
 
@@ -352,7 +411,15 @@ def bars_after(
     `limit=max(horizons)` to avoid materializing the full multi-year tail per (symbol, run); the
     result is byte-identical to the unbounded call truncated to `limit` (the boundary is unchanged,
     only later, irrelevant bars are not fetched). The no-lookahead boundary test calls it WITHOUT a
-    limit and asserts no returned bar has date <= d."""
+    limit and asserts no returned bar has date <= d.
+
+    iter-26 (J-16, item F): when a `bar_cache(session)` context is active, this slices the once-loaded
+    cached series (`_BarCache.bars_after`) instead of issuing the raw query — byte-identical (same
+    `> d` boundary, same `limit` truncation), matching `bars_asof`'s cache-aware pattern. The default
+    (no-context) path is unchanged."""
+    cache = _BAR_CACHES.get(id(session))
+    if cache is not None:
+        return cache.bars_after(session, symbol, d, limit=limit)
     stmt = (
         select(DailyPrice)
         .where(DailyPrice.symbol == symbol)
diff --git a/apps/backend/app/engine/scoring.py b/apps/backend/app/engine/scoring.py
index 81dd908..fb6c010 100644
--- a/apps/backend/app/engine/scoring.py
+++ b/apps/backend/app/engine/scoring.py
@@ -111,6 +111,14 @@ def _raw_components(
     window_3m = icfg.rs_windows["3m"]
 
     bars = bars_asof(session, ticker, asof)
+    # iter-26 (J-16, fast-platform item F): a 30-year bars_asof series can carry ~5,300 bars on a
+    # late as-of date, but every component below reads only a TRAILING window off the end (the
+    # largest is `high_window_52w`, 252). Slicing to the last `max_lookback_bars` bars BEFORE any
+    # indicator runs is byte-identical (every consumer already computes from the series' end — see
+    # `test_scoring_window.py`) and avoids feeding thousands of irrelevant older bars through them. A
+    # member with fewer than max_lookback_bars bars keeps its whole (shorter) series — short-history
+    # NA propagation is unaffected.
+    bars = bars[-icfg.max_lookback_bars:]
     series = closes(bars)
     vols = volumes(bars)
     hi, lo = highs(bars), lows(bars)
@@ -337,6 +345,10 @@ def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = No
         # as-of bars read ONCE (date <= asof, no lookahead), reused for BOTH the invalidation level
         # and the VCP detector — no extra DB round-trip.
         bars = bars_asof(session, ticker, asof)
+        # iter-26 (J-16, item F): same bounded trailing-window slice as `_raw_components` above — every
+        # pattern detector below reads only a trailing window (the largest min_history_bars is 90),
+        # well within max_lookback_bars — byte-identical, see `test_scoring_window.py`.
+        bars = bars[-icfg.max_lookback_bars:]
         inv_closes = closes(bars)
         # invalidation level: the canonical `sma` over the config invalidation period (the level ==
         # the chart's MA-series endpoint).
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index eb2cec3..d9d8189 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -150,10 +150,19 @@ def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -
                     # tick the message on each batch boundary (and the final date) so progress is live
                     if index % batch_size == 0 or index == len(dates):
                         prog.message = f"history {prog.dates_done}/{prog.dates_total}"
-        # the realized forward returns over every persisted cadence snapshot (idempotent INSERT-only,
-        # concurrency-safe) — the SAME engine the synchronous boot ran, only rescheduled.
-        result = backfill_forward_returns(engine, cfg)
-        prog.forward_returns_inserted = result["rows_inserted"]
+                # iter-26 (J-16, item F): the realized forward returns over every persisted cadence
+                # snapshot (idempotent INSERT-only, concurrency-safe) — the SAME engine the synchronous
+                # boot ran, only rescheduled. Moved INSIDE this `with bar_cache(session):` block AND
+                # passed `session` (not `engine`): `backfill_forward_returns` branches on
+                # `isinstance(session_or_engine, Session)` — passed the engine, it used to open a BRAND
+                # NEW session with a different id(), which the cache registry (keyed by id(session))
+                # never finds, so every close_on/bars_after call re-queried the DB per (run, symbol)
+                # regardless of the cache above. Passing this SAME session reuses the exact cache already
+                # active, so its close_on/bars_after calls (now cache-aware — see prices.py) read the
+                # already-loaded series instead of round-tripping the DB. Output is byte-identical either
+                # way (same rows/values; only the load path changes).
+                result = backfill_forward_returns(session, cfg)
+                prog.forward_returns_inserted = result["rows_inserted"]
         # iter-36 (J-96): precompute the dynamic-universe membership-timeline cache OFF the boot path so
         # the FIRST `GET /api/data` after a boot/rebuild serves the cached payload rather than paying the
         # O(dates × pool) `resolve_with_reasons` derivation synchronously (the iter-35 regression). This is
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 89f6000..49cfffd 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -73,6 +73,9 @@ MINIMAL_VALID = {
         "semivol_window": 63,
         "vol_contraction_recent": 21,
         "vol_contraction_prior": 63,
+        # iter-26 (J-16 item F): required window; mirrors config.yaml's real value (>= high_window_52w
+        # 252 + margin; >= the patterns block's largest min_history_bars, 90).
+        "max_lookback_bars": 320,
     },
     "sectors": {
         "weights": {
diff --git a/apps/backend/tests/test_config_engine.py b/apps/backend/tests/test_config_engine.py
index 35d17a7..56c97da 100644
--- a/apps/backend/tests/test_config_engine.py
+++ b/apps/backend/tests/test_config_engine.py
@@ -69,6 +69,9 @@ VALID = {
         "semivol_window": 63,
         "vol_contraction_recent": 21,
         "vol_contraction_prior": 63,
+        # iter-26 (J-16 item F): required window; mirrors config.yaml's real value (>= high_window_52w
+        # 252 + margin; >= the patterns block's largest min_history_bars, 90).
+        "max_lookback_bars": 320,
     },
     "sectors": {
         "weights": {
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index a47da00..3ed70d9 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -16,7 +16,7 @@ real engines on the committed seed under a REDUCED walk-forward cadence (module-
 from __future__ import annotations
 
 import json
-from datetime import date, datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 from statistics import stdev
 
 import pytest
@@ -33,7 +33,7 @@ from app.engine.forward_testing import (
     max_drawdown,
     walk_forward_asof_dates,
 )
-from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
+from app.engine.prices import bar_cache, bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.models import (
     DailyPrice,
@@ -126,6 +126,78 @@ def test_close_on_is_the_asof_close(tiny_price_engine):
         assert close_on(session, "MISSING", days[0]) is None
 
 
+# ==================================================================================================
+# iter-26 (J-16, fast-platform item F) — close_on / bars_after cache-awareness
+#
+# `close_on`/`bars_after` are now cache-aware: inside an active `bar_cache(session)` context they
+# derive their answer from the once-loaded cached series instead of issuing a raw query. Proves the
+# cache-aware path is BYTE-IDENTICAL to the default (no-context) path, for both a long-history and a
+# short-history symbol. ADDITIVE — the tests above (`test_close_on_is_the_asof_close`,
+# `test_bars_after_returns_only_future_bars_ascending`, `test_bars_after_limit_is_the_unbounded_prefix`)
+# are unedited; a new fixture keeps this proof independent of `tiny_price_engine`.
+# ==================================================================================================
+@pytest.fixture()
+def two_symbol_price_engine(tmp_path):
+    """"AAA": short history (5 bars, same shape/gap as `tiny_price_engine`) and "BBB": long history (30
+    consecutive daily bars, no gap) — sharing no dates, so each symbol's cache load is independent."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'two_symbol.db'}")
+    create_db_and_tables(engine)
+    short_days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]  # a gap at the 6th/7th (weekend-like)
+    long_days = [date(2024, 2, 1) + timedelta(days=i) for i in range(30)]  # consecutive, no gap
+    with Session(engine) as session:
+        for i, d in enumerate(short_days):
+            c = float(10 + i)
+            session.add(DailyPrice(symbol="AAA", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=100.0 + i))
+        for i, d in enumerate(long_days):
+            c = float(100 + i)
+            session.add(DailyPrice(symbol="BBB", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=1000.0 + i))
+        session.commit()
+    return engine, short_days, long_days
+
+
+def test_close_on_cache_aware_matches_uncached(two_symbol_price_engine):
+    """close_on's cache-aware path (an active bar_cache) is byte-identical to the default uncached
+    query, for a long-history symbol ("BBB") and a short-history symbol ("AAA"), each probed at an
+    in-range date, a gap/non-trading date, and a before-all-data date."""
+    engine, short_days, long_days = two_symbol_price_engine
+    probes = {
+        "AAA": [short_days[2], date(2024, 1, 7), date(2023, 12, 31)],
+        "BBB": [long_days[10], long_days[-1], date(2024, 1, 31)],
+    }
+    with Session(engine) as plain:
+        uncached = {(sym, d): close_on(plain, sym, d) for sym, ds in probes.items() for d in ds}
+    with Session(engine) as cached_session, bar_cache(cached_session):
+        cached = {(sym, d): close_on(cached_session, sym, d) for sym, ds in probes.items() for d in ds}
+    assert cached == uncached
+    assert cached[("AAA", short_days[2])] == 12.0  # the bar ON 2024-01-04
+    assert cached[("BBB", long_days[10])] == 110.0  # the bar 10 days into BBB's series
+
+
+def test_bars_after_cache_aware_matches_uncached(two_symbol_price_engine):
+    """bars_after's cache-aware path is byte-identical to the default uncached query — unlimited AND
+    with a limit — for both a long-history and a short-history symbol."""
+    engine, short_days, long_days = two_symbol_price_engine
+    cuts = {"AAA": short_days[0], "BBB": long_days[5]}
+    with Session(engine) as plain:
+        uncached_full = {s: [(b.date, b.close) for b in bars_after(plain, s, d)] for s, d in cuts.items()}
+        uncached_limited = {
+            s: [(b.date, b.close) for b in bars_after(plain, s, d, limit=2)] for s, d in cuts.items()
+        }
+    with Session(engine) as cached_session, bar_cache(cached_session):
+        cached_full = {
+            s: [(b.date, b.close) for b in bars_after(cached_session, s, d)] for s, d in cuts.items()
+        }
+        cached_limited = {
+            s: [(b.date, b.close) for b in bars_after(cached_session, s, d, limit=2)]
+            for s, d in cuts.items()
+        }
+    assert cached_full == uncached_full
+    assert cached_limited == uncached_limited
+    for sym in cuts:
+        assert cached_limited[sym] == cached_full[sym][:2]
+        assert all(bar_date > cuts[sym] for bar_date, _ in cached_full[sym])  # no-lookahead: strictly > D
+
+
 # ==================================================================================================
 # forward_return — pure no-lookahead math
 # ==================================================================================================
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index e37d94f..33d2f93 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -66,6 +66,9 @@ _CFG = {
         "atr_period": 5, "high_window_52w": 20, "vol_avg_period": 5,
         "min_history_bars": 40, "breadth_short_ma": 5, "breadth_long_ma": 10,
         "hv_window": 5, "semivol_window": 5, "vol_contraction_recent": 3, "vol_contraction_prior": 5,
+        # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
+        # >= the patterns block's min_history_bars below (20).
+        "max_lookback_bars": 20,
     },
     "sectors": {
         "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
diff --git a/apps/backend/tests/test_sectors.py b/apps/backend/tests/test_sectors.py
index f52cd91..03ed865 100644
--- a/apps/backend/tests/test_sectors.py
+++ b/apps/backend/tests/test_sectors.py
@@ -97,6 +97,9 @@ _SYNTH_CFG = {
         "min_history_bars": 40, "breadth_short_ma": 5, "breadth_long_ma": 10,
         # iter-13 volatility-family windows (required + validated positive) — synthetic small scale.
         "hv_window": 5, "semivol_window": 5, "vol_contraction_recent": 3, "vol_contraction_prior": 5,
+        # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
+        # >= the patterns block's min_history_bars below (20).
+        "max_lookback_bars": 20,
     },
     "sectors": {
         "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
diff --git a/apps/backend/tests/test_themes.py b/apps/backend/tests/test_themes.py
index 14ec1b0..61227d1 100644
--- a/apps/backend/tests/test_themes.py
+++ b/apps/backend/tests/test_themes.py
@@ -103,6 +103,9 @@ _SYNTH_CFG = {
         "min_history_bars": 40, "breadth_short_ma": 5, "breadth_long_ma": 10,
         # iter-13 volatility-family windows (required + validated positive) — synthetic small scale.
         "hv_window": 5, "semivol_window": 5, "vol_contraction_recent": 3, "vol_contraction_prior": 5,
+        # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
+        # >= the patterns block's min_history_bars below (20).
+        "max_lookback_bars": 20,
     },
     "sectors": {
         "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
diff --git a/apps/backend/tests/test_warmup.py b/apps/backend/tests/test_warmup.py
index 8d9e626..bb283a3 100644
--- a/apps/backend/tests/test_warmup.py
+++ b/apps/backend/tests/test_warmup.py
@@ -41,7 +41,7 @@ from sqlmodel import Session, select
 
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
-from app.engine import data_manager, warmup as warmup_mod
+from app.engine import data_manager, prices, warmup as warmup_mod
 from app.engine.forward_testing import backfill_forward_returns
 from app.engine.prices import latest_data_date
 from app.engine.readiness import compute_readiness
@@ -214,6 +214,52 @@ def test_warmup_produced_every_cadence_snapshot_and_forward_returns(warmed_engin
     assert warmed_engine["warmup_record"]["status"] == "ok"
 
 
+def test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns(early_engine, monkeypatch):
+    """iter-26 (J-16, fast-platform item F): the warm-up's cadence loop (`run_scan` x N dates) AND its
+    trailing `backfill_forward_returns` call now share ONE `bar_cache` context (the `warmup.py` fix —
+    the call moved inside the `with bar_cache(session):` block and now passes `session`, not `engine`),
+    so together they load each symbol's full series AT MOST ONCE for the whole warm-up run — not once
+    per cadence date, and not a SECOND time for the forward-return backfill (which used to open a brand
+    new, uncached session). Instrumented exactly like
+    `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` (every full-series bar-store
+    load: the lazy `bars_asof` fallback AND `prefill`; `bars_after`'s cache path routes through the
+    same instrumented `bars_asof`, since it calls `self.bars_asof(...)` to ensure the load).
+
+    The iter-36 (J-96) membership-timeline warm step (`_warm_membership_timeline`) is a SEPARATE,
+    pre-existing, out-of-scope feature: it deliberately opens its OWN new session (never the cadence
+    loop's) and therefore pays its own one-time prefill regardless of this fix — confirmed unrelated
+    (its own test, `test_warmup_precomputes_membership_timeline_cache`, passes unedited). It is
+    no-op'd here so this proof isolates exactly the two pieces iter-26 changed."""
+    engine, cfg = early_engine
+    monkeypatch.setattr(warmup_mod, "_warm_membership_timeline", lambda engine, cfg: None)
+    load_counts: dict[str, int] = {}
+    orig_bars_asof = prices._BarCache.bars_asof
+    orig_prefill = prices._BarCache.prefill
+
+    def _counting_bars_asof(self, session, symbol, d):
+        if symbol not in self._by_symbol:  # a real lazy bar-store load is about to happen
+            load_counts[symbol] = load_counts.get(symbol, 0) + 1
+        return orig_bars_asof(self, session, symbol, d)
+
+    def _counting_prefill(self, session, expected_symbols=None):
+        before = set(self._by_symbol)
+        orig_prefill(self, session, expected_symbols=expected_symbols)
+        for symbol in self._by_symbol:
+            if symbol not in before:  # newly loaded by this prefill
+                load_counts[symbol] = load_counts.get(symbol, 0) + 1
+
+    monkeypatch.setattr(prices._BarCache, "bars_asof", _counting_bars_asof)
+    monkeypatch.setattr(prices._BarCache, "prefill", _counting_prefill)
+
+    job_id = start_warmup(engine, cfg)
+    _join_warmup(job_id)
+    rec = data_manager.get_job(job_id)
+    assert rec["status"] == "ok"
+    assert rec["forward_returns_inserted"] > 0, "the warm-up should have inserted realized forward returns"
+    assert load_counts, "the warm-up should have loaded at least one symbol's bar series"
+    assert max(load_counts.values()) == 1, f"a symbol was loaded more than once: {load_counts}"
+
+
 # ==================================================================================================
 # iter-36 (J-96) — the warm-up precomputes the membership-timeline cache OFF the boot path so the FIRST
 # `GET /api/data` after boot/rebuild serves the cached payload (not the O(dates × pool) cold compute)
diff --git a/config.yaml b/config.yaml
index ce8878f..9952a70 100644
--- a/config.yaml
+++ b/config.yaml
@@ -649,6 +649,15 @@ indicators:
   semivol_window: 63                 # downside-semivolatility window (negative leg only, MAR=0)
   vol_contraction_recent: 21         # recent realized-vol window for the contraction ratio (numerator)
   vol_contraction_prior: 63          # prior realized-vol baseline window for the ratio (denominator)
+  # iter-26 (J-16, fast-platform item F): the TRUE maximum trailing lookback any scoring/pass-3
+  # consumer needs is `high_window_52w` (252) -- every other window above (ma_periods max 200,
+  # rs_windows max 126, vol_avg_period*2 100, vcp/pullback/flat_base min_history_bars <= 90) is
+  # smaller. `scoring.py` slices each member's as-of bar series to the last `max_lookback_bars`
+  # bars BEFORE indicator/pattern computation (bars_asof on a 30-year basis can return ~5,300 bars
+  # on late dates, but every indicator only ever reads a trailing window off the end) -- 320 =
+  # 252 + a ~68-bar safety margin. The byte-identity harness (test_scoring_window.py), not this
+  # value, is the authority: it must show 0 diffs windowed vs. unwindowed; widen this if it ever doesn't.
+  max_lookback_bars: 320
 
 # ----------------------------------------------------------------------------------------
 # iter-2 CONSUMED — Sector/industry leadership. Component weights (must cover every component
diff --git a/incredible_auto_dev/.claude/agents/goal-decomposer.md b/incredible_auto_dev/.claude/agents/goal-decomposer.md
index 543a8a4..6769a37 100644
--- a/incredible_auto_dev/.claude/agents/goal-decomposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-decomposer.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have use
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.2.1
-last_updated: 2026-07-03
+version: 1.3.0
+last_updated: 2026-07-07
 ---
 
 # Goal Decomposer Agent
@@ -204,6 +204,7 @@ If any check fails, fix the spec before writing it — downstream agents execute
 - If `journey-history.json` shows zero remaining FAILING journeys, write a one-line spec saying "All journeys passing — evaluator should declare GOAL_ACHIEVED" and let the evaluator decide. Do NOT artificially manufacture more work.
 - Flag scope creep: if a journey requires capabilities outside `docs/goal.md` Key Capabilities, note it and exclude.
 - Apply lessons. When a `lessons.md` entry's **Applies to:** pattern matches what you're planning, surface the lesson in the iteration spec's BACKGROUND or NOTES section so the developer/reviewer/evaluator sees it. Repeating a documented past mistake is the opposite of episodic memory's purpose.
+- **Log interpretation calls to the assumption ledger.** When a spec decision required interpreting the goal — the goal/journey text is ambiguous about X and you chose reading Y — append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use; never rewrite prior entries), formatted exactly as: `## iter-<N> — goal-decomposer` on its own line, then `**Ambiguity:** <what the goal leaves open>`, `**We chose:** <the reading this iteration builds on>`, `**Reversible:** yes|no`, each on its own line. Signal only — zero entries is fine for most iterations; routine scoping picks are NOT assumptions (same discipline as lessons.md). Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
 - **Conform to the blueprint, and keep it current.** In `--next` mode, plan new pages into the existing Information Architecture and register every new displayed value in the Data Contract by editing `blueprint.md` directly. These *additive* edits — new value rows, a new page under an existing nav section — need no human approval. If you must change the **nav skeleton itself** (add/rename/remove a top-level section, or move a feature's canonical home), make the edit AND write a one-line reason to `runs/goal-session-<sid>/state/blueprint.reapproval-requested`. By default `run-goal.sh` auto-approves the change and continues; only with `--require-blueprint-approval` does it pause for the human to re-approve before the next iteration. Do this only when genuinely necessary — the IA is meant to hold across the whole session.
 - **Never duplicate a contract value.** If a journey needs a value already in the Data Contract, plan to read it from its registered canonical endpoint. Do not plan a second computation or a second endpoint for it — that is exactly the drift the coherence-auditor will FAIL.
 
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index 7e11d79..9d8633c 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.2.1
-last_updated: 2026-07-03
+version: 1.4.0
+last_updated: 2026-07-07
 ---
 
 # Goal Evaluator Agent
@@ -31,11 +31,12 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 11. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
 12. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
 13. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
-14. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
+14. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
+15. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md`. The orchestrator script (`run-goal.sh`) pre-trims it and inlines the recent tail into your prompt — use the inlined content. The file grows unboundedly across a long session.
 
-When appending: use the Edit/Write tools to append to `evaluator-log.md` and `lessons.md` directly. Appending does not require reading the full file first — just append a new entry block.
+When appending: use the Edit/Write tools to append to `evaluator-log.md`, `lessons.md`, and `assumptions.md` directly. Appending does not require reading the full file first — just append a new entry block.
 
 The session id `<sid>`, iteration name `<iter-name>`, and iteration index `<N>` are passed as environment variables: `GOAL_SESSION_ID`, `GOAL_ITER_NAME`, `GOAL_ITER_INDEX`.
 
@@ -72,7 +73,8 @@ Write the updated state to `runs/goal-session-<sid>/state/journey-history.json`.
       "last_verified_iter": "<iter-name>",
       "last_passing_iter": "<iter-name or null>",
       "first_seen_iter": "<iter-name>",
-      "last_evidence_path": "reports/qa/<iter-name>-evidence/UT-01-signup.png"
+      "last_evidence_path": "reports/qa/<iter-name>-evidence/UT-01-signup.png",
+      "spec_hash": "<sha256 of this journey's goal.md block — see below>"
     },
     ...
   },
@@ -97,6 +99,10 @@ Statuses:
 - `regressed` — was passing in a prior iteration, now failing
 - `unknown` — not tested this iteration; carry over previous status
 
+**`spec_hash` — the goal-edit drift record.** Once per evaluation, run `python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md` (prints `{"J-NN": "<sha256>"}`). For every journey whose status you set from THIS iteration's evidence (`passing`, `failing`, `partial`, and baseline `already_passing`), record its current hash as `spec_hash`. For journeys you did not verify this iteration, carry the existing `spec_hash` forward unchanged — or leave it absent (pre-NEED-9 histories have none; never invent one). Never copy a new hash onto a journey you did not re-verify: the hash asserts "this status was verified against exactly this goal text", and the deterministic achievement gate audits it.
+
+**When `iter-<N>/journeys-changed.md` exists:** each listed journey's goal.md text changed AFTER its recorded pass, so that pass is void. If this iteration's evidence verifies the journey against the CURRENT text → `passing`, with the new `spec_hash`. Otherwise → `unknown`, gap noted ("goal text changed; not re-verified") — never carry the stale pass forward. The achievement gate refuses GOAL_ACHIEVED while any listed journey still carries an old-text pass.
+
 ### 4. Append to evaluator-log.md
 
 Append a new entry to `runs/goal-session-<sid>/state/evaluator-log.md`:
@@ -137,6 +143,22 @@ touching `apps/api/auth/`" or "rate-limiter / middleware changes" or "any iter
 adding a new public endpoint">
 ```
 
+### 5b. Append to assumptions.md (when scoring required an interpretation call)
+
+Append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use) whenever scoring this iteration required *interpreting* the goal rather than just reading evidence — e.g. you accepted a truncated email display as satisfying "shows the sender's email", or treated a journey's wording as covering a case it never names. These silent calls are what the human needs to see (and veto) early.
+
+**Skip this step entirely** when no such call was made — zero entries is the normal case; same signal-only discipline as lessons.md (step 5). Routine evidence reading is not an assumption. Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
+
+Format (append, never overwrite):
+
+```markdown
+## iter-<N> — goal-evaluator
+
+**Ambiguity:** <what the goal/journey text leaves open>
+**We chose:** <the interpretation your scoring used>
+**Reversible:** yes|no
+```
+
 ### 6. Write iteration verdict
 
 Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
@@ -185,7 +207,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 
 ### When to use each
 
-- **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, AND this iteration's `coherence.md` is not `COHERENCE-FAIL`. Loop halts with success.
+- **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, this iteration's `coherence.md` is not `COHERENCE-FAIL`, AND no journey listed in `journeys-changed.md` remains un-re-verified against the current goal text. Loop halts with success.
 
 - **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
 
@@ -210,6 +232,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Do NOT mark `GOAL_ACHIEVED` if any Must-have journey has status `failing` or `unknown`. All journeys must have positive evidence of passing.
 - Do NOT mark `GOAL_ACHIEVED` if any anti-goal violation is unresolved.
 - Do NOT mark `GOAL_ACHIEVED` if this iteration's `coherence.md` is `COHERENCE-FAIL`. A coherence failure is a structural veto — the product is incoherent (scattered navigation, a duplicate home, or the same value computed/served more than one way) even if all journeys pass. Drive a consolidation `CONTINUE` instead.
+- Do NOT mark `GOAL_ACHIEVED` if this iteration's `journeys-changed.md` lists any journey you did not re-verify against the current goal text this iteration — a pass earned on the old text is not a pass.
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
 - If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
diff --git a/incredible_auto_dev/.claude/agents/goal-proposer.md b/incredible_auto_dev/.claude/agents/goal-proposer.md
index 80c5b02..e18e0b1 100644
--- a/incredible_auto_dev/.claude/agents/goal-proposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-proposer.md
@@ -4,8 +4,8 @@ description: Goal-mode continuous-improvement proposer (opt-in, default-off). Af
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write, Edit]
 disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.1
-last_updated: 2026-06-30
+version: 1.1.0
+last_updated: 2026-07-08
 ---
 
 # Goal Proposer Agent (continuous improvement)
@@ -45,24 +45,32 @@ The prompt gives you: the **session id**, the **session state dir** (`SESSION_DI
    the pre-screen snapshot / scan tool when one exists, then drill down with whatever analysis tools the
    guidance names, and look at the rest of the surface for UX/structure/missing-dimension gaps). Form a
    small shortlist of *useful* candidates by the project's lens — not single-metric outliers.
-2. **Keep only what survives the project's validation screen.** The guidance defines what counts as
+2. **Detect vision gaps.** Parse `docs/goal.md`'s **Vision** paragraph and **Key Capabilities** list;
+   compare each claim against ALL Must-have journeys (human AND the `<!-- AUTO:journeys -->` block).
+   List every claim no journey covers, and record each as a candidate tagged `kind: vision-gap` with
+   `robustness: speculative` (a coverage observation is never evidence-backed) — vision-gap candidates
+   join the shortlist and flow through the same screen/de-dup/backlog steps below. Name the uncovered
+   claims in `proposer-result.json`'s `summary` (also when you stop dry). A gap alone must NOT force an
+   extension — the honest-stop rule below still wins.
+3. **Keep only what survives the project's validation screen.** The guidance defines what counts as
    validated (for data products this is typically an out-of-sample hold-out; other products may define
    usage evidence or none). An evidence-backed candidate is proposable ONLY if the project's screen
    marks it a survivor. Tag each `robustness: robust` (screened survivor) or `speculative` (a
    structural/UX idea not yet evidence-backed). Never present a speculative candidate as proven.
-3. **De-duplicate.** Drop anything already in `enhancement-proposals.jsonl` or already a journey in
+4. **De-duplicate.** Drop anything already in `enhancement-proposals.jsonl` or already a journey in
    `goal.md` (human or AUTO).
-4. **Write the backlog.** Append the survivors best-first to `SESSION_DIR/enhancement-proposals.jsonl`
+5. **Write the backlog.** Append the survivors best-first to `SESSION_DIR/enhancement-proposals.jsonl`
    (one JSON object per line) in the schema the guidance defines.
-5. **Promote the top buildable proposal(s) into the goal.** For the best 1–2 proposals, append a new
+6. **Promote the top buildable proposal(s) into the goal.** For the best 1–2 proposals, append a new
    Must-have journey to the `<!-- AUTO:journeys -->` block in `docs/goal.md` — follow the
    **`goal-self-extension` skill** exactly (surgical marker-only Edit; pick the next free `J-NN`; never
    touch human journeys or the Anti-goals). Each journey's **Steps + Acceptance MUST bake in** the
    project's consistency rule (read the canonical endpoint / register any new shared value in the Data
    Contract) and the walkthrough requirement (a `[NEW]`-flagged demo-narrator walkthrough of the new
    surface). Keep journeys small (target 1, at most 2 per cycle) so each iteration stays focused.
-6. **Write the result file** `SESSION_DIR/proposer-result.json`:
+7. **Write the result file** `SESSION_DIR/proposer-result.json`:
    `{"extended": <bool>, "n_new_journeys": <int>, "n_proposals": <int>, "dry": <bool>, "summary": "<one line>"}`.
+   When step 2 found vision gaps, `summary` names the uncovered claims.
 
 ## The honest stop (the loop's boundary)
 
diff --git a/incredible_auto_dev/.claude/agents/iteration-summarizer.md b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
index 01f91a5..23fad31 100644
--- a/incredible_auto_dev/.claude/agents/iteration-summarizer.md
+++ b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
@@ -4,8 +4,8 @@ description: Post-iteration summarizer. Reads the iteration's artifacts (dev han
 model: claude-sonnet-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /*)", "Bash(rm -rf /)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-05-12
+version: 1.1.0
+last_updated: 2026-07-07
 ---
 
 # Iteration Summarizer
@@ -55,6 +55,7 @@ The dispatch wrapper passes you a `phase-id` (e.g. `phase-7` or `goal-money-firs
 - `runs/goal-session-<sid>/iter-<N>/eval.md` — verdict, Journey Results table, Next-Step Recommendation
 - `runs/goal-session-<sid>/state/journey-history.json` — current state of every journey
 - The dispatch wrapper provides the last ~300 lines of `runs/goal-session-<sid>/state/evaluator-log.md` inline in the prompt — use the inline content, do not read the file directly.
+- The dispatch wrapper provides the recent tail of `runs/goal-session-<sid>/state/assumptions.md` (the assumption ledger, NEED-5) inline in the prompt — use the inline content, do not read the file directly. The placeholder "(no assumptions recorded yet)" means the ledger is empty.
 
 ## Iteration type detection
 
@@ -174,6 +175,16 @@ A short recommendation. Sources, in priority order:
 
 One short paragraph. Do not invent priorities. If the source says "halt — goal achieved", write that.
 
+## Assumptions made
+
+Required every iteration (both modes). Surfaces the interpretation calls other agents logged to the session assumption ledger so the product owner can veto a wrong reading early.
+
+Source: the inline assumption-ledger tail the dispatch wrapper passed in (goal mode). Ledger entries arrive as `## iter-<N> — <agent>` blocks with `**Ambiguity:**` / `**We chose:**` / `**Reversible:**` lines.
+
+- Rewrite each ledger entry as ONE plain bullet: `- iter-<N> · <agent> — Ambiguity: <…>. We chose: <…>. Reversible: <yes|no>`. Carry the fields verbatim (trim, don't re-judge). NEVER copy the ledger's `## iter-N` headings into the summary — an H2 inside this section breaks the renderer's section parsing.
+- Order entries newest-first. If the inline tail is long, keep all entries from THIS iteration plus the most recent ~10 older ones.
+- When the inline tail is the placeholder "(no assumptions recorded yet)", the wrapper passed no ledger content (phase mode), or no entries exist: write exactly `none recorded` as the section body — never omit the section.
+
 ## Quick verify
 
 Goal-full and phase iters only. If `what-to-click.md` exists and has Verification Steps, copy the numbered steps verbatim (just the action lines, not the per-step "Expect:" sub-bullets — those clutter the summary). Cap at 5 steps. Prefix the block with "From `reports/phase-<phase-id>-what-to-click.md`:".
diff --git a/incredible_auto_dev/.claude/commands/goal-init.md b/incredible_auto_dev/.claude/commands/goal-init.md
new file mode 100644
index 0000000..014d1d1
--- /dev/null
+++ b/incredible_auto_dev/.claude/commands/goal-init.md
@@ -0,0 +1,40 @@
+---
+description: Interview the user section-by-section to author or update docs/goal.md (the goal-mode product contract) — playback confirmation before any write, structural self-check after. The guided alternative to hand-editing templates/project-goal.md.
+allowed-tools: Bash(grep:*), Bash(diff:*), Bash(cat:*), Bash(ls:*), Bash(python3:*), Read, Write, Edit
+---
+You are the **goal-authoring interviewer**. Produce a high-quality `docs/goal.md` —
+the file that decides everything goal mode builds — by interviewing the user one
+topic at a time, playing back what you understood, and writing only after they
+explicitly confirm.
+
+First read `.claude/skills/goal-authoring.md` and follow it exactly: it holds the
+section-by-section interview script, the playback format, and the structural
+checklist. Do not improvise a different order and do not skip the playback.
+
+1. **Detect mode.** If `docs/goal.md` is absent — or exists but is still an unfilled
+   template copy (all `<...>` placeholders) — you are in **create mode**. Otherwise
+   you are in **update mode**: read the existing file first, summarize what each
+   section already says (one line each), and interview only about the parts the user
+   wants to change. Never silently overwrite an existing goal.
+2. **Interview** per the skill's script: one topic at a time, in the section order of
+   `templates/project-goal.md`, offering multiple-choice options where the skill
+   suggests them. Plain conversation only — assume no special tools or UI.
+3. **Play back** in the skill's playback format — one line per journey, anti-goals
+   verbatim; in update mode, show old → new for every section that would change —
+   and get an explicit "yes" BEFORE writing anything. On corrections, update and
+   re-play the changed lines.
+4. **Write.** Create mode: write the full `docs/goal.md` following the section
+   structure of `templates/project-goal.md`, every placeholder replaced by confirmed
+   content. Update mode: apply ONLY the confirmed changes as surgical edits; never
+   touch a `<!-- AUTO:journeys -->` … `<!-- /AUTO:journeys -->` block and never
+   reuse or renumber an existing `J-NN` id.
+5. **Self-check** (must pass before declaring success). If
+   `scripts/automation/lib/goal_lint.py` exists, run
+   `python3 scripts/automation/lib/goal_lint.py docs/goal.md`; otherwise apply the
+   skill's structural checklist (the `validate_goal_file` rules plus no leftover
+   `<...>` template placeholders). Fix any failure and re-check. Show the user the
+   passing result.
+6. **Stop.** Do not launch `run-goal.sh`, dispatch agents, or edit anything besides
+   `docs/goal.md`. Tell the user the next step:
+   `./scripts/automation/run-goal.sh --session-id <id>` (headless) or `/goal <id>`
+   (interactive).
diff --git a/incredible_auto_dev/.claude/commands/goal-lint.md b/incredible_auto_dev/.claude/commands/goal-lint.md
new file mode 100644
index 0000000..0e75514
--- /dev/null
+++ b/incredible_auto_dev/.claude/commands/goal-lint.md
@@ -0,0 +1,69 @@
+---
+description: Quality-lint docs/goal.md — deterministic linter plus an LLM semantic pass for what rules cannot catch (journey contradictions, unobservable acceptance, uncovered risky surfaces). Report-only — writes reports/goal-lint.md, NEVER edits goal.md.
+allowed-tools: Bash(python3:*), Bash(grep:*), Bash(cat:*), Bash(ls:*), Read, Write
+---
+You are the **goal linter**. Assess `docs/goal.md` (the goal-mode product contract)
+and write a findings report the user can act on. This command is **REPORT-ONLY**:
+the only file you may write is `reports/goal-lint.md`. You must NEVER edit
+`docs/goal.md` — journeys and anti-goals are ask-the-user-first class
+(`.claude/maintenance-protocol.md` §1). The user applies fixes themselves, by hand
+or via `/goal-init` (update mode); your job is to make every suggested rewrite
+paste-ready. Do not launch the engine, dispatch agents, or edit any other file.
+
+1. **Deterministic pass.** Run
+   `python3 scripts/automation/lib/goal_lint.py docs/goal.md` and show the user its
+   output verbatim (exit 0 + no output = structurally clean; 1 = warnings; 2 =
+   structural errors). If it reports the file unreadable or missing, stop and tell
+   the user to author one with `/goal-init` — there is nothing to lint.
+
+2. **Semantic pass.** Read `docs/goal.md` in full, plus the quality bars in
+   `.claude/skills/goal-authoring.md` (interview script items 3, 9, 10 and the
+   structural checklist). Judge MEANING, not keywords — you are looking for exactly
+   what the deterministic rules cannot see:
+   - **Journey contradictions** — two journeys whose steps or acceptance cannot both
+     hold (conflicting end states, one journey destroying state another asserts), or
+     the same value/metric named in different words across journeys without a
+     Product Shape canonical-value pin.
+   - **Unobservable acceptance phrased measurably** — an Acceptance line that passes
+     the vague-term filter yet no browser test could SEE on the page ("the data is
+     saved", "an email is sent", "the API returns 200"). Rewrite to the visible
+     surface: what text/element appears where.
+   - **Steps that require guessing** — a step with no concrete URL, visible label,
+     or input value, where a browser agent would have to invent one.
+   - **Not independently runnable** — a journey that silently depends on state a
+     prior journey created, with no setup step of its own from a fresh page load.
+   - **Risky surface with no anti-goal coverage** — journeys or Vision mention auth,
+     payments, uploads, personal data, or external network calls, and no anti-goal
+     bounds that surface.
+   - **Anti-goals that fool the keyword check** — a bullet containing a prohibition
+     word or number that is still not checkable ("must feel fast", "no bad UX").
+   - **Unmeasurable success criteria** — a Success Criteria bullet with no number
+     and no observable state.
+   Do not re-report a line the deterministic pass already flagged unless the
+   semantic problem is a different one.
+
+3. **Write the report** to `reports/goal-lint.md` (overwrite — it is a snapshot of
+   the latest run) in exactly this shape:
+
+   ```markdown
+   # goal-lint report — docs/goal.md
+
+   Run: <YYYY-MM-DD> · deterministic exit: <0|1|2> · semantic findings: <N>
+
+   ## Deterministic lint (goal_lint.py)
+   <verbatim tool output, or "clean (exit 0, no output)">
+
+   ## Semantic findings
+   ### <check name> — line <N>
+   > <the exact line quoted from docs/goal.md>
+   - **Problem:** <one sentence: why this will mislead the evaluator/browser-qa>
+   - **Suggested rewrite:** <concrete replacement text, paste-ready>
+   ```
+   Repeat the `###` block per finding; write `None.` under `## Semantic findings`
+   when the pass is clean. Close with a `## Summary` H2: 1-3 lines — overall
+   assessment plus the single highest-impact fix.
+
+4. **Show the user** the report path, the finding count, and the summary lines.
+   Remind them the report is advisory — nothing blocks the engine — and that fixes
+   go through `/goal-init` (update mode) or a hand edit of `docs/goal.md`, never
+   through this command.
diff --git a/incredible_auto_dev/.claude/commands/goal-status.md b/incredible_auto_dev/.claude/commands/goal-status.md
index 315a19c..f318de0 100644
--- a/incredible_auto_dev/.claude/commands/goal-status.md
+++ b/incredible_auto_dev/.claude/commands/goal-status.md
@@ -22,5 +22,8 @@ the engine, dispatch agents, or write anything.
    say so and point to `/goal-resume <sid>`. Also point the user at the full
    timestamped log: `tail -f runs/goal-session-<sid>/engine.log`.
 6. Summarize plainly whether the session is **running**, **paused** (and exactly
-   how to resume — e.g. review the blueprint then `/goal-resume`), **orphaned**
-   (dead engine PID — `/goal-resume`), or **finished** (and the final verdict).
+   how to resume — e.g. review the blueprint then `/goal-resume`; for
+   `AWAITING_INTENT_REVIEW` point at `runs/goal-session-<sid>/intent-review.md`,
+   the opt-in `--intent-checkpoint` "is this the product you wanted?" pause —
+   resuming acknowledges it), **orphaned** (dead engine PID — `/goal-resume`),
+   or **finished** (and the final verdict).
diff --git a/incredible_auto_dev/.claude/letter-to-future-sessions.md b/incredible_auto_dev/.claude/letter-to-future-sessions.md
index 35c24f4..fb12dd1 100644
--- a/incredible_auto_dev/.claude/letter-to-future-sessions.md
+++ b/incredible_auto_dev/.claude/letter-to-future-sessions.md
@@ -4,6 +4,10 @@ Written 2026-07-03 by the last Fable-5 session, at the end of the hardening pass
 prepared this chain for the Opus/Sonnet/Haiku era. Read this when you're about to do
 framework work; it says where this system breaks and what we most wish we'd been told.
 
+The living improvement backlog is [`docs/improvement-roadmap.md`](../docs/improvement-roadmap.md)
+— pick up framework work there (one item per session, per its ground rules), and put new
+pain into its §16 staging section.
+
 ## The three things that matter most (nobody asked for these)
 
 1. **Trust the gates more than any single verdict — including your own.** The most
diff --git a/incredible_auto_dev/.claude/skills/goal-authoring.md b/incredible_auto_dev/.claude/skills/goal-authoring.md
new file mode 100644
index 0000000..ef3d6cd
--- /dev/null
+++ b/incredible_auto_dev/.claude/skills/goal-authoring.md
@@ -0,0 +1,110 @@
+# Skill: goal-authoring — interviewing for, playing back, and checking `docs/goal.md`
+
+Used by `/goal-init` (interview → author) and, once it ships, by `/goal-lint` (checklist
+reuse). `docs/goal.md` is the product constitution: the goal-evaluator treats its
+Must-have journeys as objective ground truth and its Anti-goals as veto rules, so its
+quality decides every downstream iteration. Vague journeys are the documented #1
+failure mode (`.claude/anti-patterns.md` #1, #18).
+
+## Interview ground rules
+
+- ONE topic at a time — never a wall of questions. Follow the section order below
+  (it is the order of `templates/project-goal.md`).
+- Offer 2-4 multiple-choice options where sensible (marked ⊕ below) — picking a letter
+  beats facing a blank page. Always accept free-text instead.
+- Plain conversation only: assume no special tools, forms, or UI beyond text.
+- The user's words win. Suggest sharper phrasings, but never write content the user
+  has not confirmed. "Unknown" is acceptable — leave optional sections lean rather
+  than inventing detail.
+- Push every vague answer one step toward observable: "how would a browser test tell
+  this passed?"
+
+## Interview script (template section order)
+
+1. **Vision** — what is the product, for whom, what problem does it solve? Target:
+   one paragraph.
+2. **Target Users** — who they are and what they need. ⊕ offer archetypes if unsure
+   (solo-developer tool, internal team app, consumer web app, data dashboard).
+3. **Success Criteria** — measurable outcomes. Reject unmeasurable ones ("popular",
+   "fast"): ask for a number, an observable state, or drop the criterion.
+4. **Key Capabilities** — prioritized list; split must-have from nice-to-have.
+5. **Non-Goals** — explicitly out of scope. ⊕ suggest candidates from what the user
+   did NOT mention (auth? payments? mobile? multi-user? persistence?).
+6. **Constraints** — technical / business / timeline. ⊕ stack preference, single
+   process vs services, offline-capable, no paid services.
+7. **Design Direction** — visual style, mood, optional reference. ⊕ minimal-clean /
+   professional-dense / playful / cyber-futuristic.
+8. **Product Shape** (optional, high-leverage) — navigation sketch plus canonical
+   values (metrics/entities that must read the SAME everywhere; each is pinned to one
+   source). Explain the payoff in one line — it prevents "the same number differs
+   across pages" — and accept "skip" without pushing.
+9. **Must-have user journeys** — the core. For EACH journey collect:
+   - a unique id `J-NN` (zero-padded, sequential; never reuse or renumber),
+   - a short name,
+   - numbered steps a browser agent can execute — every step names a concrete URL,
+     visible label, or input value,
+   - one `Acceptance:` line describing the observable end state.
+   Quality bar: steps executable without guessing; the Acceptance line contains no
+   vague words ("works well", "fast", "properly", "intuitive", "user-friendly",
+   "correctly"); the end state is visible on the page — not "the data is saved" but
+   "the new row shows `<the value entered>`". 2-6 journeys is the right starting
+   size; each must be independently runnable from a fresh page load.
+10. **Anti-goals** — veto rules the evaluator enforces even when every journey
+    passes. Concrete and checkable, never aspirations ("secure" ✗ → "no credentials
+    in source files" ✓). ⊕ offer the template's defaults: no hard-coded secrets; no
+    auth tokens in `localStorage`; no paid SaaS unless listed in Constraints;
+    keyboard-accessible form inputs.
+
+## Playback format (before ANY write)
+
+Present exactly this shape, then ask for explicit confirmation:
+
+    Here is what I understood:
+    - Vision: <one line>
+    - Target users: <one line>        - Success criteria: <one line>
+    - Key capabilities: <one line>    - Non-goals: <one line>
+    - Constraints: <one line>         - Design direction: <one line>
+    - Product shape: <one line, or "skipped">
+    Journeys (one line each):
+    - J-01 <name> — <acceptance, one line>
+    - J-02 <name> — <acceptance, one line>
+    Anti-goals (verbatim, exactly as they will be written):
+    - <anti-goal 1>
+    - <anti-goal 2>
+
+    Shall I write this to docs/goal.md?
+
+No write happens before an explicit yes. That yes is the user approval required for
+editing `docs/goal.md` (ask-first class, `.claude/maintenance-protocol.md` §1).
+Corrections → update, re-play only the changed lines, re-confirm.
+
+## Update mode (a real `docs/goal.md` already exists)
+
+- Read the existing file FIRST and summarize each section in one line so the user
+  sees the current state before deciding what to change.
+- Interview only the sections the user wants changed.
+- Playback becomes a diff: for each changed section show old → new; list unchanged
+  sections by name only. Confirmation still precedes any write.
+- Never edit between `<!-- AUTO:journeys -->` and `<!-- /AUTO:journeys -->` — that
+  block is goal-proposer territory (`skills/goal-self-extension.md`). Never reuse or
+  renumber an existing `J-NN`; new journeys take the next free id at the existing
+  zero-padding width.
+
+## Structural checklist (run after writing; fix and re-check on any failure)
+
+If `scripts/automation/lib/goal_lint.py` exists, run
+`python3 scripts/automation/lib/goal_lint.py docs/goal.md` INSTEAD of this list.
+Otherwise all five rules must hold — 1-4 mirror `validate_goal_file` in
+`scripts/automation/run-goal.sh`, which aborts the engine at startup when one fails:
+
+1. Heading `## Must-have user journeys` present at line start.
+2. Heading `## Anti-goals` present at line start.
+3. At least one journey bullet matching `^- \*\*J-[0-9]+:`.
+4. The Anti-goals section has at least one non-empty bullet containing neither
+   "TODO" nor "placeholder".
+5. No leftover template placeholders: `grep -n '<' docs/goal.md` and confirm every
+   hit is intentional markup (an HTML comment, a code literal), not an unfilled
+   `<...>` fill-in copied from the template.
+
+Additionally (template contract, not engine-enforced): every journey has numbered
+steps and an `Acceptance:` line — browser-qa and the goal-evaluator parse these.
diff --git a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
index e7fd053..82e1d7d 100644
--- a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
@@ -12,6 +12,12 @@ your overall impression of the iteration.
      diff. Findings here are facts; you do not need to re-derive them.
    - `iter-diff.md` — the bounded diff (complete file list + stats; hunks may be capped, and
      the header lists exactly what was excluded/truncated).
+   - `journeys-changed.md` — goal-edit drift note, present only when a recorded-passing
+     journey's `docs/goal.md` text changed since it was verified. Every listed journey's
+     prior pass is VOID: it enters your journey table (step 2) as needing re-verification at
+     the same evidence bar as a status change — a results row + screenshot against the
+     CURRENT text — or it drops to `unknown`. Record the new `spec_hash` only for journeys
+     you actually re-verified (body step 3).
    Fallback when absent: run `git diff <snapshot-sha>..HEAD --stat` first, then read only the
    hunks for files that plausibly affect journeys or anti-goals. Never paste a full raw diff
    into your reasoning.
diff --git a/incredible_auto_dev/CLAUDE.md b/incredible_auto_dev/CLAUDE.md
index 22bd784..587432d 100644
--- a/incredible_auto_dev/CLAUDE.md
+++ b/incredible_auto_dev/CLAUDE.md
@@ -30,13 +30,13 @@ Both modes run on **Claude Code** (default) or **OpenAI Codex CLI** (`--cli code
 | `.claude/judgment-rubrics.md` | Executable judgment criteria (escalation, definition-of-done, stop-and-ask, wrong-direction signals, evidence floors, honesty) with ✚/✖ examples | Judges (evaluator, auditor, decomposer, reviewer) and anyone making verdict-class calls |
 | `.claude/delegation-templates.md` | Fill-in dispatch templates (search/implement/refactor/research/review) | Anyone dispatching agents |
 | `.claude/maintenance-protocol.md` | Which files may be edited autonomously vs. need the user; the resync invariant; lessons format; condensation rule | Anyone editing framework/instruction files |
-| `.claude/anti-patterns.md` | 20 documented failure modes from production use | Orchestrator, reviewer, auditor; add new ones per maintenance protocol §2 |
+| `.claude/anti-patterns.md` | Documented failure modes from production use | Orchestrator, reviewer, auditor; add new ones per maintenance protocol §2 |
 | `.claude/letter-to-future-sessions.md` | How this system degrades and what to check first | New sessions doing framework work |
 | `.claude/architecture/` | System architecture, agent catalog, pipeline flow, artifact map | Reference (all agents) |
 
 ## AGENTS AND SKILLS
 
-**19 agents** live in `.claude/agents/<name>.md` (rendered from `agents/<name>/`): the
+**Agents** live in `.claude/agents/<name>.md` (rendered from `agents/<name>/`): the
 pipeline chain (orchestrator, developer, reviewer, qa, auditor, release-manager,
 product-manager), the UI chain (ui-impact-analyst, ui-test-designer, browser-qa-agent,
 phase-closure-auditor, ux-regression-reviewer), goal mode (goal-decomposer, goal-evaluator,
@@ -44,7 +44,7 @@ coherence-auditor, goal-proposer), and showcase (iteration-summarizer, demo-narr
 readme-maintainer). Roles, inputs, and verdict contracts live in each agent file; the
 catalog with model tiers is [`.claude/architecture/agents.md`](.claude/architecture/agents.md).
 
-**14 skills** (reusable methodologies) live in `.claude/skills/` — each agent's body names
+**Skills** (reusable methodologies) live in `.claude/skills/` — each agent's body names
 the skills it must follow. Catalog: [`.claude/architecture/skills-and-hooks.md`](.claude/architecture/skills-and-hooks.md).
 
 Model routing: each agent's `model_tier` (`agents/<name>/agent.yaml`) resolves through
diff --git a/incredible_auto_dev/README.md b/incredible_auto_dev/README.md
index 1e10f3e..03a2e0a 100644
--- a/incredible_auto_dev/README.md
+++ b/incredible_auto_dev/README.md
@@ -5,11 +5,11 @@ A reusable framework for running phased software development with Claude AI agen
 ## What This Is
 
 A collection of:
-- **14 Claude agent definitions** covering the full dev lifecycle, UI visibility, per-iteration summary, and an auto-recorded product demo
-- **18 automation shell scripts** orchestrating an 11-step pipeline plus an on-demand demo viewer
-- **5 security hooks** guarding against supply-chain attacks, dangerous commands, and vague artifacts
-- **13 skills** providing reusable methodologies for UI analysis, test design, and doc updates
-- **18 report templates** for consistent handoffs across all agents
+- **Claude agent definitions** covering the full dev lifecycle, UI visibility, per-iteration summary, and an auto-recorded product demo — every agent is listed in [Agent Roles](#agent-roles)
+- **Automation shell scripts** orchestrating an 11-step pipeline plus an on-demand demo viewer
+- **Security hooks** guarding against supply-chain attacks, dangerous commands, and vague artifacts
+- **Skills** providing reusable methodologies for UI analysis, test design, and doc updates
+- **Report templates** for consistent handoffs across all agents
 - **A modular CLAUDE.md system** (core rules, workflow, project config, anti-patterns, architecture docs)
 
 The chain has checkpoint/resume, quota-exhaustion auto-retry, and a verdict-gated pipeline where each stage must pass before the next runs.
@@ -341,6 +341,8 @@ Iteration name `goal-<sid>-iter-<N>` is used as the "phase name" so existing scr
 | `goal-decomposer` | strong | (goal mode) | Reads goal + state, writes next iteration spec, picks lean/full depth; drafts the blueprint at baseline |
 | `goal-evaluator` | strong | (goal mode) | Skeptical done/regression/stall judgment, updates journey-history; vetoes GOAL_ACHIEVED on COHERENCE-FAIL |
 | `coherence-auditor` | standard | (goal mode) | Audits each iteration's diff against the blueprint (information architecture + data contract); hard-fails only on objective drift |
+| `goal-proposer` | strong | (goal mode, opt-in) | After every Must-have journey passes, surveys the whole product through the project's usefulness lens (`project-extensions/proposer-guidance.md`), writes an enhancement-proposals backlog, and appends the best survivors as new Must-have journeys in `docs/goal.md` AUTO:journeys — runs only when that guidance file exists |
+| `readme-maintainer` | standard | (goal mode) | After each iteration, refreshes the project-root README's marker-delimited AUTO blocks so capabilities and "How to run" stay accurate; non-blocking showcase step, never gates the pipeline |
 
 Model tiers: each agent's `model_tier` lives in `agents/<name>/agent.yaml`; tiers resolve to model ids in `config/model-tiers.yaml`. Edit, then `python3 scripts/automation/sync-cli-assets.py` and commit the regenerated mirrors.
 
@@ -374,6 +376,8 @@ Model tiers: each agent's `model_tier` lives in `agents/<name>/agent.yaml`; tier
 ./scripts/automation/demo.sh <sid> --delivered         # open the GOAL_ACHIEVED "delivered" wrap
 
 # Utilities
+./scripts/automation/run-evals.sh                      # offline eval suite (<30s, no API) — run before every framework commit
+bash scripts/automation/install-git-hooks.sh           # OPT-IN pre-commit eval guard (fast subset, <10s) — see Tests
 ./scripts/automation/generate-test-plan.sh phase-1     # write test plan before dev
 ./scripts/automation/ui-audit-phase.sh phase-1         # standalone UI audit
 ./scripts/automation/check-install.sh "pip install X"  # check install safety
@@ -448,87 +452,48 @@ This framework is designed to be added to project repos as a submodule or subtre
 - **Framework docs**: [`.claude/architecture/`](.claude/architecture/README.md) -- how this framework works
 - **Project docs**: `docs/architecture/` -- what the project has built (auto-updated per phase)
 
-## Token Optimization — Pending Work
+## Improvement Roadmap
 
-Tier 1 (safe, mechanical) shipped in commit `15507dc` (May 2026): telemetry on by default, CLAUDE.md double-load removed from 15 prompt sites, orchestrator no longer re-reads `.claude/architecture/*.md`, goal-mode `evaluator-log.md` / `lessons.md` pre-trimmed and inlined, orphan `ui-workflow-inference` skill wired up.
-
-The items below are deliberately deferred — do them in order, with a real telemetry baseline before each.
-
-### Step 0 — Establish a baseline (do this first)
-
-With `CHAIN_TELEMETRY_TOKENS` now defaulting to true, the next phase or goal iteration writes per-call usage to:
-- Phase mode: `runs/<phase>/trace/trace.jsonl`
-- Goal mode: `runs/goal-session-<sid>/telemetry.jsonl`
-
-Analyze with: `python3 scripts/automation/lib/analyze_telemetry.py runs/<phase>/trace/trace.jsonl` — gives per-agent input/output/cache/cost breakdown. Without this baseline, everything below is guesswork.
-
-### Tier 1 polish (low-risk leftovers)
-
-- [x] **Shipped** — Remove the duplicated "Token and Questioning Policy" footer from each agent file (`.claude/agents/*.md`). Agent-specific bullets are kept (e.g., developer.md "Ask only about: schema decisions, lifecycle states…"); generic paraphrasing of `core.md` is gone. See `agents/<name>/body.md`.
-- [x] **Shipped** — Drop `CLAUDE.md` from the "Always read first" list in the 11 remaining agent files. CLAUDE.md is auto-loaded into the system prompt; each agent now has a friendly one-line reassurance instead of re-reading the file.
-- [ ] Inline only the sections each agent needs from `.claude/project-template.md` — release-manager needs the never-commit list (5 lines); developer needs most of it. Add a helper in `lib/common.sh` that emits the right slice per agent. (Deferred until measured token win is meaningful.)
-
-### Tier 2 (needs baseline data first)
-
-- [x] **Shipped — Per-agent `--effort` overrides.** Resolved per agent via `lib/agent_permissions.py effort <agent>`. `developer`, `reviewer`, `auditor`, `orchestrator`, `goal-decomposer`, `goal-evaluator`, `browser-qa-agent`, and `demo-narrator` stay at `--effort max`. `release-manager`, `qa`, `ui-test-designer`, `phase-closure-auditor`, and `ui-impact-analyst` drop to `--effort medium`. Escape hatch: `CHAIN_DISABLE_EFFORT_OVERRIDE=true`.
-- [ ] **Move orchestrator from Opus → Sonnet** (`agents/orchestrator/agent.yaml` `model_tier`). Plan-writing is structured-output work. A/B against 2–3 historical phases — revert if plan quality drops.
-- [ ] **Move goal-decomposer from Opus → Sonnet.** Same rationale as orchestrator. Keep goal-evaluator on Opus (skeptical adversarial judgment).
-- [ ] **Skip `generate-test-plan.sh` (Step 2/11) when the spec already lists test scenarios.** Need a clear heuristic for "spec has tests" — don't skip silently.
-- [ ] **Cap audit-failure full-rerun.** `run-phase.sh:649-679` re-runs dev + review + QA on audit fail. If telemetry shows that path firing often, switch to fix-only mode.
-
-### Pipeline parallelism (shipped)
-
-- [x] **Parallel post-dev fanout.** Branch A (ui-impact → ui-test-design → browser-qa → demo) runs in parallel with Branch B (qa-validate), with shared services. See the [Faster Iterations](#faster-iterations) section. Default for every phase with a frontend; backend-only phases run sequentially.
-
-### Tier 3 (don't touch unless data forces)
-
-- ~~Downgrade qa below Haiku~~ — qa drives Chrome MCP browser flows; lower may misread DOM. If browser checks regress, **upgrade** to Sonnet, not down.
-- ~~Merge ui-impact-analyst + ui-test-designer + ux-regression-reviewer~~ — each is a separate skeptical source the closure auditor depends on. Not worth losing the independence for one Sonnet call's worth of savings.
-- ~~Eliminate retries~~ — they exist for quality reasons. Only consider capping the audit-failure full-rerun (see Tier 2 above).
-
-### How to know when to stop
-
-If a 30-iteration goal session costs <$X and a phase costs <$Y (your numbers), it's not worth more optimization — invest the time in features instead.
-
-## Pipeline Hardening (Strengthen Claude-only Weak Spots) — Pending Work
-
-Benchmark evidence (May 2026) shows Opus 4.7 trails GPT-5.5 on Terminal-Bench 2.0 by 13.3 points and emits ~3.5x more output tokens per task. The decision is to keep this project Claude-only and harden the pipeline at those weak spots rather than introduce a second model.
-
-### Shipped (or in this branch)
-
-- [x] **Test-failure digest script** (`scripts/automation/lib/test_failure_digest.py`) — distills raw pytest/jest/vitest/mocha output into a structured markdown digest. Invoked by the `qa` agent on test failure; the `developer` agent reads it first on retry. Removes the "grep through 500-line log" task from the model — exactly the work GPT-5.5 leads on.
-- [x] **Reviewer YAML schema + token budget** — replaces the prose review-report format with a verdict line + YAML structured findings + optional brief detailed findings. Hard caps: PASS ≤ 200 tokens, PASS_WITH_NOTES ≤ 400, FAIL ≤ 800 (vs. ~1200–2500 today).
-
-### Deferred — do these one at a time, with telemetry before/after
-
-- [ ] **Move `reviewer` from Opus to Sonnet 4.6** (or Haiku 4.5 for cheap quick reviews). Different model in the same family captures a meaningful subset of blind spots at lower cost. Per-agent tiers in `agents/*/agent.yaml` already support this. Ship after the YAML schema is stable so the cheaper model has a tighter target. See also Token Optimization Tier 2 for the orchestrator equivalent.
-- [ ] **Extended-thinking on `auditor` + adversarial framing.** Set `thinking.budget_tokens` for the auditor and prepend "assume the implementation is buggy and find why." Extended thinking is Claude's largest unexploited reasoning lever and directly attacks the "long-context-large-system" weakness on benchmarks like SWE-Bench Pro. Test budget vs. latency on 2–3 phases before rolling out broadly.
-- [ ] **Goal-mode iteration-state synthesis.** Have `goal-evaluator` produce a fresh `iteration-state.md` after each iteration, prepended to the next iteration's context. Don't rely on the model's recall of `journey-history.json`. Combats long-loop context drift — which is where Opus 4.7 weakens most relative to GPT-5.5. Touches goal-mode internals; pick it up only after the first two deferred items are stable.
-
-### How to know when each is worth doing
-
-For each deferred item, the trigger is a measured regression — not a guess:
-
-| Item | Signal that says "do it now" |
-|------|------------------------------|
-| Reviewer → Sonnet | Reviewer output tokens still > Sonnet's typical budget after the YAML schema change |
-| Auditor extended-thinking | Auditor returns PASS on phases that ship with bugs (audit gap data from real phases) |
-| Iteration-state synthesis | Goal-mode iterations show drift symptoms — repeated work, forgotten journeys, or loops that re-test fixed regressions |
-
-Without these signals, all three are speculative work — better spent on features.
+All pending framework improvements — including the former "Token Optimization — Pending Work" and "Pipeline Hardening — Pending Work" backlogs that used to live here — are maintained in one canonical file: [`docs/improvement-roadmap.md`](docs/improvement-roadmap.md). It holds ~50 specified items (problem, file:line anchors, change spec, definition of done, verification commands, rollback) written so any maintainer session can execute one at a time, plus the executor ground rules and the process for adding new items. Every absorbed item from the old sections is traceable in that file's §17 ledger (several were already shipped and are marked as such).
 
 ## Known Limitations
 
 1. **Service bootstrap**: QA expects `CHAIN_START_BACKEND_CMD` or `scripts/start-backend.sh`.
 2. **Claude Code only**: Hooks and agent definitions are Claude Code-specific.
 3. **Model tier costs**: Assumes access to Claude API with multiple model tiers.
-4. **No CI integration**: Pipeline is CLI-only. GitHub Actions integration is not included.
+4. **Pipeline is CLI-only**: Phase/goal runs don't execute in CI. GitHub Actions covers only the offline eval suite (`.github/workflows/evals.yml` — see Tests).
 5. **Chrome MCP optional for phase mode**: Browser checks require Chrome MCP. Without it, browser tests are skipped.
 6. **Chrome MCP required for goal mode**: The goal-evaluator anchors its `GOAL_ACHIEVED` decision on browser-qa journey results. Without Chrome MCP, browser tests are SKIPPED and the evaluator will likely emit `ESCALATE` indefinitely.
 
 ## Tests
 
 ```bash
+./scripts/automation/run-evals.sh         # full offline eval suite (<30s, no API credits)
 ./tests/automation/test-install-gate.sh   # supply-chain gate unit tests
 ./tests/automation/test-quota-retry.sh    # quota-retry unit tests
 ```
+
+### Eval guard: pre-commit hook + CI branch protection
+
+Two layers keep a red eval suite from landing on `main` (roadmap SAFE-1):
+
+- **Local (opt-in)** — install a pre-commit hook that runs the fast pure-python
+  eval subset (the `_run_self_test` registrations in `run-evals.sh`; well under
+  10s) and blocks the commit on any failure:
+
+  ```bash
+  bash scripts/automation/install-git-hooks.sh              # install (never installed automatically)
+  bash scripts/automation/install-git-hooks.sh --uninstall  # remove
+  ```
+
+  The hook is local-only (`.git/hooks/pre-commit`), is **never auto-installed**
+  by any pipeline script, and prints how to run the full suite. Emergency
+  bypass: `git commit --no-verify` — CI still gates the push.
+
+- **CI (recommended)** — `.github/workflows/evals.yml` (workflow
+  `harness-evals`) already runs the full suite on every push and PR to `main`.
+  To make it a hard gate, enable branch protection: GitHub → **Settings →
+  Branches → Add branch protection rule** → branch pattern `main` → check
+  **Require status checks to pass before merging** → search for and select
+  **`offline eval suite`** (the `harness-evals` job). From then on a red eval
+  suite blocks the merge instead of just reporting.
diff --git a/incredible_auto_dev/agents/goal-decomposer/agent.yaml b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
index 53d29e2..208cc54 100644
--- a/incredible_auto_dev/agents/goal-decomposer/agent.yaml
+++ b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.2.1
-last_updated: '2026-07-03'
+version: 1.3.0
+last_updated: '2026-07-07'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/body.md b/incredible_auto_dev/agents/goal-decomposer/body.md
index aa34545..785bda2 100644
--- a/incredible_auto_dev/agents/goal-decomposer/body.md
+++ b/incredible_auto_dev/agents/goal-decomposer/body.md
@@ -195,6 +195,7 @@ If any check fails, fix the spec before writing it — downstream agents execute
 - If `journey-history.json` shows zero remaining FAILING journeys, write a one-line spec saying "All journeys passing — evaluator should declare GOAL_ACHIEVED" and let the evaluator decide. Do NOT artificially manufacture more work.
 - Flag scope creep: if a journey requires capabilities outside `docs/goal.md` Key Capabilities, note it and exclude.
 - Apply lessons. When a `lessons.md` entry's **Applies to:** pattern matches what you're planning, surface the lesson in the iteration spec's BACKGROUND or NOTES section so the developer/reviewer/evaluator sees it. Repeating a documented past mistake is the opposite of episodic memory's purpose.
+- **Log interpretation calls to the assumption ledger.** When a spec decision required interpreting the goal — the goal/journey text is ambiguous about X and you chose reading Y — append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use; never rewrite prior entries), formatted exactly as: `## iter-<N> — goal-decomposer` on its own line, then `**Ambiguity:** <what the goal leaves open>`, `**We chose:** <the reading this iteration builds on>`, `**Reversible:** yes|no`, each on its own line. Signal only — zero entries is fine for most iterations; routine scoping picks are NOT assumptions (same discipline as lessons.md). Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
 - **Conform to the blueprint, and keep it current.** In `--next` mode, plan new pages into the existing Information Architecture and register every new displayed value in the Data Contract by editing `blueprint.md` directly. These *additive* edits — new value rows, a new page under an existing nav section — need no human approval. If you must change the **nav skeleton itself** (add/rename/remove a top-level section, or move a feature's canonical home), make the edit AND write a one-line reason to `runs/goal-session-<sid>/state/blueprint.reapproval-requested`. By default `run-goal.sh` auto-approves the change and continues; only with `--require-blueprint-approval` does it pause for the human to re-approve before the next iteration. Do this only when genuinely necessary — the IA is meant to hold across the whole session.
 - **Never duplicate a contract value.** If a journey needs a value already in the Data Contract, plan to read it from its registered canonical endpoint. Do not plan a second computation or a second endpoint for it — that is exactly the drift the coherence-auditor will FAIL.
 
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index d3b4b44..de5c4a3 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.2.1
-last_updated: '2026-07-03'
+version: 1.4.0
+last_updated: '2026-07-07'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index cf371ce..5a5e6da 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -22,11 +22,12 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 11. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
 12. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
 13. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
-14. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
+14. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
+15. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md`. The orchestrator script (`run-goal.sh`) pre-trims it and inlines the recent tail into your prompt — use the inlined content. The file grows unboundedly across a long session.
 
-When appending: use the Edit/Write tools to append to `evaluator-log.md` and `lessons.md` directly. Appending does not require reading the full file first — just append a new entry block.
+When appending: use the Edit/Write tools to append to `evaluator-log.md`, `lessons.md`, and `assumptions.md` directly. Appending does not require reading the full file first — just append a new entry block.
 
 The session id `<sid>`, iteration name `<iter-name>`, and iteration index `<N>` are passed as environment variables: `GOAL_SESSION_ID`, `GOAL_ITER_NAME`, `GOAL_ITER_INDEX`.
 
@@ -63,7 +64,8 @@ Write the updated state to `runs/goal-session-<sid>/state/journey-history.json`.
       "last_verified_iter": "<iter-name>",
       "last_passing_iter": "<iter-name or null>",
       "first_seen_iter": "<iter-name>",
-      "last_evidence_path": "reports/qa/<iter-name>-evidence/UT-01-signup.png"
+      "last_evidence_path": "reports/qa/<iter-name>-evidence/UT-01-signup.png",
+      "spec_hash": "<sha256 of this journey's goal.md block — see below>"
     },
     ...
   },
@@ -88,6 +90,10 @@ Statuses:
 - `regressed` — was passing in a prior iteration, now failing
 - `unknown` — not tested this iteration; carry over previous status
 
+**`spec_hash` — the goal-edit drift record.** Once per evaluation, run `python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md` (prints `{"J-NN": "<sha256>"}`). For every journey whose status you set from THIS iteration's evidence (`passing`, `failing`, `partial`, and baseline `already_passing`), record its current hash as `spec_hash`. For journeys you did not verify this iteration, carry the existing `spec_hash` forward unchanged — or leave it absent (pre-NEED-9 histories have none; never invent one). Never copy a new hash onto a journey you did not re-verify: the hash asserts "this status was verified against exactly this goal text", and the deterministic achievement gate audits it.
+
+**When `iter-<N>/journeys-changed.md` exists:** each listed journey's goal.md text changed AFTER its recorded pass, so that pass is void. If this iteration's evidence verifies the journey against the CURRENT text → `passing`, with the new `spec_hash`. Otherwise → `unknown`, gap noted ("goal text changed; not re-verified") — never carry the stale pass forward. The achievement gate refuses GOAL_ACHIEVED while any listed journey still carries an old-text pass.
+
 ### 4. Append to evaluator-log.md
 
 Append a new entry to `runs/goal-session-<sid>/state/evaluator-log.md`:
@@ -128,6 +134,22 @@ touching `apps/api/auth/`" or "rate-limiter / middleware changes" or "any iter
 adding a new public endpoint">
 ```
 
+### 5b. Append to assumptions.md (when scoring required an interpretation call)
+
+Append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use) whenever scoring this iteration required *interpreting* the goal rather than just reading evidence — e.g. you accepted a truncated email display as satisfying "shows the sender's email", or treated a journey's wording as covering a case it never names. These silent calls are what the human needs to see (and veto) early.
+
+**Skip this step entirely** when no such call was made — zero entries is the normal case; same signal-only discipline as lessons.md (step 5). Routine evidence reading is not an assumption. Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
+
+Format (append, never overwrite):
+
+```markdown
+## iter-<N> — goal-evaluator
+
+**Ambiguity:** <what the goal/journey text leaves open>
+**We chose:** <the interpretation your scoring used>
+**Reversible:** yes|no
+```
+
 ### 6. Write iteration verdict
 
 Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
@@ -176,7 +198,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 
 ### When to use each
 
-- **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, AND this iteration's `coherence.md` is not `COHERENCE-FAIL`. Loop halts with success.
+- **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, this iteration's `coherence.md` is not `COHERENCE-FAIL`, AND no journey listed in `journeys-changed.md` remains un-re-verified against the current goal text. Loop halts with success.
 
 - **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
 
@@ -201,6 +223,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Do NOT mark `GOAL_ACHIEVED` if any Must-have journey has status `failing` or `unknown`. All journeys must have positive evidence of passing.
 - Do NOT mark `GOAL_ACHIEVED` if any anti-goal violation is unresolved.
 - Do NOT mark `GOAL_ACHIEVED` if this iteration's `coherence.md` is `COHERENCE-FAIL`. A coherence failure is a structural veto — the product is incoherent (scattered navigation, a duplicate home, or the same value computed/served more than one way) even if all journeys pass. Drive a consolidation `CONTINUE` instead.
+- Do NOT mark `GOAL_ACHIEVED` if this iteration's `journeys-changed.md` lists any journey you did not re-verify against the current goal text this iteration — a pass earned on the old text is not a pass.
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
 - If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
diff --git a/incredible_auto_dev/agents/goal-proposer/agent.yaml b/incredible_auto_dev/agents/goal-proposer/agent.yaml
index 856e4c1..ca42cd3 100644
--- a/incredible_auto_dev/agents/goal-proposer/agent.yaml
+++ b/incredible_auto_dev/agents/goal-proposer/agent.yaml
@@ -13,6 +13,6 @@ tools_allowed:
 - Bash
 - Write
 - Edit
-version: 1.0.1
-last_updated: '2026-06-30'
+version: 1.1.0
+last_updated: '2026-07-08'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-proposer/body.md b/incredible_auto_dev/agents/goal-proposer/body.md
index ec63559..b96baad 100644
--- a/incredible_auto_dev/agents/goal-proposer/body.md
+++ b/incredible_auto_dev/agents/goal-proposer/body.md
@@ -36,24 +36,32 @@ The prompt gives you: the **session id**, the **session state dir** (`SESSION_DI
    the pre-screen snapshot / scan tool when one exists, then drill down with whatever analysis tools the
    guidance names, and look at the rest of the surface for UX/structure/missing-dimension gaps). Form a
    small shortlist of *useful* candidates by the project's lens — not single-metric outliers.
-2. **Keep only what survives the project's validation screen.** The guidance defines what counts as
+2. **Detect vision gaps.** Parse `docs/goal.md`'s **Vision** paragraph and **Key Capabilities** list;
+   compare each claim against ALL Must-have journeys (human AND the `<!-- AUTO:journeys -->` block).
+   List every claim no journey covers, and record each as a candidate tagged `kind: vision-gap` with
+   `robustness: speculative` (a coverage observation is never evidence-backed) — vision-gap candidates
+   join the shortlist and flow through the same screen/de-dup/backlog steps below. Name the uncovered
+   claims in `proposer-result.json`'s `summary` (also when you stop dry). A gap alone must NOT force an
+   extension — the honest-stop rule below still wins.
+3. **Keep only what survives the project's validation screen.** The guidance defines what counts as
    validated (for data products this is typically an out-of-sample hold-out; other products may define
    usage evidence or none). An evidence-backed candidate is proposable ONLY if the project's screen
    marks it a survivor. Tag each `robustness: robust` (screened survivor) or `speculative` (a
    structural/UX idea not yet evidence-backed). Never present a speculative candidate as proven.
-3. **De-duplicate.** Drop anything already in `enhancement-proposals.jsonl` or already a journey in
+4. **De-duplicate.** Drop anything already in `enhancement-proposals.jsonl` or already a journey in
    `goal.md` (human or AUTO).
-4. **Write the backlog.** Append the survivors best-first to `SESSION_DIR/enhancement-proposals.jsonl`
+5. **Write the backlog.** Append the survivors best-first to `SESSION_DIR/enhancement-proposals.jsonl`
    (one JSON object per line) in the schema the guidance defines.
-5. **Promote the top buildable proposal(s) into the goal.** For the best 1–2 proposals, append a new
+6. **Promote the top buildable proposal(s) into the goal.** For the best 1–2 proposals, append a new
    Must-have journey to the `<!-- AUTO:journeys -->` block in `docs/goal.md` — follow the
    **`goal-self-extension` skill** exactly (surgical marker-only Edit; pick the next free `J-NN`; never
    touch human journeys or the Anti-goals). Each journey's **Steps + Acceptance MUST bake in** the
    project's consistency rule (read the canonical endpoint / register any new shared value in the Data
    Contract) and the walkthrough requirement (a `[NEW]`-flagged demo-narrator walkthrough of the new
    surface). Keep journeys small (target 1, at most 2 per cycle) so each iteration stays focused.
-6. **Write the result file** `SESSION_DIR/proposer-result.json`:
+7. **Write the result file** `SESSION_DIR/proposer-result.json`:
    `{"extended": <bool>, "n_new_journeys": <int>, "n_proposals": <int>, "dry": <bool>, "summary": "<one line>"}`.
+   When step 2 found vision gaps, `summary` names the uncovered claims.
 
 ## The honest stop (the loop's boundary)
 
diff --git a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
index daa3f3f..883df49 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
+++ b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
@@ -8,6 +8,6 @@ model_tier: standard
 tools_allowed:
 - Read
 - Write
-version: 1.0.0
-last_updated: '2026-05-12'
+version: 1.1.0
+last_updated: '2026-07-07'
 body: body.md
diff --git a/incredible_auto_dev/agents/iteration-summarizer/body.md b/incredible_auto_dev/agents/iteration-summarizer/body.md
index a4abd4d..b687953 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/body.md
+++ b/incredible_auto_dev/agents/iteration-summarizer/body.md
@@ -46,6 +46,7 @@ The dispatch wrapper passes you a `phase-id` (e.g. `phase-7` or `goal-money-firs
 - `runs/goal-session-<sid>/iter-<N>/eval.md` — verdict, Journey Results table, Next-Step Recommendation
 - `runs/goal-session-<sid>/state/journey-history.json` — current state of every journey
 - The dispatch wrapper provides the last ~300 lines of `runs/goal-session-<sid>/state/evaluator-log.md` inline in the prompt — use the inline content, do not read the file directly.
+- The dispatch wrapper provides the recent tail of `runs/goal-session-<sid>/state/assumptions.md` (the assumption ledger, NEED-5) inline in the prompt — use the inline content, do not read the file directly. The placeholder "(no assumptions recorded yet)" means the ledger is empty.
 
 ## Iteration type detection
 
@@ -165,6 +166,16 @@ A short recommendation. Sources, in priority order:
 
 One short paragraph. Do not invent priorities. If the source says "halt — goal achieved", write that.
 
+## Assumptions made
+
+Required every iteration (both modes). Surfaces the interpretation calls other agents logged to the session assumption ledger so the product owner can veto a wrong reading early.
+
+Source: the inline assumption-ledger tail the dispatch wrapper passed in (goal mode). Ledger entries arrive as `## iter-<N> — <agent>` blocks with `**Ambiguity:**` / `**We chose:**` / `**Reversible:**` lines.
+
+- Rewrite each ledger entry as ONE plain bullet: `- iter-<N> · <agent> — Ambiguity: <…>. We chose: <…>. Reversible: <yes|no>`. Carry the fields verbatim (trim, don't re-judge). NEVER copy the ledger's `## iter-N` headings into the summary — an H2 inside this section breaks the renderer's section parsing.
+- Order entries newest-first. If the inline tail is long, keep all entries from THIS iteration plus the most recent ~10 older ones.
+- When the inline tail is the placeholder "(no assumptions recorded yet)", the wrapper passed no ledger content (phase mode), or no entries exist: write exactly `none recorded` as the section body — never omit the section.
+
 ## Quick verify
 
 Goal-full and phase iters only. If `what-to-click.md` exists and has Verification Steps, copy the numbered steps verbatim (just the action lines, not the per-step "Expect:" sub-bullets — those clutter the summary). Cap at 5 steps. Prefix the block with "From `reports/phase-<phase-id>-what-to-click.md`:".
diff --git a/incredible_auto_dev/commands/goal-init.md b/incredible_auto_dev/commands/goal-init.md
new file mode 100644
index 0000000..014d1d1
--- /dev/null
+++ b/incredible_auto_dev/commands/goal-init.md
@@ -0,0 +1,40 @@
+---
+description: Interview the user section-by-section to author or update docs/goal.md (the goal-mode product contract) — playback confirmation before any write, structural self-check after. The guided alternative to hand-editing templates/project-goal.md.
+allowed-tools: Bash(grep:*), Bash(diff:*), Bash(cat:*), Bash(ls:*), Bash(python3:*), Read, Write, Edit
+---
+You are the **goal-authoring interviewer**. Produce a high-quality `docs/goal.md` —
+the file that decides everything goal mode builds — by interviewing the user one
+topic at a time, playing back what you understood, and writing only after they
+explicitly confirm.
+
+First read `.claude/skills/goal-authoring.md` and follow it exactly: it holds the
+section-by-section interview script, the playback format, and the structural
+checklist. Do not improvise a different order and do not skip the playback.
+
+1. **Detect mode.** If `docs/goal.md` is absent — or exists but is still an unfilled
+   template copy (all `<...>` placeholders) — you are in **create mode**. Otherwise
+   you are in **update mode**: read the existing file first, summarize what each
+   section already says (one line each), and interview only about the parts the user
+   wants to change. Never silently overwrite an existing goal.
+2. **Interview** per the skill's script: one topic at a time, in the section order of
+   `templates/project-goal.md`, offering multiple-choice options where the skill
+   suggests them. Plain conversation only — assume no special tools or UI.
+3. **Play back** in the skill's playback format — one line per journey, anti-goals
+   verbatim; in update mode, show old → new for every section that would change —
+   and get an explicit "yes" BEFORE writing anything. On corrections, update and
+   re-play the changed lines.
+4. **Write.** Create mode: write the full `docs/goal.md` following the section
+   structure of `templates/project-goal.md`, every placeholder replaced by confirmed
+   content. Update mode: apply ONLY the confirmed changes as surgical edits; never
+   touch a `<!-- AUTO:journeys -->` … `<!-- /AUTO:journeys -->` block and never
+   reuse or renumber an existing `J-NN` id.
+5. **Self-check** (must pass before declaring success). If
+   `scripts/automation/lib/goal_lint.py` exists, run
+   `python3 scripts/automation/lib/goal_lint.py docs/goal.md`; otherwise apply the
+   skill's structural checklist (the `validate_goal_file` rules plus no leftover
+   `<...>` template placeholders). Fix any failure and re-check. Show the user the
+   passing result.
+6. **Stop.** Do not launch `run-goal.sh`, dispatch agents, or edit anything besides
+   `docs/goal.md`. Tell the user the next step:
+   `./scripts/automation/run-goal.sh --session-id <id>` (headless) or `/goal <id>`
+   (interactive).
diff --git a/incredible_auto_dev/commands/goal-lint.md b/incredible_auto_dev/commands/goal-lint.md
new file mode 100644
index 0000000..0e75514
--- /dev/null
+++ b/incredible_auto_dev/commands/goal-lint.md
@@ -0,0 +1,69 @@
+---
+description: Quality-lint docs/goal.md — deterministic linter plus an LLM semantic pass for what rules cannot catch (journey contradictions, unobservable acceptance, uncovered risky surfaces). Report-only — writes reports/goal-lint.md, NEVER edits goal.md.
+allowed-tools: Bash(python3:*), Bash(grep:*), Bash(cat:*), Bash(ls:*), Read, Write
+---
+You are the **goal linter**. Assess `docs/goal.md` (the goal-mode product contract)
+and write a findings report the user can act on. This command is **REPORT-ONLY**:
+the only file you may write is `reports/goal-lint.md`. You must NEVER edit
+`docs/goal.md` — journeys and anti-goals are ask-the-user-first class
+(`.claude/maintenance-protocol.md` §1). The user applies fixes themselves, by hand
+or via `/goal-init` (update mode); your job is to make every suggested rewrite
+paste-ready. Do not launch the engine, dispatch agents, or edit any other file.
+
+1. **Deterministic pass.** Run
+   `python3 scripts/automation/lib/goal_lint.py docs/goal.md` and show the user its
+   output verbatim (exit 0 + no output = structurally clean; 1 = warnings; 2 =
+   structural errors). If it reports the file unreadable or missing, stop and tell
+   the user to author one with `/goal-init` — there is nothing to lint.
+
+2. **Semantic pass.** Read `docs/goal.md` in full, plus the quality bars in
+   `.claude/skills/goal-authoring.md` (interview script items 3, 9, 10 and the
+   structural checklist). Judge MEANING, not keywords — you are looking for exactly
+   what the deterministic rules cannot see:
+   - **Journey contradictions** — two journeys whose steps or acceptance cannot both
+     hold (conflicting end states, one journey destroying state another asserts), or
+     the same value/metric named in different words across journeys without a
+     Product Shape canonical-value pin.
+   - **Unobservable acceptance phrased measurably** — an Acceptance line that passes
+     the vague-term filter yet no browser test could SEE on the page ("the data is
+     saved", "an email is sent", "the API returns 200"). Rewrite to the visible
+     surface: what text/element appears where.
+   - **Steps that require guessing** — a step with no concrete URL, visible label,
+     or input value, where a browser agent would have to invent one.
+   - **Not independently runnable** — a journey that silently depends on state a
+     prior journey created, with no setup step of its own from a fresh page load.
+   - **Risky surface with no anti-goal coverage** — journeys or Vision mention auth,
+     payments, uploads, personal data, or external network calls, and no anti-goal
+     bounds that surface.
+   - **Anti-goals that fool the keyword check** — a bullet containing a prohibition
+     word or number that is still not checkable ("must feel fast", "no bad UX").
+   - **Unmeasurable success criteria** — a Success Criteria bullet with no number
+     and no observable state.
+   Do not re-report a line the deterministic pass already flagged unless the
+   semantic problem is a different one.
+
+3. **Write the report** to `reports/goal-lint.md` (overwrite — it is a snapshot of
+   the latest run) in exactly this shape:
+
+   ```markdown
+   # goal-lint report — docs/goal.md
+
+   Run: <YYYY-MM-DD> · deterministic exit: <0|1|2> · semantic findings: <N>
+
+   ## Deterministic lint (goal_lint.py)
+   <verbatim tool output, or "clean (exit 0, no output)">
+
+   ## Semantic findings
+   ### <check name> — line <N>
+   > <the exact line quoted from docs/goal.md>
+   - **Problem:** <one sentence: why this will mislead the evaluator/browser-qa>
+   - **Suggested rewrite:** <concrete replacement text, paste-ready>
+   ```
+   Repeat the `###` block per finding; write `None.` under `## Semantic findings`
+   when the pass is clean. Close with a `## Summary` H2: 1-3 lines — overall
+   assessment plus the single highest-impact fix.
+
+4. **Show the user** the report path, the finding count, and the summary lines.
+   Remind them the report is advisory — nothing blocks the engine — and that fixes
+   go through `/goal-init` (update mode) or a hand edit of `docs/goal.md`, never
+   through this command.
diff --git a/incredible_auto_dev/commands/goal-status.md b/incredible_auto_dev/commands/goal-status.md
index 315a19c..f318de0 100644
--- a/incredible_auto_dev/commands/goal-status.md
+++ b/incredible_auto_dev/commands/goal-status.md
@@ -22,5 +22,8 @@ the engine, dispatch agents, or write anything.
    say so and point to `/goal-resume <sid>`. Also point the user at the full
    timestamped log: `tail -f runs/goal-session-<sid>/engine.log`.
 6. Summarize plainly whether the session is **running**, **paused** (and exactly
-   how to resume — e.g. review the blueprint then `/goal-resume`), **orphaned**
-   (dead engine PID — `/goal-resume`), or **finished** (and the final verdict).
+   how to resume — e.g. review the blueprint then `/goal-resume`; for
+   `AWAITING_INTENT_REVIEW` point at `runs/goal-session-<sid>/intent-review.md`,
+   the opt-in `--intent-checkpoint` "is this the product you wanted?" pause —
+   resuming acknowledges it), **orphaned** (dead engine PID — `/goal-resume`),
+   or **finished** (and the final verdict).
diff --git a/incredible_auto_dev/docs/goal-mode-interactive.md b/incredible_auto_dev/docs/goal-mode-interactive.md
index c9e5395..ee7511c 100644
--- a/incredible_auto_dev/docs/goal-mode-interactive.md
+++ b/incredible_auto_dev/docs/goal-mode-interactive.md
@@ -50,7 +50,7 @@ then writes the result back. The pump protocol lives in
 |---|---|
 | `/goal [session-id] [flags]` | Start (or create) a session and run **until the goal is achieved, blocked, halted, or paused by the existing rules**. No iteration cap by default — set an optional budget with e.g. `/goal my-app --max-iter 50`. |
 | `/goal-status [session-id]` | Read-only: current iteration, last verdict, pause/halt state, and whether a dispatch is in flight. Never launches the engine, never writes. |
-| `/goal-resume [session-id] [flags]` | Resume a paused/halted session (blueprint approval, GitHub auth, quota reset, or a closed session). Resuming a blueprint pause counts as approval; a `REGRESSION_HALT` needs `--acknowledge-regression`. Cleanly stops a still-running prior engine first (no double-engine). |
+| `/goal-resume [session-id] [flags]` | Resume a paused/halted session (blueprint approval, intent review, GitHub auth, quota reset, or a closed session). Resuming a blueprint pause counts as approval, and resuming an intent-checkpoint pause (`AWAITING_INTENT_REVIEW`, from `--intent-checkpoint`/`--intent-checkpoint-at`) counts as acknowledgment; a `REGRESSION_HALT` needs `--acknowledge-regression`. Cleanly stops a still-running prior engine first (no double-engine). |
 | `/goal-pause [session-id]` | Cleanly stop a running session's (detached) engine, leaving a resumable `ABORTED` checkpoint. Use after Ctrl+C to make changes, then `/goal-resume`. |
 | `/goal-step [session-id]` | Run exactly **one** more iteration, then stop. Reuses the engine's `--max-iter` cap (adds no new stop rule). |
 
@@ -142,7 +142,10 @@ programmatic path with an API key** (`run-goal.sh` without `--interactive`).
   liveness (via `engine.pid` + `kill -0`): a **dead PID with `status: in_progress`**
   means the engine was orphaned (e.g. a Ctrl+C that never reached it) — `/goal-resume`.
   If it shows `AWAITING_BLUEPRINT_APPROVAL` or `AWAITING_GITHUB_AUTH`, do the named
-  step and `/goal-resume`. If it shows `AWAITING_PUMP` (or a `dispatch/.awaiting-pump`
+  step and `/goal-resume`. If it shows `AWAITING_INTENT_REVIEW` (opt-in
+  `--intent-checkpoint` / `--intent-checkpoint-at`), read
+  `runs/goal-session-<sid>/intent-review.md`, edit `docs/goal.md` if the product
+  is drifting, then `/goal-resume` (resuming acknowledges the checkpoint). If it shows `AWAITING_PUMP` (or a `dispatch/.awaiting-pump`
   marker is present), the pump/session went away mid-iteration — re-open the session
   and `/goal-resume` to re-run that iteration cleanly.
 - **I pressed Ctrl+C and the run kept going / I want to pause** — Ctrl+C stops the
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index f844c34..a32b5dc 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -19,7 +19,11 @@ You can use both modes in the same project. They write to disjoint artifact name
 
 ### 1. Author `docs/goal.md`
 
-Start from `templates/project-goal.md` and fill in every section. The two sections required by goal mode (and ignored by phase mode) are:
+**Recommended:** run `/goal-init` inside Claude Code — it interviews you section-by-section and drafts `docs/goal.md` for you (playback confirmation before any write, structural self-check after).
+
+**Manual alternative:** start from `templates/project-goal.md` and fill in every section yourself.
+
+Either way, the two sections required by goal mode (and ignored by phase mode) are:
 
 ```markdown
 ## Must-have user journeys
@@ -99,6 +103,7 @@ Halt verdicts:
 - `STALLED` — no journey progress for `--stall-window` iterations; edit `goal.md` (clearer journeys, narrower scope) and `--resume`
 - `REGRESSION_HALT` — a previously-passing journey now fails; review, fix manually if needed, then resume with `--acknowledge-regression`
 - `AWAITING_BLUEPRINT_APPROVAL` — only when you ran with `--require-blueprint-approval`: paused after baseline (or after a structural blueprint change) for you to review `state/blueprint.md`; `--resume` to continue (counts as approval)
+- `AWAITING_INTENT_REVIEW` — only when you ran with `--intent-checkpoint` / `--intent-checkpoint-at N`: paused once mid-session for you to read `runs/goal-session-<sid>/intent-review.md` ("is this still the product you wanted?"); `--resume` to continue (counts as acknowledgment; fires once per session)
 - `AWAITING_GITHUB_AUTH` — paused at startup because per-iter push is on but a push to `origin` wouldn't authenticate (expired GitHub session, or no remote); fix auth (the run will offer to launch `gh auth login` for you when interactive) and `--resume`
 
 ## Common workflows
@@ -186,6 +191,20 @@ $EDITOR runs/goal-session-my-app/state/blueprint.md   # check IA + Data Contract
 
 `--require-blueprint-approval` is a per-run flag — pass it on each invocation/resume to keep the review pause on (it also pauses on any later structural blueprint change). `--auto-approve-blueprint` is still accepted but is now the default.
 
+### Mid-session intent checkpoint (opt-in)
+
+Goal mode normally runs hands-off from `goal.md` to `GOAL_ACHIEVED` — if the journeys encode the wrong product, you find out at the end. `--intent-checkpoint` adds one resumable mid-session pause: when **≥ 50% of the Must-have journeys pass**, the loop stops with `AWAITING_INTENT_REVIEW` and writes `runs/goal-session-<sid>/intent-review.md` — a deterministic packet (no model call) with the journey digest, the project story, the assumption-ledger tail, links to the HTML reports, and targeted questions (the still-failing journeys and any `Reversible: no` assumptions). Prefer an iteration count instead? `--intent-checkpoint-at N` fires when the loop reaches iteration N (same convention as `--max-iter`). Both are off by default and fire at most once per session:
+
+```bash
+./scripts/automation/run-goal.sh --session-id my-app --intent-checkpoint
+# ... loop pauses once half the journeys pass ...
+$EDITOR runs/goal-session-my-app/intent-review.md   # is this the product you wanted?
+# drifting? edit docs/goal.md (journeys / anti-goals) before resuming
+./scripts/automation/run-goal.sh --resume --session-id my-app   # resuming = acknowledged
+```
+
+Like the blueprint pause, these are per-run flags; the once-per-session memory lives in `state/.intent-review-done`, so a later resume never re-fires it.
+
 ### Start over
 
 ```bash
@@ -238,6 +257,29 @@ goal(my-app): iter 1 — CONTINUE (passing+1 failing+0 regressed+0)
 goal(my-app): iter 0 — CONTINUE (passing+0 failing+3 regressed+0)
 ```
 
+## Continuous improvement (opt-in)
+
+By default a session **finalizes** at `GOAL_ACHIEVED`. Opting in to continuous improvement changes that: once every Must-have journey passes, the **goal-proposer** agent surveys the finished product (via the read-only tools your guidance file names), detects vision gaps (Vision / Key Capabilities claims no journey covers), writes an improvement backlog to `runs/goal-session-<sid>/state/enhancement-proposals.jsonl`, and appends the best 1–2 proposals as new Must-have journeys inside the `<!-- AUTO:journeys -->` block of `docs/goal.md` — so the loop keeps building. When nothing worth building survives its validation screen, it reports a **dry** result and the session finalizes exactly as before (the honest stop — it never invents work to keep looping).
+
+The opt-in is two files, both outside the framework subtree. `run-goal.sh` dispatches the proposer only when BOTH exist:
+
+```bash
+# 1. The guidance file — every project-specific judgment the proposer uses.
+mkdir -p project-extensions/hooks
+cp templates/proposer-guidance.md project-extensions/proposer-guidance.md
+$EDITOR project-extensions/proposer-guidance.md   # fill in all six sections
+
+# 2. The post-goal hook — deterministic prep run before the proposer. A no-op is enough:
+cat > project-extensions/hooks/post-goal.sh <<'SH'
+#!/usr/bin/env bash
+exit 0
+SH
+```
+
+The hook is where a project refreshes a pre-screen snapshot for the proposer to read (e.g. write a `usage-scan.json` into the session state dir, and name that file in the guidance). It runs with `SESSION_ID`, `SESSION_DIR`, `REPO_ROOT`, and `GOAL_FILE` exported, is invoked via `bash` (no `chmod +x` needed), and is non-fatal — a failing hook logs a warning and the proposer still runs. If you have no prep step, the minimal no-op above is all you need.
+
+Each cycle writes `state/proposer-result.json` with the outcome (`extended` vs `dry`, plus a one-line summary naming any vision gaps found). The proposer edits **only** the `AUTO:journeys` block — human journeys and Anti-goals are never touched, and Anti-goals still bind every proposed journey. Every promoted journey bakes your consistency (Data Contract) and `[NEW]`-walkthrough requirements into its Acceptance, so the normal pipeline gates verify it like any other journey.
+
 ## Worked example: tiny goal
 
 Here's a minimal `goal.md` that demonstrates goal mode end-to-end:
@@ -301,6 +343,7 @@ Then:
 
 ## See also
 
+- `/goal-init` ([`commands/goal-init.md`](../commands/goal-init.md)) — guided interview that drafts `docs/goal.md` for you
 - [`templates/project-goal.md`](../templates/project-goal.md) — full goal template with all required sections
 - [`.claude/architecture/goal-mode.md`](../.claude/architecture/goal-mode.md) — internal architecture
 - [`docs/goal-mode-telemetry.md`](goal-mode-telemetry.md) — telemetry event schema
diff --git a/incredible_auto_dev/docs/improvement-roadmap.archive.md b/incredible_auto_dev/docs/improvement-roadmap.archive.md
new file mode 100644
index 0000000..4365dc5
--- /dev/null
+++ b/incredible_auto_dev/docs/improvement-roadmap.archive.md
@@ -0,0 +1,715 @@
+# Improvement roadmap — archive
+
+Full bodies of DONE items, moved out of `docs/improvement-roadmap.md` per its §2 step 8
+(growth rule): the active file keeps a one-line stub per archived item. Item format
+legend: active file §4.
+
+---
+
+### NEED-1 · `/goal-init` intake interview
+- **Priority:** P0 · **Effort:** M · **Risk:** LOW · **Status:** DONE (2026-07-07)
+- **Problem:** goal.md quality decides everything downstream, but adopters author it by
+  hand from a template with no guidance loop. Vague journeys → infinite review loops
+  (anti-pattern #1) and products that miss intent.
+- **Current state:** authoring guidance only in `templates/project-goal.md` comments and
+  `docs/goal-mode-quickstart.md`. The engine validates structure at start:
+  `validate_goal_file` at `scripts/automation/run-goal.sh:533-573` (called ~`:709`)
+  checks: file exists, `## Must-have user journeys` heading, `## Anti-goals` heading,
+  ≥1 `- **J-NN:` entry, ≥1 concrete non-placeholder anti-goal. Slash-command format:
+  see `commands/goal.md` / `commands/goal-status.md` (frontmatter + instruction body).
+- **Change spec:**
+  1. New `commands/goal-init.md`: interviews the user section-by-section in the order of
+     `templates/project-goal.md` (Vision → Target Users → Success Criteria → Key
+     Capabilities → Product Shape → Must-have journeys with J-NN IDs, numbered steps,
+     and an observable Acceptance line each → Anti-goals). One topic at a time;
+     multiple-choice options where sensible; conversational (no special tools assumed).
+  2. After the interview, play back "here is what I understood" — one line per journey
+     plus anti-goals verbatim — and get explicit confirmation BEFORE writing
+     `docs/goal.md`. If a goal.md already exists, offer update mode (show diff of what
+     would change) instead of overwrite.
+  3. Final self-check: the four `validate_goal_file` rules above + no leftover `<...>`
+     template placeholders. (Once NEED-3 ships, run `goal_lint.py` instead.)
+  4. New `skills/goal-authoring.md`: the interview script, playback format, and the
+     structural checklist — shared later by `/goal-lint` (NEED-4).
+- **DoD:** `/goal-init` in a scratch repo produces a goal.md that passes
+  `validate_goal_file`; playback-before-write and update-mode behavior are specified in
+  the command body; skill and command are mirrored into `.claude/`.
+- **Verify:** `python3 scripts/automation/sync-cli-assets.py --cli claude && ls
+  .claude/commands/goal-init.md .claude/skills/goal-authoring.md &&
+  ./scripts/automation/run-evals.sh`
+- **Files:** `commands/goal-init.md` (new), `skills/goal-authoring.md` (new),
+  mirrors via sync.
+- **Rollback:** delete the two new files + mirrors; nothing else references them.
+- **Note (2026-07-07):** implementation complete — `commands/goal-init.md` +
+  `skills/goal-authoring.md` written, mirrors rendered, Verify block + full eval
+  suite green (78 pass / 0 fail). Left IN-PROGRESS per G8 (Effort M, no
+  self-certification). Fresh-session verification remaining: run `/goal-init` in a
+  scratch repo, confirm the produced goal.md passes `validate_goal_file` and the
+  playback-before-write + update-mode behaviors match the command body, then flip
+  to DONE and archive per §2.8.
+- **Verified (2026-07-07, fresh session per G8):** DoD checked line by line.
+  Verify block re-run green — sync wrote 0 (mirrors drift-free), both mirror files
+  present, evals 78 pass / 0 fail. Scratch-repo test-drive (fresh git repo with the
+  rendered command/skill/template copied in): CREATE round produced a 3-journey
+  goal.md that passes the real `validate_goal_file` (function extracted verbatim
+  from `run-goal.sh`; harness red-green-tested first) with zero `<...>` placeholders;
+  transcript shows interview → playback → explicit "yes" → write, and both scripted
+  vague answers ("popular", "works properly") were pushed to observable per the
+  skill. UPDATE round on that goal.md (with an injected `AUTO:journeys` block holding
+  J-04): diff-shaped playback (old → new, unchanged by name), explicit "yes" before
+  edit, git diff exactly two surgical hunks, AUTO block and J-01..03 byte-identical
+  (md5-verified), new journey correctly assigned J-05, validator still passes.
+
+### NEED-2 · Quickstart names `/goal-init` first
+- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** DONE (2026-07-07)
+- **Problem:** even after NEED-1 ships, adopters following the quickstart will still
+  hand-author goal.md and never discover the interview.
+- **Current state:** `docs/goal-mode-quickstart.md` "4-step setup" (~line 18) says to
+  author goal.md manually from the template.
+- **Change spec:** setup step 1 becomes "run `/goal-init` inside Claude Code (interview →
+  drafted goal.md)"; manual authoring stays as the alternative path. Add `/goal-init` to
+  the quickstart's See-also list (~line 302).
+- **DoD:** quickstart names `/goal-init` before manual authoring.
+- **Verify:** `grep -n "goal-init" docs/goal-mode-quickstart.md` (≥2 hits).
+- **Files:** `docs/goal-mode-quickstart.md`.
+- **Rollback:** revert the doc edit.
+- **Verified (2026-07-07, self-certified per §2 step 7 — Effort S):** setup step 1 now
+  opens with "**Recommended:** run `/goal-init` inside Claude Code" (interview →
+  drafted goal.md) with manual template authoring kept as the explicit alternative
+  path; `/goal-init` added to See-also linking `commands/goal-init.md`. Verify block
+  green: grep shows 2 hits (step 1 + See-also); full eval suite 78 pass / 0 fail.
+
+### NEED-3 · Deterministic goal linter (`goal_lint.py`)
+- **Priority:** P0 · **Effort:** M · **Risk:** LOW · **Status:** DONE (2026-07-07)
+- **Problem:** `validate_goal_file` checks presence, not quality. Vague acceptance
+  criteria are the documented #1 failure mode and nothing catches them before a session
+  burns iterations on them.
+- **Current state:** structure checks only (`run-goal.sh:533-573`). Anti-goal bullet
+  parsing lives at `run-goal.sh:558-572`; journey-block regexes exist in
+  `scripts/automation/lib/goal_gate.py` (~`:158`, `_journey_blocks` /
+  `_JOURNEY_HEADER_RE`). Lib self-test convention: see `lib/checkpoint.sh` self-test
+  and `run-evals.sh` §2 registry.
+- **Change spec:**
+  1. New `scripts/automation/lib/goal_lint.py` (stdlib-only). Checks: duplicate J-NN
+     IDs; journey missing numbered steps or an `Acceptance` line; leftover `<...>`
+     template placeholders; vague words in Acceptance lines ("works well", "fast",
+     "properly", "intuitive", "user-friendly", "correctly"); anti-goals phrased as
+     aspirations with no checkable condition; empty Product Shape section while ≥2
+     journeys reference the same value/metric. Exit codes: 0 clean, 1 warnings,
+     2 structural errors. Subcommand `self-test` with fixtures for each rule.
+  2. Warn-only engine wiring: in `run-goal.sh` immediately after the
+     `validate_goal_file` call (~`:709`), behind `CHAIN_GOAL_LINT` (default `true`):
+     `python3 "$SCRIPT_DIR/lib/goal_lint.py" "$GOAL_FILE" || true` — print warnings,
+     NEVER block the engine (style must not gate execution).
+  3. Register in `run-evals.sh` §2: `goal_lint.py self-test`.
+- **DoD:** self-test green; engine start on a deliberately vague goal.md prints warnings
+  and proceeds; evals green.
+- **Verify:** `python3 scripts/automation/lib/goal_lint.py self-test && bash -n
+  scripts/automation/run-goal.sh && ./scripts/automation/run-evals.sh`
+- **Files:** `scripts/automation/lib/goal_lint.py` (new), `scripts/automation/run-goal.sh`
+  (2-3 lines), `scripts/automation/run-evals.sh` (1 line).
+- **Rollback:** remove the run-goal.sh call and the eval line; the lib is inert alone.
+- **Note (2026-07-07, implementer):** implemented per change spec; Verify block green
+  locally (self-test + `bash -n` + evals 79-pass), and a sandbox engine start on a
+  deliberately vague goal.md printed 6 warnings then proceeded to iteration 0
+  (`CHAIN_GOAL_LINT=false` control run printed none). Left IN-PROGRESS pending
+  fresh-session verification per G8.
+- **Verified (2026-07-07, fresh session per G8):** DoD checked line by line.
+  Verify block re-run green: `goal_lint.py self-test` passed, `bash -n run-goal.sh`
+  clean, evals 79 pass / 0 fail (self-test registered at `run-evals.sh:127`; fixtures
+  cover all six rules plus the 0/1/2 exit-code contract and negative cases). Wiring
+  confirmed at `run-goal.sh:709-713` — immediately after `validate_goal_file`, behind
+  `CHAIN_GOAL_LINT` default-true, `|| true`. Sandbox engine start (fresh framework
+  copy, dispatch pointed at a dead local endpoint so zero API tokens spent): a
+  deliberately vague goal.md printed 5 warnings (vague-acceptance ×2, placeholder,
+  aspirational-anti-goal, product-shape-empty — the last confirmed firing on a real
+  file, not just fixtures) then proceeded to Iteration 0 / Step 1 baseline-decomposer
+  dispatch; `CHAIN_GOAL_LINT=false` control run printed no lint output and proceeded
+  identically. Intake tie-in: `/goal-init` flow test-driven in a second scratch repo
+  (create-mode goal.md authored per `skills/goal-authoring.md`; interview
+  self-answered — no live user in the verifying session): produced file passes the
+  command's step-5 self-check (`goal_lint.py` exit 0, silent) and the real
+  `validate_goal_file` at engine startup (reached "Initializing new session" →
+  iteration 0 with no validation error).
+
+### NEED-4 · `/goal-lint` LLM semantic pass
+- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** DONE (2026-07-07)
+- **Problem:** deterministic rules can't catch contradictions between journeys,
+  unmeasurable acceptance phrased measurably, or risky surfaces (auth, payments,
+  uploads) with no anti-goal coverage.
+- **Current state:** no semantic review of goal.md exists anywhere.
+- **Change spec:** new `commands/goal-lint.md`: (1) run
+  `python3 scripts/automation/lib/goal_lint.py docs/goal.md` and show output; (2) apply
+  the semantic checklist from `skills/goal-authoring.md` (NEED-1); (3) write findings to
+  `reports/goal-lint.md` in the format: quoted line → problem → concrete suggested
+  rewrite. REPORT-ONLY — the command must never edit goal.md (it is user-approval class
+  per maintenance protocol §1).
+- **DoD:** command exists + mirrored; body forbids editing goal.md; running it on the
+  framework's own `docs/goal.md` produces a sane report.
+- **Verify:** `python3 scripts/automation/sync-cli-assets.py --cli claude --check`
+  after sync; manual run on `docs/goal.md`.
+- **Files:** `commands/goal-lint.md` (new) + mirror.
+- **Rollback:** delete the command + mirror.
+- **Depends on:** NEED-3 (uses the linter), NEED-1 (shares the skill checklist).
+- **Note (2026-07-07, implementer — Effort S, self-verified per §2.7):** command
+  authored with the seven-check semantic checklist (journey contradictions,
+  unobservable-but-measurably-phrased acceptance, guess-requiring steps,
+  non-independent journeys, uncovered risky surfaces, keyword-fooling anti-goals,
+  unmeasurable success criteria) drawn from `skills/goal-authoring.md` items 3/9/10
+  plus the NEED-4 problem statement; body forbids editing goal.md and restricts
+  writes to `reports/goal-lint.md` (allowed-tools has no Edit). Verify block green:
+  mirror synced, `--check` OK, evals 79 pass / 0 fail. Sanity run on the framework's
+  own meta `docs/goal.md` produced a sane `reports/goal-lint.md`: deterministic exit 2
+  (`no-journeys` — expected, the file is the documented replace-me meta goal) shown
+  verbatim, 2 semantic findings in the quoted-line → problem → paste-ready-rewrite
+  format (missing anti-goal coverage for the supply-chain surface; no measurable
+  success criterion), summary correctly identifies the file as documentation rather
+  than a runnable contract; `docs/goal.md` untouched by the run.
+
+### NEED-5 · Assumption ledger — writers
+- **Priority:** P0 · **Effort:** M · **Risk:** MED · **Status:** DONE (2026-07-07)
+- **Problem:** the decomposer and evaluator make silent interpretation calls ("the spec
+  is ambiguous about X, we chose Y") that the human never sees until the product is
+  wrong. Judgment-rubrics §3 only covers the extreme case (STALLED on conflicting
+  readings); everyday interpretation choices vanish.
+- **Current state:** no assumptions artifact exists. The proven pattern for append-only
+  session files is `lessons.md`: appended by the evaluator, pre-trimmed and inlined into
+  prompts via `_tail_or_placeholder` (`run-goal.sh:520-525`), never read whole.
+- **Change spec:**
+  1. New session file `runs/goal-session-<sid>/state/assumptions.md`, append-only.
+     Entry format: `## iter-<N> — <agent>` then `**Ambiguity:** …` / `**We chose:** …` /
+     `**Reversible:** yes|no`.
+  2. `agents/goal-decomposer/body.md`: add a rule (Rules section, ~`:189-199`) — when a
+     spec decision required interpreting the goal, append an entry; zero entries is fine
+     (signal only, no routine entries — same discipline as lessons).
+  3. `agents/goal-evaluator/body.md`: add step "5b" beside the lessons step
+     (~`:112-129`) — same, for scoring-time interpretations (e.g. "accepted truncated
+     email as 'shows email'").
+  4. Dispatch prompts: decomposer prompt block (`run-goal.sh:1241-1281`) and evaluator
+     "Prior session state" block (~`:1523-1526`) gain the ledger path (append-target)
+     plus an inlined tail via `_tail_or_placeholder`, exactly like `LESSONS_TAIL`.
+  5. Version-bump both touched `agent.yaml` files; resync mirrors.
+- **DoD:** rendered `.claude/agents/goal-{decomposer,evaluator}.md` contain the ledger
+  instructions; both dispatch prompts reference the path; an absent ledger renders as
+  placeholder text (no crash); evals green.
+- **Verify:** `python3 scripts/automation/sync-cli-assets.py --cli claude && grep -l
+  assumptions .claude/agents/goal-decomposer.md .claude/agents/goal-evaluator.md &&
+  bash -n scripts/automation/run-goal.sh && ./scripts/automation/run-evals.sh`
+- **Files:** `agents/goal-decomposer/body.md`, `agents/goal-evaluator/body.md`, both
+  `agent.yaml` (version bump), `scripts/automation/run-goal.sh`, mirrors.
+- **Rollback:** revert body edits + prompt lines; existing sessions' assumptions.md
+  files become inert.
+- **Stop-and-ask:** if the evaluator's prompt assembly has structurally changed from the
+  anchors (no `LESSONS_TAIL`-style inlining found), stop — the inline pattern is the
+  design, not an implementation detail.
+- **Note (2026-07-07):** implemented this session — writer rules in both agent bodies
+  (decomposer Rules bullet, evaluator step 5b), `ASSUMPTIONS_FILE` + `ASSUMPTIONS_TAIL`
+  wired into both dispatch prompts (tail recomputed fresh at the evaluator site), both
+  agent.yaml bumped to 1.3.0, mirrors resynced. Stop-and-ask checked: `LESSONS_TAIL`
+  inlining intact at implementation time. Verify block green (sync ok, grep found
+  ledger text in both rendered agents, `bash -n` ok, evals 79/79). Left IN-PROGRESS
+  per G8 — a FRESH session must verify and flip to DONE.
+- **Verified (2026-07-07, fresh session per G8):** DoD checked line by line.
+  (1) Ledger instructions present in both rendered agents — decomposer Rules bullet
+  (`.claude/agents/goal-decomposer.md:207`, exact entry format + signal-only
+  discipline), evaluator step 5b (`goal-evaluator.md:140-144`) plus the append-tooling
+  note (`:38`). (2) Both dispatch prompts carry `$ASSUMPTIONS_FILE` as append target
+  with an inlined `$ASSUMPTIONS_TAIL` (decomposer `run-goal.sh:1273/:1276`, evaluator
+  `:1544/:1553`; tails built at `:1226`/`:1498`, the evaluator site recomputed fresh so
+  same-iteration decomposer entries are visible; `ASSUMPTIONS_FILE` defined `:213`,
+  before both uses). (3) Absent-ledger behavior functionally tested — the function
+  extracted verbatim and run under `set -euo pipefail`: missing file → "(no assumptions
+  recorded yet)", empty file → placeholder, populated file → tail; no crash on any
+  path. (4) Verify block re-run verbatim green: sync wrote 0 (mirrors drift-free,
+  working tree clean before/after), grep matched both rendered agents, `bash -n` ok,
+  evals 79 pass / 0 fail. Both agent.yaml confirmed at 1.3.0; the NEED-5 commit
+  carries neutral source + mirrors together (G2). Cross-check per the verification
+  instructions: /goal-init CREATE round in a scratch repo (command/skill/template
+  copied in; `validate_goal_file` extracted verbatim and red-green-tested first —
+  three structurally bad files each fail with the matching specific error) produced a
+  3-journey goal.md that passes `validate_goal_file` with zero template placeholders;
+  `goal_lint.py` (itself red-tested: exit 2 `no-journeys` on a bad file) exits 0 on it.
+
+### NEED-6 · Assumption ledger — surfacing
+- **Priority:** P0 · **Effort:** M · **Risk:** MED · **Status:** DONE (2026-07-07)
+- **Problem:** a ledger nobody sees changes nothing. The human needs assumptions in the
+  iteration summary and HTML report so they can veto early (by editing goal.md — the
+  goal slice is rebuilt every iteration at `run-goal.sh:1221-1225`, so edits take effect
+  next iteration).
+- **Current state:** iteration-summarizer inputs are wired in `_run_iteration_summarizer`
+  (`run-goal.sh:244-277`, with `eval_log_inline`-style tail injection ~`:231-232`).
+  Summary template: `templates/iteration-summary.md`. The HTML renderer parses H2
+  sections generically via `_split_h2_sections`
+  (`scripts/automation/lib/render_iteration_summary.py:137-154`) and renders sections in
+  `render_html_iteration` (~`:1160-1165`); it skips absent sections.
+- **Change spec:**
+  1. `templates/iteration-summary.md`: new `## Assumptions made` H2 (after
+     `## Next step`).
+  2. `agents/iteration-summarizer/body.md`: add the assumptions tail to its inputs and
+     the new section to its output contract ("none recorded" when empty). Version-bump.
+  3. `_run_iteration_summarizer` wrapper: inline the assumptions tail like the evaluator
+     log tail.
+  4. Renderer: `_render_assumptions(data)` + insertion in `render_html_iteration`
+     (collapsed accordion, house style); extend the renderer's `self-test` with a
+     summary containing the new section AND one without it.
+- **DoD:** renderer self-test covers both cases; HTML shows the section when present,
+  nothing when absent; artifact-schema validation (if it checks section lists) updated;
+  evals green.
+- **Verify:** `python3 scripts/automation/lib/render_iteration_summary.py self-test &&
+  ./scripts/automation/run-evals.sh`
+- **Files:** `templates/iteration-summary.md`, `agents/iteration-summarizer/body.md` +
+  `agent.yaml`, `scripts/automation/run-goal.sh`,
+  `scripts/automation/lib/render_iteration_summary.py`, mirrors.
+- **Rollback:** revert; old summaries without the section keep rendering (renderer skips
+  absent sections).
+- **Stop-and-ask:** if `lib/artifact_schemas.py` hard-fails on unknown H2 sections
+  (check before adding the template section), coordinate the schema change in the same
+  commit or stop.
+- **Depends on:** NEED-5.
+- **Note (2026-07-07):** implemented this session. Stop-and-ask checked FIRST — code
+  read (`artifact_schemas.py:193-196` checks required-H2 presence only) AND empirically
+  validated (a summary with the new section passes `validate_path`), so no schema change
+  needed; `Assumptions made` deliberately NOT added to `required_h2` (old summaries must
+  keep validating). Template gains `## Assumptions made` after `## Next step` (one plain
+  bullet per ledger entry — the ledger's own `## iter-N` headings must never be copied
+  in, they'd fracture `_split_h2_sections`; "none recorded" when empty/phase mode).
+  Summarizer body: inline-tail input + authoring section; agent.yaml 1.0.0→1.1.0.
+  `_run_iteration_summarizer` inlines `_tail_or_placeholder "$ASSUMPTIONS_FILE" 200`
+  exactly like the evaluator-log tail. Renderer: `_render_assumptions` (collapsed
+  accordion, house style, bullets or plain "none recorded" text) inserted after
+  What's-left+Next-step; self-test covers WITH (goal fixture, bullet asserted in HTML)
+  and WITHOUT (phase fixture, accordion asserted absent). Verify block green: renderer
+  self-test pass, `bash -n` ok, sync --check ok, evals 79/79. Left IN-PROGRESS per
+  G8 — a FRESH session must verify and flip to DONE.
+- **Verified (2026-07-07, fresh session per G8):** DoD checked line by line.
+  (1) Self-test coverage confirmed in the code, not just by exit status: the goal
+  fixture carries the section (asserts exactly 1 extracted bullet, and both
+  "Assumptions made" + the bullet's text in the rendered HTML); the phase fixture
+  omits it (asserts "Assumptions made" absent from that HTML). Re-run fresh: pass,
+  exit 0. (2) Present/absent behavior re-proven independently of the self-test
+  fixtures — a synthetic summary run through `load_iteration` +
+  `render_html_iteration` three ways: WITH section → accordion with the bullet;
+  section stripped → no accordion at all; body `none recorded` → accordion renders
+  it affirmatively. (3) Schema: `artifact_schemas.py:193-196` checks required-H2
+  presence only (unknown sections cannot fail); iteration-summary `required_h2`
+  (`:111-118`) deliberately excludes "Assumptions made" so old summaries keep
+  validating; empirical `validate` CLI exit 0 on a section-carrying summary.
+  (4) Verify block re-run verbatim green: self-test pass, evals 79 pass / 0 fail.
+  Placement confirmed (template H2 order: … Next step, Assumptions made, Quick
+  verify, Artifacts); `ASSUMPTIONS_FILE` defined `run-goal.sh:213` before its `:241`
+  use; sync --check "would change 0" everywhere; agent.yaml at 1.1.0; commit 43159db
+  carries neutral source + mirrors together (G2). Cross-check per the verification
+  instructions: /goal-init drive in a scratch repo produced a 3-journey goal.md that
+  passes `goal_lint.py` (exit 0) and `validate_goal_file` extracted verbatim from
+  `run-goal.sh` (PASS; negative control: absent file rejected with the specific
+  error, exit 1).
+
+### NEED-9 · Goal-edit drift detection
+- **Priority:** P0 · **Effort:** M · **Risk:** MED · **Status:** DONE (2026-07-07)
+- **Problem:** the user may edit `docs/goal.md` mid-session (that's the intended veto
+  mechanism — the goal slice is rebuilt every iteration, `run-goal.sh:1221-1225`). But
+  if the edited journey was already `passing`, `journey-history.json` keeps certifying
+  it against the OLD text: a stale pass that can survive all the way into GOAL_ACHIEVED.
+- **Current state:** journey state lives in `runs/goal-session-<sid>/state/
+  journey-history.json` (rewritten by the evaluator each iteration); pre-eval snapshot
+  + deterministic artifacts are built at `run-goal.sh:1460-1475`; the achievement gate
+  (`scripts/automation/lib/goal-gates.sh:79-146`) requires every journey
+  passing/already_passing. No journey-text hashing exists anywhere.
+- **Change spec:**
+  1. `lib/goal_gate.py`: new subcommand `hash-journeys <goal.md>` — stable hash (e.g.
+     sha256 of normalized text) per `J-NN` block, JSON output. Reuse `_journey_blocks`.
+  2. Pre-eval artifact build (`run-goal.sh:1460-1475`): compare current hashes against
+     hashes recorded in journey-history (see step 4); for journeys whose recorded state
+     is passing/already_passing but whose hash changed, write
+     `iter-<N>/journeys-changed.md` listing them.
+  3. `agents/goal-evaluator/body.md` (+ methodology skill if it enumerates inputs): read
+     `journeys-changed.md` when present; listed journeys must be demoted to
+     needs-reverify (not counted as passing) until re-verified against the NEW text;
+     record new hashes when writing journey-history. Version-bump.
+  4. Journey-history schema: entries gain a `spec_hash` field (writer: evaluator;
+     tolerate absence for old sessions — treat missing hash as "unknown, no demotion").
+  5. Achievement gate (`goal-gates.sh:79-146`): refuse GOAL_ACHIEVED when
+     `journeys-changed.md` for the current iteration lists any journey not re-verified
+     this iteration. Add an eval fixture (changed-hash → gate demotes).
+- **DoD:** hash subcommand + self-test; changed-passing journey produces the note and
+  the gate demotion in the fixture; old journey-history files (no `spec_hash`) still
+  parse; evals green.
+- **Verify:** `python3 scripts/automation/lib/goal_gate.py self-test 2>/dev/null ||
+  python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md &&
+  bash -n scripts/automation/run-goal.sh && ./scripts/automation/run-evals.sh`
+- **Files:** `scripts/automation/lib/goal_gate.py`,
+  `scripts/automation/lib/goal-gates.sh`, `scripts/automation/run-goal.sh`,
+  `agents/goal-evaluator/body.md` + `agent.yaml`, `run-evals.sh` fixture, mirrors.
+- **Rollback:** stop writing `journeys-changed.md` (one call site); the schema field is
+  additive and tolerated-if-absent by design.
+- **Stop-and-ask:** if journey-history.json is written anywhere other than the evaluator
+  (grep first!), map every writer before adding the field — schema drift across writers
+  is exactly the bug class G3 exists for.
+- **Slices:** (a) hashing + change detection + pre-eval note; (b) evaluator body + gate
+  wiring + fixture.
+- **Note (2026-07-07):** slice (a) done, slice (b) pending. Writer census (stop-and-ask
+  fired; user approved proceeding): the evaluator is the sole writer of journey ENTRIES;
+  `run-goal.sh:760` only seeds the empty skeleton at session init;
+  `render_iteration_summary.py:2563/2682/2860` are temp-dir self-test fixtures. Safe for
+  slice (b) to add `spec_hash` with the evaluator as sole field writer. Interface built:
+  `goal_gate.py hash-journeys <goal.md>` bare → flat `{"J-NN": sha256}` (what the
+  evaluator should record); with `--history/--out-changed` run-goal.sh step 3c writes or
+  removes `iter-<N>/journeys-changed.md` (self-tested). Slice (b) should also add a
+  `runs/SCHEMA.md` entry for journeys-changed.md once it becomes an agent-consumed
+  contract (deliberately not documented there yet — siblings like
+  journey-history.pre.json aren't either). Known non-goal: a journey deleted from
+  goal.md while recorded passing has no current hash → unknown, not flagged (orphan
+  reconciliation stays evaluator/lint territory).
+- **Note (2026-07-07, session 2):** slice (b) done — both slices now implemented; item
+  stays IN-PROGRESS awaiting fresh-session verification (G8): re-run the Verify block,
+  then flip to DONE + archive per §2.8. What landed: evaluator contract (body.md step 3)
+  makes the evaluator record `spec_hash` per journey it verified this iteration (sole
+  writer; carry-over journeys keep their old value or stay absent) and voids the prior
+  pass of every journey listed in `iter-<N>/journeys-changed.md` — re-verify against the
+  CURRENT text or demote to `unknown` ("needs-reverify" maps to `unknown`: additive, no
+  new status value for readers to learn); methodology §A.1 bullet + evaluator dispatch
+  prompt line added; agent.yaml 1.3.0→1.4.0; mirrors resynced. Gate: new
+  `goal_gate.py drift <note> <history>` (parser lives beside the note's writer;
+  round-tripped in the self-test; fail-closed exit 2 on unparsable note/unreadable
+  history) wired as achievement-gate check 6 in `lib/goal-gates.sh` — a listed journey
+  still passing without a re-recorded hash demotes GOAL_ACHIEVED. Fixtures (run inside
+  run-evals.sh): changed-hash demotes / re-recorded hash certifies / absent note never
+  blocks (gate self-test), plus drift unit cases incl. old-history tolerance (python
+  self-test). `runs/SCHEMA.md` entry added per the session-1 note. Verified in-session:
+  both self-tests red→green, Verify block ok, evals 79/79.
+- **Verified (2026-07-07, fresh session per G8):** DoD checked line by line.
+  (1) Hash subcommand + self-test: `goal_gate.py self-test` fresh pass (exit 0);
+  `hash-journeys` exercised bare on the repo's own `docs/goal.md` (→ `{}`, correct:
+  the framework goal.md has no `J-NN` blocks) and on a real 3-journey file (three
+  64-hex sha256 values); formatting-invariance (trailing whitespace, CRLF) asserted
+  inside the self-test. (2) Fixture: `goal-gates.sh --self-test` 14/14 incl. the
+  three drift cases — the note is built by the REAL writer from a stale-hash history
+  (existence asserted), changed-hash journey demotes GOAL_ACHIEVED→CONTINUE with
+  `FAIL drift` recorded in gate-report.md, re-recorded spec_hash certifies, note
+  removed → stale hash alone never blocks. (3) Old-history tolerance asserted in the
+  python self-test: entry without `spec_hash` never flagged, missing history file →
+  no note, drift subcommand tolerates pre-NEED-9 histories, spec_hash-carrying
+  history still parses in `cmd_journeys`. (4) Evals green twice — standalone and
+  inside the verbatim Verify block — 79 pass / 0 fail each; `bash -n` ok. Wiring
+  re-confirmed at the anchors: gate check 6 `goal-gates.sh:145-158`; note builder
... [diff_bound] incredible_auto_dev/docs/improvement-roadmap.archive.md: 321 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
new file mode 100644
index 0000000..ea91623
--- /dev/null
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -0,0 +1,1280 @@
+# Improvement Roadmap — canonical backlog (single source of truth)
+
+**This file is the ONLY improvement backlog for this framework.** The README's former
+"Token Optimization — Pending Work" and "Pipeline Hardening — Pending Work" sections were
+absorbed here (see §17 ledger). If you find another TODO list, it is stale — merge it here.
+
+Written 2026-07-06 by the last Fable-5 planning session, after a full exploration of the
+codebase and a feasibility review of every P0 design. Line anchors reference commit
+`02aefc8`. **Anchors are strong hints, not gospel** — if an anchor is off by more than
+~30 lines, re-grep for the named function/pattern instead of trusting the number.
+
+---
+
+## 1. Purpose & audience
+
+- **Audience:** future maintainer sessions — interactive Claude Code sessions on
+  Opus 4.8 / Sonnet 5 (or whatever `config/model-tiers.yaml` says when you read this).
+  Items are written so you do NOT need to re-derive context: each one carries its own
+  problem statement, evidence anchors, change spec, definition of done, verification
+  commands, and rollback.
+- **Goal:** keep this framework improving — faster iterations, higher reliability, better
+  capture of what the user actually wants, stronger security, leaner tokens, clearer
+  reports and docs — even though the sessions doing the work are weaker than the one
+  that wrote this file. The gates and evals carry the judgment load; your job is to
+  execute one well-scoped item at a time and let the machinery check you.
+
+## 2. How to use this file
+
+1. Read §3 (ground rules) and §4 (item format) once per session. They are short.
+2. Pick ONE item, normally the first `TODO` item in §5's recommended order. Do not pick
+   two. Do not "also quickly fix" neighboring things.
+3. Set its `Status:` to `IN-PROGRESS` (this edit is autonomous-class; no approval needed).
+4. Read the item's anchors in the actual files before writing anything.
+5. Implement exactly the change spec. If reality contradicts the spec (anchor gone,
+   mechanism changed), STOP and ask the user — do not improvise a new design.
+6. Run the item's **Verify** block. All commands must pass.
+7. For Effort M/L items: verification must be done by a FRESH session (see §3). Leave the
+   item `IN-PROGRESS` with a note; the fresh session flips it to `DONE`.
+8. When `DONE`: move the item's body to `docs/improvement-roadmap.archive.md` (create it
+   if absent) leaving one line in place: `### <ID> — DONE <date>, archived`. This keeps
+   the active file lean (growth rule, §7 of EVO-1).
+9. New improvement ideas (yours, the user's, or retro output from EVO-2) go into §16
+   staging — never directly into a numbered section. The human promotes them (EVO-1).
+
+## 3. Ground rules for executors (non-negotiable)
+
+- **G1** Read `CLAUDE.md` and `.claude/maintenance-protocol.md` before any framework
+  edit. Protocol beats momentum. File-class permissions in protocol §1 apply — e.g.
+  `config/model-tiers.yaml` and gate defaults are ASK-THE-USER-FIRST class.
+- **G2** Edit neutral source (`agents/ skills/ commands/ hooks/ policy/ config/`),
+  NEVER the rendered `.claude/` mirrors. After any neutral-source edit:
+  `python3 scripts/automation/sync-cli-assets.py --cli claude`, commit source AND
+  mirrors together, and version-bump the touched `agent.yaml`.
+- **G3** `./scripts/automation/run-evals.sh` must be green after every item, before
+  commit. A new artifact contract (verdict line, table, JSON field, path) requires a
+  new eval fixture in the SAME change — grep for every reader of the artifact first
+  (writer→reader drift is the #1 documented bug class here).
+- **G4** Experiments ship behind a default-off env knob (`CHAIN_*`) with a named
+  tripwire metric. Never flip a default in the same change that introduces the knob.
+- **G5** Never disable gates (`CHAIN_GOAL_GATES`, `CHAIN_GOAL_CONFIRM`,
+  `CHAIN_MODEL_ESCALATION`, `CHAIN_DISABLE_MODEL_ROUTING`). If you must set an escape
+  hatch to debug, re-enable it in the same session and say so in your report.
+- **G6** One item per session. If an item won't fit, stop, split it in §16 staging with
+  a note, and ask the user. Do not improvise scope cuts.
+- **G7** Every MED/HIGH-risk item lists **Stop-and-ask** triggers. Hitting one means
+  literally stop and ask the user. "I found a workaround" is not an exemption.
+- **G8** Effort M/L items: final verification by a FRESH session — the implementer never
+  self-certifies (non-self-verification, `.claude/model-orchestration.md`). Baseline
+  before experiment: any SPEED/TOKEN experiment needs telemetry from at least one real
+  session (or an EVO-3 benchmark run) before AND after. Pre-register before running:
+  write the hypothesis + predicted metric movement into `benchmarks/experiments.md`
+  (EVO-3's ledger) BEFORE the measurement run; the writeup compares result vs
+  prediction — never rationalize after the fact.
+- **G9** Anything that spends real API tokens beyond your own session (benchmark runs,
+  test goal-sessions) → confirm with the user first, with a cost estimate.
+
+**Explicit do-NOTs** (absorbed from README Tier-3 — these were considered and rejected;
+do not resurrect them without new evidence):
+- **D1** Do not downgrade `qa` below Haiku — it drives Chrome MCP browser flows; if
+  browser checks regress, upgrade it to Sonnet, not down.
+- **D2** Do not merge ui-impact-analyst + ui-test-designer + ux-regression-reviewer —
+  each is an independent skeptical source the closure auditor depends on.
+- **D3** Do not eliminate retries — they exist for quality. Only the audit-failure
+  full-rerun cap (TOKEN-4) is sanctioned.
+- **D4** Do not lower a judge's effort to save tokens — lower the context you feed it.
+  The `JUDGE_AGENTS` guard in `scripts/automation/lib/agent_permissions.py` exists for
+  this; do not remove it.
+- **D5** Do not cap thinking/effort to cut cost — on ANY agent, not only judges (D4).
+  Superpowers 6 measured the failure mode: capping thinking increased turn count and
+  ~doubled output tokens (cost went UP, not down). Judges are hardcoded-refused
+  (`JUDGE_AGENTS`, `scripts/automation/lib/agent_permissions.py:262-264`); for
+  non-judges the `CHAIN_AGENT_EFFORT` knob stays opt-in and must carry a COST tripwire
+  (REL-8) — the current quality-only tripwire (`lib/analyze_telemetry.py:441-466`)
+  cannot see this failure mode.
+- **D6** Do not impose word/length budgets on specs or plans. If a spec must shrink,
+  cut implementation narrative — NEVER test scenarios or interface/data-contract
+  definitions (Superpowers 6: a plan word-budget cut test content −62%; tests and
+  interfaces are what carry implementation quality — see REL-9).
+- **D7** Do not dispatch a reviewer with diff-only context. The iteration spec and dev
+  handoff must accompany any diff packet (Superpowers 6: diff-only reviewers re-derived
+  requirements and produced confident but WRONG spec verdicts). Applies to TOKEN-7 and
+  any future review-packet work.
+
+## 4. Item format legend
+
+Every item carries: `ID` · `Priority` (P0/P1/P2) · `Effort` (S = part of a session,
+M = one full session, L = must be executed slice-by-slice, one slice per session) ·
+`Risk` (LOW/MED/HIGH) · `Status` (TODO / IN-PROGRESS / DONE / STALE / BLOCKED) ·
+**Problem** · **Current state** (with file:line anchors) · **Change spec** ·
+**DoD** (definition of done) · **Verify** (commands) · **Files** · **Rollback** ·
+**Stop-and-ask** (mandatory on MED/HIGH risk) · **Trigger** (experiments only: the
+signal that says "do this now").
+
+## 5. Recommended execution order (dependency-aware)
+
+1. **SAFE-1, SAFE-2, DOC-1, DOC-2** — cheap protection and drift fixes first.
+2. **REL-1** (judgment fixtures) — protects every later change against judge regressions.
+3. **NEED-1 → NEED-2** (intake), **NEED-3 → NEED-4** (linter), **NEED-5 → NEED-6**
+   (assumption ledger; 6 requires 5), **NEED-9**, **NEED-7** (checkpoint; better with 5
+   but works without), **NEED-8**.
+4. **EVO-2** (retro), **EVO-3** (benchmark; required before any SPEED/TOKEN experiment),
+   **EVO-4** (playbook), **EVO-5**. (EVO-1 ships with this file.)
+5. **SPEED-1 → SPEED-2 → SPEED-3** (strict order), **TOKEN-1…7** (TOKEN-2 requires
+   EVO-3 + REL-1 to exist; TOKEN-7 is independent of the SPEED chain).
+6. **REL-2…9, SEC-1…4, QUAL-1, REP-1…3, DOC-3…7** — as capacity allows; SEC-4 pairs
+   with SAFE-1; REL-8 must land before any real `CHAIN_AGENT_EFFORT` use; REL-9 is
+   cheap — do it early.
+7. **EXP-** items only with explicit human sign-off and a written design doc first.
+
+---
+
+## 6. P0 — User-need capture
+
+The chain's biggest structural gap: every agent is instructed "do not ask questions",
+`docs/goal.md` is treated as fixed ground truth, and nothing checks that the authored
+journeys actually capture what the user wants. These items add capture, linting,
+assumption transparency, and a mid-session human checkpoint — without breaking the
+hands-off engine (all human interaction happens either before the engine starts or at
+resumable pauses).
+
+### NEED-1 — DONE 2026-07-07, archived
+
+### NEED-2 — DONE 2026-07-07, archived
+
+### NEED-3 — DONE 2026-07-07, archived
+
+### NEED-4 — DONE 2026-07-07, archived
+
+### NEED-5 — DONE 2026-07-07, archived
+
+### NEED-6 — DONE 2026-07-07, archived
+
+### NEED-7 — DONE 2026-07-08, archived
+
+### NEED-8 — DONE 2026-07-08, archived
+
+### NEED-9 — DONE 2026-07-07, archived
+
+---
+
+## 7. P0 — Evolution engine
+
+What keeps improvement going after this initial backlog: where new items come from, how
+the system measures itself, and how it survives the next model change.
+
+### EVO-1 · Roadmap maintenance protocol  (SHIPS WITH THIS FILE — read, don't build)
+- **Priority:** P0 · **Effort:** — · **Risk:** — · **Status:** DONE (this section is it)
+- **Sources of new items** (in trust order):
+  1. §16 staging entries written by EVO-2 retros (automated, per terminal session halt).
+  2. The human's direct asks.
+  3. Telemetry anomalies (a step's wall/token cost trending up across sessions).
+  4. Session halts and their causes (`REGRESSION_HALT`, `ABORT_MALFORMED`, repeated
+     `ESCALATE`).
+  5. Recurring `lessons.md` / `evaluator-log.md` pain across projects (EVO-5).
+  6. Model/CLI releases (run EVO-4's playbook; new capabilities may unblock EXP items).
+- **Promotion rule:** only the HUMAN moves an item from §16 staging into a numbered
+  section (assigning ID, priority, effort). Sessions may draft the full mini-spec in
+  staging to make promotion easy.
+- **ID allocation:** next free number in the cluster; never reuse a retired ID.
+- **Growth control:** when an item is DONE, archive its body to
+  `docs/improvement-roadmap.archive.md` (leave a one-line stub). When §16 staging
+  exceeds ~15 entries, ask the human for a triage session.
+- **Stop rule** (absorbed from README): if a 30-iteration goal session costs less than
+  the user's stated budget and a phase costs less than their per-phase number, stop
+  optimizing tokens/speed — invest in features instead. Ask the user for their numbers
+  once and record them here: _(unset — ask when first relevant)_.
+- **Review cadence:** at the start of any framework-work session, skim §5 and §16;
+  if >8 weeks since the last edit of this file (`git log -1 --format=%cs -- docs/improvement-roadmap.md`),
+  tell the user it may be stale.
+
+### EVO-2 · Automatic post-session retrospective
+- **Priority:** P0 · **Effort:** L (2 slices) · **Risk:** MED · **Status:** TODO
+- **Problem:** every session generates evidence about what hurt (halts, quota pauses,
+  review-FAIL loops, wall-time spikes, lessons) — and none of it flows back into
+  framework improvements. The feedback loop is the evolution engine's core.
+- **Current state:** terminal halts are decided in the verdict/halt switch
+  (`run-goal.sh:1777-1919`); the showcase tail is the proven non-blocking pattern
+  (forked for CONTINUE, inline for halts, `run-goal.sh:1601-1612` / `:1770-1775`);
+  wall/token aggregation exists (`lib/analyze_telemetry.py`, `build_wall_report` ~`:273`,
+  JSON output supported); lessons tail inlining exists (`:520-525`).
+- **Change spec:**
+  1. **Slice (a) — deterministic collector + wiring.** New
+     `scripts/automation/lib/retro_collect.sh` (or `.py`): writes
+     `runs/goal-session-<sid>/state/retro-input.md` — halt reason + final verdict,
+     verdict sequence across iterations, per-agent wall/token stats
+     (`analyze_telemetry.py --json`), quota-pause count, attempt-1 review-FAIL count,
+     malformed-verdict count, lessons tail. Wire into the TERMINAL halt paths only
+     (GOAL_ACHIEVED / STALLED / REGRESSION_HALT / BUDGET_EXHAUSTED / ABORT_MALFORMED —
+     NOT resumable AWAITING_* pauses), non-blocking (`|| true`), behind
+     `CHAIN_SESSION_RETRO` (default `true`, escape hatch documented). Sandbox test
+     asserting it runs on STALLED and not on AWAITING_PUMP.
+  2. **Slice (b) — drafting agent.** Light-tier dispatch (reuse the
+     `_run_iteration_summarizer` wrapper pattern, `run-goal.sh:244-277`) reading ONLY
+     `retro-input.md`, writing `reports/goal-session-<sid>-retro.md`: 1-5 candidate
+     framework-improvement items in this file's §4 item format, each citing its
+     evidence line from retro-input. PROPOSALS ONLY — the agent never edits this
+     roadmap; the human copies candidates into §16. Neutral source: either a new
+     `agents/retro-analyst/` (agent.yaml `model_tier: light`) or a prompt template —
+     prefer the agent for consistency with the catalog. Non-blocking; failure never
+     blocks the halt.
+- **DoD:** terminal halt in a sandbox session produces both files; AWAITING_* pauses
+  produce neither; engine exit code unchanged when retro fails; evals green.
+- **Verify:** slice tests + `bash -n scripts/automation/run-goal.sh &&
+  ./scripts/automation/run-evals.sh`
+- **Files:** `scripts/automation/lib/retro_collect.sh` (new),
+  `scripts/automation/run-goal.sh`, `agents/retro-analyst/` (new, slice b),
+  `templates/retro.md` (new, slice b), mirrors, test.
+- **Rollback:** `CHAIN_SESSION_RETRO=false`; or remove the halt-path calls (isolated).
+- **Stop-and-ask:** if adding the retro-analyst agent requires touching the agent
+  catalog count in CLAUDE.md ("19 agents"), flag it — CLAUDE.md is ask-first class.
+
+### EVO-3 · Automated benchmark harness
+- **Priority:** P0 · **Effort:** L (3 slices) · **Risk:** MED · **Status:** TODO
+- **Problem:** "did my framework change help or hurt?" currently has no answer a weaker
+  maintainer can trust. The per-session tripwire compares within a session; nothing
+  compares across framework versions.
+- **Current state:** no `benchmarks/` dir. Headless engine is scriptable
+  (`run-goal.sh --session-id X --max-iter N`); telemetry JSON aggregation exists
+  (`analyze_telemetry.py`); `runs/` ships empty so any committed fixture results are
+  new territory.
+- **Change spec:**
+  1. **Slice (a) — fixture project.** `benchmarks/fixtures/todo-app/`: minimal runnable
+     scaffold (smallest stack the chain supports well — e.g. a single-page Express or
+     Flask app), a filled `.claude/project-template.md`, and a `docs/goal.md` with 2-3
+     small journeys + 2 anti-goals. Small enough that 2 lean iterations can plausibly
+     reach all-passing.
+  2. **Slice (b) — runner + metrics.** `scripts/automation/run-benchmark.sh`: copies
+     the fixture to a scratch dir, `git init`, runs
+     `run-goal.sh --session-id bench-<date> --max-iter 2` headless; on exit extracts
+     `benchmarks/results/<date>-<framework-sha>.json`: wall seconds, per-agent wall,
+     tokens in/out, est. cost, journeys passing after, iterations used, attempt-1
+     review-FAILs, final verdict. Refuses to run without `--yes-spend` (G9). Also
+     refuses to run without `--hypothesis '<one-line prediction>'`: before launching,
+     append a pre-registration entry to `benchmarks/experiments.md` (append-only
+     ledger: date · framework sha · hypothesis · metric(s) · predicted direction/size);
+     after the run, append result + `verdict-vs-prediction: CONFIRMED|REFUTED|MIXED`
+     to the same entry. Prediction BEFORE execution is the point (G8) — it catches
+     measurement errors and post-hoc rationalization (Superpowers 6 ran 25+
+     pre-registered experiments this way and credits it for catching bad measurements).
+  3. **Slice (c) — compare + baseline.** `scripts/automation/lib/benchmark_compare.py
+     <old.json> <new.json>`: delta table + verdict (REGRESS if wall or cost +>25% or
+     journeys-passing dropped; else OK). Docs section in this file + capture the first
+     baseline (one confirmed run).
+- **DoD:** one full benchmark run completes on the fixture; results JSON validates;
+  compare tool renders deltas; docs tell a weaker model exactly when to run it (before
+  AND after any SPEED/TOKEN experiment, and during EVO-4 cutovers); runner refuses
+  without a hypothesis; every recorded run has a ledger entry whose prediction
+  precedes its result.
+- **Verify:** `bash -n scripts/automation/run-benchmark.sh && python3
+  scripts/automation/lib/benchmark_compare.py --self-test &&
+  ./scripts/automation/run-evals.sh` + one confirmed real run.
+- **Files:** `benchmarks/fixtures/todo-app/**` (new),
+  `scripts/automation/run-benchmark.sh` (new),
+  `scripts/automation/lib/benchmark_compare.py` (new),
+  `benchmarks/experiments.md` (new, slice b), this file (baseline note).
+- **Rollback:** the harness is standalone; delete `benchmarks/` + the two scripts.
+- **Stop-and-ask:** EVERY benchmark run costs real API tokens (~the cost of up to 2 lean
+  iterations on a tiny app). Confirm with the user before each run — no exceptions.
+  NEVER wire this into CI.
+
+### EVO-4 · Model-cutover playbook
+- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** TODO
+- **Problem:** the Fable→Opus/Sonnet cutover was done once, by a strong model, with the
+  procedure living in its head and partially in the letter. The next cutover will be
+  done by a weaker model.
+- **Current state:** pieces exist in `.claude/letter-to-future-sessions.md` ("The model
+  table rots") and `.claude/maintenance-protocol.md` §6. No single runnable checklist.
+- **Change spec:** new `docs/model-cutover-playbook.md`, a strict ordered checklist:
+  1. Preflight every candidate id: `claude -p --model <id> 'reply OK'`.
+  2. Get explicit user approval (model spend = ask-first class), then flip
+     `config/model-tiers.yaml` — the ONE source; never per-agent `model_override`.
+  3. Resync mirrors + `sync-cli-assets.py --cli claude --check`.
+  4. Update the table in `.claude/model-orchestration.md` in the SAME commit.
+  5. `./scripts/automation/run-evals.sh` green.
+  6. Run REL-1 judgment fixtures (mark "pending REL-1" until it ships).
+  7. Run EVO-3 benchmark before/after (mark "pending EVO-3" until it ships).
+  8. First-session watchlist: `gate-report.md` appears on any GOAL_ACHIEVED;
+     `[escalation]` lines in the engine log; per-model rows in
+     `analyze_telemetry.py <session>/telemetry.jsonl`.
+  9. Append a dated note to the letter's deployment section.
+  Cross-link from the letter and from `.claude/maintenance-protocol.md` §6.
+- **DoD:** playbook exists with all 9 steps; letter + protocol link to it.
+- **Verify:** `grep -n "model-cutover-playbook" .claude/letter-to-future-sessions.md
+  .claude/maintenance-protocol.md docs/model-cutover-playbook.md`
+- **Files:** `docs/model-cutover-playbook.md` (new),
+  `.claude/letter-to-future-sessions.md` (1 line), `.claude/maintenance-protocol.md`
+  (1 line).
+- **Rollback:** docs-only.
+
+### EVO-5 · Cross-project lesson harvesting
+- **Priority:** P0 · **Effort:** M · **Risk:** LOW · **Status:** TODO
+- **Problem:** each adopting repo accumulates `lessons.md` / `evaluator-log.md` pain the
+  framework repo never learns from; anti-patterns.md only grows when someone remembers.
+- **Current state:** maintenance protocol §2 defines the lesson formats and where
+  framework lessons go (numbered anti-patterns entries: symptom → root cause →
+  checkable rule). No harvesting procedure or tooling.
+- **Change spec:**
+  1. New `scripts/automation/harvest-lessons.sh <repo-path>...`: for each repo, print
+     the tails of `runs/goal-session-*/state/lessons.md` and halt lines from
+     `session.json`s, grouped per repo — a digest for a human+session to review
+     (read-only; makes no judgments).
+  2. Procedure (documented in this file, here): quarterly or after each delivered
+     project, run the harvester over known adopting repos; for each recurring symptom,
+     draft either an anti-patterns entry (protocol §2 format) or a §16 staging item.
+- **DoD:** script handles missing dirs gracefully; procedure documented; one dry run on
+  this repo (no sessions → clean empty output).
+- **Verify:** `bash -n scripts/automation/harvest-lessons.sh &&
+  ./scripts/automation/harvest-lessons.sh . | head -20`
+- **Files:** `scripts/automation/harvest-lessons.sh` (new), this file.
+- **Rollback:** standalone script; delete it.
+
+---
+
+## 8. P1 — Self-modification safety
+
+Guards for the fact that the models editing this repo are now weaker than the one that
+built it. Do these first; they are cheap.
+
+### SAFE-1 — DONE 2026-07-08, archived
+
+### SAFE-2 — DONE 2026-07-08, archived
+
+---
+
+## 9. P1 — Speed & token efficiency
+
+Clean lean iteration ≈ 109 min (developer ~41m, reviewer ~21m, browser-qa ~20m,
+evaluator ~17m, decomposer ~8m — typicals from the timeout table comments,
+`scripts/automation/lib/agent_permissions.py:88-110`). Rule for ALL items here: EVO-3
+benchmark (or a real session's telemetry) before AND after (G8).
+
+### SPEED-1 · Refactor browser-qa into a function (no behavior change)
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** TODO
+- **Problem:** the browser-qa section of the lean executor is a ~290-line inline block;
+  SPEED-2 needs to run it in a forked subshell.
+- **Current state:** `scripts/automation/goal-iter-lean.sh:292-578` (two-lane logic:
+  deterministic golden replay lane `~:379-460`, LLM lane + merge `~:460-576`);
+  resume-skip guard `~:309-321`.
+- **Change spec:** extract into `run_browser_qa_section()` in the same file; keep the
+  resume-skip guard and `step_invalidate_from browser-qa` at the caller; byte-identical
+  sequential behavior.
+- **DoD:** existing checkpoint test green; no diff in any artifact path or verdict
+  behavior.
+- **Verify:** `bash -n scripts/automation/goal-iter-lean.sh &&
+  bash tests/automation/test-goal-checkpoints.sh && ./scripts/automation/run-evals.sh`
+- **Files:** `scripts/automation/goal-iter-lean.sh`.
+- **Rollback:** revert the commit (pure refactor).
+
+### SPEED-2 · Parallel review ∥ browser-qa — stage "replay"
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** TODO
+- **Problem:** reviewer (~21m) and browser-qa (~20m) both need only the post-dev tree
+  yet run sequentially — the single biggest safe parallelism left in the lean path.
+- **Current state:** sequence is developer → review-1 → (fix → review-2) → browser-qa
+  (`goal-iter-lean.sh:142-250` review loop; `step_invalidate_from developer-fix` on
+  FAIL at `~:217`). The coherence fork is the copyable pattern: fork `~:252-290`, join
+  `~:580-602`, reap in `cleanup_iter_servers` `~:90-107`. Feasibility verified: the
+  checkpoint canonical order (`lib/checkpoint.sh:40`) is an INVALIDATION order, not an
+  execution order — `step_invalidate_from developer-fix` already cascades deletion of
+  browser-qa/coherence/evaluator markers AND their registered artifacts
+  (`checkpoint.sh:188-225`), so an early-forked browser-qa result is auto-invalidated
+  on the FAIL path with zero checkpoint changes. Browser-qa writes land under `runs/`
+  + `reports/`, which are excluded from the tree hash (`checkpoint.sh:35`). Reviewer
+  only reads/diffs (`review_diff_hint`, `lib/common.sh:377-388`).
+- **Change spec:**
+  1. Knob `CHAIN_LEAN_PARALLEL_BROWSER_QA=off|replay|full`, default `off`.
+  2. In `replay` mode: after `step_mark_done developer` (`~:187`), fork service boot +
+     lane-1 deterministic replay ONLY (`demo_runner.py --mode verify` — pure python,
+     cleanly killable in both backends, no pump involvement) in a subshell copying the
+     coherence-fork pattern (isolate `CHAIN_CURRENT_AGENT`, rc-file, PID). Join after
+     review settles; feed `REPLAY_FAILED` into the LLM lane's target set exactly as the
+     sequential path does (`~:524`).
+  3. **On review-1 FAIL — ordering is CRITICAL:** kill the fork, `wait` for it to die,
+     THEN `step_invalidate_from developer-fix`, then re-run browser-qa sequentially
+     post-fix. Never let a forked write land after invalidation.
... [diff_bound] incredible_auto_dev/docs/improvement-roadmap.md: 886 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/reports/goal-lint.md b/incredible_auto_dev/reports/goal-lint.md
new file mode 100644
index 0000000..0d4ffe0
--- /dev/null
+++ b/incredible_auto_dev/reports/goal-lint.md
@@ -0,0 +1,42 @@
+# goal-lint report — docs/goal.md
+
+Run: 2026-07-07 · deterministic exit: 2 · semantic findings: 2
+
+## Deterministic lint (goal_lint.py)
+
+```
+[goal-lint] ERROR no-journeys: no '- **J-NN: ...**' journey blocks found — see templates/project-goal.md
+[goal-lint] docs/goal.md: 1 error(s), 0 warning(s) — advisory: lint never blocks the engine (CHAIN_GOAL_LINT=false to silence)
+```
+
+## Semantic findings
+
+### Risky surface with no anti-goal coverage — line 18
+> 4. Supply-chain security gates for all package installations
+- **Problem:** the file names security-sensitive surfaces (package installation here, "security controls" on line 11) but contains no `## Anti-goals` section at all, so if goal mode were ever run against this file the evaluator would have zero veto rules bounding installs, network calls, or secrets.
+- **Suggested rewrite:** add at the end of the file:
+
+  ```markdown
+  ## Anti-goals
+
+  - No package installation bypasses the supply-chain security gate.
+  - No secrets, API keys, or tokens committed to the repository.
+  - No paid external services invoked by the pipeline without explicit user approval.
+  ```
+
+### Unmeasurable success criteria — line 7
+> Provide a reusable, quality-gated, multi-agent development pipeline that automates phased software development using Claude AI agents.
+- **Problem:** the file has no `## Success Criteria` section and no other measurable outcome — "reusable" and "quality-gated" give the evaluator nothing observable to score against.
+- **Suggested rewrite:** add after `## Vision`:
+
+  ```markdown
+  ## Success Criteria
+
+  - `./scripts/automation/run-evals.sh` exits 0 (all offline evals pass) on every commit to main.
+  - A phase run on a template project completes all 11 steps and ends with an audit verdict of PASS.
+  - A goal-mode session on a template project reaches GOAL_ACHIEVED with every Must-have journey passing.
+  ```
+
+## Summary
+
+This `docs/goal.md` is intentionally meta: it describes the framework repository itself and tells adopting projects (lines 29-33) to replace it — it is documentation, not a runnable goal-mode contract, and `run-goal.sh` would abort on it at `validate_goal_file` (no journeys, no anti-goals). That is fine as long as nobody points goal mode at this repo. Highest-impact fix if goal mode should ever run here: author a real contract with `/goal-init` (journeys + anti-goals); otherwise the two rewrites above are optional hardening of the meta file.
diff --git a/incredible_auto_dev/runs/SCHEMA.md b/incredible_auto_dev/runs/SCHEMA.md
index 968eaa1..33752b6 100644
--- a/incredible_auto_dev/runs/SCHEMA.md
+++ b/incredible_auto_dev/runs/SCHEMA.md
@@ -153,6 +153,7 @@ Also included as a section inside `reports/qa/<phase>-qa.md` when `Frontend Pres
 | Cumulative project story (goal mode) | `runs/goal-session-<sid>/state/project-story.md` |
 | Coherence blueprint (goal mode) | `runs/goal-session-<sid>/state/blueprint.md` |
 | Coherence audit per iter (goal mode) | `runs/goal-session-<sid>/iter-<N>/coherence.md` |
+| Goal-edit drift note (goal mode) | `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` |
 | GOAL_ACHIEVED delivered wrap (MD) | `reports/goal-session-<sid>-delivered.md` |
 | GOAL_ACHIEVED delivered wrap (HTML) | `reports/goal-session-<sid>-delivered.html` |
 
@@ -358,6 +359,31 @@ treated as a non-blocking PASS. Template: `templates/coherence-verdict.md`.
 
 ---
 
+## Goal-edit drift note (goal mode only)
+
+### runs/goal-session-\<sid\>/iter-\<N\>/journeys-changed.md
+
+Written by `run-goal.sh` (pre-evaluator step 3c) via `goal_gate.py hash-journeys --history
+--out-changed`; the same call removes a stale note when nothing is flagged. Present ONLY when a
+journey recorded `passing`/`already_passing` in `state/journey-history.json` carries a `spec_hash`
+that no longer matches its current `docs/goal.md` block — i.e. the user edited the goal mid-session
+(the intended veto mechanism). One bullet per journey: id, name, recorded status, and
+`old → new` hash prefixes.
+
+Readers:
+- **goal-evaluator** — every listed journey's prior pass is void: re-verify it against the CURRENT
+  text this iteration (then record the new `spec_hash` in `journey-history.json`) or demote it to
+  `unknown`. `spec_hash` is written ONLY by the goal-evaluator, and only for journeys verified that
+  iteration.
+- **Achievement gate** (`lib/goal-gates.sh` check 6 → `goal_gate.py drift`) — refuses
+  `GOAL_ACHIEVED` while any listed journey still counts as passing without a re-recorded
+  `spec_hash`; fails closed on an unparsable note or unreadable history.
+
+Histories without `spec_hash` (pre-NEED-9 sessions) parse everywhere and are never demoted by this
+mechanism — a missing hash means "unknown", not "stale".
+
+---
+
 ## Delivered wrap (goal mode, GOAL_ACHIEVED only)
 
 When goal-evaluator returns `GOAL_ACHIEVED`, `run-goal.sh` triggers a
diff --git a/incredible_auto_dev/scripts/automation/install-git-hooks.sh b/incredible_auto_dev/scripts/automation/install-git-hooks.sh
new file mode 100644
index 0000000..95799fe
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/install-git-hooks.sh
@@ -0,0 +1,212 @@
+#!/usr/bin/env bash
+# install-git-hooks.sh — OPT-IN pre-commit eval guard (roadmap SAFE-1).
+#
+# Installs a .git/hooks/pre-commit that runs the fast pure-python eval subset
+# (every `_run_self_test` registration in scripts/automation/run-evals.sh;
+# ~0.5s today, target <10s) so a red eval cannot land in a commit unnoticed.
+#
+# OPT-IN by design: no pipeline script ever calls this — a human runs it once
+# per clone. The hook is a local convenience; CI (.github/workflows/evals.yml)
+# stays the authoritative gate. Bypass a blocked commit with
+# `git commit --no-verify` (CI will still catch a real failure).
+#
+# Usage:
+#   bash scripts/automation/install-git-hooks.sh              # install
+#   bash scripts/automation/install-git-hooks.sh --force      # replace a foreign pre-commit (backed up to pre-commit.bak)
+#   bash scripts/automation/install-git-hooks.sh --uninstall  # remove the guard hook
+#   bash scripts/automation/install-git-hooks.sh --self-test  # offline behavioral test in a scratch repo
+#
+# Rollback: --uninstall, or just delete .git/hooks/pre-commit (local-only file).
+set -euo pipefail
+
+MARKER="chain-eval-guard"   # identifies hooks written by this installer
+SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
+
+_log() { echo "[install-git-hooks] $*"; }
+
+# ── The hook body (quoted heredoc: expands at COMMIT time, not install time) ──
+_write_hook() {
+  local target="$1"
+  cat > "$target" <<'HOOK'
+#!/usr/bin/env bash
+# pre-commit eval guard — chain-eval-guard v1
+# Installed by scripts/automation/install-git-hooks.sh (roadmap SAFE-1).
+# Runs the fast pure-python eval subset: every `_run_self_test` registration
+# in scripts/automation/run-evals.sh. Blocks the commit if any fails.
+# Bypass ONCE (emergency only): git commit --no-verify   — CI still gates.
+set -uo pipefail
+
+repo_root="$(git rev-parse --show-toplevel)" || exit 1
+cd "$repo_root"
+evals="scripts/automation/run-evals.sh"
+
+_block() {
+  echo "✗ pre-commit eval guard: $1" >&2
+  echo "  Full suite:  ./scripts/automation/run-evals.sh --verbose" >&2
+  echo "  Bypass once: git commit --no-verify   (CI will still catch real failures)" >&2
+  echo "  Reinstall:   bash scripts/automation/install-git-hooks.sh --force" >&2
+  exit 1
+}
+
+[[ -f "$evals" ]] || _block "$evals not found — cannot determine the fast eval subset."
+command -v python3 >/dev/null 2>&1 || _block "python3 not found on PATH."
+
+# The subset is derived from run-evals.sh at commit time so it never drifts
+# from the suite. Zero matches means the registration format changed — fail
+# loud rather than silently passing forever.
+registrations="$(grep -E '^_run_self_test[[:space:]]' "$evals" || true)"
+[[ -n "$registrations" ]] || _block "no _run_self_test registrations found in $evals — hook out of date."
+
+total=0
+failed=0
+start=$SECONDS
+while read -r _ module arg; do
+  [[ -n "${module:-}" ]] || continue
+  total=$((total + 1))
+  if ! out="$(python3 "$module" "${arg:-self-test}" 2>&1)"; then
+    failed=$((failed + 1))
+    echo "✗ FAIL: python3 $module ${arg:-self-test}" >&2
+    echo "$out" | head -5 | sed 's/^/    /' >&2
+  fi
+done <<< "$registrations"
+
+if [[ "$failed" -gt 0 ]]; then
+  _block "$failed of $total fast self-tests failed — commit blocked."
+fi
+echo "pre-commit eval guard: $total pure-python self-tests passed in $((SECONDS - start))s (full suite: ./scripts/automation/run-evals.sh)"
+exit 0
+HOOK
+  chmod +x "$target"
+}
+
+# ── install / uninstall ──────────────────────────────────────────────────────
+_hook_path() {
+  git rev-parse --git-path hooks/pre-commit 2>/dev/null \
+    || { _log "ERROR: not inside a git repository."; exit 1; }
+}
+
+_install() {
+  local force="${1:-false}"
+  local hook; hook="$(_hook_path)"
+  mkdir -p "$(dirname "$hook")"
+
+  if [[ -f "$hook" ]] && ! grep -q "$MARKER" "$hook"; then
+    if [[ "$force" != "true" ]]; then
+      _log "ERROR: $hook exists and was not installed by this script."
+      _log "Re-run with --force to replace it (the old hook is backed up to pre-commit.bak)."
+      exit 1
+    fi
+    cp "$hook" "${hook}.bak"
+    _log "existing foreign hook backed up to ${hook}.bak"
+  fi
+
+  _write_hook "$hook"
+  _log "installed $hook"
+  _log "it runs the fast pure-python eval subset (<10s) before every commit."
+  _log "full suite: ./scripts/automation/run-evals.sh · bypass once: git commit --no-verify"
+
+  local hooks_path
+  hooks_path="$(git config --get core.hooksPath 2>/dev/null || true)"
+  if [[ -n "$hooks_path" ]]; then
+    _log "WARNING: core.hooksPath=$hooks_path is set — git will NOT run hooks from $(dirname "$hook")."
+  fi
+}
+
+_uninstall() {
+  local hook; hook="$(_hook_path)"
+  if [[ ! -f "$hook" ]]; then
+    _log "nothing to do: $hook does not exist."
+    return 0
+  fi
+  if ! grep -q "$MARKER" "$hook"; then
+    _log "ERROR: $hook was not installed by this script — refusing to delete it."
+    exit 1
+  fi
+  rm -f "$hook"
+  _log "removed $hook"
+}
+
+# ── self-test (offline, scratch repo; wired into run-evals.sh) ───────────────
+_self_test() {
+  local tmp; tmp="$(mktemp -d)"
+  # shellcheck disable=SC2064  — expand NOW: $tmp is a function local, gone when EXIT fires
+  trap "rm -rf '$tmp'" EXIT
+  # Isolate from user/system git config (gpg signing, core.hooksPath, ...).
+  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
+  local _fail=0
+  _assert() { # <label> <command...>
+    local label="$1"; shift
+    if "$@" >/dev/null 2>&1; then echo "  ok: $label"; else echo "  FAIL: $label" >&2; _fail=1; fi
+  }
+  _assert_not() {
+    local label="$1"; shift
+    if "$@" >/dev/null 2>&1; then echo "  FAIL: $label" >&2; _fail=1; else echo "  ok: $label"; fi
+  }
+
+  cd "$tmp"
+  git init -q repo && cd repo
+  git config user.email t@t && git config user.name t
+
+  # Minimal fake suite: two _run_self_test registrations over tiny fixtures.
+  mkdir -p scripts/automation/lib
+  printf 'import sys; sys.exit(0)\n' > scripts/automation/lib/ok.py
+  printf 'import sys; sys.exit(0)\n' > scripts/automation/lib/flaky.py
+  cat > scripts/automation/run-evals.sh <<'EOF'
+_run_self_test scripts/automation/lib/ok.py self-test
+_run_self_test scripts/automation/lib/flaky.py self-test
+EOF
+
+  # 1. install: hook exists, executable, carries the marker
+  _assert "install succeeds"            bash "$SCRIPT_PATH"
+  local hook=".git/hooks/pre-commit"
+  _assert "hook file exists"            test -f "$hook"
+  _assert "hook is executable"          test -x "$hook"
+  _assert "hook carries marker"         grep -q "$MARKER" "$hook"
+  _assert "reinstall is idempotent"     bash "$SCRIPT_PATH"
+
+  # 2. green path: commit passes when all self-tests pass
+  echo a > a.txt && git add a.txt
+  _assert "commit allowed when subset green" git commit -q -m ok
+
+  # 3. red path: a deliberately broken self-test blocks the commit
+  printf 'import sys; sys.exit(1)\n' > scripts/automation/lib/flaky.py
+  echo b > b.txt && git add b.txt
+  _assert_not "commit BLOCKED when a self-test is broken" git commit -q -m broken
+  _assert "blocked commit did not land"  test "$(git rev-list --count HEAD)" = "1"
+
+  # 4. restore: commit passes again
+  printf 'import sys; sys.exit(0)\n' > scripts/automation/lib/flaky.py
+  git add scripts/automation/lib/flaky.py
+  _assert "commit allowed after restore" git commit -q -m restored
+
+  # 5. fail-loud: missing run-evals.sh blocks (never silently passes)
+  mv scripts/automation/run-evals.sh scripts/automation/run-evals.sh.away
+  echo c > c.txt && git add c.txt
+  _assert_not "commit BLOCKED when run-evals.sh is missing" git commit -q -m no-suite
+  mv scripts/automation/run-evals.sh.away scripts/automation/run-evals.sh
+  git reset -q c.txt
+
+  # 6. foreign-hook safety: refuse without --force, replace+backup with it
+  printf '#!/bin/sh\nexit 0\n' > "$hook" && chmod +x "$hook"
+  _assert_not "install refuses to clobber a foreign hook" bash "$SCRIPT_PATH"
+  _assert "install --force replaces foreign hook"         bash "$SCRIPT_PATH" --force
+  _assert "foreign hook backed up"                        test -f "${hook}.bak"
+  _assert "replacement carries marker"                    grep -q "$MARKER" "$hook"
+
+  # 7. uninstall removes our hook; refuses a foreign one
+  _assert "uninstall removes the guard hook" bash "$SCRIPT_PATH" --uninstall
+  _assert "hook gone after uninstall"        test ! -f "$hook"
+  printf '#!/bin/sh\nexit 0\n' > "$hook" && chmod +x "$hook"
+  _assert_not "uninstall refuses a foreign hook" bash "$SCRIPT_PATH" --uninstall
+
+  if [[ "$_fail" -ne 0 ]]; then echo "self-test FAILED" >&2; exit 1; fi
+  echo "self-test passed"
+}
+
+case "${1:-}" in
+  --self-test) _self_test ;;
+  --uninstall) _uninstall ;;
+  --force)     _install true ;;
+  "")          _install false ;;
+  *) _log "ERROR: unknown option '$1' (expected --force, --uninstall or --self-test)"; exit 1 ;;
+esac
diff --git a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
index 6e4b444..d562432 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
+++ b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
@@ -15,8 +15,9 @@
 #     ② GOAL_ACHIEVED → deterministic achievement gate: every journey passing
 #       in journey-history.json, coherence not FAIL/stub, no FAIL cells in the
 #       browser results, no critical scan findings, no passing→failing
-#       regressions vs the pre-iteration snapshot. Any miss → demoted to
-#       CONTINUE with a written gate-report.md
+#       regressions vs the pre-iteration snapshot, no goal-edited journey
+#       still passing on its OLD text (journeys-changed.md drift check).
+#       Any miss → demoted to CONTINUE with a written gate-report.md
 #     ③ gates green → two-key confirm: ONE fresh-context adversarial
 #       evaluator dispatch (strong tier, max effort) must answer
 #       CONFIRM_ACHIEVED; anything else demotes to CONTINUE (fail-closed)
@@ -141,6 +142,22 @@ goal_gate_achievement() {
     failures=$((failures + 1))
   fi
 
+  # 6. Goal-edit drift (NEED-9): journeys flagged in journeys-changed.md
+  #    (goal.md text edited after they last passed) must have been re-verified
+  #    against the NEW text — spec_hash re-recorded by the evaluator — or
+  #    demoted out of passing. A stale pass must never certify.
+  if [[ -f "$iter_dir/journeys-changed.md" ]]; then
+    _rc=0; _out="$(python3 "$_GOAL_GATES_DIR/goal_gate.py" drift "$iter_dir/journeys-changed.md" "$history" 2>&1)" || _rc=$?
+    if [[ $_rc -eq 0 ]]; then
+      lines+=("- PASS drift: every goal-edited journey re-verified or demoted")
+    else
+      lines+=("- FAIL drift (rc=$_rc): ${_out//$'\n'/; }")
+      failures=$((failures + 1))
+    fi
+  else
+    lines+=("- PASS drift: no goal-edit drift note this iteration")
+  fi
+
   lines+=("" "**Gate result:** $([[ $failures -eq 0 ]] && echo PASS || echo "FAIL ($failures check(s) failed)")")
   printf '%s\n' "${lines[@]}" > "$report" 2>/dev/null || true
   [[ $failures -eq 0 ]]
@@ -374,6 +391,32 @@ _goal_gates_self_test() {
   v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_PASS" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
   [[ "$v" == "CONTINUE" ]] && echo "  PASS goal-gates: critical scan finding blocks certification" || { echo "  FAIL goal-gates: scan block (got '$v')"; fails=1; }
 
+  # 10. Goal-edit drift (NEED-9): the note is built by the REAL writer
+  #     (hash-journeys) from a stale-hash history. A flagged journey whose
+  #     spec_hash was never re-recorded blocks certification; re-recording
+  #     the current hash (= re-verified against the new text) certifies;
+  #     no note → a stale hash alone never blocks (pre-NEED-9 tolerance).
+  printf '# scan\n\n**Result:** CLEAN — nothing.\n' > "$d/iter-3/scan-report.md"
+  printf '# g\n\n- **J-01: A**\n  - Acceptance: freshly edited text\n- **J-02: B**\n  - Acceptance: unchanged\n' > "$d/goal-drift.md"
+  local ZERO64="0000000000000000000000000000000000000000000000000000000000000000"
+  local HIST_STALE="$d/hist-stale.json"
+  printf '{"journeys":{"J-01":{"status":"passing","name":"A","spec_hash":"%s"},"J-02":{"status":"already_passing","name":"B"}}}' "$ZERO64" > "$HIST_STALE"
+  python3 "$_GOAL_GATES_DIR/goal_gate.py" hash-journeys "$d/goal-drift.md" \
+    --history "$HIST_STALE" --out-changed "$d/iter-3/journeys-changed.md" >/dev/null 2>&1
+  [[ -f "$d/iter-3/journeys-changed.md" ]] || { echo "  FAIL goal-gates: drift fixture note not written"; fails=1; }
+  cp "$HIST_STALE" "$PRE"
+  v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_STALE" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
+  [[ "$v" == "CONTINUE" ]] && echo "  PASS goal-gates: changed-hash journey demotes GOAL_ACHIEVED" || { echo "  FAIL goal-gates: drift demote (got '$v')"; fails=1; }
+  grep -q "FAIL drift" "$d/iter-3/gate-report.md" || { echo "  FAIL goal-gates: gate-report missing drift failure"; fails=1; }
+  local _h01 HIST_REVERIFIED="$d/hist-reverified.json"
+  _h01="$(python3 "$_GOAL_GATES_DIR/goal_gate.py" hash-journeys "$d/goal-drift.md" 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["J-01"])')"
+  printf '{"journeys":{"J-01":{"status":"passing","name":"A","spec_hash":"%s"},"J-02":{"status":"already_passing","name":"B"}}}' "$_h01" > "$HIST_REVERIFIED"
+  v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_REVERIFIED" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
+  [[ "$v" == "GOAL_ACHIEVED" ]] && echo "  PASS goal-gates: re-verified journey (spec_hash re-recorded) certifies" || { echo "  FAIL goal-gates: drift re-verified (got '$v')"; fails=1; }
+  rm -f "$d/iter-3/journeys-changed.md"
+  v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_STALE" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
+  [[ "$v" == "GOAL_ACHIEVED" ]] && echo "  PASS goal-gates: no drift note → stale hash alone never blocks" || { echo "  FAIL goal-gates: drift absent-note (got '$v')"; fails=1; }
+
   unset -f claude_with_quota_retry
   rm -rf "$d"
   if [[ $fails -eq 0 ]]; then echo "goal-gates self-test: OK"; else echo "goal-gates self-test: FAILED"; fi
diff --git a/incredible_auto_dev/scripts/automation/lib/goal_gate.py b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
index d5d96ea..2da62d7 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
@@ -29,10 +29,33 @@ CLI:
         [--targets J-01,J-02] [--out <path>]
         stdout/out-file: goal.md with stable passing journeys' blocks replaced
         by one-line digests; vision/anti-goals/other prose verbatim.
+    python3 goal_gate.py hash-journeys <goal.md> [--history <journey-history.json>]
+        [--out-changed <path>]
+        stdout: {"J-01": "<sha256>", ...} — stable per-journey spec-text hash
+        (line endings and trailing whitespace normalized). With --history the
+        output becomes {"hashes": ..., "changed": [...]} where changed lists
+        passing/already_passing journeys whose recorded spec_hash no longer
+        matches the current text; --out-changed additionally writes (or, when
+        nothing changed, removes) a markdown note listing them. A missing
+        history file or a journey without spec_hash is UNKNOWN → never listed
+        (old sessions must not be demoted).
+        exit 0 (informational — changes are reported, not enforced here)
+        exit 2: goal.md unreadable
+    python3 goal_gate.py drift <journeys-changed.md> <journey-history.json>
+        The enforcement side of hash-journeys (achievement gate, NEED-9):
+        every journey listed in the note must have been re-verified against
+        the edited goal text — its recorded spec_hash re-recorded to the
+        note's current hash — or demoted out of passing/already_passing.
+        exit 0: no note file, or every listed journey re-verified/demoted
+        exit 1: a listed journey still counts as passing on the OLD text
+        exit 2: note present but unparsable, or history unreadable (a
+        certification path — fails CLOSED)
+        stdout: one line per unresolved journey
     python3 goal_gate.py self-test
 """
 from __future__ import annotations
 
+import hashlib
 import json
 import re
 import sys
@@ -177,6 +200,127 @@ def _journey_blocks(text: str) -> list[tuple[str, int, int]]:
     return blocks
 
 
+def _normalize_block(block: str) -> str:
+    """Line endings → \\n, per-line rstrip, trailing blank lines dropped — so
+    formatting-only edits to goal.md do not read as spec changes."""
+    lines = [ln.rstrip() for ln in block.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
+    while lines and lines[-1] == "":
+        lines.pop()
+    return "\n".join(lines)
+
+
+def _journey_hashes(text: str) -> dict[str, str]:
+    """sha256 hex of each journey block's normalized text, keyed by J-NN."""
+    return {
+        jid: hashlib.sha256(_normalize_block(text[start:end]).encode("utf-8")).hexdigest()
+        for jid, start, end in _journey_blocks(text)
+    }
+
+
+def cmd_hash_journeys(
+    goal_path: str,
+    history_path: str | None,
+    out_changed: str | None,
+) -> int:
+    try:
+        text = Path(goal_path).read_text(encoding="utf-8")
+    except OSError:
+        print(f"goal file unreadable: {goal_path}", file=sys.stderr)
+        return 2
+    hashes = _journey_hashes(text)
+    if history_path is None:
+        print(json.dumps(hashes, sort_keys=True))
+        return 0
+
+    changed: list[dict[str, str]] = []
+    data = _load_history(history_path)
+    if data is not None:
+        for jid in sorted(data["journeys"]):
+            j = data["journeys"][jid]
+            if not isinstance(j, dict) or j.get("status") not in PASSING_STATUSES:
+                continue
+            recorded, current = j.get("spec_hash"), hashes.get(jid)
+            if not recorded or not current:
+                # No recorded hash (pre-NEED-9 session) or journey block gone
+                # from goal.md: unknown, never a demotion signal.
+                continue
+            if recorded != current:
+                changed.append({
+                    "id": jid,
+                    "name": j.get("name", ""),
+                    "status": j.get("status", ""),
+                    "recorded_hash": recorded,
+                    "current_hash": current,
+                })
+    if out_changed:
+        note = Path(out_changed)
+        if changed:
+            lines = [
+                "<!-- Generated by goal_gate.py hash-journeys (goal-edit drift check).",
+                "     Each journey below is recorded as passing, but its goal.md spec",
+                "     text changed since it was last verified. It must be re-verified",
+                "     against the CURRENT text before it may count toward GOAL_ACHIEVED. -->",
+                "",
+                "# Passing journeys whose goal.md text changed",
+                "",
+            ]
+            lines += [
+                f"- {c['id']} ({c['name']}): status {c['status']}, "
+                f"spec_hash {c['recorded_hash'][:12]}… → {c['current_hash'][:12]}…"
+                for c in changed
+            ]
+            note.write_text("\n".join(lines) + "\n", encoding="utf-8")
+        else:
+            note.unlink(missing_ok=True)  # a stale note must not outlive the drift
+    print(json.dumps({"hashes": hashes, "changed": changed}, sort_keys=True))
+    return 0
+
+
+# One journey line of the note cmd_hash_journeys writes. Writer and parser
+# live in this file on purpose: the self-test round-trips them, so a format
+# change cannot silently disable the drift gate (it fails closed instead).
+_CHANGED_NOTE_LINE_RE = re.compile(
+    r"^-\s+(J-\d+)\s+\(.*\):\s*status\s+\S+,\s*"
+    r"spec_hash\s+[0-9a-f]+…\s*→\s*([0-9a-f]+)…\s*$",
+    re.MULTILINE,
+)
+
+
+def cmd_drift(note_path: str, history_path: str) -> int:
+    note = Path(note_path)
+    if not note.exists():
+        # No drift note this iteration — nothing to enforce.
+        return 0
+    try:
+        entries = _CHANGED_NOTE_LINE_RE.findall(note.read_text(encoding="utf-8"))
+    except OSError:
+        print(f"drift note unreadable: {note_path}", file=sys.stderr)
+        return 2
+    if not entries:
+        print(f"drift note has no parsable journey lines: {note_path}", file=sys.stderr)
+        return 2
+    data = _load_history(history_path)
+    if data is None:
+        print(f"journey history unreadable: {history_path}", file=sys.stderr)
+        return 2
+    unresolved: list[str] = []
+    for jid, current_prefix in entries:
+        j = data["journeys"].get(jid)
+        if not isinstance(j, dict):
+            unresolved.append(f"{jid}: listed as goal-edited but missing from journey-history")
+            continue
+        if j.get("status") not in PASSING_STATUSES:
+            continue  # demoted — the all-passing journeys check blocks achievement
+        if not str(j.get("spec_hash") or "").startswith(current_prefix):
+            unresolved.append(
+                f"{jid}: still {j.get('status')} but spec_hash was not re-recorded "
+                "against the edited goal text (stale pass)"
+            )
+    for line in sorted(unresolved):
+        print(line)
+    return 1 if unresolved else 0
+
+
 def cmd_goal_slice(
     goal_path: str,
     history_path: str,
@@ -325,6 +469,86 @@ def _self_test() -> int:
         assert out.read_text(encoding="utf-8") == goal.read_text(encoding="utf-8"), \
             "no history → full file fallback"
 
+        # hash-journeys: stable sha256 per J-NN block; --history/--out-changed
+        # flags passing journeys whose spec text changed since the recorded
+        # spec_hash. Missing history file / missing spec_hash = unknown → never
+        # flagged (NEED-9 tolerance: no demotion on absence).
+        goal_text = goal.read_text(encoding="utf-8")
+        h1 = _journey_hashes(goal_text)
+        assert set(h1) == {"J-01", "J-02", "J-03"}
+        assert all(re.fullmatch(r"[0-9a-f]{64}", v) for v in h1.values())
+        assert _journey_hashes(goal_text.replace("\n", " \n")) == h1, \
+            "hash must ignore trailing whitespace"
+        assert _journey_hashes(goal_text.replace("\n", "\r\n")) == h1, \
+            "hash must ignore line-ending style"
+        edited = _journey_hashes(goal_text.replace("csv downloads", "pdf downloads"))
+        assert edited["J-03"] != h1["J-03"], "hash must change when spec text changes"
+        assert edited["J-01"] == h1["J-01"], "other journeys' hashes must not change"
+
+        assert cmd_hash_journeys(str(goal), None, None) == 0
+        assert cmd_hash_journeys(str(d / "nope.md"), None, None) == 2
+        note = d / "journeys-changed.md"
+        hist_hash = d / "hist-hash.json"
+        hist_hash.write_text(json.dumps({"journeys": {
+            "J-01": {"status": "passing", "name": "Login", "spec_hash": "0" * 64},
+            "J-02": {"status": "failing", "name": "Browse", "spec_hash": "0" * 64},
+            "J-03": {"status": "already_passing", "name": "Export"},
+        }}), encoding="utf-8")
+        assert cmd_hash_journeys(str(goal), str(hist_hash), str(note)) == 0
+        note_text = note.read_text(encoding="utf-8")
+        assert "J-01" in note_text, "stale passing journey must be flagged"
+        assert "J-02" not in note_text, "non-passing journey must not be flagged"
+        assert "J-03" not in note_text, "missing spec_hash = unknown, no demotion"
+        hist_ok = d / "hist-ok.json"
+        hist_ok.write_text(json.dumps({"journeys": {
+            jid: {"status": "passing", "name": "x", "spec_hash": h}
+            for jid, h in h1.items()
+        }}), encoding="utf-8")
+        assert cmd_hash_journeys(str(goal), str(hist_ok), str(note)) == 0
+        assert not note.exists(), "no changes → stale note must be removed"
+        assert cmd_hash_journeys(str(goal), str(d / "missing.json"), str(note)) == 0
+        assert not note.exists(), "missing history = unknown → no note"
+
+        # drift: the achievement-gate side of NEED-9. Parses the note that
+        # cmd_hash_journeys itself wrote (writer↔parser round-trip lives in
+        # this one file) and fails unless every listed journey was re-verified
+        # against the edited text (spec_hash re-recorded) or demoted out of
+        # passing. Certification path → fail closed on anything unreadable.
+        assert cmd_drift(str(d / "no-note.md"), str(hist_hash)) == 0, \
+            "no note → nothing to enforce"
+        assert cmd_hash_journeys(str(goal), str(hist_hash), str(note)) == 0
+        assert note.exists(), "fixture: stale J-01 must be flagged again"
+        assert cmd_drift(str(note), str(hist_hash)) == 1, \
+            "listed journey still passing on the old hash → unresolved"
+        hist_reverified = d / "hist-reverified.json"
+        hist_reverified.write_text(json.dumps({"journeys": {
+            "J-01": {"status": "passing", "name": "Login", "spec_hash": h1["J-01"]},
+            "J-02": {"status": "failing", "name": "Browse", "spec_hash": "0" * 64},
+            "J-03": {"status": "already_passing", "name": "Export"},
+        }}), encoding="utf-8")
+        assert cmd_drift(str(note), str(hist_reverified)) == 0, \
+            "spec_hash re-recorded against the new text = re-verified"
+        hist_demoted = d / "hist-demoted.json"
+        hist_demoted.write_text(json.dumps({"journeys": {
+            "J-01": {"status": "unknown", "name": "Login", "spec_hash": "0" * 64},
+        }}), encoding="utf-8")
+        assert cmd_drift(str(note), str(hist_demoted)) == 0, \
+            "demoted out of passing = resolved (the all-passing gate blocks it)"
+        hist_gone = d / "hist-gone.json"
+        hist_gone.write_text('{"journeys": {}}', encoding="utf-8")
+        assert cmd_drift(str(note), str(hist_gone)) == 1, \
+            "listed journey missing from history → fail closed"
+        assert cmd_drift(str(note), str(d / "missing.json")) == 2, \
+            "note present but history unreadable → fail closed"
+        garbage = d / "garbage-note.md"
+        garbage.write_text(
+            "# Passing journeys whose goal.md text changed\n\nprose only\n",
+            encoding="utf-8")
+        assert cmd_drift(str(garbage), str(hist_hash)) == 2, \
+            "note with no parsable journey lines → fail closed (format drift)"
+        assert cmd_journeys(str(hist_ok)) == 0, \
+            "histories carrying spec_hash must parse everywhere"
+
     print("self-test passed")
     return 0
 
@@ -364,6 +588,21 @@ def main(argv: list[str]) -> int:
             else:
                 i += 1
         return cmd_goal_slice(goal_path, history, targets, out_path)
+    if cmd == "hash-journeys" and args:
+        history_p: str | None = None
+        out_changed: str | None = None
+        rest = args[1:]
+        i = 0
+        while i < len(rest):
+            if rest[i] == "--history" and i + 1 < len(rest):
+                history_p = rest[i + 1]; i += 2
+            elif rest[i] == "--out-changed" and i + 1 < len(rest):
+                out_changed = rest[i + 1]; i += 2
+            else:
+                i += 1
+        return cmd_hash_journeys(args[0], history_p, out_changed)
+    if cmd == "drift" and len(args) >= 2:
+        return cmd_drift(args[0], args[1])
     if cmd == "self-test":
         return _self_test()
     print(f"unknown command: {cmd}", file=sys.stderr)
diff --git a/incredible_auto_dev/scripts/automation/lib/goal_lint.py b/incredible_auto_dev/scripts/automation/lib/goal_lint.py
new file mode 100644
index 0000000..3b6cbbd
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/goal_lint.py
@@ -0,0 +1,536 @@
+"""
+goal_lint.py — deterministic goal.md quality linter (stdlib only).
+
+`validate_goal_file` (run-goal.sh) hard-fails on missing STRUCTURE; this
+linter flags QUALITY problems that predict wasted iterations (vague
+acceptance criteria are the documented #1 failure mode). It is ADVISORY:
+run-goal.sh prints its output behind CHAIN_GOAL_LINT (default true) and
+always proceeds (`|| true`) — style must never gate execution. The
+/goal-lint command (NEED-4) reuses it against drafts.
+
+Journey blocks are parsed with goal_gate's regexes (imported — one source
+of truth, per the writer/reader-drift rule).
+
+Rules — errors (exit 2) are broken machine contracts, warnings (exit 1)
+are quality signals:
+    ERROR duplicate-id       two journey headers share one J-NN id
+                             (journey-history.json is keyed by id)
+    ERROR no-journeys        no `- **J-NN` journey blocks found at all
+    WARN  journey-shape      journey missing numbered steps (1., 2., ...)
+                             or an `Acceptance:` line
+    WARN  placeholder        leftover `<...>` template placeholder outside
+                             HTML comments / code spans / autolink URLs
+    WARN  vague-acceptance   Acceptance line uses a vague term: "works
+                             well", "fast", "properly", "intuitive",
+                             "user-friendly", "correctly"
+    WARN  aspirational-anti-goal  anti-goal bullet with no checkable
+                             condition (no prohibition keyword, comparator,
+                             or number — an aspiration, not a veto rule)
+    WARN  product-shape-empty  >=2 journeys' Acceptance lines share a
+                             value/metric phrase (stopword-free adjacent
+                             word pair) but the Product Shape section is
+                             absent or has no concrete content (an explicit
+                             "none" counts as concrete)
+
+Exit codes: 0 clean, 1 warnings only, 2 structural errors (including
+unreadable file). Output: one line per finding + a summary; silent when
+clean.
+
+CLI:
+    python3 goal_lint.py <goal.md>
+    python3 goal_lint.py self-test
+"""
+from __future__ import annotations
+
+import re
+import sys
+from collections import namedtuple
+from pathlib import Path
+
+from goal_gate import _journey_blocks
+
+Finding = namedtuple("Finding", "severity rule line message")  # line: int|None
+
+_NUMBERED_STEP_RE = re.compile(r"^\s*\d+[.)]\s", re.MULTILINE)
+_ACCEPTANCE_RE = re.compile(
+    r"^\s*(?:[-*]\s*)?(?:\*\*)?Acceptance(?:\*\*)?\s*:", re.IGNORECASE | re.MULTILINE
+)
+# Template placeholders look like "<observable end state>"; HTML comments and
+# code spans are blanked before this runs, autolinks are excluded here.
+_PLACEHOLDER_RE = re.compile(r"<(?!https?://|mailto:)[A-Za-z][^<>\n]*>")
+# Exactly the spec's vague-term list (NEED-3) — do not grow it casually.
+_VAGUE_RE = re.compile(
+    r"\b(works\s+well|user[\s-]friendly|fast|properly|intuitive|correctly)\b",
+    re.IGNORECASE,
+)
+# An anti-goal is "checkable" if it prohibits or bounds something: a
+# prohibition keyword, a comparator, or a number. Anything else reads as an
+# aspiration the evaluator cannot veto on.
+_CHECKABLE_RE = re.compile(
+    r"\b(no|not|never|none|must|avoid|only|without|disallow(?:ed)?|"
+    r"forbid(?:den)?|ban(?:ned)?|excluded?|reject(?:ed)?|refused?|"
+    r"skip(?:ped)?|deny|denied|prevent(?:ed)?|block(?:ed)?)\b|\d|[<>≤≥=%]",
+    re.IGNORECASE,
+)
+_ANTI_GOALS_HEAD_RE = re.compile(r"^##\s+Anti-goals\s*$", re.IGNORECASE)
+_PRODUCT_SHAPE_HEAD_RE = re.compile(r"^##\s+Product Shape\s*$", re.IGNORECASE)
+_H2_RE = re.compile(r"^##\s")
+
+# Words too generic to name a value/metric: articles/prepositions/verbs plus
+# UI-navigation vocabulary. Used only by the product-shape heuristic.
+_STOPWORDS = frozenset("""
+the a an and or of to in on for with is are be at as by it its this that from
+into after before then when than there here each every all any some same new
+their his her our your user users page pages screen button buttons form forms
+click clicks clicking shows show showing displays display displaying displayed
+see sees seeing expect expects expected visible appears appear appearing
+renders rendered render contains contain containing reads read gains gain
+moves move without within via using use should must can will browser app site
+tab tabs open opens load loads loaded still now again
+""".split())
+
+
+def _stripped_lines(text: str) -> list[str]:
+    """The file's lines with fenced code blocks, inline code spans, and HTML
+    comments blanked out. Line count is preserved, so index+1 = line number."""
+    out: list[str] = []
+    in_fence = False
+    in_comment = False
+    for raw in text.splitlines():
+        if in_fence:
+            if raw.lstrip().startswith("```"):
+                in_fence = False
+            out.append("")
+            continue
+        if not in_comment and raw.lstrip().startswith("```"):
+            in_fence = True
+            out.append("")
+            continue
+        parts: list[str] = []
+        j = 0
+        while j < len(raw):
+            if in_comment:
+                end = raw.find("-->", j)
+                if end == -1:
+                    j = len(raw)
+                else:
+                    in_comment = False
+                    j = end + 3
+            else:
+                start = raw.find("<!--", j)
+                if start == -1:
+                    parts.append(raw[j:])
+                    break
+                parts.append(raw[j:start])
+                in_comment = True
+                j = start + 4
+        out.append(re.sub(r"`[^`]*`", "", "".join(parts)))
+    return out
+
+
+def _acceptance_bigrams(block: str) -> set[str]:
+    """Adjacent non-stopword word pairs from a journey block's Acceptance
+    line(s) — a deterministic proxy for 'this journey references a named
+    value/metric' (e.g. "unread count", "total return")."""
+    grams: set[str] = set()
+    for line in block.splitlines():
+        m = _ACCEPTANCE_RE.match(line)
+        if not m:
+            continue
+        toks = [
+            t[:-2] if t.endswith("'s") else t
+            for t in re.findall(r"[a-z][a-z'\-]*", line[m.end():].lower())
+        ]
+        for a, b in zip(toks, toks[1:]):
+            if len(a) > 2 and len(b) > 2 and a not in _STOPWORDS and b not in _STOPWORDS:
+                grams.add(f"{a} {b}")
+    return grams
+
+
+def lint_text(text: str) -> list[Finding]:
+    findings: list[Finding] = []
+    lines = _stripped_lines(text)
+
+    blocks = _journey_blocks(text)
+    if not blocks:
+        return [Finding(
+            "ERROR", "no-journeys", None,
+            "no '- **J-NN: ...**' journey blocks found — see templates/project-goal.md",
+        )]
+
+    def _line_of(char_pos: int) -> int:
+        # _JOURNEY_HEADER_RE's leading ^(\s*) may swallow the blank line before
+        # the header; advance to the first non-whitespace char (the "-") first.
+        while char_pos < len(text) and text[char_pos] in " \t\r\n":
+            char_pos += 1
+        return text.count("\n", 0, char_pos) + 1
+
+    # duplicate-id (ERROR): journey-history.json and the goal slice key on the id,
+    # so a duplicate silently merges two different journeys.
+    first_seen: dict[str, int] = {}
+    for jid, start, _end in blocks:
+        ln = _line_of(start)
+        if jid in first_seen:
+            findings.append(Finding(
+                "ERROR", "duplicate-id", ln,
+                f"duplicate journey id '{jid}' (first defined at line {first_seen[jid]})",
+            ))
+        else:
+            first_seen[jid] = ln
+
+    # journey-shape (WARN): the browser-qa agent needs executable numbered
+    # steps and an observable end state.
+    for jid, start, end in blocks:
+        block = text[start:end]
+        ln = _line_of(start)
+        if not _NUMBERED_STEP_RE.search(block):
+            findings.append(Finding(
+                "WARN", "journey-shape", ln,
+                f"journey {jid} has no numbered steps (1., 2., ...) the browser-qa agent can execute",
+            ))
+        if not _ACCEPTANCE_RE.search(block):
+            findings.append(Finding(
+                "WARN", "journey-shape", ln,
+                f"journey {jid} has no 'Acceptance:' line describing the observable end state",
+            ))
+
+    # placeholder (WARN) — comments/code already blanked in `lines`.
+    for i, line in enumerate(lines, 1):
+        hits = _PLACEHOLDER_RE.findall(line)
+        if hits:
+            extra = f" (+{len(hits) - 1} more on this line)" if len(hits) > 1 else ""
+            findings.append(Finding(
+                "WARN", "placeholder", i,
+                f'leftover template placeholder "{hits[0]}"{extra} — replace with real content',
+            ))
+
+    # vague-acceptance (WARN) — Acceptance lines only (spec scope).
+    for i, line in enumerate(lines, 1):
+        if not _ACCEPTANCE_RE.match(line):
+            continue
+        terms: list[str] = []
+        for t in _VAGUE_RE.findall(line):
+            t = re.sub(r"\s+", " ", t.lower())
+            if t not in terms:
+                terms.append(t)
+        if terms:
+            quoted = ", ".join(f'"{t}"' for t in terms)
+            findings.append(Finding(
+                "WARN", "vague-acceptance", i,
+                f"Acceptance uses vague term(s) {quoted} — state an observable end state instead",
+            ))
+
+    # aspirational-anti-goal (WARN) — bullets in the Anti-goals section.
+    ag_idx = next((i for i, l in enumerate(lines) if _ANTI_GOALS_HEAD_RE.match(l)), None)
+    if ag_idx is not None:
+        for i in range(ag_idx + 1, len(lines)):
+            line = lines[i]
+            if _H2_RE.match(line):
+                break
+            s = line.strip()
+            if not s.startswith("-") or s == "-":
+                continue
+            body = s.lstrip("-").strip()
+            if not body or "TODO" in body or _PLACEHOLDER_RE.search(body):
+                continue  # incomplete, not aspirational — placeholder rule owns those
+            if not _CHECKABLE_RE.search(body):
+                findings.append(Finding(
+                    "WARN", "aspirational-anti-goal", i + 1,
+                    f'anti-goal "{body}" has no checkable condition — phrase it as a '
+                    "veto rule (prohibition or measurable bound)",
+                ))
+
+    # product-shape-empty (WARN): >=2 journeys naming the same value/metric is
+    # exactly the "same number differs across pages" risk the Product Shape
+    # section exists to prevent.
+    gram_owners: dict[str, set[str]] = {}
+    for jid, start, end in blocks:
+        for gram in _acceptance_bigrams(text[start:end]):
+            gram_owners.setdefault(gram, set()).add(jid)
+    shared = sorted(g for g, owners in gram_owners.items() if len(owners) >= 2)
+    if shared:
+        ps_idx = next((i for i, l in enumerate(lines) if _PRODUCT_SHAPE_HEAD_RE.match(l)), None)
+        has_content = False
+        if ps_idx is not None:
+            for i in range(ps_idx + 1, len(lines)):
+                line = lines[i]
+                if _H2_RE.match(line):
+                    break
+                if line.lstrip().startswith("#"):
+                    continue  # ### subheadings are scaffolding, not content
+                content = _PLACEHOLDER_RE.sub("", line).strip().strip("-").strip()
+                if re.search(r"[A-Za-z0-9]", content):
+                    has_content = True
+                    break
+        if not has_content:
+            phrases = ", ".join(f'"{g}"' for g in shared[:3])
+            where = ("has no concrete content" if ps_idx is not None
+                     else "section is missing")
+            findings.append(Finding(
+                "WARN", "product-shape-empty",
+                ps_idx + 1 if ps_idx is not None else None,
+                f">=2 journeys' acceptance criteria reference {phrases} but the "
+                f"Product Shape {where} — pin each shared value to one source "
+                "(templates/project-goal.md, 'Canonical values')",
+            ))
+
+    return findings
+
+
+# ── output / exit-code plumbing ───────────────────────────────────────────────
+
+def exit_code(findings: list[Finding]) -> int:
+    if any(f.severity == "ERROR" for f in findings):
+        return 2
+    return 1 if findings else 0
+
+
+def render(findings: list[Finding], path: str) -> str:
+    if not findings:
+        return ""
+    lines = []
+    for f in sorted(findings, key=lambda f: (f.line or 0)):
+        loc = f" line {f.line}" if f.line else ""
+        lines.append(f"[goal-lint] {f.severity} {f.rule}{loc}: {f.message}")
+    errors = sum(1 for f in findings if f.severity == "ERROR")
+    warns = len(findings) - errors
+    lines.append(
+        f"[goal-lint] {path}: {errors} error(s), {warns} warning(s) — advisory:"
+        " lint never blocks the engine (CHAIN_GOAL_LINT=false to silence)"
+    )
+    return "\n".join(lines)
+
+
+def run_lint(path: str) -> int:
+    try:
+        text = Path(path).read_text(encoding="utf-8")
+    except OSError as e:
+        print(f"[goal-lint] ERROR unreadable: {path}: {e}")
+        return 2
+    findings = lint_text(text)
+    out = render(findings, path)
+    if out:
+        print(out)
+    return exit_code(findings)
+
+
+# ── self-test ─────────────────────────────────────────────────────────────────
+
+_CLEAN = """\
+# Project Goal
+
+## Vision
+A local-first notes app for one user.
+
+## Product Shape
+
+### Navigation / information architecture
+- Notes | Archive | Settings
+
+### Canonical values (single source of truth)
+- unread count — computed once in lib/counts.py, served from /api/counts
+
+## Must-have user journeys
+
+- **J-01: Create a note**
+  - Steps:
+    1. Visit `/notes`
+    2. Click "New note", type "Milk", press Enter
+  - Acceptance: the notes list gains a row titled "Milk" and the unread count reads 1
+
+- **J-02: Archive a note**
+  - Steps:
+    1. Visit `/notes`
+    2. Click the archive icon on the "Milk" row
+  - Acceptance: the row moves to the Archive tab and the unread count reads 0
+
+## Anti-goals
+
+- No cloud sync or third-party network calls.
+- Never store note bodies outside the local SQLite file.
+"""
+
+
+def _rules(findings: list[Finding]) -> list[str]:
+    return [f.rule for f in findings]
+
+
+def _by_rule(findings: list[Finding], rule: str) -> list[Finding]:
+    return [f for f in findings if f.rule == rule]
+
+
+def _self_test() -> int:
+    import contextlib
+    import io
+    import tempfile
+
+    # 0. clean fixture: no findings, exit 0
+    f = lint_text(_CLEAN)
+    assert f == [], f"clean fixture must be finding-free, got: {f}"
+    assert exit_code(f) == 0
+
+    # 1. duplicate-id → ERROR, exit 2 (second J-01 shadows the first)
+    dup = _CLEAN.replace("- **J-02: Archive a note**", "- **J-01: Archive a note**")
+    f = lint_text(dup)
+    d = _by_rule(f, "duplicate-id")
+    assert len(d) == 1 and d[0].severity == "ERROR", f"want 1 duplicate-id ERROR, got: {f}"
+    assert "J-01" in d[0].message
+    assert d[0].line and dup.splitlines()[d[0].line - 1].startswith("- **J-01: Archive"), \
+        "duplicate-id must point at the SECOND occurrence"
+    assert exit_code(f) == 2
+
+    # 2. no-journeys → ERROR, exit 2
+    f = lint_text("# Goal\n\n## Anti-goals\n\n- No cloud sync.\n")
+    assert _rules(f) == ["no-journeys"] and f[0].severity == "ERROR"
+    assert exit_code(f) == 2
+
+    # 3. journey-shape: unnumbered steps / missing Acceptance line
+    shaped = _CLEAN.replace(
+        "  - Steps:\n    1. Visit `/notes`\n    2. Click \"New note\", type \"Milk\", press Enter\n",
+        "  - Steps: visit the notes page and add an item called Milk\n",
+    )
+    f = lint_text(shaped)
+    s = _by_rule(f, "journey-shape")
+    assert len(s) == 1 and "J-01" in s[0].message and "numbered" in s[0].message, \
... [diff_bound] incredible_auto_dev/scripts/automation/lib/goal_lint.py: 142 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/lint_contracts.py b/incredible_auto_dev/scripts/automation/lib/lint_contracts.py
new file mode 100644
index 0000000..b4169ff
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/lint_contracts.py
@@ -0,0 +1,446 @@
+#!/usr/bin/env python3
+"""
+lint_contracts.py — agent-contract static linter (roadmap SAFE-2).
+
+Statically checks the NEUTRAL-SOURCE agent bodies (agents/*/body.md), report
+templates (templates/*.md), and agent manifests (agents/*/agent.yaml) against
+lib/verdicts.py — the single source of verdict truth — so writer→reader drift
+is caught at edit time instead of mid-session.
+
+Checks
+  1. Agent bodies: every verdict value named on a `**Verdict:**` (or
+     `**Browser QA Verdict:**`) line must belong to that agent's report-type
+     enum(s) per AGENT_CONTRACTS; a contract agent must name at least one
+     value of each of its primary enums; an agent with no verdict contract
+     must not carry verdict-marker lines at all.
+  2. Templates: every mapped template still has a line-START verdict-marker
+     line (the position machine parsers read); each such line is either a
+     literal enum value or a `<...>`/pipe placeholder list whose tokens are a
+     subset of the mapped enum(s); templates parsed by
+     verdicts.check_verdict_file() must additionally contain a line matching
+     the real _VERDICT_LINE_RE (else a report following the template could
+     never register as passing); an unmapped template must not introduce
+     verdict-marker lines.
+  3. Every agents/<name>/ dir has body.md and an agent.yaml with non-empty
+     top-level `model_tier:` and `version:` keys.
+
+Scope notes (deliberate):
+  - Lints the neutral source only — `.claude/` mirrors are build products,
+    guarded by `sync-cli-assets.py --check`.
+  - `**Demo Verdict:**` (templates/demo-results.md) is showcase-only, not in
+    verdicts.py, and gates nothing — out of scope.
+  - Verdict values are extracted only from text AFTER a marker on the same
+    line; ALL-CAPS prose elsewhere is ignored. Placeholder words (VERDICT,
+    VALUE) are skipped, not treated as values.
+
+CLI (exit 0 = clean, 1 = violations/failures, 2 = usage/environment):
+    python3 lint_contracts.py lint        # lint this repo, file:line per violation
+    python3 lint_contracts.py self-test   # broken-fixture assertions, then lint this repo
+"""
+
+import re
+import sys
+import tempfile
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parent))
+import verdicts  # noqa: E402
+from verdicts import (  # noqa: E402
+    BrowserQAVerdict,
+    ClosureVerdict,
+    CoherenceVerdict,
+    GoalEvalVerdict,
+    IterationSummaryVerdict,
+    UIVerdict,
+    UXRegressionVerdict,
+    Verdict,
+)
+
+REPO_ROOT = Path(__file__).resolve().parents[3]
+
+# The exact strings machine parsers key on. `**Verdict:**` is verdicts.py's
+# universal format; `**Browser QA Verdict:**` is parsed by
+# merge_ui_test_results.py (_VERDICT_RE) and goal-iter-lean.sh.
+_MARKERS = ("**Verdict:**", "**Browser QA Verdict:**")
+
+_TOKEN_RE = re.compile(r"[A-Z][A-Z0-9_-]{2,}")
+# Placeholder words that appear in `**Verdict:** <VERDICT>` / `**Verdict:** VALUE`
+# format examples — never actual verdict values.
+_SKIP_TOKENS = {"VERDICT", "VALUE", "VALUES"}
+
+# Which verdicts.py enum(s) each agent's report contract draws from.
+# "primary": the enums whose values the body MUST name (its own contract).
+# "extra": additional enums the body may legitimately reference (e.g. source
+# vocabularies it aggregates) — tolerated in the subset check, not required.
+# An agent absent from this map must not carry verdict-marker lines.
+AGENT_CONTRACTS = {
+    "reviewer": {"primary": [Verdict]},
+    "qa": {"primary": [Verdict, UIVerdict]},
+    "auditor": {"primary": [Verdict]},
+    "phase-closure-auditor": {"primary": [ClosureVerdict]},
+    "ux-regression-reviewer": {"primary": [UXRegressionVerdict]},
+    "browser-qa-agent": {"primary": [BrowserQAVerdict]},
+    "goal-evaluator": {"primary": [GoalEvalVerdict]},
+    "coherence-auditor": {"primary": [CoherenceVerdict]},
+    # Aggregator: carries verdicts forward from eval.md / closure-verdict.md /
+    # review.md, so it legitimately names ClosureVerdict source values too.
+    "iteration-summarizer": {"primary": [IterationSummaryVerdict], "extra": [ClosureVerdict]},
+}
+
+# Which enum(s) each verdict-bearing template's `**Verdict:**` lines draw from.
+# "phase_verdict": template output is parsed by verdicts.check_verdict_file()
+# (_VERDICT_LINE_RE), so the template must contain a matching passing line.
+# A template absent from this map must not carry line-start verdict markers.
+TEMPLATE_CONTRACTS = {
+    "audit-report.md": {"enums": [Verdict], "phase_verdict": True},
+    "qa-report.md": {"enums": [Verdict, UIVerdict], "phase_verdict": True},
+    "review-checklist.md": {"enums": [Verdict], "phase_verdict": True},
+    "closure-verdict.md": {"enums": [ClosureVerdict]},
+    "coherence-verdict.md": {"enums": [CoherenceVerdict]},
+    "iteration-summary.md": {"enums": [IterationSummaryVerdict]},
+    "ui-test-results.md": {"enums": [BrowserQAVerdict]},
+}
+
+
+def _enum_values(enums):
+    vals = set()
+    for e in enums:
+        vals.update(m.value for m in e)
+    return vals
+
+
+def _enum_names(enums):
+    return "/".join(e.__name__ for e in enums)
+
+
+def _find_marker(line):
+    """Return (marker, payload-after-marker) for the first marker on the line, else None."""
+    best = None
+    for m in _MARKERS:
+        i = line.find(m)
+        if i >= 0 and (best is None or i < best[0]):
+            best = (i, m)
+    if best is None:
+        return None
+    i, m = best
+    return m, line[i + len(m):]
+
+
+def _extract_values(payload):
+    """Candidate verdict values named after a marker (placeholder words skipped)."""
+    return [t for t in _TOKEN_RE.findall(payload) if t not in _SKIP_TOKENS]
+
+
+def lint_tree(root, agent_contracts, template_contracts):
+    """Lint one source tree. Returns sorted [(relpath, line, code, message), ...]."""
+    root = Path(root)
+    violations = []
+    violations += _lint_agents(root, agent_contracts)
+    violations += _lint_templates(root, template_contracts)
+    return sorted(violations)
+
+
+def _lint_agents(root, contracts):
+    out = []
+    agents_dir = root / "agents"
+    if not agents_dir.is_dir():
+        return out
+    for d in sorted(p for p in agents_dir.iterdir() if p.is_dir()):
+        rel_yaml = f"agents/{d.name}/agent.yaml"
+        yaml_path = d / "agent.yaml"
+        if not yaml_path.is_file():
+            out.append((rel_yaml, 1, "missing-agent-yaml", "agent dir has no agent.yaml"))
+        else:
+            text = yaml_path.read_text(encoding="utf-8")
+            for key, code in (("model_tier", "missing-model-tier"),
+                              ("version", "missing-version")):
+                m = re.search(rf"^{key}:[ \t]*(\S.*)?$", text, re.MULTILINE)
+                if not m or not (m.group(1) or "").strip():
+                    line = text[:m.start()].count("\n") + 1 if m else 1
+                    out.append((rel_yaml, line, code,
+                                f"agent.yaml must set a non-empty top-level '{key}:'"))
+
+        rel_body = f"agents/{d.name}/body.md"
+        body_path = d / "body.md"
+        if not body_path.is_file():
+            out.append((rel_body, 1, "missing-body", "agent dir has no body.md"))
+            continue
+
+        marker_hits = []  # (line_no, payload-after-marker)
+        for i, line in enumerate(body_path.read_text(encoding="utf-8").splitlines(), 1):
+            found = _find_marker(line)
+            if found:
+                marker_hits.append((i, found[1]))
+
+        contract = contracts.get(d.name)
+        if contract is None:
+            if marker_hits:
+                out.append((rel_body, marker_hits[0][0], "unmapped-verdict-contract",
+                            f"body carries a verdict-marker line but '{d.name}' has no entry in "
+                            "AGENT_CONTRACTS — register its report type (add the enum to "
+                            "lib/verdicts.py first if it is new)"))
+            continue
+
+        primary = contract["primary"]
+        allowed = _enum_values(primary) | _enum_values(contract.get("extra", []))
+        named = set()
+        for line_no, payload in marker_hits:
+            for tok in _extract_values(payload):
+                if tok in allowed:
+                    named.add(tok)
+                else:
+                    out.append((rel_body, line_no, "unknown-verdict-value",
+                                f"'{tok}' is not a {_enum_names(primary)} value "
+                                f"(allowed: {', '.join(sorted(allowed))})"))
+        for enum in primary:
+            if not named & _enum_values([enum]):
+                out.append((rel_body, 1, "missing-verdict-values",
+                            f"body never names any {enum.__name__} value on a verdict-marker "
+                            "line — the verdict contract must be stated in the body"))
+    return out
+
+
+def _lint_templates(root, contracts):
+    out = []
+    tdir = root / "templates"
+    if not tdir.is_dir():
+        return out
+    for f in sorted(tdir.glob("*.md")):
+        rel = f"templates/{f.name}"
+        content = f.read_text(encoding="utf-8")
+
+        # Only line-START markers: that is the position _VERDICT_LINE_RE and the
+        # shell greps anchor on. Mid-line mentions are prose/comments.
+        starts = []  # (line_no, payload-after-marker)
+        for i, line in enumerate(content.splitlines(), 1):
+            for m in _MARKERS:
+                if line.startswith(m):
+                    starts.append((i, line[len(m):]))
+                    break
+
+        contract = contracts.get(f.name)
+        if contract is None:
+            if starts:
+                out.append((rel, starts[0][0], "unmapped-verdict-contract",
+                            f"template carries a verdict line but '{f.name}' has no entry in "
+                            "TEMPLATE_CONTRACTS — register its report type (add the enum to "
+                            "lib/verdicts.py first if it is new)"))
+            continue
+
+        allowed = _enum_values(contract["enums"])
+        if not starts:
+            out.append((rel, 1, "missing-verdict-line",
+                        "mapped verdict template has no line starting with a verdict marker — "
+                        "machine parsers can no longer find the verdict"))
+        for line_no, payload in starts:
+            stripped = payload.strip()
+            if stripped.startswith("<") or "|" in stripped:
+                toks = _extract_values(payload)
+                if not toks:
+                    out.append((rel, line_no, "bad-verdict-line",
+                                "placeholder verdict line names no values"))
+                for tok in toks:
+                    if tok not in allowed:
+                        out.append((rel, line_no, "unknown-verdict-value",
+                                    f"'{tok}' is not a {_enum_names(contract['enums'])} value "
+                                    f"(allowed: {', '.join(sorted(allowed))})"))
+            else:
+                m = re.match(r"[ \t]+(\S+)[ \t]*$", payload)
+                if not m:
+                    out.append((rel, line_no, "bad-verdict-line",
+                                "verdict line must be '<marker> VALUE' — single value, "
+                                "whitespace-separated (this is what the parsers match)"))
+                elif m.group(1) not in allowed:
+                    out.append((rel, line_no, "unknown-verdict-value",
+                                f"'{m.group(1)}' is not a {_enum_names(contract['enums'])} value "
+                                f"(allowed: {', '.join(sorted(allowed))})"))
+
+        if contract.get("phase_verdict") and not verdicts._VERDICT_LINE_RE.search(content):
+            out.append((rel, 1, "no-passing-verdict-line",
+                        "template output is parsed by verdicts.check_verdict_file() but no line "
+                        "matches _VERDICT_LINE_RE — a report following it could never pass"))
+    return out
+
+
+def lint_repo():
+    return lint_tree(REPO_ROOT, AGENT_CONTRACTS, TEMPLATE_CONTRACTS)
+
+
+def _print_violations(violations):
+    for path, line, code, msg in violations:
+        print(f"{path}:{line}: [{code}] {msg}")
+
+
+# ── CLI: lint ─────────────────────────────────────────────────────────────────
+
+def _cmd_lint(_args):
+    if not (REPO_ROOT / "agents").is_dir() or not (REPO_ROOT / "templates").is_dir():
+        print(f"Error: {REPO_ROOT} does not look like the framework repo "
+              "(agents/ or templates/ missing)", file=sys.stderr)
+        return 2
+    violations = lint_repo()
+    _print_violations(violations)
+    if violations:
+        print(f"lint_contracts: {len(violations)} violation(s)")
+        return 1
+    n_agents = sum(1 for p in (REPO_ROOT / "agents").iterdir() if p.is_dir())
+    n_templates = len(list((REPO_ROOT / "templates").glob("*.md")))
+    print(f"lint_contracts: OK ({n_agents} agents, {n_templates} templates)")
+    return 0
+
+
+# ── CLI: self-test ────────────────────────────────────────────────────────────
+
+def _write(root, relpath, content):
+    p = root / relpath
+    p.parent.mkdir(parents=True, exist_ok=True)
+    p.write_text(content, encoding="utf-8")
+
+
+_OK_YAML = "name: {name}\nmodel_tier: standard\nversion: 1.0.0\n"
+
+
+def _build_clean_fixture(root):
+    _write(root, "agents/goodagent/agent.yaml", _OK_YAML.format(name="goodagent"))
+    _write(root, "agents/goodagent/body.md",
+           "# Good agent\n"
+           "\n"
+           "Emit `**Verdict:** PASS` on success or `**Verdict:** FAIL` otherwise.\n"
+           "\n"
+           "**Verdict:** <VERDICT>\n")
+    _write(root, "agents/plain/agent.yaml", _OK_YAML.format(name="plain"))
+    _write(root, "agents/plain/body.md", "# Plain agent\n\nNo report contract here.\n")
+    _write(root, "templates/good-report.md",
+           "# Report\n"
+           "\n"
+           "**Verdict:** PASS\n"
+           "\n"
+           "**Verdict:** <PASS | FAIL>\n")
+    _write(root, "templates/bq.md",
+           "# Browser results\n"
+           "\n"
+           "**Browser QA Verdict:** PASS | FAIL | SKIPPED\n")
+    _write(root, "templates/plain.md", "# Nothing verdict-shaped here\n")
+    agent_contracts = {"goodagent": {"primary": [Verdict]}}
+    template_contracts = {
+        "good-report.md": {"enums": [Verdict], "phase_verdict": True},
+        "bq.md": {"enums": [BrowserQAVerdict]},
+    }
+    return agent_contracts, template_contracts
+
+
+def _build_broken_fixture(root):
+    # badvalue: names a value outside its enum (and therefore none inside it)
+    _write(root, "agents/badvalue/agent.yaml", _OK_YAML.format(name="badvalue"))
+    _write(root, "agents/badvalue/body.md", "# Bad\n\n**Verdict:** PASSED\n")
+    # silent: mapped agent that names no verdict values at all
+    _write(root, "agents/silent/agent.yaml", _OK_YAML.format(name="silent"))
+    _write(root, "agents/silent/body.md", "# Silent\n\nNo verdict named here.\n")
+    # rogue: verdict line in an agent with no registered contract
+    _write(root, "agents/rogue/agent.yaml", _OK_YAML.format(name="rogue"))
+    _write(root, "agents/rogue/body.md", "# Rogue\n\n**Verdict:** PASS\n")
+    # noyaml: valid body, missing agent.yaml
+    _write(root, "agents/noyaml/body.md", "# No yaml\n\n**Verdict:** CONTINUE\n")
+    # notier: agent.yaml without model_tier
+    _write(root, "agents/notier/agent.yaml", "name: notier\nversion: 1.0.0\n")
+    _write(root, "agents/notier/body.md", "# No tier\n")
+    # nobody: agent dir without body.md
+    _write(root, "agents/nobody/agent.yaml", _OK_YAML.format(name="nobody"))
+    # broken-bold: the classic drift — bold markers broken, parser can't find the line
+    _write(root, "templates/broken-bold.md", "# Closure\n\n**Verdict: ** CLOSURE-PASS\n")
+    # wrong-value: verdict value outside the mapped enum
+    _write(root, "templates/wrong-value.md", "# Coherence\n\n**Verdict:** MAYBE\n")
+    # fail-only: valid enum value, but nothing _VERDICT_LINE_RE could ever match
+    _write(root, "templates/fail-only.md", "# Audit\n\n**Verdict:** FAIL\n")
+    # nospace: missing the required whitespace between marker and value
+    _write(root, "templates/nospace.md", "# QA\n\n**Verdict:**PASS\n")
+    # rogue-template: verdict line in a template with no registered contract
+    _write(root, "templates/rogue-template.md", "# Rogue\n\n**Verdict:** PASS\n")
+    agent_contracts = {
+        "badvalue": {"primary": [Verdict]},
+        "silent": {"primary": [GoalEvalVerdict]},
+        "noyaml": {"primary": [GoalEvalVerdict]},
+        # rogue / notier / nobody intentionally unmapped
+    }
+    template_contracts = {
+        "broken-bold.md": {"enums": [ClosureVerdict]},
+        "wrong-value.md": {"enums": [CoherenceVerdict]},
+        "fail-only.md": {"enums": [Verdict], "phase_verdict": True},
+        "nospace.md": {"enums": [Verdict]},
+        # rogue-template.md intentionally unmapped
+    }
+    return agent_contracts, template_contracts
+
+
+_EXPECTED_BROKEN = {
+    ("agents/badvalue/body.md", 3, "unknown-verdict-value"),
+    ("agents/badvalue/body.md", 1, "missing-verdict-values"),
+    ("agents/silent/body.md", 1, "missing-verdict-values"),
+    ("agents/rogue/body.md", 3, "unmapped-verdict-contract"),
+    ("agents/noyaml/agent.yaml", 1, "missing-agent-yaml"),
+    ("agents/notier/agent.yaml", 1, "missing-model-tier"),
+    ("agents/nobody/body.md", 1, "missing-body"),
+    ("templates/broken-bold.md", 1, "missing-verdict-line"),
+    ("templates/wrong-value.md", 3, "unknown-verdict-value"),
+    ("templates/fail-only.md", 1, "no-passing-verdict-line"),
+    ("templates/nospace.md", 3, "bad-verdict-line"),
+    ("templates/rogue-template.md", 3, "unmapped-verdict-contract"),
+}
+
+
+def _cmd_self_test(_args):
+    failures = []
+
+    with tempfile.TemporaryDirectory() as td:
... [diff_bound] incredible_auto_dev/scripts/automation/lib/lint_contracts.py: 52 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/render_iteration_summary.py b/incredible_auto_dev/scripts/automation/lib/render_iteration_summary.py
index dcbd2b9..eeb0982 100644
--- a/incredible_auto_dev/scripts/automation/lib/render_iteration_summary.py
+++ b/incredible_auto_dev/scripts/automation/lib/render_iteration_summary.py
@@ -1159,6 +1159,7 @@ def render_html_iteration(data: IterationData) -> str:
         parts.append(_render_technical_intro())
         parts.append(_render_what_was_done(data))
         parts.append(_render_whats_left_next_step(data))
+        parts.append(_render_assumptions(data))
         parts.append(_render_direction_trend(data))
         parts.append(_render_quick_verify(data))
         parts.append(_render_artifacts(data))
@@ -1405,6 +1406,26 @@ def _render_whats_left_next_step(data: IterationData) -> str:
     )
 
 
+def _render_assumptions(data: IterationData) -> str:
+    """Assumption-ledger surfacing (NEED-6). Renders when the summary carries
+    an 'Assumptions made' section — including the explicit 'none recorded'
+    case, which is affirmative information. Older summaries without the
+    section render nothing."""
+    body = data.sections.get("Assumptions made", "")
+    if not body.strip():
+        return ""
+    bullets = _extract_bullets(body)
+    if bullets:
+        items = "".join(f"<li>{escape(b)}</li>" for b in bullets)
+        inner = f"<ul class='bullets'>{items}</ul>"
+    else:
+        inner = f"<div class='why-text'>{escape(body.strip())}</div>"
+    return (
+        f"<details><summary>Assumptions made</summary>"
+        f"<div class='accordion-body'>{inner}</div></details>"
+    )
+
+
 def _render_direction_trend(data: IterationData) -> str:
     body = data.sections.get("Direction", "")
     if not body.strip():
@@ -2213,6 +2234,10 @@ J-04 login flow now passes browser QA.
 
 Target J-06 next iteration. Dispatch as lean if straightforward, else escalate to full.
 
+## Assumptions made
+
+- iter-18 · goal-decomposer — Ambiguity: goal doesn't say whether guests can browse without an account. We chose: browsing works logged-out. Reversible: yes
+
 ## Artifacts
 
 | Report | Verdict | Path |
@@ -2376,6 +2401,10 @@ def _cmd_self_test(_argv: list[str]) -> int:
         failures.append("split_h2: Direction section missing")
     if "In plain words" not in sections:
         failures.append("split_h2: 'In plain words' section missing")
+    if "Assumptions made" not in sections:
+        failures.append("split_h2: 'Assumptions made' section missing")
+    if len(_extract_bullets(sections.get("Assumptions made", ""))) != 1:
+        failures.append("assumptions: expected 1 bullet in goal fixture")
     signal, why = _parse_direction_signal(sections.get("Direction", ""))
     if signal != "improving":
         failures.append(f"signal: expected improving, got {signal}")
@@ -2580,6 +2609,9 @@ def _cmd_self_test(_argv: list[str]) -> int:
             ">NEW<",
             "Open sign-in",
             "Enter your email and password.",
+            # Assumption-ledger accordion (NEED-6) — summary WITH the section.
+            "Assumptions made",
+            "guests can browse",
         ):
             if expect not in html:
                 failures.append(f"goal render missing: {expect}")
@@ -2618,6 +2650,10 @@ def _cmd_self_test(_argv: list[str]) -> int:
             failures.append("phase render should hide direction badge (n/a)")
         if "<details open>" in html_p:
             failures.append("phase render leaves a technical accordion open by default")
+        # Summary WITHOUT an 'Assumptions made' section (older summaries,
+        # NEED-6): the accordion must be absent entirely.
+        if "Assumptions made" in html_p:
+            failures.append("phase render: 'Assumptions made' must not render when the section is absent")
 
         # Missing-summary fallback
         empty_data = load_iteration("missing-phase", tmp)
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 787ac2c..3083bb6 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -72,6 +72,10 @@ _run_self_test scripts/automation/lib/render_iteration_summary.py self-test
 _run_self_test scripts/automation/lib/demo_runner.py self-test
 _run_self_test scripts/automation/lib/merge_ui_test_results.py self-test
 _run_self_test scripts/automation/lib/mcp_sync_selftest.py self-test
+# Agent-contract static linter (SAFE-2): fixture assertions, then lints the live
+# tree — agents/*/body.md + templates verdict vocabulary vs lib/verdicts.py,
+# agent.yaml model_tier/version presence. Red here = writer→reader drift.
+_run_self_test scripts/automation/lib/lint_contracts.py self-test
 
 # Bash-level self-test for the generic project-gate mechanism (M2).
 if bash scripts/automation/lib/project-gates.sh self-test >/dev/null 2>&1; then
@@ -122,8 +126,16 @@ else
   _fail "self-test: parallel.sh (run: bash scripts/automation/lib/parallel.sh self-test)"
 fi
 
+# Opt-in pre-commit eval guard (SAFE-1): installer + hook behavior in a scratch repo.
+if bash scripts/automation/install-git-hooks.sh --self-test >/dev/null 2>&1; then
+  _pass "self-test: install-git-hooks.sh (pre-commit eval guard)"
+else
+  _fail "self-test: install-git-hooks.sh (run: bash scripts/automation/install-git-hooks.sh --self-test)"
+fi
+
 # Goal-mode deterministic gates (verdict cross-checks, diff scan/bounding).
 _run_self_test scripts/automation/lib/goal_gate.py self-test
+_run_self_test scripts/automation/lib/goal_lint.py self-test
 _run_self_test scripts/automation/lib/scan_diff.py self-test
 _run_self_test scripts/automation/lib/diff_bound.py self-test
 if bash scripts/automation/lib/goal-gates.sh --self-test >/dev/null 2>&1; then
@@ -135,7 +147,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-quota-retry.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh; do
+for _t in tests/automation/test-quota-retry.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
```
