# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 16. Shown in full: 16.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/phase-goal-market-compass-iter-1-demo.json               | 2 +-
 runs/goal-session-market-compass/telemetry.jsonl                 | 6 ++++++
 runs/goal-session-market-compass/trace/.next-step                | 2 +-
 runs/goal-session-market-compass/trace/trace.jsonl               | 1 +
 runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl | 6 ++++++
 5 files changed, 15 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
