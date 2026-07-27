# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (19 diff lines)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 7b15a681..7459f0fa 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1092,6 +1092,25 @@ def _scanner_run_exists(session: Session, asof: date_cls) -> bool:
     ).first() is not None
 
 
+def _tag_coverage_status(
+    payload: dict,
+    status: str,
+    *,
+    stale_dataset_version: Optional[str] = None,
+    stale_computed_at: Optional[str] = None,
+) -> dict:
+    """ops-hardening iter-27 (AG-3) — stamp the additive `coverage_status`/`stale_dataset_version`/
+    `stale_computed_at` sibling fields onto an already-resolved coverage payload (never a second
+    derivation of any coverage figure — every caller below passes through a payload some OTHER path
+    already computed/persisted verbatim). `stale_dataset_version`/`stale_computed_at` are non-null ONLY
+    when `status == "stale"`. Mutates and returns `payload` in place (each caller's `payload` is a fresh
+    dict — `json.loads(...)` or a freshly-computed literal — never a shared/cached object)."""
+    payload["coverage_status"] = status
+    payload["stale_dataset_version"] = stale_dataset_version
+    payload["stale_computed_at"] = stale_computed_at
+    return payload
+
+
 def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date_cls] = None) -> dict:
     """`GET /api/data`'s coverage block, served from the persisted `CoverageSnapshot` row for the resolved
     `(asof_key, dataset_version)` key — REPLACES the former request-path call to `compute_coverage`/
@@ -1109,6 +1128,19 @@ def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date
     This is an AG-3 correctness guarantee (displayed numbers MUST match the engine's computation) that
     overrides the AG-8 no-request-compute preference for this rare, deliberate, one-time-per-date path.
 
+    ops-hardening iter-27 (AG-3 ESCALATE fix): `_membership_dataset_version` is a GLOBAL stamp bumped by
+    ANY new `ScannerRun` row — including one created by a request-path historical `/backtest` create-once
+    view for a date decades in the past. When that bump makes the exact-match lookup above miss, a real,
+    previously-computed row for this SAME `asof_key` can still exist under the now-OLDER stamp (it
+    survives only because no ingest ran since — `_upsert_coverage_snapshot` reclaims every non-current-
+    stamp row at the end of every ingest). One bounded, INDEXED lookup by `asof_key` alone (never a
+    `daily_prices`/`scanner_runs` scan) tried AFTER both paths above miss serves that row's figures
+    labeled `coverage_status: "stale"` — honest, non-zero prior-scan figures — instead of falling through
+    to the all-zero 'not yet computed' sentinel for a database that plainly has real coverage on file.
+    Every returned payload now carries `coverage_status` ("current" / "stale" / "not_yet_computed") plus
+    `stale_dataset_version`/`stale_computed_at` (non-null only for "stale") — additive fields, the
+    pre-existing payload shape is otherwise unchanged.
+
     The common default (`as_of=None`) visit and a genuinely dataless as-of (no `ScannerRun`, e.g. pre-first-
     ingest) still take the honest zero-query 'not yet computed' sentinel — NEVER a live whole-table compute,
     never a blank/500 response (AG-8)."""
@@ -1123,12 +1155,27 @@ def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date
             )
         ).first()
         if row is not None:
-            return json.loads(row.payload_json)
+            return _tag_coverage_status(json.loads(row.payload_json), "current")
         # no persisted row: heal an explicit switcher selection of a real already-ingested historical date
         # (see docstring) — real coverage, self-healed to storage — rather than a false empty-DB sentinel.
         if as_of is not None and _scanner_run_exists(session, resolved_asof):
