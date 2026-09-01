# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index 0ca8e0d4..e3613743 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -17,7 +17,8 @@ from sqlmodel import Session, SQLModel, create_engine, select
 from app.config import REPO_ROOT, load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine import compass
-from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun
+from app.engine import market_phase as market_phase_module
+from app.models import DailyPrice, MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun
 
 BOUNDED_TIMEOUT_S = 30
 
@@ -827,6 +828,77 @@ def test_tc23_metadata_only_regeneration_content_hash_equal_manifest_hash_differ
     assert row1.manifest_hash != row2.manifest_hash
 
 
+# --- iter-30 (J-07 closure): a REGENERATED version on a frontier-shaped as-of still yields a populated
+# `state_band` AND `prospective_eligible: False` in the SAME call -- closes the auditor's iter-29 T1 gap.
+# The 11 existing `state_band` tests (test_compass.py / test_api_compass.py) only ever exercise
+# `build_state_band` directly or the `ingest_finalize` freeze path; TC-23's own regenerate coverage above
+# never seeds a prior run with real severity, so its `state_band_json` stays the no-prior-run null shape.
+# This is the exact combination the LIVE production action this iteration performs
+# (`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`) exercises -- mirrored here as a
+# fixture-scoped, isolated-DB unit test (never the live database).
+
+
+@pytest.fixture()
+def frontier_run_with_prior_and_phase(engine, cfg):
+    """Two runs, frontier-shaped: a `DailyPrice` bar dated exactly at the LATER run's as_of (the SAME
+    `frontier_run` convention above -- `_resolve_mode` reads `latest_data_date` against this bar), with
+    `MarketPhaseCache` seeded for BOTH dates (mirrors test_compass.py's `two_runs_with_phase`) so
+    `build_state_band` has a real severity input for every band -- a regenerated version's `state_band`
+    comes out non-null with real words, never the no-prior-run null state."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 7, 1), regime_score=50.0)
+        run_b = _mk_run(session, date(2024, 7, 8), regime_score=58.0)
+        _mk_result(session, run_a.id, "AAA")
+        _mk_result(session, run_b.id, "AAA")
+        session.add(DailyPrice(symbol="SPY", date=date(2024, 7, 8), open=1, high=1, low=1, close=1, volume=1))
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        version = market_phase_module._cache_version(session)
+        for run, severity in ((run_a, 25.0), (run_b, 45.0)):
+            session.add(
+                MarketPhaseCache(
+                    asof_key=run.asof_date.isoformat(), dataset_version=version,
+                    payload_json=json.dumps(
+                        {"available": True, "severity": severity, "phase": "Expansion", "p_bear": 0.15}
+                    ),
+                    created_at=datetime.now(timezone.utc),
+                )
+            )
+        session.commit()
+        return run_b.id
+
+
+def test_regenerate_on_frontier_yields_state_band_and_prospective_eligible_false(
+    engine, cfg, frontier_run_with_prior_and_phase,
+):
+    run_b_id = frontier_run_with_prior_and_phase
+    with Session(engine) as session:
+        run_b = session.get(ScannerRun, run_b_id)
+        v1 = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
+        run_b_asof = run_b.asof_date  # captured INSIDE the session -- commit() inside _freeze_manifest
+        # expires every object bound to this session (SQLAlchemy default expire_on_commit=True), so
+        # `run_b` is unusable once this `with` block exits.
+    assert v1.version == 1
+    assert v1.mode == "at_ingest"  # confirms the fixture IS frontier-shaped, matching the live production call
+
+    with Session(engine) as session:
+        v2 = compass.regenerate_manifest(session, run_b_asof, cfg)
+
+    assert v2.version == 2
+    assert v2.generation_json is not None
+    assert json.loads(v2.generation_json)["producer"] == "regenerate"
+    # TC-6: false because producer == "regenerate" (not "ingest_finalize"), never recomputed at read.
+    assert v2.prospective_eligible is False
+
+    state_band = json.loads(v2.state_band_json)
+    assert set(state_band) == {"regime", "stress", "breadth"}
+    for band in ("regime", "stress", "breadth"):
+        assert state_band[band]["direction_word"] in cfg.compass.vocabulary.direction_words.values()
+        assert state_band[band]["direction_word"] is not None  # real word, never the no-comparison null
+        assert isinstance(state_band[band]["delta"], float)  # real preceding run -> never null
+
+
 # --- TC-24 (disposition partition) ------------------------------------------------------------------
 
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/journey-scripts/J-07.json | 5 ++++-
 runs/goal-session-market-compass/telemetry.jsonl           | 7 +++++++
 runs/goal-session-market-compass/trace/.next-step          | 2 +-
 runs/goal-session-market-compass/trace/trace.jsonl         | 2 ++
 4 files changed, 14 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
