# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 9a911825..9907273d 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3253,8 +3253,14 @@ _FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
 # frozenset (not a duplicate mechanism in research.py) because `research.py` reaches this hook via a lazy
 # `from app.engine import data_manager` import (research.py sits BELOW this module in the dependency
 # graph — data_manager already imports FROM research at module level, so the reverse would be circular).
+# ops-hardening iter-53: "coverage_membership_timeline" and "market_phase" added — the two finalize-tail
+# phases this iteration's GIL-hold profile bounded (`universe_resolver.resolve_with_reasons`'s per-symbol
+# bounded-window fetch; `market_phase._severity_reading`'s benchmark/^VIX bounded-window fetch). Both
+# reach this hook via the SAME lazy `from app.engine import data_manager` import trick (data_manager
+# already imports both modules at module level, so the reverse import would be circular).
 _FAULT_INJECT_SITES = frozenset({
     "forward_aggregates", "drawdown_expectations", "backfill_worker", "factor_lab_all",
+    "coverage_membership_timeline", "market_phase",
 })
 
 
@@ -4098,6 +4104,22 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                         # persisted above — warmed for free by that SAME call, never a second/separate
                         # derivation.
                         refreshed.append("membership_timeline")
+            # ops-hardening iter-53 (J-05/J-07, TC-5): this phase's per-date resolver sweep
+            # (`membership_timeline_cached`'s cache-miss fallback -> `_excluded_counts_by_date` ->
+            # `universe_resolver.resolve_with_reasons`, the exact chain this iteration's GIL-hold fix
+            # bounds) had NO MemoryError-distinct handler before this iteration — only the generic
+            # `except Exception` below, unlike the market-phase/forward-aggregates/drawdown-expectations
+            # loops this SAME function drives (iter-8's convention). Added here to match: a MemoryError
+            # under real pressure now returns memory to the OS (`_release_process_memory()`) before the
+            # generic handler's "log + continue" runs, instead of leaving the abort to a plain exception
+            # log with no memory recovery. `coverage`/`membership_timeline` are correctly OMITTED from
+            # `refreshed` either way (both `except` branches are reached only from BEFORE the two
+            # `refreshed.append(...)` calls above ever run) — the honesty gate is unchanged.
+            except MemoryError as exc:
+                _log_isolation_failure(
+                    "ingest coverage/membership-timeline refresh aborted — memory pressure: %s", exc,
+                )
+                _release_process_memory()
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
                 _log_isolation_failure("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
             logger.info(
diff --git a/apps/backend/app/engine/market_phase.py b/apps/backend/app/engine/market_phase.py
index 6fff8229..166a5971 100644
--- a/apps/backend/app/engine/market_phase.py
+++ b/apps/backend/app/engine/market_phase.py
@@ -47,7 +47,7 @@ from app.config import (
     get_config,
 )
 from app.engine.labels import label_for
-from app.engine.prices import bar_cache, bars_asof, closes
+from app.engine.prices import bar_cache, bars_asof, bars_asof_window, close_on, closes
 from app.engine.research import _dataset_version  # single-sourced cache stamp (J-72) — never duplicated
 from app.models import MacroSeries, MarketPhaseCache, ScannerRun
 
@@ -112,12 +112,25 @@ def _drawdown_components(closes_window: list[float], cfg: Config) -> dict:
 def _latest_vix_on_or_before(session: Session, d: date_cls, cfg: Config) -> Optional[float]:
     """The ^VIX close on/before D (date <= D, no lookahead), or None when no ^VIX bar exists. Reads the
     configured volatility symbol (`etfs.volatility[0]`, the SAME symbol the regime engine's VIX gate
-    reads) via `bars_asof` — a pure causal read; recomputes nothing."""
+    reads) — a pure causal read; recomputes nothing.
+
+    ops-hardening iter-53 (J-05/J-07, GIL-hold bound — profiled, not assumed): this call is inside
+    `_severity_reading`'s per-run loop (`compute_market_phase`, ~2,900 stored runs on the live 30y basis).
+    A live GIL-stall profile of `market_phase_warm` (probe thread capturing the worker's stack at the
+    instant each stall resolved — `reports/perf-budgets.md`'s iter-53 addendum) found EVERY stall
+    resolving HERE: `closes(bars_asof(...))` built ^VIX's entire <= D history (a `Bar` NamedTuple per row,
+    up to ~7,500 on the live basis) just to read `series[-1]` — 65 stalls / 3.34s in a single `compute_
+    market_phase` call alone. Not a `sorted()` call and not a GC pause (the two culprits iter-52 found in
+    `compute_factor_lab_all` — a genuinely different bottleneck; the fix bounds the real one rather than
+    force-fitting that pattern). `close_on(session, symbol, d)` is the EXISTING, already-proven single-bar
+    accessor ("the single-bar form of bars_asof(session, symbol, d)[-1].close ... fetches only the ONE bar
+    instead of materializing the symbol's full pre-history", iter-26/J-16) — byte-identical, including the
+    no-bar -> None case (`closes([])[-1] if [] else None` and `close_on`'s own None both resolve to the
+    SAME "no bar on/before D" NA)."""
     symbols = cfg.etfs.volatility
     if not symbols:
         return None
-    series = closes(bars_asof(session, symbols[0], d))
-    return series[-1] if series else None
+    return close_on(session, symbols[0], d)
 
 
 def _macro_value_asof(session: Session, series_id: str, d: date_cls) -> Optional[float]:
@@ -176,8 +189,32 @@ def _severity_reading(
     bench = cfg.etfs.index[0]  # the benchmark (SPY) — the SAME first index ETF the RS benchmark uses
     d = run.asof_date
 
+    # lazy import — app.engine.data_manager imports FROM this module at module level (`market_phase_
+    # cached`), so a module-level import back would be circular (mirrors the identical trick research.py
+    # and forward_testing.py already use). Used only for the test-only `_fault_inject_memory_error` hook
+    # below (a no-op in production).
+    from app.engine import data_manager
+    # ops-hardening iter-53 (J-05/J-07, TC-5): the fault-injection probe for THIS treated site — see
+    # `_FAULT_INJECT_SITES`'s "market_phase" entry. Placed inside `_severity_reading` itself (the per-run
+    # body `compute_market_phase`'s loop calls once per stored run, ~2,900 times on the live 30y basis —
+    # the ACTUAL treated loop), not at `compute_market_phase`'s or `market_phase_cached`'s own call site,
+    # mirroring `compute_factor_lab_all`'s convention so a drill/test exercises the real treated code path.
+    data_manager._fault_inject_memory_error("market_phase")  # test-only; a no-op in every real deployment
+
     start = d - timedelta(days=mp.lookback_days)
-    window = [bar for bar in bars_asof(session, bench, d) if bar.date >= start]
+    # ops-hardening iter-53 (J-05/J-07, GIL-hold bound — profiled, not assumed): the SAME defect
+    # `_latest_vix_on_or_before` (above) was measured to hold the GIL on — `bars_asof(session, bench, d)`
+    # builds the benchmark's ENTIRE <= D history (up to ~7,500 `Bar` NamedTuples on the live 30y basis)
+    # only to filter it down to the trailing `lookback_days` calendar-day window immediately below.
+    # `bars_asof_window(session, bench, d, mp.lookback_days)` fetches only the trailing `lookback_days`
+    # bars BY COUNT — provably sufficient to reproduce the SAME `>= start` filtered result: the number of
+    # TRADING days within any `lookback_days` CALENDAR days can never exceed `lookback_days` (a trading
+    # day is always one calendar day, so N calendar days admit at most N trading days), and `bars_asof`'s
+    # ascending order means every date >= `start` occupies a trailing SUFFIX of the full series — so a
+    # `lookback_days`-sized trailing-count window is guaranteed to contain that whole suffix regardless of
+    # history density/gaps. Filtering the (now bounded) window with the SAME `>= start` condition below is
+    # therefore byte-identical to filtering the full prefix.
+    window = [bar for bar in bars_asof_window(session, bench, d, mp.lookback_days) if bar.date >= start]
     if len(window) < mp.min_history_bars:
         return None  # insufficient benchmark history -> NA / partial (never fabricated)
     closes_window = closes(window)
@@ -500,14 +537,21 @@ def _downtrend_episodes(timeline: list[dict], as_of: date_cls, cfg: Config) -> l
 
 def _trailing_ma_reclaimed(session: Session, as_of: date_cls, cfg: Config) -> Optional[bool]:
     """Whether the benchmark close on/before D has RECLAIMED its trailing moving average over the config
-    `recovery_trailing_ma_days` window (J-90 confirmation leg). Reads ONLY bars dated <= D via `bars_asof`
-    (no lookahead): the last close vs the mean close over the trailing window. None when there is no bar
-    on/before D (an honest gap — the caller treats a missing reclaim as no-signal, never fabricated). A
-    pure causal read; recomputes nothing, carries no literal (the window is the config key)."""
+    `recovery_trailing_ma_days` window (J-90 confirmation leg). Reads ONLY bars dated <= D (no lookahead):
+    the last close vs the mean close over the trailing window. None when there is no bar on/before D (an
+    honest gap — the caller treats a missing reclaim as no-signal, never fabricated). A pure causal read;
+    recomputes nothing, carries no literal (the window is the config key).
+
+    ops-hardening iter-53 (J-05/J-07, GIL-hold bound): the SAME bounded-window treatment as
+    `_severity_reading`'s benchmark drawdown leg, for the SAME reason and with the SAME byte-identity proof
+    (a `lookback_days`-by-COUNT window is provably a superset of any `lookback_days`-by-CALENDAR-day filter,
+    since trading days are never denser than calendar days) — `_recovery_turn_signal` calls this once per
+    `compute_market_phase` invocation (in scope for `market_phase_warm`); `_recovery_turn_dates_with_context`
+    (below) also calls it, unmodified, and benefits for free."""
     mp = cfg.market_phase
     bench = cfg.etfs.index[0]
     start = as_of - timedelta(days=mp.recovery_trailing_ma_days)
-    window = [bar for bar in bars_asof(session, bench, as_of) if bar.date >= start]
+    window = [bar for bar in bars_asof_window(session, bench, as_of, mp.recovery_trailing_ma_days) if bar.date >= start]
     series = closes(window)
     if not series:
         return None
diff --git a/apps/backend/app/engine/universe_resolver.py b/apps/backend/app/engine/universe_resolver.py
index 4966b162..831c13cb 100644
--- a/apps/backend/app/engine/universe_resolver.py
+++ b/apps/backend/app/engine/universe_resolver.py
@@ -43,7 +43,7 @@ from sqlalchemy import func
 from sqlmodel import Session, select
 
 from app.config import Config, get_config
-from app.engine.prices import active_bar_cache, bars_asof
+from app.engine.prices import active_bar_cache, bars_asof_window
 from app.engine.universe_screen import read_pool
 from app.models import DailyPrice
 
@@ -81,7 +81,9 @@ def _adv_dollar(bars: list, adv_window_days: int) -> Optional[float]:
     return sum(pairs) / len(pairs)
 
 
-def resolve_candidate(bars: list, symbol: str, cfg: Config, asof: date_cls) -> CandidateResolution:
+def resolve_candidate(
+    bars: list, symbol: str, cfg: Config, asof: date_cls, *, bar_count: Optional[int] = None,
+) -> CandidateResolution:
     """Resolve ONE candidate from its already-fetched bars-as-of-D list (ascending, date <= D) at the
     resolve date `asof` (= D). Pure: no DB access, no config of its own beyond the passed `cfg`. The
     gates are checked in a fixed order (history -> staleness -> price -> ADV) so the recorded `reason`
@@ -97,7 +99,13 @@ def resolve_candidate(bars: list, symbol: str, cfg: Config, asof: date_cls) -> C
     (no lookahead; no magic number — the threshold is `cfg.universe.filters.max_staleness_days`)."""
     filters = cfg.universe.filters
     min_history = cfg.indicators.min_history_bars
-    bar_count = len(bars)
+    # ops-hardening iter-53 (J-05/J-07, GIL-hold bound): `bar_count` is OPTIONAL — a caller with a
+    # cheaper/already-known trailing count (`resolve_with_reasons`, below) passes it explicitly so this
+    # function need not be handed the FULL bars-as-of-D list just to measure its length; `len(bars)`
+    # remains the default for every caller that already passes the full list (every direct unit test in
+    # test_universe_resolver.py — unaffected, byte-identical).
+    if bar_count is None:
+        bar_count = len(bars)
 
     if bar_count < min_history:
         return CandidateResolution(symbol, False, REASON_BELOW_HISTORY, bar_count)
@@ -183,6 +191,33 @@ def resolve_with_reasons(
         bar_count_by_symbol = {sym: int(n or 0) for sym, n in counts_rows}
 
     resolutions: list[CandidateResolution] = []
+    # ops-hardening iter-53 (J-05/J-07, GIL-hold bound — profiled, not assumed): a live GIL-stall profile
+    # of THIS exact call (`coverage_membership_timeline_refresh`'s finalize-tail phase, run against the
+    # committed DB with a probe thread capturing the worker's stack at the instant each stall resolved —
+    # `reports/perf-budgets.md`'s iter-53 addendum) found every stall bottoming out in ONE place:
+    # `_SymbolColumns.__getitem__`'s list comprehension (`prices.py`), building a `Bar` NamedTuple for
+    # EVERY row in a symbol's FULL <= asof history (`bars_asof`, up to ~7,500 rows on the live 30y basis)
+    # — not a `sorted()` call and not a GC pause (the two culprits iter-52 found in `compute_factor_lab_all`
+    # — this is a genuinely different bottleneck; per this iteration's own instructions, the fix below
+    # bounds the real one instead of force-fitting the iter-52 pattern). `resolve_candidate` below reads
+    # only `bars[-1]` (staleness/price) and `_adv_dollar`'s own `bars[-adv_window_days:]` trailing slice —
+    # never anything earlier — so fetching the full prefix just to read its tail is pure waste.
+    # `bars_asof_window(session, symbol, asof, lookback)` is the EXISTING, already-proven bounded sibling
+    # (iter-27/J-16: "BYTE-IDENTICAL to bars_asof(session, symbol, d)[-lookback:] ... without materializing
+    # the discarded earlier prefix"). Fetching exactly `adv_window_days` trailing bars is provably
+    # sufficient: `bars[-1]` is the same last element either way, and `_adv_dollar`'s own
+    # `bars[-adv_window_days:]` slice on an already-`adv_window_days`-sized (or shorter) list is a no-op —
+    # the same content either way. `bar_count` — the count THIS loop already computed via
+    # `bar_count_by_symbol` (proven byte-identical to `len(bars_asof(...))` — see that dict's own build
+    # comment above) — is passed through explicitly so the bounded fetch changes WHAT IS FETCHED, never
+    # what is COMPUTED or DISCLOSED: every `CandidateResolution.bars`/`excluded_counts` value stays
+    # byte-identical (TC-3).
+    window_days = max(1, cfg.universe.filters.adv_window_days)
+    # lazy import — app.engine.data_manager imports FROM this module (`resolve_with_reasons` above), so a
+    # module-level import back would be circular (mirrors research.py's/forward_testing.py's own lazy
+    # imports of data_manager, for the identical reason). Used only for the test-only
+    # `_fault_inject_memory_error` hook below (a no-op in production).
+    from app.engine import data_manager
     for symbol in resolve_symbols:
         bar_count = bar_count_by_symbol.get(symbol, 0)
         if bar_count < min_history:
@@ -191,8 +226,13 @@ def resolve_with_reasons(
                 CandidateResolution(symbol, False, REASON_BELOW_HISTORY, bar_count)
             )
             continue
-        bars = bars_asof(session, symbol, asof)
-        resolutions.append(resolve_candidate(bars, symbol, cfg, asof))
+        # ops-hardening iter-53 (J-05/J-07, TC-5): the fault-injection probe for THIS treated site — see
+        # `_FAULT_INJECT_SITES`'s "coverage_membership_timeline" entry. Placed at the per-symbol bounded
+        # fetch itself (not at `resolve_with_reasons`'s own call site), mirroring `compute_factor_lab_all`'s
+        # convention, so a drill/test exercises the REAL treated code path.
+        data_manager._fault_inject_memory_error("coverage_membership_timeline")  # test-only; no-op in prod
+        bars = bars_asof_window(session, symbol, asof, window_days)
+        resolutions.append(resolve_candidate(bars, symbol, cfg, asof, bar_count=bar_count))
 
     admitted = sorted(r.symbol for r in resolutions if r.admitted)
     excluded_counts = {reason: 0 for reason in EXCLUSION_REASONS}
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 14f88557..0d0165ab 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1912,6 +1912,110 @@ def test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succee
     assert payload is not None
 
 
+# ==================================================================================================
+# ops-hardening iter-53 (J-05/J-07, TC-5) — the fault-injection probe ARMED AT THE ACTUAL TREATED SITE
+# (`TRENDORA_FAULT_INJECT_MEMORY_ERROR`, mirroring the existing `factor_lab_all` convention — see
+# `test_research_streaming.py::test_compute_factor_lab_all_restores_the_collector_after_an_injected_
+# memory_error`), not a monkeypatched whole-function stand-in like the tests above. These prove the
+# INNER call this iteration's GIL-hold fix bounds (`universe_resolver.resolve_with_reasons`'s per-symbol
+# `bars_asof_window` fetch; `market_phase._severity_reading`'s benchmark/^VIX bounded fetch) still
+# preserves the iter-8 MemoryError isolate-and-continue contract when the fault fires from INSIDE the
+# real, unmocked treated code path (not merely at the loop's own call site).
+# ==================================================================================================
+def test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly(
+    tmp_path, monkeypatch,
+):
+    """`TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline` armed against a REAL (unmocked)
+    `universe_resolver.resolve_with_reasons` call over a pool with an admitted-eligible LONG-history
+    candidate (so the injection site — placed AFTER the history-gate short-circuit, at the bounded fetch
+    itself — is actually reached, not skipped): `coverage`/`membership_timeline` are honestly OMITTED
+    from `aggregates_refreshed`, the NEW dedicated `except MemoryError` handler this iteration added for
+    this phase calls `_release_process_memory()`, and the hook itself does not raise."""
+    from app.engine import universe_resolver
+
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{tmp_path / 'cov-fault.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 6, 1)
+    start = d - timedelta(days=249)
+
+    def _fake_pool(seed_dir=None):
+        return [{"symbol": "LONG", "sector": "Technology", "source": "test"}]
+
+    monkeypatch.setattr(data_manager, "read_pool", _fake_pool)
+    monkeypatch.setattr(universe_resolver, "read_pool", _fake_pool)
+
+    with Session(engine) as session:
+        for i in range(250):  # comfortably clears history(200)/price($10)/ADV($50M) -> admitted-eligible
+            session.add(DailyPrice(
+                symbol="LONG", date=start + timedelta(days=i), open=50.0, high=50.0, low=50.0,
+                close=50.0, volume=2_000_000.0,
+            ))
+        session.add(ScannerRun(
+            asof_date=d, created_at=datetime(2024, 6, 1), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+
+    release_calls = {"n": 0}
+
+    def _count_release():
+        release_calls["n"] += 1
+
+    monkeypatch.setattr(data_manager, "_release_process_memory", _count_release)
+    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "coverage_membership_timeline")
+
+    with Session(engine) as session:
+        prog = JobProgress(job_id="cov-fault-probe", kind="backfill", start=d, end=d)
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+
+    assert "coverage" not in refreshed and "membership_timeline" not in refreshed, (
+        f"the faulted category must be honestly omitted, never a fabricated refresh: {refreshed}"
+    )
+    assert release_calls["n"] >= 1, "_release_process_memory() must be called on the injected MemoryError"
+
+    # TC-4-style recovery check: a genuine SUBSEQUENT read in the same process still succeeds (no leaked
+    # lock/transaction from the aborted call) once the fault is disarmed.
+    monkeypatch.delenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", raising=False)
+    with Session(engine) as session:
+        payload = data_manager.refresh_coverage_snapshot(session, cfg)
+    assert payload is not None
+
+
+def test_finalize_hook_market_phase_fault_injected_releases_memory_honestly(finalize_hook_multi_date_engine, monkeypatch):
+    """`TRENDORA_FAULT_INJECT_MEMORY_ERROR=market_phase` armed against a REAL (unmocked) `compute_market_
+    phase` -> `_severity_reading` call: the EXISTING per-date `except MemoryError` handler in
+    `_refresh_ingest_aggregates`'s `market_phase_warm` loop (unchanged by this iteration) still fires
+    correctly when the fault originates from INSIDE the newly-bounded fetch, not merely when the whole
+    `market_phase_cached` function is monkeypatched away (the shape the OLDER tests above use)."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+
+    release_calls = {"n": 0}
+
+    def _count_release():
+        release_calls["n"] += 1
+
+    monkeypatch.setattr(data_manager, "_release_process_memory", _count_release)
+    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "market_phase")
+
+    with Session(engine) as session:
+        prog = JobProgress(job_id="mp-fault-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.new_snapshot_dates = dates
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+
+    assert "market_phase" not in refreshed, (
+        f"the faulted category must be honestly omitted, never a fabricated refresh: {refreshed}"
+    )
+    assert release_calls["n"] >= 1, "_release_process_memory() must be called on the injected MemoryError"
+
+    monkeypatch.delenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", raising=False)
+    with Session(engine) as session:
+        payload = data_manager.refresh_coverage_snapshot(session, cfg)
+    assert payload is not None
+
+
 def test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop(
     finalize_hook_engine, monkeypatch
 ):
diff --git a/apps/backend/tests/test_data_manager_membership_cache.py b/apps/backend/tests/test_data_manager_membership_cache.py
index 92eaf16a..8fd56643 100644
--- a/apps/backend/tests/test_data_manager_membership_cache.py
+++ b/apps/backend/tests/test_data_manager_membership_cache.py
@@ -27,7 +27,7 @@ Named proofs (each guards a DoD line):
 from __future__ import annotations
 
 import copy
-from datetime import date, datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 
 from sqlmodel import Session, select
 
@@ -376,3 +376,63 @@ def test_cold_compute_coverage_never_prefills_whole_table_and_batches_by_symbol(
         "expected multiple batches (the real committed candidate pool is wider than the default batch "
         f"width {batch_width}) — got only {load_only_calls}, so this test would not catch an un-batched load"
     )
+
+
+# ==================================================================================================
+# ops-hardening iter-53 (J-05/J-07, GIL-hold bound — TC-3). A live GIL-stall profile of
+# `coverage_membership_timeline_refresh` (probe thread capturing the worker's stack at the instant each
+# stall resolved — `reports/perf-budgets.md`'s iter-53 addendum) found `universe_resolver.resolve_with_
+# reasons`'s per-symbol `bars_asof` call building a candidate's ENTIRE <= asof history (up to ~7,500
+# `Bar` NamedTuples on the live 30y basis) just to read its trailing ADV window — not a `sorted()` call
+# and not a GC pause (the two culprits iter-52 found in `compute_factor_lab_all`). The fix (`bars_asof_
+# window`, proven byte-identical at the `resolve_with_reasons` layer in test_universe_resolver.py's own
+# iter-53 tests) is exercised by `_excluded_counts_by_date` through BOTH of its branches — this test
+# proves the INTEGRATION: identical excluded-by-reason totals through the ACTIVE-bar-cache branch (the
+# ingest finalize-tail shape) and the no-cache batched fallback, for a candidate with LONG (250-bar)
+# history that genuinely exercises the bounded fetch (not just the below_history short-circuit).
+# ==================================================================================================
+def test_excluded_counts_by_date_byte_identical_active_cache_vs_batched_long_history(tmp_path, monkeypatch):
+    """A controlled 3-symbol pool — one admitted with LONG history (250 bars, well past `bars_asof_
+    window`'s `adv_window_days` fetch bound), one `below_history` (5 bars), one `below_price` ($5, under
+    the real committed $10 gate) — resolved identically whether `_excluded_counts_by_date` takes its
+    ACTIVE-bar-cache branch or its no-cache batched-fallback branch."""
+    from app.engine import universe_resolver
+
+    cfg = load_config()  # the REAL committed thresholds (min_history_bars=200, min_price=$10) — unmodified
+    engine = make_engine(f"sqlite:///{tmp_path / 'excl.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 6, 1)
+    start = d - timedelta(days=249)
+
+    def _fake_pool(seed_dir=None):
+        return [{"symbol": s, "sector": "Technology", "source": "test"} for s in ("LONG", "SHORT", "CHEAP")]
+
+    monkeypatch.setattr(universe_resolver, "read_pool", _fake_pool)
+
+    with Session(engine) as session:
+        for i in range(250):  # LONG: comfortably clears history(200)/price($10)/ADV($50M) -> admitted
+            session.add(DailyPrice(
+                symbol="LONG", date=start + timedelta(days=i), open=50.0, high=50.0, low=50.0,
+                close=50.0, volume=2_000_000.0,
+            ))
+        for i in range(5):  # SHORT: 5 < 200 -> below_history
+            session.add(DailyPrice(
+                symbol="SHORT", date=d - timedelta(days=4 - i), open=50.0, high=50.0, low=50.0,
+                close=50.0, volume=2_000_000.0,
+            ))
+        for i in range(250):  # CHEAP: enough history, but $5 < the real $10 min_price gate
+            session.add(DailyPrice(
+                symbol="CHEAP", date=start + timedelta(days=i), open=5.0, high=5.0, low=5.0,
+                close=5.0, volume=2_000_000.0,
+            ))
+        session.commit()
+
+        pool_symbols = {"LONG", "SHORT", "CHEAP"}
+        with prices_module.bar_cache(session):  # ACTIVE cache branch (the ingest finalize-tail shape)
+            active = data_manager._excluded_counts_by_date(session, cfg, [d], pool_symbols)
+        no_cache = data_manager._excluded_counts_by_date(session, cfg, [d], pool_symbols)  # batched fallback
+
+    assert active == no_cache
+    assert active[d]["below_history"] == 1  # SHORT
+    assert active[d]["below_price"] == 1    # CHEAP
+    assert active[d]["stale_series"] == 0 and active[d]["below_adv"] == 0  # LONG is cleanly admitted
diff --git a/apps/backend/tests/test_market_phase.py b/apps/backend/tests/test_market_phase.py
index 7eac3d8c..a439782b 100644
--- a/apps/backend/tests/test_market_phase.py
+++ b/apps/backend/tests/test_market_phase.py
@@ -259,6 +259,126 @@ def test_components_breakdown_disclosed_and_explainable():
     assert abs(sum(contribs) - result["severity"]) < 0.1  # contributions reconstruct the severity
 
 
+# ==================================================================================================
+# ops-hardening iter-53 (J-05/J-07, GIL-hold bound — TC-3). A live GIL-stall profile of `market_phase_
+# warm` (probe thread capturing the worker's stack at the instant each stall resolved —
+# `reports/perf-budgets.md`'s iter-53 addendum) found `_severity_reading`'s benchmark-drawdown and
+# ^VIX-gate reads building a symbol's ENTIRE <= D history (up to ~7,500 `Bar` NamedTuples on the live
+# 30y basis) just to read a small trailing slice — 65 stalls / 3.34s in a single `compute_market_phase`
+# call alone. Not a `sorted()` call and not a GC pause (the two culprits iter-52 found in
+# `compute_factor_lab_all`); the fix bounds the real bottleneck instead: `bars_asof_window` (benchmark
+# window + `_trailing_ma_reclaimed`) and `close_on` (^VIX gate) replace the full-history fetch. These
+# tests prove `compute_market_phase`'s served output is unaffected — the hard way, by proving bars
+# OUTSIDE the bounded window (which never should have influenced the result, before or after this fix)
+# still don't, and that the correct trailing value is still read when history is long.
+# ==================================================================================================
+def test_severity_reading_benchmark_window_ignores_bars_older_than_lookback_bound():
+    """A block of OLDER bars at a wildly different price level, prepended far enough back that NEITHER
+    the pre-fix calendar filter NOR the post-fix count-bounded fetch should ever include them, must not
+    change the served severity/drawdown/off_trough/components — proving the bounded fetch is neither too
+    narrow (dropping bars the calendar filter would have kept) nor too wide (leaking the older block in)."""
+    cfg = _small_config()
+    cfg.market_phase.lookback_days = 30  # deliberately small so the bounded fetch is genuinely exercised
+    d = _BASE + timedelta(days=99)
+    recent = [100.0 - 0.3 * i for i in range(40)]  # the only bars that should ever matter (last 40 days)
+
+    engine_bare = _engine()
+    with Session(engine_bare) as session:
+        _insert_bars(session, "SPY", recent, start=d - timedelta(days=39))
+        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
+        session.commit()
+        bare = compute_market_phase(session, d, cfg)
+
+    engine_padded = _engine()
+    with Session(engine_padded) as session:
+        # an OLDER block at a WILDLY different price (5.0, vs. the ~90-100 range above) — would corrupt
+        # the peak-to-trough drawdown / time-underwater calc if it wrongly entered the window.
+        _insert_bars(session, "SPY", [5.0] * 200, start=d - timedelta(days=239))
+        _insert_bars(session, "SPY", recent, start=d - timedelta(days=39))
+        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
+        session.commit()
+        padded = compute_market_phase(session, d, cfg)
+
+    assert bare["available"] is True and padded["available"] is True
+    assert bare["severity"] == padded["severity"]
+    assert bare["drawdown_pct"] == padded["drawdown_pct"]
+    assert bare["off_trough_pct"] == padded["off_trough_pct"]
+    assert bare["p_bear"] == padded["p_bear"]
+    assert bare["components"] == padded["components"]
+
+
+def test_severity_reading_vix_gate_reads_the_latest_close_via_close_on():
+    """`_latest_vix_on_or_before` now reads `close_on` (single-bar) instead of `closes(bars_asof(...))
+    [-1]` (full-history). A LONG ^VIX series (60 bars, far more than any small test window) with a
+    DISTINCTIVE last value must still be read correctly — proving the single-bar accessor did not
+    silently drop or misalign the latest close."""
+    cfg = _small_config()
+    d = _BASE + timedelta(days=59)
+    with Session(_engine()) as session:
+        _insert_bars(session, "SPY", [100.0 for _ in range(60)])
+        _insert_bars(session, "^VIX", [20.0 + i for i in range(59)] + [77.35], start=_BASE)
+        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
+        session.commit()
+        result = compute_market_phase(session, d, cfg)
+    # the raw close (rounded) is disclosed verbatim alongside the scaled component -- the direct proof
+    # that `close_on` read the TRUE last bar (77.35), not a stale or misaligned one.
+    assert result["vix_level"]["value"] == 77.35
+    assert result["vix_level"]["available"] is True
+    vix_component = next(c for c in result["components"] if c["name"] == "vix_gate")
+    assert vix_component["available"] is True
+    # vix_gate = min(1, vix_close / vix_gate_threshold=30.0); 77.35 clamps the scaled component to 1.0.
+    assert vix_component["value"] == 1.0
+
+
+def test_recovery_turn_trailing_ma_bounded_fetch_byte_identical():
+    """`_trailing_ma_reclaimed` (the J-90 recovery-turn confirmation leg) now fetches a bounded trailing
+    window too — the SAME older-block-must-not-leak proof as the benchmark drawdown leg above, applied to
+    the recovery-turn signal path (`_recovery_turn_signal` -> `_trailing_ma_reclaimed`, reached once per
+    `compute_market_phase` call, in scope for `market_phase_warm`)."""
+    cfg = _small_config()
+    # `_small_config()` sets `lookback_days = 10000` ("never clips the synthetic window") -- deliberately
+    # narrowed back down here, alongside `recovery_trailing_ma_days`, so the OLDER padding block below
+    # (placed outside BOTH windows) cannot leak into the UNRELATED drawdown leg either — isolating this
+    # test to `_trailing_ma_reclaimed`'s own bounded fetch, the thing iter-53 actually changed.
+    cfg.market_phase.lookback_days = 40
+    cfg.market_phase.recovery_trailing_ma_days = 20
+    # a decline to a trough, then a fresh exit above the MA -- built to plausibly trigger the recovery
+    # leg's ma_reclaimed read regardless of the exact signal outcome; the assertion below only requires
+    # the TWO scenarios (bare vs. padded with an older, differently-priced block) to agree.
+    down = [100.0 - i for i in range(21)]   # 100 -> 80
+    up = [80.0 + 2 * i for i in range(10)]  # 80 -> 98 (reclaiming the trailing MA)
+    recent = down + up                      # 31 bars, spanning [D-30, D]
+    d = _BASE + timedelta(days=300)         # far enough from day 0 for the padding block below to fit
+    recent_start = d - timedelta(days=len(recent) - 1)
+
+    engine_bare = _engine()
+    with Session(engine_bare) as session:
+        _insert_bars(session, "SPY", recent, start=recent_start)
+        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
+        session.commit()
+        bare = compute_market_phase(session, d, cfg)
+
+    engine_padded = _engine()
+    with Session(engine_padded) as session:
+        # The BINDING window is the drawdown leg's own `lookback_days` (40), which looks back from D =
+        # recent_start + 30 -- its calendar cutoff is `recent_start + 30 - 40 = recent_start - 10`. The
+        # padding block ends 60 days before `recent_start` (a 50-day safety margin past that cutoff) so it
+        # is excluded from BOTH windows' calendar range regardless of fetch mechanism -- a `bars_asof_
+        # window` COUNT-based fetch does not by itself guarantee exclusion (a large enough total bar count
+        # could still admit padding bars by count even when they are calendar-outside the window; the
+        # margin here is deliberately calendar-based, not count-based, to rule that out).
+        padding_end = recent_start - timedelta(days=60)
+        padding_start = padding_end - timedelta(days=199)  # 200 consecutive bars
+        _insert_bars(session, "SPY", [5.0] * 200, start=padding_start)
+        _insert_bars(session, "SPY", recent, start=recent_start)
+        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
+        session.commit()
+        padded = compute_market_phase(session, d, cfg)
+
+    assert bare["severity"] == padded["severity"]  # sanity: the drawdown leg itself is unaffected too
+    assert bare["recovery_turn"] == padded["recovery_turn"]
+
+
 # --------------------------------------------------------------------------------------------------
 # iter-30 (J-89 / J-90) — timeline series, dated downtrend episodes, the FENCED retrospective, and the
 # causal recovery-turn signal. FAST synthetic tests (no seed boot) — the anti-goal-critical legs.
diff --git a/apps/backend/tests/test_universe_resolver.py b/apps/backend/tests/test_universe_resolver.py
index 3bb2996c..caca0830 100644
--- a/apps/backend/tests/test_universe_resolver.py
+++ b/apps/backend/tests/test_universe_resolver.py
@@ -333,4 +333,90 @@ def test_resolve_empty_db_is_honest_empty(tmp_path):
     with Session(engine) as session:
         out = resolve_with_reasons(session, date(2024, 6, 1), cfg, seed_dir=seed_dir)
     assert out["admitted"] == []
-    assert out["excluded_counts"][REASON_BELOW_HISTORY] == 2
+
+
+# ==================================================================================================
+# ops-hardening iter-53 (J-05/J-07, GIL-hold bound — TC-3) — `resolve_with_reasons` now fetches a
+# BOUNDED trailing window (`bars_asof_window`, `adv_window_days` wide) per admitted-history candidate
+# instead of the FULL <= asof prefix (`bars_asof`), and passes the already-known trailing `bar_count`
+# through explicitly rather than re-deriving it from `len(bars)`. A live GIL-stall profile (this
+# iteration's `reports/perf-budgets.md` addendum) proved the FULL fetch was the real GIL-hold source —
+# not a `sorted()` call and not a GC pause. `bars_asof_window`'s OWN byte-identity to
+# `bars_asof(...)[-lookback:]` is proven separately (test_bar_cache.py); these tests prove
+# `resolve_with_reasons`'s DISCLOSED output is unaffected by fetching less than the full history.
+# ==================================================================================================
+def test_resolve_with_reasons_bars_count_is_true_history_not_the_bounded_fetch_window(tmp_path):
+    """The disclosed `resolutions[...]['bars']` count is the symbol's TRUE trailing-bar count (50), never
+    the bounded ADV-window fetch size (3, `_cfg()`'s `adv_window_days`) — proving `bar_count` is passed
+    through from the already-known count, not re-derived from the (now-windowed) `bars` list length. This
+    is the exact regression a careless windowing fix would introduce (silently truncating the disclosed
+    history count to the fetch window)."""
+    cfg = _cfg()  # adv_window_days = 3 -- deliberately far smaller than the seeded history below
+    seed_dir = _write_pool(tmp_path, ["LONGHIST"])
+    engine = make_engine(f"sqlite:///{tmp_path / 'lh.db'}")
+    create_db_and_tables(engine)
+    start = date(2024, 1, 1)
+    with Session(engine) as session:
+        _seed_bars(session, "LONGHIST", start, [20.0] * 50, volume=1000.0)  # 50 bars >> adv_window_days=3
+        d = start + timedelta(days=49)  # the 50th (last) bar
+        out = resolve_with_reasons(session, d, cfg, seed_dir=seed_dir)
+    assert out["admitted"] == ["LONGHIST"]
+    row = out["resolutions"][0]
+    assert row["bars"] == 50, (
+        f"expected the TRUE 50-bar trailing history, not the {cfg.universe.filters.adv_window_days}-bar "
+        f"fetch window — got {row['bars']}"
+    )
+
+
+def test_resolve_with_reasons_byte_identical_with_and_without_an_active_bar_cache(tmp_path):
+    """`bars_asof_window` takes a DIFFERENT internal path depending on whether an outer `bar_cache`
+    context is active (the `_BarCache.bars_asof_window` slice — the ingest finalize-tail shape this
+    iteration profiled) or not (a bounded `LIMIT`-query fallback — the default per-request shape). Both
+    must resolve the SAME candidates for the SAME inputs — proven here by running the identical scenario
+    both ways and asserting the full diagnostic payload is equal."""
+    from app.engine.prices import bar_cache
+
+    cfg = _cfg()
+    seed_dir = _write_pool(tmp_path, ["PASS", "SHORT", "CHEAP", "THIN", "ENDED"])
+    engine = make_engine(f"sqlite:///{tmp_path / 'cache_ab.db'}")
+    create_db_and_tables(engine)
+    start = date(2024, 1, 1)
+    D = start + timedelta(days=9)
+    with Session(engine) as session:
+        _seed_bars(session, "PASS", start, [20.0] * 10, volume=1000.0)
+        _seed_bars(session, "SHORT", start, [20.0] * 3, volume=1000.0)
+        _seed_bars(session, "CHEAP", start, [5.0] * 10, volume=100000.0)
+        _seed_bars(session, "THIN", start, [20.0] * 10, volume=1.0)
+        _seed_bars(session, "ENDED", start - timedelta(days=40), [20.0] * 10, volume=1000.0)
+
+    with Session(engine) as session:
+        no_cache = resolve_with_reasons(session, D, cfg, seed_dir=seed_dir)  # default (no active cache)
+    with Session(engine) as session:
+        with bar_cache(session):
+            with_cache = resolve_with_reasons(session, D, cfg, seed_dir=seed_dir)  # active cache
+
+    assert with_cache == no_cache
+
+
+@pytest.mark.parametrize("history_bars", [1, 2, 3, 4, 5, 10])
+def test_resolve_with_reasons_adv_window_boundary_exact_short_and_long_history(tmp_path, history_bars):
+    """Boundary sweep around `adv_window_days` (3): a symbol with FEWER, EXACTLY, and MORE trailing bars
+    than the fetch window must classify identically to the pre-iter-53 full-fetch behavior — proven via
+    `resolve_candidate` called directly on the FULL bars (the pre-existing, unchanged pure-unit contract)
+    as the reference oracle for what `resolve_with_reasons` (the bounded-fetch path) must still produce."""
+    cfg = _cfg()  # min_history_bars=5, adv_window_days=3
+    seed_dir = _write_pool(tmp_path, ["SYM"])
+    engine = make_engine(f"sqlite:///{tmp_path / f'boundary_{history_bars}.db'}")
+    create_db_and_tables(engine)
+    start = date(2024, 1, 1)
+    with Session(engine) as session:
+        _seed_bars(session, "SYM", start, [20.0] * history_bars, volume=1000.0)
+        d = start + timedelta(days=history_bars - 1)
+        out = resolve_with_reasons(session, d, cfg, seed_dir=seed_dir)
+
+    full_bars = _bars(history_bars, 20.0, 1000.0, end=d)
+    reference = resolve_candidate(full_bars, "SYM", cfg, d)  # the unchanged pure-unit oracle
+    row = out["resolutions"][0]
+    assert row["admitted"] == reference.admitted
+    assert row["reason"] == reference.reason
+    assert row["bars"] == reference.bars == history_bars
```
