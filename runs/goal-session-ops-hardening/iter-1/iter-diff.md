# Iteration diff (bounded)

Files changed: 16. Shown in full: 15.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (250 diff lines)

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 3969f55..3db3561 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -7,7 +7,9 @@ canonical create-once paths — it computes no score/return of its own):
                                      as-of dates, backfill gaps) + the recent fetch/backfill run history.
   - `POST /api/data/jobs`          → validate the date range + kind, START the async job, return
                                      `{job_id}` IMMEDIATELY. Malformed dates / unknown kind → 422 (typed
-                                     model); inverted or over-long range → 400; no price data → 503.
+                                     model); an inverted range → 400; no price data → 503. There is NO
+                                     range-span cap (ops-hardening iter-1, J-03) — chunked execution is
+                                     the safety mechanism for an unbounded span, never a rejection.
   - `GET  /api/data/jobs/{job_id}` → live status/progress for polling, ending in the final summary; an
                                      unknown id → 404 (never a fabricated job).
 
@@ -160,10 +162,11 @@ def data_availability(session: Session = Depends(get_session)) -> dict:
 @router.post("/data/jobs")
 def start_job(payload: JobCreate, session: Session = Depends(get_session)) -> dict:
     """Validate the request, START the async fetch/backfill job, and return its `job_id` immediately
-    (the job runs in a background thread). `503` when no price data exists; `400` for an inverted or
-    over-long range, an unknown import source, or a fetch against a needs-key source with no env/pasted
-    key (an explicit rejection — never a silent no-op). The response echoes the resolved `source` (not
-    secret) and NEVER the pasted key."""
+    (the job runs in a background thread). `503` when no price data exists; `400` for an inverted range,
+    an unknown import source, or a fetch against a needs-key source with no env/pasted key (an explicit
+    rejection — never a silent no-op). There is NO range-span cap (ops-hardening iter-1, J-03): a request
+    of any span is accepted; the job's date-window chunking is the safety mechanism. The response echoes
+    the resolved `source` (not secret) and NEVER the pasted key."""
     cfg = get_config()
     if latest_data_date(session) is None:
         raise HTTPException(status_code=503, detail="no price data available")
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index a917a93..12dda8e 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1943,7 +1943,9 @@ class ProviderCatalogEntry(BaseModel):
 class ImportChunkingCfg(BaseModel):
     """Chunked-import tunables (iter-22 CONSUMED, J-34). EVERY chunk/backoff/sleep number the resilient
     live-FETCH loop reads lives here (anti-goal: No magic numbers — NO chunk/backoff/sleep literal in
-    `app.engine.data_manager` or the providers; mirrors how `max_range_days` etc. live in config).
+    `app.engine.data_manager` or the providers; mirrors how `gap_preview`/`run_history_limit` etc. live
+    in config). `date_window_days` (below) is ALSO the ops-hardening iter-1 (J-03) safety mechanism for
+    an unbounded backfill/fetch span, now that no request-time range cap exists.
 
       - `symbol_batch_size` — symbols fetched per chunk (the symbol-batch dimension of the chunk plan).
       - `date_window_days`  — max calendar days per date-window chunk (the other plan dimension); the
@@ -2056,8 +2058,10 @@ class DataManagerCfg(BaseModel):
       - `default_source` — the catalog `id` used when a job omits `source` (preserves J-17 fetch
         behavior); MUST be a real catalog id (validated below), and is a no-key source in `config.yaml`
         so an omitted-source fetch never fails the key gate.
-      - `max_range_days` bounds a single job's inclusive calendar span; `gap_preview` /
-        `run_history_limit` are payload display caps.
+      - `gap_preview` / `run_history_limit` are payload display caps. ops-hardening iter-1 (J-03):
+        there is deliberately NO job date-range span cap — an explicit request of any span is accepted;
+        `import_chunking.date_window_days` (chunked execution) is the safety mechanism for an unbounded
+        span, not a request-time rejection.
 
     Validated like the other typed sections — every limit positive, catalog ids unique, and
     `default_source` ∈ the catalog — an invalid block raises `ConfigError`, never a silent default."""
@@ -2065,7 +2069,6 @@ class DataManagerCfg(BaseModel):
     model_config = ConfigDict(extra="allow")
     providers: list[ProviderCatalogEntry] = Field(min_length=1)
     default_source: str = Field(min_length=1)
-    max_range_days: int
     gap_preview: int
     run_history_limit: int
     import_chunking: ImportChunkingCfg  # J-34 chunked-import tunables (boot-validated above)
@@ -2082,7 +2085,6 @@ class DataManagerCfg(BaseModel):
     @model_validator(mode="after")
     def _validate(self) -> "DataManagerCfg":
         limits = {
-            "max_range_days": self.max_range_days,
             "gap_preview": self.gap_preview,
             "run_history_limit": self.run_history_limit,
         }
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index e5e1381..e187033 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1621,6 +1621,22 @@ class JobProgress:
     dates_done: int = 0
     snapshots_created: int = 0
     forward_returns_inserted: int = 0
+    # ops-hardening iter-1 (J-01/J-03) — the backfill/both/rebuild run-summary exclusion breakdown,
+    # computed ONCE by `_do_backfill` and carried on both the live progress (`to_dict()`) and the
+    # persisted run detail (`_run_detail()`): a single computation, two servings, never a second
+    # derivation. `dates_total` above is REDEFINED this iteration to mean "trading days in the
+    # REQUESTED range" (was: the post-cadence/already-snapshotted-filtered target count).
+    # `calendar_days` is the inclusive calendar span of [start, end]; `non_trading_days` is calendar
+    # days in range that are not trading days; `already_snapshotted` is trading days in range that
+    # already had a snapshot before this run started; `error_other` mirrors `len(date_failures)`. All
+    # 0 for a fetch/expand-only job (no backfill stage ran). Invariants (enforced by construction for
+    # backfill/both, whose cadence gate is bypassed — see `_do_backfill`):
+    # `non_trading_days + dates_total == calendar_days`;
+    # `snapshots_created + already_snapshotted + error_other == dates_total`.
+    calendar_days: int = 0
+    non_trading_days: int = 0
+    already_snapshotted: int = 0
+    error_other: int = 0
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
     # checkpoint's resume point); `chunk_total` = the deterministic plan size (symbol-batches × date-
     # windows). Both 0 for a non-chunked job (e.g. backfill-only) so the UI hides the chunk indicator.
@@ -1658,6 +1674,13 @@ class JobProgress:
     # completed, so a multi-date backfill ends `partial` with the per-date detail instead of aborting the
     # whole stage. Each entry is {date, error}. Empty for a clean run. Never a fabricated snapshot.
     date_failures: list[dict] = field(default_factory=list)
+    # ops-hardening iter-1 (J-01) — the UNCAPPED count of per-date backfill failures. `date_failures`
+    # above is a BOUNDED sample list (capped at `_MAX_ERROR_SAMPLES`), so `len()` of it undercounts once
+    # more than 20 dates fail. `error_other` is derived from THIS total (never from the sample `len()`),
+    # so the exclusion-breakdown invariant `snapshots_created + already_snapshotted + error_other ==
+    # dates_total` stays EXACT even on a large backfill with many failures — mirroring the existing
+    # `omitted` (bounded sample) / `omitted_total` (unconditional total) precedent. 0 for a clean run.
+    date_failures_total: int = 0
     started_at: datetime = field(default_factory=_utcnow)
     finished_at: Optional[datetime] = None
     # J-53 backfill-stage scratch (NOT serialized — internal accumulators the orchestrator fills during
@@ -1757,6 +1780,12 @@ class JobProgress:
             "dates_done": self.dates_done,
             "snapshots_created": self.snapshots_created,
             "forward_returns_inserted": self.forward_returns_inserted,
+            # ops-hardening iter-1: the live exclusion breakdown (0 for a fetch/expand-only job — see
+            # the JobProgress field docstring above).
+            "calendar_days": self.calendar_days,
+            "non_trading_days": self.non_trading_days,
+            "already_snapshotted": self.already_snapshotted,
+            "error_other": self.error_other,
             "chunk_index": self.chunk_index,  # J-34: completed chunks (== checkpoint resume point)
             "chunk_total": self.chunk_total,  # J-34: total planned chunks
             "passers": self.passers,  # J-35: candidates that passed the screen (became members)
@@ -1814,29 +1843,26 @@ def validate_job_request(
     api_key: Optional[str] = None,
 ) -> None:
     """Reject an invalid job request explicitly (the API maps the raised `ValueError` to a 4xx — never a
-    silent no-op): an unknown kind, an inverted range (start > end), a span over the configured
-    `data_manager.max_range_days`, an unknown import `source`, or a fetch against a `needs_key` source
-    with neither an env key nor a pasted session key. Malformed dates are rejected earlier by the typed
-    API model. `source`/`api_key` are validated only when a `source` is supplied; the key is read
-    request-only for the gate and is never persisted (anti-goal: keys are env-or-session, never
-    persisted)."""
+    silent no-op): an unknown kind, an inverted range (start > end), an unknown import `source`, or a
+    fetch against a `needs_key` source with neither an env key nor a pasted session key. Malformed dates
+    are rejected earlier by the typed API model. `source`/`api_key` are validated only when a `source` is
+    supplied; the key is read request-only for the gate and is never persisted (anti-goal: keys are
+    env-or-session, never persisted).
+
+    ops-hardening iter-1 (J-03): there is NO range-span cap here (or anywhere) — an explicit request of
+    any span is accepted; `_do_backfill`'s date-window chunking (`import_chunking.date_window_days`) is
+    the safety mechanism for an unbounded span, never a request-time rejection."""
     cfg = config or get_config()
     if kind not in JOB_KINDS:
         raise ValueError(f"unknown job kind {kind!r}; expected one of {list(JOB_KINDS)}")
     # J-85: a rebuild ignores the supplied date range entirely — it CLEARS then create-once recomputes the
     # snapshot set over EVERY covered trading day (the full calendar by design), reading the committed seed
