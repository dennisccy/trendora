# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index 82bf77c9..fb921cae 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -459,6 +459,27 @@ def _cohort_row(row: dict, record: Optional[dict], theme_rank_by_slug: dict[str,
     }
 
 
+def _assert_disposition_predicate(comparison_cohort: list[dict], sel) -> None:
+    """goal-market-compass iter-35 (J-12): makes `selection_disposition` truthful BY CONSTRUCTION, not
+    merely by the caller's good behavior -- asserts each label's OWN predicate holds for every cohort row
+    before `evaluate_selection` ever returns: `below_selection_floor` implies leadership below the floor,
+    `excluded_by_cap` implies leadership at or above it. A violation here would mean the partition logic
+    above regressed, not that a row is legitimately mislabeled -- this must never fire in production."""
+    for row in comparison_cohort:
+        disposition = row["selection_disposition"]
+        cleared_floor = row["leadership_score"] >= sel.leadership_min_score
+        if disposition == _DISPOSITION_BELOW_FLOOR:
+            assert not cleared_floor, (
+                f"{row['ticker']}: selection_disposition=below_selection_floor but leadership_score "
+                f"{row['leadership_score']} >= leadership_min_score {sel.leadership_min_score}"
+            )
+        elif disposition == _DISPOSITION_EXCLUDED_BY_CAP:
+            assert cleared_floor, (
+                f"{row['ticker']}: selection_disposition=excluded_by_cap but leadership_score "
+                f"{row['leadership_score']} < leadership_min_score {sel.leadership_min_score}"
+            )
+
+
 def _scan_selection_language(candidates: list[dict], why_not: list[dict], cfg: Config) -> None:
     """TC-35: extend the SAME runtime banned-language guard `build_narrative` already uses to
     `evaluate_selection`'s candidate reason/caution/invalidation/why-not strings — these are about to be
@@ -485,6 +506,12 @@ def _scan_selection_language(candidates: list[dict], why_not: list[dict], cfg: C
 
 
 def _qualifier_checks(row: dict, cfg: Config) -> list[dict]:
+    """goal-market-compass iter-35 (J-12): each check now carries its own `gating` tag -- the SINGLE
+    source of truth for which qualifier is the candidacy gate (`leadership_min_score`, per the goal
+    file's own declared rule and `config.yaml`'s comment) versus an advisory qualifier
+    (`entry_min_score`/`risk_max_score`) that annotates a caution and the eligibility checklist but never
+    removes a row from candidacy. Both `evaluate_selection`'s partition and `_candidate_payload`'s
+    checklist/reason/caution construction read this ONE tag rather than re-deriving it."""
     sel = cfg.compass.selection
     return [
         {
@@ -492,23 +519,32 @@ def _qualifier_checks(row: dict, cfg: Config) -> list[dict]:
             "threshold": sel.leadership_min_score,
             "actual": row["leadership_score"],
             "passed": row["leadership_score"] >= sel.leadership_min_score,
+            "gating": True,
         },
         {
             "condition": "entry_min_score",
             "threshold": sel.entry_min_score,
             "actual": row["entry_quality_score"],
             "passed": row["entry_quality_score"] >= sel.entry_min_score,
+            "gating": False,
         },
         {
             "condition": "risk_max_score",
             "threshold": sel.risk_max_score,
             "actual": row["risk_score"],
             "passed": row["risk_score"] <= sel.risk_max_score,
+            "gating": False,
         },
     ]
 
 
 def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], run: ScannerRun, cfg: Config) -> dict:
+    """goal-market-compass iter-35 (J-12): `checks` may now include an ADVISORY qualifier that FAILED
+    (leadership_min_score is the only gate -- a candidate is guaranteed to have `checks[0]["passed"]`
+    True, but entry_min_score/risk_max_score are never guaranteed). Each check's own `gating` tag (from
+    `_qualifier_checks`, the single source) decides whether it contributes a "clears" REASON (passed) or,
+    for an advisory miss, a CAUTION citing the threshold and the row's actual stored value -- never a
+    reason claiming it clears a qualifier it did not clear."""
     vocab = cfg.compass.vocabulary
     checklist = [
         {
@@ -516,6 +552,7 @@ def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], ru
             "threshold": check["threshold"],
             "actual": check["actual"],
             "verdict": "Pass" if check["passed"] else "Miss",
+            "gating": check["gating"],
         }
         for check in checks
     ]
@@ -529,16 +566,44 @@ def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], ru
         for check in checks
     ]
     sel = cfg.compass.selection
-    reasons = [
-        f"Leadership score {row['leadership_score']:.1f} clears the {sel.leadership_min_score:.1f} floor "
-        f"({vocab.leadership_words[row['leadership_bucket']]}).",
-        f"Entry Quality score {row['entry_quality_score']:.1f} clears the {sel.entry_min_score:.1f} "
-        f"qualifier ({vocab.entry_words[row['entry_quality_bucket']]}).",
-        f"Risk score {row['risk_score']:.1f} clears the {sel.risk_max_score:.1f} ceiling "
-        f"({vocab.risk_words[row['risk_bucket']]}).",
-    ]
-
-    cautions = []
+    reason_by_condition = {
+        "leadership_min_score": (
+            f"Leadership score {row['leadership_score']:.1f} clears the {sel.leadership_min_score:.1f} floor "
+            f"({vocab.leadership_words[row['leadership_bucket']]})."
+        ),
+        "entry_min_score": (
+            f"Entry Quality score {row['entry_quality_score']:.1f} clears the {sel.entry_min_score:.1f} "
+            f"qualifier ({vocab.entry_words[row['entry_quality_bucket']]})."
+        ),
+        "risk_max_score": (
+            f"Risk score {row['risk_score']:.1f} clears the {sel.risk_max_score:.1f} ceiling "
+            f"({vocab.risk_words[row['risk_bucket']]})."
+        ),
+    }
+    # Advisory-qualifier-miss caution text (never shown for the leadership gate -- a candidate always
+    # clears it). States the threshold and the row's ACTUAL stored value only -- no advice-sounding tail
+    # (mirrors the ATR_RISK_BUDGET caution's fact-only posture, TC-34).
+    caution_by_condition = {
+        "entry_min_score": (
+            f"ENTRY_QUALITY_QUALIFIER: Entry Quality score {row['entry_quality_score']:.1f} is below the "
+            f"{sel.entry_min_score:.1f} qualifier ({vocab.entry_words[row['entry_quality_bucket']]}) -- "
+            "advisory only; Leadership alone determines candidacy."
+        ),
+        "risk_max_score": (
+            f"RISK_QUALIFIER: Risk score {row['risk_score']:.1f} is above the {sel.risk_max_score:.1f} "
+            f"ceiling ({vocab.risk_words[row['risk_bucket']]}) -- advisory only; Leadership alone "
+            "determines candidacy."
+        ),
+    }
+    reasons = []
+    qualifier_cautions = []
+    for check in checks:
+        if check["passed"]:
+            reasons.append(reason_by_condition[check["condition"]])
+        elif not check["gating"]:  # a candidate's gating check always passes -- this is always an advisory miss
+            qualifier_cautions.append(caution_by_condition[check["condition"]])
+
+    cautions = list(qualifier_cautions)
     invalidation_note = "No stored invalidation note for this row."
     risk_budget = (detail or {}).get("risk_budget") or {}
     atr = risk_budget.get("atr_pct") or {}
@@ -617,7 +682,12 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
             "sector": sector,
         }
         checks = _qualifier_checks(row, cfg)
-        if all(check["passed"] for check in checks):
+        # goal-market-compass iter-35 (J-12): `leadership_min_score` (the sole `gating: True` check) is
+        # the ONLY candidacy gate -- `entry_min_score`/`risk_max_score` are advisory and never remove a
+        # row from candidacy, matching the goal file's own declared rule and config.yaml's own comment.
+        gating_checks = [check for check in checks if check["gating"]]
+        assert len(gating_checks) == 1, "expected exactly one gating qualifier check (leadership_min_score)"
+        if gating_checks[0]["passed"]:
             qualifying.append((row, checks))
         else:
             failed = [
@@ -655,9 +725,11 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
 
     candidates_empty_reason = None
     if not candidates:
+        # goal-market-compass iter-35 (J-12, TC-7): names ONLY the gating rule -- Entry Quality/Risk are
+        # advisory qualifiers and are never cited here as though they gated inclusion.
         candidates_empty_reason = (
-            f"No stored member cleared the selection rule (Leadership >= {sel.leadership_min_score:.1f}, "
-            f"Entry Quality >= {sel.entry_min_score:.1f}, Risk <= {sel.risk_max_score:.1f}) for this as-of."
+            f"No stored member cleared the Leadership score floor ({sel.leadership_min_score:.1f}) for "
+            "this as-of -- the sole candidacy gate."
         )
 
     # --- iter-3 (J-05/J-06): comparison cohort (every non-candidate member) + near-threshold shadow.
@@ -687,6 +759,12 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
         if sel.shadow.min_score <= row["leadership_score"] < sel.leadership_min_score
     ]
 
+    # goal-market-compass iter-35 (J-12): make `selection_disposition` truthful BY CONSTRUCTION, not
+    # merely by convention -- a per-row runtime check (mirrors `_scan_selection_language`'s
+    # belt-and-suspenders posture) that each label's own predicate actually holds, on every produced
+    # manifest, before it is ever returned.
+    _assert_disposition_predicate(comparison_cohort, sel)
+
     result = {
         "candidates": candidates,
         "why_not": why_not,
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
index b016dfac..db050f4c 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -130,6 +130,69 @@ def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
     ]
 
 
+@pytest.fixture()
+def compass_engine_two_candidates(tmp_path):
+    """goal-market-compass iter-35 (J-12, TC-8): two `ScannerRun` rows each carrying TWO `ScannerResult`
+    rows -- a plain qualifier-clearing name (AAA) plus the real HPE shape (leadership clears the floor,
+    entry qualifier fails) -- so the candidate count is non-trivial (2, not 1) when proving the served
+    `selection.candidates` count agrees with the narrative's focus-count sentence."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'compass_api_two.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for bar_date in (date(2024, 6, 1), date(2024, 6, 8)):
+            session.add(DailyPrice(
+                symbol="SPY", date=bar_date, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+            ))
+        session.commit()
+        for i, (asof, regime_score) in enumerate(((date(2024, 6, 1), 50.0), (date(2024, 6, 8), 58.0))):
+            run = ScannerRun(
+                asof_date=asof, created_at=datetime(2024, 6, 1 + i * 7, tzinfo=timezone.utc),
+                provider="seed", benchmark="SPY", regime_score=regime_score, regime_label="Expansion",
+                regime_components_json="[]", breadth_above_50dma=55.0, breadth_above_200dma=60.0,
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.commit()
+            session.refresh(run)
+            session.add(ScannerResult(
+                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=92.0, leadership_bucket="A",
+                entry_quality_score=85.0, entry_quality_bucket="B", risk_score=40.0, risk_bucket="C",
+                setup_status="Breakout-watch", rank=1,
+                record_json=json.dumps({"ticker": "AAA", "invalidation": {"note": "AAA note"}}),
+            ))
+            session.add(ScannerResult(
+                run_id=run.id, ticker="HPE", name="HPE Corp", leadership_score=92.7, leadership_bucket="A",
+                entry_quality_score=21.5, entry_quality_bucket="E", risk_score=58.9, risk_bucket="C",
+                setup_status="Breakout-watch", rank=2,
+                record_json=json.dumps({"ticker": "HPE", "invalidation": {"note": "HPE note"}}),
+            ))
+            session.commit()
+    return engine
+
+
+def test_candidate_count_agrees_across_selection_and_narrative_focus_sentence(compass_engine_two_candidates, cfg):
+    """iter-35 (J-12, TC-8): `selection.candidates` length and the narrative's `focus_count` sentence
+    (fact AND text) agree at the served-response layer -- the SAME single served document the
+    Next-session focus section and the plain-English summary sentence both read directly. Also proves
+    HPE (clears leadership, fails its entry qualifier) is counted as a candidate, never a
+    `below_selection_floor` comparison_cohort row."""
+    from app.api.compass import compass as compass_route
+
+    _freeze_frontier(compass_engine_two_candidates, cfg)
+    with Session(compass_engine_two_candidates) as session:
+        result = compass_route(None, session)
+
+    candidate_tickers = {c["ticker"] for c in result["selection"]["candidates"]}
+    assert candidate_tickers == {"AAA", "HPE"}
+    assert not any(row["ticker"] == "HPE" for row in result["comparison_cohort"])
+
+    candidate_count = len(result["selection"]["candidates"])
+    focus = next(s for s in result["narrative"]["sentences"] if s["template_id"] == "focus_count")
+    facts = {f["name"]: f["value"] for f in focus["facts"]}
+    assert facts["candidate_count"] == candidate_count == 2
+    assert str(candidate_count) in focus["text"]
+
+
 def test_compass_route_computes_once_serves_from_storage_after(compass_engine, cfg, monkeypatch):
     """TC-1: once frozen, the SECOND call for the same as-of returns byte-identical content with ZERO
     additional producer calls (get_or_create_manifest short-circuits on the stored row)."""
diff --git a/apps/backend/tests/test_compass.py b/apps/backend/tests/test_compass.py
index 74ea82b1..59a847fa 100644
--- a/apps/backend/tests/test_compass.py
+++ b/apps/backend/tests/test_compass.py
@@ -87,9 +87,15 @@ def selection_run(engine, cfg):
     """One run with a deliberately varied cross-section for J-04 selection tests:
       AAA: L=92 A, E=85 B, R=40 C  -> qualifies (clears all three)
       BBB: L=88 A, E=78 B, R=45 C  -> qualifies
-      CCC: L=77 B, E=55 D, R=50 C  -> fails entry_min_score (70) -> near-miss why-not (leadership 77 >= floor 75)
-      DDD: L=30 E, E=20 E, R=90 E  -> fails everything, leadership far below why_not_floor -> tally only, no entry
+      CCC: L=77 B, E=55 D, R=50 C  -> below the leadership floor (80) -> near-miss why-not (>= why_not_floor 75)
+      DDD: L=30 E, E=20 E, R=90 E  -> far below floor -> tally only, no individual why-not entry
       EEE: L=95 A, E=90 A, R=35 B  -> qualifies, no risk_budget key at all (honest-NA caution path)
+      HPE: L=92.7 A, E=21.5 E, R=58.9 C -> goal-market-compass iter-35 (J-12): the real HPE shape from
+        the frontier export's mislabel -- leadership CLEARS the floor but the entry qualifier fails. Is a
+        CANDIDATE (leadership_min_score is the only candidacy gate) carrying an advisory caution, never
+        `below_selection_floor` despite failing a qualifier -- the exact case the prior buggy code got
+        wrong (BACKGROUND: CCC, the suite's only other qualifier-failing row, is ALSO below the floor, so
+        it alone never exercised this path).
     """
     with Session(engine) as session:
         run = _mk_run(session, date(2024, 3, 1))
@@ -98,6 +104,7 @@ def selection_run(engine, cfg):
         _mk_result(session, run.id, "CCC", 77.0, "B", 55.0, "D", 50.0, "C")
         _mk_result(session, run.id, "DDD", 30.0, "E", 20.0, "E", 90.0, "E")
         _mk_result(session, run.id, "EEE", 95.0, "A", 90.0, "A", 35.0, "B", atr_value=None)
+        _mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 58.9, "C")
         session.commit()
         session.refresh(run)
         return run.id
