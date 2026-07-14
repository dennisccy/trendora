# Iteration diff (bounded)

Files changed: 18. Shown in full: 17.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (102 diff lines)

```diff
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 75baa34..3969f55 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -27,6 +27,7 @@ from sqlmodel import Session
 from app.config import get_config
 from app.db import get_engine, get_session
 from app.engine import data_manager, scanner
+from app.engine.drift import read_drift_report
 from app.engine.prices import latest_data_date
 
 router = APIRouter(tags=["data"])
@@ -138,6 +139,10 @@ def data_overview(
         # iter-24 fast-platform item K: the DB storage-footprint snapshot (file size + row counts) —
         # additive, pure DB introspection over stored rows; no canonical value recomputed.
         "capacity": data_manager.compute_capacity(session, cfg),
+        # iter-35 (J-21/B-304): the live-vs-seed drift report — the SAME reader `compute_preflight` uses
+        # (`read_drift_report`, a tiny-file read; no recompute, no second parse path). `None` when no
+        # fetch has run yet (honest inert — the frontend renders a quiet "no fetch yet" state, not clean).
+        "drift": read_drift_report(),
     }
 
 
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 61918bc..5c717cd 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -545,17 +545,18 @@ class ReadinessCfg(BaseModel):
         negative override, via a temporary `TRENDORA_CONFIG` alt-file) is the sanctioned lever for
         inducing the DEGRADED/NO-GO test states without mutating committed seed data.
       - `severity` — which verdict a breached component forces, keyed by component name (`servability` /
-        `freshness` / `integrity`): `"degraded"` or `"no-go"`. Owner-reviewed config (B-301's "making
-        NO-GO too easy is alarm fatigue" trap) — MUST cover all three components and include at least one
-        `"degraded"` and one `"no-go"` entry so both states are inducible for the fixture matrix.
+        `freshness` / `integrity` / `drift`, the last added iter-35 for J-21/B-304): `"degraded"` or
+        `"no-go"`. Owner-reviewed config (B-301's "making NO-GO too easy is alarm fatigue" trap) — MUST
+        cover all four components and include at least one `"degraded"` and one `"no-go"` entry so both
+        states are inducible for the fixture matrix.
       - `verdict_history_path` — the append-only verdict-transition log path (written only when the
         verdict changes, never on every ~2s poll). A relative path resolves against the repo root; the
         `READINESS_VERDICT_HISTORY_PATH` env override takes precedence (test/gate seam — mirrors
         `app.engine.evidence.LEDGER_PATH_ENV`).
 
-    Boot-validated: `severity` must name exactly `{servability, freshness, integrity}` with every value
-    one of `"degraded"`/`"no-go"`, covering both. An invalid block raises `ConfigError`, never a silent
-    default."""
+    Boot-validated: `severity` must name exactly `{servability, freshness, integrity, drift}` with every
+    value one of `"degraded"`/`"no-go"`, covering both. An invalid block raises `ConfigError`, never a
+    silent default."""
 
     model_config = ConfigDict(extra="allow")
     freshness_max_age_days: int
@@ -564,7 +565,7 @@ class ReadinessCfg(BaseModel):
 
     @model_validator(mode="after")
     def _validate(self) -> "ReadinessCfg":
-        required_components = {"servability", "freshness", "integrity"}
+        required_components = {"servability", "freshness", "integrity", "drift"}
         missing = sorted(required_components - set(self.severity))
         if missing:
             raise ValueError(f"readiness.severity missing components: {missing}")
@@ -2174,6 +2175,58 @@ class RegistryCfg(BaseModel):
     enforce: bool = False
 
 
+_DEFAULT_DRIFT_REPORT_PATH = "runs/goal-session-mcp-loop/state/drift-report.json"
+
+
+class DriftCfg(BaseModel):
+    """Live-vs-seed drift monitor tunables (goal-mcp-loop iter-35, J-21 / backlog B-304 — OVERLAP CHECK
+    ONLY). `app.engine.drift` reads every tunable from here — no magic number in the module or in
+    `data_manager`'s post-fetch wiring (anti-goal: No magic numbers).
+
+      - `enabled` — DEFAULT-ON gate for the post-fetch validation stage in `data_manager._run_job`; an
+        emergency off-switch (`False` skips the stage entirely — byte-identical to pre-iter-35 fetch
+        behavior), never the shipped default.
+      - `overlap_days` — how many of the most recent dates COMMON to a fetch and the committed seed are
+        byte/fixed-precision compared (a BOUNDED per-symbol window, never the whole history — the
+        iter-24/26 anti-goal-#8 lesson). MUST be `>= 1`.
+      - `report_path` — the drift-report artifact location. Resolved relative to `REPO_ROOT` when
+        relative; the resolver (`app.engine.drift.resolve_drift_report_path`, NOT this model) applies
+        the runtime `TRENDORA_DRIFT_REPORT_PATH` override, mirroring `EvidenceCfg.ledger_path` /
+        `resolve_ledger_path()` exactly.
+
+    Boot-validated: `overlap_days >= 1`. Default-populated so a config / inline test fixture predating
+    this block still loads unchanged — the stage stays INERT (no artifact ever written) until an actual
+    fetch runs, so adding this block alone changes no committed-seed behavior."""
+
+    model_config = ConfigDict(extra="allow")
+    enabled: bool = True
+    overlap_days: int = 20
+    report_path: str = Field(default=_DEFAULT_DRIFT_REPORT_PATH, min_length=1)
+
+    @model_validator(mode="after")
+    def _validate(self) -> "DriftCfg":
+        if self.overlap_days < 1:
+            raise ValueError(f"data_quality.drift.overlap_days must be >= 1, got {self.overlap_days}")
+        return self
+
+
+class DataQualityCfg(BaseModel):
+    """Data-integrity report tunables (goal-mcp-loop iter-35). Currently carries only the live-vs-seed
+    drift monitor (`drift`); the DEFERRED B-304 sub-checks (distribution envelope, the B-113-dependent
+    junction seam scan) plug into this SAME block when they land (never a parallel config block).
+    Default-populated so a config / inline test fixture predating this block still loads unchanged."""
+
+    model_config = ConfigDict(extra="allow")
+    drift: DriftCfg = Field(default_factory=DriftCfg)
+
+
+def _default_data_quality() -> "DataQualityCfg":
+    """The built-in default data-quality config — used when a config predating the block (or an inline
+    test fixture) omits `data_quality`. The real `config.yaml` restates it explicitly as the single
+    documented source."""
+    return DataQualityCfg()
+
+
 class EvidenceCfg(BaseModel):
     """Read-side evidence config (goal-mcp-loop iter-1; iter-9 adds the staging economy; iter-30 adds the
     pre-registration registry). `ledger_path` is the certified-claims ledger the read-only `GET
@@ -2259,6 +2312,10 @@ class Config(BaseModel):
     # populated so a config / inline test fixture predating it still loads; the real `config.yaml` restates
     # the gate's certified-claims ledger path explicitly as the single documented source.
     evidence: EvidenceCfg = Field(default_factory=_default_evidence)
+    # goal-mcp-loop iter-35 (J-21 / backlog B-304) — the live-vs-seed drift monitor's config (overlap
+    # check only). Default-populated so a config / inline test fixture predating it still loads
+    # unchanged; the real `config.yaml` restates it explicitly as the single documented source.
+    data_quality: DataQualityCfg = Field(default_factory=_default_data_quality)
 
     @field_validator("themes")
     @classmethod
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 7afb151..e5e1381 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -48,9 +48,10 @@ from sqlmodel import Session, select
 
 from app.config import Config, ImportChunkingCfg, ProviderCatalogEntry, get_config
 from app.data_providers import make_provider
-from app.data_providers.base import PriceProvider, ProviderUnavailableError, RateLimitError
-from app.data_providers.seed_provider import symbol_to_filename
+from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
+from app.data_providers.seed_provider import SeedProvider, symbol_to_filename
 from app.db import get_engine
+from app.engine import drift as drift_module
 from app.engine import forward_testing, scanner
 from app.engine.prices import attach_shared_cache, bar_cache, bars_asof, latest_data_date, prefilled_bar_cache
 from app.engine import universe_resolver