-    # offline (no source/key, no span cap). So it bypasses the range-span + source/key gates below; only the
+    # offline (no source/key). So it bypasses the range-span + source/key gates below; only the
     # unknown-kind guard above applies. The endpoint still passes the latest data date as start==end.
     if kind in _REBUILD_KINDS:
         return
     if start > end:
         raise ValueError(f"start date {start.isoformat()} must be on or before end date {end.isoformat()}")
-    span_days = (end - start).days + 1
-    if span_days > cfg.data_manager.max_range_days:
-        raise ValueError(
-            f"date range too large: {span_days} days exceeds the configured maximum "
-            f"{cfg.data_manager.max_range_days}"
-        )
     # A job that FETCHES over the network = a generic fetch OR an expand (which fetches OHLCV + a cap).
     fetches = kind in _FETCH_KINDS or kind in _EXPAND_KINDS
     if source is not None:
@@ -2373,7 +2399,10 @@ def _compute_one_backfill_date(
 def _record_date_failure(prog: JobProgress, d: date_cls, error: str) -> None:
     """J-67 — record ONE per-date backfill failure (honest error + which date) so the stage ends `partial`
     with the per-date detail instead of aborting the whole stage. The other dates still complete; no
-    snapshot is fabricated for the failed date. Bounded like the per-symbol error list."""
+    snapshot is fabricated for the failed date. The sample list is bounded like the per-symbol error list;
+    ops-hardening iter-1: the UNCAPPED `date_failures_total` is ALWAYS bumped so `error_other` stays exact
+    past `_MAX_ERROR_SAMPLES` failures (the sample `len()` would undercount)."""
+    prog.date_failures_total += 1
     if len(prog.date_failures) < _MAX_ERROR_SAMPLES:
         prog.date_failures.append({"date": d.isoformat(), "error": error})
 
@@ -2382,8 +2411,12 @@ def _cadence_allowed_dates(
     session: Session, trading_days: list[date_cls], cfg: Config
 ) -> Optional[set]:
     """iter-18 — the BOUNDED deep-history snapshot cadence (`scanner.snapshot_cadence`): the set of
-    trading days the backfill/rebuild may target, or None for "no filter" (daily density everywhere —
-    the pre-iter-18 behavior, byte-identical, which is also the config default).
+    trading days a job may target, or None for "no filter" (daily density everywhere — the pre-iter-18
+    behavior, byte-identical, which is also the config default).
+
+    ops-hardening iter-1 (J-01): `_do_backfill` now calls this ONLY for a `rebuild` job — an explicit
+    `backfill`/`both` request's date range always wins over this cadence (see `_do_backfill`'s docstring).
+    This function's own logic is unchanged; only its caller's usage narrowed.
 
     Days ON/AFTER `daily_start` keep FULL daily density (the referee's recent-window power is
     preserved). Days BEFORE it keep only the FIRST trading day of each calendar month (`monthly`) or
@@ -2490,23 +2523,62 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
     run is cleaned up whole-row (`_cleanup_orphan_run`) — a failed date leaves NO inconsistent snapshot and
     the create-once re-run is clean. The stage ends `partial` (graded by the caller from
     `prog.date_failures`); no snapshot is fabricated for a failed date. The worker sessions are independent
-    read-only connections (never shared mid-transaction); only THIS thread writes."""
+    read-only connections (never shared mid-transaction); only THIS thread writes.
+
+    ops-hardening iter-1 (J-01/J-03) — an explicit `backfill`/`both` request's `[prog.start, prog.end]`
+    ALWAYS WINS over the deep-history snapshot cadence: every trading day in range is a candidate,
+    regardless of `_cadence_allowed_dates` (automatic warm-up cadence still governs only elsewhere). A
+    `rebuild` job (whose range the caller already widened to the full covered calendar) keeps the
+    EXISTING cadence-filtered target selection, unchanged — out of scope this iteration. The honest
+    run-summary breakdown (`calendar_days`/`non_trading_days`/`already_snapshotted`/`error_other`) is
+    computed from the SAME in-range set this function already derives — one computation, no second
+    derivation anywhere else. Execution is chunked into `import_chunking.date_window_days`-sized date
+    windows (reusing `_date_windows`, the same helper the fetch stage's chunk plan already uses),
+    advancing the existing `chunk_index`/`chunk_total` fields window-by-window — the safety mechanism for
+    an unbounded span now that `max_range_days` no longer rejects one (AG-8: memory stays bounded per
+    window; the shared bar cache is still loaded ONCE for the whole job, unaffected by this — its size is
+    a function of universe breadth, not date-range length)."""
     trading_days = _trading_days(session, cfg)
     snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
-    # iter-18: the bounded deep-history cadence — None means "no filter" (daily everywhere, the default).
-    allowed = _cadence_allowed_dates(session, trading_days, cfg)
+    in_range = [d for d in trading_days if prog.start <= d <= prog.end]
+
+    # J-01: `dates_total` is REDEFINED to mean "trading days in the REQUESTED range" — independent of
+    # cadence/already-snapshotted status (was: the post-filter target count). The calendar/non-trading
+    # split is exact by construction: every calendar day in [start, end] is either a trading day (counted
+    # in dates_total) or not (non_trading_days) — never approximated.
+    prog.calendar_days = (prog.end - prog.start).days + 1
+    prog.dates_total = len(in_range)
+    prog.non_trading_days = prog.calendar_days - prog.dates_total
+
+    # iter-18 cadence gate: still applies to `rebuild` (unchanged behavior, out of scope this iteration);
+    # bypassed entirely for an explicit `backfill`/`both` request (J-01 — "requested range always wins").
+    allowed = _cadence_allowed_dates(session, trading_days, cfg) if prog.kind in _REBUILD_KINDS else None
+    already = [d for d in in_range if d in snapshot_dates]
+    prog.already_snapshotted = len(already)
     targets = [
-        d for d in trading_days
-        if prog.start <= d <= prog.end
-        and d not in snapshot_dates
+        d for d in in_range
+        if d not in snapshot_dates
         and (allowed is None or d in allowed)
     ]