-            return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
-    return _coverage_not_yet_computed_payload(cfg)
+            return _tag_coverage_status(refresh_coverage_snapshot_for(session, cfg, resolved_asof), "current")
+        # iter-27: the exact-match key missed (current stamp) — check for a real row under an OLDER stamp
+        # for this SAME asof_key before conceding to the all-zero sentinel (see docstring above).
+        stale_row = session.exec(
+            select(CoverageSnapshot)
+            .where(CoverageSnapshot.asof_key == asof_key)
+            .order_by(CoverageSnapshot.computed_at.desc())
+            .limit(1)
+        ).first()
+        if stale_row is not None:
+            return _tag_coverage_status(
+                json.loads(stale_row.payload_json),
+                "stale",
+                stale_dataset_version=stale_row.dataset_version,
+                stale_computed_at=stale_row.computed_at.isoformat(),
+            )
+    return _tag_coverage_status(_coverage_not_yet_computed_payload(cfg), "not_yet_computed")
 
 
 def compute_availability(session: Session, config: Optional[Config] = None) -> dict:
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index ed60e669..c03ecef0 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -363,6 +363,24 @@ def walk_forward_asof_dates(session: Session, config: Optional[Config] = None) -
 # --------------------------------------------------------------------------------------------------
 # Backfill — persist the cadence snapshots, then INSERT realized forward returns (idempotent)
 # --------------------------------------------------------------------------------------------------
