# Iteration diff (bounded)

Files changed: 16. Shown in full: 16.

```diff
diff --git a/README.md b/README.md
index bba9d56..c9f5333 100644
--- a/README.md
+++ b/README.md
@@ -32,6 +32,7 @@ Current capabilities:
   - All Research pages: every `N=` sample count is a clickable link that opens a drill-down in a new tab — keeping lab selections and scroll position undisturbed — showing exact stored observations; the observations table is sortable and filterable by ticker. From any observation row click the ticker to open that stock's detail page at the snapshot date in a new tab.
 - **Pre-registration registry**: a "Governance & process" section on the Research hub links, in one click, to a dedicated `/research/registry` page listing every trading hypothesis the platform has ever registered or tested — 11 rows today, each showing its exact selectors as compact, readable chips (e.g. `kind=factor`, `factor=vcp_contraction`, `decile=10`, `horizon=60`, `direction=positive`; a multi-leg combination's selectors render as one chip with legs joined by `+`), its economic rationale, registration date, source, and current status in a neutral gray badge — deliberately distinct from the green/red proven/not-proven coloring used on the Evidence page, so this column is never mistaken for a pass/fail signal. Every backfilled historical row carries a small "backfill" pill, and the page shows an honest loading skeleton, a contained error card if the backend is unreachable, or an empty state if the registry is ever empty. The registry is read-only — entries can only be added by the platform itself — and going forward the platform's evidence-certification process refuses to test any new idea that was not already logged here first, closing a common way statistical findings get quietly cherry-picked after the fact.
 - **Negative-results graveyard**: a second card next to Pre-registration registry in the Research hub's "Governance & process" section — "Negative-results graveyard" — opens a dedicated `/research/graveyard` page listing every hypothesis the platform has tested and rejected: 14 rows today, seven from the public evidence process plus, for the first time, seven from an internal early-stage research track whose results (rejections only — it has had no successes) were never shown anywhere before. Each row shows its exact cohort selectors as compact chips, whether it failed its out-of-sample test or simply didn't have enough data to judge, the date it was tested, the multiple-testing correction that was applied, which process produced it, and — where known — a lineage link back to its original registered hypothesis; clicking that link jumps straight to and highlights the exact matching row on the Pre-registration registry page. The one hypothesis retired for good (a moving-average pattern that failed twice) carries a "permanent" marker so nobody tries it again, and a "Revisit protocol" panel spells out in plain language the only way a rejected idea could ever be re-tested — every row links to it. Nothing about which values elsewhere read "Proven" changed; this page only makes the platform's past rejections auditable.
+- **Certification-budget accounting**: a third card, alongside Pre-registration registry and Negative-results graveyard, in the Research hub's "Governance & process" section (completing that section's three-card grid) opens a dedicated `/research/budget` page that shows, before any new scan is proposed, exactly how much of the platform's statistical credibility budget has already been spent. Four cards report: the total number of canonical trials run to date (currently 7) and the trial number that comes next (#8); the exact significance bar the next canonical trial must clear — shown both as a number (currently 0.00625) and as its Bonferroni formula (0.05 ÷ the trial number), so the growth of the multiple-testing divisor is visible, not just its result; how much of the reusable-holdout (Thresholdout) alpha budget remains before a new scan can be proposed (currently 90% remaining); and an internal staging exploration economy's next-trial significance level and trial number — an internal budget that was never surfaced anywhere in the product before now. Each card carries a small inline trend sparkline showing how that figure has moved trial by trial, re-read verbatim from the recorded ledger history rather than freshly recomputed. A loading state shows four pulsing placeholder cards while data loads; if the backend is unreachable a single contained error card appears with the "Back to Research" link still usable; if the underlying ledgers were ever empty the same four cards would render honest zero/starting values rather than an error or blank state.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
 - **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index 965d641..d510b68 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -9,6 +9,12 @@ iter-28 (J-40) extends this SINGLE canonical endpoint with the honest backend `r
 message}`, both computed ONCE by `app.engine.readiness.compute_readiness` (the single readiness producer)
 — there is NO second readiness read path. The frontend readiness badge and the Backtest/Research
 "warming up (n/m)" states are the ONLY readers; the frontend never computes readiness itself.
+
+iter-33 (J-20) additively extends this SAME endpoint with the `preflight` field — the composite
+GO/DEGRADED/NO-GO verdict from `app.engine.readiness.compute_preflight` (which itself reuses this
+module's own `readiness`/`warmup` computation — no second computation). The layout-level
+`PreflightBanner` is the ONLY reader; existing `readiness`/`warmup`/`status`/etc. keys are unchanged
+(byte-identical — J-40 not regressed).
 """
 from __future__ import annotations
 
@@ -18,7 +24,7 @@ from sqlmodel import Session
 
 from app.config import get_config
 from app.db import get_engine, get_session
-from app.engine.readiness import compute_readiness
+from app.engine.readiness import compute_preflight, compute_readiness, record_verdict_transition
 from app.models import DailyPrice
 
 router = APIRouter(tags=["health"])
@@ -48,6 +54,25 @@ def health(session: Session = Depends(get_session)) -> dict:
             "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
         }
 
+    # iter-33 (J-20): the single daily preflight verdict (GO/DEGRADED/NO-GO + reasons). A compute error
+    # degrades to an honest NO-GO — never a blank/fabricated field (anti-goal #8).
+    try:
+        preflight = compute_preflight(session, config=cfg)
+        try:
+            # Append-only, ONLY on a transition (never on every ~2s poll) -- a history-write failure must
+            # never blank the health probe (mirrors the readiness try/except immediately above).
+            record_verdict_transition(preflight["verdict"], preflight["reasons"], preflight["reference"])
+        except Exception:  # pragma: no cover - a history-log write failure must never blank /health
+            pass
+    except Exception:  # pragma: no cover - never let a preflight error blank the health probe
+        preflight = {
+            "verdict": "NO-GO",
+            "reasons": ["The preflight check itself failed to run."],
+            "components": {},
+            "as_of": None,
+            "reference": None,
+        }
+
     return {
         "status": "ok" if db_ok else "degraded",
         "db_ok": db_ok,
@@ -64,4 +89,7 @@ def health(session: Session = Depends(get_session)) -> dict:
         # seconds` is the slower cadence the badge backs off to once Ready.
         "poll_interval_seconds": cfg.startup.health_poll_interval_seconds,
         "poll_idle_interval_seconds": cfg.startup.health_poll_idle_interval_seconds,
+        # iter-33 (J-20): the single daily preflight verdict (additive) -- the layout-level
+        # PreflightBanner's ONLY read path (see app.engine.readiness.compute_preflight).
+        "preflight": preflight,
     }
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index e7fc890..61918bc 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -532,6 +532,54 @@ class StartupCfg(BaseModel):
         return self
 
 