@@ -2191,6 +2192,8 @@ def _run_chunked_fetch(
     sleep_fn: Callable[[float], None],
     start_chunk: int,
     covered_chunks: Optional[set[int]] = None,
+    overlap_sink: Optional[dict[str, list[Bar]]] = None,
+    overlap_days: int = 0,
 ) -> None:
     """Run the chunk plan from `start_chunk`, persisting the checkpoint AFTER each completed chunk (so
     `next_chunk_index` only advances once a chunk's bars are durably committed). Within EACH chunk the
@@ -2209,7 +2212,15 @@ def _run_chunked_fetch(
         skipped by `_existing_dates`, so no duplicate fetch of committed bars.
       * a non-429 `ProviderUnavailableError` for a symbol ⇒ count it failed, record a REDACTED error
         (the resolved key scrubbed on THIS thread), and continue the chunk — unchanged semantics.
-    """
+
+    iter-35 (J-21/B-304): when `overlap_sink` is given, every "ok" result's freshly-fetched bars are
+    accumulated into it (keyed by symbol), trimmed to the last `overlap_days` entries per symbol as they
+    arrive — a BOUNDED per-symbol window, never the whole fetched history (the iter-24/26 anti-goal-#8
+    lesson). This captures the RAW fetch BEFORE the `_existing_dates` new-only filter below, because a
+    date already covered by a prior fetch/backfill is exactly the "overlap" the live-vs-seed drift check
+    needs to see — the INSERT-new-only DB write silently discards a re-adjusted value for an
+    already-stored date, so the drift artifact must be built from what the provider ACTUALLY returned,
+    never a DB re-read. `overlap_sink` defaults to `None`, so every pre-iter-35 call site is unaffected."""
     chunking = cfg.data_manager.import_chunking
     workers = chunking.fetch_workers  # the bounded pool size (config — No magic numbers)
     covered_chunks = covered_chunks or set()
@@ -2256,6 +2267,15 @@ def _run_chunked_fetch(
                 _record_error(prog, scrub(res.error or f"{res.symbol}: provider error"))
                 prog.message = _fetch_message(prog)
                 continue
+            if overlap_sink is not None and res.bars:
+                # iter-35 (J-21/B-304): capture the RAW fetch for the post-fetch drift check, bounded to
+                # the last `overlap_days` bars per symbol (see the docstring above) -- independent of
+                # whether these dates end up written below (an already-covered date is exactly what the
+                # overlap check needs to see, and INSERT-new-only would otherwise hide it).
+                bucket = overlap_sink.setdefault(res.symbol, [])
+                bucket.extend(res.bars)
+                if overlap_days > 0 and len(bucket) > overlap_days:
+                    del bucket[:-overlap_days]
             already = _existing_dates(session, res.symbol, ws, we)
             for bar in res.bars:
                 if bar.date not in already:
@@ -2284,6 +2304,50 @@ def _run_chunked_fetch(
         _advance_checkpoint(session, checkpoint, prog, next_idx=chunk_idx + 1, status="running")
 
 
+# --------------------------------------------------------------------------------------------------
+# iter-35 (J-21/B-304) -- the post-fetch live-vs-seed drift validation stage
+# --------------------------------------------------------------------------------------------------
+def _check_drift(
+    cfg: Config,
+    seed_dir: Path,
+    fetched_bars: dict[str, list[Bar]],
+    prog: JobProgress,
+    scrub: Callable[[str], str],
+) -> None:
+    """The post-fetch validation stage (J-21/B-304): byte/fixed-precision compare this job's freshly-
+    fetched bars (`overlap_sink`, accumulated by `_run_chunked_fetch`) against the COMMITTED SEED CSVs
+    (via the SAME `SeedProvider` the offline default path reads — no second CSV parser) over the
+    configured overlap window, and persist the SINGLE drift-report artifact via
+    `app.engine.drift.write_drift_report` (re-read by `compute_preflight` and `GET /api/data`). A symbol
+    with no committed seed history (e.g. a brand-new universe member) is honestly skipped — no crash, no
+    fabricated comparison.
+
+    Best-effort: this is a VALIDATION side-check, never the primary job — any failure here is recorded
+    (scrubbed, so a redacted key never leaks) and SWALLOWED, mirroring the `_create_run_record`
+    bookkeeping-failure discipline elsewhere in this module. It NEVER mutates/reconciles the fetched bars
+    (B-304 "Do NOT touch the fetched data") and never queries the DB (a tiny per-symbol CSV read only)."""
+    if not fetched_bars:
+        return  # nothing was actually fetched this job (e.g. every symbol failed) -- nothing to compare
+    try:
+        seed_provider = SeedProvider(seed_dir)
+        seed_bars: dict[str, list[Bar]] = {}
+        for symbol in fetched_bars:
+            try:
+                seed_bars[symbol] = seed_provider.get_daily(symbol)
+            except ProviderUnavailableError:
+                continue  # no committed seed history for this symbol -- honest skip, not a crash
+        report = drift_module.build_drift_report(
+            fetched_bars, seed_bars,
+            overlap_days=cfg.data_quality.drift.overlap_days,
+            # a DETERMINISTIC job parameter (never `date.today()` -- anti-goal #5), mirroring the J-20
+            # freshness-anchor precedent.
+            reference=prog.end.isoformat(),
+        )
+        drift_module.write_drift_report(report)
+    except Exception as exc:  # noqa: BLE001 -- a drift-check failure must not crash the fetch job
+        _record_error(prog, scrub(f"drift check failed: {exc}"))
+
+
 def _compute_one_backfill_date(
     eng: Engine, cfg: Config, d: date_cls, shared_cache
 ) -> tuple[date_cls, Optional[dict], float]:
@@ -3023,6 +3087,10 @@ def _run_job(
     # not forked); they differ only in the symbol set (all seed symbols vs the committed POOL) and in the
     # EXTRA screen step expand runs afterward.
     pool: list[dict] = []
+    # iter-35 (J-21/B-304): the bounded per-symbol accumulator `_run_chunked_fetch` fills with this job's
+    # RAW freshly-fetched bars (tail-trimmed to `overlap_days`) for the post-fetch drift check below. Left
+    # `None` when the feature is config-disabled, so `_run_chunked_fetch` skips the accumulation entirely.
+    overlap_sink: Optional[dict[str, list]] = {} if cfg.data_quality.drift.enabled else None
     checkpoint: Optional[ImportCheckpoint] = None  # hoisted: an expand finalizes it AFTER the screen step
     backfill_failed = False  # J-59: a `both`/`backfill` backfill-stage failure (drives failed_backfill)
     # J-60: create the run-history record IMMEDIATELY (status `running`) so the job appears in Run history
@@ -3087,6 +3155,7 @@ def _run_job(
                     session, cfg, prog, live, chunks=chunks, checkpoint=checkpoint,
                     scrub=scrub, sleep_fn=sleep_fn, start_chunk=start_chunk,
                     covered_chunks=covered_chunks,
+                    overlap_sink=overlap_sink, overlap_days=cfg.data_quality.drift.overlap_days,
                 )
                 # J-59: record fetch-stage completion (so a `both`/`backfill` resume skips it; the durable
                 # checkpoint mirrors it). Only when the fetch actually completed (not on a graceful pause).
@@ -3101,6 +3170,11 @@ def _run_job(
                     items_processed=prog.symbols_ok + prog.symbols_failed,
                     concurrency=cfg.data_manager.import_chunking.fetch_workers,
                 )
+                # iter-35 (J-21/B-304): the post-fetch drift validation stage -- ONLY when the fetch
+                # actually completed (never on a `resumable` pause, whose chunk's bars were discarded, not
+                # committed) and the feature is config-enabled (`overlap_sink` is None when disabled).
+                if overlap_sink is not None and prog.status != "resumable":
+                    _check_drift(cfg, seed_dir, overlap_sink, prog, scrub)
                 if prog.status == "resumable":
                     paused = True  # graceful pause — checkpoint already persisted resumable
                 elif not is_expand:
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index 6262452..bfdfbdd 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -32,6 +32,7 @@ from sqlalchemy import func
 from sqlmodel import Session, select
 
 from app.config import REPO_ROOT, Config, get_config
+from app.engine import drift as drift_module
 from app.engine.evidence import resolve_ledger_path
 from app.engine.graveyard import resolve_staging_ledger_path
 from app.engine.ledger import append_entry, read_entries
@@ -214,7 +215,7 @@ def _ledger_file_ok(path: str) -> tuple[bool, str]:
 
 
 def compute_preflight(session: Session, config: Optional[Config] = None) -> dict:
-    """Compute the single daily preflight verdict (Data Contract value) — a PURE composition over three
+    """Compute the single daily preflight verdict (Data Contract value) — a PURE composition over four
     inputs that exist now, recomputing none of them:
 
       - **servability** — reuses `compute_readiness`'s OWN liveness check verbatim (no second
@@ -227,6 +228,13 @@ def compute_preflight(session: Session, config: Optional[Config] = None) -> dict
       - **DB/ledger integrity** — the DB is reachable AND the canonical/staging/registry JSONL files
         (`resolve_ledger_path` / `resolve_staging_ledger_path` / `resolve_registry_path` — the EXACT
         existing resolvers, never duplicated) exist and parse. Tiny-file reads only.
+      - **drift** (iter-35, J-21 / backlog B-304) — the live-vs-seed overlap-check artifact, re-read
+        VERBATIM via `app.engine.drift.read_drift_report()` (a tiny-file read, never a DB query/scan —
+        anti-goal #8, mirroring the integrity component above). `ok` when the artifact is ABSENT (no
+        fetch has run yet — servability/freshness/integrity behave IDENTICALLY to a pre-iter-35 backend
+        in this case, the J-20 non-regression guarantee) or its `status == "clean"`; breached when
+        `status == "drift"` (the detail names every affected symbol) or the artifact exists but could
+        not be parsed (an honest degraded reason — never silently treated as clean).
 
     The overall verdict is the WORST of every breached component's configured severity (`GO` when
     nothing is breached). Returns `{verdict, reasons, components, as_of, reference}` (the spec names the
@@ -306,6 +314,29 @@ def compute_preflight(session: Session, config: Optional[Config] = None) -> dict
         else "Integrity check failed: " + "; ".join(problems) + ".",
     )
 
+    # --- drift: the live-vs-seed overlap-check artifact (iter-35, J-21 / backlog B-304) — a tiny-file
+    # read via the SINGLE reader `read_drift_report`, never a DB query/scan (anti-goal #8). A MISSING
+    # artifact means no fetch has run yet (honest inert -> ok, byte-identical to a pre-iter-35 backend);
+    # `status == "clean"` -> ok; `status == "drift"` -> breached, naming every affected symbol; any other
+    # status (the artifact exists but could not be parsed) -> breached with an honest degraded reason,
+    # never silently treated as clean.
+    drift_report = drift_module.read_drift_report()
+    if drift_report is None:
+        _apply("drift", True, "No fetch has run yet — nothing to compare against the committed seed.")
+    elif drift_report.get("status") == drift_module.STATUS_CLEAN:
+        _apply("drift", True, "The most recent fetch matched the committed seed over the overlap window.")
+    elif drift_report.get("status") == drift_module.STATUS_DRIFT:
+        symbols = sorted(a.get("symbol", "?") for a in drift_report.get("affected") or [])
+        _apply(
+            "drift", False,
+            "Live-vs-seed drift detected (adjustment seam) for: " + ", ".join(symbols) + ".",
+        )
+    else:
+        _apply(
+            "drift", False,
+            "Drift report is unreadable: the artifact exists but could not be parsed.",
+        )
+
     reference = latest_data.isoformat() if latest_data else None
     return {
         "verdict": verdict,
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index 880fa8c..3edb683 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -110,6 +110,33 @@ def test_get_data_overview_carries_capacity_snapshot(data_api_engine):
     assert cap["db_file_bytes"] > 0  # a real file-backed temp DB
 
 
+def test_get_data_overview_carries_absent_drift_on_a_cold_db(data_api_engine, monkeypatch, tmp_path):
+    """iter-35 (J-21/B-304): GET /api/data carries an additive `drift` key — the SAME reader
+    `compute_preflight` uses (`read_drift_report`). On a cold DB with no fetch ever run, the artifact is
+    absent -> `None` (honest inert), served as a normal 200 -- never a 500."""
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "never-written-drift-report.json"))
+    with Session(data_api_engine) as session:
+        payload = data_overview(session=session)
+    assert "drift" in payload  # additive — every existing key stays present
+    assert payload["drift"] is None
+
+
+def test_get_data_overview_drift_field_equals_read_drift_report_verbatim(data_api_engine, monkeypatch, tmp_path):
+    """The served `drift` field is the SINGLE reader's output verbatim — no recompute, no second parse
+    path (the Data Contract single-source requirement)."""
+    from app.engine.drift import write_drift_report
+
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "written-drift-report.json"))
+    written = {
+        "status": "drift", "reference": "2024-03-01", "overlap_days": 20,
+        "affected": [{"symbol": "AAPL", "mismatching_dates": ["2024-02-28"], "classification": "adjustment_seam"}],
+    }
+    write_drift_report(written)
+    with Session(data_api_engine) as session:
+        payload = data_overview(session=session)
+    assert payload["drift"] == written
+
+
 def test_get_data_availability_shape(data_api_engine):
     """J-61 — GET /api/data/availability returns the per-trading-date availability payload over the SAME
     bars `compute_coverage` reads. On the tiny fixture (two SPY days, no other symbols, no snapshots):
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 2c83653..405889c 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -147,11 +147,11 @@ MINIMAL_VALID = {
         "health_poll_idle_interval_seconds": 30.0,
     },
     # iter-33 made `readiness` required (the daily preflight-verdict tunables come from config, never
