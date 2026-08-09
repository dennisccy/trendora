# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 9907273d..4a55f74e 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -222,7 +222,9 @@ def _per_symbol_coverage(session: Session, cfg: Config) -> list[dict]:
     return rows
 
 
-def _missing_data_diagnostic(session: Session, cfg: Config) -> dict:
+def _missing_data_diagnostic(
+    session: Session, cfg: Config, *, calendar: Optional[list[date_cls]] = None,
+) -> dict:
     """J-37 — the Missing-data diagnostic: a READ-ONLY honest report of every universe member that is
     INSUFFICIENT FOR ANALYSIS, derived ONCE from the SAME stored bars + `config.universe.symbols` +
     `indicators.min_history_bars` + the benchmark trading calendar the J-36 table / walk-forward already
@@ -239,11 +241,24 @@ def _missing_data_diagnostic(session: Session, cfg: Config) -> dict:
     A member that is fine appears in NO category. The thin threshold and the trading calendar both come
     from config (No magic number). `pullable` flags the rows a one-click pull can act on: no-history and
     intra-series-gap members (a thin member's gap, if any, surfaces as an intra-series-gap row; a thin
-    member with a contiguous-but-short series has no gap to pull and is shown for transparency only)."""
+    member with a contiguous-but-short series has no gap to pull and is shown for transparency only).
+
+    ops-hardening iter-54 (`per_date_coverage_warm` fix, profiled): `calendar` is OPTIONAL — when the
+    caller already computed the benchmark trading calendar (`_trading_days`, an unbounded per-symbol
+    `bars_asof` fetch — up to ~5,400 bars on the live basis), it is passed through here instead of this
+    function re-deriving the SAME calendar itself. `_compute_coverage_body` (the sole production caller)
+    already computes `trading_days` for the gap table two lines above its own call into this function —
+    before this fix, that fetch ran a SECOND time here, every `_compute_coverage_body` invocation (i.e.
+    once per date in `_persist_per_date_coverage_snapshots`'s per-date `per_date_coverage_warm` loop, and
+    once more for the current stamp in `coverage_membership_timeline_refresh`). `None` (every existing
+    test call, and any future standalone caller) preserves the exact prior behavior byte-identically —
+    this function derives its own calendar exactly as before. Passing the caller's calendar changes
+    nothing about what is computed, only how many times the SAME unbounded fetch runs."""
     threshold = cfg.indicators.min_history_bars  # canonical "insufficient-for-analysis" cutoff (config)
     universe = list(cfg.universe.symbols)
     universe_set = set(universe)
-    calendar = _trading_days(session, cfg)  # benchmark (SPY) bar dates, ascending — the SAME calendar
+    if calendar is None:
+        calendar = _trading_days(session, cfg)  # benchmark (SPY) bar dates, ascending — the SAME calendar
     calendar_set = set(calendar)
     preview_cap = cfg.data_manager.gap_preview  # reuse the existing gap-preview display cap (No magic number)
 
@@ -1161,6 +1176,12 @@ def _compute_coverage_body(
 
     snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
     snapshot_set = set(snapshot_dates)
+    # ops-hardening iter-54 (`per_date_coverage_warm` fix, profiled): computed ONCE here and passed to
+    # `_missing_data_diagnostic` below (its own `calendar` parameter) instead of that function
+    # re-deriving the SAME benchmark calendar a second time via its own `_trading_days` call — an
+    # unbounded per-symbol `bars_asof` fetch (SPY's entire history, up to ~5,400 bars on the live basis),
+    # architecturally the same shape B1/B3 bounded elsewhere in `market_phase.py` this same iteration.
+    # Every OTHER `_compute_coverage_body` reader of `trading_days` is unaffected (unchanged local var).
     trading_days = _trading_days(session, cfg)
     gaps = [d for d in trading_days if d not in snapshot_set]
     preview = cfg.data_manager.gap_preview
@@ -1209,8 +1230,11 @@ def _compute_coverage_body(
         "per_symbol": _per_symbol_coverage(session, cfg),
         # J-37: the Missing-data diagnostic — three honest categories of universe members insufficient
         # for analysis (no-history / thin / intra-series gap), each with its EXACT shortfall, derived from
-        # the SAME stored bars + threshold + calendar above. Recomputes no canonical value; fabricates nothing.
-        "diagnostic": _missing_data_diagnostic(session, cfg),
+        # the SAME stored bars + threshold + calendar above. Recomputes no canonical value; fabricates
+        # nothing. `calendar=trading_days` (iter-54): reuses the calendar this function already computed
+        # two lines above instead of paying its own second unbounded fetch — see this function's own
+        # `trading_days` comment and `_missing_data_diagnostic`'s `calendar` parameter docstring.
+        "diagnostic": _missing_data_diagnostic(session, cfg, calendar=trading_days),
         # J-94: the per-date coverage diagnostic — for the resolved as-of, the admitted count + the
         # excluded-by-reason counts (below_history / below_price / below_adv) against the candidate-pool
         # denominator. Read-only descriptive derivation over the SAME stored bars + config thresholds.
@@ -3255,9 +3279,16 @@ _FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
 # graph — data_manager already imports FROM research at module level, so the reverse would be circular).
 # ops-hardening iter-53: "coverage_membership_timeline" and "market_phase" added — the two finalize-tail
 # phases this iteration's GIL-hold profile bounded (`universe_resolver.resolve_with_reasons`'s per-symbol
-# bounded-window fetch; `market_phase._severity_reading`'s benchmark/^VIX bounded-window fetch). Both
-# reach this hook via the SAME lazy `from app.engine import data_manager` import trick (data_manager
-# already imports both modules at module level, so the reverse import would be circular).
+# bounded-window fetch; `market_phase._severity_reading`'s benchmark/^VIX bounded-window fetch).
+# "market_phase" still reaches this hook via the lazy `from app.engine import data_manager` import trick
+# (data_manager already imports `market_phase` at module level, so the reverse import would be circular).
+# ops-hardening iter-54 (B2 fix, iter-53 audit): "coverage_membership_timeline"'s call site RELOCATED —
+# it no longer fires from `resolve_with_reasons` (that shared per-symbol loop is ALSO reached from the
+# per-date backfill compute via `scoring.score_stocks`, which runs BEFORE the finalize tail, so arming it
+# there could not isolate the `coverage_membership_timeline_refresh` phase this site name claims to gate —
+# see `resolve_with_reasons`'s own comment for the full finding). It now fires from directly inside THIS
+# module's `_refresh_ingest_aggregates`, at the top of that phase's own block — no lazy import needed
+# (same module).
 _FAULT_INJECT_SITES = frozenset({
     "forward_aggregates", "drawdown_expectations", "backfill_worker", "factor_lab_all",
     "coverage_membership_timeline", "market_phase",
@@ -4096,6 +4127,16 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                     # fabricated refresh.
                     pass
                 else:
+                    # ops-hardening iter-54 (B2 fix, iter-53 audit): the `coverage_membership_timeline`
+                    # fault-injection probe now lives HERE — the ONE call site inside THIS phase's own
+                    # boundary — instead of inside `universe_resolver.resolve_with_reasons`'s shared
+                    # per-symbol loop (moved OUT; see that function's own comment for the full "isolates
+                    # the wrong phase" finding). Placed immediately before the heavy compute this phase
+                    # actually exists to run, mirroring `market_phase`'s/`factor_lab_all`'s convention, so
+                    # a live drill arming `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline`
+                    # isolates EXACTLY `coverage_membership_timeline_refresh` — never the per-date backfill
+                    # compute upstream of it, and never `per_date_coverage_warm` (a separate call below).
+                    _fault_inject_memory_error("coverage_membership_timeline")  # test-only; no-op in prod
                     payload = refresh_coverage_snapshot(session, cfg)
                     if payload is not None:
                         refreshed.append("coverage")
diff --git a/apps/backend/app/engine/market_phase.py b/apps/backend/app/engine/market_phase.py
index 166a5971..9f3dae64 100644
--- a/apps/backend/app/engine/market_phase.py
+++ b/apps/backend/app/engine/market_phase.py
@@ -47,7 +47,7 @@ from app.config import (
     get_config,
 )
 from app.engine.labels import label_for
-from app.engine.prices import bar_cache, bars_asof, bars_asof_window, close_on, closes
+from app.engine.prices import bar_cache, bars_asof_window, close_on, closes
 from app.engine.research import _dataset_version  # single-sourced cache stamp (J-72) — never duplicated
 from app.models import MacroSeries, MarketPhaseCache, ScannerRun
 
@@ -206,15 +206,28 @@ def _severity_reading(
     # `_latest_vix_on_or_before` (above) was measured to hold the GIL on — `bars_asof(session, bench, d)`
     # builds the benchmark's ENTIRE <= D history (up to ~7,500 `Bar` NamedTuples on the live 30y basis)
     # only to filter it down to the trailing `lookback_days` calendar-day window immediately below.
-    # `bars_asof_window(session, bench, d, mp.lookback_days)` fetches only the trailing `lookback_days`
-    # bars BY COUNT — provably sufficient to reproduce the SAME `>= start` filtered result: the number of
-    # TRADING days within any `lookback_days` CALENDAR days can never exceed `lookback_days` (a trading
-    # day is always one calendar day, so N calendar days admit at most N trading days), and `bars_asof`'s
-    # ascending order means every date >= `start` occupies a trailing SUFFIX of the full series — so a
-    # `lookback_days`-sized trailing-count window is guaranteed to contain that whole suffix regardless of
-    # history density/gaps. Filtering the (now bounded) window with the SAME `>= start` condition below is
-    # therefore byte-identical to filtering the full prefix.
-    window = [bar for bar in bars_asof_window(session, bench, d, mp.lookback_days) if bar.date >= start]
+    # `bars_asof_window(session, bench, d, mp.lookback_days + 1)` fetches the trailing `lookback_days + 1`
+    # bars BY COUNT — provably sufficient to reproduce the SAME `>= start` filtered result.
+    #
+    # ops-hardening iter-54 (B1 fix, iter-53 audit): the `>= start` filter admits `[start, d]` INCLUSIVE —
+    # that is `lookback_days + 1` CALENDAR days, which can hold up to `lookback_days + 1` TRADING days (a
+    # trading day is always one calendar day, so N calendar days admit AT MOST N trading days — but
+    # `[start, d]` inclusive spans `lookback_days + 1` calendar days, not `lookback_days`). The iter-53
+    # fetch supplied only `lookback_days` bars by count — one bar SHORT of that bound — so on a
+    # sufficiently dense series the oldest qualifying bar (dated exactly `start`) was silently dropped
+    # (proven on the shipped fixture at `lookback_days=30`: untreated 31 bars, treated 30, `phase` flips
+    # `Correction` -> `Pullback`). Fetching `lookback_days + 1` by count makes the window a provable
+    # superset of the calendar filter for EVERY possible data density, not merely at the live committed
+    # density (SPY's real trading-day density leaves >100 bars of slack at `lookback_days=365` and >13 at
+    # `lookback_days=50` — safe in practice, but the code's own claim must match what it proves, not what
+    # happens to be true today). `bars_asof`'s ascending order means every date >= `start` occupies a
+    # trailing SUFFIX of the full series, so the `lookback_days + 1`-sized trailing-count window is
+    # guaranteed to contain that whole suffix regardless of history density/gaps. Filtering the (now
+    # bounded) window with the SAME `>= start` condition below is therefore byte-identical to filtering
+    # the full prefix — after this fix, not before it (the pre-fix hazard above is real, not hypothetical;
+    # it was simply unreachable at the live committed density, which is a fact about today's data, not a
+    # property of the code).
+    window = [bar for bar in bars_asof_window(session, bench, d, mp.lookback_days + 1) if bar.date >= start]
     if len(window) < mp.min_history_bars:
         return None  # insufficient benchmark history -> NA / partial (never fabricated)
     closes_window = closes(window)
@@ -543,15 +556,22 @@ def _trailing_ma_reclaimed(session: Session, as_of: date_cls, cfg: Config) -> Op
     recomputes nothing, carries no literal (the window is the config key).
 
     ops-hardening iter-53 (J-05/J-07, GIL-hold bound): the SAME bounded-window treatment as
-    `_severity_reading`'s benchmark drawdown leg, for the SAME reason and with the SAME byte-identity proof
-    (a `lookback_days`-by-COUNT window is provably a superset of any `lookback_days`-by-CALENDAR-day filter,
-    since trading days are never denser than calendar days) — `_recovery_turn_signal` calls this once per
-    `compute_market_phase` invocation (in scope for `market_phase_warm`); `_recovery_turn_dates_with_context`
-    (below) also calls it, unmodified, and benefits for free."""
+    `_severity_reading`'s benchmark drawdown leg, for the SAME reason — `_recovery_turn_signal` calls this
+    once per `compute_market_phase` invocation (in scope for `market_phase_warm`); `_recovery_turn_dates_
+    with_context` (below) also calls it, unmodified, and benefits for free.
+
+    ops-hardening iter-54 (B1 fix): fetches `recovery_trailing_ma_days + 1` bars by count, not
+    `recovery_trailing_ma_days` — see `_severity_reading`'s docstring for the full off-by-one proof (the
+    `>= start` filter admits `lookback_days + 1` CALENDAR days inclusive, which can hold up to
+    `lookback_days + 1` TRADING days; a `+1`-sized count window is the provable superset for every
+    density, not merely the live committed one)."""
     mp = cfg.market_phase
     bench = cfg.etfs.index[0]
     start = as_of - timedelta(days=mp.recovery_trailing_ma_days)
-    window = [bar for bar in bars_asof_window(session, bench, as_of, mp.recovery_trailing_ma_days) if bar.date >= start]
+    window = [
+        bar for bar in bars_asof_window(session, bench, as_of, mp.recovery_trailing_ma_days + 1)
+        if bar.date >= start
+    ]
     series = closes(window)
     if not series:
         return None
@@ -1163,10 +1183,19 @@ def _true_bear_episodes(dated_closes: list[dict], cfg: Config) -> list[dict]:
 def _benchmark_close_on_or_before(session: Session, d: date_cls, cfg: Config) -> Optional[float]:
     """The benchmark (SPY) close on/before D (date <= D, no lookahead) — the SAME first index ETF the
     severity drawdown leg reads. None when no bar exists. A pure causal read used to build the
