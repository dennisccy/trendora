# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 10. Shown in full: 10.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index f0fc5c63..2b8c6097 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -2576,6 +2576,11 @@ class CompassDeltaCfg(BaseModel):
     rank_move_min: int
     stock_score_min_change: float
     top_k: int
+    # goal-market-compass iter-36 (J-13) -- the Leadership rotation section's OWN display cap on
+    # session_delta.rotation.{sector,theme}.{gaining,losing}, independent of `top_k` above (which still
+    # governs ONLY session_delta.changes, unchanged). An above-threshold mover beyond this cap is
+    # disclosed in that side's `residual_count`, never dropped uncounted.
+    rotation_top_k: int
     max_stock_items: int
     velocity_flat_band: float
     # goal-market-compass iter-28 (J-07) — the `state_band.stress` flat-band edge (severity-points
@@ -2602,6 +2607,8 @@ class CompassDeltaCfg(BaseModel):
             raise ValueError("compass.delta.rank_move_min must be positive")
         if self.top_k <= 0:
             raise ValueError("compass.delta.top_k must be positive")
+        if self.rotation_top_k <= 0:
+            raise ValueError("compass.delta.rotation_top_k must be positive")
         if self.max_stock_items <= 0:
             raise ValueError("compass.delta.max_stock_items must be positive")
         return self
@@ -2748,6 +2755,7 @@ def _default_compass() -> "CompassCfg":
             rank_move_min=2,
             stock_score_min_change=8.0,
             top_k=5,
