# Iteration diff (bounded)

Files changed: 27. Shown in full: 25.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/compass.py` (99 lines not shown)
- `apps/backend/tests/test_compass.py` (9 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 03189bf6..8f3d43a4 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1808,6 +1808,17 @@ class UniverseSelectionCfg(BaseModel):
     thresholds: list[MethodologyThreshold] = Field(min_length=1)
 
 
+class CompassSelectionBasisCfg(BaseModel):
+    """goal-market-compass iter-2 (J-04) — the /methodology "Next-session focus" disclosure: plain-
+    language selection-rule prose + the live `compass.selection.*` thresholds it names, resolved via the
+    SAME `ref` mechanism `UniverseSelectionCfg.thresholds` uses (never re-typed — the matching-config
+    keystone)."""
+
+    model_config = ConfigDict(extra="allow")
+    text: str
+    thresholds: list[MethodologyThreshold] = Field(min_length=1)
+
+
 class GlossaryCategory(BaseModel):
     """One ordered glossary category (iter-4 goal-mode, J-47) — a group of terms shown together on
     /methodology and the lookup namespace tooltips read. `key` is the stable identifier a term's
@@ -1866,6 +1877,10 @@ class MethodologyCfg(BaseModel):
     model_config = ConfigDict(extra="allow")
     intro: Optional[str] = None
     universe_selection: Optional[UniverseSelectionCfg] = None
+    # goal-market-compass iter-2 (J-04) — the Next-session focus disclosure, a SIBLING of
+    # `universe_selection` (not nested inside it) for the same reason `sector_basis` is a sibling: it
+    # makes no universe-screen claim, so the J-22 honest-universe gate must not hide it.
+    compass_selection: Optional[CompassSelectionBasisCfg] = None
     entries: list[MethodologyEntry] = Field(min_length=1)
     categories: list[GlossaryCategory] = Field(default_factory=list)
     terms: list[GlossaryTerm] = Field(default_factory=list)
@@ -2535,6 +2550,190 @@ def _default_watchlist() -> "WatchlistCfg":
     return WatchlistCfg()
 
 
+class CompassDeltaCfg(BaseModel):
+    """goal-market-compass iter-2 (J-02) — `app.engine.session_delta.compute_delta`'s session-over-
+    session change thresholds. EVERY number the producer reads lives here (anti-goal: No magic numbers;
+    `session_delta.py` joins `CALC_FILES` in `test_no_magic_numbers.py`). `top_k` bounds the sector-kind
+    and theme-kind change lists (mirrors the existing "top 5" Top-Sectors/Top-Themes convention);
+    `max_stock_items` additionally bounds how many stock-kind bucket-crossing candidates are evaluated
+    at all (AG-8 — the delta producer never sweeps the full universe's `record_json`)."""
+
+    model_config = ConfigDict(extra="allow")
+    rule_version: str
+    market_score_min_change: float
+    breadth_min_change_pts: float
+    rank_move_min: int
+    stock_score_min_change: float
+    top_k: int
+    max_stock_items: int
+    velocity_flat_band: float
+    pbear_bands: list[LabelEdge] = Field(min_length=1)
+
+    @model_validator(mode="after")
+    def _validate(self) -> "CompassDeltaCfg":
+        for name, value in (
+            ("market_score_min_change", self.market_score_min_change),
+            ("breadth_min_change_pts", self.breadth_min_change_pts),
+            ("stock_score_min_change", self.stock_score_min_change),
+            ("velocity_flat_band", self.velocity_flat_band),
+        ):
+            if value < 0:
+                raise ValueError(f"compass.delta.{name} must be >= 0, got {value}")
+        if self.rank_move_min <= 0:
+            raise ValueError("compass.delta.rank_move_min must be positive")
+        if self.top_k <= 0:
+            raise ValueError("compass.delta.top_k must be positive")
+        if self.max_stock_items <= 0:
+            raise ValueError("compass.delta.max_stock_items must be positive")
+        return self
+
+
+class CompassSelectionShadowCfg(BaseModel):
+    """The J-05/J-06 near-threshold shadow-cohort floor. The key is RESERVED from iter-2 onward but read
+    by no code this iteration — the shadow cohort itself is neither computed nor stored/rendered until
+    J-05/J-06 (OUT OF SCOPE, docs/phases/goal-market-compass-iter-2.md)."""
+
+    model_config = ConfigDict(extra="allow")
+    min_score: float
+
+
+class CompassSelectionCfg(BaseModel):
+    """goal-market-compass iter-2 (J-04) — `app.engine.compass.evaluate_selection`'s transparent
+    candidate-selection rule. `leadership_min_score` is the ONLY leadership gate the rule may use — never
+    the Actionable / A-bucket setup status (today's seed data yields zero A-bucket / Actionable names
+    while still clearing a raw leadership-score floor; see the iter-2 spec BACKGROUND). No field here
+    ever feeds a new blended/composite number (anti-goal AG-11) — each is used standalone against one of
+    the three existing per-stock scores."""
+
+    model_config = ConfigDict(extra="allow")
+    rule_version: str
+    leadership_min_score: float
+    entry_min_score: float
+    risk_max_score: float
+    max_candidates: int
+    why_not_floor: float
+    why_not_cap: int
+    shadow: CompassSelectionShadowCfg
+
+    @model_validator(mode="after")
+    def _validate(self) -> "CompassSelectionCfg":
+        for name, value in (
+            ("leadership_min_score", self.leadership_min_score),
+            ("entry_min_score", self.entry_min_score),
+            ("risk_max_score", self.risk_max_score),
+            ("why_not_floor", self.why_not_floor),
+        ):
+            if not (0 <= value <= 100):
+                raise ValueError(f"compass.selection.{name} must be in [0, 100], got {value}")
+        if self.max_candidates <= 0:
+            raise ValueError("compass.selection.max_candidates must be positive")
+        if self.why_not_cap <= 0:
+            raise ValueError("compass.selection.why_not_cap must be positive")
+        if self.why_not_floor > self.leadership_min_score:
+            raise ValueError(
+                "compass.selection.why_not_floor must be <= leadership_min_score "
+                f"({self.why_not_floor} > {self.leadership_min_score})"
+            )
+        return self
+
+
+_COMPASS_BUCKETS = {"A", "B", "C", "D", "E"}
+
+
+class CompassVocabularyCfg(BaseModel):
+    """goal-market-compass iter-2 (J-03/J-04) — word maps ONLY (never a new score, anti-goal AG-11).
+    `leadership_words` / `entry_words` / `risk_words` must each cover every A-E bucket (completeness,
+    like `SECTOR_WEIGHT_KEYS` elsewhere in this file); `banned_terms` backs the TC-11 narrative
+    banned-language scan (imperative trade verbs, forecast terms, causal-attribution phrases — AG-2)."""
+
+    model_config = ConfigDict(extra="allow")
+    direction_words: dict[str, str]
+    leadership_words: dict[str, str]
+    entry_words: dict[str, str]
+    risk_words: dict[str, str]
+    banned_terms: list[str] = Field(min_length=1)
+
+    @model_validator(mode="after")
+    def _validate(self) -> "CompassVocabularyCfg":
+        missing_dir = {"up", "down", "flat"} - set(self.direction_words)
+        if missing_dir:
+            raise ValueError(f"compass.vocabulary.direction_words missing: {sorted(missing_dir)}")
+        for field_name, mapping in (
+            ("leadership_words", self.leadership_words),
+            ("entry_words", self.entry_words),
+            ("risk_words", self.risk_words),
+        ):
+            missing = _COMPASS_BUCKETS - set(mapping)
+            if missing:
+                raise ValueError(f"compass.vocabulary.{field_name} missing buckets: {sorted(missing)}")
+        return self
+
+
+class CompassCfg(BaseModel):
+    """goal-market-compass iter-2 (J-02/J-03/J-04) — the Today-page decision-surface config consumed by
+    `app.engine.session_delta` and `app.engine.compass`. Default-populated so a config / inline test
+    fixture predating this block still loads unchanged; the real `config.yaml` restates it explicitly as
+    the single documented source (see `_default_compass`)."""
+
+    model_config = ConfigDict(extra="allow")
+    delta: CompassDeltaCfg
+    selection: CompassSelectionCfg
+    vocabulary: CompassVocabularyCfg
+
+
+def _default_compass() -> "CompassCfg":
+    """The built-in default compass config — used when a config predating this block (or an inline test
+    fixture) omits `compass`. The real `config.yaml` restates it explicitly as the single documented
+    source; kept byte-for-byte in sync with it by `test_config_engine.py`."""
+    return CompassCfg(
+        delta=CompassDeltaCfg(
+            rule_version="v1",
+            market_score_min_change=5.0,
+            breadth_min_change_pts=5.0,
+            rank_move_min=2,
+            stock_score_min_change=8.0,
+            top_k=5,
+            max_stock_items=10,
+            velocity_flat_band=2.0,
+            pbear_bands=[
+                LabelEdge(min=0.0, label="calm"),
+                LabelEdge(min=0.20, label="cautious"),
+                LabelEdge(min=0.40, label="tense"),
+                LabelEdge(min=0.60, label="stressed"),
+            ],
+        ),
+        selection=CompassSelectionCfg(
+            rule_version="v1",
+            leadership_min_score=80.0,
+            entry_min_score=70.0,
+            risk_max_score=60.0,
+            max_candidates=10,
+            why_not_floor=75.0,
+            why_not_cap=20,
+            shadow=CompassSelectionShadowCfg(min_score=75.0),
+        ),
+        vocabulary=CompassVocabularyCfg(
+            direction_words={"up": "improving", "down": "deteriorating", "flat": "little changed"},
+            leadership_words={
+                "A": "Elite leader", "B": "Strong leader", "C": "Average leader",
+                "D": "Weak leader", "E": "Laggard",
+            },
+            entry_words={
+                "A": "Ideal entry", "B": "Good entry", "C": "Fair entry",
+                "D": "Poor entry", "E": "Weak entry",
+            },
+            risk_words={
+                "A": "Very high risk", "B": "High risk", "C": "Moderate risk",
+                "D": "Low risk", "E": "Very low risk",
+            },
+            banned_terms=[
+                "buy", "sell", "should buy", "should sell", "will rise", "will fall",
+                "target price", "guaranteed", "recommend", "act now", "because of", "caused by",
+            ],
+        ),
+    )
+
+
 class Config(BaseModel):
     """Validated view of config.yaml. Only the iter-1-consumed sections are typed/validated;
     scaffolded sections ride along via extra="allow" so they can be tuned without code edits."""
@@ -2599,6 +2798,11 @@ class Config(BaseModel):
     # config / inline test fixture predating this block still loads unchanged; the real `config.yaml`
     # restates it explicitly as the single documented source.
     watchlist: WatchlistCfg = Field(default_factory=_default_watchlist)
+    # goal-market-compass iter-2 (J-02/J-03/J-04) — the Today-page decision-surface config: delta
+    # thresholds, the candidate-selection rule, and word maps. Default-populated so a config / inline
+    # test fixture predating this block still loads unchanged; the real `config.yaml` restates it
+    # explicitly as the single documented source.
+    compass: CompassCfg = Field(default_factory=_default_compass)
 
     @field_validator("themes")
     @classmethod
@@ -2773,6 +2977,10 @@ class Config(BaseModel):
         threshold_lists = [entry.thresholds for entry in self.methodology.entries]
         if self.methodology.universe_selection is not None:
             threshold_lists.append(self.methodology.universe_selection.thresholds)
+        # goal-market-compass iter-2 (J-04): the Next-session focus disclosure's thresholds resolve the
+        # SAME way as Universe Selection's above.
+        if self.methodology.compass_selection is not None:
+            threshold_lists.append(self.methodology.compass_selection.thresholds)
         # J-47: glossary terms may cite config thresholds via the same `ref` mechanism — resolve them too.
         threshold_lists.extend(term.thresholds for term in self.methodology.terms)
         for thresholds in threshold_lists:
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 590611f1..a8efe27d 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -58,6 +58,7 @@ from app.engine import drift as drift_module
 from app.engine import evidence  # ops-hardening iter-7 (J-06): the finalize hook warms drawdown_expectations
 from app.engine import forward_testing, scanner
 from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
+from app.engine import compass  # goal-market-compass iter-2 (J-02/J-03/J-04): the finalize hook warms this
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
 from app.engine.prices import (
     _BarCache,
@@ -2470,9 +2471,9 @@ class JobProgress:
     # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
-    # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    # "drawdown_expectations", "index_series", "factor_lab_all", "availability_heatmap"]` it actually
-    # refreshed — empty/default until the hook has actually run (never fabricated on an
+    # "coverage", "membership_timeline", "market_phase", "next_session_manifest", "forward_aggregates",
+    # "research_hot_keys", "drawdown_expectations", "index_series", "factor_lab_all",
+    # "availability_heatmap"]` it actually refreshed — empty/default until the hook has actually run (never fabricated on an
     # interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc. already are).
     new_snapshot_dates: list[date_cls] = field(default_factory=list)
     aggregates_refreshed: list[str] = field(default_factory=list)
@@ -4198,10 +4199,10 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
-    "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
-    "drawdown_expectations", "index_series", "factor_lab_all", "availability_heatmap"]` ACTUALLY
-    refreshed — never a fabricated category (mirrors the `omitted`/`passers` honesty convention already
-    used elsewhere in this module).
+    "coverage", "membership_timeline", "market_phase", "next_session_manifest", "forward_aggregates",
+    "research_hot_keys", "drawdown_expectations", "index_series", "factor_lab_all",
+    "availability_heatmap"]` ACTUALLY refreshed — never a fabricated category (mirrors the
+    `omitted`/`passers` honesty convention already used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -4511,6 +4512,41 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 prog.job_id, "market_phase_warm", time.monotonic() - _phase_t0,
             )
 
+            # goal-market-compass iter-2 (J-02/J-03/J-04): compute + store the next-session manifest
+            # CONTENT block for each newly produced frontier date, if none exists yet. Placed AFTER the
+            # market-phase warm above (the narrative's state/direction sentences read
+            # `market_phase.market_phase_cached` — already warm by this point in the SAME pass, so this
+            # phase never pays a redundant compute) and BEFORE the forward-aggregates phase below (this is
+            # a bounded, per-date compute over already-stored scores, not a long aggregate warm). Own
+            # try/except (isolate-and-continue, mirroring the market-phase loop above) so a producer
+            # failure here never blocks or crashes the rest of the finalize tail (TC-31).
+            prog.enter_finalize_phase("compass content")
+            _phase_t0 = time.monotonic()
+            compass_warmed = False
+            for d in prog.new_snapshot_dates:
+                prog.tick()
+                time.sleep(0)
+                try:
+                    run_for_date = scanner.get_run_for_date(session, d)
+                    if run_for_date is not None:
+                        compass.get_or_create_manifest(session, run_for_date, cfg)
+                        compass_warmed = True
+                except MemoryError as exc:
+                    _log_isolation_failure(
+                        "ingest compass-content warm aborted at %s — memory pressure, stopping remaining "
+                        "dates in this loop: %s", d, exc,
+                    )
+                    _release_process_memory()
+                    break
+                except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
+                    _log_isolation_failure("ingest compass-content warm failed for %s (non-fatal): %s", d, exc)
+            if compass_warmed:
+                refreshed.append("next_session_manifest")
+            logger.info(
+                "J-05 finalize-tail phase timing: job=%s phase=%s elapsed=%.2fs",
+                prog.job_id, "compass_content_warm", time.monotonic() - _phase_t0,
+            )
+
             # ops-hardening iter-5 (J-06): warm the CURRENT latest stored run's per-horizon forward-aggregate
             # cache (GET /api/backtest's `evidence_by_horizon`, ~34.77s pre-fix over all 5 configured horizons
             # — reports/perf-budgets.md). Unconditional (not gated on `prog.new_snapshot_dates`, unlike the
diff --git a/apps/backend/app/engine/methodology.py b/apps/backend/app/engine/methodology.py
index d5754354..63b1a5ff 100644
--- a/apps/backend/app/engine/methodology.py
+++ b/apps/backend/app/engine/methodology.py
@@ -71,6 +71,10 @@ def build_catalog(config: Config) -> dict:
         # offline screen record exists, and the sector basis must stay readable regardless (see
         # `_sector_basis`). Same producer, same endpoint, one home — never recomputed elsewhere.
         payload["sector_basis"] = _sector_basis(config)
+    if catalog.compass_selection is not None:
+        # J-04 (goal-market-compass iter-2): same sibling-key reasoning as `sector_basis` above — this
+        # disclosure makes no universe-screen claim, so the J-22 gate must not hide it either.
+        payload["compass_selection"] = _compass_selection(config)
     if catalog.categories:
         payload["glossary"] = _glossary(config)
     return payload
@@ -91,6 +95,18 @@ def _sector_basis(config: Config) -> str:
     return config.methodology.universe_selection.sector_basis
 
 
