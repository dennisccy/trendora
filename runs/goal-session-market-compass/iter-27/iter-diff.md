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
index 23179f11..5811af78 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -60,6 +60,19 @@ def compass_engine(tmp_path):
     return engine
 
 
+def _scanner_run_count(engine) -> int:
+    """Read-only row count on `scanner_runs` -- used by the iter-27 tests to prove the reordered route
+    never mints a new `ScannerRun` when a manifest already exists for the resolved as-of."""
+    with Session(engine) as session:
+        return len(session.exec(select(ScannerRun)).all())
+
+
+def _manifest_count(engine) -> int:
+    """Read-only row count on `next_session_manifests` (iter-27 audit, TC-5/TC-9)."""
+    with Session(engine) as session:
+        return len(session.exec(select(NextSessionManifest)).all())
+
+
 def _freeze_frontier(engine, cfg) -> None:
     """iter-3: the route can no longer auto-mint the CURRENT frontier's manifest (J-05 step 7) -- tests
     that exercise the WARM-HIT/served-fields behavior must first simulate the ingest-finalize freeze the
@@ -247,26 +260,29 @@ def test_regenerate_route_mints_version_2_leaves_version_1_untouched(compass_eng
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
@@ -307,15 +323,221 @@ def test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historica
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
+
+
+# --- TC-5 / TC-9 (iter-27 audit: the two test-first contract items the iteration specified but did not
+# actually write — the dev handoff and QA report both claimed them PASS by citing tests that do not
+# assert them). Added by the auditor so the DEFINITION OF DONE's "TC-1..TC-5, TC-9, TC-10 all pass" is
+# backed by executed assertions rather than a structural argument. --------------------------------
+
+
+def test_tc5_create_once_on_get_for_a_historical_asof_with_no_manifest_yet(compass_engine, cfg):
+    """TC-5 (as written in the iter-27 spec): a historical, non-frontier as_of with NO manifest yet and no
+    prior GET. The FIRST call through the reordered route mints exactly one row (`mode: retrospective`);
+    the SECOND adds ZERO further rows. This is the create branch the reorder was most likely to break —
+    it is the only branch that may still create a `ScannerRun` or mint a manifest."""
+    from app.api.compass import compass as compass_route
+
+    with Session(compass_engine) as session:
+        pre = session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
+        ).all()
+    assert pre == []  # no manifest yet, no prior GET
+
+    with Session(compass_engine) as session:
+        first = compass_route("2024-06-01", session)
+    assert first["as_of"] == "2024-06-01"
+    assert first["mode"] == "retrospective"
+    assert first["version"] == 1
+    with Session(compass_engine) as session:
+        after_first = session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
+        ).all()
+    assert len(after_first) == 1  # exactly one row minted
+
+    with Session(compass_engine) as session:
+        second = compass_route("2024-06-01", session)
+    with Session(compass_engine) as session:
+        after_second = session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
+        ).all()
+    assert len(after_second) == 1  # ZERO further rows -- create-once survives the reorder
+    assert second["manifest_hash"] == first["manifest_hash"]
+    assert second["version"] == 1
+
+
+def test_tc5_create_branch_still_runs_when_neither_run_nor_manifest_exists(compass_engine, cfg):
+    """TC-5, harder limb: an as-of that resolves but has NEITHER a `ScannerRun` NOR a manifest. This is the
+    only path on which the route may still create BOTH, and the one the fast-path reorder skips past when
+    a manifest exists — so it must be proven to still fire."""
+    from app.api.compass import compass as compass_route
+
+    with Session(compass_engine) as session:
+        assert session.exec(
+            select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 5))
+        ).first() is None
+        assert session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 5))
+        ).all() == []
+
+    with Session(compass_engine) as session:
+        result = compass_route("2024-06-05", session)
+
+    assert result["as_of"] == "2024-06-05"
+    assert result["mode"] == "retrospective"
+    assert result["version"] == 1
+    with Session(compass_engine) as session:
+        assert session.exec(
+            select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 5))
+        ).first() is not None  # the slow path created the run, exactly as before the reorder
+        assert len(session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 5))
+        ).all()) == 1
+
+
+@pytest.mark.parametrize("frozen_first", [False, True])
+def test_tc9_asof_error_status_codes_are_exact_on_both_branches(compass_engine, cfg, frozen_first):
+    """TC-9 (as written in the iter-27 spec): unparseable -> EXACTLY 422, future -> EXACTLY 400, on BOTH
+    the fast (a manifest already exists for the frontier) and slow (none does) branches. The pre-existing
+    error test asserts only `status_code in (400, 404, 422, 503)` on a single future date, which would
+    pass even if the reorder had changed the mapping; these assert the exact codes and prove no row is
+    written on either error path."""
+    from app.api.compass import compass as compass_route
+
+    if frozen_first:
+        _freeze_frontier(compass_engine, cfg)
+
+    manifests_before = _manifest_count(compass_engine)
+    runs_before = _scanner_run_count(compass_engine)
+
+    with Session(compass_engine) as session:
+        with pytest.raises(HTTPException) as unparseable:
+            compass_route("not-a-date", session)
+    assert unparseable.value.status_code == 422
+    assert unparseable.value.detail
+
+    with Session(compass_engine) as session:
+        with pytest.raises(HTTPException) as future:
+            compass_route("2099-01-01", session)
+    assert future.value.status_code == 400
+    assert future.value.detail
+
+    assert _manifest_count(compass_engine) == manifests_before  # no fabricated row on either error path
+    assert _scanner_run_count(compass_engine) == runs_before
```