+            rotation_top_k=5,
             max_stock_items=10,
             velocity_flat_band=2.0,
             stress_velocity_flat_band=5.0,
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index fb921cae..b97754f5 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1,8 +1,8 @@
 """app.engine.compass — the deterministic narrative + candidate-selection trace + manifest assembly
 (goal-market-compass iter-2, J-03/J-04, CONTENT block; iter-3, J-05/J-06, the freeze/integrity block;
-iter-28, J-07, the `state_band` CONTENT block).
+iter-28, J-07, the `state_band` CONTENT block; iter-36, J-13, the `session_delta.rotation` CONTENT block).
 
-Four CONTENT producers, one assembler:
+Five CONTENT producers, one assembler:
 
   - `build_narrative(...)` — deterministic template sentences (state / direction / breadth /
     focus-count, plus a no-comparison / NA-velocity / retrospective-stamp variant where it applies),
@@ -25,10 +25,20 @@ Four CONTENT producers, one assembler:
     (never a second word map) and the SAME `_flat_band_word` classifier `_direction_word` already used.
     No-prior-run or a missing per-word input renders that word's explicit null/no-comparison state —
     never a fabricated word (mirrors `session_delta`'s and `narrative`'s own no-prior-run handling).
-  - `build_manifest_payload(...)` — assembles `session_delta` + `narrative` + `selection` +
-    `state_band` into one content document and computes `content_hash` (sha256 over the sorted-key
-    JSON of the content block only — unchanged scope/contract from iter-2, including the cohorts
-    nested inside `selection` and, since iter-28, `state_band` alongside them).
+  - `build_rotation(...)` — iter-36 (J-13): `session_delta.rotation.{sector,theme}` — two labelled,
+    signed, both-directions (`gaining`/`losing`) sides per group kind, built from the SAME sector/theme
+    rank pairs `session_delta.sector_rank_pairs`/`theme_rank_pairs` computes (no second computation),
+    each side capped by the NEW `compass.delta.rotation_top_k` and a complete per-kind accounting
+    (`shown_count`/`suppressed_count`/`residual_count`/`configured_total`) that discloses an
+    above-threshold mover beyond the cap rather than dropping it uncounted (the exact defect this
+    iteration fixes). The SAME signed `delta` + a served `direction_word` additionally ride the
+    sector/theme-kind entries of `session_delta.changes` (single computation, two placements) — group-
+    level only, no stock-kind row anywhere in `rotation` (Non-Goal).
+  - `build_manifest_payload(...)` — assembles `session_delta` (now including `rotation`) + `narrative` +
+    `selection` + `state_band` into one content document and computes `content_hash` (sha256 over the
+    sorted-key JSON of the content block only — unchanged scope/contract from iter-2, including the
+    cohorts nested inside `selection`, `state_band` alongside them since iter-28, and `session_delta.
+    rotation` since iter-36).
 
 The freeze/integrity block (iter-3, J-05/J-06) — `_freeze_manifest` is the ONE writer behind all three
 producer paths:
@@ -76,7 +86,14 @@ from app.config import Config, REPO_ROOT, get_config
 from app.engine import engine_identity, evidence, market_phase, readiness
 from app.engine.prices import latest_data_date
 from app.engine.research import _dataset_version  # single-sourced dataset stamp (J-72) — never duplicated
-from app.engine.session_delta import compute_delta, find_previous_run
+from app.engine.session_delta import (
+    KIND_SECTOR,
+    KIND_THEME,
+    compute_delta,
+    find_previous_run,
+    sector_rank_pairs,
+    theme_rank_pairs,
+)
 from app.engine.setups import RISK_OFF_LABEL
 from app.engine.snapshot_serving import dashboard_payload
 from app.engine.universe_screen import POOL_SURVIVORSHIP_LABEL, read_pool
@@ -345,6 +362,113 @@ def build_state_band(
     }
 
 
+# --- rotation (iter-36, J-13) -------------------------------------------------------------------
+
+
+def _rank_direction_word(delta: int, cfg: Config) -> str:
+    """The sector/theme rank-delta -> `direction_word` classifier (goal-market-compass iter-36, J-13) --
+    reuses the SAME `_flat_band_word`/`compass.vocabulary.direction_words` map every other direction word
+    in this module uses (never a second word map). `flat_band` reuses `compass.delta.rank_move_min`
+    itself: every caller here already gated the row to `abs(delta) >= rank_move_min`, so the word is
+    never "flat" for a displayed row -- no separate threshold key is needed (AG-15: not a new/retuned
+    threshold, just the SAME gate reused as the word classifier's flat-band). Polarity is resolved
+    engine-side: a FALLING rank number (`delta < 0`) is an IMPROVING position, so `delta` is NEGATED
+    before classifying -- mirrors the `state_band.stress` sign-transform precedent above (a falling
+    severity is also "up"/improving)."""
+    return _flat_band_word(-delta, cfg.compass.delta.rank_move_min, cfg)
+
+
+def _rotation_row(entry: dict, cfg: Config) -> dict:
+    """One `session_delta.rotation.<kind>.{gaining,losing}` row from a `session_delta.py` sector/theme
+    pair entry (already carries a signed `delta`) -- the served shape only (label/from/to/delta/
+    direction_word/drill_href); the internal `kind`/`magnitude`/`threshold` fields stay session_delta's
+    own concern and are not repeated here."""
+    return {
+        "label": entry["label"],
+        "from": entry["from"],
+        "to": entry["to"],
+        "delta": entry["delta"],
+        "direction_word": _rank_direction_word(entry["delta"], cfg),
+        "drill_href": entry["drill_href"],
+    }
+
+
+def _rotation_kind(pairs: list[tuple[dict, float]], cfg: Config, configured_total: int) -> dict:
+    """One group kind's (`sector` | `theme`) rotation block: two labelled, both-directions sides plus a
+    complete accounting (goal-market-compass iter-36, J-13) -- built from `pairs`, the SAME uncapped
+    signed-delta pairs `session_delta.sector_rank_pairs`/`theme_rank_pairs` already computed (no second
+    computation), already sorted most-moved-first.
+
+    `gaining` = an IMPROVING position (`delta < 0`, rank number fell); `losing` = a DETERIORATING one
+    (`delta > 0`); a pair that clears `rank_move_min` can never have `delta == 0` (the gate requires
+    `abs(delta) >= rank_move_min >= 1`), so every above-threshold pair lands in exactly one side.
+
+    Accounting: `shown_count` (rows actually returned, both sides, after the `rotation_top_k` cap) +
+    `suppressed_count` (below-`rank_move_min` pairs) + `residual_count` (above-threshold pairs beyond the
+    cap on EITHER side -- disclosed, never dropped, unlike the prior defect this iteration fixes) sums to
+    exactly `len(pairs)`, which equals `configured_total` whenever both runs score the full configured
+    universe (the fixed sector/industry and theme catalogs always do)."""
+    threshold = cfg.compass.delta.rank_move_min
+    cap = cfg.compass.delta.rotation_top_k
+    above = [(entry, magnitude) for entry, magnitude in pairs if magnitude >= threshold]
+    suppressed_count = len(pairs) - len(above)
+    gaining_all = [entry for entry, _magnitude in above if entry["delta"] < 0]
+    losing_all = [entry for entry, _magnitude in above if entry["delta"] > 0]
+    gaining = gaining_all[:cap]
+    losing = losing_all[:cap]
+    residual_count = (len(gaining_all) - len(gaining)) + (len(losing_all) - len(losing))
+    return {
+        "gaining": [_rotation_row(entry, cfg) for entry in gaining],
+        "losing": [_rotation_row(entry, cfg) for entry in losing],
+        "shown_count": len(gaining) + len(losing),
+        "suppressed_count": suppressed_count,
+        "residual_count": residual_count,
+        "configured_total": configured_total,
+    }
+
+
+def _rotation_no_prior(configured_total: int) -> dict:
+    """One kind's explicit no-prior-run rotation state (TC-9) -- no deltas, no direction words, no
+    fabricated rows, consistent with `session_delta`'s own top-level no-prior-run branch. `configured_total`
+    is a static config fact (not a comparison result), so it is still reported honestly here."""
+    return {
+        "gaining": [], "losing": [], "shown_count": 0, "suppressed_count": 0,
+        "residual_count": 0, "configured_total": configured_total,
+    }
+
+
+def build_rotation(
+    previous_run: Optional[ScannerRun],
+    sector_pairs: list[tuple[dict, float]],
+    theme_pairs: list[tuple[dict, float]],
+    cfg: Config,
+) -> dict:
+    """The `session_delta.rotation` CONTENT block (goal-market-compass iter-36, J-13) -- two labelled,
+    signed, both-directions sides per group kind (`sector`, `theme`), built from the SAME sector/theme
+    rank pairs `compute_delta` already computes (`sector_pairs`/`theme_pairs`, passed in by
+    `build_manifest_payload` -- no second computation). Group-level only -- no stock-kind row anywhere
+    here (Non-Goal, J-13 step 1). `previous_run is None` renders each kind's explicit no-prior-run state
+    (TC-9)."""
+    sector_total = len(cfg.etfs.sector) + len(cfg.etfs.industry)
+    theme_total = len(cfg.themes)
+    if previous_run is None:
+        return {"sector": _rotation_no_prior(sector_total), "theme": _rotation_no_prior(theme_total)}
+    return {
+        "sector": _rotation_kind(sector_pairs, cfg, sector_total),
+        "theme": _rotation_kind(theme_pairs, cfg, theme_total),
+    }
+
+
+def _attach_rank_direction_words(changes: list[dict], cfg: Config) -> None:
+    """TC-6: mutates sector/theme-kind entries of `session_delta.changes` IN PLACE, attaching the SAME
+    `direction_word` their rotation-row counterpart carries -- `delta` already rides these entries from
+    `session_delta.py`'s `_entry` calls (single computation); this adds ONLY the served word, via the SAME
+    `_rank_direction_word` helper `_rotation_row` uses (single computation, two placements, goal.md)."""
+    for entry in changes:
+        if entry["kind"] in (KIND_SECTOR, KIND_THEME) and "delta" in entry:
+            entry["direction_word"] = _rank_direction_word(entry["delta"], cfg)
+
+
 # --- selection (J-04; iter-3 J-05/J-06 adds comparison_cohort + near_threshold_shadow) --------
 
 _QUALIFIER_CHECKS = ("leadership_min_score", "entry_min_score", "risk_max_score")
@@ -794,9 +918,17 @@ def build_manifest_payload(
     block only — never re-derived at serve time; see `manifest_row_payload`). `selection` carries
     `comparison_cohort` / `near_threshold_shadow` (iter-3); `state_band` (iter-28, J-07) is a new
     top-level content block alongside `session_delta`/`narrative`/`selection` — additive to
-    `content_hash`'s scope, no other code change needed for that."""
+    `content_hash`'s scope, no other code change needed for that.
+
+    iter-36 (J-13): `sector_pairs`/`theme_pairs` are computed ONCE here (when `previous_run` exists) and
+    passed into BOTH `compute_delta` (so its own sector/theme classify+cap reuses them, no second query)
+    and `build_rotation` (`session_delta.rotation`) — one pair-building DB read per manifest build."""
     cfg = config or get_config()
-    delta = compute_delta(session, current_run, previous_run, cfg)
+    sector_pairs = sector_rank_pairs(session, current_run, previous_run, cfg) if previous_run is not None else []
+    theme_pairs = theme_rank_pairs(session, current_run, previous_run, cfg) if previous_run is not None else []
+    delta = compute_delta(session, current_run, previous_run, cfg, sector_pairs=sector_pairs, theme_pairs=theme_pairs)
+    _attach_rank_direction_words(delta["changes"], cfg)
+    delta["rotation"] = build_rotation(previous_run, sector_pairs, theme_pairs, cfg)
     selection = evaluate_selection(session, current_run, cfg)
     narrative = build_narrative(session, current_run, previous_run, selection, cfg)
     state_band = build_state_band(session, current_run, previous_run, cfg)
diff --git a/apps/backend/app/engine/session_delta.py b/apps/backend/app/engine/session_delta.py
index 363085fb..dd99e020 100644
--- a/apps/backend/app/engine/session_delta.py
+++ b/apps/backend/app/engine/session_delta.py
@@ -11,6 +11,14 @@ Reads ONLY column-projected `ScannerResult` / `SectorScoreRow` / `ThemeScoreRow`
 `record_json` sweep (AG-8); `ScannerRun` itself carries no such blob so its typed columns are read
 directly. Compares only two ALREADY-STORED, already-computed runs — there is no `forward_returns` or
 post-as-of bar for this module to read even by accident (AG-5).
+
+`sector_rank_pairs(session, current_run, previous_run, config)` / `theme_rank_pairs(...)`
+(goal-market-compass iter-36, J-13): the full, uncapped, signed-`delta` sector/theme rank-pair
+computation `_sector_changes`/`_theme_changes` (feeding `session_delta.changes`, still `top_k`-capped,
+unchanged behavior) and `app.engine.compass.build_rotation` (`session_delta.rotation`, independently
+`rotation_top_k`-capped, both directions) both build from — one query pair per manifest build, two
+capped consumers. Sector/theme-kind `changes[]` entries additionally carry this signed `delta`
+(direction-word wording is compass.py's concern — it owns `compass.vocabulary`, this module does not).
 """
 from __future__ import annotations
 
@@ -48,8 +56,11 @@ def _drill_href(kind: str, as_of_iso: str, ticker: Optional[str] = None) -> str:
     return f"/?asof={as_of_iso}"
 
 
-def _entry(kind: str, label: str, frm, to, magnitude: float, threshold: float, drill_href: str) -> dict:
-    return {
+def _entry(
+    kind: str, label: str, frm, to, magnitude: float, threshold: float, drill_href: str,
+    delta: Optional[int] = None,
+) -> dict:
+    entry = {
         "kind": kind,
         "label": label,
         "from": frm,
@@ -58,6 +69,11 @@ def _entry(kind: str, label: str, frm, to, magnitude: float, threshold: float, d
         "threshold": threshold,
         "drill_href": drill_href,
     }
+    # goal-market-compass iter-36 (J-13): a SIGNED rank delta rides sector/theme-kind entries only (never
+    # market/breadth/stock) -- additive, so the older entry shape is unchanged for every other kind.
+    if delta is not None:
+        entry["delta"] = delta
+    return entry
 
 
 def _classify(pairs: list[tuple[dict, float]], threshold: float) -> tuple[list[dict], list[dict]]:
@@ -102,10 +118,21 @@ def _breadth_changes(
     return _classify(pairs, threshold)
 
 
-def _sector_changes(
-    session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
-) -> tuple[list[dict], list[dict]]:
+def sector_rank_pairs(
+    session: Session, current: ScannerRun, previous: ScannerRun, config: Optional[Config] = None
+) -> list[tuple[dict, float]]:
+    """ALL comparable sector/industry rank pairs between `current` and `previous` (goal-market-compass
+    iter-36, J-13) — BEFORE any `rank_move_min` gate or `top_k`/`rotation_top_k` cap is applied, most-
+    moved-first (stable sort — ties keep the deterministic ticker-ordered input). Each entry carries a
+    SIGNED `delta` (`cur_rank - prev_rank`; a FALLING rank number is an IMPROVING position) alongside the
+    existing `magnitude`/`from`/`to`/`drill_href` shape. This is the ONE pair-building computation both
+    `_sector_changes` (feeding the existing `session_delta.changes`/`suppressed`, `top_k`-capped) and
+    `app.engine.compass.build_rotation` (`rotation_top_k`-capped, both directions) read — callers that
+    already hold these pairs should pass them straight into `compute_delta` so the DB is queried only
+    once per manifest build (see `compass.build_manifest_payload`)."""
+    cfg = config or get_config()
     threshold = cfg.compass.delta.rank_move_min
+    as_of_iso = current.asof_date.isoformat()
     cur_rows = session.exec(
         select(SectorScoreRow.ticker, SectorScoreRow.name, SectorScoreRow.rank)
         .where(SectorScoreRow.run_id == current.id)
@@ -123,20 +150,27 @@ def _sector_changes(
         prev_rank = prev_by_ticker.get(ticker)
         if prev_rank is None:
             continue  # the sector/industry ETF universe is fixed (config.etfs.*) — never new-to-universe
-        magnitude = float(abs(cur_rank - prev_rank))
-        entry = _entry(KIND_SECTOR, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_SECTOR, as_of_iso))
+        delta = cur_rank - prev_rank
+        magnitude = float(abs(delta))
+        entry = _entry(
+            KIND_SECTOR, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_SECTOR, as_of_iso),
+            delta=delta,
+        )
         pairs.append((entry, magnitude))
-    # Most-moved first within the kind (stable sort — ties keep the deterministic ticker-ordered input),
-    # THEN cap at top_k (mirrors the existing Top-Sectors "top 5" display convention elsewhere in the app).
+    # Most-moved first (stable sort — ties keep the deterministic ticker-ordered input); no cap here — the
+    # two callers apply their OWN independent cap (top_k vs rotation_top_k).
     pairs.sort(key=lambda pair: pair[1], reverse=True)
-    changes, suppressed = _classify(pairs, threshold)
-    return changes[: cfg.compass.delta.top_k], suppressed
+    return pairs
 
 
-def _theme_changes(
-    session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
-) -> tuple[list[dict], list[dict]]:
+def theme_rank_pairs(
+    session: Session, current: ScannerRun, previous: ScannerRun, config: Optional[Config] = None
+) -> list[tuple[dict, float]]:
+    """Theme-kind counterpart of `sector_rank_pairs` (see its docstring for the full contract) — same
+    signed-`delta` shape, same "one computation, multiple capped consumers" posture."""
+    cfg = config or get_config()
     threshold = cfg.compass.delta.rank_move_min
+    as_of_iso = current.asof_date.isoformat()
     cur_rows = session.exec(
         select(ThemeScoreRow.slug, ThemeScoreRow.name, ThemeScoreRow.rank)
         .where(ThemeScoreRow.run_id == current.id)
@@ -154,11 +188,27 @@ def _theme_changes(
         prev_rank = prev_by_slug.get(slug)
         if prev_rank is None:
             continue  # the theme universe is fixed (config.themes) — never new-to-universe
-        magnitude = float(abs(cur_rank - prev_rank))
-        entry = _entry(KIND_THEME, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_THEME, as_of_iso))
+        delta = cur_rank - prev_rank
+        magnitude = float(abs(delta))
+        entry = _entry(
+            KIND_THEME, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_THEME, as_of_iso),
+            delta=delta,
+        )
         pairs.append((entry, magnitude))
     pairs.sort(key=lambda pair: pair[1], reverse=True)
-    changes, suppressed = _classify(pairs, threshold)
+    return pairs
+
+
+def _sector_changes(pairs: list[tuple[dict, float]], cfg: Config) -> tuple[list[dict], list[dict]]:
+    """`session_delta.changes`/`suppressed`'s sector-kind slice — classify + cap at the EXISTING `top_k`
+    (unchanged behavior/value). `pairs` is `sector_rank_pairs`'s full output — no second query."""
+    changes, suppressed = _classify(pairs, cfg.compass.delta.rank_move_min)
+    return changes[: cfg.compass.delta.top_k], suppressed
+
+
+def _theme_changes(pairs: list[tuple[dict, float]], cfg: Config) -> tuple[list[dict], list[dict]]:
+    """Theme-kind counterpart of `_sector_changes` (see its docstring)."""
+    changes, suppressed = _classify(pairs, cfg.compass.delta.rank_move_min)
     return changes[: cfg.compass.delta.top_k], suppressed
 
 
@@ -221,22 +271,35 @@ def compute_delta(
     current_run: ScannerRun,
     previous_run: Optional[ScannerRun],
     config: Optional[Config] = None,
+    sector_pairs: Optional[list[tuple[dict, float]]] = None,
+    theme_pairs: Optional[list[tuple[dict, float]]] = None,
 ) -> dict:
     """The `session_delta` CONTENT block (goal-market-compass iter-2, J-02). `previous_run` is the
     immediately preceding STORED run (see `find_previous_run`), or `None` for the earliest stored run —
-    the explicit no-prior-run state (TC-6): no deltas, no direction words, nothing fabricated."""
+    the explicit no-prior-run state (TC-6): no deltas, no direction words, nothing fabricated.
+
+    `sector_pairs`/`theme_pairs` (goal-market-compass iter-36, J-13): optional PRECOMPUTED
+    `sector_rank_pairs`/`theme_rank_pairs` output. A caller that also needs the full pairs (e.g.
+    `app.engine.compass.build_manifest_payload`, to build `session_delta.rotation`) computes them once
+    and passes them in here so the DB is queried only once per manifest build; omitted, they are computed
+    the same way internally (unchanged behavior for every other caller)."""
     cfg = config or get_config()
     if previous_run is None:
         return {"prior_as_of": None, "gap_days": None, "changes": [], "suppressed": [], "suppressed_count": 0}
 
     as_of_iso = current_run.asof_date.isoformat()
+    if sector_pairs is None:
+        sector_pairs = sector_rank_pairs(session, current_run, previous_run, cfg)
+    if theme_pairs is None:
+        theme_pairs = theme_rank_pairs(session, current_run, previous_run, cfg)
+
     changes: list[dict] = []
     suppressed: list[dict] = []
     for changes_part, suppressed_part in (
         _market_changes(current_run, previous_run, as_of_iso, cfg),
         _breadth_changes(current_run, previous_run, as_of_iso, cfg),
-        _sector_changes(session, current_run, previous_run, as_of_iso, cfg),
-        _theme_changes(session, current_run, previous_run, as_of_iso, cfg),
+        _sector_changes(sector_pairs, cfg),
+        _theme_changes(theme_pairs, cfg),
         _stock_changes(session, current_run, previous_run, as_of_iso, cfg),
     ):
         changes.extend(changes_part)
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
index db050f4c..b3e648ce 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -94,8 +94,16 @@ def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
     # NOTES: assert every new field at the response layer itself -- never behind a fixture-data gate.
     assert result["as_of"] == "2024-06-08"
     assert isinstance(result["session_delta"], dict)
-    for key in ("prior_as_of", "gap_days", "changes", "suppressed", "suppressed_count"):
+    for key in ("prior_as_of", "gap_days", "changes", "suppressed", "suppressed_count", "rotation"):
         assert key in result["session_delta"]
+    # goal-market-compass iter-36 (J-13): the rotation block itself, served directly (no sector/theme
+    # rank data seeded by this fixture, so both kinds honestly show zero rows -- still fully shaped).
+    rotation = result["session_delta"]["rotation"]
+    assert set(rotation.keys()) == {"sector", "theme"}
+    for kind, total in (("sector", len(cfg.etfs.sector) + len(cfg.etfs.industry)), ("theme", len(cfg.themes))):
+        block = rotation[kind]
+        assert block["gaining"] == [] and block["losing"] == []
+        assert block["configured_total"] == total
     assert isinstance(result["narrative"], dict) and "sentences" in result["narrative"]
     assert isinstance(result["selection"], dict)
     for key in ("candidates", "why_not", "disposition_tally", "candidates_empty_reason"):
@@ -130,6 +138,41 @@ def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
     ]
 
 
+def test_compass_route_serves_legacy_pre_iter36_row_without_rotation_key(compass_engine, cfg):
+    """goal-market-compass iter-36 fix (reviewer CRITICAL): the shape the Today page's Leadership
+    rotation section must survive on as-of navigation. Every `next_session_manifests` row minted BEFORE
+    iter-36 stores a `session_delta` blob with NO `rotation` key at all (the key was added INSIDE the
+    existing blob, and a frozen row is never rewritten — AG-12), and `manifest_row_payload` serves those
+    bytes verbatim. So `GET /api/compass` for such an as-of legitimately returns a NON-NULL `prior_as_of`
+    (a real prior session exists) together with an ABSENT `rotation` — a third state, distinct from both
+    the no-prior-run state and an empty side. Asserted at the ROUTE layer (not just
+    `manifest_row_payload`) because that is the exact payload the frontend consumes; the frontend's
+    matching guard is type-enforced by `SessionDelta.rotation?:` in `apps/frontend/lib/api.ts`."""
+    from app.api.compass import compass as compass_route
+
+    _freeze_frontier(compass_engine, cfg)
+    # Simulate a pre-iter-36 row by stripping the key this iteration's write path added -- byte-for-byte
+    # the shape of every row already stored before this iteration shipped.
+    with Session(compass_engine) as session:
+        row = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))).first()
+        stored = json.loads(row.session_delta_json)
+        assert "rotation" in stored  # sanity: the current write path DOES add it
+        del stored["rotation"]
+        row.session_delta_json = json.dumps(stored)
+        session.add(row)
+        session.commit()
+
+    with Session(compass_engine) as session:
+        result = compass_route(None, session)
+
+    session_delta = result["session_delta"]
+    assert session_delta["prior_as_of"] == "2024-06-01"  # a real prior session -- NOT the no-prior-run state
+    assert "rotation" not in session_delta  # honestly absent, never fabricated/backfilled
+    # the rest of the legacy block is served unchanged -- only `rotation` is missing
+    for key in ("gap_days", "changes", "suppressed", "suppressed_count"):
+        assert key in session_delta
+
+
 @pytest.fixture()
 def compass_engine_two_candidates(tmp_path):
     """goal-market-compass iter-35 (J-12, TC-8): two `ScannerRun` rows each carrying TWO `ScannerResult`
diff --git a/apps/backend/tests/test_compass.py b/apps/backend/tests/test_compass.py
index 59a847fa..a027d138 100644
--- a/apps/backend/tests/test_compass.py
+++ b/apps/backend/tests/test_compass.py
@@ -17,7 +17,7 @@ from sqlmodel import Session, SQLModel, create_engine, select
 from app.config import load_config
 from app.engine import compass
 from app.engine import market_phase as market_phase_module
-from app.models import MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun
+from app.models import MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow
 
 
 @pytest.fixture()
@@ -788,3 +788,280 @@ def test_no_network_or_lookahead_imports_in_compass_module():
         if isinstance(node, ast.Attribute) and node.attr in banned:
             offenders.add(node.attr)
     assert not offenders, f"compass.py references banned identifiers: {offenders}"
+
+
+# --- rotation (goal-market-compass iter-36, J-13) ------------------------------------------------
+
+
+def _mk_sector_row(session: Session, run_id: int, ticker: str, rank: int, kind: str = "sector") -> None:
+    session.add(SectorScoreRow(
+        run_id=run_id, ticker=ticker, kind=kind, name=ticker, members_json="[]",
+        score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=rank,
+    ))
+
+
+def _mk_theme_row(session: Session, run_id: int, slug: str, rank: int) -> None:
+    session.add(ThemeScoreRow(
+        run_id=run_id, slug=slug, name=slug, score=80.0, bucket="A", members_json="[]",
+        breadth_label="universe-relative", trend_label="Uptrend", components_json="{}", rank=rank,
+    ))
+
+
+@pytest.fixture()
+def rotation_run_pair(engine, cfg):
+    """A small run pair with BOTH sides populated for both kinds, plus one below-threshold (suppressed)
+    pair per kind (`rank_move_min` is 2 in the real config):
+      sector XLK: rank 1 -> 5 (delta +4, LOSING)   sector XLE: rank 5 -> 1 (delta -4, GAINING)
+      sector XLF: rank 2 -> 2 (delta 0, suppressed)
+      theme  ai:  rank 1 -> 4 (delta +3, LOSING)   theme  ev:  rank 4 -> 1 (delta -3, GAINING)
+      theme  cyber: rank 2 -> 2 (delta 0, suppressed)
+    """
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 5, 1))
+        run_b = _mk_run(session, date(2024, 5, 8))
+        _mk_sector_row(session, run_a.id, "XLK", 1)
+        _mk_sector_row(session, run_b.id, "XLK", 5)
+        _mk_sector_row(session, run_a.id, "XLE", 5)
+        _mk_sector_row(session, run_b.id, "XLE", 1)
+        _mk_sector_row(session, run_a.id, "XLF", 2)
+        _mk_sector_row(session, run_b.id, "XLF", 2)
+        _mk_theme_row(session, run_a.id, "ai", 1)
+        _mk_theme_row(session, run_b.id, "ai", 4)
+        _mk_theme_row(session, run_a.id, "ev", 4)
+        _mk_theme_row(session, run_b.id, "ev", 1)
+        _mk_theme_row(session, run_a.id, "cyber", 2)
+        _mk_theme_row(session, run_b.id, "cyber", 2)
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        return run_a.id, run_b.id
+
+
+@pytest.fixture()
+def all_gainers_sector_run_pair(engine, cfg):
+    """J-13 step 8 (dev handoff citation): EVERY threshold-crossing sector mover is a GAINER -- the losing
+    side must render its explicit empty state while the gaining side is unaffected. One suppressed
+    (below-threshold) row rides alongside so the fixture also proves suppressed != empty-losing."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 5, 15))
+        run_b = _mk_run(session, date(2024, 5, 22))
+        _mk_sector_row(session, run_a.id, "XLK", 5)
+        _mk_sector_row(session, run_b.id, "XLK", 1)  # delta -4, gaining
+        _mk_sector_row(session, run_a.id, "XLE", 4)
+        _mk_sector_row(session, run_b.id, "XLE", 2)  # delta -2, gaining
+        _mk_sector_row(session, run_a.id, "XLF", 3)
+        _mk_sector_row(session, run_b.id, "XLF", 3)  # delta 0, suppressed
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        return run_a.id, run_b.id
+
+
+@pytest.fixture()
+def full_universe_rotation_runs(engine, cfg):
+    """TC-7/TC-8/TC-15 (goal-market-compass iter-36, J-13): a run pair covering the FULL configured
+    sector/industry (`config.etfs.sector` + `config.etfs.industry`) and theme (`config.themes`) universe
+    on both runs, so the rotation block's accounting can close exactly against `configured_total`. Ranks
+    are REVERSED between the two runs (`prev = N + 1 - cur`, N = the configured count) -- for ODD N (31
+    sector/industry, 11 theme today) this deterministically yields exactly ONE exact-middle pair with
+    delta 0 (below rank_move_min -- suppressed, fails the threshold OUTRIGHT) and `(N-1)/2`
+    above-threshold movers on EACH side (every non-middle delta has |delta| >= 2, matching the real
+    `rank_move_min`). With `rotation_top_k` (5) smaller than 15 (sector's per-side count), this isolates
+    the TC-8/TC-15 condition: a row that CLEARS rank_move_min but is excluded SOLELY by rotation_top_k --
+    counted in `residual_count`, distinct from the middle row that fails rank_move_min outright."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 5, 29))
+        run_b = _mk_run(session, date(2024, 6, 5))
+        sector_tickers = list(cfg.etfs.sector.keys()) + list(cfg.etfs.industry.keys())
+        n_sector = len(sector_tickers)
+        for index, ticker in enumerate(sector_tickers):
+            cur_rank = index + 1
+            prev_rank = n_sector + 1 - cur_rank
+            kind = "sector" if ticker in cfg.etfs.sector else "industry"
+            _mk_sector_row(session, run_a.id, ticker, prev_rank, kind=kind)
+            _mk_sector_row(session, run_b.id, ticker, cur_rank, kind=kind)
+        theme_slugs = list(cfg.themes.keys())
+        n_theme = len(theme_slugs)
+        for index, slug in enumerate(theme_slugs):
+            cur_rank = index + 1
+            prev_rank = n_theme + 1 - cur_rank
+            _mk_theme_row(session, run_a.id, slug, prev_rank)
+            _mk_theme_row(session, run_b.id, slug, cur_rank)
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        return run_a.id, run_b.id, n_sector, n_theme
+
+
+def test_rotation_block_present_with_sector_theme_keys_and_no_stock_rows(engine, cfg, rotation_run_pair):
+    """TC-1: `session_delta.rotation` carries `sector`/`theme` keys and zero stock-kind rows anywhere --
+    rotation rows carry no `kind` field at all (a purely structural guarantee, not just an empty filter)."""
+    run_a_id, run_b_id = rotation_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    rotation = payload["session_delta"]["rotation"]
+    assert set(rotation.keys()) == {"sector", "theme"}
+    for kind_block in rotation.values():
+        for row in kind_block["gaining"] + kind_block["losing"]:
+            assert "kind" not in row
+            assert set(row.keys()) == {"label", "from", "to", "delta", "direction_word", "drill_href"}
+
+
+def test_rotation_two_sides_ordered_most_moved_first_and_capped(engine, cfg, full_universe_rotation_runs):
+    """TC-2: two explicitly labelled sides, each ordered most-moved-first (|delta| descending), each
+    length <= `rotation_top_k`."""
+    run_a_id, run_b_id, _n_sector, _n_theme = full_universe_rotation_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    sector = payload["session_delta"]["rotation"]["sector"]
+    assert len(sector["gaining"]) <= cfg.compass.delta.rotation_top_k
+    assert len(sector["losing"]) <= cfg.compass.delta.rotation_top_k
+    for side in (sector["gaining"], sector["losing"]):
+        magnitudes = [abs(row["delta"]) for row in side]
+        assert magnitudes == sorted(magnitudes, reverse=True)
+
+
+def test_rotation_pair_below_rank_move_min_excluded_from_both_sides(engine, cfg, rotation_run_pair):
+    """TC-3: XLF (delta 0, |0| < rank_move_min=2) appears in neither `gaining` nor `losing`."""
+    run_a_id, run_b_id = rotation_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    sector = payload["session_delta"]["rotation"]["sector"]
+    labels = {row["label"] for row in sector["gaining"] + sector["losing"]}
+    assert "XLF" not in labels
+    assert sector["suppressed_count"] == 1
+
+
+def test_rotation_empty_losing_side_when_every_mover_is_a_gainer(engine, cfg, all_gainers_sector_run_pair):
+    """TC-4 / J-13 step 8 (dev handoff citation: this fixture + test): every threshold-crossing sector
+    mover is a gainer -- the losing side is an explicit empty array, the gaining side is unaffected."""
+    run_a_id, run_b_id = all_gainers_sector_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    sector = payload["session_delta"]["rotation"]["sector"]
+    assert sector["losing"] == []
+    assert {row["label"] for row in sector["gaining"]} == {"XLK", "XLE"}
+    assert sector["suppressed_count"] == 1  # XLF (delta 0) — suppressed, distinct from "empty losing"
+
+
+def test_rotation_direction_word_falling_rank_number_is_improving(engine, cfg, rotation_run_pair):
+    """TC-5: a FALLING rank number (`cur_rank < prev_rank`) always produces the "improving" word; a
+    RISING one always produces "deteriorating" — spot-checked against the stored ranks directly (the
+    same values `GET /api/sectors`/`GET /api/themes` would serve at each as-of)."""
+    run_a_id, run_b_id = rotation_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+        stored_xle = list(session.exec(select(SectorScoreRow).where(SectorScoreRow.ticker == "XLE")))
+    sector = payload["session_delta"]["rotation"]["sector"]
+    gaining_by_label = {row["label"]: row for row in sector["gaining"]}
+    losing_by_label = {row["label"]: row for row in sector["losing"]}
+    xle = gaining_by_label["XLE"]  # 5 -> 1, falling
+    assert xle["from"] == 5 and xle["to"] == 1
+    assert xle["direction_word"] == cfg.compass.vocabulary.direction_words["up"] == "improving"
+    xlk = losing_by_label["XLK"]  # 1 -> 5, rising
+    assert xlk["from"] == 1 and xlk["to"] == 5
+    assert xlk["direction_word"] == cfg.compass.vocabulary.direction_words["down"] == "deteriorating"
+    stored_ranks = {row.run_id: row.rank for row in stored_xle}
+    assert stored_ranks[run_a_id] == xle["from"] and stored_ranks[run_b_id] == xle["to"]
+    # one theme row, same check
+    theme = payload["session_delta"]["rotation"]["theme"]
+    ev = {row["label"]: row for row in theme["gaining"]}["ev"]  # 4 -> 1, falling
+    assert ev["direction_word"] == "improving"
+
+
+def test_rotation_changes_entries_carry_same_delta_and_direction_word_as_rotation_rows(engine, cfg, rotation_run_pair):
+    """TC-6: `session_delta.changes` sector/theme-kind entries carry the SAME signed `delta` AND the SAME
+    `direction_word` as their corresponding rotation row (single computation, two placements)."""
+    run_a_id, run_b_id = rotation_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    session_delta = payload["session_delta"]
+    sector_rotation = session_delta["rotation"]["sector"]
+    rotation_by_label = {row["label"]: row for row in sector_rotation["gaining"] + sector_rotation["losing"]}
+    sector_changes = {c["label"]: c for c in session_delta["changes"] if c["kind"] == "sector"}
+    for label, rotation_row in rotation_by_label.items():
+        change_entry = sector_changes[label]
+        assert change_entry["delta"] == rotation_row["delta"]
+        assert change_entry["direction_word"] == rotation_row["direction_word"]
+
+
+def test_rotation_no_prior_run_explicit_no_comparison_state(engine, cfg, rotation_run_pair):
+    """TC-9: `previous_run is None` renders each kind's explicit no-prior-run state — empty sides, zero
+    counts, no direction words — consistent with `session_delta`'s own top-level no-prior-run branch."""
+    run_a_id, _run_b_id = rotation_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        payload = compass.build_manifest_payload(session, run_a, None, cfg)
+    assert payload["session_delta"]["prior_as_of"] is None
+    rotation = payload["session_delta"]["rotation"]
+    for kind_block in rotation.values():
+        assert kind_block["gaining"] == [] and kind_block["losing"] == []
+        assert kind_block["shown_count"] == 0
+        assert kind_block["suppressed_count"] == 0
+        assert kind_block["residual_count"] == 0
+    assert rotation["sector"]["configured_total"] == len(cfg.etfs.sector) + len(cfg.etfs.industry)
+    assert rotation["theme"]["configured_total"] == len(cfg.themes)
+
+
+def test_rotation_full_universe_closure_and_residual_isolation(engine, cfg, full_universe_rotation_runs):
+    """TC-7 (accounting closure against the configured group counts) + TC-8/TC-15 (dev handoff citation:
+    this fixture + test — an above-threshold mover excluded SOLELY by `rotation_top_k`, isolated from the
+    separate `rank_move_min` condition, per iter-35's lesson). See `full_universe_rotation_runs`'s
+    docstring for the exact math this test's concrete numbers depend on."""
+    run_a_id, run_b_id, n_sector, n_theme = full_universe_rotation_runs
+    assert cfg.compass.delta.rank_move_min == 2  # this test's concrete numbers depend on the real config
+    assert cfg.compass.delta.rotation_top_k == 5
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    rotation = payload["session_delta"]["rotation"]
+
+    sector = rotation["sector"]
+    assert sector["configured_total"] == n_sector == 31
+    assert len(sector["gaining"]) == 5 and len(sector["losing"]) == 5
+    assert sector["shown_count"] == 10
+    assert sector["suppressed_count"] == 1  # the exact-middle pair, delta 0
+    assert sector["residual_count"] == 20  # 10 gainers + 10 losers cleared the threshold but beyond the cap
+    assert sector["shown_count"] + sector["suppressed_count"] + sector["residual_count"] == n_sector
+
+    theme = rotation["theme"]
+    assert theme["configured_total"] == n_theme == 11
+    assert len(theme["gaining"]) == 5 and len(theme["losing"]) == 5
+    assert theme["shown_count"] == 10
+    assert theme["suppressed_count"] == 1
+    assert theme["residual_count"] == 0  # exactly at the cap on both sides here — nothing left over
+    assert theme["shown_count"] + theme["suppressed_count"] + theme["residual_count"] == n_theme
+
+
+def test_rotation_top_k_is_config_driven(cfg):
+    """`rotation_top_k` lives ONLY in `compass.delta.*` (anti-goal: No magic numbers) — a direct typed-
+    config read, never a literal in the engine module (test_no_magic_numbers.py's static scan enforces
+    the code side; this proves the config wiring)."""
+    assert cfg.compass.delta.rotation_top_k > 0
+
+
+def test_rotation_no_composite_score_field_anywhere(engine, cfg, rotation_run_pair):
+    """AG-11: a rotation row carries only the stored ranks, their signed difference, and the served word
+    — no new blended/composite field."""
+    run_a_id, run_b_id = rotation_run_pair
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        payload = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    allowed = {"label", "from", "to", "delta", "direction_word", "drill_href"}
+    for kind_block in payload["session_delta"]["rotation"].values():
+        for row in kind_block["gaining"] + kind_block["losing"]:
+            assert set(row.keys()) == allowed
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index f3676a9e..8bac3ac8 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -18,7 +18,7 @@ from app.config import REPO_ROOT, load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine import compass
 from app.engine import market_phase as market_phase_module
-from app.models import DailyPrice, MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun
+from app.models import DailyPrice, MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow
 
 BOUNDED_TIMEOUT_S = 30
 
@@ -1079,3 +1079,78 @@ def test_tc34_atr_caution_states_the_fact_only(engine, cfg):
     caution = next(c for c in result["candidates"][0]["cautions"] if c.startswith("ATR_RISK_BUDGET"))
     assert "sized risk accordingly" not in caution
     assert "ATR is 3.00% of price" in caution
+
+
+# --- TC-12/TC-25 (goal-market-compass iter-36, J-13): rotation + schema conformance ---------------
+
+
+@pytest.fixture()
+def frontier_run_with_rotation(engine, cfg):
+    """Frontier-shaped run pair (a `DailyPrice` bar at the LATER as_of — the `frontier_run` convention)
+    carrying real sector/theme rank rows on BOTH runs, so `session_delta.rotation` renders actual
+    gaining/losing content (not the no-prior-run state) for a schema-validation-with-rotation-populated
+    proof."""
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 8, 1))
+        run_b = _mk_run(session, date(2024, 8, 8))
+        _mk_result(session, run_a.id, "AAA")
+        _mk_result(session, run_b.id, "AAA")
+        session.add(SectorScoreRow(
+            run_id=run_a.id, ticker="XLK", kind="sector", name="XLK", members_json="[]",
+            score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=5,
+        ))
+        session.add(SectorScoreRow(
+            run_id=run_b.id, ticker="XLK", kind="sector", name="XLK", members_json="[]",
+            score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=1,
+        ))
+        session.add(ThemeScoreRow(
+            run_id=run_a.id, slug="ai", name="ai", score=80.0, bucket="A", members_json="[]",
+            breadth_label="universe-relative", trend_label="Uptrend", components_json="{}", rank=4,
+        ))
+        session.add(ThemeScoreRow(
+            run_id=run_b.id, slug="ai", name="ai", score=80.0, bucket="A", members_json="[]",
+            breadth_label="universe-relative", trend_label="Uptrend", components_json="{}", rank=1,
+        ))
+        session.add(DailyPrice(symbol="SPY", date=date(2024, 8, 8), open=1, high=1, low=1, close=1, volume=1))
+        session.commit()
+        session.refresh(run_b)
+        return run_b.id
+
+
+def test_tc12_manifest_with_rotation_validates_against_schema_no_version_bump(
+    engine, cfg, frontier_run_with_rotation, schema,
+):
+    """TC-12: a manifest produced under this change (with real `session_delta.rotation` content) still
+    validates against the committed schema, with NO `schema_version` bump — `session_delta` is an open
+    object there, so the addition is purely additive."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run_with_rotation)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        document = compass.manifest_row_payload(row)
+    jsonschema.validate(document, schema)  # raises on failure
+    assert document["session_delta"]["rotation"]["sector"]["gaining"][0]["label"] == "XLK"
+    assert cfg.compass.manifest.schema_version == "v1"  # unchanged by this iteration
+
+
+def test_rotation_absent_key_on_legacy_pre_iter36_row_never_fabricated(engine, cfg, frontier_run_with_rotation, schema):
+    """AG-12 / TC-13 posture: a manifest row minted BEFORE this iteration (simulated by stripping the
+    `rotation` key out of the stored `session_delta_json` blob — exactly the shape every pre-iter-36 row
+    has, since `session_delta` is stored as ONE JSON blob and this iteration adds a key inside it rather
+    than a new column) serves `session_delta` honestly WITHOUT a `rotation` key at all — never fabricated,
+    never crashes the read path, and the resulting (older-shaped) document still validates against the
+    committed schema (session_delta stays an open object)."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run_with_rotation)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        stored = json.loads(row.session_delta_json)
+        assert "rotation" in stored  # sanity: this iteration's own write path DID add it
+        del stored["rotation"]
+        row.session_delta_json = json.dumps(stored)
+        session.add(row)
+        session.commit()
+
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 8, 8))).first()
+        document = compass.manifest_row_payload(row)
+    assert "rotation" not in document["session_delta"]
+    jsonschema.validate(document, schema)
diff --git a/apps/backend/tests/test_session_delta.py b/apps/backend/tests/test_session_delta.py
index 263b3a14..dc5cb023 100644
--- a/apps/backend/tests/test_session_delta.py
+++ b/apps/backend/tests/test_session_delta.py
@@ -13,7 +13,17 @@ import pytest
 from sqlmodel import Session, SQLModel, create_engine, select
 
 from app.config import load_config