+def _compass_selection(config: Config) -> dict:
+    """The J-04 (goal-market-compass iter-2) "Next-session focus" disclosure: the selection-rule prose
+    + its live `compass.selection.*` thresholds, resolved via the SAME `ref` mechanism as
+    `_universe_selection` (matching-config keystone — never re-typed). Served as its own top-level
+    sibling key for the same reason `_sector_basis` is a sibling (see its docstring)."""
+    basis = config.methodology.compass_selection
+    return {
+        "text": basis.text,
+        "thresholds": [_threshold_row(threshold, config) for threshold in basis.thresholds],
+    }
+
+
 # The category key the Setups & Patterns glossary rows are DERIVED into (J-47). The category itself is
 # declared in `config.methodology.categories` with this key; build_catalog fills its `terms` from the
 # existing `methodology.entries` so a setup/pattern is explained in exactly one place (never re-described).
diff --git a/apps/backend/app/engine/universe_screen.py b/apps/backend/app/engine/universe_screen.py
index 685950af..9ee13cee 100644
--- a/apps/backend/app/engine/universe_screen.py
+++ b/apps/backend/app/engine/universe_screen.py
@@ -137,9 +137,14 @@ def pool_sector_map(
         pool = read_pool(seed_dir)
     except FileNotFoundError:
         return {}
+    # B2 (goal-market-compass iter-1 audit, fixed iter-2): materialize the valid-sector set ONCE here
+    # (not once per row inside `resolve_pool_sector`) — both a per-row `set(...)` rebuild cost across the
+    # full pool, and the latent trap that a one-shot iterable (e.g. a generator) passed as `valid_sectors`
+    # would otherwise be exhausted by the FIRST row, silently resolving every later row to `None`.
+    valid = set(valid_sectors)
     out: dict[str, str] = {}
     for row in pool:
-        resolved = resolve_pool_sector(row.get("sector"), aliases=aliases, valid_sectors=valid_sectors)
+        resolved = resolve_pool_sector(row.get("sector"), aliases=aliases, valid_sectors=valid)
         if resolved is not None:
             out[row["symbol"]] = resolved
     return out
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 050f1e7b..2f9f3274 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -760,6 +760,39 @@ class AvailabilityCache(SQLModel, table=True):
     created_at: datetime
 
 
+class NextSessionManifest(SQLModel, table=True):
+    """One next-session manifest row for one `as_of` date (goal-market-compass iter-2, J-02/J-03/J-04 —
+    the CONTENT block only; J-05/J-06 add `mode`/`version`/`frozen`/`generation.*`/hashes/provenance/
+    cohort-storage/export columns ADDITIVELY in a later iteration — this iteration's five columns below
+    never change shape, per `docs/phases/goal-market-compass-iter-2.md` OUT OF SCOPE).
+
+    UNLIKE the `*Cache` tables above (`MarketPhaseCache` et al.), this is NOT a cache of a re-derivable
+    read — it is a first-class IMMUTABLE record, like `ScannerRun`: computed ONCE per `as_of` (at ingest
+    finalize, or on the first `GET /api/compass` for a not-yet-computed `as_of` — create-once-on-GET) and
+    NEVER updated or deleted afterward (anti-goal AG-12 — manifest immutability binds from this iteration
+    on, even though the `frozen`/`version` columns that make that explicit are still J-05/J-06). `as_of`
+    is unique — exactly one row per date, mirroring `ScannerRun.asof_date`. A concurrent create-once race
+    is resolved the SAME way `scanner.persist_run_payload` resolves a `ScannerRun` race: roll back the
+    losing INSERT and return the already-committed row (never raise, never duplicate, never overwrite).
+
+    The three CONTENT blocks (`session_delta`, `narrative`, `selection` — see `app.engine.compass`'s
+    Data-contract shapes) are stored as their OWN JSON columns rather than one combined blob so a future
+    column-projected read never has to deserialize a block it does not need (AG-8 posture). `content_hash`
+    is the sha256 hex digest of the sorted-key JSON of exactly these three blocks (see
+    `app.engine.compass.build_manifest_payload`) — NOT of this row's other columns."""
+
+    __tablename__ = "next_session_manifests"
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    as_of: date = Field(index=True, unique=True)
+    source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)
+    session_delta_json: str
+    narrative_json: str
+    selection_json: str
+    content_hash: str = Field(index=True)
+    created_at: datetime
+
+
 # --- ops-hardening iter-2 (J-05) coverage derived-aggregate snapshot (a PERFORMANCE cache, not a
 # snapshot) -----------------------------------------------------------------------------------
 class CoverageSnapshot(SQLModel, table=True):
diff --git a/apps/backend/main.py b/apps/backend/main.py
index 02257d3d..e0c290c5 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -21,6 +21,7 @@ from fastapi.middleware.cors import CORSMiddleware
 from app.api import (
     backtest,
     budget,
+    compass,
     dashboard,
     data,
     evidence,
@@ -188,6 +189,7 @@ def create_app() -> FastAPI:
     application.include_router(regime_history.router, prefix="/api")
     application.include_router(indexes.router, prefix="/api")
     application.include_router(market_phase.router, prefix="/api")
+    application.include_router(compass.router, prefix="/api")
     # goal-mcp-loop iter-1 — the read-only certified-claims ledger surface (GET /api/evidence).
     application.include_router(evidence.router, prefix="/api")
     # goal-mcp-loop iter-30 (J-18) — the read-only pre-registration registry (GET /api/research/registry).
diff --git a/apps/backend/tests/test_ingest_finalize_disclosure_and_split.py b/apps/backend/tests/test_ingest_finalize_disclosure_and_split.py
index ed5b56e3..e3230f66 100644
--- a/apps/backend/tests/test_ingest_finalize_disclosure_and_split.py
+++ b/apps/backend/tests/test_ingest_finalize_disclosure_and_split.py
@@ -47,8 +47,11 @@ SPY_DAYS = [
 ]
 
 # The categories each half owns. `/data` reads every essential one; none of the deferred three.
+# goal-market-compass iter-2: "next_session_manifest" runs between "market_phase" and
+# "forward_aggregates" in the SAME essential half (a bounded per-date compute, not a long aggregate warm
+# — see data_manager.py's finalize-tail comment at the insertion point).
 ESSENTIAL = {"availability_heatmap", "coverage", "membership_timeline", "market_phase",
-             "forward_aggregates", "index_series", "latest_snapshot"}
+             "next_session_manifest", "forward_aggregates", "index_series", "latest_snapshot"}
 DEFERRED = {"research_hot_keys", "factor_lab_all", "drawdown_expectations"}
 
 
diff --git a/apps/backend/tests/test_no_magic_numbers.py b/apps/backend/tests/test_no_magic_numbers.py
index d8fb1a8e..00bdeb90 100644
--- a/apps/backend/tests/test_no_magic_numbers.py
+++ b/apps/backend/tests/test_no_magic_numbers.py
@@ -50,6 +50,11 @@ CALC_FILES = [
     # min_dollar_vol, adv_window_days) is sourced from config; the only numbers in the resolver are
     # structural (0/1 indexing, the empty-shortcut). The market-cap criterion is dropped (no literal).
     "universe_resolver.py",
+    # goal-market-compass iter-2 (J-02/J-03/J-04) — the session-delta and compass producers. EVERY
+    # threshold/cap (market/breadth/rank/stock-score change minimums, top_k, max_stock_items,
+    # leadership/entry/risk selection cutoffs, max_candidates, why-not floor/cap) comes from
+    # config.compass.*; the only numbers in these two modules are structural (0/1 indexing, comparisons).
+    "session_delta.py", "compass.py",
 ]
 
 # The union of every NUMERIC tunable currently in config.yaml (periods, windows, bucket edges,
diff --git a/apps/backend/tests/test_scoring.py b/apps/backend/tests/test_scoring.py
index 7272521e..6b52d16a 100644
--- a/apps/backend/tests/test_scoring.py
+++ b/apps/backend/tests/test_scoring.py
@@ -581,7 +581,11 @@ def test_historical_row_sector_not_rewritten_by_pool_fallback(loaded_engine):
     `score_stocks` (anti-goal: Snapshots immutable). Simulated by rewinding one ALREADY-STORED
     pool-only row to its honest pre-iteration value (`sector: None`) even though the pool-CSV
     fallback would now resolve it to a real sector — the served row must still read the STORED None,
-    proving storage (not live recompute) is what /api/stocks serves."""
+    proving storage (not live recompute) is what /api/stocks serves.
+
+    T1 (goal-market-compass iter-1 audit, fixed iter-2): the mutation is restored in a `finally` —
+    `loaded_engine` is `scope="session"`, so an unrestored mutation would otherwise leak into every
+    later test in the file sort order that reads this same row's `sector`/`record_json`."""
     cfg = load_config()
     with Session(loaded_engine) as session:
         run = resolved_run(session, None)
@@ -596,15 +600,22 @@ def test_historical_row_sector_not_rewritten_by_pool_fallback(loaded_engine):
         )
         assert target.sector is not None  # sanity: currently stored WITH the fallback applied
 
-        # rewind this ALREADY-STORED row to the honest pre-iteration value
-        record = json.loads(target.record_json)
-        record["sector"] = None
-        target.record_json = json.dumps(record)
-        target.sector = None
-        session.add(target)
-        session.commit()
-
-        served = stocks_payload(session, run)
-        served_row = next(r for r in served["rows"] if r["ticker"] == target.ticker)
-
-    assert served_row["sector"] is None  # served exactly as stored, never re-resolved
+        original_sector = target.sector
+        original_record_json = target.record_json
+        try:
+            # rewind this ALREADY-STORED row to the honest pre-iteration value
+            record = json.loads(target.record_json)
+            record["sector"] = None
+            target.record_json = json.dumps(record)
+            target.sector = None
+            session.add(target)
+            session.commit()
+
+            served = stocks_payload(session, run)
+            served_row = next(r for r in served["rows"] if r["ticker"] == target.ticker)
+            assert served_row["sector"] is None  # served exactly as stored, never re-resolved
+        finally:
+            target.sector = original_sector
+            target.record_json = original_record_json
+            session.add(target)
+            session.commit()
diff --git a/apps/backend/tests/test_universe_screen.py b/apps/backend/tests/test_universe_screen.py
index ee2c257c..5735b676 100644
--- a/apps/backend/tests/test_universe_screen.py
+++ b/apps/backend/tests/test_universe_screen.py
@@ -244,3 +244,23 @@ def test_pool_sector_map_missing_pool_file_degrades_to_empty_map(tmp_path):
     """A not-yet-built pool file degrades to an empty map (never a crash) — the same honest-empty
     contract `read_pool`'s other callers already tolerate for a missing `universe_pool.csv`."""
     assert pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=tmp_path) == {}
+
+
+def test_pool_sector_map_builds_valid_set_once_survives_a_one_shot_iterable(tmp_path):
+    """B2 (goal-market-compass iter-1 audit, fixed iter-2): before the fix, `valid_sectors` was
+    re-`set(...)`-ed INSIDE `resolve_pool_sector` on every row, so a one-shot iterable (e.g. a
+    generator) would be exhausted by the FIRST row and every later row would silently resolve to
+    `None` — a whole-pool coverage collapse with no exception. `pool_sector_map` now materializes the
+    set ONCE up front, so passing a generator here — which can be iterated exactly once — must still
+    resolve every one of several rows, not just the first."""
+    seed_dir = _write_pool_csv(
+        tmp_path,
+        [
+            {"symbol": "ZZZ1", "sector": "Technology", "source": "test"},
+            {"symbol": "ZZZ2", "sector": "Financials", "source": "test"},
+            {"symbol": "ZZZ3", "sector": "Technology", "source": "test"},
+        ],
+    )
+    one_shot_valid_sectors = (name for name in ("Technology", "Financials"))  # a generator: exhausts after ONE full iteration
+    mapping = pool_sector_map(aliases={}, valid_sectors=one_shot_valid_sectors, seed_dir=seed_dir)
+    assert mapping == {"ZZZ1": "Technology", "ZZZ2": "Financials", "ZZZ3": "Technology"}
diff --git a/apps/frontend/app/methodology/page.tsx b/apps/frontend/app/methodology/page.tsx
index d448dd3c..c915d5db 100644
--- a/apps/frontend/app/methodology/page.tsx
+++ b/apps/frontend/app/methodology/page.tsx
@@ -9,6 +9,7 @@ import { Badge } from "@/components/ui/badge";
 import { Card } from "@/components/ui/card";
 import {
   fetchMethodology,
+  type CompassSelectionBasis,
   type GlossaryTerm,
   type MethodologyCatalog,
   type MethodologyEntry,
@@ -65,6 +66,10 @@ export default function MethodologyPage() {
         <SectorBasisCard sectorBasis={state.data.sector_basis} />
       ) : null}
 