-    prog.dates_total = len(targets)
+    # `dates_done` starts PRE-SEEDED with the already-accounted-for count, so a zero-work run's progress
+    # reads N/N (fully accounted for, nothing new needed) rather than a misleading 0/N on a completed job;
+    # it advances only as NEW dates are actually persisted below — unchanged accounting for a fresh range
+    # (already_snapshotted == 0 there, so this is a no-op byte-identical to the pre-iter-1 starting point).
+    prog.dates_done = prog.already_snapshotted
     prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
     workers = cfg.data_manager.import_chunking.backfill_workers  # config pool size (No magic numbers)
     prog._backfill_concurrency = min(workers, len(targets)) if targets else workers
     prog._backfill_per_date_seconds_sum = 0.0
+
+    # J-03: the date-window chunk plan derives from the REQUESTED range (config `import_chunking.
+    # date_window_days`) — the SAME plan shape + progress fields the frontend's existing chunk-progress
+    # badge already renders for a chunked fetch, so a large backfill looks identical.
+    windows = _date_windows(prog.start, prog.end, cfg.data_manager.import_chunking.date_window_days)
+    prog.chunk_total = len(windows)
+    prog.chunk_index = 0
     if not targets:
+        prog.chunk_index = prog.chunk_total  # nothing to do — the (empty) plan is trivially complete
+        prog.error_other = prog.date_failures_total  # 0 — no per-date attempt was made
         return
 
     def _persist(d: date_cls, payload: Optional[dict], per_date_seconds: float) -> None:
@@ -2598,47 +2670,67 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
     # on exit, but glibc retains that freed address space by default — so a SECOND consecutive full-universe
     # rebuild in the same long-lived process stacks on run 1's inflated VSZ and hits the `ulimit -v` ceiling.
     # `_release_process_memory()` (gc.collect + malloc_trim) in the `finally` returns it to the OS on EVERY
-    # exit path (serial `return`, parallel fall-through, or an exception), so each rebuild starts lean.
+    # exit path (window loop done or an exception), so each rebuild starts lean. Loaded ONCE for the whole
+    # job (every window shares it) — its size is bounded by universe breadth, not by how many date-window
+    # chunks the requested range is split into (J-03 chunking is an execution/progress concept only).
     try:
         with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
-            if workers <= 1 or len(targets) <= 1:
-                # serial baseline (workers=1) — compute + persist inline, one date at a time, in order. A
-                # per-date compute failure is caught here (isolated), not raised — the rest still run.
-                for d in targets:
-                    compute_error: Optional[str] = None
-                    payload: Optional[dict] = None
-                    secs = 0.0
-                    try:
-                        _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
-                    except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure
-                        compute_error = str(exc)
-                    _persist_isolated(d, payload, secs, compute_error)
-                return
-            # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as they
-            # arrive. A worker compute exception is captured PER DATE (never raised out of the drain loop, so
-            # it never aborts the whole stage or deadlocks); the `with ThreadPoolExecutor` joins every worker
-            # before returning, so no thread outlives the job (the iter-28 determinism lesson).
-            pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
-            next_idx = 0
-            with ThreadPoolExecutor(max_workers=min(workers, len(targets))) as pool:
-                future_to_date = {
-                    pool.submit(_compute_one_backfill_date, eng, cfg, d, shared_cache): d for d in targets
-                }
-                for future in as_completed(future_to_date):
-                    d = future_to_date[future]
-                    try:
-                        _, payload, secs = future.result()
-                        pending[d] = (payload, secs, None)
-                    except Exception as exc:  # noqa: BLE001 — capture this date's compute failure, keep draining
-                        pending[d] = (None, 0.0, str(exc))
-                    # drain any now-contiguous prefix in target (date) order, so writes are strictly ordered.
-                    while next_idx < len(targets) and targets[next_idx] in pending:
-                        cur = targets[next_idx]
-                        cur_payload, cur_secs, cur_err = pending.pop(cur)
-                        _persist_isolated(cur, cur_payload, cur_secs, cur_err)
-                        next_idx += 1
+
+            def _run_targets(window_targets: list[date_cls]) -> None:
+                """Compute + persist exactly this window's target dates — serial (workers<=1 or a single
+                date) or fanned-out parallel, byte-identical to the pre-chunking body (only the INPUT
+                LIST now scopes to one date-window instead of the whole requested range)."""
+                if workers <= 1 or len(window_targets) <= 1:
+                    # serial baseline — compute + persist inline, one date at a time, in order. A per-date
+                    # compute failure is caught here (isolated), not raised — the rest still run.
+                    for d in window_targets:
+                        compute_error: Optional[str] = None
+                        payload: Optional[dict] = None
+                        secs = 0.0
+                        try:
+                            _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
+                        except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure
+                            compute_error = str(exc)
+                        _persist_isolated(d, payload, secs, compute_error)
+                    return
+                # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as
+                # they arrive. A worker compute exception is captured PER DATE (never raised out of the
+                # drain loop, so it never aborts the whole stage or deadlocks); the `with ThreadPoolExecutor`
+                # joins every worker before returning, so no thread outlives the job (iter-28 determinism).
+                pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
+                next_idx = 0
+                with ThreadPoolExecutor(max_workers=min(workers, len(window_targets))) as pool:
+                    future_to_date = {
+                        pool.submit(_compute_one_backfill_date, eng, cfg, d, shared_cache): d
+                        for d in window_targets
+                    }
+                    for future in as_completed(future_to_date):
+                        d = future_to_date[future]
+                        try:
+                            _, payload, secs = future.result()
+                            pending[d] = (payload, secs, None)
+                        except Exception as exc:  # noqa: BLE001 — capture this date's failure, keep draining
+                            pending[d] = (None, 0.0, str(exc))
+                        # drain any now-contiguous prefix in target (date) order — writes stay strictly
+                        # ordered within the window.
+                        while next_idx < len(window_targets) and window_targets[next_idx] in pending:
+                            cur = window_targets[next_idx]
+                            cur_payload, cur_secs, cur_err = pending.pop(cur)
+                            _persist_isolated(cur, cur_payload, cur_secs, cur_err)
+                            next_idx += 1
+
+            # J-03: walk the date-window plan IN ORDER, advancing chunk_index once each window's targets
+            # (possibly none — an all-non-trading or all-already-snapshotted window) are accounted for.
+            for ws, we in windows:
+                window_targets = [d for d in targets if ws <= d <= we]
+                if window_targets:
+                    _run_targets(window_targets)
+                prog.chunk_index += 1
     finally:
         _release_process_memory()
+    # UNCAPPED total (not `len(date_failures)`, a bounded sample) so `error_other` — and the invariant
+    # `snapshots_created + already_snapshotted + error_other == dates_total` — stays exact past 20 failures.
+    prog.error_other = prog.date_failures_total
 
 
 # --------------------------------------------------------------------------------------------------
@@ -2912,6 +3004,17 @@ def _provider_label(prog: JobProgress, cfg: Config) -> str:
 def _run_detail(prog: JobProgress) -> dict:
     """The structured detail JSON encoded into a `DataProviderRun.message` — descriptive job-control
     values, NEVER a key (anti-goal: keys are env-or-session, never persisted)."""
