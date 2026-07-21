# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index ef226f09..43534dca 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -53,8 +53,10 @@ from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
 from app.data_providers.seed_provider import SeedProvider, symbol_to_filename
 from app.db import get_engine
 from app.engine import drift as drift_module
+from app.engine import evidence  # ops-hardening iter-7 (J-06): the finalize hook warms drawdown_expectations
 from app.engine import forward_testing, scanner
 from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
+from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.prices import attach_shared_cache, bar_cache, bars_asof, latest_data_date, prefilled_bar_cache
 from app.engine import universe_resolver
 from app.engine.universe_screen import (
@@ -3047,9 +3049,9 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
-    "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]`
-    ACTUALLY refreshed — never a fabricated category (mirrors the `omitted`/`passers` honesty convention
-    already used elsewhere in this module).
+    "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
+    "drawdown_expectations"]` ACTUALLY refreshed — never a fabricated category (mirrors the
+    `omitted`/`passers` honesty convention already used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -3140,6 +3142,43 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
         logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)
 
+    # ops-hardening iter-7 (J-06 closeout, audit B1): warm the per-claim `drawdown_expectations`
+    # EventStudyCache view slot — the SAME cache slot `build_evidence_payload` looks up lazily via
+    # `forward_testing.compute_drawdown_expectations_cached` on a live `/api/evidence` request. Without
+    # this warm, the FIRST `/evidence` view after any ingest pays a per-claim cold-miss compute (measured
+    # ~73s on the grown live dev DB, reports/perf-budgets.md iter-6 CORRECTION). Mirrors the
+    # `research_hot_keys` block just above: its own top-level try/except (a missing/corrupt ledger file
+    # degrades to zero warm calls — an honest omission, never an exception that aborts the rest of this
+    # finalize hook), the SAME `type == FORWARD_WALK_TYPE` filter `build_evidence_payload` already applies
+    # (a forward-walk record re-scores an existing claim — it is not itself a claim to warm a panel for),
+    # and the SAME `entry.get("claim")` extraction `evidence._claim_row` uses (so the cache subject hash
+    # matches exactly what `/api/evidence` looks up). A `prog.tick()` heartbeat stamps before each claim's
+    # warm call (mirrors the `forward_aggregates` per-horizon tick above), and each claim's own try/except
+    # (log + continue) means one unresolvable/erroring claim never blocks another or fails the ingest job.
+    try:
+        ledger_entries = read_entries(evidence.resolve_ledger_path())
+    except Exception as exc:  # noqa: BLE001 — non-fatal: a missing/corrupt ledger degrades to zero warm calls
+        logger.exception("ingest drawdown-expectations ledger read failed (non-fatal): %s", exc)
+        ledger_entries = []
+
+    drawdown_warmed = False
+    for entry in ledger_entries:
+        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
+            continue
+        claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
+        prog.tick()  # heartbeat stamp before each claim's warm call — see docstring above.
+        try:
+            result = forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)
+            # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an out-of-scope
+            # horizon or an unresolvable cohort returns None honestly and must NOT be reported as refreshed
+            # (mirrors the `market_phase`/`research_hot_keys` "actually did something" convention above).
+            if result is not None:
+                drawdown_warmed = True
+        except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next claim
+            logger.exception("ingest drawdown-expectations warm failed for one claim (non-fatal): %s", exc)
+    if drawdown_warmed:
+        refreshed.append("drawdown_expectations")
+
     return refreshed
 
 
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 0e45a424..005656f7 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -62,12 +62,15 @@ from app.engine.data_manager import (
     SEED_IMPORT_ENV_FLAG,
     SEED_IMPORT_SOURCE_ID,
 )
+from app.engine.evidence import LEDGER_PATH_ENV
 from app.engine.forward_testing import compute_forward_aggregates
+from app.engine.ledger import append_entry
 from app.engine.scoring import score_stocks
 from app.models import (
     CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
+    EventStudyCache,
     ForwardAggregateCache,
     ForwardReturn,
     ImportCheckpoint,
@@ -1227,6 +1230,251 @@ def test_finalize_hook_makes_no_network_call(finalize_hook_engine, monkeypatch):
     assert refreshed  # completed successfully with zero socket.connect calls
 
 
+# ==================================================================================================
+# ops-hardening iter-7 (J-06 closeout, audit B1): the finalize hook's NEW `drawdown_expectations` warm —
+# mirrors the `research_hot_keys`/`forward_aggregates` proofs above, for the per-claim
+# `compute_drawdown_expectations_cached` EventStudyCache view slot `/api/evidence` reads lazily
+# (`build_evidence_payload`). `finalize_hook_engine`'s own sparse data (no `ForwardReturn` rows at all) is
+# reused as-is for the honesty/isolation proofs below (an unresolvable cohort is the natural, not
+# hand-forced, outcome on that fixture); `finalize_hook_drawdown_engine` adds ONE real observation so the
+# "actually warmed" path is proven for real, not merely asserted.
+# ==================================================================================================
+_DD_WARM_HORIZON = 20  # in config.walk_forward.underwater_horizons by default (mirrors DD_H in
+                        # test_forward_testing.py's own compute_drawdown_expectations fixtures).
+
+_DD_LEDGER_CLAIM = {
+    "kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": _DD_WARM_HORIZON,
+    "direction": "positive",
+}
+
+
+def _dd_fake_phase_ctx(as_of_date):
+    """A trivial `phase_context_by_date` stand-in classifying ONE date "Expansion" — just enough for
+    `compute_drawdown_expectations` to resolve a non-empty by-phase cell (mirrors
+    test_forward_testing.py's own `_fake_phase_ctx`, trimmed to a single observation)."""
+    def _ctx(session=None, as_of=None, config=None):
+        ctx = {as_of_date.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}
+        if as_of is None:
+            return dict(ctx)
+        return {k: v for k, v in ctx.items() if date.fromisoformat(k) <= as_of}
+    return _ctx
+
+
+@pytest.fixture()
+def finalize_hook_drawdown_engine(tmp_path, monkeypatch):
+    """Like `finalize_hook_engine`, extended with ONE real `ForwardReturn` row at `_DD_WARM_HORIZON` for
+    the same ticker/date the base fixture's `ScannerResult` already carries a `leadership_score` for, plus
+    a monkeypatched causal phase classification — enough for `compute_drawdown_expectations` /
+    `compute_drawdown_expectations_cached` to resolve a genuine (non-None) payload for a
+    `_DD_LEDGER_CLAIM`-shaped ledger claim."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_dd.db'}")
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
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="AAA", horizon=_DD_WARM_HORIZON, asof_date=d, entry_close=100.0,
+            measured_date=d + timedelta(days=_DD_WARM_HORIZON * 2), realized_return=0.02,
+            max_drawdown=-0.05, underwater_days=2, time_to_recover_days=3,
+        ))
+        session.commit()
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _dd_fake_phase_ctx(d))
+    return engine, d
+
+
+def test_finalize_hook_warms_drawdown_expectations_for_resolvable_claim(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """TC-1 — a non-empty evidence ledger with one resolvable `_DD_LEDGER_CLAIM`-shaped claim: the
+    finalize hook's new warm step appends "drawdown_expectations" to `refreshed`, and an `EventStudyCache`
+    row for the `drawdown_expectations` view exists before the (simulated) job completes."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-warm-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "drawdown_expectations" in refreshed
+    with Session(engine) as session:
+        rows = session.exec(
+            select(EventStudyCache).where(EventStudyCache.view == "drawdown_expectations")
+        ).all()
+    assert len(rows) == 1
+
+
+def test_finalize_hook_drawdown_expectations_byte_identical_to_fresh_compute(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """TC-3 — the warmed `EventStudyCache` payload is byte-identical to a fresh, UNCACHED
+    `compute_drawdown_expectations` call for the same claim (AG-3: storage is re-served, never
+    re-derived)."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-byte-identity-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
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
+def test_finalize_hook_drawdown_expectations_unresolvable_claim_not_reported(
+    finalize_hook_engine, tmp_path, monkeypatch
+):
+    """TC-4 / honesty gate — a ledger claim whose cohort is unresolvable (the tiny `finalize_hook_engine`
+    fixture carries no `ForwardReturn` rows at all, so `compute_drawdown_expectations` legitimately
+    returns None) does not raise, and "drawdown_expectations" is NOT reported as refreshed — an honest
+    omission, never a fabricated category (mirrors the same gating `market_phase`/`research_hot_keys`
+    already apply above). The OTHER, unrelated aggregates still refresh normally — proving this is a
+    per-category honesty gate, not a whole-function failure."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-unresolvable-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert "drawdown_expectations" not in refreshed
+    assert {"coverage", "membership_timeline"} <= set(refreshed)
+
+
+def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """TC-4 — one claim's warm call raising mid-loop is logged and skipped; it never blocks a LATER
+    claim's own warm call, and it never fails the ingest job (no exception propagates out of
+    `_refresh_ingest_aggregates`). Proven by forcing the FIRST of two ledger claims to raise and asserting
+    the SECOND is still attempted and still counts toward `refreshed`."""
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
+
+    real = forward_testing.compute_drawdown_expectations_cached
+    calls = {"n": 0}
+
+    def _raise_first_then_real(session, claim, config=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            raise RuntimeError("forced claim-warm failure")
+        return real(session, claim, config)
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _raise_first_then_real)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-raise-isolation-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 2, "both claims must be attempted — the first's failure must not skip the second"
+    assert "drawdown_expectations" in refreshed  # the SECOND claim's successful warm still counts
+
+
+def test_finalize_hook_drawdown_expectations_missing_ledger_not_reported(
+    finalize_hook_engine, tmp_path, monkeypatch
+):
+    """TC-5 — a missing ledger file is an EMPTY ledger (per `read_entries`'s own documented contract):
+    zero warm calls, "drawdown_expectations" NOT reported as refreshed."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing" / "certified-claims.jsonl"))
+    calls = {"n": 0}
+    real = forward_testing.compute_drawdown_expectations_cached
+
+    def _counting(*args, **kwargs):
+        calls["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _counting)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-empty-ledger-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert calls["n"] == 0
+    assert "drawdown_expectations" not in refreshed
+
+
+def test_finalize_hook_drawdown_expectations_forward_walk_only_ledger_not_reported(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch
+):
+    """TC-5 variant — a ledger containing ONLY a forward-walk monitoring record (no original claim) warms
+    nothing: the SAME `type == FORWARD_WALK_TYPE` filter `build_evidence_payload` applies, so a re-score
+    record is never mistaken for a new claim to warm a panel for."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "type": "forward_walk", "claim": _DD_LEDGER_CLAIM, "as_of": "2024-06-01", "edge": 0.01,
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-forward-walk-only-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "drawdown_expectations" not in refreshed
+
+
+def test_finalize_hook_drawdown_expectations_corrupt_ledger_degrades_gracefully(
+    finalize_hook_engine, tmp_path, monkeypatch
+):
+    """A corrupt (malformed-JSON) ledger file must not abort the whole finalize hook — the new warm
+    step's own top-level try/except around ledger resolution degrades to zero warm calls (an honest
+    omission), and every OTHER aggregate still refreshes normally."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    bad_ledger = tmp_path / "corrupt-ledger.jsonl"
+    bad_ledger.write_text("not valid json\n")
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(bad_ledger))
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-corrupt-ledger-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert "drawdown_expectations" not in refreshed
+    assert {"latest_snapshot", "coverage", "membership_timeline", "market_phase"} <= set(refreshed)
+
+
 # ==================================================================================================
 # ops-hardening iter-4 (F1 fix): the finalize hook's own heartbeat -- `last_progress_at` must advance
 # through the WHOLE finalize tail (not just the main scan loop), or the frontend's stale-heartbeat flag
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 114 +++++++++++++++++++++
 runs/goal-session-mcp-loop/state/drift-report.json |   2 +-
 .../state/preflight-verdict-history.jsonl          |   2 +
 runs/goal-session-ops-hardening/telemetry.jsonl    |   6 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   3 +
 6 files changed, 127 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