+      {state.kind === "ok" && state.data.compass_selection ? (
+        <CompassSelectionCard selection={state.data.compass_selection} />
+      ) : null}
+
       {state.kind === "loading" ? <MethodologySkeleton /> : null}
 
       {state.kind === "error" ? (
@@ -313,6 +318,28 @@ function SectorBasisCard({ sectorBasis }: { sectorBasis: string }) {
   );
 }
 
+/** The J-04 (goal-market-compass iter-2) "Next-session focus" disclosure: the candidate-selection
+ *  rule prose + its live `compass.selection.*` thresholds, reusing the SAME `ThresholdRow` renderer
+ *  as every other threshold list on this page. A sibling of `SectorBasisCard`, rendered unconditionally
+ *  for the same reason (see that card's note) — this disclosure makes no universe-screen claim. */
+function CompassSelectionCard({ selection }: { selection: CompassSelectionBasis }) {
+  return (
+    <Card className="space-y-3 p-4" data-testid="compass-selection-basis">
+      <div className="flex flex-wrap items-center gap-2">
+        <Filter className="h-4 w-4 text-accent" aria-hidden />
+        <h2 className="text-base font-semibold text-text">Next-session focus</h2>
+        <Badge variant="default">Selection rule</Badge>
+      </div>
+      <p className="text-sm text-text-muted">{selection.text}</p>
+      <ul className="space-y-1">
+        {selection.thresholds.map((row, index) => (
+          <ThresholdRow key={index} row={row} />
+        ))}
+      </ul>
+    </Card>
+  );
+}
+
 function EntryCard({ entry }: { entry: MethodologyEntry }) {
   return (
     <Card className="space-y-3 p-4" data-entry-key={entry.key}>
diff --git a/apps/frontend/app/page.tsx b/apps/frontend/app/page.tsx
index 65767cd7..d8bb34ab 100644
--- a/apps/frontend/app/page.tsx
+++ b/apps/frontend/app/page.tsx
@@ -6,10 +6,14 @@ import { AlertTriangle, Clock, ChevronDown } from "lucide-react";
 
 import { useAsOf } from "@/components/asof-provider";
 import { ComponentBreakdown } from "@/components/component-breakdown";
+import { CompassSummaryCard } from "@/components/compass-summary-card";
+import { CompassWhatChangedCard } from "@/components/compass-whatchanged-card";
+import { CompassFocusSection } from "@/components/compass-focus-section";
 import { MarketPhaseCard } from "@/components/market-phase-card";
 import { PhaseCrossViewCard } from "@/components/phase-cross-view-card";
 import { PageHeading } from "@/components/page-heading";
 import { ScoreBadge } from "@/components/score-badge";
+import { Disclosure } from "@/components/ui/disclosure";
 import { TermInfo } from "@/components/ui/term-info";
 import { Badge } from "@/components/ui/badge";
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
@@ -19,10 +23,12 @@ import { phaseColor } from "@/lib/phase";
 import { regimeVariant } from "@/lib/regime-variant";
 import { cn } from "@/lib/utils";
 import {
+  fetchCompass,
   fetchDashboard,
   fetchMarketPhase,
   fetchSectors,
   fetchThemes,
+  type CompassResponse,
   type DashboardResponse,
   type MarketPhaseComponent,
   type MarketPhaseResponse,
@@ -38,6 +44,7 @@ type State =
       phase: MarketPhaseResponse | null;
       sectors: SectorsResponse | null;
       themes: ThemesResponse | null;
+      compass: CompassResponse | null;
     }
   | { kind: "error" };
 
@@ -61,14 +68,15 @@ export default function DashboardPage() {
     const controller = new AbortController();
     const asof = asOf ?? undefined; // historical date or latest
     // Dashboard (regime + candidate counts) is critical; the market-phase summary + Top Sectors + Top
-    // Themes read their own canonical endpoints and may fail independently. All fetch the SAME as-of date
-    // so the snapshot view is coherent across the page.
+    // Themes + compass (goal-market-compass iter-2) read their own canonical endpoints and may fail
+    // independently. All fetch the SAME as-of date so the snapshot view is coherent across the page.
     setState({ kind: "loading" });
     fetchDashboard(asof, controller.signal)
       .then(async (dashboard) => {
         let phase: MarketPhaseResponse | null = null;
         let sectors: SectorsResponse | null = null;
         let themes: ThemesResponse | null = null;
+        let compass: CompassResponse | null = null;
         try {
           phase = await fetchMarketPhase(asof, controller.signal);
         } catch {
@@ -84,7 +92,12 @@ export default function DashboardPage() {
         } catch {
           themes = null;
         }
-        setState({ kind: "ok", dashboard, phase, sectors, themes });
+        try {
+          compass = await fetchCompass(asof, controller.signal);
+        } catch {
+          compass = null;
+        }
+        setState({ kind: "ok", dashboard, phase, sectors, themes, compass });
       })
       .catch(() => {
         if (!controller.signal.aborted) setState({ kind: "error" });
@@ -120,12 +133,21 @@ export default function DashboardPage() {
       ) : null}
 
       {state.kind === "ok" ? (
-        <DashboardBody
-          dashboard={state.dashboard}
-          phase={state.phase}
-          sectors={state.sectors}
-          themes={state.themes}
-        />
+        <>
+          {/* goal-market-compass iter-2 (J-02/J-03/J-04): three new Today-page sections, each reading
+              ONLY GET /api/compass, rendered ABOVE the existing dashboard body below. That body
+              (DashboardBody and everything it renders) is UNCHANGED by this iteration — final section
+              ordering/chrome placement is J-07's job, and removing it from `/` is J-08's job. */}
+          <CompassSummaryCard compass={state.compass} />
+          <CompassWhatChangedCard compass={state.compass} />
+          <CompassFocusSection compass={state.compass} />
+          <DashboardBody
+            dashboard={state.dashboard}
+            phase={state.phase}
+            sectors={state.sectors}
+            themes={state.themes}
+          />
+        </>
       ) : null}
     </div>
   );
@@ -296,25 +318,6 @@ function SeverityBreakdown({ components }: { components: MarketPhaseComponent[]
   );
 }
 
-/** A lightweight inline disclosure (native `<details>`) — keeps a figure's named breakdown REACHABLE
- *  (one click) without crowding the at-a-glance summary. Pure presentation, no business logic. */
-function Disclosure({ summary, children }: { summary: string; children: React.ReactNode }) {
-  return (
-    <details className="group rounded border border-border bg-surface-2/40">
-      <summary
-        className={cn(
-          "flex cursor-pointer list-none items-center justify-between gap-2 px-2.5 py-1.5 text-xs text-text-muted",
-          "transition-colors hover:text-text focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
-        )}
-      >
-        {summary}
-        <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" aria-hidden />
-      </summary>
-      <div className="border-t border-border px-2.5 pb-2.5">{children}</div>
-    </details>
-  );
-}
-
 /** J-98: the collapsed "More detail" section — breadth metrics, candidate counts, Top Sectors, Top Themes,
  *  and the full Market Phase & Severity detail card. SAME data, SAME endpoints, only repositioned (nothing
  *  removed). Defaults to COLLAPSED at first paint (the spec: first paint shows only the summary + chart). */
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 3d78599c..9209404c 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -873,6 +873,135 @@ export async function fetchThemes(asof?: string, signal?: AbortSignal): Promise<
   return getJSON<ThemesResponse>(withAsOf("/api/themes", asof), signal);
 }
 
+// --- compass (goal-market-compass iter-2, J-02/J-03/J-04) -----------------------------------
+/** One session-over-session change entry (J-02) — already threshold-gated server-side; the
+ *  frontend renders it verbatim and evaluates no threshold itself. */
+export interface SessionDeltaChange {
+  kind: "market" | "breadth" | "sector" | "theme" | "stock";
+  label: string;
+  from: number | string;
+  to: number | string;
+  magnitude: number;
+  threshold: number;
+  drill_href: string;
+}
+
+/** One BELOW-threshold entry, shown only inside the "suppressed moves" disclosure. */
+export interface SessionDeltaSuppressed {
+  kind: string;
+  magnitude: number;
+  threshold: number;
+}
+
+/** The `session_delta` CONTENT block (J-02). `prior_as_of`/`gap_days` are both `null` for the
+ *  earliest stored run — the explicit no-prior-run state; never a fabricated comparison. */
+export interface SessionDelta {
+  prior_as_of: string | null;
+  gap_days: number | null;
+  changes: SessionDeltaChange[];
+  suppressed: SessionDeltaSuppressed[];
+  suppressed_count: number;
+}
+
+/** One cited fact backing a narrative sentence (J-03) — spot-checkable against the canonical
+ *  endpoint (e.g. GET /api/dashboard, GET /api/market-phase) it was read from. */
+export interface NarrativeFact {
+  name: string;
+  value: string | number | boolean | null;
+}
+
+/** One deterministic template sentence (J-03). `text` is rendered VERBATIM — the frontend
+ *  assembles no wording of its own. */
+export interface NarrativeSentence {
+  template_id: string;
+  text: string;
+  facts: NarrativeFact[];
+}
+
+/** The `narrative` CONTENT block (J-03) — the Summary card's ordered sentence list. */
+export interface Narrative {
+  sentences: NarrativeSentence[];
+}
+
+/** The fixed eligibility-checklist verdict vocabulary (J-04). */
+export type ChecklistVerdict = "Pass" | "Miss" | "Supportive" | "Neutral" | "Unknown" | "NA";
+
+export interface ChecklistRow {
+  condition: string;
+  threshold: number;
+  actual: number;
+  verdict: ChecklistVerdict;
+}
+
+export interface WhatWouldChangeRow {
+  condition: string;
+  threshold: number;
+  actual: number;
+  met: boolean;
+}
+
+/** One next-session candidate (J-04) — `leadership_word`/`entry_word`/`risk_word` are the config
+ *  word-map values for the SAME three existing scores/buckets `GET /api/stocks` serves; no new
+ *  blended/composite number is ever present here (anti-goal AG-11). */
+export interface CompassCandidate {
+  ticker: string;
+  leadership_word: string;
+  leadership_score: number;
+  entry_word: string;
+  entry_quality_score: number;
+  risk_word: string;
+  risk_score: number;
+  reasons: string[];
+  cautions: string[];
+  checklist: ChecklistRow[];
+  what_would_change: WhatWouldChangeRow[];
+  invalidation: string;
+}
+
+export interface WhyNotFailedCondition {
+  condition: string;
+  threshold: number;
+  actual: number;
+  distance: number;
+}
+
+/** One non-candidate near the selection floor (J-04) — an EMPTY `failed_conditions` means the
+ *  member passed every qualifier and was excluded only by the focus-list cap, never a fabricated
+ *  reason. */
+export interface WhyNotEntry {
+  ticker: string;
+  failed_conditions: WhyNotFailedCondition[];
+}
+
+/** The `selection` CONTENT block (J-04) — the Next-session focus section's full trace.
+ *  `disposition_tally.below_selection_floor + excluded_by_cap` partitions every non-candidate
+ *  member; `candidates_empty_reason` is set (never a bare empty list) whenever `candidates` is
+ *  empty. The near-threshold shadow cohort (J-05/J-06) appears nowhere in this shape. */
+export interface CompassSelection {
+  candidates: CompassCandidate[];
+  why_not: WhyNotEntry[];
+  disposition_tally: { below_selection_floor: number; excluded_by_cap: number };
+  candidates_empty_reason: string | null;
+}
+
+/** GET /api/compass payload (goal-market-compass iter-2) — the next-session manifest CONTENT
+ *  block: what changed (J-02), the plain-English summary (J-03), and the next-session candidates
+ *  (J-04), all computed ONCE per `as_of` and served from storage thereafter. `content_hash` is the
+ *  sha256 of the sorted-key JSON of exactly these three blocks. */
+export interface CompassResponse {
+  as_of: string;
+  session_delta: SessionDelta;
+  narrative: Narrative;
+  selection: CompassSelection;
+  content_hash: string;
+}
+
+/** Canonical next-session-manifest CONTENT source: GET /api/compass. `asof` time-travels to that
+ *  date's stored (or create-once-computed) manifest — never recomputed client-side. */
+export async function fetchCompass(asof?: string, signal?: AbortSignal): Promise<CompassResponse> {
+  return getJSON<CompassResponse>(withAsOf("/api/compass", asof), signal);
+}
+
 // --- scanner runs (iter-5) -----------------------------------------------------------------
 /** One row in the immutable scan-run history (GET /api/runs). `regime` carries the stored as-of
  *  label+score; `candidate_counts` are the stored counts of the canonical setup statuses. */
@@ -1327,6 +1456,13 @@ export interface MethodologyGlossary {
   categories: GlossaryCategory[];
 }
 
+/** J-04 (goal-market-compass iter-2): the "Next-session focus" disclosure — the selection-rule prose
+ *  + the live `compass.selection.*` thresholds it names (resolved on the backend, never re-typed). */
+export interface CompassSelectionBasis {
+  text: string;
+  thresholds: MethodologyThresholdRow[];
+}
+
 /** The config-backed Setup & Pattern catalog served by GET /api/methodology. The ONE source for the
  *  /methodology page, the /stocks badge tooltips, the /stocks setup-filter vocabulary, AND (J-47) the
  *  full terminology glossary + every inline term tooltip. `universe_selection` (J-22) carries the
@@ -1340,6 +1476,9 @@ export interface MethodologyCatalog {
    *  `universe_selection`, NOT nested inside it, so the J-22 honest-universe gate cannot hide it.
    *  Config prose served verbatim — the frontend never resolves a sector itself. */
   sector_basis?: string;
+  /** J-04 (goal-market-compass iter-2): the Next-session focus disclosure — a sibling of
+   *  `universe_selection` for the same reason `sector_basis` is a sibling (see above). */
+  compass_selection?: CompassSelectionBasis;
   entries: MethodologyEntry[];
   glossary?: MethodologyGlossary;
 }
diff --git a/config.yaml b/config.yaml
index 84d70737..5e9cfb17 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1389,6 +1389,63 @@ watchlist:
     cluster_threshold: 0.7       # Pearson correlation at/above which two members join the same cluster
     min_overlap_days: 60         # a member's own return series shorter than this renders NA throughout
 
+# ----------------------------------------------------------------------------------------
+# goal-market-compass iter-2 (J-02/J-03/J-04) — the Today-page decision surface: session-over-session
+# deltas, the deterministic plain-English narrative, and the next-session candidate-selection trace.
+# EVERY threshold/word map the three new `app.engine.session_delta` / `app.engine.compass` producers read
+# lives here (anti-goal: No magic numbers) — computed once at ingest finalize (or once on first
+# GET /api/compass for a not-yet-computed as-of) and served from the `next_session_manifests` table
+# thereafter. `selection.shadow.min_score` is reserved now for J-05/J-06's near-threshold shadow cohort —
+# unused by any code this iteration.
+compass:
+  delta:
+    rule_version: "v1"
+    market_score_min_change: 5.0     # regime-score points to report a "market" change
+    breadth_min_change_pts: 5.0      # breadth percentage points (above-50DMA / above-200DMA) to report a "breadth" change
+    rank_move_min: 2                 # sector/theme rank positions moved to report a change
+    stock_score_min_change: 8.0      # leadership-score points a bucket-crossing stock must move to report a "stock" change
+    top_k: 5                         # max sector-kind and max theme-kind change entries shown (most-moved first; mirrors the existing Top-Sectors/Top-Themes "top 5" convention)
+    max_stock_items: 10              # max stock-kind change entries evaluated/shown (bounds both compute and display — AG-8)
+    velocity_flat_band: 2.0          # |regime-score delta| below this reads as "little changed" in the narrative's direction sentence
+    pbear_bands:                     # filtered P(bear) -> narrative state word (ascending min, like market_phase.phase_edges)
+      - { min: 0.0, label: "calm" }
+      - { min: 0.20, label: "cautious" }
+      - { min: 0.40, label: "tense" }
+      - { min: 0.60, label: "stressed" }
+  selection:
+    rule_version: "v1"
+    leadership_min_score: 80.0       # the ONLY candidacy gate on Leadership (never the Actionable/A-bucket setup status)
+    entry_min_score: 70.0            # candidacy qualifier: Entry Quality score floor
+    risk_max_score: 60.0             # candidacy qualifier: Risk score ceiling (risk is a danger score — lower is safer)
+    max_candidates: 10               # cap on the Next-session focus section's candidate list
+    why_not_floor: 75.0              # a non-candidate at/above this Leadership score gets an individual why-not entry
+    why_not_cap: 20                  # max why-not entries returned (the disposition tally stays a full, uncapped count)
+    shadow:
+      min_score: 75.0                # RESERVED for J-05/J-06's near-threshold shadow cohort — not read by any iter-2 code
+  vocabulary:
+    direction_words:
+      up: "improving"
+      down: "deteriorating"
+      flat: "little changed"
+    leadership_words: { A: "Elite leader", B: "Strong leader", C: "Average leader", D: "Weak leader", E: "Laggard" }
+    entry_words: { A: "Ideal entry", B: "Good entry", C: "Fair entry", D: "Poor entry", E: "Weak entry" }
+    risk_words: { A: "Very high risk", B: "High risk", C: "Moderate risk", D: "Low risk", E: "Very low risk" }
+    # TC-11's committed banned-language list: imperative trade verbs, forecast terms, causal-attribution
+    # phrases (AG-2). Every rendered narrative sentence is scanned against this list, case-insensitively.
+    banned_terms:
+      - "buy"
+      - "sell"
+      - "should buy"
+      - "should sell"
+      - "will rise"
+      - "will fall"
+      - "target price"
+      - "guaranteed"
+      - "recommend"
+      - "act now"
+      - "because of"
+      - "caused by"
+
 # ----------------------------------------------------------------------------------------
 # iter-12 CONSUMED — Methodology / Glossary catalog (J-12). The SINGLE config-backed source that
 # EXPLAINS every setup status + the VCP pattern: a plain-language meaning, the exact thresholds that
@@ -1418,6 +1475,18 @@ methodology:
       - { label: "Minimum market cap", cmp: ">=", ref: "universe.filters.min_market_cap", unit: "$" }
       - { label: "Minimum average daily dollar volume", cmp: ">=", ref: "universe.filters.min_dollar_vol", unit: "$" }
       - { label: "Minimum share price", cmp: ">=", ref: "universe.filters.min_price", unit: "$" }
+  # goal-market-compass iter-2 (J-04): the /methodology "Next-session focus" disclosure — the
+  # candidate-selection rule prose + its live `compass.selection.*` thresholds, resolved via the SAME
+  # `ref` mechanism as Universe Selection above (never re-typed — the matching-config keystone). Served
+  # as its OWN top-level sibling key (same reasoning as sector_basis below) so the J-22 universe gate
+  # never hides it — this disclosure makes no universe-screen claim.
+  compass_selection:
+    text: "The Today page's Next-session focus list is a transparent rule over stored scores, not a prediction: a name qualifies when its Leadership score clears the floor below and its Entry Quality and Risk scores clear their own qualifiers, ranked and capped at the list size. No new blended number is computed for this — every value shown is one of the existing Leadership / Entry Quality / Risk scores plus the existing config word maps. Non-candidates at or above the floor are shown too, in a 'Not priority' list naming exactly which condition they missed and by how much."
+    thresholds:
+      - { label: "Leadership score", cmp: ">=", ref: "compass.selection.leadership_min_score" }
+      - { label: "Entry Quality score", cmp: ">=", ref: "compass.selection.entry_min_score" }
+      - { label: "Risk score", cmp: "<=", ref: "compass.selection.risk_max_score" }
+      - { label: "Focus list size", cmp: "<=", ref: "compass.selection.max_candidates" }
   entries:
     - key: Actionable
       kind: setup
@@ -1521,6 +1590,7 @@ methodology:
     - { key: universe_data,     label: "Universe & Data" }
     - { key: forward_evidence,  label: "Forward-testing & Evidence" }
     - { key: factor_stats,      label: "Factor Lab & Statistics" }
+    - { key: today_compass,     label: "Today & Next-Session Focus" }
   terms:
     # --- Scores & Buckets -----------------------------------------------------------------
     - term: "Leadership Score"
@@ -2026,3 +2096,22 @@ methodology:
       category: factor_stats
       definition: "The trailing window of bars a measure is computed over (e.g. a 63-bar 3-month RS lookback). Longer lookbacks capture structural trend; shorter ones capture recent momentum."
       where: "Indicators, factors."
+    # --- Today & Next-Session Focus (goal-market-compass iter-2, J-02/J-03/J-04) --------------
+    - term: "session delta"
+      category: today_compass
+      definition: "The set of stored market/breadth/sector/theme/stock changes between the current session and the immediately preceding stored session, each shown only when its magnitude clears a config threshold — smaller moves are counted as suppressed, never silently dropped."
+      where: "Today page — What-changed card."
+    - term: "next-session candidate"
+      category: today_compass
+      definition: "A name whose stored Leadership score clears the selection floor and whose Entry Quality and Risk scores clear their own qualifiers, as of the latest session — framed as worth monitoring next session, never as advice to buy or a return prediction."
+      where: "Today page — Next-session focus section."
+      thresholds:
+        - { label: "Leadership score", cmp: ">=", ref: "compass.selection.leadership_min_score" }
+    - term: "why-not"
+      category: today_compass
+      definition: "The explicit list of non-candidates near the selection floor, each naming which condition it missed and by how much (a distance), so absence from the focus list is as explainable as presence on it."
+      where: "Today page — Next-session focus section."
+    - term: "retrospective stamp"
+      category: today_compass
+      definition: "A visible note on a historical Today-page view stating that its summary was reconstructed under the CURRENT rule/config rather than generated live on that date — historical reads never silently pass off a rebuilt view as the original."
+      where: "Today page — summary card (historical as-of only)."
diff --git a/incredible_auto_dev/.claude/agents/demo-narrator.md b/incredible_auto_dev/.claude/agents/demo-narrator.md
index f7b271d0..bde5291f 100644
--- a/incredible_auto_dev/.claude/agents/demo-narrator.md
+++ b/incredible_auto_dev/.claude/agents/demo-narrator.md
@@ -102,6 +102,12 @@ The runner tries your hint, then auto-degrades, so prefer the most semantic one:
 Use the **exact** visible text/label from the QA artifact — that text is what
 made the QA flow pass, and the runner matches on the same accessible name.
 
+**`name`/`text`/`label`/`placeholder` values must always be plain double-quoted JSON strings** — never
+a `/regex/flags` literal (that JS/Playwright idiom is not valid JSON and breaks `json.load` on the whole
+script; the runner also has no regex matching, so it would silently never match even if it somehow
+parsed). If you're tempted to "match loosely," just use the shortest exact visible substring instead —
+e.g. write `{"role": "button", "name": "Filter by sector"}`, never `{"role": "button", "name": /Filter by sector/i}`.
+
 ### Step fields
 
 - `section`: `"highlights"` (gets a screenshot in the gallery; **cap at 8** — pick the highest-impact end-to-end smoke) or `"full_tour"` (text-only in the gallery; the live walkthrough still plays it). If everything fits in 8 steps, make them all highlights.
diff --git a/incredible_auto_dev/agents/demo-narrator/body.md b/incredible_auto_dev/agents/demo-narrator/body.md
index f8d89290..cf30b0f6 100644
--- a/incredible_auto_dev/agents/demo-narrator/body.md
+++ b/incredible_auto_dev/agents/demo-narrator/body.md
@@ -93,6 +93,12 @@ The runner tries your hint, then auto-degrades, so prefer the most semantic one:
 Use the **exact** visible text/label from the QA artifact — that text is what
 made the QA flow pass, and the runner matches on the same accessible name.
 
+**`name`/`text`/`label`/`placeholder` values must always be plain double-quoted JSON strings** — never
+a `/regex/flags` literal (that JS/Playwright idiom is not valid JSON and breaks `json.load` on the whole
+script; the runner also has no regex matching, so it would silently never match even if it somehow
+parsed). If you're tempted to "match loosely," just use the shortest exact visible substring instead —
+e.g. write `{"role": "button", "name": "Filter by sector"}`, never `{"role": "button", "name": /Filter by sector/i}`.
+
 ### Step fields
 
 - `section`: `"highlights"` (gets a screenshot in the gallery; **cap at 8** — pick the highest-impact end-to-end smoke) or `"full_tour"` (text-only in the gallery; the live walkthrough still plays it). If everything fits in 8 steps, make them all highlights.
diff --git a/apps/backend/app/api/compass.py b/apps/backend/app/api/compass.py
new file mode 100644
index 00000000..f57de130
--- /dev/null
+++ b/apps/backend/app/api/compass.py
@@ -0,0 +1,26 @@
+"""GET /api/compass — the next-session manifest CONTENT block (goal-market-compass iter-2, J-02/J-03/
+J-04). Serves the stored `NextSessionManifest` row for the resolved `as_of`, computing + persisting it
+ONCE if absent (create-once-on-GET — zero producer calls on a warm hit, TC-1) and serving from storage
+on every subsequent hit for that `as_of`. Reuses `snapshot_serving`'s as-of error mapping so a requested
+`as_of` with no stored run returns the SAME honest error shape every other as-of-aware endpoint does —
+never a fabricated payload.
+"""
+from __future__ import annotations
+
+from typing import Optional
+
+from fastapi import APIRouter, Depends
+from sqlmodel import Session
+
+from app.db import get_session
+from app.engine.compass import get_or_create_manifest, manifest_row_payload
+from app.engine.snapshot_serving import resolved_run
+
+router = APIRouter(tags=["compass"])
+
+
+@router.get("/compass")
+def compass(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
+    run = resolved_run(session, as_of)
+    row = get_or_create_manifest(session, run)
+    return manifest_row_payload(row)
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
new file mode 100644
index 00000000..8ad066a6
--- /dev/null
+++ b/apps/backend/app/engine/compass.py
@@ -0,0 +1,493 @@
+"""app.engine.compass — the deterministic narrative + candidate-selection trace + manifest assembly
+(goal-market-compass iter-2, J-03/J-04, CONTENT block only).
+
+Three producers, one assembler:
+
+  - `build_narrative(...)` — deterministic template sentences (state / direction / breadth /
+    focus-count, plus a no-comparison / NA-velocity / retrospective-stamp variant where it applies),
+    each carrying `{template_id, text, facts}`. Word maps and thresholds live only in
+    `compass.vocabulary.*` / `compass.delta.*` — never a literal here (see test_no_magic_numbers.py).
+  - `evaluate_selection(...)` — the transparent candidate-selection rule (J-04) over stored
+    `ScannerResult` rows: candidates with reasons/cautions/checklist/what-would-change/invalidation;
+    why-not entries for near-miss and cap-excluded non-candidates; a disposition tally that partitions
+    member count minus candidate count exactly; an explicit `candidates_empty_reason` when nothing
+    clears the floor. No new blended/composite score is introduced anywhere (AG-11) — every value shown
+    is one of the three existing per-stock scores/buckets plus a config word map.
+  - `build_manifest_payload(...)` — assembles `session_delta` + `narrative` + `selection` into one
+    content document and computes `content_hash` (sha256 over the sorted-key JSON of the content block
+    only).
+
+`get_or_create_manifest` / `manifest_row_payload` are the storage half: compute once per `as_of`
+(create-once), persist immutably (AG-12 — never updated or deleted), serve from storage on every later
+hit (TC-1 — zero producer calls on a warm read).
+
+Reads ONLY column-projected `ScannerResult` selects for the universe-wide sweep, plus a SMALL, bounded
+`record_json` read for the (<= `max_candidates`) actual candidates only — never a full-universe
+`record_json` sweep (AG-8). Never reads `forward_returns` or any bar dated after the as-of — it reads
+already-stored, already-computed run rows only (AG-5).
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import datetime, timezone
+from typing import Optional
+
+from sqlalchemy.exc import IntegrityError
+from sqlmodel import Session, select
+
+from app.config import Config, get_config
+from app.engine import market_phase
+from app.engine.session_delta import compute_delta, find_previous_run
+from app.engine.setups import RISK_OFF_LABEL
+from app.engine.snapshot_serving import dashboard_payload
+from app.models import NextSessionManifest, ScannerResult, ScannerRun
+
+# --- narrative -------------------------------------------------------------------------------
+
+_DIRECTION_TEMPLATE = "direction"
+_DIRECTION_NO_PRIOR_RUN_TEMPLATE = "direction_no_prior_run"
+_DIRECTION_NA_VELOCITY_TEMPLATE = "direction_na_velocity"
+
+
+def _pbear_word(p_bear: Optional[float], cfg: Config) -> Optional[str]:
+    """The filtered P(bear) -> narrative state word, via the highest `compass.delta.pbear_bands` edge
+    whose `min` the value clears (ascending-min band, same convention as `market_phase.phase_edges`)."""
+    if p_bear is None:
+        return None
+    word: Optional[str] = None
+    for band in cfg.compass.delta.pbear_bands:
+        if p_bear >= band.min:
+            word = band.label
+    return word
+
+
+def _state_sentence(dashboard: dict, phase_payload: dict, cfg: Config) -> dict:
+    regime_label = dashboard["regime"]["label"]
+    regime_score = dashboard["regime"]["score"]
+    facts = [
+        {"name": "regime_label", "value": regime_label},
+        {"name": "regime_score", "value": regime_score},
+    ]
+    if phase_payload.get("available"):
+        severity = phase_payload.get("severity")
+        phase_label = phase_payload.get("phase")
+        level_word = _pbear_word(phase_payload.get("p_bear"), cfg)
+        facts.append({"name": "market_phase", "value": phase_label})
+        facts.append({"name": "severity", "value": severity})
+        if level_word is not None and severity is not None:
+            text = (
+                f"Market regime is {regime_label} ({regime_score:.1f}/100); market phase is "
+                f"{phase_label} with {level_word} conditions (severity {severity:.1f}/100)."
+            )
+        else:
+            text = f"Market regime is {regime_label} ({regime_score:.1f}/100); market phase is {phase_label}."
+    else:
+        text = (
+            f"Market regime is {regime_label} ({regime_score:.1f}/100); market phase is not yet "
+            "available for this session (insufficient trailing history)."
+        )
+    return {"template_id": "state", "text": text, "facts": facts}
+
+
+def _direction_word(current_run: ScannerRun, previous_run: ScannerRun, cfg: Config) -> tuple[str, float]:
+    delta = current_run.regime_score - previous_run.regime_score
+    if abs(delta) < cfg.compass.delta.velocity_flat_band:
+        return cfg.compass.vocabulary.direction_words["flat"], delta
+    return cfg.compass.vocabulary.direction_words["up" if delta > 0 else "down"], delta
+
+
+def _direction_sentence(
+    current_run: ScannerRun, previous_run: Optional[ScannerRun], phase_payload: dict, cfg: Config
+) -> dict:
+    if previous_run is None:
+        return {
+            "template_id": _DIRECTION_NO_PRIOR_RUN_TEMPLATE,
+            "text": "This is the earliest stored session — no prior-session comparison is available.",
+            "facts": [],
+        }
+    if not phase_payload.get("available"):
+        return {
+            "template_id": _DIRECTION_NA_VELOCITY_TEMPLATE,
+            "text": "Not enough trailing history yet to read a session-over-session direction.",
+            "facts": [],
+        }
+    word, delta = _direction_word(current_run, previous_run, cfg)
+    return {
+        "template_id": _DIRECTION_TEMPLATE,
+        "text": f"Conditions are {word} since the prior session ({delta:+.1f} regime-score points).",
+        "facts": [
+            {"name": "regime_score_delta", "value": delta},
+            {"name": "direction_word", "value": word},
+        ],
+    }
+
+
+def _breadth_sentence(current_run: ScannerRun, cfg: Config) -> dict:
+    b50 = current_run.breadth_above_50dma
+    b200 = current_run.breadth_above_200dma
+    facts = [
+        {"name": "breadth_above_50dma", "value": b50},
+        {"name": "breadth_above_200dma", "value": b200},
+    ]
+    if b50 is None and b200 is None:
+        text = "Breadth data is not available for this session."
+    else:
+        parts = []
+        if b50 is not None:
+            parts.append(f"{b50:.1f}% of the universe above its 50-day average")
+        if b200 is not None:
+            parts.append(f"{b200:.1f}% above its 200-day average")
+        text = f"Universe breadth: {', '.join(parts)}."
+    return {"template_id": "breadth", "text": text, "facts": facts}
+
+
+def _focus_count_sentence(selection: dict, cfg: Config) -> dict:
+    count = len(selection["candidates"])
+    if count == 0:
+        reason = selection.get("candidates_empty_reason") or "no member cleared the selection rule"
+        text = f"No names are worth monitoring next session ({reason})"
+    else:
+        plural = "s" if count != 1 else ""
+        text = f"{count} name{plural} worth monitoring next session."
+    return {"template_id": "focus_count", "text": text, "facts": [{"name": "candidate_count", "value": count}]}
+
+
+def _retrospective_sentence() -> dict:
+    return {
+        "template_id": "retrospective_stamp",
+        "text": (
+            "This is a retrospective view, reconstructed under the CURRENT selection rule and config — "
+            "not necessarily what would have rendered live on this date."
+        ),
+        "facts": [],
+    }
+
+
+def _is_retrospective(session: Session, current_run: ScannerRun) -> bool:
+    """True when a LATER stored run already exists at the moment this manifest is generated — the
+    generation-time signal this narrative's retrospective stamp discloses. (Distinct from, and simpler
+    than, the future `mode`/`generation.*` freeze fields — J-05/J-06, OUT OF SCOPE this iteration.)"""
+    later = session.exec(select(ScannerRun.id).where(ScannerRun.asof_date > current_run.asof_date)).first()
+    return later is not None
+
+
+def _assert_no_banned_language(sentences: list[dict], cfg: Config) -> None:
+    """TC-11 as a runtime guarantee, not only an offline test scan: no rendered sentence may contain a
+    committed banned term (imperative trade verbs, forecast terms, causal-attribution phrases — AG-2)."""
+    banned = cfg.compass.vocabulary.banned_terms
+    for sentence in sentences:
+        lowered = sentence["text"].lower()
+        hits = [term for term in banned if term.lower() in lowered]
+        if hits:
+            raise ValueError(f"narrative sentence {sentence['template_id']!r} contains banned language: {hits}")
+
+
+def build_narrative(
+    session: Session,
+    current_run: ScannerRun,
+    previous_run: Optional[ScannerRun],
+    selection: dict,
+    config: Optional[Config] = None,
+) -> dict:
+    """The `narrative` CONTENT block (goal-market-compass iter-2, J-03). Every sentence is a
+    deterministic template over stored values — no free text, no LLM, no fabricated cause."""
+    cfg = config or get_config()
+    dashboard = dashboard_payload(current_run)
+    phase_payload = market_phase.market_phase_cached(session, current_run.asof_date, cfg)
+
+    sentences = [
+        _state_sentence(dashboard, phase_payload, cfg),
+        _direction_sentence(current_run, previous_run, phase_payload, cfg),
+        _breadth_sentence(current_run, cfg),
+        _focus_count_sentence(selection, cfg),
+    ]
+    if _is_retrospective(session, current_run):
+        sentences.append(_retrospective_sentence())
+
+    _assert_no_banned_language(sentences, cfg)
+    return {"sentences": sentences}
+
+
+# --- selection (J-04) -------------------------------------------------------------------------
+
+_QUALIFIER_CHECKS = ("leadership_min_score", "entry_min_score", "risk_max_score")
+
+
+def _record_json_by_ticker(session: Session, run: ScannerRun, tickers: list[str]) -> dict[str, dict]:
+    """A targeted, bounded `record_json` read for the actual candidates only (`len(tickers) <=
+    max_candidates`) — never a full-universe sweep (AG-8). Deliberately self-contained (does not reuse
+    `snapshot_serving.filtered_stock_rows`, which additionally attaches `forward_returns` — this producer
+    stays grep-clean of any post-as-of read, TC-23)."""
+    if not tickers:
+        return {}
+    rows = session.exec(
+        select(ScannerResult.ticker, ScannerResult.record_json).where(
+            ScannerResult.run_id == run.id, ScannerResult.ticker.in_(tickers)
+        )
+    ).all()
+    return {ticker: json.loads(record_json) for ticker, record_json in rows}
+
+
+def _qualifier_checks(row: dict, cfg: Config) -> list[dict]:
+    sel = cfg.compass.selection
+    return [
+        {
+            "condition": "leadership_min_score",
+            "threshold": sel.leadership_min_score,
+            "actual": row["leadership_score"],
+            "passed": row["leadership_score"] >= sel.leadership_min_score,
+        },
+        {
+            "condition": "entry_min_score",
+            "threshold": sel.entry_min_score,
+            "actual": row["entry_quality_score"],
+            "passed": row["entry_quality_score"] >= sel.entry_min_score,
+        },
+        {
+            "condition": "risk_max_score",
+            "threshold": sel.risk_max_score,
+            "actual": row["risk_score"],
+            "passed": row["risk_score"] <= sel.risk_max_score,
+        },
+    ]
+
+
+def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], run: ScannerRun, cfg: Config) -> dict:
+    vocab = cfg.compass.vocabulary
+    checklist = [
+        {
+            "condition": check["condition"],
+            "threshold": check["threshold"],
+            "actual": check["actual"],
+            "verdict": "Pass" if check["passed"] else "Miss",
+        }
+        for check in checks
+    ]
+    what_would_change = [
+        {
+            "condition": check["condition"],
+            "threshold": check["threshold"],
+            "actual": check["actual"],
+            "met": check["passed"],
+        }
+        for check in checks
+    ]
+    sel = cfg.compass.selection
+    reasons = [
+        f"Leadership score {row['leadership_score']:.1f} clears the {sel.leadership_min_score:.1f} floor "
+        f"({vocab.leadership_words[row['leadership_bucket']]}).",
+        f"Entry Quality score {row['entry_quality_score']:.1f} clears the {sel.entry_min_score:.1f} "
+        f"qualifier ({vocab.entry_words[row['entry_quality_bucket']]}).",
+        f"Risk score {row['risk_score']:.1f} clears the {sel.risk_max_score:.1f} ceiling "
+        f"({vocab.risk_words[row['risk_bucket']]}).",
+    ]
+
+    cautions = []
+    invalidation_note = "No stored invalidation note for this row."
+    risk_budget = (detail or {}).get("risk_budget") or {}
+    atr = risk_budget.get("atr_pct") or {}
+    if atr.get("value") is not None:
+        pct = atr.get("percentile")
+        pct_text = f"p{pct * 100:.0f} of universe" if pct is not None else "percentile NA"
+        cautions.append(
+            f"ATR_RISK_BUDGET: ATR is {atr['value']:.2f}% of price ({pct_text}) — sized risk accordingly."
+        )
+    else:
+        cautions.append("ATR_RISK_BUDGET: risk-budget data not available for this row — reported NA, never fabricated.")
+    inv = (detail or {}).get("invalidation") or {}
+    if inv.get("note"):
+        invalidation_note = inv["note"]
+    if run.regime_label == RISK_OFF_LABEL:
+        cautions.append(
+            "REGIME_RISK_OFF: the market regime is Risk-off as of this date — every candidate here is "
+            "context, not a signal to act."
+        )
+
+    return {
+        "ticker": row["ticker"],
+        "leadership_word": vocab.leadership_words[row["leadership_bucket"]],
+        "leadership_score": row["leadership_score"],
+        "entry_word": vocab.entry_words[row["entry_quality_bucket"]],
+        "entry_quality_score": row["entry_quality_score"],
+        "risk_word": vocab.risk_words[row["risk_bucket"]],
+        "risk_score": row["risk_score"],
+        "reasons": reasons,
+        "cautions": cautions,
+        "checklist": checklist,
+        "what_would_change": what_would_change,
+        "invalidation": invalidation_note,
+    }
+
+
+def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
+    """The `selection` CONTENT block (goal-market-compass iter-2, J-04). See the module docstring for
+    the anti-goal posture (AG-8 bounded reads, AG-11 no new composite score)."""
+    cfg = config or get_config()
+    sel = cfg.compass.selection
+
+    raw_rows = session.exec(
+        select(
+            ScannerResult.ticker,
+            ScannerResult.leadership_score,
+            ScannerResult.leadership_bucket,
+            ScannerResult.entry_quality_score,
+            ScannerResult.entry_quality_bucket,
+            ScannerResult.risk_score,
+            ScannerResult.risk_bucket,
+        )
+        .where(ScannerResult.run_id == run.id)
+        .order_by(ScannerResult.ticker)
+    ).all()
+    member_count = len(raw_rows)
+
+    qualifying: list[tuple[dict, list[dict]]] = []
+    non_qualifying: list[tuple[dict, list[dict]]] = []
+    for ticker, l_score, l_bucket, e_score, e_bucket, r_score, r_bucket in raw_rows:
+        row = {
+            "ticker": ticker,
+            "leadership_score": l_score,
+            "leadership_bucket": l_bucket,
+            "entry_quality_score": e_score,
+            "entry_quality_bucket": e_bucket,
+            "risk_score": r_score,
+            "risk_bucket": r_bucket,
+        }
+        checks = _qualifier_checks(row, cfg)
+        if all(check["passed"] for check in checks):
+            qualifying.append((row, checks))
+        else:
+            failed = [
+                {
+                    "condition": check["condition"],
+                    "threshold": check["threshold"],
+                    "actual": check["actual"],
+                    "distance": abs(check["actual"] - check["threshold"]),
+                }
+                for check in checks
+                if not check["passed"]
+            ]
+            non_qualifying.append((row, failed))
+
+    qualifying.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))
+    candidate_pairs = qualifying[: sel.max_candidates]
+    excluded_by_cap_pairs = qualifying[sel.max_candidates :]
+
+    candidate_tickers = [row["ticker"] for row, _checks in candidate_pairs]
+    detail_by_ticker = _record_json_by_ticker(session, run, candidate_tickers)
+    candidates = [
+        _candidate_payload(row, checks, detail_by_ticker.get(row["ticker"]), run, cfg)
+        for row, checks in candidate_pairs
+    ]
+
+    why_not_pool: list[tuple[dict, list[dict]]] = [
+        (row, failed) for row, failed in non_qualifying if row["leadership_score"] >= sel.why_not_floor
+    ]
+    why_not_pool.extend((row, []) for row, _checks in excluded_by_cap_pairs)  # passed everything, cut by cap
+    why_not_pool.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))
+    why_not = [
+        {"ticker": row["ticker"], "failed_conditions": failed}
+        for row, failed in why_not_pool[: sel.why_not_cap]
+    ]
+
+    candidates_empty_reason = None
+    if not candidates:
... [diff_bound] apps/backend/app/engine/compass.py: 99 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/session_delta.py b/apps/backend/app/engine/session_delta.py
new file mode 100644
index 00000000..363085fb
--- /dev/null
+++ b/apps/backend/app/engine/session_delta.py
@@ -0,0 +1,251 @@
+"""app.engine.session_delta — session-over-session change detection (goal-market-compass iter-2, J-02).
+
+`compute_delta(session, current_run, previous_run, config)` builds the `session_delta` CONTENT block of
+the next-session manifest (see docs/phases/goal-market-compass-iter-2.md's Data-contract addition for
+the exact served shape): the ordered list of meaningful market -> breadth -> sector -> theme -> stock
+changes between `current_run` and the immediately preceding stored run, each gated by its kind's
+`compass.delta.*` threshold, plus the suppressed (below-threshold) entries and an explicit no-prior-run
+state for the earliest stored run.
+
+Reads ONLY column-projected `ScannerResult` / `SectorScoreRow` / `ThemeScoreRow` selects — never a full
+`record_json` sweep (AG-8); `ScannerRun` itself carries no such blob so its typed columns are read
+directly. Compares only two ALREADY-STORED, already-computed runs — there is no `forward_returns` or
+post-as-of bar for this module to read even by accident (AG-5).
+"""
+from __future__ import annotations
+
+from typing import Optional
+
+from sqlmodel import Session, select
+
+from app.config import Config, get_config
+from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow
+
+KIND_MARKET = "market"
+KIND_BREADTH = "breadth"
+KIND_SECTOR = "sector"
+KIND_THEME = "theme"
+KIND_STOCK = "stock"
+
+
+def find_previous_run(session: Session, current_run: ScannerRun) -> Optional[ScannerRun]:
+    """The immediately preceding STORED run by `asof_date` (never by `id` / insertion order — TC-2)."""
+    return session.exec(
+        select(ScannerRun)
+        .where(ScannerRun.asof_date < current_run.asof_date)
+        .order_by(ScannerRun.asof_date.desc())
+    ).first()
+
+
+def _drill_href(kind: str, as_of_iso: str, ticker: Optional[str] = None) -> str:
+    """The change entry's drill-through link, carrying the current `?asof` (TC-3)."""
+    if kind == KIND_STOCK and ticker:
+        return f"/stocks/{ticker}?asof={as_of_iso}"
+    if kind == KIND_SECTOR:
+        return f"/sectors?asof={as_of_iso}"
+    if kind == KIND_THEME:
+        return f"/themes?asof={as_of_iso}"
+    return f"/?asof={as_of_iso}"
+
+
+def _entry(kind: str, label: str, frm, to, magnitude: float, threshold: float, drill_href: str) -> dict:
+    return {
+        "kind": kind,
+        "label": label,
+        "from": frm,
+        "to": to,
+        "magnitude": magnitude,
+        "threshold": threshold,
+        "drill_href": drill_href,
+    }
+
+
+def _classify(pairs: list[tuple[dict, float]], threshold: float) -> tuple[list[dict], list[dict]]:
+    """Split (entry, magnitude) pairs into (changes, suppressed) by one kind's threshold — a magnitude
+    AT OR ABOVE the threshold is a change (TC-3); below it is suppressed (TC-4)."""
+    changes: list[dict] = []
+    suppressed: list[dict] = []
+    for entry, magnitude in pairs:
+        if magnitude >= threshold:
+            changes.append(entry)
+        else:
+            suppressed.append({"kind": entry["kind"], "magnitude": magnitude, "threshold": threshold})
+    return changes, suppressed
+
+
+def _market_changes(
+    current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
+) -> tuple[list[dict], list[dict]]:
+    threshold = cfg.compass.delta.market_score_min_change
+    magnitude = abs(current.regime_score - previous.regime_score)
+    entry = _entry(
+        KIND_MARKET, "Market regime score", previous.regime_score, current.regime_score,
+        magnitude, threshold, _drill_href(KIND_MARKET, as_of_iso),
+    )
+    return _classify([(entry, magnitude)], threshold)
+
+
+def _breadth_changes(
+    current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
+) -> tuple[list[dict], list[dict]]:
+    threshold = cfg.compass.delta.breadth_min_change_pts
+    pairs: list[tuple[dict, float]] = []
+    for label, cur_val, prev_val in (
+        ("Breadth above 50-DMA", current.breadth_above_50dma, previous.breadth_above_50dma),
+        ("Breadth above 200-DMA", current.breadth_above_200dma, previous.breadth_above_200dma),
+    ):
+        if cur_val is None or prev_val is None:
+            continue  # honest NA on either side (insufficient history) — never a fabricated delta
+        magnitude = abs(cur_val - prev_val)
+        entry = _entry(KIND_BREADTH, label, prev_val, cur_val, magnitude, threshold, _drill_href(KIND_BREADTH, as_of_iso))
+        pairs.append((entry, magnitude))
+    return _classify(pairs, threshold)
+
+
+def _sector_changes(
+    session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
+) -> tuple[list[dict], list[dict]]:
+    threshold = cfg.compass.delta.rank_move_min
+    cur_rows = session.exec(
+        select(SectorScoreRow.ticker, SectorScoreRow.name, SectorScoreRow.rank)
+        .where(SectorScoreRow.run_id == current.id)
+        .order_by(SectorScoreRow.ticker)
+    ).all()
+    prev_by_ticker = {
+        ticker: rank
+        for ticker, _name, rank in session.exec(
+            select(SectorScoreRow.ticker, SectorScoreRow.name, SectorScoreRow.rank)
+            .where(SectorScoreRow.run_id == previous.id)
+        ).all()
+    }
+    pairs: list[tuple[dict, float]] = []
+    for ticker, name, cur_rank in cur_rows:
+        prev_rank = prev_by_ticker.get(ticker)
+        if prev_rank is None:
+            continue  # the sector/industry ETF universe is fixed (config.etfs.*) — never new-to-universe
+        magnitude = float(abs(cur_rank - prev_rank))
+        entry = _entry(KIND_SECTOR, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_SECTOR, as_of_iso))
+        pairs.append((entry, magnitude))
+    # Most-moved first within the kind (stable sort — ties keep the deterministic ticker-ordered input),
+    # THEN cap at top_k (mirrors the existing Top-Sectors "top 5" display convention elsewhere in the app).
+    pairs.sort(key=lambda pair: pair[1], reverse=True)
+    changes, suppressed = _classify(pairs, threshold)
+    return changes[: cfg.compass.delta.top_k], suppressed
+
+
+def _theme_changes(
+    session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
+) -> tuple[list[dict], list[dict]]:
+    threshold = cfg.compass.delta.rank_move_min
+    cur_rows = session.exec(
+        select(ThemeScoreRow.slug, ThemeScoreRow.name, ThemeScoreRow.rank)
+        .where(ThemeScoreRow.run_id == current.id)
+        .order_by(ThemeScoreRow.slug)
+    ).all()
+    prev_by_slug = {
+        slug: rank
+        for slug, _name, rank in session.exec(
+            select(ThemeScoreRow.slug, ThemeScoreRow.name, ThemeScoreRow.rank)
+            .where(ThemeScoreRow.run_id == previous.id)
+        ).all()
+    }
+    pairs: list[tuple[dict, float]] = []
+    for slug, name, cur_rank in cur_rows:
+        prev_rank = prev_by_slug.get(slug)
+        if prev_rank is None:
+            continue  # the theme universe is fixed (config.themes) — never new-to-universe
+        magnitude = float(abs(cur_rank - prev_rank))
+        entry = _entry(KIND_THEME, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_THEME, as_of_iso))
+        pairs.append((entry, magnitude))
+    pairs.sort(key=lambda pair: pair[1], reverse=True)
+    changes, suppressed = _classify(pairs, threshold)
+    return changes[: cfg.compass.delta.top_k], suppressed
+
+
+def _stock_changes(
+    session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
+) -> tuple[list[dict], list[dict]]:
+    """Stock-kind entries are leadership-BUCKET crossings (TC-5) plus new-to-universe members (TC-7,
+    reported unconditionally — never as a score change). Bounded to `max_stock_items` total (new members
+    prioritized) so this producer never evaluates, ranks, or displays the full ~500+ member universe in
+    one pass (AG-8)."""
+    threshold = cfg.compass.delta.stock_score_min_change
+    max_items = cfg.compass.delta.max_stock_items
+    cur_rows = session.exec(
+        select(ScannerResult.ticker, ScannerResult.leadership_score, ScannerResult.leadership_bucket)
+        .where(ScannerResult.run_id == current.id)
+        .order_by(ScannerResult.ticker)
+    ).all()
+    prev_by_ticker = {
+        ticker: (score, bucket)
+        for ticker, score, bucket in session.exec(
+            select(ScannerResult.ticker, ScannerResult.leadership_score, ScannerResult.leadership_bucket)
+            .where(ScannerResult.run_id == previous.id)
+        ).all()
+    }
+
+    new_pairs: list[tuple[dict, float]] = []
+    crossing_pairs: list[tuple[dict, float]] = []
+    for ticker, cur_score, cur_bucket in cur_rows:
+        prev = prev_by_ticker.get(ticker)
+        if prev is None:
+            entry = _entry(
+                KIND_STOCK, f"{ticker} new to universe", "new", cur_bucket,
+                cur_score, threshold, _drill_href(KIND_STOCK, as_of_iso, ticker),
+            )
+            new_pairs.append((entry, cur_score))
+            continue
+        prev_score, prev_bucket = prev
+        if cur_bucket == prev_bucket:
+            continue  # only a BUCKET crossing is a "stock" change (TC-5) — a same-bucket score wobble is not
+        magnitude = abs(cur_score - prev_score)
+        entry = _entry(
+            KIND_STOCK, f"{ticker} leadership bucket", prev_bucket, cur_bucket,
+            magnitude, threshold, _drill_href(KIND_STOCK, as_of_iso, ticker),
+        )
+        crossing_pairs.append((entry, magnitude))
+
+    new_pairs.sort(key=lambda pair: pair[1], reverse=True)
+    crossing_pairs.sort(key=lambda pair: pair[1], reverse=True)
+    bounded_new = new_pairs[:max_items]
+    bounded_crossings = crossing_pairs[: max(max_items - len(bounded_new), 0)]
+
+    changes = [entry for entry, _magnitude in bounded_new]
+    crossing_changes, suppressed = _classify(bounded_crossings, threshold)
+    changes.extend(crossing_changes)
+    return changes, suppressed
+
+
+def compute_delta(
+    session: Session,
+    current_run: ScannerRun,
+    previous_run: Optional[ScannerRun],
+    config: Optional[Config] = None,
+) -> dict:
+    """The `session_delta` CONTENT block (goal-market-compass iter-2, J-02). `previous_run` is the
+    immediately preceding STORED run (see `find_previous_run`), or `None` for the earliest stored run —
+    the explicit no-prior-run state (TC-6): no deltas, no direction words, nothing fabricated."""
+    cfg = config or get_config()
+    if previous_run is None:
+        return {"prior_as_of": None, "gap_days": None, "changes": [], "suppressed": [], "suppressed_count": 0}
+
+    as_of_iso = current_run.asof_date.isoformat()
+    changes: list[dict] = []
+    suppressed: list[dict] = []
+    for changes_part, suppressed_part in (
+        _market_changes(current_run, previous_run, as_of_iso, cfg),
+        _breadth_changes(current_run, previous_run, as_of_iso, cfg),
+        _sector_changes(session, current_run, previous_run, as_of_iso, cfg),
+        _theme_changes(session, current_run, previous_run, as_of_iso, cfg),
+        _stock_changes(session, current_run, previous_run, as_of_iso, cfg),
+    ):
+        changes.extend(changes_part)
+        suppressed.extend(suppressed_part)
+
+    return {
+        "prior_as_of": previous_run.asof_date.isoformat(),
+        "gap_days": (current_run.asof_date - previous_run.asof_date).days,
+        "changes": changes,
+        "suppressed": suppressed,
+        "suppressed_count": len(suppressed),
+    }
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
new file mode 100644
index 00000000..a5927ddc
--- /dev/null
+++ b/apps/backend/tests/test_api_compass.py
@@ -0,0 +1,127 @@
+"""GET /api/compass (goal-market-compass iter-2) — API-layer contract: create-once-on-GET / serve-from-
+storage (TC-1), every new field present at the response layer directly, and honest as-of error mapping.
+
+`compass_engine` is a small hand-built DB (mirrors `test_api_runs.py`'s `multi_run_engine` style) —
+deliberately NOT the session-scoped `loaded_engine`. The route function is called DIRECTLY with a
+session (the SAME lightweight pattern `test_api_runs.py::test_api_runs_n_stocks_single_grouped_query_not_per_run`
+uses) rather than through a full TestClient/lifespan, since these are query-shape/contract proofs, not
+browser-facing checks (those are QA's job).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from fastapi import HTTPException
+from sqlmodel import Session
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine import compass as compass_module
+from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+@pytest.fixture()
+def compass_engine(tmp_path):
+    """Two `ScannerRun` rows (so a "prior session" exists) each carrying one `ScannerResult`, plus the
+    `DailyPrice` bars `resolve_as_of_date`/`latest_data_date` need to resolve `as_of` at all."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'compass_api.db'}")
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
+            session.commit()
+    return engine
+
+
+def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
+    from app.api.compass import compass as compass_route
+
+    with Session(compass_engine) as session:
+        result = compass_route(None, session)
+
+    # NOTES: assert every new field at the response layer itself -- never behind a fixture-data gate.
+    assert result["as_of"] == "2024-06-08"
+    assert isinstance(result["session_delta"], dict)
+    for key in ("prior_as_of", "gap_days", "changes", "suppressed", "suppressed_count"):
+        assert key in result["session_delta"]
+    assert isinstance(result["narrative"], dict) and "sentences" in result["narrative"]
+    assert isinstance(result["selection"], dict)
+    for key in ("candidates", "why_not", "disposition_tally", "candidates_empty_reason"):
+        assert key in result["selection"]
+    assert isinstance(result["content_hash"], str) and len(result["content_hash"]) == 64  # sha256 hex
+
+
+def test_compass_route_computes_once_serves_from_storage_after(compass_engine, cfg, monkeypatch):
+    """TC-1: the second call for the same as-of returns byte-identical content with ZERO additional
+    producer calls (get_or_create_manifest short-circuits on the stored row)."""
+    from app.api.compass import compass as compass_route
+
+    calls = {"n": 0}
+    original = compass_module.build_manifest_payload
+
+    def counting_build(*args, **kwargs):
+        calls["n"] += 1
+        return original(*args, **kwargs)
+
+    monkeypatch.setattr(compass_module, "build_manifest_payload", counting_build)
+
+    with Session(compass_engine) as session:
+        first = compass_route(None, session)
+    assert calls["n"] == 1
+
+    with Session(compass_engine) as session:
+        second = compass_route(None, session)
+    assert calls["n"] == 1  # no additional producer call on the second, separate-request hit
+
+    assert first == second
+
+    with Session(compass_engine) as session:
+        rows = session.exec(
+            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
+        ).all()
+    assert len(rows) == 1
+
+
+def test_compass_route_unknown_asof_returns_honest_error_never_fabricated(compass_engine, cfg):
+    from app.api.compass import compass as compass_route
+
+    with Session(compass_engine) as session:
+        with pytest.raises(HTTPException) as exc_info:
+            compass_route("2099-01-01", session)  # far future -- no stored run for this as-of
+    assert exc_info.value.status_code in (400, 404, 422, 503)  # snapshot_serving's honest as-of mapping
+    assert exc_info.value.detail  # a real message, never a silent/empty fabricated body
+
+
+def test_compass_route_historical_asof_serves_that_dates_own_manifest(compass_engine, cfg):
+    from app.api.compass import compass as compass_route
+
+    with Session(compass_engine) as session:
+        result = compass_route("2024-06-01", session)
+    assert result["as_of"] == "2024-06-01"
+    assert result["session_delta"]["prior_as_of"] is None  # earliest stored run -- explicit no-prior-run state
diff --git a/apps/backend/tests/test_compass.py b/apps/backend/tests/test_compass.py
new file mode 100644
index 00000000..f5e203f7
--- /dev/null
+++ b/apps/backend/tests/test_compass.py
@@ -0,0 +1,403 @@
+"""app.engine.compass (goal-market-compass iter-2, J-03/J-04) — narrative, selection, manifest assembly.
+
+File-scoped synthetic fixtures (fresh in-memory SQLite DB, hand-built `ScannerRun` / `ScannerResult` /
+`MarketPhaseCache` rows) — never `loaded_engine`. `MarketPhaseCache` is pre-populated directly (keyed via
+the SAME `_cache_version` the real cache uses) so these tests need no real price history at all.
+"""
+from __future__ import annotations
+
+import ast
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.config import load_config
+from app.engine import compass
+from app.engine import market_phase as market_phase_module
+from app.models import MarketPhaseCache, NextSessionManifest, ScannerResult, ScannerRun
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+def _mk_run(session: Session, asof: date, regime_score: float = 60.0, regime_label: str = "Expansion") -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=regime_score, regime_label=regime_label, regime_components_json="[]",
+        breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _mk_result(
+    session: Session, run_id: int, ticker: str, l_score: float, l_bucket: str,
+    e_score: float, e_bucket: str, r_score: float, r_bucket: str,
+    atr_value=3.0, atr_pct=0.5, invalidation_note=None,
+) -> None:
+    record = {
+        "ticker": ticker,
+        "invalidation": {
+            "basis": "50-DMA", "ma_period": 50, "level": 100.0, "price": 110.0,
+            "note": invalidation_note or f"{ticker} invalidates below its 50-DMA (100.00).",
+        },
+    }
+    if atr_value is not None:
+        record["risk_budget"] = {"atr_pct": {"value": atr_value, "percentile": atr_pct}}
+    session.add(
+        ScannerResult(
+            run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
+            leadership_score=l_score, leadership_bucket=l_bucket,
+            entry_quality_score=e_score, entry_quality_bucket=e_bucket,
+            risk_score=r_score, risk_bucket=r_bucket,
+            setup_status="Breakout-watch", rank=1, record_json=json.dumps(record),
+        )
+    )
+
+
+def _seed_phase_cache(session: Session, as_of: date, available: bool, severity=30.0, phase="Expansion", p_bear=0.15) -> None:
+    version = market_phase_module._cache_version(session)
+    payload = {"available": available}
+    if available:
+        payload.update({"severity": severity, "phase": phase, "p_bear": p_bear})
+    session.add(
+        MarketPhaseCache(
+            asof_key=as_of.isoformat(), dataset_version=version,
+            payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
+        )
+    )
+    session.commit()
+
+
+@pytest.fixture()
+def selection_run(engine, cfg):
+    """One run with a deliberately varied cross-section for J-04 selection tests:
+      AAA: L=92 A, E=85 B, R=40 C  -> qualifies (clears all three)
+      BBB: L=88 A, E=78 B, R=45 C  -> qualifies
+      CCC: L=77 B, E=55 D, R=50 C  -> fails entry_min_score (70) -> near-miss why-not (leadership 77 >= floor 75)
+      DDD: L=30 E, E=20 E, R=90 E  -> fails everything, leadership far below why_not_floor -> tally only, no entry
+      EEE: L=95 A, E=90 A, R=35 B  -> qualifies, no risk_budget key at all (honest-NA caution path)
+    """
+    with Session(engine) as session:
+        run = _mk_run(session, date(2024, 3, 1))
+        _mk_result(session, run.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
+        _mk_result(session, run.id, "BBB", 88.0, "A", 78.0, "B", 45.0, "C")
+        _mk_result(session, run.id, "CCC", 77.0, "B", 55.0, "D", 50.0, "C")
+        _mk_result(session, run.id, "DDD", 30.0, "E", 20.0, "E", 90.0, "E")
+        _mk_result(session, run.id, "EEE", 95.0, "A", 90.0, "A", 35.0, "B", atr_value=None)
+        session.commit()
+        session.refresh(run)
+        return run.id
+
+
+# --- selection (J-04) ---------------------------------------------------------------------------
+
+
+def test_candidates_match_stored_scores_and_word_maps(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    by_ticker = {c["ticker"]: c for c in result["candidates"]}
+    assert set(by_ticker) == {"AAA", "BBB", "EEE"}
+    aaa = by_ticker["AAA"]
+    assert aaa["leadership_score"] == 92.0
+    assert aaa["leadership_word"] == cfg.compass.vocabulary.leadership_words["A"]
+    assert aaa["entry_word"] == cfg.compass.vocabulary.entry_words["B"]
+    assert aaa["risk_word"] == cfg.compass.vocabulary.risk_words["C"]
+    assert aaa["invalidation"] == "AAA invalidates below its 50-DMA (100.00)."
+
+
+def test_checklist_verdicts_reproduce_inclusion(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    for candidate in result["candidates"]:
+        assert all(row["verdict"] == "Pass" for row in candidate["checklist"])
+        assert {row["condition"] for row in candidate["checklist"]} == {
+            "leadership_min_score", "entry_min_score", "risk_max_score",
+        }
+        assert all(row["met"] is True for row in candidate["what_would_change"])
+
+
+def test_why_not_near_miss_has_failed_conditions_with_distance(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
+    assert "CCC" in why_not_by_ticker  # leadership 77 >= why_not_floor 75 -> near-miss, individually listed
+    failed = why_not_by_ticker["CCC"]["failed_conditions"]
+    assert any(f["condition"] == "entry_min_score" for f in failed)
+    entry_fail = next(f for f in failed if f["condition"] == "entry_min_score")
+    assert entry_fail["actual"] == 55.0
+    assert entry_fail["threshold"] == cfg.compass.selection.entry_min_score
+    assert entry_fail["distance"] == pytest.approx(cfg.compass.selection.entry_min_score - 55.0)
+    # DDD is far below why_not_floor -> counted in the tally, but NOT given an individual why-not entry
+    assert "DDD" not in why_not_by_ticker
+
+
+def test_disposition_tally_partitions_member_count_minus_candidates(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        member_count = len(session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all())
+        result = compass.evaluate_selection(session, run, cfg)
+    tally = result["disposition_tally"]
+    candidate_count = len(result["candidates"])
+    assert tally["below_selection_floor"] + tally["excluded_by_cap"] == member_count - candidate_count
+    assert tally["below_selection_floor"] == 2  # CCC, DDD
+    assert tally["excluded_by_cap"] == 0  # only 3 qualify, cap (10) never binds here
+
+
+def test_excluded_by_cap_get_empty_failed_conditions(engine, cfg, selection_run):
+    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
+    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, capped_cfg)
+    assert len(result["candidates"]) == 2
+    assert result["disposition_tally"]["excluded_by_cap"] == 1  # AAA/BBB/EEE qualify, cap keeps top 2
+    why_not_by_ticker = {w["ticker"]: w for w in result["why_not"]}
+    cut_ticker = ({"AAA", "BBB", "EEE"} - {c["ticker"] for c in result["candidates"]}).pop()
+    assert why_not_by_ticker[cut_ticker]["failed_conditions"] == []  # passed everything; only the cap cut it
+
+
+def test_candidates_empty_reason_when_nothing_qualifies(engine, cfg):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2024, 3, 8))
+        _mk_result(session, run.id, "ZZZ", 10.0, "E", 10.0, "E", 95.0, "E")
+        session.commit()
+        session.refresh(run)
+        result = compass.evaluate_selection(session, run, cfg)
+    assert result["candidates"] == []
+    assert isinstance(result["candidates_empty_reason"], str) and result["candidates_empty_reason"]
+
+
+def test_risk_off_regime_adds_caution_to_every_candidate(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        run.regime_label = "Risk-off"
+        session.add(run)
+        session.commit()
+        session.refresh(run)
+        result = compass.evaluate_selection(session, run, cfg)
+    assert len(result["candidates"]) == 3
+    for candidate in result["candidates"]:
+        assert any(c.startswith("REGIME_RISK_OFF") for c in candidate["cautions"])
+        assert not any("buy" in c.lower() or "sell" in c.lower() for c in candidate["cautions"])
+
+
+def test_missing_risk_budget_renders_honest_na_caution_never_crashes(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    eee = next(c for c in result["candidates"] if c["ticker"] == "EEE")
+    assert any("not available" in c for c in eee["cautions"])
+    assert any(c.startswith("ATR_RISK_BUDGET") for c in eee["cautions"])
+
+
+def test_no_composite_score_field_anywhere(engine, cfg, selection_run):
+    """AG-11: only the three existing scores/buckets (via word maps) may appear — no new blended number."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    allowed_numeric_keys = {"leadership_score", "entry_quality_score", "risk_score"}
+    for candidate in result["candidates"]:
+        numeric_keys = {k for k, v in candidate.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
+        assert numeric_keys <= allowed_numeric_keys, f"unexpected numeric field(s) on candidate: {numeric_keys - allowed_numeric_keys}"
+
+
+def test_shadow_cohort_never_appears_in_selection_payload(engine, cfg, selection_run):
+    """TC-20 / the shadow key is reserved (config only) but computes/renders nothing this iteration."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    serialized = json.dumps(result).lower()
+    assert "shadow" not in serialized
+
+
+# --- narrative (J-03) ---------------------------------------------------------------------------
+
+
+@pytest.fixture()
+def two_runs_with_phase(engine, cfg):
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 4, 1), regime_score=50.0)
+        run_b = _mk_run(session, date(2024, 4, 8), regime_score=58.0)
+        _mk_result(session, run_a.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
+        _mk_result(session, run_b.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        _seed_phase_cache(session, run_a.asof_date, available=True, severity=25.0, phase="Expansion", p_bear=0.10)
+        _seed_phase_cache(session, run_b.asof_date, available=True, severity=45.0, phase="Pullback", p_bear=0.35)
+        return run_a.id, run_b.id
+
+
+def test_state_sentence_facts_match_dashboard_and_market_phase(engine, cfg, two_runs_with_phase):
+    from app.engine.snapshot_serving import dashboard_payload
+
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_b = session.get(ScannerRun, run_b_id)
+        selection = compass.evaluate_selection(session, run_b, cfg)
+        narrative = compass.build_narrative(session, run_b, session.get(ScannerRun, run_a_id), selection, cfg)
+        phase_payload = market_phase_module.market_phase_cached(session, run_b.asof_date, cfg)
+        dashboard = dashboard_payload(run_b)
+
+    state = next(s for s in narrative["sentences"] if s["template_id"] == "state")
+    facts = {f["name"]: f["value"] for f in state["facts"]}
+    assert facts["regime_score"] == dashboard["regime"]["score"] == 58.0
+    assert facts["severity"] == phase_payload["severity"] == 45.0
+    assert "cautious" in state["text"] or "tense" in state["text"]  # p_bear 0.35 -> "tense" band
+
+
+def test_direction_no_prior_run_variant(engine, cfg, two_runs_with_phase):
+    run_a_id, _run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        selection = compass.evaluate_selection(session, run_a, cfg)
+        narrative = compass.build_narrative(session, run_a, None, selection, cfg)
+    direction = next(s for s in narrative["sentences"] if s["template_id"].startswith("direction"))
+    assert direction["template_id"] == "direction_no_prior_run"
+    assert "earliest" in direction["text"].lower()
+
+
+def test_direction_na_velocity_variant_when_phase_unavailable(engine, cfg):
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 5, 1))
+        run_b = _mk_run(session, date(2024, 5, 8))
+        _mk_result(session, run_b.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        # deliberately NO MarketPhaseCache row seeded -> market_phase_cached computes over an empty DB and
+        # must degrade to available=False (insufficient history), never crash
+        selection = compass.evaluate_selection(session, run_b, cfg)
+        narrative = compass.build_narrative(session, run_b, run_a, selection, cfg)
+    direction = next(s for s in narrative["sentences"] if s["template_id"].startswith("direction"))
+    assert direction["template_id"] == "direction_na_velocity"
+
+
+def test_focus_count_sentence_matches_candidate_count(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        selection = compass.evaluate_selection(session, run, cfg)
+        _seed_phase_cache(session, run.asof_date, available=False)
+        narrative = compass.build_narrative(session, run, None, selection, cfg)
+    focus = next(s for s in narrative["sentences"] if s["template_id"] == "focus_count")
+    facts = {f["name"]: f["value"] for f in focus["facts"]}
+    assert facts["candidate_count"] == len(selection["candidates"]) == 3
+    assert "3" in focus["text"]
+
+
+def test_banned_language_scan_raises_on_violation(cfg):
+    with pytest.raises(ValueError, match="banned language"):
+        compass._assert_no_banned_language(
+            [{"template_id": "x", "text": "You should buy this now.", "facts": []}], cfg
+        )
+
+
+def test_retrospective_stamp_appears_only_for_non_frontier_asof(engine, cfg, two_runs_with_phase):
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        selection_a = compass.evaluate_selection(session, run_a, cfg)
+        selection_b = compass.evaluate_selection(session, run_b, cfg)
+        narrative_a = compass.build_narrative(session, run_a, None, selection_a, cfg)  # run_a has a LATER run (run_b) -> retrospective
+        narrative_b = compass.build_narrative(session, run_b, run_a, selection_b, cfg)  # run_b IS the frontier -> not retrospective
+    assert any(s["template_id"] == "retrospective_stamp" for s in narrative_a["sentences"])
+    assert not any(s["template_id"] == "retrospective_stamp" for s in narrative_b["sentences"])
+
+
+# --- manifest assembly + storage -----------------------------------------------------------------
+
+
+def test_content_hash_stable_across_identical_rebuilds(engine, cfg, two_runs_with_phase):
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        first = compass.build_manifest_payload(session, run_b, run_a, cfg)
+        second = compass.build_manifest_payload(session, run_b, run_a, cfg)
+    assert first == second
+    assert first["content_hash"] == second["content_hash"]
+    assert first["narrative"]["sentences"] == second["narrative"]["sentences"]
+
+
+def test_get_or_create_manifest_computes_once_then_serves_from_storage(engine, cfg, two_runs_with_phase, monkeypatch):
+    run_a_id, run_b_id = two_runs_with_phase
+    calls = {"n": 0}
+    original = compass.build_manifest_payload
+
+    def counting_build(*args, **kwargs):
+        calls["n"] += 1
+        return original(*args, **kwargs)
+
+    monkeypatch.setattr(compass, "build_manifest_payload", counting_build)
+
+    with Session(engine) as session:
+        run_b = session.get(ScannerRun, run_b_id)
+        first_row = compass.get_or_create_manifest(session, run_b, cfg)
+        assert calls["n"] == 1
+        second_row = compass.get_or_create_manifest(session, run_b, cfg)
+        assert calls["n"] == 1  # TC-1: zero ADDITIONAL producer calls on the warm hit
+        assert first_row.id == second_row.id
+        assert first_row.content_hash == second_row.content_hash
+
+    with Session(engine) as session:
+        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 4, 8))).all()
+        assert len(rows) == 1  # never duplicated
+
+
+def test_manifest_row_payload_matches_build_manifest_payload_content(engine, cfg, two_runs_with_phase):
+    run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        built = compass.build_manifest_payload(session, run_b, run_a, cfg)
+        row = compass.get_or_create_manifest(session, run_b, cfg)
+        served = compass.manifest_row_payload(row)
+    assert served["session_delta"] == built["session_delta"]
+    assert served["narrative"] == built["narrative"]
+    assert served["selection"] == built["selection"]
+    assert served["content_hash"] == built["content_hash"]
+
+
+def test_missing_required_compass_config_key_fails_closed():
+    """A missing required `compass.*` key raises at config load, never silently falls back."""
+    from pydantic import ValidationError
+
+    from app.config import CompassSelectionCfg
+
+    with pytest.raises(ValidationError):
+        CompassSelectionCfg(rule_version="v1")  # missing every required threshold
+
+
+def test_no_network_or_lookahead_imports_in_compass_module():
+    """AG-9 (no live network call) + AG-5 (no lookahead) as a static guarantee over the module's actual
+    code (via ast, so docstring prose is never a false positive)."""
+    tree = ast.parse(open(compass.__file__).read())
+    banned = {"requests", "httpx", "urllib", "ForwardReturn", "forward_returns", "bars_after"}
+    offenders = set()
+    for node in ast.walk(tree):
... [diff_bound] apps/backend/tests/test_compass.py: 9 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_ingest_finalize_compass.py b/apps/backend/tests/test_ingest_finalize_compass.py
new file mode 100644
index 00000000..b9b4b96e
--- /dev/null
+++ b/apps/backend/tests/test_ingest_finalize_compass.py
@@ -0,0 +1,107 @@
+"""goal-market-compass iter-2 — the "compass content" finalize-tail phase in `_refresh_ingest_aggregates`
+(data_manager.py, inserted between the market-phase warm and the forward-aggregates phase).
+
+TC-31: a normal backfill still completes and every pre-existing "Refreshed:" phase still reports its
+prior counts unchanged. Also proves the new phase's own try/except isolation: a producer exception here
+is caught by ITS OWN handler and never blocks or crashes the rest of `_refresh_ingest_aggregates` (the
+same isolate-and-continue contract the market-phase loop already has).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlmodel import Session, select
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine import compass, data_manager
+from app.engine.data_manager import JobProgress
+from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun
+
+ASOF = date(2024, 7, 8)
+PRIOR_ASOF = date(2024, 7, 1)
+
+
+@pytest.fixture()
+def finalize_engine(tmp_path):
+    """Two `ScannerRun`s (so `session_delta` has a real prior session) each with one `ScannerResult`,
+    plus SPY bars so the market-phase / forward-aggregate phases can also run in the same pass."""
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_compass.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (PRIOR_ASOF, ASOF):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        for d, score in ((PRIOR_ASOF, 50.0), (ASOF, 55.0)):
+            run = ScannerRun(
+                asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+                regime_score=score, regime_label=cfg.regime.labels[0], regime_components_json="[]",
+                breadth_above_50dma=50.0, breadth_above_200dma=50.0,
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
+            session.commit()
+    return engine
+
+
+def _progress() -> JobProgress:
+    prog = JobProgress(job_id="finalize-compass-test", kind="backfill", start=PRIOR_ASOF, end=ASOF)
+    prog.dates_total = 1
+    prog.dates_done = 1
+    prog.new_snapshot_dates = [ASOF]  # only the LATEST date was "newly produced" this run
+    return prog
+
+
+def test_compass_content_phase_persists_manifest_and_reports_refreshed(finalize_engine):
+    cfg = load_config()
+    with Session(finalize_engine) as session:
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, _progress())
+    assert "next_session_manifest" in refreshed
+    assert "market_phase" in refreshed  # the pre-existing phase this one is inserted after still ran
+
+    with Session(finalize_engine) as session:
+        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == ASOF)).all()
+    assert len(rows) == 1
+    assert rows[0].content_hash
+
+
+def test_compass_content_failure_is_isolated_forward_aggregates_still_runs(finalize_engine, monkeypatch, caplog):
+    """The new phase's own try/except must catch a producer exception and continue the finalize tail —
+    it must NEVER block or crash the pre-existing forward-aggregates phase that runs right after it."""
+    def _boom(*args, **kwargs):
+        raise RuntimeError("synthetic compass-content failure")
+
+    monkeypatch.setattr(compass, "get_or_create_manifest", _boom)
+    cfg = load_config()
+    with caplog.at_level("ERROR"):
+        with Session(finalize_engine) as session:
+            refreshed = data_manager._refresh_ingest_aggregates(session, cfg, _progress())
+
+    assert "next_session_manifest" not in refreshed  # honestly NOT reported as refreshed -- it failed
+    assert "forward_aggregates" in refreshed  # the NEXT phase still ran -- isolation held
+    assert any("compass-content warm failed" in record.message for record in caplog.records)
+
+    with Session(finalize_engine) as session:
+        rows = session.exec(select(NextSessionManifest)).all()
+    assert rows == []  # no partial/corrupt row was written
+
+
+def test_compass_content_is_a_noop_when_no_new_snapshot_dates(finalize_engine):
+    """Mirrors the market-phase loop's own contract: an empty `new_snapshot_dates` (e.g. a re-run that
+    added no new date) means this phase does no work and is honestly omitted from `refreshed`."""
+    cfg = load_config()
+    prog = _progress()
+    prog.new_snapshot_dates = []
+    with Session(finalize_engine) as session:
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "next_session_manifest" not in refreshed
diff --git a/apps/backend/tests/test_session_delta.py b/apps/backend/tests/test_session_delta.py
new file mode 100644
index 00000000..263b3a14
--- /dev/null
+++ b/apps/backend/tests/test_session_delta.py
@@ -0,0 +1,318 @@
+"""app.engine.session_delta (goal-market-compass iter-2, J-02) — session-over-session change detection.
+
+File-scoped synthetic fixture (a fresh in-memory SQLite DB with hand-built `ScannerRun` /
+`ScannerResult` / `SectorScoreRow` / `ThemeScoreRow` rows) — never `loaded_engine` (the full 30y-basis
+fixture is a multi-hour cost this module's pure comparison logic does not need).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+
+import pytest
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.config import load_config
+from app.engine.session_delta import KIND_BREADTH, KIND_MARKET, KIND_SECTOR, KIND_STOCK, KIND_THEME, compute_delta, find_previous_run
+from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+def _mk_run(session: Session, asof: date, regime_score: float, b50, b200) -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof,
+        created_at=datetime.now(timezone.utc),
+        provider="seed",
+        benchmark="SPY",
+        regime_score=regime_score,
+        regime_label="Expansion",
+        regime_components_json="[]",
+        breadth_above_50dma=b50,
+        breadth_above_200dma=b200,
+        new_high_low_json="{}",
+        candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _mk_result(session: Session, run_id: int, ticker: str, score: float, bucket: str) -> None:
+    session.add(
+        ScannerResult(
+            run_id=run_id,
+            ticker=ticker,
+            name=ticker,
+            sector="Technology",
+            leadership_score=score,
+            leadership_bucket=bucket,
+            entry_quality_score=70.0,
+            entry_quality_bucket="B",
+            risk_score=40.0,
+            risk_bucket="C",
+            setup_status="Breakout-watch",
+            rank=1,
+            record_json=json.dumps({
+                "ticker": ticker,
+                "invalidation": {"basis": "50-DMA", "ma_period": 50, "level": 100.0, "price": 110.0, "note": f"{ticker} invalidation note"},
+                "risk_budget": {"atr_pct": {"value": 3.0, "percentile": 0.5}},
+            }),
+        )
+    )
+
+
+def _mk_sector(session: Session, run_id: int, ticker: str, name: str, rank: int) -> None:
+    session.add(
+        SectorScoreRow(
+            run_id=run_id, ticker=ticker, kind="sector", name=name, members_json="[]",
+            score=80.0, bucket="A", trend_label="Uptrend", components_json="{}", rank=rank,
+        )
+    )
+
+
+def _mk_theme(session: Session, run_id: int, slug: str, name: str, rank: int) -> None:
+    session.add(
+        ThemeScoreRow(
+            run_id=run_id, slug=slug, name=name, score=80.0, bucket="A",
+            members_json="[]", breadth_label="universe-relative", trend_label="Uptrend",
+            components_json="{}", rank=rank,
+        )
+    )
+
+
+@pytest.fixture()
+def two_runs(engine, cfg):
+    """run_a (earliest) -> run_b (7 days later) with hand-picked, KNOWN deltas:
+      market:  50 -> 58   (delta 8,  >= threshold 5  -> CHANGE)
+      breadth 50dma: 40 -> 44 (delta 4, <  threshold 5 -> SUPPRESSED)
+      breadth 200dma: 45 -> 52 (delta 7, >= threshold 5 -> CHANGE)
+      sector XLK: rank 1 -> 3 (delta 2, >= threshold 2 -> CHANGE)
+      sector XLF: rank 2 -> 2 (delta 0, <  threshold 2 -> SUPPRESSED)
+      sector XLE: rank 3 -> 1 (delta 2, >= threshold 2 -> CHANGE)
+      theme  ai:  rank 1 -> 3 (delta 2, >= threshold 2 -> CHANGE)
+      theme  ev:  rank 2 -> 1 (delta 1, <  threshold 2 -> SUPPRESSED)
+      stock AAPL: bucket C -> A, score 60 -> 85 (delta 25, >= threshold 8, bucket crossed -> CHANGE)
+      stock MSFT: bucket A -> A, score 90 -> 91 (unchanged bucket -> not reported at all)
+      stock NEWC: absent -> present, score 70, bucket C -> CHANGE (new-to-universe, unconditional)
+    """
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 1, 1), 50.0, 40.0, 45.0)
+        run_b = _mk_run(session, date(2024, 1, 8), 58.0, 44.0, 52.0)
+
+        _mk_sector(session, run_a.id, "XLK", "Technology", 1)
+        _mk_sector(session, run_a.id, "XLF", "Financials", 2)
+        _mk_sector(session, run_a.id, "XLE", "Energy", 3)
+        _mk_sector(session, run_b.id, "XLK", "Technology", 3)
+        _mk_sector(session, run_b.id, "XLF", "Financials", 2)
+        _mk_sector(session, run_b.id, "XLE", "Energy", 1)
+
+        _mk_theme(session, run_a.id, "ai", "Artificial Intelligence", 1)
+        _mk_theme(session, run_a.id, "ev", "Electric Vehicles", 2)
+        _mk_theme(session, run_b.id, "ai", "Artificial Intelligence", 3)
+        _mk_theme(session, run_b.id, "ev", "Electric Vehicles", 1)
+
+        _mk_result(session, run_a.id, "AAPL", 60.0, "C")
+        _mk_result(session, run_a.id, "MSFT", 90.0, "A")
+        _mk_result(session, run_b.id, "AAPL", 85.0, "A")
+        _mk_result(session, run_b.id, "MSFT", 91.0, "A")
+        _mk_result(session, run_b.id, "NEWC", 70.0, "C")
+
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        return run_a.id, run_b.id
+
+
+def _by_kind(changes: list[dict], kind: str) -> list[dict]:
+    return [c for c in changes if c["kind"] == kind]
+
+
+def test_no_prior_run_state_is_explicit(engine, cfg):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2024, 1, 1), 50.0, 40.0, 45.0)
+        session.commit()
+        session.refresh(run)
+        assert find_previous_run(session, run) is None
+        result = compute_delta(session, run, None, cfg)
+    assert result == {
+        "prior_as_of": None, "gap_days": None, "changes": [], "suppressed": [], "suppressed_count": 0,
+    }
+
+
+def test_prior_as_of_and_gap_days_match_immediately_preceding_run(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        assert find_previous_run(session, run_b).id == run_a_id
+        result = compute_delta(session, run_b, run_a, cfg)
+    assert result["prior_as_of"] == "2024-01-01"
+    assert result["gap_days"] == 7
+
+
+def test_changes_ordered_market_breadth_sector_theme_stock(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    kinds_seen = [c["kind"] for c in result["changes"]]
+    expected_order = [KIND_MARKET, KIND_BREADTH, KIND_SECTOR, KIND_THEME, KIND_STOCK]
+    # every kind present must appear in this relative order (some kinds may be entirely absent)
+    positions = [expected_order.index(k) for k in kinds_seen]
+    assert positions == sorted(positions)
+
+
+def test_market_change_matches_hand_picked_delta(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    market = _by_kind(result["changes"], KIND_MARKET)
+    assert len(market) == 1
+    assert market[0]["from"] == 50.0 and market[0]["to"] == 58.0
+    assert market[0]["magnitude"] == pytest.approx(8.0)
+    assert market[0]["drill_href"] == "/?asof=2024-01-08"
+
+
+def test_breadth_below_threshold_is_suppressed_not_dropped(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    breadth_changes = _by_kind(result["changes"], KIND_BREADTH)
+    assert len(breadth_changes) == 1
+    assert breadth_changes[0]["label"] == "Breadth above 200-DMA"
+    suppressed_breadth = [s for s in result["suppressed"] if s["kind"] == KIND_BREADTH]
+    assert len(suppressed_breadth) == 1
+    assert suppressed_breadth[0]["magnitude"] == pytest.approx(4.0)
+    assert result["suppressed_count"] == len(result["suppressed"])
+
+
+def test_sector_rank_moves_match_stored_ranks_both_dates(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+        # independently re-read the stored rank rows the same way GET /api/sectors would
+        stored_a = {t: r for t, r in session.exec(select(SectorScoreRow.ticker, SectorScoreRow.rank).where(SectorScoreRow.run_id == run_a_id))}
+        stored_b = {t: r for t, r in session.exec(select(SectorScoreRow.ticker, SectorScoreRow.rank).where(SectorScoreRow.run_id == run_b_id))}
+    sector_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_SECTOR)}
+    assert sector_changes["Technology"]["from"] == stored_a["XLK"] == 1
+    assert sector_changes["Technology"]["to"] == stored_b["XLK"] == 3
+    assert sector_changes["Energy"]["from"] == stored_a["XLE"] == 3
+    assert sector_changes["Energy"]["to"] == stored_b["XLE"] == 1
+    # XLF (unchanged rank) must not appear as a change
+    assert "Financials" not in sector_changes
+    suppressed_sector = [s for s in result["suppressed"] if s["kind"] == KIND_SECTOR]
+    assert len(suppressed_sector) == 1
+    assert suppressed_sector[0]["magnitude"] == 0.0
+
+
+def test_theme_rank_move_reported(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    theme_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_THEME)}
+    assert theme_changes["Artificial Intelligence"]["from"] == 1
+    assert theme_changes["Artificial Intelligence"]["to"] == 3
+    assert "Electric Vehicles" not in theme_changes  # delta 1 < threshold 2 -> suppressed
+
+
+def test_stock_bucket_crossing_matches_leaderboard_values(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    stock_changes = {c["label"]: c for c in _by_kind(result["changes"], KIND_STOCK)}
+    assert stock_changes["AAPL leadership bucket"]["from"] == "C"
+    assert stock_changes["AAPL leadership bucket"]["to"] == "A"
+    assert stock_changes["AAPL leadership bucket"]["drill_href"] == "/stocks/AAPL?asof=2024-01-08"
+    # MSFT's bucket did not cross (A -> A) -- must not appear as a change, even though its score moved
+    assert "MSFT leadership bucket" not in stock_changes
+
+
+def test_new_to_universe_reported_distinctly_never_as_score_change(engine, cfg, two_runs):
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        result = compute_delta(session, run_b, run_a, cfg)
+    new_entries = [c for c in _by_kind(result["changes"], KIND_STOCK) if c["from"] == "new"]
+    assert len(new_entries) == 1
+    assert new_entries[0]["label"] == "NEWC new to universe"
+    assert new_entries[0]["to"] == "C"  # the bucket, not a "from bucket -> to bucket" score-change framing
+
+
+def test_quiet_pair_yields_no_changes_but_nonzero_suppressed(engine, cfg):
+    with Session(engine) as session:
+        run_a = _mk_run(session, date(2024, 2, 1), 50.0, 40.0, 45.0)
+        run_b = _mk_run(session, date(2024, 2, 8), 50.5, 40.5, 45.5)  # every delta well under threshold
+        _mk_sector(session, run_a.id, "XLK", "Technology", 1)
+        _mk_sector(session, run_b.id, "XLK", "Technology", 1)
+        session.commit()
+        session.refresh(run_a)
+        session.refresh(run_b)
+        result = compute_delta(session, run_b, run_a, cfg)
+    assert result["changes"] == []
+    assert result["suppressed_count"] > 0
+    assert result["suppressed_count"] == len(result["suppressed"])
+
+
+def test_column_projected_reads_only_no_full_record_json_sweep(engine, cfg, two_runs, monkeypatch):
+    """AG-8: the delta producer must never deserialize `record_json` — it reads typed columns only."""
+    import app.engine.session_delta as sd
+
+    original_exec = Session.exec
+
+    def _guarded_exec(self, statement, *args, **kwargs):
+        compiled = str(statement)
+        assert "record_json" not in compiled, f"session_delta issued a record_json-touching query: {compiled}"
+        return original_exec(self, statement, *args, **kwargs)
+
+    monkeypatch.setattr(Session, "exec", _guarded_exec)
+    run_a_id, run_b_id = two_runs
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        run_b = session.get(ScannerRun, run_b_id)
+        sd.compute_delta(session, run_b, run_a, cfg)
+
+
+def test_no_forward_returns_or_lookahead_import(engine, cfg):
+    """AG-5: static guarantee that the producer module's CODE (not its prose comments) never names
+    `ForwardReturn` / `forward_returns` / a bars-after accessor — it compares two already-stored runs
+    only. Parsed via `ast` so this scans identifiers actually used by the code, not docstring prose."""
+    import ast
+
+    import app.engine.session_delta as sd
+
+    tree = ast.parse(open(sd.__file__).read())
+    banned = {"ForwardReturn", "forward_returns", "bars_after"}
+    offenders = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Name) and node.id in banned:
+            offenders.add(node.id)
+        if isinstance(node, ast.Attribute) and node.attr in banned:
+            offenders.add(node.attr)
+        if isinstance(node, (ast.Import, ast.ImportFrom)):
+            for alias in node.names:
+                if alias.name in banned:
+                    offenders.add(alias.name)
+    assert not offenders, f"session_delta.py's code references banned lookahead identifiers: {offenders}"
diff --git a/apps/frontend/components/compass-focus-section.tsx b/apps/frontend/components/compass-focus-section.tsx
new file mode 100644
index 00000000..457e5792
--- /dev/null
+++ b/apps/frontend/components/compass-focus-section.tsx
@@ -0,0 +1,181 @@
+"use client";
+
+import { AlertTriangle } from "lucide-react";
+
+import { Badge } from "@/components/ui/badge";
+import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
+import { Disclosure } from "@/components/ui/disclosure";
+import type { ChecklistVerdict, CompassCandidate, CompassResponse, WhyNotEntry } from "@/lib/api";
+
+const VERDICT_VARIANT: Record<ChecklistVerdict, "ok" | "danger" | "default" | "warn"> = {
+  Pass: "ok",
+  Miss: "danger",
+  Supportive: "ok",
+  Neutral: "default",
+  Unknown: "warn",
+  NA: "default",
+};
+
+/** One next-session candidate card. Every field — the words, the reasons, the cautions, the
+ *  checklist verdicts, and the "what would change this" rows — is rendered VERBATIM from the
+ *  served `CompassCandidate`. No rule table or threshold lives in this file (TC-18): the checklist
+ *  and what-would-change rows map only over served `condition`/`threshold`/`actual`/`verdict`/`met`
+ *  fields. */
+function CandidateCard({ candidate }: { candidate: CompassCandidate }) {
+  return (
+    <Card className="space-y-3 p-4" data-testid={`compass-candidate-${candidate.ticker}`}>
+      <h3 className="num text-base font-semibold text-text">{candidate.ticker}</h3>
+
+      <div className="grid gap-2 text-xs sm:grid-cols-3">
+        <div>
+          <p className="uppercase tracking-wide text-text-faint">Leadership</p>
+          <p className="text-text">
+            {candidate.leadership_word}{" "}
+            <span className="num text-text-muted">({candidate.leadership_score.toFixed(1)})</span>
+          </p>
+        </div>
+        <div>
+          <p className="uppercase tracking-wide text-text-faint">Entry</p>
+          <p className="text-text">
+            {candidate.entry_word}{" "}
+            <span className="num text-text-muted">({candidate.entry_quality_score.toFixed(1)})</span>
+          </p>
+        </div>
+        <div>
+          <p className="uppercase tracking-wide text-text-faint">Risk</p>
+          <p className="text-text">
+            {candidate.risk_word}{" "}
+            <span className="num text-text-muted">({candidate.risk_score.toFixed(1)})</span>
+          </p>
+        </div>
+      </div>
+
+      <div className="space-y-1">
+        <p className="text-xs uppercase tracking-wide text-text-faint">Why</p>
+        <ul className="space-y-0.5 text-xs text-text-muted">
+          {candidate.reasons.map((reason, index) => (
+            <li key={index}>{reason}</li>
+          ))}
+        </ul>
+      </div>
+
+      {candidate.cautions.length > 0 ? (
+        <div className="space-y-1">
+          <p className="text-xs uppercase tracking-wide text-warn">Cautions</p>
+          <ul className="space-y-0.5 text-xs text-warn">
+            {candidate.cautions.map((caution, index) => (
+              <li key={index}>{caution}</li>
+            ))}
+          </ul>
+        </div>
+      ) : null}
+
+      <Disclosure summary="Eligibility checklist">
+        <ul className="space-y-1 pt-1">
+          {candidate.checklist.map((row, index) => (
+            <li key={index} className="flex items-center justify-between gap-2 text-xs">
+              <span className="text-text-muted">{row.condition}</span>
+              <span className="flex items-center gap-2">
+                <span className="num text-text-faint">
+                  {row.actual.toFixed(1)} vs {row.threshold.toFixed(1)}
+                </span>
+                <Badge variant={VERDICT_VARIANT[row.verdict]}>{row.verdict}</Badge>
+              </span>
+            </li>
+          ))}
+        </ul>
+      </Disclosure>
+
+      <Disclosure summary="What would change this">
+        <ul className="space-y-1 pt-1">
+          {candidate.what_would_change.map((row, index) => (
+            <li key={index} className="flex items-center justify-between gap-2 text-xs text-text-muted">
+              <span>{row.condition}</span>
+              <span className="num">
+                {row.actual.toFixed(1)} vs {row.threshold.toFixed(1)} — {row.met ? "met" : "not met"}
+              </span>
+            </li>
+          ))}
+        </ul>
+      </Disclosure>
+
+      <p className="text-xs text-text-faint">
+        <span className="uppercase tracking-wide">Invalidation: </span>
+        {candidate.invalidation}
+      </p>
+    </Card>
+  );
+}
+
+function WhyNotList({ entries }: { entries: WhyNotEntry[] }) {
+  if (entries.length === 0) {
+    return <p className="pt-1 text-xs text-text-faint">No near-miss names this session.</p>;
+  }
+  return (
+    <ul className="space-y-2 pt-1">
+      {entries.map((entry) => (
+        <li key={entry.ticker} className="text-xs" data-testid={`compass-why-not-${entry.ticker}`}>
+          <span className="num font-medium text-text">{entry.ticker}</span>
+          {entry.failed_conditions.length === 0 ? (
+            <span className="text-text-muted"> — passed every qualifier, cut only by the focus-list cap.</span>
+          ) : (
+            <ul className="ml-3 mt-0.5 space-y-0.5 text-text-muted">
+              {entry.failed_conditions.map((failed, index) => (
+                <li key={index}>
+                  {failed.condition}: {failed.actual.toFixed(1)} vs {failed.threshold.toFixed(1)} (distance{" "}
+                  {failed.distance.toFixed(1)})
+                </li>
+              ))}
+            </ul>
+          )}
+        </li>
+      ))}
+    </ul>
+  );
+}
+
+/** J-04 (goal-market-compass iter-2): the Next-session focus section. The candidate set, its
+ *  reasons/cautions/checklist, and the why-not list are all slices of the ONE served
+ *  `compass.evaluate_selection` trace (`GET /api/compass`'s `selection` block) — this component
+ *  re-renders served structures and implements no rule. Framed as "worth monitoring next session",
+ *  never as advice (anti-goal AG-2); the near-threshold shadow cohort (J-05/J-06) has no field in
+ *  this payload and so cannot appear here. */
+export function CompassFocusSection({ compass }: { compass: CompassResponse | null }) {
+  if (compass === null) {
+    return (
+      <Card
+        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
+        data-testid="compass-focus-unavailable"
+      >
+        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
+        Next-session focus is unavailable — backend not reachable.
+      </Card>
+    );
+  }
+
+  const { selection } = compass;
+
+  return (
+    <Card data-testid="compass-focus-section">
+      <CardHeader>
+        <CardTitle>Next-session focus</CardTitle>
+      </CardHeader>
+      <CardContent className="space-y-4">
+        {selection.candidates.length === 0 ? (
+          <p className="text-sm text-text-muted" data-testid="compass-focus-empty">
+            {selection.candidates_empty_reason ?? "No names clear the focus bar this session."}
+          </p>
+        ) : (
+          <div className="grid gap-3 md:grid-cols-2" data-testid="compass-candidate-list">
+            {selection.candidates.map((candidate) => (
+              <CandidateCard key={candidate.ticker} candidate={candidate} />
+            ))}
+          </div>
+        )}
+        <Disclosure summary={`Not priority (${selection.why_not.length})`}>
+          <WhyNotList entries={selection.why_not} />
+        </Disclosure>
+      </CardContent>
+    </Card>
+  );
+}
diff --git a/apps/frontend/components/compass-summary-card.tsx b/apps/frontend/components/compass-summary-card.tsx
new file mode 100644
index 00000000..b7b32b10
--- /dev/null
+++ b/apps/frontend/components/compass-summary-card.tsx
@@ -0,0 +1,65 @@
+"use client";
+
+import { AlertTriangle } from "lucide-react";
+
+import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
+import { Disclosure } from "@/components/ui/disclosure";
+import type { CompassResponse } from "@/lib/api";
+
+/** J-03 (goal-market-compass iter-2): the plain-English summary card. Every sentence is rendered
+ *  VERBATIM from `GET /api/compass`'s `narrative.sentences` — the frontend assembles no wording,
+ *  selects no word, and evaluates no threshold; it only re-displays served text plus its cited
+ *  facts (single source of truth — no client-composed wording). */
+export function CompassSummaryCard({ compass }: { compass: CompassResponse | null }) {
+  if (compass === null) {
+    return (
+      <Card
+        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
+        data-testid="compass-summary-unavailable"
+      >
+        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
+        Summary is unavailable — backend not reachable.
+      </Card>
+    );
+  }
+
+  const { sentences } = compass.narrative;
+
+  return (
+    <Card data-testid="compass-summary-card">
+      <CardHeader>
+        <CardTitle>Summary</CardTitle>
+      </CardHeader>
+      <CardContent className="space-y-3">
+        <div className="space-y-1.5 text-sm text-text">
+          {sentences.map((sentence) => (
+            <p key={sentence.template_id} data-testid={`compass-sentence-${sentence.template_id}`}>
+              {sentence.text}
+            </p>
+          ))}
+        </div>
+        <Disclosure summary="Show cited facts">
+          <ul className="space-y-2 pt-1">
+            {sentences.map((sentence) => (
+              <li key={sentence.template_id} className="text-xs text-text-muted">
+                <span className="font-medium text-text">{sentence.template_id}</span>
+                {sentence.facts.length === 0 ? (
+                  <span className="text-text-faint"> — no cited facts.</span>
+                ) : (
+                  <ul className="ml-3 mt-0.5 space-y-0.5">
+                    {sentence.facts.map((fact) => (
+                      <li key={fact.name} className="flex items-center gap-2">
+                        <span className="text-text-faint">{fact.name}:</span>
+                        <span className="num text-text">{String(fact.value)}</span>
+                      </li>
+                    ))}
+                  </ul>
+                )}
+              </li>
+            ))}
+          </ul>
+        </Disclosure>
+      </CardContent>
+    </Card>
+  );
+}
diff --git a/apps/frontend/components/compass-whatchanged-card.tsx b/apps/frontend/components/compass-whatchanged-card.tsx
new file mode 100644
index 00000000..c038f73b
--- /dev/null
+++ b/apps/frontend/components/compass-whatchanged-card.tsx
@@ -0,0 +1,95 @@
+"use client";
+
+import { AlertTriangle } from "lucide-react";
+import Link from "next/link";
+
+import { Badge } from "@/components/ui/badge";
+import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
+import { Disclosure } from "@/components/ui/disclosure";
+import { formatIsoDate } from "@/lib/dates";
+import type { CompassResponse, SessionDeltaChange } from "@/lib/api";
+
+const KIND_LABEL: Record<SessionDeltaChange["kind"], string> = {
+  market: "Market",
+  breadth: "Breadth",
+  sector: "Sector",
+  theme: "Theme",
+  stock: "Stock",
+};
+
+/** J-02 (goal-market-compass iter-2): the What-changed card. Every entry, its ordering, and its
+ *  threshold gate are all decided server-side (`app.engine.session_delta`) — this component only
+ *  re-displays the served `session_delta` block; it computes no threshold and no diff. */
+export function CompassWhatChangedCard({ compass }: { compass: CompassResponse | null }) {
+  if (compass === null) {
+    return (
+      <Card
+        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
+        data-testid="compass-whatchanged-unavailable"
+      >
+        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
+        What-changed is unavailable — backend not reachable.
+      </Card>
+    );
+  }
+
+  const { session_delta } = compass;
+  const noPriorRun = session_delta.prior_as_of === null;
+
+  return (
+    <Card data-testid="compass-whatchanged-card">
+      <CardHeader className="flex-row items-center justify-between space-y-0">
+        <CardTitle>What changed</CardTitle>
+        {!noPriorRun ? (
+          <span className="text-xs text-text-muted" data-testid="compass-whatchanged-prior">
+            vs {formatIsoDate(session_delta.prior_as_of)} ({session_delta.gap_days}{" "}
+            day{session_delta.gap_days === 1 ? "" : "s"} ago)
+          </span>
+        ) : null}
+      </CardHeader>
+      <CardContent className="space-y-3">
+        {noPriorRun ? (
+          <p className="text-sm text-text-muted" data-testid="compass-whatchanged-no-prior">
+            This is the earliest stored session — there is no prior session to compare against.
+          </p>
+        ) : session_delta.changes.length === 0 ? (
+          <p className="text-sm text-text-muted" data-testid="compass-whatchanged-quiet">
+            No meaningful changes this session.
+          </p>
+        ) : (
+          <ul className="space-y-2" data-testid="compass-whatchanged-list">
+            {session_delta.changes.map((change, index) => (
+              <li key={`${change.kind}-${index}`} className="flex items-start justify-between gap-3 text-sm">
+                <span className="flex flex-wrap items-center gap-2">
+                  <Badge variant="default">{KIND_LABEL[change.kind]}</Badge>
+                  <Link href={change.drill_href} className="text-text hover:underline">
+                    {change.label}
+                  </Link>
+                </span>
+                <span className="num shrink-0 text-xs text-text-muted">
+                  {String(change.from)} &rarr; {String(change.to)}
+                </span>
+              </li>
+            ))}
+          </ul>
+        )}
+        <Disclosure summary={`Suppressed moves (${session_delta.suppressed_count})`}>
+          {session_delta.suppressed.length === 0 ? (
+            <p className="pt-1 text-xs text-text-faint">No moves were suppressed this session.</p>
+          ) : (
+            <ul className="space-y-1 pt-1" data-testid="compass-suppressed-list">
+              {session_delta.suppressed.map((entry, index) => (
+                <li key={index} className="flex items-center justify-between gap-2 text-xs text-text-muted">
+                  <span>{KIND_LABEL[entry.kind as SessionDeltaChange["kind"]] ?? entry.kind}</span>
+                  <span className="num">
+                    {entry.magnitude.toFixed(2)} &lt; {entry.threshold.toFixed(2)}
+                  </span>
+                </li>
+              ))}
+            </ul>
+          )}
+        </Disclosure>
+      </CardContent>
+    </Card>
+  );
+}
diff --git a/apps/frontend/components/ui/disclosure.tsx b/apps/frontend/components/ui/disclosure.tsx
new file mode 100644
index 00000000..02a5f5a4
--- /dev/null
+++ b/apps/frontend/components/ui/disclosure.tsx
@@ -0,0 +1,28 @@
+"use client";
+
+import { ChevronDown } from "lucide-react";
+
+import { cn } from "@/lib/utils";
+
+/** A lightweight inline disclosure (native `<details>`) — keeps a figure's named breakdown REACHABLE
+ *  (one click) without crowding the surrounding summary. Pure presentation, no business logic.
+ *
+ *  Extracted from the Dashboard page (J-98) so the goal-market-compass iter-2 "Show cited facts" and
+ *  "suppressed moves" disclosures reuse the SAME component rather than a third hand-copied `<details>`
+ *  block. */
+export function Disclosure({ summary, children }: { summary: string; children: React.ReactNode }) {
+  return (
+    <details className="group rounded border border-border bg-surface-2/40">
+      <summary
+        className={cn(
+          "flex cursor-pointer list-none items-center justify-between gap-2 px-2.5 py-1.5 text-xs text-text-muted",
+          "transition-colors hover:text-text focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
+        )}
+      >
+        {summary}
+        <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" aria-hidden />
+      </summary>
+      <div className="border-t border-border px-2.5 pb-2.5">{children}</div>
+    </details>
+  );
+}
```
