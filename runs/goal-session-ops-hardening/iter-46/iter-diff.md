# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 59fcddee..fd26ebb1 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1312,10 +1312,14 @@ def refresh_coverage_snapshot_for(session: Session, cfg: Config, resolved_asof:
 def refresh_coverage_snapshot(session: Session, cfg: Config) -> Optional[dict]:
     """Compute the CURRENT coverage payload (reusing the canonical `_compute_coverage_uncached` verbatim —
     never a second derivation) and persist it as the `CoverageSnapshot` row for the CURRENT `(asof_key,
-    dataset_version)` key, upserting idempotently. Called by the ingest finalize hook (unconditionally, on
-    every successful backfill/both/rebuild — including a zero-work re-run — AND, ops-hardening iter-3 B1,
-    on a successful fetch/expand that the cheap `_coverage_snapshot_is_current` gate below found stale) and
-    the boot warm-up safety net (only when no row exists yet for the current stamp). Returns the freshly
+    dataset_version)` key, upserting idempotently. Called by the ingest finalize hook — on every successful
+    fetch/expand (ops-hardening iter-3 B1) and every successful backfill/both/rebuild (ops-hardening iter-46
+    fix pass + audit B1) that the cheap `_coverage_snapshot_is_current` gate below finds STALE, or that
+    created at least one new snapshot date; the ONLY case that now skips it is a genuinely zero-work re-run
+    (no new snapshot date AND a stamp the gate already finds current, so a recompute would only reproduce
+    the persisted row byte-for-byte) — and by the boot warm-up safety net (only when no row exists yet for
+    the current stamp). NOTE for future edits: this is the ingest tail's ONE uncached heavy call, so the
+    gate is a load-bearing contract, not an optimization detail. Returns the freshly
     persisted payload, or `None` on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns
     None only then; nothing to snapshot yet). The current stamp resolves `None`→latest, so this is
     `refresh_coverage_snapshot_for` at that resolved date (byte-identical: `_compute_coverage_uncached
@@ -3764,13 +3768,56 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     try:
         with cache_ctx:
             try:
-                payload = refresh_coverage_snapshot(session, cfg)
-                if payload is not None:
-                    refreshed.append("coverage")
-                    # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
-                    # `membership_timeline_cached` internally as part of computing the payload just persisted
-                    # above — warmed for free by that SAME call, never a second/separate derivation.
-                    refreshed.append("membership_timeline")
+                # ops-hardening iter-46 FIX PASS (QA blockers 1 + 4 — J-01/J-03): gate this refresh on the
+                # SAME cheap `_coverage_snapshot_is_current` check the fetch/expand branch has used since
+                # iter-3 (audit B1) — see that call site's own comment ("so a zero-work fetch (the common
+                # offline case) pays no extra compute/write"). Until now the backfill/both/rebuild branch
+                # called `refresh_coverage_snapshot` UNCONDITIONALLY, so a backfill that resolved to ZERO
+                # trading days still paid a full `_compute_coverage_uncached` derivation (its own
+                # `prefilled_bar_cache` whole-bar load). Every OTHER heavy step in this tail is already
+                # `dataset_version`-cached — forward-aggregates, research hot keys, index series, drawdown
+                # expectations are all cheap HITS on a zero-work job — so this was the ONE uncached heavy
+                # call left, and it is why QA run 287 (`dates_total: 0`, two weekend dates) never left
+                # `status: "running"` for 15+ minutes on an otherwise idle, freshly-restarted backend.
+                #
+                # The gate is a REDUNDANCY check, never a freshness compromise: it is true only when a
+                # `CoverageSnapshot` row already exists for THIS exact `(asof_key, dataset_version)` stamp,
+                # i.e. the persisted payload already reflects this dataset version and a recompute would
+                # reproduce it byte-for-byte. Any job that actually landed a bar or a snapshot moves
+                # `_membership_dataset_version`, so no row exists for the new stamp and the canonical
+                # refresh below still runs exactly as before (TC-A2) — J-05's `aggregates_refreshed` keeps
+                # its `membership_timeline` entry on every genuinely-working ingest.
+                #
+                # ops-hardening iter-46 AUDIT (B1): the gate ALSO requires that this job created NO new
+                # snapshot date. "Any job that actually landed a snapshot moves the stamp" does NOT hold
+                # for the J-85 clear-and-recreate REBUILD: `scanner_runs.id` is a plain
+                # `INTEGER PRIMARY KEY` (no `AUTOINCREMENT`, no `sqlite_sequence` row — verified on the
+                # live DB), so clearing every run and recomputing the SAME date set restores the SAME
+                # `max(id)` and `count(*)`; with the bars untouched, `_membership_dataset_version` is
+                # byte-identical BEFORE and AFTER the rebuild. Without this clause a full rebuild — whose
+                # documented purpose is to pick up a UNIVERSE EXPANSION, i.e. exactly a change the narrow
+                # membership stamp does not encode (`universe_count` / `candidate_universe_count` /
+                # `per_symbol` / the diagnostics all read `cfg.universe`) — would skip its coverage refresh
+                # and leave `/api/data` serving the PRE-rebuild payload while `coverage_status` still
+                # reports it fresh (AG-3), and would drop `coverage`/`membership_timeline` from that job's
+                # `aggregates_refreshed` (the field J-05 asserts on). A snapshot-creating job is never the
+                # zero-work case this gate exists for, so requiring `new_snapshot_dates == []` costs the
+                # fix nothing: QA run 287 (`dates_total: 0`) and the already-snapshotted 412-day range both
+                # still skip.
+                if not prog.new_snapshot_dates and _coverage_snapshot_is_current(session, cfg):
+                    # Honesty gate (the module's standing "actually did something" convention): nothing was
+                    # recomputed, so NEITHER category may be claimed — an honest omission, never a
+                    # fabricated refresh.
+                    pass
+                else:
+                    payload = refresh_coverage_snapshot(session, cfg)
+                    if payload is not None:
+                        refreshed.append("coverage")
+                        # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
+                        # `membership_timeline_cached` internally as part of computing the payload just
+                        # persisted above — warmed for free by that SAME call, never a second/separate
+                        # derivation.
+                        refreshed.append("membership_timeline")
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
                 _log_isolation_failure("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
 
@@ -5055,7 +5102,12 @@ def _fail_unlaunched_job(prog: JobProgress, cfg: Config, eng: Engine, exc: BaseE
     try:
         _finalize_run_record(eng, cfg, prog)
     except Exception:  # noqa: BLE001 — persistence failure must not crash the launch-failure path further
-        logger.exception("failed to persist run summary for unlaunched job %s", prog.job_id)
+        # ops-hardening iter-46 (last of the module's bare `logger.exception` sites, alongside :5091):
+        # `_log_isolation_failure`, NOT a bare `logger.exception` — SAME reason as every other isolation
+        # handler in this module (iter-44/45): rendering the live traceback itself allocates, and under the
+        # SAME exhausted `ulimit -v` cap that produced the exception being handled, that allocation can
+        # raise a second exception past this `except` clause's own protection.
+        _log_isolation_failure("failed to persist run summary for unlaunched job %s", prog.job_id)
 
 
 def _fail_unlaunched_resume(import_id: str, cfg: Config, eng: Engine, exc: BaseException) -> None:
@@ -5088,7 +5140,9 @@ def _fail_unlaunched_resume(import_id: str, cfg: Config, eng: Engine, exc: BaseE
                 return
             prog = _progress_from_checkpoint(cfg, cp)
     except Exception:  # noqa: BLE001 — never let this bookkeeping path itself crash the launch-failure path
-        logger.exception("failed to rebuild job progress for unlaunched resume %s", import_id)
+        # ops-hardening iter-46 (last of the module's bare `logger.exception` sites, alongside :5058):
+        # `_log_isolation_failure`, NOT a bare `logger.exception` — same reasoning as :5058 above.
+        _log_isolation_failure("failed to rebuild job progress for unlaunched resume %s", import_id)
         return
     _fail_unlaunched_job(prog, cfg, eng, exc)
 
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 5c062804..62d51885 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -2267,6 +2267,24 @@ def _loss_streak_cell(dated_returns: list[tuple], floor: int) -> dict:
     return {"value": _longest_negative_streak(ordered), "n": n, "insufficient": False}
 
 
+def _drawdown_ticker_slice_map(
+    session: Session, horizon: int, slice_tickers: list[str], batch: int,
+) -> dict[tuple[str, str], tuple]:
+    """ops-hardening iter-46 (AG-8): the `(symbol, asof_date_iso) -> (max_drawdown, underwater_days,
+    time_to_recover_days)` read for ONE bounded SLICE of tickers — `compute_drawdown_expectations`'s chunk
+    axis (`research.drawdown_expectations_ticker_chunk`), mirroring `research.py`'s `_fr_slice_map`. A
+    named function (not an inlined loop body) so a test can wrap/instrument it to observe the live
+    per-slice size directly (TC-2)."""
+    fr_stmt = select(
+        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
+        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(slice_tickers))
+    stored_by_key: dict[tuple[str, str], tuple] = {}
+    for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).yield_per(batch):
+        stored_by_key[(symbol, asof_date.isoformat())] = (mdd, uw, ttr)
+    return stored_by_key
+
+
 def compute_drawdown_expectations(
     session: Session, claim: dict, config: Optional[Config] = None
 ) -> Optional[dict]:
@@ -2329,18 +2347,27 @@ def compute_drawdown_expectations(
     # designed purpose, the per-query row-stream size, never as the chunk width). The chunks partition
     # `tickers` disjointly, so the built dict is byte-identical to the single-query version (same keys,
     # same values — chunking only changes how many rows are in flight from the DB at once).
+    #
+    # ops-hardening iter-46 (AG-8, TC-2): the QUERY above was already ticker-chunked and `yield_per`-
+    # streamed, but every chunk's rows used to land in the SAME `stored_by_key` dict, retained WHOLE until
+    # the separate phase-aggregation loop ran afterward over the full `rows` list — a bounded READ,
+    # unbounded RETENTION (the exact shape iter-40's lesson names; `forward_testing.py:2343` pre-fix, the
+    # evidence-serving path's other named `MemoryError` site). Each chunk's `stored_by_key` slice is now
+    # folded into the by-phase accumulators immediately below and discarded before the next chunk's query
+    # starts, so peak live size is bounded by (chunk width tickers x their forward-returns rows), never by
+    # the claim's whole cohort. This requires indexing the already-in-memory `rows` list (the
+    # `compute_samples` cohort resolved above — bounded by claim resolution already, NOT the accumulator
+    # being bounded here) by ticker ONCE, so each chunk's aggregation pass only touches that chunk's own
+    # rows. `by_phase_mdd`/`by_phase_uw`/`by_phase_ttr`/`by_phase_returns` are order-insensitive
+    # accumulators (`_median_p90` sorts internally; `_loss_streak_cell` collapses-by-date and sorts
+    # chronologically internally — see their own docstrings), so folding per chunk instead of in the
+    # original `rows` order changes nothing about the emitted `by_phase` payload — byte-identical (TC-3).
     tickers = sorted({r["ticker"] for r in rows})
     chunk_width = max(1, cfg.research.drawdown_expectations_ticker_chunk)
     read_batch = cfg.research.read_batch_size
-    stored_by_key: dict[tuple[str, str], tuple] = {}
-    for i in range(0, len(tickers), chunk_width):
-        chunk = tickers[i : i + chunk_width]
-        fr_stmt = select(
-            ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
-            ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
-        ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(chunk))
-        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).yield_per(read_batch):
-            stored_by_key[(symbol, asof_date.isoformat())] = (mdd, uw, ttr)
+    rows_by_ticker: dict[str, list[dict]] = defaultdict(list)
+    for row in rows:
+        rows_by_ticker[row["ticker"]].append(row)
 
     # the SAME causal timeline `compute_market_phase` reads (all-history — the expectations panel is
     # descriptive over the claim's WHOLE tested cohort, not scoped to a single "today" as-of).
@@ -2351,23 +2378,30 @@ def compute_drawdown_expectations(
     by_phase_ttr: dict[str, list[float]] = defaultdict(list)
     by_phase_returns: dict[str, list[tuple]] = defaultdict(list)
 
-    for row in rows:
-        date_iso = row["snapshot_date"]
-        ctx = phases.get(date_iso)
-        if ctx is None:
-            continue  # no causal phase classification for this date (short benchmark window) -> excluded
-        phase = ctx["phase"]
-        by_phase_returns[phase].append((date_iso, row["forward_return"]))
-        stored = stored_by_key.get((row["ticker"], date_iso))
-        if stored is None:
-            continue
-        mdd, uw, ttr = stored
-        if mdd is not None:
-            by_phase_mdd[phase].append(mdd)
-        if uw is not None:
-            by_phase_uw[phase].append(uw)
-        if ttr is not None:
-            by_phase_ttr[phase].append(ttr)
+    for i in range(0, len(tickers), chunk_width):
+        chunk = tickers[i : i + chunk_width]
+        stored_by_key = _drawdown_ticker_slice_map(session, horizon, chunk, read_batch)
+
+        # fold THIS chunk's rows into the by-phase accumulators immediately, then let `stored_by_key`
+        # go out of scope (rebound next iteration) before the next chunk's query starts (TC-2's bound).
+        for ticker in chunk:
+            for row in rows_by_ticker.get(ticker, []):
+                date_iso = row["snapshot_date"]
+                ctx = phases.get(date_iso)
+                if ctx is None:
+                    continue  # no causal phase classification for this date (short window) -> excluded
+                phase = ctx["phase"]
+                by_phase_returns[phase].append((date_iso, row["forward_return"]))
+                stored = stored_by_key.get((row["ticker"], date_iso))
+                if stored is None:
+                    continue
+                mdd, uw, ttr = stored
+                if mdd is not None:
+                    by_phase_mdd[phase].append(mdd)
+                if uw is not None:
+                    by_phase_uw[phase].append(uw)
+                if ttr is not None:
+                    by_phase_ttr[phase].append(ttr)
 
     by_phase = [
         {
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index a5516caf..9f53baf4 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -759,51 +759,60 @@ def _combination_observations(
 
     `as_of` (iter-19, J-32) optionally scopes the pool to snapshots with `ScannerRun.asof_date <= as_of`
     (the SAME single membership filter as `_factor_observations` / `forward_testing`); `as_of=None` adds
-    NO clause → byte-identical all-history."""
+    NO clause → byte-identical all-history.
+
+    ops-hardening iter-46 (AG-8): this sibling of `_factor_observations` used to build ONE
+    `ret_by_run_symbol` dict over the ENTIRE horizon's `forward_returns` population in a single pass —
+    1,285,609 rows measured live at horizon=20 (the evidence-serving path's other named `MemoryError`
+    site, `research.py:777` pre-fix) — even though the source query was already `yield_per`-streamed (a
+    bounded READ, unbounded RETENTION, the exact shape iter-40's lesson names). Now mirrors
+    `_factor_observations`'s already-audited iter-29 fix exactly: `_runs_with_fr` discovers the distinct
+    run ids ONCE (bounded by run count, never by pair count), walked in bounded SLICES of
+    `research.factor_join_run_chunk`; each slice reuses the SAME `_fr_slice_map` join-map builder
+    `_factor_observations` already uses (its `max_drawdown` half is simply unused here), then that slice's
+    matching `ScannerResult`s are streamed ordered `(run_id, id)` and `observations` extended, before the
+    slice's dict is rebound (not accumulated into) on the next iteration — eligible for GC before the next
+    chunk's query starts. Slices walk the sorted `runs_with_fr` list in non-overlapping increasing ranges,
+    so concatenating each slice's `(run_id, id)`-ordered output reproduces the SAME global order the prior
+    single-pass implementation produced — byte-identical (TC-3), never re-derived. No new config knob."""
     parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
-    # iter-47 (J-105): column-project + stream the forward-return scan (run_id, symbol, realized_return),
-    # bounded by config — same byte-identical values as the prior full-ORM `.all()`.
-    batch = (cfg or get_config()).research.read_batch_size
-    fr_stmt = select(
-        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return
-    ).where(ForwardReturn.horizon == horizon)
-    if as_of is not None:
-        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
-            ScannerRun.asof_date <= as_of
-        )
-    ret_by_run_symbol: dict[tuple[int, str], float] = {}
-    runs_with_fr_set: set[int] = set()
-    for run_id, symbol, realized_return in session.exec(fr_stmt).yield_per(batch):
-        ret_by_run_symbol[(run_id, symbol)] = realized_return
-        runs_with_fr_set.add(run_id)
-    runs_with_fr = sorted(runs_with_fr_set)
-    # iter-48 (J-105): stream the ScannerResult side with `yield_per` (full ORM row — `record_json` is read
-    # by `_extract_factor_value` for component factors). Order by `(run_id, id)` — the EXACT prior implicit
-    # `.all()` order on the `run_id IN (...)` filter, which rides the `ix_scanner_results_run_id` index (no
-    # temp-B-tree sort, no disk spill). This closes the latent cold-miss OOM on the factor-combination path
-    # (masked only by the EventStudyCache hit) while keeping every composite/strict-overlap figure identical.
-    res_stmt = (
-        select(ScannerResult)
-        .where(ScannerResult.run_id.in_(runs_with_fr))
-        .order_by(ScannerResult.run_id, ScannerResult.id)
-    )
-    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
+    research_cfg = (cfg or get_config()).research
+    batch = research_cfg.read_batch_size
+    run_chunk = research_cfg.factor_join_run_chunk
+
+    # iter-46 (AG-8): the distinct run ids at this horizon, via the SAME shared DISTINCT-projected
+    # discovery `_factor_observations` uses — bounded by run count, never by (run, symbol) pair count.
+    runs_with_fr = _runs_with_fr(session, [horizon], as_of)
 
     observations: list[dict] = []
-    for res in results:
-        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
-        if realized is None:
-            continue  # no realized return at this horizon for this stock (excluded, never fabricated)
-        values: dict[str, float] = {}
-        for key, parsed in parsed_by_key.items():
-            value = _extract_factor_value(res, parsed)
-            if value is None:
-                break  # a NULL in ANY referenced factor EXCLUDES this observation (never fabricated)
-            values[key] = float(value)
-        else:  # ran without a break -> every referenced factor was non-null
-            observations.append({
-                "run_id": res.run_id, "ticker": res.ticker, "return": realized, "values": values,
-            })
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        # reuses `_fr_slice_map` (the SAME per-slice join accumulator `_factor_observations` already
+        # uses) rather than a second near-duplicate builder — this pool only reads the `realized_return`
+        # half of its `(realized_return, max_drawdown)` tuple.
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult)
+            .where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+            if fr is None:
+                continue  # no realized return at this horizon for this stock (excluded, never fabricated)
+            realized, _max_drawdown = fr  # this pool doesn't carry max_drawdown; the shared map does
+            values: dict[str, float] = {}
+            for key, parsed in parsed_by_key.items():
+                value = _extract_factor_value(res, parsed)
+                if value is None:
+                    break  # a NULL in ANY referenced factor EXCLUDES this observation (never fabricated)
+                values[key] = float(value)
+            else:  # ran without a break -> every referenced factor was non-null
+                observations.append({
+                    "run_id": res.run_id, "ticker": res.ticker, "return": realized, "values": values,
+                })
+        # `ret_by_run_symbol` is rebound (not accumulated into) on the next iteration — this slice's dict
+        # is eligible for GC before the next chunk's query even starts (the bounded-memory guarantee, TC-1).
     return observations
 
 
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index 61c3b213..1e42db48 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -31,8 +31,9 @@ from sqlalchemy.engine import Engine
 from sqlmodel import Session, select
 
 from app.config import Config, get_config
-from app.engine import data_manager
+from app.engine import data_manager, evidence, forward_testing
 from app.engine.forward_testing import backfill_forward_returns, walk_forward_asof_dates
+from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.prices import bar_cache, latest_data_date
 from app.engine.scanner import get_run_for_date, run_scan
 from app.models import ScannerRun
@@ -149,6 +150,73 @@ def _warm_coverage_snapshot(engine: Engine, cfg: Config) -> None:
         logger.exception("coverage snapshot warm failed (non-fatal): %s", exc)
 
 
+def _warm_drawdown_expectations(engine: Engine, cfg: Config) -> None:
+    """ops-hardening iter-46 FIX PASS (QA blocker 3 — J-06/J-07): precompute the per-claim
+    `drawdown_expectations` EventStudyCache rows `GET /api/evidence` looks up lazily, so the FIRST Evidence
+    page view after a BOOT is a cache hit instead of a multi-minute synchronous cold compute on the request
+    path.
+
+    WHY THIS EXISTS: the ingest finalize tail already warms exactly this cache
+    (`data_manager._refresh_ingest_aggregates`'s ledger loop, iter-7/audit B1), but nothing warmed it after
+    a plain RESTART — so every backend restart left the next Evidence viewer paying the full cold miss.
+    Measured on this host against the live DB, with the backend idle and NO ingest job running: a cold
+    `GET /api/evidence` returned HTTP 200 in **163.3s**; the immediately-following requests served in
+    **11-52ms**. The committed budget (`reports/perf-budgets.md` Item I) is the WARM steady-state ≤3s, so
+    closing the post-restart cold window is what makes that budget real for a user who simply opens the
+    page after a restart.
+
+    CONTRACT — mirrors `_warm_membership_timeline` / `_warm_coverage_snapshot` verbatim: opens its OWN
+    session on `engine` (never a request session); is IDEMPOTENT (each claim's call is
+    `compute_drawdown_expectations_cached`, so an already-warm row is a cheap HIT, never a recompute);
+    computes no canonical value (the cached payload IS the canonical compute, persisted); and is NON-FATAL
+    at BOTH levels — one unresolvable/erroring claim never blocks the others, and no failure here can flip
+    an otherwise-successful warm-up to `failed`.
+
+    Applies the SAME two filters `evidence.build_evidence_payload` and the finalize tail already apply, so
+    the warmed cache subjects match exactly what a live `/api/evidence` request looks up: skip
+    `type == FORWARD_WALK_TYPE` monitoring records (they re-score an existing claim — not a claim with a
+    panel of its own), and take the claim via `entry.get("claim")`.
+
+    SEQUENCING (load-bearing): `_run_warmup` calls this only AFTER it has set `prog.status = "ok"`. This
+    step is expensive, and the readiness badge J-04 and J-07 step 1 depend on must flip `Ready` on exactly
+    the schedule it did before this fix — so this warm is deliberately OUTSIDE the readiness path. The
+    consequence is disclosed honestly: an Evidence view landing inside the short window between `ok` and
+    this warm's completion still pays the cold miss."""
+    try:
+        entries = read_entries(evidence.resolve_ledger_path())
+    except Exception as exc:  # NON-FATAL: a missing/corrupt ledger degrades to zero warm calls
+        logger.exception("evidence drawdown-expectations ledger read failed (non-fatal): %s", exc)
+        return
+    warmed = 0
+    try:
+        with Session(engine) as session:
+            for entry in entries:
+                if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
+                    continue
+                claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
+                try:
+                    if forward_testing.compute_drawdown_expectations_cached(session, claim, cfg) is not None:
+                        warmed += 1
+                # A `MemoryError` stops THIS loop immediately rather than hammering the next claim's
+                # allocation under real pressure — the module-wide iter-8 isolation convention. Caught
+                # distinctly from the generic per-claim continue below, and tested against a TEXTLESS
+                # `MemoryError` (`str(MemoryError())` is `""`).
+                except MemoryError as exc:
+                    logger.exception(
+                        "evidence drawdown-expectations warm aborted — memory pressure, stopping remaining "
+                        "claims: %r", exc,
+                    )
+                    data_manager._release_process_memory()
+                    break
+                except Exception as exc:  # NON-FATAL: one bad claim never blocks the others
+                    logger.exception(
+                        "evidence drawdown-expectations warm failed for one claim (non-fatal): %r", exc
+                    )
+        logger.info("evidence drawdown-expectations cache warmed (%d claim panels)", warmed)
+    except Exception as exc:  # NON-FATAL: must never fail the otherwise-successful warm-up
+        logger.exception("evidence drawdown-expectations cache warm failed (non-fatal): %s", exc)
+
+
 def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -> None:
     """The warm-up worker body (runs in the daemon thread). Persists each remaining cadence snapshot via
     the canonical `run_scan` (batched by `config.startup.warmup_batch_size` for progress ticks), then runs
@@ -219,6 +287,16 @@ def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -
         logger.exception("background warm-up failed (non-fatal): %s", exc)
     finally:
         prog.finished_at = data_manager._utcnow()
+    # ops-hardening iter-46 FIX PASS (QA blocker 3 — J-06/J-07): warm the per-claim evidence
+    # (drawdown-expectations) cache LAST, strictly AFTER the warm-up record has fully settled above — this
+    # step is expensive (163.3s measured live for the 7 committed claims) and the readiness badge J-04 and
+    # J-07 step 1 depend on must flip `Ready` on exactly the schedule it did before this fix. Placed after
+    # the `finally` (not inside the `try`) so it can never influence the warm-up's own status/timing, and
+    # gated on a SUCCESSFUL warm-up: a failed warm-up leaves the basis partial, and the ingest finalize
+    # tail already owns the post-ingest warm for that path. `_warm_drawdown_expectations` never raises (it
+    # is fully guarded at both the ledger-read and per-claim levels), so this call cannot break the thread.
+    if prog.status == "ok":
+        _warm_drawdown_expectations(engine, cfg)
 
 
 def start_warmup(engine: Engine, config: Optional[Config] = None) -> str:
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index a93b61f7..c9528f64 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -6087,3 +6087,79 @@ def test_fatal_job_failure_log_never_leaks_the_provider_key(tmp_path, monkeypatc
     assert "data_manager.py" in caplog.text, (
         "the frames must survive the scrub — a traceback is the whole reason B6 asked for this record"
     )
+
+
+# ==================================================================================================
+# ops-hardening iter-46 (TC-5) — the LAST two bare `logger.exception` sites in this module,
+# `_fail_unlaunched_job` (`:5058`, its own `_finalize_run_record` persistence failure) and
+# `_fail_unlaunched_resume` (`:5091`, its own checkpoint-rebuild failure), disclosed as a "Known Issues"
+# carry-forward by the iter-45 dev handoff (not on the audit's own T4 list, so left alone under fix-mode
+# scope discipline that pass). Same class as B3/B5/B6: a logging allocation inside a failure handler that
+# runs under memory pressure. Both are now guarded by `_log_isolation_failure`, proven here with the SAME
+# TEXTLESS `MemoryError()` convention every other guard in this module is tested with.
+# ==================================================================================================
+def test_fail_unlaunched_job_persistence_failure_survives_a_raising_logging_call(tmp_path, monkeypatch):
+    """`data_manager.py:5058` — `_fail_unlaunched_job`'s own `_finalize_run_record` call fails (any
+    persistence error), and the guard's first (fuller) logging attempt ALSO raises a textless
+    `MemoryError` (the induced pressure this guard exists for). `_fail_unlaunched_job` must still return
+    normally (never propagate the logging failure out past the launch-failure path it is already on), and
+    the traceback-free fallback record must still name the unlaunched job."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fail_unlaunched_job_logging.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    def _boom_finalize(*_a, **_k):
+        raise MemoryError()  # noqa: RSE102 — textless: the persistence failure under test
+
+    def _boom_exception(*_a, **_k):
+        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap
+
+    monkeypatch.setattr(data_manager, "_finalize_run_record", _boom_finalize)
+    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
+    fallback = _record_log_calls(monkeypatch, "error")
+
+    prog = JobProgress(job_id="iter46-fail-unlaunched-job-probe", kind="backfill",
+                        start=date(2024, 1, 2), end=date(2024, 1, 2))
+    launch_exc = RuntimeError("can't start new thread")
+
+    data_manager._fail_unlaunched_job(prog, cfg, engine, launch_exc)  # must NOT raise
+
+    assert prog.status == "failed", "the guard's own job bookkeeping must be unaffected by the log failure"
+    naming_this_job = [rec for rec in fallback if prog.job_id in rec]
+    assert len(naming_this_job) == 1, (
+        f"the traceback-free fallback must name the unlaunched job exactly once — got {fallback!r}"
+    )
+    assert "traceback omitted" in naming_this_job[0]
+
+
+def test_fail_unlaunched_resume_checkpoint_rebuild_failure_survives_a_raising_logging_call(tmp_path, monkeypatch):
+    """`data_manager.py:5091` — `_fail_unlaunched_resume`'s own checkpoint-rebuild step fails (any error
+    loading/seeding the progress from the durable checkpoint), and the guard's first (fuller) logging
+    attempt ALSO raises a textless `MemoryError`. `_fail_unlaunched_resume` must still return normally
+    (the bookkeeping-failure handler's own documented contract), and the traceback-free fallback record
+    must still name the unlaunched resume's import id."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fail_unlaunched_resume_logging.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    def _boom_load_checkpoint(*_a, **_k):
+        raise MemoryError()  # noqa: RSE102 — textless: the checkpoint-rebuild failure under test
+
+    def _boom_exception(*_a, **_k):
+        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap
+
+    monkeypatch.setattr(data_manager, "_load_checkpoint", _boom_load_checkpoint)
+    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
+    fallback = _record_log_calls(monkeypatch, "error")
+
+    import_id = "iter46-fail-unlaunched-resume-probe"
+    launch_exc = RuntimeError("can't start new thread")
+
+    data_manager._fail_unlaunched_resume(import_id, cfg, engine, launch_exc)  # must NOT raise
+
+    naming_this_import = [rec for rec in fallback if import_id in rec]
+    assert len(naming_this_import) == 1, (
+        f"the traceback-free fallback must name the unlaunched resume's import id exactly once — got "
+        f"{fallback!r}"
+    )
+    assert "traceback omitted" in naming_this_import[0]
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 30c09fb5..44f83e2d 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -1877,3 +1877,47 @@ def test_drawdown_expectations_chunk_width_one_issues_multiple_queries(dd_expect
         f"expected multiple chunked ForwardReturn queries at chunk_width=1 over 4 distinct tickers, "
         f"got {query_count['n']}"
     )
+
+
+# ==================================================================================================
+# ops-hardening iter-46 (AG-8, TC-2): the QUERY into `stored_by_key` was already ticker-chunked
+# (iter-36), but every chunk's rows used to land in the SAME dict, RETAINED WHOLE until the separate
+# phase-aggregation loop ran afterward over the full `rows` list — a bounded READ, unbounded RETENTION
+# (the exact shape iter-40's lesson names; `forward_testing.py:2343` pre-fix, the evidence-serving path's
+# other named `MemoryError` site). Each chunk's `stored_by_key` slice (now built by the named
+# `_drawdown_ticker_slice_map` helper, mirroring `research.py`'s `_fr_slice_map`) is folded into the
+# by-phase accumulators immediately and discarded before the next chunk starts.
+# ==================================================================================================
+def test_drawdown_expectations_stored_by_key_accumulator_is_chunk_bounded(dd_expectations_engine, monkeypatch):
+    """TC-2: the live `stored_by_key` slice (`_drawdown_ticker_slice_map`'s return value, wrapped via
+    monkeypatch) never holds more than ONE chunk's worth of (symbol, date) entries at any point during a
+    call — never the claim's whole cohort (this fixture's 4 distinct tickers x their forward-returns
+    rows) all at once."""
+    import app.engine.forward_testing as forward_testing_module
+
+    observed_sizes: list[int] = []
+    real_slice_map = forward_testing_module._drawdown_ticker_slice_map
+
+    def _wrapped(session, horizon, slice_tickers, batch):
+        result = real_slice_map(session, horizon, slice_tickers, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(forward_testing_module, "_drawdown_ticker_slice_map", _wrapped)
+    cfg = load_config()
+    research_cfg = cfg.research.model_copy(update={"drawdown_expectations_ticker_chunk": 1})
+    cfg = cfg.model_copy(update={"research": research_cfg})
+
+    with Session(dd_expectations_engine) as session:
+        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg)
+
+    assert payload is not None
+    # this fixture carries 4 distinct tickers (AAA/BBB/CCC/DDD) — at chunk width 1, one slice per ticker.
+    assert len(observed_sizes) == 4, f"expected 4 per-ticker chunks, got {len(observed_sizes)}"
+    # AAA alone contributes 4 dated rows (the widest single ticker in this fixture) — every OTHER ticker
+    # contributes fewer, so the live slice never holds all 7 rows across all 4 tickers at once.
+    total_rows = 7  # 4 (AAA) + 1 (BBB) + 1 (DDD) + 1 (CCC, unclassified but still a stored ForwardReturn row)
+    assert max(observed_sizes) < total_rows, (
+        f"the live accumulator must never hold the whole cohort's rows at once — got {observed_sizes!r}"
+    )
+    assert max(observed_sizes) <= 4, f"a single ticker's own slice must not exceed its own row count, got {observed_sizes!r}"
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index a0bf48f7..4fe947f2 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -806,3 +806,174 @@ def test_factor_observations_chunks_at_the_shipped_config(tmp_path, monkeypatch)
     assert max(observed_sizes) < total_pairs, (
         "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
     )
+
+
+# ==================================================================================================
+# ops-hardening iter-46 (AG-8): `_combination_observations`'s join accumulator (`ret_by_run_symbol`) used
+# to hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history
+# for as_of=None (1,285,609 rows measured live at horizon=20) — the evidence-serving path's OTHER named
+# `MemoryError` site (`research.py:777` pre-fix), `_factor_observations`'s own iter-29 sibling gap. The fix
+# mirrors iter-29 exactly: `_runs_with_fr` discovers run ids once, `_fr_slice_map` (the SAME helper
+# `_factor_observations` already uses) builds each bounded slice's join map, discarded before the next.
+# These proofs pin, for `_combination_observations` specifically:
+#   1. TC-1: the live accumulator (`_fr_slice_map`'s return value) never holds more than one chunk's worth
+#      of entries at any point during a call.
+#   2. TC-3: the chunked rewrite is byte-identical to a pinned copy of the PRE-FIX (single-accumulator)
+#      implementation, for as_of=None AND a historical as_of=D — reproducing the live certified-claims
+#      ledger's one `kind == "combination"` claim (`condition: ["rs_spy_3m:top:quintile",
+#      "high_proximity:top:tertile"]`, `horizon: 20` — `runs/goal-session-mcp-loop/state/
+#      certified-claims.jsonl`), both `leadership.components` factors read from `record_json`.
+# ==================================================================================================
+def _leadership_component_record_json(ticker: str, rs_spy_3m: float, high_proximity: float) -> str:
+    """A `record_json` blob carrying the TWO component factors the live ledger's one `combination`-kind
+    claim actually references (`leadership.components.rs_spy_3m.raw` and
+    `leadership.components.high_proximity.raw`, `config.yaml:935/937`) — the exact shape
+    `_extract_factor_value` reads for a `component` factor."""
+    return json.dumps({
+        "ticker": ticker, "name": ticker,
+        "leadership": {"components": [
+            {"name": "rs_spy_3m", "raw": rs_spy_3m},
+            {"name": "high_proximity", "raw": high_proximity},
+        ]},
+    })
+
+
+@pytest.fixture()
+def combination_chunked_engine(tmp_path):
+    """The SAME 5-run / 3-ticker-per-run shape as `chunked_accumulator_engine` (15 distinct (run_id,
+    symbol) pairs spanning 5 distinct run ids — enough to force multiple slices at a small run-chunk
+    width), but with `record_json` carrying real `rs_spy_3m` / `high_proximity` component values so the
+    live ledger's one `combination`-kind claim can be reproduced exactly (TC-3)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'combination_chunked.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        runs = [
+            _add_run(session, date(2025, m, 10), regime_label="Risk-on" if m % 2 else "Risk-off")
+            for m in range(1, 6)  # r0=Jan .. r4=May 2025
+        ]
+        session.flush()
+        for i, run in enumerate(runs):
+            for j, base in enumerate(("AA", "BB", "CC")):
+                ticker = f"{base}{i}"  # distinct symbol per run -> 15 genuinely distinct (run_id, symbol) pairs
+                session.add(ScannerResult(
+                    run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
+                    leadership_score=50.0 + i + j, leadership_bucket="C",
+                    entry_quality_score=50.0, entry_quality_bucket="C",
+                    risk_score=50.0, risk_bucket="C",
+                    setup_status="Actionable", rank=j + 1,
+                    record_json=_leadership_component_record_json(
+                        ticker, rs_spy_3m=0.10 * (i + 1) + 0.01 * j, high_proximity=-0.05 * (i + 1) - 0.01 * j,
+                    ),
+                ))
+                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
+                        mae=-0.02, mfe=0.05, mdd=-0.03 - 0.001 * j)
+        session.commit()
+    return engine
+
+
+def _combination_observations_reference_unchunked(session, factors, horizon, as_of, cfg):
+    """A pinned copy of the PRE-iter-46 `_combination_observations` body: ONE unbounded
+    `ret_by_run_symbol` accumulator built from a SINGLE un-sliced `fr_stmt` covering the FULL
+    `runs_with_fr` set at once (no `_fr_slice_map`, no chunk loop) — the regression oracle for TC-3. Calls
+    the SAME unchanged helpers (`parse_factor_source`, `_extract_factor_value`) the real, rewritten
+    function still uses, so any divergence can only come from the chunking itself."""
+    from app.engine.research import _extract_factor_value, parse_factor_source
+    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
+    batch = cfg.research.read_batch_size
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return
+    ).where(ForwardReturn.horizon == horizon)
+    if as_of is not None:
+        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
+            ScannerRun.asof_date <= as_of
+        )
+    ret_by_run_symbol: dict[tuple[int, str], float] = {}
+    runs_with_fr_set: set[int] = set()
+    for run_id, symbol, realized_return in session.exec(fr_stmt).yield_per(batch):
+        ret_by_run_symbol[(run_id, symbol)] = realized_return
+        runs_with_fr_set.add(run_id)
+    runs_with_fr = sorted(runs_with_fr_set)
+    res_stmt = (
+        select(ScannerResult)
+        .where(ScannerResult.run_id.in_(runs_with_fr))
+        .order_by(ScannerResult.run_id, ScannerResult.id)
+    )
+    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
+    observations = []
+    for res in results:
+        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
+        if realized is None:
+            continue
+        values: dict[str, float] = {}
+        for key, parsed in parsed_by_key.items():
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                break
+            values[key] = float(value)
+        else:
+            observations.append({
+                "run_id": res.run_id, "ticker": res.ticker, "return": realized, "values": values,
+            })
+    return observations
+
+
+def test_combination_observations_accumulator_is_chunk_bounded(combination_chunked_engine, monkeypatch):
+    """TC-1: `_combination_observations`'s join accumulator (`_fr_slice_map`'s return value, wrapped via
+    monkeypatch) never holds more entries than ONE bounded chunk at any point during the call — never one
+    entry per distinct (run_id, symbol) pair in the whole fixture (15 pairs across 5 run ids)."""
+    cfg = load_config()
+    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
+    assert len(factors) == 2, "sanity: the live claim's two factors must resolve from the shipped catalog"
+    observed_sizes: list[int] = []
+    real_fr_slice_map = research_module._fr_slice_map
+
+    def _wrapped(session, horizon, slice_run_ids, batch):
+        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
+    with Session(combination_chunked_engine) as session:
+        # chunk width = 2 run ids/slice over 5 distinct run ids -> 3 slices (2, 2, 1 run ids each)
+        observations = research_module._combination_observations(
+            session, factors, H, None, cfg=_cfg_batch(2)
+        )
+
+    total_pairs = 15  # 5 runs x 3 tickers, by fixture construction
+    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
+    assert len(observed_sizes) == 3, f"expected 3 chunks (5 run ids at width 2), got {len(observed_sizes)}"
+    assert max(observed_sizes) <= 6, (
+        f"a single slice must never exceed 2 run ids x 3 tickers = 6 entries, got {max(observed_sizes)}"
+    )
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once"
+    )
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
+def test_combination_observations_chunked_equals_unchunked_reference(combination_chunked_engine, as_of):
+    """TC-3: the iter-46 chunked `_combination_observations` is byte-identical to the pinned pre-fix
+    (single-accumulator) reference — for as_of=None (all-history) AND a historical as_of=D (2025-03-15)
+    that splits the 5-run fixture into an early (Jan-Mar) / late (Apr-May) group. Uses the live certified-
+    claims ledger's own two-factor combination (`rs_spy_3m`, `high_proximity`) at its own horizon (20)."""
+    cfg = _cfg_batch(2)
+    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
+    with Session(combination_chunked_engine) as session:
+        chunked = research_module._combination_observations(session, factors, H, as_of, cfg=cfg)
+        reference = _combination_observations_reference_unchunked(session, factors, H, as_of, cfg)
+    assert chunked, "sanity: the fixture must produce at least one observation"
+    assert _eq(chunked, reference), f"chunked output != pinned pre-fix reference (as_of={as_of})"
+
+
+def test_combination_observations_chunked_as_of_excludes_runs_after_cutoff(combination_chunked_engine):
+    """No-lookahead guard: for the as_of=D-scoped chunked call, zero returned observations reference a run
+    dated after D."""
+    d = date(2025, 3, 15)  # between run r2 (Mar 10) and run r3 (Apr 10)
+    cfg = load_config()
+    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
+    with Session(combination_chunked_engine) as session:
+        observations = research_module._combination_observations(session, factors, H, d, cfg=_cfg_batch(2))
+        run_dates = {run.id: run.asof_date for run in session.exec(select(ScannerRun)).all()}
+    assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
+    for obs in observations:
+        assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"
diff --git a/apps/backend/tests/test_warmup.py b/apps/backend/tests/test_warmup.py
index 0b34d553..b19750ce 100644
--- a/apps/backend/tests/test_warmup.py
+++ b/apps/backend/tests/test_warmup.py
@@ -708,3 +708,125 @@ def _forward_return_fingerprint(session: Session) -> dict:
         )
         for fr in frs
     }
