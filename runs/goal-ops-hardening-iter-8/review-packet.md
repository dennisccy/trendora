# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 43534dca..6a9e4ace 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3039,6 +3039,19 @@ def _persist_per_date_coverage_snapshots(
             prog.tick()  # F1 fix (iter-4): per-date heartbeat stamp before this date's heavy coverage compute
             try:
                 refresh_coverage_snapshot_for(session, cfg, d)
+            # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` under real pressure must NOT be
+            # treated like any other per-date failure (the generic `except Exception` below would log it and
+            # immediately retry the NEXT date's allocation, hammering further large allocations instead of
+            # backing off — the confirmed root cause of iter-7's 7+ minute health hang). Caught distinctly,
+            # BEFORE the generic handler: stop this loop immediately (no further dates attempted) and force
+            # freed memory back to the OS before returning to the caller's next independent block.
+            except MemoryError as exc:
+                logger.exception(
+                    "ingest per-date coverage warm aborted at %s — memory pressure, stopping remaining "
+                    "dates in this loop: %s", d, exc,
+                )
+                _release_process_memory()
+                break
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
                 logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
 
@@ -3063,7 +3076,18 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     across BOTH per-date loops, `last_progress_at` freezes for the WHOLE finalize tail once the main scan
     completes (measured ~729s for a full rebuild, `reports/perf-budgets.md` Item L), and the frontend's
     stale-heartbeat flag (`job_progress.heartbeat_stale_seconds`) falsely renders "· possibly stalled" on a
-    perfectly healthy job."""
+    perfectly healthy job.
+
+    ops-hardening iter-8 (J-05 REGRESSION fix): the four per-item warm loops this function drives directly
+    or calls into (per-date coverage in `_persist_per_date_coverage_snapshots`, per-date market-phase, per-
+    horizon forward-aggregates, per-claim drawdown-expectations) each catch `MemoryError` DISTINCTLY from
+    their existing generic `except Exception: log + continue` — on the first `MemoryError`, that ONE loop
+    stops attempting further items (never hammering the next item's allocation under real pressure),
+    `_release_process_memory()` (`gc.collect()` + `malloc_trim`) runs before moving on, and the "actually
+    warmed" honesty gate still reports the category when >= 1 item warmed before the abort. Every other
+    loop's own try/except boundary — and the generic non-memory isolate-and-continue behavior within each
+    loop — is unchanged. Root cause + live before/after measurement: `reports/perf-budgets.md` (Item L
+    iter-8 update)."""
     refreshed: list[str] = []
     prog.tick()  # F1 fix: heartbeat-only stamp at the start of the finalize tail — see docstring above.
 
@@ -3100,6 +3124,17 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
         try:
             market_phase.market_phase_cached(session, d, cfg)
             market_phase_warmed = True
+        # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-date isolate-and-
+        # continue below — a `MemoryError` stops THIS loop immediately (no further dates attempted) and
+        # forces memory back to the OS, instead of hammering the next date's allocation under pressure.
+        # `market_phase_warmed` already honestly reflects any dates that succeeded before the abort.
+        except MemoryError as exc:
+            logger.exception(
+                "ingest market-phase warm aborted at %s — memory pressure, stopping remaining dates in "
+                "this loop: %s", d, exc,
+            )
+            _release_process_memory()
+            break
         except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
             logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
     if market_phase_warmed:
@@ -3122,12 +3157,29 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     try:
         latest_run_date = scanner._latest_stored_run_date(session)
         if latest_run_date is not None:
+            forward_aggregates_warmed = False
             for h in cfg.walk_forward.horizons:
                 prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
                              # compute here can take up to ~35s pre-warm; 5 sequential horizons could
                              # otherwise freeze the heartbeat for minutes without a per-horizon tick).
-                forward_testing.forward_aggregates_cached(session, h, cfg, as_of=latest_run_date)
-            refreshed.append("forward_aggregates")
+                # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` on one horizon is caught
+                # HERE, distinctly, so a horizon that already succeeded before it is still honestly
+                # reported — the outer `except Exception` below (unchanged for every OTHER exception
+                # type) has no per-horizon granularity, so a non-memory failure still aborts the whole
+                # block exactly as before (no regression to that existing behavior). On MemoryError this
+                # loop stops immediately (no further horizons attempted) and forces memory back to the OS.
+                try:
+                    forward_testing.forward_aggregates_cached(session, h, cfg, as_of=latest_run_date)
+                    forward_aggregates_warmed = True
+                except MemoryError as exc:
+                    logger.exception(
+                        "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
+                        "stopping remaining horizons in this loop: %s", h, exc,
+                    )
+                    _release_process_memory()
+                    break
+            if forward_aggregates_warmed:
+                refreshed.append("forward_aggregates")
     except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
         logger.exception("ingest forward-aggregate warm failed (non-fatal): %s", exc)
 
@@ -3174,6 +3226,17 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
             # (mirrors the `market_phase`/`research_hot_keys` "actually did something" convention above).
             if result is not None:
                 drawdown_warmed = True