+# ops-hardening iter-27 (AG-3/AG-8 ESCALATE fix) -- the DBAPI's own UNIQUE-constraint message for the
+# targeted collision this mid-loop guard tolerates (SQLite reports the constrained COLUMN list, not the
+# constraint name `uq_forward_returns_run_symbol_horizon` — verified directly: see the module-level test
+# in `test_forward_testing_concurrency.py`). Matching on this exact column list keeps the catch narrow: an
+# `IntegrityError` from any OTHER constraint (a different table, a NOT NULL violation, a foreign key) does
+# NOT match and still propagates unchanged (TC-4).
+_FORWARD_RETURN_DUPLICATE_KEY_MARKER = (
+    "UNIQUE constraint failed: forward_returns.run_id, forward_returns.symbol, forward_returns.horizon"
+)
+
+
+def _is_forward_return_duplicate_key_collision(exc: IntegrityError) -> bool:
+    """True only for the ONE collision `_insert_run_forward_returns`'s mid-loop guard tolerates: a
+    concurrent writer already committed the exact same `(run_id, symbol, horizon)` key. Never a blanket
+    `except IntegrityError` — any other constraint violation returns False here and is left to propagate."""
+    return _FORWARD_RETURN_DUPLICATE_KEY_MARKER in str(exc.orig)
+
+
 def _insert_run_forward_returns(
     session: Session,
     run: ScannerRun,
@@ -379,55 +397,89 @@ def _insert_run_forward_returns(
     ONE forward-return formula (no second math path). Only keys absent from `existing` are inserted
     (idempotent), and `existing` is updated in place. INSERT-only — it never UPDATEs/overwrites a
     snapshot row. A (symbol, horizon) with fewer than `horizon` post-D bars contributes nothing
-    (NA, n=0) — never a fabricated 0% (anti-goal: No fabricated data)."""
+    (NA, n=0) — never a fabricated 0% (anti-goal: No fabricated data).
+
+    ops-hardening iter-27 (AG-3/AG-8 ESCALATE fix): tolerates a concurrent writer's collision on the SAME
+    `(run_id, symbol, horizon)` key surfacing MID-LOOP, not only at the final commit
+    `_commit_forward_returns_concurrency_safe` already guards. SQLAlchemy's default autoflush means one
+    symbol's still-pending `session.add(...)` is actually flushed by the NEXT symbol's `close_on`/
+    `bars_after` READ — so when a concurrent sibling call (e.g. two racing `/backtest` requests for the
+    same never-scanned historical as-of) already committed that exact key, the `IntegrityError` fires at
+    that READ, not at an INSERT statement (matches the traceback this fix closes:
+    `_insert_run_forward_returns:390` was the `close_on(...)` call). On that TARGETED collision, roll
+    back — the concurrent writer's row is byte-identical for this frozen-seed data, the SAME tolerant-
+    duplicate reasoning `_commit_forward_returns_concurrency_safe` already applies at the final commit —
+    discard the just-rolled-back symbol's own bookkeeping (so `existing`/the returned count stay truthful,
+    never a fabricated insert count), and continue with the remaining symbols. Any OTHER `IntegrityError`
+    still propagates unchanged (TC-4; never a blanket catch)."""
     inserted = 0
+    pending_keys: list[tuple] = []  # keys added since the last confirmed-flushed symbol; undone on rollback
     for symbol in symbols:
         # Idempotency fast-path: if every horizon for this (run, symbol) is already persisted, skip the
         # price fetches entirely — so a warm re-run does no redundant bar materialization.
         needed = [h for h in horizons if (run.id, symbol, h) not in existing]
         if not needed:
             continue
-        entry_close = close_on(session, symbol, run.asof_date)  # close ON D (date <= D)
-        if entry_close is None:
-            continue
-        post_bars = bars_after(session, symbol, run.asof_date, limit=max_h)  # date > D, bounded
-        if not post_bars:
-            continue  # no post-snapshot bar -> nothing to measure (n=0)
-        for horizon in needed:
-            realized = forward_return(post_bars, entry_close, horizon)
-            if realized is None:
-                continue  # fewer than `horizon` post-bars -> NA, no fabricated row
-            # iter-14 (J-29): the SAME post_bars/entry_close/horizon already in hand, no extra query —
-            # excursions share forward_return's NA gate, so they are non-None whenever realized is.
-            excursions = forward_excursions(post_bars, entry_close, horizon)
-            # iter-27 (J-86): the max-drawdown over the SAME first-`horizon` post-bars window, computed
-            # once here beside mae/mfe via the pure helper that shares the EXACT NA gate — so a row's
-            # max_drawdown is non-None iff realized_return is (never a fabricated 0 for a short window).
-            mdd = max_drawdown(post_bars, entry_close, horizon)
-            # iter-41 (J-25): the two "dry spell" columns over the SAME post_bars/entry_close/horizon
-            # already in hand — zero extra bar reads. underwater_days shares the EXACT NA gate as
-            # max_drawdown (non-None iff realized is); time_to_recover_days is additionally None when the
-            # close never reclaims the entry level within the window (never a fabricated sentinel).
-            uw_days = underwater_days(post_bars, entry_close, horizon)
-            ttr_days = time_to_recover_days(post_bars, entry_close, horizon)
-            session.add(
-                ForwardReturn(
-                    run_id=run.id,
-                    symbol=symbol,
-                    horizon=horizon,
-                    asof_date=run.asof_date,
-                    entry_close=entry_close,
-                    measured_date=post_bars[horizon - 1].date,
-                    realized_return=realized,
-                    mae=excursions["mae"] if excursions else None,
-                    mfe=excursions["mfe"] if excursions else None,
-                    max_drawdown=mdd,
-                    underwater_days=uw_days,
-                    time_to_recover_days=ttr_days,
+        try:
+            entry_close = close_on(session, symbol, run.asof_date)  # close ON D (date <= D)
+            # Reaching this line means any autoflush of a PRIOR symbol's pending rows succeeded — those
+            # keys are durably staged, so this symbol's OWN bookkeeping starts a fresh pending batch.
+            pending_keys = []
+            if entry_close is None:
+                continue
+            post_bars = bars_after(session, symbol, run.asof_date, limit=max_h)  # date > D, bounded
+            if not post_bars:
+                continue  # no post-snapshot bar -> nothing to measure (n=0)
+            for horizon in needed:
+                realized = forward_return(post_bars, entry_close, horizon)
+                if realized is None:
+                    continue  # fewer than `horizon` post-bars -> NA, no fabricated row
+                # iter-14 (J-29): the SAME post_bars/entry_close/horizon already in hand, no extra query —
+                # excursions share forward_return's NA gate, so they are non-None whenever realized is.
+                excursions = forward_excursions(post_bars, entry_close, horizon)
+                # iter-27 (J-86): the max-drawdown over the SAME first-`horizon` post-bars window, computed
+                # once here beside mae/mfe via the pure helper that shares the EXACT NA gate — so a row's
+                # max_drawdown is non-None iff realized_return is (never a fabricated 0 for a short window).
+                mdd = max_drawdown(post_bars, entry_close, horizon)
+                # iter-41 (J-25): the two "dry spell" columns over the SAME post_bars/entry_close/horizon
+                # already in hand — zero extra bar reads. underwater_days shares the EXACT NA gate as
+                # max_drawdown (non-None iff realized is); time_to_recover_days is additionally None when the
+                # close never reclaims the entry level within the window (never a fabricated sentinel).
+                uw_days = underwater_days(post_bars, entry_close, horizon)
+                ttr_days = time_to_recover_days(post_bars, entry_close, horizon)
+                session.add(
+                    ForwardReturn(
+                        run_id=run.id,
+                        symbol=symbol,
+                        horizon=horizon,
+                        asof_date=run.asof_date,
+                        entry_close=entry_close,
+                        measured_date=post_bars[horizon - 1].date,
+                        realized_return=realized,
+                        mae=excursions["mae"] if excursions else None,
+                        mfe=excursions["mfe"] if excursions else None,
+                        max_drawdown=mdd,
+                        underwater_days=uw_days,
+                        time_to_recover_days=ttr_days,
+                    )
                 )
-            )
-            existing.add((run.id, symbol, horizon))
-            inserted += 1
+                key = (run.id, symbol, horizon)
+                existing.add(key)
+                pending_keys.append(key)
+                inserted += 1
+        except IntegrityError as exc:
+            session.rollback()
+            if not _is_forward_return_duplicate_key_collision(exc):
+                raise
+            # A concurrent writer already committed this exact key — the prior symbol's still-pending
+            # duplicate(s) were just rolled back; undo their optimistic `existing`/`inserted` bookkeeping
+            # too so both stay truthful, then continue with the remaining symbols (never an unhandled
+            # exception reaching the caller).
+            for key in pending_keys:
+                existing.discard(key)
+            inserted -= len(pending_keys)
+            pending_keys = []
+            continue
     return inserted
 
 
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 10a12920..57e7b4a0 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -121,7 +121,13 @@ def test_get_data_overview_serves_coverage_from_storage_zero_prefill_calls(data_
     monkeypatch.setattr(data_manager, "prefilled_bar_cache", _boom)
     with Session(data_api_engine) as session:
         payload = data_overview(session=session)
-    assert payload["coverage"] == expected
+    cov = payload["coverage"]
+    # iter-27 (TC-8 regression guard): `coverage_from_storage` now additively stamps coverage_status/
+    # stale_* on top of the byte-identical base payload — assert the stamp, then strip before comparing.
+    assert cov["coverage_status"] == "current"
+    assert cov["stale_dataset_version"] is None and cov["stale_computed_at"] is None
+    served_base = {k: v for k, v in cov.items() if k not in ("coverage_status", "stale_dataset_version", "stale_computed_at")}
+    assert served_base == expected
 
 
 def test_get_data_overview_zero_coverage_rows_serves_honest_sentinel_never_500(tmp_path, monkeypatch):
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 58f2d057..14d14f56 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -2238,6 +2238,17 @@ def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
 # extra compute. Stale coverage_snapshot rows under a superseded dataset_version must be reclaimed in one
 # bounded SQL DELETE, across every asof_key, not just the one being written (B2).
 # ==================================================================================================
+_COVERAGE_STATUS_KEYS = ("coverage_status", "stale_dataset_version", "stale_computed_at")
+
+
+def _strip_coverage_status(served: dict) -> dict:
+    """iter-27 (AG-3, TC-8 regression guard) — `coverage_from_storage` now additively stamps
+    `coverage_status`/`stale_dataset_version`/`stale_computed_at` onto the payload; every pre-existing
+    byte-equality assertion against a raw `_compute_coverage_uncached`/`refresh_coverage_snapshot_for`
+    result (neither of which carries these fields) strips them first via this one shared helper."""
+    return {k: v for k, v in served.items() if k not in _COVERAGE_STATUS_KEYS}
+
+
 def test_fetch_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
     """TC-1/TC-6 (B1) — given a committed DB with a current-stamp coverage_snapshot row already persisted,
     when a `fetch` job lands >= 1 new bar (changing `_membership_dataset_version`) and completes, the
@@ -2285,7 +2296,11 @@ def test_fetch_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
         fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
         assert stored == fresh  # TC-6: byte-identical to an independent fresh compute
         served = data_manager.coverage_from_storage(session, cfg, as_of=None)  # GET /api/data's default read
-        assert served == fresh
+        # iter-27 (TC-8 regression guard): `coverage_from_storage` now additively stamps coverage_status/
+        # stale_* on top of the byte-identical base payload — strip them before the byte-equality compare.
+        assert served["coverage_status"] == "current"
+        assert served["stale_dataset_version"] is None and served["stale_computed_at"] is None
+        assert _strip_coverage_status(served) == fresh
 
 
 def test_zero_work_fetch_skips_coverage_recompute_and_row_write(tmp_path, monkeypatch):
@@ -2483,7 +2498,8 @@ def test_finalize_hook_persists_per_date_coverage_for_historical_switcher_date(t
         # the historical date is served from storage, byte-identical to a fresh compute-at-d_old...
         cov_old = data_manager.coverage_from_storage(session, cfg, as_of=d_old)
         fresh_old = data_manager._compute_coverage_uncached(session, cfg, as_of=d_old)
-        assert cov_old == fresh_old
+        assert cov_old["coverage_status"] == "current"  # iter-27: a real persisted row, not a stale/sentinel
+        assert _strip_coverage_status(cov_old) == fresh_old
         assert cov_old["symbol_count"] == 1  # REAL coverage (the sentinel would be 0) — the regression
         assert cov_old["universe_asof"] == d_old.isoformat()
         # ...and the current/latest stamp is still served correctly too (two distinct rows now exist)
@@ -2506,7 +2522,8 @@ def test_coverage_from_storage_self_heals_explicit_legacy_historical_asof(two_sn
         # (1) explicit historical as-of WITH a real ScannerRun, no row -> REAL coverage + self-heal to storage
         cov = data_manager.coverage_from_storage(session, cfg, as_of=d_old)
         fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=d_old)
-        assert cov == fresh
+        assert cov["coverage_status"] == "current"  # iter-27: freshly self-healed under the current stamp
+        assert _strip_coverage_status(cov) == fresh
         assert cov["symbol_count"] == 1 and cov["universe_asof"] == d_old.isoformat()  # not the 0 sentinel
         healed = session.exec(
             select(CoverageSnapshot).where(CoverageSnapshot.asof_key == d_old.isoformat())
@@ -2515,6 +2532,89 @@ def test_coverage_from_storage_self_heals_explicit_legacy_historical_asof(two_sn
         # (2) an explicit as-of to a DATALESS date (no ScannerRun) still serves the honest sentinel
         sentinel = data_manager.coverage_from_storage(session, cfg, as_of=date(2024, 6, 1))
         assert sentinel["symbol_count"] == 0 and sentinel["universe_asof"] is None
+        assert sentinel["coverage_status"] == "not_yet_computed"  # iter-27: genuinely dataless, not stale
+
+
+def test_coverage_from_storage_serves_stale_prior_snapshot_when_default_view_stamp_advances_outside_ingest(
+    tmp_path,
+):
+    """iter-27 (AG-3 ESCALATE fix, TC-5) — reproduces the EXACT root cause the iter-26 evaluator's
+    ESCALATE verdict cited: `_membership_dataset_version` is a GLOBAL stamp bumped by ANY new `ScannerRun`
+    row, including one for a date decades in the past that never changes which date is "latest". Here: (1)
+    a `CoverageSnapshot` row is persisted for the latest date under the CURRENT stamp V1 (a normal ingest);
+    (2) a SECOND `ScannerRun`, for an EARLIER date, is added directly (no ingest finalize hook — modeling a
+    request-path historical `/backtest` create-once view), which bumps `_membership_dataset_version` to V2
+    (`max(scanner_runs.id)`/`count(scanner_runs)` both change) while leaving `_resolve_coverage_asof(None)`
+    resolved to the SAME latest date (unaffected — it tracks `max(ScannerRun.asof_date)`, and the new run
+    is OLDER). The default view's exact-match lookup (latest_key, V2) now misses even though the REAL V1
+    row for that exact `asof_key` still sits in the table (no ingest ran to reclaim it, per
+    `_upsert_coverage_snapshot`'s own "only ingest deletes old-version rows" contract) -- this is the
+    fallback: serve that row's real, non-zero figures labeled `coverage_status: "stale"` with
+    `stale_dataset_version` naming V1, rather than the false all-zero 'not yet computed' sentinel."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'stale_fallback.db'}")
+    create_db_and_tables(engine)
+    d_latest = date(2024, 3, 4)
+    d_old = date(2024, 1, 2)  # earlier than d_latest -- never becomes the resolved "latest" date
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=d_latest, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+        run = ScannerRun(
+            asof_date=d_latest, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
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
+
+    cfg = load_config()
+    with Session(engine) as session:
+        v1 = data_manager._membership_dataset_version(session, cfg)
+        real_payload = data_manager.refresh_coverage_snapshot(session, cfg)  # persists under V1
+    assert real_payload["symbol_count"] == 1 and real_payload["universe_asof"] == d_latest.isoformat()
+
+    # A request-path historical create-once view for an OLDER date -- a brand-new ScannerRun row, but NO
+    # ingest finalize hook (mirrors resolved_run's create-once path; never touches coverage_snapshot).
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="AAA", date=d_old, open=2.0, high=2.0, low=2.0, close=2.0, volume=1.0,
+        ))
+        session.add(ScannerRun(
+            asof_date=d_old, created_at=datetime(2024, 1, 2), provider="seed", benchmark="SPY",
+            regime_score=40.0, regime_label="Risk-off", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+
+    with Session(engine) as session:
+        v2 = data_manager._membership_dataset_version(session, cfg)
+        assert v2 != v1  # the stamp advanced from the new (older-date) ScannerRun alone
+        resolved = data_manager._resolve_coverage_asof(session, None, cfg)
+        assert resolved == d_latest  # "latest" is UNCHANGED -- the new run is for an EARLIER date
+        # the exact-match (asof_key=d_latest, dataset_version=v2) row does not exist -- only v1's does
+        assert session.exec(
+            select(CoverageSnapshot).where(
+                CoverageSnapshot.asof_key == d_latest.isoformat(),
+                CoverageSnapshot.dataset_version == v2,
+            )
+        ).first() is None
+
+        served = data_manager.coverage_from_storage(session, cfg, as_of=None)  # the default view
+
+    assert served["coverage_status"] == "stale"
+    assert served["stale_dataset_version"] == v1
+    assert served["stale_computed_at"] is not None
+    # the REAL prior figures -- never the all-zero sentinel for a database that plainly has coverage on file
+    assert served["symbol_count"] == 1 and served["universe_asof"] == d_latest.isoformat()
+    assert _strip_coverage_status(served) == real_payload
 
 
 # ==================================================================================================
diff --git a/apps/backend/tests/test_forward_testing_concurrency.py b/apps/backend/tests/test_forward_testing_concurrency.py
index 9e992fee..e2e49629 100644
--- a/apps/backend/tests/test_forward_testing_concurrency.py
+++ b/apps/backend/tests/test_forward_testing_concurrency.py
@@ -681,6 +681,122 @@ def test_iter19_concurrent_missing_run_backtest_calls_no_duplicate_rows_and_roll
     )
 
 
+# ======================================================================================================
+# ops-hardening iter-27 (AG-3/AG-8 ESCALATE fix) — closes the mid-loop autoflush race the test above's OWN
+# docstring explicitly carved out as "a separate, pre-existing finding, out of scope here": SQLAlchemy's
+# default autoflush means one symbol's still-pending `session.add(...)` is actually flushed by the NEXT
+# symbol's `close_on`/`bars_after` READ, so a concurrent writer's already-committed duplicate key raises
+# `IntegrityError` there (`_insert_run_forward_returns:390`, a `close_on(...)` read — the exact traceback
+# shape the iter-26 evaluator's ESCALATE verdict cited), not at an INSERT statement or the final commit.
+# ======================================================================================================
+def test_iter27_insert_run_forward_returns_tolerates_mid_loop_autoflush_collision(tmp_path):
+    """iter-27 TC-3 — a competing `ForwardReturn` row for symbol A's key is committed via a SEPARATE
+    session/connection AFTER this call's own `existing` snapshot was taken (so `needed` still includes
+    it, simulating "a concurrent writer already inserted this key" landing between the idempotency check
+    and this call's own flush). `_insert_run_forward_returns` stages A's now-duplicate row, then symbol
+    B's `close_on` read autoflushes it — the collision this fix catches. Asserts: no exception propagates,
+    exactly ONE row survives for A's key (the concurrent writer's — ours was rolled back), B's own row is
+    genuinely deferred (not silently dropped forever — the next call's fresh `existing` re-read would find
+    it missing and retry it, per the module's established idempotent-retry design), and a THIRD symbol C
+    (processed AFTER the collision point) still gets its own row inserted — proving the loop truly
+    continues rather than aborting the whole call."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'iter27_mid_loop_race.db'}")
+    create_db_and_tables(engine)
+    asof = date(2025, 3, 1)
+    post_date = asof + timedelta(days=1)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        run_id = run.id
+        for symbol in ("AAA", "BBB", "CCC"):
+            session.add(DailyPrice(
+                symbol=symbol, date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
+            ))
+            session.add(DailyPrice(
+                symbol=symbol, date=post_date, open=100.0, high=101.0, low=99.0, close=105.0, volume=1.0,
+            ))
+        session.commit()
+
+    # Simulate "a concurrent writer already inserted this key" — committed via a SEPARATE session/
+    # connection BEFORE this call's own per-symbol loop reaches symbol A, but AFTER the `existing` set
+    # this call is about to use was decided (the caller passes a deliberately stale, empty `existing`
+    # below — exactly what the real race looks like: two callers' OWN idempotency reads both saw the key
+    # as missing before either one wrote). `realized_return` is a distinctive sentinel (0.4242, NOT the
+    # 0.05 this call's own natural computation would produce from the seeded bars) so the assertion below
+    # unambiguously proves the SURVIVING row is the staged one, never a silently re-derived duplicate.
+    with Session(engine) as staging_session:
+        staging_session.add(ForwardReturn(
+            run_id=run_id, symbol="AAA", horizon=1, asof_date=asof, entry_close=100.0,
+            measured_date=post_date, realized_return=0.4242,
+        ))
+        staging_session.commit()
+
+    with Session(engine) as session:
+        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
+        existing: set = set()  # deliberately stale — does NOT yet know about the just-staged AAA row
+        inserted = forward_testing_module._insert_run_forward_returns(
+            session, run, ["AAA", "BBB", "CCC"], horizons=[1], max_h=1, existing=existing,
+        )
+        session.commit()
+
+    with Session(engine) as session:
+        rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
+    by_symbol = {r.symbol: r for r in rows}
+
+    assert len(rows) == len({(r.run_id, r.symbol, r.horizon) for r in rows}), "no duplicate key survived"
+    assert "AAA" in by_symbol  # the concurrent writer's row — exactly one, ours was rolled back
+    assert by_symbol["AAA"].realized_return == 0.4242  # the STAGED writer's row, not a re-derived duplicate
+    assert "BBB" not in by_symbol, (
+        "B's own insert is deferred (not lost) by design — the next call's fresh `existing` read would "
+        "find it genuinely missing and retry it, per this module's established idempotent-retry contract"
+    )
+    assert "CCC" in by_symbol  # processed AFTER the collision point — proves the loop kept going
+    assert inserted == 1  # C only: A's optimistic +1 was undone on rollback, B never got a chance to add
+
+
+def test_iter27_insert_run_forward_returns_propagates_unrelated_integrity_error(tmp_path):
+    """iter-27 TC-4 — the new mid-loop guard's catch is narrow: an `IntegrityError` that does NOT match
+    the targeted `(run_id, symbol, horizon)` UNIQUE-constraint message (a totally different constraint)
+    still propagates unchanged. Faking `close_on` itself (rather than staging a real second constraint) is
+    the simplest deterministic way to prove the narrow match — never a blanket `except IntegrityError`."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine = make_engine(f"sqlite:///{tmp_path / 'iter27_unrelated_integrity_error.db'}")
+    create_db_and_tables(engine)
+    asof = date(2025, 3, 1)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.commit()
+        run_id = run.id
+
+    def _boom_close_on(*_args, **_kwargs):
+        raise IntegrityError("stmt", {}, Exception("NOT NULL constraint failed: some_other_table.col"))
+
+    real_close_on = forward_testing_module.close_on
+    forward_testing_module.close_on = _boom_close_on
+    try:
+        with Session(engine) as session:
+            run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
+            with pytest.raises(IntegrityError, match="NOT NULL constraint failed"):
+                forward_testing_module._insert_run_forward_returns(
+                    session, run, ["AAA"], horizons=[1], max_h=1, existing=set(),
+                )
+    finally:
+        forward_testing_module.close_on = real_close_on
+
+
 # ======================================================================================================
 # ops-hardening iter-20 (J-06/J-07/J-08) — the NEW outer single-flight dispatch guard that takes the
 # historical (`is_latest == False`) carve-out's compute OFF the request thread entirely
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index ac60778e..0b1e0a8c 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -2335,6 +2335,17 @@ export interface DataCoverage {
   // ABSENT from the latest scanner snapshot's scored set (the operator-facing "rebuild to include the new
   // members" signal). Read-only descriptive derivation; absent_count 0 → the UI shows NO banner.
   absent_from_latest_snapshot: AbsentFromLatestSnapshot;
+  // ops-hardening iter-27 (AG-3): honest disclosure of WHICH persisted row this payload reflects.
+  // "current" -- the exact-match row for today's dataset version (unchanged rendering). "stale" -- a
+  // real, previously-computed row for this SAME as-of survives under an OLDER dataset version (e.g. a
+  // request-path historical /backtest create-once view bumped the global stamp without an ingest
+  // running) -- the figures above are that older row's, never fabricated/zeroed. "not_yet_computed" --
+  // genuinely no row exists for any version (the pre-existing all-zero sentinel, byte-unchanged).
+  coverage_status: "current" | "stale" | "not_yet_computed";
+  // Non-null ONLY when coverage_status === "stale": the older dataset_version the figures above reflect.
+  stale_dataset_version: string | null;
+  // Non-null ONLY when coverage_status === "stale": that row's own computed_at (ISO-8601 UTC).
+  stale_computed_at: string | null;
 }
 
 /** J-94 — the per-date coverage diagnostic. For the resolved as-of: the admitted count + the excluded-
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                                          | 2 +-
 runs/goal-session-mcp-loop/state/drift-report.json               | 2 +-
 runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl | 1 +
 runs/goal-session-ops-hardening/telemetry.jsonl                  | 7 +++++++
 runs/goal-session-ops-hardening/trace/.next-step                 | 2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl                | 3 +++
 6 files changed, 14 insertions(+), 3 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
