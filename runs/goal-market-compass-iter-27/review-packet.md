# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/api/compass.py b/apps/backend/app/api/compass.py
index 40b818b7..c02f39ac 100644
--- a/apps/backend/app/api/compass.py
+++ b/apps/backend/app/api/compass.py
@@ -24,6 +24,7 @@ from app.engine.compass import (
     ManifestNotYetFrozen,
     basis_disclosure,
     get_or_create_manifest,
+    latest_manifest_for_date,
     list_manifest_versions,
     manifest_row_payload,
     regenerate_manifest,
@@ -56,6 +57,21 @@ def _read_time_additions(session: Session, row) -> dict:  # noqa: ANN001 -- Next
 
 @router.get("/compass")
 def compass(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
+    # iter-27 (J-06 step 2's last unmet limb): resolve the as-of STRING to a concrete date FIRST via
+    # `resolved_date` -- this validates/maps as-of errors identically to `resolved_run`'s own internal
+    # ordering (`scanner.resolve_run` calls `resolve_as_of_date` before `run_scan`) but creates nothing
+    # and never self-heals a `ScannerRun`. Only when NO manifest already exists for the resolved date do
+    # we fall through to `resolved_run`/`get_or_create_manifest`, which may still create a run or mint a
+    # manifest -- exactly as before. This keeps a frozen manifest whose source run has since been removed
+    # from ever triggering a silent recompute: `basis_disclosure` (inside `_read_time_additions`) is a
+    # pure read-only `ScannerRun` SELECT, so it can now honestly observe `"unavailable"`.
+    resolved = resolved_date(session, as_of)
+    existing = latest_manifest_for_date(session, resolved)
+    if existing is not None:
+        payload = manifest_row_payload(existing)
+        payload.update(_read_time_additions(session, existing))
+        return payload
+
     run = resolved_run(session, as_of)
     try:
         row = get_or_create_manifest(session, run)
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index 547dc1f5..2b1705db 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1039,6 +1039,23 @@ def _freeze_manifest(
     return row
 
 
+def latest_manifest_for_date(session: Session, as_of: date) -> Optional[NextSessionManifest]:
+    """The LATEST stored `NextSessionManifest` version for `as_of`, or `None` if none exists yet — a
+    pure read: no run lookup, no write, no self-heal. Factored out of `get_or_create_manifest`'s
+    existing-row check (below) so both call sites share the ONE query shape for "does a manifest
+    already exist for this date" (single source, no duplicate query shape for the same fact).
+
+    iter-27 (J-06 step 2's last unmet limb): this lets `GET /api/compass` probe for an existing
+    manifest BEFORE ever resolving/self-healing a `ScannerRun`, so a frozen manifest whose source run
+    has been removed can be served with an honest `basis.status == "unavailable"` instead of the read
+    path silently recreating the run first."""
+    return session.exec(
+        select(NextSessionManifest)
+        .where(NextSessionManifest.as_of == as_of)
+        .order_by(NextSessionManifest.version.desc())
+    ).first()
+
+
 def get_or_create_manifest(
     session: Session, current_run: ScannerRun, config: Optional[Config] = None, *, producer: str = "on_demand_get",
 ) -> NextSessionManifest:
@@ -1052,11 +1069,7 @@ def get_or_create_manifest(
     (non-frontier) `as_of` still create-once-mints here regardless of caller (mode resolves
     `retrospective` since a later run already exists)."""
     cfg = config or get_config()
-    existing = session.exec(
-        select(NextSessionManifest)
-        .where(NextSessionManifest.as_of == current_run.asof_date)
-        .order_by(NextSessionManifest.version.desc())
-    ).first()
+    existing = latest_manifest_for_date(session, current_run.asof_date)
     if existing is not None:
         return existing
 
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
index 23179f11..be70d19a 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -60,6 +60,13 @@ def compass_engine(tmp_path):
     return engine
 
 
+def _scanner_run_count(engine) -> int:
+    """Read-only row count on `scanner_runs` -- used by the iter-27 tests to prove the reordered route
+    never mints a new `ScannerRun` when a manifest already exists for the resolved as-of."""
+    with Session(engine) as session:
+        return len(session.exec(select(ScannerRun)).all())
+
+
 def _freeze_frontier(engine, cfg) -> None:
     """iter-3: the route can no longer auto-mint the CURRENT frontier's manifest (J-05 step 7) -- tests
     that exercise the WARM-HIT/served-fields behavior must first simulate the ingest-finalize freeze the
@@ -247,26 +254,29 @@ def test_regenerate_route_mints_version_2_leaves_version_1_untouched(compass_eng
     assert versions[0].prospective_eligible is False  # historical as_of was never eligible either
 
 
-# --- TC-8 / TC-9 (route-level basis disclosure, iter-26) ------------------------------------------
+# --- TC-8 / TC-9 (route-level basis disclosure, iter-26/iter-27) ------------------------------------
 #
 # test_manifest_invariants.py already covers `basis_disclosure()` directly at the UNIT level (calling it
 # with a hand-built row + session where the current run has been deleted / recreated) --
 # `test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone` and
 # `test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated`. What was NOT previously proven
-# is what `GET /api/compass` ITSELF observes end-to-end when the underlying run is actually removed --
-# the route calls `resolved_run()` (snapshot_serving -> scanner.resolve_run -> scanner.run_scan) BEFORE
-# `get_or_create_manifest`/`basis_disclosure` ever run, and `run_scan` SELF-HEALS: if the requested as_of
-# still resolves to a valid date (any earlier bar exists), a missing `ScannerRun` is silently
-# RECREATED right there, so by the time `basis_disclosure` looks up "the current run for this as_of" it
-# is never actually absent. The test below proves this empirically (RE-VERIFIED, iter-26 -- iter-3's own
-# audit flagged this exact mechanism as finding B2 and it was never fixed): the live route can reach
-# "available" or "rebuilt", but "unavailable" is structurally UNREACHABLE through this endpoint as
-# currently wired -- it is real, correct, unit-tested code that a request can never actually observe.
-# This is a genuine, pre-existing finding (not a regression introduced this iteration, and fixing the
-# self-heal ordering is a deliberate change outside this iteration's IN SCOPE list) -- recorded here and
-# in the dev handoff for reviewer/auditor visibility. What IS safety-critical and IS proven here: the
-# route never 404s, never crashes, and the frozen manifest's payload/version/manifest_hash stay
-# BYTE-IDENTICAL across the self-heal (AG-12) -- only the read-time basis disclosure differs.
+# is what `GET /api/compass` ITSELF observes end-to-end when the underlying run is actually removed.
+#
+# iter-3/iter-26 finding (B2, re-confirmed twice): the route called `resolved_run()`
+# (snapshot_serving -> scanner.resolve_run -> scanner.run_scan) BEFORE `get_or_create_manifest`/
+# `basis_disclosure` ever ran, and `run_scan` SELF-HEALS -- a missing `ScannerRun` was silently
+# RECREATED right there, so `basis_disclosure` could only ever observe "available" or "rebuilt", never
+# "unavailable" -- a real, correct, unit-tested branch a live request could never actually reach (an
+# honesty gap, not coverage, per the iter-26 lesson).
+#
+# iter-27 FIX (this iteration): the route now resolves the as-of date via `resolved_date` (validates
+# only, never self-heals) and looks up `latest_manifest_for_date` FIRST. When a manifest already exists
+# for that date, it is served directly -- `resolved_run`/`run_scan` are never called on that branch, so
+# a removed source run stays removed and `basis_disclosure`'s pure read-only `ScannerRun` SELECT can
+# honestly observe "unavailable". The test below proves this empirically through the real route
+# function (not a new isolated unit branch, per the iter-26 lesson): the route never 404s, never
+# crashes, the frozen manifest's payload/version/manifest_hash stay BYTE-IDENTICAL across the removal
+# (AG-12), and the removed `ScannerRun` stays absent -- no self-heal fires on this branch.
 
 
 def test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run(compass_engine, cfg, monkeypatch, tmp_path):
@@ -307,15 +317,120 @@ def test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historica
         gone = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
     assert gone is None  # confirmed removed immediately before the route call below
 
+    scanner_runs_before = _scanner_run_count(compass_engine)
+
     with Session(compass_engine) as session:
         after = compass_route("2024-06-08", session)  # must NEVER 404, NEVER raise
 
     assert after["manifest_hash"] == before_hash  # AG-12: the frozen manifest payload is byte-unchanged
     assert after["version"] == before_version
-    # the re-verified finding: self-heal recreates the run before basis_disclosure runs, so the live
-    # route observes "rebuilt", never "unavailable" -- see the block docstring above.
-    assert after["basis"]["status"] == "rebuilt"
+    assert after["content_hash"] == before["content_hash"]
+    assert after["selection"] == before["selection"]  # includes candidates, why_not, disposition_tally
+    assert after["comparison_cohort"] == before["comparison_cohort"]
+    assert after["near_threshold_shadow"] == before["near_threshold_shadow"]
+    # iter-27 fix: the route now checks `latest_manifest_for_date` BEFORE ever calling
+    # `resolved_run`/`run_scan`, so the removed source run is never self-healed on this branch, and
+    # `basis_disclosure`'s read-only SELECT honestly observes "unavailable".
+    assert after["basis"]["status"] == "unavailable"
+    assert after["basis"]["detail"]  # a real message, never a silent/empty fabricated detail
+    assert "no longer stored" in after["basis"]["detail"]
 
     with Session(compass_engine) as session:
         healed = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
-    assert healed is not None  # confirms the self-heal actually fired (not merely absent-run tolerance)
+    assert healed is None  # no self-heal fired -- the removed run stays removed
+    assert _scanner_run_count(compass_engine) == scanner_runs_before  # zero new ScannerRun rows minted
+
+
+def test_compass_route_restore_path_flips_basis_back_to_available_or_rebuilt(compass_engine, cfg, monkeypatch, tmp_path):
+    """Restore-path (J-06 step 3): starting from the state left by the removal test above (manifest still
+    serving "unavailable"), re-creating the `ScannerRun` for that as_of with the SAME recorded
+    `created_at` flips `basis.status` back to "available"; re-creating it with a DIFFERENT `created_at`
+    yields "rebuilt" instead. In both cases the manifest's `manifest_hash`/`version`/full payload stay
+    byte-identical to the pre-removal capture."""
+    from app.api.compass import compass as compass_route
+
+    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))
+
+    _freeze_frontier(compass_engine, cfg)
+    with Session(compass_engine) as session:
+        before = compass_route("2024-06-08", session)
+
+    with Session(compass_engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=date(2024, 6, 15), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        session.add(ScannerRun(
+            asof_date=date(2024, 6, 15), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=61.0, regime_label="Expansion", regime_components_json="[]",
+            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+
+    with Session(compass_engine) as session:
+        removed_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
+        session.execute(sa_delete(ScannerResult).where(ScannerResult.run_id == removed_run.id))
+        session.execute(sa_delete(ScannerRun).where(ScannerRun.id == removed_run.id))
+        session.execute(sa_delete(DailyPrice).where(DailyPrice.date == date(2024, 6, 8)))
+        session.commit()
+
+    with Session(compass_engine) as session:
+        gone = compass_route("2024-06-08", session)
+    assert gone["basis"]["status"] == "unavailable"
+
+    recorded_created_at = datetime.fromisoformat(before["generation"]["source_run_created_at"])
+
+    # (a) re-create with the SAME recorded created_at -> "available", bytes unchanged
+    with Session(compass_engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=date(2024, 6, 8), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.add(ScannerRun(
+            asof_date=date(2024, 6, 8), created_at=recorded_created_at, provider="seed", benchmark="SPY",
+            regime_score=58.0, regime_label="Expansion", regime_components_json="[]",
+            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+
+    with Session(compass_engine) as session:
+        restored_same = compass_route("2024-06-08", session)
+    assert restored_same["basis"]["status"] == "available"
+    assert restored_same["manifest_hash"] == before["manifest_hash"]
+    assert restored_same["version"] == before["version"]
+    assert restored_same["content_hash"] == before["content_hash"]
+
+    # remove again and re-create with a DIFFERENT created_at -> "rebuilt", bytes still unchanged
+    with Session(compass_engine) as session:
+        recreated_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
+        session.execute(sa_delete(ScannerRun).where(ScannerRun.id == recreated_run.id))
+        session.commit()
+        session.add(ScannerRun(
+            asof_date=date(2024, 6, 8), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=58.0, regime_label="Expansion", regime_components_json="[]",
+            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+
+    with Session(compass_engine) as session:
+        restored_different = compass_route("2024-06-08", session)
+    assert restored_different["basis"]["status"] == "rebuilt"
+    assert restored_different["manifest_hash"] == before["manifest_hash"]
+    assert restored_different["version"] == before["version"]
+    assert restored_different["content_hash"] == before["content_hash"]
+
+
+def test_compass_route_warm_path_is_inert_two_gets_are_byte_identical_zero_new_runs(compass_engine, cfg):
+    """Warm-path regression: with an existing manifest and its run intact, two consecutive `GET` calls
+    through the route function return byte-identical responses and add zero new `ScannerRun` rows --
+    proves the new fast-path branch (`latest_manifest_for_date` before `resolved_run`) is inert on the
+    common, already-working case."""
+    from app.api.compass import compass as compass_route
+
+    _freeze_frontier(compass_engine, cfg)
+
+    scanner_runs_before = _scanner_run_count(compass_engine)
+
+    with Session(compass_engine) as session:
+        first = compass_route("2024-06-08", session)
+    with Session(compass_engine) as session:
+        second = compass_route("2024-06-08", session)
+
+    assert first == second
+    assert first["basis"]["status"] == "available"
+    assert _scanner_run_count(compass_engine) == scanner_runs_before
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/telemetry.jsonl   | 7 +++++++
 runs/goal-session-market-compass/trace/.next-step  | 2 +-
 runs/goal-session-market-compass/trace/trace.jsonl | 2 ++
 3 files changed, 10 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
