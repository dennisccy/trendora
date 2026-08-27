# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/engine/j11_stage_g_verify.py b/apps/backend/app/engine/j11_stage_g_verify.py
index 957f1bc8..b0da4729 100644
--- a/apps/backend/app/engine/j11_stage_g_verify.py
+++ b/apps/backend/app/engine/j11_stage_g_verify.py
@@ -53,6 +53,17 @@ presence + id + identity + EXACT recorded forward-return count, never zero). Thi
 the two overlapping instructions that is both internally consistent and actually satisfiable. Recorded here
 and in the dev handoff so a reviewer can independently evaluate the same judgment call.
 
+**Fix-mode correction (reviewer FAIL, this same iteration).** The first version of this module computed
+`membership_timeline_reconciled` by testing `membership_timeline_check["disposition"]` against the only two
+strings that field can ever hold -- an unconditional-pass tautology the reviewer caught, compounded by
+`run_j11_stage_g_verify.py` computing and persisting `stage_g_verdict` (and `finalize_stage_g`'s irrevocable
+boundary-deactivation write) BEFORE the one real reconciliation check (`membership_timeline_delete_
+reconciles`) even ran. `stage_g_verdict` now takes a `membership_timeline_deletion_check` argument -- the
+output of the new `confirm_membership_timeline_deletion_matches_verification`, which is genuinely failable
+-- and the CLI script now computes the delete-if-stale action and this confirmation BEFORE calling
+`stage_g_verdict`/`finalize_stage_g`, never after. See both functions' own docstrings for the exact
+semantics, and the dev handoff for the mutation-test proof that the fixed check can actually fail.
+
 Never touches (imports nothing from, calls nothing in that writes): `scanner.py`, `compass.py`,
 `sectors.py`, `scoring.py`, `j10_recovery.py`, or any canonical producer/serving function's CODE. This
 module COMPOSES already-existing, already-tested J-11 functions -- it introduces no second computation of