+    _is_backfill_like = prog.kind in _BACKFILL_KINDS or prog.kind in _REBUILD_KINDS
+    # ops-hardening iter-1: serve the breakdown ONLY once `_do_backfill` has actually computed it. Two
+    # rows are persisted BEFORE the backfill stage runs its computation and carry the JobProgress defaults
+    # (calendar_days == 0): the `running` row `_create_run_record` writes at job start, and the
+    # `interrupted` row the boot sweep freezes from it when a job's process dies mid-run. Since
+    # `calendar_days == (end - start).days + 1 >= 1` for EVERY real requested range, calendar_days == 0
+    # uniquely marks "breakdown not computed yet" → serve null there (the frontend `BackfillBreakdown`
+    # suppresses an all-null breakdown) rather than a fabricated "0 calendar days · 0 already snapshotted ·
+    # 0 non-trading" for an interrupted run whose range was really hundreds of days (AG-3: never surface a
+    # number that is not the engine's real computation; matches the fetch/seed-load null convention).
+    _breakdown_computed = _is_backfill_like and prog.calendar_days > 0
     return {
         "kind": prog.kind,
         "start": prog.start.isoformat(),
@@ -2921,6 +3024,15 @@ def _run_detail(prog: JobProgress) -> dict:
         "dates_total": prog.dates_total,
         "forward_returns_inserted": prog.forward_returns_inserted,
         "bars_fetched": prog.bars_fetched,
+        # ops-hardening iter-1 (J-01) — the run-summary exclusion breakdown on the permanent audit row:
+        # present for backfill/both/rebuild kinds only once actually computed (None for fetch/expand and
+        # for a not-yet-computed running/interrupted row — see `_breakdown_computed` above), mirroring the
+        # passers/omitted_total nullability. Read directly off `prog` — the SAME single computation
+        # `_do_backfill` already performed; never re-derived here.
+        "calendar_days": prog.calendar_days if _breakdown_computed else None,
+        "non_trading_days": prog.non_trading_days if _breakdown_computed else None,
+        "already_snapshotted": prog.already_snapshotted if _breakdown_computed else None,
+        "error_other": prog.error_other if _breakdown_computed else None,
         # J-35 expand: the screen outcome on the audit row (descriptive job-control values — NOT a recompute
         # of any canonical score/return/bucket). Present only for an expand kind.
         "passers": prog.passers if prog.kind in _EXPAND_KINDS else None,
@@ -3507,6 +3619,13 @@ def summarize_provider_run(run: DataProviderRun) -> dict:
         "snapshots_created": detail.get("snapshots_created"),
         "dates_done": detail.get("dates_done"),
         "dates_total": detail.get("dates_total"),
+        # ops-hardening iter-1 (J-01): the run-summary exclusion breakdown — None for a fetch/expand run
+        # or a plain non-JSON seed-load row (mirrors the passers/omitted_total nullability immediately
+        # below). Surfaced verbatim from the persisted detail JSON — no second computation path.
+        "calendar_days": detail.get("calendar_days"),
+        "non_trading_days": detail.get("non_trading_days"),
+        "already_snapshotted": detail.get("already_snapshotted"),
+        "error_other": detail.get("error_other"),
         "bars_fetched": detail.get("bars_fetched"),
         "passers": detail.get("passers"),  # J-35 expand screen outcome (None for non-expand runs)
         "omitted_total": detail.get("omitted_total"),  # J-35 expand screen outcome (None otherwise)
diff --git a/apps/backend/scripts/build_qa_fixture_db.py b/apps/backend/scripts/build_qa_fixture_db.py
index b110a5c..57bdf12 100644
--- a/apps/backend/scripts/build_qa_fixture_db.py
+++ b/apps/backend/scripts/build_qa_fixture_db.py
@@ -145,19 +145,15 @@ def build_fixture(
     if thin_bars <= 0 or thin_bars >= threshold:
         raise ValueError(f"--thin-bars must be in (0, {threshold}); got {thin_bars}")
 
-    # The benchmark window = the LAST `window` SPY trading days from the committed seed (a recent slice
-    # so a no-history pull's full-calendar span stays within data_manager.max_range_days).
+    # The benchmark window = the LAST `window` SPY trading days from the committed seed (a recent slice).
+    # ops-hardening iter-1 (J-03): no job date-range span cap exists anywhere in config any more (removed
+    # — was data_manager.max_range_days), so this fixture-builder no longer bounds the window's calendar
+    # span against it either; `--window` (a TRADING-day count) is its own reasonable sizing knob.
     spy = _read_seed_bars(BENCHMARK, seed_dir)
     if len(spy) < window:
         raise ValueError(f"committed SPY seed has only {len(spy)} bars; --window {window} too large")
     spy_window = spy[-window:]
     window_dates = [b["date"] for b in spy_window]
-    span_days = (window_dates[-1] - window_dates[0]).days + 1
-    if span_days > cfg.data_manager.max_range_days:
-        raise ValueError(
-            f"window spans {span_days} calendar days > data_manager.max_range_days "
-            f"{cfg.data_manager.max_range_days}; reduce --window"
-        )
     if gap_len <= 0 or gap_len >= window - 2:
         raise ValueError(f"--gap-len must be in (0, {window - 2}); got {gap_len}")
 
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 3edb683..d6f87ff 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -299,13 +299,24 @@ def test_post_job_inverted_range_is_400(data_api_engine):
     assert exc.value.status_code == 400
 
 
-def test_post_job_over_long_range_is_400(data_api_engine):
-    """A range exceeding config.data_manager.max_range_days is rejected with 400."""
-    with Session(data_api_engine) as session:
-        with pytest.raises(HTTPException) as exc:
-            # default max_range_days is 370; a ~3-year span exceeds it
-            start_job(JobCreate(kind="backfill", start=date(2020, 1, 1), end=date(2024, 1, 1)), session=session)
-    assert exc.value.status_code == 400
+def test_post_job_long_range_is_accepted_and_chunked(data_api_engine):
+    """ops-hardening iter-1 (J-03, TC-7/TC-8-equivalent unit coverage): a >370-calendar-day backfill
+    request is ACCEPTED (no 4xx "date range too large" rejection — that check no longer exists anywhere)
+    and its chunk plan derives from config `import_chunking.date_window_days` (`chunk_total > 1`,
+    `chunk_index` advancing to completion). This fixture's tiny seed has no trading day in the chosen
+    span, so the job completes near-instantly with zero real compute (`dates_total == 0`) — proving
+    ACCEPTANCE + chunk-plan arithmetic only; the true long-range, real-compute run is exercised live by
+    the J-03 browser-QA journey (goal.md TC-7/TC-8), never a unit test (a real multi-hundred-day backfill
+    is a documented hang risk on this codebase's multi-decade basis)."""
+    with Session(data_api_engine) as session:
+        # a ~3-year span (2020-01-01 -> 2024-01-01) -- comfortably past the old 370-day cap -- accepted.
+        resp = start_job(JobCreate(kind="backfill", start=date(2020, 1, 1), end=date(2024, 1, 1)), session=session)
+    assert resp["status"] == "running"
+    final = _await_job(resp["job_id"])
+    assert final is not None and final["status"] == "ok"
+    assert final["chunk_total"] > 1
+    assert final["chunk_index"] == final["chunk_total"]
+    assert final["dates_total"] == 0  # no trading day of this tiny fixture's calendar falls in range
 
 
 def test_job_payload_rejects_malformed_date_and_unknown_kind():
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index e55e38d..c26a969 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -20,7 +20,6 @@ MINIMAL_VALID = {
             {"id": "tiingo", "label": "Tiingo", "needs_key": True, "env_var": "TIINGO_API_KEY"},
         ],
         "default_source": "yahoo",
-        "max_range_days": 370,
         "gap_preview": 60,
         "run_history_limit": 50,
         # iter-22 (J-34) made `import_chunking` required (the chunk/backoff/sleep tunables come from
@@ -470,19 +469,23 @@ def test_methodology_threshold_requires_ref_xor_text(tmp_path):
 def test_data_manager_minimal_valid_loads(tmp_path):
     """MINIMAL_VALID (incl. the now-required data_manager section + the iter-21 import catalog) still
     loads, and the real config exposes the typed limits (the established pattern for every newly-required
-    section)."""
+    section). ops-hardening iter-1 (J-03): `max_range_days` no longer exists anywhere — there is no job
+    date-range span cap; `gap_preview`/`run_history_limit` remain the only display-cap limits."""
     cfg = load_config(_write(tmp_path, MINIMAL_VALID))
     assert cfg.data_manager.default_source == "yahoo"
     assert cfg.data_manager.provider_ids() == ["yahoo", "tiingo"]
-    assert cfg.data_manager.max_range_days == 370
+    assert not hasattr(cfg.data_manager, "max_range_days")
     real = load_config()
-    assert real.data_manager.max_range_days > 0 and real.data_manager.gap_preview > 0
+    assert not hasattr(real.data_manager, "max_range_days")
+    assert real.data_manager.gap_preview > 0 and real.data_manager.run_history_limit > 0
 
 
 def test_data_manager_nonpositive_limit_raises(tmp_path):
-    """A non-positive job limit fails the boot loudly — never a silent default (anti-goal: explicit)."""
+    """A non-positive job limit fails the boot loudly — never a silent default (anti-goal: explicit).
+    ops-hardening iter-1: `max_range_days` is gone, so this now pins `gap_preview` (the remaining
+    positive-limit contract) instead."""
     data = copy.deepcopy(MINIMAL_VALID)
-    data["data_manager"]["max_range_days"] = 0
+    data["data_manager"]["gap_preview"] = 0
     with pytest.raises(ConfigError):
         load_config(_write(tmp_path, data))
 
diff --git a/apps/backend/tests/test_config_engine.py b/apps/backend/tests/test_config_engine.py
index a37ed45..360471b 100644
--- a/apps/backend/tests/test_config_engine.py
+++ b/apps/backend/tests/test_config_engine.py
@@ -23,7 +23,6 @@ VALID = {
             {"id": "tiingo", "label": "Tiingo", "needs_key": True, "env_var": "TIINGO_API_KEY"},
         ],
         "default_source": "yahoo",
-        "max_range_days": 370,
         "gap_preview": 60,
         "run_history_limit": 50,
         "import_chunking": {  # iter-22 (J-34) required block
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index a175375..e111fbd 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -18,7 +18,7 @@ from __future__ import annotations
 
 import json
 import time
-from datetime import date, datetime
+from datetime import date, datetime, timedelta
 from pathlib import Path
 
 import httpx
@@ -488,21 +488,19 @@ def test_coverage_per_symbol_empty_dataset_is_members_only(persymbol_engine, tmp
 # ==================================================================================================
 # validate_job_request — config-driven limits + explicit rejection (the API maps these to 4xx)
 # ==================================================================================================
-def test_validate_job_request_reads_config_max_range():
-    """The max-range guard reads `config.data_manager.max_range_days` — shrinking it rejects a span that
-    was previously allowed (no magic range literal in control code)."""
+def test_validate_job_request_accepts_any_span():
+    """ops-hardening iter-1 (J-03): the max-range rejection is REMOVED ENTIRELY — an explicit request of
+    ANY span is accepted (no `ValueError`), including a span far exceeding the old 370-day cap. Chunked
+    execution (`_do_backfill`'s date-window loop), not a request-time cap, is the safety mechanism for an
+    unbounded span."""
     cfg = load_config()
-    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
-    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
-    # are create-once/isolation/parallelism, not the bounded-density policy).
-    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
-    cfg = cfg.model_copy(update={"scanner": _sc})
-    small = cfg.model_copy(
-        update={"data_manager": cfg.data_manager.model_copy(update={"max_range_days": 3})}
-    )
-    validate_job_request("backfill", date(2024, 1, 1), date(2024, 1, 3), small)  # exactly 3 days — ok
-    with pytest.raises(ValueError):
-        validate_job_request("backfill", date(2024, 1, 1), date(2024, 1, 10), small)  # 10 > 3
+    assert not hasattr(cfg.data_manager, "max_range_days")
+    # a 412-day span (2025-06-01 -> 2026-07-17, TC-7's own example) -- comfortably past the old 370-day
+    # cap -- raises nothing.
+    validate_job_request("backfill", date(2025, 6, 1), date(2026, 7, 17))
+    # an even larger, multi-year span is likewise accepted.
+    validate_job_request("backfill", date(2020, 1, 1), date(2024, 1, 1))
+    validate_job_request("fetch", date(2020, 1, 1), date(2024, 1, 1))
 
 
 def test_validate_job_request_rejects_inverted_and_unknown():
@@ -718,6 +716,10 @@ def backfilled_job(tmp_path_factory):
         "runs_pre2": runs_pre2, "runs_post2": runs_post2,
         "fr_pre2": fr_pre2, "fr_post2": fr_post2,
         "created_at_recheck": created_at_recheck,
+        # ops-hardening iter-1: the underlying (seed-loaded, cadence-neutralized) engine + cfg, so OTHER
+        # tests in this module can reuse the already-loaded seed DB (avoiding a second expensive load)
+        # for proofs that need a DIFFERENT cfg (e.g. real/active cadence) over the SAME committed data.
+        "engine": engine, "cfg": cfg,
     }
 
 
@@ -747,16 +749,44 @@ def test_backfill_is_lookahead_free_and_reuses_canonical(backfilled_job):
 
 def test_backfill_create_once_immutable(backfilled_job):
     """Re-running the SAME range is a no-op: 0 new snapshots, unchanged run/forward-return counts, and
-    every created_at is byte-identical (a snapshot is never overwritten — anti-goal: Snapshots immutable)."""
+    every created_at is byte-identical (a snapshot is never overwritten — anti-goal: Snapshots immutable).
+    ops-hardening iter-1: `dates_total` is REDEFINED to mean trading days in the requested range, so it is
+    UNCHANGED between the fresh run and the re-run (was: 0 on a re-run, the old post-filter semantics) —
+    the re-run's zero-work outcome is now explained by `already_snapshotted`, not by `dates_total` itself."""
     f = backfilled_job
     assert f["summary2"]["snapshots_created"] == 0
-    assert f["summary2"]["dates_total"] == 0  # nothing left to backfill in the range
+    assert f["summary2"]["dates_total"] == len(f["in_range"])  # same trading-day count as the fresh run
+    assert f["summary2"]["already_snapshotted"] == len(f["in_range"])  # every one pre-existing this time
+    assert f["summary2"]["error_other"] == 0
     assert f["runs_post2"] == f["runs_pre2"]  # no new runs created by the second job
     assert f["fr_post2"] == f["fr_pre2"]  # no new forward returns inserted by the second job
     for d, info in f["created"].items():
         assert f["created_at_recheck"][d] == info["created_at"]  # created_at never mutated
 
 
+def test_backfill_breakdown_invariants_hold_on_fresh_and_rerun(backfilled_job):
+    """ops-hardening iter-1 (J-01) — the run-summary exclusion-breakdown invariants hold EXACTLY on both
+    the fresh run (nothing pre-existing) and the identical re-run (everything pre-existing):
+    `non_trading_days + dates_total == calendar_days`;
+    `snapshots_created + already_snapshotted + error_other == dates_total`."""
+    f = backfilled_job
+    in_range = f["in_range"]
+    expected_calendar_days = (in_range[-1] - in_range[0]).days + 1
+    for summary in (f["summary1"], f["summary2"]):
+        assert summary["calendar_days"] == expected_calendar_days
+        assert summary["non_trading_days"] + summary["dates_total"] == summary["calendar_days"]
+        assert (
+            summary["snapshots_created"] + summary["already_snapshotted"] + summary["error_other"]
+            == summary["dates_total"]
+        )
+    # fresh run: nothing pre-existing, everything newly created.
+    assert f["summary1"]["already_snapshotted"] == 0
+    assert f["summary1"]["snapshots_created"] == len(in_range)
+    # re-run: nothing new, everything pre-existing (the create-once / zero-work contract).
+    assert f["summary2"]["snapshots_created"] == 0
+    assert f["summary2"]["already_snapshotted"] == len(in_range)
+
+
 def test_dataprovider_run_is_append_only_per_job(backfilled_job):
     """Each job appends exactly one DataProviderRun row (append-only); none are overwritten."""
     f = backfilled_job
@@ -766,6 +796,210 @@ def test_dataprovider_run_is_append_only_per_job(backfilled_job):
     assert callable(runs)
 
 
+# ==================================================================================================
+# ops-hardening iter-1 (J-01/J-03): cadence bypass for backfill/both (not rebuild), the run-summary
+# exclusion breakdown, and date-window chunking — reuses `backfilled_job`'s already-loaded seed engine
+# (a SECOND full seed load would be wasteful; the ACTIVE, non-neutralized cadence config is built fresh
+# here since the fixture's own `cfg` deliberately neutralizes it for its own unrelated proofs).
+# ==================================================================================================
+def _cadence_excluded_window(trading, allowed, daily_start, n, start_at=0):
+    """The first `n` consecutive trading days (searching from index `start_at`), entirely inside the
+    deep (pre-`daily_start`) region, that `_cadence_allowed_dates` excludes IN FULL — so a bypass-vs-
+    filtered contrast on this window is unambiguous (never a vacuous window cadence would have allowed
+    anyway). Real seed dates only; raises if no such window exists (a hard test-setup failure, not a
+    fabricated window)."""
+    for i in range(start_at, len(trading) - n):
+        window = trading[i:i + n]
+        if window[-1] >= daily_start:
+            break  # only the deep region is searched
+        if all(d not in allowed for d in window):
+            return window
+    raise AssertionError(f"no {n}-day fully cadence-excluded window found from index {start_at}")
+
+
+def test_do_backfill_cadence_bypass_for_backfill_not_rebuild(backfilled_job):
+    """J-01 — an explicit `backfill`/`both` request's date range ALWAYS WINS over the deep-history
+    snapshot cadence: every trading day in a cadence-excluded window still becomes a real, snapshotted
+    target. `rebuild` keeps the EXISTING cadence-filtered target selection UNCHANGED (out of scope this
+    iteration) — proven by calling `_do_backfill` directly with `kind="rebuild"` over a SEPARATE
+    cadence-excluded window (never through `run_data_job`, which would widen a real rebuild to the FULL
+    historical calendar — far too expensive for a test; the documented hang risk on this codebase's
+    multi-decade basis)."""
+    engine = backfilled_job["engine"]
+    cfg = load_config()  # the REAL, ACTIVE cadence (daily_start set, deep_cadence != "daily") — not the
+    # fixture's own neutralized copy, so the bypass-vs-filtered contrast below is real, not vacuous.
+    daily_start = cfg.scanner.snapshot_cadence.daily_start
+    assert daily_start is not None, "this proof needs an ACTIVE cadence gate to bypass/enforce"
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        allowed = data_manager._cadence_allowed_dates(session, trading, cfg)
+
+    # window A: a real BACKFILL job bypasses the cadence entirely.
+    window_a = _cadence_excluded_window(trading, allowed, daily_start, 3)
+    with Session(engine) as session:
+        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
+    job = create_job("backfill", window_a[0], window_a[-1])
+    summary = run_data_job(job.job_id, config=cfg, engine=engine)
+    assert summary["dates_total"] == 3  # J-01 redefinition: trading days in range, cadence notwithstanding
+    assert summary["snapshots_created"] == 3  # every one backfilled — the cadence gate did NOT filter them
+    assert summary["already_snapshotted"] == 0
+    with Session(engine) as session:
+        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
+        for d in window_a:
+            assert scanner.get_run_for_date(session, d) is not None
+    assert runs_after == runs_before + 3
+
+    # window B: a DIFFERENT (disjoint) cadence-excluded window, searched onward from window A's END so
+    # the two never overlap — no cleanup of window A's fresh snapshots is needed.
+    start_at = trading.index(window_a[-1]) + 1
+    window_b = _cadence_excluded_window(trading, allowed, daily_start, 3, start_at=start_at)
+    prog = JobProgress(job_id="ops-hardening-rebuild-cadence-probe", kind="rebuild",
+                        start=window_b[0], end=window_b[-1])
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog, eng=engine)
+    assert prog.dates_total == 3  # the redefinition still reports the honest trading-day-in-range count
+    assert prog.snapshots_created == 0  # cadence excluded every date in this window — UNCHANGED behavior
+    assert prog.already_snapshotted == 0
+    with Session(engine) as session:
+        for d in window_b:
+            assert scanner.get_run_for_date(session, d) is None  # rebuild's cadence filter still applies
+
+
+def test_backfill_weekend_span_mixed_and_all_non_trading_breakdown(backfilled_job):
+    """ops-hardening iter-1 (J-01, TC-11-equivalent unit coverage) — a range covering exactly two
+    consecutive REAL trading days that straddle a calendar gap (a weekend) proves the MIXED
+    trading/non-trading breakdown; the gap's OWN calendar days (strictly between them — zero trading
+    days by construction) prove the ALL-non-trading breakdown, honestly (no fabricated per-date failure,
+    `error_other == 0`) — mirroring the real J-01 weekend-only journey (TC-3) at unit-test speed."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]  # cadence-neutralized is fine here — this proof is cadence-agnostic
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+    gap_pair = next(((a, b) for a, b in zip(trading, trading[1:]) if (b - a).days > 1), None)
+    assert gap_pair is not None, "expected at least one real calendar gap in the seed trading calendar"
+    a, b = gap_pair
+    gap_days = (b - a).days - 1  # calendar days strictly between two consecutive trading days
+
+    # mixed: the two trading days themselves plus every non-trading day between them.
+    job = create_job("backfill", a, b)
+    summary = run_data_job(job.job_id, config=cfg, engine=engine)
+    assert summary["dates_total"] == 2
+    assert summary["calendar_days"] == (b - a).days + 1
+    assert summary["non_trading_days"] == gap_days
+    assert summary["non_trading_days"] + summary["dates_total"] == summary["calendar_days"]
+    assert summary["snapshots_created"] + summary["already_snapshotted"] + summary["error_other"] == 2
+    assert summary["error_other"] == 0
+
+    # all-non-trading: the gap's own span (strictly between a and b) — zero trading days by construction.
+    gap_start, gap_end = a + timedelta(days=1), b - timedelta(days=1)
+    job2 = create_job("backfill", gap_start, gap_end)
+    summary2 = run_data_job(job2.job_id, config=cfg, engine=engine)
+    assert summary2["dates_total"] == 0
+    assert summary2["calendar_days"] == gap_days
+    assert summary2["non_trading_days"] == gap_days
+    assert summary2["snapshots_created"] == 0
+    assert summary2["already_snapshotted"] == 0
+    assert summary2["error_other"] == 0
+    assert summary2["status"] == "ok"  # honest zero-work — never a fabricated failure
+
+
+def test_backfill_chunk_plan_derives_from_date_window_days_config(backfilled_job):
+    """J-03 — the backfill date-window chunk plan (`chunk_total`) derives from config
+    `import_chunking.date_window_days`, exactly like the existing fetch-side chunk plan: varying the
+    config value changes `chunk_total` for the SAME range. Uses the LARGEST all-non-trading gap in the
+    seed's own calendar (zero real compute — no scanner work is needed to prove the ARITHMETIC) so this
+    stays fast, never executing a real multi-hundred-day backfill to completion. Takes whatever gap size
+    the real seed calendar actually has (a plain weekend is >= 2 calendar days) rather than assuming a
+    specific holiday-cluster size exists."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+    a, b = max(zip(trading, trading[1:]), key=lambda pair: (pair[1] - pair[0]).days)
+    gap_start, gap_end = a + timedelta(days=1), b - timedelta(days=1)
+    calendar_days = (gap_end - gap_start).days + 1
+    assert calendar_days >= 2, "expected at least an ordinary weekend gap in the seed trading calendar"
+
+    # window_days == calendar_days -> exactly 1 chunk; window_days == 1 -> one chunk per calendar day
+    # (always calendar_days chunks, regardless of how large the found gap happens to be).
+    for window_days, expected_chunks in ((calendar_days, 1), (1, calendar_days)):
+        ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": window_days})
+        dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
+        narrow_cfg = cfg.model_copy(update={"data_manager": dm})
+        prog = JobProgress(job_id=f"chunk-plan-probe-{window_days}", kind="backfill",
+                            start=gap_start, end=gap_end)
+        with Session(engine) as session:
+            data_manager._do_backfill(session, narrow_cfg, prog, eng=engine)
+        assert prog.chunk_total == len(data_manager._date_windows(gap_start, gap_end, window_days))
+        assert prog.chunk_total == expected_chunks
+        assert prog.chunk_index == prog.chunk_total  # the (empty, all-non-trading) plan completed in full
+        assert prog.dates_total == 0  # still honestly zero trading days — no fabricated target
+
+
+def test_run_detail_omits_breakdown_until_computed():
+    """ops-hardening iter-1 audit (Finding B) — the persisted run-summary breakdown is served ONLY once
+    `_do_backfill` has computed it. The `running` row `_create_run_record` writes at job start (and the
+    `interrupted` row the boot sweep freezes from it) carries the JobProgress defaults (calendar_days ==
+    0); `_run_detail` must serve those four fields as null there — NOT a fabricated "0 calendar days · 0
+    already snapshotted · 0 non-trading" for a backfill whose range was really hundreds of days (AG-3).
+    A genuinely-computed backfill still serves the real values (calendar_days >= 1)."""
+    # not-yet-computed backfill row (exactly what `_create_run_record` serializes at job start): a real
+    # multi-hundred-day requested range, but the breakdown fields still at their JobProgress defaults.
+    fresh = JobProgress(job_id="never-ran", kind="backfill", start=date(2024, 1, 1), end=date(2025, 6, 1))
+    detail = data_manager._run_detail(fresh)
+    assert detail["calendar_days"] is None  # never a fabricated 0 for a 517-day range
+    assert detail["non_trading_days"] is None
+    assert detail["already_snapshotted"] is None
+    assert detail["error_other"] is None
+    # a genuinely-computed backfill (the finalized row) still serves the real numbers unchanged.
+    done = JobProgress(job_id="ran", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29))
+    done.calendar_days, done.dates_total, done.non_trading_days = 28, 19, 9
+    done.already_snapshotted, done.snapshots_created, done.error_other = 0, 19, 0
+    detail_done = data_manager._run_detail(done)
+    assert detail_done["calendar_days"] == 28
+    assert detail_done["non_trading_days"] == 9
+    assert detail_done["already_snapshotted"] == 0
+    assert detail_done["error_other"] == 0
+
+
+def test_backfill_error_other_uncapped_past_sample_limit(backfilled_job, monkeypatch):
+    """ops-hardening iter-1 audit (Finding A) — `error_other`, and the breakdown invariant it feeds, stay
+    EXACT when more than `_MAX_ERROR_SAMPLES` (20) in-range dates fail: it is derived from the UNCAPPED
+    `date_failures_total`, never from the bounded `date_failures` sample list. Forces every target in a
+    25-trading-day deep (un-snapshotted) window to fail its compute — the failures are recorded but never
+    persisted, so this stays fast (no real scanner/DB work), then asserts the sample list capped at 20
+    while `error_other` reports the true 25 and invariant 2 holds exactly."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]  # cadence-neutralized: every in-range trading day is a target
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    # the first run of 25 CONSECUTIVE un-snapshotted trading days (so every one becomes a real target and
+    # the [start,end] span contains exactly them) — robust to whichever ranges the fixture pre-snapshotted.
+    window = next(
+        (trading[i:i + 25] for i in range(len(trading) - 25)
+         if not any(d in snapshotted for d in trading[i:i + 25])),
+        None,
+    )
+    assert window is not None and len(window) == 25, "expected a 25-day un-snapshotted trading window"
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced compute failure")
+    monkeypatch.setattr(data_manager, "_compute_one_backfill_date", _boom)
+
+    prog = JobProgress(job_id="err-uncapped-probe", kind="backfill", start=window[0], end=window[-1])
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog, eng=engine)
+
+    n_targets = prog.dates_total - prog.already_snapshotted
+    assert n_targets == 25 and prog.snapshots_created == 0  # every target failed, none persisted
+    assert len(prog.date_failures) == data_manager._MAX_ERROR_SAMPLES  # the SAMPLE list is capped at 20
+    assert prog.error_other == 25  # ...but error_other is the UNCAPPED true failure count
+    assert prog.error_other > data_manager._MAX_ERROR_SAMPLES
+    # invariant 2 holds EXACTLY even past the sample cap (the whole point of the fix)
+    assert prog.snapshots_created + prog.already_snapshotted + prog.error_other == prog.dates_total
+
+
 # ==================================================================================================
 # iter-21 (J-33): import-source catalog availability (env-detected) — descriptive metadata, NO key
 # ==================================================================================================
diff --git a/apps/backend/tests/test_data_manager_backfill_committed_session.py b/apps/backend/tests/test_data_manager_backfill_committed_session.py
index 429c5ac..df64300 100644
--- a/apps/backend/tests/test_data_manager_backfill_committed_session.py
+++ b/apps/backend/tests/test_data_manager_backfill_committed_session.py
@@ -236,8 +236,13 @@ def test_rerun_after_isolated_failure_is_create_once(tmp_path, monkeypatch):
     s2 = run_data_job(job2.job_id, config=_with_backfill_workers(cfg, 4), engine=engine)
 
     assert s2["status"] == "ok", s2
-    assert s2["dates_total"] == 1  # only the previously-failed date remains to backfill
-    assert s2["snapshots_created"] == 1
+    # ops-hardening iter-1: `dates_total` is REDEFINED to mean trading days in the requested range, so it
+    # is UNCHANGED from the first run (was: 1, the old post-filter "only what's left" semantics); the
+    # re-run's near-zero-work outcome is now explained by `already_snapshotted` instead.
+    assert s2["dates_total"] == len(in_range)
+    assert s2["already_snapshotted"] == len(in_range) - 1  # the 5 dates run 1 already completed
+    assert s2["snapshots_created"] == 1  # only the previously-failed date remains to backfill
+    assert s2["error_other"] == 0
     assert s2["date_failures"] == []
     with Session(engine) as session:
         runs_after_second = session.scalar(select(func.count()).select_from(ScannerRun))
diff --git a/apps/backend/tests/test_data_manager_backfill_parallel.py b/apps/backend/tests/test_data_manager_backfill_parallel.py
index ff5ac87..02633e4 100644
--- a/apps/backend/tests/test_data_manager_backfill_parallel.py
+++ b/apps/backend/tests/test_data_manager_backfill_parallel.py
@@ -209,9 +209,12 @@ def test_backfill_per_date_sum_at_least_wall_clock_floor(equality_run):
 # create-once / idempotent — a re-run of a covered range changes nothing (no UNIQUE crash)
 # ==================================================================================================
 def test_parallel_rerun_is_idempotent(equality_run):
-    """Re-running the SAME range on the already-backfilled parallel DB creates NOTHING (dates_total == 0,
-    no new ScannerRun / ForwardReturn rows, no UNIQUE crash) and never overwrites a snapshot (created_at
-    unchanged) — the J-41 create-once guard holds under the parallel build."""
+    """Re-running the SAME range on the already-backfilled parallel DB creates NOTHING NEW (all snapshots
+    already present, so `snapshots_created == 0` and `already_snapshotted == len(in_range)`), no new
+    ScannerRun / ForwardReturn rows, no UNIQUE crash, and never overwrites a snapshot (created_at
+    unchanged) — the J-41 create-once guard holds under the parallel build. ops-hardening iter-1:
+    `dates_total` is REDEFINED to mean trading days in the requested range, so it stays `len(in_range)`
+    on this re-run too (was: 0, the old post-filter semantics)."""
     f = equality_run
     engine, cfg = f["par_engine"], f["cfg"]
     r_start, r_end = f["in_range"][0], f["in_range"][-1]
@@ -224,8 +227,10 @@ def test_parallel_rerun_is_idempotent(equality_run):
     summary = run_data_job(job.job_id, config=_with_backfill_workers(cfg, 4), engine=engine)
 
     assert summary["status"] == "ok"
-    assert summary["dates_total"] == 0  # nothing left to backfill — all snapshots already present
+    assert summary["dates_total"] == len(f["in_range"])
+    assert summary["already_snapshotted"] == len(f["in_range"])
     assert summary["snapshots_created"] == 0
+    assert summary["error_other"] == 0
     with Session(engine) as session:
         assert session.scalar(select(func.count()).select_from(ScannerRun)) == runs_before
         assert session.scalar(select(func.count()).select_from(ForwardReturn)) == fr_before
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index 5f15ab8..1162db9 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -32,7 +32,7 @@ _CFG = {
     "database": {"url": "sqlite:///:memory:"},
     "data_manager": {
         "providers": [{"id": "yahoo", "label": "Yahoo", "needs_key": False}],
-        "default_source": "yahoo", "max_range_days": 370, "gap_preview": 60, "run_history_limit": 50,
+        "default_source": "yahoo", "gap_preview": 60, "run_history_limit": 50,
         "import_chunking": {
             "symbol_batch_size": 25, "date_window_days": 90, "max_retries": 4,
             "backoff_base_seconds": 1.0, "backoff_cap_seconds": 30.0, "inter_request_sleep_seconds": 0.0,
diff --git a/apps/backend/tests/test_sectors.py b/apps/backend/tests/test_sectors.py
index 94e13da..115a444 100644
--- a/apps/backend/tests/test_sectors.py
+++ b/apps/backend/tests/test_sectors.py
@@ -71,7 +71,7 @@ _SYNTH_CFG = {
     "database": {"url": "sqlite:///:memory:"},
     "data_manager": {
         "providers": [{"id": "yahoo", "label": "Yahoo", "needs_key": False}],
-        "default_source": "yahoo", "max_range_days": 370, "gap_preview": 60, "run_history_limit": 50,
+        "default_source": "yahoo", "gap_preview": 60, "run_history_limit": 50,
         "import_chunking": {  # iter-22 (J-34) required block
             "symbol_batch_size": 25, "date_window_days": 90, "max_retries": 4,
             "backoff_base_seconds": 1.0, "backoff_cap_seconds": 30.0, "inter_request_sleep_seconds": 0.0,
diff --git a/apps/backend/tests/test_themes.py b/apps/backend/tests/test_themes.py
index 3af85fe..213bf9c 100644
--- a/apps/backend/tests/test_themes.py
+++ b/apps/backend/tests/test_themes.py
@@ -77,7 +77,7 @@ _SYNTH_CFG = {
     "database": {"url": "sqlite:///:memory:"},
     "data_manager": {
         "providers": [{"id": "yahoo", "label": "Yahoo", "needs_key": False}],
-        "default_source": "yahoo", "max_range_days": 370, "gap_preview": 60, "run_history_limit": 50,
+        "default_source": "yahoo", "gap_preview": 60, "run_history_limit": 50,
         "import_chunking": {  # iter-22 (J-34) required block
             "symbol_batch_size": 25, "date_window_days": 90, "max_retries": 4,
             "backoff_base_seconds": 1.0, "backoff_cap_seconds": 30.0, "inter_request_sleep_seconds": 0.0,
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 2335b26..78ee308 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -2358,6 +2358,14 @@ export interface DataRun {
   snapshots_created: number | null;
   dates_done: number | null;
   dates_total: number | null;
+  // ops-hardening iter-1 (J-01) — the backfill/both/rebuild run-summary exclusion breakdown; null for a
+  // fetch/expand run (matching the existing dates_total nullability pattern). Invariants (enforced
+  // server-side, never re-derived here): non_trading_days + dates_total == calendar_days;
+  // snapshots_created + already_snapshotted + error_other == dates_total.
+  calendar_days: number | null;
+  non_trading_days: number | null;
+  already_snapshotted: number | null;
+  error_other: number | null;
   bars_fetched: number | null;
   passers: number | null; // J-35 expand screen outcome (null for non-expand runs)
   omitted_total: number | null; // J-35 expand screen outcome (null otherwise)
@@ -2567,6 +2575,12 @@ export interface DataJob {
   dates_done: number;
   snapshots_created: number;
   forward_returns_inserted: number;
+  // ops-hardening iter-1 (J-01/J-03): the live exclusion breakdown — 0 for a fetch/expand-only job (no
+  // backfill stage ran). Mirrors the persisted `DataRun` fields (see api layer / data_manager.py).
+  calendar_days?: number;
+  non_trading_days?: number;
+  already_snapshotted?: number;
+  error_other?: number;
   chunk_index?: number; // J-34: completed chunks (== checkpoint resume point)
   chunk_total?: number; // J-34: total planned chunks (chunk x/N); 0/absent for a non-chunked job
   passers?: number; // J-35 expand: candidates that passed the screen (became universe members)
diff --git a/config.yaml b/config.yaml
index 55742a1..cc581f1 100644
--- a/config.yaml
+++ b/config.yaml
@@ -54,7 +54,9 @@ data_manager:
       supports_market_cap: false
   default_source: yahoo     # the import source used when a job omits `source` (no-key ⇒ J-17 fetch never
                             # fails the key gate). MUST be a real catalog id (validated at boot).
-  max_range_days: 370       # max span (inclusive calendar days) a single fetch/backfill job may cover
+  # ops-hardening iter-1 (J-03): no job date-range span cap (removed — was max_range_days: 370). An
+  # explicit request of any span is accepted; import_chunking.date_window_days below (chunked execution)
+  # is the safety mechanism for an unbounded span.
   gap_preview: 60           # how many backfill-gap dates the coverage payload previews (display cap)
   run_history_limit: 50     # how many recent fetch/backfill runs GET /api/data returns (display cap)
   # J-34 chunked-import tunables: every chunk/backoff/sleep number the resilient FETCH loop reads lives
```
