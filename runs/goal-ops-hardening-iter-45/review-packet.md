# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 1.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/data_manager.py` (157 lines not shown)
- `apps/backend/tests/test_data_manager.py` (202 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index fee08896..59fcddee 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -36,6 +36,7 @@ import logging
 import os
 import threading
 import time
+import traceback
 import uuid
 from concurrent.futures import ThreadPoolExecutor, as_completed
 from contextlib import nullcontext
@@ -631,6 +632,159 @@ def _excluded_counts_by_date(
     return totals
 
 
+def _parse_membership_stamp(stamp: str) -> Optional[dict]:
+    """ops-hardening iter-45 AUDIT (B4) — decompose a `research._membership_dataset_version` stamp
+    (`r{max_run_id}-rc{run_count}-b{max_bar_date|none}-bc{bar_count}-h{min_history_bars}`) into its terms.
+    Parsed right-to-left so the ISO date in the `-b` slot (which itself contains `-`) is unambiguous.
+    Returns None on ANY unrecognized shape — every caller treats None as "cannot prove it is safe" and
+    falls back to the full recompute, so a future stamp-format change degrades to the pre-iter-45
+    behavior (slow but always correct), never to a silently wrong fast path."""
+    try:
+        head, sep_h, h_part = stamp.rpartition("-h")
+        head, sep_bc, bc_part = head.rpartition("-bc")
+        _, sep_b, b_part = head.rpartition("-b")
+        if not (sep_h and sep_bc and sep_b):
+            return None
+        return {
+            "min_history_bars": int(h_part),
+            "bar_count": int(bc_part),
+            "bar_stamp": b_part,
+        }
+    except (ValueError, AttributeError):
+        return None
+
+
+def _membership_bars_are_forward_only(
+    session: Session, prev_version: str, cur_version: str,
+) -> bool:
+    """ops-hardening iter-45 AUDIT (B4) — the missing half of the append-forward precondition.
+
+    `_membership_timeline_incremental` reuses every already-cached date's `excluded` counts verbatim. Those
+    counts come from `resolve_with_reasons(session, d, cfg)`, which reads BARS `<= d` and
+    `min_history_bars` — so they are only safe to reuse if NEITHER changed for any date `<= D_prev`. The
+    original iter-45 precondition checked the SNAPSHOT-DATE ordering only, which is sufficient for
+    `size`/`entries`/`exits` (pure membership) but NOT for `excluded`: `_membership_dataset_version` folds
+    in the bars manifest, so a `both` job whose FETCH stage lands bars at a historical date (a symbol's gap
+    backfill, a newly-added pool symbol's history) while its BACKFILL stage creates one new LATER snapshot
+    date satisfies "append-forward" on dates yet silently serves stale per-date `excluded` tallies —
+    violating both the phase spec's "byte-identical output required" and AG-3 ("displayed numbers match the
+    engine's computation for the same as-of date").
+
+    Sufficient condition proven here: `min_history_bars` is unchanged AND every bar added since the cached
+    payload was computed lies STRICTLY AFTER that payload's own `max(daily_prices.date)`. Since a snapshot
+    date can only exist where bars exist, that previous max bar date is `>= D_prev`, so no bar at or before
+    any already-cached date moved — and the resolver's verdict for those dates is unchanged. Fail-safe: any
+    unparsable stamp, any bar removal, or any net count that does not match the strictly-after population
+    returns False, sending the caller to the existing full recompute."""
+    prev = _parse_membership_stamp(prev_version)
+    cur = _parse_membership_stamp(cur_version)
+    if prev is None or cur is None:
+        return False
+    if prev["min_history_bars"] != cur["min_history_bars"]:
+        return False
+    if prev["bar_stamp"] == "none":
+        # No bars existed when the cached payload was computed, yet it may still carry snapshot dates
+        # (points). Any bar added now could therefore land at or before one of them — only a still-empty
+        # bars table is provably safe.
+        return cur["bar_count"] == 0
+    try:
+        prev_max_bar_date = date_cls.fromisoformat(prev["bar_stamp"])
+    except ValueError:
+        return False
+    bars_strictly_after = session.exec(
+        select(func.count()).select_from(DailyPrice).where(DailyPrice.date > prev_max_bar_date)
+    ).one()
+    if isinstance(bars_strictly_after, tuple):
+        bars_strictly_after = bars_strictly_after[0]
+    # At the previous compute this population was empty by definition (that date WAS the max), so a
+    # forward-only bar change moves the total by exactly the number of bars now sitting after it.
+    return (cur["bar_count"] - prev["bar_count"]) == (bars_strictly_after or 0)
+
+
+def _membership_timeline_incremental(
+    session: Session, cfg: Config, snapshot_dates: list[date_cls], prev_payload: dict,
+) -> dict:
+    """ops-hardening iter-45 (J-05/J-07 fix) — the append-forward fast path `membership_timeline_cached`'s
+    MISS branch tries BEFORE falling back to `_membership_timeline`'s full O(dates × pool) sweep. Reuses
+    every previously-cached date's point UNCHANGED (byte-for-byte — TC-2) and calls
+    `_excluded_counts_by_date`/`resolve_with_reasons` (the O(dates × pool) resolver storm this fix exists
+    to bound — iter-44's live SIGUSR1 dump named this exact call chain as the block behind BOTH J-05's
+    never-completing single-day backfill and J-07's forward-aggregate warm never advancing past
+    `horizons_done: 0`) ONLY for the genuinely new date(s) — never for any date `<= D_prev` (TC-1).
+    Byte-identical to `_membership_timeline(session, cfg, snapshot_dates)` for the SAME dates (TC-3):
+    `entries`/`exits` are seeded from the SAME single membership join query `_membership_timeline` itself
+    reads unconditionally (cheap — a single JOIN, not the O(dates × pool) cost; only the resolver sweep
+    below is bounded), so the iterative seen/prev_members state the original per-date loop builds is
+    reconstructed exactly, not approximated.
+
+    Caller-enforced precondition (this function does not re-check it): every date in `snapshot_dates`
+    absent from `prev_payload`'s points is STRICTLY LATER than every already-cached date, and no
+    previously-cached date is missing from `snapshot_dates`. A historical gap-fill (a new date EARLIER
+    than an already-cached one) is NOT append-forward — `entries`/`exits` are defined relative to the FULL
+    prior timeline, so an earlier insertion can retroactively change a LATER cached date's entries/exits
+    (binding iter-27/iter-9 "order-dependent state" lesson) — the caller must use the full recompute
+    fallback for that case instead of calling this function."""
+    prev_points_by_date = {p["date"]: p for p in prev_payload.get("points", [])}
+    dates_sorted = sorted(snapshot_dates)
+    new_dates = [d for d in dates_sorted if d.isoformat() not in prev_points_by_date]
+    prev_dates = sorted(date_cls.fromisoformat(s) for s in prev_points_by_date)
+
+    pool_symbols = {row["symbol"] for row in read_pool()}
+    pool_count = len(pool_symbols)
+
+    # ONE query, same as `_membership_timeline`'s own — every (run.asof_date, ticker), read once. Cheap
+    # (a single JOIN, not the O(dates × pool) resolver sweep below); reused here to reconstruct the exact
+    # `seen`/`prev_members` state the iterative per-date loop would have built through the already-cached
+    # dates, without re-walking the resolver for any of them.
+    rows = session.exec(
+        select(ScannerRun.asof_date, ScannerResult.ticker)
+        .join(ScannerResult, ScannerResult.run_id == ScannerRun.id)
+    ).all()
+    members_by_date: dict[date_cls, set[str]] = {}
+    for asof_date, ticker in rows:
+        members_by_date.setdefault(asof_date, set()).add(ticker.upper())
+
+    seen: set[str] = set()
+    for d in prev_dates:
+        seen |= members_by_date.get(d, set())
+    prev_members = members_by_date.get(prev_dates[-1], set()) if prev_dates else set()
+
+    # THE bounded call — `resolve_with_reasons` (via `_excluded_counts_by_date`) runs ONLY for `new_dates`,
+    # never for any already-cached date (TC-1). This is the fix: J-05/J-07's shared root cause was this
+    # same call running over ALL ~2,860 historical dates on every single-date ingest.
+    excluded_by_date = _excluded_counts_by_date(session, cfg, new_dates, pool_symbols)
+
+    new_points_by_date: dict[str, dict] = {}
+    for d in new_dates:
+        members = members_by_date.get(d, set())
+        entries = sorted(m for m in members if m not in seen)
+        exits = sorted(m for m in prev_members if m not in members)
+        seen |= members
+        prev_members = members
+        new_points_by_date[d.isoformat()] = {
+            "date": d.isoformat(),
+            "size": len(members),
+            "entries": entries,
+            "exits": exits,
+            "excluded": excluded_by_date[d],
+        }
+
+    points = [
+        prev_points_by_date[d.isoformat()] if d.isoformat() in prev_points_by_date
+        else new_points_by_date[d.isoformat()]
+        for d in dates_sorted
+    ]
+
+    return {
+        "candidate_pool_count": pool_count,
+        "points": points,
+        # J-95(b)/J-96: the three honest labels carried VERBATIM beside the timeline (single source) —
+        # recomputed fresh here (cheap; unrelated to the O(dates × pool) sweep this function bounds),
+        # exactly mirroring `_membership_timeline`'s own call.
+        "labels": _membership_labels(session, cfg),
+    }
+
+
 def membership_timeline_cached(
     session: Session, cfg: Config, snapshot_dates: list[date_cls]
 ) -> dict:
@@ -662,17 +816,59 @@ def membership_timeline_cached(
     if hit is not None:
         return json.loads(hit.payload_json)
 
-    # MISS — compute once (the cold, BOUNDED compute) and persist under the current stamp.
-    # ops-hardening iter-38 (audit B7, iter-36 — stale-docstring fix): `_membership_timeline`'s per-date
-    # excluded-by-reason counts are sourced via `_excluded_counts_by_date` (above), which reuses an ACTIVE
-    # outer job-scoped bar cache when one is already open (e.g. a `_do_backfill`/`_persist_per_date_
-    # coverage_snapshots` caller), or else walks the candidate pool in `membership_timeline_batch_symbols`-
-    # wide batches — ONE `_BarCache` instance whose contents are REPLACED per batch, never a single
-    # whole-pool `prefilled_bar_cache` scan — so peak resident bar data is bounded by batch width, not by
-    # the full candidate pool's price history (the O(dates) grouped-count round-trip this replaced no
-    # longer runs either way). The warm-up daemon precomputes this off the boot path so the FIRST request
-    # after a boot/rebuild is already a hit.
-    payload = _membership_timeline(session, cfg, snapshot_dates)
+    # MISS. ops-hardening iter-45 (J-05/J-07 fix): try the append-forward fast path FIRST — reuse the most
+    # recently cached payload (any dataset_version; there is normally at most one live row at a time, since
+    # the prune below removes every OTHER version on each write) and bound the resolver sweep to genuinely
+    # new date(s) only, instead of `_membership_timeline`'s full O(dates × pool) sweep over EVERY historical
+    # date — the recompute storm that iter-44's live SIGUSR1 dump named as the shared root cause behind
+    # J-05's single-day backfill never reaching a terminal outcome (1,001s+, three attempts) and J-07's
+    # forward-aggregate warm never advancing `horizons_done` past 0 (this refresh runs BEFORE the warm loop
+    # in this function's finalize-tail caller). Falls back to the EXISTING, UNCHANGED full recompute for:
+    # the first-ever compute (no previous row), a historical gap-fill (a new date EARLIER than an
+    # already-cached one — order-dependent entries/exits, binding iter-27/iter-9 lesson), a previously-
+    # cached date now missing from `snapshot_dates`, or any OTHER dataset_version change with no new date at
+    # all (e.g. a `min_history_bars` re-basis) — none of those are append-forward, and the fast path is
+    # deliberately NOT generalized to them (`assumptions.md` iter-45).
+    prev_row = session.exec(
+        select(MembershipTimelineCache).order_by(MembershipTimelineCache.created_at.desc())
+    ).first()
+    payload = None
+    if prev_row is not None:
+        prev_payload = json.loads(prev_row.payload_json)
+        prev_dates = sorted(
+            date_cls.fromisoformat(p["date"]) for p in prev_payload.get("points", [])
+        )
+        dates_sorted = sorted(snapshot_dates)
+        dates_set = set(dates_sorted)
+        prev_dates_set = set(prev_dates)
+        new_dates = [d for d in dates_sorted if d not in prev_dates_set]
+        missing_dates = [d for d in prev_dates if d not in dates_set]
+        append_forward = bool(new_dates) and not missing_dates and (
+            not prev_dates or min(new_dates) > prev_dates[-1]
+        )
+        # ops-hardening iter-45 AUDIT (B4): the date ordering above is sufficient for the pure-membership
+        # fields (`size`/`entries`/`exits`) but NOT for the reused per-date `excluded` tallies, which the
+        # resolver derives from BARS `<= d` + `min_history_bars`. Require the bars manifest to have moved
+        # forward-only as well, or the cached `excluded` counts could be stale for already-cached dates.
+        if append_forward and not _membership_bars_are_forward_only(
+            session, prev_row.dataset_version, version,
+        ):
+            append_forward = False
+        if append_forward:
+            payload = _membership_timeline_incremental(session, cfg, dates_sorted, prev_payload)
+
+    if payload is None:
+        # the cold, BOUNDED (non-append-forward) compute — UNCHANGED from before this iteration.
+        # ops-hardening iter-38 (audit B7, iter-36 — stale-docstring fix): `_membership_timeline`'s per-date
+        # excluded-by-reason counts are sourced via `_excluded_counts_by_date` (above), which reuses an ACTIVE
+        # outer job-scoped bar cache when one is already open (e.g. a `_do_backfill`/`_persist_per_date_
+        # coverage_snapshots` caller), or else walks the candidate pool in `membership_timeline_batch_symbols`-
+        # wide batches — ONE `_BarCache` instance whose contents are REPLACED per batch, never a single
+        # whole-pool `prefilled_bar_cache` scan — so peak resident bar data is bounded by batch width, not by
+        # the full candidate pool's price history (the O(dates) grouped-count round-trip this replaced no
+        # longer runs either way). The warm-up daemon precomputes this off the boot path so the FIRST request
+        # after a boot/rebuild is already a hit.
+        payload = _membership_timeline(session, cfg, snapshot_dates)
 
     # prune stale rows (any older dataset_version) so the cache table does not grow unbounded as the
     # dataset matures; the current-version row is then inserted (idempotent upsert on the unique key).
@@ -3235,12 +3431,23 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
                 a success and never silently dropped — so `snapshots_created + already_snapshotted +
                 error_other == dates_total` still holds exactly (the run-summary contract in goal.md).
 
-                Deviation from the finalize-tail loops' `logger.exception(...)`-then-`_release_process_
-                memory()` order, deliberately: formatting a traceback ALLOCATES, and this iteration's own
+                Deviation from the finalize-tail loops' log-then-`_release_process_memory()` order,
+                deliberately: formatting a traceback ALLOCATES, and this iteration's own
                 trial-3 evidence shows that failing under real exhaustion
                 (`runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:50` —
                 "Exception ignored in thread started by: <object repr() failed>"). Freeing first buys the
-                headroom the log line needs, and the log line is what makes the abort diagnosable at all."""
+                headroom the log line needs, and the log line is what makes the abort diagnosable at all.
+
+                ops-hardening iter-45 FIX (audit B6): that log call is `_log_isolation_failure`, NOT a bare
+                `logger.exception`. Releasing first buys headroom but does not GUARANTEE it — the audit's
+                own live evidence is that the abort line this handler exists to emit
+                (`grep -c "backfill per-date compute aborted"` → 0) never appeared for run 281's fatal
+                `MemoryError`, so if the render still raises here the second exception is raised inside this
+                `except` clause, past the point its own `try` protects: it escapes `_compute_one_isolated`
+                (which the docstring above promises "never raises"), so the date is never recorded as an
+                isolated failure, the run-summary invariant `snapshots_created + already_snapshotted +
+                error_other == dates_total` breaks, and the whole job aborts to `failed` instead of ending
+                `partial` with per-date detail."""
                 if memory_pressure.is_set():
                     return d, None, 0.0, (
                         "skipped — this job already aborted a date for memory pressure "
@@ -3253,7 +3460,7 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
                 except MemoryError:
                     memory_pressure.set()  # latch FIRST so in-flight siblings stop allocating immediately
                     _release_process_memory()
-                    logger.exception(
+                    _log_isolation_failure(
                         "backfill per-date compute aborted at %s — memory pressure, skipping the remaining "
                         "dates in this job", d,
                     )
@@ -3403,8 +3610,18 @@ def _persist_per_date_coverage_snapshots(
             # backing off — the confirmed root cause of iter-7's 7+ minute health hang). Caught distinctly,
             # BEFORE the generic handler: stop this loop immediately (no further dates attempted) and force
             # freed memory back to the OS before returning to the caller's next independent block.
+            # ops-hardening iter-45 AUDIT (B5): `_log_isolation_failure`, NOT a bare `logger.exception`.
+            # iter-45 applied that guard to the 12 handlers written INSIDE `_refresh_ingest_aggregates`'s
+            # own body, but this per-date coverage loop — which that function's own docstring names as one
+            # of "the four per-item warm loops this function drives directly or CALLS INTO", and which is
+            # the very path the iter-44 review's live flake reproduced in — was missed. A `logger.exception`
+            # that raises here escapes THIS per-date isolation handler, so `_release_process_memory()` never
+            # runs and `aborted_for_memory` is never latched: the memory back-off this block exists to
+            # perform is skipped under exactly the pressure it is for. (The escape is then contained by the
+            # caller's own `_log_isolation_failure` wrapper, so the "never raise" contract still holds — but
+            # the per-date isolation and the back-off do not.)
             except MemoryError as exc:
-                logger.exception(
+                _log_isolation_failure(
                     "ingest per-date coverage warm aborted at %s — memory pressure, stopping remaining "
                     "dates in this loop: %s", d, exc,
                 )
@@ -3412,7 +3629,9 @@ def _persist_per_date_coverage_snapshots(
                 aborted_for_memory = True
                 break
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
-                logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
+                _log_isolation_failure(
+                    "ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc,
+                )
     # iter-8 AUDIT (B1 fix): the `_release_process_memory()` inside the loop above necessarily runs while
     # `cache_ctx`'s cache is still referenced by the enclosing `with`, so the single largest freeable block
     # cannot be trimmed there and the caller's NEXT independent warm block (market-phase, forward-
@@ -3427,6 +3646,45 @@ def _persist_per_date_coverage_snapshots(
         _release_process_memory()
 
 
+def _log_isolation_failure(msg: str, *args: object, exc_info: bool = True) -> None:
+    """ops-hardening iter-45 (reviewer CRITICAL — iter-44's THIRD `MemoryError` escape): `logger.exception()`
+    formats and renders the FULL current traceback, which itself allocates — under the SAME exhausted
+    `ulimit -v` cap that produced the exception a per-item isolation handler below is trying to log, that
+    allocation can itself raise a SECOND exception. That second exception is raised INSIDE the caller's
+    `except` clause, past the point the clause's own `try` protects, so it propagates straight out of
+    `_refresh_ingest_aggregates` — breaking its documented "log + continue, never raise" contract even
+    though the ORIGINAL exception was already correctly caught. Live-reproduced by
+    `test_ingest_finalize_memory_pressure.py` (1 failed/1 passed across two consecutive runs, iter-44
+    review) inside the coverage/membership-timeline refresh path (`data_manager.py` ~3506-3517); guarded
+    here for EVERY per-item isolation handler in `_refresh_ingest_aggregates`, not only the one site the
+    flaky repro happened to land on (binding iter-43 lesson: key the guard to the WHOLE exception set an
+    incident produces, not its headline exception — an allocator-timing-dependent failure could as easily
+    land in any of the other handlers' own `logger.exception()` call).
+
+    Tries the full traceback first (unchanged behavior for every normal, non-memory-pressure failure); on
+    ANY failure while logging, falls back to a minimal-allocation, traceback-free record; if even THAT
+    raises, gives up silently — logging is diagnostic-only and must never itself be the reason a "never
+    raise" contract breaks.
+
+    ops-hardening iter-45 FIX (audit B6): `exc_info=False` suppresses the automatic traceback render for
+    the ONE caller that must not have it — `_run_job`'s outer fatal-job handler. `logger.exception`
+    attaches the LIVE exception, whose formatted traceback carries the exception's RAW text; on a fetch/
+    expand job that text can embed the resolved provider key (`_make_scrubber`'s whole reason for
+    existing: "defense-in-depth on top of the `_http.py` URL redaction"). That caller passes its own
+    ALREADY-SCRUBBED traceback string as an argument instead. Default `True` — all 16 pre-existing call
+    sites are byte-identical to before; none of them handles a key-bearing exception."""
+    try:
+        if exc_info:
+            logger.exception(msg, *args)
+        else:
+            logger.error(msg, *args)
+    except Exception:  # noqa: BLE001 — logging itself must never escape an isolation handler
+        try:
+            logger.error(msg + " (traceback omitted — logging itself hit memory pressure)", *args)
+        except Exception:  # noqa: BLE001 — even the minimal fallback must never escape
+            pass
+
+
 def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress) -> list[str]:
     """The ingest finalize hook (J-05). Each aggregate is refreshed independently (its own try/except: log
     + continue) so one aggregate's failure never prevents another from refreshing, and this function itself
@@ -3514,7 +3772,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                     # above — warmed for free by that SAME call, never a second/separate derivation.
                     refreshed.append("membership_timeline")
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
-                logger.exception("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
+                _log_isolation_failure("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
 
             # iter-2 review (CRITICAL): also persist a per-date coverage_snapshot for every date THIS run
             # newly created, so the app-wide as-of switcher serves REAL coverage for each historical date
@@ -3525,7 +3783,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
             try:
                 _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates, prog)
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
-                logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)
+                _log_isolation_failure("ingest per-date coverage warm failed (non-fatal): %s", exc)
 
             market_phase_warmed = False
             for d in prog.new_snapshot_dates:
@@ -3539,14 +3797,14 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 # pressure. `market_phase_warmed` already honestly reflects any dates that succeeded before
                 # the abort.
                 except MemoryError as exc:
-                    logger.exception(
+                    _log_isolation_failure(
                         "ingest market-phase warm aborted at %s — memory pressure, stopping remaining dates "
                         "in this loop: %s", d, exc,
                     )
                     _release_process_memory()
                     break
                 except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
-                    logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
+                    _log_isolation_failure("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
             if market_phase_warmed:
                 refreshed.append("market_phase")
 
@@ -3589,7 +3847,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                             )
                             forward_aggregates_warmed = True
                         except MemoryError as exc:
-                            logger.exception(
+                            _log_isolation_failure(
                                 "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
                                 "stopping remaining horizons in this loop: %s", h, exc,
                             )
... [diff_bound] apps/backend/app/engine/data_manager.py: 157 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 3b8e46a6..a93b61f7 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -5493,3 +5493,597 @@ def test_run_job_textless_exception_still_names_a_real_reason(tmp_path, monkeypa
     persisted_message = summarize_provider_run(row)["message"]
     assert "MemoryError" in persisted_message
     assert "snapshots over" not in persisted_message
+
+
+# ==================================================================================================
+# ops-hardening iter-45 (J-05/J-07 fix) — the membership-timeline APPEND-FORWARD fast path.
+#
+# `membership_timeline_cached`'s MISS branch previously ran `_membership_timeline`'s full O(dates × pool)
+# `resolve_with_reasons` sweep over EVERY historical snapshot date on ANY dataset-version bump — including
+# the common case of exactly ONE new trading day landing via a single-day backfill. iter-44's live SIGUSR1
+# dump named this exact call chain (`resolve_with_reasons` <- `_excluded_counts_by_date` <-
+# `_membership_timeline` <- `membership_timeline_cached`) as the shared root cause of BOTH J-05's single-day
+# backfill never reaching a terminal outcome (three attempts, longest 1,001s) and J-07's forward-aggregate
+# warm never advancing `horizons_done` past 0 (this refresh runs BEFORE the warm loop in the finalize
+# tail). `_membership_timeline_incremental` now bounds that sweep to genuinely NEW date(s) only when the
+# ingest is append-forward (every new date >= every already-cached date); a historical gap-fill (a new
+# date EARLIER than an already-cached one) still falls back to the EXISTING, UNCHANGED full recompute,
+# since `entries`/`exits` are order-dependent (binding iter-27/iter-9 lesson).
+# ==================================================================================================
+def _mk_membership_snapshot(session: Session, asof: date, tickers: list[str]) -> None:
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
+        new_high_low_json="{}", candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.commit()
+    session.refresh(run)
+    for i, t in enumerate(tickers):
+        session.add(ScannerResult(
+            run_id=run.id, ticker=t, name=t, sector="Technology",
+            leadership_score=float(100 - i), leadership_bucket="A",
+            entry_quality_score=1.0, entry_quality_bucket="A", risk_score=1.0, risk_bucket="A",
+            setup_status="Watchlist", rank=i + 1, record_json="{}",
+        ))
+    session.commit()
+
+
+def _all_scanner_run_dates(session: Session) -> list[date]:
+    return sorted(session.exec(select(ScannerRun.asof_date)).all())
+
+
+@pytest.fixture()
+def membership_fast_path_engine(tmp_path):
+    """Three already-cached historical snapshots (D1 < D2 < D3, an AAA/BBB/CCC entries/exits shape mirroring
+    the dedicated membership-cache test fixture) so each test below has a genuine prior cache row to append
+    onto."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'membership_fast_path.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, date(2024, 1, 3), ["AAA", "BBB"])
+        _mk_membership_snapshot(session, date(2024, 2, 1), ["AAA", "CCC"])
+        _mk_membership_snapshot(session, date(2024, 3, 1), ["AAA", "BBB", "CCC"])
+    return engine
+
+
+def test_append_forward_ingest_does_not_reinvoke_resolver_for_cached_dates(
+    membership_fast_path_engine, monkeypatch,
+):
+    """TC-1 — an append-forward ingest of exactly ONE new, later trading day does NOT re-invoke
+    `resolve_with_reasons` (directly or via `_excluded_counts_by_date`) for any date `<= D_prev`; only the
+    new date is ever resolved (the real committed pool batches `resolve_with_reasons` per
+    `research.membership_timeline_batch_symbols`-wide chunk, so a single date can see MULTIPLE calls — all
+    of them must name the new date, never an already-cached one)."""
+    engine = membership_fast_path_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        assert len(dates) == 3
+        data_manager.membership_timeline_cached(session, cfg, dates)  # warm the cache under v1
+
+    d_new = date(2024, 4, 1)  # strictly LATER than every already-cached date -- append-forward
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
+
+    resolved_dates: list[date] = []
+    orig_resolve = data_manager.universe_resolver.resolve_with_reasons
+
+    def _spy(session_arg, d, cfg_arg, **kwargs):
+        resolved_dates.append(d)
+        return orig_resolve(session_arg, d, cfg_arg, **kwargs)
+
+    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)
+
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        assert len(dates) == 4
+        data_manager.membership_timeline_cached(session, cfg, dates)  # MISS -> the append-forward fast path
+
+    assert resolved_dates, "expected the new date's resolver sweep to actually run"
+    assert set(resolved_dates) == {d_new}, (
+        f"resolve_with_reasons must run ONLY for the new date {d_new}, never for an already-cached date "
+        f"(TC-1) -- got calls for {sorted(set(resolved_dates))}"
+    )
+
+
+def test_append_forward_reuses_cached_points_byte_for_byte(membership_fast_path_engine):
+    """TC-2 — every already-cached (`<= D_prev`) date's `size`/`entries`/`exits`/`excluded` fields are
+    byte-for-byte unchanged after an append-forward ingest, and the new stamp's payload has exactly one
+    more point than the prior stamp's (the new date, honestly reflecting its own entries/exits)."""
+    engine = membership_fast_path_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        prev_payload = data_manager.membership_timeline_cached(session, cfg, dates)
+    assert len(prev_payload["points"]) == 3
+
+    d_new = date(2024, 4, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
+
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        new_payload = data_manager.membership_timeline_cached(session, cfg, dates)
+
+    assert len(new_payload["points"]) == len(prev_payload["points"]) + 1
+    prev_by_date = {p["date"]: p for p in prev_payload["points"]}
+    new_by_date = {p["date"]: p for p in new_payload["points"]}
+    for d_iso, point in prev_by_date.items():
+        assert new_by_date[d_iso] == point, f"{d_iso}'s cached point changed after an append-forward ingest"
+
+    fresh = new_by_date[d_new.isoformat()]
+    assert fresh["date"] == d_new.isoformat()
+    assert fresh["size"] == 3
+    assert fresh["entries"] == ["DDD"]  # AAA/BBB already seen; only DDD is a first-ever appearance
+    assert fresh["exits"] == ["CCC"]  # D3's members (AAA/BBB/CCC) minus D_new's (AAA/BBB/DDD) -> CCC exits
+
+
+def test_append_forward_fast_path_byte_identical_to_full_recompute(membership_fast_path_engine):
+    """TC-3 — the append-forward fast path's served payload is byte-identical to `_membership_timeline`'s
+    own full recompute (UNCHANGED by this iteration -- the pre-fix reference oracle) for the SAME dates and
+    DB state."""
+    engine = membership_fast_path_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1
+
+    d_new = date(2024, 4, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
+
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        fast_path_payload = data_manager.membership_timeline_cached(session, cfg, dates)  # append-forward
+        oracle_payload = data_manager._membership_timeline(session, cfg, dates)  # PRE-FIX full recompute
+
+    assert fast_path_payload == oracle_payload
+
+
+def test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse(membership_fast_path_engine):
+    """Regression — a historical gap-fill (a new date STRICTLY EARLIER than an already-cached one) must NOT
+    take the append-forward fast path: `entries`/`exits` are order-dependent on the FULL prior timeline, so
+    an earlier insertion can retroactively change a LATER cached date's entries/exits (binding
+    iter-27/iter-9 lesson). The served payload must equal a fresh full recompute -- never a stale reuse of
+    the pre-gap-fill cached points."""
+    engine = membership_fast_path_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        pre_gap_payload = data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1 (3 dates)
+
+    # a new date EARLIER than 2024-01-03 (the earliest already-cached date) -- AAA now first appears here,
+    # not on D1, so a correct recompute MUST change D1's entries; a stale reuse would not.
+    d_gap = date(2023, 12, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d_gap, ["AAA", "EEE"])
+
+    with Session(engine) as session:
+        dates = _all_scanner_run_dates(session)
+        assert dates[0] == d_gap  # confirms this really is EARLIER than every previously-cached date
+        served = data_manager.membership_timeline_cached(session, cfg, dates)
+        oracle = data_manager._membership_timeline(session, cfg, dates)
+
+    assert served == oracle  # the fallback path -- byte-identical to a fresh full recompute
+    served_by_date = {p["date"]: p for p in served["points"]}
+    pre_gap_by_date = {p["date"]: p for p in pre_gap_payload["points"]}
+    assert served_by_date["2024-01-03"] != pre_gap_by_date["2024-01-03"], (
+        "the gap-fill must RECOMPUTE D1's entries (AAA is no longer first-seen there) -- a stale reuse of "
+        "the pre-gap-fill point would incorrectly still show AAA as a D1 entry"
+    )
+    assert "AAA" not in served_by_date["2024-01-03"]["entries"]  # AAA is now first-seen on d_gap, not D1
+    assert served_by_date["2024-01-03"]["exits"] == ["EEE"]  # EEE (present on d_gap) is gone by D1
+
+
+# ==================================================================================================
+# ops-hardening iter-45 AUDIT — regression tests for the three fixes applied during the audit pass.
+# ==================================================================================================
+def test_log_isolation_failure_swallows_a_raising_logger_exception(monkeypatch):
+    """AUDIT B2 — DETERMINISTIC proof of `_log_isolation_failure`'s fallback branch. iter-45's own
+    evidence for closing the third `MemoryError` escape was 5 consecutive `ulimit -v` runs of
+    `test_ingest_finalize_memory_pressure.py`; those runs prove the PRIMARY (`logger.exception`) path
+    still works, but `logs/backend.log` shows the fallback's own marker string never appeared once in the
+    live incident either — so the NEW branch this iteration added was covered by nothing. Force it."""
+    calls: list[tuple] = []
+
+    def _boom_exception(*_args, **_kwargs):
+        raise MemoryError()  # noqa: RSE102 — the textless class this session's failures actually raise
+
+    def _record_error(msg, *args, **_kwargs):
+        calls.append((msg, args))
+
+    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
+    monkeypatch.setattr(data_manager.logger, "error", _record_error)
+
+    data_manager._log_isolation_failure("some aggregate failed: %s", "detail")  # must NOT raise
+
+    assert len(calls) == 1, "the traceback-free fallback record must be emitted exactly once"
+    msg, args = calls[0]
+    assert "traceback omitted" in msg
+    assert msg.startswith("some aggregate failed: %s"), "the %s placeholders must keep their arg order"
+    assert args == ("detail",)
+
+
+def test_log_isolation_failure_swallows_even_when_the_fallback_also_raises(monkeypatch):
+    """AUDIT B2 — the last line of defence: under a truly exhausted cap even the minimal-allocation
+    fallback can raise. `_log_isolation_failure` must still return normally, or logging itself becomes the
+    reason the isolation handler's "log + continue, never raise" contract breaks."""
+    def _boom(*_args, **_kwargs):
+        raise MemoryError()  # noqa: RSE102
+
+    monkeypatch.setattr(data_manager.logger, "exception", _boom)
+    monkeypatch.setattr(data_manager.logger, "error", _boom)
+
+    data_manager._log_isolation_failure("everything is on fire: %s", "detail")  # must NOT raise
+
+
+def test_aggregate_refresh_logging_failure_never_flips_a_successful_job_to_failed(tmp_path, monkeypatch):
+    """AUDIT B3 — the SAME third-escape class, one frame OUT of `_refresh_ingest_aggregates`. A
+    `MemoryError` raised by `Session.__exit__` (SQLAlchemy `expunge_all`) lands in `_run_job`'s own
+    aggregate-refresh handler, which is OUTSIDE every per-item isolation handler iter-45 guarded —
+    live-observed in the 2026-08-04 wedge (`logs/backend.log`: a caught MemoryError whose outermost frame
+    is that `with Session(eng)` line). If the handler's own logging call then allocates and raises, the
+    second exception escapes to `_run_job`'s outer `except`, which flips `prog.status = "failed"` —
+    reporting a COMPLETED backfill as failed and breaking that branch's documented contract ("an
+    aggregate-refresh failure must never flip an otherwise-successful ingest job to failed")."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'agg_refresh_logging.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    def _boom_refresh(_session, _cfg, _prog):
+        raise MemoryError()  # noqa: RSE102 — stands in for the Session.__exit__ MemoryError
+
+    def _boom_exception(*_args, **_kwargs):
+        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap
+
+    monkeypatch.setattr(data_manager, "_refresh_ingest_aggregates", _boom_refresh)
+    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
+
+    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
+    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)
+
+    assert summary["status"] == "ok", (
+        "a failure INSIDE the non-fatal aggregate-refresh handler's own logging must never flip the "
+        f"ingest job itself to failed — got {summary['status']!r} ({summary.get('message')!r})"
+    )
+
+
+def _mk_bar(session: Session, symbol: str, d: date) -> None:
+    session.add(DailyPrice(symbol=symbol, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+    session.commit()
+
+
+def test_append_forward_falls_back_when_bars_land_at_or_before_a_cached_date(tmp_path, monkeypatch):
+    """AUDIT B4 — the append-forward precondition checked SNAPSHOT-DATE ordering only, which is sufficient
+    for `size`/`entries`/`exits` (pure membership) but NOT for the reused per-date `excluded` tallies: the
+    resolver derives those from BARS `<= d`, and `_membership_dataset_version` folds in the bars manifest.
+    So a `both` job whose FETCH stage lands a bar at a HISTORICAL date while its BACKFILL stage adds one
+    new LATER snapshot date satisfied "append-forward" and silently reused stale `excluded` counts for
+    every already-cached date — breaking the phase spec's "byte-identical output required" and AG-3.
+
+    Asserted through the SAME `resolve_with_reasons` spy TC-1 uses: taking the fallback means the resolver
+    IS re-invoked for the already-cached dates. The companion test below is the positive control proving
+    this guard did not simply disable the fast path."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'bars_guard.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    d1, d2, d3 = date(2024, 1, 3), date(2024, 2, 1), date(2024, 3, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d1, ["AAA", "BBB"])
+        _mk_membership_snapshot(session, d2, ["AAA", "CCC"])
+        _mk_membership_snapshot(session, d3, ["AAA", "BBB", "CCC"])
+        for d in (d1, d2, d3):
+            _mk_bar(session, "SPY", d)          # bars exist -> the stamp carries a real max-bar date
+        data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))
+
+    d_new = date(2024, 4, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
+        _mk_bar(session, "AAA", d2)             # a HISTORICAL bar (<= D_prev) landing in the same bump
+
+    resolved: list[date] = []
+    orig = data_manager.universe_resolver.resolve_with_reasons
+
+    def _spy(session_arg, d, cfg_arg, **kwargs):
+        resolved.append(d)
+        return orig(session_arg, d, cfg_arg, **kwargs)
+
+    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)
+    with Session(engine) as session:
+        data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))
+
+    assert set(resolved) == {d1, d2, d3, d_new}, (
+        "a bar landing at or before an already-cached date must force the FULL recompute — the cached "
+        f"`excluded` tallies are no longer valid. Resolver saw only {sorted(set(resolved))}"
+    )
+
+
+def test_append_forward_still_used_when_bars_land_strictly_after_every_cached_date(tmp_path, monkeypatch):
+    """AUDIT B4 positive control — the guard above must NOT disable the fast path for the ordinary
+    forward flow (a `both` job fetching a new trading day's bars and snapshotting it). Bars added strictly
+    after the previous max bar date cannot change any `resolve_with_reasons` verdict for a date `<=
+    D_prev`, so the fast path must still bound the resolver to the new date alone (TC-1's property)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'bars_guard_control.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    d1, d2, d3 = date(2024, 1, 3), date(2024, 2, 1), date(2024, 3, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d1, ["AAA", "BBB"])
+        _mk_membership_snapshot(session, d2, ["AAA", "CCC"])
+        _mk_membership_snapshot(session, d3, ["AAA", "BBB", "CCC"])
+        for d in (d1, d2, d3):
+            _mk_bar(session, "SPY", d)
+        data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))
+
+    d_new = date(2024, 4, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
+        _mk_bar(session, "SPY", d_new)          # forward-only bar, strictly after every cached date
+
+    resolved: list[date] = []
+    orig = data_manager.universe_resolver.resolve_with_reasons
+
+    def _spy(session_arg, d, cfg_arg, **kwargs):
+        resolved.append(d)
+        return orig(session_arg, d, cfg_arg, **kwargs)
+
+    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)
+    with Session(engine) as session:
+        served = data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))
+
+    assert set(resolved) == {d_new}, (
+        "a forward-only bar change must keep the append-forward fast path (resolver bounded to the new "
+        f"date) — got {sorted(set(resolved))}"
+    )
+    assert len(served["points"]) == 4
+
+
+def test_per_date_coverage_warm_logging_failure_does_not_skip_the_memory_backoff(tmp_path, monkeypatch):
+    """AUDIT B5 — iter-45 guarded the 12 isolation handlers written inside `_refresh_ingest_aggregates`'s
+    own body, but NOT the per-date coverage warm loop it CALLS INTO
+    (`_persist_per_date_coverage_snapshots`) — which that function's own docstring names as one of "the
+    four per-item warm loops this function drives directly or calls into", and which is the path the
+    iter-44 review's live flake actually reproduced in. A `logger.exception` that raises there escapes the
+    per-date `except MemoryError` handler, so `_release_process_memory()` never runs and
+    `aborted_for_memory` is never latched — the memory back-off is skipped under exactly the pressure it
+    exists for."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'coverage_warm_logging.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+    d1, d2 = date(2024, 1, 3), date(2024, 2, 1)
+    with Session(engine) as session:
+        _mk_membership_snapshot(session, d1, ["AAA", "BBB"])
+        _mk_membership_snapshot(session, d2, ["AAA", "CCC"])
+        for d in (d1, d2):
+            _mk_bar(session, "SPY", d)
+
+    def _boom_coverage(_session, _cfg, _asof):
+        raise MemoryError()  # noqa: RSE102 — the real pressure this loop's handler exists for
+
+    def _boom_exception(*_args, **_kwargs):
+        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap
+
+    released: list[int] = []
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _boom_coverage)
+    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
+    monkeypatch.setattr(data_manager, "_release_process_memory", lambda: released.append(1))
+
+    job = create_job("backfill", d1, d1)
+    prog = data_manager._JOBS[job.job_id]
+    with Session(engine) as session:
+        data_manager._persist_per_date_coverage_snapshots(session, cfg, [d1], prog)  # must NOT raise
+
+    assert released, (
+        "the per-date MemoryError handler's `_release_process_memory()` back-off must still run when the "
+        "handler's own logging call raises — otherwise the loop aborts with no memory reclaimed"
+    )
+
+
+# ==================================================================================================
+# ops-hardening iter-45 FIX PASS (audit B6) — a fatal data job must LEAVE EVIDENCE.
+#
+# The audit's single most important live failure (run 281, `2019-02-25`) reached terminal `failed` with
+# the persisted reason `"MemoryError (no message)"` and wrote NOTHING to `logs/backend.log`:
... [diff_bound] apps/backend/tests/test_data_manager.py: 202 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index f262b76f..dba151b2 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -32,9 +32,11 @@ from __future__ import annotations
 import datetime
 import json
 import os
+import struct
 import sys
 import urllib.error
 import urllib.request
+import zlib
 from pathlib import Path
 from urllib.parse import urlsplit, urlunsplit
 
@@ -339,6 +341,47 @@ def render_script_md(phase_id: str, frontend_url: str, iteration, steps: list[di
     return "\n".join(lines)
 
 
+_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
+
+
+def _png_text_chunk(keyword: str, text: str) -> bytes:
+    """One PNG `tEXt` chunk: length + type + (keyword NUL text) + CRC32."""
+    payload = (keyword.encode("latin-1", "replace")[:79] + b"\x00"
+               + text.encode("latin-1", "replace"))
+    return (struct.pack(">I", len(payload)) + b"tEXt" + payload
+            + struct.pack(">I", zlib.crc32(b"tEXt" + payload) & 0xFFFFFFFF))
+
+
+def png_with_provenance(raw: bytes, entries: list[tuple[str, str]]) -> bytes:
+    """Return `raw` with provenance `tEXt` chunks inserted directly after IHDR.
+
+    WHY (ops-hardening iter-45, audit F1): verify mode captures ONE end-state
+    screenshot per journey, so two journeys whose last step lands on the same
+    page in the same state produce BYTE-IDENTICAL files — J-03 and J-04 both end
+    on `/data`, and both captures hashed `9d77429b…`. The regression check that
+    exists to prove every journey got its OWN capture (never one file re-cited by
+    several journeys — the iter-43 defect) then fires on evidence that is in fact
+    honest, and cannot distinguish that case from the dishonest one it targets.
+
+    Stamping the journey's own identity into the file settles it by construction:
+    each capture is unique because its provenance differs, and the PNG says which
+    journey it belongs to when read directly. `tEXt` is a standard ANCILLARY
+    chunk — decoders ignore what they don't know, so NOT ONE PIXEL changes. This
+    annotates the file, never the page: overlaying a banner on the rendered page
+    before capture would have altered the very evidence being recorded.
+
+    Returns `raw` unchanged if it is not a PNG with a leading IHDR (never raises
+    — evidence capture must not be able to fail a replay).
+    """
+    if not raw.startswith(_PNG_SIGNATURE) or len(raw) < 16 or raw[12:16] != b"IHDR":
+        return raw
+    ihdr_end = 8 + 8 + struct.unpack(">I", raw[8:12])[0] + 4  # sig + len/type + data + crc
+    if ihdr_end > len(raw):
+        return raw
+    stamped = b"".join(_png_text_chunk(k, v) for k, v in entries)
+    return raw[:ihdr_end] + stamped + raw[ihdr_end:]
+
+
 # ── self-test (written first, TDD) ───────────────────────────────────────────
 # Each _t_* function checks one behavior. The harness runs them all and reports
 # every failure, so a fresh run shows the full RED surface at once.
@@ -705,7 +748,63 @@ def _t_derive_prefix_without_journey_key() -> None:
     assert golden["steps"][0]["action"]["type"] == "goto"
 
 
+def _png_chunks(raw: bytes) -> list[tuple[bytes, bytes]]:
+    """Parse a PNG into `[(type, data), …]` — the self-test's independent reader,
+    so the stamp is verified by decoding it, never by trusting the writer."""
+    out, i = [], len(_PNG_SIGNATURE)
+    while i + 8 <= len(raw):
+        n = struct.unpack(">I", raw[i:i + 4])[0]
+        typ, data = raw[i + 4:i + 8], raw[i + 8:i + 8 + n]
+        assert zlib.crc32(typ + data) & 0xFFFFFFFF == struct.unpack(">I", raw[i + 8 + n:i + 12 + n])[0], \
+            f"chunk {typ!r} CRC mismatch — the stamped file is not a valid PNG"
+        out.append((typ, data))
+        i += 12 + n
+    return out
+
+
+def _tiny_png() -> bytes:
+    """A minimal, valid 1x1 greyscale PNG — the fixture two 'identical captures' share."""
+    def chunk(typ: bytes, data: bytes) -> bytes:
+        return (struct.pack(">I", len(data)) + typ + data
+                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))
+    return (_PNG_SIGNATURE
+            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
+            + chunk(b"IDAT", zlib.compress(b"\x00\x00"))
+            + chunk(b"IEND", b""))
+
+
+def _t_png_provenance_makes_identical_captures_distinct() -> None:
+    """iter-45 audit F1 — the exact J-03/J-04 case: two journeys, one identical
+    end-state capture. After stamping, the files must differ, must each name their
+    OWN journey, and must still be valid PNGs whose pixel data is untouched."""
+    raw = _tiny_png()
+    a = png_with_provenance(raw, [("Journey", "J-03"), ("Phase", "iter-45")])
+    b = png_with_provenance(raw, [("Journey", "J-04"), ("Phase", "iter-45")])
+    assert a != b, "two journeys' captures must not stay byte-identical after stamping"
+
+    for stamped, jid in ((a, "J-03"), (b, "J-04")):
+        chunks = _png_chunks(stamped)                      # asserts every CRC
+        types = [t for t, _ in chunks]
+        assert types[0] == b"IHDR" and types[-1] == b"IEND", types
+        assert b"tEXt" in types
+        texts = [d for t, d in chunks if t == b"tEXt"]
+        assert any(d.startswith(b"Journey\x00") and d.endswith(jid.encode()) for d in texts), texts
+        # NOT ONE PIXEL changed: every non-tEXt chunk is byte-identical to the original.
+        assert [(t, d) for t, d in chunks if t != b"tEXt"] == _png_chunks(raw)
+
+
+def _t_png_provenance_leaves_a_non_png_untouched() -> None:
+    """Evidence capture must never be able to fail a replay: anything that is not
+    a PNG with a leading IHDR comes back byte-for-byte unchanged, never an error."""
+    assert png_with_provenance(b"", [("Journey", "J-03")]) == b""
+    assert png_with_provenance(b"not a png at all", [("Journey", "J-03")]) == b"not a png at all"
+    truncated = _tiny_png()[:12]
+    assert png_with_provenance(truncated, [("Journey", "J-03")]) == truncated
+
+
 _SELF_TEST_CHECKS = [
+    _t_png_provenance_makes_identical_captures_distinct,
+    _t_png_provenance_leaves_a_non_png_untouched,
     _t_normalize_url_relative,
     _t_normalize_url_rewrites_localhost,
     _t_normalize_url_keeps_external,
@@ -1395,6 +1494,20 @@ def run_verify(opts, base_url: str) -> int:
                     try:
                         page.screenshot(path=str(shot_abs))
                         shot_rel = _rel(str(shot_abs), opts.repo_root)
+                        # iter-45 audit F1: stamp the capture with its OWN journey so two
+                        # journeys ending on the same page in the same state can never be
+                        # byte-identical (J-03/J-04 both end on /data and both hashed
+                        # 9d77429b…). Ancillary `tEXt` only — no pixel is altered. Its own
+                        # try: a stamping failure must never fail an otherwise-passing replay.
+                        try:
+                            shot_abs.write_bytes(png_with_provenance(shot_abs.read_bytes(), [
+                                ("Journey", jid),
+                                ("Phase", str(opts.phase_id or "")),
+                                ("Created", datetime.datetime.now().isoformat(timespec="seconds")),
+                                ("Source", "demo_runner.py --mode verify"),
+                            ]))
+                        except Exception:  # noqa: BLE001
+                            pass
                     except Exception:  # noqa: BLE001
                         pass
                 results.append({"journey": jid, "name": name, "verdict": verdict,
```

## Excluded-path stat (dependency/lockfile visibility)

 .../journey-scripts/J-07.json                      |  4 +-
 .../state/drift-report.json                        |  2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    | 43 ++++++++++++++++++++++
 runs/goal-session-ops-hardening/trace/.next-step   |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  9 +++++
 5 files changed, 56 insertions(+), 4 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