@@ -765,6 +776,53 @@ def execute_membership_timeline_delete_if_stale(session: Session, *, verificatio
     return {"generated_at": _now_iso(), "deleted": True, "reason": "stale row deleted per verification mismatch"}
 
 
+def confirm_membership_timeline_deletion_matches_verification(
+    *, verification: dict, delete_action: dict, live_row_count_after_action: int,
+) -> dict:
+    """The REAL, failable check `stage_g_verdict` folds into `membership_timeline_reconciled` (fix for the
+    review FAIL: the old code tested `disposition in {"preserve_for_incremental_reuse", "explicit_delete"}`
+    -- the only two strings `verify_membership_timeline_preserved_row` can ever return, so that expression
+    was true unconditionally and proved nothing; its docstring also cited this exact function's name as
+    already existing when no caller had ever computed or passed it in).
+
+    - `disposition == "preserve_for_incremental_reuse"`: nothing needed deleting -- the per-date
+      recompute-and-compare in `verify_membership_timeline_preserved_row` already proved the row correct
+      field-by-field, so this trivially matches.
+    - `disposition == "explicit_delete"`: matches ONLY if `execute_membership_timeline_delete_if_stale`
+      reported `deleted: True` **and** a live, post-action `COUNT(*)` on `membership_timeline_cache` is
+      genuinely `0` -- i.e. the corrective write actually happened AND actually took effect, never merely
+      that the code branched into the delete-if-stale path. A delete that raised and was swallowed
+      upstream, ran against the wrong session, or was rolled back would leave `deleted=False` or the live
+      count `> 0`, and this correctly reports `matches: False` -- which the caller must compute and pass to
+      `stage_g_verdict` BEFORE calling `finalize_stage_g`, so a silently-failed corrective write blocks the
+      FULLY REPAIRED declaration and the boundary-deactivation write instead of being unable to affect it.
+    - Any other `disposition` value: fail-closed (`matches: False`) -- `verify_membership_timeline_
+      preserved_row` should never produce one, but this function does not trust that by construction."""
+    disposition = verification.get("disposition")
+    if disposition == "preserve_for_incremental_reuse":
+        return {
+            "matches": True, "disposition": disposition,
+            "reason": "no delete required -- preserve confirmed by the per-date recompute-and-compare",
+        }
+    if disposition == "explicit_delete":
+        deleted = bool(delete_action.get("deleted"))
+        row_confirmed_absent = live_row_count_after_action == 0
+        matches = deleted and row_confirmed_absent
+        return {
+            "matches": matches, "disposition": disposition,
+            "deleted": deleted, "live_row_count_after_action": live_row_count_after_action,
+            "reason": (
+                "stale row deleted and confirmed absent by a live post-action COUNT(*)" if matches else
+                f"corrective delete did NOT verifiably take effect (deleted={deleted}, "
+                f"live_row_count_after_action={live_row_count_after_action}) -- treating as UNRECONCILED"
+            ),
+        }
+    return {
+        "matches": False, "disposition": disposition,
+        "reason": f"unrecognized disposition {disposition!r} -- treating as UNRECONCILED, fail-closed",
+    }
+
+
 # ================================================================================================
 # Step 2h -- the ~18 named traps (schema/identity/retry family + J-10/J-11 sequencing family)
 # ================================================================================================
@@ -1251,7 +1309,7 @@ def stage_g_verdict(
     manifests: dict,
     audit_evidence_and_user_state: dict,
     cache_dispositions: dict,
-    membership_timeline_check: dict,
+    membership_timeline_deletion_check: dict,
     named_traps: dict,
     write_path_classification: dict,
     evidence_reinterpretation_check: dict,
@@ -1261,16 +1319,18 @@ def stage_g_verdict(
     iter-20/21's flagged-tautology discipline applies here explicitly: every value folded in below is
     itself a REAL, previously-computed, falsifiable result (not re-derived here), and this function's own
     logic is a plain `all(...)` over them -- it introduces no new boolean that could pass by construction.
-    `membership_timeline_check`'s own `ok` is always True BY DESIGN (see its docstring: staleness is
-    reported via `disposition`, never treated as a hard failure, because the pre-approved delete fallback
-    exists precisely to repair it) -- this function additionally requires the delete-if-stale action to
-    have actually been taken whenever a mismatch was found (via the caller-supplied
-    `membership_timeline_deletion_matches_verification` flag), so a mismatch can never silently survive
-    into a PASS verdict."""
-    membership_timeline_reconciled = (
-        membership_timeline_check["disposition"] == "preserve_for_incremental_reuse"
-        or membership_timeline_check["disposition"] == "explicit_delete"
-    )
+
+    FIX (review FAIL, iter-22 fix pass): this function used to take the raw `membership_timeline_check`
+    dict and test `disposition in {"preserve_for_incremental_reuse", "explicit_delete"}` -- the only two
+    strings that dict's `disposition` field can ever hold, so the test was true unconditionally and was not
+    a check at all (confirmed by the reviewer and, separately, by mutation testing -- see the dev handoff).
+    This function now instead takes `membership_timeline_deletion_check`, the dict returned by
+    `confirm_membership_timeline_deletion_matches_verification`, whose `matches` field IS genuinely
+    failable: when the delete-if-stale corrective write was required, `matches` is True only if that write
+    actually happened AND a live post-write `COUNT(*)` confirms the row is really gone -- never merely that
+    the code took that branch. The caller (`run_j11_stage_g_verify.py`) computes this BEFORE calling this
+    function and before `finalize_stage_g`'s boundary-deactivation write, so a corrective write that
+    silently fails now blocks the FULLY REPAIRED declaration instead of being unable to affect it."""
     category_results = {
         "preflight_gate": bool(preflight_gate.get("proceed")),
         "raw_inputs": bool(raw_inputs.get("ok")),
@@ -1279,7 +1339,7 @@ def stage_g_verdict(
         "manifests": bool(manifests.get("ok")),
         "audit_evidence_and_user_state": bool(audit_evidence_and_user_state.get("ok")),
         "cache_dispositions": bool(cache_dispositions.get("ok")),
-        "membership_timeline_reconciled": membership_timeline_reconciled,
+        "membership_timeline_reconciled": bool(membership_timeline_deletion_check.get("matches")),
         "named_traps": bool(named_traps.get("ok")),
         "write_path_classification": bool(write_path_classification.get("ok")),
         "evidence_reinterpretation_check": bool(evidence_reinterpretation_check.get("clean")),
diff --git a/apps/backend/scripts/run_j11_stage_g_verify.py b/apps/backend/scripts/run_j11_stage_g_verify.py
index 26393ff7..6e057947 100644
--- a/apps/backend/scripts/run_j11_stage_g_verify.py
+++ b/apps/backend/scripts/run_j11_stage_g_verify.py
@@ -25,18 +25,25 @@ whichever of Stage G's two honest terminal states verification proves. Sequence:
      audit/evidence/user-state, cache dispositions, the `membership_timeline_cache` B2 per-date
      recompute-and-compare, the 18 named traps, a fresh write-path call-site re-enumeration + classification,
      an evidence-reinterpretation static check, and operational isolation.
-  3. Aggregate verdict (`stage_g_verdict`) -- no boolean permitted to pass by construction.
-  4. The ONE conditional corrective write this iteration may perform outside `finalize_stage_g` itself: if
-     the membership-timeline B2 check found a stale row, delete it (Stage F's own pre-approved fallback) --
-     this happens regardless of the overall verdict (a stale cache row is repaired either way, per the phase
-     spec's own wording: "the membership-timeline delete already covered above if that specific check is
-     what failed" is explicitly still authorized on a FAIL attempt).
+  3. The ONE conditional corrective write this iteration may perform outside `finalize_stage_g` itself: if
+     the membership-timeline B2 check found a stale row, delete it now (Stage F's own pre-approved
+     fallback) -- this happens regardless of the overall verdict (a stale cache row is repaired either way,
+     per the phase spec's own wording: "the membership-timeline delete already covered above if that
+     specific check is what failed" is explicitly still authorized on a FAIL attempt), followed immediately
+     by a live, post-action `COUNT(*)` proving the delete genuinely took effect
+     (`confirm_membership_timeline_deletion_matches_verification`). **This runs BEFORE the aggregate
+     verdict below (review FAIL fix, iter-22 -- was formerly computed only after the verdict/finalize had
+     already run, too late to affect anything) so a corrective write that silently fails can actually block
+     the FULLY REPAIRED declaration.**
+  4. Aggregate verdict (`stage_g_verdict`) -- no boolean permitted to pass by construction; folds in step
+     3's real, failable delete-reconciliation result as `membership_timeline_reconciled`.
   5. `finalize_stage_g` -- the ONE further conditional write: on a full PASS, deactivate (never delete) the
      `j11-incident-recovery` boundary; on any FAIL, zero further writes, boundary stays `active=1`.
   6. Post-write, read-only cross-iteration mutation accounting -- reconciles every changed table's delta
      since iteration 18's pre-Stage-D baseline sweep to exactly Stage D + Stage E + Stage F + this
-     iteration's own two possible conditional writes. Written LAST, alongside the final terminal-outcome
-     block, unconditionally.
+     iteration's own two possible conditional writes, and takes a SECOND, independent confirming
+     measurement of the membership-timeline delete (step 3 already gated the verdict on the first). Written
+     LAST, alongside the final terminal-outcome block, unconditionally.
 
 Usage:
     apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_g_verify.py \\
@@ -119,6 +126,7 @@ OUTPUT_FILENAMES = (
     "j11-stage-g-verify-cache-dispositions.json",
     "j11-stage-g-verify-membership-timeline-check.json",
     "j11-stage-g-verify-membership-timeline-delete-action.json",
+    "j11-stage-g-verify-membership-timeline-deletion-check.json",
     "j11-stage-g-verify-named-traps.json",
     "j11-stage-g-verify-write-path-sites.json",
     "j11-stage-g-verify-write-path-classification.json",
@@ -490,12 +498,49 @@ def main() -> int:
     _write_json(evidence_dir / "j11-stage-g-verify-memory-check.json", memory_check)
     print(f"memory check: vm_peak_mb={memory_check['vm_peak_mb']} within_cap={memory_check['within_cap']}", file=sys.stderr)
 
-    # === Step 4: aggregate verdict ======================================================================
+    # === Step 4: the one conditional corrective write (membership-timeline delete-if-stale) -- MOVED to
+    #             run BEFORE the verdict/finalize (review FAIL fix -- was Step 5, after the verdict/write).
+    #             A corrective write that silently fails must be able to block the FULLY REPAIRED
+    #             declaration; that is impossible if the verdict is computed and the boundary already
+    #             deactivated before this even runs. This action executes regardless of the overall
+    #             verdict, per the phase spec's own wording ("the membership-timeline delete already
+    #             covered above if that specific check is what failed" is explicitly still authorized on a
+    #             FAIL attempt). ================================================================
+    with Session(engine) as session:
+        membership_timeline_delete_action = jsgv.execute_membership_timeline_delete_if_stale(
+            session, verification=membership_timeline_check,
+        )
+    _write_json(evidence_dir / "j11-stage-g-verify-membership-timeline-delete-action.json", membership_timeline_delete_action)
+    print(f"membership timeline delete action: deleted={membership_timeline_delete_action['deleted']}", file=sys.stderr)
+
+    # The real, failable reconciliation check (review FAIL fix -- was only computed post-write in the old
+    # Step 7, too late to affect anything). A fresh live COUNT(*), taken immediately after the delete
+    # action above, proves the write actually took effect rather than merely that the code branched into
+    # the delete-if-stale path.
+    with Session(engine) as session:
+        live_membership_timeline_row_count_after_delete = session.scalar(
+            select(sa_func.count()).select_from(MembershipTimelineCache)
+        )
+    membership_timeline_deletion_check = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification=membership_timeline_check, delete_action=membership_timeline_delete_action,
+        live_row_count_after_action=int(live_membership_timeline_row_count_after_delete or 0),
+    )
+    _write_json(
+        evidence_dir / "j11-stage-g-verify-membership-timeline-deletion-check.json", membership_timeline_deletion_check,
+    )
+    print(
+        f"membership timeline deletion-matches-verification: matches={membership_timeline_deletion_check['matches']}",
+        file=sys.stderr,
+    )
+
+    # === Step 5: aggregate verdict -- now strictly AFTER the delete-if-stale action and its real
+    #             reconciliation check above, so a silently-failed corrective write can flip
+    #             `membership_timeline_reconciled` to False before finalize_stage_g's write runs. =======
     verdict = jsgv.stage_g_verdict(
         preflight_gate=preflight_gate, raw_inputs=raw_inputs, snapshot_scope=snapshot_scope,
         forward_returns=forward_returns, manifests=manifests,
         audit_evidence_and_user_state=audit_evidence_and_user_state, cache_dispositions=cache_dispositions,
-        membership_timeline_check=membership_timeline_check, named_traps=named_traps,
+        membership_timeline_deletion_check=membership_timeline_deletion_check, named_traps=named_traps,
         write_path_classification=write_path_classification,
         evidence_reinterpretation_check=evidence_reinterpretation_check,
         operational_isolation=operational_isolation,
@@ -514,21 +559,16 @@ def main() -> int:
     _write_json(evidence_dir / "j11-stage-g-verify-verdict.json", verdict)
     print(f"STAGE G VERDICT: full_pass={verdict['full_pass']} failing={verdict['failing_categories']}", file=sys.stderr)
 
-    # === Step 5: the one conditional corrective write (membership-timeline delete-if-stale) ============
-    with Session(engine) as session:
-        membership_timeline_delete_action = jsgv.execute_membership_timeline_delete_if_stale(
-            session, verification=membership_timeline_check,
-        )
-    _write_json(evidence_dir / "j11-stage-g-verify-membership-timeline-delete-action.json", membership_timeline_delete_action)
-    print(f"membership timeline delete action: deleted={membership_timeline_delete_action['deleted']}", file=sys.stderr)
-
     # === Step 6: finalize -- the ONE further conditional write on a full PASS ==========================
     with Session(engine) as session:
         finalize = jsgv.finalize_stage_g(session, verdict=verdict)
     _write_json(evidence_dir / "j11-stage-g-verify-finalize.json", finalize)
     print(f"finalize: outcome={finalize['outcome']} boundary_deactivated={finalize['boundary_deactivated']}", file=sys.stderr)
 
-    # === Step 7: post-write, read-only mutation accounting -- written LAST, as final evidence ==========
+    # === Step 7: post-write, read-only mutation accounting -- written LAST, as final evidence. This is
+    #             now a SECOND, independent confirming measurement of the membership-timeline delete (the
+    #             actual gate already ran pre-finalize, in Step 4 above) -- the same dual-instrument idiom
+    #             `_boundary_dump_diff_matches_expectation` already uses for the boundary row. ===========
     with Session(engine) as session:
         live_post_sweep = j11_maintenance.capture_full_table_sweep(session)
         post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
diff --git a/apps/backend/tests/test_j11_stage_g_verify.py b/apps/backend/tests/test_j11_stage_g_verify.py
index 643e7e55..e90c4527 100644
--- a/apps/backend/tests/test_j11_stage_g_verify.py
+++ b/apps/backend/tests/test_j11_stage_g_verify.py
@@ -585,6 +585,49 @@ def test_tc12_membership_timeline_mismatch_flips_disposition_to_explicit_delete(
         assert session.exec(select(MembershipTimelineCache)).first() is None
 
 
+def test_tc12_deletion_confirmed_reconciles_stage_g_verdict_after_a_genuine_repair(engine, cfg):
+    """Closes the loop end-to-end over REAL database state (not hand-constructed dicts, unlike the
+    `test_deletion_check_*`/`test_stage_g_verdict_membership_timeline_*` unit tests above): a genuinely
+    stale row is found, genuinely deleted, and a genuine live post-delete `COUNT(*)` confirms it -- proving
+    the full corrected chain (`verify_membership_timeline_preserved_row` ->
+    `execute_membership_timeline_delete_if_stale` -> `confirm_membership_timeline_deletion_matches_
+    verification` -> `stage_g_verdict`) composes correctly for the exact repair scenario this iteration's
+    own live run actually hit (a genuine B2 mismatch, genuinely corrected)."""
+    target_date = INCIDENT_DATES[0]
+    with Session(engine) as session:
+        run = _mk_run(session, target_date)
+        _mk_result(session, run, "AAA")
+        session.commit()
+        stale_point = {"date": target_date.isoformat(), "size": 999, "entries": ["ZZZ"], "exits": [], "excluded": {}}
+        session.add(MembershipTimelineCache(
+            dataset_version="stub-stamp",
+            payload_json=json.dumps({"candidate_pool_count": 1, "points": [stale_point], "labels": {}}),
+            created_at=datetime.now(timezone.utc),
+        ))
+        session.commit()
+
+    with Session(engine) as session:
+        verification = jsgv.verify_membership_timeline_preserved_row(session, cfg, stage_f_new_dates=[])
+    assert verification["disposition"] == "explicit_delete"
+
+    with Session(engine) as session:
+        delete_action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=verification)
+    assert delete_action["deleted"] is True
+
+    with Session(engine) as session:
+        live_row_count_after = len(session.exec(select(MembershipTimelineCache)).all())
+    assert live_row_count_after == 0  # sanity: the row is genuinely gone, not merely reported as deleted
+
+    deletion_check = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification=verification, delete_action=delete_action, live_row_count_after_action=live_row_count_after,
+    )
+    assert deletion_check["matches"] is True
+
+    verdict = jsgv.stage_g_verdict(**{**_all_pass_inputs(), "membership_timeline_deletion_check": deletion_check})
+    assert verdict["category_results"]["membership_timeline_reconciled"] is True
+    assert verdict["full_pass"] is True
+
+
 def test_membership_timeline_dates_in_stage_f_new_dates_are_never_targeted(engine, cfg):
     """A date Stage F itself recorded as `new_dates` (never previously cached) must be excluded from the
     B2 verification target set -- there is nothing stale to prove about a date that was never cached
@@ -912,7 +955,7 @@ def _all_pass_inputs() -> dict:
         "manifests": {"ok": True},
         "audit_evidence_and_user_state": {"ok": True},
         "cache_dispositions": {"ok": True},
-        "membership_timeline_check": {"disposition": "preserve_for_incremental_reuse"},
+        "membership_timeline_deletion_check": {"matches": True, "disposition": "preserve_for_incremental_reuse"},
         "named_traps": {"ok": True},
         "write_path_classification": {"ok": True},
         "evidence_reinterpretation_check": {"clean": True},
@@ -936,6 +979,7 @@ def test_stage_g_verdict_full_pass_when_every_category_holds():
         ("manifests", {"ok": False}),
         ("audit_evidence_and_user_state", {"ok": False}),
         ("cache_dispositions", {"ok": False}),
+        ("membership_timeline_deletion_check", {"matches": False, "disposition": "explicit_delete"}),
         ("named_traps", {"ok": False}),
         ("write_path_classification", {"ok": False}),
         ("evidence_reinterpretation_check", {"clean": False}),
@@ -943,21 +987,105 @@ def test_stage_g_verdict_full_pass_when_every_category_holds():
     ],
 )
 def test_stage_g_verdict_fails_when_any_single_category_fails(category, broken_value):
+    """The full 12-category tautology guard (review FAIL fix -- the old 11-case list deliberately EXCLUDED
+    the membership-timeline category, the exact gap that let its unconditional-pass bug through review).
+    Every one of `stage_g_verdict`'s 12 `category_results` keys is now covered here: flipping any ONE
+    input, including this one, must flip the verdict."""
     inputs = _all_pass_inputs()
     inputs[category] = broken_value
     verdict = jsgv.stage_g_verdict(**inputs)
     assert verdict["full_pass"] is False
-    assert category in verdict["failing_categories"]
+    # the `membership_timeline_deletion_check` PARAMETER feeds the `membership_timeline_reconciled`
+    # CATEGORY key (pre-existing asymmetry: every other parameter name already equals its category key).
+    expected_failing_category = (
+        "membership_timeline_reconciled" if category == "membership_timeline_deletion_check" else category
+    )
+    assert expected_failing_category in verdict["failing_categories"]
 
 
-def test_stage_g_verdict_membership_timeline_explicit_delete_is_still_a_pass_category():
-    """A stale row that got correctly caught-and-deleted is a SUCCESSFUL repair, not a failure -- the
-    disposition itself (never a raw boolean) carries the signal, and either legitimate disposition value
-    keeps this category passing."""
+def test_stage_g_verdict_membership_timeline_reconciled_when_deletion_confirmed_after_explicit_delete():
+    """A stale row that got correctly caught, deleted, AND confirmed gone by a live post-action COUNT(*)
+    is a SUCCESSFUL repair -- `membership_timeline_reconciled` is real evidence of the confirmed outcome,
+    never the mere fact that `disposition` held one of its two possible strings."""
     inputs = _all_pass_inputs()
-    inputs["membership_timeline_check"] = {"disposition": "explicit_delete"}
+    inputs["membership_timeline_deletion_check"] = {
+        "matches": True, "disposition": "explicit_delete", "deleted": True, "live_row_count_after_action": 0,
+    }
     verdict = jsgv.stage_g_verdict(**inputs)
     assert verdict["category_results"]["membership_timeline_reconciled"] is True
+    assert verdict["full_pass"] is True
+
+
+def test_stage_g_verdict_membership_timeline_NOT_reconciled_when_corrective_delete_silently_fails():
+    """The exact scenario the review's CRITICAL finding named: `disposition == "explicit_delete"` (a
+    corrective write was required) but the write did not verifiably take effect (`matches: False`) --
+    `membership_timeline_reconciled` must be False and the overall verdict must FAIL, never silently pass
+    through to a FULLY REPAIRED declaration and the boundary-deactivation write."""
+    inputs = _all_pass_inputs()
+    inputs["membership_timeline_deletion_check"] = {
+        "matches": False, "disposition": "explicit_delete", "deleted": False, "live_row_count_after_action": 1,
+    }
+    verdict = jsgv.stage_g_verdict(**inputs)
+    assert verdict["category_results"]["membership_timeline_reconciled"] is False
+    assert verdict["full_pass"] is False
+    assert "membership_timeline_reconciled" in verdict["failing_categories"]
+
+
+# =======================================================================================================
+# confirm_membership_timeline_deletion_matches_verification -- the real, failable check itself
+# (review FAIL fix: proves the fixed check can actually fail, closing the mutation-bar gap the coordinator
+# flagged -- only 2 of 12 acceptance checks were mutation-tested in the original submission).
+# =======================================================================================================
+
+
+def test_deletion_check_preserve_disposition_trivially_matches_with_no_delete_action_needed():
+    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification={"disposition": "preserve_for_incremental_reuse"},
+        delete_action={"deleted": False, "reason": "nothing to delete"},
+        live_row_count_after_action=1,  # the preserved row is still there -- correctly irrelevant here
+    )
+    assert result["matches"] is True
+
+
+def test_deletion_check_explicit_delete_matches_when_deleted_true_and_row_confirmed_absent():
+    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification={"disposition": "explicit_delete"},
+        delete_action={"deleted": True, "reason": "stale row deleted per verification mismatch"},
+        live_row_count_after_action=0,
+    )
+    assert result["matches"] is True
+
+
+def test_deletion_check_explicit_delete_does_NOT_match_when_delete_action_never_reported_deleted():
+    """The delete-if-stale action never actually ran the DELETE (e.g. it raised and was swallowed, or ran
+    against the wrong session) -- `deleted=False` even though the disposition said a delete was required."""
+    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification={"disposition": "explicit_delete"},
+        delete_action={"deleted": False, "reason": "row already absent"},
+        live_row_count_after_action=0,
+    )
+    assert result["matches"] is False
+
+
+def test_deletion_check_explicit_delete_does_NOT_match_when_row_survives_the_delete():
+    """The critical silent-failure scenario: the delete action REPORTED `deleted=True`, but a live,
+    independent post-action COUNT(*) still finds the row present (e.g. a rolled-back transaction, a session
+    that never committed, or a stale read) -- this must NOT be treated as a successful repair."""
+    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification={"disposition": "explicit_delete"},
+        delete_action={"deleted": True, "reason": "stale row deleted per verification mismatch"},
+        live_row_count_after_action=1,
+    )
+    assert result["matches"] is False
+
+
+def test_deletion_check_unrecognized_disposition_fails_closed():
+    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification={"disposition": "not_a_real_disposition"},
+        delete_action={"deleted": False},
+        live_row_count_after_action=0,
+    )
+    assert result["matches"] is False
 
 
 # =======================================================================================================
@@ -1223,19 +1351,30 @@ def test_full_end_to_end_stage_g_shaped_fixture_reaches_fully_repaired(tmp_path,
     )
     assert pre_write_accounting["ok"] is True
 
+    # The delete-if-stale action and its real reconciliation check now run BEFORE stage_g_verdict /
+    # finalize_stage_g (review FAIL fix) -- mirrors the corrected script ordering exactly, so this
+    # end-to-end fixture exercises the SAME sequence the live CLI script now runs, not the buggy one.
+    with Session(fixture_engine) as session:
+        delete_action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=membership)
+    assert delete_action["deleted"] is False  # confirmed fresh, nothing to delete
+
+    with Session(fixture_engine) as session:
+        live_membership_row_count_after_delete = len(session.exec(select(MembershipTimelineCache)).all())
+    deletion_check = jsgv.confirm_membership_timeline_deletion_matches_verification(
+        verification=membership, delete_action=delete_action,
+        live_row_count_after_action=live_membership_row_count_after_delete,
+    )
+    assert deletion_check["matches"] is True
+
     verdict = jsgv.stage_g_verdict(
         preflight_gate=preflight_gate, raw_inputs=raw_inputs, snapshot_scope=snapshot_scope,
         forward_returns=forward_returns, manifests=manifests, audit_evidence_and_user_state=audit,
-        cache_dispositions=caches, membership_timeline_check=membership, named_traps=traps,
+        cache_dispositions=caches, membership_timeline_deletion_check=deletion_check, named_traps=traps,
         write_path_classification=write_path_classification, evidence_reinterpretation_check=reinterpretation,
         operational_isolation=isolation,
     )
     assert verdict["full_pass"] is True, verdict["failing_categories"]
 
-    with Session(fixture_engine) as session:
-        delete_action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=membership)
-    assert delete_action["deleted"] is False  # confirmed fresh, nothing to delete
-
     with Session(fixture_engine) as session:
         finalize = jsgv.finalize_stage_g(session, verdict=verdict)
     assert finalize["outcome"] == "FULLY_REPAIRED"
```

## Excluded-path stat (dependency/lockfile visibility)

 docs/handoffs/goal-market-compass-iter-22-dev.md   | 167 +++++++++++++++++++++
 reports/goal-session-market-compass-index.html     |  29 ++--
 ...arket-compass-iter-22-implementation-summary.md |  39 ++++-
 runs/goal-market-compass-iter-22/status.json       |   4 +-
 .../state/assumptions.md                           |  77 ++++++++++
 .../state/project-story.md                         |  12 +-
 runs/goal-session-market-compass/telemetry.jsonl   |  28 ++++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   6 +
 .../state/preflight-verdict-history.jsonl          |  20 +++
 10 files changed, 360 insertions(+), 24 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