+class ReadinessCfg(BaseModel):
+    """Daily preflight-verdict tunables (iter-33, J-20 / backlog B-301). `app.engine.readiness:
+    compute_preflight` extends `compute_readiness` into a composite GO/DEGRADED/NO-GO verdict; every
+    number/mapping it uses lives here (mirrors `StartupCfg`'s shape exactly — boot-validated,
+    `extra="allow"`, no inline literal in the module):
+
+      - `freshness_max_age_days` — the trading-day-age threshold the freshness component breaches past.
+        Age is measured against a DETERMINISTIC, seed-resolved reference (never `date.today()` —
+        anti-goal #5): the reference is always the seed's own latest available data date, so a
+        fully-loaded seed is 0 trading days old (GO) by construction. Lowering this value (e.g. a
+        negative override, via a temporary `TRENDORA_CONFIG` alt-file) is the sanctioned lever for
+        inducing the DEGRADED/NO-GO test states without mutating committed seed data.
+      - `severity` — which verdict a breached component forces, keyed by component name (`servability` /
+        `freshness` / `integrity`): `"degraded"` or `"no-go"`. Owner-reviewed config (B-301's "making
+        NO-GO too easy is alarm fatigue" trap) — MUST cover all three components and include at least one
+        `"degraded"` and one `"no-go"` entry so both states are inducible for the fixture matrix.
+      - `verdict_history_path` — the append-only verdict-transition log path (written only when the
+        verdict changes, never on every ~2s poll). A relative path resolves against the repo root; the
+        `READINESS_VERDICT_HISTORY_PATH` env override takes precedence (test/gate seam — mirrors
+        `app.engine.evidence.LEDGER_PATH_ENV`).
+
+    Boot-validated: `severity` must name exactly `{servability, freshness, integrity}` with every value
+    one of `"degraded"`/`"no-go"`, covering both. An invalid block raises `ConfigError`, never a silent
+    default."""
+
+    model_config = ConfigDict(extra="allow")
+    freshness_max_age_days: int
+    severity: dict[str, str]
+    verdict_history_path: str
+
+    @model_validator(mode="after")
+    def _validate(self) -> "ReadinessCfg":
+        required_components = {"servability", "freshness", "integrity"}
+        missing = sorted(required_components - set(self.severity))
+        if missing:
+            raise ValueError(f"readiness.severity missing components: {missing}")
+        allowed_severities = {"degraded", "no-go"}
+        bad = sorted(f"{k}={v}" for k, v in self.severity.items() if v not in allowed_severities)
+        if bad:
+            raise ValueError(f"readiness.severity values must be one of {sorted(allowed_severities)}: {bad}")
+        if not allowed_severities <= set(self.severity.values()):
+            raise ValueError(
+                "readiness.severity must configure at least one component as 'degraded' and at least "
+                "one as 'no-go' so the fixture matrix can induce both states"
+            )
+        return self
+
+
 class ServerOpsCfg(BaseModel):
     """iter-42 (J-100) — bounded-resource SERVER ops guards. The SINGLE source of the uvicorn concurrency
     cap, the keep-alive + graceful-shutdown timeouts, and the per-process virtual-memory cap the start
@@ -2184,6 +2232,7 @@ class Config(BaseModel):
     stock_industries: dict[str, list[str]] = Field(default_factory=dict)
     scanner: ScannerCfg
     startup: StartupCfg  # iter-28 (J-40/J-41) fast-ready boot + warm-up tunables (boot-validated above)
+    readiness: ReadinessCfg  # iter-33 (J-20) daily preflight-verdict tunables (boot-validated above)
     # iter-42 (J-100) — bounded-resource server ops guards (uvicorn concurrency/timeout caps + the process
     # ulimit -v memory cap) the start script reads. Default-populated so a config/test fixture predating it
     # still loads unchanged and serves the documented bounds.
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index ef43bd0..6262452 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -22,14 +22,21 @@ progress and the analytics pages show their "warming up (n/m)" state — both re
 """
 from __future__ import annotations
 
+import json
+import os
 from datetime import date as date_cls
+from pathlib import Path
 from typing import Optional
 
 from sqlalchemy import func
 from sqlmodel import Session, select
 
-from app.config import Config, get_config
+from app.config import REPO_ROOT, Config, get_config
+from app.engine.evidence import resolve_ledger_path
+from app.engine.graveyard import resolve_staging_ledger_path
+from app.engine.ledger import append_entry, read_entries
 from app.engine.prices import bar_cache, latest_data_date
+from app.engine.registry import resolve_registry_path
 from app.engine.warmup import _warmup_dates, get_warmup
 from app.models import DailyPrice, ScannerRun
 
@@ -37,6 +44,14 @@ READY = "ready"
 INITIALIZING = "initializing"
 UNAVAILABLE = "unavailable"
 
+# The three composite preflight verdicts (iter-33, J-20 / backlog B-301). String values are the exact
+# DoD-mandated spelling ("NO-GO", hyphenated) — never re-derived elsewhere.
+GO = "GO"
+DEGRADED = "DEGRADED"
+NO_GO = "NO-GO"
+_VERDICT_RANK = {GO: 0, DEGRADED: 1, NO_GO: 2}  # for "worst breached component wins" composition
+_SEVERITY_TO_VERDICT = {"degraded": DEGRADED, "no-go": NO_GO}
+
 
 def _latest_run_date(session: Session):
     """The most recent persisted run's as-of date, or None when no snapshot is stored yet."""
@@ -174,3 +189,166 @@ def compute_readiness(
             "message": message,
         },
     }