+        # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-claim isolate-and-
+        # continue below — a `MemoryError` stops THIS loop immediately (no further claims attempted) and
+        # forces memory back to the OS, instead of hammering the next claim's allocation under pressure.
+        # `drawdown_warmed` already honestly reflects any claim that succeeded before the abort.
+        except MemoryError as exc:
+            logger.exception(
+                "ingest drawdown-expectations warm aborted — memory pressure, stopping remaining claims "
+                "in this loop: %s", exc,
+            )
+            _release_process_memory()
+            break
         except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next claim
             logger.exception("ingest drawdown-expectations warm failed for one claim (non-fatal): %s", exc)
     if drawdown_warmed:
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 005656f7..3794e44b 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1475,6 +1475,316 @@ def test_finalize_hook_drawdown_expectations_corrupt_ledger_degrades_gracefully(
     assert {"latest_snapshot", "coverage", "membership_timeline", "market_phase"} <= set(refreshed)
 
 
+# ==================================================================================================
+# ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` inside any of the four finalize-hook warm
+# loops (per-date coverage, per-date market-phase, per-horizon forward-aggregates, per-claim drawdown-
+# expectations) must be caught DISTINCTLY from the existing generic `except Exception: log + continue` —
+# stop that ONE loop immediately (never hammer the next item's allocation under real pressure) while every
+# OTHER loop's own generic-exception isolate-and-continue behavior (proven above/below, e.g.
+# `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises`) stays byte-unchanged. TC-3 = first
+# item raises (zero items warmed, honest omission); TC-5 = a LATER item raises after >=1 succeeded (honest
+# partial report, no further items attempted); TC-4 = a same-process DB read afterward still succeeds (no
+# leaked lock/transaction).
+# ==================================================================================================
+def test_persist_per_date_coverage_memory_error_on_first_date_aborts_loop(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """TC-3 — a MemoryError on the FIRST date passed to the per-date coverage-persist loop stops it
+    immediately: the SECOND date is never attempted, and the function itself does not raise (its caller,
+    `_refresh_ingest_aggregates`, treats this whole call as non-fatal)."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+    calls = {"n": 0}
+
+    def _boom(*_a, **_k):
+        calls["n"] += 1
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _boom)
+    # force BOTH fixture dates into `todo` — neither is the resolved "current" stamp this iteration.
+    monkeypatch.setattr(data_manager, "_resolve_coverage_asof", lambda *a, **k: date(2099, 1, 1))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="cov-mem-first-probe", kind="backfill", start=dates[0], end=dates[-1])
+        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog)  # must not raise
+    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — second date never attempted"
+
+
+def test_persist_per_date_coverage_memory_error_after_partial_success_stops_remaining(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """TC-5 — a MemoryError on the SECOND of two dates: the first date's real persist still happens (a
+    genuine `CoverageSnapshot` row exists for it afterward), and the loop stops there — no further dates
+    attempted."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+    real = data_manager.refresh_coverage_snapshot_for
+    calls = {"n": 0}
+
+    def _succeed_then_boom(session, cfg, d):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            return real(session, cfg, d)
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _succeed_then_boom)
+    monkeypatch.setattr(data_manager, "_resolve_coverage_asof", lambda *a, **k: date(2099, 1, 1))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="cov-mem-partial-probe", kind="backfill", start=dates[0], end=dates[-1])
+        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog)  # must not raise
+    assert calls["n"] == 2, "both dates must be attempted — the second raises, stopping the loop there"
+    with Session(engine) as session:
+        rows = session.exec(
+            select(CoverageSnapshot).where(CoverageSnapshot.asof_key == dates[0].isoformat())
+        ).all()
+    assert len(rows) == 1  # the FIRST date's real persist succeeded before the abort
+
+
+def test_finalize_hook_market_phase_memory_error_on_first_date_aborts_loop(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """TC-3 — a MemoryError on the FIRST date of the market-phase warm loop stops the loop immediately
+    (zero dates warmed): 'market_phase' is honestly omitted from `refreshed` (never a fabricated
+    category), and the finalize hook itself does not raise."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+    calls = {"n": 0}
+
+    def _boom(*_a, **_k):
+        calls["n"] += 1
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="mp-mem-first-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.new_snapshot_dates = dates
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — second date never attempted"
+    assert "market_phase" not in refreshed
+
+
+def test_finalize_hook_market_phase_memory_error_after_partial_success_reports_honestly(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """TC-5 — a MemoryError on the SECOND of two dates: the first date's real warm still counts (honest
+    partial report — 'market_phase' IS in `refreshed`), and the loop stops there."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+    real = market_phase.market_phase_cached
+    calls = {"n": 0}
+
+    def _succeed_then_boom(session, as_of, config=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            return real(session, as_of, config)
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(market_phase, "market_phase_cached", _succeed_then_boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="mp-mem-partial-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.new_snapshot_dates = dates
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 2, "both dates must be attempted — the second raises, stopping the loop there"
+    assert "market_phase" in refreshed  # the FIRST date's real warm still counts honestly
+
+
+def test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds(
+    finalize_hook_multi_date_engine, monkeypatch
+):
+    """TC-4 — after an injected MemoryError aborts the market-phase warm loop mid-finalize-hook, a
+    SUBSEQUENT DB read in the SAME process (a fresh `refresh_coverage_snapshot` call, mirroring what a
+    live `GET /api/data` request would do next) still succeeds — proving no leaked lock/open transaction
+    blocks recovery without a process restart."""
+    engine, dates = finalize_hook_multi_date_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="mp-mem-recovery-probe", kind="backfill", start=dates[0], end=dates[-1])
+        prog.new_snapshot_dates = dates
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise, must not leak a lock
+
+    # a genuine subsequent DB read, in the SAME process, on a FRESH session against the SAME engine —
+    # `refresh_coverage_snapshot` is unrelated to the patched `market_phase_cached`, so this proves the DB
+    # itself (not just an unrelated code path) is still fully readable/writable after the abort.
+    with Session(engine) as session:
+        payload = data_manager.refresh_coverage_snapshot(session, cfg)
+    assert payload is not None
+
+
+def test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-3 — a MemoryError on the FIRST configured horizon stops the forward-aggregates warm loop
+    immediately: 'forward_aggregates' is honestly omitted (zero horizons warmed), and the hook itself does
+    not raise. Unlike the coverage/market-phase/drawdown loops, this loop had NO per-item isolation before
+    this iteration (a single exception aborted the whole block) — a MemoryError now gets its OWN early-
+    abort handling while every OTHER exception type keeps that exact pre-existing whole-block-abort
+    behavior (proven by `test_finalize_hook_never_raises_even_when_everything_fails`, unchanged)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    calls = {"n": 0}
+
+    def _boom(*_a, **_k):
+        calls["n"] += 1
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="fa-mem-first-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — no further horizons attempted"
+    assert "forward_aggregates" not in refreshed
+
+
+def test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-5 — a MemoryError on the SECOND of N configured horizons: the first horizon's real warm still
+    counts (honest partial report — 'forward_aggregates' IS in `refreshed`), and no horizon after the
+    second is attempted."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    n_horizons = len(cfg.walk_forward.horizons)
+    assert n_horizons >= 3, "fixture config must configure >= 3 horizons for this test to be meaningful"
+    real = forward_testing.forward_aggregates_cached
+    calls = {"n": 0}
+
+    def _succeed_then_boom(session, horizon, config=None, *, as_of=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            return real(session, horizon, config, as_of=as_of)
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _succeed_then_boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="fa-mem-partial-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 2, "the loop must stop right after the SECOND (raising) horizon"
+    assert "forward_aggregates" in refreshed  # the FIRST horizon's real warm still counts honestly
+
+
+def test_finalize_hook_drawdown_expectations_memory_error_on_first_claim_aborts_loop(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """TC-3 — a MemoryError on the FIRST of two ledger claims stops the drawdown-expectations warm loop
+    immediately: the SECOND claim is never attempted, and 'drawdown_expectations' is honestly omitted
+    (zero claims warmed)."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    calls = {"n": 0}
+
+    def _boom(*_a, **_k):
+        calls["n"] += 1
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-mem-first-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — second claim never attempted"
+    assert "drawdown_expectations" not in refreshed
+
+
+def test_finalize_hook_drawdown_expectations_memory_error_after_partial_success_reports_honestly(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """TC-5 / TC-7 — a MemoryError on the SECOND of two claims: the FIRST claim's real warm still counts
+    (honest partial report — 'drawdown_expectations' IS in `refreshed`), the second claim is never
+    attempted, and the FIRST claim's persisted payload is byte-identical to a fresh, uncached compute for
+    the same claim (AG-3 — the error-handling change never touches correctness)."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    real = forward_testing.compute_drawdown_expectations_cached
+    calls = {"n": 0}
+
+    def _succeed_then_boom(session, claim, config=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            return real(session, claim, config)
+        raise MemoryError("simulated memory pressure")
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _succeed_then_boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-mem-partial-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 2, "both claims must be attempted — the second raises, stopping the loop there"
+    assert "drawdown_expectations" in refreshed  # the FIRST claim's real warm still counts honestly
+
+    with Session(engine) as session:
+        row = session.exec(
+            select(EventStudyCache).where(EventStudyCache.view == "drawdown_expectations")
+        ).one()
+        stored = json.loads(row.payload_json)
+        fresh = forward_testing.compute_drawdown_expectations(session, _DD_LEDGER_CLAIM, cfg)
+    assert fresh is not None
+    assert stored == fresh
+
+
+def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises_non_memory_unchanged(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """Regression guard — a NON-`MemoryError` exception on the first claim keeps the pre-existing generic
+    isolate-and-continue behavior byte-unchanged by this iteration's diff: the second claim IS still
+    attempted and still counts. (`test_finalize_hook_drawdown_expectations_isolates_claim_that_raises`
+    above proves the same invariant; this is a second, explicit confirmation scoped to this iteration's
+    new MemoryError-specific branch not altering the generic branch.)"""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "forced-raise fixture claim"},
+    })
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
+        "verdict": {"status": "FAIL", "reason": "resolvable fixture claim"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    real = forward_testing.compute_drawdown_expectations_cached
+    calls = {"n": 0}
+
+    def _raise_first_then_real(session, claim, config=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            raise ValueError("forced non-memory claim-warm failure")
+        return real(session, claim, config)
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _raise_first_then_real)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-nonmem-isolation-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 2, "a non-memory exception must NOT abort the loop — both claims still attempted"
+    assert "drawdown_expectations" in refreshed
+
+
 # ==================================================================================================
 # ops-hardening iter-4 (F1 fix): the finalize hook's own heartbeat -- `last_progress_at` must advance
 # through the WHOLE finalize tail (not just the main scan loop), or the frontend's stale-heartbeat flag
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index a9fc998e..d6d57d3c 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -7,13 +7,27 @@ script as a subprocess against the real repo checkout, on an isolated test-only
 with an already-running dev/QA backend on this machine.
 
 TC-15 (RLIMIT_AS + MALLOC_ARENA_MAX), TC-16 (persistent logfile has boot events), TC-17 (a SIGKILL leaves
-the logfile ending abruptly, no clean-shutdown entry)."""
+the logfile ending abruptly, no clean-shutdown entry).
+
+ops-hardening iter-8 (J-05 REGRESSION recovery, TC-1/TC-2) adds
+`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`: a REAL full-universe `rebuild`
+immediately followed by a second heavy `backfill` in the SAME long-lived spawned process — the exact
+scenario that made `GET /api/health` hang 7+ minutes with a worker-thread `MemoryError` in iter-7
+(`runs/goal-session-ops-hardening/iter-7/eval.md`). Runs against a THROWAWAY COPY of the real dev DB
+(never the shared committed file — mirrors `reports/perf-budgets.md` Item L/H's own established
+methodology) via a dedicated `spawned_backend_throwaway_db` fixture. This is a genuinely slow, heavy test
+(a full rebuild alone measures ~16 minutes on the real dev DB's current size, Item L) — an accepted cost
+for a real-process capacity proof, consistent with this project's existing slow real-engine tests (e.g.
+`test_forward_testing.py`'s session-scoped 30-year seed rebuild)."""
 from __future__ import annotations
 
 import hashlib
 import os
+import re
+import shutil
 import signal
 import subprocess
+import threading
 import time
 from dataclasses import dataclass
 from pathlib import Path
@@ -25,12 +39,17 @@ import pytest
 REPO_ROOT = Path(__file__).resolve().parents[3]
 SCRIPT = REPO_ROOT / "scripts" / "start-backend.sh"
 LOG_FILE = REPO_ROOT / "logs" / "backend.log"
+REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
+REAL_CONFIG = REPO_ROOT / "config.yaml"
 
 # A deterministic-but-distinct port range (offset +10000 from the scripts' own 8000-8999 per-project
 # range) so this test never collides with an already-running dev/QA backend on this machine, while still
 # being reproducible across runs of the SAME checkout.
 _offset = int(hashlib.sha1(str(REPO_ROOT).encode()).hexdigest()[:4], 16) % 1000
 _TEST_PORT = 18000 + _offset
+# A THIRD, further-distinct port for the throwaway-DB heavy-ingest test below — never shared with the
+# other tests in this module (which may run in the same session) or with a real dev/QA instance.
+_HEAVY_TEST_PORT = 18500 + _offset
 
 
 def _read_proc_limits_max_address_space_bytes(pid: int) -> int:
@@ -182,6 +201,223 @@ def test_start_backend_logfile_ends_abruptly_after_simulated_crash(spawned_backe
         time.sleep(0.1)
     assert not _pid_alive(pid), "the simulated-crash process should be gone after SIGKILL"
 
+
+# ==================================================================================================
+# ops-hardening iter-8 (J-05 REGRESSION recovery, TC-1/TC-2): a REAL back-to-back heavy ingest — a
+# full-universe `rebuild` immediately followed by a second heavy `backfill` in the SAME long-lived
+# process — must stay under the enforced `memory_cap_mb` `ulimit -v` ceiling with margin, and
+# `GET /api/health` must stay responsive throughout. This is the literal scenario that broke in iter-7
+# (`runs/goal-session-ops-hardening/iter-7/eval.md`: 7+ minute health hang, worker-thread `MemoryError`,
+# manual restart required). Runs on a THROWAWAY COPY of the real dev DB (mirrors `reports/perf-budgets.md`
+# Item L/H's own established methodology) — never the shared committed file.
+# ==================================================================================================
+@dataclass
+class ThrowawayBackend:
+    pid: int
+    port: int
+    scratch_db: Path
+    scratch_config: Path
+
+
+@pytest.fixture()
+def spawned_backend_throwaway_db(tmp_path):
+    """Like `spawned_backend`, but launched against a THROWAWAY COPY of the real dev DB (copied, along
+    with its WAL/SHM sidecars, to `tmp_path`) via a scratch `config.yaml` with ONLY `database.url`
+    rewritten — every other setting (`server.memory_cap_mb`, `malloc_arena_max`, `walk_forward.horizons`,
+    `snapshot_cadence`, etc.) is the REAL committed config, unchanged, so the enforced `ulimit -v` and the
+    finalize hook's warm scope exactly match production. Skips (never fails) if the real dev DB is not
+    present — this test needs real, substantial seed-derived data to be a meaningful capacity proof, not a
+    tiny hand-built fixture."""
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    if not REAL_DB.exists():
+        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to copy for a real capacity measurement")
+
+    scratch_db = tmp_path / "throwaway.db"
+    for suffix in ("", "-wal", "-shm"):
+        src = Path(str(REAL_DB) + suffix)
+        if src.exists():
+            shutil.copy2(src, Path(str(scratch_db) + suffix))
+
+    scratch_config = tmp_path / "throwaway-config.yaml"
+    real_cfg_text = REAL_CONFIG.read_text()
+    new_cfg_text, n = re.subn(
+        r'url:\s*"sqlite:///apps/backend/data/trendora\.db"',
+        f'url: "sqlite:///{scratch_db}"',
+        real_cfg_text,
+        count=1,
+    )
+    assert n == 1, "expected exactly one database.url line to rewrite in the real config.yaml"
+    scratch_config.write_text(new_cfg_text)
+
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_HEAVY_TEST_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_HEAVY_TEST_PORT + 1000)
+    env["TRENDORA_CONFIG"] = str(scratch_config)
+    proc = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        _wait_for_health(_HEAVY_TEST_PORT, timeout=60.0)
+        yield ThrowawayBackend(
+            pid=proc.pid, port=_HEAVY_TEST_PORT, scratch_db=scratch_db, scratch_config=scratch_config
+        )
+    finally:
+        if _pid_alive(proc.pid):
+            os.kill(proc.pid, signal.SIGTERM)
+            deadline = time.monotonic() + 15.0
+            while _pid_alive(proc.pid) and time.monotonic() < deadline:
+                time.sleep(0.2)
+            if _pid_alive(proc.pid):
+                os.kill(proc.pid, signal.SIGKILL)
+        try:
+            proc.wait(timeout=10)
+        except ChildProcessError:
+            pass
+        # tmp_path (pytest's own per-test fixture) is cleaned up by pytest itself; nothing else to remove.
+
+
+def _read_proc_status_kb(pid: int) -> dict[str, int]:
+    """Parse `/proc/<pid>/status`'s VmPeak/VmSize/VmRSS/VmHWM rows -> kB ints. Gone process -> {}."""
+    out: dict[str, int] = {}
+    try:
+        with open(f"/proc/{pid}/status") as fh:
+            for line in fh:
+                for key in ("VmPeak", "VmSize", "VmRSS", "VmHWM"):
+                    if line.startswith(key + ":"):
+                        out[key] = int(line.split()[1])
+    except (FileNotFoundError, ProcessLookupError):
+        return {}
+    return out
+
+
+class _MemSampler(threading.Thread):
+    """Background thread: samples `/proc/<pid>/status` every 0.25s until stopped (mirrors
+    `reports/perf-budgets.md` Item L/H's own sampling cadence)."""
+
+    def __init__(self, pid: int):
+        super().__init__(daemon=True)
+        self.pid = pid
+        # NOTE: named `_stop_event`, NOT `_stop` — `threading.Thread` already owns a private `_stop()`
+        # method internally; shadowing it with an instance attribute breaks `Thread.join()`.
+        self._stop_event = threading.Event()
+        self.samples: list[dict] = []
+
+    def run(self) -> None:
+        while not self._stop_event.is_set():
+            row = _read_proc_status_kb(self.pid)
+            if row:
+                self.samples.append(row)
+            time.sleep(0.25)
+
+    def stop(self) -> None:
+        self._stop_event.set()
+
+    def peak(self, key: str) -> int:
+        vals = [s[key] for s in self.samples if key in s]
+        return max(vals) if vals else 0
+
+
+class _HealthPoller(threading.Thread):
+    """Background thread: polls `GET /api/health` every ~2s until stopped, recording status + elapsed."""
+
+    def __init__(self, port: int):
+        super().__init__(daemon=True)
+        self.port = port
+        self._stop_event = threading.Event()  # see `_MemSampler`'s note on why not `_stop`
+        self.results: list[dict] = []
+
+    def run(self) -> None:
+        while not self._stop_event.is_set():
+            start = time.monotonic()
+            try:
+                resp = httpx.get(f"http://127.0.0.1:{self.port}/api/health", timeout=10.0)
+                self.results.append({"status": resp.status_code, "elapsed": time.monotonic() - start})
+            except Exception as exc:  # noqa: BLE001 — a timeout/refused connect IS the failure signal
+                self.results.append({"status": None, "elapsed": time.monotonic() - start, "error": str(exc)})
+            time.sleep(2.0)
+
+    def stop(self) -> None:
+        self._stop_event.set()
+
+
+def _post_job(port: int, kind: str, start: str, end: str) -> str:
+    resp = httpx.post(
+        f"http://127.0.0.1:{port}/api/data/jobs", json={"kind": kind, "start": start, "end": end},
+        timeout=30.0,
+    )
+    resp.raise_for_status()
+    return resp.json()["job_id"]
+
+
+def _poll_job_to_terminal(port: int, job_id: str, timeout_s: float) -> dict:
+    deadline = time.monotonic() + timeout_s
+    last: dict = {}
+    while time.monotonic() < deadline:
+        resp = httpx.get(f"http://127.0.0.1:{port}/api/data/jobs/{job_id}", timeout=10.0)
+        resp.raise_for_status()
+        last = resp.json()
+        if last.get("status") in ("ok", "partial", "failed"):
+            return last
+        time.sleep(1.0)
+    raise AssertionError(f"job {job_id} did not reach terminal status within {timeout_s}s; last={last}")
+
+
+def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawned_backend_throwaway_db):
+    """TC-1/TC-2 — the literal iter-7 regression scenario, reproduced live and hardened: a full-universe
+    `rebuild` (exercises the finalize hook's per-date coverage/market-phase loops + all configured
+    forward-aggregate horizons + every ledger claim's drawdown-expectations warm at full scale — Item L
+    measured ~378 snapshot dates / ~16 min on this real DB) immediately followed by a second heavy
+    `backfill` for a genuine non-cadence historical date (`2010-07-15` — the SAME date iter-7's browser-qa
+    session used, which the rebuild's monthly/daily cadence does not itself touch, so this creates real new
+    snapshot/forward-return work through the SAME finalize hook a second time) in the SAME spawned process.
+    `/proc/<pid>/status` is sampled every 0.25s throughout both jobs; `GET /api/health` is polled every 2s
+    throughout. Asserts: both jobs reach a terminal (non-`failed`) status, peak VmPeak/VmSize stay under
+    `server.memory_cap_mb` with margin, and every health poll returns HTTP 200 (zero timeouts, zero
+    hangs)."""
+    from app.config import get_config
+
+    backend = spawned_backend_throwaway_db
+    cfg = get_config()
+    cap_kb = cfg.server.memory_cap_mb * 1024
+
+    mem = _MemSampler(backend.pid)
+    mem.start()
+    health = _HealthPoller(backend.port)
+    health.start()
+    try:
+        job_id_1 = _post_job(backend.port, "rebuild", "2024-01-01", "2024-01-01")
+        job1 = _poll_job_to_terminal(backend.port, job_id_1, timeout_s=1800.0)
+        assert job1.get("status") in ("ok", "partial"), f"rebuild job did not succeed: {job1}"
+
+        job_id_2 = _post_job(backend.port, "backfill", "2010-07-15", "2010-07-15")
+        job2 = _poll_job_to_terminal(backend.port, job_id_2, timeout_s=600.0)
+        assert job2.get("status") in ("ok", "partial"), f"second backfill job did not succeed: {job2}"
+
+        time.sleep(3.0)  # settle window so any tail allocation/gc shows up in the sampled peak too
+    finally:
+        mem.stop()
+        mem.join(timeout=5)
+        health.stop()
+        health.join(timeout=5)
+
+    peak_vmpeak = mem.peak("VmPeak")
+    peak_vmsize = mem.peak("VmSize")
+    assert mem.samples, "expected at least one /proc/<pid>/status sample across the whole run"
+    assert peak_vmpeak < cap_kb, (
+        f"peak VmPeak {peak_vmpeak} KB ({peak_vmpeak / 1024:.1f} MB) reached/exceeded the "
+        f"{cap_kb} KB ({cfg.server.memory_cap_mb} MB) ulimit -v cap — the iter-7 regression is NOT resolved"
+    )
+    assert peak_vmsize < cap_kb, f"peak VmSize {peak_vmsize} KB reached/exceeded the {cap_kb} KB cap"
+
+    assert health.results, "expected at least one GET /api/health poll across the whole run"
+    non_200_or_error = [r for r in health.results if r["status"] != 200]
+    assert not non_200_or_error, (
+        f"expected EVERY health poll to be HTTP 200 with zero timeouts/hangs; got "
+        f"{len(non_200_or_error)}/{len(health.results)} non-200-or-error polls: {non_200_or_error[:5]}"
+    )
+
     content_after = LOG_FILE.read_text(errors="replace")[spawned_backend.log_offset_before:]
     assert "start-backend.sh: launching at" in content_after  # this spawn's own boot IS in its own slice
     for phrase in ("Shutting down", "Application shutdown complete", "Finished server process"):
diff --git a/docs/goal.md b/docs/goal.md
index ddd70710..87410343 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -292,6 +292,16 @@ no-ops or arbitrary limits.
 - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
   against the committed seed / local provider fixtures — no live external network calls or
   paid data services may be introduced without an explicit goal.md amendment. *(critical)*
+- **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
+  full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
+  only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
+  scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
+  whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
+  `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
+  marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
+  are a physical constraint of the current host (two instant hardware resets under all-core
+  vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
+  optimize away. *(critical)*
 
 ## Loop mechanics (for the iteration planner)
 
@@ -364,3 +374,13 @@ tables + orphan sweep + existence checks. Nothing global loads at startup.
   persistent backend logfile (today uvicorn writes only to the launching terminal).
 - Job history must survive restarts: the `/data` progress/history panels read persisted
   `data_provider_runs` (extended with per-date exclusion reasons), not in-memory job state.
+- **Host-guard cap enforcement (added 2026-07-21 after two hard-reset incidents):** the existing
+  "launch scripts must enforce declared caps" requirement extends to host-guard: when
+  `project-extensions/host-guard/host-guard.env` declares them, `scripts/start-backend.sh` AND the
+  backend subshell of `scripts/dev.sh` apply an SMT-aware CPU-affinity mask (`taskset -c`) plus
+  BLAS/OMP/numexpr thread caps, and `dev.sh`'s backend subshell mirrors prod's `ulimit -v` +
+  `MALLOC_ARENA_MAX` (never the frontend subshell — `next dev` requires the address space).
+  Values come from `host-guard.env` — no magic numbers in scripts. As of 2026-07-21 `dev.sh`
+  applies no caps at all (confirmed by direct read); closing that gap is in-scope launcher work
+  for the next iteration. The sampler, `run-goal.sh` preflight, and `host-guard.env` itself are
+  owner/framework work, not product scope.
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 1e734448..2ad36ccc 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -65,6 +65,10 @@
 #   AWAITING_GITHUB_AUTH - preflight found no GitHub push access; fix auth, then --resume
 #   AWAITING_DISK    - free disk under the hard floor even after automatic aggressive cleanup;
 #                      free space or run scripts/automation/tmp-doctor.sh --aggressive, then --resume
+#   AWAITING_HOST_GUARD - host-guard preflight failed (hwmon sampler dead and unstartable,
+#                      CPU-affinity wrap absent, or a launcher lost its HOST-GUARD cap block);
+#                      fix per the printed reason (project-extensions/host-guard/README.md),
+#                      then --resume
 #
 # Quota exhaustion is NOT a halt: claude_with_quota_retry transparently sleeps
 # until the quota resets and resumes.
@@ -82,6 +86,37 @@ source "$SCRIPT_DIR/lib/telemetry.sh"
 source "$SCRIPT_DIR/lib/goal-gates.sh"
 source "$SCRIPT_DIR/lib/engine-lock.sh"
 
+# ── Host-guard self-wrap (hardware protection — goal.md AG-10) ─────────────
+# Two instant hardware resets (2026-07-20 19:17, 2026-07-21 10:33) under
+# all-core vectorized ingest bursts: when the project declares host caps
+# (project-extensions/host-guard/host-guard.env), re-exec the ENTIRE engine
+# tree under an SMT-aware CPU-affinity mask (taskset — hard, inherited,
+# instantaneous) plus, when a user manager is reachable, a systemd user scope
+# adding CPUQuota/MemoryHigh/TasksMax as averaging/aggregate backstops. Sits
+# BEFORE extract_cli_arg so "$@" is still the original argv. HOST_GUARD_WRAPPED
+# guards recursion — deliberately NOT CHAIN_-prefixed so the REL-2 ambient
+# snapshot above stays clean. Absent/disabled env file ⇒ no-op (the framework
+# stays project-neutral). Details: project-extensions/host-guard/README.md.
+_HOST_GUARD_ENV_FILE="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+if [[ -z "${HOST_GUARD_WRAPPED:-}" && -f "$_HOST_GUARD_ENV_FILE" ]] \
+   && command -v taskset >/dev/null 2>&1; then
+  # shellcheck disable=SC1090
+  source "$_HOST_GUARD_ENV_FILE"
+  if [[ "${HOST_GUARD_ENABLED:-0}" == "1" && -n "${HOST_GUARD_CPU_LIST:-}" ]]; then
+    export HOST_GUARD_WRAPPED=1
+    if systemd-run --user --scope --quiet -p CPUQuota=10% true 2>/dev/null; then
+      exec systemd-run --user --scope --quiet --collect \
+        --unit "chain-goal-hostguard-$$" \
+        -p "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}" \
+        -p "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}" \
+        -p "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" \
+        taskset -c "$HOST_GUARD_CPU_LIST" "$SCRIPT_DIR/run-goal.sh" "$@"
+    else
+      exec taskset -c "$HOST_GUARD_CPU_LIST" "$SCRIPT_DIR/run-goal.sh" "$@"
+    fi
+  fi
+fi
+
 # Pull --cli (and --force-cli) out of the args BEFORE the existing parse loop,
 # so the loop below sees only its known flags.
 extract_cli_arg "$@" || exit $?
@@ -797,6 +832,99 @@ PY
   exit 0
 }
 
+# ── Host-guard preflight (hardware protection — goal.md AG-10) ─────────────
+# This host hard-reset twice (2026-07-20/21) under all-core vectorized ingest
+# bursts — see project-extensions/host-guard/README.md. When the project
+# declares host caps, the engine must not run unprotected: verify the affinity
+# wrap (top of this script) took effect and the 1 Hz hwmon forensics sampler is
+# alive — auto-starting the sampler first (self-heal, like the disk guard's
+# sweep), pausing (AWAITING_HOST_GUARD, resumable) only when self-heal fails.
+# Absent or disabled host-guard.env ⇒ no-op (framework stays project-neutral).
+_host_guard_mask_width() { # "0-3,8-11" → 8; 0 when unparseable
+  local list="${1:-}" n=0 part a b
+  [[ -n "$list" ]] || { echo 0; return 0; }
+  local -a parts=()
+  IFS=',' read -ra parts <<< "$list"
+  for part in "${parts[@]}"; do
+    if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+      a="${part%-*}"; b="${part#*-}"
+      if (( b >= a )); then n=$(( n + b - a + 1 )); fi
+    elif [[ "$part" =~ ^[0-9]+$ ]]; then
+      n=$(( n + 1 ))
+    fi
+  done
+  echo "$n"
+}
+preflight_host_guard() {
+  local hg_env="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+  [[ -f "$hg_env" ]] || return 0
+  # shellcheck disable=SC1090
+  source "$hg_env"
+  [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+  local sampler="$REPO_ROOT/project-extensions/host-guard/hwmon-log.sh"
+  local fail_reason=""
+
+  # 1. Forensics sampler alive + csv fresh (self-heal: try to start it first).
+  if [[ -f "$sampler" ]]; then
+    if ! bash "$sampler" status >/dev/null 2>&1; then
+      echo "[run-goal] host-guard: hwmon sampler not running — auto-starting."
+      bash "$sampler" start || true
+      sleep 2
+      bash "$sampler" status >/dev/null 2>&1 \
+        || fail_reason="hwmon sampler failed to start (try: bash project-extensions/host-guard/hwmon-log.sh start)"
+    fi
+  else
+    fail_reason="sampler script missing: $sampler"
+  fi
+
+  # 2. Affinity wrap took effect: REAL allowed CPUs ≤ declared mask width.
+  # Read Cpus_allowed_list, not `nproc` — nproc honors OMP_NUM_THREADS, so a
+  # BLAS thread-cap env var would fake a confined engine (false PASS).
+  if [[ -z "$fail_reason" ]]; then
+    local width allowed_list allowed_n
+    width=$(_host_guard_mask_width "${HOST_GUARD_CPU_LIST:-}")
+    allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null)
+    allowed_n=$(_host_guard_mask_width "$allowed_list")
+    if (( width > 0 && allowed_n > width )); then
+      fail_reason="engine not confined to HOST_GUARD_CPU_LIST=${HOST_GUARD_CPU_LIST:-} (Cpus_allowed_list=$allowed_list = $allowed_n CPUs > mask width $width — the taskset wrap did not take effect)"
+    fi
+  fi
+
+  # 3. Launcher cap blocks (AG-10) — enforced only once the launcher caps have
+  # landed (goal.md binding note); until then HOST_GUARD_REQUIRE_MARKERS=0.
+  if [[ -z "$fail_reason" && "${HOST_GUARD_REQUIRE_MARKERS:-0}" == "1" ]]; then
+    local lsc
+    for lsc in "$REPO_ROOT/scripts/dev.sh" "$REPO_ROOT/scripts/start-backend.sh"; do
+      if [[ -f "$lsc" ]] && ! grep -q "HOST-GUARD" "$lsc"; then
+        fail_reason="launcher $(basename "$lsc") lost its HOST-GUARD cap block (AG-10 regression)"
+        break
+      fi
+    done
+  fi
+
+  [[ -n "$fail_reason" ]] || return 0
+  echo "[run-goal] Host-guard preflight failed — pausing (AWAITING_HOST_GUARD)."
+  echo "[run-goal]   reason: $fail_reason"
+  python3 - <<PY
+import json, datetime
+d = json.load(open("$SESSION_JSON"))
+d["status"] = "AWAITING_HOST_GUARD"
+d["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')
+import os as _os, tempfile as _tf
+_fd, _tmp = _tf.mkstemp(dir=_os.path.dirname("$SESSION_JSON") or ".", suffix=".sjtmp")
+with _os.fdopen(_fd, "w") as _f:
+    json.dump(d, _f, indent=2)
+    _f.write("\n")
+_os.replace(_tmp, "$SESSION_JSON")
+PY
+  record_telemetry_event "halt" '{"reason":"AWAITING_HOST_GUARD","detected_at_step":"preflight"}'
+  echo ""
+  echo "Fix the host-guard issue (project-extensions/host-guard/README.md), then resume:"
+  echo "  ./scripts/automation/run-goal.sh --resume --session-id $SESSION_ID"
+  echo "════════════════════════════════════════════════════════════════════"
+  exit 0
+}
+
 # ── Preflight doctor (REL-2) ──────────────────────────────────────────────
 # Advisory BY CONSTRUCTION: the doctor observes and reports; it must never be
 # able to stop a session (a broken doctor gating the engine would invert its
@@ -1084,7 +1212,7 @@ if $( [[ "$AUTO_RELEASE" == "true" ]] && echo "True" || echo "False" ):
 d["push_per_iter"] = $( [[ "$PUSH_PER_ITER" == "true" ]] && echo "True" || echo "False" )
 d["push_branch"] = "$PUSH_BRANCH"
 d["agent_backend"] = "$AGENT_BACKEND"
-if "$RUN_MODE" == "resume" and d.get("status") in ("REGRESSION_HALT", "AWAITING_BLUEPRINT_APPROVAL", "AWAITING_PUMP", "AWAITING_INTENT_REVIEW", "AWAITING_GITHUB_AUTH", "AWAITING_DISK"):
+if "$RUN_MODE" == "resume" and d.get("status") in ("REGRESSION_HALT", "AWAITING_BLUEPRINT_APPROVAL", "AWAITING_PUMP", "AWAITING_INTENT_REVIEW", "AWAITING_GITHUB_AUTH", "AWAITING_DISK", "AWAITING_HOST_GUARD"):
   d["status"] = "in_progress"
 import os as _os, tempfile as _tf
 _fd, _tmp = _tf.mkstemp(dir=_os.path.dirname("$SESSION_JSON") or ".", suffix=".sjtmp")
@@ -1455,6 +1583,10 @@ chain_tmp_janitor
 # (AWAITING_DISK) only when the tmp root's filesystem is still critically low.
 preflight_disk_space
 
+# Host-guard preflight (AG-10): forensics sampler + affinity confinement. The
+# 2026-07-20/21 hard-reset incidents make unprotected engine runs unacceptable.
+preflight_host_guard
+
 # Verify we can push to GitHub before the loop starts (once; fresh + resume).
 # Fails fast / pauses here rather than stalling on a credential prompt mid-run.
 preflight_github_access
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-index.html      |   4 +-
 reports/perf-budgets.md                            | 122 +++++++++++++++
 runs/goal-session-mcp-loop/state/drift-report.json |   2 +-
 .../state/preflight-verdict-history.jsonl          |  10 ++
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 runs/goal-session-ops-hardening/session.json       |  11 +-
 .../state/assumptions.md                           | 164 +++------------------
 .../state/assumptions.md.archive.md                | 150 +++++++++++++++++++
 runs/goal-session-ops-hardening/state/blueprint.md |   8 +-
 runs/goal-session-ops-hardening/summary.md         |  97 +++++++++++-
 runs/goal-session-ops-hardening/telemetry.jsonl    |  24 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   5 +
 16 files changed, 441 insertions(+), 168 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