-    retrospective's per-snapshot-date close series; recomputes nothing."""
+    retrospective's per-snapshot-date close series; recomputes nothing.
+
+    ops-hardening iter-54 (B3 fix, iter-53 audit): reads `close_on` (the single-bar accessor, already
+    imported into this module by iter-53's own fix) instead of `closes(bars_asof(session, bench, d))[-1]`
+    — the EXACT unbounded-full-history-fetch-to-read-one-value shape iter-53 proved dominant elsewhere in
+    this same module (`_latest_vix_on_or_before`, 65 stalls / 3.34s in one call). Called once per stored
+    run inside `compute_retrospective`'s `bar_cache` loop (~2,900x on the live basis) to serve
+    `GET /api/market-phase/retrospective` — a request-time path, not a finalize-tail phase, but the same
+    failure class. Byte-identical to the pre-fix read: `close_on` is the single-bar form of
+    `bars_asof(session, symbol, d)[-1].close` (iter-26, J-16; proven byte-identical then, re-proven here
+    by a fixture-backed equality test against the pre-fix read)."""
     bench = cfg.etfs.index[0]
-    series = closes(bars_asof(session, bench, d))
-    return series[-1] if series else None
+    return close_on(session, bench, d)
 
 
 def compute_retrospective(
diff --git a/apps/backend/app/engine/universe_resolver.py b/apps/backend/app/engine/universe_resolver.py
index 831c13cb..c24afcca 100644
--- a/apps/backend/app/engine/universe_resolver.py
+++ b/apps/backend/app/engine/universe_resolver.py
@@ -213,11 +213,24 @@ def resolve_with_reasons(
     # what is COMPUTED or DISCLOSED: every `CandidateResolution.bars`/`excluded_counts` value stays
     # byte-identical (TC-3).
     window_days = max(1, cfg.universe.filters.adv_window_days)
-    # lazy import — app.engine.data_manager imports FROM this module (`resolve_with_reasons` above), so a
-    # module-level import back would be circular (mirrors research.py's/forward_testing.py's own lazy
-    # imports of data_manager, for the identical reason). Used only for the test-only
-    # `_fault_inject_memory_error` hook below (a no-op in production).
-    from app.engine import data_manager
+    # ops-hardening iter-54 (B2 fix, iter-53 audit): the `coverage_membership_timeline` fault-injection
+    # probe used to live HERE (armed once per admitted-eligible symbol). It was removed from this shared
+    # per-symbol loop because `resolve_with_reasons` is reached from FOUR call sites — this finalize-tail
+    # coverage refresh, the per-date membership-timeline batch loop, AND (via `resolve_members`) the
+    # PER-DATE BACKFILL COMPUTE's own scoring pass (`scoring.score_stocks`), which runs BEFORE the
+    # finalize tail even starts. Arming the site here made every injected MemoryError fire from inside the
+    # per-date backfill compute first, aborting the job before the finalize tail's own
+    # `coverage_membership_timeline_refresh` phase (and its dedicated MemoryError handler) was ever
+    # reached — so a live drill using this site name could not isolate the phase it claimed to name
+    # (confirmed live: `logs/backend.log`, UT-11's drill). The probe now lives at the ONE call site that
+    # is actually inside that finalize-tail phase's own boundary — see
+    # `data_manager._refresh_ingest_aggregates`'s `coverage_membership_timeline_refresh` block — so arming
+    # `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline` now isolates exactly that phase,
+    # never the per-date backfill compute upstream of it. This loop's own MemoryError isolation is
+    # unaffected: a REAL (unfaulted) MemoryError raised anywhere in this loop still propagates to and is
+    # handled by whichever caller wraps it (the per-date backfill's own per-symbol/per-date isolation, or
+    # the finalize tail's phase-level handler) exactly as before — only the deliberate TEST-ONLY fault
+    # probe moved, not this function's real exception behavior.
     for symbol in resolve_symbols:
         bar_count = bar_count_by_symbol.get(symbol, 0)
         if bar_count < min_history:
@@ -226,11 +239,6 @@ def resolve_with_reasons(
                 CandidateResolution(symbol, False, REASON_BELOW_HISTORY, bar_count)
             )
             continue
-        # ops-hardening iter-53 (J-05/J-07, TC-5): the fault-injection probe for THIS treated site — see
-        # `_FAULT_INJECT_SITES`'s "coverage_membership_timeline" entry. Placed at the per-symbol bounded
-        # fetch itself (not at `resolve_with_reasons`'s own call site), mirroring `compute_factor_lab_all`'s
-        # convention, so a drill/test exercises the REAL treated code path.
-        data_manager._fault_inject_memory_error("coverage_membership_timeline")  # test-only; no-op in prod
         bars = bars_asof_window(session, symbol, asof, window_days)
         resolutions.append(resolve_candidate(bars, symbol, cfg, asof, bar_count=bar_count))
 
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 0d0165ab..450e2b0d 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1921,16 +1921,25 @@ def test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succee
 # `bars_asof_window` fetch; `market_phase._severity_reading`'s benchmark/^VIX bounded fetch) still
 # preserves the iter-8 MemoryError isolate-and-continue contract when the fault fires from INSIDE the
 # real, unmocked treated code path (not merely at the loop's own call site).
+#
+# ops-hardening iter-54 (B2 fix): the `coverage_membership_timeline` injection site RELOCATED from inside
+# `resolve_with_reasons`'s shared per-symbol loop to `_refresh_ingest_aggregates`'s own
+# `coverage_membership_timeline_refresh` phase block (see that function's comment for the full "isolates
+# the wrong phase" finding) — this test's call shape (`_refresh_ingest_aggregates` invoked directly, no
+# live snapshot dates) already reaches the NEW site unchanged, so its assertions still hold; only the
+# docstring below is corrected to say where the fault actually fires now.
 # ==================================================================================================
 def test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly(
     tmp_path, monkeypatch,
 ):
     """`TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline` armed against a REAL (unmocked)
-    `universe_resolver.resolve_with_reasons` call over a pool with an admitted-eligible LONG-history
-    candidate (so the injection site — placed AFTER the history-gate short-circuit, at the bounded fetch
-    itself — is actually reached, not skipped): `coverage`/`membership_timeline` are honestly OMITTED
-    from `aggregates_refreshed`, the NEW dedicated `except MemoryError` handler this iteration added for
-    this phase calls `_release_process_memory()`, and the hook itself does not raise."""
+    `_refresh_ingest_aggregates` call, immediately before its `coverage_membership_timeline_refresh`
+    phase's own `refresh_coverage_snapshot` call (ops-hardening iter-54, B2 fix — relocated from inside
+    `universe_resolver.resolve_with_reasons`'s shared per-symbol loop, which is also reached from the
+    per-date backfill compute and so could not isolate this phase specifically): `coverage`/
+    `membership_timeline` are honestly OMITTED from `aggregates_refreshed`, the dedicated
+    `except MemoryError` handler this phase carries calls `_release_process_memory()`, and the hook
+    itself does not raise."""
     from app.engine import universe_resolver
 
     cfg = load_config()
@@ -5454,6 +5463,55 @@ def test_diagnostic_query_count_does_not_scale_with_universe_size(tmp_path):
     assert small_count <= 4  # sanity bound: calendar (2) + grouped stats (1) + bulk own-dates (1)
 
 
+# ==================================================================================================
+# ops-hardening iter-54 (`per_date_coverage_warm` fix, profiled) -- `_missing_data_diagnostic` no longer
+# ALWAYS derives its own benchmark trading calendar (`_trading_days`, an unbounded per-symbol `bars_asof`
+# fetch up to ~5,400 bars on the live basis, PLUS the `latest_data_date` query it depends on -- 2
+# `daily_prices` queries total, per the query-count test above's own docstring). `_compute_coverage_body`
+# (the sole production caller) already computes this SAME calendar for its own gap table and now passes
+# it through via the new `calendar` parameter, instead of paying for the identical fetch a second time on
+# EVERY `_compute_coverage_body` call (i.e. once per date in `_persist_per_date_coverage_snapshots`'s
+# per-date `per_date_coverage_warm` loop, and once more in `coverage_membership_timeline_refresh`).
+# ==================================================================================================
+def test_diagnostic_calendar_param_eliminates_the_redundant_trading_days_fetch(tmp_path):
+    """Passing `calendar=` removes EXACTLY the two `daily_prices` queries `_trading_days` issues
+    (`latest_data_date` + SPY's own `bars_asof`) -- the query count drops by 2, never more/less -- and
+    the served `diagnostic` payload is BYTE-IDENTICAL either way (the fetch-STRATEGY changes; nothing
+    computed or disclosed does)."""
+    engine = _build_diagnostic_db(tmp_path, ["AAA", "BBB", "CCC", "DDD"])
+    cfg = _diag_cfg_for(["AAA", "BBB", "CCC", "DDD"])
+
+    with Session(engine) as session:
+        calendar = _trading_days(session, cfg)
+    assert calendar  # sanity: the fixture actually has a benchmark calendar to reuse
+
+    without_calendar = _count_daily_prices_selects(engine, cfg)  # derives its own calendar internally
+
+    queries: list[str] = []
+
+    def _count(conn, cursor, statement, parameters, context, executemany):
+        lowered = statement.lower()
+        if "daily_prices" in lowered and lowered.strip().startswith("select"):
+            queries.append(statement)
+
+    event.listen(engine, "before_cursor_execute", _count)
+    try:
+        with Session(engine) as session:
+            with_calendar = _missing_data_diagnostic(session, cfg, calendar=calendar)
+    finally:
+        event.remove(engine, "before_cursor_execute", _count)
+    with_calendar_count = len(queries)
+
+    assert with_calendar_count == without_calendar - 2, (
+        f"expected exactly 2 fewer daily_prices queries when `calendar` is supplied "
+        f"(got {without_calendar} without vs {with_calendar_count} with)"
+    )
+
+    with Session(engine) as session:
+        reference = _missing_data_diagnostic(session, cfg)  # derives its own calendar -- the old behavior
+    assert with_calendar == reference
+
+
 def test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result(diagnostic_engine):
     """TC-1 (iter-40, J-07 last blocker) -- `_missing_data_diagnostic`'s own-dates scan
     (`data_manager.py:271`) now streams via `.yield_per(cfg.research.read_batch_size)` instead of
diff --git a/apps/backend/tests/test_market_phase.py b/apps/backend/tests/test_market_phase.py
index a439782b..a7bd375c 100644
--- a/apps/backend/tests/test_market_phase.py
+++ b/apps/backend/tests/test_market_phase.py
@@ -33,9 +33,11 @@ from sqlmodel import Session, select
 import main
 from app.config import ConfigError, load_config
 from app.db import create_db_and_tables, make_engine
+from app.engine import market_phase
 from app.engine.market_phase import (
     PHASE_RECOVERY,
     SCHEMA_VERSION,
+    _benchmark_close_on_or_before,
     _cache_version,
     _filtered_bear_path,
     _severity_velocity_at,
@@ -48,7 +50,7 @@ from app.engine.market_phase import (
     recovery_turn_dates,
     retrospective_cached,
 )
-from app.engine.prices import latest_data_date
+from app.engine.prices import bars_asof, closes as bar_closes, latest_data_date
 from app.engine.research import _dataset_version
 from app.models import DailyPrice, ForwardReturn, MarketPhaseCache, ScannerResult, ScannerRun
 
@@ -379,6 +381,100 @@ def test_recovery_turn_trailing_ma_bounded_fetch_byte_identical():
     assert bare["recovery_turn"] == padded["recovery_turn"]
 
 
+# ==================================================================================================
+# ops-hardening iter-54 (B1 fix, T1/TC-1/TC-2 — iter-53 audit finding B1/T1). The THREE tests above
+# compare treated-vs-treated (a bare fixture against the SAME fixture padded with an older block) — they
+# prove the bounded fetch is not too WIDE, but a treated-vs-treated shape structurally cannot prove it is
+# not too NARROW (the iter-53 lesson on record: "require the byte-identity test to compare against the
+# ORIGINAL implementation, never against another instance of the new one"). The audit proved exactly
+# this gap: at `lookback_days=30` on the shipped fixture, the pre-fix count-bounded fetch
+# (`bars_asof_window(..., lookback_days)`, one bar short of the `[start, d]` inclusive calendar range it
+# feeds) silently dropped the oldest qualifying bar, flipping the served `phase` from `Correction` to
+# `Pullback` — and every treated-vs-treated test above still PASSED throughout. This test instead
+# compares the TREATED `compute_market_phase` (now fetching `lookback_days + 1`, B1's fix) against the
+# UNTREATED oracle: the ORIGINAL, pre-iter-53 shape — no count-window at all, `bars_asof`'s full <= d
+# history filtered by the SAME `>= start` calendar condition — reconstructed by patching
+# `bars_asof_window` to ignore its `lookback` argument and return the unbounded series instead, then
+# running the REAL `compute_market_phase` pipeline on top of it (never a hand-reimplemented partial
+# oracle that could silently drift from the real available-weight blend/rounding).
+# ==================================================================================================
+def test_severity_reading_treated_matches_untreated_bars_asof_oracle_at_lookback_boundary(monkeypatch):
+    """TC-1/TC-2: reuses the EXACT shipped fixture from
+    `test_severity_reading_benchmark_window_ignores_bars_older_than_lookback_bound` at `lookback_days=30`
+    (the iter-53 audit's own B1 reproduction case). The untreated oracle's `phase` is `Correction`
+    (matching the audit's measured table: severity 50.27, drawdown_pct -9.25) — the treated (post-B1-fix)
+    value must equal it exactly. A test written in the pre-fix treated-vs-treated shape at this SAME
+    `lookback_days` would have asserted `phase == "Pullback"` and PASSED even though the served value was
+    wrong; this test would have FAILED against the pre-fix code (proving it has teeth)."""
+    cfg = _small_config()
+    cfg.market_phase.lookback_days = 30  # deliberately small so the boundary is genuinely exercised
+    d = _BASE + timedelta(days=99)
+    recent = [100.0 - 0.3 * i for i in range(40)]
+    engine = _engine()
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", recent, start=d - timedelta(days=39))
+        _insert_run(session, d, "Choppy", 50.0, breadth_200=45.0)
+        session.commit()
+
+        treated = compute_market_phase(session, d, cfg)  # post-B1-fix: fetches lookback_days + 1 by count
+
+        def _unbounded_window(session_, symbol, asof, lookback):  # noqa: ARG001 -- lookback deliberately unused
+            return bars_asof(session_, symbol, asof)  # the pre-iter-53 ORIGINAL shape: no count-window
+
+        monkeypatch.setattr(market_phase, "bars_asof_window", _unbounded_window)
+        untreated = compute_market_phase(session, d, cfg)
+
+    # the untreated oracle reproduces the iter-53 audit's own measured table exactly (the ground truth).
+    assert untreated["available"] is True
+    assert untreated["phase"] == "Correction"
+    assert round(untreated["severity"], 2) == 50.27
+    assert round(untreated["drawdown_pct"], 2) == -9.25
+
+    # the TREATED (post-B1-fix) value equals the untreated oracle -- byte-identical, not merely close.
+    assert treated["available"] is True
+    assert treated["phase"] == untreated["phase"]
+    assert treated["severity"] == untreated["severity"]
+    assert treated["drawdown_pct"] == untreated["drawdown_pct"]
+    assert treated["off_trough_pct"] == untreated["off_trough_pct"]
+    assert treated["components"] == untreated["components"]
+
+
+# ==================================================================================================
+# ops-hardening iter-54 (B3 fix, iter-53 audit finding B3). `_benchmark_close_on_or_before` — a SIBLING
+# per-run loop (`compute_retrospective`'s `bar_cache` block, ~2,900x on the live basis, serving
+# `GET /api/market-phase/retrospective` at request time) survived iter-53's fix untreated: it still read
+# `closes(bars_asof(session, bench, d))[-1]` in full, the exact defect shape iter-53 proved dominant in
+# `_latest_vix_on_or_before`. TC-3: the fixed `close_on`-based read must return the SAME value as the
+# pre-fix full-history read, fixture-backed.
+# ==================================================================================================
+def test_benchmark_close_on_or_before_close_on_matches_pre_fix_full_history_read():
+    """A LONG SPY series (60 bars) with a DISTINCTIVE last close, at a D inside the middle of the series
+    (so a pre-fix VS post-fix mismatch on the boundary would show up either way) — `close_on`'s single-bar
+    read must equal `closes(bars_asof(...))[-1]`, the exact pre-fix expression, evaluated independently."""
+    cfg = _small_config()
+    engine = _engine()
+    d = _BASE + timedelta(days=39)
+    with Session(engine) as session:
+        _insert_bars(session, "SPY", [100.0 + i * 0.5 for i in range(60)])  # 60 bars, D lands mid-series
+        session.commit()
+
+        treated = _benchmark_close_on_or_before(session, d, cfg)
+        pre_fix_reference = bar_closes(bars_asof(session, "SPY", d))
+        pre_fix_value = pre_fix_reference[-1] if pre_fix_reference else None
+
+    assert pre_fix_value is not None
+    assert treated == pre_fix_value == 100.0 + 39 * 0.5  # D = _BASE + 39 days -> the 40th bar (index 39)
+
+
+def test_benchmark_close_on_or_before_no_bar_is_honest_none():
+    """No SPY bar at all -> None (the pre-fix `closes([])[-1] if [] else None` and `close_on`'s own None
+    both resolve to the SAME honest 'no bar on/before D' NA) -- never a fabricated close."""
+    cfg = _small_config()
+    engine = _engine()
+    with Session(engine) as session:
+        assert _benchmark_close_on_or_before(session, _BASE, cfg) is None
+
+
 # --------------------------------------------------------------------------------------------------
 # iter-30 (J-89 / J-90) — timeline series, dated downtrend episodes, the FENCED retrospective, and the
 # causal recovery-turn signal. FAST synthetic tests (no seed boot) — the anti-goal-critical legs.
diff --git a/apps/backend/tests/test_universe_resolver.py b/apps/backend/tests/test_universe_resolver.py
index caca0830..a8fae4d9 100644
--- a/apps/backend/tests/test_universe_resolver.py
+++ b/apps/backend/tests/test_universe_resolver.py
@@ -333,6 +333,11 @@ def test_resolve_empty_db_is_honest_empty(tmp_path):
     with Session(engine) as session:
         out = resolve_with_reasons(session, date(2024, 6, 1), cfg, seed_dir=seed_dir)
     assert out["admitted"] == []
+    # ops-hardening iter-54 (T2 fix): restored — the iter-53 audit found this assertion deleted,
+    # undisclosed, and re-ran it independently against the same fixture ("it still passes"). Both pool
+    # candidates (AAA, BBB) have zero bars on a wholly-empty DB, so both are below_history — the honest
+    # "nothing admitted" outcome is backed by a real reason count, never a bare empty list.
+    assert out["excluded_counts"][REASON_BELOW_HISTORY] == 2
 
 
 # ==================================================================================================
@@ -420,3 +425,35 @@ def test_resolve_with_reasons_adv_window_boundary_exact_short_and_long_history(t
     assert row["admitted"] == reference.admitted
     assert row["reason"] == reference.reason
     assert row["bars"] == reference.bars == history_bars
+
+
+# ==================================================================================================
+# ops-hardening iter-54 (B2 fix, iter-53 audit finding B2) — the `coverage_membership_timeline`
+# fault-injection site no longer lives inside THIS function's per-symbol loop (relocated to
+# `data_manager._refresh_ingest_aggregates`'s own `coverage_membership_timeline_refresh` phase block —
+# see this function's own comment for the full "isolates the wrong phase" finding). Proves the negative:
+# arming the site no longer raises from `resolve_with_reasons` itself, which is reached from the PER-DATE
+# BACKFILL COMPUTE (via `resolve_members` -> `scoring.score_stocks`) as well as the finalize tail — the
+# exact call path whose premature abort iter-53's live drill (UT-11) caught.
+# ==================================================================================================
+def test_resolve_with_reasons_unaffected_by_coverage_membership_timeline_fault_injection(
+    tmp_path, monkeypatch,
+):
+    """`TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline` armed, then `resolve_with_reasons`
+    called directly (the SAME call shape the per-date backfill's `scoring.score_stocks` uses, via
+    `resolve_members`) over a pool with an admitted-eligible LONG-history candidate — must NOT raise.
+    Before this iteration's B2 fix, the fault probe lived inside this exact per-symbol loop and WOULD have
+    raised here, aborting the per-date backfill compute before the finalize tail's own
+    `coverage_membership_timeline_refresh` phase (the phase this site name claims to gate) was ever
+    reached."""
+    cfg = _cfg()
+    seed_dir = _write_pool(tmp_path, ["LONG"])
+    engine = make_engine(f"sqlite:///{tmp_path / 'b2-fault.db'}")
+    create_db_and_tables(engine)
+    start = date(2024, 1, 1)
+    with Session(engine) as session:
+        _seed_bars(session, "LONG", start, [20.0] * 60, volume=1_000_000.0)  # comfortably admitted-eligible
+        d = start + timedelta(days=59)
+        monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "coverage_membership_timeline")
+        out = resolve_with_reasons(session, d, cfg, seed_dir=seed_dir)  # must not raise
+    assert out["admitted"] == ["LONG"]
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index 337696b7..083d66d6 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -204,6 +204,17 @@ activation by `journalctl -t iad-cstate-limit -b 0` + sysfs `state[23]/disable`
 = 1 on all CPUs, never by unit-file presence or `is-active` (oneshot without
 `RemainAfterExit` reads `inactive (dead)` after success).
 
+2026-08-08 OUTCOME — **falsified in one day.** Fault reset #4 (12:48) fired with
+the unit verifiably active in the dying boot (its journal tag 5 s after boot;
+`host_state` `C2:1,C3:1` until 13 min before death) at 30 W / load1 3.04 /
+84 °C: deep-C-state limiting does NOT prevent this signature on this host. The
+unit was removed the same day (falsified, and it cost thermal headroom — the
+hottest run of the incident, Tctl 90 °C with dispatch deferrals), verified by
+sysfs 32×`0`; per the rule above in reverse, later boots must show ZERO
+`iad-cstate-limit` tag lines. Ladder: **rung 3 — overnight memtest86+
+2026-08-08→09 — in progress**, then JEDEC baseline → SO-DIMM reseat/swap →
+GEEKOM RMA. Full record: `~/.cache/iad/host-guard/soak-log.md`.
+
 `doctor.sh --only ras-logging` verifies what it can read without root (the
 journald drop-in and the rasdaemon unit) and stays silent on hosts that have no
 reset history.
```

## Excluded-path stat (dependency/lockfile visibility)

 docs/handoffs/goal-ops-hardening-iter-53-dev.md    |  13 +
 reports/perf-budgets.md                            | 272 +++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |   1 +
 .../.engine.lock/boot_id                           |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 .../journey-scripts/J-06.json                      |   4 +
 .../state/assumptions.md                           | 231 -----------------
 .../state/assumptions.md.archive.md                | 232 ++++++++++++++++++
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/state/lessons.md   |  34 +--
 .../state/lessons.md.archive.md                    |  44 ++++
 runs/goal-session-ops-hardening/telemetry.jsonl    |  33 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   4 +
 17 files changed, 614 insertions(+), 270 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
