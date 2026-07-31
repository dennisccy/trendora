# Iteration diff (bounded)

Files changed: 23. Shown in full: 23.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 76a84e49..08b63ea3 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -2079,6 +2079,13 @@ class JobProgress:
     # written onto this job's OPEN run-history row (NOT serialized — internal throttle scratch, like the
     # two accumulators above). 0.0 means "never checkpointed", so the first advance always writes.
     _last_checkpoint_monotonic: float = 0.0
+    # ops-hardening iter-41 (D9, dev Known Issue #2 from iter-40's own handoff) — dates completed since
+    # the last durable checkpoint write (NOT serialized — internal throttle scratch, like
+    # `_last_checkpoint_monotonic` above). The time-based throttle alone (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`)
+    # lets an extremely fast per-date compute (iter-40's live drill observed ~120-140 ms/date bursts) run
+    # several dates between checkpoints; this count-based floor (see `_RUN_RECORD_CHECKPOINT_DATE_FLOOR`)
+    # forces a write on every Kth date regardless of elapsed time, bounding the OTHER axis of staleness.
+    _dates_since_checkpoint: int = 0
 
     def tick(self, activity: Optional[str] = None) -> None:
         """J-66 — stamp the last-progress HEARTBEAT (and optionally the current-activity line) on a
@@ -4084,6 +4091,17 @@ def _has_open_run_record(engine: Engine, job_id: Optional[str]) -> bool:
 # would buy nothing); write amplification stays bounded to at most one UPDATE per second per running job.
 _RUN_RECORD_CHECKPOINT_INTERVAL_S = 1.0
 
+# ops-hardening iter-41 (D9, dev Known Issue #2 from iter-40's own handoff) — a COUNT-based floor added
+# to the time-based throttle above: even an EXTREMELY fast per-date compute (iter-40's own live drill
+# observed a burst rate of ~120-140 ms/date, well under the 1.0s interval) forces a durable checkpoint
+# write at least once every this-many completed dates, regardless of how little wall-clock time has
+# elapsed. Same throttled writer, same `message` field, same `_run_detail()` serializer — this only
+# widens WHEN a write is forced, never what gets written. 5 mirrors the density iter-40's own tightened
+# 1.0s interval already achieves at a typical ~1-2.5s/date rate (roughly one checkpoint every 1-2 dates
+# there); at a pathologically fast sub-200ms/date rate this floor caps the worst-case staleness at 5
+# dates instead of the ~5-8 dates the time-only throttle would otherwise allow (1.0s / 0.14s ~= 7).
+_RUN_RECORD_CHECKPOINT_DATE_FLOOR = 5
+
 
 def _checkpoint_run_record(engine: Engine, prog: JobProgress) -> None:
     """ops-hardening iter-9 (F1 — J-04 step 6): freeze the job's CURRENT progress onto its OPEN
@@ -4100,13 +4118,20 @@ def _checkpoint_run_record(engine: Engine, prog: JobProgress) -> None:
     already serialize — one representation, no second derivation). It never sets `status`/`finished_at`,
     so the row stays OPEN and the boot sweep can still claim it, and it never INSERTs — a job with no open
     row (already terminal) is a silent no-op. Throttled to one write per
