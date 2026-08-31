# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 10. Shown in full: 9.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/page.tsx` (154 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 3b3a7679..5d092b3d 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -2567,6 +2567,13 @@ class CompassDeltaCfg(BaseModel):
     top_k: int
     max_stock_items: int
     velocity_flat_band: float
+    # goal-market-compass iter-28 (J-07) — the `state_band.stress` flat-band edge (severity-points
+    # between two stored runs' market-phase severity). NEW key (the developer's config-naming choice
+    # per goal.md's NOTES: "reuse an existing edge ... or add a new compass.delta.* key" — a dedicated
+    # key was chosen over reusing `velocity_flat_band` because severity is a DIFFERENT 0-100 scale than
+    # the regime score, not because the reading was unsound). `state_band.breadth` reuses
+    # `breadth_min_change_pts` above unchanged (no new key needed there).
+    stress_velocity_flat_band: float
     pbear_bands: list[LabelEdge] = Field(min_length=1)
 
     @model_validator(mode="after")
@@ -2576,6 +2583,7 @@ class CompassDeltaCfg(BaseModel):
             ("breadth_min_change_pts", self.breadth_min_change_pts),
             ("stock_score_min_change", self.stock_score_min_change),
             ("velocity_flat_band", self.velocity_flat_band),
+            ("stress_velocity_flat_band", self.stress_velocity_flat_band),
         ):
             if value < 0:
                 raise ValueError(f"compass.delta.{name} must be >= 0, got {value}")
@@ -2731,6 +2739,7 @@ def _default_compass() -> "CompassCfg":
             top_k=5,
             max_stock_items=10,
             velocity_flat_band=2.0,