+
+
+# ==================================================================================================
+# ops-hardening iter-46 FIX PASS (QA blockers 3 — J-06 / J-07) — the evidence (per-claim
+# drawdown-expectations) cache boot warm.
+#
+# WHAT THE QA RUN MEASURED: `GET /api/evidence` did not return inside a 300s budget, both in isolation
+# (UT-J-06 step 7) and under concurrent load (UT-J-07). The dev handoff and the QA report both attributed
+# this to GIL contention from a concurrent backfill's finalize tail.
+#
+# THAT ATTRIBUTION WAS WRONG, and this fix pass measured it directly: on a FULLY IDLE, freshly-restarted
+# backend with no ingest job running at all, a cold `GET /api/evidence` took **163.3s** (HTTP 200, 100%
+# CPU, one runnable thread, ~1 GB RSS — never a memory problem). Immediately afterwards the SAME endpoint
+# served in **11-52ms**. So the endpoint is not slow; its COLD MISS is expensive, and the committed budget
+# (`reports/perf-budgets.md` Item I) is explicitly the WARM steady-state one (≤3s).
+#
+# ROOT CAUSE: the per-claim `drawdown_expectations` EventStudyCache is warmed by the INGEST finalize tail
+# (`data_manager._refresh_ingest_aggregates`) but NOT by the boot warm-up — so every backend restart left
+# the first `/evidence` viewer paying the full 7-claim cold compute synchronously, on the request path.
+# The QA run restarted the backend immediately before the browser sweep, which is exactly why it hit it.
+#
+# THE FIX MIRRORS THE TWO WARM STEPS ALREADY BESIDE IT (`_warm_membership_timeline`, iter-36;
+# `_warm_coverage_snapshot`, iter-2): own session on the engine, idempotent (a cache HIT is a cheap no-op),
+# NON-FATAL, and — critically — sequenced AFTER the warm-up record reaches `ok` so the readiness badge
+# (J-04, and J-07 step 1's "Ready") is never delayed by it.
+# ==================================================================================================
+def _stub_ledger(monkeypatch, entries):
+    """Pin the ledger the warm loop iterates — the committed ledger's real contents are not the subject
+    of these proofs, only which of its entries get warmed."""
+    monkeypatch.setattr(warmup_mod, "read_entries", lambda _path: entries)
+    monkeypatch.setattr(warmup_mod.evidence, "resolve_ledger_path", lambda *_a, **_k: "unused.jsonl")
+
+
+def test_warmup_warms_every_ledger_claim_and_skips_forward_walk_records(early_engine, monkeypatch):
+    """The boot warm must warm the SAME per-claim cache `GET /api/evidence` looks up lazily — once per
+    ORIGINAL claim — and must skip `forward_walk` MONITORING records, applying the exact filter
+    `build_evidence_payload` and the ingest finalize tail already apply (a forward-walk record re-scores an
+    existing claim; it is not itself a claim with a panel to warm)."""
+    engine, cfg = early_engine
+    claim_a = {"signal": "claim-a", "horizon": 20}
+    claim_b = {"signal": "claim-b", "horizon": 60}
+    _stub_ledger(monkeypatch, [
+        {"type": "claim", "claim": claim_a},
+        {"type": "forward_walk", "claim": {"signal": "monitoring-record", "horizon": 20}},
+        {"type": "claim", "claim": claim_b},
+        "a malformed non-dict ledger line",
+    ])
+    warmed: list[dict] = []
+    monkeypatch.setattr(
+        warmup_mod.forward_testing, "compute_drawdown_expectations_cached",
+        lambda _session, claim, _cfg: warmed.append(claim) or {"by_phase": []},
+    )
+
+    warmup_mod._warm_drawdown_expectations(engine, cfg)
+
+    assert warmed == [claim_a, claim_b], (
+        "the boot warm must warm exactly the ORIGINAL claims, in ledger order, skipping forward-walk "
+        f"monitoring records and malformed lines; warmed={warmed}"
+    )
+
+
+def test_warmup_drawdown_expectations_failure_is_nonfatal_on_textless_memoryerror(
+    early_engine, monkeypatch, caplog
+):
+    """A `MemoryError` — raised TEXTLESS, the shape this session's honesty rule requires every new handler
+    to be tested against (`str(MemoryError())` is `""`, so any handler that relies on the message degrades
+    silently) — during the evidence warm is CAUGHT + logged and does NOT flip an otherwise-successful
+    warm-up to `failed`. Mirrors the membership-timeline / coverage-snapshot non-fatal proofs above."""
+    engine, cfg = early_engine
+    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+    _stub_ledger(monkeypatch, [{"type": "claim", "claim": {"signal": "boom", "horizon": 20}}])
+
+    def _boom(*_args, **_kwargs):
+        raise MemoryError()  # TEXTLESS on purpose — see docstring
+
+    monkeypatch.setattr(warmup_mod.forward_testing, "compute_drawdown_expectations_cached", _boom)
+    with caplog.at_level("ERROR"):
+        job_id = start_warmup(engine, cfg)
+        _join_warmup(job_id)
+
+    rec = data_manager.get_job(job_id)
+    assert rec is not None and rec["status"] == "ok", (
+        f"an evidence-cache warm failure must be non-fatal to the warm-up; record={rec}"
+    )
+    assert any(
+        "drawdown-expectations" in r.message.lower() or "drawdown_expectations" in r.message.lower()
+        for r in caplog.records
+    ), (
+        "the textless MemoryError must still be logged honestly (never swallowed silently); "
+        f"captured={[r.message for r in caplog.records]}"
+    )
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+
+
+def test_warmup_evidence_warm_runs_only_after_readiness_reaches_ok(early_engine, monkeypatch):
+    """SEQUENCING PROOF (protects J-04 and J-07 step 1): the evidence warm is expensive (163.3s measured
+    live for 7 claims), so it must run strictly AFTER the warm-up record has settled `ok` — the readiness
+    badge must flip `Ready` on exactly the same schedule as before this fix. Asserted by reading the job's
+    OWN status at the moment the warm is invoked, never inferred from ordering in the source."""
+    engine, cfg = early_engine
+    ensure_latest_snapshot(engine, cfg)
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+
+    status_when_warmed: list[object] = []
+
+    def _record_status(_engine, _cfg):
+        rec = data_manager.get_job(WARMUP_JOB_ID)
+        status_when_warmed.append(rec["status"] if rec else None)
+
+    monkeypatch.setattr(warmup_mod, "_warm_drawdown_expectations", _record_status)
+    job_id = start_warmup(engine, cfg)
+    _join_warmup(job_id)
+
+    assert status_when_warmed == ["ok"], (
+        "the evidence warm must be invoked exactly once, and only after the warm-up already reported `ok` "
+        "(otherwise it delays the readiness badge J-04/J-07 depend on); "
+        f"status at warm time={status_when_warmed}"
+    )
diff --git a/apps/backend/tests/test_ingest_finalize_zero_work_coverage.py b/apps/backend/tests/test_ingest_finalize_zero_work_coverage.py
new file mode 100644
index 00000000..ddcc568d
--- /dev/null
+++ b/apps/backend/tests/test_ingest_finalize_zero_work_coverage.py
@@ -0,0 +1,217 @@
+"""ops-hardening iter-46 FIX PASS (QA blocker 1 + 4 — J-01 / J-03) — the ingest finalize tail must not pay
+the heavy `_compute_coverage_uncached` derivation for a ZERO-WORK backfill.
+
+WHAT THE QA RUN MEASURED: a backfill whose payload resolved to zero trading days (`dates_total: 0`, QA run
+287 — two weekend dates) never left `status: "running"` for 15+ minutes on an otherwise idle,
+freshly-restarted backend. The per-date work resolved instantly; the job record stayed `running` because
+the finalize tail ran an unconditional full coverage/membership-timeline recompute afterward.
+
+ROOT CAUSE, READ DIRECTLY FROM THE CODE: `_refresh_ingest_aggregates` called `refresh_coverage_snapshot`
+UNCONDITIONALLY on every backfill/both/rebuild. Every OTHER heavy step in that tail is already served by a
+`dataset_version`-keyed cache (forward-aggregates, research hot keys, index series, drawdown expectations),
+so on a zero-work job they are all cheap HITS — `refresh_coverage_snapshot` was the ONE uncached heavy call
+left, and it re-derives the whole payload (its own `prefilled_bar_cache` whole-bar load) even when the
+persisted row already reflects this exact `(asof_key, dataset_version)` stamp.
+
+THE FIX REUSES AN ALREADY-AUDITED GATE, NOT A NEW MECHANISM: `_coverage_snapshot_is_current` was added in
+iter-3 (audit B1) for EXACTLY this purpose and is already applied to the fetch/expand finalize branch
+(`data_manager.py`, "gated by `_coverage_snapshot_is_current` so a zero-work fetch (the common offline
+case) pays no extra compute/write"). This pass applies the SAME gate to the backfill branch.
+
+The contract proven here is a CALL-COUNT contract (mirroring iter-3's own TC-2), never a wall-clock
+assertion: a zero-work finalize must reach `_compute_coverage_uncached` ZERO times, and a genuinely stale
+one must still reach it (no regression to the refresh that keeps `/api/data` honest).
+"""
+from __future__ import annotations
+
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine import data_manager, forward_testing, research
+from app.engine.data_manager import JobProgress
+from app.models import ScannerRun
+
+ASOF = date(2020, 1, 2)
+LATER_ASOF = date(2020, 1, 3)
+
+
+def _make_run(cfg, asof: date) -> ScannerRun:
+    return ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=50.0, regime_label=cfg.regime.labels[0], regime_components_json="[]",
+        new_high_low_json="{}", candidate_counts_json="{}",
+    )
+
+
+@pytest.fixture()
+def finalize_session(tmp_path):
+    """The smallest DB the finalize tail needs: one `ScannerRun` (so the coverage as-of resolves and the
+    per-horizon forward-aggregate loop is reached). No price rows — this module proves a CALL-COUNT
+    contract, so the real cost of any individual warm is irrelevant to what is being asserted."""
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_zero_work.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(_make_run(cfg, ASOF))
+        session.commit()
+    with Session(engine) as session:
+        yield session, cfg
+
+
+@pytest.fixture()
+def quiet_finalize(monkeypatch):
+    """Silence the finalize tail's OTHER aggregate warms so this module measures exactly one thing: how
+    many times the COVERAGE path reaches `_compute_coverage_uncached`. Each stub stands in for a step that
+    is already `dataset_version`-cached in production (a cheap HIT on a zero-work job) — they are not this
+    module's subject."""
+    monkeypatch.setattr(data_manager, "read_entries", lambda _path: [])          # no ledger claims to warm
+    monkeypatch.setattr(data_manager, "subject_catalog", lambda _cfg: [])        # no research hot key
+    monkeypatch.setattr(
+        forward_testing, "forward_aggregates_ingest_cached", lambda *_a, **_k: None
+    )
+
+
+def _spy_uncached_coverage(monkeypatch) -> list[object]:
+    """Record every `_compute_coverage_uncached` call — the heavy derivation whose avoidance IS the fix."""
+    calls: list[object] = []
+    real = data_manager._compute_coverage_uncached
+
+    def _spy(session, cfg, *, as_of=None):
+        calls.append(as_of)
+        return real(session, cfg, as_of=as_of)
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _spy)
+    return calls
+
+
+# ==================================================================================================
+# TC-A1 — a ZERO-WORK backfill's finalize tail must not recompute coverage at all
+# ==================================================================================================
+def test_zero_work_backfill_finalize_skips_heavy_coverage_recompute(
+    finalize_session, quiet_finalize, monkeypatch
+):
+    """TC-A1 (QA blocker 1, J-01): when the persisted `CoverageSnapshot` already reflects the CURRENT
+    `(asof_key, dataset_version)` stamp and the job created NO new snapshot dates, the finalize tail must
+    reach `_compute_coverage_uncached` ZERO times — the same zero-work call-count contract iter-3's B1 fix
+    already established for the fetch/expand branch.
+
+    This is the defect that kept QA run 287 (`dates_total: 0`) `running` for 15+ minutes: nothing to
+    backfill, yet a full coverage/membership-timeline derivation ran anyway."""
+    session, cfg = finalize_session
+    # a prior ingest already persisted the row for this exact stamp (the real precondition, via the real path)
+    data_manager.refresh_coverage_snapshot(session, cfg)
+    assert data_manager._coverage_snapshot_is_current(session, cfg), (
+        "fixture precondition: the persisted snapshot must be current for this stamp before the drill"
+    )
+
+    calls = _spy_uncached_coverage(monkeypatch)  # spy installed AFTER the seed, so it counts only the tail
+    prog = JobProgress(job_id="zero-work-backfill", kind="backfill", start=ASOF, end=ASOF)
+    prog.new_snapshot_dates = []  # the zero-work case: no trading day in range produced a snapshot
+
+    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise
+
+    assert calls == [], (
+        "a zero-work backfill must pay NO coverage recompute — `_compute_coverage_uncached` was reached "
+        f"{len(calls)} time(s) with as_of={calls}. This is the unconditional heavy call that kept QA run "
+        "287 (dates_total:0) in `running` for 15+ minutes."
+    )
+    # honesty gate: nothing was refreshed, so neither category may be claimed (never a fabricated refresh).
+    assert "coverage" not in refreshed and "membership_timeline" not in refreshed, (
+        "a skipped (already-current) refresh must be honestly ABSENT from the reported categories; "
+        f"refreshed={refreshed}"
+    )
+
+
+# ==================================================================================================
+# TC-A2 — a genuinely STALE stamp must still refresh (no regression to the freshness the gate protects)
+# ==================================================================================================
+def test_stale_stamp_backfill_finalize_still_refreshes_coverage(
+    finalize_session, quiet_finalize, monkeypatch
+):
+    """TC-A2: the gate must skip ONLY redundant work. When the job actually landed a new snapshot date the
+    `dataset_version` moves, no row exists for the new stamp, and the finalize tail must still run the
+    canonical refresh exactly once and report BOTH categories — otherwise `/api/data` would serve a stale
+    coverage payload (and J-05's `aggregates_refreshed` would lose `membership_timeline`)."""
+    session, cfg = finalize_session
+    data_manager.refresh_coverage_snapshot(session, cfg)  # current for the ONE-run stamp
+
+    # this job landed a genuinely new snapshot date -> the narrow membership dataset version moves
+    session.add(_make_run(cfg, LATER_ASOF))
+    session.commit()
+    assert not data_manager._coverage_snapshot_is_current(session, cfg), (
+        "fixture precondition: a new snapshot date must stale the persisted stamp"
+    )
+
+    calls = _spy_uncached_coverage(monkeypatch)
+    prog = JobProgress(job_id="real-work-backfill", kind="backfill", start=ASOF, end=LATER_ASOF)
+    prog.new_snapshot_dates = [LATER_ASOF]
+
+    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    # exactly one CURRENT-stamp refresh, plus the per-date warm for the one new date (unchanged behavior)
+    assert LATER_ASOF in calls, (
+        f"the new snapshot date's own coverage row must still be computed; calls={calls}"
+    )
+    assert "coverage" in refreshed and "membership_timeline" in refreshed, (
+        f"a genuinely stale stamp must still refresh + report both categories; refreshed={refreshed}"
+    )
+    assert data_manager._coverage_snapshot_is_current(session, cfg), (
+        "after the finalize tail the persisted snapshot must be current again for the NEW stamp"
+    )
+
+
+# ==================================================================================================
+# TC-A3 (iter-46 AUDIT, B1) — a CLEAR-AND-RECREATE rebuild restores an IDENTICAL stamp, so the gate must
+# not be allowed to skip on it
+# ==================================================================================================
+def test_rebuild_that_restores_an_identical_stamp_still_refreshes_coverage(
+    finalize_session, quiet_finalize, monkeypatch
+):
+    """TC-A3: the fix-pass rationale ("any job that actually landed a bar or a snapshot moves
+    `_membership_dataset_version`") does NOT hold for the J-85 clear-and-recreate rebuild.
+    `scanner_runs.id` is a plain `INTEGER PRIMARY KEY` (no `AUTOINCREMENT`, no `sqlite_sequence` row), so
+    clearing every run and recomputing the SAME date set restores the SAME `max(id)` and `count(*)`; with
+    the bars untouched the stamp is byte-identical before and after. A rebuild whose whole documented
+    purpose is to pick up a universe expansion — a change the NARROW membership stamp does not encode —
+    would then skip its coverage refresh, leave `/api/data` serving the pre-rebuild payload while
+    `coverage_status` still reports it fresh, and drop `coverage`/`membership_timeline` from the field
+    J-05 asserts on.
+
+    The gate therefore also requires `new_snapshot_dates == []` — the zero-work case it exists for."""
+    session, cfg = finalize_session
+    data_manager.refresh_coverage_snapshot(session, cfg)
+    stamp_before = research._membership_dataset_version(session, cfg)
+
+    # the rebuild's clear-then-create-once cycle, reproduced exactly: drop every snapshot, then recompute
+    # the SAME date set. SQLite hands the recreated row the SAME id, so the stamp lands back where it was.
+    for run in session.exec(select(ScannerRun)).all():
+        session.delete(run)
+    session.commit()
+    session.add(_make_run(cfg, ASOF))
+    session.commit()
+
+    assert research._membership_dataset_version(session, cfg) == stamp_before, (
+        "fixture precondition: the clear-and-recreate cycle must restore the IDENTICAL stamp — this is "
+        "the exact blind spot the `_coverage_snapshot_is_current` gate has on its own"
+    )
+    assert data_manager._coverage_snapshot_is_current(session, cfg), (
+        "fixture precondition: with the stamp restored, the pre-rebuild row still reads as 'current'"
+    )
+
+    calls = _spy_uncached_coverage(monkeypatch)
+    prog = JobProgress(job_id="rebuild-same-stamp", kind="rebuild", start=ASOF, end=ASOF)
+    prog.new_snapshot_dates = [ASOF]  # a rebuild recreates every snapshot -> every date is 'new'
+
+    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    assert calls, (
+        "a rebuild that recreated snapshots must still recompute coverage even when the narrow stamp "
+        f"happens to be unchanged; `_compute_coverage_uncached` was reached {len(calls)} time(s)"
+    )
+    assert "coverage" in refreshed and "membership_timeline" in refreshed, (
+        f"a snapshot-creating job must report both categories honestly; refreshed={refreshed}"
+    )
```