-    # code): the freshness threshold + the per-component severity map (must cover all three components
-    # and include at least one "degraded" and one "no-go").
+    # code): the freshness threshold + the per-component severity map (must cover all four components —
+    # iter-35 added `drift` — and include at least one "degraded" and one "no-go").
     "readiness": {
         "freshness_max_age_days": 5,
-        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
         "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
     },
     # iter-6 made `walk_forward` required (forward-testing params come from config, never code).
diff --git a/apps/backend/tests/test_config_engine.py b/apps/backend/tests/test_config_engine.py
index f74f533..b02abdf 100644
--- a/apps/backend/tests/test_config_engine.py
+++ b/apps/backend/tests/test_config_engine.py
@@ -147,7 +147,7 @@ VALID = {
     # iter-33 made `readiness` required (daily preflight-verdict tunables come from config, never code).
     "readiness": {
         "freshness_max_age_days": 5,
-        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
         "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
     },
     # iter-6 made `walk_forward` required (forward-testing params come from config, never code).
diff --git a/apps/backend/tests/test_data_manager_jobs_pipeline.py b/apps/backend/tests/test_data_manager_jobs_pipeline.py
index 7dcdfc4..5f67437 100644
--- a/apps/backend/tests/test_data_manager_jobs_pipeline.py
+++ b/apps/backend/tests/test_data_manager_jobs_pipeline.py
@@ -16,15 +16,18 @@ wall-clock). J-67 (transaction-sound parallel backfill + per-date isolation) liv
 """
 from __future__ import annotations
 
+import csv
 import json
 from datetime import date
+from pathlib import Path
 
 import pytest
 from sqlalchemy import func
 from sqlmodel import Session, select
 
 from app.config import load_config
-from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
+from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
+from app.data_providers.seed_provider import symbol_to_filename
 from app.db import create_db_and_tables, make_engine
 from app.engine import data_manager, scanner
 from app.engine.data_manager import (
@@ -38,6 +41,7 @@ from app.engine.data_manager import (
     sweep_orphaned_runs,
     unfinished_imports,
 )
+from app.engine.drift import read_drift_report
 from app.models import DailyPrice, DataProviderRun, ImportCheckpoint, ScannerRun
 from app.seed_loader import load_seed, price_load_symbols
 
@@ -496,3 +500,171 @@ def test_stage_checkpoint_survives_restart_resume_at_backfill(tmp_path, monkeypa
     with Session(fresh_engine) as session:
         for d in in_range:
             assert scanner.get_run_for_date(session, d) is not None
+
+
+# ==================================================================================================
+# iter-35 (J-21/B-304) — the post-fetch drift validation stage: runs end-to-end on a completed fetch,
+# does NOT run on a resumable pause, does NOT re-run on a skip-fetch/backfill-only resume
+# ==================================================================================================
+def _light_fetch_engine(tmp_path, name: str):
+    """A tiny engine for the drift-wiring tests below: schema only, NO committed-seed load. These tests
+    fetch exactly one synthetic symbol and need no universe/sector/theme data, so they deliberately skip
+    `load_seed`'s expensive full 30-year/590-symbol seed (unlike `_fresh_seed_engine` above) — narrower,
+    faster, and avoids inflating this file's already-heavy total fixture-setup cost with four MORE full
+    seed loads for tests that don't need one."""
+    cfg = load_config()
+    engine = make_engine(f"sqlite:///{tmp_path / f'{name}.db'}")
+    create_db_and_tables(engine)
+    return cfg, engine
+
+
+class _FixedBarsProvider(PriceProvider):
+    """Returns a FIXED, pre-configured set of bars per symbol (deterministic — drives a real drift
+    comparison through the actual fetch pipeline, not just `build_drift_report` in isolation). Counts
+    calls so a test can assert ZERO provider calls on a skip-fetch resume."""
+
+    def __init__(self, bars_by_symbol: dict[str, list[Bar]]):
+        self._bars = bars_by_symbol
+        self.calls = 0
+
+    def get_daily(self, symbol, start=None, end=None):
+        self.calls += 1
+        bars = self._bars.get(symbol, [])
+        return [b for b in bars if (start is None or b.date >= start) and (end is None or b.date <= end)]
+
+
+def _write_seed_csv(seed_dir: Path, symbol: str, bars: list[Bar]) -> None:
+    """A tiny committed-seed CSV for ONE symbol, in the exact `SeedProvider`-readable shape (mirrors
+    `data_manager._write_universe_csv`'s header/column shape)."""
+    prices_dir = seed_dir / "prices"
+    prices_dir.mkdir(parents=True, exist_ok=True)
+    path = prices_dir / symbol_to_filename(symbol)
+    with path.open("w", newline="") as fh:
+        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
+        writer.writeheader()
+        for bar in bars:
+            writer.writerow({
+                "date": bar.date.isoformat(), "open": bar.open, "high": bar.high,
+                "low": bar.low, "close": bar.close, "volume": bar.volume,
+            })
+
+
+def test_drift_stage_writes_report_on_completed_fetch_end_to_end(tmp_path, monkeypatch):
+    """A REAL fetch through the full `_run_job` pipeline, with a committed seed CSV re-adjusted vs the
+    live provider's return, proves the drift artifact is correctly written end-to-end (not merely that
+    `build_drift_report` works in isolation — this is the wiring itself)."""
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
+    cfg, engine = _light_fetch_engine(tmp_path, "drift_e2e")
+    d = date(2024, 3, 1)
+    _seed_calendar(engine, [d])  # AAA has no prior bars -> the fetch is NOT J-59-covered, it really runs
+
+    seed_dir = tmp_path / "seed_e2e"
+    _write_seed_csv(seed_dir, "AAA", [Bar(date=d, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)])
+    # the "live" fetch returns a RE-ADJUSTED close for the same date -- an adjustment seam.
+    provider = _FixedBarsProvider({"AAA": [Bar(date=d, open=100.0, high=101.0, low=99.0, close=95.0, volume=1000.0)]})
+
+    job = create_job("fetch", d, d)
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep,
+        seed_dir=seed_dir, symbols=["AAA"],
+    )
+    assert summary["status"] == "ok"
+    report = read_drift_report()
+    assert report is not None
+    assert report["status"] == "drift"
+    assert report["affected"] == [
+        {"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}
+    ]
+
+
+def test_drift_stage_writes_clean_report_when_fetch_matches_seed(tmp_path, monkeypatch):
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
+    cfg, engine = _light_fetch_engine(tmp_path, "drift_clean_e2e")
+    d = date(2024, 3, 1)
+    _seed_calendar(engine, [d])
+
+    seed_dir = tmp_path / "seed_clean_e2e"
+    bar = Bar(date=d, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)
+    _write_seed_csv(seed_dir, "AAA", [bar])
+    provider = _FixedBarsProvider({"AAA": [bar]})  # byte-identical re-fetch
+
+    job = create_job("fetch", d, d)
+    run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep,
+        seed_dir=seed_dir, symbols=["AAA"],
+    )
+    report = read_drift_report()
+    assert report is not None and report["status"] == "clean" and report["affected"] == []
+
+
+def test_drift_stage_does_not_run_on_a_resumable_pause(tmp_path, monkeypatch):
+    """A persistent-429 fetch pauses `resumable` -- the chunk's bars were DISCARDED (never committed), so
+    the drift stage must NOT run (there is nothing durably fetched to honestly compare)."""
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
+    cfg, engine = _light_fetch_engine(tmp_path, "drift_resumable")
+    d = date(2024, 3, 1)
+    _seed_calendar(engine, [d])
+
+    class _Always429(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            raise RateLimitError("HTTP 429 at https://provider/x")
+
+    job = create_job("fetch", d, d)
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_Always429(), sleep_fn=_noop_sleep,
+        seed_dir=tmp_path / "unused_seed", symbols=["AAA"],
+    )
+    assert summary["status"] == "resumable"
+    assert read_drift_report() is None  # the stage never ran -- nothing written
+
+
+def test_drift_stage_does_not_rerun_on_skip_fetch_backfill_only_resume(tmp_path, monkeypatch):
+    """A `both` job whose FETCH stage completes (writing a real drift artifact) but whose BACKFILL stage
+    fails resumes at the backfill stage with ZERO provider calls (J-59) -- the drift stage, which lives
+    entirely inside the fetch branch, must NOT re-run on that resume: a resumed fetch with a provider that
+    WOULD produce a different (drift) result if the fetch stage actually re-ran must leave the ORIGINAL
+    artifact byte-identical."""
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_path / "drift-report.json"))
+    cfg, engine = _light_fetch_engine(tmp_path, "drift_skip_fetch")
+    d = date(2024, 3, 1)
+    _seed_calendar(engine, [d])
+
+    seed_dir = tmp_path / "seed_skip_fetch"
+    bar = Bar(date=d, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)
+    _write_seed_csv(seed_dir, "AAA", [bar])
+    provider = _FixedBarsProvider({"AAA": [bar]})  # clean -- byte-identical re-fetch
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced backfill fault")
+
+    job = create_job("both", d, d)
+    with monkeypatch.context() as fault_mp:  # scoped -- restores compute_run_payload without undoing
+        fault_mp.setattr(scanner, "compute_run_payload", _boom)  # the env var set above
+        summary = run_data_job(
+            job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep,
+            seed_dir=seed_dir, symbols=["AAA"],
+        )
+    assert summary["status"] in ("partial", "failed")
+    first_report = read_drift_report()
+    assert first_report is not None and first_report["status"] == "clean"
+
+    with Session(engine) as session:
+        cp = get_checkpoint(session, job.job_id)
+        assert cp is not None and cp.status == "failed_backfill"
+        stages = json.loads(cp.completed_stages_json)
+        assert "fetch" in stages and "backfill" not in stages  # confirms this IS the skip-fetch resume path
+
+    # a TELLTALE provider that would flip the artifact to "drift" if the fetch stage re-ran (it must not).
+    # This fixture's tiny DB carries no real universe/sector data, so the resumed BACKFILL is kept under
+    # the SAME harmless per-date fault (isolated, caught -- see `_record_date_failure`/`_do_backfill`
+    # above) as the original run, keeping this test hermetic and independent of what a REAL scanner run
+    # would need; only that the fetch stage (and therefore the drift check) did NOT re-run is asserted,
+    # which is this test's entire point.
+    telltale = _FixedBarsProvider({"AAA": [Bar(date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]})
+    with monkeypatch.context() as resume_fault_mp:
+        resume_fault_mp.setattr(scanner, "compute_run_payload", _boom)
+        resume_data_job(
+            job.job_id, config=cfg, engine=engine, provider=telltale, sleep_fn=_noop_sleep, seed_dir=seed_dir,
+        )
+    assert telltale.calls == 0, "resume-at-backfill must perform ZERO provider calls (fetch stage skipped)"
+    assert read_drift_report() == first_report, "a skip-fetch resume must leave the drift artifact untouched"
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index adf91cf..eaeb141 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -68,7 +68,8 @@ def test_health_carries_additive_preflight_field(loaded_engine, tmp_path, monkey
     assert preflight["verdict"] in {"GO", "DEGRADED", "NO-GO"}
     assert isinstance(preflight["reasons"], list)
     assert preflight["as_of"] == preflight["reference"]  # same value under both spec-named keys
-    assert set(preflight["components"]) == {"servability", "freshness", "integrity"}
+    # iter-35 (J-21/B-304) added the 4th `drift` component (the live-vs-seed overlap check).
+    assert set(preflight["components"]) == {"servability", "freshness", "integrity", "drift"}
     for component in preflight["components"].values():
         assert set(component) == {"ok", "severity", "detail"}
         assert component["severity"] in {"degraded", "no-go"}
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index b910e0e..eddfc84 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -105,7 +105,7 @@ _CFG = {
     },
     "readiness": {
         "freshness_max_age_days": 5,
-        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
         "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
     },
     "walk_forward": {
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index 7e67dc5..058f422 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -45,7 +45,10 @@ def _readiness_cfg(cfg, **overrides):
 
 def _point_ledgers_at(monkeypatch, tmp_dir, *, ok: bool) -> None:
     """Point all three ledger/registry resolvers at `tmp_dir`: valid-but-empty files when `ok`, else
-    paths that are never created (the honest "missing" integrity failure)."""
+    paths that are never created (the honest "missing" integrity failure). Also points the iter-35
+    drift-report resolver at a guaranteed-ABSENT path under `tmp_dir` (never created here), so the new
+    `drift` preflight component is deterministically `ok` (no fetch has run yet) regardless of the real
+    repo's filesystem state — the drift-specific fixture tests below point it elsewhere explicitly."""
     for filename, env_var in (
         ("certified-claims.jsonl", "TRENDORA_LEDGER_PATH"),
         ("staging-ledger.jsonl", "STAGING_LEDGER_PATH"),
@@ -55,6 +58,7 @@ def _point_ledgers_at(monkeypatch, tmp_dir, *, ok: bool) -> None:
         if ok:
             target.write_text("")
         monkeypatch.setenv(env_var, str(target))
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_dir / "drift-report.json"))
 
 
 # ==================================================================================================
@@ -123,7 +127,12 @@ def test_preflight_fixture_matrix(loaded_engine, empty_engine, unscanned_engine,
         assert result["verdict"] == expected_verdict, f"{label}: got {result}"
         assert set(result) == {"verdict", "reasons", "components", "as_of", "reference"}
         assert result["as_of"] == result["reference"]  # same value under both spec-named keys
-        assert set(result["components"]) == {"servability", "freshness", "integrity"}
+        # iter-35 (J-21/B-304) added the 4th `drift` component; `_point_ledgers_at` points it at an
+        # absent path for every row above, so it is always `ok` here (no fetch has run in this matrix) —
+        # the drift-specific behavior (breach on a written "drift"/unreadable artifact) is covered by its
+        # own dedicated tests below, not re-derived per row of this pre-existing 3-axis matrix.
+        assert set(result["components"]) == {"servability", "freshness", "integrity", "drift"}
+        assert result["components"]["drift"]["ok"] is True, f"{label}: {result['components']['drift']}"
         for component, expected_ok in expected_oks.items():
             assert result["components"][component]["ok"] is expected_ok, f"{label}/{component}: {result}"
         if expected_verdict == GO:
@@ -146,6 +155,7 @@ def test_preflight_components_always_carry_configured_severity(loaded_engine, tm
     assert result["components"]["servability"]["severity"] == cfg.readiness.severity["servability"]
     assert result["components"]["freshness"]["severity"] == cfg.readiness.severity["freshness"]
     assert result["components"]["integrity"]["severity"] == cfg.readiness.severity["integrity"]
+    assert result["components"]["drift"]["severity"] == cfg.readiness.severity["drift"]
 
 
 # ==================================================================================================
@@ -193,7 +203,7 @@ def test_readiness_cfg_rejects_severity_missing_both_states():
     with pytest.raises(ValueError, match="degraded.*no-go|no-go.*degraded"):
         ReadinessCfg(
             freshness_max_age_days=5,
-            severity={"servability": "no-go", "freshness": "no-go", "integrity": "no-go"},
+            severity={"servability": "no-go", "freshness": "no-go", "integrity": "no-go", "drift": "no-go"},
             verdict_history_path="x.jsonl",
         )
 
@@ -204,11 +214,35 @@ def test_readiness_cfg_rejects_unknown_severity_value():
     with pytest.raises(ValueError, match="must be one of"):
         ReadinessCfg(
             freshness_max_age_days=5,
-            severity={"servability": "critical", "freshness": "degraded", "integrity": "no-go"},
+            severity={"servability": "critical", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
             verdict_history_path="x.jsonl",
         )
 
 
+def test_readiness_cfg_rejects_severity_missing_drift_component():
+    """iter-35 (J-21/B-304): `drift` joins the required component set — a severity map covering the
+    original three but omitting `drift` alone is rejected, exactly like an original omission."""
+    from app.config import ReadinessCfg
+
+    with pytest.raises(ValueError, match="missing components"):
+        ReadinessCfg(
+            freshness_max_age_days=5,
+            severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},  # drift missing
+            verdict_history_path="x.jsonl",
+        )
+
+
+def test_readiness_cfg_accepts_severity_with_all_four_components():
+    from app.config import ReadinessCfg
+
+    cfg = ReadinessCfg(
+        freshness_max_age_days=5,
+        severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
+        verdict_history_path="x.jsonl",
+    )
+    assert cfg.severity["drift"] == "degraded"
+
+
 # ==================================================================================================
 # Single source: servability is REUSED from compute_readiness, never re-derived
 # ==================================================================================================
@@ -241,6 +275,89 @@ def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
     assert set(result["warmup"]) == {"done", "total", "status", "message"}
 
 
+# ==================================================================================================
+# iter-35 (J-21/B-304): the `drift` component -- ok when absent/clean, breached on a written artifact,
+# worst-severity composition across all FOUR components still correct
+# ==================================================================================================
+def test_drift_component_ok_when_artifact_absent(loaded_engine, tmp_path_factory, monkeypatch):
+    """No fetch has ever run -> the drift artifact is absent -> `ok` (the J-20 non-regression
+    guarantee: GO stays GO with the drift component wired in but inert)."""
+    cfg = load_config()
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("drift_absent"), ok=True)
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["drift"]["ok"] is True
+    assert result["verdict"] == GO
+
+
+def test_drift_component_ok_when_artifact_clean(loaded_engine, tmp_path_factory, monkeypatch):
+    from app.engine.drift import write_drift_report
+
+    cfg = load_config()
+    tmp_dir = tmp_path_factory.mktemp("drift_clean")
+    _point_ledgers_at(monkeypatch, tmp_dir, ok=True)
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_dir / "written-drift-report.json"))
+    write_drift_report({"status": "clean", "reference": "2024-03-01", "overlap_days": 20, "affected": []})
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["drift"]["ok"] is True
+    assert result["verdict"] == GO
+
+
+def test_drift_component_breached_on_drift_status_names_affected_symbols(loaded_engine, tmp_path_factory, monkeypatch):
+    from app.engine.drift import write_drift_report
+
+    cfg = load_config()
+    tmp_dir = tmp_path_factory.mktemp("drift_breach")
+    _point_ledgers_at(monkeypatch, tmp_dir, ok=True)
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(tmp_dir / "written-drift-report.json"))
+    write_drift_report({
+        "status": "drift", "reference": "2024-03-01", "overlap_days": 20,
+        "affected": [{"symbol": "AAPL", "mismatching_dates": ["2024-02-28"], "classification": "adjustment_seam"}],
+    })
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["drift"]["ok"] is False
+    assert "AAPL" in result["components"]["drift"]["detail"]
+    assert result["components"]["drift"]["detail"] in result["reasons"]
+    assert result["verdict"] == DEGRADED  # config default: readiness.severity.drift == "degraded"
+
+
+def test_drift_component_breached_on_unreadable_artifact(loaded_engine, tmp_path_factory, monkeypatch):
+    cfg = load_config()
+    tmp_dir = tmp_path_factory.mktemp("drift_unreadable")
+    _point_ledgers_at(monkeypatch, tmp_dir, ok=True)
+    drift_path = tmp_dir / "corrupt-drift-report.json"
+    drift_path.write_text("{not valid json")
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(drift_path))
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)  # must not raise
+    assert result["components"]["drift"]["ok"] is False
+    assert "unreadable" in result["components"]["drift"]["detail"].lower()
+
+
+def test_drift_breach_composes_with_other_breaches_worst_severity_wins(loaded_engine, tmp_path_factory, monkeypatch):
+    """A drift breach (config-default `degraded`) alongside an integrity breach (config-default `no-go`)
+    still yields the WORST verdict, NO-GO -- the 4th component doesn't change the existing worst-of
+    composition rule."""
+    from app.engine.drift import write_drift_report
+
+    cfg = load_config()
+    tmp_dir = tmp_path_factory.mktemp("drift_plus_integrity")
+    _point_ledgers_at(monkeypatch, tmp_dir, ok=False)  # integrity breach (no-go)
+    drift_path = tmp_dir / "written-drift-report.json"
+    monkeypatch.setenv("TRENDORA_DRIFT_REPORT_PATH", str(drift_path))  # override the absent default
+    write_drift_report({
+        "status": "drift", "reference": "x", "overlap_days": 20,
+        "affected": [{"symbol": "ZZZ", "mismatching_dates": ["2024-01-01"], "classification": "adjustment_seam"}],
+    })
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["integrity"]["ok"] is False
+    assert result["components"]["drift"]["ok"] is False
+    assert result["verdict"] == NO_GO  # integrity's no-go outranks drift's degraded
+
+
 # ==================================================================================================
 # Error cases: honest degradation, never a raise, never a fabricated GO
 # ==================================================================================================