-from app.engine.session_delta import KIND_BREADTH, KIND_MARKET, KIND_SECTOR, KIND_STOCK, KIND_THEME, compute_delta, find_previous_run
+from app.engine.session_delta import (
+    KIND_BREADTH,
+    KIND_MARKET,
+    KIND_SECTOR,
+    KIND_STOCK,
+    KIND_THEME,
+    compute_delta,
+    find_previous_run,
+    sector_rank_pairs,
+    theme_rank_pairs,
+)
 from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow
 
 
@@ -316,3 +326,96 @@ def test_no_forward_returns_or_lookahead_import(engine, cfg):
                 if alias.name in banned:
                     offenders.add(alias.name)
     assert not offenders, f"session_delta.py's code references banned lookahead identifiers: {offenders}"
+
+
+# --- iter-36 (J-13): signed delta + sector/theme rank-pair builders -----------------------------
+
+
+def test_sector_theme_change_entries_carry_signed_delta(engine, cfg, two_runs):
+    """`session_delta.changes` sector/theme-kind entries now carry a SIGNED `delta` (`cur_rank -
+    prev_rank`) alongside the existing unsigned `magnitude` -- other kinds (market/breadth/stock) are
+    untouched (no `delta` key at all)."""
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    sector_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_SECTOR)}
+    # Technology XLK: rank 1 -> 3 (rose, worse -> positive delta); Energy XLE: rank 3 -> 1 (fell, better -> negative)
+    assert sector_changes["Technology"]["delta"] == 2
+    assert sector_changes["Energy"]["delta"] == -2
+    theme_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_THEME)}
+    # Artificial Intelligence: rank 1 -> 3 (delta +2)
+    assert theme_changes["Artificial Intelligence"]["delta"] == 2
+    for kind in (KIND_MARKET, KIND_BREADTH, KIND_STOCK):
+        for entry in _by_kind(result["changes"], kind):
+            assert "delta" not in entry
+
+
+def test_sector_rank_pairs_returns_all_comparable_pairs_uncapped_and_unthresholded(engine, cfg, two_runs):
+    """`sector_rank_pairs` returns EVERY comparable pair (XLK, XLF, XLE — including the below-threshold
+    XLF), unlike `compute_delta`'s own `changes`/`suppressed` split, and each carries a signed `delta`."""
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        pairs = sector_rank_pairs(session, run_b, run_a, cfg)
+    by_label = {entry["label"]: entry for entry, _magnitude in pairs}
+    assert set(by_label) == {"Technology", "Financials", "Energy"}
+    assert by_label["Technology"]["delta"] == 2
+    assert by_label["Energy"]["delta"] == -2
+    assert by_label["Financials"]["delta"] == 0  # below rank_move_min=2, but STILL present (not dropped)
+    # most-moved-first ordering (by |delta|)
+    assert [entry["label"] for entry, _m in pairs] in (
+        ["Technology", "Energy", "Financials"], ["Energy", "Technology", "Financials"],
+    )
+
+
+def test_theme_rank_pairs_returns_all_comparable_pairs_uncapped_and_unthresholded(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        pairs = theme_rank_pairs(session, run_b, run_a, cfg)
+    by_label = {entry["label"]: entry for entry, _magnitude in pairs}
+    assert set(by_label) == {"Artificial Intelligence", "Electric Vehicles"}
+    assert by_label["Artificial Intelligence"]["delta"] == 2
+    assert by_label["Electric Vehicles"]["delta"] == -1  # below rank_move_min=2, still present
+
+
+def test_compute_delta_reuses_precomputed_pairs_no_second_query(engine, cfg, two_runs):
+    """Passing precomputed `sector_pairs`/`theme_pairs` into `compute_delta` reuses the SAME entry
+    objects for `session_delta.changes` (identity check) -- proof there is no second, independent
+    recomputation of the pairs."""
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        precomputed_sector_pairs = sector_rank_pairs(session, run_b, run_a, cfg)
+        precomputed_theme_pairs = theme_rank_pairs(session, run_b, run_a, cfg)
+        result = compute_delta(
+            session, run_b, run_a, cfg, sector_pairs=precomputed_sector_pairs, theme_pairs=precomputed_theme_pairs,
+        )
+    sector_entry_ids = {id(entry) for entry, _m in precomputed_sector_pairs if entry["magnitude"] >= cfg.compass.delta.rank_move_min}
+    theme_entry_ids = {id(entry) for entry, _m in precomputed_theme_pairs if entry["magnitude"] >= cfg.compass.delta.rank_move_min}
+    for entry in _by_kind(result["changes"], KIND_SECTOR):
+        assert id(entry) in sector_entry_ids
+    for entry in _by_kind(result["changes"], KIND_THEME):
+        assert id(entry) in theme_entry_ids
+
+
+def test_compute_delta_without_precomputed_pairs_matches_precomputed_call(engine, cfg, two_runs):
+    """Omitting `sector_pairs`/`theme_pairs` (every pre-iter-36 caller) yields the SAME `changes`/
+    `suppressed` values as passing them explicitly -- backward-compatible default."""
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        implicit = compute_delta(session, run_b, run_a, cfg)
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        sector_pairs = sector_rank_pairs(session, run_b, run_a, cfg)
+        theme_pairs = theme_rank_pairs(session, run_b, run_a, cfg)
+        explicit = compute_delta(session, run_b, run_a, cfg, sector_pairs=sector_pairs, theme_pairs=theme_pairs)
+    assert implicit == explicit
diff --git a/apps/frontend/components/compass-leadership-rotation-section.tsx b/apps/frontend/components/compass-leadership-rotation-section.tsx
index 48bd5ad2..97dc67d8 100644
--- a/apps/frontend/components/compass-leadership-rotation-section.tsx
+++ b/apps/frontend/components/compass-leadership-rotation-section.tsx
@@ -5,23 +5,96 @@ import Link from "next/link";
 
 import { Badge } from "@/components/ui/badge";
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
-import type { CompassResponse, SessionDeltaChange } from "@/lib/api";
+import type { CompassResponse, CompassRotationKind, CompassRotationRow } from "@/lib/api";
 
-const ROTATION_KINDS: readonly SessionDeltaChange["kind"][] = ["sector", "theme", "stock"];
+type RotationGroupKind = "sector" | "theme";
+type RotationSideKey = "gaining" | "losing";
 
-const KIND_LABEL: Record<SessionDeltaChange["kind"], string> = {
-  market: "Market",
-  breadth: "Breadth",
+const KIND_LABEL: Record<RotationGroupKind, string> = {
   sector: "Sector",
   theme: "Theme",
-  stock: "Stock",
 };
 
-/** J-07 (goal-market-compass iter-28): the Leadership rotation section — a presentational, kind-filtered
- *  slice of the ALREADY-served `session_delta.changes` array (`GET /api/compass`, the existing J-02
- *  Data-Contract row). No new computed value, no client-side threshold or word selection — this
- *  component only filters the served list to `kind ∈ {sector, theme, stock}` for display; the market-
- *  and breadth-kind entries stay in the What-changed card above, unfiltered. */
+const SIDE_LABEL: Record<RotationSideKey, string> = {
+  gaining: "Gaining",
+  losing: "Losing",
+};
+
+const EMPTY_SIDE_TEXT: Record<RotationGroupKind, Record<RotationSideKey, string>> = {
+  sector: {
+    gaining: "No sector gained ground beyond the threshold this session.",
+    losing: "No sector lost ground beyond the threshold this session.",
+  },
+  theme: {
+    gaining: "No theme gained ground beyond the threshold this session.",
+    losing: "No theme lost ground beyond the threshold this session.",
+  },
+};
+
+function RotationRow({ row }: { row: CompassRotationRow }) {
+  return (
+    <li className="flex items-start justify-between gap-3 text-sm">
+      <Link href={row.drill_href} className="text-text hover:underline">
+        {row.label}
+      </Link>
+      <span className="num shrink-0 text-xs text-text-muted">
+        {row.from} &rarr; {row.to} ({row.delta > 0 ? "+" : ""}
+        {row.delta}) &middot; {row.direction_word}
+      </span>
+    </li>
+  );
+}
+
+function RotationSide({ kind, side, rows }: { kind: RotationGroupKind; side: RotationSideKey; rows: CompassRotationRow[] }) {
+  return (
+    <div className="space-y-1.5" data-testid={`compass-leadership-rotation-${kind}-${side}`}>
+      <Badge variant="default">{SIDE_LABEL[side]}</Badge>
+      {rows.length === 0 ? (
+        <p className="text-xs text-text-muted" data-testid={`compass-leadership-rotation-${kind}-${side}-empty`}>
+          {EMPTY_SIDE_TEXT[kind][side]}
+        </p>
+      ) : (
+        <ul className="space-y-1.5" data-testid={`compass-leadership-rotation-${kind}-${side}-list`}>
+          {rows.map((row) => (
+            <RotationRow key={row.label} row={row} />
+          ))}
+        </ul>
+      )}
+    </div>
+  );
+}
+
+function RotationKindBlock({ kind, block }: { kind: RotationGroupKind; block: CompassRotationKind }) {
+  return (
+    <div className="space-y-2" data-testid={`compass-leadership-rotation-${kind}`}>
+      <h4 className="text-sm font-medium text-text">{KIND_LABEL[kind]} rotation</h4>
+      <div className="grid gap-3 md:grid-cols-2">
+        <RotationSide kind={kind} side="gaining" rows={block.gaining} />
+        <RotationSide kind={kind} side="losing" rows={block.losing} />
+      </div>
+      <p className="text-xs text-text-faint" data-testid={`compass-leadership-rotation-${kind}-accounting`}>
+        {block.shown_count} of {block.configured_total} shown &middot; {block.suppressed_count} below threshold
+        &middot; {block.residual_count} beyond the display cap.
+      </p>
+    </div>
+  );
+}
+
+/** J-13 (goal-market-compass iter-36): the Leadership rotation section — renders the SERVED
+ *  `session_delta.rotation.{sector,theme}` block directly (two labelled, signed, both-directions sides
+ *  per group kind, most-moved-first, each with its own honest empty state), replacing the prior
+ *  client-side `session_delta.changes.filter(kind ∈ {sector, theme, stock})` slice that duplicated the
+ *  What-changed card above it verbatim. This component selects no word, computes no sign, and applies no
+ *  threshold — every value (label, from/to, signed delta, direction_word, drill_href, and the
+ *  shown/suppressed/residual/configured_total accounting) is a served field, re-formatted only. No
+ *  stock-kind row exists anywhere in `session_delta.rotation` (group-level only; stock leadership-bucket
+ *  crossings stay in the What-changed card only).
+ *
+ *  Three distinct honest states, never a crash (AG-8): (1) `prior_as_of === null` — the earliest stored
+ *  session, nothing to compare against; (2) `rotation` absent — a stored manifest row minted before this
+ *  section existed, served verbatim and never backfilled (AG-12), so the block is reported as
+ *  not-recorded rather than recomputed; (3) a served block whose side arrays may individually be empty,
+ *  each rendering its own empty-state string. */
 export function CompassLeadershipRotationSection({ compass }: { compass: CompassResponse | null }) {
   if (compass === null) {
     return (
@@ -35,34 +108,35 @@ export function CompassLeadershipRotationSection({ compass }: { compass: Compass
     );
   }
 
-  const entries = compass.session_delta.changes.filter((change) => ROTATION_KINDS.includes(change.kind));
+  const { session_delta } = compass;
+  const noPriorRun = session_delta.prior_as_of === null;
+  // Third state, distinct from both no-prior-run and an empty side: a stored manifest row minted BEFORE
+  // iter-36 has a non-null `prior_as_of` but no `rotation` key at all (never backfilled — AG-12). Read
+  // it once here so the render below can never dereference an absent block (AG-8: degrade honestly, do
+  // not crash the page on as-of navigation).
+  const rotation = session_delta.rotation ?? null;
 
   return (
     <Card data-testid="compass-leadership-rotation-section">
       <CardHeader>
         <CardTitle>Leadership rotation</CardTitle>
       </CardHeader>
-      <CardContent>
-        {entries.length === 0 ? (
-          <p className="text-sm text-text-muted" data-testid="compass-leadership-rotation-empty">
-            No sector, theme, or stock rotation this session.
+      <CardContent className="space-y-4">
+        {noPriorRun ? (
+          <p className="text-sm text-text-muted" data-testid="compass-leadership-rotation-no-prior">
+            This is the earliest stored session — there is no prior session to compare rotation against.
+          </p>
+        ) : rotation === null ? (
+          <p className="text-sm text-text-muted" data-testid="compass-leadership-rotation-not-recorded">
+            Rotation detail was not recorded for this session — its stored manifest predates this section,
+            and a frozen manifest is never rewritten, so nothing is shown here rather than recomputed. The
+            What changed card above still lists this session&rsquo;s moves.
           </p>
         ) : (
-          <ul className="space-y-2" data-testid="compass-leadership-rotation-list">
-            {entries.map((change, index) => (
-              <li key={`${change.kind}-${index}`} className="flex items-start justify-between gap-3 text-sm">
-                <span className="flex flex-wrap items-center gap-2">
-                  <Badge variant="default">{KIND_LABEL[change.kind]}</Badge>
-                  <Link href={change.drill_href} className="text-text hover:underline">
-                    {change.label}
-                  </Link>
-                </span>
-                <span className="num shrink-0 text-xs text-text-muted">
-                  {String(change.from)} &rarr; {String(change.to)}
-                </span>
-              </li>
-            ))}
-          </ul>
+          <>
+            <RotationKindBlock kind="sector" block={rotation.sector} />
+            <RotationKindBlock kind="theme" block={rotation.theme} />
+          </>
         )}
       </CardContent>
     </Card>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 9be729f3..2e4da4b8 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -873,9 +873,15 @@ export async function fetchThemes(asof?: string, signal?: AbortSignal): Promise<
   return getJSON<ThemesResponse>(withAsOf("/api/themes", asof), signal);
 }
 
-// --- compass (goal-market-compass iter-2, J-02/J-03/J-04) -----------------------------------
+// --- compass (goal-market-compass iter-2, J-02/J-03/J-04; iter-36, J-13 rotation) ------------
 /** One session-over-session change entry (J-02) — already threshold-gated server-side; the
- *  frontend renders it verbatim and evaluates no threshold itself. */
+ *  frontend renders it verbatim and evaluates no threshold itself.
+ *
+ *  iter-36 (J-13) additive fields: `delta` (signed) + `direction_word` ride `kind === "sector"` and
+ *  `kind === "theme"` entries ONLY — undefined for `market`/`breadth`/`stock` kinds and for any entry
+ *  served from a manifest minted before this field existed (honest absence, never fabricated). These
+ *  are the SAME values the corresponding `session_delta.rotation` row carries (single computation, two
+ *  placements) — the frontend selects no word and computes no sign here either way. */
 export interface SessionDeltaChange {
   kind: "market" | "breadth" | "sector" | "theme" | "stock";
   label: string;
@@ -884,6 +890,55 @@ export interface SessionDeltaChange {
   magnitude: number;
   threshold: number;
   drill_href: string;
+  delta?: number;
+  direction_word?: string;
+}
+
+/** One `session_delta.rotation.<kind>.{gaining,losing}` row (goal-market-compass iter-36, J-13) — a
+ *  served, group-level (sector/theme only, never stock) rank-move row: the label, the stored from/to rank
+ *  positions, a SIGNED `delta` (`to - from`; a FALLING rank number is an IMPROVING position), the served
+ *  `direction_word` (one of `compass.vocabulary.direction_words`' three values, polarity already resolved
+ *  server-side), and the existing drill-through link. Re-formatted only — the frontend selects no word,
+ *  computes no sign, and applies no threshold. */
+export interface CompassRotationRow {
+  label: string;
+  from: number;
+  to: number;
+  delta: number;
+  direction_word: string;
+  drill_href: string;
+}
+
+/** One group kind's (`sector` | `theme`) rotation block (J-13): two explicitly labelled, both-directions
+ *  sides, each capped by the config-only `compass.delta.rotation_top_k` and ordered most-moved-first, plus
+ *  a complete accounting — `shown_count` (rows actually returned across both sides) + `suppressed_count`
+ *  (below-`rank_move_min` pairs) + `residual_count` (above-threshold pairs beyond the cap, disclosed —
+ *  NEVER silently dropped, the exact defect this iteration fixes) sums to `configured_total` (31 for
+ *  sector/industry, 11 for theme, read from the SAME config catalogs `GET /api/sectors`/`GET /api/themes`
+ *  serve). An empty `gaining`/`losing` array is the honest empty state for that side — the component
+ *  renders its own explicit empty-state text, never a blank. */
+export interface CompassRotationKind {
+  gaining: CompassRotationRow[];
+  losing: CompassRotationRow[];
+  shown_count: number;
+  suppressed_count: number;
+  residual_count: number;
+  configured_total: number;
+}
+
+/** The `session_delta.rotation` CONTENT block (J-13) — one block per group kind, no stock-kind row
+ *  anywhere (group-level only, Non-Goal). Computed ONCE by `app.engine.compass.build_manifest_payload`
+ *  (reusing `app.engine.session_delta.compute_delta`'s sector/theme rank pairs — no second computation)
+ *  and served only by the existing `GET /api/compass` — no new producer, no new route. `previous_run is
+ *  None` (the earliest stored session) renders each kind's explicit no-prior-run state: empty sides, zero
+ *  counts — never fabricated, consistent with `session_delta`'s own top-level `prior_as_of: null` state
+ *  (check that field, not this block's shape, to detect the no-comparison case). The block itself is
+ *  OPTIONAL on the wire: a stored manifest row minted before iter-36 carries no `rotation` key at all
+ *  ("pre-rotation era", never backfilled — AG-12), which is a THIRD state, distinct from both
+ *  no-prior-run and an empty side. */
+export interface CompassRotation {
+  sector: CompassRotationKind;
+  theme: CompassRotationKind;
 }
 
 /** One BELOW-threshold entry, shown only inside the "suppressed moves" disclosure. */
@@ -901,6 +956,12 @@ export interface SessionDelta {
   changes: SessionDeltaChange[];
   suppressed: SessionDeltaSuppressed[];
   suppressed_count: number;
+  // iter-36 (J-13) — additive and OPTIONAL: every `next_session_manifests` row minted before iter-36
+  // stores a `session_delta` blob with NO `rotation` key at all (the key is added inside the existing
+  // blob, never backfilled — AG-12), and those rows are served verbatim by `manifest_row_payload`. So a
+  // historical as-of can legitimately have a non-null `prior_as_of` and NO `rotation` — consumers must
+  // branch on its absence and show an honest placeholder (AG-8), never dereference it unguarded.
+  rotation?: CompassRotation;
 }
 
 /** One cited fact backing a narrative sentence (J-03) — spot-checkable against the canonical
diff --git a/config.yaml b/config.yaml
index 7e0f3fe2..e6f60bb1 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1421,6 +1421,7 @@ compass:
     rank_move_min: 2                 # sector/theme rank positions moved to report a change
     stock_score_min_change: 8.0      # leadership-score points a bucket-crossing stock must move to report a "stock" change
     top_k: 5                         # max sector-kind and max theme-kind change entries shown (most-moved first; mirrors the existing Top-Sectors/Top-Themes "top 5" convention)
+    rotation_top_k: 5                # goal-market-compass iter-36 (J-13): max GAINING and max LOSING rows shown per side of session_delta.rotation.{sector,theme} -- independent of top_k above (session_delta.changes stays unchanged); above-threshold movers beyond this cap are counted in that side's residual_count, never dropped uncounted
     max_stock_items: 10              # max stock-kind change entries evaluated/shown (bounds both compute and display — AG-8)
     velocity_flat_band: 2.0          # |regime-score delta| below this reads as "little changed" in the narrative's direction sentence
     stress_velocity_flat_band: 5.0   # goal-market-compass iter-28 (J-07): |severity delta| below this reads as "little changed" for state_band.stress (a dedicated key -- severity is a different 0-100 scale than the regime score, not a reuse of velocity_flat_band above). state_band.breadth reuses breadth_min_change_pts below unchanged.
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/telemetry.jsonl   | 16 ++++++++++++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  3 +++
 3 files changed, 20 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