+            stress_velocity_flat_band=5.0,
             pbear_bands=[
                 LabelEdge(min=0.0, label="calm"),
                 LabelEdge(min=0.20, label="cautious"),
diff --git a/apps/backend/app/db.py b/apps/backend/app/db.py
index 7490bd1a..e5afd467 100644
--- a/apps/backend/app/db.py
+++ b/apps/backend/app/db.py
@@ -161,6 +161,12 @@ _ADDITIVE_COLUMNS: tuple[tuple[str, str, str], ...] = (
     ("next_session_manifests", "available_at_utc", "ALTER TABLE next_session_manifests ADD COLUMN available_at_utc DATETIME"),
     ("next_session_manifests", "manifest_hash", "ALTER TABLE next_session_manifests ADD COLUMN manifest_hash VARCHAR"),
     ("next_session_manifests", "export_path", "ALTER TABLE next_session_manifests ADD COLUMN export_path VARCHAR"),
+    # goal-market-compass iter-28 (J-07): the state_band CONTENT block (regime/stress/breadth direction
+    # words + deltas). NULLABLE VARCHAR (matches `state_band_json: Optional[str] = Field(default=None)`)
+    # — every row minted before this iteration reads NULL forever ("pre-state_band era", AG-12: never
+    # backfilled). A fresh DB gets the column from the model directly (create_all); an existing live DB
+    # gains it in place.
+    ("next_session_manifests", "state_band_json", "ALTER TABLE next_session_manifests ADD COLUMN state_band_json VARCHAR"),
 )
 
 
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index 2b1705db..82bf77c9 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1,7 +1,8 @@
 """app.engine.compass — the deterministic narrative + candidate-selection trace + manifest assembly
-(goal-market-compass iter-2, J-03/J-04, CONTENT block; iter-3, J-05/J-06, the freeze/integrity block).
+(goal-market-compass iter-2, J-03/J-04, CONTENT block; iter-3, J-05/J-06, the freeze/integrity block;
+iter-28, J-07, the `state_band` CONTENT block).
 
-Three CONTENT producers, one assembler (iter-2, unchanged this iteration):
+Four CONTENT producers, one assembler:
 
   - `build_narrative(...)` — deterministic template sentences (state / direction / breadth /
     focus-count, plus a no-comparison / NA-velocity / retrospective-stamp variant where it applies),
@@ -18,9 +19,16 @@ Three CONTENT producers, one assembler (iter-2, unchanged this iteration):
     partitions the disposition tally already computed. No new blended/composite score is introduced
     anywhere (AG-11) — every value shown is one of the three existing per-stock scores/buckets, a
     config word map, or a structural context field already computed by `scoring.score_stocks`.
-  - `build_manifest_payload(...)` — assembles `session_delta` + `narrative` + `selection` into one
-    content document and computes `content_hash` (sha256 over the sorted-key JSON of the content block
-    only — unchanged scope/contract from iter-2, including the cohorts now nested inside `selection`).
+  - `build_state_band(...)` — iter-28 (J-07): three direction words (regime, stress, breadth), each
+    with a signed delta, comparing the current stored run against the immediately preceding one. Reuses
+    the SAME `compass.vocabulary.direction_words` map as `build_narrative`'s own direction sentence
+    (never a second word map) and the SAME `_flat_band_word` classifier `_direction_word` already used.
+    No-prior-run or a missing per-word input renders that word's explicit null/no-comparison state —
+    never a fabricated word (mirrors `session_delta`'s and `narrative`'s own no-prior-run handling).
+  - `build_manifest_payload(...)` — assembles `session_delta` + `narrative` + `selection` +
+    `state_band` into one content document and computes `content_hash` (sha256 over the sorted-key
+    JSON of the content block only — unchanged scope/contract from iter-2, including the cohorts
+    nested inside `selection` and, since iter-28, `state_band` alongside them).
 
 The freeze/integrity block (iter-3, J-05/J-06) — `_freeze_manifest` is the ONE writer behind all three
 producer paths:
@@ -123,11 +131,21 @@ def _state_sentence(dashboard: dict, phase_payload: dict, cfg: Config) -> dict:
     return {"template_id": "state", "text": text, "facts": facts}
 
 
+def _flat_band_word(delta: float, flat_band: float, cfg: Config) -> str:
+    """Generic up/down/flat classification of a SIGNED delta against a flat-band threshold, via the ONE
+    shared `compass.vocabulary.direction_words` map (goal.md, iter-28/J-07: "reuses the SAME ...  map,
+    never a second word map"). The caller is responsible for the delta's SIGN meaning "higher is
+    healthier" (positive -> "up"/improving) — see `build_state_band`'s stress-band sign note for the one
+    band where that requires a deliberate transform before calling this."""
+    vocab = cfg.compass.vocabulary.direction_words
+    if abs(delta) < flat_band:
+        return vocab["flat"]
+    return vocab["up" if delta > 0 else "down"]
+
+
 def _direction_word(current_run: ScannerRun, previous_run: ScannerRun, cfg: Config) -> tuple[str, float]:
     delta = current_run.regime_score - previous_run.regime_score
-    if abs(delta) < cfg.compass.delta.velocity_flat_band:
-        return cfg.compass.vocabulary.direction_words["flat"], delta
-    return cfg.compass.vocabulary.direction_words["up" if delta > 0 else "down"], delta
+    return _flat_band_word(delta, cfg.compass.delta.velocity_flat_band, cfg), delta
 
 
 def _direction_sentence(
@@ -247,6 +265,86 @@ def build_narrative(
     return {"sentences": sentences}
 
 
+# --- state_band (iter-28, J-07) -----------------------------------------------------------------
+
+_STATE_BAND_NO_COMPARISON: dict = {"direction_word": None, "delta": None}
+
+
+def _severity_at(session: Session, as_of: date, cfg: Config) -> Optional[float]:
+    """One date's stored/cached severity, via the SAME `market_phase_cached` read `build_narrative`
+    already uses for the current run (a warm cache hit for any date that was itself once the frontier —
+    never a fresh full-history recompute here). Honest `None` (never fabricated) when phase data is
+    unavailable for that date (insufficient trailing history)."""
+    payload = market_phase.market_phase_cached(session, as_of, cfg)
+    if not payload.get("available"):
+        return None
+    return payload.get("severity")
+
+
+def build_state_band(
+    session: Session,
+    current_run: ScannerRun,
+    previous_run: Optional[ScannerRun],
+    config: Optional[Config] = None,
+) -> dict:
+    """The `state_band` CONTENT block (goal-market-compass iter-28, J-07) — three direction words
+    (`regime`, `stress`, `breadth`), each with a signed delta, computed ONCE here inside
+    `build_manifest_payload` (same producer/scope as `session_delta`/`narrative`), never recomputed at
+    read. No-prior-run, OR a missing per-word input, independently renders THAT word's explicit
+    null/no-comparison state — never a fabricated word (mirrors `session_delta`'s and `narrative`'s own
+    no-prior-run handling).
+
+      - `regime`: reuses `_direction_word` verbatim (current vs previous `regime_score`,
+        `compass.delta.velocity_flat_band` — goal.md: "unchanged").
+      - `breadth`: current vs previous `breadth_above_50dma`, banded via `compass.delta.
+        breadth_min_change_pts` (goal.md's NOTES authorize reusing this existing edge). Higher breadth
+        shares regime's polarity (more names above their 50-DMA is more constructive), so the raw delta
+        classifies directly — no sign transform.
+      - `stress`: current vs previous market-phase `severity` (the "severity velocity" goal.md names),
+        banded via the NEW `compass.delta.stress_velocity_flat_band`. `state_band.stress.delta` is the
+        LITERAL `current_severity - previous_severity` (unflipped — positive means severity ROSE).
+        Severity's polarity is the OPPOSITE of regime_score/breadth: a rising severity is DETERIORATING,
+        not improving (the engine's own existing convention: `market_phase._severity_velocity_at`'s
+        docstring states "positive = severity worsening"). So the WORD is classified off this delta's
+        NEGATION — a falling severity (stress easing) reads "up"/improving, a rising severity reads
+        "down"/deteriorating — so the shared direction_words map's plain-English meaning ("improving" /
+        "deteriorating") stays truthful for this band too. This sign choice is a deliberate design
+        decision (documented in the dev handoff), not a literal-only reading of the delta equation."""
+    cfg = config or get_config()
+    if previous_run is None:
+        return {
+            "regime": dict(_STATE_BAND_NO_COMPARISON),
+            "stress": dict(_STATE_BAND_NO_COMPARISON),
+            "breadth": dict(_STATE_BAND_NO_COMPARISON),
+        }
+
+    regime_word, regime_delta = _direction_word(current_run, previous_run, cfg)
+
+    current_severity = _severity_at(session, current_run.asof_date, cfg)
+    previous_severity = _severity_at(session, previous_run.asof_date, cfg)
+    if current_severity is not None and previous_severity is not None:
+        stress_delta = current_severity - previous_severity
+        stress_word = _flat_band_word(-stress_delta, cfg.compass.delta.stress_velocity_flat_band, cfg)
+    else:
+        stress_delta = None
+        stress_word = None
+
+    b_cur = current_run.breadth_above_50dma
+    b_prev = previous_run.breadth_above_50dma
+    if b_cur is not None and b_prev is not None:
+        breadth_delta = b_cur - b_prev
+        breadth_word = _flat_band_word(breadth_delta, cfg.compass.delta.breadth_min_change_pts, cfg)
+    else:
+        breadth_delta = None
+        breadth_word = None
+
+    return {
+        "regime": {"direction_word": regime_word, "delta": regime_delta},
+        "stress": {"direction_word": stress_word, "delta": stress_delta},
+        "breadth": {"direction_word": breadth_word, "delta": breadth_delta},
+    }
+
+
 # --- selection (J-04; iter-3 J-05/J-06 adds comparison_cohort + near_threshold_shadow) --------
 
 _QUALIFIER_CHECKS = ("leadership_min_score", "entry_min_score", "risk_max_score")
@@ -614,15 +712,17 @@ def build_manifest_payload(
     previous_run: Optional[ScannerRun],
     config: Optional[Config] = None,
 ) -> dict:
-    """Assemble the three CONTENT blocks + `content_hash` (sha256 hex over the sorted-key JSON of the
-    content block only — never re-derived at serve time; see `manifest_row_payload`). UNCHANGED scope
-    from iter-2: `selection` now carries `comparison_cohort` / `near_threshold_shadow` (iter-3), which
-    flow through into `content_hash`'s scope automatically — no code change needed here for that."""
+    """Assemble the CONTENT blocks + `content_hash` (sha256 hex over the sorted-key JSON of the content
+    block only — never re-derived at serve time; see `manifest_row_payload`). `selection` carries
+    `comparison_cohort` / `near_threshold_shadow` (iter-3); `state_band` (iter-28, J-07) is a new
+    top-level content block alongside `session_delta`/`narrative`/`selection` — additive to
+    `content_hash`'s scope, no other code change needed for that."""
     cfg = config or get_config()
     delta = compute_delta(session, current_run, previous_run, cfg)
     selection = evaluate_selection(session, current_run, cfg)
     narrative = build_narrative(session, current_run, previous_run, selection, cfg)
-    content = {"session_delta": delta, "narrative": narrative, "selection": selection}
+    state_band = build_state_band(session, current_run, previous_run, cfg)
+    content = {"session_delta": delta, "narrative": narrative, "selection": selection, "state_band": state_band}
     canonical = json.dumps(content, sort_keys=True, default=str)
     content_hash = hashlib.sha256(canonical.encode()).hexdigest()
     return {**content, "content_hash": content_hash}
@@ -902,6 +1002,7 @@ def _freeze_manifest(
     comparison_cohort = selection.pop("comparison_cohort")
     near_threshold_shadow = selection.pop("near_threshold_shadow")
     member_count = selection.pop("member_count")  # folded into universe.member_count -- one source, not two
+    state_band = content_payload["state_band"]  # iter-28 (J-07) -- its own top-level document key + column
 
     generated_at = datetime.now(timezone.utc)
     available_at_utc = generated_at + timedelta(seconds=cfg.compass.manifest.availability_margin_seconds)
@@ -958,6 +1059,7 @@ def _freeze_manifest(
         "session_delta": content_payload["session_delta"],
         "narrative": content_payload["narrative"],
         "selection": selection,
+        "state_band": state_band,
         "comparison_cohort": comparison_cohort,
         "near_threshold_shadow": near_threshold_shadow,
         "content_hash": content_payload["content_hash"],
@@ -988,6 +1090,7 @@ def _freeze_manifest(
         session_delta_json=json.dumps(content_payload["session_delta"]),
         narrative_json=json.dumps(content_payload["narrative"]),
         selection_json=json.dumps(selection),
+        state_band_json=json.dumps(state_band),
         content_hash=content_payload["content_hash"],
         created_at=generated_at,
         mode=mode,
@@ -1204,6 +1307,9 @@ def manifest_row_payload(row: NextSessionManifest) -> dict:
         "session_delta": json.loads(row.session_delta_json),
         "narrative": json.loads(row.narrative_json),
         "selection": json.loads(row.selection_json),
+        # iter-28 (J-07): NULL for every row minted before this iteration ("pre-state_band era" — never
+        # backfilled, AG-12) — an honest None, mirrors every other iter-3+ additive block's None default.
+        "state_band": json.loads(row.state_band_json) if row.state_band_json else None,
         "comparison_cohort": json.loads(row.comparison_cohort_json) if row.comparison_cohort_json else [],
         "near_threshold_shadow": json.loads(row.near_threshold_shadow_json) if row.near_threshold_shadow_json else [],
         "content_hash": row.content_hash,
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index e55f2983..8a2766df 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -784,13 +784,13 @@ class NextSessionManifest(SQLModel, table=True):
     never duplicate, never overwrite). `next_session_manifests` joins NEITHER `clear_snapshot_set` NOR
     the remove-data cascade — no code path deletes a row here.
 
-    The three CONTENT blocks (`session_delta`, `narrative`, `selection` — the `selection` block now also
-    carries `comparison_cohort` / `near_threshold_shadow`, iter-3) are stored as their OWN JSON columns
-    rather than one combined blob so a future column-projected read never has to deserialize a block it
-    does not need (AG-8 posture). `content_hash` is the sha256 hex digest of the sorted-key JSON of
-    exactly these three blocks (see `app.engine.compass.build_manifest_payload`) — NOT of this row's
-    other columns; it stays invariant across legitimate generation-metadata-only differences (e.g. a
-    regenerate with unchanged inputs).
+    The CONTENT blocks (`session_delta`, `narrative`, `selection` — the `selection` block now also
+    carries `comparison_cohort` / `near_threshold_shadow`, iter-3; `state_band`, iter-28, J-07) are
+    stored as their OWN JSON columns rather than one combined blob so a future column-projected read
+    never has to deserialize a block it does not need (AG-8 posture). `content_hash` is the sha256 hex
+    digest of the sorted-key JSON of exactly these content blocks (see
+    `app.engine.compass.build_manifest_payload`) — NOT of this row's other columns; it stays invariant
+    across legitimate generation-metadata-only differences (e.g. a regenerate with unchanged inputs).
 
     The FREEZE/INTEGRITY columns below are all ADDITIVE and nullable/defaulted (`db._ADDITIVE_COLUMNS`)
     so an existing pre-iter-3 row backfills `version=1`, `frozen=False`, `mode`/every hash/JSON-block
@@ -895,6 +895,13 @@ class NextSessionManifest(SQLModel, table=True):
     comparison_cohort_json: Optional[str] = Field(default=None)  # list of frozen non-candidate rows
     near_threshold_shadow_json: Optional[str] = Field(default=None)  # subset of the above, near the floor
     caveats_json: Optional[str] = Field(default=None)  # {evidence, survivorship, sector_basis, cohort_semantics}
+    # goal-market-compass iter-28 (J-07): the state_band CONTENT block (three direction words -- regime,
+    # stress, breadth -- each with a signed delta), additive/nullable like every other iter-3+ column here.
+    # A pre-iter-28 row (every row minted before this iteration) reads NULL forever -- an honest
+    # "pre-state_band era" marker (AG-12: never backfilled/regenerated to add it retroactively). Stored as
+    # its OWN JSON column (not folded into selection_json) for the same AG-8 column-projection reasoning as
+    # the other content/freeze blocks above.
+    state_band_json: Optional[str] = Field(default=None)
     # fail-closed, write-once: true iff mode=at_ingest, producer=ingest_finalize, version=1, frozen=True,
     # a well-formed available_at_utc, and complete provenance — derived ONCE at write, NEVER at read.
     prospective_eligible: bool = Field(default=False, index=True)
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
index 5811af78..b016dfac 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -199,6 +199,52 @@ def test_compass_route_historical_asof_serves_that_dates_own_manifest(compass_en
     assert result["session_delta"]["prior_as_of"] is None  # earliest stored run -- explicit no-prior-run state
 
 
+# --- state_band (goal-market-compass iter-28, J-07) -----------------------------------------------
+
+
+def test_compass_route_serves_state_band_directly(compass_engine, cfg):
+    """iter-28 (J-07): `state_band` is present at the response layer, additive alongside
+    `session_delta`/`narrative`/`selection`. `compass_engine` seeds no `MarketPhaseCache` row, so
+    `stress` honestly reads the no-comparison NA state (never fabricated); `regime` (50.0 -> 58.0) and
+    `breadth` (55.0 -> 55.0, unchanged) compute directly from the two stored runs."""
+    from app.api.compass import compass as compass_route
+
+    _freeze_frontier(compass_engine, cfg)
+    with Session(compass_engine) as session:
+        result = compass_route(None, session)
+
+    assert "state_band" in result
+    state_band = result["state_band"]
+    for band in ("regime", "stress", "breadth"):
+        assert band in state_band
+        assert set(state_band[band]) == {"direction_word", "delta"}
+    assert state_band["regime"]["delta"] == pytest.approx(8.0)  # 58.0 - 50.0
+    assert state_band["regime"]["direction_word"] == cfg.compass.vocabulary.direction_words["up"]
+    assert state_band["breadth"]["delta"] == pytest.approx(0.0)
+    assert state_band["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["flat"]
+    assert state_band["stress"] == {"direction_word": None, "delta": None}  # no MarketPhaseCache seeded
+
+
+def test_compass_route_state_band_null_on_pre_iter28_row(compass_engine, cfg):
+    """A manifest row minted before `state_band_json` existed (simulated by clearing the column, which
+    is exactly the shape every one of the 26+ live pre-iter-28 rows has -- AG-12: never backfilled)
+    serves `state_band: None` honestly -- never fabricated, never crashes the route."""
+    from app.api.compass import compass as compass_route
+
+    _freeze_frontier(compass_engine, cfg)
+    with Session(compass_engine) as session:
+        row = session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
+        ).first()
+        row.state_band_json = None
+        session.add(row)
+        session.commit()
+
+    with Session(compass_engine) as session:
+        result = compass_route(None, session)
+    assert result["state_band"] is None
+
+
 # --- POST /api/compass/regenerate (iter-3, J-05/J-06) --------------------------------------------
 
 
diff --git a/apps/backend/tests/test_compass.py b/apps/backend/tests/test_compass.py
index 103ab537..74ea82b1 100644
--- a/apps/backend/tests/test_compass.py
+++ b/apps/backend/tests/test_compass.py
@@ -7,6 +7,7 @@ the SAME `_cache_version` the real cache uses) so these tests need no real price
 from __future__ import annotations
 
 import ast
+import hashlib
 import json
 from datetime import date, datetime, timezone
 
@@ -412,6 +413,147 @@ def test_retrospective_stamp_appears_only_for_non_frontier_asof(engine, cfg, two
     assert not any(s["template_id"] == "retrospective_stamp" for s in narrative_b["sentences"])
 
 
+# --- state_band (goal-market-compass iter-28, J-07) -----------------------------------------------
+
+
+def test_state_band_no_prior_run_renders_null_for_all_three(engine, cfg, two_runs_with_phase):
+    """TC-4: the earliest stored run (no previous run) renders an explicit null/no-comparison state for
+    ALL THREE bands -- never a fabricated word."""
+    run_a_id, _run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        state_band = compass.build_state_band(session, run_a, None, cfg)
+    for band in ("regime", "stress", "breadth"):
+        assert state_band[band] == {"direction_word": None, "delta": None}
+
+
+def test_state_band_regime_matches_direction_word_and_stress_flips_polarity(engine, cfg, two_runs_with_phase):
+    """TC-1/TC-2: `two_runs_with_phase` has regime_score 50.0 -> 58.0 (+8.0, well above the 2.0 flat
+    band) and severity 25.0 -> 45.0 (+20.0, well above the 5.0 flat band -- severity ROSE, i.e. stress
+    WORSENED). `state_band.regime.delta` equals `current.regime_score - previous.regime_score` exactly
+    and its word is the SAME word `_direction_word` (the narrative's own direction sentence) already
+    produces for this pair -- one shared computation, not a second one. `state_band.stress.delta` is the
+    LITERAL `current_severity - previous_severity` (+20.0, unflipped -- TC-2's exact equation), but
+    because a RISING severity is deteriorating (not improving), its WORD is the OPPOSITE polarity of
+    regime's: regime reads "improving", stress reads "deteriorating" for this SAME pair of runs, proving
+    the sign transform is deliberate and not an accidental copy of regime's polarity."""
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        expected_regime_word, expected_regime_delta = compass._direction_word(run_b, run_a, cfg)
+        state_band = compass.build_state_band(session, run_b, run_a, cfg)
+    assert state_band["regime"]["delta"] == pytest.approx(8.0) == expected_regime_delta
+    assert state_band["regime"]["direction_word"] == expected_regime_word == cfg.compass.vocabulary.direction_words["up"]
+    assert state_band["stress"]["delta"] == pytest.approx(20.0)  # current_severity - previous_severity, literal
+    assert state_band["stress"]["direction_word"] == cfg.compass.vocabulary.direction_words["down"]
+    assert state_band["regime"]["direction_word"] != state_band["stress"]["direction_word"]
+
+
+def test_state_band_breadth_flat_when_unchanged(engine, cfg, two_runs_with_phase):
+    """TC-3: `_mk_run`'s fixture rows both carry `breadth_above_50dma=55.0` (unchanged) -- delta 0.0 is
+    well within the reused `breadth_min_change_pts` (5.0) flat band, so the word is "flat", never
+    fabricated as up/down from a zero delta."""
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        state_band = compass.build_state_band(session, run_b, run_a, cfg)
+    assert state_band["breadth"]["delta"] == pytest.approx(0.0)
+    assert state_band["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["flat"]
+
+
+def test_state_band_breadth_up_and_down_bands(engine, cfg):
+    """TC-3 at the config edge: a breadth move well above `breadth_min_change_pts` (5.0) reads up/down by
+    sign; a move well below it reads flat -- all three read straight off the SAME config threshold
+    `session_delta._breadth_changes` uses for its own breadth-kind gate (one threshold, two producers)."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 6, 1))
+        run_a.breadth_above_50dma = 40.0
+        run_b = _mk_run(session, date(2024, 6, 8))
+        run_b.breadth_above_50dma = 55.0  # +15.0, well above the 5.0 flat band
+        run_c = _mk_run(session, date(2024, 6, 15))
+        run_c.breadth_above_50dma = 42.0  # -13.0 vs run_b, well above the flat band (down)
+        session.add_all([run_a, run_b, run_c])
+        session.commit()
+        up = compass.build_state_band(session, run_b, run_a, cfg)
+        down = compass.build_state_band(session, run_c, run_b, cfg)
+    assert up["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["up"]
+    assert down["breadth"]["direction_word"] == cfg.compass.vocabulary.direction_words["down"]
+
+
+def test_state_band_stress_na_when_phase_unavailable(engine, cfg):
+    """A missing/NA severity input on EITHER side renders `stress` as an explicit no-comparison state --
+    never a guessed word -- while `regime`/`breadth` (unaffected inputs) still compute normally. Mirrors
+    `test_direction_na_velocity_variant_when_phase_unavailable`'s "no MarketPhaseCache row seeded" setup."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 7, 1), regime_score=50.0)
+        run_b = _mk_run(session, date(2024, 7, 8), regime_score=60.0)
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        # deliberately NO MarketPhaseCache row seeded -> market_phase_cached degrades to available=False
+        state_band = compass.build_state_band(session, run_b, run_a, cfg)
+    assert state_band["stress"] == {"direction_word": None, "delta": None}
+    assert state_band["regime"]["direction_word"] is not None
+    assert state_band["breadth"]["direction_word"] is not None
+
+
+def test_state_band_breadth_na_when_either_side_missing(engine, cfg):
+    """A missing `breadth_above_50dma` on EITHER stored run renders `breadth` as an explicit
+    no-comparison state -- never a guessed word -- while `regime` (unaffected input) still computes."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 8, 1), regime_score=50.0)
+        run_a.breadth_above_50dma = None
+        run_b = _mk_run(session, date(2024, 8, 8), regime_score=55.0)
+        session.add_all([run_a, run_b])
+        session.commit()
+        state_band = compass.build_state_band(session, run_b, run_a, cfg)
+    assert state_band["breadth"] == {"direction_word": None, "delta": None}
+    assert state_band["regime"]["direction_word"] is not None
+
+
+def test_state_band_is_wired_into_manifest_payload_and_content_hash(engine, cfg, two_runs_with_phase):
+    """`state_band` is a top-level content block alongside `session_delta`/`narrative`/`selection` (same
+    `content_hash` scope) -- flipping it changes `content_hash` (proving it is actually inside the
+    hashed scope, not decorative)."""
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    assert "state_band" in payload
+    assert payload["state_band"] == compass.build_state_band(session, run_b, run_a, cfg)
+    tampered_content = {
+        "session_delta": payload["session_delta"], "narrative": payload["narrative"],
+        "selection": payload["selection"],
+        "state_band": {**payload["state_band"], "regime": {"direction_word": "improving", "delta": 999.0}},
+    }
+    tampered_hash = hashlib.sha256(
+        json.dumps(tampered_content, sort_keys=True, default=str).encode()
+    ).hexdigest()
+    assert tampered_hash != payload["content_hash"]
+
+
+def test_state_band_served_verbatim_by_manifest_row_payload(engine, cfg, two_runs_with_phase):
+    """`manifest_row_payload` reconstructs `state_band` verbatim from its own storage column (a read,
+    never a recompute) -- mirrors `test_manifest_row_payload_matches_build_manifest_payload_content`."""
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        built = compass.build_manifest_payload(session, run_b, run_a, cfg)
+        row = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
+        served = compass.manifest_row_payload(row)
+    assert served["state_band"] == built["state_band"]
+
+
+def test_state_band_stress_threshold_is_config_driven(cfg):
+    """The new `stress_velocity_flat_band` threshold lives ONLY in `compass.delta.*` (anti-goal: No
+    magic numbers) -- a direct typed-config read, never a literal in the engine module."""
+    assert cfg.compass.delta.stress_velocity_flat_band > 0
+
+
 # --- manifest assembly + storage -----------------------------------------------------------------
 
 
diff --git a/apps/frontend/app/page.tsx b/apps/frontend/app/page.tsx
index 63a205fb..64042acd 100644
--- a/apps/frontend/app/page.tsx
+++ b/apps/frontend/app/page.tsx
@@ -1,40 +1,26 @@
 "use client";
 
 import { useEffect, useState } from "react";
-import Link from "next/link";
-import { AlertTriangle, Clock, ChevronDown } from "lucide-react";
+import { AlertTriangle, Clock } from "lucide-react";
 
 import { useAsOf } from "@/components/asof-provider";
-import { ComponentBreakdown } from "@/components/component-breakdown";
+import { CompassStateBandCard } from "@/components/compass-state-band-card";
 import { CompassSummaryCard } from "@/components/compass-summary-card";
 import { CompassWhatChangedCard } from "@/components/compass-whatchanged-card";
+import { CompassLeadershipRotationSection } from "@/components/compass-leadership-rotation-section";
 import { CompassFocusSection } from "@/components/compass-focus-section";
 import { CompassManifestStrip } from "@/components/compass-manifest-strip";
-import { MarketPhaseCard } from "@/components/market-phase-card";
-import { PhaseCrossViewCard } from "@/components/phase-cross-view-card";
 import { PageHeading } from "@/components/page-heading";
-import { ScoreBadge } from "@/components/score-badge";
-import { Disclosure } from "@/components/ui/disclosure";
-import { TermInfo } from "@/components/ui/term-info";
 import { Badge } from "@/components/ui/badge";
-import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
+import { Card } from "@/components/ui/card";
 import { formatIsoDate } from "@/lib/dates";
-import { usePersistedToggle } from "@/lib/use-persisted-toggle";
-import { phaseColor } from "@/lib/phase";
-import { regimeVariant } from "@/lib/regime-variant";
-import { cn } from "@/lib/utils";
 import {
   fetchCompass,
   fetchDashboard,
   fetchMarketPhase,
-  fetchSectors,
-  fetchThemes,
   type CompassResponse,
   type DashboardResponse,
-  type MarketPhaseComponent,
   type MarketPhaseResponse,
-  type SectorsResponse,
-  type ThemesResponse,
 } from "@/lib/api";
 
 type State =
@@ -43,62 +29,42 @@ type State =
       kind: "ok";
       dashboard: DashboardResponse;
       phase: MarketPhaseResponse | null;
-      sectors: SectorsResponse | null;
-      themes: ThemesResponse | null;
       compass: CompassResponse | null;
     }
   | { kind: "error" };
 
-function fmtPct(value: number | null | undefined): string {
-  return typeof value === "number" ? `${value.toFixed(2)}%` : "NA";
-}
-
-/** Phase label → Badge palette variant (same posture grouping as the Market-Phase card; presentation
- *  only). Reuses the shared `lib/phase` posture so the colour matches the cross-view bands. */
-function phaseBadgeVariant(phase: string | null): "ok" | "warn" | "danger" {
-  if (phase === "Bear" || phase === "Correction") return "danger";
-  if (phase === "Pullback") return "warn";
-  return "ok";
-}
-
-export default function DashboardPage() {
+/** J-07 (goal-market-compass iter-28): the Today page — the ten-second read, top to bottom: market-state
+ *  band, summary, What changed, Leadership rotation, Next-session focus, manifest strip. The readiness
+ *  badge + preflight strip stay in `layout.tsx` chrome, ABOVE this body (unchanged). `/` fetches ONLY
+ *  `GET /api/dashboard`, `GET /api/market-phase`, and `GET /api/compass` on load — it no longer fetches
+ *  `/api/sectors` or `/api/themes` (those moved to `/market`, J-08, where the former dashboard body now
+ *  lives verbatim). */
+export default function TodayPage() {
   const { asOf } = useAsOf();
   const [state, setState] = useState<State>({ kind: "loading" });
 
   useEffect(() => {
     const controller = new AbortController();
     const asof = asOf ?? undefined; // historical date or latest
-    // Dashboard (regime + candidate counts) is critical; the market-phase summary + Top Sectors + Top
-    // Themes + compass (goal-market-compass iter-2) read their own canonical endpoints and may fail
-    // independently. All fetch the SAME as-of date so the snapshot view is coherent across the page.
+    // Dashboard (regime + candidate counts) is critical; market-phase and compass read their own
+    // canonical endpoints and may fail independently. All fetch the SAME as-of date so the snapshot
+    // view is coherent across the page.
     setState({ kind: "loading" });
     fetchDashboard(asof, controller.signal)
       .then(async (dashboard) => {
         let phase: MarketPhaseResponse | null = null;
-        let sectors: SectorsResponse | null = null;
-        let themes: ThemesResponse | null = null;
         let compass: CompassResponse | null = null;
         try {
           phase = await fetchMarketPhase(asof, controller.signal);
         } catch {
           phase = null;
         }
-        try {
-          sectors = await fetchSectors(asof, controller.signal);
-        } catch {
-          sectors = null;
-        }
-        try {
-          themes = await fetchThemes(asof, controller.signal);
-        } catch {
-          themes = null;
-        }
         try {
           compass = await fetchCompass(asof, controller.signal);
         } catch {
           compass = null;
         }
-        setState({ kind: "ok", dashboard, phase, sectors, themes, compass });
+        setState({ kind: "ok", dashboard, phase, compass });
       })
       .catch(() => {
         if (!controller.signal.aborted) setState({ kind: "error" });
@@ -109,7 +75,7 @@ export default function DashboardPage() {
   return (
     <div className="space-y-4">
       <div className="flex flex-wrap items-end justify-between gap-2">
-        <PageHeading title="Dashboard" subtitle="The daily snapshot at a glance" />
+        <PageHeading title="Today" subtitle="The ten-second read after the close" />
         {state.kind === "ok" ? (
           <Badge variant="default" className="num gap-1.5">
             <Clock className="h-3.5 w-3.5" aria-hidden />
@@ -118,7 +84,7 @@ export default function DashboardPage() {
         ) : null}
       </div>
 
-      {state.kind === "loading" ? <DashboardSkeleton /> : null}
+      {state.kind === "loading" ? <TodaySkeleton /> : null}
 
       {state.kind === "error" ? (
         <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
@@ -126,7 +92,7 @@ export default function DashboardPage() {
           <div>
             <p className="font-medium">Backend unavailable</p>
             <p className="text-text-muted">
-              The dashboard could not load the market regime from the API. Nothing is fabricated —
+              The Today page could not load the market regime from the API. Nothing is fabricated —
               confirm the backend is running and reload.
             </p>
           </div>
@@ -135,394 +101,27 @@ export default function DashboardPage() {
 
       {state.kind === "ok" ? (
         <>
-          {/* goal-market-compass iter-2 (J-02/J-03/J-04): three new Today-page sections, each reading
-              ONLY GET /api/compass, rendered ABOVE the existing dashboard body below. That body
-              (DashboardBody and everything it renders) is UNCHANGED by this iteration — final section
-              ordering/chrome placement is J-07's job, and removing it from `/` is J-08's job.
-              iter-3 (J-05/J-06) appends the manifest strip as the LAST compass card, per goal.md's
-              Product Shape ordering ("...next-session focus, manifest strip") — still above the
-              unmodified DashboardBody (preserves the free in-image AG-3 cross-check, lessons.md iter-2). */}
+          <CompassStateBandCard dashboard={state.dashboard} phase={state.phase} compass={state.compass} />
           <CompassSummaryCard compass={state.compass} />
           <CompassWhatChangedCard compass={state.compass} />
+          <CompassLeadershipRotationSection compass={state.compass} />
           <CompassFocusSection compass={state.compass} />
           <CompassManifestStrip compass={state.compass} asOf={asOf} />
-          <DashboardBody
-            dashboard={state.dashboard}
-            phase={state.phase}
-            sectors={state.sectors}
-            themes={state.themes}
-          />
         </>
       ) : null}
     </div>
   );
 }
 
-function DashboardBody({
-  dashboard,
-  phase,
-  sectors,
-  themes,
-}: {
-  dashboard: DashboardResponse;
-  phase: MarketPhaseResponse | null;
-  sectors: SectorsResponse | null;
-  themes: ThemesResponse | null;
-}) {
-  const { regime } = dashboard;
-
+function TodaySkeleton() {
   return (
     <div className="space-y-4">
-      {/* J-98: the compact AT-A-GLANCE summary — Market Regime + Market Phase & Severity. Each re-displays
-          the SAME served canonical values and keeps its named component breakdown reachable (no bare
-          number). This is the first paint, above the cross-view chart. */}
-      <div className="grid gap-4 md:grid-cols-2">
-        <RegimeGlanceCard regime={regime} />
-        <PhaseGlanceCard phase={phase} />
-      </div>
-
-      {/* J-97 / J-101a: the single two-pane synced regime × phase cross-view chart — the ONE market chart on
-          the Dashboard. The former standalone "Major indexes & regime" card (J-44/J-49) was a DUPLICATE of
-          this chart's pane 0 (same `/api/indexes?full=true` + `/api/regime-history?full=true` series) and is
-          removed (J-101a) — nothing is lost, pane 0 already IS that chart. */}
-      <PhaseCrossViewCard />
-
-      {/* J-98: every supporting figure relocated into a collapsed, expandable "More detail" section —
-          same data, same endpoints, only repositioned (nothing removed). */}
-      <MoreDetailSection dashboard={dashboard} sectors={sectors} themes={themes} />
-    </div>
-  );
-}
-
-/** J-98 compact Market Regime figure: the stored label + 0–100 score, with the named component breakdown
- *  reachable via an inline disclosure (explainable — never a bare number). Re-displays `/api/dashboard`. */
-function RegimeGlanceCard({ regime }: { regime: DashboardResponse["regime"] }) {
-  return (
-    <Card>
-      <CardHeader className="flex-row items-center justify-between space-y-0">
-        <CardTitle className="flex items-center gap-1.5">
-          Market Regime
-          <TermInfo term="market regime" />
-        </CardTitle>
-        <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
-      </CardHeader>
-      <CardContent className="space-y-3">
-        <div className="flex items-baseline gap-2">
-          <span className="num text-4xl font-semibold text-text">{regime.score.toFixed(2)}</span>
-          <span className="text-sm text-text-muted">/ 100</span>
-        </div>
-        <Disclosure summary="Why this regime — component breakdown">
-          <ComponentBreakdown components={regime.components} className="max-w-xl pt-1" />
-        </Disclosure>
-        {/* J-04: a discoverable affordance from the current regime to the certified evidence that holds
-            in it — the Dashboard regime → Evidence ledger flow. The regime number/label above is unchanged. */}
-        <Link
-          href="/evidence"
-          className="inline-flex items-center gap-1 text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
-        >
-          See evidence proven in this regime →
-        </Link>
-      </CardContent>
-    </Card>
-  );
-}
-
-/** J-98 compact Market Phase & Severity figure: the stored phase label + 0–100 severity + filtered P(bear),
- *  with the named severity-component breakdown reachable via an inline disclosure. Re-displays
- *  `/api/market-phase` (the SAME served value the detail card shows — single source). */
-function PhaseGlanceCard({ phase }: { phase: MarketPhaseResponse | null }) {
-  if (phase === null) {
-    return (
-      <Card>
-        <CardHeader>
-          <CardTitle className="flex items-center gap-1.5">Market Phase &amp; Severity</CardTitle>
-        </CardHeader>
-        <CardContent>
-          <p className="text-sm text-neg">Market-phase data unavailable — backend not reachable.</p>
-        </CardContent>
-      </Card>
-    );
-  }
-  const available = phase.available;
-  return (
-    <Card>
-      <CardHeader className="flex-row items-center justify-between space-y-0">
-        <CardTitle className="flex items-center gap-1.5">Market Phase &amp; Severity</CardTitle>
-        {available && phase.phase ? (
-          <span className="flex items-center gap-2">
-            <Badge variant={phaseBadgeVariant(phase.phase)}>{phase.phase}</Badge>
-            <span
-              className="num rounded border border-border bg-surface-2 px-2 py-0.5 text-xs text-text-muted"
-              title={`filtered P(bear) ${phase.p_bear?.toFixed(2) ?? "NA"}`}
-            >
-              P(bear) {phase.p_bear != null ? phase.p_bear.toFixed(2) : "NA"}
-            </span>
-          </span>
-        ) : null}
-      </CardHeader>
-      <CardContent className="space-y-3">
-        {available ? (
-          <>
-            <div className="flex items-baseline gap-2">
-              <span
-                className="num text-4xl font-semibold"
-                style={{ color: phase.phase ? phaseColor(phase.phase) : undefined }}
-              >
-                {phase.severity != null ? phase.severity.toFixed(2) : "NA"}
-              </span>
-              <span className="text-sm text-text-muted">/ 100 severity</span>
-            </div>
-            <Disclosure summary="Why this severity — component breakdown">
-              <SeverityBreakdown components={phase.components} />
-            </Disclosure>
-          </>
-        ) : (
-          <p className="text-sm text-text-muted">
-            Not enough history to derive a market phase for this date — reported NA, never fabricated.
-          </p>
-        )}
-      </CardContent>
-    </Card>
-  );
-}
-
-/** Human labels for the five named severity component keys (presentation only). Mirrors the Market-Phase
- *  card so the compact breakdown reads identically to the detail card (single source). */
-const SEVERITY_COMPONENT_LABELS: Record<string, string> = {
-  drawdown_depth: "Drawdown depth",
-  time_underwater: "Time underwater",
-  regime_risk: "Market regime (stored)",
-  breadth_below_200dma: "Breadth below 200-DMA",
-  vix_gate: "VIX stress gate",
-};
-
-/** The compact named severity breakdown for the at-a-glance phase figure (every component with its [0,1]
- *  value + contribution; NA honestly marked) — the SAME values the detail card shows (single source). */
-function SeverityBreakdown({ components }: { components: MarketPhaseComponent[] }) {
-  return (
-    <div className="space-y-1.5 pt-1">
-      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 text-xs uppercase tracking-wide text-text-faint">
-        <span>Severity driver</span>
-        <span className="text-right">Value</span>
-        <span className="text-right">Contribution</span>
-      </div>
-      {components.map((component) => (
-        <div key={component.name} className="grid grid-cols-[1fr_auto_auto] items-center gap-x-4 text-xs">
-          <span className="text-text-muted">
-            {SEVERITY_COMPONENT_LABELS[component.name] ?? component.name}
-          </span>
-          <span className={cn("num text-right", component.available ? "text-text-faint" : "text-warn")}>
-            {component.available && component.value != null ? component.value.toFixed(2) : "NA"}
-          </span>
-          <span className="num text-right text-text">
-            {component.contribution == null ? "—" : component.contribution.toFixed(2)}
-          </span>
-        </div>
-      ))}
-    </div>
-  );
-}
-
-/** J-98: the collapsed "More detail" section — breadth metrics, candidate counts, Top Sectors, Top Themes,
- *  and the full Market Phase & Severity detail card. SAME data, SAME endpoints, only repositioned (nothing
- *  removed). Defaults to COLLAPSED at first paint (the spec: first paint shows only the summary + chart). */
-function MoreDetailSection({
-  dashboard,
-  sectors,
-  themes,
-}: {
-  dashboard: DashboardResponse;
-  sectors: SectorsResponse | null;
-  themes: ThemesResponse | null;
-}) {
-  const [open, setOpen] = usePersistedToggle("trendora.dashboard.moreDetail", false);
-  const { breadth } = dashboard;
-  const topSectors = sectors ? sectors.rows.slice(0, 5) : [];
-  const topThemes = themes ? themes.rows.slice(0, 5) : [];
-
-  return (
-    <Card>
-      <button
-        type="button"
-        onClick={() => setOpen(!open)}
-        aria-expanded={open}
-        className={cn(
-          "flex w-full items-center justify-between gap-2 px-5 py-3 text-left",
-          "transition-colors hover:bg-surface-2 focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
-        )}
-      >
-        <span className="flex items-center gap-2">
-          <CardTitle>More detail</CardTitle>
-          <span className="text-xs text-text-muted">
-            Breadth · candidate counts · Top Sectors · Top Themes · Market Phase detail
-          </span>
-        </span>
-        <ChevronDown
-          className={cn("h-4 w-4 text-text-muted transition-transform", open ? "rotate-180" : "")}
-          aria-hidden
-        />
-      </button>
-      {open ? (
-        <CardContent className="space-y-4 border-t border-border pt-4">
-          {/* breadth metrics (relocated, unchanged) */}
-          <div className="grid gap-4 sm:grid-cols-3">
-            <MetricCard
-              title="Breadth · above 50-DMA"
-              term="breadth > 50-DMA"
-              value={fmtPct(breadth.above_50dma_pct)}
-              caption={breadth.label}
-            />
-            <MetricCard
-              title="Breadth · above 200-DMA"
-              term="breadth > 200-DMA"
-              value={fmtPct(breadth.above_200dma_pct)}
-              caption={breadth.label}
-            />
... [diff_bound] apps/frontend/app/page.tsx: 154 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/components/sidebar.tsx b/apps/frontend/components/sidebar.tsx
index b7a1e99a..a4cdbfe3 100644
--- a/apps/frontend/components/sidebar.tsx
+++ b/apps/frontend/components/sidebar.tsx
@@ -4,6 +4,7 @@ import Link from "next/link";
 import { usePathname } from "next/navigation";
 import {
   BookOpen,
+  Compass,
   Database,
   FlaskConical,
   Grid2x2,
@@ -28,8 +29,12 @@ interface NavItem {
 
 // The approved Information Architecture (blueprint). Stock Detail and Run Detail are
 // intentionally NOT here — they are reached from a leaderboard / run row.
+// goal-market-compass iter-28 (J-07/J-08): `/` renamed "Dashboard" -> "Today" (the new ten-second
+// compass read); "Market" is a NEW entry immediately after it, carrying the former dashboard body
+// (relocated verbatim to `/market`). Every other entry keeps its route/order/label unchanged.
 const NAV: NavItem[] = [
-  { href: "/", label: "Dashboard", icon: LayoutDashboard },
+  { href: "/", label: "Today", icon: Compass },
+  { href: "/market", label: "Market", icon: LayoutDashboard },
   { href: "/stocks", label: "Stocks", icon: TrendingUp },
   { href: "/themes", label: "Themes", icon: Layers },
   { href: "/sectors", label: "Sectors", icon: Grid2x2 },
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index a889ae72..9be729f3 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -923,6 +923,25 @@ export interface Narrative {
   sentences: NarrativeSentence[];
 }
 
+// --- state_band (goal-market-compass iter-28, J-07) ------------------------------------------
+/** One `state_band.<band>` entry — a direction word (one of `compass.vocabulary.direction_words`'
+ *  three values) plus its signed delta. BOTH are `null` together when no comparison is possible for
+ *  that band (no prior stored run, or a missing per-band input) — never a fabricated word. */
+export interface CompassStateBandEntry {
+  direction_word: string | null;
+  delta: number | null;
+}
+
+/** The `state_band` CONTENT block (J-07) — three direction words (regime/stress/breadth), computed
+ *  ONCE at ingest inside `build_manifest_payload` and served verbatim; the frontend evaluates no
+ *  threshold and selects no word. `null` (the WHOLE block, not per-band) on any manifest row minted
+ *  before this field existed ("pre-state_band era" — honestly rendered, never fabricated). */
+export interface CompassStateBand {
+  regime: CompassStateBandEntry;
+  stress: CompassStateBandEntry;
+  breadth: CompassStateBandEntry;
+}
+
 /** The fixed eligibility-checklist verdict vocabulary (J-04). */
 export type ChecklistVerdict = "Pass" | "Miss" | "Supportive" | "Neutral" | "Unknown" | "NA";
 
@@ -1093,6 +1112,9 @@ export interface CompassResponse {
   frozen: boolean;
   session_delta: SessionDelta;
   narrative: Narrative;
+  // goal-market-compass iter-28 (J-07) — additive, `null` on any manifest minted before this field
+  // existed (see `CompassStateBand`'s own doc comment).
+  state_band: CompassStateBand | null;
   selection: CompassSelection;
   comparison_cohort: CompassComparisonCohortRow[];
   near_threshold_shadow: CompassCohortRow[];
diff --git a/config.yaml b/config.yaml
index 52cf1586..9d9141ff 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1408,6 +1408,7 @@ compass:
     top_k: 5                         # max sector-kind and max theme-kind change entries shown (most-moved first; mirrors the existing Top-Sectors/Top-Themes "top 5" convention)
     max_stock_items: 10              # max stock-kind change entries evaluated/shown (bounds both compute and display — AG-8)
     velocity_flat_band: 2.0          # |regime-score delta| below this reads as "little changed" in the narrative's direction sentence
+    stress_velocity_flat_band: 5.0   # goal-market-compass iter-28 (J-07): |severity delta| below this reads as "little changed" for state_band.stress (a dedicated key -- severity is a different 0-100 scale than the regime score, not a reuse of velocity_flat_band above). state_band.breadth reuses breadth_min_change_pts below unchanged.
     pbear_bands:                     # filtered P(bear) -> narrative state word (ascending min, like market_phase.phase_edges)
       - { min: 0.0, label: "calm" }
       - { min: 0.20, label: "cautious" }
```

## Excluded-path stat (dependency/lockfile visibility)

 .../trendora-next-session-manifest-v1.schema.json  |   1 +
 reports/goal-session-market-compass-index.html     |  11 +-
 .../.engine.lock/boot_id                           |   2 +-
 .../goal-session-market-compass/.engine.lock/epoch |   2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |   2 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-market-compass/engine.pid        |   2 +-
 runs/goal-session-market-compass/session.json      |   8 +-
 .../state/assumptions.md                           | 165 --------------------
 .../state/assumptions.md.archive.md                | 168 +++++++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  |  36 +----
 .../state/lessons.md.archive.md                    |  45 ++++++
 runs/goal-session-market-compass/summary.md        |  70 ++++++---
 runs/goal-session-market-compass/telemetry.jsonl   |  65 ++++++++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   3 +
 16 files changed, 352 insertions(+), 234 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