@@ -111,7 +118,7 @@ def test_candidates_match_stored_scores_and_word_maps(engine, cfg, selection_run
         run = session.get(ScannerRun, selection_run)
         result = compass.evaluate_selection(session, run, cfg)
     by_ticker = {c["ticker"]: c for c in result["candidates"]}
-    assert set(by_ticker) == {"AAA", "BBB", "EEE"}
+    assert set(by_ticker) == {"AAA", "BBB", "EEE", "HPE"}
     aaa = by_ticker["AAA"]
     assert aaa["leadership_score"] == 92.0
     assert aaa["leadership_word"] == cfg.compass.vocabulary.leadership_words["A"]
@@ -121,14 +128,30 @@ def test_candidates_match_stored_scores_and_word_maps(engine, cfg, selection_run
 
 
 def test_checklist_verdicts_reproduce_inclusion(engine, cfg, selection_run):
+    """iter-35 (J-12, TC-6/TC-14): the GATING check (leadership_min_score) ALONE reproduces inclusion --
+    every candidate's gating verdict is Pass and is tagged `gating: True` -- while ADVISORY checks
+    (entry_min_score/risk_max_score) are tagged `gating: False` and may legitimately Miss (HPE clears
+    leadership but misses its entry qualifier) without affecting candidacy."""
     with Session(engine) as session:
         run = session.get(ScannerRun, selection_run)
         result = compass.evaluate_selection(session, run, cfg)
     for candidate in result["candidates"]:
-        assert all(row["verdict"] == "Pass" for row in candidate["checklist"])
         assert {row["condition"] for row in candidate["checklist"]} == {
             "leadership_min_score", "entry_min_score", "risk_max_score",
         }
+        for row in candidate["checklist"]:
+            assert row["gating"] == (row["condition"] == "leadership_min_score")
+        gating_rows = [row for row in candidate["checklist"] if row["gating"]]
+        assert len(gating_rows) == 1
+        assert gating_rows[0]["verdict"] == "Pass"  # the gating verdict ALONE reproduces inclusion
+    # HPE: leadership (gating) Pass, entry (advisory) Miss -- proves an advisory Miss never excludes.
+    hpe = next(c for c in result["candidates"] if c["ticker"] == "HPE")
+    entry_row = next(row for row in hpe["checklist"] if row["condition"] == "entry_min_score")
+    assert entry_row["verdict"] == "Miss" and entry_row["gating"] is False
+    # every OTHER candidate in this fixture clears every qualifier -- what_would_change stays all-met there
+    for candidate in result["candidates"]:
+        if candidate["ticker"] == "HPE":
+            continue
         assert all(row["met"] is True for row in candidate["what_would_change"])
 
 
@@ -167,10 +190,14 @@ def test_excluded_by_cap_get_empty_failed_conditions(engine, cfg, selection_run)
         run = session.get(ScannerRun, selection_run)
         result = compass.evaluate_selection(session, run, capped_cfg)
     assert len(result["candidates"]) == 2
-    assert result["disposition_tally"]["excluded_by_cap"] == 1  # AAA/BBB/EEE qualify, cap keeps top 2
+    # AAA/BBB/EEE/HPE all clear the leadership floor (qualify); cap keeps only the top 2 by leadership.
+    assert {c["ticker"] for c in result["candidates"]} == {"EEE", "HPE"}
+    assert result["disposition_tally"]["excluded_by_cap"] == 2
     why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
-    cut_ticker = ({"AAA", "BBB", "EEE"} - {c["ticker"] for c in result["candidates"]}).pop()
-    assert why_not_by_ticker[cut_ticker]["failed_conditions"] == []  # passed everything; only the cap cut it
+    cut_tickers = {"AAA", "BBB", "EEE", "HPE"} - {c["ticker"] for c in result["candidates"]}
+    assert cut_tickers == {"AAA", "BBB"}
+    for cut_ticker in cut_tickers:
+        assert why_not_by_ticker[cut_ticker]["failed_conditions"] == []  # passed everything; only the cap cut it
 
 
 def test_candidates_empty_reason_when_nothing_qualifies(engine, cfg):
@@ -182,6 +209,13 @@ def test_candidates_empty_reason_when_nothing_qualifies(engine, cfg):
         result = compass.evaluate_selection(session, run, cfg)
     assert result["candidates"] == []
     assert isinstance(result["candidates_empty_reason"], str) and result["candidates_empty_reason"]
+    # iter-35 (J-12, TC-7): names ONLY the gating rule (leadership) -- never entry/risk as though they gated.
+    reason_lower = result["candidates_empty_reason"].lower()
+    assert "entry_min_score" not in reason_lower
+    assert "risk_max_score" not in reason_lower
+    assert "entry quality" not in reason_lower
+    assert "risk" not in reason_lower
+    assert "leadership" in reason_lower
 
 
 def test_risk_off_regime_adds_caution_to_every_candidate(engine, cfg, selection_run):
@@ -192,7 +226,7 @@ def test_risk_off_regime_adds_caution_to_every_candidate(engine, cfg, selection_
         session.commit()
         session.refresh(run)
         result = compass.evaluate_selection(session, run, cfg)
-    assert len(result["candidates"]) == 3
+    assert len(result["candidates"]) == 4
     for candidate in result["candidates"]:
         assert any(c.startswith("REGIME_RISK_OFF") for c in candidate["cautions"])
         assert not any("buy" in c.lower() or "sell" in c.lower() for c in candidate["cautions"])
@@ -263,9 +297,92 @@ def test_excluded_by_cap_cohort_rows_carry_that_disposition(engine, cfg, selecti
     with Session(engine) as session:
         run = session.get(ScannerRun, selection_run)
         result = compass.evaluate_selection(session, run, capped_cfg)
-    cut_ticker = ({"AAA", "BBB", "EEE"} - {c["ticker"] for c in result["candidates"]}).pop()
-    cohort_row = next(row for row in result["comparison_cohort"] if row["ticker"] == cut_ticker)
-    assert cohort_row["selection_disposition"] == "excluded_by_cap"
+    cut_tickers = {"AAA", "BBB", "EEE", "HPE"} - {c["ticker"] for c in result["candidates"]}
+    for cut_ticker in cut_tickers:
+        cohort_row = next(row for row in result["comparison_cohort"] if row["ticker"] == cut_ticker)
+        assert cohort_row["selection_disposition"] == "excluded_by_cap"
+
+
+# --- iter-35 (J-12): leadership_min_score is the ONLY candidacy gate --------------------------------
+
+
+def test_hpe_shape_row_clears_floor_never_below_selection_floor_and_carries_caution(engine, cfg, selection_run):
+    """TC-2/TC-5/TC-9: the real HPE shape (leadership clears the floor, entry qualifier fails) is a
+    CANDIDATE -- never `below_selection_floor` -- and carries an advisory caution citing `entry_min_score`
+    and the row's actual `entry_quality_score` value, never a reason claiming it clears that qualifier.
+    This is the EXACT case the prior buggy code mislabeled on the frontier export (37/539 rows, HPE
+    92.71 highest)."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    hpe = next(c for c in result["candidates"] if c["ticker"] == "HPE")
+    assert not any(row["ticker"] == "HPE" for row in result["comparison_cohort"])  # never a non-candidate here
+    assert not any(reason.startswith("Entry Quality") for reason in hpe["reasons"])  # never claims it clears entry
+    assert any(reason.startswith("Leadership") for reason in hpe["reasons"])  # the gating check IS a reason
+    caution = next(c for c in hpe["cautions"] if c.startswith("ENTRY_QUALITY_QUALIFIER"))
+    assert "21.5" in caution  # the row's actual stored entry_quality_score value
+    assert f"{cfg.compass.selection.entry_min_score:.1f}" in caution  # the threshold
+
+
+def test_disposition_predicate_holds_for_every_comparison_cohort_row(engine, cfg, selection_run):
+    """iter-35 (J-12): `selection_disposition` is truthful BY CONSTRUCTION -- every row's OWN predicate
+    holds (below_selection_floor => leadership < floor; excluded_by_cap => leadership >= floor). Zero
+    comparison_cohort rows at/above the floor are mislabeled below_selection_floor (TC-2/TC-9's
+    zero-mislabel requirement, exercised directly rather than only via the internal runtime assertion)."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    floor = cfg.compass.selection.leadership_min_score
+    assert result["comparison_cohort"]  # the fixture has non-candidate rows -- a non-vacuous check
+    for row in result["comparison_cohort"]:
+        if row["selection_disposition"] == "below_selection_floor":
+            assert row["leadership_score"] < floor
+        elif row["selection_disposition"] == "excluded_by_cap":
+            assert row["leadership_score"] >= floor
+        else:
+            pytest.fail(f"unexpected disposition {row['selection_disposition']!r}")
+    assert not any(
+        row["leadership_score"] >= floor and row["selection_disposition"] == "below_selection_floor"
+        for row in result["comparison_cohort"]
+    )
+
+
+def test_perturbing_advisory_qualifiers_leaves_hashes_membership_and_dispositions_unchanged(engine, cfg, selection_run):
+    """iter-35 (J-12, TC-4/TC-15): completes the counter-test J-06 already specified but the suite never
+    implemented (the suite's only other qualifier-failing row, CCC, was ALSO below the leadership floor,
+    so it alone never exercised this path). Perturbing entry_min_score/risk_max_score moves NEITHER
+    candidate_rule_hash NOR cohort_rule_hash, and leaves the candidate list (tickers, in order), the
+    comparison_cohort (membership AND every selection_disposition), and the near-threshold shadow cohort
+    byte-identical -- proving the two advisory qualifiers no longer gate membership at all."""
+    perturbed_selection = cfg.compass.selection.model_copy(
+        update={
+            "entry_min_score": cfg.compass.selection.entry_min_score + 15.0,
+            "risk_max_score": cfg.compass.selection.risk_max_score - 15.0,
+        }
+    )
+    perturbed_cfg = cfg.model_copy(
+        update={"compass": cfg.compass.model_copy(update={"selection": perturbed_selection})}
+    )
+    # sanity: the perturbation is real (manifest_config_hash DOES move) -- otherwise this test proves nothing.
+    assert compass._hash_subset(compass._manifest_config_subset(cfg)) != compass._hash_subset(
+        compass._manifest_config_subset(perturbed_cfg)
+    )
+
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        before = compass.evaluate_selection(session, run, cfg)
+        after = compass.evaluate_selection(session, run, perturbed_cfg)
+
+    assert compass._hash_subset(compass._candidate_rule_subset(cfg)) == compass._hash_subset(
+        compass._candidate_rule_subset(perturbed_cfg)
+    )
+    assert compass._hash_subset(compass._cohort_rule_subset(cfg)) == compass._hash_subset(
+        compass._cohort_rule_subset(perturbed_cfg)
+    )
+    assert [c["ticker"] for c in before["candidates"]] == [c["ticker"] for c in after["candidates"]]
+    assert before["comparison_cohort"] == after["comparison_cohort"]  # membership AND every disposition
+    assert before["near_threshold_shadow"] == after["near_threshold_shadow"]
+    assert before["disposition_tally"] == after["disposition_tally"]
 
 
 def test_near_threshold_shadow_is_half_open_band_below_floor(engine, cfg, selection_run):
@@ -389,8 +506,8 @@ def test_focus_count_sentence_matches_candidate_count(engine, cfg, selection_run
         narrative = compass.build_narrative(session, run, None, selection, cfg)
     focus = next(s for s in narrative["sentences"] if s["template_id"] == "focus_count")
     facts = {f["name"]: f["value"] for f in focus["facts"]}
-    assert facts["candidate_count"] == len(selection["candidates"]) == 3
-    assert "3" in focus["text"]
+    assert facts["candidate_count"] == len(selection["candidates"]) == 4
+    assert "4" in focus["text"]
 
 
 def test_banned_language_scan_raises_on_violation(cfg):
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index e3613743..f3676a9e 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -46,7 +46,10 @@ def _mk_run(session: Session, asof: date, regime_score: float = 60.0) -> Scanner
     return run
 
 
-def _mk_result(session: Session, run_id: int, ticker: str, l_score: float = 92.0, l_bucket: str = "A") -> None:
+def _mk_result(
+    session: Session, run_id: int, ticker: str, l_score: float = 92.0, l_bucket: str = "A",
+    e_score: float = 85.0, e_bucket: str = "B", r_score: float = 40.0, r_bucket: str = "C",
+) -> None:
     record = {
         "ticker": ticker,
         "invalidation": {"note": f"{ticker} note", "price": 100.0},
@@ -56,8 +59,8 @@ def _mk_result(session: Session, run_id: int, ticker: str, l_score: float = 92.0
         ScannerResult(
             run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
             leadership_score=l_score, leadership_bucket=l_bucket,
-            entry_quality_score=85.0, entry_quality_bucket="B",
-            risk_score=40.0, risk_bucket="C",
+            entry_quality_score=e_score, entry_quality_bucket=e_bucket,
+            risk_score=r_score, risk_bucket=r_bucket,
             setup_status="Breakout-watch", rank=1, record_json=json.dumps(record),
         )
     )
@@ -920,6 +923,26 @@ def test_tc24_disposition_tallies_partition_member_count_minus_candidate_count(e
     assert set(dispositions) <= {"below_selection_floor", "excluded_by_cap"}
 
 
+def test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers(engine, cfg):
+    """goal-market-compass iter-35 (J-12): a row that CLEARS the leadership floor but fails BOTH the
+    entry and risk qualifiers is never `below_selection_floor` -- it is a candidate (or `excluded_by_cap`
+    if the cap binds). A row BELOW the floor is `below_selection_floor` regardless of how its qualifiers
+    score. Mirrors the frontier export's measured defect (37/539 rows, HPE 92.71 highest, BACKGROUND)."""
+    with Session(engine) as session:
+        run = _mk_run(session, date(2024, 12, 8))
+        _mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 58.9, "C")  # clears floor, fails BOTH qualifiers
+        _mk_result(session, run.id, "LOW", 30.0, "E", 90.0, "A", 10.0, "A")  # below floor, clears BOTH qualifiers
+        session.commit()
+        session.refresh(run)
+        result = compass.evaluate_selection(session, run, cfg)
+    candidate_tickers = {c["ticker"] for c in result["candidates"]}
+    cohort_by_ticker = {row["ticker"]: row for row in result["comparison_cohort"]}
+    assert "HPE" in candidate_tickers or cohort_by_ticker.get("HPE", {}).get("selection_disposition") == "excluded_by_cap"
+    assert "HPE" not in cohort_by_ticker or cohort_by_ticker["HPE"]["selection_disposition"] != "below_selection_floor"
+    assert cohort_by_ticker["LOW"]["selection_disposition"] == "below_selection_floor"
+    assert "LOW" not in candidate_tickers
+
+
 # --- TC-25 (schema conformance) ---------------------------------------------------------------------
 
 
diff --git a/config.yaml b/config.yaml
index 7d26498e..7e0f3fe2 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1430,7 +1430,13 @@ compass:
       - { min: 0.40, label: "tense" }
       - { min: 0.60, label: "stressed" }
   selection:
-    rule_version: "v1"
+    # goal-market-compass iter-35 (J-12): bumped v1 -> v2 -- `evaluate_selection` now actually enforces
+    # what this section's own comments always declared (leadership_min_score is the ONLY candidacy gate;
+    # entry_min_score/risk_max_score are advisory qualifiers that never remove a row from candidacy). No
+    # threshold VALUE below changed (AG-15) -- only which checks GATE vs. ANNOTATE. rule_version is inside
+    # BOTH candidate_rule_hash's and cohort_rule_hash's scope, so manifests minted under the corrected
+    # rule are distinguishable from those minted under the old (buggy) one.
+    rule_version: "v2"
     leadership_min_score: 80.0       # the ONLY candidacy gate on Leadership (never the Actionable/A-bucket setup status)
     entry_min_score: 70.0            # candidacy qualifier: Entry Quality score floor
     risk_max_score: 60.0             # candidacy qualifier: Risk score ceiling (risk is a danger score — lower is safer)
```