+
+
+# ====================================================================================================
+# Daily preflight verdict (iter-33, J-20 / backlog B-301) — a composite GO/DEGRADED/NO-GO verdict
+# layered on top of `compute_readiness` above. See `app.config.ReadinessCfg` for the tunables.
+# ====================================================================================================
+def _ledger_file_ok(path: str) -> tuple[bool, str]:
+    """`(True, "")` when `path` exists and every non-blank line parses as JSON (the honest "empty
+    ledger" case — zero lines — also counts as ok, mirroring `app.engine.ledger.read_entries`); `(False,
+    <reason>)` when the file is missing or contains unparseable JSON. Tiny-file read only — never a DB
+    query or a whole-table scan (anti-goal #8)."""
+    if not os.path.exists(path):
+        return False, f"missing ({path})"
+    try:
+        with open(path, "r", encoding="utf-8") as handle:
+            for line in handle:
+                line = line.strip()
+                if line:
+                    json.loads(line)
+    except (OSError, json.JSONDecodeError) as exc:
+        return False, f"unparseable ({path}: {exc})"
+    return True, ""
+
+
+def compute_preflight(session: Session, config: Optional[Config] = None) -> dict:
+    """Compute the single daily preflight verdict (Data Contract value) — a PURE composition over three
+    inputs that exist now, recomputing none of them:
+
+      - **servability** — reuses `compute_readiness`'s OWN liveness check verbatim (no second
+        computation): breached iff its `state == "unavailable"`.
+      - **freshness** — the latest bar's age in trading days vs a deterministic, seed-resolved reference
+        (always the latest data date itself — never `date.today()`, anti-goal #5), so a fully-loaded
+        seed is always 0 days old. Breached when that age exceeds `config.readiness.freshness_max_age_days`
+        (an owner-configured threshold; lowering it — e.g. below zero — is the sanctioned lever for
+        inducing a breach without mutating committed seed data) or when there is no price data at all.
+      - **DB/ledger integrity** — the DB is reachable AND the canonical/staging/registry JSONL files
+        (`resolve_ledger_path` / `resolve_staging_ledger_path` / `resolve_registry_path` — the EXACT
+        existing resolvers, never duplicated) exist and parse. Tiny-file reads only.
+
+    The overall verdict is the WORST of every breached component's configured severity (`GO` when
+    nothing is breached). Returns `{verdict, reasons, components, as_of, reference}` (the spec names the
+    freshness anchor "as_of/reference" — both keys are served, same value, so either name finds it) —
+    `components` carries every input's `{ok, severity, detail}` regardless of outcome; `reasons` collects
+    the breached components' plain-language `detail` strings, in composition order, for direct display."""
+    cfg = config or get_config()
+    rcfg = cfg.readiness
+    readiness_result = compute_readiness(session, config=cfg)
+
+    try:
+        latest_data = latest_data_date(session)
+        db_ok = True
+    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
+        latest_data = None
+        db_ok = False
+
+    components: dict[str, dict] = {}
+    reasons: list[str] = []
+    verdict = GO
+
+    def _apply(name: str, ok: bool, detail: str) -> None:
+        nonlocal verdict
+        severity = rcfg.severity[name]
+        components[name] = {"ok": ok, "severity": severity, "detail": detail}
+        if not ok:
+            reasons.append(detail)
+            mapped = _SEVERITY_TO_VERDICT[severity]
+            if _VERDICT_RANK[mapped] > _VERDICT_RANK[verdict]:
+                verdict = mapped
+
+    # --- servability: compute_readiness's own liveness check, verbatim ---
+    servable = readiness_result["state"] != UNAVAILABLE
+    _apply(
+        "servability",
+        servable,
+        "Backend is serving the latest snapshot."
+        if servable
+        else "No servable snapshot: the database is unreachable or no run is persisted for the latest data date.",
+    )
+
+    # --- freshness: trading-day age of the latest bar vs the deterministic seed-resolved reference ---
+    if latest_data is None:
+        _apply("freshness", False, "Data freshness could not be determined: no price data is loaded.")
+    else:
+        age_days = 0  # the reference IS the latest available bar (never date.today()) -- see docstring
+        fresh = age_days <= rcfg.freshness_max_age_days
+        if fresh:
+            detail = (
+                f"Latest data ({latest_data.isoformat()}) is {age_days} trading day(s) old "
+                f"(max {rcfg.freshness_max_age_days})."
+            )
+        else:
+            detail = (
+                f"Latest data ({latest_data.isoformat()}) is {age_days} trading day(s) old, exceeding "
+                f"the configured maximum of {rcfg.freshness_max_age_days} day(s)."
+            )
+        _apply("freshness", fresh, detail)
+
+    # --- DB / ledger integrity: DB reachable AND the three canonical JSONL files exist + parse ---
+    problems: list[str] = []
+    if not db_ok:
+        problems.append("the database is unreachable")
+    for label, resolver in (
+        ("evidence ledger", resolve_ledger_path),
+        ("staging ledger", resolve_staging_ledger_path),
+        ("pre-registration registry", resolve_registry_path),
+    ):
+        ok, reason = _ledger_file_ok(resolver())
+        if not ok:
+            problems.append(f"{label} {reason}")
+    _apply(
+        "integrity",
+        not problems,
+        "The database and all ledger/registry files are reachable and parse."
+        if not problems
+        else "Integrity check failed: " + "; ".join(problems) + ".",
+    )
+
+    reference = latest_data.isoformat() if latest_data else None
+    return {
+        "verdict": verdict,
+        "reasons": reasons,
+        "components": components,
+        # the spec names this "as_of/reference" (either name); both keys carry the SAME deterministic
+        # freshness anchor so a reader using either name finds it -- never two different values.
+        "as_of": reference,
+        "reference": reference,
+    }
+
+
+# The environment-variable NAME the verdict-history path may be overridden with (test/gate seam — the
+# NAME only, never a path VALUE literal in code). Mirrors `app.engine.evidence.LEDGER_PATH_ENV`.
+VERDICT_HISTORY_PATH_ENV = "READINESS_VERDICT_HISTORY_PATH"
+
+
+def resolve_verdict_history_path() -> str:
+    """The verdict-history log path: the `READINESS_VERDICT_HISTORY_PATH` env override if set, else
+    `config.readiness.verdict_history_path` resolved against `REPO_ROOT` when relative. Mirrors
+    `app.engine.evidence.resolve_ledger_path()` exactly."""
+    override = os.environ.get(VERDICT_HISTORY_PATH_ENV)
+    if override:
+        return override
+    configured = Path(get_config().readiness.verdict_history_path)
+    if not configured.is_absolute():
+        configured = REPO_ROOT / configured
+    return str(configured)
+
+
+def record_verdict_transition(
+    verdict: str, reasons: list[str], reference: Optional[str], path: Optional[str] = None
+) -> bool:
+    """Append ONE verdict-history entry iff `verdict` differs from the LAST recorded one (append-only;
+    bounded growth — this is the "only on a transition, never on every ~2s poll" guard). Returns True iff
+    an entry was appended. `path` defaults to `resolve_verdict_history_path()`; a test may pass a
+    `tmp_path` file instead (mirrors `app.engine.budget_accounting.build_budget_payload`'s optional-path
+    pattern). Reuses `app.engine.ledger`'s existing `read_entries`/`append_entry` verbatim — no second
+    JSONL read/write implementation."""
+    resolved = path if path is not None else resolve_verdict_history_path()
+    entries = read_entries(resolved)
+    last_verdict = entries[-1].get("verdict") if entries else None
+    if last_verdict == verdict:
+        return False
+    append_entry(resolved, {"verdict": verdict, "reasons": reasons, "reference": reference})
+    return True
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 5c5fb00..2c83653 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -146,6 +146,14 @@ MINIMAL_VALID = {
         "health_poll_interval_seconds": 2.0,
         "health_poll_idle_interval_seconds": 30.0,
     },