-    `_RUN_RECORD_CHECKPOINT_INTERVAL_S`. Best-effort telemetry: a write failure is logged and swallowed,
-    never propagated into the backfill loop (the job's own outcome must not depend on its progress
+    `_RUN_RECORD_CHECKPOINT_INTERVAL_S` — OR forced on every `_RUN_RECORD_CHECKPOINT_DATE_FLOOR`th call
+    regardless of elapsed time (ops-hardening iter-41, D9: the time-based throttle alone lets an
+    extremely fast per-date compute run several dates between writes; this count-based floor bounds that
+    OTHER axis of staleness). Best-effort telemetry: a write failure is logged and swallowed, never
+    propagated into the backfill loop (the job's own outcome must not depend on its progress
     bookkeeping)."""
     now = time.monotonic()
-    if (now - prog._last_checkpoint_monotonic) < _RUN_RECORD_CHECKPOINT_INTERVAL_S:
+    prog._dates_since_checkpoint += 1
+    time_due = (now - prog._last_checkpoint_monotonic) >= _RUN_RECORD_CHECKPOINT_INTERVAL_S
+    count_due = prog._dates_since_checkpoint >= _RUN_RECORD_CHECKPOINT_DATE_FLOOR
+    if not time_due and not count_due:
         return
     prog._last_checkpoint_monotonic = now
+    prog._dates_since_checkpoint = 0
     # Keep the breakdown internally consistent at the checkpoint instant: `error_other` is derived from
     # the SAME uncapped `date_failures_total` the end of `_do_backfill` uses (one derivation, applied
     # earlier), so a checkpointed row never shows failures in its summary and 0 in its breakdown.
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index 9c6e73d1..edb84c33 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -15,8 +15,10 @@ Also provides the tiny ascending-series extractors the indicator functions consu
 """
 from __future__ import annotations
 
+import array
 import bisect
 import threading
+from collections.abc import Sequence
 from contextlib import contextmanager
 from datetime import date as date_cls
 from typing import Iterable, Iterator, NamedTuple, Optional
@@ -53,6 +55,70 @@ def latest_data_date(session: Session) -> Optional[date_cls]:
     return session.scalar(select(func.max(DailyPrice.date)))
 
 
+# ops-hardening iter-41 (B5) — the columnar per-symbol accumulator `_BarCache.prefill` publishes,
+# replacing a plain `list[Bar]`. `prefill`'s query is already `.yield_per(batch)`-streamed on the DB
+# cursor side, but every row still ended up as ONE resident `Bar` NamedTuple per row (a tuple holding
+# 5 individually-boxed Python `float` objects, ~24 bytes each, plus the tuple's own ~56 bytes) inside
+# ONE Python list per symbol — ~1.1 GB at the live basis (3.3M rows), open since iter-29/d and
+# EXPLICITLY left untouched by iter-35/36/37's narrower fix (which bounded only
+# `membership_timeline_cached`'s cache-miss sub-call via the separate, unrelated `load_only` batching
+# below — that mechanism is UNCHANGED by this class). `array.array('d')` stores each numeric column as
+# raw 8-byte C doubles with NO per-element Python object overhead — the same values, a fraction of the
+# resident bytes. A full `collections.abc.Sequence`: indexing/slicing synthesize real `Bar` NamedTuples
+# on demand, so `_BarCache.bars_asof`/`bars_asof_window`/`bars_after`/`close_on` (below) read it via the
+# EXACT SAME `full[:cut]` / `full[cut-1]` / `len(full)` code they already used for a plain `list[Bar]`
+# — NOT ONE LINE of those methods changes. `dates` aliases the SAME list `_BarCache._dates_by_symbol`
+# already owns (no duplication) — the bisect boundary and the served Bar values share one source, so
+# they can never drift apart. Also duck-types cleanly against a plain `list[Bar]` (equality, iteration
+# yielding real `Bar` objects that support `._replace()`) so code that later REPLACES one symbol's
+# entry with an ordinary list (e.g. a test simulating a poisoned/mutated series) keeps working
+# unchanged — `_by_symbol`'s per-symbol value only needs to support the Sequence protocol, never a
+# specific concrete type.
+class _SymbolColumns(Sequence):
+    """Columnar per-symbol OHLCV storage — see the module-level comment block above for the full
+    rationale (memory bound + duck-typing contract)."""
+    __slots__ = ("dates", "opens", "highs", "lows", "closes", "volumes")
+
+    def __init__(
+        self,
+        dates: list[date_cls],
+        opens: "array.array",
+        highs: "array.array",
+        lows: "array.array",
+        closes: "array.array",
+        volumes: "array.array",
+    ) -> None:
+        self.dates = dates
+        self.opens = opens
+        self.highs = highs
+        self.lows = lows
+        self.closes = closes
+        self.volumes = volumes
+
+    def __len__(self) -> int:
+        return len(self.dates)
+
+    def __getitem__(self, item):
+        if isinstance(item, slice):
+            idxs = range(*item.indices(len(self.dates)))
+            return [
+                Bar(self.dates[i], self.opens[i], self.highs[i], self.lows[i], self.closes[i], self.volumes[i])
+                for i in idxs
+            ]
+        return Bar(
+            self.dates[item], self.opens[item], self.highs[item], self.lows[item],
+            self.closes[item], self.volumes[item],
+        )
+
+    def __eq__(self, other) -> bool:
+        if isinstance(other, (list, _SymbolColumns)):
+            return list(self) == list(other)
+        return NotImplemented
+
+    def __repr__(self) -> str:  # pragma: no cover -- debugging aid only
+        return f"_SymbolColumns({len(self)} bars)"
+
+
 # --------------------------------------------------------------------------------------------------
 # J-46 — load-once bar cache (Capability 33): an OPT-IN, per-session optimization at the single
 # `bars_asof` seam. A multi-date backfill calls `bars_asof(symbol, D)` once PER DATE today, so each
@@ -79,7 +145,11 @@ class _BarCache:
     has loaded every symbol up front, the hot path is a pure lock-free read of immutable lists."""
 
     def __init__(self) -> None:
-        self._by_symbol: dict[str, list[Bar]] = {}
+        # iter-41 (B5): a symbol's value here is EITHER a plain `list[Bar]` (the lazy per-symbol path,
+        # `load_only`, or a caller-replaced series) OR a `_SymbolColumns` (`prefill`'s eager whole-table
+        # scan) — every read site below uses only the shared Sequence operations (`full[:cut]`, indexing,
+        # `len`) both shapes support identically, so callers never need to know which one they hold.
+        self._by_symbol: dict[str, "list[Bar] | _SymbolColumns"] = {}
         self._dates_by_symbol: dict[str, list[date_cls]] = {}
         self._load_lock = threading.Lock()
         # iter-19: whether the ONE expensive whole-table scan has already run on this cache instance. A
@@ -125,7 +195,17 @@ class _BarCache:
         series has 0 trailing bars, exactly the grouped-count path's result (`below_history`). Recording an
         absent symbol as `[]` is descriptive, not fabricated: it means "this name has no bars at/through D".
         This cheap bookkeeping still runs on EVERY call (even when the whole-table scan is skipped), so a
-        later call passing a WIDER `expected_symbols` set still records any newly-named no-bar candidate."""
+        later call passing a WIDER `expected_symbols` set still records any newly-named no-bar candidate.
+
+        iter-41 (B5, AG-8 memory bound): the resident accumulator built by this scan is now `_SymbolColumns`
+        (module-level, above) — `array.array('d')` per numeric field instead of a `list[Bar]` of
+        individually-boxed-float NamedTuples — cutting the ~1.1 GB this scan holds resident for the whole
+        cache's lifetime (3.3M rows at the live basis) without changing a single served value: every
+        consumer (`bars_asof`/`bars_asof_window`/`bars_after`/`close_on` below) reads `self._by_symbol[symbol]`
+        through the exact same `full[:cut]` / `full[cut-1]` / `len(full)` operations it already used, and
+        `_SymbolColumns` implements the full `Sequence` protocol those operations need — so none of those
+        methods change. The `.yield_per(batch)` cursor streaming above is unchanged (already bounded since
+        before iter-35); this closes the OTHER half — the destination the streamed rows accumulate into."""
         with self._load_lock:
             need_scan = not self._prefilled
         if need_scan:
@@ -137,19 +217,31 @@ class _BarCache:
                 )
                 .order_by(DailyPrice.symbol, DailyPrice.date)
             )
-            by_symbol: dict[str, list[Bar]] = {}
+            by_symbol: dict[str, _SymbolColumns] = {}
             for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
-                by_symbol.setdefault(symbol, []).append(Bar(d, o, h, lo, c, v))
+                cols = by_symbol.get(symbol)
+                if cols is None:
+                    cols = _SymbolColumns(
+                        [], array.array("d"), array.array("d"), array.array("d"),
+                        array.array("d"), array.array("d"),
+                    )
+                    by_symbol[symbol] = cols
+                cols.dates.append(d)
+                cols.opens.append(o)
+                cols.highs.append(h)
+                cols.lows.append(lo)
+                cols.closes.append(c)
+                cols.volumes.append(v)
             # publish atomically under the lock so a concurrent reader sees a fully-built map, not a
             # partial one; re-check `_prefilled` in case another thread raced us to the scan (rare —
             # `_BarCache` is normally driven by one orchestrating thread — but the merge below is
             # idempotent either way, so a lost race just discards redundant work, never corrupts state).
             with self._load_lock:
                 if not self._prefilled:
-                    for symbol, full in by_symbol.items():
+                    for symbol, cols in by_symbol.items():
                         if symbol not in self._by_symbol:  # never overwrite a series already loaded
-                            self._by_symbol[symbol] = full
-                            self._dates_by_symbol[symbol] = [bar.date for bar in full]
+                            self._by_symbol[symbol] = cols
+                            self._dates_by_symbol[symbol] = cols.dates  # SAME list object — no duplication
                     self._prefilled = True
         # record an EMPTY series for every expected (candidate-pool) symbol with no bars, so it is never
         # lazy-loaded per-date later — load-once-per-job holds for no-bar names too. Cheap (no query), so
diff --git a/apps/backend/main.py b/apps/backend/main.py
index 1fcb03df..bf408ff2 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -9,6 +9,7 @@ from __future__ import annotations
 
 import logging
 import os
+import signal
 import time
 from contextlib import asynccontextmanager
 
@@ -50,6 +51,21 @@ configure_app_logging()
 
 logger = logging.getLogger("trendora.lifespan")
 
+# ops-hardening iter-41 (C7) — DIAGNOSTIC ONLY, opt-in via env var, never on by default: arms
+# `faulthandler.register(SIGUSR1, all_threads=True)` so a throwaway-DB wedge-drill can send
+# `kill -USR1 <pid>` to a suspected-frozen process and get an ALL-THREAD stack dump on stderr
+# WITHOUT killing it — the exact tool iter-40's run 1 needed but didn't have (`gdb` attach was
+# denied by this host's `yama.ptrace_scope` policy; no `py-spy` was installed). Deliberately NOT a
+# launch-script change (AG-10's byte-frozen `scripts/start-backend.sh` stays untouched) — the drill
+# sets `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` in its own environment before invoking that SAME
+# unmodified script, which inherits it like any other env var. Every real deployment leaves this
+# unset, so `signal.SIGUSR1` is never touched outside an explicit diagnostic drill.
+if os.environ.get("TRENDORA_DIAG_FAULTHANDLER_SIGUSR1") == "1":
+    import faulthandler
+
+    faulthandler.register(signal.SIGUSR1, all_threads=True)
+    logger.info("diagnostic: faulthandler armed on SIGUSR1 (TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1)")
+
 
 @asynccontextmanager
 async def lifespan(app: FastAPI):
diff --git a/apps/backend/tests/test_bar_cache.py b/apps/backend/tests/test_bar_cache.py
index 629fc5e2..df590c08 100644
--- a/apps/backend/tests/test_bar_cache.py
+++ b/apps/backend/tests/test_bar_cache.py
@@ -96,6 +96,54 @@ def test_prefill_returns_bar_records_matching_plain_query_row_level(tiny_engine)
     assert prefilled == reference
 
 
+def _old_prefill_by_symbol(session) -> dict:
+    """ops-hardening iter-41 (B5, TC-6) -- a faithful reimplementation of the PRE-iter-41
+    `_BarCache.prefill` accumulation body (the exact code this iteration's B5 fix replaced): one `Bar`
+    NamedTuple per row, appended into a plain `list[Bar]` per symbol. Kept here ONLY as a benchmark/
+    test reference -- never imported by the shipped app (mirrors
+    `runs/goal-ops-hardening-iter-41/bar-cache-prefill-bench/measure_prefill_peak.py`'s own `_old_
+    prefill_peak`, the live-DB peak-memory measurement's OLD arm)."""
+    from app.config import get_config
+
+    batch = get_config().research.read_batch_size
+    stmt = (
+        select(
+            DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
+            DailyPrice.low, DailyPrice.close, DailyPrice.volume,
+        )
+        .order_by(DailyPrice.symbol, DailyPrice.date)
+    )
+    by_symbol: dict = {}
+    for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
+        by_symbol.setdefault(symbol, []).append(prices.Bar(d, o, h, lo, c, v))
+    return by_symbol
+
+
+def test_prefill_old_vs_new_implementation_byte_identical(tiny_engine):
+    """TC-6 -- the OLD (pre-iter-41, `list[Bar]`) and NEW (iter-41 B5, columnar `_SymbolColumns`)
+    `_BarCache.prefill` implementations, run through the SAME fixture inputs, return byte-identical
+    `Bar` values for every symbol/date -- the fixture-backed old-vs-new equality proof the B5 memory
+    bound requires (byte-identical output, only the resident storage shape changed)."""
+    engine, days = tiny_engine
+    with Session(engine) as old_session:
+        old_by_symbol = _old_prefill_by_symbol(old_session)
+    with Session(engine) as new_session:
+        cache = prices._BarCache()
+        cache.prefill(new_session)
+        new_by_symbol = cache._by_symbol
+
+    assert set(old_by_symbol) == set(new_by_symbol) == {"SPY", "AAA"}
+    for symbol in old_by_symbol:
+        old_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in old_by_symbol[symbol]]
+        new_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in new_by_symbol[symbol]]
+        assert new_bars == old_bars, f"symbol {symbol}: NEW prefill output diverges from OLD"
+        # every synthesized element is still a REAL `Bar` NamedTuple (supports `.date`/`._replace()`/
+        # structural equality with the OLD implementation's own Bar instances) -- not merely
+        # value-equal tuples of a different type.
+        assert all(isinstance(b, prices.Bar) for b in new_by_symbol[symbol])
+        assert list(new_by_symbol[symbol]) == list(old_by_symbol[symbol])
+
+
 def test_lazy_load_returns_bar_records_matching_plain_query_row_level(tiny_engine):
     """The lazy per-symbol fallback inside `bars_asof` (already per-symbol-bounded — iter-19 only changes
     its record type, never its bounding) also returns `Bar` records whose values match a plain reference
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index f267d0d7..0fa5ec17 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -4547,6 +4547,123 @@ def test_checkpoint_cadence_density_and_throttle_control(tmp_path, monkeypatch):
     )
 
 
+# ==================================================================================================
+# ops-hardening iter-41 (D9, TC-8) -- the count-based floor on top of the time-based throttle
+# ==================================================================================================
+def test_checkpoint_count_based_floor_forces_write_within_one_interval(tmp_path, monkeypatch):
+    """TC-8 -- dev Known Issue #2 from iter-40's own handoff: the time-based throttle alone
+    (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`) never forces a write if the mocked clock NEVER crosses the
+    interval threshold, no matter how many dates complete. This proves the ADDED count-based floor
+    (`_RUN_RECORD_CHECKPOINT_DATE_FLOOR`) closes that gap on its own -- a checkpoint write lands on
+    the Kth call even when elapsed wall-clock time is (deliberately) always 0."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'floor.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    # A clock that NEVER advances -- isolates the count-based floor from the time-based throttle
+    # entirely: if only the interval throttle existed, this would produce exactly ONE write (the
+    # unconditional first call) and never another, regardless of how many dates complete.
+    frozen_now = [1_000_000.0]
+    monkeypatch.setattr(data_manager.time, "monotonic", lambda: frozen_now[0])
+
+    floor = data_manager._RUN_RECORD_CHECKPOINT_DATE_FLOOR
+    assert floor > 1, "the floor must be a real multi-date cadence, not a de-facto every-call throttle"
+
+    prog = JobProgress(job_id="floor-probe", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 30))
+    prog.dates_total = floor * 3
+    data_manager._create_run_record(engine, cfg, prog)
+
+    def _persisted_dates_done() -> int:
+        with Session(engine) as session:
+            row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "floor-probe")).one()
+        return json.loads(row.message)["dates_done"]
+
+    # Call 1 (priming): the unconditional first write (time-based -- `_last_checkpoint_monotonic`
+    # starts at 0.0, so `now - 0.0` always clears the interval on the very first call regardless of
+    # the frozen clock's value). This ALSO resets `_dates_since_checkpoint` to 0 -- the same as any
+    # other write -- so it establishes the baseline the count-based floor counts FROM, exactly like a
+    # job's real first per-date checkpoint would.
+    prog.dates_done = 1
+    data_manager._checkpoint_run_record(engine, prog)
+    assert _persisted_dates_done() == 1, "the first checkpoint call must always write"
+    assert prog._dates_since_checkpoint == 0, "the counter resets on every write, including the first"
+
+    # Calls 2..floor+1 (floor MORE calls after the priming reset): the frozen clock means `time_due`
+    # is False for every one of these -- ONLY the count-based floor can force a write, and it must do
+    # so on EXACTLY the (floor+1)th ABSOLUTE call (the `floor`th call SINCE the last write), not
+    # before and not after -- i.e. at most `floor` dates may complete between checkpoint writes.
+    for i in range(2, floor + 2):
+        prog.dates_done = i
+        data_manager._checkpoint_run_record(engine, prog)
+        persisted = _persisted_dates_done()
+        if i < floor + 1:
+            assert persisted == 1, (
+                f"call {i} ({i - 1} dates since the last write, < floor={floor}) must NOT force a "
+                f"write under a frozen clock -- persisted dates_done unexpectedly advanced to {persisted}"
+            )
+        else:
+            assert persisted == i, (
+                f"call {i} ({i - 1} dates since the last write, == floor={floor}) must force a write "
+                f"under a frozen clock -- persisted dates_done is {persisted}, expected {i}"
+            )
+            assert prog._dates_since_checkpoint == 0, "the floor-triggered write resets the counter"
+
+    # The cycle repeats: another `floor` calls under the still-frozen clock forces exactly one more
+    # write, `floor` calls after the previous forced write (not sooner) -- proves this is a
+    # recurring cadence, not a one-shot fluke of the first cycle.
+    second_write_call = floor + 1
+    for i in range(second_write_call + 1, second_write_call + floor):
+        prog.dates_done = i
+        data_manager._checkpoint_run_record(engine, prog)
+        assert _persisted_dates_done() == second_write_call, (
+            f"call {i} (mid-second-cycle) must not write again before the counter reaches the floor a "
+            f"second time"
+        )
+    third_write_call = second_write_call + floor
+    prog.dates_done = third_write_call
+    data_manager._checkpoint_run_record(engine, prog)
+    assert _persisted_dates_done() == third_write_call, (
+        "the second full cycle must also force a write exactly `floor` calls after the previous one"
+    )
+
+
+def test_checkpoint_time_based_throttle_still_wins_when_faster(tmp_path, monkeypatch):
+    """TC-8 companion -- the count-based floor is additive, never a REGRESSION of the existing
+    time-based density: when the mocked clock crosses the interval before the count reaches the
+    floor (the normal ~1-2.5s/date rate iter-40 measured), the time-based path still fires first and
+    the counter still resets (no double-write, no drift between the two mechanisms)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'floor2.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    fake_now = [1_000_000.0]
+    monkeypatch.setattr(data_manager.time, "monotonic", lambda: fake_now[0])
+    interval = data_manager._RUN_RECORD_CHECKPOINT_INTERVAL_S
+    floor = data_manager._RUN_RECORD_CHECKPOINT_DATE_FLOOR
+
+    prog = JobProgress(job_id="floor-vs-time", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 10))
+    prog.dates_total = floor
+    data_manager._create_run_record(engine, cfg, prog)
+
+    def _persisted_dates_done() -> int:
+        with Session(engine) as session:
+            row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "floor-vs-time")).one()
+        return json.loads(row.message)["dates_done"]
+
+    prog.dates_done = 1
+    data_manager._checkpoint_run_record(engine, prog)  # call 1: always writes
+    assert _persisted_dates_done() == 1
+
+    # call 2: advance the clock past the interval but stay WELL under the count floor -- the
+    # time-based path must fire (this is a REAL date completing at the throttle's own configured
+    # cadence, not the pathologically-fast case TC-8's first test isolates).
+    fake_now[0] += interval + 0.01
+    prog.dates_done = 2
+    data_manager._checkpoint_run_record(engine, prog)
+    assert _persisted_dates_done() == 2, "a time-due call must still write even with the count floor added"
+    assert prog._dates_since_checkpoint == 0, "a time-triggered write must also reset the count floor"
+
+
 # ==================================================================================================
 # J-37 — Pull-missing job constructor (gap-exact, dispatched through the EXISTING J-34 chunked engine)
 # ==================================================================================================
diff --git a/incredible_auto_dev/.claude/agents/ui-test-designer.md b/incredible_auto_dev/.claude/agents/ui-test-designer.md
index 90ceb8b7..041ce3ea 100644
--- a/incredible_auto_dev/.claude/agents/ui-test-designer.md
+++ b/incredible_auto_dev/.claude/agents/ui-test-designer.md
@@ -22,6 +22,10 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 5. `reports/qa/<phase>-test-plan.md` — existing functional test plan (for context)
 6. `.claude/skills/manual-ui-test-plan-generator.md` — methodology for test case design
 7. `.claude/skills/what-to-click-writer.md` — how to write the operator guide
+8. `docs/goal.md`'s "Must-have user journeys" section (or a token-lean goal-slice file, when the
+   dispatch prompt points at one) — ONLY when the phase spec is backend-only AND names
+   required-still-passing journeys (see "Backend-only phase handling" below); read ONLY the named
+   journeys' own Steps/Acceptance text, not the whole file. Skip entirely otherwise.
 
 ## Process
 
@@ -77,9 +81,31 @@ Each step must have:
 
 ## Backend-only phase handling
 
-If `Frontend Present: no` or if user-visible-changes report says N/A:
+If `Frontend Present: no` or if user-visible-changes report says N/A, `Frontend Present: no`
+suppresses NEW-surface UI test-case generation ONLY (Step 1's smoke/happy-path/validation/
+error/UX cases for a UI surface map row) — it never suppresses regression coverage for a
+required-still-passing journey (ops-hardening iter-40/41 lesson, binding: a required-still-passing
+journey shipping with ZERO evidence — this exact stub, applied blindly — was the root cause of a
+5-consecutive-ESCALATE session where every gate reported clean while journeys silently rotted
+unverified).
+
+1. Read the phase spec (`docs/phases/<phase>.md`) for a `**Required-still-passing journeys:**`
+   metadata line (goal mode only; a plain phase-mode spec, or a goal-mode spec with no such line
+   or whose line reads `none`, has nothing to regress here).
+2. If that line names one or more journey IDs (e.g. `J-01, J-03, J-04`): for EACH one, write
+   exactly one regression test case using **Test ID `UT-<journey-id>`** (e.g. `UT-J-01`, not the
+   sequential `UT-01` scheme) into the UI test plan, `Type: regression`, `Priority: P1`. Steps and
+   Expected Result come from that journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s
+   "Must-have user journeys" section (or the token-lean goal slice this phase's inputs point at,
+   when one is supplied) — read the journey's numbered steps and acceptance criteria and translate
+   them into the SAME exact-URL/exact-click/exact-expected format Step 2 above requires; do not
+   invent a generic "re-check journey X" placeholder. Do NOT emit a NEW-surface case for anything
+   else (there is no UI surface map row to derive one from on a backend-only phase).
+3. Still write the What-to-Click operator guide, scoped to the same required-still-passing
+   journeys (skip the "New capability" prioritization — there is none this phase).
+4. If that metadata line is absent, empty, or reads `none`: write the minimal N/A stubs below and
+   STOP — there is genuinely nothing to test.
 
-Write minimal N/A stubs:
 ```
 # Phase {N} — UI Test Plan
 **Status:** N/A — Backend-only phase. No UI tests required.
@@ -90,8 +116,6 @@ Write minimal N/A stubs:
 **Status:** N/A — Backend-only phase. No UI verification steps.
 ```
 
-Then STOP.
-
 ## Rules
 
 - Do NOT edit source files
diff --git a/incredible_auto_dev/agents/ui-test-designer/body.md b/incredible_auto_dev/agents/ui-test-designer/body.md
index 24eba591..ed96d4f3 100644
--- a/incredible_auto_dev/agents/ui-test-designer/body.md
+++ b/incredible_auto_dev/agents/ui-test-designer/body.md
@@ -14,6 +14,10 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 5. `reports/qa/<phase>-test-plan.md` — existing functional test plan (for context)
 6. `.claude/skills/manual-ui-test-plan-generator.md` — methodology for test case design
 7. `.claude/skills/what-to-click-writer.md` — how to write the operator guide
+8. `docs/goal.md`'s "Must-have user journeys" section (or a token-lean goal-slice file, when the
+   dispatch prompt points at one) — ONLY when the phase spec is backend-only AND names
+   required-still-passing journeys (see "Backend-only phase handling" below); read ONLY the named
+   journeys' own Steps/Acceptance text, not the whole file. Skip entirely otherwise.
 
 ## Process
 
@@ -69,9 +73,31 @@ Each step must have:
 
 ## Backend-only phase handling
 
-If `Frontend Present: no` or if user-visible-changes report says N/A:
+If `Frontend Present: no` or if user-visible-changes report says N/A, `Frontend Present: no`
+suppresses NEW-surface UI test-case generation ONLY (Step 1's smoke/happy-path/validation/
+error/UX cases for a UI surface map row) — it never suppresses regression coverage for a
+required-still-passing journey (ops-hardening iter-40/41 lesson, binding: a required-still-passing
+journey shipping with ZERO evidence — this exact stub, applied blindly — was the root cause of a
+5-consecutive-ESCALATE session where every gate reported clean while journeys silently rotted
+unverified).
+
+1. Read the phase spec (`docs/phases/<phase>.md`) for a `**Required-still-passing journeys:**`
+   metadata line (goal mode only; a plain phase-mode spec, or a goal-mode spec with no such line
+   or whose line reads `none`, has nothing to regress here).
+2. If that line names one or more journey IDs (e.g. `J-01, J-03, J-04`): for EACH one, write
+   exactly one regression test case using **Test ID `UT-<journey-id>`** (e.g. `UT-J-01`, not the
+   sequential `UT-01` scheme) into the UI test plan, `Type: regression`, `Priority: P1`. Steps and
+   Expected Result come from that journey's own "Steps:"/"Acceptance:" text in `docs/goal.md`'s
+   "Must-have user journeys" section (or the token-lean goal slice this phase's inputs point at,
+   when one is supplied) — read the journey's numbered steps and acceptance criteria and translate
+   them into the SAME exact-URL/exact-click/exact-expected format Step 2 above requires; do not
+   invent a generic "re-check journey X" placeholder. Do NOT emit a NEW-surface case for anything
+   else (there is no UI surface map row to derive one from on a backend-only phase).
+3. Still write the What-to-Click operator guide, scoped to the same required-still-passing
+   journeys (skip the "New capability" prioritization — there is none this phase).
+4. If that metadata line is absent, empty, or reads `none`: write the minimal N/A stubs below and
+   STOP — there is genuinely nothing to test.
 
-Write minimal N/A stubs:
 ```
 # Phase {N} — UI Test Plan
 **Status:** N/A — Backend-only phase. No UI tests required.
@@ -82,8 +108,6 @@ Write minimal N/A stubs:
 **Status:** N/A — Backend-only phase. No UI verification steps.
 ```
 
-Then STOP.
-
 ## Rules
 
 - Do NOT edit source files
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 77b2cc73..fbcfda4f 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -48,13 +48,20 @@ if detect_frontend_in_plan "$PLAN_FILE"; then
   FRONTEND_PRESENT="yes"
 fi
 
-# Skip for backend-only phases
-if [[ "$FRONTEND_PRESENT" == "no" ]]; then
+# Skip for backend-only phases -- UNLESS this is a goal-mode iteration naming
+# required-still-passing journeys (ops-hardening iter-41, A1 companion fix): those
+# journeys still need fresh browser-QA evidence every iteration (the GOAL-MODE
+# REGRESSION LANES logic below already handles them — it was simply unreachable
+# behind this early exit). See lib/common.sh::phase_spec_has_required_regression.
+if [[ "$FRONTEND_PRESENT" == "no" ]] && ! phase_spec_has_required_regression "$SPEC"; then
   echo "[browser-qa] Backend-only phase — writing N/A stubs."
   write_na_ui_artifacts "$PHASE" "ui-test-results"
   echo "[browser-qa] Done (backend-only, N/A stubs written)."
   exit 0
 fi
+if [[ "$FRONTEND_PRESENT" == "no" ]]; then
+  echo "[browser-qa] Backend-only phase, but required-still-passing journeys are named — running browser QA for regression re-verification only."
+fi
 
 # Verify test plan exists
 if [[ ! -f "$UI_TEST_PLAN" ]]; then
@@ -159,7 +166,10 @@ fi
 # Derive URLs from the resolved port env vars
 _BACKEND_PORT="${CHAIN_BACKEND_PORT}"
 _FRONTEND_PORT="${CHAIN_FRONTEND_PORT}"
-BACKEND_HEALTH_URL="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${_BACKEND_PORT}/health}"
+# ops-hardening iter-41 (A1): resolve the project-specific health path (Trendora's
+# `/api/health`, not the framework's generic `/health`) via the shared helper — see
+# `lib/common.sh::resolve_backend_health_url`.
+BACKEND_HEALTH_URL="$(resolve_backend_health_url "$_BACKEND_PORT")"
 FRONTEND_URL="${CHAIN_FRONTEND_URL:-http://localhost:${_FRONTEND_PORT}}"
 echo "[browser-qa] Resolved ports: frontend=${FRONTEND_URL} backend=${BACKEND_HEALTH_URL}"
 
diff --git a/incredible_auto_dev/scripts/automation/demo-phase.sh b/incredible_auto_dev/scripts/automation/demo-phase.sh
index 6a1f4a75..b96e20b4 100755
--- a/incredible_auto_dev/scripts/automation/demo-phase.sh
+++ b/incredible_auto_dev/scripts/automation/demo-phase.sh
@@ -188,7 +188,10 @@ ensure_phase_ports
 
 _BACKEND_PORT="${CHAIN_BACKEND_PORT:-8000}"
 _FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-3000}"
-BACKEND_HEALTH_URL="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${_BACKEND_PORT}/health}"
+# ops-hardening iter-41 (A1): resolve the project-specific health path (Trendora's
+# `/api/health`, not the framework's generic `/health`) via the shared helper — see
+# `lib/common.sh::resolve_backend_health_url`.
+BACKEND_HEALTH_URL="$(resolve_backend_health_url "$_BACKEND_PORT")"
 FRONTEND_URL="${CHAIN_FRONTEND_URL:-http://localhost:${_FRONTEND_PORT}}"
 
 if [[ "${CHAIN_SHARED_SERVICES:-false}" != "true" ]]; then
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 21e9922d..52d2d43f 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -262,7 +262,10 @@ fi
 
 _BACKEND_PORT="${CHAIN_BACKEND_PORT:-8000}"
 _FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-3000}"
-BACKEND_HEALTH_URL="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${_BACKEND_PORT}/health}"
+# ops-hardening iter-41 (A1): resolve the project-specific health path (Trendora's
+# `/api/health`, not the framework's generic `/health`) via the shared helper — see
+# `lib/common.sh::resolve_backend_health_url`.
+BACKEND_HEALTH_URL="$(resolve_backend_health_url "$_BACKEND_PORT")"
 FRONTEND_URL="${CHAIN_FRONTEND_URL:-http://localhost:${_FRONTEND_PORT}}"
 
 kill_stale_next_dev_server 2>/dev/null || true
@@ -481,7 +484,7 @@ _bqa_full_fork_consume() {
   replay_lane_paths "$ITER_NAME"
   cd "$REPO_ROOT"
   # Checkpoint mark — verbatim the section's own tail, which the fork skipped.
-  _bq_verdict="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED' | head -1)"
+  _bq_verdict="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED|BLOCKED' | head -1)"
   if [[ "$_bq_verdict" == "PASS" || "$_bq_verdict" == "FAIL" ]]; then
     step_mark_done browser-qa --dir "$ITER_DIR" --verdict "$_bq_verdict" --journeys "$_bq_sig" "$UI_TEST_RESULTS"
   fi
@@ -528,7 +531,7 @@ _bqa_checkpoint_reusable() {
   step_done_valid browser-qa --verify-tree --dir "$ITER_DIR" "$UI_TEST_RESULTS" || return 1
   [[ "$(step_field browser-qa journeys "$ITER_DIR")" == "$_bq_sig" ]] || return 1
   local _v
-  _v="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED' | head -1 || true)"
+  _v="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED|BLOCKED' | head -1 || true)"
   [[ "$_v" == "PASS" || "$_v" == "FAIL" ]]
 }
 
@@ -887,7 +890,7 @@ replay_lane_golden_coverage "$UI_TEST_RESULTS" "$ITER_NAME"
 # SPEED-3: inside the full fork the mark is DEFERRED to the join
 # (_bqa_full_fork_consume) — a marker written from the fork could race the
 # review loop's invalidation cascade in the parent shell.
-_bq_verdict="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED' | head -1)"
+_bq_verdict="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED|BLOCKED' | head -1)"
 if [[ ( "$_bq_verdict" == "PASS" || "$_bq_verdict" == "FAIL" ) && -z "${_BQA_IN_FULL_FORK:-}" ]]; then
   step_mark_done browser-qa --dir "$ITER_DIR" --verdict "$_bq_verdict" --journeys "$_bq_sig" "$UI_TEST_RESULTS"
 fi
@@ -1218,7 +1221,7 @@ if declare -F iter_budget_check >/dev/null 2>&1; then iter_budget_check "browser
 _bq_skip="no"
 if step_done_valid browser-qa --verify-tree --dir "$ITER_DIR" "$UI_TEST_RESULTS" \
    && [[ "$(step_field browser-qa journeys "$ITER_DIR")" == "$_bq_sig" ]]; then
-  _prior_bq_verdict="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED' | head -1)"
+  _prior_bq_verdict="$(grep -m1 -E '^\*\*Browser QA Verdict:\*\*' "$UI_TEST_RESULTS" 2>/dev/null | grep -oE 'PASS|FAIL|SKIPPED|BLOCKED' | head -1)"
   if [[ "$_prior_bq_verdict" == "PASS" || "$_prior_bq_verdict" == "FAIL" ]]; then
     _bq_skip="yes"
     _step_skipped_event "browser-qa"
diff --git a/incredible_auto_dev/scripts/automation/lib/closure_gate.py b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
index d9329e21..3d3c0711 100644
--- a/incredible_auto_dev/scripts/automation/lib/closure_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
@@ -424,6 +424,22 @@ def _crossref_frontend(
                     "validation was not required for this phase.",
                 ))
                 r.crossref.append("ui-test-results: all SKIPPED, NO reason (blocking).")
+        elif file_top_verdict(results) == "BLOCKED":
+            # ops-hardening iter-41 (A3, TC-3): a required-still-passing journey with ZERO executed
+            # test cases has no row at all, so it survives `all_skipped` (other rows DO show real
+            # PASS/FAIL execution) while merge_ui_test_results.merge() still forces the headline to
+            # BLOCKED for exactly this gap. Without this branch closure would read "execution
+            # evidence present" and pass a phase where a required journey was silently never
+            # attempted -- iter-40's own failure mode.
+            r.blocking.append((
+                f"`phase-{phase}-ui-test-results.md` headline is BLOCKED — at least one "
+                "required-still-passing journey has zero executed test cases (see its "
+                '"Missing Required Journeys" section) or another journey\'s own assertions '
+                "were never checked",
+                "Run browser QA / the deterministic replay lane so every required-still-passing "
+                "journey gets a real row, then re-run closure.",
+            ))
+            r.crossref.append("ui-test-results: headline BLOCKED (unmet DoD item, blocking).")
         else:
             r.crossref.append("ui-test-results: execution evidence present (PASS/FAIL rows).")
 
@@ -708,6 +724,27 @@ def _self_test() -> int:
             assert r.verdict == "CLOSURE-FAIL"
             assert any("no documented reason" in b[0] for b in r.blocking), r.blocking
 
+    def t_missing_required_journey_headline_blocked():
+        # ops-hardening iter-41 (A3, TC-3): merge_ui_test_results.merge() forces the headline to
+        # BLOCKED when a required-still-passing journey has ZERO executed test cases -- even though
+        # every OTHER row is a clean PASS (so `all_skipped` alone would miss it and this file would
+        # otherwise read "execution evidence present"). Must be CLOSURE-FAIL, not CLOSURE-PASS.
+        with tempfile.TemporaryDirectory() as d:
+            root = Path(d)
+            _write_fixture(root, "p1")
+            rp = root / "reports" / "phase-p1-ui-test-results.md"
+            rp.write_text(
+                "# r\n\n**Browser QA Verdict:** BLOCKED\n\n"
+                "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+                "|---|---|---|---|---|---|---|---|\n"
+                "| UT-J-01 | Backfill honors range | regression | P1 | e | ok | PASS | a.png |\n\n"
+                "## Missing Required Journeys\n\n"
+                "- `UT-J-03` — no test case executed for J-03 by any lane\n\n"
+                + _RICH + "\n", encoding="utf-8")
+            r = run_gate("p1", root)
+            assert r.verdict == "CLOSURE-FAIL", r.blocking
+            assert any("headline is BLOCKED" in b[0] for b in r.blocking), r.blocking
+
     def t_backend_only_stubs_pass():
         with tempfile.TemporaryDirectory() as d:
             root = Path(d)
@@ -746,6 +783,7 @@ def _self_test() -> int:
         ("missing_artifact", t_missing_artifact),
         ("failed_gate_verdict", t_failed_gate_verdict),
         ("all_skipped_reason_nuance", t_all_skipped_reason_nuance),
+        ("missing_required_journey_headline_blocked", t_missing_required_journey_headline_blocked),
         ("backend_only_stubs_pass", t_backend_only_stubs_pass),
         ("vague_what_to_click", t_vague_what_to_click),
         ("na_stub_on_frontend_phase", t_na_stub_on_frontend_phase),
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 64702753..99889ab8 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -359,6 +359,60 @@ ensure_phase_ports() {
   fi
 }
 
+# ops-hardening iter-41 (A1) — the backend health-check URL surfaced BOTH to
+# `ensure_services_running`'s liveness probe AND (critically) to the browser-qa /
+# QA LLM dispatch prompt (the "Note:"/SERVICES_NOTE text each `*-phase.sh` caller
+# embeds for the agent). The framework's own generic default (a bare `/health`)
+# 404s on this project — Trendora namespaces EVERY route under `/api`
+# (`apps/backend/main.py` mounts `health.router` with `prefix="/api"`) — so an
+# agent told to poll the wrong path reads a live, healthy backend's 404 as "down"
+# and reports a false regression. `ensure_services_running`'s own probe is already
+# permissive (any 1xx-5xx counts as "up" — see its docstring above), so THAT half
+# was never broken; the break was this URL being handed to the LLM verbatim as
+# "the health endpoint," which the agent (reasonably) treats as authoritative and
+# checks literally. Root cause #1 of iter-40's ESCALATE (4th consecutive
+# audit-only catch of all required-still-passing journeys shipping unverified).
+#
+# Mirrors `lib/demo_runner.py`'s already-fixed (iter-39) `resolve_backend_health_url`
+# — same project-specific override, same reasoning — factored into ONE shared
+# helper so the five `*-phase.sh` callers (browser-qa-phase.sh, goal-iter-lean.sh,
+# qa-phase.sh, demo-phase.sh, run-phase.sh) can never drift from each other again
+# (which is exactly how this bug happened: demo_runner.py was fixed at iter-39,
+# the shell scripts were not, because each duplicated its own inline default).
+#
+# An explicit `CHAIN_BACKEND_HEALTH_URL` always wins (unchanged override contract
+# — a caller/test that needs a different URL still can).
+#
+# Usage: BACKEND_HEALTH_URL="$(resolve_backend_health_url "$_BACKEND_PORT")"
+resolve_backend_health_url() {
+  local port="$1"
+  if [[ -n "${CHAIN_BACKEND_HEALTH_URL:-}" ]]; then
+    echo "$CHAIN_BACKEND_HEALTH_URL"
+    return 0
+  fi
+  echo "http://localhost:${port}/api/health"
+}
+
+# ops-hardening iter-41 (A1 companion fix) — true iff phase-spec file $1 names at least one journey
+# on its "Required-still-passing journeys:" metadata line (goal mode). Steps 5 (ui-test-design) and
+# 6 (browser-qa) in run-phase.sh, plus their own standalone scripts' redundant early exits, used to
+# gate ENTIRELY on `Frontend Present: yes` — so a backend-only goal-mode iteration (this session's
+# steady state for ops-only work) skipped UI test design AND browser QA unconditionally, writing
+# bare N/A stubs, even when the iteration spec named required-still-passing journeys that need
+# fresh regression evidence every iteration. Regression re-verification of an EXISTING page needs
+# no NEW UI surface, so `Frontend Present: no` must not suppress it. This was iter-40's actual
+# mechanism for shipping all seven required-still-passing journeys with ZERO evidence (screenshots,
+# replay artifacts, demo steps) while every gate reported clean — the ui-test-designer agent's own
+# "Backend-only phase handling" section (fixed separately this iteration) was never even reached,
+# because these shell-level gates returned before the agent was ever dispatched.
+#
+# Mirrors `lib/replay-lane.sh::replay_lane_spec_journeys`'s extraction (kept dependency-free here —
+# not every caller of this helper also sources replay-lane.sh).
+phase_spec_has_required_regression() {
+  local spec="$1"
+  [[ -n "$(grep -iE 'Required-still-passing' "$spec" 2>/dev/null | head -1 | grep -oE 'J-[0-9]+' | head -1)" ]]
+}
+
 # Pin the QA browser's identity for this project (and lane). The Chrome MCP
 # server reads CHROME_WS_PROFILE/CHROME_WS_PORT from its environment; without
 # them it invents profile names (superpowers-chrome, -2, -3 …) as locks contend,
diff --git a/incredible_auto_dev/scripts/automation/lib/goal_gate.py b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
index 1c1b1b46..fe5e1430 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
@@ -87,6 +87,14 @@ _DEFERRED_CELL_RE = re.compile(r"\|\s*DEFERRED-BUDGET\s*\|")
 # audit). BLOCKED means NOT VERIFIED — exactly the DEFERRED-BUDGET case above — so it must block
 # GOAL_ACHIEVED identically until a later iteration actually replays the journey.
 _BLOCKED_CELL_RE = re.compile(r"\|\s*BLOCKED\s*\|")
+# ops-hardening iter-41 (A3, TC-3): a required-still-passing journey with ZERO executed test cases
+# has no row at all (distinct from an explicit BLOCKED row, which the cell-scan above already
+# catches) -- merge_ui_test_results.merge() forces the file's HEADLINE to BLOCKED in that case
+# without necessarily adding any `| BLOCKED |` table cell (nothing to render a row for -- the whole
+# point is that no lane ever produced one). The cell-scan above cannot see a headline-only BLOCKED,
+# so check the headline too. Same tolerant-of-markdown-emphasis pattern as
+# merge_ui_test_results._VERDICT_RE.
+_UI_HEADLINE_RE = re.compile(r"\*\*Browser QA Verdict:\*\*\s*[*_`~\s]*([A-Z_]+)")
 
 
 def _load_history(path: str) -> dict | None:
@@ -147,8 +155,10 @@ def cmd_results(path: str) -> int:
         text = Path(path).read_text(encoding="utf-8")
     except OSError:
         return 2
-    return 1 if (_FAIL_CELL_RE.search(text) or _DEFERRED_CELL_RE.search(text)
-                 or _BLOCKED_CELL_RE.search(text)) else 0
+    if _FAIL_CELL_RE.search(text) or _DEFERRED_CELL_RE.search(text) or _BLOCKED_CELL_RE.search(text):
+        return 1
+    m = _UI_HEADLINE_RE.search(text)
+    return 1 if (m and m.group(1) == "BLOCKED") else 0
 
 
 def cmd_regressions(pre_path: str, post_path: str) -> int:
@@ -480,6 +490,21 @@ def _self_test() -> int:
             "| T1 | the run was never BLOCKED at any point | ui | P1 | e | a | PASS | x.png |\n",
             encoding="utf-8")
         assert cmd_results(str(res_blocked_prose)) == 0, "BLOCKED must match a whole cell only"
+        # ops-hardening iter-41 (A3, TC-3): a required-still-passing journey with ZERO executed test
+        # cases has no ROW at all, so merge_ui_test_results.merge() forces the HEADLINE to BLOCKED
+        # with no `| BLOCKED |` cell anywhere -- the cell-scan above alone would miss this and let a
+        # run with one entirely-unattempted required journey read as achievable. Every OTHER row here
+        # is a clean PASS -- only the headline (which merge() forces) signals the gap.
+        res_missing_required = d / "r7.md"; res_missing_required.write_text(
+            "**Browser QA Verdict:** BLOCKED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-01 | Backfill honors range | regression | P1 | e | ok | PASS | a.png |\n"
+            "\n## Missing Required Journeys\n\n- `UT-J-03` — no test case executed for J-03 by any lane\n",
+            encoding="utf-8")
+        assert cmd_results(str(res_missing_required)) == 1, (
+            "a headline-only BLOCKED (missing-required journey, no BLOCKED cell) must block GOAL_ACHIEVED"
+        )
 
         # regressions: J-01 passing→failing is caught; missing pre → 0
         post = d / "post.json"
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index 3f2372fc..49e78271 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -156,10 +156,73 @@ def _cell(row: dict, i: int) -> str:
     return cells[i] if i < len(cells) else ""
 
 
-def merge(texts: "list[str]") -> str:
+def missing_required_journeys(rows: "list[dict]", required_journeys: "list[str] | None") -> "list[str]":
+    """Which of `required_journeys` (bare IDs like `J-01`) have ZERO executed test cases in `rows`
+    — i.e. no row at all, not even a BLOCKED/SKIP one. Distinct from BLOCKED (a row exists,
+    recording that the journey's assertions were never checked) and from SKIP (a row exists,
+    recording why it was skipped): "missing" means no lane produced ANY row for this required
+    journey, so nothing about it was even recorded, let alone checked."""
+    if not required_journeys:
+        return []
+    present_ids = {r["test_id"] for r in rows}
+    missing = []
+    for jid in required_journeys:
+        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
+        if tid not in present_ids:
+            missing.append(jid)
+    return missing
+
+
+def skipped_required_journeys(rows: "list[dict]", required_journeys: "list[str] | None") -> "list[str]":
+    """Which of `required_journeys` have a row whose ONLY recorded outcome is `SKIP` — the journey
+    was named, a row exists, and it says "not executed." The companion to
+    `missing_required_journeys` above: iter-40's actual artifact
+    (`reports/phase-goal-ops-hardening-iter-40-ui-test-results.md`) has a row for EVERY required
+    journey, all of them `SKIP` ("Not executed — dispatch instructions state frontend is not
+    available"), so the missing-row check alone still merged it into a clean `SKIPPED` headline —
+    exactly the outcome iter-41's DoD ("an all-SKIP/zero-executed regression run can no longer merge
+    into a clean SKIPPED/PASS headline") forbids, and exactly the shape the spec's own wording
+    requires ("fresh, NON-`SKIP` mechanical verification"). Only a literal `SKIP` counts: a
+    `DEFERRED-BUDGET` row (SPEED-15 rung 2, an explicit "keeps prior status" record) parses to an
+    empty verdict and is deliberately NOT treated as a skip here — `goal_gate.py`'s
+    `_DEFERRED_CELL_RE` already blocks achievement on those."""
+    if not required_journeys:
+        return []
+    by_id = {r["test_id"]: r for r in rows}
+    skipped = []
+    for jid in required_journeys:
+        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
+        row = by_id.get(tid)
+        if row is not None and row["verdict"] == "SKIP":
+            skipped.append(jid)
+    return skipped
+
+
+def merge(texts: "list[str]", required_journeys: "list[str] | None" = None) -> str:
     """Merge in order; later inputs win per Test ID. Returns the merged markdown
     with a single authoritative headline verdict and detail rebuilt from the
-    surviving rows (no verbatim per-lane embedding → exactly one verdict line)."""
+    surviving rows (no verbatim per-lane embedding → exactly one verdict line).
+
+    `required_journeys` (ops-hardening iter-41, A3 — TC-3): the iteration spec's own
+    "Required-still-passing journeys:" list (bare IDs, e.g. `["J-01", "J-03"]`). iter-40 shipped
+    ALL seven required-still-passing journeys with ZERO executed test cases while every gate
+    (including this merger) reported a clean headline, because a journey with NO row at all was
+    invisible to `compute_overall` — it only ever reasons about rows that exist. When at least one
+    required journey has zero executed test cases (see `missing_required_journeys` above) AND the
+    rows-derived headline would otherwise be a CLEAN "PASS" or "SKIPPED", the headline is forced to
+    "BLOCKED" instead — reusing the existing BLOCKED semantics ("never checked at all") rather than
+    inventing a second gate; `goal_gate.py` already blocks achievement on any BLOCKED verdict. A
+    headline that was already FAIL or BLOCKED is left alone (already non-clean; the gap is still
+    surfaced in the new "Missing Required Journeys" section below, but doesn't need to change an
+    already-blocking headline).
+
+    iter-41 audit (B1 fix): the same forcing applies to a required journey whose row exists but
+    reads `SKIP` (`skipped_required_journeys` above). The zero-row check alone did NOT close
+    iter-40's own failure mode — that run's merged file carries a `SKIP` row for all seven required
+    journeys, so it still merged to a clean `SKIPPED` headline under the first implementation of
+    this guard (reproduced directly against the committed iter-40 artifact). Both shapes mean the
+    same thing to a reader of the headline — "this journey was not verified this iteration" — so
+    both force `BLOCKED`."""
     by_id: "dict[str, dict]" = {}
     order: "list[str]" = []
     file_verdicts: "list[str]" = []
@@ -172,6 +235,10 @@ def merge(texts: "list[str]") -> str:
             by_id[tid] = row  # later wins
     rows = [by_id[t] for t in order]
     overall = compute_overall(rows, file_verdicts)
+    missing_required = missing_required_journeys(rows, required_journeys)
+    skipped_required = skipped_required_journeys(rows, required_journeys)
+    if (missing_required or skipped_required) and overall in ("PASS", "SKIPPED"):
+        overall = "BLOCKED"
     n_pass = sum(1 for r in rows if r["verdict"] == "PASS")
     n_skip = sum(1 for r in rows if r["verdict"] == "SKIP")
     n_blocked = sum(1 for r in rows if r["verdict"] == "BLOCKED")
@@ -179,6 +246,8 @@ def merge(texts: "list[str]") -> str:
 
     overall_line = f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped"
     overall_line += f", {n_blocked} blocked" if n_blocked else ""
+    overall_line += f", {len(missing_required)} required-missing" if missing_required else ""
+    overall_line += f", {len(skipped_required)} required-unverified" if skipped_required else ""
     overall_line += ")"
     out = ["# UI Test Results (merged)", "",
            f"**Date:** {_today()}",
@@ -196,6 +265,19 @@ def merge(texts: "list[str]") -> str:
     failed = [r for r in rows if r["verdict"] == "FAIL"]
     skipped = [r for r in rows if r["verdict"] == "SKIP"]
     blocked = [r for r in rows if r["verdict"] == "BLOCKED"]
+    if missing_required or skipped_required:
+        out += ["## Missing Required Journeys", "",
+                "_Required-still-passing journeys named in the iteration spec that were NOT "
+                "verified this iteration — either no lane (deterministic replay or LLM browser-qa) "
+                "produced a row for them at all, or the only row they have reads SKIP (not "
+                "executed). Never a clean PASS/SKIPPED headline while any of these are present "
+                "(ops-hardening iter-40 lesson: this is exactly how required journeys shipped with "
+                "zero evidence while every gate reported clean)._", ""]
+        for jid in missing_required:
+            out.append(f"- `UT-{jid}` — no test case executed for {jid} by any lane")
+        for jid in skipped_required:
+            out.append(f"- `UT-{jid}` — only a SKIP row for {jid}: named but never executed")
+        out.append("")
     if failed:
         out += ["## Failed Tests", ""]
         for r in failed:
@@ -318,8 +400,31 @@ def main(argv: "list[str]") -> int:
             sys.stderr.write("usage: merge_ui_test_results.py verdict-of <results.md> <test-id>\n")
             return 2
         return cmd_verdict_of(argv[1], argv[2])
+    # ops-hardening iter-41 (A3): an optional `--required J-01,J-03,...` flag (space- or
+    # comma-separated; may appear anywhere in argv) names this iteration's required-still-passing
+    # journeys, so `merge` can detect any with ZERO executed test cases. Absent (the pre-iter-41
+    # call shape every existing caller still uses until its bash wiring passes this) => no change
+    # in behavior, matching every pre-existing test in this file's self-test suite.
+    required: list[str] = []
+    rest: list[str] = []
+    i = 0
+    while i < len(argv):
+        a = argv[i]
+        if a == "--required" and i + 1 < len(argv):
+            required = [j for j in argv[i + 1].replace(",", " ").split() if j]
+            i += 2
+            continue
+        if a.startswith("--required="):
+            required = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
+            i += 1
+            continue
+        rest.append(a)
+        i += 1
+    argv = rest
     if len(argv) < 2:
-        sys.stderr.write("usage: merge_ui_test_results.py <out.md> <in1.md> [<in2.md> ...]\n")
+        sys.stderr.write(
+            "usage: merge_ui_test_results.py [--required J-01,J-03,...] <out.md> <in1.md> [<in2.md> ...]\n"
+        )
         return 2
     out_path = Path(argv[0])
     texts: list[str] = []
@@ -331,7 +436,7 @@ def main(argv: "list[str]") -> int:
         sys.stderr.write("[merge_ui_test_results] no readable input files\n")
         return 2
     out_path.parent.mkdir(parents=True, exist_ok=True)
-    out_path.write_text(merge(texts), encoding="utf-8")
+    out_path.write_text(merge(texts, required_journeys=required), encoding="utf-8")
     print(f"[merge_ui_test_results] merged {len(texts)} file(s) → {out_path}")
     return 0
 
@@ -550,6 +655,110 @@ def _self_test() -> int:
         assert len(re.split(r"(?<!\\)\|", row)) == len(re.split(r"(?<!\\)\|",
             "| UT-J-07 | Filter \\| sort table | regression | P1 | e | step 2 failed | FAIL | b.png |")), row
 
+    # ==============================================================================================
+    # ops-hardening iter-41 (A3, TC-3) — a required-still-passing journey with ZERO executed test
+    # cases must never merge into a clean PASS/SKIPPED headline.
+    # ==============================================================================================
+    clean_pair = (
+        "**Browser QA Verdict:** PASS\n\n## Results Table\n"
+        "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+        "|---|---|---|---|---|---|---|---|\n"
+        "| UT-J-01 | Backfill honors range | regression | P1 | e | ok | PASS | a.png |\n")
+
+    def t_missing_required_journey_blocks_clean_pass():
+        # iter-40's own failure mode reproduced: J-03 is required-still-passing but NO lane ever
+        # produced a row for it (unlike BLOCKED, where a row exists recording "never checked") --
+        # the merge must not headline a clean PASS while that gap is invisible.
+        md = merge([clean_pair], required_journeys=["J-01", "J-03"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Required Journeys" in md and "UT-J-03" in md
+        # the journey that DID execute keeps its own row/verdict untouched.
+        assert verdict_for(md, "UT-J-01") == "PASS", verdict_for(md, "UT-J-01")
+
+    def t_missing_required_journey_blocks_clean_skipped():
+        skip_only = (
+            "**Browser QA Verdict:** SKIPPED\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-09 | Export | regression | P1 | e | no script | SKIP | none |\n")
+        md = merge([skip_only], required_journeys=["J-01"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Required Journeys" in md and "UT-J-01" in md
+
+    def t_all_skip_required_journeys_block_clean_skipped():
+        # iter-41 audit (B1): iter-40's ACTUAL artifact shape — a row EXISTS for every required
+        # journey, and every one of them reads SKIP ("not executed"). The zero-row check alone
+        # left this merging into a clean SKIPPED headline, which is precisely the DoD line
+        # "an all-SKIP/zero-executed regression run can no longer merge into a clean
+        # SKIPPED/PASS headline".
+        all_skip = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-01 | Backfill honors range | regression | P1 | e | Not executed — frontend down | SKIP | none |\n"
+            "| UT-J-03 | No per-run range cap | regression | P1 | e | Not executed — frontend down | SKIP | none |\n")
+        md = merge([all_skip], required_journeys=["J-01", "J-03"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Required Journeys" in md
+        assert "only a SKIP row for J-01" in md and "only a SKIP row for J-03" in md
+
+    def t_mixed_skip_and_pass_blocks_only_on_the_skip():
+        # A required journey that really was executed keeps its PASS; the one that only has a
+        # SKIP row still forces the headline off clean.
+        mixed = (
+            "**Browser QA Verdict:** PASS\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-01 | Backfill honors range | regression | P1 | e | ok | PASS | a.png |\n"
+            "| UT-J-03 | No per-run range cap | regression | P1 | e | Not executed | SKIP | none |\n")
+        md = merge([mixed], required_journeys=["J-01", "J-03"])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert verdict_for(md, "UT-J-01") == "PASS", verdict_for(md, "UT-J-01")
+        assert "only a SKIP row for J-03" in md
+        # a NON-required journey's SKIP row must NOT trip the guard
+        md2 = merge([mixed], required_journeys=["J-01"])
+        assert file_top_verdict(md2) == "PASS", file_top_verdict(md2)
+        assert "## Missing Required Journeys" not in md2
+
+    def t_all_required_present_stays_clean():
+        # No missing required journey -> headline and rendering are UNCHANGED (no regression on the
+        # common case, and no "Missing Required Journeys" section when there is nothing missing).
+        md = merge([clean_pair], required_journeys=["J-01"])
+        assert file_top_verdict(md) == "PASS", file_top_verdict(md)
+        assert "## Missing Required Journeys" not in md
+
+    def t_no_required_journeys_arg_unchanged():
+        # The default (no `required_journeys` argument at all) is BYTE-IDENTICAL to before this
+        # iteration -- every pre-existing caller of merge() until its bash wiring passes `--required`.
+        assert merge([clean_pair]) == merge([clean_pair], required_journeys=None)
+        assert merge([clean_pair], required_journeys=[]) == merge([clean_pair])
+
+    def t_missing_required_never_downgrades_fail_or_blocked():
+        # A real FAIL (or an existing BLOCKED) elsewhere must stay exactly that -- the missing-
+        # required check only ever prevents a CLEAN PASS/SKIPPED, never overrides a worse verdict.
+        fail_pair = (
+            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-01 | Backfill honors range | regression | P1 | e | step 2 failed | FAIL | a.png |\n")
+        md = merge([fail_pair], required_journeys=["J-01", "J-99"])
+        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
+        assert "## Missing Required Journeys" in md and "UT-J-99" in md
+
+    def t_missing_required_via_cli_required_flag():
+        # main()'s `--required` parsing (anywhere in argv, comma- or space-separated) reaches merge()
+        # exactly like the direct kwarg above -- the bash wiring in lib/replay-lane.sh depends on this.
+        import tempfile
+        with tempfile.TemporaryDirectory() as td:
+            out = f"{td}/out.md"
+            in1 = f"{td}/in1.md"
+            Path(in1).write_text(clean_pair, encoding="utf-8")
+            rc = main(["--required", "J-01,J-03", out, in1])
+            assert rc == 0, rc
+            merged = Path(out).read_text(encoding="utf-8")
+            assert file_top_verdict(merged) == "BLOCKED", file_top_verdict(merged)
+            assert "UT-J-03" in merged
+
     # Self-counting list (local form) rather than a hardcoded total — upstream's void
     # tests and the local verdict-normalization tests both live here, so a literal
     # count goes stale on the next pull.
@@ -566,7 +775,15 @@ def _self_test() -> int:
               ("void_rewrites_and_recomputes", t_void_rewrites_and_recomputes),
               ("void_keeps_unlisted_fail", t_void_keeps_unlisted_fail),
               ("void_no_match_is_noop", t_void_no_match_is_noop),
-              ("void_respects_escaped_pipes", t_void_respects_escaped_pipes)]
+              ("void_respects_escaped_pipes", t_void_respects_escaped_pipes),
+              ("missing_required_journey_blocks_clean_pass", t_missing_required_journey_blocks_clean_pass),
+              ("missing_required_journey_blocks_clean_skipped", t_missing_required_journey_blocks_clean_skipped),
+              ("all_skip_required_journeys_block_clean_skipped", t_all_skip_required_journeys_block_clean_skipped),
+              ("mixed_skip_and_pass_blocks_only_on_the_skip", t_mixed_skip_and_pass_blocks_only_on_the_skip),
+              ("all_required_present_stays_clean", t_all_required_present_stays_clean),
+              ("no_required_journeys_arg_unchanged", t_no_required_journeys_arg_unchanged),
+              ("missing_required_never_downgrades_fail_or_blocked", t_missing_required_never_downgrades_fail_or_blocked),
+              ("missing_required_via_cli_required_flag", t_missing_required_via_cli_required_flag)]
     for name, fn in checks:
         check(name, fn)
 
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index 4c86a2d8..b055798e 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -451,7 +451,15 @@ replay_lane_merge_results() {
   local _rl_out="$1" _rl_llm="$2"
   local _rl_mid=()
   [[ -n "${CANARY_RESULTS:-}" && -f "${CANARY_RESULTS:-}" ]] && _rl_mid=("$CANARY_RESULTS")
-  if ! python3 "$MERGE_RESULTS" "$_rl_out" "$REGRESSION_RESULTS" ${_rl_mid[@]+"${_rl_mid[@]}"} "$_rl_llm"; then
+  # ops-hardening iter-41 (A3): pass this iteration's required-still-passing journeys (set as a
+  # global by the caller before partition_and_verify -- browser-qa-phase.sh/goal-iter-lean.sh both
+  # compute REQUIRED_JOURNEYS via replay_lane_spec_journeys before calling in) through to the
+  # merger so a required journey with ZERO executed test cases can never merge into a clean
+  # PASS/SKIPPED headline (TC-3). Empty when this is plain phase mode (REQUIRED_JOURNEYS unset) --
+  # merge()'s new check is then a no-op, unchanged behavior.
+  local _rl_required_args=()
+  [[ -n "${REQUIRED_JOURNEYS:-}" && -n "${REQUIRED_JOURNEYS// /}" ]] && _rl_required_args=(--required "$REQUIRED_JOURNEYS")
+  if ! python3 "$MERGE_RESULTS" "${_rl_required_args[@]}" "$_rl_out" "$REGRESSION_RESULTS" ${_rl_mid[@]+"${_rl_mid[@]}"} "$_rl_llm"; then
     _replay_lane_warn "results merge failed — falling back to a lane output."
     if [[ -f "$_rl_llm" ]]; then cp "$_rl_llm" "$_rl_out" 2>/dev/null || true
     elif [[ -f "$REGRESSION_RESULTS" ]]; then cp "$REGRESSION_RESULTS" "$_rl_out" 2>/dev/null || true; fi
diff --git a/incredible_auto_dev/scripts/automation/lib/verdicts.py b/incredible_auto_dev/scripts/automation/lib/verdicts.py
index a2a17827..33df3428 100644
--- a/incredible_auto_dev/scripts/automation/lib/verdicts.py
+++ b/incredible_auto_dev/scripts/automation/lib/verdicts.py
@@ -54,10 +54,19 @@ class UXRegressionVerdict(str, Enum):
 
 
 class BrowserQAVerdict(str, Enum):
-    """Browser QA verdicts (reports/phase-{N}-ui-test-results.md)."""
+    """Browser QA verdicts (reports/phase-{N}-ui-test-results.md).
+
+    BLOCKED (ops-hardening iter-40/41, A4): a DISTINCT class from FAIL — a journey's own
+    assertions were never checked at all (e.g. the backend was unreachable, or a required-still-
+    passing journey had zero executed test cases), not that they were checked and failed. Already
+    shipped in `merge_ui_test_results.py`/`demo_runner.py`/`goal_gate.py` since iter-39/40; this
+    enum (the single source of truth every report agent's verdict line is validated against) had
+    not caught up — a bare `**Browser QA Verdict:** BLOCKED` line failed `validate-verdict`-style
+    checks against this enum even though every consumer downstream already understood it."""
     PASS = "PASS"
     FAIL = "FAIL"
     SKIPPED = "SKIPPED"
+    BLOCKED = "BLOCKED"
 
 
 class GoalEvalVerdict(str, Enum):
diff --git a/incredible_auto_dev/scripts/automation/qa-phase.sh b/incredible_auto_dev/scripts/automation/qa-phase.sh
index 1e2b9a34..107000a1 100755
--- a/incredible_auto_dev/scripts/automation/qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/qa-phase.sh
@@ -86,7 +86,10 @@ fi
 # Derive URLs from port env vars (set by run-phase.sh for port isolation)
 _BACKEND_PORT="${CHAIN_BACKEND_PORT:-8000}"
 _FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-3000}"
-BACKEND_HEALTH_URL="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${_BACKEND_PORT}/health}"
+# ops-hardening iter-41 (A1): resolve the project-specific health path (Trendora's
+# `/api/health`, not the framework's generic `/health`) via the shared helper — see
+# `lib/common.sh::resolve_backend_health_url`.
+BACKEND_HEALTH_URL="$(resolve_backend_health_url "$_BACKEND_PORT")"
 FRONTEND_URL="${CHAIN_FRONTEND_URL:-http://localhost:${_FRONTEND_PORT}}"
 
 # Export vars consumed by ensure_services_running (shared helper in common.sh).
diff --git a/incredible_auto_dev/scripts/automation/run-phase.sh b/incredible_auto_dev/scripts/automation/run-phase.sh
index c7932b00..dbbbf6c6 100755
--- a/incredible_auto_dev/scripts/automation/run-phase.sh
+++ b/incredible_auto_dev/scripts/automation/run-phase.sh
@@ -215,7 +215,10 @@ _render_summary_html() {
 _boot_shared_services() {
   local _be_port="${CHAIN_BACKEND_PORT:-8000}"
   local _fe_port="${CHAIN_FRONTEND_PORT:-3000}"
-  local _be_health="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${_be_port}/health}"
+  # ops-hardening iter-41 (A1): resolve the project-specific health path (Trendora's
+  # `/api/health`, not the framework's generic `/health`) via the shared helper — see
+  # `lib/common.sh::resolve_backend_health_url`.
+  local _be_health; _be_health="$(resolve_backend_health_url "$_be_port")"
   local _fe_url="${CHAIN_FRONTEND_URL:-http://localhost:${_fe_port}}"
   local _be_cmd="${CHAIN_START_BACKEND_CMD:-}"
   local _fe_cmd="${CHAIN_START_FRONTEND_CMD:-}"
@@ -867,7 +870,10 @@ echo ""
 
 # ── Step 5/11: UI Test Design ─────────────────────────────────────────────────
 if [[ "$SKIP_UI_TEST_DESIGN" == "false" ]]; then
-  if [[ "$FRONTEND_PRESENT" == "yes" ]]; then
+  # ops-hardening iter-41 (A1 companion fix): a backend-only goal-mode iteration with
+  # required-still-passing journeys still needs this step -- regression re-verification of an
+  # EXISTING page needs no NEW UI surface. See lib/common.sh::phase_spec_has_required_regression.
+  if [[ "$FRONTEND_PRESENT" == "yes" ]] || phase_spec_has_required_regression "$SPEC"; then
     log "Step 5/11 -- UI Test Design..."
     utd_q=0
     while true; do
@@ -892,7 +898,9 @@ echo ""
 
 # ── Step 6/11: Browser QA ─────────────────────────────────────────────────────
 if [[ "$SKIP_BROWSER_QA" == "false" ]]; then
-  if [[ "$FRONTEND_PRESENT" == "yes" ]]; then
+  # ops-hardening iter-41 (A1 companion fix): same carve-out as Step 5 above -- required-still-
+  # passing journeys need fresh browser-QA evidence even on a backend-only iteration.
+  if [[ "$FRONTEND_PRESENT" == "yes" ]] || phase_spec_has_required_regression "$SPEC"; then
     log "Step 6/11 -- Browser QA..."
     # Clear stale results so a script crash before write doesn't leave
     # an old run's results pretending to be this run's.
diff --git a/incredible_auto_dev/scripts/automation/ui-test-design-phase.sh b/incredible_auto_dev/scripts/automation/ui-test-design-phase.sh
index 9a8fb83c..2bc492f3 100755
--- a/incredible_auto_dev/scripts/automation/ui-test-design-phase.sh
+++ b/incredible_auto_dev/scripts/automation/ui-test-design-phase.sh
@@ -38,13 +38,22 @@ if detect_frontend_in_plan "$PLAN_FILE"; then
   FRONTEND_PRESENT="yes"
 fi
 
-# Skip for backend-only phases
-if [[ "$FRONTEND_PRESENT" == "no" ]]; then
+# Skip for backend-only phases -- UNLESS this is a goal-mode iteration naming
+# required-still-passing journeys (ops-hardening iter-41, A1 companion fix): those
+# journeys still need one UT-J-XX regression test case each every iteration, and
+# regression re-verification of an EXISTING page needs no NEW UI surface. See
+# lib/common.sh::phase_spec_has_required_regression and the ui-test-designer
+# agent's own "Backend-only phase handling" section, which stubs NEW-surface
+# generation only and still emits the required-still-passing rows.
+if [[ "$FRONTEND_PRESENT" == "no" ]] && ! phase_spec_has_required_regression "$SPEC"; then
   echo "[ui-test-design] Backend-only phase — writing N/A stubs."
   write_na_ui_artifacts "$PHASE" "ui-test-plan" "what-to-click"
   echo "[ui-test-design] Done (backend-only, N/A stubs written)."
   exit 0
 fi
+if [[ "$FRONTEND_PRESENT" == "no" ]]; then
+  echo "[ui-test-design] Backend-only phase, but required-still-passing journeys are named — running the agent for regression-only test-case generation (no NEW-surface cases)."
+fi
 
 # Verify dependencies
 if [[ ! -f "$USER_VISIBLE" ]]; then
@@ -64,6 +73,16 @@ if [[ -f "$EXISTING_TEST_PLAN" ]]; then
   EXISTING_TEST_PLAN_NOTE="Existing functional test plan: $EXISTING_TEST_PLAN  <-- read for context, do not duplicate API tests"
 fi
 
+BACKEND_ONLY_REGRESSION_NOTE=""
+if [[ "$FRONTEND_PRESENT" == "no" ]]; then
+  BACKEND_ONLY_REGRESSION_NOTE="
+NOTE: This phase spec's metadata says \`Frontend Present: no\` (no NEW UI surface this iteration) —
+follow your agent instructions' \"Backend-only phase handling\" section EXACTLY: stub out NEW-surface
+test-case generation only. You MUST still emit one UT-J-XX regression test case for EVERY journey
+named on the Phase spec file's own \"Required-still-passing journeys:\" metadata line (see the Phase
+spec path above) — do not write a bare N/A stub if that line names any journey."
+fi
+
 _FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-3000}"
 FRONTEND_URL="${CHAIN_FRONTEND_URL:-http://localhost:${_FRONTEND_PORT}}"
 
@@ -85,6 +104,7 @@ Execution plan: $PLAN_FILE
 User-visible changes: $USER_VISIBLE  <-- read this first
 UI surface map: $UI_SURFACE_MAP  <-- read this for surfaces to test
 $EXISTING_TEST_PLAN_NOTE
+$BACKEND_ONLY_REGRESSION_NOTE
 
 Frontend URL: $FRONTEND_URL
 
diff --git a/apps/backend/tests/test_faulthandler_sigusr1_diagnostic.py b/apps/backend/tests/test_faulthandler_sigusr1_diagnostic.py
new file mode 100644
index 00000000..e3e06874
--- /dev/null
+++ b/apps/backend/tests/test_faulthandler_sigusr1_diagnostic.py
@@ -0,0 +1,121 @@
+"""ops-hardening iter-41 (C7) — `main.py`'s opt-in `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1` diagnostic.
+
+Proves the ONE property the wedge-drill actually depends on: with the env var set, sending
+`SIGUSR1` to a process that has imported `main` dumps an all-thread stack trace and the process
+SURVIVES; without it, `main` never touches `SIGUSR1` at all (default disposition — the signal would
+terminate a bare process, which is exactly how the test distinguishes "registered" from "not").
+
+Runs `main.py`'s import in a SUBPROCESS (never in the pytest process itself) so this never mutates
+the test runner's own signal handlers — `faulthandler.register` is process-global and irreversible
+within the process that calls it."""
+from __future__ import annotations
+
+import os
+import re
+import signal
+import subprocess
+import sys
+import time
+from pathlib import Path
+
+import pytest
+
+# Matches faulthandler's per-thread header in BOTH forms it emits:
+#   "Current thread 0x00007f... (most recent call first):"  (the signalled thread)
+#   "Thread 0x00007f... (most recent call first):"          (every other live thread)
+_THREAD_ID_LINE_RE = re.compile(r"^(?:Current )?thread 0x[0-9a-f]+ ", re.IGNORECASE | re.MULTILINE)
+
+_BACKEND_DIR = Path(__file__).resolve().parents[1]
+_IMPORT_MAIN = (
+    "import sys; sys.path.insert(0, %r); "
+    "import main; "  # noqa -- imports the FastAPI app module under test, side effects are the point
+    "import time; sys.stderr.write('READY\\n'); sys.stderr.flush(); time.sleep(10)"
+) % str(_BACKEND_DIR)
+
+
+def _spawn(env_extra: dict) -> subprocess.Popen:
+    env = dict(os.environ)
+    env.update(env_extra)
+    # Isolate from any real backend DB/port env the host session may have exported.
+    env.pop("CHAIN_BACKEND_PORT", None)
+    return subprocess.Popen(
+        [sys.executable, "-c", _IMPORT_MAIN],
+        cwd=str(_BACKEND_DIR),
+        env=env,
+        stdout=subprocess.PIPE,
+        stderr=subprocess.PIPE,
+        text=True,
+    )
+
+
+def _wait_for_ready(proc: subprocess.Popen, timeout: float = 30.0) -> str:
+    """Block until the subprocess writes READY to stderr (import + app construction done), or the
+    process exits early (import failure) -- returns whatever stderr was captured so far either way."""
+    deadline = time.time() + timeout
+    buf = ""
+    while time.time() < deadline:
+        line = proc.stderr.readline()
+        if line:
+            buf += line
+            if "READY" in line:
+                return buf
+        if proc.poll() is not None:
+            buf += proc.stderr.read()
+            return buf
+    return buf
+
+
+def test_sigusr1_armed_dumps_all_thread_stack_and_survives():
+    proc = _spawn({"TRENDORA_DIAG_FAULTHANDLER_SIGUSR1": "1"})
+    try:
+        ready_log = _wait_for_ready(proc)
+        assert proc.poll() is None, f"subprocess exited before READY (import failed?): {ready_log}"
+
+        proc.send_signal(signal.SIGUSR1)
+        time.sleep(1.0)  # faulthandler writes synchronously on signal receipt
+
+        assert proc.poll() is None, "the process must SURVIVE SIGUSR1 when faulthandler is armed"
+
+        proc.send_signal(signal.SIGTERM)
+        _, stderr = proc.communicate(timeout=10)
+        # faulthandler's all-threads dump heads each live thread's stack with a thread-id line:
+        # "Current thread 0x<id> (most recent call first):" for the signalled thread and
+        # "Thread 0x<id> (most recent call first):" for every other one. This subprocess is
+        # single-threaded, so only the lowercase "Current thread" form appears -- match the
+        # id line case-insensitively so BOTH forms satisfy it, then require at least one real
+        # stack frame ('File "..." , line N in ...') so an empty header alone cannot pass.
+        assert _THREAD_ID_LINE_RE.search(stderr) and 'File "' in stderr, (
+            f"expected an all-thread stack dump on SIGUSR1, got stderr: {stderr!r}"
+        )
+    finally:
+        if proc.poll() is None:
+            proc.kill()
+            proc.wait(timeout=5)
+
+
+def test_sigusr1_unarmed_by_default_leaves_default_disposition():
+    """The env var is opt-in: with it UNSET (the real-deployment default), `main` never touches
+    SIGUSR1 -- the signal keeps its default disposition (terminate), proving nothing about this
+    diagnostic is on by default."""
+    proc = _spawn({})  # TRENDORA_DIAG_FAULTHANDLER_SIGUSR1 absent
+    try:
+        ready_log = _wait_for_ready(proc)
+        assert proc.poll() is None, f"subprocess exited before READY (import failed?): {ready_log}"
+
+        proc.send_signal(signal.SIGUSR1)
+        try:
+            proc.wait(timeout=5)
+        except subprocess.TimeoutExpired:
+            pytest.fail(
+                "process survived SIGUSR1 with the diagnostic env var UNSET -- faulthandler must "
+                "not be armed by default"
+            )
+        # default SIGUSR1 disposition terminates the process; Popen reports this as a negative
+        # returncode equal to -SIGUSR1 on POSIX.
+        assert proc.returncode == -signal.SIGUSR1, (
+            f"expected default-disposition termination (-{int(signal.SIGUSR1)}), got {proc.returncode}"
+        )
+    finally:
+        if proc.poll() is None:
+            proc.kill()
+            proc.wait(timeout=5)
diff --git a/incredible_auto_dev/tests/automation/test-backend-only-regression-gate.sh b/incredible_auto_dev/tests/automation/test-backend-only-regression-gate.sh
new file mode 100755
index 00000000..7d1205cd
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-backend-only-regression-gate.sh
@@ -0,0 +1,96 @@
+#!/usr/bin/env bash
+# test-backend-only-regression-gate.sh — ops-hardening iter-41 (A1 companion fix, TC-1/TC-4):
+# a backend-only (`Frontend Present: no`) goal-mode iteration that names required-still-passing
+# journeys must still run UI test design (Step 5) and browser QA (Step 6) for those journeys'
+# regression re-verification — a bare N/A stub (the old unconditional behavior) left every one of
+# them completely unverified while every gate reported clean (iter-40's ESCALATE root cause: the
+# ui-test-designer agent's own "Backend-only phase handling" fix was unreachable because these
+# shell-level gates returned before the agent was ever dispatched).
+#
+# Two things proven:
+#   1. `lib/common.sh::phase_spec_has_required_regression` itself — a spec naming at least one
+#      "Required-still-passing journeys:" J-ID -> true; a spec with none/absent -> false.
+#   2. Regression guard: run-phase.sh's Step 5/6 gates and the two standalone phase scripts
+#      (ui-test-design-phase.sh, browser-qa-phase.sh) all consult the helper before falling back
+#      to the backend-only N/A-stub path.
+#
+# Offline, no model, <1s.
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+LIB="$REPO_ROOT/scripts/automation/lib/common.sh"
+
+PASS=0
+FAIL=0
+assert() {
+  local label="$1" result="$2"
+  if [[ "$result" == "pass" ]]; then
+    echo "  PASS  $label"; PASS=$((PASS+1))
+  else
+    echo "  FAIL  $label"; FAIL=$((FAIL+1))
+  fi
+}
+
+T=$(TMPDIR=/tmp mktemp -d)
+trap 'rm -rf "$T"' EXIT
+
+# ── 1. A spec naming required-still-passing journeys -> true ─────────────────────────────────
+cat > "$T/with-journeys.md" <<'EOF'
+## Goal Mode Metadata
+
+- **Session ID:** ops-hardening
+- **Iteration:** 41
+- **Frontend Present:** no
+- **Target journeys:** J-05, J-07
+- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
+EOF
+rc=0
+bash -c 'set -euo pipefail; source "'"$LIB"'"; phase_spec_has_required_regression "'"$T"'/with-journeys.md"' || rc=$?
+[[ $rc -eq 0 ]] \
+  && assert "spec naming 6 required-still-passing journeys -> true" "pass" \
+  || assert "spec naming 6 required-still-passing journeys -> true (rc=$rc)" "fail"
+
+# ── 2. A spec with "none" on that line -> false ───────────────────────────────────────────────
+cat > "$T/none.md" <<'EOF'
+- **Frontend Present:** no
+- **Required-still-passing journeys:** none — first iteration, nothing to regress yet
+EOF
+rc=0
+bash -c 'set -euo pipefail; source "'"$LIB"'"; phase_spec_has_required_regression "'"$T"'/none.md"' || rc=$?
+[[ $rc -ne 0 ]] \
+  && assert "spec with 'none' on the required-regression line -> false" "pass" \
+  || assert "spec with 'none' on the required-regression line -> false (rc=$rc)" "fail"
+
+# ── 3. A spec with no such line at all (plain phase mode) -> false ───────────────────────────
+cat > "$T/plain.md" <<'EOF'
+# phase-3 — Add watchlist export
+Some ordinary phase-mode spec with no goal-mode metadata block at all.
+EOF
+rc=0
+bash -c 'set -euo pipefail; source "'"$LIB"'"; phase_spec_has_required_regression "'"$T"'/plain.md"' || rc=$?
+[[ $rc -ne 0 ]] \
+  && assert "plain phase-mode spec (no goal-mode metadata) -> false" "pass" \
+  || assert "plain phase-mode spec (no goal-mode metadata) -> false (rc=$rc)" "fail"
+
+# ── 4. Regression guard: the three call sites reference the helper ───────────────────────────
+declare -A CALLERS=(
+  ["run-phase.sh"]=2
+  ["ui-test-design-phase.sh"]=1
+  ["browser-qa-phase.sh"]=1
+)
+for f in "${!CALLERS[@]}"; do
+  path="$REPO_ROOT/scripts/automation/$f"
+  n=$(grep -c 'phase_spec_has_required_regression' "$path" 2>/dev/null || true)
+  n=${n:-0}
+  if [[ "$n" -ge "${CALLERS[$f]}" ]]; then
+    assert "$f: consults phase_spec_has_required_regression ($n call site(s))" "pass"
+  else
+    assert "$f: consults phase_spec_has_required_regression (expected >= ${CALLERS[$f]}, got $n)" "fail"
+  fi
+done
+
+echo ""
+echo "=== Results: $PASS passed, $FAIL failed ==="
+[[ $FAIL -gt 0 ]] && exit 1
+exit 0
diff --git a/incredible_auto_dev/tests/automation/test-blocked-verdict-grep-sites.sh b/incredible_auto_dev/tests/automation/test-blocked-verdict-grep-sites.sh
new file mode 100755
index 00000000..ff9e86d1
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-blocked-verdict-grep-sites.sh
@@ -0,0 +1,67 @@
+#!/usr/bin/env bash
+# test-blocked-verdict-grep-sites.sh — ops-hardening iter-41 (A4, TC-9): `BLOCKED` joins
+# `verdicts.py::BrowserQAVerdict` (previously PASS/FAIL/SKIPPED only) and every one of
+# goal-iter-lean.sh's four `grep -oE 'PASS|FAIL|SKIPPED'` verdict-extraction sites also matches it
+# (audit iter-40 finding T3: before this fix, extracting a BLOCKED headline's verdict word silently
+# produced an EMPTY string — "fail-safe by accident, not by contract").
+#
+# Two things proven:
+#   1. `BrowserQAVerdict` (verdicts.py) accepts "BLOCKED" as a legal member.
+#   2. All four grep sites in goal-iter-lean.sh extract "BLOCKED" correctly from a
+#      `**Browser QA Verdict:** BLOCKED` line (not an empty string).
+#
+# Offline, no model, <1s.
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+LEAN="$REPO_ROOT/scripts/automation/goal-iter-lean.sh"
+VERDICTS_PY="$REPO_ROOT/scripts/automation/lib/verdicts.py"
+
+PASS=0
+FAIL=0
+assert() {
+  local label="$1" result="$2"
+  if [[ "$result" == "pass" ]]; then
+    echo "  PASS  $label"; PASS=$((PASS+1))
+  else
+    echo "  FAIL  $label"; FAIL=$((FAIL+1))
+  fi
+}
+
+# ── 1. BrowserQAVerdict accepts BLOCKED as a legal enum member ───────────────────────────────
+rc=0
+out=$(python3 -c "
+import sys
+sys.path.insert(0, '$(dirname "$VERDICTS_PY")')
+from verdicts import BrowserQAVerdict
+print(BrowserQAVerdict('BLOCKED').value)
+") || rc=$?
+[[ $rc -eq 0 && "$out" == "BLOCKED" ]] \
+  && assert "BrowserQAVerdict accepts BLOCKED" "pass" \
+  || assert "BrowserQAVerdict accepts BLOCKED (rc=$rc, got '$out')" "fail"
+
+# ── 2. Every grep -oE site in goal-iter-lean.sh matches BLOCKED ──────────────────────────────
+n_sites=$(grep -c "grep -oE 'PASS|FAIL|SKIPPED" "$LEAN" || true)
+n_sites=${n_sites:-0}
+[[ "$n_sites" -eq 4 ]] \
+  && assert "goal-iter-lean.sh has exactly 4 verdict-extraction grep sites (got $n_sites)" "pass" \
+  || assert "goal-iter-lean.sh has exactly 4 verdict-extraction grep sites (got $n_sites, expected 4)" "fail"
+
+n_with_blocked=$(grep -c "grep -oE 'PASS|FAIL|SKIPPED|BLOCKED'" "$LEAN" || true)
+n_with_blocked=${n_with_blocked:-0}
+[[ "$n_with_blocked" -eq "$n_sites" && "$n_sites" -gt 0 ]] \
+  && assert "all $n_sites site(s) include BLOCKED in the pattern" "pass" \
+  || assert "all site(s) include BLOCKED in the pattern (got $n_with_blocked of $n_sites)" "fail"
+
+# ── 3. Functional: the pattern actually extracts BLOCKED, not an empty string ────────────────
+line='**Browser QA Verdict:** BLOCKED'
+extracted="$(echo "$line" | grep -oE 'PASS|FAIL|SKIPPED|BLOCKED' | head -1)"
+[[ "$extracted" == "BLOCKED" ]] \
+  && assert "the widened pattern extracts BLOCKED (not empty) from a BLOCKED headline" "pass" \
+  || assert "the widened pattern extracts BLOCKED (not empty) from a BLOCKED headline (got '$extracted')" "fail"
+
+echo ""
+echo "=== Results: $PASS passed, $FAIL failed ==="
+[[ $FAIL -gt 0 ]] && exit 1
+exit 0
diff --git a/incredible_auto_dev/tests/automation/test-health-url-resolution.sh b/incredible_auto_dev/tests/automation/test-health-url-resolution.sh
new file mode 100755
index 00000000..1081dbdb
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-health-url-resolution.sh
@@ -0,0 +1,75 @@
+#!/usr/bin/env bash
+# test-health-url-resolution.sh — ops-hardening iter-41 (A1, TC-2): the backend health-check URL
+# surfaced to the browser-qa / QA LLM dispatch must resolve to this project's actual `/api/health`
+# path (Trendora namespaces every route under `/api` — `apps/backend/main.py` mounts
+# `health.router` with `prefix="/api"`), never the framework's generic bare `/health` default,
+# which 404s on a live, healthy backend and gets misread as "down" (iter-40's root cause #1).
+#
+# Two things proven:
+#   1. `lib/common.sh::resolve_backend_health_url` itself — no override -> `/api/health`; an
+#      explicit `CHAIN_BACKEND_HEALTH_URL` always wins (unchanged override contract).
+#   2. Regression guard: none of the five `*-phase.sh` callers this iteration fixed still carry
+#      the OLD inline `.../health}"` default — the exact drift that let `demo_runner.py`'s iter-39
+#      fix diverge from the shell scripts in the first place (each script duplicating its own
+#      inline default instead of sharing one helper).
+#
+# Offline, no model, <1s.
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+LIB="$REPO_ROOT/scripts/automation/lib/common.sh"
+
+PASS=0
+FAIL=0
+assert() {
+  local label="$1" result="$2"
+  if [[ "$result" == "pass" ]]; then
+    echo "  PASS  $label"; PASS=$((PASS+1))
+  else
+    echo "  FAIL  $label"; FAIL=$((FAIL+1))
+  fi
+}
+
+# ── 1. No override -> the project-specific `/api/health` default ─────────────────────────────
+rc=0
+out=$(bash -c '
+  set -euo pipefail
+  unset CHAIN_BACKEND_HEALTH_URL
+  source "'"$LIB"'"
+  resolve_backend_health_url 8123') || rc=$?
+[[ $rc -eq 0 && "$out" == "http://localhost:8123/api/health" ]] \
+  && assert "default resolves to /api/health (got '$out')" "pass" \
+  || assert "default resolves to /api/health (got '$out', rc=$rc)" "fail"
+
+# ── 2. An explicit CHAIN_BACKEND_HEALTH_URL override always wins ─────────────────────────────
+rc=0
+out=$(bash -c '
+  set -euo pipefail
+  export CHAIN_BACKEND_HEALTH_URL="http://example.test/custom-health"
+  source "'"$LIB"'"
+  resolve_backend_health_url 8123') || rc=$?
+[[ $rc -eq 0 && "$out" == "http://example.test/custom-health" ]] \
+  && assert "explicit CHAIN_BACKEND_HEALTH_URL overrides the default" "pass" \
+  || assert "explicit CHAIN_BACKEND_HEALTH_URL overrides the default (got '$out')" "fail"
+
+# ── 3. Regression guard: none of the five fixed callers still carry the OLD inline default ───
+OLD_PATTERN='CHAIN_BACKEND_HEALTH_URL:-http://localhost:\${?[A-Za-z_]*}?/health'
+for f in browser-qa-phase.sh goal-iter-lean.sh qa-phase.sh demo-phase.sh run-phase.sh; do
+  path="$REPO_ROOT/scripts/automation/$f"
+  if grep -Eq "$OLD_PATTERN" "$path" 2>/dev/null; then
+    assert "$f: no longer carries the old inline /health default" "fail"
+  else
+    assert "$f: no longer carries the old inline /health default" "pass"
+  fi
+  if grep -q 'resolve_backend_health_url' "$path" 2>/dev/null; then
+    assert "$f: calls the shared resolve_backend_health_url helper" "pass"
+  else
+    assert "$f: calls the shared resolve_backend_health_url helper" "fail"
+  fi
+done
+
+echo ""
+echo "=== Results: $PASS passed, $FAIL failed ==="
+[[ $FAIL -gt 0 ]] && exit 1
+exit 0
```
