# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 9f6b7cd..82729c9 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -985,20 +985,20 @@ def _coverage_not_yet_computed_payload(cfg: Config) -> dict:
 def _upsert_coverage_snapshot(
     session: Session, asof_key: str, dataset_version: str, payload: dict
 ) -> None:
-    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: prunes any
-    STALE row for this `asof_key` (an older `dataset_version`), then updates the current-stamp row in
-    place if one already exists or inserts a fresh one. Mirrors `market_phase_cached`'s prune-stale-then-
-    write upsert, generalized to also cover a repeat call under the SAME stamp — this is called
-    unconditionally at the end of every successful ingest (not gated behind a cache-miss check, unlike the
-    `*_cached` read-through caches)."""
-    stale = session.exec(
-        select(CoverageSnapshot).where(
-            CoverageSnapshot.asof_key == asof_key,
-            CoverageSnapshot.dataset_version != dataset_version,
-        )
-    ).all()
-    for row in stale:
-        session.delete(row)
+    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: reclaims
+    EVERY row in the table left under a superseded `dataset_version` — ops-hardening iter-3 (B2), widened
+    from the iter-2 original, which pruned only a stale row for THIS SAME `asof_key` and left every OTHER
+    `asof_key`'s row under an old stamp orphaned forever once the dataset version moved on — then updates
+    the current-stamp row in place if one already exists or inserts a fresh one. The reclaim is ONE bounded
+    SQL `DELETE ... WHERE dataset_version != :current` (never a per-row Python scan), so it stays cheap
+    regardless of how many stale `asof_key` rows have accumulated (this table is small — bounded by the
+    handful of distinct as-of dates ever selected — never the multi-million-row `daily_prices` scale AG-8
+    guards against). Mirrors `market_phase_cached`'s prune-stale-then-write upsert, generalized to also
+    cover a repeat call under the SAME stamp — this is called unconditionally at the end of every
+    successful ingest (not gated behind a cache-miss check, unlike the `*_cached` read-through caches).
+    Shared by every caller — the ingest finalize hook's rich backfill/rebuild path AND its fetch/expand
+    path (B1), plus `warmup.py`'s boot safety net — so all benefit automatically from one shared fix."""
+    session.execute(delete(CoverageSnapshot).where(CoverageSnapshot.dataset_version != dataset_version))
 
     existing = session.exec(
         select(CoverageSnapshot).where(
@@ -1043,18 +1043,44 @@ def refresh_coverage_snapshot(session: Session, cfg: Config) -> Optional[dict]:
     """Compute the CURRENT coverage payload (reusing the canonical `_compute_coverage_uncached` verbatim —
     never a second derivation) and persist it as the `CoverageSnapshot` row for the CURRENT `(asof_key,
     dataset_version)` key, upserting idempotently. Called by the ingest finalize hook (unconditionally, on
-    every successful backfill/both/rebuild — including a zero-work re-run) and the boot warm-up safety net
-    (only when no row exists yet for the current stamp). Returns the freshly persisted payload, or `None`
-    on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns None only then; nothing to
-    snapshot yet). The current stamp resolves `None`→latest, so this is `refresh_coverage_snapshot_for` at
-    that resolved date (byte-identical: `_compute_coverage_uncached(as_of=None)` and `(as_of=latest)` both
-    resolve through `_resolve_coverage_asof` to the SAME latest date)."""
+    every successful backfill/both/rebuild — including a zero-work re-run — AND, ops-hardening iter-3 B1,
+    on a successful fetch/expand that the cheap `_coverage_snapshot_is_current` gate below found stale) and
+    the boot warm-up safety net (only when no row exists yet for the current stamp). Returns the freshly
+    persisted payload, or `None` on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns
+    None only then; nothing to snapshot yet). The current stamp resolves `None`→latest, so this is
+    `refresh_coverage_snapshot_for` at that resolved date (byte-identical: `_compute_coverage_uncached
+    (as_of=None)` and `(as_of=latest)` both resolve through `_resolve_coverage_asof` to the SAME latest
+    date)."""
     resolved_asof = _resolve_coverage_asof(session, None, cfg)
     if resolved_asof is None:
         return None
     return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
 
 
+def _coverage_snapshot_is_current(session: Session, cfg: Config) -> bool:
+    """ops-hardening iter-3 (B1) — the cheap "already fresh" gate the fetch/expand finalize branch checks
+    BEFORE ever calling `refresh_coverage_snapshot` (which would invoke the heavy `_compute_coverage_uncached`
+    whole-bar-cache derivation): true iff a `CoverageSnapshot` row already exists for the CURRENT `(asof_key,
+    dataset_version)` key, i.e. the persisted snapshot already reflects this exact dataset version, so a
+    refresh would be redundant. Issues only the SAME cheap resolve `refresh_coverage_snapshot` itself needs
+    (`_resolve_coverage_asof` — a couple of bounded scalar reads, never a table scan) plus one indexed row
+    lookup — it NEVER invokes `_compute_coverage_uncached` (the zero-work fetch call-count contract, TC-2).
+    A wholly-empty DB (`resolved_asof is None`) has nothing to snapshot yet — treated as "already current"
+    (a no-op), mirroring `refresh_coverage_snapshot`'s own no-op contract for that case."""
+    resolved_asof = _resolve_coverage_asof(session, None, cfg)
+    if resolved_asof is None:
+        return True
+    asof_key = resolved_asof.isoformat()
+    dataset_version = _membership_dataset_version(session, cfg)
+    row = session.exec(
+        select(CoverageSnapshot).where(
+            CoverageSnapshot.asof_key == asof_key,
+            CoverageSnapshot.dataset_version == dataset_version,
+        )
+    ).first()
+    return row is not None
+
+
 def _scanner_run_exists(session: Session, asof: date_cls) -> bool:
     """Whether a real `ScannerRun` snapshot exists for exactly this as-of date — the signal that `asof` is
     genuinely-ingested historical data (the app-wide as-of switcher, `GET /api/runs`, only ever offers such
@@ -3764,6 +3790,27 @@ def _run_job(
                         prog.aggregates_refreshed = _refresh_ingest_aggregates(agg_session, cfg, prog)
                 except Exception as exc:  # noqa: BLE001 — non-fatal: never flips a successful job to failed
                     logger.exception("ingest aggregate refresh failed (non-fatal): %s", exc)
+            elif final_status in ("ok", "partial") and (
+                prog.kind in _FETCH_KINDS or prog.kind in _EXPAND_KINDS
+            ):
+                # ops-hardening iter-3 (B1): a pure fetch/expand does not run the rich backfill-style hook
+                # above (no per-date snapshot loop, no market-phase/research-hot-key warm — not asked for
+                # here — `elif` naturally excludes "both", which is ALSO in `_BACKFILL_KINDS` and already
+                # ran through the branch above), but it CAN change the bars/membership manifest
+                # (`_membership_dataset_version`), which silently staled the persisted `coverage_snapshot`
+                # row `GET /api/data`'s default view reads — until this fix, only an unrelated restart or
+                # backfill/rebuild ever refreshed it (audit finding B1). Calls `refresh_coverage_snapshot`
+                # directly (the SAME canonical compute the rich path uses) — never a second derivation —
+                # gated by `_coverage_snapshot_is_current` so a zero-work fetch (the common offline case)
+                # pays no extra compute/write (TC-2). Deliberately does NOT set `prog.aggregates_refreshed`
+                # — that field's existing backfill/both/rebuild-only nullability contract is unchanged
+                # (already gated to null for fetch/expand via `_breakdown_computed`, `_run_detail` above).
+                try:
+                    with Session(eng) as agg_session:
+                        if not _coverage_snapshot_is_current(agg_session, cfg):
+                            refresh_coverage_snapshot(agg_session, cfg)
+                except Exception as exc:  # noqa: BLE001 — non-fatal: never flips a successful job to failed
+                    logger.exception("ingest coverage refresh failed for fetch/expand (non-fatal): %s", exc)
             prog.status = final_status
     except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job (scrubbed)
         prog.status = "failed"
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 4933157..9b02846 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1303,6 +1303,205 @@ def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
     assert this_run["aggregates_refreshed"] is None  # the persisted/served view: null for a fetch kind
 
 
+# ==================================================================================================
+# ops-hardening iter-3 (audit B1/B2): a fetch/expand that changes the bars manifest must ALSO refresh the
+# persisted coverage_snapshot (today only backfill/both/rebuild do) — closing the fetch-then-view gap the
+# iter-2 audit found live: a fully-ingested DB silently kept serving the false all-zero sentinel until an
+# unrelated restart or backfill/rebuild. A zero-work fetch/expand (the common offline case) must pay ZERO
+# extra compute. Stale coverage_snapshot rows under a superseded dataset_version must be reclaimed in one
+# bounded SQL DELETE, across every asof_key, not just the one being written (B2).
+# ==================================================================================================
+def test_fetch_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
+    """TC-1/TC-6 (B1) — given a committed DB with a current-stamp coverage_snapshot row already persisted,
+    when a `fetch` job lands >= 1 new bar (changing `_membership_dataset_version`) and completes, the
+    finalize hook persists a FRESH coverage_snapshot row for the new current stamp, and
+    `coverage_from_storage` (what `GET /api/data`'s default view reads) serves the fresh symbol_count —
+    byte-identical to an independent fresh `_compute_coverage_uncached` call — never the stale pre-fetch
+    value."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_refresh.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 1, 2)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    cfg = load_config()
+
+    with Session(engine) as session:
+        pre_payload = data_manager.refresh_coverage_snapshot(session, cfg)  # the pre-existing current row
+        pre_version = data_manager._membership_dataset_version(session, cfg)
+    assert pre_payload["symbol_count"] == 1  # SPY only, before the fetch
+
+    class _OneBarProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return [Bar(date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0)]
+
+    # J-13: an empty temp seed_dir degrades the fetch target to the small context-only set (fast/small),
+    # exactly the pattern `test_fetch_forced_failure_writes_no_bars_or_snapshots` already relies on.
+    job = create_job("fetch", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_OneBarProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "ok"
+    assert summary["bars_fetched"] > 0
+
+    with Session(engine) as session:
+        new_version = data_manager._membership_dataset_version(session, cfg)
+        assert new_version != pre_version  # real new bars landed -> the stamp actually changed
+
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1  # the stale pre-fetch-stamp row was reclaimed (B2), not left alongside
+        assert rows[0].dataset_version == new_version
+        stored = json.loads(rows[0].payload_json)
+        assert stored["symbol_count"] > 1  # more than SPY alone -- the fresh count, not the stale 1
+
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+        assert stored == fresh  # TC-6: byte-identical to an independent fresh compute
+        served = data_manager.coverage_from_storage(session, cfg, as_of=None)  # GET /api/data's default read
+        assert served == fresh
+
+
+def test_zero_work_fetch_skips_coverage_recompute_and_row_write(tmp_path, monkeypatch):
+    """TC-2 — given the same setup as TC-1 but the fetch lands ZERO new bars (the common offline no-op),
+    `_compute_coverage_uncached` is NEVER invoked (a call-count assertion — the 'already fresh' gate must
+    resolve off the cheap dataset-version comparison + one row lookup alone) and no coverage_snapshot row
+    is written or re-timestamped."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_zero_work.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 1, 2)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    cfg = load_config()
+
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, cfg)  # the pre-existing current-stamp row
+        rows_before = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows_before) == 1
+        computed_at_before = rows_before[0].computed_at
+
+    calls: list[int] = []
+    orig = data_manager._compute_coverage_uncached
+
+    def _counting(*args, **kwargs):
+        calls.append(1)
+        return orig(*args, **kwargs)
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _counting)
+
+    class _EmptyProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return []  # a successful fetch that finds no new bars -- never a fabricated one
+
+    job = create_job("fetch", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_EmptyProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "ok"
+    assert summary["bars_fetched"] == 0
+    assert calls == []  # never invoked -- the skip gate resolved first, off the stamp comparison alone
+
+    with Session(engine) as session:
+        rows_after = session.exec(select(CoverageSnapshot)).all()
+    assert len(rows_after) == 1
+    assert rows_after[0].computed_at == computed_at_before  # untouched -- no re-timestamp
+
+
+def test_fully_failed_fetch_writes_no_coverage_snapshot(tmp_path):
+    """Error case (TESTING REQUIREMENTS) — a fetch that fails for every symbol must not leave a
+    partially-written/inconsistent coverage_snapshot row: `final_status == "failed"` never reaches the new
+    refresh branch (it is gated the same as the existing backfill/rebuild branch: `ok`/`partial` only)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_failed.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+    cfg = load_config()
+
+    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_FailingProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "failed"
+    with Session(engine) as session:
+        assert session.exec(select(CoverageSnapshot)).all() == []
+
+
+def test_stale_dataset_version_rows_pruned_via_one_bulk_delete(tmp_path):
+    """TC-4 (B2) — multiple coverage_snapshot rows under a now-superseded dataset_version, across DIFFERENT
+    asof_keys, are ALL deleted the next time a write detects the dataset version has changed -- via one
+    bounded SQL DELETE (asserted by counting DELETE statements against coverage_snapshot), not a per-row
+    Python scan."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'stale_prune.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        # three rows under an OLD stamp, across three DIFFERENT asof_keys -- today's per-asof_key-only
+        # prune would leave two of these three orphaned forever (the B2 bug).
+        for asof_key in ("2024-01-01", "2024-02-01", "2024-03-01"):
+            session.add(CoverageSnapshot(
+                asof_key=asof_key, dataset_version="old-v1", payload_json="{}",
+                computed_at=datetime(2024, 1, 1),
+            ))
+        session.commit()
+
+    delete_statements: list[str] = []
+
+    def _count_deletes(conn, cursor, statement, parameters, context, executemany):
+        lowered = statement.lower()
+        if "coverage_snapshot" in lowered and lowered.strip().startswith("delete"):
+            delete_statements.append(statement)
+
+    event.listen(engine, "before_cursor_execute", _count_deletes)
+    try:
+        with Session(engine) as session:
+            # a write under a NEW dataset_version, for a FOURTH, different asof_key.
+            data_manager._upsert_coverage_snapshot(session, "2024-04-01", "new-v2", {"fake": "payload"})
+    finally:
+        event.remove(engine, "before_cursor_execute", _count_deletes)
+
+    assert len(delete_statements) == 1  # ONE bounded SQL DELETE -- not a per-row scan
+
+    with Session(engine) as session:
+        rows = session.exec(select(CoverageSnapshot)).all()
+    assert len(rows) == 1  # every old-v1 row (all three asof_keys) reclaimed; only the new row remains
+    assert rows[0].asof_key == "2024-04-01" and rows[0].dataset_version == "new-v2"
+
+
+def test_fetch_coverage_refresh_makes_no_network_call(tmp_path, monkeypatch):
+    """TC-7 (AG-9) — the widened finalize trigger for a fetch that lands a new bar issues ZERO outbound
+    network/socket calls during the whole job (the stub provider itself is offline; the new coverage-
+    refresh branch reuses only DB-backed derivations)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_no_network.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 1, 2)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    cfg = load_config()
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, cfg)
+
+    def _no_network(*_a, **_k):
+        raise AssertionError("unexpected network call during the fetch coverage refresh")
+
+    monkeypatch.setattr(socket.socket, "connect", _no_network)
+
+    class _OneBarProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return [Bar(date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0)]
+
+    job = create_job("fetch", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_OneBarProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "ok"  # completed successfully with zero socket.connect calls
+
+
 # ==================================================================================================
 # iter-2 review (CRITICAL regression): the app-wide as-of switcher (J-93/J-94) must serve REAL coverage
 # for EVERY already-ingested date — not just the DB's single current stamp. Before the fix, only the
@@ -2168,6 +2367,51 @@ def test_expand_kind_is_in_job_kinds():
     assert "expand" in data_manager.JOB_KINDS
 
 
+def test_expand_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
+    """TC-3/TC-6 (B1) — an `expand` job whose bars manifest changes (a new passer's history is added)
+    triggers the SAME fetch-path finalize behavior as a plain fetch: a fresh coverage_snapshot row is
+    persisted for the current stamp, byte-identical to a direct fresh `_compute_coverage_uncached` call."""
+    cfg = load_config()
+    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
+    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
+    # are create-once/isolation/parallelism, not the bounded-density policy).
+    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
+    cfg = cfg.model_copy(update={"scanner": _sc})
+    seed_dir = tmp_path / "seed"
+    _write_pool(seed_dir)
+    engine = make_engine(f"sqlite:///{tmp_path / 'expand_refresh.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 3, 1)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        pre_payload = data_manager.refresh_coverage_snapshot(session, cfg)
+        pre_version = data_manager._membership_dataset_version(session, cfg)
+    assert pre_payload["symbol_count"] == 1  # SPY only, before the expand lands any passer bars
+
+    job = create_job("expand", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_ExpandProvider(),
+        sleep_fn=_noop_sleep, seed_dir=seed_dir,
+    )
+    assert summary["status"] == "partial"  # FETCHFAIL's OHLCV fetch fails; the two passers still land bars
+    assert summary["passers"] == 2
+
+    with Session(engine) as session:
+        new_version = data_manager._membership_dataset_version(session, cfg)
+        assert new_version != pre_version
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1  # the stale pre-expand-stamp row was reclaimed (B2), not left alongside
+        assert rows[0].dataset_version == new_version
+        stored = json.loads(rows[0].payload_json)
+        # SPY + every candidate whose OHLCV fetch succeeded (5 of 6 — FETCHFAIL's fetch itself fails, so it
+        # stores no bar; the other four are OMITTED by the screen but still get their fetched bar stored,
+        # per test_expand_omitted_candidates_contribute_no_member_and_no_fabricated_bar's own contract).
+        assert stored["symbol_count"] == 6
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+        assert stored == fresh  # TC-6: byte-identical to an independent fresh compute
+
+
 class _ExpandCap429Provider(PriceProvider):
     """An expand provider whose OHLCV fetch always succeeds but whose market-cap feed is PERSISTENTLY
     rate-limited — so the screen step pauses the expand gracefully `resumable` (never fabricates a cap)."""
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 92 ++++++++++++++++++++++
 runs/goal-session-mcp-loop/state/drift-report.json |  2 +-
 .../state/preflight-verdict-history.jsonl          |  2 +
 runs/goal-session-ops-hardening/telemetry.jsonl    |  6 ++
 runs/goal-session-ops-hardening/trace/.next-step   |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  3 +
 6 files changed, 105 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