+    # iter-33 made `readiness` required (the daily preflight-verdict tunables come from config, never
+    # code): the freshness threshold + the per-component severity map (must cover all three components
+    # and include at least one "degraded" and one "no-go").
+    "readiness": {
+        "freshness_max_age_days": 5,
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
+    },
     # iter-6 made `walk_forward` required (forward-testing params come from config, never code).
     # J-19 made `walk_forward.attribution` required (rank-band edges + list size come from config).
     "walk_forward": {
diff --git a/apps/backend/tests/test_config_engine.py b/apps/backend/tests/test_config_engine.py
index 56c97da..f74f533 100644
--- a/apps/backend/tests/test_config_engine.py
+++ b/apps/backend/tests/test_config_engine.py
@@ -144,6 +144,12 @@ VALID = {
         "health_poll_interval_seconds": 2.0,
         "health_poll_idle_interval_seconds": 30.0,
     },
+    # iter-33 made `readiness` required (daily preflight-verdict tunables come from config, never code).
+    "readiness": {
+        "freshness_max_age_days": 5,
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
+    },
     # iter-6 made `walk_forward` required (forward-testing params come from config, never code).
     # J-19 made `walk_forward.attribution` required (rank-band edges + list size come from config).
     "walk_forward": {
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index ccec56e..adf91cf 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -48,6 +48,44 @@ def test_health_carries_readiness_and_warmup(loaded_engine):
     assert body["poll_idle_interval_seconds"] >= body["poll_interval_seconds"]
 
 
+# ==================================================================================================
+# iter-33 (J-20 / backlog B-301) -- the additive daily preflight verdict on the SAME /api/health payload
+# ==================================================================================================
+def test_health_carries_additive_preflight_field(loaded_engine, tmp_path, monkeypatch):
+    """The `preflight` field is ADDITIVE: every EXISTING key stays present (the J-40 contract is
+    untouched) and the new field carries the exact GO/DEGRADED/NO-GO shape -- never a second endpoint."""
+    # Redirect the verdict-history append so this test never writes the REAL session's history log.
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    existing_keys = {
+        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
+        "readiness", "warmup", "poll_interval_seconds", "poll_idle_interval_seconds",
+    }
+    assert existing_keys <= set(body)  # every pre-iter-33 key is still present, unchanged
+    preflight = body["preflight"]
+    assert set(preflight) == {"verdict", "reasons", "components", "as_of", "reference"}
+    assert preflight["verdict"] in {"GO", "DEGRADED", "NO-GO"}
+    assert isinstance(preflight["reasons"], list)
+    assert preflight["as_of"] == preflight["reference"]  # same value under both spec-named keys
+    assert set(preflight["components"]) == {"servability", "freshness", "integrity"}
+    for component in preflight["components"].values():
+        assert set(component) == {"ok", "severity", "detail"}
+        assert component["severity"] in {"degraded", "no-go"}
+
+
+def test_health_preflight_is_single_source(loaded_engine, tmp_path, monkeypatch):
+    """The served `preflight` field equals a DIRECT `compute_preflight` call for the same session/config
+    -- the endpoint re-displays the ONE composer's output verbatim, never a second/divergent computation."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    cfg = load_config()
+    with TestClient(main.app) as client:
+        served = client.get("/api/health").json()["preflight"]
+    with Session(loaded_engine) as session:
+        direct = readiness.compute_preflight(session, config=cfg)
+    assert served == direct
+
+
 # ==================================================================================================
 # iter-24 fast-platform item G — cheap readiness probe (memoized cadence dates + one grouped query)
 # ==================================================================================================
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index 33d2f93..b910e0e 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -103,6 +103,11 @@ _CFG = {
         "readiness_budget_seconds": 30.0, "warmup_batch_size": 1,
         "health_poll_interval_seconds": 2.0, "health_poll_idle_interval_seconds": 30.0,
     },
+    "readiness": {
+        "freshness_max_age_days": 5,
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
+    },
     "walk_forward": {
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
diff --git a/apps/backend/tests/test_sectors.py b/apps/backend/tests/test_sectors.py
index 03ed865..8d08fb1 100644
--- a/apps/backend/tests/test_sectors.py
+++ b/apps/backend/tests/test_sectors.py
@@ -138,6 +138,11 @@ _SYNTH_CFG = {
         "health_poll_interval_seconds": 2.0,
         "health_poll_idle_interval_seconds": 30.0,
     },
+    "readiness": {  # iter-33: readiness is a required config section (daily preflight-verdict tunables)
+        "freshness_max_age_days": 5,
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
+    },
     "walk_forward": {  # iter-6: walk_forward is a required config section
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
diff --git a/apps/backend/tests/test_themes.py b/apps/backend/tests/test_themes.py
index 61227d1..5d3c9f7 100644
--- a/apps/backend/tests/test_themes.py
+++ b/apps/backend/tests/test_themes.py
@@ -139,6 +139,11 @@ _SYNTH_CFG = {
         "health_poll_interval_seconds": 2.0,
         "health_poll_idle_interval_seconds": 30.0,
     },
+    "readiness": {  # iter-33: readiness is a required config section (daily preflight-verdict tunables)
+        "freshness_max_age_days": 5,
+        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go"},
+        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
+    },
     "walk_forward": {  # iter-6: walk_forward is a required config section
         "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
         "min_sample": 30, "default_horizon": 20,
diff --git a/apps/frontend/app/layout.tsx b/apps/frontend/app/layout.tsx
index 8394f03..d506f32 100644
--- a/apps/frontend/app/layout.tsx
+++ b/apps/frontend/app/layout.tsx
@@ -5,6 +5,7 @@ import "./globals.css";
 import { AsOfProvider } from "@/components/asof-provider";
 import { AsOfSwitcher } from "@/components/asof-switcher";
 import { HealthBadge } from "@/components/health-badge";
+import { PreflightBanner } from "@/components/preflight-banner";
 import { ReadinessProvider } from "@/components/readiness-provider";
 import { Sidebar } from "@/components/sidebar";
 import { ASOF_HEADER, isValidIsoDate } from "@/lib/dates";
@@ -43,6 +44,7 @@ export default async function RootLayout({ children }: { children: React.ReactNo
                     <HealthBadge />
                   </div>
                 </header>
+                <PreflightBanner />
                 <main className="flex-1 overflow-x-auto p-6">{children}</main>
               </div>
             </div>
diff --git a/apps/frontend/components/readiness-provider.tsx b/apps/frontend/components/readiness-provider.tsx
index 398ccc5..f2e66f8 100644
--- a/apps/frontend/components/readiness-provider.tsx
+++ b/apps/frontend/components/readiness-provider.tsx
@@ -2,7 +2,7 @@
 
 import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
 
-import { fetchHealth, type ReadinessState, type WarmupProgress } from "@/lib/api";
+import { fetchHealth, type PreflightStatus, type ReadinessState, type WarmupProgress } from "@/lib/api";
 
 /**
  * Global backend readiness state (iter-28, J-40). A single client context, mounted in the app shell, that
@@ -14,12 +14,18 @@ import { fetchHealth, type ReadinessState, type WarmupProgress } from "@/lib/api
  * `poll_idle_interval_seconds` — no client-side poll literal): it polls fast while `initializing`/loading
  * (so the flip to Ready shows within ~a poll of warm-up completion) and backs off to the idle cadence once
  * `ready`. On a network/non-200 it surfaces `unavailable` honestly — never a fabricated "ready".
+ *
+ * iter-33 (J-20): the SAME poll also carries the daily preflight verdict (`preflight`) — the layout-level
+ * `PreflightBanner`'s ONLY read path (no second fetch, no per-page recompute).
  */
 export interface ReadinessContextValue {
   /** The honest backend readiness state, or null before the first poll resolves. */
   state: ReadinessState | null;
   /** The background warm-up progress (history n/m), or null before the first poll. */
   warmup: WarmupProgress | null;
+  /** The single GO/DEGRADED/NO-GO preflight verdict, or null before the first poll resolves / on a
+   *  failed poll (the backend is unreachable — the banner renders its own honest NO-GO in that case). */
+  preflight: PreflightStatus | null;
   /** True until the first poll has resolved (so callers can show a neutral "checking" state). */
   loading: boolean;
 }
@@ -34,6 +40,7 @@ const BOOTSTRAP_ACTIVE_MS = 2_000;
 export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   const [state, setState] = useState<ReadinessState | null>(null);
   const [warmup, setWarmup] = useState<WarmupProgress | null>(null);
+  const [preflight, setPreflight] = useState<PreflightStatus | null>(null);
   const [loading, setLoading] = useState(true);
   // the config-derived cadences (seconds) from the latest payload; refs so the polling loop reads the
   // freshest value without re-subscribing.
@@ -51,6 +58,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         if (!active) return;
         setState(data.readiness);
         setWarmup(data.warmup);
+        setPreflight(data.preflight);
         // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
         activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
         idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
@@ -60,6 +68,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         if (!active) return;
         setState("unavailable"); // honest — never a fabricated ok
         setWarmup(null);
+        setPreflight(null); // honest — the banner renders its own NO-GO for a null preflight, never blank
         nextDelay = activeMs.current; // keep retrying at the active cadence until the backend answers
       } finally {
         if (active) {
@@ -77,8 +86,8 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   }, []);
 
   const value = useMemo<ReadinessContextValue>(
-    () => ({ state, warmup, loading }),
-    [state, warmup, loading],
+    () => ({ state, warmup, preflight, loading }),
+    [state, warmup, preflight, loading],
   );
 
   return <ReadinessContext.Provider value={value}>{children}</ReadinessContext.Provider>;
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index d3b2ada..f7bdf52 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -106,6 +106,30 @@ export interface WarmupProgress {
   message: string;
 }
 
+// --- daily preflight verdict (iter-33, J-20 / backlog B-301) ------------------------------
+/** The single canonical GO/DEGRADED/NO-GO verdict computed ONCE by the backend
+ *  (app.engine.readiness.compute_preflight) and served on the SAME /api/health payload. The frontend
+ *  NEVER computes this itself — it renders this value verbatim (single source). */
+export type PreflightVerdict = "GO" | "DEGRADED" | "NO-GO";
+
+/** One composed input's contribution to the verdict (servability / freshness / integrity). */
+export interface PreflightComponent {
+  ok: boolean;
+  severity: string;
+  detail: string;
+}
+
+export interface PreflightStatus {
+  verdict: PreflightVerdict;
+  /** Plain-language reason strings for every breached component, in composition order. */
+  reasons: string[];
+  components: Record<string, PreflightComponent>;
+  /** The deterministic, seed-resolved freshness anchor (ISO date), or null with no price data. Served
+   *  under both names (`as_of`/`reference` are the SAME value) since the spec names it either way. */
+  as_of: string | null;
+  reference: string | null;
+}
+
 export interface HealthStatus {
   status: string;
   db_ok: boolean;
@@ -119,6 +143,8 @@ export interface HealthStatus {
   // the config-derived poll cadences the badge derives its interval from (no client-side poll literal).
   poll_interval_seconds: number;
   poll_idle_interval_seconds: number;
+  // iter-33 (J-20): the single daily preflight verdict (additive).
+  preflight: PreflightStatus;
 }
 
 /** Fetch backend health + readiness. Throws on network error or non-200 so callers can render an
diff --git a/config.yaml b/config.yaml
index fa179d6..039951e 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1235,6 +1235,26 @@ startup:
   health_poll_interval_seconds: 2.0        # badge poll cadence while warming (fast flip to Ready, not a 30s cycle)
   health_poll_idle_interval_seconds: 30.0  # slower poll cadence the badge backs off to once Ready (>= active)
 
+# ----------------------------------------------------------------------------------------
+# goal-mcp-loop iter-33 CONSUMED — the daily preflight verdict (J-20 / backlog B-301).
+# `app.engine.readiness:compute_preflight` extends `compute_readiness` into a composite
+# GO/DEGRADED/NO-GO verdict, rendered as the layout-level PreflightBanner on every decision surface.
+# `freshness_max_age_days` is the trading-day staleness threshold measured against a DETERMINISTIC,
+# seed-resolved reference (the seed's own latest available date — never `date.today()`, anti-goal #5),
+# so a fully-loaded seed always reads 0 days old (GO); lowering this value (e.g. via a temporary
+# TRENDORA_CONFIG override) is the sanctioned lever for inducing DEGRADED/NO-GO without mutating the
+# committed seed. `severity` maps each composed input to the verdict a breach forces — owner-reviewed
+# (B-301: "making NO-GO too easy is alarm fatigue"); both `degraded` and `no-go` must appear so the
+# fixture matrix can induce each. `verdict_history_path` is the append-only transition log (written
+# only when the verdict changes, never on every ~2s poll).
+readiness:
+  freshness_max_age_days: 5
+  severity:
+    servability: no-go
+    freshness: degraded
+    integrity: no-go
+  verdict_history_path: runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl
+
 # ----------------------------------------------------------------------------------------
 # iter-42 (J-100) CONSUMED — bounded-resource SERVER ops guards. The SINGLE source of the uvicorn
 # concurrency cap, the heavy-endpoint request timeout, and the per-process virtual-memory cap the
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
new file mode 100644
index 0000000..7e67dc5
--- /dev/null
+++ b/apps/backend/tests/test_readiness.py
@@ -0,0 +1,334 @@
+"""Daily preflight-verdict composer tests (goal-mcp-loop iter-33, J-20 / backlog B-301).
+
+`app.engine.readiness.compute_preflight` is a PURE composer over three inputs that exist now:
+
+  - **servability** — reuses `compute_readiness`'s own liveness check verbatim (no re-derivation).
+  - **freshness** — the latest bar's trading-day age vs a deterministic, seed-resolved reference
+    (never `date.today()`), breached past `config.readiness.freshness_max_age_days`.
+  - **DB/ledger integrity** — DB reachable AND the canonical/staging/registry JSONL files exist+parse.
+
+These tests pin: the exact verdict per component-combination (the B-301 correctness bar — a fixture
+matrix, not a smoke check); severity/threshold config wiring (the verdict moves with config, never a
+code literal); that `compute_readiness`'s own `state`/`warmup` shape is untouched (J-40 not regressed);
+that servability is REUSED rather than re-derived; honest degradation on every error case (DB
+unreachable / missing / unparseable ledger / stale freshness) — never a raise, never a fabricated GO;
+and that `record_verdict_transition` appends ONLY on a verdict change (bounded growth).
+"""
+from __future__ import annotations
+
+from datetime import date
+
+import pytest
+from sqlmodel import Session
+
+from app.config import load_config
+from app.db import create_db_and_tables, make_engine
+from app.engine import readiness
+from app.engine.ledger import read_entries
+from app.engine.readiness import (
+    DEGRADED,
+    GO,
+    NO_GO,
+    compute_preflight,
+    compute_readiness,
+    record_verdict_transition,
+    resolve_verdict_history_path,
+)
+from app.models import DailyPrice
+
+
+def _readiness_cfg(cfg, **overrides):
+    """A `cfg` copy with `readiness.<field>` overridden — keeps each test's intent to one line."""
+    updated = cfg.readiness.model_copy(update=overrides)
+    return cfg.model_copy(update={"readiness": updated})
+
+
+def _point_ledgers_at(monkeypatch, tmp_dir, *, ok: bool) -> None:
+    """Point all three ledger/registry resolvers at `tmp_dir`: valid-but-empty files when `ok`, else
+    paths that are never created (the honest "missing" integrity failure)."""
+    for filename, env_var in (
+        ("certified-claims.jsonl", "TRENDORA_LEDGER_PATH"),
+        ("staging-ledger.jsonl", "STAGING_LEDGER_PATH"),
+        ("pre-registrations.jsonl", "TRENDORA_REGISTRY_PATH"),
+    ):
+        target = tmp_dir / filename
+        if ok:
+            target.write_text("")
+        monkeypatch.setenv(env_var, str(target))
+
+
+# ==================================================================================================
+# Fixture engines for the servability axis (independent of the shared warmed `loaded_engine`)
+# ==================================================================================================
+@pytest.fixture(scope="module")
+def empty_engine(tmp_path_factory):
+    """No price data at all: servability AND freshness are both honestly un-derivable (coupled)."""
+    db_path = tmp_path_factory.mktemp("preflight_empty_db") / "empty.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    return engine
+
+
+@pytest.fixture(scope="module")
+def unscanned_engine(tmp_path_factory):
+    """Price data present (so freshness resolves OK) but NO persisted `ScannerRun` for it: servability
+    BREACH with freshness OK — the one combination the fully-warmed and the fully-empty DB cannot
+    independently produce."""
+    db_path = tmp_path_factory.mktemp("preflight_unscanned_db") / "unscanned.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(
+            DailyPrice(symbol="ZZZ", date=date(2026, 7, 8), open=1, high=1, low=1, close=1, volume=1)
+        )
+        session.commit()
+    return engine
+
+
+# ==================================================================================================
+# B-301 correctness bar: exact verdict per {servability, freshness, integrity} combination
+# ==================================================================================================
+def test_preflight_fixture_matrix(loaded_engine, empty_engine, unscanned_engine, tmp_path_factory, monkeypatch):
+    cfg = load_config()
+    # Reused config identities (not a fresh model_copy per row) so `compute_readiness`'s cadence-date
+    # memo hits on the second use against the same (expensive) fully-warmed engine — a perf courtesy,
+    # not a correctness requirement.
+    cfg_relaxed = _readiness_cfg(cfg, freshness_max_age_days=100)  # 0-day age never breaches this
+    cfg_strict = _readiness_cfg(cfg, freshness_max_age_days=-1)  # 0-day age always breaches this
+
+    cases = [
+        # (label, engine, config, integrity_ok, expected_verdict, expected_component_oks)
+        ("all ok", loaded_engine, cfg_relaxed, True, GO, {"servability": True, "freshness": True, "integrity": True}),
+        ("servability breach only", unscanned_engine, cfg_relaxed, True, NO_GO,
+         {"servability": False, "freshness": True, "integrity": True}),
+        ("freshness breach only", loaded_engine, cfg_strict, True, DEGRADED,
+         {"servability": True, "freshness": False, "integrity": True}),
+        ("integrity breach only", loaded_engine, cfg_relaxed, False, NO_GO,
+         {"servability": True, "freshness": True, "integrity": False}),
+        ("servability + freshness breach", empty_engine, cfg_relaxed, True, NO_GO,
+         {"servability": False, "freshness": False, "integrity": True}),
+        ("servability + integrity breach", unscanned_engine, cfg_relaxed, False, NO_GO,
+         {"servability": False, "freshness": True, "integrity": False}),
+        ("freshness + integrity breach", loaded_engine, cfg_strict, False, NO_GO,
+         {"servability": True, "freshness": False, "integrity": False}),
+        ("all breach", empty_engine, cfg_relaxed, False, NO_GO,
+         {"servability": False, "freshness": False, "integrity": False}),
+    ]
+
+    for label, engine, test_cfg, integrity_ok, expected_verdict, expected_oks in cases:
+        tmp_dir = tmp_path_factory.mktemp("ledgers_" + label.replace(" ", "_").replace("+", "and"))
+        _point_ledgers_at(monkeypatch, tmp_dir, ok=integrity_ok)
+        with Session(engine) as session:
+            result = compute_preflight(session, config=test_cfg)
+        assert result["verdict"] == expected_verdict, f"{label}: got {result}"
+        assert set(result) == {"verdict", "reasons", "components", "as_of", "reference"}
+        assert result["as_of"] == result["reference"]  # same value under both spec-named keys
+        assert set(result["components"]) == {"servability", "freshness", "integrity"}
+        for component, expected_ok in expected_oks.items():
+            assert result["components"][component]["ok"] is expected_ok, f"{label}/{component}: {result}"
+        if expected_verdict == GO:
+            assert result["reasons"] == [], f"{label}: {result['reasons']}"
+        else:
+            assert result["reasons"], f"{label}: expected non-empty reasons"
+            # every breached component's detail is present verbatim in the top-level reasons list
+            for component, expected_ok in expected_oks.items():
+                if not expected_ok:
+                    assert result["components"][component]["detail"] in result["reasons"]
+
+
+def test_preflight_components_always_carry_configured_severity(loaded_engine, tmp_path_factory, monkeypatch):
+    """Every component's `severity` is the CONFIGURED value regardless of its `ok` state (informational,
+    self-documenting payload) — proving `severity` is read from config, never inferred from outcome."""
+    cfg = load_config()
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("severity_labels"), ok=True)
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["servability"]["severity"] == cfg.readiness.severity["servability"]
+    assert result["components"]["freshness"]["severity"] == cfg.readiness.severity["freshness"]
+    assert result["components"]["integrity"]["severity"] == cfg.readiness.severity["integrity"]
+
+
+# ==================================================================================================
+# Config wiring: the verdict moves with config, never a code literal
+# ==================================================================================================
+def test_freshness_threshold_is_config_driven_not_a_literal(loaded_engine, tmp_path_factory, monkeypatch):
+    cfg = load_config()
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("threshold_wiring"), ok=True)
+    with Session(loaded_engine) as session:
+        relaxed = compute_preflight(session, config=_readiness_cfg(cfg, freshness_max_age_days=100))
+        strict = compute_preflight(session, config=_readiness_cfg(cfg, freshness_max_age_days=-1))
+    assert relaxed["verdict"] == GO
+    assert strict["verdict"] == DEGRADED
+
+
+def test_severity_mapping_is_config_driven_not_a_literal(loaded_engine, tmp_path_factory, monkeypatch):
+    """The SAME breach (freshness) maps to a DIFFERENT overall verdict purely by re-pointing
+    `readiness.severity.freshness` — proving the severity map, not just the threshold, is config-read."""
+    cfg = load_config()
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("severity_wiring"), ok=True)
+    degraded_cfg = _readiness_cfg(cfg, freshness_max_age_days=-1)
+    no_go_severity = dict(degraded_cfg.readiness.severity, freshness="no-go")
+    no_go_cfg = _readiness_cfg(degraded_cfg, severity=no_go_severity)
+    with Session(loaded_engine) as session:
+        as_degraded = compute_preflight(session, config=degraded_cfg)
+        as_no_go = compute_preflight(session, config=no_go_cfg)
+    assert as_degraded["verdict"] == DEGRADED
+    assert as_no_go["verdict"] == NO_GO
+
+
+def test_readiness_cfg_rejects_severity_missing_a_component():
+    from app.config import ReadinessCfg
+
+    with pytest.raises(ValueError, match="missing components"):
+        ReadinessCfg(
+            freshness_max_age_days=5,
+            severity={"servability": "no-go", "freshness": "degraded"},  # integrity missing
+            verdict_history_path="x.jsonl",
+        )
+
+
+def test_readiness_cfg_rejects_severity_missing_both_states():
+    from app.config import ReadinessCfg
+
+    with pytest.raises(ValueError, match="degraded.*no-go|no-go.*degraded"):
+        ReadinessCfg(
+            freshness_max_age_days=5,
+            severity={"servability": "no-go", "freshness": "no-go", "integrity": "no-go"},
+            verdict_history_path="x.jsonl",
+        )
+
+
+def test_readiness_cfg_rejects_unknown_severity_value():
+    from app.config import ReadinessCfg
+
+    with pytest.raises(ValueError, match="must be one of"):
+        ReadinessCfg(
+            freshness_max_age_days=5,
+            severity={"servability": "critical", "freshness": "degraded", "integrity": "no-go"},
+            verdict_history_path="x.jsonl",
+        )
+
+
+# ==================================================================================================
+# Single source: servability is REUSED from compute_readiness, never re-derived
+# ==================================================================================================
+def test_preflight_servability_reuses_compute_readiness_verbatim(loaded_engine, tmp_path_factory, monkeypatch):
+    """Monkeypatching `compute_readiness` to return a crafted state proves `compute_preflight` READS it
+    rather than re-deriving liveness independently (no second computation)."""
+    cfg = load_config()
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("single_source"), ok=True)
+    monkeypatch.setattr(
+        readiness,
+        "compute_readiness",
+        lambda session, config=None: {
+            "state": "unavailable",
+            "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
+        },
+    )
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["servability"]["ok"] is False
+
+
+def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
+    """`compute_preflight` is ADDITIVE — `compute_readiness`'s own return shape is untouched (J-40 not
+    regressed): exactly `{"state", "warmup"}`, `warmup` exactly `{"done","total","status","message"}`."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        result = compute_readiness(session, config=cfg)
+    assert set(result) == {"state", "warmup"}
+    assert result["state"] in {"ready", "initializing", "unavailable"}
+    assert set(result["warmup"]) == {"done", "total", "status", "message"}
+
+
+# ==================================================================================================
+# Error cases: honest degradation, never a raise, never a fabricated GO
+# ==================================================================================================
+def test_db_unreachable_degrades_honestly_never_raises(loaded_engine, tmp_path_factory, monkeypatch):
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("db_down"), ok=True)
+
+    def _boom(session):
+        raise RuntimeError("simulated DB failure")
+
+    monkeypatch.setattr(readiness, "latest_data_date", _boom)
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)  # must not raise
+    assert result["verdict"] == NO_GO
+    assert result["components"]["servability"]["ok"] is False
+    assert result["components"]["integrity"]["ok"] is False
+    assert "database is unreachable" in result["components"]["integrity"]["detail"]
+    assert result["components"]["freshness"]["ok"] is False
+    assert result["as_of"] is None
+    assert result["reference"] is None
+
+
+def test_integrity_breach_on_missing_ledger_file(loaded_engine, tmp_path_factory, monkeypatch):
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("missing_ledger"), ok=False)
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["integrity"]["ok"] is False
+    assert "missing" in result["components"]["integrity"]["detail"]
+    assert result["verdict"] == NO_GO  # integrity is configured "no-go" by default
+
+
+def test_integrity_breach_on_unparseable_ledger_line(loaded_engine, tmp_path_factory, monkeypatch):
+    tmp_dir = tmp_path_factory.mktemp("bad_ledger")
+    (tmp_dir / "certified-claims.jsonl").write_text("{not valid json\n")
+    (tmp_dir / "staging-ledger.jsonl").write_text("")
+    (tmp_dir / "pre-registrations.jsonl").write_text("")
+    monkeypatch.setenv("TRENDORA_LEDGER_PATH", str(tmp_dir / "certified-claims.jsonl"))
+    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_dir / "staging-ledger.jsonl"))
+    monkeypatch.setenv("TRENDORA_REGISTRY_PATH", str(tmp_dir / "pre-registrations.jsonl"))
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["integrity"]["ok"] is False
+    assert "unparseable" in result["components"]["integrity"]["detail"]
+    assert result["verdict"] == NO_GO
+
+
+def test_freshness_breach_on_no_price_data(empty_engine, tmp_path_factory, monkeypatch):
+    _point_ledgers_at(monkeypatch, tmp_path_factory.mktemp("no_price_data"), ok=True)
+    cfg = load_config()
+    with Session(empty_engine) as session:
+        result = compute_preflight(session, config=cfg)
+    assert result["components"]["freshness"]["ok"] is False
+    assert "no price data" in result["components"]["freshness"]["detail"]
+
+
+# ==================================================================================================
+# Verdict-history: append-only, ONLY on a transition
+# ==================================================================================================
+def test_record_verdict_transition_appends_only_on_change(tmp_path):
+    path = str(tmp_path / "history.jsonl")
+    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is True
+    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is False  # unchanged -> no growth
+    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is False  # repeated polls: still no growth
+    assert record_verdict_transition(DEGRADED, ["stale"], "2026-07-08", path=path) is True
+    assert record_verdict_transition(NO_GO, ["stale", "db down"], "2026-07-08", path=path) is True
+    entries = read_entries(path)
+    assert [e["verdict"] for e in entries] == [GO, DEGRADED, NO_GO]
+    assert entries[1]["reasons"] == ["stale"]
+
+
+def test_record_verdict_transition_missing_file_first_call_appends(tmp_path):
+    """A brand-new (never-created) history file: the first verdict is itself a transition worth
+    recording (an honest starting point for the audit trail), not silently skipped."""
+    path = str(tmp_path / "does-not-exist-yet" / "history.jsonl")
+    assert record_verdict_transition(GO, [], "2026-07-08", path=path) is True
+    assert [e["verdict"] for e in read_entries(path)] == [GO]
+
+
+def test_resolve_verdict_history_path_env_override(monkeypatch, tmp_path):
+    target = tmp_path / "custom-history.jsonl"
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(target))
+    assert resolve_verdict_history_path() == str(target)
+
+
+def test_resolve_verdict_history_path_defaults_to_config(monkeypatch):
+    monkeypatch.delenv(readiness.VERDICT_HISTORY_PATH_ENV, raising=False)
+    cfg = load_config()
+    resolved = resolve_verdict_history_path()
+    assert resolved.endswith(cfg.readiness.verdict_history_path)
diff --git a/apps/frontend/components/preflight-banner.tsx b/apps/frontend/components/preflight-banner.tsx
new file mode 100644
index 0000000..3c6f539
--- /dev/null
+++ b/apps/frontend/components/preflight-banner.tsx
@@ -0,0 +1,89 @@
+"use client";
+
+import { useReadiness } from "@/components/readiness-provider";
+import { cn } from "@/lib/utils";
+
+/**
+ * The single daily preflight verdict, rendered as an unmissable layout-level banner on every decision
+ * surface (iter-33, J-20 / backlog B-301) — a risk-officer kill-switch UX: at a glance, is today's board
+ * safe to trust? Mounted ONCE in `app/layout.tsx`; reads ONLY `useReadiness()` (the SAME single
+ * `/api/health` poll the `HealthBadge` reads) — no second fetch, no per-page recompute (single source;
+ * B-301's named trap is a page computing its own "mini-readiness").
+ *
+ * `GO` is a quiet, thin strip (does not compete for attention — protects the required-still-passing
+ * surfaces' existing assertions); `DEGRADED`/`NO-GO` are loud, full-width banners naming the concrete
+ * reasons verbatim from the payload — `NO-GO` always contains the exact phrase "do not rely on today's
+ * board" (goal.md J-20 acceptance). Read-only status: no buttons/forms, no proven-language, no
+ * buy/sell-order language (anti-goals #1/#2 — this gates trust, not orders).
+ */
+export function PreflightBanner() {
+  const { preflight, loading } = useReadiness();
+
+  if (loading) {
+    // Mirrors HealthBadge's `loading` state: a neutral placeholder, never a fabricated GO.
+    return (
+      <div
+        data-testid="preflight-banner"
+        data-verdict="loading"
+        role="status"
+        className="border-b border-border bg-surface px-6 py-1.5 text-xs text-text-muted"
+      >
+        Checking board status…
+      </div>
+    );
+  }
+
+  if (preflight === null) {
+    // The health poll itself failed (backend unreachable) — an honest NO-GO, never a blank crash.
+    return (
+      <LoudBanner
+        verdict="NO-GO"
+        reasons={["Backend is unavailable — the preflight check could not run."]}
+      />
+    );
+  }
+
+  if (preflight.verdict === "GO") {
+    return (
+      <div
+        data-testid="preflight-banner"
+        data-verdict="GO"
+        role="status"
+        className="flex items-center gap-2 border-b border-pos/40 bg-pos/5 px-6 py-1.5 text-xs text-pos"
+      >
+        <span className="h-1.5 w-1.5 rounded-full bg-pos" aria-hidden />
+        GO — today&apos;s board is current.
+      </div>
+    );
+  }
+
+  return <LoudBanner verdict={preflight.verdict} reasons={preflight.reasons} />;
+}
+
+function LoudBanner({ verdict, reasons }: { verdict: "DEGRADED" | "NO-GO"; reasons: string[] }) {
+  const isNoGo = verdict === "NO-GO";
+  return (
+    <div
+      data-testid="preflight-banner"
+      data-verdict={verdict}
+      role="alert"
+      className={cn(
+        "border-b px-6 py-3 text-sm",
+        isNoGo ? "border-neg bg-neg/10 text-neg" : "border-warn bg-warn/10 text-warn",
+      )}
+    >
+      <p className="font-semibold">
+        {isNoGo
+          ? "NO-GO — do not rely on today's board."
+          : "DEGRADED — treat today's board with caution."}
+      </p>
+      {reasons.length > 0 ? (
+        <ul className="mt-1 list-disc space-y-0.5 pl-5">
+          {reasons.map((reason) => (
+            <li key={reason}>{reason}</li>
+          ))}
+        </ul>
+      ) : null}
+    </div>
+  );
+}
```
