# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 10. Shown in full: 7.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (82 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/data_manager.py` (60 lines not shown)
- `apps/backend/tests/test_data_manager.py` (25 lines not shown)

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 3db3561..2450569 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -119,7 +119,12 @@ def data_overview(
         except scanner.AsOfError:
             resolved_asof = None  # graceful: descriptive coverage falls back to the latest stored date
     return {
-        "coverage": data_manager.compute_coverage(session, cfg, as_of=resolved_asof),
+        # ops-hardening iter-2 (J-05): served ONLY from the persisted `coverage_snapshot` row — never a
+        # live `compute_coverage` call on this request path (the whole-table bar-prefill OOM/hang source,
+        # iter-24 evidence). A genuinely missing row serves an honest "not yet computed" partial payload —
+        # never a 500/blank response. The row is written by the ingest finalize hook and the boot warm-up
+        # safety net (`app.engine.data_manager._refresh_ingest_aggregates` / `app.engine.warmup._run_warmup`).
+        "coverage": data_manager.coverage_from_storage(session, cfg, as_of=resolved_asof),
         "runs": data_manager.recent_runs(session, cfg),
         "sources": data_manager.compute_provider_availability(cfg),
         # J-92: the OPTIONAL FRED macro feed catalog + availability (env-detected; committed-seed coverage;
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index e187033..9f6b7cd 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -32,6 +32,7 @@ import ctypes.util
 import gc
 import hashlib
 import json
+import logging
 import os
 import threading
 import time
@@ -53,6 +54,7 @@ from app.data_providers.seed_provider import SeedProvider, symbol_to_filename
 from app.db import get_engine
 from app.engine import drift as drift_module
 from app.engine import forward_testing, scanner
+from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
 from app.engine.prices import attach_shared_cache, bar_cache, bars_asof, latest_data_date, prefilled_bar_cache
 from app.engine import universe_resolver
 from app.engine.universe_screen import (
@@ -62,6 +64,7 @@ from app.engine.universe_screen import (
     screen_reasons,
 )
 from app.models import (
+    CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
     ForwardReturn,
@@ -76,9 +79,13 @@ from app.models import (
 from app.engine.research import (
     _dataset_version,  # single-sourced cache stamp (J-72/J-87) — never duplicated
     _membership_dataset_version,  # J-100: the NARROW membership-cache stamp (no forward-return term)
+    event_study_cached,  # ops-hardening iter-2 (J-05): the ingest finalize hook warms one default hot key
+    subject_catalog,
 )
 from app.seed_loader import price_load_symbols
 
+logger = logging.getLogger("trendora.data_manager")
+
 # Injectable sleep (J-34): the chunked fetch's inter-request delay + 429 backoff call this. Tests pass
 # their own recorder so backoff/sleep add NO wall-clock (MEMORY: backend-test-suite-runtime).
 _sleep: Callable[[float], None] = time.sleep
@@ -888,6 +895,214 @@ def _compute_coverage_body(
     }
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-2 (J-05) — the coverage_snapshot persisted table. `GET /api/data` is served ONLY
+# from this table (never a live `compute_coverage`/`_compute_coverage_uncached` call on the request path
+# — that whole-table bar-prefill is the documented OOM/hang source, iter-24 evidence). The row is written
+# by the ingest finalize hook (`_refresh_ingest_aggregates`, below) and the boot warm-up safety net
+# (`app.engine.warmup._run_warmup`) — both reuse `_compute_coverage_uncached` verbatim, never a second
+# derivation of the coverage figure.
+# --------------------------------------------------------------------------------------------------
+def _coverage_not_yet_computed_payload(cfg: Config) -> dict:
+    """The honest 'not yet computed' coverage sentinel `coverage_from_storage` serves when no
+    `CoverageSnapshot` row exists yet for the resolved key (before the first ingest finalize hook or the
+    boot warm-up safety net has run). Issues ZERO database queries — only the committed-pool FILE read
+    (`read_pool`, the same file `pool_survivorship`/`_resolved_universe` already read) plus config reads —
+    so this fallback can never pay the whole-table bar-prefill cost the persisted snapshot exists to avoid
+    (AG-8). Every DB-derived figure is honestly zero/null/empty — the SAME shape
+    `_compute_coverage_uncached` already serves for a genuinely empty DB (never a fabricated value)."""
+    pool_count = len({row["symbol"] for row in read_pool()})
+    threshold = cfg.indicators.min_history_bars
+    filters = cfg.universe.filters
+    return {
+        "price_start": None,
+        "price_end": None,
+        "symbol_count": 0,
+        "universe_count": 0,
+        "universe_asof": None,
+        "candidate_pool_count": pool_count,
+        "candidate_universe_count": len(cfg.universe.symbols),
+        "snapshot_count": 0,
+        "snapshot_dates": [],
+        "trading_day_count": 0,
+        "gap_count": 0,
+        "gap_first": None,
+        "gap_last": None,
+        "gaps_preview": [],
+        "per_symbol": [],
+        "diagnostic": {
+            "threshold": threshold,
+            "no_history": [],
+            "thin": [],
+            "intra_series_gaps": [],
+            "affected_count": 0,
+        },
+        "universe_diagnostic": {
+            "asof": None,
+            "candidate_pool_count": pool_count,
+            "admitted_count": 0,
+            "excluded_total": 0,
+            "excluded": {reason: 0 for reason in universe_resolver.EXCLUSION_REASONS},
+            "thresholds": {
+                "min_history_bars": threshold,
+                "min_price": filters.min_price,
+                "min_dollar_vol": filters.min_dollar_vol,
+                "adv_window_days": filters.adv_window_days,
+                "max_staleness_days": filters.max_staleness_days,
+            },
+        },
+        "membership_timeline": {
+            "candidate_pool_count": pool_count,
+            "points": [],
+            "labels": {
+                "survivorship": pool_survivorship(),
+                "warmup": {
+                    "min_history_bars": threshold,
+                    "boundary_date": None,
+                    "label": (
+                        "Coverage has not been computed yet for this database — an ingest job or the "
+                        "background warm-up will populate it shortly."
+                    ),
+                },
+                "universe_relative": (
+                    "Breadth and walk-forward evidence are universe-relative. The dynamic point-in-time "
+                    "universe REDUCES survivorship versus the static current-membership universe (a "
+                    "30-bar name is never ranked against a 1000-bar peer), while residual pool-survivorship "
+                    "remains until a true point-in-time index-constituent feed is added."
+                ),
+            },
+        },
+        "absent_from_latest_snapshot": {
+            "absent_count": 0,
+            "absent_preview": [],
+            "latest_snapshot_date": None,
+            "universe_count": 0,
+            "candidate_pool_count": pool_count,
+        },
+    }
+
+
+def _upsert_coverage_snapshot(
+    session: Session, asof_key: str, dataset_version: str, payload: dict
+) -> None:
+    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: prunes any
+    STALE row for this `asof_key` (an older `dataset_version`), then updates the current-stamp row in
+    place if one already exists or inserts a fresh one. Mirrors `market_phase_cached`'s prune-stale-then-
+    write upsert, generalized to also cover a repeat call under the SAME stamp — this is called
+    unconditionally at the end of every successful ingest (not gated behind a cache-miss check, unlike the
+    `*_cached` read-through caches)."""
+    stale = session.exec(
+        select(CoverageSnapshot).where(
+            CoverageSnapshot.asof_key == asof_key,
+            CoverageSnapshot.dataset_version != dataset_version,
+        )
+    ).all()
+    for row in stale:
+        session.delete(row)
+
+    existing = session.exec(
+        select(CoverageSnapshot).where(
+            CoverageSnapshot.asof_key == asof_key,
+            CoverageSnapshot.dataset_version == dataset_version,
+        )
+    ).first()
+    now = datetime.now(timezone.utc)
+    if existing is not None:
+        existing.payload_json = json.dumps(payload)
+        existing.computed_at = now
+        session.add(existing)
+    else:
+        session.add(CoverageSnapshot(
+            asof_key=asof_key, dataset_version=dataset_version,
+            payload_json=json.dumps(payload), computed_at=now,
+        ))
+    try:
+        session.commit()
+    except Exception:  # a concurrent writer raced us to the same key — best-effort, not a source of truth
+        session.rollback()
+
+
+def refresh_coverage_snapshot_for(session: Session, cfg: Config, resolved_asof: date_cls) -> dict:
+    """Compute + persist the `CoverageSnapshot` row for ONE SPECIFIC already-resolved as-of date (reusing
+    the canonical `_compute_coverage_uncached` verbatim — byte-identical to a fresh compute FOR THAT as-of,
+    never a second derivation). Shared by `refresh_coverage_snapshot` (the current stamp), the ingest
+    finalize hook's per-date warm loop (`_persist_per_date_coverage_snapshots`), and `coverage_from_storage`'s
+    read-path safety net for an already-ingested HISTORICAL as-of that predates this table. Returns the
+    freshly persisted payload."""
+    asof_key = resolved_asof.isoformat()
+    dataset_version = _membership_dataset_version(session, cfg)
+    # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls `membership_timeline_cached`
+    # internally as part of computing this SAME payload — warming that cache is a free side effect of this
+    # one call, never a second derivation.
+    payload = _compute_coverage_uncached(session, cfg, as_of=resolved_asof)
+    _upsert_coverage_snapshot(session, asof_key, dataset_version, payload)
+    return payload
+
+
+def refresh_coverage_snapshot(session: Session, cfg: Config) -> Optional[dict]:
+    """Compute the CURRENT coverage payload (reusing the canonical `_compute_coverage_uncached` verbatim —
+    never a second derivation) and persist it as the `CoverageSnapshot` row for the CURRENT `(asof_key,
+    dataset_version)` key, upserting idempotently. Called by the ingest finalize hook (unconditionally, on
+    every successful backfill/both/rebuild — including a zero-work re-run) and the boot warm-up safety net
+    (only when no row exists yet for the current stamp). Returns the freshly persisted payload, or `None`
+    on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns None only then; nothing to
+    snapshot yet). The current stamp resolves `None`→latest, so this is `refresh_coverage_snapshot_for` at
+    that resolved date (byte-identical: `_compute_coverage_uncached(as_of=None)` and `(as_of=latest)` both
+    resolve through `_resolve_coverage_asof` to the SAME latest date)."""
+    resolved_asof = _resolve_coverage_asof(session, None, cfg)
+    if resolved_asof is None:
+        return None
+    return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
+
+
+def _scanner_run_exists(session: Session, asof: date_cls) -> bool:
+    """Whether a real `ScannerRun` snapshot exists for exactly this as-of date — the signal that `asof` is
+    genuinely-ingested historical data (the app-wide as-of switcher, `GET /api/runs`, only ever offers such
+    dates), not a dataless/pre-ingest as-of that must honestly serve the 'not yet computed' sentinel."""
+    return session.exec(
+        select(ScannerRun.asof_date).where(ScannerRun.asof_date == asof).limit(1)
+    ).first() is not None
+
+
+def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date_cls] = None) -> dict:
+    """`GET /api/data`'s coverage block, served from the persisted `CoverageSnapshot` row for the resolved
+    `(asof_key, dataset_version)` key — REPLACES the former request-path call to `compute_coverage`/
+    `_compute_coverage_uncached` (the whole-table bar-prefill OOM/hang source, iter-24 evidence —
+    `compute_coverage` itself is UNCHANGED and still used directly by the ingest finalize hook / boot
+    warm-up safety net / tests that want a genuine live compute).
+
+    Explicit-historical-as-of safety net (iter-2 review, CRITICAL): the ingest finalize hook persists a row
+    for EVERY newly-created snapshot date, so the app-wide as-of switcher normally reads every selectable
+    date straight from storage. If a row is nonetheless missing for an EXPLICIT `as_of` (the switcher
+    selected a date — `data_overview` passes `None` for the default latest-date visit, a concrete date only
+    for an explicit `?as_of=`) that is backed by a REAL `ScannerRun` (an already-ingested historical date,
+    e.g. one ingested BEFORE this table existed), serve the CORRECT coverage for that date — computed once
+    and persisted so the next visit is instant (self-healing) — rather than the false all-zero sentinel.
+    This is an AG-3 correctness guarantee (displayed numbers MUST match the engine's computation) that
+    overrides the AG-8 no-request-compute preference for this rare, deliberate, one-time-per-date path.
+
+    The common default (`as_of=None`) visit and a genuinely dataless as-of (no `ScannerRun`, e.g. pre-first-
+    ingest) still take the honest zero-query 'not yet computed' sentinel — NEVER a live whole-table compute,
+    never a blank/500 response (AG-8)."""
+    resolved_asof = _resolve_coverage_asof(session, as_of, cfg)
+    if resolved_asof is not None:
+        asof_key = resolved_asof.isoformat()
+        dataset_version = _membership_dataset_version(session, cfg)
+        row = session.exec(
+            select(CoverageSnapshot).where(
+                CoverageSnapshot.asof_key == asof_key,
+                CoverageSnapshot.dataset_version == dataset_version,
+            )
+        ).first()
+        if row is not None:
+            return json.loads(row.payload_json)
+        # no persisted row: heal an explicit switcher selection of a real already-ingested historical date
+        # (see docstring) — real coverage, self-healed to storage — rather than a false empty-DB sentinel.
+        if as_of is not None and _scanner_run_exists(session, resolved_asof):
+            return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
+    return _coverage_not_yet_computed_payload(cfg)
+
+
 def compute_availability(session: Session, config: Optional[Config] = None) -> dict:
     """J-61 — the per-trading-date availability derivation. READ-ONLY descriptive metadata over the
     SAME stored bars + stored runs `compute_coverage` reads (never a second derivation of a coverage
@@ -1637,6 +1852,17 @@ class JobProgress:
     non_trading_days: int = 0
     already_snapshotted: int = 0
     error_other: int = 0
+    # ops-hardening iter-2 (J-05) — the ingest finalize hook's inputs/output. `new_snapshot_dates` is
+    # INTERNAL scratch (not serialized, like `_backfill_per_date_seconds_sum` below): the dates THIS run's
+    # `_do_backfill` genuinely persisted a NEW `ScannerRun` for (populated in `_persist()` exactly where it
+    # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
+    # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
+    # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
+    # "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` it actually refreshed —
+    # empty/default until the hook has actually run (never fabricated on an interrupted/failed row; gated
+    # in `_run_detail()` the SAME way `calendar_days` etc. already are).
+    new_snapshot_dates: list[date_cls] = field(default_factory=list)
+    aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
     # checkpoint's resume point); `chunk_total` = the deterministic plan size (symbol-batches × date-
     # windows). Both 0 for a non-chunked job (e.g. backfill-only) so the UI hides the chunk indicator.
@@ -1786,6 +2012,10 @@ class JobProgress:
             "non_trading_days": self.non_trading_days,
             "already_snapshotted": self.already_snapshotted,
             "error_other": self.error_other,
+            # ops-hardening iter-2 (J-05): the live job's finalize-hook output so far — empty while running/
+            # before the hook has run (honest; never fabricated), populated once the finalize hook completes
+            # (mirrors how the OTHER live fields above simply read the current in-memory value).
+            "aggregates_refreshed": list(self.aggregates_refreshed),
             "chunk_index": self.chunk_index,  # J-34: completed chunks (== checkpoint resume point)
             "chunk_total": self.chunk_total,  # J-34: total planned chunks
             "passers": self.passers,  # J-35: candidates that passed the screen (became members)
@@ -2632,6 +2862,11 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
         prog.forward_returns_inserted += result["rows_inserted"]
         prog.dates_done += 1
         prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
+        # ops-hardening iter-2 (J-05): record every date THIS call genuinely created a NEW snapshot for
+        # (never one that already existed — a rare inter-job race, see `existed_before` above) so the
+        # ingest finalize hook knows exactly which as-ofs to warm in `MarketPhaseCache`.
+        if not existed_before:
+            prog.new_snapshot_dates.append(d)
 
     def _persist_isolated(d: date_cls, payload: Optional[dict], secs: float, compute_error: Optional[str]) -> None:
         """J-67 + J-68 — write ONE date with failure isolation: if the worker COMPUTE already failed
@@ -2733,6 +2968,105 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
     prog.error_other = prog.date_failures_total
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-2 (J-05) — the ingest finalize hook: reached at the end of a successful
+# backfill/both/rebuild job (`_run_job`, below). Persists a fresh coverage_snapshot, warms
+# MarketPhaseCache for each snapshot date this run newly created, and warms one default EventStudyCache
+# hot key — reusing each cache's existing compute function, never a second derivation of any of them.
+# --------------------------------------------------------------------------------------------------
+def _persist_per_date_coverage_snapshots(
+    session: Session, cfg: Config, dates: list[date_cls]
+) -> None:
+    """Persist a byte-identical `CoverageSnapshot` row for each as-of in `dates` (the snapshot dates a
+    backfill NEWLY created), so the app-wide as-of switcher serves REAL coverage for each from storage —
+    never the all-zero 'not yet computed' sentinel (the iter-2 review's CRITICAL AG-3 regression: only the
+    single current stamp was persisted, so every OTHER already-ingested date read as an empty DB).
+
+    The CURRENT resolved as-of is skipped (already persisted by `refresh_coverage_snapshot`), so the common
+    single-latest-date backfill filters to nothing and pays NO bar-cache load at all. When there IS extra
+    work, ONE shared, re-entrant `prefilled_bar_cache` covers the whole loop — the whole-table bar scan runs
+    at most once regardless of date count (each per-date `_compute_coverage_uncached` reuses it), so warming
+    N dates costs one load, not N. Each row equals a fresh `_compute_coverage_uncached(as_of=d)`. Per-date
+    isolation (log + continue) so one date's failure never drops the rest; the caller wraps this whole call
+    non-fatally too. Reads only committed bars (backfill adds none), writes only `CoverageSnapshot` rows —
+    so the shared cache never serves a stale series (AG-8: no unbounded request-path load; this is ingest)."""
+    if not dates:
+        return
+    current = _resolve_coverage_asof(session, None, cfg)
+    todo = [d for d in dates if d != current]
+    if not todo:
+        return  # the only newly-created date IS the current stamp (already persisted) — no extra load
+    pool_symbols = {row["symbol"] for row in read_pool()}
+    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
+        for d in todo:
+            try:
+                refresh_coverage_snapshot_for(session, cfg, d)
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
+                logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
+
+
+def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress) -> list[str]:
+    """The ingest finalize hook (J-05). Each aggregate is refreshed independently (its own try/except: log
+    + continue) so one aggregate's failure never prevents another from refreshing, and this function itself
+    never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
+    `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
+    flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
+    "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` ACTUALLY refreshed — never a
+    fabricated category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this
+    module)."""
+    refreshed: list[str] = []
+
+    if prog.new_snapshot_dates:
+        # this run's own date-loop already created + committed these snapshots (scanner.persist_run_payload
+        # / run_scan, inside `_do_backfill._persist`) before this hook runs — nothing further to compute
+        # here; just acknowledge honestly that a fresh snapshot now exists.
+        refreshed.append("latest_snapshot")
+
+    try:
+        payload = refresh_coverage_snapshot(session, cfg)
+        if payload is not None:
+            refreshed.append("coverage")
+            # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
+            # `membership_timeline_cached` internally as part of computing the payload just persisted above
+            # — warmed for free by that SAME call, never a second/separate derivation.
+            refreshed.append("membership_timeline")
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
+
+    # iter-2 review (CRITICAL): also persist a per-date coverage_snapshot for every date THIS run newly
+    # created, so the app-wide as-of switcher serves REAL coverage for each historical date from storage —
+    # not the all-zero "not yet computed" sentinel. Still the "coverage" category (no new one); own
+    # try/except (log + continue) so it never flips the job. Skips the current stamp (persisted above) and
+    # is a no-op — no bar-cache load — for the common single-latest-date backfill.
+    try:
+        _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates)
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)
+
+    market_phase_warmed = False
+    for d in prog.new_snapshot_dates:
+        try:
+            market_phase.market_phase_cached(session, d, cfg)
+            market_phase_warmed = True
+        except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
+            logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
+    if market_phase_warmed:
+        refreshed.append("market_phase")
+
+    try:
+        subjects = subject_catalog(cfg)
+        if subjects:
+            # the SAME default (first catalog subject, config default_horizon, episodes view, all-history)
+            # a fresh `/research/event-study` page load with no query params would request — the one hot
+            # key worth warming at ingest (goal.md: "warm default (subject,horizon,all-history) keys").
+            event_study_cached(session, subjects[0]["key"], cfg.walk_forward.default_horizon, cfg)
+            refreshed.append("research_hot_keys")
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
+        logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)
+
+    return refreshed
+
... [diff_bound] apps/backend/app/engine/data_manager.py: 60 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index d9d8189..61c3b21 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -119,6 +119,36 @@ def _warm_membership_timeline(engine: Engine, cfg: Config) -> None:
         logger.exception("membership-timeline cache warm failed (non-fatal): %s", exc)
 
 
+def _warm_coverage_snapshot(engine: Engine, cfg: Config) -> None:
+    """ops-hardening iter-2 (J-05): the boot-time safety net for a not-yet-ingested-once database — persist
+    a `CoverageSnapshot` row for the CURRENT `(asof_key, dataset_version)` stamp ONLY IF no row exists yet
+    for it. Mirrors `_warm_membership_timeline`'s exact contract: opens its OWN session on `engine` (never a
+    request session), is idempotent (a no-op when a row already exists — this is a bootstrap safety net,
+    not a per-boot refresh; the ingest finalize hook is what keeps it fresh thereafter), and is NON-FATAL
+    (any exception is caught + logged here so a coverage-warm failure never aborts the otherwise-successful
+    warm-up). Reads the committed bars/runs only; computes no canonical value — it reuses
+    `data_manager.refresh_coverage_snapshot`, which itself reuses `_compute_coverage_uncached` verbatim."""
+    try:
+        with Session(engine) as session:
+            resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+            if resolved_asof is None:
+                return  # wholly empty DB (no bars at all) — nothing to snapshot yet
+            asof_key = resolved_asof.isoformat()
+            dataset_version = data_manager._membership_dataset_version(session, cfg)
+            existing = session.exec(
+                select(data_manager.CoverageSnapshot).where(
+                    data_manager.CoverageSnapshot.asof_key == asof_key,
+                    data_manager.CoverageSnapshot.dataset_version == dataset_version,
+                )
+            ).first()
+            if existing is not None:
+                return  # already computed under the current stamp — idempotent no-op
+            data_manager.refresh_coverage_snapshot(session, cfg)
+            logger.info("coverage snapshot warmed (asof=%s)", asof_key)
+    except Exception as exc:  # NON-FATAL: a coverage-snapshot warm failure must not fail the whole warm-up
+        logger.exception("coverage snapshot warm failed (non-fatal): %s", exc)
+
+
 def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -> None:
     """The warm-up worker body (runs in the daemon thread). Persists each remaining cadence snapshot via
     the canonical `run_scan` (batched by `config.startup.warmup_batch_size` for progress ticks), then runs
@@ -174,6 +204,12 @@ def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -
         # is logged but does NOT flip an otherwise-successful warm-up to `failed` (the cadence snapshots +
         # forward returns already succeeded; a cold `GET /api/data` still serves the bounded miss).
         _warm_membership_timeline(engine, cfg)
+        # ops-hardening iter-2 (J-05): the coverage_snapshot boot-time safety net — own guard, own session,
+        # non-fatal, idempotent (no-op once a row exists) — so a not-yet-ingested-once DB still has a
+        # coverage_snapshot row before the first `GET /api/data` request, without the boot path itself
+        # gaining any new synchronous compute (this step runs strictly in this background warm-up thread,
+        # after `yield`).
+        _warm_coverage_snapshot(engine, cfg)
         prog.status = "ok"
         prog.message = f"history {prog.dates_total}/{prog.dates_total}"
     except Exception as exc:  # NON-FATAL: caught + logged, never re-raised out of the thread
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 3a19595..f09fc15 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -590,6 +590,57 @@ class MembershipTimelineCache(SQLModel, table=True):
     created_at: datetime
 
 
+# --- ops-hardening iter-2 (J-05) coverage derived-aggregate snapshot (a PERFORMANCE cache, not a
+# snapshot) -----------------------------------------------------------------------------------
+class CoverageSnapshot(SQLModel, table=True):
+    """A STANDALONE, create_all-managed persisted snapshot of `GET /api/data`'s coverage block
+    (`app.engine.data_manager._compute_coverage_uncached`).
+
+    Like `EventStudyCache` / `MarketPhaseCache` / `MembershipTimelineCache`, this is EXPLICITLY NOT a
+    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
+    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache state:
+    it stores the SERIALIZED `_compute_coverage_uncached(...)` payload (byte-identical to a fresh compute
+    — a cache of the deterministic read-only derivation, never a second computation or a hand-authored
+    value) keyed by the resolved as-of + a dataset-version stamp, so `GET /api/data` serves the stored
+    aggregate instead of recomputing it on the request path (No recompute in the read path).
+
+    WHY: `_compute_coverage_uncached` wraps the whole derivation in one shared `prefilled_bar_cache`
+    (a one-time whole-universe bar load) so a cold `/api/data` request paid this cost synchronously on
+    the request path — the documented OOM/hang source (iter-24 evidence). This table moves that compute
+    to the ingest finalize hook (`app.engine.data_manager._run_job`, on a successful backfill/both/rebuild)
+    and a boot-time warm-up safety net (`app.engine.warmup._run_warmup`), so the request path only ever
+    reads a stored row (or serves an honest "not yet computed" sentinel — never a live whole-table
+    compute on that path).
+
+    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
+    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
+    existing table gains a column.
+
+    CACHE KEY: `(asof_key, dataset_version)`:
+      - `asof_key` is the resolved as-of cutoff ISO date — the SAME value `_coverage_cache_key` already
+        computes for the in-process single-flight cache (`_resolve_coverage_asof`).
+      - `dataset_version` is the SAME narrow `_membership_dataset_version` stamp (J-100) the in-process
+        coverage cache and `MembershipTimelineCache` already key on (snapshot set + bars manifest +
+        `min_history_bars` — NOT the forward-return count), so this row refreshes exactly when a real
+        membership/bars change could change the served coverage, and is reused across the warm-up's
+        forward-return churn.
+
+    `payload_json` is the full serialized `_compute_coverage_uncached(...)` derivation (byte-identical to
+    a fresh compute); `computed_at` is bookkeeping/audit only (no freshness indicator is rendered this
+    iteration). Unique on the composite key so a write is an idempotent upsert."""
+
+    __tablename__ = "coverage_snapshot"
+    __table_args__ = (
+        UniqueConstraint("asof_key", "dataset_version", name="uq_coverage_snapshot_key"),
+    )
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    asof_key: str = Field(index=True)  # resolved as-of ISO cutoff date (matches _coverage_cache_key)
+    dataset_version: str  # the SAME narrow stamp _membership_dataset_version produces
+    payload_json: str  # the serialized _compute_coverage_uncached(...) derivation (byte-identical)
+    computed_at: datetime  # UTC bookkeeping/audit timestamp — not rendered as a freshness indicator
+
+
 # --- iter-7 watchlist (USER-MUTABLE — the product's FIRST user-write surface; J-11) ----------
 class Watchlist(SQLModel, table=True):
     """One user-saved stock on the persistent research watchlist (iter-7). The product's FIRST
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index d6f87ff..10a1292 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -42,7 +42,14 @@ from app.models import DailyPrice, DataProviderRun, ImportCheckpoint
 def data_api_engine(tmp_path):
     """A tiny isolated DB (a few SPY bars so a trading calendar + latest date exist), set as the process
     engine for the duration of the test and restored afterward — so a job's appended DataProviderRun
-    row writes here, never to the shared `loaded_engine`."""
+    row writes here, never to the shared `loaded_engine`.
+
+    ops-hardening iter-2 (J-05): `GET /api/data`'s coverage block is now served ONLY from the persisted
+    `coverage_snapshot` row (never a live compute on the request path) — this fixture represents a DB that
+    has already been through an ingest, so it seeds that row here (via the SAME `refresh_coverage_snapshot`
+    the real ingest finalize hook / boot warm-up safety net use — never a second derivation), keeping
+    every existing coverage-shape assertion in this file reading the SAME live-equivalent numbers as
+    before this iteration."""
     prev = db_module._engine
     engine = make_engine(f"sqlite:///{tmp_path / 'data_api.db'}")
     create_db_and_tables(engine)
@@ -50,6 +57,8 @@ def data_api_engine(tmp_path):
         for d in (date(2024, 1, 2), date(2024, 1, 3)):
             session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
         session.commit()
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, get_config())
     db_module.set_engine(engine)
     yield engine
     db_module.set_engine(prev)
@@ -95,6 +104,68 @@ def test_get_data_overview_shape(data_api_engine):
         assert set(s) == {"id", "label", "needs_key", "env_var", "supports_market_cap", "available", "reason"}
 
 
+def test_get_data_overview_serves_coverage_from_storage_zero_prefill_calls(data_api_engine, monkeypatch):
+    """ops-hardening iter-2 (J-05 / TC-6 pytest-level proxy) — GET /api/data's coverage block is served
+    BYTE-IDENTICAL from the persisted `coverage_snapshot` row (seeded by the fixture, representing "already
+    ingested") with ZERO calls to `_compute_coverage_uncached`/`prefilled_bar_cache` on the request —
+    simulating "restart, then first request": a fresh session reading an already-ingested DB never pays a
+    live whole-table compute on this path (AG-8)."""
+    with Session(data_api_engine) as session:
+        cfg = get_config()
+        expected = data_manager._compute_coverage_uncached(session, cfg, as_of=None)  # ground truth
+
+    def _boom(*_a, **_k):
+        raise AssertionError("data_overview must never call this on the request path")
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _boom)
+    monkeypatch.setattr(data_manager, "prefilled_bar_cache", _boom)
+    with Session(data_api_engine) as session:
+        payload = data_overview(session=session)
+    assert payload["coverage"] == expected
+
+
+def test_get_data_overview_zero_coverage_rows_serves_honest_sentinel_never_500(tmp_path, monkeypatch):
+    """TC-9 — a database with zero `coverage_snapshot` rows (a simulated pre-ingest state; real bars ARE
+    present) still serves an honest all-zero/empty coverage block (never an exception, never a live
+    whole-table compute) — the API layer's 200-vs-500 status is FastAPI's own concern; what this proves is
+    that `data_overview` itself does not raise and does not call the whole-table-prefill path."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'no_snapshot_yet.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (date(2024, 1, 2), date(2024, 1, 3)):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+
+    def _boom(*_a, **_k):
+        raise AssertionError("must never call _compute_coverage_uncached when no coverage_snapshot row exists")
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _boom)
+    monkeypatch.setattr(data_manager, "prefilled_bar_cache", _boom)
+    with Session(engine) as session:
+        payload = data_overview(session=session)  # must not raise — never a 500/blank page
+    cov = payload["coverage"]
+    assert cov["symbol_count"] == 0  # honest sentinel — never a live-derived 1, despite real SPY bars
+    assert cov["snapshot_count"] == 0
+    assert cov["per_symbol"] == []
+    assert cov["universe_diagnostic"]["excluded"] == {
+        "below_history": 0, "stale_series": 0, "below_price": 0, "below_adv": 0,
+    }
+    assert cov["membership_timeline"]["points"] == []
+    assert cov["absent_from_latest_snapshot"]["absent_count"] == 0
+
+
+def test_get_data_overview_coverage_from_storage_empty_db_still_graceful(tmp_path):
+    """A wholly empty DB (no bars at all) also serves the honest sentinel gracefully — no crash on the
+    genuinely-empty-DB edge (`_resolve_coverage_asof` returns None; `coverage_from_storage` short-circuits
+    straight to the static sentinel)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'wholly_empty.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        payload = data_overview(session=session)
+    assert payload["coverage"]["symbol_count"] == 0
+    assert payload["coverage"]["price_start"] is None
+
+
 def test_get_data_overview_carries_capacity_snapshot(data_api_engine):
     """Item K (iter-24 fast-platform pass): GET /api/data carries an additive `capacity` key — the DB
     storage-footprint snapshot (file size + row counts for the three largest tables), exact on the tiny
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index e111fbd..4933157 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -17,6 +17,7 @@ backfill proof loads the committed seed and runs the real engines ONCE (module-s
 from __future__ import annotations
 
 import json
+import socket
 import time
 from datetime import date, datetime, timedelta
 from pathlib import Path
@@ -30,7 +31,7 @@ from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
 from app.engine import data_manager
-from app.engine import forward_testing, scanner
+from app.engine import forward_testing, market_phase, scanner
 from app.engine.data_manager import (
     JobProgress,
     _chunk_plan,
@@ -64,6 +65,7 @@ from app.engine.data_manager import (
 from app.engine.forward_testing import compute_forward_aggregates
 from app.engine.scoring import score_stocks
 from app.models import (
+    CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
     ForwardReturn,
@@ -1000,6 +1002,395 @@ def test_backfill_error_other_uncapped_past_sample_limit(backfilled_job, monkeyp
     assert prog.snapshots_created + prog.already_snapshotted + prog.error_other == prog.dates_total
 
 
+# ==================================================================================================
+# ops-hardening iter-2 (J-05): the ingest finalize hook — coverage_snapshot persistence, market-phase/
+# membership-timeline/research hot-key warming, and the aggregates_refreshed honesty gate.
+#
+# `finalize_hook_engine` is a TINY hand-built DB (mirrors `coverage_engine`'s own style) — fast, no full
+# seed load needed: the finalize hook's sub-steps (`_compute_coverage_uncached`, `market_phase_cached`,
+# `event_study_cached`) all degrade gracefully on sparse data (the SAME graceful-empty-DB behavior
+# `coverage_engine`'s own tests already exercise, since `read_pool()` always reads the REAL committed
+# candidate-pool file regardless of this tiny DB's contents).
+# ==================================================================================================
+@pytest.fixture()
+def finalize_hook_engine(tmp_path):
+    """A tiny hand-built DB with one stored ScannerRun + ScannerResult on a single as-of date — enough for
+    every finalize-hook sub-step to run for real."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 3, 4)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        run = ScannerRun(
+            asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.commit()
+        session.refresh(run)
+        session.add(ScannerResult(
+            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.commit()
+    return engine, d
+
+
+def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_hook_engine):
+    """TC-1/TC-5 — a finalize hook call for a job that newly created a snapshot on `d` persists exactly one
+    `coverage_snapshot` row for the current stamp and reports every category this fixture's data supports
+    as refreshed: `latest_snapshot` (this run created a snapshot), `coverage` + `membership_timeline` (one
+    compute warms both), `market_phase` (the new date), `research_hot_keys` (the default hot key)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="finalize-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert set(refreshed) == {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys",
+    }
+    with Session(engine) as session:
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1
+        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+        assert rows[0].asof_key == resolved_asof.isoformat()
+        assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)
+
+
+def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finalize_hook_engine):
+    """TC-8 — the persisted payload_json is byte-identical (field-by-field) to a direct fresh
+    `_compute_coverage_uncached` call for the same session state (AG-3: storage is re-served, never
+    re-derived)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="byte-identity-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    with Session(engine) as session:
+        row = session.exec(select(CoverageSnapshot)).one()
+        stored = json.loads(row.payload_json)
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+    assert stored == fresh
+
+
+def test_finalize_hook_market_phase_computed_exactly_once_not_on_subsequent_read(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-4 — `compute_market_phase` executes exactly once per newly-created date, during the finalize
+    hook; a subsequent read of the SAME as-of serves from `MarketPhaseCache` (zero further compute calls)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    calls: list[int] = []
+    orig = market_phase.compute_market_phase
+
+    def _counting(*args, **kwargs):
+        calls.append(1)
+        return orig(*args, **kwargs)
+
+    monkeypatch.setattr(market_phase, "compute_market_phase", _counting)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="market-phase-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert len(calls) == 1, "compute_market_phase should run exactly once, during the finalize hook"
+
+    # a subsequent read of the SAME as-of must serve from the cache — zero additional compute calls.
+    with Session(engine) as session:
+        market_phase.market_phase_cached(session, d, cfg)
+    assert len(calls) == 1, "a subsequent read must serve from MarketPhaseCache, not recompute"
+
+
+def test_finalize_hook_only_warms_market_phase_for_newly_created_dates(finalize_hook_engine):
+    """A finalize hook call with an EMPTY `new_snapshot_dates` (e.g. a zero-work re-run) warms neither
+    `market_phase` nor `latest_snapshot` — never a fabricated category for work that did not happen —
+    while `coverage`/`membership_timeline`/`research_hot_keys` still refresh unconditionally."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="zero-work-probe", kind="backfill", start=d, end=d)
+        # prog.new_snapshot_dates deliberately left empty — simulates a zero-work re-run.
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "market_phase" not in refreshed
+    assert "latest_snapshot" not in refreshed
+    assert {"coverage", "membership_timeline", "research_hot_keys"} <= set(refreshed)
+
+
+def test_finalize_hook_partial_failure_isolated_other_aggregates_still_refresh(
+    finalize_hook_engine, monkeypatch
+):
+    """A single aggregate's failure (research hot-key warm, forced) does not prevent the OTHERS
+    (`latest_snapshot`/`coverage`/`membership_timeline`/`market_phase`) from refreshing — log + continue,
+    never raise (mirrors `_warm_membership_timeline`'s non-fatal contract)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced research hot-key failure")
+
+    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="partial-failure-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "research_hot_keys" not in refreshed
+    assert {"latest_snapshot", "coverage", "membership_timeline", "market_phase"} <= set(refreshed)
+
+
+def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_engine, monkeypatch):
+    """The finalize hook never raises even when EVERY compute-based sub-step fails (only the
+    zero-compute `latest_snapshot` acknowledgment survives) — `_run_job`'s own call site additionally
+    wraps this call, but the function itself is designed to never propagate."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced failure")
+
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _boom)
+    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
+    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert refreshed == ["latest_snapshot"]
+
+
+def test_finalize_hook_makes_no_network_call(finalize_hook_engine, monkeypatch):
+    """AG-9 / TC-19 — the finalize hook's aggregate-refresh calls issue ZERO outbound network calls (every
+    reused compute function is a pure DB-backed derivation, never a live provider)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _no_network(*_a, **_k):
+        raise AssertionError("unexpected network call during the ingest finalize hook")
+
+    monkeypatch.setattr(socket.socket, "connect", _no_network)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="no-network-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert refreshed  # completed successfully with zero socket.connect calls
+
+
+def test_run_detail_omits_aggregates_refreshed_until_computed():
+    """TC-13/TC-14 — mirrors `test_run_detail_omits_breakdown_until_computed`: a not-yet-computed (fresh,
+    `_create_run_record`-time) backfill row serves `aggregates_refreshed` null; an INTERRUPTED row whose
+    finalize hook never ran also serves null (the breakdown fields ARE computed — the date-loop ran — but
+    `aggregates_refreshed` stays at its empty JobProgress default, never a fabricated list — TC-13); a
+    fetch/expand row serves null unconditionally (`_breakdown_computed` is always False for those kinds —
+    TC-14); a genuinely computed row serves its real list."""
+    fresh = JobProgress(job_id="never-ran", kind="backfill", start=date(2024, 1, 1), end=date(2025, 6, 1))
+    assert data_manager._run_detail(fresh)["aggregates_refreshed"] is None
+
+    # TC-13: interrupted between the date-loop and the finalize hook — calendar_days IS computed (the
+    # date-loop ran and set it), but aggregates_refreshed stays empty (the hook never ran).
+    interrupted = JobProgress(
+        job_id="interrupted", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29)
+    )
+    interrupted.calendar_days, interrupted.dates_total, interrupted.non_trading_days = 28, 19, 9
+    interrupted.already_snapshotted, interrupted.snapshots_created, interrupted.error_other = 0, 19, 0
+    assert data_manager._run_detail(interrupted)["aggregates_refreshed"] is None
+
+    # TC-14: a fetch kind never routes through the finalize hook — null regardless of any (hypothetical,
+    # impossible-in-practice) populated field, since `_breakdown_computed` is always False for this kind.
+    fetch_kind = JobProgress(job_id="fetch-kind", kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 1))
+    fetch_kind.aggregates_refreshed = ["coverage"]
+    assert data_manager._run_detail(fetch_kind)["aggregates_refreshed"] is None
+
+    done = JobProgress(job_id="ran", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29))
+    done.calendar_days, done.dates_total, done.non_trading_days = 28, 19, 9
+    done.already_snapshotted, done.snapshots_created, done.error_other = 0, 19, 0
+    done.aggregates_refreshed = ["coverage", "market_phase"]
+    assert data_manager._run_detail(done)["aggregates_refreshed"] == ["coverage", "market_phase"]
+
+
+def test_do_backfill_new_snapshot_dates_tracks_genuinely_new_dates_only(backfilled_job):
+    """ops-hardening iter-2 (J-05) — `_persist` populates `prog.new_snapshot_dates` with exactly the dates
+    THIS call genuinely created a NEW snapshot for (never a date that already existed) — the finalize
+    hook's input for which as-ofs to warm in `MarketPhaseCache`. A fresh single-date window (re-queried
+    live, so this is safe regardless of what other tests in this module already touched) proves the
+    fresh-create case; re-running the SAME date proves the already-exists case records nothing new."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in trading if d not in snapshotted)
+
+    prog = JobProgress(job_id="new-snapshot-dates-probe", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog, eng=engine)
+    assert prog.new_snapshot_dates == [fresh_date]
+    assert prog.snapshots_created == 1
+
+    # re-run the SAME date: it already exists now -> nothing new is recorded.
+    prog2 = JobProgress(job_id="new-snapshot-dates-probe-2", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog2, eng=engine)
+    assert prog2.new_snapshot_dates == []
+    assert prog2.snapshots_created == 0
+    assert prog2.already_snapshotted == 1
+
+
+def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job):
+    """ops-hardening iter-2 (J-05) end-to-end: a real backfill job dispatched through `run_data_job` (the
+    SAME path the API uses) reaches the finalize hook, persists a `coverage_snapshot` row, and the job's
+    final summary (the SAME dict `GET /api/data/jobs/{id}` serves) carries a non-empty
+    `aggregates_refreshed`. Searches from the LATEST end of the trading calendar (the other new-date test
+    above searches from the earliest) so the two never contend for the same fresh date."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in reversed(trading) if d not in snapshotted)
+
+    job = create_job("backfill", fresh_date, fresh_date)
+    summary = run_data_job(job.job_id, config=cfg, engine=engine)
+    assert summary["status"] == "ok"
+    assert set(summary["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}
+
+    with Session(engine) as session:
+        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+        version = data_manager._membership_dataset_version(session, cfg)
+        row = session.exec(
+            select(CoverageSnapshot).where(
+                CoverageSnapshot.asof_key == resolved_asof.isoformat(),
+                CoverageSnapshot.dataset_version == version,
+            )
+        ).first()
+        assert row is not None
+
+    # the SAME dict shape GET /api/data's `runs` list serves (`recent_runs` -> `_run_detail` for the
+    # persisted row) also carries the finalize hook's output — one computation, two servings.
+    with Session(engine) as session:
+        persisted = recent_runs(session, cfg)
+    this_run = next(r for r in persisted if r["kind"] == "backfill" and r["start"] == fresh_date.isoformat())
+    assert set(this_run["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}
+
+
+def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
+    """TC-14 — a completed `fetch` run's persisted detail always carries `aggregates_refreshed: null` (the
+    finalize hook is gated to backfill/both/rebuild-like kinds only in `_run_job`; a fetch never reaches
+    it)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_only.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+    cfg = load_config()
+
+    class _EmptyProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return []  # a successful fetch that finds no new bars — never a fabricated one
+
+    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_EmptyProvider(), sleep_fn=_noop_sleep,
+        seed_dir=tmp_path,
+    )
+    assert summary["aggregates_refreshed"] == []  # the live in-memory default (never populated for fetch)
+    with Session(engine) as session:
+        persisted = recent_runs(session, cfg)
+    this_run = next(r for r in persisted if r["kind"] == "fetch")
+    assert this_run["aggregates_refreshed"] is None  # the persisted/served view: null for a fetch kind
+
+
+# ==================================================================================================
+# iter-2 review (CRITICAL regression): the app-wide as-of switcher (J-93/J-94) must serve REAL coverage
+# for EVERY already-ingested date — not just the DB's single current stamp. Before the fix, only the
+# current stamp got a coverage_snapshot row, so any OTHER selectable historical date read as an all-zero
+# empty-DB sentinel (an AG-3 violation on the shipped switcher). Two layers close it: (1) the ingest
+# finalize hook persists a per-date row for every NEWLY-created date; (2) coverage_from_storage self-heals
+# an explicit historical selection that has a real ScannerRun but no row (a legacy pre-table date).
+# ==================================================================================================
+@pytest.fixture()
+def two_snapshot_dates_engine(tmp_path):
+    """A tiny DB with TWO stored ScannerRun/ScannerResult dates (an older historical date + a newer/latest
+    date), each with one priced bar — enough to prove per-date coverage differs from the current stamp."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'two_dates.db'}")
+    create_db_and_tables(engine)
+    d_old, d_new = date(2024, 3, 1), date(2024, 3, 4)
+    with Session(engine) as session:
+        for d in (d_old, d_new):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        for d in (d_old, d_new):
+            run = ScannerRun(
+                asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.commit()
+            session.refresh(run)
+            session.add(ScannerResult(
+                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+                setup_status="Actionable", rank=1, record_json="{}",
+            ))
+            session.commit()
+    return engine, d_old, d_new
+
+
+def test_finalize_hook_persists_per_date_coverage_for_historical_switcher_date(two_snapshot_dates_engine):
+    """iter-2 review fix, layer 1 — a backfill that newly created a NON-latest (historical) snapshot date
+    persists a per-date coverage_snapshot for it, so coverage_from_storage serves REAL coverage for that
+    date (byte-identical to a fresh compute-at-that-date; AG-3) — never the all-zero sentinel. The CURRENT
+    stamp row is unaffected, and there are now exactly two rows (old + latest), not one."""
+    engine, d_old, d_new = two_snapshot_dates_engine
+    cfg = load_config()
+    # a backfill whose date-loop newly created the OLDER (historical, non-latest) date
+    with Session(engine) as session:
+        prog = JobProgress(job_id="hist-per-date-probe", kind="backfill", start=d_old, end=d_old)
+        prog.new_snapshot_dates = [d_old]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    with Session(engine) as session:
+        # the historical date is served from storage, byte-identical to a fresh compute-at-d_old...
+        cov_old = data_manager.coverage_from_storage(session, cfg, as_of=d_old)
+        fresh_old = data_manager._compute_coverage_uncached(session, cfg, as_of=d_old)
+        assert cov_old == fresh_old
+        assert cov_old["symbol_count"] == 1  # REAL coverage (the sentinel would be 0) — the regression
+        assert cov_old["universe_asof"] == d_old.isoformat()
+        # ...and the current/latest stamp is still served correctly too (two distinct rows now exist)
+        cov_new = data_manager.coverage_from_storage(session, cfg, as_of=d_new)
+        assert cov_new["universe_asof"] == d_new.isoformat()
+        assert len(session.exec(select(CoverageSnapshot)).all()) == 2
+
+
+def test_coverage_from_storage_self_heals_explicit_legacy_historical_asof(two_snapshot_dates_engine):
+    """iter-2 review fix, layer 2 — an EXPLICIT historical as-of backed by a real ScannerRun but with NO
+    persisted coverage_snapshot row (a legacy date ingested before this table existed) is served REAL
... [diff_bound] apps/backend/tests/test_data_manager.py: 25 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_warmup.py b/apps/backend/tests/test_warmup.py
index bb283a3..0b34d55 100644
--- a/apps/backend/tests/test_warmup.py
+++ b/apps/backend/tests/test_warmup.py
@@ -32,6 +32,7 @@ early as-of date (less history → faster) and never the latest.
 """
 from __future__ import annotations
 
+import json
 import threading
 from datetime import date
 
@@ -56,6 +57,7 @@ from app.engine.warmup import (
 from app.engine.data_manager import _membership_timeline, membership_timeline_cached
 from app.engine.research import _membership_dataset_version
 from app.models import (
+    CoverageSnapshot,
     ForwardReturn,
     MembershipTimelineCache,
     ScannerResult,
@@ -329,6 +331,80 @@ def test_membership_timeline_cache_warm_failure_is_nonfatal(early_engine, monkey
     warmup_mod._WARMUP_THREAD = None
 
 
+# ==================================================================================================
+# ops-hardening iter-2 (J-05) — the coverage_snapshot boot-time safety net: a not-yet-ingested-once DB
+# gets exactly one persisted coverage_snapshot row after the background warm-up finishes, computed
+# strictly in this background thread (never on the boot/request path), idempotent, and non-fatal.
+# ==================================================================================================
+def test_warmup_precomputes_coverage_snapshot_if_missing(warmed_engine):
+    """After the background warm-up finishes, a `CoverageSnapshot` row exists for the CURRENT (asof_key,
+    dataset_version) stamp — the boot-time safety net for a not-yet-ingested-once DB, run strictly in this
+    background warm-up thread (never blocking `yield`/serving). Byte-identical to a fresh
+    `_compute_coverage_uncached` compute (a cache of the deterministic derivation, not a second
+    computation)."""
+    engine, cfg = warmed_engine["engine"], warmed_engine["cfg"]
+    with Session(engine) as session:
+        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+        version = data_manager._membership_dataset_version(session, cfg)
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1, f"expected exactly one warmed coverage_snapshot row, got {len(rows)}"
+        assert rows[0].asof_key == resolved_asof.isoformat()
+        assert rows[0].dataset_version == version
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+        stored = json.loads(rows[0].payload_json)
+    assert stored == fresh
+
+
+def test_warmup_coverage_snapshot_is_noop_when_already_present(early_engine):
+    """The boot safety net is a no-op when a `coverage_snapshot` row already exists for the current stamp
+    — it does not recompute/overwrite on every boot; only the ingest finalize hook refreshes it
+    thereafter."""
+    engine, cfg = early_engine
+    ensure_latest_snapshot(engine, cfg)  # latest servable
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, cfg)  # seed one row directly (a prior ingest)
+        rows_before = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows_before) == 1
+        computed_at_before = rows_before[0].computed_at
+
+    warmup_mod._warm_coverage_snapshot(engine, cfg)  # the safety net — must see the row and no-op
+
+    with Session(engine) as session:
+        rows_after = session.exec(select(CoverageSnapshot)).all()
+    assert len(rows_after) == 1
+    assert rows_after[0].computed_at == computed_at_before  # untouched — no recompute
+
+
+def test_warmup_coverage_snapshot_warm_failure_is_nonfatal(early_engine, monkeypatch, caplog):
+    """A failure precomputing the coverage snapshot during warm-up is CAUGHT + logged and does NOT flip an
+    otherwise-successful warm-up to `failed` (mirrors
+    `test_membership_timeline_cache_warm_failure_is_nonfatal`)."""
+    engine, cfg = early_engine
+    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+
+    def _boom(*_args, **_kwargs):
+        raise RuntimeError("forced coverage snapshot warm failure")
+
+    monkeypatch.setattr(warmup_mod.data_manager, "refresh_coverage_snapshot", _boom)
+    with caplog.at_level("ERROR"):
+        job_id = start_warmup(engine, cfg)
+        _join_warmup(job_id)
+
+    rec = data_manager.get_job(job_id)
+    # the warm-up still settled OK (the coverage-warm failure is non-fatal — it did not fail the job).
+    assert rec is not None and rec["status"] == "ok"
+    assert any("coverage snapshot warm failed" in r.message.lower() for r in caplog.records)
+    # no stale/garbage row was written by the failed warm (the inner compute raised before persist).
+    with Session(engine) as session:
+        assert session.exec(select(CoverageSnapshot)).all() == []
+
+    monkeypatch.undo()
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+
+
 def test_lifespan_serves_dashboard_200_while_warmup_in_flight(tmp_path_factory, monkeypatch):
     """The J-40 keystone integration proof named verbatim in goal.md acceptance: the SERVER is serving —
     the lifespan has yielded, the latest snapshot is present, `GET /api/dashboard` returns 200 and the
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 78ee308..017d1ed 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -2366,6 +2366,11 @@ export interface DataRun {
   non_trading_days: number | null;
   already_snapshotted: number | null;
   error_other: number | null;
+  // ops-hardening iter-2 (J-05) — which downstream aggregates (coverage, latest snapshot, membership
+  // timeline, market phase, research hot-keys) this run's ingest finalize hook refreshed. null for a
+  // fetch/expand run and for a not-yet-computed/interrupted row (matches the calendar_days-style
+  // nullability convention above — never a fabricated list).
+  aggregates_refreshed: string[] | null;
   bars_fetched: number | null;
   passers: number | null; // J-35 expand screen outcome (null for non-expand runs)
   omitted_total: number | null; // J-35 expand screen outcome (null otherwise)
@@ -2581,6 +2586,9 @@ export interface DataJob {
   non_trading_days?: number;
   already_snapshotted?: number;
   error_other?: number;
+  // ops-hardening iter-2 (J-05): the live job's finalize-hook output so far — empty/absent while running
+  // or before the hook has run (honest; never fabricated), populated once the finalize hook completes.
+  aggregates_refreshed?: string[] | null;
   chunk_index?: number; // J-34: completed chunks (== checkpoint resume point)
   chunk_total?: number; // J-34: total planned chunks (chunk x/N); 0/absent for a non-chunked job
   passers?: number; // J-35 expand: candidates that passed the screen (became universe members)
diff --git a/incredible_auto_dev/scripts/start-backend.sh b/incredible_auto_dev/scripts/start-backend.sh
index ff31d48..58fb00a 100755
--- a/incredible_auto_dev/scripts/start-backend.sh
+++ b/incredible_auto_dev/scripts/start-backend.sh
@@ -28,7 +28,45 @@ if [[ -d alembic ]]; then
   "$REPO_ROOT/apps/backend/.venv/bin/alembic" upgrade head 2>/dev/null || true
 fi
 
+# ops-hardening iter-2 (J-04 remainder) — actually ENFORCE the declared memory cap + malloc-arena cap and
+# write a PERSISTENT boot logfile. goal.md's binding note: prior to this iteration none of these three were
+# enforced by this script at all (confirmed by a direct read: no ulimit, no env export, no logfile redirect
+# anywhere in it) — do not trust reports/perf-budgets.md's or config.yaml's prose claiming otherwise; this
+# is where the enforcement actually lives now. Values come from config.yaml via the venv Python (No magic
+# numbers — the same `app.config.get_config()` every engine reads).
+read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE <<< "$(
+  "$REPO_ROOT/apps/backend/.venv/bin/python" -c '
+from app.config import get_config
+cfg = get_config()
+print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
+'
+)"
+
+# ulimit -v is KiB; config.server.memory_cap_mb is MB. Set on THIS shell BEFORE exec — a ulimit is a
+# process attribute inherited across exec() (same PID, new program image), so the cap applies to the
+# uvicorn process itself, not just this launcher shell.
+ulimit -v $((MEMORY_CAP_MB * 1024))
+# iter-27 (anti-goal #8): bound how many independently-fragmenting malloc arenas glibc creates across the
+# uvicorn threadpool + parallel backfill workers (the dominant VSZ-fragmentation lever behind the
+# iter-26/iter-27 rebuild crash). Exported before exec so glibc reads it at the process's own startup.
+export MALLOC_ARENA_MAX="$MALLOC_ARENA_MAX_VALUE"
+
+# A PERSISTENT backend logfile (today uvicorn writes only to the launching terminal, lost the moment that
+# terminal closes or the process is backgrounded). One fixed, repo-relative path — `logs/` is already
+# gitignored — so a boot's log survives the launching shell and a crash test can read it afterward. Append
+# (not truncate) across restarts so a crash's abrupt ending stays visible in the SAME file the next boot's
+# lines are appended to (a real operational history, not a wiped-per-restart snapshot).
+LOG_DIR="$REPO_ROOT/logs"
+mkdir -p "$LOG_DIR"
+LOG_FILE="$LOG_DIR/backend.log"
+{
+  echo ""
+  echo "=== start-backend.sh: launching at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
+  echo "    port=$PORT memory_cap_mb=$MEMORY_CAP_MB malloc_arena_max=$MALLOC_ARENA_MAX_VALUE"
+} >> "$LOG_FILE"
+
 exec "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
   --host 0.0.0.0 \
   --port "$PORT" \
-  --app-dir "$REPO_ROOT/apps/backend"
+  --app-dir "$REPO_ROOT/apps/backend" \
+  >> "$LOG_FILE" 2>&1
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 95 ++++++++++++++++++++++
 runs/goal-session-mcp-loop/state/drift-report.json |  2 +-
 .../state/preflight-verdict-history.jsonl          |  1 +
 runs/goal-session-ops-hardening/telemetry.jsonl    | 11 +++
 runs/goal-session-ops-hardening/trace/.next-step   |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  5 ++
 6 files changed, 114 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
