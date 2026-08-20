# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 15. Shown in full: 14.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/compass.py` (514 lines not shown)

```diff
diff --git a/.gitignore b/.gitignore
index 99e8cf6d..85dfa74c 100644
--- a/.gitignore
+++ b/.gitignore
@@ -76,6 +76,13 @@ htmlcov/
 # Anchored with a leading slash so apps/backend/data/ is unaffected.
 /data/
 
+# goal-market-compass iter-3 (J-05/J-06): the at-ingest-mode next-session-manifest export writer's
+# target dir (config.yaml compass.manifest.export_dir) — a LOCAL JSON artifact directory regenerated
+# from stored manifest rows on every freeze (never hand-edited, never a repo artifact), the SAME
+# never-commit posture as the DB file itself. Test runs that omit TRENDORA_COMPASS_EXPORT_DIR also
+# write here — ephemeral either way.
+apps/backend/data/exports/
+
 # Goal-mode interactive pump transient logs
 runs/goal-session-*/pump-launch.out
 
diff --git a/apps/backend/app/api/compass.py b/apps/backend/app/api/compass.py
index f57de130..40b818b7 100644
--- a/apps/backend/app/api/compass.py
+++ b/apps/backend/app/api/compass.py
@@ -1,26 +1,87 @@
-"""GET /api/compass — the next-session manifest CONTENT block (goal-market-compass iter-2, J-02/J-03/
-J-04). Serves the stored `NextSessionManifest` row for the resolved `as_of`, computing + persisting it
-ONCE if absent (create-once-on-GET — zero producer calls on a warm hit, TC-1) and serving from storage
-on every subsequent hit for that `as_of`. Reuses `snapshot_serving`'s as-of error mapping so a requested
-`as_of` with no stored run returns the SAME honest error shape every other as-of-aware endpoint does —
-never a fabricated payload.
+"""GET /api/compass — the next-session manifest (goal-market-compass iter-2, J-02/J-03/J-04 CONTENT
+block; iter-3, J-05/J-06 freeze/integrity block). Serves the LATEST stored `NextSessionManifest` version
+for the resolved `as_of`, computing + persisting version 1 ONCE if absent (create-once — TC-1: zero
+producer calls on a warm hit) and serving from storage on every subsequent hit for that `as_of`. Reuses
+`snapshot_serving`'s as-of error mapping so a requested `as_of` with no stored run returns the SAME
+honest error shape every other as-of-aware endpoint does — never a fabricated payload.
+
+`POST /api/compass/regenerate` (iter-3) is an ACTION route, not a second read path — `GET /api/compass`
+remains the sole READ endpoint. It is confirm-gated (`confirm=true` required) and mints a NEW version for
+an as_of that already has a manifest; it never mints a first version (that stays `GET`'s / the ingest
+finalize hook's job).
 """
 from __future__ import annotations
 
+import json
 from typing import Optional
 
-from fastapi import APIRouter, Depends
+from fastapi import APIRouter, Depends, HTTPException
 from sqlmodel import Session
 
 from app.db import get_session
-from app.engine.compass import get_or_create_manifest, manifest_row_payload
-from app.engine.snapshot_serving import resolved_run
+from app.engine.compass import (
+    ManifestNotFoundError,
+    ManifestNotYetFrozen,
+    basis_disclosure,
+    get_or_create_manifest,
+    list_manifest_versions,
+    manifest_row_payload,
+    regenerate_manifest,
+)
+from app.engine.snapshot_serving import resolved_date, resolved_run
 
 router = APIRouter(tags=["compass"])
 
 
+def _read_time_additions(session: Session, row) -> dict:  # noqa: ANN001 -- NextSessionManifest, avoids an import cycle w/ typing-only use
+    """The read-time-only `basis` + `versions` fields BOTH routes attach on top of `manifest_row_payload`'s
+    pure reconstruction -- never part of what `manifest_hash` covers (TC-4/TC-22 verification must strip
+    these first). Factored out so GET and the regenerate action serve the IDENTICAL shape (a caller that
+    stores either response as `CompassResponse` never hits a missing-field crash)."""
+    versions = list_manifest_versions(session, row.as_of)
+    return {
+        "basis": basis_disclosure(session, row),
+        "versions": [
+            {
+                "version": v.version, "mode": v.mode, "frozen": v.frozen,
+                "prospective_eligible": v.prospective_eligible,
+                "generated_at": (
+                    json.loads(v.generation_json).get("generated_at") if v.generation_json else None
+                ),
+            }
+            for v in versions
+        ],
+    }
+
+
 @router.get("/compass")
 def compass(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
     run = resolved_run(session, as_of)
-    row = get_or_create_manifest(session, run)
-    return manifest_row_payload(row)
+    try:
+        row = get_or_create_manifest(session, run)
+    except ManifestNotYetFrozen as exc:
+        # J-05 step 7 / TC-8: the CURRENT frontier's manifest is minted only by the ingest finalize
+        # freeze or an explicit regenerate -- a plain GET never mints it. Honest 404, never a
+        # fabricated payload; the frontend's existing compass-card "unavailable" states degrade
+        # gracefully on any non-2xx (J-07's dedicated "not yet frozen" UI treatment is out of scope
+        # this iteration).
+        raise HTTPException(status_code=404, detail=str(exc)) from exc
+    payload = manifest_row_payload(row)
+    payload.update(_read_time_additions(session, row))
+    return payload
+
+
+@router.post("/compass/regenerate")
+def compass_regenerate(
+    as_of: str, confirm: bool = False, session: Session = Depends(get_session),
+) -> dict:
+    if not confirm:
+        raise HTTPException(status_code=400, detail="regenerate requires confirm=true — no row was created")
+    resolved = resolved_date(session, as_of)  # honest as-of resolution error mapping, reused verbatim
+    try:
+        row = regenerate_manifest(session, resolved)
+    except ManifestNotFoundError as exc:
+        raise HTTPException(status_code=404, detail=str(exc)) from exc
+    payload = manifest_row_payload(row)
+    payload.update(_read_time_additions(session, row))
+    return payload
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 8f3d43a4..3b3a7679 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -2669,16 +2669,52 @@ class CompassVocabularyCfg(BaseModel):
         return self
 
 
+class CompassManifestCfg(BaseModel):
+    """goal-market-compass iter-3 (J-05/J-06) — the next-session manifest freeze/export tunables.
+    `schema_version` is versioned in lockstep with the committed JSON Schema file at `schema_path` (a
+    schema change is always a NEW versioned file, never an in-place edit). `export_dir` is where the
+    at-ingest-mode export writer places the byte-identical JSON artifact (a `TRENDORA_COMPASS_EXPORT_DIR`
+    env override exists for tests — name only, never a value in files). `availability_margin_seconds` is
+    a conservative PUBLICATION-LATENCY allowance added to the canonical-serialization instant to compute
+    `available_at_utc` — never a research threshold; tuning it from outcomes is forbidden like any other
+    threshold (AG-15)."""
+
+    model_config = ConfigDict(extra="allow")
+    schema_version: str
+    export_dir: str
+    availability_margin_seconds: int = 60
+    schema_path: str
+
+    @model_validator(mode="after")
+    def _validate(self) -> "CompassManifestCfg":
+        if self.availability_margin_seconds < 0:
+            raise ValueError("compass.manifest.availability_margin_seconds must be >= 0")
+        return self
+
+
+def _default_compass_manifest() -> "CompassManifestCfg":
+    """The built-in default `compass.manifest` config — used when a config predating this block (or an
+    inline test fixture) omits it. The real `config.yaml` restates it explicitly as the single documented
+    source."""
+    return CompassManifestCfg(
+        schema_version="v1",
+        export_dir="apps/backend/data/exports/next_session_manifests",
+        availability_margin_seconds=60,
+        schema_path="docs/handoffs/trendora-next-session-manifest-v1.schema.json",
+    )
+
+
 class CompassCfg(BaseModel):
-    """goal-market-compass iter-2 (J-02/J-03/J-04) — the Today-page decision-surface config consumed by
-    `app.engine.session_delta` and `app.engine.compass`. Default-populated so a config / inline test
-    fixture predating this block still loads unchanged; the real `config.yaml` restates it explicitly as
-    the single documented source (see `_default_compass`)."""
+    """goal-market-compass iter-2/iter-3 (J-02/J-03/J-04/J-05/J-06) — the Today-page decision-surface
+    config consumed by `app.engine.session_delta` and `app.engine.compass`. Default-populated so a config
+    / inline test fixture predating this block still loads unchanged; the real `config.yaml` restates it
+    explicitly as the single documented source (see `_default_compass`)."""
 
     model_config = ConfigDict(extra="allow")
     delta: CompassDeltaCfg
     selection: CompassSelectionCfg
     vocabulary: CompassVocabularyCfg
+    manifest: CompassManifestCfg = Field(default_factory=_default_compass_manifest)
 
 
 def _default_compass() -> "CompassCfg":
@@ -2734,6 +2770,32 @@ def _default_compass() -> "CompassCfg":
     )
 
 
+class ProvenanceCfg(BaseModel):
+    """goal-market-compass iter-3 (J-05/J-06) — the engine-identity stamp's own inputs:
+    `engine_files` (repo-root-relative paths whose CONTENT is hashed) and `config_keys` (dotted config
+    paths whose VALUES are hashed) — see `app.engine.engine_identity.compute_engine_identity`. Both are
+    the single documented source for what the identity stamp is sensitive to; changing either list is
+    itself an engine-identity-affecting change."""
+
+    model_config = ConfigDict(extra="allow")
+    engine_files: list[str] = Field(min_length=1)
+    config_keys: list[str] = Field(min_length=1)
+
+
+def _default_provenance() -> "ProvenanceCfg":
+    """The built-in default `provenance` config — used when a config predating this block (or an inline
+    test fixture) omits it. The real `config.yaml` restates it explicitly as the single documented
+    source."""
+    return ProvenanceCfg(
+        engine_files=[
+            "apps/backend/app/engine/compass.py",
+            "apps/backend/app/engine/session_delta.py",
+            "apps/backend/app/engine/engine_identity.py",
+        ],
+        config_keys=["compass.selection", "compass.delta", "compass.manifest"],
+    )
+
+
 class Config(BaseModel):
     """Validated view of config.yaml. Only the iter-1-consumed sections are typed/validated;
     scaffolded sections ride along via extra="allow" so they can be tuned without code edits."""
@@ -2803,6 +2865,11 @@ class Config(BaseModel):
     # test fixture predating this block still loads unchanged; the real `config.yaml` restates it
     # explicitly as the single documented source.
     compass: CompassCfg = Field(default_factory=_default_compass)
+    # goal-market-compass iter-3 (J-05/J-06) — the engine-identity stamp's inputs (which files' content +
+    # which config subset feed `app.engine.engine_identity.compute_engine_identity`). Default-populated so
+    # a config / inline test fixture predating this block still loads unchanged; the real `config.yaml`
+    # restates it explicitly as the single documented source.
+    provenance: ProvenanceCfg = Field(default_factory=_default_provenance)
 
     @field_validator("themes")
     @classmethod
diff --git a/apps/backend/app/db.py b/apps/backend/app/db.py
index 31aea2e0..7490bd1a 100644
--- a/apps/backend/app/db.py
+++ b/apps/backend/app/db.py
@@ -129,6 +129,38 @@ _ADDITIVE_COLUMNS: tuple[tuple[str, str, str], ...] = (
     # rebuild repopulates them (mirrors the max_drawdown / J-86 precedent directly above).
     ("forward_returns", "underwater_days", "ALTER TABLE forward_returns ADD COLUMN underwater_days INTEGER"),
     ("forward_returns", "time_to_recover_days", "ALTER TABLE forward_returns ADD COLUMN time_to_recover_days INTEGER"),
+    # goal-market-compass iter-3 (J-05/J-06): the engine-identity stamp on newly created scanner_runs rows
+    # only. NULLABLE VARCHAR (matches `engine_identity: Optional[str] = Field(default=None)`) — an
+    # existing live DB gains the column in place; every pre-iter-3 row reads NULL forever ("pre-stamping
+    # era" — never backfilled).
+    ("scanner_runs", "engine_identity", "ALTER TABLE scanner_runs ADD COLUMN engine_identity VARCHAR"),
+    # goal-market-compass iter-3 (J-05/J-06): the freeze/integrity block on next_session_manifests, all
+    # ADDITIVE and NULLABLE/DEFAULTED so an existing live DB's pre-iter-3 rows backfill the documented
+    # "pre-freeze era" honesty marker (version=1, frozen=False, prospective_eligible=False, every hash /
+    # JSON block NULL) — never retroactively marked frozen or eligible. `version` NOT NULL DEFAULT 1
+    # satisfies "existing pre-iter-3 rows backfill version=1" directly at the DDL level; `frozen` and
+    # `prospective_eligible` NOT NULL DEFAULT 0 satisfy the fail-closed "absent field reads false" rule
+    # even before any Python-level default is consulted.
+    ("next_session_manifests", "version", "ALTER TABLE next_session_manifests ADD COLUMN version INTEGER NOT NULL DEFAULT 1"),
+    ("next_session_manifests", "mode", "ALTER TABLE next_session_manifests ADD COLUMN mode VARCHAR"),
+    ("next_session_manifests", "frozen", "ALTER TABLE next_session_manifests ADD COLUMN frozen BOOLEAN NOT NULL DEFAULT 0"),
+    ("next_session_manifests", "generation_json", "ALTER TABLE next_session_manifests ADD COLUMN generation_json VARCHAR"),
+    ("next_session_manifests", "engine_identity", "ALTER TABLE next_session_manifests ADD COLUMN engine_identity VARCHAR"),
+    ("next_session_manifests", "candidate_rule_hash", "ALTER TABLE next_session_manifests ADD COLUMN candidate_rule_hash VARCHAR"),
+    ("next_session_manifests", "candidate_rule_config_json", "ALTER TABLE next_session_manifests ADD COLUMN candidate_rule_config_json VARCHAR"),
+    ("next_session_manifests", "cohort_rule_hash", "ALTER TABLE next_session_manifests ADD COLUMN cohort_rule_hash VARCHAR"),
+    ("next_session_manifests", "cohort_rule_config_json", "ALTER TABLE next_session_manifests ADD COLUMN cohort_rule_config_json VARCHAR"),
+    ("next_session_manifests", "manifest_config_hash", "ALTER TABLE next_session_manifests ADD COLUMN manifest_config_hash VARCHAR"),
+    ("next_session_manifests", "manifest_config_subset_json", "ALTER TABLE next_session_manifests ADD COLUMN manifest_config_subset_json VARCHAR"),
+    ("next_session_manifests", "dataset_json", "ALTER TABLE next_session_manifests ADD COLUMN dataset_json VARCHAR"),
+    ("next_session_manifests", "universe_json", "ALTER TABLE next_session_manifests ADD COLUMN universe_json VARCHAR"),
+    ("next_session_manifests", "comparison_cohort_json", "ALTER TABLE next_session_manifests ADD COLUMN comparison_cohort_json VARCHAR"),
+    ("next_session_manifests", "near_threshold_shadow_json", "ALTER TABLE next_session_manifests ADD COLUMN near_threshold_shadow_json VARCHAR"),
+    ("next_session_manifests", "caveats_json", "ALTER TABLE next_session_manifests ADD COLUMN caveats_json VARCHAR"),
+    ("next_session_manifests", "prospective_eligible", "ALTER TABLE next_session_manifests ADD COLUMN prospective_eligible BOOLEAN NOT NULL DEFAULT 0"),
+    ("next_session_manifests", "available_at_utc", "ALTER TABLE next_session_manifests ADD COLUMN available_at_utc DATETIME"),
+    ("next_session_manifests", "manifest_hash", "ALTER TABLE next_session_manifests ADD COLUMN manifest_hash VARCHAR"),
+    ("next_session_manifests", "export_path", "ALTER TABLE next_session_manifests ADD COLUMN export_path VARCHAR"),
 )
 
 
@@ -162,14 +194,22 @@ def _ensure_additive_columns(engine: Engine) -> None:
 #   - `ix_daily_prices_date` (ADDED) — `func.max(DailyPrice.date)` (read on ~every request) and the
 #     availability/coverage `group_by(date)` scans walk the whole table without a `date`-only index; this
 #     one lets SQLite's MIN/MAX optimization + the group-by resolve straight from the index.
+#   - `ix_next_session_manifests_as_of` (DROPPED, goal-market-compass iter-3) — the OLD single-column
+#     UNIQUE index (one manifest per `as_of`, no versioning). iter-3 allows a confirm-gated regenerate to
+#     mint version N+1 for the SAME `as_of`, so the uniqueness constraint must widen to the composite
+#     `(as_of, version)` — `uq_next_session_manifests_as_of_version` (ADDED) below. This is the idempotent
+#     guarded swap pattern (never a destructive table rewrite): an existing live DB's stored manifest rows
+#     are untouched — only the index changes.
 #
 # Dropping a redundant index changes ONLY the query plan, never a result (No canonical value affected).
 _INDEX_DROPS: tuple[str, ...] = (
     "DROP INDEX IF EXISTS ix_daily_prices_symbol_date",
     "DROP INDEX IF EXISTS ix_forward_returns_run_symbol",
+    "DROP INDEX IF EXISTS ix_next_session_manifests_as_of",
 )
 _INDEX_ADDS: tuple[str, ...] = (
     "CREATE INDEX IF NOT EXISTS ix_daily_prices_date ON daily_prices (date)",
+    "CREATE UNIQUE INDEX IF NOT EXISTS uq_next_session_manifests_as_of_version ON next_session_manifests (as_of, version)",
 )
 
 
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index 8ad066a6..e43b3fae 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1,7 +1,7 @@
 """app.engine.compass — the deterministic narrative + candidate-selection trace + manifest assembly
-(goal-market-compass iter-2, J-03/J-04, CONTENT block only).
+(goal-market-compass iter-2, J-03/J-04, CONTENT block; iter-3, J-05/J-06, the freeze/integrity block).
 
-Three producers, one assembler:
+Three CONTENT producers, one assembler (iter-2, unchanged this iteration):
 
   - `build_narrative(...)` — deterministic template sentences (state / direction / breadth /
     focus-count, plus a no-comparison / NA-velocity / retrospective-stamp variant where it applies),
@@ -11,37 +11,70 @@ Three producers, one assembler:
     `ScannerResult` rows: candidates with reasons/cautions/checklist/what-would-change/invalidation;
     why-not entries for near-miss and cap-excluded non-candidates; a disposition tally that partitions
     member count minus candidate count exactly; an explicit `candidates_empty_reason` when nothing
-    clears the floor. No new blended/composite score is introduced anywhere (AG-11) — every value shown
-    is one of the three existing per-stock scores/buckets plus a config word map.
+    clears the floor. iter-3 (J-05/J-06) additionally serializes FULL frozen-context rows for every
+    non-candidate member — `comparison_cohort` (the whole non-selected pool, each row carrying a
+    closed-vocabulary `selection_disposition`) and `near_threshold_shadow` (the leadership-banded
+    subset just below the floor) — reusing the SAME `non_qualifying` / `excluded_by_cap_pairs`
+    partitions the disposition tally already computed. No new blended/composite score is introduced
+    anywhere (AG-11) — every value shown is one of the three existing per-stock scores/buckets, a
+    config word map, or a structural context field already computed by `scoring.score_stocks`.
   - `build_manifest_payload(...)` — assembles `session_delta` + `narrative` + `selection` into one
     content document and computes `content_hash` (sha256 over the sorted-key JSON of the content block
-    only).
+    only — unchanged scope/contract from iter-2, including the cohorts now nested inside `selection`).
 
-`get_or_create_manifest` / `manifest_row_payload` are the storage half: compute once per `as_of`
-(create-once), persist immutably (AG-12 — never updated or deleted), serve from storage on every later
-hit (TC-1 — zero producer calls on a warm read).
+The freeze/integrity block (iter-3, J-05/J-06) — `_freeze_manifest` is the ONE writer behind all three
+producer paths:
 
-Reads ONLY column-projected `ScannerResult` selects for the universe-wide sweep, plus a SMALL, bounded
-`record_json` read for the (<= `max_candidates`) actual candidates only — never a full-universe
-`record_json` sweep (AG-8). Never reads `forward_returns` or any bar dated after the as-of — it reads
-already-stored, already-computed run rows only (AG-5).
+  - (a) `get_or_create_manifest(..., producer="ingest_finalize")` — the ingest-finalize freeze call site;
+    mints version 1, `mode` is data-driven (`at_ingest` iff no bar dated later than the as-of exists at
+    generation — `_resolve_mode`), `frozen: true` always.
+  - (b) `get_or_create_manifest(...)` (default `producer="on_demand_get"`) — create-once-on-GET for a
+    HISTORICAL (non-frontier) as-of with no row yet. The CURRENT frontier's manifest is NEVER minted this
+    way (`ManifestNotYetFrozen`) — only (a) or an explicit (c) can mint it (J-05 step 7 / TC-8).
+  - (c) `regenerate_manifest(...)` — the confirm-gated regenerate action; mints version N+1 for an
+    EXISTING `as_of`. `prospective_eligible` is write-once and version-shopping-proof: only version 1
+    minted by `ingest_finalize` can ever be `true` (`_derive_prospective_eligible` is fail-closed on
+    every condition independently — mode, producer, version, frozen, the `available_at_utc` fence, and
+    complete provenance).
+
+`manifest_row_payload(row)` reconstructs the served document from the row's split storage columns —
+a READ, never a recompute (AG-8 column-projection posture: `comparison_cohort_json` /
+`near_threshold_shadow_json` / `generation_json` / the three rule-identity config-subset columns are
+their OWN columns so a future column-projected read never has to deserialize a block it does not need).
+`basis_disclosure(session, row)` is a READ-TIME-ONLY comparison (never a mutation, never a recompute of
+the frozen content) between the manifest's recorded `source_run_created_at` and the CURRENT stored run
+for that as-of (never the dataset-version stamp alone, which a rebuild can reproduce byte-identically).
+
+Reads ONLY column-projected `ScannerResult` selects for the universe-wide sweep, plus a bounded
+`record_json` read for candidates AND (iter-3) every non-candidate member of the ONE run being frozen
+(up to ~530 rows today) — never a full-universe sweep across runs (AG-8; TC-30). Never reads
+`forward_returns` or any bar dated after the as-of — it reads already-stored, already-computed run rows
+only (AG-5).
 """
 from __future__ import annotations
 
 import hashlib
 import json
-from datetime import datetime, timezone
-from typing import Optional
+import logging
+import os
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
+from typing import Any, Optional
 
 from sqlalchemy.exc import IntegrityError
 from sqlmodel import Session, select
 
-from app.config import Config, get_config
-from app.engine import market_phase
+from app.config import Config, REPO_ROOT, get_config
+from app.engine import engine_identity, evidence, market_phase, readiness
+from app.engine.prices import latest_data_date
+from app.engine.research import _dataset_version  # single-sourced dataset stamp (J-72) — never duplicated
 from app.engine.session_delta import compute_delta, find_previous_run
 from app.engine.setups import RISK_OFF_LABEL
 from app.engine.snapshot_serving import dashboard_payload
-from app.models import NextSessionManifest, ScannerResult, ScannerRun
+from app.engine.universe_screen import POOL_SURVIVORSHIP_LABEL, read_pool
+from app.models import NextSessionManifest, ScannerResult, ScannerRun, ThemeScoreRow
+
+logger = logging.getLogger(__name__)
 
 # --- narrative -------------------------------------------------------------------------------
 
@@ -166,15 +199,20 @@ def _retrospective_sentence() -> dict:
 
 def _is_retrospective(session: Session, current_run: ScannerRun) -> bool:
     """True when a LATER stored run already exists at the moment this manifest is generated — the
-    generation-time signal this narrative's retrospective stamp discloses. (Distinct from, and simpler
-    than, the future `mode`/`generation.*` freeze fields — J-05/J-06, OUT OF SCOPE this iteration.)"""
+    generation-time signal this narrative's retrospective stamp discloses. iter-3 (J-05/J-06) REUSES
+    this exact check as "is this NOT the current frontier run" — the manifest-freeze frontier guard
+    (`get_or_create_manifest`) and this narrative stamp ask the SAME question, so they share one
+    answer rather than two independently-drifting checks."""
     later = session.exec(select(ScannerRun.id).where(ScannerRun.asof_date > current_run.asof_date)).first()
     return later is not None
 
 
 def _assert_no_banned_language(sentences: list[dict], cfg: Config) -> None:
     """TC-11 as a runtime guarantee, not only an offline test scan: no rendered sentence may contain a
-    committed banned term (imperative trade verbs, forecast terms, causal-attribution phrases — AG-2)."""
+    committed banned term (imperative trade verbs, forecast terms, causal-attribution phrases — AG-2).
+    iter-3 (J-05/J-06, TC-35) reuses this SAME scan over `evaluate_selection`'s candidate reason/caution/
+    invalidation/why-not strings (`_scan_selection_language`, below) — these are about to be frozen into
+    an immutable exported artifact, so the guard must cover them too, not only narrative sentences."""
     banned = cfg.compass.vocabulary.banned_terms
     for sentence in sentences:
         lowered = sentence["text"].lower()
@@ -209,16 +247,38 @@ def build_narrative(
     return {"sentences": sentences}
 
 
-# --- selection (J-04) -------------------------------------------------------------------------
+# --- selection (J-04; iter-3 J-05/J-06 adds comparison_cohort + near_threshold_shadow) --------
 
 _QUALIFIER_CHECKS = ("leadership_min_score", "entry_min_score", "risk_max_score")
 
+# iter-3 (J-05/J-06): the cohort row's frozen context field list — part of `cohort_rule_hash`'s scope
+# (goal.md: "the cohort row field list"). Changing this list is itself a cohort-rule-affecting change
+# (a new/removed field moves `cohort_rule_hash`), so it is read into that hash's subset dict verbatim
+# rather than left as an unhashed implementation detail.
+_COHORT_ROW_FIELDS: tuple[str, ...] = (
+    "ticker", "leadership_score", "leadership_bucket", "entry_quality_score", "entry_quality_bucket",
+    "risk_score", "risk_bucket", "setup_status", "rank_in_run", "sector", "theme_memberships",
+    "close", "atr_pct", "distance_from_52w_high", "gap_p95", "worst_20d", "distance_to_invalidation",
+    "adv_dollars",
+)
+# The closed selection_disposition vocabulary (goal.md: partitions the non-selected set exactly under
+# the frozen rule — floor, then cap; nothing else excludes). Part of `cohort_rule_hash`'s scope.
+_DISPOSITION_BELOW_FLOOR = "below_selection_floor"
+_DISPOSITION_EXCLUDED_BY_CAP = "excluded_by_cap"
+_DISPOSITION_VOCABULARY: tuple[str, ...] = (_DISPOSITION_BELOW_FLOOR, _DISPOSITION_EXCLUDED_BY_CAP)
+# The declared candidate ordering rule (goal.md: "leadership desc, ticker asc") — a fixed descriptive
+# string, not a config value; part of `candidate_rule_hash`'s scope so a future re-ordering shows up as
+# an identity change even though no config KEY governs it today.
+_CANDIDATE_ORDERING_RULE = "leadership desc, ticker asc"
+
 
 def _record_json_by_ticker(session: Session, run: ScannerRun, tickers: list[str]) -> dict[str, dict]:
-    """A targeted, bounded `record_json` read for the actual candidates only (`len(tickers) <=
-    max_candidates`) — never a full-universe sweep (AG-8). Deliberately self-contained (does not reuse
-    `snapshot_serving.filtered_stock_rows`, which additionally attaches `forward_returns` — this producer
-    stays grep-clean of any post-as-of read, TC-23)."""
+    """A targeted, bounded `record_json` read for a specific ticker list SCOPED TO THIS ONE RUN — never a
+    full-universe or cross-run sweep (AG-8). Used for both candidates (`len(tickers) <= max_candidates`)
+    and, since iter-3 (J-05/J-06), every non-candidate member of the run being frozen (up to ~530 rows
+    today, TC-30) — still one bounded per-run query, not a whole-table scan. Deliberately self-contained
+    (does not reuse `snapshot_serving.filtered_stock_rows`, which additionally attaches `forward_returns`
+    — this producer stays grep-clean of any post-as-of read, TC-29)."""
     if not tickers:
         return {}
     rows = session.exec(
@@ -229,6 +289,103 @@ def _record_json_by_ticker(session: Session, run: ScannerRun, tickers: list[str]
     return {ticker: json.loads(record_json) for ticker, record_json in rows}
 
 
+def _theme_rank_by_slug(session: Session, run: ScannerRun) -> dict[str, int]:
+    """One small, per-run-bounded query (as many rows as configured themes — 11 today) mapping this run's
+    theme slug -> its stored rank. Used to attach `theme_memberships`' per-theme rank to each cohort row
+    without a per-ticker query (AG-8)."""
+    rows = session.exec(
+        select(ThemeScoreRow.slug, ThemeScoreRow.rank).where(ThemeScoreRow.run_id == run.id)
+    ).all()
+    return dict(rows)
+
+
+def _component_raw(components: list[dict], name: str) -> Optional[float]:
+    """The stored RAW value of one named component from a `leadership`/`entry_quality`/`risk` score
+    block's `components` array (`scoring._build_score`'s output, already stored verbatim in
+    `record_json`) — a READ of an already-computed value, never a new computation. `None` when the
+    component is absent or was NA for this row (honestly propagated, never fabricated)."""
+    for component in components:
+        if component.get("name") == name:
+            return component.get("raw")
+    return None
+
+
+def _cohort_row(row: dict, record: Optional[dict], theme_rank_by_slug: dict[str, int]) -> dict:
+    """One frozen `comparison_cohort` / `near_threshold_shadow` context row (goal-market-compass iter-3,
+    J-05/J-06) — every value is read from the run's ALREADY-STORED `record_json` (the SAME canonical
+    per-stock document `_candidate_payload` already reads a slice of), never a new bar/DB read (AG-8, "no
+    new data sources"):
+
+      - `close` reuses the invalidation block's `price` field — the as-of last close
+        (`scoring._invalidation`'s `price` arg is literally `inv_closes[-1]`, the as-of-date close).
+      - `distance_from_52w_high` reuses the Leadership score's stored `high_proximity` component raw
+        (`scoring._raw_components`: `dist_high = ind.dist_from_high(...)`, <= 0; already surfaced
+        verbatim by the Factor Lab at `leadership.components.high_proximity.raw` — an established
+        cross-surface read of this exact stored value, not a new one).
+      - `adv_dollars` reuses the Risk score's stored `liquidity` component raw, sign-flipped back
+        (`scoring._raw_components` stores `_neg(adv)` there so a HIGHER raw reads as MORE dangerous,
+        matching every other Risk component's orientation — this is a re-sign of an already-stored
+        number, not a new computation, no bars read).
+      - `atr_pct` / `gap_p95` / `worst_20d` / `distance_to_invalidation` all come from the SAME
+        `risk_budget` block `_candidate_payload`'s ATR caution already reads a slice of."""
+    record = record or {}
+    risk_budget = record.get("risk_budget") or {}
+    atr = risk_budget.get("atr_pct") or {}
+    gap_profile = risk_budget.get("gap_profile") or {}
+    leadership_components = (record.get("leadership") or {}).get("components") or []
+    risk_components = (record.get("risk") or {}).get("components") or []
+    liquidity_raw = _component_raw(risk_components, "liquidity")
+    themes = record.get("themes") or []
+
+    return {
+        "ticker": row["ticker"],
+        "leadership_score": row["leadership_score"],
+        "leadership_bucket": row["leadership_bucket"],
+        "entry_quality_score": row["entry_quality_score"],
+        "entry_quality_bucket": row["entry_quality_bucket"],
+        "risk_score": row["risk_score"],
+        "risk_bucket": row["risk_bucket"],
+        "setup_status": row["setup_status"],
+        "rank_in_run": row["rank_in_run"],
+        "sector": row["sector"],
+        "theme_memberships": [
+            {"theme": theme["slug"], "rank": theme_rank_by_slug.get(theme["slug"])} for theme in themes
+        ],
+        "close": (record.get("invalidation") or {}).get("price"),
+        "atr_pct": {"value": atr.get("value"), "percentile": atr.get("percentile")},
+        "distance_from_52w_high": _component_raw(leadership_components, "high_proximity"),
+        "gap_p95": (gap_profile.get("p95") or {}).get("value"),
+        "worst_20d": (risk_budget.get("worst_20d_window") or {}).get("value"),
+        "distance_to_invalidation": (risk_budget.get("distance_to_invalidation_pct") or {}).get("value"),
+        "adv_dollars": -liquidity_raw if liquidity_raw is not None else None,
+    }
+
+
+def _scan_selection_language(candidates: list[dict], why_not: list[dict], cfg: Config) -> None:
+    """TC-35: extend the SAME runtime banned-language guard `build_narrative` already uses to
+    `evaluate_selection`'s candidate reason/caution/invalidation/why-not strings — these are about to be
+    frozen into an immutable exported artifact (iter-3), so the guard must cover them before ANY
+    candidate is returned, not only narrative sentences (the exact gap `lessons.md` iter-2 flagged)."""
+    pseudo_sentences: list[dict] = []
+    for candidate in candidates:
+        ticker = candidate["ticker"]
+        for index, text in enumerate(candidate["reasons"]):
+            pseudo_sentences.append({"template_id": f"candidate_reason_{ticker}_{index}", "text": text, "facts": []})
+        for index, text in enumerate(candidate["cautions"]):
+            pseudo_sentences.append({"template_id": f"candidate_caution_{ticker}_{index}", "text": text, "facts": []})
+        pseudo_sentences.append(
+            {"template_id": f"candidate_invalidation_{ticker}", "text": candidate["invalidation"], "facts": []}
+        )
+    for entry in why_not:
+        for index, failed in enumerate(entry["failed_conditions"]):
+            # `condition` is always one of the fixed `_QUALIFIER_CHECKS` tokens, never free text — scanned
+            # anyway so the guard's coverage matches goal.md's literal "why-not strings" wording exactly.
+            pseudo_sentences.append(
+                {"template_id": f"why_not_{entry['ticker']}_{index}", "text": failed["condition"], "facts": []}
+            )
+    _assert_no_banned_language(pseudo_sentences, cfg)
+
+
 def _qualifier_checks(row: dict, cfg: Config) -> list[dict]:
     sel = cfg.compass.selection
     return [
@@ -290,9 +447,8 @@ def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], ru
     if atr.get("value") is not None:
         pct = atr.get("percentile")
         pct_text = f"p{pct * 100:.0f} of universe" if pct is not None else "percentile NA"
-        cautions.append(
-            f"ATR_RISK_BUDGET: ATR is {atr['value']:.2f}% of price ({pct_text}) — sized risk accordingly."
-        )
+        # TC-34 (iter-3 MINOR finding, iter-2 eval): states the fact only — no advice-sounding tail.
+        cautions.append(f"ATR_RISK_BUDGET: ATR is {atr['value']:.2f}% of price ({pct_text}).")
     else:
         cautions.append("ATR_RISK_BUDGET: risk-budget data not available for this row — reported NA, never fabricated.")
     inv = (detail or {}).get("invalidation") or {}
@@ -321,8 +477,9 @@ def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], ru
 
 
 def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
-    """The `selection` CONTENT block (goal-market-compass iter-2, J-04). See the module docstring for
-    the anti-goal posture (AG-8 bounded reads, AG-11 no new composite score)."""
+    """The `selection` CONTENT block (goal-market-compass iter-2, J-04; iter-3, J-05/J-06 adds
+    `comparison_cohort` + `near_threshold_shadow`). See the module docstring for the anti-goal posture
+    (AG-8 bounded reads, AG-11 no new composite score)."""
     cfg = config or get_config()
     sel = cfg.compass.selection
 
@@ -335,6 +492,9 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
             ScannerResult.entry_quality_bucket,
             ScannerResult.risk_score,
             ScannerResult.risk_bucket,
+            ScannerResult.setup_status,
+            ScannerResult.rank,
+            ScannerResult.sector,
         )
         .where(ScannerResult.run_id == run.id)
         .order_by(ScannerResult.ticker)
@@ -343,7 +503,9 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
 
     qualifying: list[tuple[dict, list[dict]]] = []
     non_qualifying: list[tuple[dict, list[dict]]] = []
-    for ticker, l_score, l_bucket, e_score, e_bucket, r_score, r_bucket in raw_rows:
+    for (
+        ticker, l_score, l_bucket, e_score, e_bucket, r_score, r_bucket, setup_status, rank, sector,
+    ) in raw_rows:
         row = {
             "ticker": ticker,
             "leadership_score": l_score,
@@ -352,6 +514,9 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
             "entry_quality_bucket": e_bucket,
             "risk_score": r_score,
             "risk_bucket": r_bucket,
+            "setup_status": setup_status,
+            "rank_in_run": rank,
+            "sector": sector,
         }
         checks = _qualifier_checks(row, cfg)
         if all(check["passed"] for check in checks):
@@ -397,7 +562,34 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
             f"Entry Quality >= {sel.entry_min_score:.1f}, Risk <= {sel.risk_max_score:.1f}) for this as-of."
         )
 
-    return {
+    # --- iter-3 (J-05/J-06): comparison cohort (every non-candidate member) + near-threshold shadow.
+    # Reuses the SAME non_qualifying / excluded_by_cap_pairs partitions the disposition tally above
+    # already computed — exactly the below_selection_floor / excluded_by_cap split (BACKGROUND).
+    non_candidate_pairs: list[tuple[dict, str]] = [(row, _DISPOSITION_BELOW_FLOOR) for row, _failed in non_qualifying]
+    non_candidate_pairs.extend((row, _DISPOSITION_EXCLUDED_BY_CAP) for row, _checks in excluded_by_cap_pairs)
+    non_candidate_pairs.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))
+
+    non_candidate_tickers = [row["ticker"] for row, _disposition in non_candidate_pairs]
+    non_candidate_records = _record_json_by_ticker(session, run, non_candidate_tickers)  # TC-30: one bounded per-run read
+    theme_rank_by_slug = _theme_rank_by_slug(session, run)
+
+    comparison_cohort = [
+        {
+            **_cohort_row(row, non_candidate_records.get(row["ticker"]), theme_rank_by_slug),
+            "selection_disposition": disposition,
+        }
+        for row, disposition in non_candidate_pairs
+    ]
+    # Half-open band [shadow.min_score, leadership_min_score) — a name AT the floor is candidate-eligible,
+    # never shadow. A subset of comparison_cohort by construction (built from the SAME ordered pairs, so
+    # both stay in lockstep — never independently re-sorted / re-derived).
+    near_threshold_shadow = [
+        {k: v for k, v in cohort_row.items() if k != "selection_disposition"}
+        for cohort_row, (row, _disposition) in zip(comparison_cohort, non_candidate_pairs)
+        if sel.shadow.min_score <= row["leadership_score"] < sel.leadership_min_score
+    ]
+
+    result = {
         "candidates": candidates,
         "why_not": why_not,
         "disposition_tally": {
@@ -405,10 +597,15 @@ def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Confi
             "excluded_by_cap": len(excluded_by_cap_pairs),
         },
         "candidates_empty_reason": candidates_empty_reason,
+        "member_count": member_count,
+        "comparison_cohort": comparison_cohort,
+        "near_threshold_shadow": near_threshold_shadow,
     }
+    _scan_selection_language(candidates, why_not, cfg)  # TC-35 — before ANY candidate/why-not is returned
+    return result
 
 
-# --- manifest assembly + storage ----------------------------------------------------------------
+# --- manifest CONTENT assembly (iter-2, unchanged scope) ----------------------------------------
 
 
 def build_manifest_payload(
@@ -418,7 +615,9 @@ def build_manifest_payload(
     config: Optional[Config] = None,
 ) -> dict:
     """Assemble the three CONTENT blocks + `content_hash` (sha256 hex over the sorted-key JSON of the
-    content block only — never re-derived at serve time; see `manifest_row_payload`)."""
+    content block only — never re-derived at serve time; see `manifest_row_payload`). UNCHANGED scope
+    from iter-2: `selection` now carries `comparison_cohort` / `near_threshold_shadow` (iter-3), which
+    flow through into `content_hash`'s scope automatically — no code change needed here for that."""
     cfg = config or get_config()
     delta = compute_delta(session, current_run, previous_run, cfg)
     selection = evaluate_selection(session, current_run, cfg)
@@ -429,32 +628,370 @@ def build_manifest_payload(
     return {**content, "content_hash": content_hash}
 
 
-def get_or_create_manifest(
-    session: Session, current_run: ScannerRun, config: Optional[Config] = None
+# --- freeze/integrity block (iter-3, J-05/J-06) --------------------------------------------------
+
+
... [diff_bound] apps/backend/app/engine/compass.py: 514 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index a8efe27d..cd2fa001 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -2471,7 +2471,7 @@ class JobProgress:
     # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
-    # "coverage", "membership_timeline", "market_phase", "next_session_manifest", "forward_aggregates",
+    # "coverage", "membership_timeline", "market_phase", "next-session_manifest", "forward_aggregates",
     # "research_hot_keys", "drawdown_expectations", "index_series", "factor_lab_all",
     # "availability_heatmap"]` it actually refreshed — empty/default until the hook has actually run (never fabricated on an
     # interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc. already are).
@@ -4199,7 +4199,7 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
-    "coverage", "membership_timeline", "market_phase", "next_session_manifest", "forward_aggregates",
+    "coverage", "membership_timeline", "market_phase", "next-session_manifest", "forward_aggregates",
     "research_hot_keys", "drawdown_expectations", "index_series", "factor_lab_all",
     "availability_heatmap"]` ACTUALLY refreshed — never a fabricated category (mirrors the
     `omitted`/`passers` honesty convention already used elsewhere in this module).
@@ -4529,7 +4529,13 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 try:
                     run_for_date = scanner.get_run_for_date(session, d)
                     if run_for_date is not None:
-                        compass.get_or_create_manifest(session, run_for_date, cfg)
+                        # goal-market-compass iter-3 (J-05/J-06): producer="ingest_finalize" routes this
+                        # through the freeze writer's path (a) -- mints version 1, mode is data-driven
+                        # (at_ingest only for the actual frontier date; a mid-history backfilled date in
+                        # this SAME loop honestly resolves mode="retrospective" and prospective_eligible
+                        # stays False via _derive_prospective_eligible's own mode check -- no special-
+                        # casing needed here for "is this the frontier").
+                        compass.get_or_create_manifest(session, run_for_date, cfg, producer="ingest_finalize")
                         compass_warmed = True
                 except MemoryError as exc:
                     _log_isolation_failure(
@@ -4541,7 +4547,11 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                 except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
                     _log_isolation_failure("ingest compass-content warm failed for %s (non-fatal): %s", d, exc)
             if compass_warmed:
-                refreshed.append("next_session_manifest")
+                # goal-market-compass iter-3 (J-05/J-06, TC-1): renamed so the frontend's
+                # `s.replace(/_/g, " ")` humanizer (apps/frontend/app/data/page.tsx) renders "next-session
+                # manifest" (hyphenated) exactly matching J-05 step 1's disclosure text -- the OLD key
+                # "next_session_manifest" rendered "next session manifest" (missing hyphen).
+                refreshed.append("next-session_manifest")
             logger.info(
                 "J-05 finalize-tail phase timing: job=%s phase=%s elapsed=%.2fs",
                 prog.job_id, "compass_content_warm", time.monotonic() - _phase_t0,
diff --git a/apps/backend/app/engine/scanner.py b/apps/backend/app/engine/scanner.py
index 157a19b2..941b58ae 100644
--- a/apps/backend/app/engine/scanner.py
+++ b/apps/backend/app/engine/scanner.py
@@ -35,6 +35,7 @@ from sqlalchemy.exc import IntegrityError
 from sqlmodel import Session, select
 
 from app.config import Config, get_config
+from app.engine import engine_identity
 from app.engine.prices import bar_cache, latest_data_date
 from app.engine.regime import score_regime
 from app.engine.scoring import score_stocks
@@ -113,6 +114,9 @@ def persist_run_payload(
         breadth_above_200dma=regime["breadth_above_200dma"],
         new_high_low_json=json.dumps(regime["new_high_low"]),
         candidate_counts_json=json.dumps(candidate_counts),
+        # goal-market-compass iter-3 (J-05/J-06): stamped ONCE at persist time on every NEWLY created
+        # run only — an existing pre-iter-3 row stays NULL forever ("pre-stamping era", never backfilled).
+        engine_identity=engine_identity.compute_engine_identity(cfg),
     )
     session.add(run)
     try:
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 2f9f3274..5fa1bb33 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -212,6 +212,13 @@ class ScannerRun(SQLModel, table=True):
     breadth_above_200dma: Optional[float] = None
     new_high_low_json: str
     candidate_counts_json: str
+    # goal-market-compass iter-3 (J-05/J-06): the engine-code + config identity stamp
+    # (`app.engine.engine_identity.compute_engine_identity`), written ONCE at persist time by
+    # `scanner.persist_run_payload` — an ADDITIVE nullable column (`db._ADDITIVE_COLUMNS`). An existing
+    # pre-iter-3 row stays NULL forever ("pre-stamping era" — never backfilled); only NEWLY created runs
+    # carry a stamp. Read (never recomputed) by the next-session manifest freeze writer's read-time basis
+    # disclosure (compares this against the manifest's own frozen `generation.engine_identity`).
+    engine_identity: Optional[str] = Field(default=None)
 
 
 class ScannerResult(SQLModel, table=True):
@@ -761,30 +768,55 @@ class AvailabilityCache(SQLModel, table=True):
 
 
 class NextSessionManifest(SQLModel, table=True):
-    """One next-session manifest row for one `as_of` date (goal-market-compass iter-2, J-02/J-03/J-04 —
-    the CONTENT block only; J-05/J-06 add `mode`/`version`/`frozen`/`generation.*`/hashes/provenance/
-    cohort-storage/export columns ADDITIVELY in a later iteration — this iteration's five columns below
-    never change shape, per `docs/phases/goal-market-compass-iter-2.md` OUT OF SCOPE).
+    """One next-session manifest VERSION row for one `(as_of, version)` pair (goal-market-compass iter-2,
+    J-02/J-03/J-04 — the CONTENT block; iter-3, J-05/J-06 — the freeze/integrity block: `mode`/`version`/
+    `frozen`/`generation`/three hashes/provenance/cohort-storage/`prospective_eligible`/
+    `available_at_utc`/`export_path`, added ADDITIVELY).
 
     UNLIKE the `*Cache` tables above (`MarketPhaseCache` et al.), this is NOT a cache of a re-derivable
-    read — it is a first-class IMMUTABLE record, like `ScannerRun`: computed ONCE per `as_of` (at ingest
-    finalize, or on the first `GET /api/compass` for a not-yet-computed `as_of` — create-once-on-GET) and
-    NEVER updated or deleted afterward (anti-goal AG-12 — manifest immutability binds from this iteration
-    on, even though the `frozen`/`version` columns that make that explicit are still J-05/J-06). `as_of`
-    is unique — exactly one row per date, mirroring `ScannerRun.asof_date`. A concurrent create-once race
-    is resolved the SAME way `scanner.persist_run_payload` resolves a `ScannerRun` race: roll back the
-    losing INSERT and return the already-committed row (never raise, never duplicate, never overwrite).
-
-    The three CONTENT blocks (`session_delta`, `narrative`, `selection` — see `app.engine.compass`'s
-    Data-contract shapes) are stored as their OWN JSON columns rather than one combined blob so a future
-    column-projected read never has to deserialize a block it does not need (AG-8 posture). `content_hash`
-    is the sha256 hex digest of the sorted-key JSON of exactly these three blocks (see
-    `app.engine.compass.build_manifest_payload`) — NOT of this row's other columns."""
+    read — it is a first-class IMMUTABLE record, like `ScannerRun`: computed ONCE per `(as_of, version)`
+    (at ingest finalize for the frontier date, on the first `GET /api/compass` for a not-yet-computed
+    HISTORICAL `as_of` — create-once-on-GET, never the frontier — or via the explicit confirm-gated
+    regenerate action) and NEVER updated or deleted afterward (anti-goal AG-12 — manifest immutability).
+    `(as_of, version)` is unique — `version` starts at 1 and is dense/append-only per `as_of`; a
+    concurrent create-once race is resolved the SAME way `scanner.persist_run_payload` resolves a
+    `ScannerRun` race: roll back the losing INSERT and return the already-committed row (never raise,
+    never duplicate, never overwrite). `next_session_manifests` joins NEITHER `clear_snapshot_set` NOR
+    the remove-data cascade — no code path deletes a row here.
+
+    The three CONTENT blocks (`session_delta`, `narrative`, `selection` — the `selection` block now also
+    carries `comparison_cohort` / `near_threshold_shadow`, iter-3) are stored as their OWN JSON columns
+    rather than one combined blob so a future column-projected read never has to deserialize a block it
+    does not need (AG-8 posture). `content_hash` is the sha256 hex digest of the sorted-key JSON of
+    exactly these three blocks (see `app.engine.compass.build_manifest_payload`) — NOT of this row's
+    other columns; it stays invariant across legitimate generation-metadata-only differences (e.g. a
+    regenerate with unchanged inputs).
+
+    The FREEZE/INTEGRITY columns below are all ADDITIVE and nullable/defaulted (`db._ADDITIVE_COLUMNS`)
+    so an existing pre-iter-3 row backfills `version=1`, `frozen=False`, `mode`/every hash/JSON-block
+    column NULL, `prospective_eligible=False` — an honest "pre-freeze era" marker, NEVER retroactively
+    marked frozen or eligible. Every column here is written ONCE, together, by
+    `app.engine.compass._freeze_manifest` (the single writer behind all three producer paths) and never
+    touched again. `generation_json`/`candidate_rule_config_json`/`cohort_rule_config_json`/
+    `manifest_config_subset_json`/`dataset_json`/`universe_json`/`comparison_cohort_json`/
+    `near_threshold_shadow_json`/`caveats_json` hold their block's OWN verbatim JSON (AG-8 posture, same
+    reasoning as the three content columns above). `engine_identity`/`candidate_rule_hash`/
+    `cohort_rule_hash`/`manifest_config_hash`/`prospective_eligible`/`manifest_hash` are ALSO typed
+    top-level columns (not just JSON-nested) so a future consumer can column-project-filter without
+    parsing `generation_json` (`prospective_eligible` is explicitly called out for this in goal.md).
+    `export_path` stays NULL when the at-ingest export write fails (isolate-and-continue — an honest gap,
+    never a half-written file silently treated as present)."""
 
     __tablename__ = "next_session_manifests"
+    __table_args__ = (
+        UniqueConstraint("as_of", "version", name="uq_next_session_manifests_as_of_version"),
+    )
 
     id: Optional[int] = Field(default=None, primary_key=True)
-    as_of: date = Field(index=True, unique=True)
+    as_of: date = Field(index=True)
+    # iter-3: version starts at 1 (the finalize freeze or the first historical on-demand GET); a
+    # confirm-gated regenerate mints version N+1 for an existing as_of. Pre-iter-3 rows backfill 1.
+    version: int = Field(default=1)
     source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)
     session_delta_json: str
     narrative_json: str
@@ -792,6 +824,30 @@ class NextSessionManifest(SQLModel, table=True):
     content_hash: str = Field(index=True)
     created_at: datetime
 
+    # --- iter-3 freeze/integrity block (additive; NULL/False on a pre-iter-3 row) -----------------
+    mode: Optional[str] = Field(default=None)  # "at_ingest" | "retrospective" — data-driven, never chosen
+    frozen: bool = Field(default=False)  # True for every row minted by the iter-3 freeze writer
+    generation_json: Optional[str] = Field(default=None)  # {producer, frontier_bar_date, generated_at,
+    # preflight_verdict, engine_identity, source_run_created_at}
+    engine_identity: Optional[str] = Field(default=None)  # mirror of generation.engine_identity (typed)
+    candidate_rule_hash: Optional[str] = Field(default=None, index=True)
+    candidate_rule_config_json: Optional[str] = Field(default=None)
+    cohort_rule_hash: Optional[str] = Field(default=None, index=True)
+    cohort_rule_config_json: Optional[str] = Field(default=None)
+    manifest_config_hash: Optional[str] = Field(default=None)
+    manifest_config_subset_json: Optional[str] = Field(default=None)
+    dataset_json: Optional[str] = Field(default=None)  # {"stamp": ...}
+    universe_json: Optional[str] = Field(default=None)  # {pool_hash, resolver_gate, member_count, profile}
+    comparison_cohort_json: Optional[str] = Field(default=None)  # list of frozen non-candidate rows
+    near_threshold_shadow_json: Optional[str] = Field(default=None)  # subset of the above, near the floor
+    caveats_json: Optional[str] = Field(default=None)  # {evidence, survivorship, sector_basis, cohort_semantics}
+    # fail-closed, write-once: true iff mode=at_ingest, producer=ingest_finalize, version=1, frozen=True,
+    # a well-formed available_at_utc, and complete provenance — derived ONCE at write, NEVER at read.
+    prospective_eligible: bool = Field(default=False, index=True)
+    available_at_utc: Optional[datetime] = Field(default=None)
+    manifest_hash: Optional[str] = Field(default=None)  # whole-document integrity hash (excl. itself)
+    export_path: Optional[str] = Field(default=None)  # NULL when never exported / export write failed
+
 
 # --- ops-hardening iter-2 (J-05) coverage derived-aggregate snapshot (a PERFORMANCE cache, not a
 # snapshot) -----------------------------------------------------------------------------------
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
index a5927ddc..21895ea3 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -59,9 +59,21 @@ def compass_engine(tmp_path):
     return engine
 
 
+def _freeze_frontier(engine, cfg) -> None:
+    """iter-3: the route can no longer auto-mint the CURRENT frontier's manifest (J-05 step 7) -- tests
+    that exercise the WARM-HIT/served-fields behavior must first simulate the ingest-finalize freeze the
+    same way `data_manager._refresh_ingest_aggregates` does."""
+    with Session(engine) as session:
+        run = session.exec(
+            __import__("sqlmodel").select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))
+        ).first()
+        compass_module.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+
+
 def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
     from app.api.compass import compass as compass_route
 
+    _freeze_frontier(compass_engine, cfg)
     with Session(compass_engine) as session:
         result = compass_route(None, session)
 
@@ -75,13 +87,42 @@ def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
     for key in ("candidates", "why_not", "disposition_tally", "candidates_empty_reason"):
         assert key in result["selection"]
     assert isinstance(result["content_hash"], str) and len(result["content_hash"]) == 64  # sha256 hex
+    # iter-3 (J-05/J-06) freeze/integrity fields -- every one served at the response layer directly.
+    assert result["mode"] == "at_ingest"
+    assert result["version"] == 1
+    assert result["frozen"] is True
+    assert result["prospective_eligible"] is True
+    assert result["generation"]["producer"] == "ingest_finalize"
+    assert result["generation"]["engine_identity"]
+    assert result["candidate_rule_hash"] and result["cohort_rule_hash"] and result["manifest_config_hash"]
+    assert result["dataset"]["stamp"]
+    assert result["universe"]["member_count"] == 1
+    assert isinstance(result["comparison_cohort"], list)
+    assert isinstance(result["near_threshold_shadow"], list)
+    assert result["caveats"]["cohort_semantics"]
+    assert result["available_at_utc"]
+    assert isinstance(result["manifest_hash"], str) and len(result["manifest_hash"]) == 64
+    # `basis`/`versions` are READ-TIME-ONLY additions the API layer attaches AFTER manifest_row_payload()
+    # -- they were never part of what got hashed at write time, so verification runs over the pure
+    # reconstructed document (TC-4's exact contract), not the full API response shape.
+    hashed_document = {k: v for k, v in result.items() if k not in ("basis", "versions")}
+    assert compass_module.verify_manifest_hash(hashed_document)
+    assert result["basis"]["status"] == "available"
+    assert result["versions"] == [
+        {
+            "version": 1, "mode": "at_ingest", "frozen": True, "prospective_eligible": True,
+            "generated_at": result["generation"]["generated_at"],
+        }
+    ]
 
 
 def test_compass_route_computes_once_serves_from_storage_after(compass_engine, cfg, monkeypatch):
-    """TC-1: the second call for the same as-of returns byte-identical content with ZERO additional
-    producer calls (get_or_create_manifest short-circuits on the stored row)."""
+    """TC-1: once frozen, the SECOND call for the same as-of returns byte-identical content with ZERO
+    additional producer calls (get_or_create_manifest short-circuits on the stored row)."""
     from app.api.compass import compass as compass_route
 
+    _freeze_frontier(compass_engine, cfg)
+
     calls = {"n": 0}
     original = compass_module.build_manifest_payload
 
@@ -93,11 +134,11 @@ def test_compass_route_computes_once_serves_from_storage_after(compass_engine, c
 
     with Session(compass_engine) as session:
         first = compass_route(None, session)
-    assert calls["n"] == 1
+    assert calls["n"] == 0  # already frozen by _freeze_frontier -- this call is a pure warm read
 
     with Session(compass_engine) as session:
         second = compass_route(None, session)
-    assert calls["n"] == 1  # no additional producer call on the second, separate-request hit
+    assert calls["n"] == 0  # no additional producer call on the second, separate-request hit
 
     assert first == second
 
@@ -108,6 +149,23 @@ def test_compass_route_computes_once_serves_from_storage_after(compass_engine, c
     assert len(rows) == 1
 
 
+def test_compass_route_frontier_with_no_manifest_yet_returns_honest_404(compass_engine, cfg):
+    """J-05 step 7 / TC-8: a plain GET for the CURRENT frontier with no manifest yet never mints one --
+    an honest 404, never a fabricated payload."""
+    from app.api.compass import compass as compass_route
+
+    with Session(compass_engine) as session:
+        with pytest.raises(HTTPException) as exc_info:
+            compass_route(None, session)
+    assert exc_info.value.status_code == 404
+
+    with Session(compass_engine) as session:
+        rows = session.exec(
+            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
+        ).all()
+    assert rows == []  # no partial/fabricated row was written
+
+
 def test_compass_route_unknown_asof_returns_honest_error_never_fabricated(compass_engine, cfg):
     from app.api.compass import compass as compass_route
 
@@ -125,3 +183,64 @@ def test_compass_route_historical_asof_serves_that_dates_own_manifest(compass_en
         result = compass_route("2024-06-01", session)
     assert result["as_of"] == "2024-06-01"
     assert result["session_delta"]["prior_as_of"] is None  # earliest stored run -- explicit no-prior-run state
+
+
+# --- POST /api/compass/regenerate (iter-3, J-05/J-06) --------------------------------------------
+
+
+def test_regenerate_route_requires_confirm_flag(compass_engine, cfg):
+    """TC-13 / Error cases: called without confirm=true, no row is created."""
+    from app.api.compass import compass_regenerate
+
+    with Session(compass_engine) as session:
+        with pytest.raises(HTTPException) as exc_info:
+            compass_regenerate("2024-06-01", False, session)
+    assert exc_info.value.status_code == 400
+
+    with Session(compass_engine) as session:
+        rows = session.exec(
+            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 1))
+        ).all()
+    assert rows == []
+
+
+def test_regenerate_route_missing_manifest_returns_honest_404(compass_engine, cfg):
+    """Error cases: regenerate for an as_of with no existing manifest returns an honest 4xx, never
+    fabricates a version."""
+    from app.api.compass import compass_regenerate
+
+    with Session(compass_engine) as session:
+        with pytest.raises(HTTPException) as exc_info:
+            compass_regenerate("2024-06-01", True, session)
+    assert exc_info.value.status_code == 404
+
+
+def test_regenerate_route_mints_version_2_leaves_version_1_untouched(compass_engine, cfg):
+    """TC-12: version 2 carries its own generation/available_at_utc/manifest_hash, prospective_eligible
+    False even though a historical as_of's mode also computes at_ingest-ineligible (retrospective);
+    version 1 stays byte-identical."""
+    from app.api.compass import compass as compass_route
+    from app.api.compass import compass_regenerate
+
+    with Session(compass_engine) as session:
+        v1 = compass_route("2024-06-01", session)
+
+    with Session(compass_engine) as session:
+        v2 = compass_regenerate("2024-06-01", True, session)
+
+    assert v2["version"] == 2
+    assert v2["prospective_eligible"] is False
+    assert v2["manifest_hash"] != v1["manifest_hash"]
+    assert v2["generation"]["producer"] == "regenerate"
+
+    with Session(compass_engine) as session:
+        v1_reread = compass_route("2024-06-01", session)
+    # re-reading after a regenerate still serves the LATEST version by default...
+    assert v1_reread["version"] == 2
+    # ...but version 1's own row is untouched -- fetch it explicitly via list_manifest_versions
+    with Session(compass_engine) as session:
+        versions = compass_module.list_manifest_versions(session, date(2024, 6, 1))
+    assert [v.version for v in versions] == [1, 2]
+    assert versions[0].manifest_hash == v1["manifest_hash"]
+    assert versions[0].content_hash == v1["content_hash"]
+    assert versions[0].prospective_eligible is False  # historical as_of was never eligible either
diff --git a/apps/backend/tests/test_compass.py b/apps/backend/tests/test_compass.py
index f5e203f7..103ab537 100644
--- a/apps/backend/tests/test_compass.py
+++ b/apps/backend/tests/test_compass.py
@@ -217,13 +217,104 @@ def test_no_composite_score_field_anywhere(engine, cfg, selection_run):
         assert numeric_keys <= allowed_numeric_keys, f"unexpected numeric field(s) on candidate: {numeric_keys - allowed_numeric_keys}"
 
 
-def test_shadow_cohort_never_appears_in_selection_payload(engine, cfg, selection_run):
-    """TC-20 / the shadow key is reserved (config only) but computes/renders nothing this iteration."""
+def test_comparison_cohort_covers_every_non_candidate_with_disposition(engine, cfg, selection_run):
+    """iter-3 (J-05/J-06, TC-19/TC-24): comparison_cohort holds EVERY non-candidate member (member_count
+    minus candidate_count), each carrying exactly one closed-vocabulary disposition, tallies partitioning
+    the cohort exactly."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        member_count = len(session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all())
+        result = compass.evaluate_selection(session, run, cfg)
+    cohort = result["comparison_cohort"]
+    assert len(cohort) == member_count - len(result["candidates"])
+    by_ticker = {row["ticker"]: row for row in cohort}
+    assert by_ticker["CCC"]["selection_disposition"] == "below_selection_floor"
+    assert by_ticker["DDD"]["selection_disposition"] == "below_selection_floor"
+    dispositions = {row["selection_disposition"] for row in cohort}
+    assert dispositions <= {"below_selection_floor", "excluded_by_cap"}
+    tally = result["disposition_tally"]
+    below = sum(1 for row in cohort if row["selection_disposition"] == "below_selection_floor")
+    capped = sum(1 for row in cohort if row["selection_disposition"] == "excluded_by_cap")
+    assert below == tally["below_selection_floor"]
+    assert capped == tally["excluded_by_cap"]
+    # every candidate ticker is ticker-disjoint from the cohort (never both selected AND non-selected)
+    assert {c["ticker"] for c in result["candidates"]}.isdisjoint(by_ticker)
+
+
+def test_comparison_cohort_row_carries_frozen_context_fields(engine, cfg, selection_run):
+    """iter-3 (J-05/J-06): every cohort row's context is read from the run's own stored record_json —
+    close (invalidation.price), atr_pct {value, percentile}, sector, setup_status, rank_in_run."""
     with Session(engine) as session:
         run = session.get(ScannerRun, selection_run)
         result = compass.evaluate_selection(session, run, cfg)
-    serialized = json.dumps(result).lower()
-    assert "shadow" not in serialized
+    ccc = next(row for row in result["comparison_cohort"] if row["ticker"] == "CCC")
+    assert ccc["close"] == 110.0  # _mk_result's invalidation.price fixture value
+    assert ccc["atr_pct"] == {"value": 3.0, "percentile": 0.5}
+    assert ccc["sector"] == "Technology"
+    assert ccc["setup_status"] == "Breakout-watch"
+    assert ccc["rank_in_run"] == 1
+    assert ccc["theme_memberships"] == []  # no themes configured on this synthetic fixture row
+
+
+def test_excluded_by_cap_cohort_rows_carry_that_disposition(engine, cfg, selection_run):
+    capped_selection = cfg.compass.selection.model_copy(update={"max_candidates": 2})
+    capped_cfg = cfg.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": capped_selection})})
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, capped_cfg)
+    cut_ticker = ({"AAA", "BBB", "EEE"} - {c["ticker"] for c in result["candidates"]}).pop()
+    cohort_row = next(row for row in result["comparison_cohort"] if row["ticker"] == cut_ticker)
+    assert cohort_row["selection_disposition"] == "excluded_by_cap"
+
+
+def test_near_threshold_shadow_is_half_open_band_below_floor(engine, cfg, selection_run):
+    """iter-3 (J-05/J-06, TC-19): near_threshold_shadow = leadership in [shadow.min_score,
+    leadership_min_score) -- half-open, deterministic order (leadership desc, ticker), a subset of
+    comparison_cohort with no selection_disposition key. CCC (leadership 77.0, in [75.0, 80.0)) is
+    shadow-eligible; DDD (30.0) is not; nothing at/above the 80.0 floor is ever shadow."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    shadow = result["near_threshold_shadow"]
+    assert [row["ticker"] for row in shadow] == ["CCC"]
+    assert "selection_disposition" not in shadow[0]
+    assert shadow[0]["leadership_score"] == 77.0
+    # never contains a candidate-eligible name (score >= floor) nor DDD (far below the shadow floor)
+    shadow_tickers = {row["ticker"] for row in shadow}
+    assert shadow_tickers.isdisjoint({c["ticker"] for c in result["candidates"]})
+    assert "DDD" not in shadow_tickers
+
+
+def test_near_threshold_shadow_is_subset_of_comparison_cohort(engine, cfg, selection_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, selection_run)
+        result = compass.evaluate_selection(session, run, cfg)
+    cohort_tickers = {row["ticker"] for row in result["comparison_cohort"]}
+    shadow_tickers = {row["ticker"] for row in result["near_threshold_shadow"]}
+    assert shadow_tickers <= cohort_tickers
+
+
+def test_selection_language_scan_covers_candidate_and_why_not_strings(engine, cfg, monkeypatch):
+    """TC-35: the SAME banned-language guard build_narrative uses now also scans evaluate_selection's
+    candidate reason/caution/invalidation/why-not strings -- a banned term anywhere in them raises."""
+    from app.engine import compass as compass_module
+
+    original = compass_module._candidate_payload
+
+    def poisoned(row, checks, detail, run, cfg_arg):
+        payload = original(row, checks, detail, run, cfg_arg)
+        if payload["ticker"] == "AAA":
+            payload["cautions"] = payload["cautions"] + ["You should buy this now."]
+        return payload
+
+    monkeypatch.setattr(compass_module, "_candidate_payload", poisoned)
+    with Session(engine) as session:
+        run = _mk_run(session, date(2024, 3, 20))
+        _mk_result(session, run.id, "AAA", 92.0, "A", 85.0, "B", 40.0, "C")
+        session.commit()
+        session.refresh(run)
+        with pytest.raises(ValueError, match="banned language"):
+            compass_module.evaluate_selection(session, run, cfg)
 
 
 # --- narrative (J-03) ---------------------------------------------------------------------------
@@ -337,6 +428,9 @@ def test_content_hash_stable_across_identical_rebuilds(engine, cfg, two_runs_wit
 
 
 def test_get_or_create_manifest_computes_once_then_serves_from_storage(engine, cfg, two_runs_with_phase, monkeypatch):
+    """iter-3: run_b is the FRONTIER of this fixture -- get_or_create_manifest now requires
+    producer="ingest_finalize" to mint the frontier's version 1 (J-05 step 7); TC-1's "zero ADDITIONAL
+    producer calls on the warm hit" property is unchanged once minted."""
     run_a_id, run_b_id = two_runs_with_phase
     calls = {"n": 0}
     original = compass.build_manifest_payload
@@ -349,7 +443,7 @@ def test_get_or_create_manifest_computes_once_then_serves_from_storage(engine, c
 
     with Session(engine) as session:
         run_b = session.get(ScannerRun, run_b_id)
-        first_row = compass.get_or_create_manifest(session, run_b, cfg)
+        first_row = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
         assert calls["n"] == 1
         second_row = compass.get_or_create_manifest(session, run_b, cfg)
         assert calls["n"] == 1  # TC-1: zero ADDITIONAL producer calls on the warm hit
@@ -361,17 +455,51 @@ def test_get_or_create_manifest_computes_once_then_serves_from_storage(engine, c
         assert len(rows) == 1  # never duplicated
 
 
+def test_get_or_create_manifest_never_mints_frontier_on_plain_get(engine, cfg, two_runs_with_phase):
+    """J-05 step 7 / TC-8: a plain (non-finalize) call for the CURRENT frontier with no manifest yet
+    raises ManifestNotYetFrozen -- never silently fabricates one."""
+    _run_a_id, run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_b = session.get(ScannerRun, run_b_id)
+        with pytest.raises(compass.ManifestNotYetFrozen):
+            compass.get_or_create_manifest(session, run_b, cfg)
+    with Session(engine) as session:
+        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 4, 8))).all()
+        assert rows == []  # no partial/fabricated row was written
+
+
+def test_get_or_create_manifest_historical_asof_still_create_once_mints(engine, cfg, two_runs_with_phase):
+    """A HISTORICAL (non-frontier) as_of still create-once-mints on a plain GET-style call (path b) --
+    only the CURRENT frontier is guarded."""
+    run_a_id, _run_b_id = two_runs_with_phase
+    with Session(engine) as session:
+        run_a = session.get(ScannerRun, run_a_id)
+        row = compass.get_or_create_manifest(session, run_a, cfg)
+    assert row.mode == "retrospective"
+    assert row.prospective_eligible is False
+
+
 def test_manifest_row_payload_matches_build_manifest_payload_content(engine, cfg, two_runs_with_phase):
     run_a_id, run_b_id = two_runs_with_phase
     with Session(engine) as session:
         run_a = session.get(ScannerRun, run_a_id)
         run_b = session.get(ScannerRun, run_b_id)
         built = compass.build_manifest_payload(session, run_b, run_a, cfg)
-        row = compass.get_or_create_manifest(session, run_b, cfg)
+        row = compass.get_or_create_manifest(session, run_b, cfg, producer="ingest_finalize")
         served = compass.manifest_row_payload(row)
     assert served["session_delta"] == built["session_delta"]
     assert served["narrative"] == built["narrative"]
-    assert served["selection"] == built["selection"]
+    # iter-3: comparison_cohort/near_threshold_shadow/member_count are LIFTED OUT of the served
+    # "selection" block into their own top-level keys (universe.member_count) -- reassemble built's
+    # shape the SAME way before comparing (single source, not a shape mismatch).
+    built_selection = dict(built["selection"])
+    built_comparison_cohort = built_selection.pop("comparison_cohort")
+    built_near_threshold_shadow = built_selection.pop("near_threshold_shadow")
+    built_member_count = built_selection.pop("member_count")
+    assert served["selection"] == built_selection
+    assert served["comparison_cohort"] == built_comparison_cohort
+    assert served["near_threshold_shadow"] == built_near_threshold_shadow
+    assert served["universe"]["member_count"] == built_member_count
     assert served["content_hash"] == built["content_hash"]
 
 
diff --git a/apps/backend/tests/test_ingest_finalize_compass.py b/apps/backend/tests/test_ingest_finalize_compass.py
index b9b4b96e..b76e2cde 100644
--- a/apps/backend/tests/test_ingest_finalize_compass.py
+++ b/apps/backend/tests/test_ingest_finalize_compass.py
@@ -66,7 +66,7 @@ def test_compass_content_phase_persists_manifest_and_reports_refreshed(finalize_
     cfg = load_config()
     with Session(finalize_engine) as session:
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, _progress())
-    assert "next_session_manifest" in refreshed
+    assert "next-session_manifest" in refreshed
     assert "market_phase" in refreshed  # the pre-existing phase this one is inserted after still ran
 
     with Session(finalize_engine) as session:
@@ -87,7 +87,7 @@ def test_compass_content_failure_is_isolated_forward_aggregates_still_runs(final
         with Session(finalize_engine) as session:
             refreshed = data_manager._refresh_ingest_aggregates(session, cfg, _progress())
 
-    assert "next_session_manifest" not in refreshed  # honestly NOT reported as refreshed -- it failed
+    assert "next-session_manifest" not in refreshed  # honestly NOT reported as refreshed -- it failed
     assert "forward_aggregates" in refreshed  # the NEXT phase still ran -- isolation held
     assert any("compass-content warm failed" in record.message for record in caplog.records)
 
@@ -104,4 +104,4 @@ def test_compass_content_is_a_noop_when_no_new_snapshot_dates(finalize_engine):
     prog.new_snapshot_dates = []
     with Session(finalize_engine) as session:
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
-    assert "next_session_manifest" not in refreshed
+    assert "next-session_manifest" not in refreshed
diff --git a/apps/frontend/app/page.tsx b/apps/frontend/app/page.tsx
index d8bb34ab..63a205fb 100644
--- a/apps/frontend/app/page.tsx
+++ b/apps/frontend/app/page.tsx
@@ -9,6 +9,7 @@ import { ComponentBreakdown } from "@/components/component-breakdown";
 import { CompassSummaryCard } from "@/components/compass-summary-card";
 import { CompassWhatChangedCard } from "@/components/compass-whatchanged-card";
 import { CompassFocusSection } from "@/components/compass-focus-section";
+import { CompassManifestStrip } from "@/components/compass-manifest-strip";
 import { MarketPhaseCard } from "@/components/market-phase-card";
 import { PhaseCrossViewCard } from "@/components/phase-cross-view-card";
 import { PageHeading } from "@/components/page-heading";
@@ -137,10 +138,14 @@ export default function DashboardPage() {
           {/* goal-market-compass iter-2 (J-02/J-03/J-04): three new Today-page sections, each reading
               ONLY GET /api/compass, rendered ABOVE the existing dashboard body below. That body
               (DashboardBody and everything it renders) is UNCHANGED by this iteration — final section
-              ordering/chrome placement is J-07's job, and removing it from `/` is J-08's job. */}
+              ordering/chrome placement is J-07's job, and removing it from `/` is J-08's job.
+              iter-3 (J-05/J-06) appends the manifest strip as the LAST compass card, per goal.md's
+              Product Shape ordering ("...next-session focus, manifest strip") — still above the
+              unmodified DashboardBody (preserves the free in-image AG-3 cross-check, lessons.md iter-2). */}
           <CompassSummaryCard compass={state.compass} />
           <CompassWhatChangedCard compass={state.compass} />
           <CompassFocusSection compass={state.compass} />
+          <CompassManifestStrip compass={state.compass} asOf={asOf} />
           <DashboardBody
             dashboard={state.dashboard}
             phase={state.phase}
diff --git a/apps/frontend/components/compass-summary-card.tsx b/apps/frontend/components/compass-summary-card.tsx
index b7b32b10..bfa8659c 100644
--- a/apps/frontend/components/compass-summary-card.tsx
+++ b/apps/frontend/components/compass-summary-card.tsx
@@ -4,6 +4,7 @@ import { AlertTriangle } from "lucide-react";
 
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
 import { Disclosure } from "@/components/ui/disclosure";
+import { formatFactValue } from "@/lib/format-fact";
 import type { CompassResponse } from "@/lib/api";
 
 /** J-03 (goal-market-compass iter-2): the plain-English summary card. Every sentence is rendered
@@ -50,7 +51,10 @@ export function CompassSummaryCard({ compass }: { compass: CompassResponse | nul
                     {sentence.facts.map((fact) => (
                       <li key={fact.name} className="flex items-center gap-2">
                         <span className="text-text-faint">{fact.name}:</span>
-                        <span className="num text-text">{String(fact.value)}</span>
+                        {/* TC-36: a number renders rounded (e.g. "-0.20"), never a raw floating-point
+                            artifact ("-0.20000000000000284") -- display-only, the served fact value
+                            itself is unchanged. */}
+                        <span className="num text-text">{formatFactValue(fact.value)}</span>
                       </li>
                     ))}
                   </ul>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 9209404c..b77b31ee 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -984,24 +984,151 @@ export interface CompassSelection {
   candidates_empty_reason: string | null;
 }
 
-/** GET /api/compass payload (goal-market-compass iter-2) — the next-session manifest CONTENT
- *  block: what changed (J-02), the plain-English summary (J-03), and the next-session candidates
- *  (J-04), all computed ONCE per `as_of` and served from storage thereafter. `content_hash` is the
- *  sha256 of the sorted-key JSON of exactly these three blocks. */
+// --- freeze/integrity block (goal-market-compass iter-3, J-05/J-06) --------------------------
+
+/** The manifest's provenance/generation record — WHO/WHEN/HOW it was minted. `engine_identity` is the
+ *  config-listed engine-code + config-subset hash (`app.engine.engine_identity`); `preflight_verdict`
+ *  is recorded here ONLY (at-ingest mode only) — never on the market/narrative surface (AG-13). */
+export interface CompassGeneration {
+  producer: "ingest_finalize" | "on_demand_get" | "regenerate";
+  frontier_bar_date: string | null;
+  generated_at: string;
+  preflight_verdict: string | null;
+  engine_identity: string;
+  source_run_created_at: string | null;
+}
+
+export interface CompassThemeMembership {
+  theme: string;
+  rank: number | null;
+}
+
+export interface CompassAtrPct {
+  value: number | null;
+  percentile: number | null;
+}
+
+/** One frozen context row shared by `comparison_cohort` / `near_threshold_shadow` (J-05/J-06) — every
+ *  field is read from the run's own stored record, never a new computation (AG-8, AG-11: only the
+ *  existing three scores/buckets plus named structural context, nothing blended). */
+export interface CompassCohortRow {
+  ticker: string;
+  leadership_score: number;
+  leadership_bucket: string;
+  entry_quality_score: number;
+  entry_quality_bucket: string;
+  risk_score: number;
+  risk_bucket: string;
+  setup_status: string;
+  rank_in_run: number;
+  sector: string | null;
+  theme_memberships: CompassThemeMembership[];
+  close: number | null;
+  atr_pct: CompassAtrPct;
+  distance_from_52w_high: number | null;
+  gap_p95: number | null;
+  worst_20d: number | null;
+  distance_to_invalidation: number | null;
+  adv_dollars: number | null;
+}
+
+/** The closed selection_disposition vocabulary (J-05/J-06) — partitions every non-candidate member of
+ *  the run exactly; tallies sum to member_count minus candidate count. */
+export type CompassSelectionDisposition = "below_selection_floor" | "excluded_by_cap";
+
+export interface CompassComparisonCohortRow extends CompassCohortRow {
+  selection_disposition: CompassSelectionDisposition;
+}
+
+export interface CompassDatasetStamp {
+  stamp: string | null;
+}
+
+export interface CompassUniverseBlock {
+  pool_hash: string | null;
+  resolver_gate: Record<string, number>;
+  member_count: number;
+  profile: string;
+}
+
+/** The manifest's own embedded evidence caveat + survivorship/sector-basis disclosures + the
+ *  non-causal cohort-semantics sentence (AG-16) — rendered verbatim, never re-composed client-side. */
+export interface CompassCaveats {
+  evidence: string;
+  survivorship: string;
+  sector_basis: string;
+  cohort_semantics: string;
+}
+
+/** The read-time-only basis disclosure (never a mutation, never a recompute of the frozen content) —
+ *  compares the manifest's recorded source run against the CURRENT stored run for its as_of. */
+export interface CompassBasisDisclosure {
+  status: "available" | "unavailable" | "rebuilt";
+  detail: string | null;
+}
+
+/** One entry in the "both versions" summary list — present once more than one version exists for an
+ *  as_of (a confirm-gated regenerate minted a later one). */
+export interface CompassVersionSummary {
+  version: number;
+  mode: string | null;
+  frozen: boolean;
+  prospective_eligible: boolean;
+  generated_at: string | null;
+}
+
+/** GET /api/compass payload (goal-market-compass iter-2 CONTENT block; iter-3 J-05/J-06 freeze/
+ *  integrity block). Every freeze/integrity field is `null`/absent-shaped on a pre-iter-3 legacy row
+ *  ("pre-freeze era" — honestly rendered, never fabricated as frozen). `content_hash` is the sha256 of
+ *  the sorted-key JSON of the CONTENT block only; `manifest_hash` is the whole-document integrity
+ *  identity (a DIFFERENT, broader hash, excluding only itself). */
 export interface CompassResponse {
   as_of: string;
+  version: number;
+  mode: "at_ingest" | "retrospective" | null;
+  frozen: boolean;
   session_delta: SessionDelta;
   narrative: Narrative;
   selection: CompassSelection;
+  comparison_cohort: CompassComparisonCohortRow[];
+  near_threshold_shadow: CompassCohortRow[];
   content_hash: string;
-}
-
-/** Canonical next-session-manifest CONTENT source: GET /api/compass. `asof` time-travels to that
- *  date's stored (or create-once-computed) manifest — never recomputed client-side. */
+  generation: CompassGeneration | null;
+  candidate_rule_hash: string | null;
+  candidate_rule_config: Record<string, unknown> | null;
+  cohort_rule_hash: string | null;
+  cohort_rule_config: Record<string, unknown> | null;
+  manifest_config_hash: string | null;
+  manifest_config_subset: Record<string, unknown> | null;
+  dataset: CompassDatasetStamp | null;
+  universe: CompassUniverseBlock | null;
+  caveats: CompassCaveats | null;
+  prospective_eligible: boolean;
+  available_at_utc: string | null;
+  manifest_hash: string | null;
+  basis: CompassBasisDisclosure;
+  versions: CompassVersionSummary[];
+}
+
+/** Canonical next-session-manifest source: GET /api/compass. `asof` time-travels to that date's stored
+ *  (or create-once-computed, for a HISTORICAL date only) manifest — never recomputed client-side. The
+ *  CURRENT frontier with no manifest yet (not-yet-frozen) throws (404) like any other unavailable
+ *  state — callers already degrade to `compass = null` on any fetch failure. */
 export async function fetchCompass(asof?: string, signal?: AbortSignal): Promise<CompassResponse> {
   return getJSON<CompassResponse>(withAsOf("/api/compass", asof), signal);
 }
 
+/** POST /api/compass/regenerate — the confirm-gated regenerate action (J-05/J-06). Mints a NEW version
+ *  for a stored `as_of` that already has a manifest; `GET /api/compass` remains the sole read path (this
+ *  is an action route, not a second read path). Throws with the backend's honest `detail` on a non-2xx
+ *  (404 no existing manifest for this as_of) so the UI shows an explicit failure, never a silent no-op. */
+export async function regenerateManifest(asOf: string): Promise<CompassResponse> {
+  return sendJSON<CompassResponse>(
+    "POST",
+    `/api/compass/regenerate?as_of=${encodeURIComponent(asOf)}&confirm=true`,
+  );
+}
+
 // --- scanner runs (iter-5) -----------------------------------------------------------------
 /** One row in the immutable scan-run history (GET /api/runs). `regime` carries the stored as-of
  *  label+score; `candidate_counts` are the stored counts of the canonical setup statuses. */
diff --git a/config.yaml b/config.yaml
index 5e9cfb17..e16db5cb 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1445,6 +1445,29 @@ compass:
       - "act now"
       - "because of"
       - "caused by"
+  # goal-market-compass iter-3 (J-05/J-06) — the next-session manifest freeze/export tunables.
+  # `availability_margin_seconds` is a publication-latency allowance, never a research threshold.
+  manifest:
+    schema_version: "v1"
+    export_dir: "apps/backend/data/exports/next_session_manifests"
+    availability_margin_seconds: 60
+    schema_path: "docs/handoffs/trendora-next-session-manifest-v1.schema.json"
+
+# ----------------------------------------------------------------------------------------
+# goal-market-compass iter-3 (J-05/J-06) — the engine-identity stamp's own inputs. `engine_files` are
+# repo-root-relative paths whose CONTENT is hashed; `config_keys` are dotted config paths whose VALUES
+# are hashed. Together they define what `app.engine.engine_identity.compute_engine_identity` is
+# sensitive to — stamped on every manifest's `generation.engine_identity` and on newly created
+# `scanner_runs` rows (old rows stay NULL, "pre-stamping era", never backfilled).
+provenance:
+  engine_files:
+    - "apps/backend/app/engine/compass.py"
+    - "apps/backend/app/engine/session_delta.py"
+    - "apps/backend/app/engine/engine_identity.py"
+  config_keys:
+    - "compass.selection"
+    - "compass.delta"
+    - "compass.manifest"
 
 # ----------------------------------------------------------------------------------------
 # iter-12 CONSUMED — Methodology / Glossary catalog (J-12). The SINGLE config-backed source that
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/security/install-decisions.jsonl           |  1 +
 .../goal-session-market-compass/.engine.lock/epoch |  2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |  2 +-
 runs/goal-session-market-compass/engine.pid        |  2 +-
 .../iter-3/goal-slice.md                           | 63 +++++++++++++++++++++-
 runs/goal-session-market-compass/telemetry.jsonl   | 14 +++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  2 +
 8 files changed, 83 insertions(+), 5 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