diff --git a/apps/backend/tests/test_sectors.py b/apps/backend/tests/test_sectors.py
index 8d08fb1..4457836 100644
--- a/apps/backend/tests/test_sectors.py
+++ b/apps/backend/tests/test_sectors.py
@@ -140,7 +140,7 @@ _SYNTH_CFG = {
     },
     "readiness": {  # iter-33: readiness is a required config section (daily preflight-verdict tunables)
         "freshness_max_age_days": 5,
-        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
         "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
     },
     "walk_forward": {  # iter-6: walk_forward is a required config section
diff --git a/apps/backend/tests/test_themes.py b/apps/backend/tests/test_themes.py
index 5d3c9f7..664c9f2 100644
--- a/apps/backend/tests/test_themes.py
+++ b/apps/backend/tests/test_themes.py
@@ -141,7 +141,7 @@ _SYNTH_CFG = {
     },
     "readiness": {  # iter-33: readiness is a required config section (daily preflight-verdict tunables)
         "freshness_max_age_days": 5,
-        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
         "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
     },
     "walk_forward": {  # iter-6: walk_forward is a required config section
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index f7bdf52..8a3d796 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -2361,6 +2361,29 @@ export interface DataCapacity {
   forward_returns_rows: number;
 }
 
+/** iter-35 (J-21/B-304) — one symbol whose overlap window disagreed between a live fetch and the
+ *  committed seed: the exact mismatching dates + the honest classification (an "adjustment_seam" — the
+ *  vendor silently re-adjusted already-committed history). Never a fabricated diagnosis. */
+export interface DriftAffectedSymbol {
+  symbol: string;
+  mismatching_dates: string[];
+  classification: string;
+}
+
+/** iter-35 (J-21/B-304) — the live-vs-seed drift report: the SAME artifact the readiness `drift`
+ *  preflight component reads (`app.engine.drift.read_drift_report`), served here VERBATIM — no
+ *  recompute, no second parse path (the Data Contract single-source requirement). `status` is
+ *  `"clean"` (the last fetch matched the seed over the overlap window), `"drift"` (a mismatch —
+ *  `affected` names every symbol + its mismatching dates), or `"unreadable"` (the artifact exists but
+ *  could not be parsed — an honest degraded state, never silently treated as clean). Descriptive
+ *  integrity reporting only — no proven/not-proven language. */
+export interface DriftReport {
+  status: "clean" | "drift" | "unreadable";
+  reference: string | null;
+  overlap_days: number | null;
+  affected: DriftAffectedSymbol[];
+}
+
 export interface DataOverviewResponse {
   coverage: DataCoverage;
   runs: DataRun[];
@@ -2370,6 +2393,9 @@ export interface DataOverviewResponse {
   unfinished_imports: UnfinishedImport[]; // J-38 unified unfinished imports (resumable + partial + failed)
   job_progress: JobProgressConfig; // J-66 poll/heartbeat/granularity knobs (config-driven)
   capacity: DataCapacity; // item K (iter-24) — the DB storage-footprint snapshot
+  // iter-35 (J-21/B-304): `null` when no fetch has ever run (honest inert — the card renders a quiet
+  // "no fetch yet" state, distinct from a confirmed "clean").
+  drift: DriftReport | null;
 }
 
 export type DataJobKind = "fetch" | "backfill" | "both" | "expand" | "rebuild";
diff --git a/config.yaml b/config.yaml
index 039951e..029a421 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1105,6 +1105,24 @@ evidence:
                               # behave correctly. Blocks nothing today (no iteration currently carries a
                               # ## Evidence Claim); closes the ad-hoc-mining door for every future one.
 
+# ----------------------------------------------------------------------------------------
+# goal-mcp-loop iter-35 CONSUMED — live-vs-seed drift monitor (app.engine.drift, J-21 / backlog B-304,
+# OVERLAP CHECK ONLY — the distribution-envelope check and the B-113-dependent seam scan are deferred).
+# `enabled` is the post-fetch validation stage's emergency off-switch (data_manager._run_job) — a
+# generic Fetch/Expand/`both` job compares the last `overlap_days` dates COMMON to what it just fetched
+# and the committed seed CSVs (data/seed/prices/*.csv); a byte/fixed-precision mismatch on any OHLCV
+# field is an "adjustment seam" (the vendor silently re-adjusted already-committed history). The result
+# is written ONCE to `report_path` (a RELATIVE path resolves against the repo root; the runtime env
+# override TRENDORA_DRIFT_REPORT_PATH takes precedence when set — mirrors evidence.ledger_path) and
+# re-read verbatim by both the readiness `drift` preflight component (readiness.severity.drift below)
+# and the additive `drift` field on GET /api/data. Currently DEFAULT-ON; the stage stays byte-identically
+# INERT (no artifact written, no preflight effect) until an actual live fetch runs.
+data_quality:
+  drift:
+    enabled: true
+    overlap_days: 20                                          # bounded per-symbol compare window (anti-goal #8 — never the whole history)
+    report_path: runs/goal-session-mcp-loop/state/drift-report.json
+
 # ----------------------------------------------------------------------------------------
 # Analyst-loop triad scan (app.engine.triad_scan / scan_product_triad). Tunables for the
 # deterministic scan that ranks factor cross-over cohorts by the "triad" (higher forward
@@ -1246,13 +1264,16 @@ startup:
 # committed seed. `severity` maps each composed input to the verdict a breach forces — owner-reviewed
 # (B-301: "making NO-GO too easy is alarm fatigue"); both `degraded` and `no-go` must appear so the
 # fixture matrix can induce each. `verdict_history_path` is the append-only transition log (written
-# only when the verdict changes, never on every ~2s poll).
+# only when the verdict changes, never on every ~2s poll). iter-35 adds `drift` (J-21/B-304): a failed
+# live-vs-seed overlap check forces DEGRADED (an adjustment seam is worth a cautious look, not treated
+# as severely as a NO-GO integrity/servability breach) with the affected symbols named in the reason.
 readiness:
   freshness_max_age_days: 5
   severity:
     servability: no-go
     freshness: degraded
     integrity: no-go
+    drift: degraded
   verdict_history_path: runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl
 
 # ----------------------------------------------------------------------------------------
diff --git a/apps/backend/app/engine/drift.py b/apps/backend/app/engine/drift.py
new file mode 100644
index 0000000..0bf6dfd
--- /dev/null
+++ b/apps/backend/app/engine/drift.py
@@ -0,0 +1,150 @@
+"""Live-vs-seed drift monitor (goal-mcp-loop iter-35, J-21 / backlog B-304 — OVERLAP CHECK ONLY).
+
+When the live provider fetches new bars, the vendor may have silently RE-ADJUSTED already-committed
+history (Stooq back-adjusts a symbol's WHOLE history on every dividend/split). Because the price DB is
+INSERT-new-only (`data_manager._existing_dates` skips any date already stored), a re-adjusted value for an
+already-covered date is silently DISCARDED — the DB keeps the OLD value forever, and nobody is told the
+live feed disagrees with what was validated. This module is the detector: it byte/fixed-precision compares
+the bars a fetch just returned against the **committed seed CSVs** (`data/seed/prices/{symbol}.csv` — the
+validated history) for the last `overlap_days` dates common to both, and reports any mismatch as an
+"adjustment seam". It NEVER mutates, reconciles, or re-fetches the fetched data (B-304 "Do NOT touch the
+fetched data" — reconciliation is an owner decision, possibly a future re-basis); it only REPORTS.
+
+Comparator discipline (the named B-304 trap): the compare is FIXED-PRECISION (6 decimal places, matching
+the deepest precision the committed seed carries) and EXACT — never a tolerance window (`abs(a - b) <
+eps`). A tolerant comparator would silently pass a genuine small-magnitude re-adjustment; see
+`test_drift.py::test_small_price_delta_is_flagged_never_smoothed_by_a_tolerance_window`.
+
+The artifact is a SINGLE overwritten JSON object (not an append-only ledger — only the most recent fetch's
+drift status matters for the daily preflight verdict), written ONCE by the fetch pipeline's post-fetch
+validation stage (`app.engine.data_manager._run_job`) and re-read VERBATIM by both
+`app.engine.readiness.compute_preflight` (the `drift` preflight component) and the additive `drift` field
+on `GET /api/data` (`app.api.data.data_overview`) — the single-source Data Contract. A missing artifact
+(no fetch has run yet) is honestly inert; an unparseable one reads back an honest `status ==
+"unreadable"` — `read_drift_report` NEVER raises.
+"""
+from __future__ import annotations
+
+import json
+import os
+from pathlib import Path
+from typing import Optional
+
+from app.config import REPO_ROOT, get_config
+from app.data_providers.base import Bar
+
+# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime
+# drift-report path may be overridden with. Mirrors `app.engine.evidence.LEDGER_PATH_ENV`.
+DRIFT_REPORT_PATH_ENV = "TRENDORA_DRIFT_REPORT_PATH"
+
+STATUS_CLEAN = "clean"
+STATUS_DRIFT = "drift"
+# The artifact file exists but could not be parsed as the expected JSON object — an honest degraded
+# read (never silently treated as "clean", never a raise). Distinct from a MISSING artifact (`None`
+# from `read_drift_report`), which means "no fetch has run yet" and is genuinely inert.
+STATUS_UNREADABLE = "unreadable"
+
+_OHLCV_FIELDS = ("open", "high", "low", "close", "volume")
+# Fixed decimal places for the byte/fixed-precision comparator — matches the deepest precision the
+# committed seed CSVs carry (e.g. `0.241539`). No magic number at the call site; named here once.
+_COMPARE_PRECISION = 6
+
+
+def resolve_drift_report_path() -> str:
+    """The drift-report artifact path: the `TRENDORA_DRIFT_REPORT_PATH` env override if set, else
+    `config.data_quality.drift.report_path` resolved against `REPO_ROOT` when relative. Mirrors
+    `app.engine.evidence.resolve_ledger_path()` exactly, so the browser-qa/gate lanes and the fetch
+    pipeline always resolve the SAME artifact. No path literal lives here — the default lives in config
+    (anti-goal: No magic numbers)."""
+    override = os.environ.get(DRIFT_REPORT_PATH_ENV)
+    if override:
+        return override
+    configured = Path(get_config().data_quality.drift.report_path)
+    if not configured.is_absolute():
+        configured = REPO_ROOT / configured
+    return str(configured)
+
+
+def _fixed(value: float) -> str:
+    """Fixed-precision string form of one OHLCV field value — the byte/fixed-precision comparator unit.
+    Two values that format to different strings here ARE a mismatch, however small the numeric delta
+    (never a tolerance window — the B-304 trap)."""
+    return f"{float(value):.{_COMPARE_PRECISION}f}"
+
+
+def _bars_mismatch(fetched: Bar, seed: Bar) -> bool:
+    """True iff ANY OHLCV field differs at fixed precision between the two bars for the SAME date."""
+    return any(_fixed(getattr(fetched, field)) != _fixed(getattr(seed, field)) for field in _OHLCV_FIELDS)
+
+
+def build_drift_report(
+    fetched_bars: dict[str, list[Bar]],
+    seed_bars: dict[str, list[Bar]],
+    *,
+    overlap_days: int,
+    reference: str,
+) -> dict:
+    """The SINGLE overlap comparator (PURE — recomputes/mutates nothing, touches no filesystem/DB).
+
+    For each symbol present in `fetched_bars`, take the last `overlap_days` dates COMMON to
+    `fetched_bars[symbol]` and `seed_bars[symbol]` (bounded — never the whole history, per the
+    iter-24/26 anti-goal-#8 lesson), and byte/fixed-precision compare OHLCV on each. A symbol with no
+    seed history at all (e.g. a brand-new universe member) has zero common dates and is honestly never
+    flagged — no KeyError, no fabricated mismatch.
+
+    Returns `{status: "clean"|"drift", reference, overlap_days, affected: [{symbol, mismatching_dates,
+    classification: "adjustment_seam"}, ...]}`, `affected` sorted by symbol. `reference` is passed
+    through verbatim — the caller supplies a DETERMINISTIC anchor (a job/fetch parameter, never
+    `date.today()` — anti-goal #5)."""
+    affected: list[dict] = []
+    for symbol in sorted(fetched_bars):
+        fetched_by_date = {bar.date: bar for bar in (fetched_bars.get(symbol) or [])}
+        seed_by_date = {bar.date: bar for bar in (seed_bars.get(symbol) or [])}
+        common_dates = sorted(set(fetched_by_date) & set(seed_by_date))
+        window = common_dates[-overlap_days:] if overlap_days > 0 else []
+        mismatching = [d for d in window if _bars_mismatch(fetched_by_date[d], seed_by_date[d])]
+        if mismatching:
+            affected.append({
+                "symbol": symbol,
+                "mismatching_dates": [d.isoformat() for d in mismatching],
+                "classification": "adjustment_seam",
+            })
+    return {
+        "status": STATUS_DRIFT if affected else STATUS_CLEAN,
+        "reference": reference,
+        "overlap_days": overlap_days,
+        "affected": affected,
+    }
+
+
+def write_drift_report(report: dict) -> None:
+    """Persist the SINGLE drift-report artifact (OVERWRITE, not append — only the latest fetch's status
+    matters for the preflight verdict). Creates the parent directory on first write. Written via a
+    temp-file-then-rename so a reader never observes a partially-written file."""
+    path = resolve_drift_report_path()
+    parent = os.path.dirname(os.path.abspath(path))
+    os.makedirs(parent, exist_ok=True)
+    tmp_path = f"{path}.tmp"
+    with open(tmp_path, "w", encoding="utf-8") as handle:
+        json.dump(report, handle, sort_keys=True, default=str)
+    os.replace(tmp_path, path)
+
+
+def read_drift_report() -> Optional[dict]:
+    """The SINGLE reader both `compute_preflight` and `GET /api/data` call — no second parse path.
+
+    - Missing artifact (no fetch has run yet) -> `None`, the honest inert case (every caller treats
+      `None` as "ok" / "no report to show", distinct from a confirmed `status == "clean"`).
+    - Unparseable artifact -> an honest `{"status": "unreadable", ...}` dict — NEVER a raise, and never
+      silently treated as clean (a corrupt artifact is worth surfacing, not hiding)."""
+    path = resolve_drift_report_path()
+    if not os.path.exists(path):
+        return None
+    try:
+        with open(path, "r", encoding="utf-8") as handle:
+            data = json.load(handle)
+    except (OSError, json.JSONDecodeError):
+        data = None
+    if not isinstance(data, dict) or "status" not in data:
+        return {"status": STATUS_UNREADABLE, "reference": None, "overlap_days": None, "affected": []}
+    return data
diff --git a/apps/backend/tests/test_drift.py b/apps/backend/tests/test_drift.py
new file mode 100644
index 0000000..98e443b
--- /dev/null
+++ b/apps/backend/tests/test_drift.py
@@ -0,0 +1,209 @@
+"""Live-vs-seed drift monitor (goal-mcp-loop iter-35, J-21 / backlog B-304 — OVERLAP CHECK ONLY).
+
+`app.engine.drift` is a PURE comparator + single writer/reader pair for the drift-report artifact:
+
+  - `build_drift_report` — byte/fixed-precision OHLCV compare (never a loose float tolerance) over the
+    last `overlap_days` dates COMMON to a fetch and the committed seed. Fixture matrix: a re-adjusted
+    overlap is detected with the exact mismatching dates + `adjustment_seam` classification; a clean
+    overlap reports `status == "clean"` with an empty `affected` list; a byte/fixed-precision compare
+    catches a real (small-magnitude) seam a loose/tolerant float compare would miss (the named B-304
+    trap); only the last `overlap_days` COMMON dates are ever compared (older mismatches outside the
+    window are invisible); a symbol absent from the seed entirely is never flagged (honest skip, no
+    KeyError).
+  - `resolve_drift_report_path` — env override, else config default resolved against REPO_ROOT (mirrors
+    `app.engine.evidence.resolve_ledger_path` exactly).
+  - `write_drift_report` / `read_drift_report` — a single writer/reader pair; a missing artifact is
+    inert (`None`); an unparseable artifact reads back an honest `status == "unreadable"` — NEVER a
+    raise.
+"""
+from __future__ import annotations
+
+import os
+from datetime import date
+
+import pytest
+
+from app.config import REPO_ROOT, get_config
+from app.data_providers.base import Bar
+from app.engine.drift import (
+    DRIFT_REPORT_PATH_ENV,
+    STATUS_CLEAN,
+    STATUS_DRIFT,
+    STATUS_UNREADABLE,
+    build_drift_report,
+    read_drift_report,
+    resolve_drift_report_path,
+    write_drift_report,
+)
+
+
+def _bar(d: date, *, close: float = 100.0, open_: float = 100.0, high: float = 101.0, low: float = 99.0, volume: float = 1000.0) -> Bar:
+    return Bar(date=d, open=open_, high=high, low=low, close=close, volume=volume)
+
+
+# ==================================================================================================
+# build_drift_report — fixture matrix
+# ==================================================================================================
+def test_clean_overlap_reports_clean_status_and_empty_affected():
+    dates = [date(2024, 3, 1), date(2024, 3, 4), date(2024, 3, 5)]
+    seed = {"AAA": [_bar(d) for d in dates]}
+    fetched = {"AAA": [_bar(d) for d in dates]}  # byte-identical re-fetch
+    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-05")
+    assert report == {
+        "status": STATUS_CLEAN,
+        "reference": "2024-03-05",
+        "overlap_days": 5,
+        "affected": [],
+    }
+
+
+def test_readjusted_overlap_detected_with_exact_symbol_and_dates():
+    seed = {
+        "AAA": [
+            _bar(date(2024, 3, 1), close=100.0),
+            _bar(date(2024, 3, 4), close=101.0),
+            _bar(date(2024, 3, 5), close=102.0),
+        ]
+    }
+    # the vendor re-adjusted the 3/1 close (a whole-history back-adjustment on a dividend/split) — the
+    # OTHER two dates are byte-identical.
+    fetched = {
+        "AAA": [
+            _bar(date(2024, 3, 1), close=95.0),
+            _bar(date(2024, 3, 4), close=101.0),
+            _bar(date(2024, 3, 5), close=102.0),
+        ]
+    }
+    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-05")
+    assert report["status"] == STATUS_DRIFT
+    assert report["affected"] == [
+        {"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}
+    ]
+
+
+def test_small_price_delta_is_flagged_never_smoothed_by_a_tolerance_window():
+    """The B-304 trap: a 1-cent close delta is exactly the kind of 'surely just rounding' difference a
+    loose `abs(a - b) < 0.01` comparator would silently let through. This must FAIL if the comparator is
+    ever 'simplified' to a numeric tolerance window instead of exact fixed-precision equality."""
+    d = date(2024, 3, 1)
+    seed = {"AAA": [_bar(d, close=100.00)]}
+    fetched = {"AAA": [_bar(d, close=100.01)]}
+    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-01")
+    assert report["status"] == STATUS_DRIFT
+    assert report["affected"] == [
+        {"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}
+    ]
+
+
+def test_mismatch_in_any_single_ohlcv_field_is_sufficient():
+    """A mismatch on ANY of open/high/low/close/volume (not just close) is caught."""
+    d = date(2024, 3, 1)
+    base = {"open_": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0}
+    for field in ("open_", "high", "low", "close", "volume"):
+        bumped = dict(base)
+        bumped[field] = bumped[field] + 5.0
+        seed = {"AAA": [_bar(d, **base)]}
+        fetched = {"AAA": [_bar(d, **bumped)]}
+        report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-01")
+        assert report["status"] == STATUS_DRIFT, f"field {field} mismatch was not detected"
+
+
+def test_only_last_overlap_days_common_dates_are_compared():
+    """A mismatch OUTSIDE the last `overlap_days` common dates is invisible (bounded window, per the
+    iter-24/26 anti-goal-#8 lesson — a bounded per-symbol overlap-window compare, never the whole
+    history); a mismatch INSIDE the window is still caught."""
+    dates = [date(2024, 3, d) for d in (1, 4, 5, 6, 7)]  # 5 common dates
+    seed = {"AAA": [_bar(d, close=100.0 + i) for i, d in enumerate(dates)]}
+
+    # mismatch on the OLDEST date only, outside a 2-day window -> invisible -> clean
+    fetched_old_only = {
+        "AAA": [
+            _bar(dates[0], close=999.0),  # re-adjusted, but outside the window
+            *[_bar(d, close=100.0 + i) for i, d in enumerate(dates) if i > 0],
+        ]
+    }
+    report = build_drift_report(fetched_old_only, seed, overlap_days=2, reference="2024-03-07")
+    assert report["status"] == STATUS_CLEAN
+
+    # mismatch on the NEWEST date -> inside a 2-day window -> caught
+    fetched_recent = {
+        "AAA": [
+            *[_bar(d, close=100.0 + i) for i, d in enumerate(dates) if i < 4],
+            _bar(dates[4], close=999.0),
+        ]
+    }
+    report2 = build_drift_report(fetched_recent, seed, overlap_days=2, reference="2024-03-07")
+    assert report2["status"] == STATUS_DRIFT
+    assert report2["affected"][0]["mismatching_dates"] == ["2024-03-07"]
+
+
+def test_symbol_absent_from_seed_is_not_flagged_no_crash():
+    """A fetched symbol with NO committed-seed history at all (e.g. a brand-new universe member) has no
+    common dates to compare -- an honest skip, never a KeyError or a fabricated mismatch."""
+    fetched = {"NEWCO": [_bar(date(2024, 3, 1))]}
+    report = build_drift_report(fetched, seed_bars={}, overlap_days=5, reference="2024-03-01")
+    assert report == {"status": STATUS_CLEAN, "reference": "2024-03-01", "overlap_days": 5, "affected": []}
+
+
+def test_multiple_symbols_only_mismatching_ones_are_affected():
+    d = date(2024, 3, 1)
+    seed = {"AAA": [_bar(d, close=100.0)], "BBB": [_bar(d, close=50.0)], "CCC": [_bar(d, close=10.0)]}
+    fetched = {"AAA": [_bar(d, close=100.0)], "BBB": [_bar(d, close=999.0)], "CCC": [_bar(d, close=10.0)]}
+    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-01")
+    assert report["status"] == STATUS_DRIFT
+    assert [a["symbol"] for a in report["affected"]] == ["BBB"]
+
+
+# ==================================================================================================
+# resolve_drift_report_path -- env override / config default (mirrors resolve_ledger_path exactly)
+# ==================================================================================================
+def test_resolve_drift_report_path_env_override(tmp_path, monkeypatch):
+    override = tmp_path / "custom-drift-report.json"
+    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(override))
+    assert resolve_drift_report_path() == str(override)
+
+
+def test_resolve_drift_report_path_config_default(monkeypatch):
+    monkeypatch.delenv(DRIFT_REPORT_PATH_ENV, raising=False)
+    resolved = resolve_drift_report_path()
+    configured = get_config().data_quality.drift.report_path
+    assert resolved == str(REPO_ROOT / configured)
+    assert os.path.isabs(resolved)
+
+
+# ==================================================================================================
+# write_drift_report / read_drift_report -- single writer/reader pair
+# ==================================================================================================
+def test_write_then_read_round_trips(tmp_path, monkeypatch):
+    target = tmp_path / "nested" / "drift-report.json"
+    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(target))
+    report = {"status": STATUS_DRIFT, "reference": "2024-03-01", "overlap_days": 5,
+               "affected": [{"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}]}
+    write_drift_report(report)
+    assert target.exists()  # write_drift_report creates the parent directory on first write
+    assert read_drift_report() == report
+
+
+def test_read_missing_artifact_is_inert_none(tmp_path, monkeypatch):
+    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(tmp_path / "never-written.json"))
+    assert read_drift_report() is None
+
+
+def test_read_unparseable_artifact_is_honest_never_raises(tmp_path, monkeypatch):
+    target = tmp_path / "corrupt-drift-report.json"
+    target.write_text("{not valid json")
+    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(target))
+    report = read_drift_report()  # must not raise
+    assert report is not None
+    assert report["status"] == STATUS_UNREADABLE
+
+
+def test_write_overwrites_the_single_artifact_not_append(tmp_path, monkeypatch):
+    """The drift artifact is a SINGLE overwritten snapshot (only the latest fetch's status matters for
+    readiness) -- NOT an append-only ledger."""
+    target = tmp_path / "drift-report.json"
+    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(target))
+    write_drift_report({"status": STATUS_DRIFT, "reference": "d1", "overlap_days": 5, "affected": []})
+    write_drift_report({"status": STATUS_CLEAN, "reference": "d2", "overlap_days": 5, "affected": []})
+    assert read_drift_report()["status"] == STATUS_CLEAN
+    assert read_drift_report()["reference"] == "d2"
```
